<?php
// site.php?s=<key> — Command Center PER-SITE overview (one parametrized file, like
// review.php's ?p= pattern — not seven near-identical copies).
//
// Shows: quick-links grid (editable in place → ops-api sitelinks), the site's OPEN tasks
// pulled from the ops board (priority → revenue-impact order, each deep-linking into
// ops.php#task=<id>), a site-scoped quick-add, and a notes log (ops-api sitenote,
// newest first — the feedback-log pattern). Data: data/cc-sites.json + data/ops-tasks.json.
declare(strict_types=1);
require_once __DIR__ . '/inc/ops.php';
require_auth();

$sites = ops_sites();
$key   = (string)($_GET['s'] ?? '');
if (!isset($sites[$key])) { header('Location: cc.php'); exit; }
$site = $sites[$key];

$tasks = ops_load()['tasks'];
$mine = array_values(array_filter($tasks, fn($t) => ops_open($t) && in_array($key, (array)($t['sites'] ?? []), true)));
$rank = ['critical'=>0, 'high'=>1, 'medium'=>2, 'low'=>3, ''=>4];
usort($mine, fn($a, $b) => ($rank[$a['priority'] ?? ''] ?? 4) <=> ($rank[$b['priority'] ?? ''] ?? 4)
    ?: ((int)($b['revenueImpact'] ?? 0)) <=> ((int)($a['revenueImpact'] ?? 0)));

$doneRecent = 0;
foreach ($tasks as $t)
    if (($t['status'] ?? '') === 'done' && in_array($key, (array)($t['sites'] ?? []), true)
        && (string)($t['completedOn'] ?? '') >= date('Y-m-d', strtotime('-30 days'))) $doneRecent++;

