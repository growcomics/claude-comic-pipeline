# Vision Audit — Metrics v5

**Run tag:** `v5`
**Rubric:** `docs/experiments/02-vision-audit-pilot/rubric_v5.md`
**Labeled set:** v1 — 20 panels (8 GOOD / 12 BAD)

## Overall

- Total panels: 20
- GOOD predicted GOOD: **4/8** (50%)
- BAD predicted BAD:   **8/12** (67%)
- Total accuracy:      **60%**

## Per-defect-category

| Category | Priority | Support (BAD) | TP | FP | FN | Recall | Precision |
|---|---|---|---|---|---|---|---|
| `composite_mismatch` | HIGH | 0 | 0 | 0 | 0 | n/a | n/a |
| `hair_discontinuity` | HIGH | 3 | 3 | 5 | 0 | 100% | 38% |
| `costume_discontinuity` | HIGH | 4 | 3 | 4 | 1 | 75% | 43% |
| `scale_error` | HIGH | 0 | 0 | 0 | 0 | n/a | n/a |
| `empty_speech_bubble` | med/low | 1 | 0 | 0 | 1 | 0% | n/a |
| `tier_visualization_mismatch` | med/low | 0 | 0 | 0 | 0 | n/a | n/a |
| `prompt_bloat_artifact` | med/low | 0 | 0 | 0 | 0 | n/a | n/a |
| `lettering_error` | med/low | 3 | 2 | 0 | 1 | 67% | 100% |
| `character_count_error` | med/low | 2 | 0 | 0 | 2 | 0% | n/a |
| `character_identity_swap` | med/low | 1 | 0 | 0 | 1 | 0% | n/a |

## HIGH-priority recall (stop-condition check)

The experiment's stop condition is **recall ≥ 80% on every HIGH-priority category** (composite_mismatch, hair_discontinuity, costume_discontinuity, scale_error).

- `composite_mismatch`: **n/a** (0 BAD examples in labeled set — cannot measure)
- `costume_discontinuity`: recall 75% (3/4) — **FAIL**
- `hair_discontinuity`: recall 100% (3/3) — **PASS**
- `scale_error`: **n/a** (0 BAD examples in labeled set — cannot measure)

**Stop-condition: NOT MET** — recall < 80% on: costume_discontinuity

## Per-panel detail

| Panel | Label | Labeled defects | Detected (high/med) | Notes |
|---|---|---|---|---|
| `p01-02` | GOOD | — | (none) | clean |
| `p01-03` | BAD | empty_speech_bubble, lettering_error | lettering_error(m) | hits: lettering_error; missed: empty_speech_bubble;  |
| `p02-01` | GOOD | — | costume_discontinuity(m) | FALSE ALARMS: costume_discontinuity |
| `p02-02` | BAD | character_identity_swap, lettering_error | lettering_error(h) | hits: lettering_error; missed: character_identity_swap;  |
| `p02-03` | BAD | costume_discontinuity | costume_discontinuity(m) | hits: costume_discontinuity;  |
| `p02-04` | BAD | hair_discontinuity | hair_discontinuity(m) | hits: hair_discontinuity;  |
| `p03-04` | GOOD | — | costume_discontinuity(h) | FALSE ALARMS: costume_discontinuity |
| `p04-01` | BAD | lettering_error | hair_discontinuity(m), costume_discontinuity(h) | missed: lettering_error; extra: hair_discontinuity,costume_discontinuity |
| `p04-02` | GOOD | — | costume_discontinuity(h) | FALSE ALARMS: costume_discontinuity |
| `p04-03` | GOOD | — | (none) | clean |
| `p04-04` | BAD | costume_discontinuity | hair_discontinuity(m), costume_discontinuity(h) | hits: costume_discontinuity; extra: hair_discontinuity |
| `p05-01` | BAD | costume_discontinuity | hair_discontinuity(m), costume_discontinuity(h) | hits: costume_discontinuity; extra: hair_discontinuity |
| `p05-02` | BAD | character_count_error | (none) | missed: character_count_error;  |
| `p05-03` | GOOD | — | hair_discontinuity(m) | FALSE ALARMS: hair_discontinuity |
| `p05-04` | BAD | character_count_error | (none) | missed: character_count_error;  |
| `p06-01` | GOOD | — | (none) | clean |
| `p06-02` | BAD | costume_discontinuity | hair_discontinuity(m) | missed: costume_discontinuity; extra: hair_discontinuity |
| `p06-03` | GOOD | — | (none) | clean |
| `p06-04` | BAD | hair_discontinuity | hair_discontinuity(m) | hits: hair_discontinuity;  |
| `p07-01` | BAD | hair_discontinuity | hair_discontinuity(m) | hits: hair_discontinuity;  |

