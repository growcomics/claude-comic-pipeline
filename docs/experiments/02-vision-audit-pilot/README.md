# Experiment 02 — Vision Audit Pilot

**Hypothesis:** a minimal vision-audit pass running against locked panels can catch ≥80% of the defects Magnamus and Matt eyeball-catch, with ≤30% false-positive rate on good panels.

**Outcome:** **partially true; don't ship yet.** See [`recommendation.md`](recommendation.md) for the full writeup.

## Files

- [`labeled-set-v1.json`](labeled-set-v1.json) — 20 panels from `ultra-gal-origin` pages 1-7, labeled GOOD/BAD against the project's checked-in QA audit doc (`projects/ultra-gal-origin/audits/pages-01-07-audit-2026-05-16.md`).
- `rubric_v1.md` … `rubric_v5.md` — the rubric across 5 tuning iterations.
- `metrics-v1.md` … `metrics-v5.md` — per-iteration recall/precision tables + per-panel detail.
- `runs/raw-predictions-vN.jsonl` — the raw model verdicts for each iteration.
- `runs/metrics-vN.json` — machine-readable metrics.
- [`recommendation.md`](recommendation.md) — final findings + recommendation.

## The script

[`skills/continuity-check/scripts/vision_audit.py`](../../../skills/continuity-check/scripts/vision_audit.py) — the production-shaped runner. Two modes:

```bash
# Live mode (production) — needs ANTHROPIC_API_KEY
python3 vision_audit.py \
    --labeled-set docs/experiments/02-vision-audit-pilot/labeled-set-v1.json \
    --rubric docs/experiments/02-vision-audit-pilot/rubric_v3.md \
    --out-dir docs/experiments/02-vision-audit-pilot/runs/ \
    --run-tag v3-live

# Score-only mode (offline, from pre-computed predictions)
python3 vision_audit.py \
    --labeled-set docs/experiments/02-vision-audit-pilot/labeled-set-v1.json \
    --rubric docs/experiments/02-vision-audit-pilot/rubric_v3.md \
    --score-from docs/experiments/02-vision-audit-pilot/runs/raw-predictions-v3.jsonl \
    --out-dir docs/experiments/02-vision-audit-pilot/runs/ \
    --run-tag v3
```

In this experiment, predictions were produced via Claude Code sub-agents (the harness blanks `ANTHROPIC_API_KEY`) and consumed via `--score-from`. The live-mode path is exercised by the dry-run and is the production code path.

## Headline metrics

```
ver  acc   good  bad    hair-r  hair-p  cost-r  cost-p  lett-r  lett-p
v1   60%   75%   50%    0%      n/a     100%    57%     67%     100%
v2   65%   88%   50%    0%      n/a     75%     60%     100%    100%
v3   75%   88%   67%    33%     25%     100%    67%     100%    100%
v4   55%   75%   42%    33%     100%    25%     50%     100%    75%
v5   60%   50%   67%    100%    38%     75%     43%     67%     100%
```

**No single rubric hits the stop condition** (recall ≥ 80% on every HIGH-priority category in one run). v3 was the best-balanced; v5 unlocked hair recall at the cost of precision; v4 backfired.

## Not wired

Per the experiment spec, the audit script lands on this branch but is **NOT wired into autopilot acceptance**. Wiring it in spends regen credits and is a separate decision after the recommendation is acted on. The existing `skills/comic-production/scripts/audit_panels.py` (per-rule vision dispatch) is the related production layer; the new `vision_audit.py` is a holistic alternative.
