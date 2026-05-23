"""Match the attached prior panel — state continuity.

Replaces the inline "STATE ANCHOR — L1.5" prose that compose_prompt
was emitting directly. When a prior panel is attached as a state
anchor, this rule emits the short directive instructing the model to
carry forward costume state, hair state, body size, and any cumulative
damage from the attached prior panel.

Paired with attach/prior_panel.py which decides WHICH prior panel to
attach.

Rule ID: L1 (the original L1 chaining lesson; previously emitted inline
without a rule ID, recorded in trace as "L1.5").
"""

from __future__ import annotations

from .._base import (
    Rule, Verification, STATUS_PASS, STATUS_SKIPPED, CATEGORY_MATCH,
)


class L1(Rule):
    id = "L1"
    title = "Match the attached prior panel for state continuity"
    slot = "10_state_anchor"
    section_label = "STATE ANCHOR — L1"
    severity = "soft"
    applicable_transformations = ("*",)
    category = CATEGORY_MATCH
    vision_rubric = (
        "Look at this rendered comic panel and compare it to the attached "
        "prior panel (the state anchor). Does the costume state continue "
        "(same tears in the same places, same level of dishevelment)? Does "
        "the hair state match (same up/down/wet/dry as the prior panel "
        "if there's no explicit state change in the shotlist)? Does the "
        "body size carry forward (never regress)? PASS if continuity holds. "
        "FAIL with a description of the regression (e.g. 'costume tears "
        "disappeared between panels')."
    )

    def should_apply(self, panel: dict, ctx: dict) -> bool:
        return ctx.get("anchor") is not None

    def compose_contribution(self, panel: dict, ctx: dict, slot: str) -> str | None:
        if slot != "10_state_anchor":
            return None
        anchor = ctx.get("anchor")
        if not anchor:
            return None
        anchor_panel = anchor.get("panel", {})
        anchor_id = anchor_panel.get("panel_id", "?")
        anchor_view = anchor_panel.get("camera", "?")
        return (
            f"Match the attached prior panel `{anchor_id}` ({anchor_view}) "
            "for state continuity: preserve costume state (tears, "
            "dishevelment), hair state, body size, and any cumulative "
            "damage. Costume tears never regress across panels."
        )

    def verify_pre_render(self, panel: dict, ctx: dict) -> Verification:
        if self.should_apply(panel, ctx):
            anchor = ctx.get("anchor")
            anchor_id = anchor.get("panel", {}).get("panel_id", "?")
            return Verification(
                status=STATUS_PASS,
                reason=f"prior panel `{anchor_id}` attached as state anchor",
            )
        return Verification(
            status=STATUS_SKIPPED,
            reason="no prior panel attached (first panel, ECU-face, etc.)",
        )
