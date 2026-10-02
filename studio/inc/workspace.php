<?php
// Lieutenant workspace: shared helpers (2026-10-01). Loaded by inc/boot.php. See studio/docs/LIEUTENANT-WORKSPACE.md.
//
// A "lieutenant" is a hired helper who signs in with a private magic link (no password)
// and works ONLY in the workspace pages (ws.php, ws-api.php, picker.php) on the comics of
// their brand(s). ws_gate() runs inside is_authed() for EVERY studio page and confines a
// lieutenant session to that allow-list; every other session (owner, staff, collab) is
// untouched, so the existing studio behaves exactly as before.
//
// Stores (all under data/ws/, web-denied by data/.htaccess; every write is s_with_lock'd):
//   team.json         people[], projectBrands{pid:brand}, brands[], settings{}
//   proj-<pid>.json   story, style, aspect, pages[{n,title,prompt,refs[],note}], refs[{file,label,kind}]
//   chat-<pid>.json   msgs[{id,ts,uid,by,role:user|ai|system,text,actions[]}]
//   picks-<pid>.json  pages{group:{pick:[]|'drop',c,prev_c,sig,by,ts}}
//   jobs.json         jobs[], meta{lastSubmitAt,cooldownUntil}
//   usage.json        days{YYYY-MM-DD:{users:{uid:{gens,msgs,usd}},gens}}
//   worker.json       {keyHash}  (sha256 of the generation worker's own key; never the bridge key)
declare(strict_types=1);

define('WS_DIR', SDATA . '/ws');
define('WS_TEAM', WS_DIR . '/team.json');
define('WS_JOBS', WS_DIR . '/jobs.json');
define('WS_USAGE', WS_DIR . '/usage.json');
define('WS_WORKER', WS_DIR . '/worker.json');
define('WS_ROLE', 'lieutenant');
define('WS_TZ', 'America/Los_Angeles');           // quota days roll over at midnight Pacific
define('WS_BRANDS_DEFAULT', ['3DMC', 'GrowGetter', 'Maxx Muscle', 'Bloom Beauty', '3DGC']);
define('WS_SETTINGS_DEFAULT', [
    'gensPerDay'       => 50,      // images per lieutenant per day
    'globalGensPerDay' => 150,     // images per day across everyone (credit guard)
    'msgsPerDay'       => 80,      // AI chat replies per lieutenant per day
    'usdPerDay'        => 3.0,     // AI chat spend per lieutenant per day
    'maxTakes'         => 4,       // takes per Generate click
    'minGapSec'        => 30,      // worker pacing between submits
    'genModel'         => 'nano_banana_pro',
    'genResolution'    => '1k',
    'chatModel'        => 'claude-opus-5-5',
    'chatEffort'       => 'low',
    'workerEnabled'    => true,
]);
// Scripts a lieutenant may open (basename, studio root only). Everything else is 403.
define('WS_LT_ALLOW', ['ws.php', 'ws-api.php', 'picker.php', 'img.php', 'help.php', 'login.php']);

// ---- small utils ------------------------------------------------------------
function ws_pid(string $s): string { return preg_replace('/[^a-z0-9-]/', '', $s); }
function ws_day(?int $t = null): string { $d = new DateTime('@' . ($t ?? time())); $d->setTimezone(new DateTimeZone(WS_TZ)); return $d->format('Y-m-d'); }
function ws_now(): string { return date('c'); }
function ws_json_out(array $a, int $code = 200): void {
    http_response_code($code);
    header('Content-Type: application/json; charset=utf-8');
    header('Cache-Control: no-store');
    echo json_encode($a, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE);
    exit;
}
function ws_file(string $kind, string $pid): string { return WS_DIR . '/' . $kind . '-' . ws_pid($pid) . '.json'; }

