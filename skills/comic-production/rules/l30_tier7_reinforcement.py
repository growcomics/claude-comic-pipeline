"""L30 — Tier-7 needs dedicated proportion reinforcement refs (sibling of L29).

Tier 7 ("beyond peak" per L11's `_BUILD_BY_TIER`) extends the same failure
mode L29 fixed at tier 6: the multi-figure `muscle-size-lineup-4-9.png`
chart averages across its six figures (tiers 4, 5, 6, 7, 8, 9) and the
tier-7 figure renders closer to a tier 5-6 interpolation instead of the
beyond-peak target. The fix mirrors L29 verbatim — keep the lineup
attached (tier context), additionally attach two dedicated tier-7
anatomical reference sheets (full-body annotated overview + close-up
anatomical detail) as isolated tier-7 anchors.

The two PNGs at `peak-body-scale/tier-7/` were generated 2026-05-16
evening using Mira as the source character and the prompt recipe in
[`docs/posts/2026-05-16-tier-7-8-9-reinforcement-plan.md`](../../../docs/posts/2026-05-16-tier-7-8-9-reinforcement-plan.md);
the user picked 1 of 8 candidates for each sheet (Sheet A: `fb14428d`,
Sheet B: `3beb5bbd`).

Slot: `8b_tier_reinforcement` — same slot L29 occupies, immediately
after L11's `8_tier_build`. Multiple rules can occupy one slot in
registry order (per `_registry.iter_rules_for_slot`); L29 fires at
tier == 6, L30 at tier == 7, etc.

See:
  - skills/comic-production/references/peak-body-scale.md § Tier-7 reinforcement
  - skills/comic-production/references/lessons-learned.md § L30
"""

from __future__ import annotations

from ._base import Rule, Verification, STATUS_PASS, STATUS_FAIL, STATUS_SKIPPED


TIER7_REINFORCEMENT_FILES = (
    "tier-7-full-body.png",
    "tier-7-anatomical-detail.png",
)


L30_DIRECTIVE = (
    "TIER-7 PROPORTION REINFORCEMENT: Two additional reference images "
    "attached showing canonical tier-7 (beyond-peak) muscle proportions "
    "— a full-body reference with annotated proportion stats (biceps "
    "profile, chest / thoracic detail, waist narrowness, leg musculature) "
    "and a close-up anatomical detail sheet (biceps anatomy, breast volume "
    "and shape, waistline metrics, full rear view + posterior musculature). "
    "These sit ALONGSIDE the muscle-size lineup (tier-4-to-9 chart), not "
    "in place of it — the lineup gives tier context (figure 7 relative to "
    "tiers 4-6 and 8-9); these reinforcement sheets isolate tier-7 "
    "proportions as their own dedicated anchor against the lineup's "
    "averaging-toward-the-middle bias. Match the BUST VOLUME and forward "
    "PROJECTION, DELTOID MASS dwarfing the head, PECTORAL development, "
    "LAT spread with V-taper, OBLIQUE definition, BICEP peak (approaching "
    "waist width at this tier), and QUAD size shown in these references — "
    "and over-render: the model normalizes off-distribution features "
    "toward average, so the rendered output should target the SAME or "
    "LARGER scale than the reinforcement refs show, never smaller. "
    "PROPORTION REFERENCE ONLY — do NOT adopt the clothing, hair, "
    "hairstyle, hair color, skin tone, face, pose, lighting, background, "
    "or setting from these references. Do NOT render the reference images "
    "as physical scene objects (no inset photos, no annotated overlays, "
    "no figure labels, no proportion stats text floating in the frame). "
    "Borrow scale and mass only — character identity, hair, face, costume, "
    "pose, and setting are specified in the prompt and the other attached "
    "reference images."
)


