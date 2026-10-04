<?php
// attribution.php — 🧭 ATTRIBUTION: cross-property multi-touch attribution rollup.
//
// Companion to the ATS v5 WordPress plugin (Attribution Tracking System v5,
// first deployed on growgettercomics.com 2026-07-09). Each WP property exposes a
// key-gated aggregate endpoint /wp-json/ats/v1/rollup (NO PII — source sequences
// and dollar totals only). This page:
//   - do=sync (POST, session or bridge-key): pulls every site in
//     data/attribution-sites.json and stores data/attribution/<site>.json
//   - renders: per-site funnel cards, source × model credit table with a model
//     switcher (first/last/linear/U-shaped/time-decay), model-comparison matrix,
//     patron journey explorer, and monthly traffic trend — all dependency-free.
// Standalone file (low clobber risk). Only shared-file touch: one cc.php tile.
// Site configs (incl. rollup keys) live under data/ which is .htaccess-denied.
declare(strict_types=1);
require_once __DIR__ . '/inc/boot.php';

define('ATTR_SITES_FILE', SDATA . '/attribution-sites.json');
define('ATTR_DIR', SDATA . '/attribution');

// bridge key fallback (same trust model as bridge.php / growgetter.php) so a
// headless session can trigger the daily sync without a browser login.
function attr_bridge_ok(): bool {
    $k = (string)($_POST['key'] ?? ($_GET['key'] ?? ''));
    if ($k === '') return false;
    $cfg = s_read(SDATA . '/bridge.json', []);
    $real = (string)($cfg['key'] ?? '');
    return $real !== '' && hash_equals($real, $k);
}

$isBridge = attr_bridge_ok();
if (!$isBridge) require_auth();

// ---- do=sync: pull every configured site's rollup ---------------------------
if (($_REQUEST['do'] ?? '') === 'sync') {
    header('Content-Type: application/json');
    if (!$isBridge) { if (!csrf_ok()) { echo json_encode(['ok'=>false,'error'=>'bad csrf']); exit; } }
    $sites = s_read(ATTR_SITES_FILE, []);
    if (!$sites) { echo json_encode(['ok'=>false,'error'=>'no sites configured in data/attribution-sites.json']); exit; }
    if (!is_dir(ATTR_DIR)) @mkdir(ATTR_DIR, 0755, true);
    $out = ['ok'=>true,'synced'=>[],'errors'=>[]];
    foreach ($sites as $key => $s) {
        if (empty($s['rollup']) || empty($s['key'])) { $out['errors'][$key] = 'missing rollup url or key'; continue; }
        $url = $s['rollup'] . (strpos($s['rollup'],'?')!==false ? '&' : '?')
             . 'months=' . (int)($s['months'] ?? 12) . '&key=' . rawurlencode($s['key']);
        $ch = curl_init($url);
        curl_setopt_array($ch, [CURLOPT_RETURNTRANSFER=>true, CURLOPT_TIMEOUT=>90,
            CURLOPT_CONNECTTIMEOUT=>15, CURLOPT_FOLLOWLOCATION=>true, CURLOPT_USERAGENT=>'studio-ats-sync/1.0']);
        $body = curl_exec($ch);
        $code = (int)curl_getinfo($ch, CURLINFO_RESPONSE_CODE);
        $err  = curl_error($ch);
        curl_close($ch);
        if ($body === false || $code !== 200) { $out['errors'][$key] = "HTTP $code $err"; continue; }
        $j = json_decode((string)$body, true);
        if (!is_array($j) || !isset($j['models'])) { $out['errors'][$key] = 'bad payload'; continue; }
        $j['_synced_at'] = time();
        $j['_site_key'] = $key;
        $j['_site_name'] = (string)($s['name'] ?? $key);
        s_write(ATTR_DIR . '/' . preg_replace('/[^a-z0-9_-]/','',$key) . '.json', $j);
        $out['synced'][] = $key;
    }
    if ($out['errors'] && !$out['synced']) $out['ok'] = false;
    echo json_encode($out); exit;
}

