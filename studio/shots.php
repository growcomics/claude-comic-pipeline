<?php
// Production guide — turns the page plan + locked refs into a per-panel "shot sheet"
// for manual generation in Flow: a copy-ready prompt + the exact refs to attach +
// a done tracker. Pure render; forms post to creator.php (style: ret=shots; done: JSON).
declare(strict_types=1);
require_once __DIR__ . '/inc/boot.php';
require_auth();

$id    = preg_replace('/[^a-z0-9-]/', '', (string)($_GET['p'] ?? ''));
$cfile = $id !== '' ? SDATA . '/creator-' . $id . '.json' : '';
$proj  = $id !== '' ? project_get($id) : null;
if ($id === '' || (!is_file($cfile) && !$proj)) { header('Location: creator.php'); exit; }
$c = is_file($cfile) ? s_read($cfile, []) : [];
$c += ['projectId'=>$id, 'name'=>($proj['name'] ?? $id), 'refs'=>[], 'plan'=>[]];
if (!is_array($c['refs'])) $c['refs'] = [];
if (!is_array($c['plan'])) $c['plan'] = [];

$style = trim((string)($c['style'] ?? '')) ?: 'Photorealistic 3D CGI comic panel, DAZ3D / Octane render style, cinematic lighting, sharp detail';
// per-project lettering / text-paneling spec (speech balloons + captions). The stored
// value (empty until the owner sets it) is shown in the edit box; the prompt builder
// falls back to LETTER_SPEC_DEFAULT so dialogue panels always get a consistent block.
$letterSpec = trim((string)($c['lettering'] ?? ''));

// is the AI key installed? (prompt-polish needs it; mirrors refs.php's inline check — ck_ai_cfg lives in creator.php)
$aiOn = (function(){ $f = SDATA . '/ai.json'; if (!is_file($f)) return false; $j = s_read($f, []); return !empty($j['key']); })();

// index locked refs for matching
$charRefs = []; $sceneRefs = []; $propRefs = [];
foreach ($c['refs'] as $r) {
    $k = $r['kind'] ?? '';
    if ($k === 'scene') $sceneRefs[] = $r;
    elseif ($k === 'prop') $propRefs[] = $r;
    else { $cn = strtolower(trim((string)($r['char'] ?? ''))); if ($cn !== '') $charRefs[$cn][] = $r; }
}
function shot_prompt(string $style, array $pn, string $lettering = ''): string {
    $bits = [rtrim($style, ' .')];
    if (!empty($pn['beat']))   $bits[] = rtrim(trim((string)$pn['beat']), ' .');
    if (!empty($pn['camera'])) $bits[] = trim((string)$pn['camera']);
    $p = implode('. ', array_filter($bits)) . '.';
    if (!empty($pn['location'])) $p .= ' Setting: ' . trim((string)$pn['location']) . '.';
    $p .= ck_letter_block($lettering, (string)($pn['dialogue'] ?? ''));   // appends the house lettering style + the exact line for panels that have dialogue
    return $p;
}
function match_chars(array $names, array $charRefs): array {
    $out = []; $pri = ['face'=>0, 'view'=>1, 'body'=>2];
    foreach ($names as $n) { $nl = strtolower(trim((string)$n)); if ($nl === '') continue;
        $matched = [];
        foreach ($charRefs as $cn => $rs)                         // exact, or one name is a prefix of the other ("Andrea" ~ "Andrea Müller"); NOT loose substring
            if ($cn === $nl || strpos($cn, $nl . ' ') === 0 || strpos($nl, $cn . ' ') === 0)
                foreach ($rs as $r) $matched[] = $r;
        usort($matched, fn($a, $b) => ($pri[$a['kind'] ?? ''] ?? 3) <=> ($pri[$b['kind'] ?? ''] ?? 3));
        foreach (array_slice($matched, 0, 4) as $r) $out[$r['file']] = $r;   // a few key refs, face first
    }
    return array_values($out);
}
function match_scene(string $loc, array $sceneRefs): array {
    $words = array_filter(preg_split('/\s+/', preg_replace('/[^a-z ]/', '', strtolower($loc))), fn($w)=>strlen($w) >= 3);
    $hits = [];
    foreach ($sceneRefs as $r) { $hay = strtolower(($r['char'] ?? '') . ' ' . ($r['label'] ?? ''));
        $s = 0; foreach ($words as $w) if (strpos($hay, $w) !== false) $s++;
        if ($s > 0) $hits[] = [$s, $r]; }
    usort($hits, fn($a, $b) => $b[0] <=> $a[0]);
    return array_map(fn($h) => $h[1], $hits);
}
$kindColor = ['face'=>'#EF9F27','body'=>'#5DCAA5','view'=>'#7A7FEC','scene'=>'#378ADD','prop'=>'#D85A30'];
$totalPanels = array_sum(array_map(fn($p)=>count($p['panels'] ?? []), $c['plan']));
$donePanels  = 0; foreach ($c['plan'] as $pg) foreach (($pg['panels'] ?? []) as $pn) if (!empty($pn['done'])) $donePanels++;
function thumb(string $id, array $r): string {
    $f = $r['file'] ?? ''; if ($f === '') return '';
    $u = 'img.php?p=' . urlencode($id) . '&f=' . urlencode($f);
    return '<img loading="lazy" class="sh-rimg" src="' . h($u) . '&t=1" data-full="' . h($u) . '" alt="">';
}
?><!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><meta name="color-scheme" content="dark">
<meta name="robots" content="noindex,nofollow"><title><?= h($c['name']) ?> · Production guide</title>
<link rel="icon" href="assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="assets/studio.css?v=<?= @filemtime(STUDIO_ROOT.'/assets/studio.css') ?>"></head><body>
<header class="topbar" style="border-bottom:2px solid #7A7FEC"><div class="brand"><span class="dot"></span> Comic Studio <span style="background:#7A7FEC;color:#0B0C10;font-size:11px;font-weight:800;letter-spacing:.04em;border-radius:999px;padding:2px 9px;margin-left:6px">📋 PRODUCTION GUIDE</span></div>
  <a class="ghost" href="creator.php?p=<?= h(urlencode($id)) ?>">← Comic Creator</a>
  <a class="ghost" href="refs.php?p=<?= h(urlencode($id)) ?>">🗂 References</a>
  <span class="spacer"></span>
  <span class="ghost"><?= h(current_studio_user()) ?></span> <a class="ghost" href="login.php?do=logout">Log out</a></header>
