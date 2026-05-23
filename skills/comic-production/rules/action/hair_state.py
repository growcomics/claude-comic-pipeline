"""L22 — Hair state per panel (state delta, not appearance).

Hair STYLE (Chun Li's twin buns, ribbon design, length, color) is part
of the character's identity and belongs in the face card. Hair STATE
(up/down, wet/dry, intact/coming-loose, bound/released) is a per-panel
delta that the shotlist author owns.

Reads panel.hair_state and surfaces it as a named, anchored prompt line.
Reclassified as ACTION (state delta) in the 2026-05-23 refs-are-truth
refactor — the rule is fine as-is, but it lives in the action category
because it describes a momentary state, not character appearance.

See:
  - skills/comic-production/references/lessons-learned.md § L22
  - memory: feedback_dont_invent_state_changes
"""

from __future__ import annotations

from .._base import (
    Rule, Verification, STATUS_PASS, STATUS_SKIPPED, CATEGORY_ACTION,
)


class L22(Rule):
    id = "L22"
    title = "Hair state must be explicit in every face-visible panel"
    slot = "4_subject_state"
    section_label = "HAIR — L22"
    severity = "soft"
    applicable_transformations = ("*",)
    category = CATEGORY_ACTION
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
