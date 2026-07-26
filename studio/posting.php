<?php
// posting.php — 🗓 Posting board: cross-property content queue with per-platform
// "locked & loaded" status. Lanes: Fan Art Friday (weekly, Patreon/DA-first),
// Monthly comic (per property), Side content. The board schedules, prepares and
// tracks — a HUMAN presses post on the actual platforms.
// Auth: studio session (same logins as everything else) OR bridge key (headless,
// same data/bridge.json key bridge.php uses). State: data/posting.json.
declare(strict_types=1);
require_once __DIR__ . '/inc/boot.php';

define('PO_FILE', SDATA . '/posting.json');

$PLATFORMS = array('site' => 'Site', 'patreon' => 'Patreon', 'deviantart' => 'DeviantArt', 'twitter' => 'X', 'instagram' => 'IG');
$PSTATES = array('todo', 'scheduled', 'posted', 'na');
$LANES = array('faf' => 'Fan Art Friday', 'comic' => 'Monthly comic', 'side' => 'Side content');
$ISTATES = array('draft', 'ready', 'posted', 'skipped');

$SITES = s_read(SDATA . '/cc-sites.json', array());
$PROPS = array();
// giantessgirl removed 2026-07-25 — property transferred away, not ours to schedule
foreach (array('growgetter', 'maxxmuscle', 'bloombeauty') as $pk) {
    if (isset($SITES[$pk])) $PROPS[$pk] = array('name' => (string)$SITES[$pk]['name'], 'color' => (string)$SITES[$pk]['color']);
}

function po_bridge_ok(): bool {
    $cfg = s_read(SDATA . '/bridge.json', array());
    $key = (string)(isset($cfg['key']) ? $cfg['key'] : '');
    $given = (string)(isset($_POST['key']) ? $_POST['key'] : (isset($_GET['key']) ? $_GET['key'] : (isset($_SERVER['HTTP_X_BRIDGE_KEY']) ? $_SERVER['HTTP_X_BRIDGE_KEY'] : '')));
    return $key !== '' && strlen($given) >= 16 && hash_equals($key, $given);
}
$keyAuthed = po_bridge_ok();
if (!$keyAuthed) require_auth();

function po_locked(array $it): bool {
    if (($it['status'] ?? '') !== 'ready') return false;
    $armed = 0;
    foreach ($it['platforms'] as $st) {
        if ($st === 'todo') return false;
        if ($st === 'scheduled' || $st === 'posted') $armed++;
    }
    return $armed > 0;
}

