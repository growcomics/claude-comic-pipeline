// 3DMC Studio Tools — Flow model bake-off (A/B).
//
// WHAT IT DOES: run the SAME prompt through several image models so you can see, on
// your own work, what Nano Banana Pro actually buys you over Nano Banana 2 / 2 Lite.
// With bake-off ON, after you submit a generation the panel re-arms the composer on
// the next model in your list and shows a badge telling you to hit Create again. Then
// "📊 Compare" lays every multi-model prompt out side by side, one column per model.
//
// WHY IT IS ASSISTED AND NOT FULLY AUTOMATIC — verified live 2026-07-26:
//   • Switching the model programmatically WORKS, and leaves the prompt, the attached
//     refs, the aspect ratio and the xN count untouched. That is the tedious part and
//     we automate all of it.
//   • Clicking Create programmatically DOES NOT WORK. Flow ignores synthetic events on
//     the submit button — a full pointerdown/mousedown/pointerup/mouseup/click sequence
//     produces no batchGenerateImages request at all. Generation is gated behind real
//     user activation. So the Create click stays yours; everything around it is ours.
//     (Driving it anyway would need chrome.debugger and its "being debugged" banner.)
//
// HARD-WON UI FACTS — change these only against a live page:
//   • Bare .click() does nothing to Flow's React controls; the popover needs the whole
//     pointer-event sequence (realClick below).
//   • The composer's buttons carry NO type attribute, so `button[type="submit"]` matches
//     NOTHING — document-wide. `.type` reads "submit" purely as the IDL default, which
//     makes a broken selector look like it worked. Match on the icon text instead.
//   • Two buttons sit at the same spot: "arrow_forwardCreate" and "closeClear prompt".
//     Grab the wrong one and you silently clear the prompt and generate nothing.
//   • Escape CLEARS the composer. Never use it to dismiss the popover — re-click the chip.
//   • The chip reads "Nano Banana 2 Litecrop_squarex4", so model names are prefix-matched
//     longest-first or "Nano Banana 2" swallows "Nano Banana 2 Lite".
(() => {
  if (self.FlowBakeoff) return;

  // Display names as Flow renders them, paired with the enum in the tRPC record
  // (image.generatedImage.modelNameType) so the compare board can label a generation.
  const MODELS = [
    { id: "pro",  label: "Nano Banana Pro",    key: "GEM_PIX_2" },
    { id: "nb2",  label: "Nano Banana 2",      key: "NARWHAL" },
    { id: "lite", label: "Nano Banana 2 Lite", key: "HARBOR_SEAL" },
  ];
  const byKey = {}; MODELS.forEach((m) => (byKey[m.key] = m.label));
  const BY_LEN = MODELS.slice().sort((a, b) => b.label.length - a.label.length);

  const DEFAULTS = { on: false, auto: true, models: ["pro", "nb2", "lite"], maxCredits: 0 };
  let cfg = Object.assign({}, DEFAULTS);
  let queue = [], origin = null, statusCb = () => {};

  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const say = (t) => statusCb(t);
  const norm = (el) => (el ? (el.textContent || "").replace(/[^\w\s.+-]/g, " ").replace(/\s+/g, " ").trim() : "");
  const vis = (el) => !!(el && el.offsetParent !== null && el.getBoundingClientRect().height > 4);

  // Flow's React controls ignore a bare .click(); they listen on pointer/mouse events.
  function realClick(el) {
    if (!el) return false;
    const r = el.getBoundingClientRect();
    const o = { bubbles: true, cancelable: true, composed: true, view: window,
                clientX: r.left + r.width / 2, clientY: r.top + r.height / 2,
                button: 0, buttons: 1, isPrimary: true, pointerId: 1, pointerType: "mouse" };
    const up = Object.assign({}, o, { buttons: 0 });
    el.dispatchEvent(new PointerEvent("pointerover", o));
    el.dispatchEvent(new PointerEvent("pointermove", o));
    el.dispatchEvent(new PointerEvent("pointerdown", o));
    el.dispatchEvent(new MouseEvent("mousedown", o));
    try { el.focus(); } catch (e) {}
    el.dispatchEvent(new PointerEvent("pointerup", up));
    el.dispatchEvent(new MouseEvent("mouseup", up));
    el.dispatchEvent(new MouseEvent("click", up));
    return true;
  }

  // ---- finders (the UI-coupled surface) ----------------------------------------
  const editorEl = () => document.querySelector('[data-slate-editor="true"]');

  // Anchor on the nearest ancestor of the editor that holds the composer's button row.
  // NOT "an ancestor containing a Nano Banana button" — when the popover is open that
  // match walks up to the wrong container.
  function composerEl() {
    let n = editorEl();
    for (let i = 0; n && i < 12; i++, n = n.parentElement) if (n.querySelectorAll("button").length >= 3) return n;
    return null;
  }
  // The composer's own model chip — never the identical-looking one inside the popover.
  function chipEl() {
    const c = composerEl(); if (!c) return null;
    return [...c.querySelectorAll("button")].filter((b) => /Nano Banana|Veo |Imagen/i.test(b.textContent || "") && !b.closest('[role="menu"]')).pop() || null;
  }
  // "arrow_forwardCreate", never "closeClear prompt".
  // Do NOT select on [type="submit"]: these buttons carry no type ATTRIBUTE, so that
  // selector matches nothing document-wide. (`.type` reads "submit" only because that's
  // the IDL default for a <button> — which is exactly what made this look fine at first
  // and silently returned null forever.) Match the arrow icon instead.
  function sendEl() {
    const c = composerEl(); if (!c) return null;
    const btns = [...c.querySelectorAll("button")].filter(vis);
    return btns.find((b) => /arrow_forward/i.test(b.textContent || ""))
        || btns.find((b) => b.type === "submit" && !/clear/i.test(b.textContent || "")) || null;
  }
  // Settings popover vs the model dropdown: both are role=menu with a model button in
  // them; only the dropdown has menuitems.
  function popoverEl() {
    return [...document.querySelectorAll('[role="menu"]')].filter(vis)
      .find((m) => !m.querySelector('[role="menuitem"]') && [...m.querySelectorAll("button")].some((b) => /Nano Banana|Veo |Imagen/i.test(b.textContent || ""))) || null;
  }
  function modelTriggerEl() {
    const p = popoverEl(); if (!p) return null;
    return [...p.querySelectorAll("button")].find((b) => /Nano Banana|Veo |Imagen/i.test(b.textContent || "")) || null;
  }
  function modelMenuEl() {
    const p = popoverEl();
    return [...document.querySelectorAll('[role="menu"]')]
      .filter((m) => vis(m) && m !== p && m.querySelector('[role="menuitem"]'))
      .find((m) => [...m.querySelectorAll('[role="menuitem"]')].some((i) => /Nano Banana|Veo |Imagen/i.test(i.textContent || ""))) || null;
  }
  function creditsPending() {
    const p = popoverEl(); if (!p) return null;
    const m = (p.textContent || "").match(/use\s+([\d,]+)\s+credit/i);
    return m ? parseInt(m[1].replace(/,/g, ""), 10) : null;
  }
  const promptText = () => (editorEl() ? (editorEl().textContent || "").trim() : "");
  const currentModel = () => {
    const c = chipEl(); if (!c) return null;
    const t = norm(c);
    const hit = BY_LEN.find((m) => t.startsWith(m.label)) || BY_LEN.find((m) => t.includes(m.label));
    return hit ? hit.label : null;
  };

  async function waitFor(fn, ms = 4000) {
    const t0 = Date.now();
    for (;;) {
      let v; try { v = fn(); } catch (e) { v = null; }
      if (v) return v;
      if (Date.now() - t0 > ms) return null;
      await sleep(100);
    }
  }

  // ---- model switching ----------------------------------------------------------
  async function closePopover() {
    if (!popoverEl()) return;
    realClick(chipEl());                       // toggle shut — Escape would wipe the prompt
    await waitFor(() => !popoverEl(), 2000);
  }

  async function selectModel(label) {
    if (currentModel() === label) return true;
    if (!popoverEl()) { realClick(chipEl()); if (!(await waitFor(popoverEl, 3000))) return "no-popover"; }
    const trig = modelTriggerEl(); if (!trig) return "no-trigger";
    realClick(trig);
    const menu = await waitFor(modelMenuEl, 3000); if (!menu) return "no-menu";
    // Exact match — "Nano Banana 2" must not swallow "Nano Banana 2 Lite".
    const item = [...menu.querySelectorAll('[role="menuitem"]')].find((i) => norm(i) === label);
    if (!item) return "not-offered";
    realClick(item.querySelector("button") || item);
    return (await waitFor(() => currentModel() === label, 4000)) ? true : "no-switch";
  }

  // ---- the assisted run ---------------------------------------------------------
  const badge = document.createElement("div");
  badge.id = "fst-bakeoff-badge";
  badge.style.cssText = "position:fixed;left:50%;transform:translateX(-50%);bottom:120px;z-index:2147483647;display:none;align-items:center;gap:10px;padding:10px 14px;border-radius:10px;background:#1d9e75;color:#fff;font:600 13px system-ui,sans-serif;box-shadow:0 8px 30px rgba(0,0,0,.5)";
  badge.innerHTML = '<span class="t"></span><button class="s" style="border:none;border-radius:6px;padding:4px 9px;background:rgba(0,0,0,.28);color:#fff;cursor:pointer;font-weight:700">Stop</button>';
  const showBadge = (t) => { badge.querySelector(".t").textContent = t; badge.style.display = "flex"; };
  const hideBadge = () => { badge.style.display = "none"; };
  const mountBadge = () => { if (!badge.isConnected) document.documentElement.appendChild(badge); };
  badge.querySelector(".s").addEventListener("click", () => reset("⏹ Bake-off run stopped."));

  function reset(msg) {
    queue = []; hideBadge();
    if (origin) { const o = origin; origin = null; selectModel(o).then(closePopover); }
    if (msg) say(msg);
  }

  // ---- auto-fire ----------------------------------------------------------------
  // flow-inject.js (MAIN world) calls the Create button's own React onClick and ticks a
  // counter on every outgoing batchGenerateImages request. We compare the counter across
  // the attempt: if it moved, Flow really did accept the fire; if not, no amount of
  // pretending helps and we drop into assisted mode and ask for a real click.
  const genTicks = () => parseInt(document.documentElement.getAttribute("data-fst-gen-ticks") || "0", 10) || 0;

  async function tryAutoFire() {
    if (!document.documentElement.hasAttribute("data-fst-gen-ticks")) return false;  // injector absent
    const before = genTicks();
    document.dispatchEvent(new CustomEvent("fst-fire"));
    const moved = await waitFor(() => genTicks() > before, 6000);
    return !!moved;
  }

  // Arm the composer on the next model and ask for the (necessarily human) Create click.
  async function armNext() {
    if (!queue.length) {
      const done = origin;
      origin = null; hideBadge();
      if (done) { await selectModel(done); await closePopover(); }
      say("✓ Bake-off complete — model restored. Hit 📊 Compare to see them side by side.");
      return;
    }
    const next = queue[0];
    const res = await selectModel(next.label);
    if (res !== true) {
      say("✖ " + next.label + " — " + res + "; skipped.");
      queue.shift();
      return armNext();
    }
    const cost = creditsPending();
    if (cost != null && cost > cfg.maxCredits) {
      say("⏭ " + next.label + " would cost " + cost + " credits (cap " + cfg.maxCredits + ") — skipped.");
      queue.shift();
      return armNext();
    }
    await closePopover();
    const n = next.i, total = next.total;

    // Preferred path: fire it ourselves so one click really does run all the models.
    if (cfg.auto !== false) {
      mountBadge();
      showBadge("🔬 Bake-off " + n + "/" + total + " — generating on " + next.label + "…");
      if (await tryAutoFire()) {
        say("✓ " + next.label + " (" + n + "/" + total + ") fired automatically.");
        queue.shift();
        await sleep(6000);                 // Flow throttles rapid submits
        return armNext();
      }
      // Flow refused the programmatic fire — say so once, then hand the click back.
      say("Flow wouldn't accept an automatic click — falling back to manual for this run.");
    }
    mountBadge();
    showBadge("🔬 Bake-off " + n + "/" + total + " — now on " + next.label + ". Click Create ▶");
    say("Armed on " + next.label + " (" + n + "/" + total + ") — click Create.");
  }

  // Only a REAL click counts: e.isTrusted is exactly the thing Flow itself requires, and
  // it also means our own synthetic clicks can never drive this loop.
  function onCreateClick(e) {
    if (!cfg.on || !e.isTrusted) return;
    const s = sendEl(); if (!s) return;
    const btn = e.target.closest && e.target.closest("button");
    if (btn !== s) return;
    if (!promptText()) return;

    if (queue.length) { queue.shift(); setTimeout(armNext, 1500); return; }   // mid-run
    const from = currentModel();
    origin = from;
    const rest = MODELS.filter((m) => cfg.models.includes(m.id) && m.label !== from);
    if (!rest.length) { origin = null; return; }
    queue = rest.map((m, i) => ({ label: m.label, i: i + 2, total: rest.length + 1 }));
    setTimeout(armNext, 1500);                 // let Flow's own submit land first
  }
  document.addEventListener("click", onCreateClick, true);

  // ---- compare board ------------------------------------------------------------
  // Group the project's generations by prompt, keep those that ran on 2+ models. Works
  // retroactively on any project — the model is recorded per generation, so no local
  // bookkeeping is needed.
  async function buildCompare() {
    const proj = await self.FlowCore.getProject();
    if (!proj) return { error: "Open a Flow project first." };
    const groups = new Map();
    proj.records.forEach((r) => {
      const p = (r.prompt || "").trim(); if (!p) return;
      if (!groups.has(p)) groups.set(p, { prompt: p, byModel: {}, latest: "" });
      const g = groups.get(p);
      const label = byKey[r.model_key] || r.model || r.model_key || "unknown";
      (g.byModel[label] = g.byModel[label] || []).push(...r.output_media_ids.map((id) => self.FlowCore.MEDIA(id)));
      if (String(r.timestamp) > g.latest) g.latest = String(r.timestamp);
    });
    const rows = [...groups.values()].filter((g) => Object.keys(g.byModel).length >= 2)
      .sort((a, b) => b.latest.localeCompare(a.latest));
    return {
      project: proj.name, projectId: proj.id,
      columns: MODELS.map((m) => m.label).filter((l) => rows.some((r) => r.byModel[l])),
      rows, totalPrompts: groups.size,
    };
  }

  self.FlowBakeoff = {
    MODELS,
    get cfg() { return cfg; },
    isRunning: () => queue.length > 0,
    stop: () => reset("⏹ Bake-off run stopped."),
    onStatus: (fn) => { statusCb = fn || (() => {}); },
    setCfg(patch) { cfg = Object.assign({}, cfg, patch); chrome.storage.local.set({ bakeoff: cfg }); if (!cfg.on) reset(); },
    async load() {
      const s = await chrome.storage.local.get(["bakeoff"]);
      cfg = Object.assign({}, DEFAULTS, s.bakeoff || {});
      if (!Array.isArray(cfg.models) || !cfg.models.length) cfg.models = DEFAULTS.models.slice();
      return cfg;
    },
    buildCompare, currentModel,
  };
})();
