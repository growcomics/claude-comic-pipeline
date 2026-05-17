# Plan — Extend L29 to tiers 7, 8, 9 (post-peak reinforcement refs)

**Date authored**: 2026-05-16
**Status**: Plan only — no generations yet
**Owner**: TBD
**Triggers**: When the pipeline needs to ship comics escalating past tier 6 (the `muscle-size-lineup-4-9.png` range). Tier-6 reinforcement (L29) is already wired; tiers 7-9 currently fall back to lineup-only and inherit the same under-rendering failure mode that L29 fixed at tier 6.

---

## Why this is needed

L29 fires strictly on `muscle_size_tier == 6` because the two ingested reference sheets were generated and annotated specifically for the figure-6 anatomical target. Applying them at tier 7+ would *under-anchor* — tier 7 is "beyond peak" per the L11 build descriptors and tier 9 is "maximum cartoony FMG." A tier-7 panel attaching the tier-6 sheets would tell the model to render at tier-6 mass while the prompt declares tier 7, producing an unresolved tension that the model splits the difference on.

The fix mirrors L29: a dedicated reinforcement sheet per tier, isolating that tier's proportions as a single-figure anchor, attached alongside the multi-figure `muscle-size-lineup-4-9.png` chart.

## Generation recipe (per tier)

The user provided the canonical prompt recipe used to produce the existing tier-6 sheets. Five distinct prompts per tier:

1. **`Generate a sheet that is used to show all the different muscle and breast sizes of this character`** — anchor sheet showing tier variations (or, at tiers 7-9 specifically, the single figure with annotated proportion stats; the tier-6-full-body.png follows this shape).
2. **`Zoom in on the biceps`** — bicep close-up with anatomical labels (coracobrachialis, brachialis, etc. visible on the existing tier-6-anatomical-detail.png).
3. **`Zoom in on the breast`** — breast volume + shape detail view.
4. **`Zoom in and take note how narrow the waist is`** — waist proportion close-up with metric annotations.
5. **`give a rear view`** — full posterior musculature view (trapezius, glutes, hamstrings, calves visible).

**Per-prompt batch size: 8 generations, pick the best one.** This is the user-specified bar — single renders don't have enough signal, and the reinforcement sheets are load-bearing for every downstream tier-N panel forever, so it's worth the credit burn to land a strong pick.

The two ingested tier-6 sheets compose these five prompts into two final assets:

- **`tier-N-full-body.png`** ≈ prompt 1 + prompt 5 (front sheet + rear view side-by-side, with proportion-stat annotations from prompts 3 and 4 if present)
- **`tier-N-anatomical-detail.png`** ≈ prompts 2 + 3 + 4 + 5 (multi-zoom composite)

Reuse this composition for tiers 7, 8, 9 so the file shape stays consistent with tier 6.

## Per-tier targets

Pull from `_BUILD_BY_TIER` in [`l11_muscular_build.py`](../../skills/comic-production/rules/l11_muscular_build.py) — the build descriptors are already calibrated:

| Tier | Build target | Real-world analog |
|---|---|---|
| 7 | Beyond peak — proportions exaggerated past realism, frame-filling cartoony FMG muscle mass, biceps approach waist width, every muscle group massively developed with clear striation | superpowered female |
| 8 | Super-peak cartoony FMG — deltoids dwarf the head, biceps wider than the waist, pure comic-fantasy proportions with maximal muscle volume | full FMG fantasy |
| 9 | Maximum cartoony FMG — pure FMG-comic exaggeration, near-total muscle dominance over the frame, every muscle group at maximal volume and definition | maximum cartoony |

