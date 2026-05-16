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


# Per-tier muscular-build descriptors. Each describes the 3D RENDERED MUSCLE
# VOLUME of the corresponding lineup figure — not an outline / not a
# silhouette. The lineup is a 3D body chart with visible musculature
# (delts, biceps, chest, abs, quads), and the model needs vocabulary that
# points at muscle MASS and DEFINITION, not just outline width.
#
# 2026-05-16 vocabulary correction (Alignment Diff #2): replaced "silhouette"
# language with "muscular build" / "physique" / "muscle mass and definition"
# throughout — the model was interpreting "match the silhouette of figure N"
# as "match the OUTLINE shape" and skipping the visible 3D muscle volume.
# Tier 4-6 panels in Test 1 and Test 2 both rendered as "wider fitness
# model" instead of cartoony FMG because of this exact word choice.
_BUILD_BY_TIER = {
    1: "baseline athletic — slim, healthy, no developed muscle mass",
    2: ("visibly developed — defined deltoid mass beginning to show, "
        "small bicep peak, tighter midsection with hint of abdominal "
        "definition"),
    3: ("clearly muscular — broad deltoids with clear separation, "
        "defined bicep peaks, full chest, visible abdominal definition, "
        "noticeable quad mass"),
    4: ("cartoony hyper-FMG threshold — deltoids 2x normal mass with "
        "clear striation, biceps with visible peaks and triceps mass, "
        "full powerful chest pushing fabric, ridged 6-pack abdominal "
        "definition, strong sculpted quads, hip flare. THICK 3D muscle "
        "volume, not just a wider outline"),
    5: ("massive cartoony FMG — deltoids 2.5x normal mass, huge sculpted "
        "biceps with deep peaks and visible vascularity, deep powerful "
        "chest with separation, blocky 8-pack abdominal definition, "
        "powerful sculpted quads with hamstring detail. HEAVY 3D muscle "
        "volume visible from every angle, not a slim outline at wider "
        "scale"),
    6: ("peak cartoony FMG — deltoids 3x normal mass dwarfing the head, "
        "biceps as wide as the waist, full hyper-muscular build with "
        "every muscle group visibly developed and individually defined. "
        "MAXIMAL 3D muscle volume, the body reads as a cartoony hyper-"
        "muscular figure not a fitness model at wider proportions"),
    7: ("beyond peak — proportions exaggerated past realism, frame-"
        "filling cartoony FMG muscle mass, biceps approach waist width, "
        "every muscle group massively developed with clear striation"),
    8: ("super-peak cartoony FMG — deltoids dwarf the head, biceps wider "
        "than the waist, pure comic-fantasy proportions with maximal "
        "muscle volume"),
    9: ("maximum cartoony FMG — pure FMG-comic exaggeration, near-"
        "total muscle dominance over the frame, every muscle group at "
        "maximal volume and definition"),
}

# Legacy alias for any external code that imports the old name.
_SILHOUETTE_BY_TIER = _BUILD_BY_TIER


L11_STYLE_ANCHOR = (
    "Style anchor for the body: cartoony hyper-FMG comic-book proportions "
    "with HEAVY 3D muscle volume — NOT realistic fitness modelling, NOT a "
    "fitness-model build at wider scale. The lineup attached is a 3D body "
    "chart with visible musculature; the storytelling element is the muscle "
    "MASS and DEFINITION (delts, biceps, chest, abs, quads), not the outline "
    "width. Render thick, defined, comic-exaggerated muscle volume."
)


def _build_desc(tier) -> str:
    """Per-tier muscular-build descriptor. Reads the lineup as a 3D body
    chart and tells the model to match muscle VOLUME, not outline shape."""
    try:
        t_int = int(tier)
    except (TypeError, ValueError):
        t_int = None
    return _BUILD_BY_TIER.get(t_int, f"tier {tier} cartoony FMG muscular build")


# Legacy alias for any external code that imports the old name.
_silhouette_desc = _build_desc


def _tier_is_at_least_2(tier) -> bool:
    return (tier is not None and isinstance(tier, (int, float)) and tier >= 2)


