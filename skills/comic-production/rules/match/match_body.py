"""Match the attached body-tier references.

Pre-refactor, five rules emitted prose describing body proportions to
the model: L11 (style anchor + tier build prose, up to ~1900 chars per
panel) and L29/L30/L31/L32 (tier-6/7/8/9 reinforcement directives,
~800 chars each).

That was the single biggest L10 violation in the pipeline — telling
the model in 2700+ chars what muscles and breasts to render every
panel, when the lineup PNG + reinforcement PNGs are attached and
ARE the canonical truth for proportion.

Post-refactor, this single rule emits one short line at slot
5_style_anchor (the prior L11 STYLE slot) and another at slot
8_tier_build (the prior L11 LINEUP slot) pointing at the attached
refs. The 8b_tier_reinforcement slot is also handled here — when a
tier reinforcement attachment fired, one match line covers it.

Replaces:
  - rules/l11_muscular_build.py (the multi-slot L11 emission)
  - rules/l29_tier6_reinforcement.py (text directive only; attach part
    moved to rules/attach/tier_reinforcement.py)
  - rules/l30_tier7_reinforcement.py (same)
  - rules/l31_tier8_reinforcement.py (same)
  - rules/l32_tier9_reinforcement.py (same)

The L11 rule ID is preserved so audit ledgers remain interpretable.
L29/L30/L31/L32 are also preserved as rule IDs — they continue to fire
at the same slot to record per-tier verification, they just no longer
emit prose.
"""

from __future__ import annotations

from .._base import (
    Rule, Verification, STATUS_PASS, STATUS_SKIPPED, STATUS_FAIL,
    CATEGORY_MATCH,
)


def _tier_int(panel: dict) -> int | None:
    t = panel.get("muscle_size_tier")
    try:
        return int(t)
    except (TypeError, ValueError):
        return None


class L11(Rule):
    """Body proportions — match-the-ref. Replaces the multi-slot L11
    cartoony-FMG prose with one short line per slot."""

    id = "L11"
    title = "Body proportions match the attached body-tier references"
    slot = ("5_style_anchor", "8_tier_build")
    section_label = {
        "5_style_anchor": "STYLE — L11 body-tier anchor",
        "8_tier_build": "BODY TIER — L11 match-the-ref",
    }
    severity = "hard"
    applicable_transformations = ("fmg",)
    category = CATEGORY_MATCH
    vision_rubric = (
        "Look at this rendered comic panel. The panel's shotlist declares "
        "a specific muscle_size_tier and the matching body-tier reference(s) "
        "were attached at generation time. Does the rendered character's "
        "body match the attached tier reference for muscle volume AND "
        "breast scale? Common failure: body lands at a smaller tier because "
        "the model averaged toward the prior. PASS if BOTH muscle and "
        "breast proportions match the attached ref. FAIL with a description "
        "of which attribute regressed."
    )

    def should_apply(self, panel: dict, ctx: dict) -> bool:
        return _tier_int(panel) is not None

    def compose_contribution(self, panel: dict, ctx: dict, slot: str) -> str | None:
        tier = _tier_int(panel)
        if tier is None:
            return None

        if slot == "5_style_anchor":
            if tier >= 2:
                return (
                    "Body style: match the attached body-tier reference "
                    "exactly — cartoony hyper-FMG proportions per the ref, "
                    "not a realistic fitness build."
                )
            return None

        if slot == "8_tier_build":
            lineup_attached = ctx.get("lineup_attached", False)
            stage_change = ctx.get("stage_change", False)
            if lineup_attached:
                return (
                    f"Body proportions: match figure {tier} of the attached "
                    "muscle-size lineup exactly — both the muscle mass AND "
                    "the breast scale. Borrow proportions only; do not "
                    "borrow face, hair, costume, or pose from the lineup."
                )
            if stage_change:
                return (
                    f"Body proportions: tier {tier} (new tier — grown from "
                    "prior panel). Match the attached body refs; both muscle "
                    "AND breast scale escalate to the new tier."
                )
            return (
                f"Body proportions: tier {tier} (unchanged). Carry forward "
                "from the attached state anchor."
            )

        return None

    def verify_pre_render(self, panel: dict, ctx: dict) -> Verification:
        tier = _tier_int(panel)
        if tier is None:
            return Verification(
                status=STATUS_SKIPPED,
                reason="panel.muscle_size_tier is null — non-arc panel",
            )
        slot = ctx.get("_active_slot")
        if slot == "8_tier_build":
            lineup_attached = ctx.get("lineup_attached", False)
            stage_change = ctx.get("stage_change", False)
            if lineup_attached:
                return Verification(
                    status=STATUS_PASS,
                    reason=f"tier={tier}, lineup attached — match-the-ref",
                )
            if stage_change:
                return Verification(
                    status=STATUS_FAIL,
                    reason=(f"tier={tier} stage-change but lineup NOT "
                            "attached — verbal-only fallback (per L11 "
                            "memo: less reliable)"),
                )
        return Verification(status=STATUS_PASS, reason=f"tier={tier}")

    def retry_strategy(self, panel: dict, ctx: dict, failure: dict) -> dict:
        lineup_attached = ctx.get("lineup_attached", False)
        if not lineup_attached:
            return {
                "kind": "auto_resubmit_with_corrected_refs",
                "rule_id": self.id,
                "strengthening": (
                    "attach the muscle-size lineup PNG at generation time. "
                    "Verbal-only body anchoring is significantly less "
                    "reliable per L11. Per L10, the fix is the ref, not "
                    "more prose."
                ),
            }
        tier = _tier_int(panel)
        if tier is not None and tier >= 7:
            return {
                "kind": "auto_resubmit_with_corrected_refs",
                "rule_id": self.id,
                "strengthening": (
                    f"tier {tier} may be at the model's muscularity ceiling. "
                    "Recommend routing to nano_banana_pro for this panel."
                ),
            }
        return {
            "kind": "auto_resubmit_with_corrected_refs",
            "rule_id": self.id,
            "strengthening": (
                "the rendered body landed below the attached ref's scale. "
                "Verify the body-tier reference itself is at-spec; if it "
                "is, regenerate the panel with the tier reinforcement PNGs "
                "for over-spec compensation (per attach/tier_reinforcement.py)."
            ),
        }


