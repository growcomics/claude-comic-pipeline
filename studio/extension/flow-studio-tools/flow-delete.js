// 3DMC Studio Tools — Flow Bulk Delete module (the only destructive action; kept in
// its own file so the fragile DOM selectors are easy to find + patch).
// Flow has no clean delete API, so we drive Flow's OWN per-tile "Move to trash"
// control — a SOFT delete (items go to Trash, recoverable). Selection is keyed by
// a stable media id so the grid's virtualization can't lose ticks.
// Exposes self.FlowDelete = { start, stop, selectVisible, clear, count, run }.
//
// flow.google.com (the Angular UI, 2.8.2 — mapped 2026-09-07 from a live DOM snapshot):
//   • Grid tile: <flow-grid-tile-container aria-label="<Flow's auto-generated title>"> …
//                (NOT the prompt: a "…a red apple on a white table…" prompt produced
//                "Red apple on table", and an x4 run gives four tiles the same label) …
//                <flow-image-tile> <img class="image" data-media-id="<uuid>"> — the
//                media id is right on the element, so that IS the selection key.
//   • Its hotbar (always in the DOM, only CSS-hidden until hover): buttons
//                [aria-label="Favorite"] / ["Reuse prompt"] / ["More options"]. The last
//                is a mat-menu trigger; the menu renders into .cdk-overlay-container as
//                .mat-mdc-menu-panel > flow-menu-item > button[mat-menu-item] .label, with
//                {Favorite, Reuse prompt, Animate, Add to prompt, Download, Copy, Rename,
//                Share, Set project cover, Flag output, Move to trash}. The Trash view
//                (URL …/project/<id>/trash) has NO hotbar on its tiles — its menu is the
//                right-click context menu {Restore, Delete permanently} — so we match
//                "Move to trash" only and refuse to run while the sidenav/URL says Trash
//                (verified live 2026-09-07: run() returns the Trash error at once).
//   • Trashing shows a toast "N item(s) moved to trash" with an Undo button — no confirm
//                dialog. VERIFIED LIVE 2026-09-07: the toast is immediate, but the tile only
//                leaves the grid on the next data refresh (~10 s later), so the Undo toast /
//                the tile vanishing — whichever comes first — is the success signal.
//   • The grid is a <cdk-virtual-scroll-viewport>: off-screen tiles are not in the DOM,
//                and the scroll container is that element, not the window.
// The pre-Sept-2026 labs.google grid (img src on googleusercontent, hover → trash
// button inside the tile) is kept as the fallback path.
(() => {
  if (self.FlowDelete) return;
  const selected = new Map();
  const wait = (ms) => new Promise((r) => setTimeout(r, ms));
  const vis = (el) => !!(el && el.getClientRects().length);
  async function waitFor(fn, ms) { const t0 = Date.now(); for (;;) { let v; try { v = fn(); } catch (e) { v = null; } if (v) return v; if (Date.now() - t0 > ms) return null; await wait(80); } }

  // ---- finders (both UIs) ----
  const angular = () => !!document.querySelector("flow-grid-tile-container");
  const isMediaHost = (s) => { try { return /googleusercontent|usercontent/i.test(new URL(s, location.href).host); } catch (e) { return false; } };
  const legacyKey = (img) => { const s = img.currentSrc || img.src || ""; return s.split("?")[0].replace(/=[swh].*$/i, "").replace(/=.*$/, ""); };
  const keyOf = (el) => (el.dataset && el.dataset.mediaId) ? el.dataset.mediaId : legacyKey(el);
  const tileOf = (el) => el.closest("flow-grid-tile-container") || el.closest('button,[role="button"],[role="gridcell"],li,figure') || el.parentElement || el;
  const mediaImgs = () => angular()
    ? [...document.querySelectorAll("flow-grid-tile-container [data-media-id]")]
    : [...document.querySelectorAll("img")].filter((i) => isMediaHost(i.currentSrc || i.src));
  const findByKey = (key) => mediaImgs().find((el) => keyOf(el) === key) || null;
  const scroller = () => document.querySelector("cdk-virtual-scroll-viewport") || document.scrollingElement || document.documentElement;
  const inTrashView = () => {
    const t = document.querySelector("flow-project-nav-list .mdc-list-item--activated .mat-mdc-list-item-title");
    return !!(t && /trash/i.test(t.textContent || "")) || /\/trash(\/|$)/i.test(location.pathname);
  };
  const hover = (el) => { const r = el.getBoundingClientRect(); ["pointerover", "pointerenter", "mouseover", "mouseenter", "mousemove"].forEach((type) => el.dispatchEvent(new MouseEvent(type, { bubbles: true, cancelable: true, clientX: r.x + r.width / 2, clientY: r.y + r.height / 2 }))); };

  // legacy: a trash control inside the tile itself
  const findTrashBtn = (tile) => {
    const c = [...tile.querySelectorAll('button,[role="menuitem"],[role="button"]')];
    return c.find((b) => { const t = ((b.getAttribute("aria-label") || "") + " " + (b.getAttribute("title") || "") + " " + (b.innerText || "")).toLowerCase(); return /move to trash|trash|delete/.test(t); }) || null;
  };
  // angular: the open mat-menu's item whose label matches
  function menuItem(re) {
    const panels = [...document.querySelectorAll(".cdk-overlay-container .mat-mdc-menu-panel, .cdk-overlay-container [role=\"menu\"]")].filter(vis);
    for (const m of panels) {
      for (const fi of m.querySelectorAll("flow-menu-item, [mat-menu-item], [role=\"menuitem\"]")) {
        const el = fi.matches("flow-menu-item") ? (fi.querySelector("button, a") || fi) : fi;
        const text = ((fi.querySelector(".label") || fi).textContent || "").trim();
        if (re.test(text)) return el;
      }
    }
    return null;
  }
  const closeMenus = () => { const bd = [...document.querySelectorAll(".cdk-overlay-container .cdk-overlay-backdrop")].filter(vis).pop(); if (bd) bd.click(); };

  // Trash one tile. Returns true (gone / accepted), or a short reason string.
  async function trashTile(tile, key) {
    if (angular()) {
      const more = tile.querySelector('button[aria-label="More options"]') || tile.querySelector("button.mat-mdc-menu-trigger");
      if (!more) return "no menu button";
      hover(tile); more.click();
      const item = await waitFor(() => menuItem(/^\s*move to trash\s*$/i), 2500);
      if (!item) { closeMenus(); return "no 'Move to trash' item"; }
      // Success = Flow's "N item(s) moved to trash · Undo" toast (its count climbs while a
      // previous toast is still up, so compare the text, not just its presence) or the tile
      // leaving the grid — the latter lags the toast by ~10 s, so don't wait for it alone.
      const toastKey = () => { const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT); let n; while ((n = w.nextNode())) { if (/moved to trash/i.test(n.nodeValue || "")) return n.nodeValue.trim(); } return ""; };
      const undoUp = () => [...document.querySelectorAll("button")].some((b) => /^\s*undo\s*$/i.test(b.textContent || ""));
      const toast0 = toastKey(), undo0 = undoUp();
      item.click();
      const trashed = () => !findByKey(key) || toastKey() !== toast0 || (!undo0 && undoUp());
      const confirmBtn = await waitFor(() => [...document.querySelectorAll('mat-dialog-container button, [role="dialog"] button')].find((b) => /move to trash|confirm/i.test(b.textContent || "")) || (trashed() ? { none: true } : null), 2500);
      if (confirmBtn && !confirmBtn.none) { confirmBtn.click(); await wait(250); }
      if (await waitFor(trashed, 6000)) return true;
      return "no 'moved to trash' toast and the tile is still on screen";
    }
    hover(tile); await wait(180);
    const btn = findTrashBtn(tile);
    if (!btn) return "no trash control";
    btn.click(); await wait(250);
    const confirmBtn = [...document.querySelectorAll('[role="dialog"] button, .modal button')].find((b) => /move to trash|delete|confirm|remove/i.test(b.innerText || ""));
    if (confirmBtn) { confirmBtn.click(); await wait(250); }
    return true;
  }

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
      cb.addEventListener("pointerdown", (e) => e.stopPropagation());   // the tile's own click/select handlers must not see it
      // The virtual grid RECYCLES tile elements, so read the media key at click time, never at decorate time.
      cb.addEventListener("change", () => { const cur = tile.querySelector("[data-media-id]") || img; const k = keyOf(cur); if (cb.checked) selected.set(k, cur.currentSrc || cur.src || k); else selected.delete(k); tile.classList.toggle("fst-sel", cb.checked); fire(); });
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
  function selectVisible() { for (const img of mediaImgs()) selected.set(keyOf(img), img.currentSrc || img.src || keyOf(img)); decorate(); fire(); }
  function clear() { selected.clear(); decorate(); fire(); }
  function count() { return selected.size; }

  async function run(onProgress) {
    const n = selected.size; let done = 0, miss = 0, guard = 0;
    if (inTrashView()) return { done: 0, miss: n, error: "You're in the Trash view — switch to All media first (here the same menu slot restores or deletes permanently)." };
    const reasons = {};
    while (selected.size > 0 && guard++ < n * 6 + 50) {
      let hit = null, hitEl = null;
      for (const el of mediaImgs()) { if (selected.has(keyOf(el))) { hit = tileOf(el); hitEl = el; break; } }
      if (!hit) {
        // ticked tiles may be virtualized away — page the grid until something ticked shows up
        const sc = scroller(), before = mediaImgs().map(keyOf).join("|"), top0 = sc.scrollTop;
        sc.scrollBy(0, Math.round((sc.clientHeight || innerHeight) * 0.85)); await wait(500); decorate();
        if (mediaImgs().map(keyOf).join("|") === before && sc.scrollTop === top0) { miss += selected.size; break; }
        continue;
      }
      const key = keyOf(hitEl);
      hit.scrollIntoView({ block: "center" }); await wait(120);
      const res = await trashTile(hit, key);
      selected.delete(key);
      if (res === true) done++; else { miss++; reasons[res] = (reasons[res] || 0) + 1; }
      if (onProgress) onProgress(done, n, miss);
      decorate(); await wait(res === true ? 550 : 200);
    }
    const why = Object.entries(reasons).sort((a, b) => b[1] - a[1]).map(([k, v]) => k + " ×" + v).join(", ");
    return { done, miss, error: why || undefined };
  }

  self.FlowDelete = { start, stop, selectVisible, clear, count, run };
})();