// ---- team store ---------------------------------------------------------------
function ws_team_norm($t): array {
    $t = is_array($t) ? $t : [];
    $t['people']        = array_values(array_filter((array)($t['people'] ?? []), 'is_array'));
    $t['projectBrands'] = (array)($t['projectBrands'] ?? []);
    $t['brands']        = array_values((array)($t['brands'] ?? WS_BRANDS_DEFAULT)) ?: WS_BRANDS_DEFAULT;
    $t['settings']      = array_merge(WS_SETTINGS_DEFAULT, (array)($t['settings'] ?? []));
    return $t;
}
function ws_team(): array { static $c = null; if ($c === null) $c = ws_team_norm(s_read(WS_TEAM, [])); return $c; }
// Locked read-modify-write. $fn(array $team): array $team. Returns the saved team.
function ws_team_update(callable $fn): array {
    return s_with_lock(WS_TEAM, function ($t) use ($fn) { $n = ws_team_norm($fn(ws_team_norm($t))); return ['data' => $n, 'result' => $n]; });
}
function ws_settings(): array { return ws_team()['settings']; }
function ws_person(string $id): ?array { foreach (ws_team()['people'] as $p) if (($p['id'] ?? '') === $id && $id !== '') return $p; return null; }
function ws_token_hash(string $tok): string { return hash('sha256', 'ws-magic|' . $tok); }

// ---- session roles ------------------------------------------------------------
function ws_is_lt(): bool { s_boot(); return !empty($_SESSION['studio_ok']) && ($_SESSION['studio_role'] ?? '') === WS_ROLE; }
function ws_uid(): string {
    s_boot();
    if (ws_is_lt()) return (string)($_SESSION['studio_uid'] ?? '');
    return 'staff:' . strtolower(preg_replace('/[^A-Za-z0-9]+/', '-', current_studio_user()));
}
function ws_me(): ?array { return ws_is_lt() ? ws_person((string)($_SESSION['studio_uid'] ?? '')) : null; }
// Owner = signed in through the main-site admin file (studio_login sets no studio_role)
// with an admin row whose role is 'owner'. Collab logins (users-studio.json) set
// studio_role, so they are never the owner.
function ws_is_owner(): bool {
    s_boot();
    if (empty($_SESSION['studio_ok']) || isset($_SESSION['studio_role'])) return false;
    $name = current_studio_user();
    foreach (studio_users() as $u) {
        if (($u['role'] ?? '') === 'owner' && ($name === ($u['name'] ?? null) || $name === ($u['username'] ?? null))) return true;
    }
    return false;
}

// ---- brands + visibility ------------------------------------------------------
function ws_project_brand(string $pid): string { return (string)(ws_team()['projectBrands'][ws_pid($pid)] ?? ''); }
function ws_can_see(string $pid): bool {
    $pid = ws_pid($pid);
    if ($pid === '') return false;
    if (!ws_is_lt()) return true;
    $me = ws_me(); $b = ws_project_brand($pid);
    return $me && $b !== '' && in_array($b, (array)($me['brands'] ?? []), true) && project_get($pid) !== null;
}
// Projects the current user may list in the workspace (lieutenant: own brands; others: all).
function ws_projects_visible(): array {
    $all = projects_all();
    if (!ws_is_lt()) return $all;
    $me = ws_me(); $mine = (array)($me['brands'] ?? []); $pb = ws_team()['projectBrands'];
    return array_values(array_filter($all, function ($p) use ($mine, $pb) {
        $b = (string)($pb[$p['id'] ?? ''] ?? '');
        return $b !== '' && in_array($b, $mine, true) && ($p['status'] ?? '') !== 'archived';
    }));
}

