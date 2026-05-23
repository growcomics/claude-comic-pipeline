# Experiment 02 — Vision Audit Pilot — Recommendation

**Status:** experiment complete. 5 iterations attempted. Stop condition (recall ≥ 80% on every HIGH-priority category in a single run) NOT MET. Strong findings either way.

**Date:** 2026-05-22
**Author:** Claude (spawned task)
**Branch:** `experiment/02-vision-audit-pilot`

---

## Headline

**Iterate, don't ship yet. The vision audit can clearly catch real defects — but no single rubric setting hits the HIGH-priority recall threshold on every category. There's a precision/recall tradeoff the rubric alone cannot collapse, and the labeled set is too narrow to make a confident production decision.**

Specifically:
- `costume_discontinuity` is consistently detectable at high recall (75%-100% across v1, v2, v3, v5) — the audit catches Heather-in-navy-not-green reliably.
- `hair_discontinuity` is detectable but the precision/recall point depends sharply on rubric confidence semantics (0% → 33% → 100% recall as we tuned, with precision crashing to 38% at the high-recall point).
- `composite_mismatch` and `scale_error` — the other two HIGH categories — had **zero examples** in the labeled set, so we cannot certify them at all. That's a labeled-set gap, not a model gap.
- `character_count_error` and `character_identity_swap` were **0% recall across all 5 iterations**. The vision model is not catching these defects.

## Summary metrics

```
ver  acc   good  bad    hair-r  hair-p  cost-r  cost-p  lett-r  lett-p
v1   60%   75%   50%    0%      n/a     100%    57%     67%     100%
v2   65%   88%   50%    0%      n/a     75%     60%     100%    100%
v3   75%   88%   67%    33%     25%     100%    67%     100%    100%
v4   55%   75%   42%    33%     100%    25%     50%     100%    75%
v5   60%   50%   67%    100%    38%     75%     43%     67%     100%
```

Best single-version balance: **v3** (75% total accuracy, 100% costume recall + 67% costume precision, 33% hair recall). v3's rubric added canonical face cards alongside the panel — that was the biggest single-iteration improvement (+10pp accuracy over v2).

Best hair recall: **v5** (100% hair recall, but precision 38% and total accuracy drops to 60%).

## What the audit catches reliably

- **`lettering_error`** — typos, doubled words, duplicate bubbles. 67-100% recall, 75-100% precision across iterations. v2 onward catches "MAAM, MAAM" word-doubling and identical adjacent bubbles.
- **`costume_discontinuity`** for explicit canonical-vs-actual mismatches (e.g. Heather wearing navy instead of canonical green). 75-100% recall on v1, v2, v3, v5.
- **`hair_discontinuity`** when face cards are passed alongside the panel AND the rubric anchors confidence semantics correctly (v5). 100% recall but precision falls — model also flags hair drift on panels where the audit only labeled costume drift (which could be true positives the audit doc undercounted, or could be model over-detection — needs human re-labeling to resolve).

## What the audit doesn't catch

- **`character_count_error`** — 0% recall across all 5 versions. The model didn't notice when Heather is entirely missing from a 2-character scene (p05-02) or when her mirroring arm is missing (p05-04). This suggests the rubric can't make the model count people reliably — or that the visual-area-based detection is fundamentally hard for ECU-region crops.
- **`character_identity_swap`** — 0% recall (only 1 example, but consistently missed). The Lenny↔Carl swap on p02-02 went undetected even with explicit "Lenny=dark+blue overalls, Carl=blonde+brown overalls" in the rubric. The model called the panel character_count_error in v1 (noticed someone was off) but never connected it to the swap.
- **`empty_speech_bubble`** (tail-points-to-wrong-character variant) — 0% recall (1 example). The p01-03 bubble that visually attaches to the BLONDE Carl but contains dialogue script-attributed to dark-haired Lenny wasn't flagged across any version.

## What we couldn't measure

- **`composite_mismatch`** — 0 labeled examples in v1 set. Cannot certify recall.
- **`scale_error`** — 0 labeled examples in v1 set. Cannot certify recall.
- **`tier_visualization_mismatch`** — 0 labeled examples. (Not surprising; the labeled set is pages 1-7 ultra-gal-origin, all pre-transformation civilian scenes.)
- **`prompt_bloat_artifact`** — 0 labeled examples.

These four uncertified categories represent half the HIGH-priority list (`composite_mismatch` and `scale_error` are HIGH). **Half the experiment's HIGH categories are unmeasured.** That's the biggest reason to not ship yet.

## Key methodological caveats

1. **Single project source.** All 20 labeled panels came from one project (`ultra-gal-origin`) because it's the only one in this checkout with accepted panels AND a checked-in per-panel audit doc. We cannot assess generalization.

