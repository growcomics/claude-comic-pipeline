#!/usr/bin/env python3
"""Calibration harness for the STORY gates in studio/gribble.php.

Companion to validate_targets.py, which covers the STRUCTURE gates (page grid,
growth density, merges). This one covers the story-axis gates, mirroring
gr_report()'s logic exactly:

  * splash repetition  (gr_sim + the L36/F5b consecutive-merged-page check)
  * ending closure     (L36/F5c — "The End" / a page after the last growth / dialogue)
  * dominance          (88% of the corpus — somebody gets physically overpowered)
  * ending type        (apotheosis 71% / deflation 12% — a warm resolution is un-Gribble)

Same rule as always: a gate that rejects Gribble's own work is measuring the wrong
thing. The dominance and ending-type gates were added 2026-08-09 after the owner
pointed out that generated scripts hit every structural target and still read
nothing like Gribble — the generator was writing wholesome empowerment. The first
draft of the ending pattern failed 34% of his endings because it omitted the
contempt-for-mortals and cosmic-scale vocabulary ("PUNY MORTALS", "a Universe to
rule"); broadened, the pair passes 83%.

Run after ANY edit to GR_DOMINANCE / GR_APOTHEOSIS / GR_DEFLATION / gr_sim.
"""
from __future__ import annotations

import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from profile import CORPUS, parse, read, page_text, ACTIVE, GROWTH  # noqa: E402

# --- mirrors of the PHP constants -------------------------------------------
DOMINANCE = (r"\b(overpower\w*|crush\w*|humiliat\w*|stomp\w*|pins? (?:her|him)|lifts? (?:her|him)|"
             r"by the throat|backhand\w*|flick\w*|effortless\w*|helpless|no match|puny|pathetic|"
             r"insect|mortals?|kneel\w*|bow(?:s|ing)? (?:down|before)|worship\w*|begs?|beggin|"
             r"sent (?:her|him) flying|tosse[sd])\b")
APOTHEOSIS = (r"\b(worship\w*|kneel\w*|bow down|rule (?:the|this) (?:world|universe)|conquer\w*|"
              r"goddess|god\b|supreme|almighty|omnipotent|reality itself|obey|serve me|mortals?|"
              r"puny|insect|universe|galax\w+|planet|limitless|beyond all)\b")
DEFLATION = (r"\b(losing (?:my|her|his) power|lost (?:her|his|my) power|shrink\w*|shrunk|"
             r"back to normal|it'?s over|drained away|no longer super|powerless|too unstable|"
             r"gone forever|nothing is happening|my power)\b")


def sim(a: str, b: str) -> float:
    """Mirror of gr_sim()."""
    A = set(re.findall(r"[a-z']{3,}", a.lower()))
    B = set(re.findall(r"[a-z']{3,}", b.lower()))
    if len(A) < 8 or len(B) < 8:
        return 0.0
    return len(A & B) / len(A | B)


def is_growth(t: str) -> bool:
    return len(ACTIVE.findall(t)) >= 2 or (
        len(ACTIVE.findall(t)) >= 1 and len(GROWTH.findall(t)) >= 3)


def gates(doc: dict) -> list[str]:
    pages = doc["pages"]
    n = len(pages)
    whole = " ".join(page_text(p) for p in pages)
    tail = " ".join(page_text(p) for p in pages[-2:])

    mflags, gflags, pdesc = [], [], []
    for p in pages:
        spans = [s.get("span", 1) for s in p]
        merged = any(s > 1 for s in spans)
        t = page_text(p)
        mflags.append(merged)
        gflags.append(is_growth(t) or (merged and bool(GROWTH.search(t))))
        pdesc.append(" ".join(s["desc"] for s in p))

    f = []

    # splash repetition — consecutive MERGED pages restating each other
    pair = {}
    for i in range(n - 1):
        if mflags[i] and mflags[i + 1]:
            pair[i] = sim(pdesc[i], pdesc[i + 1])
    if any(s >= 0.55 for s in pair.values()):
        f.append("splash-repeat-pair")
    if any(s >= 0.40 and pair.get(i + 1, 0.0) >= 0.40 for i, s in pair.items()):
        f.append("splash-repeat-chain")

    # ending closure
    last_g = max((k for k, g in enumerate(gflags) if g), default=-1)
    last_dlg = sum(len(s["lines"]) for s in pages[-1])
    has_end = bool(re.search(r"\bthe\s+end\b", whole[-400:], re.I))
    if not (has_end or (0 <= last_g < n - 1) or last_dlg > 0):
        f.append("ending-mid-swing")

    # story devices
    if not re.search(DOMINANCE, whole, re.I):
        f.append("no-dominance")
    if not re.search(APOTHEOSIS, tail, re.I) and not re.search(DEFLATION, tail, re.I):
        f.append("ending-neither")
    return f


def main() -> int:
    seen, rows = set(), []
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
        rows.append((d["title"], gates(d)))

    n = len(rows)
    clean = [r for r in rows if not r[1]]
    why = Counter(x for _, f in rows for x in f)

    print(f"STORY GATES vs Gribble's own {n} scripts")
    print(f"  pass every story gate: {len(clean)}/{n} ({100*len(clean)/n:.0f}%)\n")
    print("  which gates bite:")
    for k, v in why.most_common():
        print(f"    {v:3d}/{n}  ({100*v/n:3.0f}%)  {k}")
    print("\n  scripts that would be sent back for repair:")
    for t, f in rows:
        if f:
            print(f"    {t[:46]:<48} {','.join(f)}")

    # A story gate biting more than ~20% of the corpus is miscalibrated, not strict.
    bad = [k for k, v in why.items() if v / n > 0.20]
    print()
    if bad:
        print(f"  ⚠️  OVER-STRICT (>20% of his own work): {', '.join(bad)}")
        return 1
    print("  ✅ every story gate stays under the 20% false-reject line")
    return 0


if __name__ == "__main__":
    sys.exit(main())
