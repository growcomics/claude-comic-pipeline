#!/usr/bin/env python3
"""Validate a shotlist.json against the contract the pipeline assumes.

Exit 0 = clean (warnings allowed), 1 = errors (shotlist rejected), 2 = usage.

Usage:
    python3 validate_shotlist.py <project_root>

Hooks: call from script-breakdown before a shotlist is accepted, and/or from
build_plan as a warn-only preflight so a known-bad shotlist surfaces before
generation credits are spent.
"""
import json
import sys
from pathlib import Path

# Canonical view tokens. The HEAD token of `camera` (first comma-clause, minus
# any parenthetical) must be one of these after lowercasing.
#
# Derived from skills/comic-production/data/view-vocabulary.json — the single
# source of truth shared with next_panel.py. KNOWN_VIEWS is the union of the
# runtime's VIEW_COMPATIBILITY keys, its _VIEW_ALIASES keys, and the extra
# normalized targets (mcu/medium/medium-wide). To add a new view token, edit
# the JSON file; this script and next_panel.py both pick it up at load time.
_VIEW_VOCAB_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "comic-production" / "data" / "view-vocabulary.json"
)
_VIEW_VOCAB = json.loads(_VIEW_VOCAB_PATH.read_text())
KNOWN_VIEWS = (
    set(_VIEW_VOCAB["compatibility"].keys())
    | set(_VIEW_VOCAB["aliases"].keys())
    | set(_VIEW_VOCAB["aliases"].values())
)

ON_SCREEN_DIALOGUE = {"balloon", "thought", "whisper", "shout"}


def _add(rows, pid, field, msg):
    rows.append(f"  panel {pid or '?'}: {field}: {msg}")


def validate(project_root: Path):
    """Returns (errors, warnings, panel_count)."""
    sl = project_root / "shotlist.json"
    if not sl.exists():
        return ([f"  {sl} not found"], [], 0)

    try:
        s = json.loads(sl.read_text())
    except json.JSONDecodeError as e:
        return ([f"  shotlist.json is not valid JSON: {e}"], [], 0)

    errors, warnings = [], []

    pages = s.get("pages") or []
    if not pages:
        errors.append("  top-level: no pages[] found")
    panels = [p for pg in pages for p in pg.get("panels", [])]
    if not panels:
        errors.append("  top-level: pages[] contain no panels")

    seen = set()
    for p in panels:
        pid = p.get("panel_id")
        if not pid:
            _add(errors, None, "panel_id", "missing")
            continue
        if pid in seen:
            _add(errors, pid, "panel_id", "duplicate")
        seen.add(pid)

        # camera: head token must be a known view, not prose.
        cam = (p.get("camera") or "").strip()
        if not cam:
            _add(errors, pid, "camera", "missing")
        else:
            head = cam.split(",")[0].split("(")[0].strip().lower()
            if head not in KNOWN_VIEWS:
                if len(head.split()) > 4:
                    _add(errors, pid, "camera",
                         f"prose, not a view tag (move to `action`): {head!r}")
                else:
                    _add(errors, pid, "camera",
                         f"unknown view token (add alias or fix): {head!r}")

        # tier: int when present.
        tier = p.get("tier", p.get("muscle_size_tier"))
        if tier is not None and not isinstance(tier, int):
            _add(errors, pid, "tier", f"not an int: {tier!r}")

        # dialogue: on-screen lines need a speaker or L4 attribution blanks.
        for d in p.get("dialogue", []) or []:
            if isinstance(d, dict) and d.get("type", "balloon") in ON_SCREEN_DIALOGUE \
                    and not (d.get("speaker") or d.get("character")):
                _add(warnings, pid, "dialogue",
                     "on-screen line missing `speaker` (L4 tail will be blank)")

        if not p.get("characters"):
            _add(warnings, pid, "characters", "empty — panel has no cast")
        if not p.get("location"):
            _add(warnings, pid, "location", "missing")

    return (errors, warnings, len(panels))


def main():
    if len(sys.argv) < 2:
        print("usage: validate_shotlist.py <project_root>")
        return 2
    errors, warnings, n = validate(Path(sys.argv[1]))
    if warnings:
        print(f"WARNINGS ({len(warnings)}):")
        print("\n".join(warnings))
    if errors:
        print(f"\nERRORS ({len(errors)}) — shotlist rejected:")
        print("\n".join(errors))
        return 1
    tail = f", {len(warnings)} warnings" if warnings else ""
    print(f"OK — {n} panels valid{tail}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
