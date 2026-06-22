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
if (!$id || !project_get($id)) bout(['ok'=>false,'error'=>'unknown project']);

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
bout(['ok'=>false,'error'=>'unknown action']);
