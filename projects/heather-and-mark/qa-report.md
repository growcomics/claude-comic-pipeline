# QA Report — Heather & Mark (69-panel canonical set)

- **Audit date:** 2026-07-20
- **Auditor:** fresh-context QA pass (generator did not grade its own work)
- **Rubrics applied verbatim:** `skills/comic-production/references/qa-checklist.md` (L19 baked-lettering checks ACTIVE, L35 transformation checks) + `skills/comic-production/references/cinematic-framing.md` (variety check: ≥5 distances / ≥4 angles / ≤3 same combo / ≥1 ECU + ≥1 wide-or-splash per 10 panels, scaled)
- **Inputs:** `projects/heather-and-mark/panels/001–069`, `ORDER-MANIFEST.json` act labels
- **Scope note:** the beach-trigger act's six athletic women are a sanctioned plot device and are NOT flagged. Crowd scenes that narratively require a public (001 party, 019/034/057-059 street) are logged as documented-intentional cosmetic entries, not violations. Gym/store extras ARE flagged — other gym panels prove empty-gym renders were achievable.

---

## Per-panel defects (defect panels only)

Severity: **B** = blocker (re-roll before composition), **S** = should-fix, **C** = cosmetic.

### Blockers

| Panel | Act | Category (checklist) | Sev | Description |
|---|---|---|---|---|
| 007 | 2 — beach trigger | Character consistency — duplicate character; Dialogue — repeated line | **B** | Second identical blue-swimsuit Heather figure bent over in left foreground (duplicate-Heather); the line "They're incredible. Tight arms, legs... those abs." is rendered TWICE (floating text top-right + bubble bottom). |
| 009 | 2 — beach trigger | Dialogue and Text — AI-garbled | **B** | Mark's bubble duplicates its opening clause: "You are a lovely girl and I / You are a lovely girl and I admit…". Classic baked-lettering garble; re-roll. |
| 020 | 3b — 14.5in | Dialogue and Text — AI-garbled | **B** | Heather's bubble truncated mid-thought: "I wonder if I'm bigger than." — broken sentence baked into the panel. |
| 032 | 3c — 18in | Continuity — size regression | **B** | Store-mirror Heather rendered slim-toned (arms ~baseline athletic) immediately after the visibly huge 030–031. Tier regresses within the act. |
| 033 | 3c — 18in | Continuity — size regression; Transformation — bicep benchmark | **B** | The act's payoff measurement panel: the arm labeled "18 inches" is rendered slender/smooth, far below the size shown in 030–031 and below any 18-inch benchmark. Undermines the act's central claim. |
| 059 | 5 — world + resolution | Dialogue and Text — AI-garbled; attribution | **B** | Orphan garbled bubble 'HEATHE: grace.' (misspelled prefix + fragment). Also the narration "We chose grace." carries a bubble tail pointing at the angry stranger — reads as his speech. |
| 062 | 5 — world + resolution | Continuity — size/stat regression | **B** | "New PR … Biceps: 26 inches" — but 052's wall chart (earlier in reading order) already circles CURRENT = 28. The stated stat regresses by 2 inches across acts. |

### Should-fix

