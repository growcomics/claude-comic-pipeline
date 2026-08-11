# Vitality gap — automated lane vs owner Flow favorites (2026-08-11)

## CHANGELOG
- **2026-08-11 (later)** — STYLE BLOCK v3 from two fresh owner calibrations on the v2 re-rolls: (1) body scale still under-shoots → aggressive explicit bust/bicep over-spec; (2) new defect class WARD-07 skin-fabric gradient blend → SLEEVES clause + injection rule 6 + stage-A checklist line. Validation burn (b07 + b23 re-rolled with v3) recorded at bottom.
- **2026-08-11** — Initial diagnosis from 3-lens Sonnet analysis (26 owner ⭐ favorites vs 11 bo-autopilot-ab judge winners), prescription table, STYLE BLOCK v2, judge-rubric vitality additions, and validation burn (b07-amulet-flex + b14-margo-steps re-rolled with v2, 4 variants each, nano_banana_2). Validation verdict recorded at bottom.

## The owner's brief (verbatim intent)

> "yours seem dull — the lighting isn't there, the characters' expressions aren't really there, I don't feel the emotion… mine have way more intensity, more close-ups, the muscles are bigger and rounder, chestier and bustier, more ass shots."

Method: SPOTTER MODE. Three Sonnet analysts each viewed BOTH full sets through one lens (lighting/color, expression/pose, body/shot grammar) and returned quantified comparisons. Numbers below are their tallies.

## Diagnosis — what the numbers say

### Lens A — Lighting & color
| Signal | Owner (26) | Lane (11) |
|---|---|---|
| Rim/kicker light present | 24/26 (92%) — and colored (warm-gold or electric-blue) | 4/11 (36%) — neutral white when present |
| Colored practical/FX source | 13/26 (50%) | 1/11 (9%) — lanewin-03's green amulet only |
| Warm-key/cool-fill temperature split | 18/26 (69%) | ~2-3/11 — 8-9/11 are flat single-temperature fluorescent/overcast |
| Glossy specular skin | 26/26 (100%) — full-body oiled sheen | ~6/11 — and only as incidental forehead sweat |
| Subject/bg separation BY LIGHT | ~24/26 (backlight blowout, silhouette, FX glow) | 4/11 — the rest lean on DOF blur, which reads flat |

### Lens B — Expression & pose energy
| Signal | Owner (26) | Lane (11) |
|---|---|---|
| High-intensity face (open mouth + engaged eyes) | ~20/26 | 4/11 |
| Neutral/blank face | ~0 (even quiet beats stay engaged) | 5/11 |
| Body torque / asymmetric stance | nearly every high-energy frame | static frontal-planted dominates |
| Motion-cue stacking (hair + fabric + SFX + energy, ≥2 at once) | nearly every panel from -02 on | 2/11 |
| Strong face undercut by body-less crop | — | 4/11 (face/back-of-head crops hide all pose data) |

### Lens C — Body & shot grammar
| Signal | Owner (26) | Lane (11) |
|---|---|---|
| Enormous / beyond-bodybuilder build | ~19/26, structured as a visible growth ARC | 1/11 (lanewin-10) |
| Chest as the compositional focal point | 16/26 (62%) | 1/11 (9%) |
| Glute / rear-three-quarter emphasis | 7/26, deliberately clustered in the back third | 0/11 |
| Low-angle hero shot | ~10/26 (40%) | 2-3/11 |
| Subject fills ≥70% of frame | 21/26 (81%) | mostly 45-70%; 4/11 are face-only crops |
| Diagonal / depth-layered composition | 24/26 | ~half flat frontal |

## Top-5 root causes (ranked)

1. **"cinematic key light" is a no-op.** The style block's only lighting language has no direction, no contrast spec, no second source, no color temperature — so the model defaults to flat even fluorescent/skylight fill. Owner's look is *defined* by a directional back/side key + a second colored source + high contrast. This is the single biggest visible gap.
2. **No specular-skin spec.** Owner: glossy oiled sheen 26/26. Lane: matte by default. Muscle definition literally disappears without hard speculars; this alone flattens every body shot.
3. **No expression mandate anywhere in the stack.** The style block says nothing about faces; several beat prompts name no emotion; and the stage-B judge scores expression as tiebreaker-only. Net effect: neutral resting faces win. (The lessons file already codifies "name the emotion + expression and pose reflect that" — the lane never enforced it.)
4. **Body scale & framing are conservative.** Refs are athletic-tier and nothing tells the model to over-shoot them (it systematically scales DOWN — owner-defect B23, feedback_chest_oversize_compensate). Combined with zero chest-focal, zero rear-3/4 framing and face-only crops on hero beats, "bigger, rounder, chestier, more ass shots" simply never gets asked for.
5. **The judge selects for safe, not alive.** Stage A removes defects; stage B weights put lighting at #6 and expression dead last, with no floor — so a defect-free flat panel beats a vivid one with any tiny wobble. Defect-avoidance + no vitality floor = systematic dullness selection.

