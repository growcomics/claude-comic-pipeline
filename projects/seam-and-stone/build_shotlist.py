#!/usr/bin/env python3
"""Script -> shotlist for Seam and Stone.

A Gribble-format script is already panel-level (`Page N` / `Panel N- direction` /
`Speaker- "line"`), so there is no prose to break down — the breakdown is a parse,
not an AI call. This emits one row per DRAWN SLOT (a merged "Panels 1, 2, 3 and 4-"
page is ONE slot, one full-page image, which is the whole point of Gribble's grid
break) with camera, cast, dialogue and Marla's growth tier resolved.

Feeds: the panel beat sheet for the bakeoff lane, once the reference sheets from
runners/bakeoff/queue/seam-and-stone-refs.json are generated and locked.

    python3 build_shotlist.py <script.txt> > shotlist.json
"""
from __future__ import annotations

import json
import os
import re
import sys

sys.path.insert(0, os.path.expanduser("~/Documents/claude-comic-pipeline/research/gribble-corpus"))
from profile import parse  # noqa: E402  (the corpus parser already handles merged slots)

CAST = ["Marla", "Jess", "Annie", "Coach"]

# Camera, inferred from the art direction's own language. Order matters — the
# tightest match wins, so ECU is tested before the wide/establishing cues.
CAMERA = [
    ("ecu",          r"\b(close on|closeup|close[- ]up|extreme close)\b"),
    ("establishing", r"(\bestablishing\b|\bwide shot\b|\bbirdseye\b|from far below|"
                     r"\bshot of (?:a|the|some)\b|\bexterior\b|\boutside (?:of )?the\b)"),
    ("wide",         r"\b(whole crowd|entire campus|from a distance|towering over|full height)\b"),
]

# Marla's size ladder — which tier the artist should be rendering her at.
# Derived from the beats in the script, not guessed: she is baseline until the
# tear, subtle through the "doesn't notice" run, visible at the serve, huge after
# the reclaim, then colossal.
def marla_tier(page: int) -> int:
    if page <= 2:  return 1     # unremarkable
    if page <= 6:  return 2     # subtly broader — the unnoticed-growth run
    if page <= 12: return 3     # visibly dense, seams going
    if page <= 17: return 4     # far beyond bodybuilder
    if page <= 19: return 5     # ~30 feet
    return 6                    # city-block colossal


def camera_for(desc: str, merged: bool) -> str:
    if merged:
        return "full-page"
    for name, rx in CAMERA:
        if re.search(rx, desc, re.I):
            return name
    return "medium"


def main() -> int:
    src = sys.argv[1]
    doc = parse(open(src, encoding="utf-8").read())
    rows = []
    for pi, page in enumerate(doc["pages"], start=1):
        for si, slot in enumerate(page, start=1):
            # the parser keeps the "(Full page panel)- " prefix when the line reads
            # "Panels 1, 2, 3 and 4- (Full page panel)- ..." — strip it, it is layout
            # metadata and already captured by span/layout
            desc = re.sub(r"^\(?full[- ]?page(?:\s+panel)?\)?\s*[-:.]\s*", "", slot["desc"], flags=re.I).strip()
            merged = slot.get("span", 1) > 1

            # ON-SCREEN cast comes from the ART DIRECTION only. A character named in
            # dialogue is not in frame — "Coach still doesn't know your name" put the
            # Coach in a panel he is nowhere near.
            cast = [c for c in CAST if re.search(rf"\b{c}\b", desc, re.I)]
            for who, _ in slot["lines"]:                     # a speaker IS present
                w = who.strip().split()[0].title()
                if w in CAST and w not in cast:
                    cast.append(w)
            mentioned = [c for c in CAST
                         if c not in cast
                         and any(re.search(rf"\b{c}\b", l, re.I) for _, l in slot["lines"])]
            rows.append({
                "id": f"p{pi:02d}s{si}",
                "page": pi,
                "slot": si,
                "span": slot.get("span", 1),
                "layout": "full-page merge" if merged else "panel",
                "camera": camera_for(desc, merged),
                "cast": cast,
                "mentionedOnly": mentioned,
                "marlaTier": marla_tier(pi) if "Marla" in cast else None,
                "action": desc,
                "dialogue": [{"who": w, "line": l} for w, l in slot["lines"]],
            })

    merged_n = sum(1 for r in rows if r["span"] > 1)
    out = {
        "project": "seam-and-stone",
        "title": doc["title"],
        "source": os.path.basename(src),
        "pages": len(doc["pages"]),
        "slots": len(rows),
        "fullPageMerges": merged_n,
        "note": ("Merged slots are ONE full-page image, never a four-panel grid — that grid break is "
                 "how the transformation is staged (70% of Gribble's merged pages are growth vs 1.7% "
                 "of ordinary panels)."),
        "shots": rows,
    }
    json.dump(out, sys.stdout, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
