<?php
declare(strict_types=1);
require_once __DIR__ . '/inc/boot.php';
require_auth();

$id = preg_replace('/[^a-z0-9-]/', '', (string)($_GET['p'] ?? ''));
$proj = project_get($id);
if (!$proj) { header('Location: index.php'); exit; }

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    csrf_check();
    $do = $_POST['do'] ?? '';
    if ($do === 'save_meta') {
        $all = projects_all();
        foreach ($all as &$p) if (($p['id']??'')===$id) {
            $p['name']   = mb_substr(trim($_POST['name'] ?? $p['name']),0,120);
            $p['status'] = in_array($_POST['status']??'', STATUSES, true) ? $_POST['status'] : $p['status'];
            $p['stage']  = in_array($_POST['stage']??'', STAGES, true) ? $_POST['stage'] : $p['stage'];
            $p['tags']   = array_values(array_filter(array_map('trim', preg_split('/,/', (string)($_POST['tags']??'')))));
            $p['notes']  = trim($_POST['notes'] ?? '');
            $p['updated']= date('c');
        }
        unset($p); projects_save($all);
        header('Location: project.php?p=' . urlencode($id)); exit;
    }
    if ($do === 'delete_project') {
        projects_save(array_values(array_filter(projects_all(), fn($p)=>($p['id']??'')!==$id)));
        @array_map('unlink', glob(project_dir($id) . '/thumb/*') ?: []);
        @array_map('unlink', glob(project_dir($id) . '/*') ?: []);
        @unlink(imeta_path($id));
        header('Location: index.php'); exit;
    }
}

$imgs = images_all($id);
$groups = [];
foreach ($imgs as $im) { $g = $im['group'] ?? ''; $groups[$g === '' ? 'Ungrouped' : $g][] = $im; }
$bn = fn($s) => preg_match('/(\d+)/', (string)$s, $m) ? (int)$m[1] : 9999;
uksort($groups, function($a,$b) use ($bn){ if($a==='Ungrouped') return 1; if($b==='Ungrouped') return -1; return $bn($a) <=> $bn($b) ?: strcmp($a,$b); });
?><!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark"><meta name="robots" content="noindex,nofollow">
<title><?= h($proj['name']) ?> · Studio</title><link rel="stylesheet" href="assets/studio.css?v=<?= @filemtime(STUDIO_ROOT . '/assets/studio.css') ?>"></head><body>
<header class="topbar"><div class="brand"><span class="dot"></span> Comic Studio</div>
  <a class="ghost" href="index.php">← Projects</a><span class="spacer"></span>
  <span class="ghost"><?= h(current_studio_user()) ?></span> <a class="ghost" href="login.php?do=logout">Log out</a></header>
