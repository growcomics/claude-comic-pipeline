"""Attach the canonical face card for every named character in the panel.

Pre-refactor, face-card attachment was inline in
next_panel.build_plan(). This module documents the contract and gives
audit tools a place to hook in.

The face card carries the character's CANONICAL look — face features,
hair style, color, accessories that always travel with the character.
Per L10, the face card is the source of truth for identity; no prompt
text describes the face.

Expected location: `references/characters/<slug>/face-card.png` (or
whichever path is set in cast[].ref_folder + a face filename
convention).
"""

from __future__ import annotations

from pathlib import Path

from .._base import (
    Rule, Verification, STATUS_PASS, STATUS_SKIPPED, CATEGORY_ATTACH,
)


class AttachFaceCard(Rule):
    id = "ATTACH_FACE_CARD"
    title = "Attach canonical face card per named character"
    slot = ""  # ATTACH rules do not emit text at a composition slot
    section_label = "ATTACH — face card"
    severity = "hard"
    applicable_transformations = ("*",)
    category = CATEGORY_ATTACH

    def should_apply(self, panel: dict, ctx: dict) -> bool:
        return bool(panel.get("characters"))

    def attached_refs(self, panel: dict, ctx: dict) -> list[dict]:
        refs: list[dict] = []
        project_root = ctx.get("project_root")
        cast_lookup = ctx.get("cast_lookup") or {}
        for char_id in (panel.get("characters") or []):
            entry = cast_lookup.get(char_id) or {}
            ref_folder = entry.get("ref_folder")
            if not ref_folder or not project_root:
                refs.append({
                    "kind": "MISSING_face_card",
                    "path": None,
                    "character": char_id,
                    "reason": (f"{char_id}: cast[].ref_folder not set OR "
                               "project_root not in ctx"),
                })
                continue
            candidate = Path(project_root) / ref_folder / "face-card.png"
            if candidate.exists():
                refs.append({
                    "kind": "face_card",
                    "path": str(candidate.relative_to(project_root)),
                    "character": char_id,
                    "reason": f"{char_id}: canonical face card (L10 identity ref)",
                })
            else:
                refs.append({
                    "kind": "MISSING_face_card",
                    "path": str(candidate.relative_to(project_root)),
                    "character": char_id,
                    "reason": f"{char_id}: face card expected at {candidate} but missing",
                })
        return refs

    def verify_pre_render(self, panel: dict, ctx: dict) -> Verification:
        refs = self.attached_refs(panel, ctx)
        missing = [r for r in refs if r["kind"].startswith("MISSING_")]
        if not refs:
            return Verification(
                status=STATUS_SKIPPED,
                reason="no characters in panel",
            )
        if missing:
            return Verification(
                status=STATUS_PASS,  # soft warning, not a hard fail
                reason=(f"face card(s) missing for "
                        f"{[m['character'] for m in missing]}"),
            )
        return Verification(
            status=STATUS_PASS,
            reason=f"face card attached for {len(refs)} character(s)",
        )
