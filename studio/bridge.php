<?php
// Studio bridge — lets a Claude Code session (the "AI organizer", like
// comic-folder-organizer) pull a project's draft images and write ratings /
// grouping / cover back. KEY-GATED (shared secret in data/bridge.json) so it
// works without a browser login. The key is rotatable by editing bridge.json.
//   GET  bridge.php?key=..&do=projects
//   GET  bridge.php?key=..&do=images&p=<id>
//   GET  bridge.php?key=..&do=img&p=<id>&f=<file>[&t=1]      -> {b64}
//   POST bridge.php  key,do=write,p,decisions=<json>[,cover] -> writes ratings
declare(strict_types=1);
require_once __DIR__ . '/inc/boot.php';
header('Content-Type: application/json');
header('X-Robots-Tag: noindex');
function bout($a){ echo json_encode($a); exit; }

define('BRIDGE_FILE', SDATA . '/bridge.json');
$cfg = s_read(BRIDGE_FILE, []);
$key = (string)($cfg['key'] ?? '');
$given = (string)($_POST['key'] ?? $_GET['key'] ?? ($_SERVER['HTTP_X_BRIDGE_KEY'] ?? ''));
if ($key === '' || strlen($given) < 16 || !hash_equals($key, $given)) { http_response_code(403); bout(['ok'=>false,'error'=>'bad key']); }

$do = $_POST['do'] ?? $_GET['do'] ?? '';
if ($do === 'projects') bout(['ok'=>true,'projects'=>projects_all()]);

$id = preg_replace('/[^a-z0-9-]/','',(string)($_POST['p'] ?? $_GET['p'] ?? ''));
if ($do !== 'ingest_init' && $do !== 'ingest' && (!$id || !project_get($id))) bout(['ok'=>false,'error'=>'unknown project']);

if ($do === 'images') bout(['ok'=>true,'project'=>project_get($id),'images'=>images_all($id)]);

if ($do === 'img') {
    $f = basename((string)($_GET['f'] ?? $_POST['f'] ?? ''));
    $p = project_dir($id) . (empty($_GET['t']) && empty($_POST['t']) ? '' : '/thumb') . '/' . $f;
    if (!is_file($p)) $p = project_dir($id) . '/' . $f;
    if (!is_file($p)) bout(['ok'=>false,'error'=>'no file']);
    bout(['ok'=>true,'file'=>$f,'b64'=>base64_encode((string)file_get_contents($p))]);
}

