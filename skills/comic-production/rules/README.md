# Per-rule modules

Each active L-rule from `lessons-learned.md` becomes a discrete module under this directory. The registry (`_registry.RULES`) maps rule_id → Rule instance; composer call sites in `next_panel.compose_prompt` delegate here instead of inlining rule logic.

See [`docs/checks-and-balances-design.md`](../../../docs/checks-and-balances-design.md) for the full design. Section 3.A covers the `Rule` interface; section 3.C covers the verification taxonomy.

## Status

| File | Rule | Phase migrated | Notes |
|---|---|---|---|
| `l21_ref_safety.py` | L21 — Suppress in-scene rendering of refs | **phase 2** | First migrated. Single slot (`12_ref_safety`). |
| (TODO) `l18_anatomy.py` | L18 — Pose anatomy coherence | phase 3 | Always-emit. Universal soft guardrail. |
| (TODO) `l20_camera.py` | L20 — Camera distance bias | phase 3 | Two-piece: in-prompt directive + chapter-aggregate check. |
| (TODO) `l15_glamour.py` | L15 — Female beauty anchor | phase 3 | `applicable_transformations=("fmg",)`. |
| (TODO) `l17_canonical.py` | L17 — Canonical character | phase 3 | Reads `cast[].canonical_anchor`. |
| (TODO) `l22_hair_state.py` | L22 — Hair state explicit | phase 3 | Reads `panel.hair_state`. |
| (TODO) `l23_env_anchor.py` | L23 — Verbal env anchor when ref dropped | phase 3 | Fires when env_dropped=True. |
| (TODO) `l24_accessory.py` | L24 — Suppress anachronistic accessories | phase 3 | Reads `cast[].accessories`. |
| (TODO) `l11_silhouette.py` | L11 — Cartoony FMG anchoring | phase 3 | Two slots: style anchor + tier silhouette. FMG-only initially. |
| (TODO) `l10_render_directive.py` | L10 — Refs are truth, prompts are deltas | phase 3 | The load-bearing render directive. Always emit. |
| (TODO) `female_anatomy.py` | Female anatomy anchor (May-14 finding) | phase 3 | FMG-only. Body-region ECU at tier≥2. |

Phase 4 adds pre-render verification (migrating `rules_audit.py` checks into rule modules). Phase 5 adds post-render vision verification. Phase 6 adds retry strategies.

## Adding a new rule

1. Create `lNN_<slug>.py` exposing a class that subclasses `_base.Rule`. Set class attributes (`id`, `title`, `slot`, `applicable_transformations`, `severity`). Implement `should_apply` and `compose_contribution`. Override `verify_pre_render` / `verify_post_render` / `retry_strategy` as needed.
2. Register the instance in `_registry.RULE_INSTANCES`.
3. Replace the inline helper site in `next_panel.compose_prompt` with a registry-driven call.
4. Run the golden-output test (the composed prompt must remain byte-identical against the historical corpus).

## Genre extensibility

Every rule declares `applicable_transformations`. The registry doesn't pre-filter — callers do, via `rule.applies_to_transformation(transformation_type)`. The transformation type is read from `production-config.json -> transformation_type` (defaults to `"fmg"` for legacy projects).

`("*",)` = applies to every project. `("fmg",)` = FMG-only. Adding BE / glute / MMG variants = new modules with the same `lNN_<slug>` shape — don't add complexity inside the FMG module to support other transformations.
