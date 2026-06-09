#!/usr/bin/env python3
"""cgi_convert.py — convert source captures to photoreal CGI via Higgsfield.

This script does NOT call the Higgsfield MCP directly — MCP tool calls are made
from Claude's tool layer, not from Python. Instead, this script:

  - Emits the conversion prompt + Higgsfield params for a given slot
    (`--slot-id X --emit-prompt`); Claude reads stdout, then calls
    mcp__c26fa20c-...__generate_image with those params.
  - Downloads a finished job's result URL into cgi/<id>-<slug>.png and
    updates _targets.json (`--slot-id X --download <url>`).
  - Emits the final canonical manifest into meta/locations.json
    (`--emit-manifest`).
  - Lists slots needing conversion (`--list-pending-cgi`).
  - Resume helper: --slot-id X --skip-existing skips slots already done.

Usage examples:

    # Get the prompt + params to feed to generate_image:
    cgi_convert.py --pack-dir references/locations/las-vegas/ \\
                   --slot-id street-01 \\
                   --emit-prompt
    # stdout is JSON: {"model": "nano_banana_pro", "prompt": "...", "aspect_ratio": "16:9", "source_path": "source/street-01-fremont-street.jpg"}

    # After Claude calls generate_image and gets a result URL:
    cgi_convert.py --pack-dir references/locations/las-vegas/ \\
                   --slot-id street-01 \\
                   --download "https://higgsfield.../result.png"

    # Final pass:
    cgi_convert.py --pack-dir references/locations/las-vegas/ --emit-manifest
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# The canonical conversion prompt. Same body for every slot; the per-slot
# `intent` is appended as a scene anchor.
#
# Style target: OBVIOUSLY CGI — the output should read as a stylized 3D
# render, not a photograph. Think default DAZ3D Iray render, architectural
# visualization, or video-game cinematic — the model defaults to hyper-photoreal
# which makes the CGI quality vanish. We tone it down by removing
# micro-detail anchors ("8K texture", "subsurface scattering") and adding
# explicit "clearly rendered, not photographic" language. Comic background
# refs benefit from this — a too-photoreal env ref clashes with the CGI
# character render and breaks the look.
PROMPT_BODY = (
    "Re-render this real-world photograph as a stylized 3D CGI scene — "
    "default DAZ3D / Iray render look, architectural visualization quality, "
    "video-game cinematic. It should clearly read as a 3D render, NOT a "
    "photograph. Cleaner shaders, smoother surfaces, slightly simplified "
    "geometry. Match the composition, architecture, lighting direction, "
    "time of day, and overall color palette of the source. Do NOT match "
    "photographic micro-detail (no skin pores, no dust speckles, no film "
    "grain) — keep it CG-clean. Do NOT change the camera angle, framing, "
    "focal length, or perspective. Do NOT add or remove buildings, signs, "
    "vehicles, or signage text. SAME scene, SAME composition, CGI re-render. "
    "No people in frame — only the empty location/setting. If any people "
    "appear in the source, render the same scene without them. Remove "
    "Google Maps watermarks, Street View brand stamps, and any UI overlays. "
    "Render at 1k, stylized 3D CGI look."
)

# Aspect ratio per type — landscape for outdoor / street / landmark; 4:3 for
# tighter interiors.
DEFAULT_ASPECT_BY_TYPE = {
    "street": "16:9",
    "landmark": "16:9",
    "specific": "16:9",
    "restaurant": "4:3",  # interiors and storefront close-ups
}

# Model defaults
MODEL_DEFAULT = "nano_banana_pro"  # top quality, 2 credits / gen
MODEL_FAST = "nano_banana_2"  # 1.5 credits / gen


def load_plan(pack_dir: Path) -> dict:
    p = pack_dir / "_targets.json"
    if not p.exists():
        raise FileNotFoundError(f"{p} missing")
    return json.loads(p.read_text())


def save_plan(pack_dir: Path, plan: dict) -> None:
    p = pack_dir / "_targets.json"
    p.write_text(json.dumps(plan, indent=2) + "\n")


def find_slot(plan: dict, slot_id: str) -> dict:
    for slot in plan["targets"]:
        if slot["id"] == slot_id:
            return slot
    raise KeyError(f"slot_id={slot_id} not in plan")


def build_prompt(slot: dict) -> str:
    return f"{PROMPT_BODY}\n\nScene anchor: {slot['intent']}."


def emit_prompt(pack_dir: Path, slot_id: str, model: str) -> dict:
    plan = load_plan(pack_dir)
    slot = find_slot(plan, slot_id)
    if not slot.get("source_image"):
        raise RuntimeError(f"slot {slot_id} has no source_image yet")
    aspect = DEFAULT_ASPECT_BY_TYPE.get(slot["type"], "16:9")
    return {
        "slot_id": slot_id,
        "model": model,
        "prompt": build_prompt(slot),
        "aspect_ratio": aspect,
        "count": 1,
        "resolution": "1k",
        "source_path": slot["source_image"],
        "source_abs_path": str((pack_dir / slot["source_image"]).resolve()),
        "media_role": "image",
    }


def download_result(pack_dir: Path, slot_id: str, url: str) -> dict:
    plan = load_plan(pack_dir)
    slot = find_slot(plan, slot_id)
    final_id = slot.get("final_id", slot_id)
    dst = pack_dir / "cgi" / f"{final_id}.png"

    with urllib.request.urlopen(url) as resp:
        data = resp.read()
    dst.write_bytes(data)

    slot["cgi_image"] = f"cgi/{final_id}.png"
    slot["cgi_url"] = url
    slot["cgi_completed_at"] = datetime.now(timezone.utc).isoformat()
    save_plan(pack_dir, plan)
    return slot


def register_local_result(pack_dir: Path, slot_id: str, local_path: Path) -> dict:
    """Used when the result was already downloaded locally and just needs
    to be registered into the plan."""
    plan = load_plan(pack_dir)
    slot = find_slot(plan, slot_id)
    final_id = slot.get("final_id", slot_id)
    dst = pack_dir / "cgi" / f"{final_id}.png"
    if local_path.resolve() != dst.resolve():
        dst.write_bytes(local_path.read_bytes())
    slot["cgi_image"] = f"cgi/{final_id}.png"
    slot["cgi_completed_at"] = datetime.now(timezone.utc).isoformat()
    save_plan(pack_dir, plan)
    return slot


def emit_manifest(pack_dir: Path) -> dict:
    plan = load_plan(pack_dir)
    locations = []
    for slot in plan["targets"]:
        if not slot.get("source_image"):
            continue  # incomplete slot — skip from manifest
        loc = {
            "id": slot.get("final_id", slot["id"]),
            "type": slot["type"],
            "name": slot.get("name_slug", slot["id"]),
            "intent": slot["intent"],
            "google_maps_query": slot.get("google_maps_query"),
            "google_maps_url": slot.get("google_maps_url"),
            "source_image": slot["source_image"],
            "cgi_image": slot.get("cgi_image"),
            "tags": slot.get("tags", []),
        }
        if "neighborhood" in slot:
            loc["neighborhood"] = slot["neighborhood"]
        locations.append(loc)

    manifest = {
        "city": plan["city"],
        "city_slug": plan["city_slug"],
        "scouted_at": datetime.now(timezone.utc).isoformat(),
        "count": len(locations),
        "locations": locations,
    }

    out = pack_dir / "meta" / "locations.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def list_pending_cgi(plan: dict) -> list[dict]:
    return [
        s
        for s in plan["targets"]
        if s.get("source_image") and not s.get("cgi_image")
    ]


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Convert source captures to CGI via Higgsfield.")
    p.add_argument("--pack-dir", required=True, type=Path)
    p.add_argument("--slot-id", help="Slot to operate on")
    p.add_argument("--model", default=MODEL_DEFAULT, choices=[MODEL_DEFAULT, MODEL_FAST, "gpt_image_2"])
    p.add_argument("--fast", action="store_true", help=f"Alias for --model {MODEL_FAST}")
    p.add_argument("--emit-prompt", action="store_true", help="Print Higgsfield params for this slot")
    p.add_argument("--download", metavar="URL", help="Download the CGI result URL for this slot")
    p.add_argument("--register-local", metavar="PATH", type=Path, help="Register an already-downloaded CGI image for this slot")
    p.add_argument("--emit-manifest", action="store_true", help="Write meta/locations.json from current plan")
    p.add_argument("--list-pending-cgi", action="store_true", help="List slots needing CGI conversion")
    args = p.parse_args(argv)

    if not args.pack_dir.exists():
        print(f"ERROR: pack dir {args.pack_dir} does not exist", file=sys.stderr)
        return 2

    model = MODEL_FAST if args.fast else args.model

    if args.list_pending_cgi:
        plan = load_plan(args.pack_dir)
        pending = list_pending_cgi(plan)
        if not pending:
            print(f"No pending CGI conversions in {args.pack_dir}.")
        else:
            print(f"{len(pending)} slots pending CGI conversion:")
            for s in pending:
                print(f"  - {s['id']:18}  source={s['source_image']}")
        return 0

    if args.emit_manifest:
        manifest = emit_manifest(args.pack_dir)
        print(f"Wrote {args.pack_dir / 'meta' / 'locations.json'}")
        print(f"  {manifest['count']} locations")
        return 0

    if not args.slot_id:
        print("ERROR: --slot-id required (or use --list-pending-cgi / --emit-manifest)", file=sys.stderr)
        return 2

    if args.emit_prompt:
        params = emit_prompt(args.pack_dir, args.slot_id, model)
        print(json.dumps(params, indent=2))
        return 0

    if args.download:
        slot = download_result(args.pack_dir, args.slot_id, args.download)
        print(f"Saved {slot['cgi_image']}")
        return 0

    if args.register_local:
        slot = register_local_result(args.pack_dir, args.slot_id, args.register_local)
        print(f"Registered {slot['cgi_image']}")
        return 0

    print(
        "ERROR: nothing to do. Pass --emit-prompt, --download, --register-local, "
        "--emit-manifest, or --list-pending-cgi.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
