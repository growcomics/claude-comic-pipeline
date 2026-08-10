# Credit-burn validation — v2.7.0 lighting schemes + v2.7.1 Drawn prefix

**Date:** 2026-08-09
**Owed by:** `INTEGRATION.md` §5 step 5 (`~/Documents/flow-prompt-lab/lighting/`) and `feedback_validate_with_credits`
**Covers:** c7890a5 (`Light:`/`Render:` selectors + 19 schemes + 💡 Light), 92a203b (✏️ Drawn style prefix)
**Does NOT cover:** c5aed3a (🔎 Detail / ECU) — see *Not run* below.
**Assets:** `docs/posts/assets/2026-08-09-lighting-validation/` (20 images + `index.json` with per-image seed/timestamp)

## Setup

| | |
| --- | --- |
| Account | `marrtrobinson2312@gmail.com` (laptop default, confirmed live before first submit) |
| Flow project | `57409e7f-d6e6-443f-93ae-0cdbae156b12` |
| Model | Nano Banana Pro (`GEM_PIX_2`), 4:3, ×4 per submit |
| Reference | `projects/tmb-daz-study/references/characters/zara/identity-sheet.png` — one ref, media id `74a9bb22`, **identical across all 20** |
| Extension | v2.7.1 as loaded (see *Not run*) |

Five conditions × 4 seeds. The beat, camera, wardrobe, reference, model and aspect were byte-identical across all five; **the lighting block was the only variable.** Control verified from the exported Review manifest, not assumed: one unique ref set, one model, one aspect across all 20 records.

The beat was freehanded rather than composed through `qa/compose.py`. That chain is project-scoped (receipt → audit → bank against a project ledger) and this burn has no project; `INTEGRATION.md` §5 step 5 prescribes exactly this ad-hoc comparison. Flagged rather than silently skipped.

Wardrobe was set to sports bra + shorts in the beat, overriding the ref's hoodie + leggings, so that the abdominal wall, spine trench and thigh/hip split the schemes name are actually visible. Constant across all five conditions, so the comparison holds.

## Verdicts

### 1. Golden v2 does **not** beat v1 — default flipped back to v1

| | v1 | v2 |
| --- | --- | --- |
| Usable panels | 3/4 | 3/4 |
| Clear per-mass terminator staggering | 2/4 | 2/4 |
| Collarbone-notch AO (new in v2) | n/a | faint in **1/4** |
| Calf-split AO (new in v2) | n/a | **0/4** |
| New failure mode | — | `goldenV2-3` renders **cool blue-grey** |

v2's rewrite exists to add two AO locations, tighten terminator placement, and strengthen the anti-glow rim guard. On this evidence it delivers none of the three: the two new AO locations barely render, terminator variation is a wash, and `goldenV2-3` has the most continuous silhouette-hugging rim of any golden image in either arm — the opposite of a stronger guard. It also drifts off-palette entirely, which v1 never does; v1's own failure (`goldenV1-2`, hot rim + crushed shadow) is at least the same lighting family gone wrong.

The single best image across both arms is `goldenV1-4` — also the only golden image of the eight that hits the specified mid-thigh crop.

**Action taken:** `content.js:342` `pbLight` default flipped `"golden"` → `"golden1"`. v1 keeps its 28/28 production record and the default. v2 stays selectable in the dropdown.

> ⚠️ **The flip only affects a fresh install.** `pbLight` is persisted in `chrome.storage.local` and the stored value wins over the default (`content.js:478`). Any browser that has ever touched the `Light:` dropdown will keep its stored scheme. To actually land on v1, pick **Legacy → Golden v1** in the panel once, or clear the key:
> ```js
> chrome.storage.local.remove("pbLight")
> ```

**Caveat:** two of v2's four draws occluded the very anatomy its new claims describe (crossed arms hid the collarbone in `goldenV2-1`; the crop cut the legs out of `goldenV2-2`). Those claims are *unproven*, not *disproven*. A re-run with poses that expose collarbone and calves would be needed to actually settle them — but "unproven after a controlled burn" is not grounds to hold the default against an incumbent with 28/28.

### 2. Venetian Slat — the flagship claim half-lands

