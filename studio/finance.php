<?php
// finance.php — 💰 Costs: the payee ledger + monthly rollup, split OFF the
// schedule so the people planning posts never have to look at it.
//
// Owner ask (2026-08-19): the sheet's money tabs should come across, but as "a
// different view, so alternate doesn't have to see it". Studio auth has no roles
// — every login is equal — so access is an explicit allowlist in
// data/finance-acl.json. Absent/empty = unclaimed: the first authed person to
// open the page can lock it to themselves, and anyone already on the list can
// add or remove names. Not a hard security boundary (everyone here is already a
// trusted studio login) — a divider, which is what was asked for.
//
// Source data: data/finance.json, seeded from the sheet's payee ledger by
// tools/import_release_sheet.py. The sheet's own Budget tab is NOT copied — it
// had three rows and died in Aug 2025; monthly spend is computed from the ledger
// instead, and earnings are the one number entered by hand.
declare(strict_types=1);
require_once __DIR__ . '/inc/boot.php';
require_auth();

define('FI_FILE', SDATA . '/finance.json');
define('FI_ACL',  SDATA . '/finance-acl.json');

$me = current_studio_user();

function fi_allow(): array {
    $acl = s_read(FI_ACL, array());
    $a = isset($acl['allow']) && is_array($acl['allow']) ? $acl['allow'] : array();
    return array_values(array_filter(array_map('strval', $a)));
}
function fi_may(string $user): bool {
    $allow = fi_allow();
    if (!$allow) return false;                       // unclaimed → nobody, until claimed
    foreach ($allow as $a) if (strcasecmp($a, $user) === 0) return true;
    return false;
}
$allow = fi_allow();
$unclaimed = !$allow;
$may = fi_may($me);

// ---------------- mutations --------------------------------------------------
$action = isset($_POST['action']) ? (string)$_POST['action'] : '';
if ($action !== '') {
    csrf_check();
    header('Content-Type: application/json');
    $out = array('ok' => false, 'error' => 'Not permitted.');

    if ($action === 'claim' && $unclaimed && $me !== '') {
        // first-open claim; races are resolved inside the lock, not out here
        $res = s_with_lock(FI_ACL, function ($acl) use ($me) {
            if (is_array($acl) && !empty($acl['allow'])) return array('data' => $acl, 'result' => 'Already claimed.');
            return array('data' => array('allow' => array($me), 'claimedAt' => gmdate('c')), 'result' => '');
        });
        $out = $res === '' ? array('ok' => true) : array('ok' => false, 'error' => (string)$res);

    } elseif ($may && $action === 'acl') {
        $name = trim((string)($_POST['name'] ?? ''));
        $drop = trim((string)($_POST['drop'] ?? ''));
        $res = s_with_lock(FI_ACL, function ($acl) use ($name, $drop, $me) {
            $list = (is_array($acl) && is_array($acl['allow'] ?? null)) ? $acl['allow'] : array();
            if ($name !== '' && !in_array($name, $list, true)) $list[] = $name;
            if ($drop !== '') {
                if (strcasecmp($drop, $me) === 0 && count($list) <= 1)
                    return array('data' => $acl, 'result' => 'You are the only one with access — add someone else first.');
                $list = array_values(array_filter($list, fn($x) => strcasecmp($x, $drop) !== 0));
            }
            $acl = is_array($acl) ? $acl : array();
            $acl['allow'] = array_values($list);
            return array('data' => $acl, 'result' => '');
        });
        $out = $res === '' ? array('ok' => true) : array('ok' => false, 'error' => (string)$res);

    } elseif ($may && ($action === 'row' || $action === 'delrow')) {
        $rid = (string)($_POST['rid'] ?? '');
        $res = s_with_lock(FI_FILE, function ($db) use ($action, $rid) {
            if (!is_array($db)) $db = array('budget' => array(), 'payees' => array());
            if (!is_array($db['payees'] ?? null)) $db['payees'] = array();

            if ($action === 'delrow') {
                foreach ($db['payees'] as $i => $r) {
                    if ((string)($r['id'] ?? '') === $rid) { array_splice($db['payees'], $i, 1); return array('data' => $db, 'result' => ''); }
                }
                return array('data' => $db, 'result' => 'No such row.');
            }

            $cost = (string)($_POST['cost'] ?? '');
            $cost = preg_replace('/[^0-9.\-]/', '', $cost);
            $fields = array(
                'date'    => substr(preg_replace('/[^0-9\-\/.]/', '', (string)($_POST['date'] ?? '')), 0, 10),
                'payee'   => substr(trim((string)($_POST['payee'] ?? '')), 0, 80),
                'project' => substr(trim((string)($_POST['project'] ?? '')), 0, 120),
                'cost'    => $cost === '' ? null : (float)$cost,
                'notes'   => substr(trim((string)($_POST['notes'] ?? '')), 0, 300),
            );
            if ($fields['payee'] === '') return array('data' => $db, 'result' => 'Payee required.');

            foreach ($db['payees'] as $i => $r) {
                if ((string)($r['id'] ?? '') === $rid) {
                    $db['payees'][$i] = array_merge($r, $fields, array('updatedAt' => gmdate('c')));
                    return array('data' => $db, 'result' => '');
                }
            }
            $db['payees'][] = array_merge(array('id' => 'fi_' . nid(), 'source' => 'manual', 'createdAt' => gmdate('c')), $fields);
            return array('data' => $db, 'result' => '');
        });
        $out = $res === '' ? array('ok' => true) : array('ok' => false, 'error' => (string)$res);
    }

    echo json_encode($out);
    exit;
}

