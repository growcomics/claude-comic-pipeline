"""L11 — Cartoony FMG proportions need explicit anchoring.

The only multi-slot rule in the registry. L11 contributes at two slots:

  - `5_style_anchor` — universal cartoony-FMG style anchor, fires when
    tier >= 2. (Tier 1 is the realistic baseline where the anchor would
    actively hurt.)

  - `8_tier_silhouette` — tier-specific block whose content depends on
    whether the lineup ref was attached, whether this is a stage-change
    panel, or whether it's an unchanged carry-forward.

Phase 3b ships as FMG-only (`applicable_transformations=("fmg",)`). A
future MMG / BE / glute variant lives in a sibling module
(`l11_mmg_silhouette.py` etc) — DON'T add genre-conditionals here.

See:
  - skills/comic-production/references/lessons-learned.md § L11
  - skills/comic-production/references/the-rules-explained.md § L11
  - skills/comic-production/references/peak-body-scale.md (tier silhouettes)
"""

from __future__ import annotations

from ._base import Rule, Verification, STATUS_PASS, STATUS_FAIL, STATUS_SKIPPED


# Per-tier silhouette descriptors. Numbers are deliberately aggressive — they
# describe the silhouette of the corresponding lineup figure, not realistic
# anatomy. Tier 4 is the friction zone (realistic vs cartoony commit).
_SILHOUETTE_BY_TIER = {
    1: "baseline athletic — slim, healthy, no exaggerated muscle",
    2: ("visibly developed — defined shoulders, hint of bicep mass, "
        "tighter midsection"),
    3: ("clearly muscular — broad shoulders, defined biceps and chest, "
        "visible abs"),
    4: ("cartoony hyper-FMG threshold — shoulders 2x normal width with "
        "clear deltoid mass, large defined biceps and triceps, full "
        "powerful chest, ridged abdominal definition across the midriff, "
        "strong sculpted quads, sculpted hips"),
    5: ("massive cartoony FMG — shoulders 2.5x normal width, huge "
        "sculpted biceps, deep powerful chest, blocky abdominal "
        "definition, powerful quads"),
    6: ("peak cartoony FMG — shoulders 3x normal width, full "
        "hyper-muscular silhouette dominating the frame, every muscle "
        "group visibly developed"),
    7: ("beyond peak — proportions exaggerated past realism, "
        "frame-filling cartoony FMG silhouette, biceps approach waist "
        "width"),
    8: ("super-peak cartoony FMG — shoulders dwarf the head, biceps "
        "wider than the waist, pure comic-fantasy proportions"),
    9: ("maximum cartoony FMG — pure FMG-comic exaggeration, near-"
        "silhouette dominance over the entire frame"),
}


L11_STYLE_ANCHOR = (
    "Style anchor for the body: cartoony hyper-FMG comic-book "
    "proportions, NOT realistic fitness modelling. Exaggerated comic "
    "musculature where the silhouette is the storytelling element."
)


def _silhouette_desc(tier) -> str:
    try:
        t_int = int(tier)
    except (TypeError, ValueError):
        t_int = None
    return _SILHOUETTE_BY_TIER.get(t_int, f"tier {tier} cartoony FMG silhouette")


def _tier_is_at_least_2(tier) -> bool:
    return (tier is not None and isinstance(tier, (int, float)) and tier >= 2)


