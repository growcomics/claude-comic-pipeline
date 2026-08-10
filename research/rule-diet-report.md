# Rule-Diet Report — lessons-learned.md classified by enforcement mechanism

**Date: 2026-08-09** · Report-only; nothing in the pipeline was modified. Pruning is an **owner decision** — this document deletes nothing and proposes candidates only.

**Sources read in full**: `skills/comic-production/references/lessons-learned.md` (L1–L36 + L1.5 + L10-refinement = 38 lessons), `skills/comic-production/references/DEFECT-REGISTRY.md` (V/S/J/H detection codes), `studio/inc/defects.php` `ck_qa_checklist()` (the 9-item live vision checklist: duplicate character, extra person, people count, wooden face, wardrobe drift, anachronism, wrong stage, anatomy, text artifact).

**Why this exists**: single-shot prompt walls with ~30 clauses at 90–95% per-clause compliance yield ~20% clean panels (0.93³⁰ ≈ 0.11–0.21). The over-generate+judge lane moves enforcement to **(a) attach-by-construction** and **(b) post-gen detection**; anything that is neither — **(c) prompt-prose wish** — is the compression target.

## Classes

- **(a) mechanical attach-requirement** — enforceable by construction at job-build time (ref selection/ordering, chaining, manifests, model/count settings, shotlist-structure gates that block before spend).
- **(b) post-gen detector** — the violation is visible in the output image/lettering and is (or feasibly can be) caught by a QA scan/judge; mapped to DEFECT-REGISTRY IDs, with coverage gaps noted (H-only / J-only).
- **(c) prompt-prose-only wish** — exists only as prompt wording; compliance probabilistic; not constructible and not detectable except by generic quality judgment.

## Summary counts

| Class | Count | Lessons |
|---|---|---|
| (a) mechanical | **22** | L1, L1.5, L3, L5, L6, L9, L10, L10-refinement, L12, L13, L14, L16, L19, L20, L28, L29, L30, L31, L32, L33, L34, L36 |
| (b) detector | **15** | L2, L4, L7, L8, L11, L17, L18, L21, L22, L23, L24, L25, L26, L27, L35 |
| (c) prose wish | **1** | L15 |
| Total | **38** | |

Headline: the catalog is healthier than the prompt walls suggest. Only one lesson is a pure (c) wish — but many (b) lessons carry large prose payloads whose *prevention* role becomes optional once the judge lane re-rolls their failures (see the secondary compression note after the prune list).

## Per-lesson classification