class _TierReinforcementMatchBase(Rule):
    """Shared base for L29/L30/L31/L32 match-the-ref directives.

    The actual attachment of the tier PNGs happens in
    rules/attach/tier_reinforcement.py. This base records that the
    reinforcement refs were attached and emits one short match line.

    Subclasses set `tier_value`, `ctx_flag_key`, and `id`.
    """

    slot = "8b_tier_reinforcement"
    severity = "hard"
    applicable_transformations = ("fmg",)
    category = CATEGORY_MATCH
    tier_value: int = 0
    ctx_flag_key: str = ""

    def should_apply(self, panel: dict, ctx: dict) -> bool:
        return _tier_int(panel) == self.tier_value

    def compose_contribution(self, panel: dict, ctx: dict, slot: str) -> str | None:
        if slot != "8b_tier_reinforcement":
            return None
        if not self.should_apply(panel, ctx):
            return None
        if not ctx.get(self.ctx_flag_key):
            return None
        return (
            f"Tier-{self.tier_value} reinforcement refs are attached "
            "alongside the body-tier lineup — match those references "
            "exactly for muscle and breast scale; over-render slightly "
            "to compensate for the model's average-prior normalization."
        )

    def verify_pre_render(self, panel: dict, ctx: dict) -> Verification:
        if _tier_int(panel) != self.tier_value:
            return Verification(
                status=STATUS_SKIPPED,
                reason=(
                    f"panel.muscle_size_tier != {self.tier_value} — "
                    f"L{self.id_num()} only applies at this tier"
                ),
            )
        if ctx.get(self.ctx_flag_key):
            return Verification(
                status=STATUS_PASS,
                reason=(
                    f"tier={self.tier_value}; reinforcement refs attached"
                ),
            )
        return Verification(
            status=STATUS_FAIL,
            reason=(
                f"tier={self.tier_value} but tier-{self.tier_value} "
                "reinforcement refs NOT attached — falling back to lineup-"
                "only is significantly less reliable at this tier."
            ),
        )

    def id_num(self) -> str:
        return self.id.lstrip("L")

    def retry_strategy(self, panel: dict, ctx: dict, failure: dict) -> dict:
        if not ctx.get(self.ctx_flag_key):
            return {
                "kind": "auto_resubmit_with_corrected_refs",
                "rule_id": self.id,
                "strengthening": (
                    f"attach BOTH tier-{self.tier_value} reinforcement "
                    "PNGs at generation time. Per L10, the fix is the ref, "
                    "not more prose."
                ),
            }
        return {
            "kind": "auto_resubmit_with_corrected_refs",
            "rule_id": self.id,
            "strengthening": (
                "reinforcement refs are attached but rendered proportions "
                "under-shot. The refs themselves may need to be regenerated "
                "with stronger over-spec; do not paraphrase the refs into "
                "the prompt."
            ),
        }


class L29(_TierReinforcementMatchBase):
    id = "L29"
    title = "Tier-6 reinforcement match"
    section_label = "TIER-6 REINFORCEMENT — L29"
    tier_value = 6
    ctx_flag_key = "tier6_refs_attached"


class L30(_TierReinforcementMatchBase):
    id = "L30"
    title = "Tier-7 reinforcement match"
    section_label = "TIER-7 REINFORCEMENT — L30"
    tier_value = 7
    ctx_flag_key = "tier7_refs_attached"


class L31(_TierReinforcementMatchBase):
    id = "L31"
    title = "Tier-8 reinforcement match"
    section_label = "TIER-8 REINFORCEMENT — L31"
    tier_value = 8
    ctx_flag_key = "tier8_refs_attached"


class L32(_TierReinforcementMatchBase):
    id = "L32"
    title = "Tier-9 reinforcement match"
    section_label = "TIER-9 REINFORCEMENT — L32"
    tier_value = 9
    ctx_flag_key = "tier9_refs_attached"
