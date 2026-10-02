<?php
// ws-api.php: JSON API behind the lieutenant workspace page (ws.php). See docs/LIEUTENANT-WORKSPACE.md.
//
// Always answers JSON. Unauthenticated -> 401 {ok:false,error:'Sign in'}. Every action that names a
// comic (p) is checked with ws_can_see() + project_get(). GET actions are read-only (state, ping,
// chat); every other action is POST-only and needs the CSRF token (X-CSRF header or csrf field).
// There is deliberately NO publish / post / port / delete-image / key action here: lieutenants can
// never reach those, and owner/staff keep using the existing studio pages for them.
//
// Local helpers are prefixed ws_api_ (shared helpers live in inc/workspace.php).
declare(strict_types=1);
require_once __DIR__ . '/inc/boot.php';

header('X-Robots-Tag: noindex');
header('X-Content-Type-Options: nosniff');

const WS_API_ASPECTS   = ['3:4', '2:3', '9:16', '1:1', '4:3', '16:9'];
const WS_API_GET       = ['state', 'ping', 'chat'];
const WS_API_POST      = ['create', 'setproj', 'page_save', 'page_delete', 'upload', 'ref_update', 'ref_remove',
                          'generate', 'cancel', 'ready', 'chat_send', 'action'];
const WS_API_MAX_PAGES = 200;
const WS_API_MAX_REFS  = 200;
const WS_API_MAX_FILES = 20;
const WS_API_CHAT_MAX_BODY  = 16384;   // bytes: a chat_send request body above this is refused (413)
const WS_API_TEAM_PER_MIN   = 20;      // thread posts per lieutenant per rolling minute
const WS_API_TEAM_PER_DAY   = 400;     // thread posts per lieutenant per (Pacific) day
const WS_API_CHAT_MAX_TOKENS = 4000;   // Claude reply cap (also sizes the up-front cost reservation)

// ---- input helpers -------------------------------------------------------------------
// Clean user/model text: valid UTF-8 only (an invalid byte would make json_encode fail and s_write
// would then blank the store), no control chars, normalised newlines, trimmed, capped.
function ws_api_text($v, int $max, bool $multiline = true): string {
    if (!is_string($v) && !is_int($v) && !is_float($v)) return '';
    $s = mb_scrub((string)$v, 'UTF-8');
    $s = str_replace(["\r\n", "\r"], "\n", $s);
    if (!$multiline) $s = str_replace(["\n", "\t"], ' ', $s);
    $s = (string)preg_replace('/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/u', '', $s);
    return mb_substr(trim($s), 0, $max);
}
function ws_api_int($v): int {
    if (is_int($v)) return $v;
    if (is_float($v)) return (int)$v;
    if (is_string($v) && preg_match('/^\s*-?\d{1,9}\s*$/', $v)) return (int)trim($v);
    return 0;
}
// A project file name: basename only, safe charset, else ''.
function ws_api_file($v): string {
    if (!is_string($v)) return '';
    $f = basename($v);
    return ($f !== '' && preg_match('/^[A-Za-z0-9._-]+$/', $f) && $f[0] !== '.') ? $f : '';
}
// An uploaded file's original name, made safe to store (it lands in images-<pid>.json).
function ws_api_fname($v): string {
    $s = ws_api_text(is_string($v) ? basename(str_replace('\\', '/', $v)) : '', 120, false);
    return $s !== '' ? $s : 'upload';
}
function ws_api_fail(string $error, int $code = 400, array $extra = []): void {
    ws_json_out(array_merge(['ok' => false, 'error' => $error], $extra), $code);
}
// The comic this request is about. Must be clean, visible to the caller and exist.
function ws_api_pid(): string {
    $g = $_GET['p'] ?? ''; $q = $_POST['p'] ?? '';
    $g = is_string($g) ? $g : ''; $q = is_string($q) ? $q : '';
    if ($g !== '' && $q !== '' && $g !== $q) ws_api_fail('Mismatched comic id.');
    $raw = $g !== '' ? $g : $q;
    if ($raw === '') ws_api_fail('Missing comic id.');
    $pid = ws_pid($raw);
    if ($pid === '' || $pid !== $raw) ws_api_fail('Bad comic id.');
    if (!ws_can_see($pid) || project_get($pid) === null) ws_api_fail('That comic is not in your workspace.', 403);
    return $pid;
}
function ws_api_sys(string $text): array { return ['role' => 'system', 'uid' => '', 'by' => 'Studio', 'text' => $text]; }

// ---- page numbers ---------------------------------------------------------------------------
// The next page number never handed out in this comic. proj['nextN'] only counts up, so a deleted
// page's number (and its group "Page NN") is never given to a new page.
function ws_api_next_n(array $d): int {
    $max = 0; foreach ($d['pages'] as $pg) $max = max($max, (int)($pg['n'] ?? 0));
    return max((int)($d['nextN'] ?? 0), $max + 1);
}
// ws_proj_update() that also keeps proj['nextN'] (initialised from the pages when absent). Taken
// before AND after $fn, so deleting the highest page still leaves its number used up.
function ws_api_proj_update(string $pid, callable $fn): array {
    return ws_proj_update($pid, function ($d) use ($fn) {
        $before = ws_api_next_n($d);
        $d = ws_proj_norm($fn($d));
        $d['nextN'] = max($before, ws_api_next_n($d));
        return $d;
    });
}
function ws_api_reused_n(int $n): string { return "Page $n was deleted, and page numbers are never reused. Add a new page instead."; }

// Thread flood guard for a lieutenant: WS_API_TEAM_PER_MIN posts per rolling minute and
// WS_API_TEAM_PER_DAY per day, counted in usage.json users[uid] (tmin = timestamps of the last
// minute, tmsgs = today's posts). Returns '' when the post may go ahead (and counts it), else the error.
function ws_api_team_rate(string $uid): string {
    $now = time();
    return (string)ws_usage_mutate(function ($d) use ($uid, $now) {
        $u = (array)($d['users'][$uid] ?? []);
        $win = array_values(array_filter(array_map('intval', (array)($u['tmin'] ?? [])), fn($t) => $t > $now - 60 && $t <= $now));
        $day = (int)($u['tmsgs'] ?? 0);
        if ($day >= WS_API_TEAM_PER_DAY) return [$d, 'You have posted ' . WS_API_TEAM_PER_DAY . ' messages today, which is the daily limit. It resets at midnight Pacific.'];
        if (count($win) >= WS_API_TEAM_PER_MIN) return [$d, 'You are sending messages very fast. Wait a minute, then try again.'];
        $win[] = $now;
        $u['tmin'] = $win; $u['tmsgs'] = $day + 1;
        $d['users'][$uid] = $u;
        return [$d, ''];
    });
}

