<?php
// Creator Pulse — patron analytics section of the Command Center.
// GENERATED from index.html by tools/deploy_3dmc.sh — edit index.html, not this file.
declare(strict_types=1);
require_once __DIR__ . '/../inc/boot.php';
// Join the studio's session scope: boot.php's s_boot() would scope the cookie to
// /studio/pulse (dirname of THIS script), shadowing the /studio login cookie.
if (session_status() === PHP_SESSION_NONE) {
    session_name('mgstudio');
    session_set_cookie_params(['lifetime'=>0,'path'=>'/studio','httponly'=>true,'samesite'=>'Lax',
        'secure'=>(!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS']!=='off')]);
    session_start();
}
if (!is_authed()) { header('Location: ../login.php'); exit; }
?><!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8">

<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Creator Pulse — your patron analytics</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Nunito+Sans:wght@400;600;700;800;900&display=swap" rel="stylesheet">
<link rel="stylesheet" href="css/style.css">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.min.js"></script>
<!-- the one bar across every system: ⌂ back to the hub, and a menu of everything else. Source: /hub/nav.js -->
<script src="https://3dmusclecomics.com/hub/nav.js"></script>
</head>
<body>
<aside class="sidebar">
  <a class="cc-back" href="../cc.php">&#8984; Command Center</a>
  <a class="logo" href="#/dashboard">
    <svg viewBox="0 0 40 32" width="34" height="28">
      <rect x="0"  y="12" width="6" height="8"  rx="1" fill="#d94f63"/>
      <rect x="8"  y="9"  width="6" height="14" rx="1" fill="#d94f63"/>
      <rect x="16" y="2"  width="7" height="28" rx="1" fill="#0d2136"/>
      <rect x="26" y="6"  width="6" height="12" rx="1" fill="#d94f63"/>
      <rect x="34" y="10" width="6" height="8"  rx="1" fill="#d94f63"/>
    </svg>
    <span>Creator<br>Pulse</span>
  </a>
  <div class="acct-switch" id="acct-switch"></div>
  <nav class="nav-main">
    <a href="#/dashboard" data-route="dashboard">
      <svg viewBox="0 0 20 20"><rect x="2" y="2" width="7" height="7" rx="1.5"/><rect x="11" y="2" width="7" height="7" rx="1.5"/><rect x="2" y="11" width="7" height="7" rx="1.5"/><rect x="11" y="11" width="7" height="7" rx="1.5"/></svg>
      Overview</a>
    <a href="#/rollup" data-route="rollup">
      <svg viewBox="0 0 20 20"><rect x="2" y="10" width="4" height="8" rx="1"/><rect x="8" y="5" width="4" height="13" rx="1"/><rect x="14" y="2" width="4" height="16" rx="1"/></svg>
      All accounts</a>
    <a href="#/balance" data-route="balance">
      <svg viewBox="0 0 20 20"><rect x="2" y="4" width="16" height="12" rx="2"/><circle cx="10" cy="10" r="3" fill="#fff"/></svg>
      Balance</a>
    <a href="#/retention" data-route="retention">
      <svg viewBox="0 0 20 20"><path d="M10 2a8 8 0 1 1-8 8h3a5 5 0 1 0 5-5z"/><path d="M10 2v5l-4 3z" opacity=".55"/></svg>
      Retention</a>
    <a href="#/strategy" data-route="strategy">
      <svg viewBox="0 0 20 20"><rect x="2" y="2" width="16" height="16" rx="2"/><path d="M5 13l3-4 3 2 4-6" stroke="#fff" stroke-width="1.8" fill="none"/></svg>
      Strategy</a>
    <a href="#/patrons" data-route="patrons">
      <svg viewBox="0 0 20 20"><rect x="3" y="2" width="3" height="16" rx="1"/><circle cx="12.5" cy="8" r="5.5"/></svg>
      Patrons</a>
    <a href="#/emails" data-route="emails">
      <svg viewBox="0 0 20 20"><rect x="2" y="4" width="16" height="12" rx="2"/><path d="M3 6l7 5 7-5" stroke="#fff" stroke-width="1.6" fill="none"/></svg>
      Emails</a>
  </nav>
  <nav class="nav-bottom">
    <a href="#/account">
      <svg viewBox="0 0 20 20"><circle cx="10" cy="6.5" r="3.5"/><path d="M3 17a7 7 0 0 1 14 0z"/></svg>
      Account</a>
    <a href="#/logout">
      <svg viewBox="0 0 20 20"><path d="M8 3H4a1.5 1.5 0 0 0-1.5 1.5v11A1.5 1.5 0 0 0 4 17h4"/><path d="M12 6l4 4-4 4M8 10h8" stroke-width="1.8" stroke="currentColor" fill="none"/></svg>
      Log out</a>
    <a href="mailto:you@example.com">
      <svg viewBox="0 0 20 20"><circle cx="10" cy="10" r="8"/><text x="10" y="14" text-anchor="middle" font-size="11" fill="#fff" font-weight="bold">?</text></svg>
      Help / Feedback</a>
  </nav>
</aside>

<div class="app-body" id="app"></div>

<script src="js/data.js"></script>
<script src="js/app.js"></script>
</body>
</html>
