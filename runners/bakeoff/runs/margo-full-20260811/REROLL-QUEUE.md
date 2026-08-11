# margo-full — re-roll queue (as of 2026-08-11 ~08:10)

## Why these exist
The `wardrobe` field was never injected into `fullPrompt` (0/86 beats). The only
clothing signal reaching the model was the `margo` identity reference — a photo of
her IN A LAB COAT. Every beat after b17 (where the story destroys the coat) tended
to render it anyway.

FIXED at source 2026-08-11 ~07:45 (commit 54a511f): every beat prompt now carries a
`WARDROBE (exact ...)` block that explicitly outranks the reference image.
Proof it works: b40 and b43 were 0/4 and 0/7 before the fix; corrective re-rolls came
back 6/6 clean.

**Everything generated BEFORE ~07:45 is suspect. Everything after is clean by default.**

## Zero clean variants — MUST re-roll (7)
- b18-doorframe    — 7/7 lab coat (full garment or torn remnant clinging to the arm)
- b19-crate        — 6/6 lab coat; ALSO none staged the crate-lift-to-shoulder action
- b22-tomorrow     — 8/8 lab coat; v04 also had stray quote marks on the balloon
- b26-margo-watches— 7/7 lab coat
- b48-terms        — 7/7 lab coat
- b52-amulet-blaze — 6/6 lab coat
- b53-quads        — 3/3 lab coat; v03 also swapped leggings for shorts

## Clean wardrobe but WRONG ACTION — re-roll (1)
- b18b-calipers — v07/v08 are coat-free, but NO tile actually shows calipers clamped
  on the bicep. Winner not banked; re-roll for the action.

## How to re-roll
The beat sheet is already fixed, so a plain re-roll from `fullPrompt` should work.
For the stubborn ones add an explicit corrective, as used on b40/b43:
  "CRITICAL FIX: the previous roll dressed MARGO in a white lab coat. There is NO
   lab coat, jacket, cardigan or any white over-garment in this scene — that coat
   was destroyed earlier in the story. She wears the grey tank top ONLY."
Do NOT use registry RETRY_INJECTION WARD-01 here — it says "match the attached
reference images EXACTLY", which is backwards: the reference is the source of the defect.

## FLAT FACES — corrective re-roll (4)
Audited all 42 banked winners on two axes (face intensity, text accuracy).
TEXT: 42/42 clean — every expected line present and correctly spelled. Text is NOT a problem.
FACE: 4 flat. These are banked but should be replaced:
- b02-vial          — exhausted/hopeful reads as neutral
- b07-stay-out      — should be a threat landing; face is slack
- b13-sleeve-tight  — detail shot, but the face in frame is blank
- b50-clipboard-back— "SAYS THE DATA. MY DATA." should be a counterpunch; reads placid

ROOT CAUSE: judging gap, not a prompt gap. Every prompt already carries
"FACES: never blank or neutral - the emotion named in the prompt renders at full
theatrical intensity", but face quality was NOT one of the 8 kill rules, so flat
faces passed as KEEP.

FIX — add as kill rule 9 for every future judge pass:
  9. Flat face - blank, neutral, waxy, doll-like, or a mild expression on a beat
     that calls for something strong. A calm face on a dramatic beat is a KILL.
Corrective clause for the re-roll (mirrors registry FACE-01):
  "CRITICAL FIX: the face was wooden last roll. The named emotion must visibly
   transform the WHOLE face - brows driven, eyes wide or narrowed, mouth open or
   set. Theatrical intensity, not a neutral expression."

## STRUCTURE — resolved, no action
Owner confirmed 2026-08-11: each panel IS its own standalone page/image. 86 beats
= 86 pages. No page-composition/multi-panel-grid step is needed, and the Gribble
4-panel-grid figure does NOT apply to this run. The apparent "only ~20 images"
is simply run progress: 42 of 86 banked.

## Other open defects (not blocking)
- IDENTITY BLEED, b45-tape: in 3 of 4 tiles the amulet + grey tank bound to INGRID
  instead of Margo, and the coat appeared on Ingrid in 2 of 4. Ref/staging attachment
  issue — fix inputs before re-rolling.
- KRESS TEAR BLEED: Margo's growth-tear effect lands on Kress's tracksuit. Cost 6/8
  tiles in b49-kress-protest, 3/8 in b06, and b04 v02/v03. The global SLEEVES style
  clause is not scoped to Margo or to the stages where she outgrows clothes.
- AMULET-AS-BRACELET: cost 5/7 tiles in b09, killed b12 v06.
- b41-money-lift winner v04 is banked but shows the coat (pre-fix). Re-roll when convenient.
