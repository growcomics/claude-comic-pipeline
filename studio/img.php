<?php
// Serves a project image (or its thumbnail with t=1) to signed-in users only.
// Files live under studio/uploads/<id>/ which is web-blocked by .htaccess.
declare(strict_types=1);
require_once __DIR__ . '/inc/boot.php';
require_auth();

$id = preg_replace('/[^a-z0-9-]/','',(string)($_GET['p'] ?? ''));
$f  = basename((string)($_GET['f'] ?? ''));
if ($id === '' || $f === '' || !preg_match('/^[A-Za-z0-9._-]+$/', $f)) { http_response_code(404); exit; }
$path = project_dir($id) . (empty($_GET['t']) ? '' : '/thumb') . '/' . $f;
if (!is_file($path)) { // thumb may be missing -> fall back to full
    $path = project_dir($id) . '/' . $f;
    if (!is_file($path)) { http_response_code(404); exit; }
}
$types = ['jpg'=>'image/jpeg','jpeg'=>'image/jpeg','png'=>'image/png','webp'=>'image/webp','gif'=>'image/gif'];
header('Content-Type: ' . ($types[ext_of($f)] ?? 'application/octet-stream'));
header('Cache-Control: private, max-age=600');
header('X-Robots-Tag: noindex');
header('Content-Length: ' . filesize($path));
readfile($path);
