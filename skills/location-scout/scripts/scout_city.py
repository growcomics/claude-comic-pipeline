#!/usr/bin/env python3
"""scout_city.py — plan a city location-scout pack.

Emits a _targets.json slot plan based on city + types + count. The plan is
city-agnostic at this layer (the planner does NOT know which Google Maps query
to use for "downtown" in Tokyo vs Las Vegas); Claude fills in `google_maps_query`
per slot in Phase B by combining the slot's `intent` with the city name.

Usage:
    scout_city.py --city "Las Vegas" \\
                  [--count 11] \\
                  [--types streets,restaurants,landmarks,specific] \\
                  [--output-root references/locations/]

Defaults (count=11):
    streets:     4   (downtown, residential, industrial, scenic)
    restaurants: 3   (fancy interior, diner interior, street-level exterior)
    landmarks:   2   (local-distinctive)
    specific:    2   (alley, rooftop)

--count N scales every type proportionally with floor(N * weight) and
distributes any remainder to the highest-weight types until N is reached.
--types narrows the mix; counts within remaining types are re-balanced.

Output:
    <output-root>/<city-slug>/
        _targets.json   — N slot entries, google_maps_query=null awaiting Claude
        source/         — empty, populated in Phase B
        cgi/            — empty, populated in Phase C
        meta/           — empty, populated in Phase D
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Default scope per type — (count, list_of_(intent, tags))
# Each "intent" entry expands to ONE slot of that type. Order within a type
# is intentional: variety across slots so a count of N=2 still hits two
# meaningfully different angles within that type.
DEFAULT_SCOPE = {
    "street": [
        ("downtown pedestrian street with neon signage", ["downtown", "neon", "pedestrian"]),
        ("main commercial avenue, midday traffic", ["commercial", "wide", "daytime"]),
        ("residential street, suburban housing", ["residential", "suburban", "quiet"]),
        ("industrial / warehouse district street", ["industrial", "back-of-house", "gritty"]),
        ("scenic / natural overlook street, mountains or coastline visible", ["scenic", "wide-vista"]),
    ],
    "restaurant": [
        ("diner interior, booths and counter", ["interior", "diner", "casual"]),
        ("fancy restaurant interior, low light", ["interior", "upscale", "evening"]),
        ("street-level restaurant exterior, signage visible", ["exterior", "storefront", "daytime"]),
        ("cafe interior, daytime, large windows", ["interior", "cafe", "daytime"]),
    ],
    "landmark": [
        ("iconic local landmark, exterior wide angle", ["landmark", "wide", "tourist"]),
        ("secondary local landmark, mid-distance angle", ["landmark", "mid", "tourist"]),
        ("transit hub or civic building exterior", ["civic", "exterior"]),
    ],
    "specific": [
        ("back alley, dumpsters and fire escapes", ["alley", "back-of-house", "noir"]),
        ("rooftop view over the city", ["rooftop", "skyline", "vantage"]),
        ("multi-story parking garage interior level", ["parking", "interior", "concrete"]),
        ("gym interior, weight room", ["interior", "gym", "fitness"]),
    ],
}

DEFAULT_WEIGHTS = {"street": 4, "restaurant": 3, "landmark": 2, "specific": 2}


def slugify(text: str) -> str:
    """City name -> 'las-vegas'-style slug."""
    s = text.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[-\s]+", "-", s)
    return s.strip("-")


def allocate(count: int, types: list[str]) -> dict[str, int]:
    """Split `count` across `types` proportionally to DEFAULT_WEIGHTS.

    Guarantees ≥1 per included type when count >= len(types); raises if
    count < len(types) (caller should bump count).
    """
    if count < len(types):
        raise ValueError(
            f"count={count} cannot cover {len(types)} types ({', '.join(types)}). "
            f"Use --count {len(types)}+ or trim --types."
        )

    total_weight = sum(DEFAULT_WEIGHTS[t] for t in types)
    # First pass: floor(count * w / total_weight), min 1
    alloc = {t: max(1, (count * DEFAULT_WEIGHTS[t]) // total_weight) for t in types}
    # Remainder: assign to heaviest-weight types in order until sum == count
    remainder = count - sum(alloc.values())
    if remainder > 0:
        # Sort types by weight desc, then alphabetically for determinism
        order = sorted(types, key=lambda t: (-DEFAULT_WEIGHTS[t], t))
        i = 0
        while remainder > 0:
            alloc[order[i % len(order)]] += 1
            remainder -= 1
            i += 1
    elif remainder < 0:
        # Overshot due to min-1 rounding; trim lightest types
        order = sorted(types, key=lambda t: (DEFAULT_WEIGHTS[t], t))
        i = 0
        while remainder < 0:
            t = order[i % len(order)]
            if alloc[t] > 1:
                alloc[t] -= 1
                remainder += 1
            i += 1
            if i > 1000:
                raise RuntimeError("allocate() infinite loop guard")
    return alloc


def build_slots(city: str, alloc: dict[str, int]) -> list[dict]:
    """Emit slot entries from the allocation map."""
    slots: list[dict] = []
    for type_name, n in alloc.items():
        templates = DEFAULT_SCOPE[type_name]
        for i in range(n):
            # Cycle through templates if N > len(templates)
            intent, tags = templates[i % len(templates)]
            slot_id = f"{type_name}-{i+1:02d}"
            slots.append(
                {
                    "id": slot_id,
                    "type": type_name,
                    "intent": intent,
                    "google_maps_query": None,
                    "source_image": None,
                    "cgi_image": None,
                    "tags": list(tags),
                }
            )
    return slots


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Plan a city location-scout pack.")
    p.add_argument("--city", required=True, help='City name (e.g. "Las Vegas")')
    p.add_argument(
        "--count",
        type=int,
        default=11,
        help="Total number of locations to scout (default: 11)",
    )
    p.add_argument(
        "--types",
        default="street,restaurant,landmark,specific",
        help="Comma-separated subset of types to include "
        "(default: street,restaurant,landmark,specific)",
    )
    p.add_argument(
        "--output-root",
        default="references/locations/",
        help="Where to write the pack folder (default: references/locations/)",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing _targets.json (default: refuse if exists)",
    )
    args = p.parse_args(argv)

    types = [t.strip() for t in args.types.split(",") if t.strip()]
    unknown = [t for t in types if t not in DEFAULT_SCOPE]
    if unknown:
        print(
            f"ERROR: unknown type(s): {unknown}. "
            f"Valid: {', '.join(DEFAULT_SCOPE.keys())}",
            file=sys.stderr,
        )
        return 2

    try:
        alloc = allocate(args.count, types)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    city_slug = slugify(args.city)
    if not city_slug:
        print(f"ERROR: city slug came out empty from '{args.city}'", file=sys.stderr)
        return 2

    out_root = Path(args.output_root).resolve()
    pack_dir = out_root / city_slug
    targets_path = pack_dir / "_targets.json"

    if targets_path.exists():
        if not args.force:
            print(
                f"ERROR: {targets_path} already exists. Use --force to overwrite.",
                file=sys.stderr,
            )
            return 1
        # --force replaces only the plan; warn about stale captures from the
        # previous plan that can collide with re-used slot IDs.
        leftovers = [
            f
            for sub in ("source", "cgi")
            for f in sorted((pack_dir / sub).glob("*"))
            if f.is_file()
        ]
        if leftovers:
            print(
                f"WARNING: --force replaces _targets.json but {len(leftovers)} "
                f"file(s) from the previous plan remain in source/ and cgi/. "
                f"Slot IDs repeat across plans, so new captures can silently "
                f"mix with old ones. Move the old files aside before Phase B.",
                file=sys.stderr,
            )

    # Create folder layout
    (pack_dir / "source").mkdir(parents=True, exist_ok=True)
    (pack_dir / "cgi").mkdir(parents=True, exist_ok=True)
    (pack_dir / "meta").mkdir(parents=True, exist_ok=True)

    slots = build_slots(args.city, alloc)
    plan = {
        "city": args.city,
        "city_slug": city_slug,
        "planned_at": datetime.now(timezone.utc).isoformat(),
        "count": len(slots),
        "allocation": alloc,
        "targets": slots,
    }

    targets_path.write_text(json.dumps(plan, indent=2) + "\n")

    print(f"Wrote {targets_path}")
    print(f"  city: {args.city}  slug: {city_slug}")
    print(f"  allocation: {alloc}  total: {len(slots)}")
    print(f"  pack dir: {pack_dir}")
    print()
    print("Next: Phase B — for each slot in _targets.json,")
    print("  1. Fill in google_maps_query (city + intent)")
    print("  2. Drive Chrome MCP to maps.google.com, screenshot")
    print("  3. Run scripts/maps_capture.py --slot-id <id> --screenshot <path> --url <url>")

    return 0


if __name__ == "__main__":
    sys.exit(main())
