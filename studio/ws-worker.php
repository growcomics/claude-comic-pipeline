<?php
// Lieutenant workspace: generation-worker endpoint (2026-10-01). See docs/LIEUTENANT-WORKSPACE.md.
//
// The worker is a headless `claude -p` job on the owner's opsbox VM (orchestrator ops/opsbox/jobs/ws-worker.*).
// It calls the Higgsfield MCP itself and talks to the Studio ONLY through this file, with its OWN key
// (data/ws/worker.json {keyHash: sha256(key)}), never the master bridge key. No session, no cookies, always JSON.
//
// Auth: header X-WS-Key (or POST field key). Exception: do=refimg is authorised by an HMAC signature that this
// file minted at claim time, so Higgsfield's media_import_url can fetch a ref image without any key or session.
//
//   GET|POST do=claim      worker=<name>        -> {job:{…}|null, reason?, refs:[{file,label,kind,url}]}   (edit job: +kind, parentFile; 1 ref)
//   GET      do=refimg     p,f,exp,sig (no key) -> the full-size image bytes (signed URL, 2 h)
//   POST     do=submit_ok  job                  -> {ok:true} | {ok:false, wait:N} | {ok:false, stop:true, error?}
//   POST     do=heartbeat  job[, note]          -> {ok, stop}
//   POST     do=ingest_url job, url[, gen]      -> {ok, file, done[, adjustResolved]} | {ok, duplicate:true}
//   POST     do=take_failed job, reason         -> {ok, failed}
//   POST     do=cooldown   minutes(1..60), reason -> {ok, until, set}   (never extends a cooldown already running)
//   POST     do=done       job, status=done|error[, note] -> {ok, status}
//   GET      do=status     [worker=<name>]      -> {ok, counts, meta, enabled, claimable, active[]}
// Every keyed verb may carry worker=<name>; liveness goes to data/ws/worker-seen.json (ws_worker_touch), never jobs.json.
//
// Quota = SUBMITS (every generate call may be charged), not landed images: enqueue reserved `takes` images; each
// submit past `takes` reserves one more (refused -> stop), at most takes x 2 submits per job; closing a job gives back
// only the never-submitted slots, once (job.released).
//
// Locks: only data/ws/jobs.json (ws_jobs_mutate), plus the usage lock taken INSIDE it for quota reserves/releases
// (jobs -> usage, the one allowed nesting). Image storing and chat appends run after the jobs lock is released.
// The cockpit-Adjust import and the card flips take the legacy data/jobs.json and data/creator-<pid>.json locks ALONE
// (never while holding another lock; the quota reserve runs between two legacy-lock passes, not inside one).
//
// Cockpit ✎ Adjust (2026-10-02): creator.php do=adjust still writes a pending card (creator-<pid>.json adjusts[]) and a
// LEGACY job (data/jobs.json kind 'adjust'). Nothing runs the legacy queue any more, so `claim` imports those jobs
// (settings importAdjusts / importAdjustsSince / editTakes) as ws jobs of kind 'edit': one ref = the parent image,
// a server-built edit prompt, the global image cap only. Their takes land as derived versions under the parent
// (parent/root/ver/derived, like bridge.php's lineage branch); the first landing flips the card to done, a job that
// closes with nothing landed flips it to failed. A card the owner cancelled (abandoned) cancels the job unrun.
declare(strict_types=1);
require_once __DIR__ . '/inc/boot.php';
header('X-Robots-Tag: noindex');

define('WS_WK_STALE_SEC', 900);          // a running job with no heartbeat for 15 min is presumed dead
define('WS_WK_MAX_ATTEMPTS', 3);         // re-queues before a job is given up as "worker kept dying"
define('WS_WK_REF_TTL', 7200);           // signed ref URLs live 2 h
define('WS_WK_MAX_DL', 30 * 1024 * 1024);
define('WS_WK_DL_TIMEOUT', 60);
// Where Higgsfield serves generation results (results.rawUrl). Checked 2026-10-01 against the owner's archive of
// 30,062 Higgsfield generations: every image rawUrl is on d8j0ntlcm91z4.cloudfront.net (2 older ones, another account,
// on dqv0cqkoy5oj7.cloudfront.net); cdn.higgsfield.ai served a few older outputs. Nothing else is downloaded. If
// Higgsfield moves its CDN, add the exact host to data/ws/worker.json "ingestHosts" (no code change needed).
define('WS_WK_HOSTS_EXACT', ['d8j0ntlcm91z4.cloudfront.net', 'dqv0cqkoy5oj7.cloudfront.net']);
define('WS_WK_HOST_SUFFIXES', ['higgsfield.ai']);
define('WS_WK_SUBMITS_PER_TAKE', 2);     // hard cap: submit_ok grants at most takes x 2 submits per job
define('WS_WK_EDIT_ASPECTS', ['3:4', '2:3', '9:16', '1:1', '4:3', '16:9', '4:5', '3:2']);   // an edit keeps its parent's shape
define('WS_WK_IMPORT_MAX', 10);          // legacy Adjust jobs imported per claim, at most
define('WS_WK_IMPORT_STALE', 600);       // a legacy job an import marked 'claimed' and never closed (killed) is retried after 10 min