// ---------------- API (form POSTs; redirect back when 'back' given) ----------
$action = isset($_POST['action']) ? (string)$_POST['action'] : '';
if ($action !== '') {
    if (!$keyAuthed) csrf_check();
    $db = s_read(PO_FILE, array('seq' => 0, 'items' => array()));
    $idx = -1;
    $id = isset($_POST['id']) ? (string)$_POST['id'] : '';
    foreach ($db['items'] as $i => $it) { if (($it['id'] ?? '') === $id) { $idx = $i; break; } }
    $err = '';

    if ($action === 'add' || ($action === 'update' && $idx >= 0)) {
        global $PROPS, $LANES, $ISTATES, $PLATFORMS;
        $prop = isset($_POST['property']) && isset($PROPS[$_POST['property']]) ? (string)$_POST['property'] : 'growgetter';
        $lane = isset($_POST['lane']) && isset($LANES[$_POST['lane']]) ? (string)$_POST['lane'] : 'side';
        $slot = substr(preg_replace('/[^0-9\-]/', '', (string)($_POST['slot'] ?? '')), 0, 10);
        $assets = array_values(array_filter(array_map('trim', explode("\n", (string)($_POST['assets'] ?? '')))));
        $fields = array(
            'property' => $prop, 'lane' => $lane, 'slot' => $slot,
            'title' => trim((string)($_POST['title'] ?? '')),
            'owner' => trim((string)($_POST['owner'] ?? '')),
            'caption' => trim((string)($_POST['caption'] ?? '')),
            'notes' => trim((string)($_POST['notes'] ?? '')),
            'assets' => $assets,
            'status' => in_array(($_POST['status'] ?? 'draft'), $ISTATES, true) ? (string)$_POST['status'] : 'draft',
            'updatedAt' => gmdate('c'),
        );
        if ($fields['title'] === '') {
            $err = 'Title required.';
        } elseif ($action === 'add') {
            $plats = array();
            foreach ($PLATFORMS as $k => $l) $plats[$k] = 'todo';
            $db['seq'] = (int)($db['seq'] ?? 0) + 1;
            $db['items'][] = array_merge(array('id' => 'po_' . nid(), 'platforms' => $plats, 'createdAt' => gmdate('c')), $fields);
        } else {
            $db['items'][$idx] = array_merge($db['items'][$idx], $fields);
        }
    } elseif ($action === 'plat' && $idx >= 0) {
        $pl = isset($_POST['plat']) ? (string)$_POST['plat'] : '';
        $st = isset($_POST['state']) ? (string)$_POST['state'] : '';
        if (isset($db['items'][$idx]['platforms'][$pl]) && in_array($st, $PSTATES, true)) {
            $db['items'][$idx]['platforms'][$pl] = $st;
            $db['items'][$idx]['updatedAt'] = gmdate('c');
        } else $err = 'Bad platform/state.';
    } elseif ($action === 'del' && $idx >= 0) {
        array_splice($db['items'], $idx, 1);
    } elseif ($idx < 0) {
        $err = 'No such item.';
    }

    if ($err === '') s_write(PO_FILE, $db);
    $back = isset($_POST['back']) ? (string)$_POST['back'] : '';
    if ($back !== '' && preg_match('/^posting\.php/', $back)) {
        header('Location: ' . $back . (strpos($back, '?') === false ? '?' : '&') . ($err !== '' ? 'err=' . urlencode($err) : 'ok=1'));
        exit;
    }
    header('Content-Type: application/json');
    echo json_encode($err === '' ? array('ok' => true) : array('ok' => false, 'error' => $err));
    exit;
}

// ---------------- render prep ------------------------------------------------
$db = s_read(PO_FILE, array('seq' => 0, 'items' => array()));
$items = $db['items'];
usort($items, function ($a, $b) { return strcmp((string)($a['slot'] ?? ''), (string)($b['slot'] ?? '')); });

$fridays = array();
$t = time();
for ($d = 0; $d < 28 && count($fridays) < 4; $d++) {
    $ts = $t + $d * 86400;
    if (gmdate('N', $ts) === '5') $fridays[] = gmdate('Y-m-d', $ts);
}
$months = array(gmdate('Y-m'), gmdate('Y-m', strtotime('first day of next month')));

$live = array(); $archive = array();
foreach ($items as $it) {
    if (in_array($it['status'], array('posted', 'skipped'), true)) $archive[] = $it; else $live[] = $it;
}
$archive = array_slice(array_reverse($archive), 0, 20);

function po_pick(array $live, string $lane, string $slotPrefix, string $prop = ''): array {
    $out = array();
    foreach ($live as $it) {
        if ($it['lane'] !== $lane) continue;
        if ($slotPrefix !== '' && strpos((string)$it['slot'], $slotPrefix) !== 0) continue;
        if ($prop !== '' && $it['property'] !== $prop) continue;
        $out[] = $it;
    }
    return $out;
}

$newOpen = isset($_GET['new']);
$pre = array(
    'lane' => isset($_GET['lane']) && isset($LANES[$_GET['lane']]) ? (string)$_GET['lane'] : 'side',
    'slot' => isset($_GET['slot']) ? substr(preg_replace('/[^0-9\-]/', '', (string)$_GET['slot']), 0, 10) : '',
    'property' => isset($_GET['property']) && isset($PROPS[$_GET['property']]) ? (string)$_GET['property'] : 'growgetter',
);
$AUTHJS = $keyAuthed
    ? json_encode(array('key' => (string)(isset($_GET['key']) ? $_GET['key'] : '')))
    : json_encode(array('csrf' => csrf()));