// ---- the gate (called from is_authed() for every studio request) ----------------
function ws_deny(string $msg, int $code = 403): void {
    $json = stripos((string)($_SERVER['HTTP_ACCEPT'] ?? ''), 'application/json') !== false
         || in_array(basename((string)($_SERVER['SCRIPT_NAME'] ?? '')), ['ws-api.php', 'api.php'], true)
         || ($_SERVER['REQUEST_METHOD'] ?? 'GET') === 'POST';
    if ($json) ws_json_out(['ok' => false, 'error' => $msg], $code);
    http_response_code($code);
    header('Content-Type: text/html; charset=utf-8');
    echo '<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Studio</title>'
       . '<body style="font:15px system-ui;background:#0f1115;color:#e8e8ec;display:flex;min-height:100vh;align-items:center;justify-content:center">'
       . '<div style="max-width:420px;text-align:center"><p>' . h($msg) . '</p><p><a style="color:#9aa3ff" href="ws.php">Go to your workspace</a></p></div>';
    exit;
}
function ws_gate(): void {
    static $done = false;
    if ($done) return; $done = true;
    if (!ws_is_lt()) return;                                     // owner/staff/collab: unchanged
    $me = ws_me();
    if (!$me || empty($me['active']) || (int)($me['rev'] ?? 0) !== (int)($_SESSION['studio_rev'] ?? -1)) {
        $_SESSION = []; session_destroy();
        ws_deny('Your access link is no longer active. Ask for a new one.', 401);
    }
    $scriptFile = (string)($_SERVER['SCRIPT_FILENAME'] ?? '');
    $script     = basename($scriptFile !== '' ? $scriptFile : (string)($_SERVER['SCRIPT_NAME'] ?? ''));   // the file actually executed
    $inRoot     = $scriptFile !== '' && realpath(dirname($scriptFile)) === realpath(STUDIO_ROOT);
    if ($inRoot && $script === 'index.php') { header('Location: ws.php'); exit; }
    if (!$inRoot || !in_array($script, WS_LT_ALLOW, true)) ws_deny('That page is not part of your workspace.');
    // Check GET and POST separately (a page may read either) and refuse non-strings (p[]=…) outright.
    foreach (['p', 'pid'] as $k) foreach ([$_GET[$k] ?? null, $_POST[$k] ?? null] as $raw) {
        if ($raw === null || $raw === '') continue;
        if (!is_string($raw) || !ws_can_see(ws_pid($raw))) ws_deny('That comic is not in your workspace.');
    }
    if (time() - (int)strtotime((string)($me['lastSeenAt'] ?? '1970-01-01')) > 3600) {
        $id = $me['id'];
        ws_team_update(function ($t) use ($id) {
            foreach ($t['people'] as &$p) if (($p['id'] ?? '') === $id) $p['lastSeenAt'] = ws_now();
            unset($p); return $t;
        });
    }
}
// Exchange a magic-link token for a lieutenant session. Returns true on success.
function ws_magic_login(string $tok): bool {
    $tok = trim($tok);
    if ($tok === '' || strlen($tok) < 24) return false;
    $h = ws_token_hash($tok);
    foreach (ws_team()['people'] as $p) {
        if (!empty($p['active']) && !empty($p['tokenHash']) && hash_equals((string)$p['tokenHash'], $h)) {
            s_boot(); session_regenerate_id(true);
            $_SESSION = ['studio_ok' => true, 'studio_user' => (string)($p['name'] ?? 'Lieutenant'),
                         'studio_role' => WS_ROLE, 'studio_uid' => (string)$p['id'], 'studio_rev' => (int)($p['rev'] ?? 0)];
            return true;
        }
    }
    return false;
}

// ---- per-project workspace store ------------------------------------------------
function ws_proj_norm($d): array {
    $d = is_array($d) ? $d : [];
    $d['story']  = (string)($d['story'] ?? '');
    $d['style']  = (string)($d['style'] ?? '');
    $d['aspect'] = (string)($d['aspect'] ?? '3:4');
    $d['pages']  = array_values(array_filter((array)($d['pages'] ?? []), 'is_array'));
    $d['refs']   = array_values(array_filter((array)($d['refs'] ?? []), 'is_array'));
    usort($d['pages'], fn($a, $b) => ((int)($a['n'] ?? 0)) <=> ((int)($b['n'] ?? 0)));
    return $d;
}
function ws_proj(string $pid): array { return ws_proj_norm(s_read(ws_file('proj', $pid), [])); }
function ws_proj_update(string $pid, callable $fn): array {
    return s_with_lock(ws_file('proj', $pid), function ($d) use ($fn) { $n = ws_proj_norm($fn(ws_proj_norm($d))); return ['data' => $n, 'result' => $n]; });
}
// The image group a page's takes land in. Picker + review group by this.
function ws_page_group(int $n): string { return sprintf('Page %02d', max(0, $n)); }
function ws_page_get(array $proj, int $n): ?array { foreach ($proj['pages'] as $pg) if ((int)($pg['n'] ?? 0) === $n) return $pg; return null; }

