// Compare board — renders the payload flow-bakeoff.js stashed in chrome.storage, and
// (on demand) measures what actually differs between the models.
//
// Images can't be loaded straight into <img>: Flow's media URL 302s cross-origin to the
// CDN and needs the logged-in session, so we ask the service worker to fetch each one
// and hand back a data URL (the same worker-side path Download/→Studio already use).
// Lazy, via IntersectionObserver, so a project with hundreds of generations doesn't try
// to inline them all at once. Fetched images are cached here so the analyser can reuse
// them instead of pulling everything twice.
(async () => {
  const out = document.getElementById("out"), meta = document.getElementById("meta");
  const lb = document.getElementById("lb"), lbImg = lb.querySelector("img");
  const analyzeBtn = document.getElementById("analyze"), verdict = document.getElementById("verdict");
  lb.addEventListener("click", () => (lb.style.display = "none"));

  const { bakeoffCompare: data } = await chrome.storage.local.get("bakeoffCompare");
  if (!data) { out.innerHTML = '<div class="empty">No comparison data — open a Flow project and hit <b>📊 Compare</b> in the panel.</div>'; meta.textContent = ""; return; }
  if (data.error) { out.innerHTML = '<div class="empty">' + data.error + "</div>"; meta.textContent = ""; return; }

  meta.textContent = data.project + " · " + data.rows.length + " of " + data.totalPrompts + " prompts ran on 2+ models";

  if (!data.rows.length) {
    out.innerHTML = '<div class="empty">Nothing to compare yet.<br>Turn <b>🔬 Bake-off</b> ON in the panel, then generate — each prompt will run on every model you ticked and show up here.</div>';
    return;
  }
  analyzeBtn.style.display = "inline-block";

  // ---- image loading (shared by the board and the analyser) ----
  const cache = new Map();
  async function grab(url) {
    if (cache.has(url)) return cache.get(url);
    const p = chrome.runtime.sendMessage({ type: "bakeoffImage", url })
      .then((r) => (r && r.ok ? r.dataUrl : null))
      .catch(() => null);
    cache.set(url, p);
    return p;
  }

  const io = new IntersectionObserver((entries) => {
    entries.forEach((e) => { if (e.isIntersecting) { io.unobserve(e.target); fill(e.target); } });
  }, { rootMargin: "300px" });

  async function fill(el) {
    const dataUrl = await grab(el.dataset.src);
    if (!dataUrl) { el.classList.add("ph"); return; }
    const img = new Image();
    img.src = dataUrl;
    img.alt = el.dataset.model;
    img.addEventListener("click", () => { lbImg.src = dataUrl; lb.style.display = "flex"; });
    el.replaceWith(img);
  }

  // Only prompts that genuinely overflow get the fade + expand affordance.
  //
  // Measuring once, inline, is not enough: if the page is laid out at zero width (a
  // background/offscreen tab), every prompt measures as overflowing and they all end up
  // permanently faded. Re-wrapping on a window resize or a webfont swap changes the
  // answer too. So re-measure from every signal available — a ResizeObserver where it's
  // delivered, plus rAF / resize / fonts.ready as backstops, since a starved observer
  // alone would leave the board stuck on its first guess.
  const prompts = [];
  const measure = (el) => {
    if (el.classList.contains("open")) return;
    el.classList.toggle("clip", el.scrollHeight > el.clientHeight + 2);
  };
  const measureAll = () => prompts.forEach(measure);
  let clipObserver = null;
  try { clipObserver = new ResizeObserver((es) => es.forEach((e) => measure(e.target))); } catch (e) {}

  const cols = data.columns;
  const rowEls = [];
  data.rows.forEach((r) => {
    const row = document.createElement("div");
    row.className = "row";

    const p = document.createElement("div");
    p.className = "prompt";
    p.textContent = r.prompt;
    p.addEventListener("click", () => { if (p.classList.contains("clip")) p.classList.toggle("open"); });
    row.appendChild(p);
    prompts.push(p);
    if (clipObserver) clipObserver.observe(p);

    const grid = document.createElement("div");
    grid.className = "cols";
    grid.style.setProperty("--n", cols.length);
    const statEls = {};
    cols.forEach((label) => {
      const urls = r.byModel[label] || [];
      const col = document.createElement("div");
      col.className = "col" + (urls.length ? "" : " miss");
      const h = document.createElement("h3");
      h.textContent = label + (urls.length ? " · " + urls.length : "");
      col.appendChild(h);
      const st = document.createElement("div");
      st.className = "stats";
      col.appendChild(st);
      statEls[label] = st;
      if (!urls.length) {
        const n = document.createElement("div");
        n.className = "none"; n.textContent = "— not run —";
        col.appendChild(n);
      } else {
        const strip = document.createElement("div");
        strip.className = "strip";
        urls.forEach((u) => {
          const ph = document.createElement("div");
          ph.className = "ph";
          ph.dataset.src = u; ph.dataset.model = label;
          strip.appendChild(ph);
          io.observe(ph);
        });
        col.appendChild(strip);
      }
      grid.appendChild(col);
    });
    row.appendChild(grid);
    out.appendChild(row);
    rowEls.push({ r, statEls });
  });

  requestAnimationFrame(() => requestAnimationFrame(measureAll));
  addEventListener("resize", measureAll);
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(measureAll).catch(() => {});

  // ============================ ANALYSIS ============================
  // What separates these models on YOUR panels, measured rather than guessed.
  //
  // Every metric is computed on the decoded pixels at a fixed working width, so the
  // numbers are comparable even when models return different native resolutions —
  // otherwise "more detail" would just be "more pixels".
  const WORK = 384;

  // Metrics chosen because they map onto things that matter in a comic panel:
  //  detail    — MEDIAN local gradient: how much dense fine texture (skin, hair, weave)
  //  acutance  — 90th-percentile gradient: strength of the real edges
  //  noise     — energy that survives nowhere but single pixels: grain / compression junk
  //  contrast  — luminance standard deviation: tonal separation / punch
  //  saturation— mean(max-min) over RGB: colour intensity
  //  clipped   — % pixels crushed to black or blown to white: lost highlight/shadow info
  //
  // Detail and acutance are measured on a BLURRED copy, and as percentiles rather than
  // means, on purpose. A plain mean-|Laplacian| sharpness score is dominated by isolated
  // single-pixel spikes, so a noisy or heavily-clipped image scores as the most
  // "detailed" one — verified against a harness where the deliberately softest image won
  // detail 3/3 before this fix. Real texture is DENSE (the median sees it); noise is
  // SPARSE (the median ignores it), and what noise there is gets reported on its own.
  const METRICS = [
    { key: "detail",     label: "Detail",     hint: "dense fine texture — skin, hair, fabric weave (noise-robust median)", better: "high" },
    { key: "acutance",   label: "Edge crisp", hint: "strength of real edges (is it soft/smeary?)",        better: "high" },
    { key: "noise",      label: "Noise",      hint: "grain / compression artefacts — lower is better",    better: "low" },
    { key: "contrast",   label: "Contrast",   hint: "tonal separation / punch",                           better: "high" },
    { key: "saturation", label: "Colour",     hint: "colour intensity",                                   better: "high" },
    { key: "clipped",    label: "Clipping",   hint: "% pixels crushed black or blown white — lower is better", better: "low" },
  ];

  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d", { willReadFrequently: true });

  function measureImage(img) {
    const scale = WORK / Math.max(img.naturalWidth, 1);
    const w = Math.max(8, Math.round(img.naturalWidth * scale));
    const h = Math.max(8, Math.round(img.naturalHeight * scale));
    canvas.width = w; canvas.height = h;
    ctx.drawImage(img, 0, 0, w, h);
    const d = ctx.getImageData(0, 0, w, h).data;

    const lum = new Float32Array(w * h);
    let satSum = 0, clip = 0;
    for (let i = 0, p = 0; i < d.length; i += 4, p++) {
      const r = d[i], g = d[i + 1], b = d[i + 2];
      const L = 0.299 * r + 0.587 * g + 0.114 * b;
      lum[p] = L;
      satSum += Math.max(r, g, b) - Math.min(r, g, b);
      if (L < 4 || L > 251) clip++;
    }
    let mean = 0;
    for (let p = 0; p < lum.length; p++) mean += lum[p];
    mean /= lum.length;
    let varSum = 0;
    for (let p = 0; p < lum.length; p++) { const dv = lum[p] - mean; varSum += dv * dv; }

    // 3×3 MEDIAN filter, not a box blur. A blur doesn't remove salt-and-pepper spikes,
    // it SMEARS each one across its neighbourhood — turning sparse noise into dense
    // mid-frequency texture that then reads as "detail". (Verified: with a box blur the
    // deliberately softest, most-clipped image still won detail 3/3.) A median discards
    // impulse outliers outright, so what survives is real structure — and the residual
    // between the original and the median IS the impulse-noise estimate.
    const sm = new Float32Array(w * h);
    const win = new Float32Array(9);
    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        let cnt = 0;
        for (let dy = -1; dy <= 1; dy++) {
          const yy = y + dy; if (yy < 0 || yy >= h) continue;
          for (let dx = -1; dx <= 1; dx++) {
            const xx = x + dx; if (xx < 0 || xx >= w) continue;
            const v = lum[yy * w + xx];
            let j = cnt++;                       // insertion sort, ≤9 elements
            while (j > 0 && win[j - 1] > v) { win[j] = win[j - 1]; j--; }
            win[j] = v;
          }
        }
        sm[y * w + x] = win[cnt >> 1];
      }
    }
    let noiseSum = 0;
    for (let p = 0; p < lum.length; p++) noiseSum += Math.abs(lum[p] - sm[p]);

    // Gradients over the median-filtered copy. Because impulse noise is already gone,
    // a MEAN is now safe and is the right summary for "how much texture is there" — a
    // median gradient is not, because in any detailed image most pixels still sit in flat
    // regions, so the median lands at zero and detailed images score 0. (Seen: with a
    // median gradient the sharpest image scored 0% and the softest 100%.) The histogram
    // is kept for the high percentile, which is what "edge strength" wants.
    const hist = new Uint32Array(256);
    let n = 0, gradSum = 0;
    for (let y = 1; y < h - 1; y++) {
      for (let x = 1; x < w - 1; x++) {
        const p = y * w + x;
        const g = (Math.abs(sm[p] - sm[p + 1]) + Math.abs(sm[p] - sm[p + w])) / 2;
        gradSum += g;
        hist[Math.min(255, Math.round(g))]++; n++;
      }
    }
    const pct = (frac) => {
      if (!n) return 0;
      const want = frac * n;
      let seen = 0;
      for (let i = 0; i < 256; i++) { seen += hist[i]; if (seen >= want) return i; }
      return 255;
    };

    return {
      detail: n ? gradSum / n : 0,   // mean gradient on the de-noised copy = texture density
      acutance: pct(0.9),            // strong-edge percentile
      noise: noiseSum / lum.length,
      contrast: Math.sqrt(varSum / lum.length),
      saturation: satSum / (lum.length),
      clipped: (clip / lum.length) * 100,
      megapixels: (img.naturalWidth * img.naturalHeight) / 1e6,
      native: img.naturalWidth + "×" + img.naturalHeight,
    };
  }

  const decode = (dataUrl) => new Promise((res) => {
    const im = new Image();
    im.onload = () => res(im);
    im.onerror = () => res(null);
    im.src = dataUrl;
  });

  const mean = (a) => (a.length ? a.reduce((x, y) => x + y, 0) / a.length : 0);
  const median = (a) => { if (!a.length) return 0; const s = a.slice().sort((x, y) => x - y); const m = s.length >> 1; return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2; };
  const fmt = (v) => (Math.abs(v) >= 100 ? v.toFixed(0) : Math.abs(v) >= 10 ? v.toFixed(1) : v.toFixed(2));

  async function analyze() {
    analyzeBtn.disabled = true;
    const total = data.rows.reduce((n, r) => n + Object.values(r.byModel).reduce((m, u) => m + u.length, 0), 0);
    let done = 0;

    const perRow = [];           // [{model: {metric: value}}]
    for (const { r, statEls } of rowEls) {
      const rowRes = {};
      for (const label of cols) {
        const urls = r.byModel[label] || [];
        if (!urls.length) continue;
        const shots = [];
        for (const u of urls) {
          analyzeBtn.textContent = "Analysing " + (++done) + "/" + total + "…";
          const du = await grab(u);
          if (!du) continue;
          const im = await decode(du);
          if (im) shots.push(measureImage(im));
        }
        if (!shots.length) continue;
        const agg = { native: shots[0].native };
        METRICS.forEach((m) => (agg[m.key] = mean(shots.map((s) => s[m.key]))));
        agg.megapixels = mean(shots.map((s) => s.megapixels));
        rowRes[label] = agg;
        statEls[label].innerHTML = METRICS.map((m) =>
          '<span class="chip" title="' + m.hint + '">' + m.label + " <b>" + fmt(agg[m.key]) + "</b></span>").join("")
          + '<span class="chip dim">' + agg.native + "</span>";
      }
      perRow.push(rowRes);
    }

    renderVerdict(perRow);
    analyzeBtn.textContent = "🔬 Re-analyse";
    analyzeBtn.disabled = false;
  }

  function renderVerdict(perRow) {
    // Only compare models on prompts where BOTH actually ran — otherwise a model that
    // happened to run on easier prompts would look better than it is.
    const rows = METRICS.map((m) => {
      const wins = {}, ratios = {};
      cols.forEach((c) => { wins[c] = 0; ratios[c] = []; });
      let contested = 0;
      perRow.forEach((rr) => {
        const present = cols.filter((c) => rr[c]);
        if (present.length < 2) return;
        contested++;
        const vals = present.map((c) => ({ c, v: rr[c][m.key] }));
        const best = m.better === "high"
          ? vals.reduce((a, b) => (b.v > a.v ? b : a))
          : vals.reduce((a, b) => (b.v < a.v ? b : a));
        wins[best.c]++;
        // express each model against the row's best, so rows of differing difficulty
        // can be pooled without one bright prompt dominating the average
        vals.forEach(({ c, v }) => { if (best.v > 0) ratios[c].push(m.better === "high" ? v / best.v : best.v / (v || 0.0001)); });
      });
      return { m, wins, ratios, contested };
    });

    const present = cols.filter((c) => perRow.some((rr) => rr[c]));
    let html = '<h2>What actually differs</h2>';
    html += '<table><thead><tr><th>Measure</th>' + present.map((c) => "<th>" + c + "</th>").join("") + "<th>Verdict</th></tr></thead><tbody>";
    rows.forEach(({ m, wins, ratios, contested }) => {
      if (!contested) return;
      const lead = present.reduce((a, b) => (wins[b] > wins[a] ? b : a), present[0]);
      const spread = present.map((c) => median(ratios[c].map((x) => x * 100)));
      const lo = Math.min(...spread), hi = Math.max(...spread);
      const gap = hi > 0 ? Math.round(hi - lo) : 0;
      html += "<tr><td><b>" + m.label + "</b><div class='hint'>" + m.hint + "</div></td>";
      present.forEach((c, i) => {
        const isLead = c === lead;
        html += "<td" + (isLead ? ' class="lead"' : "") + ">" + Math.round(spread[i]) + "%"
              + "<div class='hint'>" + wins[c] + "/" + contested + " wins</div></td>";
      });
      html += "<td>" + (gap < 3
        ? "<span class='tie'>effectively tied</span>"
        : "<b>" + lead + "</b> leads by ~" + gap + "%") + "</td></tr>";
    });
    html += "</tbody></table>";
    html += "<p class='foot'>Each cell is that model's median score as a % of the best model on the same prompt, so prompts of differing difficulty can be pooled fairly. "
         +  "Measured on decoded pixels at a fixed working width, so a model isn't credited for merely returning a larger image — native size is shown separately per column. "
         +  "These are objective signal measurements: they capture softness, texture and tonal punch, but not anatomy, hands, wardrobe fidelity or whether the lettering is legible. Judge those by eye.</p>";
    verdict.innerHTML = html;
    verdict.style.display = "block";
  }

  analyzeBtn.addEventListener("click", analyze);
})();
