<?php
// picker.php — the owner's picker format, inside the Studio (Lieutenant workspace, 2026-10-01).
// See studio/docs/LIEUTENANT-WORKSPACE.md, panel 5.
//
// Per page (= image group, e.g. "Page 03"): a grid of EVERY take; click a take to pick or
// unpick it (multi-pick); 🔍 opens a lightbox where ←/→ walk the takes of the page, ↑/↓ the
// pages, Enter/Space toggles the pick and Esc closes. Each page has a comment box (debounced
// autosave), a "Drop page" button, and Claude's pick (image tag 'judge-pick') tagged yellow.
// New takes come first, the take(s) picked earlier come last. The header has the counts, a
// "show settled (N)" toggle and "Copy list".
//
// Settled rule: a page's signature is sha1 of its sorted take file names. A page is "to do"
// when it has no picks record, when its record was saved against a different signature (new or
// removed takes), or when its pick is an empty list. Settled pages are hidden by default. When
// the signature changed, the old comment is shown greyed as "your last comment" above an empty
// box and is archived into prev_c on the next save.
//
// Store: data/ws/picks-<pid>.json pages{group:{pick:[files]|'drop', c, prev_c, sig, by, ts}}.
// A pick change is mirrored into images-<pid>.json (accepted/rating) so review.php, export.php
// and the cockpit see the same picks. A picked row records what the picker changed in pk {acc, r}
// (an owner 'bad' rating is never turned 'good'); un-picking restores only rows carrying pk: keeps
// made elsewhere in the Studio are never cleared from here. Comment-only saves never touch the images file.
// Lock order: picks lock first, images lock nested inside it (never the reverse).
//
// Endpoints (all need a Studio session; lieutenants only for their brand's comics via ws_gate):
//   GET  picker.php?p=<pid>              the page
//   GET  picker.php?do=sig&p=<pid>       {ok, img, picks}: cheap change stamps (mtime.size), polled every 20 s
//   POST picker.php  do=save p page [pick] [c] (+csrf) -> {ok, todo, rec, sigBefore, sig}
declare(strict_types=1);
require_once __DIR__ . '/inc/boot.php';

// ---- local helpers (ws_picker_ prefix; not shared) ---------------------------------------
function ws_picker_s($v): string { return is_string($v) ? $v : ((is_int($v) || is_float($v)) ? (string)$v : ''); }
// The page (group) a take belongs to. '' -> 'Ungrouped'. Capped at 80 chars (the POST limit).
function ws_picker_gkey(array $m): string { $g = trim(ws_picker_s($m['group'] ?? '')); return $g === '' ? 'Ungrouped' : mb_substr($g, 0, 80); }
// A pickable take: a real, non-reference, non-blueprint image row with a safe file name.
function ws_picker_is_take($m): bool {
    return is_array($m) && is_string($m['file'] ?? null) && empty($m['isref']) && empty($m['blueprint'])
        && preg_match('/^[A-Za-z0-9._-]+$/', $m['file']) === 1;
}
function ws_picker_page_files(array $imgs, string $page): array {
    $out = []; $seen = [];
    foreach ($imgs as $m) {
        if (!ws_picker_is_take($m) || ws_picker_gkey($m) !== $page) continue;
        $f = (string)$m['file'];
        if (!isset($seen[$f])) { $seen[$f] = 1; $out[] = $f; }
    }
    return $out;
}
function ws_picker_sig(array $files): string {
    $f = array_values(array_unique(array_map('strval', $files)));
    sort($f, SORT_STRING);
    return sha1(implode('|', $f));
}
// Normalize a stored/posted pick to 'drop' or a de-duplicated list of safe file names.
function ws_picker_pick_norm($p) {
    if ($p === 'drop') return 'drop';
    if (!is_array($p)) return [];
    $o = [];
    foreach ($p as $f) {
        if (!is_string($f)) continue;
        $f = basename($f);
        if ($f !== '' && preg_match('/^[A-Za-z0-9._-]+$/', $f) === 1 && !in_array($f, $o, true)) $o[] = $f;
    }
    return $o;
}
function ws_picker_same($a, $b): bool {
    if ($a === 'drop' || $b === 'drop') return $a === $b;
    $x = (array)$a; $y = (array)$b; sort($x, SORT_STRING); sort($y, SORT_STRING);
    return $x === $y;
}
// Cheap change stamp of a file: "mtime.size" (or '0' when missing). No JSON decode.
function ws_picker_stamp(string $f): string {
    clearstatcache(true, $f);
    return is_file($f) ? ((string)@filemtime($f) . '.' . (string)@filesize($f)) : '0';
}
function ws_picker_filesig(string $pid): array {
    return ['img' => ws_picker_stamp(imeta_path($pid)), 'picks' => ws_picker_stamp(ws_file('picks', $pid))];
}
function ws_picker_clean_c(string $s): string {
    $s = mb_scrub(substr($s, 0, 16000), 'UTF-8');
    $s = str_replace(["\r\n", "\r"], "\n", $s);
    $s = (string)preg_replace('/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/u', '', $s);
    return mb_substr(trim($s), 0, 2000);
}
function ws_picker_404(): void {
    http_response_code(404);
    header('Content-Type: text/html; charset=utf-8');
    header('Cache-Control: no-store');
    echo '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
       . '<meta name="robots" content="noindex,nofollow"><title>Picker</title><link rel="stylesheet" href="assets/studio.css"></head>'
       . '<body style="display:flex;min-height:100vh;align-items:center;justify-content:center;padding:16px">'
       . '<div class="card" style="max-width:420px;text-align:center"><p>That comic was not found, or it is not part of your workspace.</p>'
       . '<p><a class="btn" href="ws.php">Back to the workspace</a></p></div></body></html>';
    exit;
}

// ---- request routing ---------------------------------------------------------------------
$isPost = ($_SERVER['REQUEST_METHOD'] ?? 'GET') === 'POST';
$do     = ws_picker_s($_GET['do'] ?? ($_POST['do'] ?? null));
$isApi  = $isPost || $do !== '';
if ($isApi && !is_authed()) ws_json_out(['ok' => false, 'error' => 'You are signed out. Reload the page and sign in again.'], 401);
require_auth();

// Same precedence as ws_gate() (GET p first), and checked again here for every request.
$pid  = ws_pid(ws_picker_s($_GET['p'] ?? ($_POST['p'] ?? null)));
$proj = $pid !== '' ? project_get($pid) : null;
if (!$proj || !ws_can_see($pid)) {
    if ($isApi) ws_json_out(['ok' => false, 'error' => 'Comic not found.'], 404);
    ws_picker_404();
}

// ---- GET do=sig: change stamps for the 20 s poll (never decodes the images file) -----------
if (!$isPost && $do === 'sig') ws_json_out(['ok' => true] + ws_picker_filesig($pid));

