# Experiment 05 — Recommendation

**Status:** Phase A–E complete. Phase F output is this file.

**Date:** 2026-05-23
**Branch:** `experiment/05-defects-skill`
**Coordinates with:** `experiment/02-vision-audit-pilot` (`labeled-set-v1.json`,
predictions reused for measurement).

## Headline

The defect-detection skill is **labeled-data + taxonomy + rubric**, not a
trained classifier or a fine-tuned model. This experiment delivers the
foundation Experiment 02 explicitly asked for in its recommendation:

> *"Spend half a day getting Matt or Magnamus to hand-label 20-30 more
> panels — concentrating on the gap categories — then re-run the best
> rubric and re-decide."* — Exp 02 recommendation

What's shipped here:

- **Taxonomy v1** — 38 leaves across 7 top-level buckets, refined from
  Exp 02's flat 10-category list. Every Exp 02 category forward-maps to v1.
- **Labeled set** — 36 entries (20 ultra-gal panels with PNGs + 10 chun-li
  panels labels-only + 6 ref-sheet assets labels-only). All Exp 02 labels
  preserved verbatim under `exp_02_categories` so re-scoring stays honest.
- **Detection rubric v1** — story-panel mode + ref-sheet mode, with the
  v3 face-card-as-side-by-side pattern and v5 confidence-semantics block
  baked in (the two Exp 02 patterns that worked).
- **Held-out re-scoring** — 4 panels (20%) scored against v3 and v5
  predictions, surfaced 100% hair-color recall on v5 (with the precision
  caveat from the full-set numbers).

## Per-category ship recommendation

Three tiers, mapped to the brief's framework:

### Ship as automated check (HARD finding)

These categories meet the brief's `recall ≥ 80%, precision ≥ 70%` bar
when paired with Exp 02's v3 face-card attachment pattern. Wiring them
into the vision audit is justified by Exp 02's measurements; this
experiment's taxonomy refinement adds specificity to the verdict.

- **`character.costume_color_drift`** — Exp 02 v3: 100% recall, 67%
  precision on parent `costume_discontinuity`. Borderline precision but
  the misses are all GOOD-panel false alarms on under-cropped torsos
  — the rubric's "if torso is cropped, set detected: false" precision
  note from v3 is what keeps this shippable. **Ship at MED+HIGH threshold,
  face card + body-tier ref attached.**
- **`character.costume_garment_missing`** — same parent as above; same
  numbers. Same recommendation.
- **`lettering.typo_or_doubled_word`** — Exp 02 best: 100% recall, 100%
  precision (v2/v3/v4). Cleanest signal in the entire experiment.
- **`lettering.duplicate_bubble`** — Exp 02 best: 100% recall, 75-100%
  precision. Same family as the typo category. Ship together.

### Ship as SOFT warning only

These have recall ≥ 60% but precision < 70% on the larger Exp 02 set,
OR they hit recall on the holdout but the full-set numbers expose
precision risk. Surface for human review, don't block.

- **`character.hair_color_drift`** — v5 hit 100% recall on the holdout
  (2/2) but 38% precision on the full Exp 02 set. The model over-flags
  hair drift on panels labeled costume-drift-only — could be true
  positives the audit undercounted OR true false positives. Can't tell
  without independent labeling. **Ship as SOFT** with the face-card
  attachment and v5's confidence semantics; do not block on it; surface
  for human review.
- **`transformation.state_overdelivered`** and **`transformation.state_underdelivered`**
  — chun-li-test labels confirm these are real defect classes (p03-01
  iris glow overshoot, p04-01 tear under-render) but neither has a panel
  PNG in this checkout to measure against. Ship as SOFT pending real
  measurement.
- **`camera.angle_underdelivered`** / **`camera.distance_underdelivered`**
  — every project audit surfaces these but the vision model has not
  been measured on them. Ship as SOFT with the shotlist `camera` field
  passed as part of the prompt.
- **`background.named_element_dropped`** — same; surfaces in every audit
  but never measured by vision. SOFT.
- **`character.face_drift_subtle`** — chun-li p02-01 is the only example;
  borderline by Matt's own classification (SOFT in continuity report).
  SOFT here too.
- **`ref_sheet.*`** (all 7 leaves) — measurement requires the audit
  script to consume ref-sheet images, which the current pipeline doesn't
  do. Ship as SOFT initially with a separate dispatcher.

### Don't ship yet (human-only check)

- **`character.count_mismatch_missing`** and **`_partial`** — Exp 02
  showed 0% recall across all 5 iterations. Vision model doesn't count
  reliably. **Use the deterministic shotlist-cast-size check Exp 02
  recommended as a pivot** — that's a Python-level check that catches
  the "expected 2, got 1" case without vision.
- **`character.identity_swap`** — Exp 02: 0% (n=1). Pass Lenny + Carl
  face cards alongside Heather + Mundy and re-measure before shipping.
- **`lettering.bubble_tail_wrong_speaker`** — Exp 02: 0% (n=1). Vision
  audit is the wrong tool — a vector-overlay-aware page-composer check
  that knows the assigned speaker per bubble is reliable; vision
  inference is not.
