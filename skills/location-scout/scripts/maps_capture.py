#!/usr/bin/env python3
"""maps_capture.py — register a Google Maps screenshot into the scout pack.

The actual screenshot is taken by Claude via the Chrome MCP `computer` tool
(action=screenshot) on a viewport showing Google Maps Street View or a POI
Photos panel. This script handles the post-capture bookkeeping:

  - Normalize/save the screenshot under source/<id>-<slug>.jpg
  - Update _targets.json with `google_maps_query`, `source_image`, and
    provenance (URL, captured-at timestamp)
  - Optionally resize/clean (strip borders, downscale > 1920 px wide)

Usage:
    maps_capture.py --pack-dir references/locations/las-vegas/ \\
                    --slot-id street-01 \\
                    --query "Fremont Street Las Vegas" \\
                    --url "https://www.google.com/maps/..." \\
                    --screenshot /tmp/capture.png \\
                    [--name-slug fremont-street] \\
                    [--neighborhood Downtown]

    # Resume / list pending slots:
    maps_capture.py --pack-dir references/locations/las-vegas/ --list-pending
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def slugify(text: str) -> str:
    s = text.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[-\s]+", "-", s)
    return s.strip("-")


def load_plan(pack_dir: Path) -> dict:
    targets_path = pack_dir / "_targets.json"
    if not targets_path.exists():
        raise FileNotFoundError(
            f"{targets_path} missing. Run scout_city.py first."
        )
    return json.loads(targets_path.read_text())


def save_plan(pack_dir: Path, plan: dict) -> None:
    # Atomic write: a crash mid-write must not destroy the plan (it holds
    # every prior capture's provenance).
    targets_path = pack_dir / "_targets.json"
    tmp = targets_path.with_name("_targets.json.tmp")
    tmp.write_text(json.dumps(plan, indent=2) + "\n")
    os.replace(tmp, targets_path)


def find_slot(plan: dict, slot_id: str) -> dict:
    for slot in plan["targets"]:
        if slot["id"] == slot_id:
            return slot
    raise KeyError(f"slot_id={slot_id} not in plan. Known: " + ", ".join(s["id"] for s in plan["targets"]))


def normalize_image(src: Path, dst: Path, max_width: int = 1920) -> Path:
    """Copy src → dst as JPG, downscale if wider than max_width.

    Uses sips (macOS built-in) for format conversion + resize. If sips is
    unavailable or fails, falls back to a plain copy — but with the SOURCE's
    real extension, never a mislabeled .jpg. Returns the actual destination
    path written (may differ from `dst` in the fallback case).
    """
    if not src.exists():
        raise FileNotFoundError(f"screenshot source not found: {src}")

    if src.suffix.lower() in (".jpg", ".jpeg") and dst.suffix.lower() in (".jpg", ".jpeg"):
        # straight copy when already JPG
        shutil.copy(src, dst)
    else:
        # sips converts to JPG and writes to dst
        converted = False
        if shutil.which("sips"):
            try:
                subprocess.run(
                    [
                        "sips",
                        "-s", "format", "jpeg",
                        "-s", "formatOptions", "85",
                        str(src),
                        "--out", str(dst),
                    ],
                    check=True,
                    capture_output=True,
                )
                converted = True
            except subprocess.CalledProcessError:
                pass
        if not converted:
            # Plain copy keeping the real format: don't mislabel a PNG as .jpg
            dst = dst.with_suffix(src.suffix.lower())
            shutil.copy(src, dst)

    # Try to downscale via sips if wider than max_width
    if shutil.which("sips"):
        try:
            res = subprocess.run(
                ["sips", "-g", "pixelWidth", str(dst)],
                capture_output=True,
                text=True,
                check=True,
            )
            for line in res.stdout.splitlines():
                if "pixelWidth" in line:
                    width = int(line.strip().split(":")[1])
                    if width > max_width:
                        subprocess.run(
                            ["sips", "-Z", str(max_width), str(dst)],
                            check=True,
                            capture_output=True,
                        )
                    break
        except (subprocess.CalledProcessError, ValueError):
            pass

    return dst


def register_capture(
    pack_dir: Path,
    slot_id: str,
    query: str,
    url: str,
    screenshot: Path,
    name_slug: str | None,
    neighborhood: str | None,
) -> dict:
    plan = load_plan(pack_dir)
    slot = find_slot(plan, slot_id)

    # Build the canonical filename: <id>-<name-slug>.jpg
    name = name_slug or slugify(query)[:48] or slot_id
    final_id = f"{slot_id}-{name}"
    dst = pack_dir / "source" / f"{final_id}.jpg"

    # normalize_image may change the extension in the no-sips fallback;
    # record whatever was actually written.
    dst = normalize_image(screenshot, dst)

    # Update slot in plan
    slot["google_maps_query"] = query
    slot["google_maps_url"] = url
    slot["source_image"] = f"source/{dst.name}"
    slot["final_id"] = final_id
    slot["name_slug"] = name
    if neighborhood:
        slot["neighborhood"] = neighborhood
    slot["captured_at"] = datetime.now(timezone.utc).isoformat()

    try:
        save_plan(pack_dir, plan)
    except Exception:
        # Don't leave an orphan capture the plan knows nothing about
        dst.unlink(missing_ok=True)
        raise
    return slot


def list_pending(plan: dict) -> list[dict]:
    return [s for s in plan["targets"] if not s.get("source_image")]


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Register a Google Maps screenshot into the pack.")
    p.add_argument("--pack-dir", required=True, type=Path, help="Pack directory (contains _targets.json)")
    p.add_argument("--slot-id", help="Slot ID from _targets.json (e.g. street-01)")
    p.add_argument("--query", help="Google Maps search query used")
    p.add_argument("--url", help="Google Maps URL at the time of capture (provenance)")
    p.add_argument("--screenshot", type=Path, help="Path to the screenshot file")
    p.add_argument("--name-slug", help="Short name slug for filename (default: slugified query)")
    p.add_argument("--neighborhood", help="Neighborhood / district label (e.g. Downtown)")
    p.add_argument("--list-pending", action="store_true", help="Print pending slots and exit")
    args = p.parse_args(argv)

    if not args.pack_dir.exists():
        print(f"ERROR: pack dir {args.pack_dir} does not exist", file=sys.stderr)
        return 2

    plan = load_plan(args.pack_dir)

    if args.list_pending:
        pending = list_pending(plan)
        if not pending:
            print(f"All {plan['count']} slots have source_image set. Nothing pending.")
        else:
            print(f"{len(pending)} / {plan['count']} slots pending:")
            for s in pending:
                print(f"  - {s['id']:18}  type={s['type']:10}  intent: {s['intent']}")
        return 0

    if not (args.slot_id and args.query and args.url and args.screenshot):
        print(
            "ERROR: --slot-id, --query, --url, --screenshot all required "
            "(or pass --list-pending)",
            file=sys.stderr,
        )
        return 2

    slot = register_capture(
        args.pack_dir,
        args.slot_id,
        args.query,
        args.url,
        args.screenshot,
        args.name_slug,
        args.neighborhood,
    )
    print(f"Registered {slot['id']} → {slot['source_image']}")
    print(f"  query: {slot['google_maps_query']}")
    print(f"  url:   {slot.get('google_maps_url', '')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
