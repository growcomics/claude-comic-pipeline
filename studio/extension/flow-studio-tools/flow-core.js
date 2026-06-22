// Flow Studio Tools — shared core (runs in the page origin, before content.js).
// One harvester for all actions: reads a Flow project via the same-origin tRPC
// `flow.projectInitialData` query (prompts + input refs + outputs + model +
// timestamp), plus the active account. Everything downstream (Download / Send to
// Studio / Review bundle) consumes the normalized records this produces.
(() => {
  if (self.FlowCore) return;

  const MEDIA = (id) => "https://labs.google/fx/api/trpc/media.getMediaUrlRedirect?name=" + encodeURIComponent(id);
  const unwrap = (j) => (j && j.result && j.result.data ? (j.result.data.json || j.result.data) : j);
  const currentProjectId = () => (location.pathname.match(/project\/([0-9a-f-]+)/i) || [])[1] || null;

  async function fetchProjectData() {
    const pid = currentProjectId();
    if (!pid) return null;
    try {
      const input = encodeURIComponent(JSON.stringify({ json: { projectId: pid } }));
      const r = await fetch("/fx/api/trpc/flow.projectInitialData?input=" + input, { credentials: "include", headers: { "content-type": "application/json" } });
      if (!r.ok) return null;
      const d = unwrap(await r.json());
      return d && d.projectContents ? d : null;
    } catch (e) { return null; }
  }

  async function fetchAccount() {
    try { const r = await fetch("/fx/api/auth/session", { credentials: "include" }); if (r.ok) { const j = await r.json(); if (j && j.user && j.user.email) return j.user.email; } } catch (e) {}
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
    media.forEach((m) => {
      const gi = m.image && m.image.generatedImage; if (!gi) return;          // skip user uploads + video (they appear as input refs)
      const wf = m.workflowId || gi.workflowId || m.name; if (!wf) return;
      if (!byWf[wf]) byWf[wf] = {
        gen_id: wf, prompt: gi.prompt || "", model_key: gi.modelNameType || "", model: mmap[gi.modelNameType] || gi.modelNameType || "",
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

  // flat list of output images (newest-first), one entry per output media
  function outputList(records, limit) {
    const recs = (limit && limit !== Infinity) ? records.slice(0, limit) : records.slice();
    const out = [];
    recs.forEach((r) => r.output_media_ids.forEach((id) => out.push({ id, url: MEDIA(id), gen_id: r.gen_id })));
    return out;
  }

  self.FlowCore = { MEDIA, currentProjectId, getProject, getAccount: fetchAccount, buildReviewBundle, outputList };
})();
