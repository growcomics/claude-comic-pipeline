"""Registry mapping rule_id -> Rule instance.

Restructured 2026-05-23 in the refs-are-truth refactor — rules are now
grouped into four category subpackages:

  attach/  — reference-image attachment rules (Category A)
  action/  — action / camera / lighting / state-delta rules (Category B)
  match/   — short "match the attached <ref>" directives (Category C)
  safety/  — negation / "do not render X" rules (Category D)

DELETED in this refactor (no longer L10-compliant — they emitted
appearance prose that should come from refs instead):
  - l15_glamour.py  (beauty is in the face card)
  - female_anatomy.py  (femaleness is in face card + body-tier refs)
  - l11_muscular_build.py (text directives — see match/match_body.py)
  - l17_canonical.py  (text directives — see match/match_face_card.py)
  - l10_render_directive.py (text directive — see match/match_face_card.py)
  - l22_hair_state.py (moved — see action/hair_state.py — STATE delta)
  - l18_anatomy.py (moved — see safety/anatomy_coherence.py)
  - l20_camera.py (moved — see action/camera_directive.py)
  - l21_ref_safety.py (moved — see safety/ref_safety.py)
  - l23_env_anchor.py (moved — see action/environment_directive.py)
  - l24_accessory.py (moved — see safety/accessory_suppression.py)
  - l29_tier6_reinforcement.py, l30_*, l31_*, l32_*
    (split: attach part → attach/tier_reinforcement.py;
            match part → match/match_body.py)
"""

from __future__ import annotations

from ._base import Rule

# Attach rules — reference image attachment, no prompt text
from .attach.face_card import AttachFaceCard
from .attach.body_tier import AttachBodyTier
from .attach.tier_reinforcement import AttachTierReinforcement
from .attach.env_ref import AttachEnvRef
from .attach.prior_panel import AttachPriorPanel
from .attach.internet_3d_base import AttachInternet3DBase

# Action rules — camera / lighting / state-delta text
from .action.camera_directive import L20
from .action.hair_state import L22
from .action.environment_directive import L23

# Match rules — short "match the attached <ref>" directives
from .match.match_face_card import L10, L17
from .match.match_body import L11, L29, L30, L31, L32
from .match.match_env import MatchEnv
from .match.match_prior_panel import L1

# Safety rules — negation / "do not render X"
from .safety.ref_safety import L21
from .safety.anatomy_coherence import L18
from .safety.accessory_suppression import L24


# Registration order matters for shared-slot rules (iter_rules_for_slot
# returns in this order). Attach rules come first by category so the
# refs-list builders see them before composer slots dispatch.
RULE_INSTANCES: list[Rule] = [
    # ATTACH (Category A)
    AttachFaceCard(),
    AttachBodyTier(),
    AttachTierReinforcement(),
    AttachEnvRef(),
    AttachPriorPanel(),
    AttachInternet3DBase(),

    # SAFETY (Category D)
    L21(),  # ref safety
    L18(),  # anatomy coherence
    L24(),  # accessory suppression

    # ACTION (Category B)
    L20(),  # camera directive
    L22(),  # hair state (per-panel delta)
    L23(),  # env fallback

    # MATCH (Category C)
    L17(),  # match canonical face card
    L11(),  # match body proportions (multi-slot)
    MatchEnv(),  # match env ref
    L1(),    # match prior panel for state continuity
    L29(),  # tier-6 reinforcement match
    L30(),  # tier-7 reinforcement match
    L31(),  # tier-8 reinforcement match
    L32(),  # tier-9 reinforcement match
    L10(),  # render directive ("match the attached refs")
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
    RULE_INSTANCES (stable)."""
    return [r for r in RULE_INSTANCES if slot in r.slots()]


def iter_rules_for_category(category: str) -> list[Rule]:
    """Rules in the given category, in registration order."""
    return [r for r in RULE_INSTANCES if r.category == category]
