#!/usr/bin/env python3
"""Generate STATUS.md at the project root by reading the on-disk project state.

Reads `shotlist.json` (if present), walks `references/<bucket>/<slug>/` and
`pages/panels/<panel-folder>/`, and writes `STATUS.md` at the project root.
Idempotent: safe to re-run after every change.

Usage:
    python generate_status.py <project_root>

See `references/folder-convention.md` for the layout this script reads.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# Project state readers


def read_shotlist(root: Path) -> dict | None:
    path = root / "shotlist.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return None


def enumerate_refs(root: Path) -> dict[str, list[dict]]:
    """Walk references/<bucket>/<slug>/ and return refs grouped by bucket."""
    refs_root = root / "references"
    if not refs_root.exists():
        return {}

    out: dict[str, list[dict]] = {}
    for bucket_dir in sorted(refs_root.iterdir()):
        if not bucket_dir.is_dir():
            continue
        bucket = bucket_dir.name
        out[bucket] = []
        for slug_dir in sorted(bucket_dir.iterdir()):
            if not slug_dir.is_dir():
                continue
            images = sorted(
                p for p in slug_dir.iterdir()
                if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
                and not p.name.startswith("_")
            )
            # Special-case _source.jpg (env-reference convention)
            source_jpg = slug_dir / "_source.jpg"
            if source_jpg.exists():
                images = [source_jpg, *images]
            out[bucket].append({
                "slug": slug_dir.name,
                "images": [img.relative_to(root) for img in images],
                "has_provenance": (slug_dir / "_provenance.md").exists(),
            })
    return out


def enumerate_panels(root: Path) -> list[dict]:
    """Walk pages/panels/<panel-folder>/ and return per-panel revision data."""
    panels_root = root / "pages" / "panels"
    if not panels_root.exists():
        return []

    panels = []
    for panel_dir in sorted(panels_root.iterdir()):
        if not panel_dir.is_dir():
            # Flat file? Treat as single-revision panel.
            if panel_dir.suffix.lower() in {".png", ".jpg"}:
                panels.append({
                    "name": panel_dir.stem,
                    "folder_path": None,
                    "versions": [panel_dir.relative_to(root)],
                    "accepted": panel_dir.relative_to(root),
                    "accepted_label": "v1 (flat layout)",
                    "notes": {},
                })
            continue

        versions = sorted(
            p for p in panel_dir.iterdir()
            if p.suffix.lower() in {".png", ".jpg"}
            and p.stem.startswith("v") and p.stem[1:].isdigit()
        )
        if not versions:
            continue

        accepted_marker = panel_dir / "_accepted.txt"
        accepted_label = None
        accepted_path = None
        if accepted_marker.exists():
            accepted_label = accepted_marker.read_text().strip()
            candidates = [v for v in versions if v.stem == accepted_label]
            if candidates:
                accepted_path = candidates[0].relative_to(root)

        notes = {}
        for v in versions:
            notes_file = panel_dir / f"{v.stem}.notes.md"
            if notes_file.exists():
                notes[v.stem] = notes_file.read_text().strip()

        panels.append({
            "name": panel_dir.name,
            "folder_path": panel_dir.relative_to(root),
            "versions": [v.relative_to(root) for v in versions],
            "accepted": accepted_path,
            "accepted_label": accepted_label,
            "notes": notes,
        })

    return panels


def detect_stages(root: Path, shotlist: dict | None,
                  refs: dict, panels: list[dict]) -> list[dict]:
    """Detect status of each pipeline stage."""
    stages = []

    # 1. Script breakdown
    if shotlist:
        page_count = shotlist.get("page_count", "?")
        cast_count = len(shotlist.get("cast", []))
        loc_count = len(shotlist.get("locations", []))
        stages.append({
            "name": "Script breakdown",
            "status": "done",
            "notes": f"shotlist.json — {page_count} pages, {cast_count} cast, {loc_count} locations",
        })
    else:
        stages.append({"name": "Script breakdown", "status": "pending", "notes": "no shotlist.json yet"})
        # No further detection meaningful without shotlist
        for label in ("References", "Generation", "Continuity", "Composition", "Posting"):
            stages.append({"name": label, "status": "pending", "notes": "-"})
        return stages

    # 2. References — count hero subjects with ref_folder set in shotlist vs found on disk
    def count_with_ref_folder(items):
        return sum(1 for it in items if it.get("ref_folder"))

    cast = shotlist.get("cast", [])
    locs = shotlist.get("locations", [])
    props = shotlist.get("props", [])
    expected_chars = len(cast)  # cast always has ref_folder per script-breakdown rules
    expected_locs = count_with_ref_folder(locs)
    expected_props = count_with_ref_folder(props)
    found_chars = len(refs.get("characters", []))
    found_locs = len(refs.get("locations", []))
    found_props = len(refs.get("props", []))
    total_expected = expected_chars + expected_locs + expected_props
    total_found = found_chars + found_locs + found_props
    if total_expected == 0:
        refs_status = "done"
    elif total_found >= total_expected:
        refs_status = "done"
    elif total_found > 0:
        refs_status = "partial"
    else:
        refs_status = "pending"
    stages.append({
        "name": "References",
        "status": refs_status,
        "notes": f"{found_chars}/{expected_chars} characters, {found_locs}/{expected_locs} locations, {found_props}/{expected_props} props",
    })

    # 3. Generation — count panels with _accepted vs total in shotlist
    expected_panels = sum(len(p.get("panels", [])) for p in shotlist.get("pages", []))
    accepted = sum(1 for p in panels if p["accepted"] is not None)
    if expected_panels == 0:
        gen_status = "pending"
    elif accepted >= expected_panels:
        gen_status = "done"
    elif accepted > 0:
        gen_status = "in_progress"
    else:
        gen_status = "pending"
    stages.append({
        "name": "Generation",
        "status": gen_status,
        "notes": f"{accepted}/{expected_panels} panels accepted",
    })

    # 4. Continuity
    cr = root / "continuity-report.md"
    stages.append({
        "name": "Continuity",
        "status": "done" if cr.exists() else "pending",
        "notes": "continuity-report.md present" if cr.exists() else "-",
    })

    # 5. Composition
    pages_dir = root / "pages"
    composed = []
    if pages_dir.exists():
        composed = sorted(p for p in pages_dir.iterdir() if p.is_file()
                          and p.stem.startswith("page-") and p.suffix.lower() == ".png")
    expected_pages = shotlist.get("page_count", 0) or 0
    if expected_pages == 0:
        comp_status = "pending"
    elif len(composed) >= expected_pages:
        comp_status = "done"
    elif len(composed) > 0:
        comp_status = "partial"
    else:
        comp_status = "pending"
    stages.append({
        "name": "Composition",
        "status": comp_status,
        "notes": f"{len(composed)}/{expected_pages} pages composed",
    })

    # 6. Posting
    posted = root / "posting" / "posted.json"
    stages.append({
        "name": "Posting",
        "status": "done" if posted.exists() else "pending",
        "notes": "posted.json present" if posted.exists() else "-",
    })

    return stages


# ---------------------------------------------------------------------------
# Renderer


STATUS_ICON = {"done": "✅", "partial": "🟡", "in_progress": "🔄",
               "pending": "⏳", "blocked": "🛑"}


def render(root: Path, shotlist: dict | None, stages: list[dict],
           refs: dict, panels: list[dict]) -> str:
    project_name = shotlist.get("project") if shotlist else root.name
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        f"# {project_name}",
        f"_Last updated: {timestamp}_",
        "",
        "## Stages",
    ]
    for s in stages:
        icon = STATUS_ICON.get(s["status"], "·")
        lines.append(f"- {icon} **{s['name']}** — {s['notes']}")
    lines.append("")

    # Composites links
    composites = []
    for mode in ("references", "generation", "composition"):
        p = root / f"STATUS-{mode}-board.png"
        if p.exists():
            composites.append(f"[{mode}-board](STATUS-{mode}-board.png)")
    if composites:
        lines.append("**Composite boards:** " + " · ".join(composites))
        lines.append("")

    # References section
    lines.append("## References")
    if not refs:
        lines.append("_No references gathered yet._")
    else:
        for bucket in ("characters", "locations", "props", "style"):
            if bucket not in refs or not refs[bucket]:
                continue
            lines.append(f"\n### {bucket.capitalize()}")
            for entry in refs[bucket]:
                imgs = " ".join(f"![{img.stem}]({img})" for img in entry["images"][:4])
                lines.append(f"- **{entry['slug']}**")
                if imgs:
                    lines.append(f"  {imgs}")
    lines.append("")

    # Generation section
    lines.append("## Generation Progress")
    if not panels:
        lines.append("_No panels generated yet._")
    else:
        for panel in panels:
            attempts = len(panel["versions"])
            if panel["accepted"]:
                icon = "✅"
                status_text = f"accepted **{panel['accepted_label']}** ({attempts} attempt{'s' if attempts != 1 else ''})"
            else:
                icon = "🔄"
                status_text = f"in progress ({attempts} variant{'s' if attempts != 1 else ''} pending review)"
            lines.append(f"\n### {icon} {panel['name']} — {status_text}")
            for v in panel["versions"]:
                stem = v.stem
                marker = " — **accepted**" if panel["accepted_label"] == stem else ""
                note = panel["notes"].get(stem, "")
                if note:
                    lines.append(f"- `{stem}`: {note}{marker}")
                else:
                    lines.append(f"- `{stem}`{marker}")
            if panel["accepted"]:
                lines.append(f"  ![{panel['accepted_label']}]({panel['accepted']})")
    lines.append("")

    # Composition section
    lines.append("## Composition")
    composed_pages = []
    pages_dir = root / "pages"
    if pages_dir.exists():
        composed_pages = sorted(
            p.relative_to(root) for p in pages_dir.iterdir()
            if p.is_file() and p.stem.startswith("page-") and p.suffix.lower() == ".png"
        )
    if composed_pages:
        for p in composed_pages:
            lines.append(f"- ![{p.stem}]({p})")
    else:
        lines.append("_No pages composed yet._")
    lines.append("")

    # Posting section
    lines.append("## Posting")
    posted = root / "posting" / "posted.json"
    if posted.exists():
        lines.append(f"See [posted.json](posting/posted.json).")
    else:
        lines.append("_Not started._")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("project_root", type=Path)
    args = parser.parse_args()

    root = args.project_root.expanduser().resolve()
    if not root.exists():
        print(f"error: project root does not exist: {root}", file=sys.stderr)
        sys.exit(1)

    shotlist = read_shotlist(root)
    refs = enumerate_refs(root)
    panels = enumerate_panels(root)
    stages = detect_stages(root, shotlist, refs, panels)

    out = root / "STATUS.md"
    out.write_text(render(root, shotlist, stages, refs, panels))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
