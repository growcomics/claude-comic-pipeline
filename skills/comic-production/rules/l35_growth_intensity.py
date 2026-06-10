"""L35 — Growth money-shot intensity: face register + physical manifestation.

Corpus-derived (2026-06-09, research/comic-corpus 9-comic synthesis v2). Two
findings this rule enforces at the panel level:

  - Finding 3: in the reference corpus the growth money-shots crop the FACE
    out (pure body-region ECU) or leave it neutral, so the niche's highest-
    value panels land emotionless. The books that LEAD the transformation with
    a high-intensity face (strain / ecstasy / awe) score a full expression
    point higher. So any growth beat where the face is in frame gets a
    mandatory peak-intensity expression directive.
  - Finding 4: physical manifestation (sweat-sheen, fabric strain, flushed
    taut skin, displaced air) is the genre's dominant escalation signal. On
    growth beats we inject the L7-compliant PHYSICAL cues — never baked SFX
    text or action lines (those are page-composer vector overlays per L7).

The directive branches on whether the face is in frame:
  - body-region ECU beat (chest/arms/abs/... — head cropped per L20): physical
    escalation cues ONLY. No face directive — it would contradict L20's "head
    cropped out of frame".
  - stage_change / whole_body / reveal / aftermath / trigger / first_sensation
    (face in frame): peak-intensity FACE directive + physical cues.

Complements, does not reverse: L20 (where the camera is), L34 (subject
blocking within the frame), L15 (baseline female beauty). L35 governs the
EMOTIONAL register of the face during a growth beat and the physical weight of
the growth itself.

See:
  - skills/comic-production/references/lessons-learned.md § L35
  - skills/comic-production/references/escalation-devices.md
  - research/comic-corpus/synthesis/success-elements.md (Findings 3, 4)
"""

from __future__ import annotations

from ._base import Rule, Verification, STATUS_PASS, STATUS_SKIPPED


# Body-region beats where L20 crops the head OUT — face is not in frame, so
# the face-intensity directive does not apply (only physical manifestation).
_BODY_REGION_BEATS = {
    "chest", "hips", "rear", "arms", "abs", "legs", "back", "shoulders",
    "suit_fail",
}

# Growth beats where the face IS in frame — these get the face directive.
_FACE_VISIBLE_BEATS = {
    "trigger", "first_sensation", "whole_body", "reveal", "aftermath",
}

# All growth beats this rule fires on (union + stage_change handled in code).
_GROWTH_BEATS = _BODY_REGION_BEATS | _FACE_VISIBLE_BEATS


_FACE_INTENSITY = (
    "L35 money-shot intensity: the character's face MUST register the "
    "transformation at PEAK emotional intensity matched to the beat — "
    "overwhelmed strain, ecstatic effort, awe, or triumphant exertion: mouth "
    "open or teeth gritted, eyes wide and blazing (or rolled back in rapture), "
    "brow fully engaged, jaw and neck tension visible, flushed with effort. "
    "The face SELLS the sensation of the growth and pulls the reader into it. "
    "NEVER neutral, calm, slack, or blank during a growth beat — a dead face "
    "here kills the whole panel (the single most-cited weakness in the "
    "reference corpus)."
)

_PHYSICAL_MANIFESTATION = (
    "L35 growth manifestation: render the growth as PHYSICAL scene phenomena — "
    "sweat-sheen and glisten over the swelling muscle, fabric straining and "
    "splitting at the seams across the expanding region, skin taut and flushed, "
    "displaced air and motion (dust, particles, snapping cloth). Physical "
    "phenomena ONLY — no comic-book SFX text and no action lines (those are "
    "added as vector overlays in page-composer per L7)."
)


class L35(Rule):
    id = "L35"
    title = "Growth money-shot intensity (face register + physical manifestation)"
    slot = "6_growth_intensity"
    section_label = "GROWTH INTENSITY — L35"
    severity = "soft"
    applicable_transformations = ("fmg",)
    vision_rubric = (
        "Look at this rendered growth/transformation panel. (A) If a face is "
        "visible: does it register PEAK emotional intensity appropriate to the "
        "beat — strain, ecstasy, awe, or triumphant exertion (open/gritted "
        "mouth, wide or blazing eyes, engaged brow, visible effort)? FAIL if "
        "the face is neutral, calm, slack, or blank during the growth. (B) Does "
        "the growth read as physical phenomena — sweat-sheen, fabric strain, "
        "flushed taut skin, displaced air? PASS only if the face sells the "
        "sensation (when visible) AND the growth has physical weight. FAIL with "
        "a description of which half is missing."
    )

    def _beat(self, panel: dict, ctx: dict) -> str | None:
        return panel.get("transformation_beat")

    def _is_growth(self, panel: dict, ctx: dict) -> bool:
        beat = self._beat(panel, ctx)
        return (beat in _GROWTH_BEATS) or bool(ctx.get("stage_change"))

    def _face_in_frame(self, panel: dict, ctx: dict) -> bool:
        """Face is in frame unless this is a head-cropped body-region ECU."""
        beat = self._beat(panel, ctx)
        if beat in _BODY_REGION_BEATS:
            return False
        return True

    def should_apply(self, panel: dict, ctx: dict) -> bool:
        return self._is_growth(panel, ctx)

    def compose_contribution(self, panel: dict, ctx: dict, slot: str) -> str | None:
        if slot != "6_growth_intensity":
            return None
        if not self._is_growth(panel, ctx):
            return None
        if self._face_in_frame(panel, ctx):
            return f"{_FACE_INTENSITY}\n\n{_PHYSICAL_MANIFESTATION}"
        # Body-region ECU — head cropped per L20; physical cues only.
        return _PHYSICAL_MANIFESTATION

    def verify_pre_render(self, panel: dict, ctx: dict) -> Verification:
        if not self._is_growth(panel, ctx):
            return Verification(
                status=STATUS_SKIPPED,
                reason="not a growth/transformation beat — L35 does not apply",
            )
        face = "face-in-frame (intensity + physical)" if self._face_in_frame(panel, ctx) \
            else "body-region ECU (physical only — head cropped per L20)"
        return Verification(
            status=STATUS_PASS,
            reason=f"growth beat detected, L35 injected: {face}",
        )

    def retry_strategy(self, panel: dict, ctx: dict, failure: dict) -> dict:
        return {
            "kind": "auto_resubmit_with_stronger_contribution",
            "rule_id": self.id,
            "strengthening": (
                "escalate the face directive with mechanical facial-acting "
                "vocabulary from posing-and-expressions.md (eyelid position, "
                "brow angle, mouth shape, neck cords) and name the exact "
                "emotion for the beat. If the money-shot is a body-region ECU "
                "with no face, the fix is at the shotlist level: interleave a "
                "reaction-intercut face panel (per L35 / escalation-devices.md) "
                "rather than strengthening this ECU panel alone."
            ),
        }
