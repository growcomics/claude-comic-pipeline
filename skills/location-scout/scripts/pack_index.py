#!/usr/bin/env python3
"""pack_index.py — unified index + integrity check for references/locations/.

Two pack conventions coexist in this repo and BOTH are first-class:

  1. "scout" packs (built by this skill's scout_city/maps_capture/cgi_convert):
         <pack>/_targets.json            planning + provenance
         <pack>/meta/locations.json     canonical consumer manifest
         <pack>/source/*.jpg            captures
         <pack>/cgi/*.png               CGI conversions

  2. "flat" packs (built by the studio real-photo SOP / Wikimedia Commons
     harvests — see studio/docs/REAL-PHOTO-ENV-REFS.md):
         <pack>/<pack>-NN.jpg           source photos
         <pack>/_provenance.md          per-image provenance + "QA:" lines
         <pack>/cgi/<name>-daz.png      CGI plates (optional)
         <pack>/cgi/_provenance.md      conversion provenance (optional)

This tool walks references/locations/ and emits a single consumer index at
references/locations/index.json so downstream code (reference-gathering,
next_panel's env-ref fallback) never needs to know which convention a pack
uses.

Usage:
    pack_index.py [--root references/locations] [--write] [--verify]

    --write    write/refresh references/locations/index.json
    --verify   integrity check: referenced files exist, orphan files,
               unknown tags, incomplete packs. Exit 1 on hard errors.
    (default with neither flag: print the index to stdout)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
VOCAB_PATH = SKILL_DIR / "tag-vocabulary.json"

IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def load_vocab() -> dict:
    v = json.loads(VOCAB_PATH.read_text())
    v["_all_tags"] = set(v["framing"]) | set(v["setting"]) | set(v["mood_time"])
    return v


# ---------------------------------------------------------------- scout packs

def read_scout_pack(pack_dir: Path) -> dict:
    """Index a scout-convention pack from meta/locations.json or _targets.json."""
    slug = pack_dir.name
    targets = json.loads((pack_dir / "_targets.json").read_text())
    manifest_path = pack_dir / "meta" / "locations.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else None

    slots = targets.get("targets", [])
    n_src = sum(1 for s in slots if s.get("source_image"))
    n_cgi = sum(1 for s in slots if s.get("cgi_image"))
    if n_src == 0:
        status = "planned"
    elif n_cgi == 0:
        status = "sources-only"
    elif n_cgi < len(slots):
        status = "partial"
    else:
        status = "complete"

    entries = []
    source_rows = (manifest or {}).get("locations") or [
        s for s in slots if s.get("source_image")
    ]
    for row in source_rows:
        entries.append(
            {
                "id": row.get("final_id") or row.get("id"),
                "type": row.get("type"),
                "tags": row.get("tags", []),
                "intent": row.get("intent"),
                "neighborhood": row.get("neighborhood"),
                "source_image": row.get("source_image"),
                "cgi_image": row.get("cgi_image"),
                "qa": row.get("qa"),
                "variants": row.get("variants"),
            }
        )

    return {
        "slug": slug,
        "layout": "scout",
        "city": targets.get("city"),
        "status": status,
        "planned": len(slots),
        "captured": n_src,
        "converted": n_cgi,
        "locations": entries,
    }


# ----------------------------------------------------------------- flat packs

QA_LINE = re.compile(r"^\s*-\s*QA:\s*(?:\[([A-Z]+)\]\s*)?(.*)$")
HEADING = re.compile(r"^##\s+(\S+\.(?:jpg|jpeg|png|webp))\s*$", re.I)
PLATE_ROW = re.compile(
    r"^\|\s*([^|]+?\.(?:jpg|jpeg|png|webp))\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|", re.I
)


def parse_provenance(md: Path) -> dict[str, dict]:
    """Extract per-image {shot_tag, qa_note} from a flat pack's _provenance.md."""
    out: dict[str, dict] = {}
    cur = None
    for line in md.read_text().splitlines():
        h = HEADING.match(line)
        if h:
            cur = h.group(1)
            out[cur] = {}
            continue
        q = QA_LINE.match(line)
        if q and cur:
            out[cur] = {"shot_tag": q.group(1), "qa_note": q.group(2).strip()}
    return out


