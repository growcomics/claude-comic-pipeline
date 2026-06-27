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
   #fst .autostat{font-size:11px;opacity:.85;margin-top:6px;min-height:14px}
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
     <div class="delbody" style="display:none">
       <div class="warn">⚠ Destructive. Soft-deletes to Flow's <b>Trash</b> (recoverable via "View Trash"). Tick the tiles on the page you want gone.</div>
       <div class="row"><button class="pick selvis">Select visible</button><button class="pick clr">Clear</button></div>
       <div class="row" style="margin-top:8px"><button class="pick danger trash" style="flex:1" disabled>🗑 Move 0 to Trash</button></div>
     </div>
     <div class="bar"><i></i></div><div class="stat">Idle — open a Flow project, pick an action.</div><div class="foot"></div>
   </div>`;
  document.documentElement.appendChild(panel);
  const $ = (s) => panel.querySelector(s);
  const accEl = $(".acctval"), urlInput = $(".url"), keyInput = $(".key"), projInput = $(".proj");
  const barFill = $(".bar>i"), statEl = $(".stat"), footEl = $(".foot"), numInput = $(".num");
  const studioOnly = $(".studio-only"), modeHint = $(".modehint"), actbody = $(".actbody"), delbody = $(".delbody"), trashBtn = $(".trash");
  const autoToggleBtn = $(".autotoggle"), autoIntInput = $(".autoint"), autoStatEl = $(".autostat");
  const buttons = [...panel.querySelectorAll("button.pick")];

  chrome.storage.local.get(["studioUrl", "bridgeKey"]).then((s) => { if (s.studioUrl) cfg.url = s.studioUrl; if (s.bridgeKey) cfg.key = s.bridgeKey; urlInput.value = cfg.url; keyInput.value = cfg.key; });
  projInput.placeholder = "blank → new section each send";

  function onDelCount(n) { trashBtn.textContent = "🗑 Move " + n + " to Trash"; trashBtn.disabled = n === 0; }
  function setMode(m) {
    if (prevMode === "delete" && m !== "delete" && self.FlowDelete) self.FlowDelete.stop();
    prevMode = mode = m;
    panel.querySelectorAll(".tab").forEach((t) => t.classList.toggle("on", t.dataset.mode === m));
    const del = m === "delete";
    actbody.style.display = del ? "none" : "block";
    delbody.style.display = del ? "block" : "none";
    studioOnly.style.display = m === "studio" ? "block" : "none";
    if (m === "studio" && !cfg.key) panel.classList.add("cfgopen");
    if (del && self.FlowDelete) self.FlowDelete.start(onDelCount);
    if (!del) modeHint.textContent = m === "download" ? "Download most-recent generations:" : m === "studio" ? "Send most-recent generations to Studio:" : "Review-bundle most-recent generations:";
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
          payload = { items: outs.map((o, i) => ({ url: o.url, orig: "flow-" + String(i + 1).padStart(3, "0") + ".jpg", gen: o.gen_id || "", prompt: o.prompt || "" })), project, newSection, cfg };
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

  FC.getAccount().then(stampAccount);
})();
