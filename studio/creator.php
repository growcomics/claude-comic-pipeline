<?php
// Comic Creator cockpit — references + LIVE panels review + run/feedback/stop.
// Opens for any project that has a creator config (data/creator-<id>.json) OR a
// gallery (data/images-<id>.json, listed in projects.json). The live board reads
// the REAL gallery so generated panels (Flow ingest today, the worker later) show
// up live; Approve / Disapprove / Keep / Note drive the human-in-the-loop loop.
declare(strict_types=1);
require_once __DIR__ . '/inc/boot.php';
require_auth();

function creator_file(string $id): string { return SDATA . '/creator-' . preg_replace('/[^a-z0-9-]/', '', $id) . '.json'; }
function creator_list(): array {
    $out = [];
    foreach (glob(SDATA . '/creator-*.json') ?: [] as $f) {
        $c = s_read($f, []);
        if (!empty($c['projectId'])) $out[] = $c;
    }
    return $out;
}
// Merged index: creator configs + gallery projects, deduped by id.
function cockpit_projects(): array {
    $out = [];
    foreach (creator_list() as $c) {
        $pid = $c['projectId'];
        $out[$pid] = ['id'=>$pid, 'name'=>$c['name'] ?? $pid, 'stage'=>$c['stage'] ?? '', 'cfg'=>true];
    }
    foreach (projects_all() as $p) {
        $pid = $p['id'] ?? ''; if ($pid === '') continue;
        if (!isset($out[$pid])) $out[$pid] = ['id'=>$pid, 'name'=>$p['name'] ?? $pid, 'stage'=>$p['stage'] ?? '', 'cfg'=>false];
    }
    return array_values($out);
}
// Group a gallery (images_all) into ordered beats. Ungrouped images fall into one bucket.
function ck_beats(array $imgs): array {
    $groups = [];
    foreach ($imgs as $im) { $g = ($im['group'] ?? '') === '' ? 'Ungrouped' : $im['group']; $groups[$g][] = $im; }
    $bn = fn($s) => preg_match('/(\d+)/', (string)$s, $m) ? (int)$m[1] : 9999;
    uksort($groups, function($a,$b) use ($bn){ if($a==='Ungrouped') return 1; if($b==='Ungrouped') return -1; return $bn($a) <=> $bn($b) ?: strcmp($a,$b); });
    return $groups;
}
// The newest non-terminal job for a project (what the cockpit is "watching"), or null.
function ck_active_job(string $pid): ?array {
    $live = ['open','claimed','running','blocked','needs_login','stopping'];
    $best = null;
    foreach (jobs_all() as $j) {
        if (($j['projectId'] ?? '') !== $pid) continue;
        if (!in_array($j['status'] ?? '', $live, true)) continue;
        if ($best === null || ($j['createdAt'] ?? '') > ($best['createdAt'] ?? '')) $best = $j;
    }
    return $best;
}
// Append a new job to the global store under lock; returns the job id.
function ck_enqueue(array $job): string {
    $job['id'] = 'job_' . nid();
    $job += ['status'=>'open','progress'=>['done'=>0,'total'=>0,'note'=>''],'stopRequested'=>false,'comments'=>[],'seen'=>[],'createdAt'=>date('c')];
    s_with_lock(JOBS_FILE, function($jobs) use ($job){ $jobs[] = $job; return ['data'=>$jobs,'result'=>true]; });
    return $job['id'];
}

// ---- version lineage (iterative refinement) --------------------------------
// A derived version records the PARENT image it was edited from + the adjustment
// note. Walk parent links to compute, per file: chain root, version depth (1-based),
// and direct children. Cycle-safe; originals (no parent) are their own root at v1.
// No backfill needed: missing fields => treated as an original.
function ck_lineage(array $imgs): array {
    $by = [];
    foreach ($imgs as $m) { $f = $m['file'] ?? ''; if ($f !== '') $by[$f] = $m; }
    $rootOf = []; $verOf = []; $children = [];
    foreach ($by as $f => $m) {
        $chain = [$f]; $cur = $f; $seen = [$f => true]; $guard = 0;     // walk up to the root, cycle-safe
        while (isset($by[$cur]) && ($p = (string)($by[$cur]['parent'] ?? '')) !== '' && isset($by[$p]) && empty($seen[$p]) && $guard++ < 128) {
            $cur = $p; $seen[$p] = true; $chain[] = $p;
        }
        $rootOf[$f] = $cur;              // top reachable ancestor (== $f for originals)
        $verOf[$f]  = count($chain);     // distance from root + 1
    }
    foreach ($by as $f => $m) {
        $p = (string)($m['parent'] ?? '');
        if ($p !== '' && $p !== $f && isset($by[$p])) $children[$p][] = $f;
    }
    return ['root'=>$rootOf, 'ver'=>$verOf, 'children'=>$children];
}
// Order one beat's images so each root is immediately followed by its descendants
// (depth-first, by ts), so a base sits next to its v2 / v3. Stragglers appended.
function ck_order_lineage(array $list, array $lin): array {
    $children = $lin['children'];
    $inBeat = []; foreach ($list as $m) { $f = $m['file'] ?? ''; if ($f !== '') $inBeat[$f] = $m; }
    $roots = [];
    foreach ($list as $m) { $p = (string)($m['parent'] ?? ''); if ($p === '' || !isset($inBeat[$p])) $roots[] = $m; }
    usort($roots, fn($a,$b)=>($a['ts'] ?? 0) <=> ($b['ts'] ?? 0));
    $out = []; $emitted = [];
    $emit = function($f) use (&$emit, &$out, &$emitted, $inBeat, $children) {
        if ($f === '' || isset($emitted[$f]) || !isset($inBeat[$f])) return;
        $emitted[$f] = true; $out[] = $inBeat[$f];
        $kids = array_values(array_filter($children[$f] ?? [], fn($k)=>isset($inBeat[$k])));
        usort($kids, fn($x,$y)=>(($inBeat[$x]['ts'] ?? 0)) <=> (($inBeat[$y]['ts'] ?? 0)));
        foreach ($kids as $k) $emit($k);
    };
    foreach ($roots as $r) $emit($r['file'] ?? '');
    foreach ($list as $m) { $f = $m['file'] ?? ''; if (!isset($emitted[$f])) { $emitted[$f] = true; $out[] = $m; } }
    return $out;
}
// Assemble an image-to-image EDIT prompt from a short nudge: change ONLY this, keep all else.
function ck_adjust_prompt(string $note, string $wardrobe = ''): string {
    $p = trim($note);
    if ($p !== '' && !preg_match('/[.!?]$/u', $p)) $p .= '.';
    $p .= ' Keep the same composition, character identity, pose, framing, wardrobe and background — change ONLY what this note asks.';
    if (trim($wardrobe) !== '') $p .= ' Wardrobe stays: ' . trim($wardrobe) . '.';
    return mb_substr($p, 0, 1200);
}

// ---- reference auto-categorize helpers ------------------------------------
// Guess a reference's kind from its aspect ratio (rough; the user fixes faces).
function ck_kind_from_shape(string $path): string {
    $s = @getimagesize($path); if (!$s || $s[0] <= 0 || $s[1] <= 0) return 'view';
    $r = $s[1] / $s[0];                       // height / width
    if ($r >= 1.3) return 'body';             // tall portrait -> full figure / body tier
    if ($r <= 0.7) return 'scene';            // wide landscape -> scene / location
    return 'view';                            // squarish -> turnaround / view
}
// 64-bit difference hash from an image (same method as the organizer's Group-similar).
function ck_dhash(string $path): ?array {
    if (!function_exists('imagecreatefromstring')) return null;
    $data = @file_get_contents($path); if ($data === false) return null;
    $im = @imagecreatefromstring($data); if (!$im) return null;
    $W = 9; $H = 8; $sm = imagecreatetruecolor($W, $H);
    imagecopyresampled($sm, $im, 0,0,0,0, $W,$H, imagesx($im), imagesy($im));
    $bits = [];
    for ($y = 0; $y < $H; $y++) { $prev = null;
        for ($x = 0; $x < $W; $x++) { $c = imagecolorat($sm, $x, $y);
            $l = (int)(0.299*(($c>>16)&0xFF) + 0.587*(($c>>8)&0xFF) + 0.114*($c&0xFF));
            if ($prev !== null) $bits[] = ($l > $prev) ? 1 : 0; $prev = $l; } }
    imagedestroy($sm); imagedestroy($im); return $bits;
}
function ck_ham(array $a, array $b): int { $d=0; $n=min(count($a),count($b)); for($i=0;$i<$n;$i++) if($a[$i]!==$b[$i]) $d++; return $d + abs(count($a)-count($b)); }
// AI auto-tag (dormant until a key is dropped in studio/data/ai.json). Returns [kind,char,label] or null.
function ck_ai_cfg(): ?array { $f = SDATA . '/ai.json'; if (!is_file($f)) return null; $j = s_read($f, []); return !empty($j['key']) ? $j : null; }
function ck_ai_classify(string $imgPath, string $script): ?array {
    $cfg = ck_ai_cfg(); if (!$cfg || !is_file($imgPath) || !function_exists('curl_init')) return null;
    $data = @file_get_contents($imgPath); if ($data === false) return null;
    $ext = ext_of($imgPath); $mime = $ext==='png'?'image/png':($ext==='webp'?'image/webp':($ext==='gif'?'image/gif':'image/jpeg'));
    $sys = 'You categorize reference images for a comic. Reply ONLY with compact JSON: {"kind":"face|body|view|scene|prop","char":"<character name, or empty for scenes/props>","label":"<2-4 word note>"}. kind: face=head/face closeup of a person; body=full-figure physique of a person; view=character turnaround / multi-angle sheet; prop=a standalone object/item/costume piece/vehicle with no person; scene=location/background/environment with no main character. If the image has a printed title, header or panel caption overlaid on it (a reference-sheet label), READ that text and use it for char and label — e.g. a sheet titled "GYM EXTERIOR / LOCATION REFERENCE" means kind=scene and char="Gym exterior". Trust an overlaid sheet title over your own guess; ignore incidental in-scene signage unless it actually names the location.';
    if (trim($script) !== '') $sys .= ' The comic cast and scenes (use these exact names when you recognize a character): ' . mb_substr($script, 0, 4000);
    $payload = json_encode(['model'=>$cfg['model'] ?? 'claude-haiku-4-5', 'max_tokens'=>120, 'system'=>$sys,
        'messages'=>[['role'=>'user','content'=>[
            ['type'=>'image','source'=>['type'=>'base64','media_type'=>$mime,'data'=>base64_encode($data)]],
            ['type'=>'text','text'=>'Categorize this reference image. JSON only.']]]]]);
    $ch = curl_init('https://api.anthropic.com/v1/messages');
    curl_setopt_array($ch, [CURLOPT_POST=>true, CURLOPT_RETURNTRANSFER=>true, CURLOPT_TIMEOUT=>30,
        CURLOPT_HTTPHEADER=>['content-type: application/json','anthropic-version: 2023-06-01','x-api-key: '.$cfg['key']],
        CURLOPT_POSTFIELDS=>$payload]);
    $resp = curl_exec($ch); $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE); curl_close($ch);
    if (!$resp || $code >= 400) return null;
    $j = json_decode($resp, true); $txt = $j['content'][0]['text'] ?? '';
    if (preg_match('/\{.*\}/s', $txt, $m)) $txt = $m[0];
    $o = json_decode($txt, true); if (!is_array($o)) return null;
    $kind = in_array($o['kind'] ?? '', ['face','body','view','scene','prop'], true) ? $o['kind'] : null;
    return ['kind'=>$kind, 'char'=>mb_substr(trim((string)($o['char'] ?? '')),0,40), 'label'=>mb_substr(trim((string)($o['label'] ?? '')),0,80)];
}
// AI script -> page/panel shotlist. Returns a $c['plan'] array (pages -> panels) or null.
function ck_ai_breakdown(string $script, string $cast): ?array {
    $cfg = ck_ai_cfg(); if (!$cfg || !function_exists('curl_init') || trim($script) === '') return null;
    $sys = 'You are a comic script breakdown artist. Turn the script into a page-by-page shotlist. Reply ONLY with JSON of the form {"pages":[{"stage":"","panels":[{"id":"p1-1","beat":"one vivid sentence of what we SEE in this panel","camera":"shot size + angle e.g. wide low-angle","location":"where","characters":["names present"],"dialogue":"spoken line(s) or empty"}]}]}. Use 3 to 5 panels per page. Make beats visual and specific (action, expression, staging) not summary. Use the provided cast names. Break down the OPENING of the story, the first 6 to 10 pages. '
        . 'The page-level "stage" tags a character-progression arc so each page pulls the right version of the cast. ONLY set it when the script is clearly a transformation / progression story (a character visibly changes physique, e.g. muscle growth): use "pre" for pages BEFORE the change begins, "mid" while it is happening, "post" once the character has transformed. If the story is NOT such an arc, set "stage" to "" (empty) on every page. Do NOT invent a transformation the script does not describe — when unsure, leave it "". '
        . 'Output compact JSON only, no prose, no markdown fences.';
    if (trim($cast) !== '') $sys .= ' Cast: ' . mb_substr($cast, 0, 500) . '.';
    $payload = json_encode(['model'=>'claude-sonnet-4-6', 'max_tokens'=>3500, 'system'=>$sys,
        'messages'=>[['role'=>'user', 'content'=>"SCRIPT:\n" . mb_substr($script, 0, 16000)]]]);
    $ch = curl_init('https://api.anthropic.com/v1/messages');
    curl_setopt_array($ch, [CURLOPT_POST=>true, CURLOPT_RETURNTRANSFER=>true, CURLOPT_TIMEOUT=>100,
        CURLOPT_HTTPHEADER=>['content-type: application/json', 'anthropic-version: 2023-06-01', 'x-api-key: '.$cfg['key']],
        CURLOPT_POSTFIELDS=>$payload]);
    $resp = curl_exec($ch); $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE); curl_close($ch);
    if (!$resp || $code >= 400) return null;
    $j = json_decode($resp, true); $txt = $j['content'][0]['text'] ?? '';
    if (preg_match('/\{.*\}/s', $txt, $m)) $txt = $m[0];
    $o = json_decode($txt, true); $pages = $o['pages'] ?? null;
    if (!is_array($pages) || !$pages) return null;
    $out = []; $pi = 0;
    foreach ($pages as $pg) {
        $pi++; $panels = [];
        foreach ((array)($pg['panels'] ?? []) as $qi => $pn) {
            if (!is_array($pn)) continue;
            $panels[] = [
                'id'         => mb_substr((string)($pn['id'] ?? ('p'.$pi.'-'.($qi+1))), 0, 20),
                'beat'       => mb_substr((string)($pn['beat'] ?? ''), 0, 400),
                'camera'     => mb_substr((string)($pn['camera'] ?? ''), 0, 80),
                'location'   => mb_substr((string)($pn['location'] ?? ''), 0, 80),
                'characters' => array_slice(array_map(fn($x)=>mb_substr((string)$x,0,40), (array)($pn['characters'] ?? [])), 0, 6),
                'dialogue'   => mb_substr((string)($pn['dialogue'] ?? ''), 0, 300),
            ];
        }
        if ($panels) $out[] = ['stage'=>ck_stage_key((string)($pg['stage'] ?? '')), 'panels'=>$panels];
    }
    return $out ?: null;
}
// AI prompt-polish: elaborate a planned panel's flat template into ONE director-grade Flow prompt.
// ONE claude-sonnet-4-6 call. Looks come from the ATTACHED refs (names only here, never prose —
// per refs-are-truth). Used by the production guide (shots.php). Returns the prompt string or null.
function ck_ai_polish(array $pn, array $siblings, array $charNames, string $wardrobe, string $style): ?string {
    $cfg = ck_ai_cfg(); if (!$cfg || !function_exists('curl_init')) return null;
    $sys = 'You are a comic shot director. Rewrite a flat panel template into ONE vivid, director-grade image-generation prompt for a photoreal 3D/CGI comic panel. '
        . 'Order the prompt: (1) shot size + angle, (2) lighting — source, direction, colour temperature, shadows, (3) staging / pose / the character\'s EXACT named emotion, (4) foreground / background depth staging, (5) colour palette + lens / depth-of-field. '
        . 'CRITICAL: describe ONLY action, camera, lighting, staging and mood — NEVER describe a character\'s face, body, hair or wardrobe in prose (their look comes from attached reference images). Refer to characters by name only. '
        . 'Do NOT invent props, accessories, watches or jewellery. Do NOT let any reference render as a literal object in the scene. Include ONLY the named characters — no background extras. Name the emotion explicitly. '
        . 'Do NOT add any speech balloons, captions, SFX or lettering — text is appended separately in a consistent house style; describe only the picture. '
        . 'Vary the camera from the other panels on the page. Keep it to 2-4 sentences. Output ONLY the prompt text — no preamble, no quotes, no markdown.';
    $ctx  = 'STYLE: ' . ($style !== '' ? $style : 'Photoreal 3D CGI / DAZ3D render') . "\n";
    $ctx .= 'PANEL: ' . trim((string)($pn['beat'] ?? '')) . "\n";
    if (!empty($pn['camera']))   $ctx .= 'Suggested camera: ' . trim((string)$pn['camera']) . "\n";
    if (!empty($pn['location'])) $ctx .= 'Location: ' . trim((string)$pn['location']) . "\n";
    if ($charNames)              $ctx .= 'Characters in frame (names only — looks come from refs): ' . implode(', ', $charNames) . "\n";
    if (trim($wardrobe) !== '')  $ctx .= 'Wardrobe continuity: ' . trim($wardrobe) . "\n";
    if ($siblings) { $sib = array_values(array_filter(array_map(fn($s)=>trim((string)($s['camera'] ?? '')), $siblings))); if ($sib) $ctx .= 'Other panels on this page use these cameras (differ from them): ' . implode(' / ', $sib) . "\n"; }
    $payload = json_encode(['model'=>'claude-sonnet-4-6', 'max_tokens'=>400, 'system'=>$sys,
        'messages'=>[['role'=>'user', 'content'=>$ctx]]]);
    $ch = curl_init('https://api.anthropic.com/v1/messages');
    curl_setopt_array($ch, [CURLOPT_POST=>true, CURLOPT_RETURNTRANSFER=>true, CURLOPT_TIMEOUT=>60,
        CURLOPT_HTTPHEADER=>['content-type: application/json', 'anthropic-version: 2023-06-01', 'x-api-key: '.$cfg['key']],
        CURLOPT_POSTFIELDS=>$payload]);
    $resp = curl_exec($ch); $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE); curl_close($ch);
    if (!$resp || $code >= 400) return null;
    $j = json_decode($resp, true); $txt = trim((string)($j['content'][0]['text'] ?? ''));
    $txt = trim($txt, " \t\n\r\"'`");
    return $txt !== '' ? mb_substr($txt, 0, 1200) : null;
}

