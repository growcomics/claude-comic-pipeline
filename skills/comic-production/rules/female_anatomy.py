"""Female-anatomy anchor on body-region ECUs at tier ≥ 2 (May-14 finding).

Body-region ECUs on a heavily muscular female character drift to male
anatomy (square pectorals, flat-plane chest, no breast contour) when the
face is off-frame. Caught on chun-li-grok-validation p5 (tier 5 abs ECU
rendered male).

Conditions for firing:
  - camera is `ecu-region`
  - panel.muscle_size_tier >= 2
  - the panel's first arc character is female (sex == "f", pronoun in
    {"she","her"}, or both unset and default-true)

FMG-only initially. A future MMG-anatomy module would live in a parallel
file (e.g. male_anatomy.py) and never share state.

See:
  - skills/comic-production/CHANGELOG entry 2026-05-14 (Grok validation)
  - skills/comic-production/scripts/next_panel.py history (legacy
    implementation removed in phase 3)
"""

from __future__ import annotations

from ._base import Rule, Verification, STATUS_PASS, STATUS_SKIPPED


FEMALE_ANATOMY_ANCHOR = (
    "Female anatomy anchor: the body is unambiguously FEMALE despite the "
    "hyper-developed muscle. Feminine bone structure, visible breast "
    "contour where the chest is in or near frame, feminine waist taper "
    "above the hips, smaller hands and wrists than a male equivalent, "
    "soft feminine collarbone line. NOT a male body — no square male "
    "pectorals, no flat-plane male upper chest."
)


def _arc_character_is_female(panel: dict, cast_lookup: dict) -> bool:
    chars = panel.get("characters", []) or []
    if not chars:
        return False
    char = cast_lookup.get(chars[0])
    if not char:
        return False
    sex = (char.get("sex") or "").lower()
    if sex in ("f", "female"):
        return True
    if sex in ("m", "male"):
        return False
    pronoun = (char.get("pronoun") or "").lower()
    if pronoun in ("she", "she/her", "her"):
        return True
    if pronoun in ("he", "he/him", "him"):
        return False
    return True  # default-true for FMG-heavy projects


def _female_anatomy_anchor_needed(panel: dict, cast_lookup: dict, camera: str) -> bool:
    if camera != "ecu-region":
        return False
    tier = panel.get("muscle_size_tier")
    if tier is None:
        return False
    try:
        if int(tier) < 2:
            return False
    except (TypeError, ValueError):
        return False
    return _arc_character_is_female(panel, cast_lookup)


class FemaleAnatomy(Rule):
    id = "female_anatomy"
    title = "Female anatomy anchor on body-region ECUs (May 14 lesson)"
    slot = "4_subject_state"
    section_label = "FEMALE ANATOMY"
    severity = "hard"
    applicable_transformations = ("fmg",)
    vision_rubric = (
        "Look at this rendered comic panel — it's a body-region ECU (e.g. "
        "chest, abs, arms) at high muscle tier (tier >= 2) where the "
        "character should be unambiguously female despite the hyper-developed "
        "muscle. Does the rendered body read as FEMALE? Check: visible "
        "breast contour (when chest is in or near frame), feminine collarbone, "
        "feminine waist taper above the hips, smaller hands and wrists than "
        "a male equivalent, soft feminine bone structure. Or did the body "
        "regress to male anatomy — square male pectorals, flat-plane upper "
        "chest, masculine collarbone? PASS if the body unambiguously reads "
        "female. FAIL with a description if the body reads as male/masculinized."
    )

    def should_apply(self, panel: dict, ctx: dict) -> bool:
        camera = ctx.get("camera") or ""
        cast_lookup = ctx.get("cast_lookup") or {}
        return _female_anatomy_anchor_needed(panel, cast_lookup, camera)

    def compose_contribution(self, panel: dict, ctx: dict, slot: str) -> str | None:
        if slot != "4_subject_state":
            return None
        if not self.should_apply(panel, ctx):
            return None
        return FEMALE_ANATOMY_ANCHOR

    def verify_pre_render(self, panel: dict, ctx: dict) -> Verification:
        camera = ctx.get("camera") or ""
        tier = panel.get("muscle_size_tier")
        if self.should_apply(panel, ctx):
            return Verification(
                status=STATUS_PASS,
                reason=(f"camera=ecu-region tier>=2 female cast (tier={tier})"),
            )
        return Verification(
            status=STATUS_SKIPPED,
            reason=(f"not a body-region ECU tier>=2 with female cast "
                    f"(camera={camera!r}, tier={tier})"),
        )

    def retry_strategy(self, panel: dict, ctx: dict, failure: dict) -> dict:
        return {
            "kind": "auto_resubmit_with_stronger_contribution",
            "rule_id": self.id,
            "strengthening": (
                "double down on the female-anatomy negation: 'this is a "
                "female torso — visible breast tissue, feminine collarbone, "
                "feminine waist. NOT a male chest. NOT a flat pectoral plane. "
                "The breast contour MUST be visible.'"
            ),
        }