// ---- POST do=save: pick and/or comment for one page ----------------------------------------
if ($isPost) {
    if (!csrf_ok()) ws_json_out(['ok' => false, 'error' => 'Your session token expired. Reload the page.'], 403);
    if ($do !== 'save') ws_json_out(['ok' => false, 'error' => 'Unknown action.'], 400);
    $sigBefore = ws_picker_filesig($pid);

    $page = mb_substr(trim(ws_picker_s($_POST['page'] ?? null)), 0, 80);
    if ($page === '') ws_json_out(['ok' => false, 'error' => 'Missing page.'], 400);

    // pick: optional. "drop", or a JSON array of take file names.
    $pickGiven = array_key_exists('pick', $_POST);
    $newPick = [];
    if ($pickGiven) {
        $raw = trim(ws_picker_s($_POST['pick']));
        $dec = $raw === 'drop' ? 'drop' : json_decode($raw, true);
        if ($dec === 'drop') {
            $newPick = 'drop';
        } else {
            if (!is_array($dec) || !array_is_list($dec) || count($dec) > 500) ws_json_out(['ok' => false, 'error' => 'Bad pick list.'], 400);
            foreach ($dec as $f) {
                $f = is_string($f) ? basename($f) : '';
                if ($f === '' || preg_match('/^[A-Za-z0-9._-]+$/', $f) !== 1) ws_json_out(['ok' => false, 'error' => 'Bad file name in pick.'], 400);
                if (!in_array($f, $newPick, true)) $newPick[] = $f;
            }
        }
    }
    // c: optional comment (≤ 2000 chars).
    $cGiven = array_key_exists('c', $_POST);
    $newC = $cGiven ? ws_picker_clean_c(ws_picker_s($_POST['c'])) : '';
    if (!$pickGiven && !$cGiven) ws_json_out(['ok' => false, 'error' => 'Nothing to save.'], 400);

    // Lock order for the whole save: picks lock FIRST, then (nested) the images lock — never the
    // reverse anywhere, so two saves (or a page delete) cannot deadlock or interleave. The previous
    // pick is read inside the picks lock, so the mirror below always undoes the pick that was really stored.
    $by  = current_studio_user();
    $sig = ''; $err = null;
    $rec = s_with_lock(ws_file('picks', $pid), function ($d) use ($pid, $page, $by, $pickGiven, $newPick, $cGiven, $newC, &$sig, &$err) {
        $d = is_array($d) ? $d : [];
        $d['pages'] = is_array($d['pages'] ?? null) ? $d['pages'] : [];
        $old = is_array($d['pages'][$page] ?? null) ? $d['pages'][$page] : null;
        $oldPick = $old ? ws_picker_pick_norm($old['pick'] ?? []) : [];
        $pickChanged = $pickGiven && !ws_picker_same($newPick, $oldPick);

        if ($pickChanged) {
            // Validate + mirror under the images lock in ONE read (images-<pid>.json can be tens of MB).
            // Same lock images_update() takes; called directly so an invalid pick aborts WITHOUT a rewrite.
            //
            // The picker only ever undoes what it set itself. Picking a take records on the row what the
            // pick changed — pk = {acc: old accepted, r: old rating} — the first time it flips anything;
            // an owner 'bad' is never overwritten with 'good'. Un-picking (or dropping the page) restores
            // ONLY rows carrying pk, and only the fields still holding the picker's value; rows without pk
            // (kept in review.php / the cockpit) are left exactly as they are.
            s_with_lock(imeta_path($pid), function ($meta) use ($page, $newPick, &$sig, &$err) {
                $meta  = is_array($meta) ? $meta : [];
                $files = ws_picker_page_files($meta, $page);
                if (!$files) { $err = 'That page has no takes.'; return ['result' => null]; }
                if ($newPick !== 'drop') {
                    foreach ($newPick as $f) if (!in_array($f, $files, true)) { $err = 'Take ' . $f . ' is not on ' . $page . '.'; return ['result' => null]; }
                }
                $sig    = ws_picker_sig($files);
                $picked = $newPick === 'drop' ? [] : $newPick;
                foreach ($meta as $i => $m) {
                    if (!ws_picker_is_take($m) || ws_picker_gkey($m) !== $page) continue;
                    $f  = (string)$m['file'];
                    $pk = is_array($m['pk'] ?? null) ? $m['pk'] : null;
                    if (in_array($f, $picked, true)) {
                        $oa = !empty($m['accepted']);
                        $or = array_key_exists('rating', $m) ? $m['rating'] : null;
                        $nr = $or === 'bad' ? 'bad' : 'good';
                        if ($pk === null && (!$oa || $or !== $nr)) $meta[$i]['pk'] = ['acc' => $oa, 'r' => $or];
                        $meta[$i]['accepted'] = true;
                        $meta[$i]['rating']   = $nr;
                    } elseif ($pk !== null) {
                        $pr = $pk['r'] ?? null;
                        if (!empty($m['accepted'])) $meta[$i]['accepted'] = !empty($pk['acc']);
                        if (($m['rating'] ?? null) === ($pr === 'bad' ? 'bad' : 'good')) {
                            if ($pr === null) unset($meta[$i]['rating']); else $meta[$i]['rating'] = $pr;
                        }
                        unset($meta[$i]['pk']);
                    }
                }
                return ['data' => $meta, 'result' => null];
            });
        } else {
            $imgs  = images_all($pid);
            $files = ws_picker_page_files(is_array($imgs) ? $imgs : [], $page);
            unset($imgs);
            if (!$files) $err = 'That page has no takes.';
            else $sig = ws_picker_sig($files);
        }
        if ($err !== null) return ['result' => null];   // nothing written; the lock is released normally

        $oc  = $old ? ws_picker_s($old['c'] ?? '') : '';
        $pc  = $old ? ws_picker_s($old['prev_c'] ?? '') : '';
        $c   = $oc;
        // The takes changed since that comment was written: archive it as "your last comment".
        if ($old && ws_picker_s($old['sig'] ?? '') !== $sig && $oc !== '') { $pc = $oc; $c = ''; }
        if ($cGiven) $c = $newC;
        $pick = $pickGiven ? $newPick : $oldPick;
        $r = array_merge($old ?? [], ['pick' => $pick, 'c' => $c, 'prev_c' => $pc, 'sig' => $sig, 'by' => $by, 'ts' => time()]);
        $d['pages'][$page] = $r;
        return ['data' => $d, 'result' => $r];
    });
    if ($err !== null || !is_array($rec)) ws_json_out(['ok' => false, 'error' => $err ?? 'Not saved.'], 400);

    $todo = is_array($rec['pick']) && count($rec['pick']) === 0;
    ws_json_out([
        'ok' => true, 'todo' => $todo,
        'rec' => ['pick' => $rec['pick'], 'c' => $rec['c'], 'prev_c' => $rec['prev_c'], 'by' => $rec['by'], 'ts' => $rec['ts']],
        'sigBefore' => $sigBefore, 'sig' => ws_picker_filesig($pid),
    ]);
}
if ($do !== '') ws_json_out(['ok' => false, 'error' => 'Unknown action.'], 400);

