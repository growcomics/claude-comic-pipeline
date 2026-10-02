<?php
declare(strict_types=1);
require_once __DIR__ . '/inc/boot.php';
s_boot();
header('Content-Type: application/json');
function jout($a){ echo json_encode($a); exit; }

if (!is_authed()) jout(['ok'=>false,'error'=>'Not signed in.']);
if (!csrf_ok())   jout(['ok'=>false,'error'=>'Bad token — reload.']);

$id = preg_replace('/[^a-z0-9-]/','',(string)($_POST['p'] ?? ''));
if (!project_get($id)) jout(['ok'=>false,'error'=>'Unknown project.']);
$action = $_POST['action'] ?? '';

// Every write below is a LOCKED read-modify-write (2026-10-01): the lieutenant workspace (ws-api.php,
// picker.php) and the worker write the same images-<id>.json / projects.json under s_with_lock(), so
// a write here re-reads the file INSIDE the lock instead of saving a copy read earlier in the request.
// Slow work (store_image, hashing) runs before the lock. Locks are never nested: images first, then
// projects, one after the other.
// $fn(&$p) edits project $id's row in projects.json.
function api_project_patch(string $id, callable $fn): void {
    s_with_lock(PROJECTS_FILE, function ($all) use ($id, $fn) {
        $hit = false;
        foreach ($all as &$p) if (($p['id']??'')===$id) { $fn($p); $hit = true; }
        unset($p);
        return $hit ? ['data'=>$all, 'result'=>true] : ['result'=>false];
    });
}
function touch_project(string $id): void { api_project_patch($id, function (&$p) { $p['updated']=date('c'); }); }
// Clear the project's cover if it no longer names an image of the project (read fresh, in the lock).
function api_cover_check(string $id, bool $touch): void {
    api_project_patch($id, function (&$p) use ($id, $touch) {
        $cov = (string)($p['cover'] ?? '');
        if ($cov !== '' && !in_array($cov, array_column(images_all($id), 'file'), true)) $p['cover'] = null;
        if ($touch) $p['updated'] = date('c');
    });
}
// $fn(&$meta, $idx) edits the image named $file and returns the JSON reply; null = the image is gone.
function api_image_edit(string $id, string $file, callable $fn): ?array {
    return s_with_lock(imeta_path($id), function ($meta) use ($file, $fn) {
        $idx = null; foreach ($meta as $k=>$m) if (($m['file']??'')===$file) { $idx=$k; break; }
        if ($idx === null) return ['result'=>null];
        $res = $fn($meta, $idx);
        return ['data'=>$meta, 'result'=>$res];
    });
}
function beat_num(string $s): int { return preg_match('/(\d+)/',$s,$m) ? (int)$m[1] : 9999; }
function ordered_beats(array $meta): array {
    $b = [];
    foreach ($meta as $m) { $g = $m['group'] ?? ''; if ($g!=='' && !in_array($g,$b,true)) $b[]=$g; }
    usort($b, fn($x,$y)=> beat_num($x) <=> beat_num($y) ?: strcmp($x,$y));
    return $b;
}

if ($action === 'upload') {
    $files = $_FILES['files'] ?? null;
    if (!$files || empty($files['name'])) jout(['ok'=>false,'error'=>'No files.']);
    $added = [];
    $names = (array)$files['name'];
    for ($i=0; $i<count($names); $i++) {
        if ((int)($files['error'][$i] ?? 4) !== UPLOAD_ERR_OK) continue;
        if (!is_uploaded_file($files['tmp_name'][$i])) continue;
        if ((int)($files['size'][$i] ?? 0) > MAX_BYTES) continue;
        $res = store_image($files['tmp_name'][$i], (string)$files['name'][$i], $id);
        if (!$res) continue;
        $entry = ['file'=>$res['file'],'orig'=>mb_substr((string)$files['name'][$i],0,120),
                  'rating'=>'unrated','accepted'=>false,'group'=>'','tags'=>[],'ts'=>time()];
        $added[] = $entry;
    }
    $meta = images_update($id, function ($meta) use ($added) { return array_merge($meta, $added); });
    touch_project($id);
    jout(['ok'=>true,'added'=>$added,'count'=>count($meta)]);
}

