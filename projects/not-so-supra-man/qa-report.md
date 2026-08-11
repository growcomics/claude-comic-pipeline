# QA Defect Report — "Not So Supra... Man" (46 pages)

Audit date: 2026-06-10. One finished image per page (`pages/panels-hf/pNN-01.png`).
Rubric: `skills/comic-production/references/qa-checklist.md` + `cinematic-framing.md`.
Size truth: `.flow-scratch/anchor-4d81c347.jpg` (tier-9). Agreed benchmark page: `p43-01.png`.

> Note on the anchor: the anchor render itself has RED hair + an S-shield (it is a "Super-Lana Lang" DAZ asset). It is used here for MASS/SIZE parity ONLY — Dana's canonical hair (jet-black bob) and emblem (gold double-chevron) are NOT taken from it.

## Defect table

| page | severity | issue |
|---|---|---|
| p01 | LOW | Supraman rendered hyper-massive (bodybuilder bulk) — violates "athletic, NOT hyper." Dana/Destroya tier sizes OK. |
| p02 | HIGH | Anachronistic gold chevron/insignia on Dana's civilian white blouse — she is a captive reporter pre-transformation, blouse should be plain. |
| p04 | LOW | Faint emblem reads on Dana's blouse (pre-transformation captive — should be plain). |
| p06 | HIGH | Large gold double-chevron emblem on Dana's plain white blouse at tier 2 (bound captive). Should be plain blouse. |
| p07 | HIGH | WRONG LOCATION — scene is a boxing/wrestling ring with ropes, posts, arena seating. Should be doomer-lab (concrete, gantry, ray rig). Binding-ropes conflated with ring-ropes. |
| p08 | LOW | Growth-progressive format correct, but stray gold chevron appears on the white blouse in stage 3 (civilian garment). |
| p09 | LOW | Growth-progressive format correct, but stray gold chevron appears at hip/waist in stage 3 (civilian garment). |
| p10 | HIGH | WRONG LOCATION — outdoor rubble field, should be doomer-lab interior. |
| p12 | HIGH | WRONG LOCATION — outdoor city street in rain, should be doomer-lab interior. |
| p13 | HIGH | WARDROBE TOO EARLY — Dana in the BLUE hero suit + chevron. Page 13 (tier 6) she is still in the torn WHITE blouse; the blue suit does not appear until page 20. |
| p14 | HIGH | WARDROBE TOO EARLY — blue hero suit + cape instead of torn white blouse. |
| p15 | HIGH | WARDROBE TOO EARLY — blue suit/skirt instead of the charcoal pencil skirt remnant. |
| p16 | HIGH | WARDROBE TOO EARLY — Dana in full blue suit (should be torn white-blouse remnants). Also location reads as a city rooftop, should be lab. |
| p17 | HIGH | WARDROBE TOO EARLY — Dana in blue suit; should still be torn-but-covering white remnants (suit-swap is page 20). |
| p18 | LOW | "No characters" cutaway page contains a human figure standing on the rooftop at right — unintended extra. Otherwise correct exterior gag. |
| p20 | HIGH | Compositing artifact — Supraman's reaction is a disembodied FLOATING HEAD in the doorway (no body), instead of a stunned figure. |
| p22 | HIGH | Gold hero chevron on Dee-Dee's (villain scientist) black top under the lab coat. Villains must not bear the hero emblem. |
| p23 | HIGH | Gold hero chevron on Dee-Dee's chest in the beam. Same villain-emblem defect. |
| p24 | HIGH | Gold hero chevron on Destroya's black corset. Destroya's corset is plain black — no chevron. |
| p25 | HIGH | Gold hero chevron on Dee-Dee's top (stages 1–2). Villain-emblem defect. Growth format otherwise correct. |
| p26 | HIGH | Gold hero chevron on Destroya's corset/glute (stage 3). Villain-emblem defect. Growth format otherwise correct. |
| p27 | HIGH | Gold hero chevron on Destroya's wrist cuff / corset. Villain-emblem defect. Implied-violence framing otherwise OK. |
| p29 | LOW | Supraman is barefoot — missing his red boots (wardrobe slip). |
| p30 | HIGH | Scale error — Supraman rendered doll/figurine-sized (~2 ft) cradled against Dana. Tier-6 gap is overshot to near-tier-9; reads as a toy, not a 6 ft man. |
| p31 | HIGH | Gold hero chevron on Destroya's corset. Villain-emblem defect. Rampage shot otherwise strong. |
| p32 | LOW | Likely chevron on Destroya's corset (villain-emblem); hard to confirm at angle. Composition good. |
| p33 | LOW | Chevron on Destroya's corset (villain-emblem defect). |
| p36 | LOW | Chevron on Destroya's corset (villain-emblem defect). |
| p39 | BLOCKER | STYLE DRIFT — page rendered in anime / cel-shaded 2D illustration style (glossy manga shading, painterly energy streaks), NOT photoreal 3D/DAZ3D. Breaks the photoreal mandate and clashes with every adjacent page. Face also off-model. |
| p42 | BLOCKER | PROMPT LITERALIZATION — "cobra back … in full eclipse of the sun" rendered as a LITERAL giant king-cobra snake head (hood, scales, eyes) growing out of Dana's back in stage 3. Grotesque/unusable. (Should be trapezius/lat spread.) |
| p45 | BLOCKER | EMBLEM WRONG — chest emblem is a single stylized "S"/lightning-bolt glyph in a rounded shield, NOT the gold double-chevron delta. Rule-2 violation (no S-shield). Secondary faint emblem malformed. |
| p46 | HIGH | TIER-9 SIZE REGRESSION — final-page Dana reads ~tier 6–7, only modestly larger than Supraman; arms not thicker than her head, bust not colossal. Downsized vs the p43 benchmark and the anchor. (Timmy + camera intentionally present — OK.) |

