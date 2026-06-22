// Service worker: fetch each Flow image (cross-origin, with the user's Google
// session) and POST it into the Studio project via the bridge. Reports progress.

chrome.runtime.onConnect.addListener((port) => {
  if (port.name !== "flow-studio") return;
  port.onMessage.addListener(async (msg) => {
    if (msg.type !== "start") return;
    const { items, project, cfg } = msg;
    const url = (cfg && cfg.url) || "https://3dmusclecomics.com/studio/bridge.php";
    const key = (cfg && cfg.key) || "";

    // 1) resolve / create the Studio project
    let pid;
    try {
      const fd = new FormData(); fd.append("do", "ingest_init"); fd.append("key", key); fd.append("project", project);
      const r = await fetch(url, { method: "POST", body: fd });
      const j = await r.json();
      if (!j.ok) { port.postMessage({ type: "error", message: j.error || "init failed" }); return; }
      pid = j.project;
    } catch (e) { port.postMessage({ type: "error", message: "can't reach Studio (URL/key?)" }); return; }

    // 2) push each image
    let ok = 0, fail = 0;
    for (let i = 0; i < items.length; i++) {
      const { up, raw } = items[i];
      let blob = await grab(up); if (!blob && raw && raw !== up) blob = await grab(raw);
      if (!blob) { fail++; report(port, i, items.length, ok, fail); continue; }
      const ext = extOf(blob.type);
      try {
        const fd = new FormData();
        fd.append("do", "ingest"); fd.append("key", key); fd.append("p", pid);
        fd.append("seq", String(i)); fd.append("orig", `flow-${String(i + 1).padStart(3, "0")}.${ext}`);
        fd.append("file", blob, `flow-${String(i + 1).padStart(3, "0")}.${ext}`);
        const r = await fetch(url, { method: "POST", body: fd });
        const j = await r.json();
        if (j.ok) ok++; else fail++;
      } catch (e) { fail++; }
      report(port, i, items.length, ok, fail);
    }
    try { port.postMessage({ type: "done", ok, fail, total: items.length }); } catch (e) {}
  });
});

async function grab(u) {
  try { const r = await fetch(u, { credentials: "include" }); if (!r.ok) return null; const b = await r.blob(); return b.size ? b : null; }
  catch (e) { return null; }
}
function extOf(t) {
  t = (t || "").toLowerCase();
  if (t.includes("png")) return "png";
  if (t.includes("webp")) return "webp";
  if (t.includes("gif")) return "gif";
  return "jpg";
}
function report(port, i, total, ok, fail) {
  try { port.postMessage({ type: "progress", done: i + 1, total, ok, fail }); } catch (e) {}
}
