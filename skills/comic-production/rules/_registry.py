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


# Phase 3a — all single-slot rules migrated. Phase 3b adds L11 (the only
# multi-slot rule). After phase 3b, compose_prompt is purely a registry
# walker and the legacy inline helpers in next_panel.py are removed.
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
