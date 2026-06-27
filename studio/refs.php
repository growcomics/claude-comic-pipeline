<?php
// References workspace — full-width page for uploading + sorting + approving a
// project's reference set. Pure render: every form posts to creator.php's proven
// handlers with ret=refs, so there is NO duplicated mutation logic here.
declare(strict_types=1);
require_once __DIR__ . '/inc/boot.php';
require_auth();

$id    = preg_replace('/[^a-z0-9-]/', '', (string)($_GET['p'] ?? ''));
$cfile = $id !== '' ? SDATA . '/creator-' . $id . '.json' : '';
$proj  = $id !== '' ? project_get($id) : null;
if ($id === '' || (!is_file($cfile) && !$proj)) { header('Location: creator.php'); exit; }

$c = is_file($cfile) ? s_read($cfile, []) : [];
$c += ['projectId'=>$id, 'name'=>($proj['name'] ?? $id), 'refs'=>[]];
if (!is_array($c['refs'])) $c['refs'] = [];

// grouping (mirrors creator.php exactly): scenes + props get their own sections
$byChar = [];
foreach ($c['refs'] as $r) { $kd = $r['kind'] ?? ''; $k = $kd==='scene' ? '_scenes' : ($kd==='prop' ? '_props' : ((($r['char'] ?? '') !== '') ? $r['char'] : '_')); $byChar[$k][] = $r; }
$refTotal = count($c['refs']); $refOk = count(array_filter($c['refs'], fn($r)=>($r['status']??'')==='approved'));
$charName  = fn($k) => $k==='_scenes' ? 'Scenes & locations' : ($k==='_props' ? 'Props & objects' : ($k==='_' ? 'Uncategorized' : ucwords(str_replace('-',' ',$k))));
$locked    = !empty($c['refsLocked']); $lockedN = count($c['refsLockedSet'] ?? []);
$kindOpts  = ['face'=>'face','body'=>'body tier','view'=>'turnaround / view','scene'=>'scene / location','prop'=>'prop / object'];
$kindColor = ['face'=>'#EF9F27','body'=>'#5DCAA5','view'=>'#7A7FEC','scene'=>'#378ADD','prop'=>'#D85A30'];
$aiOn = is_file(SDATA . '/ai.json') && !empty((s_read(SDATA . '/ai.json', []))['key']);
$post = 'creator.php?p=' . urlencode($id);   // forms post to the shared handlers
?><!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><meta name="color-scheme" content="dark">
<meta name="robots" content="noindex,nofollow"><title><?= h($c['name']) ?> · References</title>
<link rel="icon" href="assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="assets/studio.css?v=<?= @filemtime(STUDIO_ROOT.'/assets/studio.css') ?>"></head><body>
<header class="topbar" style="border-bottom:2px solid #7A7FEC"><div class="brand"><span class="dot"></span> Comic Studio <span style="background:#7A7FEC;color:#0B0C10;font-size:11px;font-weight:800;letter-spacing:.04em;border-radius:999px;padding:2px 9px;margin-left:6px">🗂 REFERENCES</span></div>
  <a class="ghost" href="creator.php?p=<?= h(urlencode($id)) ?>">← Comic Creator</a>
  <span class="spacer"></span>
  <span class="ghost"><?= h(current_studio_user()) ?></span> <a class="ghost" href="login.php?do=logout">Log out</a></header>