// ---- read models --------------------------------------------------------------------------
// One pass over images-<pid>.json: takes / picks / newest thumbs per workspace page.
function ws_api_pages(string $pid, array $proj): array {
    $picks = ws_picks($pid)['pages'];
    $by = [];
    foreach (images_all($pid) as $m) {
        if (!is_array($m) || !empty($m['isref'])) continue;
        $g = (string)($m['group'] ?? ''); $f = (string)($m['file'] ?? '');
        if ($g === '' || $f === '') continue;
        $by[$g][] = [$f, (int)($m['ts'] ?? 0)];
    }
    $out = [];
    foreach ($proj['pages'] as $pg) {
        $n = (int)($pg['n'] ?? 0); $g = ws_page_group($n);
        $list = $by[$g] ?? [];
        usort($list, fn($a, $b) => $b[1] <=> $a[1]);
        $pk = is_array($picks[$g] ?? null) ? $picks[$g] : [];
        $pick = $pk['pick'] ?? [];
        $pickFiles = [];
        if (is_array($pick)) foreach ($pick as $f) { $f = is_string($f) ? ws_api_file($f) : ''; if ($f !== '') $pickFiles[] = $f; }
        $refs = [];
        foreach ((array)($pg['refs'] ?? []) as $f) { $f = ws_api_file($f); if ($f !== '') $refs[] = $f; }
        $out[] = [
            'n' => $n, 'title' => (string)($pg['title'] ?? ''), 'prompt' => (string)($pg['prompt'] ?? ''),
            'refs' => $refs, 'group' => $g, 'takes' => count($list), 'picked' => count($pickFiles),
            'dropped' => $pick === 'drop', 'pickFiles' => $pickFiles,
            'comment' => is_string($pk['c'] ?? null) ? (string)$pk['c'] : '',
            'thumbs' => array_map(fn($x) => $x[0], array_slice($list, 0, 4)),
            'lastTs' => $list ? $list[0][1] : 0,
        ];
    }
    return $out;
}
function ws_api_refs(string $pid, array $proj): array {
    $out = [];
    foreach ($proj['refs'] as $r) {
        $f = ws_api_file($r['file'] ?? '');
        if ($f === '' || !ws_image_exists($pid, $f)) continue;
        $out[] = ['file' => $f, 'label' => (string)($r['label'] ?? ''), 'kind' => (string)($r['kind'] ?? 'ref')];
    }
    return $out;
}
// Job rows trimmed to what the page shows (never the worker's internals).
function ws_api_jobs(string $pid, string $uid, bool $isLt, int $limit = 20): array {
    $out = [];
    foreach (ws_jobs_for($pid, $limit) as $j) {
        if (!is_array($j)) continue;
        $st = (string)($j['status'] ?? ''); $mine = (string)($j['uid'] ?? '') === $uid;
        $stop = !empty($j['stopRequested']);
        $out[] = [
            'id' => (string)($j['id'] ?? ''), 'page' => (int)($j['page'] ?? 0), 'takes' => (int)($j['takes'] ?? 0),
            'done' => (int)($j['done'] ?? 0), 'failed' => (int)($j['failed'] ?? 0), 'status' => $st,
            'by' => (string)($j['by'] ?? ''), 'mine' => $mine, 'stopRequested' => $stop,
            'canCancel' => in_array($st, ['queued', 'running'], true) && !$stop && (!$isLt || $mine),
            'note' => mb_substr((string)($j['note'] ?? ''), 0, 200),
            'ts' => (int)strtotime((string)($j['createdAt'] ?? '')),
            'fts' => (int)strtotime((string)($j['finishedAt'] ?? '')),
        ];
    }
    return $out;
}
// Cheap change signatures: mtime+size of every store the page shows. 'sig' covers all of them
// (the spec'd value); 'chat' and 'rest' let the page refetch only the part that changed.
// Jobs: a digest of THIS comic's jobs only (the global jobs.json stamp moves on every worker
// heartbeat for any comic, which made every open page reload its state).
function ws_api_sigs(string $pid): array {
    clearstatcache();
    $st = function (string $f): string { return is_file($f) ? (filemtime($f) . ':' . filesize($f)) : '-'; };
    $chat = $st(ws_file('chat', $pid));
    $jobs = [];
    foreach (ws_jobs_for($pid) as $j) {
        if (is_array($j)) $jobs[] = [(string)($j['id'] ?? ''), (string)($j['status'] ?? ''), (int)($j['done'] ?? 0), (int)($j['failed'] ?? 0)];
    }
    $rest = $st(imeta_path($pid)) . '|' . $st(ws_file('proj', $pid)) . '|' . $st(ws_file('picks', $pid))
          . '|' . md5((string)json_encode($jobs)) . '|' . (ws_worker_alive() ? 'w1' : 'w0');
    return ['sig' => md5($rest . '|' . $chat), 'chat' => md5($chat), 'rest' => md5($rest)];
}