class L11(Rule):
    id = "L11"
    title = "Cartoony FMG proportions need explicit anchoring"
    slot = ("5_style_anchor", "8_tier_silhouette")
    severity = "hard"
    applicable_transformations = ("fmg",)

    def should_apply(self, panel: dict, ctx: dict) -> bool:
        # L11 applies when tier is set. Per-slot specifics decide what
        # actually gets emitted.
        return panel.get("muscle_size_tier") is not None

    # ---- composition ------------------------------------------------------

    def compose_contribution(self, panel: dict, ctx: dict, slot: str) -> str | None:
        tier = panel.get("muscle_size_tier")
        if tier is None:
            return None

        if slot == "5_style_anchor":
            if _tier_is_at_least_2(tier):
                return L11_STYLE_ANCHOR
            return None

        if slot == "8_tier_silhouette":
            silhouette = _silhouette_desc(tier)
            lineup_attached = ctx.get("lineup_attached", False)
            stage_change = ctx.get("stage_change", False)
            if lineup_attached:
                return (
                    f"Size tier: {tier}. The attached muscle-size lineup "
                    "reference is a PROPORTION reference ONLY — use figure "
                    f"{tier} from the lineup to determine ONLY: (a) the size, "
                    "mass, and definition of the muscle groups — shoulders, "
                    "deltoids, biceps, triceps, chest, lats, abdominal "
                    "definition, quadriceps, hamstrings, calves; (b) the size, "
                    "fullness, and shape of the breasts; (c) the overall body "
                    f"mass and frame width. Target silhouette dimensions for "
                    f"tier {tier}: {silhouette}. Do NOT borrow from the "
                    "lineup: face, hair, skin tone, clothing, costume, pose, "
                    "facial expression, lighting, setting, background, or any "
                    "visual element other than the muscle and breast "
                    "proportions themselves. The character's identity, hair, "
                    "face, costume, pose, and setting are specified in the "
                    "prompt and the other attached reference images. Render "
                    "the muscle and breast proportions TO MATCH figure "
                    f"{tier} in the lineup exactly — do not approximate to "
                    "smaller realistic-fitness proportions. NOT realistic "
                    "fitness, NOT athletic — cartoony FMG, comic-book "
                    "proportions."
                )
            if stage_change:
                return (
                    f"Size tier: {tier} (NEW tier — grown from prior panel). "
                    f"Cartoony FMG silhouette: {silhouette}. Render the build "
                    "unmistakably larger than the body baseline reference. NOT "
                    "realistic fitness — cartoony comic-book proportions."
                )
            return (
                f"Size tier: {tier} (unchanged from prior panel). Carry "
                "forward the build from the attached state anchor exactly. "
                "No growth in this panel. Preserve the cartoony FMG silhouette "
                "from the prior accepted panel."
            )

        return None

    # ---- verification -----------------------------------------------------

    def verify_pre_render(self, panel: dict, ctx: dict) -> Verification:
        """Slot-dispatched verification. The helper injects `_active_slot`
        into ctx before calling this so multi-slot rules can branch."""
        tier = panel.get("muscle_size_tier")
        if tier is None:
            return Verification(
                status=STATUS_SKIPPED,
                reason="panel.muscle_size_tier is null — non-arc panel",
            )

        slot = ctx.get("_active_slot")

        if slot == "5_style_anchor":
            if _tier_is_at_least_2(tier):
                return Verification(
                    status=STATUS_PASS,
                    reason=f"tier={tier} >= 2 — style anchor at slot 5_style_anchor",
                )
            return Verification(
                status=STATUS_SKIPPED,
                reason=f"tier={tier} < 2 — style anchor would hurt at realistic baseline",
            )

        if slot == "8_tier_silhouette":
            lineup_attached = ctx.get("lineup_attached", False)
            stage_change = ctx.get("stage_change", False)
            if lineup_attached:
                return Verification(
                    status=STATUS_PASS,
                    reason=(f"tier={tier}, lineup attached at generation — "
                            "slot 8_tier_silhouette (lineup-attached path)"),
                )
            if stage_change:
                return Verification(
                    status=STATUS_FAIL,
                    reason=(f"tier={tier} stage-change but lineup NOT attached "
                            "— falling back to verbal-only (significantly less "
                            "reliable per L11)"),
                )
            # Unchanged carry-forward.
            if _tier_is_at_least_2(tier):
                return Verification(
                    status=STATUS_PASS,
                    reason=(f"tier={tier} unchanged carry-forward; style "
                            "anchor already emitted at slot 5"),
                )
            return Verification(
                status=STATUS_SKIPPED,
                reason=(f"tier={tier} unchanged carry-forward; style anchor "
                        "not needed at tier 1"),
            )

        # Slot-agnostic fallback (shouldn't happen with current helper).
        return Verification(status=STATUS_PASS, reason=f"tier={tier}")

    # ---- retry ------------------------------------------------------------

    def retry_strategy(self, panel: dict, ctx: dict, failure: dict) -> dict:
        """Three escalation paths:

          1. Lineup dropped at compose time → reattach it.
          2. Silhouette rendered too small despite lineup → strengthen
             vocabulary (more aggressive shoulder-width / muscle-mass terms).
          3. Tier ≥ 7 + lineup-attached but still too small → known model
             ceiling (Grok caps ~3 on female anatomy); recommend model swap.
        """
        tier = panel.get("muscle_size_tier")
        lineup_attached = ctx.get("lineup_attached", False)
        if not lineup_attached:
            return {
                "kind": "auto_resubmit_with_corrected_refs",
                "rule_id": self.id,
                "strengthening": (
                    "attach the muscle-size lineup PNG as a reference at "
                    "generation time; verbal-only silhouette directives are "
                    "significantly less reliable per L11"
                ),
            }
        try:
            t_int = int(tier)
        except (TypeError, ValueError):
            t_int = None
        if t_int is not None and t_int >= 7:
            return {
                "kind": "auto_resubmit_with_corrected_refs",
                "rule_id": self.id,
                "strengthening": (
                    f"tier {t_int} may be at the model's muscularity ceiling "
                    "(observed for Grok ~3, see chun-li-grok-validation). "
                    "Recommend routing to nano_banana_flash or nano_banana_2 "
                    "for this panel."
                ),
            }
        return {
            "kind": "auto_resubmit_with_stronger_contribution",
            "rule_id": self.id,
            "strengthening": (
                "escalate the silhouette vocabulary one notch: 'shoulders "
                "3x normal width with massive deltoid caps, biceps the size "
                "of the head, every muscle group hyper-defined and visible. "
                "NOT athletic, NOT realistic, NOT a fitness model — comic-"
                "book exaggerated proportions.'"
            ),
        }