| ID | Gist (one line) | Class | Registry IDs (b) | Evidence / reasoning |
|---|---|---|---|---|
| L1 | Chain progressive sequences sequentially; prior panel job_id + portrait in medias | **a** | — | Pure job-build rule: which refs go in `medias[]` and in what order; runner enforces. Failure surfaces as CONT-01/WARD-02/BODY-02 but the rule itself is constructible. |
| L1.5 | Chain to the most recent view-compatible prior, not blindly N−1 | **a** | — | Anchor-selection algorithm over `view`/`chain_input` fields at build time; compatibility table is deterministic code, not prose. |
| L2 | Safety-filter fires on 4 stacked risk factors; dial back exactly one and retry | **b** | GEN-01 | Violation is auto-detected (job returns `nsfw` status — perfect detection, zero cost); the lesson is a repair playbook triggered by that signal, not a compliance wish. |
| L3 | Always pass the `.png` ref URL, never `_min.webp` | **a** | — | URL-string check at job build; trivially enforceable by construction (composer/runner rejects `_min.webp`). |
| L4 | Bubble shape per dialogue type, explicit position + tail attribution per speaker | **b** | LET-03, LET-04 | The block is auto-emitted (mechanically) inside L19, but compliance is probabilistic; wrong tails / paraphrased text are visible in lettering. LET-03 J-only, LET-04 V-partial (scanner receives the line but doesn't OCR-compare) — coverage gap noted in registry Tier 2. |
| L5 | Lineup ref only on stage-change panels (historical Higgsfield-era heuristic) | **a** | — | Attach policy; **superseded by L11's attach rule** (`should_attach_lineup()`: stage-change AND every full-body panel). Kept for diagnosis narrative only. |
| L6 | Display job batches in chunks of ~5 to avoid tool-result truncation | **a** | — | Pure tool-call batching mechanics at call-build time; nothing to do with image content. |
| L7 | Comic-coded vocabulary pulls the render to 2D illustration; positive CGI anchoring + one negation | **b** | STYLE-01 | 2D drift is visible in the output (BLOCKER); judge check 13 covers it; registry flags "photoreal CGI or 2D illustration?" as the **cheapest high-value V add** (no refs/context needed). The prose fix remains useful as re-roll-rate reduction, not as the enforcement. |
| L8 | CARRY FORWARD STATE blocks re-pin prior-grown features in later beats | **b** | WARD-02, BODY-02, CONT-01 | Regression of accumulated state is visible by comparing frames/panels; J-covered (judge check 11, qa-checklist §Continuity); no V (single-image scanner can't see the neighbour) — sequence-aware scan is the noted gap. |
| L9 | Record every job_id before the next submit or the chain silently breaks | **a** | — | Process gate: `state.json`/`verify_chain.py` make it constructible; registry classes it as GEN-02 with S-process detection ("a partially-filled job_ids.md IS the defect"). |
| L10 | References are the truth, prompts are deltas; env chaining; render directive | **a** | — | Architectural build rule: the composer builds delta-only prompts and attaches the accepted-panel env anchor by construction; the "linting hint" (suppress costume colors/wall materials when refs attached) is an S-check. Violations surface as IDENT-01/ENV-01 (both J-covered), but enforcement lives at compose time. |
| L10-refinement | Identity/costume/location → refs; camera/pose/expression/action/momentary state → prompt | **a** | — | Authoring/lint boundary for the same architecture — a deterministic column table enforceable by compose-time suppression (D11 pointer-only-prose gates), not a probabilistic wish. |
| L11 | Tier under-render: lineup attach rule + CRITICAL—MUSCLE/BREASTS + over-spec vocabulary | **b** | BODY-01 | The attach half is (a) (`should_attach_lineup()`, L28 lineup-at-ref-gen); but the ~9-part vocabulary wall is probabilistic and the failure is precisely judged post-gen (judge check 3: four-axis size vs anchor, "under on ANY axis = FAIL"). No V — feasible if the scan call attaches the tier ref (registry Tier-1 rank 2). |
| L12 | On-screen dialogue forces mcu-or-closer camera | **a** | — | Shotlist-structure gate at breakdown (rules_audit HARD; composer WARNING) — blocked by construction before generation spend. Registry: CAM-04, detect = S. |
| L13 | ≥3 dialogue lines from ≥2 speakers → split into per-speaker panels | **a** | — | Deterministic threshold gate at script-breakdown (rules_audit HARD). Registry: CAM-05, detect = S. |
| L14 | Multi-view env refs (`_source-reverse.jpg`) for shot-reverse-shot scenes | **a** | — | Attach requirement + `pick_location_anchor()` direction-matching at build time; L28 manifest makes the reverse ref mandatory when reverse shots are detected. Residual failure = ENV-01 (b-covered). |
| L15 | Female cast must read as strikingly beautiful — glamour-anchor block on every prompt | **c** | (IDENT-04, H-only) | Registry detection is "H (taste call)" — i.e. detection IS generic quality judging, the definition of (c). Not constructible; compliance probabilistic. See prune list. |
| L16 | Arc characters need 5-view reference packs (3q/profile/back/low-angle/ecu-region) | **a** | — | Manifest `views[]` block + `check_reference_completeness()` HARD gate — pure attach/asset requirement by construction. |
| L17 | Canonical IP characters: canon-sourced refs + canonical-anchor line | **b** | IDENT-02 | The ref-sourcing half is (a) (`canonical: true` drives ref gathering); the per-prompt anchor line is prose whose failure ("a fan wouldn't recognize them") is visible and judged — J/H only, no V (gap). Repair path exists (`auto_resubmit_with_different_face_card`). |
| L18 | Anatomy-coherence line (torso/hips/abs/feet same direction) on every prompt | **b** | BODY-05 | The lesson itself calls the line a "soft guardrail — doesn't catch every case"; malformed anatomy is the single best-covered defect: live V (`anatomy` in ck_qa_checklist), J (hand-count check 8), S (D13 gates). Detector-backed prose. |
| L19 | Bake 2D lettering, scope-bounded to bubble/caption/SFX only; unconditional | **b → a** classed **a** | — | The mandate ("lettering ALWAYS bakes; block auto-emitted by `_l19_lettering_block()`, no opt-out; page-composer no longer letters") is by-construction. Its failure modes are separately registered: STYLE-01 (via L7), LET-01/02/03/04 — all (b) rows of their own. |
| L20 | Camera distance bias: mean ≤ 2.5, ≥30% middle distances, body-region beats never full+ | **a** | — | Enforced by HARD rules_audit gates on the shotlist at breakdown (by construction, pre-spend) plus the auto-prepended ECU directive. Residual gap: rendered-wider-than-declared = CAM-01, S-covered upstream, V-feasible (registry Tier 3). |
| L21 | Ref-exclusion clause: never render an attached ref as an in-scene object | **b** | PROP-02 | The clause is cheap insurance prose; the leak (photo-in-seam, grid lines, figure labels) is visible and covered live: V (`anachronism` names "a reference sheet rendered as a literal in-scene object") + J (check 9) + S (reference-bleed negative gate). |
| L22 | Hair state named explicitly in every face-visible panel | **b** | HAIR-01 | Mechanically emitted from the shotlist `hair_state` field (`l22_hair_state.py`) but compliance probabilistic; drift (buns→updo, ribbon colour) is visible. J-covered; **scanner has no hair item — V gap** ("easy add" per registry). |
| L23 | Dense verbal env anchor (5+ named elements) when the env ref is dropped | **b** | ENV-02 | Void/grey background is visible and "trivially V-feasible" per registry (currently H/J — gap). The prose anchor stays useful to reduce the re-roll rate, but the failure is cleanly detectable. |
| L24 | Accessory suppression: canonical inventory + NO-watches/jewelry negation list | **b** | PROP-01 | Hallucinated watches/bracelets are visible and covered live by V (`anachronism`) + J; module `l24_accessory.py` even auto-negates the specific leaked item on retry — the detect-then-re-roll loop already exists. |
| L25 | Body-region reveals are sticky: exposure must not be retracted post-reveal | **b** | WARD-03 | Retraction is visible but needs story context: J/H only, **no V, no S, no rule module — flagged gap** in both the registry and its infrastructure-gap list. Detector-buildable (compare against the beat's declared exposure state). |
| L26 | Costume identity = explicit garment FAMILY, canonical remnant phrasing every panel | **b** | WARD-01 | Garment-family swap (bandeau ↔ collared blouse) is visible and covered: V (`wardrobe_drift`, strengthened by the Studio wardrobe note) + J (check 2) + S (D4/D11 turnaround gates). No dedicated rule module (registry gap note). |
| L27 | Skin sheen continuity: matte vs competition-oil named every panel | **b** | BODY-08 | Sheen inconsistency is visible across adjacent panels but **H-only today — "GAP everywhere"** (no module, no gate, no scanner line, no judge line). A sequence-aware scan could catch it specifically; until then this is the weakest (b). |
| L28 | `references_required.json` manifest; ref completeness gates Stage 3; tier refs generated WITH lineup | **a** | — | The canonical (a): manifest emitted at breakdown, walked by reference-gathering, HARD-failed by `check_reference_completeness()`, gating the stage transition. |
| L29 | Tier-6 dedicated reinforcement sheets attach alongside lineup (all-or-nothing, HARD gate) | **a** | — | Pure attach requirement with deterministic trigger (`tier == 6`), all-or-nothing file check, HARD audit gate. The accompanying directive is prose but the mechanism is attachment; failure = BODY-01 (b-covered by judge check 3). |
| L30 | Tier-7 reinforcement sheets (sibling of L29) | **a** | — | Same shape as L29; trigger `tier == 7`; HARD gate. |
| L31 | Tier-8 reinforcement sheets (sibling) | **a** | — | Same shape; trigger `tier == 8`; HARD gate. |
| L32 | Tier-9 reinforcement sheets (completes the series) | **a** | — | Same shape; trigger `tier == 9`; HARD gate. |
| L33 | Model selection at extreme tiers: NB2 for reliability, GPT for one cartoonish splash; never mix per chapter | **a** | — | A model-settings decision rule at project/job setup — the task definition's "count/model settings" case. Filter rejections it predicts are GEN-01 (auto-detected). |
| L34 | Subject staging: break the camera plane; per-beat `subject_staging` field + directives | **a** | — | The shotlist field + `check_subject_staging` HARD gate are by-construction. Caveat from the registry: the cited `_l34_staging_directive()` **does not exist in next_panel.py** (dangling reference) — enforcement today is gate-only; render-side flat staging = CAM-03 (S at shotlist; J/H for the render). |
| L35 | Growth money-shot face intensity + growth-page ratio + escalation-device menu | **b** | FACE-01, FACE-02, PAGE-01, PAGE-02 | Mixed lesson classed by its core: the peak-intensity face directive is prose whose failure (dead face) is covered LIVE by V (`wooden_face`, strengthened when plan-matched with dialogue) + J (check 6). The ratio and device pieces are S-gates at breakdown (a-style) — PAGE-01/PAGE-02 detect = S. |
| L36 | Story spine: required `story_spine` shotlist field, setup/payoff pairing, ending, distinguishing marks | **a** | — | Chapter-level structural gate (`check_story_spine`, Gate B, HARD) — checks structural *presence* by construction; story *quality* remains human (PAGE-03, H-only by design — "taste stays with the writer"). |

### Coverage-gap flags carried over from the registry (for the (b) rows)

- **H-only (no automated coverage at all)**: L27/BODY-08.
- **J/H-only (no live scanner line)**: L7/STYLE-01 (cheapest V add), L8+L25 (sequence/story-context aware), L17/IDENT-02, L22/HAIR-01 (easy V add), L23/ENV-02 (trivial V add), L4/LET-03 partial.
- **Live V today (ck_qa_checklist)**: L18/BODY-05, L21+L24 (via `anachronism`), L26/WARD-01, L35/FACE-01, L2 (platform status), plus the cast-count trio (CAST-01/02/03 — which, notably, has **no dedicated L-lesson and no rule module**: the owner's #1 defect is detector-covered but prompt-side unowned).

---

## PROPOSED PRUNE LIST (c)

> **Pruning is an owner decision. Nothing has been deleted, and this report changes no prompt, module, or gate.** These are candidates for removal from per-panel prompt walls **once the over-generate+judge lane exists** — each clause removed raises the per-panel clean probability of everything else (at ~30 clauses × 90–95%, every clause dropped is worth roughly 5–10 points of compound compliance).

### 1. L15 — glamour-anchor block on every female-cast panel (the only strict (c))

The 5-phrase glamour wall ("Vogue-cover face quality… sculpted cheekbones… strikingly beautiful…") is injected on **every panel** with a female cast member. Evidence it is not load-bearing at the per-panel layer:

- **Detection = quality judging.** IDENT-04's registry detection is "H (taste call)" — there is no violation distinct from "the judge/picker liked another variant's face better." In an over-generate+judge lane, the picker performs this selection natively on every submit; a prose clause whose only check is the pick itself is definitionally redundant with the lane.
- **It contradicts the pipeline's own L10 architecture.** Face quality is a *constant* carried by the face card; L15 itself records that the fix that actually worked was a **face-card re-roll** ("re-rolled with vogue-cover language and got dramatically better results" — a one-time ref-time act, and the registry's listed prevention is "face-card quality at ref time" plus the repair "face-card re-roll, then re-chain"). Re-describing the face's beauty per panel is exactly the constants-in-prose bleed L10/L10-refinement prohibit. Keep the glamour vocabulary **at face-card generation time only** (that half is (a): a ref-generation recipe), drop the per-panel `_female_beauty_anchor()` injection.
- **Refs-are-truth already moved this way.** CLAUDE.md's active default ("prompts describe ACTION, CAMERA, LIGHTING — never appearance walls") and the `refactor/refs-are-truth-prompts-are-action` branch treat per-panel appearance prose as a violation; the L15 per-panel line is the largest remaining appearance wall with no detector behind it.

**Risk if pruned**: chained panels whose face drifts plainer would previously get nudged back by the prose. Mitigation is already in the (a)/(b) stack: portrait paired on every chained panel (L1), face-card comparison in the judge rubric (IDENT-01, judge check 1), and the picker choosing among 4 variants.

### 2. Secondary compression note — detector-covered prose inside (b) lessons (not strict (c); flagged for the same diet)

These lessons stay in the catalog (their *diagnosis* and their *detectors* are load-bearing), but their per-panel prose clauses become **re-roll-rate optimizations rather than enforcement** once the judge lane is live — candidates for thinning if measured re-roll economics permit. Each is an owner call informed by the lane's actual re-roll costs:

| Prose clause | Lesson | Why the prose may not be load-bearing |
|---|---|---|
| Anatomy-coherence line (every panel, unconditional) | L18 | Self-described "soft guardrail"; BODY-05 has the strongest coverage in the whole registry (live V + J hand-count + S gates). The judge lane catches what the line misses either way. |
| Ref-exclusion clause (every panel with refs) | L21 | PROP-02 is V+J+S covered and the module's retry already auto-negates the specific leaked artifact — the detect-and-retry loop, not the standing clause, is the working mechanism ("per-panel detection is hopeless, but the suppression clause is cheap" was written before live V existed). |
| Accessory negation list | L24 | PROP-01 live-V covered (`anachronism`); `l24_accessory.py`'s retry appends the hallucinated item on failure — reactive negation demonstrably works, so the standing pre-emptive list is the thinnable half. |
| The 4-negation stacks L7 warns about | L7/L11 | L7 itself proved stacked negations dilute ("one strong NOT lands; four compete") — the same audit applied to L11's 9-part block and L24's lists would shrink walls with the judge as backstop (BODY-01 judge check 3 is the harsh-calibrated catcher). |
| L5 as a standing rule | L5 | Fully superseded by L11's attach rule; keep as history, remove from any active prompt/attach guidance surface. |

**Explicitly NOT prune candidates** despite being prose-heavy: L11's CRITICAL—MUSCLE/BREASTS + over-spec block (BODY-01 is VH-frequency and product-defining — prevention is worth real prompt budget until re-roll data says otherwise, and `feedback_chest_oversize_compensate` documents the model bias it corrects), L19's three-part scope-bounding (all three pieces validated load-bearing in production; STYLE-01 is BLOCKER), L23's verbal env anchor (fires only in the ref-ceiling corner case where no attach fix exists), and L26/L22 state-naming (they carry shotlist state the refs cannot, per L10-refinement's right-column).

---

*End of report. 38 lessons classified: 22 (a), 15 (b), 1 (c). No files modified other than the creation of this report.*