// ---- small helpers (ws_wk_* = local to this file) ------------------------------------
function ws_wk_cfg(): array { $c = s_read(WS_WORKER, []); return is_array($c) ? $c : []; }
function ws_wk_keyhash(): string {
    $h = strtolower(trim((string)(ws_wk_cfg()['keyHash'] ?? '')));
    return preg_match('/^[0-9a-f]{64}$/', $h) ? $h : '';
}
// A request parameter as a string (arrays and other junk become ''). $post=true: POST body only.
function ws_wk_in(string $k, bool $post = false): string {
    $v = $post ? ($_POST[$k] ?? null) : ($_POST[$k] ?? $_GET[$k] ?? null);
    return is_string($v) ? $v : '';
}
function ws_wk_clip(string $s, int $n): string { return mb_substr(trim(preg_replace('/[\x00-\x1F\x7F]+/u', ' ', $s) ?? ''), 0, $n); }
// heartbeatAt / claimedAt may be an epoch int or an ISO string; normalise to epoch seconds (0 = never).
function ws_wk_ts($v): int {
    if (is_int($v)) return $v;
    if (is_float($v)) return (int)$v;
    if (is_string($v) && $v !== '') { if (ctype_digit($v)) return (int)$v; $t = strtotime($v); return $t === false ? 0 : $t; }
    return 0;
}
function ws_wk_sig(string $pid, string $f, int $exp, string $kh): string { return hash_hmac('sha256', $pid . '|' . $f . '|' . $exp, $kh); }
// Absolute URL of this script (for signed ref links). worker.json may pin it with publicBase (https only).
function ws_wk_self_url(): string {
    $pb = trim((string)(ws_wk_cfg()['publicBase'] ?? ''));
    if ($pb !== '' && preg_match('#^https://[A-Za-z0-9.-]+(:\d+)?/#', $pb)) return rtrim($pb, '?');
    $host = strtolower((string)($_SERVER['HTTP_HOST'] ?? ''));
    if (!preg_match('/^[a-z0-9.-]+(:\d{1,5})?$/', $host)) $host = '3dmusclecomics.com';
    // Higgsfield only imports https URLs. Production is always https (also behind a TLS-terminating proxy, where
    // PHP may see plain http), so only a local dev host gets http.
    $local = preg_match('/^(localhost|127\.0\.0\.1)(:\d+)?$|\.(test|localhost)(:\d+)?$/', $host) === 1;
    $https = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off') || (string)($_SERVER['SERVER_PORT'] ?? '') === '443' || !$local;
    $path = (string)($_SERVER['SCRIPT_NAME'] ?? '/studio/ws-worker.php');
    if (!preg_match('#^/[A-Za-z0-9/._-]*$#', $path)) $path = '/studio/ws-worker.php';
    return ($https ? 'https' : 'http') . '://' . $host . $path;
}
// workerEnabled / importAdjusts may arrive as a bool, 0/1 or a string from a settings form; anything false-ish means off.
function ws_wk_flag($v): bool { return !in_array(is_string($v) ? strtolower(trim($v)) : $v, [false, 0, '0', 'false', 'off', 'no', '', null], true); }
function ws_wk_enabled(array $s): bool { return ws_wk_flag($s['workerEnabled'] ?? true); }
function ws_wk_get(string $k): string { $v = $_GET[$k] ?? null; return is_string($v) ? $v : ''; }
function ws_wk_find(array $j, string $id): ?int {
    if ($id === '') return null;
    foreach ($j['jobs'] as $i => $x) if (($x['id'] ?? '') === $id) return $i;
    return null;
}
function ws_wk_left(array $x): int { return max(0, (int)($x['takes'] ?? 0) - (int)($x['done'] ?? 0)); }
function ws_wk_is_lt(string $uid): bool { return strncmp($uid, 'lt_', 3) === 0; }
// Give back the reserved generations a closed job never submitted, exactly once. The enqueue reservation covers the
// first `takes` submits; a submit, a landed take and a failed take each used one slot (whichever count is larger).
// Call INSIDE the jobs lock only.
function ws_wk_release(array &$x): void {
    if (!empty($x['released']) || array_key_exists('quotaReleased', $x)) return;
    $used = max((int)($x['submits'] ?? 0), (int)($x['done'] ?? 0) + (int)($x['failed'] ?? 0));
    $n = max(0, (int)($x['takes'] ?? 0) - $used);
    if ($n > 0 && (string)($x['uid'] ?? '') !== '' && (string)($x['day'] ?? '') !== '') ws_quota_release((string)$x['uid'], $n, (string)$x['day']);
    $x['quotaReleased'] = $n; $x['released'] = true;
}
// Last sign of life of a running job: heartbeatAt, else claimedAt (epoch seconds, 0 = never).
function ws_wk_hb(array $x): int { $hb = ws_wk_ts($x['heartbeatAt'] ?? null); return $hb !== 0 ? $hb : ws_wk_ts($x['claimedAt'] ?? null); }
function ws_wk_rows(): array {
    $rows = [];
    foreach (projects_all() as $p) if (is_array($p) && (string)($p['id'] ?? '') !== '') $rows[(string)$p['id']] = $p;
    return $rows;
}
// May a queued job still run? null = yes; else [final status, note]. The comic must still be the one it was queued on
// (same created stamp) and still have the job's page, and a lieutenant's job needs that person active with the comic's
// brand among theirs. An edit job (cockpit Adjust) has no page: it needs its parent image and a still-pending card.
function ws_wk_unrunnable(array $x, array $rows): ?array {
    $pid = (string)($x['pid'] ?? ''); $row = $rows[$pid] ?? null;
    if (!$row) return ['error', 'the comic no longer exists'];
    $pc = (string)($x['pcreated'] ?? '');
    if ($pc !== '' && $pc !== (string)($row['created'] ?? '')) return ['error', 'the comic was deleted and recreated'];
    if (($x['kind'] ?? '') === 'edit') {
        if (!ws_image_exists($pid, (string)($x['parentFile'] ?? ''))) return ['cancelled', 'cancelled: the image to edit is gone'];
        $card = ws_wk_card($x);
        if (!$card || ($card['status'] ?? '') !== 'pending') return ['cancelled', 'cancelled in the cockpit'];
        return null;
    }
    // the page was deleted after the job was queued (page numbers are never reused, so it cannot come back)
    if (!ws_page_get(ws_proj($pid), (int)($x['page'] ?? 0))) return ['cancelled', 'cancelled: the page was deleted'];
    $uid = (string)($x['uid'] ?? '');
    if (ws_wk_is_lt($uid)) {
        $p = ws_person($uid);
        if (!$p || empty($p['active'])) return ['cancelled', 'cancelled: access changed'];
        $b = ws_project_brand($pid, $row);
        if ($b === '' || !in_array($b, array_map('strval', (array)($p['brands'] ?? [])), true)) return ['cancelled', 'cancelled: access changed'];
    }
    return null;
}
function ws_wk_job_out(array $x): array {
    $o = [
        'id' => (string)$x['id'], 'pid' => (string)$x['pid'], 'page' => (int)$x['page'], 'group' => (string)($x['group'] ?? ws_page_group((int)$x['page'])),
        'prompt' => (string)$x['prompt'], 'aspect' => (string)($x['aspect'] ?? '3:4'), 'takes' => (int)$x['takes'],
        'done' => (int)($x['done'] ?? 0), 'failed' => (int)($x['failed'] ?? 0), 'submits' => (int)($x['submits'] ?? 0),
        'model' => (string)($x['model'] ?? ''), 'resolution' => (string)($x['resolution'] ?? ''),
    ];
    if (($x['kind'] ?? '') === 'edit') $o += ['kind' => 'edit', 'parentFile' => (string)($x['parentFile'] ?? '')];
    return $o;
}
function ws_wk_ref_rows(string $pid, array $files, bool $withUrl): array {
    $labels = [];
    foreach (ws_proj($pid)['refs'] as $r) { $f = (string)($r['file'] ?? ''); if ($f !== '') $labels[$f] = $r; }
    $kh = ws_wk_keyhash(); $exp = time() + WS_WK_REF_TTL; $base = $withUrl ? ws_wk_self_url() : '';
    $out = [];
    foreach ($files as $f) {
        $f = basename((string)$f);
        if (!ws_image_exists($pid, $f)) continue;
        $row = ['file' => $f, 'label' => mb_substr((string)($labels[$f]['label'] ?? $f), 0, 120), 'kind' => mb_substr((string)($labels[$f]['kind'] ?? 'ref'), 0, 24)];
        if ($withUrl) $row['url'] = $base . '?do=refimg&p=' . rawurlencode($pid) . '&f=' . rawurlencode($f) . '&exp=' . $exp . '&sig=' . ws_wk_sig($pid, $f, $exp, $kh);
        $out[] = $row;
    }
    return $out;
}
function ws_wk_chat_line(array $x): string {
    $n = (int)$x['page']; $d = (int)($x['done'] ?? 0); $st = (string)$x['status'];
    if (($x['kind'] ?? '') === 'edit') {
        $g = (string)($x['group'] ?? '') ?: 'Ungrouped';
        $vers = $d === 1 ? '1 edited version' : "$d edited versions";
        if ($st === 'done') return "✅ $g: $vers landed under the original — open the picker";
        $why = trim((string)($x['note'] ?? '')) ?: ($st === 'cancelled' ? 'cancelled' : 'error');
        if ($d > 0) return "⚠ $g: the Adjust stopped ($why) — $vers landed under the original, open the picker";
        return "⚠ $g: the Adjust could not be generated ($why)";
    }
    $takes = $d === 1 ? '1 new take landed' : "$d new takes landed";
    if ($st === 'done') return "✅ Page $n: $takes — open the picker";
    $why = trim((string)($x['note'] ?? '')) ?: ($st === 'cancelled' ? 'cancelled' : 'error');
    if ($st === 'cancelled') $why = 'cancelled';
    return "⚠ Page $n: generation stopped ($why)" . ($d > 0 ? " — $takes, open the picker" : '');
}

