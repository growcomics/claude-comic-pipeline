// Flow Red-Pen — production-QA verdicts on Flow generations, keyed by media uuid.
// TAGS are REGENERATED from projects/<project>/qa/defect-registry.json — do not hand-edit
// without updating the registry first. Last regen: 2026-06-10 (D1–D9).

const TAGS = [
  ["accept",  "✓",  "Accept as-is"],
  ["gold",    "★",  "Golden — use as style anchor for regens"],
  ["refs",    "🖼️", "D1/D5 — ref stack thin or wrong (identity/continuity drift)"],
  ["prose",   "🔤", "D11 — appearance written in prompt text instead of carried by references"],
  ["vary",    "🎲", "D12 — variants wildly divergent (staging/prompt under-pinned)"],
  ["anatomy", "🖐️", "D13 — extra/phantom limbs or hands"],
  ["face",    "😐", "D2 — expression flat / wrong emotion for the beat"],
  ["angle",   "📐", "D3 — too front-facing / camera not as specced"],
  ["ward",    "👗", "D4 — outfit wrong or inconsistent vs wardrobe state"],
  ["size",    "📏", "D6 — muscle size under tier (no-downsize violation)"],
  ["height",  "🧍", "D7 — height/scale wrong (giant or shrunken vs height chart)"],
  ["scene",   "📷", "D8 — background invented / scene ref proximity mismatch"],
  ["staging", "🧩", "D9 — pose/interaction staging wrong (needed a staging ref)"],
  ["vfx",     "⚡", "D10 — effect too perfect/AI-looking; should read as DAZ store prop + postwork"],
  ["style",   "🎨", "Style drift — not photoreal CGI"],
  ["reject",  "✗",  "Reject outright — regenerate"]
];

let verdicts = {};
chrome.storage.local.get("verdicts").then(v => {
  verdicts = v.verdicts || {};
  renderAll();
});

function save() {
  chrome.storage.local.set({ verdicts });
  updatePill();
}

const uuidOf = img => (img.src.match(/name=([0-9a-f-]{36})/) || [])[1];

function decorate(img) {
  const uuid = uuidOf(img);
  if (!uuid) return;
  const host = img.parentElement;
  if (!host || host.dataset.redpen) return;
  if (img.clientWidth && img.clientWidth < 120) return; // skip tiny attached-ref thumbs
  host.dataset.redpen = uuid;
  if (getComputedStyle(host).position === "static") host.style.position = "relative";

  const bar = document.createElement("div");
  bar.className = "rp-bar";
  for (const [key, icon, tip] of TAGS) {
    const b = document.createElement("button");
    b.className = "rp-btn";
    b.textContent = icon;
    b.title = tip;
    b.dataset.key = key;
    b.addEventListener("click", e => {
      e.stopPropagation(); e.preventDefault();
      toggle(uuid, key, host);
    });
    bar.appendChild(b);
  }
  const note = document.createElement("button");
  note.className = "rp-btn";
  note.textContent = "📝";
  note.title = "Add a free-text note";
  note.addEventListener("click", e => {
    e.stopPropagation(); e.preventDefault();
    const v = verdicts[uuid] || (verdicts[uuid] = { tags: [], note: "" });
    const t = prompt("Red-pen note for this image:", v.note || "");
    if (t !== null) { v.note = t; save(); paint(host); }
  });
  bar.appendChild(note);
  host.appendChild(bar);

  const badge = document.createElement("div");
  badge.className = "rp-badge";
  host.appendChild(badge);
  paint(host);
}

function toggle(uuid, key, host) {
  const v = verdicts[uuid] || (verdicts[uuid] = { tags: [], note: "" });
  if (key === "accept" || key === "reject") {
    // accept/reject are mutually exclusive top-level verdicts
    const had = v.tags.includes(key);
    v.tags = v.tags.filter(t => t !== "accept" && t !== "reject");
    if (!had) v.tags.push(key);
  } else {
    v.tags = v.tags.includes(key) ? v.tags.filter(t => t !== key) : [...v.tags, key];
  }
  if (!v.tags.length && !v.note) delete verdicts[uuid];
  save();
  paint(host);
}

function paint(host) {
  const uuid = host.dataset.redpen;
  const v = verdicts[uuid];
  const badge = host.querySelector(".rp-badge");
  if (!badge) return;
  badge.textContent = v
    ? TAGS.filter(([k]) => v.tags.includes(k)).map(([, i]) => i).join(" ") + (v.note ? " 📝" : "")
    : "";
  badge.style.display = v ? "block" : "none";
  host.querySelectorAll(".rp-btn").forEach(b =>
    b.classList.toggle("rp-on", !!v && v.tags && v.tags.includes(b.dataset.key))
  );
}

function renderAll() {
  document.querySelectorAll("[data-redpen]").forEach(paint);
  updatePill();
}

function scan() {
  document.querySelectorAll('img[src*="getMediaUrlRedirect"]').forEach(decorate);
  if (!document.getElementById("rp-pill")) makePill();
}

function makePill() {
  if (!document.body) return;
  const p = document.createElement("button");
  p.id = "rp-pill";
  p.title = "Click: export verdicts JSON · Double-click: clear all";
  p.addEventListener("click", exportJSON);
  p.addEventListener("dblclick", () => {
    if (confirm("Clear ALL red-pen verdicts?")) { verdicts = {}; save(); renderAll(); }
  });
  document.body.appendChild(p);
  updatePill();
}

function updatePill() {
  const p = document.getElementById("rp-pill");
  if (p) p.textContent = `⤓ red-pen verdicts (${Object.keys(verdicts).length})`;
}

function exportJSON() {
  const payload = {
    tool: "flow-red-pen",
    taxonomy_version: "D1-D9 2026-06-10",
    exported_at: new Date().toISOString(),
    legend: Object.fromEntries(TAGS.map(([k, i, tip]) => [k, tip])),
    verdicts
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `flow-redpen-verdicts-${new Date().toISOString().replace(/[:.]/g, "-")}.json`;
  a.click();
  URL.revokeObjectURL(a.href);
}

setInterval(scan, 1200);
scan();