class L11(Rule):
    id = "L11"
    title = "Cartoony FMG proportions need explicit anchoring"
    slot = ("5_style_anchor", "8_tier_silhouette")
    severity = "hard"
    applicable_transformations = ("fmg",)
    vision_rubric = (
        "Look at this rendered comic panel. The panel's shotlist declares a "
        "specific muscle_size_tier and the attached muscle-size lineup is a "
        "3D body chart with six figures showing progressive muscle "
        "development (delts, biceps, chest, abs, quads, frame width). Does "
        "the rendered character's muscular build match the lineup figure for "
        "the declared tier? Compare specifically the 3D MUSCLE VOLUME, not "
        "just the outline width: deltoid mass and separation, bicep peak and "
        "thickness, chest depth, abdominal definition (visible 6-pack or 8-"
        "pack), lat width, quad mass, frame width relative to head. Does the "
        "rendered body look 'cartoony hyper-FMG' (thick 3D muscle mass like "
        "the lineup target) or did it regress to realistic fitness modelling "
        "(athletic but thin musculature with the right outline width)? "
        "Critical distinction: a fitness-model body at wider proportions is "
        "NOT a tier 5/6 match — the muscle VOLUME must actually be heavy and "
        "defined. PASS if muscle mass and definition match the lineup figure. "
        "FAIL with a specific description of the regression (e.g. 'shoulders "
        "are wider but deltoid mass undersized — looks like a fitness model "
        "at tier 3 proportions, not the heavy muscle volume of lineup figure "
        "6'). Critical at tier 4 (the friction zone) and tier 5-6 (peak)."
    )

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
            build = _build_desc(tier)
            lineup_attached = ctx.get("lineup_attached", False)
            stage_change = ctx.get("stage_change", False)
            if lineup_attached:
                return (
                    f"Size tier: {tier}. The attached muscle-size lineup is "
                    "a 3D BODY CHART with six figures showing progressive "
                    "muscle development — visible deltoids, biceps, chest, "
                    "abdominal definition, quad mass, frame width. It is a "
                    "MUSCULAR-BUILD reference ONLY (NOT an outline reference) "
                    f"— use figure {tier} from the lineup to determine ONLY: "
                    "(a) the size, mass, and definition of the muscle groups "
                    "— shoulders, deltoids, biceps, triceps, chest, lats, "
                    "abdominal definition, quadriceps, hamstrings, calves; "
                    "(b) the size, fullness, and shape of the breasts; (c) "
                    "the overall body mass and frame width. Target muscular "
                    f"build for tier {tier}: {build}. CRITICAL: match the "
                    f"visible 3D MUSCLE VOLUME and DEFINITION of figure "
                    f"{tier}, not just the outline width — render the body "
                    f"with the same thick muscle mass, the same striation, "
                    f"the same chest depth, the same arm thickness that "
                    f"figure {tier} shows. Do NOT borrow from the lineup: "
                    "face, hair, skin tone, clothing, costume, pose, facial "
                    "expression, lighting, setting, background, or any visual "
                    "element other than the muscle and breast proportions "
                    "themselves. The character's identity, hair, face, "
                    "costume, pose, and setting are specified in the prompt "
                    "and the other attached reference images. Render the "
                    f"muscular build and breast proportions TO MATCH figure "
                    f"{tier} in the lineup exactly — do not approximate to "
                    "smaller realistic-fitness proportions. NOT realistic "
                    "fitness, NOT athletic, NOT a fitness model at wider "
                    "scale — cartoony FMG, comic-book proportions with HEAVY "
                    "3D muscle mass."
                )
            if stage_change:
                return (
                    f"Size tier: {tier} (NEW tier — grown from prior panel). "
                    f"Cartoony FMG muscular build: {build}. Render the muscle "
                    "MASS and DEFINITION (delts, biceps, chest, abs, quads) "
                    "unmistakably larger than the body baseline reference — "
                    "thick 3D muscle volume, not just a wider outline. NOT "
                    "realistic fitness — cartoony comic-book proportions."
                )
            return (
                f"Size tier: {tier} (unchanged from prior panel). Carry "
                "forward the muscular build from the attached state anchor "
                "exactly. No growth in this panel. Preserve the same muscle "
                "mass and definition from the prior accepted panel."
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
                "escalate the muscular-build vocabulary one notch: "
                "'deltoids 3x normal MASS (not just 3x outline width) with "
                "visible striation, biceps thick and peaked, chest deep with "
                "clear separation, abdominal definition carved in 3D, every "
                "muscle group hyper-defined with heavy 3D volume. The "
                "lineup figure shows the MUSCLE MASS to match, not just the "
                "outline. NOT athletic, NOT a fitness model at wider scale "
                "— comic-book exaggerated muscle volume.'"
            ),
        }
