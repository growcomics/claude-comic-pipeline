"""L32 — Tier-9 needs dedicated proportion reinforcement refs (sibling of L29/L30/L31).

Tier 9 ("maximum cartoony FMG" per L11's `_BUILD_BY_TIER`) caps the
peak-tier reinforcement series. Same failure mode as L29-L31 (multi-
figure muscle-size-lineup-4-9.png chart averages tier-9 toward middle);
same fix (lineup + dedicated tier-9 reference sheets isolating the
maximum proportions).

The tier-9 PNGs at `peak-body-scale/tier-9/` were chosen 2026-05-16
evening via a user-directed Grok image-edit pass: the user took Sheet A
candidate `bc2bac33` from a 16-gen batch and ran it through Grok with
"Make the breasts bigger, change nothing else" — the resulting composite
(`4b290bcc-b8fe-4daa-bf1b-50c4009226b2`) became BOTH the tier-9 full-body
and the tier-9 anatomical-detail file. The composite layout already
includes both full-body views AND detail insets (biceps profile, chest /
thoracic detail, waist narrowness, leg musculature), so using one image
for both file slots is intentional — not a degradation.

See:
  - skills/comic-production/references/peak-body-scale.md § Tier-9 reinforcement
  - skills/comic-production/references/lessons-learned.md § L32
"""

from __future__ import annotations

from ._base import Rule, Verification, STATUS_PASS, STATUS_FAIL, STATUS_SKIPPED


TIER9_REINFORCEMENT_FILES = (
    "tier-9-full-body.png",
    "tier-9-anatomical-detail.png",
)


L32_DIRECTIVE = (
    "TIER-9 PROPORTION REINFORCEMENT: Two additional reference images "
    "attached showing canonical tier-9 (maximum cartoony FMG) muscle "
    "proportions. These sit ALONGSIDE the muscle-size lineup-4-9, not "
    "in place of it. Match the MAXIMUM bust volume and forward "
    "projection, deltoid mass DWARFING the head (4x normal), bicep WIDER "
    "than the waist by a lot, near-cartoonish pectoral mass, sweeping "
    "V-taper lats with extreme striation, blocky 8-pack abs, tree-trunk "
    "quads — frame-filling muscle MASS approaching comic-superhero "
    "exaggeration shown in these references. Over-render: the model "
    "normalizes off-distribution features toward average, so target the "
    "SAME or LARGER scale than the reinforcement refs show, never "
    "smaller. PROPORTION REFERENCE ONLY — do NOT adopt the clothing, "
    "hair, hairstyle, hair color, skin tone, face, pose, lighting, "
    "background, or setting from these references. Do NOT render the "
    "reference images as physical scene objects (no inset photos, no "
    "annotated overlays, no figure labels, no proportion stats text "
    "floating in the frame). Borrow scale and mass only — character "
    "identity, hair, face, costume, pose, and setting are specified in "
    "the prompt and the other attached reference images."
)


class L32(Rule):
    id = "L32"
    title = "Tier-9 needs dedicated proportion reinforcement refs"
    slot = "8b_tier_reinforcement"
    section_label = "TIER-9 REINFORCEMENT — L32"
    severity = "hard"
    applicable_transformations = ("fmg",)
    vision_rubric = (
        "Look at this rendered comic panel. The panel's shotlist declares "
        "muscle_size_tier == 9 (maximum cartoony FMG) and the tier-9 "
        "reinforcement reference was attached alongside the muscle-size "
        "lineup at generation time.\n\n"
        "MUSCLE: Does the rendered character show tier-9-scale deltoid "
        "mass (4x normal, dwarfing the head with maximum striation), "
        "bicep significantly wider than the waist, near-cartoonish "
        "pectoral mass, tree-trunk quads, sweeping V-taper lats? The "
        "failure mode is the body landing at tier 7-8 proportions because "
        "the lineup-4-9 chart averaged downward.\n\n"
        "BREASTS: Tier-9 bust scale reads as MAXIMUM comic-fantasy — "
        "visibly larger and more dramatically forward-projected than "
        "tier 8 (the user's Grok edit specifically amped this attribute "
        "beyond the base A-02 candidate). PASS only if BOTH muscle AND "
        "breast proportions match the tier-9 reinforcement refs.\n\n"
        "LEAKAGE: Did any element from the reinforcement refs bleed into "
        "the panel that shouldn't have — wrong hairstyle, wrong skin "
        "tone, the reference's grey training top replacing the panel's "
        "costume, the annotated overlay text rendering as a watermark, "
        "the reference's plain studio backdrop overriding the panel's "
        "setting? FAIL with a description of which attribute leaked."
    )

    def should_apply(self, panel: dict, ctx: dict) -> bool:
        tier = panel.get("muscle_size_tier")
        try:
            return int(tier) == 9
        except (TypeError, ValueError):
            return False

    def compose_contribution(self, panel: dict, ctx: dict, slot: str) -> str | None:
        if slot != "8b_tier_reinforcement":
            return None
        if not self.should_apply(panel, ctx):
            return None
        if not ctx.get("tier9_refs_attached"):
            return None
        return L32_DIRECTIVE

    def verify_pre_render(self, panel: dict, ctx: dict) -> Verification:
        if not self.should_apply(panel, ctx):
            return Verification(
                status=STATUS_SKIPPED,
                reason="panel.muscle_size_tier != 9 — L32 only applies at the maximum figure",
            )
        if ctx.get("tier9_refs_attached"):
            return Verification(
                status=STATUS_PASS,
                reason=(
                    "tier=9 panel; tier-9 reinforcement refs attached "
                    "alongside the muscle-size lineup"
                ),
            )
        return Verification(
            status=STATUS_FAIL,
            reason=(
                "tier=9 panel but tier-9 reinforcement refs NOT attached. "
                "Expected the tier-9 PNGs from "
                "skills/comic-production/references/peak-body-scale/tier-9/ "
                "on disk. Falling back to lineup-only at the maximum "
                "tier is the worst-case for the multi-figure interpolation "
                "failure (the chart's tier-9 figure is most distant from "
                "the model's prior)."
            ),
        )

    def retry_strategy(self, panel: dict, ctx: dict, failure: dict) -> dict:
        if not ctx.get("tier9_refs_attached"):
            return {
                "kind": "auto_resubmit_with_corrected_refs",
                "rule_id": self.id,
                "strengthening": (
                    "attach BOTH tier-9 reinforcement PNGs at generation "
                    "time from skills/comic-production/references/peak-body-"
                    "scale/tier-9/. Note: both files are intentionally the "
                    "same composite (user-directed Grok edit) — this is "
                    "not a bug, the layout already includes full-body + "
                    "detail panels in one image."
                ),
            }
        return {
            "kind": "auto_resubmit_with_stronger_contribution",
            "rule_id": self.id,
            "strengthening": (
                "the reinforcement refs are attached but the rendered "
                "proportions still under-shot. Escalate the directive to "
                "maximum: deltoid mass 4x normal DWARFING the head, "
                "bicep MUCH wider than waist, near-cartoonish pectoral "
                "mass, tree-trunk quads, MAXIMUM comic-fantasy bust scale."
            ),
        }
