# Per-rule modules

Each active L-rule from `lessons-learned.md` becomes a discrete module under this directory. The registry (`_registry.RULES`) maps rule_id → Rule instance; composer call sites in `next_panel.compose_prompt` delegate here instead of inlining rule logic.

See [`docs/checks-and-balances-design.md`](../../../docs/checks-and-balances-design.md) for the full design. Section 3.A covers the `Rule` interface; section 3.C covers the verification taxonomy.

## Status

All active L-rules are migrated to per-rule modules. Every rule contribution to `compose_prompt` now flows through `_registry.RULES`.

| File | Rule | Phase | Notes |
|---|---|---|---|
| `l21_ref_safety.py` | L21 — Suppress in-scene rendering of refs | phase 2 | Slot `12_ref_safety`. Universal. |
| `l18_anatomy.py` | L18 — Pose anatomy coherence | phase 3a | Slot `13_anatomy_guardrail`. Always-emit universal soft guardrail. |
| `l10_render_directive.py` | L10 — Refs are truth, prompts are deltas | phase 3a | Slot `11_render_directive`. Always-emit. The load-bearing render directive. |
| `l20_camera.py` | L20 — Camera distance bias (in-prompt directive) | phase 3a | Slot `2_camera_strengthening`. Body-region beats. Chapter-aggregate L20 check still lives in build_plan as `L20_chapter`; phase 4 migrates that. |
| `l22_hair_state.py` | L22 — Hair state explicit | phase 3a | Slot `4_subject_state`. Reads `panel.hair_state`. |
| `l23_env_anchor.py` | L23 — Verbal env anchor when env_ref dropped | phase 3a | Slot `9_environment`. Fires when env_ref=None + env_dropped + location_slug set. |
| `l24_accessory.py` | L24 — Suppress anachronistic accessories | phase 3a | Slot `4_subject_state`. Reads `cast[].accessories`. |
| `l15_glamour.py` | L15 — Female beauty anchor | phase 3a | Slot `3_subject_identity`. `applicable_transformations=("fmg",)`. |
| `l17_canonical.py` | L17 — Canonical character | phase 3a | Slot `3_subject_identity`. Reads `cast[].canonical_anchor`. |
| `female_anatomy.py` | Female anatomy anchor (May-14 finding) | phase 3a | Slot `4_subject_state`. `applicable_transformations=("fmg",)`. Body-region ECU at tier≥2. |
| `l11_silhouette.py` | L11 — Cartoony FMG anchoring | phase 3b | **Only multi-slot rule.** Slots `5_style_anchor` + `8_tier_silhouette`. `applicable_transformations=("fmg",)`. Tier-specific block depends on `lineup_attached` / `stage_change`. |

Multi-slot rules: the helper `next_panel._apply_rule_at_slot` injects `_active_slot` into ctx so `verify_pre_render` can branch per slot. Compose-side ordering: `compose_prompt` issues two explicit `_apply_rule_at_slot` calls for L11 (one per slot) at the right places in the function.

Phase 4 adds pre-render verification (migrating `rules_audit.py` checks into rule modules — moves `L20_chapter`, `L13`, `L12`, `L28`, etc.). Phase 5 adds post-render vision verification. Phase 6 adds retry strategies.

## Adding a new rule

1. Create `lNN_<slug>.py` exposing a class that subclasses `_base.Rule`. Set class attributes (`id`, `title`, `slot`, `applicable_transformations`, `severity`). Implement `should_apply` and `compose_contribution`. Override `verify_pre_render` / `verify_post_render` / `retry_strategy` as needed.
2. Register the instance in `_registry.RULE_INSTANCES`.
3. Replace the inline helper site in `next_panel.compose_prompt` with a registry-driven call.
4. Run the golden-output test (the composed prompt must remain byte-identical against the historical corpus).

## Genre extensibility

Every rule declares `applicable_transformations`. The registry doesn't pre-filter — callers do, via `rule.applies_to_transformation(transformation_type)`. The transformation type is read from `production-config.json -> transformation_type` (defaults to `"fmg"` for legacy projects).

`("*",)` = applies to every project. `("fmg",)` = FMG-only. Adding BE / glute / MMG variants = new modules with the same `lNN_<slug>` shape — don't add complexity inside the FMG module to support other transformations.
