# QA Defect Doctrine (D1–D13) — user-calibrated, 2026-06-10

Source of truth for *why pages fail* and the **hard gates** that prevent recurrence. Distilled from a
live red-pen session on Not-So-Supra-Man (17 pre-refit pages). Per-project machine-readable registry:
`projects/<project>/qa/defect-registry.json` (regenerates the Flow Red-Pen extension's tags and the
post-flight QA rubric). Prevention is **enforced pre-flight, never guidance-only** — the root failure
was that mandated refs lived in docs and got skipped under time pressure.

## The two laws

1. **Refs own appearance; prompts own action.** A prompt may describe a character's appearance ONLY
   when no reference exists at all (bootstrapping the first card). Once any ref exists: pointer
   language only ("the woman from reference 1"), and EVERY character in frame has face + turnaround
   attached. Anything not pinned by a reference re-samples randomly in every x4 variant (verified:
   4 variants = 4 different outfits / 4 different Supramans).
2. **Prompts are maximal structured specs** (JSON, submitted single-line; template:
   `projects/<project>/qa/prompt-template-v4.json`). The length goes to camera, staging,
   per-limb pose, per-HAND accounting, expression, lighting, continuity — never appearance.

## Defect classes → gates (compact)

| ID | Defect | Hard gate |
|---|---|---|
| D1 | Thin ref stack | Per-panel required-ref manifest; submit blocked if missing |
| D2 | Flat expression | Expression block mandatory on any dialogue/beat panel |
| D3 | Front-facing default | Camera fragment leads the prompt + angle-matched turnaround attached |
| D4 | Outfit probabilistic | Wardrobe-state turnaround must exist before any page in that state |
| D5 | Ref manifest skipped | Page phase cannot start with manifest incomplete (override = logged) |
| D6 | Size normalization | Tier card (+anchor at top tier) attached; over-spec one notch; 4-axis check |
| D7 | Height inflation | `references/height-chart.json` is the only legal height source; turnarounds carry a grey scale-silhouette + grid; size language pairs with "muscle mass increases, height does NOT" |
| D8 | Scene-ref proximity mismatch | Scene refs are a LADDER (wide→medium→close, chained); attach the rung matching the shot's camera distance ("basketball-court rule") |
| D9 | Staging missing | Novel pose/interaction ⇒ staging ref generated, INSPECTED, then consumed |
| D10 | VFX too perfect (AI tell) | Effect language only from `qa/vfx-style-bible.md` (DAZ store-prop + postwork look); "volumetric/cinematic/physically accurate" banned |
| D11 | Appearance in prose | Lint fails prompts containing appearance adjectives for ref'd characters |
| D12 | Prompt underspecified | Completeness lint: per-character position/orientation/per-limb/contact/expression + spatial rules |
| D13 | Phantom limbs | Every hand enumerated with a task + total-hands line + limb-count auto-reject post-flight |

## Aesthetic principle (D10, generalizes)

Target is **"skilled human DAZ artist," not "best possible render."** Store-prop effects: emissive
tube beams (white core + one color sleeve), emissive geoshell skin energy (hard-edged filigree, zoned
not anatomical), 2D billboard starbursts, one uniform postwork bloom, effects that barely light the
scene. Rule of thumb: *if the effect obeys physics it's wrong; if it looks parented-and-airbrushed
it's right.* Full vocabulary: `projects/<project>/qa/vfx-style-bible.md`.

## Review loop

User reviews in Flow via the **Red-Pen extension** (`tools/flow-review-extension/`): hover-tag any
generation with the defect taxonomy, verdicts keyed by media uuid, exported JSON merges into the fix
queue. Planned: post-flight QA subagent emits the same tags blind; calibrate against user verdicts
until agreement ≥85–90%, then it gates acceptance.
