<?php
// Port a project's images (pages) into the 3dmusclecomics catalog as a (draft)
// part — new series / existing series, new part / append to an existing part.
// Reuses the CMS's content.json (atomic same-pattern write) + copies pages into
// assets/comics/. New parts land as DRAFT so nothing goes public until you
// publish it in the admin. Pages stay in Studio (marked ported). The project's
// current contents = your curated set after triage + purge, in beat/page order.
declare(strict_types=1);
require_once __DIR__ . '/inc/boot.php';
require_auth();

define('CMS_CONTENT', dirname(STUDIO_ROOT) . '/admin/data/content.json');
define('CMS_COMICS_DIR', dirname(STUDIO_ROOT) . '/assets/comics');

function cms_read() { return s_read(CMS_CONTENT, null); }            // null if missing/corrupt
function part_dir_n($n): string { return 'part-' . str_pad((string)(int)$n, 2, '0', STR_PAD_LEFT); }
function cms_valid($c): bool { return is_array($c) && isset($c['series']) && is_array($c['series']); }

$id = preg_replace('/[^a-z0-9-]/', '', (string)($_GET['p'] ?? $_POST['p'] ?? ''));
$proj = project_get($id);
if (!$proj) { header('Location: index.php'); exit; }

$pages = images_all($id);
usort($pages, fn($a,$b)=> (preg_match('/(\d+)/',$a['group']??'',$m)?(int)$m[1]:9999) <=> (preg_match('/(\d+)/',$b['group']??'',$n)?(int)$n[1]:9999) ?: (($a['ts']??0) <=> ($b['ts']??0)));

$err = ''; $done = '';
if ($_SERVER['REQUEST_METHOD'] === 'POST' && ($_POST['do'] ?? '') === 'port') {
    csrf_check();
    $cms = cms_read();
    if (!cms_valid($cms))            $err = 'Could not read the catalog safely — aborted (nothing changed).';
    elseif (!$pages)                 $err = 'No images to port — add some first.';
    else {
        $serSel = (string)($_POST['series'] ?? '');
        $partSel = (string)($_POST['part'] ?? '__new__');
        // resolve / create series
        $si = -1;
        if ($serSel === '__new__') {
            $title = trim($_POST['new_title'] ?? '');
            if ($title === '') $err = 'Name the new series.';
            else {
                $sid = slugify($title); $taken = array_column($cms['series'], 'id'); $base=$sid; $k=2;
                while (in_array($sid, $taken, true)) $sid = $base.'-'.$k++;
                $cms['series'][] = ['id'=>$sid,'title'=>mb_substr($title,0,120),'short'=>strtoupper(substr(preg_replace('/[^A-Za-z]/','',$title),0,2) ?: 'NS'),
                    'status'=>'ongoing','color'=>'#534AB7','accent'=>'#CECBF6','cover'=>null,'blurb'=>'','parts'=>[]];
                $si = count($cms['series']) - 1;
            }
        } else {
            foreach ($cms['series'] as $i=>$s) if (($s['id']??'')===$serSel) { $si=$i; break; }
            if ($si < 0) $err = 'Pick a series.';
        }

        if (!$err) {
            $sid = $cms['series'][$si]['id'];
            $parts = $cms['series'][$si]['parts'] ?? [];
            // resolve / create part
            if ($partSel === '__new__') {
                $n = 0; foreach ($parts as $p) $n = max($n, (int)($p['n'] ?? 0)); $n++;
                $pi = count($parts);
                $parts[$pi] = ['id'=>nid(),'n'=>$n,'title'=>'','date'=>date('Y-m-d'),'teaser'=>'',
                    'status'=>'draft','publishAt'=>'','early'=>false,'publicDate'=>'','patreonUrl'=>'','pages'=>[]];
            } else {
                $pi = -1; foreach ($parts as $i=>$p) if ((string)($p['n']??'')===$partSel) { $pi=$i; break; }
                if ($pi < 0) $err = 'Pick a part.';
            }

            if (!$err) {
                $n = (int)$parts[$pi]['n'];
                $dir = CMS_COMICS_DIR . '/' . $sid . '/' . part_dir_n($n);
                @mkdir($dir, 0755, true);
                $existing = $parts[$pi]['pages'] ?? [];
                $start = count($existing) + 1; $i = $start; $newpages = [];
                foreach ($pages as $x) {
                    $src = project_dir($id) . '/' . $x['file'];
                    if (!is_file($src)) continue;
                    $ext = ext_of($x['file']) ?: 'png';
                    $name = sprintf('page-%02d.%s', $i++, $ext);
                    if (@copy($src, $dir . '/' . $name)) $newpages[] = $name;
                }
                if (!$newpages) $err = 'Could not copy any pages — aborted.';
                else {
                    $parts[$pi]['pages'] = array_merge($existing, $newpages);
                    $cms['series'][$si]['parts'] = $parts;
                    if (!s_write(CMS_CONTENT, $cms)) $err = 'Could not save the catalog.';
                    else {
                        // mark ported (pages stay in Studio)
                        $meta = images_all($id); $tag = $sid . '/' . part_dir_n($n);
                        foreach ($meta as &$m) $m['ported_to'] = $tag;
                        unset($m); images_save($id, $meta);
                        header('Location: port.php?p=' . urlencode($id) . '&done=' . urlencode($sid . ':' . $n . ':' . count($newpages))); exit;
                    }
                }
            }
        }
    }
}

