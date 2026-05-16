"""L22 — Hair state must be explicit in every face-visible panel.

Reads `panel.hair_state` from the shotlist. The composer does NOT auto-
derive hair state from tier + transformation_beat — that's the May 14
"don't invent transformation state changes" lesson. Shotlist author owns
the field; this rule just surfaces it as a named, anchored prompt line.

See:
  - skills/comic-production/references/lessons-learned.md § L22
  - skills/comic-production/references/the-rules-explained.md § L22
  - memory: feedback_dont_invent_state_changes
"""

from __future__ import annotations

from ._base import Rule, Verification, STATUS_PASS, STATUS_SKIPPED


class L22(Rule):
    id = "L22"
    title = "Hair state must be explicit in every face-visible panel"
    slot = "4_subject_state"
    severity = "soft"
    applicable_transformations = ("*",)
    vision_rubric = (
        "Look at this rendered comic panel and check the character's hair. "
        "The shotlist explicitly declares panel.hair_state (e.g. 'twin buns "
        "with red ribbons'). Does the rendered hair match the declared state "
        "exactly? Compare: number of buns (twin vs single), accessory "
        "presence + color (red ribbons vs grey vs absent), overall length "
        "and style. PASS if the rendered hair matches the declared state. "
        "FAIL with a description of the drift (e.g. 'rendered as single bun "
        "where shotlist declares twin', 'ribbons rendered grey instead of "
        "red')."
    )

    def should_apply(self, panel: dict, ctx: dict) -> bool:
        hs = panel.get("hair_state")
        return bool(hs and isinstance(hs, str) and hs.strip())

    def compose_contribution(self, panel: dict, ctx: dict, slot: str) -> str | None:
        if slot != "4_subject_state":
            return None
        hs = panel.get("hair_state")
        if not hs or not isinstance(hs, str) or not hs.strip():
            return None
        return f"Hair state: {hs.strip()}."

    def verify_pre_render(self, panel: dict, ctx: dict) -> Verification:
        if self.should_apply(panel, ctx):
            return Verification(
                status=STATUS_PASS,
                reason="panel.hair_state explicitly set",
            )
        return Verification(
            status=STATUS_SKIPPED,
            reason="panel.hair_state not set (shotlist author owns this field)",
        )

    def retry_strategy(self, panel: dict, ctx: dict, failure: dict) -> dict:
        # When post-render vision spots hair drift (twin buns became a single
        # bun, ribbons turned grey, hair length jumped), strengthen the line
        # with concrete anchors (color, count, length).
        return {
            "kind": "auto_resubmit_with_stronger_contribution",
            "rule_id": self.id,
            "strengthening": (
                "expand panel.hair_state with concrete visual anchors: name "
                "the count (two buns vs one), color (red ribbons vs grey), "
                "and length explicitly. The shotlist author may need to edit "
                "panel.hair_state to add this detail."
            ),
        }
