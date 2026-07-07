<?php
// ops-api.php — JSON verbs for the Command Center ops board (tasks, notes, site notes).
//
// Mirrors api.php's shape (jout / session gate / CSRF / action dispatch) but is a NEW file:
// api.php hard-gates on a project id before dispatch and ops tasks aren't projects, so
// extending it would mean restructuring the guard of a live multi-feature file (clobber
// risk per DEPLOY-NOTES.md). Every write here is a locked read-modify-write via
// s_with_lock(), so two browsers (owner + Magnamus) and a future AI batch runner can't
// clobber each other. Update threads live in data/ops-updates.json — a separate file from
// the tasks, so note-adds never contend on the same lock as status flips and the board
// page never ships ~½ MB of Monday history to the browser.
//
// Verbs: create · update · move · archive · bulk · note · updates · sitenote · sitelinks
declare(strict_types=1);
require_once __DIR__ . '/inc/ops.php';
s_boot();
header('Content-Type: application/json');
function jout($a) { echo json_encode($a); exit; }

if (!is_authed()) jout(['ok'=>false, 'error'=>'Not signed in.']);
if (!csrf_ok())   jout(['ok'=>false, 'error'=>'Bad token — reload.']);

$action = (string)($_POST['action'] ?? '');
$id     = preg_replace('/[^a-z0-9]/', '', (string)($_POST['id'] ?? ''));

// whitelist-sanitize a client patch into safe task fields (shared by update + bulk)
function ops_clean_patch(array $in): array {
    $out = [];
    if (array_key_exists('title', $in)) { $t = mb_substr(trim((string)$in['title']), 0, 300); if ($t !== '') $out['title'] = $t; }
    if (array_key_exists('body', $in))   $out['body']   = mb_substr(trim((string)$in['body']), 0, 8000);
    if (array_key_exists('aiPlan', $in)) $out['aiPlan'] = mb_substr(trim((string)$in['aiPlan']), 0, 4000);
    if (array_key_exists('batch', $in))  $out['batch']  = mb_substr(trim((string)$in['batch']), 0, 60);
    if (array_key_exists('status', $in)   && isset(OPS_STATUSES[(string)$in['status']]))                    $out['status']   = (string)$in['status'];
    if (array_key_exists('group', $in)    && isset(OPS_GROUPS[(string)$in['group']]))                       $out['group']    = (string)$in['group'];
    if (array_key_exists('priority', $in) && array_key_exists((string)$in['priority'], OPS_PRIORITIES))     $out['priority'] = (string)$in['priority'];
    if (array_key_exists('aiTag', $in)    && array_key_exists((string)$in['aiTag'], OPS_AI_TAGS))           $out['aiTag']    = (string)$in['aiTag'];
    if (array_key_exists('revenueImpact', $in)) $out['revenueImpact'] = max(0, min(5, (int)$in['revenueImpact']));
    if (array_key_exists('person', $in) && is_array($in['person']))
        $out['person'] = array_values(array_filter(array_map(fn($p) => mb_substr(trim((string)$p), 0, 60), $in['person']), 'strlen'));
    if (array_key_exists('sites', $in) && is_array($in['sites'])) {
        $reg = ops_sites();
        $out['sites'] = array_values(array_unique(array_filter(array_map('strval', $in['sites']), fn($s) => isset($reg[$s]))));
    }
    if (array_key_exists('checklist', $in) && is_array($in['checklist'])) {
        $cl = [];
        foreach ($in['checklist'] as $c) {
            if (!is_array($c)) continue;
            $txt = mb_substr(trim((string)($c['text'] ?? '')), 0, 300);
            if ($txt === '') continue;
            $item = ['text'=>$txt, 'done'=>!empty($c['done'])];
            if (!empty($c['mondayId'])) $item['mondayId'] = (string)$c['mondayId'];
            $cl[] = $item;
        }
        $out['checklist'] = $cl;
    }
    return $out;
}

// apply a clean patch + bookkeeping: entering done stamps completedOn, leaving clears it
function ops_apply(array $t, array $patch): array {
    $wasDone = ($t['status'] ?? '') === 'done';
    foreach ($patch as $k => $v) $t[$k] = $v;
    $isDone = ($t['status'] ?? '') === 'done';
    if ($isDone && !$wasDone)  $t['completedOn'] = date('c');
    if (!$isDone && $wasDone)  $t['completedOn'] = '';
    $t['updated'] = date('c');
    return $t;
}

