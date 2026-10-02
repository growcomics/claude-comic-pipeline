<?php
// ws.php: the lieutenant workspace. One page for a hired helper to run a comic end to end
// (story -> pages -> refs -> generate -> pick -> hand to the owner). Owner/staff can use it too.
// See docs/LIEUTENANT-WORKSPACE.md. All data goes through ws-api.php (JSON); this file renders
// the shell and the "My comics" list. Nothing here can publish, post, port or delete images.
//
//   ws.php?t=<token>  magic-link sign-in (token is stripped from the URL by a redirect)
//   ws.php            My comics (+ New comic)
//   ws.php?p=<pid>    the comic workspace
//
// Local helpers are prefixed ws_ws_ (shared helpers live in inc/workspace.php).
declare(strict_types=1);
require_once __DIR__ . '/inc/boot.php';

header('X-Robots-Tag: noindex');
header('Referrer-Policy: same-origin');
header('X-Content-Type-Options: nosniff');

const WS_WS_ASPECTS = ['3:4' => '3:4 portrait (default)', '2:3' => '2:3 portrait', '9:16' => '9:16 phone', '1:1' => '1:1 square',
                       '4:3' => '4:3 landscape', '16:9' => '16:9 wide'];

function ws_ws_head(string $title, string $extraCss = ''): void {
    echo '<!doctype html><html lang="en"><head><meta charset="utf-8">'
       . '<meta name="viewport" content="width=device-width, initial-scale=1">'
       . '<meta name="color-scheme" content="dark"><meta name="robots" content="noindex,nofollow">'
       . '<title>' . h($title) . '</title><link rel="icon" href="assets/favicon.svg" type="image/svg+xml">'
       . '<link rel="stylesheet" href="assets/studio.css">'
       . ($extraCss !== '' ? '<style>' . $extraCss . '</style>' : '')
       . '</head><body>';
}
// A small centered message page (bad link, signed out). $body is plain text.
function ws_ws_notice(int $code, string $title, string $body, string $href = '', string $linkText = ''): void {
    http_response_code($code);
    header('Cache-Control: no-store');
    ws_ws_head($title, 'body{display:flex;align-items:center;justify-content:center;min-height:100vh;padding:16px}.card.auth{max-width:420px}');
    echo '<div class="card auth"><div class="brand"><span class="dot"></span> 🧑‍✈️ Workspace</div>'
       . '<h1 style="font-size:20px;margin-bottom:8px">' . h($title) . '</h1>'
       . '<p class="muted" style="margin:0 0 16px">' . h($body) . '</p>'
       . ($href !== '' ? '<a class="btn primary" href="' . h($href) . '">' . h($linkText) . '</a>' : '')
       . '</div></body></html>';
    exit;
}
function ws_ws_status_color(string $s): string {
    return ['active' => '#1D9E75', 'on-hold' => '#EF9F27', 'done' => '#378ADD', 'archived' => '#6F7380'][$s] ?? '#6F7380';
}
// Page + picked counts from the small workspace stores only (never images-<pid>.json).
function ws_ws_counts(string $pid): array {
    $pages = is_file(ws_file('proj', $pid)) ? count(ws_proj($pid)['pages']) : -1;
    $picked = 0;
    if (is_file(ws_file('picks', $pid))) {
        foreach (ws_picks($pid)['pages'] as $pk) if (is_array($pk) && is_array($pk['pick'] ?? null) && $pk['pick']) $picked++;
    }
    return [$pages, $picked];
}
function ws_ws_topbar(string $name, bool $isLt, bool $isOwner): void { ?>
<header class="topbar">
  <a class="brand" href="ws.php"><span class="dot"></span> 🧑‍✈️ Workspace</a>
  <span class="spacer"></span>
  <?php if (!$isLt): ?><a class="ghost" href="index.php">🎬 Studio</a><?php endif; ?>
  <?php if ($isOwner): ?><a class="ghost" href="team.php">👥 Team</a><?php endif; ?>
  <button type="button" class="tb-btn" id="howBtn" aria-expanded="false" aria-controls="howto">❔ How it works</button>
  <span class="ghost tb-user"><?= h($name) ?></span>
  <a class="ghost" href="login.php?do=logout">Log out</a>
</header>
<?php }
function ws_ws_howto(): void { ?>
<section class="card howto" id="howto" hidden>
  <div class="howto-head"><h2>❔ How it works</h2><button type="button" class="btn sm" id="howClose">Hide</button></div>
  <ol>
    <li><b>Write the story and the style.</b> Open <em>Story &amp; style</em>, paste or write the story, and describe the look in a line or two.</li>
    <li><b>Ask Claude to break the story into pages.</b> In the chat, type something like “Split the story into pages” and press <em>Ask Claude</em>. Claude only proposes: nothing changes until you press <em>Confirm</em> on its card.</li>
    <li><b>Upload references and attach them to pages.</b> Character sheets and locations go in <em>References</em>. On each page, use <em>+ attach ref</em> so the generator knows who and where.</li>
    <li><b>Generate takes.</b> Press <em>Generate ×2</em> or <em>×4</em> on a page. Your images left for today are shown at the top. Jobs wait in the <em>Queue</em> until the generator picks them up.</li>
    <li><b>Pick the best take.</b> Open the picker, pick the best take for each page, and leave a comment on any page that needs a redo.</li>
    <li><b>Hand it over.</b> When every page has a pick, press <em>Ready for owner review</em>.</li>
  </ol>
  <p class="muted small" style="margin:10px 0 0">Nothing here publishes anything. The owner reviews and releases comics.</p>
</section>
<?php }

// ---- 1) magic link: exchange the token, then strip it from the URL ------------------------------
if (isset($_GET['t'])) {
    header('Referrer-Policy: no-referrer');
    header('Cache-Control: no-store');
    $tok = is_string($_GET['t']) ? $_GET['t'] : '';
    if ($tok !== '' && ws_magic_login($tok)) { header('Location: ws.php'); exit; }
    usleep(300000);
    ws_ws_notice(401, 'This link is not valid any more', 'Your private link was changed or switched off. Ask the owner for a new one.');
}

// ---- 2) not signed in ----------------------------------------------------------------------------
if (!is_authed()) {   // (a lieutenant reaching outside their scope is answered inside is_authed -> ws_gate)
    ws_ws_notice(200, 'Workspace', 'Lieutenants: open your private link. Staff: sign in with your studio login.', 'login.php', 'Staff: sign in →');
}

$meName  = current_studio_user();
$isLt    = ws_is_lt();
$isOwner = ws_is_owner();
$uid     = ws_uid();
$person  = ws_me();

