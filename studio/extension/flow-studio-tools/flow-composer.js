// 3DMC Studio Tools — Flow composer adapter for the flow.google.com UI (2.8.2).
//
// Google moved Flow to flow.google.com in early Sept 2026. It is a different app
// (BOQ Angular, `boq-labs-ai-sandbox.AiSandboxAngularFrontend`) with a ProseMirror
// prompt box, and labs.google/fx/tools/flow/* now redirects there for signed-in users.
// This file is the ONE place that knows the new composer's DOM. content.js (prompt
// buttons / Angle card), flow-bakeoff.js and the 🐞 dump all go through it; flow-delete.js
// owns the media-tile side. Everything here was mapped 2026-09-07 from a DOM snapshot of
// the owner's live project page plus the app's own JS bundle (m=XRV0Af — the prompt box,
// settings popover, context menus). Facts that matter, in one place:
//
//   • Prompt box:  flow-prompt-box > flow-base-prompt-box > .base-prompt-box
//                    .prompt-top-row > flow-rich-text-editor > .prosemirror-editor
//                      > div.ProseMirror[contenteditable=true] > p …
//                  Empty state = <p><span class="prosemirror-placeholder">What do you want
//                  to create?</span><img class="ProseMirror-separator"><br></p>.
//   • Insert:      VERIFIED LIVE 2026-09-07 (paste path, start + end, blur-safe, Create
//                  enables). The app registers its own ProseMirror `handlePaste`: image files →
//                  upload; else text/plain → `preventDefault()`, split on "\n", text nodes
//                  joined by hard_break nodes, `replaceSelection` at the STATE selection.
//                  A synthetic ClipboardEvent("paste") with a DataTransfer carrying
//                  text/plain therefore inserts exactly like a user paste, from the
//                  isolated world, no MAIN-world bridge needed. The state selection is
//                  pulled from the DOM selection on `selectionchange`, so we focus, aim
//                  the caret, dispatch a synthetic selectionchange, wait a tick, paste.
//                  Fallback: execCommand("insertText") — ProseMirror's DOM observer
//                  parses that mutation back into its document (this is how typing
//                  works), verified live 2026-09-03 on this composer.
//   • Replace:     (2.8.5) the same paste handler does `replaceSelection`, so selecting a
//                  known sentence in the box (DOM Range over its text nodes, synthetic
//                  selectionchange) and pasting over it swaps exactly that sentence and
//                  leaves every other character — and the staged refs — alone. This is how
//                  🎥 Angle card's 🎲 Deal swaps the previous card out for the next one.
//   • Send:        flow-generate-icon-button > button[type=submit][aria-label="Start
//                  generation"] (icon arrow_forward), `disabled` while the prompt is
//                  empty / a run is loading. It is an Angular (click) listener — no
//                  React handler, no isTrusted gate in the template — so a plain
//                  .click() is expected to work; fire() proves it before believing it.
//   • Proof of a fire: a new <flow-pending-tile> in the grid (appears ~100 ms after the
//                  click — verified live 2026-09-07). Second signal (2.8.4, verified the
//                  same evening): the generation RPC IS in resource timing — the BOQ app
//                  posts ONE XHR per submit to flow.google.com
//                  /_/AiSandboxAngularFrontend/data/batchexecute?rpcids=ogiZ0b (the entry
//                  lands when the RESPONSE ends, ~6 s later, never at the click). Other
//                  rpcids seen there are not generations (as29s = project load, WuwhI =
//                  grid refresh, DTaVef). The old aisandbox-pa.googleapis.com …generat…
//                  pattern stays for the legacy app.
//   • Settings:    button.settings-trigger-button[aria-label="Settings trigger"] whose
//                  .settings-summary reads "🍌 Nano Banana 2 Lite <crop_16_9> x1". It
//                  toggles a cdkConnectedOverlay holding <flow-prompt-box-settings>:
//                  flow-toggles[aria-label="Aspect ratio" | "Output count" | "Mode"]
//                  (mat-button-toggle-group; Mode = mat-button-toggle >
//                  button[role=radio][aria-checked] labelled "Image" / "Video" — in Video
//                  mode the summary reads "Video · 720p · 8s crop_16_9 x1", the picker
//                  lists video models such as "Omni 1.1 Flash" and NO Nano Banana, which
//                  is why mode() exists and the bake-off refuses to start there), the model picker
//                  button[aria-label="Select model family"] (matMenuTriggerFor) whose
//                  mat-menu panel .flow-model-picker-panel lists <flow-menu-item>s
//                  (button[mat-menu-item] .item-text .label), and
//                  <flow-credit-cost-label> "Generating will use N credits". VERIFIED LIVE
//                  2026-09-07: a plain .click() on the picker item switches the model, the
//                  picker menu closes, the popover STAYS open (credits readable), the chip
//                  updates within ~1 s. The popover closes on an outside click (handler ignores clicks inside the
//                  model picker); CDK records the pointerdown target first, so an outside
//                  click is pointerdown+click on <body>.
//   • Never send Escape to the page: the app maps it to deselectAll / blurInput.
(() => {
  if (self.FlowComposer) return;

  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const vis = (el) => !!(el && el.getClientRects().length && el.getBoundingClientRect().height > 2);
  async function waitFor(fn, ms = 3000) {
    const t0 = Date.now();
    for (;;) {
      let v; try { v = fn(); } catch (e) { v = null; }
      if (v) return v;
      if (Date.now() - t0 > ms) return null;
      await sleep(80);
    }
  }
  const norm = (s) => (s || "").replace(/[^\w\s.+-]/g, " ").replace(/\s+/g, " ").trim();
  const PLACEHOLDER = ".prosemirror-placeholder, [data-slate-placeholder]";

  // ---- finders ------------------------------------------------------------------
  const editorEl = () =>
    document.querySelector('flow-rich-text-editor .ProseMirror[contenteditable="true"]') ||
    document.querySelector('flow-base-prompt-box .ProseMirror[contenteditable="true"]') ||
    document.querySelector('flow-rich-text-editor [contenteditable="true"]') || null;
  // "angular" = flow.google.com (this file's job); "slate" = the pre-Sept-2026 labs.google
  // composer (content.js / flow-bakeoff.js keep their legacy paths for it); null = no composer.
  const ui = () => (editorEl() ? "angular" : document.querySelector('[data-slate-editor="true"]') ? "slate" : null);
  const composerEl = () => { const e = editorEl(); return e ? (e.closest("flow-base-prompt-box") || e.closest("flow-prompt-box") || e.parentElement) : null; };
  function promptText() {
    const e = editorEl(); if (!e) return "";
    const c = e.cloneNode(true);
    c.querySelectorAll(PLACEHOLDER).forEach((n) => n.remove());
    c.querySelectorAll("br").forEach((n) => n.replaceWith("\n"));
    return c.textContent.replace(/[​﻿]/g, "").trim();
  }
  const isEmpty = () => !promptText();
  function sendEl() {
    const c = composerEl(); if (!c) return null;
    return c.querySelector("flow-generate-icon-button button") ||
      [...c.querySelectorAll("button")].find((b) => /start generation/i.test(b.getAttribute("aria-label") || "") || /arrow_forward/.test(b.textContent || "")) || null;
  }
  const sendDisabled = () => { const b = sendEl(); return !b || b.disabled || b.getAttribute("aria-disabled") === "true"; };
  const settingsTriggerEl = () => { const c = composerEl(); return c ? (c.querySelector("button.settings-trigger-button") || c.querySelector('button[aria-label="Settings trigger"]')) : null; };
  const settingsPanelEl = () => [...document.querySelectorAll("flow-prompt-box-settings")].find(vis) || null;
  const modelTriggerEl = () => { const p = settingsPanelEl(); return p ? p.querySelector('button[aria-label="Select model family"]') : null; };
  const modelMenuEl = () => [...document.querySelectorAll(".cdk-overlay-container .flow-model-picker-panel, .cdk-overlay-container .mat-mdc-menu-panel")]
    .filter(vis).find((m) => m.querySelector("flow-menu-item, [mat-menu-item]")) || null;
  const pendingCount = () => document.querySelectorAll("flow-pending-tile").length;

  // Text of an element minus Material icon ligatures ("crop_16_9", "arrow_drop_down"…).
  function textSansIcons(el) {
    if (!el) return "";
    const c = el.cloneNode(true);
    c.querySelectorAll("mat-icon, .mat-icon, svg").forEach((n) => n.remove());
    return c.textContent || "";
  }
  // Current model as Flow labels it, e.g. "Nano Banana 2 Lite" — from the open popover's
  // picker button when the popover is up, else from the composer's summary chip. The
  // caller (bake-off) resolves this against its own model table, longest label first.
  function currentModel() {
    const trig = modelTriggerEl();
    if (trig) return norm(textSansIcons(trig.querySelector(".model-select-trigger-content") || trig));
    const t = settingsTriggerEl(); if (!t) return "";
    return norm(textSansIcons(t.querySelector(".settings-summary") || t)).replace(/\s*x\d+\s*$/i, "").trim();
  }
  function creditsPending() {
    const p = settingsPanelEl(); if (!p) return null;
    const lbl = p.querySelector("flow-credit-cost-label") || p;
    const m = (lbl.textContent || "").match(/use\s+([\d,]+)\s+credit/i);
    return m ? parseInt(m[1].replace(/,/g, ""), 10) : null;
  }
  function toggleValue(ariaLabel) {
    const p = settingsPanelEl(); if (!p) return null;
    const g = p.querySelector('flow-toggles[aria-label="' + ariaLabel + '"]'); if (!g) return null;
    const on = g.querySelector(".mat-button-toggle-checked, [aria-pressed=\"true\"], [aria-checked=\"true\"]");
    return on ? norm(textSansIcons(on)) : null;
  }
  // "Image" | "Video" | null — the popover's Mode toggle when it is open, else inferred from the
  // summary chip ("Video · 720p · 8s …" vs "🍌 Nano Banana …"). Video mode offers no Nano
  // Banana model, so the bake-off checks this before it queues anything.
  function mode() {
    const v = toggleValue("Mode");
    if (v) return /video/i.test(v) ? "Video" : "Image";
    const t = settingsTriggerEl(); if (!t) return null;
    return /^\s*video\b/i.test(textSansIcons(t.querySelector(".settings-summary") || t)) ? "Video" : "Image";
  }
  // Snapshot of the composer's settings (popover must be open for aspect/count/credits).
  const readSettings = () => ({ model: currentModel(), mode: mode(), aspect: toggleValue("Aspect ratio"), count: toggleValue("Output count"), credits: creditsPending(), open: !!settingsPanelEl() });

  // ---- clicks -------------------------------------------------------------------
  // CDK's outside-click dispatcher decides "outside" from the last pointerdown target,
  // then the click. Both on <body> = an outside click for every open overlay.
  function outsideClick(target) {
    const o = { bubbles: true, cancelable: true, composed: true, clientX: 2, clientY: 2, button: 0, isPrimary: true, pointerId: 1, pointerType: "mouse" };
    target.dispatchEvent(new PointerEvent("pointerdown", o));
    target.dispatchEvent(new MouseEvent("mousedown", o));
    target.dispatchEvent(new PointerEvent("pointerup", o));
    target.dispatchEvent(new MouseEvent("mouseup", o));
    target.dispatchEvent(new MouseEvent("click", o));
  }
  // mat-menus sit on a full-screen backdrop; clicking it is how they close.
  function closeMenu() {
    const bd = [...document.querySelectorAll(".cdk-overlay-container .cdk-overlay-backdrop")].filter(vis).pop();
    if (bd) bd.click();
  }

  async function openSettings() {
    if (settingsPanelEl()) return true;
    const t = settingsTriggerEl(); if (!t) return false;
    t.click();
    return !!(await waitFor(settingsPanelEl, 3000));
  }
  async function closeSettings() {
    if (!settingsPanelEl()) return true;
    if (modelMenuEl()) { closeMenu(); await waitFor(() => !modelMenuEl(), 1500); }
    outsideClick(document.body);
    if (await waitFor(() => !settingsPanelEl(), 1500)) return true;
    const t = settingsTriggerEl(); if (t) t.click();        // it is a toggle
    return !!(await waitFor(() => !settingsPanelEl(), 1500));
  }
  function modelItems() {
    const m = modelMenuEl(); if (!m) return [];
    // a flow-menu-item WRAPS a button[mat-menu-item] — select one layer or every model lists twice
    const nodes = m.querySelectorAll("flow-menu-item").length ? m.querySelectorAll("flow-menu-item") : m.querySelectorAll("[mat-menu-item]");
    return [...nodes].map((fi) => {
      const b = fi.matches("flow-menu-item") ? (fi.querySelector("button, a") || fi) : fi;
      const lab = fi.querySelector(".label");
      return { el: b, label: norm(textSansIcons(lab || b)), disabled: !!(b.disabled || b.getAttribute("aria-disabled") === "true"), selected: fi.classList.contains("selected") };
    });
  }
  // isCurrent(): the caller's own "are we on `label` now?" test (it owns the model table).
  async function selectModel(label, isCurrent) {
    isCurrent = isCurrent || (() => currentModel() === label);
    if (isCurrent()) return true;
    if (!(await openSettings())) return "no-popover";
    if (isCurrent()) return true;
    const trig = modelTriggerEl(); if (!trig) return "no-trigger";
    trig.click();
    if (!(await waitFor(modelMenuEl, 3000))) return "no-menu";
    const items = modelItems();
    const want = norm(label);
    // Exact label first. Else the SHORTEST label that starts with it — a "New"/"Fast" badge
    // appended to "Nano Banana 2" must not send us to "Nano Banana 2 Lite".
    const item = items.find((i) => i.label === want) || items.filter((i) => i.label.startsWith(want)).sort((a, b) => a.label.length - b.label.length)[0];
    if (!item) { closeMenu(); return "not-offered"; }
    if (item.disabled) { closeMenu(); return "disabled"; }
    item.el.click();
    await waitFor(() => !modelMenuEl(), 1500);
    if (modelMenuEl()) closeMenu();
    return (await waitFor(isCurrent, 4000)) ? true : "no-switch";
  }

  // ---- proof of life for a fire -------------------------------------------------
  let genHits = 0;
  // flow.google.com: the generate RPC = batchexecute with rpcids=ogiZ0b (verified 2026-09-07;
  // an obfuscated id that a future bundle may rename — the pending tile stays the primary proof).
  const isGenUrl = (u) => (/\/_\/AiSandboxAngularFrontend\/data\/batchexecute\?/i.test(u) && /[?&]rpcids=[^&]*ogiZ0b/i.test(u))
    || (/aisandbox-pa\.googleapis\.com\//i.test(u) && /generat/i.test(u) && !/getSharedMedia|getMedia|checkStatus|Status\b/i.test(u));
  try {
    new PerformanceObserver((list) => { for (const e of list.getEntries()) if (isGenUrl(e.name || "")) genHits++; }).observe({ type: "resource", buffered: false });
  } catch (e) {}
  // Click Create and wait for evidence Flow really started a generation. VERIFIED LIVE
  // 2026-09-07 (growcomics, flow.google.com): a plain .click() fires, and a <flow-pending-tile>
  // appears within ~100 ms; the prompt stays in the box afterwards. The RPC does reach resource
  // timing (batchexecute?rpcids=ogiZ0b) but only when its response ends ~6 s later, so the
  // pending tile is the signal that counts and genHits is the slower second witness.
  async function fire(timeout = 8000) {
    const b = sendEl();
    if (!b) return { ok: false, why: "no Create button on screen" };
    if (b.disabled || b.getAttribute("aria-disabled") === "true") return { ok: false, why: "Create is disabled (empty prompt, or still generating)" };
    const h0 = genHits, p0 = pendingCount();
    b.click();
    const moved = await waitFor(() => genHits > h0 || pendingCount() > p0, timeout);
    return { ok: !!moved, why: moved ? "" : "no generation request seen within " + Math.round(timeout / 1000) + "s of the click" };
  }
  // The newest tile's "Reuse prompt" hotbar button re-populates the composer (prompt +
  // refs) from that generation — the way back when Flow clears the box after a submit.
  async function reuseLatestPrompt() {
    const tile = document.querySelector("flow-pending-tile, flow-grid-tile-container");
    const btn = tile && tile.querySelector('button[aria-label="Reuse prompt"]');
    if (!btn) return false;
    btn.click();
    return !!(await waitFor(() => !isEmpty(), 3000));
  }

  // ---- insert -------------------------------------------------------------------
  function aimCaret(el, atStart) {
    const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, {
      acceptNode: (n) => (n.parentElement && n.parentElement.closest(PLACEHOLDER)) ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT,
    });
    let first = null, last = null, t;
    while ((t = walker.nextNode())) { if (!first) first = t; last = t; }
    const target = atStart ? first : last;
    const sel = getSelection(), range = document.createRange();
    if (target) range.setStart(target, atStart ? 0 : target.length);
    else range.setStart(el.querySelector("p") || el, 0);
    range.collapse(true);
    sel.removeAllRanges(); sel.addRange(range);
  }
  function synthPaste(el, text) {
    try {
      const dt = new DataTransfer(); dt.setData("text/plain", text);
      el.dispatchEvent(new ClipboardEvent("paste", { bubbles: true, cancelable: true, clipboardData: dt }));
      return true;
    } catch (e) { return false; }
  }
  // Insert `text` at the start or end of the prompt. Never clears anything, never touches
  // the staged refs, never submits. Resolves {ok, method, why}.
  async function insert(text, where) {
    const el = editorEl();
    if (!el) return { ok: false, why: "no composer on screen" };
    if (el.getAttribute("contenteditable") !== "true") return { ok: false, why: "the composer is read-only right now" };
    const atStart = where === "start";
    const before = promptText().length;
    const grew = () => promptText().length > before;
    el.focus();
    await sleep(40);                                   // let ProseMirror's focus handler settle first
    aimCaret(el, atStart);
    document.dispatchEvent(new Event("selectionchange")); // ProseMirror pulls the DOM selection into its state on this
    await sleep(60);
    if (synthPaste(el, text) && (await waitFor(grew, 800))) return { ok: true, method: "paste" };
    aimCaret(el, atStart);
    document.execCommand("insertText", false, text);
    if (await waitFor(grew, 800)) return { ok: true, method: "insertText" };
    return { ok: false, why: "the composer ignored both paste and insertText — hit 🐞 Dump composer and send the file" };
  }

  // ---- replace (2.8.5) ----------------------------------------------------------
  // The editor's text nodes (placeholder excluded) with running offsets, so a substring
  // position in the joined text maps back to (node, offset) pairs for a DOM Range.
  function textRuns(el) {
    const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, {
      acceptNode: (n) => (n.parentElement && n.parentElement.closest(PLACEHOLDER)) ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT,
    });
    const runs = []; let pos = 0, t;
    while ((t = walker.nextNode())) { runs.push({ node: t, start: pos, len: t.data.length }); pos += t.data.length; }
    return runs;
  }
  // ProseMirror renders some spaces as nbsp — a 1:1 swap, so offsets computed on the
  // normalised text still address the real nodes.
  const plain = (s) => (s || "").replace(/\u00a0/g, " ");
  const count = (hay, needle) => { let n = 0, i = 0; if (!needle) return 0; while ((i = hay.indexOf(needle, i)) >= 0) { n++; i += needle.length; } return n; };
  // DOM-select the first occurrence of `needle` inside the editor. False when it is not there.
  function selectText(el, needle) {
    const runs = textRuns(el);
    if (!runs.length) return false;
    const hay = plain(runs.map((r) => r.node.data).join(""));
    const i = hay.indexOf(plain(needle));
    if (i < 0) return false;
    const j = i + needle.length;
    const start = runs.find((r) => i >= r.start && i < r.start + r.len);
    const end = runs.find((r) => j > r.start && j <= r.start + r.len) || runs[runs.length - 1];
    if (!start) return false;
    const sel = getSelection(), range = document.createRange();
    range.setStart(start.node, i - start.start);
    range.setEnd(end.node, Math.min(j - end.start, end.len));
    sel.removeAllRanges(); sel.addRange(range);
    return true;
  }
  // Swap `oldText` for `newText` in place: select the old sentence, paste the new one over it
  // (handlePaste → replaceSelection), verify. Nothing else in the box changes. Resolves
  // {ok, method, why}; why === "not-found" when the old sentence is no longer in the box
  // (edited away, or Flow cleared it) — the caller appends instead.
  async function replace(oldText, newText) {
    const el = editorEl();
    if (!el) return { ok: false, why: "no composer on screen" };
    if (el.getAttribute("contenteditable") !== "true") return { ok: false, why: "the composer is read-only right now" };
    if (!oldText) return { ok: false, why: "not-found" };
    const oldN = count(plain(promptText()), plain(oldText));
    if (!oldN) return { ok: false, why: "not-found" };
    if (plain(oldText) === plain(newText)) return { ok: true, method: "same" };
    const swapped = () => { const now = plain(promptText()); return count(now, plain(oldText)) < oldN && now.includes(plain(newText)); };
    el.focus();
    await sleep(40);
    if (!selectText(el, oldText)) return { ok: false, why: "not-found" };
    document.dispatchEvent(new Event("selectionchange"));   // ProseMirror adopts the DOM range as its state selection
    await sleep(60);
    if (synthPaste(el, newText) && (await waitFor(swapped, 800))) return { ok: true, method: "paste" };
    if (!selectText(el, oldText)) return { ok: false, why: "not-found" };
    document.execCommand("insertText", false, newText);   // typing over a selection — the DOM-observer path
    if (await waitFor(swapped, 800)) return { ok: true, method: "insertText" };
    return { ok: false, why: "the composer ignored both paste and insertText over the selection — hit 🐞 Dump composer and send the file" };
  }
  // True once Create is enabled (Angular needs a tick after an insert; a run still submitting
  // keeps it disabled a little longer).
  const ready = async (ms = 8000) => !!(await waitFor(() => !sendDisabled(), ms));

  // ---- 🐞 dump: ground truth for the next time Google moves the furniture -------
  function dump() {
    const strip = (el, cap) => { if (!el) return "(none)"; let h = el.outerHTML.replace(/<svg[\s\S]*?<\/svg>/g, "<svg/>"); return h.length > cap ? h.slice(0, cap) + "\n<!-- …truncated -->" : h; };
    const probe = {
      when: new Date().toISOString(), url: location.href, ui: ui(), editor: !!editorEl(), promptText: promptText().slice(0, 300),
      send: !!sendEl(), sendDisabled: sendDisabled(), settingsTrigger: !!settingsTriggerEl(), settings: readSettings(),
      modelMenuOpen: !!modelMenuEl(), modelItems: modelItems().map((i) => i.label + (i.disabled ? " (disabled)" : "")),
      tiles: document.querySelectorAll("flow-grid-tile-container").length, mediaIds: document.querySelectorAll("flow-grid-tile-container [data-media-id]").length,
      pending: pendingCount(), genHits, virtualScroller: !!document.querySelector("cdk-virtual-scroll-viewport"),
      customElements: [...new Set([...document.querySelectorAll("*")].map((e) => e.localName).filter((n) => n.startsWith("flow-")))].sort(),
    };
    return "<!-- 3DMC Studio Tools composer dump -->\n<script type=\"application/json\" id=\"fst-probe\">\n" + JSON.stringify(probe, null, 2) + "\n</script>\n" +
      "<!-- ===== COMPOSER ===== -->\n" + strip(document.querySelector("flow-prompt-box") || composerEl(), 400000) +
      "\n<!-- ===== OVERLAY (popovers / menus open right now) ===== -->\n" + strip(document.querySelector(".cdk-overlay-container"), 400000) +
      "\n<!-- ===== FIRST TILE ===== -->\n" + strip(document.querySelector("flow-grid-tile-container"), 100000) +
      "\n<!-- ===== SIDENAV ===== -->\n" + strip(document.querySelector("flow-project-nav-list"), 60000);
  }

  self.FlowComposer = {
    ui, editorEl, composerEl, promptText, isEmpty, sendEl, sendDisabled,
    settingsTriggerEl, settingsPanelEl, openSettings, closeSettings, currentModel, mode, creditsPending, readSettings, modelItems, selectModel,
    fire, reuseLatestPrompt, pendingCount, get genHits() { return genHits; },
    insert, replace, ready, dump, norm,
  };
})();
