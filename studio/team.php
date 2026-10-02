<?php
// team.php — OWNER-ONLY admin for the Lieutenant workspace (2026-10-01).
// See docs/LIEUTENANT-WORKSPACE.md. Shared contract: inc/workspace.php (ws_*).
//
// Sections (plain PHP forms; every POST = csrf_check() + Post/Redirect/Get with a flash):
//   1. People          add a lieutenant (private magic link shown ONCE), edit brands + caps,
//                      rotate the link ("New link"), deactivate / activate. Today's usage.
//   2. Comics → brand  assign every project to a brand (blank = invisible to lieutenants),
//                      plus a bulk "set all unassigned" helper.
//   3. Brands          add / remove brand names (a brand in use cannot be removed).
//   4. Settings        the WS_SETTINGS_DEFAULT keys (caps, takes, pacing, models, worker on/off).
//   5. Generator       worker heartbeat, job counts, last 15 jobs, cancel queued jobs.
//
// Magic-link tokens are generated here, hashed with ws_token_hash() and only the hash is
// stored. The raw link rides from the POST to the very next GET in $_SESSION['ws_once'] and is
// dropped as soon as that GET renders, so it is never stored, logged or shown again.
// Lieutenants never reach this page: ws_gate() 403s them (team.php is not on WS_LT_ALLOW),
// and ws_is_owner() below rejects everyone except the owner.
declare(strict_types=1);
require_once __DIR__ . '/inc/boot.php';
require_auth();

if (!function_exists('ws_is_owner') || !ws_is_owner()) {
    http_response_code(403);
    header('Content-Type: text/html; charset=utf-8');
    header('Cache-Control: no-store');
    ?><!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark"><meta name="robots" content="noindex,nofollow">
<title>Team · Comic Studio</title><link rel="stylesheet" href="assets/studio.css">
<style>body{display:flex;align-items:center;justify-content:center;min-height:100vh;padding:16px}</style></head><body>
<div class="card auth" style="text-align:center"><div class="brand" style="justify-content:center"><span class="dot"></span> Comic Studio</div>
<p>👥 The Team page is for the owner only.</p><p><a class="btn" href="index.php">← Back to the Studio</a></p></div>
</body></html><?php
    exit;
}
header('Cache-Control: no-store, private');
header('X-Robots-Tag: noindex');
header('Referrer-Policy: same-origin');

const WS_TEAM_CHAT_MODELS = ['claude-opus-5-5', 'claude-sonnet-5-5', 'claude-haiku-4-5'];
const WS_TEAM_EFFORTS     = ['low', 'medium', 'high'];
const WS_TEAM_RES         = ['1k', '2k'];
// Numeric settings: key => [isFloat, min, max, label]
const WS_TEAM_NUM = [
    'gensPerDay'       => [false, 0, 1000, 'Images per person per day'],
    'globalGensPerDay' => [false, 0, 5000, 'Images per day, whole studio'],
    'msgsPerDay'       => [false, 0, 2000, 'Claude replies per person per day'],
    'usdPerDay'        => [true,  0, 100,  'Claude $ per person per day'],
    'maxTakes'         => [false, 1, 8,    'Takes per Generate click'],
    'minGapSec'        => [false, 20, 3600, 'Seconds between worker submits'],
];
// Per-person cap overrides: key => [isFloat, min, max, label]
const WS_TEAM_CAPS = [
    'gensPerDay' => [false, 0, 1000, 'Images/day'],
    'msgsPerDay' => [false, 0, 2000, 'Claude replies/day'],
    'usdPerDay'  => [true,  0, 100,  'Claude $/day'],
];

// ---- page-local helpers (prefix ws_team_; not shared) ---------------------------------
function ws_team_s(string $k, int $max = 2000): string {
    $v = $_POST[$k] ?? '';
    if (!is_string($v) || !mb_check_encoding($v, 'UTF-8')) return '';
    return trim(mb_substr($v, 0, $max));
}
function ws_team_clean(string $s): string {
    $s = preg_replace('/[\x00-\x1F\x7F]+/u', ' ', $s) ?? '';
    $s = preg_replace('/\s+/u', ' ', $s) ?? '';
    return trim($s);
}
// Post/Redirect/Get with a one-shot flash.
function ws_team_back(string $anchor, string $type, string $msg): never {
    $_SESSION['ws_team_flash'] = ['type' => $type === 'ok' ? 'ok' : 'err', 'msg' => $msg];
    header('Location: team.php' . ($anchor !== '' ? '#' . $anchor : ''), true, 303);
    exit;
}
// Parse a number string within bounds. null = invalid.
function ws_team_num(string $v, bool $float, float $lo, float $hi): int|float|null {
    $v = trim($v);
    if ($float ? !preg_match('/^\d{1,6}(\.\d{1,4})?$/', $v) : !preg_match('/^\d{1,6}$/', $v)) return null;
    $n = $float ? round((float)$v, 2) : (int)$v;
    if ($n < $lo || $n > $hi) return null;
    return $n;
}
// caps[...] overrides from POST. Blank = use the default (key omitted). Returns [caps, error|null].
function ws_team_caps_in($raw): array {
    $raw = is_array($raw) ? $raw : [];
    $out = [];
    foreach (WS_TEAM_CAPS as $k => [$isF, $lo, $hi, $label]) {
        $v = $raw[$k] ?? '';
        if (!is_string($v)) return [[], "Bad value for $label."];
        if (trim($v) === '') continue;
        $n = ws_team_num($v, $isF, (float)$lo, (float)$hi);
        if ($n === null) return [[], "$label must be " . ($isF ? 'a number' : 'a whole number') . " from $lo to $hi (or blank for the default)."];
        $out[$k] = $n;
    }
    return [$out, null];
}
// brands[] checkboxes from POST, filtered to the known list (order kept, de-duplicated).
function ws_team_brands_in($raw, array $valid): array {
    $out = [];
    foreach ((is_array($raw) ? $raw : []) as $b) if (is_string($b) && in_array($b, $valid, true) && !in_array($b, $out, true)) $out[] = $b;
    return $out;
}
function ws_team_person_id(): string { $id = ws_team_s('id', 40); return preg_match('/^lt_[a-f0-9]{1,20}$/', $id) ? $id : ''; }
// The magic link for a token, built from the request host. Always https except a local dev host.
function ws_team_link(string $tok): string {
    $host  = preg_replace('/[^A-Za-z0-9.:\[\]-]/', '', (string)($_SERVER['HTTP_HOST'] ?? '')) ?: '3dmusclecomics.com';
    $local = (bool)preg_match('/^(localhost|127\.0\.0\.1|\[::1\])(:\d+)?$|\.(localhost|test)(:\d+)?$/i', $host);
    $https = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off') || strtolower((string)($_SERVER['HTTP_X_FORWARDED_PROTO'] ?? '')) === 'https';
    $dir   = str_replace('\\', '/', dirname((string)($_SERVER['SCRIPT_NAME'] ?? '/studio/team.php')));
    $dir   = ($dir === '.' || $dir === '/') ? '' : rtrim($dir, '/');
    return (($https || !$local) ? 'https' : 'http') . '://' . $host . $dir . '/ws.php?t=' . $tok;
}
function ws_team_ts($v): int {
    if ($v === null || $v === '' || $v === false) return 0;
    if (is_int($v) || is_float($v)) return (int)$v;
    if (is_string($v) && ctype_digit($v)) return (int)$v;
    return is_string($v) ? (int)strtotime($v) : 0;
}
function ws_team_date($v, string $fmt = 'M j, Y'): string {
    $t = ws_team_ts($v); if ($t <= 0) return '—';
    $d = new DateTime('@' . $t); $d->setTimezone(new DateTimeZone(WS_TZ)); return $d->format($fmt);
}
function ws_team_rel($v, string $never = 'never'): string {
    $t = ws_team_ts($v); if ($t <= 0) return $never;
    $d = time() - $t; $fut = $d < 0; $d = abs($d);
    if ($d < 45) return $fut ? 'in a moment' : 'just now';
    if ($d < 3600) $s = max(1, (int)round($d / 60)) . 'm';
    elseif ($d < 86400) $s = (int)round($d / 3600) . 'h';
    elseif ($d < 86400 * 45) $s = (int)round($d / 86400) . 'd';
    else return ws_team_date($t);
    return $fut ? "in $s" : "$s ago";
}
function ws_team_money($v): string { return '$' . number_format((float)$v, 2); }
function ws_team_status_color(string $s): string {
    return ['queued' => '#EF9F27', 'running' => '#378ADD', 'done' => '#1D9E75', 'failed' => '#E24B4A', 'cancelled' => '#6F7380',
            'active' => '#1D9E75', 'on-hold' => '#EF9F27', 'archived' => '#6F7380'][$s] ?? '#9CA0AC';
}

