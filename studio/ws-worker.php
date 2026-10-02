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
//   GET|POST do=claim      worker=<name>        -> {job:{…}|null, reason?, refs:[{file,label,kind,url}]}
//   GET      do=refimg     p,f,exp,sig (no key) -> the full-size image bytes (signed URL, 2 h)
//   POST     do=submit_ok  job                  -> {ok:true} | {ok:false, wait:N} | {ok:false, stop:true}
//   POST     do=heartbeat  job[, note]          -> {ok, stop}
//   POST     do=ingest_url job, url[, gen]      -> {ok, file, done} | {ok, duplicate:true}
//   POST     do=take_failed job, reason         -> {ok, failed}
//   POST     do=cooldown   minutes, reason      -> {ok, until}
//   POST     do=done       job, status=done|error[, note] -> {ok, status}
//   GET      do=status     [worker=<name>]      -> {ok, counts, meta, enabled, claimable, active[]}
//
// Locks: only data/ws/jobs.json (ws_jobs_mutate), plus the usage lock taken INSIDE it for quota releases
// (jobs -> usage, the one allowed nesting). Image storing and chat appends run after the jobs lock is released.
declare(strict_types=1);
require_once __DIR__ . '/inc/boot.php';
header('X-Robots-Tag: noindex');

define('WS_WK_STALE_SEC', 900);          // a running job with no heartbeat for 15 min is presumed dead
define('WS_WK_MAX_ATTEMPTS', 3);         // re-queues before a job is given up as "worker kept dying"
define('WS_WK_REF_TTL', 7200);           // signed ref URLs live 2 h
define('WS_WK_MAX_DL', 30 * 1024 * 1024);
define('WS_WK_DL_TIMEOUT', 60);
define('WS_WK_HOSTS', ['cloudfront.net', 'higgsfield.ai', 'amazonaws.com', 'googleusercontent.com']);
define('WS_WK_TRIES_PER_TAKE', 4);       // 1 try + 3 retries (owner rule); bounds submit_ok calls per job

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
// workerEnabled may arrive as a bool, 0/1 or a string from a settings form; anything false-ish means off.
function ws_wk_enabled(array $s): bool { $v = $s['workerEnabled'] ?? true; return !in_array(is_string($v) ? strtolower(trim($v)) : $v, [false, 0, '0', 'false', 'off', 'no', '', null], true); }
function ws_wk_get(string $k): string { $v = $_GET[$k] ?? null; return is_string($v) ? $v : ''; }
function ws_wk_find(array $j, string $id): ?int {
    if ($id === '') return null;
    foreach ($j['jobs'] as $i => $x) if (($x['id'] ?? '') === $id) return $i;
    return null;
}
function ws_wk_left(array $x): int { return max(0, (int)($x['takes'] ?? 0) - (int)($x['done'] ?? 0)); }
// Give back the reserved-but-unproduced generations of a finished job, once. Call INSIDE the jobs lock only.
function ws_wk_release(array &$x): void {
    if (!empty($x['quotaReleased'])) return;
    $n = ws_wk_left($x);
    if ($n > 0 && (string)($x['uid'] ?? '') !== '' && (string)($x['day'] ?? '') !== '') ws_quota_release((string)$x['uid'], $n, (string)$x['day']);
    $x['quotaReleased'] = $n;
}
function ws_wk_job_out(array $x): array {
    return [
        'id' => (string)$x['id'], 'pid' => (string)$x['pid'], 'page' => (int)$x['page'], 'group' => (string)($x['group'] ?? ws_page_group((int)$x['page'])),
        'prompt' => (string)$x['prompt'], 'aspect' => (string)($x['aspect'] ?? '3:4'), 'takes' => (int)$x['takes'],
        'done' => (int)($x['done'] ?? 0), 'failed' => (int)($x['failed'] ?? 0),
        'model' => (string)($x['model'] ?? ''), 'resolution' => (string)($x['resolution'] ?? ''),
    ];
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
    $takes = $d === 1 ? '1 new take landed' : "$d new takes landed";
    if ($st === 'done') return "✅ Page $n: $takes — open the picker";
    $why = trim((string)($x['note'] ?? '')) ?: ($st === 'cancelled' ? 'cancelled' : 'error');
    if ($st === 'cancelled') $why = 'cancelled';
    return "⚠ Page $n: generation stopped ($why)" . ($d > 0 ? " — $takes, open the picker" : '');
}