Note: "more intensity" must NOT be implemented as repetition — the owner has flagged their own comics for over-repeating images near the end. Intensity comes from lighting, expression, body scale and framing variety per panel, never from duplicating panels.

## PRESCRIPTION TABLE — dull spec language → alive language

| Layer | Current (dull) | Replacement (alive) |
|---|---|---|
| Style: lighting | "cinematic key light" | "strong DIRECTIONAL key from behind or beside the subject — never flat overhead fill; warm key against cool fill (or cool rim against a warm key); high contrast, deep shadow falloff; rim light tracing the body's edge; background darker than the subject" |
| Style: color sources | *(absent)* | "one saturated practical or FX source per scene coloring the skin (glowing object, window blowout, neon, energy glow)" |
| Style: skin | "physically-based skin … shading" | "+ glossy specular sheen, hard highlights popping on flexed muscle" |
| Style: faces | *(absent)* | "no blank or neutral faces — the emotion named in the prompt renders at full theatrical intensity" |
| Style: bodies | *(absent — refs alone, which the model scales down)* | "delts, pecs, chest and glutes render FULLER and ROUNDER than the reference baseline suggests; the physique fills the frame" |
| Beat prompt: expression | often unnamed (e.g. b02, b03) | EVERY beat names one emotion from the rubric list (strain/awe/ecstasy/rage/determination/panic/smug/…) + "expression and pose reflect that at full intensity" (lessons-learned L-expression) |
| Beat prompt: pose | "steps forward", "flexes one arm" | add torque + amplitude: "torso torqued, shoulders rotated off the hip axis, weight on one leg" / "arm thrown overhead / double-bicep / fist clenched at full flex"; ban "symmetrical frontal stance" on energy beats |
| Beat prompt: lighting state | *(absent)* | per-scene lighting recipe injected as momentary state (L10-compliant): lab = "the amulet's saturated green glow rakes her face and arm, cool rim, dim background"; gym = "hard warm backlight from the high windows haloes hair and shoulders, cool ambient fill" |
| Beat prompt: motion cues | *(absent)* | action/growth beats stack ≥2 kinetic cues: hair swept, fabric straining mid-tear, SFX text, energy glow |
| Shot grammar quotas (sheet-author rule) | full-body/medium default, face-only close-ups | per page: ≥1 low-angle hero, ≥1 rear-three-quarter (glute/back musculature prominent) in act 2+, chest-centered framing on payoff beats, body fills 75-90% of frame on money shots; face-only crops banned on growth/hero beats |
| Judge stage B | lighting #6, expression tiebreaker-only, no floor | add VITALITY GATE (below) |

## STYLE BLOCK v2 — ready to paste as the beatsheet `"style"` string

```json
"style": "Photoreal 3D CGI render, DAZ3D/Iray look, physically-based skin and fabric shading with a glossy specular sheen — hard highlights pop on flexed muscle. LIGHTING: strong DIRECTIONAL key from behind or beside the subject, never flat overhead fill; warm key against cool fill (or cool rim against a warm key); one saturated practical or FX light source coloring the scene; high contrast with deep shadow falloff; a rim light traces the body's edge and the background stays darker than the subject. BODIES: heroically massive and ROUND — delts, pecs, chest and glutes render fuller and rounder than the reference baseline suggests, and the physique fills the frame. FACES: never blank or neutral — the emotion named in the prompt renders at full theatrical intensity. NOT 2D illustration, NOT anime, NOT cartoon. Strictly SFW: every character fully clothed; garments may strain or split at seams but skin itself is NEVER torn or damaged; chest, torso and hips stay covered. No background extras — only the named cast appears. Speech bubbles: clean white 3D bubbles, identical style on every panel."
```

(Everything after "NOT 2D illustration" is unchanged from v1 — the SFW, no-extras and bubble invariants are load-bearing and stay.)

## STYLE BLOCK v3 — supersedes v2 (owner calibrations 2026-08-11 on the v2 re-rolls)

Two fresh owner calls after reviewing the v2 validation set:

1. **Body scale STILL under-shoots.** v2's "fuller and rounder than the reference baseline" improved framing, but the physiques are "still not too big — I never see the huge breasts that are common in what I make." The model scales DOWN whatever is asked (owner-defect B23, `feedback_chest_oversize_compensate`), so polite comparative language ("fuller than baseline") is not enough — v3 over-specs aggressively and EXPLICITLY with concrete anatomical overshoot language.
2. **New defect class — skin-fabric gradient blend (WARD-07).** Flex-in-sleeves beats sometimes render the bicep as bare skin gradienting impossibly into the fabric of the same arm. v3 adds a SLEEVES clause plus per-beat injection rule 6.

**Exact spec lines changed vs v2** (LIGHTING / FACES / tail unchanged):

- BODIES (v2): "heroically massive and ROUND — delts, pecs, chest and glutes render fuller and rounder than the reference baseline suggests, and the physique fills the frame."
- BODIES (v3): "dramatically oversized, far BEYOND the reference baseline — the bust renders dramatically enlarged, well past athletic-realistic proportions, round and heavy; each bicep rivals her head in size when flexed; delts, pecs, chest and glutes carry exaggerated round mass; the physique dominates and fills the frame. Garments visibly strain and split at their seams under the mass, but coverage of chest, torso and hips is always preserved."
- SLEEVES (new in v3): "when a muscle flexes inside a sleeved garment the fabric responds physically — the sleeve seam splits open around the flexed muscle with crisp torn fabric edges, or the sleeve is rolled up with a clean cuff edge; bare skin NEVER blends or gradients into fabric on the same limb."

```json
"style": "Photoreal 3D CGI render, DAZ3D/Iray look, physically-based skin and fabric shading with a glossy specular sheen — hard highlights pop on flexed muscle. LIGHTING: strong DIRECTIONAL key from behind or beside the subject, never flat overhead fill; warm key against cool fill (or cool rim against a warm key); one saturated practical or FX light source coloring the scene; high contrast with deep shadow falloff; a rim light traces the body's edge and the background stays darker than the subject. BODIES: dramatically oversized, far BEYOND the reference baseline — the bust renders dramatically enlarged, well past athletic-realistic proportions, round and heavy; each bicep rivals her head in size when flexed; delts, pecs, chest and glutes carry exaggerated round mass; the physique dominates and fills the frame. Garments visibly strain and split at their seams under the mass, but coverage of chest, torso and hips is always preserved. SLEEVES: when a muscle flexes inside a sleeved garment the fabric responds physically — the sleeve seam splits open around the flexed muscle with crisp torn fabric edges, or the sleeve is rolled up with a clean cuff edge; bare skin NEVER blends or gradients into fabric on the same limb. FACES: never blank or neutral — the emotion named in the prompt renders at full theatrical intensity. NOT 2D illustration, NOT anime, NOT cartoon. Strictly SFW: every character fully clothed; garments may strain or split at seams but skin itself is NEVER torn or damaged; chest, torso and hips stay covered. No background extras — only the named cast appears. Speech bubbles: clean white 3D bubbles, identical style on every panel."
```

**Injection rule 6 (adds to the five per-beat rules below):** any flex-in-sleeves beat MUST state the sleeve behavior explicitly in the beat prompt — legal renderings are only (a) the sleeve visibly tears/splits around the muscle ("the sleeve seam splits open around the flexed bicep, torn fabric edges visible"), (b) sleeve rolled up with a crisp fabric edge, or (c) the garment established as off in a prior transition panel. A skin-to-cloth gradient on one limb is WARD-07, an insta-kill.

## Per-beat injection rules (composer/authoring contract)

1. **Expression injection** — every beat carries a named emotion + "expression and pose reflect that at full intensity". A beatsheet linter should reject beats with no emotion word.
2. **Pose energy injection** — energy/growth/confrontation beats add one torque phrase + one amplitude phrase; "symmetrical frontal standing pose" is a banned default.
3. **Scene lighting recipe** — each location in the sheet declares a 1-sentence recipe (key direction + palette + practical source); the composer injects it into every beat in that location as momentary lighting state. This is L10-compliant: the recipe is the *state*, the env ref stays the architecture anchor.
4. **Motion-cue stacking** — action/growth beats stack ≥2 kinetic cues (hair / straining fabric / SFX lettering / energy glow).
5. **Shot-grammar quotas** — per page: ≥1 low-angle hero, ≥1 rear-three-quarter from act 2 on, chest-focal framing on payoff beats, subject fills 75-90% on money shots, no face-only crops on growth/hero beats. Variety, not repetition: quotas force *different* framings across a page, never duplicated panels.