<main class="wrap" id="proj" data-id="<?= h($id) ?>" data-csrf="<?= h(csrf()) ?>">
  <?php $totalN = count($imgs);
        $purgeN = count(array_filter($imgs, fn($x) => ($x['rating'] ?? '') !== 'good' && empty($x['accepted']))); ?>
  <div class="pagehead"><h1><?= h($proj['name']) ?></h1>
    <span class="phead-actions">
      <?php if ($totalN): ?>
        <a class="btn sm" href="export.php?p=<?= h(urlencode($id)) ?>">⬇ Download all (<?= $totalN ?>)</a>
        <a class="btn sm primary" href="port.php?p=<?= h(urlencode($id)) ?>">→ Port to comic</a>
      <?php endif; ?>
      <?php if ($purgeN): ?><button class="btn sm danger" id="purgebtn" data-n="<?= $purgeN ?>" data-kept="<?= count($imgs) - $purgeN ?>">🧹 Purge <?= $purgeN ?></button><?php endif; ?>
    </span>
  </div>

  <details class="card metabox">
    <summary>Project details — <span class="badge" style="--c:#1D9E75"><?= h($proj['status']) ?></span> · <?= h($proj['stage']) ?></summary>
    <form method="post" style="margin-top:12px">
      <?= csrf_field() ?><input type="hidden" name="do" value="save_meta">
      <div class="row">
        <label class="grow">Name<input name="name" value="<?= h($proj['name']) ?>"></label>
        <label>Status<select name="status"><?php foreach (STATUSES as $s): ?><option<?= $proj['status']===$s?' selected':'' ?>><?= $s ?></option><?php endforeach; ?></select></label>
        <label>Stage<select name="stage"><?php foreach (STAGES as $s): ?><option<?= $proj['stage']===$s?' selected':'' ?>><?= $s ?></option><?php endforeach; ?></select></label>
      </div>
      <label>Tags (comma-separated)<input name="tags" value="<?= h(implode(', ', $proj['tags'] ?? [])) ?>"></label>
      <label>Notes<textarea name="notes" rows="3"><?= h($proj['notes'] ?? '') ?></textarea></label>
      <div class="actions">
        <button class="btn primary">Save</button>
        <button class="btn danger" name="do" value="delete_project" onclick="return confirm('Delete this project and its images?')">Delete project</button>
      </div>
    </form>
  </details>

  <div id="dropzone" class="dropzone">
    <input type="file" id="fileinput" accept="image/*" multiple hidden>
    <p><strong>Drag &amp; drop draft images here</strong> or <button type="button" class="btn" id="pickbtn">choose files</button></p>
    <p class="muted">JPG / PNG / WebP. Auto-downscaled + thumbnailed on upload.</p>
    <div id="uploadbar" class="uploadbar" hidden><div></div></div>
  </div>

  <p class="muted khint">Reorder beats with ▲▼ or type a number. <b>Compare</b> opens a lightbox: <b>←/→</b> to flip, <b>Enter</b> picks the winner. In the grid: hover + <b>G</b>/<b>B</b>/<b>A</b>.</p>
  <?php if ($imgs): ?><div class="seqbar"><button class="btn sm" id="oneeach" type="button">▭ One beat each</button> <span class="muted">— a sequence (not variants)? Make every image its own panel/page, all kept. Then delete any dupes &amp; Port.</span></div><?php endif; ?>

  <div id="gallery">
  <?php $pos = 0; foreach ($groups as $gname => $list): $isU = ($gname === 'Ungrouped'); if (!$isU) $pos++; ?>
    <section class="beat" data-beat="<?= h($gname) ?>">
      <div class="beat-head">
        <?php if (!$isU): ?>
          <span class="beat-move">
            <button class="rb bmove" data-dir="up" title="Move up">▲</button>
            <button class="rb bmove" data-dir="down" title="Move down">▼</button>
          </span>
          <input class="beat-pos" type="number" min="1" value="<?= $pos ?>" title="Type a position then Enter">
        <?php endif; ?>
        <h2 class="gtitle"><?= h($gname) ?> <span class="muted"><?= count($list) ?></span></h2>
        <span class="spacer"></span>
        <?php if (!$isU && count($list) > 1): ?><button class="btn sm bcompare">Compare ▦</button><?php endif; ?>
      </div>
      <div class="shots">
        <?php foreach ($list as $im): $f = $im['file']; ?>
          <figure class="shot rate-<?= h($im['rating'] ?? 'unrated') ?><?= !empty($im['accepted'])?' kept':'' ?>" tabindex="0"
                  data-file="<?= h($f) ?>" data-rating="<?= h($im['rating'] ?? 'unrated') ?>" data-accepted="<?= !empty($im['accepted'])?'1':'0' ?>">
            <div class="shot-img"><?php if (!empty($im['ported_to'])): ?><span class="ported-tag" title="Ported to <?= h($im['ported_to']) ?>">ported</span><?php endif; ?><?php $an = $im['analysis'] ?? null; if ($an): $df = $an['defects'] ?? []; ?><span class="an-tag<?= $df ? ' has-def' : '' ?>" title="<?= h(trim(($an['caption'] ?? '') . ($df ? ' — ⚠ ' . implode(', ', $df) : ''))) ?>"><?= $df ? '⚠' . count($df) : '🔍' ?></span><?php endif; ?><img loading="lazy" src="img.php?p=<?= h(urlencode($id)) ?>&f=<?= h(urlencode($f)) ?>&t=1" alt=""></div>
            <div class="shot-bar">
              <button class="rb good" data-act="good" title="Good (G)">▲</button>
              <button class="rb bad"  data-act="bad"  title="Bad (B)">▼</button>
              <button class="rb keep" data-act="keep" title="Keep (A)">★</button>
              <span class="spacer"></span>
              <button class="rb cover" data-act="cover" title="Set as cover">◳</button>
              <button class="rb del"  data-act="delete" title="Delete">✕</button>
            </div>
          </figure>
        <?php endforeach; ?>
      </div>
    </section>
  <?php endforeach; ?>
  <?php if (!$imgs): ?><p class="muted" id="empty">No images yet — drop some above.</p><?php endif; ?>
  </div>
</main>

<div id="lightbox" class="lb" hidden>
  <button class="lb-x" type="button" title="Close (Esc)">✕</button>
  <button class="lb-arrow lb-prev" type="button" title="Previous (←)">‹</button>
  <div class="lb-stage"><img class="lb-img" src="" alt=""></div>
  <button class="lb-arrow lb-next" type="button" title="Next (→)">›</button>
  <div class="lb-analysis" hidden></div>
  <div class="lb-bar">
    <span class="lb-count muted"></span>
    <span class="lb-beat muted"></span>
    <span class="spacer"></span>
    <button class="lb-rate lb-good" type="button" title="Good (G)">▲</button>
    <button class="lb-rate lb-bad" type="button" title="Bad (B)">▼</button>
    <button class="lb-rate lb-star" type="button" title="Keep (A)">★</button>
    <button class="lb-rate lb-del" type="button" title="Delete">🗑</button>
    <button class="btn primary lb-keep" type="button">🏆 Winner (Enter)</button>
  </div>
</div>
<?php $analysis = []; foreach ($imgs as $im) if (!empty($im['analysis'])) $analysis[$im['file']] = $im['analysis']; ?>
<script>window.STUDIO_ANALYSIS = <?= json_encode($analysis, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE) ?>;</script>
<script src="assets/studio.js?v=<?= @filemtime(STUDIO_ROOT . '/assets/studio.js') ?>"></script></body></html>