// ---- images ---------------------------------------------------------------------
// Store an image file (uploaded tmp OR a server-side temp file) into a project and append
// its metadata under the images lock. $meta extras: group, prompt, refs_used, tags, isref,
// gen, by, source, wsJob. Returns the new image row or null.
function ws_add_image(string $pid, string $tmp, string $orig, array $extra = []): ?array {
    $pid = ws_pid($pid);
    $res = store_image($tmp, $orig, $pid);
    if (!$res) return null;
    $row = array_merge([
        'file' => $res['file'], 'orig' => mb_substr($orig, 0, 120), 'rating' => 'unrated', 'accepted' => false,
        'group' => '', 'tags' => [], 'ts' => time(), 'gen' => '', 'genkey' => '',
    ], $extra);
    images_update($pid, function ($m) use ($row) { $m[] = $row; return $m; });
    return $row;
}
function ws_image_exists(string $pid, string $file): bool {
    $file = basename($file);
    if ($file === '' || !preg_match('/^[A-Za-z0-9._-]+$/', $file)) return false;
    return is_file(project_dir($pid) . '/' . $file);
}

// ---- usage + quotas ---------------------------------------------------------------
function ws_usage_today(): array { $u = s_read(WS_USAGE, []); return (array)($u['days'][ws_day()] ?? ['users' => [], 'gens' => 0]); }
function ws_user_caps(string $uid): array {
    $s = ws_settings(); $p = ws_person($uid); $c = (array)($p['caps'] ?? []);
    return [
        'gensPerDay' => (int)($c['gensPerDay'] ?? $s['gensPerDay']),
        'msgsPerDay' => (int)($c['msgsPerDay'] ?? $s['msgsPerDay']),
        'usdPerDay'  => (float)($c['usdPerDay'] ?? $s['usdPerDay']),
    ];
}
function ws_usage_mutate(callable $fn) {
    return s_with_lock(WS_USAGE, function ($u) use ($fn) {
        $u = is_array($u) ? $u : [];
        $u['days'] = (array)($u['days'] ?? []);
        $day = ws_day();
        $u['days'][$day] = (array)($u['days'][$day] ?? ['users' => [], 'gens' => 0]);
        $out = $fn($u['days'][$day]);                       // [$dayData, $result]
        $u['days'][$day] = $out[0];
        $keep = array_slice(array_keys($u['days']), -21);   // 3 weeks of history
        $u['days'] = array_intersect_key($u['days'], array_flip($keep));
        return ['data' => $u, 'result' => $out[1]];
    });
}
// Reserve $n generations for $uid. Returns ['ok'=>bool,'left'=>int,'error'=>?].
// Lieutenants are bound by their own cap AND the global cap; others only the global cap.
function ws_quota_reserve(string $uid, int $n, bool $isLt): array {
    $caps = ws_user_caps($uid); $global = (int)ws_settings()['globalGensPerDay'];
    return ws_usage_mutate(function ($d) use ($uid, $n, $isLt, $caps, $global) {
        $mine = (int)($d['users'][$uid]['gens'] ?? 0); $all = (int)($d['gens'] ?? 0);
        $leftMine = $isLt ? max(0, $caps['gensPerDay'] - $mine) : PHP_INT_MAX;
        $leftAll  = max(0, $global - $all);
        $left = min($leftMine, $leftAll);
        if ($n > $left) {
            $why = $leftAll < $leftMine ? "The studio-wide daily limit is reached ($global images). It resets at midnight Pacific."
                                        : 'Daily limit reached: ' . $caps['gensPerDay'] . ' images. It resets at midnight Pacific.';
            if ($left > 0) $why = "Only $left image(s) left today.";
            return [$d, ['ok' => false, 'left' => $left === PHP_INT_MAX ? -1 : $left, 'error' => $why]];
        }
        $d['users'][$uid]['gens'] = $mine + $n; $d['gens'] = $all + $n;
        $l = min($leftMine === PHP_INT_MAX ? PHP_INT_MAX : $leftMine - $n, $leftAll - $n);
        return [$d, ['ok' => true, 'left' => $l === PHP_INT_MAX ? -1 : $l]];
    });
}
// Give back generations that were reserved but never produced (cancel / error).
function ws_quota_release(string $uid, int $n, string $day): void {
    if ($n <= 0) return;
    s_with_lock(WS_USAGE, function ($u) use ($uid, $n, $day) {
        if (!isset($u['days'][$day])) return ['result' => null];
        $u['days'][$day]['users'][$uid]['gens'] = max(0, (int)($u['days'][$day]['users'][$uid]['gens'] ?? 0) - $n);
        $u['days'][$day]['gens'] = max(0, (int)($u['days'][$day]['gens'] ?? 0) - $n);
        return ['data' => $u, 'result' => null];
    });
}
// Chat quota: check (and count) one AI reply. Returns ['ok'=>bool,'error'=>?].
function ws_chat_quota_take(string $uid, bool $isLt): array {
    $caps = ws_user_caps($uid);
    return ws_usage_mutate(function ($d) use ($uid, $isLt, $caps) {
        $m = (int)($d['users'][$uid]['msgs'] ?? 0); $usd = (float)($d['users'][$uid]['usd'] ?? 0);
        if ($isLt && ($m >= $caps['msgsPerDay'] || $usd >= $caps['usdPerDay'])) {
            return [$d, ['ok' => false, 'error' => 'Daily Claude chat limit reached. The team thread still works; Claude is back after midnight Pacific.']];
        }
        $d['users'][$uid]['msgs'] = $m + 1;
        return [$d, ['ok' => true]];
    });
}
function ws_chat_cost_add(string $uid, float $usd): void {
    ws_usage_mutate(function ($d) use ($uid, $usd) { $d['users'][$uid]['usd'] = round((float)($d['users'][$uid]['usd'] ?? 0) + $usd, 4); return [$d, null]; });
}
function ws_quota_status(string $uid, bool $isLt): array {
    $d = ws_usage_today(); $caps = ws_user_caps($uid); $g = (int)ws_settings()['globalGensPerDay'];
    $mine = (int)($d['users'][$uid]['gens'] ?? 0); $all = (int)($d['gens'] ?? 0);
    return ['used' => $mine, 'cap' => $isLt ? $caps['gensPerDay'] : null, 'globalUsed' => $all, 'globalCap' => $g,
            'left' => $isLt ? max(0, min($caps['gensPerDay'] - $mine, $g - $all)) : max(0, $g - $all),
            'msgs' => (int)($d['users'][$uid]['msgs'] ?? 0), 'msgsCap' => $caps['msgsPerDay']];
}