## Judge rubric addition — stage A checklist line (2026-08-11, WARD-07)

Add to the stage-A defect screen (qascan / rubric-driven defect pass), insta-kill tier:

> **SKIN-FABRIC GRADIENT BLEND (WARD-07)** — on any single limb, check the transition between skin and garment fabric: if bare skin gradients or blends into cloth with NO seam, hem, rolled cuff, or torn fabric edge separating the two materials (typical case: a flexed bicep rendered bare mid-sleeve on a lab coat or sweater), the variant is KILLED. Legal renderings only: sleeve visibly torn/split around the muscle, sleeve rolled up with a crisp edge, or the garment established as off.

## Judge rubric addition — VITALITY GATE (stage B)

Insert before ranking in `runners/bakeoff/judge.py` WEIGHTS:

> **VITALITY GATE — score each surviving variant 0-5 on three axes before ranking: (a) lighting drama (directional key, rim/colored source, contrast — flat even fill = 0-1), (b) expression intensity (rubric AXIS 3 — dead face in an emotional beat = 0-1), (c) frame-fill (share of frame the subject's physique occupies vs the beat's shot spec). A variant scoring 0-1 on ANY axis cannot be declared winner while a variant scoring ≥2 on all three survives. Then rank survivors with the weights below.**

Rationale and an honest caveat: the current weights were calibrated on picks-profile-eva (expression won 0/8 owner picks) — but that comparison was *within* batches that were uniformly generated, i.e. siblings shared the same (flat) lighting and (neutral) faces, so those axes could never discriminate. The 2026-08-10 owner walkthrough (B18 "flat face, flat lighting, not dynamic") and this vitality-gap analysis show they discriminate hard *between* the lane and the owner's standard. The gate adds a floor without disturbing the validated camera-first ranking.

## Validation burn (2026-08-11)

Protocol: b07-amulet-flex and b14-margo-steps re-rolled with STYLE v2 + injections, 4 variants each, Higgsfield nano_banana_2, same identity refs as the original run (margo 408ea3036d, env-lab 966a9f9282, env-gym 55acc4a1db). Fresh Sonnet judge compared each beat's ORIGINAL stage-B winner (r1v2 in both cases) against the 4 new variants on the vitality axes only (all candidates defect-screened). New variants ingested to the autopilot-ab board tagged `style-v2`, **not** accepted — owner side-by-side at https://3dmusclecomics.com/studio/review.php?p=autopilot-ab

**Verdict: v2 WINS DECISIVELY on both beats — no iteration needed.** Fresh Sonnet judge, vitality axes only (lighting drama / expression intensity / pose energy / frame-fill, each 0-5):

| Beat | OLD winner (r1v2) | Best v2 (v2v3) | v2 set vs old |
|---|---|---|---|
| b07-amulet-flex | 2 / 1 / 2 / 1 | 5 / 4 / 4 / 4 | all 4 v2 variants beat the old winner on every axis |
| b14-margo-steps | 2 / 1 / 1 / 1 | 5 / 5 / 4 / 5 | all 4 v2 variants beat the old winner on every axis |

Judge quotes: b07 — *"OLD is technically correct and emotionally inert; v2v3 is the first one in the set that looks like it's happening to someone."* b14 — *"r1v2 isn't underlit determination, it's a different, calmer beat that happened to get picked — every v2 variant, even the weakest, is closer to the script than the old winner is."*

Zero new catastrophic defects (identity holds, no skin-torn-as-fabric, no prop glitches, no fourth-wall gaze). The b14 finding also confirms root cause #5: the old stage-B pick was a brief-miss that survived because nothing scored vitality.

Board files (group Beat 12 = b07, Beat 13 = b14, all tagged `style-v2`, none accepted): 5236c887f4 / e3428b3881 / 1994daa040 / 70f77b42f3 and 55288f8b19 / 890ac5bed6 / 866a2a8936 / ace26720df. Judge's recommended promotions (owner's call): **1994daa040.png** (b07 v2v3) and **866a2a8936.png** (b14 v2v3).

Cost: 8 generations via Higgsfield MCP, model `nano_banana_2` (served as `nano_banana_flash`), 1k, 3:4 — 12 credits total (1.5 per image, balance-verified 5685.06 → 5673.06).

Next steps (not yet applied): paste STYLE v2 into the next beatsheet's `"style"`, add the VITALITY GATE block to `runners/bakeoff/judge.py` WEIGHTS, and adopt the five injection rules in the sheet composer/linter.
