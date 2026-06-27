// 3DMC Studio Tools — Flow Bulk Delete module (the only destructive action; kept in
// its own file so the fragile DOM selectors are easy to find + patch).
// Flow has no clean delete API, so we drive Flow's OWN per-tile "Move to trash"
// control — a SOFT delete (items go to Trash, recoverable). Selection is keyed by
// a stable media id so the grid's virtualization can't lose ticks.
// Exposes self.FlowDelete = { start, stop, selectVisible, clear, count, run }.
(() => {
  if (self.FlowDelete) return;
  const selected = new Map();
  const wait = (ms) => new Promise((r) => setTimeout(r, ms));
  const isMediaHost = (s) => { try { return /googleusercontent|usercontent/i.test(new URL(s, location.href).host); } catch (e) { return false; } };
  const keyOf = (img) => { const s = img.currentSrc || img.src || ""; return s.split("?")[0].replace(/=[swh].*$/i, "").replace(/=.*$/, ""); };
  const tileOf = (img) => img.closest('button,[role="button"],[role="gridcell"],li,figure') || img.parentElement || img;
  const mediaImgs = () => [...document.querySelectorAll("img")].filter((i) => isMediaHost(i.currentSrc || i.src));
  const findTrashBtn = (tile) => {
    const c = [...tile.querySelectorAll('button,[role="menuitem"],[role="button"]')];
    return c.find((b) => { const t = ((b.getAttribute("aria-label") || "") + " " + (b.getAttribute("title") || "") + " " + (b.innerText || "")).toLowerCase(); return /move to trash|trash|delete/.test(t); }) || null;
  };
  const hover = (el) => { const r = el.getBoundingClientRect(); ["pointerover", "pointerenter", "mouseover", "mouseenter", "mousemove"].forEach((type) => el.dispatchEvent(new MouseEvent(type, { bubbles: true, cancelable: true, clientX: r.x + r.width / 2, clientY: r.y + r.height / 2 }))); };

  let onChange = null, mo = null, scrollH = null, active = false, style = null;
  const css = ".fst-check{position:absolute;top:6px;left:6px;z-index:30;width:20px;height:20px;cursor:pointer;accent-color:#e24b4a}.fst-sel{outline:3px solid #e24b4a;outline-offset:-3px}";
  const fire = () => { if (onChange) onChange(selected.size); };

  function decorate() {
    for (const img of mediaImgs()) {
      const tile = tileOf(img); if (!tile) continue;
      if (tile.dataset.fstd) { syncTile(tile, img); continue; }
      tile.dataset.fstd = "1";
      if (getComputedStyle(tile).position === "static") tile.style.position = "relative";
      const cb = document.createElement("input"); cb.type = "checkbox"; cb.className = "fst-check";
      cb.addEventListener("click", (e) => e.stopPropagation());
      cb.addEventListener("change", () => { const k = keyOf(img); if (cb.checked) selected.set(k, img.currentSrc || img.src); else selected.delete(k); tile.classList.toggle("fst-sel", cb.checked); fire(); });
      tile.appendChild(cb); syncTile(tile, img);
    }
  }
  function syncTile(tile, img) { const cb = tile.querySelector(":scope > .fst-check"); if (!cb) return; const on = selected.has(keyOf(img)); cb.checked = on; tile.classList.toggle("fst-sel", on); }

  function start(cb) {
    if (active) return; active = true; onChange = cb;
    style = document.createElement("style"); style.textContent = css; document.documentElement.appendChild(style);
    decorate();
    mo = new MutationObserver(() => { clearTimeout(mo._t); mo._t = setTimeout(decorate, 150); });
    mo.observe(document.body, { childList: true, subtree: true });
    scrollH = () => { clearTimeout(self.__fstS); self.__fstS = setTimeout(decorate, 120); };
    addEventListener("scroll", scrollH, true);
    fire();
  }
  function stop() {
    if (!active) return; active = false;
    if (mo) { mo.disconnect(); mo = null; } if (scrollH) { removeEventListener("scroll", scrollH, true); scrollH = null; }
    document.querySelectorAll(".fst-check").forEach((c) => c.remove());
    document.querySelectorAll(".fst-sel").forEach((t) => t.classList.remove("fst-sel"));
    document.querySelectorAll("[data-fstd]").forEach((t) => { delete t.dataset.fstd; });
    selected.clear();
    if (style) { style.remove(); style = null; }
  }
  function selectVisible() { for (const img of mediaImgs()) selected.set(keyOf(img), img.currentSrc || img.src); decorate(); fire(); }
  function clear() { selected.clear(); decorate(); fire(); }
  function count() { return selected.size; }

  async function run(onProgress) {
    const n = selected.size; let done = 0, miss = 0, guard = 0;
    while (selected.size > 0 && guard++ < n * 6 + 50) {
      let hit = null, hitImg = null;
      for (const img of mediaImgs()) { if (selected.has(keyOf(img))) { hit = tileOf(img); hitImg = img; break; } }
      if (!hit) { const before = mediaImgs().length; scrollBy(0, Math.round(innerHeight * 0.85)); await wait(450); if (mediaImgs().length === before) { miss = selected.size; break; } decorate(); continue; }
      const key = keyOf(hitImg);
      hit.scrollIntoView({ block: "center" }); hover(hit); await wait(180);
      const btn = findTrashBtn(hit);
      if (!btn) { selected.delete(key); miss++; if (onProgress) onProgress(done, n, miss); await wait(60); continue; }
      btn.click(); await wait(250);
      const confirmBtn = [...document.querySelectorAll('[role="dialog"] button, .modal button')].find((b) => /move to trash|delete|confirm|remove/i.test(b.innerText || ""));
      if (confirmBtn) { confirmBtn.click(); await wait(250); }
      selected.delete(key); done++; if (onProgress) onProgress(done, n, miss); decorate(); await wait(550);
    }
    return { done, miss };
  }

  self.FlowDelete = { start, stop, selectVisible, clear, count, run };
})();
