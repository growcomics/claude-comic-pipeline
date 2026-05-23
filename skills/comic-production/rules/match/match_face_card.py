"""Match the attached face card — replaces L10's render-directive paragraph
and L17's canonical-character anchor.

Pre-refactor, two rules emitted prose at slot 3_subject_identity and
slot 11_render_directive describing what the character's face should
look like. That violated L10 ("references are the truth").

Post-refactor, this rule emits a single short line per slot pointing at
the attached face card. The face card itself carries the canonical look.
For IP characters (cast[].canonical=true), the line names the
characters so the model knows which face card slot maps to which
character.

Replaces:
  - rules/l10_render_directive.py (the ~300 char L10_RENDER_DIRECTIVE)
  - rules/l17_canonical.py (the per-character anchor prose)

The L10 rule ID is preserved at slot 11_render_directive so audit
ledgers stay interpretable. The L17 rule ID continues at slot
3_subject_identity for canonical-character panels.
"""

from __future__ import annotations

from .._base import (
    Rule, Verification, STATUS_PASS, STATUS_SKIPPED, CATEGORY_MATCH,
)


def _has_canonical(panel: dict, cast_lookup: dict) -> list[str]:
    out: list[str] = []
    for char_id in (panel.get("characters") or []):
        entry = cast_lookup.get(char_id) or {}
        if entry.get("canonical"):
            out.append(char_id)
    return out


class L10(Rule):
    """Render directive — one-line match instruction. Was the
    L10_RENDER_DIRECTIVE paragraph; now points at the attached refs."""

    id = "L10"
    title = "References are the truth, prompts are deltas"
    slot = "11_render_directive"
    section_label = "RENDER DIRECTIVE — L10"
    severity = "hard"
    applicable_transformations = ("*",)
    category = CATEGORY_MATCH
    vision_rubric = (
        "Look at this rendered comic panel and compare it to the attached "
        "reference images. Does the rendered character match the face card "
        "(same face, same canonical features)? Does the costume match the "
        "body baseline (same garment, same colors, same accessories)? If a "
        "location ref is attached, does the rendered background match it "
        "(same architecture, same lighting baseline)? PASS if visual "
        "identity matches the refs. FAIL with a specific description of the "
        "drift."
    )

    def should_apply(self, panel: dict, ctx: dict) -> bool:
        return True

    def compose_contribution(self, panel: dict, ctx: dict, slot: str) -> str | None:
        if slot != "11_render_directive":
            return None
        return (
            "Match the attached references exactly for identity, costume, "
            "and location. The prompt above describes only what is NEW in "
            "this panel (camera, pose, action, momentary state); identity "
            "is fixed by the refs."
        )

    def verify_pre_render(self, panel: dict, ctx: dict) -> Verification:
        return Verification(
            status=STATUS_PASS,
            reason="match-the-refs directive always emitted",
        )

    def retry_strategy(self, panel: dict, ctx: dict, failure: dict) -> dict:
        return {
            "kind": "auto_resubmit_with_corrected_refs",
            "rule_id": self.id,
            "strengthening": (
                "the model drifted from the attached refs. Either the face "
                "card / body / env ref is not strong enough (regenerate it) "
                "or the prompt is contradicting the ref (audit the action "
                "delta for accidental appearance prose)."
            ),
        }


class L17(Rule):
    """Canonical-character match — one-line directive naming the IP
    characters whose face card to match. Was the L17 anchor paragraph
    plus per-character canonical_anchor prose."""

    id = "L17"
    title = "Match canonical face card for IP characters"
    slot = "3_subject_identity"
    section_label = "CHARACTER — L17 match canonical face card"
    severity = "hard"
    applicable_transformations = ("*",)
    category = CATEGORY_MATCH
    vision_rubric = (
        "Look at this rendered comic panel. The panel features an IP / "
        "canonical character (Chun Li, Supergirl, April O'Neil, Lex Luthor). "
        "Compare the rendered character to the attached canonical face card: "
        "are the load-bearing canonical details correct? Or did the model "
        "drift toward a generic AI interpretation? PASS if the character is "
        "recognizable as the canonical version. FAIL with a description of "
        "the specific canon details that drifted."
    )

    def should_apply(self, panel: dict, ctx: dict) -> bool:
        cast_lookup = ctx.get("cast_lookup") or {}
        return bool(_has_canonical(panel, cast_lookup))

    def compose_contribution(self, panel: dict, ctx: dict, slot: str) -> str | None:
        if slot != "3_subject_identity":
            return None
        cast_lookup = ctx.get("cast_lookup") or {}
        canon_ids = _has_canonical(panel, cast_lookup)
        if not canon_ids:
            return None
        ids_str = ", ".join(canon_ids)
        return (
            f"Match the attached canonical face card for {ids_str} exactly. "
            "The face card IS the canon — do not reinterpret from the "
            "character name alone."
        )

    def verify_pre_render(self, panel: dict, ctx: dict) -> Verification:
        cast_lookup = ctx.get("cast_lookup") or {}
        if _has_canonical(panel, cast_lookup):
            return Verification(
                status=STATUS_PASS,
                reason="cast[].canonical=true — match-canon directive emitted",
            )
        return Verification(
            status=STATUS_SKIPPED,
            reason="no character with cast[].canonical=true in panel",
        )

    def retry_strategy(self, panel: dict, ctx: dict, failure: dict) -> dict:
        return {
            "kind": "auto_resubmit_with_different_face_card",
            "rule_id": self.id,
            "strengthening": (
                "the rendered character drifted from canon. The face card "
                "may be off-canon — regenerate it from official source art. "
                "Per L10, do NOT re-add prose describing what the canonical "
                "version looks like; fix the ref."
            ),
        }
