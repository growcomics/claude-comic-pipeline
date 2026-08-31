# DEFECT REGISTRY — canonical taxonomy of AI comic-page defects

*Created 2026-07-18. THE single source of truth for defect classes across the whole
pipeline. Unifies, without replacing: the L1–L35 lessons catalog
(`lessons-learned.md`), the rule modules (`../rules/`), the canonical audit rubrics
(`qa-checklist.md` + `cinematic-framing.md`), the per-project `qa/defect-registry.json`
(D1–D14, copy-propagated across manila-bay-rising / not-so-supra-man / tmb-daz-study /
ultra-gal-origin), the Studio's live `ck_ai_qa` vision scanner (creator.php), and the
`research/comic-corpus` findings. Those sources stay authoritative for their own layer
(lessons = diagnosis+fix narrative; rules = enforcement code; rubrics = audit
instructions); THIS file is the index that says what can go wrong, who catches it, and
where the holes are.*

*Owner-feedback loop that consumes these IDs: `docs/DEFECT-FEEDBACK-LOOP.md`.*

## ID scheme and legends

Canonical ID = `CATEGORY-NN` (stable, never renumbered; retire by marking DEPRECATED).
Each class also has a snake_case **slug** for JSON payloads (Studio flags, scanner
events, gate verdicts). Categories: CAST, IDENT, WARD, BODY, HAIR, ENV, PROP, LET,
FACE, CAM, STYLE, CONT, PAGE, GEN.

**Severity** — `BLOCKER` page unshippable; `MAJOR` a reader/owner notices, re-roll
expected; `MINOR` polish-pass item.
**Frequency** (estimate + evidence) — `VH` hits most batches; `H` several times per
chapter; `M` a few times per project; `L` rare/one-off.
**Detection codes** — `V` live auto-vision (Studio `ck_ai_qa`, per-panel);
`S` static/pre-generation gate (`compose.py`/`audit_prompt.py`/`preflight.py`/
`rules_audit.py` — text/metadata, no pixels); `J` post-flight judge / audit subagent
(rubric-driven vision: `judge-rubric.md`, `qa-checklist.md`); `H` human-only today.
A class whose only code is `H` (or `H`+`J` with no `V`/`S`) is a **coverage gap** —
see §Gap analysis.

### Scanner ↔ registry mapping (the live `ck_ai_qa` 10-type enum)

| ck_ai_qa `type` | canonical ID | slug |
|---|---|---|
| `duplicate_character` | CAST-01 | `duplicate_character` |
| `extra_person` | CAST-02 | `extra_person` |
| `people_count` | CAST-03 | `people_count` |
| `wooden_face` | FACE-01 | `dead_face` |
| `wardrobe_drift` | WARD-01 | `wardrobe_drift` |
| `anachronism` | PROP-01 (or PROP-02 when the detail names a reference sheet) | `anachronistic_prop` / `ref_as_object` |
| `wrong_stage` | BODY-03 | `wrong_stage` |
| `anatomy` | BODY-05 | `malformed_anatomy` |
| `text_artifact` | LET-02 | `garbled_text` |
| `other` | MISC-00 | `other` |

### Project D1–D14 ↔ registry mapping (`projects/*/qa/defect-registry.json`)

D-entries are mostly ROOT-CAUSE/process framed; canonical entries are SYMPTOM framed.
D1 thin-ref-stack → cause of IDENT-01/WARD-01/ENV-01 · D2 → FACE-01 · D3 → CAM-06 ·
D4 → WARD-01 · D5 → GEN-03 (process) · D6 → BODY-01 · D7 → BODY-07 · D8 → ENV-01 ·
D9 → BODY-09 · D10 → STYLE-03 · D11 → cause of IDENT-01/WARD-01 (L10 violation) ·
D12 → GEN-04 · D13 → BODY-05 · D14 → BODY-01. The D-file reserved lesson IDs
L36–L48 for its prevention gates; those reservations stand.

---

## CAST — people in frame

### CAST-01 · Duplicate character · `duplicate_character`
- **Symptom**: the SAME character appears two or more times in one panel (cloned/twinned figure).
- **Root cause**: identity refs get re-used as scene-fill; multi-ref confusion; the model's crowd prior. Worst with a face card + state anchor + lineup all showing the same person.
- **Severity/Frequency**: BLOCKER / VH — the owner's stated #1 defect (Studio QA-scan priority, "owner Beat 48").
- **Detect**: V (`duplicate_character` — verified live: synthetic duplicate → high/fail) · J (qa-checklist "Character count correct").
- **Prevent**: explicit cast-count line in every prompt ("EXACTLY N figures in frame: <names>; no other humans"); L21 ref-exclusion clause; no-extras negation. **No rule module emits a people-count clause today — prompt-side gap.**
- **Repair**: re-roll; or i2i edit on the winner ("remove the second <name>; change nothing else").
- **Links**: ck_ai_qa ✅ · qa-checklist §Character Consistency · lesson: none dedicated (candidate: new L-lesson under the loop) · rule module: none (GAP).

### CAST-02 · Unwanted extra / background person · `extra_person`
- **Symptom**: any human in frame who is not named cast — strangers, crowd, photo-bombers, blurred background people.
- **Root cause**: model's public-space prior (gyms, streets, beaches fill with people) unless the cast is declared closed.
- **Severity/Frequency**: MAJOR–BLOCKER / VH (repo default exists because of it; also not-so-supra-man qa-report p18).
- **Detect**: V (`extra_person`, biased to over-flag by design) · J.
- **Prevent**: CLAUDE.md default "NO background extras — only the named cast appears"; per-panel closed-cast line; negation "empty background, no bystanders" on public locations.
- **Repair**: re-roll; i2i person-removal.
- **Links**: memory `feedback_no_extra_characters` · ck_ai_qa ✅ · rule module: none (GAP — same clause as CAST-01).