def parse_plate_table(md: Path) -> dict[str, dict]:
    """Extract {plate_filename: {shot, desc}} from a cgi/_provenance.md
    '## Plates' markdown table (| file | shot | source photo | ... |)."""
    out: dict[str, dict] = {}
    for line in md.read_text().splitlines():
        m = PLATE_ROW.match(line.strip())
        if m and m.group(1).lower() != "file":
            out[m.group(1)] = {
                "shot": m.group(2).strip(),
                "desc": m.group(3).strip(),
            }
    return out


def read_flat_pack(pack_dir: Path, vocab: dict) -> dict:
    slug = pack_dir.name
    sources = sorted(
        p for p in pack_dir.iterdir()
        if p.is_file() and p.suffix.lower() in IMG_EXTS
    )
    cgi_dir = pack_dir / "cgi"
    cgi_files = sorted(
        p for p in cgi_dir.iterdir()
        if p.is_file() and p.suffix.lower() in IMG_EXTS
    ) if cgi_dir.is_dir() else []

    prov = {}
    prov_md = pack_dir / "_provenance.md"
    if prov_md.exists():
        prov = parse_provenance(prov_md)

    shot_map = vocab.get("flat_shot_tag_map", {})
    entries = []
    for src in sources:
        stem = src.stem
        # cgi plate matches on stem prefix: <stem>-daz.png (or exact stem)
        plate = next(
            (c for c in cgi_files if c.stem in (f"{stem}-daz", stem)), None
        )
        meta = prov.get(src.name, {})
        tags = []
        if meta.get("shot_tag"):
            mapped = shot_map.get(meta["shot_tag"])
            if mapped:
                tags.append(mapped)
        entries.append(
            {
                "id": stem,
                "type": None,
                "tags": tags,
                "intent": meta.get("qa_note"),
                "neighborhood": None,
                "source_image": src.name,
                "cgi_image": f"cgi/{plate.name}" if plate else None,
                "qa": None,
                "variants": None,
            }
        )

    # Plates that didn't stem-match any source (renamed descriptively, e.g.
    # natal's coastline-reefs-aerial-daz.jpg) become standalone entries,
    # enriched from the cgi/_provenance.md '## Plates' table when present.
    matched_plates = {e["cgi_image"] for e in entries if e["cgi_image"]}
    plate_meta = {}
    plate_qa: dict = {}
    cgi_prov = cgi_dir / "_provenance.md" if cgi_dir.is_dir() else None
    if cgi_prov and cgi_prov.exists():
        plate_meta = parse_plate_table(cgi_prov)
    qa_path = cgi_dir / "_qa.json" if cgi_dir.is_dir() else None
    if qa_path and qa_path.exists():
        try:
            plate_qa = json.loads(qa_path.read_text())
        except json.JSONDecodeError:
            plate_qa = {}
    # attach QA to source-matched entries too
    for e in entries:
        if e["cgi_image"]:
            e["qa"] = plate_qa.get(Path(e["cgi_image"]).name)
    for plate in cgi_files:
        rel = f"cgi/{plate.name}"
        if rel in matched_plates:
            continue
        meta = plate_meta.get(plate.name, {})
        shot_tokens = (meta.get("shot") or "").lower().split()
        tags = [t for t in shot_tokens if t in vocab["_all_tags"]]
        entries.append(
            {
                "id": plate.stem,
                "type": None,
                "tags": tags,
                "intent": meta.get("desc"),
                "neighborhood": None,
                "source_image": None,
                "cgi_image": rel,
                "qa": plate_qa.get(plate.name),
                "variants": None,
            }
        )

    n_cgi = sum(1 for e in entries if e["cgi_image"])
    status = (
        "complete" if entries and n_cgi == len(entries)
        else "partial" if n_cgi
        else "sources-only" if entries
        else "empty"
    )
    return {
        "slug": slug,
        "layout": "flat",
        "city": None,
        "status": status,
        "planned": len(entries),
        "captured": len(entries),
        "converted": n_cgi,
        "locations": entries,
    }


