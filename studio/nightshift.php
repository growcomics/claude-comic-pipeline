<?php
// nightshift.php — COMMAND CENTER: Night Shift view.
// Read-only renderer of the autonomous overnight worker's shift history.
// Data source: studio/data/nightshift.json (the night-shift worker appends one
// shift object per night; newest first). No POST handlers, no writes.
declare(strict_types=1);
require_once __DIR__ . '/inc/ops.php';
require_auth();

// Defensive guards — no-ops if the studio already defines these (it does), but
// prevent a fatal if a helper name ever differs.
if (!function_exists('h')) { function h($s){ return htmlspecialchars((string)$s, ENT_QUOTES); } }
if (!function_exists('current_studio_user')) { function current_studio_user(){ return ''; } }
if (!defined('SDATA')) { define('SDATA', __DIR__ . '/data'); }

$NS = json_decode((string)@file_get_contents(SDATA . '/nightshift.json'), true) ?: [];
$meta   = $NS['meta']   ?? ['what' => '', 'cadence' => '', 'guardrails' => [], 'generated' => ''];
$stats  = $NS['stats']  ?? [];
$shifts = $NS['shifts'] ?? [];

function badge_(string $t, string $c): string {
    return '<span class="badge" style="--c:' . h($c) . '">' . h($t) . '</span>';
}
function comic_(array $c): string {
    $tiers = $c['tierByPage'] ?? []; $gp = array_flip($c['growthPages'] ?? []);
    $mx = $tiers ? max($tiers) : 1; $bars = '';
    foreach ($tiers as $i => $t) {
        $page = $i + 1; $isg = isset($gp[$page]);
        $col = $isg ? 'var(--accent)' : 'var(--muted2)';
        $hp = (int)(18 + ($t / $mx) * 82);
        $bars .= '<div class="bar" style="height:' . $hp . '%;background:' . $col . '" title="P' . $page . ' · tier ' . (int)$t . ($isg ? ' · growth' : '') . '"></div>';
    }
    $gates = badge_('Gate A ✓ ' . ($c['gateA'] ?? ''), 'var(--teal)') . badge_('Gate B ✓ clean', 'var(--teal)');
    $ng = count($c['growthPages'] ?? []);
    return '<div class="comic"><div class="comic-h"><span class="t">🔥 ' . h($c['series'] ?? '') . ' — Ch.' . h($c['chapter'] ?? '') . '</span>'
        . '<span class="badge" style="--c:var(--blue)">tier ' . (int)($c['tierStart'] ?? 0) . ' → ' . (int)($c['tierEnd'] ?? 0) . '</span>'
        . '<span class="spacer"></span><div class="gates">' . $gates . '</div></div>'
        . '<div class="gmeta"><div class="ring" style="--p:' . (int)($c['growthPct'] ?? 0) . '"><div class="in">' . (int)($c['growthPct'] ?? 0) . '%</div></div>'
        . '<div><div style="font-weight:700">' . $ng . '/' . (int)($c['pages'] ?? 0) . ' growth pages</div>'
        . '<div style="color:var(--muted);font-size:12.5px">transformation-chapter target ≥60% · camera mean ' . h($c['cameraMean'] ?? '') . ' (≤2.5)</div></div></div>'
        . '<div class="ladder">' . $bars . '</div>'
        . '<div class="ladder-legend"><span><i class="dotk" style="background:var(--accent)"></i>growth page (body actively changing)</span>'
        . '<span><i class="dotk" style="background:var(--muted2)"></i>story / setup page</span>'
        . '<span>bar height = muscle tier, page 1 → 20 left to right</span></div></div>';
}
function shift_(array $s): string {
    $st = $s['status'] ?? 'done';
    $sc = $st === 'done' ? 'var(--teal)' : 'var(--accent)';
    $runs = '';
    foreach (($s['runs'] ?? []) as $r) {
        $ic = ($r['status'] ?? '') === 'done' ? '✅' : '⛔';
        $cls = ($r['status'] ?? '') === 'blocked' ? 'run blocked' : 'run';
        $runs .= '<div class="' . $cls . '"><div class="ic">' . $ic . '</div><div><div class="rt">' . h($r['title'] ?? '') . '</div><div class="rd">' . h($r['detail'] ?? '') . '</div></div></div>';
    }
    $comic = !empty($s['comic']) ? comic_($s['comic']) : '';
    $blocks = '';
    if (!empty($s['blocks'])) {
        $items = '';
        foreach ($s['blocks'] as $b) {
            $items .= '<div class="block"><div>⛔</div><div><div class="bt">' . h($b['title'] ?? '') . '</div><div class="bf">Fix — ' . h($b['fix'] ?? '') . '</div></div></div>';
        }
        $blocks = '<div class="blocks">' . $items . '</div>';
    }
    $links = '';
    if (!empty($s['links'])) {
        $items = '';
        foreach ($s['links'] as $l) {
            $items .= '<span class="link"><b>' . h($l['label'] ?? '') . '</b> · ' . h($l['note'] ?? '') . '</span>';
        }
        $links = '<div class="links">' . $items . '</div>';
    }
    return '<div class="shift ' . h($st) . '"><div class="node"></div><div class="shead">'
        . '<span class="sdate">' . h($s['date'] ?? '') . '</span><span class="swin">' . h($s['window'] ?? '') . '</span>'
        . badge_($s['statusLabel'] ?? '', $sc) . '</div>'
        . '<div class="smission">' . h($s['mission'] ?? '') . ' — ' . h($s['charter'] ?? '') . '</div>'
        . '<div class="headline">' . h($s['headline'] ?? '') . '</div>'
        . $comic . '<div class="runs">' . $runs . '</div>' . $blocks . $links . '</div>';
}
?><!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark"><meta name="robots" content="noindex,nofollow">
<title>Night Shift · Command Center</title>
<link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="assets/studio.css">
<style>
.sub{color:var(--muted);font-size:13.5px;max-width:680px;margin:8px 0 0}
.eyebrow{font-size:12px;text-transform:uppercase;letter-spacing:.09em;color:var(--muted);margin:26px 0 10px}
.chips{display:flex;flex-wrap:wrap;gap:7px;margin-top:6px}
.chip{font-size:12px;color:var(--muted);border:1px solid var(--border2);border-radius:999px;padding:4px 10px;background:var(--bg2)}
.stats{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:12px;margin:8px 0 4px}
.stat{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:14px 16px}
.stat .v{font-size:26px;font-weight:800}.stat .l{color:var(--muted);font-size:12px;margin-top:2px}.stat .s{color:var(--muted2);font-size:11.5px;margin-top:3px}
.tl{position:relative;margin-top:8px;padding-left:26px}
.tl:before{content:"";position:absolute;left:7px;top:6px;bottom:6px;width:2px;background:var(--border2)}
.shift{position:relative;margin-bottom:22px}
.shift>.node{position:absolute;left:-26px;top:16px;width:16px;height:16px;border-radius:50%;border:3px solid var(--bg);background:var(--accent)}
.shift.done>.node{background:var(--teal)}
.shead{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:4px}
.sdate{font-weight:800;font-size:16px}.swin{color:var(--muted2);font-size:12.5px}.smission{color:var(--muted);font-size:13px}
.badge{display:inline-flex;align-items:center;gap:6px;font-size:11.5px;font-weight:700;padding:3px 10px;border-radius:999px;color:var(--c);background:color-mix(in srgb,var(--c) 16%,transparent)}
.headline{color:var(--text);font-size:14.5px;margin:6px 0 12px;opacity:.95}
.runs{display:flex;flex-direction:column;border:1px solid var(--border);border-radius:10px;overflow:hidden}
.run{display:grid;grid-template-columns:26px 1fr;gap:10px;padding:11px 13px;background:var(--surface);align-items:start}
.run+.run{border-top:1px solid var(--border)}
.run .ic{font-size:15px;line-height:1.5}.run .rt{font-weight:650;font-size:13.5px}.run .rd{color:var(--muted);font-size:12.5px;margin-top:2px}
.run.blocked .rt{color:#F0B24B}
.blocks{margin-top:12px;display:flex;flex-direction:column;gap:8px}
.block{display:flex;gap:10px;align-items:flex-start;border:1px solid color-mix(in srgb,var(--red) 40%,var(--border));background:color-mix(in srgb,var(--red) 8%,transparent);border-radius:10px;padding:10px 12px}
.block .bt{font-weight:700;font-size:13px;color:#F1948A}.block .bf{color:var(--muted);font-size:12.5px;margin-top:2px}
.links{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}
.link{font-size:12px;color:var(--muted);border:1px solid var(--border2);border-radius:8px;padding:5px 10px;background:var(--bg2)}.link b{color:var(--text);font-weight:650}
.comic{border:1px solid var(--border2);border-radius:12px;padding:14px 16px;margin:12px 0;background:linear-gradient(180deg,var(--surface2),var(--surface))}
.comic-h{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:10px}.comic-h .t{font-weight:800}
.gates{display:flex;gap:7px}.spacer{flex:1}
.ladder{display:flex;align-items:flex-end;gap:3px;height:72px;margin:8px 0 4px}
.bar{flex:1;border-radius:3px 3px 0 0;min-width:6px}
.ladder-legend{display:flex;gap:16px;color:var(--muted2);font-size:11px;margin-top:6px;flex-wrap:wrap}
.dotk{display:inline-block;width:9px;height:9px;border-radius:2px;vertical-align:middle;margin-right:5px}
.ring{--p:0;width:64px;height:64px;border-radius:50%;background:conic-gradient(var(--accent) calc(var(--p)*1%),var(--border2) 0);display:grid;place-items:center;flex:none}
.ring .in{width:48px;height:48px;border-radius:50%;background:var(--surface);display:grid;place-items:center;font-weight:800;font-size:15px}
.gmeta{display:flex;gap:18px;align-items:center;flex-wrap:wrap}
</style></head><body>
<header class="topbar">
  <div class="brand"><span class="dot"></span> ⌘ Command Center</div>
  <a class="ghost" href="cc.php">Home</a>
  <a class="ghost" href="ops.php">📋 Ops Board</a>
  <a class="ghost" href="index.php">🎬 Pipeline</a>
  <a class="ghost" href="pulse/">📈 Analytics</a>
  <a class="ghost" href="analytics.php">📊 Traffic</a>
  <a class="ghost" href="ideas.php">💡 Idea Vault</a>
  <a class="ghost" href="nightshift.php" style="color:var(--text);font-weight:700">🌙 Night Shift</a>
  <span class="spacer"></span>
  <span class="ghost"><?= h(current_studio_user()) ?></span>
  <a class="ghost" href="login.php?do=logout">Log out</a>
</header>
<main class="wrap">
  <div class="pagehead"><h1>🌙 Night Shift</h1></div>
  <p class="sub"><?= h($meta['what']) ?></p>

  <div class="stats">
    <?php foreach ($stats as $x): ?>
      <div class="stat"><div class="v"><?= h($x['value']) ?></div><div class="l"><?= h($x['label']) ?></div><div class="s"><?= h($x['sub']) ?></div></div>
    <?php endforeach; ?>
  </div>

  <div class="card">
    <div style="font-weight:700;margin-bottom:4px">How it works</div>
    <div style="color:var(--muted);font-size:13px"><?= h($meta['cadence']) ?></div>
    <div class="eyebrow" style="margin:14px 0 6px">Guardrails</div>
    <div class="chips"><?php foreach (($meta['guardrails'] ?? []) as $g): ?><span class="chip"><?= h($g) ?></span><?php endforeach; ?></div>
  </div>

  <div class="eyebrow">Shift history — newest first</div>
  <div class="tl"><?php foreach ($shifts as $s) echo shift_($s); ?></div>

  <div style="color:var(--muted2);font-size:11.5px;margin-top:24px">Generated <?= h($meta['generated']) ?> from night-shift/reports + state.json.</div>
</main>
</body></html>