// ---- cockpit ✎ Adjust → edit jobs ------------------------------------------------------
// Owner/staff Adjusts run as 'staff:<name>' (the same id ws_uid() gives a staff session): the global cap only.
function ws_wk_staff_uid(string $name): string { return 'staff:' . strtolower(preg_replace('/[^A-Za-z0-9]+/', '-', $name) ?? ''); }
function ws_wk_edit_takes(array $s): int { return max(1, min(4, (int)($s['editTakes'] ?? 2))); }
function ws_wk_creator_file(string $pid): string { return SDATA . '/creator-' . ws_pid($pid) . '.json'; }
// The cockpit card a legacy Adjust job answers: adjusts[] row with id === job.adjustId, else jobId === job.id.
function ws_wk_card_match(array $cards, string $adjustId, string $jobId): ?array {
    foreach ($cards as $a) if (is_array($a) && $adjustId !== '' && (string)($a['id'] ?? '') === $adjustId) return $a;
    foreach ($cards as $a) if (is_array($a) && $jobId !== '' && (string)($a['jobId'] ?? '') === $jobId) return $a;
    return null;
}
// The current cockpit card of an edit job (plain read), or null.
function ws_wk_card(array $x): ?array {
    $aid = (string)($x['adjustId'] ?? ''); $f = ws_wk_creator_file((string)($x['pid'] ?? ''));
    if ($aid === '' || !is_file($f)) return null;
    return ws_wk_card_match((array)(s_read($f, [])['adjusts'] ?? []), $aid, '');
}
// Patch an edit job's card while it is still PENDING (mirrors bridge.php: ingest → done + resultFile, done → failed).
// Takes only the creator-<pid>.json lock. Best-effort: never throws; true when the card changed.
function ws_wk_card_set(array $x, array $patch): bool {
    $aid = (string)($x['adjustId'] ?? ''); $pf = (string)($x['parentFile'] ?? '');
    if (($x['kind'] ?? '') !== 'edit' || $aid === '') return false;
    try {
        $f = ws_wk_creator_file((string)($x['pid'] ?? ''));
        if (!is_file($f)) return false;
        return (bool)s_with_lock($f, function ($c) use ($aid, $pf, $patch) {
            if (!is_array($c) || empty($c['adjusts']) || !is_array($c['adjusts'])) return ['result' => false];
            foreach ($c['adjusts'] as $i => $a) {
                if (!is_array($a) || (string)($a['id'] ?? '') !== $aid || ($a['status'] ?? '') !== 'pending') continue;
                if ($pf !== '' && (string)($a['parentFile'] ?? '') !== $pf) continue;
                $c['adjusts'][$i] = array_merge($a, $patch);
                return ['data' => $c, 'result' => true];
            }
            return ['result' => false];
        });
    } catch (\Throwable $e) { return false; }
}
// A closed edit job with nothing landed: its pending card → failed (bridge.php do=done's failure branch).
function ws_wk_card_fail(array $x): void {
    if (($x['kind'] ?? '') !== 'edit' || (int)($x['done'] ?? 0) > 0) return;
    $patch = ['status' => 'failed', 'failReason' => ($x['status'] ?? '') === 'cancelled' ? 'stopped' : 'error', 'failedAt' => date('c')];
    $n = trim((string)($x['note'] ?? ''));
    if ($n !== '') $patch['failNote'] = mb_substr($n, 0, 300);
    ws_wk_card_set($x, $patch);
}
// The supported aspect closest to the parent image's pixel shape (log-ratio distance); 3:4 if unreadable.
function ws_wk_edit_aspect(string $pid, string $file): string {
    $info = @getimagesize(project_dir($pid) . '/' . basename($file));
    if (!$info || (int)$info[0] <= 0 || (int)$info[1] <= 0) return '3:4';
    $r = log((int)$info[0] / (int)$info[1]); $best = '3:4'; $bd = INF;
    foreach (WS_WK_EDIT_ASPECTS as $a) {
        [$w, $h] = array_map('intval', explode(':', $a));
        $d = abs($r - log($w / $h));
        if ($d < $bd - 1e-9) { $bd = $d; $best = $a; }
    }
    return $best;
}
// The cockpit note, control characters out and whitespace collapsed, ≤ $max chars ('' = unusable).
function ws_wk_edit_note(string $note, int $max): string {
    $n = preg_replace('/\s+/u', ' ', preg_replace('/[\x00-\x1F\x7F]+/u', ' ', $note) ?? '') ?? '';
    return mb_substr(trim($n), 0, $max);
}
// The server-built image-to-image instruction (the worker generates exactly this; the hook checks it).
function ws_wk_edit_prompt(string $note): string {
    $n = ws_wk_edit_note($note, 1500);
    if ($n !== '' && !preg_match('/[.!?]$/u', $n)) $n .= '.';
    return mb_substr('Edit this comic page image. Keep the same 2D/3D art style, page layout, panel borders, characters, faces, hair, '
        . 'outfits, colors, lettering and speech bubbles exactly as they are. Change only this: ' . $n
        . ' Every person has exactly two arms, two hands and two legs. Do not add any new text, people or objects.', 0, 2500);
}
// Import eligible legacy Adjust jobs (data/jobs.json kind 'adjust') as ws edit jobs. Returns how many were queued.
// Eligible: status open (or claimed by an import that died > WS_WK_IMPORT_STALE ago), createdAt ≥ importAdjustsSince,
// an existing comic, the parent file on disk, a usable note and a matching PENDING cockpit card. A plain read decides;
// the legacy lock is taken only when there are candidates, and never together with another lock:
//   (a) legacy lock: mark them claimed by 'ws-import'
//   (b) no legacy lock: reserve editTakes of the global cap (usage lock), append the ws job (ws jobs lock), chat line
//   (c) legacy lock: close each — done (moved), back to open (quota refused: importing stops), or stopped
function ws_wk_import_adjusts(array $s): int {
    if (!ws_wk_flag($s['importAdjusts'] ?? true)) return 0;
    $since = strtotime((string)($s['importAdjustsSince'] ?? ''));
    $legacy = s_read(JOBS_FILE, []);
    if ($since === false || !is_array($legacy) || !$legacy) return 0;
    $now = time();
    $open = function (array $j) use ($now): bool {
        $st = (string)($j['status'] ?? '');
        return ($j['kind'] ?? '') === 'adjust' && ($st === 'open'
            || ($st === 'claimed' && ($j['worker'] ?? '') === 'ws-import' && $now - ws_wk_ts($j['claimedAt'] ?? null) > WS_WK_IMPORT_STALE));
    };
    $rows = null; $cards = []; $cand = [];
    foreach ($legacy as $j) {
        if (!is_array($j) || !$open($j)) continue;
        $t = strtotime((string)($j['createdAt'] ?? ''));
        $jid = (string)($j['id'] ?? '');
        if ($t === false || $t < $since || $jid === '' || isset($cand[$jid])) continue;
        $rows = $rows ?? ws_wk_rows();
        $pid = ws_pid((string)($j['projectId'] ?? '')); $pf = basename((string)($j['parentFile'] ?? ''));
        if ($pid === '' || !isset($rows[$pid]) || !ws_image_exists($pid, $pf)) continue;
        if (!array_key_exists($pid, $cards)) $cards[$pid] = (array)(s_read(ws_wk_creator_file($pid), [])['adjusts'] ?? []);
        $card = ws_wk_card_match($cards[$pid], (string)($j['adjustId'] ?? ''), $jid);
        if (!$card || ($card['status'] ?? '') !== 'pending' || (string)($card['id'] ?? '') === '' || ws_wk_edit_note((string)($card['note'] ?? ''), 1500) === '') continue;
        $cand[$jid] = ['pid' => $pid, 'pf' => $pf, 'card' => $card, 'row' => $rows[$pid]];
        if (count($cand) >= WS_WK_IMPORT_MAX) break;
    }
    if (!$cand) return 0;
    // (a)
    $ids = array_keys($cand);
    $marked = s_with_lock(JOBS_FILE, function ($jobs) use ($ids, $open) {
        if (!is_array($jobs)) return ['result' => []];
        $got = [];
        foreach ($jobs as $i => $j) {
            if (!is_array($j) || !in_array((string)($j['id'] ?? ''), $ids, true) || !$open($j)) continue;   // taken meanwhile
            $jobs[$i]['status'] = 'claimed'; $jobs[$i]['worker'] = 'ws-import'; $jobs[$i]['claimedAt'] = ws_now(); $jobs[$i]['heartbeatAt'] = time();
            $got[] = (string)$j['id'];
        }
        return $got ? ['data' => $jobs, 'result' => $got] : ['result' => []];
    });
    if (!$marked) return 0;
    // (b)
    $takes = ws_wk_edit_takes($s); $out = []; $queued = 0; $refused = false;
    $known = [];
    foreach (ws_jobs_read()['jobs'] as $x) if (is_array($x) && (string)($x['legacyJob'] ?? '') !== '') $known[(string)$x['legacyJob']] = (string)($x['id'] ?? '');
    foreach ($marked as $lid) {
        if ($refused) { $out[$lid] = ['open', '']; continue; }
        if (isset($known[$lid])) { $out[$lid] = ['done', 'moved to the workspace generator (' . $known[$lid] . ')', $known[$lid]]; continue; }   // an import that died after (b)
        ['pid' => $pid, 'pf' => $pf, 'card' => $card, 'row' => $row] = $cand[$lid];
        $by = ws_wk_clip((string)($card['by'] ?? ''), 80) ?: 'Owner';
        $uid = ws_wk_staff_uid((string)($card['by'] ?? '') ?: 'owner');
        $q = ws_quota_reserve($uid, $takes, false);
        if (empty($q['ok'])) { $refused = true; $out[$lid] = ['open', '']; continue; }
        $group = '';
        foreach (images_all($pid) as $m) if (is_array($m) && ($m['file'] ?? '') === $pf) { $group = (string)($m['group'] ?? ''); break; }
        $job = [
            'id' => 'wsj_' . nid(), 'kind' => 'edit', 'pid' => $pid, 'pcreated' => (string)($row['created'] ?? ''), 'page' => 0, 'group' => $group,
            'prompt' => ws_wk_edit_prompt((string)($card['note'] ?? '')), 'refs' => [$pf], 'aspect' => ws_wk_edit_aspect($pid, $pf), 'takes' => $takes,
            'model' => (string)$s['genModel'], 'resolution' => (string)$s['genResolution'],
            'uid' => $uid, 'by' => $by, 'day' => ws_day(),
            'status' => 'queued', 'done' => 0, 'failed' => 0, 'submits' => 0, 'files' => [], 'note' => '',
            'parentFile' => $pf, 'adjustId' => (string)$card['id'], 'adjust' => ws_wk_edit_note((string)($card['note'] ?? ''), 1000), 'legacyJob' => $lid,
            'createdAt' => ws_now(), 'claimedAt' => null, 'heartbeatAt' => null, 'finishedAt' => null, 'worker' => '',
        ];
        $added = ws_jobs_mutate(function ($j) use ($job, $lid) {
            foreach ($j['jobs'] as $x) if ((string)($x['legacyJob'] ?? '') === $lid) return [$j, (string)($x['id'] ?? '')];
            $j['jobs'][] = $job;
            return [$j, ''];
        });
        if ($added !== '') { ws_quota_release($uid, $takes, (string)$job['day']); $out[$lid] = ['done', "moved to the workspace generator ($added)", $added]; continue; }
        $out[$lid] = ['done', 'moved to the workspace generator (' . $job['id'] . ')', $job['id']];
        $queued++;
        $vers = $takes === 1 ? '1 version' : "$takes versions";
        try { ws_chat_append($pid, [['role' => 'system', 'by' => 'Studio', 'uid' => '', 'text' => "✎ $by's Adjust on " . ($group ?: 'Ungrouped') . " is queued for the generator ($vers)"]]); }
        catch (\Throwable $e) { /* best-effort */ }
    }
    // (c)
    s_with_lock(JOBS_FILE, function ($jobs) use ($out) {
        if (!is_array($jobs)) return ['result' => 0];
        $n = 0;
        foreach ($jobs as $i => $j) {
            $id = is_array($j) ? (string)($j['id'] ?? '') : '';
            if (!isset($out[$id]) || ($j['status'] ?? '') !== 'claimed' || ($j['worker'] ?? '') !== 'ws-import') continue;   // e.g. cancelled in the cockpit meanwhile
            [$st, $note] = $out[$id];
            if ($st === 'open') { $jobs[$i]['status'] = 'open'; $jobs[$i]['worker'] = ''; $jobs[$i]['claimedAt'] = null; $n++; continue; }
            $jobs[$i]['status'] = $st; $jobs[$i]['endedAt'] = date('c'); $jobs[$i]['heartbeatAt'] = time();
            if (isset($out[$id][2])) $jobs[$i]['wsJob'] = $out[$id][2];
            $p = is_array($j['progress'] ?? null) ? $j['progress'] : ['done' => 0, 'total' => 0, 'note' => ''];
            $p['note'] = $note; $jobs[$i]['progress'] = $p;
            $n++;
        }
        return $n ? ['data' => $jobs, 'result' => $n] : ['result' => 0];
    });
    return $queued;
}