// ---- generation job queue (workspace lane; separate from the legacy data/jobs.json) ----
function ws_jobs_read(): array { $j = s_read(WS_JOBS, []); $j['jobs'] = array_values((array)($j['jobs'] ?? [])); $j['meta'] = (array)($j['meta'] ?? []); return $j; }
function ws_jobs_mutate(callable $fn) {
    return s_with_lock(WS_JOBS, function ($j) use ($fn) {
        $j = is_array($j) ? $j : [];
        $j['jobs'] = array_values((array)($j['jobs'] ?? [])); $j['meta'] = (array)($j['meta'] ?? []);
        [$j, $res] = $fn($j);
        // prune finished jobs older than 30 days
        $cut = time() - 30 * 86400;
        $j['jobs'] = array_values(array_filter($j['jobs'], fn($x) => in_array($x['status'] ?? '', ['queued', 'running'], true)
            || (int)strtotime((string)($x['finishedAt'] ?? $x['createdAt'] ?? 'now')) > $cut));
        return ['data' => $j, 'result' => $res];
    });
}
// Enqueue a page generation. Validates the project, page, refs and quota. Returns
// ['ok'=>true,'job'=>…,'left'=>…] or ['ok'=>false,'error'=>…].
function ws_job_enqueue(string $pid, int $page, int $takes, string $promptOverride = ''): array {
    $pid = ws_pid($pid);
    if (!project_get($pid)) return ['ok' => false, 'error' => 'Unknown comic.'];
    $s = ws_settings();
    $takes = max(1, min((int)$s['maxTakes'], $takes));
    $proj = ws_proj($pid); $pg = ws_page_get($proj, $page);
    if (!$pg) return ['ok' => false, 'error' => "Page $page does not exist yet."];
    $prompt = trim($promptOverride !== '' ? $promptOverride : (string)($pg['prompt'] ?? ''));
    if ($prompt === '') return ['ok' => false, 'error' => "Page $page has no prompt yet. Write one first (or ask Claude to draft it)."];
    if ($proj['style'] !== '' && stripos($prompt, $proj['style']) === false) $prompt .= "\n\nStyle: " . $proj['style'];
    $prompt = mb_substr($prompt, 0, 2500);
    $refs = [];
    foreach ((array)($pg['refs'] ?? []) as $f) { $f = basename((string)$f); if (ws_image_exists($pid, $f)) $refs[] = $f; }
    $refs = array_slice(array_values(array_unique($refs)), 0, 6);
    $uid = ws_uid(); $isLt = ws_is_lt();
    $q = ws_quota_reserve($uid, $takes, $isLt);
    if (!$q['ok']) return ['ok' => false, 'error' => $q['error'], 'left' => $q['left']];
    $job = [
        'id' => 'wsj_' . nid(), 'pid' => $pid, 'page' => $page, 'group' => ws_page_group($page),
        'prompt' => $prompt, 'refs' => $refs, 'aspect' => $proj['aspect'] ?: '3:4', 'takes' => $takes,
        'model' => (string)$s['genModel'], 'resolution' => (string)$s['genResolution'],
        'uid' => $uid, 'by' => current_studio_user(), 'day' => ws_day(),
        'status' => 'queued', 'done' => 0, 'failed' => 0, 'files' => [], 'note' => '',
        'createdAt' => ws_now(), 'claimedAt' => null, 'heartbeatAt' => null, 'finishedAt' => null, 'worker' => '',
    ];
    ws_jobs_mutate(function ($j) use ($job) { $j['jobs'][] = $job; return [$j, null]; });
    return ['ok' => true, 'job' => $job, 'left' => $q['left']];
}
// Cancel a queued job (running jobs finish their current take, then stop). Releases unused quota.
function ws_job_cancel(string $jobId, string $pid): array {
    return ws_jobs_mutate(function ($j) use ($jobId, $pid) {
        foreach ($j['jobs'] as &$x) {
            if (($x['id'] ?? '') !== $jobId || ($x['pid'] ?? '') !== $pid) continue;
            if (!in_array($x['status'], ['queued', 'running'], true)) return [$j, ['ok' => false, 'error' => 'That job already finished.']];
            if (!ws_is_owner() && ws_is_lt() && ($x['uid'] ?? '') !== ws_uid()) return [$j, ['ok' => false, 'error' => 'You can only cancel your own jobs.']];
            $left = max(0, (int)$x['takes'] - (int)$x['done'] - (int)$x['failed']);
            if ($x['status'] === 'queued') { $x['status'] = 'cancelled'; $x['finishedAt'] = ws_now(); ws_quota_release((string)$x['uid'], $left, (string)$x['day']); }
            else { $x['stopRequested'] = true; }
            return [$j, ['ok' => true]];
        }
        unset($x);
        return [$j, ['ok' => false, 'error' => 'Job not found.']];
    });
}
function ws_jobs_for(string $pid, int $limit = 30): array {
    $out = array_values(array_filter(ws_jobs_read()['jobs'], fn($x) => ($x['pid'] ?? '') === $pid));
    return array_slice(array_reverse($out), 0, $limit);
}
// Is a worker alive? (heartbeat within the last 10 minutes)
function ws_worker_alive(): bool { $m = ws_jobs_read()['meta']; return time() - (int)($m['workerSeenAt'] ?? 0) < 600; }