$CSS = <<<'CSS'
.topbar{flex-wrap:wrap;height:auto;min-height:56px;padding:8px 22px;gap:8px 16px}
.topbar .brand{color:var(--text)}
.tb-btn{background:none;border:0;color:var(--muted);font:13px Inter,system-ui,sans-serif;cursor:pointer;padding:0}
.tb-btn:hover,.tb-btn[aria-expanded=true]{color:var(--text)}
.small{font-size:12.5px}
.btn.sm{padding:7px 11px;font-size:12.5px}
.btn:disabled{opacity:.45;cursor:not-allowed}
.howto ol{margin:4px 0 0;padding-left:20px}.howto li{margin:7px 0;font-size:14px}.howto em{font-style:normal;color:var(--accent)}
.howto-head{display:flex;align-items:center;justify-content:space-between;gap:10px}.howto-head h2{margin:0}
.pill{display:inline-flex;align-items:center;gap:6px;font-size:12.5px;font-weight:600;padding:5px 11px;border-radius:999px;background:var(--surface2);border:1px solid var(--border2);color:var(--text)}
.pill.ok{color:#7fe0bf;border-color:rgba(29,158,117,.45)}.pill.warn{color:#f5c67a;border-color:rgba(239,159,39,.45)}.pill.bad{color:#f3a3a2;border-color:rgba(226,75,74,.45)}
.bbadge{--c:#9aa3ff}
/* list */
.ws-filter{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:14px}
.ws-filter input,.ws-filter select{width:auto;margin:0;flex:0 1 240px}
.pcard.hide{display:none}
.pcard.archived{opacity:.6}
.newform{display:grid;grid-template-columns:minmax(0,2fr) minmax(0,1fr);gap:12px;margin-top:12px}
.newform .full{grid-column:1/-1}
.newform label{margin:0}
/* comic */
.ws-wrap{max-width:1320px}
.ws-head{display:flex;flex-wrap:wrap;gap:12px 18px;align-items:center}
.ws-title{display:flex;flex-wrap:wrap;align-items:center;gap:6px 12px;flex:1 1 320px;min-width:0}
.ws-title h1{font-size:21px;word-break:break-word}
.ws-pills,.ws-hbtns{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.ws-cols{display:grid;grid-template-columns:minmax(0,1.45fr) minmax(0,1fr);gap:18px;align-items:start}
.ws-cols>div{min-width:0}
.card h2 .muted{font-size:13px;font-weight:500;margin-left:6px}
details.card>summary{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
details.card>summary .muted{font-size:12.5px;font-weight:400}
details.card>summary::after{content:'▸';margin-left:auto;color:var(--muted)}
details.card[open]>summary::after{content:'▾'}
.story-grid{display:grid;grid-template-columns:minmax(0,1fr) 200px;gap:12px;margin-top:12px}
.story-grid .full{grid-column:1/-1}
.story-grid label{margin:0}
#fStory{min-height:200px}
.pg{border:1px solid var(--border2);border-radius:10px;padding:12px;margin-bottom:12px;background:var(--bg2)}
.pg.dirty{border-color:rgba(239,159,39,.6)}
.pg-head{display:flex;align-items:center;gap:8px 10px;flex-wrap:wrap}
.pg-n{font-weight:800;white-space:nowrap}
.pg-title{flex:1 1 160px;width:auto;margin:0;padding:6px 9px}
.pg-badge{font-size:11px;font-weight:700;padding:2px 9px;border-radius:999px;background:var(--surface2);color:var(--muted);white-space:nowrap}
.pg-badge.ok{color:#7fe0bf;background:rgba(29,158,117,.14)}.pg-badge.warn{color:#f5c67a;background:rgba(239,159,39,.12)}
.pg-prompt{margin-top:8px;min-height:88px}
.pg-refs{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin-top:8px}
.chips{display:contents}
.chip{display:inline-flex;align-items:center;gap:5px;background:var(--surface2);border:1px solid var(--border2);border-radius:999px;padding:2px 2px 2px 2px;font-size:12px;max-width:100%}
.chip img{width:24px;height:24px;border-radius:50%;object-fit:cover;background:#000}
.chip span{max-width:150px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.chip button{background:none;border:0;color:var(--muted);cursor:pointer;font-size:13px;padding:0 6px;line-height:1}
.chip button:hover{color:var(--red)}
.pg-attach{width:auto;max-width:220px;margin:0;padding:5px 8px;font-size:12.5px}
.pg-stats{font-size:12.5px;color:var(--muted);margin-top:8px}
.pg-thumbs{display:flex;gap:6px;margin-top:6px;flex-wrap:wrap}
.pg-thumbs a{position:relative;width:64px;aspect-ratio:3/4;border-radius:7px;overflow:hidden;background:#000;border:1px solid var(--border2);display:flex;align-items:center;justify-content:center;font-size:12px;color:var(--muted)}
.pg-thumbs img{width:100%;height:100%;object-fit:cover;display:block}
.pg-thumbs a.picked{border-color:var(--teal);box-shadow:0 0 0 1px var(--teal)}
.pg-thumbs a.picked::after{content:'✓';position:absolute;top:3px;right:3px;color:#04221a;background:var(--teal);border-radius:50%;font-size:10px;font-weight:800;width:16px;height:16px;display:flex;align-items:center;justify-content:center}
.pg-comment{font-size:12.5px;margin-top:8px;padding:7px 10px;border-radius:8px;background:rgba(55,138,221,.1);border:1px solid rgba(55,138,221,.3);white-space:pre-wrap;word-break:break-word}
.pg-btns{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px;align-items:center}
.ws-refs{display:grid;grid-template-columns:repeat(auto-fill,minmax(112px,1fr));gap:10px;margin-top:12px}
.ref{background:var(--bg2);border:1px solid var(--border2);border-radius:10px;overflow:hidden;position:relative}
.ref img{width:100%;aspect-ratio:1;object-fit:cover;display:block;background:#000}
.ref input{margin:0;border:0;border-top:1px solid var(--border2);border-radius:0;padding:6px 8px;font-size:12px}
.ref .rm{position:absolute;top:5px;right:5px;background:rgba(12,13,18,.82);border:1px solid var(--border2);color:var(--text);border-radius:6px;cursor:pointer;font-size:12px;padding:2px 7px}
.ref .rm:hover{color:var(--red)}
label.dropzone{display:block;cursor:pointer;margin:0;color:var(--muted);font-size:13.5px}
.chat-list{max-height:min(60vh,620px);min-height:120px;overflow-y:auto;display:flex;flex-direction:column;gap:8px;padding-right:4px;margin-bottom:10px;overscroll-behavior:contain}
.msg{padding:8px 11px;border-radius:10px;background:var(--bg2);border:1px solid var(--border)}
.msg.mine{background:rgba(239,159,39,.07);border-color:rgba(239,159,39,.25)}
.msg-ai{background:rgba(122,127,236,.09);border-color:rgba(122,127,236,.32)}
.msg-system{background:transparent;border:0;padding:1px 4px;color:var(--muted)}
.msg-meta{font-size:11.5px;color:var(--muted);display:flex;flex-wrap:wrap;gap:4px 8px;margin-bottom:2px}
.msg-meta b{color:var(--text)}
.msg-meta .askd{color:#b9bcf5}
.msg-text{white-space:pre-wrap;word-break:break-word;font-size:14px}
.msg-system .msg-text{font-size:12.5px}
.msg-system .ts{font-size:11px;color:var(--muted2);margin-left:6px}
.act{margin-top:8px;border:1px solid var(--border2);border-radius:9px;padding:9px 10px;background:var(--surface)}
.act-sum{font-weight:600;font-size:13px;word-break:break-word}
.act details{margin-top:6px;font-size:12.5px}.act summary{cursor:pointer;color:var(--muted)}
.act pre{white-space:pre-wrap;word-break:break-word;font:12.5px/1.45 Inter,system-ui,sans-serif;margin:6px 0 0;color:#c7cad4;max-height:260px;overflow:auto}
.act-btns{display:flex;gap:8px;margin-top:8px;flex-wrap:wrap}
.act-status{margin-top:6px;font-size:12.5px;color:var(--muted);word-break:break-word}
.act.confirmed{border-color:rgba(29,158,117,.5)}.act.failed{border-color:rgba(226,75,74,.5)}.act.dismissed{opacity:.6}
.typing{font-size:12.5px;color:var(--muted);margin:0 0 8px;display:flex;align-items:center;gap:5px}
.typing[hidden]{display:none}
.typing i{width:6px;height:6px;border-radius:50%;background:var(--muted);animation:wsb 1s infinite}
.typing i:nth-child(2){animation-delay:.15s}.typing i:nth-child(3){animation-delay:.3s}
@keyframes wsb{0%,80%,100%{opacity:.25}40%{opacity:1}}
#chatText{min-height:72px;margin-top:0}
.chat-btns{display:flex;gap:8px;margin-top:8px;flex-wrap:wrap;align-items:center}
.job{display:flex;flex-wrap:wrap;align-items:center;gap:4px 10px;padding:8px 0;border-top:1px solid var(--border);font-size:13px}
.job:first-child{border-top:0}
.jst{font-size:10.5px;font-weight:800;padding:2px 8px;border-radius:999px;text-transform:uppercase;letter-spacing:.03em;background:var(--surface2);color:var(--muted)}
.jst.queued{color:#f5c67a}.jst.running{color:#9ec5f0}.jst.done{color:#7fe0bf}.jst.failed,.jst.error{color:#f3a3a2}.jst.cancelled{color:var(--muted2)}
.jnote{flex-basis:100%}
.empty{font-size:13px;color:var(--muted);margin:4px 0}
#toasts{position:fixed;left:50%;bottom:18px;transform:translateX(-50%);z-index:200;display:flex;flex-direction:column;gap:8px;align-items:center;width:min(520px,calc(100% - 24px));pointer-events:none}
.toast{pointer-events:auto;background:var(--surface2);border:1px solid var(--border2);color:var(--text);padding:10px 14px;border-radius:10px;font-size:13.5px;box-shadow:0 8px 24px rgba(0,0,0,.45);cursor:pointer;word-break:break-word;max-width:100%}
.toast.err{border-color:rgba(226,75,74,.6);background:#2a1517}
.toast.ok{border-color:rgba(29,158,117,.6)}
@media(max-width:900px){.ws-cols{grid-template-columns:minmax(0,1fr)}}
@media(max-width:600px){
  .wrap{padding:14px 12px 80px}.topbar{padding:8px 12px;gap:6px 12px}.tb-user{display:none}
  .card{padding:14px}.newform,.story-grid{grid-template-columns:minmax(0,1fr)}
  .pg-thumbs a{width:56px}.ws-hbtns .btn,.ws-hbtns a.btn{flex:1 1 auto;justify-content:center}
  .ws-filter input,.ws-filter select{flex:1 1 140px}
}
CSS;

// ---- 4) the comic workspace (?p=) ------------------------------------------------------------------
$pidRaw = $_GET['p'] ?? '';
$pidRaw = is_string($pidRaw) ? $pidRaw : '';
if ($pidRaw !== '') {
    $pid = ws_pid($pidRaw);
    $project = ($pid !== '' && $pid === $pidRaw && ws_can_see($pid)) ? project_get($pid) : null;
    if (!$project) {
        http_response_code(404);
        ws_ws_head('Not found · Workspace', $CSS);
        ws_ws_topbar($meName, $isLt, $isOwner);
        echo '<main class="wrap"><div class="card"><h1 style="font-size:20px;margin-bottom:8px">That comic is not in your workspace</h1>'
           . '<p class="muted">It may have been renamed or moved to another brand.</p><a class="btn primary" href="ws.php">← My comics</a></div></main></body></html>';
        exit;
    }
    $pname = (string)($project['name'] ?? $pid);
    $boot = ['view' => 'comic', 'pid' => $pid, 'csrf' => csrf(), 'uid' => $uid, 'name' => $meName, 'isLt' => $isLt];
    ws_ws_head($pname . ' · Workspace', $CSS);
    ws_ws_topbar($meName, $isLt, $isOwner);
    ?>
<main class="wrap ws-wrap">
  <?php ws_ws_howto(); ?>
  <section class="card ws-head">
    <div class="ws-title">
      <a class="ghost" href="ws.php">← My comics</a>
      <h1 id="hName"><?= h($pname) ?></h1>
      <span class="badge bbadge" id="hBrand"><?= h(ws_project_brand($pid) ?: 'no brand') ?></span>
      <span class="muted small" id="hStage"><?= h(str_replace('-', ' ', (string)($project['stage'] ?? ''))) ?></span>
    </div>
    <div class="ws-pills"><span class="pill" id="pQuota">🎨 …</span><span class="pill" id="pWorker">● …</span></div>
    <div class="ws-hbtns">
      <a class="btn" href="picker.php?p=<?= h(urlencode($pid)) ?>">🖼 Open picker</a>
      <button type="button" class="btn primary" id="bReady">✅ Ready for owner review</button>
    </div>
  </section>

  <div class="ws-cols">
    <div class="ws-left">
      <details class="card" id="storyCard">
        <summary>📜 Story &amp; style <span class="muted" id="storySum"></span></summary>
        <div class="story-grid">
          <label class="full">Story <span class="muted">(up to 20,000 characters)</span>
            <textarea id="fStory" maxlength="20000" placeholder="Paste or write the story here. Claude reads it when you ask it to plan pages."></textarea></label>
          <label>Style <span class="muted">(one or two lines, up to 600 characters)</span>
            <textarea id="fStyle" maxlength="600" rows="3" placeholder="e.g. glossy 3D render, warm gym lighting, cinematic angles"></textarea></label>
          <label>Page shape
            <select id="fAspect"><?php foreach (WS_WS_ASPECTS as $k => $v): ?><option value="<?= h($k) ?>"><?= h($v) ?></option><?php endforeach; ?></select></label>
          <div class="full"><button type="button" class="btn" id="bStorySave">💾 Save story &amp; style</button></div>
        </div>
      </details>

      <section class="card" id="pagesCard">
        <h2>📑 Pages <span class="muted" id="pagesCount"></span></h2>
        <p class="empty" id="pagesEmpty" hidden>No pages yet. Ask Claude to split the story into pages, or add one yourself.</p>
        <div id="pages"></div>
        <button type="button" class="btn" id="bAddPage">+ Add page</button>
      </section>

      <section class="card" id="refsCard">
        <h2>🧷 References <span class="muted" id="refsCount"></span></h2>
        <label class="dropzone" id="dropzone" for="refInput">
          <p><b>Drop character sheets, locations or source images here</b></p>
          <p class="small">or click to choose files · jpg, png, webp, gif · up to 30 MB each</p>
        </label>
        <input type="file" id="refInput" accept="image/jpeg,image/png,image/webp,image/gif" multiple hidden>
        <p class="empty" id="refsEmpty" hidden>No references yet. Each one gets a label you can edit; attach them to pages with “+ attach ref”.</p>
        <div class="ws-refs" id="refs"></div>
      </section>
    </div>

    <div class="ws-right">
      <section class="card" id="chatCard">
        <h2>💬 Chat <span class="muted">team + Claude</span></h2>
        <div class="chat-list" id="chatList" aria-live="polite">
          <p class="empty" id="chatEmpty">No messages yet. Say hi to the team, or ask Claude where to start.</p>
        </div>
        <div class="typing" id="typing" hidden><i></i><i></i><i></i> <span>Claude is thinking… this can take up to a minute.</span></div>
        <textarea id="chatText" maxlength="4000" placeholder="Message the team, or ask Claude (e.g. “Split the story into pages”)"></textarea>
        <div class="chat-btns">
          <button type="button" class="btn" id="bSend">Send</button>
          <button type="button" class="btn primary" id="bAsk">✨ Ask Claude</button>
          <span class="muted small" id="chatHint">Enter sends to the team · ⌘/Ctrl+Enter asks Claude · Shift+Enter for a new line</span>
        </div>
      </section>

      <section class="card" id="queueCard">
        <h2>⏳ Queue <span class="muted" id="queueCount"></span></h2>
        <p class="empty" id="queueEmpty">No jobs yet. Press Generate on a page.</p>
        <div id="queue"></div>
      </section>
    </div>
  </div>
</main>
<div id="toasts" aria-live="polite"></div>
<script type="application/json" id="wsboot"><?= json_encode($boot, JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT | JSON_UNESCAPED_UNICODE | JSON_INVALID_UTF8_SUBSTITUTE) ?></script>
<?php
} else {
// ---- 3) My comics -------------------------------------------------------------------------------
    $projects = array_values(array_filter(ws_projects_visible(), fn($p) => is_array($p) && ws_pid((string)($p['id'] ?? '')) !== ''));
    // workspace comics (brand assigned) first, archived last; otherwise keep projects.json order (newest first)
    $rank = function ($p) { $id = (string)$p['id']; return (($p['status'] ?? '') === 'archived' ? 2 : 0) + (ws_project_brand($id) === '' ? 1 : 0); };
    usort($projects, fn($a, $b) => $rank($a) <=> $rank($b));
    $brands = $isLt ? array_values(array_map('strval', (array)($person['brands'] ?? []))) : array_values(array_map('strval', ws_team()['brands']));
    $boot = ['view' => 'list', 'csrf' => csrf(), 'uid' => $uid, 'name' => $meName, 'isLt' => $isLt];
    ws_ws_head('My comics · Workspace', $CSS);
    ws_ws_topbar($meName, $isLt, $isOwner);
    ?>
<main class="wrap">
  <?php ws_ws_howto(); ?>
  <div class="pagehead"><h1>My comics <span class="muted"><?= count($projects) ?></span></h1>
    <?php if ($isOwner): ?><a class="btn sm" href="team.php">👥 Team &amp; links</a><?php endif; ?></div>

  <?php if ($brands): ?>
  <details class="card newproj"<?= $projects ? '' : ' open' ?>>
    <summary>+ New comic</summary>
    <form id="newForm" class="newform" autocomplete="off">
      <label>Name<input name="name" maxlength="120" required placeholder="e.g. Gym Rivals, Part 1"></label>
      <label>Brand<select name="brand" required><?php foreach ($brands as $b): ?><option value="<?= h($b) ?>"><?= h($b) ?></option><?php endforeach; ?></select></label>
      <label class="full">Style <span class="muted">(optional, you can change it later)</span><input name="style" maxlength="600" placeholder="e.g. glossy 3D render, warm gym lighting"></label>
      <div class="full"><button type="submit" class="btn primary">Create comic</button></div>
    </form>
  </details>
  <?php elseif ($isLt): ?>
  <p class="flash err">You don't have a brand yet, so you can't start a comic. Ask the owner to add one to your profile.</p>
  <?php endif; ?>

  <?php if (!$projects): ?>
    <p class="muted"><?= $isLt ? 'No comics for your brand yet. Start one with “+ New comic”.' : 'No projects yet.' ?></p>
  <?php else: ?>
    <?php if (count($projects) > 8): ?>
    <div class="ws-filter">
      <input type="search" id="fq" placeholder="Filter by name…" aria-label="Filter comics by name">
      <select id="fb" aria-label="Filter by brand"><option value="">All brands</option>
        <?php foreach (array_unique(array_map(fn($p) => ws_project_brand((string)$p['id']), $projects)) as $b): ?>
          <option value="<?= h($b === '' ? '-' : $b) ?>"><?= h($b === '' ? 'No brand' : $b) ?></option>
        <?php endforeach; ?></select>
      <span class="muted small" id="fcount"></span>
    </div>
    <?php endif; ?>
  <div class="grid">
    <?php foreach ($projects as $p):
        $id = (string)$p['id']; $nm = (string)($p['name'] ?? $id); $brand = ws_project_brand($id);
        [$pgN, $pkN] = ws_ws_counts($id);
        $cov = is_string($p['cover'] ?? null) && preg_match('/^[A-Za-z0-9._-]+$/', (string)$p['cover']) ? (string)$p['cover'] : '';
        $st = (string)($p['status'] ?? '');
    ?>
    <a class="pcard<?= $st === 'archived' ? ' archived' : '' ?>" href="ws.php?p=<?= h(urlencode($id)) ?>" data-name="<?= h(mb_strtolower($nm)) ?>" data-brand="<?= h($brand) ?>">
      <div class="pcover">
        <?php if ($cov !== ''): ?><img loading="lazy" src="img.php?p=<?= h(urlencode($id)) ?>&amp;f=<?= h(urlencode($cov)) ?>&amp;t=1" alt="">
        <?php else: ?><span class="pcover-empty"><?= h(mb_strtoupper(mb_substr($nm, 0, 2))) ?></span><?php endif; ?>
      </div>
      <div class="pmeta">
        <div class="pname"><?= h($nm) ?></div>
        <div class="prow">
          <span class="badge" style="--c:<?= h(ws_ws_status_color($st)) ?>"><?= h($st) ?></span>
          <span class="muted small"><?= h(str_replace('-', ' ', (string)($p['stage'] ?? ''))) ?></span>
        </div>
        <div class="prow"><span class="badge bbadge"><?= h($brand !== '' ? $brand : 'no brand') ?></span></div>
        <div class="muted psub"><?= $pgN < 0 ? 'Not set up in the workspace yet' : (h((string)$pgN) . ' page' . ($pgN === 1 ? '' : 's') . ' · ' . h((string)$pkN) . ' picked') ?></div>
      </div>
    </a>
    <?php endforeach; ?>
  </div>
  <?php endif; ?>
</main>
<div id="toasts" aria-live="polite"></div>
<script type="application/json" id="wsboot"><?= json_encode($boot, JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT | JSON_UNESCAPED_UNICODE | JSON_INVALID_UTF8_SUBSTITUTE) ?></script>
<?php } ?>
<script>
(function () {
  'use strict';
  var BOOT = {};
  try { BOOT = JSON.parse(document.getElementById('wsboot').textContent || '{}'); } catch (e) { BOOT = {}; }
  var CSRF = BOOT.csrf || '';
  var API = 'ws-api.php';
  var COARSE = !!(window.matchMedia && window.matchMedia('(pointer: coarse)').matches);

  // ---------- tiny DOM + net helpers (all text goes in via textContent / value) ----------
  function $(id) { return document.getElementById(id); }
  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = String(text); return e; }
  function button(label, cls, onClick, title) {
    var b = el('button', 'btn ' + (cls || ''), label); b.type = 'button';
    if (title) b.title = title;
    if (onClick) b.addEventListener('click', onClick);
    return b;
  }
  function plural(n, w) { n = n | 0; return n + ' ' + w + (n === 1 ? '' : 's'); }
  function ago(ts) {
    ts = +ts || 0; if (!ts) return '';
    var s = Math.max(0, Math.round(Date.now() / 1000 - ts));
    if (s < 45) return 'just now';
    if (s < 3600) return Math.round(s / 60) + ' min ago';
    if (s < 86400) return Math.round(s / 3600) + ' h ago';
    if (s < 7 * 86400) return Math.round(s / 86400) + ' d ago';
    return new Date(ts * 1000).toLocaleDateString();
  }
  function toast(msg, kind, ms) {
    var host = $('toasts'); if (!host) return null;
    var t = el('div', 'toast ' + (kind || ''), msg);
    t.setAttribute('role', kind === 'err' ? 'alert' : 'status');
    t.addEventListener('click', function () { t.remove(); });
    host.appendChild(t);
    if (ms !== 0) setTimeout(function () { t.remove(); }, ms || (kind === 'err' ? 9000 : 4000));
    while (host.children.length > 4) host.firstChild.remove();
    return t;
  }
  var signedOut = false;
  function apiUrl(params) { return API + '?' + new URLSearchParams(params).toString(); }
  async function call(method, params, body) {
    var opts = { method: method, credentials: 'same-origin', headers: { 'Accept': 'application/json' } };
    if (method === 'POST') { opts.headers['X-CSRF'] = CSRF; opts.body = body; }
    var r, j;
    try { r = await fetch(apiUrl(params), opts); }
    catch (e) { return { ok: false, error: 'Network problem. Check your connection and try again.' }; }
    try { j = await r.json(); } catch (e) { j = { ok: false, error: 'The server answered oddly (' + r.status + '). Try again.' }; }
    if (!j || typeof j !== 'object') j = { ok: false, error: 'Empty answer from the server.' };
    if (r.status === 401 && !signedOut) { signedOut = true; toast('You are signed out. Open your private link again (staff: sign in).', 'err', 0); }
    return j;
  }
  function toForm(data) {
    var fd = new FormData();
    Object.keys(data || {}).forEach(function (k) {
      var v = data[k];
      if (Array.isArray(v)) { if (!v.length) fd.append(k, ''); v.forEach(function (x) { fd.append(k + '[]', x); }); }
      else if (v != null) fd.append(k, String(v));
    });
    return fd;
  }
  function post(doName, data, fd) {
    var params = { do: doName }; if (BOOT.pid) params.p = BOOT.pid;
    var body = fd || toForm(data);
    body.append('csrf', CSRF);                       // also keeps $_POST non-empty
    return call('POST', params, body);
  }
  function get(doName, extra) { return call('GET', Object.assign({ do: doName, p: BOOT.pid }, extra || {})); }

  // ---------- "How it works" ----------
  var howBtn = $('howBtn'), how = $('howto');
  function setHow(open) {
    if (!how) return;
    how.hidden = !open;
    if (howBtn) howBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
    try { localStorage.setItem('ws-howto', open ? '1' : '0'); } catch (e) { /* storage off */ }
  }
  if (howBtn && how) {
    howBtn.addEventListener('click', function () { setHow(how.hidden); if (!how.hidden) how.scrollIntoView({ behavior: 'smooth', block: 'start' }); });
    if ($('howClose')) $('howClose').addEventListener('click', function () { setHow(false); });
    var savedHow = null; try { savedHow = localStorage.getItem('ws-howto'); } catch (e) { savedHow = null; }
    if (savedHow === '1') setHow(true);
  }

  if (BOOT.view === 'list') { initList(); return; }
  if (BOOT.view === 'comic') { initComic(); }

  // =====================================================================================
  function initList() {
    var f = $('newForm');
    if (f) f.addEventListener('submit', async function (ev) {
      ev.preventDefault();
      var b = f.querySelector('button[type=submit]'); b.disabled = true;
      var j = await post('create', null, new FormData(f));
      b.disabled = false;
      if (j.ok && j.id) { location.href = 'ws.php?p=' + encodeURIComponent(j.id); return; }
      toast(j.error || 'Could not create the comic.', 'err');
    });
    var qi = $('fq'), bs = $('fb');
    var cards = Array.prototype.slice.call(document.querySelectorAll('.pcard[data-name]'));
    function apply() {
      var q = (qi ? qi.value : '').trim().toLowerCase(), b = bs ? bs.value : '', shown = 0;
      cards.forEach(function (c) {
        var ok = (!q || c.getAttribute('data-name').indexOf(q) >= 0)
              && (!b || (b === '-' ? c.getAttribute('data-brand') === '' : c.getAttribute('data-brand') === b));
        c.classList.toggle('hide', !ok); if (ok) shown++;
      });
      if ($('fcount')) $('fcount').textContent = (q || b) ? shown + ' shown' : '';
    }
    if (qi) qi.addEventListener('input', apply);
    if (bs) bs.addEventListener('change', apply);
  }

  // =====================================================================================
  function initComic() {
    var PID = BOOT.pid;
    var S = null, rows = {}, refTiles = {}, chatNodes = {}, chatJson = {}, chatMsgs = {}, chatLast = 0;
    var lastRest = '', lastChat = '', firstState = true, storyDirty = false, aiBusy = false;
    var STATUS_LABEL = { queued: 'Queued', running: 'Generating', done: 'Landed', failed: 'Failed', error: 'Error', cancelled: 'Cancelled' };
    var KIND_ICON = { set_prompt: '✏️', add_pages: '➕', generate: '🎨' };
    var IMG_RE = /\.(jpe?g|png|webp|gif)$/i;
    var MAX_FILE = 30 * 1024 * 1024;

    function imgUrl(f, thumb) { return 'img.php?p=' + encodeURIComponent(PID) + '&f=' + encodeURIComponent(f) + (thumb ? '&t=1' : ''); }
    function pickerUrl(group) { return 'picker.php?p=' + encodeURIComponent(PID) + (group ? '#page=' + encodeURIComponent(group) : ''); }
    function maxT() { return (S && S.settings && S.settings.maxTakes) || 4; }

    // ---------- state ----------
    var stateSeq = 0;
    async function loadState() {
      var seq = ++stateSeq;
      var j = await get('state');
      if (seq !== stateSeq) return;                  // a newer load is on its way
      if (!j.ok) { if (!signedOut) toast(j.error || 'Could not load this comic.', 'err'); return; }
      S = j;
      if (j.sigs && j.sigs.rest) lastRest = j.sigs.rest;
      render();
    }
    function render() { renderHead(); renderStory(); renderPages(); renderRefs(); renderQueue(); firstState = false; }

    function renderHead() {
      var p = S.project || {};
      $('hName').textContent = p.name || PID;
      document.title = (p.name || PID) + ' · Workspace';
      $('hBrand').textContent = p.brand || 'no brand';
      $('hStage').textContent = p.stage === 'review' ? 'waiting for owner review' : String(p.stage || '').replace(/-/g, ' ');
      var q = S.quota || {}, qp = $('pQuota'), left = q.left | 0;
      qp.textContent = S.me && S.me.isLt ? '🎨 ' + left + ' of ' + (q.cap | 0) + ' images left today' : '🎨 ' + left + ' studio images left today';
      qp.className = 'pill' + (left > 5 ? '' : (left > 0 ? ' warn' : ' bad'));
      var alive = !!(S.worker && S.worker.alive), wp = $('pWorker');
      wp.textContent = alive ? '● Generator online' : '● Generator offline — jobs wait in the queue';
      wp.className = 'pill ' + (alive ? 'ok' : 'warn');
      $('bReady').textContent = p.stage === 'review' ? '✅ Sent for owner review' : '✅ Ready for owner review';
    }

    // ---------- story & style ----------
    function renderStory() {
      var st = $('fStory'), sy = $('fStyle'), as = $('fAspect'), pr = S.proj || {};
      if (!storyDirty) {
        if (document.activeElement !== st) st.value = pr.story || '';
        if (document.activeElement !== sy) sy.value = pr.style || '';
        if (document.activeElement !== as) as.value = pr.aspect || '3:4';
      }
      var words = (pr.story || '').trim() ? (pr.story || '').trim().split(/\s+/).length : 0;
      $('storySum').textContent = (words ? words + ' words' : 'no story yet') + ' · ' + (pr.style ? 'style set' : 'no style yet') + ' · ' + (pr.aspect || '3:4');
      if (firstState && !words) $('storyCard').open = true;
    }
    function storyMark() { storyDirty = true; $('bStorySave').classList.add('primary'); }
    ['fStory', 'fStyle'].forEach(function (id) { $(id).addEventListener('input', storyMark); });
    $('fAspect').addEventListener('change', storyMark);
    $('bStorySave').addEventListener('click', async function () {
      var b = $('bStorySave'), sent = { story: $('fStory').value, style: $('fStyle').value, aspect: $('fAspect').value };
      b.disabled = true;
      var j = await post('setproj', sent);
      b.disabled = false;
      if (!j.ok) { toast(j.error || 'Could not save.', 'err'); return; }
      if ($('fStory').value === sent.story && $('fStyle').value === sent.style && $('fAspect').value === sent.aspect) { storyDirty = false; b.classList.remove('primary'); }
      toast('Story & style saved.', 'ok');
      loadState();
    });

    // ---------- pages ----------
    function makeRow(n) {
      var r = { n: n, dirty: false, pg: { refs: [] }, thumbKey: null };
      r.root = el('div', 'pg'); r.root.id = 'page-' + n;
      var head = el('div', 'pg-head');
      r.label = el('span', 'pg-n', 'Page ' + n);
      r.title = el('input', 'pg-title'); r.title.maxLength = 120; r.title.placeholder = 'Page title (optional)';
      r.title.setAttribute('aria-label', 'Page ' + n + ' title');
      r.badge = el('span', 'pg-badge');
      head.append(r.label, r.title, r.badge);
      r.prompt = el('textarea', 'pg-prompt'); r.prompt.rows = 4; r.prompt.maxLength = 2500;
      r.prompt.placeholder = 'What happens on this page: action, camera/shot, setting, lighting, emotion, dialogue. The refs carry how people look.';
      r.prompt.setAttribute('aria-label', 'Page ' + n + ' prompt');
      var refsRow = el('div', 'pg-refs');
      r.chips = el('span', 'chips');
      r.attach = el('select', 'pg-attach'); r.attach.setAttribute('aria-label', 'Attach a reference to page ' + n);
      refsRow.append(r.chips, r.attach);
      r.stats = el('div', 'pg-stats');
      r.thumbs = el('div', 'pg-thumbs');
      r.comment = el('div', 'pg-comment'); r.comment.hidden = true;
      var btns = el('div', 'pg-btns');
      r.save = button('💾 Save', 'sm', function () { savePage(r, false); });
      r.gen2 = button('🎨 Generate ×2', 'sm', function () { generate(r, Math.min(2, maxT())); });
      r.gen4 = button('🎨 Generate ×4', 'sm', function () { generate(r, Math.min(4, maxT())); });
      r.file = el('input'); r.file.type = 'file'; r.file.multiple = true; r.file.accept = 'image/jpeg,image/png,image/webp,image/gif'; r.file.hidden = true;
      r.file.addEventListener('change', function () { var fs = Array.prototype.slice.call(r.file.files || []); r.file.value = ''; if (fs.length) uploadFiles(fs, 'take', r.n); });
      r.up = button('⬆ Upload takes', 'sm', function () { r.file.click(); }, 'Add takes you made elsewhere to this page');
      r.del = button('🗑', 'sm danger', function () { deletePage(r); }, 'Delete this page from the list (its images stay in the studio)');
      var sp = el('span', 'spacer');
      btns.append(r.save, r.gen2, r.gen4, r.up, r.file, sp, r.del);
      r.root.append(head, r.prompt, refsRow, r.stats, r.thumbs, r.comment, btns);
      function mark() { r.dirty = true; r.root.classList.add('dirty'); r.save.classList.add('primary'); updateGen(r); }
      r.title.addEventListener('input', mark);
      r.prompt.addEventListener('input', mark);
      r.prompt.addEventListener('keydown', function (e) { if (e.key === 's' && (e.metaKey || e.ctrlKey)) { e.preventDefault(); savePage(r, false); } });
      r.attach.addEventListener('change', function () {
        var f = r.attach.value; r.attach.value = '';
        if (f) setPageRefs(r, (r.pg.refs || []).concat([f]));
      });
      return r;
    }
    function updateGen(r) {
      var has = r.prompt.value.trim() !== '', left = S && S.quota ? (S.quota.left | 0) : 99, mt = maxT();
      r.gen2.textContent = '🎨 Generate ×' + Math.min(2, mt);
      r.gen4.textContent = '🎨 Generate ×' + Math.min(4, mt);
      r.gen4.hidden = mt <= 2;
      [r.gen2, r.gen4].forEach(function (b) {
        b.disabled = !has || left <= 0;
        b.title = !has ? 'Write a prompt first' : (left <= 0 ? 'No images left today' : 'Queue new takes of this page');
      });
    }
    function updateRow(r, pg) {
      r.pg = pg;
      if (!r.dirty) {
        if (document.activeElement !== r.title) r.title.value = pg.title || '';
        if (document.activeElement !== r.prompt) r.prompt.value = pg.prompt || '';
      }
      var refMap = {}; (S.refs || []).forEach(function (x) { refMap[x.file] = x; });
      r.chips.replaceChildren();
      (pg.refs || []).forEach(function (f) {
        var ref = refMap[f], c = el('span', 'chip');
        c.title = ref ? (ref.label || f) : f + ' (removed)';
        var im = el('img'); im.alt = ''; im.loading = 'lazy'; im.src = imgUrl(f, true);
        var x = el('button', null, '✕'); x.type = 'button'; x.title = 'Detach from this page';
        x.addEventListener('click', function () { setPageRefs(r, (r.pg.refs || []).filter(function (y) { return y !== f; })); });
        c.append(im, el('span', null, ref ? (ref.label || 'ref') : 'removed ref'), x);
        r.chips.appendChild(c);
      });
      if (document.activeElement !== r.attach) {
        var avail = (S.refs || []).filter(function (x) { return (pg.refs || []).indexOf(x.file) < 0; });
        r.attach.replaceChildren();
        var o0 = el('option', null, avail.length ? '+ attach ref…' : ((S.refs || []).length ? 'all refs attached' : 'no refs uploaded yet'));
        o0.value = ''; r.attach.appendChild(o0);
        avail.forEach(function (x) { var o = el('option', null, x.label || x.file); o.value = x.file; r.attach.appendChild(o); });
        r.attach.disabled = !avail.length;
      }
      var parts = [plural(pg.takes, 'take')];
      if (pg.picked) parts.push(pg.picked + ' picked ✓'); else if (pg.dropped) parts.push('dropped'); else if (pg.takes) parts.push('no pick yet');
      if (pg.lastTs) parts.push('newest ' + ago(pg.lastTs));
      r.stats.textContent = parts.join(' · ');
      r.badge.textContent = pg.picked ? '✓ picked' : (pg.dropped ? 'dropped' : (pg.takes ? 'needs a pick' : (pg.prompt ? 'ready to generate' : 'needs a prompt')));
      r.badge.className = 'pg-badge' + (pg.picked ? ' ok' : (pg.takes || !pg.prompt ? ' warn' : ''));
      var key = (pg.thumbs || []).join(',') + '|' + (pg.pickFiles || []).join(',') + '|' + pg.takes;
      if (r.thumbKey !== key) {
        r.thumbKey = key; r.thumbs.replaceChildren();
        (pg.thumbs || []).forEach(function (f) {
          var a = el('a'); a.href = pickerUrl(pg.group); a.target = '_blank'; a.rel = 'noopener'; a.title = 'Open page ' + pg.n + ' in the picker';
          if ((pg.pickFiles || []).indexOf(f) >= 0) a.className = 'picked';
          var im = el('img'); im.alt = 'Take'; im.loading = 'lazy'; im.src = imgUrl(f, true);
          a.appendChild(im); r.thumbs.appendChild(a);
        });
        var extra = (pg.takes | 0) - (pg.thumbs || []).length;
        if (extra > 0) { var more = el('a', null, '+' + extra); more.href = pickerUrl(pg.group); more.target = '_blank'; more.rel = 'noopener'; more.title = 'See every take in the picker'; r.thumbs.appendChild(more); }
      }
      r.comment.hidden = !pg.comment;
      r.comment.textContent = pg.comment ? '💬 ' + pg.comment : '';
      updateGen(r);
    }
    function renderPages() {
      var host = $('pages'), seen = {}, pages = S.pages || [];
      pages.forEach(function (pg, i) {
        var r = rows[pg.n]; if (!r) { r = makeRow(pg.n); rows[pg.n] = r; }
        seen[pg.n] = 1; updateRow(r, pg);
        if (host.children[i] !== r.root) host.insertBefore(r.root, host.children[i] || null);   // only move when the order changed
      });
      Object.keys(rows).forEach(function (n) { if (!seen[n]) { rows[n].root.remove(); delete rows[n]; } });
      $('pagesEmpty').hidden = pages.length > 0;
      var done = pages.filter(function (p) { return p.picked > 0 || p.dropped; }).length;
      $('pagesCount').textContent = pages.length ? plural(pages.length, 'page') + ' · ' + done + ' picked' : '';
    }
    async function savePage(r, quiet) {
      var sent = { n: r.n, title: r.title.value, prompt: r.prompt.value };
      r.save.disabled = true;
      var j = await post('page_save', sent);
      r.save.disabled = false;
      if (!j.ok) { toast(j.error || 'Could not save the page.', 'err'); return false; }
      if (r.title.value === sent.title && r.prompt.value === sent.prompt) { r.dirty = false; r.root.classList.remove('dirty'); r.save.classList.remove('primary'); }
      if (!quiet) toast('Page ' + r.n + ' saved.', 'ok');
      loadState();
      return true;
    }
    async function generate(r, takes) {
      if (r.dirty && !(await savePage(r, true))) return;
      r.gen2.disabled = true; r.gen4.disabled = true;
      var j = await post('generate', { page: r.n, takes: takes });
      updateGen(r);
      if (!j.ok) { toast(j.error || 'Could not queue that.', 'err'); return; }
      toast('Queued ' + plural(j.job.takes, 'take') + ' of page ' + r.n + (j.left >= 0 ? ' · ' + j.left + ' left today' : '') + '.', 'ok');
      loadState();
    }
    async function setPageRefs(r, list) {
      r.pg.refs = list;
      var j = await post('page_save', { n: r.n, refs: list });
      if (!j.ok) toast(j.error || 'Could not update the refs.', 'err');
      loadState();
    }
    async function deletePage(r) {
      if (!confirm('Delete page ' + r.n + ' from the list? Its takes stay in the studio.')) return;
      var j = await post('page_delete', { n: r.n });
      if (!j.ok) { toast(j.error || 'Could not delete the page.', 'err'); return; }
      toast('Page ' + r.n + ' removed.', 'ok');
      loadState();
    }
    $('bAddPage').addEventListener('click', async function () {
      var b = $('bAddPage'); b.disabled = true;
      var j = await post('page_save', { n: 0, title: '', prompt: '' });
      b.disabled = false;
      if (!j.ok) { toast(j.error || 'Could not add a page.', 'err'); return; }
      await loadState();
      var r = rows[j.n];
      if (!r) { await new Promise(function (res) { setTimeout(res, 700); }); r = rows[j.n]; }
      if (r) { r.root.scrollIntoView({ behavior: 'smooth', block: 'center' }); r.prompt.focus({ preventScroll: true }); }
    });

    // ---------- refs ----------
    function makeRefTile(file) {
      var t = { file: file, dirty: false };
      t.root = el('div', 'ref');
      var a = el('a'); a.href = imgUrl(file, false); a.target = '_blank'; a.rel = 'noopener'; a.title = 'Open full size';
      var im = el('img'); im.alt = ''; im.loading = 'lazy'; im.src = imgUrl(file, true); a.appendChild(im);
      t.input = el('input'); t.input.maxLength = 80; t.input.placeholder = 'Label, e.g. Andrea sheet'; t.input.setAttribute('aria-label', 'Reference label');
      t.input.addEventListener('input', function () { t.dirty = true; });
      t.input.addEventListener('keydown', function (e) { if (e.key === 'Enter') { e.preventDefault(); t.input.blur(); } });
      t.input.addEventListener('change', async function () {
        var j = await post('ref_update', { file: file, label: t.input.value });
        if (!j.ok) { toast(j.error || 'Could not rename the ref.', 'err'); return; }
        t.dirty = false; loadState();
      });
      var rm = el('button', 'rm', '✕'); rm.type = 'button'; rm.title = 'Remove from this comic (the image stays in the studio)';
      rm.addEventListener('click', async function () {
        if (!confirm('Remove this reference from the workspace? It is also detached from every page. The image itself stays in the studio.')) return;
        var j = await post('ref_remove', { file: file });
        if (!j.ok) { toast(j.error || 'Could not remove the ref.', 'err'); return; }
        loadState();
      });
      t.root.append(a, rm, t.input);
      return t;
    }
    function renderRefs() {
      var host = $('refs'), seen = {}, refs = S.refs || [];
      refs.forEach(function (rf, i) {
        var t = refTiles[rf.file]; if (!t) { t = makeRefTile(rf.file); refTiles[rf.file] = t; }
        seen[rf.file] = 1;
        if (!t.dirty && document.activeElement !== t.input) t.input.value = rf.label || '';
        if (host.children[i] !== t.root) host.insertBefore(t.root, host.children[i] || null);
      });
      Object.keys(refTiles).forEach(function (f) { if (!seen[f]) { refTiles[f].root.remove(); delete refTiles[f]; } });
      $('refsEmpty').hidden = refs.length > 0;
      $('refsCount').textContent = refs.length ? String(refs.length) : '';
    }
    async function uploadFiles(files, kind, page) {
      var okFiles = [], skipped = [];
      files.forEach(function (f) { if (!IMG_RE.test(f.name)) skipped.push(f.name + ': not an image'); else if (f.size > MAX_FILE) skipped.push(f.name + ': too large'); else okFiles.push(f); });
      if (skipped.length) toast('Skipped ' + skipped.slice(0, 3).join(' · ') + (skipped.length > 3 ? ' (+' + (skipped.length - 3) + ' more)' : ''), 'err');
      if (!okFiles.length) return;
      var batches = [], cur = [], size = 0;
      okFiles.forEach(function (f) {
        if (cur.length && (cur.length >= 8 || size + f.size > 40 * 1024 * 1024)) { batches.push(cur); cur = []; size = 0; }
        cur.push(f); size += f.size;
      });
      if (cur.length) batches.push(cur);
      var prog = toast('Uploading ' + plural(okFiles.length, 'file') + '…', '', 0), done = 0, errs = [];
      for (var i = 0; i < batches.length; i++) {
        var fd = new FormData(); fd.append('kind', kind); if (page) fd.append('page', String(page));
        batches[i].forEach(function (f) { fd.append('files[]', f, f.name); });
        var j = await post('upload', null, fd);
        done += (j.files || []).length;
        (j.errors || []).forEach(function (e) { errs.push(e); });
        if (!j.ok && !(j.errors || []).length && j.error) errs.push(j.error);
      }
      if (prog) prog.remove();
      if (done) toast('Uploaded ' + plural(done, kind === 'take' ? 'take' : 'reference') + (page ? ' for page ' + page : '') + '.', 'ok');
      if (errs.length) toast(errs.slice(0, 3).join(' · ') + (errs.length > 3 ? ' (+' + (errs.length - 3) + ' more)' : ''), 'err', 12000);
      loadState();
    }
    var dz = $('dropzone'), rin = $('refInput');
    ['dragenter', 'dragover'].forEach(function (ev) { dz.addEventListener(ev, function (e) { e.preventDefault(); dz.classList.add('drag'); }); });
    ['dragleave', 'drop'].forEach(function (ev) { dz.addEventListener(ev, function (e) { e.preventDefault(); dz.classList.remove('drag'); }); });
    dz.addEventListener('drop', function (e) { var fs = Array.prototype.slice.call((e.dataTransfer && e.dataTransfer.files) || []); if (fs.length) uploadFiles(fs, 'ref', 0); });
    rin.addEventListener('change', function () { var fs = Array.prototype.slice.call(rin.files || []); rin.value = ''; if (fs.length) uploadFiles(fs, 'ref', 0); });
    // a file dropped anywhere else must not navigate away from unsaved work
    window.addEventListener('dragover', function (e) { e.preventDefault(); });
    window.addEventListener('drop', function (e) { e.preventDefault(); });

    // ---------- queue ----------
    function renderQueue() {
      var host = $('queue'), jobs = S.jobs || [];
      host.replaceChildren();
      $('queueEmpty').hidden = jobs.length > 0;
      var active = jobs.filter(function (j) { return j.status === 'queued' || j.status === 'running'; }).length;
      $('queueCount').textContent = active ? active + ' active' : '';
      jobs.forEach(function (j) {
        var row = el('div', 'job');
        row.appendChild(el('span', 'jst ' + j.status, STATUS_LABEL[j.status] || j.status));
        row.appendChild(el('b', null, 'Page ' + j.page));
        var prog = plural(j.takes, 'take');
        if (j.done || j.failed) prog += ' · ' + j.done + ' landed' + (j.failed ? ' · ' + j.failed + ' failed' : '');
        if (j.stopRequested && j.status === 'running') prog += ' · stopping…';
        row.appendChild(el('span', null, prog));
        var who = el('span', 'muted small', (j.by || '') + ' · ' + ago(j.ts)); who.setAttribute('data-ago', j.ts); who.setAttribute('data-pre', (j.by || '') + ' · ');
        row.appendChild(who);
        if (j.canCancel) {
          row.appendChild(el('span', 'spacer'));
          var cb = button('Cancel', 'sm', null, j.status === 'running' ? 'Stops after the current take' : 'Remove from the queue (your images come back)');
          cb.addEventListener('click', async function () {
            if (!confirm(j.status === 'running' ? 'Stop this job after the current take? Takes already made stay.' : 'Cancel this job? The images go back to today’s allowance.')) return;
            cb.disabled = true;
            var r = await post('cancel', { job: j.id });
            if (!r.ok) toast(r.error || 'Could not cancel.', 'err'); else toast('Cancelled.', 'ok');
            loadState();
          });
          row.appendChild(cb);
        }
        if (j.note) row.appendChild(el('span', 'muted small jnote', j.note));
        host.appendChild(row);
      });
    }

    // ---------- ready for review ----------
    $('bReady').addEventListener('click', async function () {
      if (!S) return;
      var pages = S.pages || [], open = pages.filter(function (p) { return !(p.picked > 0 || p.dropped); }).length;
      var msg = !pages.length ? 'This comic has no pages yet. Tell the owner it is ready anyway?'
              : open ? open + ' of ' + plural(pages.length, 'page') + ' have no pick yet. Tell the owner it is ready anyway?'
              : 'Tell the owner this comic is ready for review? Nothing gets published; the owner decides.';
      if (!confirm(msg)) return;
      var j = await post('ready', {});
      if (!j.ok) { toast(j.error || 'Could not mark it ready.', 'err'); return; }
      toast(j.stage === 'review' ? 'Sent. The owner will review it.' : 'This comic is already past review.', 'ok');
      loadState(); fetchChat(false);
    });

    // ---------- chat ----------
    var list = $('chatList');
    function nearBottom() { return list.scrollHeight - list.scrollTop - list.clientHeight < 90; }
    function scrollChat() { list.scrollTop = list.scrollHeight; }
    function actionCard(m, a) {
      var st = a.status || 'pending', args = a.args || {};
      var c = el('div', 'act ' + st);
      c.appendChild(el('div', 'act-sum', (KIND_ICON[a.kind] || '•') + ' ' + (a.summary || a.kind || 'Action')));
      if (a.kind === 'set_prompt' && args.prompt) {
        var d = el('details'); d.appendChild(el('summary', null, 'Show the full prompt')); d.appendChild(el('pre', null, args.prompt)); c.appendChild(d);
      }
      if (a.kind === 'add_pages' && args.pages && args.pages.length) {
        var d2 = el('details'); d2.appendChild(el('summary', null, 'Show the ' + plural(args.pages.length, 'page')));
        d2.appendChild(el('pre', null, args.pages.map(function (p, i) { return (i + 1) + '. ' + (p.title || '(untitled)') + (p.prompt ? '\n' + p.prompt : ''); }).join('\n\n')));
        c.appendChild(d2);
      }
      if (st === 'pending') {
        if (Date.now() / 1000 - (+m.ts || 0) > 86400) { c.appendChild(el('div', 'act-status', 'Expired (older than a day). Ask Claude again.')); return c; }
        var bs = el('div', 'act-btns');
        var yes = button('✔ Confirm', 'sm primary', function () { decide(m.id, a.aid, 'confirm', bs); });
        var no = button('Dismiss', 'sm', function () { decide(m.id, a.aid, 'dismiss', bs); });
        bs.append(yes, no); c.appendChild(bs);
      } else {
        var who = a.decidedBy || 'someone';
        var txt = st === 'working' ? '⏳ Working…'
                : st === 'confirmed' ? '✔ Confirmed by ' + who + (a.result ? ' — ' + a.result : '')
                : st === 'dismissed' ? '✖ Dismissed by ' + who
                : '⚠ Failed' + (a.result ? ': ' + a.result : '');
        c.appendChild(el('div', 'act-status', txt));
      }
      return c;
    }
    function msgNode(m) {
      var role = m.role === 'ai' ? 'ai' : (m.role === 'system' ? 'system' : 'user');
      var root = el('div', 'msg msg-' + role + (role === 'user' && m.uid && m.uid === BOOT.uid ? ' mine' : ''));
      if (role !== 'system') {
        var meta = el('div', 'msg-meta');
        meta.appendChild(el('b', null, role === 'ai' ? '✨ Claude' : (m.by || 'Someone')));
        if (role === 'user' && m.ai) meta.appendChild(el('span', 'askd', 'asked Claude'));
        var t = el('span', 'ts', ago(m.ts)); t.setAttribute('data-ago', m.ts); meta.appendChild(t);
        root.appendChild(meta);
      }
      var body = el('div', 'msg-text', m.text || '');
      if (role === 'system') { var t2 = el('span', 'ts', ago(m.ts)); t2.setAttribute('data-ago', m.ts); body.appendChild(t2); }
      root.appendChild(body);
      (m.actions || []).forEach(function (a) { if (a && typeof a === 'object') root.appendChild(actionCard(m, a)); });
      return root;
    }
    function renderMsg(m) {
      var id = m && (m.id | 0); if (!id) return;
      var js = JSON.stringify(m);
      if (chatJson[id] === js) return;
      var node = msgNode(m), old = chatNodes[id];
      if (old) old.replaceWith(node);
      else {
        var after = null;
        Object.keys(chatNodes).forEach(function (k) { k = +k; if (k > id && (!after || k < after)) after = k; });
        list.insertBefore(node, after ? chatNodes[after] : null);
      }
      chatNodes[id] = node; chatJson[id] = js; chatMsgs[id] = m;
      if (id > chatLast) chatLast = id;
      $('chatEmpty').hidden = true;
    }
    function updateTyping() {
      var show = aiBusy;
      if (!show && chatLast) {
        var m = chatMsgs[chatLast];
        show = !!(m && m.role === 'user' && m.ai && Date.now() / 1000 - (+m.ts || 0) < 120);
      }
      $('typing').hidden = !show;
    }
    var chatBusy = false, chatAgain = false;
    async function fetchChat(initial) {
      if (chatBusy) { chatAgain = true; return; }
      chatBusy = true;
      try {
        var since = chatLast, now = Date.now() / 1000;
        // re-read from the oldest live card, so a card decided by a teammate updates here too
        Object.keys(chatMsgs).forEach(function (k) {
          var m = chatMsgs[k];
          if (now - (+m.ts || 0) > 86400) return;
          if ((m.actions || []).some(function (a) { return a && (a.status === 'pending' || a.status === 'working'); })) since = Math.min(since, (+k) - 1);
        });
        var near = nearBottom();
        var j = await get('chat', { since: Math.max(0, since) });
        if (!j.ok) return;
        (j.msgs || []).forEach(renderMsg);
        if (initial || near) scrollChat();
        updateTyping();
      } finally {
        chatBusy = false;
        if (chatAgain) { chatAgain = false; fetchChat(false); }
      }
    }
    async function decide(mid, aid, decision, bs) {
      Array.prototype.forEach.call(bs.querySelectorAll('button'), function (b) { b.disabled = true; });
      var j = await post('action', { msg: mid, aid: aid, decision: decision });
      if (j.msg) renderMsg(j.msg);
      (j.msgs || []).forEach(renderMsg);
      if (!j.ok) {
        toast(j.error || 'That did not work.', 'err');
        if (!j.msg) Array.prototype.forEach.call(bs.querySelectorAll('button'), function (b) { b.disabled = false; });
      } else if (j.result) toast(j.result, 'ok');
      scrollChat();
      loadState();
    }
    async function send(ai) {
      var ta = $('chatText'), text = ta.value.trim();
      if (!text) { ta.focus(); return; }
      if (text.length > 4000) { toast('That message is too long (4000 characters max).', 'err'); return; }
      if (ai && aiBusy) { toast('Claude is still answering the last question.', 'err'); return; }
      ta.value = '';
      if (ai) { aiBusy = true; $('bAsk').disabled = true; updateTyping(); }
      var j;
      try { j = await post('chat_send', { text: text, ai: ai ? 1 : 0 }); }
      finally { if (ai) { aiBusy = false; $('bAsk').disabled = false; } }
      if (!j.ok) { if (!ta.value) ta.value = text; toast(j.error || 'Message not sent.', 'err'); updateTyping(); return; }
      (j.msgs || []).forEach(renderMsg);
      scrollChat(); updateTyping();
      if (j.error) toast(j.error, 'err');
    }
    $('bSend').addEventListener('click', function () { send(false); });
    $('bAsk').addEventListener('click', function () { send(true); });
    $('chatText').addEventListener('keydown', function (e) {
      if (e.key !== 'Enter' || e.isComposing) return;
      if (e.metaKey || e.ctrlKey) { e.preventDefault(); send(true); return; }
      if (e.shiftKey || e.altKey || COARSE) return;      // phones: Enter is a new line, use the buttons
      e.preventDefault(); send(false);
    });
    if (COARSE) $('chatHint').textContent = 'Send goes to the team · Ask Claude gets Claude to answer';

    // ---------- live refresh ----------
    var pingBusy = false;
    async function ping() {
      if (document.hidden || signedOut || pingBusy) return;
      pingBusy = true;
      try {
        var j = await get('ping');
        if (!j.ok) return;
        var rest = j.rest || j.sig, chat = j.chat || j.sig;
        if (rest && rest !== lastRest) { lastRest = rest; loadState(); }
        if (chat && chat !== lastChat) { lastChat = chat; fetchChat(false); }
      } finally { pingBusy = false; }
    }
    setInterval(ping, 5000);
    document.addEventListener('visibilitychange', function () { if (!document.hidden) ping(); });
    setInterval(function () {
      Array.prototype.forEach.call(document.querySelectorAll('[data-ago]'), function (e) { e.textContent = (e.getAttribute('data-pre') || '') + ago(e.getAttribute('data-ago')); });
      updateTyping();
    }, 30000);
    window.addEventListener('beforeunload', function (e) {
      var dirty = storyDirty || $('chatText').value.trim() !== '' || Object.keys(rows).some(function (n) { return rows[n].dirty; });
      if (dirty) { e.preventDefault(); e.returnValue = ''; }
    });

    loadState();
    fetchChat(true);
  }
})();
</script>
</body></html>