// ---------------- render -----------------------------------------------------
// The importer writes rows without ids; back-fill them under the lock and render
// from what was actually stored, so the rids in the HTML always match the file
// (rendering pre-write ids would leave every delete button pointing at nothing).
$fin = $may
    ? s_with_lock(FI_FILE, function ($db) {
        if (!is_array($db)) $db = array('budget' => array(), 'payees' => array());
        if (!is_array($db['payees'] ?? null)) $db['payees'] = array();
        $dirty = false;
        foreach ($db['payees'] as $i => $r) {
            if (empty($r['id'])) { $db['payees'][$i]['id'] = 'fi_' . substr(md5(json_encode($r) . $i), 0, 10); $dirty = true; }
        }
        return $dirty ? array('data' => $db, 'result' => $db) : array('result' => $db);
    })
    : s_read(FI_FILE, array('budget' => array(), 'payees' => array()));
$payees = is_array($fin['payees'] ?? null) ? $fin['payees'] : array();

// monthly spend, derived from the ledger rather than re-typed
$byMonth = array(); $byPayee = array();
foreach ($payees as $r) {
    $c = isset($r['cost']) && $r['cost'] !== null ? (float)$r['cost'] : 0.0;
    $d = (string)($r['date'] ?? '');
    $mk = '';
    foreach (array('m/d/Y', 'm/d/y', 'Y-m-d', 'n/j/y', 'n/j/Y') as $f) {
        $dt = DateTime::createFromFormat($f, $d);
        if ($dt instanceof DateTime) { $mk = $dt->format('Y-m'); break; }
    }
    if ($mk !== '') {
        if (!isset($byMonth[$mk])) $byMonth[$mk] = array('in' => 0.0, 'out' => 0.0, 'n' => 0);
        $byMonth[$mk][$c >= 0 ? 'in' : 'out'] += abs($c);
        $byMonth[$mk]['n']++;
    }
    $p = (string)($r['payee'] ?? '');
    if ($p !== '') {
        if (!isset($byPayee[$p])) $byPayee[$p] = array('spend' => 0.0, 'n' => 0);
        if ($c < 0) $byPayee[$p]['spend'] += abs($c);
        $byPayee[$p]['n']++;
    }
}
krsort($byMonth);
uasort($byPayee, fn($a, $b) => $b['spend'] <=> $a['spend']);