if ($action === 'create') {
    $title = mb_substr(trim((string)($_POST['title'] ?? '')), 0, 300);
    if ($title === '') jout(['ok'=>false, 'error'=>'Empty title.']);
    $group = isset(OPS_GROUPS[(string)($_POST['group'] ?? '')]) ? (string)$_POST['group'] : 'todo';
    $reg   = ops_sites();
    $sites = json_decode((string)($_POST['sites'] ?? '[]'), true);
    $sites = is_array($sites) ? array_values(array_unique(array_filter(array_map('strval', $sites), fn($s) => isset($reg[$s])))) : [];
    $task = [
        'id'=>nid(), 'mondayId'=>'', 'title'=>$title, 'body'=>'', 'checklist'=>[],
        'group'=>$group, 'status'=>'notstarted', 'mondayStatus'=>'',
        'person'=>[], 'sites'=>$sites, 'priority'=>'', 'revenueImpact'=>0,
        'aiTag'=>'', 'aiPlan'=>'', 'batch'=>'',
        'createdBy'=>current_studio_user(), 'created'=>date('c'), 'updated'=>date('c'),
        'completedOn'=>'', 'creationLog'=>'', 'archived'=>false, 'sort'=>0,
    ];
    $task = s_with_lock(OPS_TASKS_FILE, function ($d) use ($task) {
        $d['tasks'] = $d['tasks'] ?? [];
        $min = 0;
        foreach ($d['tasks'] as $t) if (($t['group'] ?? '') === $task['group']) $min = min($min, (int)($t['sort'] ?? 0));
        $task['sort'] = $min - 1;                       // new tasks land at the top of their group
        array_unshift($d['tasks'], $task);
        return ['data'=>$d, 'result'=>$task];
    });
    jout(['ok'=>true, 'task'=>$task]);
}

if ($action === 'update') {
    $patch = ops_clean_patch(json_decode((string)($_POST['patch'] ?? '{}'), true) ?: []);
    if (!$patch) jout(['ok'=>false, 'error'=>'Nothing to update.']);
    $res = s_with_lock(OPS_TASKS_FILE, function ($d) use ($id, $patch) {
        foreach (($d['tasks'] ?? []) as $k => $t) {
            if (($t['id'] ?? '') !== $id) continue;
            $d['tasks'][$k] = ops_apply($t, $patch);
            return ['data'=>$d, 'result'=>$d['tasks'][$k]];
        }
        return ['result'=>null];
    });
    $res ? jout(['ok'=>true, 'task'=>$res]) : jout(['ok'=>false, 'error'=>'Task not found.']);
}

// move a task into $group at 1-based position $pos; resequences that group's sort values
if ($action === 'move') {
    $group = (string)($_POST['group'] ?? '');
    $pos   = (int)($_POST['pos'] ?? 1);
    if (!isset(OPS_GROUPS[$group])) jout(['ok'=>false, 'error'=>'Unknown group.']);
    $res = s_with_lock(OPS_TASKS_FILE, function ($d) use ($id, $group, $pos) {
        $tasks = $d['tasks'] ?? [];
        $me = null;
        foreach ($tasks as $k => $t) if (($t['id'] ?? '') === $id) { $me = $k; break; }
        if ($me === null) return ['result'=>null];
        $tasks[$me]['group'] = $group;
        $tasks[$me]['updated'] = date('c');
        $members = [];                                   // group order = current sort
        foreach ($tasks as $k => $t) if (($t['group'] ?? '') === $group && $k !== $me) $members[] = $k;
        usort($members, fn($a, $b) => ((int)($tasks[$a]['sort'] ?? 0)) <=> ((int)($tasks[$b]['sort'] ?? 0)));
        $pos = max(1, min(count($members) + 1, $pos)) - 1;
        array_splice($members, $pos, 0, [$me]);
        foreach ($members as $i => $k) $tasks[$k]['sort'] = $i;
        $d['tasks'] = $tasks;
        return ['data'=>$d, 'result'=>$tasks[$me]];
    });
    $res ? jout(['ok'=>true, 'task'=>$res]) : jout(['ok'=>false, 'error'=>'Task not found.']);
}

if ($action === 'archive') {
    $on = !empty($_POST['on']) && $_POST['on'] !== '0';
    $res = s_with_lock(OPS_TASKS_FILE, function ($d) use ($id, $on) {
        foreach (($d['tasks'] ?? []) as $k => $t) {
            if (($t['id'] ?? '') !== $id) continue;
            $d['tasks'][$k]['archived'] = $on;
            $d['tasks'][$k]['updated']  = date('c');
            return ['data'=>$d, 'result'=>true];
        }
        return ['result'=>false];
    });
    $res ? jout(['ok'=>true]) : jout(['ok'=>false, 'error'=>'Task not found.']);
}