function po_card(array $it, array $PROPS, array $PLATFORMS, array $LANES, array $ISTATES, bool $keyAuthed): void {
    $pc = isset($PROPS[$it['property']]) ? $PROPS[$it['property']]['color'] : '#888';
    $pn = isset($PROPS[$it['property']]) ? $PROPS[$it['property']]['name'] : $it['property'];
    $locked = po_locked($it);
    echo '<div class="po-card' . ($locked ? ' locked' : '') . '" data-id="' . h($it['id']) . '">';
    echo '<div class="po-head"><span class="dot" style="background:' . h($pc) . '"></span>';
    echo '<strong>' . h($it['title']) . '</strong>';
    echo '<span class="po-slot">' . h($it['slot'] !== '' ? $it['slot'] : 'no date') . '</span>';
    echo '<span class="po-st po-st-' . h($it['status']) . '">' . h($it['status']) . '</span>';
    if ($locked) echo '<span class="po-lock">🔒 locked &amp; loaded</span>';
    if ($it['owner'] !== '') echo '<span class="po-owner">🎯 ' . h($it['owner']) . '</span>';
    echo '</div>';
    echo '<div class="po-plats">';
    foreach ($PLATFORMS as $k => $label) {
        $st = isset($it['platforms'][$k]) ? $it['platforms'][$k] : 'todo';
        echo '<button type="button" class="po-plat ps-' . h($st) . '" onclick="cyclePlat(this,\'' . h($it['id']) . '\',\'' . h($k) . '\',\'' . h($st) . '\')" title="click to cycle">' . h($label) . ' · ' . h($st === 'na' ? '—' : $st) . '</button>';
    }
    echo '</div>';
    if ($it['caption'] !== '') {
        echo '<div class="po-cap"><button type="button" class="mini" onclick="copyCap(this)">copy</button><span>' . nl2br(h($it['caption'])) . '</span></div>';
    }
    if (!empty($it['assets'])) {
        echo '<div class="po-assets">';
        foreach ($it['assets'] as $a) echo '🖼 <a href="' . h($a) . '" target="_blank" rel="noopener">' . h(strlen($a) > 58 ? substr($a, 0, 55) . '…' : $a) . '</a><br>';
        echo '</div>';
    }
    if ($it['notes'] !== '') echo '<div class="po-notes">' . h($it['notes']) . '</div>';
    // edit form
    echo '<details class="po-edit"><summary>edit</summary><form method="post" action="posting.php">';
    echo '<input type="hidden" name="action" value="update"><input type="hidden" name="id" value="' . h($it['id']) . '">';
    echo '<input type="hidden" name="back" value="posting.php">';
    if (!$keyAuthed) echo csrf_field();
    po_fields($it);
    echo '<div class="po-row"><button class="btn" type="submit">Save</button></div></form>';
    echo '<form method="post" action="posting.php" onsubmit="return confirm(\'Delete this item?\')" style="margin-top:6px">';
    echo '<input type="hidden" name="action" value="del"><input type="hidden" name="id" value="' . h($it['id']) . '">';
    echo '<input type="hidden" name="back" value="posting.php">';
    if (!$keyAuthed) echo csrf_field();
    echo '<button class="btn danger" type="submit">Delete</button></form></details>';
    echo '</div>';
}

function po_fields(array $it): void {
    global $PROPS, $LANES, $ISTATES;
    echo '<div class="po-row">';
    echo '<input type="text" name="title" value="' . h($it['title']) . '" placeholder="Title" style="flex:2;min-width:200px">';
    echo '<select name="property">';
    foreach ($PROPS as $k => $p) echo '<option value="' . h($k) . '"' . ($it['property'] === $k ? ' selected' : '') . '>' . h($p['name']) . '</option>';
    echo '</select><select name="lane">';
    foreach ($LANES as $k => $l) echo '<option value="' . h($k) . '"' . ($it['lane'] === $k ? ' selected' : '') . '>' . h($l) . '</option>';
    echo '</select>';
    echo '<input type="date" name="slot" value="' . h($it['slot']) . '">';
    echo '<select name="status">';
    foreach ($ISTATES as $s) echo '<option' . ($it['status'] === $s ? ' selected' : '') . '>' . h($s) . '</option>';
    echo '</select>';
    echo '<input type="text" name="owner" value="' . h($it['owner']) . '" placeholder="who fires it (e.g. Alternate)" style="min-width:170px">';
    echo '</div>';
    echo '<textarea name="caption" rows="3" placeholder="Caption / description (copy-paste ready)">' . h($it['caption']) . '</textarea>';
    echo '<textarea name="assets" rows="2" placeholder="Asset links, one per line (Drive / portal / Flow CDN)">' . h(implode("\n", $it['assets'])) . '</textarea>';
    echo '<input type="text" name="notes" value="' . h($it['notes']) . '" placeholder="Notes">';
}

