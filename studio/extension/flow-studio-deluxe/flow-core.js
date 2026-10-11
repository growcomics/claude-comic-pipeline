// 3DMC Studio Tools — Flow shared core (runs in the page origin, before content.js).
// One harvester for all actions: reads a Flow project via the tRPC
// `flow.projectInitialData` query (prompts + input refs + outputs + model +
// timestamp), plus the active account. Everything downstream (Download / Send to
// Studio / Review bundle) consumes the normalized records this produces.
//
// 2026-09-07: Flow moved to flow.google.com (a different, Angular front end) and
// labs.google/fx/tools/flow/* now redirects there. The tRPC API itself still lives
// on labs.google and still answers with the same Google session, so every API call
// is now ABSOLUTE to labs.google. From a flow.google.com page that is cross-origin
// (CORS-blocked in the page), so the call is relayed through background.js, which
// has host permission for labs.google and sends the session cookie — the same path
// the media fetches already use.
(() => {
  if (self.FlowCore) return;

  const API = "https://labs.google";
  const MEDIA = (id) => API + "/fx/api/trpc/media.getMediaUrlRedirect?name=" + encodeURIComponent(id);
  let lastError = "";   // why the last harvest came back empty — content.js shows it
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  // Google FIFE image URL → full-resolution original. A grid tile src carries a size suffix
  // ("…=s512-rw") and a record's lh3 URL carries NONE (it is itself a 512px thumbnail), so we
  // strip any existing "=<suffix>" and append "=s0" — that returns the original either way
  // (verified 2026-09-15: 512px thumb → 768×1376 / 1280×720 originals; "=s0" won over "=s1024").
  const fullRes = (u) => u ? u.replace(/=[^=/]*$/, "") + "=s0" : u;
  // GET a labs.google API path as JSON: direct when the page IS labs.google, else via the worker.
  async function apiJson(path) {
    const url = API + path;
    if (location.origin === API) {
      try {
        const r = await fetch(url, { credentials: "include", headers: { "content-type": "application/json" } });
        return { ok: r.ok, status: r.status, json: r.ok ? await r.json() : null };
      } catch (e) { return { ok: false, status: 0, error: String((e && e.message) || e) }; }
    }
    return new Promise((res) => {
      try {
        chrome.runtime.sendMessage({ type: "flowJson", url }, (r) => {
          const le = chrome.runtime.lastError;
          res(r || { ok: false, status: 0, error: (le && le.message) || "no reply from the service worker" });
        });
      } catch (e) { res({ ok: false, status: 0, error: String((e && e.message) || e) }); }
    });
  }
  const unwrap = (j) => (j && j.result && j.result.data ? (j.result.data.json || j.result.data) : j);
  const currentProjectId = () => (location.pathname.match(/project\/([0-9a-f-]+)/i) || [])[1] || null;

  async function fetchProjectData() {
    lastError = "";
    const pid = currentProjectId();
    if (!pid) { lastError = "not on a project page (/project/<id>)"; return null; }
    const input = encodeURIComponent(JSON.stringify({ json: { projectId: pid } }));
    const r = await apiJson("/fx/api/trpc/flow.projectInitialData?input=" + input);
    if (!r.ok) {
      lastError = r.status === 401 || r.status === 403
        ? "labs.google says " + r.status + " — open https://labs.google/fx/tools/flow once in this Chrome profile to sign in, then retry"
        : "labs.google API " + (r.status ? "HTTP " + r.status : "unreachable") + (r.error ? " (" + r.error + ")" : "");
      return null;
    }
    const d = unwrap(r.json);
    if (!(d && d.projectContents)) { lastError = "unexpected API shape (no projectContents)"; return null; }
    return d;
  }

  async function fetchAccount() {
    try { const r = await apiJson("/fx/api/auth/session"); const j = r.ok ? r.json : null; if (j && j.user && j.user.email) return j.user.email; } catch (e) {}
    try {
      const found = new Set();
      document.querySelectorAll("script").forEach((s) => { if (s.textContent) { const mm = s.textContent.match(/[a-zA-Z0-9._%+-]+@gmail\.com/g); if (mm) mm.forEach((e) => found.add(e)); } });
      const arr = [...found]; if (arr.length) return arr[0];
    } catch (e) {}
    return null;
  }

  function modelMap(data) {
    const m = {};
    try { (data.modelConfig.imageModelFamilies || []).forEach((fam) => { const name = (fam.displayName || fam.id || "").replace(/^[^\w]+\s*/, "").trim(); (fam.usages || []).forEach((u) => { if (u.key) m[u.key] = name; }); if (fam.id) m[fam.id] = name; }); } catch (e) {}
    return m;
  }

  // one record per generation, newest-first
  function extract(data) {
    const pc = data.projectContents || {}, media = Array.isArray(pc.media) ? pc.media : [], mmap = modelMap(data), byWf = {};
    // ⭐ favorites: workflow-level metadata.favorited (workflow.name === gen id). Carried
    // onto each record so Send-to-Studio can land favorited gens pre-approved (bridge fav=1).
    const favSet = new Set((Array.isArray(pc.workflows) ? pc.workflows : []).filter((w) => w && w.metadata && w.metadata.favorited).map((w) => w.name));
    media.forEach((m) => {
      const gi = m.image && m.image.generatedImage; if (!gi) return;          // skip user uploads + video (they appear as input refs)
      const wf = m.workflowId || gi.workflowId || m.name; if (!wf) return;
      if (!byWf[wf]) byWf[wf] = {
        gen_id: wf, fav: favSet.has(wf), prompt: gi.prompt || "", model_key: gi.modelNameType || "", model: mmap[gi.modelNameType] || gi.modelNameType || "",
        timestamp: (m.mediaMetadata && m.mediaMetadata.createTime) || "", aspect_ratio: gi.aspectRatio || "",
        seed: typeof gi.seed === "number" ? gi.seed : null, project: data.projectName || "", project_id: data.projectId || "",
        dimensions: (m.image && m.image.dimensions) || null, output_media_ids: [], input_ref_media_ids: [],
      };
      const rec = byWf[wf];
      if (!rec.prompt && gi.prompt) rec.prompt = gi.prompt;
      if (m.name && !rec.output_media_ids.includes(m.name)) rec.output_media_ids.push(m.name);
      const rd = m.mediaMetadata && m.mediaMetadata.requestData;
      const inp = rd && rd.imageGenerationRequestData && rd.imageGenerationRequestData.imageGenerationImageInputs;
      if (Array.isArray(inp)) inp.forEach((i) => { if (i && i.mediaId && !rec.input_ref_media_ids.includes(i.mediaId)) rec.input_ref_media_ids.push(i.mediaId); });
    });
    const records = Object.values(byWf).map((r) => { r.flow_url = r.project_id && r.output_media_ids[0] ? "https://labs.google/fx/tools/flow/project/" + r.project_id + "/edit/" + r.output_media_ids[0] : ""; return r; });
    records.sort((a, b) => String(b.timestamp || "").localeCompare(String(a.timestamp || "")));
    return records;
  }

  async function getProject() {
    const data = await fetchProjectData();
    if (!data) return null;
    return { name: data.projectName || "", id: data.projectId || "", records: extract(data) };
  }

  // Review-bundle plan: outputs + deduped input refs + a manifest. Same shape the
  // standalone review-harvester produced.
  function buildReviewBundle(records, account, projectName, projectId, limit) {
    const now = new Date();
    const folder = "flow-review-export-" + now.toISOString().replace(/[:.]/g, "-").slice(0, 19);
    const recs = (limit && limit !== Infinity) ? records.slice(0, limit) : records.slice();
    const jobs = [], seen = new Set(), refPathById = {};
    const addJob = (url, path) => { if (!seen.has(path)) { seen.add(path); jobs.push({ url, path }); } };
    const generations = recs.map((r) => {
      const outputs = r.output_media_ids.map((id, i) => { const rel = "outputs/" + r.gen_id + "-out-" + i + ".jpg"; addJob(MEDIA(id), folder + "/" + rel); return rel; });
      const input_refs = r.input_ref_media_ids.map((id) => { if (!refPathById[id]) { const rel = "refs/ref-" + id + ".jpg"; refPathById[id] = rel; addJob(MEDIA(id), folder + "/" + rel); } return refPathById[id]; });
      return { gen_id: r.gen_id, account: account || null, timestamp: r.timestamp, model: r.model, model_key: r.model_key, project: r.project, project_id: r.project_id, prompt: r.prompt, aspect_ratio: r.aspect_ratio, seed: r.seed, dimensions: r.dimensions, input_refs, input_ref_media_ids: r.input_ref_media_ids, outputs, output_media_ids: r.output_media_ids, flow_url: r.flow_url };
    });
    const manifest = JSON.stringify({ meta: { exported_at: now.toISOString(), account: account || null, project: projectName || null, project_id: projectId || null, generation_count: generations.length, ref_files: Object.keys(refPathById).length, source: "flow-studio-tools" }, generations }, null, 2);
    return { folder, jobs, manifest, count: generations.length, refCount: Object.keys(refPathById).length };
  }

  // flat list of output images in CHRONOLOGICAL order (first-generated first), one
  // entry per output media. `records` is newest-first, so we pick the most-recent N
  // (the limit), then REVERSE so the oldest of that set leads — matching comic page
  // order: the first thing you generated in Flow becomes the first page in the Studio.
  function outputList(records, limit) {
    const recs = (limit && limit !== Infinity) ? records.slice(0, limit) : records.slice();
    recs.reverse();
    const out = [];
    recs.forEach((r) => r.output_media_ids.forEach((id) => out.push({ id, url: MEDIA(id), gen_id: r.gen_id, prompt: r.prompt || "", fav: r.fav ? 1 : 0 })));
    return out;
  }

  // flow.google.com (2.8.6): the labs.google project RPC was deprecated and disabled
  // (2026-09-15 — "Flow RPCs have been deprecated and disabled. Flow has migrated to
  // flow.google.com"), so Download reads the project's OWN grid instead of the dead API.
  // Each output tile is `flow-grid-tile-container img[data-media-id]` whose `src` is a
  // signed `https://flow.google.com/asb/<token>=s512-rw` THUMBNAIL; the trailing bit is a
  // Google FIFE size suffix, so swapping it to `=s0` yields the full-resolution original
  // (verified 2026-09-15: the 512px webp thumb → the 768×1376 jpeg the model produced).
  // The grid is a `cdk-virtual-scroll-viewport` (off-screen tiles unmount and their <img>
  // recycles), so we page it, collecting NEWEST-first, until it stops growing or we have
  // `limit` images. Returns [{id, url}] OLDEST-first — generation / comic-page order, the
  // same ordering the old outputList produced. Media ids are unique per output image.
  async function getGridOutputs(limit, onProgress) {
    const scroller = document.querySelector("cdk-virtual-scroll-viewport") || document.scrollingElement;
    const ordered = [], seen = new Set();
    const grab = () => {
      document.querySelectorAll("flow-grid-tile-container img[data-media-id]").forEach((img) => {
        const id = img.getAttribute("data-media-id"); if (!id || seen.has(id)) return;
        const src = img.currentSrc || img.getAttribute("src") || "";
        if (!/\/asb\//.test(src)) return;                       // tile not painted yet — skip; a later pass catches it
        seen.add(id);
        // ★ favorite state lives only in the DOM (NOT in the Zzl0ze payload — verified 2026-09-15
        // by toggling one and diffing): a favorited tile's hotbar button reads "Remove favorite",
        // an un-favorited one "Favorite". Send-to-Studio reads this so favourites ingest pre-approved.
        const tile = img.closest("flow-grid-tile-container");
        const fav = tile && tile.querySelector('button[aria-label="Remove favorite"]') ? 1 : 0;
        ordered.push({ id, url: fullRes(src), fav });
      });
      if (onProgress) try { onProgress(ordered.length); } catch (e) {}
    };
    const want = (limit && limit !== Infinity) ? limit : Infinity;
    if (scroller && scroller.scrollTo) scroller.scrollTo(0, 0); else if (scroller) scroller.scrollTop = 0;
    await sleep(160); grab();
    let guard = 0, lastLen = -1, stall = 0;
    while (scroller && guard++ < 400 && ordered.length < want) {
      const before = scroller.scrollTop;
      scroller.scrollTop = before + Math.max(240, scroller.clientHeight * 0.85);
      await sleep(160); grab();
      if (ordered.length === lastLen) stall++; else { stall = 0; lastLen = ordered.length; }
      if (scroller.scrollTop <= before + 1 && stall >= 2) { await sleep(220); grab(); break; }   // reached the bottom
      if (stall >= 8) break;                                    // grid not growing — done (or nothing to page)
    }
    const pick = (want === Infinity) ? ordered.slice() : ordered.slice(0, want);
    pick.reverse();                                             // oldest-first = generation / page order
    return pick;
  }

  // ───────── flow.google.com project READ via the new backend (2.8.7) ─────────
  // The labs.google tRPC that getProject()/buildReviewBundle() used was deprecated and
  // disabled (2026-09-15). flow.google.com fetches a project over a Google `batchexecute`
  // RPC, rpcid `Zzl0ze`, arg `["projects/<id>",null,null,null,[1]]`. We reconstruct that
  // POST from the ISOLATED content-script world: the request needs the WIZ tokens (SNlM0e =
  // the `at` XSRF token, FdrFJe = f.sid, cfb2h = bl) which live on the page's `window`
  // (unreadable from here) but are ALSO printed into the inline bootstrap `<script>`, so we
  // scrape them out of the DOM HTML; then POST same-origin (cookies ride) and decode the
  // `)]}'`-prefixed envelope. Verified live 2026-09-15 across 3 projects (0 / 1 / many refs).
  function wizToken(k) { const m = document.documentElement.innerHTML.match(new RegExp('"' + k + '":"([^"]+)"')); return m ? m[1] : null; }
  function decodeBatchExecute(text, rpcid) {
    const m = text.match(new RegExp('\\[\\["wrb\\.fr","' + rpcid + '","((?:\\\\.|[^"\\\\])*)"'));
    if (!m) return null;
    try { return JSON.parse(JSON.parse('"' + m[1] + '"')); } catch (e) { return null; }
  }
  async function fetchProjectAngular(pid) {
    const at = wizToken("SNlM0e"), fsid = wizToken("FdrFJe"), bl = wizToken("cfb2h");
    if (!at) { lastError = "couldn't read the page's request token — reload the Flow tab and retry"; return null; }
    const params = new URLSearchParams({ rpcids: "Zzl0ze", "source-path": "/project/" + pid, "f.sid": fsid || "", bl: bl || "", hl: "en", _reqid: String(Math.floor(Math.random() * 1e6)), rt: "c" });
    const inner = JSON.stringify(["projects/" + pid, null, null, null, [1]]);
    const body = "f.req=" + encodeURIComponent(JSON.stringify([[["Zzl0ze", inner, null, "generic"]]])) + "&at=" + encodeURIComponent(at) + "&";
    let text;
    try {
      const r = await fetch(location.origin + "/_/AiSandboxAngularFrontend/data/batchexecute?" + params.toString(),
        { method: "POST", credentials: "include", headers: { "content-type": "application/x-www-form-urlencoded;charset=UTF-8" }, body });
      if (!r.ok) { lastError = "flow.google.com project API HTTP " + r.status; return null; }
      text = await r.text();
    } catch (e) { lastError = "flow.google.com project API unreachable (" + ((e && e.message) || e) + ")"; return null; }
    const data = decodeBatchExecute(text, "Zzl0ze");
    if (!data || !Array.isArray(data[2])) { lastError = "unexpected project API response shape (no records)"; return null; }
    return data;
  }
  // Per-record extraction from `Zzl0ze` data[2]. The nested indices VARY between projects
  // (the prompt sits at different depths once a project uses refs), so we SEARCH rather than
  // hardcode: prompt = the longest natural-language string in the record; output image URL =
  // rec[5][5] when present (stable across projects) else the first https string; refs = every
  // OTHER uuid in the record (a best-effort superset — see the note below). Verified live.
  function extractAngularRecords(data) {
    const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    const strs = (n, acc) => { acc = acc || []; if (typeof n === "string") acc.push(n); else if (Array.isArray(n)) n.forEach((c) => strs(c, acc)); return acc; };
    return (data[2] || []).map((rec) => {
      const outId = rec[0] || "", projId = rec[1] || "", wfId = rec[2] || "";
      const detail = Array.isArray(rec[5]) ? rec[5] : [];
      const all = strs(rec);
      const url = (typeof detail[5] === "string" && /^https:\/\//.test(detail[5])) ? detail[5] : (all.find((s) => /^https:\/\//.test(s)) || "");
      const prompt = all.filter((s) => !/^https/.test(s) && !UUID.test(s) && /\s/.test(s)).sort((a, b) => b.length - a.length)[0] || "";
      const ts = (Array.isArray(detail[0]) && typeof detail[0][0] === "number") ? detail[0][0] : null;
      const refs = [...new Set(all.filter((s) => UUID.test(s) && s !== outId && s !== projId && s !== wfId))];
      return { gen_id: wfId || outId, out_media_id: outId, project_id: projId, prompt: prompt, image_url: url, timestamp: ts, input_ref_media_ids: refs };
    });
  }
  // media-id → uploaded/source filename, from data[1] (every media record: rec[3][4] = the
  // media id, rec[3][0] = its name/title). Refs are UPLOADED images with a filename here but
  // NO image URL anywhere in the payload (verified 2026-09-15), so the Review manifest can
  // NAME the references a generation used, but their image files can't be fetched from Zzl0ze.
  function mediaNames(data) {
    const map = {};
    (data[1] || []).forEach((r) => { const d = (Array.isArray(r) && Array.isArray(r[3])) ? r[3] : null; if (d && d[4]) map[d[4]] = d[0] || null; });
    return map;
  }
  // One record per OUTPUT image, with prompt + named refs. `name` from the tab title (Zzl0ze
  // carries no clean project name). Sets lastError on failure, like getProject().
  async function getAngularProject() {
    lastError = "";
    const pid = currentProjectId();
    if (!pid) { lastError = "not on a project page (/project/<id>)"; return null; }
    const data = await fetchProjectAngular(pid);
    if (!data) return null;
    const names = mediaNames(data);
    const records = extractAngularRecords(data).map((r) => Object.assign(r, {
      input_refs: (r.input_ref_media_ids || []).map((id) => ({ media_id: id, name: names[id] || null })),
    }));
    const name = (document.title || "").replace(/[\\/:*?"<>|]+/g, " ").replace(/\s*[-–|].*$/, "").trim() || "Flow project";
    return { id: pid, name: name, records: records };
  }
  // Flat outputs for Send-to-Studio / Auto-sync: prompts from Zzl0ze paired with the record's
  // OWN full-res image URL (lh3 =s0) — no grid scrolling, so an auto-sync tick never yanks the
  // user's view. Oldest-first (beat order), most-recent `limit`. Same {id,url,gen_id,prompt,fav}
  // shape outputList produced. fav is 0 — the favorite flag isn't located in the new payload
  // yet, so items ingest un-favorited (re-star them in the Studio).
  async function getAngularOutputs(limit) {
    const proj = await getAngularProject();
    if (!proj) return null;
    // Only real generations go to the Studio — data[2] also lists the project's UPLOADED
    // reference images (they carry an image but no prompt), and those must not be ingested
    // as panels. Requiring a prompt matches the old harvest's generatedImage-only filter.
    const gens = proj.records.filter((r) => r.image_url && r.prompt);
    const sorted = gens.sort((a, b) => (a.timestamp || 0) - (b.timestamp || 0));
    const recs = (limit && limit !== Infinity) ? sorted.slice(-limit) : sorted;
    return recs.map((r) => ({ id: r.out_media_id, url: fullRes(r.image_url), gen_id: r.gen_id, prompt: r.prompt || "", fav: 0 }));
  }
  // Review bundle for the new backend: full-res outputs (joined to the grid's =s0 URLs by
  // media id, falling back to the record's own image URL at =s0) + a manifest of prompts,
  // timestamps and ref media ids. `gmap` = Map(mediaId → full-res grid URL) from
  // getGridOutputs. Records are ordered oldest-first by timestamp (page/generation order).
  // NOTE: reference INPUT images are listed by media id but not downloaded in this version
  // (their URL is not yet reliably located in the payload) — outputs + prompts are complete.
  function buildReviewBundleAngular(records, account, projectName, projectId, limit, gmap) {
    const now = new Date();
    const folder = "flow-review-export-" + now.toISOString().replace(/[:.]/g, "-").slice(0, 19);
    const sorted = records.slice().sort((a, b) => (a.timestamp || 0) - (b.timestamp || 0));
    const recs = (limit && limit !== Infinity) ? sorted.slice(-limit) : sorted;
    const jobs = [], refs = new Map();
    const generations = recs.map((r, i) => {
      const nnn = String(i + 1).padStart(3, "0");
      const gridUrl = gmap && gmap.get(r.out_media_id);
      const url = gridUrl || (r.image_url ? fullRes(r.image_url) : "");
      const rel = "outputs/" + nnn + "-" + String(r.out_media_id || r.gen_id || "img").slice(0, 8) + ".jpg";
      if (url) jobs.push({ url, path: folder + "/" + rel });
      const inRefs = r.input_refs || (r.input_ref_media_ids || []).map((id) => ({ media_id: id, name: null }));
      inRefs.forEach((x) => refs.set(x.media_id, x.name || null));
      return { gen_id: r.gen_id, out_media_id: r.out_media_id, timestamp: r.timestamp, project: projectName || "", project_id: projectId || "", prompt: r.prompt || "", output: url ? rel : null, output_full_res: !!gridUrl, input_refs: inRefs };
    });
    const manifest = JSON.stringify({
      meta: { exported_at: now.toISOString(), account: account || null, project: projectName || null, project_id: projectId || null, generation_count: generations.length, references: [...refs.entries()].map(([media_id, name]) => ({ media_id, name })), source: "flow-studio-tools", backend: "flow.google.com batchexecute Zzl0ze", note: "Outputs are full-resolution. Reference INPUT images are listed by id and filename but not downloaded — their URL is not present in the project payload." },
      generations,
    }, null, 2);
    return { folder, jobs, manifest, count: generations.length };
  }

  self.FlowCore = { API, MEDIA, currentProjectId, getProject, getGridOutputs, getAngularProject, getAngularOutputs, buildReviewBundle, buildReviewBundleAngular, getAccount: fetchAccount, outputList, get lastError() { return lastError; } };
})();