// reorder a beat to a 1-based position; renumbers all beats to "Beat 1..N" in the new order
if ($action === 'move_beat') {
    $beat = trim((string)($_POST['beat'] ?? ''));
    $to   = (int)($_POST['to'] ?? 0);
    $ok = s_with_lock(imeta_path($id), function ($meta) use ($beat, $to) {
        $beats = ordered_beats($meta);
        $from = array_search($beat, $beats, true);
        if ($from === false || !$beats) return ['result'=>false];
        $to = max(1, min(count($beats), $to)) - 1;
        array_splice($beats, $from, 1);
        array_splice($beats, $to, 0, [$beat]);
        $map = []; foreach ($beats as $i=>$b) $map[$b] = 'Beat ' . ($i+1);
        foreach ($meta as &$m) { $g = $m['group'] ?? ''; if (isset($map[$g])) $m['group'] = $map[$g]; }
        unset($m);
        return ['data'=>$meta, 'result'=>true];
    });
    if (!$ok) jout(['ok'=>false,'error'=>'no such beat']);
    touch_project($id);
    jout(['ok'=>true]);
}

// sequence mode: each image becomes its own beat (page), in current order, all kept
if ($action === 'one_beat_each') {
    images_update($id, function ($meta) {
        usort($meta, fn($a,$b)=> beat_num($a['group']??'') <=> beat_num($b['group']??'') ?: (($a['ts']??0) <=> ($b['ts']??0)));
        foreach ($meta as $i=>&$m) { $m['group'] = 'Beat ' . ($i+1); $m['accepted'] = true; $m['rating'] = 'good'; }
        unset($m);
        return $meta;
    });
    touch_project($id);
    jout(['ok'=>true]);
}

// purge: hard-delete every image that is NOT rated good (▲) and NOT kept (★)
if ($action === 'purge') {
    $del = [];
    $keep = images_update($id, function ($meta) use (&$del) {
        $keep = []; $del = [];
        foreach ($meta as $m) { if (($m['rating'] ?? '') === 'good' || !empty($m['accepted'])) $keep[] = $m; else $del[] = $m; }
        return $keep;
    });
    foreach ($del as $m) { @unlink(project_dir($id) . '/' . $m['file']); @unlink(project_dir($id) . '/thumb/' . $m['file']); }
    api_cover_check($id, true);
    jout(['ok' => true, 'deleted' => count($del), 'kept' => count($keep)]);
}

