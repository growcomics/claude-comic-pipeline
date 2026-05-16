"""Per-rule modules for the checks-and-balances architecture.

Phase 2 of the refactor (see docs/checks-and-balances-design.md). Each L-rule
becomes a discrete module with a uniform interface (see `_base.Rule`). The
registry (`_registry.RULES`) maps rule_id -> Rule instance. Composer call
sites in `next_panel.compose_prompt` delegate to the registry instead of
inlining rule logic.

Phase 2 ships only L21 through this path; every other rule still routes
through the legacy helpers in `next_panel.py`. Phase 3 migrates the rest of
the active rules (L18, L20, L15, L17, L22, L23, L24, L11, L10) one at a
time, with byte-identical golden-output tests at each step.

Adding a new rule:

  1. Create rules/lNN_<slug>.py exposing a class that subclasses
     `_base.Rule`. Set class attributes id, title, slot,
     applicable_transformations, severity. Implement should_apply,
     compose_contribution, verify_pre_render at minimum.
  2. Register it in `_registry.RULES` by importing the class and
     instantiating it in the RULE_INSTANCES list.
  3. Replace the inline helper site in `next_panel.compose_prompt` with a
     registry-driven call that asks the rule for its contribution at its
     slot.
  4. Run the golden-output test (cmp composed_prompt before/after on the
     historical corpus).

Genre extensibility: every rule declares applicable_transformations. The
registry filters by `production-config.json -> transformation_type` (defaults
to "fmg"). Rules with `["*"]` apply to every project; rules with
`["fmg"]` skip on non-FMG projects. Adding BE / glute / MMG variants =
new modules with the same `lNN_<slug>` shape, not surgery on existing ones.
"""
