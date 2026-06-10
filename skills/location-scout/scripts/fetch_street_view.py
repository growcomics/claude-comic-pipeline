#!/usr/bin/env python3
"""fetch_street_view.py — Phase B alternative.

Fetches Street View Static API images for every target in a location-scout
pack's _targets.json. Replaces Chrome MCP screenshotting when (a) Chrome MCP
isn't connected, (b) screenshots can't be persisted to disk from this side,
or (c) we want a clean, repeatable, headless workflow.

Uses Google Maps Street View Static API:
    https://developers.google.com/maps/documentation/streetview/overview

Pricing: ~$0.007 per image. A typical 10-target pack costs ~$0.07.

Setup (one-time):
    1. Create / pick a Google Cloud project at console.cloud.google.com
    2. Enable: "Street View Static API"
       (and "Places API (New)" later if you want interior photos)
    3. Create an API key under APIs & Services -> Credentials
    4. (Recommended) Restrict the key to those two APIs
    5. Export it:
        export GOOGLE_MAPS_API_KEY=AIza...

Usage:
    fetch_street_view.py --pack-dir references/locations/lakewood-california \\
                        [--api-key $GOOGLE_MAPS_API_KEY] \\
                        [--size 1600x900] \\
                        [--fov 90] \\
                        [--pitch 0] \\
                        [--overwrite]

Reads `<pack-dir>/_targets.json`. For each target with `google_maps_query`
set, calls Street View Static using the query string as the `location`
parameter. Saves JPG to `<pack-dir>/source/<target-id>-<slug>.jpg`. Updates
the target's `source_image` field on success.

Per-target overrides (optional fields in _targets.json):
    "heading": <int 0-360>        # camera direction, default 0
    "pitch":   <int -90..90>      # up/down tilt, default 0
    "fov":     <int 10-120>       # field of view, default 90
    "size":    "WxH"              # image size, default 1600x900
    "skip":    true               # skip this target (e.g. interior photos)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

STREET_VIEW_ENDPOINT = "https://maps.googleapis.com/maps/api/streetview"


def slugify(text: str, max_len: int = 60) -> str:
    """Filesystem-safe slug from a free-form string."""
    s = re.sub(r"[^a-zA-Z0-9-]+", "-", text.lower()).strip("-")
    s = re.sub(r"-+", "-", s)
    return s[:max_len].rstrip("-")


def derive_slug(target: dict) -> str:
    """Pick a descriptive slug from query / intent / id."""
    candidates = [
        target.get("google_maps_query"),
        target.get("intent"),
        target.get("name"),
        target.get("id"),
    ]
    for c in candidates:
        if c:
            slug = slugify(c)
            if slug:
                return slug
    return target.get("id", "unknown")


def fetch_one(target: dict, api_key: str, defaults: dict, source_dir: Path,
              overwrite: bool = False, verbose: bool = True) -> dict:
    """Fetch a single Street View image. Returns {ok, path, http_status, bytes, error}."""
    query = target.get("google_maps_query")
    if not query:
        return {"ok": False, "error": "no google_maps_query set on target",
                "target_id": target.get("id")}

    if target.get("skip"):
        return {"ok": False, "error": "target marked skip=true",
                "target_id": target.get("id"), "skipped": True}

    slug = derive_slug(target)
    out_name = f"{target['id']}-{slug}.jpg"
    out_path = source_dir / out_name

    if out_path.exists() and not overwrite:
        return {"ok": True, "path": str(out_path), "skipped_existing": True,
                "target_id": target.get("id")}

    params = {
        "size": target.get("size", defaults["size"]),
        "location": query,
        "fov": str(target.get("fov", defaults["fov"])),
        "heading": str(target.get("heading", defaults["heading"])),
        "pitch": str(target.get("pitch", defaults["pitch"])),
        "key": api_key,
        "return_error_code": "true",
    }
    url = f"{STREET_VIEW_ENDPOINT}?{urlencode(params)}"

    if verbose:
        # Strip key from log
        safe_url = url.replace(api_key, "***")
        print(f"  GET {safe_url}", file=sys.stderr)

    try:
        req = Request(url, headers={"User-Agent": "claude-comic-pipeline location-scout"})
        with urlopen(req, timeout=20) as resp:
            data = resp.read()
            ctype = resp.headers.get("Content-Type", "")
            status = resp.status
    except HTTPError as e:
        body = e.read()[:300].decode("utf-8", errors="replace")
        return {"ok": False, "http_status": e.code, "error": f"HTTPError {e.code}: {body}",
                "target_id": target.get("id")}
    except URLError as e:
        return {"ok": False, "error": f"URLError: {e}",
                "target_id": target.get("id")}

    if "image" not in ctype.lower():
        return {"ok": False, "http_status": status,
                "error": f"non-image response (Content-Type={ctype}): {data[:200].decode('utf-8', errors='replace')}",
                "target_id": target.get("id")}

    out_path.write_bytes(data)
    return {"ok": True, "path": str(out_path), "bytes": len(data),
            "http_status": status, "target_id": target.get("id"),
            "filename": out_name}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pack-dir", required=True, type=Path,
                    help="Path to a location-scout pack directory containing _targets.json")
    ap.add_argument("--api-key", default=os.environ.get("GOOGLE_MAPS_API_KEY"),
                    help="Google Maps API key. Defaults to $GOOGLE_MAPS_API_KEY")
    ap.add_argument("--size", default="1600x900",
                    help="Image WxH, max 640x640 per request without billing tier; we allow larger")
    ap.add_argument("--fov", type=int, default=90,
                    help="Field of view 10-120, default 90")
    ap.add_argument("--pitch", type=int, default=0,
                    help="Up/down tilt -90..90, default 0")
    ap.add_argument("--heading", type=int, default=0,
                    help="Camera direction 0-360 (north=0), default 0")
    ap.add_argument("--overwrite", action="store_true",
                    help="Re-fetch even if source file already exists")
    ap.add_argument("--throttle-ms", type=int, default=200,
                    help="Sleep between requests in ms, default 200")
    args = ap.parse_args()

    if not args.api_key:
        print("ERROR: no API key. Set $GOOGLE_MAPS_API_KEY or pass --api-key.", file=sys.stderr)
        return 2

    pack_dir = args.pack_dir.resolve()
    targets_path = pack_dir / "_targets.json"
    if not targets_path.exists():
        print(f"ERROR: {targets_path} not found", file=sys.stderr)
        return 2

    data = json.loads(targets_path.read_text())
    source_dir = pack_dir / "source"
    source_dir.mkdir(parents=True, exist_ok=True)

    defaults = {"size": args.size, "fov": args.fov, "pitch": args.pitch, "heading": args.heading}

    print(f"city: {data.get('city')}  pack: {pack_dir.name}", file=sys.stderr)
    print(f"targets: {len(data['targets'])}  source dir: {source_dir}", file=sys.stderr)
    print(f"defaults: {defaults}", file=sys.stderr)
    print("", file=sys.stderr)

    results = []
    for i, t in enumerate(data["targets"]):
        print(f"[{i+1}/{len(data['targets'])}] {t['id']} -- {t.get('google_maps_query', '<no query>')}", file=sys.stderr)
        r = fetch_one(t, args.api_key, defaults, source_dir, overwrite=args.overwrite)
        results.append(r)
        if r["ok"]:
            if r.get("skipped_existing"):
                print(f"  exists, skipping (use --overwrite to re-fetch)", file=sys.stderr)
            else:
                print(f"  saved {r['filename']} ({r['bytes']/1024:.1f}KB)", file=sys.stderr)
                # Update the target's source_image field
                t["source_image"] = f"source/{r['filename']}"
        else:
            if r.get("skipped"):
                print(f"  skip (marked in _targets.json)", file=sys.stderr)
            else:
                print(f"  FAILED: {r.get('error')}", file=sys.stderr)
        print("", file=sys.stderr)
        if args.throttle_ms > 0:
            time.sleep(args.throttle_ms / 1000)

    # Persist any source_image updates
    targets_path.write_text(json.dumps(data, indent=2) + "\n")

    ok = sum(1 for r in results if r["ok"] and not r.get("skipped_existing"))
    existed = sum(1 for r in results if r.get("skipped_existing"))
    failed = sum(1 for r in results if not r["ok"] and not r.get("skipped"))
    skipped = sum(1 for r in results if r.get("skipped"))

    print(f"== summary ==", file=sys.stderr)
    print(f"fetched fresh: {ok}", file=sys.stderr)
    print(f"already on disk: {existed}", file=sys.stderr)
    print(f"explicitly skipped: {skipped}", file=sys.stderr)
    print(f"failed: {failed}", file=sys.stderr)
    print(f"\nupdated {targets_path.name} with source_image fields", file=sys.stderr)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
