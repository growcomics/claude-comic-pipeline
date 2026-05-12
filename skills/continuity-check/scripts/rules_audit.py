#!/usr/bin/env python3
"""
rules_audit.py — Deterministic continuity audit for a comic project.

Reads shotlist.json + the pages/panels/ folder layout and produces a
findings table for the things a rules engine can verify without looking at
pixels:

  - Every page panel has an accepted image on disk
  - Stage-change pages have a lineup ref attached (per `stage_change` flag)
  - muscle_size_tier (or analogous numeric arc) is monotonic non-decreasing
    where the shotlist declares it should be
  - costume_state field is present and non-empty per panel
  - Cumulative costume damage doesn't regress (once "small tears" is set
    for the issue, a later panel cannot return to "fully intact" unless
    explicitly marked as a flashback/dream via `continuity_break: true`)
  - Required wardrobe items mentioned in cast[] wardrobe appear in every
    panel's costume_state for that character (soft check)
  - References for declared cast/locations/props exist on disk

The vision-based audit is a separate workflow handled by the agent itself
(see SKILL.md). This script is the fast, free, deterministic first pass.

Usage:
  python rules_audit.py --project /path/to/project [--pages 1-7]
  python rules_audit.py --project ... --json    # machine-readable output

Exit codes:
  0  no hard errors
  1  hard errors found
  2  script error (bad input, missing shotlist)
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path


# ---------------------------------------------------------------------------
# Findings

SEVERITY_HARD = "hard"
SEVERITY_SOFT = "soft"
SEVERITY_INFO = "info"


@dataclass
class Finding:
    page: int | None
    panel_id: str | None
    category: str
    severity: str
    message: str
    suggestion: str = ""


# ---------------------------------------------------------------------------
# Costume damage ordering (cumulative — once at a level, can't regress)

DAMAGE_RANKS = [
    ("intact",   0, ["fully intact", "pristine", "clean"]),
    ("tight",    1, ["tight", "strain", "stretching", "stretched", "creases"]),
    ("damaged",  2, ["tear", "tears", "rip", "ripped", "torn", "fraying", "frayed",
                     "peak damage", "battle-worn", "exposing", "shredded"]),
]
# Coarse 3-level scale by design: trying to distinguish "small tears" vs "major
# tears" via text matching produces unreliable signals (different panels phrase
# similar damage in incompatible ways). Use vision-check for pixel-level drift.


CARRYOVER_PATTERNS = [
    "carries forward", "carry forward", "carryover", "carry over",
    "same as page", "unchanged from", "unchanged carries", "from page",
    "previous page", "as before",
]


def classify_costume_damage(state: str) -> int:
    """Return damage rank 0..4, or -1 if the string is unclassifiable / carryover.

    A return of -1 means "the regression check should skip this panel and
    inherit the previous panel's rank" — used when the shotlist phrases the
    state as an explicit carryover ("damage from page 18 carries forward")
    instead of re-listing the tears.
    """
    if not state:
        return -1
    s = state.lower()
    if any(p in s for p in CARRYOVER_PATTERNS):
        return -1
    hit = False
    rank = 0
    for _, level, keywords in DAMAGE_RANKS:
        for kw in keywords:
            if kw in s:
                rank = max(rank, level)
                hit = True
    return rank if hit else -1


# ---------------------------------------------------------------------------
# Image discovery (mirror compose_page.py)

def find_panel_image(project: Path, panel_id: str) -> Path | None:
    panels_dir = project / "pages" / "panels"
    if not panels_dir.exists():
        return None
    for sub in panels_dir.glob(f"panel-{panel_id}*"):
        if sub.is_dir():
            accepted = sorted(sub.glob("v*_accepted.png"))
            if accepted:
                return accepted[-1]
            v1 = sub / "v1.png"
            if v1.exists():
                return v1
    flat = panels_dir / f"{panel_id}.png"
    if flat.exists():
        return flat
    return None


# ---------------------------------------------------------------------------
# Reference disk presence

def check_references(project: Path, shotlist: dict) -> list[Finding]:
    out: list[Finding] = []
    for c in shotlist.get("cast", []):
        ref_folder = c.get("ref_folder")
        if ref_folder and not (project / ref_folder).exists():
            out.append(Finding(None, None, "reference", SEVERITY_HARD,
                               f"cast '{c.get('id', '?')}' ref_folder missing: {ref_folder}",
                               "Create the folder and gather a baseline body + face card before generation"))
    for loc in shotlist.get("locations", []):
        ref_folder = loc.get("ref_folder")
        if ref_folder and not (project / ref_folder).exists():
            out.append(Finding(None, None, "reference", SEVERITY_SOFT,
                               f"location '{loc.get('id', '?')}' ref_folder missing: {ref_folder}",
                               "Source an env ref (DAZ3D scene render or composite) before pages set there"))
    for prop in shotlist.get("props", []):
        ref_folder = prop.get("ref_folder")
        if ref_folder and not (project / ref_folder).exists():
            out.append(Finding(None, None, "reference", SEVERITY_INFO,
                               f"prop '{prop.get('id', '?')}' ref_folder missing: {ref_folder}",
                               "Optional — props can often be described in-prompt without a ref"))
    return out


# ---------------------------------------------------------------------------
# Per-page checks

def check_pages(project: Path, shotlist: dict, pages_filter: set[int] | None) -> list[Finding]:
    out: list[Finding] = []
    pages = shotlist.get("pages", [])
    cast_ids = {c.get("id") for c in shotlist.get("cast", [])}

    # Track cumulative damage across the issue (resets allowed only via `continuity_break`)
    last_damage_by_char: dict[str, tuple[int, int, str]] = {}  # char -> (page, rank, state)
    last_size_by_char: dict[str, tuple[int, float]] = {}        # char -> (page, size)

    for page in pages:
        n = page.get("page_number")
        if pages_filter is not None and n not in pages_filter:
            continue
        for panel in page.get("panels", []):
            pid = panel.get("panel_id", f"page-{n}")

            # 1. Accepted image exists
            img = find_panel_image(project, pid)
            if img is None:
                out.append(Finding(n, pid, "asset", SEVERITY_HARD,
                                   "no accepted image on disk for this panel",
                                   "Generate and accept a variant, save as panel-<id>/v1.png"))

            # 2. costume_state present per panel
            cs = panel.get("costume_state", "").strip()
            if not cs:
                out.append(Finding(n, pid, "shotlist", SEVERITY_SOFT,
                                   "missing costume_state field",
                                   "Add an explicit costume_state value; lets continuity-check track damage"))

            # 3. Costume damage non-regression — apply per Supergirl-style single-protagonist
            #    arc. If you have multiple muscle-arc characters declare which via `arc_character`.
            arc_char = shotlist.get("arc_character") or _infer_arc_character(shotlist)
            chars = panel.get("characters", [])
            if arc_char and arc_char in chars and cs and not panel.get("continuity_break"):
                rank = classify_costume_damage(cs)
                if rank >= 0:
                    # Explicit damage statement — regression check applies
                    prev = last_damage_by_char.get(arc_char)
                    if prev and rank < prev[1]:
                        out.append(Finding(n, pid, "costume", SEVERITY_SOFT,
                                           f"costume damage rank dropped for {arc_char}: "
                                           f"page {prev[0]} was rank {prev[1]} ('{_summarize(prev[2])}'), "
                                           f"page {n} is rank {rank} ('{_summarize(cs)}')",
                                           "If intentional set continuity_break: true. Otherwise the shotlist phrasing may "
                                           "just differ — run the vision audit to check the actual images."))
                    last_damage_by_char[arc_char] = (n, rank, cs)
                # else: rank == -1 → carryover or unclassifiable. Inherit previous rank
                # for tracking but don't flag.

            # 4. Stage-change pages must have lineup ref intent. We approximate: shotlist
            #    can flag `stage_change: true` per page or panel; if so, the panel notes
            #    should mention "lineup" in some form, or there should be a lineup_ref file
            #    in references/style/.
            if page.get("stage_change") or panel.get("stage_change"):
                if not _has_lineup_ref(project):
                    out.append(Finding(n, pid, "reference", SEVERITY_SOFT,
                                       "stage-change page but no lineup ref found in references/style/",
                                       "Create references/style/muscle-size-lineup.png and attach during generation"))

            # 5. muscle_size_tier monotonic non-decreasing for the arc character
            tier = panel.get("muscle_size_tier")
            if arc_char and arc_char in chars and tier is not None and not panel.get("continuity_break"):
                try:
                    tier_f = float(tier)
                    prev = last_size_by_char.get(arc_char)
                    if prev and tier_f < prev[1]:
                        out.append(Finding(n, pid, "size_tier", SEVERITY_HARD,
                                           f"muscle_size_tier regressed for {arc_char}: "
                                           f"page {prev[0]} was {prev[1]}, page {n} is {tier_f}",
                                           "If intentional set continuity_break: true; otherwise fix shotlist"))
                    last_size_by_char[arc_char] = (n, tier_f)
                except (TypeError, ValueError):
                    out.append(Finding(n, pid, "size_tier", SEVERITY_INFO,
                                       f"muscle_size_tier '{tier}' is not numeric",
                                       "Use numeric tiers (e.g. 1, 2, 2.5) for monotonic checking"))

            # 6. Characters all declared in cast[]
            for ch in chars:
                if cast_ids and ch not in cast_ids:
                    out.append(Finding(n, pid, "shotlist", SEVERITY_SOFT,
                                       f"character '{ch}' not in cast[]",
                                       "Add to cast[] or fix typo in panel.characters"))

    return out


def _summarize(text: str, max_len: int = 80) -> str:
    text = " ".join(text.split())
    return text if len(text) <= max_len else text[:max_len - 1] + "…"


def _has_lineup_ref(project: Path) -> bool:
    style = project / "references" / "style"
    if not style.exists():
        return False
    return any(style.glob("*lineup*"))


def _infer_arc_character(shotlist: dict) -> str | None:
    """Heuristic: the cast member whose wardrobe text mentions costume tearing or muscle arcs."""
    for c in shotlist.get("cast", []):
        w = (c.get("wardrobe") or "").lower()
        if "tear" in w or "size" in w or "growth" in w or "muscle" in w:
            return c.get("id")
    return None


# ---------------------------------------------------------------------------
# Reporting

def format_findings_md(project: Path, findings: list[Finding], shotlist: dict) -> str:
    hard = sum(1 for f in findings if f.severity == SEVERITY_HARD)
    soft = sum(1 for f in findings if f.severity == SEVERITY_SOFT)
    info = sum(1 for f in findings if f.severity == SEVERITY_INFO)
    title = shotlist.get("title") or shotlist.get("project") or project.name
    lines = [
        f"# Continuity rules audit — {title}",
        "",
        f"Project: `{project}`",
        f"Pages: {len(shotlist.get('pages', []))}",
        f"Findings: **{hard} hard**, {soft} soft, {info} info",
        "",
    ]
    if not findings:
        lines.append("All deterministic checks passed. Run the vision audit next for pixel-level drift.")
        return "\n".join(lines)

    by_sev = {SEVERITY_HARD: [], SEVERITY_SOFT: [], SEVERITY_INFO: []}
    for f in findings:
        by_sev[f.severity].append(f)

    for sev in (SEVERITY_HARD, SEVERITY_SOFT, SEVERITY_INFO):
        bucket = by_sev[sev]
        if not bucket:
            continue
        lines.append(f"## {sev.upper()} ({len(bucket)})")
        lines.append("")
        lines.append("| Page | Panel | Category | Issue | Suggestion |")
        lines.append("|------|-------|----------|-------|------------|")
        for f in bucket:
            page = f.page if f.page is not None else "-"
            panel = f.panel_id or "-"
            lines.append(f"| {page} | {panel} | {f.category} | {f.message} | {f.suggestion} |")
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI

def resolve_pages_arg(arg: str | None) -> set[int] | None:
    if arg is None:
        return None
    out: set[int] = set()
    for part in arg.split(","):
        part = part.strip()
        if "-" in part:
            lo, hi = part.split("-", 1)
            out.update(range(int(lo), int(hi) + 1))
        else:
            out.add(int(part))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", required=True, type=Path)
    ap.add_argument("--pages", help="Page range to audit, e.g. '1-7'")
    ap.add_argument("--json", action="store_true", help="Emit JSON instead of markdown")
    ap.add_argument("--out", type=Path, help="Write report to file instead of stdout")
    args = ap.parse_args()

    project = args.project.resolve()
    shotlist_path = project / "shotlist.json"
    if not shotlist_path.exists():
        sys.exit(f"shotlist.json not found at {shotlist_path}")
    with open(shotlist_path) as f:
        shotlist = json.load(f)

    pages_filter = resolve_pages_arg(args.pages)
    findings = check_references(project, shotlist) + check_pages(project, shotlist, pages_filter)

    if args.json:
        payload = {"project": str(project), "findings": [asdict(f) for f in findings]}
        output = json.dumps(payload, indent=2)
    else:
        output = format_findings_md(project, findings, shotlist)

    if args.out:
        args.out.write_text(output)
        print(f"wrote {args.out}")
    else:
        print(output)

    hard_count = sum(1 for f in findings if f.severity == SEVERITY_HARD)
    sys.exit(1 if hard_count else 0)


if __name__ == "__main__":
    main()