2. **LLM-in-the-loop labels.** Labels were derived from a Claude-subagent-authored audit doc that Matt committed but did not personally re-author per panel. When the vision audit agrees, that could be two LLMs agreeing rather than a tool catching real defects. Future iterations need independent labels from Matt/Magnamus directly — ideally one of them spends 30 minutes labeling 30-50 new panels by eyeball, with no LLM in the loop.

3. **Predictions produced via Claude Code sub-agents, not the script's API path.** The harness blanks `ANTHROPIC_API_KEY` in subshells, so the actual `vision_audit.py --labeled-set` mode could not be executed end-to-end. Predictions were produced by spawning sub-agents that loaded the rubric + face cards + panels via the Read tool, applied the rubric, and wrote JSONL. This mirrors what the production-API call would produce but isn't byte-identical. The script's `score_from_existing` mode is what consumed those predictions for metrics.

4. **Tuning was on the same set we measured against.** Iterations v2-v5 were tuned by looking at v1+ failures and adjusting the rubric. This is the standard pattern but could overfit. The remedy is to hold out a second labeled set Matt/Magnamus produce, and re-measure the best rubric (v3 OR v5) on the holdout before any production wiring.

## Specific next-step recommendations

### Don't ship — iterate. Specifically, collect more labeled data in these three buckets:

1. **5-10 labeled `composite_mismatch` panels.** Hand-pick panels where the foreground subject and background were clearly composited / re-lit / the lighting doesn't match. Examples worth hunting for: any panel where a character ref was attached for foreground but the environment ref dictates a different time-of-day or light direction. This is a HIGH category we cannot certify with v1's labels.

2. **5-10 labeled `scale_error` panels.** Hand-pick panels where background extras are obviously the wrong scale (huge or tiny relative to perspective). The qa-checklist.md "No background extras" check should generate these as a byproduct.

3. **20-30 mixed GOOD/BAD panels from at least 3 other projects** (`chun-li-test`, `emma-frost-ascension`, `bryn-anvil-of-ages` — whichever Matt has handy). Label them by eyeball, no LLM. This is the cross-project generalization test that v1's single-project set cannot do.

After those labels exist, re-run v3 (the best-balanced rubric) and v5 (the best-recall rubric) on the combined set. If v3 holds at ≥80% recall on every HIGH category — ship v3 at MED+HIGH threshold (current default). If only v5 hits HIGH recall, then we have a real precision/recall tradeoff to surface to Matt and let him pick the threshold.

### If/when shipping, ship with:

- **Rubric: v3 + v5's confidence semantics block.** The face cards are non-negotiable (v3's biggest win). v5's confidence-semantics anchoring is the right "don't down-shift to LOW when you see drift" instruction, applied to hair_discontinuity specifically — but NOT generalized to all categories (that's what made v4 backfire).
- **Threshold: configurable per-category.** Hair benefits from a lower threshold (`detected: any`); costume needs MED+HIGH to avoid false alarms; composite/scale needs more data before we know.
- **Output: HARD findings for HIGH+precision categories, SOFT findings for the rest.** Map detections to the existing `defects.jsonl` ledger shape so the autopilot can consume them.
- **Wiring: separate task, not this one.** Per the experiment spec, the audit script lands HERE but does NOT get wired into autopilot acceptance. That decision needs its own task with Matt's signoff because it spends generation credits on regen.

### Pivots to consider (if iteration doesn't unlock):

- **For `character_count_error`:** add a deterministic "expected cast size from shotlist" check BEFORE the vision audit. If the shotlist says 2 characters and the vision audit sees only 1, that's a HARD finding. The vision pass would only need to count visible figures.
- **For `character_identity_swap`:** pass Lenny + Carl face cards (not just text descriptions) the same way v3 did for Heather + Mundy. Wasn't done here because their face cards weren't readily available; that's the obvious next thing to try.
- **For `empty_speech_bubble` (misdirected tail):** vision audit is probably the wrong tool. A vector-overlay-aware page-composer check that knows which character each bubble was assigned to (then checks bubble-tail-endpoint character matches the assigned speaker) is more reliable than vision inference.

## Conclusion

The experiment validates the hypothesis as PARTIALLY TRUE: a vision audit can catch real defects (costume, lettering reliably; hair with face cards + careful confidence semantics). But it doesn't yet hit the ≥80% recall threshold on every HIGH category in a single run, and four of the ten categories (including two HIGH ones) have zero labeled examples.

Don't ship the audit yet. Don't pivot away from vision either. Spend a half-day getting Matt or Magnamus to hand-label 20-30 more panels across the four under-tested categories, re-run the best rubric, and re-decide.
