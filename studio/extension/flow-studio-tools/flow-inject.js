// 3DMC Studio Tools — MAIN-world injector for Flow's Slate composer.
//
// Why this file exists: Flow's prompt box is a Slate editor whose MODEL only updates
// through Slate's own editor.insertText. VERIFIED live (2026-07-19) against the real
// composer: execCommand("insertText") AND synthetic/real beforeinput both mutate only
// the DOM — Slate never records them, so the text vanished on the next re-render (blur
// or submit). editor.insertText lives in the PAGE's JS world, which the isolated
// content script (content.js) cannot reach. This script is declared world:"MAIN" in the
// manifest, so it runs in the page context and CAN reach it.
//
// Handshake: content.js (isolated) stashes {text, where, index} as JSON in a shared
// #__fstBridge <div> and dispatches a "fst-insert" event on document (document is the
// same object in both worlds). We read it here, grab the live editor off the editable's
// React fiber, insert via editor.insertText, and call editor.onChange() so React
// re-renders the view. The text is now in Slate's model → it persists exactly like
// something the user typed (survives blur, included on submit).
//
// It also hosts the bake-off's AUTO-FIRE (see flow-bakeoff.js). Flow ignores synthetic
// events on the Create button — a full pointer sequence produces no generate request at
// all. But React keeps the button's real handler in `__reactProps$…onClick`, which lives
// in the PAGE world, so we can call it directly from here. Whether Flow accepts that is
// something only the page can answer, so we also tick a counter on every outgoing
// batchGenerateImages request; the content script reads that counter off a DOM attribute
// to confirm a fire actually landed, and falls back to asking for a real click if not.
(() => {
  if (window.__fstInject) return;
  window.__fstInject = true;

  // ---- generation-request counter (the auto-fire's proof of life) ----
  const TICK_ATTR = "data-fst-gen-ticks";
  let ticks = 0;
  document.documentElement.setAttribute(TICK_ATTR, "0");
  const _fetch = window.fetch;
  window.fetch = function (input, init) {
    try {
      const url = typeof input === "string" ? input : (input && input.url) || "";
      if (url.includes("batchGenerateImages")) document.documentElement.setAttribute(TICK_ATTR, String(++ticks));
    } catch (e) {}
    return _fetch.apply(this, arguments);
  };

  // ---- auto-fire: invoke the Create button's React onClick directly ----
  const vis = (el) => !!(el && el.offsetParent !== null && el.getBoundingClientRect().height > 4);
  function createBtn() {
    const ed = document.querySelector('[data-slate-editor="true"]');
    let n = ed, box = null;
    for (let i = 0; n && i < 14; i++, n = n.parentElement) if (n.querySelectorAll("button").length >= 3) { box = n; break; }
    if (!box) return null;
    // Match the arrow icon. NOT [type=submit]: these buttons carry no type attribute
    // (the IDL default just reports "submit"), and "Clear prompt" sits right beside it.
    return [...box.querySelectorAll("button")].filter(vis).find((b) => /arrow_forward/i.test(b.textContent || "")) || null;
  }
  document.addEventListener("fst-fire", () => {
    try {
      const b = createBtn();
      if (!b || b.disabled) { console.warn("[3DMC Studio Tools] auto-fire: Create button not available"); return; }
      const pk = Object.keys(b).find((k) => k.startsWith("__reactProps$"));
      const onClick = pk && b[pk] && b[pk].onClick;
      if (typeof onClick !== "function") { console.warn("[3DMC Studio Tools] auto-fire: no React onClick on Create"); return; }
      onClick({ preventDefault() {}, stopPropagation() {}, persist() {}, nativeEvent: {}, currentTarget: b, target: b, type: "click", isTrusted: true });
    } catch (e) {
      console.error("[3DMC Studio Tools] auto-fire failed", e);
    }
  });

  const isEditor = (v) =>
    v && typeof v === "object" && Array.isArray(v.children) &&
    typeof v.insertText === "function" && "selection" in v;

  // The Slate editor object hangs off the editable element's React fiber. Walk up the
  // fiber chain, scanning each node's prop/state bags for something shaped like an editor.
  function grabEditor(node) {
    const key = Object.keys(node).find(
      (k) => k.startsWith("__reactFiber$") || k.startsWith("__reactInternalInstance$"));
    if (!key) return null;
    let fiber = node[key], hops = 0;
    while (fiber && hops < 80) {
      for (const bag of [fiber.memoizedProps, fiber.pendingProps, fiber.stateNode, fiber.memoizedState]) {
        if (bag && typeof bag === "object") {
          if (isEditor(bag)) return bag;
          let vals; try { vals = Object.values(bag); } catch (e) { continue; }
          for (const v of vals) { try { if (isEditor(v)) return v; } catch (e) {} }
        }
      }
      fiber = fiber.return; hops++;
    }
    return null;
  }

  // First (start) or last (end) text position in the model.
  function edgePoint(editor, atStart) {
    let cur = editor, path = [];
    while (cur.children && cur.children.length) {
      const i = atStart ? 0 : cur.children.length - 1;
      path.push(i); cur = cur.children[i];
    }
    return { path, offset: atStart ? 0 : (cur.text || "").length };
  }

  document.addEventListener("fst-insert", () => {
    try {
      const bridge = document.getElementById("__fstBridge");
      if (!bridge) return;
      let payload; try { payload = JSON.parse(bridge.textContent || "{}"); } catch (e) { return; }
      const { text, where, index } = payload;
      if (!text) return;
      const editors = document.querySelectorAll('[data-slate-editor="true"]');
      const el = (index != null && editors[index]) ? editors[index] : editors[0];
      if (!el) return;
      const editor = grabEditor(el);
      if (!editor) { console.warn("[3DMC Studio Tools] Slate editor not reachable — did Flow change its editor?"); return; }
      try { el.focus(); } catch (e) {}
      const pt = edgePoint(editor, where === "start");
      editor.selection = { anchor: pt, focus: pt };  // aim the insert at the chosen edge
      editor.insertText(text);                        // enters Slate's MODEL → persists like typing
      editor.onChange();                              // notify React so the view re-renders
    } catch (e) {
      console.error("[3DMC Studio Tools] prompt insert failed", e);
    }
  });
})();