// ---- download a generated image (SSRF-guarded) ------------------------------------
// https only, host must end with an allowed CDN suffix, no credentials, port 443 only, the host must resolve to
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
    $allowed = false;
    foreach (WS_WK_HOSTS as $sfx) if ($host === $sfx || str_ends_with($host, '.' . $sfx)) { $allowed = true; break; }
    if (!$allowed) return ['ok' => false, 'error' => 'host not allowed: ' . $host];
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

// ---- claim ----------------------------------------------------------------------------
if ($do === 'claim') {
    if ($worker === '') $worker = 'worker';
    $s = ws_settings(); $dead = [];
    $res = ws_jobs_mutate(function ($j) use ($worker, $s, &$dead) {
        $now = time();
        $j['meta']['workerSeenAt'] = $now; $j['meta']['workerName'] = $worker;
        if (!ws_wk_enabled($s)) return [$j, ['job' => null, 'reason' => 'disabled']];
        $cd = (int)($j['meta']['cooldownUntil'] ?? 0);
        if ($cd > $now) return [$j, ['job' => null, 'reason' => 'cooldown', 'retryAfter' => $cd - $now, 'cooldownReason' => (string)($j['meta']['cooldownReason'] ?? '')]];
        // 1) reap running jobs whose worker went quiet
        foreach ($j['jobs'] as &$x) {
            if (($x['status'] ?? '') !== 'running') continue;
            $hb = ws_wk_ts($x['heartbeatAt'] ?? null); if ($hb === 0) $hb = ws_wk_ts($x['claimedAt'] ?? null);
            if ($now - $hb <= WS_WK_STALE_SEC) continue;
            $x['attempts'] = (int)($x['attempts'] ?? 0) + 1;
            if (!empty($x['stopRequested'])) {
                $x['status'] = 'cancelled'; $x['finishedAt'] = ws_now(); $x['note'] = 'cancelled'; ws_wk_release($x); $dead[] = $x;
            } elseif ($x['attempts'] >= WS_WK_MAX_ATTEMPTS) {
                $x['status'] = 'error'; $x['finishedAt'] = ws_now(); $x['note'] = 'worker kept dying'; ws_wk_release($x); $dead[] = $x;
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
        // 4) oldest queued job whose comic still exists
        if ($pick === null) {
            foreach ($j['jobs'] as $i => &$x) {
                if (($x['status'] ?? '') !== 'queued') continue;
                if (!project_get((string)($x['pid'] ?? ''))) {
                    $x['status'] = 'error'; $x['finishedAt'] = ws_now(); $x['note'] = 'the comic no longer exists'; ws_wk_release($x); continue;
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
    if (empty($res['job'])) ws_json_out(['ok' => true] + $res + ['serverTime' => ws_now()]);
    $job = $res['job'];
    $refs = ws_wk_ref_rows($job['pid'], (array)$res['refFiles'], true);
    ws_json_out(['ok' => true, 'job' => $job, 'refs' => $refs, 'resumed' => (bool)$res['resumed'], 'serverTime' => ws_now()]);
}

// ---- status (read-only, except: with worker=<name> it also records that the worker's timer is alive) ----
if ($do === 'status') {
    $s = ws_settings();
    if ($worker !== '') {
        ws_jobs_mutate(function ($j) use ($worker) { $j['meta']['workerSeenAt'] = time(); $j['meta']['workerName'] = $worker; return [$j, null]; });
    }
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
    $m = $jj['meta'];
    $cd = (int)($m['cooldownUntil'] ?? 0);
    $enabled = ws_wk_enabled($s);
    if (!$enabled || $cd > $now) $claimable = false;
    ws_json_out(['ok' => true, 'counts' => $counts, 'enabled' => $enabled, 'claimable' => $claimable, 'active' => $active,
        'meta' => ['workerSeenAt' => (int)($m['workerSeenAt'] ?? 0), 'workerName' => (string)($m['workerName'] ?? ''),
                   'lastSubmitAt' => (int)($m['lastSubmitAt'] ?? 0), 'cooldownUntil' => $cd, 'cooldownReason' => (string)($m['cooldownReason'] ?? ''),
                   'minGapSec' => (int)$s['minGapSec']],
        'serverTime' => ws_now()]);
}

// ---- cooldown ---------------------------------------------------------------------------
if ($do === 'cooldown') {
    $min = ws_wk_in('minutes', true);
    if (!preg_match('/^\d{1,4}$/', $min) || (int)$min < 1) ws_json_out(['ok' => false, 'error' => 'minutes must be 1..240'], 400);
    $min = min(240, (int)$min); $why = ws_wk_clip(ws_wk_in('reason', true), 200);
    $until = ws_jobs_mutate(function ($j) use ($min, $why) {
        $u = time() + $min * 60;
        $j['meta']['cooldownUntil'] = max($u, (int)($j['meta']['cooldownUntil'] ?? 0));
        $j['meta']['cooldownReason'] = $why; $j['meta']['cooldownAt'] = ws_now(); $j['meta']['workerSeenAt'] = time();
        return [$j, (int)$j['meta']['cooldownUntil']];
    });
    ws_json_out(['ok' => true, 'until' => $until, 'minutes' => $min]);
}

// ---- verbs on one job ------------------------------------------------------------------
$jobId = preg_replace('/[^A-Za-z0-9_-]/', '', ws_wk_in('job', true)) ?? '';
if (in_array($do, ['submit_ok', 'heartbeat', 'ingest_url', 'take_failed', 'done'], true) && $jobId === '') ws_json_out(['ok' => false, 'error' => 'job required'], 400);

if ($do === 'submit_ok') {
    $gap = max(5, (int)ws_settings()['minGapSec']);
    $r = ws_jobs_mutate(function ($j) use ($jobId, $gap) {
        $i = ws_wk_find($j, $jobId); $now = time();
        if ($i === null) return [$j, ['ok' => false, 'stop' => true, 'error' => 'unknown job']];
        $x = &$j['jobs'][$i];
        $j['meta']['workerSeenAt'] = $now;
        if (($x['status'] ?? '') !== 'running' || !empty($x['stopRequested'])) return [$j, ['ok' => false, 'stop' => true]];
        $x['heartbeatAt'] = $now;
        $cd = (int)($j['meta']['cooldownUntil'] ?? 0);
        if ($cd > $now) return [$j, ['ok' => false, 'wait' => $cd - $now, 'cooldown' => true, 'reason' => (string)($j['meta']['cooldownReason'] ?? '')]];
        $since = $now - (int)($j['meta']['lastSubmitAt'] ?? 0);
        if ($since < $gap) return [$j, ['ok' => false, 'wait' => $gap - $since]];
        // credit guard: at most 4 submits (1 try + 3 retries) per take of this job
        $budget = (int)$x['takes'] * WS_WK_TRIES_PER_TAKE;
        if ((int)($x['submits'] ?? 0) >= $budget) return [$j, ['ok' => false, 'stop' => true, 'error' => "submit budget for this job used up ($budget tries)"]];
        $x['submits'] = (int)($x['submits'] ?? 0) + 1;
        $j['meta']['lastSubmitAt'] = $now;
        return [$j, ['ok' => true, 'submits' => $x['submits'], 'budget' => $budget]];
    });
    ws_json_out($r);
}

if ($do === 'heartbeat') {
    $note = ws_wk_clip(ws_wk_in('note', true), 200);
    $r = ws_jobs_mutate(function ($j) use ($jobId, $note) {
        $i = ws_wk_find($j, $jobId);
        $j['meta']['workerSeenAt'] = time();
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
        $x['heartbeatAt'] = time(); $j['meta']['workerSeenAt'] = time();
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
        $j['meta']['workerSeenAt'] = time();
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
        $pend[$ikey] = $now; $x['ingesting'] = $pend; $x['heartbeatAt'] = $now; $j['meta']['workerSeenAt'] = $now;
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
    $refsUsed = [];
    foreach (ws_wk_ref_rows((string)$job['pid'], (array)($job['refs'] ?? []), false) as $ref) {
        $refsUsed[] = ['file' => $ref['file'], 'label' => $ref['label'], 'kind' => 'ref', 'src' => 'ws'];
    }
    $n = (int)($job['done'] ?? 0) + 1;
    $row = null; $why = 'the Studio could not store the image';
    try {
        $row = ws_add_image((string)$job['pid'], $dl['path'], (string)$job['group'] . '-' . $n . '.' . $dl['ext'], [
            'group' => (string)$job['group'], 'prompt' => mb_substr((string)$job['prompt'], 0, 2000), 'refs_used' => $refsUsed,
            'tags' => ['ws-gen'], 'gen' => $gen, 'by' => (string)($job['by'] ?? ''), 'source' => 'ws-worker', 'wsJob' => (string)$job['id'],
        ]);
    } catch (\Throwable $e) {
        $row = null; $why .= ' (' . mb_substr($e->getMessage(), 0, 120) . ')';
    } finally {
        @unlink($dl['path']);
    }
    if (!$row) { $unmark(null); ws_json_out(['ok' => false, 'error' => $why], 500); }
    $done = $unmark($row);
    ws_json_out(['ok' => true, 'file' => (string)$row['file'], 'done' => $done, 'takes' => (int)$job['takes']]);
}

ws_json_out(['ok' => false, 'error' => 'unknown do'], 400);
