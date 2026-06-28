<?php
// review.php — FULL-WIDTH chapter review surface for the Comic Creator.
//
// The cockpit (creator.php) keeps a 340px references column + a sticky run bar, so when the
// owner just wants to REVIEW a chapter's generated panels the images get squeezed into a narrow
// column — "scrolling one tiny image at a time." This page drops both: it lays out EVERY panel
// in a justified full-width grid IN STORY ORDER (by beat number), with sorts (story / newest)
// and filters (notes / approval / rating / flagged defects), keeps the per-panel ✓/✕/★/💬
// controls, and on click opens a per-panel DETAIL showing the larger image + the PROMPT it was
// built from + the REFERENCES used + that panel's notes + rating/approval. (Owner notes Beat 2 /
// Beat 4 / Beat 81 + feedback_comic_stage_refs_and_realism point 5.)
//
// Pure renderer in the refs.php / shots.php mold: it reuses api.php (winner/rate/keep) for the
// rating controls and writes panel notes to the SAME creator-<id>.json feedback log the cockpit
// reads (do=note here, no reshoot side-effect — a review note is an annotation, not a run
// command). Depends only on inc/boot.php helpers. Prompt + refs_used come from image metadata
// captured at ingest (bridge.php) / the Flow auto-sync; legacy panels show an honest "not
// recorded" state until a re-sync backfills them.
declare(strict_types=1);
require_once __DIR__ . '/inc/boot.php';
require_auth();

$id   = preg_replace('/[^a-z0-9-]/', '', (string)($_GET['p'] ?? ''));
$proj = $id !== '' ? project_get($id) : null;
if (!$proj) { header('Location: creator.php'); exit; }          // unknown / no project -> creator index
$cfile = SDATA . '/creator-' . $id . '.json';

// ---- note endpoint (JSON): append a panel-targeted annotation to the feedback log ----
// Same log the cockpit shows, but NO reshoot enqueue — review notes are diagnostic annotations.
if ($_SERVER['REQUEST_METHOD'] === 'POST' && ($_POST['do'] ?? '') === 'note') {
    header('Content-Type: application/json');
    if (!csrf_ok()) { echo json_encode(['ok' => false, 'error' => 'Bad token — reload.']); exit; }
    $txt  = trim((string)($_POST['text'] ?? ''));
    $beat = mb_substr(trim((string)($_POST['panel'] ?? '')), 0, 60);
    if ($txt === '') { echo json_encode(['ok' => false, 'error' => 'Empty note.']); exit; }
    $note = ['ts' => date('c'), 'by' => current_studio_user(), 'panel' => $beat, 'text' => mb_substr($txt, 0, 2000)];
    s_with_lock($cfile, function ($cc) use ($note) {
        if (!is_array($cc)) $cc = [];
        $cc['feedback'] = $cc['feedback'] ?? [];
        array_unshift($cc['feedback'], $note);
        return ['data' => $cc, 'result' => true];
    });
    echo json_encode(['ok' => true, 'note' => $note]);
    exit;
}

// ---- ping endpoint (JSON): lightweight liveness signal for the live auto-refresh ----
// Read-only. The review board polls this so newly Auto-Synced panels surface a "+N new" toast
// without a manual reload. Returns just the panel count + newest import ts (cheap to diff).
if (($_GET['do'] ?? '') === 'ping') {
    header('Content-Type: application/json');
    $pp = array_filter(images_all($id), fn($m) => empty($m['isref']));
    $cnt = count($pp); $newest = 0;
    foreach ($pp as $m) { $t = (int)($m['ts'] ?? 0); if ($t > $newest) $newest = $t; }
    echo json_encode(['ok' => true, 'count' => $cnt, 'newest' => $newest]);
    exit;
}

$c       = is_file($cfile) ? s_read($cfile, []) : [];
$gallery = images_all($id);
$panels  = array_values(array_filter($gallery, fn($m) => empty($m['isref'])));   // refs are tagged isref

// story order: by beat number, then import time. A flat justified grid (not grouped boxes).
$beatNum = fn($s) => preg_match('/(\d+)/', (string)$s, $m) ? (int)$m[1] : 999999;
usort($panels, function ($a, $b) use ($beatNum) {
    return ($beatNum($a['group'] ?? '') <=> $beatNum($b['group'] ?? ''))
        ?: (((int)($a['ts'] ?? 0)) <=> ((int)($b['ts'] ?? 0)))
        ?: strcmp((string)($a['file'] ?? ''), (string)($b['file'] ?? ''));
});

// lookups for resolving refs_used + notes (self-contained; no creator.php-only helpers)
$refByFile = []; foreach (($c['refs'] ?? []) as $r) { $f = (string)($r['file'] ?? ''); if ($f !== '') $refByFile[$f] = $r; }
$galFiles  = []; foreach ($gallery as $m) { $f = (string)($m['file'] ?? ''); if ($f !== '') $galFiles[$f] = true; }
$notesByBeat = []; foreach (($c['feedback'] ?? []) as $fb) { $p = (string)($fb['panel'] ?? ''); if ($p !== '') $notesByBeat[$p][] = $fb; }

$imgUrl = fn($f, $thumb = false) => 'img.php?p=' . urlencode($id) . '&f=' . urlencode($f) . ($thumb ? '&t=1' : '');

// newest panel (so it's always spottable, the owner's "can't tell what's newest" pain)
$newestTs = 0; $newestFile = '';
foreach ($panels as $im) { $t = (int)($im['ts'] ?? 0); if ($t > $newestTs) { $newestTs = $t; $newestFile = (string)$im['file']; } }