// ---- download a generated image (SSRF-guarded) ------------------------------------
// Is $host one of Higgsfield's result hosts? Exact hosts (+ worker.json ingestHosts) or a higgsfield.ai subdomain.
function ws_wk_host_allowed(string $host): bool {
    $exact = WS_WK_HOSTS_EXACT;
    foreach ((array)(ws_wk_cfg()['ingestHosts'] ?? []) as $h) {
        $h = is_string($h) ? strtolower(trim($h)) : '';
        if (preg_match('/^[a-z0-9-]+(\.[a-z0-9-]+){2,}$/', $h)) $exact[] = $h;   // a full host name, never a bare suffix
    }
    if (in_array($host, $exact, true)) return true;
    foreach (WS_WK_HOST_SUFFIXES as $sfx) if ($host === $sfx || str_ends_with($host, '.' . $sfx)) return true;
    return false;
}
// https only, host must be a Higgsfield result host, no credentials, port 443 only, the host must resolve to
// public IPv4 addresses (and is pinned to the checked IP so it cannot re-resolve), ≤3 redirects (each re-checked),
// 60 s total, ≤30 MB, and the bytes must be a real JPEG/PNG/WebP/GIF. Returns ['ok'=>true,'path','ext'] or error.
function ws_wk_url_ok(string $url): array {
    if (strlen($url) > 2048) return ['ok' => false, 'error' => 'url too long'];
    $u = parse_url($url);
    if (!is_array($u) || strtolower((string)($u['scheme'] ?? '')) !== 'https') return ['ok' => false, 'error' => 'url must be https'];
    if (isset($u['user']) || isset($u['pass'])) return ['ok' => false, 'error' => 'credentials in url'];
    if (isset($u['port']) && (int)$u['port'] !== 443) return ['ok' => false, 'error' => 'non-standard port'];
    $host = strtolower(rtrim((string)($u['host'] ?? ''), '.'));
    if ($host === '' || $host[0] === '[' || filter_var($host, FILTER_VALIDATE_IP) !== false || !preg_match('/^[a-z0-9.-]+$/', $host)) return ['ok' => false, 'error' => 'host not allowed'];
    if (!ws_wk_host_allowed($host)) return ['ok' => false, 'error' => 'host not allowed: ' . $host];
    $ips = @gethostbynamel($host);
    if (!$ips) return ['ok' => false, 'error' => 'host does not resolve'];
    foreach ($ips as $ip) {
        if (filter_var($ip, FILTER_VALIDATE_IP, FILTER_FLAG_IPV4 | FILTER_FLAG_NO_PRIV_RANGE | FILTER_FLAG_NO_RES_RANGE) === false) return ['ok' => false, 'error' => 'host resolves to a private address'];
    }
    return ['ok' => true, 'host' => $host, 'ip' => $ips[0]];
}
function ws_wk_download(string $url): array {
    if (!function_exists('curl_init')) return ['ok' => false, 'error' => 'curl missing on the server'];
    $deadline = time() + WS_WK_DL_TIMEOUT;
    for ($hop = 0; $hop <= 3; $hop++) {
        $chk = ws_wk_url_ok($url);
        if (!$chk['ok']) return $chk;
        $tmp = tempnam(sys_get_temp_dir(), 'wsw');
        if ($tmp === false) return ['ok' => false, 'error' => 'no temp file'];
        $fh = fopen($tmp, 'wb');
        if (!$fh) { @unlink($tmp); return ['ok' => false, 'error' => 'no temp file']; }
        $bytes = 0; $tooBig = false;
        $ch = curl_init($url);
        curl_setopt_array($ch, [
            CURLOPT_FOLLOWLOCATION => false, CURLOPT_PROTOCOLS => CURLPROTO_HTTPS,
            CURLOPT_RESOLVE => [$chk['host'] . ':443:' . $chk['ip']], CURLOPT_IPRESOLVE => CURL_IPRESOLVE_V4,
            CURLOPT_CONNECTTIMEOUT => 15, CURLOPT_TIMEOUT => max(5, $deadline - time()),
            CURLOPT_SSL_VERIFYPEER => true, CURLOPT_SSL_VERIFYHOST => 2,
            CURLOPT_USERAGENT => 'Mozilla/5.0 (3DMC Studio ws-worker)', CURLOPT_HTTPHEADER => ['Accept: image/*'],
            CURLOPT_WRITEFUNCTION => function ($c, string $data) use ($fh, &$bytes, &$tooBig): int {
                $bytes += strlen($data);
                if ($bytes > WS_WK_MAX_DL) { $tooBig = true; return 0; }
                $w = fwrite($fh, $data);
                return $w === false ? 0 : $w;
            },
        ]);
        $ok = curl_exec($ch);
        $code = (int)curl_getinfo($ch, CURLINFO_RESPONSE_CODE);
        $ctype = strtolower((string)curl_getinfo($ch, CURLINFO_CONTENT_TYPE));
        $redir = (string)curl_getinfo($ch, CURLINFO_REDIRECT_URL);
        $err = curl_error($ch);
        curl_close($ch); fclose($fh);
        if ($tooBig) { @unlink($tmp); return ['ok' => false, 'error' => 'image larger than 30 MB']; }
        if ($ok === false) { @unlink($tmp); return ['ok' => false, 'error' => 'download failed: ' . mb_substr($err, 0, 120)]; }
        if ($code >= 300 && $code < 400 && $redir !== '') { @unlink($tmp); $url = $redir; continue; }
        if ($code !== 200) { @unlink($tmp); return ['ok' => false, 'error' => "download HTTP $code"]; }
        // Content type must be image/*; S3-style generic octet-stream is tolerated because the bytes are sniffed below.
        $generic = preg_match('#^(application|binary)/octet-stream#', $ctype) === 1;
        if (strpos($ctype, 'image/') !== 0 && !$generic) { @unlink($tmp); return ['ok' => false, 'error' => 'not an image (content-type ' . mb_substr($ctype, 0, 60) . ')']; }
        $info = @getimagesize($tmp);
        $types = [IMAGETYPE_JPEG => 'jpg', IMAGETYPE_PNG => 'png', IMAGETYPE_WEBP => 'webp', IMAGETYPE_GIF => 'gif'];
        if (!$info || !isset($types[(int)$info[2]]) || (int)$info[0] < 64 || (int)$info[1] < 64 || (int)$info[0] > 12000 || (int)$info[1] > 12000) {
            @unlink($tmp); return ['ok' => false, 'error' => 'downloaded file is not a usable image'];
        }
        return ['ok' => true, 'path' => $tmp, 'ext' => $types[(int)$info[2]]];
    }
    return ['ok' => false, 'error' => 'too many redirects'];
}

