// Flow Studio Tools — service worker. Two job kinds from the content script:
//   download : save {url,path} jobs (+ optional manifest) via chrome.downloads
//              (it fetches with the logged-in session, sidestepping page CORS).
//   studio   : fetch each image and POST it into a Studio project via the bridge.
chrome.runtime.onConnect.addListener((port) => {
  if (port.name !== "fst") return;
  port.onMessage.addListener(async (msg) => {
    if (msg.type !== "start") return;
    if (msg.kind === "download") return runDownload(port, msg);
    if (msg.kind === "studio") return runStudio(port, msg);
  });
});

function post(port, m) { try { port.postMessage(m); } catch (e) {} }

async function runDownload(port, msg) {
  const { folder, jobs, manifest } = msg;
  let ok = 0, fail = 0;
  const total = jobs.length + (manifest ? 1 : 0);
  if (manifest) {
    const u = "data:application/json;charset=utf-8," + encodeURIComponent(manifest);
    (await downloadOne(u, folder + "/manifest.json")).ok ? ok++ : fail++;
    post(port, { type: "progress", done: ok + fail, total, ok, fail });
  }
  for (let i = 0; i < jobs.length; i++) {
    (await downloadOne(jobs[i].url, jobs[i].path)).ok ? ok++ : fail++;
    post(port, { type: "progress", done: ok + fail, total, ok, fail });
  }
  post(port, { type: "done", ok, fail, total });
}

async function runStudio(port, msg) {
  const { items, project, newSection, cfg } = msg;
  const url = (cfg && cfg.url) || "https://3dmusclecomics.com/studio/bridge.php";
  const key = (cfg && cfg.key) || "";
  let pid;
  try {
    const fd = new FormData(); fd.append("do", "ingest_init"); fd.append("key", key); fd.append("project", project);
    if (newSection) fd.append("new", "1");
    const j = await (await fetch(url, { method: "POST", body: fd })).json();
    if (!j.ok) { post(port, { type: "error", message: j.error || "init failed" }); return; }
    pid = j.project;
  } catch (e) { post(port, { type: "error", message: "can't reach Studio (URL/key?)" }); return; }

  let ok = 0, fail = 0;
  for (let i = 0; i < items.length; i++) {
    const blob = await grab(items[i].url);
    if (!blob) { fail++; post(port, { type: "progress", done: ok + fail, total: items.length, ok, fail }); continue; }
    const ext = extOf(blob.type);
    const name = (items[i].orig || ("flow-" + (i + 1) + ".jpg")).replace(/\.\w+$/, "") + "." + ext;
    try {
      const fd = new FormData();
      fd.append("do", "ingest"); fd.append("key", key); fd.append("p", pid);
      fd.append("seq", String(i)); fd.append("orig", name); fd.append("file", blob, name);
      if (items[i].gen) fd.append("gen", items[i].gen);
      if (items[i].prompt) fd.append("prompt", items[i].prompt);
      const j = await (await fetch(url, { method: "POST", body: fd })).json();
      j.ok ? ok++ : fail++;
    } catch (e) { fail++; }
    post(port, { type: "progress", done: ok + fail, total: items.length, ok, fail });
  }
  post(port, { type: "done", ok, fail, total: items.length });
}

async function grab(u) {
  try { const r = await fetch(u, { credentials: "include" }); if (!r.ok) return null; const b = await r.blob(); return b.size ? b : null; }
  catch (e) { return null; }
}
function extOf(t) { t = (t || "").toLowerCase(); if (t.includes("png")) return "png"; if (t.includes("webp")) return "webp"; if (t.includes("gif")) return "gif"; return "jpg"; }
function downloadOne(url, filename) {
  return new Promise((resolve) => {
    chrome.downloads.download({ url, filename, conflictAction: "uniquify" }, (id) => {
      if (chrome.runtime.lastError || id == null) { resolve({ ok: false }); return; }
      const onChanged = (delta) => {
        if (delta.id !== id || !delta.state) return;
        if (delta.state.current === "complete") { chrome.downloads.onChanged.removeListener(onChanged); resolve({ ok: true }); }
        else if (delta.state.current === "interrupted") { chrome.downloads.onChanged.removeListener(onChanged); resolve({ ok: false }); }
      };
      chrome.downloads.onChanged.addListener(onChanged);
    });
  });
}
