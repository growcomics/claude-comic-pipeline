<?php
// thanks.php — 🙏 SPECIAL THANKS manager (replaces the monthly Google Form flow).
// Create an "edition" per comic release → get an unguessable fan link
// (https://<site>/thanks/?e=<token>) to drop in the Patreon comic-tier post →
// fans add the handle they want credited → names collect in studio/data/thanks/
// (web-denied). This page: create/rename/open-close editions, copy the link,
// view + prune names, add stragglers by hand, copy a paste-ready credits block,
// export CSV for Boogie. Fan-facing form lives at /thanks/index.php (public).
// NEW standalone file — shares only inc/boot.php; no other studio file touched.
declare(strict_types=1);
require_once __DIR__ . '/inc/boot.php';
require_auth();

define('THANKS_DIR', SDATA . '/thanks');
define('EDITIONS_FILE', THANKS_DIR . '/editions.json');

function th_entries_file(string $id): string {
    return THANKS_DIR . '/entries-' . preg_replace('/[^a-z0-9\-]/i', '', $id) . '.json';
}
// Same handle sanitizer as thanks/index.php — keep the two in sync.
function th_clean_handle(string $h): string {
    $h = strip_tags($h);
    $h = preg_replace('/[\x00-\x1F\x7F]/u', '', $h) ?? '';
    $h = preg_replace('/\s+/u', ' ', trim($h)) ?? '';
    return mb_substr($h, 0, 40);
}
function th_link(string $token): string {
    $host = $_SERVER['HTTP_HOST'] ?? '3dmusclecomics.com';
    return 'https://' . $host . '/thanks/?e=' . $token;
}

$editions = s_read(EDITIONS_FILE, []);
$msg = '';

// ---- CSV export (GET, auth'd) ---------------------------------------------
if (isset($_GET['export'])) {
    $id = (string)$_GET['export'];
    foreach ($editions as $e) {
        if (($e['id'] ?? '') === $id) {
            $rows = s_read(th_entries_file($id), []);
            usort($rows, fn($a, $b) => ($a['ts'] ?? 0) <=> ($b['ts'] ?? 0));
            header('Content-Type: text/csv; charset=utf-8');
            header('Content-Disposition: attachment; filename="special-thanks-' . preg_replace('/[^a-z0-9\-]/i', '-', strtolower((string)$e['title'])) . '.csv"');
            $out = fopen('php://output', 'w');
            fputcsv($out, ['handle', 'submitted_utc']);
            foreach ($rows as $r) fputcsv($out, [(string)($r['n'] ?? ''), gmdate('Y-m-d H:i', (int)($r['ts'] ?? 0))]);
            fclose($out);
            exit;
        }
    }
    http_response_code(404); exit('unknown edition');
}