# -------------------------------------------------------------------- walker

def build_index(root: Path) -> dict:
    vocab = load_vocab()
    packs = []
    for pack_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        if pack_dir.name.startswith((".", "_")) or pack_dir.name == "trash":
            continue
        try:
            if (pack_dir / "_targets.json").exists():
                packs.append(read_scout_pack(pack_dir))
            else:
                packs.append(read_flat_pack(pack_dir, vocab))
        except Exception as e:  # a broken pack must not sink the whole index
            packs.append(
                {"slug": pack_dir.name, "layout": "error", "status": "error",
                 "error": f"{type(e).__name__}: {e}", "locations": []}
            )
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "pack_count": len(packs),
        "packs": packs,
    }


# -------------------------------------------------------------------- verify

def verify(root: Path, index: dict) -> tuple[list[str], list[str]]:
    """Returns (errors, warnings)."""
    vocab = load_vocab()
    errors: list[str] = []
    warnings: list[str] = []

    for pack in index["packs"]:
        slug = pack["slug"]
        pdir = root / slug
        if pack["layout"] == "error":
            errors.append(f"{slug}: unreadable pack — {pack.get('error')}")
            continue

        referenced: set[Path] = set()
        for loc in pack["locations"]:
            for key in ("source_image", "cgi_image"):
                rel = loc.get(key)
                if not rel:
                    continue
                fp = pdir / rel
                referenced.add(fp.resolve())
                if not fp.exists():
                    errors.append(f"{slug}/{loc['id']}: missing {key} → {rel}")
            for t in loc.get("tags") or []:
                if t not in vocab["_all_tags"]:
                    warnings.append(f"{slug}/{loc['id']}: unknown tag '{t}'")

        # orphans: image files under the pack not referenced by any entry
        for sub in ("", "source", "cgi"):
            d = pdir / sub if sub else pdir
            if not d.is_dir():
                continue
            for f in d.iterdir():
                if f.is_file() and f.suffix.lower() in IMG_EXTS:
                    if f.resolve() not in referenced:
                        warnings.append(f"{slug}: orphan image not in index → "
                                        f"{f.relative_to(pdir)}")

        if pack["status"] in ("planned", "empty"):
            warnings.append(f"{slug}: status={pack['status']} "
                            f"(plan exists but no captures)")

    return errors, warnings


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Unified location-pack index / verify.")
    ap.add_argument("--root", type=Path, default=Path("references/locations"))
    ap.add_argument("--write", action="store_true",
                    help="write <root>/index.json")
    ap.add_argument("--verify", action="store_true",
                    help="integrity check; exit 1 on errors")
    args = ap.parse_args(argv)

    if not args.root.is_dir():
        print(f"ERROR: root {args.root} not found", file=sys.stderr)
        return 2

    index = build_index(args.root)

    if args.write:
        out = args.root / "index.json"
        tmp = out.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(index, indent=2) + "\n")
        os.replace(tmp, out)
        print(f"Wrote {out}: {index['pack_count']} packs, "
              f"{sum(len(p['locations']) for p in index['packs'])} locations")
        for p in index["packs"]:
            print(f"  {p['slug']:34} {p['layout']:6} {p['status']:13} "
                  f"{p.get('converted', 0)}/{p.get('planned', 0)} cgi")

    if args.verify:
        errors, warnings = verify(args.root, index)
        for w in warnings:
            print(f"WARN  {w}")
        for e in errors:
            print(f"ERROR {e}", file=sys.stderr)
        print(f"--- verify: {len(errors)} error(s), {len(warnings)} warning(s)")
        if errors:
            return 1

    if not args.write and not args.verify:
        print(json.dumps(index, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
