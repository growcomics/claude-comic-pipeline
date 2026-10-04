<?php
declare(strict_types=1);
require_once __DIR__ . '/inc/boot.php';
require_auth();

/* =============================================================================
 * Comic -> 3D Import  (studio/import.php)  — a SEPARATE section of the Studio.
 * Upload a comic PDF -> render pages in the browser (pdf.js, no server PDF tools
 * needed — the live host is shared cPanel) -> AI detects each page's panels ->
 * you adjust the boxes. Layer 2 slices + stores them as blueprint refs; Layer 3
 * runs the proven Higgsfield image-to-image transform (panel = blueprint + the
 * project's locked refs -> 3D). This is the "source-anchored i2i" path: the 2D
 * panel carries pose/blocking/camera/composition, so we lean on it, not the prompt.
 * ===========================================================================*/

// ---- AI panel detection (mirrors creator.php ck_ai_qa; reuses data/ai.json Anthropic key)
function imp_ai_cfg(): ?array { $f = SDATA . '/ai.json'; if (!is_file($f)) return null; $j = s_read($f, []); return !empty($j['key']) ? $j : null; }
// Last AI failure reason (API 'error.message' or a short local note), so the do= handlers can surface
// a clearer message. NEVER holds the key or the full request — only the API-provided human message.
$GLOBALS['imp_ai_err'] = '';
function imp_ai_err(): string { return (string)($GLOBALS['imp_ai_err'] ?? ''); }
// Decode an Anthropic /v1/messages response body: return its content text, or null on an error-shaped
// (or empty/unparseable) body — recording a safe human message in $GLOBALS['imp_ai_err'].
function imp_ai_text(?string $resp, int $code): ?string {
    $GLOBALS['imp_ai_err'] = '';
    if ($resp === null || trim((string)$resp) === '') { $GLOBALS['imp_ai_err'] = $code ? "empty response (HTTP $code)" : 'no response from AI'; return null; }
    $j = json_decode($resp, true);
    if (!is_array($j)) { $GLOBALS['imp_ai_err'] = 'unreadable AI response'; return null; }
    if (($j['type'] ?? '') === 'error' || isset($j['error'])) {                 // a 200 can still be an error/refusal
        $msg = (string)($j['error']['message'] ?? $j['message'] ?? 'AI returned an error');
        $GLOBALS['imp_ai_err'] = mb_substr($msg, 0, 240); return null;
    }
    $txt = $j['content'][0]['text'] ?? '';
    if (trim((string)$txt) === '') { $GLOBALS['imp_ai_err'] = 'AI returned no content'; return null; }
    return (string)$txt;
}
function imp_ai_panels(string $b64, string $mime): ?array {
    $cfg = imp_ai_cfg(); if (!$cfg || !function_exists('curl_init')) return null;
    $sys = 'You are given ONE comic book page image. Identify every distinct comic PANEL (each framed sub-image / drawing on the page — NOT speech balloons, thought clouds, captions, gutters or page margins). '
         . 'Each panel is a rectangle bounded by its drawn border and/or the gutter bars between panels. Make each box HUG the panel ARTWORK precisely: align the four edges to the panel\'s frame, and EXCLUDE black or white gutter bars, page background, and the dark margins around the art. A box must not bleed into a neighbouring panel across a gutter. '
         . 'Return ONLY compact JSON, no prose: {"panels":[{"x":<left>,"y":<top>,"w":<width>,"h":<height>}]} where x,y,w,h are fractions of the page in [0,1], tight to each panel. '
         . 'List the panels in READING ORDER: left-to-right within a tier, top tier before lower tier. '
         . 'A balloon that overflows into a neighbour does NOT change a panel\'s box — box the drawn panel, not the balloon. '
         . 'If the page is a single full-bleed splash, return one box covering ~the whole page.';
    $payload = json_encode(['model'=>'claude-sonnet-4-6', 'max_tokens'=>900, 'system'=>$sys,
        'messages'=>[['role'=>'user','content'=>[
            ['type'=>'image','source'=>['type'=>'base64','media_type'=>$mime,'data'=>$b64]],
            ['type'=>'text','text'=>'Detect the panels. JSON only.']]]]], JSON_UNESCAPED_SLASHES);
    $ch = curl_init('https://api.anthropic.com/v1/messages');
    curl_setopt_array($ch, [CURLOPT_RETURNTRANSFER=>true, CURLOPT_POST=>true,
        CURLOPT_HTTPHEADER=>['content-type: application/json', 'x-api-key: '.$cfg['key'], 'anthropic-version: 2023-06-01'],
        CURLOPT_POSTFIELDS=>$payload, CURLOPT_TIMEOUT=>60]);
    $resp = curl_exec($ch); $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE); curl_close($ch);
    $txt = imp_ai_text($resp !== false ? (string)$resp : null, $code);
    if ($txt === null) return null;
    if (preg_match('/\{.*\}/s', $txt, $m)) { $o = json_decode($m[0], true);
        if (isset($o['panels']) && is_array($o['panels'])) return $o['panels']; }
    $GLOBALS['imp_ai_err'] = 'AI reply had no panel JSON';
    return null;
}

// ---- AI interpretation: read each panel's dialogue + action, attributing balloons to the
//      panel of the character SPEAKING (by tail/flow), not the panel they physically overlap.
//      The captured slice stays art-only; the words live here as data (for the lettering post-pass).
function imp_ai_interpret(string $b64, string $mime, array $boxes): ?array {
    $cfg = imp_ai_cfg(); if (!$cfg || !function_exists('curl_init')) return null;
    $list = '';
    foreach ($boxes as $i => $b) {
        $list .= sprintf("Panel %d: x=%.3f y=%.3f w=%.3f h=%.3f\n", $i + 1,
            (float)($b['x'] ?? 0), (float)($b['y'] ?? 0), (float)($b['w'] ?? 0), (float)($b['h'] ?? 0));
    }
    $sys = 'You are reading ONE comic book page. You get the page image and a numbered list of PANEL rectangles (fractions of the page, in reading order). For EACH panel return its dialogue/caption text and a one-sentence description of the action/illustration. '
         . 'CRITICAL: a speech or thought balloon frequently overflows into a NEIGHBOURING panel. Attribute each balloon to the panel whose character is SPEAKING or THINKING it — follow the balloon TAIL and the conversation flow — NOT the panel it physically overlaps. '
         . 'Classify every line as "speech", "thought" or "caption". Give the speaker name if identifiable from context, else "". Transcribe text VERBATIM. '
         . 'Return ONLY compact JSON, no prose: {"panels":[{"n":<1-based panel number>,"action":"<one sentence>","lines":[{"type":"speech|thought|caption","speaker":"<name or empty>","text":"<verbatim>"}]}]}. Include EVERY panel number, with an empty lines array if it has no text.';
    $payload = json_encode(['model'=>'claude-sonnet-4-6', 'max_tokens'=>2000, 'system'=>$sys,
        'messages'=>[['role'=>'user','content'=>[
            ['type'=>'image','source'=>['type'=>'base64','media_type'=>$mime,'data'=>$b64]],
            ['type'=>'text','text'=>"Panels on this page (reading order):\n".$list."\nRead each panel's dialogue + action and attribute overflowing balloons by tail. JSON only."]]]]], JSON_UNESCAPED_SLASHES);
    $ch = curl_init('https://api.anthropic.com/v1/messages');
    curl_setopt_array($ch, [CURLOPT_RETURNTRANSFER=>true, CURLOPT_POST=>true,
        CURLOPT_HTTPHEADER=>['content-type: application/json', 'x-api-key: '.$cfg['key'], 'anthropic-version: 2023-06-01'],
        CURLOPT_POSTFIELDS=>$payload, CURLOPT_TIMEOUT=>90]);
    $resp = curl_exec($ch); $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE); curl_close($ch);
    $txt = imp_ai_text($resp !== false ? (string)$resp : null, $code);
    if ($txt === null) return null;
    if (preg_match('/\{.*\}/s', $txt, $m)) { $o = json_decode($m[0], true);
        if (isset($o['panels']) && is_array($o['panels'])) return $o['panels']; }
    $GLOBALS['imp_ai_err'] = 'AI reply had no panel JSON';
    return null;
}

