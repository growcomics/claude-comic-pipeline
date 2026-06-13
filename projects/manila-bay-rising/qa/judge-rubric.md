# Post-flight judge rubric (LAYER 4)

The judge is a **fresh-context subagent** — never the agent that composed or submitted.
The generator never grades its own work.

## Spawn inputs
Give the subagent: (1) the downloaded variant image paths, (2) the job's receipt JSON,
(3) the on-disk paths of every reference the receipt says was attached (face card,
turnaround, scene rung, prior panel, anchor where applicable), (4) this rubric verbatim,
(5) if available, the post-submit metadata screenshot showing the attached-ref chips.

## Output
Write `qa/receipts/<job>.verdict.json`:
```json
{"pass": true|false, "tags": ["size", "ward"], "reasons": ["..."], "variant_ranking": ["<uuid-best>", "..."]}
```
`tags` use the defect-registry keys (the Red-Pen vocabulary). `pass` is true only if at
least one variant passes EVERY check; that variant must be ranked first.

## Bias — calibrated against the user
**When uncertain, FAIL.** Calibration exemplar: the agent passed T9 card `270c06dc` as
matching the size anchor; the user's verdict was "so so so so so smaller." On size
especially, judge by LITERAL side-by-side comparison at matched scale, never by
impression. Be harsher than feels natural.

## Checks (against the actual attached reference images, not the prompt's words)
1. **Identity (refs)** — face matches the face card; hair matches. Open the images side by side.
2. **Wardrobe (ward, D4)** — outfit identical to the attached turnaround's state: same garments, same colors, same damage. Any color/emblem drift = FAIL.
3. **Size (size, D6/D14)** — muscle volume matches the attached turnaround/anchor on the four axes (arm-vs-head width, deltoid breadth, chest-shelf depth, mass fraction). Under on ANY axis = FAIL.
4. **Height (height, D7)** — relative heights match height-chart.json; muscle mass never adds height. Giantess or shrinkage vs other characters/props = FAIL.
5. **Camera (angle, D3)** — framing matches the receipt's camera spec (distance class + angle). Default-front-facing when the spec says otherwise = FAIL.
6. **Expression (face, D2)** — matches the beat described in the prompt's expression field; flat/neutral when the beat is strain/joy/shock = FAIL.
7. **Scene (scene, D8)** — background consistent with the attached scene rung; invented architecture = FAIL.
8. **Anatomy (anatomy, D13)** — count hands and limbs against the prompt's total-hands line. Any extra/phantom/orphan = FAIL.
9. **Reference bleed (refs)** — any grey mannequin, silhouette figure, grid lines, or model-sheet panel layout visible in a PAGE image = FAIL.
10. **VFX (vfx, D10)** — effects must read as DAZ store props + postwork per the style bible; physically-accurate/volumetric/AI-perfect looks = FAIL.
11. **Progressive pages** — stages strictly monotonic (size and damage only increase left→right), identical camera/distance/lighting across stages, final stage matches the attached turnaround's state, earlier stages show less. Any reversion = FAIL.
12. **Chip check** — if the metadata screenshot is provided: the attached-ref chips must match the receipt's attach list exactly. Mismatch = FAIL the SUBMIT (not the image): tag `refs`, reason "attached refs differ from receipt".
13. **Style** — photoreal 3D CGI / DAZ Iray look; anything illustrated/anime/2D = FAIL.

## Procedure
Judge each variant independently against all 13 checks before comparing variants.
Report per-variant findings in `reasons`. Never soften a FAIL because other variants
are worse — ranking is separate from passing.