// ---- action cards (Claude proposes, a human confirms) -------------------------------------
// Validate + normalise one proposed action. Returns [kind, args] or null (dropped).
function ws_api_action_clean(string $kind, array $a): ?array {
    $maxTakes = max(1, (int)ws_settings()['maxTakes']);
    if ($kind === 'set_prompt') {
        $page = ws_api_int($a['page'] ?? 0); $prompt = ws_api_text($a['prompt'] ?? '', 2500);
        if ($page < 1 || $page > 999 || $prompt === '') return null;
        return ['set_prompt', ['page' => $page, 'title' => ws_api_text($a['title'] ?? '', 120, false), 'prompt' => $prompt]];
    }
    if ($kind === 'add_pages') {
        $pages = [];
        foreach (array_slice(array_values((array)($a['pages'] ?? [])), 0, 40) as $p) {
            if (!is_array($p)) continue;
            $t = ws_api_text($p['title'] ?? '', 120, false); $pr = ws_api_text($p['prompt'] ?? '', 2500);
            if ($t === '' && $pr === '') continue;
            $pages[] = ['title' => $t, 'prompt' => $pr];
        }
        return $pages ? ['add_pages', ['pages' => $pages]] : null;
    }
    if ($kind === 'generate') {
        $page = ws_api_int($a['page'] ?? 0); $takes = ws_api_int($a['takes'] ?? 0);
        if ($page < 1 || $page > 999) return null;
        if ($takes < 1) $takes = 2;
        return ['generate', ['page' => $page, 'takes' => min($maxTakes, $takes)]];
    }
    return null;
}
function ws_api_action_summary(string $kind, array $args): string {
    if ($kind === 'set_prompt') {
        $p = (string)$args['prompt'];
        $t = (string)($args['title'] ?? '');
        return 'Set page ' . (int)$args['page'] . ' prompt' . ($t !== '' ? ' ("' . $t . '")' : '') . ': '
             . (mb_strlen($p) > 160 ? mb_substr($p, 0, 157) . '...' : $p);
    }
    if ($kind === 'add_pages') {
        $n = count((array)$args['pages']);
        $titles = array_values(array_filter(array_map(fn($p) => (string)($p['title'] ?? ''), (array)$args['pages']), 'strlen'));
        $tl = implode(', ', array_slice($titles, 0, 4)) . (count($titles) > 4 ? ', ...' : '');
        return 'Add ' . $n . ' page' . ($n === 1 ? '' : 's') . ($tl !== '' ? ': ' . $tl : '');
    }
    if ($kind === 'generate') {
        $t = (int)$args['takes'];
        return 'Generate ' . $t . ' take' . ($t === 1 ? '' : 's') . ' of page ' . (int)$args['page'];
    }
    return $kind;
}
// Run a confirmed action. Returns [bool ok, string resultText].
function ws_api_action_exec(string $pid, string $kind, array $args): array {
    $c = ws_api_action_clean($kind, $args);
    if (!$c) return [false, 'This suggestion is not valid any more.'];
    [$kind, $args] = $c;
    if ($kind === 'set_prompt') {
        $res = ''; $err = '';
        ws_api_proj_update($pid, function ($d) use ($args, &$res, &$err) {
            foreach ($d['pages'] as &$pg) {
                if ((int)($pg['n'] ?? 0) !== $args['page']) continue;
                $pg['prompt'] = $args['prompt'];
                if ($args['title'] !== '') $pg['title'] = $args['title'];
                $res = 'Page ' . $args['page'] . ' prompt saved.';
                return $d;
            }
            unset($pg);
            if ($args['page'] < ws_api_next_n($d)) { $err = ws_api_reused_n($args['page']); return $d; }
            if (count($d['pages']) >= WS_API_MAX_PAGES) { $err = 'This comic already has the maximum of ' . WS_API_MAX_PAGES . ' pages.'; return $d; }
            $d['pages'][] = ['n' => $args['page'], 'title' => $args['title'], 'prompt' => $args['prompt'], 'refs' => [], 'note' => ''];
            $res = 'Page ' . $args['page'] . ' created with this prompt.';
            return $d;
        });
        return $res !== '' ? [true, $res] : [false, $err !== '' ? $err : 'Could not save that prompt.'];
    }
    if ($kind === 'add_pages') {
        $first = 0; $last = 0;
        ws_api_proj_update($pid, function ($d) use ($args, &$first, &$last) {
            $next = ws_api_next_n($d);
            foreach ($args['pages'] as $p) {
                if (count($d['pages']) >= WS_API_MAX_PAGES || $next > 999) break;
                $n = $next++; if ($first === 0) $first = $n; $last = $n;
                $d['pages'][] = ['n' => $n, 'title' => $p['title'], 'prompt' => $p['prompt'], 'refs' => [], 'note' => ''];
            }
            return $d;
        });
        if ($first === 0) return [false, 'This comic already has the maximum of ' . WS_API_MAX_PAGES . ' pages.'];
        return [true, $first === $last ? "Added page $first." : "Added pages $first-$last."];
    }
    if ($kind === 'generate') {
        $r = ws_job_enqueue($pid, $args['page'], $args['takes']);
        if (empty($r['ok'])) return [false, (string)($r['error'] ?? 'Could not queue that.')];
        $t = (int)($r['job']['takes'] ?? $args['takes']); $left = (int)($r['left'] ?? -1);
        return [true, 'Queued ' . $t . ' take' . ($t === 1 ? '' : 's') . ' of page ' . $args['page'] . ($left >= 0 ? " ($left left today)." : '.')];
    }
    return [false, 'Unknown action.'];
}

// ---- Claude (the chat brain) --------------------------------------------------------------
const WS_API_SYSTEM_PROMPT = <<<'TXT'
You are the production assistant inside a comic studio workspace. The studio makes adult-oriented but non-explicit muscle-growth and transformation comics. You help a production lieutenant (and their teammates) run one comic: break a story into pages, write and refine page prompts, say what is left to do, and suggest fixes for weak pages.

How the workspace works: one page = one generated image. A page's prompt goes to the image model together with the reference images attached to that page. The team generates a few takes per page, picks the best one in the picker, and leaves a comment where a redo is needed. The owner reviews and releases finished comics; nobody in this workspace publishes anything.

Prompt-writing rules:
- References carry each character's appearance. A prompt describes action, camera/shot, setting, lighting, emotion and dialogue. Do not describe faces, hair or outfits that the refs already show.
- Never put "Page N" or any page number inside a prompt. It gets lettered onto the art.
- Every character is an adult who clearly reads 25 or older.
- Keep everything non-explicit.
- One page = one image. When several people are in frame, say how many (for example "two women, one man").
- Put dialogue in quotes and say who speaks it.

Actions. You can only PROPOSE actions; a person confirms each one before anything happens:
- set_prompt: set (or create) one page's prompt. Use page, title and prompt.
- add_pages: append new pages after the existing ones. Use pages, a list of {title, prompt}. Keep each prompt under about 400 characters, propose at most 12 pages per reply, and offer to continue with the rest.
- generate: queue takes for a page that already has a prompt. Use page and takes (1 to 4). Respect the daily image limit shown in the context.
Never claim something was done. Say what you propose; it runs only when someone confirms the card.

Keep replies short, concrete and in plain language for a new team member. Use an empty actions array when no action is needed. For fields an action does not use, send 0, "" or [].
TXT;

