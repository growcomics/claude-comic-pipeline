<?php
// Project overview — renders the shared handoff doc inside the Studio (admin-gated).
// Source: data/handoff.md (web-blocked; served only through this page to logged-in users).
declare(strict_types=1);
require_once __DIR__ . '/inc/boot.php';
require_auth();

function ov_render_md(string $md): string {
    $inline = function ($s) {
        $s = htmlspecialchars($s, ENT_QUOTES, 'UTF-8');
        $s = preg_replace('/`([^`]+)`/', '<code>$1</code>', $s);
        $s = preg_replace('/\*\*([^*]+)\*\*/', '<strong>$1</strong>', $s);
        $s = preg_replace('/(^|[^*])\*([^*]+)\*/', '$1<em>$2</em>', $s);
        return $s;
    };
    $lines = explode("\n", $md);
    $n = count($lines); $i = 0; $html = ''; $list = null; $intable = false;
    $closeList = function () use (&$html, &$list) { if ($list) { $html .= '</' . $list . '>'; $list = null; } };
    while ($i < $n) {
        $line = $lines[$i];
        if (preg_match('/^\s*\|(.+)\|\s*$/', $line) && $i+1 < $n && preg_match('/^\s*\|[\s:\-|]+\|\s*$/', $lines[$i+1])) {
            $closeList();
            $cells = fn($l) => array_map('trim', explode('|', trim(trim($l), '|')));
            $html .= '<table class="ov-tbl"><thead><tr>';
            foreach ($cells($line) as $cth) $html .= '<th>' . $inline($cth) . '</th>';
            $html .= '</tr></thead><tbody>'; $i += 2;
            while ($i < $n && preg_match('/^\s*\|(.+)\|\s*$/', $lines[$i])) {
                $html .= '<tr>'; foreach ($cells($lines[$i]) as $ctd) $html .= '<td>' . $inline($ctd) . '</td>'; $html .= '</tr>'; $i++;
            }
            $html .= '</tbody></table>'; continue;
        }
        if (preg_match('/^(#{1,3}) (.*)/', $line, $m)) { $closeList(); $hl = strlen($m[1]); $html .= "<h$hl>" . $inline($m[2]) . "</h$hl>"; $i++; continue; }
        if (preg_match('/^---\s*$/', $line)) { $closeList(); $html .= '<hr>'; $i++; continue; }
        if (preg_match('/^\s*[-*] (.*)/', $line, $m)) { if ($list !== 'ul') { $closeList(); $html .= '<ul>'; $list = 'ul'; } $html .= '<li>' . $inline($m[1]) . '</li>'; $i++; continue; }
        if (preg_match('/^\s*\d+\. (.*)/', $line, $m)) { if ($list !== 'ol') { $closeList(); $html .= '<ol>'; $list = 'ol'; } $html .= '<li>' . $inline($m[1]) . '</li>'; $i++; continue; }
        if (trim($line) === '') { $closeList(); $i++; continue; }
        $closeList();
        $buf = [$line]; $i++;
        while ($i < $n && trim($lines[$i]) !== '' && !preg_match('#^(\s*#{1,3} |\s*[-*] |\s*\d+\. |---|\s*\|)#', $lines[$i])) { $buf[] = $lines[$i]; $i++; }
        $html .= '<p>' . $inline(implode(' ', $buf)) . '</p>';
    }
    $closeList();
    return $html;
}

$mdPath = SDATA . '/handoff.md';
$md = is_file($mdPath) ? file_get_contents($mdPath) : '';
?><!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><meta name="color-scheme" content="dark">
<meta name="robots" content="noindex,nofollow"><title>Project overview · Studio</title>
<link rel="icon" href="assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="assets/studio.css"><!-- the one bar across every system: ⌂ back to the hub, and a menu of everything else. Source: /hub/nav.js -->
<script src="https://3dmusclecomics.com/hub/nav.js"></script>
</head><body>
<header class="topbar"><div class="brand"><span class="dot"></span> Comic Studio</div>
  <a class="ghost" href="index.php">← Projects</a><span class="spacer"></span>
  <span class="ghost"><?= h(current_studio_user()) ?></span> <a class="ghost" href="login.php?do=logout">Log out</a></header>
<style>
.ov{max-width:860px;line-height:1.65;font-size:15px;color:#dfe1e7}
.ov h1{font-size:25px;font-weight:800;margin:8px 0 14px;line-height:1.25}
.ov h2{font-size:19px;font-weight:700;margin:30px 0 10px;padding-top:14px;border-top:1px solid #23252E}
.ov h3{font-size:16px;font-weight:600;margin:20px 0 8px;color:#fff}
.ov p{margin:0 0 12px}.ov ul,.ov ol{margin:0 0 14px;padding-left:22px}.ov li{margin:5px 0}
.ov strong{color:#fff;font-weight:600}.ov em{color:#c7cad4}
.ov code{background:#101116;border:1px solid #2E3140;border-radius:5px;padding:1px 5px;font:12.5px ui-monospace,Menlo,monospace;color:#f0c98a}
.ov hr{border:none;border-top:1px solid #23252E;margin:26px 0}
.ov a{color:#EF9F27;text-decoration:underline}
.ov-tbl{width:100%;border-collapse:collapse;margin:0 0 16px;font-size:13.5px}
.ov-tbl th,.ov-tbl td{border:1px solid #2E3140;padding:7px 10px;text-align:left;vertical-align:top}
.ov-tbl th{background:#14151C;color:#fff}
.ov-note{background:rgba(122,127,236,.1);border:1px solid rgba(122,127,236,.35);color:#c9ccf7;border-radius:10px;padding:11px 14px;font-size:13.5px;margin:6px 0 22px}
</style>
<main class="wrap">
  <div class="pagehead"><h1>Project overview</h1></div>
  <div class="ov-note">Shared get-up-to-speed brief for the team — what 3DMuscleComics is, what's live, and the comic-creator plan. Read the <a href="creator.php">Comic Creator</a> cockpit to see it in action.</div>
  <article class="ov"><?= $md !== '' ? ov_render_md($md) : '<p class="muted">Overview not found.</p>' ?></article>
</main></body></html>
