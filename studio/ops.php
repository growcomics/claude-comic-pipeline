<?php
// ops.php — Command Center OPS BOARD: the Monday.com replacement.
//
// One-time import of the Monday "Operations" board (tools/monday-import.py) seeded
// data/ops-tasks.json + data/ops-updates.json; from then on THIS board is the source of
// truth for owner + Magnamus. Pure renderer in the review.php mold: PHP embeds the task
// list + site registry as JSON, vanilla JS renders groups / filter bar / task drawer /
// bulk bar, and every mutation POSTs to ops-api.php. View state lives in location.hash
// (shareable filters; ops.php#task=<id> deep-links a task drawer — site.php links here).
// Update threads are NOT embedded (≈½ MB of Monday history) — the drawer lazy-fetches
// them per task (action=updates); only per-task counts are computed server-side.
declare(strict_types=1);
require_once __DIR__ . '/inc/ops.php';
require_auth();

$data  = ops_load();
$tasks = $data['tasks'];
$sites = ops_sites();

$noteCounts = [];
foreach (s_read(OPS_UPDATES_FILE, []) as $tid => $arr) $noteCounts[$tid] = count($arr);
foreach ($tasks as &$t) $t['notes'] = $noteCounts[$t['id'] ?? ''] ?? 0;
unset($t);

$openN = 0; $critN = 0;
foreach ($tasks as $t) if (ops_open($t)) { $openN++; if (($t['priority'] ?? '') === 'critical') $critN++; }

$siteLite = [];
foreach ($sites as $k => $s) $siteLite[$k] = ['name'=>$s['name'], 'color'=>$s['color'] ?? '#6F7380', 'active'=>!empty($s['active'])];

$payload = [
    'tasks'      => $tasks,
    'sites'      => $siteLite,
    'groups'     => OPS_GROUPS,
    'statuses'   => OPS_STATUSES,
    'priorities' => OPS_PRIORITIES,
    'aiTags'     => OPS_AI_TAGS,
    'user'       => current_studio_user(),
    'csrf'       => csrf(),
];
?><!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark"><meta name="robots" content="noindex,nofollow">
<title>Ops Board · Command Center</title>
<link rel="icon" href="assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="assets/studio.css">
<style>
/* ---- ops board ---- */
.ob-filters{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:14px 0;position:sticky;top:0;z-index:5;
  background:var(--bg);padding:10px 0;border-bottom:1px solid var(--border)}
