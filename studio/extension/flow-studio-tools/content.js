// 3DMC Studio Tools — Flow content script (UI). One panel, four actions, all driven
// off FlowCore's single tRPC harvest: Download (disk) / Send to Studio (ingest) /
// Review bundle (outputs + refs + manifest) / Bulk delete (guarded, via FlowDelete).
(() => {
  if (window.__flowStudioTools) return;
  window.__flowStudioTools = true;
  const FC = self.FlowCore;
  if (!FC) { console.error("[3DMC Studio Tools] core missing"); return; }
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
   #fst.min .bd{display:none}`;
  const style = document.createElement("style"); style.textContent = css; document.documentElement.appendChild(style);
  const panel = document.createElement("div"); panel.id = "fst";
  panel.innerHTML = `
   <div class="hd"><b>3DMC Studio Tools</b><span class="g" title="Studio settings">⚙</span><span class="x" title="Close">✕</span></div>
   <div class="bd">
     <div class="acct"><span class="k">Flow account:</span> <b class="acctval">…</b></div>
     <div class="tabs">
       <div class="tab on" data-mode="download">Download</div>
       <div class="tab" data-mode="studio">→ Studio</div>
       <div class="tab" data-mode="review">Review</div>
       <div class="tab" data-mode="bakeoff" title="Model bake-off — run each prompt on every Nano Banana model, then compare">🔬</div>
       <div class="tab del" data-mode="delete">🗑</div>
     </div>
     <div class="cfg">
       <div class="lbl">Studio bridge URL</div><input class="url" type="text">
       <div class="lbl">Studio key (Studio → Flow import)</div><input class="key" type="password" placeholder="paste your bridge key">
       <div class="row" style="margin-bottom:10px"><button class="pick savecfg">Save settings</button></div>
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
     <div class="row" style="margin-top:8px"><span class="lbl" style="margin:0 4px 0 0">Prompt:</span><button class="pick pb" data-pb="director" title="Append the director's-choice reframe block — attach a panel as ref; the scene stays, the model re-stages the camera (dolly / orbit / height / zoom) for this specific beat. Unlike Cine+Light/Framing it prescribes NO fixed angle, so it never ruts into low-hero shots.">🎥 Director</button><button class="pick pb" data-pb="cine" title="Append the cinematic-framing + golden-hour volume-lighting master block (fresh generations only — it directs the camera, so don't pair it with the i2i keep-composition lock). Camera height + figure count follow the Cam/Cast selectors below.">📷 Cine+Light</button><button class="pick pb" data-pb="frame" title="Append the cinematic-framing block ONLY — hero staging, no lighting (fresh generations only; like Cine+Light it directs the camera, so don't pair it with the i2i keep-composition lock). Camera height + figure count follow the Cam/Cast selectors below.">🎬 Framing</button><button class="pick pb" data-pb="sheet" title="Append the character turnaround-sheet block — attach the character as ref; asks for the character's name (blank = no name plate). Front + back + side profile + face close-up on a clean studio background.">🧍 Char sheet</button><button class="pick pb" data-pb="daz" title="Prepend the canonical DAZ3D style prefix — style anchors lead the prompt">🎨 DAZ style</button></div>
     <div class="row" style="margin-top:6px"><span class="lbl" style="margin:0 4px 0 0">Cam:</span><select class="pbsel pbcam" title="Camera height for Cine+Light / Framing. Vary = the model picks the height that serves the beat (never ruts into low-hero shots)."><option value="vary">Vary per beat</option><option value="low">Low hero</option><option value="eye">Eye-level</option><option value="high">High look-down</option></select><span class="lbl" style="margin:0 4px 0 6px">Cast:</span><select class="pbsel pbcast" title="Figure count the Cine+Light / Framing staging assumes. Auto = neutral wording that never asserts a count — no phantom second figure."><option value="auto">Auto</option><option value="solo">Solo</option><option value="duo">Duo</option></select></div>
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

  chrome.storage.local.get(["studioUrl", "bridgeKey"]).then((s) => { if (s.studioUrl) cfg.url = s.studioUrl; if (s.bridgeKey) cfg.key = s.bridgeKey; urlInput.value = cfg.url; keyInput.value = cfg.key; });
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
  $(".savecfg").addEventListener("click", () => { cfg.url = urlInput.value.trim() || DEFAULT_URL; cfg.key = keyInput.value.trim(); chrome.storage.local.set({ studioUrl: cfg.url, bridgeKey: cfg.key }); statEl.textContent = "Settings saved."; panel.classList.remove("cfgopen"); });
  $(".selvis").addEventListener("click", () => { if (self.FlowDelete) self.FlowDelete.selectVisible(); });
  $(".clr").addEventListener("click", () => { if (self.FlowDelete) self.FlowDelete.clear(); });
  trashBtn.addEventListener("click", runTrash);
  (() => { const hd = $(".hd"); let sx, sy, sr, sb, drag = false; hd.addEventListener("mousedown", (e) => { if (e.target.tagName === "SPAN") return; drag = true; sx = e.clientX; sy = e.clientY; const r = panel.getBoundingClientRect(); sr = innerWidth - r.right; sb = innerHeight - r.bottom; e.preventDefault(); }); addEventListener("mousemove", (e) => { if (!drag) return; panel.style.right = Math.max(0, sr - (e.clientX - sx)) + "px"; panel.style.bottom = Math.max(0, sb - (e.clientY - sy)) + "px"; }); addEventListener("mouseup", () => { drag = false; }); })();

  let busy = false;
  const setBusy = (b) => { busy = b; buttons.forEach((x) => (x.disabled = b)); };
  const setBar = (f) => { barFill.style.width = Math.round(f * 100) + "%"; };
  const status = (t) => { statEl.textContent = t; };
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
    setBar(1); status("Done ✓ " + res.done + " trashed" + (res.miss ? " · " + res.miss + " not found (scroll + retry)" : ""));
    onDelCount(self.FlowDelete.count()); setBusy(false);
  }

  async function run(limit) {
    if (busy || mode === "delete") return;
    if (mode === "studio" && !cfg.key) { panel.classList.add("cfgopen"); status("Paste your Studio key (⚙) first."); keyInput.focus(); return; }
    setBusy(true); setBar(0); footEl.textContent = "";
    try {
      status("Reading project…");
      const [proj, account] = await Promise.all([FC.getProject(), FC.getAccount()]);
      stampAccount(account);
      if (!proj) { status("No project data — open a Flow project (/project/<id>), let it load, then retry."); return; }
      if (!proj.records.length) { status("No generations found in this project."); return; }
      let kind, payload;
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
    if (b.classList.contains("savecfg") || b.classList.contains("selvis") || b.classList.contains("clr") || b.classList.contains("trash")) return;
    const n = b.dataset.n; if (!n) return;
    if (n === "all") return run(Infinity);
    if (n === "custom") { const v = parseInt(numInput.value, 10); if (v > 0) return run(v); numInput.focus(); return; }
    return run(parseInt(n, 10));
  });

  // ───────── Prompt blocks — one-click paste of canonical prompt presets ─────
  // Sources: skills/comic-production/references/prompt-templates.md (Style Prefix —
  // exact tested wording, do not rewrite) and cinematic-framing.md (hero framing +
  // "volume block" golden-hour lighting). Five blocks:
  //   • daz      — style prefix, PREPENDS (style anchors lead the prompt)
  //   • director — scene-adaptive reframe, APPENDS — attach a source panel as ref;
  //                the model chooses the camera (dolly/orbit/height/zoom) for the
  //                beat instead of a prescribed angle. Keeps scene + lighting.
  //   • sheet    — character turnaround reference page, APPENDS — attach the
  //                character as ref; front/back/side + face close-up on a clean
  //                studio background. askName: prompts for the character's name on
  //                click (blank = "no text/name plate" variant) — never leaves an
  //                unfilled [placeholder] in the prompt (documented failure mode).
  //   • cine     — framing + golden-hour lighting master block, APPENDS
  //   • frame    — framing ONLY (no lighting), APPENDS — for pairing with a separate
  //                lighting choice, or when you'll relight the panel afterward
  // cine + frame are PARAMETERIZED by the Cam:/Cast: selectors (persisted):
  //   Cam  — vary (default; the model picks the height per beat — fixes the old
  //          hardcoded "below chest height" low-angle rut) / low / eye / high
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
    cine: { where: "end", label: "Cine+Light block", build: () => pbFramingText() + pbLightingText() },
    frame: { where: "end", label: "Framing block", build: () => pbFramingText() }
  };
  // ── Cam/Cast variant system for cine + frame ──────────────────────────────
  // The old blocks hardcoded "camera slightly below chest height" and "both women",
  // which rutted every generation into a low duo shot. Height and cast are now
  // selected in the panel (persisted in chrome.storage) and the block text is
  // assembled per click. Wording is de-gendered ("figure") — appearance is carried
  // by the attached refs, never by the prompt (refs-are-truth).
  const PB_CAM = {
    vary: "Camera and framing: choose the camera height that serves this specific beat — drop below chest height and tilt up when power or dominance is the story, hold natural eye level for connection and confidence, rise above head height and look down when scale, vulnerability, or the geography of the scene carries the moment; do NOT default to a low hero angle. Whatever the height, %STAND% on the same ground plane as the camera, normal human proportions, no wide-angle distortion.",
    low: "Camera and framing: the camera sits slightly below chest height, tilted up a gentle ten degrees — low enough that the physiques loom with quiet authority, never so steep that proportions distort; %STAND% on the same ground plane as the camera, normal human proportions, no wide-angle distortion.",
    eye: "Camera and framing: the camera sits at natural eye level, held level with no tilt — a grounded, confident vantage that lets the physiques carry the frame on sheer mass; %STAND% on the same ground plane as the camera, normal human proportions, no wide-angle distortion.",
    high: "Camera and framing: the camera sits above head height, tilted gently down — high enough to read the staging and the scale of the physiques against the space, never so steep that proportions distort; %STAND% on the same ground plane as the camera, normal human proportions, no wide-angle distortion."
  };
  const PB_CAST = {
    auto: {
      stand: "every figure stands",
      dominate: "the upper bodies dominate the frame", pop: "the figures pop",
      staging: "Staging breaks the camera plane deliberately: nothing stands flat and parallel to the lens. Whoever is in frame sits on a diagonal axis running from lower-left toward upper-right — if more than one figure is present, angle them toward each other with visible intent, one nearer the camera and meaningfully larger in frame, silhouettes slightly overlapping — so the composition reads in distinct depth layers: an out-of-focus environmental element grazing a lower corner in the extreme foreground, the figure or figures in the mid-ground, the readable environment behind, with asymmetric negative space above one shoulder line giving the masses room to read as mass.",
      faces: "Every face in frame is visible and carries the beat's emotion clearly.",
      rake: "rakes across every figure in frame", rim: "tracing each silhouette",
      closer: "The overall shape of the shot is dynamic and diagonal: intent angles, overlapping depth layers, varied scale, and not a single element sitting flat against the picture plane."
    },
    solo: {
      stand: "the figure stands",
      dominate: "the upper body dominates the frame", pop: "the figure pops",
      staging: "Staging breaks the camera plane deliberately: nothing stands flat and parallel to the lens. The figure is set on a diagonal axis, body angled roughly forty-five degrees to the lens rather than square, weight shifted so the silhouette reads dynamic, so the composition reads in distinct depth layers: an out-of-focus environmental element grazing a lower corner in the extreme foreground, the figure commanding the mid-ground, the readable environment behind, with asymmetric negative space above one shoulder line giving the mass room to read as mass.",
      faces: "The face is visible and carries the beat's emotion clearly.",
      rake: "rakes across the figure's body", rim: "tracing the silhouette",
      closer: "The overall shape of the shot is dynamic and diagonal: intent angles, layered depth between figure and environment, and not a single element sitting flat against the picture plane."
    },
    duo: {
      stand: "both figures stand",
      dominate: "the upper bodies dominate the frame", pop: "the figures pop",
      staging: "Staging breaks the camera plane deliberately: nothing stands flat and parallel to the lens. The two figures sit on a diagonal axis from lower-left toward upper-right, angled toward each other with visible intent, one nearer the camera and meaningfully larger in frame, the other a step deeper and smaller by perspective, silhouettes slightly overlapping, so the composition reads in distinct depth layers — foreground figure, mid-ground figure, environment behind, with an out-of-focus environmental element grazing a lower corner in the extreme foreground and asymmetric negative space above one shoulder line giving the masses room to read as mass.",
      faces: "Both faces are visible and carry the beat's emotion clearly.",
      rake: "rakes across both figures' bodies", rim: "tracing both silhouettes",
      closer: "The overall shape of the shot is dynamic and diagonal: intent angles, overlapping depth layers, varied scale between figures, and not a single element sitting flat against the picture plane."
    }
  };
  let pbCam = "vary", pbCast = "auto";
  function pbFramingText() {
    const c = PB_CAST[pbCast];
    return PB_CAM[pbCam].replace("%STAND%", c.stand) +
      " Framed from mid-thigh up so " + c.dominate + ", at a three-quarter angle forty-five degrees between front and side — the most sculptural angle for figure work, showing chest depth, arm peaks, and thigh sweep simultaneously instead of flattening them into symmetry — with gentle 50–85mm portrait-lens compression so " + c.pop + " from the background. " +
      c.staging + " " + c.faces + " " + c.closer;
  }
  function pbLightingText() {
    const c = PB_CAST[pbCast];
    return " Lighting: late golden-hour sunlight, the sun low on the horizon to the left of frame, throwing long warm light that skims almost parallel across the scene and " + c.rake + " at a shallow grazing angle, so every muscle group is modeled with a full highlight-to-shadow gradient — bright warm gold where each muscle faces the sun, rolling through midtone amber, falling into soft warm shadow on the far side of every curve. Because the light arrives from the side, every ridge and swell casts its own small shadow and every hollow deepens: ambient-occlusion shadows one stop deeper in every crease where muscle heads meet — the separation between shoulder and arm, between the heads of arms and legs, along the spine and the abdominal wall — so each muscle reads as its own distinct, rounded volume. Striations, veins, and tendon lines catch the raking light and cast crisp micro-shadows. The skin carries a glossy sheen of sweat, with tight specular highlights riding the highest point of every muscle peak and sweat beads sparkling on the lit side. A subtle warm rim light wraps from behind, " + c.rim + " with a thin amber edge along shoulders, arms, hips, and legs — lifting them off the background without ever becoming a glow or outline. The environment sits half a stop darker than the figures, catching the same warm dusk light through a veil of light atmospheric haze, slightly cooler and softer, with faint dust motes drifting in the low sun shafts, so the bodies pop forward as the brightest, sharpest, warmest things in frame; nearby surfaces return a faint warm bounce that keeps shadow sides luminous rather than black. Everything is photoreal DAZ3D CGI render quality — no restyling, no illustration drift, no added blur.";
  }
  function findPromptBox() {
    const vis = (el) => el.offsetParent !== null && el.getBoundingClientRect().height > 0 && !panel.contains(el);
    // Flow's composer is a Slate contenteditable (data-slate-editor) — prefer it.
    const slate = [...document.querySelectorAll('[data-slate-editor="true"]')].filter(vis)[0];
    if (slate) return { el: slate, kind: "ce" };
    const tas = [...document.querySelectorAll("textarea")].filter(vis);
    const ta = tas.find((t) => /what do you want/i.test(t.placeholder || "")) || tas[0];
    if (ta) return { el: ta, kind: "ta" };
    const ce = [...document.querySelectorAll('[contenteditable="true"]')].filter(vis)[0];
    return ce ? { el: ce, kind: "ce" } : null;
  }
  function ceRealText(el) {
    // textContent includes Slate's in-DOM placeholder + zero-width chars; exclude both
    const clone = el.cloneNode(true);
    clone.querySelectorAll("[data-slate-placeholder]").forEach((n) => n.remove());
    return clone.textContent.replace(/[﻿​]/g, "").trim();
  }
  function insertPromptBlock(kind) {
    let blk = PROMPT_BLOCKS[kind]; if (!blk) return;
    if (blk.build) blk = Object.assign({}, blk, { text: blk.build(), label: blk.label + " (cam: " + pbCam + " · cast: " + pbCast + ")" });
    if (blk.askName) {
      const nm = window.prompt("Character name for the sheet's name plate (leave blank for no name):", "");
      if (nm === null) return; // cancelled
      const t = nm.trim();
      blk = Object.assign({}, blk, { text: t ? blk.textNamed.replace("%NAME%", t.toUpperCase()) : blk.text });
    }
    const box = findPromptBox();
    if (!box) { status("No Flow prompt box on screen — open a project composer first."); return; }
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
  }
  panel.querySelectorAll("button.pb").forEach((b) => b.addEventListener("click", () => insertPromptBlock(b.dataset.pb)));
  // Cam/Cast selectors — persisted so the chosen framing style sticks across reloads
  const camSel = $(".pbcam"), castSel = $(".pbcast");
  chrome.storage.local.get(["pbCam", "pbCast"]).then((s) => {
    if (s.pbCam && PB_CAM[s.pbCam]) pbCam = s.pbCam;
    if (s.pbCast && PB_CAST[s.pbCast]) pbCast = s.pbCast;
    camSel.value = pbCam; castSel.value = pbCast;
  });
  camSel.addEventListener("change", () => { pbCam = camSel.value; chrome.storage.local.set({ pbCam }); });
  castSel.addEventListener("change", () => { pbCast = castSel.value; chrome.storage.local.set({ pbCast }); });

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
      const proj = await FC.getProject();
      if (!proj || !proj.records.length) { autoStatus("No generations yet."); autoBusy = false; return; }
      const outs = FC.outputList(proj.records, Infinity);   // chronological (oldest first) → beats in order
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
