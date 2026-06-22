// Flow Studio Tools — content script (UI). One panel, three actions, all driven
// off FlowCore's single tRPC harvest: Download (disk) / Send to Studio (ingest) /
// Review bundle (outputs + refs + manifest). [Bulk delete = Phase 2.]
(() => {
  if (window.__flowStudioTools) return;
  window.__flowStudioTools = true;
  const FC = self.FlowCore;
  if (!FC) { console.error("[Flow Studio Tools] core missing"); return; }
  const DEFAULT_URL = "https://3dmusclecomics.com/studio/bridge.php";
  let cfg = { url: DEFAULT_URL, key: "" };
  let mode = "download";

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
   #fst input{width:100%;box-sizing:border-box;padding:7px 9px;border-radius:8px;border:1px solid #2e3140;background:#0f1115;color:#e8eaed;margin-bottom:8px}
   #fst .cfg{display:none} #fst.cfgopen .cfg{display:block}
   #fst .lbl{opacity:.7;font-size:12px;margin:2px 0 5px}
   #fst .row{display:flex;gap:6px;align-items:center;flex-wrap:wrap}
   #fst button.pick{flex:1;min-width:42px;padding:8px 0;border:none;border-radius:8px;background:#23252e;color:#e8eaed;cursor:pointer;font-weight:600}
   #fst button.pick:hover{background:#2e3140} #fst button.go{background:#ef9f27;color:#412402} #fst button.go:hover{filter:brightness(1.07)}
   #fst button:disabled{opacity:.45;cursor:default} #fst input.num{width:52px;margin:0}
   #fst .bar{height:6px;border-radius:4px;background:#23252e;margin:10px 0 4px;overflow:hidden} #fst .bar>i{display:block;height:100%;width:0;background:#ef9f27;transition:width .15s}
   #fst .stat{font-size:12px;opacity:.9;min-height:16px} #fst .foot{font-size:11px;opacity:.55;margin-top:6px;word-break:break-all}
   #fst.min .bd{display:none}`;
  const style = document.createElement("style"); style.textContent = css; document.documentElement.appendChild(style);
  const panel = document.createElement("div"); panel.id = "fst";
  panel.innerHTML = `
   <div class="hd"><b>Flow Studio Tools</b><span class="g" title="Studio settings">⚙</span><span class="x" title="Close">✕</span></div>
   <div class="bd">
     <div class="acct"><span class="k">Flow account:</span> <b class="acctval">…</b></div>
     <div class="tabs">
       <div class="tab on" data-mode="download">Download</div>
       <div class="tab" data-mode="studio">→ Studio</div>
       <div class="tab" data-mode="review">Review</div>
     </div>
     <div class="cfg">
       <div class="lbl">Studio bridge URL</div><input class="url" type="text">
       <div class="lbl">Studio key (Studio → Flow import)</div><input class="key" type="password" placeholder="paste your bridge key">
       <div class="row" style="margin-bottom:10px"><button class="pick savecfg">Save settings</button></div>
     </div>
     <div class="studio-only" style="display:none"><div class="lbl">Studio project (created if new)</div><input class="proj" type="text"></div>
     <div class="lbl modehint">Most-recent generations:</div>
     <div class="row"><button class="pick" data-n="5">5</button><button class="pick" data-n="10">10</button><button class="pick" data-n="25">25</button>
       <input class="num" type="number" min="1" placeholder="#"><button class="pick go" data-n="custom">Go</button></div>
     <div class="row" style="margin-top:8px"><button class="pick go" data-n="all" style="flex:1">Whole project</button></div>
     <div class="bar"><i></i></div><div class="stat">Idle — open a Flow project, pick an action.</div><div class="foot"></div>
   </div>`;
  document.documentElement.appendChild(panel);
  const $ = (s) => panel.querySelector(s);
  const accEl = $(".acctval"), urlInput = $(".url"), keyInput = $(".key"), projInput = $(".proj");
  const barFill = $(".bar>i"), statEl = $(".stat"), footEl = $(".foot"), numInput = $(".num");
  const studioOnly = $(".studio-only"), modeHint = $(".modehint");
  const buttons = [...panel.querySelectorAll("button.pick")];

  chrome.storage.local.get(["studioUrl", "bridgeKey"]).then((s) => {
    if (s.studioUrl) cfg.url = s.studioUrl; if (s.bridgeKey) cfg.key = s.bridgeKey;
    urlInput.value = cfg.url; keyInput.value = cfg.key;
  });
  projInput.value = defaultProject();

  function setMode(m) {
    mode = m;
    panel.querySelectorAll(".tab").forEach((t) => t.classList.toggle("on", t.dataset.mode === m));
    studioOnly.style.display = m === "studio" ? "block" : "none";
    if (m === "studio" && !cfg.key) panel.classList.add("cfgopen");
    modeHint.textContent = m === "download" ? "Download most-recent generations:" : m === "studio" ? "Send most-recent generations to Studio:" : "Review-bundle most-recent generations:";
  }
  panel.querySelectorAll(".tab").forEach((t) => t.addEventListener("click", () => setMode(t.dataset.mode)));

  $(".hd .x").addEventListener("click", () => { panel.remove(); style.remove(); window.__flowStudioTools = false; });
  $(".hd .g").addEventListener("click", () => panel.classList.toggle("cfgopen"));
  $(".savecfg").addEventListener("click", () => { cfg.url = urlInput.value.trim() || DEFAULT_URL; cfg.key = keyInput.value.trim(); chrome.storage.local.set({ studioUrl: cfg.url, bridgeKey: cfg.key }); statEl.textContent = "Settings saved."; panel.classList.remove("cfgopen"); });
  (() => { const hd = $(".hd"); let sx, sy, sr, sb, drag = false; hd.addEventListener("mousedown", (e) => { if (e.target.tagName === "SPAN") return; drag = true; sx = e.clientX; sy = e.clientY; const r = panel.getBoundingClientRect(); sr = innerWidth - r.right; sb = innerHeight - r.bottom; e.preventDefault(); }); addEventListener("mousemove", (e) => { if (!drag) return; panel.style.right = Math.max(0, sr - (e.clientX - sx)) + "px"; panel.style.bottom = Math.max(0, sb - (e.clientY - sy)) + "px"; }); addEventListener("mouseup", () => { drag = false; }); })();

  let busy = false;
  const setBusy = (b) => { busy = b; buttons.forEach((x) => (x.disabled = b)); };
  const setBar = (f) => { barFill.style.width = Math.round(f * 100) + "%"; };
  const status = (t) => { statEl.textContent = t; };
  function stampAccount(email) { document.documentElement.setAttribute("data-flow-account", email || "unknown"); accEl.textContent = email || "(unknown)"; accEl.style.color = email ? "#34d399" : "#fbbf24"; }

  async function run(limit) {
    if (busy) return;
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
          const project = projInput.value.trim() || defaultProject();
          payload = { items: outs.map((o, i) => ({ url: o.url, orig: "flow-" + String(i + 1).padStart(3, "0") + ".jpg" })), project, cfg };
          footEl.textContent = "→ Studio project: " + project; kind = "studio"; status("Sending " + outs.length + " to Studio…");
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
    } catch (e) { console.error("[Flow Studio Tools]", e); status("Error — see console."); }
    finally { setBusy(false); }
  }

  panel.addEventListener("click", (e) => {
    const b = e.target.closest("button.pick"); if (!b || busy || b.classList.contains("savecfg")) return;
    const n = b.dataset.n; if (!n) return;
    if (n === "all") return run(Infinity);
    if (n === "custom") { const v = parseInt(numInput.value, 10); if (v > 0) return run(v); numInput.focus(); return; }
    return run(parseInt(n, 10));
  });

  FC.getAccount().then(stampAccount);
})();
