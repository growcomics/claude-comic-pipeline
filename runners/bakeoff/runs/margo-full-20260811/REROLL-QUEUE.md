# margo-full — regeneration queue

## STATUS 2026-08-23: CLEARED. 86/86 banked, all known defects corrected.

The 2026-08-16 four-strip QA sweep found 22 defective banked panels. 21 were re-rolled and
re-banked in the 2026-08-23 corrective pass; 1 was a false positive. See CHANGELOG 2026-08-23.

### Replaced (21)
- **Phantom lab coat, act one (15):** b02, b03b, b04, b05, b07, b08, b09, b10, b12, b13, b14,
  b14b, b15, b16, b17. b13/b14/b14b/b15 additionally strained/split the wrong garment (coat
  sleeve rather than the tank's shoulder seam) — the tank-strain arc is now continuous into b18+.
- **Garment strain leaking onto non-Margo cast (3):** b42 (Dev's polo), b47, b55 (Harlan).
- **Headcount + cropped face (2):** b70 (was 5 figures vs 4), b74 (was 6 vs 5). Both re-rolled at
  12 variants against a strict CAST COUNT clause; b74 also got the finale payoff treatment.
- **Lettering (1):** b34b — SFX was baked onto Margo's torso, now floats off-body.

### False positive — NOT changed (1)
- **b26-margo-watches.** Flagged as rendering a spoken line in a thought bubble. The script
  specifies `"type": "thought"` for that line; the panel matches spec.

### Open / next
- **Investor wardrobe has no canonical text.** Harlan, Dev and Ingrid are pinned only by a shared
  reference image, so Harlan reads as a maroon polo in b74 and a dark suit in b47/b55. Give each
  investor an explicit wardrobe line the way Kress has ("navy tracksuit, gold chain").
- **b47's winner has Kress in a suit rather than his tracksuit.** Its actual defect (torn sleeves)
  is fixed, but two full re-rolls never paired a silver-haired Kress with the navy tracksuit —
  wardrobe and identity kept trading off. Worth one more pass once the investors are pinned.

## Standing generation rules (owner-set)
- nano_banana_2_lite, 3:4 (b23 = 16:9), ONE count=4 call per roll, never sequential count=1.
- Judge with kill rules 1-9 (9 = flat face), plus: no lab coat on Margo, no torn/strained garment
  on any non-Margo character, headcount must equal the beat's `chars` list.
- **Wardrobe grading is a Sonnet-tier read.** A Haiku triage pass called the coat-wearing b02
  winner "correct grey tank top, bare arms". Haiku is fine for coarse triage, not for wardrobe.
- **After editing any beat's `fullPrompt`, run `python3 makeplans.py <beat>`.** The driver reads
  `plan/<beat>.json`, not the beatsheet — an un-regenerated plan silently rolls the stale prompt.