// ---- GET: build the page data ------------------------------------------------------------
$fsig  = ws_picker_filesig($pid);          // stamp BEFORE reading, so a write mid-render triggers the toast, never hides
$picks = ws_picks($pid)['pages'];
$imgs  = images_all($pid);                 // loaded ONCE
$byPage = []; $seen = [];
foreach ((is_array($imgs) ? $imgs : []) as $m) {
    if (!ws_picker_is_take($m)) continue;
    $g = ws_picker_gkey($m); $f = (string)$m['file'];
    if (strncmp($g, 'Deleted Page ', 13) === 0) continue;   // takes of a page deleted in the workspace (ws-api page_delete): not a page to pick
    if (isset($seen[$g . "\0" . $f])) continue;
    $seen[$g . "\0" . $f] = 1;
    $tags = is_array($m['tags'] ?? null) ? $m['tags'] : [];
    $byPage[$g][] = [
        'f'    => $f,
        'ts'   => (int)($m['ts'] ?? 0),
        'cl'   => in_array('judge-pick', $tags, true),
        'acc'  => !empty($m['accepted']),
        'p'    => mb_substr(trim(ws_picker_s($m['prompt'] ?? '')), 0, 300),
    ];
}
unset($imgs, $seen);

// Natural order: Page 01 < Page 02 < Page 10, Beat 2 < Beat 10; 'Ungrouped' last.
$keys = array_map('strval', array_keys($byPage));
usort($keys, function (string $a, string $b): int {
    $ua = $a === 'Ungrouped'; $ub = $b === 'Ungrouped';
    if ($ua !== $ub) return $ua ? 1 : -1;
    return strnatcasecmp($a, $b) ?: strcmp($a, $b);
});

$pages = []; $nTodo = 0; $nSettled = 0;
foreach ($keys as $g) {
    $takes = $byPage[$g];
    $files = array_column($takes, 'f');
    $sig   = ws_picker_sig($files);
    $rec   = is_array($picks[$g] ?? null) ? $picks[$g] : null;
    $rawPick = $rec ? ws_picker_pick_norm($rec['pick'] ?? []) : [];
    $stale = $rec !== null && ws_picker_s($rec['sig'] ?? '') !== $sig;
    $todo  = $rec === null || $stale || (is_array($rawPick) && count($rawPick) === 0);
    // Only takes still on the page can show as picked.
    $pick  = is_array($rawPick) ? array_values(array_filter($rawPick, fn($f) => in_array($f, $files, true))) : 'drop';
    // "Previously picked" goes last: the record's pick, or (no record yet) takes kept elsewhere in the Studio.
    $prev  = $rec !== null ? (is_array($pick) ? $pick : []) : array_column(array_filter($takes, fn($t) => $t['acc']), 'f');
    $prevSet = array_fill_keys($prev, true);
    usort($takes, function (array $a, array $b) use ($prevSet): int {
        $pa = isset($prevSet[$a['f']]); $pb = isset($prevSet[$b['f']]);
        if ($pa !== $pb) return $pa ? 1 : -1;
        return ($b['ts'] <=> $a['ts']) ?: strcmp($a['f'], $b['f']);
    });
    $recTs = $rec ? (int)($rec['ts'] ?? 0) : 0;
    $out = [];
    foreach ($takes as $t) {
        $row = ['f' => $t['f'], 'ts' => $t['ts'], 'cl' => $t['cl'], 'p' => $t['p']];
        if ($rec === null && $t['acc']) $row['k'] = true;              // kept in review/cockpit, no picker record yet
        if ($rec !== null && $stale && $t['ts'] > $recTs) $row['n'] = true;  // landed after the last pick
        $out[] = $row;
    }
    $c   = $rec ? ws_picker_s($rec['c'] ?? '') : '';
    $pc  = $rec ? ws_picker_s($rec['prev_c'] ?? '') : '';
    $pages[] = [
        'g' => $g, 'todo' => $todo, 'stale' => $stale, 'rec' => $rec !== null, 'pick' => $pick,
        'c' => $stale ? '' : $c, 'last' => ($stale && $c !== '') ? $c : $pc,
        'by' => $rec ? ws_picker_s($rec['by'] ?? '') : '', 'ts' => $recTs, 'takes' => $out,
    ];
    if ($todo) $nTodo++; else $nSettled++;
}
unset($byPage);

$pname = trim(ws_picker_s($proj['name'] ?? '')) ?: $pid;
$isLt  = ws_is_lt();
$asp   = (string)(ws_proj($pid)['aspect'] ?? '3:4');
$ar    = preg_match('/^(\d{1,2}):(\d{1,2})$/', $asp, $mm) && (int)$mm[1] > 0 && (int)$mm[2] > 0 ? ((int)$mm[1] . ' / ' . (int)$mm[2]) : '3 / 4';
$boot  = ['pid' => $pid, 'name' => $pname, 'sig' => $fsig, 'pages' => $pages];
$bootJson = json_encode($boot, JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT | JSON_UNESCAPED_UNICODE | JSON_INVALID_UTF8_SUBSTITUTE) ?: '{}';
$cssv  = (string)(@filemtime(STUDIO_ROOT . '/assets/studio.css') ?: '1');