$priC = ['critical'=>'#D9534F', 'high'=>'#EF9F27', 'medium'=>'#5BA7E6', 'low'=>'#6F7380'];
?><!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark"><meta name="robots" content="noindex,nofollow">
<title><?= h($site['name']) ?> · Command Center</title>
<link rel="icon" href="assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="assets/studio.css">
<style>
.sp-head{display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.sdot{width:14px;height:14px;border-radius:50%;flex:none;background:<?= h($site['color'] ?? '#6F7380') ?>}
.sp-links{display:flex;gap:8px;flex-wrap:wrap;margin:14px 0}
.sp-links a.btn.empty{opacity:.4;border-style:dashed}
.sp-cols{display:grid;grid-template-columns:1fr 340px;gap:18px;align-items:start}
@media(max-width:900px){.sp-cols{grid-template-columns:1fr}}
.tk{display:flex;align-items:center;gap:8px;padding:8px 12px;border-bottom:1px solid var(--border);flex-wrap:wrap}
.tk:last-child{border-bottom:0}
.tk a{color:var(--text);text-decoration:none;flex:1;min-width:200px;font-size:14px}
.tk a:hover{text-decoration:underline}
.chip{border-radius:6px;padding:1px 7px;font-size:11px;font-weight:600;background:color-mix(in srgb,var(--c) 20%,transparent);color:var(--c);border:1px solid color-mix(in srgb,var(--c) 40%,transparent);white-space:nowrap}
.dots{font-size:11px;letter-spacing:1px;color:#EF9F27;white-space:nowrap}
.sp-add{display:flex;gap:8px;padding:8px 12px;border-bottom:1px solid var(--border)}
.sp-add input{flex:1;background:var(--bg);color:var(--text);border:1px dashed var(--border);border-radius:8px;padding:6px 10px;font-size:13px}
.note{border-left:2px solid var(--border);padding:6px 10px;margin:8px 0;font-size:13px}
.note .meta{color:var(--muted);font-size:11px;margin-bottom:2px}
.note .txt{white-space:pre-wrap;word-break:break-word}
.el-row{display:flex;gap:6px;margin:4px 0}
.el-row input{background:var(--bg);color:var(--text);border:1px solid var(--border);border-radius:8px;padding:5px 8px;font-size:12px}
.toast{position:fixed;bottom:16px;right:16px;background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:10px 14px;font-size:13px;z-index:60;display:none}
</style></head><body>
<header class="topbar">
  <div class="brand"><a href="cc.php" style="color:inherit;text-decoration:none"><span class="dot"></span> ⌘ Command Center</a></div>
  <a class="ghost" href="cc.php">Home</a>
  <a class="ghost" href="ops.php">📋 Ops Board</a>
  <a class="ghost" href="index.php">🎬 Pipeline</a>
  <span class="spacer"></span>
  <span class="ghost"><?= h(current_studio_user()) ?></span>
  <a class="ghost" href="login.php?do=logout">Log out</a>
</header>
<main class="wrap">
  <div class="pagehead sp-head">
    <span class="sdot"></span><h1><?= h($site['name']) ?></h1>
    <span class="muted"><?= h($site['type'] ?? '') ?><?= empty($site['active']) ? ' · inactive' : '' ?></span>
    <span class="spacer"></span>
    <span class="muted"><?= count($mine) ?> open · <?= $doneRecent ?> done in 30d</span>
  </div>

  <div class="sp-links" id="linksView">
    <?php foreach ((array)($site['links'] ?? []) as $l): $url = trim((string)($l['url'] ?? '')); ?>
      <?php if ($url !== ''): ?><a class="btn sm" target="_blank" rel="noopener" href="<?= h($url) ?>">🔗 <?= h($l['label']) ?></a>
      <?php else: ?><a class="btn sm empty" href="#" onclick="editLinks();return false" title="no URL yet — click to add"><?= h($l['label']) ?> ＋</a><?php endif; ?>
    <?php endforeach; ?>
    <a class="btn sm ghost" href="#" onclick="editLinks();return false">✎ Edit links</a>
  </div>
  <div id="linksEdit" style="display:none;margin:14px 0"></div>

  <div class="sp-cols">
    <div class="card" style="padding:0;overflow:hidden">
      <div style="padding:10px 12px;border-bottom:1px solid var(--border);display:flex;align-items:center">
        <strong>Open tasks</strong><span class="spacer"></span>
        <a class="ghost" href="ops.php#site=<?= h(urlencode($key)) ?>" style="font-size:12px">view on board →</a>
      </div>
      <div class="sp-add"><input id="quickAdd" placeholder="+ Add a <?= h($site['name']) ?> task, press Enter…"></div>
      <?php if (!$mine): ?><p class="muted" style="padding:12px">No open tasks for this site.</p><?php endif; ?>
      <?php foreach ($mine as $t): ?>
      <div class="tk">
        <a href="ops.php#task=<?= h(urlencode($t['id'])) ?>"><?= h($t['title']) ?></a>
        <?php if (!empty($t['aiTag'])): ?><span class="chip" style="--c:<?= ['ai-now'=>'#1D9E75','ai-assist'=>'#7A7FEC','human-only'=>'#6F7380'][$t['aiTag']] ?? '#6F7380' ?>">🤖 <?= h(OPS_AI_TAGS[$t['aiTag']] ?? $t['aiTag']) ?></span><?php endif; ?>
        <?php if (!empty($t['priority'])): ?><span class="chip" style="--c:<?= $priC[$t['priority']] ?? '#6F7380' ?>"><?= h(OPS_PRIORITIES[$t['priority']] ?? $t['priority']) ?></span><?php endif; ?>
        <?php if (!empty($t['revenueImpact'])): ?><span class="dots"><?= str_repeat('●', (int)$t['revenueImpact']) . str_repeat('○', 5 - (int)$t['revenueImpact']) ?></span><?php endif; ?>
        <span class="muted" style="font-size:12px"><?= h(OPS_STATUSES[$t['status']] ?? $t['status']) ?></span>
      </div>
      <?php endforeach; ?>
    </div>

    <div class="card">
      <strong>Notes</strong>
      <div style="display:flex;gap:8px;margin:10px 0"><input type="text" id="noteNew" placeholder="Write a site note…" style="flex:1;background:var(--bg);color:var(--text);border:1px solid var(--border);border-radius:8px;padding:6px 9px;font-size:13px"><button class="btn sm primary" id="noteAdd">Post</button></div>
      <div id="notes">
        <?php foreach ((array)($site['notes'] ?? []) as $n): ?>
        <div class="note"><div class="meta"><?= h($n['by'] ?? '') ?> · <?= h(substr((string)($n['ts'] ?? ''), 0, 10)) ?></div><div class="txt"><?= h($n['text'] ?? '') ?></div></div>
        <?php endforeach; ?>
        <?php if (empty($site['notes'])): ?><p class="muted" id="noNotes" style="font-size:13px">No notes yet.</p><?php endif; ?>
      </div>
    </div>
  </div>
</main>
<div class="toast" id="toast"></div>
<script>
const CSRF = <?= json_encode(csrf()) ?>, SITE = <?= json_encode($key) ?>;
const LINKS = <?= json_encode(array_values((array)($site['links'] ?? [])), JSON_HEX_TAG | JSON_HEX_AMP | JSON_UNESCAPED_UNICODE) ?>;
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function toast(m){ const t=document.getElementById('toast'); t.textContent=m; t.style.display='block'; clearTimeout(t._h); t._h=setTimeout(()=>t.style.display='none',2200); }
async function api(action, fields){
  const fd = new FormData(); fd.append('action', action); fd.append('csrf', CSRF);
  for (const [k,v] of Object.entries(fields||{})) fd.append(k, (v!==null && typeof v==='object')?JSON.stringify(v):v);
  const r = await fetch('ops-api.php', {method:'POST', body:fd}); const j = await r.json();
  if (!j.ok) toast('⚠ '+(j.error||'Failed'));
  return j;
}
document.getElementById('quickAdd').addEventListener('keydown', async e=>{
  if (e.key!=='Enter') return;
  const title = e.target.value.trim(); if (!title) return;
  const j = await api('create', {title, group:'todo', sites:[SITE]});
  if (j.ok){ toast('Task added — reloading'); setTimeout(()=>location.reload(), 500); }
});
document.getElementById('noteAdd').addEventListener('click', async ()=>{
  const inp = document.getElementById('noteNew'); const txt = inp.value.trim(); if (!txt) return;
  const j = await api('sitenote', {site:SITE, text:txt});
  if (j.ok){
    inp.value='';
    const nn = document.getElementById('noNotes'); if (nn) nn.remove();
    document.getElementById('notes').insertAdjacentHTML('afterbegin',
      `<div class="note"><div class="meta">${esc(j.note.by)} · ${esc(j.note.ts.slice(0,10))}</div><div class="txt">${esc(j.note.text)}</div></div>`);
  }
});
document.getElementById('noteNew').addEventListener('keydown', e=>{ if (e.key==='Enter') document.getElementById('noteAdd').click(); });
function editLinks(){
  const box = document.getElementById('linksEdit');
  document.getElementById('linksView').style.display='none';
  box.style.display='block';
  const rows = LINKS.map((l,i)=>`<div class="el-row"><input value="${esc(l.label)}" data-l="${i}" placeholder="label" size="14"><input value="${esc(l.url)}" data-u="${i}" placeholder="https://…" style="flex:1"></div>`).join('');
  box.innerHTML = rows + `<div class="el-row"><input id="nlLabel" placeholder="new label" size="14"><input id="nlUrl" placeholder="https://…" style="flex:1"></div>
    <div style="display:flex;gap:8px;margin-top:8px"><button class="btn sm primary" onclick="saveLinks()">Save links</button><button class="btn sm" onclick="location.reload()">Cancel</button></div>`;
}
async function saveLinks(){
  const box = document.getElementById('linksEdit');
  const out = [];
  LINKS.forEach((l,i)=>{
    const label = box.querySelector(`[data-l="${i}"]`).value.trim();
    const url   = box.querySelector(`[data-u="${i}"]`).value.trim();
    if (label) out.push({label, url});
  });
  const nl = document.getElementById('nlLabel').value.trim(), nu = document.getElementById('nlUrl').value.trim();
  if (nl) out.push({label:nl, url:nu});
  const j = await api('sitelinks', {site:SITE, links:out});
  if (j.ok){ toast('Links saved'); setTimeout(()=>location.reload(), 400); }
}
</script>
</body></html>
