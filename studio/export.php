<?php
// Download ALL of a project's images, full-res, in beat/page order, as a zip.
// The project's current contents = your curated set after triage + purge.
declare(strict_types=1);
require_once __DIR__ . '/inc/boot.php';
require_auth();

$id = preg_replace('/[^a-z0-9-]/', '', (string)($_GET['p'] ?? ''));
$proj = project_get($id);
if (!$proj) { http_response_code(404); exit('Unknown project.'); }

function _bnum(string $s): int { return preg_match('/(\d+)/', $s, $m) ? (int)$m[1] : 9999; }

$imgs = images_all($id);
usort($imgs, fn($a, $b) => _bnum($a['group'] ?? '') <=> _bnum($b['group'] ?? '') ?: (($a['ts'] ?? 0) <=> ($b['ts'] ?? 0)));
if (!$imgs) { http_response_code(404); exit('No images in this project yet.'); }

if (!class_exists('ZipArchive')) { http_response_code(500); exit('Zip support unavailable on this host.'); }
$zip = new ZipArchive();
$tmp = tempnam(sys_get_temp_dir(), 'studiozip');
$zip->open($tmp, ZipArchive::CREATE | ZipArchive::OVERWRITE);
$i = 1;
foreach ($imgs as $x) {
    $path = project_dir($id) . '/' . $x['file'];
    if (!is_file($path)) continue;
    $ext = ext_of($x['file']) ?: 'png';
    $zip->addFile($path, sprintf('page-%02d.%s', $i++, $ext));
}
// a small manifest mapping pages -> beat + original gen filename
$man = "page\tbeat\toriginal\n"; $i = 1;
foreach ($imgs as $x) { $man .= sprintf("page-%02d\t%s\t%s\n", $i++, $x['group'] ?? '', $x['orig'] ?? ''); }
$zip->addFromString('manifest.txt', $man);
$zip->close();

$fn = preg_replace('/[^A-Za-z0-9._-]/', '-', $id) . '-all.zip';
header('Content-Type: application/zip');
header('Content-Disposition: attachment; filename="' . $fn . '"');
header('Content-Length: ' . filesize($tmp));
header('X-Robots-Tag: noindex');
readfile($tmp);
@unlink($tmp);