header('Content-Type: text/html; charset=utf-8');
header('Cache-Control: no-store');
header('X-Robots-Tag: noindex');
?><!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><meta name="color-scheme" content="dark">
<meta name="robots" content="noindex,nofollow"><title><?= h($pname) ?> · Picker</title>
<link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="assets/studio.css?v=<?= h($cssv) ?>">
<style>
:root{--pick:#ff3b3b;--cl:#f5c542}
body.pk-noscroll{overflow:hidden}
.pk-top{gap:14px;padding:0 16px}
.pk-badge{background:var(--pick);color:#fff;font-size:11px;font-weight:800;letter-spacing:.04em;border-radius:999px;padding:2px 9px;margin-left:6px}
.pk-bar{position:sticky;top:56px;z-index:25;background:rgba(11,12,16,.94);backdrop-filter:blur(6px);-webkit-backdrop-filter:blur(6px);border-bottom:1px solid var(--border);padding:10px 16px;display:flex;flex-wrap:wrap;gap:8px 14px;align-items:center}
.pk-title{display:flex;align-items:baseline;gap:6px 12px;flex-wrap:wrap;min-width:0;flex:1 1 320px}
.pk-title h1{font-size:19px;margin:0;min-width:0;max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.pk-counts{color:var(--muted);font-size:13px}.pk-counts b{color:var(--text)}
.pk-tools{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.pk-tools .btn{padding:8px 12px}
.pk-tools .btn.on{background:#3a2d5e;color:#cdb6ff;border-color:#4a3d6e}
.pk-status{font-size:12.5px;color:var(--muted);min-width:70px}
.pk-status.err{color:#f3a3a2}
.pk-help{flex-basis:100%;font-size:12px;color:var(--muted2);margin:0}
.pk-help b{color:var(--cl);font-weight:700}.pk-help i{font-style:normal;color:#ff8a8a;font-weight:700}
.pk-wrap{max-width:1560px;margin:0 auto;padding:4px 16px 96px}
.pk-page{padding:16px 0 18px;border-bottom:1px solid var(--border);scroll-margin-top:150px}
.pk-page.flash{animation:pkflash 1.6s ease}
@keyframes pkflash{0%,40%{background:rgba(239,159,39,.10)}100%{background:transparent}}
.pk-page.dropped .pk-grid{opacity:.35}
.pk-phead{display:flex;align-items:center;gap:6px 10px;flex-wrap:wrap;margin-bottom:8px}
.pk-phead h2{margin:0;font-size:18px;overflow-wrap:anywhere}
.pk-chip{font:800 10.5px/1 Inter,sans-serif;padding:4px 8px;border-radius:999px;letter-spacing:.03em;text-transform:uppercase}
.pk-chip.todo{background:rgba(239,159,39,.16);color:var(--accent)}
.pk-chip.new{background:rgba(29,158,117,.18);color:#6fe0bd}
.pk-chip.ok{background:var(--surface2);color:var(--muted)}
.pk-chip.err{background:rgba(226,75,74,.2);color:#f3a3a2}
.pk-sub{color:var(--muted);font-size:13px}
.pk-btn{border:1px solid var(--border2);background:var(--surface2);color:var(--text);font:600 12.5px/1 Inter,sans-serif;padding:7px 11px;border-radius:8px;cursor:pointer}
.pk-btn:hover{border-color:#3c4052}
.pk-btn[hidden]{display:none}
.pk-link{color:var(--muted2);font-size:14px;padding:4px 6px;border-radius:6px}
.pk-link:hover{color:var(--text);background:var(--surface2)}
.pk-last{font-size:12.5px;color:var(--muted2);border-left:2px solid var(--border2);padding:2px 0 2px 9px;margin:2px 0 8px;white-space:pre-wrap;overflow-wrap:anywhere}
.pk-last b{color:var(--muted);font-weight:600}
.pk-last[hidden]{display:none}
textarea.pk-ta{min-height:44px;margin:0 0 10px;font:14px/1.45 Inter,system-ui,sans-serif;padding:8px 10px}
.pk-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:10px}
.pk-cell{position:relative;background:var(--surface);border-radius:8px;overflow:hidden;cursor:pointer;outline:4px solid transparent;outline-offset:-4px;transition:outline-color .1s;-webkit-tap-highlight-color:transparent}
.pk-cell:hover{outline-color:#666}
.pk-cell.sel{outline-color:var(--pick)}
.pk-cell:focus-visible{box-shadow:0 0 0 3px #7A7FEC}
.pk-img{display:block;width:100%;aspect-ratio:var(--ar,3 / 4);object-fit:contain;background:#000;user-select:none;-webkit-user-select:none}
.pk-tag{position:absolute;top:6px;left:6px;background:#000c;color:#fff;padding:2px 7px;border-radius:5px;font-weight:700;font-size:13px}
.pk-cell.sel .pk-tag{background:var(--pick)}
.pk-cl{position:absolute;top:6px;right:6px;background:var(--cl);color:#000;padding:2px 6px;border-radius:5px;font-size:11px;font-weight:700}
.pk-new,.pk-kept{position:absolute;bottom:8px;left:6px;padding:2px 6px;border-radius:5px;font:800 10px/1.3 Inter,sans-serif;letter-spacing:.04em}
.pk-new{background:var(--teal);color:#04130d}
.pk-kept{background:#000c;color:#6fe0bd;border:1px solid rgba(29,158,117,.6)}
.pk-zoom{position:absolute;bottom:6px;right:6px;background:#000b;color:#fff;border:0;border-radius:6px;padding:5px 9px;font-size:14px;line-height:1;cursor:pointer}
.pk-zoom:hover{background:#000}
.pk-empty{border:1px dashed var(--border2);border-radius:12px;padding:34px 18px;text-align:center;color:var(--muted);margin-top:18px}
.pk-empty[hidden]{display:none}
.pk-empty p{margin:0 0 12px}
/* lightbox */
.pk-lb{position:fixed;inset:0;z-index:200;background:rgba(0,0,0,.95);display:flex;flex-direction:column}
.pk-lb[hidden]{display:none}
.pk-lbstage{flex:1;min-height:0;display:flex;align-items:center;justify-content:center;padding:12px}
.pk-lbimg{max-width:96vw;max-height:100%;object-fit:contain;outline:6px solid transparent;cursor:zoom-out}
.pk-lbimg.sel{outline-color:var(--pick)}
.pk-lbbar{background:#000c;border-top:1px solid #222;padding:8px 12px calc(10px + env(safe-area-inset-bottom));display:flex;flex-direction:column;align-items:center;gap:6px}
.pk-lbinfo{font-size:14px;text-align:center;color:#fff}
.pk-lbinfo .pk-on{color:#ff8a8a}.pk-lbinfo .pk-c{color:var(--cl)}
.pk-lbprompt{font-size:12px;color:var(--muted);max-width:980px;text-align:center;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.pk-lbprompt[hidden]{display:none}
.pk-lbkeys{font-size:11.5px;color:var(--muted2)}
.pk-lbbtns{display:flex;gap:6px;flex-wrap:wrap;justify-content:center}
.pk-lbbtns button{background:#26272e;color:#fff;border:1px solid #444;border-radius:8px;padding:8px 12px;font:600 13px/1 Inter,sans-serif;cursor:pointer;min-width:44px}
.pk-lbbtns button:hover{background:#33343c}
.pk-lbbtns button.pk-lbpick{min-width:120px}
.pk-lbbtns button.pk-lbpick.on{background:var(--pick);border-color:transparent}
.pk-lbx{position:absolute;top:10px;right:12px;background:#000b;color:#fff;border:1px solid #444;border-radius:8px;width:40px;height:40px;font-size:18px;cursor:pointer}
/* toast */
.pk-toast{position:fixed;left:50%;bottom:22px;transform:translateX(-50%);z-index:250;background:var(--teal);color:#04130d;font:800 13px/1.2 Inter,sans-serif;padding:10px 12px 10px 16px;border-radius:999px;box-shadow:0 6px 20px rgba(0,0,0,.45);display:none;align-items:center;gap:10px;cursor:pointer;max-width:calc(100% - 32px)}
.pk-toast.show{display:flex}
.pk-toast.err{background:var(--red);color:#fff}
.pk-toastx{background:transparent;border:0;color:inherit;opacity:.65;font-size:18px;line-height:1;cursor:pointer;padding:0 4px}
@media(max-width:700px){
  .pk-grid{grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:8px}
  .pk-bar{position:static}
  .pk-page{scroll-margin-top:66px}
  .pk-hide-sm{display:none}
  .pk-lbkeys{display:none}
  .pk-lbimg{max-width:100%}
  .pk-lbstage{padding:6px}
  .pk-lbbtns{flex-wrap:nowrap;gap:5px}
  .pk-lbbtns button{padding:8px 9px;min-width:40px}
  .pk-lbbtns button.pk-lbpick{min-width:84px}
}
</style>
<?php if (!$isLt): ?><!-- the one bar across every system (owner + staff only). Source: /hub/nav.js -->
<script src="https://3dmusclecomics.com/hub/nav.js"></script>
<?php endif; ?>
</head><body>
<header class="topbar pk-top">
  <div class="brand"><span class="dot"></span><span class="pk-hide-sm">Comic Studio</span><span class="pk-badge">🎯 PICKER</span></div>
  <a class="ghost" href="ws.php?p=<?= h(urlencode($pid)) ?>">← Workspace</a>
  <?php if (!$isLt): ?><a class="ghost pk-hide-sm" href="review.php?p=<?= h(urlencode($pid)) ?>">🖼 Review</a><?php endif; ?>
  <span class="spacer"></span>
  <span class="ghost pk-hide-sm"><?= h(current_studio_user()) ?></span>
  <a class="ghost pk-hide-sm" href="help.php">❔ Help</a>
  <a class="ghost" href="login.php?do=logout">Log out</a>
</header>

<div id="pk" data-csrf="<?= h(csrf()) ?>" style="--ar:<?= h($ar) ?>">
  <div class="pk-bar">
    <div class="pk-title"><h1 title="<?= h($pname) ?>"><?= h($pname) ?></h1><span class="pk-counts" id="counts"></span></div>
    <div class="pk-tools">
      <button type="button" class="btn" id="tgl" aria-pressed="false">show settled (<?= (int)$nSettled ?>)</button>
      <button type="button" class="btn primary" id="copy">Copy list</button>
      <span class="pk-status" id="status" role="status" aria-live="polite"></span>
    </div>
    <p class="pk-help pk-hide-sm">Click = pick / unpick (pick as many as you like per page) · 🔍 = enlarge · <b>yellow tag = Claude's pick</b> · new takes first, your earlier pick last · <i>red = picked</i></p>
  </div>
  <main class="pk-wrap" id="m"></main>
  <div class="pk-wrap"><div class="pk-empty" id="empty" hidden></div></div>
</div>

<div class="pk-lb" id="lb" hidden role="dialog" aria-modal="true" aria-label="Take viewer">
  <button type="button" class="pk-lbx" id="lbx" aria-label="Close">✕</button>
  <div class="pk-lbstage" id="lbstage"><img class="pk-lbimg" id="lbimg" alt=""></div>
  <div class="pk-lbbar">
    <div class="pk-lbinfo" id="lbinfo"></div>
    <div class="pk-lbprompt" id="lbprompt" hidden></div>
    <div class="pk-lbbtns">
      <button type="button" id="lbup" aria-label="Previous page">▲ page</button>
      <button type="button" id="lbprev" aria-label="Previous take">◀</button>
      <button type="button" class="pk-lbpick" id="lbpick">Pick</button>
      <button type="button" id="lbnext" aria-label="Next take">▶</button>
      <button type="button" id="lbdown" aria-label="Next page">page ▼</button>
    </div>
    <div class="pk-lbkeys">←/→ takes · ↑/↓ pages · Enter/Space = pick/unpick · Esc = close</div>
  </div>
</div>
<div class="pk-toast" id="toast" role="status" aria-live="polite"></div>

<script type="application/json" id="pkdata"><?= $bootJson ?></script>
<script>
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  let D = {};
  try { D = JSON.parse($('pkdata').textContent || '{}') || {}; } catch (e) { D = {}; }
  const root = $('pk');
  const PID = String(D.pid || '');
  const NAME = String(D.name || PID);
  const CSRF = root.dataset.csrf || '';
  const PAGES = Array.isArray(D.pages) ? D.pages : [];
  let BASE = Object.assign({ img: '', picks: '' }, D.sig || {});
  const main = $('m'), st = $('status'), toastEl = $('toast'), tgl = $('tgl'), emptyEl = $('empty');
  let showSettled = false;

  const imgUrl = (f, thumb) => 'img.php?p=' + encodeURIComponent(PID) + '&f=' + encodeURIComponent(f) + (thumb ? '&t=1' : '');
  const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = String(text); return e; };
  const pickArr = p => Array.isArray(p.pick) ? p.pick : [];
  const isPicked = (p, f) => pickArr(p).indexOf(f) >= 0;
  const visible = p => !p.settled0 || showSettled || p.forced;
  const claudeFiles = p => p.takes.filter(t => t.cl).map(t => t.f);
  const pickedNums = p => p.takes.map((t, i) => isPicked(p, t.f) ? '#' + (i + 1) : '').filter(Boolean);
  const ago = ts => {
    if (!ts) return '';
    const s = Math.max(0, Date.now() / 1000 - ts);
    if (s < 90) return 'just now';
    if (s < 3600) return Math.round(s / 60) + ' min ago';
    if (s < 86400) return Math.round(s / 3600) + ' h ago';
    return Math.round(s / 86400) + ' d ago';
  };
  const status = (msg, kind) => { st.textContent = msg || ''; st.className = 'pk-status' + (kind ? ' ' + kind : ''); };

  PAGES.forEach((p, i) => {
    p.i = i;
    p.g = String(p.g);
    p.takes = Array.isArray(p.takes) ? p.takes : [];
    if (p.pick !== 'drop' && !Array.isArray(p.pick)) p.pick = [];
    p.settled0 = !p.todo;
    p.forced = false; p.built = false; p.dirtyC = false; p.timer = 0; p.unsaved = false;
    p.newN = p.takes.filter(t => t.n).length;
  });

  // ---------- sections ----------
  function buildShell(p) {
    const s = el('section', 'pk-page'); s.hidden = true; s.dataset.i = String(p.i); p.el = s;
    const head = el('div', 'pk-phead');
    head.appendChild(el('h2', null, p.g));
    p.chip = el('span', 'pk-chip'); head.appendChild(p.chip);
    p.sub = el('span', 'pk-sub'); head.appendChild(p.sub);
    head.appendChild(el('span', 'spacer'));
    p.keepBtn = el('button', 'pk-btn', '✓ Keep pick'); p.keepBtn.type = 'button';
    p.keepBtn.title = 'New takes landed but your earlier pick stands: mark this page done';
    p.keepBtn.addEventListener('click', () => savePick(p));
    p.dropBtn = el('button', 'pk-btn'); p.dropBtn.type = 'button';
    p.dropBtn.addEventListener('click', () => {
      p.pick = p.pick === 'drop' ? claudeFiles(p) : 'drop';
      refresh(p); counts(); savePick(p);
    });
    const link = el('a', 'pk-link', '🔗'); link.href = '#page=' + encodeURIComponent(p.g); link.title = 'Link to this page';
    head.appendChild(p.keepBtn); head.appendChild(p.dropBtn); head.appendChild(link);
    s.appendChild(head);
    p.lastEl = el('div', 'pk-last'); s.appendChild(p.lastEl);
    p.ta = el('textarea', 'pk-ta'); p.ta.rows = 1; p.ta.maxLength = 2000;
    p.ta.placeholder = 'Comment for Claude on this page (saved automatically)…';
    p.ta.setAttribute('aria-label', 'Comment on ' + p.g);
    p.ta.value = String(p.c || '');
    p.ta.addEventListener('input', () => { p.dirtyC = true; clearTimeout(p.timer); p.timer = setTimeout(() => saveComment(p), 700); status('typing…'); });
    p.ta.addEventListener('blur', () => { if (p.dirtyC) saveComment(p); });
    s.appendChild(p.ta);
    p.grid = el('div', 'pk-grid'); s.appendChild(p.grid);
    main.appendChild(s);
  }

  function fillGrid(p) {
    if (p.built) return;
    p.built = true; p.cells = [];
    const frag = document.createDocumentFragment();
    p.takes.forEach((t, i) => {
      const c = el('div', 'pk-cell'); c.tabIndex = 0; c.setAttribute('role', 'button'); c.dataset.k = String(i);
      const im = el('img', 'pk-img'); im.loading = 'lazy'; im.decoding = 'async'; im.draggable = false;
      im.alt = p.g + ' take #' + (i + 1); im.src = imgUrl(t.f, true);
      c.appendChild(im);
      c.appendChild(el('span', 'pk-tag', '#' + (i + 1)));
      if (t.cl) c.appendChild(el('span', 'pk-cl', 'Claude'));
      if (t.n) c.appendChild(el('span', 'pk-new', 'NEW'));
      else if (t.k) c.appendChild(el('span', 'pk-kept', 'KEPT'));
      const z = el('button', 'pk-zoom', '🔍'); z.type = 'button'; z.setAttribute('aria-label', 'Enlarge take #' + (i + 1));
      c.appendChild(z);
      p.cells.push(c); frag.appendChild(c);
    });
    p.grid.appendChild(frag);
    refresh(p);
  }

  function refresh(p) {
    const drop = p.pick === 'drop';
    p.el.classList.toggle('dropped', drop);
    if (p.cells) p.cells.forEach((c, i) => {
      const on = isPicked(p, p.takes[i].f);
      c.classList.toggle('sel', on);
      c.setAttribute('aria-pressed', on ? 'true' : 'false');
      c.querySelector('.pk-tag').textContent = '#' + (i + 1) + (on ? ' ✔' : '');
    });
    let chip, cc;
    if (p.unsaved) { chip = 'not saved'; cc = 'err'; }
    else if (!p.todo) { chip = 'settled ✓'; cc = 'ok'; }
    else if (p.stale) { chip = p.newN ? p.newN + ' new take' + (p.newN === 1 ? '' : 's') : 'takes changed'; cc = 'new'; }
    else { chip = 'to do'; cc = 'todo'; }
    p.chip.textContent = chip; p.chip.className = 'pk-chip ' + cc;
    const n = p.takes.length;
    let sub = n + ' take' + (n === 1 ? '' : 's') + ' · ';
    sub += drop ? 'DROPPED' : (pickArr(p).length ? 'picked ' + pickedNums(p).join(', ') : 'no pick yet');
    if (p.by) sub += ' · ' + p.by + (p.ts ? ' ' + ago(p.ts) : '');
    p.sub.textContent = sub;
    p.dropBtn.textContent = drop ? 'Restore page' : 'Drop page';
    p.keepBtn.hidden = !(p.todo && p.stale && (drop || pickArr(p).length > 0));
    p.lastEl.textContent = '';
    p.lastEl.hidden = !p.last;
    if (p.last) { p.lastEl.appendChild(el('b', null, 'your last comment: ')); p.lastEl.appendChild(document.createTextNode(String(p.last))); }
  }

  function counts() {
    const n = PAGES.length;
    const todo = PAGES.filter(p => p.todo).length;
    const picked = PAGES.filter(p => pickArr(p).length > 0).length;
    const dropped = PAGES.filter(p => p.pick === 'drop').length;
    const c = $('counts'); c.textContent = '';
    const parts = [[n, n === 1 ? 'page' : 'pages'], [todo, 'to do'], [picked, 'picked']];
    if (dropped) parts.push([dropped, 'dropped']);
    parts.forEach((x, i) => {
      if (i) c.appendChild(document.createTextNode(' · '));
      c.appendChild(el('b', null, x[0])); c.appendChild(document.createTextNode(' ' + x[1]));
    });
  }

  function applyVis() {
    let shown = 0;
    PAGES.forEach(p => { const v = visible(p); if (v) { fillGrid(p); shown++; } p.el.hidden = !v; });
    const nSettled = PAGES.filter(p => p.settled0).length;
    tgl.textContent = (showSettled ? 'hide settled' : 'show settled') + ' (' + nSettled + ')';
    tgl.classList.toggle('on', showSettled);
    tgl.setAttribute('aria-pressed', showSettled ? 'true' : 'false');
    tgl.disabled = nSettled === 0;
    emptyEl.textContent = '';
    if (!PAGES.length) {
      emptyEl.appendChild(el('p', null, 'No takes yet. Generate or upload takes from the workspace, then come back to pick.'));
      const a = el('a', 'btn', '← Back to the workspace'); a.href = 'ws.php?p=' + encodeURIComponent(PID); emptyEl.appendChild(a);
      emptyEl.hidden = false;
    } else if (!shown) {
      emptyEl.appendChild(el('p', null, 'Nothing to pick right now: all ' + PAGES.length + ' pages are settled.'));
      const b = el('button', 'btn', 'show settled (' + nSettled + ')'); b.type = 'button';
      b.addEventListener('click', () => { showSettled = true; applyVis(); });
      emptyEl.appendChild(b);
      emptyEl.hidden = false;
    } else emptyEl.hidden = true;
  }

  // ---------- saving (serialized, so replies arrive in order) ----------
  let chain = Promise.resolve(), inflight = 0, saveGen = 0;
  const changed = { img: false, picks: false };
  // inflight counts queued + running saves, so the poll never mistakes our own write for someone else's.
  function doFetch(fields, keepalive) {
    const body = new URLSearchParams(Object.assign({ do: 'save', p: PID, csrf: CSRF }, fields));
    const bad = r => ({ ok: false, status: r.status, error: 'Unexpected reply (HTTP ' + r.status + '). Not saved.' });
    return fetch('picker.php?p=' + encodeURIComponent(PID), {
      method: 'POST', body: body, credentials: 'same-origin', keepalive: !!keepalive,
      headers: { 'X-CSRF': CSRF, 'Accept': 'application/json' }
    })
      .then(r => r.json().then(j => (j && typeof j === 'object') ? Object.assign({ status: r.status }, j) : bad(r), () => bad(r)))
      .catch(() => ({ ok: false, status: 0, error: 'Network error. Not saved; check your connection.' }));
  }
  function post(fields, keepalive) {          // direct (used for the keepalive flush when the tab hides)
    inflight++; saveGen++;
    return doFetch(fields, keepalive).then(j => { inflight--; return j; });
  }
  function send(fields) {                     // serialized: replies arrive in the order they were sent
    inflight++; saveGen++;
    const run = () => doFetch(fields, false);
    const pr = chain.then(run, run).then(j => { inflight--; return j; });
    chain = pr;
    return pr;
  }
  function onReply(p, j) {
    if (j.ok) {
      p.unsaved = false; p.todo = !!j.todo; p.stale = false;
      if (j.rec) {
        p.by = String(j.rec.by || p.by || ''); p.ts = +j.rec.ts || p.ts; p.last = String(j.rec.prev_c || '');
        // Server archived the comment (takes changed under us): mirror it unless the user is mid-edit.
        if (!p.dirtyC && document.activeElement !== p.ta && typeof j.rec.c === 'string' && j.rec.c !== p.ta.value.trim()) p.ta.value = j.rec.c;
      }
      if (j.sigBefore && j.sig) {
        if (j.sigBefore.img !== BASE.img) changed.img = true;
        if (j.sigBefore.picks !== BASE.picks) changed.picks = true;
        BASE = { img: String(j.sig.img), picks: String(j.sig.picks) };
        showChangeToast();
      }
      status('✔ saved ' + new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
    } else {
      p.unsaved = true;
      status('✖ ' + (j.error || 'Not saved.'), 'err');
      if (j.status === 401 || j.status === 403) toast(String(j.error || 'Session expired.') + ' Tap to reload.', 'err', () => location.reload());
    }
    refresh(p); counts();
  }
  function savePick(p) {
    const f = { page: p.g, pick: p.pick === 'drop' ? 'drop' : JSON.stringify(pickArr(p)) };
    if (p.dirtyC) { clearTimeout(p.timer); p.dirtyC = false; f.c = p.ta.value; }
    status('saving…');
    send(f).then(j => { if (!j.ok && 'c' in f) p.dirtyC = true; onReply(p, j); });
  }
  function saveComment(p, keepalive) {
    clearTimeout(p.timer);
    if (!p.dirtyC) return;
    p.dirtyC = false;
    const f = { page: p.g, c: p.ta.value };
    status('saving…');
    (keepalive ? post(f, true) : send(f)).then(j => { if (!j.ok) p.dirtyC = true; onReply(p, j); });
  }
  const flushAll = keepalive => PAGES.forEach(p => { if (p.dirtyC) saveComment(p, keepalive); });

  function toggle(p, f) {
    const a = pickArr(p).slice(); const k = a.indexOf(f);
    if (k >= 0) a.splice(k, 1); else a.push(f);
    p.pick = a;
    refresh(p); counts(); savePick(p);
    if (LB && LB.p === p) lbShow();
  }

  // ---------- grid events (delegated) ----------
  main.addEventListener('click', e => {
    const c = e.target.closest('.pk-cell'); if (!c) return;
    const p = PAGES[+c.closest('.pk-page').dataset.i], k = +c.dataset.k;
    if (!p || !p.takes[k]) return;
    if (e.target.closest('.pk-zoom')) { lbOpen(p, k); return; }
    toggle(p, p.takes[k].f);
  });
  main.addEventListener('keydown', e => {
    if (LB) return;
    const c = e.target; if (!c.classList || !c.classList.contains('pk-cell')) return;
    const p = PAGES[+c.closest('.pk-page').dataset.i], k = +c.dataset.k;
    if (!p || !p.takes[k]) return;
    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle(p, p.takes[k].f); }
    else if (e.key === 'z' || e.key === 'Z') { e.preventDefault(); lbOpen(p, k); }
  });
  tgl.addEventListener('click', () => { showSettled = !showSettled; applyVis(); });

  // ---------- lightbox ----------
  const lb = $('lb'), lbImg = $('lbimg'), lbInfo = $('lbinfo'), lbPrompt = $('lbprompt'), lbPick = $('lbpick'), lbStage = $('lbstage');
  let LB = null;
  function lbOpen(p, k) {
    LB = { p: p, k: k };
    lb.hidden = false; document.body.classList.add('pk-noscroll');
    if (document.activeElement && document.activeElement.blur) document.activeElement.blur();
    lbShow();
  }
  function lbShow() {
    const p = LB.p, t = p.takes[LB.k]; if (!t) return;
    const on = isPicked(p, t.f);
    lbImg.src = imgUrl(t.f, false); lbImg.alt = p.g + ' take #' + (LB.k + 1);
    lbImg.classList.toggle('sel', on);
    lbInfo.textContent = '';
    lbInfo.appendChild(document.createTextNode(p.g + ' · ' + (LB.k + 1) + '/' + p.takes.length));
    if (on) { lbInfo.appendChild(document.createTextNode(' · ')); lbInfo.appendChild(el('b', 'pk-on', '✔ PICKED')); }
    if (t.cl) { lbInfo.appendChild(document.createTextNode(' · ')); lbInfo.appendChild(el('b', 'pk-c', "Claude's pick")); }
    if (t.n) lbInfo.appendChild(document.createTextNode(' · new'));
    if (p.pick === 'drop') lbInfo.appendChild(document.createTextNode(' · page dropped'));
    lbPrompt.textContent = t.p || ''; lbPrompt.hidden = !t.p; lbPrompt.title = t.p || '';
    lbPick.textContent = on ? '✔ Picked' : 'Pick';
    lbPick.classList.toggle('on', on);
    [LB.k + 1, LB.k - 1].forEach(j => { const n = p.takes[(j + p.takes.length) % p.takes.length]; if (n && n !== t) { const im = new Image(); im.src = imgUrl(n.f, false); } });
  }
  function lbClose() {
    if (!LB) return;
    const p = LB.p, k = LB.k;
    LB = null; lb.hidden = true; lbImg.removeAttribute('src'); document.body.classList.remove('pk-noscroll');
    if (!visible(p)) { p.forced = true; applyVis(); }
    fillGrid(p);
    const c = p.cells && p.cells[k];
    if (c) { c.scrollIntoView({ block: 'nearest' }); try { c.focus({ preventScroll: true }); } catch (e) { /* old browsers */ } }
  }
  const lbStep = d => { const n = LB.p.takes.length; LB.k = (LB.k + d + n) % n; };
  function lbPage(d) {
    let list = PAGES.filter(visible), idx = list.indexOf(LB.p);
    if (idx < 0) { list = PAGES; idx = PAGES.indexOf(LB.p); }
    const q = list[idx + d]; if (!q || !q.takes.length) return;
    LB.p = q;
    const first = q.takes.findIndex(t => isPicked(q, t.f));
    LB.k = first >= 0 ? first : 0;
  }
  document.addEventListener('keydown', e => {
    if (!LB || e.metaKey || e.ctrlKey || e.altKey) return;
    const tag = e.target && e.target.tagName;
    if (tag === 'TEXTAREA' || tag === 'INPUT') return;
    switch (e.key) {
      case 'ArrowRight': lbStep(1); break;
      case 'ArrowLeft': lbStep(-1); break;
      case 'ArrowDown': lbPage(1); break;
      case 'ArrowUp': lbPage(-1); break;
      case 'Enter': case ' ': case 'Spacebar': e.preventDefault(); toggle(LB.p, LB.p.takes[LB.k].f); return;
      case 'Escape': e.preventDefault(); lbClose(); return;
      default: return;
    }
    e.preventDefault(); lbShow();
  });
  const lbBtn = (id, fn) => $(id).addEventListener('click', e => { e.stopPropagation(); e.currentTarget.blur(); if (LB) fn(); });
  lbBtn('lbprev', () => { lbStep(-1); lbShow(); });
  lbBtn('lbnext', () => { lbStep(1); lbShow(); });
  lbBtn('lbup', () => { lbPage(-1); lbShow(); });
  lbBtn('lbdown', () => { lbPage(1); lbShow(); });
  lbBtn('lbpick', () => toggle(LB.p, LB.p.takes[LB.k].f));
  lbBtn('lbx', lbClose);
  lb.addEventListener('click', e => { if (e.target === lb || e.target === lbStage || e.target === lbImg) lbClose(); });
  let tx = 0, ty = 0, tOn = false;
  lb.addEventListener('touchstart', e => {
    if (e.touches.length !== 1) { tOn = false; return; }
    tOn = true; tx = e.touches[0].clientX; ty = e.touches[0].clientY;
  }, { passive: true });
  lb.addEventListener('touchend', e => {
    if (!tOn || !LB) return; tOn = false;
    const t = e.changedTouches[0], dx = t.clientX - tx, dy = t.clientY - ty;
    if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy) * 1.2) { lbStep(dx < 0 ? 1 : -1); lbShow(); }
    else if (Math.abs(dy) > 70 && Math.abs(dy) > Math.abs(dx) * 1.2) { lbPage(dy < 0 ? 1 : -1); lbShow(); }
  }, { passive: true });

  // ---------- copy list ----------
  function copyText(s) {
    const btn = $('copy');
    const done = () => { status('✔ list copied'); btn.textContent = 'Copied ✔'; setTimeout(() => { btn.textContent = 'Copy list'; }, 1600); };
    const fallback = () => {
      const ta = el('textarea'); ta.value = s; ta.setAttribute('readonly', '');
      ta.style.cssText = 'position:fixed;top:0;left:0;width:1px;height:1px;opacity:0';
      document.body.appendChild(ta); ta.select();
      let ok = false; try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
      ta.remove();
      if (ok) done(); else status('✖ copy failed: your browser blocked the clipboard', 'err');
    };
    if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(s).then(done, fallback); else fallback();
  }
  $('copy').addEventListener('click', () => {
    let list = PAGES.filter(visible); if (!list.length) list = PAGES;
    const lines = [NAME + ' — picks'];
    list.forEach(p => {
      let s;
      if (p.pick === 'drop') s = 'DROP';
      else { const nums = pickedNums(p); s = nums.length ? nums.join(', ') : '— (no pick yet)'; }
      lines.push(p.g + ' → ' + s);
      const c = String(p.ta ? p.ta.value : (p.c || '')).trim();
      if (c) c.split(/\n+/).forEach(l => { if (l.trim()) lines.push('   ↳ ' + l.trim()); });
    });
    copyText(lines.join('\n'));
  });

  // ---------- toast + live poll ----------
  function toast(msg, kind, onClick) {
    toastEl.textContent = '';
    toastEl.className = 'pk-toast show' + (kind ? ' ' + kind : '');
    toastEl.appendChild(el('span', null, msg));
    const x = el('button', 'pk-toastx', '×'); x.type = 'button'; x.setAttribute('aria-label', 'Dismiss');
    toastEl.appendChild(x);
    toastEl.onclick = e => {
      if (e.target === x) { toastEl.className = 'pk-toast'; changed.img = changed.picks = false; return; }
      if (onClick) onClick();
    };
  }
  function reloadSafely() { flushAll(false); chain.then(() => location.reload()); }
  function showChangeToast() {
    if (!changed.img && !changed.picks) return;
    toast(changed.img ? '+ new takes — refresh' : 'Someone else changed picks — refresh', '', reloadSafely);
  }
  function poll() {
    if (document.hidden || inflight) return;
    const g = saveGen;
    fetch('picker.php?do=sig&p=' + encodeURIComponent(PID), { headers: { 'Accept': 'application/json' }, cache: 'no-store', credentials: 'same-origin' })
      .then(r => r.json().then(j => Object.assign({ status: r.status }, j || {})))
      .then(j => {
        if (j.status === 401 || j.status === 403) { toast(String(j.error || 'You are signed out.') + ' Tap to reload.', 'err', () => location.reload()); return; }
        if (!j.ok || inflight || g !== saveGen) return;
        let hit = false;
        if (String(j.img) !== BASE.img) { changed.img = true; hit = true; }
        if (String(j.picks) !== BASE.picks) { changed.picks = true; hit = true; }
        if (hit) { BASE = { img: String(j.img), picks: String(j.picks) }; showChangeToast(); }
      })
      .catch(() => { /* offline: try again next tick */ });
  }
  setInterval(poll, 20000);
  document.addEventListener('visibilitychange', () => { if (document.hidden) flushAll(true); else poll(); });
  window.addEventListener('pagehide', () => flushAll(true));

  // ---------- deep link #page=<group> ----------
  function fromHash(noScroll) {
    const m = /^#page=(.+)$/.exec(location.hash || ''); if (!m) return;
    let g; try { g = decodeURIComponent(m[1]); } catch (e) { return; }
    const p = PAGES.find(x => x.g === g) || PAGES.find(x => x.g === g.replace(/\+/g, ' '));
    if (!p) return;
    if (!visible(p)) { p.forced = true; applyVis(); }
    if (noScroll === true) return;           // a reload keeps the reader's scroll position
    p.el.scrollIntoView({ block: 'start' });
    p.el.classList.remove('flash'); void p.el.offsetWidth; p.el.classList.add('flash');
  }
  window.addEventListener('hashchange', () => fromHash(false));

  // ---------- boot ----------
  PAGES.forEach(buildShell);
  PAGES.forEach(refresh);
  applyVis(); counts();
  let isReload = false;
  try { const nav = performance.getEntriesByType('navigation')[0]; isReload = !!nav && nav.type === 'reload'; } catch (e) { isReload = false; }
  fromHash(isReload);
})();
</script>
</body></html>