// ---- load synced data --------------------------------------------------------
$sitesCfg = s_read(ATTR_SITES_FILE, []);
$data = [];
if (is_dir(ATTR_DIR)) {
    foreach (glob(ATTR_DIR . '/*.json') as $f) {
        $j = s_read($f, null);
        if (is_array($j) && isset($j['models'])) $data[basename($f, '.json')] = $j;
    }
}
?><!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark"><meta name="robots" content="noindex,nofollow">
<title>Attribution — Command Center</title>
<link rel="icon" href="assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="assets/studio.css">
<style>
.at-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:12px;margin:14px 0}
.at-tile{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:14px}
.at-tile h4{margin:0 0 6px;font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}
.at-tile .big{font-size:22px;font-weight:800}
.at-tile .sub{color:var(--muted);font-size:11px;margin-top:4px}
.at-card{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:16px;margin:14px 0}
.at-card h2{margin:0 0 4px;font-size:15px}
.at-card .hint{color:var(--muted);font-size:12px;margin:0 0 12px}
.at-table{width:100%;border-collapse:collapse;font-size:13px}
.at-table th,.at-table td{padding:7px 10px;text-align:left;border-bottom:1px solid var(--border)}
.at-table th{font-size:10px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}
.at-table td.num,.at-table th.num{text-align:right;font-variant-numeric:tabular-nums}
.at-badge{display:inline-block;padding:2px 8px;border-radius:999px;font-size:10px;border:1px solid var(--border);color:var(--muted)}
.at-badge.search{border-color:#2c7a4b;color:#5fd38d}.at-badge.social{border-color:#2b5f8f;color:#6fb6ff}
.at-badge.referral{border-color:#8a6d1a;color:#e8c554}.at-badge.direct{border-color:#555;color:#aaa}
.at-badge.paid{border-color:#8f2b3d;color:#ff7f96}.at-badge.affiliate{border-color:#22757a;color:#59d3da}
.at-badge.other{border-color:#4a4a5a;color:#9aa}
.at-jseq{display:flex;flex-wrap:wrap;gap:4px;align-items:center}
.at-jarrow{color:var(--muted);font-size:10px}
.at-bar{height:8px;border-radius:4px;background:var(--accent);opacity:.75;min-width:2px}
.at-ctl{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin:14px 0}
.at-ctl select{background:var(--surface);color:var(--text);border:1px solid var(--border);border-radius:8px;padding:7px 10px}
.at-note{color:var(--muted);font-size:12px}
.at-empty{padding:40px;text-align:center;color:var(--muted)}
button.btn{background:var(--accent);color:#fff;border:0;border-radius:8px;padding:8px 14px;cursor:pointer;font-weight:700}
button.btn.ghost2{background:transparent;border:1px solid var(--border);color:var(--text);font-weight:500}
</style><!-- the one bar across every system: ⌂ back to the hub, and a menu of everything else. Source: /hub/nav.js -->
<script src="https://3dmusclecomics.com/hub/nav.js"></script>
</head><body>
<header class="topbar">
  <div class="brand"><span class="dot"></span> 🧭 Attribution</div>
  <a class="ghost" href="cc.php">⌘ Command Center</a>
  <a class="ghost" href="ops.php">📋 Ops Board</a>
  <a class="ghost" href="analytics.php">📊 Site Traffic</a>
  <a class="ghost" href="pulse/">📈 Patron Analytics</a>
  <a class="ghost" href="nightshift.php">🌙 Night Shift</a>
  <span class="spacer"></span>
  <span class="ghost"><?= h(current_studio_user()) ?></span>
  <a class="ghost" href="login.php?do=logout">Log out</a>
</header>
<main class="wrap">
  <div class="pagehead"><h1>Multi-Touch Attribution</h1></div>
  <p class="at-note">Where the money actually comes from — every patron's full journey (not just last click),
  credited under five attribution models. Fed by the ATS v5 plugin on each property; aggregates only, no PII ever leaves a site.</p>

  <div class="at-ctl">
    <label class="at-note">Site</label><select id="siteSel"></select>
    <label class="at-note">Model</label>
    <select id="modelSel">
      <option value="ushape" selected>U-shaped (40/20/40)</option>
      <option value="first">First-touch</option>
      <option value="last">Last-touch</option>
      <option value="linear">Linear</option>
      <option value="decay">Time-decay (7d half-life)</option>
    </select>
    <button class="btn ghost2" id="syncBtn">↻ Sync now</button>
    <span class="at-note" id="syncNote"></span>
  </div>

  <div id="content"></div>
  <?php if (!$data): ?>
  <div class="at-card"><div class="at-empty">No attribution data synced yet — hit <strong>↻ Sync now</strong>.<br>
  Sites configured: <?= count($sitesCfg) ?> (data/attribution-sites.json)</div></div>
  <?php endif; ?>
</main>
<script>
const ATTR = <?= json_encode($data, JSON_UNESCAPED_SLASHES) ?>;
const CSRF = "<?= h(csrf()) ?>";
const MODELS = {first:'First-touch', last:'Last-touch', linear:'Linear', ushape:'U-shaped', decay:'Time-decay'};
const esc = s => { const d = document.createElement('div'); d.textContent = String(s==null?'':s); return d.innerHTML; };
const fmt = n => Number(n||0).toLocaleString();
const usd = (n,dec=2) => '$' + Number(n||0).toFixed(dec).replace(/\B(?=(\d{3})+(?!\d))/g, ',');

function srcInfo(site, sid){ const s = (site.sources||{})[sid]; return s || {name:'#'+sid, slug:'', type:'other'}; }

function render(){
  const keys = Object.keys(ATTR);
  const sel = document.getElementById('siteSel');
  if (!keys.length) { sel.innerHTML='<option>—</option>'; return; }
  const sk = sel.value && ATTR[sel.value] ? sel.value : keys[0];
  sel.innerHTML = keys.map(k=>`<option value="${esc(k)}"${k===sk?' selected':''}>${esc(ATTR[k]._site_name||k)}</option>`).join('');
  const site = ATTR[sk];
  const model = document.getElementById('modelSel').value;
  const ov = site.overview||{};
  const totals = (site.totals||{})[model]||{};
  const synced = site._synced_at ? new Date(site._synced_at*1000).toLocaleString() : '?';

  let html = `<div class="at-grid">
    <div class="at-tile"><h4>Visitors · 30d</h4><div class="big">${fmt(ov.visitors_30d)}</div><div class="sub">${fmt(ov.sessions_30d)} sessions</div></div>
    <div class="at-tile"><h4>Registrations</h4><div class="big">${fmt(ov.regs_30d)}</div><div class="sub">30d · ${fmt(ov.regs_total)} all-time</div></div>
    <div class="at-tile"><h4>Active patrons</h4><div class="big">${fmt(ov.subs)}</div><div class="sub">via Patreon sync</div></div>
    <div class="at-tile"><h4>Monthly $</h4><div class="big">${usd(ov.monthly)}</div><div class="sub">active pledges</div></div>
    <div class="at-tile"><h4>Lifetime $</h4><div class="big">${usd(ov.lifetime,0)}</div><div class="sub">active patrons · all-time credited ${usd((totals.rev_l||0),0)}</div></div>
    <div class="at-tile"><h4>Store $ (Woo)</h4><div class="big">${usd(ov.woo_total)}</div><div class="sub">attributed orders</div></div>
  </div>`;

  // ---- source table under selected model
  const mm = (site.models||{})[model]||{};
  const rows = Object.entries(mm).map(([sid,d])=>({sid, s:srcInfo(site,sid), d}))
    .filter(r => (r.d.regs||0)>=0.05 || (r.d.subs||0)>=0.05 || (r.d.rev_l||0)>=0.5 || (r.d.rev_woo||0)>=0.5)
    .sort((a,b)=>((b.d.rev_l||0)+(b.d.rev_m||0)*10)-((a.d.rev_l||0)+(a.d.rev_m||0)*10)||(b.d.regs||0)-(a.d.regs||0));
  html += `<div class="at-card"><h2>Sources under ${MODELS[model]}</h2>
    <p class="hint">Fractional credit across each converting visitor's full session journey · computed ${esc(synced)}</p>
    <div style="overflow-x:auto"><table class="at-table"><thead><tr><th>Source</th><th>Type</th><th class="num">Regs</th><th class="num">Subs</th><th class="num">Monthly $</th><th class="num">Lifetime $</th><th class="num">Woo $</th></tr></thead><tbody>`;
  rows.forEach(r => {
    html += `<tr><td><strong>${esc(r.s.name)}</strong></td><td><span class="at-badge ${esc(r.s.type)}">${esc(r.s.type)}</span></td>
      <td class="num">${(r.d.regs||0).toFixed(1)}</td><td class="num">${(r.d.subs||0).toFixed(2)}</td>
      <td class="num">${usd(r.d.rev_m)}</td><td class="num">${usd(r.d.rev_l,0)}</td><td class="num">${usd(r.d.rev_woo)}</td></tr>`;
  });
  html += rows.length ? '' : '<tr><td colspan="7" class="at-empty">no attributed conversions yet</td></tr>';
  html += `</tbody></table></div></div>`;

  // ---- model comparison (monthly $)
  const sids = {};
  Object.keys(MODELS).forEach(m => { const mo=(site.models||{})[m]||{}; Object.keys(mo).forEach(sid=>{ if((mo[sid].rev_m||0)>0.005||(mo[sid].rev_l||0)>0.5) sids[sid]=1; }); });
  const cmp = Object.keys(sids).map(sid => { let best=0; Object.keys(MODELS).forEach(m=>{ const v=(((site.models||{})[m]||{})[sid]||{}).rev_m||0; if(v>best)best=v; }); return [sid,best]; })
    .sort((a,b)=>b[1]-a[1]).slice(0,20);
  html += `<div class="at-card"><h2>Model comparison — monthly $ by source</h2>
    <p class="hint">Channels that START journeys shine under first-touch/U-shaped; channels that CLOSE them shine under last-touch. Big gaps = money hiding behind "Direct".</p>
    <div style="overflow-x:auto"><table class="at-table"><thead><tr><th>Source</th>${Object.values(MODELS).map(n=>`<th class="num">${n}</th>`).join('')}</tr></thead><tbody>`;
  cmp.forEach(([sid]) => {
    const s = srcInfo(site,sid);
    html += `<tr><td><strong>${esc(s.name)}</strong></td>` + Object.keys(MODELS).map(m => {
      const v = (((site.models||{})[m]||{})[sid]||{}).rev_m||0;
      return `<td class="num">${usd(v)}</td>`;
    }).join('') + '</tr>';
  });
  html += cmp.length ? '' : '<tr><td colspan="6" class="at-empty">no revenue attributed yet</td></tr>';
  html += `</tbody></table></div></div>`;

  // ---- journeys
  const js = (site.journeys||[]).slice(0,60);
  html += `<div class="at-card"><h2>Patron journeys</h2>
    <p class="hint">Top ${js.length} active patrons by lifetime — the actual touch sequence that produced each pledge (anonymized).</p>
    <div style="overflow-x:auto"><table class="at-table"><thead><tr><th>Journey</th><th class="num">Sessions</th><th class="num">Days</th><th>Tier</th><th class="num">Monthly</th><th class="num">Lifetime</th></tr></thead><tbody>`;
  js.forEach(j => {
    let seq = '';
    if (!j.journey || !j.journey.length) seq = '<span class="at-note">pre-tracking patron — no recorded sessions</span>';
    else j.journey.forEach((st,i)=>{ if(i) seq += '<span class="at-jarrow">→</span>'; seq += `<span class="at-badge other">${esc(st.s)}${st.n>1?' ×'+st.n:''}</span>`; });
    html += `<tr><td><div class="at-jseq">${seq}</div></td><td class="num">${j.sessions||0}</td><td class="num">${j.days||0}</td>
      <td>${esc(j.tier||'—')}</td><td class="num">${usd(j.pledge)}</td><td class="num">${usd(j.lifetime,0)}</td></tr>`;
  });
  html += js.length ? '' : '<tr><td colspan="6" class="at-empty">no journeys synced</td></tr>';
  html += `</tbody></table></div></div>`;

  // ---- monthly traffic (top sources by total visitors)
  const traffic = site.traffic||[];
  const months = [...new Set(traffic.map(t=>t.ym))].sort();
  const bySrc = {};
  traffic.forEach(t => { bySrc[t.source_id] = (bySrc[t.source_id]||0) + Number(t.visitors||0); });
  const top = Object.entries(bySrc).sort((a,b)=>b[1]-a[1]).slice(0,8).map(([sid])=>sid);
  const maxV = Math.max(1, ...traffic.filter(t=>top.includes(String(t.source_id))).map(t=>Number(t.visitors||0)));
  html += `<div class="at-card"><h2>Traffic by month — top sources</h2>
    <p class="hint">Distinct visitors per month (beacon-collected from ${esc(site.site||'site')}; pre-v5 months undercount referrers — that's the bug v5 fixed)</p>
    <div style="overflow-x:auto"><table class="at-table"><thead><tr><th>Source</th>${months.map(m=>`<th>${esc(m)}</th>`).join('')}</tr></thead><tbody>`;
  top.forEach(sid => {
    const s = srcInfo(site, sid);
    html += `<tr><td><strong>${esc(s.name)}</strong></td>` + months.map(m => {
      const row = traffic.find(t=>String(t.source_id)===String(sid) && t.ym===m);
      const v = row ? Number(row.visitors||0) : 0;
      return `<td title="${fmt(v)}"><div class="at-bar" style="width:${Math.max(2,Math.round(v/maxV*70))}px"></div><span class="at-note">${fmt(v)}</span></td>`;
    }).join('') + '</tr>';
  });
  html += `</tbody></table></div></div>`;

  document.getElementById('content').innerHTML = html;
}

document.getElementById('modelSel').addEventListener('change', render);
document.getElementById('siteSel').addEventListener('change', render);
document.getElementById('syncBtn').addEventListener('click', async () => {
  const b = document.getElementById('syncBtn'), n = document.getElementById('syncNote');
  b.disabled = true; n.textContent = 'syncing… (cold pulls can take ~30s per site)';
  try {
    const fd = new FormData(); fd.append('do','sync'); fd.append('csrf', CSRF);
    const r = await fetch('attribution.php?do=sync', {method:'POST', body:fd, credentials:'same-origin'});
    const j = await r.json();
    if (j.ok) { n.textContent = 'synced: ' + (j.synced||[]).join(', ') + (Object.keys(j.errors||{}).length ? ' · errors: '+JSON.stringify(j.errors) : '') + ' — reloading…'; setTimeout(()=>location.reload(), 900); }
    else { n.textContent = 'sync failed: ' + (j.error || JSON.stringify(j.errors)); b.disabled = false; }
  } catch(e) { n.textContent = 'sync failed: ' + e; b.disabled = false; }
});
render();
</script>
</body></html>