<style>
.sh-in{background:#101116;border:1px solid #2E3140;color:#F2F2F4;border-radius:7px;padding:6px 9px;font:13px Inter,sans-serif}
.sh-card{background:#14151C;border:1px solid #23252E;border-radius:12px;padding:14px 16px;margin-bottom:14px}
.sh-card h3{margin:0 0 9px;font-size:12px;text-transform:uppercase;letter-spacing:.05em;color:#9CA0AC}
.sh-pagehd{font-size:16px;font-weight:700;margin:22px 0 10px;border-bottom:1px solid #23252E;padding-bottom:7px}
.sh-panel{display:grid;grid-template-columns:minmax(0,1fr) 300px;gap:16px;background:#14151C;border:1px solid #23252E;border-radius:12px;padding:14px 16px;margin-bottom:12px}
@media(max-width:820px){.sh-panel{grid-template-columns:1fr}}
.sh-panel.done{opacity:.55}
.sh-id{font:600 12px ui-monospace,Menlo,monospace;color:#fac775}
.sh-meta{font-size:11.5px;color:#6F7380;margin:2px 0 8px}
.sh-beat{font-size:13px;color:#dfe1e7;line-height:1.5;margin-bottom:8px}
.sh-prompt{width:100%;min-height:74px;background:#0B0C10;border:1px solid #2E3140;color:#e8e8ee;border-radius:8px;padding:9px 11px;font:12.5px ui-monospace,Menlo,monospace;resize:vertical;line-height:1.45}
.sh-copy{margin-top:6px}
.sh-dia{margin-top:8px;font-size:12.5px;color:#9aa0ec}
.sh-refs h4{margin:0 0 6px;font-size:11px;text-transform:uppercase;letter-spacing:.04em;color:#9CA0AC}
.sh-rgrid{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:9px}
.sh-rwrap{width:62px}
.sh-rimg{width:62px;height:78px;object-fit:cover;border-radius:6px;border:1px solid #2E3140;background:#0B0C10;cursor:zoom-in;display:block}
.sh-rlbl{font-size:9.5px;color:#9CA0AC;text-align:center;margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.sh-tag{display:inline-block;font-size:9px;font-weight:800;color:#0B0C10;padding:1px 5px;border-radius:999px;text-transform:uppercase;margin-right:4px}
.sh-done-row{display:flex;align-items:center;gap:8px;margin-bottom:8px}
.sh-done-row input{width:17px;height:17px;accent-color:#1D9E75}
.sh-lb{position:fixed;inset:0;z-index:60;background:rgba(8,9,12,.94);display:none;align-items:center;justify-content:center}
.sh-lb.open{display:flex}.sh-lb img{max-width:90vw;max-height:90vh;border-radius:10px;border:2px solid #2E3140}
.sh-empty{border:1px dashed #2E3140;border-radius:12px;padding:24px;color:#9CA0AC;font-size:14px;text-align:center}
.sh-prompt:focus{outline:none;border-color:#7A7FEC;box-shadow:0 0 0 2px rgba(122,127,236,.2)}
.btn.sm{padding:6px 11px;font-size:12px;border-radius:8px}
.btn.sub{background:#101116;color:#b9bdca}.btn.sub:hover{color:#F2F2F4}
.sh-copy{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.sh-pstate{font-size:10.5px;font-weight:800;color:#cdb6ff;text-transform:uppercase;letter-spacing:.04em}
.sh-prompt.busy{opacity:.5;pointer-events:none}
.sh-ov{position:fixed;inset:0;z-index:70;background:rgba(8,9,12,.92);display:none;align-items:center;justify-content:center}
.sh-ov.open{display:flex}
.sh-ovbox{background:#14151C;border:1px solid #2E3140;border-radius:14px;padding:22px 24px;width:min(440px,90vw);text-align:center}
.sh-ovbox h3{margin:0 0 4px;font-size:15px;color:#F2F2F4}
.sh-ovmsg{font-size:12.5px;color:#9CA0AC;margin:0 0 14px;min-height:16px}
.sh-bar{height:8px;border-radius:999px;background:#23252E;overflow:hidden;margin-bottom:14px}
.sh-bar > i{display:block;height:100%;width:0;background:linear-gradient(90deg,#7A7FEC,#cdb6ff);transition:width .25s}
</style>
<main class="wrap" id="sh" data-id="<?= h($id) ?>" data-csrf="<?= h(csrf()) ?>" style="max-width:min(1840px,95vw)">
  <div class="pagehead" style="display:flex;align-items:center;gap:12px;flex-wrap:wrap">
    <h1 style="margin:0"><?= h($c['name']) ?> <span class="muted" style="font-size:15px;font-weight:400">· production guide</span></h1>
    <?php if ($totalPanels): ?><span class="badge" style="--c:#1D9E75"><?= $donePanels ?> / <?= $totalPanels ?> done</span><?php endif; ?>
  </div>
  <p class="muted" style="max-width:820px;margin:2px 0 16px">For each panel: copy the prompt into Flow, attach the reference images shown, generate, then tick it off. Bring the results back with the Flow → Studio importer. Refs are matched from your locked set by character and location — double-check the scene picks.</p>

  <div class="sh-card">
    <h3>🎨 Style — prepended to every prompt</h3>
    <form method="post" action="creator.php?p=<?= h(urlencode($id)) ?>" style="display:flex;gap:8px;flex-wrap:wrap">
      <?= csrf_field() ?><input type="hidden" name="ret" value="shots"><input type="hidden" name="do" value="style">
      <input type="text" name="style" class="sh-in" style="flex:1;min-width:280px" value="<?= h($style) ?>">
      <button class="btn">Save style</button>
    </form>
  </div>

  <div class="sh-card">
    <h3>💬 Lettering — added to every panel that has dialogue</h3>
    <p class="muted" style="margin:0 0 9px;font-size:12.5px;max-width:780px">One house style for speech balloons &amp; captions so text paneling stays consistent across the comic. This spec — together with the panel's exact line — is appended to the prompt of every panel that has dialogue (and to its AI-polished version). Leave it blank to use the built-in default shown in the box.</p>
    <form method="post" action="creator.php?p=<?= h(urlencode($id)) ?>">
      <?= csrf_field() ?><input type="hidden" name="ret" value="shots"><input type="hidden" name="do" value="lettering">
      <textarea name="lettering" class="sh-prompt" style="min-height:84px" maxlength="800" placeholder="<?= h(LETTER_SPEC_DEFAULT) ?>"><?= h($letterSpec) ?></textarea>
      <div style="display:flex;align-items:center;gap:10px;margin-top:8px;flex-wrap:wrap">
        <button class="btn">Save lettering</button>
        <span class="muted" style="font-size:12px"><?= $letterSpec === '' ? 'Using the built-in default house style.' : 'Custom house style set.' ?></span>
        <button type="button" class="btn sm sub" id="sheetbtn">📄 Style sheet</button>
      </div>
    </form>
    <div id="sheet" style="display:none;margin-top:14px;border-top:1px solid #23252E;padding-top:14px">
      <p class="muted" style="margin:0 0 8px;font-size:12px">A sample plate of the recommended balloon style — save it and attach it in Flow alongside the panel so the generator matches the shapes. Your written spec above rides in the prompt automatically.</p>
      <svg id="sheetsvg" viewBox="0 0 720 440" width="100%" style="max-width:720px;background:#cfd3da;border-radius:10px;border:1px solid #2E3140;display:block" xmlns="http://www.w3.org/2000/svg" font-family="Arial, Helvetica, sans-serif">
        <text x="24" y="40" font-size="20" font-weight="800" fill="#11131a">LETTERING STYLE REFERENCE</text>
        <rect x="24" y="58" width="262" height="50" rx="3" fill="#F4E08A" stroke="#11131a" stroke-width="2"/>
        <text x="38" y="80" font-size="13" font-weight="700" fill="#11131a">CAPTION — narration box,</text>
        <text x="38" y="98" font-size="13" font-weight="700" fill="#11131a">pale yellow, top-left corner.</text>
        <rect x="118" y="152" width="334" height="120" rx="26" fill="#ffffff" stroke="#11131a" stroke-width="3"/>
        <path d="M182 270 L168 320 L228 272 Z" fill="#ffffff" stroke="#11131a" stroke-width="3"/>
        <text x="285" y="196" font-size="17" font-weight="700" fill="#11131a" text-anchor="middle">SPEECH BALLOON</text>
        <text x="285" y="224" font-size="14" fill="#11131a" text-anchor="middle">Bold black sans-serif,</text>
        <text x="285" y="246" font-size="14" fill="#11131a" text-anchor="middle">centered, 20 words max.</text>
        <ellipse cx="568" cy="322" rx="118" ry="70" fill="#ffffff" stroke="#11131a" stroke-width="3"/>
        <circle cx="478" cy="392" r="13" fill="#ffffff" stroke="#11131a" stroke-width="3"/>
        <circle cx="458" cy="416" r="8" fill="#ffffff" stroke="#11131a" stroke-width="3"/>
        <text x="568" y="318" font-size="15" font-weight="700" fill="#11131a" text-anchor="middle">THOUGHT BALLOON</text>
        <text x="568" y="340" font-size="13" fill="#11131a" text-anchor="middle">same font, cloud edge.</text>
      </svg>
      <div style="margin-top:10px"><button type="button" class="btn sm" id="sheetdl">⬇ Save as PNG</button></div>
    </div>
  </div>

  <?php if ($totalPanels): ?>
  <div class="sh-card" style="display:flex;align-items:center;gap:12px;flex-wrap:wrap">
    <div style="flex:1;min-width:240px">
      <h3 style="margin:0 0 4px">✨ AI prompt polish</h3>
      <p class="muted" style="margin:0;font-size:12.5px">Rewrite each panel's flat template into a director-grade prompt — staging, lighting, lens &amp; depth-of-field, camera variety across the page, and guards against the usual failure modes. Looks still come from the attached refs. <?= $aiOn ? 'You can also polish one panel at a time, or hand-edit any prompt below.' : '' ?></p>
    </div>
    <?php if ($aiOn): ?>
      <button type="button" id="polishall" class="btn" data-total="<?= $totalPanels ?>">✨ Polish all prompts</button>
    <?php else: ?>
      <button type="button" class="btn" disabled>✨ Polish all prompts</button>
      <span class="muted" style="font-size:12px">add your API key (<a href="refs.php?p=<?= h(urlencode($id)) ?>" style="color:#9aa0ec">references workspace</a>) to enable</span>
    <?php endif; ?>
  </div>
  <?php endif; ?>

  <?php if (!$totalPanels): ?>
  <div class="sh-empty">No page plan yet. Go to the <a href="creator.php?p=<?= h(urlencode($id)) ?>" style="color:#9aa0ec">Comic Creator</a> → <b>📜 Script</b> panel → <b>📑 Break script into pages</b>, then come back here.</div>
  <?php else: ?>
    <?php foreach ($c['plan'] as $pi => $pg): ?>
    <div class="sh-pagehd">Page <?= $pi + 1 ?> <span class="muted" style="font-weight:400;font-size:13px">· <?= count($pg['panels'] ?? []) ?> panels</span></div>
    <?php foreach (($pg['panels'] ?? []) as $pn): if (!is_array($pn)) continue;
        $pid = (string)($pn['id'] ?? ('p'.($pi+1)));
        $isDone = !empty($pn['done']);
        $template   = shot_prompt($style, $pn, $letterSpec);
        $polished   = trim((string)($pn['polished'] ?? ''));
        $isPolished = $polished !== '';
        $prompt     = $isPolished ? $polished : $template;     // show the polished prompt if we have one, else the flat template
        $chars = (array)($pn['characters'] ?? []);
        $cRefs = match_chars($chars, $charRefs);
        $sRefs = $pn['location'] ? match_scene((string)$pn['location'], $sceneRefs) : [];
        $sFallback = (!$sRefs && $sceneRefs);
    ?>
    <div class="sh-panel<?= $isDone?' done':'' ?>" data-panel="<?= h($pid) ?>">
      <div>
        <div class="sh-done-row">
          <input type="checkbox" class="sh-done" <?= $isDone?'checked':'' ?>>
          <span class="sh-id"><?= h($pid) ?></span>
          <span class="sh-meta"><?= h((string)($pn['camera'] ?? '')) ?><?= !empty($pn['location'])?' · '.h((string)$pn['location']):'' ?></span>
        </div>
        <?php if (!empty($pn['beat'])): ?><div class="sh-beat"><?= h((string)$pn['beat']) ?></div><?php endif; ?>
        <textarea class="sh-prompt" data-template="<?= h($template) ?>"<?= $isPolished?' data-polished="1"':'' ?>><?= h($prompt) ?></textarea>
        <div class="sh-copy">
          <button type="button" class="btn sm sh-copybtn">⧉ Copy prompt</button>
          <?php if ($aiOn): ?><button type="button" class="btn sm sub sh-polishbtn"><?= $isPolished ? '↻ Re-polish' : '✨ Polish' ?></button><?php endif; ?>
          <button type="button" class="btn sm sub sh-resetbtn" style="<?= $isPolished?'':'display:none' ?>">↺ Template</button>
          <span class="sh-pstate" style="<?= $isPolished?'':'display:none' ?>">✨ polished</span>
        </div>
        <?php if (!empty($pn['dialogue'])): ?><div class="sh-dia">💬 <?= h((string)$pn['dialogue']) ?></div><?php endif; ?>
      </div>
      <div class="sh-refs">
        <h4>Attach these refs</h4>
        <?php if ($cRefs): ?>
          <div class="sh-rgrid">
          <?php foreach ($cRefs as $r): ?>
            <div class="sh-rwrap"><?= thumb($id, $r) ?><div class="sh-rlbl"><span class="sh-tag" style="background:<?= $kindColor[$r['kind']??'']??'#9CA0AC' ?>"><?= h(substr($r['kind']??'?',0,1)) ?></span><?= h($r['char'] ?? '') ?></div></div>
          <?php endforeach; ?>
          </div>
        <?php else: ?><div class="muted" style="font-size:11.5px;margin-bottom:8px"><?= $chars ? 'No locked ref for: '.h(implode(', ',$chars)) : 'No character in this panel' ?></div><?php endif; ?>
        <?php if ($sRefs || $sFallback): ?>
          <h4><?= $sFallback ? 'Scene — pick the right one' : 'Scene' ?></h4>
          <div class="sh-rgrid">
          <?php foreach (($sRefs ?: $sceneRefs) as $r): ?>
            <div class="sh-rwrap"><?= thumb($id, $r) ?><div class="sh-rlbl"><?= h($r['label'] ?: ($r['char'] ?: 'scene')) ?></div></div>
          <?php endforeach; ?>
          </div>
        <?php endif; ?>
      </div>
    </div>
    <?php endforeach; ?>
    <?php endforeach; ?>
    <?php if ($propRefs): ?>
    <div class="sh-card" style="margin-top:18px">
      <h3>🧩 Props &amp; objects — attach when they appear</h3>
      <div class="sh-rgrid">
      <?php foreach ($propRefs as $r): ?>
        <div class="sh-rwrap"><?= thumb($id, $r) ?><div class="sh-rlbl"><?= h($r['char'] ?: ($r['label'] ?: 'prop')) ?></div></div>
      <?php endforeach; ?>
      </div>
    </div>
    <?php endif; ?>
  <?php endif; ?>
</main>
<div class="sh-lb" id="lb"><img id="lbimg" src="" alt=""></div>
<div class="sh-ov" id="polishov"><div class="sh-ovbox">
  <h3>✨ Polishing prompts</h3>
  <p class="sh-ovmsg" id="polishmsg">Starting…</p>
  <div class="sh-bar"><i id="polishfill"></i></div>
  <button type="button" class="btn sm sub" id="polishcancel">Cancel</button>
</div></div>
<script>
(function(){
  var root=document.getElementById('sh'), PID=root.dataset.id, CSRF=root.dataset.csrf;
  function post(body){ body.p=PID; return fetch('creator.php?p='+encodeURIComponent(PID), {method:'POST', headers:{'X-CSRF':CSRF}, body:new URLSearchParams(body)}).then(function(r){return r.json();}); }

  // reflect a panel's polished/template state in its controls
  function setState(card, polished){
    var reset=card.querySelector('.sh-resetbtn'), pstate=card.querySelector('.sh-pstate'),
        pb=card.querySelector('.sh-polishbtn'), ta=card.querySelector('.sh-prompt');
    if(reset)  reset.style.display  = polished ? '' : 'none';
    if(pstate) pstate.style.display = polished ? '' : 'none';
    if(pb)     pb.textContent = polished ? '↻ Re-polish' : '✨ Polish';
    if(ta){ if(polished) ta.dataset.polished='1'; else delete ta.dataset.polished; }
  }
  function pbLabel(card){ return card.querySelector('.sh-prompt').dataset.polished ? '↻ Re-polish' : '✨ Polish'; }

  // AI-polish ONE panel; resolves {ok, err}
  function polishOne(card){
    var ta=card.querySelector('.sh-prompt'); ta.classList.add('busy');
    return post({do:'polish_one', panel:card.dataset.panel}).then(function(j){
      ta.classList.remove('busy');
      if(j && j.ok){ ta.value=j.polished; setState(card,true); return {ok:true}; }
      return {ok:false, err:(j&&j.err)||'failed'};
    }).catch(function(){ ta.classList.remove('busy'); return {ok:false, err:'network error'}; });
  }

  document.addEventListener('click', function(e){
    var b=e.target.closest('.sh-copybtn');                       // copy prompt
    if(b){ var ta=b.closest('.sh-panel').querySelector('.sh-prompt');
      if(ta){ ta.select(); navigator.clipboard.writeText(ta.value).then(function(){ var o=b.textContent; b.textContent='✓ copied'; setTimeout(function(){b.textContent=o;},1200); }).catch(function(){ document.execCommand('copy'); }); }
      return; }
    var pb=e.target.closest('.sh-polishbtn');                    // polish this panel
    if(pb){ var card=pb.closest('.sh-panel'); pb.disabled=true; pb.textContent='✨ …';
      polishOne(card).then(function(r){ pb.disabled=false; pb.textContent=pbLabel(card);
        if(!r.ok){ pb.textContent='⚠ '+(r.err||'retry'); setTimeout(function(){ pb.textContent=pbLabel(card); }, 2200); } });
      return; }
    var rb=e.target.closest('.sh-resetbtn');                     // reset this panel to the flat template
    if(rb){ var card2=rb.closest('.sh-panel'), ta2=card2.querySelector('.sh-prompt');
      ta2.value=ta2.dataset.template||''; setState(card2,false);
      post({do:'polishedit', panel:card2.dataset.panel, text:''}).catch(function(){});
      return; }
    var img=e.target.closest('.sh-rimg');                        // lightbox
    if(img){ var lb=document.getElementById('lb'); document.getElementById('lbimg').src=img.dataset.full||img.src; lb.classList.add('open'); return; }
    if(e.target.id==='lb' || e.target.id==='lbimg'){ document.getElementById('lb').classList.remove('open'); }
  });
  document.addEventListener('keydown', function(e){ if(e.key==='Escape'){ document.getElementById('lb').classList.remove('open'); } });

  // done toggle + save manual prompt edits (JSON, no reload)
  document.addEventListener('change', function(e){
    var cb=e.target.closest('.sh-done');
    if(cb){ var card=cb.closest('.sh-panel'), done=cb.checked; card.classList.toggle('done', done);
      post({do:'shotdone', panel:card.dataset.panel, done:done?'1':''}).catch(function(){}); return; }
    var ta=e.target.closest('.sh-prompt');                       // hand-edited a prompt -> persist (editing back to the template stores nothing)
    if(ta){ var card2=ta.closest('.sh-panel'), txt=ta.value.trim(), tmpl=(ta.dataset.template||'').trim();
      var send=(txt===tmpl)?'':txt; setState(card2, send!=='');
      post({do:'polishedit', panel:card2.dataset.panel, text:send}).catch(function(){}); return; }
  });

  // batch: polish every panel, sequentially, with a progress overlay
  var allBtn=document.getElementById('polishall');
  if(allBtn){
    var cancel=false, running=false;
    var ov=document.getElementById('polishov'), fill=document.getElementById('polishfill'),
        msg=document.getElementById('polishmsg'), cancelBtn=document.getElementById('polishcancel');
    allBtn.addEventListener('click', function(){
      if(running) return;
      var cards=[].slice.call(document.querySelectorAll('.sh-panel')); if(!cards.length) return;
      cancel=false; running=true; allBtn.disabled=true;
      cancelBtn.textContent='Cancel'; fill.style.width='0'; msg.textContent='Starting…'; ov.classList.add('open');
      var done=0, fail=0, total=cards.length;
      (function step(i){
        if(cancel || i>=cards.length){
          msg.textContent=(cancel?'Cancelled — ':'Done — ')+done+' polished'+(fail?(', '+fail+' failed'):'')+'.';
          cancelBtn.textContent='Close'; allBtn.disabled=false; running=false; return;
        }
        msg.textContent='Panel '+(i+1)+' of '+total+'  ·  '+(cards[i].dataset.panel||'');
        polishOne(cards[i]).then(function(r){ if(r.ok) done++; else fail++; fill.style.width=Math.round((i+1)/total*100)+'%'; step(i+1); });
      })(0);
    });
    cancelBtn.addEventListener('click', function(){ cancel=true; ov.classList.remove('open'); if(!running) cancelBtn.textContent='Cancel'; });
  }

  // lettering style sheet: toggle the sample plate + save it as a PNG to attach in Flow
  var sheetBtn=document.getElementById('sheetbtn'), sheet=document.getElementById('sheet');
  if(sheetBtn && sheet){ sheetBtn.addEventListener('click', function(){
    var hidden=sheet.style.display==='none'; sheet.style.display=hidden?'':'none';
    if(hidden) sheet.scrollIntoView({behavior:'smooth', block:'nearest'}); }); }
  var dl=document.getElementById('sheetdl');
  if(dl){ dl.addEventListener('click', function(){
    var svg=document.getElementById('sheetsvg'); if(!svg) return;
    var xml=new XMLSerializer().serializeToString(svg), scale=2, img=new Image();
    img.onload=function(){
      var c=document.createElement('canvas'); c.width=720*scale; c.height=440*scale;
      var ctx=c.getContext('2d'); ctx.fillStyle='#cfd3da'; ctx.fillRect(0,0,c.width,c.height);
      ctx.drawImage(img,0,0,c.width,c.height);
      var a=document.createElement('a'); a.download='lettering-style-sheet.png'; a.href=c.toDataURL('image/png'); a.click();
    };
    img.onerror=function(){ alert('Could not export — right-click the sample and "Save image" instead.'); };
    img.src='data:image/svg+xml;charset=utf-8,'+encodeURIComponent(xml);
  }); }
})();
</script>
</body></html>
