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

## Other open defects (not blocking)
- IDENTITY BLEED, b45-tape: in 3 of 4 tiles the amulet + grey tank bound to INGRID
  instead of Margo, and the coat appeared on Ingrid in 2 of 4. Ref/staging attachment
  issue — fix inputs before re-rolling.
- KRESS TEAR BLEED: Margo's growth-tear effect lands on Kress's tracksuit. Cost 6/8
  tiles in b49-kress-protest, 3/8 in b06, and b04 v02/v03. The global SLEEVES style
  clause is not scoped to Margo or to the stages where she outgrows clothes.
- AMULET-AS-BRACELET: cost 5/7 tiles in b09, killed b12 v06.
- b41-money-lift winner v04 is banked but shows the coat (pre-fix). Re-roll when convenient.
