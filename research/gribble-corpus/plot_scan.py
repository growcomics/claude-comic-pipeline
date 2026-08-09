#!/usr/bin/env python3
"""Second pass over the corpus — PLOT, not structure.

The first pass (profile.py) measured the page grid and growth density and got
those right. It said almost nothing useful about story: the generator ended up
writing "ordinary woman consumes a thing, gets strong, wins," which the owner
correctly called not-very-Gribble.

This extracts a readable SKELETON of every script — the setup, the ending, and
the biggest growth beat — so the actual plot machinery can be read rather than
guessed at, plus regex probes for the devices the owner named: twists,
overpowering, power theft, villain turns.
"""
from __future__ import annotations

import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from profile import CORPUS, parse, read, page_text, ACTIVE, GROWTH  # noqa: E402

PROBES = {
    "power_transfer": r"\b(drain|drains|draining|steal|steals|stole|stolen|transfer|transferr?ed|"
                      r"absorb|absorbs|absorbing|siphon|takes? (?:her|his) (?:power|strength)|"
                      r"lose[sd]? (?:her|his) (?:power|strength|muscle))\b",
    "overpower":      r"\b(overpower|overpowers|crush|crushes|crushing|humiliat|beat(?:s|en)? up|"
                      r"lifts? her|pins? her|toss(?:es|ed)? her|effortless|helpless|no match|"
                      r"one hand|snaps? (?:it|him|her)|dominat)\b",
    "rival_wins":     r"\b(rival|nemesis|enemy)\b",
    "villain_turn":   r"\b(evil|villain|wicked|cruel|revenge|conquer|rule the|enslav|world domination|"
                      r"laughing|hahaha|maniacal)\b",
    "giantess":       r"\b(giantess|towering over the city|planet|galaxy|god|goddess|colossal|"
                      r"skyscraper|larger than the|size of a (?:mountain|building))\b",
    "backfire":       r"\b(too much|out of control|can't stop|cannot stop|uncontroll|side effect|"
                      r"went wrong|not exactly|mistake|accident|shouldn'?t have|regret)\b",
    "swap_or_split":  r"\b(swap|swapped|switch(?:ed)? bodies|split into|clone|duplicate|copy of her)\b",
    "twist_marker":   r"\b(but then|suddenly|little did|unknown to|it turns out|reveal|secretly|"
                      r"all along|surprise|plot twist|unbeknownst)\b",
}


def condense(t: str, n: int) -> str:
    t = re.sub(r"\s+", " ", t).strip()
    return t[:n] + ("…" if len(t) > n else "")


def main() -> int:
    seen, docs = set(), []
    for fn in sorted(os.listdir(CORPUS)):
        if not fn.endswith(".txt"):
            continue
        d = parse(read(os.path.join(CORPUS, fn)))
        if len(d["pages"]) < 4:
            continue
        k = d["title"].strip().lower()
        if k in seen:
            continue
        seen.add(k)
        docs.append(d)

    tally = Counter()
    for d in docs:
        pages = d["pages"]
        full = " ".join(page_text(p) for p in pages).lower()
        hits = [k for k, rx in PROBES.items() if re.search(rx, full, re.I)]
        for h in hits:
            tally[h] += 1

        # the single biggest growth page
        best, bi = None, -1
        for i, p in enumerate(pages):
            t = page_text(p)
            sc = len(ACTIVE.findall(t)) * 2 + len(GROWTH.findall(t))
            if best is None or sc > best:
                best, bi = sc, i

        print("=" * 100)
        print(f"### {d['title']}  ({len(pages)} pages)")
        print(f"  DEVICES: {', '.join(hits) if hits else '—'}")
        print(f"  OPEN  : {condense(page_text(pages[0]), 320)}")
        print(f"  PEAK  : [p{bi+1}] {condense(page_text(pages[bi]), 300)}")
        if len(pages) >= 2:
            print(f"  END-1 : {condense(page_text(pages[-2]), 260)}")
        print(f"  END   : {condense(page_text(pages[-1]), 340)}")

    print("=" * 100)
    print(f"\nDEVICE FREQUENCY across {len(docs)} scripts:")
    for k, v in tally.most_common():
        print(f"  {v:3d}/{len(docs)}  ({100*v/len(docs):3.0f}%)  {k}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