$money = fn($v) => ($v < 0 ? '-' : '') . '$' . number_format(abs((float)$v), 2);
?><!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>💰 Costs — Studio</title>
<link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="assets/studio.css">
<style>
.fi-wrap{max-width:1120px;margin:0 auto;padding:18px 18px 80px}
.fi-sec{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:16px 18px;margin-top:16px}
.fi-sec h2{margin:0 0 4px;font-size:15px}
.fi-sec .sub{color:var(--muted);font-size:12px;margin-bottom:12px}
table.fi{border-collapse:collapse;width:100%;font-size:12.5px}
table.fi th,table.fi td{border-bottom:1px solid var(--border);padding:7px 9px;text-align:left}
table.fi th{font-size:11.5px;color:var(--muted);font-weight:600}
table.fi td.num,table.fi th.num{text-align:right;font-family:ui-monospace,Menlo,monospace}
table.fi td.neg{color:#f3a3a2}
table.fi tr:hover td{background:rgba(255,255,255,.03)}
.fi-in{font:inherit;font-size:12.5px;background:var(--bg2);border:1px solid var(--border2);color:var(--text);
       border-radius:7px;padding:5px 8px;width:100%;margin:0;display:block}
.fi-grid{display:grid;grid-template-columns:110px 1fr 1.4fr 110px 1fr auto;gap:8px;align-items:center}
.fi-tot{display:flex;gap:22px;flex-wrap:wrap;margin-bottom:12px}
.fi-tot div b{display:block;font-size:20px;font-weight:800}
.fi-tot div span{font-size:11.5px;color:var(--muted)}
.fi-msg{font-size:12.5px;margin-top:8px;min-height:16px}
.fi-msg.err{color:#f3a3a2}.fi-msg.ok{color:#5FD39A}
.fi-lock{max-width:520px;margin:60px auto;text-align:center}
.fi-acl{display:flex;gap:7px;flex-wrap:wrap;align-items:center;margin-top:8px}
.fi-who{display:inline-flex;align-items:center;gap:7px;border:1px solid var(--border2);border-radius:999px;padding:3px 10px;font-size:12px}
.fi-who button{background:none;border:none;color:var(--muted);cursor:pointer;font-size:13px;padding:0}
</style>
</head>
<body>
<div class="topbar">
  <a class="brand" href="cc.php"><span class="dot"></span> Command Center</a>
  <a class="ghost" href="schedule.php">📅 Schedule</a>
  <a class="ghost" href="posting.php">🗓 Posting board</a>
  <span class="spacer"></span>
  <span class="ghost"><?= h($me) ?></span>
</div>

<div class="fi-wrap">
<?php if ($unclaimed): ?>
  <div class="card fi-lock">
    <h1 style="font-size:19px">💰 Costs are unassigned</h1>
    <p class="muted" style="font-size:13.5px">
      Nobody has been granted access to the money view yet. Claim it and only you will see it —
      the schedule and posting board stay open to everyone as they are.
    </p>
    <div class="actions" style="justify-content:center">
      <button class="btn primary" id="fi-claim">Lock costs to <?= h($me ?: 'me') ?></button>
    </div>
    <div class="fi-msg" id="fi-msg"></div>
  </div>

<?php elseif (!$may): ?>
  <div class="card fi-lock">
    <h1 style="font-size:19px">💰 Restricted</h1>
    <p class="muted" style="font-size:13.5px">
      The costs view is limited to <?= h(implode(', ', $allow)) ?>.
      Everything about scheduling and posting lives on
      <a href="schedule.php" style="text-decoration:underline">the schedule</a>.
    </p>
  </div>

<?php else: ?>
  <div class="pagehead">
    <h1>💰 Costs</h1>
    <div class="ghost">Ledger + monthly rollup · not linked from anyone else's view</div>
  </div>

  <?php
    $spend = 0.0; $income = 0.0;
    foreach ($payees as $r) { $c = (float)($r['cost'] ?? 0); if ($c < 0) $spend += abs($c); else $income += $c; }
    $noCost = count(array_filter($payees, fn($r) => !isset($r['cost']) || $r['cost'] === null));
  ?>
  <div class="fi-sec">
    <div class="fi-tot">
      <div><b><?= h($money($spend)) ?></b><span>recorded spend</span></div>
      <div><b><?= h($money($income)) ?></b><span>recorded income</span></div>
      <div><b><?= count($payees) ?></b><span>ledger rows</span></div>
      <?php if ($noCost): ?><div><b style="color:#EF9F27"><?= (int)$noCost ?></b><span>rows with no amount</span></div><?php endif; ?>
    </div>
    <p class="sub" style="margin:0">
      Imported from the sheet's payee tabs. Many of the older rows carry a payee and a project but no
      amount — the sheet was filled in that way, so the totals above are a floor, not the real spend.
    </p>
  </div>

  <div class="fi-sec">
    <h2>By month</h2>
    <div class="sub">Derived from the ledger dates — nothing re-typed.</div>
    <table class="fi"><thead><tr><th>Month</th><th class="num">Out</th><th class="num">In</th><th class="num">Net</th><th class="num">Rows</th></tr></thead><tbody>
    <?php foreach ($byMonth as $mk => $v): ?>
      <tr><td><?= h($mk) ?></td>
        <td class="num neg"><?= h($money(-$v['out'])) ?></td>
        <td class="num"><?= h($money($v['in'])) ?></td>
        <td class="num"><?= h($money($v['in'] - $v['out'])) ?></td>
        <td class="num"><?= (int)$v['n'] ?></td></tr>
    <?php endforeach; ?>
    <?php if (!$byMonth): ?><tr><td colspan="5" class="muted">No dated rows yet.</td></tr><?php endif; ?>
    </tbody></table>
  </div>

  <div class="fi-sec">
    <h2>By payee</h2>
    <table class="fi"><thead><tr><th>Payee</th><th class="num">Spend</th><th class="num">Rows</th></tr></thead><tbody>
    <?php foreach ($byPayee as $p => $v): ?>
      <tr><td><?= h($p) ?></td><td class="num neg"><?= h($money(-$v['spend'])) ?></td><td class="num"><?= (int)$v['n'] ?></td></tr>
    <?php endforeach; ?>
    </tbody></table>
  </div>

  <div class="fi-sec">
    <h2>Ledger</h2>
    <div class="sub">Costs are negative, payouts positive. Blank amount = the sheet never recorded one.</div>
    <div class="fi-grid" style="margin-bottom:10px">
      <input class="fi-in" id="n-date" placeholder="date"><input class="fi-in" id="n-payee" placeholder="payee">
      <input class="fi-in" id="n-project" placeholder="project"><input class="fi-in" id="n-cost" placeholder="-400">
      <input class="fi-in" id="n-notes" placeholder="notes">
      <button class="btn primary" id="fi-add">Add</button>
    </div>
    <div class="fi-msg" id="fi-msg"></div>
    <table class="fi"><thead><tr><th>Date</th><th>Payee</th><th>Project</th><th class="num">Amount</th><th>Notes</th><th></th></tr></thead><tbody>
    <?php foreach (array_reverse($payees) as $r):
        $c = isset($r['cost']) && $r['cost'] !== null ? (float)$r['cost'] : null; ?>
      <tr data-rid="<?= h($r['id']) ?>">
        <td><?= h($r['date'] ?? '') ?></td>
        <td><?= h($r['payee'] ?? '') ?></td>
        <td><?= h($r['project'] ?? '') ?></td>
        <td class="num <?= $c !== null && $c < 0 ? 'neg' : '' ?>"><?= $c === null ? '<span class="muted">—</span>' : h($money($c)) ?></td>
        <td class="muted"><?= h($r['notes'] ?? '') ?></td>
        <td><button class="fi-del" style="background:none;border:none;color:var(--muted);cursor:pointer">✕</button></td>
      </tr>
    <?php endforeach; ?>
    </tbody></table>
  </div>

  <div class="fi-sec">
    <h2>Who can see this</h2>
    <div class="fi-acl" id="fi-acl">
      <?php foreach ($allow as $a): ?>
        <span class="fi-who"><?= h($a) ?><button data-drop="<?= h($a) ?>" title="remove">✕</button></span>
      <?php endforeach; ?>
      <input class="fi-in" id="acl-name" placeholder="add a studio username" style="width:210px">
      <button class="mini btn" id="acl-add">Add</button>
    </div>
  </div>
<?php endif; ?>
</div>

<script>
const CSRF = <?= json_encode(csrf()) ?>;
const $ = s => document.querySelector(s);
const msg = (t, ok) => { const m = $('#fi-msg'); if (m) { m.className = 'fi-msg ' + (ok ? 'ok' : 'err'); m.textContent = t; } };

async function post(data, reload) {
  const r = await fetch('finance.php', { method: 'POST', body: new URLSearchParams(Object.assign({ csrf: CSRF }, data)) });
  const j = await r.json().catch(() => ({ ok: false, error: 'Bad response.' }));
  if (!j.ok) { msg(j.error || 'Failed.', false); return false; }
  if (reload !== false) location.reload();
  return true;
}

if ($('#fi-claim')) $('#fi-claim').onclick = () => post({ action: 'claim' });
if ($('#fi-add')) $('#fi-add').onclick = () => post({
  action: 'row', rid: '', date: $('#n-date').value, payee: $('#n-payee').value,
  project: $('#n-project').value, cost: $('#n-cost').value, notes: $('#n-notes').value,
});
if ($('#acl-add')) $('#acl-add').onclick = () => post({ action: 'acl', name: $('#acl-name').value });
document.addEventListener('click', e => {
  const drop = e.target.closest('[data-drop]');
  if (drop) { if (confirm('Remove ' + drop.dataset.drop + ' from the costs view?')) post({ action: 'acl', drop: drop.dataset.drop }); return; }
  const del = e.target.closest('.fi-del');
  if (del) {
    const tr = del.closest('tr');
    if (confirm('Delete this ledger row?')) post({ action: 'delrow', rid: tr.dataset.rid });
  }
});
</script>
</body></html>