// ---- pick the closest supported aspect ratio for a panel's pixel dims
function imp_aspect(int $w, int $h): string {
    if ($w <= 0 || $h <= 0) return '1:1';
    $r = $w / $h;
    $opts = ['1:1'=>1.0,'4:5'=>0.8,'5:4'=>1.25,'3:4'=>0.75,'4:3'=>1.3333,'2:3'=>0.6667,'3:2'=>1.5,'9:16'=>0.5625,'16:9'=>1.7778,'21:9'=>2.333];
    $best='1:1'; $bd=9.9; foreach ($opts as $k=>$v) { $d=abs($v-$r); if ($d<$bd){ $bd=$d; $best=$k; } }
    return $best;
}
// ---- the comic->3D transform prompt: composition from the blueprint, identity from the attached
//      refs, lettering fully suppressed (words live as data for the post-pass).
function imp_transform_prompt(string $action): string {
    $a = trim($action) !== '' ? (' The panel depicts: ' . mb_substr(trim($action),0,300) . '.') : '';
    return 'Photoreal 3D CGI render, DAZ3D Iray style, cinematic lighting, high detail, single comic panel. '
         . 'Recreate THIS 2D comic panel as a photorealistic 3D render — keep the EXACT same composition, camera angle, framing, poses, gestures, expressions and background staging as the source (first) image.' . $a . ' '
         . 'Render the people using the attached character references for face, hair, body build and wardrobe; keep each character on-model and at the build the reference shows. '
         . 'Render ONLY the illustrated scene — NO speech balloons, NO thought bubbles, NO caption boxes, NO text or lettering of any kind; fill any area where a balloon or caption was with the natural continuation of the scene. '
         . 'Realistic skin texture, strong readable facial expressions, cohesive comic panel.';
}

// ---- POST: enqueue a comic->3D TRANSFORM job for every stored blueprint that doesn't have one yet.
//      The worker (Lane B) renders each: blueprint (i2i source) + the project's locked character refs.
if ($_SERVER['REQUEST_METHOD'] === 'POST' && ($_POST['do'] ?? '') === 'transform') {
    header('Content-Type: application/json'); csrf_check();
    $pid = preg_replace('/[^a-z0-9-]/', '', (string)($_POST['p'] ?? ''));
    if ($pid === '' || !project_get($pid)) { echo json_encode(['ok'=>false,'err'=>'pick a project']); exit; }
    $meta = images_all($pid);
    $transformed = [];
    foreach ($meta as $m) { $p = (string)($m['parent'] ?? ''); if ($p !== '') $transformed[$p] = true; }   // a 3D panel chained to its blueprint
    // ...also skip blueprints that already have a still-OPEN transform job (non-terminal), so a second
    // click / a click while jobs are pending doesn't re-enqueue duplicates.
    $pending = [];
    foreach (jobs_all() as $j) {
        if (($j['kind'] ?? '') !== 'transform' || ($j['projectId'] ?? '') !== $pid) continue;
        if (in_array($j['status'] ?? '', ['done','blocked','error','stopped'], true)) continue;   // terminal-ish — doesn't block
        $bf = (string)($j['blueprintFile'] ?? ''); if ($bf !== '') $pending[$bf] = true;
    }
    $blueprints = array_values(array_filter($meta, fn($m) => !empty($m['blueprint'])
        && empty($transformed[$m['file'] ?? '']) && empty($pending[$m['file'] ?? ''])));
    if (!$blueprints) { echo json_encode(['ok'=>false,'err'=>'Nothing new to transform — every blueprint is already transformed or has a pending job.']); exit; }
    $n = 0; $by = current_studio_user();
    s_with_lock(JOBS_FILE, function($jobs) use (&$n, $blueprints, $pid, $by) {
        foreach ($blueprints as $b) {
            $file  = (string)$b['file']; $page = (int)($b['page'] ?? 0); $panel = (int)($b['panel'] ?? 0);
            $dims  = @getimagesize(project_dir($pid) . '/' . $file);
            $aspect = imp_aspect((int)($dims[0] ?? 1), (int)($dims[1] ?? 1));
            $jobs[] = ['id'=>'job_' . bin2hex(random_bytes(5)), 'status'=>'open', 'kind'=>'transform',
                'projectId'=>$pid, 'scope'=>'panel', 'panel'=>'Page ' . $page, 'backend'=>'higgsfield',
                'blueprintFile'=>$file, 'page'=>$page, 'panelNo'=>$panel, 'aspect'=>$aspect,
                'prompt'=>imp_transform_prompt((string)($b['action'] ?? '')),
                'createdAt'=>date('c'), 'progress'=>['done'=>0,'total'=>1,'note'=>"comic2d3d p{$page} #{$panel}"],
                'stopRequested'=>false, 'comments'=>[], 'seen'=>[], 'createdBy'=>$by];
            $n++;
        }
        return ['data'=>$jobs, 'result'=>$n];
    });
    echo json_encode(['ok'=>true, 'enqueued'=>$n]); exit;
}

// ---- POST: live transform progress for a project — job buckets + count of stored 3D results.
//      Powers the progress strip under the Transform button (polls until nothing is queued/running).
if ($_SERVER['REQUEST_METHOD'] === 'POST' && ($_POST['do'] ?? '') === 'transformstatus') {
    header('Content-Type: application/json'); csrf_check();
    $pid = preg_replace('/[^a-z0-9-]/', '', (string)($_POST['p'] ?? ''));
    if ($pid === '' || !project_get($pid)) { echo json_encode(['ok'=>false,'err'=>'pick a project']); exit; }
    $queued = 0; $running = 0; $done = 0; $failed = 0;
    foreach (jobs_all() as $j) {
        if (($j['kind'] ?? '') !== 'transform' || ($j['projectId'] ?? '') !== $pid) continue;
        switch ($j['status'] ?? '') {
            case 'open': case 'claimed':                     $queued++;  break;
            case 'running':                                  $running++; break;
            case 'done':                                     $done++;    break;
            case 'blocked': case 'error': case 'stopped':    $failed++;  break;
            default:                                         $queued++;  break;   // needs_login / stopping etc — still in-flight
        }
    }
    // stored 3D results = images chained to a blueprint (non-empty parent), newest first for the thumb rail
    $meta = images_all($pid); $results = [];
    foreach ($meta as $m) { if ((string)($m['parent'] ?? '') !== '') $results[] = $m; }
    usort($results, fn($a, $b) => (int)($b['ts'] ?? 0) <=> (int)($a['ts'] ?? 0));
    $recent = [];
    foreach (array_slice($results, 0, 8) as $m) {
        $recent[] = ['file'=>(string)($m['file'] ?? ''), 'group'=>(string)($m['group'] ?? '')];
    }
    echo json_encode(['ok'=>true, 'queued'=>$queued, 'running'=>$running, 'done'=>$done,
        'failed'=>$failed, 'results'=>count($results), 'recent'=>$recent]); exit;
}

