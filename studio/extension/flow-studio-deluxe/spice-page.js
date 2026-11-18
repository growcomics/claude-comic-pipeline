// 3DMC Studio Tools — the 🌶 Spice page (spice.html, also the extension's Options page): Siray key + optional
// permissions, default model / size, prompt presets, and every Spice job with its results.
(() => {
  const SP = self.FOSpice;
  const $ = (id) => document.getElementById(id);
  const get = (k) => new Promise((r) => chrome.storage.local.get(k, (o) => r(o ? o[k] : undefined)));
  const set = (k, v) => new Promise((r) => chrome.storage.local.set({ [k]: v }, () => r()));
  const cfg = async () => Object.assign({}, SP.DEFAULTS, (await get(SP.CFG_KEY)) || {});
  const say = (el, text, kind) => { el.textContent = text || ""; el.className = "msg" + (kind ? " " + kind : ""); };
  function h(tag, props, ...kids) {
    const el = document.createElement(tag);
    for (const [k, v] of Object.entries(props || {})) { if (v == null) continue; if (k.startsWith("on")) el.addEventListener(k.slice(2), v); else el.setAttribute(k, v); }
    for (const k of kids.flat()) if (k != null && k !== false) el.append(k);
    return el;
  }

  for (const m of SP.MODELS) $("model").append(h("option", { value: m.id }, m.label));
  function fillSizes(modelId, want) {
    const m = SP.modelById(modelId);
    $("size").replaceChildren(...m.sizes.map((s) => h("option", { value: s }, s)));
    $("size").value = m.sizes.includes(want) ? want : m.sizes[Math.min(1, m.sizes.length - 1)];
  }

  async function load() {
    const c = await cfg();
    $("key").value = c.key ? "••••••••" + c.key.slice(-4) : "";
    $("key").dataset.masked = c.key ? "1" : "";
    $("model").value = SP.modelById(c.model).id;
    fillSizes(c.model, c.size);
    $("presets").value = (c.presets || []).map((p) => p.name + ": " + p.prompt).join("\n");
    if (!c.key) say($("setupMsg"), "Paste your API key and press Save & allow. Chrome then asks once to let 3DMC Studio Tools reach api.siray.ai. Results also save to Downloads/Flow Spice/.");
  }
  $("key").addEventListener("focus", () => { if ($("key").dataset.masked) { $("key").value = ""; $("key").dataset.masked = ""; } });
  $("model").addEventListener("change", async () => { fillSizes($("model").value, $("size").value); const c = await cfg(); c.model = $("model").value; c.size = $("size").value; await set(SP.CFG_KEY, c); });
  $("size").addEventListener("change", async () => { const c = await cfg(); c.size = $("size").value; await set(SP.CFG_KEY, c); });

  $("save").addEventListener("click", () => {
    // permissions.request must run inside the click itself (user gesture). Nothing awaits before it.
    chrome.permissions.request({ origins: [SP.API + "/*"] }, async (granted) => {
      const c = await cfg();
      const typed = $("key").dataset.masked ? "" : $("key").value.trim();
      if (typed) c.key = typed;
      c.model = $("model").value; c.size = $("size").value;
      await set(SP.CFG_KEY, c);
      await load();
      if (!c.key) return say($("setupMsg"), "No key yet. Paste it first.", "err");
      if (!granted) return say($("setupMsg"), "Key saved, but Chrome didn't grant access to api.siray.ai, so Spice can't run. Press Save & allow again and choose Allow.", "err");
      say($("setupMsg"), "Saved ✓ Checking the key…");
      checkPrice(true);
    });
  });
  $("price").addEventListener("click", () => checkPrice(false));
  function checkPrice(afterSave) {
    chrome.runtime.sendMessage({ type: "fst-spice-price", model: $("model").value }, (r) => {
      if (chrome.runtime.lastError || !r) return say($("setupMsg"), "No answer from the extension.", "err");
      if (!r.ok) return say($("setupMsg"), r.reason ? "Siray: " + r.reason : "Save your key first.", "err");
      const lines = r.lines.length ? r.lines.join("\n") : "(Siray didn't list prices for this model)";
      say($("setupMsg"), (afterSave ? "Key works ✓\n" : "") + SP.modelById($("model").value).label + " pricing" + (r.discount ? " (your discount " + Math.round(r.discount * 100) + "%)" : "") + ":\n" + lines + (r.note ? "\n" + r.note : ""), "ok");
    });
  }

  $("savePresets").addEventListener("click", async () => {
    const presets = $("presets").value.split("\n").map((l) => l.trim()).filter(Boolean).map((l) => {
      const i = l.indexOf(":");
      return i > 0 && i < 40 ? { name: l.slice(0, i).trim(), prompt: l.slice(i + 1).trim() } : { name: l.slice(0, 24), prompt: l };
    }).filter((p) => p.prompt).slice(0, 30);
    const c = await cfg(); c.presets = presets; await set(SP.CFG_KEY, c);
    say($("presetMsg"), "Saved " + presets.length + " preset" + (presets.length === 1 ? "" : "s") + " ✓", "ok");
  });

  // ───── results ─────
  async function renderJobs() {
    const jobs = (await get(SP.JOBS_KEY)) || [];
    $("count").textContent = jobs.length ? jobs.length + " job" + (jobs.length === 1 ? "" : "s") : "";
    if (!jobs.length) { $("jobs").replaceChildren(h("div", { class: "empty" }, "Nothing yet. In Flow, open the Studio Tools panel → 🌶 tab, then hit 🌶 on any image.")); return; }
    $("jobs").replaceChildren(...jobs.map((j) => h("div", { class: "job", id: j.id },
      h("div", { class: "src" }, j.src && j.src.thumb ? h("img", { src: j.src.thumb, alt: "source", title: "Source image from Flow" }) : h("div", { class: "meta" }, "(no preview)")),
      h("div", null,
        h("div", { class: "meta" }, h("span", { class: "st " + j.status }, j.status === "SUCCESS" ? "Done" : j.status === "FAILURE" ? "Failed" : "Working… " + (j.progress || j.status.toLowerCase())),
          "  ·  " + SP.modelById(j.model).label + " · " + j.size + " · " + j.aspect + (j.n > 1 ? " · ×" + j.n : "") + "  ·  " + new Date(j.at).toLocaleString() + (j.src && j.src.title ? "  ·  " + j.src.title : "")),
        h("div", { class: "prompt" }, j.prompt),
        j.error ? h("div", { class: "msg err" }, j.error) : null,
        h("div", { class: "outs" }, (j.outputs || []).map((u, i) => h("div", { class: "out" },
          h("a", { href: u, target: "_blank", rel: "noopener", title: "Open full size" }, h("img", { src: u, alt: "result " + (i + 1), loading: "lazy" })),
          h("button", { class: "primary", title: "Edit this result again with a new prompt", onclick: () => openAgain(j, u) }, "🌶 Spice again")))),
        h("div", { class: "acts" },
          (j.files || []).length ? h("button", { onclick: () => chrome.downloads.show(j.files[0]) }, "Show in Finder") : null,
          (j.outputs || []).length && !(j.files || []).length ? h("button", { onclick: () => j.outputs.forEach((u, i) => chrome.downloads && chrome.downloads.download({ url: u, filename: "Flow Spice/" + j.id + "-" + (i + 1) + ".png", conflictAction: "uniquify" })) }, "Download") : null,
          nextBtn(j),
          h("button", { onclick: () => navigator.clipboard.writeText(j.prompt) }, "Copy prompt"),
          h("button", { onclick: () => removeJob(j.id), title: "Removes this entry from the list. Downloaded files stay where they are." }, "Remove from list"))))));
    const want = decodeURIComponent(location.hash.slice(1));
    if (want && !renderJobs._flashed) { const el = document.getElementById(want); if (el) { renderJobs._flashed = true; el.classList.add("flash"); el.scrollIntoView({ block: "center" }); } }
  }
  // ───── ↻ Try next model: same input + prompt on the next model in FOSpice.NEXT (Qwen 3 Edit → Seedream 5.5 →
  // Seedream 5.0 Pro → Wan 2.7). Offered once a job has finished or failed, until the chain runs out.
  function nextBtn(j) {
    if (j.status !== "SUCCESS" && j.status !== "FAILURE") return null;
    const nm = SP.nextModel((j.tried || []).concat(j.model));
    if (!nm) return null;
    const name = SP.modelById(nm).label.split(" · ")[0].replace(" 🌶", "");
    return h("button", { class: j.status === "FAILURE" ? "primary" : "", title: "Send the same image and prompt to " + name + ". Fallback order: " + SP.NEXT.map((id) => SP.modelById(id).label.split(" · ")[0].replace(" 🌶", "")).join(" → "),
      onclick: (e) => { e.target.disabled = true; e.target.textContent = "Sending…";
        chrome.runtime.sendMessage({ type: "fst-spice-next", jobId: j.id }, (r) => {
          if (chrome.runtime.lastError || !r || !r.ok) { e.target.disabled = false; e.target.textContent = "↻ Try " + name; alert("🌶 " + ((r && r.reason) || (chrome.runtime.lastError && chrome.runtime.lastError.message) || "Couldn't try the next model")); return; }
          renderJobs._flashed = false; location.hash = r.jobId; window.scrollTo({ top: 0, behavior: "smooth" });
        }); } }, "↻ Try " + name);
  }

  // ───── 🌶 Spice again: a finished result → Siray again, by its own URL (Siray accepts image URLs) ─────
  let agJob = null, agUrl = "", agAr = 0;
  const jobAr = (job) => { const [x, y] = String((job && job.aspect) || "").split(":").map(Number); return x > 0 && y > 0 ? x / y : 0; };   // a result keeps its job's shape
  for (const m of SP.MODELS) $("agModel").append(h("option", { value: m.id }, m.label));
  function agFill(want) {
    const m = SP.modelById($("agModel").value);
    $("agSize").replaceChildren(...m.sizes.map((s) => h("option", { value: s }, s)));
    $("agSize").value = m.sizes.includes(want) ? want : m.sizes[m.sizes.length - 1];
    $("agN").style.display = m.n ? "" : "none";
  }
  $("agModel").addEventListener("change", () => agFill($("agSize").value));
  async function openAgain(job, url) {
    const c = await cfg();
    agJob = job; agUrl = url; agAr = jobAr(job);
    $("agImg").src = url;
    const probe = new Image(); probe.onload = () => { agAr = probe.naturalWidth / probe.naturalHeight; }; probe.src = url;
    $("agPresets").replaceChildren(...(c.presets || []).slice(0, 12).map((p) => h("button", { title: p.prompt, onclick: () => { $("agPrompt").value = p.prompt; $("agPrompt").focus(); } }, p.name)));
    $("agPrompt").value = job.prompt || c.lastPrompt || "";
    $("agModel").value = SP.modelById(job.model || c.model).id; agFill(c.size);
    $("agN").value = "1";
    say($("agMsg"), "");
    $("again").classList.add("show");
    $("agPrompt").focus();
  }
  const agClose = () => { $("again").classList.remove("show"); agJob = null; };
  $("agCancel").addEventListener("click", agClose);
  $("again").addEventListener("pointerdown", (e) => { if (e.target === $("again")) agClose(); });
  document.addEventListener("keydown", (e) => { if (!$("again").classList.contains("show")) return; if (e.key === "Escape") agClose(); else if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) $("agGo").click(); });
  $("agGo").addEventListener("click", () => {
    const prompt = $("agPrompt").value.trim();
    if (!prompt) return $("agPrompt").focus();
    const m = SP.modelById($("agModel").value), job = agJob;
    say($("agMsg"), "Sending…");
    chrome.runtime.sendMessage({ type: "fst-spice-run", image: agUrl, thumb: agUrl, prompt, model: m.id, size: $("agSize").value, n: m.n ? +$("agN").value : 1, aspect: SP.nearestAspect(agAr), ar: agAr,
      src: { id: "", fromJob: job.id, title: "Spice again: " + String(job.prompt || "").slice(0, 120), projectId: (job.src && job.src.projectId) || "" } }, (r) => {
      if (chrome.runtime.lastError || !r || !r.ok) return say($("agMsg"), "🌶 " + ((r && r.reason) || (chrome.runtime.lastError && chrome.runtime.lastError.message) || "Spice failed"), "err");
      agClose();
      renderJobs._flashed = false; location.hash = r.jobId;   // the new job appears at the top; scroll to it
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  });

  async function removeJob(id) { const jobs = (await get(SP.JOBS_KEY)) || []; await set(SP.JOBS_KEY, jobs.filter((j) => j.id !== id)); }
  chrome.storage.onChanged.addListener((ch, area) => { if (area === "local" && ch[SP.JOBS_KEY]) renderJobs(); });

  load(); renderJobs();
})();
