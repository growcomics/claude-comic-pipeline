<?php
// Creator Pulse — session-gated data passthrough (Task 6).
// Revenue JSON lives in studio/data/pulse/, protected by studio/data/.htaccess
// ("Require all denied") so it is NEVER publicly fetchable over HTTP. This endpoint
// checks the studio session and streams the requested account's synced JSON server-side;
// anything else 4xx's and the frontend falls back to demo data.
declare(strict_types=1);
require_once __DIR__ . '/../inc/boot.php';
// Join the studio session scope BEFORE is_authed()/s_boot() runs, exactly as index.php does,
// so the cookie isn't re-scoped to /studio/pulse and shadow the /studio login.
if (session_status() === PHP_SESSION_NONE) {
    session_name('mgstudio');
    session_set_cookie_params(['lifetime' => 0, 'path' => '/studio', 'httponly' => true, 'samesite' => 'Lax',
        'secure' => (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off')]);
    session_start();
}

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');
header('X-Content-Type-Options: nosniff');

if (!is_authed()) { http_response_code(403); echo '{"error":"not authenticated"}'; exit; }

$acct  = (string)($_GET['acct'] ?? '');
$allow = ['bloom', 'growgetter', 'maxx', 'giantess'];
if (!in_array($acct, $allow, true)) { http_response_code(400); echo '{"error":"unknown account"}'; exit; }

$path = '/home/dmusclecomics/public_html/studio/data/pulse/' . $acct . '.json';
if (!is_file($path)) { http_response_code(404); echo '{"error":"no synced data yet"}'; exit; }

readfile($path);