// ---- POST: already-stored blueprints for a project (reopen-session view — see prior progress).
//      Lightweight/read-only: file, page, panel, and whether a 3D result is already chained to it.
if ($_SERVER['REQUEST_METHOD'] === 'POST' && ($_POST['do'] ?? '') === 'blueprints') {
    header('Content-Type: application/json'); csrf_check();
    $pid = preg_replace('/[^a-z0-9-]/', '', (string)($_POST['p'] ?? ''));
    if ($pid === '' || !project_get($pid)) { echo json_encode(['ok'=>false,'err'=>'pick a project']); exit; }
    $meta = images_all($pid);
    $has3d = [];
    foreach ($meta as $m) { $p = (string)($m['parent'] ?? ''); if ($p !== '') $has3d[$p] = true; }
    $bp = [];
    foreach ($meta as $m) {
        if (empty($m['blueprint'])) continue;
        $file = (string)($m['file'] ?? '');
        $bp[] = ['file'=>$file, 'page'=>(int)($m['page'] ?? 0), 'panel'=>(int)($m['panel'] ?? 0),
                 'has3d'=>!empty($has3d[$file])];
    }
    usort($bp, fn($a, $b) => [$a['page'], $a['panel']] <=> [$b['page'], $b['panel']]);
    echo json_encode(['ok'=>true, 'blueprints'=>$bp]); exit;
}

// ---- POST: detect panels on one rendered page (browser-driven — one call per page, no PHP timeout)
if ($_SERVER['REQUEST_METHOD'] === 'POST' && ($_POST['do'] ?? '') === 'detectpanels') {
    header('Content-Type: application/json'); csrf_check();
    if (!imp_ai_cfg()) { echo json_encode(['ok'=>false,'err'=>'No AI key set — add your Anthropic key in the references workspace first. You can still box panels by hand.']); exit; }
    $data = (string)($_POST['img'] ?? '');
    if (preg_match('#^data:(image/[\w.+-]+);base64,(.*)$#s', $data, $m)) { $mime = $m[1]; $b64 = $m[2]; }
    else { $mime = 'image/jpeg'; $b64 = $data; }
    if ($b64 === '') { echo json_encode(['ok'=>false,'err'=>'no image']); exit; }
    $panels = imp_ai_panels($b64, $mime);
    if ($panels === null) { $why = imp_ai_err();
        echo json_encode(['ok'=>false,'err'=>'Detection failed'.($why!==''?' — '.$why:'').' — box the panels by hand, or retry.']); exit; }
    $clean = [];
    foreach ($panels as $p) {
        $x = max(0.0, min(1.0, (float)($p['x'] ?? 0))); $y = max(0.0, min(1.0, (float)($p['y'] ?? 0)));
        $w = max(0.02, min(1.0, (float)($p['w'] ?? 0))); $h = max(0.02, min(1.0, (float)($p['h'] ?? 0)));
        if ($x + $w > 1) $w = 1 - $x; if ($y + $h > 1) $h = 1 - $y;
        $clean[] = ['x'=>round($x,4), 'y'=>round($y,4), 'w'=>round($w,4), 'h'=>round($h,4)];
    }
    echo json_encode(['ok'=>true, 'panels'=>$clean]); exit;
}

// ---- POST: read one page's dialogue + action, attributed to the (already-adjusted) boxes
if ($_SERVER['REQUEST_METHOD'] === 'POST' && ($_POST['do'] ?? '') === 'interpretpage') {
    header('Content-Type: application/json'); csrf_check();
    if (!imp_ai_cfg()) { echo json_encode(['ok'=>false,'err'=>'No AI key set.']); exit; }
    $data  = (string)($_POST['img'] ?? '');
    $boxes = json_decode((string)($_POST['boxes'] ?? '[]'), true); if (!is_array($boxes)) $boxes = [];
    if (preg_match('#^data:(image/[\w.+-]+);base64,(.*)$#s', $data, $m)) { $mime = $m[1]; $b64 = $m[2]; }
    else { $mime = 'image/jpeg'; $b64 = $data; }
    if ($b64 === '' || !$boxes) { echo json_encode(['ok'=>false,'err'=>'need page image + boxes']); exit; }
    $panels = imp_ai_interpret($b64, $mime, $boxes);
    if ($panels === null) { $why = imp_ai_err();
        echo json_encode(['ok'=>false,'err'=>'read failed'.($why!==''?' — '.$why:'').' — retry']); exit; }
    echo json_encode(['ok'=>true, 'panels'=>$panels]); exit;
}

// ---- POST: store ONE snipped panel crop into the project as a BLUEPRINT (i2i source) +
//      its dialogue/action data. Off the live board (isref). Layer 3 transforms these to 3D.
if ($_SERVER['REQUEST_METHOD'] === 'POST' && ($_POST['do'] ?? '') === 'saveslice') {
    header('Content-Type: application/json'); csrf_check();
    $pid = preg_replace('/[^a-z0-9-]/', '', (string)($_POST['p'] ?? ''));
    if ($pid === '' || !project_get($pid)) { echo json_encode(['ok'=>false,'err'=>'pick a project']); exit; }
    $f = $_FILES['file'] ?? null;
    if (!$f || ($f['error'] ?? 1) !== UPLOAD_ERR_OK || !is_uploaded_file($f['tmp_name'])) { echo json_encode(['ok'=>false,'err'=>'no file']); exit; }
    if (($f['size'] ?? 0) > MAX_BYTES) { echo json_encode(['ok'=>false,'err'=>'too big']); exit; }
    $page  = max(1, (int)($_POST['page'] ?? 1));
    $panel = max(1, (int)($_POST['panel'] ?? 1));
    $name  = "page{$page}-panel{$panel}.png";
    $res = store_image($f['tmp_name'], $name, $pid);
    if (!$res) { echo json_encode(['ok'=>false,'err'=>'store failed (unsupported image?)']); exit; }
    $lines = json_decode((string)($_POST['lines'] ?? '[]'), true); if (!is_array($lines)) $lines = [];
    $action = mb_substr(trim((string)($_POST['action'] ?? '')), 0, 400);
    // Locked read-modify-write (was: unlocked images_all -> append -> images_save; concurrent Flow-autosync /
    // worker ingests could lose panels via last-writer-wins). Record shape unchanged. $pid is already
    // sanitized to [a-z0-9-], so this path matches imeta_path()'s SDATA . "/images-$pid.json".
    $record = ['file'=>$res['file'], 'orig'=>$name, 'rating'=>'good', 'accepted'=>false,
               'group'=>'Page ' . $page, 'tags'=>['blueprint'], 'isref'=>true, 'blueprint'=>true,
               'page'=>$page, 'panel'=>$panel, 'dialogue'=>$lines, 'action'=>$action,
               'ts'=>time() + (int)($_POST['seq'] ?? 0)];
    s_with_lock(SDATA . "/images-$pid.json", function($meta) use ($record) {
        if (!is_array($meta)) $meta = [];
        $meta[] = $record;
        return ['data'=>$meta, 'result'=>true];
    });
    echo json_encode(['ok'=>true, 'file'=>$res['file'], 'group'=>'Page ' . $page]); exit;
}