### CAST-03 · Wrong people count · `people_count`
- **Symptom**: more or fewer figures than the panel's intended cast (including a MISSING named character).
- **Root cause**: crammed multi-speaker beats (L13); contact poses collapsing two bodies (see BODY-09); prompt never stating the count.
- **Severity/Frequency**: MAJOR / H.
- **Detect**: V (`people_count` + the scanner's people integer) · J.
- **Prevent**: per-panel "should contain ONLY: X, Y (2 characters)" (the scanner already receives this context); L13 split gate at script-breakdown.
- **Repair**: re-roll with the count line strengthened.
- **Links**: L13 (rules_audit) · ck_ai_qa ✅.

## IDENT — character identity

### IDENT-01 · Identity/likeness drift · `identity_drift`
- **Symptom**: face/features drift panel-to-panel; character stops looking like themselves mid-chapter.
- **Root cause**: broken/naive chain (L1, L1.5, L9); thumbnail `_min.webp` refs (L3); prompt re-describing appearance so text fights refs (L10 / D11); missing portrait pairing on chained panels.
- **Severity/Frequency**: MAJOR / H (multiple confirmed productions).
- **Detect**: J (judge-rubric check 1 — face vs face card, side-by-side) · H. **No V — the live scanner sees one image with no face card to compare.**
- **Prevent**: L1 (portrait paired on every chained panel) · L1.5 view-aware chaining · L3 full-res refs · L10 render directive (module `l10_render_directive`) · D1/D11 gates (ref-stack completeness, pointer-only appearance prose).
- **Repair**: re-roll with face card attached + render directive; if a chain is broken, restart chain from last good panel (L9 recovery paths).
- **Links**: L1/L1.5/L3/L9/L10 · rules `l10_render_directive.py` · qa-checklist §Character Consistency · scanner GAP.

### IDENT-02 · Canonical/IP character off-model · `canon_drift`
- **Symptom**: known character (Chun Li, Supergirl…) renders "in the family" but a fan wouldn't recognize them — wrong hair form, wrong costume cut.
- **Root cause**: model treats the name as a soft hint; interpolates between prior, prose, refs (L17).
- **Severity/Frequency**: MAJOR / M.
- **Detect**: J/H.
- **Prevent**: canon-sourced refs + per-prompt canonical-anchor line with negation — module `l17_canonical.py`.
- **Repair**: re-roll with canon face card swap (`auto_resubmit_with_different_face_card`).
- **Links**: L17 · rules `l17_canonical.py`.

### IDENT-03 · Male-anatomy drift on muscular female ECU · `male_drift`
- **Symptom**: body-region ECU of a muscular female character reads male — square pectorals, flat chest plane, no breast contour (face off-frame so nothing else disambiguates).
- **Root cause**: hyper-muscle vocabulary pulls toward male bodybuilder prior when the face is cropped.
- **Severity/Frequency**: MAJOR / M (Grok-validation p5).
- **Detect**: J/H; V-feasible (a single-image check could catch it) — GAP.
- **Prevent**: module `female_anatomy.py` (HARD, fires on ecu-region + tier ≥ 2 + female).
- **Repair**: re-roll with the female-anatomy anchor doubled.
- **Links**: May-14 finding · rules `female_anatomy.py`.

### IDENT-04 · Beauty regression (plain faces) · `beauty_regression`
- **Symptom**: female cast renders at "default attractiveness" — pleasant but unremarkable; "AI-generated woman" instead of a striking face.
- **Root cause**: the model's flat-middle beauty prior absent explicit glamour vocabulary (L15).
- **Severity/Frequency**: MAJOR (product-defining for the genre) / M.
- **Detect**: H (taste call).
- **Prevent**: glamour-anchor block — module `l15_glamour.py`; face-card quality at ref time.
- **Repair**: face-card re-roll with vogue-cover vocabulary, then re-chain.
- **Links**: L15 · rules `l15_glamour.py` · memories `project_chun_li_beauty`, `project_mira_character_anchor`.

## WARD — wardrobe

### WARD-01 · Wardrobe drift / garment redesign · `wardrobe_drift`
- **Symptom**: outfit or colour differs from intended wardrobe or changes mid-scene; garment FAMILY swaps between panels (bandeau wrap ↔ knotted blouse); outfit differs across the 4 variants of one submit; naming anatomy ("abs") silently redesigns the shirt into a crop-top.
- **Root cause**: generic costume prose lets the model improvise the garment each call (L26); anatomy keywords override garment state (memory `wardrobe_drift_from_anatomy_keywords`); no wardrobe-state turnaround attached (D4).
- **Severity/Frequency**: BLOCKER–MAJOR / VH.
- **Detect**: V (`wardrobe_drift`, strengthened when the project wardrobe note is filled in Studio) · J (judge check 2: "any color/emblem drift = FAIL") · S (D4/D11 gates require the turnaround + pointer-only prose).
- **Prevent**: garment-family lock phrasing (L26); wardrobe-state turnarounds per costume state (D4→`pick_turnaround()`); lock garment state + ref-chain the winner; never name covered anatomy — light with L27-style sheen/lighting language instead.
- **Repair**: re-roll with turnaround attached; i2i garment correction with composition lock.
- **Links**: L26 · D4/D11 · ck_ai_qa ✅ · memory `feedback_wardrobe_drift_from_anatomy_keywords`.

### WARD-02 · Costume-damage regression · `damage_regression`
- **Symptom**: tears/damage reset, shrink, or relocate across a sequence instead of accumulating monotonically.
- **Root cause**: parallel generation of a chained sequence (L1); silently broken chain (L9); missing carry-forward block (L8).
- **Severity/Frequency**: MAJOR / H (Chun-Li p8–10 confirmed).
- **Detect**: J (judge check 11: progressive monotonic; qa-checklist §Continuity) · H. No V (single-image scanner can't see the neighbour panel) — GAP for a sequence-aware pass.
- **Prevent**: sequential chaining + job-id discipline (L1/L9); CARRY FORWARD STATE blocks (L8); view-aware anchors (L1.5).
- **Repair**: re-run from the break point per L9's recovery paths.
- **Links**: L1/L1.5/L8/L9 · qa-checklist §Continuity.

### WARD-03 · Reveal retraction · `reveal_retraction`
- **Symptom**: a body region exposed as a story beat gets re-covered in later panels (the climax visually undone).
- **Root cause**: post-reveal prompts use vague coverage phrasing the model reads as full coverage (L25).
- **Severity/Frequency**: MAJOR / M.
- **Detect**: J/H (needs story context). GAP in V.
- **Prevent**: post-reveal canonical costume phrasing that names the exposure (L25).
- **Repair**: re-roll with the exposure-preserving directive.
- **Links**: L25 · no rule module (GAP).

### WARD-04 · Wrong story-stage costume · `costume_stage_error`
- **Symptom**: costume from the wrong story stage — hero suit pages before the in-story reveal; pre-transformation outfit after it.
- **Root cause**: stage-agnostic ref matched to an early/late panel; refs not stage-keyed.
- **Severity/Frequency**: MAJOR / H (5 consecutive pages in not-so-supra-man).
- **Detect**: V-partial (`wrong_stage` covers build, and wardrobe note may catch costume) · J · H.
- **Prevent**: stage-aware refs (Studio `ck_stage_eligible` matching; project `pick_turnaround()` costume-state resolver); per-page stage set in the plan.
- **Repair**: re-roll with the stage-correct turnaround.
- **Links**: Studio stage-aware refs (DEPLOY-NOTES 🎚) · memory `feedback_comic_stage_refs_and_realism`.

### WARD-05 · Emblem/insignia leak · `emblem_leak`
- **Symptom**: a costume emblem bleeds onto garments that must not carry it (hero chevron on a civilian blouse, on the villain's costume) — or renders as the wrong glyph entirely.
- **Root cause**: emblem/costume ref attached too broadly; ref applies itself to every torso in frame.
- **Severity/Frequency**: MAJOR (BLOCKER when wrong-glyph, e.g. the p45 S-shield-instead-of-chevron) / VH — **the single most frequent defect in the only full-chapter audit on file (15 of 32 defect rows, not-so-supra-man qa-report)**.
- **Detect**: J-partial (judge check 2 catches emblem drift when the turnaround is attached) · H. **No V, no S — GAP despite top measured frequency.**
- **Prevent**: attach emblem-bearing refs ONLY on suit pages; explicit negation on non-suit pages/characters ("plain blouse, NO emblem, NO chevron"); scope refs per character (L21-style exclusion naming which character each ref belongs to).
- **Repair**: i2i emblem removal ("remove the gold chevron from X's blouse; change nothing else") — cheaper than re-roll.
- **Links**: qa-report 2026-06-10 root-cause #1 · candidate for a new L-lesson + scanner checklist line (top of the loop's queue).

### WARD-06 · Coverage violation · `coverage_violation`
- **Symptom**: breasts/buttocks/groin coverage lost — violates the `always_clothed: true` project default.
- **Root cause**: destruction vocabulary ("tattered remnants") without the coverage clamp.
- **Severity/Frequency**: BLOCKER (policy) / L–M.
- **Detect**: S (compose.py torn-costume insurance auto-appends "coverage of chest and hips fully intact" whenever a character's costume state is torn/remnant) · H. GAP in V.
- **Prevent**: coverage clamp sentence; "straining/tearing" applies to fabric only, at seams.
- **Repair**: re-roll with clamp; do NOT ship.
- **Links**: CLAUDE.md generation defaults · compose.py insurance clause.

### WARD-07 · Skin-fabric gradient blend · `skin_fabric_blend`
- **Symptom**: a character flexes inside a long-sleeved garment (lab coat, sweater) and the model renders the bicep/limb as BARE SKIN that gradients impossibly into the fabric of the SAME arm — no seam, no hem, no cuff, no torn edge; skin and cloth read as one continuous material. Physically impossible.
- **Root cause**: skin/fabric material confusion — same family as skin-rendered-as-torn-fabric (owner walkthrough B20, insta-kill tier). When the prompt demands a visible flexed muscle while the garment ref says intact long sleeves, the model resolves the conflict by blending materials instead of choosing a physical outcome (tear, roll-up, garment off).
- **Severity/Frequency**: BLOCKER (physically impossible render; owner-flagged calibration 2026-08-11) / M on flex-in-sleeves beats.
- **Detect**: J (rubric line: look for a skin-to-cloth gradient on a single limb with NO seam/hem/rolled cuff/torn fabric edge between the two materials) · H. GAP in V and S.
- **Prevent**: any flex-in-sleeves beat MUST state the sleeve behavior explicitly. The only legal renderings: (a) the sleeve visibly TEARS/splits around the flexed muscle — e.g. "the sleeve seam splits open around the flexed bicep, torn fabric edges visible"; (b) sleeve rolled up with a crisp fabric edge; (c) the garment established as off in a prior transition panel. Enforced by STYLE v3 SLEEVES clause + per-beat injection rule 6 (`research/vitality-gap-2026-08-11.md`).
- **Repair**: re-roll with the explicit sleeve-behavior sentence; do NOT ship.
- **Links**: owner calibration 2026-08-11 (`research/owner-defect-feedback-2026-08-10.md` addendum) · sibling: skin-torn-as-fabric (B20) · STYLE v3 · stage-A checklist line in vitality-gap rubric section.

## BODY — build, size, anatomy

### BODY-01 · Tier under-render (size scale-down) · `size_underrender`
- **Symptom**: rendered body visibly smaller than the declared tier — right outline, missing 3-D muscle volume; or muscle lands but breast scale regresses; or the generated card is drastically smaller than the attached size anchor.
- **Root cause**: model normalizes off-distribution proportions toward average (D6); multi-figure lineup interpolates the peak figure downward (L29–L32); "silhouette" vocabulary reads as outline-only (L11); anchor-transfer direction failure even with the anchor attached (D14).
- **Severity/Frequency**: MAJOR (product-defining — the growth IS the product) / VH at tier ≥ 4.
- **Detect**: J (judge check 3: four-axis size vs anchor — arm-vs-head width, deltoid breadth, chest-shelf depth, mass fraction; "under on ANY axis = FAIL"; calibration exemplar: agent-pass/user-fail on `270c06dc`, "be harsher than feels natural") · H. **No V — single-image scanner can't compare to an anchor (feasible if the scan call attaches the tier ref).**
- **Prevent**: L11 vocabulary (CRITICAL—MUSCLE / CRITICAL—BREASTS + over-spec compensation) · lineup + tier-6/7/8/9 reinforcement attach rules (`l29`–`l32` modules, HARD) · anchor-first size transfer (D14) · body-tier refs generated WITH lineup (L28).
- **Repair**: re-roll with reinforcement refs + over-spec language; tier ≥ 7 persistent under-render → model swap per L33.
- **Links**: L11/L28/L29–L32/L33 · D6/D14 · memories `feedback_chest_oversize_compensate`, `feedback_growgetter_size_and_growth_scenes`.

### BODY-02 · Size regression across panels · `size_regression`
- **Symptom**: character shrinks back toward an earlier tier after a growth beat.
- **Root cause**: same chain failures as WARD-02 (L1/L8/L9); later-beat templates resetting carry-forward state.
- **Severity/Frequency**: MAJOR / H.
- **Detect**: J (qa-checklist "no size regression"; judge check 11) · H. GAP in V (sequence-aware).
- **Prevent**: chaining discipline; L8 carry-forward blocks re-pinning every grown feature per frame.
- **Repair**: re-run from break point.
- **Links**: L1/L8/L9 · qa-checklist §Continuity.

### BODY-03 · Wrong transformation stage vs beat · `wrong_stage`
- **Symptom**: character muscular/transformed on a beat that should be soft/untransformed, or vice-versa.
- **Root cause**: stage-agnostic refs; stage not named per panel; wrong ref matched.
- **Severity/Frequency**: MAJOR / H.
- **Detect**: V (`wrong_stage`, when the panel is plan-matched and the page stage is set) · J.
- **Prevent**: stage-aware ref matching (Studio) / `pick_turnaround()` (projects); tier comes from the shotlist only.
- **Repair**: re-roll with stage-correct refs.
- **Links**: ck_ai_qa ✅ · Studio 🎚 stage-aware refs.

### BODY-04 · Invented state change · `invented_state_change`
- **Symptom**: an un-scripted transformation appears — tier bump, new damage, hair change nobody asked for.
- **Root cause**: agent/prompt-side invention: deriving state from vibes instead of the shotlist (the L22 module explicitly refuses to auto-derive for this reason).
- **Severity/Frequency**: MAJOR / M.
- **Detect**: J vs shotlist · H. GAP in V (needs plan context — partially feasible via the plan-match the scanner already does).
- **Prevent**: state fields (tier, hair_state, costume_state) are author-owned shotlist data; composer passes through, never invents (memory `feedback_dont_invent_state_changes`).
- **Repair**: re-roll from the shotlist's declared state.
- **Links**: memory `feedback_dont_invent_state_changes` · L22 module's design note.

### BODY-05 · Malformed anatomy · `malformed_anatomy`
- **Symptom**: extra/missing fingers or limbs, fused bodies, broken hands, melted faces, impossible torso/hip twists, floating disembodied parts.
- **Root cause**: per-region generation without whole-body coherence (L18); un-accounted hands in multi-character contact (D13).
- **Severity/Frequency**: BLOCKER–MAJOR / H.
- **Detect**: V (`anatomy`) · J (judge check 8: count hands/limbs vs the total-hands line) · S (D13 gates demand per-hand accounting text).
- **Prevent**: L18 anatomy-coherence line (module `l18_anatomy.py`, universal) · D13 per-hand accounting + total-hands line in spatial_rules.
- **Repair**: re-roll; light i2i for a single bad hand.
- **Links**: L18 · D13 · ck_ai_qa ✅ · qa-checklist §Anatomy.

### BODY-06 · FMG-anatomy style errors · `fmg_anatomy_error`
- **Symptom**: teardrop instead of round breasts, blocky abs, drumstick forearms, lost hourglass, big head/hands on the grown body.
- **Root cause**: bodybuilder prior details leaking into the FMG aesthetic.
- **Severity/Frequency**: MINOR–MAJOR / M.
- **Detect**: J (qa-checklist §Anatomy FMG line + `fmg-anatomy-guide.md` failure table) · H.
- **Prevent**: fmg-anatomy-guide vocabulary in tier-build blocks (already partially in L11 tier descriptors).
- **Repair**: re-roll with the specific corrective phrase from the guide's table.
- **Links**: `fmg-anatomy-guide.md` · qa-checklist §Anatomy.

### BODY-07 · Height/scale inflation · `height_inflation`
- **Symptom**: character renders giant/towering (or doll-scale small) relative to cast/props when only muscle should change.
- **Root cause**: size vocabulary bleeding into height; missing height clamp (D7).
- **Severity/Frequency**: MAJOR / M (qa-report p30 toy-scale; giantess drift on tier pages).
- **Detect**: S (scale-risk regex + clamp check in audit_prompt/preflight) · J (judge check 4 vs height-chart.json) · H. GAP in V.
- **Prevent**: "height changes ONLY per the tier lineup, never beyond it" clamp on every tier page (compose.py injects).
- **Repair**: re-roll with clamp + a same-frame height reference (door, cast member).
- **Links**: D7 · judge check 4.

### BODY-08 · Skin sheen/texture inconsistency · `skin_sheen_drift`
- **Symptom**: skin material changes between adjacent panels — competition-oil shine vs natural matte.
- **Root cause**: PBR vocabulary leaves specular response free per generation; worse on big builds (L27).
- **Severity/Frequency**: MINOR / M.
- **Detect**: H only — GAP everywhere.
- **Prevent**: explicit sheen vocabulary every panel ("natural healthy matte skin… NOT oiled, NOT competition shine") (L27); volume comes from the lighting block, not oil.
- **Repair**: i2i lighting pass with the sheen named (cinematic-framing §volume block).
- **Links**: L27 · no module, no gate, no scanner line (GAP).

### BODY-09 · Contact-pose failure · `contact_pose_failure`
- **Symptom**: carries, holds, hugs, slams — multi-character physical contact renders wrong or differently per variant; bodies merge; hands misattach.
- **Root cause**: novel interaction with no staging reference (D9); un-specified spatial relationship resolved randomly.
- **Severity/Frequency**: MAJOR / M.
- **Detect**: S (preflight CONTACT_WORDS regex demands a staging ref) · J (anatomy + staging checks) · V-partial (`anatomy` catches the worst).
- **Prevent**: staging refs for novel poses (D9); per-character position/pose/hands staging JSON (qa/staging/*.json pattern).
- **Repair**: generate a staging ref first, then re-roll.
- **Links**: D9 · staging JSON pattern (cheer-ascension/manila).

### BODY-10 · Skin rendered as torn fabric · `skin_torn_as_fabric`
- **Symptom**: tear/rip/shred texture applied to SKIN instead of the garment — "her SKIN is torn like clothing" (owner B20, "recurring problem"). Also surfaces in animation transitions (2026-07-28 incident).
- **Root cause**: skin/fabric material confusion under damage vocabulary — same family as WARD-07's skin-fabric gradient.
- **Severity/Frequency**: BLOCKER (owner insta-kill tier) / M.
- **Detect**: J (rubric: any tear edge on a skin region) · H. V-feasible — GAP.
- **Prevent**: damage vocabulary always scoped to fabric at seams ("torn fabric edges"; "skin is never torn"); coverage clamp co-fires.
- **Repair**: re-roll; do NOT ship.
- **Links**: owner walkthrough 2026-08-10 B20 · sibling WARD-07 · `research/owner-missed-defects-2026-08-30.md`.

### BODY-11 · Growth plateau across sequence · `growth_plateau`
- **Symptom**: a growth rung renders no visibly larger than its predecessor — the sequence stalls even though each single image is clean (8 "growth plateaued" annotations; distinct from BODY-02 regression: nothing shrinks, it just stops).
- **Root cause**: additive deltas too timid at high tiers; model normalizes successive rungs toward the anchor.
- **Severity/Frequency**: MAJOR (growth IS the product) / H in ladder work.
- **Detect**: J with neighbour-panel context (compare rung N vs N-1 on the named axes) · H. No V (needs sequence).
- **Prevent**: explicit per-rung delta language ("visibly larger than the previous panel: bust +X, biceps rivaling head size"); "very"-stacking per the growth ladder.
- **Repair**: re-roll the rung chained off rung N-1 with the delta doubled.
- **Links**: bootcamp annotations · `reference_growth_comic_prompt_ladder` memory · L11.

## HAIR

### HAIR-01 · Hair-state drift · `hair_drift`
- **Symptom**: buns become updos, ribbons change colour or vanish, loose/tied state flips between panels.
- **Root cause**: hair is low-priority for state-anchor inheritance; drifts unless named per panel (L22).
- **Severity/Frequency**: MAJOR / H (three panels in one chapter, chun-li-ascension v2).
- **Detect**: J (qa-checklist "Hair consistent") · H. **The scanner checklist has no hair item — GAP in V** (easy add: "hair state differs from the wardrobe/continuity note").
- **Prevent**: explicit hair line on every head-in-frame panel from the shotlist `hair_state` field (module `l22_hair_state.py`).
- **Repair**: re-roll with the hair state named; i2i for ribbon-colour-only fixes.
- **Links**: L22 · rules `l22_hair_state.py`.

## ENV — environment

### ENV-01 · Location reinvention / room drift · `location_drift`
- **Symptom**: the same location renders as visibly different rooms across a scene; reverse angles invent a different room; backgrounds drift from the scene ref.
- **Root cause**: prompt re-describes location so text fights the env ref (L10); one env anchor can't serve a reversed camera (L14); scene ref framing mismatched to shot framing (D8).
- **Severity/Frequency**: MAJOR / H (Supergirl p02/p05; qa-report Act-1 lab drifting to boxing ring / rubble / street).
- **Detect**: J (judge check 7: "invented architecture = FAIL") · S (D8 gates: scene rung must exist + match camera distance class) · H. GAP in V (needs env-ref comparison).
- **Prevent**: env chaining — first accepted panel becomes the location anchor (L10); multi-view location refs for shot-reverse-shot (L14); scene ladder rungs by camera distance (D8).
- **Repair**: re-roll with the accepted-panel env anchor attached.
- **Links**: L10/L14 · D8 · qa-checklist §Background.

### ENV-02 · Void/grey background · `void_background`
- **Symptom**: character floats in a grey/blurry studio void on a panel where every neighbour shows the location.
- **Root cause**: env ref dropped at the 3-ref ceiling with only a vague verbal location mention left (L23).
- **Severity/Frequency**: MAJOR / M — and it hits the most important panels (stage changes, which is why the ceiling was hit).
- **Detect**: H/J today; trivially V-feasible ("empty studio void background") — GAP.
- **Prevent**: dense verbal env anchor — 5+ named location elements injected verbatim when the env ref drops (module `l23_env_anchor.py`).
- **Repair**: i2i background replacement with the location description + env ref re-attached.
- **Links**: L23 · rules `l23_env_anchor.py`.

### ENV-03 · Lighting/time-of-day drift · `lighting_drift`
- **Symptom**: morning light becomes fluorescent mid-scene; a lighting pass shifts dusk → cool night, breaking neighbours.
- **Root cause**: lighting state lives in prose and re-derives per panel; un-keyed lighting passes drift the palette (cinematic-framing hard rule: ALWAYS name the palette to preserve).
- **Severity/Frequency**: MINOR–MAJOR / M.
- **Detect**: J (qa-checklist "Lighting consistent") · H. GAP in V.
- **Prevent**: name the palette in every lighting pass; L28-v2 lighting-state refs (logged, not built).
- **Repair**: re-run the lighting pass with the palette-preserve clause.
- **Links**: cinematic-framing §volume block hard rules · L28 v2 (future).

### ENV-04 · Prop/furniture inconsistency · `prop_drift`
- **Symptom**: furniture and props appear/disappear/move between panels of one scene.
- **Root cause**: props live in prose, not refs; per-panel re-derivation.
- **Severity/Frequency**: MINOR / M.
- **Detect**: J (qa-checklist §Background props line) · H. GAP in V.
- **Prevent**: env chaining (props ride the accepted-panel anchor); recurring props get their own refs (L28 v2 prop-state refs).
- **Repair**: usually accept unless story-load-bearing; i2i for a load-bearing prop.
- **Links**: qa-checklist §Background · L28 v2 (future).

## PROP — accessories & artifacts

### PROP-01 · Anachronistic/hallucinated accessory · `anachronistic_prop`
- **Symptom**: unprompted modern wristwatch, bracelet, jewelry, phone; hot spots: wrists, ears, neck, ring fingers.
- **Root cause**: "young woman in studio render" prior fills accessory slots (L24).
- **Severity/Frequency**: MINOR–MAJOR / H.
- **Detect**: V (`anachronism`) · J.
- **Prevent**: per-character accessory inventory + negation list ("white spiked wristbands ONLY… NO watches, NO bracelets") — module `l24_accessory.py` (requires `cast[].accessories`).
- **Repair**: i2i removal; re-roll with the hallucinated item added to the negation list (the module's retry does this automatically).
- **Links**: L24 · rules `l24_accessory.py` · ck_ai_qa ✅.

### PROP-02 · Reference rendered as scene object · `ref_as_object`
- **Symptom**: an attached ref appears IN the scene — photo tucked in a seam, poster, badge, grid lines, figure numbers, floating proportion-stats text, model-sheet panels.
- **Root cause**: reference-aware models sometimes treat `role: image` refs as content (L21); worst in ECU/macro (blank canvas).
- **Severity/Frequency**: MAJOR / M (recurring across long chapters).
- **Detect**: V (`anachronism` names "a reference sheet rendered as a literal in-scene object") · J (judge check 9: mannequin/grid/model-sheet = FAIL) · S (reference-bleed negative required whenever a turnaround attaches).
- **Prevent**: exclusion clause whenever any ref attaches — module `l21_ref_safety.py`; no-mannequin/no-grid negative (gates).
- **Repair**: re-roll with the specific leaked artifact negated (module retry reads `substitute_rendered`).
- **Links**: L21 · rules `l21_ref_safety.py` · judge check 9.

### PROP-03 · Prompt literalization · `prompt_literalization`
- **Symptom**: figurative language renders literally — "cobra back" produces an actual snake in frame.
- **Root cause**: metaphor in prompt prose.
- **Severity/Frequency**: BLOCKER when it lands / L (qa-report p42).
- **Detect**: H (V-feasible as "object in frame contradicts the scene"). GAP.
- **Prevent**: no figurative language in composed prompts; lint pass at compose time for known metaphor vocabulary (candidate gate).
- **Repair**: re-roll with literal anatomy vocabulary.
- **Links**: qa-report p42 · no lesson yet (loop candidate).

### PROP-04 · Prop/object integrity glitch · `prop_glitch`
- **Symptom**: physically incoherent object — barbell reduced to an "empty/glitch bar" with the rest lying on the ground (owner B19); floating/duplicated parts; equipment fused with a body; held object not connecting through the grip.
- **Root cause**: per-region rendering without object-level coherence; complex equipment under occlusion.
- **Severity/Frequency**: BLOCKER (owner insta-kill tier) / M ("prop mangled" annotation + B19).
- **Detect**: J (trace every load-bearing prop end to end) · H. V-feasible — GAP.
- **Prevent**: equipment-integrity sentence when a prop is held/load-bearing ("the barbell renders complete, plates on both ends, bar continuous through her grip").
- **Repair**: re-roll; i2i rarely fixes structure.
- **Links**: owner walkthrough 2026-08-10 B19 · `research/owner-missed-defects-2026-08-30.md`.

## LET — lettering

### LET-01 · Missing/empty lettering · `missing_lettering`
- **Symptom**: panel ships with zero lettering, or balloons render EMPTY (the #1 flaw in the reference corpus: 6 of 9 published books ship blank balloons).
- **Root cause**: dialogue not baked (pre-L19 path) or bake silently dropped; empty `dialogue[]` upstream.
- **Severity/Frequency**: BLOCKER (competitive edge is lettered pages) / M in our output, VH in the genre corpus.
- **Detect**: J (qa-checklist §Dialogue) · H. **GAP in V — trivially feasible ("balloons present? empty?"), high value.**
- **Prevent**: L19 unconditional bake from shotlist `dialogue[]`/`captions[]`/`sfx[]`; Studio per-project lettering spec (`ck_letter_block`); memory `feedback_bake_dialogue`.
- **Repair**: re-roll (lettering is baked — there is no post-hoc letterer anymore).
- **Links**: L19 · corpus Finding 2 · Studio 💬 lettering spec.

### LET-02 · Garbled text / text artifacts · `garbled_text`
- **Symptom**: AI-mangled words, nonsense glyphs, stray tier labels or metadata baked into art, watermark strips mutating across passes (GHUN-LI → SHUN-LI).
- **Root cause**: model text-rendering instability; micro-text never survives re-renders (cinematic-framing hard rule).
- **Severity/Frequency**: BLOCKER–MAJOR / H ("the most common baked-lettering defect" — qa-checklist).
- **Detect**: V (`text_artifact`) · J.
- **Prevent**: short ALL-CAPS display text only; no render-carried micro-text/footers; exact-quote lettering blocks (L19/L4).
- **Repair**: re-roll the panel (text never patches well in i2i).
- **Links**: L19/L4 · ck_ai_qa ✅ · qa-checklist §Dialogue.

### LET-03 · Wrong speaker attribution · `wrong_attribution`
- **Symptom**: tail points at the wrong character; bubbles merged or attributed across speakers.
- **Root cause**: missing per-bubble position/tail spec (L4).
- **Severity/Frequency**: MAJOR / M.
- **Detect**: J (qa-checklist "Correct character speaking") · H. GAP in V (feasible: tail-vs-speaker geometry).
- **Prevent**: per-bubble fragments with named side-of-frame + "tail pointing directly to <name>'s mouth" (L4, emitted inside the L19 block).
- **Repair**: re-roll; i2i tail fix sometimes lands.
- **Links**: L4/L19.

### LET-04 · Dialogue mismatch vs script · `dialogue_mismatch`
- **Symptom**: bubble text paraphrases, drops, adds, or repeats lines vs the shotlist `dialogue[]`.
- **Root cause**: model rewrites text it can't reproduce; duplicate lines across adjacent panels.
- **Severity/Frequency**: MAJOR / M.
- **Detect**: J (qa-checklist "Dialogue matches the script… exactly") · V-partial (scanner receives the line when plan-matched but doesn't OCR-compare — GAP).
- **Prevent**: exact-quote directives ("reads exactly: …"); short lines (split beats per L13).
- **Repair**: re-roll.
- **Links**: L19/L4 · qa-checklist §Dialogue.

### LET-05 · Watermark/branding baked in · `watermark_branding`
- **Symptom**: a rendered wordmark, invented trademark, logo, render-engine credit ("RENDERED IN DAZ STUDIO"), or signature baked into the art — corners and edges are the hot spots.
- **Root cause**: product-sheet / promo-art training prior; franchise names in prompts invite the franchise wordmark.
- **Severity/Frequency**: BLOCKER (hard fail no matter the sculpt) / H — 12 of 193 loser annotations in the bootcamp case study ("watermark present").
- **Detect**: J/H; V-feasible (corner/edge text sweep, no context needed) — GAP.
- **Prevent**: explicit negation "no text, logos, watermarks, trademarks, or render credits" whenever a franchise/product name appears in the prompt.
- **Repair**: i2i removal sometimes lands on clean backgrounds; else re-roll.
- **Links**: bootcamp annotations rounds 2+ · `research/owner-missed-defects-2026-08-30.md`.

### LET-06 · SFX crowding / missing · `sfx_misuse`
- **Symptom**: sound-effect lettering covers a face or the growth payload, or dominates the frame; or an impact/growth beat that specifies SFX ships with none.
- **Root cause**: SFX placement unspecified; model sizes display text generously.
- **Severity/Frequency**: MAJOR / M (6 "SFX crowding" + 1 "SFX missing" annotations).
- **Detect**: J · H. GAP in V.
- **Prevent**: per-SFX placement fragment (side of frame, clear of faces/payload, small fraction of frame) in the L19 block.
- **Repair**: re-roll (baked lettering doesn't patch).
- **Links**: bootcamp annotations · L19.

### LET-07 · Lettering style inconsistency · `lettering_style_drift`
- **Symptom**: one bubble breaks the project's uniform balloon style — e.g. a single BLUE bubble in an all-white-bubble book (owner walkthrough B13).
- **Root cause**: bubble style re-derived per panel; not pinned in the lettering spec.
- **Severity/Frequency**: MAJOR / M.
- **Detect**: J; V-feasible (bubble fill/outline comparison — owner called it "easy detector, color histogram") — GAP.
- **Prevent**: bubble style sentence (fill, outline, font) in every L19 block from the project lettering spec.
- **Repair**: re-roll the odd panel.
- **Links**: owner walkthrough 2026-08-10 B13 · Studio `ck_letter_block`.

## FACE — expression

### FACE-01 · Dead face on an emotional beat · `dead_face`
- **Symptom**: flat/neutral/slack face where the beat demands strain, shock, ecstasy, fear — especially growth money-shots. The corpus's #1 weakness; "the reader mirrors a blank face and feels nothing."
- **Root cause**: no expression directive; expression prose too mild; face treated as detail.
- **Severity/Frequency**: MAJOR (product-defining) / VH (corpus aggregate 1.8% dead-face, up to 6% in the worst individual books; every un-guided run under-delivers).
- **Detect**: V (`wooden_face`, strengthened when plan-matched with dialogue: "a wooden face is a defect on this beat") · J (judge check 6; qa-checklist L35 lines).
- **Prevent**: peak-intensity face directive on growth beats (module `l35_growth_intensity.py`); mechanical face descriptions (posing-and-expressions.md); name the beat's emotion on every face (memory `feedback_expression_intensity`).
- **Repair**: re-roll with the named emotion + mechanical description; i2i expression pass holds composition.
- **Links**: L35 · corpus Finding 3 · rules `l35_growth_intensity.py` · ck_ai_qa ✅.

### FACE-02 · Faceless money-shot run · `faceless_run`
- **Symptom**: >2 consecutive face-cropped growth ECUs with no reaction/reveal face interleaved — the transformation sequence is emotionally mute end-to-end.
- **Root cause**: shotlist structure, not rendering: body-region beats stacked without reaction intercuts.
- **Severity/Frequency**: MAJOR / M.
- **Detect**: S (script-breakdown reaction-intercut rule; qa-checklist L35 line) — page-sequence check, not per-panel.
- **Prevent**: interleave reaction-intercut panels (escalation-devices.md).
- **Repair**: insert a reaction panel (new generation), not a re-roll.
- **Links**: L35 shotlist rules · qa-checklist §Transformation.

### FACE-03 · Expression uniformity / wrong gaze / no bystander reaction · `expression_uniformity`
- **Symptom**: identical expressions across a multi-character panel; characters staring at camera or into space; bystanders neutral during the extraordinary.
- **Root cause**: no per-character emotional beat assigned; gaze not directed.
- **Severity/Frequency**: MINOR–MAJOR / M.
- **Detect**: J (qa-checklist §Facial Expressions, three separate lines) · H. GAP in V.
- **Prevent**: distinct per-character emotion + who-looks-at-whom in every multi-character prompt (multi-character-variation.md).
- **Repair**: re-roll with per-character beats.
- **Links**: qa-checklist §Facial Expressions.

## CAM — camera & composition

### CAM-01 · Camera too far for the beat · `camera_too_far`
- **Symptom**: body-region growth beat shot full-body — the change doesn't dominate the frame; the transformation "never happens" on the page. Includes the render coming back wider than the declared camera.
- **Root cause**: camera authored independently of beat; model interprets soft camera vocabulary generously (L20's post-strengthening note).
- **Severity/Frequency**: MAJOR (genre-defining: hand-made mean 2.4 vs AI 4.1) / H un-guided.
- **Detect**: S (rules_audit HARD: mean ≤ 2.5 transformation chapters, ≥30% middle distances, body-region beats never full+) · J (rendered-distance audit) · **GAP in V for declared-vs-rendered distance (feasible)**.
- **Prevent**: aggressive body-region ECU directive (module `l20_camera.py`, HARD: "filling 70%+ of the frame… head and feet cropped OUT").
- **Repair**: re-roll with the ECU directive escalated (90% of frame).
- **Links**: L20 · rules `l20_camera.py` · rules_audit `check_camera_distance_bias`.

### CAM-02 · Camera monotony · `camera_monotony`
- **Symptom**: sequence sits at one distance/angle; comic reads static even when the action is intense (corpus flat% up to 25%, "five flat talking heads in a row").
- **Root cause**: per-panel authoring with no sequence-level rhythm.
- **Severity/Frequency**: MAJOR / H un-guided.
- **Detect**: S (rules_audit `check_camera_variety`: ≤3 same combo; cinematic-framing variety check: ≥5 distances, ≥4 angles per 10 panels) · J (qa-checklist §Camera Variety — ALWAYS included in audits per memory).
- **Prevent**: rhythm patterns (pull-in/pull-out/alternating/orbit); per-page distance spread ≥3 target (corpus).
- **Repair**: reassign cameras on the worst run; re-roll those panels.
- **Links**: cinematic-framing · corpus Finding 6 · memory `feedback_overshoot_camera_dynamism`.

### CAM-03 · Flat subject staging · `flat_staging`
- **Symptom**: figures parallel to the camera plane at equal scale — yearbook photo; passes distance/variety checks and still reads dead.
- **Root cause**: L20 governs the camera, nothing governed the blocking until L34.
- **Severity/Frequency**: MAJOR / H un-guided (corpus `flat-level` = "THE failure mode").
- **Detect**: S (rules_audit `check_subject_staging` HARD on multi-char medium+ panels; not-so-supra-man compose.py FLAT_LINEUP_RE — **only that one project**) · J/H.
- **Prevent**: `subject_staging` per beat (tension-block / depth-staged / triangular / negative-space-asymmetric / foreground-occlusion) with auto-emitted directives (L34). **Caveat found during this unification: L34 and cinematic-framing.md cite a `_l34_staging_directive()` in next_panel.py that does NOT exist in that file — the directive emission is unimplemented (dangling reference). Enforcement today = the rules_audit gate + not-so-supra-man's compose.py; no rule module.**
- **Repair**: re-roll with the staging directive.
- **Links**: L34 · cinematic-framing §Subject staging · corpus Finding 6.

### CAM-04 · Dialogue at wide framing · `dialogue_wide`
- **Symptom**: 30 words of dialogue on a wide establish; speaker unreadable, bubble floats over a tiny figure.
- **Root cause**: camera and dialogue authored independently (L12).
- **Severity/Frequency**: MAJOR / M.
- **Detect**: S (rules_audit HARD at breakdown; composer WARNING_DIALOGUE_CAMERA_CONFLICT).
- **Prevent**: on-screen dialogue forces mcu-or-closer (captions/off-panel exempt) (L12).
- **Repair**: tighten camera or convert to caption; re-roll.
- **Links**: L12.

### CAM-05 · Multi-speaker crammed panel · `crammed_speakers`
- **Symptom**: 3+ dialogue lines from 2+ speakers in one panel — sitcom freeze-frame, ambiguous reading order.
- **Root cause**: "one action beat = one panel" conflation (L13).
- **Severity/Frequency**: MAJOR / M.
- **Detect**: S (rules_audit HARD at breakdown: ≥3 entries from ≥2 speakers).
- **Prevent**: split into per-speaker panels at breakdown (L13 thresholds).
- **Repair**: split the beat and generate the new panels.
- **Links**: L13.

### CAM-06 · Declared camera disobeyed · `camera_disobeyed`
- **Symptom**: characters render front-facing/static regardless of the specced angle; profile requested, front delivered.
- **Root cause**: front-facing default prior (D3); no angle ref attached; soft angle vocabulary.
- **Severity/Frequency**: MAJOR / H (D3 is a founding entry of the project registry).
- **Detect**: J (judge check 5: "Default-front-facing when the spec says otherwise = FAIL") · H. GAP in V (feasible).
- **Prevent**: camera-first prompt ordering + angle refs (D3 → view packs, L16); lens vocabulary (cinematic-framing).
- **Repair**: re-roll with view-matched character ref attached (L16 view pack).
- **Links**: D3 · L16 · judge check 5.

### CAM-07 · 2D→3D composition infidelity · `composition_infidelity`
- **Symptom**: an import.php comic→3D transform loses the source panel's composition — camera, blocking, gestures, background staging differ from the 2D source.
- **Root cause**: identity refs outweigh the composition blueprint; prompt fails to pin "EXACT same composition".
- **Severity/Frequency**: MAJOR / M (importer pipeline only).
- **Detect**: H side-by-side. GAP (V-feasible with the source panel attached to the scan).
- **Prevent**: import.php contract — source panel is the composition blueprint, prompt leans on it, not prose.
- **Repair**: re-run i2i with the source panel as first ref + composition-lock opening clause.
- **Links**: studio/import.php · memory `project_comic_to_3d_importer`.

### CAM-08 · Fourth-wall gaze · `fourth_wall_gaze`
- **Symptom**: a character makes eye contact with the camera on a beat that is not scripted POV/direct address (owner B7).
- **Root cause**: forward-facing reference images bias output to face camera (ref-pose bleed).
- **Severity/Frequency**: MAJOR / M–H (owner: "acceptable only rarely/deliberately").
- **Detect**: J · H. V-feasible (gaze-at-camera on non-POV beats, plan-matched) — GAP.
- **Prevent**: 3/4 + profile view packs in refs (L16); per-panel who-looks-at-whom line.
- **Repair**: re-roll with gaze direction named and a view-matched ref attached.
- **Links**: owner walkthrough 2026-08-10 B7 · L16 · FACE-03 (gaze line).

### CAM-09 · Payload cropped out of frame · `payload_cropped`
- **Symptom**: the beat's declared key body region (waist, bust, bicep) is cut off by the frame edge even though camera distance is otherwise right — 6 "waist out of frame" annotations; the growth delta becomes unverifiable.
- **Root cause**: camera height/crop unspecified; distance vocabulary controls scale but not what the frame keeps.
- **Severity/Frequency**: MAJOR / H in ladder/lineup work.
- **Detect**: J (is the named payload region fully in frame?) · H. V-feasible when the plan names the region — GAP.
- **Prevent**: framing clause naming the payload ("waist to shoulders fully in frame, nothing cropped"); wardrobe-as-feature framing rules.
- **Repair**: re-roll with the framing clause; outpaint only as last resort.
- **Links**: bootcamp annotations · CAM-01 (sibling: too far vs cropped).

## STYLE

### STYLE-01 · 2D/illustration drift · `style_2d_drift`
- **Symptom**: panel renders as flat 2D comic illustration instead of photoreal DAZ3D CGI; usually the panels with heavy lettering/SFX.
- **Root cause**: comic-coded vocabulary (SFX, panels, bubbles) pulls toward illustration training data without scope-bounding (L7); 2D character ref inherits its aesthetic.
- **Severity/Frequency**: BLOCKER (style is the product spec) / M–H on lettered panels (3 of 10 in the Chun-Li run pre-fix; qa-report p39).
- **Detect**: J (judge check 13; qa-checklist scope-bounded lettering line) · H. **GAP in V — single-image "photoreal CGI or 2D illustration?" is the easiest high-value scanner add.**
- **Prevent**: L19 three-part scope-bounding (concrete render-engine opening + 2D-scope-bounded lettering block + scope-bounded closing negation — all three load-bearing); one negation not four (L7); CGI refs only.
- **Repair**: re-roll with the full L19 frame; NEVER strip the lettering to fix style.
- **Links**: L7/L19 · memory `feedback_comic_style_3d` · **no rule module for the L7/L19 style frame (composer-inline) — flagged gap**.

### STYLE-02 · Cast/style propagation failure · `style_propagation`
- **Symptom**: panels drift from the cast lineup's rendered style; base starter refs keep steering after the generated cast exists; characters look like different render engines.
- **Root cause**: starter refs used past lock-in; lineup not rendered photoreal first.
- **Severity/Frequency**: MAJOR / M.
- **Detect**: H. GAP.
- **Prevent**: render the cast lineup photoreal FIRST — its style propagates (memory `feedback_cast_lineup_style_propagates`); after page 0 attach generated lineup + size guide, not base refs (memory `feedback_use_generated_refs_after_lockin`).
- **Repair**: rebuild refs at the locked style; re-chain.
- **Links**: memories above · style-lock skill.

### STYLE-03 · VFX too perfect / AI-grade effects · `vfx_too_perfect`
- **Symptom**: energy/VFX reads simulation-grade — volumetric god-rays, physically-accurate filaments — "obviously AI-generated" instead of DAZ-store-prop + postwork aesthetic.
- **Root cause**: VFX vocabulary invoking simulation registers (D10).
- **Severity/Frequency**: MINOR–MAJOR / M.
- **Detect**: S (BANNED_VFX regex in audit_prompt+preflight) · J (judge check 10 vs vfx-style-bible).
- **Prevent**: vfx-style-bible vocabulary only (positive + negative blocks).
- **Repair**: re-roll with bible vocabulary.
- **Links**: D10 · `qa/vfx-style-bible.md` (absent from tmb-daz-study — dangling reference, see §Gap analysis).

## CONT — cross-panel continuity (umbrella)

### CONT-01 · State regression (general) · `state_regression`
- **Symptom**: any accumulated state — damage, size, hair, aura, weather — flickers or resets between panels (the umbrella over WARD-02/BODY-02/HAIR-01 when several fire at once).
- **Root cause**: parallel generation of chained beats (L1); silently broken chain (L9); wrong anchor view (L1.5); missing carry-forward (L8).
- **Severity/Frequency**: MAJOR / H.
- **Detect**: J (qa-checklist §Continuity; judge check 11) · S-process (`verify_chain.py` catches chainless ledger entries before the symptom ships).
- **Prevent**: L1 sequential chaining · L1.5 view-aware anchor choice · L9 job-id discipline · L8 carry-forward blocks.
- **Repair**: L9 recovery — accept the break and re-chain forward, or re-run from the break.
- **Links**: L1/L1.5/L8/L9 · `verify_chain.py`.

## PAGE — page/chapter structure

### PAGE-01 · Growth ratio under target · `growth_ratio_low`
- **Symptom**: the niche payload is crowded out — growth pages ÷ total under the chapter-type target (transformation ≥60%, climax ≥70%, action ≥30%; corpus median ~52%, pooled aggregate ~50%).
- **Root cause**: un-targeted shotlists drift low; plot/action fills the page budget (L35 Finding 1).
- **Severity/Frequency**: MAJOR (the product IS growth — memory `feedback_growth_density_mandate`) / H un-guided.
- **Detect**: S (script-breakdown §4.6 target check; qa-checklist L35 line).
- **Prevent**: ratio targets at breakdown; spread growth beats.
- **Repair**: shotlist revision — add/spread growth beats before generating.
- **Links**: L35 · corpus Finding 1.

### PAGE-02 · Escalation-by-repetition · `escalation_repetition`
- **Symptom**: climax pads with near-identical splashes; <2 escalation devices; each reveal repeats instead of changing scale/angle/stakes.
- **Root cause**: no device selection at breakdown (L35 Finding; corpus story weakness).
- **Severity/Frequency**: MAJOR / M.
- **Detect**: S (qa-checklist: scene declares ≥2 devices) · H.
- **Prevent**: escalation-device menu selection per transformation scene (escalation-devices.md).
- **Repair**: replace repeated splashes with different devices.
- **Links**: L35 · corpus Findings 4–5.

### PAGE-03 · Story flatline / stall · `story_stall`
- **Symptom**: mid-chapter dialogue stall between growth peaks; one-note tails ("villain hits, hero reels" ×10 pages); abrupt momentum-only endings; empty plot spine.
- **Root cause**: writing-layer weakness — the corpus's universal weak axis (no book above 3/5, median 2).
- **Severity/Frequency**: MAJOR (differentiation target: the niche fails here) / M.
- **Detect**: H (writers-room / owner read). GAP in tooling — story critique belongs to `story-writers-room`.
- **Prevent**: beat-sheet review before breakdown; "edging the payoff is fine; going silent is not".
- **Repair**: script revision; insert reversal/tease beats.
- **Links**: corpus Finding 5 · story-writers-room skill.

### PAGE-04 · Duplicate/orphan beats shipped · `duplicate_beats`
- **Symptom**: two shipped panels show the same growth beat; rejected alternates left in the folder; pages out of order.
- **Root cause**: production hygiene — regenerations not superseding, folder not curated.
- **Severity/Frequency**: MINOR–MAJOR / M.
- **Detect**: J (qa-checklist §Production Hygiene + no-duplicate-transformation line) · Studio organizer (winner-per-group model largely prevents this).
- **Prevent**: winner selection per group; trash-to-subfolder never rm (memory).
- **Repair**: curate; supersede.
- **Links**: qa-checklist §Production Hygiene/§Transformation.

## GEN — generation-time failures (process, not pixels)

### GEN-01 · Safety-filter rejection · `filter_rejection`
- **Symptom**: generation returns `nsfw`/blocked; on Flow, all 4 variants can hard-fail; steep low-angle compositions trip it on otherwise-SFW content.
- **Root cause**: stacked risk factors — max-size body + shredded clothing + flex pose + tight framing (any 3 of 4 usually passes, L2); GPT Image 2 far stricter than NB2 (L33); steep low-angle + body emphasis (Flow).
- **Severity/Frequency**: MAJOR (blocks production; costs retries) / H at peak tiers.
- **Detect**: automatic (status).
- **Prevent**: dial back exactly one of the four factors (L2); fuller athletic wear at extreme tiers (L33); reframe steep low-angle to three-quarter + foreshortening (memory `feedback_flow_low_angle_filter`); coverage clamps.
- **Repair**: retry up to 4× (filter variance clears — memory `feedback_nsfw_retry_policy`), then pivot styling/model — never grind identical retries on a hard policy block.
- **Links**: L2/L33 · memories `feedback_nsfw_retry_policy`, `feedback_flow_nsfw_policy_block`, `feedback_flow_low_angle_filter`.

### GEN-02 · Broken chain (lost job IDs) · `broken_chain`
- **Symptom**: process defect whose visible result is CONT-01/WARD-02/BODY-02 — panels generated "sequentially" but from baseline refs because prior job IDs weren't recorded.
- **Root cause**: IDs not captured before the next submit; runner bypassed mid-batch; ref_id/job_id confusion (L9).
- **Severity/Frequency**: MAJOR / M (was H before the discipline).
- **Detect**: S-process (`verify_chain.py`; a partially-filled job_ids.md IS the defect).
- **Prevent**: no submit without the prior ID in hand + current ID recorded (L9); runner/state.json.
- **Repair**: L9 recovery paths.
- **Links**: L9 · `verify_chain.py`.

### GEN-03 · Reference manifest skipped · `manifest_skipped`
- **Symptom**: process defect — mandated ref set silently skipped; surfaces later as IDENT-01/CAM-06/WARD-01.
- **Root cause**: "minimize ref gathering, do it in the prompt" default (L28/D5).
- **Severity/Frequency**: MAJOR upstream cause / M.
- **Detect**: S (`check_reference_completeness()` HARD; Stage-2 gate; compose/preflight D1 checks).
- **Prevent**: references_required.json manifest as a GATE (L28); body-tier refs generated WITH lineup.
- **Repair**: generate the missing refs, then re-roll affected panels.
- **Links**: L28 · D5.

### GEN-04 · Variant divergence · `variant_divergence`
- **Symptom**: the 4 Flow variants of one submit diverge wildly in blocking/wardrobe/count — ambiguity resolved randomly per variant; picking is a lottery.
- **Root cause**: under-specified prompt (D12) — everything not pinned varies.
- **Severity/Frequency**: MINOR (costs picking time, not pages) / H.
- **Detect**: H at pick time.
- **Prevent**: maximal structured prompts (D12 → prompt-template-v4); refs for everything constant.
- **Repair**: none needed if one variant lands; tighten the spec otherwise.
- **Links**: D12 · `prompt-template-v4.json`.

### MISC-00 · Other / unclassified · `other`
- Catch-all for owner flags that fit no class. Every MISC-00 flag with a note is a
  candidate new registry row — review whenever one recurs (see the feedback loop doc).

---

# Gap analysis — what nothing catches today

Ranked by how often the owner actually hits the defect (evidence: the not-so-supra-man
46-page audit — the only full-chapter defect count on file; corpus stats; the owner's
stated priorities; lesson-confirmed production incidents).

## Tier 1 — high frequency, weak/no automated coverage (build these first)

| Rank | Defect | Measured frequency | ck_ai_qa? | Gate chain? | What's missing |
|---|---|---|---|---|---|
| 1 | WARD-05 emblem leak | **15/32 rows** in the one full audit | ❌ | ❌ (judge-partial) | Scanner checklist line ("emblem/insignia on a garment that shouldn't carry it — the wardrobe note lists which"); compose-side emblem-scope rule; new L-lesson (loop's first auto-draft candidate) |
| 2 | BODY-01 size under-render | VH at tier ≥4; the "so smaller" calibration failure | ❌ | S-partial (attach gates only — can't see the render) | Anchor-aware scan: attach the tier ref to the QA vision call and ask "does the build match?"; the judge does this but only in gated projects |
| 3 | STYLE-01 2D drift | 3/10 panels pre-fix; BLOCKER when it lands | ❌ | ❌ (judge check 13 only) | **Cheapest high-value scanner add**: "photoreal CGI or 2D illustration?" needs no refs, no context |
| 4 | WARD-04 wrong-stage costume | 5 consecutive pages in the audit | partial (`wrong_stage` is build-only) | Studio stage-refs prevent; nothing detects | Extend `wrong_stage` wording to costume stage; pass the page's costume state in the scan context |
| 5 | LET-01 missing/empty lettering | genre-wide 6/9 books; our edge | ❌ | ❌ | Scanner line: "speech balloons present and filled when the panel context says a character speaks?" — context is already passed |
| 6 | IDENT-01 identity drift | H across productions | ❌ | J-only, gated projects only | Multi-image scan (panel + face card) — bigger lift; interim: sequence-aware audit batches |
| 7 | ENV-01/ENV-02 location drift / void bg | 3–4 pages in audit; hits stage-change panels | ❌ | S-prevent only | ENV-02 first ("studio void background?" — trivial); ENV-01 needs the env ref attached to the scan |

## Tier 2 — meaningful but lower measured frequency, no coverage

- **CAM-06 camera disobeyed** (D3 founding defect; judge-only) — feasible scan line when the plan carries the camera spec (it does when plan-matched).
- **HAIR-01** — scanner checklist has no hair item at all; one line + the wardrobe note fixes it.
- **PROP-03 prompt literalization** — rare but BLOCKER; a compose-time metaphor lint is cheap.
- **BODY-07 height inflation** — prevention gates exist; no render-side check outside gated projects.
- **WARD-03 reveal retraction, BODY-08 skin sheen, ENV-03 lighting drift, STYLE-02 style propagation, FACE-03 uniform expressions** — H/J-only across the board.
- **LET-03/LET-04 attribution + script-match** — the scanner already receives the dialogue line when plan-matched; it just isn't asked to compare.

## Tier 3 — covered upstream (static gates) but blind post-render

CAM-01 (rendered wider than declared), CAM-03 (flat staging in the render), PAGE-01/02
(shotlist-time only — fine, that's where they belong).

## Infrastructure gaps found while unifying (fix as hygiene, they corrupt the loop's data)

1. **Two disconnected defect vocabularies already exist** — the project D1–D14 file and
   the Studio scanner enum — and the one full audit used a THIRD, informal vocabulary
   ("stray gold chevron"), which is exactly how 15 hits of one defect stayed invisible
   to both. This registry is the merge; the loop keeps it merged.
2. **`rules/` on this branch: the `attach/ action/ match/ safety/` subdirs are stale
   `__pycache__`-only leftovers** from the unmerged `refactor/refs-are-truth-prompts-are-action`
   branch; live registry = 16 flat modules. `rules/README.md`'s status table documents
   only 11 of them (L29–L32 and L35 missing).
3. **No rule module for**: the L7/L19 style frame (composer-inline), L34 staging
   (audit gate only — the `_l34_staging_directive()` that L34 and cinematic-framing.md
   cite does NOT exist in next_panel.py; the directive emission is unimplemented),
   L25 reveal-stickiness, L26 garment-family lock, L27 skin sheen, CAST-01/02
   closed-cast clause. Composer-inline is acceptable; lessons with NO enforcement
   anywhere (L25/L26/L27, and L34's directive half) are real gaps.
4. **Judge verdict schema drift** — the banked verdicts use two ad-hoc shapes
   (`reason` in manila/tmb vs `notes`+`variant` in ultra-gal-origin, with free-form
   provenance fields `judged_by` vs `judge`+`date`); NO project emits the rubric's
   spec'd `reasons[]`/`variant_ranking`, and ultra-gal-origin's tags are pass-labels
   instead of defect tags. The loop needs verdicts carrying **registry slugs** in `tags[]`.
5. **Copy-propagation drift in the gate chain** — CONTACT_WORDS regexes and D1
   ref-count thresholds differ silently per project; tmb-daz-study enforces the
   BANNED_VFX regex referencing a vfx-style-bible.md it doesn't have; scene-ladder
   banking exists only in manila while the richer ladder logic lives in the other three;
   judge-rubric.md is absent from tmb-daz-study and ultra-gal-origin even though both
   produce verdicts; cheer-ascension has staging JSONs and a rubric but no gates at all.
   (Gate scripts are integrity-protected — any harmonization is a proposed diff for
   user re-blessing, per protocol.)
6. **`~/Downloads/april-lessons.md` no longer exists on disk** (memory says read it
   before pipeline changes). Its era's findings appear absorbed into
   `docs/posts/2026-05-14-what-works-and-what-doesnt.md` and L1–L24, but the memory
   pointer is stale.

---

# How this registry stays alive

1. **Every owner flag and every scanner hit carries a registry ID** — see
   `docs/DEFECT-FEEDBACK-LOOP.md` for the Studio flag UX, the shared event log, the
   frequency stats, and the auto-draft threshold (recurring flags on a GAP class →
   drafted lesson/rule for owner approval).
2. **New defect class** = new row here FIRST (ID + slug + symptom), then coverage:
   qa-checklist line, scanner checklist line if vision-detectable, rule module /
   gate if preventable, L-lesson when the diagnosis narrative is worth keeping.
   L36–L48 remain reserved for the D-registry's lesson candidates.
3. **The frequency column is a snapshot** (2026-07-18). Once the defect log
   accumulates, the Studio stats table supersedes these estimates — update this file
   when the ranking materially shifts.
4. Audits (subagent QA passes) must cite registry IDs in findings, and continue to
   receive `qa-checklist.md` + `cinematic-framing.md` **by path, verbatim, never
   paraphrased** — this registry indexes those rubrics; it does not replace them.
