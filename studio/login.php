<?php
declare(strict_types=1);
require_once __DIR__ . '/inc/boot.php';
s_boot();
if (($_GET['do'] ?? '') === 'logout') { sign_out(); header('Location: login.php'); exit; }
if (is_authed()) { header('Location: index.php'); exit; }

$err = '';
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    usleep(250000);
    if (studio_login((string)($_POST['username'] ?? ''), (string)($_POST['password'] ?? ''))) { header('Location: index.php'); exit; }
    $err = 'Wrong username or password.';
}
?><!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark"><meta name="robots" content="noindex,nofollow">
<title>Studio · sign in</title><link rel="stylesheet" href="assets/studio.css">
<style>body{display:flex;align-items:center;justify-content:center;min-height:100vh}</style></head><body>
<form class="card auth" method="post" autocomplete="on">
  <div class="brand"><span class="dot"></span> Comic Studio</div>
  <h1>Sign in</h1>
  <p class="muted">Use your <strong>3dmusclecomics admin</strong> username &amp; password.</p>
  <?php if ($err): ?><div class="flash err"><?= h($err) ?></div><?php endif; ?>
  <label>Username<input name="username" required autofocus autocomplete="username"></label>
  <label>Password<input type="password" name="password" required autocomplete="current-password"></label>
  <button class="btn primary">Sign in</button>
</form></body></html>
