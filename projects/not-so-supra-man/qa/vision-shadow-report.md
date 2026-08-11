# Vision-Shadow Agreement Report — `not-so-supra-man`

> **ADVISORY SIDECAR.** Nothing in this report gates anything. The shadow reads
> banked state and writes `qa/receipts/*.vision.json` advisory files only; the
> compose→audit→bank→verify chain and its integrity manifest are untouched.

- Generated: 2026-08-11T06:23:01Z  ·  Scope: **45 panels**  ·  Image coverage of banked logs: **100.0%**
- Ground truth: qa-report table: qa-report.md
- Vision side: rubric v3 categories + v5 confidence semantics + face cards (`qa/vision-shadow/rubric.md`, sha256 `a26729df2e1fc7e8…`), detections counted at confidence high+medium.
- Agreement is scored per COMPARISON GROUP (canonical registry IDs bucketed — see `vision_shadow.py group_of_id`); registry IDs are cited per flag in the advisory receipts.

## Headline

- Defective panels (per ground truth): **23** — shadow flagged the SAME defect group on **17** (74%), flagged anything at all on 20.
- Clean panels (per ground truth): **13** — shadow agreed clean on **6** (46%).

## Per-group agreement (ship bar: recall ≥ 80%, precision ≥ 70%, support ≥ 5)

| Group | Support | agree-fail (TP) | vision-only (FP) | subagent-only (FN) | agree-pass (TN) | Recall | Precision | Verdict |
|---|---|---|---|---|---|---|---|---|
| WARD | 22 | 17 | 9 | 5 | 14 | 77% | 65% | iterate/park (recall below bar) |
| HAIR | 0 | 0 | 15 | 0 | 30 | n/a | 0% | insufficient-support |
| IDENT | 1 | 0 | 0 | 1 | 44 | 0% | n/a | insufficient-support |
| COUNT | 1 | 1 | 0 | 0 | 44 | 100% | 100% | insufficient-support |
| SIZE | 3 | 0 | 1 | 3 | 41 | 0% | 0% | insufficient-support |
| ANATOMY | 1 | 1 | 0 | 0 | 44 | 100% | 100% | insufficient-support |
| ENV | 4 | 3 | 5 | 1 | 36 | 75% | 38% | insufficient-support |
| COMPOSITE | 1 | 1 | 0 | 0 | 44 | 100% | 100% | insufficient-support |
| STYLE | 1 | 0 | 1 | 1 | 43 | 0% | 0% | insufficient-support |
| PROP | 1 | 0 | 0 | 1 | 44 | 0% | n/a | insufficient-support |

## Disagreements — vision-only flags (23 panels)

Vision flagged a group the banked verdict didn't. Each is either a vision false
positive or a defect that ESCAPED the banked QA — the drill-down below says which
after human/orchestrator review of the flagged panels.

