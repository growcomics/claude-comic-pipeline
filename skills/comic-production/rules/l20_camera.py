"""L20 — Camera distance bias (in-prompt directive piece).

This module owns the in-prompt body-region camera directive: when a panel
has a body-region `transformation_beat` (chest / hips / rear / arms / abs /
legs / shoulders / back / suit_fail), inject aggressive ECU vocabulary so
the model commits to tight framing before reading the action content.

The chapter-aggregate L20 check (mean distance, per-beat overshoot) lives in
build_plan as `L20_chapter` and stays there for phase 3. Phase 4 migrates
the rules_audit.py-style checks into rule modules; until then the two halves
of L20 live in two places.

See:
  - skills/comic-production/references/lessons-learned.md § L20
  - skills/comic-production/references/the-rules-explained.md § L20 (strengthened May 2026)
  - skills/comic-production/references/camera-distance-analysis/README.md
"""

from __future__ import annotations

from ._base import Rule, Verification, STATUS_PASS, STATUS_SKIPPED


# Mirror of next_panel._BODY_REGION_BEAT_TO_REGION. The two must stay in sync
# until phase 3 cleanup removes the legacy copy; for now this module is the
# canonical source.
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
    severity = "hard"
    applicable_transformations = ("*",)

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
        # If post-render vision (phase 5) shows the framing is too wide,
        # escalate the DOMINATES language one more notch.
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