## Counts by severity

- BLOCKER: 3 (p39, p42, p45)
- HIGH: 22 (p02, p06, p07, p10, p12, p13, p14, p15, p16, p17, p20, p22, p23, p24, p25, p26, p27, p30, p31, p46) — *(20 distinct; see note)*
- LOW: 11 (p01, p04, p08, p09, p18, p29, p32, p33, p36)

(Severity tallies are per-row; some pages carry a single dominant defect. Distinct page counts: 3 BLOCKER, 20 HIGH, 9 LOW.)

## Pages to REGENERATE (BLOCKER + HIGH)

p02, p06, p07, p10, p12, p13, p14, p15, p16, p17, p20, p22, p23, p24, p25, p26, p27, p30, p31, p39, p42, p45, p46

(23 pages.) LOW-only pages (p01, p04, p08, p09, p18, p29, p32, p33, p36) are shippable but should be cleaned in a polish pass if cheap — most are the same stray-chevron issue.

## Systemic patterns (root causes, not per-page)

1. **Stray gold chevron leaking onto the wrong garments** — the hero emblem appears on Dana's pre-transformation civilian blouse (p02, p04, p06, p08, p09) AND on Dee-Dee/Destroya's villain costume (p22–p27, p31, p33, p36). The emblem ref is being attached/applied too broadly. Fix: only attach the chevron emblem ref to Dana's HERO-suit pages (20+) and to Supraman; never to Dana's Act-1 blouse or to any Dee-Dee/Destroya panel.
2. **Wardrobe jumped ~7 pages early** — Dana is in the blue hero suit on p13–p17; canon keeps her in the torn WHITE blouse/charcoal-skirt remnants until the suit-swap reveal on p20. Fix: re-attach the white-blouse/torn-remnant turnaround for p13–p17, not the suit.
3. **Location drift in Act 1** — the doomer-lab interior drifts to a boxing ring (p07), open rubble (p10), and rainy city street (p12). Fix: attach the doomer-lab env ref verbatim on every Act-1 lab page; verbally anchor 5+ lab elements (concrete walls, steel gantry, cable bundles, ray rig, interrogation chair, overhead floods).
4. **Scale/compositing glitches** — floating disembodied head (p20) and toy-scale Supraman (p30). Fix: render Supraman full-figure in-scene; cap the tier-6 size gap so he still reads as a full-grown man.
5. **Prompt-literalization + style breaks on isolated pages** — literal cobra (p42), anime style (p39), S-glyph emblem (p45). These are one-off generation failures, each a hard regenerate.

## Camera Variety check (46-page sequence)

PASS. Distance categories present: 7/8 — medium(11), ecu-region(10), cowboy(7), full(7), mcu(6), wide-establish(4), low-angle-front(1, shotlist typo for p03). Angle categories present: 10/10 — low-angle-front(10), three-quarter(9), eye-level(5), profile(5), worms-eye(5), dutch(4), low-angle-back(3), high-angle(2), over-shoulder(2), birds-eye(1). Max distance×angle combo = 3 (medium-profile, full-low-angle-front, mcu-three-quarter) — within the ≤3 limit. ≥1 ECU and ≥1 wide-establish/splash both satisfied. The spread comfortably clears the rubric's 5-distance / 4-angle / ≤3-combo / ECU+wide thresholds; no camera-static run found. (Minor: p03's `camera` field lists two angles "low-angle-front, dutch" with no distance token — a shotlist data nit, not a render defect.)