// group_similar: images that carry a Flow generation key (identical prompt = same beat)
// group EXACTLY by that key; anything without one falls back to visual difference-hash.
if ($action === 'group_similar') {
    $hasGD = function_exists('imagecreatefromstring');
    $meta = images_all($id);
    if (count($meta) < 2) jout(['ok'=>true,'beats'=>count($meta)]);
    $dhash = function (string $path) {                      // 64-bit difference hash from a thumbnail
        $data = @file_get_contents($path); if ($data === false) return null;
        $im = @imagecreatefromstring($data); if (!$im) return null;
        $W = 9; $H = 8; $sm = imagecreatetruecolor($W, $H);
        imagecopyresampled($sm, $im, 0,0,0,0, $W,$H, imagesx($im), imagesy($im));
        $bits = [];
        for ($y = 0; $y < $H; $y++) {
            $prev = null;
            for ($x = 0; $x < $W; $x++) {
                $c = imagecolorat($sm, $x, $y);
                $l = (int)(0.299*(($c>>16)&0xFF) + 0.587*(($c>>8)&0xFF) + 0.114*($c&0xFF));
                if ($prev !== null) $bits[] = ($l > $prev) ? 1 : 0;
                $prev = $l;
            }
        }
        imagedestroy($sm); imagedestroy($im);
        return $bits;
    };
    $ham = function (array $a, array $b) { $d = 0; $n = min(count($a), count($b)); for ($i=0;$i<$n;$i++) if ($a[$i] !== $b[$i]) $d++; return $d + abs(count($a) - count($b)); };
    $rows = [];
    foreach ($meta as $k => $m) {
        $key = trim((string)($m['genkey'] ?? ''));
        $h = null;
        if ($key === '' && $hasGD) {                        // only hash images that need the visual fallback
            $tp = project_dir($id) . '/thumb/' . $m['file'];
            if (!is_file($tp)) $tp = project_dir($id) . '/' . $m['file'];
            $h = $dhash($tp);
        }
        $rows[] = ['k'=>$k, 'key'=>$key, 'h'=>$h, 'ts'=>(int)($m['ts'] ?? 0)];
    }
    usort($rows, fn($a,$b) => $a['ts'] <=> $b['ts']);       // beat numbering follows import order
    $THRESH = 12;                                            // /64 bits — variants of one prompt cluster well below this
    $clusters = [];                                          // each: ['key'=>str|null, 'rep'=>bits|null, 'members'=>[]]
    $byKey = [];                                             // genkey => cluster index
    foreach ($rows as $r) {
        if ($r['key'] !== '') {                              // exact group by Flow generation/prompt
            if (!isset($byKey[$r['key']])) { $clusters[] = ['key'=>$r['key'], 'rep'=>null, 'members'=>[]]; $byKey[$r['key']] = count($clusters) - 1; }
            $clusters[$byKey[$r['key']]]['members'][] = $r['k'];
            continue;
        }
        if ($r['h'] === null) { $clusters[] = ['key'=>null, 'rep'=>null, 'members'=>[$r['k']]]; continue; }
        $bi = -1; $bd = $THRESH + 1;
        foreach ($clusters as $i => $c) {
            if ($c['key'] !== null || $c['rep'] === null) continue;
            $d = $ham($r['h'], $c['rep']);
            if ($d < $bd) { $bd = $d; $bi = $i; }
        }
        if ($bi >= 0 && $bd <= $THRESH) $clusters[$bi]['members'][] = $r['k'];
        else $clusters[] = ['key'=>null, 'rep'=>$r['h'], 'members'=>[$r['k']]];
    }
    // the hashing above ran on a snapshot; apply the beats by FILE inside the lock, so an image that
    // landed meanwhile keeps its own group instead of being overwritten from a stale copy
    $groupOf = []; $n = 1;
    foreach ($clusters as $c) { $g = 'Beat ' . $n++; foreach ($c['members'] as $k) $groupOf[(string)($meta[$k]['file'] ?? '')] = $g; }
    unset($groupOf['']);
    images_update($id, function ($meta) use ($groupOf) {
        foreach ($meta as &$m) { $f = (string)($m['file'] ?? ''); if (isset($groupOf[$f])) $m['group'] = $groupOf[$f]; }
        unset($m); return $meta;
    });
    touch_project($id);
    jout(['ok'=>true,'beats'=>count($clusters),'by_prompt'=>count($byKey)]);
}

