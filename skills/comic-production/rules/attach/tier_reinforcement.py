"""Attach the tier-N reinforcement PNGs (consolidates L29/L30/L31/L32 attachment).

Pre-refactor, four sibling rules (L29 tier-6, L30 tier-7, L31 tier-8,
L32 tier-9) each carried their own attach + directive logic. The attach
part was data-driven on tier; the directive part was ~800 chars of
prose describing what the PNGs depict.

Post-refactor, the directive part is gone (covered by the one-line
match in match/match_body.py). The attach part is consolidated here —
one module that picks the right tier folder based on
panel.muscle_size_tier and attaches both PNGs from that folder.

Expected on disk:
  skills/comic-production/references/peak-body-scale/tier-{N}/
    tier-{N}-full-body.png
    tier-{N}-anatomical-detail.png
"""

from __future__ import annotations

from pathlib import Path

from .._base import (
    Rule, Verification, STATUS_PASS, STATUS_SKIPPED, STATUS_FAIL,
    CATEGORY_ATTACH,
)


# Tier-aware filename pairs. Same files L29/L30/L31/L32 each used to
# enumerate individually. Tier 9 intentionally uses the same composite
# for both files per user-directed Grok edit.
TIER_REINFORCEMENT_FILES = {
    6: ("tier-6-full-body.png", "tier-6-anatomical-detail.png"),
    7: ("tier-7-full-body.png", "tier-7-anatomical-detail.png"),
    8: ("tier-8-full-body.png", "tier-8-anatomical-detail.png"),
    9: ("tier-9-full-body.png", "tier-9-anatomical-detail.png"),
}

# Tiers that get reinforcement (and the ctx_flag_key the match rules check).
REINFORCEMENT_TIERS = (6, 7, 8, 9)
CTX_FLAG_KEYS = {
    6: "tier6_refs_attached",
    7: "tier7_refs_attached",
    8: "tier8_refs_attached",
    9: "tier9_refs_attached",
}


def _skill_refs_root() -> Path:
    return (
        Path.home() / ".claude" / "skills" / "comic-production"
        / "references" / "peak-body-scale"
    )


def _find_tier_refs(tier: int) -> list[Path]:
    """Return existing tier-N reinforcement PNGs (both, if present)."""
    files = TIER_REINFORCEMENT_FILES.get(tier)
    if not files:
        return []
    base = _skill_refs_root() / f"tier-{tier}"
    found: list[Path] = []
    for fname in files:
        p = base / fname
        if p.exists():
            found.append(p)
    return found


class AttachTierReinforcement(Rule):
    id = "ATTACH_TIER_REINFORCEMENT"
    title = "Attach tier-N reinforcement PNGs (consolidates L29-L32 attachment)"
    slot = ""
    section_label = "ATTACH — tier reinforcement"
    severity = "hard"
    applicable_transformations = ("fmg",)
    category = CATEGORY_ATTACH

    def should_apply(self, panel: dict, ctx: dict) -> bool:
        try:
            tier = int(panel.get("muscle_size_tier"))
        except (TypeError, ValueError):
            return False
        return tier in REINFORCEMENT_TIERS

    def attached_refs(self, panel: dict, ctx: dict) -> list[dict]:
        try:
            tier = int(panel.get("muscle_size_tier"))
        except (TypeError, ValueError):
            return []
        if tier not in REINFORCEMENT_TIERS:
            return []
        found = _find_tier_refs(tier)
        expected_count = len(TIER_REINFORCEMENT_FILES[tier])
        if not found:
            return [{
                "kind": f"MISSING_tier{tier}_reinforcement",
                "path": None,
                "tier": tier,
                "reason": (f"tier-{tier} reinforcement PNGs not found on disk "
                           "— pipeline will fall back to lineup-only "
                           "(per L29-L32 verify_pre_render: HARD fail at "
                           "this tier)"),
            }]
        refs = [{
            "kind": f"tier{tier}_reinforcement",
            "path": str(p),
            "tier": tier,
            "reason": (f"tier-{tier} dedicated reinforcement ref "
                       f"({i+1}/{expected_count})"),
        } for i, p in enumerate(found)]
        if len(found) < expected_count:
            refs.append({
                "kind": f"MISSING_tier{tier}_reinforcement_partial",
                "path": None,
                "tier": tier,
                "reason": (f"only {len(found)}/{expected_count} "
                           f"tier-{tier} PNGs found"),
            })
        return refs

    def verify_pre_render(self, panel: dict, ctx: dict) -> Verification:
        try:
            tier = int(panel.get("muscle_size_tier"))
        except (TypeError, ValueError):
            return Verification(
                status=STATUS_SKIPPED,
                reason="no muscle_size_tier",
            )
        if tier not in REINFORCEMENT_TIERS:
            return Verification(
                status=STATUS_SKIPPED,
                reason=f"tier {tier} not in {REINFORCEMENT_TIERS}",
            )
        found = _find_tier_refs(tier)
        if not found:
            return Verification(
                status=STATUS_FAIL,
                reason=(f"tier-{tier} reinforcement PNGs missing on disk "
                        "— at this tier the lineup-only fallback is "
                        "significantly less reliable (per L29-L32)"),
            )
        return Verification(
            status=STATUS_PASS,
            reason=f"{len(found)} tier-{tier} reinforcement PNG(s) found",
        )