.ob-filters input[type=search]{flex:1;min-width:160px}
.ob-filters select,.ob-filters input{background:var(--surface);color:var(--text);border:1px solid var(--border);border-radius:8px;padding:6px 8px;font-size:13px}
.ob-view{display:flex;gap:0;border:1px solid var(--border);border-radius:8px;overflow:hidden}
.ob-view button{background:var(--surface);color:var(--muted);border:0;padding:6px 12px;font-size:13px;cursor:pointer}
.ob-view button.on{background:var(--accent);color:var(--accent-ink,#fff);font-weight:700}
.ob-group{margin:18px 0}
.ob-ghead{display:flex;align-items:center;gap:10px;cursor:pointer;user-select:none;padding:4px 0}
.ob-ghead h2{margin:0;font-size:15px}
.ob-ghead .n{color:var(--muted);font-size:13px}
.ob-ghead .tri{color:var(--muted);font-size:11px;width:12px}
.ob-rows{border:1px solid var(--border);border-radius:10px;overflow:hidden}
.ob-row{display:flex;align-items:center;gap:8px;padding:8px 12px;border-bottom:1px solid var(--border);background:var(--surface);flex-wrap:wrap}
.ob-row:last-child{border-bottom:0}
.ob-row:hover{background:rgba(255,255,255,.03)}
.ob-title{flex:1;min-width:220px;cursor:pointer;font-size:14px}
.ob-title:hover{text-decoration:underline}
.ob-title .arch{color:var(--muted);font-size:11px;margin-left:6px}
.pill{border-radius:999px;padding:2px 10px;font-size:12px;font-weight:700;border:1px solid transparent;cursor:pointer;background:color-mix(in srgb,var(--c) 22%,transparent);color:var(--c);border-color:color-mix(in srgb,var(--c) 45%,transparent)}
select.pill{appearance:none;-webkit-appearance:none}
.chip{border-radius:6px;padding:1px 7px;font-size:11px;font-weight:600;background:color-mix(in srgb,var(--c) 20%,transparent);color:var(--c);border:1px solid color-mix(in srgb,var(--c) 40%,transparent);white-space:nowrap}
.dots{font-size:11px;letter-spacing:1px;color:#EF9F27;white-space:nowrap}
.mut{color:var(--muted);font-size:12px;white-space:nowrap}
.ob-add{display:flex;gap:8px;padding:8px 12px;background:var(--surface);border-bottom:1px solid var(--border)}
.ob-add input{flex:1;background:var(--bg);color:var(--text);border:1px dashed var(--border);border-radius:8px;padding:6px 10px;font-size:13px}
.ob-check{width:15px;height:15px;flex:none}
/* ---- drawer ---- */
.dw-wrap{position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:40;display:none}
.dw-wrap.open{display:block}
.dw{position:fixed;top:0;right:0;bottom:0;width:min(560px,96vw);background:var(--bg);border-left:1px solid var(--border);z-index:41;
  overflow-y:auto;padding:18px 20px 40px;transform:translateX(100%);transition:transform .15s ease}
.dw-wrap.open .dw{transform:none}
.dw h2{margin:2px 0 10px;font-size:17px}
.dw label{display:block;font-size:12px;color:var(--muted);margin:12px 0 4px}
.dw input[type=text],.dw textarea,.dw select{width:100%;background:var(--surface);color:var(--text);border:1px solid var(--border);border-radius:8px;padding:7px 9px;font-size:13px;box-sizing:border-box}
.dw textarea{min-height:70px;resize:vertical}
.dw-grid{display:grid;grid-template-columns:1fr 1fr;gap:0 14px}
.dw-x{position:absolute;top:12px;right:14px;background:none;border:0;color:var(--muted);font-size:20px;cursor:pointer}
.dw-sites{display:flex;gap:6px;flex-wrap:wrap;margin-top:4px}
.dw-sites label{display:flex;align-items:center;gap:4px;margin:0;font-size:12px;border:1px solid var(--border);border-radius:999px;padding:3px 9px;cursor:pointer;color:var(--text)}
.dw-sites label.on{border-color:var(--c);color:var(--c);background:color-mix(in srgb,var(--c) 15%,transparent)}
.cl-item{display:flex;align-items:center;gap:8px;padding:3px 0;font-size:13px}
.cl-item input[type=checkbox]{flex:none}
.cl-item .t.done{text-decoration:line-through;color:var(--muted)}
.cl-item .rm{margin-left:auto;background:none;border:0;color:var(--muted);cursor:pointer}
.up{border-left:2px solid var(--border);padding:6px 10px;margin:8px 0;font-size:13px}
.up.reply{margin-left:22px}
.up.studio{border-color:var(--accent)}
.up .meta{color:var(--muted);font-size:11px;margin-bottom:3px}
.up .txt{white-space:pre-wrap;word-break:break-word}
.prov{margin-top:16px;padding-top:10px;border-top:1px solid var(--border);color:var(--muted);font-size:11px;line-height:1.7}
/* ---- bulk bar ---- */
.bb{position:fixed;left:50%;transform:translateX(-50%);bottom:14px;z-index:30;display:none;gap:8px;align-items:center;
  background:var(--surface);border:1px solid var(--accent);border-radius:12px;padding:10px 14px;box-shadow:0 6px 30px rgba(0,0,0,.5);flex-wrap:wrap;max-width:96vw}
.bb.on{display:flex}
.bb select,.bb input{background:var(--bg);color:var(--text);border:1px solid var(--border);border-radius:8px;padding:5px 8px;font-size:12px}
.toast{position:fixed;bottom:16px;right:16px;background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:10px 14px;font-size:13px;z-index:60;display:none}
</style></head><body>
<header class="topbar">
  <div class="brand"><a href="cc.php" style="color:inherit;text-decoration:none"><span class="dot"></span> ⌘ Command Center</a></div>
  <a class="ghost" href="cc.php">Home</a>
  <a class="ghost" href="ops.php" style="color:var(--text);font-weight:700">📋 Ops Board</a>
  <a class="ghost" href="index.php">🎬 Pipeline</a>
  <span class="spacer"></span>
  <span class="ghost"><?= h(current_studio_user()) ?></span>
  <a class="ghost" href="login.php?do=logout">Log out</a>
</header>
<main class="wrap">
  <div class="pagehead"><h1>Ops Board <span class="muted"><?= $openN ?> open<?= $critN ? ' · ' . $critN . ' critical' : '' ?></span></h1></div>

  <div class="ob-filters" id="filters">
    <div class="ob-view" id="viewTabs"></div>
    <input type="search" id="fSearch" placeholder="Search tasks…">
    <select id="fSite"></select>
    <select id="fPerson"></select>
    <select id="fStatus"></select>
    <select id="fPriority"></select>
    <select id="fAi"></select>
    <select id="fBatch"></select>
    <select id="fSort">
      <option value="manual">Sort: board order</option>
      <option value="priority">Sort: priority</option>
      <option value="revenue">Sort: revenue impact</option>
      <option value="updated">Sort: recently updated</option>
      <option value="created">Sort: newest</option>
    </select>
    <button class="btn sm" id="bulkToggle">☑ Bulk</button>
  </div>

  <div id="board"></div>
</main>

<div class="bb" id="bulkBar">
  <strong id="bbCount">0 selected</strong>
  <select id="bbAi"></select>
  <input id="bbBatch" placeholder="batch label" size="10">
  <select id="bbStatus"></select>
  <select id="bbGroup"></select>
  <button class="btn sm primary" id="bbApply">Apply</button>
  <button class="btn sm" id="bbArchive">Archive</button>
  <button class="btn sm" id="bbClear">✕</button>
</div>

<div class="dw-wrap" id="dwWrap"><div class="dw" id="dw"></div></div>
<div class="toast" id="toast"></div>

<script>
const OPS = <?= json_encode($payload, JSON_HEX_TAG | JSON_HEX_AMP | JSON_UNESCAPED_UNICODE) ?>;
const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const STATUS_C = {notstarted:'#6F7380', working:'#EF9F27', confirm:'#C678DD', onhold:'#5BA7E6', done:'#1D9E75', cancelled:'#D9534F'};
const PRI_C    = {critical:'#D9534F', high:'#EF9F27', medium:'#5BA7E6', low:'#6F7380'};
const AI_C     = {'ai-now':'#1D9E75', 'ai-assist':'#7A7FEC', 'human-only':'#6F7380'};
const GROUP_ORDER = ['todo','onhold','done','cancelled'];

let state = {view:'open', q:'', site:'', person:'', status:'', priority:'', ai:'', batch:'', sort:'manual', task:'', bulk:false};
let selected = new Set();
let collapsed = new Set(['done','cancelled']);

function toast(m){ const t=$('#toast'); t.textContent=m; t.style.display='block'; clearTimeout(t._h); t._h=setTimeout(()=>t.style.display='none',2200); }
async function api(action, fields){
  const fd = new FormData();
  fd.append('action', action); fd.append('csrf', OPS.csrf);
  for (const [k,v] of Object.entries(fields||{})) fd.append(k, (v!==null && typeof v==='object') ? JSON.stringify(v) : v);
  try {
    const r = await fetch('ops-api.php', {method:'POST', body:fd});
    const j = await r.json();
    if (!j.ok) toast('⚠ ' + (j.error||'Failed'));
    return j;
  } catch(e){ toast('⚠ Network error'); return {ok:false}; }
}
const taskById = id => OPS.tasks.find(t=>t.id===id);
const fmtDay = iso => (iso||'').slice(0,10);

/* ---- hash state (shareable views / deep links) ---- */
function writeHash(){
  const p = new URLSearchParams();
  for (const k of ['view','q','site','person','status','priority','ai','batch','sort']) if (state[k] && !(k==='view'&&state[k]==='open') && !(k==='sort'&&state[k]==='manual')) p.set(k, state[k]);
  if (state.task) p.set('task', state.task);
  const s = p.toString();
  history.replaceState(null,'', s ? '#'+s : location.pathname);
}
function readHash(){
  const p = new URLSearchParams(location.hash.slice(1));
  for (const k of ['view','q','site','person','status','priority','ai','batch','sort','task']) if (p.has(k)) state[k]=p.get(k);
  if (!['open','all','archived'].includes(state.view)) state.view='open';
}

/* ---- filtering ---- */
function visibleTasks(){
  const q = state.q.toLowerCase();
  return OPS.tasks.filter(t=>{
    if (state.view==='archived'){ if(!t.archived) return false; }
    else if (t.archived) return false;
    if (state.view==='open' && !(['todo','onhold'].includes(t.group) && !['done','cancelled'].includes(t.status))) return false;
    if (q && !((t.title||'').toLowerCase().includes(q) || (t.body||'').toLowerCase().includes(q) || (t.aiPlan||'').toLowerCase().includes(q))) return false;
    if (state.site && !(t.sites||[]).includes(state.site)) return false;
    if (state.person && !(t.person||[]).includes(state.person)) return false;
    if (state.status && t.status!==state.status) return false;
    if (state.priority && t.priority!==state.priority) return false;
    if (state.ai && (t.aiTag||'')!==state.ai) return false;
    if (state.batch && (t.batch||'')!==state.batch) return false;
    return true;
  });
}
const PRI_RANK = {critical:0, high:1, medium:2, low:3, '':4};
function sortTasks(arr){
  const s = state.sort;
  return arr.slice().sort((a,b)=>{
    if (s==='priority') return (PRI_RANK[a.priority??'']??4)-(PRI_RANK[b.priority??'']??4) || (b.revenueImpact||0)-(a.revenueImpact||0);
    if (s==='revenue')  return (b.revenueImpact||0)-(a.revenueImpact||0);
    if (s==='updated')  return (b.updated||'').localeCompare(a.updated||'');
    if (s==='created')  return (b.created||'').localeCompare(a.created||'');
    return (a.sort||0)-(b.sort||0);
  });
}

/* ---- board render ---- */
function rowHtml(t){
  const st = esc(t.status), sc = STATUS_C[t.status]||'#6F7380';
  const opts = Object.entries(OPS.statuses).map(([k,v])=>`<option value="${k}"${k===t.status?' selected':''}>${esc(v)}</option>`).join('');
  const siteChips = (t.sites||[]).map(k=>{const s=OPS.sites[k]; return s?`<span class="chip" style="--c:${s.color}">${esc(s.name)}</span>`:'';}).join('');
  const persons = (t.person||[]).map(p=>`<span class="chip" style="--c:#9aa0b4">${esc(p)}</span>`).join('');
  const pri = t.priority ? `<span class="chip" style="--c:${PRI_C[t.priority]||'#6F7380'}">${esc(OPS.priorities[t.priority]||t.priority)}</span>` : '';
  const ai  = t.aiTag ? `<span class="chip" style="--c:${AI_C[t.aiTag]||'#6F7380'}">🤖 ${esc(OPS.aiTags[t.aiTag]||t.aiTag)}</span>` : '';
  const batch = t.batch ? `<span class="chip" style="--c:#C678DD">⛁ ${esc(t.batch)}</span>` : '';
  const rev = t.revenueImpact ? `<span class="dots" title="revenue impact ${t.revenueImpact}/5">${'●'.repeat(t.revenueImpact)}${'○'.repeat(5-t.revenueImpact)}</span>` : '';
  const cl = (t.checklist&&t.checklist.length) ? `<span class="mut">☑ ${t.checklist.filter(c=>c.done).length}/${t.checklist.length}</span>` : '';
  const notes = t.notes ? `<span class="mut">💬 ${t.notes}</span>` : '';
  const cb = state.bulk ? `<input type="checkbox" class="ob-check" data-sel="${t.id}"${selected.has(t.id)?' checked':''}>` : '';
  return `<div class="ob-row" data-id="${t.id}">${cb}
    <span class="ob-title" data-open="${t.id}">${esc(t.title)}${t.archived?'<span class="arch">archived</span>':''}</span>
    ${ai}${batch}${pri}${rev}${cl}${siteChips}${persons}${notes}
    <select class="pill" style="--c:${sc}" data-status="${t.id}" title="status">${opts}</select>
    <span class="mut">${fmtDay(t.updated)}</span></div>`;
}
function render(){
  const vis = visibleTasks();
  const byGroup = {};
  vis.forEach(t=>{ (byGroup[t.group]=byGroup[t.group]||[]).push(t); });
  let html = '';
  for (const g of GROUP_ORDER){
    const arr = sortTasks(byGroup[g]||[]);
    if (!arr.length && !(g==='todo' && state.view!=='archived')) continue;
    const open = !collapsed.has(g);
    html += `<section class="ob-group"><div class="ob-ghead" data-g="${g}"><span class="tri">${open?'▼':'▶'}</span><h2>${esc(OPS.groups[g]||g)}</h2><span class="n">${arr.length}</span></div>`;
    if (open){
      html += '<div class="ob-rows">';
      if (g==='todo' && state.view!=='archived') html += `<div class="ob-add"><input id="quickAdd" placeholder="+ Add a task and press Enter…"></div>`;
      html += arr.map(rowHtml).join('') || '';
      html += '</div>';
    }
    html += '</section>';
  }
  $('#board').innerHTML = html || '<p class="muted">Nothing matches.</p>';
  $('#bbCount').textContent = selected.size + ' selected';
  $('#bulkBar').classList.toggle('on', state.bulk && selected.size>0);
}

/* ---- filter bar ---- */
function fillSelect(el, label, entries, cur){
  el.innerHTML = `<option value="">${label}</option>` + entries.map(([k,v])=>`<option value="${esc(k)}"${k===cur?' selected':''}>${esc(v)}</option>`).join('');
}
function renderFilters(){
  $('#viewTabs').innerHTML = ['open','all','archived'].map(v=>`<button data-view="${v}" class="${state.view===v?'on':''}">${v[0].toUpperCase()+v.slice(1)}</button>`).join('');
  fillSelect($('#fSite'), 'Site: all', Object.entries(OPS.sites).map(([k,s])=>[k,s.name]), state.site);
  const persons = [...new Set(OPS.tasks.flatMap(t=>t.person||[]))].sort();
  fillSelect($('#fPerson'), 'Person: all', persons.map(p=>[p,p]), state.person);
  fillSelect($('#fStatus'), 'Status: all', Object.entries(OPS.statuses), state.status);
  fillSelect($('#fPriority'), 'Priority: all', Object.entries(OPS.priorities).filter(([k])=>k), state.priority);
  fillSelect($('#fAi'), 'AI tag: all', Object.entries(OPS.aiTags).filter(([k])=>k), state.ai);
  const batches = [...new Set(OPS.tasks.map(t=>t.batch).filter(Boolean))].sort();
  fillSelect($('#fBatch'), 'Batch: all', batches.map(b=>[b,b]), state.batch);
  $('#fSort').value = state.sort;
  $('#fSearch').value = state.q;
  fillSelect($('#bbAi'), 'AI tag…', Object.entries(OPS.aiTags).filter(([k])=>k), '');
  fillSelect($('#bbStatus'), 'Status…', Object.entries(OPS.statuses), '');
  fillSelect($('#bbGroup'), 'Group…', Object.entries(OPS.groups), '');
}

/* ---- drawer ---- */
let dwId = '';
function drawerHtml(t){
  const sel = (name, entries, cur) => `<select data-f="${name}">` + entries.map(([k,v])=>`<option value="${esc(k)}"${String(k)===String(cur)?' selected':''}>${esc(v)}</option>`).join('') + '</select>';
  const sitesHtml = Object.entries(OPS.sites).map(([k,s])=>{
    const on = (t.sites||[]).includes(k);
    return `<label class="${on?'on':''}" style="--c:${s.color}"><input type="checkbox" data-site="${k}"${on?' checked':''} hidden>${esc(s.name)}</label>`;
  }).join('');
  const cl = (t.checklist||[]).map((c,i)=>`<div class="cl-item"><input type="checkbox" data-cl="${i}"${c.done?' checked':''}><span class="t ${c.done?'done':''}">${esc(c.text)}</span><button class="rm" data-clrm="${i}" title="remove">✕</button></div>`).join('');
  return `<button class="dw-x" id="dwClose">✕</button>
  <h2 style="padding-right:30px">${esc(t.title)}</h2>
  <label>Title</label><input type="text" data-f="title" value="${esc(t.title)}">
  <div class="dw-grid">
    <div><label>Group</label>${sel('group', Object.entries(OPS.groups), t.group)}</div>
    <div><label>Status</label>${sel('status', Object.entries(OPS.statuses), t.status)}</div>
    <div><label>Priority</label>${sel('priority', Object.entries(OPS.priorities), t.priority||'')}</div>
    <div><label>Revenue impact</label>${sel('revenueImpact', [0,1,2,3,4,5].map(n=>[n, n? '●'.repeat(n)+'○'.repeat(5-n)+' '+n : '—']), t.revenueImpact||0)}</div>
    <div><label>AI tag</label>${sel('aiTag', Object.entries(OPS.aiTags), t.aiTag||'')}</div>
    <div><label>Batch</label><input type="text" data-f="batch" value="${esc(t.batch||'')}" placeholder="batch label"></div>
  </div>
  <label>Sites</label><div class="dw-sites" id="dwSites">${sitesHtml}</div>
  <label>People (comma-separated)</label><input type="text" data-f="person" value="${esc((t.person||[]).join(', '))}">
  <label>Details / body</label><textarea data-f="body">${esc(t.body||'')}</textarea>
  <label>AI plan (how AI would complete this)</label><textarea data-f="aiPlan">${esc(t.aiPlan||'')}</textarea>
  <label>Checklist</label><div id="dwCl">${cl}</div>
  <div style="display:flex;gap:8px;margin-top:6px"><input type="text" id="clNew" placeholder="+ checklist item, press Enter" style="flex:1"></div>
  <div style="display:flex;gap:8px;margin-top:16px">
    <button class="btn sm" id="dwArchive">${t.archived?'♻ Unarchive':'🗄 Archive'}</button>
  </div>
  <label>Updates</label><div id="dwUpdates" class="muted" style="font-size:12px">Loading…</div>
  <div style="display:flex;gap:8px;margin-top:8px"><input type="text" id="noteNew" placeholder="Write a note…" style="flex:1"><button class="btn sm primary" id="noteAdd">Post</button></div>
  <div class="prov">
    ${t.mondayId?`Monday ID ${esc(t.mondayId)} · `:''}${t.creationLog?esc(t.creationLog)+' · ':''}created ${fmtDay(t.created)}${t.completedOn?' · completed '+fmtDay(t.completedOn):''}
  </div>`;
}
function updatesHtml(arr){
  if (!arr.length) return '<span class="muted">No updates yet.</span>';
  return arr.map(u=>`<div class="up ${u.parent?'reply':''} ${u.src==='studio'?'studio':''}">
    <div class="meta">${esc(u.by||'?')} · ${fmtDay(u.ts)}${u.src==='monday'?' · <span title="imported from Monday.com">Ⓜ</span>':''}${u.likes?` · 👍${u.likes}`:''}</div>
    <div class="txt">${esc(u.text)}</div></div>`).join('');
}
async function openDrawer(id){
  const t = taskById(id); if (!t) return;
  dwId = id; state.task = id; writeHash();
  $('#dw').innerHTML = drawerHtml(t);
  $('#dwWrap').classList.add('open');
  const j = await api('updates', {id});
  if (dwId === id && j.ok) $('#dwUpdates').innerHTML = updatesHtml(j.updates||[]);
}
function closeDrawer(){ dwId=''; state.task=''; writeHash(); $('#dwWrap').classList.remove('open'); }
async function patchTask(id, patch){
  const j = await api('update', {id, patch});
  if (j.ok && j.task){ const i = OPS.tasks.findIndex(x=>x.id===id); if (i>=0) { j.task.notes = OPS.tasks[i].notes; OPS.tasks[i]=j.task; } render(); }
  return j;
}

/* ---- events ---- */
document.addEventListener('click', async e=>{
  const g = e.target.closest('[data-g]'); if (g){ const k=g.dataset.g; collapsed.has(k)?collapsed.delete(k):collapsed.add(k); render(); return; }
  const o = e.target.closest('[data-open]'); if (o){ openDrawer(o.dataset.open); return; }
  const vb = e.target.closest('[data-view]'); if (vb){ state.view=vb.dataset.view; if(state.view!=='open'){collapsed.delete('done');collapsed.delete('cancelled');} writeHash(); renderFilters(); render(); return; }
  if (e.target.id==='dwClose' || e.target.id==='dwWrap') closeDrawer();
});
$('#dwWrap').addEventListener('click', e=>{ if (e.target.id==='dwWrap') closeDrawer(); });
document.addEventListener('keydown', e=>{ if (e.key==='Escape' && dwId) closeDrawer(); });

document.addEventListener('change', async e=>{
  const st = e.target.closest('[data-status]');
  if (st){ await patchTask(st.dataset.status, {status: st.value}); return; }
  const cb = e.target.closest('[data-sel]');
  if (cb){ cb.checked ? selected.add(cb.dataset.sel) : selected.delete(cb.dataset.sel); render(); return; }
  if (!dwId) return;
  const t = taskById(dwId);
  const f = e.target.closest('[data-f]');
  if (f){
    const name = f.dataset.f;
    let val = f.value;
    if (name==='person') val = val.split(',').map(s=>s.trim()).filter(Boolean);
    if (name==='revenueImpact') val = parseInt(val,10)||0;
    await patchTask(dwId, {[name]: val});
    if (name==='title') $('#dw h2').textContent = val;
    return;
  }
  const siteCb = e.target.closest('[data-site]');
  if (siteCb){
    const k = siteCb.dataset.site;
    const cur = new Set(t.sites||[]);
    siteCb.checked ? cur.add(k) : cur.delete(k);
    await patchTask(dwId, {sites:[...cur]});
    $('#dw').innerHTML = drawerHtml(taskById(dwId));
    api('updates',{id:dwId}).then(j=>{ if(j.ok && dwId) $('#dwUpdates').innerHTML = updatesHtml(j.updates||[]); });
    return;
  }
  const clCb = e.target.closest('[data-cl]');
  if (clCb){
    const cl = (t.checklist||[]).slice();
    cl[+clCb.dataset.cl].done = clCb.checked;
    await patchTask(dwId, {checklist: cl});
    const row = clCb.closest('.cl-item');
    if (row) row.querySelector('.t').classList.toggle('done', clCb.checked);
    return;
  }
});

document.addEventListener('click', async e=>{
  if (!dwId) return;
  const rm = e.target.closest('[data-clrm]');
  if (rm){
    const t = taskById(dwId);
    const cl = (t.checklist||[]).slice(); cl.splice(+rm.dataset.clrm,1);
    await patchTask(dwId, {checklist: cl});
    $('#dw').innerHTML = drawerHtml(taskById(dwId));
    api('updates',{id:dwId}).then(j=>{ if(j.ok && dwId) $('#dwUpdates').innerHTML = updatesHtml(j.updates||[]); });
    return;
  }
  if (e.target.id==='dwArchive'){
    const t = taskById(dwId);
    const j = await api('archive', {id: dwId, on: t.archived?0:1});
    if (j.ok){ t.archived = !t.archived; t.updated = new Date().toISOString(); render(); $('#dw').innerHTML = drawerHtml(t); api('updates',{id:dwId}).then(x=>{ if(x.ok&&dwId) $('#dwUpdates').innerHTML=updatesHtml(x.updates||[]); }); toast(t.archived?'Archived':'Unarchived'); }
    return;
  }
  if (e.target.id==='noteAdd'){
    const inp = $('#noteNew'); const txt = inp.value.trim(); if (!txt) return;
    const j = await api('note', {id: dwId, text: txt});
    if (j.ok){ inp.value=''; const t=taskById(dwId); t.notes=(t.notes||0)+1; const cur=$('#dwUpdates').innerHTML; $('#dwUpdates').innerHTML = (cur.includes('No updates')?'':cur) + updatesHtml([j.note]); render(); }
    return;
  }
});

document.addEventListener('keydown', async e=>{
  if (e.key!=='Enter') return;
  if (e.target.id==='quickAdd'){
    const title = e.target.value.trim(); if (!title) return;
    const fields = {title, group:'todo'};
    if (state.site) fields.sites = [state.site];
    const j = await api('create', fields);
    if (j.ok){ j.task.notes=0; OPS.tasks.unshift(j.task); render(); const qa=$('#quickAdd'); if(qa){qa.focus();} toast('Task added'); }
    return;
  }
  if (e.target.id==='clNew' && dwId){
    const txt = e.target.value.trim(); if (!txt) return;
    const t = taskById(dwId);
    const cl = (t.checklist||[]).concat([{text:txt, done:false}]);
    const j = await patchTask(dwId, {checklist: cl});
    if (j.ok){ $('#dw').innerHTML = drawerHtml(taskById(dwId)); $('#clNew').focus(); api('updates',{id:dwId}).then(x=>{ if(x.ok&&dwId) $('#dwUpdates').innerHTML=updatesHtml(x.updates||[]); }); }
    return;
  }
  if (e.target.id==='noteNew' && dwId){ $('#noteAdd').click(); return; }
});

let qT;
$('#fSearch').addEventListener('input', e=>{ clearTimeout(qT); qT=setTimeout(()=>{ state.q=e.target.value; writeHash(); render(); },200); });
for (const [elId, key] of [['fSite','site'],['fPerson','person'],['fStatus','status'],['fPriority','priority'],['fAi','ai'],['fBatch','batch'],['fSort','sort']])
  $('#'+elId).addEventListener('change', e=>{ state[key]=e.target.value; writeHash(); render(); });

$('#bulkToggle').addEventListener('click', ()=>{ state.bulk=!state.bulk; if(!state.bulk) selected.clear(); $('#bulkToggle').classList.toggle('primary', state.bulk); render(); });
$('#bbClear').addEventListener('click', ()=>{ selected.clear(); render(); });
$('#bbApply').addEventListener('click', async ()=>{
  const patch = {};
  if ($('#bbAi').value) patch.aiTag = $('#bbAi').value;
  if ($('#bbBatch').value.trim()) patch.batch = $('#bbBatch').value.trim();
  if ($('#bbStatus').value) patch.status = $('#bbStatus').value;
  if ($('#bbGroup').value) patch.group = $('#bbGroup').value;
  if (!Object.keys(patch).length) return toast('Pick something to set');
  const j = await api('bulk', {ids:[...selected], patch});
  if (j.ok){
    for (const id of selected){ const t=taskById(id); if (t) Object.assign(t, patch, {updated:new Date().toISOString()}); }
    toast('Updated '+j.updated); selected.clear(); render(); renderFilters();
  }
});
$('#bbArchive').addEventListener('click', async ()=>{
  let n=0;
  for (const id of [...selected]){ const r = await api('archive', {id, on:1}); if (r.ok){ const t=taskById(id); if(t) t.archived=true; n++; } }
  toast('Archived '+n); selected.clear(); render();
});

/* ---- boot ---- */
readHash();
renderFilters();
render();
if (state.task) openDrawer(state.task);
</script>
</body></html>