$id     = preg_replace('/[^a-z0-9-]/', '', (string)($_GET['p'] ?? ''));
$cfile  = $id !== '' ? creator_file($id) : '';
$proj   = $id !== '' ? project_get($id) : null;
$gallery = $id !== '' ? images_all($id) : [];
$hasCockpit = $id !== '' && (is_file($cfile) || $proj !== null);

// ---- live poll endpoint (JSON): cheap signature of gallery + job state ----
if ($id !== '' && isset($_GET['poll'])) {
    header('Content-Type: application/json');
    header('X-Robots-Tag: noindex');
    $c = is_file($cfile) ? s_read($cfile, []) : [];
    $job = ck_active_job($id);
    $state = $job['status'] ?? ($c['run']['state'] ?? 'idle');
    if (!empty($job['stopRequested']) && in_array($state, ['claimed','running','open'], true)) $state = 'stopping';
    $workerLive = $job && in_array($state, ['claimed','running','stopping'], true) && (time() - (int)($job['heartbeatAt'] ?? 0)) < 40;
    $waiting = $job && in_array(($job['status'] ?? ''), ['open','queued'], true) && !$workerLive;
    $prog = $job['progress'] ?? null;
    $progTxt = $prog && (($prog['total'] ?? 0) > 0 || ($prog['note'] ?? '') !== '')
        ? trim((($prog['total'] ?? 0) > 0 ? ($prog['done'] ?? 0) . '/' . $prog['total'] . '  ' : '') . ($prog['note'] ?? '')) : '';
    $parts = [];
    foreach ($gallery as $m) $parts[] = ($m['file'] ?? '') . ':' . ($m['rating'] ?? '') . ':' . (!empty($m['accepted']) ? '1' : '0') . ':' . ($m['group'] ?? '');
    $sig = md5(implode('|', $parts) . '#' . $state . '#' . $progTxt . '#' . ($job['id'] ?? '') . '#' . ($waiting?'w':'') . '#' . count($c['feedback'] ?? []));
    echo json_encode(['ok'=>true, 'count'=>count($gallery), 'state'=>$state, 'progress'=>$progTxt,
                      'backend'=>$job['backend'] ?? '', 'stopRequested'=>!empty($job['stopRequested']),
                      'waiting'=>$waiting, 'sig'=>$sig]);
    exit;
}

// ---- index mode: no/unknown project -> list cockpit-able projects ----
if (!$hasCockpit) {
    $list = cockpit_projects();
    ?><!doctype html><html lang="en"><head><meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1"><meta name="color-scheme" content="dark">
    <meta name="robots" content="noindex,nofollow"><title>Comic Creator · Studio</title>
    <link rel="icon" href="assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="assets/studio.css?v=<?= @filemtime(STUDIO_ROOT . '/assets/studio.css') ?>"></head><body>
    <header class="topbar"><div class="brand"><span class="dot"></span> Comic Studio</div>
      <a class="ghost" href="index.php">← Projects</a><span class="spacer"></span>
      <span class="ghost"><?= h(current_studio_user()) ?></span> <a class="ghost" href="help.php">❔ How it works</a> <a class="ghost" href="login.php?do=logout">Log out</a></header>
    <main class="wrap">
      <div class="pagehead"><h1>Comic Creator</h1></div>
      <p class="muted" style="max-width:660px">Generate comics references-first, then pages — watch panels land live, approve / disapprove, and hand feedback per panel. Pick a project to open its cockpit. <em>(The live board reads the real gallery, so Flow imports show up here now; the generation worker is the next step.)</em></p>
      <?php if (!$list): ?>
        <p class="muted">No projects yet.</p>
      <?php else: ?>
      <div class="grid">
        <?php foreach ($list as $p):
            $g = images_all($p['id']); $n = count($g);
            $acc = 0; foreach ($g as $im) if (!empty($im['accepted'])) $acc++;
            $pp = project_get($p['id']); $cov = $pp['cover'] ?? null; ?>
        <a class="pcard" href="creator.php?p=<?= h(urlencode($p['id'])) ?>">
          <div class="pcover">
            <?php if ($cov): ?><img loading="lazy" src="img.php?p=<?= h(urlencode($p['id'])) ?>&f=<?= h(urlencode($cov)) ?>&t=1" alt="">
            <?php else: ?><span class="pcover-empty"><?= h(strtoupper(substr($p['name'],0,2))) ?></span><?php endif; ?>
          </div>
          <div class="pmeta"><div class="pname"><?= h($p['name']) ?></div>
            <div class="prow"><span class="badge" style="--c:#7A7FEC">cockpit</span> <span class="muted"><?= h($p['stage']) ?></span></div>
            <div class="muted psub"><?= $n ?> panel<?= $n===1?'':'s' ?> · <?= $acc ?> approved</div></div>
        </a>
        <?php endforeach; ?>
      </div>
      <?php endif; ?>
    </main></body></html>
    <?php exit;
}

