<?php
// studio/post/index.php — 📤 Posting Wizard: a clean, one-thing-at-a-time flow
// for queueing content onto the posting board. Built for Alternate (posting/ops)
// so he never has to see the comic-GENERATION side of the studio.
//
// This page FORKS NO LOGIC: every write goes through ../posting.php's existing
// form-POST API (add / update / upload / plat / del) and the data is the same
// data/posting.json the board renders. The only server-side work here is
// read-only: list items for the "pick" step and refresh after a save.
//
// Publishing stays HUMAN-FIRED. The wizard prepares + queues; a person presses
// post on the actual platforms and marks them posted on the board.
//
// Auth: the shared studio session (same logins as posting.php) OR the bridge
// key (headless QA), exactly like posting.php.
declare(strict_types=1);
require_once dirname(__DIR__) . '/inc/boot.php';

// boot.php's s_boot() scopes the session cookie to dirname(SCRIPT_NAME), which
// here would be /studio/post — a DIFFERENT cookie than the /studio one the rest
// of the studio (and login.php) uses. Start the session pinned to /studio first
// so an existing studio login just works; s_boot() then sees it and no-ops.
if (session_status() === PHP_SESSION_NONE) {
    session_name('mgstudio');
    session_set_cookie_params(['lifetime' => 0, 'path' => '/studio', 'httponly' => true, 'samesite' => 'Lax',
        'secure' => (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off')]);
    session_start();
}

define('PO_FILE', SDATA . '/posting.json');

// Mirrors posting.php's vocab — keep in sync with the board.
$PLATFORMS = array('site' => 'Site', 'patreon' => 'Patreon', 'deviantart' => 'DeviantArt', 'twitter' => 'X', 'instagram' => 'IG');
$LANES = array('faf' => 'Fan Art Friday', 'comic' => 'Monthly comic', 'side' => 'Side content');

$SITES = s_read(SDATA . '/cc-sites.json', array());
$PROPS = array();
foreach (array('growgetter', 'maxxmuscle', 'bloombeauty') as $pk) {
    if (isset($SITES[$pk])) $PROPS[$pk] = array('name' => (string)$SITES[$pk]['name'], 'color' => (string)$SITES[$pk]['color']);
}

function pw_bridge_ok(): bool {
    $cfg = s_read(SDATA . '/bridge.json', array());
    $key = (string)(isset($cfg['key']) ? $cfg['key'] : '');
    $given = (string)(isset($_POST['key']) ? $_POST['key'] : (isset($_GET['key']) ? $_GET['key'] : (isset($_SERVER['HTTP_X_BRIDGE_KEY']) ? $_SERVER['HTTP_X_BRIDGE_KEY'] : '')));
    return $key !== '' && strlen($given) >= 16 && hash_equals($key, $given);
}
$keyAuthed = pw_bridge_ok();
if (!$keyAuthed && !is_authed()) { header('Location: ../login.php'); exit; }

// ---- read-only state (the wizard's only server-side API) -------------------
function pw_state(array $PROPS, array $LANES, array $PLATFORMS): array {
    $db = s_read(PO_FILE, array('seq' => 0, 'items' => array()));
    $live = array();
    foreach ($db['items'] as $it) {
        if (!in_array((string)($it['status'] ?? 'draft'), array('posted', 'skipped'), true)) $live[] = $it;
    }
    usort($live, function ($a, $b) { return strcmp((string)($b['updatedAt'] ?? ''), (string)($a['updatedAt'] ?? '')); });
    $fridays = array(); $t = time();
    for ($d = 0; $d < 28 && count($fridays) < 4; $d++) {
        $ts = $t + $d * 86400;
        if (gmdate('N', $ts) === '5') $fridays[] = gmdate('Y-m-d', $ts);
    }
    return array(
        'items' => $live,
        'fridays' => $fridays,
        'monthEnds' => array(gmdate('Y-m-t'), gmdate('Y-m-t', strtotime('first day of next month'))),
        'today' => gmdate('Y-m-d'),
        'props' => $PROPS, 'lanes' => $LANES, 'platforms' => $PLATFORMS,
    );
}
if (isset($_GET['do']) && $_GET['do'] === 'state') {
    header('Content-Type: application/json');
    echo json_encode(array('ok' => true) + pw_state($PROPS, $LANES, $PLATFORMS), JSON_UNESCAPED_SLASHES);
    exit;
}

$STATE = pw_state($PROPS, $LANES, $PLATFORMS);
$AUTHJS = $keyAuthed
    ? json_encode(array('key' => (string)(isset($_GET['key']) ? $_GET['key'] : '')))
    : json_encode(array('csrf' => csrf()));
?><!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>📤 Post something — Studio</title>
<link rel="icon" href="../assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="../assets/studio.css">
<style>
body{background:var(--bg)}
.pw-wrap{max-width:680px;margin:0 auto;padding:22px 18px 90px}
.pw-top{display:flex;align-items:baseline;gap:12px;margin-bottom:6px}
.pw-top h1{font-size:20px;margin:0}
.pw-top .full{margin-left:auto;font-size:12px;color:var(--muted);text-decoration:none}
.pw-top .full:hover{color:var(--text)}
.pw-sub{color:var(--muted);font-size:13px;margin:0 0 18px}
.pw-steps{display:flex;gap:4px;margin:0 0 20px}
.pw-step{flex:1;text-align:center;font-size:11px;color:var(--muted);padding-top:8px;position:relative}
.pw-step::before{content:'';display:block;height:4px;border-radius:99px;background:var(--border);margin-bottom:6px}
.pw-step.on{color:var(--text);font-weight:700}
.pw-step.on::before{background:var(--accent, #378ADD)}
.pw-step.done{color:#5fd39a}
.pw-step.done::before{background:#2e7d4f}
.pw-card{background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:20px}
.pw-card h2{margin:0 0 4px;font-size:17px}
.pw-hint{color:var(--muted);font-size:12.5px;margin:0 0 14px}
.pw-field{margin:12px 0}
.pw-field label{display:block;font-size:12px;font-weight:700;margin-bottom:5px}
.pw-field .note{font-weight:400;color:var(--muted)}
.pw-field input[type=text],.pw-field input[type=date],.pw-field textarea,.pw-field select{width:100%;font:inherit;font-size:14px;background:rgba(0,0,0,.2);border:1px solid var(--border);border-radius:9px;color:var(--text);padding:9px 11px;box-sizing:border-box}
.pw-field textarea{resize:vertical}
.pw-choices{display:flex;gap:8px;flex-wrap:wrap}
.pw-choice{font:inherit;font-size:13px;padding:8px 14px;border-radius:10px;border:1px solid var(--border);background:rgba(0,0,0,.15);color:var(--text);cursor:pointer;display:flex;align-items:center;gap:7px}
.pw-choice.on{border-color:var(--accent,#378ADD);box-shadow:0 0 0 1px var(--accent,#378ADD)}
.pw-choice .dot{width:9px;height:9px;border-radius:2px;display:inline-block}
.pw-resume{border:1px solid var(--border);border-radius:10px;padding:10px 12px;margin:8px 0;display:flex;gap:10px;align-items:center;cursor:pointer;background:rgba(0,0,0,.12)}
.pw-resume:hover{border-color:var(--accent,#378ADD)}
.pw-resume .dot{width:9px;height:9px;border-radius:2px;flex:none}
.pw-resume .t{font-weight:700;font-size:13.5px}
.pw-resume .m{color:var(--muted);font-size:11.5px}
.pw-resume .go{margin-left:auto;color:var(--muted);font-size:12px;flex:none}
.pw-nav{display:flex;gap:10px;margin-top:18px}
.pw-btn{font:inherit;font-size:14px;font-weight:700;padding:10px 20px;border-radius:10px;border:1px solid var(--border);background:rgba(255,255,255,.06);color:var(--text);cursor:pointer}
.pw-btn.primary{background:var(--accent,#378ADD);border-color:transparent;color:#fff}
.pw-btn.primary:disabled{opacity:.5;cursor:default}
.pw-btn.back{background:transparent;color:var(--muted)}
.pw-spacer{flex:1}
.pw-discard{font-size:11.5px;color:#ff9aa6;background:none;border:none;cursor:pointer;padding:0}
.pw-thumbs{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}
.pw-thumbs img{height:76px;border-radius:6px;border:1px solid var(--border);display:block}
.pw-plat{display:flex;align-items:center;gap:11px;border:1px solid var(--border);border-radius:10px;padding:11px 13px;margin:8px 0;cursor:pointer;background:rgba(0,0,0,.12)}
.pw-plat.on{border-color:#2b5b8a;box-shadow:0 0 0 1px #2b5b8a66}
.pw-plat input{width:16px;height:16px;accent-color:var(--accent,#378ADD)}
.pw-plat .n{font-weight:700;font-size:14px}
.pw-plat .d{color:var(--muted);font-size:11.5px}
.pw-rev{border:1px solid var(--border);border-radius:10px;padding:12px 14px;margin:10px 0;background:rgba(0,0,0,.12);font-size:13.5px}
.pw-rev .row{display:flex;gap:8px;margin:4px 0}
.pw-rev .k{color:var(--muted);width:88px;flex:none;font-size:12px;padding-top:1px}
.pw-rev .cap{white-space:pre-wrap}
.pw-warn{border-radius:10px;padding:11px 14px;margin-top:14px;font-size:13px;background:#332810;color:#ffd88a}
.pw-ok{border-radius:10px;padding:11px 14px;margin-top:14px;font-size:13px;background:#10331f;color:#9fe8bd}
.pw-done{text-align:center;padding:14px 0 6px}
.pw-done .big{font-size:42px}
.pw-done h2{margin:8px 0 6px}
.pw-err{background:#38151a;color:#ffb3bd;border-radius:10px;padding:10px 14px;margin-top:12px;font-size:13px;display:none}
.pw-chip{font-size:12px;padding:4px 11px;border-radius:999px;border:1px solid var(--border);background:transparent;color:var(--muted);cursor:pointer}
.pw-chip:hover{color:var(--text);border-color:var(--accent,#378ADD)}
.pw-lock{color:#5fd39a;font-weight:700}
</style>
</head><body>
<div class="pw-wrap">
  <div class="pw-top">
    <h1>📤 Post something</h1>
    <a class="full" href="../cc.php">Full studio →</a>
  </div>
  <p class="pw-sub">Queue a piece onto the posting board, one step at a time. Nothing posts by itself — you fire each platform yourself at the end.</p>
  <div class="pw-steps" id="steps"></div>
  <div id="stage"></div>
  <div class="pw-err" id="err"></div>
</div>
<script>
var AUTH = <?= $AUTHJS ?>;
var STATE = <?= json_encode($STATE, JSON_UNESCAPED_SLASHES) ?>;
var STEPS = ['Pick', 'Art & copy', 'Platforms', 'Schedule', 'Review'];
var PLAT_HINTS = {
  patreon: 'Fan Art Friday fires here first — the weekly metronome.',
  deviantart: 'Biggest audience on every property. Mirror FAF here.',
  site: 'The property’s own website.',
  twitter: 'Quick announce post.',
  instagram: 'growgettercomics is the logged-in account.'
};

// Wizard state: the item being built. All fields are kept here and ALWAYS sent
// in full on update (posting.php's update replaces every field it reads).
var W = { step: 0, id: '', item: null, chosen: null };

function el(html) { var d = document.createElement('div'); d.innerHTML = html; return d; }
function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]; }); }
function showErr(m) { var e = document.getElementById('err'); e.textContent = m; e.style.display = 'block'; setTimeout(function () { e.style.display = 'none'; }, 6000); }

function apiPost(fields, done) {
  var fd = new FormData();
  for (var k in fields) {
    if (fields[k] instanceof FileList) { for (var i = 0; i < fields[k].length; i++) fd.append(k, fields[k][i]); }
    else fd.append(k, fields[k]);
  }
  if (AUTH.csrf) fd.append('csrf', AUTH.csrf);
  if (AUTH.key) fd.append('key', AUTH.key);
  fetch('../posting.php', { method: 'POST', body: fd }).then(function (r) { return r.json(); })
    .then(function (j) { if (!j.ok) { showErr(j.error || 'Save failed'); done(null); } else done(j); })
    .catch(function () { showErr('Network error — nothing saved. Try again.'); done(null); });
}
function refreshState(done) {
  fetch('index.php?do=state' + (AUTH.key ? '&key=' + encodeURIComponent(AUTH.key) : ''))
    .then(function (r) { return r.json(); })
    .then(function (j) { if (j.ok) STATE = j; done(); })
    .catch(function () { done(); });
}
function findItem(id) {
  for (var i = 0; i < STATE.items.length; i++) if (STATE.items[i].id === id) return STATE.items[i];
  return null;
}
// Full field set posting.php's update expects — always sent together.
function fieldsOf(it, over) {
  var f = {
    action: 'update', id: it.id, title: it.title || '', property: it.property || 'growgetter',
    lane: it.lane || 'side', slot: it.slot || '', status: it.status || 'draft',
    owner: it.owner || '', caption: it.caption || '', notes: it.notes || '',
    assets: (it.assets || []).filter(function (a) { return a.indexOf('posting.php?img=') !== 0; }).join('\n')
  };
  // NB: uploaded-art assets (posting.php?img=…) are managed by the upload action;
  // update's assets field only carries the external links so we re-merge below.
  for (var k in (over || {})) f[k] = over[k];
  return f;
}
// posting.php update replaces the whole assets list with the textarea links, so
// re-send uploaded-art URLs too, appended after the links.
function fullAssets(it, links) {
  var art = (it.assets || []).filter(function (a) { return a.indexOf('posting.php?img=') === 0; });
  return links.concat(art).join('\n');
}

function setStep(n) { W.step = n; render(); window.scrollTo(0, 0); }

function render() {
  var bar = document.getElementById('steps');
  bar.innerHTML = '';
  STEPS.forEach(function (s, i) {
    bar.appendChild(el('<div class="pw-step ' + (i === W.step ? 'on' : (i < W.step ? 'done' : '')) + '">' + s + '</div>').firstChild);
  });
  var stage = document.getElementById('stage');
  stage.innerHTML = '';
  stage.appendChild([step1, step2, step3, step4, step5][W.step]());
}

// ---- Step 1: pick ----------------------------------------------------------
function step1() {
  var c = el('<div class="pw-card"><h2>What are you posting?</h2>' +
    '<p class="pw-hint">Pick something already in progress, or start fresh.</p><div id="resume"></div>' +
    '<div class="pw-field"><label>Start new — which property?</label><div class="pw-choices" id="props"></div></div>' +
    '<div class="pw-field"><label>What kind of post?</label><div class="pw-choices" id="lanes"></div></div>' +
    '<div class="pw-field"><label>Title <span class="note">— what the piece is called</span></label>' +
    '<input type="text" id="title" placeholder="e.g. Fan Art Friday — Jacked Jill by Boogie"></div>' +
    '<div class="pw-nav"><span class="pw-spacer"></span><button class="pw-btn primary" id="go">Start →</button></div></div>').firstChild;

  var res = c.querySelector('#resume');
  var inProgress = STATE.items.slice(0, 8);
  if (inProgress.length) {
    res.appendChild(el('<div class="pw-field"><label>Continue where you left off</label></div>').firstChild);
    inProgress.forEach(function (it) {
      var p = STATE.props[it.property] || { name: it.property, color: '#888' };
      var r = el('<div class="pw-resume"><span class="dot" style="background:' + esc(p.color) + '"></span>' +
        '<span><span class="t">' + esc(it.title) + '</span><br><span class="m">' + esc(STATE.lanes[it.lane] || it.lane) +
        ' · ' + esc(it.slot || 'no date') + ' · ' + esc(it.status) + '</span></span><span class="go">continue →</span></div>').firstChild;
      r.onclick = function () { W.id = it.id; W.item = it; setStep(1); };
      res.appendChild(r);
    });
    res.appendChild(el('<div class="pw-field"><label>…or start new</label></div>').firstChild);
  }

  var selProp = 'growgetter', selLane = 'faf';
  function paintChoices(box, opts, sel, isProp) {
    box.innerHTML = '';
    Object.keys(opts).forEach(function (k) {
      var label = isProp ? opts[k].name : opts[k];
      var b = el('<button type="button" class="pw-choice' + (k === sel ? ' on' : '') + '">' +
        (isProp ? '<span class="dot" style="background:' + esc(opts[k].color) + '"></span>' : '') + esc(label) + '</button>').firstChild;
      b.onclick = function () {
        if (isProp) selProp = k; else selLane = k;
        paintChoices(box, opts, k, isProp);
      };
      box.appendChild(b);
    });
  }
  paintChoices(c.querySelector('#props'), STATE.props, selProp, true);
  paintChoices(c.querySelector('#lanes'), STATE.lanes, selLane, false);

  c.querySelector('#go').onclick = function () {
    var title = c.querySelector('#title').value.trim();
    if (!title) { showErr('Give it a title first.'); return; }
    this.disabled = true;
    apiPost({ action: 'add', title: title, property: selProp, lane: selLane, slot: '', status: 'draft', owner: 'Alternate', caption: '', notes: '', assets: '' }, function (j) {
      if (!j) { c.querySelector('#go').disabled = false; return; }
      refreshState(function () {
        // posting.php returns the new id; fall back to newest match by title.
        var it = j.id ? findItem(j.id) : null;
        if (!it) { for (var i = 0; i < STATE.items.length; i++) if (STATE.items[i].title === title) { it = STATE.items[i]; break; } }
        if (!it) { showErr('Created, but could not reload it — open the board.'); return; }
        W.id = it.id; W.item = it; setStep(1);
      });
    });
  };
  return c;
}

// ---- Step 2: art & copy ----------------------------------------------------
function step2() {
  var it = W.item;
  var links = (it.assets || []).filter(function (a) { return a.indexOf('posting.php?img=') !== 0; });
  var art = (it.assets || []).filter(function (a) { return a.indexOf('posting.php?img=') === 0; });
  var keyQ = AUTH.key ? '&key=' + encodeURIComponent(AUTH.key) : '';
  var c = el('<div class="pw-card"><h2>Art &amp; copy</h2>' +
    '<p class="pw-hint">Attach the files and write the caption you’ll paste when posting.</p>' +
    '<div class="pw-field"><label>Upload the art <span class="note">— jpg/png/webp/gif, up to 30 MB each</span></label>' +
    '<input type="file" id="art" accept="image/*" multiple>' +
    (art.length ? '<div class="pw-thumbs">' + art.map(function (a) { return '<img src="../' + esc(a) + '&t=1' + keyQ + '" alt="art">'; }).join('') + '</div>' : '') + '</div>' +
    '<div class="pw-field"><label>…or link it <span class="note">— Drive / portal / Flow links, one per line</span></label>' +
    '<textarea id="links" rows="2" placeholder="https://…">' + esc(links.join('\n')) + '</textarea></div>' +
    '<div class="pw-field"><label>Caption <span class="note">— copy-paste ready for the platforms</span></label>' +
    '<textarea id="cap" rows="4" placeholder="Title, artist credit, links…">' + esc(it.caption || '') + '</textarea></div>' +
    '<div class="pw-field"><label>Notes <span class="note">— anything future-you should know (optional)</span></label>' +
    '<input type="text" id="notes" value="' + esc(it.notes || '') + '"></div>' +
    '<div class="pw-nav"><button class="pw-btn back" id="back">← Back</button><span class="pw-spacer"></span>' +
    '<button class="pw-discard" id="discard">discard this draft</button>' +
    '<button class="pw-btn primary" id="next">Save &amp; continue →</button></div></div>').firstChild;

  c.querySelector('#back').onclick = function () { setStep(0); };
  c.querySelector('#discard').onclick = function () {
    if (!confirm('Delete this draft item entirely?')) return;
    apiPost({ action: 'del', id: W.id }, function (j) {
      if (j) refreshState(function () { W.id = ''; W.item = null; setStep(0); });
    });
  };
  c.querySelector('#next').onclick = function () {
    var btn = this; btn.disabled = true;
    var files = c.querySelector('#art').files;
    var save = function () {
      var newLinks = c.querySelector('#links').value.split('\n').map(function (s) { return s.trim(); }).filter(Boolean);
      apiPost(fieldsOf(it, {
        caption: c.querySelector('#cap').value.trim(),
        notes: c.querySelector('#notes').value.trim(),
        assets: fullAssets(W.item, newLinks)
      }), function (j) {
        if (!j) { btn.disabled = false; return; }
        refreshState(function () { W.item = findItem(W.id) || W.item; setStep(2); });
      });
    };
    if (files.length) {
      apiPost({ action: 'upload', id: W.id, 'art[]': files }, function (j) {
        if (!j) { btn.disabled = false; return; }
        refreshState(function () { W.item = findItem(W.id) || W.item; save(); });
      });
    } else save();
  };
  return c;
}

// ---- Step 3: platforms -----------------------------------------------------
function step3() {
  var it = W.item;
  var c = el('<div class="pw-card"><h2>Where does it go?</h2>' +
    '<p class="pw-hint">Tick every platform this piece should be posted to. Unticked ones get marked "n/a" on the board.</p>' +
    '<div id="plats"></div>' +
    '<div class="pw-nav"><button class="pw-btn back" id="back">← Back</button><span class="pw-spacer"></span>' +
    '<button class="pw-btn primary" id="next">Save &amp; continue →</button></div></div>').firstChild;

  var box = c.querySelector('#plats');
  var sel = {};
  Object.keys(STATE.platforms).forEach(function (k) {
    var st = (it.platforms || {})[k] || 'todo';
    sel[k] = st !== 'na';
    var row = el('<label class="pw-plat' + (sel[k] ? ' on' : '') + '"><input type="checkbox"' + (sel[k] ? ' checked' : '') + '>' +
      '<span><span class="n">' + esc(STATE.platforms[k]) + '</span><br><span class="d">' + esc(PLAT_HINTS[k] || '') + '</span></span></label>').firstChild;
    row.querySelector('input').onchange = function () { sel[k] = this.checked; row.classList.toggle('on', this.checked); };
    box.appendChild(row);
  });

  c.querySelector('#back').onclick = function () { setStep(1); };
  c.querySelector('#next').onclick = function () {
    var btn = this; btn.disabled = true;
    var keys = Object.keys(STATE.platforms), i = 0;
    (function nextPlat() {
      if (i >= keys.length) { refreshState(function () { W.item = findItem(W.id) || W.item; setStep(3); }); return; }
      var k = keys[i++];
      var cur = (W.item.platforms || {})[k] || 'todo';
      var want = sel[k] ? (cur === 'na' ? 'todo' : cur) : 'na';
      if (want === cur) { nextPlat(); return; }
      apiPost({ action: 'plat', id: W.id, plat: k, state: want }, function (j) {
        if (!j) { btn.disabled = false; return; }
        nextPlat();
      });
    })();
  };
  return c;
}

// ---- Step 4: schedule ------------------------------------------------------
function step4() {
  var it = W.item;
  var chips = '';
  if (it.lane === 'faf') {
    chips = STATE.fridays.map(function (f) { return '<button type="button" class="pw-chip" data-d="' + esc(f) + '">Fri ' + esc(f) + '</button>'; }).join('');
  } else if (it.lane === 'comic') {
    chips = STATE.monthEnds.map(function (m) { return '<button type="button" class="pw-chip" data-d="' + esc(m) + '">' + esc(m) + '</button>'; }).join('');
  } else {
    chips = '<button type="button" class="pw-chip" data-d="' + esc(STATE.today) + '">Today</button>';
  }
  var c = el('<div class="pw-card"><h2>When should it go out?</h2>' +
    '<p class="pw-hint">' + (it.lane === 'faf' ? 'Fan Art Friday means a Friday — pick one.' : 'Pick the target date. It can move later on the board.') + '</p>' +
    '<div class="pw-field"><div class="pw-choices" style="margin-bottom:10px">' + chips + '</div>' +
    '<label>Date</label><input type="date" id="slot" value="' + esc(it.slot || '') + '"></div>' +
    '<div class="pw-nav"><button class="pw-btn back" id="back">← Back</button><span class="pw-spacer"></span>' +
    '<button class="pw-btn primary" id="next">Save &amp; continue →</button></div></div>').firstChild;

  c.querySelectorAll('.pw-chip').forEach(function (b) {
    b.onclick = function () { c.querySelector('#slot').value = this.getAttribute('data-d'); };
  });
  c.querySelector('#back').onclick = function () { setStep(2); };
  c.querySelector('#next').onclick = function () {
    var btn = this; btn.disabled = true;
    var slot = c.querySelector('#slot').value;
    if (!slot) { showErr('Pick a date.'); btn.disabled = false; return; }
    apiPost(fieldsOf(W.item, { slot: slot, assets: fullAssets(W.item, (W.item.assets || []).filter(function (a) { return a.indexOf('posting.php?img=') !== 0; })) }), function (j) {
      if (!j) { btn.disabled = false; return; }
      refreshState(function () { W.item = findItem(W.id) || W.item; setStep(4); });
    });
  };
  return c;
}

// ---- Step 5: review + confirm ---------------------------------------------
function step5() {
  var it = W.item;
  var p = STATE.props[it.property] || { name: it.property, color: '#888' };
  var on = [], off = [];
  Object.keys(STATE.platforms).forEach(function (k) {
    var st = (it.platforms || {})[k] || 'todo';
    (st === 'na' ? off : on).push(STATE.platforms[k]);
  });
  var art = (it.assets || []).filter(function (a) { return a.indexOf('posting.php?img=') === 0; });
  var links = (it.assets || []).filter(function (a) { return a.indexOf('posting.php?img=') !== 0; });
  var keyQ = AUTH.key ? '&key=' + encodeURIComponent(AUTH.key) : '';

  var c = el('<div class="pw-card"><h2>Ready to queue?</h2>' +
    '<p class="pw-hint">One last look. Confirming marks it <b>ready</b> and arms the platforms as <b>scheduled</b> on the board.</p>' +
    '<div class="pw-rev">' +
    '<div class="row"><span class="k">Piece</span><span><span class="dot" style="background:' + esc(p.color) + ';width:9px;height:9px;border-radius:2px;display:inline-block;margin-right:6px"></span><b>' + esc(it.title) + '</b> · ' + esc(p.name) + ' · ' + esc(STATE.lanes[it.lane] || it.lane) + '</span></div>' +
    '<div class="row"><span class="k">Date</span><span>' + esc(it.slot || '—') + '</span></div>' +
    '<div class="row"><span class="k">Platforms</span><span>' + esc(on.join(', ') || 'none!') + (off.length ? ' <span style="color:var(--muted)">(skipping ' + esc(off.join(', ')) + ')</span>' : '') + '</span></div>' +
    (art.length ? '<div class="row"><span class="k">Art</span><span class="pw-thumbs" style="margin:0">' + art.map(function (a) { return '<img src="../' + esc(a) + '&t=1' + keyQ + '" alt="art">'; }).join('') + '</span></div>' : '') +
    (links.length ? '<div class="row"><span class="k">Links</span><span>' + links.map(esc).join('<br>') + '</span></div>' : '') +
    (it.caption ? '<div class="row"><span class="k">Caption</span><span class="cap">' + esc(it.caption) + '</span></div>' : '') +
    '</div>' +
    '<div class="pw-warn">⚠️ Nothing posts automatically. On the day, <b>you</b> post to each platform yourself, then flip its chip to <b>posted</b> on the board.</div>' +
    '<div class="pw-nav"><button class="pw-btn back" id="back">← Back</button><span class="pw-spacer"></span>' +
    '<button class="pw-btn primary" id="confirm">🔒 Queue it</button></div></div>').firstChild;

  c.querySelector('#back').onclick = function () { setStep(3); };
  c.querySelector('#confirm').onclick = function () {
    var btn = this; btn.disabled = true;
    if (!on.length) { showErr('No platforms selected — go back and tick at least one.'); btn.disabled = false; return; }
    // Arm each non-na platform that's still 'todo' as 'scheduled', then mark ready.
    var keys = Object.keys(STATE.platforms).filter(function (k) { return ((it.platforms || {})[k] || 'todo') === 'todo'; });
    var i = 0;
    (function arm() {
      if (i >= keys.length) {
        apiPost(fieldsOf(it, { status: 'ready', assets: fullAssets(it, links) }), function (j) {
          if (!j) { btn.disabled = false; return; }
          refreshState(function () { W.item = findItem(W.id) || W.item; renderDone(); });
        });
        return;
      }
      apiPost({ action: 'plat', id: W.id, plat: keys[i++], state: 'scheduled' }, function (j) {
        if (!j) { btn.disabled = false; return; }
        arm();
      });
    })();
  };
  return c;
}

function renderDone() {
  var it = W.item;
  var bar = document.getElementById('steps');
  bar.innerHTML = '';
  STEPS.forEach(function (s) { bar.appendChild(el('<div class="pw-step done">' + s + '</div>').firstChild); });
  var stage = document.getElementById('stage');
  stage.innerHTML = '';
  var c = el('<div class="pw-card"><div class="pw-done"><div class="big">🔒</div>' +
    '<h2><span class="pw-lock">Locked &amp; loaded</span></h2>' +
    '<p class="pw-hint" style="margin-bottom:0"><b>' + esc(it.title) + '</b> is queued for ' + esc(it.slot || 'its date') + '.<br>' +
    'On the day: post it on each platform, then flip the chips to <b>posted</b>.</p></div>' +
    '<div class="pw-ok">It’s now on the posting board with everything you prepared — caption ready to copy, art attached.</div>' +
    '<div class="pw-nav"><a class="pw-btn" href="../posting.php" style="text-decoration:none">Open the board</a>' +
    '<span class="pw-spacer"></span><button class="pw-btn primary" id="again">Queue another →</button></div></div>').firstChild;
  c.querySelector('#again').onclick = function () {
    W = { step: 0, id: '', item: null };
    refreshState(render);
  };
  stage.appendChild(c);
}

render();
</script>
</body></html>