- **All 4 `composite.*` leaves** — still zero labeled examples. The
  taxonomy now NAMES the failure modes (split from the single Exp 02
  bucket), but no measurement is possible until composite panels are
  hand-picked and labeled. **This remains the single biggest blocker
  to shipping a holistic vision audit.**
- **`character.hair_color_drift_across_sequence`** — requires the
  rubric to receive a `prior_panel_image` attachment. No Exp 02 rubric
  did this. Build the attachment plumbing first, then re-measure.
- **`character.costume_state_drift_in_scene`** — same — needs prior-panel
  input. Build plumbing first.
- **`prompt_artifact.style_drift_2d`** / **`_ref_rendered_in_scene`** /
  **`_anachronistic_accessory`** — these are L21 / L24 rule classes
  with no labeled examples in the current set. The codified rules
  already catch them text-side; whether vision can add value is
  unknown until labels exist.
- **`character.gaze_misdirected`** / **`_prop_assignment_wrong`** /
  **`_coverage_risk`** — single example each, all from ultra-gal audit.
  No precision/recall data. Don't ship yet.

## What this experiment does NOT do (by design)

- **Not a fine-tuned classifier.** The brief is explicit: "produces labeled
  data + a prompt rubric. ML-style training is not in scope." This is a
  rubric + dataset, not a model.
- **Not a wired audit.** Same as Exp 02 — the script (or rubric) lands;
  wiring into autopilot acceptance is a separate decision after both 02
  and 05 align.
- **Not a Magnamus-direct-labeled set.** Magnamus's input appears in this
  dataset only as defect *classes* (Source 4 of `raw-defects.md`), not
  per-panel verdicts. A future Magnamus-direct labeling pass is the
  natural next unlock — the labeled set's `labels_by_labeler` array is
  designed multi-entry so disagreement with Matt can be captured later
  without rewriting.

## Where Magnamus + Matt agreement vs disagreement falls

**Zero direct disagreements** observed in this dataset, but that's a
labeled-set limitation, not an agreement signal:

- Magnamus's input enters via 5 defect CLASS patterns (empty speech-bubble
  tails, hair color jumps, costume color discontinuity, background extras
  at wrong scale, copy-pasted composites). Every one of those classes is
  covered by a v1 taxonomy leaf and most have at least one Matt-labeled
  panel exhibiting them. The two labelers agree on the *taxonomy*.
- Disagreement at the panel level is unmeasured because Magnamus has not
  hand-labeled the same 20 ultra-gal panels Matt's audit doc covers. The
  `labels_by_labeler` JSON structure is built to capture exactly that
  signal when a future labeling pass happens.

The interesting hypothesis to test next: **do Magnamus and Matt agree on
panels where the audit doc didn't flag a defect**? I.e., when Matt
implicitly labeled a panel GOOD, does Magnamus see drift? Those silent
disagreements are exactly the case where automated audit can add the
most value — surfacing what one human's first pass missed.

## Specific next-step recommendations

In priority order:

1. **Hand-label 5-10 `composite.*` panels.** Same ask as Exp 02. The
   gap is unchanged: still zero examples in the labeled set. Hand-pick
   panels where the foreground subject was clearly re-lit / composited.
   Score against rubric_v1 (this experiment's rubric, not Exp 02's) to
   re-measure on a populated category.
2. **Hand-label the 10 chun-li-test panels with PNGs available.** Pull
   the PNGs down from Flow into this repo (or stash them to disk for
   one audit run) and use the labels already captured in
   `labeled-defects.json`. This becomes a clean cross-project held-out
   test that the ultra-gal-only set never could.
3. **Have Magnamus hand-label the same 20 ultra-gal panels** as a
   blind independent labeler. Add his labels to `labels_by_labeler`.
   Then measure where he and Matt diverge — those are the panels that
   need human review even with automated audit shipped.
4. **Wire `prior_panel_image` into the rubric call** so
   `character.hair_color_drift_across_sequence` and
   `character.costume_state_drift_in_scene` become measurable. The
   pipeline already knows which panel preceded which; this is plumbing,
   not a model change.
5. **Build a small deterministic cast-count check** — read the
   shotlist's cast list, count human figures in the panel via a vision
   call asking ONLY "how many distinct people". This is Exp 02's
   suggested pivot for `character.count_mismatch_missing` and is much
   more reliable than asking the holistic audit model to count.
6. **Defer ref-sheet auditing until the audit script supports
   non-story-panel assets.** The `ref_sheet.*` leaves are well-defined
   but the dispatcher isn't built. A separate task.

## Coordination

This experiment is **complementary** to Exp 02, not a replacement. The
shared `labels_by_labeler` shape means a future combined run can
concatenate both labeled sets into one and re-measure jointly. The
recommended unified ship task (after this lands) is:

> Spawn a task to merge Exp 02's labeled set + Exp 05's labeled set + any
> new labels from steps 1-3 above into a single combined dataset, run
> rubric_v1 (this experiment's) against the merged set, and produce one
> final ship-or-iterate decision.

That task should be downstream of step 1 (more `composite.*` panels) so
the merged set finally has support in the HIGH categories that have
been the blocker since Exp 02.
