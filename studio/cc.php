<?php
// cc.php — COMMAND CENTER landing: the front door for running all the properties.
//
// Four sections — Ops Board (the Monday.com replacement, ops.php), the Comic Pipeline
// (the existing studio pages, untouched), Patron Analytics (pulse/ — Creator Pulse,
// the creatormetrics.io clone; static app auth-gated by pulse/index.php), and per-site
// overviews (site.php?s=<key>) — plus grayed tiles where the remaining v2 sections
// (posting calendar / SOP library) will slot in.
// Open-task counts are computed in one PHP pass over data/ops-tasks.json;
// a task with no sites[] counts as "cross-property". Pure renderer: no POST handlers.
declare(strict_types=1);
require_once __DIR__ . '/inc/ops.php';
require_auth();

$tasks = ops_load()['tasks'];
$sites = ops_sites();

$openN = 0; $critN = 0; $aiNowN = 0; $crossN = 0;
$bySite = array_fill_keys(array_keys($sites), 0);
foreach ($tasks as $t) {
    if (!ops_open($t)) continue;
    $openN++;
    if (($t['priority'] ?? '') === 'critical') $critN++;
    if (($t['aiTag'] ?? '') === 'ai-now') $aiNowN++;
    $ts = (array)($t['sites'] ?? []);
    if (!$ts) $crossN++;
    foreach ($ts as $k) if (isset($bySite[$k])) $bySite[$k]++;
}
$projN = count(projects_all());

// site-traffic headline (latest analytics snapshot) — Command Center Traffic section
$anSnaps = s_read(SDATA . '/analytics-snapshots.json', ['snapshots' => []])['snapshots'] ?? [];
$anSnap = null; foreach ($anSnaps as $s) if (!$anSnap || strcmp((string)($s['month'] ?? ''), (string)($anSnap['month'] ?? '')) > 0) $anSnap = $s;
$anSess = 0; $anMonth = '';
if ($anSnap) { $anMonth = (string)($anSnap['label'] ?? ''); foreach (($anSnap['properties'] ?? []) as $pp) $anSess += (int)($pp['sessions'] ?? 0); }
?><!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark"><meta name="robots" content="noindex,nofollow">
<title>Command Center</title>
<link rel="icon" href="assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="assets/studio.css">
<style>
.cc-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:14px;margin:14px 0 26px}
.cc-tile{display:block;background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:16px;color:var(--text);text-decoration:none;position:relative}
.cc-tile:hover{border-color:var(--accent)}
.cc-tile h3{margin:0 0 6px;font-size:15px;display:flex;align-items:center;gap:8px}
.cc-tile .big{font-size:26px;font-weight:800;margin:4px 0}
.cc-tile .sub{color:var(--muted);font-size:12px;line-height:1.6}
.cc-tile.soon{opacity:.45;pointer-events:none}
.cc-tile.soon .tag{position:absolute;top:10px;right:12px;font-size:10px;color:var(--muted);border:1px solid var(--border);border-radius:999px;padding:2px 8px}
.sdot{width:10px;height:10px;border-radius:50%;flex:none;background:var(--c)}
.cc-h{margin:26px 0 4px;font-size:13px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted)}
.cc-crit{color:#D9534F;font-weight:700}
</style></head><body>
<header class="topbar">
  <div class="brand"><span class="dot"></span> ⌘ Command Center</div>
  <a class="ghost" href="cc.php" style="color:var(--text);font-weight:700">Home</a>
  <a class="ghost" href="ops.php">📋 Ops Board</a>
  <a class="ghost" href="index.php">🎬 Pipeline</a>
  <a class="ghost" href="pulse/">📈 Analytics</a>
  <a class="ghost" href="analytics.php">📊 Traffic</a>
  <span class="spacer"></span>
  <span class="ghost"><?= h(current_studio_user()) ?></span>
  <a class="ghost" href="login.php?do=logout">Log out</a>
</header>
<main class="wrap">
  <div class="pagehead"><h1>Command Center</h1></div>

  <div class="cc-h">Work</div>
  <div class="cc-grid">
    <a class="cc-tile" href="ops.php">
      <h3>📋 Ops Board</h3>
      <div class="big"><?= $openN ?></div>
      <div class="sub">open tasks<?= $critN ? ' · <span class="cc-crit">' . $critN . ' critical</span>' : '' ?><?= $aiNowN ? ' · 🤖 ' . $aiNowN . ' AI-ready' : '' ?><br>the Monday.com replacement — full backlog, filters, AI triage</div>
    </a>
    <a class="cc-tile" href="index.php">
      <h3>🎬 Comic Pipeline</h3>
      <div class="big"><?= $projN ?></div>
      <div class="sub">studio projects<br>creator · references · review · GrowGetter generator · importer</div>
    </a>
    <a class="cc-tile" href="pulse/">
      <h3>📈 Patron Analytics</h3>
      <div class="big">4</div>
      <div class="sub">Patreon accounts · Creator Pulse<br>patrons · earnings · retention · cohorts, per account</div>
    </a>
    <a class="cc-tile" href="analytics.php">
      <h3>📊 Site Traffic</h3>
      <div class="big"><?= $anSess ? number_format($anSess) : '—' ?></div>
      <div class="sub"><?= $anMonth ? h($anMonth) . ' sessions · GA4 + Search Console' : 'GA4 web traffic' ?><br>insights + actions to grow the sites</div>
    </a>
    <a class="cc-tile" href="ops.php#view=open&ai=ai-now">
      <h3>🤖 AI queue</h3>
      <div class="big"><?= $aiNowN ?></div>
      <div class="sub">tasks tagged “AI can do now” — triage fills this, batches empty it</div>
    </a>
  </div>

  <div class="cc-h">Sites</div>
  <div class="cc-grid">
    <?php foreach ($sites as $k => $s): if (empty($s['active'])) continue; ?>
    <a class="cc-tile" href="site.php?s=<?= h(urlencode($k)) ?>">
      <h3><span class="sdot" style="--c:<?= h($s['color'] ?? '#6F7380') ?>"></span> <?= h($s['name']) ?></h3>
      <div class="big"><?= (int)$bySite[$k] ?></div>
      <div class="sub">open tasks · <?= h($s['type'] ?? '') ?></div>
    </a>
    <?php endforeach; ?>
    <a class="cc-tile" href="ops.php">
      <h3><span class="sdot" style="--c:#9aa0b4"></span> Cross-property</h3>
      <div class="big"><?= $crossN ?></div>
      <div class="sub">open tasks not tied to one site</div>
    </a>
  </div>

  <div class="cc-h">Coming next</div>
  <div class="cc-grid">
    <div class="cc-tile soon"><span class="tag">soon</span><h3>🗓 Posting calendar</h3><div class="sub">cross-property content schedule</div></div>
    <div class="cc-tile soon"><span class="tag">soon</span><h3>📚 SOP library</h3><div class="sub">every guide and SOP, indexed</div></div>
  </div>
</main></body></html>
