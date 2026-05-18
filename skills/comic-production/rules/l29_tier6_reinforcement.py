"""L29 — Tier-6 needs dedicated proportion reinforcement refs.

The cast lineup (tiers 1-6 in one PNG, or 4-9 in the second PNG) is a multi-
figure 3D body chart. Tier 6 is the peak figure on the 1-6 chart, but
empirically the model under-renders tier-6 proportions when only the multi-
figure lineup is attached — the model averages across the visible figures and
the tier-6 muscle mass / breast scale lands closer to tier 4-5 than figure 6.

L29 fixes this by auto-attaching two dedicated tier-6 anatomical reference
sheets on top of the lineup whenever `panel.muscle_size_tier == 6`:

  - `peak-body-scale/tier-6/tier-6-full-body.png` — front + rear full-body
    reference with annotated proportion stats, biceps profile, chest /
    thoracic detail, waist narrowness, leg musculature.
  - `peak-body-scale/tier-6/tier-6-anatomical-detail.png` — close-up
    detail sheet for biceps anatomy, breast volume / shape, waistline
    metrics, full rear view + posterior musculature.

These are REINFORCEMENT — the lineup stays attached. The reinforcement
sheets sit alongside the lineup and isolate tier-6 proportions as their own
dedicated visual anchor instead of one figure among six.

L29 inherits the L11 surgical-scoping pattern verbatim — the reinforcement
refs are PROPORTION reference ONLY (NOT a clothing / hair / face / pose /
lighting / background reference). Lineup leakage is the exact failure mode
L11 fixed for the multi-figure chart; the dedicated tier-6 refs would
otherwise reintroduce it (single-figure refs are even more prone to bleed
than 6-figure charts).

Slot: 8b_tier_reinforcement — fires immediately after L11's 8_tier_build
so the reinforcement directive sits next to the lineup directive.

See:
  - skills/comic-production/references/peak-body-scale.md § Tier-6 reinforcement
  - skills/comic-production/references/lessons-learned.md § L29
  - skills/comic-production/references/the-rules-explained.md § L29
"""

from __future__ import annotations

from ._base import Rule, Verification, STATUS_PASS, STATUS_FAIL, STATUS_SKIPPED


# Filename constants — also referenced by next_panel.find_tier6_reinforcement_refs.
TIER6_REINFORCEMENT_FILES = (
    "tier-6-full-body.png",
    "tier-6-anatomical-detail.png",
)


L29_DIRECTIVE = (
    "TIER-6 PROPORTION REINFORCEMENT: Two additional reference images "
    "attached showing canonical tier-6 muscle proportions — a full-body "
    "reference with annotated proportion stats (biceps profile, chest / "
    "thoracic detail, waist narrowness, leg musculature) and a close-up "
    "anatomical detail sheet (biceps anatomy, breast volume and shape, "
    "waistline metrics, full rear view + posterior musculature). These "
    "sit ALONGSIDE the muscle-size lineup, not in place of it — the "
    "lineup gives tier context (figure 6 vs the other tiers); these "
    "reinforcement sheets isolate tier-6 proportions as their own dedicated "
    "anchor. Match the BUST VOLUME and forward PROJECTION, DELTOID MASS, "
    "PECTORAL development, LAT spread, OBLIQUE definition, BICEP peak and "
    "thickness, and QUAD size shown in these references — and over-render: "
    "the model normalizes off-distribution features toward average, so the "
    "rendered output should target the SAME or LARGER scale than the "
    "reinforcement refs show, never smaller. "
    "PROPORTION REFERENCE ONLY — do NOT adopt the clothing, hair, "
    "hairstyle, hair color, skin tone, face, pose, lighting, background, "
    "or setting from these references. Do NOT render the reference images "
    "as physical scene objects (no inset photos, no annotated overlays, no "
    "figure labels, no proportion stats text floating in the frame). "
    "Borrow scale and mass only — character identity, hair, face, costume, "
    "pose, and setting are specified in the prompt and the other attached "
    "reference images."
)