// =============================== POST actions ===============================================
if (($_SERVER['REQUEST_METHOD'] ?? 'GET') === 'POST') {
    csrf_check();
    $do = ws_team_s('do', 40);
    $brandsNow = ws_team()['brands'];

    // ---- People ----------------------------------------------------------------------------
    if ($do === 'add') {
        $name = ws_team_clean(ws_team_s('name', 400));
        if ($name === '') ws_team_back('people', 'err', 'A name is required.');
        if (mb_strlen($name) > 60) ws_team_back('people', 'err', 'That name is too long (60 characters max).');
        $brands = ws_team_brands_in($_POST['brands'] ?? null, $brandsNow);
        if (!$brands) ws_team_back('people', 'err', 'Pick at least one brand for ' . $name . '.');
        [$caps, $cerr] = ws_team_caps_in($_POST['caps'] ?? null);
        if ($cerr !== null) ws_team_back('people', 'err', $cerr);
        $tok = bin2hex(random_bytes(24));
        $person = [
            'id' => 'lt_' . nid(), 'name' => $name, 'brands' => $brands, 'active' => true,
            'tokenHash' => ws_token_hash($tok), 'rev' => 1, 'caps' => $caps,
            'createdAt' => ws_now(), 'lastSeenAt' => null,
        ];
        ws_team_update(function (array $t) use ($person): array { $t['people'][] = $person; return $t; });
        $_SESSION['ws_once'] = ['name' => $name, 'url' => ws_team_link($tok), 'kind' => 'new', 'active' => true];
        $tok = '';
        ws_team_back('people', 'ok', $name . ' was added. Copy their private link below now.');
    }

    if ($do === 'edit') {
        $id = ws_team_person_id();
        if ($id === '') ws_team_back('people', 'err', 'Unknown person.');
        $brands = ws_team_brands_in($_POST['brands'] ?? null, $brandsNow);
        if (!$brands) ws_team_back('people', 'err', 'Pick at least one brand.');
        [$caps, $cerr] = ws_team_caps_in($_POST['caps'] ?? null);
        if ($cerr !== null) ws_team_back('people', 'err', $cerr);
        $nm = '';
        ws_team_update(function (array $t) use ($id, $brands, $caps, &$nm): array {
            foreach ($t['people'] as &$p) {
                if (($p['id'] ?? '') !== $id) continue;
                $p['brands'] = array_values(array_filter($brands, fn($b) => in_array($b, $t['brands'], true)));
                $p['caps'] = $caps; $nm = (string)($p['name'] ?? '');
            }
            unset($p);
            return $t;
        });
        if ($nm === '') ws_team_back('people', 'err', 'That person no longer exists.');
        ws_team_back('people', 'ok', 'Saved ' . $nm . '.');
    }

    if ($do === 'rotate') {
        $id = ws_team_person_id();
        if ($id === '') ws_team_back('people', 'err', 'Unknown person.');
        $tok = bin2hex(random_bytes(24)); $hash = ws_token_hash($tok);
        $nm = ''; $active = false;
        ws_team_update(function (array $t) use ($id, $hash, &$nm, &$active): array {
            foreach ($t['people'] as &$p) {
                if (($p['id'] ?? '') !== $id) continue;
                $p['tokenHash'] = $hash; $p['rev'] = (int)($p['rev'] ?? 0) + 1;
                $nm = (string)($p['name'] ?? ''); $active = !empty($p['active']);
            }
            unset($p);
            return $t;
        });
        if ($nm === '') ws_team_back('people', 'err', 'That person no longer exists.');
        $_SESSION['ws_once'] = ['name' => $nm, 'url' => ws_team_link($tok), 'kind' => 'rotated', 'active' => $active];
        $tok = '';
        ws_team_back('people', 'ok', 'New link made for ' . $nm . '. The old link and their open sessions no longer work.');
    }

    if ($do === 'active') {
        $id = ws_team_person_id();
        if ($id === '') ws_team_back('people', 'err', 'Unknown person.');
        $on = ws_team_s('on', 2) === '1';
        $nm = '';
        ws_team_update(function (array $t) use ($id, $on, &$nm): array {
            foreach ($t['people'] as &$p) {
                if (($p['id'] ?? '') !== $id) continue;
                if ($on) { $p['active'] = true; }
                else { $p['active'] = false; $p['rev'] = (int)($p['rev'] ?? 0) + 1; }   // kills open sessions
                $nm = (string)($p['name'] ?? '');
            }
            unset($p);
            return $t;
        });
        if ($nm === '') ws_team_back('people', 'err', 'That person no longer exists.');
        ws_team_back('people', 'ok', $on ? ($nm . ' is active again. Their existing link works again; use New link if it may have leaked.')
                                         : ($nm . ' is deactivated. Their link and open sessions stopped working.'));
    }

    // ---- Comics → brand --------------------------------------------------------------------
    if ($do === 'brands') {
        $raw = $_POST['brand'] ?? null;
        if (!is_array($raw) || !$raw) ws_team_back('comics', 'ok', 'Nothing changed.');
        $ids = [];
        foreach (projects_all() as $p) { $pid = (string)($p['id'] ?? ''); if ($pid !== '') $ids[$pid] = true; }
        $set = [];
        foreach ($raw as $pid => $b) {
            $pid = (string)$pid;
            if (!is_string($b) || $pid === '' || ws_pid($pid) !== $pid || !isset($ids[$pid])) continue;
            $set[$pid] = trim($b);
        }
        $changed = 0; $skipped = 0;
        ws_team_update(function (array $t) use ($set, &$changed, &$skipped): array {
            foreach ($set as $pid => $b) {
                $pid = (string)$pid;
                if ($b !== '' && !in_array($b, $t['brands'], true)) { $skipped++; continue; }
                if ((string)($t['projectBrands'][$pid] ?? '') === $b) continue;
                if ($b === '') unset($t['projectBrands'][$pid]); else $t['projectBrands'][$pid] = $b;
                $changed++;
            }
            return $t;
        });
        ws_team_back('comics', $skipped ? 'err' : 'ok', ($changed ? "Saved $changed comic" . ($changed === 1 ? '' : 's') . '.' : 'Nothing changed.')
            . ($skipped ? " $skipped row(s) skipped: unknown brand." : ''));
    }

    if ($do === 'bulkbrand') {
        $b = ws_team_s('brand', 100);
        $skipArch = ws_team_s('skiparchived', 2) === '1';
        $projs = projects_all();
        $n = 0; $bad = false;
        ws_team_update(function (array $t) use ($b, $skipArch, $projs, &$n, &$bad): array {
            if (!in_array($b, $t['brands'], true)) { $bad = true; return $t; }
            foreach ($projs as $p) {
                $pid = (string)($p['id'] ?? '');
                if ($pid === '' || ws_pid($pid) !== $pid) continue;
                if ($skipArch && ($p['status'] ?? '') === 'archived') continue;
                if ((string)($t['projectBrands'][$pid] ?? '') !== '') continue;
                $t['projectBrands'][$pid] = $b; $n++;
            }
            return $t;
        });
        if ($bad) ws_team_back('comics', 'err', 'Pick a brand first.');
        ws_team_back('comics', 'ok', $n ? "$n unassigned comic" . ($n === 1 ? '' : 's') . " set to $b." : 'There were no unassigned comics to set.');
    }

    // ---- Brands ----------------------------------------------------------------------------
    if ($do === 'brand_add') {
        $name = ws_team_clean(ws_team_s('name', 200));
        if ($name === '' || mb_strlen($name) > 40) ws_team_back('brands', 'err', 'Brand names are 1 to 40 characters.');
        if (!preg_match('/^[\p{L}\p{N}][\p{L}\p{N} .&\'+_-]*$/u', $name)) ws_team_back('brands', 'err', "Use letters, numbers, spaces and . & ' + _ - only.");
        $dup = false;
        ws_team_update(function (array $t) use ($name, &$dup): array {
            foreach ($t['brands'] as $b) if (mb_strtolower((string)$b) === mb_strtolower($name)) { $dup = true; return $t; }
            $t['brands'][] = $name;
            return $t;
        });
        ws_team_back('brands', $dup ? 'err' : 'ok', $dup ? "$name already exists." : "Added brand $name.");
    }

    if ($do === 'brand_del') {
        $name = ws_team_s('name', 200);
        $why = '';
        ws_team_update(function (array $t) use ($name, &$why): array {
            if (!in_array($name, $t['brands'], true)) { $why = 'That brand does not exist.'; return $t; }
            if (count($t['brands']) <= 1) { $why = 'You need at least one brand.'; return $t; }
            $np = 0; foreach ($t['people'] as $p) if (in_array($name, (array)($p['brands'] ?? []), true)) $np++;
            $nc = 0; foreach ($t['projectBrands'] as $b) if ((string)$b === $name) $nc++;
            if ($np || $nc) { $why = "$name is still used by $np person(s) and $nc comic(s). Move them to another brand first."; return $t; }
            $t['brands'] = array_values(array_filter($t['brands'], fn($b) => $b !== $name));
            return $t;
        });
        ws_team_back('brands', $why !== '' ? 'err' : 'ok', $why !== '' ? $why : "Removed brand $name.");
    }

    // ---- Settings --------------------------------------------------------------------------
    if ($do === 'settings') {
        $cur = ws_settings();
        $errs = []; $new = [];
        foreach (WS_TEAM_NUM as $k => [$isF, $lo, $hi, $label]) {
            $n = ws_team_num(ws_team_s($k, 40), $isF, (float)$lo, (float)$hi);
            if ($n === null) $errs[] = "$label must be " . ($isF ? 'a number' : 'a whole number') . " from $lo to $hi.";
            else $new[$k] = $n;
        }
        $gm = ws_team_s('genModel', 80);
        if (!preg_match('/^[A-Za-z0-9][A-Za-z0-9._\/-]{0,59}$/', $gm)) $errs[] = 'Image model: letters, numbers and . _ / - only (60 max).';
        else $new['genModel'] = $gm;
        $gr = ws_team_s('genResolution', 10);
        if (!in_array($gr, WS_TEAM_RES, true)) $errs[] = 'Resolution must be 1k or 2k.'; else $new['genResolution'] = $gr;
        $cm = ws_team_s('chatModel', 80);
        if (!in_array($cm, WS_TEAM_CHAT_MODELS, true) && $cm !== (string)$cur['chatModel']) $errs[] = 'Pick a chat model from the list.';
        else $new['chatModel'] = $cm;
        $ce = ws_team_s('chatEffort', 10);
        if (!in_array($ce, WS_TEAM_EFFORTS, true)) $errs[] = 'Chat effort must be low, medium or high.'; else $new['chatEffort'] = $ce;
        $new['workerEnabled'] = ws_team_s('workerEnabled', 2) === '1';
        if ($errs) ws_team_back('settings', 'err', 'Not saved. ' . implode(' ', $errs));
        ws_team_update(function (array $t) use ($new): array { $t['settings'] = array_merge($t['settings'], $new); return $t; });
        ws_team_back('settings', 'ok', 'Settings saved.' . ($new['workerEnabled'] ? '' : ' The generator is paused.'));
    }

    // ---- Generator -------------------------------------------------------------------------
    if ($do === 'cancel') {
        $jid = ws_team_s('job', 60);
        $pid = ws_pid(ws_team_s('pid', 80));
        if (!preg_match('/^wsj_[A-Za-z0-9]{1,40}$/', $jid) || $pid === '') ws_team_back('generator', 'err', 'Unknown job.');
        $r = ws_job_cancel($jid, $pid);
        ws_team_back('generator', !empty($r['ok']) ? 'ok' : 'err', !empty($r['ok']) ? 'Job cancelled. Unused images went back to the quota.' : (string)($r['error'] ?? 'Could not cancel.'));
    }

    ws_team_back('', 'err', 'Unknown action.');
}

