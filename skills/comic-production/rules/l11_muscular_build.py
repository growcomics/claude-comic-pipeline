"""L11 — Cartoony FMG proportions need explicit anchoring.

The only multi-slot rule in the registry. L11 contributes at two slots:

  - `5_style_anchor` — universal cartoony-FMG style anchor, fires when
    tier >= 2. (Tier 1 is the realistic baseline where the anchor would
    actively hurt.)

  - `8_tier_build` — tier-specific block whose content depends on
    whether the lineup ref was attached, whether this is a stage-change
    panel, or whether it's an unchanged carry-forward.

Phase 3b ships as FMG-only (`applicable_transformations=("fmg",)`). A
future MMG / BE / glute variant lives in a sibling module
(`l11_mmg_muscular_build.py` etc) — DON'T add genre-conditionals here.

See:
  - skills/comic-production/references/lessons-learned.md § L11
  - skills/comic-production/references/the-rules-explained.md § L11
  - skills/comic-production/references/peak-body-scale.md (tier muscular builds)
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
#
# 2026-05-16 vocabulary correction (Alignment Diff #3): added explicit
# breast-scale anchoring with parallel "CRITICAL — BREASTS:" framing.
# Pre-correction the lineup-attached path mentioned breasts as a passing
# list item ("(b) the size, fullness, and shape of the breasts") but only
# muscle had the CAPS-LOCK / "do not regress" guards. Result: nano_banana_2
# reliably matched muscle scale but defaulted to average / conservative
# breast scale even when the user's explicit prompt asked for tier-6
# breast size to match figure 6. Fix: promote breast scale to a first-
# class anchor using the same surgical-scoping pattern that fixed muscle
# — explicit "match figure N's breasts" + "do NOT regress to a smaller
# tier's breast proportions" + style-anchor mention + stage-change
# verbal-fallback mention + vision-rubric verification.
#
# 2026-05-16 v1→v2 iteration: v1 vocabulary landed close but breasts still
# undershot at tier 6 on nano_banana_flash. Four additions folded in from
# the v2 validation render that resolved the regression:
#   1. Over-spec compensation — explicitly tells the model that nano_banana
#      normalizes off-distribution features toward an average prior, and
#      instructs it to render SLIGHTLY LARGER than the lineup figure shows
#      so the downward bias lands at parity (per `feedback_chest_oversize_
#      compensate` memory).
#   2. Costume-accommodates anchor — the costume must accommodate the
#      breast scale (pushed forward, stretched, fitted around the volume);
#      NOT the breasts shrunk to fit the costume's modest silhouette.
#      Critical for traditional / modest-coded garments (qipao, kimono,
#      robe, business attire) where the model has a "this garment =
#      modest profile" prior that overrides the breast scale.
#   3. Anti-flattening negation — NO flattening, NO modest profile, NO
#      conservative coverage minimizing the breast contour.
#   4. Dramatic-enhancement framing — "at tier N the breast scale should
#      read as a DRAMATIC enhancement over figure 1's baseline."
# Validated on Chun Li tier 6 with blue qipao costume; v1 landed at ~tier
# 4-5 breast scale, v2 landed at ~tier 6+ (over-spec compensation
# intentional).
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
    "with HEAVY 3D muscle volume AND tier-scaled breast proportions — NOT "
    "realistic fitness modelling, NOT a fitness-model build at wider scale, "
    "NOT a smaller-breasted body grafted onto bigger muscles, NOT a modest "
    "costume silhouette flattening the chest. The lineup attached is a 3D "
    "body chart that scales TWO attributes per tier: visible musculature AND "
    "breast size / fullness / forward projection. The storytelling elements "
    "are the muscle MASS and DEFINITION (delts, biceps, chest, abs, quads) "
    "AND the breast SIZE, FULLNESS, and forward PROJECTION — not the outline "
    "width, not a default-conservative breast size, not a costume that "
    "flattens the breast contour. The costume must ACCOMMODATE the breast "
    "scale (pushed forward, stretched, fitted around the volume), not the "
    "other way around. Render thick, defined, comic-exaggerated muscle "
    "volume with proportionally matched breast scale."
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
    slot = ("5_style_anchor", "8_tier_build")
    section_label = {
        "5_style_anchor": "STYLE — L11 cartoony FMG anchor",
        "8_tier_build": "LINEUP PROPORTIONS — L11 surgical scope",
    }
    severity = "hard"
    applicable_transformations = ("fmg",)
    vision_rubric = (
        "Look at this rendered comic panel. The panel's shotlist declares a "
        "specific muscle_size_tier and the attached muscle-size lineup is a "
        "3D body chart with six figures showing TWO progressively-scaled "
        "attributes per tier: (1) muscle mass / definition, and (2) breast "
        "size / fullness / forward projection. Verify BOTH attributes match "
        "the lineup figure for the declared tier.\n\n"
        "MUSCLE: Does the rendered character's muscular build match the "
        "lineup figure for the declared tier? Compare the 3D MUSCLE VOLUME "
        "specifically, not just the outline width: deltoid mass and "
        "separation, bicep peak and thickness, chest depth, abdominal "
        "definition (visible 6-pack or 8-pack), lat width, quad mass, "
        "frame width relative to head.\n\n"
        "BREASTS: Does the rendered character's breast size, fullness, and "
        "forward projection match the lineup figure for the declared tier? "
        "The lineup scales breasts proportionally to muscle tier — figure "
        "6's breasts are visibly larger, fuller, and more forward-projected "
        "than figure 1's. Common regression: the body lands at tier N "
        "muscle mass but the breasts render at tier 2-3 size (model "
        "defaults to average / conservative breast scale even when the "
        "lineup shows otherwise).\n\n"
        "Does the rendered body look 'cartoony hyper-FMG' (thick 3D muscle "
        "mass AND tier-matched breast scale, like the lineup target) or "
        "did it regress — either to realistic fitness modelling (thin "
        "musculature with the right outline width) OR to a smaller-"
        "breasted body with bigger muscles (muscle landed but breasts "
        "undershot)? Critical distinction: a fitness-model body at wider "
        "proportions with conservative breasts is NOT a tier 5/6 match — "
        "both muscle VOLUME and breast PROPORTIONS must actually be heavy "
        "and tier-scaled. PASS only if BOTH attributes match the lineup "
        "figure. FAIL with a specific description of which attribute "
        "regressed and how (e.g. 'muscle mass matches figure 6 but breasts "
        "rendered at tier 2-3 size — undershot the lineup's breast scale' "
        "or 'shoulders are wider but deltoid mass undersized — looks like "
        "a fitness model at tier 3 proportions'). Critical at tier 4 (the "
        "friction zone) and tier 5-6 (peak)."
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

        if slot == "8_tier_build":
            build = _build_desc(tier)
            lineup_attached = ctx.get("lineup_attached", False)
            stage_change = ctx.get("stage_change", False)
            if lineup_attached:
                return (
                    f"Size tier: {tier}. The attached muscle-size lineup is "
                    "a 3D BODY CHART with six figures showing TWO "
                    "progressively-scaled attributes per tier: (1) muscle "
                    "mass / definition (visible deltoids, biceps, chest, "
                    "abdominal definition, quad mass, frame width) AND (2) "
                    "breast scale (size, fullness, forward projection). Both "
                    "attributes scale per tier — figure 6 has visibly larger "
                    "and more forward-projected breasts than figure 1 IN "
                    "ADDITION TO larger muscle mass. It is a PROPORTION "
                    "reference ONLY (NOT an outline reference, NOT a face / "
                    "hair / costume reference) — use figure "
                    f"{tier} from the lineup to determine ONLY: "
                    "(a) the size, mass, and definition of the muscle groups "
                    "— shoulders, deltoids, biceps, triceps, chest, lats, "
                    "abdominal definition, quadriceps, hamstrings, calves; "
                    "(b) the SIZE, FULLNESS, and forward PROJECTION of the "
                    "breasts; (c) the overall body mass and frame width. "
                    f"Target muscular build for tier {tier}: {build}. "
                    f"CRITICAL — MUSCLE: match the visible 3D MUSCLE VOLUME "
                    f"and DEFINITION of figure {tier}, not just the outline "
                    "width — render the body with the same thick muscle "
                    "mass, the same striation, the same chest depth, the "
                    f"same arm thickness that figure {tier} shows. "
                    f"CRITICAL — BREASTS: match the BREAST SIZE, FULLNESS, "
                    f"and forward PROJECTION of figure {tier} EXACTLY. The "
                    "lineup scales breasts proportionally to muscle tier — "
                    "render the breasts at the SAME visible volume, the "
                    "SAME fullness, and the SAME forward projection that "
                    f"figure {tier} shows. At tier {tier} the breast scale "
                    "should read as a DRAMATIC enhancement over figure 1's "
                    "baseline; the lineup scales breast volume substantially "
                    "across tiers and the rendered output must reflect that. "
                    "OVER-SPEC COMPENSATION: nano_banana models normalize "
                    "breast scale DOWN toward an average prior even when "
                    "explicit anchoring is in the prompt — render the "
                    f"breasts SLIGHTLY LARGER than figure {tier} shows so "
                    "that after the model's downward bias the final rendered "
                    f"scale lands AT figure {tier}'s level. The costume "
                    "must ACCOMMODATE the breast scale (pushed forward, "
                    "stretched, fitted around the volume) — NOT flatten or "
                    "compress the breasts; NO modest profile, NO conservative "
                    "coverage minimizing the breast contour, NO costume drape "
                    "that hides the breast volume. Do NOT default to average "
                    "/ conservative breast size; do NOT regress to a smaller "
                    "tier's breast proportions; do NOT render the body at "
                    f"tier {tier} muscle mass with breasts shrunk to tier "
                    "2 or 3 size. Breast scale is a LOAD-BEARING attribute "
                    "of the lineup, not an afterthought. Do NOT borrow from "
                    "the lineup: face, hair, skin tone, clothing, costume, "
                    "pose, facial expression, lighting, setting, background, "
                    "or any visual element other than the muscle and breast "
                    "proportions themselves. The character's identity, "
                    "hair, face, costume, pose, and setting are specified "
                    "in the prompt and the other attached reference images. "
                    "Render the muscular build AND the breast proportions "
                    f"TO MATCH figure {tier} in the lineup exactly — do not "
                    "approximate either to smaller realistic-fitness "
                    "proportions. NOT realistic fitness, NOT athletic, NOT "
                    "a fitness model at wider scale, NOT bigger muscles "
                    "with conservative breasts, NOT a modest costume "
                    "silhouette flattening the chest — cartoony FMG, "
                    "comic-book proportions with HEAVY 3D muscle mass AND "
                    "lineup-matched (or slightly over-spec'd) breast scale "
                    "that the costume accommodates."
                )
            if stage_change:
                return (
                    f"Size tier: {tier} (NEW tier — grown from prior panel). "
                    f"Cartoony FMG muscular build: {build}. Render the muscle "
                    "MASS and DEFINITION (delts, biceps, chest, abs, quads) "
                    "AND the breast SIZE, FULLNESS, and forward PROJECTION "
                    "unmistakably larger than the body baseline reference — "
                    "thick 3D muscle volume with tier-scaled breast "
                    "proportions, not just a wider outline, NOT bigger "
                    "muscles with conservative breasts, NOT a modest costume "
                    "silhouette flattening the chest. Over-spec the breast "
                    "scale slightly so the model's downward-bias normalization "
                    "lands at the new tier's level rather than below it; the "
                    "costume must accommodate the breast scale, not the other "
                    "way around. NOT realistic fitness — cartoony comic-book "
                    "proportions with both muscle mass AND breast scale "
                    "escalated to the new tier."
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

        if slot == "8_tier_build":
            lineup_attached = ctx.get("lineup_attached", False)
            stage_change = ctx.get("stage_change", False)
            if lineup_attached:
                return Verification(
                    status=STATUS_PASS,
                    reason=(f"tier={tier}, lineup attached at generation — "
                            "slot 8_tier_build (lineup-attached path)"),
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
                    "generation time; verbal-only muscular-build directives are "
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
                "escalate BOTH the muscular-build and breast-scale "
                "vocabulary one notch with explicit over-spec "
                "compensation: 'deltoids 3x normal MASS (not just 3x "
                "outline width) with visible striation, biceps thick and "
                "peaked, chest deep with clear separation, abdominal "
                "definition carved in 3D, every muscle group hyper-"
                "defined with heavy 3D volume. Breasts: massive, "
                "voluminous, dramatically forward-projecting at the "
                "lineup figure's tier size — render SLIGHTLY LARGER than "
                "the lineup figure shows so the model's downward-bias "
                "normalization lands at parity (nano_banana models scale "
                "off-distribution features toward an average prior; "
                "over-spec compensates). The costume must accommodate the "
                "breast scale — pushed forward, stretched, fitted around "
                "the volume; NO flattening, NO modest profile, NO "
                "conservative coverage. If the body landed at the right "
                "muscle tier but breasts shrunk to tier 2-3, the prompt "
                "is missing the CRITICAL — BREASTS guard AND the over-"
                "spec compensation. The lineup figure shows BOTH the "
                "MUSCLE MASS and the BREAST SCALE to match. NOT athletic, "
                "NOT a fitness model at wider scale, NOT bigger muscles "
                "with conservative breasts, NOT a modest costume "
                "silhouette flattening the chest — comic-book exaggerated "
                "muscle volume with proportionally matched (or slightly "
                "over-spec'd) breast scale.'"
            ),
        }
