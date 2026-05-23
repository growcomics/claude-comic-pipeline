"""Attach the internet-sourced-then-3D-converted base reference for the character.

NEW in the 2026-05-23 refs-are-truth refactor.

The user's canonical workflow for bootstrapping a new character:
  1. Find a high-quality reference image of the character on the
     internet (official art, screenshot from game/show, fan art).
  2. Run that image through an image model with a "render this as a
     photoreal 3D model, A-pose, neutral background" prompt.
  3. Save the resulting 3D-converted base render at
     `references/characters/<slug>/internet-3d-base.png`.
  4. Use it as the starting anchor for all subsequent generation —
     paired with the face card (close-up) and the body-tier lineup
     (proportions), this base ref carries the FULL canonical character
     in a clean rendered state the downstream model has zero ambiguity
     about.

This attach rule looks for `internet-3d-base.png` in the character's
ref folder and attaches it for every panel where the character is in
frame. If absent, it surfaces a soft warning suggesting the user run
the reference-acquisition skill to bootstrap one.

See: skills/reference-acquisition/SKILL.md for the workflow that
generates this ref.
"""

from __future__ import annotations

from pathlib import Path

from .._base import (
    Rule, Verification, STATUS_PASS, STATUS_SKIPPED, CATEGORY_ATTACH,
)


INTERNET_3D_BASE_FILENAME = "internet-3d-base.png"


class AttachInternet3DBase(Rule):
    id = "ATTACH_INTERNET_3D_BASE"
    title = "Attach internet-sourced 3D base reference per character"
    slot = ""
    section_label = "ATTACH — internet 3D base"
    severity = "soft"
    applicable_transformations = ("*",)
    category = CATEGORY_ATTACH

    def should_apply(self, panel: dict, ctx: dict) -> bool:
        return bool(panel.get("characters"))

    def attached_refs(self, panel: dict, ctx: dict) -> list[dict]:
        refs: list[dict] = []
        project_root = ctx.get("project_root")
        cast_lookup = ctx.get("cast_lookup") or {}
        if not project_root:
            return refs
        for char_id in (panel.get("characters") or []):
            entry = cast_lookup.get(char_id) or {}
            ref_folder = entry.get("ref_folder")
            if not ref_folder:
                continue
            candidate = (
                Path(project_root) / ref_folder / INTERNET_3D_BASE_FILENAME
            )
            if candidate.exists():
                refs.append({
                    "kind": "internet_3d_base",
                    "path": str(candidate.relative_to(project_root)),
                    "character": char_id,
                    "reason": (
                        f"{char_id}: internet-sourced 3D base ref "
                        "(canonical full-character anchor)"
                    ),
                })
            else:
                # Soft warning — surfaces in the audit but doesn't block
                # generation. Pre-refactor projects don't have these refs;
                # we want them generated going forward but won't break old
                # projects on the first run.
                refs.append({
                    "kind": "MISSING_internet_3d_base",
                    "path": str(candidate.relative_to(project_root)),
                    "character": char_id,
                    "reason": (
                        f"{char_id}: internet-3d-base.png missing at "
                        f"{ref_folder}/. Run the reference-acquisition "
                        "skill to bootstrap one from an internet image."
                    ),
                })
        return refs

    def verify_pre_render(self, panel: dict, ctx: dict) -> Verification:
        refs = self.attached_refs(panel, ctx)
        if not refs:
            return Verification(
                status=STATUS_SKIPPED,
                reason="no characters in panel",
            )
        found = [r for r in refs if r["kind"] == "internet_3d_base"]
        missing = [r for r in refs if r["kind"].startswith("MISSING_")]
        if found and not missing:
            return Verification(
                status=STATUS_PASS,
                reason=f"internet-3d-base attached for {len(found)} char(s)",
            )
        if found and missing:
            return Verification(
                status=STATUS_PASS,
                reason=(
                    f"internet-3d-base attached for {len(found)} char(s); "
                    f"missing for {[m['character'] for m in missing]} "
                    "(soft warning — generate via reference-acquisition skill)"
                ),
            )
        return Verification(
            status=STATUS_PASS,  # soft: never blocks the run
            reason=(
                f"internet-3d-base missing for all {len(refs)} char(s). "
                "Generate via skills/reference-acquisition/SKILL.md to "
                "improve character consistency."
            ),
        )
