"""L21 — Suppress in-scene rendering of reference images.

Lesson: every panel prompt that attaches at least one ref must include the
exclusion clause forbidding the model from rendering the ref as a physical
scene object (a small photo on a sleeve, a badge, a poster, a watermark-style
figure number). Empirically validated on chun-li-grok-validation panel 6 v2,
where the lineup figure's "1" label rendered as a watermark in the corner of
the panel; the v3 with the exclusion clause cleared it.

See:
  - skills/comic-production/references/lessons-learned.md § L21
  - skills/comic-production/references/the-rules-explained.md § L21
"""

from __future__ import annotations

from ._base import Rule, Verification, STATUS_PASS, STATUS_SKIPPED


L21_REF_EXCLUSION = (
    "DO NOT render any reference image as a physical scene object — "
    "no inset photos, no watermarks, no figure numbers, no badges. "
    "References are for identity, proportion, location, and state guidance "
    "only and must NOT appear inside the rendered scene."
)


class L21(Rule):
    id = "L21"
    title = "Suppress in-scene rendering of reference images"
    slot = "12_ref_safety"
    severity = "soft"
    applicable_transformations = ("*",)
    vision_rubric = (
        "Look at this rendered comic panel. Does the panel contain any element "
        "that appears to be a reference image rendered as a physical scene "
        "object — a tiny inset photo, a badge, a poster on a wall, a "
        "watermark-style figure number or label floating in the corner, a "
        "patch with a face on it, or any visible '1' / '2' / 'figure N' text "
        "where there shouldn't be one? Be specific about what you spot and "
        "where in the frame (corner, sleeve, wall, etc). PASS if no such "
        "element appears; FAIL with a description of the substitute and its "
        "location if one does."
    )

    def should_apply(self, panel: dict, ctx: dict) -> bool:
        """Fire whenever at least one ref is attached to the panel."""
        env_ref = ctx.get("env_ref")
        anchor = ctx.get("anchor")
        lineup_attached = ctx.get("lineup_attached", False)
        return bool(env_ref) or bool(anchor) or bool(lineup_attached)

    def compose_contribution(self, panel: dict, ctx: dict, slot: str) -> str | None:
        if slot != "12_ref_safety":
            return None
        if not self.should_apply(panel, ctx):
            return None
        return L21_REF_EXCLUSION

    def verify_pre_render(self, panel: dict, ctx: dict) -> Verification:
        if self.should_apply(panel, ctx):
            env_ref = ctx.get("env_ref")
            anchor = ctx.get("anchor")
            lineup_attached = ctx.get("lineup_attached", False)
            return Verification(
                status=STATUS_PASS,
                reason=(
                    f"at least one ref attached "
                    f"(env={bool(env_ref)}, anchor={bool(anchor)}, "
                    f"lineup={lineup_attached})"
                ),
            )
        return Verification(
            status=STATUS_SKIPPED,
            reason="no refs attached — ref-exclusion clause unnecessary",
        )

    def retry_strategy(self, panel: dict, ctx: dict, failure: dict) -> dict:
        """When post-render vision spots a ref rendered as a scene object,
        strengthen the negation list. The substitute the model produced
        (watermark, badge, photo, poster, figure-number, holographic overlay)
        gets added to the negation enumeration on retry.
        """
        substitute = (failure.get("evidence") or {}).get("substitute_rendered")
        if substitute:
            strengthening = (
                f"add explicit negation of the substitute the model produced "
                f"({substitute}) to the ref-exclusion clause"
            )
        else:
            strengthening = (
                "expand the ref-exclusion clause to enumerate every substitute "
                "the model commonly produces: 'no badges, no holographic overlays, "
                "no figure-number watermarks, no inset photos, no posters'"
            )
        return {
            "kind": "auto_resubmit_with_stronger_contribution",
            "rule_id": self.id,
            "strengthening": strengthening,
        }
