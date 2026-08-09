#!/usr/bin/env python3
"""Calibration check: run studio/gribble.php's PASS/FAIL gate against Gribble's OWN
scripts.

The generator rejects a draft that misses the corpus targets and sends it back for
repair. If those same targets reject the man's actual work, the gate is wrong — it
would be training the generator away from the thing it is imitating. This script
applies the identical rules (ported from gr_report()) to every real script and
reports the pass rate and which rules bite.

Only scripts of >=12 pages are gated the same way a generated 20-pager would be;
short pieces (7 pages) legitimately cannot carry 3 separate growth runs.
"""
from __future__ import annotations

import os
import statistics
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from profile import CORPUS, ACTIVE, GROWTH, parse, read, page_text  # noqa: E402


def is_growth(t: str) -> bool:
    return len(ACTIVE.findall(t)) >= 2 or (
        len(ACTIVE.findall(t)) >= 1 and len(GROWTH.findall(t)) >= 3)


def report(pages: list) -> tuple[dict, list[str]]:
    n = len(pages)
    gflags, mflags, bad_grid, descw, silent, slots, linew = [], [], [], [], 0, 0, []
    for i, page in enumerate(pages):
        spans = [p.get("span", 1) for p in page]
        merged = any(s > 1 for s in spans)
        if sum(spans) != 4:
            bad_grid.append(i + 1)
        txt = page_text(page)
        mflags.append(merged)
        gflags.append(is_growth(txt) or (merged and bool(GROWTH.search(txt))))
        for p in page:
            slots += 1
            descw.append(len(p["desc"].split()))
            if not p["lines"]:
                silent += 1
            linew += [len(w.split()) for _, w in p["lines"]]

    runs, c = [], 0
    for g in gflags:
        if g:
            c += 1
        elif c:
            runs.append(c); c = 0
    if c:
        runs.append(c)

    gp, mp = sum(gflags), sum(mflags)
    first = gflags.index(True) if gp else None
    align = (sum(1 for k in range(n) if mflags[k] and gflags[k]) / mp) if mp else 0.0

    m = {
        "pages": n, "growthPct": round(100 * gp / n, 1), "runs": runs,
        "runCount": len(runs), "longestRun": max(runs) if runs else 0,
        "mergedPct": round(100 * mp / n, 1), "mergedAlignPct": round(100 * align, 1),
        "firstGrowthPct": round(100 * (first + 1) / n, 1) if first is not None else None,
        "descMedian": statistics.median(descw) if descw else 0,
        "silentPct": round(100 * silent / slots, 1) if slots else 0,
        "badGrid": len(bad_grid),
    }

    # Thresholds mirror gr_report() in studio/gribble.php. Two kinds of rule here:
    #   (a) DESCRIPTIVE — calibrated so Gribble's own scripts pass. If a rule rejects
    #       his work it is measuring the wrong thing, and it got loosened.
    #   (b) DELIBERATE FLOORS — growth density and the grid-break device, held at the
    #       high end of his range on purpose. The owner's standing direction is that
    #       growth IS the product, so the generator should write like his BEST scripts
    #       (Social Order, Not Exactly as Planned), not his median. These knowingly
    #       reject his low-growth outliers (The Hotter Sister at 4.8%).
    need_runs = 3 if m["pages"] >= 16 else 2
    f = []
    if len(bad_grid) > max(2, round(0.1 * n)):
        f.append(f"grid({len(bad_grid)}pp)")
    if m["growthPct"] < 20: f.append("growth<20")          # (b) floor
    if m["growthPct"] > 55: f.append("growth>55")
    if m["runCount"] < need_runs: f.append(f"runs<{need_runs}")
    if m["longestRun"] < 2: f.append("longestRun<2")
    if m["mergedPct"] < 20: f.append("merged<20")          # (b) floor — the device
    if m["mergedPct"] > 65: f.append("merged>65")
    if mp and m["mergedAlignPct"] < 45: f.append("align<45")
    if m["firstGrowthPct"] is None: f.append("nogrowth")
    elif m["firstGrowthPct"] > 30: f.append("firstLate")
    if m["descMedian"] > 30: f.append("desc>30")
    if m["silentPct"] < 8: f.append("silent<8")
    return m, f


def main() -> int:
    seen, rows = set(), []
    for fn in sorted(os.listdir(CORPUS)):
        if not fn.endswith(".txt"):
            continue
        text = read(os.path.join(CORPUS, fn))
        doc = parse(text)
        if len(doc["pages"]) < 4:
            continue
        key = doc["title"].strip().lower()
        if key in seen:
            continue
        seen.add(key)
        m, f = report(doc["pages"])
        rows.append((doc["title"][:38], m, f))

    long_rows = [r for r in rows if r[1]["pages"] >= 12]
    passed = [r for r in long_rows if not r[2]]
    print(f"{len(rows)} scripts · {len(long_rows)} of >=12 pages (gated like a generated 20-pager)")
    print(f"PASS the generator's gate: {len(passed)}/{len(long_rows)} "
          f"({100*len(passed)/len(long_rows):.0f}%)\n")

    why = Counter(x for _, _, f in long_rows for x in f)
    print("which rules bite, across his own scripts:")
    for k, v in why.most_common():
        print(f"  {v:3d}x  {k}")

    print("\nper-script (>=12pp):")
    for title, m, f in sorted(long_rows, key=lambda r: len(r[2])):
        flag = "PASS" if not f else "fail: " + ",".join(f)
        print(f"  {m['pages']:3d}pp  g={m['growthPct']:5.1f}%  merge={m['mergedPct']:5.1f}%  "
              f"align={m['mergedAlignPct']:5.1f}%  runs={str(m['runs'])[:18]:<18} {title:<38} {flag}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