// ---- cockpit mode ----
$c = is_file($cfile) ? s_read($cfile, []) : [];
$c += ['projectId'=>$id, 'name'=>($proj['name'] ?? $id), 'stage'=>($proj['stage'] ?? ''),
       'refs'=>[], 'plan'=>[], 'feedback'=>[], 'run'=>['state'=>'idle','backend'=>'flow','account'=>'growcomics','stopRequested'=>false]];

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    csrf_check();
    $do  = $_POST['do'] ?? '';
    $run = $c['run'];
    $by  = current_studio_user();
    $c['gateMsg'] = '';

    if ($do === 'aisort_one') {                                  // incremental AI sort: classify ONE ref, return JSON (the browser drives the progress bar; no PHP timeout)
        header('Content-Type: application/json');
        if (!empty($c['refsLocked'])) { echo json_encode(['ok'=>false,'err'=>'locked']); exit; }
        if (!ck_ai_cfg())             { echo json_encode(['ok'=>false,'err'=>'no key']); exit; }
        $rid = (string)($_POST['rid'] ?? ''); $out = ['ok'=>false, 'rid'=>$rid, 'err'=>'not found'];
        foreach ($c['refs'] as &$r) if (($r['id'] ?? '') === $rid) {
            $res = ck_ai_classify(project_dir($id) . '/' . ($r['file'] ?? ''), $c['script'] ?? '');
            if ($res) { if ($res['kind']) $r['kind']=$res['kind']; if ($res['char']!=='') $r['char']=$res['char']; if ($res['label']!=='') $r['label']=$res['label'];
                        $out = ['ok'=>true, 'rid'=>$rid, 'kind'=>$r['kind'], 'char'=>$r['char'], 'label'=>$r['label']]; }
            else $out = ['ok'=>false, 'rid'=>$rid, 'err'=>'unreadable'];
            break;
        }
        unset($r);
        s_write($cfile, $c);
        echo json_encode($out); exit;
    }

    if ($do === 'shotdone') {                                    // toggle a planned panel's done flag (production guide); JSON, no reload
        header('Content-Type: application/json');
        $pid = (string)($_POST['panel'] ?? ''); $done = !empty($_POST['done']); $found = false;
        $plan = $c['plan'] ?? [];
        foreach ($plan as $pi => $pg) foreach (($pg['panels'] ?? []) as $qi => $pn)
            if (($pn['id'] ?? '') === $pid) { $plan[$pi]['panels'][$qi]['done'] = $done; $found = true; }
        if ($found) { $c['plan'] = $plan; s_write($cfile, $c); }
        echo json_encode(['ok'=>$found, 'panel'=>$pid, 'done'=>$done]); exit;
    }

    if ($do === 'breakdown') {                                   // AI: script -> page/panel plan ($c['plan']); JSON so the browser shows a working overlay
        header('Content-Type: application/json'); @set_time_limit(120);
        if (!ck_ai_cfg())                    { echo json_encode(['ok'=>false,'err'=>'Add your API key first (the AI key box in the references workspace).']); exit; }
        if (trim($c['script'] ?? '') === '') { echo json_encode(['ok'=>false,'err'=>'Add your script first (the Script panel).']); exit; }
        $cast = implode(', ', array_values(array_unique(array_filter(array_map(function($r){ $k=$r['kind']??''; return ($k==='scene'||$k==='prop')?'':trim((string)($r['char']??'')); }, $c['refs'])))));
        $plan = ck_ai_breakdown($c['script'], $cast);
        if ($plan) { $c['plan'] = $plan; s_write($cfile, $c);
            echo json_encode(['ok'=>true, 'pages'=>count($plan), 'panels'=>array_sum(array_map(fn($p)=>count($p['panels']??[]), $plan))]); }
        else echo json_encode(['ok'=>false, 'err'=>'The AI did not return a usable plan — try again (or run "test key" to confirm access).']);
        exit;
    }

    if ($do === 'adjust') {                                      // iterative refinement: derive a NEW version FROM a chosen image (image-to-image), not from refs
        header('Content-Type: application/json');
        $file = basename((string)($_POST['file'] ?? ''));
        $note = trim((string)($_POST['note'] ?? ''));
        if ($file === '' || $note === '') { echo json_encode(['ok'=>false,'err'=>'Pick an image and write an adjustment note.']); exit; }
        $src = null; foreach ($gallery as $m) if (($m['file'] ?? '')===$file && empty($m['isref'])) { $src = $m; break; }
        if (!$src) { echo json_encode(['ok'=>false,'err'=>'That image is not a panel in this project.']); exit; }
        $lin  = ck_lineage($gallery);
        $root = $lin['root'][$file] ?? $file;
        $ver  = ($lin['ver'][$file] ?? 1) + 1;
        $beat = (string)($src['group'] ?? '');
        $note = mb_substr($note, 0, 1000);
        $prompt = ck_adjust_prompt($note, $c['wardrobe'] ?? '');
        $adjId  = 'adj_' . nid();
        $jobId  = ck_enqueue([
            'projectId'=>$id, 'kind'=>'adjust', 'scope'=>'panel', 'panel'=>$beat,
            'parentFile'=>$file, 'root'=>$root, 'ver'=>$ver,
            'adjust'=>$note, 'prompt'=>$prompt, 'fromImage'=>true, 'adjustId'=>$adjId,
            'backend'=>$run['backend'] ?? 'flow', 'account'=>(($run['backend'] ?? 'flow')==='flow') ? ($run['account'] ?? 'growcomics') : '',
            'brief'=>$c['brief'] ?? '', 'wardrobe'=>$c['wardrobe'] ?? '', 'createdBy'=>$by,
        ]);
        $c['adjusts']  = $c['adjusts'] ?? [];
        $c['adjusts'][] = ['id'=>$adjId, 'parentFile'=>$file, 'root'=>$root, 'ver'=>$ver, 'beat'=>$beat,
                           'note'=>$note, 'prompt'=>$prompt, 'status'=>'pending', 'jobId'=>$jobId, 'ts'=>time(), 'by'=>$by];
        $c['feedback'] = $c['feedback'] ?? [];
        array_unshift($c['feedback'], ['ts'=>date('c'), 'by'=>$by, 'panel'=>$beat, 'text'=>'✎ adjust v'.$ver.': '.$note]);
        $c['run']['state'] = 'queued'; $c['updatedAt'] = date('c');
        s_write($cfile, $c);
        echo json_encode(['ok'=>true, 'adjustId'=>$adjId, 'ver'=>$ver, 'beat'=>$beat, 'prompt'=>$prompt]); exit;
    }

    if ($do === 'polish_one') {                                  // AI: elaborate ONE planned panel's template into a director-grade prompt (production guide / shots.php)
        header('Content-Type: application/json'); @set_time_limit(90);
        if (!ck_ai_cfg()) { echo json_encode(['ok'=>false,'err'=>'Add your API key first (the references workspace).']); exit; }
        $pid = (string)($_POST['panel'] ?? ''); $found = null; $fi = null; $fj = null; $siblings = [];
        foreach (($c['plan'] ?? []) as $pgi => $pg) foreach (($pg['panels'] ?? []) as $pqi => $pn)
            if (($pn['id'] ?? '') === $pid) { $found = $pn; $fi = $pgi; $fj = $pqi; $siblings = $pg['panels'] ?? []; }
        if ($found === null) { echo json_encode(['ok'=>false,'err'=>'panel not found']); exit; }
        $names = array_values(array_filter(array_map(fn($x)=>trim((string)$x), (array)($found['characters'] ?? []))));
        $polished = ck_ai_polish($found, $siblings, $names, $c['wardrobe'] ?? '', $c['style'] ?? '');
        if ($polished === null) { echo json_encode(['ok'=>false,'err'=>'The AI did not return a usable prompt — try again (or test your key).']); exit; }
        $polished .= ck_letter_block($c['lettering'] ?? '', (string)($found['dialogue'] ?? ''));  // dialogue panels get the consistent lettering block (no-op when there is no dialogue)
        $c['plan'][$fi]['panels'][$fj]['polished'] = $polished; $c['updatedAt'] = date('c');
        s_write($cfile, $c);
        echo json_encode(['ok'=>true, 'polished'=>$polished]); exit;
    }

    if ($do === 'polishedit') {                                  // save a hand-edited prompt (empty text clears back to the template)
        header('Content-Type: application/json');
        $pid = (string)($_POST['panel'] ?? ''); $text = trim((string)($_POST['text'] ?? '')); $found = false;
        $plan = $c['plan'] ?? [];
        foreach ($plan as $pgi => $pg) foreach (($pg['panels'] ?? []) as $pqi => $pn)
            if (($pn['id'] ?? '') === $pid) { if ($text === '') unset($plan[$pgi]['panels'][$pqi]['polished']); else $plan[$pgi]['panels'][$pqi]['polished'] = mb_substr($text, 0, 1200); $found = true; }
        if ($found) { $c['plan'] = $plan; $c['updatedAt'] = date('c'); s_write($cfile, $c); }
        echo json_encode(['ok'=>$found]); exit;
    }

    if ($do === 'queue') {
        $run['backend'] = in_array($_POST['backend'] ?? '', ['flow','higgsfield'], true) ? $_POST['backend'] : ($run['backend'] ?? 'flow');
        $run['account'] = in_array($_POST['account'] ?? '', ['growcomics','marrtrobinson'], true) ? $_POST['account'] : ($run['account'] ?? 'growcomics');
        $run['scope']   = in_array($_POST['scope'] ?? '', ['refs','page','panel','all'], true) ? $_POST['scope'] : 'page';
        if (in_array($run['scope'], ['page','panel','all'], true) && empty($c['refsLocked'])) {
            $c['gateMsg'] = 'Lock your references & scenes before generating pages.';
        } else {
            $run['jobId']   = ck_enqueue([
                'projectId'=>$id, 'kind'=>$run['scope'], 'scope'=>$run['scope'],
                'backend'=>$run['backend'], 'account'=>$run['backend']==='flow' ? $run['account'] : '',
                'brief'=>$c['brief'] ?? '', 'wardrobe'=>$c['wardrobe'] ?? '', 'lettering'=>$c['lettering'] ?? '',
                'createdBy'=>$by,
            ]);
            $run['state'] = 'queued'; $run['stopRequested'] = false; $run['queuedAt'] = date('c'); $run['queuedBy'] = $by;
        }

    } elseif ($do === 'stop') {                                  // cooperative stop: flag every live job for this project
        s_with_lock(JOBS_FILE, function($jobs) use ($id){
            foreach ($jobs as &$j) if (($j['projectId']??'')===$id && in_array($j['status']??'', ['open','claimed','running'], true)) $j['stopRequested'] = true;
            unset($j); return ['data'=>$jobs,'result'=>true];
        });
        $run['state'] = 'stopping';

    } elseif ($do === 'reset') {                                 // clear UI state + cancel any still-open jobs
        s_with_lock(JOBS_FILE, function($jobs) use ($id){
            foreach ($jobs as &$j) if (($j['projectId']??'')===$id && in_array($j['status']??'', ['open','claimed'], true)) $j['status'] = 'stopped';
            unset($j); return ['data'=>$jobs,'result'=>true];
        });
        $run['state'] = 'idle'; $run['stopRequested'] = false; $run['scope'] = null; $run['jobId'] = null;

    } elseif ($do === 'feedback') {
        $txt   = trim($_POST['text'] ?? '');
        $panel = trim($_POST['panel'] ?? '');
        if ($txt !== '') {
            $c['feedback'] = $c['feedback'] ?? [];
            array_unshift($c['feedback'], ['ts'=>date('c'), 'by'=>$by, 'panel'=>$panel, 'text'=>mb_substr($txt, 0, 2000)]);
            if ($panel !== '') {                                 // targeted feedback => enqueue a reshoot of that beat
                $rejects = [];
                foreach ($gallery as $m) if (($m['group'] ?? '') === $panel && ($m['rating'] ?? '') === 'bad') $rejects[] = $m['file'];
                $run['jobId'] = ck_enqueue([
                    'projectId'=>$id, 'kind'=>'reshoot', 'scope'=>'panel', 'panel'=>$panel,
                    'feedback'=>mb_substr($txt, 0, 2000), 'rejects'=>$rejects,
                    'backend'=>$run['backend'] ?? 'flow', 'account'=>($run['backend']??'flow')==='flow' ? ($run['account'] ?? 'growcomics') : '',
                    'createdBy'=>$by,
                ]);
                $run['state'] = 'queued'; $run['stopRequested'] = false;
            } else {                                             // general feedback => relay as a comment to the active job
                $aj = ck_active_job($id);
                if ($aj) s_with_lock(JOBS_FILE, function($jobs) use ($aj,$txt,$by){
                    foreach ($jobs as &$j) if (($j['id']??'')===$aj['id']) { $j['comments'][] = ['ts'=>date('c'),'by'=>$by,'text'=>mb_substr($txt,0,2000)]; }
                    unset($j); return ['data'=>$jobs,'result'=>true];
                });
            }
        }
    } elseif ($do === 'brief') {
        $c['brief'] = mb_substr(trim($_POST['brief'] ?? ''), 0, 4000);
    } elseif ($do === 'wardrobe') {
        $c['wardrobe'] = mb_substr(trim($_POST['wardrobe'] ?? ''), 0, 1000);
    } elseif ($do === 'lockrefs') {
        if (!empty($_POST['locked'])) {                          // freeze the approved set (so we can show WHICH ones)
            $approved = array_values(array_filter($c['refs'], fn($r)=>($r['status']??'')==='approved'));
            if (!$approved) { $c['gateMsg'] = 'Add at least one approved reference before locking.'; }
            else { $c['refsLocked']=true; $c['refsLockedAt']=date('c');
                   $c['refsLockedSet']=array_values(array_filter(array_map(fn($r)=>$r['file']??'', $approved))); }
        } else { $c['refsLocked']=false; $c['refsLockedSet']=[]; }
    } elseif ($do === 'addref') {                                // promote a live panel into the reference set
        if (empty($c['refsLocked'])) {
            $file = basename((string)($_POST['file'] ?? '')); $exists=false; $dup=false;
            foreach ($gallery as $m) if (($m['file']??'')===$file) { $exists=true; break; }
            foreach ($c['refs'] as $r) if (($r['file']??'')===$file) { $dup=true; break; }
            if ($file!=='' && $exists && !$dup) {
                $kind = in_array($_POST['kind']??'', ['face','body','view','scene','prop'], true) ? $_POST['kind'] : 'view';
                $c['refs'][] = ['id'=>nid(), 'file'=>$file, 'char'=>mb_substr(trim($_POST['char'] ?? ''),0,40),
                                'kind'=>$kind, 'label'=>mb_substr(trim($_POST['label'] ?? ''),0,80),
                                'stage'=>ck_stage_key((string)($_POST['stage'] ?? '')),
                                'status'=>'approved', 'src'=>'promoted', 'ts'=>time()];
            }
        } else { $c['gateMsg']='Unlock references to add more.'; }
    } elseif ($do === 'uploadref') {                             // bulk upload character sheets / scene plates as references
        if (empty($c['refsLocked'])) {
            $fu = $_FILES['reffile'] ?? null;
            $kindSel  = $_POST['kind'] ?? 'auto';                 // 'auto' = guess per image from shape
            $charAll  = mb_substr(trim($_POST['char'] ?? ''), 0, 40);  // set = apply to all; blank = auto-cluster
            $labelAll = mb_substr(trim($_POST['label'] ?? ''), 0, 80);
            $stageAll = ck_stage_key((string)($_POST['stage'] ?? ''));  // optional progression stage applied to the whole batch ('' = any)
            $names = $fu ? (array)($fu['name'] ?? []) : [];
            $meta = images_all($id); $newRefs = [];
            for ($i = 0; $i < count($names); $i++) {
                if ((int)($fu['error'][$i] ?? 4) !== UPLOAD_ERR_OK) continue;
                if (!is_uploaded_file($fu['tmp_name'][$i] ?? '')) continue;
                if ((int)($fu['size'][$i] ?? 0) > MAX_BYTES) continue;
                $res = store_image($fu['tmp_name'][$i], (string)$names[$i], $id);
                if (!$res) continue;
                $meta[] = ['file'=>$res['file'], 'orig'=>mb_substr((string)$names[$i],0,120),
                           'rating'=>'good','accepted'=>false,'group'=>'','tags'=>[],'isref'=>true,'ts'=>time()];
                $path = project_dir($id) . '/' . $res['file'];
                $kind = in_array($kindSel, ['face','body','view','scene','prop'], true) ? $kindSel : ck_kind_from_shape($path);
                $newRefs[] = ['id'=>nid(), 'file'=>$res['file'], 'char'=>$charAll, 'kind'=>$kind, 'label'=>$labelAll,
                              'stage'=>$stageAll, 'status'=>'pending', 'src'=>'upload', 'ts'=>time()];
            }
            $cnt = count($newRefs);
            if ($cnt) {
                // single upload = auto-approved; bulk = pending review
                if ($cnt === 1) $newRefs[0]['status'] = 'approved';
                // auto-cluster by look when no character was given (blank char => "Cast A/B/..." per look-alike group)
                if ($charAll === '' && $cnt > 1) {
                    $TH = 12; $clusters = []; $letters = range('A','Z');
                    foreach ($newRefs as $k => &$r) {
                        $tp = project_dir($id).'/thumb/'.$r['file']; if (!is_file($tp)) $tp = project_dir($id).'/'.$r['file'];
                        $hash = ck_dhash($tp); $bi = -1; $bd = $TH + 1;
                        if ($hash !== null) foreach ($clusters as $ci => $rep) { if ($rep === null) continue; $d = ck_ham($hash, $rep); if ($d < $bd) { $bd = $d; $bi = $ci; } }
                        if ($bi >= 0 && $bd <= $TH) $ci = $bi; else { $clusters[] = $hash; $ci = count($clusters) - 1; }
                        $r['char'] = 'Cast ' . ($letters[$ci] ?? ($ci + 1));
                    }
                    unset($r);
                }
                images_save($id, $meta);
                $c['refs'] = array_merge($c['refs'], $newRefs);
                $c['gateMsg'] = $cnt === 1 ? 'Reference added.'
                    : ($cnt . ' references added' . ($charAll === '' ? ' and grouped by look — rename the groups, set kinds, then approve.' : ' — set kinds and approve.'));
            } else { $c['gateMsg'] = 'Upload failed — no valid image (JPG / PNG / WebP, max 30MB).'; }
        } else { $c['gateMsg']='Unlock references to add more.'; }
    } elseif ($do === 'aisort') {                                // AI refine kinds + character names (dormant until keyed)
        if (!empty($c['refsLocked'])) { $c['gateMsg'] = 'Unlock references to sort.'; }
        elseif (!ck_ai_cfg()) { $c['gateMsg'] = 'AI sort is not set up yet — it needs an API key in studio/data/ai.json (and works best with your script). Ask Claude to enable it.'; }
        else {
            $done = 0; $fail = 0; $cap = 40;
            foreach ($c['refs'] as &$r) {
                if ($done >= $cap) break;
                if (($r['status'] ?? '') === 'approved') continue;   // only the unreviewed
                $res = ck_ai_classify(project_dir($id) . '/' . ($r['file'] ?? ''), $c['script'] ?? '');
                if ($res) { if ($res['kind']) $r['kind'] = $res['kind']; if ($res['char'] !== '') $r['char'] = $res['char']; if ($res['label'] !== '') $r['label'] = $res['label']; $done++; }
                else $fail++;
            }
            unset($r);
            $c['gateMsg'] = "AI sorted $done reference" . ($done===1?'':'s') . ($fail ? " · $fail could not be read (often explicit content the filter blocks — set those by hand)" : '') . '. Review and approve.';
        }
    } elseif ($do === 'editgroup') {                             // rename / set-kind / approve a whole reference group at once
        if (empty($c['refsLocked'])) {
            $gk = (string)($_POST['gk'] ?? '');
            $newChar = isset($_POST['char']) ? mb_substr(trim($_POST['char']),0,40) : '';
            $newKind = (isset($_POST['kind']) && in_array($_POST['kind'], ['face','body','view','scene','prop'], true)) ? $_POST['kind'] : '';
            // stage on the group select: '' = leave each ref's stage as-is; '-' = clear to any-stage; a valid key = set that stage
            $stageRaw = (string)($_POST['stage'] ?? '');
            $appr = ($_POST['approve'] ?? '') === '1';
            foreach ($c['refs'] as &$r) {
                $kd = $r['kind'] ?? ''; $rk = $kd==='scene' ? '_scenes' : ($kd==='prop' ? '_props' : ((($r['char'] ?? '')!=='') ? $r['char'] : '_'));
                if ($rk === $gk) {
                    if ($newChar !== '') $r['char'] = $newChar;
                    if ($newKind !== '') $r['kind'] = $newKind;
                    if ($stageRaw === '-') $r['stage'] = '';
                    elseif ($stageRaw !== '' && ck_stage_key($stageRaw) !== '') $r['stage'] = ck_stage_key($stageRaw);
                    if ($appr) $r['status'] = 'approved';
                }
            }
            unset($r);
        } else { $c['gateMsg']='Unlock references to edit.'; }
    } elseif ($do === 'script') {
        $c['script'] = mb_substr(trim($_POST['script'] ?? ''), 0, 20000);
    } elseif ($do === 'style') {
        $c['style'] = mb_substr(trim($_POST['style'] ?? ''), 0, 300);
    } elseif ($do === 'lettering') {                            // per-project speech-balloon / caption style spec, appended to every dialogue panel's prompt
        $c['lettering'] = mb_substr(trim($_POST['lettering'] ?? ''), 0, 800);
    } elseif ($do === 'pagestage') {                            // tag a plan PAGE with a transformation stage (so its panels pull the stage-right character refs)
        $pi = (int)($_POST['page'] ?? -1);
        $stage = ck_stage_key((string)($_POST['stage'] ?? ''));
        if (isset($c['plan'][$pi]) && is_array($c['plan'][$pi])) { $c['plan'][$pi]['stage'] = $stage; }
        else { $c['gateMsg'] = 'That page is no longer in the plan.'; }
    } elseif ($do === 'aikey') {                                 // user pastes THEIR OWN key; stored server-side in .htaccess-denied data/ai.json
        $k = trim((string)($_POST['aikey'] ?? ''));
        if (strlen($k) >= 20 && strncmp($k, 'sk-', 3) === 0) {
            s_write(SDATA . '/ai.json', ['key'=>$k, 'model'=>'claude-haiku-4-5']);
            $c['gateMsg'] = 'AI key saved — AI sort is now on. Click "test key" to confirm access and billing.';
        } else { $c['gateMsg'] = 'That does not look like an Anthropic key (it should start with sk-...). Not saved.'; }
    } elseif ($do === 'aikeydel') {
        @unlink(SDATA . '/ai.json');
        $c['gateMsg'] = 'AI key removed — AI sort is off.';
    } elseif ($do === 'aikeytest') {
        $cfg = ck_ai_cfg();
        if (!$cfg) { $c['gateMsg'] = 'No AI key is configured.'; }
        elseif (!function_exists('curl_init')) { $c['gateMsg'] = 'Server cannot make outbound requests (curl missing).'; }
        else {
            $ch = curl_init('https://api.anthropic.com/v1/messages');
            curl_setopt_array($ch, [CURLOPT_POST=>true, CURLOPT_RETURNTRANSFER=>true, CURLOPT_TIMEOUT=>20,
                CURLOPT_HTTPHEADER=>['content-type: application/json','anthropic-version: 2023-06-01','x-api-key: '.$cfg['key']],
                CURLOPT_POSTFIELDS=>json_encode(['model'=>$cfg['model'] ?? 'claude-haiku-4-5','max_tokens'=>5,'messages'=>[['role'=>'user','content'=>'ping']]])]);
            $resp = curl_exec($ch); $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE); curl_close($ch);
            if ($code >= 200 && $code < 300) { $c['gateMsg'] = 'AI key works — access and billing are good. AI sort is ready to use.'; }
            else { $j = json_decode((string)$resp, true); $c['gateMsg'] = 'AI key test failed: ' . mb_substr((string)($j['error']['message'] ?? ('HTTP '.$code)), 0, 160); }
        }
    } elseif ($do === 'editref') {                               // re-categorize / approve a reference
        if (empty($c['refsLocked'])) {
            $rid=(string)($_POST['rid'] ?? '');
            foreach ($c['refs'] as &$r) if (($r['id']??'')===$rid) {
                if (isset($_POST['kind'])  && in_array($_POST['kind'],['face','body','view','scene','prop'],true)) $r['kind']=$_POST['kind'];
                if (isset($_POST['char']))  $r['char']  = mb_substr(trim($_POST['char']),0,40);
                if (isset($_POST['label'])) $r['label'] = mb_substr(trim($_POST['label']),0,80);
                if (isset($_POST['stage'])) $r['stage'] = ck_stage_key((string)$_POST['stage']);   // '' (any-stage option) clears it
                if (isset($_POST['status']) && in_array($_POST['status'],['approved','needed'],true)) $r['status']=$_POST['status'];
            }
            unset($r);
        } else { $c['gateMsg']='Unlock references to edit.'; }
    } elseif ($do === 'removeref') {                             // drop a reference (and its uploaded image, if orphaned)
        if (empty($c['refsLocked'])) {
            $rid=(string)($_POST['rid'] ?? ''); $gone=null;
            $c['refs']=array_values(array_filter($c['refs'], function($r) use ($rid,&$gone){ if(($r['id']??'')===$rid){ $gone=$r; return false; } return true; }));
            if ($gone && ($gone['src']??'')==='upload') {
                $f=$gone['file']??''; $still=false; foreach ($c['refs'] as $r) if (($r['file']??'')===$f) { $still=true; break; }
                if ($f!=='' && !$still) {
                    images_save($id, array_values(array_filter(images_all($id), fn($m)=>($m['file']??'')!==$f)));
                    @unlink(project_dir($id).'/'.basename($f)); @unlink(project_dir($id).'/thumb/'.basename($f));
                }
            }
        } else { $c['gateMsg']='Unlock references to remove.'; }
    } elseif ($do === 'adjustresult') {                          // the refined version came back from Flow — store it + chain it under its parent
        $adjId = (string)($_POST['adjustId'] ?? ''); $rec = null; $ri = null;
        foreach (($c['adjusts'] ?? []) as $k=>$a) if (($a['id'] ?? '')===$adjId && ($a['status'] ?? '')==='pending') { $rec=$a; $ri=$k; break; }
        $fu = $_FILES['resultfile'] ?? null;
        if (!$rec) { $c['gateMsg']='That adjustment request is no longer pending.'; }
        elseif (!$fu || ((int)($fu['error'] ?? 1))!==UPLOAD_ERR_OK || !is_uploaded_file($fu['tmp_name'] ?? '')) { $c['gateMsg']='No image received — drop the new version onto the upload slot.'; }
        elseif (((int)($fu['size'] ?? 0)) > MAX_BYTES) { $c['gateMsg']='That image is too big (max 30MB).'; }
        else {
            $res = store_image($fu['tmp_name'], (string)($fu['name'] ?? 'adjust.png'), $id);
            if (!$res) { $c['gateMsg']='Could not store that image (JPG / PNG / WebP only).'; }
            else {
                $meta = images_all($id);
                $pgk = ''; foreach ($meta as $mm) if (($mm['file'] ?? '')===$rec['parentFile']) { $pgk = (string)($mm['genkey'] ?? ''); break; }
                $meta[] = ['file'=>$res['file'], 'orig'=>mb_substr((string)($fu['name'] ?? 'adjust.png'),0,120),
                           'rating'=>'unrated','accepted'=>false,'group'=>$rec['beat'],'tags'=>[],'ts'=>time(),
                           'genkey'=>$pgk,   // inherit parent's genkey so "Group similar" keeps the chain in one beat
                           'parent'=>$rec['parentFile'],'root'=>$rec['root'],'ver'=>(int)$rec['ver'],'adjust'=>$rec['note'],'derived'=>true];
                images_save($id, $meta);
                $c['adjusts'][$ri]['status']='done'; $c['adjusts'][$ri]['resultFile']=$res['file']; $c['adjusts'][$ri]['doneAt']=date('c');
                $jid = (string)($rec['jobId'] ?? '');
                if ($jid !== '') s_with_lock(JOBS_FILE, function($jobs) use ($jid){ foreach ($jobs as &$j) if (($j['id']??'')===$jid && in_array($j['status']??'',['open','claimed','running'],true)) $j['status']='done'; unset($j); return ['data'=>$jobs,'result'=>true]; });
                $c['gateMsg']='Version v'.(int)$rec['ver'].' added under '.$rec['beat'].' — review it on the board.';
            }
        }
    } elseif ($do === 'adjustcancel') {                          // abandon a pending refinement request + cancel its job
        $adjId = (string)($_POST['adjustId'] ?? '');
        foreach (($c['adjusts'] ?? []) as $k=>$a) if (($a['id'] ?? '')===$adjId && ($a['status'] ?? '')==='pending') {
            $c['adjusts'][$k]['status']='abandoned';
            $jid = (string)($a['jobId'] ?? '');
            if ($jid !== '') s_with_lock(JOBS_FILE, function($jobs) use ($jid){ foreach ($jobs as &$j) if (($j['id']??'')===$jid && in_array($j['status']??'',['open','claimed'],true)) $j['status']='stopped'; unset($j); return ['data'=>$jobs,'result'=>true]; });
            $c['gateMsg']='Adjustment cancelled.'; break;
        }
    }
    $c['run'] = $run; $c['updatedAt'] = date('c');
    s_write($cfile, $c);   // lazily creates the creator config for gallery-only projects
    if (($_POST['ret'] ?? '') === 'refs')  { header('Location: refs.php?p=' . urlencode($id)); exit; }
    if (($_POST['ret'] ?? '') === 'shots') { header('Location: shots.php?p=' . urlencode($id)); exit; }
    header('Location: creator.php?p=' . urlencode($id) . '#run'); exit;
}