// ---- render ----
$cms = cms_read();
$series = cms_valid($cms) ? $cms['series'] : [];
// build JS map: series id -> {title, nextN, parts:[n]}
$jsmap = [];
foreach ($series as $s) {
    $ns = array_map(fn($p)=>(int)($p['n']??0), $s['parts'] ?? []);
    $jsmap[$s['id']] = ['title'=>$s['title'] ?? $s['id'], 'next'=>($ns ? max($ns)+1 : 1), 'parts'=>array_values($ns)];
}
$E = fn($s)=>htmlspecialchars((string)$s, ENT_QUOTES, 'UTF-8');
?><!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark"><meta name="robots" content="noindex,nofollow">
<title>Port · <?= $E($proj['name']) ?></title><link rel="stylesheet" href="assets/studio.css"></head><body>
<header class="topbar"><div class="brand"><span class="dot"></span> Comic Studio</div>
  <a class="ghost" href="project.php?p=<?= $E(urlencode($id)) ?>">← <?= $E($proj['name']) ?></a><span class="spacer"></span>
  <span class="ghost"><?= $E(current_studio_user()) ?></span> <a class="ghost" href="login.php?do=logout">Log out</a></header>
<main class="wrap">
  <div class="pagehead"><h1>Port → comic</h1></div>
  <?php if (isset($_GET['done'])): [$ds,$dn,$dc] = array_pad(explode(':', (string)$_GET['done']), 3, ''); ?>
    <div class="flash">Ported <?= $E($dc) ?> page<?= $dc==='1'?'':'s' ?> into <strong><?= $E($ds) ?></strong> · Part <?= $E($dn) ?> (draft).
      <a href="https://3dmusclecomics.com/admin/series.php" target="_blank">Open in the CMS</a> to review &amp; publish.</div>
  <?php endif; ?>
  <?php if ($err): ?><div class="flash err"><?= $E($err) ?></div><?php endif; ?>

  <p class="muted"><?= count($pages) ?> page<?= count($pages)===1?'':'s' ?> ready to port (all images, in beat/page order). They’re copied as the part’s pages and stay here in Studio. New parts land as <strong>draft</strong>.</p>

  <?php if (!$pages): ?>
    <p class="muted">No images in this project yet — add some, then come back.</p>
  <?php elseif (!cms_valid($cms)): ?>
    <div class="flash err">Couldn’t read the catalog — porting disabled.</div>
  <?php else: ?>
  <form class="card form" method="post">
    <?= csrf_field() ?><input type="hidden" name="do" value="port"><input type="hidden" name="p" value="<?= $E($id) ?>">
    <label>Series
      <select name="series" id="ser">
        <?php foreach ($series as $s): ?><option value="<?= $E($s['id']) ?>"><?= $E($s['title'] ?? $s['id']) ?></option><?php endforeach; ?>
        <option value="__new__">➕ New series…</option>
      </select>
    </label>
    <label id="newwrap" hidden>New series name<input name="new_title" placeholder="e.g. Power Surge"></label>
    <label>Part
      <select name="part" id="prt"></select>
    </label>
    <div class="actions"><button class="btn primary">Port <?= count($pages) ?> page<?= count($pages)===1?'':'s' ?> →</button></div>
  </form>
  <script>
    var SER = <?= json_encode($jsmap, JSON_UNESCAPED_SLASHES) ?>;
    var ser = document.getElementById('ser'), prt = document.getElementById('prt'), nw = document.getElementById('newwrap');
    function fill() {
      var v = ser.value; prt.innerHTML = ''; nw.hidden = (v !== '__new__');
      var next = 1, parts = [];
      if (v !== '__new__' && SER[v]) { next = SER[v].next; parts = SER[v].parts; }
      var o = document.createElement('option'); o.value = '__new__'; o.textContent = 'New part (Part ' + next + ')'; prt.appendChild(o);
      parts.forEach(function (n) { var x = document.createElement('option'); x.value = n; x.textContent = 'Append to Part ' + n; prt.appendChild(x); });
    }
    ser.addEventListener('change', fill); fill();
  </script>
  <?php endif; ?>
</main></body></html>