// ---- routing ------------------------------------------------------------------------
$do = ws_wk_in('do');
$method = (string)($_SERVER['REQUEST_METHOD'] ?? 'GET');

// do=refimg: signature-authorised (no key header), so Higgsfield can import a ref by URL.
if ($do === 'refimg') {
    $kh = ws_wk_keyhash();
    $pid = ws_pid(ws_wk_get('p')); $f = basename(ws_wk_get('f'));
    $exp = ws_wk_get('exp'); $sig = strtolower(ws_wk_get('sig'));
    $now = time();
    $valid = $kh !== '' && $pid !== '' && $f !== '' && preg_match('/^[A-Za-z0-9._-]+$/', $f) && ctype_digit($exp)
          && (int)$exp >= $now && (int)$exp <= $now + WS_WK_REF_TTL + 600 && preg_match('/^[0-9a-f]{64}$/', $sig)
          && hash_equals(ws_wk_sig($pid, $f, (int)$exp, $kh), $sig);
    $path = project_dir($pid) . '/' . $f;
    if (!$valid || !is_file($path)) { http_response_code(403); header('Content-Type: text/plain'); header('Cache-Control: no-store'); echo 'forbidden'; exit; }
    $types = ['jpg' => 'image/jpeg', 'png' => 'image/png', 'webp' => 'image/webp', 'gif' => 'image/gif'];
    $ct = $types[ext_of($f)] ?? '';
    if ($ct === '') { http_response_code(403); header('Content-Type: text/plain'); echo 'forbidden'; exit; }
    header('Content-Type: ' . $ct);
    header('Content-Length: ' . filesize($path));
    header('Cache-Control: private, no-store');
    header('X-Content-Type-Options: nosniff');
    if ($method !== 'HEAD') readfile($path);
    exit;
}

// Everything else: the worker key.
$kh = ws_wk_keyhash();
$given = (string)($_SERVER['HTTP_X_WS_KEY'] ?? '');
if ($given === '') $given = ws_wk_in('key', true);
if ($kh === '' || strlen($given) < 24 || !hash_equals($kh, hash('sha256', $given))) ws_json_out(['ok' => false, 'error' => 'bad key'], 403);
unset($given);

$postOnly = ['submit_ok', 'heartbeat', 'ingest_url', 'take_failed', 'cooldown', 'done'];
if (in_array($do, $postOnly, true) && $method !== 'POST') ws_json_out(['ok' => false, 'error' => 'POST required'], 405);
$worker = ws_wk_clip(preg_replace('/[^A-Za-z0-9 ._:@-]/', '', ws_wk_in('worker')) ?? '', 40);
if ($do === 'claim' && $worker === '') $worker = 'worker';
// liveness for the "worker online" badge: data/ws/worker-seen.json (at most one write per 30 s), never jobs.json
if ($worker !== '' && in_array($do, ['claim', 'status', 'submit_ok', 'heartbeat', 'ingest_url', 'take_failed', 'cooldown', 'done'], true)) ws_worker_touch($worker);

