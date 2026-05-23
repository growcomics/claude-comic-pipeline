"""Attach the environment reference for the panel's location.

Pre-refactor, env attachment was inline in next_panel.build_plan(). This
module documents the contract.

The env ref carries the location's CANONICAL look — architecture,
lighting baseline, scale, depth. Per L10 the env ref is the source of
truth for location; the prompt's match directive (match/match_env.py)
points at it.

When the env ref must be dropped due to the 3-ref ceiling, the
verbal-anchor fallback in action/environment_directive.py (L23) fires.
"""

from __future__ import annotations

from pathlib import Path

from .._base import (
    Rule, Verification, STATUS_PASS, STATUS_SKIPPED, CATEGORY_ATTACH,
)


def _candidate_env_paths(project_root: Path, location_slug: str) -> list[Path]:
    """Possible env ref locations to try, in priority order."""
    base = project_root / "references" / "locations" / location_slug
    return [
        base / "_source.jpg",
        base / "_source.png",
        base / "env-ref.png",
        base / "env-ref.jpg",
    ]


class AttachEnvRef(Rule):
    id = "ATTACH_ENV_REF"
    title = "Attach the environment reference for the panel's location"
    slot = ""
    section_label = "ATTACH — env ref"
    severity = "soft"
    applicable_transformations = ("*",)
    category = CATEGORY_ATTACH

    def should_apply(self, panel: dict, ctx: dict) -> bool:
        return bool(panel.get("location"))

    def attached_refs(self, panel: dict, ctx: dict) -> list[dict]:
        location_slug = panel.get("location")
        if not location_slug:
            return []
        project_root = ctx.get("project_root")
        if not project_root:
            return [{
                "kind": "MISSING_env_ref",
                "path": None,
                "location": location_slug,
                "reason": "project_root not in ctx",
            }]
        for candidate in _candidate_env_paths(Path(project_root), location_slug):
            if candidate.exists():
                return [{
                    "kind": "env_ref",
                    "path": str(candidate.relative_to(project_root)),
                    "location": location_slug,
                    "reason": (f"env reference for {location_slug} "
                               "(L10 location-truth)"),
                }]
        return [{
            "kind": "MISSING_env_ref",
            "path": None,
            "location": location_slug,
            "reason": (f"no env ref found at references/locations/"
                       f"{location_slug}/ — L23 fallback will fire"),
        }]

    def verify_pre_render(self, panel: dict, ctx: dict) -> Verification:
        refs = self.attached_refs(panel, ctx)
        if not refs:
            return Verification(
                status=STATUS_SKIPPED,
                reason="panel has no location",
            )
        if refs[0]["kind"].startswith("MISSING_"):
            return Verification(
                status=STATUS_PASS,  # soft warning; L23 handles fallback
                reason=refs[0]["reason"],
            )
        return Verification(
            status=STATUS_PASS,
            reason=f"env ref attached: {refs[0]['path']}",
        )