// one locked pass over many tasks — the AI-triage writer and the board's bulk bar
if ($action === 'bulk') {
    $ids = json_decode((string)($_POST['ids'] ?? '[]'), true);
    $ids = is_array($ids) ? array_flip(array_map('strval', $ids)) : [];
    $patch = ops_clean_patch(json_decode((string)($_POST['patch'] ?? '{}'), true) ?: []);
    if (!$ids || !$patch) jout(['ok'=>false, 'error'=>'Need ids + patch.']);
    $n = s_with_lock(OPS_TASKS_FILE, function ($d) use ($ids, $patch) {
        $n = 0;
        foreach (($d['tasks'] ?? []) as $k => $t) {
            if (!isset($ids[(string)($t['id'] ?? '')])) continue;
            $d['tasks'][$k] = ops_apply($t, $patch);
            $n++;
        }
        return ['data'=>$d, 'result'=>$n];
    });
    jout(['ok'=>true, 'updated'=>$n]);
}

if ($action === 'note') {
    $txt = trim((string)($_POST['text'] ?? ''));
    if ($txt === '') jout(['ok'=>false, 'error'=>'Empty note.']);
    $known = false;
    foreach (ops_load()['tasks'] as $t) if (($t['id'] ?? '') === $id) { $known = true; break; }
    if (!$known) jout(['ok'=>false, 'error'=>'Task not found.']);
    $note = ['id'=>nid(), 'parent'=>'', 'src'=>'studio', 'by'=>current_studio_user(),
             'ts'=>date('c'), 'text'=>mb_substr($txt, 0, 4000), 'likes'=>0, 'assets'=>[]];
    s_with_lock(OPS_UPDATES_FILE, function ($u) use ($id, $note) {
        $u[$id] = $u[$id] ?? [];
        $u[$id][] = $note;                               // threads read oldest → newest
        return ['data'=>$u, 'result'=>true];
    });
    jout(['ok'=>true, 'note'=>$note]);
}

if ($action === 'updates') {
    $u = s_read(OPS_UPDATES_FILE, []);
    jout(['ok'=>true, 'updates'=>array_values($u[$id] ?? [])]);
}

if ($action === 'sitenote') {
    $site = (string)($_POST['site'] ?? '');
    $txt  = trim((string)($_POST['text'] ?? ''));
    if ($txt === '') jout(['ok'=>false, 'error'=>'Empty note.']);
    $note = ['ts'=>date('c'), 'by'=>current_studio_user(), 'text'=>mb_substr($txt, 0, 4000)];
    $res = s_with_lock(CC_SITES_FILE, function ($s) use ($site, $note) {
        if (!isset($s[$site])) return ['result'=>false];
        $s[$site]['notes'] = $s[$site]['notes'] ?? [];
        array_unshift($s[$site]['notes'], $note);        // newest first, feedback-log style
        return ['data'=>$s, 'result'=>true];
    });
    $res ? jout(['ok'=>true, 'note'=>$note]) : jout(['ok'=>false, 'error'=>'Unknown site.']);
}

// replace a site's quick-links (label+url rows, edited from site.php)
if ($action === 'sitelinks') {
    $site  = (string)($_POST['site'] ?? '');
    $links = json_decode((string)($_POST['links'] ?? '[]'), true);
    if (!is_array($links)) jout(['ok'=>false, 'error'=>'Bad links.']);
    $clean = [];
    foreach ($links as $l) {
        if (!is_array($l)) continue;
        $label = mb_substr(trim((string)($l['label'] ?? '')), 0, 60);
        $url   = trim((string)($l['url'] ?? ''));
        if ($url !== '' && !preg_match('#^https?://#i', $url)) continue;
        if ($label === '') continue;
        $clean[] = ['label'=>$label, 'url'=>$url];
    }
    $res = s_with_lock(CC_SITES_FILE, function ($s) use ($site, $clean) {
        if (!isset($s[$site])) return ['result'=>false];
        $s[$site]['links'] = $clean;
        return ['data'=>$s, 'result'=>true];
    });
    $res ? jout(['ok'=>true, 'links'=>$clean]) : jout(['ok'=>false, 'error'=>'Unknown site.']);
}

jout(['ok'=>false, 'error'=>'Unknown action.']);
