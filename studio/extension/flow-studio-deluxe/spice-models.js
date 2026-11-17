// 3DMC Studio Tools — 🌶 Spice: the Siray image-edit models it offers. Shared by the service worker
// (importScripts), the Spice page (spice.html) and flow-spice.js. Specs: docs.siray.ai/llms.txt →
// api-reference/openapi-spec/<model>.json (all use POST /v1/images/generations/async).
(() => {
  if (self.FOSpice) return;
  // Every Siray "spicy" model that takes an input image (docs.siray.ai/llms.txt, 2026-11-16). Owner: Qwen Image 3 Edit 🌶
  // "is the only model that works", so it stays first = the default. The rest are offered but not yet proven live;
  // the box asks Siray's pricing endpoint first and warns when a model isn't available to the account.
  // MiniMax H3 Edit 🌶 is left out: the first live job on it failed at 34% ("Task failed").
  // kinds: "ar" = size 1k|2k + aspect_ratio (+ n);  "wh" = one exact WIDTHxHEIGHT size, no aspect_ratio (Seedream).
  const WH = {
    "1k": ["1024x1024", "1152x864", "864x1152", "1424x800", "800x1424", "1248x832", "832x1248", "1568x672"],
    "2k": ["2048x2048", "2368x1776", "1776x2368", "2816x1584", "1584x2816", "2496x1664", "1664x2496", "3136x1344"],
  };
  const MODELS = [
    { id: "alibaba/qwen-image-3-edit-spicy", label: "Qwen Image 3 Edit 🌶 (works)", sizes: ["1k", "2k"], n: true, kind: "ar", maxRefs: 3 },
    { id: "alibaba/qwen-image-3-pro-edit-spicy", label: "Qwen Image 3 Pro Edit 🌶", sizes: ["1k", "2k"], n: true, kind: "ar", maxRefs: 3 },
    { id: "bytedance/seedream-5.5-i2i-spicy", label: "Seedream 5.5 🌶", sizes: ["1k", "2k"], n: false, kind: "wh", maxRefs: 10 },
    { id: "bytedance/seedream-5.0-pro-i2i-spicy", label: "Seedream 5.0 Pro 🌶", sizes: ["1k", "2k"], n: false, kind: "wh", maxRefs: 10 },
    { id: "alibaba/wan-2.7-image-pro-i2i-spicy", label: "Wan 2.7 Image Pro 🌶", sizes: ["1k", "2k"], n: true, kind: "ar", maxRefs: 9 },
    { id: "alibaba/wan-2.7-image-i2i-spicy", label: "Wan 2.7 Image 🌶", sizes: ["1k", "2k"], n: true, kind: "ar", maxRefs: 9 },
  ];
  // The WxH of that tier whose shape is closest to the source image's (log distance, like nearestAspect).
  function nearestWH(tier, ar) {
    const list = WH[tier] || WH["2k"];
    if (!(ar > 0)) ar = 1;
    let best = list[0], bd = Infinity;
    for (const s of list) { const [w, h] = s.split("x").map(Number); const d = Math.abs(Math.log(ar) - Math.log(w / h)); if (d < bd) { bd = d; best = s; } }
    return best;
  }
  const ASPECTS = ["1:1", "1:2", "2:1", "1:3", "3:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "9:21", "21:9"];
  // The listed ratio closest to w/h (log distance, so 2:1 and 1:2 are equally far from 1:1).
  function nearestAspect(ar) {
    if (!(ar > 0)) return "1:1";
    let best = "1:1", bd = Infinity;
    for (const a of ASPECTS) { const [x, y] = a.split(":").map(Number); const d = Math.abs(Math.log(ar) - Math.log(x / y)); if (d < bd) { bd = d; best = a; } }
    return best;
  }
  const DEFAULTS = {
    key: "", model: MODELS[0].id, size: "2k", n: 1, lastPrompt: "",
    presets: [
      { name: "Tighter fit", prompt: "Keep the same character, face, pose, framing and art style. Make the outfit tighter and more revealing." },
      { name: "Sultry look", prompt: "Keep everything the same, but give the character a sultry, confident expression and a seductive pose." },
    ],
  };
  const API = "https://api.siray.ai";
  const modelById = (id) => MODELS.find((m) => m.id === id) || MODELS[0];
  self.FOSpice = { MODELS, ASPECTS, DEFAULTS, API, nearestAspect, nearestWH, modelById, CFG_KEY: "fst:spice:cfg", JOBS_KEY: "fst:spice:jobs" };
})();