// bulk mutate a set of files in one request (review surface: approve-visible / delete-rejects)
if ($action === 'bulk') {
    $files = json_decode((string)($_POST['files'] ?? '[]'), true) ?: [];
    $op    = (string)($_POST['op'] ?? '');
    $set   = array_flip(array_map('basename', (array)$files));
    if ($op === 'delete') {
        $gone = [];
        $keep = images_update($id, function ($meta) use ($set, &$gone) {
            $keep = []; $gone = [];
            foreach ($meta as $m) { if (isset($set[$m['file'] ?? ''])) $gone[] = $m['file']; else $keep[] = $m; }
            return $keep;
        });
        foreach ($gone as $f) { @unlink(project_dir($id) . '/' . $f); @unlink(project_dir($id) . '/thumb/' . $f); }
        api_cover_check($id, true);
        jout(['ok' => true, 'deleted' => count($gone), 'count' => count($keep)]);
    }
    $n = 0;
    images_update($id, function ($meta) use ($set, $op, &$n) {
        $n = 0;
        foreach ($meta as &$m) {
            if (!isset($set[$m['file'] ?? ''])) continue;
            if      ($op === 'approve')   { $m['rating'] = 'good'; $m['accepted'] = true; }
            elseif  ($op === 'unapprove') { $m['accepted'] = false; if (($m['rating'] ?? '') === 'good') $m['rating'] = 'unrated'; }
            elseif  ($op === 'bad')       { $m['rating'] = 'bad';  $m['accepted'] = false; }
            elseif  ($op === 'keep')      { $m['accepted'] = true; }
            else continue;
            $n++;
        }
        unset($m); return $meta;
    });
    touch_project($id);
    jout(['ok' => true, 'updated' => $n]);
}

// per-image mutations — each re-finds the image inside the lock (api_image_edit)
$file = basename((string)($_POST['file'] ?? ''));
$gone = ['ok'=>false,'error'=>'Image not found.'];
if (!in_array($file, array_column(images_all($id), 'file'), true)) jout($gone);

// mark current image the winner of its beat: it becomes accepted+good, siblings lose accept + any 'good'
if ($action === 'winner') {
    $res = api_image_edit($id, $file, function (array &$meta, $idx) use ($file) {
        $beat = $meta[$idx]['group'] ?? '';
        foreach ($meta as &$m) {
            if ($beat !== '' && ($m['group'] ?? '') === $beat) {
                $win = (($m['file'] ?? '') === $file);
                $m['accepted'] = $win;
                if ($win) $m['rating'] = 'good';
                elseif (($m['rating'] ?? '') === 'good') $m['rating'] = 'unrated';
            }
        }
        unset($m); return ['ok'=>true];
    });
    if ($res === null) jout($gone);
    api_project_patch($id, function (&$p) use ($file) { if (empty($p['cover'])) $p['cover']=$file; });
    jout($res);
}
if ($action === 'rate') {
    $r = in_array($_POST['rating']??'', RATINGS, true) ? $_POST['rating'] : 'unrated';
    jout(api_image_edit($id, $file, function (array &$meta, $idx) use ($r) { $meta[$idx]['rating'] = $r; return ['ok'=>true,'rating'=>$r]; }) ?? $gone);
}
if ($action === 'keep') {
    $acc = !empty($_POST['accepted']) && $_POST['accepted'] !== '0';
    jout(api_image_edit($id, $file, function (array &$meta, $idx) use ($acc) { $meta[$idx]['accepted'] = $acc; return ['ok'=>true,'accepted'=>$acc]; }) ?? $gone);
}
if ($action === 'group') {
    $g = mb_substr(trim((string)($_POST['group'] ?? '')),0,60);
    jout(api_image_edit($id, $file, function (array &$meta, $idx) use ($g) { $meta[$idx]['group'] = $g; return ['ok'=>true]; }) ?? $gone);
}
if ($action === 'cover') {
    api_project_patch($id, function (&$p) use ($file) { $p['cover']=$file; });
    jout(['ok'=>true]);
}
if ($action === 'delete') {
    $res = api_image_edit($id, $file, function (array &$meta, $idx) { array_splice($meta, $idx, 1); return ['ok'=>true,'count'=>count($meta)]; });
    if ($res === null) jout($gone);
    @unlink(project_dir($id) . '/' . $file);
    @unlink(project_dir($id) . '/thumb/' . $file);
    api_project_patch($id, function (&$p) use ($file) { if (($p['cover']??'')===$file) $p['cover']=null; });
    jout($res);
}
jout(['ok'=>false,'error'=>'Unknown action.']);
