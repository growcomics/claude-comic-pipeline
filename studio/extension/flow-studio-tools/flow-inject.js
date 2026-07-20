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
(() => {
  if (window.__fstInject) return;
  window.__fstInject = true;

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