function ws_api_schema(): array {
    return [
        'type' => 'object', 'additionalProperties' => false, 'required' => ['reply', 'actions'],
        'properties' => [
            'reply' => ['type' => 'string'],
            'actions' => ['type' => 'array', 'items' => [
                'type' => 'object', 'additionalProperties' => false,
                'required' => ['kind', 'page', 'title', 'prompt', 'takes', 'pages'],
                'properties' => [
                    'kind'   => ['type' => 'string', 'enum' => ['set_prompt', 'add_pages', 'generate']],
                    'page'   => ['type' => 'integer'],
                    'title'  => ['type' => 'string'],
                    'prompt' => ['type' => 'string'],
                    'takes'  => ['type' => 'integer'],
                    'pages'  => ['type' => 'array', 'items' => [
                        'type' => 'object', 'additionalProperties' => false, 'required' => ['title', 'prompt'],
                        'properties' => ['title' => ['type' => 'string'], 'prompt' => ['type' => 'string']],
                    ]],
                ],
            ]],
        ],
    ];
}
function ws_api_oneline(string $s, int $max): string {
    $s = trim((string)preg_replace('/\s*\n\s*/u', ' / ', $s));
    return mb_strlen($s) > $max ? mb_substr($s, 0, $max - 3) . '...' : $s;
}
// Built server-side from the stores on every call (never from client input).
function ws_api_context(string $pid, array $me): string {
    $p = project_get($pid) ?? []; $proj = ws_proj($pid); $pages = ws_api_pages($pid, $proj);
    $L = [];
    $L[] = 'Comic: ' . (string)($p['name'] ?? $pid);
    $L[] = 'Brand: ' . (ws_project_brand($pid, $p ?: null) ?: '(not assigned)');
    $L[] = 'Stage: ' . (string)($p['stage'] ?? '');
    $L[] = 'Style: ' . ($proj['style'] !== '' ? $proj['style'] : '(not set)');
    $L[] = 'Aspect: ' . $proj['aspect'];
    $L[] = '';
    $L[] = 'Story (first 8000 characters):';
    $L[] = $proj['story'] !== '' ? mb_substr($proj['story'], 0, 8000) : '(no story written yet)';
    $L[] = '';
    $L[] = 'Pages (n | title | prompt | takes | picked | comment):';
    if (!$pages) $L[] = '(no pages yet)';
    foreach ($pages as $pg) {
        $pick = $pg['picked'] > 0 ? $pg['picked'] . ' picked' : ($pg['dropped'] ? 'dropped' : 'no pick');
        $L[] = $pg['n'] . ' | ' . ($pg['title'] !== '' ? ws_api_oneline($pg['title'], 120) : '-')
             . ' | ' . ($pg['prompt'] !== '' ? ws_api_oneline($pg['prompt'], 500) : '(no prompt)')
             . ' | ' . $pg['takes'] . ' takes | ' . $pick . ' | ' . ($pg['comment'] !== '' ? ws_api_oneline($pg['comment'], 300) : '-');
    }
    $L[] = '';
    $L[] = 'Refs (file -> label):';
    $refs = ws_api_refs($pid, $proj);
    if (!$refs) $L[] = '(no refs uploaded yet)';
    foreach ($refs as $r) $L[] = $r['file'] . ' -> ' . ($r['label'] !== '' ? ws_api_oneline($r['label'], 80) : '(no label)');
    $L[] = '';
    $q = ws_quota_status($me['uid'], $me['isLt']);
    $L[] = 'Images left today for ' . $me['name'] . ': ' . (int)$q['left'] . ($me['isLt'] ? ' of ' . (int)$q['cap'] : ' (studio-wide)');
    $L[] = 'Last jobs:';
    $jobs = ws_api_jobs($pid, $me['uid'], $me['isLt'], 5);
    if (!$jobs) $L[] = '(none)';
    foreach ($jobs as $j) $L[] = 'page ' . $j['page'] . ' | ' . $j['takes'] . ' takes | done ' . $j['done'] . ' | failed ' . $j['failed'] . ' | ' . $j['status'] . ' | by ' . $j['by'];
    return implode("\n", $L);
}
function ws_api_thread(string $pid, int $beforeId): string {
    $msgs = array_values(array_filter(ws_chat($pid), fn($m) => is_array($m) && (int)($m['id'] ?? 0) < $beforeId));
    $L = [];
    foreach (array_slice($msgs, -20) as $m) {
        $role = (string)($m['role'] ?? ''); $text = ws_api_oneline((string)($m['text'] ?? ''), 1200);
        if ($role === 'system') { $L[] = '[system] ' . $text; continue; }
        $L[] = ($role === 'ai' ? 'Claude' : (string)($m['by'] ?? 'Someone')) . ': ' . $text;
        foreach ((array)($m['actions'] ?? []) as $a) {
            if (!is_array($a)) continue;
            $L[] = '  [proposed: ' . ws_api_oneline((string)($a['summary'] ?? ($a['kind'] ?? '')), 200) . ' -> ' . (string)($a['status'] ?? '')
                 . (!empty($a['result']) ? ': ' . ws_api_oneline((string)$a['result'], 200) : '') . ']';
        }
    }
    return $L ? implode("\n", $L) : '(no earlier messages)';
}
// The Messages request body for one reply (context + thread built from the stores, never from the client).
function ws_api_claude_body(string $pid, string $newText, array $me, int $newMsgId): array {
    $content = "<comic_context>\n" . ws_api_context($pid, $me) . "\n</comic_context>\n\n"
             . "<recent_thread>\n" . ws_api_thread($pid, $newMsgId) . "\n</recent_thread>\n\n"
             . 'NEW MESSAGE from ' . $me['name'] . ': ' . $newText;
    return [
        'max_tokens'    => WS_API_CHAT_MAX_TOKENS,
        'output_config' => ['effort' => (string)ws_settings()['chatEffort'], 'format' => ['type' => 'json_schema', 'schema' => ws_api_schema()]],
        'system'        => [['type' => 'text', 'text' => WS_API_SYSTEM_PROMPT, 'cache_control' => ['type' => 'ephemeral']]],
        'messages'      => [['role' => 'user', 'content' => $content]],
    ];
}
// What one finished ws_ai_call() costs the person: [actualUsd, refundMsg].
//  - Claude answered: its real cost.
//  - A definite API error (HTTP >= 400 with a JSON error body; ws_ai_call returns ok=false WITH the
//    decoded json): not billed, so cost 0 and the message is given back.
//  - Anything else (timeout, transport error, an unreadable body): it may have been billed, so the
//    whole worst-case reservation stays charged.
function ws_api_claude_cost(array $r, float $reserveUsd): array {
    $j = $r['json'] ?? null;
    if (!empty($r['ok']) && is_array($j)) return [(float)($r['usd'] ?? 0), false];
    if (empty($r['ok']) && is_array($j) && isset($j['error'])) return [0.0, true];
    return [$reserveUsd, false];
}
// Turn a ws_ai_call() result into the chat row to append.
function ws_api_claude_row(array $r): array {
    if (empty($r['ok']) || !is_array($r['json'] ?? null)) {
        return ws_api_sys('Claude could not answer right now (' . ws_api_text((string)($r['error'] ?? 'unknown error'), 240, false) . '). The team thread still works.');
    }
    $j = $r['json']; $stop = (string)($j['stop_reason'] ?? '');
    if ($stop === 'refusal') {
        return ['role' => 'ai', 'uid' => 'claude', 'by' => 'Claude', 'text' => "I can't help with that one — try rephrasing.", 'actions' => []];
    }
    if ($stop === 'max_tokens') {
        return ws_api_sys("Claude's answer ran too long and was cut off. Try asking for fewer pages at a time.");
    }
    $data = json_decode(ws_ai_text($j), true);
    if (!is_array($data) || !array_key_exists('reply', $data)) {
        return ws_api_sys("Claude's answer could not be read. Please try again.");
    }
    $actions = []; $i = 0;
    foreach (array_slice(array_values((array)($data['actions'] ?? [])), 0, 5) as $a) {
        if (!is_array($a)) continue;
        $c = ws_api_action_clean(is_string($a['kind'] ?? null) ? $a['kind'] : '', $a);
        if (!$c) continue;
        $actions[] = ['aid' => 'a' . (++$i), 'kind' => $c[0], 'args' => $c[1], 'summary' => ws_api_action_summary($c[0], $c[1]), 'status' => 'pending'];
    }
    $reply = ws_api_text($data['reply'], 6000);
    if ($reply === '') $reply = $actions ? 'Here is what I propose:' : '(no reply)';
    return ['role' => 'ai', 'uid' => 'claude', 'by' => 'Claude', 'text' => $reply, 'actions' => $actions, 'model' => (string)($j['model'] ?? '')];
}