class L29(Rule):
    id = "L29"
    title = "Tier-6 needs dedicated proportion reinforcement refs"
    slot = "8b_tier_reinforcement"
    section_label = "TIER-6 REINFORCEMENT — L29"
    severity = "hard"
    applicable_transformations = ("fmg",)
    vision_rubric = (
        "Look at this rendered comic panel. The panel's shotlist declares "
        "muscle_size_tier == 6 and two dedicated tier-6 reinforcement "
        "reference images were attached alongside the muscle-size lineup at "
        "generation time. Verify the rendered character matches the tier-6 "
        "proportions shown in the reinforcement refs, not a smaller tier "
        "interpolated from the multi-figure lineup.\n\n"
        "MUSCLE (compare against tier-6-full-body.png + tier-6-anatomical-"
        "detail.png): Does the rendered character show tier-6-scale deltoid "
        "mass (3x normal mass dwarfing the head, with visible separation), "
        "bicep peak and thickness, pectoral development, lat spread / V-"
        "taper, oblique and abdominal definition, quad mass, and overall "
        "frame width? The most common failure: tier-6 declared but the body "
        "renders at tier 4-5 proportions because the multi-figure lineup "
        "interpolated downward. The reinforcement refs exist precisely to "
        "block that interpolation.\n\n"
        "BREASTS (compare against tier-6-anatomical-detail.png 'Breast "
        "Volume & Shape — Detail View'): Does the rendered character's "
        "bust volume, fullness, and forward projection match the tier-6 "
        "detail sheet? Same failure mode as muscle — the model tends to "
        "default conservative even when the ref shows otherwise. PASS only "
        "if BOTH muscle AND breast proportions match the tier-6 reinforcement "
        "refs (or render LARGER — over-spec is acceptable, under-spec is "
        "the failure).\n\n"
        "LEAKAGE: Did any element from the reinforcement refs bleed into "
        "the panel that shouldn't have — wrong hairstyle, wrong skin tone, "
        "the reference's grey shorts replacing the panel's costume, the "
        "annotated overlay text rendering as a watermark, the reference "
        "lighting overriding the panel's lighting? FAIL with a description "
        "of which attribute leaked. The reinforcement refs are PROPORTION-"
        "ONLY; anything else from them in the panel is a leakage failure."
    )

    def should_apply(self, panel: dict, ctx: dict) -> bool:
        # Strict tier-6 trigger. Tiers 7-9 are beyond peak and use their own
        # reinforcement refs in a future expansion of this rule; don't apply
        # the tier-6 sheets to higher tiers because the anatomical detail is
        # calibrated specifically for figure-6 proportions.
        tier = panel.get("muscle_size_tier")
        try:
            return int(tier) == 6
        except (TypeError, ValueError):
            return False

    def compose_contribution(self, panel: dict, ctx: dict, slot: str) -> str | None:
        if slot != "8b_tier_reinforcement":
            return None
        if not self.should_apply(panel, ctx):
            return None
        # Only emit the directive when the reinforcement refs actually got
        # attached at generation time. Verbal-only fallback is significantly
        # weaker; pre_render verification surfaces the missing-refs case as a
        # HARD fail so the missing PNG path can be fixed before render.
        if not ctx.get("tier6_refs_attached"):
            return None
        return L29_DIRECTIVE

    def verify_pre_render(self, panel: dict, ctx: dict) -> Verification:
        if not self.should_apply(panel, ctx):
            return Verification(
                status=STATUS_SKIPPED,
                reason="panel.muscle_size_tier != 6 — L29 only applies at the peak-1-6 figure",
            )
        if ctx.get("tier6_refs_attached"):
            return Verification(
                status=STATUS_PASS,
                reason=(
                    "tier=6 panel; both tier-6 reinforcement refs attached "
                    "alongside the muscle-size lineup"
                ),
            )
        return Verification(
            status=STATUS_FAIL,
            reason=(
                "tier=6 panel but tier-6 reinforcement refs NOT attached. "
                "Expected both PNGs from "
                "skills/comic-production/references/peak-body-scale/tier-6/ "
                "(tier-6-full-body.png + tier-6-anatomical-detail.png) on disk. "
                "Falling back to lineup-only is significantly less reliable "
                "at tier 6 — the multi-figure chart interpolates downward "
                "and the rendered body lands at tier 4-5 proportions. Ship "
                "the reinforcement PNGs into the canonical repo path before "
                "regenerating this panel."
            ),
        )

    def retry_strategy(self, panel: dict, ctx: dict, failure: dict) -> dict:
        if not ctx.get("tier6_refs_attached"):
            return {
                "kind": "auto_resubmit_with_corrected_refs",
                "rule_id": self.id,
                "strengthening": (
                    "attach BOTH tier-6 reinforcement PNGs at generation "
                    "time from skills/comic-production/references/peak-body-"
                    "scale/tier-6/ (tier-6-full-body.png + tier-6-anatomical-"
                    "detail.png) IN ADDITION TO the muscle-size lineup. "
                    "Verbal-only tier-6 anchoring under-renders consistently."
                ),
            }
        return {
            "kind": "auto_resubmit_with_stronger_contribution",
            "rule_id": self.id,
            "strengthening": (
                "the reinforcement refs are attached but the rendered "
                "proportions still under-shot. Escalate the directive: name "
                "the specific muscle groups (deltoid mass, pectoral "
                "development, lat spread, oblique definition, bicep peak, "
                "quad size) AND the bust volume / forward projection as "
                "tier-6 targets, and over-spec — instruct the model to "
                "render LARGER than the reinforcement refs show (model "
                "normalizes off-distribution features toward average, so "
                "over-spec lands the output at parity)."
            ),
        }
