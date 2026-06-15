#!/usr/bin/env python3
"""ingest_script.py — normalize a TEXT comic script into a corpus record (B1 feedstock).

The user's own comic *story scripts* (premise, transformation arc, beats) — distinct
from ingest.py, which fetches rendered comic PAGE IMAGES. A script is text, so it
supports only the two TEXT-assessable rubric axes (growth density, story structure);
the two visual axes (camera dynamism, expression intensity) are deferred to
storyboard/render. The record reuses analysis-rubric.md vocabulary so scripts and
rendered comics pool into one corpus.

Creates:
    corpus/<slug>/
        source.txt           (gitignored — extracted raw script text)
        source.<ext>         (gitignored — original, for non-text formats, re-extraction)
        meta.json            (record_type: script; source: user-script)
        script-record.json   (skeleton; analysis_status: pending)

Then a FRESH subagent analyzes source.txt against analysis-rubric.md and fills
script-record.json (schema: schema/script-record.schema.json) + notes.md, and sets
analysis_status: done.

Usage:
    ingest_script.py --local scripts-raw/my-script.md --title "My Script"
    cat my.txt | ingest_script.py --stdin --slug my-script --title "My Script"
    ingest_script.py --list
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from shutil import which

CORPUS_ROOT = Path(__file__).resolve().parent.parent / "corpus"
RUBRIC_VERSION = "1.0"
TEXT_EXTS = {".txt", ".md", ".markdown"}


def slugify(text: str) -> str:
    s = text.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[-\s]+", "-", s)
    return s.strip("-")


def extract_text(src: Path, dst_txt: Path) -> tuple[bool, str]:
    """Extract script text into dst_txt. Returns (extracted, note).

    Dependency-light, mirroring ingest.py's PDF handling: text formats are read
    directly; PDFs try poppler's pdftotext if present, else are left for the `pdf`
    skill; DOCX is left for the `docx` skill. Either way the record is registered.
    """
    ext = src.suffix.lower()
    if ext in TEXT_EXTS:
        dst_txt.write_text(src.read_text(errors="replace"))
        return True, "text copied"
    if ext == ".pdf":
        if which("pdftotext"):
            subprocess.run(["pdftotext", "-layout", str(src), str(dst_txt)], check=False)
            if dst_txt.exists() and dst_txt.stat().st_size > 0:
                return True, "pdftotext"
        return False, "PDF registered; extract text into source.txt via the `pdf` skill"
    if ext == ".docx":
        return False, "DOCX registered; extract text into source.txt via the `docx` skill"
    return False, f"unsupported ext {ext}; place plain text into source.txt manually"


def meta_skeleton(slug: str, source_path: Path | None, title: str | None, delivered_as: str) -> dict:
    return {
        "comic_id": slug,
        "record_type": "script",
        "title": title or slug.replace("-", " ").title(),
        "source": {
            "kind": "user-script",
            "delivered_as": delivered_as,
            "path": str(source_path) if source_path else None,
        },
        "popularity": {"available": False},
        "ingested_at": datetime.now(timezone.utc).isoformat(),
        "analysis_status": "pending",
        "rubric_version": RUBRIC_VERSION,
    }


def record_skeleton(slug: str, title: str | None, source_path: Path | None, delivered_as: str) -> dict:
    return {
        "record_type": "script",
        "script_id": slug,
        "title": title or slug.replace("-", " ").title(),
        "source": {
            "kind": "user-script",
            "delivered_as": delivered_as,
            "path": str(source_path) if source_path else None,
            "delivered_at": datetime.now(timezone.utc).isoformat(),
        },
        "premise": "",
        "transformation": {"flavor": "", "trigger": "", "arc": "", "peak_state": ""},
        "cast": [],
        # cast_size is intentionally OMITTED from the skeleton: a pending record
        # doesn't yet know the cast, and the schema requires cast_size >= 1 when
        # present. The analyzer adds it. This keeps even pending skeletons valid.
        "structure": {"act_breakdown": "", "scene_count": 0, "est_page_count": 0, "narrative_arc": ""},
        "notable_beats": [],
        "chapter_type": "mixed",
        "growth_accounting": {"est_growth_scene_ratio": 0, "growth_scenes": [], "escalation_devices_planned": []},
        "assessable_scores": {"growth_density_score": 0, "story_structure_score": 0},
        "deferred_axes": ["camera_dynamism", "expression_intensity"],
        "strengths": [],
        "weaknesses": [],
        "rubric_version": RUBRIC_VERSION,
        "analyzed_at": None,
        "analysis_status": "pending",
    }


def cmd_list() -> int:
    if not CORPUS_ROOT.exists():
        print("corpus empty")
        return 0
    rows = 0
    for pack in sorted(CORPUS_ROOT.iterdir()):
        mp = pack / "meta.json"
        if not (pack.is_dir() and mp.exists()):
            continue
        try:
            meta = json.loads(mp.read_text())
        except json.JSONDecodeError:
            continue
        if meta.get("record_type") != "script":
            continue
        rows += 1
        status = meta.get("analysis_status", "?")
        rec = "✓record" if (pack / "script-record.json").exists() else "—"
        print(f"  {pack.name:46} script  status={status:9} {rec}")
    if rows == 0:
        print("  (no script records yet — drop scripts in scripts-raw/ and --local them)")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Normalize a comic SCRIPT into a corpus record (B1).")
    p.add_argument("--local", type=Path, help="A script file (.txt/.md/.pdf/.docx)")
    p.add_argument("--stdin", action="store_true", help="Read pasted script text from stdin")
    p.add_argument("--slug", help="Corpus slug (default: derived from filename/title)")
    p.add_argument("--title", help="Human title")
    p.add_argument("--list", action="store_true", help="List script records + status")
    args = p.parse_args(argv)

    if args.list:
        return cmd_list()
    if not (args.local or args.stdin):
        print("ERROR: pass --local FILE, --stdin, or --list", file=sys.stderr)
        return 2

    source_path: Path | None
    if args.stdin:
        slug = args.slug or (slugify(args.title) if args.title else "")
        if not slug:
            print("ERROR: --stdin needs --slug or --title", file=sys.stderr)
            return 2
        delivered_as = "paste"
        source_path = None
        text = sys.stdin.read()
    else:
        src = args.local
        if not src.exists():
            print(f"ERROR: no such file: {src}", file=sys.stderr)
            return 2
        slug = args.slug or slugify(src.stem)
        delivered_as = src.suffix.lower().lstrip(".") or "other"
        source_path = src

    pack = CORPUS_ROOT / slug
    pack.mkdir(parents=True, exist_ok=True)
    dst_txt = pack / "source.txt"

    if args.stdin:
        dst_txt.write_text(text)
        note = "stdin captured"
    else:
        extracted, note = extract_text(src, dst_txt)
        # Keep the raw original (gitignored) for non-text formats so text can be re-extracted.
        if src.suffix.lower() not in TEXT_EXTS:
            raw_copy = pack / f"source{src.suffix.lower()}"
            if src.resolve() != raw_copy.resolve():
                shutil.copy(src, raw_copy)

    (pack / "meta.json").write_text(json.dumps(meta_skeleton(slug, source_path, args.title, delivered_as), indent=2) + "\n")
    (pack / "script-record.json").write_text(json.dumps(record_skeleton(slug, args.title, source_path, delivered_as), indent=2) + "\n")

    print(f"Registered script → {pack}")
    print(f"  text: {note}")
    print("  meta.json + script-record.json (skeleton, analysis_status=pending) written")
    print("Next: a FRESH subagent analyzes source.txt against analysis-rubric.md")
    print("      (text axes only: growth density + story structure; visual axes deferred),")
    print("      fills script-record.json (schema/script-record.schema.json) + notes.md,")
    print("      and sets analysis_status='done'.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
