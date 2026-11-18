// 3DMC Studio Tools — 🌶 Spice, service-worker half. Sends one Flow image + a prompt to a Siray image-edit model,
// polls the async task, records every job in chrome.storage.local (fst:spice:jobs) and saves the results to
// Downloads/Flow Spice/. The API key lives only in chrome.storage.local (fst:spice:cfg) and is only ever sent
// to api.siray.ai. The content script never sees it. (Ported from Flow Organizer 0.7.0.)
//
// Network access to api.siray.ai is an OPTIONAL host permission, granted from the Spice page when the key is
// saved, so an install that never uses Spice asks for nothing new. (downloads is a regular permission here.)
importScripts("spice-models.js");
(() => {
  const SP = self.FOSpice;
  const ORIGIN = SP.API + "/*";
  const hasDownloads = () => !!chrome.downloads;
  const PENDING = new Set(["NOT_START", "SUBMITTED", "QUEUED", "IN_PROGRESS"]);
  const MAX_JOBS = 200, POLL_MS = 4000, TIMEOUT_MS = 20 * 60000;

  const get = (k) => new Promise((r) => chrome.storage.local.get(k, (o) => r(o ? o[k] : undefined)));
  const set = (k, v) => new Promise((r) => chrome.storage.local.set({ [k]: v }, () => r()));
  const cfg = async () => Object.assign({}, SP.DEFAULTS, (await get(SP.CFG_KEY)) || {});
  const hasPerm = (p) => new Promise((r) => { try { chrome.permissions.contains(p, (ok) => r(!!ok)); } catch (e) { r(false); } });

  // Jobs are read-modify-written by both this worker and the Spice page (delete). Writes here are serialized.
  let q = Promise.resolve();
  const editJobs = (fn) => (q = q.then(async () => { const jobs = (await get(SP.JOBS_KEY)) || []; const out = fn(jobs) || jobs; await set(SP.JOBS_KEY, out.slice(0, MAX_JOBS)); return out; }).catch((e) => { console.warn("[3DMC Studio Tools] spice jobs", e); }));
  const patchJob = (id, patch) => editJobs((jobs) => { const j = jobs.find((x) => x.id === id); if (j) Object.assign(j, patch); return jobs; });

  async function api(path, opts, key) {
    const r = await fetch(SP.API + path, Object.assign({}, opts, { headers: Object.assign({ Authorization: "Bearer " + key, "Content-Type": "application/json" }, (opts && opts.headers) || {}) }));
    let body = null; try { body = await r.json(); } catch (e) {}
    return { status: r.status, ok: r.ok, body };
  }
  const errText = (res) => { const b = res.body || {}; return (b.message || b.fail_code || (b.error && (b.error.message || b.error)) || "HTTP " + res.status) + ""; };

  // The image each job was sent with, kept so ↻ Try next model can resend it. A Siray result URL is stored on the job
  // itself; a Flow image arrives as a data URL (Flow's signed URLs expire), which is too big for storage.local's
  // 10 MB, so it goes to this worker's IndexedDB, newest KEEP_INPUTS only.
  const KEEP_INPUTS = 60;
  const idb = () => new Promise((res, rej) => { const r = indexedDB.open("fst-spice", 1); r.onupgradeneeded = () => r.result.createObjectStore("inputs"); r.onsuccess = () => res(r.result); r.onerror = () => rej(r.error); });
  async function putInput(id, dataUrl) {
    try {
      const db = await idb();
      await new Promise((res) => { const tx = db.transaction("inputs", "readwrite"); const st = tx.objectStore("inputs");
        st.put({ at: Date.now(), dataUrl }, id);
        const all = st.getAllKeys(); all.onsuccess = () => { const keys = all.result; if (keys.length > KEEP_INPUTS) { const ats = st.getAll(); ats.onsuccess = () => { ats.result.map((v, i) => [v.at, keys[i]]).sort((a, b) => a[0] - b[0]).slice(0, keys.length - KEEP_INPUTS).forEach(([, k]) => st.delete(k)); }; } };
        tx.oncomplete = res; tx.onerror = res; });
    } catch (e) { console.warn("[3DMC Studio Tools] spice input store", e); }
  }
  async function getInput(id) {
    try { const db = await idb(); return await new Promise((res) => { const r = db.transaction("inputs").objectStore("inputs").get(id); r.onsuccess = () => res(r.result && r.result.dataUrl || null); r.onerror = () => res(null); }); }
    catch (e) { return null; }
  }

  // ↻ Try next model: same input, prompt, size and shape, on the next model in FOSpice.NEXT that this chain hasn't tried.
  async function next(jobId) {
    const job = ((await get(SP.JOBS_KEY)) || []).find((j) => j.id === jobId);
    if (!job) return { ok: false, reason: "that job is no longer in the list" };
    const tried = (job.tried || []).concat(job.model);
    const nm = SP.nextModel(tried);
    if (!nm) return { ok: false, reason: "every model in the fallback order has been tried on this image" };
    const oldChain = job.src && /^https?:/i.test(job.src.thumb || "") ? job.src.thumb : "";   // pre-2.11 "Spice again" jobs: the thumb IS the input URL
    const image = job.input || (await getInput(job.inputKey || job.id)) || oldChain;
    if (!image) return { ok: false, reason: "this job's input image wasn't kept (jobs from before 2.11.0, or more than " + KEEP_INPUTS + " jobs ago). Spice the image again from Flow" };
    return run({ image, thumb: (job.src && job.src.thumb) || "", prompt: job.prompt, model: nm, size: job.tier || (String(job.size).startsWith("2") ? "2k" : "1k"), n: job.n || 1,
      aspect: job.aspect, ar: job.ar || 0, tried, inputKey: job.input ? "" : (job.inputKey || job.id),
      src: Object.assign({}, job.src || {}, { retryOf: job.id, title: "↻ " + SP.modelById(nm).label.split(" · ")[0] + ": " + String(job.prompt || "").slice(0, 110) }) });
  }

  async function run(msg) {
    const c = await cfg();
    if (!c.key) return { ok: false, needKey: true, reason: "no Siray API key yet" };
    if (!(await hasPerm({ origins: [ORIGIN] }))) return { ok: false, needKey: true, reason: "3DMC Studio Tools isn't allowed to reach api.siray.ai yet. Open 🌶 Settings & results and press Save & allow" };
    const m = SP.modelById(msg.model);
    const tier = m.sizes.includes(msg.size) ? msg.size : m.sizes[m.sizes.length - 1];
    const aspect = SP.ASPECTS.includes(msg.aspect) ? msg.aspect : "1:1";
    const body = { model: m.id, prompt: String(msg.prompt || "").slice(0, 4000), images: [msg.image].concat((msg.refs || []).slice(0, (m.maxRefs || 3) - 1)) };
    if (m.kind === "wh") { const [x, y] = aspect.split(":").map(Number); body.size = SP.nearestWH(tier, msg.ar > 0 ? msg.ar : x / y); body.output_format = "png"; }
    else { body.size = tier; body.aspect_ratio = aspect; }
    if (m.n) body.n = Math.max(1, Math.min(6, msg.n | 0 || 1));
    if (!body.prompt.trim()) return { ok: false, reason: "the prompt is empty" };
    let res;
    try { res = await api("/v1/images/generations/async", { method: "POST", body: JSON.stringify(body) }, c.key); }
    catch (e) { return { ok: false, reason: "couldn't reach Siray: " + (e && e.message || e) }; }
    const taskId = res.body && res.body.data && res.body.data.task_id;
    if (!res.ok || !taskId) return { ok: false, reason: "Siray said: " + errText(res), needKey: res.status === 401 || res.status === 403 };
    const job = { id: "sp_" + Date.now().toString(36) + Math.random().toString(36).slice(2, 6), taskId, model: m.id, prompt: body.prompt, size: body.size, tier, aspect: body.aspect_ratio || aspect, ar: msg.ar > 0 ? msg.ar : 0, n: body.n || 1,
      tried: Array.isArray(msg.tried) ? msg.tried : [],
      src: Object.assign({}, msg.src || {}, { thumb: typeof msg.thumb === "string" ? msg.thumb : "" }), status: "SUBMITTED", progress: "", outputs: [], files: [], error: "", at: Date.now(), doneAt: 0 };
    const img = String(msg.image || "");
    if (/^https?:/i.test(img)) job.input = img;                                  // a Siray result: its URL is enough
    else if (msg.inputKey) job.inputKey = msg.inputKey;                          // a retry: reuse the stored copy
    else if (img.startsWith("data:")) { job.inputKey = job.id; await putInput(job.id, img); }
    await editJobs((jobs) => { jobs.unshift(job); return jobs; });
    c.lastPrompt = body.prompt; c.model = m.id; c.size = tier; if (body.n) c.n = body.n;
    await set(SP.CFG_KEY, c);
    poll(job.id, taskId);
    return { ok: true, jobId: job.id };
  }

  const polling = new Set();
  async function poll(id, taskId) {
    if (polling.has(id)) return;
    polling.add(id);
    try {
      const c = await cfg();
      const started = ((await get(SP.JOBS_KEY)) || []).find((j) => j.id === id);
      const t0 = started ? started.at : Date.now();
      for (;;) {
        await new Promise((r) => setTimeout(r, POLL_MS));
        if (Date.now() - t0 > TIMEOUT_MS) { await patchJob(id, { status: "FAILURE", error: "gave up after 20 min (Siray task " + taskId + ")", doneAt: Date.now() }); return; }
        let res;
        try { res = await api("/v1/images/generations/async/" + encodeURIComponent(taskId), { method: "GET" }, c.key); }
        catch (e) { await patchJob(id, { progress: "network hiccup, retrying…" }); continue; }
        const d = res.body && res.body.data;
        if (!res.ok || !d) {
          if (res.status === 401 || res.status === 403 || res.status === 404) { await patchJob(id, { status: "FAILURE", error: "Siray said: " + errText(res), doneAt: Date.now() }); return; }
          continue;
        }
        if (d.status === "SUCCESS") {
          const outputs = (d.outputs || []).filter((u) => typeof u === "string");
          await patchJob(id, { status: "SUCCESS", progress: "100%", outputs, doneAt: Date.now() });
          await saveFiles(id, outputs);
          return;
        }
        if (d.status === "FAILURE" || !PENDING.has(d.status)) { await patchJob(id, { status: "FAILURE", error: ([d.fail_reason, d.fail_code && d.fail_code !== d.fail_reason ? "code " + d.fail_code : ""].filter(Boolean).join(" · ") || "Siray reported " + d.status) + " (task " + taskId + ")", doneAt: Date.now() }); return; }
        await patchJob(id, { status: d.status, progress: d.progress || "" });   // each write also keeps this worker awake
      }
    } finally { polling.delete(id); }
  }

  async function saveFiles(id, outputs) {
    if (!outputs.length || !hasDownloads()) return;
    const job = ((await get(SP.JOBS_KEY)) || []).find((j) => j.id === id) || {};
    const t = new Date(job.at || Date.now()), p2 = (x) => String(x).padStart(2, "0");
    const stamp = t.getFullYear() + "-" + p2(t.getMonth() + 1) + "-" + p2(t.getDate()) + "-" + p2(t.getHours()) + p2(t.getMinutes()) + p2(t.getSeconds());
    const base = "Flow Spice/" + stamp + "-" + String((job.src && job.src.id) || "img").replace(/[^A-Za-z0-9_-]/g, "").slice(0, 12);
    const files = [];
    for (let i = 0; i < outputs.length; i++) {
      const ext = (/\.(png|jpe?g|webp)(\?|$)/i.exec(outputs[i]) || [, "png"])[1].toLowerCase();
      const dl = await new Promise((r) => chrome.downloads.download({ url: outputs[i], filename: base + "-" + (i + 1) + "." + ext, conflictAction: "uniquify", saveAs: false }, (did) => r(chrome.runtime.lastError ? null : did)));
      if (dl != null) files.push(dl);
    }
    await patchJob(id, { files });
  }

  async function price(model) {
    const c = await cfg();
    if (!c.key || !(await hasPerm({ origins: [ORIGIN] }))) return { ok: false };
    try {
      const res = await api("/v1/models/pricing/" + model, { method: "GET" }, c.key);   // model ids contain a "/" — kept as-is, like the docs' examples
      const d = res.body && res.body.data;
      if (res.status === 404) return { ok: false, missing: true, reason: "Siray says this model isn't available to your account" };
      if (!res.ok || !d) return { ok: false, reason: errText(res) };
      const cat = d.catalog || {};
      const lines = (cat.pricing_options || []).slice(0, 8).map((o) => (o.parameters || []).map((p) => p.value).join(" · ")).filter(Boolean);
      if (!lines.length && d.output_price) lines.push("$" + d.output_price.price + " / " + d.output_price.unit);
      return { ok: true, billing: d.billing_type, discount: d.discount || 0, lines, note: cat.pricing_description || "" };
    } catch (e) { return { ok: false, reason: String(e && e.message || e) }; }
  }

  chrome.runtime.onMessage.addListener((msg, sender, reply) => {
    if (!msg || typeof msg.type !== "string" || !msg.type.startsWith("fst-spice-")) return;
    if (msg.type === "fst-spice-run") { run(msg).then(reply); return true; }
    if (msg.type === "fst-spice-next") { next(msg.jobId).then(reply); return true; }
    if (msg.type === "fst-spice-cfg") { cfg().then((c) => reply({ ok: true, hasKey: !!c.key, model: c.model, size: c.size, n: c.n, presets: c.presets || [], lastPrompt: c.lastPrompt || "" })); return true; }
    if (msg.type === "fst-spice-price") { price(SP.modelById(msg.model).id).then(reply); return true; }
    if (msg.type === "fst-spice-open") { chrome.tabs.create({ url: chrome.runtime.getURL("spice.html") + (msg.jobId ? "#" + encodeURIComponent(msg.jobId) : "") }); reply({ ok: true }); return; }
    if (msg.type === "fst-spice-resume") { resume(); reply({ ok: true }); return; }
  });

  // A service worker can be stopped mid-poll; every start picks unfinished tasks back up (task ids are stored).
  async function resume() { for (const j of (await get(SP.JOBS_KEY)) || []) if (PENDING.has(j.status) && j.taskId) poll(j.id, j.taskId); }
  resume();
})();
