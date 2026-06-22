<?php
declare(strict_types=1);
require_once __DIR__ . '/inc/boot.php';
s_boot();
header('Content-Type: application/json');
function jout($a){ echo json_encode($a); exit; }

if (!is_authed()) jout(['ok'=>false,'error'=>'Not signed in.']);
if (!csrf_ok())   jout(['ok'=>false,'error'=>'Bad token — reload.']);

$id = preg_replace('/[^a-z0-9-]/','',(string)($_POST['p'] ?? ''));
if (!project_get($id)) jout(['ok'=>false,'error'=>'Unknown project.']);
$action = $_POST['action'] ?? '';

function touch_project(string $id): void {
    $all = projects_all();
    foreach ($all as &$p) if (($p['id']??'')===$id) $p['updated']=date('c');
    unset($p); projects_save($all);
}
function beat_num(string $s): int { return preg_match('/(\d+)/',$s,$m) ? (int)$m[1] : 9999; }
function ordered_beats(array $meta): array {
    $b = [];
    foreach ($meta as $m) { $g = $m['group'] ?? ''; if ($g!=='' && !in_array($g,$b,true)) $b[]=$g; }
    usort($b, fn($x,$y)=> beat_num($x) <=> beat_num($y) ?: strcmp($x,$y));
    return $b;
}

if ($action === 'upload') {
    $files = $_FILES['files'] ?? null;
    if (!$files || empty($files['name'])) jout(['ok'=>false,'error'=>'No files.']);
    $meta = images_all($id); $added = [];
    $names = (array)$files['name'];
    for ($i=0; $i<count($names); $i++) {
        if ((int)($files['error'][$i] ?? 4) !== UPLOAD_ERR_OK) continue;
        if (!is_uploaded_file($files['tmp_name'][$i])) continue;
        if ((int)($files['size'][$i] ?? 0) > MAX_BYTES) continue;
        $res = store_image($files['tmp_name'][$i], (string)$files['name'][$i], $id);
        if (!$res) continue;
        $entry = ['file'=>$res['file'],'orig'=>mb_substr((string)$files['name'][$i],0,120),
                  'rating'=>'unrated','accepted'=>false,'group'=>'','tags'=>[],'ts'=>time()];
        $meta[] = $entry; $added[] = $entry;
    }
    images_save($id, $meta); touch_project($id);
    jout(['ok'=>true,'added'=>$added,'count'=>count($meta)]);
}

// reorder a beat to a 1-based position; renumbers all beats to "Beat 1..N" in the new order
if ($action === 'move_beat') {
    $beat = trim((string)($_POST['beat'] ?? ''));
    $to   = (int)($_POST['to'] ?? 0);
    $meta = images_all($id);
    $beats = ordered_beats($meta);
    $from = array_search($beat, $beats, true);
    if ($from === false || !$beats) jout(['ok'=>false,'error'=>'no such beat']);
    $to = max(1, min(count($beats), $to)) - 1;
    array_splice($beats, $from, 1);
    array_splice($beats, $to, 0, [$beat]);
    $map = []; foreach ($beats as $i=>$b) $map[$b] = 'Beat ' . ($i+1);
    foreach ($meta as &$m) { $g = $m['group'] ?? ''; if (isset($map[$g])) $m['group'] = $map[$g]; }
    unset($m);
    images_save($id, $meta); touch_project($id);
    jout(['ok'=>true]);
}

// sequence mode: each image becomes its own beat (page), in current order, all kept
if ($action === 'one_beat_each') {
    $meta = images_all($id);
    usort($meta, fn($a,$b)=> beat_num($a['group']??'') <=> beat_num($b['group']??'') ?: (($a['ts']??0) <=> ($b['ts']??0)));
    foreach ($meta as $i=>&$m) { $m['group'] = 'Beat ' . ($i+1); $m['accepted'] = true; $m['rating'] = 'good'; }
    unset($m);
    images_save($id, $meta); touch_project($id);
    jout(['ok'=>true]);
}

// per-image mutations
$file = basename((string)($_POST['file'] ?? ''));
$meta = images_all($id);
$idx = null; foreach ($meta as $k=>$m) if (($m['file']??'')===$file) { $idx=$k; break; }
if ($idx === null) jout(['ok'=>false,'error'=>'Image not found.']);

// mark current image the winner of its beat: it becomes accepted+good, siblings lose accept + any 'good'
if ($action === 'winner') {
    $beat = $meta[$idx]['group'] ?? '';
    foreach ($meta as &$m) {
        if ($beat !== '' && ($m['group'] ?? '') === $beat) {
            $win = ($m['file'] === $file);
            $m['accepted'] = $win;
            if ($win) $m['rating'] = 'good';
            elseif (($m['rating'] ?? '') === 'good') $m['rating'] = 'unrated';
        }
    }
    unset($m); images_save($id, $meta);
    $all = projects_all(); foreach ($all as &$p) if (($p['id']??'')===$id && empty($p['cover'])) $p['cover']=$file; unset($p); projects_save($all);
    jout(['ok'=>true]);
}
if ($action === 'rate') {
    $r = in_array($_POST['rating']??'', RATINGS, true) ? $_POST['rating'] : 'unrated';
    $meta[$idx]['rating'] = $r; images_save($id,$meta); jout(['ok'=>true,'rating'=>$r]);
}
if ($action === 'keep') {
    $meta[$idx]['accepted'] = !empty($_POST['accepted']) && $_POST['accepted'] !== '0';
    images_save($id,$meta); jout(['ok'=>true,'accepted'=>$meta[$idx]['accepted']]);
}
if ($action === 'group') {
    $meta[$idx]['group'] = mb_substr(trim((string)($_POST['group'] ?? '')),0,60);
    images_save($id,$meta); jout(['ok'=>true]);
}
if ($action === 'cover') {
    $all = projects_all();
    foreach ($all as &$p) if (($p['id']??'')===$id) $p['cover']=$file;
    unset($p); projects_save($all); jout(['ok'=>true]);
}
if ($action === 'delete') {
    @unlink(project_dir($id) . '/' . $file);
    @unlink(project_dir($id) . '/thumb/' . $file);
    array_splice($meta, $idx, 1); images_save($id,$meta);
    $all = projects_all(); foreach ($all as &$p) if (($p['id']??'')===$id && ($p['cover']??'')===$file) $p['cover']=null;
    unset($p); projects_save($all);
    jout(['ok'=>true,'count'=>count($meta)]);
}
jout(['ok'=>false,'error'=>'Unknown action.']);
