<?php
// analytics.php — Command Center SITE TRAFFIC section (GA4 + Search Console).
//
// Distinct from pulse/ (Creator Pulse = Patreon revenue/patrons). THIS is web-traffic
// analytics: sessions, channels, top pages, search, and — the point — INSIGHTS + ACTIONS.
// Claude gathers a snapshot from the owner's live GA4/Search Console during an analytics
// session and appends it to data/analytics-snapshots.json (needs the owner's Google login,
// so it's not headless). Each month adds a snapshot; this page renders the latest one and
// lists prior months. Pure renderer — no POST handlers. New standalone file (low clobber risk).
declare(strict_types=1);
require_once __DIR__ . '/inc/ops.php';
require_auth();

define('ANALYTICS_FILE', SDATA . '/analytics-snapshots.json');
$data = s_read(ANALYTICS_FILE, ['meta' => [], 'snapshots' => []]);
$snaps = $data['snapshots'] ?? [];
usort($snaps, fn($a, $b) => strcmp((string)($b['month'] ?? ''), (string)($a['month'] ?? '')));

$sel = (string)($_GET['m'] ?? '');
$snap = null;
foreach ($snaps as $s) if (($s['month'] ?? '') === $sel) { $snap = $s; break; }
if (!$snap) $snap = $snaps[0] ?? null;

