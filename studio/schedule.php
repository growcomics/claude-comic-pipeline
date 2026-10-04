<?php
// schedule.php — 📅 Release schedule: the long-horizon view of the posting board.
//
// posting.php answers "what fires this week" (next 4 Fridays + this month and next).
// THIS answers "how far ahead are we, per property, per lane, and who is making it" —
// the question the old Google Sheet ("Comics and Future releases - Visual Format")
// was built for and the studio never had. Same question the owner asked 2026-08-19:
// Alternate cannot tell what should be posted where without it.
//
// SAME DATA STORE as posting.php — data/posting.json. This is a second VIEW, not a
// second board: an item scheduled four months out and an item firing on Friday are
// the same record, so nothing is ever entered twice and nothing can drift apart.
// Fields this view adds to an item (posting.php's array_merge update preserves
// unknown keys, so the two stay compatible in both directions):
//     stage   production state — the sheet's colour legend, made queryable
//     artist  who is drawing it
//     weeks   how many consecutive weekly slots this drop occupies (merged cells)
//
// Pure renderer in the ops.php/review.php mold: PHP embeds the item list as JSON,
// vanilla JS draws the grid / drawer / filters, every mutation POSTs back here.
// Auth: studio session OR bridge key (same contract as posting.php).
// It schedules and tracks — a HUMAN still presses post. Nothing here fires outward.
declare(strict_types=1);
require_once __DIR__ . '/inc/boot.php';

define('SC_FILE', SDATA . '/posting.json');
define('SC_SYND', SDATA . '/syndication.json');

// Lanes: the board's three plus `weekly`, the serial cadence the sheet tracked as
// its own row and posting.php had nowhere to put (it was being filed under "side").
$SC_LANES = array(
    'faf'    => array('label' => 'Fan Art Friday', 'short' => 'Fan art'),
    'weekly' => array('label' => 'Weekly serial',  'short' => 'Weekly'),
    'comic'  => array('label' => 'Monthly comic',  'short' => 'Monthly'),
    'side'   => array('label' => 'Side content',   'short' => 'Side'),
);

// The sheet's colour legend, promoted from cell-fill to a real field.
$SC_STAGES = array(
    'planning'    => array('label' => 'Planning',        'color' => '#6F7380'),
    'notstarted'  => array('label' => 'Not started',     'color' => '#4A4D5C'),
    'missing'     => array('label' => 'Missing content', 'color' => '#B3523F'),
    '3d'          => array('label' => '3D work',         'color' => '#7A5CC4'),
    'inking'      => array('label' => 'Inking',          'color' => '#378ADD'),
    'coloring'    => array('label' => 'Coloring',        'color' => '#1D9E75'),
    'waitingtext' => array('label' => 'Waiting for text', 'color' => '#EF9F27'),
    'ready'       => array('label' => 'Ready to post',   'color' => '#5FD39A'),
    'posted'      => array('label' => 'Posted',          'color' => '#2E7D4F'),
    'missed'      => array('label' => 'Slot missed',     'color' => '#E24B4A'),
);

$SC_SITES = s_read(SDATA . '/cc-sites.json', array());
$SC_PROPS = array();
foreach (array('growgetter', 'maxxmuscle', 'bloombeauty') as $pk) {
    if (isset($SC_SITES[$pk])) {
        $SC_PROPS[$pk] = array('name' => (string)$SC_SITES[$pk]['name'], 'color' => (string)$SC_SITES[$pk]['color'], 'archived' => false);
    }
}
// Transferred away 2026-07-25 — kept so the imported history stays readable, but
// hidden until you ask for it. Never a target for new scheduling.
$SC_PROPS['giantessgirl'] = array('name' => 'GiantessGirl (transferred)', 'color' => '#6F7380', 'archived' => true);

function sc_bridge_ok(): bool {
    $cfg = s_read(SDATA . '/bridge.json', array());
    $key = (string)(isset($cfg['key']) ? $cfg['key'] : '');
    $given = (string)(isset($_POST['key']) ? $_POST['key'] : (isset($_GET['key']) ? $_GET['key'] : (isset($_SERVER['HTTP_X_BRIDGE_KEY']) ? $_SERVER['HTTP_X_BRIDGE_KEY'] : '')));
    return $key !== '' && strlen($given) >= 16 && hash_equals($key, $given);
}
$scKeyAuthed = sc_bridge_ok();
if (!$scKeyAuthed) require_auth();

// Monday of the week a date falls in — the grid's column unit.
function sc_week(string $date): string {
    $ts = strtotime($date . ' 00:00:00 UTC');
    if ($ts === false) return '';
    $dow = (int)gmdate('N', $ts);            // 1 = Monday
    return gmdate('Y-m-d', $ts - ($dow - 1) * 86400);
}