// ---- chat store ---------------------------------------------------------------------
function ws_chat(string $pid, int $sinceId = 0): array {
    $msgs = (array)(s_read(ws_file('chat', $pid), [])['msgs'] ?? []);
    if ($sinceId > 0) $msgs = array_values(array_filter($msgs, fn($m) => (int)($m['id'] ?? 0) > $sinceId));
    return $msgs;
}
// Append messages. Each gets a monotonically increasing integer id. Returns the stored rows.
function ws_chat_append(string $pid, array $rows): array {
    return s_with_lock(ws_file('chat', $pid), function ($c) use ($rows) {
        $c = is_array($c) ? $c : []; $c['msgs'] = (array)($c['msgs'] ?? []);
        $last = 0; foreach ($c['msgs'] as $m) $last = max($last, (int)($m['id'] ?? 0));
        $out = [];
        foreach ($rows as $r) { $r['id'] = ++$last; $r['ts'] = $r['ts'] ?? time(); $c['msgs'][] = $r; $out[] = $r; }
        if (count($c['msgs']) > 1500) $c['msgs'] = array_slice($c['msgs'], -1500);
        return ['data' => $c, 'result' => $out];
    });
}
// Update one message in place (e.g. an action card's status). $fn(array $msg): array $msg.
function ws_chat_patch(string $pid, int $id, callable $fn): ?array {
    return s_with_lock(ws_file('chat', $pid), function ($c) use ($id, $fn) {
        $c = is_array($c) ? $c : []; $c['msgs'] = (array)($c['msgs'] ?? []);
        foreach ($c['msgs'] as $i => $m) if ((int)($m['id'] ?? 0) === $id) { $c['msgs'][$i] = $fn($m); return ['data' => $c, 'result' => $c['msgs'][$i]]; }
        return ['result' => null];
    });
}