// per-panel detail payload (embedded once; the overlay reads from it — no server round-trip)
$detail = [];
$galN = count($panels); $accN = 0; $noPromptN = 0; $defectN = 0; $noteTotal = 0;
foreach ($panels as $im) {
    $f = (string)$im['file'];
    if (!empty($im['accepted'])) $accN++;
    if (empty($im['prompt'])) $noPromptN++;
    $beat = (string)($im['group'] ?? '');

    $rused = [];
    foreach ((array)($im['refs_used'] ?? []) as $ru) {
        if (!is_array($ru)) continue;
        $entry = ['label' => (string)($ru['label'] ?? ''), 'kind' => (string)($ru['kind'] ?? ''), 'src' => (string)($ru['src'] ?? '')];
        $rf = (string)($ru['file'] ?? '');
        if ($rf !== '' && isset($galFiles[$rf])) {                       // a studio-resident ref -> renderable thumbnail
            $entry['thumb'] = $imgUrl($rf, true);
            $entry['full']  = $imgUrl($rf);
            if (isset($refByFile[$rf])) { $rr = $refByFile[$rf];
                if ($entry['label'] === '') $entry['label'] = (string)($rr['label'] ?: ($rr['char'] ?? ''));
                if ($entry['kind']  === '') $entry['kind']  = (string)($rr['kind'] ?? '');
            }
        }
        if (!empty($ru['url']) && preg_match('#^https?://#i', (string)$ru['url'])) $entry['url'] = (string)$ru['url'];  // Flow input ref -> external link (re-validate scheme: defense-in-depth vs any future refs_used writer)
        $rused[] = $entry;
    }

    $notes = [];
    foreach ($notesByBeat[$beat] ?? [] as $n) $notes[] = ['text' => (string)($n['text'] ?? ''), 'by' => (string)($n['by'] ?? ''), 'ts' => (string)($n['ts'] ?? '')];
    $noteTotal += count($notes);
    $an = $im['analysis'] ?? [];
    $defects = array_values(array_filter(array_map('strval', (array)($an['defects'] ?? [])), 'strlen'));
    if ($defects) $defectN++;

    $detail[$f] = [
        'beat'     => $beat,
        'rating'   => (string)($im['rating'] ?? 'unrated'),
        'accepted' => !empty($im['accepted']),
        'ver'      => (int)($im['ver'] ?? 1),
        'derived'  => !empty($im['parent']),
        'adjust'   => (string)($im['adjust'] ?? ''),
        'prompt'   => (string)($im['prompt'] ?? ''),
        'gen'      => (string)($im['gen'] ?? ''),
        'orig'     => (string)($im['orig'] ?? ''),
        'full'     => $imgUrl($f),
        'refs'     => $rused,
        'notes'    => $notes,
        'defects'  => $defects,
        'caption'  => (string)($an['caption'] ?? ''),
        'tier'     => (string)($an['tier'] ?? ''),
        'newest'   => ($f === $newestFile),
    ];
}
$pname = (string)($proj['name'] ?? $id);
?><!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><meta name="color-scheme" content="dark">
<meta name="robots" content="noindex,nofollow"><title><?= h($pname) ?> · Review</title>
<link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="assets/studio.css?v=<?= @filemtime(STUDIO_ROOT . '/assets/studio.css') ?>">
<style>
.rv-wrap{max-width:1760px;margin:0 auto;padding:16px 22px 90px}
.rv-head{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;margin:4px 0 12px}
.rv-head h1{font-size:20px;margin:0}
.rv-head .sub{color:var(--muted);font-size:13px}
/* sticky toolbar: sorts + filters + size */
.rv-bar{position:sticky;top:56px;z-index:20;background:rgba(11,12,16,.92);backdrop-filter:blur(6px);border:1px solid var(--border2);border-radius:12px;padding:9px 12px;margin-bottom:16px;display:flex;align-items:center;gap:14px;flex-wrap:wrap}
.rv-grp{display:flex;align-items:center;gap:6px}
.rv-grp>.lab{font-size:10.5px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted2);margin-right:1px}
.rv-seg{display:inline-flex;border:1px solid var(--border2);border-radius:8px;overflow:hidden}
.rv-seg button{border:0;background:var(--surface2);color:var(--muted);font:600 12px/1 Inter,sans-serif;padding:7px 11px;cursor:pointer}
.rv-seg button+button{border-left:1px solid var(--border2)}
.rv-seg button.on{background:var(--accent);color:var(--accent-ink)}
.rv-seg button:hover:not(.on){color:var(--text)}
.rv-tog{border:1px solid var(--border2);background:var(--surface2);color:var(--muted);font:600 12px/1 Inter,sans-serif;padding:7px 11px;border-radius:8px;cursor:pointer}
.rv-tog.on{background:#3a2d5e;color:#cdb6ff;border-color:#4a3d6e}
.rv-tog:hover:not(.on){color:var(--text)}
.rv-spacer{flex:1}
.rv-count{font-size:12px;color:var(--muted)}
.rv-count b{color:var(--text)}
/* backfill nudge */
.rv-nudge{background:rgba(239,159,39,.09);border:1px solid #7a5a1f;color:#fac775;border-radius:10px;padding:9px 13px;font-size:12.5px;margin-bottom:14px}
.rv-nudge b{color:#ffd591}
/* the grid */
.rv-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(var(--tile,200px),1fr));gap:11px}
.rv-tile{position:relative;border:1px solid var(--border2);border-radius:10px;overflow:hidden;background:var(--bg2);cursor:pointer;aspect-ratio:4/5}
.rv-tile img{width:100%;height:100%;object-fit:cover;display:block;transition:transform .18s ease}
.rv-grid.fit .rv-tile img{object-fit:contain;background:#07080b}
.rv-tile:hover img{transform:scale(1.03)}
.rv-tile.rate-good{border-color:var(--teal)}
.rv-tile.rate-bad{border-color:var(--red)}
.rv-tile.rate-bad img{opacity:.5}
.rv-tile.kept{box-shadow:inset 0 0 0 2px var(--accent)}
.rv-beat{position:absolute;top:6px;left:6px;background:rgba(8,9,12,.82);color:#cfd3dc;font:700 10.5px/1 Inter,sans-serif;padding:3px 7px;border-radius:999px;letter-spacing:.02em}
.rv-vbadge{position:absolute;top:6px;right:6px;background:#3a2d5e;color:#cdb6ff;font:800 10px/1 Inter,sans-serif;padding:3px 6px;border-radius:999px}
.rv-new{position:absolute;top:6px;right:6px;background:var(--teal);color:#04130d;font:800 9.5px/1 Inter,sans-serif;padding:3px 7px;border-radius:999px;letter-spacing:.04em}
.rv-flags{position:absolute;bottom:34px;left:6px;display:flex;gap:4px}
.rv-flag{font-size:11px;background:rgba(8,9,12,.8);border-radius:6px;padding:2px 5px;line-height:1.3}
.rv-flag.def{color:#f3a3a2}.rv-flag.note{color:#cdb6ff}
.rv-okmark{position:absolute;bottom:34px;right:6px;background:var(--teal);color:#04130d;font:800 11px/1 Inter,sans-serif;width:20px;height:20px;border-radius:50%;display:none;align-items:center;justify-content:center}
.rv-tile.kept .rv-okmark{display:flex}
/* quick rate bar (hover) */
.rv-qbar{position:absolute;left:0;right:0;bottom:0;display:flex;background:rgba(8,9,12,.86);opacity:0;transition:opacity .15s ease}
.rv-tile:hover .rv-qbar,.rv-tile:focus-within .rv-qbar{opacity:1}
.rv-qbar button{flex:1;border:0;background:transparent;color:#cfd3dc;font-size:13px;padding:6px 0;cursor:pointer}
.rv-qbar button:hover{background:rgba(255,255,255,.08)}
.rv-qbar .qb-approve:hover{color:#6fe0bd}.rv-qbar .qb-bad:hover{color:#f3a3a2}.rv-qbar .qb-keep:hover{color:var(--accent)}
.rv-empty{border:1px dashed var(--border2);border-radius:12px;padding:40px;text-align:center;color:var(--muted)}
.rv-hidden{display:none!important}
/* ---- detail overlay ---- */
.rv-lb{position:fixed;inset:0;z-index:90;background:rgba(6,7,10,.95);display:none}
.rv-lb.open{display:flex}
.rv-lb-stage{flex:1;min-width:0;display:flex;align-items:center;justify-content:center;position:relative;padding:18px}
.rv-lb-stage img{max-width:100%;max-height:100%;object-fit:contain;border-radius:8px}
.rv-arrow{position:absolute;top:50%;transform:translateY(-50%);background:rgba(20,21,28,.85);border:1px solid var(--border2);color:#fff;font-size:26px;width:44px;height:54px;border-radius:10px;cursor:pointer;display:flex;align-items:center;justify-content:center}
.rv-arrow.prev{left:14px}.rv-arrow.next{right:14px}
.rv-arrow:disabled{opacity:.25;cursor:default}
.rv-info{width:380px;flex:none;background:var(--surface);border-left:1px solid var(--border);padding:18px 20px;overflow-y:auto;display:flex;flex-direction:column;gap:14px}
@media(max-width:820px){.rv-lb{flex-direction:column}.rv-info{width:auto;border-left:0;border-top:1px solid var(--border);max-height:48vh}}
.rv-info h2{font-size:15px;margin:0}
.rv-x{position:absolute;top:14px;right:14px;z-index:2;background:rgba(20,21,28,.9);border:1px solid var(--border2);color:#fff;font-size:15px;width:36px;height:36px;border-radius:8px;cursor:pointer}
.rv-meta{display:flex;align-items:center;gap:8px;flex-wrap:wrap;font-size:12px;color:var(--muted)}
.rv-chip{font:700 10.5px/1 Inter,sans-serif;padding:3px 8px;border-radius:999px}
.rv-chip.beat{background:var(--surface2);color:#cfd3dc}
.rv-chip.good{background:rgba(29,158,117,.18);color:#6fe0bd}
.rv-chip.bad{background:rgba(226,75,74,.18);color:#f3a3a2}
.rv-chip.kept{background:var(--accent);color:var(--accent-ink)}
.rv-chip.ver{background:#3a2d5e;color:#cdb6ff}
.rv-ctrls{display:flex;gap:7px;flex-wrap:wrap}
.rv-ctrls button{flex:1;min-width:64px;border:1px solid var(--border2);background:var(--surface2);color:var(--text);font:600 12.5px/1 Inter,sans-serif;padding:9px 6px;border-radius:8px;cursor:pointer}
.rv-ctrls button:hover{border-color:#3c4052}
.rv-ctrls .d-approve.on{background:var(--teal);color:#04130d;border-color:transparent}
.rv-ctrls .d-bad.on{background:var(--red);color:#fff;border-color:transparent}
.rv-ctrls .d-keep.on{background:var(--accent);color:var(--accent-ink);border-color:transparent}
.rv-sec h3{font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted2);margin:0 0 6px;display:flex;align-items:center;gap:7px}
.rv-sec h3 .mini{background:var(--surface2);color:var(--muted);border:0;font:600 10.5px/1 Inter,sans-serif;padding:3px 7px;border-radius:6px;cursor:pointer}
.rv-prompt{background:var(--bg2);border:1px solid var(--border);border-radius:9px;padding:10px 12px;font:13px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace;color:#dfe2ea;white-space:pre-wrap;word-break:break-word;max-height:230px;overflow:auto}
.rv-prompt.empty{font-family:Inter,sans-serif;color:var(--muted);font-style:italic}
/* structured prompt: surface the SCENE prominently, push style/quality boilerplate to the background */
.rv-prompt.scene{font:14px/1.55 Inter,system-ui,sans-serif;color:#eef0f5}
.rv-prompt-cam{display:flex;gap:8px;align-items:baseline;margin-top:8px;font:13px/1.5 Inter,sans-serif;color:#cdd2dd}
.rv-prompt-cam .lab{flex:none;font:700 9.5px/1 Inter,sans-serif;text-transform:uppercase;letter-spacing:.05em;color:var(--muted2);background:var(--surface2);padding:4px 7px;border-radius:6px}
.rv-prompt-dlg{margin-bottom:8px;border-left:3px solid var(--accent);background:rgba(122,127,236,.08);border-radius:0 8px 8px 0;padding:7px 11px;color:#e8eaf2}
.rv-prompt-dlg .lab{display:block;font:700 9px/1 Inter,sans-serif;text-transform:uppercase;letter-spacing:.05em;color:var(--muted2);margin-bottom:5px}
.rv-prompt-dlg .ln{display:block;margin:3px 0;font:13.5px/1.45 Inter,sans-serif}
.rv-prompt-dlg .ln:before{content:"“"}.rv-prompt-dlg .ln:after{content:"”"}
.rv-prompt-meta{margin-top:9px;display:flex;flex-direction:column;gap:4px;font:11.5px/1.45 Inter,sans-serif;color:var(--muted)}
.rv-prompt-meta .mk{font:700 8.5px/1 Inter,sans-serif;text-transform:uppercase;letter-spacing:.05em;color:var(--muted2);margin-right:6px;vertical-align:1px}
.rv-refs{display:grid;grid-template-columns:repeat(auto-fill,minmax(74px,1fr));gap:8px}
.rv-ref{border:1px solid var(--border2);border-radius:8px;overflow:hidden;background:var(--bg2);text-decoration:none;color:var(--text);display:block}
.rv-ref img{width:100%;aspect-ratio:1;object-fit:cover;display:block}
.rv-ref .rl{padding:4px 5px;font-size:9.5px;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.rv-ref .rk{display:inline-block;font:800 8px/1 Inter,sans-serif;padding:1px 4px;border-radius:4px;color:#0b0c10;margin-right:3px;vertical-align:middle}
.rv-refchip{display:flex;align-items:center;gap:6px;border:1px solid var(--border2);border-radius:8px;padding:7px 9px;background:var(--bg2);font-size:11.5px;color:#cfd3dc;text-decoration:none}
.rv-refchip:hover{border-color:#3c4052}
.rv-note{border-left:2px solid var(--border2);padding:2px 0 2px 9px;margin-bottom:8px}
.rv-note .nt{font-size:12.5px;color:#e2e4ea;white-space:pre-wrap}
.rv-note .nm{font-size:10.5px;color:var(--muted2);margin-top:2px}
.rv-def{display:inline-block;background:rgba(226,75,74,.14);color:#f3a3a2;font-size:11px;border-radius:6px;padding:3px 8px;margin:0 5px 5px 0}
.rv-notebox{display:flex;flex-direction:column;gap:7px}
.rv-notebox textarea{background:var(--bg2);border:1px solid var(--border2);color:var(--text);border-radius:8px;padding:8px 10px;font:13px Inter,sans-serif;resize:vertical;min-height:46px}
.rv-notebox .row{display:flex;gap:7px;align-items:center}
.rv-muted{color:var(--muted);font-size:12px}
.rv-link{color:#9aa0ec;font-size:12px;text-decoration:none}.rv-link:hover{text-decoration:underline}
/* --- added: focus ring, live-refresh toast, fresh markers, sibling filmstrip, lightbox zoom --- */
.rv-tile:focus{outline:2px solid var(--accent);outline-offset:2px}
.rv-toast{position:fixed;left:50%;bottom:22px;transform:translateX(-50%) translateY(20px);z-index:120;background:var(--teal);color:#04130d;font:800 13px/1 Inter,sans-serif;padding:11px 16px;border-radius:999px;box-shadow:0 6px 20px rgba(0,0,0,.4);cursor:pointer;opacity:0;transition:opacity .2s ease,transform .2s ease;display:flex;align-items:center;gap:10px}
.rv-toast.show{opacity:1;transform:translateX(-50%) translateY(0)}
.rv-toast .x{opacity:.6}
.rv-tile.fresh::after{content:'';position:absolute;top:8px;right:8px;width:10px;height:10px;border-radius:50%;background:var(--teal);box-shadow:0 0 0 2px rgba(8,9,12,.85);z-index:4}
.rv-sibs{display:flex;gap:7px;flex-wrap:wrap}
.rv-sib{position:relative;border:1px solid var(--border2);border-radius:7px;overflow:hidden;width:58px;height:72px;cursor:pointer;background:var(--bg2);padding:0}
.rv-sib img{width:100%;height:100%;object-fit:cover;display:block}
.rv-sib.cur{outline:2px solid var(--accent);outline-offset:-2px}
.rv-sib.kept{outline:2px solid var(--teal);outline-offset:-2px}
.rv-sib .vb{position:absolute;top:2px;left:2px;background:rgba(8,9,12,.82);color:#cfd3dc;font:800 8px/1 Inter,sans-serif;padding:2px 4px;border-radius:4px}
.rv-sib .ok{position:absolute;bottom:2px;right:2px;background:var(--teal);color:#04130d;font:800 9px/1 Inter,sans-serif;width:14px;height:14px;border-radius:50%;display:flex;align-items:center;justify-content:center}
#lbimg{cursor:zoom-in}
#lbimg.zoomed{max-width:none;max-height:none;width:auto;height:auto;cursor:zoom-out}
.rv-lb-stage.zoomed-stage{overflow:auto;align-items:flex-start;justify-content:flex-start}
.rv-lb-stage.zoomed-stage .rv-arrow{display:none}
</style></head><body>
<header class="topbar" style="border-bottom:2px solid #7A7FEC">
  <div class="brand"><span class="dot"></span> Comic Studio
    <span style="background:#7A7FEC;color:#0B0C10;font-size:11px;font-weight:800;letter-spacing:.04em;border-radius:999px;padding:2px 9px;margin-left:6px">🖼 REVIEW</span></div>
  <a class="ghost" href="creator.php?p=<?= h(urlencode($id)) ?>">← Cockpit</a>
  <a class="ghost" href="shots.php?p=<?= h(urlencode($id)) ?>">📋 Production guide</a>
  <span class="spacer"></span>
  <span class="ghost"><?= h(current_studio_user()) ?></span>
  <a class="ghost" href="help.php">❔ How it works</a>
  <a class="ghost" href="login.php?do=logout">Log out</a>
</header>

<main class="rv-wrap" id="rv" data-id="<?= h($id) ?>" data-csrf="<?= h(csrf()) ?>" data-count="<?= $galN ?>" data-newest="<?= $newestTs ?>">
  <div class="rv-head">
    <h1><?= h($pname) ?> — review</h1>
    <span class="sub">whole chapter, full width, in story order · click any panel for the prompt + references that built it · keys: A approve, D bad, K keep, N next-unrated</span>
  </div>

  <?php if ($galN && $noPromptN === $galN): ?>
  <div class="rv-nudge">⚠ <b>No prompts recorded yet</b> for these <?= $galN ?> panels (imported before prompt capture). Open this project in <b>Google Flow</b> and hit <b>Sync now</b> in the Auto-Sync panel — it backfills each panel's prompt + the references used, then they show up here.</div>
  <?php elseif ($noPromptN > 0): ?>
  <div class="rv-nudge"><b><?= $noPromptN ?></b> of <?= $galN ?> panels have no recorded prompt. Re-run the Flow <b>Auto-Sync (Sync now)</b> to backfill their prompts + references.</div>
  <?php endif; ?>

  <div class="rv-bar">
    <div class="rv-grp"><span class="lab">Sort</span>
      <span class="rv-seg" id="sortseg">
        <button data-sort="story" class="on">Story order</button>
        <button data-sort="newest">Newest</button>
      </span>
    </div>
    <div class="rv-grp"><span class="lab">Approval</span>
      <span class="rv-seg" id="apprseg">
        <button data-appr="all" class="on">All</button>
        <button data-appr="yes">Approved</button>
        <button data-appr="no">Not</button>
      </span>
    </div>
    <div class="rv-grp"><span class="lab">Rating</span>
      <span class="rv-seg" id="rateseg">
        <button data-rate="all" class="on">All</button>
        <button data-rate="good">Good</button>
        <button data-rate="bad">Bad</button>
        <button data-rate="unrated">Unrated</button>
      </span>
    </div>
    <button class="rv-tog" id="tognotes" data-f="notes">💬 Has notes</button>
    <button class="rv-tog" id="togdef" data-f="defects">⚑ Flagged defects</button>
    <span class="rv-spacer"></span>
    <span class="rv-count" id="rvcount"><b><?= $galN ?></b> panels · <b><?= $accN ?></b> approved</span>
    <div class="rv-grp"><span class="lab">Size</span>
      <span class="rv-seg" id="sizeseg">
        <button data-size="150">S</button>
        <button data-size="200" class="on">M</button>
        <button data-size="290">L</button>
      </span>
    </div>
    <button class="rv-tog" id="togfit" title="Fit whole image (no crop)">⛶ Fit</button>
    <button class="rv-tog" id="rvrefresh" title="Reload to pick up new panels">↻ Refresh</button>
  </div>

  <?php if (!$galN): ?>
    <div class="rv-empty">No panels yet. Import from Flow (the ⚙ Auto-Sync extension) or queue a run — generated panels land here in story order.</div>
  <?php else: ?>
  <div class="rv-grid" id="grid" style="--tile:200px">
    <?php foreach ($panels as $i => $im): $f = (string)$im['file']; $d = $detail[$f];
          $rt = $d['rating']; $kp = $d['accepted']; $nN = count($d['notes']); $dN = count($d['defects']); ?>
    <figure class="rv-tile rate-<?= h($rt) ?><?= $kp ? ' kept' : '' ?>"
            data-file="<?= h($f) ?>" data-idx="<?= $i ?>" data-ts="<?= (int)($im['ts'] ?? 0) ?>"
            data-rating="<?= h($rt) ?>" data-accepted="<?= $kp ? '1' : '0' ?>"
            data-notes="<?= $nN ?>" data-defects="<?= $dN ?>"
            data-hasprompt="<?= $d['prompt'] !== '' ? '1' : '0' ?>" data-hasrefs="<?= $d['refs'] ? '1' : '0' ?>"
            tabindex="0">
      <span class="rv-beat"><?= h($d['beat'] !== '' ? $d['beat'] : '—') ?></span>
      <?php if ($d['newest']): ?><span class="rv-new">NEW</span>
      <?php elseif ($d['derived']): ?><span class="rv-vbadge">v<?= (int)$d['ver'] ?></span><?php endif; ?>
      <img loading="lazy" src="<?= h($imgUrl($f, true)) ?>" alt="">
      <div class="rv-flags">
        <?php if ($dN): ?><span class="rv-flag def" title="flagged defects">⚑ <?= $dN ?></span><?php endif; ?>
        <?php if ($nN): ?><span class="rv-flag note" title="notes">💬 <?= $nN ?></span><?php endif; ?>
      </div>
      <span class="rv-okmark" title="approved + kept">✓</span>
      <div class="rv-qbar">
        <button type="button" class="qb-approve" data-act="approve" title="Approve — winner of this beat">✓</button>
        <button type="button" class="qb-bad" data-act="disapprove" title="Disapprove">✕</button>
        <button type="button" class="qb-keep" data-act="keep" title="Keep">★</button>
        <button type="button" class="qb-note" data-act="note" title="Open + add a note">💬</button>
      </div>
    </figure>
    <?php endforeach; ?>
  </div>
  <div class="rv-empty rv-hidden" id="nonematch">No panels match these filters. <a class="rv-link" href="javascript:void(0)" id="clearfilters">Clear filters</a></div>
  <?php endif; ?>
</main>

<!-- per-panel detail overlay -->
<div class="rv-lb" id="lb">
  <button class="rv-x" id="lbx" title="Close (Esc)">✕</button>
  <div class="rv-lb-stage">
    <button class="rv-arrow prev" id="lbprev" title="Previous (←)">‹</button>
    <img id="lbimg" src="" alt="">
    <button class="rv-arrow next" id="lbnext" title="Next (→)">›</button>
  </div>
  <aside class="rv-info" id="lbinfo"></aside>
</div>

<script id="detaildata" type="application/json"><?= json_encode($detail, JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT | JSON_UNESCAPED_UNICODE | JSON_INVALID_UTF8_SUBSTITUTE) ?: '{}' ?></script>
<script>
(function(){
  var root = document.getElementById('rv'); if(!root) return;
  var PID = root.dataset.id, CSRF = root.dataset.csrf;
  var DATA = {}; try { DATA = JSON.parse(document.getElementById('detaildata').textContent || '{}'); } catch(e){}
  var grid = document.getElementById('grid');
  var KIND_COLOR = {face:'#EF9F27',body:'#5DCAA5',view:'#7A7FEC',scene:'#378ADD',prop:'#D85A30'};

  function tiles(){ return [].slice.call(grid ? grid.querySelectorAll('.rv-tile') : []); }
  function el(tag, cls, txt){ var e=document.createElement(tag); if(cls) e.className=cls; if(txt!=null) e.textContent=txt; return e; }

  // ---------- sort + filter (client-side; the grid holds every panel) ----------
  var state = { sort:'story', appr:'all', rate:'all', notes:false, defects:false };
  function applySort(){
    if(!grid) return;
    var t = tiles();
    t.sort(function(a,b){
      if(state.sort==='newest') return (+b.dataset.ts) - (+a.dataset.ts) || (+a.dataset.idx) - (+b.dataset.idx);
      return (+a.dataset.idx) - (+b.dataset.idx);   // story order = the PHP render order
    });
    t.forEach(function(x){ grid.appendChild(x); });   // re-append in new order
  }
  function applyFilter(){
    var shown = 0;
    tiles().forEach(function(x){
      var ok = true;
      if(state.appr==='yes' && x.dataset.accepted!=='1') ok=false;
      if(state.appr==='no'  && x.dataset.accepted==='1') ok=false;
      if(state.rate==='good' && x.dataset.rating!=='good') ok=false;
      if(state.rate==='bad'  && x.dataset.rating!=='bad')  ok=false;
      if(state.rate==='unrated' && x.dataset.rating!=='unrated') ok=false;
      if(state.notes   && (+x.dataset.notes)<1)   ok=false;
      if(state.defects && (+x.dataset.defects)<1) ok=false;
      x.classList.toggle('rv-hidden', !ok);
      if(ok) shown++;
    });
    var none = document.getElementById('nonematch');
    if(none) none.classList.toggle('rv-hidden', shown>0 || tiles().length===0);
    var cnt = document.getElementById('rvcount');
    var acc = tiles().filter(function(x){ return x.dataset.accepted==='1'; }).length;
    if(cnt) cnt.innerHTML = '<b>'+shown+'</b>'+(shown!==tiles().length?(' / '+tiles().length):'')+' panels · <b>'+acc+'</b> approved';
  }
  function seg(id, key, after){
    var box = document.getElementById(id); if(!box) return;
    box.addEventListener('click', function(e){ var b=e.target.closest('button'); if(!b) return;
      [].forEach.call(box.querySelectorAll('button'), function(x){ x.classList.remove('on'); });
      b.classList.add('on'); state[key]=b.dataset[Object.keys(b.dataset)[0]]; after && after(b); writeHash();
    });
  }
  seg('sortseg','sort', applySort);
  seg('apprseg','appr', applyFilter);
  seg('rateseg','rate', applyFilter);
  seg('sizeseg','size', function(b){ grid.style.setProperty('--tile', b.dataset.size+'px'); });
  function tog(id, key, render){ var b=document.getElementById(id); if(!b) return;
    b.addEventListener('click', function(){ b.classList.toggle('on'); state[key]=b.classList.contains('on'); render(); writeHash(); }); }
  tog('tognotes','notes', applyFilter);
  tog('togdef','defects', applyFilter);
  var fitBtn=document.getElementById('togfit');
  if(fitBtn) fitBtn.addEventListener('click', function(){ fitBtn.classList.toggle('on'); grid.classList.toggle('fit', fitBtn.classList.contains('on')); writeHash(); });
  var rf=document.getElementById('rvrefresh'); if(rf) rf.addEventListener('click', function(){ location.reload(); });
  var cf=document.getElementById('clearfilters'); if(cf) cf.addEventListener('click', function(){
    state.appr='all'; state.rate='all'; state.notes=false; state.defects=false;
    ['apprseg','rateseg'].forEach(function(id){ var box=document.getElementById(id); if(box){ [].forEach.call(box.querySelectorAll('button'),function(x){x.classList.remove('on');}); box.querySelector('button').classList.add('on'); }});
    ['tognotes','togdef'].forEach(function(id){ var b=document.getElementById(id); if(b) b.classList.remove('on'); });
    applyFilter();
  });

  // ---------- rating mutations (reuse api.php, same as the cockpit board) ----------
  async function api(action, file, extra){
    var body = new URLSearchParams(Object.assign({p:PID, action:action, file:file, csrf:CSRF}, extra||{}));
    var r = await fetch('api.php', {method:'POST', body:body, headers:{'X-CSRF':CSRF}});
    return r.json();
  }
  function tileOf(file){ return grid ? grid.querySelector('.rv-tile[data-file="'+(window.CSS&&CSS.escape?CSS.escape(file):file)+'"]') : null; }
  function setRating(file, rating){
    var d=DATA[file]; if(d) d.rating=rating;
    var t=tileOf(file); if(t){ t.dataset.rating=rating; t.classList.remove('rate-good','rate-bad','rate-unrated'); t.classList.add('rate-'+rating); }
  }
  function setKeep(file, kept){
    var d=DATA[file]; if(d) d.accepted=kept;
    var t=tileOf(file); if(t){ t.dataset.accepted=kept?'1':'0'; t.classList.toggle('kept', kept); }
  }
  function doApprove(file){      // winner: this becomes good+kept; beat siblings lose accept + any 'good' (mirror api.php)
    api('winner', file).then(function(j){ if(!j||!j.ok) return;
      var beat = DATA[file] && DATA[file].beat;
      setRating(file,'good'); setKeep(file,true);
      if(beat){ Object.keys(DATA).forEach(function(k){ if(k!==file && DATA[k].beat===beat){ setKeep(k,false); if(DATA[k].rating==='good') setRating(k,'unrated'); } }); }
      applyFilter(); syncDetail(file);
    });
  }
  function doBad(file){ api('rate', file, {rating:'bad'}).then(function(j){ if(j&&j.ok){ setRating(file,'bad'); applyFilter(); syncDetail(file); }}); }
  function doKeep(file){ var d=DATA[file]; var next=!(d&&d.accepted); api('keep', file, {accepted:next?'1':'0'}).then(function(j){ if(j&&j.ok){ setKeep(file,next); applyFilter(); syncDetail(file); }}); }

  // quick bar on tiles
  if(grid) grid.addEventListener('click', function(e){
    var btn = e.target.closest('.rv-qbar button');
    if(btn){ e.stopPropagation(); var file=btn.closest('.rv-tile').dataset.file, act=btn.dataset.act;
      if(act==='approve') doApprove(file);
      else if(act==='disapprove') doBad(file);
      else if(act==='keep') doKeep(file);
      else if(act==='note') openLb(file, true);
      return;
    }
    var tile = e.target.closest('.rv-tile'); if(tile) openLb(tile.dataset.file, false);
  });
  if(grid) grid.addEventListener('keydown', function(e){
    var tile = e.target.closest('.rv-tile'); if(!tile) return;
    var f=tile.dataset.file, k=(e.key||'').toLowerCase();
    if(e.key==='Enter'||e.key===' '){ e.preventDefault(); openLb(f, false); }
    else if(k==='a'||k==='g'){ e.preventDefault(); doApprove(f); }
    else if(k==='d'||k==='b'){ e.preventDefault(); doBad(f); }
    else if(k==='k'){ e.preventDefault(); doKeep(f); }
    else if(k==='n'){ e.preventDefault(); focusNextUnrated(tile); }
  });

  // ---------- detail overlay ----------
  var lb=document.getElementById('lb'), lbimg=document.getElementById('lbimg'), lbinfo=document.getElementById('lbinfo'),
      lbprev=document.getElementById('lbprev'), lbnext=document.getElementById('lbnext');
  var curFile=null;
  function visibleOrder(){ return tiles().filter(function(x){ return !x.classList.contains('rv-hidden'); }).map(function(x){ return x.dataset.file; }); }
  function copyBtn(label, text){ var b=el('button','mini',label); b.type='button';
    b.addEventListener('click', function(){ function ok(){ var o=b.textContent; b.textContent='✓ copied'; setTimeout(function(){ b.textContent=o; },1300); }
      if(navigator.clipboard&&navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(ok, function(){ window.prompt('Copy:', text); }); else window.prompt('Copy:', text); });
    return b; }

  // ---------- prompt parsing (display only — copy/storage always use the RAW prompt) ----------
  // Generated prompts follow a consistent template: STYLE preamble · CAMERA/shot · SCENE/action (+ dialogue) ·
  // QUALITY suffix. We surface the SCENE prominently, give the shot its own line, pull dialogue/lettering out,
  // and de-emphasize the repeated style + quality boilerplate. Off-template prompts (Flow-imported / hand-written
  // in other projects) don't start with a style preamble — those fall back to the RAW prompt, unchanged.
  var STYLE_VOCAB = ['photoreal','3d cgi','daz3d','iray','cinematic lighting','high detail','single comic panel','octane','unreal','hyperreal','cgi render'];
  var CAM_VOCAB = ['shot','two-shot','over-the-shoulder','over the shoulder','pov','angle','eye level','eye-level','low angle','high angle','overhead','bird','dutch','wide','medium','close-up','close up','closeup','ecu','extreme close','establishing','framed','framing','looking down','looking up'];
  var QUAL_VOCAB = ['realistic skin','skin texture','readable expression','facial expression','cohesive comic panel','layered depth','sense of motion','sharp focus','high resolution','night tones','blue tones','warm tones','golden tones','color grade','color grading','depth of field','bokeh','soft focus'];
  function hasVocab(s, vocab){ s=s.toLowerCase(); for(var i=0;i<vocab.length;i++){ if(s.indexOf(vocab[i])>=0) return true; } return false; }
  function splitSentences(text){
    var out=[], buf='', straight=false, curly=0;
    function flushIfBreak(i){
      var j=i+1;
      while(j<text.length && (text[j]==='.'||text[j]==='!'||text[j]==='?'||text[j]==='”'||text[j]==='"')){
        buf+=text[j];
        if(text[j]==='"') straight=!straight; else if(text[j]==='”'){ if(curly>0) curly--; }
        i=j; j++;
      }
      if(j>=text.length || /\s/.test(text[j])){ var s=buf.trim(); if(s) out.push(s); buf=''; }
      return i;
    }
    for(var i=0;i<text.length;i++){
      var ch=text[i]; buf+=ch;
      var prevInQuote=(straight||curly>0);
      if(ch==='"') straight=!straight; else if(ch==='“') curly++; else if(ch==='”'){ if(curly>0) curly--; }
      var nowInQuote=(straight||curly>0);
      var isTerm=(ch==='.'||ch==='!'||ch==='?');
      if(isTerm && !nowInQuote){ i=flushIfBreak(i); }
      else if(prevInQuote && !nowInQuote){                 // a quote just closed — break if its last char was a terminator
        var before=buf.length>=2?buf[buf.length-2]:'';
        if(before==='.'||before==='!'||before==='?') i=flushIfBreak(i);
      }
    }
    if(buf.trim()) out.push(buf.trim());
    return out;
  }
  function wordCount(s){ return (s.trim().match(/\S+/g)||[]).length; }
  function extractDialogue(text){
    if(!/bubble|caption|lettering|\btext\b|\bsfx\b|sign reading|banner|\bsays\b|\breads\b/i.test(text)) return [];
    var lines=[], re=/[“"]([^“”"]{1,240})[”"]/g, m, seen={};
    while((m=re.exec(text))){ var t=m[1].trim(); if(t && /[a-z0-9]/i.test(t) && !seen[t]){ seen[t]=1; lines.push(t); } }
    return lines;
  }
  function parsePrompt(text){
    var sents=splitSentences(text);
    if(!sents.length || !hasVocab(sents[0], STYLE_VOCAB)) return {templated:false};   // no style preamble -> raw
    var i=0, style=[]; while(i<sents.length && hasVocab(sents[i], STYLE_VOCAB)){ style.push(sents[i]); i++; }
    var j=sents.length-1, quality=[]; while(j>=i && hasVocab(sents[j], QUAL_VOCAB)){ quality.unshift(sents[j]); j--; }
    var camera=''; if(i<=j && hasVocab(sents[i], CAM_VOCAB) && wordCount(sents[i])<=14){ camera=sents[i]; i++; }
    var scene=sents.slice(i, j+1).join(' ').trim();
    if(!scene) return {templated:false};                                              // nothing left to surface -> raw
    return {templated:true, style:style.join(' '), camera:camera, scene:scene, quality:quality.join(' '), dialogue:extractDialogue(text)};
  }
  // Render the prompt body into `ps`: structured sections when the template matches, RAW box otherwise.
  // `ph` is the section <h3> — we hang the "raw" power-user toggle off it next to the copy button.
  function renderPromptBody(ps, raw, ph){
    var parsed=parsePrompt(raw);
    if(!parsed.templated){ var pp=el('div','rv-prompt'); pp.textContent=raw; ps.appendChild(pp); return; }
    var box=el('div'); box.className='rv-prompt-struct';
    if(parsed.dialogue && parsed.dialogue.length){
      var dl=el('div','rv-prompt-dlg'); dl.appendChild(el('span','lab','Dialogue / lettering'));
      parsed.dialogue.forEach(function(t){ dl.appendChild(el('span','ln', t)); });
      box.appendChild(dl);
    }
    var sc=el('div','rv-prompt scene'); sc.textContent=parsed.scene; box.appendChild(sc);
    if(parsed.camera){ var cam=el('div','rv-prompt-cam'); cam.appendChild(el('span','lab','Camera')); cam.appendChild(el('span',null,parsed.camera)); box.appendChild(cam); }
    if(parsed.style || parsed.quality){
      var meta=el('div','rv-prompt-meta');
      if(parsed.style){ var st=el('div'); st.appendChild(el('span','mk','Style')); st.appendChild(document.createTextNode(parsed.style)); meta.appendChild(st); }
      if(parsed.quality){ var qu=el('div'); qu.appendChild(el('span','mk','Quality')); qu.appendChild(document.createTextNode(parsed.quality)); meta.appendChild(qu); }
      box.appendChild(meta);
    }
    ps.appendChild(box);
    var rawBox=null, rawOn=false, tg=el('button','mini','raw'); tg.type='button';
    tg.addEventListener('click', function(){
      rawOn=!rawOn;
      if(rawOn){ if(!rawBox){ rawBox=el('div','rv-prompt'); rawBox.textContent=raw; ps.appendChild(rawBox); } rawBox.style.display=''; box.style.display='none'; tg.textContent='structured'; }
      else { if(rawBox) rawBox.style.display='none'; box.style.display=''; tg.textContent='raw'; }
    });
    ph.appendChild(tg);
  }

  function buildInfo(file){
    var d = DATA[file]; lbinfo.innerHTML=''; if(!d) return;
    // header: beat + version + status chips
    var meta = el('div','rv-meta');
    meta.appendChild(el('span','rv-chip beat', d.beat||'—'));
    if(d.derived) meta.appendChild(el('span','rv-chip ver','v'+d.ver));
    if(d.rating==='good') meta.appendChild(el('span','rv-chip good','approved'));
    else if(d.rating==='bad') meta.appendChild(el('span','rv-chip bad','disapproved'));
    if(d.accepted) meta.appendChild(el('span','rv-chip kept','★ kept'));
    if(d.newest) meta.appendChild(el('span','rv-chip good','newest'));
    lbinfo.appendChild(meta);
    if(d.adjust){ var aj=el('div','rv-muted','✎ '+d.adjust); lbinfo.appendChild(aj); }

    // rating controls
    var ctr=el('div','rv-ctrls');
    var ba=el('button','d-approve'+(d.rating==='good'&&d.accepted?' on':''),'✓ Approve'); ba.type='button';
    var bd=el('button','d-bad'+(d.rating==='bad'?' on':''),'✕ Disapprove'); bd.type='button';
    var bk=el('button','d-keep'+(d.accepted?' on':''),'★ Keep'); bk.type='button';
    ba.addEventListener('click',function(){ doApprove(file); });
    bd.addEventListener('click',function(){ doBad(file); });
    bk.addEventListener('click',function(){ doKeep(file); });
    ctr.appendChild(ba); ctr.appendChild(bd); ctr.appendChild(bk);
    lbinfo.appendChild(ctr);

    // OTHER TAKES for this beat — winner-pick filmstrip (only when the beat has >1 candidate)
    var sibs = siblingsOf(file);
    if(sibs.length>1){
      var ss=el('div','rv-sec'); ss.appendChild(el('h3',null,'Other takes for this beat ('+sibs.length+')'));
      var strip=el('div','rv-sibs');
      sibs.forEach(function(sf){ var sd=DATA[sf]; if(!sd) return;
        var b=el('button','rv-sib'+(sf===file?' cur':'')+(sd.accepted?' kept':'')); b.type='button';
        b.title=(sd.beat||'')+(sd.derived?(' · v'+sd.ver):'')+(sd.accepted?' · kept':'')+(sd.rating==='good'?' · approved':'')+(sd.rating==='bad'?' · disapproved':'');
        var im=el('img'); im.src='img.php?p='+encodeURIComponent(PID)+'&f='+encodeURIComponent(sf)+'&t=1'; im.loading='lazy'; im.alt=''; b.appendChild(im);
        if(sd.derived){ b.appendChild(el('span','vb','v'+sd.ver)); }
        if(sd.accepted){ b.appendChild(el('span','ok','✓')); }
        b.addEventListener('click', function(){ if(sf!==curFile) openLb(sf, false); });
        strip.appendChild(b);
      });
      ss.appendChild(strip); lbinfo.appendChild(ss);
    }

    // PROMPT (always shown) — structured display; ⧉ copy + stored value always use the RAW prompt verbatim
    var ps=el('div','rv-sec'); var ph=el('h3'); ph.appendChild(document.createTextNode('Prompt'));
    if(d.prompt){ ph.appendChild(copyBtn('⧉ copy', d.prompt)); }
    ps.appendChild(ph);
    if(d.prompt){ renderPromptBody(ps, d.prompt, ph); }
    else { var pe=el('div','rv-prompt empty','Prompt not recorded for this panel — it was generated before prompt capture. Re-run the Flow Auto-Sync (Sync now) to backfill it.'); ps.appendChild(pe); }
    lbinfo.appendChild(ps);

    // REFERENCES USED
    var rs=el('div','rv-sec'); rs.appendChild(el('h3',null,'References used'));
    function refChip(r){
      var node = r.url ? el('a','rv-refchip') : el('div','rv-refchip'); if(r.url){ node.href=r.url; node.target='_blank'; node.rel='noopener noreferrer'; }
      node.textContent = (r.kind?('['+r.kind+'] '):'') + (r.label||'ref') + (r.src?(' · '+r.src):'') + (r.url?' ↗':'');
      return node;
    }
    if(d.refs && d.refs.length){
      var thumbs = d.refs.filter(function(r){ return r.thumb || r.url; });
      var chips  = d.refs.filter(function(r){ return !(r.thumb || r.url); });
      if(thumbs.length){ var g=el('div','rv-refs');
        thumbs.forEach(function(r){
          var ttl = (r.label||'ref') + (r.src?(' · '+r.src):'');
          var href = r.full || r.url;
          var a = href ? el('a','rv-ref') : el('div','rv-ref'); if(href){ a.href=href; a.target='_blank'; a.rel='noopener noreferrer'; }
          a.title = ttl;
          var im=el('img'); im.src=r.thumb || r.url; im.loading='lazy'; im.alt=ttl;
          im.onerror=function(){ if(a.parentNode) a.parentNode.removeChild(a); rs.appendChild(refChip(r)); };
          a.appendChild(im);
          var lab=el('div','rl'); if(r.kind){ var k=el('span','rk'); k.textContent=r.kind; k.style.background=KIND_COLOR[r.kind]||'#9CA0AC'; lab.appendChild(k); } lab.appendChild(document.createTextNode(r.label||r.kind||'ref')); a.appendChild(lab);
          g.appendChild(a);
        }); rs.appendChild(g);
      }
      chips.forEach(function(r){ rs.appendChild(refChip(r)); });
    } else {
      rs.appendChild(el('div','rv-muted','References used not recorded for this panel.'));
    }
    lbinfo.appendChild(rs);

    // DEFECTS (from the QA scan)
    if(d.defects && d.defects.length){ var ds=el('div','rv-sec'); ds.appendChild(el('h3',null,'⚑ Flagged defects'));
      d.defects.forEach(function(x){ ds.appendChild(el('span','rv-def', x)); }); lbinfo.appendChild(ds); }
    if(d.caption||d.tier){ var cs=el('div','rv-sec'); cs.appendChild(el('h3',null,'Analysis'));
      if(d.tier) cs.appendChild(el('div','rv-muted','tier: '+d.tier));
      if(d.caption) cs.appendChild(el('div','rv-muted', d.caption)); lbinfo.appendChild(cs); }

    // NOTES
    var ns=el('div','rv-sec'); ns.appendChild(el('h3',null,'Notes ('+(d.notes?d.notes.length:0)+')'));
    var nlist=el('div'); nlist.id='lbnotes';
    renderNotes(nlist, d.notes);
    ns.appendChild(nlist);
    var nb=el('div','rv-notebox');
    var ta=el('textarea'); ta.placeholder='Add a note on this panel — e.g. “shirt drifted gray→white”, “face too muscular, wrong stage ref”. Saved to the feedback log.'; ta.id='lbnotetext';
    var row=el('div','row'); var send=el('button','btn primary','Add note'); send.type='button';
    var hint=el('span','rv-muted',''); hint.id='lbnotehint';
    send.addEventListener('click', function(){ submitNote(file, ta, hint); });
    ta.addEventListener('keydown', function(e){ if((e.metaKey||e.ctrlKey)&&e.key==='Enter') submitNote(file, ta, hint); });
    row.appendChild(send); row.appendChild(hint); nb.appendChild(ta); nb.appendChild(row);
    ns.appendChild(nb);
    lbinfo.appendChild(ns);

    var link=el('a','rv-link','✎ Refine this image in the cockpit →'); link.href='creator.php?p='+encodeURIComponent(PID); lbinfo.appendChild(link);
  }
  function renderNotes(container, notes){
    container.innerHTML='';
    if(!notes || !notes.length){ container.appendChild(el('div','rv-muted','No notes on this panel yet.')); return; }
    notes.forEach(function(n){ var w=el('div','rv-note'); w.appendChild(el('div','nt', n.text||''));
      var when=''; try{ if(n.ts){ when=new Date(n.ts).toLocaleString(); } }catch(e){}
      w.appendChild(el('div','nm', [n.by, when].filter(Boolean).join(' · '))); container.appendChild(w); });
  }
  function submitNote(file, ta, hint){
    var txt=(ta.value||'').trim(); if(!txt){ ta.focus(); return; }
    var d=DATA[file]; var beat=d?d.beat:'';
    hint.textContent='saving…';
    fetch('review.php?p='+encodeURIComponent(PID), {method:'POST', headers:{'X-CSRF':CSRF},
        body:new URLSearchParams({p:PID, do:'note', panel:beat, text:txt, csrf:CSRF})})
      .then(function(r){ return r.json(); })
      .then(function(j){ if(j&&j.ok){ d.notes=d.notes||[]; d.notes.unshift({text:j.note.text, by:j.note.by, ts:j.note.ts});
          ta.value=''; hint.textContent='✓ added';
          renderNotes(document.getElementById('lbnotes'), d.notes);
          var t=tileOf(file); if(t){ t.dataset.notes=String(d.notes.length); var fl=t.querySelector('.rv-flags'); if(fl){ var nf=fl.querySelector('.note'); if(!nf){ nf=el('span','rv-flag note'); fl.appendChild(nf); } nf.textContent='💬 '+d.notes.length; } }
          // update the "Notes (N)" heading
          [].forEach.call(lbinfo.querySelectorAll('.rv-sec h3'), function(x){ if(/^Notes \(/.test(x.textContent)) x.textContent='Notes ('+d.notes.length+')'; });
          setTimeout(function(){ hint.textContent=''; }, 1400);
        } else { hint.textContent=(j&&j.error)||'failed'; } })
      .catch(function(){ hint.textContent='failed'; });
  }
  function syncDetail(file){ if(lb.classList.contains('open') && curFile===file) buildInfo(file); }

  function openLb(file, focusNote){
    curFile=file; var d=DATA[file]; if(!d) return;
    lbimg.classList.remove('zoomed'); if(lbimg.parentNode) lbimg.parentNode.classList.remove('zoomed-stage');
    lbimg.src=d.full; lbimg.alt=d.orig||'';
    buildInfo(file);
    var order=visibleOrder(); var pos=order.indexOf(file);
    lbprev.disabled = pos<=0; lbnext.disabled = pos<0 || pos>=order.length-1;
    lb.classList.add('open');
    if(focusNote){ var ta=document.getElementById('lbnotetext'); if(ta){ ta.scrollIntoView({block:'center'}); ta.focus(); } }
  }
  function closeLb(){ lb.classList.remove('open'); curFile=null; lbimg.src=''; }
  function step(dir){ var order=visibleOrder(); var i=order.indexOf(curFile); if(i<0) return; var n=i+dir; if(n<0||n>=order.length) return; openLb(order[n], false); }
  document.getElementById('lbx').addEventListener('click', closeLb);
  lbprev.addEventListener('click', function(){ step(-1); });
  lbnext.addEventListener('click', function(){ step(1); });
  lbimg.addEventListener('click', function(e){ e.stopPropagation(); var z=!lbimg.classList.contains('zoomed'); lbimg.classList.toggle('zoomed', z); if(lbimg.parentNode) lbimg.parentNode.classList.toggle('zoomed-stage', z); });
  lb.addEventListener('click', function(e){ if(e.target===lb || e.target.classList.contains('rv-lb-stage')) closeLb(); });
  document.addEventListener('keydown', function(e){
    if(!lb.classList.contains('open')) return;
    var typing = document.activeElement && document.activeElement.tagName==='TEXTAREA';
    if(e.key==='Escape'){ if(typing){ document.activeElement.blur(); } else closeLb(); }
    else if(typing) return;
    else if(e.key==='ArrowLeft') step(-1);
    else if(e.key==='ArrowRight') step(1);
    else if(e.key==='a'||e.key==='A'||e.key==='g'||e.key==='G'){ if(curFile) doApprove(curFile); }
    else if(e.key==='d'||e.key==='D'||e.key==='b'||e.key==='B'){ if(curFile) doBad(curFile); }
    else if(e.key==='k'||e.key==='K'){ if(curFile) doKeep(curFile); }
    else if(e.key==='n'||e.key==='N'){ stepUnrated(); }
  });
  // ====== view-state persistence (URL hash) — shareable + survives the live-refresh reload ======
  function setSeg(id, val){ var box=document.getElementById(id); if(!box) return;
    [].forEach.call(box.querySelectorAll('button'), function(x){ var dv=x.dataset[Object.keys(x.dataset)[0]]; x.classList.toggle('on', dv===String(val)); }); }
  function setTog(id, on){ var b=document.getElementById(id); if(b) b.classList.toggle('on', !!on); }
  function writeHash(){
    var p=[];
    if(state.sort!=='story') p.push('sort='+state.sort);
    if(state.appr!=='all') p.push('appr='+state.appr);
    if(state.rate!=='all') p.push('rate='+state.rate);
    if(state.notes) p.push('notes=1');
    if(state.defects) p.push('defects=1');
    var sz=grid?parseInt(grid.style.getPropertyValue('--tile'),10):0; if(sz && sz!==200) p.push('size='+sz);
    if(grid && grid.classList.contains('fit')) p.push('fit=1');
    try{ history.replaceState(null,'', p.length?('#'+p.join('&')):(location.pathname+location.search)); }catch(e){}
  }
  function readHash(){
    var h=(location.hash||'').replace(/^#/,''); if(!h) return;
    var q={}; h.split('&').forEach(function(kv){ var i=kv.indexOf('='); if(i>0) q[kv.slice(0,i)]=decodeURIComponent(kv.slice(i+1)); });
    if(q.sort){ state.sort=q.sort; setSeg('sortseg',q.sort); }
    if(q.appr){ state.appr=q.appr; setSeg('apprseg',q.appr); }
    if(q.rate){ state.rate=q.rate; setSeg('rateseg',q.rate); }
    state.notes=q.notes==='1'; setTog('tognotes',state.notes);
    state.defects=q.defects==='1'; setTog('togdef',state.defects);
    if(q.size && grid){ var sb=document.querySelector('#sizeseg button[data-size="'+q.size+'"]'); if(sb){ setSeg('sizeseg',q.size); grid.style.setProperty('--tile', q.size+'px'); } }
    if(q.fit==='1' && grid){ var fb=document.getElementById('togfit'); if(fb) fb.classList.add('on'); grid.classList.add('fit'); }
  }
  // ====== winner-pick: siblings (other takes) of a beat ======
  function siblingsOf(file){ var d=DATA[file]; var beat=d&&d.beat; if(!beat) return [file];
    return tiles().filter(function(t){ var dd=DATA[t.dataset.file]; return dd && dd.beat===beat; }).map(function(t){ return t.dataset.file; }); }
  // ====== triage: jump to next UNRATED ======
  function focusNextUnrated(fromTile){
    var vis=tiles().filter(function(x){ return !x.classList.contains('rv-hidden'); });
    var start=fromTile?vis.indexOf(fromTile):-1, i;
    for(i=start+1;i<vis.length;i++){ if(vis[i].dataset.rating==='unrated'){ vis[i].focus(); vis[i].scrollIntoView({block:'center',behavior:'smooth'}); return; } }
    for(i=0;i<=start;i++){ if(vis[i].dataset.rating==='unrated'){ vis[i].focus(); vis[i].scrollIntoView({block:'center',behavior:'smooth'}); return; } }
  }
  function stepUnrated(){ var order=visibleOrder(); var i=order.indexOf(curFile), n;
    for(n=i+1;n<order.length;n++){ if(DATA[order[n]] && DATA[order[n]].rating==='unrated'){ openLb(order[n], false); return; } }
    for(n=0;n<=i;n++){ if(DATA[order[n]] && DATA[order[n]].rating==='unrated'){ openLb(order[n], false); return; } }
  }
  // ====== live auto-refresh: poll ping; toast when new panels land ======
  var INIT_COUNT=+root.dataset.count||0, INIT_NEWEST=+root.dataset.newest||0, toastEl=null;
  function showToast(delta){
    if(!toastEl){ toastEl=el('div','rv-toast'); var t=el('span'); toastEl._txt=t; toastEl.appendChild(t);
      var x=el('span','x','✕');
      toastEl.addEventListener('click', function(e){ if(e.target===x){ toastEl.classList.remove('show'); return; }
        try{ sessionStorage.setItem('rvscroll-'+PID, String(window.scrollY||window.pageYOffset||0)); }catch(_){}
        location.reload(); });
      toastEl.appendChild(x); document.body.appendChild(toastEl);
    }
    toastEl._txt.textContent='+'+delta+' new panel'+(delta===1?'':'s')+' — show';
    toastEl.classList.add('show');
  }
  function poll(){
    fetch('review.php?p='+encodeURIComponent(PID)+'&do=ping', {headers:{'X-Requested-With':'fetch'}})
      .then(function(r){ return r.json(); })
      .then(function(j){ if(j&&j.ok){ var delta=(j.count|0)-INIT_COUNT; if(delta>0 || (j.newest|0)>INIT_NEWEST) showToast(delta>0?delta:1); } })
      .catch(function(){});
  }
  // ====== "new since last visit" markers ======
  function markFresh(){
    try{ var k='rvseen-'+PID, last=+localStorage.getItem(k)||0;
      if(last>0){ tiles().forEach(function(t){ if((+t.dataset.ts)>last && !t.querySelector('.rv-new') && !t.querySelector('.rv-vbadge')) t.classList.add('fresh'); }); }
      localStorage.setItem(k, String(INIT_NEWEST||0));
    }catch(_){}
  }
  function restoreScroll(){ try{ if('scrollRestoration' in history) history.scrollRestoration='manual'; var k='rvscroll-'+PID, v=sessionStorage.getItem(k); if(v){ sessionStorage.removeItem(k); window.scrollTo(0, +v); } }catch(_){} }
  // ====== init ======
  readHash(); applySort(); applyFilter(); markFresh(); restoreScroll();
  if(grid) setInterval(poll, 25000);
})();
</script>
</body></html>
