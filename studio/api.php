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

// per-image mutations
$file = basename((string)($_POST['file'] ?? ''));
$meta = images_all($id);
$idx = null; foreach ($meta as $k=>$m) if (($m['file']??'')===$file) { $idx=$k; break; }
if ($action !== 'upload' && $idx === null) jout(['ok'=>false,'error'=>'Image not found.']);

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