| Panel | Act | Category | Sev | Description |
|---|---|---|---|---|
| SYSTEMIC (28 panels: 010, 014, 015, 017, 018, 021, 023, 025, 027, 030, 035, 037, 038, 039, 042, 043, 046, 047, 049, 053, 056, 059, 060, 062, 063, 064, 065, 068) | all | Dialogue and Text — lettering quality | **S** | Script formatting leaked into baked lettering: speaker-name prefixes ("HEATHER:", "MARK:", "MARK'S THOUGHTS:"), quotation marks around lines, and one stage direction "(Heather's voice)" (017). Bubbles should carry the line only; tail carries attribution. ~40% of the book. |
| 006 | 2 | Character consistency — clothing stable | S | Heather in white/cream top in foreground ECU; she wore the blue one-piece in 005, same beach outing. Also one of the six women is an auburn-redhead — reads close to Heather. |
| 011 | 2 | Dialogue — correct speaker | S | Narration "She didn't hesitate." rendered as a tailed speech bubble pointing at the gym clerk — misattributes Mark's caption voice to her. |
| 012 | 3a | No background extras; expressions | S | Gym extras present with wildly over-shocked faces at a routine curl; left extra is a Heather-lookalike redhead (duplicate-confusion risk). |
| 013 | 3a | No background extras — duplicate risk | S | Smiling auburn-redhead extra directly behind Heather; near-duplicate of the lead. |
| 015 | 3a | Dialogue — correct speaker | S | Heather speaks ("I have abs! Finally!") but the bubble tail drops toward Mark's blurred head at frame right. |
| 016 | 3a | Character consistency — clothing stable | S | White tee (014/015) becomes dark-green tee in the same "Mark, look!" beat (caption continues the moment). |
| 017 | 3a | Production/render artifact | S | Unmotivated torn holes in Heather's top plus ink-like black blotches on Mark's tee — no story cause at this tier. |
| 020→022 | 3b | Props consistent | S | Measuring-tape prop morphs across the sequence: soft white tape (020) → rigid construction tape from drawer (021) → soft yellow tailor tape (022). |
| 021 | 3b | Character consistency — clothing stable | S | Cream tee + navy shorts (020) becomes red tee + red shorts mid-conversation ("measure my muscles?" → "let's find out"), same room, same evening. |
| 024 | 3b | Character consistency — clothing stable | S | Red tee (021–023) becomes red sports bra mid-scene with no on-page beat. |
| 027 | 3b | Character consistency — clothing stable | S | Dark-green tank (025/026) becomes green long-sleeve top in the same bedroom scene. |
| 039 | 3c | Character consistency — clothing stable | S | Mauve tank during massage (037/038) becomes black sports bra + leggings in the continuing bedroom scene. |
| 040 | 4a | Continuity — mirror logic | S | Real Heather does a single-arm flex; the bathroom-mirror reflection shows a double-biceps pose. Reflection contradicts subject. |
| 041 | 4a | Continuity — mirror logic | S | Full-length mirror shows her back/rear view while she faces it — physically impossible reflection. |
| 041 | 4a | Coverage (always_clothed default) | S | Bottomless below the sweater (thong): bare glutes in reflection — buttock coverage not preserved per project default. |
| 042 | 4a | Coverage (always_clothed default) | S | No bottoms visible below the torn crop tee; groin implied-covered only by shadow/pose. |
| 046 | 4a | Continuity — costume regression | S | Inside the continuous 043→046 growth beat, the outfit jumps from blue long-sleeve + grey jeans (mid-rip in 044/045) to a white tee + khaki torn pants; blue scraps litter the floor but no on-page transition — reads as a reset. |
| 052 | 4b | Spec continuity | S | Chart circles CURRENT biceps = 28in; the locked story spec peaks at 26in (200+lb/26" peak). Internal chart is otherwise beautifully consistent with 022/033 — but the top number overshoots the spec. |
| 053 | 4b | No background extras — duplicate risk | S | Gym now populated: Mark plus a Heather-lookalike redhead extra and others; earlier acts prove clean empty-gym renders. |
| 054 | 4b | No background extras — duplicate risk | S | Gawking extras include the recurring Heather-lookalike redhead AND a Mark-lookalike (brown hair, gray tee, khaki) — two near-duplicates of cast in one frame. |
| 055 | 4b | Character count — duplicated extra | S | The gray-tank woman appears twice (center near Mark + right-foreground back view); plus assorted extras. |
| 058 | 5 | Character consistency — ambiguity | S | The office-dressed companion is an auburn-ponytail near-duplicate of baseline Heather. If intentional ("girl next door" callback), it needs a caption; as delivered it reads as an unexplained doppelganger. |
| 061 | 5 | Dialogue and Text — repeated line | S | Caption "Discipline. Joy. Fire." rendered twice in the same panel (lower-left box + upper-right box). |
| 065→068 | 5 | Pacing/order | S | Heather's question "You think I'm done growing?" (065) is answered by Mark's "God, I hope not." (068) with two unrelated caption panels (066, 067) interleaved — the exchange loses its snap. Consider reordering 067 before 065. |
| 069 | 5 | Dialogue and Text — repeated line | S | "To be continued..." duplicated (top-left and bottom-right) on the closer splash. |

### Cosmetic

| Panel | Act | Category | Sev | Description |
|---|---|---|---|---|
| 001 | 1 | Extras (documented-intentional) | C | Party flashback requires a crowd; logged for the record per the no-extras rule. Drink-splash physics slightly odd. |
| 003 | 1 | Text legibility (micro) | C | Marquee reads "X OFFICE" (BOX cut off); phone inset UI garbled ("missed call" + live Accept/Decline simultaneously, mangled button labels). |
| 008 | 2 | Extras | C | Single blurred bystander top-right on the beach. |
| 014 | 3a | Mirror logic; micro-text | C | Mirror-reflection geometry loose (real Heather off-frame); fitness-book spines garbled. |
| 018 | 3b | Dialogue — tail direction | C | Tail points at the wall mirror rather than Heather. |
| 019 | 3b | Extras (street, documented) | C | A few blurred pedestrians; store signage mush. |
| 020 | 3b | Costume artifact | C | Unmotivated slit/tear at the midriff of the cream tee. |
| 022 | 3b | Lettering convention | C | "Biceps: 14.5 inches" caption box carries a pointer tail (caption/bubble hybrid). |
| 023 | 3b | Anatomy — hands | C | Hand cluster at Mark's cheek is muddled (her hand + his two hands merge). |
| 025 | 3b | Clothing (scene change) | C | Red outfit → green romper on the living-room→bedroom cut; plausible change, noted. |
| 028 | 3b | Size consistency | C | Arms render noticeably softer/slimmer than 025–027 (morning-light aftermath panel); minor dip, not a tier break. |
| 029 | 3c | Expressions | C | Neutral/blank working face on the act-opener curl; acceptable for a work set but flat. |
| 031 | 3c | Extras; render | C | Extra man at right edge; background through mirror desaturated to near-greyscale. |
| 033 | 3c | Props | C | Butt sub-panel has two overlapping tapes; thigh tape floats loose. Skin on thigh/glute sub-panels heavily mottled. |
| 034 | 3c | Extras — duplicate risk (documented street) | C | Public-reaction beat needs a crowd (fine), but one whispering woman is another auburn Heather-lookalike. |
| 036 | 3c | Mirror logic | C | Foreground real pose (hand behind head) doesn't quite match reflection (fist beside head). |
| 037 | 3c | Anatomy; micro-text | C | Her trailing right-arm bend is awkward; massage-oil label garbled. |
| 040 | 4a | Micro-text | C | On-scale display garbled/mirrored; the clean "140.0 LBS" inset carries the info. |
| 045 | 4a | L19 overlay scope | C | Full-frame red/black burst lines are at the density the rubric warns about; bodies stayed photoreal, so no drift — watch it on re-rolls. |
| 049 | 4a | Anatomy — hands | C | Interlaced-fingers ECU has one knuckle-row too many at the clasp crest. |
| 052 | 4b | Anatomy — ambiguity | C | The arm pointing at the chart reads ambiguous in ownership (crosses in front of Mark). |
| 056 | 4b | Mirror logic | C | Reflection fills the mirror but the subject isn't in frame; passable if she stands just off-frame left. |
| 057 | 5 | Character consistency (Mark); extras | C | Mark's face is off-model (younger/narrower); crowd includes yet another redhead lookalike. Crowd itself is documented-intentional. |
| 063 | 5 | Mirror logic | C | Reflection shows Mark's arm around her waist; real Mark's arms are held in front of him. |
| 064 | 5 | Wardrobe vs reflection | C | Foreground real-Heather strap reads black; reflection tank is gray-green (likely shadow, but check). |
| 065 | 5 | Skin render | C | Chest/pec skin heavily vein-marbled at peak tier; borders on "raw" — keep on the healthy side of the muscle-color rule. |
| 067 | 5 | Caption prose | C | "super powered" caption is clunky/wordy; not garbled, just weak. |

---

## Summary

- **Blockers: 7** (panels 007, 009, 020, 032, 033, 059, 062)
- **Should-fix: 26 findings** (1 systemic lettering issue spanning 28 panels + 25 panel-level findings)
- **Cosmetic: 28 findings**

### Camera-variety verdict per act (cinematic-framing check, scaled to act length)

| Act | Panels | Verdict | Notes |
|---|---|---|---|
| 1 — origin | 001–004 | PASS (scaled) | medium/full/montage/mcu; fine for 4 panels. |
| 2 — beach trigger | 005–011 | PASS | wide beach, deep-staged crowd, OTS, mcu, solo medium; good depth staging in 007. |
| 3a — first gains | 012–017 | MARGINAL PASS | 4 distances incl. abs ECU; angles limited to eye-level/3q/profile; no wide. |
| 3b — 14.5in | 018–028 | **FAIL** | 11 panels, no wide-establish or splash; angle set ~3 (eye-level dominant, one profile ECU, one high-ish); heavy medium-eye-level repetition 018–021. Camera-static per the rubric. |
| 3c — 18in | 029–039 | PASS | street wide (034), measurement ECU collage (033), OTS mirror (036), high-ish (037), back/low variety. |
| 4a — 140lb | 040–051 | MARGINAL FAIL | Strong full-body coverage but eye-level-front dominates; 043–046 hold near-identical full-frontal framing (documented-intentional for the growth run); only 049 ECU; no true wide. |
| 4b — chart + peak | 052–056 | MARGINAL PASS | chart insert, full profile mirror, low-angle tower shot; no ECU in-act. |
| 5 — world + resolution | 057–069 | PASS | wide street opener, collage, measure ECU, low-angle scale shot, mirrors, splash closer. |

### Tier-continuity verdict

**FAIL — two regression events.** The per-act ladder (baseline → subtle → 14.5" → 18" → 140lb → peak) is respected everywhere EXCEPT: (1) Act 3c panels 032–033 render Heather at a visibly lower tier than 030–031 — with 033 being the act's own "18 inches" payoff panel; (2) Act 5 panel 062 states a "New PR" of 26" after Act 4b's chart already circled 28" current. Minor cosmetic softening in 028. Everything else, including the 052 chart's back-references (14.5 → 16 → 18 → 24 → 26; hips 55 at month 6 matching 033's tape), is impressively consistent.

### L35 transformation notes

- Only ONE active on-page growth sequence exists (043–046, RRRIP/SKRAK/aftermath) — it is excellent (SFX baked and legible, reaction intercuts, monotonic clothing destruction, peak faces). Growth-page ratio ≈30–35% counting reveal/measure panels: meets a plot-chapter target (≥30%), well under a transformation-chapter target (≥60%). Given the story is a life-arc romance this may be intentional, but per the growth-density mandate the book is light on on-page growth beats.
- No faceless money-shot runs (033 is a single 3-up body collage — borderline, noted).
- Muscle color natural throughout; no torn-skin language; muscles+breasts scale together.

### 5 worst panels

1. **059** — garbled orphan bubble ('HEATHE: grace.') plus a narration caption tail-pointed at a stranger; two lettering failures on one story-critical grace beat.
2. **033** — the 18-inch measurement payoff rendered on a visibly slim arm; contradicts the act it concludes.
3. **007** — duplicate Heather in frame plus the same line lettered twice.
4. **062** — "New PR: 26 inches" numerically regresses the 28-inch chart from 052.
5. **009** — duplicated clause baked into Mark's pivotal supportive line.

### Biggest risk before page composition

**The lettering is baked, and ~40% of panels (28 of 69) carry script-format leakage — "HEATHER:"/"MARK:" prefixes, quote marks, and one "(Heather's voice)" stage direction — plus 4 panels with outright garbled text (009, 020, 059, plus 007's duplicated line).** Page-composer is layout+PDF only (L19): none of this is fixable downstream, so every leaked prefix ships to the reader unless those panels are re-rolled. Triage order: re-roll the 7 blockers first, then decide whether the systemic prefix leak is accepted as a house style or batch-re-rolled — it is the single largest reader-facing defect class in the book.
