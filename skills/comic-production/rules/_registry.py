"""Registry mapping rule_id -> Rule instance.

Phase 2 ships only L21. Phase 3 migrates L18, L20, L15, L17, L22, L23, L24,
L11, L10 one at a time, with byte-identical golden-output tests at each step.

The registry is the only place that needs to know which rules exist. Composer
call sites look up by rule_id and ask the rule for its contribution. Audit
walkers iterate over RULES.values() and dispatch verify_pre_render /
verify_post_render.

A rule's `applicable_transformations` is consulted by callers via
`Rule.applies_to_transformation(transformation_type)`. The registry itself
doesn't pre-filter — callers do, with the rule's help.
"""

from __future__ import annotations

from ._base import Rule
from .l21_ref_safety import L21
from .l18_anatomy import L18
from .l10_render_directive import L10
from .l20_camera import L20
from .l22_hair_state import L22
from .l23_env_anchor import L23
from .l24_accessory import L24
from .l15_glamour import L15
from .l17_canonical import L17
from .female_anatomy import FemaleAnatomy
from .l11_muscular_build import L11
from .l29_tier6_reinforcement import L29
from .l30_tier7_reinforcement import L30
from .l31_tier8_reinforcement import L31
from .l32_tier9_reinforcement import L32
from .l35_growth_intensity import L35


# Phase 3b — every active L-rule migrated to its own module. compose_prompt
# now routes ALL rule contributions through this registry. The legacy
# inline helpers in next_panel.py are dead code (left in place for
# backwards compat; phase 3 cleanup will prune them).
RULE_INSTANCES: list[Rule] = [
    L21(),
    L18(),
    L10(),
    L20(),
    L22(),
    L23(),
    L24(),
    L15(),
    L17(),
    FemaleAnatomy(),
    L11(),
    L29(),
    L30(),
    L31(),
    L32(),
    L35(),
]


RULES: dict[str, Rule] = {rule.id: rule for rule in RULE_INSTANCES}


def get_rule(rule_id: str) -> Rule | None:
    """Look up a rule by its id. Returns None if not registered."""
    return RULES.get(rule_id)


def iter_rules() -> list[Rule]:
    """All registered rules, in registration order."""
    return list(RULE_INSTANCES)


def iter_rules_for_slot(slot: str) -> list[Rule]:
    """Rules whose slot includes the given slot name. Order follows
    RULE_INSTANCES (stable). When phase 3 has multiple rules per slot, the
    composition order within a slot is the list order here.
    """
    return [r for r in RULE_INSTANCES if slot in r.slots()]
