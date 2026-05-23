"""Attach panel N-1 (or the most recent accepted panel) as a state-continuity anchor.

NEW in the 2026-05-23 refs-are-truth refactor.

Pre-refactor, the prior-panel-as-state-anchor logic lived inline in
next_panel.py's build_plan. It was the most reliable continuity device
in the pipeline (transformations, costume tears, hair state all chained
through the attached prior panel) but it wasn't a first-class rule.

This module formalizes L1 ("continuity-chain through prior accepted
panel") as an explicit attach rule. The paired match rule is
match/match_prior_panel.py which emits the one-line "preserve state
from the attached prior panel" directive.

Selection logic (mirrors the inline view-aware chain pick from
build_plan):
  - skip if this is the first panel of the chapter
  - skip if camera is ecu-face (face-only beats don't carry costume state)
  - prefer the most recent accepted panel with a compatible camera
    (full-body / 3q-full / medium / mcu — anything that shows the
    costume + body)
  - fall back to the previous panel in shotlist order if no compatible
    earlier panel exists
"""

from __future__ import annotations

from pathlib import Path

from .._base import (
    Rule, Verification, STATUS_PASS, STATUS_SKIPPED, CATEGORY_ATTACH,
)


# Cameras that show enough of the costume/body to be useful as a state
# anchor. ECU-face panels typically can't anchor costume continuity.
_STATE_CARRYING_CAMERAS = {
    "front-full", "3q-full", "back-full", "side-full",
    "low-angle-front", "low-angle-back", "high-angle",
    "medium", "cowboy", "mcu", "ecu-region",
    "wide-establish", "splash",
}


def _accepted_panel_path(project_root: Path, panel_id: str) -> Path | None:
    """The canonical accepted PNG path used by next_panel.py."""
    p = project_root / "pages" / "panels" / f"{panel_id}.png"
    return p if p.exists() else None


def _pick_anchor(
    panel: dict,
    shotlist: dict,
    project_root: Path,
    camera: str,
) -> dict | None:
    """View-aware chain pick — prefer the most-recent accepted panel
    with a state-carrying camera, fall back to the immediately-previous
    panel if needed."""
    # Build flat ordered list of panels in shotlist order
    flat: list[dict] = []
    for page in shotlist.get("pages", []) or []:
        for p in page.get("panels", []) or []:
            flat.append(p)
    # Find this panel's position
    panel_id = panel.get("panel_id")
    try:
        idx = next(i for i, p in enumerate(flat) if p.get("panel_id") == panel_id)
    except StopIteration:
        return None
    if idx == 0:
        return None
    # Walk backwards looking for an accepted panel with a state-carrying camera
    for j in range(idx - 1, -1, -1):
        prev = flat[j]
        prev_id = prev.get("panel_id")
        prev_cam = (prev.get("camera") or "").split(",")[0].strip()
        accepted = _accepted_panel_path(project_root, prev_id)
        if not accepted:
            continue
        if prev_cam in _STATE_CARRYING_CAMERAS:
            return {
                "panel": prev,
                "accepted_path": str(accepted.relative_to(project_root)),
                "selection": "view-aware",
            }
    # Fallback — the immediately-previous accepted panel regardless of camera
    for j in range(idx - 1, -1, -1):
        prev = flat[j]
        prev_id = prev.get("panel_id")
        accepted = _accepted_panel_path(project_root, prev_id)
        if accepted:
            return {
                "panel": prev,
                "accepted_path": str(accepted.relative_to(project_root)),
                "selection": "immediately-previous",
            }
    return None


class AttachPriorPanel(Rule):
    id = "ATTACH_PRIOR_PANEL"
    title = "Attach prior accepted panel as state-continuity anchor"
    slot = ""
    section_label = "ATTACH — prior panel"
    severity = "soft"
    applicable_transformations = ("*",)
    category = CATEGORY_ATTACH

    def should_apply(self, panel: dict, ctx: dict) -> bool:
        camera = ctx.get("camera") or ""
        # ECU-face panels are pure portraiture; the face card carries
        # everything the model needs. Attaching a costume-state anchor
        # would just be noise.
        if camera == "ecu-face":
            return False
        return True

    def attached_refs(self, panel: dict, ctx: dict) -> list[dict]:
        if not self.should_apply(panel, ctx):
            return []
        project_root = ctx.get("project_root")
        shotlist = ctx.get("shotlist") or {}
        if not project_root:
            return []
        anchor = _pick_anchor(
            panel, shotlist, Path(project_root),
            ctx.get("camera") or "",
        )
        if not anchor:
            return []
        return [{
            "kind": "prior_panel_anchor",
            "path": anchor["accepted_path"],
            "anchor_panel_id": anchor["panel"].get("panel_id"),
            "anchor_camera": anchor["panel"].get("camera"),
            "selection_strategy": anchor["selection"],
            "reason": (
                f"prior panel `{anchor['panel'].get('panel_id')}` "
                "attached as state-continuity anchor (L1 chaining)"
            ),
        }]

    def verify_pre_render(self, panel: dict, ctx: dict) -> Verification:
        camera = ctx.get("camera") or ""
        if camera == "ecu-face":
            return Verification(
                status=STATUS_SKIPPED,
                reason="ecu-face panel — face card carries identity, no state anchor needed",
            )
        refs = self.attached_refs(panel, ctx)
        if not refs:
            return Verification(
                status=STATUS_SKIPPED,
                reason="no accepted prior panel available (first panel or all priors pending)",
            )
        return Verification(
            status=STATUS_PASS,
            reason=(f"prior panel `{refs[0]['anchor_panel_id']}` "
                    f"attached ({refs[0]['selection_strategy']})"),
        )
