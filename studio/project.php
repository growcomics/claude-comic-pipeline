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
uksort($groups, fn($a,$b)=> $a==='Ungrouped' ? 1 : ($b==='Ungrouped' ? -1 : strcmp($a,$b)));
?><!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark"><meta name="robots" content="noindex,nofollow">
<title><?= h($proj['name']) ?> · Studio</title><link rel="stylesheet" href="assets/studio.css"></head><body>
<header class="topbar"><div class="brand"><span class="dot"></span> Comic Studio</div>
  <a class="ghost" href="index.php">← Projects</a><span class="spacer"></span>
  <span class="ghost"><?= h(current_studio_user()) ?></span> <a class="ghost" href="login.php?do=logout">Log out</a></header>
<main class="wrap" id="proj" data-id="<?= h($id) ?>" data-csrf="<?= h(csrf()) ?>">
  <div class="pagehead"><h1><?= h($proj['name']) ?></h1></div>

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

  <p class="muted khint">Tip: hover an image and press <b>G</b> good · <b>B</b> bad · <b>A</b> keep/unkeep.</p>

  <div id="gallery">
  <?php foreach ($groups as $gname => $list): ?>
    <h2 class="gtitle"><?= h($gname) ?> <span class="muted"><?= count($list) ?></span></h2>
    <div class="shots">
      <?php foreach ($list as $im): $f = $im['file']; ?>
        <figure class="shot rate-<?= h($im['rating'] ?? 'unrated') ?><?= !empty($im['accepted'])?' kept':'' ?>" tabindex="0"
                data-file="<?= h($f) ?>" data-rating="<?= h($im['rating'] ?? 'unrated') ?>" data-accepted="<?= !empty($im['accepted'])?'1':'0' ?>">
          <div class="shot-img"><img loading="lazy" src="img.php?p=<?= h(urlencode($id)) ?>&f=<?= h(urlencode($f)) ?>&t=1" alt=""></div>
          <div class="shot-bar">
            <button class="rb good" data-act="good" title="Good (G)">▲</button>
            <button class="rb bad"  data-act="bad"  title="Bad (B)">▼</button>
            <button class="rb keep" data-act="keep" title="Keep (A)">★</button>
            <span class="spacer"></span>
            <a class="rb" href="img.php?p=<?= h(urlencode($id)) ?>&f=<?= h(urlencode($f)) ?>" target="_blank" title="Full size">⤢</a>
            <button class="rb cover" data-act="cover" title="Set as cover">◳</button>
            <button class="rb del"  data-act="delete" title="Delete">✕</button>
          </div>
        </figure>
      <?php endforeach; ?>
    </div>
  <?php endforeach; ?>
  <?php if (!$imgs): ?><p class="muted" id="empty">No images yet — drop some above.</p><?php endif; ?>
  </div>
</main>
<script src="assets/studio.js"></script></body></html>
