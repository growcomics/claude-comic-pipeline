// 3DMC Studio Tools — Patreon module (self-contained, patreon.com only).
//
// Folded in from the standalone "Patreon Gallery Downloader" extension. This is a
// SEPARATE content script (manifest scopes it to https://www.patreon.com/*), so it
// never touches the Flow panel and the Flow scripts never touch Patreon — one
// install, two non-overlapping surfaces. It injects its own small panel on a post
// page, collects the post's full-res gallery in-page, and hands the list to the
// shared background worker (`type:"patreonDownload"`) which does the actual saving.
(() => {
  if (window.top !== window) return;            // top frame only — skip Patreon's embeds
  if (window.__fstPatreon) return;
  window.__fstPatreon = true;

  // ───────── collector (ported verbatim from collect.js) ─────────────────────
  // Patreon is an SPA: navigating between posts swaps content via XHR but leaves
  // the PREVIOUS post's data embedded in <script> tags. So we (1) re-fetch the
  // current URL fresh and (2) filter every candidate by the current post id
  // (/p/post/<id>/), guaranteeing we only ever return images for the post you're on.
  async function collectPatreonImages() {
    const out = { postId: null, slug: null, title: null, images: [], source: null, debug: { url: location.href, strategies: [] } };

    const m = location.pathname.match(/\/posts\/(?:.*?-)?(\d+)\b/);
    out.postId = m ? m[1] : null;
    out.slug = (location.pathname.match(/\/posts\/([^/?#]+)/) || [])[1] || null;
    out.title = (document.title || "patreon-post").replace(/\s*\|\s*Patreon.*$/i, "").trim();

    const postTag = out.postId ? "/p/post/" + out.postId + "/" : null;
    const matchesPost = (u) => !postTag || (typeof u === "string" && u.indexOf(postTag) !== -1);

    const images = [];
    const seen = new Set();
    const push = (url, name) => {
      if (!url) return;
      url = url.replace(/\\\//g, "/").replace(/\\u0026/gi, "&").replace(/&amp;/g, "&");
      if (!matchesPost(url)) return;            // hard guard against wrong post
      if (seen.has(url)) return;
      seen.add(url);
      images.push({ url, name: name || null });
    };

    const hashOf = (url) => {
      const m2 = url.match(/\/patreon-media\/p\/(?:post|campaign|user)\/[^/]+\/([a-f0-9]{16,})\b/i) || url.match(/\/([a-f0-9]{24,})\//i);
      return m2 ? m2[1] : url;
    };
    const widthOf = (url) => {
      const m2 = url.match(/\/patreon-media\/[^?]*?\/([A-Za-z0-9_-]{6,})\/\d+\.[a-z]+/i);
      if (m2) { try { const j = JSON.parse(atob(m2[1].replace(/-/g, "+").replace(/_/g, "/"))); if (j && typeof j.w === "number") return j.w; } catch (_) {} }
      return 1;
    };
    const scanDownloadUrls = (text) => {
      const re = /"download_url"\s*:\s*"([^"]+)"/g; let mm, n = 0;
      while ((mm = re.exec(text))) { const b = images.length; push(mm[1]); if (images.length > b) n++; }
      return n;
    };

    // Strategy 1: fetch the current URL fresh (authoritative for THIS post)
    try {
      const res = await fetch(location.href, { credentials: "include", headers: { accept: "text/html" } });
      if (res.ok) { const html = await res.text(); const added = scanDownloadUrls(html); out.debug.strategies.push({ tag: "fresh-html", added, htmlLen: html.length }); }
      else { out.debug.strategies.push({ tag: "fresh-html", httpStatus: res.status }); }
    } catch (e) { out.debug.strategies.push({ tag: "fresh-html", error: String(e && e.message) }); }

    // Strategy 2: download_url fields already in the live page scripts
    if (!images.length) {
      let added = 0;
      for (const s of document.querySelectorAll("script")) { const t = s.textContent || ""; if (t.indexOf("download_url") === -1) continue; added += scanDownloadUrls(t); }
      out.debug.strategies.push({ tag: "live-scripts", added });
    }

    // Strategy 3: parse embedded JSON for media objects
    if (!images.length) {
      let added = 0;
      const scripts = [document.getElementById("__NEXT_DATA__"), ...document.querySelectorAll('script[type="application/json"]')].filter(Boolean);
      for (const s of scripts) {
        let json; try { json = JSON.parse(s.textContent); } catch (_) { continue; }
        const stack = [json];
        while (stack.length) {
          const node = stack.pop();
          if (!node || typeof node !== "object") continue;
          if (Array.isArray(node)) { for (const v of node) stack.push(v); continue; }
          const a = node.type === "media" && node.attributes ? node.attributes : node;
          const url = a.download_url || (a.image_urls && (a.image_urls.original || a.image_urls.default || a.image_urls.url));
          const isImg = a.media_type === "image" || (a.mimetype || "").startsWith("image") || !!a.image_urls;
          if (url && isImg) { const b = images.length; push(url, a.file_name); if (images.length > b) added++; }
          for (const k of Object.keys(node)) if (node[k] && typeof node[k] === "object") stack.push(node[k]);
        }
      }
      out.debug.strategies.push({ tag: "nextdata", added });
    }

    // Strategy 4: visible CDN urls, deduped to one best-res per image
    if (!images.length) {
      const byHash = new Map();
      const consider = (url) => {
        if (!/patreonusercontent\.com/i.test(url)) return;
        if (!matchesPost(url)) return;
        const h = hashOf(url), w = widthOf(url);
        const cur = byHash.get(h);
        if (!cur || w > cur.width) byHash.set(h, { url, width: w });
      };
      document.querySelectorAll("img").forEach((img) => { if (img.srcset) img.srcset.split(",").forEach((c) => consider(c.trim().split(/\s+/)[0])); consider(img.currentSrc || img.src || ""); });
      document.querySelectorAll('a[href*="patreonusercontent.com"]').forEach((a) => consider(a.href));
      let added = 0;
      for (const { url } of byHash.values()) { const b = images.length; push(url); if (images.length > b) added++; }
      out.debug.strategies.push({ tag: "cdn-dedup", added });
    }

    out.images = images;
    out.source = (out.debug.strategies.find((s) => s.added > 0) || {}).tag || null;
    out.debug.total = images.length;
    out.debug.sample = images.slice(0, 3).map((x) => x.url);
    return out;
  }

  // ───────── naming (ported from popup.js) ───────────────────────────────────
  const sanitize = (s) => (s || "").replace(/[\\/:*?"<>|]+/g, "_").replace(/\s+/g, " ").trim().slice(0, 80);
  const extOf = (url) => { try { const base = (new URL(url).pathname.split("/").pop() || "").split("?")[0]; const mm = base.match(/\.(jpe?g|png|gif|webp|avif)$/i); if (mm) return mm[0].toLowerCase(); } catch (_) {} return ".png"; };
  // Each post gets its own folder. The page title is unreliable (for the owner it's
  // just "Edit post"), so prefer the unique-per-post URL slug, then a non-generic
  // title, then the post id.
  function folderFor(result) {
    const slug = (result && result.slug || "").replace(/[^a-z0-9._-]+/gi, "-").replace(/^-+|-+$/g, "").slice(0, 80);
    if (slug && slug.length > 1) return "Patreon/" + slug;
    const t = sanitize(result && result.title || "");
    if (t && !/^edit\b/i.test(t)) return "Patreon/" + t;
    return "Patreon/post-" + ((result && result.postId) || "x");
  }
  // CDN basenames are all "1.png" → keeping them collides into 1(1).png. Use a clean
  // zero-padded sequence; keep a real file_name if Patreon gave one.
  function buildName(img, i) {
    const seq = String(i + 1).padStart(3, "0");
    const name = (img.name || "").trim();
    if (name && !/^\d+\.\w+$/.test(name)) return seq + "_" + sanitize(name);
    return seq + extOf(img.url);
  }

  async function mergeReport(patch) {
    const { lastReport } = await chrome.storage.local.get("lastReport");
    const next = Object.assign({ version: chrome.runtime.getManifest().version }, lastReport || {}, patch);
    await chrome.storage.local.set({ lastReport: next });
    return next;
  }

  // ───────── in-page panel ───────────────────────────────────────────────────
  const isPostPage = () => /\/posts\//.test(location.pathname);
  let panel = null, statusEl = null, goBtn = null, poll = null;

  function line(msg, cls) { const div = document.createElement("div"); if (cls) div.className = "pgd-" + cls; div.textContent = msg; statusEl.appendChild(div); statusEl.scrollTop = statusEl.scrollHeight; }

  function build() {
    if (panel) return;
    const style = document.createElement("style");
    style.id = "pgd-style";
    style.textContent = `
     #pgd{position:fixed;right:20px;bottom:20px;z-index:2147483647;width:300px;background:#1b1b1d;color:#f2f2f2;border:1px solid #2c2c30;border-radius:12px;box-shadow:0 8px 30px rgba(0,0,0,.5);font:13px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;overflow:hidden}
     #pgd .hd{display:flex;align-items:center;gap:8px;padding:10px 12px;background:#232327;cursor:move;user-select:none}
     #pgd .hd b{flex:1;font-size:13px} #pgd .hd span{cursor:pointer;opacity:.7;padding:2px 6px;border-radius:6px} #pgd .hd span:hover{background:#34343a;opacity:1}
     #pgd .bd{padding:12px}
     #pgd button{width:100%;padding:10px;font-size:13.5px;font-weight:700;border:0;border-radius:8px;background:#ff424d;color:#fff;cursor:pointer}
     #pgd button:hover{filter:brightness(1.06)} #pgd button.sec{background:#333;color:#ddd;font-weight:500;margin-top:8px;font-size:12px;padding:8px} #pgd button:disabled{background:#555;cursor:default}
     #pgd #pgd-status{margin-top:11px;font-size:12px;line-height:1.5;max-height:200px;overflow-y:auto;font-family:ui-monospace,monospace}
     #pgd .pgd-ok{color:#4ade80} #pgd .pgd-err{color:#f87171} #pgd .pgd-muted{color:#9a9a9a}
     #pgd.min .bd{display:none}`;
    document.documentElement.appendChild(style);

    panel = document.createElement("div"); panel.id = "pgd";
    panel.innerHTML = `
     <div class="hd"><b>Patreon Gallery</b><span class="m" title="Minimize">–</span><span class="x" title="Close">✕</span></div>
     <div class="bd">
       <button id="pgd-go">⬇ Download all images</button>
       <button id="pgd-copy" class="sec">Copy debug report</button>
       <div id="pgd-status"></div>
     </div>`;
    document.documentElement.appendChild(panel);
    statusEl = panel.querySelector("#pgd-status");
    goBtn = panel.querySelector("#pgd-go");

    panel.querySelector(".hd .x").addEventListener("click", () => { destroy(); });
    panel.querySelector(".hd .m").addEventListener("click", () => panel.classList.toggle("min"));
    goBtn.addEventListener("click", run);
    panel.querySelector("#pgd-copy").addEventListener("click", copyDebug);
    // drag by header
    (() => { const hd = panel.querySelector(".hd"); let sx, sy, sr, sb, drag = false; hd.addEventListener("mousedown", (e) => { if (e.target.tagName === "SPAN") return; drag = true; sx = e.clientX; sy = e.clientY; const r = panel.getBoundingClientRect(); sr = innerWidth - r.right; sb = innerHeight - r.bottom; e.preventDefault(); }); addEventListener("mousemove", (e) => { if (!drag) return; panel.style.right = Math.max(0, sr - (e.clientX - sx)) + "px"; panel.style.bottom = Math.max(0, sb - (e.clientY - sy)) + "px"; }); addEventListener("mouseup", () => { drag = false; }); })();

    // reflect an in-progress run if the panel was rebuilt mid-download
    chrome.storage.local.get("lastReport").then(({ lastReport: r }) => {
      if (r && r.running) { line("Resuming: " + (r.downloaded || 0) + "/" + (r.total || "?") + " downloading…", "muted"); goBtn.disabled = true; startPolling(r.total || r.found || 0); }
    });
  }

  function destroy() {
    if (poll) { clearInterval(poll); poll = null; }
    if (panel) { panel.remove(); panel = null; }
    const st = document.getElementById("pgd-style"); if (st) st.remove();
    statusEl = goBtn = null;
  }

  let progressLine = null;
  function startPolling(total) {
    if (poll) clearInterval(poll);
    poll = setInterval(async () => {
      const { lastReport: r } = await chrome.storage.local.get("lastReport");
      if (!r || !progressLine) return;
      progressLine.textContent = "  …" + (r.downloaded || 0) + "/" + total + " downloaded" + (r.failed ? ", " + r.failed + " failed" : "");
      progressLine.className = r.failed ? "pgd-err" : "pgd-muted";
      if (!r.running) { clearInterval(poll); poll = null; line("Done: " + r.downloaded + " downloaded" + (r.failed ? ", " + r.failed + " failed" : "") + ".", r.failed ? "err" : "ok"); if (goBtn) goBtn.disabled = false; }
    }, 350);
  }

  async function run() {
    if (!goBtn) return;
    goBtn.disabled = true; statusEl.textContent = "";
    if (!isPostPage()) { line("Open a Patreon post (a /posts/… URL) first.", "err"); goBtn.disabled = false; return; }
    line("Scanning the post…", "muted");
    let result;
    try { result = await collectPatreonImages(); }
    catch (e) { line("Could not read the page: " + ((e && e.message) || e), "err"); await mergeReport({ error: "collect:" + ((e && e.message) || e) }); goBtn.disabled = false; return; }

    const images = (result && result.images || []).map((img, i) => ({ url: img.url, name: buildName(img, i) }));
    const folder = folderFor(result);
    await mergeReport({ found: images.length, source: (result && result.source) || null, debug: (result && result.debug) || null, folder, tabUrl: location.href, downloaded: 0, failed: 0, errors: [] });

    if (!images.length) { line("No images found — click Copy debug report and send it to Claude.", "err"); goBtn.disabled = false; return; }
    line("Found " + images.length + " image(s) via " + result.source + ".", "ok");
    line("Saving to Downloads/" + folder + "/", "muted");
    line("Downloading in the background — safe to navigate away.", "muted");
    progressLine = document.createElement("div"); progressLine.className = "pgd-muted"; statusEl.appendChild(progressLine);

    // Hand off to the shared service worker; it keeps going if the panel closes.
    chrome.runtime.sendMessage({ type: "patreonDownload", folder, images });
    startPolling(images.length);
  }

  async function copyDebug() {
    const { lastReport: r } = await chrome.storage.local.get("lastReport");
    const btn = panel.querySelector("#pgd-copy");
    if (!r) { btn.textContent = "Nothing yet — run it first"; setTimeout(() => (btn.textContent = "Copy debug report"), 1800); return; }
    try { await navigator.clipboard.writeText(JSON.stringify(r, null, 2)); btn.textContent = "Copied! Paste it to Claude"; }
    catch (_) { btn.textContent = "Copy failed (clipboard blocked)"; }
    setTimeout(() => (btn.textContent = "Copy debug report"), 1800);
  }

  // ───────── show only on post pages; track SPA navigation ───────────────────
  function sync() { if (isPostPage()) build(); else destroy(); }
  sync();
  let lastPath = location.pathname;
  setInterval(() => { if (location.pathname !== lastPath) { lastPath = location.pathname; sync(); } }, 1200);
  addEventListener("popstate", sync);
})();