// ---- claim ----------------------------------------------------------------------------
// Decided on a plain read first: a claim with nothing to hand out (disabled, cooldown, busy, none) never writes
// jobs.json. The jobs lock is taken only when there is a job to hand out, resume or close (stale / no longer
// runnable), and everything is re-checked under it.
if ($do === 'claim') {
    $s = ws_settings(); $dead = []; $closed = [];
    $idle = function (string $reason, array $extra = []): void { ws_json_out(['ok' => true, 'job' => null, 'reason' => $reason] + $extra + ['serverTime' => ws_now()]); };
    if (!ws_wk_enabled($s)) $idle('disabled');
    $jj = ws_jobs_read(); $now = time();
    $cd = (int)($jj['meta']['cooldownUntil'] ?? 0);
    if ($cd > $now) $idle('cooldown', ['retryAfter' => $cd - $now, 'cooldownReason' => (string)($jj['meta']['cooldownReason'] ?? '')]);
    // cockpit ✎ Adjusts waiting in the legacy queue become edit jobs first (a plain read when there are none)
    if (ws_wk_import_adjusts($s) > 0) $jj = ws_jobs_read();
    $act = false; $busy = false; $queued = false;
    foreach ($jj['jobs'] as $x) {
        $st = (string)($x['status'] ?? '');
        if ($st === 'queued') $queued = true;
        elseif ($st === 'running') {
            if ($now - ws_wk_hb($x) > WS_WK_STALE_SEC || (string)($x['worker'] ?? '') === $worker) $act = true;   // reap or resume
            else $busy = true;
        }
    }
    if (!$act && $busy) $idle('busy');
    if (!$act && !$queued) $idle('none');
    $rows = ws_wk_rows();
    $res = ws_jobs_mutate(function ($j) use ($worker, $rows, &$dead, &$closed) {
        $now = time();
        $cd = (int)($j['meta']['cooldownUntil'] ?? 0);
        if ($cd > $now) return [$j, ['job' => null, 'reason' => 'cooldown', 'retryAfter' => $cd - $now, 'cooldownReason' => (string)($j['meta']['cooldownReason'] ?? '')]];
        // 1) reap running jobs whose worker went quiet
        foreach ($j['jobs'] as &$x) {
            if (($x['status'] ?? '') !== 'running') continue;
            $hb = ws_wk_hb($x);
            if ($now - $hb <= WS_WK_STALE_SEC) continue;
            $x['attempts'] = (int)($x['attempts'] ?? 0) + 1;
            if (!empty($x['stopRequested'])) {
                $x['status'] = 'cancelled'; $x['finishedAt'] = ws_now(); $x['note'] = 'cancelled'; ws_wk_release($x); $dead[] = $x; $closed[] = $x;
            } elseif ($x['attempts'] >= WS_WK_MAX_ATTEMPTS) {
                $x['status'] = 'error'; $x['finishedAt'] = ws_now(); $x['note'] = 'worker kept dying'; ws_wk_release($x); $dead[] = $x; $closed[] = $x;
            } else {
                $x['status'] = 'queued'; $x['heartbeatAt'] = null; $x['worker'] = ''; $x['note'] = 'requeued: the worker went quiet';
            }
        }
        unset($x);
        // 2) resume: a fresh running job held by THIS worker name means its previous run was killed mid-job
        //    (opsjob's flock guarantees the old run is gone before a new one starts), so hand it back.
        $pick = null; $resumed = false;
        foreach ($j['jobs'] as $i => $x) if (($x['status'] ?? '') === 'running' && (string)($x['worker'] ?? '') === $worker) { $pick = $i; $resumed = true; break; }
        // 3) single flight: another worker holds a live job
        if ($pick === null) foreach ($j['jobs'] as $x) if (($x['status'] ?? '') === 'running') return [$j, ['job' => null, 'reason' => 'busy']];
        // 4) oldest queued job that may still run; on the way, close the ones that may not (comic gone or recreated →
        //    error; lieutenant deactivated or the comic no longer in their brands → cancelled), giving their quota back
        if ($pick === null) {
            foreach ($j['jobs'] as $i => &$x) {
                if (($x['status'] ?? '') !== 'queued') continue;
                $why = ws_wk_unrunnable($x, $rows);
                if ($why !== null) {
                    $x['status'] = $why[0]; $x['finishedAt'] = ws_now(); $x['note'] = $why[1]; ws_wk_release($x); $closed[] = $x;
                    if ($why[0] === 'cancelled') $dead[] = $x;   // the comic is still there: tell its thread
                    continue;
                }
                $pick = $i; break;
            }
            unset($x);
        }
        if ($pick === null) return [$j, ['job' => null, 'reason' => 'none']];
        $x = &$j['jobs'][$pick];
        if ($resumed) $x['resumedAt'] = ws_now(); else $x['claimedAt'] = ws_now();
        $x['status'] = 'running'; $x['heartbeatAt'] = $now; $x['worker'] = $worker;
        if (!$resumed) $x['note'] = 'generating';
        $out = ['job' => ws_wk_job_out($x), 'refFiles' => array_values((array)($x['refs'] ?? [])), 'resumed' => $resumed];
        unset($x);
        return [$j, $out];
    });
    foreach ($dead as $x) {   // tell the comic's thread about jobs given up while reaping (best-effort)
        try { ws_chat_append((string)$x['pid'], [['role' => 'system', 'by' => 'Studio', 'uid' => '', 'text' => ws_wk_chat_line($x)]]); } catch (\Throwable $e) {}
    }
    foreach ($closed as $x) ws_wk_card_fail($x);   // an edit job closed with nothing landed: its pending cockpit card → failed
    if (empty($res['job'])) ws_json_out(['ok' => true] + $res + ['serverTime' => ws_now()]);
    $job = $res['job'];
    $refs = ws_wk_ref_rows($job['pid'], (array)$res['refFiles'], true);
    if (($job['kind'] ?? '') === 'edit') {
        // exactly one ref: the image to edit. Gone since the check (or on a resume)? Never generate an edit without it.
        $refs = array_map(fn($r) => array_merge($r, ['label' => 'image to edit', 'kind' => 'parent']), array_slice($refs, 0, 1));
        if (!$refs) {
            $gone = ws_jobs_mutate(function ($j) use ($job) {
                $i = ws_wk_find($j, (string)$job['id']);
                if ($i === null || ($j['jobs'][$i]['status'] ?? '') !== 'running') return [$j, null];
                $x = &$j['jobs'][$i];
                $x['status'] = 'error'; $x['finishedAt'] = ws_now(); $x['note'] = 'the image to edit is gone'; ws_wk_release($x);
                $out = $x; unset($x);
                return [$j, $out];
            });
            if ($gone) {
                ws_wk_card_fail($gone);
                try { ws_chat_append((string)$gone['pid'], [['role' => 'system', 'by' => 'Studio', 'uid' => '', 'text' => ws_wk_chat_line($gone)]]); } catch (\Throwable $e) {}
            }
            $idle('none');
        }
    }
    ws_json_out(['ok' => true, 'job' => $job, 'refs' => $refs, 'resumed' => (bool)$res['resumed'], 'serverTime' => ws_now()]);
}

// ---- status (read-only; with worker=<name> the routing above records that the worker's timer is alive) ----
if ($do === 'status') {
    $s = ws_settings();
    $jj = ws_jobs_read(); $now = time();
    $counts = ['queued' => 0, 'running' => 0, 'done' => 0, 'error' => 0, 'cancelled' => 0];
    $active = []; $claimable = false;
    foreach ($jj['jobs'] as $x) {
        $st = (string)($x['status'] ?? '');
        $counts[$st] = (int)($counts[$st] ?? 0) + 1;
        if ($st !== 'queued' && $st !== 'running') continue;
        $hbAge = $st === 'running' ? $now - max(ws_wk_ts($x['heartbeatAt'] ?? null), ws_wk_ts($x['claimedAt'] ?? null)) : null;
        if ($st === 'queued' || $hbAge > WS_WK_STALE_SEC || ($worker !== '' && (string)($x['worker'] ?? '') === $worker)) $claimable = true;
        $active[] = ['id' => (string)($x['id'] ?? ''), 'pid' => (string)($x['pid'] ?? ''), 'page' => (int)($x['page'] ?? 0), 'status' => $st,
                     'takes' => (int)($x['takes'] ?? 0), 'done' => (int)($x['done'] ?? 0), 'failed' => (int)($x['failed'] ?? 0),
                     'worker' => (string)($x['worker'] ?? ''), 'heartbeatAge' => $hbAge, 'stopRequested' => !empty($x['stopRequested'])];
    }
    $m = $jj['meta']; $seen = ws_worker_seen();
    $cd = (int)($m['cooldownUntil'] ?? 0);
    $enabled = ws_wk_enabled($s);
    if (!$enabled || $cd > $now) $claimable = false;
    ws_json_out(['ok' => true, 'counts' => $counts, 'enabled' => $enabled, 'claimable' => $claimable, 'active' => $active,
        'meta' => ['workerSeenAt' => (int)($seen['at'] ?? 0), 'workerName' => is_string($seen['name'] ?? null) ? $seen['name'] : '',
                   'lastSubmitAt' => (int)($m['lastSubmitAt'] ?? 0), 'cooldownUntil' => $cd, 'cooldownReason' => (string)($m['cooldownReason'] ?? ''),
                   'minGapSec' => (int)$s['minGapSec']],
        'serverTime' => ws_now()]);
}

