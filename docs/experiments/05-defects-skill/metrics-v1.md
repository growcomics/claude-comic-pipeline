# Experiment 05 — Metrics v1

**Phase E output.** Per-category recall and precision on the held-out 20%.

## What was actually measured

The 4 held-out panels (`ug-p05-02`, `ug-p06-03`, `ug-p06-04`, `ug-p07-01`)
were scored by **re-using Experiment 02's existing model predictions** (the
`raw-predictions-v3.jsonl` and `raw-predictions-v5.jsonl` JSONLs in
`docs/experiments/02-vision-audit-pilot/runs/`) and forward-mapping the
flat Exp 02 categories into v1 taxonomy leaves.

**This is not a clean cross-validated measurement.** Exp 02's iterations
v1-v5 were tuned by inspecting failures on the full 20-panel set including
these 4 panels. The measurement here answers a narrower question:

> Given the model already saw these panels during Exp 02's rubric tuning,
> does the refined v1 taxonomy still produce coherent per-category metrics?

A clean held-out test requires labeled panels outside Exp 02's tuning loop.
The chun-li-test panels are exactly that population — they are labeled in
this experiment's dataset but their PNGs are not in this checkout (they live
in the user's Flow project on macmini). When those PNGs are pulled down or
when a new project's panels are labeled fresh, that becomes the real
held-out measurement. This metrics file is honest about being a
re-scoring exercise, not a generalization test.

## Per-category metrics (holdout = 4 panels)

### Re-scoring Exp 02 **rubric v3** predictions:

| v1 category | TP | FP | FN | TN | recall | precision | support_bad |
|---|---|---|---|---|---|---|---|
| `character.hair_color_drift` | 1 | 0 | 1 | 2 | **50%** | **100%** | 2 |
| `character.hair_color_drift_across_sequence` | 0 | 0 | 1 | 3 | 0% | n/a | 1 |
| `character.count_mismatch_missing` | 0 | 0 | 1 | 3 | 0% | n/a | 1 |

### Re-scoring Exp 02 **rubric v5** predictions:

| v1 category | TP | FP | FN | TN | recall | precision | support_bad |
|---|---|---|---|---|---|---|---|
| `character.hair_color_drift` | 2 | 0 | 0 | 2 | **100%** | **100%** | 2 |
| `character.hair_color_drift_across_sequence` | 0 | 0 | 1 | 3 | 0% | n/a | 1 |
| `character.count_mismatch_missing` | 0 | 0 | 1 | 3 | 0% | n/a | 1 |

### Other categories

The remaining 35 v1 taxonomy leaves were not exercised on the holdout (no
positive examples in the 4-panel held-out partition). Their full-set
behavior carries over from Exp 02's measurements where the parent
category was measured:

| v1 leaf | Inherited from Exp 02 parent | Exp 02 best-version recall | Exp 02 best-version precision |
|---|---|---|---|
| `character.costume_color_drift` | `costume_discontinuity` | 100% (v3) | 67% (v3) |
| `character.costume_garment_missing` | `costume_discontinuity` | 100% (v3) | 67% (v3) |
| `character.costume_design_drift` | (new in v1; no Exp 02 measurement) | n/a | n/a |
| `character.costume_state_drift_in_scene` | (new in v1; needs prior-panel input) | n/a | n/a |
| `character.identity_swap` | `character_identity_swap` | 0% across all 5 | n/a |
| `character.count_mismatch_partial` | `character_count_error` | 0% across all 5 | n/a |
| `lettering.typo_or_doubled_word` | `lettering_error` | 100% (v2/v3/v4) | 100% |
| `lettering.duplicate_bubble` | `lettering_error` | 100% (v2/v3/v4) | 75-100% |
| `lettering.empty_bubble` | `empty_speech_bubble` | 0% (n=0 examples; the labeled example was actually a tail-wrong-speaker) | n/a |
| `lettering.bubble_tail_wrong_speaker` | `empty_speech_bubble` | 0% across all 5 | n/a |
| `composite.*` (all 4) | `composite_mismatch` | not measurable (n=0) | n/a |
| `background.extra_at_wrong_scale` | `scale_error` | not measurable (n=0) | n/a |
| `transformation.*` (all 3) | `tier_visualization_mismatch` | not measurable (n=0) | n/a |
| `prompt_artifact.style_drift_2d` | `prompt_bloat_artifact` | not measurable (n=0) | n/a |
| `prompt_artifact.ref_rendered_in_scene` | (new in v1; no Exp 02 mapping) | n/a | n/a |
| `prompt_artifact.anachronistic_accessory` | (new in v1; no Exp 02 mapping) | n/a | n/a |
| `camera.*` (3 leaves) | (new in v1; not in Exp 02 taxonomy) | n/a | n/a |
| `background.unsanctioned_extra` | (new in v1) | n/a | n/a |
| `background.environment_drift` | (new in v1) | n/a | n/a |
| `background.named_element_dropped` | (new in v1) | n/a | n/a |
| `character.face_drift_subtle` | (new in v1) | n/a | n/a |
| `character.face_identity_drift` | (new in v1) | n/a | n/a |
| `character.gaze_misdirected` | (new in v1) | n/a | n/a |
| `character.prop_assignment_wrong` | (new in v1) | n/a | n/a |
| `character.coverage_risk` | (new in v1; partial overlap with L33) | n/a | n/a |
| `character.scale_normalization_drift` | (new in v1) | n/a | n/a |
| `character.hair_state_drift` | (new in v1; partial overlap with hair_discontinuity in Exp 02) | n/a | n/a |
| `ref_sheet.*` (7 leaves) | (new in v1; Exp 02 didn't audit ref sheets) | n/a | n/a |

(So 26 of the 38 v1 leaves are genuinely new vs Exp 02 — they have NO prior
measurement and therefore no shipping evidence either way.)

## Headline read

- **Hair color drift detection is mature.** v5 hit 100% recall on the holdout
  (2/2) and 100% precision (0 FP). Full-set Exp 02 numbers were 100%
  recall / 38% precision on v5 — the holdout precision is better because
  the GOOD panel in the holdout (`ug-p06-03`) is an ECU-region from-behind
  crop without much face-card-comparable hair surface, which Exp 02's v5
  did not over-flag here. The full-set 38% precision is the more honest
  number to plan around.

- **Cross-sequence hair drift remains unmeasured by the rubric.** The new v1
  category `hair_color_drift_across_sequence` requires a `prior_panel_image`
  attachment that no Exp 02 rubric received. Recall is 0% by construction.

- **Cast counting remains 0% recall.** Same finding as Exp 02. The vision
  model does not count people reliably from a panel-only input.

- **The refined taxonomy doesn't change Exp 02's headline.** v5 still has
  the precision tradeoff visible on the larger set; v3 still misses the
  subtler hair cases. The v1 contribution is not "better metrics" — it's
  "categories named more specifically so the rubric can target them."

## Per-category ship recommendation

(See [`recommendation.md`](recommendation.md) for the full per-category
recommendation derived from these metrics.)
