<?php
// Studio guide — graphical "how to use the system" walkthrough of the full
// references-first comic workflow (Studio + Google Flow). Replaces the old
// worker/queue help (that automated path isn't built yet — see the gotchas).
declare(strict_types=1);
require_once __DIR__ . '/inc/boot.php';
require_auth();
$cssv = @filemtime(STUDIO_ROOT.'/assets/studio.css') ?: '1';
?><!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><meta name="color-scheme" content="dark">
<meta name="robots" content="noindex,nofollow"><title>Guide · how to use the Comic Studio</title>
<link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="assets/studio.css?v=<?= h((string)$cssv) ?>"><!-- the one bar across every system: ⌂ back to the hub, and a menu of everything else. Source: /hub/nav.js -->
<script src="https://3dmusclecomics.com/hub/nav.js"></script>
</head><body>
<header class="topbar" style="border-bottom:2px solid #7A7FEC"><div class="brand"><span class="dot"></span> Comic Studio
  <span style="background:#7A7FEC;color:#0B0C10;font-size:11px;font-weight:800;letter-spacing:.04em;border-radius:999px;padding:2px 9px;margin-left:6px">📖 GUIDE</span></div>
  <a class="ghost" href="index.php">← Projects</a> <a class="ghost" href="creator.php">🎬 Comic Creator</a>
  <span class="spacer"></span><span class="ghost"><?= h(current_studio_user()) ?></span>
  <a class="ghost" href="login.php?do=logout">Log out</a></header>