// ---- cooldown ---------------------------------------------------------------------------
// The agent reports "out of credits / rate limited" with this, so it is bounded: 1..60 minutes (clamped), and a
// cooldown that is already running is never extended or re-worded (set:false, its own `until`).
if ($do === 'cooldown') {
    $min = ws_wk_in('minutes', true);
    if (!preg_match('/^\d{1,4}$/', $min)) ws_json_out(['ok' => false, 'error' => 'minutes must be a whole number 1..60'], 400);
    $min = max(1, min(60, (int)$min)); $why = ws_wk_clip(ws_wk_in('reason', true), 200);
    $cur = (int)(ws_jobs_read()['meta']['cooldownUntil'] ?? 0);
    if ($cur > time()) ws_json_out(['ok' => true, 'until' => $cur, 'minutes' => $min, 'set' => false]);   // read-only: nothing to write
    $r = ws_jobs_mutate(function ($j) use ($min, $why) {
        $now = time(); $cur = (int)($j['meta']['cooldownUntil'] ?? 0);
        if ($cur > $now) return [$j, ['until' => $cur, 'set' => false]];
        $j['meta']['cooldownUntil'] = $now + $min * 60;
        $j['meta']['cooldownReason'] = $why; $j['meta']['cooldownAt'] = ws_now();
        return [$j, ['until' => (int)$j['meta']['cooldownUntil'], 'set' => true]];
    });
    ws_json_out(['ok' => true, 'until' => (int)$r['until'], 'minutes' => $min, 'set' => (bool)$r['set']]);
}

// ---- verbs on one job ------------------------------------------------------------------
$jobId = preg_replace('/[^A-Za-z0-9_-]/', '', ws_wk_in('job', true)) ?? '';
if (in_array($do, ['submit_ok', 'heartbeat', 'ingest_url', 'take_failed', 'done'], true) && $jobId === '') ws_json_out(['ok' => false, 'error' => 'job required'], 400);

// The credit gate: every generate call needs its own ok here. Quota counts SUBMITS: the first `takes` are covered by
// the reservation made at enqueue, each one after that reserves one more image of the person's quota (refused → stop),
// and a job never gets more than takes x 2.
if ($do === 'submit_ok') {
    $s = ws_settings();
    if (!ws_wk_enabled($s)) ws_json_out(['ok' => false, 'stop' => true, 'error' => 'generator paused']);
    $gap = max(5, (int)$s['minGapSec']);
    // an edit job whose cockpit card the owner cancelled (abandoned) stops before it spends anything more (plain reads)
    $pre = ws_jobs_read(); $pi = ws_wk_find($pre, $jobId);
    $abandoned = $pi !== null && ($pre['jobs'][$pi]['kind'] ?? '') === 'edit' && (ws_wk_card($pre['jobs'][$pi])['status'] ?? '') === 'abandoned';
    $r = ws_jobs_mutate(function ($j) use ($jobId, $gap, $abandoned) {
        $i = ws_wk_find($j, $jobId); $now = time();
        if ($i === null) return [$j, ['ok' => false, 'stop' => true, 'error' => 'unknown job']];
        $x = &$j['jobs'][$i];
        if (($x['status'] ?? '') !== 'running' || !empty($x['stopRequested'])) return [$j, ['ok' => false, 'stop' => true]];
        if ($abandoned) { $x['stopRequested'] = true; return [$j, ['ok' => false, 'stop' => true, 'error' => 'the Adjust was cancelled in the cockpit']]; }
        $x['heartbeatAt'] = $now;
        $takes = (int)($x['takes'] ?? 0); $sub = (int)($x['submits'] ?? 0); $cap = $takes * WS_WK_SUBMITS_PER_TAKE;
        if ((int)($x['done'] ?? 0) + (int)($x['failed'] ?? 0) >= $takes) return [$j, ['ok' => false, 'stop' => true, 'error' => 'every take of this job is finished']];
        if ($sub >= $cap) return [$j, ['ok' => false, 'stop' => true, 'error' => "submit cap for this job reached ($cap submits)"]];
        $cd = (int)($j['meta']['cooldownUntil'] ?? 0);
        if ($cd > $now) return [$j, ['ok' => false, 'wait' => $cd - $now, 'cooldown' => true, 'reason' => (string)($j['meta']['cooldownReason'] ?? '')]];
        $since = $now - (int)($j['meta']['lastSubmitAt'] ?? 0);
        if ($since < $gap) return [$j, ['ok' => false, 'wait' => $gap - $since]];
        if ($sub >= $takes) {   // past the enqueue reservation: this submit costs one more image (jobs -> usage lock)
            $uid = (string)($x['uid'] ?? '');
            $q = ws_quota_reserve($uid, 1, ws_wk_is_lt($uid));
            if (empty($q['ok'])) return [$j, ['ok' => false, 'stop' => true, 'error' => 'quota: ' . (string)($q['error'] ?? 'no images left today')]];
            $x['extraSubmits'] = (int)($x['extraSubmits'] ?? 0) + 1;
        }
        $x['submits'] = $sub + 1;
        $j['meta']['lastSubmitAt'] = $now;
        return [$j, ['ok' => true, 'submits' => $x['submits'], 'cap' => $cap]];
    });
    ws_json_out($r);
}

if ($do === 'heartbeat') {
    $note = ws_wk_clip(ws_wk_in('note', true), 200);
    $r = ws_jobs_mutate(function ($j) use ($jobId, $note) {
        $i = ws_wk_find($j, $jobId);
        if ($i === null) return [$j, ['ok' => false, 'stop' => true, 'error' => 'unknown job']];
        $x = &$j['jobs'][$i];
        $running = ($x['status'] ?? '') === 'running';
        if ($running) { $x['heartbeatAt'] = time(); if ($note !== '') $x['note'] = $note; }
        return [$j, ['ok' => true, 'stop' => !$running || !empty($x['stopRequested']), 'status' => (string)$x['status']]];
    });
    ws_json_out($r);
}

if ($do === 'take_failed') {
    $why = ws_wk_clip(ws_wk_in('reason', true), 300);
    $r = ws_jobs_mutate(function ($j) use ($jobId, $why) {
        $i = ws_wk_find($j, $jobId);
        if ($i === null) return [$j, ['ok' => false, 'error' => 'unknown job']];
        $x = &$j['jobs'][$i];
        if (($x['status'] ?? '') !== 'running') return [$j, ['ok' => false, 'error' => 'job is not running', 'status' => (string)$x['status']]];
        $x['failed'] = min(ws_wk_left($x), (int)($x['failed'] ?? 0) + 1);
        $x['note'] = $why !== '' ? 'take failed: ' . $why : 'take failed';
        $x['heartbeatAt'] = time();
        return [$j, ['ok' => true, 'failed' => (int)$x['failed'], 'done' => (int)($x['done'] ?? 0), 'takes' => (int)$x['takes']]];
    });
    ws_json_out($r, empty($r['ok']) && ($r['error'] ?? '') === 'unknown job' ? 404 : 200);
}

if ($do === 'done') {
    $want = ws_wk_in('status', true);
    if (!in_array($want, ['done', 'error'], true)) ws_json_out(['ok' => false, 'error' => 'status must be done or error'], 400);
    $note = ws_wk_clip(ws_wk_in('note', true), 300);
    $r = ws_jobs_mutate(function ($j) use ($jobId, $want, $note) {
        $i = ws_wk_find($j, $jobId);
        if ($i === null) return [$j, ['ok' => false, 'error' => 'unknown job']];
        $x = &$j['jobs'][$i];
        $st = (string)($x['status'] ?? '');
        if (in_array($st, ['done', 'error', 'cancelled'], true)) return [$j, ['ok' => true, 'already' => true, 'status' => $st]];
        if ($st !== 'running') return [$j, ['ok' => false, 'error' => 'job is not running', 'status' => $st]];
        $final = !empty($x['stopRequested']) ? 'cancelled' : $want;
        // "done" with nothing landed is an error from the lieutenant's point of view
        if ($final === 'done' && (int)($x['done'] ?? 0) === 0) { $final = 'error'; if ($note === '') $note = 'every take was blocked or failed'; }
        if ($final === 'done') $x['note'] = $note;
        elseif ($final === 'error') $x['note'] = $note !== '' ? $note : (trim((string)($x['note'] ?? '')) ?: 'error');
        else $x['note'] = 'cancelled';
        $x['status'] = $final; $x['finishedAt'] = ws_now(); $x['heartbeatAt'] = time();
        ws_wk_release($x);
        return [$j, ['ok' => true, 'status' => $final, 'job' => $x]];
    });
    if (!empty($r['ok']) && !empty($r['job'])) {
        $x = $r['job'];
        try { ws_chat_append((string)$x['pid'], [['role' => 'system', 'by' => 'Studio', 'uid' => '', 'text' => ws_wk_chat_line($x)]]); }
        catch (\Throwable $e) { /* the chat line is best-effort; the job state is already saved */ }
        ws_wk_card_fail($x);   // an edit job with nothing landed: its pending cockpit card → failed (no-op otherwise)
        ws_json_out(['ok' => true, 'status' => (string)$x['status'], 'done' => (int)($x['done'] ?? 0), 'released' => (int)($x['quotaReleased'] ?? 0)]);
    }
    ws_json_out($r, empty($r['ok']) && ($r['error'] ?? '') === 'unknown job' ? 404 : 200);
}