// ---- actions ---------------------------------------------------------------
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    csrf_check();
    $do = (string)($_POST['do'] ?? '');
    $id = (string)($_POST['id'] ?? '');
    $idx = null;
    foreach ($editions as $k => $e) if (($e['id'] ?? '') === $id) { $idx = $k; break; }

    if ($do === 'create') {
        $title = th_clean_handle((string)($_POST['title'] ?? ''));
        if ($title === '') { $msg = 'Give the edition a title.'; }
        else {
            $editions[] = [
                'id' => nid(), 'token' => bin2hex(random_bytes(10)), 'title' => $title,
                'status' => 'open', 'created' => time(), 'by' => current_studio_user(),
            ];
            s_write(EDITIONS_FILE, $editions);
            header('Location: thanks.php'); exit;
        }
    } elseif ($idx !== null && $do === 'toggle') {
        $editions[$idx]['status'] = (($editions[$idx]['status'] ?? 'open') === 'open') ? 'closed' : 'open';
        s_write(EDITIONS_FILE, $editions);
        header('Location: thanks.php'); exit;
    } elseif ($idx !== null && $do === 'rename') {
        $title = th_clean_handle((string)($_POST['title'] ?? ''));
        if ($title !== '') { $editions[$idx]['title'] = $title; s_write(EDITIONS_FILE, $editions); }
        header('Location: thanks.php'); exit;
    } elseif ($idx !== null && $do === 'trash') {
        // Recoverable, never rm: status flips to trashed (hidden below) and the
        // entries file stays on disk untouched.
        $editions[$idx]['status'] = 'trashed';
        s_write(EDITIONS_FILE, $editions);
        header('Location: thanks.php'); exit;
    } elseif ($idx !== null && $do === 'addname') {
        $h = th_clean_handle((string)($_POST['handle'] ?? ''));
        if ($h !== '') {
            $f = th_entries_file($id);
            $rows = s_read($f, []);
            $dup = false;
            foreach ($rows as $r) if (mb_strtolower((string)($r['n'] ?? '')) === mb_strtolower($h)) $dup = true;
            if (!$dup) { $rows[] = ['n' => $h, 'ts' => time(), 'ip' => 'admin']; s_write($f, $rows); }
        }
        header('Location: thanks.php#ed-' . $id); exit;
    } elseif ($idx !== null && $do === 'delname') {
        $ts = (int)($_POST['ts'] ?? 0); $n = (string)($_POST['n'] ?? '');
        $f = th_entries_file($id);
        $rows = s_read($f, []);
        foreach ($rows as $k => $r) {
            if ((int)($r['ts'] ?? 0) === $ts && (string)($r['n'] ?? '') === $n) { unset($rows[$k]); break; }
        }
        s_write($f, array_values($rows));
        header('Location: thanks.php#ed-' . $id); exit;
    }
}

// newest first, trashed hidden
$visible = array_values(array_filter($editions, fn($e) => ($e['status'] ?? 'open') !== 'trashed'));
usort($visible, fn($a, $b) => ($b['created'] ?? 0) <=> ($a['created'] ?? 0));
?><!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>Special Thanks — editions &amp; names</title>
<script src="https://3dmusclecomics.com/hub/nav.js"></script>
</head>
<body style="margin:0">
<div style="padding:10px 18px;font:600 13px system-ui;border-bottom:1px solid rgba(128,128,128,.35);display:flex;gap:18px;align-items:center">
  <a href="cc.php" style="color:inherit;text-decoration:none">&#8984; Command Center</a>
  <a href="index.php" style="color:inherit;text-decoration:none;opacity:.75">🎬 Studio</a>