$blank = array('title' => '', 'property' => $pre['property'], 'lane' => $pre['lane'], 'slot' => $pre['slot'],
    'status' => 'draft', 'owner' => '', 'caption' => '', 'assets' => array(), 'notes' => '');
?><!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>🗓 Posting — Studio</title>
<link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="assets/studio.css">
<style>
.po-wrap{max-width:1100px;margin:0 auto;padding:18px 18px 80px}
.po-sec{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:16px 18px;margin-top:16px}
.po-sec h2{margin:0 0 10px;font-size:16px}
.po-sec h2 .sub{color:var(--muted);font-weight:400;font-size:12px;margin-left:8px}
.po-card{border:1px solid var(--border);border-radius:10px;padding:10px 12px;margin:8px 0;background:rgba(0,0,0,.12)}
.po-card.locked{border-color:#2e7d4f;box-shadow:0 0 0 1px #2e7d4f66}
.po-head{display:flex;align-items:baseline;gap:9px;flex-wrap:wrap}
.po-head .dot{width:9px;height:9px;border-radius:2px;display:inline-block;flex:none;align-self:center}
.po-slot{font-family:ui-monospace,Menlo,monospace;font-size:12px;color:var(--muted)}
.po-owner{font-size:12px;color:var(--muted)}
.po-lock{font-size:11px;font-weight:700;color:#5fd39a}
.po-st{font-size:11px;border-radius:999px;padding:1px 8px;border:1px solid var(--border);color:var(--muted)}
.po-st-ready{color:#8fc7ff;border-color:#2b5b8a}
.po-st-posted{color:#5fd39a;border-color:#2e7d4f}
.po-st-skipped{color:#ff9aa6}
.po-plats{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}
.po-plat{font-size:11.5px;border-radius:999px;padding:2px 10px;border:1px solid var(--border);background:transparent;color:var(--muted);cursor:pointer}
.po-plat.ps-scheduled{color:#8fc7ff;border-color:#2b5b8a}
.po-plat.ps-posted{color:#5fd39a;border-color:#2e7d4f}
.po-plat.ps-na{opacity:.45;text-decoration:line-through}
.po-cap{display:flex;gap:8px;align-items:flex-start;margin-top:8px;font-size:13px;color:var(--text);background:rgba(0,0,0,.18);border-radius:8px;padding:8px 10px}
.po-assets{margin-top:6px;font-size:12.5px}
.po-notes{margin-top:6px;font-size:12px;color:var(--muted)}
.po-edit{margin-top:8px}
.po-edit summary{cursor:pointer;font-size:12px;color:var(--muted)}
.po-edit form{margin-top:8px}
.po-row{display:flex;gap:8px;flex-wrap:wrap;margin:6px 0}
.po-row input,.po-row select,.po-edit textarea,.po-edit input[type=text],#po-new textarea,#po-new input[type=text]{font:inherit;font-size:13px;background:rgba(0,0,0,.2);border:1px solid var(--border);border-radius:8px;color:var(--text);padding:6px 9px}
.po-edit textarea,#po-new textarea{width:100%;margin:6px 0;resize:vertical}
.po-edit input[type=text],#po-new input[type=text]{width:100%}
.btn{font:inherit;font-size:13px;padding:6px 14px;border-radius:8px;border:1px solid var(--border);background:rgba(255,255,255,.06);color:var(--text);cursor:pointer}
.btn.danger{color:#ff9aa6;border-color:#6e2430}
.mini{font-size:11px;padding:1px 8px;border-radius:6px;border:1px solid var(--border);background:transparent;color:var(--muted);cursor:pointer;flex:none}
.po-ghost{border:1px dashed var(--border);border-radius:10px;padding:10px 12px;margin:8px 0;color:var(--muted);font-size:13px;display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.po-ghost a{color:var(--accent)}
.po-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:10px}
.po-mon{font-family:ui-monospace,Menlo,monospace;font-size:11px;color:var(--muted);margin:8px 0 2px}
.po-banner{border-radius:8px;padding:8px 12px;margin-top:12px;font-size:13px}
.po-banner.ok{background:#10331f;color:#9fe8bd}
.po-banner.err{background:#38151a;color:#ffb3bd}
</style></head><body>
<div class="topbar">
  <a class="ghost" href="cc.php" style="color:var(--text);font-weight:700">⌘ Command Center</a>
  <a class="ghost" href="posting.php" style="font-weight:700">🗓 Posting</a>
  <span style="flex:1"></span>
  <a class="ghost" href="posting.php?new=1">➕ New item</a>
</div>
<div class="po-wrap">
<?php
if (isset($_GET['ok'])) echo '<div class="po-banner ok">Saved.</div>';
if (isset($_GET['err'])) echo '<div class="po-banner err">' . h((string)$_GET['err']) . '</div>';

// 🅿️ Patreon member-count strip (cached by patreon-sync.php)
$pstats = s_read(SDATA . '/patreon-stats.json', array());
$syncUrl = 'patreon-sync.php?back=1' . ($keyAuthed ? '&key=' . urlencode((string)($_GET['key'] ?? '')) : '');
echo '<div class="po-sec" style="padding:10px 18px;display:flex;gap:16px;align-items:baseline;flex-wrap:wrap">';
echo '<strong style="font-size:13px">🅿️ Patreon</strong>';
if (!empty($pstats['accounts'])) {
    $names = array('growgetter' => 'GrowGetter', 'maxxmuscle' => 'MAXX', 'bloombeauty' => 'Bloom', '3dmuscle' => '3DMC');
    foreach ($names as $pk => $label) {
        $a = $pstats['accounts'][$pk] ?? null;
        if (!$a) continue;
        $col = isset($PROPS[$pk]) ? $PROPS[$pk]['color'] : '#378ADD';
        echo '<span class="small"><span class="dot" style="background:' . h($col) . ';width:8px;height:8px;border-radius:2px;display:inline-block;margin-right:5px"></span>';
        if (!empty($a['ok'])) {
            echo '<a href="' . h($a['url']) . '" target="_blank" rel="noopener" style="color:var(--text)">' . h($label) . '</a> <strong>' . number_format((int)$a['members']) . '</strong>';
        } else {
            echo h($label) . ' <span style="color:#ff9aa6">sync err</span>';
        }
        echo '</span>';
    }
    $age = time() - (int)strtotime((string)($pstats['ts'] ?? ''));
    $ageTxt = $age < 3600 ? floor($age / 60) . 'm' : ($age < 86400 ? floor($age / 3600) . 'h' : floor($age / 86400) . 'd');
    echo '<span class="small" style="color:var(--muted)">synced ' . h($ageTxt) . ' ago · <a href="' . h($syncUrl) . '">↻ sync now</a></span>';
} else {
    echo '<span class="small" style="color:var(--muted)">no data yet — <a href="' . h($syncUrl) . '">run first sync</a></span>';
}
echo '</div>';
?>

<?php if ($newOpen): ?>
<div class="po-sec" id="po-new">
  <h2>➕ New item</h2>
  <form method="post" action="posting.php">
    <input type="hidden" name="action" value="add">
    <input type="hidden" name="back" value="posting.php">
    <?php if (!$keyAuthed) echo csrf_field(); ?>
    <?php po_fields($blank); ?>
    <div class="po-row"><button class="btn" type="submit">Add to board</button>
    <a class="btn" href="posting.php" style="text-decoration:none">Cancel</a></div>
  </form>
</div>
<?php endif; ?>

<div class="po-sec">
  <h2>🖼 Fan Art Friday <span class="sub">weekly · fires on Patreon first, then DeviantArt — the proven metronome</span></h2>
  <?php foreach ($fridays as $f):
      $slotItems = po_pick($live, 'faf', $f); ?>
    <?php if ($slotItems): foreach ($slotItems as $it) po_card($it, $PROPS, $PLATFORMS, $LANES, $ISTATES, $keyAuthed); ?>
    <?php else: ?>
      <div class="po-ghost"><span class="po-slot"><?= h($f) ?></span> Friday is EMPTY —
        <a href="posting.php?new=1&amp;lane=faf&amp;slot=<?= h($f) ?>&amp;property=growgetter#po-new">queue a piece</a></div>
    <?php endif; ?>
  <?php endforeach; ?>
</div>

<div class="po-sec">
  <h2>📚 Monthly comic <span class="sub">one slot per property per month — fed by the Artist Portal pipeline</span></h2>
  <?php foreach ($months as $m): ?>
    <div class="po-mon"><?= h($m) ?></div>
    <div class="po-grid">
    <?php foreach ($PROPS as $pk => $p):
        $slotItems = po_pick($live, 'comic', $m, $pk); ?>
      <div>
      <?php if ($slotItems): foreach ($slotItems as $it) po_card($it, $PROPS, $PLATFORMS, $LANES, $ISTATES, $keyAuthed); ?>
      <?php else: ?>
        <div class="po-ghost"><span class="dot" style="background:<?= h($p['color']) ?>;width:9px;height:9px;border-radius:2px;display:inline-block"></span>
          <?= h($p['name']) ?> — no comic slotted.
          <a href="posting.php?new=1&amp;lane=comic&amp;slot=<?= h($m) ?>-28&amp;property=<?= h($pk) ?>#po-new">slot one</a></div>
      <?php endif; ?>
      </div>
    <?php endforeach; ?>
    </div>
  <?php endforeach; ?>
</div>

<div class="po-sec">
  <h2>✨ Side content <span class="sub">Wrench's 3D drops, guest artists, one-offs</span></h2>
  <?php $sideItems = po_pick($live, 'side', ''); ?>
  <?php if (!$sideItems): ?><div class="po-ghost">Nothing queued. <a href="posting.php?new=1&amp;lane=side#po-new">Add something</a></div><?php endif; ?>
  <?php foreach ($sideItems as $it) po_card($it, $PROPS, $PLATFORMS, $LANES, $ISTATES, $keyAuthed); ?>
</div>

<?php if ($archive): ?>
<div class="po-sec">
  <h2>🗄 Recently posted / skipped</h2>
  <?php foreach ($archive as $it) po_card($it, $PROPS, $PLATFORMS, $LANES, $ISTATES, $keyAuthed); ?>
</div>
<?php endif; ?>

<p style="color:var(--muted);font-size:12px;margin-top:18px">Chips cycle todo → scheduled → posted → — (n/a).
An item goes <b style="color:#5fd39a">🔒 locked &amp; loaded</b> when it's marked <i>ready</i> and every platform is
scheduled, posted, or n/a. The board never posts anywhere by itself.</p>
</div>
<script>
var AUTH = <?= $AUTHJS ?>;
var CYCLE = {todo:'scheduled', scheduled:'posted', posted:'na', na:'todo'};
function apiPost(fields, done) {
  var fd = new FormData();
  for (var k in fields) fd.append(k, fields[k]);
  if (AUTH.csrf) fd.append('csrf', AUTH.csrf);
  if (AUTH.key) fd.append('key', AUTH.key);
  fetch('posting.php', {method: 'POST', body: fd}).then(function (r) { return r.json(); })
    .then(function (j) { if (!j.ok) alert(j.error || 'error'); done(j); })
    .catch(function () { alert('network error'); });
}
function cyclePlat(btn, id, plat, cur) {
  var next = CYCLE[cur] || 'todo';
  apiPost({action: 'plat', id: id, plat: plat, state: next}, function (j) {
    if (j.ok) location.reload();
  });
}
function copyCap(btn) {
  var txt = btn.parentNode.querySelector('span').innerText;
  navigator.clipboard.writeText(txt).then(function () {
    btn.textContent = 'copied!'; setTimeout(function () { btn.textContent = 'copy'; }, 900);
  });
}
</script>
</body></html>
