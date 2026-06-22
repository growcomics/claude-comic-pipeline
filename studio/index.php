<?php
declare(strict_types=1);
require_once __DIR__ . '/inc/boot.php';
require_auth();

if ($_SERVER['REQUEST_METHOD'] === 'POST' && ($_POST['do'] ?? '') === 'create') {
    csrf_check();
    $name = trim($_POST['name'] ?? '');
    if ($name !== '') {
        $all = projects_all();
        $base = slugify($name); $id = $base; $i = 2;
        $taken = array_column($all, 'id');
        while (in_array($id, $taken, true)) $id = $base . '-' . $i++;
        array_unshift($all, [
            'id'=>$id, 'name'=>mb_substr($name,0,120),
            'status'=>'active', 'stage'=>'page-build', 'tags'=>[], 'notes'=>'',
            'cover'=>null, 'created'=>date('c'), 'updated'=>date('c'),
        ]);
        projects_save($all);
        header('Location: project.php?p=' . urlencode($id)); exit;
    }
    header('Location: index.php'); exit;
}

$projects = projects_all();
function status_color(string $s): string { return ['active'=>'#1D9E75','on-hold'=>'#EF9F27','done'=>'#378ADD','archived'=>'#6F7380'][$s] ?? '#6F7380'; }
?><!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark"><meta name="robots" content="noindex,nofollow">
<title>Comic Studio</title><link rel="stylesheet" href="assets/studio.css"></head><body>
<header class="topbar"><div class="brand"><span class="dot"></span> Comic Studio</div>
  <span class="spacer"></span><span class="ghost"><?= h(current_studio_user()) ?></span> <a class="ghost" href="login.php?do=logout">Log out</a></header>
<main class="wrap">
  <div class="pagehead"><h1>Projects <span class="muted"><?= count($projects) ?></span></h1></div>

  <details class="card newproj"<?= $projects ? '' : ' open' ?>>
    <summary>+ New project</summary>
    <form method="post" class="row" style="margin-top:12px">
      <?= csrf_field() ?><input type="hidden" name="do" value="create">
      <input name="name" placeholder="Project name" required style="flex:1">
      <button class="btn primary">Create</button>
    </form>
  </details>

  <?php if (!$projects): ?>
    <p class="muted">No projects yet — create one above.</p>
  <?php else: ?>
  <div class="grid">
    <?php foreach ($projects as $p):
      $imgs = images_all($p['id']); $n = count($imgs);
      $acc = 0; foreach ($imgs as $im) if (!empty($im['accepted'])) $acc++;
      $cov = $p['cover'] ?? null;
    ?>
    <a class="pcard" href="project.php?p=<?= h(urlencode($p['id'])) ?>">
      <div class="pcover">
        <?php if ($cov): ?><img loading="lazy" src="img.php?p=<?= h(urlencode($p['id'])) ?>&f=<?= h(urlencode($cov)) ?>&t=1" alt="">
        <?php else: ?><span class="pcover-empty"><?= h(strtoupper(substr($p['name'],0,2))) ?></span><?php endif; ?>
      </div>
      <div class="pmeta">
        <div class="pname"><?= h($p['name']) ?></div>
        <div class="prow">
          <span class="badge" style="--c:<?= status_color($p['status']??'') ?>"><?= h($p['status']??'') ?></span>
          <span class="muted"><?= h($p['stage']??'') ?></span>
        </div>
        <div class="muted psub"><?= $n ?> image<?= $n===1?'':'s' ?><?= $acc?(' · '.$acc.' kept'):'' ?></div>
      </div>
    </a>
    <?php endforeach; ?>
  </div>
  <?php endif; ?>
</main></body></html>
