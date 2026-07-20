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
<title>Comic Studio</title><link rel="icon" href="assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="assets/studio.css"></head><body>
<header class="topbar">
  <div class="brand"><a href="cc.php" style="color:inherit;text-decoration:none"><span class="dot"></span> ⌘ Command Center</a></div>
  <a class="ghost" href="index.php" style="color:var(--text);font-weight:700">🎬 Comic Studio</a>
  <a class="ghost" href="ops.php">📋 Ops Board</a>
  <span class="spacer"></span><span class="ghost"><?= h(current_studio_user()) ?></span> <a class="ghost" href="help.php">❔ How it works</a> <a class="ghost" href="login.php?do=logout">Log out</a></header>
<main class="wrap">
  <div class="pagehead"><h1>Projects <span class="muted"><?= count($projects) ?></span></h1></div>

  <!-- GUIDE BANNER -->
  <a class="card" href="help.php" style="display:flex;align-items:center;gap:18px;flex-wrap:wrap;margin-bottom:16px;border-color:#3a3470;background:linear-gradient(135deg,rgba(122,127,236,.16),rgba(29,158,117,.08))">
    <svg width="300" height="46" viewBox="0 0 372 56" style="flex:none;max-width:46%;height:auto" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <defs><marker id="gba" markerWidth="7" markerHeight="7" refX="5" refY="2.6" orient="auto"><path d="M0,0 L5,2.6 L0,5.2 Z" fill="#6F7380"/></marker></defs>
      <g font-size="18" text-anchor="middle">
        <circle cx="22" cy="28" r="17" fill="#14151C" stroke="#EF9F27" stroke-width="1.5"/><text x="22" y="34">🗂</text>
        <circle cx="92" cy="28" r="17" fill="#14151C" stroke="#5BA7E6" stroke-width="1.5"/><text x="92" y="34">📜</text>
        <circle cx="162" cy="28" r="17" fill="#14151C" stroke="#378ADD" stroke-width="1.5"/><text x="162" y="34">📑</text>
        <circle cx="232" cy="28" r="17" fill="#14151C" stroke="#7A7FEC" stroke-width="1.5"/><text x="232" y="34">🍌</text>
        <circle cx="302" cy="28" r="17" fill="#14151C" stroke="#4FB3A0" stroke-width="1.5"/><text x="302" y="34">🔄</text>
        <circle cx="356" cy="28" r="14" fill="#14151C" stroke="#1D9E75" stroke-width="1.5"/><text x="356" y="33" font-size="15" font-weight="800" fill="#1D9E75">✓</text>
      </g>
      <g stroke="#6F7380" stroke-width="1.5" marker-end="url(#gba)">
        <line x1="41" y1="28" x2="71" y2="28"/><line x1="111" y1="28" x2="141" y2="28"/>
        <line x1="181" y1="28" x2="211" y2="28"/><line x1="251" y1="28" x2="281" y2="28"/>
        <line x1="321" y1="28" x2="338" y2="28"/>
      </g>
    </svg>
    <div style="flex:1;min-width:180px">
      <div style="font-weight:800;font-size:16px;color:#fff">📖 New here? Read the guide</div>
      <div class="muted" style="font-size:13px;margin-top:3px">The full workflow — references → script → pages → generate in Flow → review — with diagrams.</div>
    </div>
    <span class="btn primary" style="flex:none">Open the guide →</span>
  </a>

  <div style="display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap">
    <a class="btn sm primary" href="creator.php">🎬 Comic Creator</a>
    <a class="btn sm" href="overview.php">📋 Project overview</a>
    <a class="btn sm" href="import.php">📄 Comic → 3D Import</a>
    <a class="btn sm" href="growgetter.php">🎲 Random comic (SFW)</a>
  </div>

  <details class="card newproj"<?= $projects ? '' : ' open' ?>>
    <summary>+ New project</summary>
    <form method="post" class="row" style="margin-top:12px">
      <?= csrf_field() ?><input type="hidden" name="do" value="create">
      <input name="name" placeholder="Project name" required style="flex:1">
      <button class="btn primary">Create</button>
    </form>
  </details>

  <?php $bkey = (s_read(SDATA . '/bridge.json', [])['key'] ?? ''); ?>
  <details class="card newproj">
    <summary>⚙ Flow import (browser extension)</summary>
    <div style="margin-top:10px;font-size:13px;color:var(--muted);max-width:560px">
      <p>Install the <strong>Flow → 3DMC Studio</strong> extension, open it on a Google Flow project, click its ⚙ and paste the values below. Then “Send to Studio” drops a Flow project’s images straight into a project here.</p>
      <div style="font-size:12px;margin:8px 0 4px">Bridge URL</div>
      <input readonly value="https://3dmusclecomics.com/studio/bridge.php" onclick="this.select()">
      <div style="font-size:12px;margin:8px 0 4px">Your Studio key (keep private)</div>
      <input readonly value="<?= h($bkey) ?>" onclick="this.select()">
    </div>
  </details>

  <?php if (!$projects): ?>
    <p class="muted">No projects yet — create one above.</p>
  <?php else: ?>
  <div class="grid">
    <?php foreach ($projects as $p):
      $imgs = images_all($p['id']); $n = count($imgs);
      $acc = 0; foreach ($imgs as $im) if (!empty($im['accepted'])) $acc++;
      $cov = ($p['cover'] ?? null) ?: ck_pick_cover($imgs);   // explicit cover, else best kept/rated panel (never a ref)
    ?>
    <a class="pcard" href="creator.php?p=<?= h(urlencode($p['id'])) ?>">
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