// ---- picks store ---------------------------------------------------------------------
function ws_picks(string $pid): array { $d = s_read(ws_file('picks', $pid), []); $d['pages'] = (array)($d['pages'] ?? []); return $d; }

// ---- Anthropic (chat brain) ------------------------------------------------------------
function ws_ai_key(): string { $c = s_read(SDATA . '/ai.json', []); return (string)($c['key'] ?? ''); }
// One Messages API call. $body is the request body without model. Returns
// ['ok'=>bool,'json'=>array|null,'error'=>?,'usd'=>float].
function ws_ai_call(array $body, int $timeout = 75): array {
    $key = ws_ai_key();
    if ($key === '') return ['ok' => false, 'json' => null, 'error' => 'No AI key installed in the Studio.', 'usd' => 0.0];
    $s = ws_settings();
    $body = array_merge(['model' => (string)$s['chatModel']], $body);
    $headers = ['content-type: application/json', 'x-api-key: ' . $key, 'anthropic-version: 2023-06-01'];
    if (preg_match('/^claude-(opus-5|sonnet-5-5|fable-5-1)/', (string)$body['model'])) {
        // Refusal fallback: let the API retry a declined request on its recommended model.
        $body['fallbacks'] = 'default';
        $headers[] = 'anthropic-beta: server-side-fallback-2026-07-01';
    }
    @set_time_limit($timeout + 20);
    $ch = curl_init('https://api.anthropic.com/v1/messages');
    curl_setopt_array($ch, [CURLOPT_POST => true, CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => $timeout,
        CURLOPT_HTTPHEADER => $headers, CURLOPT_POSTFIELDS => json_encode($body, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE)]);
    $resp = curl_exec($ch); $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE); $cerr = curl_error($ch); curl_close($ch);
    if ($resp === false || $resp === '') return ['ok' => false, 'json' => null, 'error' => 'Claude did not answer (' . ($cerr ?: 'network') . ').', 'usd' => 0.0];
    $j = json_decode((string)$resp, true);
    if ($code >= 400 || !is_array($j)) {
        $msg = is_array($j) ? (string)($j['error']['message'] ?? 'API error') : 'API error';
        return ['ok' => false, 'json' => $j, 'error' => "Claude error ($code): " . mb_substr($msg, 0, 200), 'usd' => 0.0];
    }
    return ['ok' => true, 'json' => $j, 'error' => null, 'usd' => ws_ai_cost($j)];
}
// Rough USD cost from usage (per-MTok input/output; cache reads at 10% of input).
function ws_ai_cost(array $j): float {
    $rates = ['claude-opus-5-5' => [4, 20], 'claude-sonnet-5-5' => [2, 10], 'claude-haiku-4-5' => [1, 5], 'claude-sonnet-4-6' => [3, 15], 'claude-opus-5' => [5, 25], 'claude-opus-4-8' => [5, 25]];
    $m = (string)($j['model'] ?? ''); $r = [4, 20];
    foreach ($rates as $k => $v) if (strpos($m, $k) === 0) { $r = $v; break; }
    $u = (array)($j['usage'] ?? []);
    $in = (int)($u['input_tokens'] ?? 0); $cw = (int)($u['cache_creation_input_tokens'] ?? 0); $cr = (int)($u['cache_read_input_tokens'] ?? 0);
    $out = (int)($u['output_tokens'] ?? 0);
    return round(($in * $r[0] + $cw * $r[0] * 1.25 + $cr * $r[0] * 0.1 + $out * $r[1]) / 1e6, 5);
}
// Concatenate the text blocks of a Messages response (skips thinking/fallback blocks).
function ws_ai_text(array $j): string {
    $t = '';
    foreach ((array)($j['content'] ?? []) as $b) if (($b['type'] ?? '') === 'text') $t .= (string)($b['text'] ?? '');
    return $t;
}