The breast-scale per tier follows the same progression — figure 9's breasts should read as visibly larger, fuller, and more forward-projected than figure 6's (per the breast-scale anchoring work in L11 Alignment Diff #3).

## Generation parameters

- **Model**: `nano_banana_flash` (per `feedback_higgsfield_model_flash` — same model used for the tier-6 sheets).
- **Resolution**: `1k` default (per `feedback_higgsfield_resolution`). Bump to `2k` only if the 1k pick has insufficient anatomical detail to be useful as a reinforcement ref.
- **Count**: `1` per submit (per `feedback_higgsfield_count_one`); 8 submits per prompt totals 8 candidates.
- **Aspect ratio**: `3:4` for the full-body sheets; `1:1` for the zoom shots; `16:9` for the multi-panel composite if compositing in a final pass.
- **Reference attached for stylistic continuity**: the tier-6-full-body.png as a STYLE reference (annotated-anatomical-sheet visual register), per the L11 surgical-scoping pattern — borrow style only, not proportions (which are the tier-specific delta).

## Per-tier credit budget

5 prompts × 8 candidates × 3 tiers = 120 generations. At ~10-15 credits per nano_banana_flash 1k generation, budget ~1200-1800 credits. The user has 2471 available; comfortable headroom.

The validation gen for L29 (this sitting) is the upper-bound reference for cost — adjust the tier-7/8/9 budget based on what that actually burns per gen.

## Code wiring (after refs are picked + ingested)

### Rule modules

Three options:

1. **One module per tier** (`l30_tier7_reinforcement.py`, `l31_tier8_reinforcement.py`, `l32_tier9_reinforcement.py`). Mirrors L29's structure exactly. Each fires on its own `tier == N` condition. Verbose but clear.

2. **Single module covering tiers 7-9** with per-tier dispatch (`l30_post_peak_reinforcement.py`). One rule, multiple ref-attach decisions inside. Less code duplication; harder to delete or revise one tier independently.

3. **Generalize L29 to tier ≥ 6** with a per-tier ref folder lookup. Most DRY; ties all peak-tier reinforcement into one rule. Riskiest because the anatomical detail is tier-specific and the surgical-scoping language has to remain calibrated.

**Recommendation: option 1.** Each tier's reinforcement sheets have distinct calibration; one-module-per-tier preserves the L29 pattern, keeps the audit trail per-tier, and matches how L11 declares each tier as a discrete `_BUILD_BY_TIER` entry rather than a single function.

### Attachment helpers

Mirror `find_tier6_reinforcement_refs(root)` and `should_attach_tier6_reinforcement(panel)`. Either rename to `find_peak_reinforcement_refs(root, tier)` accepting a tier parameter, or copy-paste per tier. Likely the parameterized form is cleaner since the path is `peak-body-scale/tier-{N}/{tier-N-full-body,tier-N-anatomical-detail}.png`.

### `build_plan` ref attachment

Extend the existing tier-6 block to dispatch on tier and attach the appropriate sheets. Update the ref-ceiling counter to include the tier-N reinforcement count (already factored for tier 6).

### `compose_prompt` slot dispatch

Add `_apply_rule_at_slot("L30", "8b_tier_reinforcement", ...)`, etc. — same slot, same position right after L11's `8_tier_build`. Multiple rules can occupy one slot in the registry order (per `_registry.iter_rules_for_slot`).

### Manifest schema

Extend `body_tiers[].tier6_reinforcement_required` to a more general field. Options:

- `tier_reinforcement_required: <tier_int>` — explicit which tier's sheets to attach.
- `peak_reinforcement_required: true` and let the panel-renderer pick based on `tier`.

Either is fine; the first is more explicit. Update [`script-breakdown/SKILL.md`](../../skills/script-breakdown/SKILL.md) and [`reference-gathering/SKILL.md`](../../skills/reference-gathering/SKILL.md).

### Audit gates

Mirror `_has_tier6_reinforcement_refs` for the new tiers. Same HARD severity, same per-panel and manifest-level checks.

## Open decisions for the user

1. **Source character for the tier-7/8/9 ref generations.** The tier-6 sheets appear to use a generic "default" anatomical model. Want to use the same generic model for consistency, or anchor on Chun Li / Mira since those are the active arc characters?

2. **Annotation style.** The existing tier-6 sheets have inline annotations ("Proportion Stats", "Bicep Profile Focus", anatomical labels like "Coracobrachialis"). Should tier-7/8/9 keep the same labeling, simplify (just figure + tier number), or escalate (more annotations as the proportions get more cartoony)?

3. **Single-figure or multi-figure variant sheet.** The user's prompt 1 says "all the different muscle and breast sizes of this character" — that suggests a multi-figure progression chart. The existing tier-6 sheets are single-figure (one body, multiple views/zooms). Which shape do tiers 7-9 want?

4. **Pick procedure.** "Pick the best one" of 8 — user-driven manual pick (preferred for first run) or auto-pick via a Claude vision rubric (faster but lower quality bar)?

5. **Validation rendering after ingest.** L29 ships with a validation pass (this sitting). Tier-7/8/9 will need the same — render a tier-N comic panel with full ref stack, see what comes out, document. Budget for that on top of the ingest gens.

## Sequencing

1. User answers the 5 open decisions above.
2. Generate the 120 candidates (8 × 5 prompts × 3 tiers). Batch the gens — Higgsfield handles parallel submits cleanly.
3. User (or vision rubric) picks 1 of 8 per prompt → 15 picked images.
4. Composite picks into 2 PNGs per tier (full-body + anatomical-detail), matching the tier-6 file shape.
5. Ingest into `skills/comic-production/references/peak-body-scale/tier-{7,8,9}/`.
6. Wire L30/L31/L32 rule modules + helpers + registry + audit gates.
7. Validation pass — render tier-7/8/9 panels through the full L11 + LNN stack, verify proportions land correctly.
8. Document results + CHANGELOG entry + commit + push.

## Where this does NOT apply

Tier 1-5 (L11 lineup handles these fine — only tier 6+ has the multi-figure interpolation failure). Non-FMG transformations (BE, glute, MMG genres would need their own reinforcement scheme, not piggy-back on the FMG tier-N pattern).
