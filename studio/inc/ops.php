<?php
// Studio — Command Center shared constants + helpers (ops board, site registry).
// Deliberately a SEPARATE include so inc/boot.php (live, marker-protected — see
// DEPLOY-NOTES.md) never needs redeploying for Command Center work.
//
// Data files:
//   data/ops-tasks.json    {meta:{importedAt,source,importedCount}, tasks:[...]}
//   data/ops-updates.json  {taskId: [ {id,parent,src:'monday'|'studio',by,ts,text,likes,assets[]} ]}
//   data/cc-sites.json     {siteKey: {name,type,active,order,color,aliases[],links[],notes[]}}
// Tasks came from the one-time Monday.com Operations-board import (tools/monday-import.py);
// new tasks are created by ops-api.php. All writes go through s_with_lock().
declare(strict_types=1);
require_once __DIR__ . '/boot.php';

define('OPS_TASKS_FILE',   SDATA . '/ops-tasks.json');
define('OPS_UPDATES_FILE', SDATA . '/ops-updates.json');
define('CC_SITES_FILE',    SDATA . '/cc-sites.json');

const OPS_GROUPS     = ['todo'=>'To do', 'onhold'=>'On hold', 'done'=>'Done', 'cancelled'=>'Cancelled'];
const OPS_STATUSES   = ['notstarted'=>'Not started', 'working'=>'Working on it', 'confirm'=>'Needs confirm',
                        'onhold'=>'On hold', 'done'=>'Done', 'cancelled'=>'Cancelled'];
const OPS_PRIORITIES = [''=>'—', 'low'=>'Low', 'medium'=>'Medium', 'high'=>'High', 'critical'=>'Critical'];
const OPS_AI_TAGS    = [''=>'—', 'ai-now'=>'AI can do now', 'ai-assist'=>'AI-assisted', 'human-only'=>'Human only'];

function ops_load(): array {
    $d = s_read(OPS_TASKS_FILE, []);
    return ['meta' => $d['meta'] ?? [], 'tasks' => array_values($d['tasks'] ?? [])];
}
function ops_sites(): array {
    $s = s_read(CC_SITES_FILE, []);
    uasort($s, fn($a, $b) => ((int)($a['order'] ?? 99)) <=> ((int)($b['order'] ?? 99)));
    return $s;
}
// "open" = still needs doing: in a live group, not finished, not archived.
function ops_open(array $t): bool {
    return empty($t['archived'])
        && in_array((string)($t['group'] ?? ''), ['todo', 'onhold'], true)
        && !in_array((string)($t['status'] ?? ''), ['done', 'cancelled'], true);
}