<style>
.gd{--p:#7A7FEC}
.gd-shell{display:flex;gap:36px;align-items:flex-start;max-width:1140px;margin:0 auto;padding:26px 22px 100px}
.gd-rail{position:sticky;top:74px;flex:none;width:210px;font-size:13px}
.gd-rail a{display:block;color:var(--muted);padding:6px 11px;border-radius:7px;border-left:2px solid transparent;line-height:1.3}
.gd-rail a:hover{color:var(--text);background:var(--surface);border-left-color:var(--p)}
.gd-rail .lbl{font-size:10.5px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted2);margin:16px 0 4px;padding-left:11px}
.gd-rail .lbl:first-child{margin-top:0}
.gd-main{flex:1;min-width:0;max-width:850px}
@media(max-width:880px){.gd-shell{flex-direction:column;gap:14px}.gd-rail{position:static;width:auto;display:flex;flex-wrap:wrap;gap:3px}.gd-rail .lbl{width:100%;margin:8px 0 2px}}
.gd h1{font-size:30px;font-weight:800;letter-spacing:-.015em;margin:0 0 8px}
.gd .lead{color:var(--muted);font-size:15.5px;line-height:1.6;margin:0 0 22px;max-width:700px}
.gd h2{font-size:12.5px;text-transform:uppercase;letter-spacing:.08em;color:var(--p);margin:42px 0 14px;scroll-margin-top:76px}
.gd section{scroll-margin-top:76px}
.gd h3{font-size:18px;margin:0 0 8px;font-weight:700}
.gd p{margin:0 0 12px;line-height:1.64;color:#dadce3}
.gd ul,.gd ol{margin:0 0 14px;padding-left:21px}.gd li{margin:6px 0;line-height:1.55;color:#dadce3}
.gd b{color:#fff;font-weight:700}
.gd a.ln{color:#aeb2ff;font-weight:600}
.gd code{background:var(--bg2);border:1px solid var(--border2);border-radius:5px;padding:1px 6px;font:12.5px ui-monospace,Menlo,monospace;color:#f0c98a}
.gd .pill{display:inline-block;background:rgba(122,127,236,.16);color:#c2c5ff;border:1px solid rgba(122,127,236,.4);border-radius:999px;padding:1px 9px;font-size:12.5px;font-weight:700;white-space:nowrap}
.gd kbd{display:inline-block;min-width:22px;text-align:center;background:#14151C;border:1px solid #2E3140;border-bottom-width:2px;border-radius:6px;padding:1px 7px;font:600 12px ui-monospace,Menlo,monospace;color:#fff}
.gd .fig{background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:16px 16px 12px;margin:0 0 20px}
.gd .fig svg{display:block;width:100%;height:auto}
.gd .figcap{font-size:12px;color:var(--muted2);margin-top:10px;text-align:center;line-height:1.4}
.gd .breath{background:linear-gradient(135deg,rgba(122,127,236,.14),rgba(29,158,117,.10));border:1px solid rgba(122,127,236,.32);border-radius:14px;padding:16px 20px;margin:0 0 26px;font-size:15px;line-height:1.6;color:#e7e8f2}
.gd .breath b{color:#fff}
.gd .tools{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:0 0 16px}
@media(max-width:560px){.gd .tools{grid-template-columns:1fr}}
.gd .tool{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:15px 17px}
.gd .tool h4{margin:0 0 5px;font-size:15px;color:#fff}
.gd .tool p{margin:0;font-size:13.5px;color:var(--muted)}
.gd .stage{position:relative;background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:20px 22px 16px 22px;margin:0 0 16px}
.gd .stage>.n{position:absolute;top:-14px;left:20px;width:30px;height:30px;border-radius:50%;background:var(--p);color:#0B0C10;font-weight:800;font-size:14px;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 8px rgba(122,127,236,.4)}
.gd .stage h3{margin:8px 0 8px;display:flex;align-items:center;gap:9px}
.gd .stage h3 .em{font-size:21px;line-height:1}
.gd .where{background:var(--bg2);border:1px solid var(--border2);border-radius:10px;padding:9px 13px;font-size:13px;color:var(--muted);margin:12px 0 4px}
.gd .where b{color:#fff}
.gd .where .pin{color:var(--p);font-weight:700}
.gd .cal{border-radius:11px;padding:11px 14px;margin:14px 0;font-size:14px;border:1px solid;line-height:1.55}
.gd .cal b{font-weight:800}
.gd .tip{background:rgba(29,158,117,.10);border-color:rgba(29,158,117,.35);color:#8fe3c2}
.gd .warn{background:rgba(239,159,39,.10);border-color:rgba(239,159,39,.38);color:#f4cd8a}
.gd .stop{background:rgba(226,75,74,.10);border-color:rgba(226,75,74,.38);color:#f3a3a2}
.gd .cal .h{color:#fff;font-weight:800}
.gd .gotchas{display:grid;gap:12px}
.gd .gotcha{display:flex;gap:13px;background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:13px 16px}
.gd .gotcha .gi{flex:none;font-size:21px;line-height:1.2}
.gd .gotcha h4{margin:0 0 3px;font-size:14.5px;color:#fff}
.gd .gotcha p{margin:0;font-size:13.5px;color:var(--muted);line-height:1.5}
.gd .good{background:rgba(29,158,117,.08);border:1px solid rgba(29,158,117,.3);border-radius:14px;padding:16px 20px;margin:0 0 16px}
.gd .good h3{color:#8fe3c2;margin:0 0 8px;font-size:16px}
.gd .good li{color:#cfeede}
.gd .endnote{color:var(--muted2);font-size:13px;margin-top:30px;text-align:center}
</style>

<main class="gd"><div class="gd-shell">

<!-- ============ LEFT RAIL ============ -->
<nav class="gd-rail">
  <div class="lbl">Orientation</div>
  <a href="#overview">Pipeline at a glance</a>
  <a href="#tools">The two tools</a>
  <a href="#map">Studio map</a>
  <div class="lbl">Step by step</div>
  <a href="#signin">1 · Sign in</a>
  <a href="#project">2 · Create a project</a>
  <a href="#references">3 · Build references</a>
  <a href="#script">4 · Script → pages</a>
  <a href="#prodguide">5 · Production guide</a>
  <a href="#flow">6 · Generate in Flow</a>
  <a href="#review">7 · Auto-sync &amp; review</a>
  <div class="lbl">Keep handy</div>
  <a href="#gotchas">Honest gotchas</a>
  <a href="#good">What "good" looks like</a>
</nav>

<!-- ============ MAIN ============ -->
<div class="gd-main">

  <h1>How to use the Comic Studio</h1>
  <p class="lead">Take a script and a set of references and turn them into finished comic pages — using this Studio as the brain and Google Flow as the hands. Follow the steps in order. The first comic is the slow one; after that it's fast.</p>

  <div class="breath"><b>The whole job in one breath:</b> make your reference images → upload &amp; <b>lock</b> them in the Studio → paste your script and break it into pages → generate each panel in <b>Google Flow</b> using the Studio's per-panel prompts &amp; references → the finished panels <b>auto-sync</b> back here, where you review them.</div>

  <!-- ===== PIPELINE AT A GLANCE ===== -->
  <section id="overview">
  <h2>Pipeline at a glance</h2>
  <div class="fig">
    <svg viewBox="0 0 1000 152" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Six-stage pipeline: References, Script, Pages, Generate in Flow, Auto-sync, Review">
      <defs>
        <marker id="arP" markerWidth="9" markerHeight="9" refX="6.5" refY="3.2" orient="auto"><path d="M0,0 L7,3.2 L0,6.4 Z" fill="#6F7380"/></marker>
      </defs>
      <!-- nodes: x = 4 + i*174, w=126, y=20 h=98 -->
      <!-- 1 References -->
      <g><rect x="4" y="20" width="126" height="98" rx="13" fill="#14151C" stroke="#EF9F27" stroke-width="1.6"/>
        <text x="67" y="60" text-anchor="middle" font-size="28">🗂</text>
        <text x="67" y="92" text-anchor="middle" font-size="13.5" font-weight="700" fill="#F2F2F4">References</text>
        <text x="67" y="108" text-anchor="middle" font-size="10.5" fill="#9CA0AC">the cast</text></g>
      <!-- 2 Script -->
      <g><rect x="178" y="20" width="126" height="98" rx="13" fill="#14151C" stroke="#5BA7E6" stroke-width="1.6"/>
        <text x="241" y="60" text-anchor="middle" font-size="28">📜</text>
        <text x="241" y="92" text-anchor="middle" font-size="13.5" font-weight="700" fill="#F2F2F4">Script</text>
        <text x="241" y="108" text-anchor="middle" font-size="10.5" fill="#9CA0AC">the story</text></g>
      <!-- 3 Pages -->
      <g><rect x="352" y="20" width="126" height="98" rx="13" fill="#14151C" stroke="#378ADD" stroke-width="1.6"/>
        <text x="415" y="60" text-anchor="middle" font-size="28">📑</text>
        <text x="415" y="92" text-anchor="middle" font-size="13.5" font-weight="700" fill="#F2F2F4">Pages</text>
        <text x="415" y="108" text-anchor="middle" font-size="10.5" fill="#9CA0AC">panel plan</text></g>
      <!-- 4 Generate in Flow -->
      <g><rect x="526" y="20" width="126" height="98" rx="13" fill="#14151C" stroke="#7A7FEC" stroke-width="1.6"/>
        <text x="589" y="58" text-anchor="middle" font-size="28">🍌</text>
        <text x="589" y="89" text-anchor="middle" font-size="13" font-weight="700" fill="#F2F2F4">Generate</text>
        <text x="589" y="105" text-anchor="middle" font-size="11" fill="#9CA0AC">in Flow</text></g>
      <!-- 5 Auto-sync -->
      <g><rect x="700" y="20" width="126" height="98" rx="13" fill="#14151C" stroke="#4FB3A0" stroke-width="1.6"/>
        <text x="763" y="60" text-anchor="middle" font-size="26">🔄</text>
        <text x="763" y="92" text-anchor="middle" font-size="13.5" font-weight="700" fill="#F2F2F4">Auto-sync</text>
        <text x="763" y="108" text-anchor="middle" font-size="10.5" fill="#9CA0AC">back here</text></g>
      <!-- 6 Review -->
      <g><rect x="874" y="20" width="126" height="98" rx="13" fill="#14151C" stroke="#1D9E75" stroke-width="1.6"/>
        <text x="937" y="59" text-anchor="middle" font-size="26" fill="#1D9E75" font-weight="800">✓</text>
        <text x="937" y="92" text-anchor="middle" font-size="13.5" font-weight="700" fill="#F2F2F4">Review</text>
        <text x="937" y="108" text-anchor="middle" font-size="10.5" fill="#9CA0AC">pick winners</text></g>
      <!-- arrows -->
      <line x1="132" y1="69" x2="174" y2="69" stroke="#6F7380" stroke-width="1.8" marker-end="url(#arP)"/>
      <line x1="306" y1="69" x2="348" y2="69" stroke="#6F7380" stroke-width="1.8" marker-end="url(#arP)"/>
      <line x1="480" y1="69" x2="522" y2="69" stroke="#6F7380" stroke-width="1.8" marker-end="url(#arP)"/>
      <line x1="654" y1="69" x2="696" y2="69" stroke="#6F7380" stroke-width="1.8" marker-end="url(#arP)"/>
      <line x1="828" y1="69" x2="870" y2="69" stroke="#6F7380" stroke-width="1.8" marker-end="url(#arP)"/>
    </svg>
    <div class="figcap">Consistency lives in stage&nbsp;1. Everything downstream just <em>reuses</em> the references you lock.</div>
  </div>
  </section>

  <!-- ===== THE TWO TOOLS ===== -->
  <section id="tools">
  <h2>The two tools</h2>
  <div class="tools">
    <div class="tool"><h4>🗂 The Comic Studio</h4><p>The <b>brain</b>. Holds your references, your script, the page plan, and a per-panel "production guide" that tells you exactly what to generate. This site.</p></div>
    <div class="tool"><h4>🍌 Google Flow</h4><p>The <b>hands</b>. The actual image generator. Use the model <b>Nano Banana Pro</b>. Browser only — <code>labs.google/fx/tools/flow</code>.</p></div>
  </div>
  <div class="cal tip"><b class="h">The one big idea:</b> consistency comes from <b>references</b>. Every character, place, and prop in a panel is <em>copied from a reference image</em>. Great reference sheets = the same character in every panel. Skimp here and your character changes face every panel. Spend your effort in stage&nbsp;3.</div>
  </section>

  <!-- ===== STUDIO MAP ===== -->
  <section id="map">
  <h2>Studio map — the pages and how they connect</h2>
  <div class="fig">
    <svg viewBox="0 0 1000 350" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Studio page map: Sign in to Projects to Comic Creator, which branches to References workspace, Production guide and Gallery; Flow and the auto-sync extension feed panels back into the cockpit.">
      <defs>
        <marker id="arM" markerWidth="9" markerHeight="9" refX="6.5" refY="3.2" orient="auto"><path d="M0,0 L7,3.2 L0,6.4 Z" fill="#6F7380"/></marker>
        <marker id="arMd" markerWidth="9" markerHeight="9" refX="6.5" refY="3.2" orient="auto"><path d="M0,0 L7,3.2 L0,6.4 Z" fill="#4FB3A0"/></marker>
      </defs>
      <!-- Sign in -->
      <rect x="190" y="14" width="220" height="38" rx="9" fill="#191B24" stroke="#2E3140"/>
      <text x="300" y="38" text-anchor="middle" font-size="13" fill="#dadce3">Sign in · <tspan fill="#9CA0AC">/studio</tspan></text>
      <line x1="300" y1="52" x2="300" y2="72" stroke="#6F7380" stroke-width="1.6" marker-end="url(#arM)"/>
      <!-- Projects -->
      <rect x="205" y="74" width="190" height="42" rx="9" fill="#14151C" stroke="#23252E"/>
      <text x="300" y="96" text-anchor="middle" font-size="13.5" font-weight="700" fill="#F2F2F4">Projects</text>
      <text x="300" y="109" text-anchor="middle" font-size="10.5" fill="#9CA0AC">index.php</text>
      <line x1="300" y1="116" x2="300" y2="136" stroke="#6F7380" stroke-width="1.6" marker-end="url(#arM)"/>
      <!-- Comic Creator hub -->
      <rect x="160" y="138" width="280" height="62" rx="12" fill="#1a1626" stroke="#7A7FEC" stroke-width="1.8"/>
      <text x="300" y="166" text-anchor="middle" font-size="15" font-weight="800" fill="#fff">🎬 Comic Creator</text>
      <text x="300" y="185" text-anchor="middle" font-size="11" fill="#c2c5ff">creator.php — the cockpit / hub</text>
      <!-- fan to 3 children -->
      <line x1="240" y1="200" x2="120" y2="244" stroke="#6F7380" stroke-width="1.6" marker-end="url(#arM)"/>
      <line x1="300" y1="200" x2="300" y2="244" stroke="#6F7380" stroke-width="1.6" marker-end="url(#arM)"/>
      <line x1="360" y1="200" x2="480" y2="244" stroke="#6F7380" stroke-width="1.6" marker-end="url(#arM)"/>
      <!-- children -->
      <rect x="20" y="246" width="200" height="64" rx="11" fill="#14151C" stroke="#23252E"/>
      <text x="120" y="270" text-anchor="middle" font-size="13" font-weight="700" fill="#F2F2F4">🗂 References</text>
      <text x="120" y="286" text-anchor="middle" font-size="11" fill="#dadce3">workspace</text>
      <text x="120" y="300" text-anchor="middle" font-size="10.5" fill="#9CA0AC">refs.php</text>
      <rect x="200" y="246" width="200" height="64" rx="11" fill="#14151C" stroke="#23252E"/>
      <text x="300" y="270" text-anchor="middle" font-size="13" font-weight="700" fill="#F2F2F4">📋 Production</text>
      <text x="300" y="286" text-anchor="middle" font-size="11" fill="#dadce3">guide</text>
      <text x="300" y="300" text-anchor="middle" font-size="10.5" fill="#9CA0AC">shots.php</text>
      <rect x="380" y="246" width="200" height="64" rx="11" fill="#14151C" stroke="#23252E"/>
      <text x="480" y="270" text-anchor="middle" font-size="13" font-weight="700" fill="#F2F2F4">🖼 Gallery /</text>
      <text x="480" y="286" text-anchor="middle" font-size="11" fill="#dadce3">organize</text>
      <text x="480" y="300" text-anchor="middle" font-size="10.5" fill="#9CA0AC">project.php</text>
      <!-- Flow round-trip box (right) -->
      <rect x="640" y="120" width="340" height="118" rx="12" fill="#101116" stroke="#4FB3A0" stroke-width="1.5" stroke-dasharray="6 5"/>
      <text x="810" y="146" text-anchor="middle" font-size="13.5" font-weight="800" fill="#fff">🍌 Google Flow  +  🔄 Auto-sync</text>
      <text x="810" y="170" text-anchor="middle" font-size="11.5" fill="#cfe9e0">You generate panels in Flow; the</text>
      <text x="810" y="187" text-anchor="middle" font-size="11.5" fill="#cfe9e0">auto-sync browser extension drops the</text>
      <text x="810" y="204" text-anchor="middle" font-size="11.5" fill="#cfe9e0">results straight into the cockpit's</text>
      <text x="810" y="221" text-anchor="middle" font-size="11.5" font-weight="700" fill="#8fe3c2">Live panels.</text>
      <!-- curved dashed connector creator <-> flow -->
      <path d="M440 165 C 540 150, 560 175, 638 175" fill="none" stroke="#4FB3A0" stroke-width="1.5" stroke-dasharray="6 5" marker-end="url(#arMd)"/>
      <path d="M638 200 C 560 215, 540 205, 442 192" fill="none" stroke="#4FB3A0" stroke-width="1.5" stroke-dasharray="6 5" marker-end="url(#arMd)"/>
    </svg>
    <div class="figcap">The cockpit (<code>creator.php</code>) is the hub. Open a project from Projects and everything branches from there.</div>
  </div>
  </section>

  <h2>Before you start</h2>
  <div class="cal stop"><b class="h">Never</b> paste or forward API keys, passwords, or tokens in email, chat, or any document. If a step needs a key, that's the owner's job. You'll need: a <b>Studio login</b> (the owner sends it separately), a <b>Google account with Flow</b> (Pro/Ultra — it needs image generation), and a couple of hours of patience for the first comic.</div>

  <!-- ============ STAGES ============ -->

  <!-- 1 SIGN IN -->
  <section id="signin"><div class="stage"><span class="n">1</span>
    <h3><span class="em">🔑</span> Sign in to the Studio</h3>
    <p>Go to <code>3dmusclecomics.com/studio</code> and sign in with the username + password the owner gave you. You land on the <b>Projects</b> list — your home base. (The Studio uses the same logins as the site's admin team.)</p>
    <div class="where"><span class="pin">Where:</span> top of every page — <b>← Projects</b> takes you home; <b>Log out</b> is on the right of the topbar.</div>
  </div></section>

  <!-- 2 CREATE PROJECT -->
  <section id="project"><div class="stage"><span class="n">2</span>
    <h3><span class="em">🎬</span> Create a project — meet the cockpit</h3>
    <p>On the Projects page click <span class="pill">🎬 Comic Creator</span>, then <b>+ New project</b> and name it your comic's title. Opening any project drops you straight into the <b>Comic Creator</b> — your cockpit, marked with a purple <span class="pill">🎬 COMIC CREATOR</span> badge so you always know which mode you're in.</p>
    <div class="fig">
      <svg viewBox="0 0 600 366" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Sketch of the Comic Creator cockpit: a Brief field, a Script panel with a break-into-pages button, a references panel with an open-workspace button, a production-guide button, a disabled queue button, and a Live panels grid.">
        <rect x="6" y="6" width="588" height="354" rx="14" fill="#101116" stroke="#23252E"/>
        <!-- topbar -->
        <rect x="6" y="6" width="588" height="38" rx="14" fill="#0d0e13"/>
        <rect x="6" y="42" width="588" height="2" fill="#7A7FEC"/>
        <circle cx="26" cy="25" r="5" fill="#EF9F27"/>
        <text x="40" y="30" font-size="12.5" font-weight="800" fill="#fff">Comic Studio</text>
        <rect x="132" y="15" width="132" height="20" rx="10" fill="#7A7FEC"/>
        <text x="198" y="29" text-anchor="middle" font-size="11" font-weight="800" fill="#0B0C10">🎬 COMIC CREATOR</text>
        <text x="556" y="30" text-anchor="end" font-size="11" fill="#9CA0AC">❔ Guide · Log out</text>
        <!-- left column -->
        <!-- Brief -->
        <text x="26" y="68" font-size="11.5" font-weight="700" fill="#c2c5ff">📝 Brief</text>
        <rect x="26" y="74" width="300" height="26" rx="7" fill="#14151C" stroke="#2E3140"/>
        <text x="38" y="91" font-size="11" fill="#6F7380">one line — what we're making</text>
        <!-- Script -->
        <text x="26" y="120" font-size="11.5" font-weight="700" fill="#c2c5ff">📜 Script / story</text>
        <rect x="26" y="126" width="300" height="58" rx="7" fill="#14151C" stroke="#2E3140"/>
        <text x="38" y="145" font-size="10.5" fill="#6F7380">paste your synopsis + scene beats…</text>
        <rect x="26" y="190" width="74" height="22" rx="6" fill="#191B24" stroke="#2E3140"/>
        <text x="63" y="205" text-anchor="middle" font-size="10" fill="#dadce3">Save</text>
        <rect x="106" y="190" width="160" height="22" rx="6" fill="#7A7FEC"/>
        <text x="186" y="205" text-anchor="middle" font-size="10" font-weight="800" fill="#0B0C10">📑 Break into pages</text>
        <!-- References -->
        <text x="26" y="236" font-size="11.5" font-weight="700" fill="#c2c5ff">🗂 References  <tspan fill="#1D9E75">🔒 locked ✓</tspan></text>
        <rect x="26" y="244" width="300" height="40" rx="7" fill="#14151C" stroke="#2E3140"/>
        <rect x="36" y="254" width="22" height="22" rx="4" fill="#23252E"/><rect x="62" y="254" width="22" height="22" rx="4" fill="#23252E"/><rect x="88" y="254" width="22" height="22" rx="4" fill="#23252E"/>
        <text x="320" y="270" text-anchor="end" font-size="10" fill="#6F7380">read-only here ↑</text>
        <rect x="26" y="292" width="190" height="24" rx="7" fill="#191B24" stroke="#3c4052"/>
        <text x="121" y="308" text-anchor="middle" font-size="10.5" fill="#dadce3">🗂 Open references workspace</text>
        <!-- prod guide + queue -->
        <rect x="26" y="326" width="150" height="24" rx="7" fill="#7A7FEC"/>
        <text x="101" y="342" text-anchor="middle" font-size="10.5" font-weight="800" fill="#0B0C10">📋 Production guide</text>
        <rect x="184" y="326" width="142" height="24" rx="7" fill="#101116" stroke="#2E3140" stroke-dasharray="4 3"/>
        <text x="255" y="342" text-anchor="middle" font-size="10.5" fill="#5b5f6b">▶ Queue (not built)</text>
        <!-- right column: live panels -->
        <line x1="346" y1="56" x2="346" y2="350" stroke="#23252E"/>
        <text x="364" y="68" font-size="11.5" font-weight="700" fill="#c2c5ff">Live panels</text>
        <text x="556" y="68" text-anchor="end" font-size="10" fill="#6F7380">↻ auto-refresh</text>
        <rect x="364" y="78" width="103" height="80" rx="7" fill="#14151C" stroke="#2E3140"/>
        <rect x="475" y="78" width="103" height="80" rx="7" fill="#14151C" stroke="#2E3140"/>
        <rect x="364" y="166" width="103" height="80" rx="7" fill="#14151C" stroke="#2E3140"/>
        <rect x="475" y="166" width="103" height="80" rx="7" fill="#14151C" stroke="#2E3140"/>
        <text x="471" y="124" text-anchor="middle" font-size="22" fill="#2E3140">▦</text>
        <text x="471" y="300" text-anchor="middle" font-size="10.5" fill="#6F7380">finished panels land here →</text>
      </svg>
      <div class="figcap">The cockpit, top to bottom: <b>Brief</b> · <b>Script</b> (with 📑 break into pages) · <b>References</b> (read-only summary + a button to the full workspace) · <b>Production guide</b> · <b>Live panels</b>.</div>
    </div>
    <div class="cal warn"><b class="h">Ignore the ▶ Queue generation button.</b> It's wired for a future automated generator that isn't built yet — clicking it just parks a job that nothing picks up. For now you generate by hand in Flow using the <b>Production guide</b> (stage&nbsp;5).</div>
  </div></section>

  <!-- 3 REFERENCES -->
  <section id="references"><div class="stage"><span class="n">3</span>
    <h3><span class="em">🗂</span> Build &amp; lock your references <span class="muted" style="font-size:13px;font-weight:500">— the real work</span></h3>
    <p><b>Make a reference for everything that recurs.</b> Per character: a reference sheet — full-body <b>turnaround</b> (front / side / back) + the face + a few expressions, on a plain neutral background. Per location: a clean <b>scene plate</b>. Per important prop: a clean shot. Generate them in Flow with a character-sheet prompt, e.g.:</p>
    <p style="background:#0d1320;border-left:3px solid #5BA7E6;border-radius:0 8px 8px 0;padding:10px 14px;font-size:13px;color:#bcd4ee;margin:0 0 14px"><em>"Character reference sheet, photorealistic 3D CGI / DAZ3D render style, neutral grey studio background. Full-body turnaround of [age, build, hair, outfit] — front, three-quarter, side, back — plus a row of head-and-shoulders expressions (neutral, smiling, angry, surprised). Consistent lighting, sharp detail."</em></p>
    <p>Then bring them into the Studio:</p>
    <div class="fig">
      <svg viewBox="0 0 600 326" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Sketch of the references workspace: a lock bar, an add-references dropzone, and character groups with thumbnails, set-kind and approve-all controls.">
        <rect x="6" y="6" width="588" height="314" rx="14" fill="#101116" stroke="#23252E"/>
        <!-- lock bar -->
        <rect x="20" y="20" width="560" height="40" rx="9" fill="#14151C" stroke="#7a5a1f"/>
        <text x="34" y="44" font-size="12.5" font-weight="700" fill="#fac775">🔒 Lock references &amp; scenes</text>
        <text x="566" y="44" text-anchor="end" font-size="11" fill="#9CA0AC">freezes the approved set ✓</text>
        <!-- dropzone -->
        <rect x="20" y="70" width="270" height="56" rx="10" fill="#101116" stroke="#2E3140" stroke-dasharray="5 4"/>
        <text x="155" y="94" text-anchor="middle" font-size="12" font-weight="700" fill="#dadce3">➕ Add references</text>
        <text x="155" y="111" text-anchor="middle" font-size="10.5" fill="#6F7380">drop a whole batch · auto-groups</text>
        <!-- tools -->
        <rect x="300" y="70" width="280" height="56" rx="10" fill="#14151C" stroke="#23252E"/>
        <text x="314" y="90" font-size="11" fill="#9CA0AC">✨ AI sort   ·   📖 read text   ·   📜 script context</text>
        <text x="314" y="112" font-size="10.5" fill="#6F7380">(optional helpers — owner enables ✨)</text>
        <!-- group A -->
        <text x="20" y="152" font-size="12" font-weight="800" fill="#fff">Andrea</text>
        <rect x="76" y="140" width="72" height="18" rx="5" fill="#191B24" stroke="#2E3140"/><text x="112" y="153" text-anchor="middle" font-size="9.5" fill="#dadce3">set kind ▾</text>
        <rect x="152" y="140" width="46" height="18" rx="5" fill="#191B24" stroke="#2E3140"/><text x="175" y="153" text-anchor="middle" font-size="9.5" fill="#dadce3">apply</text>
        <rect x="202" y="140" width="86" height="18" rx="5" fill="#1D9E75"/><text x="245" y="153" text-anchor="middle" font-size="9.5" font-weight="800" fill="#04221a">✓ approve all</text>
        <g>
          <rect x="20" y="164" width="74" height="74" rx="7" fill="#14151C" stroke="#2E3140"/><rect x="24" y="226" width="36" height="9" rx="3" fill="#EF9F27"/><text x="42" y="234" text-anchor="middle" font-size="7" fill="#412402">face</text>
          <rect x="100" y="164" width="74" height="74" rx="7" fill="#14151C" stroke="#2E3140"/><rect x="104" y="226" width="36" height="9" rx="3" fill="#378ADD"/><text x="122" y="234" text-anchor="middle" font-size="7" fill="#04223a">body</text>
          <rect x="180" y="164" width="74" height="74" rx="7" fill="#14151C" stroke="#2E3140"/><rect x="184" y="226" width="36" height="9" rx="3" fill="#5BA7E6"/><text x="202" y="234" text-anchor="middle" font-size="7" fill="#04223a">view</text>
        </g>
        <!-- group scenes -->
        <text x="300" y="152" font-size="12" font-weight="800" fill="#fff">Scenes &amp; locations</text>
        <rect x="300" y="164" width="120" height="74" rx="7" fill="#14151C" stroke="#2E3140"/><rect x="304" y="226" width="44" height="9" rx="3" fill="#1D9E75"/><text x="326" y="234" text-anchor="middle" font-size="7" fill="#04221a">scene</text>
        <rect x="426" y="164" width="120" height="74" rx="7" fill="#14151C" stroke="#2E3140"/><rect x="430" y="226" width="44" height="9" rx="3" fill="#1D9E75"/><text x="452" y="234" text-anchor="middle" font-size="7" fill="#04221a">scene</text>
        <!-- footer note -->
        <text x="20" y="266" font-size="10.5" fill="#6F7380">kinds: face · body · view · scene · prop  —  set per card or a whole group at once</text>
        <rect x="20" y="278" width="560" height="30" rx="8" fill="#0d1f17" stroke="#1D9E75"/>
        <text x="300" y="297" text-anchor="middle" font-size="11" fill="#8fe3c2">Approve the keepers → <tspan font-weight="800">🔒 Lock</tspan> → this becomes the cast your whole comic is built from.</text>
      </svg>
      <div class="figcap">The references workspace (<code>refs.php</code>) — reach it from the cockpit's <b>🗂 Open references workspace</b> button.</div>
    </div>
    <ol>
      <li><b>Add references</b> — under <b>➕ Add references</b>, select <b>all</b> your images at once. Leave the character box <b>blank</b> → the Studio auto-groups look-alikes. Leave kind on <b>auto</b>.</li>
      <li><b>Name each group</b> to a character (one character = one name): the group header's rename box → <b>apply</b>.</li>
      <li><b>Set the kind</b> — <code>face</code> / <code>body</code> / <code>view</code> / <code>scene</code> / <code>prop</code>. The group header's <b>set-kind</b> dropdown does a whole group in one click.</li>
      <li><b>✓ approve all</b> the keepers in each group.</li>
      <li><b>🔒 Lock references &amp; scenes</b> — this <em>freezes</em> the approved set. Lock is disabled until at least one ref is approved.</li>
    </ol>
    <div class="cal tip"><b class="h">Tip:</b> each card has a <b>📖 read text</b> button. If a sheet has a title printed on it (e.g. "ANDREA — LOCATION REFERENCE"), it pulls that into the label for you.</div>
    <div class="cal stop"><b class="h">Don't skip the lock.</b> An unlocked or half-approved reference set is the #1 cause of inconsistent comics — and the cockpit <b>gates page generation</b> until references are locked.</div>
  </div></section>

  <!-- 4 SCRIPT -->
  <section id="script"><div class="stage"><span class="n">4</span>
    <h3><span class="em">📜</span> Add your script &amp; break it into pages</h3>
    <p>Back in the cockpit, open the <b>📜 Script</b> panel and paste your story — a <b>synopsis + scene-by-scene</b> description works best (who's in it, where, what happens, any dialogue). Click <b>Save script</b>, then <span class="pill">📑 Break script into pages</span>. The Studio's AI reads the whole thing and lays it out as <b>pages → panels</b>, each with a beat (what we see), camera, location, characters, and dialogue. Give it about a minute.</p>
    <div class="where"><span class="pin">Where:</span> cockpit → <b>📜 Script</b> panel → <b>📑 Break script into pages</b>. The resulting plan shows up in <b>Live panels</b> as an empty page/panel outline.</div>
    <div class="cal warn"><b class="h">Needs a key.</b> The breakdown is an AI step the owner configures once. If the button says <b>"setup needed,"</b> ask the owner to enable it — or plan the pages by hand. Tweak the script and re-run if the breakdown is off.</div>
  </div></section>

  <!-- 5 PRODUCTION GUIDE -->
  <section id="prodguide"><div class="stage"><span class="n">5</span>
    <h3><span class="em">📋</span> The Production guide — your shot sheet</h3>
    <p>Open the <span class="pill">📋 Production guide</span> from the cockpit. For <b>every panel</b> it gives you a <b>copy-ready Flow prompt</b> and shows <b>exactly which locked references to attach</b>. This is the bridge from "plan" to "generate" — work through it panel by panel.</p>
    <div class="fig">
      <svg viewBox="0 0 600 270" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Sketch of a production-guide shot card: a copy-ready prompt textarea with polish and template buttons, the references to attach, and a done checkbox.">
        <rect x="6" y="6" width="588" height="258" rx="14" fill="#101116" stroke="#23252E"/>
        <!-- card header -->
        <text x="24" y="36" font-size="13" font-weight="800" fill="#fff">Page 1 · Panel 2</text>
        <rect x="500" y="22" width="80" height="22" rx="6" fill="#0d1f17" stroke="#1D9E75"/>
        <text x="540" y="37" text-anchor="middle" font-size="10.5" fill="#8fe3c2">☑ done</text>
        <!-- prompt box -->
        <text x="24" y="62" font-size="10.5" font-weight="700" fill="#9CA0AC">FLOW PROMPT — copy this</text>
        <rect x="24" y="68" width="556" height="78" rx="9" fill="#14151C" stroke="#2E3140"/>
        <text x="36" y="88" font-size="10.5" fill="#cdd0d8">Photoreal 3D CGI comic panel, DAZ3D style. Medium two-shot at the</text>
        <text x="36" y="104" font-size="10.5" fill="#cdd0d8">dining table: Andrea recoils, dismayed. Cinematic warm light.</text>
        <text x="36" y="120" font-size="10.5" fill="#cdd0d8">Setting: the kitchen. A speech bubble reads: "Not again."</text>
        <!-- buttons -->
        <rect x="24" y="154" width="74" height="22" rx="6" fill="#7A7FEC"/><text x="61" y="169" text-anchor="middle" font-size="10" font-weight="800" fill="#0B0C10">✨ Polish</text>
        <rect x="104" y="154" width="74" height="22" rx="6" fill="#191B24" stroke="#2E3140"/><text x="141" y="169" text-anchor="middle" font-size="10" fill="#dadce3">↺ Template</text>
        <rect x="184" y="154" width="60" height="22" rx="6" fill="#191B24" stroke="#2E3140"/><text x="214" y="169" text-anchor="middle" font-size="10" fill="#dadce3">⧉ Copy</text>
        <!-- attach refs -->
        <text x="24" y="200" font-size="10.5" font-weight="700" fill="#9CA0AC">ATTACH THESE REFERENCES IN FLOW →</text>
        <rect x="24" y="208" width="56" height="46" rx="7" fill="#14151C" stroke="#2E3140"/><text x="52" y="248" text-anchor="middle" font-size="8" fill="#9CA0AC">Andrea face</text>
        <rect x="86" y="208" width="56" height="46" rx="7" fill="#14151C" stroke="#2E3140"/><text x="114" y="248" text-anchor="middle" font-size="8" fill="#9CA0AC">Andrea body</text>
        <rect x="148" y="208" width="56" height="46" rx="7" fill="#14151C" stroke="#2E3140"/><text x="176" y="248" text-anchor="middle" font-size="8" fill="#9CA0AC">kitchen</text>
        <text x="226" y="236" font-size="10.5" fill="#6F7380">← drag these same images into Flow</text>
      </svg>
      <div class="figcap">A production-guide shot card (<code>shots.php</code>): copy-ready prompt + the exact refs to attach + a <b>done</b> checkbox to track progress.</div>
    </div>
    <ul>
      <li><b>✨ Polish</b> turns the flat template into a director-grade prompt (camera, lighting, staging, depth) and adds guard clauses that suppress junk text/props. <b>↺ Template</b> reverts. There's also a <b>✨ Polish all prompts</b> button to do the whole comic.</li>
      <li><b>Copy the prompt</b> and note <b>which refs the card lists</b> — those are the images you'll attach in Flow next.</li>
      <li>Tick each panel <b>done</b> as you finish it, so you always know where you are.</li>
    </ul>
  </div></section>

  <!-- 6 FLOW -->
  <section id="flow"><div class="stage"><span class="n">6</span>
    <h3><span class="em">🍌</span> Generate the panels in Google Flow</h3>
    <p>This is the hands-on part, done in Flow with the prompts &amp; refs from the production guide.</p>
    <div class="fig">
      <svg viewBox="0 0 600 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Sketch of the Flow prompt bar: attached reference thumbnails, a plus attach button, the prompt field, an Agent settings chip showing Nano Banana Pro x4, and a generate button.">
        <rect x="6" y="6" width="588" height="208" rx="14" fill="#101116" stroke="#23252E"/>
        <text x="24" y="34" font-size="11.5" font-weight="700" fill="#9CA0AC">Attached references (drag in once per project)</text>
        <rect x="24" y="42" width="46" height="46" rx="7" fill="#14151C" stroke="#2E3140"/>
        <rect x="76" y="42" width="46" height="46" rx="7" fill="#14151C" stroke="#2E3140"/>
        <rect x="128" y="42" width="46" height="46" rx="7" fill="#14151C" stroke="#2E3140"/>
        <!-- prompt bar -->
        <rect x="24" y="108" width="552" height="44" rx="22" fill="#14151C" stroke="#3c4052"/>
        <circle cx="48" cy="130" r="13" fill="#191B24" stroke="#2E3140"/><text x="48" y="135" text-anchor="middle" font-size="15" fill="#dadce3">+</text>
        <text x="72" y="135" font-size="11.5" fill="#6F7380">Paste the panel prompt… name the outfit for featured characters</text>
        <rect x="430" y="116" width="58" height="28" rx="14" fill="#191B24" stroke="#2E3140"/><text x="459" y="134" text-anchor="middle" font-size="11" fill="#dadce3">⚙ Agent</text>
        <rect x="494" y="116" width="76" height="28" rx="14" fill="#7A7FEC"/><text x="532" y="134" text-anchor="middle" font-size="11" font-weight="800" fill="#0B0C10">Generate</text>
        <!-- model pill -->
        <rect x="24" y="166" width="190" height="26" rx="13" fill="#0d1f17" stroke="#1D9E75"/>
        <text x="119" y="183" text-anchor="middle" font-size="11" font-weight="700" fill="#8fe3c2">🍌 Nano Banana Pro · x4</text>
        <rect x="224" y="166" width="352" height="26" rx="9" fill="#1a1407" stroke="#7a5a1f"/>
        <text x="238" y="183" font-size="10.5" fill="#f4cd8a">⚠ Agent may flip to "Nano Banana 2" / 1 image — results still strong</text>
      </svg>
      <div class="figcap">Flow's prompt bar — confirm the <b>Nano Banana Pro</b> model, attach the refs the guide listed, paste the prompt, generate.</div>
    </div>
    <p class="muted" style="font-size:12.5px;text-transform:uppercase;letter-spacing:.05em;margin:0 0 6px;font-weight:700">One-time Flow setup</p>
    <ol>
      <li>Go to <code>labs.google/fx/tools/flow</code> and <b>confirm you're on the right Google account</b> — check it every session.</li>
      <li>Create/open a project.</li>
      <li><b>Upload your references into Flow</b> — drag the same images into Flow's asset library (<code>+</code> → Upload media). Flow needs its <em>own</em> copy to attach them. <b>One time per project; can't be skipped.</b></li>
      <li>Open <b>Agent settings</b> (the sliders icon) → set <b>Nano Banana Pro</b>, <b>x4</b> variants (free), and your aspect ratio (e.g. 16:9).</li>
    </ol>
    <p class="muted" style="font-size:12.5px;text-transform:uppercase;letter-spacing:.05em;margin:14px 0 6px;font-weight:700">For each panel</p>
    <ol>
      <li><kbd>+</kbd> on the prompt bar → find the reference(s) the production guide listed → <b>Add to Prompt</b>. Re-use refs across panels; add a character's sheet when they enter the scene.</li>
      <li><b>Paste the panel's prompt</b> from the production guide.</li>
      <li><b>Name the outfit</b> for any featured character — e.g. <em>"…in a cream sweater and apron…"</em> — even though the reference already shows clothes. This keeps wardrobe consistent scene-to-scene.</li>
      <li>For dialogue, add <em>A speech bubble reads: "…"</em> — Flow letters it into the image.</li>
      <li><b>Generate</b> (~30s), pick the best variant, then tick the panel <b>done</b> in the production guide.</li>
    </ol>
  </div></section>

  <!-- 7 REVIEW -->
  <section id="review"><div class="stage"><span class="n">7</span>
    <h3><span class="em">🔄</span> Auto-sync &amp; review in Live panels</h3>
    <p>You don't have to download and re-upload by hand. The <b>Flow → Studio auto-sync</b> browser extension watches your Flow project and drops each new generation straight into this project's <b>Live panels</b>. Turn <b>Auto-sync ON</b> in its in-page panel (or hit <b>Sync now</b> to pull what's already there).</p>
    <div class="where"><span class="pin">Where:</span> finished panels appear on the cockpit's <b>Live panels</b> board, which auto-refreshes every few seconds. The owner installs the extension and gives you the bridge key + project to point it at.</div>
    <p>On the board you review each beat: dim the bad ones, shortlist contenders, and pick the winner. Use <b>✎ Adjust</b> on a panel to refine a near-miss (image-to-image) without re-rolling from scratch — it chains a new version under the original. When a page is approved, it can be assembled into the finished comic (publishing always stays a manual human step).</p>
    <div class="cal tip"><b class="h">No extension yet?</b> You can still <b>download</b> the finished panels from Flow and hand them to the owner — auto-sync just removes that step.</div>
  </div></section>

  <!-- GOTCHAS -->
  <section id="gotchas">
  <h2>Honest gotchas</h2>
  <div class="gotchas">
    <div class="gotcha"><span class="gi">🍌</span><div><h4>Flow's Agent overrides the model</h4><p>Even after you set Nano Banana Pro, the Agent sometimes generates on <b>"Nano Banana 2"</b> / a single image. The results are still strong — don't fight it. Re-check the model pill before each submit anyway.</p></div></div>
    <div class="gotcha"><span class="gi">👗</span><div><h4>Name the outfit in the prompt</h4><p>References carry face/body/hair, but a character can still revert to whatever outfit their sheet wore. For featured characters, <b>name the outfit in the prompt</b> every scene.</p></div></div>
    <div class="gotcha"><span class="gi">📎</span><div><h4>Refs must be dragged into Flow once</h4><p>Flow can only attach images that live in <em>its own</em> asset library. <b>Drag your references into Flow once per project</b> before you can add them to prompts — this step can't be skipped.</p></div></div>
    <div class="gotcha"><span class="gi">⛔</span><div><h4>▶ Queue generation isn't built</h4><p>The cockpit's Queue button is scaffolding for a future automated worker. It doesn't generate anything today. <b>Use the Production guide + Flow</b> (stages 5–6) for now.</p></div></div>
    <div class="gotcha"><span class="gi">🔁</span><div><h4>Confirm the Flow account every session</h4><p>Generating on the wrong Google account is the easiest mistake to make. There's no in-app account switcher — the account is the browser profile, so <b>check it every session</b>.</p></div></div>
    <div class="gotcha"><span class="gi">🎬</span><div><h4>The Storyboard panel pops open</h4><p>Flow's Agent sometimes opens a "Storyboard" view and shifts the layout. Just close it (the <kbd>✕</kbd>) to get the prompt bar back.</p></div></div>
  </div>
  </section>

  <!-- WHAT GOOD LOOKS LIKE -->
  <section id="good">
  <h2>What "good" looks like</h2>
  <div class="good">
    <h3>✅ A finished page passes this check</h3>
    <ul>
      <li>Same character = same face, body, and hair in <b>every</b> panel.</li>
      <li>Locations stay consistent — the kitchen is the same kitchen.</li>
      <li><b>Camera variety</b> — not every panel a flat medium shot.</li>
      <li>Expressions match the beat; dialogue is lettered where the script calls for it.</li>
      <li>No stray extras, no anachronistic props, no reference sheet rendered as an object in the scene.</li>
    </ul>
  </div>
  <p class="endnote">Questions on any step — ask the owner. Good luck. 🎬</p>
  </section>

</div><!-- /gd-main -->
</div></main>
</body></html>
