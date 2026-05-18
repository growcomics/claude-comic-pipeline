"""L15 — Female characters must read as beautiful.

Female cast members render at "default attractiveness" without explicit
prompt vocabulary — pleasant but unremarkable, average AI-generated faces.
The fix is a mandatory glamour anchor: vogue-cover face quality, sculpted
features, expressive eyes, magazine-cover finish.

Detection heuristic on cast entries: sex in {"f", "female", "woman"} or
pronoun in {"she", "her", "her/hers", "she/her"}. Defaults to female when
both fields are unset (most comics in this pipeline are FMG-heavy).
Suppressible per character via cast[].glamour_anchor: false.

Phase 3 ships as FMG-only (applicable_transformations=("fmg",)). The
vocabulary is universal enough that a future MMG-male-handsome variant
could share the same module or live as a sibling.

See:
  - skills/comic-production/references/lessons-learned.md § L15
  - skills/comic-production/references/the-rules-explained.md § L15
"""

from __future__ import annotations

from ._base import Rule, Verification, STATUS_PASS, STATUS_SKIPPED


L15_FEMALE_BEAUTY_ANCHOR = (
    "L15 glamour anchor: render any female character in this panel with "
    "vogue-cover face quality — sculpted cheekbones, refined jawline, "
    "expressive eyes with long natural lashes and depth in the gaze, "
    "magazine-cover finish. Strikingly beautiful — the kind of face that "
    "commands attention. NOT plain, NOT generic-AI-face."
)


def _female_focal_in_panel(panel: dict, cast_lookup: dict) -> bool:
    """True iff any female cast member is in the panel and not suppressed
    via cast[].glamour_anchor: false."""
    for char_id in (panel.get("characters") or []):
        entry = cast_lookup.get(char_id) or {}
        if entry.get("glamour_anchor") is False:
            continue  # explicit opt-out
        sex = (entry.get("sex") or "").lower()
        pronoun = (entry.get("pronoun") or "").lower()
        if (sex in {"f", "female", "woman"}
                or pronoun in {"she", "her", "her/hers", "she/her"}):
            return True
        # If sex and pronoun unset, default-assume female (most pipeline
        # comics are FMG-heavy). Override via explicit sex: "m" or
        # glamour_anchor: false on the cast entry.
        if not sex and not pronoun and entry.get("glamour_anchor") is not False:
            return True
    return False


class L15(Rule):
    id = "L15"
    title = "Female characters must read as beautiful"
    slot = "3_subject_identity"
    section_label = "BEAUTY ANCHOR — L15"
    severity = "soft"
    applicable_transformations = ("fmg",)
    vision_rubric = (
        "Look at this rendered comic panel where a female character is in "
        "frame. Does the face read as vogue-cover / magazine-cover quality "
        "— sculpted cheekbones, refined jawline, expressive eyes with depth, "
        "striking beauty? Or does it look like a generic AI-generated "
        "face (plain features, flat eyes, average-looking)? PASS if the face "
        "reads as 'commands attention, magazine-cover finish'. FAIL with a "
        "description if the face reads as generic/plain/AI-flat."
    )

    def should_apply(self, panel: dict, ctx: dict) -> bool:
        cast_lookup = ctx.get("cast_lookup") or {}
        return _female_focal_in_panel(panel, cast_lookup)

    def compose_contribution(self, panel: dict, ctx: dict, slot: str) -> str | None:
        if slot != "3_subject_identity":
            return None
        if not self.should_apply(panel, ctx):
            return None
        return L15_FEMALE_BEAUTY_ANCHOR

    def verify_pre_render(self, panel: dict, ctx: dict) -> Verification:
        if self.should_apply(panel, ctx):
            return Verification(
                status=STATUS_PASS,
                reason="female cast member detected, glamour anchor injected",
            )
        return Verification(
            status=STATUS_SKIPPED,
            reason="no female cast member in panel (or glamour_anchor=false)",
        )

    def retry_strategy(self, panel: dict, ctx: dict, failure: dict) -> dict:
        return {
            "kind": "auto_resubmit_with_stronger_contribution",
            "rule_id": self.id,
            "strengthening": (
                "escalate the glamour anchor with concrete model-face anchors: "
                "name the face-card ref explicitly and add 'render this exact "
                "face — do not blend toward the generic AI prior'. If the "
                "issue persists, regenerate the face card with vogue-cover "
                "prompt language (see the Supergirl face-card re-roll for "
                "canonical phrasing)."
            ),
        }
