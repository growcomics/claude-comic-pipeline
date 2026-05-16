"""L24 — Suppress anachronistic accessories explicitly.

Models hallucinate modern accessories (wristwatches, bracelets, rings,
earrings, necklaces) on characters even when the canonical character wears
none. Wrists, neck, ears, and ring fingers are hotspots.

Reads per-character `cast[].accessories` block with `canonical` text and a
`negation` list. The negation list is the load-bearing part — enumerating
the substitutes the model actually produces suppresses the prior.

See:
  - skills/comic-production/references/lessons-learned.md § L24
  - skills/comic-production/references/the-rules-explained.md § L24
"""

from __future__ import annotations

from ._base import Rule, Verification, STATUS_PASS, STATUS_SKIPPED


# Cameras where wrists / neck / ears / fingers may be in frame — i.e. where
# the model has room to hallucinate. ECU-region on an arm is included
# because the wrist is usually at the bottom of frame.
_L24_CAMERAS = {
    "ecu-face", "ecu-region", "mcu", "medium", "cowboy",
    "front-full", "3q-full", "back-full", "side-full", "profile",
    "low-angle-front", "low-angle-back", "high-angle",
    "wide-establish", "splash",
}


def _accessory_line(panel: dict, cast_lookup: dict, camera: str) -> str | None:
    if camera not in _L24_CAMERAS:
        return None
    chars = panel.get("characters", []) or []
    if not chars:
        return None
    pieces: list[str] = []
    for char_id in chars:
        char = cast_lookup.get(char_id)
        if not char:
            continue
        acc = char.get("accessories")
        if not acc:
            continue
        canonical = (acc.get("canonical") or "").strip()
        negation = acc.get("negation") or []
        if not canonical and not negation:
            continue
        if canonical:
            pieces.append(f"Accessories ({char_id}): {canonical} — canonical, ONLY these.")
        if negation:
            neg_terms = ", ".join(f"NO {n}" for n in negation)
            pieces.append(neg_terms + ", no anachronistic accessories.")
    if not pieces:
        return None
    return " ".join(pieces)


class L24(Rule):
    id = "L24"
    title = "Suppress anachronistic accessories explicitly"
    slot = "4_subject_state"
    severity = "soft"
    applicable_transformations = ("*",)
    vision_rubric = (
        "Look at this rendered comic panel and check the character's wrists, "
        "neck, ears, and fingers (whichever are visible in the frame). Are "
        "there any anachronistic accessories — wristwatches, smartwatches, "
        "bracelets, rings, earrings, necklaces, dark studded cuffs, leather "
        "cuffs, tactical gloves — that the canonical character should NOT be "
        "wearing? PASS if no anachronistic accessories appear. FAIL with a "
        "description of the substitute and the body part it appeared on."
    )

    def should_apply(self, panel: dict, ctx: dict) -> bool:
        camera = ctx.get("camera") or ""
        cast_lookup = ctx.get("cast_lookup") or {}
        return _accessory_line(panel, cast_lookup, camera) is not None

    def compose_contribution(self, panel: dict, ctx: dict, slot: str) -> str | None:
        if slot != "4_subject_state":
            return None
        camera = ctx.get("camera") or ""
        cast_lookup = ctx.get("cast_lookup") or {}
        return _accessory_line(panel, cast_lookup, camera)

    def verify_pre_render(self, panel: dict, ctx: dict) -> Verification:
        camera = ctx.get("camera") or ""
        cast_lookup = ctx.get("cast_lookup") or {}
        line = _accessory_line(panel, cast_lookup, camera)
        if line is not None:
            return Verification(
                status=STATUS_PASS,
                reason=(f"camera={camera!r} may include wrists/neck/etc and "
                        "cast has accessories block"),
            )
        return Verification(
            status=STATUS_SKIPPED,
            reason=("no cast[].accessories block, or camera does not include "
                    "wrists/neck/etc in frame"),
        )

    def retry_strategy(self, panel: dict, ctx: dict, failure: dict) -> dict:
        substitute = (failure.get("evidence") or {}).get("substitute_rendered")
        if substitute:
            strengthening = (
                f"add '{substitute}' to the cast[].accessories.negation list "
                "for the affected character so future panels suppress it"
            )
        else:
            strengthening = (
                "expand cast[].accessories.negation with the common substitutes: "
                "wristwatch, smartwatch, bracelet, ring, earring, necklace, "
                "dark studded cuff, leather cuff, tactical glove"
            )
        return {
            "kind": "auto_resubmit_with_stronger_contribution",
            "rule_id": self.id,
            "strengthening": strengthening,
        }