// ============================================================================================
s_boot();
if (!is_authed()) ws_api_fail('Sign in', 401);          // (a lieutenant session outside its scope is denied inside is_authed)

$ME = ['name' => current_studio_user(), 'uid' => ws_uid(), 'isLt' => ws_is_lt(), 'isOwner' => ws_is_owner()];
$method = (string)($_SERVER['REQUEST_METHOD'] ?? 'GET');
$doRaw = $_GET['do'] ?? ($_POST['do'] ?? '');
$do = is_string($doRaw) ? $doRaw : '';

if (!in_array($do, WS_API_GET, true) && !in_array($do, WS_API_POST, true)) ws_api_fail('Unknown action.', 404);
if (in_array($do, WS_API_POST, true)) {
    if ($method !== 'POST') ws_api_fail('Use POST for this action.', 405);
    if (!$_POST && !$_FILES && (int)($_SERVER['CONTENT_LENGTH'] ?? 0) > 0) {
        ws_api_fail('That upload is too large for the server. Send fewer or smaller files at a time.', 413);
    }
    if (!csrf_ok()) ws_api_fail('Your session expired. Reload the page and try again.', 403);
}

switch ($do) {

// ---- reads -----------------------------------------------------------------------------------
case 'ping': {
    $pid = ws_api_pid();
    session_write_close();
    $sg = ws_api_sigs($pid);
    ws_json_out(['ok' => true, 'sig' => $sg['sig'], 'chat' => $sg['chat'], 'rest' => $sg['rest']]);
}

case 'state': {
    $pid = ws_api_pid();
    session_write_close();
    $sg = ws_api_sigs($pid);                                  // taken BEFORE the reads, so a write in between re-triggers
    $p = project_get($pid) ?? [];
    $proj = ws_proj($pid);
    ws_json_out([
        'ok' => true,
        'me' => ['name' => $ME['name'], 'isLt' => $ME['isLt'], 'isOwner' => $ME['isOwner'], 'uid' => $ME['uid']],
        'project' => ['id' => $pid, 'name' => (string)($p['name'] ?? $pid), 'status' => (string)($p['status'] ?? ''),
                      'stage' => (string)($p['stage'] ?? ''), 'brand' => ws_project_brand($pid, $p ?: null)],
        'proj' => ['story' => $proj['story'], 'style' => $proj['style'], 'aspect' => $proj['aspect'],
                   'pages' => $proj['pages'], 'refs' => $proj['refs']],
        'pages' => ws_api_pages($pid, $proj),
        'refs' => ws_api_refs($pid, $proj),
        'jobs' => ws_api_jobs($pid, $ME['uid'], $ME['isLt']),
        'quota' => ws_quota_status($ME['uid'], $ME['isLt']),
        'worker' => ['alive' => ws_worker_alive()],
        'settings' => ['maxTakes' => (int)ws_settings()['maxTakes']],
        'sig' => $sg['sig'], 'sigs' => ['chat' => $sg['chat'], 'rest' => $sg['rest']],
    ]);
}

case 'chat': {
    $pid = ws_api_pid();
    session_write_close();
    $since = max(0, ws_api_int($_GET['since'] ?? 0));
    $msgs = array_values(array_filter(ws_chat($pid, $since), 'is_array'));
    if ($since === 0) $msgs = array_slice($msgs, -300);     // first load: the recent thread only
    ws_json_out(['ok' => true, 'msgs' => $msgs]);
}

// ---- comics -----------------------------------------------------------------------------------
case 'create': {
    $name = ws_api_text($_POST['name'] ?? '', 120, false);
    if ($name === '') ws_api_fail('Give the comic a name.');
    $brand = ws_api_text($_POST['brand'] ?? '', 60, false);
    $allowed = $ME['isLt'] ? array_values((array)((ws_me() ?? [])['brands'] ?? [])) : ws_team()['brands'];
    if ($brand === '' || !in_array($brand, $allowed, true)) ws_api_fail('Pick one of your brands.');
    $style = ws_api_text($_POST['style'] ?? '', 2000);
    $now = date('c');
    $made = s_with_lock(PROJECTS_FILE, function ($all) use ($name, $now) {
        $all = is_array($all) ? $all : [];
        $base = slugify($name);
        if (strlen(trim(substr($base, 2), '-')) < 2 && strpos($base, 'p-') === 0) $base = 'comic-' . substr(nid(), 0, 6);
        $base = rtrim(substr($base, 0, 44), '-');
        $taken = []; foreach ($all as $row) if (is_array($row)) $taken[(string)($row['id'] ?? '')] = true;
        $pb = (array)(ws_team_norm(s_read(WS_TEAM, []))['projectBrands']);      // fresh, not the per-request cache
        // leftover workspace stores: data/ws/<kind>-<id>.json (proj, chat, picks, ...); exact id match only
        $wsLeft = function (string $id): bool {
            foreach ((array)glob(WS_DIR . '/*-' . $id . '.json') as $f) if (preg_match('/^[a-z]+-' . preg_quote($id, '/') . '\.json$/', basename((string)$f))) return true;
            return false;
        };
        $id = $base; $i = 2;
        // never reuse an id that still has leftover data (a deleted comic's images, chat, picks or brand must not resurface)
        while (isset($taken[$id]) || array_key_exists($id, $pb) || is_file(imeta_path($id)) || is_dir(project_dir($id)) || $wsLeft($id)) $id = $base . '-' . $i++;
        $row = ['id' => $id, 'name' => $name, 'status' => 'active', 'stage' => 'page-build', 'tags' => ['workspace'],
                'notes' => '', 'cover' => null, 'created' => $now, 'updated' => $now];
        array_unshift($all, $row);
        return ['data' => $all, 'result' => $row];
    });
    $id = (string)$made['id'];
    ws_team_update(function ($t) use ($id, $brand, $made) { $t['projectBrands'][$id] = ws_pb_make($brand, $made); return $t; });
    ws_api_proj_update($id, function ($d) use ($style) { $d['style'] = $style; return $d; });
    ws_chat_append($id, [ws_api_sys('📁 ' . $name . ' created by ' . $ME['name'])]);
    ws_json_out(['ok' => true, 'id' => $id]);
}

case 'setproj': {
    $pid = ws_api_pid();
    $set = [];
    if (array_key_exists('story', $_POST)) $set['story'] = ws_api_text($_POST['story'], 20000);
    if (array_key_exists('style', $_POST)) $set['style'] = ws_api_text($_POST['style'], 2000);
    if (array_key_exists('aspect', $_POST)) {
        $a = ws_api_text($_POST['aspect'], 8, false);
        if (!in_array($a, WS_API_ASPECTS, true)) ws_api_fail('Pick one of the listed aspect ratios.');
        $set['aspect'] = $a;
    }
    if (!$set) ws_api_fail('Nothing to save.');
    ws_api_proj_update($pid, function ($d) use ($set) { return array_merge($d, $set); });
    ws_json_out(['ok' => true]);
}

case 'ready': {
    $pid = ws_api_pid();
    $res = s_with_lock(PROJECTS_FILE, function ($all) use ($pid) {
        $all = is_array($all) ? $all : [];
        foreach ($all as &$row) {
            if (!is_array($row) || (string)($row['id'] ?? '') !== $pid) continue;
            if (($row['stage'] ?? '') === 'publish') return ['result' => 'publish'];   // never move a comic backwards
            $row['stage'] = 'review'; $row['updated'] = date('c');
            return ['data' => $all, 'result' => 'ok'];
        }
        unset($row);
        return ['result' => 'missing'];
    });
    if ($res === 'missing') ws_api_fail('Unknown comic.', 404);
    if ($res === 'ok') ws_chat_append($pid, [ws_api_sys('✅ ' . $ME['name'] . ' marked this comic ready for owner review')]);
    ws_json_out(['ok' => true, 'stage' => $res === 'ok' ? 'review' : 'publish']);
}

// ---- pages --------------------------------------------------------------------------------------
case 'page_save': {
    $pid = ws_api_pid();
    $n = ws_api_int($_POST['n'] ?? 0);
    if ($n < 0 || $n > 999) ws_api_fail('Bad page number.');
    $title  = array_key_exists('title', $_POST) ? ws_api_text($_POST['title'], 120, false) : null;
    $prompt = array_key_exists('prompt', $_POST) ? ws_api_text($_POST['prompt'], 2500) : null;
    $refsIn = null;
    if (array_key_exists('refs', $_POST)) {
        $raw = $_POST['refs'];
        $list = is_array($raw) ? $raw : (is_string($raw) && $raw !== '' ? explode(',', $raw) : []);
        $refsIn = [];
        foreach ($list as $f) { $f = ws_api_file($f); if ($f !== '' && !in_array($f, $refsIn, true)) $refsIn[] = $f; }
        $refsIn = array_slice($refsIn, 0, 12);
    }
    $newN = 0; $err = '';
    ws_api_proj_update($pid, function ($d) use ($n, $title, $prompt, $refsIn, &$newN, &$err) {
        $known = []; foreach ($d['refs'] as $r) $known[(string)($r['file'] ?? '')] = true;
        $refs = $refsIn === null ? null : array_values(array_filter($refsIn, fn($f) => isset($known[$f])));
        if ($n > 0) {
            foreach ($d['pages'] as &$pg) {
                if ((int)($pg['n'] ?? 0) !== $n) continue;
                if ($title !== null) $pg['title'] = $title;
                if ($prompt !== null) $pg['prompt'] = $prompt;
                if ($refs !== null) $pg['refs'] = $refs;
                $newN = $n;
                return $d;
            }
            unset($pg);
        }
        $next = ws_api_next_n($d);
        if ($n > 0 && $n < $next) { $err = ws_api_reused_n($n); return $d; }   // e.g. a teammate deleted it meanwhile
        if (count($d['pages']) >= WS_API_MAX_PAGES) { $err = 'This comic already has the maximum of ' . WS_API_MAX_PAGES . ' pages.'; return $d; }
        if ($n === 0) $n = $next;                                                    // nextN is bumped by ws_api_proj_update
        if ($n > 999) { $err = 'This comic has used up its page numbers (999).'; return $d; }
        $d['pages'][] = ['n' => $n, 'title' => (string)$title, 'prompt' => (string)$prompt, 'refs' => $refs ?? [], 'note' => ''];
        $newN = $n;
        return $d;
    });
    if ($err !== '') ws_api_fail($err);
    ws_json_out(['ok' => true, 'n' => $newN]);
}

case 'page_delete': {
    $pid = ws_api_pid();
    $n = ws_api_int($_POST['n'] ?? 0);
    if ($n < 1) ws_api_fail('Bad page number.');
    $found = false;
    ws_api_proj_update($pid, function ($d) use ($n, &$found) {   // nextN stays: the number is never handed out again
        $keep = [];
        foreach ($d['pages'] as $pg) { if ((int)($pg['n'] ?? 0) === $n) { $found = true; continue; } $keep[] = $pg; }
        $d['pages'] = $keep;
        return $d;
    });
    if (!$found) ws_api_fail("Page $n is not in this comic.", 404);
    $group = ws_page_group($n);
    // 1) its picker record goes
    s_with_lock(ws_file('picks', $pid), function ($d) use ($group) {
        if (!is_array($d) || !is_array($d['pages'] ?? null) || !array_key_exists($group, $d['pages'])) return ['result' => null];
        unset($d['pages'][$group]);
        return ['data' => $d, 'result' => null];
    });
    // 2) its takes move to "Deleted Page NN <time>" (nothing is deleted). A take the picker had accepted
    //    (row key 'pk' = {acc, r}: what the pick changed, written by picker.php) is un-picked exactly like
    //    picker.php does it: only fields still holding the picker's value are restored. Keeps made elsewhere stay.
    $dest = 'Deleted ' . $group . ' ' . date('Y-m-d H:i:s');
    $moved = 0;
    images_update($pid, function ($meta) use ($group, $dest, &$moved) {
        foreach ($meta as $i => $m) {
            if (!is_array($m) || !empty($m['isref']) || !empty($m['blueprint']) || trim((string)($m['group'] ?? '')) !== $group) continue;
            $meta[$i]['group'] = $dest; $moved++;
            if (!array_key_exists('pk', $m)) continue;
            $pk = is_array($m['pk']) ? $m['pk'] : [];
            $pr = $pk['r'] ?? null;
            if (!empty($m['accepted'])) $meta[$i]['accepted'] = !empty($pk['acc']);
            if (($m['rating'] ?? null) === ($pr === 'bad' ? 'bad' : 'good')) {
                if ($pr === null) unset($meta[$i]['rating']); else $meta[$i]['rating'] = $pr;
            }
            unset($meta[$i]['pk']);
        }
        return $meta;
    });
    $line = '🗑 ' . $ME['name'] . ' deleted page ' . $n . ($moved ? '. Its ' . $moved . ' take' . ($moved === 1 ? '' : 's') . ' moved to "' . $dest . '" in the studio.' : '.');
    ws_chat_append($pid, [ws_api_sys($line)]);
    ws_json_out(['ok' => true, 'moved' => $moved, 'group' => $dest]);
}

// ---- uploads + refs -----------------------------------------------------------------------------
case 'upload': {
    $pid = ws_api_pid();
    $kind = ws_api_text($_POST['kind'] ?? '', 8, false);
    if (!in_array($kind, ['ref', 'take'], true)) ws_api_fail('Upload kind must be ref or take.');
    $page = ws_api_int($_POST['page'] ?? 0);
    if ($kind === 'take' && ($page < 1 || !ws_page_get(ws_proj($pid), $page))) ws_api_fail("Page $page does not exist.");
    $F = $_FILES['files'] ?? null;
    if (!is_array($F) || !isset($F['name'])) ws_api_fail('No files received.');
    session_write_close();                                    // resizing can take a while; don't block the page's polling
    $names = (array)$F['name']; $tmps = (array)($F['tmp_name'] ?? []); $errs = (array)($F['error'] ?? []); $sizes = (array)($F['size'] ?? []);
    $files = []; $errors = []; $newRefs = []; $by = $ME['name'];
    $i = 0;
    foreach (array_keys($names) as $k) {
        $orig = ws_api_fname($names[$k] ?? '');
        if (++$i > WS_API_MAX_FILES) { $errors[] = $orig . ': skipped (max ' . WS_API_MAX_FILES . ' files per upload)'; continue; }
        $tmp = $tmps[$k] ?? ''; $e = $errs[$k] ?? UPLOAD_ERR_NO_FILE; $size = $sizes[$k] ?? 0;
        if (!is_string($tmp) || !is_int($e) || !is_int($size)) { $errors[] = $orig . ': not a file'; continue; }
        if ($e === UPLOAD_ERR_INI_SIZE || $e === UPLOAD_ERR_FORM_SIZE) { $errors[] = $orig . ': too large'; continue; }
        if ($e !== UPLOAD_ERR_OK) { $errors[] = $orig . ': upload failed (code ' . $e . ')'; continue; }
        if ($size > MAX_BYTES) { $errors[] = $orig . ': too large (max ' . (int)(MAX_BYTES / 1048576) . ' MB)'; continue; }
        if (!is_uploaded_file($tmp)) { $errors[] = $orig . ': not an upload'; continue; }
        if (!in_array(ext_of($orig), IMG_EXT, true)) { $errors[] = $orig . ': not an image (jpg, png, webp, gif)'; continue; }
        if (@getimagesize($tmp) === false) { $errors[] = $orig . ': not a readable image'; continue; }
        $extra = $kind === 'take'
            ? ['group' => ws_page_group($page), 'tags' => ['ws-upload'], 'by' => $by, 'source' => 'ws']
            : ['isref' => true, 'group' => '', 'tags' => ['ws-ref'], 'by' => $by, 'source' => 'ws'];
        $row = ws_add_image($pid, $tmp, $orig, $extra);
        if (!$row) { $errors[] = $orig . ': could not be stored'; continue; }
        $files[] = (string)$row['file'];
        if ($kind === 'ref') {
            $label = ws_api_text(pathinfo($orig, PATHINFO_FILENAME), 80, false);
            $newRefs[] = ['file' => (string)$row['file'], 'label' => $label, 'kind' => 'ref'];
        }
    }
    if ($newRefs) {
        ws_api_proj_update($pid, function ($d) use ($newRefs) {
            foreach ($newRefs as $r) if (count($d['refs']) < WS_API_MAX_REFS) $d['refs'][] = $r;
            return $d;
        });
    }
    $c = count($files);
    if ($c) {
        $msg = $kind === 'take'
            ? '⬆ ' . $by . ' uploaded ' . $c . ' take' . ($c === 1 ? '' : 's') . ' for page ' . $page
            : '⬆ ' . $by . ' uploaded ' . $c . ' ref' . ($c === 1 ? '' : 's');
        ws_chat_append($pid, [ws_api_sys($msg)]);
    }
    ws_json_out(['ok' => $c > 0, 'files' => $files, 'errors' => $errors, 'error' => $c ? null : ($errors[0] ?? 'No files received.')], $c ? 200 : 400);
}

case 'ref_update': {
    $pid = ws_api_pid();
    $file = ws_api_file($_POST['file'] ?? '');
    if ($file === '') ws_api_fail('Bad file name.');
    $label = ws_api_text($_POST['label'] ?? '', 80, false);
    $found = false;
    ws_api_proj_update($pid, function ($d) use ($file, $label, &$found) {
        foreach ($d['refs'] as &$r) if ((string)($r['file'] ?? '') === $file) { $r['label'] = $label; $found = true; }
        unset($r);
        return $d;
    });
    if (!$found) ws_api_fail('That reference is not in this comic.', 404);
    ws_json_out(['ok' => true]);
}

case 'ref_remove': {
    $pid = ws_api_pid();
    $file = ws_api_file($_POST['file'] ?? '');
    if ($file === '') ws_api_fail('Bad file name.');
    $found = false;
    ws_api_proj_update($pid, function ($d) use ($file, &$found) {
        $keep = [];
        foreach ($d['refs'] as $r) { if ((string)($r['file'] ?? '') === $file) { $found = true; continue; } $keep[] = $r; }
        $d['refs'] = $keep;
        foreach ($d['pages'] as &$pg) $pg['refs'] = array_values(array_filter((array)($pg['refs'] ?? []), fn($f) => $f !== $file));
        unset($pg);
        return $d;
    });
    if (!$found) ws_api_fail('That reference is not in this comic.', 404);
    ws_json_out(['ok' => true]);   // unlinks from the workspace only; the image file stays
}

// ---- generation -----------------------------------------------------------------------------
case 'generate': {
    $pid = ws_api_pid();
    $page = ws_api_int($_POST['page'] ?? 0);
    $takes = ws_api_int($_POST['takes'] ?? 0);
    if ($page < 1) ws_api_fail('Bad page number.');
    if ($takes < 1) ws_api_fail('Ask for at least one take.');
    $prompt = ws_api_text($_POST['prompt'] ?? '', 2500);
    $r = ws_job_enqueue($pid, $page, $takes, $prompt);
    if (empty($r['ok'])) ws_api_fail((string)($r['error'] ?? 'Could not queue that.'), 400, ['left' => (int)($r['left'] ?? -1)]);
    $t = (int)$r['job']['takes'];
    ws_chat_append($pid, [ws_api_sys('🎨 ' . $ME['name'] . ' queued ' . $t . ' take' . ($t === 1 ? '' : 's') . ' of page ' . $page)]);
    $job = $r['job'];
    ws_json_out(['ok' => true, 'left' => (int)$r['left'], 'job' => [
        'id' => $job['id'], 'page' => $job['page'], 'takes' => $job['takes'], 'status' => $job['status'], 'by' => $job['by'],
    ]]);
}

case 'cancel': {
    $pid = ws_api_pid();
    $job = is_string($_POST['job'] ?? null) ? (string)$_POST['job'] : '';
    if (!preg_match('/^wsj_[A-Za-z0-9]{4,32}$/', $job)) ws_api_fail('Bad job id.');
    $r = ws_job_cancel($job, $pid);
    if (empty($r['ok'])) ws_api_fail((string)($r['error'] ?? 'Could not cancel.'), 409);
    ws_json_out(['ok' => true]);
}

// ---- chat ---------------------------------------------------------------------------------------
case 'chat_send': {
    $pid = ws_api_pid();
    $rawText = $_POST['text'] ?? '';
    if ((int)($_SERVER['CONTENT_LENGTH'] ?? 0) > WS_API_CHAT_MAX_BODY || (is_string($rawText) && strlen($rawText) > WS_API_CHAT_MAX_BODY)) {
        ws_api_fail('That message is too long (4000 characters max).', 413);
    }
    $full = ws_api_text($rawText, WS_API_CHAT_MAX_BODY);
    if ($full === '') ws_api_fail('Write a message first.');
    if (mb_strlen($full) > 4000) ws_api_fail('That message is too long (4000 characters max).');
    $ai = ws_api_int($_POST['ai'] ?? 0) === 1;
    if ($ME['isLt']) {                                         // flood guard: every post to the thread counts (team or Claude)
        $slow = ws_api_team_rate($ME['uid']);
        if ($slow !== '') ws_api_fail($slow, 429);
    }
    $new = ws_chat_append($pid, [['role' => 'user', 'uid' => $ME['uid'], 'by' => $ME['name'], 'text' => $full, 'ai' => $ai, 'actions' => []]]);
    if (!$ai) ws_json_out(['ok' => true, 'msgs' => $new]);

    // No AI key installed: no call can be made, so nothing is charged.
    if (ws_ai_key() === '') {
        $new = array_merge($new, ws_chat_append($pid, [ws_api_claude_row(['ok' => false, 'json' => null, 'error' => 'No AI key installed in the Studio.'])]));
        ws_json_out(['ok' => true, 'msgs' => $new]);
    }
    // Build the request first: its size sets the worst-case cost reserved up front, so parallel
    // requests can never run past the person's daily dollars.
    $body = ws_api_claude_body($pid, $full, $ME, (int)($new[0]['id'] ?? PHP_INT_MAX));
    $bodyLen = strlen((string)json_encode($body, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE | JSON_INVALID_UTF8_SUBSTITUTE));
    $reserve = ws_chat_reserve_usd($bodyLen, (int)$body['max_tokens']);
    ignore_user_abort(true);                                   // once taken, always settle + store the reply, even if the tab goes away
    $q = ws_chat_quota_take($ME['uid'], $ME['isLt'], $reserve);
    if (empty($q['ok'])) {
        // Over today's allowance, or this person's previous question is still with Claude. Nothing was
        // taken, so there is nothing to settle or refund: just a friendly line in the thread.
        $err = (string)($q['error'] ?? 'Daily Claude chat limit reached.');
        $new = array_merge($new, ws_chat_append($pid, [ws_api_sys('For ' . $ME['name'] . ': ' . $err)]));
        ws_json_out(['ok' => true, 'msgs' => $new, 'error' => $err]);
    }
    // Claude can take up to ~60 s: release the session lock so the page keeps polling meanwhile.
    session_write_close();
    $res = ['ok' => false, 'json' => null, 'error' => 'the request did not finish', 'usd' => 0.0];
    try {
        $res = ws_ai_call($body);
    } finally {
        [$actual, $refund] = ws_api_claude_cost($res, $reserve);
        ws_chat_settle($ME['uid'], $reserve, $actual, $refund);   // exactly once per taken reservation
    }
    $new = array_merge($new, ws_chat_append($pid, [ws_api_claude_row($res)]));
    ws_json_out(['ok' => true, 'msgs' => $new]);
}

case 'action': {
    $pid = ws_api_pid();
    $mid = ws_api_int($_POST['msg'] ?? 0);
    $aid = is_string($_POST['aid'] ?? null) ? (string)$_POST['aid'] : '';
    $decision = is_string($_POST['decision'] ?? null) ? (string)$_POST['decision'] : '';
    if ($mid < 1 || !preg_match('/^a\d{1,2}$/', $aid) || !in_array($decision, ['confirm', 'dismiss'], true)) ws_api_fail('Bad request.');
    // 1) claim the card atomically, so two people clicking Confirm cannot run it twice
    $claimErr = ''; $claimed = null; $who = $ME['name'];
    $msg = ws_chat_patch($pid, $mid, function ($m) use ($aid, $who, &$claimErr, &$claimed) {
        if (($m['role'] ?? '') !== 'ai') { $claimErr = 'That message has no actions.'; return $m; }
        if (time() - (int)($m['ts'] ?? 0) > 86400) { $claimErr = 'This suggestion is more than a day old. Ask Claude again.'; return $m; }
        foreach ((array)($m['actions'] ?? []) as $i => $a) {
            if (!is_array($a) || ($a['aid'] ?? '') !== $aid) continue;
            if (($a['status'] ?? '') !== 'pending') { $claimErr = 'Someone already handled this card.'; return $m; }
            $m['actions'][$i]['status'] = 'working'; $m['actions'][$i]['decidedBy'] = $who;
            $claimed = $a;
            return $m;
        }
        $claimErr = 'That action was not found.';
        return $m;
    });
    if ($msg === null) ws_api_fail('That message was not found.', 404);
    if ($claimErr !== '' || !$claimed) ws_api_fail($claimErr ?: 'That action was not found.', 409, ['msg' => $msg]);

    // 2) run it (re-validated server-side) or dismiss it
    $kind = (string)($claimed['kind'] ?? ''); $args = (array)($claimed['args'] ?? []);
    $summary = (string)($claimed['summary'] ?? $kind);
    if ($decision === 'dismiss') { $ok = true; $status = 'dismissed'; $result = ''; }
    else { [$ok, $result] = ws_api_action_exec($pid, $kind, $args); $status = $ok ? 'confirmed' : 'failed'; }

    // 3) patch the card + leave a trail in the thread
    $msg = ws_chat_patch($pid, $mid, function ($m) use ($aid, $status, $result, $who) {
        foreach ((array)($m['actions'] ?? []) as $i => $a) {
            if (!is_array($a) || ($a['aid'] ?? '') !== $aid) continue;
            $m['actions'][$i]['status'] = $status; $m['actions'][$i]['result'] = $result;
            $m['actions'][$i]['decidedBy'] = $who; $m['actions'][$i]['decidedAt'] = ws_now();
        }
        return $m;
    });
    $line = $status === 'dismissed' ? '✖ ' . $who . ' dismissed: ' . $summary
          : ($status === 'confirmed' ? '✔ ' . $who . ' confirmed: ' . $summary . ' — ' . $result
                                     : '⚠ ' . $summary . ' — failed: ' . $result);
    $sys = ws_chat_append($pid, [ws_api_sys(mb_substr($line, 0, 600))]);
    if (!$ok) ws_api_fail($result, 400, ['msg' => $msg, 'msgs' => $sys]);
    ws_json_out(['ok' => true, 'msg' => $msg, 'msgs' => $sys, 'result' => $result]);
}

}
ws_api_fail('Unknown action.', 404);