if ($do === 'ingest_url') {
    $url = trim(ws_wk_in('url', true));
    $gen = ws_wk_clip(preg_replace('/[^A-Za-z0-9._:-]/', '', ws_wk_in('gen', true)) ?? '', 80);
    $pre = ws_wk_url_ok($url);
    if (!$pre['ok']) ws_json_out(['ok' => false, 'error' => $pre['error']], 400);
    $ikey = $gen !== '' ? 'g:' . $gen : 'u:' . sha1($url);
    // 1) under the jobs lock: validate, de-duplicate, and mark this result as being ingested
    $r = ws_jobs_mutate(function ($j) use ($jobId, $ikey) {
        $i = ws_wk_find($j, $jobId); $now = time();
        if ($i === null) return [$j, ['ok' => false, 'error' => 'unknown job', 'code' => 404]];
        $x = &$j['jobs'][$i];
        if (($x['status'] ?? '') !== 'running') return [$j, ['ok' => false, 'error' => 'job is not running', 'status' => (string)$x['status'], 'code' => 409]];
        foreach ((array)($x['ingested'] ?? []) as $row) if (($row['k'] ?? '') === $ikey) return [$j, ['ok' => true, 'duplicate' => true, 'file' => (string)($row['file'] ?? ''), 'done' => (int)($x['done'] ?? 0)]];
        $pend = (array)($x['ingesting'] ?? []);
        if (isset($pend[$ikey]) && $now - (int)$pend[$ikey] < 180) return [$j, ['ok' => false, 'error' => 'this result is already being ingested; retry in a minute', 'code' => 409]];
        if ((int)($x['done'] ?? 0) >= (int)$x['takes']) return [$j, ['ok' => false, 'error' => 'every take of this job has already landed', 'code' => 409]];
        $pend[$ikey] = $now; $x['ingesting'] = $pend; $x['heartbeatAt'] = $now;
        return [$j, ['ok' => true, 'job' => $x]];
    });
    if (empty($r['ok']) || !empty($r['duplicate'])) { $code = (int)($r['code'] ?? 200); unset($r['code']); ws_json_out($r, $code); }
    $job = $r['job'];
    $unmark = function (?array $landed) use ($jobId, $ikey) {
        return ws_jobs_mutate(function ($j) use ($jobId, $ikey, $landed) {
            $i = ws_wk_find($j, $jobId);
            if ($i === null) return [$j, 0];
            $x = &$j['jobs'][$i];
            $pend = (array)($x['ingesting'] ?? []); unset($pend[$ikey]); $x['ingesting'] = $pend;
            if ($landed) {
                $x['done'] = (int)($x['done'] ?? 0) + 1;
                $x['files'] = array_values(array_merge((array)($x['files'] ?? []), [$landed['file']]));
                $x['ingested'] = array_values(array_merge((array)($x['ingested'] ?? []), [['k' => $ikey, 'file' => $landed['file'], 'ts' => time()]]));
                $x['heartbeatAt'] = time(); $x['note'] = 'take ' . $x['done'] . '/' . (int)$x['takes'] . ' landed';
            }
            return [$j, (int)($x['done'] ?? 0)];
        });
    };
    // 2) download outside any lock
    @set_time_limit(WS_WK_DL_TIMEOUT + 60);
    $dl = ws_wk_download($url);
    if (!$dl['ok']) { $unmark(null); ws_json_out(['ok' => false, 'error' => $dl['error']], 422); }
    // 3) store it under the page's group (images lock lives inside ws_add_image)
    $isEdit = ($job['kind'] ?? '') === 'edit';
    $n = (int)($job['done'] ?? 0) + 1;
    $refsUsed = [];
    if ($isEdit) {   // a derived version under the parent image (bridge.php's lineage fields), in the parent's group
        $pf = basename((string)($job['parentFile'] ?? '')); $par = null;
        foreach (images_all((string)$job['pid']) as $m) if (is_array($m) && ($m['file'] ?? '') === $pf) { $par = $m; break; }
        $root = (string)($par['root'] ?? ''); if ($root === '') $root = $pf;
        $orig = ((string)$job['group'] ?: 'edit') . '-edit-' . $n . '.' . $dl['ext'];
        $extra = [
            'group' => (string)$job['group'], 'parent' => $pf, 'root' => $root, 'ver' => max(1, (int)($par['ver'] ?? 1)) + 1, 'derived' => true,
            'adjust' => mb_substr((string)($job['adjust'] ?? ''), 0, 1000), 'adjustId' => (string)($job['adjustId'] ?? ''),
            'genkey' => (string)($par['genkey'] ?? ''),   // inherit the parent's genkey so "Group similar" keeps the chain together
            'prompt' => mb_substr((string)$job['prompt'], 0, 2000), 'refs_used' => [['file' => $pf, 'label' => 'base image', 'kind' => 'parent', 'src' => 'ws']],
            'tags' => ['ws-gen', 'ws-edit'], 'gen' => $gen, 'by' => (string)($job['by'] ?? ''), 'source' => 'ws-worker', 'wsJob' => (string)$job['id'],
        ];
    } else {
        foreach (ws_wk_ref_rows((string)$job['pid'], (array)($job['refs'] ?? []), false) as $ref) {
            $refsUsed[] = ['file' => $ref['file'], 'label' => $ref['label'], 'kind' => 'ref', 'src' => 'ws'];
        }
        $orig = (string)$job['group'] . '-' . $n . '.' . $dl['ext'];
        $extra = [
            'group' => (string)$job['group'], 'prompt' => mb_substr((string)$job['prompt'], 0, 2000), 'refs_used' => $refsUsed,
            'tags' => ['ws-gen'], 'gen' => $gen, 'by' => (string)($job['by'] ?? ''), 'source' => 'ws-worker', 'wsJob' => (string)$job['id'],
        ];
    }
    $row = null; $why = 'the Studio could not store the image';
    try {
        $row = ws_add_image((string)$job['pid'], $dl['path'], $orig, $extra);
    } catch (\Throwable $e) {
        $row = null; $why .= ' (' . mb_substr($e->getMessage(), 0, 120) . ')';
    } finally {
        @unlink($dl['path']);
    }
    if (!$row) { $unmark(null); ws_json_out(['ok' => false, 'error' => $why], 500); }
    $done = $unmark($row);
    // the first landed edit resolves the cockpit card (done + resultFile); later takes find it no longer pending and
    // just land as more derived versions. Best-effort: a failed card flip never fails the ingest.
    $adj = $isEdit && ws_wk_card_set($job, ['status' => 'done', 'resultFile' => (string)$row['file'], 'doneAt' => date('c')]);
    ws_json_out(['ok' => true, 'file' => (string)$row['file'], 'done' => $done, 'takes' => (int)$job['takes']] + ($isEdit ? ['adjustResolved' => $adj] : []));
}

ws_json_out(['ok' => false, 'error' => 'unknown do'], 400);
