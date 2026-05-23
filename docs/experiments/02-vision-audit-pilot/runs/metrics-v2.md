# Vision Audit — Metrics v2

**Run tag:** `v2`
**Rubric:** `docs/experiments/02-vision-audit-pilot/rubric_v2.md`
**Labeled set:** v1 — 20 panels (8 GOOD / 12 BAD)

## Overall

- Total panels: 20
- GOOD predicted GOOD: **7/8** (88%)
- BAD predicted BAD:   **6/12** (50%)
- Total accuracy:      **65%**

## Per-defect-category

| Category | Priority | Support (BAD) | TP | FP | FN | Recall | Precision |
|---|---|---|---|---|---|---|---|
| `composite_mismatch` | HIGH | 0 | 0 | 0 | 0 | n/a | n/a |
| `hair_discontinuity` | HIGH | 3 | 0 | 0 | 3 | 0% | n/a |
| `costume_discontinuity` | HIGH | 4 | 3 | 2 | 1 | 75% | 60% |
| `scale_error` | HIGH | 0 | 0 | 0 | 0 | n/a | n/a |
| `empty_speech_bubble` | med/low | 1 | 0 | 0 | 1 | 0% | n/a |
| `tier_visualization_mismatch` | med/low | 0 | 0 | 0 | 0 | n/a | n/a |
| `prompt_bloat_artifact` | med/low | 0 | 0 | 0 | 0 | n/a | n/a |
| `lettering_error` | med/low | 3 | 3 | 0 | 0 | 100% | 100% |
| `character_count_error` | med/low | 2 | 0 | 0 | 2 | 0% | n/a |
| `character_identity_swap` | med/low | 1 | 0 | 0 | 1 | 0% | n/a |

## HIGH-priority recall (stop-condition check)

The experiment's stop condition is **recall ≥ 80% on every HIGH-priority category** (composite_mismatch, hair_discontinuity, costume_discontinuity, scale_error).

- `composite_mismatch`: **n/a** (0 BAD examples in labeled set — cannot measure)
- `costume_discontinuity`: recall 75% (3/4) — **FAIL**
- `hair_discontinuity`: recall 0% (0/3) — **FAIL**
- `scale_error`: **n/a** (0 BAD examples in labeled set — cannot measure)

**Stop-condition: NOT MET** — recall < 80% on: costume_discontinuity, hair_discontinuity

## Per-panel detail

| Panel | Label | Labeled defects | Detected (high/med) | Notes |
|---|---|---|---|---|
| `p01-02` | GOOD | — | (none) | clean |
| `p01-03` | BAD | empty_speech_bubble, lettering_error | lettering_error(h) | hits: lettering_error; missed: empty_speech_bubble;  |
| `p02-01` | GOOD | — | (none) | clean |
| `p02-02` | BAD | character_identity_swap, lettering_error | lettering_error(h) | hits: lettering_error; missed: character_identity_swap;  |
| `p02-03` | BAD | costume_discontinuity | costume_discontinuity(h) | hits: costume_discontinuity;  |
| `p02-04` | BAD | hair_discontinuity | (none) | missed: hair_discontinuity;  |
| `p03-04` | GOOD | — | (none) | clean |
| `p04-01` | BAD | lettering_error | costume_discontinuity(m), lettering_error(h) | hits: lettering_error; extra: costume_discontinuity |
| `p04-02` | GOOD | — | costume_discontinuity(m) | FALSE ALARMS: costume_discontinuity |
| `p04-03` | GOOD | — | (none) | clean |
| `p04-04` | BAD | costume_discontinuity | costume_discontinuity(m) | hits: costume_discontinuity;  |
| `p05-01` | BAD | costume_discontinuity | (none) | missed: costume_discontinuity;  |
| `p05-02` | BAD | character_count_error | (none) | missed: character_count_error;  |
| `p05-03` | GOOD | — | (none) | clean |
| `p05-04` | BAD | character_count_error | (none) | missed: character_count_error;  |
| `p06-01` | GOOD | — | (none) | clean |
| `p06-02` | BAD | costume_discontinuity | costume_discontinuity(m) | hits: costume_discontinuity;  |
| `p06-03` | GOOD | — | (none) | clean |
| `p06-04` | BAD | hair_discontinuity | (none) | missed: hair_discontinuity;  |
| `p07-01` | BAD | hair_discontinuity | (none) | missed: hair_discontinuity;  |

