"""Match the attached environment reference.

Short directive emitted when an env ref is attached for this panel,
telling the model to match the architecture, lighting baseline, scale,
and depth shown in the ref.

Replaces the inline "ENVIRONMENT — ref anchor" prose that
compose_prompt was emitting directly. Behavior is the same; emission
moves into the rules taxonomy so all match-the-ref directives live
together.

Slot: 9_environment. Fires before L23 (the env-fallback) because in
the L10-correct path the env ref is always attached and L23 only fires
when ref attachment fails.
"""

from __future__ import annotations

from .._base import (
    Rule, Verification, STATUS_PASS, STATUS_SKIPPED, CATEGORY_MATCH,
)


class MatchEnv(Rule):
    id = "MATCH_ENV"
    title = "Match the attached environment reference"
    slot = "9_environment_match"  # distinct sub-slot to fire BEFORE L23 fallback
    section_label = "ENVIRONMENT — match the ref"
    severity = "soft"
    applicable_transformations = ("*",)
    category = CATEGORY_MATCH

    def should_apply(self, panel: dict, ctx: dict) -> bool:
        return ctx.get("env_ref") is not None

    def compose_contribution(self, panel: dict, ctx: dict, slot: str) -> str | None:
        if slot != "9_environment_match":
            return None
        if not self.should_apply(panel, ctx):
            return None
        location_slug = ctx.get("location_slug") or ""
        env_anchor_from = ctx.get("env_anchor_from")
        if env_anchor_from:
            anchor_panel = env_anchor_from.get("panel", {})
            anchor_id = anchor_panel.get("panel_id", "?")
            return (
                f"Location: {location_slug}. The attached environment "
                f"reference IS this location (it's the accepted "
                f"establishing shot from panel `{anchor_id}`). Match it "
                "exactly for architecture, lighting baseline, scale, "
                "and depth."
            )
        return (
            f"Location: {location_slug}. Match the attached environment "
            "reference for architecture, lighting baseline, scale, and "
            "depth. Do not reinterpret the location."
        )

    def verify_pre_render(self, panel: dict, ctx: dict) -> Verification:
        if self.should_apply(panel, ctx):
            return Verification(
                status=STATUS_PASS,
                reason="env ref attached — match directive emitted",
            )
        return Verification(
            status=STATUS_SKIPPED,
            reason="no env ref attached — L23 fallback handles env if needed",
        )