The stripes genuinely behave as a measuring instrument **on limbs**: in `slat-2/3/4` bars wrap the bicep cylinder, compress at the waist, re-widen over hip and thigh, and in `slat-3` the floor-plane stripe angle is visibly discontinuous from the body-plane stripes — a clean break-and-displace.

**But across all four seeds the bars cross the chest/sports-bra region as straight, evenly-spaced lines** — precisely what the block's own wording calls "a mistake". That is a repeatable scheme-wide gap, not seed noise. Rim behaviour passed cleanly in all four.

### 3. Overcast Soft — the hardest case, and the most fragile

Only `overcast-2` is unambiguously clean, and it does prove the thesis: volume carried by falloff plus tight contained occlusion, no cast shadows needed. `overcast-3` is a **severe rim failure** — a continuous uniform-width white line tracing the entire silhouette, the exact sticker/aura mode the hard rules forbid. `overcast-4` is milder than first flagged (brighter jaw edge, modest arm contour) and reads marginal rather than failed. `overcast-1` is disqualified on generation-consistency, not lighting: wrong crop, teal bra instead of charcoal, brick-and-wet-floor instead of plain wall.

### 4. ✏️ Drawn prefix — anchor holds, physics doesn't transfer

The painted-comic anchor **holds in all 4**: real ink contours, painted value blocking, brushed backgrounds, no drift back toward photoreal or CGI. That is a clean win for the separate-prefix decision (INTEGRATION.md §6.1) — one render anchor per prompt, and it sticks.

The stripe deformation, however, only fully transfers in `slat-drawn-3`. In `slat-drawn-1` and `-4` the bars ride as straight evenly-spaced diagonals across wall, torso and legs — the same mistake, rendered in ink. The illustration medium appears to make the deformation *harder* for the model to execute, not easier.

## Defects worth registering

1. `overcast-3` — rim-light hard-rule violation, severe (continuous glowing outline).
2. `goldenV1-2` — rim-light violation + crushed-shadow volume loss over ~2/3 of the body.
3. `goldenV2-3` — palette drift: "Golden Rake" rendered cool blue-grey; weakest anti-glow control in either golden arm.
4. `slat-*` (all 4) — bars never deform over the chest/bra region. Pattern, not a one-off. Candidate wording fix to the slat block.
5. `slat-1`, `overcast-3` — both landed on a back-three-quarter camera despite "torso three-quarters to camera", in two unrelated lighting conditions. Likely base-beat camera adherence, independent of the lighting blocks.
6. `overcast-1` — wardrobe and environment drift under an identical beat.

## Strongest image per condition

| Condition | Winner | Runner-up |
| --- | --- | --- |
| Golden v1 | `goldenV1-4` | `goldenV1-3` |
| Golden v2 | `goldenV2-4` | `goldenV2-1` |
| Venetian Slat | `slat-3` | `slat-4` |
| Overcast Soft | `overcast-2` | `overcast-4` (rim caveat) |
| Slat / Drawn | `slat-drawn-3` | `slat-drawn-2` |

## Not run

**🔎 Detail / ECU (c5aed3a, v2.7.2) is still unvalidated.** The extension loaded in the browser was **v2.7.1** — `flow-lighting.js` was present and all 20 `Light:` options worked, but the panel exposed no `detail` button (`director, cine, frame, light, staging, sheet, daz, drawn`), confirmed after a hard page reload. The unpacked extension needs reloading at `chrome://extensions` before Lane 2 (true-macro-ECU check, rim-as-lit-edge check, and the bokeh ÷ "no added blur" reconciliation when 🔎 Detail is stacked with 💡 Light) can run. That burn is still owed.

## Method

Judged by a fresh-context subagent against `skills/comic-production/references/qa-checklist.md` and `cinematic-framing.md`, passed by path and read verbatim, per `feedback_audit_via_subagent`. Note both `CLAUDE.md` and `INTEGRATION.md` cite these as `skills/continuity-check/qa-checklist.md` + `cinematic-framing.md`; **neither file exists at that path** — they live under `skills/comic-production/references/`. The stale pointer should be corrected wherever it appears.