// =============================== GET: gather ===============================================
$team     = ws_team();
$S        = $team['settings'];
$brands   = array_values(array_map('strval', $team['brands']));
$pb       = (array)$team['projectBrands'];
$people   = $team['people'];
usort($people, fn($a, $b) => [empty($a['active']) ? 1 : 0, mb_strtolower((string)($a['name'] ?? ''))]
                          <=> [empty($b['active']) ? 1 : 0, mb_strtolower((string)($b['name'] ?? ''))]);
$usage    = ws_usage_today();
$uUsers   = (array)($usage['users'] ?? []);
$projects = projects_all();
$pname    = [];
foreach ($projects as $p) $pname[(string)($p['id'] ?? '')] = (string)($p['name'] ?? '');

$brandPeople = array_fill_keys($brands, 0); $brandComics = array_fill_keys($brands, 0);
foreach ($people as $p) foreach ((array)($p['brands'] ?? []) as $b) if (isset($brandPeople[$b])) $brandPeople[$b]++;
$unassigned = 0;
foreach ($projects as $p) {
    $b = (string)($pb[(string)($p['id'] ?? '')] ?? '');
    if ($b === '') $unassigned++; elseif (isset($brandComics[$b])) $brandComics[$b]++;
}

$jd      = ws_jobs_read();
$jobs    = $jd['jobs'];
$meta    = $jd['meta'];
$jCounts = [];
foreach ($jobs as $j) { $st = (string)($j['status'] ?? '?'); $jCounts[$st] = ($jCounts[$st] ?? 0) + 1; }
$recent  = array_slice(array_reverse($jobs), 0, 15);
$alive   = ws_worker_alive();
$keyOn   = is_file(WS_WORKER);

