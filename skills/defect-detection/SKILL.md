# defect-detection (skeleton)

**Status:** intent-only skeleton. Real implementation is a separate task
once Experiment 02 + Experiment 05 align on a shared rubric.

## What this skill is

A vision-audit skill that, given a locked comic panel + shotlist excerpt
+ canonical refs, returns which defect categories from
[`docs/experiments/05-defects-skill/taxonomy-v1.md`](../../docs/experiments/05-defects-skill/taxonomy-v1.md)
are present.

## What this skill is NOT

- Not a fine-tuned classifier — uses the Claude vision API directly
  against the rubric.
- Not a per-rule dispatcher — complementary to `audit_panels.py` (which
  dispatches per-rule vision rubrics for the L-rules registry).
- Not wired into autopilot acceptance — wiring is a separate task gated
  on a unified ship recommendation.

## Inputs

The skill expects the inputs documented in
[`detection-rubric-v1.md`](../../docs/experiments/05-defects-skill/detection-rubric-v1.md)
§ "Inputs the rubric expects at call time".

## Output

The JSON object documented in `detection-rubric-v1.md` § "Output format".
Each leaf returns `{detected, confidence, reason}`.

## Provenance

- **Taxonomy:** `docs/experiments/05-defects-skill/taxonomy-v1.md`
- **Rubric:** `docs/experiments/05-defects-skill/detection-rubric-v1.md`
- **Labeled corpus:** `docs/experiments/05-defects-skill/labeled-defects.json`
- **Measurement:** `docs/experiments/05-defects-skill/metrics-v1.md`
- **Ship recommendation per category:**
  `docs/experiments/05-defects-skill/recommendation.md`

## Why this is a skeleton

The brief for Experiment 05 explicitly says:

> If this lands as a skill: skeleton at `skills/defect-detection/SKILL.md`
> describing intent. Real implementation is a separate spawn after
> Experiment 02 + this one agree on a shared rubric.

The implementation work — actually wiring the rubric into a callable
script, hooking it into `audit_panels.py` or `vision_audit.py`,
adding per-category threshold knobs, producing `defects.jsonl` ledger
output — is the follow-up task. This file exists so the skill's
location and intent are reserved in the repo.