// references (left) grouped by character; scenes/locations get their own group
$byChar = [];
foreach ($c['refs'] as $r) { $kd = $r['kind'] ?? ''; $k = $kd==='scene' ? '_scenes' : ($kd==='prop' ? '_props' : ((($r['char'] ?? '') !== '') ? $r['char'] : '_')); $byChar[$k][] = $r; }
$refTotal = count($c['refs']); $refOk = count(array_filter($c['refs'], fn($r)=>($r['status']??'')==='approved'));
$refFiles = array_values(array_filter(array_map(fn($r)=>$r['file']??'', $c['refs'])));   // panels already used as a ref

// live panels (right) from the real gallery — reference uploads are tagged isref, so exclude them
$panels = array_values(array_filter($gallery, fn($m)=>empty($m['isref'])));
$beats = ck_beats($panels);
$lin   = ck_lineage($panels);                                   // version chains (base -> v2 -> v3) within each beat
$pendByBeat = [];                                               // pending refinement requests, grouped by beat
foreach (($c['adjusts'] ?? []) as $a) if (($a['status'] ?? '')==='pending') $pendByBeat[(string)($a['beat'] ?? '')][] = $a;
$galN  = count($panels);
$accN  = count(array_filter($panels, fn($m)=>!empty($m['accepted'])));
$planN = array_sum(array_map(fn($p)=>count($p['panels']??[]), $c['plan']));

$run = $c['run'];
$activeJob = ck_active_job($id);
$state = $activeJob['status'] ?? ($run['state'] ?? 'idle');
if (!empty($activeJob['stopRequested']) && in_array($state, ['open','claimed','running'], true)) $state = 'stopping';
$workerLive = $activeJob && in_array($state, ['claimed','running','stopping'], true) && (time() - (int)($activeJob['heartbeatAt'] ?? 0)) < 40;
$waiting = $activeJob && in_array(($activeJob['status'] ?? ''), ['open','queued'], true) && !$workerLive;
$progTxt = '';
if ($activeJob && !empty($activeJob['progress'])) { $pr = $activeJob['progress']; $progTxt = trim(((($pr['total']??0)>0) ? ($pr['done']??0).'/'.$pr['total'].'  ' : '') . ($pr['note'] ?? '')); }
$stateColor = ['idle'=>'#6F7380','queued'=>'#EF9F27','open'=>'#EF9F27','claimed'=>'#EF9F27','running'=>'#1D9E75','stopping'=>'#E24B4A','stopped'=>'#E24B4A','blocked'=>'#E24B4A','needs_login'=>'#E24B4A','error'=>'#E24B4A','done'=>'#378ADD'][$state] ?? '#6F7380';
$charName = fn($k) => $k === '_scenes' ? 'Scenes & locations' : ($k === '_props' ? 'Props & objects' : ($k === '_' ? 'Uncategorized' : ucwords(str_replace('-', ' ', $k))));
?><!doctype html><html lang="en"><head>
<meta name="viewport" content="width=device-width, initial-scale=1"><meta name="color-scheme" content="dark">
<meta name="robots" content="noindex,nofollow"><title><?= h($c['name']) ?> · Comic Creator</title>
<link rel="icon" href="assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="assets/studio.css?v=<?= @filemtime(STUDIO_ROOT . '/assets/studio.css') ?>"></head><body>
<header class="topbar" style="border-bottom:2px solid #7A7FEC"><div class="brand"><span class="dot"></span> Comic Studio <span style="background:#7A7FEC;color:#0B0C10;font-size:11px;font-weight:800;letter-spacing:.04em;border-radius:999px;padding:2px 9px;margin-left:6px">🎬 COMIC CREATOR</span></div>
  <a class="ghost" href="index.php">← Projects</a>
  <?php if ($proj): ?><a class="ghost" href="project.php?p=<?= h(urlencode($id)) ?>">Gallery / organize</a><?php endif; ?>
  <span class="spacer"></span>
  <span class="ghost"><?= h(current_studio_user()) ?></span> <a class="ghost" href="help.php">❔ How it works</a> <a class="ghost" href="login.php?do=logout">Log out</a></header>