$staffUse = [];
foreach ($uUsers as $uid => $u) if (str_starts_with((string)$uid, 'staff:')) $staffUse[(string)$uid] = (array)$u;

$once  = $_SESSION['ws_once'] ?? null;        unset($_SESSION['ws_once']);         // shown once, then gone
$flash = $_SESSION['ws_team_flash'] ?? null;  unset($_SESSION['ws_team_flash']);
$csrfField = csrf_field();
?><!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark"><meta name="robots" content="noindex,nofollow">
<title>Team · Comic Studio</title><link rel="icon" href="assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="assets/studio.css">
<style>
.topbar{overflow-x:auto;scrollbar-width:none}.topbar::-webkit-scrollbar{display:none}.topbar>*{flex:none}
.btn.sm{padding:7px 11px;font-size:12.5px}
.btn[disabled]{opacity:.45;cursor:not-allowed}
.tm-nav{display:flex;gap:8px;flex-wrap:wrap;margin:-4px 0 16px}
.tm-nav a{font-size:12.5px;color:var(--muted);border:1px solid var(--border2);border-radius:999px;padding:4px 11px;background:var(--surface)}
.tm-nav a:hover{color:var(--text);border-color:#3c4052}
.tm-intro{font-size:13px;margin:-8px 0 14px;max-width:720px}
.flash.ok{background:rgba(29,158,117,.14);color:#8fe0c4;border:1px solid rgba(29,158,117,.35)}
.card>h2{display:flex;align-items:baseline;gap:8px;flex-wrap:wrap}
.card>h2 .muted{font-size:13px}
.tm-help{font-size:12.5px;margin:-6px 0 12px}
input[type=checkbox]{display:inline-block;width:auto;margin:0;accent-color:var(--accent)}
.tm-chk{display:inline-flex;align-items:center;gap:6px;margin:0 14px 8px 0;color:var(--text);font-size:13.5px;cursor:pointer}
.tm-fieldset{border:0;padding:0;margin:0 0 12px}
.tm-fieldset legend{font-size:12.5px;color:var(--muted);padding:0;margin-bottom:6px}
.tm-once{border:2px solid var(--accent);background:rgba(239,159,39,.09);border-radius:var(--radius);padding:14px 16px;margin:0 0 18px}
.tm-once-h{font-weight:700;margin-bottom:8px}
.tm-once-row{display:flex;gap:8px;align-items:stretch}
.tm-once-row input{margin:0;font:13px ui-monospace,SFMono-Regular,Menlo,monospace;min-width:0}
.tm-once p{margin:10px 0 0;font-size:13px}
.tm-person{border:1px solid var(--border2);border-radius:10px;padding:12px 14px;margin-bottom:10px;background:var(--bg2)}
.tm-person.off{opacity:.62}
.tm-ph{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.tm-ph strong{font-size:15px}
.tm-chip{display:inline-block;font-size:11.5px;border:1px solid var(--border2);border-radius:999px;padding:1px 8px;color:#c7cad4;background:var(--surface2)}
.tm-meta{font-size:12.5px;margin-top:4px}
.tm-usage{font-size:13px;margin-top:6px}.tm-usage b{color:var(--text)}
.tm-usage .over{color:#f3a3a2}
.tm-acts{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px;align-items:center}
.tm-acts form{margin:0}
details.tm-edit{margin-top:10px}
details.tm-edit>summary{cursor:pointer;font-size:13px;color:var(--muted);list-style:none}
details.tm-edit>summary:hover{color:var(--text)}
details.tm-edit[open]>summary{margin-bottom:10px;color:var(--text)}
.tm-caps label{flex:1 1 120px}
.tm-tools{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-bottom:10px}
.tm-tools input[type=search]{flex:1 1 200px;margin:0;width:auto}
.tm-tablewrap{overflow:auto;-webkit-overflow-scrolling:touch;border:1px solid var(--border);border-radius:10px}
.tm-tablewrap.tall{max-height:70vh}
.tm-table{width:100%;border-collapse:collapse;font-size:13.5px}
.tm-table th{position:sticky;top:0;z-index:1;text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted2);font-weight:700;padding:9px 10px;background:var(--bg2);border-bottom:1px solid var(--border);white-space:nowrap}
.tm-table td{padding:8px 10px;border-bottom:1px solid var(--border);vertical-align:middle}
.tm-table tr:last-child td{border-bottom:0}
.tm-table tr[hidden]{display:none}
.tm-table select{margin:0;padding:6px 8px;min-width:128px;font-size:13px}
.tm-table form{margin:0}
.tm-table tr.unassigned td{background:rgba(239,159,39,.07)}
.tm-table tr.unassigned td:first-child{box-shadow:inset 3px 0 0 var(--accent)}
.tm-table tr.changed td:first-child{box-shadow:inset 3px 0 0 var(--blue)}
.tm-id{font-size:11.5px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;word-break:break-all}
.tm-name a{font-weight:600}.tm-name a:hover{text-decoration:underline}
.tm-num{white-space:nowrap;font-variant-numeric:tabular-nums}
.tm-savebar{display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin-top:12px}
.tm-bulk{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-top:14px;padding-top:14px;border-top:1px solid var(--border)}
.tm-bulk select{width:auto;margin:0;min-width:150px}
.tm-bulk form{display:contents}
.tm-brandlist{list-style:none;margin:0 0 14px;padding:0}
.tm-brandlist li{display:flex;align-items:center;gap:10px;flex-wrap:wrap;padding:8px 0;border-bottom:1px solid var(--border)}
.tm-brandlist li:last-child{border-bottom:0}
.tm-brandlist form{margin:0 0 0 auto}
.tm-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:4px 14px}
.tm-grid small{display:block;color:var(--muted2);font-size:11.5px;margin-top:3px}
.tm-stat{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px}
.tm-stat span{font-size:12.5px;border:1px solid var(--border2);border-radius:8px;padding:5px 10px;background:var(--bg2)}
.tm-stat b{color:var(--text)}
.tm-dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:5px;vertical-align:middle}
@media(max-width:600px){
  .wrap{padding:16px 14px 60px}
  .topbar{gap:12px;padding:0 14px}
  .tm-user,.hide-sm{display:none}
  .tm-once-row{flex-direction:column}
  .tm-brandlist form{margin-left:0}
  .tm-table td,.tm-table th{padding:7px 8px}
  .tm-table select{min-width:0;max-width:132px}
}
</style><!-- the one bar across every system: ⌂ back to the hub, and a menu of everything else. Source: /hub/nav.js -->
<script src="https://3dmusclecomics.com/hub/nav.js"></script>
</head><body>
<header class="topbar">
  <div class="brand"><a href="cc.php" style="color:inherit;text-decoration:none"><span class="dot"></span> ⌘ Command Center</a></div>
  <a class="ghost" href="index.php">🎬 Comic Studio</a>
  <a class="ghost" href="ws.php">🧑‍✈️ Workspace</a>
  <a class="ghost" href="team.php" style="color:var(--text);font-weight:700">👥 Team</a>
  <span class="spacer"></span><span class="ghost tm-user"><?= h(current_studio_user()) ?></span> <a class="ghost" href="help.php">❔ How it works</a> <a class="ghost" href="login.php?do=logout">Log out</a></header>
<main class="wrap">
  <div class="pagehead"><h1>👥 Team <span class="muted"><?= count($people) ?></span></h1></div>
  <p class="muted tm-intro">Lieutenants sign in with a private link and only see the comics of their brands, in the Workspace. They can draft, generate takes and pick, but never publish, post, port or delete.</p>
  <nav class="tm-nav"><a href="#people">People</a><a href="#comics">Comics → brand</a><a href="#brands">Brands</a><a href="#settings">Settings</a><a href="#generator">Generator</a></nav>

  <?php if (is_array($flash) && ($flash['msg'] ?? '') !== ''): ?>
    <div class="flash <?= ($flash['type'] ?? '') === 'ok' ? 'ok' : 'err' ?>" role="status"><?= h($flash['msg']) ?></div>
  <?php endif; ?>

  <?php if (is_array($once) && !empty($once['url'])): ?>
  <div class="tm-once" role="alert">
    <div class="tm-once-h">🔗 <?= ($once['kind'] ?? '') === 'rotated' ? 'New private link for' : 'Private link for' ?> <?= h($once['name'] ?? '') ?></div>
    <div class="tm-once-row">
      <input id="onceUrl" readonly value="<?= h($once['url']) ?>" spellcheck="false" autocomplete="off" aria-label="Magic link">
      <button type="button" class="btn primary" id="onceCopy">Copy link</button>
    </div>
    <p>Send this privately. It is shown only once. Anyone with it can open their workspace — rotate it if it leaks.</p>
    <?php if (($once['kind'] ?? '') === 'rotated'): ?><p class="muted">Their old link and any open sessions have stopped working.</p><?php endif; ?>
    <?php if (empty($once['active'])): ?><p class="muted">This person is deactivated. The link works after you click Activate.</p><?php endif; ?>
  </div>
  <?php endif; ?>

  <!-- ============================== 1. PEOPLE ============================== -->
  <section class="card" id="people">
    <h2>People <span class="muted"><?= count(array_filter($people, fn($p) => !empty($p['active']))) ?> active · today <?= h(ws_day()) ?> (Pacific)</span></h2>
    <?php if (!$people): ?><p class="muted tm-help">No lieutenants yet. Add one below to get their private link.</p><?php endif; ?>

    <?php foreach ($people as $p):
      $pid = (string)($p['id'] ?? ''); if ($pid === '') continue;
      $on = !empty($p['active']);
      $u = (array)($uUsers[$pid] ?? []);
      $eff = ws_user_caps($pid);
      $ov = (array)($p['caps'] ?? []);
      $gens = (int)($u['gens'] ?? 0); $msgs = (int)($u['msgs'] ?? 0); $usd = (float)($u['usd'] ?? 0);
      $pBrands = array_map('strval', (array)($p['brands'] ?? []));
    ?>
    <div class="tm-person<?= $on ? '' : ' off' ?>">
      <div class="tm-ph">
        <strong><?= h($p['name'] ?? '') ?></strong>
        <span class="badge" style="--c:<?= $on ? '#1D9E75' : '#6F7380' ?>"><?= $on ? 'active' : 'inactive' ?></span>
        <?php foreach ($pBrands as $b): ?><span class="tm-chip"><?= h($b) ?></span><?php endforeach; ?>
      </div>
      <div class="muted tm-meta">Added <?= h(ws_team_date($p['createdAt'] ?? null)) ?> · last seen <span title="Updated about once an hour"><?= h(ws_team_rel($p['lastSeenAt'] ?? null)) ?></span> · link v<?= (int)($p['rev'] ?? 0) ?></div>
      <div class="muted tm-usage">Today:
        <b class="<?= $gens >= $eff['gensPerDay'] ? 'over' : '' ?>"><?= $gens ?></b>/<?= (int)$eff['gensPerDay'] ?> images ·
        <b class="<?= $msgs >= $eff['msgsPerDay'] ? 'over' : '' ?>"><?= $msgs ?></b>/<?= (int)$eff['msgsPerDay'] ?> Claude replies ·
        <b class="<?= $usd >= $eff['usdPerDay'] ? 'over' : '' ?>"><?= h(ws_team_money($usd)) ?></b>/<?= h(ws_team_money($eff['usdPerDay'])) ?></div>
      <div class="muted tm-meta">Caps: <?php
        $parts = [];
        foreach (WS_TEAM_CAPS as $k => $spec) if (isset($ov[$k]) && $ov[$k] !== '') $parts[] = $spec[3] . ' ' . ($spec[0] ? ws_team_money($ov[$k]) : (string)(int)$ov[$k]);
        echo $parts ? h(implode(' · ', $parts)) . ' (custom)' : 'studio defaults';
      ?></div>

      <details class="tm-edit">
        <summary>✎ Edit brands &amp; caps</summary>
        <form method="post">
          <?= $csrfField ?><input type="hidden" name="do" value="edit"><input type="hidden" name="id" value="<?= h($pid) ?>">
          <fieldset class="tm-fieldset"><legend>Brands (they see every comic of these brands)</legend>
            <?php foreach ($brands as $b): ?>
              <label class="tm-chk"><input type="checkbox" name="brands[]" value="<?= h($b) ?>"<?= in_array($b, $pBrands, true) ? ' checked' : '' ?>> <?= h($b) ?></label>
            <?php endforeach; ?>
          </fieldset>
          <div class="row tm-caps">
            <?php foreach (WS_TEAM_CAPS as $k => [$isF, $lo, $hi, $label]): ?>
              <label><?= h($label) ?>
                <input type="number" name="caps[<?= h($k) ?>]" min="<?= $lo ?>" max="<?= $hi ?>" step="<?= $isF ? '0.01' : '1' ?>" inputmode="<?= $isF ? 'decimal' : 'numeric' ?>"
                  value="<?= isset($ov[$k]) && $ov[$k] !== '' ? h((string)$ov[$k]) : '' ?>" placeholder="default <?= h((string)$S[$k]) ?>">
              </label>
            <?php endforeach; ?>
          </div>
          <p class="muted tm-help" style="margin:8px 0 0">Leave a cap blank to use the studio default.</p>
          <div class="actions"><button class="btn primary sm">Save</button></div>
        </form>
      </details>

      <div class="tm-acts">
        <form method="post" data-confirm="Make a new link for <?= h($p['name'] ?? '') ?>? Their current link and any open sessions stop working right away.">
          <?= $csrfField ?><input type="hidden" name="do" value="rotate"><input type="hidden" name="id" value="<?= h($pid) ?>">
          <button class="btn sm">🔗 New link</button>
        </form>
        <form method="post"<?= $on ? ' data-confirm="Deactivate ' . h($p['name'] ?? '') . '? Their link and open sessions stop working until you activate them again."' : '' ?>>
          <?= $csrfField ?><input type="hidden" name="do" value="active"><input type="hidden" name="id" value="<?= h($pid) ?>"><input type="hidden" name="on" value="<?= $on ? '0' : '1' ?>">
          <?php if ($on): ?><button class="btn sm danger">Deactivate</button><?php else: ?><button class="btn sm">Activate</button><?php endif; ?>
        </form>
      </div>
    </div>
    <?php endforeach; ?>

    <?php if ($staffUse): ?>
      <p class="muted tm-help" style="margin:10px 0 4px">Staff today:
        <?php $sp = []; foreach ($staffUse as $uid => $u) $sp[] = substr($uid, 6) . ' ' . (int)($u['gens'] ?? 0) . ' images, ' . (int)($u['msgs'] ?? 0) . ' replies, ' . ws_team_money($u['usd'] ?? 0); echo h(implode(' · ', $sp)); ?>
      </p>
    <?php endif; ?>

    <details class="card newproj" style="margin:14px 0 0;background:var(--bg2)"<?= $people ? '' : ' open' ?>>
      <summary>＋ Add person</summary>
      <form method="post" style="margin-top:12px">
        <?= $csrfField ?><input type="hidden" name="do" value="add">
        <label>Name <input name="name" maxlength="60" required autocomplete="off" placeholder="e.g. Alex"></label>
        <fieldset class="tm-fieldset"><legend>Brands (at least one)</legend>
          <?php foreach ($brands as $b): ?>
            <label class="tm-chk"><input type="checkbox" name="brands[]" value="<?= h($b) ?>"<?= count($brands) === 1 ? ' checked' : '' ?>> <?= h($b) ?></label>
          <?php endforeach; ?>
        </fieldset>
        <div class="row tm-caps">
          <?php foreach (WS_TEAM_CAPS as $k => [$isF, $lo, $hi, $label]): ?>
            <label><?= h($label) ?>
              <input type="number" name="caps[<?= h($k) ?>]" min="<?= $lo ?>" max="<?= $hi ?>" step="<?= $isF ? '0.01' : '1' ?>" inputmode="<?= $isF ? 'decimal' : 'numeric' ?>" placeholder="default <?= h((string)$S[$k]) ?>">
            </label>
          <?php endforeach; ?>
        </div>
        <p class="muted tm-help" style="margin:8px 0 0">Caps are optional; blank uses the studio default. You get their private link once, right after adding.</p>
        <div class="actions"><button class="btn primary">Add person</button></div>
      </form>
    </details>
  </section>

  <!-- ============================== 2. COMICS → BRAND ============================== -->
  <section class="card" id="comics">
    <h2>Comics → brand <span class="muted"><?= count($projects) ?> comics · <?= $unassigned ?> unassigned</span></h2>
    <p class="muted tm-help">A lieutenant sees every comic of their brands. A comic with no brand is not visible to any lieutenant.</p>
    <?php if (!$projects): ?>
      <p class="muted">No comics in the Studio yet.</p>
    <?php else: ?>
    <div class="tm-tools">
      <input type="search" id="cFilter" placeholder="Filter by name, id, status or brand…" aria-label="Filter comics" autocomplete="off">
      <label class="tm-chk" style="margin:0"><input type="checkbox" id="cUn"> Unassigned only</label>
      <span class="muted" id="cCount" style="font-size:12.5px"></span>
    </div>
    <form method="post" id="brandsForm">
      <?= $csrfField ?><input type="hidden" name="do" value="brands">
      <div class="tm-tablewrap tall">
        <table class="tm-table" id="cTable">
          <thead><tr><th>Comic</th><th>Status</th><th class="hide-sm">Stage</th><th>Brand</th></tr></thead>
          <tbody>
          <?php foreach ($projects as $p):
            $id = (string)($p['id'] ?? ''); if ($id === '' || ws_pid($id) !== $id) continue;
            $cur = (string)($pb[$id] ?? ''); $st = (string)($p['status'] ?? '');
            $q = mb_strtolower(((string)($p['name'] ?? '')) . ' ' . $id . ' ' . $st . ' ' . (string)($p['stage'] ?? ''));
          ?>
            <tr class="<?= $cur === '' ? 'unassigned' : '' ?>" data-q="<?= h($q) ?>">
              <td class="tm-name"><a href="creator.php?p=<?= h(urlencode($id)) ?>"><?= h($p['name'] ?? $id) ?></a><div class="muted tm-id"><?= h($id) ?></div></td>
              <td><span class="badge" style="--c:<?= ws_team_status_color($st) ?>"><?= h($st) ?></span></td>
              <td class="hide-sm muted"><?= h($p['stage'] ?? '') ?></td>
              <td><select name="brand[<?= h($id) ?>]" data-orig="<?= h($cur) ?>" aria-label="Brand for <?= h($p['name'] ?? $id) ?>">
                <option value="">— none —</option>
                <?php foreach ($brands as $b): ?><option value="<?= h($b) ?>"<?= $b === $cur ? ' selected' : '' ?>><?= h($b) ?></option><?php endforeach; ?>
                <?php if ($cur !== '' && !in_array($cur, $brands, true)): ?><option value="<?= h($cur) ?>" selected><?= h($cur) ?> (removed)</option><?php endif; ?>
              </select></td>
            </tr>
          <?php endforeach; ?>
          </tbody>
        </table>
      </div>
      <div class="tm-savebar"><button class="btn primary">Save brands</button><span class="muted" id="cDirty" style="font-size:12.5px"></span></div>
    </form>
    <div class="tm-bulk">
      <form method="post" data-confirm="Set every unassigned comic to the chosen brand? Lieutenants of that brand will see them all.">
        <?= $csrfField ?><input type="hidden" name="do" value="bulkbrand">
        <span class="muted" style="font-size:13px">Set all unassigned to</span>
        <select name="brand" required aria-label="Brand for all unassigned comics">
          <option value="">Pick a brand…</option>
          <?php foreach ($brands as $b): ?><option value="<?= h($b) ?>"><?= h($b) ?></option><?php endforeach; ?>
        </select>
        <label class="tm-chk" style="margin:0"><input type="checkbox" name="skiparchived" value="1" checked> skip archived</label>
        <button class="btn sm"<?= $unassigned ? '' : ' disabled' ?>>Apply to <?= $unassigned ?></button>
      </form>
    </div>
    <?php endif; ?>
  </section>

  <!-- ============================== 3. BRANDS ============================== -->
  <section class="card" id="brands">
    <h2>Brands <span class="muted"><?= count($brands) ?></span></h2>
    <ul class="tm-brandlist">
      <?php foreach ($brands as $b): $np = (int)($brandPeople[$b] ?? 0); $nc = (int)($brandComics[$b] ?? 0); $used = $np + $nc > 0; ?>
        <li>
          <strong><?= h($b) ?></strong>
          <span class="muted" style="font-size:12.5px"><?= $np ?> <?= $np === 1 ? 'person' : 'people' ?> · <?= $nc ?> comic<?= $nc === 1 ? '' : 's' ?></span>
          <form method="post" data-confirm="Remove the brand <?= h($b) ?>?">
            <?= $csrfField ?><input type="hidden" name="do" value="brand_del"><input type="hidden" name="name" value="<?= h($b) ?>">
            <button class="btn sm danger"<?= ($used || count($brands) <= 1) ? ' disabled title="' . ($used ? 'Still used by a person or comic' : 'You need at least one brand') . '"' : '' ?>>Remove</button>
          </form>
        </li>
      <?php endforeach; ?>
    </ul>
    <form method="post" class="row">
      <?= $csrfField ?><input type="hidden" name="do" value="brand_add">
      <label class="grow">New brand <input name="name" maxlength="40" required autocomplete="off" placeholder="e.g. Peak Week"></label>
      <button class="btn">Add brand</button>
    </form>
    <p class="muted tm-help" style="margin:10px 0 0">A brand that a person or comic still uses can't be removed. Move them first.</p>
  </section>

  <!-- ============================== 4. SETTINGS ============================== -->
  <section class="card" id="settings">
    <h2>Settings</h2>
    <form method="post">
      <?= $csrfField ?><input type="hidden" name="do" value="settings">
      <div class="tm-grid">
        <?php
        $hints = [
            'gensPerDay' => 'Default for each lieutenant. Per-person caps override it.',
            'globalGensPerDay' => 'Credit guard across everyone, staff included.',
            'msgsPerDay' => 'Claude chat replies per lieutenant.',
            'usdPerDay' => 'Claude chat spend per lieutenant.',
            'maxTakes' => '1 to 8 images per Generate click.',
            'minGapSec' => 'Worker pacing. At least 20.',
        ];
        foreach (WS_TEAM_NUM as $k => [$isF, $lo, $hi, $label]): ?>
          <label><?= h($label) ?>
            <input type="number" name="<?= h($k) ?>" required min="<?= $lo ?>" max="<?= $hi ?>" step="<?= $isF ? '0.01' : '1' ?>" inputmode="<?= $isF ? 'decimal' : 'numeric' ?>" value="<?= h($isF ? (string)round((float)$S[$k], 2) : (string)(int)$S[$k]) ?>">
            <small><?= h($hints[$k] ?? '') ?></small>
          </label>
        <?php endforeach; ?>
        <label>Image model
          <input name="genModel" required maxlength="60" pattern="[A-Za-z0-9][A-Za-z0-9._/\-]{0,59}" value="<?= h((string)$S['genModel']) ?>" autocomplete="off">
          <small>Higgsfield model id the worker uses.</small>
        </label>
        <label>Image resolution
          <select name="genResolution">
            <?php foreach (WS_TEAM_RES as $r): ?><option value="<?= h($r) ?>"<?= (string)$S['genResolution'] === $r ? ' selected' : '' ?>><?= h($r) ?></option><?php endforeach; ?>
          </select>
          <small>1k is the default and cheapest.</small>
        </label>
        <label>Chat model
          <select name="chatModel">
            <?php $cmCur = (string)$S['chatModel']; foreach (WS_TEAM_CHAT_MODELS as $m): ?><option value="<?= h($m) ?>"<?= $cmCur === $m ? ' selected' : '' ?>><?= h($m) ?></option><?php endforeach; ?>
            <?php if (!in_array($cmCur, WS_TEAM_CHAT_MODELS, true)): ?><option value="<?= h($cmCur) ?>" selected><?= h($cmCur) ?> (current)</option><?php endif; ?>
          </select>
          <small>Claude model for the comic chat.</small>
        </label>
        <label>Chat effort
          <select name="chatEffort">
            <?php foreach (WS_TEAM_EFFORTS as $e): ?><option value="<?= h($e) ?>"<?= (string)$S['chatEffort'] === $e ? ' selected' : '' ?>><?= h($e) ?></option><?php endforeach; ?>
          </select>
          <small>Low is fastest and cheapest.</small>
        </label>
      </div>
      <label class="tm-chk" style="margin-top:6px"><input type="checkbox" name="workerEnabled" value="1"<?= !empty($S['workerEnabled']) ? ' checked' : '' ?>> Generator on (uncheck to pause all workspace generation)</label>
      <div class="actions"><button class="btn primary">Save settings</button></div>
    </form>
  </section>

  <!-- ============================== 5. GENERATOR ============================== -->
  <section class="card" id="generator">
    <h2>Generator</h2>
    <div class="tm-stat">
      <span><i class="tm-dot" style="background:<?= $alive ? 'var(--teal)' : 'var(--red)' ?>"></i>Worker <b><?= $alive ? 'alive' : 'not seen' ?></b> · last seen <?= h(ws_team_rel($meta['workerSeenAt'] ?? null)) ?></span>
      <span>Worker key installed: <b><?= $keyOn ? 'yes' : 'no' ?></b></span>
      <span>Generator: <b><?= !empty($S['workerEnabled']) ? 'on' : 'paused' ?></b></span>
      <span>Today: <b><?= (int)($usage['gens'] ?? 0) ?></b>/<?= (int)$S['globalGensPerDay'] ?> images studio-wide</span>
    </div>
    <div class="tm-stat">
      <?php if (!$jCounts): ?><span class="muted">No jobs yet.</span><?php endif; ?>
      <?php foreach (['queued', 'running', 'done', 'failed', 'cancelled'] as $st): if (empty($jCounts[$st])) continue; ?>
        <span><i class="tm-dot" style="background:<?= ws_team_status_color($st) ?>"></i><?= h($st) ?> <b><?= (int)$jCounts[$st] ?></b></span>
      <?php endforeach; ?>
      <?php foreach ($jCounts as $st => $n): if (in_array($st, ['queued', 'running', 'done', 'failed', 'cancelled'], true)) continue; ?>
        <span><?= h($st) ?> <b><?= (int)$n ?></b></span>
      <?php endforeach; ?>
    </div>
    <?php if ($recent): ?>
    <div class="tm-tablewrap">
      <table class="tm-table">
        <thead><tr><th>Comic</th><th>Page</th><th>Takes</th><th>Done / failed</th><th>Status</th><th class="hide-sm">Who</th><th>When</th><th></th></tr></thead>
        <tbody>
        <?php foreach ($recent as $j):
          $jpid = ws_pid((string)($j['pid'] ?? '')); $st = (string)($j['status'] ?? '');
          $jid = (string)($j['id'] ?? '');
        ?>
          <tr>
            <td class="tm-name"><?= h($pname[$jpid] ?? $jpid) ?><?php if (($pname[$jpid] ?? null) === null): ?> <span class="muted" style="font-size:11.5px">(gone)</span><?php endif; ?></td>
            <td class="tm-num"><?= (int)($j['page'] ?? 0) ?></td>
            <td class="tm-num"><?= (int)($j['takes'] ?? 0) ?></td>
            <td class="tm-num"><?= (int)($j['done'] ?? 0) ?> / <?= (int)($j['failed'] ?? 0) ?></td>
            <td><span class="badge" style="--c:<?= ws_team_status_color($st) ?>"<?= ($j['note'] ?? '') !== '' ? ' title="' . h(mb_substr((string)$j['note'], 0, 300)) . '"' : '' ?>><?= h($st) ?><?= !empty($j['stopRequested']) && $st === 'running' ? ' · stopping' : '' ?></span></td>
            <td class="hide-sm"><?= h($j['by'] ?? '') ?></td>
            <td class="tm-num muted" title="<?= h(ws_team_date($j['createdAt'] ?? null, 'M j, Y g:i a')) ?> Pacific"><?= h(ws_team_rel($j['createdAt'] ?? null, '—')) ?></td>
            <td>
              <?php if (in_array($st, ['queued', 'running'], true) && $jid !== '' && $jpid !== '' && !($st === 'running' && !empty($j['stopRequested']))): ?>
              <form method="post" data-confirm="<?= $st === 'queued' ? 'Cancel this queued job? Its images go back to the quota.' : 'Stop this job after the take that is generating now?' ?>">
                <?= $csrfField ?><input type="hidden" name="do" value="cancel"><input type="hidden" name="job" value="<?= h($jid) ?>"><input type="hidden" name="pid" value="<?= h($jpid) ?>">
                <button class="btn sm danger"><?= $st === 'queued' ? 'Cancel' : 'Stop' ?></button>
              </form>
              <?php endif; ?>
            </td>
          </tr>
        <?php endforeach; ?>
        </tbody>
      </table>
    </div>
    <?php endif; ?>
    <p class="muted tm-help" style="margin:10px 0 0">The worker runs on the opsbox timer and signs in with its own key (data/ws/worker.json), never the bridge key. Showing the last <?= count($recent) ?> of <?= count($jobs) ?> jobs (finished jobs are kept 30 days).</p>
  </section>
</main>
<script>
(function () {
  'use strict';
  // Copy the one-time link.
  var copyBtn = document.getElementById('onceCopy'), onceUrl = document.getElementById('onceUrl');
  if (copyBtn && onceUrl) {
    onceUrl.addEventListener('focus', function () { onceUrl.select(); });
    copyBtn.addEventListener('click', function () {
      var done = function () { copyBtn.textContent = 'Copied ✓'; setTimeout(function () { copyBtn.textContent = 'Copy link'; }, 1800); };
      var legacy = function () { onceUrl.focus(); onceUrl.select(); try { document.execCommand('copy'); done(); } catch (e) { copyBtn.textContent = 'Select + copy'; } };
      if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(onceUrl.value).then(done, legacy);
      else legacy();
    });
  }
  // data-confirm="…" on any form asks first.
  document.addEventListener('submit', function (e) {
    var f = e.target, m = f && f.getAttribute ? f.getAttribute('data-confirm') : null;
    if (m && !window.confirm(m)) e.preventDefault();
  }, true);

  // Comics → brand: quick filter, unassigned toggle, dirty tracking, send only changed rows.
  var table = document.getElementById('cTable');
  if (!table) return;
  var rows = Array.prototype.slice.call(table.tBodies[0].rows);
  var filter = document.getElementById('cFilter'), unOnly = document.getElementById('cUn');
  var countEl = document.getElementById('cCount'), dirtyEl = document.getElementById('cDirty');
  var form = document.getElementById('brandsForm');
  var submitting = false;
  function sel(r) { return r.querySelector('select'); }
  function apply() {
    var q = (filter.value || '').toLowerCase().trim(), un = unOnly.checked, n = 0;
    rows.forEach(function (r) {
      var s = sel(r), hay = (r.getAttribute('data-q') || '') + ' ' + s.value.toLowerCase();
      var show = (!q || hay.indexOf(q) !== -1) && (!un || s.value === '');
      r.hidden = !show; if (show) n++;
    });
    countEl.textContent = n + ' of ' + rows.length + ' shown';
  }
  function dirtyCount() {
    var c = 0;
    rows.forEach(function (r) {
      var s = sel(r), ch = s.value !== (s.getAttribute('data-orig') || '');
      r.classList.toggle('changed', ch); r.classList.toggle('unassigned', s.value === '');
      if (ch) c++;
    });
    dirtyEl.textContent = c ? (c + ' unsaved change' + (c === 1 ? '' : 's')) : '';
    return c;
  }
  filter.addEventListener('input', apply);
  unOnly.addEventListener('change', apply);
  table.addEventListener('change', function (e) { if (e.target && e.target.tagName === 'SELECT') dirtyCount(); });
  form.addEventListener('submit', function (e) {
    if (e.defaultPrevented) return;
    if (!dirtyCount()) { e.preventDefault(); dirtyEl.textContent = 'Nothing changed.'; return; }
    rows.forEach(function (r) { var s = sel(r); if (s.value === (s.getAttribute('data-orig') || '')) s.disabled = true; });
    submitting = true;
  });
  window.addEventListener('pageshow', function () { rows.forEach(function (r) { sel(r).disabled = false; }); submitting = false; });
  window.addEventListener('beforeunload', function (e) { if (!submitting && dirtyCount()) { e.preventDefault(); e.returnValue = ''; } });
  apply();
})();
</script>
</body></html>