class L30(Rule):
    id = "L30"
    title = "Tier-7 needs dedicated proportion reinforcement refs"
    slot = "8b_tier_reinforcement"
    severity = "hard"
    applicable_transformations = ("fmg",)
    vision_rubric = (
        "Look at this rendered comic panel. The panel's shotlist declares "
        "muscle_size_tier == 7 (beyond peak) and two dedicated tier-7 "
        "reinforcement reference images were attached alongside the muscle-"
        "size lineup at generation time. Verify the rendered character "
        "matches the tier-7 proportions shown in the reinforcement refs, "
        "not a smaller tier interpolated from the multi-figure lineup.\n\n"
        "MUSCLE: Does the rendered character show tier-7-scale deltoid mass "
        "(massively developed, 3x normal mass dwarfing the head with clear "
        "striation), bicep approaching waist width, deep powerful pectoral "
        "development pushing fabric, broad sweeping lats with V-taper, "
        "blocky 8-pack abdominal definition, powerful sculpted quads with "
        "hamstring detail? The most common failure mode at tier 7 — same "
        "as tier 6 — is the body landing at tier 5-6 proportions because "
        "the multi-figure lineup interpolated downward. The reinforcement "
        "refs exist to block that interpolation at this tier specifically.\n\n"
        "BREASTS: Does the bust read at tier-7 scale — visibly larger and "
        "more forward-projected than tier 6, dramatically full? PASS only "
        "if BOTH muscle AND breast proportions match the tier-7 "
        "reinforcement refs (or render LARGER — over-spec is acceptable, "
        "under-spec is the failure).\n\n"
        "LEAKAGE: Did any element from the reinforcement refs bleed into "
        "the panel that shouldn't have — wrong hairstyle (auburn ponytail "
        "from the source character), wrong skin tone, the reference's grey "
        "training top replacing the panel's costume, the annotated overlay "
        "text rendering as a watermark, the reference's plain studio "
        "backdrop overriding the panel's setting? FAIL with a description "
        "of which attribute leaked. The reinforcement refs are PROPORTION-"
        "ONLY; anything else from them in the panel is a leakage failure."
    )

    def should_apply(self, panel: dict, ctx: dict) -> bool:
        tier = panel.get("muscle_size_tier")
        try:
            return int(tier) == 7
        except (TypeError, ValueError):
            return False

    def compose_contribution(self, panel: dict, ctx: dict, slot: str) -> str | None:
        if slot != "8b_tier_reinforcement":
            return None
        if not self.should_apply(panel, ctx):
            return None
        if not ctx.get("tier7_refs_attached"):
            return None
        return L30_DIRECTIVE

    def verify_pre_render(self, panel: dict, ctx: dict) -> Verification:
        if not self.should_apply(panel, ctx):
            return Verification(
                status=STATUS_SKIPPED,
                reason="panel.muscle_size_tier != 7 — L30 only applies at the beyond-peak figure",
            )
        if ctx.get("tier7_refs_attached"):
            return Verification(
                status=STATUS_PASS,
                reason=(
                    "tier=7 panel; both tier-7 reinforcement refs attached "
                    "alongside the muscle-size lineup"
                ),
            )
        return Verification(
            status=STATUS_FAIL,
            reason=(
                "tier=7 panel but tier-7 reinforcement refs NOT attached. "
                "Expected both PNGs from "
                "skills/comic-production/references/peak-body-scale/tier-7/ "
                "(tier-7-full-body.png + tier-7-anatomical-detail.png) on disk. "
                "Falling back to lineup-only is significantly less reliable "
                "at tier 7 (same failure mode as tier 6 — see L29 + L30 "
                "lessons-learned). Ship the reinforcement PNGs into the "
                "canonical repo path before regenerating this panel."
            ),
        )

    def retry_strategy(self, panel: dict, ctx: dict, failure: dict) -> dict:
        if not ctx.get("tier7_refs_attached"):
            return {
                "kind": "auto_resubmit_with_corrected_refs",
                "rule_id": self.id,
                "strengthening": (
                    "attach BOTH tier-7 reinforcement PNGs at generation "
                    "time from skills/comic-production/references/peak-body-"
                    "scale/tier-7/ (tier-7-full-body.png + tier-7-anatomical-"
                    "detail.png) IN ADDITION TO the muscle-size lineup-4-9. "
                    "Verbal-only tier-7 anchoring under-renders consistently."
                ),
            }
        return {
            "kind": "auto_resubmit_with_stronger_contribution",
            "rule_id": self.id,
            "strengthening": (
                "the reinforcement refs are attached but the rendered "
                "proportions still under-shot. Escalate the directive: name "
                "the specific muscle groups (deltoid mass dwarfing head, "
                "bicep approaching waist width, pectoral development, lat "
                "spread with V-taper, oblique definition, quad mass) AND "
                "the bust volume / forward projection as tier-7 targets, "
                "and over-spec — instruct the model to render LARGER than "
                "the reinforcement refs show."
            ),
        }
