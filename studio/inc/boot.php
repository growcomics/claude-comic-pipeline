<?php
// Studio — shared bootstrap: config, session/auth, CSRF, JSON store, images.
// Self-contained internal tool. Lives at <docroot>/studio/.
declare(strict_types=1);
date_default_timezone_set('UTC');

define('STUDIO_ROOT', dirname(__DIR__));
define('SDATA', STUDIO_ROOT . '/data');
define('SUPLOADS', STUDIO_ROOT . '/uploads');
define('ADMIN_USERS_FILE', dirname(STUDIO_ROOT) . '/admin/data/users.json'); // share the 3dmusclecomics admin/team logins
define('PROJECTS_FILE', SDATA . '/projects.json');

define('STAGES', ['ideator','writer','storyboard','reference','page-build','review','publish']);
define('STATUSES', ['active','on-hold','done','archived']);
define('RATINGS', ['unrated','good','bad']);
define('IMG_EXT', ['jpg','jpeg','png','webp','gif']);
define('IMG_MAX_W', 1600);   // downscale stored copy
define('THUMB_W', 360);
define('MAX_BYTES', 30 * 1024 * 1024);

function s_boot(): void {
    if (session_status() === PHP_SESSION_NONE) {
        $dir = rtrim(dirname($_SERVER['SCRIPT_NAME'] ?? '/studio'), '/') ?: '/studio';
        session_name('mgstudio');
        session_set_cookie_params(['lifetime'=>0,'path'=>$dir,'httponly'=>true,'samesite'=>'Lax',
            'secure'=>(!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS']!=='off')]);
        session_start();
    }
}

// ---- JSON store (atomic) ---------------------------------------------------
function s_read(string $f, $def = []) {
    if (!is_file($f)) return $def;
    $raw = file_get_contents($f);
    if ($raw === false || $raw === '') return $def;
    $d = json_decode($raw, true);
    return $d === null ? $def : $d;
}
function s_write(string $f, $data): bool {
    if (!is_dir(dirname($f))) @mkdir(dirname($f), 0755, true);
    $json = json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE);
    $tmp = $f . '.tmp' . getmypid();
    if (file_put_contents($tmp, $json, LOCK_EX) === false) return false;
    return rename($tmp, $f);
}

// ---- auth: shares the 3dmusclecomics admin/team logins (admin/data/users.json).
// Studio keeps its own session; you sign in with the SAME username + password as
// the 3dmusclecomics admin. Any admin/contributor account works.
function studio_users(): array { return s_read(ADMIN_USERS_FILE, []); }
function studio_login(string $username, string $password): bool {
    $username = strtolower(trim($username));
    foreach (studio_users() as $u) {
        if (strtolower($u['username'] ?? '') === $username && !empty($u['hash']) && password_verify($password, $u['hash'])) {
            s_boot(); session_regenerate_id(true);
            $_SESSION['studio_ok'] = true;
            $_SESSION['studio_user'] = $u['name'] ?? $u['username'];
            return true;
        }
    }
    return false;
}
function is_authed(): bool { s_boot(); return !empty($_SESSION['studio_ok']); }
function current_studio_user(): string { s_boot(); return (string)($_SESSION['studio_user'] ?? ''); }
function sign_out(): void { s_boot(); $_SESSION = []; if (ini_get('session.use_cookies')) { $p = session_get_cookie_params(); setcookie(session_name(),'',time()-42000,$p['path'],$p['domain']??'',$p['secure'],$p['httponly']); } session_destroy(); }
function require_auth(): void { s_boot(); if (!is_authed()) { header('Location: login.php'); exit; } }

// ---- CSRF ------------------------------------------------------------------
function csrf(): string { s_boot(); if (empty($_SESSION['csrf'])) $_SESSION['csrf'] = bin2hex(random_bytes(16)); return $_SESSION['csrf']; }
function csrf_field(): string { return '<input type="hidden" name="csrf" value="' . csrf() . '">'; }
function csrf_ok(): bool { $t = $_POST['csrf'] ?? ($_SERVER['HTTP_X_CSRF'] ?? ''); s_boot(); return is_string($t) && !empty($_SESSION['csrf']) && hash_equals($_SESSION['csrf'], $t); }
function csrf_check(): void { if (!csrf_ok()) { http_response_code(403); exit('Bad CSRF token — reload and retry.'); } }

// ---- helpers ---------------------------------------------------------------
function h($s): string { return htmlspecialchars((string)$s, ENT_QUOTES, 'UTF-8'); }
function slugify(string $s): string { $s = strtolower(trim($s)); $s = preg_replace('/[^a-z0-9]+/','-',$s); $s = trim($s,'-'); if ($s===''||!preg_match('/^[a-z]/',$s)) $s='p-'.$s; return substr($s,0,48); }
function nid(): string { return substr(bin2hex(random_bytes(6)),0,10); }
function ext_of(string $f): string { $e = strtolower(pathinfo($f, PATHINFO_EXTENSION)); return $e==='jpeg'?'jpg':$e; }

// ---- projects --------------------------------------------------------------
function projects_all(): array { return s_read(PROJECTS_FILE, []); }
function projects_save(array $p): bool { return s_write(PROJECTS_FILE, $p); }
function project_get(string $id): ?array { foreach (projects_all() as $p) if (($p['id']??'')===$id) return $p; return null; }

// ---- per-project image metadata + files ------------------------------------
function imeta_path(string $id): string { return SDATA . '/images-' . preg_replace('/[^a-z0-9-]/','',$id) . '.json'; }
function images_all(string $id): array { return s_read(imeta_path($id), []); }
function images_save(string $id, array $a): bool { return s_write(imeta_path($id), $a); }
function project_dir(string $id): string { return SUPLOADS . '/' . preg_replace('/[^a-z0-9-]/','',$id); }

// Downscale + thumbnail an uploaded image. Returns [file, thumb] or null.
function store_image(string $tmp, string $orig, string $id): ?array {
    $ext = ext_of($orig);
    if (!in_array($ext, IMG_EXT, true)) return null;
    $dir = project_dir($id); @mkdir($dir . '/thumb', 0755, true);
    $name = nid() . '.' . $ext;
    $dest = $dir . '/' . $name; $thumb = $dir . '/thumb/' . $name;
    if (!extension_loaded('gd')) { if (!move_uploaded_file($tmp, $dest)) return null; @copy($dest,$thumb); return ['file'=>$name]; }
    $im = @($ext==='png'?imagecreatefrompng($tmp):($ext==='webp'&&function_exists('imagecreatefromwebp')?imagecreatefromwebp($tmp):($ext==='gif'?imagecreatefromgif($tmp):imagecreatefromjpeg($tmp))));
    if (!$im) { if (!move_uploaded_file($tmp,$dest)) return null; @copy($dest,$thumb); return ['file'=>$name]; }
    _img_out(_img_fit($im, IMG_MAX_W), $dest, $ext);
    _img_out(_img_fit($im, THUMB_W), $thumb, $ext);
    imagedestroy($im);
    return ['file'=>$name];
}
function _img_fit($im, int $maxW) {
    $w=imagesx($im); $h=imagesy($im); if ($w<=$maxW) return $im;
    $nw=$maxW; $nh=(int)round($h*$maxW/$w); $d=imagecreatetruecolor($nw,$nh);
    imagealphablending($d,false); imagesavealpha($d,true);
    imagecopyresampled($d,$im,0,0,0,0,$nw,$nh,$w,$h); return $d;
}
function _img_out($im, string $path, string $ext): void {
    if ($ext==='png') imagepng($im,$path,6);
    elseif ($ext==='webp' && function_exists('imagewebp')) imagewebp($im,$path,82);
    elseif ($ext==='gif') imagegif($im,$path);
    else imagejpeg($im,$path,82);
}
