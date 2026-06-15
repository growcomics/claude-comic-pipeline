# Three-Panel Growth Sequences — v4 template

Fuses the legacy growth-sequence doctrine (size benchmarks, per-panel face beats, escalating
effects, "TWO REFERENCES" device, never-shrink rule) with the v4 gates (refs own appearance,
size-chart pinning, per-hand accounting, baked 2D lettering per L19). One image, three equal panels, time
reads in panel order.

## What the legacy doctrine got right (keep forever)

- **Concrete size benchmarks per panel** ("softball → grapefruit → bigger than her head"), not
  adjectives ("toned → ballooning") — adjectives let every variant pick its own scale.
- **Per-panel face beats** when the face is in frame: first sensation → growing shock → peak
  reaction, each specified by brows/eyes/mouth/head, never "surprised" alone.
- **Escalating VISUAL effects**: 1 thin action line → multiple radiating lines → dense burst +
  motion blur + sweat droplets mid-air. Effects grow with the body part.
- **Wardrobe damage escalates monotonically** and is named per panel (tight → seam splitting →
  burst to threads, coverage held).
- **Never-shrink rule** stated inside the prompt ("each panel strictly larger than the last").
- **The size chart as an attached reference** with per-panel woman-numbers — growth = walking the
  chart (#N → #N+1 → #N+2), not vibes.

## v4 corrections to the legacy doctrine

- **No appearance prose** — legacy templates described characters; v4 uses pointer language only
  ("the woman from reference 1"); face card + wardrobe turnaround attached (D11).
- **Baked SFX text (L19)** — SFX is auto-emitted as a flat 2D comic overlay from `sfx[]` and baked
  into the render; check legibility (AI text can garble — re-roll if scrambled). Action lines/motion
  blur stay IN the photoreal render (they're visuals). `page-composer` no longer letters.
- **Per-hand accounting + exactly-N-limbs lines** (D13), **identical camera/lighting/background
  across panels** stated explicitly (only size, damage, expression change), **height clamp** (D7),
  and Flow-filter-safe language on chest/glute pages (neutral anatomy terms, coverage explicit —
  legacy cleavage phrasing trips Flow's filter and burns variants).

## Template (JSON, submit single-line; placeholders in [brackets])

```json
{
  "instruction": "Generate one image.",
  "style": "Photorealistic 3D CGI render, DAZ Studio Iray render-engine look, photoreal CGI comic production still. NOT illustrated, NOT anime, NOT cartoon, NOT 2D.",
  "format": {
    "layout": "ONE image divided into THREE equal vertical panels side by side with thin gutters",
    "reading_order": "left to right = time passing during one continuous growth event",
    "consistency": "same camera position, same distance, same lighting, same background in all three panels — the ONLY changes are [BODY PART] size, clothing damage, and her expression"
  },
  "camera": { "shot": "[medium shot from mid-torso up, face fully visible in EVERY panel | EXTREME CLOSEUP of the [BODY PART] only]", "angle": "[eye-level three-quarter | profile | low-angle]", "lens": "85mm portrait" },
  "references": "Appearance EXACTLY as attached: reference 1 = face card, reference 2 = wardrobe-state turnaround (with height scale guide), reference 3 = SIZE CHART (per-panel scale), reference 4 = previous accepted panel (continuity). No appearance description on purpose — the references own appearance.",
  "panels": [
    { "panel": 1, "size": "[BODY PART] matches SIZE CHART figure #[N] — [concrete object benchmark]", "wardrobe": "[garment] intact but pulling tight, first tension wrinkles", "expression": "first sensation — brows raised, eyes widening, lips parting", "effects": "a single thin action line radiating off the [BODY PART]" },
    { "panel": 2, "size": "[BODY PART] matches SIZE CHART figure #[N+1] — [bigger benchmark]", "wardrobe": "[seam/strap] visibly splitting, threads snapping", "expression": "growing shock — brows fully arched, eyes wide, mouth open in a gasp", "effects": "multiple action lines radiating outward, faint sweat sheen" },
    { "panel": 3, "size": "[BODY PART] matches SIZE CHART figure #[N+2] — [peak benchmark]", "wardrobe": "[garment] burst to hanging threads, ragged edges — coverage of chest/hips fully intact", "expression": "peak exhilaration — head tilted back, mouth fully open, cheeks flushed", "effects": "dense burst of action lines, motion blur on the expanding [BODY PART], sweat droplets mid-air" }
  ],
  "anatomy_rules": [ "exactly one woman in frame", "exactly two arms and two hands — [each hand's task]", "no extra limbs" ],
  "size_rules": [ "growth is strictly monotonic across panels — each panel larger than the previous, never equal, never smaller", "muscle mass increases, her HEIGHT does not change" ],
  "lighting": "[scene lighting] — identical in all three panels",
  "background": "EXACTLY the environment of the attached scene reference rung, softly defocused — identical in all three panels",
  "sfx": "[SFX word(s) for this growth beat, e.g. RRRIP / THROB — baked as flat 2D comic ALL-CAPS overlay per L19, scope-bounded so bodies stay photoreal; one per growth panel]",
  "negative": "not illustrated on the bodies, not cartoon-shaded skin, no extra limbs or hands, no heavy vein networks, no height change, panels must not repeat the same size (the lettering overlay is the only 2D element — keep it via the L19 scope-bounded positive negation, do not ban text globally)"
}
```

**Body-part swaps:** arms (flex pose, sleeve/cuff damage) · abs (hem parting, midriff only) ·
chest (FLOW-SAFE: "muscular chest", "coverage fully intact", knotted-remnant wardrobe — never
cleavage-forward phrasing) · glutes/legs (profile or low-back angle, skirt-to-wrap damage,
boots creaking). Benchmarks ladder: softball → grapefruit → bigger than her head (arms);
flat → four-pack emerging → deep-cut six-pack (abs).
