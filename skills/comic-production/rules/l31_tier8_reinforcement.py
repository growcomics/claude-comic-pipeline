"""L31 — Tier-8 needs dedicated proportion reinforcement refs (sibling of L29/L30).

Tier 8 ("super-peak cartoony FMG" per L11's `_BUILD_BY_TIER`) extends the
same multi-figure interpolation failure mode L29 fixed at tier 6 and L30
fixed at tier 7. The fix is identical: keep the lineup attached, add
two dedicated tier-8 reference sheets (full-body + anatomical detail)
as isolated anchors. The two PNGs at `peak-body-scale/tier-8/` were
generated 2026-05-16 evening using Mira as the source character; user
picked Sheet A `7c0d52dd` and Sheet B `6072b6d6` from 14 successful
candidates of a 16-gen batch.

See:
  - skills/comic-production/references/peak-body-scale.md § Tier-8 reinforcement
  - skills/comic-production/references/lessons-learned.md § L31
"""

from __future__ import annotations

from ._base import Rule, Verification, STATUS_PASS, STATUS_FAIL, STATUS_SKIPPED


TIER8_REINFORCEMENT_FILES = (
    "tier-8-full-body.png",
    "tier-8-anatomical-detail.png",
)


L31_DIRECTIVE = (
    "TIER-8 PROPORTION REINFORCEMENT: Two additional reference images "
    "attached showing canonical tier-8 (super-peak) muscle proportions "
    "— a full-body reference with annotated proportion stats (biceps "
    "profile, chest / thoracic detail, waist narrowness, leg musculature) "
    "and a close-up anatomical detail sheet (biceps anatomy, breast volume "
    "and shape, waistline metrics, full rear view + posterior musculature). "
    "These sit ALONGSIDE the muscle-size lineup, not in place of it — the "
    "lineup gives tier context, these reinforcement sheets isolate tier-8 "
    "proportions as their own dedicated anchor. Match the SUPER-PEAK bust "
    "volume and forward projection, deltoid mass DWARFING the head, bicep "
    "WIDER than the waist, deep cavernous pectoral mass, sweeping V-taper "
    "lats, blocky 8-pack abdominal definition, and tree-trunk quads shown "
    "in these references — and over-render: the model normalizes off-"
    "distribution features toward average, so target the SAME or LARGER "
    "scale than the reinforcement refs show, never smaller. PROPORTION "
    "REFERENCE ONLY — do NOT adopt the clothing, hair, hairstyle, hair "
    "color, skin tone, face, pose, lighting, background, or setting from "
    "these references. Do NOT render the reference images as physical "
    "scene objects (no inset photos, no annotated overlays, no figure "
    "labels, no proportion stats text floating in the frame). Borrow "
    "scale and mass only — character identity, hair, face, costume, "
    "pose, and setting are specified in the prompt and the other attached "
    "reference images."
)


class L31(Rule):
    id = "L31"
    title = "Tier-8 needs dedicated proportion reinforcement refs"
    slot = "8b_tier_reinforcement"
    severity = "hard"
    applicable_transformations = ("fmg",)
    vision_rubric = (
        "Look at this rendered comic panel. The panel's shotlist declares "
        "muscle_size_tier == 8 (super-peak) and two dedicated tier-8 "
        "reinforcement reference images were attached alongside the muscle-"
        "size lineup at generation time. Verify the rendered character "
        "matches the tier-8 proportions shown in the reinforcement refs, "
        "not a smaller tier interpolated from the multi-figure lineup.\n\n"
        "MUSCLE: Does the rendered character show tier-8-scale deltoid "
        "mass (3.5x normal, dramatically dwarfing the head with extreme "
        "striation), bicep WIDER than the waist, deep cavernous pectoral "
        "development, blocky 8-pack abdominal definition, tree-trunk "
        "quads, sweeping V-taper lats? The failure mode at this tier is "
        "the body landing at tier 6-7 proportions because the lineup-4-9 "
        "chart averaged downward.\n\n"
        "BREASTS: Tier-8 bust scale reads as comic-fantasy — visibly "
        "larger and more dramatically forward-projected than tier 7. PASS "
        "only if BOTH muscle AND breast proportions match the tier-8 "
        "reinforcement refs (or render LARGER — over-spec is acceptable, "
        "under-spec is the failure).\n\n"
        "LEAKAGE: Did any element from the reinforcement refs bleed into "
        "the panel that shouldn't have — wrong hairstyle (auburn ponytail "
        "from Mira-as-source), wrong skin tone, the reference's grey "
        "training top replacing the panel's costume, the annotated overlay "
        "text rendering as a watermark, the reference's plain studio "
        "backdrop overriding the panel's setting? FAIL with a description "
        "of which attribute leaked."
    )

    def should_apply(self, panel: dict, ctx: dict) -> bool:
        tier = panel.get("muscle_size_tier")
        try:
            return int(tier) == 8
        except (TypeError, ValueError):
            return False

    def compose_contribution(self, panel: dict, ctx: dict, slot: str) -> str | None:
        if slot != "8b_tier_reinforcement":
            return None
        if not self.should_apply(panel, ctx):
            return None
        if not ctx.get("tier8_refs_attached"):
            return None
        return L31_DIRECTIVE

    def verify_pre_render(self, panel: dict, ctx: dict) -> Verification:
        if not self.should_apply(panel, ctx):
            return Verification(
                status=STATUS_SKIPPED,
                reason="panel.muscle_size_tier != 8 — L31 only applies at the super-peak figure",
            )
        if ctx.get("tier8_refs_attached"):
            return Verification(
                status=STATUS_PASS,
                reason=(
                    "tier=8 panel; both tier-8 reinforcement refs attached "
                    "alongside the muscle-size lineup"
                ),
            )
        return Verification(
            status=STATUS_FAIL,
            reason=(
                "tier=8 panel but tier-8 reinforcement refs NOT attached. "
                "Expected both PNGs from "
                "skills/comic-production/references/peak-body-scale/tier-8/ "
                "(tier-8-full-body.png + tier-8-anatomical-detail.png) on disk. "
                "Falling back to lineup-only is significantly less reliable "
                "at tier 8 (same failure mode as tier 6/7 — see L29/L30/L31 "
                "lessons-learned)."
            ),
        )

    def retry_strategy(self, panel: dict, ctx: dict, failure: dict) -> dict:
        if not ctx.get("tier8_refs_attached"):
            return {
                "kind": "auto_resubmit_with_corrected_refs",
                "rule_id": self.id,
                "strengthening": (
                    "attach BOTH tier-8 reinforcement PNGs at generation "
                    "time from skills/comic-production/references/peak-body-"
                    "scale/tier-8/. Verbal-only tier-8 anchoring under-"
                    "renders consistently."
                ),
            }
        return {
            "kind": "auto_resubmit_with_stronger_contribution",
            "rule_id": self.id,
            "strengthening": (
                "the reinforcement refs are attached but the rendered "
                "proportions still under-shot. Escalate the directive: "
                "deltoid mass DWARFING the head, bicep WIDER than the "
                "waist, deep cavernous pectoral mass, tree-trunk quads, "
                "comic-fantasy bust scale. Over-spec LARGER than the refs."
            ),
        }
