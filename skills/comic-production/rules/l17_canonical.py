"""L17 — Known/canonical characters can't drift in appearance.

IP characters (Chun Li, Lex Luthor, Supergirl, April O'Neil) render with
materially wrong canon details without explicit canonical anchoring. The
model has a learned representation but treats the name as a soft hint —
without "canonical version of X" framing + a negation of generic
interpretation, the output lands somewhere that loosely satisfies the
training prior + the prompt without rigorously matching canon.

Reads `cast[].canonical: true` and `cast[].canonical_anchor` text strings.

See:
  - skills/comic-production/references/lessons-learned.md § L17
  - skills/comic-production/references/the-rules-explained.md § L17
"""

from __future__ import annotations

from ._base import Rule, Verification, STATUS_PASS, STATUS_SKIPPED


def _canonical_anchors(panel: dict, cast_lookup: dict) -> list[str]:
    out: list[str] = []
    for char_id in (panel.get("characters") or []):
        entry = cast_lookup.get(char_id) or {}
        if not entry.get("canonical"):
            continue
        anchor_text = entry.get("canonical_anchor") or ""
        if anchor_text:
            out.append(f"{char_id}: {anchor_text}")
        else:
            out.append(
                f"{char_id}: render the canonical published version, NOT a "
                "generic interpretation"
            )
    return out


class L17(Rule):
    id = "L17"
    title = "Known/canonical characters can't drift"
    slot = "3_subject_identity"
    section_label = "CHARACTER — L17 canonical anchor"
    severity = "hard"
    applicable_transformations = ("*",)
    vision_rubric = (
        "Look at this rendered comic panel. The panel features an IP / "
        "canonical character (e.g. Chun Li from Street Fighter, Supergirl, "
        "April O'Neil, Lex Luthor). Compare the rendered character to the "
        "canonical published version: are the load-bearing canonical details "
        "correct (Chun Li: ox-horn hair buns + blue cheongsam + white spiked "
        "wristbands; Supergirl: blue suit + red cape + S-shield)? Or did the "
        "model drift toward a generic AI interpretation (loose flowing hair, "
        "wrong garment, missing accessories)? PASS if the character is "
        "recognizable as the canonical version. FAIL with a description of "
        "the specific canon details that drifted."
    )

    def should_apply(self, panel: dict, ctx: dict) -> bool:
        cast_lookup = ctx.get("cast_lookup") or {}
        return bool(_canonical_anchors(panel, cast_lookup))

    def compose_contribution(self, panel: dict, ctx: dict, slot: str) -> str | None:
        if slot != "3_subject_identity":
            return None
        cast_lookup = ctx.get("cast_lookup") or {}
        anchors = _canonical_anchors(panel, cast_lookup)
        if not anchors:
            return None
        return (
            "L17 canonical anchor: render the canonical published versions of "
            "these IP characters EXACTLY as fans recognize them. "
            + " ".join(anchors)
            + ". Do not drift toward generic AI interpretations."
        )

    def verify_pre_render(self, panel: dict, ctx: dict) -> Verification:
        cast_lookup = ctx.get("cast_lookup") or {}
        if _canonical_anchors(panel, cast_lookup):
            return Verification(
                status=STATUS_PASS,
                reason="cast[].canonical=true with canonical_anchor text",
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
                "swap the face card for a canon-sourced ref (e.g. official "
                "Street Fighter art for Chun Li, not a generic 'Asian martial "
                "artist'). Strengthen the prompt with: 'NOT a generic "
                "interpretation — match the canonical published version "
                "exactly, the way fans recognize the character'."
            ),
        }