<style>
.ck-bg{--surface:#14151C;--bg2:#101116;--border:#23252E;--border2:#2E3140;--muted:#9CA0AC}
.ck-head{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:6px}
.ck-sub{color:#9CA0AC;font-size:13.5px;margin:0 0 18px}
.ck-run{position:sticky;top:0;z-index:5;background:#14151C;border:1px solid #2E3140;border-radius:12px;padding:14px 16px;margin-bottom:20px}
.ck-runrow{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.ck-pill{display:inline-flex;align-items:center;gap:6px;font-size:12px;font-weight:700;padding:4px 11px;border-radius:999px;color:#fff;text-transform:capitalize}
.ck-pill .dot{width:8px;height:8px;border-radius:50%;background:currentColor;opacity:.9}
.ck-sel{background:#101116;border:1px solid #2E3140;color:#F2F2F4;border-radius:8px;padding:7px 10px;font:13px Inter,sans-serif}
.ck-fb{display:flex;gap:8px;margin-top:12px;align-items:flex-start}
.ck-fb textarea{flex:1;background:#101116;border:1px solid #2E3140;color:#F2F2F4;border-radius:9px;padding:9px 11px;font:14px Inter,sans-serif;resize:vertical;min-height:42px}
.ck-fbpanel{font-size:11.5px;color:#fac775;margin-top:6px;display:none}
.ck-cols{display:grid;grid-template-columns:340px minmax(0,1fr);gap:20px;align-items:start}
@media(max-width:880px){.ck-cols{grid-template-columns:1fr}}
.ck-panel{background:#14151C;border:1px solid #23252E;border-radius:12px;padding:16px 18px}
.ck-panel h2{font-size:15px;font-weight:700;margin:0 0 4px}
.ck-cap{color:#9CA0AC;font-size:12.5px;margin:0 0 14px}
.ck-refgroup{margin-bottom:14px}
.ck-refgroup h3{font-size:12px;text-transform:uppercase;letter-spacing:.05em;color:#9CA0AC;margin:0 0 7px}
.ck-ref{display:flex;align-items:center;gap:9px;padding:7px 9px;border:1px solid #2E3140;border-radius:9px;margin-bottom:6px;background:#101116}
.ck-ref .tile{width:30px;height:30px;border-radius:6px;flex:none;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:800;color:#0B0C10}
.ck-ref .lbl{flex:1;font-size:13px;min-width:0}
.ck-ref .st{font-size:10.5px;font-weight:700;padding:2px 7px;border-radius:999px;white-space:nowrap}
.ck-st-approved{background:rgba(29,158,117,.18);color:#6fe0bd}
.ck-st-needed{background:rgba(239,159,39,.16);color:#fac775}
/* reference thumbnails */
.ck-refgrid{display:grid;grid-template-columns:repeat(2,1fr);gap:9px;margin-top:2px}
.ck-refcard{border:1px solid #2E3140;border-radius:9px;overflow:hidden;background:#101116;position:relative}
.ck-refcard.locked{border-color:#1D9E75}
.ck-refcard img{display:block;width:100%;aspect-ratio:3/4;object-fit:cover;background:#0B0C10;cursor:zoom-in}
.ck-reftag{position:absolute;top:5px;left:5px;font-size:9.5px;font-weight:800;color:#0B0C10;padding:2px 6px;border-radius:999px;text-transform:uppercase;letter-spacing:.03em}
.ck-reflock{position:absolute;top:5px;right:5px;font-size:11px;background:rgba(29,158,117,.95);color:#04231b;border-radius:999px;padding:1px 6px;font-weight:800}
.ck-refbody{padding:7px 8px}
.ck-refbody select,.ck-refbody input{width:100%;background:#0B0C10;border:1px solid #2E3140;color:#F2F2F4;border-radius:6px;padding:4px 6px;font:11.5px Inter,sans-serif;margin-bottom:4px}
.ck-refbtns{display:flex;gap:4px;margin-top:2px}
.ck-refbtns button{flex:1;background:#191B24;border:1px solid #2E3140;color:#c7cad4;border-radius:6px;padding:4px 0;font-size:11px;cursor:pointer;line-height:1.2}
.ck-refbtns button:hover{background:#23252E;color:#fff}
.ck-refbtns .b-rm:hover{background:#8a3b3b;border-color:#8a3b3b}
.ck-addref{border:1px solid #2E3140;border-radius:9px;padding:10px;margin-bottom:14px;background:#101116}
.ck-addref select{background:#0B0C10;border:1px solid #2E3140;color:#F2F2F4;border-radius:6px;padding:5px 7px;font:12px Inter,sans-serif}
.ck-addref input[type=text]{background:#0B0C10;border:1px solid #2E3140;color:#F2F2F4;border-radius:6px;padding:5px 7px;font:12px Inter,sans-serif}
.ck-shot .ck-refbadge{position:absolute;top:6px;left:6px;font-size:9.5px;font-weight:800;background:rgba(122,127,236,.95);color:#0B0C10;border-radius:999px;padding:2px 7px;z-index:2}
.ck-shot-bar .b-ref:hover{background:#5b5fd0;border-color:#5b5fd0;color:#fff}
/* live board */
.ck-bgroup{margin-bottom:18px}
.ck-bg-head{display:flex;align-items:baseline;gap:9px;margin-bottom:8px}
.ck-bg-head .ck-beat-id{font:600 12px ui-monospace,Menlo,monospace;color:#fac775}
.ck-shots{display:grid;grid-template-columns:repeat(auto-fill,minmax(165px,1fr));gap:11px}
.ck-shot{margin:0;border:2px solid #23252E;border-radius:10px;overflow:hidden;background:#0B0C10;position:relative}
.ck-shot img{display:block;width:100%;aspect-ratio:3/4;object-fit:cover;background:#0B0C10}
.ck-shot.rate-good{border-color:#1D9E75}
.ck-shot.rate-bad{border-color:#5a2b2b}.ck-shot.rate-bad img{opacity:.45}
.ck-shot.kept{box-shadow:inset 0 0 0 2px #EF9F27}
.ck-shot-bar{display:flex;gap:2px;padding:5px;background:#14151C;border-top:1px solid #23252E}
.ck-shot-bar button{flex:1;background:#191B24;border:1px solid #2E3140;color:#c7cad4;border-radius:6px;padding:5px 0;font-size:13px;cursor:pointer;line-height:1}
.ck-shot-bar button:hover{background:#23252E;color:#fff}
.ck-shot-bar .b-approve:hover{background:#1D9E75;border-color:#1D9E75}
.ck-shot-bar .b-disapprove:hover{background:#8a3b3b;border-color:#8a3b3b}
.ck-empty{border:1px dashed #2E3140;border-radius:10px;padding:18px;color:#9CA0AC;font-size:13px}
.ck-beat{border:1px solid #23252E;border-radius:10px;padding:11px 13px;margin-bottom:9px;background:#101116}
.ck-beat-head{display:flex;align-items:baseline;gap:9px;flex-wrap:wrap;margin-bottom:5px}
.ck-beat-id{font:600 12px ui-monospace,Menlo,monospace;color:#fac775}
.ck-beat-meta{font-size:11.5px;color:#6F7380}
.ck-beat-body{font-size:13.5px;line-height:1.5;color:#dfe1e7}
/* notes log — collapsible, lives BELOW the run bar so the live panels get the room */
.ck-notes{border:1px solid #2E3140;border-radius:12px;background:#101116;margin:-6px 0 20px}
.ck-notes>summary{list-style:none;cursor:pointer;display:flex;align-items:center;gap:12px;padding:11px 16px;font:700 14px Inter,sans-serif;color:#dfe1e7}
.ck-notes>summary::-webkit-details-marker{display:none}
.ck-notes>summary:hover{background:#14151C;border-radius:12px}
.ck-notes-n{display:inline-block;min-width:18px;text-align:center;background:#7A7FEC;color:#0B0C10;font-size:12px;font-weight:800;border-radius:999px;padding:1px 7px;margin-left:3px}
.ck-notes-sub{font-weight:400;font-size:12px;color:#6F7380}
.ck-notes-hint{margin-left:auto;font-weight:400;font-size:11.5px;color:#6F7380}
.ck-notes[open]>summary{border-bottom:1px solid #23252E;border-radius:12px 12px 0 0}
.ck-notes[open]>summary .ck-notes-hint{display:none}
.ck-notes-body{padding:12px 16px 14px}
.ck-notes-bar{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:12px}
.ck-notes-filter{display:inline-flex;gap:4px;background:#0B0C10;border:1px solid #23252E;border-radius:9px;padding:3px}
.ck-notes-filter button{background:none;border:none;color:#9CA0AC;font:600 12px Inter,sans-serif;padding:5px 10px;border-radius:7px;cursor:pointer}
.ck-notes-filter button:hover{color:#fff}
.ck-notes-filter button.on{background:#23252E;color:#fff}
.ck-notes-copy{margin-left:auto;background:#191B24;border:1px solid #2E3140;color:#c7cad4;border-radius:8px;padding:6px 12px;font:600 12px Inter,sans-serif;cursor:pointer}
.ck-notes-copy:hover{background:#23252E;color:#fff}
.ck-notes-list{display:flex;flex-direction:column;gap:10px;max-height:48vh;overflow:auto}
.ck-note{border-left:2px solid #7A7FEC;padding:3px 0 3px 11px}
.ck-note.system{border-left-color:#EF9F27}
.ck-note-meta{display:flex;align-items:center;gap:7px;flex-wrap:wrap;font-size:11px;color:#6F7380;margin-bottom:2px}
.ck-note-badge{font-size:10px;font-weight:800;border-radius:999px;padding:1px 7px;letter-spacing:.2px}
.ck-note-badge.panel{background:rgba(122,127,236,.18);color:#aeb2f3}
.ck-note-badge.system{background:rgba(239,159,39,.16);color:#f2c071}
.ck-note-txt{font-size:13px;color:#dfe1e7;white-space:pre-wrap;line-height:1.45}
.ck-notes-empty{font-size:12px;color:#6F7380;padding:6px 0}
.ck-newbanner{display:none;position:fixed;left:50%;bottom:20px;transform:translateX(-50%);z-index:20;background:#1D9E75;color:#fff;font-weight:700;font-size:13px;padding:9px 16px;border-radius:999px;cursor:pointer;box-shadow:0 6px 24px rgba(0,0,0,.4)}
.ck-shot img{cursor:zoom-in}
.ck-lb{position:fixed;inset:0;z-index:60;background:rgba(8,9,12,.94);display:none;flex-direction:column;align-items:center;justify-content:center;gap:14px}
.ck-lb.open{display:flex}
.ck-lb-x{position:absolute;top:16px;right:22px;background:none;border:none;color:#9CA0AC;font-size:28px;line-height:1;cursor:pointer}
.ck-lb-x:hover{color:#fff}
.ck-lb-stage{display:flex;align-items:center;gap:14px;max-width:97vw}
.ck-lb-stage img{max-width:82vw;max-height:76vh;border-radius:10px;border:2px solid #2E3140;background:#0B0C10}
.ck-lb-stage img.rate-good{border-color:#1D9E75}.ck-lb-stage img.rate-bad{border-color:#8a3b3b}
.ck-lb-arrow{background:#191B24;border:1px solid #2E3140;color:#fff;font-size:24px;width:46px;height:46px;border-radius:50%;cursor:pointer;flex:none}
.ck-lb-arrow:hover{background:#2E3140}.ck-lb-arrow:disabled{opacity:.3;cursor:default}
.ck-lb-bar{display:flex;align-items:center;gap:8px;background:#14151C;border:1px solid #2E3140;border-radius:12px;padding:10px 14px;flex-wrap:wrap;justify-content:center}
.ck-lb-bar .meta{color:#9CA0AC;font-size:12.5px;margin-right:6px}
.ck-lb-bar button{background:#191B24;border:1px solid #2E3140;color:#dfe1e7;border-radius:8px;padding:8px 13px;font-size:13.5px;cursor:pointer}
.ck-lb-bar .b-approve:hover{background:#1D9E75;border-color:#1D9E75;color:#fff}
.ck-lb-bar .b-disapprove:hover{background:#8a3b3b;border-color:#8a3b3b;color:#fff}
.ck-lb-bar .b-keep:hover,.ck-lb-bar .b-note:hover{background:#2E3140;color:#fff}
/* iterative refinement — version lineage */
.ck-shot-bar .b-adjust:hover{background:#7A7FEC;border-color:#7A7FEC;color:#0B0C10}
.ck-shot.derived{border-left:3px solid #7A7FEC}
.ck-vbadge{position:absolute;top:6px;right:6px;font-size:9.5px;font-weight:800;background:rgba(122,127,236,.96);color:#0B0C10;border-radius:999px;padding:2px 7px;z-index:2}
.ck-vbadge.pend{position:static;display:inline-block;margin:0 0 7px;background:rgba(239,159,39,.95)}
.ck-adjnote{font-size:10.5px;line-height:1.35;color:#bcbfe9;padding:5px 7px 0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.ck-pending{margin:0;border:2px dashed #5b5fd0;border-radius:10px;overflow:hidden;background:#13131d;position:relative;display:flex;flex-direction:column}
.ck-pending>img{display:block;width:100%;aspect-ratio:3/4;object-fit:cover;background:#0B0C10;opacity:.55}
.ck-pbody{padding:9px;display:flex;flex-direction:column;gap:6px}
.ck-pnote{font-size:12px;font-weight:700;color:#c9cbf2;line-height:1.35}
.ck-pcap{font-size:11px;color:#9CA0AC;line-height:1.4}
.ck-pbtn{display:block;width:100%;box-sizing:border-box;text-align:center;background:#191B24;border:1px solid #2E3140;color:#c7cad4;border-radius:7px;padding:6px 8px;font:600 11.5px Inter,sans-serif;cursor:pointer;text-decoration:none}
.ck-pbtn:hover{background:#23252E;color:#fff}
.ck-pbtn.primary{background:#7A7FEC;border-color:#7A7FEC;color:#0B0C10}
.ck-pbtn.primary:hover{background:#9296f0}
.ck-pbtn.ghost{background:none;border-color:transparent;color:#8a8d99;padding:3px}
.ck-pbtn.ghost:hover{color:#E24B4A;background:none}
.ck-pform{display:flex;flex-direction:column;gap:6px;margin:0}
.ck-pdrop{position:relative;display:block;border:1px dashed #3a3d52;border-radius:7px;padding:9px 8px;text-align:center;font-size:11px;color:#9CA0AC;cursor:pointer}
.ck-pdrop:hover{border-color:#7A7FEC;color:#c9cbf2}
.ck-pdrop input[type=file]{position:absolute;inset:0;opacity:0;width:100%;height:100%;cursor:pointer}
.ck-pdrop.has span{color:#6fe0bd}
/* adjust modal */
.ck-adj{position:fixed;inset:0;z-index:65;background:rgba(8,9,12,.92);display:none;align-items:center;justify-content:center;padding:18px}
.ck-adj.open{display:flex}
.ck-adjbox{background:#14151C;border:1px solid #2E3140;border-radius:14px;padding:18px;max-width:560px;width:100%;display:grid;grid-template-columns:150px 1fr;gap:16px}
@media(max-width:560px){.ck-adjbox{grid-template-columns:1fr}}
.ck-adjbox img{width:100%;border-radius:9px;border:1px solid #2E3140;background:#0B0C10}
.ck-adjbox h3{margin:0 0 4px;font-size:15px}
.ck-adjbox .sub{font-size:12px;color:#9CA0AC;margin:0 0 10px;line-height:1.45}
.ck-adjbox textarea{width:100%;box-sizing:border-box;background:#101116;border:1px solid #2E3140;color:#F2F2F4;border-radius:9px;padding:9px 11px;font:13.5px Inter,sans-serif;resize:vertical;min-height:78px}
.ck-adjbox .row{display:flex;gap:8px;margin-top:10px;justify-content:flex-end}
.ck-adjbox button{border:1px solid #2E3140;border-radius:8px;padding:8px 14px;font:600 13px Inter,sans-serif;cursor:pointer;background:#191B24;color:#dfe1e7}
.ck-adjbox button.primary{background:#7A7FEC;border-color:#7A7FEC;color:#0B0C10}
.ck-adjbox button.primary:disabled{opacity:.5;cursor:default}
.ck-adjerr{color:#f1a3a3;font-size:12px;margin-top:8px;display:none}
</style>

<main class="wrap ck-bg" id="cockpit" data-id="<?= h($id) ?>" data-csrf="<?= h(csrf()) ?>" style="max-width:min(1840px,95vw)">
  <div class="ck-head">
    <h1 style="margin:0"><?= h($c['name']) ?></h1>
    <span class="badge" style="--c:#7A7FEC">cockpit</span>
    <span class="muted"><?= h($c['stage'] ?? '') ?></span>
  </div>
  <p class="ck-sub">References on the left, the live panels they produce on the right. Launch a run, watch panels land, approve / disapprove, and hand feedback per panel — or stop — from the bar below.</p>

  <!-- BRIEF: what to make (rides on every queued run -> the worker) -->
  <details class="ck-panel" style="margin-bottom:14px"<?= empty($c['brief'])?' open':'' ?>>
    <summary style="cursor:pointer;font-weight:700;font-size:14px;list-style:none">📝 Brief — what to make
      <?= !empty($c['brief']) ? '<span class="muted" style="font-weight:400;font-size:12px">· set ✓</span>' : '<span style="font-weight:400;font-size:12px;color:#fac775">· not set yet</span>' ?></summary>
    <form method="post" style="margin-top:10px">
      <?= csrf_field() ?><input type="hidden" name="do" value="brief">
      <textarea name="brief" style="width:100%;min-height:74px;background:#101116;border:1px solid #2E3140;color:#F2F2F4;border-radius:9px;padding:9px 11px;font:14px Inter,sans-serif;resize:vertical" placeholder="Describe the comic / this run — characters, setting, what happens per panel. The worker uses this to generate. e.g. 'Roxy at a park touches a glowing rock and bulks up over 3 panels — photoreal CGI, keep her tank top.'"><?= h($c['brief'] ?? '') ?></textarea>
      <div style="margin-top:8px"><button class="btn primary">Save brief</button> <span class="muted" style="font-size:12px">Saved on the project; every ▶ Queue run sends it to the worker.</span></div>
    </form>
  </details>

  <!-- SCRIPT: optional story / cast / scenes — context for AI sort + the worker -->
  <details class="ck-panel" style="margin-bottom:14px">
    <summary style="cursor:pointer;font-weight:700;font-size:14px;list-style:none">📜 Script / story <span class="muted" style="font-weight:400;font-size:12px"><?= !empty($c['script']) ? '· set ✓' : '· optional — gives AI your cast &amp; scenes' ?></span></summary>
    <form method="post" style="margin-top:10px">
      <?= csrf_field() ?><input type="hidden" name="do" value="script">
      <textarea name="script" style="width:100%;min-height:90px;background:#101116;border:1px solid #2E3140;color:#F2F2F4;border-radius:9px;padding:9px 11px;font:13px Inter,sans-serif;resize:vertical" placeholder="Paste your comic script, or a character + scene list. The ✨ AI sort uses this to name characters and recognize scenes; the worker can use it for context too."><?= h($c['script'] ?? '') ?></textarea>
      <div style="margin-top:8px"><button class="btn primary">Save script</button> <span class="muted" style="font-size:12px">Used by ✨ AI sort, and later by the worker.</span></div>
    </form>
    <div style="margin-top:10px;border-top:1px solid #23252E;padding-top:10px">
      <button type="button" id="bdbtn" class="btn"<?= (empty($c['script'])||!ck_ai_cfg())?' disabled':'' ?>>📑 Break script into pages</button>
      <span class="muted" style="font-size:12px"><?= ck_ai_cfg() ? 'AI turns your saved script into a page + panel plan you can generate from' : 'add your API key (references workspace) to enable' ?></span>
    </div>
  </details>

  <!-- RUN BAR -->
  <section class="ck-run" id="run">
    <div class="ck-runrow">
      <span class="ck-pill" id="statepill" style="background:<?= $stateColor ?>"><span class="dot"></span><?= h($state) ?></span>
      <span id="ckrefresh" class="muted" style="font-size:11.5px;white-space:nowrap" title="The board auto-checks for new panels / status; reloads when something changes">↻ 4s</span>
      <span class="muted" id="progline" style="font-size:12.5px;color:#9CA0AC;<?= $progTxt===''?'display:none':'' ?>"><?= h($progTxt) ?></span>
      <?php if (!empty($run['scope'])): ?><span class="muted" style="font-size:12.5px">scope: <?= h($run['scope']) ?> · <?= h($run['backend'] ?? '') ?><?= ($run['backend']??'')==='flow' && !empty($run['account']) ? ' / '.h($run['account']) : '' ?></span><?php endif; ?>
      <span class="muted" id="stopnote" style="font-size:12.5px;color:#f3a3a2;<?= ($activeJob && !empty($activeJob['stopRequested']))?'':'display:none' ?>">⏹ stop requested — will halt at the next panel boundary</span>
      <span class="muted" id="waitnote" style="font-size:12.5px;color:#fac775;<?= $waiting?'':'display:none' ?>">⏳ queued — waiting for a worker to connect. Flow runs on the mac mini; a worker session must be watching the queue.</span>
      <?php if (!empty($c['gateMsg'])): ?><span class="muted" style="font-size:12.5px;color:#fac775"><?= h($c['gateMsg']) ?></span><?php endif; ?>
      <span class="spacer"></span>

      <form method="post" class="ck-runrow" style="gap:8px">
        <?= csrf_field() ?><input type="hidden" name="do" value="queue">
        <select name="backend" class="ck-sel" id="backend" title="Generation backend">
          <option value="flow"<?= ($run['backend']??'')==='flow'?' selected':'' ?>>Flow (free · testing)</option>
          <option value="higgsfield"<?= ($run['backend']??'')==='higgsfield'?' selected':'' ?>>Higgsfield (fast · paid)</option>
        </select>
        <select name="account" class="ck-sel" id="account" title="Flow account / profile">
          <option value="growcomics"<?= ($run['account']??'')==='growcomics'?' selected':'' ?>>growcomics (mac mini)</option>
          <option value="marrtrobinson"<?= ($run['account']??'')==='marrtrobinson'?' selected':'' ?>>marrtrobinson (laptop)</option>
        </select>
        <select name="scope" id="scope" class="ck-sel" title="What to generate">
          <option value="refs">References</option>
          <option value="page" selected>Next page</option>
          <option value="panel">Next panel</option>
          <option value="all">Whole comic</option>
        </select>
        <button class="btn primary" id="queuebtn">▶ Queue generation</button>
        <span id="gatehint" class="muted" style="display:none;font-size:11.5px;color:#fac775">🔒 lock refs first</span>
      </form>
      <form method="post"><?= csrf_field() ?><input type="hidden" name="do" value="stop"><button class="btn danger"<?= in_array($state,['idle','stopped','done'],true)?' disabled':'' ?>>⏹ Stop</button></form>
      <?php if (in_array($state, ['queued','running','stopping'], true)): ?>
      <form method="post"><?= csrf_field() ?><input type="hidden" name="do" value="reset"><button class="btn sm" title="Clear the run state">reset</button></form>
      <?php endif; ?>
    </div>
    <div class="muted" style="font-size:11.5px;margin-top:9px">▶ <b>Queue generation</b> is for the automated worker, which isn't wired up yet — it'll just park a job that nothing picks up. To make pages <b>now</b>, open the <a href="shots.php?p=<?= h(urlencode($id)) ?>" style="color:#9aa0ec">📋 Production guide</a> and run each panel in Flow by hand.</div>

    <form method="post" class="ck-fb" id="fbform">
      <?= csrf_field() ?><input type="hidden" name="do" value="feedback"><input type="hidden" name="panel" id="fbpanel" value="">
      <textarea name="text" id="fbtext" placeholder="Relay feedback to the run — e.g. “tighten this angle”, “warm the key light”, “Dana’s chest bigger”, “kill the phantom watch”… (use 💬 on a panel to target it)"></textarea>
      <button class="btn">Send feedback</button>
    </form>
    <div class="ck-fbpanel" id="fbpanellbl"></div>
  </section>

  <?php if (!empty($c['feedback'])):
        $fbAll = $c['feedback']; $fbN = count($fbAll);
        $fbPanelN = 0; foreach ($fbAll as $_f) { if (!empty($_f['panel'])) $fbPanelN++; }
        $fbSysN = $fbN - $fbPanelN; ?>
  <!-- NOTES LOG — collapsed by default so the live panels get the room (was an inline list inside the run bar) -->
  <details class="ck-notes" id="notes">
    <summary>
      <span class="ck-notes-t">💬 Notes <span class="ck-notes-n"><?= $fbN ?></span></span>
      <span class="ck-notes-sub"><?= $fbPanelN ?> panel · <?= $fbSysN ?> system</span>
      <span class="ck-notes-hint">review &amp; copy ▾</span>
    </summary>
    <div class="ck-notes-body">
      <div class="ck-notes-bar">
        <div class="ck-notes-filter" role="group" aria-label="Filter notes">
          <button type="button" class="on" data-f="all">All <?= $fbN ?></button>
          <button type="button" data-f="panel">💬 Panel <?= $fbPanelN ?></button>
          <button type="button" data-f="system">🛠 System <?= $fbSysN ?></button>
        </div>
        <button type="button" class="ck-notes-copy" id="notescopy" title="Copy every note as plain text">📋 Copy all</button>
      </div>
      <div class="ck-notes-list" id="noteslist">
        <?php foreach ($fbAll as $fb): $isPanel = !empty($fb['panel']); $ntype = $isPanel ? 'panel' : 'system'; ?>
        <div class="ck-note <?= $ntype ?>" data-type="<?= $ntype ?>">
          <div class="ck-note-meta">
            <?php if ($isPanel): ?><span class="ck-note-badge panel">💬 <?= h($fb['panel']) ?></span>
            <?php else: ?><span class="ck-note-badge system">🛠 system</span><?php endif; ?>
            <span class="ck-note-when"><?= h(date('M j, g:ia', strtotime($fb['ts'] ?? 'now'))) ?></span>
            <span class="ck-note-by"><?= h($fb['by'] ?? '') ?></span>
          </div>
          <div class="ck-note-txt"><?= h($fb['text'] ?? '') ?></div>
        </div>
        <?php endforeach; ?>
        <div class="ck-notes-empty" id="notesempty" style="display:none">No notes of this type.</div>
      </div>
    </div>
  </details>
  <?php endif; ?>

  <div class="ck-cols">
    <!-- REFERENCES -->
    <section class="ck-panel">
      <h2>References &amp; scenes</h2>
      <?php $locked = !empty($c['refsLocked']); $lockedN = count($c['refsLockedSet'] ?? []); ?>
      <a class="btn primary" href="refs.php?p=<?= h(urlencode($id)) ?>" style="display:block;text-align:center;margin:0 0 10px">🗂 Open references workspace</a>
      <div style="margin:0 0 12px;padding:8px 10px;border:1px solid <?= $locked?'#1D9E75':'#7a5a1f' ?>;background:<?= $locked?'rgba(29,158,117,.10)':'rgba(239,159,39,.08)' ?>;border-radius:9px">
        <div style="font-size:12px;font-weight:700;color:<?= $locked?'#6fe0bd':'#fac775' ?>"><?= $locked ? '🔒 '.$lockedN.' locked — pages can generate' : ($refOk ? '🔓 '.$refOk.' ready — not locked yet' : '🔓 none yet — page generation blocked') ?></div>
        <form method="post" style="margin-top:6px"><?= csrf_field() ?><input type="hidden" name="do" value="lockrefs"><input type="hidden" name="locked" value="<?= $locked?'':'1' ?>"><button class="btn sm<?= $locked?'':' primary' ?>"<?= (!$locked && $refOk<1)?' disabled':'' ?>><?= $locked?'🔓 Unlock':'🔒 Lock' ?></button> <span class="muted" style="font-size:11px"><?= $locked?'':'add &amp; sort in the workspace →' ?></span></form>
      </div>
      <?php if ($refTotal): ?>
      <p class="ck-cap" style="margin-bottom:8px"><?= $refOk ?> of <?= $refTotal ?> approved · <a href="refs.php?p=<?= h(urlencode($id)) ?>" style="color:#9aa0ec">edit in workspace</a></p>
      <?php foreach ($byChar as $gk => $list): ?>
      <div class="ck-refgroup">
        <h3><?= h($charName($gk)) ?> <span class="muted" style="font-weight:400">(<?= count($list) ?>)</span></h3>
        <div class="ck-refgrid">
        <?php foreach ($list as $r): $appr=($r['status']??'')==='approved'; $kind=$r['kind']??'view';
              $tc=['face'=>'#EF9F27','body'=>'#5DCAA5','view'=>'#7A7FEC','scene'=>'#378ADD','prop'=>'#D85A30'][$kind]??'#9CA0AC';
              $rfile=$r['file']??''; ?>
        <div class="ck-refcard<?= $locked&&$appr?' locked':'' ?>">
          <span class="ck-reftag" style="background:<?= $tc ?>"><?= h($kind) ?></span>
          <?php if ($locked&&$appr): ?><span class="ck-reflock">🔒</span><?php elseif (!$appr): ?><span class="ck-reflock" style="background:rgba(239,159,39,.92);color:#412402" title="not yet approved">•</span><?php endif; ?>
          <?php if ($rfile): ?><img loading="lazy" src="img.php?p=<?= h(urlencode($id)) ?>&f=<?= h(urlencode($rfile)) ?>&t=1" data-full="img.php?p=<?= h(urlencode($id)) ?>&f=<?= h(urlencode($rfile)) ?>" alt=""><?php endif; ?>
          <div class="ck-refbody" style="padding:5px 7px"><div style="font-size:11px;color:#9CA0AC;white-space:nowrap;overflow:hidden;text-overflow:ellipsis"><?php $rst=ck_stage_key((string)($r['stage']??'')); if ($rst!==''): ?><span style="display:inline-block;background:#3a2d5e;color:#cdb6ff;font-weight:800;font-size:9px;border-radius:999px;padding:0 5px;margin-right:4px;text-transform:uppercase"><?= h($rst) ?></span><?php endif; ?><?= h($r['char']?:($r['label']?:'—')) ?></div></div>
        </div>
        <?php endforeach; ?>
        </div>
      </div>
      <?php endforeach; ?>
      <?php if (!empty($c['wardrobe'])): ?><div class="muted" style="font-size:11px;margin-top:8px;border-top:1px solid #23252E;padding-top:8px">👕 <?= h($c['wardrobe']) ?></div><?php endif; ?>
      <?php if (!empty($c['lettering'])): ?><div class="muted" style="font-size:11px;margin-top:6px">💬 <?= h(mb_strimwidth((string)$c['lettering'], 0, 160, '…')) ?> <a href="shots.php?p=<?= h(urlencode($id)) ?>" style="color:#9aa0ec">edit</a></div><?php endif; ?>
      <?php else: ?>
      <div class="ck-empty">No references yet. <a href="refs.php?p=<?= h(urlencode($id)) ?>" style="color:#9aa0ec">Open the workspace</a> to upload &amp; sort them — it has room for a big batch.</div>
      <?php endif; ?>
    </section>

    <!-- LIVE PANELS -->
    <section class="ck-panel">
      <h2>Live panels <span class="muted" style="font-weight:400">· auto-refresh</span></h2>
      <p class="ck-cap"><?= $galN ?> panel<?= $galN===1?'':'s' ?> in this project · <?= $accN ?> approved<?= $planN ? ' · ' . $planN . ' planned' : '' ?>. <span class="muted">✓ approve · ✕ disapprove · ★ keep · ⊕ reference · ✎ adjust (refine this image) · 💬 note</span></p>
      <?php if ($planN): ?><a class="btn sm primary" href="shots.php?p=<?= h(urlencode($id)) ?>" style="margin:0 0 12px;display:inline-block">📋 Open production guide — Flow prompts + refs for all <?= $planN ?> panels</a><?php endif; ?>
      <?php if ($galN): ?>
        <?php foreach ($beats as $gname => $list): $pend = $pendByBeat[$gname] ?? []; ?>
        <div class="ck-bgroup">
          <div class="ck-bg-head"><span class="ck-beat-id"><?= h($gname) ?></span> <span class="muted"><?= count($list) ?> shot<?= count($list)===1?'':'s' ?><?= $pend ? ' · '.count($pend).' refining' : '' ?></span></div>
          <div class="ck-shots">
            <?php foreach (ck_order_lineage($list, $lin) as $im): $f = $im['file']; $rt = $im['rating'] ?? 'unrated'; $kp = !empty($im['accepted']); $isRef = in_array($f, $refFiles, true);
                  $ver = (int)($im['ver'] ?? ($lin['ver'][$f] ?? 1)); $isDer = !empty($im['parent']); $anote = (string)($im['adjust'] ?? ''); ?>
            <figure class="ck-shot rate-<?= h($rt) ?><?= $kp?' kept':'' ?><?= $isDer?' derived':'' ?>" data-file="<?= h($f) ?>" data-rating="<?= h($rt) ?>" data-accepted="<?= $kp?'1':'0' ?>" data-beat="<?= h($gname) ?>" data-ver="<?= (int)$ver ?>">
              <?php if ($isRef): ?><span class="ck-refbadge">★ ref</span><?php endif; ?>
              <?php if ($isDer): ?><span class="ck-vbadge" title="<?= h($anote!=='' ? 'adjusted: '.$anote : 'refined version') ?>">v<?= (int)$ver ?></span><?php endif; ?>
              <img loading="lazy" src="img.php?p=<?= h(urlencode($id)) ?>&f=<?= h(urlencode($f)) ?>&t=1" alt="">
              <?php if ($isDer && $anote!==''): ?><div class="ck-adjnote" title="<?= h($anote) ?>">✎ <?= h($anote) ?></div><?php endif; ?>
              <div class="ck-shot-bar">
                <button type="button" class="b-approve" data-act="approve" title="Approve — winner of this beat">✓</button>
                <button type="button" class="b-disapprove" data-act="disapprove" title="Disapprove">✕</button>
                <button type="button" class="b-keep" data-act="keep" title="Keep">★</button>
                <button type="button" class="b-ref" data-act="ref" title="<?= $isRef?'Already a reference':'Use as reference' ?>"<?= $isRef?' disabled':'' ?>>⊕</button>
                <button type="button" class="b-adjust" data-act="adjust" title="Adjust — refine THIS image with a small prompt nudge">✎</button>
                <button type="button" class="b-note" data-act="note" title="Note this panel">💬</button>
              </div>
            </figure>
            <?php endforeach; ?>
            <?php foreach ($pend as $a): $pf = (string)($a['parentFile'] ?? ''); ?>
            <figure class="ck-pending" data-adjust="<?= h($a['id'] ?? '') ?>">
              <span class="ck-vbadge pend">v<?= (int)($a['ver'] ?? 2) ?> · pending</span>
              <img loading="lazy" src="img.php?p=<?= h(urlencode($id)) ?>&f=<?= h(urlencode($pf)) ?>&t=1" alt="base">
              <div class="ck-pbody">
                <div class="ck-pnote">✎ <?= h((string)($a['note'] ?? '')) ?></div>
                <div class="ck-pcap">Edit the base in Flow (image-input / edit mode), then drop the result here.</div>
                <button type="button" class="ck-pbtn b-copyprompt" data-prompt="<?= h((string)($a['prompt'] ?? '')) ?>">⧉ Copy edit prompt</button>
                <a class="ck-pbtn" href="img.php?p=<?= h(urlencode($id)) ?>&f=<?= h(urlencode($pf)) ?>" target="_blank" rel="noopener">⤓ Open base image</a>
                <form class="ck-pform" method="post" action="creator.php?p=<?= h(urlencode($id)) ?>" enctype="multipart/form-data">
                  <?= csrf_field() ?><input type="hidden" name="do" value="adjustresult"><input type="hidden" name="adjustId" value="<?= h($a['id'] ?? '') ?>">
                  <label class="ck-pdrop"><input type="file" name="resultfile" accept="image/*" required><span>⬆ Drop / choose the new version</span></label>
                  <button class="ck-pbtn primary" type="submit">Add this version</button>
                </form>
                <form method="post" action="creator.php?p=<?= h(urlencode($id)) ?>" onsubmit="return confirm('Cancel this refinement request?')">
                  <?= csrf_field() ?><input type="hidden" name="do" value="adjustcancel"><input type="hidden" name="adjustId" value="<?= h($a['id'] ?? '') ?>">
                  <button class="ck-pbtn ghost" type="submit">Cancel</button>
                </form>
              </div>
            </figure>
            <?php endforeach; ?>
          </div>
        </div>
        <?php endforeach; ?>
      <?php elseif ($planN): ?>
        <div class="ck-empty" style="margin-bottom:12px">No panels generated yet — here’s what’s planned. Queue a run to start filling these in.</div>
        <?php foreach ($c['plan'] as $pg): foreach ($pg['panels'] as $pn): ?>
        <div class="ck-beat">
          <div class="ck-beat-head">
            <span class="ck-beat-id"><?= h($pn['id'] ?? '') ?></span>
            <span class="ck-beat-meta"><?= h($pn['size'] ?? '') ?><?= !empty($pn['camera'])?' · '.h($pn['camera']):'' ?><?= !empty($pn['location'])?' · '.h($pn['location']):'' ?></span>
          </div>
          <div class="ck-beat-body"><?= h($pn['beat'] ?? '') ?></div>
        </div>
        <?php endforeach; endforeach; ?>
      <?php else: ?>
        <div class="ck-empty">Nothing here yet. Import panels from Flow (the ⚙ extension on the Studio home page) or queue a run — they’ll appear here live.</div>
      <?php endif; ?>
    </section>
  </div>
</main>

<div class="ck-newbanner" id="newbanner">↻ New panels landed — click to refresh</div>

<div id="bdov" style="position:fixed;inset:0;z-index:70;background:rgba(8,9,12,.92);display:none;align-items:center;justify-content:center">
  <div style="background:#14151C;border:1px solid #2E3140;border-radius:14px;padding:24px 28px;text-align:center;max-width:360px;margin:16px">
    <div style="font-size:16px;font-weight:700;margin-bottom:8px">📑 Breaking down your script…</div>
    <div id="bdmsg" style="font-size:13px;color:#9CA0AC">Reading the script and planning pages — this can take up to a minute.</div>
  </div>
</div>
<div class="ck-lb" id="cklb">
  <button class="ck-lb-x" id="lbx" title="Close (Esc)">✕</button>
  <div class="ck-lb-stage">
    <button class="ck-lb-arrow" id="lbprev" title="Previous (←)">‹</button>
    <img id="lbimg" src="" alt="">
    <button class="ck-lb-arrow" id="lbnext" title="Next (→)">›</button>
  </div>
  <div class="ck-lb-bar">
    <span class="meta" id="lbmeta"></span>
    <button class="b-approve" data-act="approve" title="Approve — winner (A)">✓ Approve</button>
    <button class="b-disapprove" data-act="disapprove" title="Disapprove (D)">✕ Disapprove</button>
    <button class="b-keep" data-act="keep" title="Keep (K)">★ Keep</button>
    <button class="b-adjust" data-act="adjust" title="Adjust — refine this image (E)">✎ Adjust</button>
    <button class="b-note" data-act="note" title="Note this panel">💬 Note</button>
  </div>
</div>

<!-- ADJUST modal: derive a new version FROM this image with a small prompt nudge -->
<div class="ck-adj" id="ckadj">
  <div class="ck-adjbox">
    <img id="adjimg" src="" alt="base">
    <div>
      <h3>✎ Adjust this image</h3>
      <p class="sub">Refine the chosen image instead of re-rolling from scratch. Describe the <b>one change</b> — the rest is kept. This derives a new version <span id="adjver"></span> chained under it.</p>
      <textarea id="adjnote" maxlength="1000" placeholder="e.g. warm the key light · lower the camera ~15° · open her hand · make her shirt the gray tank · soften the jaw"></textarea>
      <div class="ck-adjerr" id="adjerr"></div>
      <div class="row">
        <button type="button" id="adjcancel">Cancel</button>
        <button type="button" class="primary" id="adjgo">Request new version</button>
      </div>
    </div>
  </div>
</div>

<script>
(function(){
  var root = document.getElementById('cockpit');
  var PID = root.dataset.id, CSRF = root.dataset.csrf;

  // --- approve / disapprove / keep / note on a panel ---
  async function api(action, file, extra){
    var body = new URLSearchParams(Object.assign({p:PID, action:action, file:file, csrf:CSRF}, extra||{}));
    var r = await fetch('api.php', {method:'POST', body:body, headers:{'X-CSRF':CSRF}});
    return r.json();
  }
  document.addEventListener('click', function(e){
    var btn = e.target.closest('.ck-shot-bar button'); if(!btn) return;
    var fig = btn.closest('.ck-shot'); if(!fig) return;
    var file = fig.dataset.file, act = btn.dataset.act;
    if(act === 'note'){
      var beat = fig.dataset.beat || '';
      document.getElementById('fbpanel').value = beat;
      var lbl = document.getElementById('fbpanellbl');
      lbl.textContent = '💬 feedback targeted at: ' + beat; lbl.style.display = 'block';
      var ta = document.getElementById('fbtext'); ta.focus();
      window.scrollTo({top:0, behavior:'smooth'});
      return;
    }
    if(act === 'approve'){            // winner: accept + good, siblings demoted -> reload to reflect siblings
      api('winner', file).then(function(j){ if(j && j.ok) location.reload(); });
    } else if(act === 'disapprove'){  // rate bad, in place
      api('rate', file, {rating:'bad'}).then(function(j){ if(j && j.ok){ fig.className='ck-shot rate-bad' + (fig.dataset.accepted==='1'?' kept':''); fig.dataset.rating='bad'; }});
    } else if(act === 'keep'){        // toggle keep, in place
      var next = fig.dataset.accepted==='1' ? '0' : '1';
      api('keep', file, {accepted:next}).then(function(j){ if(j && j.ok){ fig.dataset.accepted=next; fig.classList.toggle('kept', next==='1'); }});
    } else if(act === 'ref'){         // promote this panel into the References set (reloads to show it on the left)
      btn.disabled = true;
      var rb = new URLSearchParams({p:PID, do:'addref', file:file, csrf:CSRF});
      fetch('creator.php?p=' + encodeURIComponent(PID), {method:'POST', body:rb, headers:{'X-CSRF':CSRF}}).then(function(){ location.reload(); });
    } else if(act === 'adjust'){       // refine THIS image: open the adjust modal
      openAdjust(file, fig.dataset.ver || '1');
    }
  });

  // --- lightbox: expand a panel, approve / disapprove / keep / note full-size ---
  var lb = document.getElementById('cklb'), lbimg = document.getElementById('lbimg'),
      lbmeta = document.getElementById('lbmeta'), lbprev = document.getElementById('lbprev'), lbnext = document.getElementById('lbnext');
  var shots = [], lbIdx = -1;
  function ratingWord(fig){ var r = fig.dataset.rating; return (r==='good'?'approved':r==='bad'?'disapproved':'unrated') + (fig.dataset.accepted==='1'?' · kept':''); }
  function openLb(i){
    shots = [].slice.call(document.querySelectorAll('.ck-shot'));
    if(i<0 || i>=shots.length) return; lbIdx = i;
    var fig = shots[i], file = fig.dataset.file, beat = fig.dataset.beat||'';
    lbimg.src = 'img.php?p='+encodeURIComponent(PID)+'&f='+encodeURIComponent(file);   // full-res, not thumb
    lbimg.className = fig.dataset.rating==='good'?'rate-good':fig.dataset.rating==='bad'?'rate-bad':'';
    lbmeta.textContent = (beat?beat+' · ':'') + (i+1)+' / '+shots.length + '  ·  ' + ratingWord(fig);
    lbprev.disabled = i<=0; lbnext.disabled = i>=shots.length-1;
    lb.classList.add('open');
  }
  function closeLb(){ lb.classList.remove('open'); lbIdx = -1; }
  document.addEventListener('click', function(e){
    var img = e.target.closest('.ck-shot img'); if(!img) return;
    var fig = img.closest('.ck-shot');
    openLb([].slice.call(document.querySelectorAll('.ck-shot')).indexOf(fig));
  });
  document.addEventListener('click', function(e){    // expand a reference thumbnail full-size (standalone)
    var rimg = e.target.closest('.ck-refcard img'); if(!rimg) return;
    shots = []; lbIdx = -1;
    lbimg.src = rimg.dataset.full || rimg.src; lbimg.className = '';
    lbmeta.textContent = 'reference'; lbprev.disabled = true; lbnext.disabled = true;
    lb.classList.add('open');
  });
  document.getElementById('lbx').addEventListener('click', closeLb);
  lb.addEventListener('click', function(e){ if(e.target===lb) closeLb(); });
  lbprev.addEventListener('click', function(){ if(lbIdx>0) openLb(lbIdx-1); });
  lbnext.addEventListener('click', function(){ if(lbIdx<shots.length-1) openLb(lbIdx+1); });
  lb.querySelectorAll('.ck-lb-bar button').forEach(function(b){
    b.addEventListener('click', function(){
      if(lbIdx<0) return; var fig = shots[lbIdx], file = fig.dataset.file, act = b.dataset.act;
      if(act==='note'){
        document.getElementById('fbpanel').value = fig.dataset.beat||'';
        var l = document.getElementById('fbpanellbl'); l.textContent = '💬 feedback targeted at: '+(fig.dataset.beat||''); l.style.display='block';
        closeLb(); document.getElementById('fbtext').focus(); window.scrollTo({top:0,behavior:'smooth'}); return;
      }
      if(act==='adjust'){ closeLb(); openAdjust(file, fig.dataset.ver || '1'); return; }
      if(act==='approve'){ api('winner',file).then(function(j){ if(j&&j.ok) location.reload(); }); }
      else if(act==='disapprove'){ api('rate',file,{rating:'bad'}).then(function(j){ if(j&&j.ok){ fig.className='ck-shot rate-bad'+(fig.dataset.accepted==='1'?' kept':''); fig.dataset.rating='bad'; openLb(lbIdx); }}); }
      else if(act==='keep'){ var n=fig.dataset.accepted==='1'?'0':'1'; api('keep',file,{accepted:n}).then(function(j){ if(j&&j.ok){ fig.dataset.accepted=n; fig.classList.toggle('kept',n==='1'); openLb(lbIdx); }}); }
    });
  });
  document.addEventListener('keydown', function(e){
    if(!lb.classList.contains('open')) return;
    if(e.key==='Escape') closeLb();
    else if(e.key==='ArrowLeft' && lbIdx>0) openLb(lbIdx-1);
    else if(e.key==='ArrowRight' && lbIdx<shots.length-1) openLb(lbIdx+1);
    else if(e.key==='a'||e.key==='A'){ lb.querySelector('.b-approve').click(); }
    else if(e.key==='d'||e.key==='D'){ lb.querySelector('.b-disapprove').click(); }
    else if(e.key==='k'||e.key==='K'){ lb.querySelector('.b-keep').click(); }
    else if((e.key==='e'||e.key==='E') && lbIdx>=0){ lb.querySelector('.ck-lb-bar .b-adjust').click(); }
  });

  // --- adjust modal: derive a new version FROM a chosen image (image-to-image) ---
  var adj = document.getElementById('ckadj'), adjImg = document.getElementById('adjimg'),
      adjNote = document.getElementById('adjnote'), adjGo = document.getElementById('adjgo'),
      adjErr = document.getElementById('adjerr'), adjVer = document.getElementById('adjver'), adjFile = null;
  function openAdjust(file, ver){
    adjFile = file;
    adjImg.src = 'img.php?p='+encodeURIComponent(PID)+'&f='+encodeURIComponent(file)+'&t=1';
    adjVer.textContent = '(v'+((parseInt(ver,10)||1)+1)+')';
    adjNote.value = ''; adjErr.style.display='none'; adjGo.disabled=false;
    adj.classList.add('open'); setTimeout(function(){ adjNote.focus(); }, 30);
  }
  function closeAdjust(){ adj.classList.remove('open'); adjFile=null; }
  document.getElementById('adjcancel').addEventListener('click', closeAdjust);
  adj.addEventListener('click', function(e){ if(e.target===adj) closeAdjust(); });
  document.addEventListener('keydown', function(e){ if(adj.classList.contains('open') && e.key==='Escape') closeAdjust(); });
  adjGo.addEventListener('click', function(){
    var note = adjNote.value.trim();
    if(!note){ adjErr.textContent='Write the one change you want.'; adjErr.style.display='block'; adjNote.focus(); return; }
    if(!adjFile) return;
    adjGo.disabled=true; adjErr.style.display='none';
    fetch('creator.php?p='+encodeURIComponent(PID), {method:'POST', headers:{'X-CSRF':CSRF},
        body:new URLSearchParams({p:PID, do:'adjust', file:adjFile, note:note, csrf:CSRF})})
      .then(function(r){ return r.json(); })
      .then(function(j){ if(j&&j.ok){ closeAdjust(); location.reload(); }
                         else { adjErr.textContent=(j&&j.err)||'Could not start the adjustment.'; adjErr.style.display='block'; adjGo.disabled=false; } })
      .catch(function(){ adjErr.textContent='Request failed — try again.'; adjErr.style.display='block'; adjGo.disabled=false; });
  });
  adjNote.addEventListener('keydown', function(e){ if((e.metaKey||e.ctrlKey) && e.key==='Enter') adjGo.click(); });

  // --- pending refinement cards: copy the edit prompt + filename feedback on the drop slot ---
  document.addEventListener('click', function(e){
    var cb = e.target.closest('.b-copyprompt'); if(!cb) return;
    var txt = cb.dataset.prompt || '';
    function done(){ var o=cb.textContent; cb.textContent='✓ Copied'; setTimeout(function(){ cb.textContent=o; }, 1400); }
    if(navigator.clipboard && navigator.clipboard.writeText){ navigator.clipboard.writeText(txt).then(done, function(){ window.prompt('Copy the edit prompt:', txt); }); }
    else { window.prompt('Copy the edit prompt:', txt); }
  });
  document.addEventListener('change', function(e){
    var inp = e.target.closest('.ck-pdrop input[type=file]'); if(!inp) return;
    var drop = inp.closest('.ck-pdrop'), span = drop.querySelector('span');
    if(inp.files && inp.files[0]){ drop.classList.add('has'); span.textContent='✓ '+inp.files[0].name; }
    else { drop.classList.remove('has'); span.textContent='⬆ Drop / choose the new version'; }
  });

  // --- live poll: reload when the gallery / run state changes ---
  var lastSig = null, pending = false;
  var banner = document.getElementById('newbanner');
  banner.addEventListener('click', function(){ location.reload(); });
  function typing(){ var a = document.activeElement; return a && (a.id==='fbtext'); }
  async function poll(){
    try{
      var r = await fetch('creator.php?p=' + encodeURIComponent(PID) + '&poll=1', {cache:'no-store'});
      var j = await r.json(); if(!j || !j.ok) return;
      var pill = document.getElementById('statepill');
      if(pill && pill.textContent.trim() !== j.state){
        var col = {idle:'#6F7380',queued:'#EF9F27',open:'#EF9F27',claimed:'#EF9F27',running:'#1D9E75',stopping:'#E24B4A',stopped:'#E24B4A',blocked:'#E24B4A',needs_login:'#E24B4A',error:'#E24B4A',done:'#378ADD'}[j.state] || '#6F7380';
        pill.style.background = col; pill.innerHTML = '<span class="dot"></span>' + j.state;
      }
      var pg = document.getElementById('progline'); if(pg){ pg.textContent = j.progress || ''; pg.style.display = j.progress ? '' : 'none'; }
      var sn = document.getElementById('stopnote'); if(sn) sn.style.display = j.stopRequested ? '' : 'none';
      var wn = document.getElementById('waitnote'); if(wn) wn.style.display = j.waiting ? '' : 'none';
      if(lastSig === null){ lastSig = j.sig; return; }
      if(j.sig !== lastSig){
        lastSig = j.sig;
        if(typing() || notesOpen()){ pending = true; banner.style.display = 'block'; }
        else location.reload();
      }
    }catch(e){}
  }
  // visible countdown so the user can see it's alive (not frozen/broken)
  var REFRESH = 4, crEl = document.getElementById('ckrefresh'), left = REFRESH, busy = false;
  async function cycle(){ busy = true; if(crEl) crEl.textContent = '↻ checking…'; try{ await poll(); } finally { busy = false; left = REFRESH; if(crEl) crEl.textContent = '↻ ' + left + 's'; } }
  setInterval(function(){ if(busy) return; left--; if(left <= 0){ cycle(); } else if(crEl){ crEl.textContent = '↻ ' + left + 's'; } }, 1000);
  cycle();

  // refs/scenes gate: block page/panel/all generation until references are locked
  var REFS_LOCKED = <?= !empty($c['refsLocked'])?'true':'false' ?>;
  (function(){ var sc=document.getElementById('scope'), qb=document.getElementById('queuebtn'), gh=document.getElementById('gatehint');
    function g(){ if(!sc||!qb) return; var s=sc.value, blk=(s==='page'||s==='panel'||s==='all') && !REFS_LOCKED; qb.disabled=blk; if(gh) gh.style.display=blk?'inline':'none'; }
    if(sc){ sc.addEventListener('change', g); g(); } })();
  if(REFS_LOCKED){ document.querySelectorAll('.ck-shot-bar .b-ref').forEach(function(b){ b.disabled=true; b.title='References locked — unlock to add more'; }); }

  // script -> shotlist breakdown (AI), with a working overlay (one call, can take ~a minute)
  var bdbtn=document.getElementById('bdbtn'), bdov=document.getElementById('bdov'), bdmsg=document.getElementById('bdmsg');
  if(bdbtn) bdbtn.addEventListener('click', function(){
    if(bdov) bdov.style.display='flex'; bdbtn.disabled=true;
    fetch('creator.php?p='+encodeURIComponent(PID), {method:'POST', headers:{'X-CSRF':CSRF}, body:new URLSearchParams({p:PID,do:'breakdown',csrf:CSRF})})
      .then(function(r){ return r.json(); })
      .then(function(j){ if(j&&j.ok){ if(bdmsg) bdmsg.textContent='Done — '+j.pages+' pages / '+j.panels+' panels. Loading…'; location.reload(); }
                         else { if(bdmsg) bdmsg.textContent=(j&&j.err)||'Breakdown failed.'; setTimeout(function(){ if(bdov) bdov.style.display='none'; bdbtn.disabled=false; },3000); } })
      .catch(function(){ if(bdmsg) bdmsg.textContent='Request failed — try again.'; setTimeout(function(){ if(bdov) bdov.style.display='none'; bdbtn.disabled=false; },3000); });
  });

  // --- notes log: filter (all / panel / system) + copy-all export; collapsed by default ---
  function notesOpen(){ var n = document.getElementById('notes'); return !!(n && n.open); }
  (function(){
    var list = document.getElementById('noteslist'); if(!list) return;
    var fbtns = [].slice.call(document.querySelectorAll('.ck-notes-filter button'));
    var empty = document.getElementById('notesempty');
    function applyFilter(f){
      var any = false;
      list.querySelectorAll('.ck-note').forEach(function(n){
        var show = (f === 'all') || (n.dataset.type === f);
        n.style.display = show ? '' : 'none'; if(show) any = true;
      });
      if(empty) empty.style.display = any ? 'none' : '';
    }
    fbtns.forEach(function(b){ b.addEventListener('click', function(){
      fbtns.forEach(function(x){ x.classList.remove('on'); }); b.classList.add('on');
      applyFilter(b.dataset.f);
    }); });
    var copyBtn = document.getElementById('notescopy');
    if(copyBtn) copyBtn.addEventListener('click', function(){
      var out = [].slice.call(list.querySelectorAll('.ck-note')).map(function(n){
        function t(sel){ var el = n.querySelector(sel); return el ? el.textContent.trim() : ''; }
        var head = [t('.ck-note-badge'), t('.ck-note-when'), t('.ck-note-by')].filter(Boolean).join(' · ');
        return '[' + head + ']\n' + t('.ck-note-txt');
      }).join('\n\n');
      function done(){ var o = copyBtn.textContent; copyBtn.textContent = '✓ Copied'; setTimeout(function(){ copyBtn.textContent = o; }, 1400); }
      if(navigator.clipboard && navigator.clipboard.writeText){ navigator.clipboard.writeText(out).then(done, function(){ window.prompt('Copy all notes:', out); }); }
      else window.prompt('Copy all notes:', out);
    });
  })();
})();
</script>
</body></html>