function sc_norm_item(array $it, array $stages, array $lanes, array $props): array {
    $stage = (string)($it['stage'] ?? '');
    if (!isset($stages[$stage])) {
        // Items created on posting.php have no stage yet: infer one from the
        // status it does have, so a mixed board still reads correctly.
        $st = (string)($it['status'] ?? 'draft');
        $stage = $st === 'posted' ? 'posted' : ($st === 'ready' ? 'ready' : ($st === 'skipped' ? 'missed' : 'planning'));
    }
    $lane = (string)($it['lane'] ?? '');
    if (!isset($lanes[$lane])) $lane = '';
    $prop = (string)($it['property'] ?? '');
    if (!isset($props[$prop])) $prop = '';
    $weeks = (int)($it['weeks'] ?? 1);
    if ($weeks < 1) $weeks = 1;
    if ($weeks > 60) $weeks = 60;
    $slot = (string)($it['slot'] ?? '');
    return array(
        'id'       => (string)($it['id'] ?? ''),
        'title'    => (string)($it['title'] ?? ''),
        'artist'   => (string)($it['artist'] ?? ''),
        'property' => $prop,
        'lane'     => $lane,
        'slot'     => $slot,
        'week'     => $slot !== '' ? sc_week($slot) : '',
        'weeks'    => $weeks,
        'stage'    => $stage,
        'status'   => (string)($it['status'] ?? 'draft'),
        'notes'    => (string)($it['notes'] ?? ''),
        'merged'   => !empty($it['merged']),
        'source'   => (string)($it['source'] ?? ''),
        // deliberately NOT the platform chips: the calendar never renders them and
        // they are the bulk of the file — posting.php owns that half.
    );
}

// ---------------- mutations --------------------------------------------------
// Every write goes through s_with_lock on the SHARED posting.json: posting.php,
// the drop-pipeline runner and this page can all be mid-write at once.
$action = isset($_POST['action']) ? (string)$_POST['action'] : '';
if ($action !== '') {
    if (!$scKeyAuthed) csrf_check();
    header('Content-Type: application/json');
    $id = (string)($_POST['id'] ?? '');
    $out = array('ok' => false, 'error' => 'Unknown action.');

    if ($action === 'save') {
        $isNew = ($id === '');
        $title = trim((string)($_POST['title'] ?? ''));
        if ($title === '') {
            $out = array('ok' => false, 'error' => 'Title required.');
        } else {
            $fields = array(
                'title'    => $title,
                'artist'   => trim((string)($_POST['artist'] ?? '')),
                'property' => isset($SC_PROPS[$_POST['property'] ?? '']) ? (string)$_POST['property'] : '',
                'lane'     => isset($SC_LANES[$_POST['lane'] ?? '']) ? (string)$_POST['lane'] : '',
                'stage'    => isset($SC_STAGES[$_POST['stage'] ?? '']) ? (string)$_POST['stage'] : 'planning',
                'notes'    => trim((string)($_POST['notes'] ?? '')),
                'weeks'    => max(1, min(60, (int)($_POST['weeks'] ?? 1))),
                'updatedAt' => gmdate('c'),
            );
            $slot = substr(preg_replace('/[^0-9\-]/', '', (string)($_POST['slot'] ?? '')), 0, 10);
            $fields['slot'] = $slot !== '' ? sc_week($slot) : '';
            // Keep `status` — posting.php's lanes and archive key off it — in step
            // with the stage the user just picked, so the two views never disagree.
            $fields['status'] = $fields['stage'] === 'posted' ? 'posted'
                : ($fields['stage'] === 'missed' ? 'skipped'
                : ($fields['stage'] === 'ready' ? 'ready' : 'draft'));

            $newId = $id;
            $res = s_with_lock(SC_FILE, function ($db) use ($fields, $id, $isNew, &$newId, $SC_LANES) {
                if (!is_array($db) || !isset($db['items']) || !is_array($db['items'])) $db = array('seq' => 0, 'items' => array());
                if ($isNew) {
                    $plats = array();
                    foreach (array('site', 'patreon', 'deviantart', 'twitter', 'instagram') as $p) $plats[$p] = 'todo';
                    $db['seq'] = (int)($db['seq'] ?? 0) + 1;
                    $newId = 'po_' . nid();
                    $db['items'][] = array_merge(array('id' => $newId, 'platforms' => $plats, 'createdAt' => gmdate('c')), $fields);
                    return array('data' => $db, 'result' => '');
                }
                foreach ($db['items'] as $i => $it) {
                    if (($it['id'] ?? '') === $id) {
                        $db['items'][$i] = array_merge($db['items'][$i], $fields);
                        return array('data' => $db, 'result' => '');
                    }
                }
                return array('data' => $db, 'result' => 'No such item.');
            });
            $out = $res === '' ? array('ok' => true, 'id' => $newId) : array('ok' => false, 'error' => (string)$res);
        }

    } elseif ($action === 'move') {
        // drag a bar to a different week / lane row
        $slot = substr(preg_replace('/[^0-9\-]/', '', (string)($_POST['slot'] ?? '')), 0, 10);
        $prop = (string)($_POST['property'] ?? '');
        $lane = (string)($_POST['lane'] ?? '');
        $res = s_with_lock(SC_FILE, function ($db) use ($id, $slot, $prop, $lane, $SC_PROPS, $SC_LANES) {
            if (!is_array($db) || !isset($db['items'])) return array('data' => $db, 'result' => 'Empty board.');
            foreach ($db['items'] as $i => $it) {
                if (($it['id'] ?? '') === $id) {
                    if ($slot !== '') $db['items'][$i]['slot'] = sc_week($slot);
                    if (isset($SC_PROPS[$prop]) && empty($SC_PROPS[$prop]['archived'])) $db['items'][$i]['property'] = $prop;
                    if (isset($SC_LANES[$lane])) $db['items'][$i]['lane'] = $lane;
                    $db['items'][$i]['updatedAt'] = gmdate('c');
                    return array('data' => $db, 'result' => '');
                }
            }
            return array('data' => $db, 'result' => 'No such item.');
        });
        $out = $res === '' ? array('ok' => true) : array('ok' => false, 'error' => (string)$res);

    } elseif ($action === 'stage') {
        $stage = (string)($_POST['stage'] ?? '');
        if (!isset($SC_STAGES[$stage])) {
            $out = array('ok' => false, 'error' => 'Bad stage.');
        } else {
            $res = s_with_lock(SC_FILE, function ($db) use ($id, $stage) {
                if (!is_array($db) || !isset($db['items'])) return array('data' => $db, 'result' => 'Empty board.');
                foreach ($db['items'] as $i => $it) {
                    if (($it['id'] ?? '') === $id) {
                        $db['items'][$i]['stage'] = $stage;
                        $db['items'][$i]['status'] = $stage === 'posted' ? 'posted'
                            : ($stage === 'missed' ? 'skipped' : ($stage === 'ready' ? 'ready' : 'draft'));
                        $db['items'][$i]['updatedAt'] = gmdate('c');
                        return array('data' => $db, 'result' => '');
                    }
                }
                return array('data' => $db, 'result' => 'No such item.');
            });
            $out = $res === '' ? array('ok' => true) : array('ok' => false, 'error' => (string)$res);
        }

    } elseif ($action === 'del') {
        $res = s_with_lock(SC_FILE, function ($db) use ($id) {
            if (!is_array($db) || !isset($db['items'])) return array('data' => $db, 'result' => 'Empty board.');
            foreach ($db['items'] as $i => $it) {
                if (($it['id'] ?? '') === $id) {
                    array_splice($db['items'], $i, 1);
                    return array('data' => $db, 'result' => '');
                }
            }
            return array('data' => $db, 'result' => 'No such item.');
        });
        $out = $res === '' ? array('ok' => true) : array('ok' => false, 'error' => (string)$res);

    } elseif ($action === 'synd') {
        // toggle one cell of the comic x destination matrix
        $dest = (string)($_POST['dest'] ?? '');
        $state = (string)($_POST['state'] ?? '');
        $url = trim((string)($_POST['url'] ?? ''));
        if (!preg_match('~^(https?://[^\s]{4,300})?$~', $url)) {
            $out = array('ok' => false, 'error' => 'Link must be an http(s) URL.');
        } else {
            $res = s_with_lock(SC_SYND, function ($db) use ($id, $dest, $state, $url) {
                if (!is_array($db) || !isset($db['rows'])) $db = array('destinations' => array(), 'rows' => array());
                foreach ($db['rows'] as $i => $r) {
                    if (($r['id'] ?? '') === $id) {
                        if ($dest !== '') {
                            if (!in_array($dest, $db['destinations'], true)) return array('data' => $db, 'result' => 'Unknown destination.');
                            $db['rows'][$i]['posted'][$dest] = $state === 'posted' ? 'posted' : '';
                        }
                        if (isset($_POST['url'])) $db['rows'][$i]['url'] = $url;
                        $db['rows'][$i]['updatedAt'] = gmdate('c');
                        return array('data' => $db, 'result' => '');
                    }
                }
                return array('data' => $db, 'result' => 'No such row.');
            });
            $out = $res === '' ? array('ok' => true) : array('ok' => false, 'error' => (string)$res);
        }
    }

    echo json_encode($out);
    exit;
}