| Panel | Image | Vision-only groups | Vision reason (first) |
|---|---|---|---|
| `p01-01` | `projects/not-so-supra-man/pages/panels-hf/p01-01.png` | ENV, HAIR | The tier-9 Dana figure (center) has black bob-length hair, but the bangs are swept/voluminous with a side part rather than the reference's straight, blunt full  |
| `p10-01` | `projects/not-so-supra-man/pages/panels-hf/p10-01.png` | WARD | Supraman's suit is scripted as 'scorched' but renders as a pristine, unblemished blue suit with no soot, char, or singe marks visible on chest, sleeves, cape, b |
| `p11-01` | `projects/not-so-supra-man/pages/panels-hf/p11-01.png` | ENV | The background is a dark, blurred exterior with rectilinear building-like silhouettes under what reads as a night sky — no lab elements (concrete walls, steel g |
| `p12-01` | `projects/not-so-supra-man/pages/panels-hf/p12-01.png` | WARD | Supraman's suit is scripted 'scorched' but reads as an intact, clean blue suit that is merely rain-wet, not charred or singed. Dana's white blouse and charcoal  |
| `p18-01` | `projects/not-so-supra-man/pages/panels-hf/p18-01.png` | STYLE | The panel breaks from the photoreal CGI look used elsewhere: cracks glow as bright graphic/vector-style jagged lines rather than physically-lit fractures, the p |
| `p19-01` | `projects/not-so-supra-man/pages/panels-hf/p19-01.png` | WARD | costume_state specifies 'suit rumpled, hair wrecked, one boot' but the render shows Supraman wearing a matched pair of red boots on both feet (not one boot as s |
| `p20-01` | `projects/not-so-supra-man/pages/panels-hf/p20-01.png` | WARD | Dana wears black boots rather than red; action/costume_state describe her wearing 'HIS spare suit stretched skin-tight, cape and all,' and Supraman's canonical  |
| `p21-01` | `projects/not-so-supra-man/pages/panels-hf/p21-01.png` | WARD | Supraman's suit is rendered as a red/blue color-blocked design with a large, ornate gold chest emblem, sharply different from the solid blue suit with a small c |
| `p23-01` | `projects/not-so-supra-man/pages/panels-hf/p23-01.png` | HAIR | Dee-Dee's hair reads as much lighter/less saturated (near white-blonde) than her warm golden-blonde reference. This is partly attributable to the teal beam's il |
| `p24-01` | `projects/not-so-supra-man/pages/panels-hf/p24-01.png` | HAIR | Dee-Dee's hair renders as very pale platinum/white-blonde, clearly lighter and less saturated than her warm golden dirty-blonde reference, with no special color |
| `p25-01` | `projects/not-so-supra-man/pages/panels-hf/p25-01.png` | HAIR | Dee-Dee's hair across all three stages reads as a light, cool platinum/ash-white blonde with minimal warmth, versus the canonical face-card which shows a warmer |
| `p26-01` | `projects/not-so-supra-man/pages/panels-hf/p26-01.png` | HAIR | The curly hair visible at the top of frame in all three stages reads as light, cool platinum/ash-white blonde, matching the same lightened-and-desaturated shift |
| `p27-01` | `projects/not-so-supra-man/pages/panels-hf/p27-01.png` | HAIR | Dee-Dee's curly hair reads as a bright, fairly cool-toned blonde with less of the honey/caramel warmth seen in the canonical face-card reference. The scene's mo |
| `p31-01` | `projects/not-so-supra-man/pages/panels-hf/p31-01.png` | HAIR | Dee-Dee/Destroya's large curly hair reads as a light, cool platinum/white-blonde, far lighter and less saturated than the warm honey-gold curly hair in her cano |
| `p32-01` | `projects/not-so-supra-man/pages/panels-hf/p32-01.png` | ENV, HAIR | Dee-Dee/Destroya's curly hair reads as a bright, warm golden blonde here — closer to canonical than in this batch's other panels, but still appears slightly bri |
| `p33-01` | `projects/not-so-supra-man/pages/panels-hf/p33-01.png` | HAIR | Destroya's (Dee-Dee) curly hair on the left reads as pale platinum/ash-blonde in this panel, noticeably lighter and less saturated than the warm honey-gold blon |
| `p34-01` | `projects/not-so-supra-man/pages/panels-hf/p34-01.png` | HAIR, WARD | Extremely clear close view of Destroya's hair (right): pale/platinum-blonde ringlets, a clear hue and saturation shift lighter than the warm gold-blonde in her  |
| `p35-01` | `projects/not-so-supra-man/pages/panels-hf/p35-01.png` | HAIR, SIZE | Very close, clear view of Destroya's hair (center): pale platinum-blonde, a clear hue/saturation shift from the warmer gold-blonde in her canonical reference. |
| `p36-01` | `projects/not-so-supra-man/pages/panels-hf/p36-01.png` | HAIR | Destroya's hair (top) again reads pale/platinum-blonde, lighter and less saturated than the warm gold-blonde canonical reference. Dana's hair (background, climb |
| `p37-01` | `projects/not-so-supra-man/pages/panels-hf/p37-01.png` | ENV, HAIR | Destroya's hair (background, center) reads pale/platinum-blonde, lighter and less saturated than the gold-blonde canonical reference. Dana (right, being hammere |
| `p38-01` | `projects/not-so-supra-man/pages/panels-hf/p38-01.png` | ENV, HAIR, WARD | Destroya's hair (background, partially cropped) again reads pale/platinum-blonde vs the gold-blonde canonical reference. Dana's black bob (left, kneeling) match |
| `p42-01` | `projects/not-so-supra-man/pages/panels-hf/p42-01.png` | HAIR, WARD | In stage 1 and stage 2 (neutral, non-backlit blue-sky lighting), Dana's hair reads as a solid medium-dark BROWN/chestnut with visible lighter brown tonal variat |
| `p46-01` | `projects/not-so-supra-man/pages/panels-hf/p46-01.png` | WARD | Dana's suit is rendered fully intact/pristine -- no tears visible anywhere on torso, arms, or legs -- which conflicts with the scripted costume_state 'dana: sui |

## Disagreements — subagent-only flags (11 panels)

The banked verdict recorded a defect group the shadow missed (vision false
negatives — these cap recall).

| Panel | Image | Missed groups | GT severity | GT issue |
|---|---|---|---|---|
| `p01-01` | `projects/not-so-supra-man/pages/panels-hf/p01-01.png` | SIZE | LOW | Supraman rendered hyper-massive (bodybuilder bulk) — violates "athletic, NOT hyper." Dana/Destroya tier sizes OK. |
| `p04-01` | `projects/not-so-supra-man/pages/panels-hf/p04-01.png` | WARD | LOW | Faint emblem reads on Dana's blouse (pre-transformation captive — should be plain). |
| `p10-01` | `projects/not-so-supra-man/pages/panels-hf/p10-01.png` | ENV | HIGH | WRONG LOCATION — outdoor rubble field, should be doomer-lab interior. |
| `p29-01` | `projects/not-so-supra-man/pages/panels-hf/p29-01.png` | WARD | LOW | Supraman is barefoot — missing his red boots (wardrobe slip). |
| `p30-01` | `projects/not-so-supra-man/pages/panels-hf/p30-01.png` | SIZE | HIGH | Scale error — Supraman rendered doll/figurine-sized (~2 ft) cradled against Dana. Tier-6 gap is overshot to near-tier-9; reads as a toy, not |
| `p32-01` | `projects/not-so-supra-man/pages/panels-hf/p32-01.png` | WARD | LOW | Likely chevron on Destroya's corset (villain-emblem); hard to confirm at angle. Composition good. |
| `p36-01` | `projects/not-so-supra-man/pages/panels-hf/p36-01.png` | WARD | LOW | Chevron on Destroya's corset (villain-emblem defect). |
| `p39-01` | `projects/not-so-supra-man/pages/panels-hf/p39-01.png` | IDENT, STYLE | BLOCKER | STYLE DRIFT — page rendered in anime / cel-shaded 2D illustration style (glossy manga shading, painterly energy streaks), NOT photoreal 3D/D |
| `p42-01` | `projects/not-so-supra-man/pages/panels-hf/p42-01.png` | PROP | BLOCKER | PROMPT LITERALIZATION — "cobra back … in full eclipse of the sun" rendered as a LITERAL giant king-cobra snake head (hood, scales, eyes) gro |
| `p45-01` | `projects/not-so-supra-man/pages/panels-hf/p45-01.png` | WARD | BLOCKER | EMBLEM WRONG — chest emblem is a single stylized "S"/lightning-bolt glyph in a rounded shield, NOT the gold double-chevron delta. Rule-2 vio |
| `p46-01` | `projects/not-so-supra-man/pages/panels-hf/p46-01.png` | SIZE | HIGH | TIER-9 SIZE REGRESSION — final-page Dana reads ~tier 6–7, only modestly larger than Supraman; arms not thicker than her head, bust not colos |

## Full panel matrix

| Panel | GT groups (sev) | Vision groups | agree-fail | vision-only | subagent-only |
|---|---|---|---|---|---|
| `p01-01` | SIZE (LOW) | ENV, HAIR | — | ENV, HAIR | SIZE |
| `p02-01` | WARD (HIGH) | WARD | WARD | — | — |
| `p03-01` | clean | clean | — | — | — |
| `p04-01` | WARD (LOW) | clean | — | — | WARD |
| `p05-01` | clean | clean | — | — | — |
| `p06-01` | WARD (HIGH) | WARD | WARD | — | — |
| `p07-01` | ENV (HIGH) | ENV | ENV | — | — |
| `p08-01` | WARD (LOW) | WARD | WARD | — | — |
| `p09-01` | WARD (LOW) | WARD | WARD | — | — |
| `p10-01` | ENV (HIGH) | WARD | — | WARD | ENV |
| `p11-01` | clean | ENV | — | ENV | — |
| `p12-01` | ENV (HIGH) | ENV, WARD | ENV | WARD | — |
| `p13-01` | WARD (HIGH) | WARD | WARD | — | — |
| `p14-01` | WARD (HIGH) | WARD | WARD | — | — |
| `p15-01` | WARD (HIGH) | WARD | WARD | — | — |
| `p16-01` | ENV, WARD (HIGH) | ENV, WARD | ENV, WARD | — | — |
| `p17-01` | WARD (HIGH) | WARD | WARD | — | — |
| `p18-01` | COUNT (LOW) | COUNT, STYLE | COUNT | STYLE | — |
| `p19-01` | clean | WARD | — | WARD | — |
| `p20-01` | ANATOMY, COMPOSITE (HIGH) | ANATOMY, COMPOSITE, WARD | ANATOMY, COMPOSITE | WARD | — |
| `p21-01` | clean | WARD | — | WARD | — |
| `p22-01` | WARD (HIGH) | WARD | WARD | — | — |
| `p23-01` | WARD (HIGH) | HAIR, WARD | WARD | HAIR | — |
| `p24-01` | WARD (HIGH) | HAIR, WARD | WARD | HAIR | — |
| `p25-01` | WARD (HIGH) | HAIR, WARD | WARD | HAIR | — |
| `p26-01` | WARD (HIGH) | HAIR, WARD | WARD | HAIR | — |
| `p27-01` | WARD (HIGH) | HAIR, WARD | WARD | HAIR | — |
| `p28-01` | clean | clean | — | — | — |
| `p29-01` | WARD (LOW) | clean | — | — | WARD |
| `p30-01` | SIZE (HIGH) | clean | — | — | SIZE |
| `p31-01` | WARD (HIGH) | HAIR, WARD | WARD | HAIR | — |
| `p32-01` | WARD (LOW) | ENV, HAIR | — | ENV, HAIR | WARD |
| `p33-01` | WARD (LOW) | HAIR, WARD | WARD | HAIR | — |
| `p34-01` | clean | HAIR, WARD | — | HAIR, WARD | — |
| `p35-01` | clean | HAIR, SIZE | — | HAIR, SIZE | — |
| `p36-01` | WARD (LOW) | HAIR | — | HAIR | WARD |
| `p37-01` | clean | ENV, HAIR | — | ENV, HAIR | — |
| `p38-01` | clean | ENV, HAIR, WARD | — | ENV, HAIR, WARD | — |
| `p39-01` | IDENT, STYLE (BLOCKER) | clean | — | — | IDENT, STYLE |
| `p40-01` | clean | clean | — | — | — |
| `p41-01` | clean | clean | — | — | — |
| `p42-01` | PROP (BLOCKER) | HAIR, WARD | — | HAIR, WARD | PROP |
| `p44-01` | clean | clean | — | — | — |
| `p45-01` | WARD (BLOCKER) | clean | — | — | WARD |
| `p46-01` | SIZE (HIGH) | WARD | — | WARD | SIZE |

## Appendix — parsed ground truth (auditable keyword mapping)

| Panel | Severity | Registry IDs | Groups | Issue (source row) |
|---|---|---|---|---|
| `p01-01` | LOW | BODY-07 | SIZE | Supraman rendered hyper-massive (bodybuilder bulk) — violates "athletic, NOT hyper." Dana/Destroya tier sizes OK. |
| `p02-01` | HIGH | WARD-05 | WARD | Anachronistic gold chevron/insignia on Dana's civilian white blouse — she is a captive reporter pre-transformation, blouse should be plain. |
| `p04-01` | LOW | WARD-05 | WARD | Faint emblem reads on Dana's blouse (pre-transformation captive — should be plain). |
| `p06-01` | HIGH | WARD-05 | WARD | Large gold double-chevron emblem on Dana's plain white blouse at tier 2 (bound captive). Should be plain blouse. |
| `p07-01` | HIGH | ENV-01 | ENV | WRONG LOCATION — scene is a boxing/wrestling ring with ropes, posts, arena seating. Should be doomer-lab (concrete, gantry, ray rig). Bindin |
| `p08-01` | LOW | WARD-05 | WARD | Growth-progressive format correct, but stray gold chevron appears on the white blouse in stage 3 (civilian garment). |
| `p09-01` | LOW | WARD-05 | WARD | Growth-progressive format correct, but stray gold chevron appears at hip/waist in stage 3 (civilian garment). |
| `p10-01` | HIGH | ENV-01 | ENV | WRONG LOCATION — outdoor rubble field, should be doomer-lab interior. |
| `p12-01` | HIGH | ENV-01 | ENV | WRONG LOCATION — outdoor city street in rain, should be doomer-lab interior. |
| `p13-01` | HIGH | WARD-05, WARD-04 | WARD | WARDROBE TOO EARLY — Dana in the BLUE hero suit + chevron. Page 13 (tier 6) she is still in the torn WHITE blouse; the blue suit does not ap |
| `p14-01` | HIGH | WARD-04 | WARD | WARDROBE TOO EARLY — blue hero suit + cape instead of torn white blouse. |
| `p15-01` | HIGH | WARD-04 | WARD | WARDROBE TOO EARLY — blue suit/skirt instead of the charcoal pencil skirt remnant. |
| `p16-01` | HIGH | WARD-04, ENV-01 | ENV, WARD | WARDROBE TOO EARLY — Dana in full blue suit (should be torn white-blouse remnants). Also location reads as a city rooftop, should be lab. |
| `p17-01` | HIGH | WARD-04 | WARD | WARDROBE TOO EARLY — Dana in blue suit; should still be torn-but-covering white remnants (suit-swap is page 20). |
| `p18-01` | LOW | CAST-02 | COUNT | "No characters" cutaway page contains a human figure standing on the rooftop at right — unintended extra. Otherwise correct exterior gag. |
| `p20-01` | HIGH | BODY-05, ENV-03 | ANATOMY, COMPOSITE | Compositing artifact — Supraman's reaction is a disembodied FLOATING HEAD in the doorway (no body), instead of a stunned figure. |
| `p22-01` | HIGH | WARD-05 | WARD | Gold hero chevron on Dee-Dee's (villain scientist) black top under the lab coat. Villains must not bear the hero emblem. |
| `p23-01` | HIGH | WARD-05 | WARD | Gold hero chevron on Dee-Dee's chest in the beam. Same villain-emblem defect. |
| `p24-01` | HIGH | WARD-05 | WARD | Gold hero chevron on Destroya's black corset. Destroya's corset is plain black — no chevron. |
| `p25-01` | HIGH | WARD-05 | WARD | Gold hero chevron on Dee-Dee's top (stages 1–2). Villain-emblem defect. Growth format otherwise correct. |
| `p26-01` | HIGH | WARD-05 | WARD | Gold hero chevron on Destroya's corset/glute (stage 3). Villain-emblem defect. Growth format otherwise correct. |
| `p27-01` | HIGH | WARD-05 | WARD | Gold hero chevron on Destroya's wrist cuff / corset. Villain-emblem defect. Implied-violence framing otherwise OK. |
| `p29-01` | LOW | WARD-01 | WARD | Supraman is barefoot — missing his red boots (wardrobe slip). |
| `p30-01` | HIGH | BODY-02 | SIZE | Scale error — Supraman rendered doll/figurine-sized (~2 ft) cradled against Dana. Tier-6 gap is overshot to near-tier-9; reads as a toy, not |
| `p31-01` | HIGH | WARD-05 | WARD | Gold hero chevron on Destroya's corset. Villain-emblem defect. Rampage shot otherwise strong. |
| `p32-01` | LOW | WARD-05 | WARD | Likely chevron on Destroya's corset (villain-emblem); hard to confirm at angle. Composition good. |
| `p33-01` | LOW | WARD-05 | WARD | Chevron on Destroya's corset (villain-emblem defect). |
| `p36-01` | LOW | WARD-05 | WARD | Chevron on Destroya's corset (villain-emblem defect). |
| `p39-01` | BLOCKER | STYLE-01, IDENT-01 | IDENT, STYLE | STYLE DRIFT — page rendered in anime / cel-shaded 2D illustration style (glossy manga shading, painterly energy streaks), NOT photoreal 3D/D |
| `p42-01` | BLOCKER | PROP-03 | PROP | PROMPT LITERALIZATION — "cobra back … in full eclipse of the sun" rendered as a LITERAL giant king-cobra snake head (hood, scales, eyes) gro |
| `p45-01` | BLOCKER | WARD-05 | WARD | EMBLEM WRONG — chest emblem is a single stylized "S"/lightning-bolt glyph in a rounded shield, NOT the gold double-chevron delta. Rule-2 vio |
| `p46-01` | HIGH | BODY-01 | SIZE | TIER-9 SIZE REGRESSION — final-page Dana reads ~tier 6–7, only modestly larger than Supraman; arms not thicker than her head, bust not colos |

> Cost: 6 sonnet vision subagents (~8 panels each), zero generation credits spent.
> p43-01 exists on disk but in no banked log (it is the agreed tier-9 benchmark page) — excluded from scope.
> GT validity: all 46 panels generated 2026-06-10 evening, audited same night, never re-rolled (project pivoted to restart-plan-v2 rebuild) — qa-report.md matches the on-disk images.

## Orchestrator adjudication (Fable 5, personally viewed the disputed panels)

The main-session judge reviewed the highest-stakes disagreements by eye. Rulings:

**Vision-only flags CONFIRMED REAL (escaped the human audit):**
- `hair_discontinuity` cluster, 12 panels p23–p38 — Destroya/Dee-Dee's hair renders platinum/ash-white-blonde vs the warm honey-golden face card (verified on `p34-01` vs `references/characters/dee-dee/face-card.png`). Systematic HAIR-01 drift the qa-report never logged (its eye was on emblems). These 12 "false positives" are true positives against reality.
- `p19-01` costume — scripted "suit rumpled, hair wrecked, one boot"; rendered composed with BOTH boots (and emblem drifting toward a shield form). Real WARD-04 escape; page absent from the audit table.
- `p21-01` costume — Supraman's suit color-blocked red-torso (canon: blue) with a large ornate shield-form emblem. Real canon-drift escape; page absent from the audit table.
- `p34-01`/`p38-01` skirt-absence calls: plausible (hero suit canonically includes skirt); left to owner.

**Vision misses CONFIRMED (human audit right, shadow wrong):**
- `p39-01` STYLE — the page is glossy painterly/anime-adjacent illustration, plainly off the DAZ photoreal house style; sonnet called it photoreal with high confidence. Real BLOCKER missed.
- `p30-01` SIZE — Supraman is unmistakably doll/figurine-scale; shadow returned clean. Confirms scale/size stays vision-hopeless (matches experiment 02).
- `p45-01` emblem-shape BLOCKER and `p29-01` missing-boots LOW also missed.

**Net effect on the naive table:** WARD effective precision rises to ~73% (19/26 flags real after adjudication) with recall vs. human GT unchanged at 77%; HAIR flips from "0% precision" to a verified systematic discovery. SIZE and STYLE remain below any usable bar.
