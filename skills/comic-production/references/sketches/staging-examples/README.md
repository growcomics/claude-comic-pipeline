# Subject staging examples — L34 canonical reference figures

8 generated examples demonstrating L34's subject-staging principles applied to FMG-genre subjects (lead character "Vera", peak tier 8 — heavily muscled with large bust, full glutes, narrow waist, beautiful sculpted face). Each image is the visual reference for one staging value in `cinematic-framing.md` § Subject staging — L34.

Generated 2026-05-25 via Higgsfield `nano_banana_pro` at 16:9, ~$0.40 total (8 generations).

| File | Staging value | Lesson |
|---|---|---|
| `01-tension-good.png` | `tension-block` ✓ | Two characters foreheads-touching along a diagonal axis; lead foreground dominant; bodies thrust into each other; intent angle creates frame energy |
| `02-static-bad.jpeg` | (anti-pattern) ✗ | Same two characters parallel to camera plane with empty horizontal space between them; symmetric, balanced, DEAD |
| `03-zdepth-good.jpeg` | `depth-staged` ✓ | Lead massive foreground left at ~60% frame height; secondary deep background through architecture at ~20% frame height; three depth layers; dominance via scale contrast |
| `04-flat-bad.jpeg` | (anti-pattern) ✗ | Same two characters on identical Z-plane at similar scale; reads as yearbook photo |
| `05-triangular-good.jpeg` | `triangular` ✓ | Lead at apex (foreground, largest); two supporting characters at lower base points at varied depths/scales; pyramidal composition; lead unambiguously THE focal subject |
| `06-lineup-bad.jpeg` | (anti-pattern) ✗ | Three characters in a horizontal row at equal scale and depth; police-lineup parade-formation |
| `07-negative-space-good.jpeg` | `negative-space-asymmetric` ✓ | Lead occupies lower-right third; upper-left two thirds dominated by empty space + single light shaft; mass amplified by void contrast |
| `08-fg-occlusion-good.jpeg` | `foreground-occlusion` ✓ | Camera shoots past an out-of-focus barbell in lower-left FG; lead sharp in midground framed by the FG element; layered depth + intimate-witness energy |

## How to cite these in prompts

`next_panel.py` `_l34_staging_directive()` auto-injects the canonical prompt fragment for whichever `subject_staging` value the shotlist declares. The fragments and the lessons are in `cinematic-framing.md` § Subject staging fragments (L34). These reference images are the *visual* canonical examples to compare generated output against during QA.

## How to regenerate

If you want to refresh the canonical examples (different lead, different setting), the prompts are in cinematic-framing.md § "Subject staging fragments (L34)". Generate at 16:9 with `nano_banana_pro` for consistency with the rest of the pipeline.

## Related

- `lessons-learned.md` § L34 — the rule itself
- `cinematic-framing.md` § Subject staging — L34 — the operator reference + prompt fragments
- `composition-reading-list.md` — annotated source bibliography (Wally Wood, Mateu-Mestre, Eisner, Mascelli, Block, Zhou, McCaig)
- `rules_audit.py` `check_subject_staging()` — the audit gate
