"""L21 — Suppress in-scene rendering of reference images.

Negation-only safety rule. Tells the model NOT to render any attached
reference image as a physical scene object (badge, watermark, inset
photo, figure-number overlay).

Moved from rules/l21_ref_safety.py in the 2026-05-23 refs-are-truth
refactor. Behavior unchanged — only the module path moved and the
category attribute was added.
"""

from __future__ import annotations

from .._base import (
    Rule, Verification, STATUS_PASS, STATUS_SKIPPED, CATEGORY_SAFETY,
)


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
    section_label = "REF SAFETY — L21 no-render-as-prop"
    severity = "soft"
    applicable_transformations = ("*",)
    category = CATEGORY_SAFETY
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
