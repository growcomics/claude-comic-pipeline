"""Attach the appropriate body-tier lineup based on the panel's tier.

Pre-refactor, lineup attachment was inline in next_panel.build_plan().
This module documents the contract.

The lineup is the 3D body chart with multiple figures at different
tiers. Two lineup files exist:
  - muscle-size-lineup.png       — tiers 1-6
  - muscle-size-lineup-4-9.png   — tiers 4-9 (peak range)

The appropriate lineup is attached based on the panel's
muscle_size_tier; per L10 the lineup PNG IS the truth for proportion
and the prompt's match directive (in match/match_body.py) points at it.
"""

from __future__ import annotations

from pathlib import Path

from .._base import (
    Rule, Verification, STATUS_PASS, STATUS_SKIPPED, CATEGORY_ATTACH,
)


def _resolve_lineup(project_root: Path, tier: int, config: dict) -> Path | None:
    """Resolve the lineup PNG path based on tier + production config.

    Reads project-level config first (config["lineup_files"]); falls back
    to skill-level defaults.
    """
    lineup_files = (config or {}).get("lineup_files") or {}
    tier_low = lineup_files.get("tier_low") or "muscle-size-lineup.png"
    tier_high = lineup_files.get("tier_high") or "muscle-size-lineup-4-9.png"
    active_range = lineup_files.get("active_range", "auto")
    if active_range == "low":
        fname = tier_low
    elif active_range == "high":
        fname = tier_high
    else:  # "auto" or unknown
        fname = tier_high if tier >= 4 else tier_low
    candidate = project_root / "references" / "body-tiers" / fname
    if candidate.exists():
        return candidate
    # Fallback to the skill's bundled refs
    skill_candidate = (
        Path.home() / ".claude" / "skills" / "comic-production"
        / "references" / "peak-body-scale" / fname
    )
    if skill_candidate.exists():
        return skill_candidate
    return None


class AttachBodyTier(Rule):
    id = "ATTACH_BODY_TIER"
    title = "Attach body-tier lineup based on panel.muscle_size_tier"
    slot = ""
    section_label = "ATTACH — body-tier lineup"
    severity = "hard"
    applicable_transformations = ("fmg",)
    category = CATEGORY_ATTACH

    def should_apply(self, panel: dict, ctx: dict) -> bool:
        t = panel.get("muscle_size_tier")
        try:
            return int(t) is not None
        except (TypeError, ValueError):
            return False

    def attached_refs(self, panel: dict, ctx: dict) -> list[dict]:
        try:
            tier = int(panel.get("muscle_size_tier"))
        except (TypeError, ValueError):
            return []
        project_root = ctx.get("project_root")
        if not project_root:
            return [{
                "kind": "MISSING_lineup",
                "path": None,
                "tier": tier,
                "reason": "project_root not in ctx",
            }]
        config = ctx.get("production_config") or {}
        lineup_path = _resolve_lineup(Path(project_root), tier, config)
        if lineup_path is None:
            return [{
                "kind": "MISSING_lineup",
                "path": None,
                "tier": tier,
                "reason": f"lineup PNG not found for tier {tier}",
            }]
        try:
            rel = str(lineup_path.relative_to(project_root))
        except ValueError:
            rel = str(lineup_path)
        return [{
            "kind": "lineup",
            "path": rel,
            "tier": tier,
            "reason": f"tier-{tier} body proportions ref (L10 body-truth)",
        }]

    def verify_pre_render(self, panel: dict, ctx: dict) -> Verification:
        refs = self.attached_refs(panel, ctx)
        if not refs:
            return Verification(
                status=STATUS_SKIPPED,
                reason="panel has no muscle_size_tier",
            )
        missing = [r for r in refs if r["kind"].startswith("MISSING_")]
        if missing:
            return Verification(
                status=STATUS_PASS,  # soft warning
                reason=f"lineup PNG missing: {missing[0]['reason']}",
            )
        return Verification(
            status=STATUS_PASS,
            reason=f"lineup attached: {refs[0]['path']}",
        )