</div>
<style>
:root{--bg:#F2F4F3;--panel:#FFFFFF;--ink:#1B2126;--mut:#5C676E;--line:#DDE3E1;--acc:#D64550;--acc-ink:#fff;--good:#1F7A4D;--chipbg:#EDF0EF}
@media (prefers-color-scheme: dark){:root{--bg:#14171B;--panel:#1C2026;--ink:#E8ECEF;--mut:#95A0A8;--line:#2A3138;--acc:#E8565F;--good:#4CC48A;--chipbg:#242A31}}
:root[data-theme="dark"]{--bg:#14171B;--panel:#1C2026;--ink:#E8ECEF;--mut:#95A0A8;--line:#2A3138;--acc:#E8565F;--good:#4CC48A;--chipbg:#242A31}
:root[data-theme="light"]{--bg:#F2F4F3;--panel:#FFFFFF;--ink:#1B2126;--mut:#5C676E;--line:#DDE3E1;--acc:#D64550;--good:#1F7A4D;--chipbg:#EDF0EF}
*{box-sizing:border-box}body{background:var(--bg);color:var(--ink);font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;margin:0}
.wrap{max-width:900px;margin:0 auto;padding:28px 20px 80px}
h1{font-family:"Avenir Next Condensed","HelveticaNeue-CondensedBold","Arial Narrow",sans-serif;font-weight:800;font-size:clamp(30px,5vw,42px);letter-spacing:.5px;text-transform:uppercase;margin:0}
h1 em{color:var(--acc);font-style:normal}
.sub{color:var(--mut);margin:6px 0 0;max-width:75ch}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:18px;margin-top:18px}
.newrow{display:flex;gap:10px}
.newrow input{flex:1;padding:10px 12px;font-size:15px;border:1px solid var(--line);border-radius:8px;background:var(--bg);color:var(--ink)}
button,.btn{padding:9px 16px;font-size:14px;font-weight:700;border:0;border-radius:8px;background:var(--acc);color:var(--acc-ink,#fff);cursor:pointer;text-decoration:none;display:inline-block}
button.ghost,.btn.ghost{background:var(--chipbg);color:var(--ink);border:1px solid var(--line);font-weight:600}
.edhead{display:flex;flex-wrap:wrap;gap:8px 14px;align-items:center}
.edhead h2{font-family:"Avenir Next Condensed","Arial Narrow",sans-serif;text-transform:uppercase;letter-spacing:.6px;font-size:20px;margin:0}
.chip{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.6px;padding:3px 9px;border-radius:99px}
.c-open{background:color-mix(in srgb,var(--good) 15%,transparent);color:var(--good)}
.c-closed{background:color-mix(in srgb,var(--mut) 18%,transparent);color:var(--mut)}
.cnt{font-family:ui-monospace,Menlo,monospace;font-size:12.5px;color:var(--mut)}
.linkrow{display:flex;gap:8px;margin-top:12px;align-items:center}
.linkrow input{flex:1;padding:8px 10px;font:12.5px ui-monospace,Menlo,monospace;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--ink)}
.names{display:flex;flex-wrap:wrap;gap:6px;margin-top:12px}
.names form{display:inline}
.names .nm{display:inline-flex;align-items:center;gap:6px;background:var(--chipbg);border:1px solid var(--line);border-radius:99px;padding:4px 6px 4px 12px;font-size:13.5px}
.names .nm button{background:none;border:0;color:var(--mut);font-size:13px;padding:0 4px;cursor:pointer;font-weight:700}
.names .nm button:hover{color:var(--acc)}
.tools{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px;align-items:center}
.tools form{display:flex;gap:8px;align-items:center}
.tools input[type=text]{padding:8px 10px;font-size:13.5px;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--ink)}
textarea.credits{width:100%;margin-top:10px;min-height:90px;padding:10px;font:13px ui-monospace,Menlo,monospace;border:1px solid var(--line);border-radius:8px;background:var(--bg);color:var(--ink)}
.empty{color:var(--mut);font-size:13.5px;margin-top:10px}
.msg{background:color-mix(in srgb,var(--acc) 12%,transparent);color:var(--acc);border:1px solid var(--acc);border-radius:8px;padding:9px 13px;margin-top:12px;font-weight:600}
details.danger{margin-top:12px}
details.danger summary{color:var(--mut);font-size:12.5px;cursor:pointer}
.copied{color:var(--good);font-size:12.5px;font-weight:700;display:none}
</style>
<div class="wrap">
  <h1>Special <em>Thanks</em></h1>
  <p class="sub">One edition per comic release. Create it, copy the fan link into the comic-tier Patreon post, and the credited handles collect here — Boogie reads or exports them from this page. No Google Forms, no Sheets.</p>

  <div class="card">
    <form method="post" class="newrow">
      <?= csrf_field() ?>
      <input type="hidden" name="do" value="create">
      <input type="text" name="title" maxlength="40" required placeholder='New edition title — e.g. "Boogie — August 2026"'>
      <button type="submit">+ Create edition</button>
    </form>
    <?php if ($msg): ?><div class="msg"><?= h($msg) ?></div><?php endif; ?>
  </div>

  <?php if (!$visible): ?>
    <p class="empty" style="margin-top:22px">No editions yet — create the first one above.</p>
  <?php endif; ?>

  <?php foreach ($visible as $e):
      $eid = (string)$e['id'];
      $rows = s_read(th_entries_file($eid), []);
      usort($rows, fn($a, $b) => ($a['ts'] ?? 0) <=> ($b['ts'] ?? 0));
      $open = ($e['status'] ?? 'open') === 'open';
      $creditNames = array_map(fn($r) => (string)($r['n'] ?? ''), $rows);
  ?>
  <div class="card" id="ed-<?= h($eid) ?>">
    <div class="edhead">
      <h2><?= h($e['title']) ?></h2>
      <span class="chip <?= $open ? 'c-open' : 'c-closed' ?>"><?= $open ? 'open' : 'closed' ?></span>
      <span class="cnt"><?= count($rows) ?> name<?= count($rows) === 1 ? '' : 's' ?> · created <?= gmdate('M j, Y', (int)($e['created'] ?? 0)) ?></span>
      <form method="post" style="margin-left:auto"><?= csrf_field() ?><input type="hidden" name="do" value="toggle"><input type="hidden" name="id" value="<?= h($eid) ?>"><button class="ghost" type="submit"><?= $open ? '✋ Close submissions' : '▶ Reopen' ?></button></form>
    </div>

    <div class="linkrow">
      <input type="text" readonly value="<?= h(th_link((string)$e['token'])) ?>" onclick="this.select()">
      <button class="ghost" type="button" onclick="copyVal(this)">📋 Copy link</button>
      <span class="copied">copied ✓</span>
    </div>

    <?php if ($rows): ?>
      <div class="names">
        <?php foreach ($rows as $r): ?>
          <span class="nm"><?= h($r['n'] ?? '') ?><form method="post" onsubmit="return confirm('Remove &quot;<?= h($r['n'] ?? '') ?>&quot; from the list?')"><?= csrf_field() ?><input type="hidden" name="do" value="delname"><input type="hidden" name="id" value="<?= h($eid) ?>"><input type="hidden" name="ts" value="<?= (int)($r['ts'] ?? 0) ?>"><input type="hidden" name="n" value="<?= h($r['n'] ?? '') ?>"><button type="submit" title="remove">✕</button></form></span>
        <?php endforeach; ?>
      </div>
      <textarea class="credits" readonly onclick="this.select()">SPECIAL THANKS
<?= h(implode("\n", $creditNames)) . "\n" ?></textarea>
    <?php else: ?>
      <p class="empty">No names yet — share the link above in the Patreon post.</p>
    <?php endif; ?>

    <div class="tools">
      <form method="post"><?= csrf_field() ?><input type="hidden" name="do" value="addname"><input type="hidden" name="id" value="<?= h($eid) ?>"><input type="text" name="handle" maxlength="40" placeholder="Add a name by hand"><button class="ghost" type="submit">＋ Add</button></form>
      <?php if ($rows): ?><a class="btn ghost" href="?export=<?= h($eid) ?>">⬇ Export CSV</a><?php endif; ?>
      <form method="post"><?= csrf_field() ?><input type="hidden" name="do" value="rename"><input type="hidden" name="id" value="<?= h($eid) ?>"><input type="text" name="title" maxlength="40" placeholder="Rename edition" value="<?= h($e['title']) ?>"><button class="ghost" type="submit">Rename</button></form>
    </div>

    <details class="danger">
      <summary>Danger zone</summary>
      <form method="post" style="margin-top:8px" onsubmit="return confirm('Hide this edition? The link stops working; the names file stays on disk (recoverable).')"><?= csrf_field() ?><input type="hidden" name="do" value="trash"><input type="hidden" name="id" value="<?= h($eid) ?>"><button class="ghost" type="submit">🗑 Trash edition (recoverable)</button></form>
    </details>
  </div>
  <?php endforeach; ?>
</div>
<script>
function copyVal(btn){
  const inp = btn.parentElement.querySelector('input');
  inp.select();
  navigator.clipboard.writeText(inp.value).then(()=>{
    const ok = btn.parentElement.querySelector('.copied');
    ok.style.display='inline'; setTimeout(()=>ok.style.display='none', 1600);
  });
}
</script>
</body>
</html>