$projects = projects_all();
$pid = preg_replace('/[^a-z0-9-]/', '', (string)($_GET['p'] ?? ''));
$hasAI = (bool)imp_ai_cfg();
?><!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark"><meta name="robots" content="noindex,nofollow">
<title>Comic → 3D Import · Studio</title>
<link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="assets/studio.css?v=<?= @filemtime(STUDIO_ROOT . '/assets/studio.css') ?>">
<style>
  .imp-band{border-bottom:2px solid #E0a13a}
  .imp-badge{background:#E0a13a;color:#1a1205;font-size:11px;font-weight:800;border-radius:999px;padding:3px 10px;margin-left:8px;letter-spacing:.3px}
  .imp-bar{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin:14px 0}
  .imp-bar select,.imp-bar input[type=file]{background:var(--bg2);border:1px solid var(--border2);color:var(--text);border-radius:8px;padding:8px 10px;font:13px Inter,sans-serif}
  .imp-steps{font-size:12px;color:var(--muted);margin:2px 0 10px}
  .imp-steps b{color:#E0a13a}
  .imp-status{font-size:13px;color:var(--muted);min-height:18px;margin:6px 0}
  #pages{display:flex;flex-direction:column;gap:22px;margin-top:10px}
  .page{position:relative;align-self:flex-start;border:1px solid var(--border);border-radius:8px;overflow:hidden;background:#000;box-shadow:0 2px 10px rgba(0,0,0,.4)}
  .page canvas{display:block;max-width:100%}
  .page .plabel{position:absolute;top:6px;left:6px;background:rgba(0,0,0,.7);color:#cfd3dc;font-size:11px;font-weight:700;padding:2px 8px;border-radius:6px;z-index:5}
  .page .overlay{position:absolute;inset:0;z-index:3;cursor:crosshair}
  .pbox{position:absolute;border:2px solid #E0a13a;background:rgba(224,161,58,.10);box-sizing:border-box;cursor:move}
  .pbox .pnum{position:absolute;top:-1px;left:-1px;background:#E0a13a;color:#1a1205;font-size:11px;font-weight:800;padding:1px 6px;border-bottom-right-radius:6px}
  .pbox .pdel{position:absolute;top:-1px;right:-1px;background:#c0392b;color:#fff;font-size:11px;font-weight:800;width:18px;height:18px;line-height:16px;text-align:center;cursor:pointer;border-bottom-left-radius:6px}
  .pbox .phandle{position:absolute;right:-6px;bottom:-6px;width:13px;height:13px;background:#E0a13a;border:2px solid #1a1205;border-radius:50%;cursor:nwse-resize}
  .page-tools{display:flex;gap:6px;align-items:center;padding:6px;background:var(--bg2);border-top:1px solid var(--border)}
  .page-tools .muted{font-size:12px}
  .page-interp{padding:8px 10px;background:#0f1117;border-top:1px solid var(--border);font:12px/1.55 Inter,sans-serif;max-width:1100px}
  .ip-row{padding:5px 0;border-bottom:1px solid #1a1d26}
  .ip-head{color:#E0a13a;font-weight:700;margin-bottom:2px}
  .ip-line{color:#cfd3dc}
  .ip-tag{display:inline-block;font-size:10px;font-weight:800;padding:1px 5px;border-radius:5px;margin-right:5px;text-transform:uppercase;vertical-align:1px}
  .ip-speech{background:#2b6cb0;color:#fff} .ip-thought{background:#6b46c1;color:#fff} .ip-caption{background:#4a5568;color:#fff}
  .imp-prog{margin:8px 0 2px;font-size:13px;color:var(--muted)}
  .imp-prog.hidden{display:none}
  .imp-prog b{color:#E0a13a}
  .imp-prog .pf{color:#f3a3a2}
  .imp-prog-rail{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}
  .imp-prog-rail a{display:block;border:1px solid var(--border);border-radius:6px;overflow:hidden;line-height:0}
  .imp-prog-rail img{width:56px;height:56px;object-fit:cover;display:block}
  .imp-reopen{margin-top:10px}
  .imp-reopen.hidden{display:none}
  .imp-reopen h3{font-size:13px;color:#E0a13a;margin:6px 0 4px}
  .imp-reopen-grp{margin-bottom:8px}
  .imp-reopen-grp .grp-h{font-size:12px;color:var(--muted);margin:4px 0 3px}
  .imp-reopen-thumbs{display:flex;gap:6px;flex-wrap:wrap}
  .imp-bp{position:relative;border:1px solid var(--border);border-radius:6px;overflow:hidden;line-height:0}
  .imp-bp img{width:52px;height:52px;object-fit:cover;display:block}
  .imp-bp .bp-mark{position:absolute;bottom:0;right:0;background:#2f855a;color:#fff;font-size:9px;font-weight:800;padding:0 3px;border-top-left-radius:5px;line-height:13px}
</style><!-- the one bar across every system: ⌂ back to the hub, and a menu of everything else. Source: /hub/nav.js -->
<script src="https://3dmusclecomics.com/hub/nav.js"></script>
</head><body>
<header class="topbar imp-band"><div class="brand"><span class="dot"></span> Comic Studio <span class="imp-badge">📄 COMIC → 3D</span></div>
  <a class="ghost" href="index.php">← Projects</a>
  <a class="ghost" id="lnkCockpit" href="creator.php?p=<?= h(urlencode($pid)) ?>"<?= ($pid===''?' hidden':'') ?>>← Cockpit</a>
  <a class="ghost" id="lnkReview" href="review.php?p=<?= h(urlencode($pid)) ?>"<?= ($pid===''?' hidden':'') ?>>🖌 Review</a>
  <span class="spacer"></span>
  <span class="ghost"><?= h(current_studio_user()) ?></span> <a class="ghost" href="login.php?do=logout">Log out</a></header>

<main class="wrap" data-csrf="<?= h(csrf()) ?>">
  <div class="pagehead"><h1>Comic → 3D Import</h1></div>
  <p class="imp-steps"><b>1.</b> pick the project (its references get reused) → <b>2.</b> upload a comic PDF → <b>3.</b> ✂ <b>snip</b> each panel (drag a box; AI “Detect” gives an optional rough start) → <b>4.</b> read dialogue → <b>5.</b> slice + transform to 3D <span class="muted">(step 5 lands next)</span></p>

  <?php if (!$hasAI): ?>
    <div class="rv-nudge" style="background:#3a2a10;border:1px solid #5a4520;color:#e8d9b8;padding:10px 12px;border-radius:8px;font-size:13px;margin-bottom:10px">⚠ No AI key set — auto-detect is off. Add your Anthropic key in the references workspace to enable AI panel detection. You can still box panels by hand.</div>
  <?php endif; ?>

  <div class="card" style="padding:14px">
    <div class="imp-bar">
      <label>Project
        <select id="proj">
          <option value="">— choose a project —</option>
          <?php foreach ($projects as $p): ?>
            <option value="<?= h($p['id']) ?>"<?= ($p['id']===$pid?' selected':'') ?>><?= h($p['name']) ?></option>
          <?php endforeach; ?>
        </select>
      </label>
      <label>Comic PDF <input type="file" id="pdf" accept="application/pdf"></label>
      <button class="btn" id="detectall" type="button" disabled>🔍 Detect panels (all pages)</button>
      <button class="btn" id="readall" type="button" disabled>🧠 Read dialogue (all)</button>
      <button class="btn" id="snapall" type="button" disabled>⊹ Snap to borders (all)</button>
      <span class="spacer"></span>
      <button class="btn primary" id="saveslices" type="button" disabled>✂ Slice &amp; store</button>
      <button class="btn" id="transform3d" type="button"<?= ($pid===''?' disabled':'') ?>>🎬 Transform → 3D</button>
    </div>
    <div class="imp-status" id="status">Choose a project and drop in a comic PDF to begin.</div>
    <div class="imp-prog hidden" id="prog"></div>
    <div class="imp-prog-rail" id="progRail"></div>
    <div class="imp-reopen hidden" id="reopen"></div>
  </div>

  <div id="pages"></div>
</main>

<script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
<script>
(function(){
  const CSRF = document.querySelector('main').dataset.csrf;
  const elPdf = document.getElementById('pdf'), elProj = document.getElementById('proj');
  const elPages = document.getElementById('pages'), elStatus = document.getElementById('status');
  const elDetect = document.getElementById('detectall');
  const elRead = document.getElementById('readall');
  const elSnap = document.getElementById('snapall');
  const elSave = document.getElementById('saveslices');
  const elTransform = document.getElementById('transform3d');
  const elProg = document.getElementById('prog'), elProgRail = document.getElementById('progRail');
  const elReopen = document.getElementById('reopen');
  const lnkCockpit = document.getElementById('lnkCockpit'), lnkReview = document.getElementById('lnkReview');
  const status = (t) => elStatus.textContent = t;
  if (window.pdfjsLib) pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';

  let pageEls = [];   // { wrap, canvas, overlay, boxes:[{x,y,w,h, el}], natW, natH }
  let aiAbort = null; // AbortController for the current "all pages" AI loop (a second click / project switch cancels it)

  // #transform3d starts disabled until a project is chosen (matches the other action buttons).
  elTransform.disabled = !elProj.value;

  // ---------- render the PDF ----------
  elPdf.addEventListener('change', async (e) => {
    const file = e.target.files[0]; if (!file) return;
    elPages.innerHTML = ''; pageEls = []; elDetect.disabled = true; elRead.disabled = true; elSnap.disabled = true; elSave.disabled = true;
    status('Reading ' + file.name + '…');
    try {
      const buf = await file.arrayBuffer();
      const pdf = await pdfjsLib.getDocument({data: buf}).promise;
      status('Rendering ' + pdf.numPages + ' page' + (pdf.numPages>1?'s':'') + '…');
      for (let n = 1; n <= pdf.numPages; n++) {
        const page = await pdf.getPage(n);
        const scale = Math.min(2, 1100 / page.getViewport({scale:1}).width);
        const vp = page.getViewport({scale});
        const canvas = document.createElement('canvas');
        canvas.width = vp.width; canvas.height = vp.height;
        await page.render({canvasContext: canvas.getContext('2d'), viewport: vp}).promise;

        const wrap = document.createElement('div'); wrap.className = 'page';
        const lab = document.createElement('div'); lab.className = 'plabel'; lab.textContent = 'Page ' + n;
        const overlay = document.createElement('div'); overlay.className = 'overlay';
        const tools = document.createElement('div'); tools.className = 'page-tools';
        const interp = document.createElement('div'); interp.className = 'page-interp'; interp.hidden = true;
        wrap.appendChild(lab); wrap.appendChild(canvas); wrap.appendChild(overlay); wrap.appendChild(tools); wrap.appendChild(interp);
        elPages.appendChild(wrap);

        const rec = { wrap, canvas, overlay, boxes: [], natW: vp.width, natH: vp.height, n, interpEl: interp, interp: null };
        tools.appendChild(mkBtn('🔍 Detect (start)', () => detectPage(rec)));
        tools.appendChild(mkBtn('✕ Clear', () => { rec.boxes.forEach(b=>b.el.remove()); rec.boxes=[]; updateCount(rec); }));
        tools.appendChild(mkBtn('⊹ Snap', () => { snapPage(rec); status('Page '+rec.n+': boxes snapped to panel borders.'); }));
        tools.appendChild(mkBtn('🧠 Read text', () => interpretPage(rec)));
        const cnt = document.createElement('span'); cnt.className='muted'; cnt.dataset.count='1'; tools.appendChild(cnt);
        rec._cnt = cnt; updateCount(rec);
        wireDraw(rec);
        pageEls.push(rec);
      }
      elDetect.disabled = false; elRead.disabled = false; elSnap.disabled = false; elSave.disabled = false;
      status('Rendered ' + pdf.numPages + ' page(s). ✂ Drag on any page to snip a panel — drag a box to move, corner to resize, × to delete. (Or “Detect (start)” for a rough set.) Then “Read dialogue”.');
    } catch (err) { status('Could not read the PDF: ' + err.message); }
  });

  function mkBtn(label, fn){ const b=document.createElement('button'); b.className='btn sm'; b.type='button'; b.textContent=label; b.addEventListener('click',fn); return b; }

  // ---------- AI detect one page ----------
  async function detectPage(rec, signal){
    status('Detecting panels on page ' + rec.n + '…');
    const dataUrl = rec.canvas.toDataURL('image/jpeg', 0.82);
    try {
      const body = new URLSearchParams({do:'detectpanels', csrf:CSRF, img:dataUrl});
      const r = await fetch('import.php', {method:'POST', body, signal});
      const j = await r.json();
      if (!j.ok) { status('Page ' + rec.n + ': ' + (j.err||'detect failed')); return; }
      rec.boxes.forEach(b=>b.el.remove()); rec.boxes = [];
      j.panels.forEach(p => addBox(rec, p.x, p.y, p.w, p.h));
      renumber(rec);
      status('Page ' + rec.n + ': found ' + j.panels.length + ' panel(s). Adjust as needed.');
    } catch (err) { if (err.name === 'AbortError') throw err; status('Page ' + rec.n + ' detect error: ' + err.message); }
  }
  // "Detect (all)": cap + throttle guard — confirm on big PDFs, run sequentially, abortable, with progress.
  elDetect.addEventListener('click', async () => {
    const N = pageEls.length; if (!N) return;
    if (N > 30 && !confirm('This PDF has '+N+' pages. “Detect panels (all)” makes one 60–90s AI call PER page ('+N+' calls). Run it for all of them?')) return;
    const ac = runAllStart();
    try {
      for (let i = 0; i < pageEls.length; i++){
        if (ac.signal.aborted) break;
        status('Detecting panels — page '+(i+1)+'/'+N+'…');
        await detectPage(pageEls[i], ac.signal);
      }
      if (!ac.signal.aborted) status('Detection complete — review every page.');
    } catch (err){ if (err.name === 'AbortError') status('Detect (all) canceled.'); else status('Detect (all) error: '+err.message); }
    finally { runAllEnd(ac); }
  });

  // ---- AI read: dialogue + action per panel (text stored as DATA, not baked into the art) ----
  function orderedBoxes(rec){ return rec.boxes.slice()
      .sort((a,b)=> (a.y-b.y)>0.06?1:(a.y-b.y)<-0.06?-1:a.x-b.x)
      .map(b=>({x:+b.x.toFixed(4), y:+b.y.toFixed(4), w:+b.w.toFixed(4), h:+b.h.toFixed(4)})); }
  async function interpretPage(rec, signal){
    if (!rec.boxes.length){ status('Page '+rec.n+': box the panels first (Detect or ＋ Add).'); return; }
    status('Reading page '+rec.n+' dialogue…');
    const boxes = orderedBoxes(rec);
    const dataUrl = rec.canvas.toDataURL('image/jpeg', 0.82);
    try {
      const body = new URLSearchParams({do:'interpretpage', csrf:CSRF, img:dataUrl, boxes:JSON.stringify(boxes)});
      const r = await fetch('import.php', {method:'POST', body, signal});
      const j = await r.json();
      if (!j.ok){ status('Page '+rec.n+': '+(j.err||'read failed')); return; }
      rec.interp = j.panels; renderInterp(rec);
      status('Page '+rec.n+': read '+j.panels.length+' panel(s) — text captured as data.');
    } catch(err){ if (err.name === 'AbortError') throw err; status('Page '+rec.n+' read error: '+err.message); }
  }
  function renderInterp(rec){
    const el = rec.interpEl; el.innerHTML=''; el.hidden=false;
    (rec.interp||[]).forEach(p=>{
      const row=document.createElement('div'); row.className='ip-row';
      const head=document.createElement('div'); head.className='ip-head';
      head.textContent='Panel '+p.n+(p.action?(' — '+p.action):''); row.appendChild(head);
      (p.lines||[]).forEach(l=>{
        const ln=document.createElement('div'); ln.className='ip-line';
        const tag=document.createElement('span'); tag.className='ip-tag ip-'+(l.type||'speech'); tag.textContent=(l.type||'speech');
        ln.appendChild(tag);
        ln.appendChild(document.createTextNode(' '+(l.speaker?(l.speaker+': '):'')+'“'+(l.text||'')+'”'));
        row.appendChild(ln);
      });
      if(!(p.lines||[]).length){ const ln=document.createElement('div'); ln.className='ip-line'; ln.style.color='var(--muted)'; ln.textContent='(no text)'; row.appendChild(ln); }
      el.appendChild(row);
    });
  }
  // "Read dialogue (all)": same cap + throttle + abort guard as Detect (all).
  elRead.addEventListener('click', async () => {
    const N = pageEls.length; if (!N) return;
    if (N > 30 && !confirm('This PDF has '+N+' pages. “Read dialogue (all)” makes one 60–90s AI call PER page ('+N+' calls). Run it for all of them?')) return;
    const ac = runAllStart();
    try {
      for (let i = 0; i < pageEls.length; i++){
        if (ac.signal.aborted) break;
        status('Reading dialogue — page '+(i+1)+'/'+N+'…');
        await interpretPage(pageEls[i], ac.signal);
      }
      if (!ac.signal.aborted) status('Dialogue read for all pages — text stored as data, ready to slice.');
    } catch (err){ if (err.name === 'AbortError') status('Read (all) canceled.'); else status('Read (all) error: '+err.message); }
    finally { runAllEnd(ac); }
  });

  // ---- shared abort plumbing for the "all pages" AI loops. A second click / a project switch aborts
  //      any in-flight loop before a new one starts, so we never pile up 60–90s calls. ----
  function runAllStart(){ if (aiAbort) aiAbort.abort(); aiAbort = new AbortController(); return aiAbort; }
  function runAllEnd(ac){ if (aiAbort === ac) aiAbort = null; }
  function cancelAllAI(){ if (aiAbort){ aiAbort.abort(); aiAbort = null; } }

  // ---- snap boxes to panel borders: trim uniform near-black / near-white margins (gutter bars) inward,
  //      leaving the coloured artwork untouched (so a loose box hugs the panel frame).
  function getImg(rec){ if(rec._img===undefined){ try{ rec._img = rec.canvas.getContext('2d').getImageData(0,0,rec.canvas.width,rec.canvas.height); }catch(e){ rec._img=null; } } return rec._img; }
  function lineStats(img, W, fixed, a, b, vertical){
    const d=img.data; let n=0,s=0,s2=0;
    for(let t=a;t<b;t+=3){ const x=vertical?fixed:t, y=vertical?t:fixed; const i=(y*W+x)*4; const v=(d[i]+d[i+1]+d[i+2])/3; s+=v; s2+=v*v; n++; }
    if(!n) return {mean:128,vari:99999}; const m=s/n; return {mean:m, vari:s2/n - m*m};
  }
  const isGutter = (st)=> st.vari < 230 && (st.mean < 50 || st.mean > 206);  // uniform AND near-black/near-white
  function snapBox(rec, box){
    const img=getImg(rec); if(!img) return; const W=rec.canvas.width, H=rec.canvas.height;
    let x0=Math.max(0,Math.round(box.x*W)), y0=Math.max(0,Math.round(box.y*H)),
        x1=Math.min(W,Math.round((box.x+box.w)*W)), y1=Math.min(H,Math.round((box.y+box.h)*H));
    const minW=Math.round(0.04*W), minH=Math.round(0.04*H), capX=Math.round(0.20*W), capY=Math.round(0.20*H);
    let c;
    c=0; while(x1-x0>minW && c<capX && isGutter(lineStats(img,W,x0,    y0,y1,true ))){x0++;c++;}
    c=0; while(x1-x0>minW && c<capX && isGutter(lineStats(img,W,x1-1,  y0,y1,true ))){x1--;c++;}
    c=0; while(y1-y0>minH && c<capY && isGutter(lineStats(img,W,y0,    x0,x1,false))){y0++;c++;}
    c=0; while(y1-y0>minH && c<capY && isGutter(lineStats(img,W,y1-1,  x0,x1,false))){y1--;c++;}
    box.x=x0/W; box.y=y0/H; box.w=(x1-x0)/W; box.h=(y1-y0)/H; place(rec,box);
  }
  function snapPage(rec){ rec.boxes.forEach(b=>snapBox(rec,b)); renumber(rec); }
  elSnap.addEventListener('click', () => { pageEls.forEach(snapPage); status('Snapped every page’s boxes to their panel borders — review + adjust as needed.'); });

  // ---- Layer 2: slice every snipped panel + store it in the project as a blueprint (i2i source) + its dialogue ----
  function cropBlob(canvas, b){
    return new Promise(res=>{
      const W=canvas.width, H=canvas.height;
      const sx=Math.round(b.x*W), sy=Math.round(b.y*H), sw=Math.max(1,Math.round(b.w*W)), sh=Math.max(1,Math.round(b.h*H));
      const c=document.createElement('canvas'); c.width=sw; c.height=sh;
      c.getContext('2d').drawImage(canvas, sx,sy,sw,sh, 0,0, sw,sh);
      c.toBlob(blob=>res(blob), 'image/png');
    });
  }
  elSave.addEventListener('click', async () => {
    const proj = elProj.value;
    if (!proj){ status('Pick a project first (top-left) — its references get reused for the transform.'); return; }
    const pages = window.__IMPORT__.pages();
    const total = pages.reduce((n,p)=>n+p.boxes.length, 0);
    if (!total){ status('Snip at least one panel first (drag on a page).'); return; }
    if (!confirm('Slice + store '+total+' panel'+(total===1?'':'s')+' into project “'+proj+'” as blueprints?')) return;
    elSave.disabled = true; elDetect.disabled = true;
    let done=0, fail=0, seq=0; const fails=[];   // fails: ['p2 #3', 'p4 #1', …] — which page/panel didn't store
    for (const pg of pages){
      const byPanel = {}; (pg.interp||[]).forEach(p=> byPanel[p.n]=p);
      for (let i=0;i<pg.boxes.length;i++){
        const ip = byPanel[i+1] || {};
        status('Storing page '+pg.n+' · panel '+(i+1)+'  ('+(done+fail+1)+'/'+total+')…');
        let ok=false;
        try {
          const blob = await cropBlob(pg.canvas, pg.boxes[i]);
          const fd = new FormData();
          fd.append('do','saveslice'); fd.append('csrf',CSRF); fd.append('p',proj);
          fd.append('page', pg.n); fd.append('panel', i+1); fd.append('seq', seq++);
          fd.append('action', ip.action || ''); fd.append('lines', JSON.stringify(ip.lines || []));
          fd.append('file', blob, 'page'+pg.n+'-panel'+(i+1)+'.png');
          const r = await fetch('import.php', {method:'POST', body:fd});
          const j = await r.json();
          ok = !!j.ok;
        } catch(e){ ok=false; }
        if (ok) done++; else { fail++; fails.push('p'+pg.n+' #'+(i+1)); }   // keep going on failures
      }
    }
    elSave.disabled = false; elDetect.disabled = false;
    if (fail){
      const shown = fails.slice(0,8).join(', ') + (fails.length>8?(' +'+(fails.length-8)+' more'):'');
      status('Stored '+done+' · '+fail+' failed ('+shown+'). Fix + re-run “Slice & store” to retry the failures, then 🎬 Transform → 3D.');
    } else {
      status('✓ Stored '+done+' blueprint panel'+(done===1?'':'s')+' into “'+proj+'”. Now hit 🎬 Transform → 3D.');
      loadBlueprints(proj);   // refresh the reopen-session view so the newly-stored panels show as sliced ✓
    }
  });

  // ---- Layer 3: enqueue a comic->3D transform job for each stored blueprint (worker renders them) ----
  elTransform.addEventListener('click', async () => {
    const proj = elProj.value;
    if (!proj){ status('Pick a project first (top-left).'); return; }
    if (!confirm('Enqueue a 3D transform for every stored blueprint in “'+proj+'” that doesn’t have one yet?\nThe worker renders each (blueprint + the project’s character refs) onto the board.')) return;
    status('Enqueuing transform jobs…'); elTransform.disabled = true;
    try {
      const r = await fetch('import.php', {method:'POST', body:new URLSearchParams({do:'transform', csrf:CSRF, p:proj})});
      const j = await r.json();
      status(j.ok ? ('🎬 Enqueued '+j.enqueued+' transform job'+(j.enqueued===1?'':'s')+' for “'+proj+'”. The worker renders them onto the board — watch the progress below.')
                  : ('Transform: '+(j.err||'failed')));
      if (j.ok) startProgress(proj);
    } catch(e){ status('Transform error: '+e.message); }
    elTransform.disabled = !elProj.value;
  });

  // ---- live transform progress: poll transformstatus, auto-stop when nothing queued/running ----
  let progTimer = null, progProj = null;
  async function pollProgress(){
    if (!progProj) return;
    try {
      const r = await fetch('import.php', {method:'POST', body:new URLSearchParams({do:'transformstatus', csrf:CSRF, p:progProj})});
      const j = await r.json();
      if (!j.ok){ elProg.classList.add('hidden'); return; }
      const queued = j.queued|0, running = j.running|0, failed = j.failed|0, results = j.results|0, done = j.done|0;
      const total = queued + running + done + failed;   // total transform jobs seen for this project
      elProg.classList.remove('hidden');
      elProg.innerHTML = '<b>'+results+'</b> of '+(total||results)+' transformed'
        + (running?(' · <b>'+running+'</b> running'):'')
        + (queued?(' · '+queued+' queued'):'')
        + (failed?(' · <span class="pf">'+failed+' failed</span>'):'');
      // newest transformed panels — small thumb rail, each links to review
      elProgRail.innerHTML = '';
      (j.recent||[]).forEach(m=>{
        if (!m.file) return;
        const a=document.createElement('a'); a.href='review.php?p='+encodeURIComponent(progProj);
        a.title=(m.group||'')+' — open in Review';
        const img=document.createElement('img'); img.loading='lazy';
        img.src='img.php?p='+encodeURIComponent(progProj)+'&f='+encodeURIComponent(m.file)+'&t=1';
        a.appendChild(img); elProgRail.appendChild(a);
      });
      if (queued===0 && running===0){ stopProgress(); }   // nothing in flight — stop polling (leave the strip visible)
    } catch(e){ /* transient — keep polling */ }
  }
  function startProgress(proj){ progProj = proj; if (progTimer) clearInterval(progTimer); pollProgress(); progTimer = setInterval(pollProgress, 5000); }
  function stopProgress(){ if (progTimer){ clearInterval(progTimer); progTimer = null; } }

  // ---------- editable boxes (fractions 0..1 of the page) ----------
  function addBox(rec, x, y, w, h){
    const el = document.createElement('div'); el.className = 'pbox';
    const num = document.createElement('div'); num.className='pnum';
    const del = document.createElement('div'); del.className='pdel'; del.textContent='×';
    const hnd = document.createElement('div'); hnd.className='phandle';
    el.appendChild(num); el.appendChild(del); el.appendChild(hnd);
    rec.overlay.appendChild(el);
    const box = { x, y, w, h, el, num };
    place(rec, box);
    del.addEventListener('mousedown', (ev)=>{ ev.stopPropagation(); ev.preventDefault(); el.remove(); rec.boxes = rec.boxes.filter(b=>b!==box); renumber(rec); });
    dragMove(rec, box, el);
    dragResize(rec, box, hnd);
    rec.boxes.push(box); updateCount(rec);
    return box;
  }
  function place(rec, b){ const W=rec.overlay.clientWidth, H=rec.overlay.clientHeight;
    b.el.style.left=(b.x*W)+'px'; b.el.style.top=(b.y*H)+'px'; b.el.style.width=(b.w*W)+'px'; b.el.style.height=(b.h*H)+'px'; }
  function renumber(rec){ rec.boxes.slice().sort((a,b)=> (a.y - b.y) > 0.06 ? 1 : (a.y - b.y) < -0.06 ? -1 : a.x - b.x )
      .forEach((b,i)=> b.num.textContent = (i+1)); updateCount(rec); }
  function updateCount(rec){ if (rec._cnt) rec._cnt.textContent = rec.boxes.length + ' panel' + (rec.boxes.length===1?'':'s'); }

  function dragMove(rec, box, handle){
    handle.addEventListener('mousedown', (ev)=>{
      if (ev.target.classList.contains('pdel') || ev.target.classList.contains('phandle')) return;
      ev.preventDefault(); const W=rec.overlay.clientWidth, H=rec.overlay.clientHeight;
      const sx=ev.clientX, sy=ev.clientY, ox=box.x, oy=box.y;
      const mv=(e)=>{ box.x=Math.max(0,Math.min(1-box.w, ox+(e.clientX-sx)/W)); box.y=Math.max(0,Math.min(1-box.h, oy+(e.clientY-sy)/H)); place(rec,box); };
      const up=()=>{ document.removeEventListener('mousemove',mv); document.removeEventListener('mouseup',up); renumber(rec); };
      document.addEventListener('mousemove',mv); document.addEventListener('mouseup',up);
    });
  }
  function dragResize(rec, box, hnd){
    hnd.addEventListener('mousedown', (ev)=>{ ev.stopPropagation(); ev.preventDefault();
      const W=rec.overlay.clientWidth, H=rec.overlay.clientHeight; const sx=ev.clientX, sy=ev.clientY, ow=box.w, oh=box.h;
      const mv=(e)=>{ box.w=Math.max(0.03,Math.min(1-box.x, ow+(e.clientX-sx)/W)); box.h=Math.max(0.03,Math.min(1-box.y, oh+(e.clientY-sy)/H)); place(rec,box); };
      const up=()=>{ document.removeEventListener('mousemove',mv); document.removeEventListener('mouseup',up); };
      document.addEventListener('mousemove',mv); document.addEventListener('mouseup',up);
    });
  }
  // SNIP: drag anywhere on empty page area to rubber-band a new panel rectangle (any direction).
  function wireDraw(rec){
    rec.overlay.addEventListener('mousedown', (ev)=>{
      if (ev.target!==rec.overlay || ev.button!==0) return;
      ev.preventDefault();
      const W=rec.overlay.clientWidth, H=rec.overlay.clientHeight, r=rec.overlay.getBoundingClientRect();
      const sx=(ev.clientX-r.left)/W, sy=(ev.clientY-r.top)/H;
      const box=addBox(rec, sx, sy, 0.001, 0.001);
      const mv=(e)=>{ const cx=Math.max(0,Math.min(1,(e.clientX-r.left)/W)), cy=Math.max(0,Math.min(1,(e.clientY-r.top)/H));
        box.x=Math.min(sx,cx); box.y=Math.min(sy,cy); box.w=Math.abs(cx-sx); box.h=Math.abs(cy-sy); place(rec,box); };
      const up=()=>{ document.removeEventListener('mousemove',mv); document.removeEventListener('mouseup',up);
        if (box.w<0.02 || box.h<0.02){ box.el.remove(); rec.boxes=rec.boxes.filter(b=>b!==box); }   // discard tiny accidental clicks
        updateCount(rec); renumber(rec); };
      document.addEventListener('mousemove',mv); document.addEventListener('mouseup',up);
    });
  }

  // keep boxes positioned on resize
  window.addEventListener('resize', ()=> pageEls.forEach(rec=> rec.boxes.forEach(b=> place(rec,b))));

  // ---- reopen session: on project select (and initial ?p= load) show already-stored blueprints,
  //      grouped by Page N, with an "already sliced ✓" marker — so the owner sees prior progress. ----
  async function loadBlueprints(proj){
    elReopen.classList.add('hidden'); elReopen.innerHTML = '';
    if (!proj) return;
    try {
      const r = await fetch('import.php', {method:'POST', body:new URLSearchParams({do:'blueprints', csrf:CSRF, p:proj})});
      const j = await r.json();
      if (!j.ok || !(j.blueprints||[]).length) return;
      const groups = {};
      j.blueprints.forEach(b=>{ (groups[b.page] = groups[b.page] || []).push(b); });
      const h3 = document.createElement('h3');
      h3.textContent = 'Already sliced in this project — '+j.blueprints.length+' blueprint panel'+(j.blueprints.length===1?'':'s');
      elReopen.appendChild(h3);
      Object.keys(groups).map(Number).sort((a,b)=>a-b).forEach(pg=>{
        const g = document.createElement('div'); g.className='imp-reopen-grp';
        const gh = document.createElement('div'); gh.className='grp-h'; gh.textContent = 'Page '+pg; g.appendChild(gh);
        const th = document.createElement('div'); th.className='imp-reopen-thumbs';
        groups[pg].sort((a,b)=>a.panel-b.panel).forEach(b=>{
          const cell = document.createElement('div'); cell.className='imp-bp'; cell.title='Page '+b.page+' · panel '+b.panel+(b.has3d?' · 3D done':'');
          const img = document.createElement('img'); img.loading='lazy';
          img.src='img.php?p='+encodeURIComponent(proj)+'&f='+encodeURIComponent(b.file)+'&t=1';
          cell.appendChild(img);
          const mark = document.createElement('span'); mark.className='bp-mark'; mark.textContent = b.has3d ? '3D ✓' : 'sliced ✓';
          cell.appendChild(mark); th.appendChild(cell);
        });
        g.appendChild(th); elReopen.appendChild(g);
      });
      elReopen.classList.remove('hidden');
    } catch(e){ /* non-fatal — reopen view is a convenience */ }
  }

  // ---- project select: keep action buttons + cross-links in sync, cancel any in-flight AI loop,
  //      reset progress, and reload the reopen-session view for the new project. ----
  function syncProjectUI(){
    const proj = elProj.value;
    elTransform.disabled = !proj;
    const q = proj ? encodeURIComponent(proj) : '';
    if (lnkCockpit){ lnkCockpit.href = 'creator.php?p='+q; lnkCockpit.hidden = !proj; }
    if (lnkReview){ lnkReview.href = 'review.php?p='+q; lnkReview.hidden = !proj; }
  }
  elProj.addEventListener('change', () => {
    cancelAllAI();                                   // don't let a prior page's "all" loop keep firing
    stopProgress(); elProg.classList.add('hidden'); elProgRail.innerHTML = '';
    syncProjectUI();
    loadBlueprints(elProj.value);
  });
  // initial load: if a project is preselected (?p=), reflect it + show its stored blueprints.
  syncProjectUI();
  if (elProj.value){ loadBlueprints(elProj.value); startProgress(elProj.value); }

  // expose for Layer 2 (slice + store): each page's natural canvas + fractional boxes in reading order
  window.__IMPORT__ = { pages: ()=> pageEls.map(rec=>({ n:rec.n, canvas:rec.canvas,
    boxes: orderedBoxes(rec), interp: rec.interp || null })),
    project: ()=> elProj.value };
})();
</script>
</body></html>
