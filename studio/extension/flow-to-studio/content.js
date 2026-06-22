// Flow → 3DMC Studio — content script.
// Scans a Google Flow project's (virtualized) gallery and sends the chosen
// images straight into a Comic Studio project via the Studio bridge. Harvesting
// logic is shared with the Flow Bulk Downloader; the action is "POST to Studio".

(() => {
  if (window.__flow2studio) return;
  window.__flow2studio = true;
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const DEFAULT_URL = "https://3dmusclecomics.com/studio/bridge.php";

  // ---- Flow image harvesting (shared with the downloader) ------------------
  function upgradeGuc(url) {
    try { const u = new URL(url); return (u.origin + u.pathname).replace(/=[\w-]+$/, "") + "=s0"; }
    catch (e) { return url; }
  }
  function genImage(img) {
    const raw = img.currentSrc || img.src; if (!raw) return null;
    let u; try { u = new URL(raw); } catch (e) { return null; }
    if (u.host === "labs.google" && /media\.getMediaUrlRedirect/.test(u.pathname)) {
      const name = u.searchParams.get("name"); if (!name) return null;
      return { key: name, url: raw, up: raw };
    }
    if (/googleusercontent\.com$/.test(u.host)) {
      if (/^\/a\//.test(u.pathname)) return null;
      if ((img.naturalWidth || 0) && img.naturalWidth < 200) return null;
      const up = upgradeGuc(raw); return { key: up, url: raw, up };
    }
    return null;
  }
  function findScroller() {
    let best = document.scrollingElement || document.documentElement, bestArea = 0;
    for (const el of document.querySelectorAll("*")) {
      const oy = getComputedStyle(el).overflowY;
      if ((oy === "auto" || oy === "scroll") && el.scrollHeight - el.clientHeight > 200) {
        const area = el.clientWidth * el.clientHeight;
        if (area > bestArea) { bestArea = area; best = el; }
      }
    }
    return best;
  }
  async function scan(target, onTick) {
    const collected = new Map(); const scroller = findScroller();
    scroller.scrollTo({ top: 0 }); await sleep(350);
    const collectNow = () => {
      for (const img of document.querySelectorAll("img")) {
        const g = genImage(img); if (g && !collected.has(g.key)) collected.set(g.key, { up: g.up, raw: g.url });
      }
    };
    collectNow(); onTick(collected.size);
    let lastTop = -1, stable = 0;
    for (let i = 0; i < 800 && stable < 4 && collected.size < target; i++) {
      scroller.scrollBy(0, Math.max(200, scroller.clientHeight * 0.85)); await sleep(420);
      collectNow(); onTick(collected.size);
      const top = scroller.scrollTop;
      if (Math.abs(top - lastTop) < 4) stable++; else stable = 0;
      lastTop = top;
    }
    scroller.scrollTo({ top: 0 });
    const all = [...collected.values()];
    return target === Infinity ? all : all.slice(0, target);
  }
  function defaultProject() {
    let t = (document.title || "").replace(/[\\/:*?"<>|]+/g, " ").replace(/\s*[-–|].*$/, "").trim();
    return (t || "Flow import").slice(0, 60);
  }

  // ---- config (chrome.storage) --------------------------------------------
  let cfg = { url: DEFAULT_URL, key: "" };
  chrome.storage.local.get(["studioUrl", "bridgeKey"]).then((s) => {
    if (s.studioUrl) cfg.url = s.studioUrl;
    if (s.bridgeKey) cfg.key = s.bridgeKey;
    urlInput.value = cfg.url; keyInput.value = cfg.key;
    if (!cfg.key) panel.classList.add("cfgopen");
  });

  // ---- UI ------------------------------------------------------------------
  const css = `
   #f2s{position:fixed;right:20px;bottom:20px;z-index:2147483647;width:330px;background:#14151c;color:#e8eaed;
     border-radius:12px;box-shadow:0 8px 30px rgba(0,0,0,.55);font:13px system-ui,sans-serif;overflow:hidden;border:1px solid #2e3140}
   #f2s .hd{display:flex;align-items:center;gap:8px;padding:10px 12px;background:#191b24;cursor:move;user-select:none}
   #f2s .hd b{flex:1;font-size:13px} #f2s .hd span{cursor:pointer;opacity:.7;padding:2px 6px;border-radius:6px} #f2s .hd span:hover{background:#2e3140;opacity:1}
   #f2s .bd{padding:12px} #f2s .lbl{opacity:.7;font-size:12px;margin:2px 0 5px}
   #f2s input{width:100%;box-sizing:border-box;padding:7px 9px;border-radius:8px;border:1px solid #2e3140;background:#0f1115;color:#e8eaed;margin-bottom:8px}
   #f2s .cfg{display:none} #f2s.cfgopen .cfg{display:block}
   #f2s .row{display:flex;gap:6px;align-items:center;flex-wrap:wrap}
   #f2s button.pick{flex:1;min-width:42px;padding:8px 0;border:none;border-radius:8px;background:#23252e;color:#e8eaed;cursor:pointer;font-weight:600}
   #f2s button.pick:hover{background:#2e3140} #f2s button.go{background:#ef9f27;color:#412402} #f2s button.go:hover{filter:brightness(1.07)}
   #f2s button:disabled{opacity:.45;cursor:default} #f2s input.num{width:52px;margin:0}
   #f2s .bar{height:6px;border-radius:4px;background:#23252e;margin:10px 0 4px;overflow:hidden} #f2s .bar>i{display:block;height:100%;width:0;background:#ef9f27;transition:width .15s}
   #f2s .stat{font-size:12px;opacity:.85} #f2s .foot{font-size:11px;opacity:.55;margin-top:6px;word-break:break-all}
   #f2s.min .bd{display:none}`;
  const style = document.createElement("style"); style.textContent = css; document.documentElement.appendChild(style);
  const panel = document.createElement("div"); panel.id = "f2s";
  panel.innerHTML = `
   <div class="hd"><b>→ 3DMC Studio</b><span class="g" title="Settings">⚙</span><span class="x" title="Close">✕</span></div>
   <div class="bd">
     <div class="cfg">
       <div class="lbl">Studio bridge URL</div><input class="url" type="text">
       <div class="lbl">Studio key (from Studio → Flow import)</div><input class="key" type="password" placeholder="paste your bridge key">
       <div class="row" style="margin-bottom:10px"><button class="pick savecfg">Save settings</button></div>
     </div>
     <div class="lbl">Studio project (created if new)</div><input class="proj" type="text">
     <div class="lbl">Send most-recent images (top of gallery):</div>
     <div class="row"><button class="pick" data-n="5">5</button><button class="pick" data-n="10">10</button><button class="pick" data-n="20">20</button>
       <input class="num" type="number" min="1" placeholder="#"><button class="pick go" data-n="custom">Send</button></div>
     <div class="row" style="margin-top:8px"><button class="pick go" data-n="all" style="flex:1">Send ALL to Studio</button></div>
     <div class="bar"><i></i></div><div class="stat">Idle.</div><div class="foot"></div>
   </div>`;
  document.documentElement.appendChild(panel);
  const $ = (s) => panel.querySelector(s);
  const urlInput = $(".url"), keyInput = $(".key"), projInput = $(".proj");
  const barFill = $(".bar>i"), statEl = $(".stat"), footEl = $(".foot"), numInput = $(".num");
  const buttons = [...panel.querySelectorAll("button.pick")];
  projInput.value = defaultProject();

  $(".hd .x").addEventListener("click", () => { panel.remove(); style.remove(); window.__flow2studio = false; });
  $(".hd .g").addEventListener("click", () => panel.classList.toggle("cfgopen"));
  $(".savecfg").addEventListener("click", () => {
    cfg.url = urlInput.value.trim() || DEFAULT_URL; cfg.key = keyInput.value.trim();
    chrome.storage.local.set({ studioUrl: cfg.url, bridgeKey: cfg.key });
    statEl.textContent = "Settings saved."; panel.classList.remove("cfgopen");
  });
  (() => { // drag
    const hd = $(".hd"); let sx, sy, sr, sb, drag = false;
    hd.addEventListener("mousedown", (e) => { if (e.target.tagName === "SPAN") return; drag = true; sx = e.clientX; sy = e.clientY; const r = panel.getBoundingClientRect(); sr = innerWidth - r.right; sb = innerHeight - r.bottom; e.preventDefault(); });
    addEventListener("mousemove", (e) => { if (!drag) return; panel.style.right = Math.max(0, sr - (e.clientX - sx)) + "px"; panel.style.bottom = Math.max(0, sb - (e.clientY - sy)) + "px"; });
    addEventListener("mouseup", () => { drag = false; });
  })();

  let busy = false;
  const setBusy = (b) => { busy = b; buttons.forEach((x) => (x.disabled = b)); };
  const setBar = (f) => { barFill.style.width = Math.round(f * 100) + "%"; };

  async function run(target) {
    if (busy) return;
    if (!cfg.key) { panel.classList.add("cfgopen"); statEl.textContent = "Paste your Studio key first (⚙)."; keyInput.focus(); return; }
    const project = projInput.value.trim() || defaultProject();
    setBusy(true); setBar(0); footEl.textContent = "";
    try {
      statEl.textContent = target === Infinity ? "Scanning all…" : `Scanning for ${target}…`;
      const items = await scan(target, (n) => { statEl.textContent = `Scanning… ${n} found`; });
      if (!items.length) { statEl.textContent = "No images found — scroll the gallery into view, then retry."; return; }
      footEl.textContent = "→ Studio project: " + project;
      statEl.textContent = `Sending 0/${items.length}…`;
      await new Promise((resolve) => {
        const port = chrome.runtime.connect({ name: "flow-studio" });
        port.onMessage.addListener((m) => {
          if (m.type === "progress") { setBar(m.done / m.total); statEl.textContent = `Sending ${m.done}/${m.total}…` + (m.fail ? ` · ${m.fail} failed` : ""); }
          else if (m.type === "done") { setBar(1); statEl.textContent = `Done ✓ ${m.ok}/${m.total} sent` + (m.fail ? ` · ${m.fail} failed` : "") + ` → open Studio`; port.disconnect(); resolve(); }
          else if (m.type === "error") { statEl.textContent = "Error: " + m.message; port.disconnect(); resolve(); }
        });
        port.postMessage({ type: "start", items, project, cfg });
      });
    } catch (e) { console.error("[Flow→Studio]", e); statEl.textContent = "Error — see console."; }
    finally { setBusy(false); }
  }
  panel.addEventListener("click", (e) => {
    const b = e.target.closest("button.pick"); if (!b || busy || b.classList.contains("savecfg")) return;
    const n = b.dataset.n; if (!n) return;
    if (n === "all") return run(Infinity);
    if (n === "custom") { const v = parseInt(numInput.value, 10); if (v > 0) return run(v); numInput.focus(); return; }
    return run(parseInt(n, 10));
  });
})();
