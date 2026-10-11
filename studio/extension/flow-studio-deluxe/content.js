// 3DMC Studio Tools — Flow content script (UI). One panel, two modes (Creator /
// Advanced — see uiMode below), all actions driven
// off FlowCore's single tRPC harvest: Download (disk) / Send to Studio (ingest) /
// Review bundle (outputs + refs + manifest) / Bulk delete (guarded, via FlowDelete).
(() => {
  if (window.__flowStudioTools) return;
  window.__flowStudioTools = true;
  const FC = self.FlowCore;
  if (!FC) { console.error("[3DMC Studio Tools] core missing"); return; }
  // Flavor: the manifest name decides. "Flow Studio Deluxe" is built from this same source
  // by ../build_deluxe.py — the owner/staff build: always the full panel, no Creator/Advanced
  // switch, Patreon downloader always on. If BOTH flavors are installed, two panels would fight
  // over the composer, so whichever content script lands first keeps the page.
  const DELUXE = /deluxe/i.test((chrome.runtime.getManifest && chrome.runtime.getManifest().name) || "");
  if (document.getElementById("fst")) { console.warn("[3DMC Studio Tools] a 3DMC panel is already on this page — both Studio Tools and Deluxe installed? Skipping this one."); return; }
  const DEFAULT_URL = "https://3dmusclecomics.com/studio/bridge.php";
  let cfg = { url: DEFAULT_URL, key: "" };
  let mode = "download", prevMode = "download";

  function defaultProject() { let t = (document.title || "").replace(/[\\/:*?"<>|]+/g, " ").replace(/\s*[-–|].*$/, "").trim(); return (t || "Flow import").slice(0, 60); }
  function folderName() { const m = location.pathname.match(/project\/([0-9a-f-]+)/i); const id = m ? m[1].slice(0, 8) : "project"; let t = (document.title || "").replace(/[\\/:*?"<>|]+/g, " ").trim() || "Flow"; return ("Flow " + t + " " + id).replace(/\s+/g, " ").slice(0, 80); }

  const css = `
   #fst{position:fixed;right:20px;bottom:20px;z-index:2147483647;width:340px;background:#14151c;color:#e8eaed;border-radius:12px;box-shadow:0 8px 30px rgba(0,0,0,.55);font:13px system-ui,sans-serif;overflow:hidden;border:1px solid #2e3140}
   #fst .hd{display:flex;align-items:center;gap:8px;padding:10px 12px;background:#191b24;cursor:move;user-select:none}
   #fst .hd b{flex:1;font-size:13px} #fst .hd span{cursor:pointer;opacity:.7;padding:2px 6px;border-radius:6px} #fst .hd span:hover{background:#2e3140;opacity:1}
   #fst .bd{padding:12px}
   #fst .acct{font-size:11.5px;margin-bottom:10px;padding:6px 9px;background:#0f1115;border-radius:8px;border:1px solid #232a33;word-break:break-all}
   #fst .acct .k{opacity:.6}
   #fst .tabs{display:flex;gap:4px;margin-bottom:10px}
   #fst .tab{flex:1;padding:7px 0;border:1px solid #2e3140;border-radius:8px;background:#0f1115;color:#9aa0ab;cursor:pointer;font-size:12px;font-weight:600;text-align:center}
   #fst .tab.on{background:#ef9f27;color:#412402;border-color:transparent}
   #fst .tab.del.on{background:#e24b4a;color:#fff}
   #fst input{width:100%;box-sizing:border-box;padding:7px 9px;border-radius:8px;border:1px solid #2e3140;background:#0f1115;color:#e8eaed;margin-bottom:8px}
   #fst .cfg{display:none} #fst.cfgopen .cfg{display:block}
   #fst .lbl{opacity:.7;font-size:12px;margin:2px 0 5px}
   #fst .row{display:flex;gap:6px;align-items:center;flex-wrap:wrap}
   #fst button.pick{flex:1;min-width:42px;padding:8px 0;border:none;border-radius:8px;background:#23252e;color:#e8eaed;cursor:pointer;font-weight:600}
   #fst button.pick:hover{background:#2e3140} #fst button.go{background:#ef9f27;color:#412402} #fst button.go:hover{filter:brightness(1.07)}
   #fst button.danger{background:#e24b4a;color:#fff} #fst button:disabled{opacity:.45;cursor:default} #fst input.num{width:52px;margin:0}
   #fst .warn{font-size:11.5px;background:rgba(226,75,74,.12);border:1px solid rgba(226,75,74,.4);color:#f3a3a2;border-radius:8px;padding:7px 9px;margin-bottom:8px}
   #fst .bar{height:6px;border-radius:4px;background:#23252e;margin:10px 0 4px;overflow:hidden} #fst .bar>i{display:block;height:100%;width:0;background:#ef9f27;transition:width .15s}
   #fst .stat{font-size:12px;opacity:.9;min-height:16px} #fst .foot{font-size:11px;opacity:.55;margin-top:6px;word-break:break-all}
   #fst .autorow{margin-top:8px;align-items:center}
   #fst button.autotoggle{flex:1;padding:8px 0;border:none;border-radius:8px;background:#3a3f4b;color:#fff;cursor:pointer;font-weight:700;font-size:12px}
   #fst button.autotoggle:hover{filter:brightness(1.08)} #fst button.autotoggle.on{background:#1d9e75}
   #fst input.autoint{width:54px;box-sizing:border-box;padding:7px 6px;border-radius:8px;border:1px solid #2e3140;background:#0f1115;color:#e8eaed;margin:0;text-align:center}
   #fst select.pbsel{flex:1;min-width:0;padding:6px 4px;border-radius:8px;border:1px solid #2e3140;background:#0f1115;color:#e8eaed;font-size:11.5px}
   #fst .autostat{font-size:11px;opacity:.85;margin-top:6px;min-height:14px}
   #fst .bakemodels{gap:4px;margin-bottom:2px}
   #fst label.mchk{flex:1;display:flex;align-items:center;justify-content:center;gap:4px;padding:6px 4px;border:1px solid #2e3140;border-radius:8px;background:#0f1115;cursor:pointer;font-size:11px;font-weight:600;white-space:nowrap}
   #fst label.mchk:hover{background:#181b22} #fst label.mchk input{width:auto;margin:0;accent-color:#ef9f27}
   #fst .anglebody{margin-top:8px;padding:8px;border:1px solid #2e3140;border-radius:10px;background:#0f1115}
   #fst .anglehd{display:flex;align-items:center;gap:6px;margin-bottom:4px;font-size:12px} #fst .anglehd b{flex:1}
   #fst .anglehd .anglecount{opacity:.6;font-size:11px} #fst .anglehd .anglex{cursor:pointer;opacity:.7;padding:0 6px;border-radius:6px} #fst .anglehd .anglex:hover{background:#2e3140;opacity:1}
   #fst .chips{gap:4px;margin-top:4px} #fst .chips .clbl{opacity:.6;font-size:11px;width:40px}
   #fst button.chip{flex:0 0 auto;padding:4px 8px;border:1px solid #2e3140;border-radius:999px;background:#14151c;color:#9aa0ab;font-size:11px;font-weight:600;cursor:pointer}
   #fst button.chip:hover{background:#23252e} #fst button.chip.on{background:#ef9f27;color:#412402;border-color:transparent}
   #fst .anglelist{max-height:230px;overflow-y:auto;margin-top:8px;display:flex;flex-direction:column;gap:4px}
   #fst .acard{padding:6px 8px;border:1px solid #232a33;border-radius:8px;background:#14151c;cursor:pointer}
   #fst .acard:hover{background:#1d2028;border-color:#3a3f4b} #fst .acard.last{border-color:#ef9f27}
   #fst .acard-l{font-size:11px;color:#c9cdd4;display:flex;gap:6px;align-items:baseline} #fst .acard-star{color:#ef9f27;font-weight:700;flex:0 0 auto}
   #fst .acard-t{font-size:11.5px;opacity:.85;margin-top:2px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
   #fst .acard-s{font-size:10.5px;opacity:.5;margin-top:2px}
   #fst .anglefoot{font-size:10.5px;opacity:.5;margin-top:6px;word-break:break-all}
   #fst .hd .ver{font-weight:400;opacity:.55;font-size:11px;margin-left:6px}
   #fst .hd a.help{color:#e8eaed;text-decoration:none;cursor:pointer;opacity:.7;padding:2px 7px;border-radius:6px;font-weight:700} #fst .hd a.help:hover{background:#2e3140;opacity:1}
   #fst.creator .tab.adv{display:none} #fst.creator .cfg .adv{display:none}
   #fst .moderow button.pick.on{background:#ef9f27;color:#412402}
   #fst .modehelp{font-size:11px;opacity:.6;margin:-2px 0 10px}
  #fst.deluxe .cfg .modelbl,#fst.deluxe .moderow,#fst.deluxe .modehelp{display:none}
  #fst.deluxe .hd .ver{color:#ef9f27;opacity:.9}
   #fst.min .bd{display:none}`;
  const style = document.createElement("style"); style.textContent = css; document.documentElement.appendChild(style);
  const panel = document.createElement("div"); panel.id = "fst"; if (!DELUXE) panel.classList.add("creator");
  panel.innerHTML = `
   <div class="hd"><b>3DMC Studio Tools<span class="ver"></span></b><a class="help" href="https://3dmusclecomics.com/toolbox/" target="_blank" rel="noopener" title="Open the guide (3dmusclecomics.com/toolbox)">?</a><span class="g" title="Settings — mode, Studio key">⚙</span><span class="x" title="Close">✕</span></div>
   <div class="bd">
     <div class="acct"><span class="k">Flow account:</span> <b class="acctval">…</b></div>
     <div class="tabs">
       <div class="tab on" data-mode="download">Download</div>
       <div class="tab adv" data-mode="studio">→ Studio</div>
       <div class="tab" data-mode="review">Review</div>
       <div class="tab adv" data-mode="bakeoff" title="Model bake-off — run each prompt on every Nano Banana model, then compare">🔬</div>
       <div class="tab del adv" data-mode="delete">🗑</div>
     </div>
     <div class="cfg">
       <div class="lbl modelbl">Mode</div>
       <div class="row moderow" style="margin-bottom:6px"><button class="pick modepick" data-uimode="creator" title="Download, Review bundle and the prompt buttons — everything a contributor needs. No setup.">Creator</button><button class="pick modepick" data-uimode="advanced" title="Adds → Studio / Auto-sync, 🔬 Bake-off, 🗑 Delete and the Patreon downloader. → Studio needs the Studio key below.">Advanced</button></div>
       <div class="modehelp">Creator = Download + Review + prompt buttons. Advanced adds → Studio, Bake-off, Delete, Patreon.</div>
       <div class="adv">
       <div class="lbl">Studio bridge URL</div><input class="url" type="text">
       <div class="lbl">Studio key (Studio → Flow import)</div><input class="key" type="password" placeholder="paste your bridge key">
       <div class="row" style="margin-bottom:10px"><button class="pick savecfg">Save settings</button><button class="pick dumpcomposer" title="Debug: save a snapshot of Flow's composer / open popover / first tile (plus a probe of what the extension can see) to Downloads/3dmc-debug/ and copy it to the clipboard — send that file when a prompt button, Bake-off or Delete misbehaves after a Flow UI change">🐞 Dump composer</button></div>
       </div>
     </div>
     <div class="studio-only" style="display:none">
       <div class="lbl">Studio section — blank = a new one each send (or type a name to append)</div>
       <input class="proj" type="text">
       <div class="row autorow">
         <button class="autotoggle" title="While ON, every new Flow generation is pushed into the named Studio section as it lands">○ Auto-sync OFF</button>
         <input class="autoint" type="number" min="8" title="seconds between checks">
         <span class="lbl" style="margin:0">sec</span>
       </div>
       <div class="autostat"></div>
     </div>
     <div class="actbody">
       <div class="lbl modehint">Most-recent generations:</div>
       <div class="row"><button class="pick" data-n="5">5</button><button class="pick" data-n="10">10</button><button class="pick" data-n="25">25</button>
         <input class="num" type="number" min="1" placeholder="#"><button class="pick go" data-n="custom">Go</button></div>
       <div class="row" style="margin-top:8px"><button class="pick go" data-n="all" style="flex:1">Whole project</button></div>
     </div>
     <div class="bakebody" style="display:none">
       <div class="lbl">While ON, hit Create once and the same prompt is run on every ticked model — same refs, aspect and count. If Flow refuses the automatic click it falls back to arming each model and asking you to press Create.</div>
       <div class="row bakemodels"></div>
       <div class="row autorow">
         <button class="autotoggle baketoggle" title="After each submit, re-arm the composer on the next ticked model">○ Bake-off OFF</button>
       </div>
       <div class="row" style="margin-top:8px"><button class="pick go bakecompare" style="flex:1">📊 Compare this project</button></div>
       <div class="autostat bakestat"></div>
     </div>
     <div class="delbody" style="display:none">
       <div class="warn">⚠ Destructive. Soft-deletes to Flow's <b>Trash</b> (recoverable via "View Trash"). Tick the tiles on the page you want gone.</div>
       <div class="row"><button class="pick selvis">Select visible</button><button class="pick clr">Clear</button></div>
       <div class="row" style="margin-top:8px"><button class="pick danger trash" style="flex:1" disabled>🗑 Move 0 to Trash</button></div>
     </div>
     <div class="row" style="margin-top:8px"><span class="lbl" style="margin:0 4px 0 0">Prompt:</span><button class="pick pb" data-pb="director" title="Append the director's-choice reframe block — attach a panel as ref; the scene stays, the model re-stages the camera (dolly / orbit / height / zoom) for this specific beat. Unlike Cine+Light/Framing it prescribes NO fixed angle, so it never ruts into low-hero shots.">🎥 Director</button><button class="pick pb" data-pb="cine" title="PREPEND the shot-first camera block plus the lighting scheme, so the camera leads the prompt (cutscene-camera-rules.md). The shot, figure count and lighting follow the Shot / Cast / Light selectors below. Click 🎨 DAZ style afterwards so the style line ends up first. Fresh generations only: it directs the camera, so don't pair it with the i2i keep-composition lock.">📷 Cine+Light</button><button class="pick pb" data-pb="frame" title="PREPEND the shot-first camera block ONLY, with no lighting. The shot and figure count follow the Shot / Cast selectors below. Fresh generations only: like Cine+Light it directs the camera, so don't pair it with the i2i keep-composition lock.">🎬 Framing</button><button class="pick pb" data-pb="light" title="Append the selected lighting scheme ONLY — no framing, no camera. The one prompt block that rides with the i2i keep-composition lock: attach an accepted panel as the sole ref, prepend the composition-lock sentence, and the same shot comes back re-lit. Scheme + render mode follow the Light/Render selectors below.">💡 Light</button><button class="pick pb" data-pb="detail" title="Append the extreme-close-up detail block — it asks which region the shot is on, then fills the frame with it: macro 100–135mm at f/1.8, background melted to bokeh, the muscle tack-sharp with the key raking low so striations and veins cast micro-shadows. It deliberately RE-CROPS, so like Framing and Director it must not ride with the i2i keep-composition lock. Composes with 💡 Light (pick any of the 19 schemes); don't stack it with Cine+Light, whose framing half fights it.">🔎 Detail</button><button class="pick pb" data-pb="staging" title="Append the anti-flat staging block — tilted eye-line diagonals for two-character tension, near/far depth layers, varied-scale pyramid for 3+; forbids flat same-height lineups. No camera prescribed, so it rides with your own action prompt (not with the i2i keep-composition lock).">📐 Staging</button><button class="pick pbangle" title="Pick a camera/pose card from the comic-corpus Angle Deck (76 Deed Arts seeds, L40 body-to-camera staging) and APPEND it as the prompt's final sentence — camera height, nearest limb, muscle sold, crop, body line; no appearance, no style. Filter by angle and by the muscle the shot sells, or 🎲 deal a random one — a deal swaps the previous card out and presses Create, so keep clicking for new angles. It directs the camera, so like Framing/Director/Detail it must not ride with the i2i keep-composition lock.">🎥 Angle card</button><button class="pick pb" data-pb="sheet" title="Append the character turnaround-sheet block — attach the character as ref; asks for the character's name (blank = no name plate). Front + back + side profile + face close-up on a clean studio background.">🧍 Char sheet</button><button class="pick pb" data-pb="daz" title="Prepend the canonical DAZ3D style prefix — style anchors lead the prompt">🎨 DAZ style</button><button class="pick pb" data-pb="drawn" title="Prepend the painted-comic style prefix — the counterpart to 🎨 DAZ, for the Render: Drawn lighting variants. Use ONE render anchor per prompt: stacking this with 🎨 DAZ puts two opposed anchors in the same prompt and yields plastic-looking linework.">✏️ Drawn style</button></div>
     <div class="row" style="margin-top:6px"><span class="lbl" style="margin:0 4px 0 0">Shot:</span><select class="pbsel pbcam" title="Cutscene shot for 📷 Cine+Light / 🎬 Framing (cutscene-camera-rules.md). Vary per beat = the model picks one of the five shots for this beat. Every option frames tight: the crop line puts hips, legs and feet completely outside the frame, and the block tells the model the refs carry appearance, not camera placement. Full body is not on the menu; write the 1-in-8 establishing or size-reveal shot yourself. Name wardrobe only for what is in frame (no shoes in a chest-up shot)."><option value="vary">Vary per beat</option><option value="ots">Over the shoulder</option><option value="below">Torso from below</option><option value="side">Torso side profile</option><option value="hero">Low hero · biggest nearest</option><option value="ecu">Insert ECU</option></select><span class="lbl" style="margin:0 4px 0 6px">Cast:</span><select class="pbsel pbcast" title="Figure count the Cine+Light / Framing shot assumes. Auto = neutral wording that never asserts a count (no phantom second figure). Solo / Duo pick the one- or two-figure version of Over the shoulder and Low hero, and set the depth line: different distances from the lens, a different expression per face, never a symmetric row."><option value="auto">Auto</option><option value="solo">Solo</option><option value="duo">Duo</option></select></div>
     <div class="row" style="margin-top:6px"><span class="lbl" style="margin:0 4px 0 0">Light:</span><select class="pbsel pblight" title="Lighting scheme for Cine+Light and 💡 Light. Each scheme is built to the same spec — a named key with a stated angle, a per-form gradient, ambient occlusion by anatomical location, micro-shadow detail, a rim with an anti-glow guard, and the environment held below the figures."></select><span class="lbl" style="margin:0 4px 0 6px">Render:</span><select class="pbsel pbrender" title="Which variant of the scheme to use. 3D = photoreal / PBR language (pairs with the 🎨 DAZ prefix). Drawn = the same light logic in painted-comic language — pair it with the ✏️ Drawn style prefix, and do NOT stack it with 🎨 DAZ."><option value="cgi">3D</option><option value="illo">Drawn</option></select></div>
     <div class="anglebody" style="display:none">
       <div class="anglehd"><b>🎥 Angle card</b><span class="anglecount">loading…</span><span class="anglex" title="Close the picker">✕</span></div>
       <div class="row chips anglechips-angle"></div>
       <div class="row chips anglechips-muscle"></div>
       <div class="row" style="margin-top:8px"><button class="pick go angledeal" title="Deal ONE random card from the current filter into the prompt — in place of the card dealt before (your own text and the staged refs are left alone) — and press Create. Keep clicking for a fresh angle every time.">🎲 Deal me one</button><button class="pick angleclear" title="Switch every chip off — all cards">All cards</button></div>
       <div class="anglelist"></div>
       <div class="anglefoot">Cards: research/comic-corpus/synthesis/cards.json — regenerate with scripts/angle_deck.py, then re-copy into the extension.</div>
     </div>
     <div class="bar"><i></i></div><div class="stat">Idle — open a Flow project, pick an action.</div><div class="foot"></div>
   </div>`;
  document.documentElement.appendChild(panel);
  const $ = (s) => panel.querySelector(s);
  const accEl = $(".acctval"), urlInput = $(".url"), keyInput = $(".key"), projInput = $(".proj");
  const barFill = $(".bar>i"), statEl = $(".stat"), footEl = $(".foot"), numInput = $(".num");
  const studioOnly = $(".studio-only"), modeHint = $(".modehint"), actbody = $(".actbody"), delbody = $(".delbody"), trashBtn = $(".trash");
  const bakebody = $(".bakebody"), bakeToggleBtn = $(".baketoggle"), bakeStatEl = $(".bakestat"), bakeModelsEl = $(".bakemodels"), bakeCompareBtn = $(".bakecompare");
  const autoToggleBtn = $(".autotoggle"), autoIntInput = $(".autoint"), autoStatEl = $(".autostat");
  const buttons = [...panel.querySelectorAll("button.pick")];

  // ── Mode: "creator" (Download + Review + prompt buttons — the contributor build) vs
  // "advanced" (adds → Studio / Auto-sync, Bake-off, Delete, and the Patreon panel).
  // Fresh installs start in creator. A machine that already holds a Studio key is the
  // owner's, so it keeps the full panel without flipping anything. Persisted as uiMode;
  // patreon.js reads the same key (and listens for changes) to show/hide its panel.
  let uiMode = DELUXE ? "advanced" : "creator";
  const modeBtns = [...panel.querySelectorAll("button.modepick")];
  function applyMode() {
    panel.classList.toggle("creator", uiMode === "creator");
    modeBtns.forEach((b) => b.classList.toggle("on", b.dataset.uimode === uiMode));
    if (uiMode === "creator" && (mode === "studio" || mode === "bakeoff" || mode === "delete")) setMode("download");
  }
  modeBtns.forEach((b) => b.addEventListener("click", () => {
    uiMode = b.dataset.uimode; chrome.storage.local.set({ uiMode }); applyMode();
    statEl.textContent = uiMode === "creator" ? "Creator mode — Download, Review, prompt buttons." : "Advanced mode — all tools shown.";
  }));
  chrome.storage.local.get(["studioUrl", "bridgeKey", "uiMode"]).then((s) => {
    if (s.studioUrl) cfg.url = s.studioUrl; if (s.bridgeKey) cfg.key = s.bridgeKey; urlInput.value = cfg.url; keyInput.value = cfg.key;
    uiMode = DELUXE ? "advanced" : ((s.uiMode === "creator" || s.uiMode === "advanced") ? s.uiMode : (cfg.key ? "advanced" : "creator"));
    applyMode();
  });
  try {
    const m = chrome.runtime.getManifest();
    $(".hd .ver").textContent = "v" + (m.version_name || m.version);
    if (DELUXE) { $(".hd b").firstChild.textContent = m.name; panel.classList.add("deluxe"); $(".hd .g").title = "Settings — Studio bridge URL + key"; }
  } catch (e) {}
  projInput.placeholder = "blank → new section each send";

  function onDelCount(n) { trashBtn.textContent = "🗑 Move " + n + " to Trash"; trashBtn.disabled = n === 0; }
  function setMode(m) {
    if (prevMode === "delete" && m !== "delete" && self.FlowDelete) self.FlowDelete.stop();
    prevMode = mode = m;
    panel.querySelectorAll(".tab").forEach((t) => t.classList.toggle("on", t.dataset.mode === m));
    const del = m === "delete", bake = m === "bakeoff";
    actbody.style.display = del || bake ? "none" : "block";
    delbody.style.display = del ? "block" : "none";
    bakebody.style.display = bake ? "block" : "none";
    studioOnly.style.display = m === "studio" ? "block" : "none";
    if (m === "studio" && !cfg.key) panel.classList.add("cfgopen");
    if (del && self.FlowDelete) self.FlowDelete.start(onDelCount);
    if (!del && !bake) modeHint.textContent = m === "download" ? "Download most-recent generations:" : m === "studio" ? "Send most-recent generations to Studio:" : "Review-bundle most-recent generations:";
  }
  panel.querySelectorAll(".tab").forEach((t) => t.addEventListener("click", () => setMode(t.dataset.mode)));

  $(".hd .x").addEventListener("click", () => { if (self.FlowDelete) self.FlowDelete.stop(); panel.remove(); style.remove(); window.__flowStudioTools = false; });
  $(".hd .g").addEventListener("click", () => panel.classList.toggle("cfgopen"));
  $(".dumpcomposer").addEventListener("click", () => {
    // Ground truth for the next Flow redesign: composer + overlay + tile markup and a probe of
    // every finder, saved via the worker's download path (data: URL, like the Review manifest).
    const FCo = self.FlowComposer;
    if (!FCo) { status("Dump: flow-composer.js not loaded."); return; }
    let html; try { html = FCo.dump(); } catch (e) { status("Dump failed: " + ((e && e.message) || e)); return; }
    const name = "3dmc-debug/flow-composer-" + new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19) + ".html";
    try { navigator.clipboard.writeText(html).catch(() => {}); } catch (e) {}
    try {
      const port = chrome.runtime.connect({ name: "fst" });
      port.onMessage.addListener((m) => { if (m.type === "done") status(m.ok ? "🐞 Dump saved to Downloads/" + name + " (also on the clipboard, " + Math.round(html.length / 1024) + " KB)." : "🐞 Dump download failed — it is on the clipboard (" + Math.round(html.length / 1024) + " KB)."); });
      port.postMessage({ type: "start", kind: "download", folder: "", jobs: [{ url: "data:text/html;charset=utf-8," + encodeURIComponent(html), path: name }], manifest: null });
    } catch (e) { status("🐞 Dump is on the clipboard (" + Math.round(html.length / 1024) + " KB); download failed: " + ((e && e.message) || e)); }
  });
  $(".savecfg").addEventListener("click", () => { cfg.url = urlInput.value.trim() || DEFAULT_URL; cfg.key = keyInput.value.trim(); chrome.storage.local.set({ studioUrl: cfg.url, bridgeKey: cfg.key }); statEl.textContent = "Settings saved."; panel.classList.remove("cfgopen"); });
  $(".selvis").addEventListener("click", () => { if (self.FlowDelete) self.FlowDelete.selectVisible(); });
  $(".clr").addEventListener("click", () => { if (self.FlowDelete) self.FlowDelete.clear(); });
  trashBtn.addEventListener("click", runTrash);
  (() => { const hd = $(".hd"); let sx, sy, sr, sb, drag = false; hd.addEventListener("mousedown", (e) => { if (e.target.tagName === "SPAN" || e.target.tagName === "A") return; drag = true; sx = e.clientX; sy = e.clientY; const r = panel.getBoundingClientRect(); sr = innerWidth - r.right; sb = innerHeight - r.bottom; e.preventDefault(); }); addEventListener("mousemove", (e) => { if (!drag) return; panel.style.right = Math.max(0, sr - (e.clientX - sx)) + "px"; panel.style.bottom = Math.max(0, sb - (e.clientY - sy)) + "px"; }); addEventListener("mouseup", () => { drag = false; }); })();

  let busy = false;
  const setBusy = (b) => { busy = b; buttons.forEach((x) => (x.disabled = b)); };
  const setBar = (f) => { barFill.style.width = Math.round(f * 100) + "%"; };
  const status = (t) => { statEl.textContent = t; };
  // flow.google.com (the Angular UI, since 2026-09-07): composer-driven tools (prompt buttons,
  // 🎥 Angle card, 🔬 Bake-off, 🗑 Delete) go through flow-composer.js / flow-delete.js (2.8.2).
  // The labs.google project API the DATA tools used was deprecated and disabled 2026-09-15;
  // they are now rebuilt on Flow's own backend — Download reads the grid (2.8.6), Review /
  // → Studio / Auto-sync read the project over batchexecute Zzl0ze (2.8.7–2.8.8). Only
  // reference INPUT images in a Review bundle are still unavailable (no URL in the payload).
  if (location.hostname === "flow.google.com") {
    const ui = self.FlowComposer ? self.FlowComposer.ui() : null;
    status(ui === "angular"
      ? "New Flow UI — all tools work here again: Download, Review, → Studio, Auto-sync (rebuilt on Flow's new backend after Google retired the old data API), plus prompt buttons + 🎥 Angle card, 🔬 Bake-off, 🗑 Delete. ⚙ → 🐞 dumps the composer if something misbehaves."
      : "New Flow UI — open a project to use Download / Review / → Studio / Auto-sync, the prompt buttons, 🔬 Bake-off or 🗑 Delete.");
    // The Angular app renders the composer after document_idle; re-check once it has had time to.
    if (ui !== "angular") setTimeout(() => { if (self.FlowComposer && self.FlowComposer.ui() === "angular" && /open a project/.test(statEl.textContent)) status("New Flow UI — Download, Review, → Studio, Auto-sync, the prompt buttons + 🎥 Angle card, 🔬 Bake-off and 🗑 Delete are all live here."); }, 4000);
  }
  function stampAccount(email) { document.documentElement.setAttribute("data-flow-account", email || "unknown"); accEl.textContent = email || "(unknown)"; accEl.style.color = email ? "#34d399" : "#fbbf24"; }

  async function runTrash() {
    if (busy || !self.FlowDelete) return;
    const n = self.FlowDelete.count(); if (!n) return;
    const acct = accEl.textContent || "(unknown)";
    const typed = prompt("⚠ Move " + n + " generation(s) to Flow's Trash on account:\n  " + acct + "\n\nSoft delete — recoverable from \"View Trash\".\nType the number " + n + " to confirm:");
    if (typed === null) return;
    if (typed.trim() !== String(n)) { status("Cancelled — number didn't match."); return; }
    setBusy(true); setBar(0); status("Trashing 0/" + n + "…");
    const res = await self.FlowDelete.run((done, total, miss) => { setBar(done / total); status("Trashing " + done + "/" + total + "…" + (miss ? " · " + miss + " not found" : "")); });
    setBar(1); status((res.done ? "Done ✓ " + res.done + " trashed" : "Nothing trashed") + (res.miss ? " · " + res.miss + " skipped" : "") + (res.error ? " — " + res.error : (res.miss ? " (scroll + retry)" : "")));
    onDelCount(self.FlowDelete.count()); setBusy(false);
  }

  async function run(limit) {
    if (busy || mode === "delete") return;
    if (mode === "studio" && !cfg.key) { panel.classList.add("cfgopen"); status("Paste your Studio key (⚙) first."); keyInput.focus(); return; }
    setBusy(true); setBar(0); footEl.textContent = "";
    try {
      let kind, payload;
      const angular = self.FlowComposer && self.FlowComposer.ui() === "angular";
      // flow.google.com (the labs.google project API was deprecated and disabled 2026-09-15):
      //   • Download (2.8.6) pulls outputs straight from the project grid — full-res via the
      //     =s0 FIFE suffix, no dead API, no auth token.
      //   • Review (2.8.7) reads prompts from the new batchexecute `Zzl0ze` RPC (FlowCore.
      //     getAngularProject) and joins them to the grid's full-res images by media id.
      // Send-to-Studio still uses the legacy harvest below (honest 404 until it is ported).
      if (angular && (mode === "download" || mode === "review" || mode === "studio")) {
        stampAccount(await FC.getAccount());
        if (mode === "download") {
          status("Reading the grid…");
          const outs = await FC.getGridOutputs(limit, (n) => status("Reading the grid… " + n + " image" + (n === 1 ? "" : "s")));
          if (!outs.length) { status("No images in this project's grid — open a Flow project, let the tiles load, then retry."); return; }
          const folder = folderName();
          payload = { folder, jobs: outs.map((o, i) => ({ url: o.url, path: folder + "/flow-" + String(i + 1).padStart(3, "0") + ".jpg" })) };
          footEl.textContent = "→ Downloads/" + folder + "/"; kind = "download";
          status("Downloading " + outs.length + " image" + (outs.length === 1 ? "" : "s") + " (full-res)…");
        } else if (mode === "review") {
          // Prompts from the new project API; full-res images from each record's own URL
          // (=s0) — no grid scrolling. Reference input images are named in the manifest
          // but not downloaded (their URL isn't in the payload).
          status("Reading prompts…");
          const proj = await FC.getAngularProject();
          if (!proj) { status("Couldn't read the project — " + (FC.lastError || "reload the Flow tab and retry.")); return; }
          if (!proj.records.length) { status("No generations found in this project."); return; }
          const b = FC.buildReviewBundleAngular(proj.records, await FC.getAccount(), proj.name, proj.id, limit, null);
          if (!b.jobs.length) { status("No output images resolved for the bundle."); return; }
          footEl.textContent = "→ Downloads/" + b.folder + "/"; kind = "download"; payload = { folder: b.folder, jobs: b.jobs, manifest: b.manifest };
          status("Bundling " + b.count + " generations (" + b.jobs.length + " files, full-res)…");
        } else {
          // Send to Studio — full-res outputs + ★ favorite state from the grid, prompts from the
          // new project API (joined by media id). Reading the grid carries the favorite flag (a
          // favorited tile's hotbar reads "Remove favorite"), which the RPC does not, so favourited
          // Flow gens land pre-approved in the Studio. Auto-sync keeps the no-grid path (fav 0 —
          // gens are usually favourited after they generate, so a sync tick can't know yet).
          status("Reading the grid…");
          const grid = await FC.getGridOutputs(limit, (n) => status("Reading the grid… " + n + " image" + (n === 1 ? "" : "s")));
          if (!grid.length) { status("No images in this project's grid — open a Flow project, let the tiles load, then retry."); return; }
          status("Reading prompts…");
          const proj = await FC.getAngularProject();
          const pmap = proj ? new Map(proj.records.map((r) => [r.out_media_id, r])) : new Map();
          const typed = projInput.value.trim();
          const project = typed || defaultProject();
          const newSection = typed ? 0 : 1;   // blank field → a fresh Studio section for this batch
          payload = { items: grid.map((o, i) => { const r = pmap.get(o.id) || {}; return { url: o.url, orig: "flow-" + String(i + 1).padStart(3, "0") + ".jpg", gen: r.gen_id || "", prompt: r.prompt || "", fav: o.fav || 0 }; }), project, newSection, cfg };
          footEl.textContent = newSection ? ("→ Studio: NEW section (" + project + " · …)") : ("→ Studio project: " + project);
          const favN = grid.filter((o) => o.fav).length;
          kind = "studio"; status("Sending " + grid.length + " to Studio" + (favN ? " (★ " + favN + " pre-approved)" : "") + "…");
        }
      } else {
        status("Reading project…");
        const [proj, account] = await Promise.all([FC.getProject(), FC.getAccount()]);
        stampAccount(account);
        if (!proj) { status("No project data — " + (FC.lastError || "open a Flow project (/project/<id>), let it load, then retry.")); return; }
        if (!proj.records.length) { status("No generations found in this project."); return; }
        if (mode === "review") {
          const b = FC.buildReviewBundle(proj.records, account, proj.name, proj.id, limit);
          footEl.textContent = "→ Downloads/" + b.folder + "/"; kind = "download"; payload = { folder: b.folder, jobs: b.jobs, manifest: b.manifest };
          status("Bundling " + b.count + " generations (" + b.jobs.length + " files)…");
        } else {
          const outs = FC.outputList(proj.records, limit);
          if (!outs.length) { status("No output images found."); return; }
          if (mode === "download") {
            const folder = folderName();
            payload = { folder, jobs: outs.map((o, i) => ({ url: o.url, path: folder + "/flow-" + String(i + 1).padStart(3, "0") + ".jpg" })) };
            footEl.textContent = "→ Downloads/" + folder + "/"; kind = "download"; status("Downloading " + outs.length + " images…");
          } else {
            const typed = projInput.value.trim();
            const project = typed || defaultProject();
            const newSection = typed ? 0 : 1;   // blank field → a fresh Studio section for this batch
            payload = { items: outs.map((o, i) => ({ url: o.url, orig: "flow-" + String(i + 1).padStart(3, "0") + ".jpg", gen: o.gen_id || "", prompt: o.prompt || "", fav: o.fav || 0 })), project, newSection, cfg };
            footEl.textContent = newSection ? ("→ Studio: NEW section (" + project + " · …)") : ("→ Studio project: " + project);
            kind = "studio"; status("Sending " + outs.length + " to Studio…");
          }
        }
      }
      await new Promise((resolve) => {
        const port = chrome.runtime.connect({ name: "fst" });
        port.onMessage.addListener((m) => {
          if (m.type === "progress") { setBar(m.done / m.total); status((mode === "studio" ? "Sending " : "Saving ") + m.done + "/" + m.total + (m.fail ? " · " + m.fail + " failed" : "")); }
          else if (m.type === "done") { setBar(1); status("Done ✓ " + m.ok + "/" + m.total + (m.fail ? " · " + m.fail + " failed" : "")); port.disconnect(); resolve(); }
          else if (m.type === "error") { status("Error: " + m.message); port.disconnect(); resolve(); }
        });
        port.postMessage(Object.assign({ type: "start", kind }, payload));
      });
    } catch (e) { console.error("[3DMC Studio Tools]", e); status("Error — see console."); }
    finally { setBusy(false); }
  }

  panel.addEventListener("click", (e) => {
    const b = e.target.closest("button.pick"); if (!b || busy) return;
    if (b.classList.contains("savecfg") || b.classList.contains("dumpcomposer") || b.classList.contains("selvis") || b.classList.contains("clr") || b.classList.contains("trash")) return;
    const n = b.dataset.n; if (!n) return;
    if (n === "all") return run(Infinity);
    if (n === "custom") { const v = parseInt(numInput.value, 10); if (v > 0) return run(v); numInput.focus(); return; }
    return run(parseInt(n, 10));
  });

  // ───────── Prompt blocks — one-click paste of canonical prompt presets ─────
  // Sources: skills/comic-production/references/prompt-templates.md (Style Prefix —
  // exact tested wording, do not rewrite) and cinematic-framing.md (hero framing +
  // "volume block" golden-hour lighting). Six blocks:
  //   • daz      — style prefix, PREPENDS (style anchors lead the prompt)
  //   • director — scene-adaptive reframe, APPENDS — attach a source panel as ref;
  //                the model chooses the camera (dolly/orbit/height/zoom) for the
  //                beat instead of a prescribed angle. Keeps scene + lighting.
  //   • sheet    — character turnaround reference page, APPENDS — attach the
  //                character as ref; front/back/side + face close-up on a clean
  //                studio background. askName: prompts for the character's name on
  //                click (blank = "no text/name plate" variant) — never leaves an
  //                unfilled [placeholder] in the prompt (documented failure mode).
  //   • staging  — anti-flat subject-blocking guard, APPENDS — composes with the
  //                user's own action prompt (L34 distilled: tilted eye-line for
  //                2-character tension, near/far depth layers with readable space,
  //                varied-scale pyramid for 3+; forbids flat same-height lineups).
  //                Prescribes NO camera, so it pairs with anything except the
  //                i2i keep-composition lock.
  //   • cine     — shot-first camera block + lighting scheme, PREPENDS (2.9.0)
  //   • frame    — shot-first camera block ONLY (no lighting), PREPENDS — for pairing
  //                with a separate lighting choice, or when you'll relight the panel afterward
  // cine + frame are PARAMETERIZED by the Shot:/Cast: selectors (persisted):
  //   Shot — vary (default; the model picks one cutscene shot per beat) / ots / below /
  //          side / hero / ecu. The UI calls it "Shot", but the storage key is still pbCam.
  //          2.8.x's Cam menu only set the height and every shot came out "mid-thigh up".
  //   Cast — auto (default; neutral "figure(s)" wording that never asserts a count —
  //          fixes the old hardcoded "both women" phantom-duo) / solo / duo
  // NOTE: cine AND frame both DIRECT THE CAMERA, so they are for FRESH generations —
  // they fight the i2i composition-lock sentence. director is the opposite: it is
  // FOR i2i reframes (source attached), and must NOT be paired with the composition
  // lock either — its whole job is to move the camera.
  const PROMPT_BLOCKS = {
    daz: {
      where: "start",
      label: "DAZ style prefix",
      text: "Hyperrealistic DAZ3D Studio 3D CGI render, physically-based rendering — NOT an illustration, NOT anime, NOT cartoon, NOT 2D drawn art."
    },
    // The opposite anchor, for the Render: Drawn lighting variants — they argue volume in
    // illustrator's terms (lit shape → halftone → core shadow, terminator as a drawn shape,
    // cross-hatch occlusion, broken rim strokes) and go plastic if the DAZ prefix is stacked
    // on top of them. Mutually exclusive with 🎨 DAZ by construction: one render anchor per
    // prompt. Wording is NOT yet credit-validated — unlike DAZ, which is tested.
    drawn: {
      where: "start",
      label: "Drawn style prefix",
      text: "Painted comic-book illustration — hand-drawn linework with brushed, painted value rendering, the media visibly present in the mark-making — NOT a photoreal render, NOT DAZ3D or any CGI, NOT physically-based rendering, NOT a photograph."
    },
    sheet: {
      where: "end",
      label: "Turnaround sheet block",
      askName: true,
      text: "Create a professional character model sheet — a full turnaround reference page for the character in the source image, preserving the exact same face, hairstyle, body proportions, muscle size, and outfit in every view. Clean plain light-grey studio background, soft even studio lighting, no scenery, no props beyond what the character wears. Layout: a FULL-BODY FRONT view, a FULL-BODY BACK view seen from directly behind, and a FULL-BODY SIDE PROFILE view, all in the same relaxed neutral standing pose, at identical scale and height, evenly spaced across the page like an animation turnaround. Plus one large CLOSE-UP PORTRAIT of the face, front three-quarter from the shoulders up, showing the hairstyle and facial features clearly. Flat reference-sheet presentation: straight-on camera for every view, no dramatic angles, no action poses, no environment; every view is the same character at the same size. No text, no labels, no name plate anywhere on the page. Hyperrealistic DAZ3D Studio 3D CGI render, physically-based rendering — NOT an illustration, NOT anime, NOT cartoon, NOT 2D drawn art.",
      textNamed: "Create a professional character model sheet — a full turnaround reference page for the character in the source image, preserving the exact same face, hairstyle, body proportions, muscle size, and outfit in every view. Clean plain light-grey studio background, soft even studio lighting, no scenery, no props beyond what the character wears. Layout: a FULL-BODY FRONT view, a FULL-BODY BACK view seen from directly behind, and a FULL-BODY SIDE PROFILE view, all in the same relaxed neutral standing pose, at identical scale and height, evenly spaced across the page like an animation turnaround. Plus one large CLOSE-UP PORTRAIT of the face, front three-quarter from the shoulders up, showing the hairstyle and facial features clearly. A bold header name plate reading “%NAME%” in clean capital letters sits at the top of the page; no other text or labels anywhere. Flat reference-sheet presentation: straight-on camera for every view, no dramatic angles, no action poses, no environment; every view is the same character at the same size. Hyperrealistic DAZ3D Studio 3D CGI render, physically-based rendering — NOT an illustration, NOT anime, NOT cartoon, NOT 2D drawn art."
    },
    director: {
      where: "end",
      label: "Director block",
      text: "You are the film director and cinematographer for this scene. Study the source image — who is in it, what they are doing, the emotion of the beat, and the space around them — then re-stage the CAMERA ONLY for maximum cinematic impact: dolly in or out, orbit around the subjects to a new angle, raise or lower the camera height, tilt it, frame tighter or wider — whatever this specific moment calls for. Keep the scene itself untouched: the same characters with the same faces, bodies, proportions, costumes, poses, expressions, action, speech bubbles, environment, and time of day — only the camera changes. Choose like a director: if the beat is emotional, move close on the faces; if it is a power moment, get low; if scale is the story, pull wide; if the tension lives between two characters, shoot past one onto the other; if one body region carries the beat, fill the frame with it. Vary your choice — do NOT default to a low hero angle: high angles looking down, pure profiles, over-the-shoulder, three-quarter rear, and top-down are all in play when they serve the beat. Strongly avoid the source image's exact framing — pick a meaningfully different distance AND a meaningfully different angle — and avoid flat, front-on, eye-level staging: put the subjects on diagonals, stage depth between foreground and background, let the physiques dominate the composition from whatever angle you choose. Do not re-light the scene: keep the existing lighting scheme and mood, re-rendered correctly and consistently from the new camera position. Photoreal DAZ3D CGI render, no restyling, no illustration drift."
    },
    staging: {
      where: "end",
      label: "Staging block",
      text: "STAGING — break the flat picture plane. Never arrange the characters in a flat lineup: standing side by side at the same height, the same scale, the same distance from the camera, with a level eye-line — that staging is forbidden. Instead: if TWO characters face each other, stage them on a diagonal — one face higher in frame and one lower, so the line connecting their eyes runs at a steep angle across the panel, bodies leaning in, faces close, the tension riding that tilted eye-line. When characters share a scene, stage them in DEPTH: one clearly nearer the camera and larger in frame, the other deeper in the scene and smaller by perspective, with readable space — floor, walls, a doorway, furniture — receding between them so the shot has a front and a back. With THREE or more characters, build a pyramid: every figure at a different scale and a different depth, one large in the near foreground cut by the frame edge, the others staggered behind at varied heights, their heads tracing a V or a diagonal across the panel — never a flat row of same-sized heads. Let the environment's perspective lines converge to support the depth, and keep every face readable."
    },
    // Prepended (2.9.0): the camera comes first in the prompt (cutscene-camera-rules.md §2).
    cine: { where: "start", label: "Cine+Light block", build: () => pbFramingText() + pbLightingText() },
    frame: { where: "start", label: "Framing block", build: () => pbFramingText() },
    // Lighting only — the one block that legally rides with the i2i keep-composition
    // lock, because it prescribes no camera. That's the post-hoc lighting pass in
    // cinematic-framing.md §Lighting-pass fragments, which had no button before v2.7.0.
    light: { where: "end", label: "Lighting block", build: () => pbLightingText() },
    // ECU-region — the shot type the panel had no button for. When this shipped (2.7.2),
    // every other framing block here was mid-thigh-up hero staging. Shot: replaced that in
    // 2.9.0: its Insert ECU is the generic insert, and this block is the lit muscle macro.
    // The Variety check wants at least one ECU per
    // 10 panels and Pattern 2 (the pull-out) opens on one. Spine is the owner's own
    // f/1.8 fragment; four edits, each bought with a documented failure in
    // cinematic-framing.md "Lighting-pass fragments → Hard rules":
    //   1. the region is ASKED FOR, never left as "[muscle group]" — an unfilled
    //      placeholder makes the model hunt for what to fill in;
    //   2. macro 100–135mm added, per the lens table (100mm+ = ECU-region, isolation) —
    //      an f-stop alone states the aperture but not the magnification;
    //   3. "strong rim" → bright rim + the anti-glow guard: "strong, hot" rim renders a
    //      literal glowing outline (sticker/aura look) on ~half the variants;
    //   4. the defocus is named as OPTICAL, reconciling it with the "no added blur" clause
    //      that closes all 19 lighting schemes and PB_LIGHT_V1 — otherwise the two fight.
    // Recropping is the POINT here, so like Framing/Director it must never ride with the
    // i2i keep-composition lock. Carries no render anchor, so it works in either lane.
    detail: {
      where: "end",
      label: "Detail / ECU block",
      askName: true,
      askUpper: false,
      askQuestion: "Which region is this detail shot on? (e.g. \"the right bicep peak, flexed\" — blank = let the model pick the region carrying the beat)",
      askDefault: "the right bicep peak, flexed",
      textNamed: "EXTREME CLOSE-UP — a detail shot. Fill the frame with %NAME%, framed on that region alone and cropped tight, everything else out of frame. Macro 100–135mm lens at f/1.8: the background falls away into soft, creamy bokeh and %NAME% alone is tack-sharp. That defocus is optical depth of field from the lens, not a softening of the render — the region in focus is rendered at full hyperdetailed sharpness, skin texture and pore detail resolved. At this magnification the light does the describing: the key rakes across the muscle at a low grazing angle so every striation, every surface vein, and every tendon line casts its own fine micro-shadow, with tight speculars riding the highest points of the form and the glisten of sweat catching in the lit relief. A bright rim from behind and to the left traces the contour of the muscle in a clean edge highlight — separation only, never a glow, never an outline, never a halo. Hold the environment well below the subject in both brightness and detail so nothing in the frame competes with the region in focus.",
      text: "EXTREME CLOSE-UP — a detail shot. Pick the single muscle group that carries this beat and fill the frame with it, framed on that region alone and cropped tight, everything else out of frame. Macro 100–135mm lens at f/1.8: the background falls away into soft, creamy bokeh and that region alone is tack-sharp. That defocus is optical depth of field from the lens, not a softening of the render — the region in focus is rendered at full hyperdetailed sharpness, skin texture and pore detail resolved. At this magnification the light does the describing: the key rakes across the muscle at a low grazing angle so every striation, every surface vein, and every tendon line casts its own fine micro-shadow, with tight speculars riding the highest points of the form and the glisten of sweat catching in the lit relief. A bright rim from behind and to the left traces the contour of the muscle in a clean edge highlight — separation only, never a glow, never an outline, never a halo. Hold the environment well below the subject in both brightness and detail so nothing in the frame competes with the region in focus."
    }
  };
  // ── Shot/Cast variant system for cine + frame (2.9.0: shot-first) ─────────────
  // Through 2.8.9 the Cam: menu only moved the camera HEIGHT; every insert still said
  // "Framed from mid-thigh up … at a three-quarter angle … 50–85mm". So every page landed
  // on the same knees-up cowboy shot. The Three Wishes audit (10-11) found 19 of 44 kept
  // pages knees-up and only 2 close-ups, and the owner has rejected that framing six times.
  // 2.9.0 follows skills/comic-production/references/cutscene-camera-rules.md:
  //   • the menu names a CUTSCENE SHOT (§4), or "vary" lets the model pick one per beat;
  //   • the block is PREPENDED, so the camera leads the prompt (§2);
  //   • each crop names the image EDGE and the body line it cuts, then lists what is
  //     "completely outside the frame" (§3). Plain "no legs" was ignored on ~60% of takes;
  //   • every shot says "References define appearance, not camera placement." (§2, CAM-11),
  //     because full-body character sheets otherwise pull the camera back;
  //   • the biggest figure goes NEAREST the lens, since a low camera shrinks whoever is
  //     furthest (CAM-13). No symmetric rows (CAM-03), a different expression per face;
  //   • an INSERT ECU keeps every other character out of the frame (CAM-14).
  // Full body / wide is deliberately NOT on the menu (§5 caps it at 1 panel in 8:
  // establishing or size reveal). Write that one yourself.
  // Wording stays de-gendered ("figure"): appearance comes from the attached refs, never
  // from the prompt (refs-are-truth).
  // Stored 2.8.x pbCam values: "low" maps to "hero"; "eye" and "high" fall back to "vary".
  const PB_REFS = "References define appearance, not camera placement. Do not copy the framing, distance or pose of any attached image: the character sheets are full-body, and this shot is not.";
  const PB_TIGHT = "The bottom edge of the image cuts across the chest or the waist; hips, legs and feet are completely outside the frame.";
  const PB_SHOT = {
    vary: {
      label: "Vary per beat",
      text: () => "CAMERA FIRST: pick the one cutscene shot that serves this beat, the way a video-game cutscene is cut. The options: OVER THE SHOULDER (camera just behind one figure's shoulder, which is big and soft in the foreground, looking onto the other figure seen from the chest up). TORSO FROM BELOW (camera at navel height and close, pointing steeply up; the chest fills the frame and the face is at the very top). TORSO SIDE PROFILE (camera level at shoulder height, about three feet to one side; the shoulder and upper arm fill the near half and the face is in clean profile). LOW HERO, BIGGEST NEAREST (camera low and close in front of whoever must read biggest; everyone else is further back and smaller). INSERT ECU (one hand, face, prop or muscle fills the frame). Whichever you pick, frame it tight. " + PB_TIGHT + " Not a knees-up or full-body frame, and not a three-quarter medium shot of everyone facing the camera."
    },
    ots: {
      label: "Over the shoulder",
      text: (k) => k === "solo"
        ? "OVER THE SHOULDER. The camera sits just behind the figure's shoulder at shoulder height, looking past it at what the figure faces. The shoulder, upper arm and back of the head are big and soft in the left foreground, cut by the frame edge, and the face turns just enough to show the edge of its profile. What lies beyond is sharp. The bottom edge of the image cuts across the shoulder blades; the waist, hips, legs and feet are completely outside the frame."
        : "OVER THE SHOULDER. The camera sits just behind the nearer figure's shoulder at shoulder height. That shoulder and the back of the head are big and soft in the left foreground, cut by the frame edge. Beyond them, the other figure faces the lens, seen from the chest up and sharp, and carries the beat. The bottom edge of the image cuts across the far figure's chest; stomachs, hips, legs and feet are completely outside the frame."
    },
    below: {
      label: "Torso from below",
      text: () => "TORSO FROM BELOW. The camera is at navel height, about eighteen inches from the main figure, pointing steeply UP. The chest fills the middle of the frame and the face is at the very top, looking down toward the lens, with the ceiling or sky behind the head. The bottom edge of the image cuts across the waist; the hips, legs and feet are completely outside the frame."
    },
    side: {
      label: "Torso side profile",
      text: () => "TORSO SIDE PROFILE. A pure side-profile medium close-up: the camera is level at shoulder height, about three feet from the main figure's right side. The shoulder and upper arm fill the near half of the frame, the face is in clean profile, and both the line of the chest and the line of the back read clearly. The bottom edge of the image cuts across the ribs; the stomach, hips, legs and feet are completely outside the frame."
    },
    hero: {
      label: "Low hero · biggest nearest",
      text: (k) => k === "solo"
        ? "LOW HERO. The camera is low and close, about two feet in front of the figure's chest, looking up. Chest and shoulders fill the lower two-thirds of the frame, and the face above them looks down past the lens. The bottom edge of the image cuts across the waist; the hips, legs and feet are completely outside the frame."
        : "LOW HERO, BIGGEST NEAREST. The camera is low and close in front of the figure who must read biggest, looking up. That figure is NEAREST the lens and clearly the BIGGEST thing in frame, with chest and shoulders filling the lower two-thirds. Everyone else crowds in behind those shoulders, smaller because they are further back. A low camera shrinks whoever is furthest away, so the biggest figure is never at the back. The bottom edge of the image cuts across the nearest figure's waist; hips, legs and feet are completely outside the frame."
    },
    ecu: {
      label: "Insert ECU",
      solo: true,   // one subject: the Cast: depth line does not apply
      text: () => "INSERT ECU: an extreme close-up insert. One subject fills the frame (a hand on a prop, a face, a phone screen, or the single muscle the beat is about), with the camera within a foot of it. The frame edges cut through that subject; every other body part and every other character is completely outside the frame. No other character appears anywhere in the frame, not even a shoulder or a hand."
    }
  };
  const PB_CAST = {
    auto: {
      depth: "If more than one figure is in the shot, they stand at clearly different distances from the lens (never a centred, symmetric row facing the camera), and each face shows a different expression.",
      rake: "rakes across every figure in frame", rim: "tracing each silhouette"
    },
    solo: {
      depth: "Only this one figure is in the shot; no one else appears anywhere in the frame.",
      rake: "rakes across the figure's body", rim: "tracing the silhouette"
    },
    duo: {
      depth: "Exactly two figures stand at clearly different distances from the lens, never a mirrored pair side by side facing the camera, and each face shows a different expression.",
      rake: "rakes across both figures' bodies", rim: "tracing both silhouettes"
    }
  };
  // pbLight defaults to "golden1" (v1), NOT the tightened "golden" (v2). The 2026-08-09
  // credit-burn A/B ran both on identical refs/beat/model/aspect, 4 seeds each: v2 tied v1
  // on usable-panel rate (3/4 vs 3/4) and on terminator variation (2/4 vs 2/4), failed to
  // render either of the two AO locations its rewrite exists to add (collarbone notch
  // faint in 1/4, calf split in 0/4), and introduced a failure mode v1 does not have
  // (goldenV2-3 rendered cool blue-grey — a "Golden Rake" with no golden). v1 keeps its
  // 28/28 production record and the default. See docs/posts/2026-08-09-lighting-validation.md.
  let pbCam = "vary", pbCast = "auto", pbLight = "golden1", pbRender = "cgi";
  // Order per §2: shot + camera + crop, then the refs sentence, then depth/expressions.
  // The operator's own action text follows the block, because the block is prepended.
  function pbFramingText() {
    const s = PB_SHOT[pbCam];
    return s.text(pbCast) + " " + PB_REFS + (s.solo ? "" : " " + PB_CAST[pbCast].depth);
  }
  // The lighting block shipped through v2.6.0, verbatim (its two cast hooks now
  // written as the same %RAKE% / %RIM% placeholders the library uses). Two jobs:
  // the "Golden v1" dropdown entry, so the tightened v2 can be A/B'd against it on
  // real generations, and the fallback when flow-lighting.js is absent — a missing
  // library must never yield an unlit prompt.
  const PB_LIGHT_V1 = " Lighting: late golden-hour sunlight, the sun low on the horizon to the left of frame, throwing long warm light that skims almost parallel across the scene and %RAKE% at a shallow grazing angle, so every muscle group is modeled with a full highlight-to-shadow gradient — bright warm gold where each muscle faces the sun, rolling through midtone amber, falling into soft warm shadow on the far side of every curve. Because the light arrives from the side, every ridge and swell casts its own small shadow and every hollow deepens: ambient-occlusion shadows one stop deeper in every crease where muscle heads meet — the separation between shoulder and arm, between the heads of arms and legs, along the spine and the abdominal wall — so each muscle reads as its own distinct, rounded volume. Striations, veins, and tendon lines catch the raking light and cast crisp micro-shadows. The skin carries a glossy sheen of sweat, with tight specular highlights riding the highest point of every muscle peak and sweat beads sparkling on the lit side. A subtle warm rim light wraps from behind, %RIM% with a thin amber edge along shoulders, arms, hips, and legs — lifting them off the background without ever becoming a glow or outline. The environment sits half a stop darker than the figures, catching the same warm dusk light through a veil of light atmospheric haze, slightly cooler and softer, with faint dust motes drifting in the low sun shafts, so the bodies pop forward as the brightest, sharpest, warmest things in frame; nearby surfaces return a faint warm bounce that keeps shadow sides luminous rather than black. Everything is photoreal DAZ3D CGI render quality — no restyling, no illustration drift, no added blur.";
  function pbLightingText() {
    const c = PB_CAST[pbCast];
    const L = self.FlowLighting;
    const s = (pbLight !== "golden1" && L && L.schemes) ? L.schemes[pbLight] : null;
    const raw = s ? s[pbRender] : PB_LIGHT_V1;
    return raw.replaceAll("%RAKE%", c.rake).replaceAll("%RIM%", c.rim);
  }
  function findPromptBox() {
    const vis = (el) => el.offsetParent !== null && el.getBoundingClientRect().height > 0 && !panel.contains(el);
    // flow.google.com (Angular, since 2026-09): a ProseMirror composer — flow-composer.js owns it.
    const pm = self.FlowComposer && self.FlowComposer.ui() === "angular" ? self.FlowComposer.editorEl() : null;
    if (pm && vis(pm)) return { el: pm, kind: "pm" };
    // legacy labs.google composer: a Slate contenteditable (data-slate-editor) — prefer it.
    const slate = [...document.querySelectorAll('[data-slate-editor="true"]')].filter(vis)[0];
    if (slate) return { el: slate, kind: "ce" };
    const tas = [...document.querySelectorAll("textarea")].filter(vis);
    const ta = tas.find((t) => /what do you want/i.test(t.placeholder || "")) || tas[0];
    if (ta) return { el: ta, kind: "ta" };
    const ce = [...document.querySelectorAll('[contenteditable="true"]')].filter(vis)[0];
    return ce ? { el: ce, kind: "ce" } : null;
  }
  function ceRealText(el) {
    // textContent includes the editor's in-DOM placeholder (Slate: [data-slate-placeholder];
    // ProseMirror: .prosemirror-placeholder) + zero-width chars; exclude both
    const clone = el.cloneNode(true);
    clone.querySelectorAll("[data-slate-placeholder], .prosemirror-placeholder").forEach((n) => n.remove());
    return clone.textContent.replace(/[﻿​]/g, "").trim();
  }
  function insertPromptBlock(kind) {
    let blk = PROMPT_BLOCKS[kind]; if (!blk) return;
    if (blk.build) blk = Object.assign({}, blk, { text: blk.build(), label: blk.label + " (shot: " + pbCam + " · cast: " + pbCast + " · light: " + pbLight + "/" + pbRender + ")" });
    // Blocks that need one word from the operator ask for it on click, and ship a real
    // no-answer variant — an unfilled "[placeholder]" reaching the model is a documented
    // failure (cinematic-framing.md: it makes the model hunt for what to fill in).
    if (blk.askName) {
      const nm = window.prompt(blk.askQuestion || "Character name for the sheet's name plate (leave blank for no name):", blk.askDefault || "");
      if (nm === null) return; // cancelled
      const t = nm.trim();
      const val = blk.askUpper === false ? t : t.toUpperCase();
      blk = Object.assign({}, blk, { text: t ? blk.textNamed.replaceAll("%NAME%", val) : blk.text });
    }
    insertBlock(blk);
  }
  // The insert itself, shared by the preset buttons above and the 🎥 Angle card picker
  // below. Takes a {where, label, text} block and returns true once it has been handed
  // to the composer. It APPENDS (or PREPENDS) around whatever is already there — it
  // never clears the text, never touches the staged ref chips, never submits.
  function insertBlock(blk) {
    const box = findPromptBox();
    if (!box) { status("No Flow prompt box on screen — open a project composer first."); return false; }
    if (box.kind === "pm") {
      // flow.google.com's ProseMirror composer: flow-composer.js inserts through the app's own
      // paste handler (a synthetic ClipboardEvent — text/plain → text + hard_break nodes at the
      // caret), falling back to execCommand("insertText"), and verifies the text landed. Async,
      // so the status line reports the outcome when it is known; the caller gets `true` meaning
      // "handed to the composer".
      const isEmpty = !ceRealText(box.el);
      const text = isEmpty ? blk.text : (blk.where === "start" ? blk.text + "\n\n" : "\n\n" + blk.text);
      status(blk.label + " — inserting…");
      self.FlowComposer.insert(text, blk.where).then((r) => {
        status(r.ok ? blk.label + " inserted (" + r.method + ") — review & submit." : "✖ " + blk.label + " not inserted: " + r.why);
      });
      return true;
    }
    box.el.focus();
    if (box.kind === "ta") {
      const cur = box.el.value || "";
      const next = blk.where === "start"
        ? blk.text + (cur ? "\n\n" + cur.replace(/^\s+/, "") : "")
        : (cur ? cur.replace(/\s+$/, "") + "\n\n" : "") + blk.text;
      // React ignores plain .value writes — go through the native setter + input event
      Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, "value").set.call(box.el, next);
      box.el.dispatchEvent(new Event("input", { bubbles: true }));
      box.el.selectionStart = box.el.selectionEnd = next.length;
    } else if (box.el.getAttribute("data-slate-editor") === "true") {
      // Flow's composer is a Slate editor. VERIFIED live (2026-07-19) against the real
      // composer: its MODEL ignores execCommand AND beforeinput entirely — those mutate
      // only the DOM, so Slate discards the text on its next re-render (it vanished on
      // blur/submit; the earlier caret-placement fix did NOT help — the model stayed
      // empty). The ONLY thing that persists is Slate's own editor.insertText, which
      // lives in the PAGE's JS world and is unreachable from this isolated content
      // script. So we hand off to flow-inject.js (a world:"MAIN" content script): stash
      // {text, where, index} in a shared #__fstBridge node and fire a "fst-insert" DOM
      // event (document is shared across worlds). flow-inject grabs the live editor off
      // the React fiber, calls editor.insertText, then editor.onChange() to re-render.
      const editors = [...document.querySelectorAll('[data-slate-editor="true"]')];
      const idx = editors.indexOf(box.el);
      const isEmpty = !ceRealText(box.el);
      // Blank-line separator on BOTH edges so it's obvious where the block landed
      const text = isEmpty ? blk.text : (blk.where === "start" ? blk.text + "\n\n" : "\n\n" + blk.text);
      let bridge = document.getElementById("__fstBridge");
      if (!bridge) { bridge = document.createElement("div"); bridge.id = "__fstBridge"; bridge.style.display = "none"; document.documentElement.appendChild(bridge); }
      bridge.textContent = JSON.stringify({ text, where: blk.where, index: idx });
      document.dispatchEvent(new Event("fst-insert"));
    } else {
      // Plain contenteditable fallback (non-Slate surfaces): caret in a real text node,
      // then execCommand insertText. Skips Slate's overlaid placeholder span.
      const isEmpty = !ceRealText(box.el);
      const toStart = isEmpty || blk.where === "start";
      const walker = document.createTreeWalker(box.el, NodeFilter.SHOW_TEXT, {
        acceptNode: (n) => (n.parentElement && n.parentElement.closest("[data-slate-placeholder]"))
          ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT,
      });
      let firstT = null, lastT = null, tn;
      while ((tn = walker.nextNode())) { if (!firstT) firstT = tn; lastT = tn; }
      const target = toStart ? firstT : lastT;
      const sel = getSelection(), range = document.createRange();
      if (target) { range.setStart(target, toStart ? 0 : target.length); range.collapse(true); }
      else { range.selectNodeContents(box.el); range.collapse(toStart); }
      sel.removeAllRanges(); sel.addRange(range);
      const text = isEmpty ? blk.text : (blk.where === "start" ? blk.text + "\n\n" : "\n\n" + blk.text);
      document.execCommand("insertText", false, text);
    }
    status(blk.label + " inserted — review & submit.");
    return true;
  }
  panel.querySelectorAll("button.pb").forEach((b) => b.addEventListener("click", () => insertPromptBlock(b.dataset.pb)));

  // ───────── 🎥 Angle card — camera/pose seeds mined from the comic corpus ─────
  // The deck is research/comic-corpus/synthesis/cards.json (76 Deed Arts seeds, one
  // per steal-worthy panel), built by research/comic-corpus/scripts/angle_deck.py from
  // every corpus/*/angle-study.json. A COPY ships beside this file as cards.json —
  // regenerate the deck, re-copy, never hand-edit. The service worker reads it for us
  // (a content script can only fetch extension files that are exposed to the page via
  // web_accessible_resources), one "angleDeck" message for the whole deck.
  // Each card is a single plain-speech sentence — camera height, nearest limb, muscle
  // sold, crop, body line — carrying no appearance and no style, meant to be APPENDED
  // after the action prompt as its final sentence.
  // ONE card at a time (2.8.5): the picker remembers the card it last placed (angleDealt)
  // and the next card takes ITS place — FlowComposer.replace() selects exactly that
  // sentence in the ProseMirror box and pastes the new one over it, so the operator's
  // own text and the staged ref chips are never touched. If the old sentence is no
  // longer in the box (edited away, or Flow cleared it) the card is appended as before.
  // 🎲 Deal me one also presses Create, so the loop is deal → generate → deal → generate…
  // (never re-dealing the card that is in the box while the filter offers another);
  // a click on a listed card only swaps the sentence in — review & submit. The legacy
  // labs.google composer keeps the plain append through insertBlock() (Slate's own
  // editor.insertText via flow-inject.js). Chip filters persist in chrome.storage.local
  // (pbAngle).
  const ANGLE_CHIPS = [["worm", "Worm"], ["low", "Low"], ["eye", "Eye"], ["high", "High"], ["dutch", "Dutch"], ["OTS", "OTS"]];
  const MUSCLE_CHIPS = [["arms", "Arms"], ["chest", "Chest"], ["back", "Back"], ["glutes", "Glutes"], ["shoulders", "Shoulders"], ["abs", "Abs"], ["full-silhouette", "Silhouette"]];
  const angleBody = $(".anglebody"), angleBtn = $(".pbangle"), angleListEl = $(".anglelist"), angleCountEl = $(".anglecount"), angleDealBtn = $(".angledeal");
  let angleDeck = null, angleFilt = { angle: [], muscle: [] }, angleLast = null;
  let angleDealt = null, angleBusy = false;   // { id, text } of the card the picker last put in the composer; a deal in flight
  const angleCards = () => (angleDeck ? angleDeck.cards : []);
  function angleVal(c, dim) { const t = c.tags || {}; return dim === "angle" ? (t.angle || c.group) : t.muscle_sold; }
  // The spec'd chips first, then any extra value a regenerated deck introduces (angle_deck.py
  // knows bird / aerial / pov too) so no card can ever hide behind a chip that isn't drawn.
  function angleChipDefs(dim) {
    const base = dim === "angle" ? ANGLE_CHIPS : MUSCLE_CHIPS;
    const known = new Set(base.map((c) => c[0])), extra = [];
    angleCards().forEach((c) => { const v = angleVal(c, dim); if (v && v !== "none" && !known.has(v)) { known.add(v); extra.push([v, v]); } });
    return base.concat(extra);
  }
  function angleMatch(c, f) { return (!f.angle.length || f.angle.includes(angleVal(c, "angle"))) && (!f.muscle.length || f.muscle.includes(angleVal(c, "muscle"))); }
  const angleFiltered = () => angleCards().filter((c) => angleMatch(c, angleFilt));
  function loadAngleDeck() {
    if (angleDeck) return Promise.resolve(angleDeck);
    return new Promise((res) => {
      chrome.runtime.sendMessage({ type: "angleDeck" }, (r) => {
        const err = chrome.runtime.lastError;
        if (err || !r || !r.ok) { status("Angle deck failed to load: " + ((r && r.error) || (err && err.message) || "no response")); angleCountEl.textContent = "deck missing"; res(null); return; }
        angleDeck = r.deck;
        // Guarded read: a stored chip value the current deck doesn't know is dropped, so a
        // stale filter can never hide every card behind a chip that isn't on screen.
        ["angle", "muscle"].forEach((dim) => { const ok = new Set(angleChipDefs(dim).map((c) => c[0])); angleFilt[dim] = angleFilt[dim].filter((v) => ok.has(v)); });
        res(angleDeck);
      });
    });
  }
  function renderAngleChips() {
    ["angle", "muscle"].forEach((dim) => {
      const row = $(".anglechips-" + dim); row.innerHTML = "";
      const lbl = document.createElement("span"); lbl.className = "clbl"; lbl.textContent = dim === "angle" ? "Angle:" : "Sells:"; row.appendChild(lbl);
      // A chip's count honours the OTHER dimension's filter — it says how many cards lighting it would leave.
      const other = dim === "angle" ? { angle: [], muscle: angleFilt.muscle } : { angle: angleFilt.angle, muscle: [] };
      angleChipDefs(dim).forEach(([k, label]) => {
        const n = angleCards().filter((c) => angleVal(c, dim) === k && angleMatch(c, other)).length;
        const b = document.createElement("button"); b.className = "chip" + (angleFilt[dim].includes(k) ? " on" : ""); b.dataset.k = k;
        b.textContent = angleDeck ? label + " " + n : label;
        b.title = (dim === "angle" ? "Camera angle: " : "Muscle the card is built to sell: ") + k + " — click to toggle. No chips lit = every card.";
        b.addEventListener("click", () => {
          const arr = angleFilt[dim], i = arr.indexOf(k);
          if (i >= 0) arr.splice(i, 1); else arr.push(k);
          chrome.storage.local.set({ pbAngle: angleFilt });
          renderAngle();
        });
        row.appendChild(b);
      });
    });
  }
  function renderAngleList() {
    angleListEl.innerHTML = "";
    const list = angleFiltered();
    angleCountEl.textContent = angleDeck ? list.length + " / " + angleCards().length + " cards" : "loading…";
    angleDealBtn.disabled = !list.length;
    if (angleDeck && !list.length) { const e = document.createElement("div"); e.className = "anglefoot"; e.textContent = "No card matches — switch a chip off."; angleListEl.appendChild(e); return; }
    list.forEach((c) => {
      const t = c.tags || {}, src = c.source || {};
      const d = document.createElement("div"); d.className = "acard" + (c.id === angleLast ? " last" : ""); d.dataset.id = c.id;
      d.title = c.text + "\n\n" + [src.artist, src.comic, "p" + src.page + "." + src.panel].filter(Boolean).join(" · ") +  " — click to put it in as the prompt's final sentence (in place of the card dealt before)";
      const l = document.createElement("div"); l.className = "acard-l";
      const st = document.createElement("span"); st.className = "acard-star"; st.textContent = "★" + (c.steal_score != null ? c.steal_score : "?");
      const lab = document.createElement("span"); lab.className = "acard-lab"; lab.textContent = c.label || c.id;
      l.append(st, lab);
      const tx = document.createElement("div"); tx.className = "acard-t"; tx.textContent = c.text;
      const f = document.createElement("div"); f.className = "acard-s";
      f.textContent = [t.shot_distance, t.crop, t.body_line].filter(Boolean).join(" · ") + " · " + (c.chars || c.text.length) + " ch" + (t.explicit ? " · 18+" : "");
      d.append(l, tx, f);
      d.addEventListener("click", () => angleAppend(c));
      angleListEl.appendChild(d);
    });
  }
  function renderAngle() { renderAngleChips(); renderAngleList(); }
  const angularComposer = () => !!(self.FlowComposer && self.FlowComposer.ui() === "angular" && self.FlowComposer.editorEl());
  // Put card `c` in the composer — over the previous card's sentence while that is still in
  // the box, else appended as the final sentence. Resolves {ok, how, why}; `legacy` = the old
  // labs.google composer, where insertBlock() did the append (and wrote the status line).
  async function anglePlace(c) {
    const FCo = self.FlowComposer;
    if (!angularComposer()) return { ok: insertBlock({ where: "end", label: "Angle card " + c.id, text: c.text }), how: "appended", legacy: true };
    const prev = angleDealt && angleDealt.text !== c.text ? angleDealt : null;
    if (angleDealt && angleDealt.text === c.text && FCo.promptText().includes(c.text)) return { ok: true, how: "already in the box" };
    if (prev) {
      const r = await FCo.replace(prev.text, c.text);
      if (r.ok) return { ok: true, how: "swapped in for " + prev.id + " (" + r.method + ")" };
      if (r.why !== "not-found") return { ok: false, why: r.why };
    }
    const r = await FCo.insert(FCo.isEmpty() ? c.text : "\n\n" + c.text, "end");
    if (!r.ok) return { ok: false, why: r.why };
    return { ok: true, how: "appended (" + r.method + ")" + (prev ? " — the previous card was no longer in the box" : "") };
  }
  function angleMark(c) {
    angleDealt = { id: c.id, text: c.text }; angleLast = c.id; renderAngleList();
    const el = angleListEl.querySelector('.acard[data-id="' + c.id + '"]'); if (el) el.scrollIntoView({ block: "nearest" });
  }
  // A listed card, clicked: swap it in, leave Create to the operator.
  async function angleAppend(c) {
    const label = "Angle card " + c.id;
    if (angularComposer()) status(label + " — inserting…");
    const r = await anglePlace(c);
    if (r.legacy) { if (r.ok) angleMark(c); return; }
    if (!r.ok) { status("✖ " + label + " not inserted: " + r.why); return; }
    angleMark(c);
    status(label + " " + r.how + " — review & submit.");
  }
  // 🎲 Deal: a fresh card from the filter (not the one already in the box, while there is
  // another), swapped in over the previous one, then Create. Click again for the next angle.
  async function angleDeal() {
    if (angleBusy) return;
    let list = angleFiltered();
    if (!list.length) { status("No angle card matches the current chips."); return; }
    if (list.length > 1 && angleDealt) list = list.filter((c) => c.id !== angleDealt.id);
    const c = list[Math.floor(Math.random() * list.length)], label = "🎲 " + c.id;
    angleBusy = true; angleDealBtn.disabled = true;
    try {
      if (angularComposer()) status(label + " — inserting…");
      const r = await anglePlace(c);
      if (r.legacy) { if (r.ok) angleMark(c); return; }
      if (!r.ok) { status("✖ " + label + " not inserted: " + r.why); return; }
      angleMark(c);
      const FCo = self.FlowComposer;
      status(label + " " + r.how + " — generating…");
      if (!(await FCo.ready(8000))) { status(label + " " + r.how + ", but Create stayed disabled (a run still submitting?) — press Create yourself."); return; }
      const f = await FCo.fire(8000);
      status(f.ok ? "✓ " + label + " " + r.how + " → generating. Deal again for the next angle." : "✖ " + label + " " + r.how + ", but Create didn't fire: " + f.why + " — press Create yourself.");
    } finally { angleBusy = false; angleDealBtn.disabled = !angleFiltered().length; }
  }
  angleDealBtn.addEventListener("click", angleDeal);
  $(".angleclear").addEventListener("click", () => { angleFilt = { angle: [], muscle: [] }; chrome.storage.local.set({ pbAngle: angleFilt }); renderAngle(); });
  $(".anglex").addEventListener("click", () => { angleBody.style.display = "none"; });
  angleBtn.addEventListener("click", () => {
    if (angleBody.style.display !== "none") { angleBody.style.display = "none"; return; }
    angleBody.style.display = "block"; renderAngle();
    loadAngleDeck().then((d) => { if (d) renderAngle(); });
  });
  chrome.storage.local.get(["pbAngle"]).then((s) => {
    const f = s.pbAngle || {}, keep = (a) => (Array.isArray(a) ? a.filter((v) => typeof v === "string") : []);
    angleFilt = { angle: keep(f.angle), muscle: keep(f.muscle) };
  });
  // Cam/Cast/Light/Render selectors — persisted so the chosen framing style and
  // lighting scheme stick across reloads.
  const camSel = $(".pbcam"), castSel = $(".pbcast"), lightSel = $(".pblight"), renderSel = $(".pbrender");
  // Light options come from the library, not from hardcoded markup: adding a scheme to
  // lighting.json and re-running build_ext.py is then the whole change. If the library
  // failed to load, the dropdown offers only the v1 block, which is also the fallback.
  (function fillLightSel() {
    const L = self.FlowLighting;
    if (!L || !L.order || !L.schemes) { lightSel.innerHTML = '<option value="golden1">Golden v1 (legacy)</option>'; pbLight = "golden1"; return; }
    L.order.forEach((grp) => {
      const og = document.createElement("optgroup");
      og.label = grp.label;
      grp.keys.forEach((k) => {
        const o = document.createElement("option");
        o.value = k; o.textContent = L.schemes[k].label; o.title = L.schemes[k].tip;
        og.appendChild(o);
      });
      lightSel.appendChild(og);
    });
    const og = document.createElement("optgroup");
    og.label = "Legacy";
    const o = document.createElement("option");
    o.value = "golden1"; o.textContent = "Golden v1";
    o.title = "The exact block shipped through v2.6.0 — kept for A/B against the tightened Golden Rake.";
    og.appendChild(o); lightSel.appendChild(og);
  })();
  // Guarded reads: a stored scheme key that no longer exists in the library (renamed or
  // removed) falls back to the default rather than emitting a prompt with no lighting.
  chrome.storage.local.get(["pbCam", "pbCast", "pbLight", "pbRender"]).then((s) => {
    const cam = s.pbCam === "low" ? "hero" : s.pbCam;   // 2.8.x height values → the 2.9.0 shot menu
    if (cam && PB_SHOT[cam]) pbCam = cam;
    if (s.pbCast && PB_CAST[s.pbCast]) pbCast = s.pbCast;
    const L = self.FlowLighting;
    if (s.pbLight && (s.pbLight === "golden1" || (L && L.schemes[s.pbLight]))) pbLight = s.pbLight;
    if (s.pbRender === "cgi" || s.pbRender === "illo") pbRender = s.pbRender;
    camSel.value = pbCam; castSel.value = pbCast;
    lightSel.value = pbLight; renderSel.value = pbRender;
  });
  camSel.addEventListener("change", () => { pbCam = camSel.value; chrome.storage.local.set({ pbCam }); });
  castSel.addEventListener("change", () => { pbCast = castSel.value; chrome.storage.local.set({ pbCast }); });
  lightSel.addEventListener("change", () => { pbLight = lightSel.value; chrome.storage.local.set({ pbLight }); });
  renderSel.addEventListener("change", () => { pbRender = renderSel.value; chrome.storage.local.set({ pbRender }); });

  // ───────── Auto-sync (continuous → Studio) ─────────────────────────────────
  // Ported from the standalone "Flow → Studio Auto-Sync" extension. While ON, a
  // timer reads the open Flow project, finds outputs not yet sent (deduped by a
  // per-project "seen" set in chrome.storage), and pushes only the fresh ones via
  // the SAME background.js port-based `studio` path the manual send uses. The
  // bridge groups identical-prompt panels into "Beat N", so they land organized.
  // Cross-origin image fetch stays in the service worker (page fetch dies on CORS).
  let autoOn = false, autoInt = 20, autoTimer = null, autoBusy = false;
  let sentSet = new Set();
  const sentKey = () => "sent:" + (FC.currentProjectId() || "none");
  const autoStatus = (t) => { if (autoStatEl) autoStatEl.textContent = t; };
  function loadSent(cb) { chrome.storage.local.get(["sentStore"]).then((s) => { sentSet = new Set((s.sentStore || {})[sentKey()] || []); cb && cb(); }); }
  function persistSent() { chrome.storage.local.get(["sentStore"]).then((s) => { const store = s.sentStore || {}; store[sentKey()] = [...sentSet].slice(-3000); chrome.storage.local.set({ sentStore: store }); }); }
  function updateAutoToggle() { autoToggleBtn.textContent = autoOn ? "● Auto-sync ON" : "○ Auto-sync OFF"; autoToggleBtn.classList.toggle("on", autoOn); }

  async function syncOnce() {
    if (busy || autoBusy) return;                       // never race a manual op or a prior tick
    if (!cfg.key) { autoStatus("Add your Studio key (⚙) to auto-sync."); return; }
    const project = projInput.value.trim();
    if (!project) { autoStatus("Type a Studio section name above to auto-sync into."); return; }
    if (!FC.currentProjectId()) { autoStatus("Open a Flow project to auto-sync."); return; }
    autoBusy = true; autoStatus("Checking Flow…");
    try {
      // flow.google.com: prompts + full-res outputs from the new project API (getAngularOutputs
      // uses each record's own image URL, so a sync tick never scrolls the user's grid). Legacy
      // labs.google UI keeps getProject()/outputList().
      const angular = self.FlowComposer && self.FlowComposer.ui() === "angular";
      let outs;
      if (angular) {
        outs = await FC.getAngularOutputs(Infinity);
        if (outs == null) { autoStatus("Couldn't read Flow — " + (FC.lastError || "reload the tab.")); autoBusy = false; return; }
      } else {
        const proj = await FC.getProject();
        if (!proj || !proj.records.length) { autoStatus("No generations yet."); autoBusy = false; return; }
        outs = FC.outputList(proj.records, Infinity);   // chronological (oldest first) → beats in order
      }
      if (!outs.length) { autoStatus("No generations yet."); autoBusy = false; return; }
      const fresh = outs.filter((o) => !sentSet.has(o.id));
      if (!fresh.length) { autoStatus("✓ Up to date · " + sentSet.size + " synced"); autoBusy = false; return; }
      autoStatus("Syncing " + fresh.length + " new…");
      const items = fresh.map((o, i) => ({ url: o.url, orig: "flow-" + String(i + 1).padStart(3, "0") + ".jpg", gen: o.gen_id || "", prompt: o.prompt || "" }));
      await new Promise((resolve) => {
        const port = chrome.runtime.connect({ name: "fst" });
        port.onMessage.addListener((m) => {
          if (m.type === "progress") { autoStatus("Syncing " + m.done + "/" + m.total + (m.fail ? " · " + m.fail + " failed" : "")); }
          else if (m.type === "done") {
            // Mark the whole batch seen on completion: re-sending succeeded items would
            // duplicate panels in the Studio, which is worse than a rare un-synced miss
            // (recover those with a manual "Whole project" send). m.fail surfaces any.
            fresh.forEach((o) => sentSet.add(o.id)); persistSent();
            autoStatus("Synced ✓ " + m.ok + "/" + m.total + " · " + sentSet.size + " total" + (m.fail ? " · " + m.fail + " failed" : ""));
            port.disconnect(); resolve();
          } else if (m.type === "error") { autoStatus("Error: " + m.message); port.disconnect(); resolve(); }
        });
        port.postMessage({ type: "start", kind: "studio", items, project, newSection: 0, cfg });
      });
    } catch (e) { console.error("[3DMC Studio Tools] auto-sync", e); autoStatus("Error — see console."); }
    autoBusy = false;
  }
  function startAuto() { stopAuto(); autoTimer = setInterval(syncOnce, Math.max(8, autoInt) * 1000); syncOnce(); }
  function stopAuto() { if (autoTimer) clearInterval(autoTimer); autoTimer = null; }

  autoToggleBtn.addEventListener("click", () => {
    autoOn = !autoOn; chrome.storage.local.set({ autoSync: autoOn, autoSyncProject: projInput.value.trim() }); updateAutoToggle();
    if (autoOn) { autoStatus("Auto-sync on. Watching…"); startAuto(); } else { autoStatus("Auto-sync off."); stopAuto(); }
  });
  autoIntInput.addEventListener("change", () => { autoInt = Math.max(8, parseInt(autoIntInput.value, 10) || 20); chrome.storage.local.set({ autoSyncInterval: autoInt }); if (autoOn) startAuto(); });
  // remember the section name across reloads (the standalone autosync persisted its project)
  projInput.addEventListener("change", () => { if (autoOn) chrome.storage.local.set({ autoSyncProject: projInput.value.trim() }); });
  // close button also stops the watcher
  $(".hd .x").addEventListener("click", stopAuto);
  // react to SPA project switches: swap in that project's own "seen" set
  let lastPid = FC.currentProjectId();
  setInterval(() => { const p = FC.currentProjectId(); if (p !== lastPid) { lastPid = p; loadSent(() => { if (autoOn) autoStatus("Switched project · " + sentSet.size + " synced"); }); } }, 3000);

  chrome.storage.local.get(["autoSync", "autoSyncInterval", "autoSyncProject"]).then((s) => {
    autoOn = !!s.autoSync; if (s.autoSyncInterval) autoInt = s.autoSyncInterval;
    if (s.autoSyncProject && !projInput.value) projInput.value = s.autoSyncProject;
    autoIntInput.value = autoInt; updateAutoToggle();
    loadSent(() => { if (autoOn) { autoStatus("Auto-sync on. Watching…"); startAuto(); } });
  });

  // ---------------- 🔬 Model bake-off ----------------
  // The engine lives in flow-bakeoff.js (it drives Flow's composer); this is just its
  // panel: which models to mirror onto, the ON/OFF switch, and the compare board.
  const BO = self.FlowBakeoff;
  if (BO) {
    BO.onStatus((t) => { bakeStatEl.textContent = t; });
    const updateBakeToggle = () => {
      bakeToggleBtn.textContent = BO.cfg.on ? "● Bake-off ON" : "○ Bake-off OFF";
      bakeToggleBtn.classList.toggle("on", BO.cfg.on);
    };
    bakeModelsEl.innerHTML = BO.MODELS.map((m) =>
      `<label class="mchk" title="${m.label}"><input type="checkbox" data-m="${m.id}"><span>${m.label.replace("Nano Banana", "NB")}</span></label>`).join("");
    const syncChecks = () => bakeModelsEl.querySelectorAll("input").forEach((i) => (i.checked = BO.cfg.models.includes(i.dataset.m)));

    bakeModelsEl.addEventListener("change", () => {
      const models = [...bakeModelsEl.querySelectorAll("input")].filter((i) => i.checked).map((i) => i.dataset.m);
      if (!models.length) { bakeStatEl.textContent = "Pick at least one model."; syncChecks(); return; }
      BO.setCfg({ models });
      bakeStatEl.textContent = "Mirroring onto: " + models.length + " model(s).";
    });
    bakeToggleBtn.addEventListener("click", () => {
      BO.setCfg({ on: !BO.cfg.on }); updateBakeToggle();
      bakeStatEl.textContent = BO.cfg.on
        ? "ON — hit Create once; the other models follow."
        : "Off — submits run on the selected model only.";
    });
    bakeCompareBtn.addEventListener("click", async () => {
      bakeCompareBtn.disabled = true; bakeStatEl.textContent = "Reading this project…";
      try {
        const data = await BO.buildCompare();
        await chrome.storage.local.set({ bakeoffCompare: data });
        chrome.runtime.sendMessage({ type: "openCompare" });
        bakeStatEl.textContent = data.error ? data.error : data.rows.length + " prompt(s) with 2+ models — opened in a new tab.";
      } catch (e) { bakeStatEl.textContent = "✖ " + ((e && e.message) || e); }
      bakeCompareBtn.disabled = false;
    });

    BO.load().then(() => { syncChecks(); updateBakeToggle(); });
  }

  FC.getAccount().then(stampAccount);
})();