if ($do === 'write') {
    $decs = json_decode((string)($_POST['decisions'] ?? '[]'), true) ?: [];
    $meta = images_all($id);
    $byfile = []; foreach ($meta as $k=>$m) $byfile[$m['file']] = $k;
    $n = 0;
    foreach ($decs as $d) {
        $f = $d['file'] ?? ''; if (!isset($byfile[$f])) continue;
        $k = $byfile[$f];
        if (isset($d['rating']) && in_array($d['rating'], RATINGS, true)) $meta[$k]['rating'] = $d['rating'];
        if (array_key_exists('accepted', $d)) $meta[$k]['accepted'] = (bool)$d['accepted'];
        if (isset($d['group'])) $meta[$k]['group'] = mb_substr((string)$d['group'], 0, 60);
        $n++;
    }
    images_save($id, $meta);
    $cover = basename((string)($_POST['cover'] ?? ''));
    if ($cover !== '') { $all = projects_all(); foreach ($all as &$pp) if (($pp['id']??'')===$id) $pp['cover'] = $cover; unset($pp); projects_save($all); }
    bout(['ok'=>true,'updated'=>$n]);
}
// ---- ingest (used by the Flow → Studio extension) ----
// resolve or create a project by name, return its id
if ($do === 'ingest_init') {
    $name = trim((string)($_POST['project'] ?? $_GET['project'] ?? ''));
    if ($name === '') bout(['ok'=>false,'error'=>'no project name']);
    // new=1 → always create a FRESH section (each Flow→Studio batch gets its own
    // project). Otherwise resolve an existing project by id/name = "append to".
    $forceNew = !empty($_POST['new']) || !empty($_GET['new']);
    $all = projects_all(); $pid = '';
    if (!$forceNew) {
        foreach ($all as $p) if (($p['id']??'')===$name || strcasecmp((string)($p['name']??''),$name)===0) { $pid=$p['id']; break; }
    }
    if ($pid === '') {
        $disp = mb_substr($name, 0, 80);
        if ($forceNew) {                                    // timestamp the section so it's unique + self-documenting
            $disp .= ' · ' . date('M j, H:i');
            $lc = array_map(fn($p)=>strtolower((string)($p['name']??'')), $all);
            if (in_array(strtolower($disp), $lc, true)) { $k=2; while (in_array(strtolower($disp.' #'.$k), $lc, true)) $k++; $disp .= ' #'.$k; }
        }
        $base = slugify($name); $pid=$base; $k=2; $taken=array_column($all,'id');
        while (in_array($pid,$taken,true)) $pid=$base.'-'.$k++;
        array_unshift($all, ['id'=>$pid,'name'=>$disp,'status'=>'active','stage'=>'page-build',
            'tags'=>[],'notes'=>'','cover'=>null,'created'=>date('c'),'updated'=>date('c')]);
        projects_save($all);
    }
    bout(['ok'=>true,'project'=>$pid]);
}
// store one uploaded image into a project (multipart field 'file')
if ($do === 'ingest') {
    $pid = preg_replace('/[^a-z0-9-]/','',(string)($_POST['p'] ?? ''));
    if ($pid==='' || !project_get($pid)) bout(['ok'=>false,'error'=>'unknown project']);
    $f = $_FILES['file'] ?? null;
    if (!$f || ($f['error'] ?? 1) !== UPLOAD_ERR_OK || !is_uploaded_file($f['tmp_name'])) bout(['ok'=>false,'error'=>'no file']);
    if (($f['size'] ?? 0) > MAX_BYTES) bout(['ok'=>false,'error'=>'too big']);
    $orig = (string)($_POST['orig'] ?? $f['name'] ?? 'flow.png');
    $res = store_image($f['tmp_name'], $orig, $pid);
    if (!$res) bout(['ok'=>false,'error'=>'store failed (unsupported image?)']);
    $meta = images_all($pid);
    $seq = (int)($_POST['seq'] ?? count($meta));
    $meta[] = ['file'=>$res['file'],'orig'=>mb_substr($orig,0,120),'rating'=>'unrated','accepted'=>false,'group'=>'','tags'=>[],'ts'=>time()+$seq];
    images_save($pid, $meta);
    bout(['ok'=>true,'count'=>count($meta)]);
}

// ---- annotate (AI analysis pass): per-image caption / defects / tier / notes / tags ----
if ($do === 'annotate') {
    $notes = json_decode((string)($_POST['notes'] ?? '[]'), true) ?: [];
    $meta = images_all($id);
    $byfile = []; foreach ($meta as $k=>$m) $byfile[$m['file']] = $k;
    $n = 0;
    foreach ($notes as $note) {
        $f = $note['file'] ?? ''; if (!isset($byfile[$f])) continue;
        $k = $byfile[$f];
        $meta[$k]['analysis'] = [
            'caption' => mb_substr((string)($note['caption'] ?? ''), 0, 300),
            'defects' => array_values(array_slice(array_map(fn($d)=>mb_substr((string)$d,0,60), (array)($note['defects'] ?? [])), 0, 12)),
            'tier'    => mb_substr((string)($note['tier'] ?? ''), 0, 60),
            'notes'   => mb_substr((string)($note['notes'] ?? ''), 0, 800),
            'at'      => date('c'),
        ];
        if (isset($note['tags'])) $meta[$k]['tags'] = array_values(array_slice(array_map(fn($t)=>mb_substr((string)$t,0,40), (array)$note['tags']), 0, 12));
        $n++;
    }
    images_save($id, $meta);
    bout(['ok'=>true,'annotated'=>$n]);
}

bout(['ok'=>false,'error'=>'unknown action']);
