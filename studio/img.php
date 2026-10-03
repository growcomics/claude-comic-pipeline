<?php
// Serves a project image (or its thumbnail with t=1) to signed-in users only.
// Files live under studio/uploads/<id>/ which is web-blocked by .htaccess.
declare(strict_types=1);
require_once __DIR__ . '/inc/boot.php';
require_auth();

$id = preg_replace('/[^a-z0-9-]/','',(string)($_GET['p'] ?? ''));
$f  = basename((string)($_GET['f'] ?? ''));
if ($id === '' || $f === '' || !preg_match('/^[A-Za-z0-9._-]+$/', $f)) { http_response_code(404); exit; }
// m=1: a viewing copy (≤1200 px wide JPEG q85), made once on first request and cached in uploads/<id>/mid/.
// The picker lightbox uses it so stepping through takes doesn't wait on 1-2 MB PNGs. Falls back to the full file.
if (!empty($_GET['m']) && empty($_GET['t'])) {
    $full = project_dir($id) . '/' . $f;
    $mid  = project_dir($id) . '/mid/' . pathinfo($f, PATHINFO_FILENAME) . '.jpg';
    if (is_file($full) && !is_file($mid) && extension_loaded('gd') && filesize($full) > 350000) {
        $e = ext_of($f);
        $im = @($e === 'png' ? imagecreatefrompng($full) : ($e === 'webp' && function_exists('imagecreatefromwebp') ? imagecreatefromwebp($full) : ($e === 'gif' ? imagecreatefromgif($full) : imagecreatefromjpeg($full))));
        if ($im) {
            $w = imagesx($im); $h = imagesy($im); $nw = min($w, 1200); $nh = (int)round($h * $nw / max(1, $w));
            $d = imagecreatetruecolor($nw, $nh);
            imagefill($d, 0, 0, imagecolorallocate($d, 255, 255, 255));   // flatten any alpha onto white
            imagecopyresampled($d, $im, 0, 0, 0, 0, $nw, $nh, $w, $h);
            @mkdir(dirname($mid), 0755, true);
            $tmp = $mid . '.tmp' . getmypid();
            if (@imagejpeg($d, $tmp, 85)) @rename($tmp, $mid); else @unlink($tmp);
            imagedestroy($d); imagedestroy($im);
        }
    }
    if (is_file($mid)) {
        header('Content-Type: image/jpeg');
        header('Cache-Control: private, max-age=2592000, immutable');
        header('X-Robots-Tag: noindex');
        header('Content-Length: ' . filesize($mid));
        readfile($mid); exit;
    }
    // small originals (≤350 KB) or no GD: just serve the full file below
}
// t=1 on a PNG: the stored PNG thumbnail of a big take is ~300 KB; serve a cached 360px JPEG (mid/<name>.t.jpg, ~25 KB)
// so a page grid of 12 takes doesn't pull ~4 MB.
if (!empty($_GET['t']) && ext_of($f) === 'png') {
    $tp = project_dir($id) . '/thumb/' . $f;
    $tj = project_dir($id) . '/mid/' . pathinfo($f, PATHINFO_FILENAME) . '.t.jpg';
    if (is_file($tp) && !is_file($tj) && extension_loaded('gd') && filesize($tp) > 120000 && ($im = @imagecreatefrompng($tp))) {
        $d = imagecreatetruecolor(imagesx($im), imagesy($im));
        imagefill($d, 0, 0, imagecolorallocate($d, 255, 255, 255));
        imagecopy($d, $im, 0, 0, 0, 0, imagesx($im), imagesy($im));
        @mkdir(dirname($tj), 0755, true);
        $tmp = $tj . '.tmp' . getmypid();
        if (@imagejpeg($d, $tmp, 82)) @rename($tmp, $tj); else @unlink($tmp);
        imagedestroy($d); imagedestroy($im);
    }
    if (is_file($tj)) {
        header('Content-Type: image/jpeg');
        header('Cache-Control: private, max-age=2592000, immutable');
        header('X-Robots-Tag: noindex');
        header('Content-Length: ' . filesize($tj));
        readfile($tj); exit;
    }
}
$path = project_dir($id) . (empty($_GET['t']) ? '' : '/thumb') . '/' . $f;
if (!is_file($path)) { // thumb may be missing -> fall back to full
    $path = project_dir($id) . '/' . $f;
    if (!is_file($path)) { http_response_code(404); exit; }
}
$types = ['jpg'=>'image/jpeg','jpeg'=>'image/jpeg','png'=>'image/png','webp'=>'image/webp','gif'=>'image/gif'];
header('Content-Type: ' . ($types[ext_of($f)] ?? 'application/octet-stream'));
header('Cache-Control: private, max-age=2592000, immutable');   // stored names are random and never rewritten
header('X-Robots-Tag: noindex');
header('Content-Length: ' . filesize($path));
readfile($path);
