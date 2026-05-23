"""L20 — Camera distance bias (in-prompt directive piece).

Action-only rule. Emits an aggressive ECU vocabulary directive when a
panel has a body-region transformation_beat, so the model commits to
tight framing before reading the action content.

Moved from rules/l20_camera.py in the 2026-05-23 refs-are-truth refactor.
Behavior unchanged.
"""

from __future__ import annotations

from .._base import (
    Rule, Verification, STATUS_PASS, STATUS_SKIPPED, CATEGORY_ACTION,
)


_BODY_REGION_BEAT_TO_REGION = {
    "chest": "chest",
    "hips": "hips and waist",
    "rear": "rear and lower-back",
    "arms": "arms (biceps, shoulders, triceps)",
    "abs": "abdomen and midsection",
    "legs": "legs (quadriceps, hamstrings)",
    "back": "upper back and shoulders",
    "shoulders": "shoulders and deltoids",
    "suit_fail": "the tearing fabric over the body region in transition",
}


class L20(Rule):
    id = "L20"
    title = "Camera distance bias (in-prompt directive)"
    slot = "2_camera_strengthening"
    section_label = "CAMERA — L20 distance bias"
    severity = "hard"
    applicable_transformations = ("*",)
    category = CATEGORY_ACTION
    vision_rubric = (
        "Look at this rendered comic panel. The shotlist declares a body-"
        "region transformation beat (e.g. chest / arms / abs / hips) which "
        "requires an extreme close-up where the named region fills 70%+ of "
        "the frame and the head and feet are cropped OUT. Does the rendered "
        "framing match? Estimate what fraction of the frame is occupied by "
        "the body region. Are the head and feet cropped out? Is this an "
        "ECU/macro framing, or did the camera pull back to medium/full body? "
        "PASS if the region dominates 70%+ and the head/feet are cropped. "
        "FAIL with the actual estimated region-fill percentage if too wide."
    )

    def should_apply(self, panel: dict, ctx: dict) -> bool:
        beat = panel.get("transformation_beat")
        return bool(beat) and beat in _BODY_REGION_BEAT_TO_REGION

    def compose_contribution(self, panel: dict, ctx: dict, slot: str) -> str | None:
        if slot != "2_camera_strengthening":
            return None
        beat = panel.get("transformation_beat")
        if not beat:
            return None
        region = _BODY_REGION_BEAT_TO_REGION.get(beat)
        if not region:
            return None
        return (
            f"L20 framing directive: EXTREME CLOSE-UP on the {region} filling "
            "70%+ of the frame. Macro 100mm lens equivalent, shallow depth-of-field, "
            f"background completely defocused. The {region} DOMINATES the panel — "
            "head and feet cropped OUT of frame. This is a body-region ECU, NOT a "
            "full-body shot. Do not pull back."
        )

    def verify_pre_render(self, panel: dict, ctx: dict) -> Verification:
        beat = panel.get("transformation_beat")
        if beat and beat in _BODY_REGION_BEAT_TO_REGION:
            return Verification(
                status=STATUS_PASS,
                reason=f"transformation_beat={beat} — body-region directive injected",
            )
        return Verification(
            status=STATUS_SKIPPED,
            reason=f"no body-region transformation_beat (got {beat!r})",
        )

    def retry_strategy(self, panel: dict, ctx: dict, failure: dict) -> dict:
        return {
            "kind": "auto_resubmit_with_stronger_contribution",
            "rule_id": self.id,
            "strengthening": (
                "escalate the camera directive to 'the region COMPLETELY FILLS "
                "90% of the frame. Head, shoulders, hips ALL OUT of frame. "
                "NO body context visible. Pure region-only crop.' Add explicit "
                "'NOT a medium shot, NOT a cowboy shot, NOT a 3q-full' negation."
            ),
        }
