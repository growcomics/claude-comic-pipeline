"""L18 — Pose anatomy coherence.

Universal soft guardrail. Mandatory render line at the end of every panel
prompt: torso, hips, abdomen, and feet face the same direction; no impossible
twists between hips and torso; all limbs attach naturally. Cheap (~30 tokens),
auto-injected on every panel regardless of camera or beat.

See:
  - skills/comic-production/references/lessons-learned.md § L18
  - skills/comic-production/references/the-rules-explained.md § L18
"""

from __future__ import annotations

from ._base import Rule, Verification, STATUS_PASS


L18_ANATOMY_ANCHOR = (
    "L18 anatomy coherence: torso, hips, abdomen, and feet all face the same "
    "direction. No impossible twists between hips and torso. All limbs attach "
    "naturally to the body. Both shoulders visible if the chest is visible; "
    "both hips visible if the legs are visible."
)


class L18(Rule):
    id = "L18"
    title = "Pose anatomy coherence"
    slot = "13_anatomy_guardrail"
    severity = "soft"
    applicable_transformations = ("*",)
    vision_rubric = (
        "Look at this rendered comic panel and check the anatomy. Count: how "
        "many arms? How many legs? How many heads? Are torso, hips, and feet "
        "facing the same direction (or is there an impossible twist)? Do "
        "limbs attach naturally to the body? If the chest is visible, are "
        "both shoulders visible? If legs are visible, are both hips visible? "
        "PASS if anatomy is coherent (correct limb count, consistent facing, "
        "natural attachment). FAIL with a specific description if any of "
        "these check fail."
    )

    def should_apply(self, panel: dict, ctx: dict) -> bool:
        return True  # universal soft guardrail

    def compose_contribution(self, panel: dict, ctx: dict, slot: str) -> str | None:
        if slot != "13_anatomy_guardrail":
            return None
        return L18_ANATOMY_ANCHOR

    def verify_pre_render(self, panel: dict, ctx: dict) -> Verification:
        return Verification(
            status=STATUS_PASS,
            reason="universal soft guardrail — always emitted",
        )

    def retry_strategy(self, panel: dict, ctx: dict, failure: dict) -> dict:
        return {
            "kind": "auto_resubmit_with_stronger_contribution",
            "rule_id": self.id,
            "strengthening": (
                "expand the anatomy line with explicit limb-count negation: "
                "'exactly two arms, exactly two legs, exactly one head, all "
                "limbs visible and attached naturally — no extra hands, no "
                "missing fingers, no impossible joint angles'"
            ),
        }
