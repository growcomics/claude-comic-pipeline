# comic-production tests

Fixture-based + inline unit tests for `scripts/next_panel.py`. Mirrors the
shape of `skills/continuity-check/tests/`.

## Run

```bash
python tests/run_tests.py             # all fixtures + inline tests
python tests/run_tests.py --fixture compose-tier3-fullbody-pending  # one
python tests/run_tests.py --inline-only
python tests/run_tests.py --verbose   # dump composed prompts on failure
```

Exit 0 on full pass, 1 if anything fails.

## Layout

```
tests/
  run_tests.py             # driver — invokes build_plan + asserts
  fixtures/<name>/
    shotlist.json          # synthetic shotlist (looks like a real project)
    expected.json          # assertions about plan output + composed prompt
    references/...         # optional: face cards, env source refs
    pages/panels/<id>/...  # optional: accepted-history images
    production-config.json # optional: lineup_files overrides
```

## Expected schema

```json
{
  "description": "...",
  "expect_no_pending_panels": false,
  "expect_panel_id": "p1",
  "expect_stage_change": true,
  "expect_aspect": "3:4",
  "expect_prompt_contains": ["substring1", "substring2"],
  "expect_prompt_not_contains": ["substring3"],
  "expect_ref_kinds_in_order": ["face_card", "lineup"],
  "expect_ref_kinds_present": ["WARNING_MODEL_MUSCULARITY_CEILING"],
  "expect_ref_kinds_absent": ["env_ref"]
}
```

All fields are optional — fixtures assert only what they care about.

## What's covered

Functions under test (per GROA-19 scope):

| Function | Coverage |
|---|---|
| `compose_prompt()` | style prefix, mandatory rules, L21 ref-exclusion, L22 hair-state explicit-only (no auto-derive), L23 env-dense-anchor fallback, L24 accessory line, female-anatomy anchor on tier≥2 ecu-region, tier silhouette descriptor |
| `build_plan()` | 3-ref ceiling enforcement, ref attachment order, env-chaining-vs-source, no-pending-panels exit, grok-muscularity warning |
| `should_attach_lineup()` | L11 widening: attach on every full-body camera, not just stage-changes (regression for the deprecated L5 path) |
| `find_lineup()` | resolves repo asset, returns None when tier=None, no-phantom-refs rule (returned path always exists) |
| `pick_location_anchor()` | first panel → no anchor; subsequent same-location panel → returns prior accepted history item |
| `MODEL_MUSCULARITY_CEILING` | grok_image has cap; nano_banana_2 / gpt_image_2 do NOT |

## Out of scope (intentional gaps)

- Tests for the `runners/` infrastructure — separate issue.
- L14 multi-view env refs for shot-reverse-shot — still pending in CHANGELOG.
- Integration tests against a live Flow run.
- compose_prompt shape will change for [GROA-20] (L19 wire-through). Substring
  assertions here focus on the L21-L24 contracts; the camera-fragment shape
  itself is not pinned. When GROA-20 lands, the L19 substring assertion
  should be added in that PR.