// ---------------- render prep ------------------------------------------------
$db = s_read(SC_FILE, array('seq' => 0, 'items' => array()));
$rawItems = is_array($db['items'] ?? null) ? $db['items'] : array();
$items = array();
foreach ($rawItems as $it) {
    if (!is_array($it)) continue;
    $items[] = sc_norm_item($it, $SC_STAGES, $SC_LANES, $SC_PROPS);
}

$synd = s_read(SC_SYND, array('destinations' => array(), 'rows' => array()));
if (!is_array($synd['destinations'] ?? null)) $synd['destinations'] = array();
if (!is_array($synd['rows'] ?? null)) $synd['rows'] = array();

$payload = array(
    'items'    => $items,
    'props'    => $SC_PROPS,
    'lanes'    => $SC_LANES,
    'stages'   => $SC_STAGES,
    'synd'     => $synd,
    'today'    => gmdate('Y-m-d'),
    'thisWeek' => sc_week(gmdate('Y-m-d')),
    'user'     => $scKeyAuthed ? 'bridge' : current_studio_user(),
    'auth'     => $scKeyAuthed ? array('key' => (string)($_GET['key'] ?? '')) : array('csrf' => csrf()),
);
?><!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>📅 Schedule — Studio</title>
<link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="assets/studio.css">
<style>
.sc-wrap{max-width:1600px;margin:0 auto;padding:18px 18px 90px}
.sc-bar{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin:14px 0 10px}
.sc-bar .sp{flex:1}
.sc-tab{font:600 13px Inter,sans-serif;padding:7px 14px;border-radius:8px;border:1px solid var(--border2);background:var(--surface2);color:var(--muted);cursor:pointer}
.sc-tab.on{background:var(--accent);color:var(--accent-ink);border-color:transparent}
.mini{font:inherit;font-size:12.5px;padding:5px 11px;border-radius:7px;border:1px solid var(--border2);background:var(--surface2);color:var(--text);cursor:pointer}
.mini:hover{border-color:#3c4052}
.mini.on{background:var(--accent);color:var(--accent-ink);border-color:transparent}
.sc-sel{font:inherit;font-size:12.5px;background:var(--bg2);border:1px solid var(--border2);color:var(--text);border-radius:7px;padding:5px 9px;width:auto;margin:0;display:inline-block}

/* ---- runway summary ---- */
.sc-runway{display:grid;grid-template-columns:repeat(auto-fit,minmax(215px,1fr));gap:10px;margin:6px 0 16px}
.sc-rw{background:var(--surface);border:1px solid var(--border);border-left-width:3px;border-radius:10px;padding:10px 13px}
.sc-rw b{display:block;font-size:13px;margin-bottom:5px}
.sc-rw .n{font-size:21px;font-weight:800;line-height:1.1}
.sc-rw .n.ok{color:#5FD39A}.sc-rw .n.warn{color:#EF9F27}.sc-rw .n.dry{color:#E24B4A}
.sc-rw .sub{font-size:11.5px;color:var(--muted);margin-top:3px}

/* ---- the grid ---- */
.sc-scroll{overflow-x:auto;border:1px solid var(--border);border-radius:12px;background:var(--surface)}
.sc-grid{display:grid;min-width:max-content;font-size:12.5px}
.sc-cell{border-right:1px solid var(--border);border-bottom:1px solid var(--border);min-height:38px;padding:3px}
.sc-lbl{position:sticky;left:0;z-index:2;background:var(--surface2);border-right:1px solid var(--border2);
        padding:7px 11px;display:flex;flex-direction:column;justify-content:center;gap:2px}
.sc-lbl .p{font-weight:700;font-size:12.5px;display:flex;align-items:center;gap:6px}
.sc-lbl .p i{width:8px;height:8px;border-radius:2px;flex:none;font-style:normal}
.sc-lbl .l{font-size:11.5px;color:var(--muted);display:flex;align-items:center;gap:7px}
.sc-lbl .rw{font-size:10.5px;border-radius:999px;padding:0 7px;border:1px solid var(--border2);color:var(--muted)}
.sc-lbl .rw.ok{color:#5FD39A;border-color:#2e7d4f}
.sc-lbl .rw.warn{color:#EF9F27;border-color:#7a5b12}
.sc-lbl .rw.dry{color:#E24B4A;border-color:#6e2430}
.sc-mon{position:sticky;top:0;z-index:3;background:var(--bg2);border-right:1px solid var(--border);border-bottom:1px solid var(--border2);
        padding:5px 9px;font-weight:700;font-size:11.5px;color:var(--muted);white-space:nowrap}
.sc-wk{position:sticky;top:27px;z-index:3;background:var(--bg2);border-right:1px solid var(--border);border-bottom:1px solid var(--border2);
       padding:4px 6px;font:11px ui-monospace,Menlo,monospace;color:var(--muted2);text-align:center;white-space:nowrap}
.sc-wk.now{color:var(--accent);font-weight:700}
.sc-col-now{background:rgba(239,159,39,.07)}
.sc-col-past{background:rgba(0,0,0,.16)}
.sc-bar-item{border-radius:6px;padding:4px 8px;height:100%;min-height:32px;cursor:pointer;overflow:hidden;
             display:flex;flex-direction:column;justify-content:center;border-left:3px solid rgba(0,0,0,.35)}
.sc-bar-item .t{font-weight:600;font-size:12px;line-height:1.25;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#fff}
.sc-bar-item .a{font-size:10.5px;opacity:.8;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#fff}
.sc-bar-item.miss{background:repeating-linear-gradient(45deg,rgba(226,75,74,.16),rgba(226,75,74,.16) 6px,transparent 6px,transparent 12px);border-left-color:#E24B4A}
.sc-bar-item.miss .t{color:#f3a3a2;font-weight:500;font-style:italic}
.sc-add{width:100%;height:100%;min-height:32px;border:1px dashed transparent;border-radius:6px;background:transparent;
        color:var(--muted2);cursor:pointer;font-size:15px;opacity:0}
.sc-cell:hover .sc-add{opacity:1;border-color:var(--border2)}
.sc-gap .sc-add{opacity:.55;border-color:rgba(226,75,74,.3)}

/* ---- legend ---- */
.sc-legend{display:flex;gap:7px;flex-wrap:wrap;margin:12px 0 0}
.sc-lg{display:inline-flex;align-items:center;gap:6px;font-size:11.5px;color:var(--muted);border:1px solid var(--border);
       border-radius:999px;padding:3px 10px;cursor:pointer;user-select:none}
.sc-lg i{width:9px;height:9px;border-radius:2px;font-style:normal;flex:none}
.sc-lg.off{opacity:.35}

/* ---- backlog ---- */
.sc-backlog{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:14px 16px;margin-top:16px}
.sc-bl-list{display:flex;flex-wrap:wrap;gap:7px;margin-top:9px}
.sc-chip{display:inline-flex;align-items:center;gap:7px;border:1px solid var(--border2);border-radius:999px;
         padding:4px 11px;font-size:12px;cursor:grab;background:var(--surface2)}
.sc-chip i{width:8px;height:8px;border-radius:2px;font-style:normal;flex:none}
.sc-chip .p{color:var(--muted2);font-size:10.5px}

/* ---- syndication ---- */
.sc-syn{overflow-x:auto;border:1px solid var(--border);border-radius:12px;background:var(--surface)}
.sc-syn table{border-collapse:collapse;width:100%;font-size:12.5px}
.sc-syn th,.sc-syn td{border-bottom:1px solid var(--border);border-right:1px solid var(--border);padding:7px 10px;text-align:left;white-space:nowrap}
.sc-syn th{position:sticky;top:0;background:var(--bg2);font-size:11.5px;color:var(--muted);z-index:2}
.sc-syn th.rot{font-size:11px;max-width:130px;white-space:normal;line-height:1.2}
.sc-syn td.n{position:sticky;left:0;background:var(--surface2);font-weight:600;z-index:1}
.sc-syn td.c{text-align:center;cursor:pointer;font-size:13px;color:var(--muted2)}
.sc-syn td.c.on{color:#5FD39A}
.sc-syn td.c:hover{background:rgba(255,255,255,.04)}

/* ---- drawer ---- */
.sc-back{position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:40;display:none}
.sc-back.on{display:block}
.sc-draw{position:fixed;top:0;right:0;bottom:0;width:min(440px,100%);background:var(--surface);border-left:1px solid var(--border2);
         z-index:41;overflow-y:auto;padding:20px 22px 40px;transform:translateX(100%);transition:transform .16s ease}
.sc-draw.on{transform:none}
.sc-draw h3{margin:0 0 4px;font-size:16px}
.sc-draw .who{font-size:12px;color:var(--muted);margin-bottom:14px}
.sc-draw label{font-size:12px}
.sc-two{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.sc-msg{font-size:12.5px;margin-top:10px;min-height:17px}
.sc-msg.err{color:#f3a3a2}.sc-msg.ok{color:#5FD39A}
.sc-empty{padding:26px;text-align:center;color:var(--muted);font-size:13.5px}
</style>
</head>
<body>
<div class="topbar">
  <a class="brand" href="cc.php"><span class="dot"></span> Command Center</a>
  <a class="ghost" href="posting.php">🗓 Posting board</a>
  <a class="ghost" href="ops.php">📋 Ops</a>
  <span class="spacer"></span>
  <span class="ghost"><?= h($payload['user']) ?></span>
</div>

<div class="sc-wrap">
  <div class="pagehead">
    <h1>📅 Release schedule</h1>
    <div class="ghost">Plan the runway · <a class="ghost" href="posting.php" style="text-decoration:underline">posting board</a> fires the week</div>
  </div>

  <div class="sc-bar">
    <button class="sc-tab on" data-tab="cal">📅 Calendar</button>
    <button class="sc-tab" data-tab="syn">🔗 Syndication</button>
    <span class="sp"></span>
    <span id="sc-ctl-cal">
      <button class="mini" id="sc-prev">◀</button>
      <button class="mini" id="sc-today">Today</button>
      <button class="mini" id="sc-next">▶</button>
      <select class="sc-sel" id="sc-zoom">
        <option value="13">13 weeks</option>
        <option value="26" selected>26 weeks</option>
        <option value="52">52 weeks</option>
      </select>
      <select class="sc-sel" id="sc-prop"><option value="">All properties</option></select>
      <label style="display:inline-flex;align-items:center;gap:6px;margin:0;font-size:12.5px;color:var(--muted)">
        <input type="checkbox" id="sc-arch" style="width:auto;margin:0;display:inline-block"> archived
      </label>
    </span>
  </div>

  <div id="tab-cal">
    <div class="sc-runway" id="sc-runway"></div>
    <div class="sc-scroll" id="sc-scroll"><div class="sc-grid" id="sc-grid"></div></div>
    <div class="sc-legend" id="sc-legend"></div>
    <div class="sc-backlog">
      <h2 style="margin:0;font-size:14px">🎒 Backlog <span class="muted" style="font-size:12px">— in production, not yet scheduled. Drag onto a slot, or click to place.</span></h2>
      <div class="sc-bl-list" id="sc-backlog"></div>
    </div>
  </div>

  <div id="tab-syn" style="display:none">
    <div class="sc-syn" id="sc-syn"></div>
    <p class="muted" style="font-size:12px;margin-top:10px">
      Click a cell to flip it. This is the "where did it actually go" half — the publisher stage's
      <code>posted.json</code> carries the proof URLs per comic; this grid is the cross-property sweep.
    </p>
  </div>
</div>

<div class="sc-back" id="sc-back"></div>
<aside class="sc-draw" id="sc-draw" aria-hidden="true"></aside>

<script>
const SCHED = <?= json_encode($payload, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE) ?>;

const $ = (s, r) => (r || document).querySelector(s);
const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const MS_WEEK = 7 * 86400000;

function d2s(d) { return d.toISOString().slice(0, 10); }
function s2d(s) { return new Date(s + 'T00:00:00Z'); }
function addWeeks(s, n) { const d = s2d(s); d.setUTCDate(d.getUTCDate() + n * 7); return d2s(d); }
function weeksBetween(a, b) { return Math.round((s2d(b) - s2d(a)) / MS_WEEK); }
function monthLabel(s) { const d = s2d(s); return d.toLocaleDateString('en-US', { month: 'short', year: '2-digit', timeZone: 'UTC' }); }
function dayLabel(s) { const d = s2d(s); return d.toLocaleDateString('en-US', { month: 'numeric', day: 'numeric', timeZone: 'UTC' }); }

const state = {
  tab: 'cal',
  start: addWeeks(SCHED.thisWeek, -4),   // open on TODAY, with a little history behind it
  span: 26,
  prop: '',
  archived: false,
  hidden: new Set(),                     // stages toggled off in the legend
  dragId: null,
};

/* ------------------------------------------------------------------ helpers */
function laneRows() {
  const rows = [];
  for (const [pk, p] of Object.entries(SCHED.props)) {
    if (p.archived && !state.archived) continue;
    if (state.prop && pk !== state.prop) continue;
    for (const [lk, l] of Object.entries(SCHED.lanes)) {
      if (lk === 'side') continue;                       // side content is ad-hoc, not a cadence
      rows.push({ prop: pk, propName: p.name, color: p.color, lane: lk, laneName: l.short });
    }
  }
  return rows;
}
const scheduled = () => SCHED.items.filter(i => i.week && !state.hidden.has(i.stage));
const backlog = () => SCHED.items.filter(i => !i.week && i.stage !== 'posted' && i.stage !== 'missed');

function rowItems(prop, lane) {
  return scheduled().filter(i => i.property === prop && i.lane === lane)
                    .sort((a, b) => a.week < b.week ? -1 : 1);
}

// CK-RUNWAY-HORIZON v2 2026-08-23 — how far ahead this lane is actually booked:
// weeks from this week out to the last future slot that has not been missed, plus
// how many slots sit inside that stretch.
//
// v1 counted CONSECUTIVE weeks and stopped at the first empty one. That silently
// only worked for Fan Art Friday. The moment the board carried real forward data
// for the monthly and bi-weekly lanes (2026-08-23), seven of the nine lanes read
// "dry now" in red while being booked into 2027 — a weekly walk cannot measure a
// monthly cadence, because the gap between two monthly slots IS the cadence.
// A lane is dry when nothing is booked ahead, not when next week happens to be
// empty. `slots` is carried alongside so a lane booked far out but thinly (five
// monthly slots over five months) still reads differently from a dense one.
function runway(prop, lane) {
  let last = null, slots = 0;
  for (const it of SCHED.items) {
    if (it.property !== prop || it.lane !== lane || !it.week) continue;
    if (it.stage === 'missed') continue;
    const end = addWeeks(it.week, Math.max(1, it.weeks) - 1);
    if (end < SCHED.thisWeek) continue;      // already behind us
    slots++;
    if (last === null || end > last) last = end;
  }
  return { weeks: last === null ? 0 : Math.max(0, weeksBetween(SCHED.thisWeek, last)), slots: slots, last: last };
}
// Shared thresholds so the runway strip and the row chips can never disagree.
function runwayCls(n) { return n >= 8 ? 'ok' : (n >= 2 ? 'warn' : 'dry'); }

/* -------------------------------------------------------------- the calendar */
function renderRunway() {
  const el = $('#sc-runway');
  const rows = laneRows().filter(r => !SCHED.props[r.prop].archived);
  el.innerHTML = rows.map(r => {
    const rw = runway(r.prop, r.lane), n = rw.weeks;
    const cls = runwayCls(n);
    const word = rw.slots === 0 ? 'nothing booked'
      : `${rw.slots} slot${rw.slots === 1 ? '' : 's'} out to ${dayLabel(rw.last)}`;
    return `<div class="sc-rw" style="border-left-color:${esc(r.color)}">
      <b>${esc(r.propName)} <span class="muted">· ${esc(r.laneName)}</span></b>
      <div class="n ${cls}">${rw.slots === 0 ? '—' : n + 'w'}</div>
      <div class="sub">${esc(word)}</div>
    </div>`;
  }).join('') || '<div class="sc-empty">No lanes match this filter.</div>';
}

function renderGrid() {
  const grid = $('#sc-grid'), rows = laneRows();
  const weeks = [];
  for (let k = 0; k < state.span; k++) weeks.push(addWeeks(state.start, k));

  grid.style.gridTemplateColumns = `210px repeat(${weeks.length}, 128px)`;
  const now = SCHED.thisWeek;
  let html = '';

  // two sticky header rows: month bands, then week-start dates
  html += `<div class="sc-mon sc-lbl" style="top:0;z-index:4"></div>`;
  let m = null;
  for (const w of weeks) {
    const lbl = monthLabel(w);
    html += `<div class="sc-mon">${lbl !== m ? esc(lbl) : ''}</div>`;
    m = lbl;
  }
  html += `<div class="sc-wk sc-lbl" style="top:27px;z-index:4"></div>`;
  for (const w of weeks) {
    html += `<div class="sc-wk ${w === now ? 'now' : ''}">${w === now ? '▸ ' : ''}${esc(dayLabel(w))}</div>`;
  }

  for (const r of rows) {
    const rw = runway(r.prop, r.lane), n = rw.weeks;
    const cls = runwayCls(n);
    html += `<div class="sc-cell sc-lbl">
      <span class="p"><i style="background:${esc(r.color)}"></i>${esc(r.propName)}</span>
      <span class="l">${esc(r.laneName)} <span class="rw ${cls}" title="${rw.slots} slot${rw.slots === 1 ? '' : 's'} booked${rw.last ? ', last week beginning ' + esc(rw.last) : ''}">${rw.slots === 0 ? 'dry' : n + 'w'}</span></span>
    </div>`;

    const its = rowItems(r.prop, r.lane);
    let skip = 0;
    for (let ci = 0; ci < weeks.length; ci++) {
      if (skip > 0) { skip--; continue; }
      const w = weeks[ci];
      // an item starting here, or one whose span began before the window
      let it = its.find(x => x.week === w);
      let span = 1, clipped = false;
      if (!it && ci === 0) {
        it = its.find(x => x.week < w && weeksBetween(x.week, w) < x.weeks);
        if (it) { span = it.weeks - weeksBetween(it.week, w); clipped = true; }
      } else if (it) {
        span = it.weeks;
      }
      const colCls = w === now ? 'sc-col-now' : (w < now ? 'sc-col-past' : '');

      if (it) {
        span = Math.max(1, Math.min(span, weeks.length - ci));
        skip = span - 1;
        const st = SCHED.stages[it.stage] || { color: '#6F7380', label: it.stage };
        const miss = it.stage === 'missed';
        html += `<div class="sc-cell ${colCls}" style="grid-column:span ${span}">
          <div class="sc-bar-item ${miss ? 'miss' : ''}" data-id="${esc(it.id)}" draggable="true"
               style="${miss ? '' : `background:${esc(st.color)}22;border-left-color:${esc(st.color)}`}"
               title="${esc(it.title)}${it.artist ? ' — ' + esc(it.artist) : ''}\n${esc(st.label)}${clipped ? '\n(continues from earlier)' : ''}">
            <span class="t">${it.merged ? '▤ ' : ''}${esc(it.title)}</span>
            ${it.artist ? `<span class="a">${esc(it.artist)}</span>` : ''}
          </div></div>`;
      } else {
        const gap = w >= now;
        html += `<div class="sc-cell ${colCls} ${gap ? 'sc-gap' : ''}">
          <button class="sc-add" data-new="${esc(r.prop)}|${esc(r.lane)}|${esc(w)}">+</button>
        </div>`;
      }
    }
  }
  grid.innerHTML = html;
}

function renderLegend() {
  $('#sc-legend').innerHTML = Object.entries(SCHED.stages).map(([k, s]) =>
    `<span class="sc-lg ${state.hidden.has(k) ? 'off' : ''}" data-stage="${esc(k)}">
       <i style="background:${esc(s.color)}"></i>${esc(s.label)}</span>`).join('');
}

function renderBacklog() {
  const bl = backlog();
  $('#sc-backlog').innerHTML = bl.length ? bl.map(i => {
    const st = SCHED.stages[i.stage] || { color: '#6F7380' };
    const p = SCHED.props[i.property];
    return `<span class="sc-chip" draggable="true" data-id="${esc(i.id)}">
      <i style="background:${esc(st.color)}"></i>${esc(i.title)}
      ${p ? `<span class="p">${esc(p.name)}</span>` : ''}</span>`;
  }).join('') : '<span class="muted" style="font-size:12.5px">Nothing waiting — every in-production comic has a slot.</span>';
}

/* ------------------------------------------------------------- syndication */
function renderSynd() {
  const d = SCHED.synd;
  if (!d.rows.length) { $('#sc-syn').innerHTML = '<div class="sc-empty">No syndication rows yet.</div>'; return; }
  let h = '<table><thead><tr><th>Comic</th><th>Date</th><th>Property</th>' +
    d.destinations.map(x => `<th class="rot">${esc(x)}</th>`).join('') + '</tr></thead><tbody>';
  for (const r of [...d.rows].reverse()) {
    const p = SCHED.props[r.property];
    h += `<tr><td class="n">${esc(r.title)}</td><td>${esc(r.date || r.date_raw || '')}</td>
          <td>${p ? esc(p.name) : esc(r.property)}</td>` +
      d.destinations.map(x => {
        const on = (r.posted || {})[x] === 'posted';
        return `<td class="c ${on ? 'on' : ''}" data-row="${esc(r.id)}" data-dest="${esc(x)}">${on ? '●' : '○'}</td>`;
      }).join('') + '</tr>';
  }
  $('#sc-syn').innerHTML = h + '</tbody></table>';
}

/* ------------------------------------------------------------------ drawer */
function openDrawer(item, prefill) {
  const it = item || Object.assign({ id: '', title: '', artist: '', property: '', lane: '', slot: '', weeks: 1, stage: 'planning', notes: '' }, prefill || {});
  const opts = (obj, cur, blank) =>
    (blank ? `<option value="">${blank}</option>` : '') +
    Object.entries(obj).map(([k, v]) => `<option value="${esc(k)}" ${k === cur ? 'selected' : ''}>${esc(v.name || v.label)}</option>`).join('');

  $('#sc-draw').innerHTML = `
    <h3>${item ? 'Edit drop' : 'New drop'}</h3>
    <div class="who">${item ? esc(item.source || 'manual') : 'Lands on the posting board too — same record.'}</div>
    <label>Title<input type="text" id="f-title" value="${esc(it.title)}"></label>
    <label>Artist<input type="text" id="f-artist" value="${esc(it.artist)}" placeholder="who is drawing it"></label>
    <div class="sc-two">
      <label>Property<select id="f-prop">${opts(SCHED.props, it.property, '—')}</select></label>
      <label>Lane<select id="f-lane">${opts(SCHED.lanes, it.lane, '—')}</select></label>
    </div>
    <div class="sc-two">
      <label>Week of<input type="date" id="f-slot" value="${esc(it.slot)}"></label>
      <label>Runs for<input type="number" id="f-weeks" min="1" max="60" value="${esc(it.weeks || 1)}"></label>
    </div>
    <label>Stage<select id="f-stage">${opts(SCHED.stages, it.stage, '')}</select></label>
    <label>Notes<textarea id="f-notes" rows="3">${esc(it.notes)}</textarea></label>
    <div class="actions">
      <button class="btn primary" id="f-save">Save</button>
      ${item ? `<a class="btn" href="posting.php">Open board</a><button class="btn danger" id="f-del">Delete</button>` : ''}
      <button class="btn" id="f-cancel">Cancel</button>
    </div>
    <div class="sc-msg" id="f-msg"></div>`;

  $('#sc-draw').classList.add('on'); $('#sc-back').classList.add('on');
  $('#sc-draw').setAttribute('aria-hidden', 'false');
  setTimeout(() => $('#f-title').focus(), 60);

  $('#f-cancel').onclick = closeDrawer;
  $('#f-save').onclick = () => post('save', {
    id: it.id, title: $('#f-title').value, artist: $('#f-artist').value,
    property: $('#f-prop').value, lane: $('#f-lane').value, slot: $('#f-slot').value,
    weeks: $('#f-weeks').value, stage: $('#f-stage').value, notes: $('#f-notes').value,
  });
  if (item) $('#f-del').onclick = () => {
    if (confirm('Delete "' + it.title + '" from the schedule? This removes it from the posting board too.')) post('del', { id: it.id });
  };
}
function closeDrawer() {
  $('#sc-draw').classList.remove('on'); $('#sc-back').classList.remove('on');
  $('#sc-draw').setAttribute('aria-hidden', 'true');
}

/* ------------------------------------------------------------------- writes */
async function post(action, data, quiet) {
  const body = new URLSearchParams(Object.assign({ action }, SCHED.auth, data));
  const msg = $('#f-msg');
  try {
    const r = await fetch('schedule.php', { method: 'POST', body, headers: { 'X-CSRF': SCHED.auth.csrf || '' } });
    const j = await r.json();
    if (!j.ok) { if (msg) { msg.className = 'sc-msg err'; msg.textContent = j.error || 'Save failed.'; } else alert(j.error || 'Save failed.'); return false; }
    if (!quiet) location.reload();
    return true;
  } catch (e) {
    if (msg) { msg.className = 'sc-msg err'; msg.textContent = 'Network error — nothing was saved.'; } else alert('Network error.');
    return false;
  }
}

/* -------------------------------------------------------------------- wiring */
function renderAll() {
  if (state.tab === 'cal') { renderRunway(); renderGrid(); renderLegend(); renderBacklog(); }
  else renderSynd();
}

document.addEventListener('click', e => {
  const tab = e.target.closest('.sc-tab');
  if (tab) {
    state.tab = tab.dataset.tab;
    document.querySelectorAll('.sc-tab').forEach(t => t.classList.toggle('on', t === tab));
    $('#tab-cal').style.display = state.tab === 'cal' ? '' : 'none';
    $('#tab-syn').style.display = state.tab === 'syn' ? '' : 'none';
    $('#sc-ctl-cal').style.display = state.tab === 'cal' ? '' : 'none';
    renderAll(); return;
  }
  const bar = e.target.closest('.sc-bar-item');
  if (bar) { openDrawer(SCHED.items.find(i => i.id === bar.dataset.id)); return; }
  const add = e.target.closest('.sc-add');
  if (add) {
    const [prop, lane, slot] = add.dataset.new.split('|');
    openDrawer(null, { property: prop, lane, slot }); return;
  }
  const chip = e.target.closest('.sc-chip');
  if (chip) { openDrawer(SCHED.items.find(i => i.id === chip.dataset.id)); return; }
  const lg = e.target.closest('.sc-lg');
  if (lg) {
    const k = lg.dataset.stage;
    state.hidden.has(k) ? state.hidden.delete(k) : state.hidden.add(k);
    renderAll(); return;
  }
  const cell = e.target.closest('.sc-syn td.c');
  if (cell) {
    const on = cell.classList.contains('on');
    post('synd', { id: cell.dataset.row, dest: cell.dataset.dest, state: on ? '' : 'posted' }, true).then(ok => {
      if (ok) {
        cell.classList.toggle('on', !on); cell.textContent = on ? '○' : '●';
        const row = SCHED.synd.rows.find(r => r.id === cell.dataset.row);
        if (row) { row.posted = row.posted || {}; row.posted[cell.dataset.dest] = on ? '' : 'posted'; }
      }
    });
    return;
  }
  if (e.target.id === 'sc-back') closeDrawer();
});

$('#sc-prev').onclick = () => { state.start = addWeeks(state.start, -Math.round(state.span / 2)); renderAll(); };
$('#sc-next').onclick = () => { state.start = addWeeks(state.start, Math.round(state.span / 2)); renderAll(); };
$('#sc-today').onclick = () => { state.start = addWeeks(SCHED.thisWeek, -4); renderAll(); $('#sc-scroll').scrollLeft = 0; };
$('#sc-zoom').onchange = e => { state.span = parseInt(e.target.value, 10) || 26; renderAll(); };
$('#sc-prop').onchange = e => { state.prop = e.target.value; renderAll(); };
$('#sc-arch').onchange = e => { state.archived = e.target.checked; renderAll(); };
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeDrawer(); });

// drag a bar or a backlog chip onto a slot
document.addEventListener('dragstart', e => {
  const src = e.target.closest('.sc-bar-item, .sc-chip');
  if (src) { state.dragId = src.dataset.id; e.dataTransfer.effectAllowed = 'move'; }
});
document.addEventListener('dragover', e => { if (state.dragId && e.target.closest('.sc-cell')) e.preventDefault(); });
document.addEventListener('drop', e => {
  const cell = e.target.closest('.sc-cell');
  if (!cell || !state.dragId) return;
  const add = cell.querySelector('.sc-add');
  if (!add) return;                               // only drop onto an empty slot
  e.preventDefault();
  const [prop, lane, slot] = add.dataset.new.split('|');
  post('move', { id: state.dragId, property: prop, lane, slot });
  state.dragId = null;
});

for (const [k, p] of Object.entries(SCHED.props)) {
  if (p.archived) continue;
  $('#sc-prop').insertAdjacentHTML('beforeend', `<option value="${esc(k)}">${esc(p.name)}</option>`);
}
renderAll();
</script>
</body></html>