function pct($v): string {
    if ($v === null || $v === '') return '<span class="mut">—</span>';
    $v = (float)$v;
    $cls = $v > 0 ? 'up' : ($v < 0 ? 'down' : 'flat');
    $arw = $v > 0 ? '▲' : ($v < 0 ? '▼' : '');
    return '<span class="' . $cls . '">' . $arw . ' ' . number_format(abs($v), 1) . '%</span>';
}
function secs($s): string { $s = (int)$s; return $s >= 60 ? intdiv($s, 60) . 'm ' . ($s % 60) . 's' : $s . 's'; }
?><!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark"><meta name="robots" content="noindex,nofollow">
<title>Site Traffic · Command Center</title>
<link rel="icon" href="assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="assets/studio.css">
<style>
.an-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:14px;margin:12px 0 8px}
.card2{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:16px}
.card2 h3{margin:0 0 8px;font-size:15px;display:flex;align-items:center;gap:8px}
.metric{font-size:30px;font-weight:800;margin:2px 0}
.metricrow{display:flex;gap:18px;flex-wrap:wrap;margin-top:8px}
.metricrow div{font-size:12px;color:var(--muted)}
.metricrow b{display:block;color:var(--text);font-size:15px;font-weight:700}
.up{color:#1D9E75;font-weight:700}.down{color:#D9534F;font-weight:700}.flat{color:var(--muted)}
.mut{color:var(--muted)}
.badge-warn{display:inline-block;font-size:11px;font-weight:700;color:#EF9F27;border:1px solid #EF9F27;border-radius:999px;padding:1px 8px}
.badge-ok{display:inline-block;font-size:11px;font-weight:700;color:#1D9E75;border:1px solid #1D9E75;border-radius:999px;padding:1px 8px}
table.t{width:100%;border-collapse:collapse;font-size:13px;margin-top:6px}
table.t th,table.t td{text-align:left;padding:5px 8px;border-bottom:1px solid var(--border)}
table.t th{color:var(--muted);font-weight:600}
table.t td.n,table.t th.n{text-align:right}
.cc-h{margin:26px 0 6px;font-size:13px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted)}
.ins{border:1px solid var(--border);border-radius:12px;background:var(--surface);padding:0;overflow:hidden;margin-top:8px}
.ins .row{display:flex;gap:14px;padding:14px 16px;border-bottom:1px solid var(--border)}
.ins .row:last-child{border-bottom:0}
.ins .rank{flex:none;width:30px;height:30px;border-radius:50%;background:var(--accent);color:#fff;font-weight:800;display:flex;align-items:center;justify-content:center;font-size:14px}
.ins h4{margin:0 0 4px;font-size:15px}
.ins .detail{color:var(--muted);font-size:13px;margin:0 0 6px;line-height:1.5}
.ins .act{font-size:13px;line-height:1.5}
.ins .act b{color:#1D9E75}
.gap{display:flex;gap:8px;align-items:flex-start;font-size:13px;color:var(--text);padding:6px 0}
.gap::before{content:"⚠";color:#EF9F27;flex:none}
.goal{background:linear-gradient(135deg,rgba(122,127,236,.14),rgba(29,158,117,.07));border:1px solid #3a3470;border-radius:12px;padding:14px 16px;font-size:14px;line-height:1.6;margin-top:8px}
.msel{background:var(--surface);color:var(--text);border:1px solid var(--border);border-radius:8px;padding:5px 10px;font-size:13px}
.freshnote{font-size:12px;color:var(--muted);margin-top:4px}
</style><!-- the one bar across every system: ⌂ back to the hub, and a menu of everything else. Source: /hub/nav.js -->
<script src="https://3dmusclecomics.com/hub/nav.js"></script>
</head><body>
<header class="topbar">
  <div class="brand"><a href="cc.php" style="color:inherit;text-decoration:none"><span class="dot"></span> ⌘ Command Center</a></div>
  <a class="ghost" href="cc.php">Home</a>
  <a class="ghost" href="ops.php">📋 Ops Board</a>
  <a class="ghost" href="index.php">🎬 Pipeline</a>
  <a class="ghost" href="pulse/">📈 Patron $</a>
  <a class="ghost" href="analytics.php" style="color:var(--text);font-weight:700">📊 Traffic</a>
  <span class="spacer"></span>
  <span class="ghost"><?= h(current_studio_user()) ?></span>
  <a class="ghost" href="login.php?do=logout">Log out</a>
</header>
<main class="wrap">
<?php if (!$snap): ?>
  <div class="pagehead"><h1>Site Traffic</h1></div>
  <p class="muted">No analytics gathered yet. Claude appends a snapshot each analytics session (GA4 + Search Console).</p>
<?php else: ?>
  <div class="pagehead" style="display:flex;align-items:center;gap:12px;flex-wrap:wrap">
    <h1>Site Traffic</h1>
    <?php if (count($snaps) > 1): ?>
    <select class="msel" onchange="location.href='analytics.php?m='+this.value">
      <?php foreach ($snaps as $s): ?><option value="<?= h($s['month']) ?>"<?= ($s['month']===$snap['month'])?' selected':'' ?>><?= h($s['label'] ?? $s['month']) ?></option><?php endforeach; ?>
    </select>
    <?php else: ?><span class="muted"><?= h($snap['label'] ?? $snap['month']) ?></span><?php endif; ?>
    <span class="spacer"></span>
    <span class="freshnote">Gathered <?= h($snap['capturedAt'] ?? '') ?> · <?= h($snap['source'] ?? '') ?> · <?= h($snap['compare'] ?? '') ?></span>
  </div>

  <!-- property cards -->
  <div class="an-grid">
    <?php foreach (($snap['properties'] ?? []) as $p): ?>
    <div class="card2">
      <h3><?= h($p['name']) ?>
        <?php if (($p['keyEvents'] ?? 1) == 0): ?><span class="badge-warn" title="No conversions tracked in GA4">no conv. tracking</span><?php else: ?><span class="badge-ok">conv. tracked</span><?php endif; ?>
      </h3>
      <div class="metric"><?= number_format((int)($p['sessions'] ?? 0)) ?></div>
      <div><?= pct($p['sessionsChangePct'] ?? null) ?> <span class="mut">sessions vs. prior</span></div>
      <div class="metricrow">
        <div>Engagement rate<b><?= h(number_format((float)($p['engagementRatePct'] ?? 0), 1)) ?>%</b></div>
        <div>Avg. time<b><?= secs($p['avgEngagementSec'] ?? 0) ?></b></div>
        <div>Events<b><?= number_format((int)($p['eventCount'] ?? 0)) ?></b></div>
      </div>
      <?php if (!empty($p['note'])): ?><div class="mut" style="font-size:12px;margin-top:10px;line-height:1.5"><?= h($p['note']) ?></div><?php endif; ?>
    </div>
    <?php endforeach; ?>
  </div>

  <!-- INSIGHTS & ACTIONS -->
  <div class="cc-h">Insights &amp; actions — what to do to grow</div>
  <div class="ins">
    <?php foreach (($snap['insights'] ?? []) as $ins): ?>
    <div class="row">
      <div class="rank"><?= (int)($ins['rank'] ?? 0) ?></div>
      <div>
        <h4><?= h($ins['title'] ?? '') ?></h4>
        <p class="detail"><?= h($ins['detail'] ?? '') ?></p>
        <div class="act"><b>Do:</b> <?= h($ins['action'] ?? '') ?></div>
      </div>
    </div>
    <?php endforeach; ?>
  </div>
  <?php if (!empty($snap['goalCheck'])): ?><div class="goal"><b>Goal check.</b> <?= h($snap['goalCheck']) ?></div><?php endif; ?>

  <!-- gaps -->
  <?php if (!empty($snap['gaps'])): ?>
  <div class="cc-h">Gaps to fix</div>
  <div class="card2">
    <?php foreach ($snap['gaps'] as $g): ?><div class="gap"><span><?= h($g) ?></span></div><?php endforeach; ?>
  </div>
  <?php endif; ?>

  <!-- detail tables -->
  <div class="cc-h">Detail by property</div>
  <div class="an-grid" style="grid-template-columns:repeat(auto-fill,minmax(320px,1fr))">
    <?php foreach (($snap['properties'] ?? []) as $p): ?>
    <div class="card2">
      <h3><?= h($p['name']) ?></h3>
      <?php if (!empty($p['channels'])): ?>
      <div class="mut" style="font-size:12px;margin-top:4px">Traffic by channel</div>
      <table class="t"><tr><th>Channel</th><th class="n">Sessions</th><th class="n">Share</th><th class="n">vs prior</th></tr>
        <?php foreach ($p['channels'] as $c): ?>
        <tr><td><?= h($c['name']) ?></td>
          <td class="n"><?= $c['sessions']!==null ? number_format((int)$c['sessions']) : '<span class="mut">—</span>' ?></td>
          <td class="n"><?= h(number_format((float)($c['sharePct'] ?? 0), 1)) ?>%</td>
          <td class="n"><?= pct($c['changePct'] ?? null) ?></td></tr>
        <?php endforeach; ?>
      </table>
      <?php endif; ?>
      <?php if (!empty($p['topPages'])): ?>
      <div class="mut" style="font-size:12px;margin-top:12px">Top pages (views)</div>
      <table class="t"><tr><th>Page</th><th class="n">Views</th><th class="n">vs prior</th></tr>
        <?php foreach ($p['topPages'] as $pg): ?>
        <tr><td><?= h($pg['path']) ?></td><td class="n"><?= number_format((int)($pg['views'] ?? 0)) ?></td><td class="n"><?= pct($pg['changePct'] ?? null) ?></td></tr>
        <?php endforeach; ?>
      </table>
      <?php endif; ?>
      <?php if (!empty($p['search'])): $sr = $p['search']; ?>
      <div class="mut" style="font-size:12px;margin-top:12px">Search Console (trailing 3 mo)</div>
      <div class="metricrow" style="margin-top:4px">
        <div>Clicks<b><?= number_format((int)($sr['clicks'] ?? 0)) ?></b></div>
        <div>CTR<b><?= h($sr['ctrPct'] ?? 0) ?>%</b></div>
        <div>Avg pos<b><?= h($sr['avgPosition'] ?? 0) ?></b></div>
        <div>Branded<b><?= h($sr['brandedSharePct'] ?? 0) ?>%</b></div>
      </div>
      <?php if (!empty($sr['topNonBranded'])): ?>
      <div class="mut" style="font-size:12px;margin-top:8px">Non-branded upside</div>
      <table class="t"><tr><th>Query</th><th class="n">Clicks</th><th class="n">Impr.</th></tr>
        <?php foreach ($sr['topNonBranded'] as $q): ?><tr><td><?= h($q['q']) ?></td><td class="n"><?= number_format((int)$q['clicks']) ?></td><td class="n"><?= number_format((int)$q['impressions']) ?></td></tr><?php endforeach; ?>
      </table>
      <?php endif; ?>
      <?php endif; ?>
    </div>
    <?php endforeach; ?>
  </div>

  <p class="freshnote" style="margin-top:24px">This section is refreshed by Claude during an analytics session (it needs the owner's live Google login, so it isn't automatic). Ask Claude to "refresh site traffic" to append the next month.</p>
<?php endif; ?>
</main></body></html>