<style>
.rf-flash{background:rgba(239,159,39,.12);border:1px solid #7a5a1f;color:#fac775;border-radius:9px;padding:9px 13px;font-size:13px;margin:0 0 14px}
.rf-lock{display:flex;align-items:center;justify-content:space-between;gap:14px;flex-wrap:wrap;background:#14151C;border:1px solid #7a5a1f;border-radius:12px;padding:14px 16px;margin-bottom:16px}
.rf-lock.on{border-color:#1D9E75}
.rf-tools{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:14px;margin-bottom:18px}
.rf-card{background:#14151C;border:1px solid #23252E;border-radius:12px;padding:14px 16px}
.rf-card h3{font-size:12px;text-transform:uppercase;letter-spacing:.05em;color:#9CA0AC;margin:0 0 9px}
.rf-in{background:#101116;border:1px solid #2E3140;color:#F2F2F4;border-radius:7px;padding:6px 9px;font:13px Inter,sans-serif}
.rf-ta{width:100%;min-height:56px;background:#101116;border:1px solid #2E3140;color:#F2F2F4;border-radius:8px;padding:8px 10px;font:13px Inter,sans-serif;resize:vertical}
.rf-group{margin-bottom:22px}
.rf-ghead{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin:0 0 10px;border-bottom:1px solid #23252E;padding-bottom:8px}
.rf-ghead h2{margin:0;font-size:17px}
.rf-gform{display:flex;gap:6px;align-items:center;flex-wrap:wrap;margin:0}
.rf-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(155px,1fr));gap:12px}
.rf-substage{grid-column:1/-1;display:flex;align-items:baseline;gap:8px;margin:4px 0 -2px;font-size:12px;font-weight:800;letter-spacing:.03em;color:#cdb6ff;text-transform:uppercase;border-top:1px dashed #2E3140;padding-top:9px}
.rf-substage:first-child{border-top:0;padding-top:0}
.rf-subnote{font-weight:400;text-transform:none;letter-spacing:0;color:#7f8492;font-size:11px}
.rf-stage{display:inline-block;background:#3a2d5e;color:#cdb6ff;font-weight:800;font-size:9.5px;border-radius:999px;padding:1px 7px;text-transform:uppercase;letter-spacing:.03em}
.rf-stagerow{margin:0 0 5px}
.rf-cardx{border:1px solid #2E3140;border-radius:10px;overflow:hidden;background:#101116;position:relative}
.rf-cardx.ok{border-color:#3a6f5c}
.rf-img{display:block;width:100%;aspect-ratio:3/4;object-fit:cover;background:#0B0C10;cursor:zoom-in}
.rf-tag{position:absolute;top:6px;left:6px;font-size:10px;font-weight:800;color:#0B0C10;padding:2px 7px;border-radius:999px;text-transform:uppercase}
.rf-lk{position:absolute;top:6px;right:6px;font-size:12px;background:rgba(29,158,117,.95);color:#04231b;border-radius:999px;padding:1px 7px;font-weight:800}
.rf-body{padding:8px 9px}
.rf-body .rf-in{width:100%;margin-bottom:5px;font-size:12px;padding:5px 7px}
.rf-btns{display:flex;gap:5px}
.rf-btns button{flex:1;background:#191B24;border:1px solid #2E3140;color:#c7cad4;border-radius:6px;padding:5px 0;font-size:12px;cursor:pointer;line-height:1.2}
.rf-btns button:hover{background:#23252E;color:#fff}
.rf-btns .rf-rm:hover{background:#8a3b3b;border-color:#8a3b3b}
.rf-ocr{width:100%;background:#191B24;border:1px solid #2E3140;color:#c7cad4;border-radius:6px;padding:5px 0;font-size:12px;cursor:pointer;margin-bottom:6px;line-height:1.2}
.rf-ocr:hover{background:#2b2f60;border-color:#5b5fd0;color:#fff}
.rf-ocr:disabled{opacity:.7;cursor:default}
.rf-st{font-size:10.5px;font-weight:700;padding:2px 7px;border-radius:999px;display:inline-block;margin-top:4px}
.rf-ok{background:rgba(29,158,117,.18);color:#6fe0bd}
.rf-need{background:rgba(239,159,39,.16);color:#fac775}
.rf-prov{margin-top:5px;font-size:10px;color:#7f8492;line-height:1.3;word-break:break-word}
.rf-role{background:#23252E;color:#9CA0AC;border-radius:999px;padding:1px 6px;font-weight:700;text-transform:uppercase;font-size:9px}
.rf-env code{background:#101116;border:1px solid #2E3140;border-radius:4px;padding:1px 4px;font-size:11px;color:#c7cad4}
.rf-empty{border:1px dashed #2E3140;border-radius:12px;padding:24px;color:#9CA0AC;font-size:14px;text-align:center}
.rf-lb{position:fixed;inset:0;z-index:60;background:rgba(8,9,12,.94);display:none;align-items:center;justify-content:center}
.rf-lb.open{display:flex}
.rf-lb img{max-width:90vw;max-height:90vh;border-radius:10px;border:2px solid #2E3140;background:#0B0C10}
.ai-ov{position:fixed;inset:0;z-index:70;background:rgba(8,9,12,.92);display:none;align-items:center;justify-content:center}
.ai-ov.open{display:flex}
.ai-box{background:#14151C;border:1px solid #2E3140;border-radius:14px;padding:22px 26px;width:min(420px,90vw);text-align:center}
.ai-title{font-size:16px;font-weight:700;margin-bottom:6px}
.ai-sub{color:#9CA0AC;font-size:13px;margin-bottom:14px;min-height:18px}
.ai-track{height:10px;background:#23252E;border-radius:999px;overflow:hidden;margin-bottom:14px}
.ai-fill{height:100%;width:0;background:#7A7FEC;transition:width .25s ease}
.ai-cur{max-width:120px;max-height:120px;border-radius:8px;border:1px solid #2E3140;margin:0 auto 14px;object-fit:cover;display:none}
.ai-box .btn{width:100%}
</style>
<main class="wrap" id="refs" data-id="<?= h($id) ?>" data-csrf="<?= h(csrf()) ?>" style="max-width:min(1840px,95vw)">
  <div class="pagehead" style="display:flex;align-items:center;gap:12px;flex-wrap:wrap">
    <h1 style="margin:0"><?= h($c['name']) ?> <span class="muted" style="font-size:15px;font-weight:400">· references workspace</span></h1>
  </div>
  <p class="muted" style="max-width:820px;margin:2px 0 16px">Drop in faces, characters, props and scenes — one or many at a time. Leave the character box blank and a batch <b>auto-groups by look</b>; then name the groups, set kinds, approve, and lock. Locked references are what every page gets built from. For a <b>transformation comic</b>, tag a character's refs with a <b>stage</b> (pre / mid / post, or a tier) so early pages pull the <em>before</em> look and later pages the <em>after</em> — a ref left at <b>any stage</b> (e.g. a face that doesn't change) is used throughout.</p>

  <?php if (!empty($c['gateMsg'])): ?><div class="rf-flash"><?= h($c['gateMsg']) ?></div><?php endif; ?>

  <div class="rf-lock <?= $locked?'on':'' ?>">
    <div>
      <div style="font-weight:700;font-size:14px;color:<?= $locked?'#6fe0bd':'#fac775' ?>"><?= $locked ? '🔒 '.$lockedN.' reference'.($lockedN===1?'':'s').' locked — pages can generate' : '🔓 Not locked — page generation is blocked' ?></div>
      <div class="muted" style="font-size:12px;margin-top:2px"><?= $locked ? 'Frozen set — every page pulls from these. Unlock to keep editing.' : ($refOk ? ('Lock to freeze the '.$refOk.' approved reference'.($refOk===1?'':'s').'.') : 'Add and approve at least one reference, then lock.') ?></div>
    </div>
    <form method="post" action="<?= h($post) ?>"><?= csrf_field() ?><input type="hidden" name="ret" value="refs"><input type="hidden" name="do" value="lockrefs"><input type="hidden" name="locked" value="<?= $locked?'':'1' ?>"><button class="btn<?= $locked?'':' primary' ?>"<?= (!$locked && $refOk<1)?' disabled':'' ?>><?= $locked?'🔓 Unlock':'🔒 Lock references' ?></button></form>
  </div>

  <?php if (!$locked): ?>
  <div class="rf-tools">
    <div class="rf-card">
      <h3>➕ Add references — drop one or many</h3>
      <form method="post" action="<?= h($post) ?>" enctype="multipart/form-data">
        <?= csrf_field() ?><input type="hidden" name="ret" value="refs"><input type="hidden" name="do" value="uploadref">
        <input type="file" name="reffile[]" accept="image/*" multiple required style="width:100%;margin-bottom:8px;color:#c7cad4">
        <div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px">
          <select name="kind" class="rf-in" title="'auto' guesses each image from its shape">
            <option value="auto" selected>kind: auto — guess each</option>
            <?php foreach ($kindOpts as $kv=>$kl): ?><option value="<?= $kv ?>">all: <?= $kl ?></option><?php endforeach; ?>
          </select>
          <select name="stage" class="rf-in" title="transformation stage for this whole batch — leave 'any' if the look doesn't change">
            <option value="" selected>stage: any</option>
            <?php foreach (STAGE_OPTS as $sv=>$sl): ?><option value="<?= h($sv) ?>"><?= h($sl) ?></option><?php endforeach; ?>
          </select>
          <input type="text" name="char" class="rf-in" placeholder="character — blank = auto-group by look" style="flex:1;min-width:170px">
        </div>
        <button class="btn primary">⬆ Upload</button>
        <span class="muted" style="font-size:12px"> &nbsp;blank character + many files → grouped automatically by look</span>
      </form>
      <div style="margin-top:10px;border-top:1px solid #23252E;padding-top:10px;display:flex;align-items:center;gap:8px;flex-wrap:wrap">
        <form method="post" action="<?= h($post) ?>" id="aisortform"><?= csrf_field() ?><input type="hidden" name="ret" value="refs"><input type="hidden" name="do" value="aisort"><button class="btn"<?= $refTotal?'':' disabled' ?>>✨ AI sort</button></form>
        <span class="muted" style="font-size:12px"><?= $aiOn ? 'refines kinds and names characters from your script' : '— paste your API key below to enable' ?></span>
      </div>
      <?php if ($aiOn): ?>
      <div style="margin-top:8px;display:flex;align-items:center;gap:8px;flex-wrap:wrap;font-size:12px">
        <span style="color:#6fe0bd">🔑 AI key installed</span>
        <form method="post" action="<?= h($post) ?>" style="display:inline"><?= csrf_field() ?><input type="hidden" name="ret" value="refs"><input type="hidden" name="do" value="aikeytest"><button class="btn sm">test key</button></form>
        <form method="post" action="<?= h($post) ?>" style="display:inline" onsubmit="return confirm('Remove the AI key? AI sort will turn off.')"><?= csrf_field() ?><input type="hidden" name="ret" value="refs"><input type="hidden" name="do" value="aikeydel"><button class="btn sm">remove key</button></form>
      </div>
      <?php else: ?>
      <form method="post" action="<?= h($post) ?>" style="margin-top:8px">
        <?= csrf_field() ?><input type="hidden" name="ret" value="refs"><input type="hidden" name="do" value="aikey">
        <label style="font-size:11px;color:#9CA0AC;display:block;margin-bottom:4px">🔑 Enable AI sort — paste your Anthropic API key (saved on your server only, never displayed again)</label>
        <div style="display:flex;gap:6px;flex-wrap:wrap">
          <input type="password" name="aikey" autocomplete="off" spellcheck="false" placeholder="sk-ant-..." class="rf-in" style="flex:1;min-width:220px">
          <button class="btn primary">Save key</button>
        </div>
      </form>
      <?php endif; ?>
      <div style="margin-top:10px;border-top:1px solid #23252E;padding-top:10px"><button type="button" id="ocrall" class="btn sm"<?= $refTotal?'':' disabled' ?>>📖 Read text on all</button> <span class="muted" style="font-size:11px">free, in your browser — reads on-image text into the labels (first run downloads the engine; then review &amp; save)</span></div>
    </div>
    <div class="rf-card">
      <h3>👕 Wardrobe / continuity</h3>
      <form method="post" action="<?= h($post) ?>"><?= csrf_field() ?><input type="hidden" name="ret" value="refs"><input type="hidden" name="do" value="wardrobe">
        <textarea name="wardrobe" class="rf-ta" placeholder="e.g. gray tank top covering the midriff, black shorts — never crop the shirt to show abs"><?= h($c['wardrobe'] ?? '') ?></textarea>
        <div style="margin-top:6px"><button class="btn">Save</button> <span class="muted" style="font-size:11px">sent with every panel</span></div>
      </form>
      <h3 style="margin-top:14px">📜 Script — cast &amp; scenes for AI</h3>
      <form method="post" action="<?= h($post) ?>"><?= csrf_field() ?><input type="hidden" name="ret" value="refs"><input type="hidden" name="do" value="script">
        <textarea name="script" class="rf-ta" placeholder="Paste your script, or a character + scene list. ✨ AI sort uses this to name characters."><?= h($c['script'] ?? '') ?></textarea>
        <div style="margin-top:6px"><button class="btn">Save script</button></div>
      </form>
    </div>
    <div class="rf-card rf-env">
      <h3>🌍 Real-photo location refs</h3>
      <p class="muted" style="font-size:12px;margin:0 0 8px">Backgrounds built fully by AI read as "too AI" (samey crowds, invented geometry). Source <b>real photos</b> of the location, restyle them to your CGI look, and drop them in here as <b>scene</b> plates — far more realistic, and consistent every panel. <b>Real&nbsp;→&nbsp;DAZ&nbsp;→&nbsp;insert.</b></p>
      <input type="text" id="envloc" class="rf-in" placeholder='location, e.g. "commercial gym"' style="width:100%;margin-bottom:7px">
      <button type="button" class="btn" id="envbrief">📋 Copy gather brief</button>
      <span class="muted" id="envbriefmsg" style="font-size:11px;margin-left:6px"></span>
      <p class="muted" style="font-size:11px;margin:9px 0 0">Paste the brief into a Claude Code session: it gathers real photos <b>with provenance</b>, converts them to your CGI plate, and runs <code>push-env-refs.sh</code> to land them here as scene refs. Then approve &amp; lock — the production guide attaches them to every panel at this location. SOP: <code>studio/docs/REAL-PHOTO-ENV-REFS.md</code>.</p>
    </div>
  </div>
  <?php endif; ?>

  <?php if ($refTotal): ?>
  <div style="margin:6px 0 10px;color:#9CA0AC;font-size:13px"><?= $refOk ?> of <?= $refTotal ?> approved — the cast, body tiers, props &amp; scenes every page pulls from.</div>
  <?php foreach ($byChar as $gk=>$list): ?>
  <section class="rf-group">
    <div class="rf-ghead">
      <h2><?= h($charName($gk)) ?> <span class="muted" style="font-weight:400;font-size:14px">(<?= count($list) ?>)</span></h2>
      <?php if (!$locked): ?>
      <span class="spacer"></span>
      <form method="post" action="<?= h($post) ?>" class="rf-gform">
        <?= csrf_field() ?><input type="hidden" name="ret" value="refs"><input type="hidden" name="do" value="editgroup"><input type="hidden" name="gk" value="<?= h($gk) ?>">
        <input type="text" name="char" class="rf-in" placeholder="rename group" style="width:130px">
        <select name="kind" class="rf-in"><option value="">set kind…</option><?php foreach ($kindOpts as $kv=>$kl): ?><option value="<?= $kv ?>"><?= $kl ?></option><?php endforeach; ?></select>
        <?php if ($gk !== '' && $gk[0] !== '_'): ?><select name="stage" class="rf-in" title="Set the transformation stage for the whole group"><option value="">set stage…</option><option value="-">— any stage —</option><?php foreach (STAGE_OPTS as $sv=>$sl): ?><option value="<?= h($sv) ?>"><?= h($sl) ?></option><?php endforeach; ?></select><?php endif; ?>
        <button class="btn sm" title="Apply rename / kind / stage to everyone in this group">apply</button>
        <button class="btn sm" name="approve" value="1" title="Approve all in this group">✓ approve all</button>
      </form>
      <?php endif; ?>
    </div>
    <?php
      $isCharGroup = ($gk !== '' && $gk[0] !== '_');
      $hasStaged = false; foreach ($list as $rr) { if (ck_stage_key((string)($rr['stage'] ?? '')) !== '') { $hasStaged = true; break; } }
      $renderList = $list;
      if ($isCharGroup && $hasStaged) {                          // order staged buckets (pre→post→tiers), any-stage last, so cards visibly group by stage
        $ord = array_flip(array_keys(STAGE_OPTS));
        usort($renderList, function($a, $b) use ($ord) {
          $sa = ck_stage_key((string)($a['stage'] ?? '')); $sb = ck_stage_key((string)($b['stage'] ?? ''));
          $oa = $sa === '' ? 999 : ($ord[$sa] ?? 500); $ob = $sb === '' ? 999 : ($ord[$sb] ?? 500);
          return $oa <=> $ob;
        });
      }
      $curStage = '__init__';
    ?>
    <div class="rf-grid">
      <?php foreach ($renderList as $r): $appr=($r['status']??'')==='approved'; $kind=$r['kind']??'view'; $tc=$kindColor[$kind]??'#9CA0AC'; $rfile=$r['file']??''; $rid=$r['id']??''; $rst=ck_stage_key((string)($r['stage']??'')); $isStageable=in_array($kind,['face','body','view'],true); ?>
      <?php if ($isCharGroup && $hasStaged && $rst !== $curStage): $curStage=$rst; ?>
      <div class="rf-substage"><?php if ($rst===''): ?>◇ any stage <span class="rf-subnote">— used at every stage</span><?php else: ?>▸ <?= h(ck_stage_label($rst)) ?><?php endif; ?></div>
      <?php endif; ?>
      <div class="rf-cardx<?= $appr?' ok':'' ?>" data-rid="<?= h($rid) ?>" data-status="<?= h($r['status'] ?? '') ?>">
        <span class="rf-tag" style="background:<?= $tc ?>"><?= h($kind) ?></span>
        <?php if ($locked&&$appr): ?><span class="rf-lk">🔒</span><?php endif; ?>
        <?php if ($rfile): ?><img loading="lazy" class="rf-img" src="img.php?p=<?= h(urlencode($id)) ?>&f=<?= h(urlencode($rfile)) ?>&t=1" data-full="img.php?p=<?= h(urlencode($id)) ?>&f=<?= h(urlencode($rfile)) ?>" alt=""><?php endif; ?>
        <div class="rf-body">
          <?php if ($rst!=='' && $isStageable): ?><div class="rf-stagerow"><span class="rf-stage" title="transformation stage"><?= h($rst) ?></span></div><?php endif; ?>
          <?php if ($locked): ?>
            <div style="font-size:12px;color:#dfe1e7"><?= h($r['char']?:'') ?><?= !empty($r['label'])?' · '.h($r['label']):'' ?></div>
            <span class="rf-st <?= $appr?'rf-ok':'rf-need' ?>"><?= $appr?'approved':'needed' ?></span>
          <?php else: ?>
            <button type="button" class="rf-ocr" title="Read text printed on this image and fill the label">📖 read text</button>
            <form method="post" action="<?= h($post) ?>">
              <?= csrf_field() ?><input type="hidden" name="ret" value="refs"><input type="hidden" name="do" value="editref"><input type="hidden" name="rid" value="<?= h($rid) ?>">
              <select name="kind" class="rf-in"><?php foreach ($kindOpts as $kv=>$kl): ?><option value="<?= $kv ?>"<?= $kind===$kv?' selected':'' ?>><?= $kl ?></option><?php endforeach; ?></select>
              <input type="text" name="char" class="rf-in" value="<?= h($r['char']??'') ?>" placeholder="character">
              <input type="text" name="label" class="rf-in" value="<?= h($r['label']??'') ?>" placeholder="label">
              <?php if ($isStageable): ?><select name="stage" class="rf-in" title="transformation stage — leave 'any' if this look doesn't change across the arc"><option value="">stage: any</option><?php foreach (STAGE_OPTS as $sv=>$sl): ?><option value="<?= h($sv) ?>"<?= $rst===$sv?' selected':'' ?>><?= h($sl) ?></option><?php endforeach; ?></select><?php endif; ?>
              <div class="rf-btns">
                <button name="status" value="<?= $appr?'needed':'approved' ?>"><?= $appr?'✓ approved':'mark ok' ?></button>
                <button>save</button>
              </div>
            </form>
            <form method="post" action="<?= h($post) ?>" style="margin-top:4px"><?= csrf_field() ?><input type="hidden" name="ret" value="refs"><input type="hidden" name="do" value="removeref"><input type="hidden" name="rid" value="<?= h($rid) ?>"><div class="rf-btns"><button class="rf-rm" onclick="return confirm('Remove this reference?')">✕ remove</button></div></form>
          <?php endif; ?>
          <?php if (!empty($r['prov']) || !empty($r['role'])): ?>
          <div class="rf-prov" title="<?= h((string)($r['prov'] ?? '')) ?>"><?php if (!empty($r['role'])): ?><span class="rf-role"><?= h((string)$r['role']) ?></span> <?php endif; ?><?php if (!empty($r['prov'])): ?><span><?= h(mb_strimwidth((string)$r['prov'], 0, 64, '…')) ?></span><?php endif; ?></div>
          <?php endif; ?>
        </div>
      </div>
      <?php endforeach; ?>
    </div>
  </section>
  <?php endforeach; ?>
  <?php else: ?>
  <div class="rf-empty">No references yet. Use <b>➕ Add references</b> above to drop in a batch — faces, characters, props, scenes. Blank character + many files auto-groups them by look; then name the groups, set kinds, approve and lock.</div>
  <?php endif; ?>
</main>

<div class="rf-lb" id="lb"><img id="lbimg" src="" alt=""></div>
<div class="ai-ov" id="aiov">
  <div class="ai-box">
    <div class="ai-title">✨ AI sorting references</div>
    <div class="ai-sub" id="aitxt">Starting…</div>
    <div class="ai-track"><div class="ai-fill" id="aibar"></div></div>
    <img class="ai-cur" id="aicur" src="" alt="">
    <button class="btn" id="aicancel" type="button">Cancel</button>
  </div>
</div>
<script src="https://cdn.jsdelivr.net/npm/tesseract.js@5/dist/tesseract.min.js"></script>
<script>
(function(){    // lightbox
  var lb=document.getElementById('lb'), im=document.getElementById('lbimg');
  document.addEventListener('click', function(e){
    var t=e.target.closest('.rf-img');
    if(t){ im.src=t.dataset.full||t.src; lb.classList.add('open'); return; }
    if(e.target===lb || e.target===im){ lb.classList.remove('open'); }
  });
  document.addEventListener('keydown', function(e){ if(e.key==='Escape') lb.classList.remove('open'); });
})();
(function(){    // browser OCR — read baked-in text into the label/char fields (no key, nothing leaves your browser)
  var worker=null, loading=null;
  function ensureWorker(){
    if(worker) return Promise.resolve(worker);
    if(loading) return loading;
    if(typeof Tesseract==='undefined') return Promise.reject(new Error('lib'));
    loading = Tesseract.createWorker('eng').then(function(w){ worker=w; return w; });
    return loading;
  }
  function clean(text){
    return (text||'').split('\n').map(function(s){ return s.replace(/\s+/g,' ').trim(); })
      .filter(function(s){ if(s.length<2) return false; var a=(s.match(/[A-Za-z]/g)||[]).length; return a>=2 && a>=s.length*0.4; });
  }
  function titleCase(s){ return s.toLowerCase().replace(/\b[a-z]/g, function(c){ return c.toUpperCase(); }); }
  function ocrCard(card, btn){
    var img=card.querySelector('.rf-img'); if(!img) return Promise.resolve();
    var url=img.dataset.full||img.src, old=btn.dataset.lbl || btn.textContent;
    btn.dataset.lbl=old; btn.disabled=true; btn.textContent='📖 reading…';
    return ensureWorker().then(function(w){ return w.recognize(url); }).then(function(res){
      var lines=clean(res.data && res.data.text);
      if(!lines.length){ btn.textContent='no text found'; return; }
      var lab=card.querySelector('input[name="label"]'), ch=card.querySelector('input[name="char"]');
      if(lab){ lab.value=lines.join(' · ').slice(0,80); lab.style.borderColor='#7A7FEC'; }
      if(ch && (!ch.value.trim() || /^cast\s+[a-z0-9]+$/i.test(ch.value.trim()))){ ch.value=titleCase(lines[0]).slice(0,40); ch.style.borderColor='#7A7FEC'; }
      btn.textContent='✓ review & save';
    }).catch(function(e){ btn.textContent = (e && e.message==='lib') ? 'OCR not loaded' : 'OCR failed'; }).then(function(){
      setTimeout(function(){ btn.textContent=btn.dataset.lbl||'📖 read text'; btn.disabled=false; }, 2200);
    });
  }
  document.addEventListener('click', function(e){
    var b=e.target.closest('.rf-ocr'); if(!b) return;
    var card=b.closest('.rf-cardx'); if(card) ocrCard(card,b);
  });
  var all=document.getElementById('ocrall');
  if(all) all.addEventListener('click', async function(){
    var cards=[].slice.call(document.querySelectorAll('.rf-cardx')); all.disabled=true;
    for(var i=0;i<cards.length;i++){ var b=cards[i].querySelector('.rf-ocr'); if(b){ all.textContent='📖 reading '+(i+1)+'/'+cards.length+'…'; await ocrCard(cards[i],b); } }
    all.textContent='✓ all read — review & save'; setTimeout(function(){ all.textContent='📖 Read text on all'; all.disabled=false; }, 2500);
  });
})();
(function(){    // ✨ AI sort with a progress overlay — browser drives it one ref at a time (real progress bar, no PHP timeout)
  var root=document.getElementById('refs'); if(!root) return;
  var PID=root.dataset.id, CSRF=root.dataset.csrf, AI_ON=<?= $aiOn?'true':'false' ?>;
  var form=document.getElementById('aisortform'); if(!form) return;
  form.addEventListener('submit', function(e){ if(!AI_ON) return; e.preventDefault(); run(); });
  function apply(card,j){
    var k=card.querySelector('select[name="kind"]'); if(k&&j.kind) k.value=j.kind;
    var c=card.querySelector('input[name="char"]'); if(c&&j.char) c.value=j.char;
    var l=card.querySelector('input[name="label"]'); if(l&&j.label) l.value=j.label;
    card.style.outline='2px solid #5DCAA5';
  }
  function run(){
    var cards=[].slice.call(document.querySelectorAll('.rf-cardx')).filter(function(c){ return (c.dataset.status||'')!=='approved'; });
    var ov=document.getElementById('aiov'), bar=document.getElementById('aibar'), txt=document.getElementById('aitxt'),
        cur=document.getElementById('aicur'), btn=document.getElementById('aicancel');
    ov.classList.add('open'); bar.style.width='0%'; cur.style.display='none'; btn.textContent='Cancel';
    if(!cards.length){ txt.textContent='Nothing to sort — every reference is already approved.'; btn.textContent='Close'; btn.onclick=function(){ ov.classList.remove('open'); }; return; }
    var total=cards.length, done=0, ok=0, fail=0, cancelled=false;
    btn.onclick=function(){ cancelled=true; };
    txt.textContent='Sorting 0 / '+total+'…';
    (async function(){
      for(var i=0;i<cards.length;i++){
        if(cancelled) break;
        var card=cards[i], rid=card.dataset.rid||'';
        txt.textContent='Sorting '+(i+1)+' / '+total+'…';
        var im=card.querySelector('.rf-img'); if(im){ cur.src=im.src; cur.style.display='block'; }
        try{
          var r=await fetch('creator.php?p='+encodeURIComponent(PID), {method:'POST', headers:{'X-CSRF':CSRF}, body:new URLSearchParams({p:PID,do:'aisort_one',rid:rid,csrf:CSRF})});
          var j=await r.json();
          if(j&&j.ok){ ok++; apply(card,j); } else { fail++; }
        }catch(e){ fail++; }
        done++; bar.style.width=Math.round(done/total*100)+'%';
      }
      txt.textContent=(cancelled?'Stopped — ':'Done — ')+ok+' sorted'+(fail?(' · '+fail+' skipped (often explicit images the filter blocks — set those by hand)'):'');
      btn.textContent='Close & review'; btn.onclick=function(){ location.reload(); };
    })();
  }
})();
</script>
<script>
(function(){    // 🌍 real-photo env-ref gather brief — copy a ready instruction for a Claude Code session
  var b=document.getElementById('envbrief'); if(!b) return;
  var root=document.getElementById('refs'); var PID=root?root.dataset.id:'';
  b.addEventListener('click', function(){
    var loc=(document.getElementById('envloc').value||'').trim()||'<LOCATION>';
    var slug=loc.toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+$/g,'')||'location';
    var brief=[
      'Source real-photo environment references for the Comic Studio project "'+PID+'", location: "'+loc+'".',
      '',
      '1. Use the reference-gathering skill to gather 5-7 REAL photos of "'+loc+'" into references/locations/'+slug+'/ with provenance (prefer CC0 / Wikimedia / press-kit sources).',
      '2. Convert each to the project’s CGI/DAZ look -> references/locations/'+slug+'/cgi/  (see skills/comic-production/references/environment-references.md).',
      '3. Push them into the studio as scene refs:',
      '   studio/tools/push-env-refs.sh --project '+PID+' --location "'+loc+'" --dir references/locations/'+slug+'/ --lock',
      '',
      'Full SOP: studio/docs/REAL-PHOTO-ENV-REFS.md'
    ].join('\n');
    var msg=document.getElementById('envbriefmsg');
    var done=function(t){ msg.textContent=t; setTimeout(function(){ msg.textContent=''; }, 2600); };
    if(navigator.clipboard&&navigator.clipboard.writeText) navigator.clipboard.writeText(brief).then(function(){done('copied ✓');},function(){window.prompt('Copy this brief:',brief);done('shown');});
    else { window.prompt('Copy this brief:',brief); done('shown'); }
  });
})();
</script>
</body></html>
