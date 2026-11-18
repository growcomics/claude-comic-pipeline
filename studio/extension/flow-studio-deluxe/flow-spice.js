// 3DMC Studio Tools — 🌶 Spice, the Flow-page half. While the panel's 🌶 tab is open, every Flow image tile gets a
// 🌶 button (top-left, like 🗑 Delete's tick box). Click it → a small box (prompt presets, prompt, model, size,
// count, Siray's live price) → the image goes to a Siray image-edit model with YOUR key, via the service worker
// (spice-bg.js). The result saves to Downloads/Flow Spice/ and shows on the Spice page (spice.html). Flow itself
// is never touched. Exposes self.FlowSpice = { start, stop, settings }.
//
// DOM facts used (shared with flow-delete.js / flow-core.js): tile = flow-grid-tile-container, image =
// img[data-media-id] whose src is a same-origin https://flow.google.com/asb/<token>=s512-rw thumbnail; swapping
// the FIFE suffix gives any size (=s2048-rj = 2048px JPEG). Same-origin fetch = the signed-in session.
// The box is LIGHT DOM on purpose: Flow's key handlers check whether the event target is editable, and a
// textarea inside a shadow root is retargeted to its (non-editable) host. Key events are also stopped at the box.
(() => {
  if (self.FlowSpice) return;
  const SP = self.FOSpice;
  const bg = (msg) => new Promise((res) => {
    try { chrome.runtime.sendMessage(msg, (r) => { const le = chrome.runtime.lastError; res(r || { ok: false, reason: le ? le.message : "no reply from the extension" }); }); }
    catch (e) { res({ ok: false, reason: String((e && e.message) || e) }); }
  });
  const el = (tag, props, ...kids) => {
    const n = document.createElement(tag);
    for (const [k, v] of Object.entries(props || {})) { if (v == null) continue; if (k.startsWith("on")) n.addEventListener(k.slice(2), v); else if (k === "text") n.textContent = v; else n.setAttribute(k, v); }
    for (const k of kids.flat()) if (k != null && k !== false) n.append(k);
    return n;
  };
  const sized = (src, suffix) => /\/asb\//.test(src || "") ? src.replace(/=[^=/]*$/, "") + "=" + suffix : src;
  // Flow's full-size viewer (…/project/<id>/edit/<id>) shows the ORIGINAL from a signed
  // https://flow-content.google/image/<media id>?Expires&KeyName&Signature URL (verified live 2026-11-16: 1376×768,
  // fetchable from the page as-is). Tiles use the same-origin /asb/ thumbnail. Either is an image we can send.
  const isViewerSrc = (src) => { try { const u = new URL(src, location.href); return u.host === "flow-content.google" && /^\/image\//.test(u.pathname); } catch (e) { return false; } };
  const usable = (src) => /\/asb\//.test(src || "") || isViewerSrc(src);
  const viewerMediaId = (src) => { try { return new URL(src, location.href).pathname.split("/")[2] || ""; } catch (e) { return ""; } };

  const css = `
.fsp-btn{position:absolute;top:6px;left:6px;z-index:30;width:30px;height:30px;border-radius:50%;border:1px solid rgba(255,255,255,.35);background:rgba(20,21,28,.82);font-size:16px;line-height:28px;text-align:center;cursor:pointer;padding:0;opacity:.85}
.fsp-btn:hover{opacity:1;background:#ff5a36;border-color:#ff5a36}
#fsp-veil{position:fixed;inset:0;z-index:2147483600;background:rgba(5,6,9,.66);display:flex;align-items:center;justify-content:center;font:13px/1.4 -apple-system,system-ui,sans-serif;color:#e6e9f2}
#fsp-veil *{box-sizing:border-box}
#fsp-box{width:min(560px,calc(100% - 32px));max-height:calc(100% - 32px);overflow:auto;padding:16px;border-radius:14px;border:1px solid #2a2f43;background:#12141c;box-shadow:0 14px 40px rgba(0,0,0,.6);display:flex;flex-direction:column;gap:10px}
#fsp-box .hd{display:flex;gap:12px;align-items:center} #fsp-box .hd img{width:72px;height:72px;object-fit:cover;border-radius:8px;flex:none}
#fsp-box .sub{font-size:12px;color:#8a92aa;margin-top:2px}
#fsp-box .presets{display:flex;flex-wrap:wrap;gap:6px}
#fsp-box button{background:#1c2030;color:#e6e9f2;border:1px solid #2a2f43;border-radius:8px;padding:6px 11px;font:inherit;cursor:pointer}
#fsp-box button:hover{filter:brightness(1.2)} #fsp-box button.go{background:#ff5a36;border-color:#ff5a36;color:#fff;font-weight:600}
#fsp-box textarea{width:100%;min-height:96px;resize:vertical;padding:8px 10px;border-radius:8px;border:1px solid #2a2f43;background:#0a0c11;color:#e6e9f2;font:inherit}
#fsp-box .opts{display:flex;gap:8px} #fsp-box select{flex:1;padding:6px 8px;border-radius:8px;border:1px solid #2a2f43;background:#0a0c11;color:#e6e9f2;font:inherit;font-size:12.5px}
#fsp-box .price{font-size:11.5px;color:#8a92aa;min-height:14px}
#fsp-box .row{display:flex;gap:8px;align-items:center} #fsp-box .sp{flex:1}
#fsp-toasts{position:fixed;left:16px;bottom:16px;z-index:2147483601;display:flex;flex-direction:column;gap:6px;font:12.5px/1.4 -apple-system,system-ui,sans-serif}
.fsp-toast{padding:8px 12px;border-radius:10px;border:1px solid #2a2f43;background:#161925;color:#e6e9f2;box-shadow:0 8px 26px rgba(0,0,0,.55);max-width:440px}
.fsp-toast.err{border-color:#6b2f2f;color:#f3a3a2}
.fsp-prog{min-width:300px;border-color:#5a3326} .fsp-prog .ln{display:flex;gap:8px;align-items:center} .fsp-prog .ln b{flex:1;font-weight:600}
.fsp-prog .tm{opacity:.6;font-variant-numeric:tabular-nums} .fsp-prog .pv{width:34px;height:34px;object-fit:cover;border-radius:6px;flex:none}
.fsp-bar{height:5px;border-radius:3px;background:#262b3d;margin-top:7px;overflow:hidden;position:relative} .fsp-bar i{position:absolute;left:0;top:0;bottom:0;width:0;background:#ff5a36;border-radius:3px;transition:width .6s}
.fsp-bar.ind i{width:30%;animation:fspind 1.3s ease-in-out infinite} @keyframes fspind{0%{left:-30%}100%{left:100%}} .fsp-toast button{margin-left:8px;background:#1c2030;color:#e6e9f2;border:1px solid #2a2f43;border-radius:7px;padding:2px 8px;font:inherit;cursor:pointer}`;
  let style = null;
  const ensureStyle = () => { if (!style || !style.isConnected) { style = el("style", { text: css }); document.documentElement.appendChild(style); } };

  // ───── toasts + job watch ─────
  let toasts = null;
  function toast(text, opts) {
    opts = opts || {}; ensureStyle();
    if (!toasts || !toasts.isConnected) { toasts = el("div", { id: "fsp-toasts" }); document.documentElement.appendChild(toasts); }
    const t = el("div", { class: "fsp-toast" + (opts.err ? " err" : "") }, text);
    for (const a of [].concat(opts.action || [], opts.actions || [])) t.append(el("button", { onclick: () => { t.remove(); a.run(); } }, a.label));
    toasts.append(t);
    const plain = () => [...toasts.children].filter((x) => !x.classList.contains("fsp-prog"));
    while (plain().length > 4) plain()[0].remove();
    setTimeout(() => t.remove(), opts.ms || 5200);
    return t;
  }

  // ───── live progress: one pinned card per job, fed by the worker's storage writes + a 1 s clock ─────
  const prog = new Map();   // key (local id, then job id) → { t, word, pct, bar, tm, start, status, pctNum }
  const WORD = { UPLOAD: "Uploading image to Siray", SUBMITTED: "Sent, waiting for a slot", NOT_START: "Sent, waiting for a slot", QUEUED: "In Siray's queue", IN_PROGRESS: "Generating" };
  let clock = null;
  function progStart(key, thumbSrc) {
    ensureStyle();
    if (!toasts || !toasts.isConnected) { toasts = el("div", { id: "fsp-toasts" }); document.documentElement.appendChild(toasts); }
    const word = el("b", null, "🌶 " + WORD.UPLOAD + "…"), pct = el("span", null, ""), tm = el("span", { class: "tm" }, "0 s");
    const bar = el("div", { class: "fsp-bar ind" }, el("i"));
    const t = el("div", { class: "fsp-toast fsp-prog" }, el("div", { class: "ln" }, thumbSrc ? el("img", { class: "pv", src: thumbSrc, alt: "" }) : null, word, pct, tm), bar);
    toasts.append(t);
    prog.set(key, { t, word, pct, bar, tm, start: Date.now(), status: "UPLOAD", pctNum: null });
    if (!clock) clock = setInterval(tick, 1000);
    return key;
  }
  function progRekey(from, to) { const p = prog.get(from); if (p) { prog.delete(from); prog.set(to, p); } }
  function progUpdate(key, status, progress) {
    const p = prog.get(key); if (!p) return;
    p.status = status || p.status;
    const n = parseFloat(String(progress || "").replace("%", ""));
    p.pctNum = isFinite(n) ? Math.max(0, Math.min(100, n)) : p.pctNum;
    p.word.textContent = "🌶 " + (WORD[p.status] || p.status.toLowerCase()) + "…";
    p.pct.textContent = p.pctNum != null ? Math.round(p.pctNum) + "%" : "";
    p.bar.classList.toggle("ind", p.pctNum == null);
    p.bar.firstChild.style.width = p.pctNum != null ? p.pctNum + "%" : "";
  }
  function progEnd(key) { const p = prog.get(key); if (p) { p.t.remove(); prog.delete(key); } if (!prog.size && clock) { clearInterval(clock); clock = null; } }
  function tick() { for (const p of prog.values()) { const s = Math.round((Date.now() - p.start) / 1000); p.tm.textContent = s < 60 ? s + " s" : Math.floor(s / 60) + ":" + String(s % 60).padStart(2, "0"); } }
  const openPage = (jobId) => bg({ type: "fst-spice-open", jobId: jobId || "" });
  const mine = new Set();
  try {
    chrome.storage.onChanged.addListener((ch, area) => {
      const c = area === "local" && ch[SP.JOBS_KEY];
      if (!c || !mine.size) return;
      for (const j of c.newValue || []) {
        if (!mine.has(j.id)) continue;
        if (j.status !== "SUCCESS" && j.status !== "FAILURE") { progUpdate(j.id, j.status, j.progress); continue; }
        mine.delete(j.id); progEnd(j.id);
        const n = (j.outputs || []).length;
        const nm = SP.nextModel((j.tried || []).concat(j.model));
        const nextAct = nm ? [{ label: "↻ Try " + SP.modelById(nm).label.split(" · ")[0].replace(" 🌶", ""), run: () => tryNext(j) }] : [];
        if (j.status === "SUCCESS") toast("🌶 Done: " + n + " image" + (n === 1 ? "" : "s") + " (saving to Downloads/Flow Spice)", { ms: 20000, actions: [{ label: "Open", run: () => openPage(j.id) },
          n === 1 ? { label: "🌶 Spice again", run: () => openAgain(j, j.outputs[0]) } : { label: "🌶 Spice again…", run: () => openPage(j.id) }].concat(nextAct) });
        else toast("🌶 Spice failed: " + String(j.error || "unknown error").slice(0, 200), { err: true, ms: 20000, actions: [{ label: "Details", run: () => openPage(j.id) }].concat(nextAct) });
      }
    });
  } catch (e) {}

  // ↻ Try next model: the worker resends this job's stored input + prompt to the next model in FOSpice.NEXT.
  async function tryNext(j) {
    const key = progStart("nx" + Date.now(), (j.src && j.src.thumb) || "");
    const res = await bg({ type: "fst-spice-next", jobId: j.id });
    if (!res || !res.ok) { progEnd(key); toast("🌶 " + ((res && res.reason) || "Couldn't try the next model"), { err: true, ms: 10000 }); return; }
    mine.add(res.jobId);
    progRekey(key, res.jobId); progUpdate(res.jobId, "SUBMITTED", "");
  }

  // ───── run ─────
  async function dataUrl(src) {
    try {
      // The signed flow-content.google URL answers CORS only WITHOUT cookies (verified live 2026-11-16: "omit" → 200
      // image/jpeg, "include" → blocked); the same-origin /asb/ path needs them.
      const r = await fetch(src, { credentials: isViewerSrc(src) ? "omit" : "include" });
      const ct = r.headers.get("content-type") || "";
      if (!r.ok || !/^image\//.test(ct)) return null;
      const b = await r.blob();
      return await new Promise((res) => { const fr = new FileReader(); fr.onload = () => res(fr.result); fr.onerror = () => res(null); fr.readAsDataURL(b); });
    } catch (e) { return null; }
  }
  async function run(src, small, meta, opts) {
    const key = progStart("up" + Date.now(), sized(small, "s128"));
    const remote = /^https:\/\/([a-z0-9-]+\.)*siray\.ai\//i.test(src);   // a Spice result: Siray reads its own URL
    let [image, thumb] = remote ? [src, src] : await Promise.all([dataUrl(sized(src, "s2048-rj")), dataUrl(sized(small, "s384-rj"))]);
    if (!image && small !== src) image = await dataUrl(sized(small, "s2048-rj"));   // viewer original refused → the 2048px copy of the same image
    if (!image) { progEnd(key); toast("🌶 Couldn't load that image from Flow.", { err: true, ms: 8000 }); return; }
    const res = await bg(Object.assign({ type: "fst-spice-run", image, thumb: thumb || "", src: meta }, opts));
    if (!res || !res.ok) { progEnd(key); toast("🌶 " + ((res && res.reason) || "Spice failed"), { err: true, ms: 10000, action: res && res.needKey ? { label: "Open Spice settings", run: () => openPage() } : null }); return; }
    mine.add(res.jobId);
    progRekey(key, res.jobId); progUpdate(res.jobId, "SUBMITTED", "");
  }

  // ───── the box ─────
  let veil = null;
  function closeBox() { if (veil) { veil.remove(); veil = null; } }
  // A Flow image (grid tile or the full-size viewer) → the box.
  function openBox(img) {
    const src = img.currentSrc || img.getAttribute("src") || "";
    if (!usable(src)) { toast("🌶 That tile hasn't loaded yet — try again in a second.", { err: true }); return; }
    const tile = img.closest("flow-grid-tile-container");
    const mid = img.getAttribute("data-media-id") || (isViewerSrc(src) ? viewerMediaId(src) : "");
    const twin = !/\/asb\//.test(src) && mid ? document.querySelector('img[data-media-id="' + CSS.escape(mid) + '"]') : null;   // the viewer's filmstrip thumb
    const small = twin && /\/asb\//.test(twin.currentSrc || twin.src) ? (twin.currentSrc || twin.src) : src;
    const meta = { id: mid, title: ((tile && tile.getAttribute("aria-label")) || "").slice(0, 160), projectId: (location.pathname.match(/\/project\/([^/]+)/) || [])[1] || "" };
    return openBoxFor({ src, small, meta, ar: img.naturalWidth && img.naturalHeight ? img.naturalWidth / img.naturalHeight : 0, heading: "🌶 Spice this image" });
  }
  // A finished Spice result → the box again ("Spice again"). Siray takes the result's own URL as the input image,
  // so nothing is fetched here and nothing goes through Flow. The shape is read from the image itself.
  const jobAr = (job) => { const [x, y] = String((job && job.aspect) || "").split(":").map(Number); return x > 0 && y > 0 ? x / y : 0; };   // a result keeps its job's shape
  async function openAgain(job, url) {
    // Flow's page may refuse to load an outside image; then the job's own aspect stands in, never a square default.
    const ar = (await new Promise((res) => { const im = new Image(); im.onload = () => res(im.naturalWidth / im.naturalHeight); im.onerror = () => res(0); setTimeout(() => res(0), 3000); im.src = url; })) || jobAr(job);
    return openBoxFor({ src: url, small: url, meta: { id: "", fromJob: job.id, title: "Spice again: " + String(job.prompt || "").slice(0, 120), projectId: (job.src && job.src.projectId) || "" }, ar, heading: "🌶 Spice again (edit this result)" });
  }
  async function openBoxFor(S) {
    const { src, small, meta } = S;
    const c = await bg({ type: "fst-spice-cfg" });
    if (!c || !c.ok) { toast("🌶 The extension didn't answer. Reload this tab.", { err: true }); return; }
    if (!c.hasKey) { toast("🌶 Add your Siray API key first.", { ms: 9000, action: { label: "Open Spice settings", run: () => openPage() } }); return; }
    ensureStyle(); closeBox();
    const aspect = SP.nearestAspect(S.ar);
    const prompt = el("textarea", { rows: "5", placeholder: "What should change? e.g. Keep the same character, pose and style; make the outfit…" });
    prompt.value = c.lastPrompt || "";
    const model = el("select", null, SP.MODELS.map((m) => el("option", { value: m.id }, m.label)));
    model.value = SP.modelById(c.model).id;
    const size = el("select"), count = el("select", { title: "How many versions" }, [1, 2, 3, 4].map((n) => el("option", { value: String(n) }, "×" + n)));
    count.value = String(Math.max(1, Math.min(4, c.n || 1)));
    const price = el("div", { class: "price" });
    const fill = () => {
      const m = SP.modelById(model.value), want = size.value || c.size;
      size.replaceChildren(...m.sizes.map((s) => el("option", { value: s }, s)));
      size.value = m.sizes.includes(want) ? want : m.sizes[Math.min(1, m.sizes.length - 1)];
      count.style.display = m.n ? "" : "none";
      price.textContent = "";
      bg({ type: "fst-spice-price", model: m.id }).then((r) => { if (model.value !== m.id || !r) return; if (r.ok && r.lines.length) price.textContent = "Siray price: " + r.lines.slice(0, 3).join("  |  "); else if (r.missing) price.textContent = "⚠ " + r.reason + ". Pick another model."; });
    };
    model.addEventListener("change", fill);
    const go = () => {
      const p = prompt.value.trim();
      if (!p) { prompt.focus(); return; }
      const m = SP.modelById(model.value);
      closeBox();
      run(src, small, meta, { prompt: p, model: m.id, size: size.value, n: m.n ? +count.value : 1, aspect, ar: S.ar });
    };
    const presets = (c.presets || []).slice(0, 12);
    const box = el("div", { id: "fsp-box" },
      el("div", { class: "hd" }, el("img", { src: sized(small, "s256"), alt: "" }),
        el("div", null, el("b", null, S.heading), el("div", { class: "sub" }, "Sends it to Siray with your key · " + aspect + " · the result is a new image; Flow is not touched."))),
      presets.length ? el("div", { class: "presets" }, presets.map((p) => el("button", { title: p.prompt, onclick: () => { prompt.value = p.prompt; prompt.focus(); } }, p.name))) : null,
      prompt, el("div", { class: "opts" }, model, size, count), price,
      el("div", { class: "row" }, el("button", { title: "Key, presets and all results", onclick: () => openPage() }, "Settings & results"), el("div", { class: "sp" }),
        el("button", { onclick: closeBox }, "Cancel"), el("button", { class: "go", title: "⌘↵", onclick: go }, "🌶 Spice it")));
    veil = el("div", { id: "fsp-veil", onpointerdown: (e) => { if (e.target === veil) closeBox(); } }, box);
    // Keys typed here belong to the box, never to Flow's shortcuts (Escape = deselect-all, ⌘A = select every tile…).
    const keys = (e) => {
      e.stopPropagation();
      if (e.type !== "keydown") return;
      if (e.key === "Escape") { e.preventDefault(); closeBox(); }
      else if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) { e.preventDefault(); go(); }
    };
    ["keydown", "keyup", "keypress"].forEach((t) => veil.addEventListener(t, keys));
    document.documentElement.appendChild(veil);
    fill();
    setTimeout(() => { prompt.focus(); prompt.setSelectionRange(prompt.value.length, prompt.value.length); }, 0);
  }

  // ───── tile buttons (only while the panel's 🌶 tab is open) ─────
  let mo = null, scrollH = null, active = false;
  function decorate() {
    for (const tile of document.querySelectorAll("flow-grid-tile-container")) {
      if (!tile.querySelector("flow-image-tile img[data-media-id], img[data-media-id]")) continue;   // videos / empty slots: no 🌶
      if (tile.querySelector(":scope > .fsp-btn")) continue;
      if (getComputedStyle(tile).position === "static") tile.style.position = "relative";
      const b = el("button", { class: "fsp-btn", title: "🌶 Spice this image (Siray, your own key)" }, "🌶");
      b.addEventListener("pointerdown", (e) => e.stopPropagation());
      // The virtual grid RECYCLES tile elements, so read the image at click time, never at decorate time.
      b.addEventListener("click", (e) => { e.preventDefault(); e.stopPropagation(); const img = tile.querySelector("img[data-media-id]"); if (img) openBox(img); });
      tile.appendChild(b);
    }
  }
  // Flow's full-size viewer (click a tile) has no grid tile, so a floating 🌶 sits on its top-left instead. The
  // viewer image = the largest same-origin /asb/ <img> outside the grid that covers a good part of the window.
  // Found by size, not by Flow's element names, so a viewer redesign doesn't break it.
  let viewBtn = null;
  function viewerImg() {
    let best = null, area = 0;
    for (const img of document.querySelectorAll("img")) {
      if (img.closest("flow-grid-tile-container, #fsp-veil")) continue;
      if (!usable(img.currentSrc || img.getAttribute("src") || "")) continue;
      const r = img.getBoundingClientRect();
      // Big in EITHER direction: a portrait original in a wide window is tall but narrow (measured 2026-11-17: an
      // 894×1198 image shown 500×670 in a 1710×896 window, under the old 30%-of-width cut-off, so it got no 🌶).
      if (Math.min(r.width, r.height) < 200 || (r.width < innerWidth * 0.3 && r.height < innerHeight * 0.45)) continue;
      if (r.width * r.height > area) { area = r.width * r.height; best = img; }
    }
    return best;
  }
  function placeViewBtn() {
    const img = active ? viewerImg() : null;
    if (!img) { if (viewBtn) viewBtn.style.display = "none"; return; }
    if (!viewBtn || !viewBtn.isConnected) {
      viewBtn = el("button", { class: "fsp-btn fsp-view", title: "🌶 Spice this image (Siray, your own key)" }, "🌶");
      viewBtn.addEventListener("pointerdown", (e) => e.stopPropagation());
      viewBtn.addEventListener("click", (e) => { e.preventDefault(); e.stopPropagation(); const cur = viewerImg(); if (cur) openBox(cur); });
      document.documentElement.appendChild(viewBtn);
    }
    const r = img.getBoundingClientRect();
    Object.assign(viewBtn.style, { display: "", position: "fixed", left: Math.max(4, r.left + 12) + "px", top: Math.max(4, r.top + 12) + "px", zIndex: "2147483000", width: "40px", height: "40px", fontSize: "21px", lineHeight: "38px" });
  }
  function start() {
    if (active) return; active = true; ensureStyle(); decorate();
    placeViewBtn();
    mo = new MutationObserver(() => { clearTimeout(mo._t); mo._t = setTimeout(() => { decorate(); placeViewBtn(); }, 150); });
    mo.observe(document.body, { childList: true, subtree: true });
    scrollH = () => { clearTimeout(self.__fspS); self.__fspS = setTimeout(() => { decorate(); placeViewBtn(); }, 120); };
    addEventListener("scroll", scrollH, true);
    addEventListener("resize", scrollH);
  }
  function stop() {
    if (!active) return; active = false;
    if (mo) { mo.disconnect(); mo = null; } if (scrollH) { removeEventListener("scroll", scrollH, true); removeEventListener("resize", scrollH); scrollH = null; }
    if (viewBtn) { viewBtn.remove(); viewBtn = null; }
    document.querySelectorAll(".fsp-btn").forEach((b) => b.remove());
    closeBox();
  }
  self.FlowSpice = { start, stop, settings: () => openPage(), isActive: () => active };
})();
