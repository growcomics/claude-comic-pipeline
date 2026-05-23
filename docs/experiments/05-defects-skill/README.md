# Experiment 05 — Defects-identification skill

**Hypothesis:** the defects human reviewers (Magnamus, Matt) catch in
eyeball passes follow recognizable patterns. Codifying them into a
labeled dataset + a structured rubric makes them detectable by an
automated vision audit, AND surfaces where the labelers agree (reliable
audit targets) vs disagree (need human review).

**Outcome:** **labeled-data foundation shipped.** This experiment produces
the dataset + taxonomy + rubric that Experiment 02 explicitly asked for
in its recommendation. Not a fine-tuned model. Not a wired audit. See
[`recommendation.md`](recommendation.md) for ship/soft/don't-ship per
category.

## Files

- [`raw-defects.md`](raw-defects.md) — Phase A. 57 defect observations
  collected from 5 sources (panel audit, ref-sheet audit, chun-li-test
  continuity report, Magnamus Discord pattern brief, CHANGELOG/MEMORY).
- [`taxonomy-v1.md`](taxonomy-v1.md) — Phase B. 38 leaves across 7 top
  buckets: `composite`, `character`, `background`, `camera`, `lettering`,
  `transformation`, `prompt_artifact`, `ref_sheet`. Forward-compatible
  mapping from Exp 02's 10 flat categories.
- [`labeled-defects.json`](labeled-defects.json) — Phase C. 36 labeled
  entries: 20 ultra-gal-origin panels (PNGs on disk; same set Exp 02
  used) with refined v1 sub-category labels, 10 chun-li-test panels
  (labels-only; PNGs in Flow cloud), 6 ref-sheet assets. Same JSON
  shape as Exp 02. Labels carry through Exp 02's labels verbatim under
  `exp_02_categories`.
- [`detection-rubric-v1.md`](detection-rubric-v1.md) — Phase D. The
  vision-model prompt. Story-panel mode + ref-sheet mode. Builds on
  Exp 02 v3 (canonical face cards as side-by-side reference) and v5
  (confidence-semantics anchoring). Avoids Exp 02 v4 (lowering the floor)
  which backfired.
- [`metrics-v1.md`](metrics-v1.md) — Phase E. Per-category recall and
  precision on the 4-panel holdout. Re-scoring of Exp 02's v3 and v5
  predictions against the refined taxonomy.
- [`recommendation.md`](recommendation.md) — Phase F. Ship-tier per
  category, what this experiment does NOT do, and the prioritized
  next-step list.
- `runs/holdout-rescoring-v3.json` and `runs/holdout-rescoring-v5.json`
  — per-panel rescoring verdicts.

## Headline numbers

- **57 raw defects** collected across 5 sources.
- **38 taxonomy leaves** in v1 (up from 10 in Exp 02).
- **36 labeled entries**: 20 by Matt-mapped-from-audit (ultra-gal) +
  10 by Matt-mapped-from-audit (chun-li) + 6 by Matt-mapped-from-audit
  (ref sheets). 5 additional defect-class observations from
  Magnamus-discord-pattern feed the taxonomy without per-panel labels.
- **Held-out (20%) re-scoring:** v5's `character.hair_color_drift`
  hits 100% recall + 100% precision on the holdout. Full-set Exp 02
  numbers were 100% recall / 38% precision — the holdout precision is
  optimistic.
- **`character.count_mismatch_*`** and the four `composite.*` leaves
  remain 0% (or unmeasurable) — Exp 02's unchanged blocker. The
  refinement names the failure modes but doesn't collect new labels
  for them.

## How this experiment relates to Exp 02

| Aspect | Exp 02 | Exp 05 |
|---|---|---|
| Taxonomy | 10 flat categories | 38 leaves across 7 buckets, forward-compatible |
| Labels | 20 panels, single project | 36 entries, 2 projects + ref sheets |
| Rubric | 5 iterations, best = v3 + v5 patterns | One rubric, combines v3 + v5 patterns + new categories |
| Measurement | Full 20-panel set, 5 iterations | 4-panel holdout, re-scored against refined taxonomy |
| Output | Script + recommendation | Dataset + taxonomy + rubric + recommendation |

The two experiments are **complementary**. The labeled set's JSON shape
is the same; concatenating them is a one-task follow-up.

## What this experiment does NOT do

- **No new model inference run.** All "measurement" uses Exp 02's
  existing predictions. The rubric is ready to call but the harness
  blanks `ANTHROPIC_API_KEY` (Exp 02 documented this), so a clean
  run would happen as a separate task using sub-agents (or the live
  API path when the key is restored).
- **No fine-tuning, no training a classifier.** Per the brief:
  "ML-style training is not in scope."
- **No wiring into the autopilot.** Same as Exp 02. Wiring is a
  separate decision after a unified rubric + measurement task.
- **No skill implementation.** Skill skeleton at
  `skills/defect-detection/SKILL.md` describes the intent only.

## Single-line conclusion

The defect-detection skill is now a **labeled corpus + a structured
rubric** that future audit runs can consume. Two of the 38 leaves
(costume color/garment drift + lettering typos and duplicates) are
ship-ready as automated checks. Six are ship-ready as soft warnings.
The blockers are the same ones Exp 02 surfaced: `composite.*` still
has zero labeled examples, `character.count_mismatch_*` still 0%
recall, `character.identity_swap` still 0% recall. Building this
labeled foundation is what unblocks all three.
