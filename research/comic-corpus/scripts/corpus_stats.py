#!/usr/bin/env python3
"""corpus_stats.py — roll up per-comic beats.json into corpus-wide metrics.

Reads every corpus/<slug>/beats.json and computes the derived numbers the
rubric defines but does NOT store per-comic (so the raw analysis stays small
and a future, smarter model can recompute these — or new metrics — without
re-reading a single page):

  - growth_page_ratio        = growth pages / total pages   (the niche metric)
  - shot_distance histogram  + distance_spread per page
  - flat_panel_pct           = panels staged flat-level only / total panels
  - mean_expression_intensity + dead_face_pct
  - escalation-device leaderboard across the corpus
  - the 0-5 axis scores per comic, side by side

Usage:
    corpus_stats.py --corpus-root research/comic-corpus/corpus
    corpus_stats.py --corpus-root research/comic-corpus/corpus --json   # machine output
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

GROWTH_STATES = {"trigger", "early", "mid", "peak"}
DISTANCE_ORDER = ["EWS", "WS", "MLS", "MS", "MCU", "CU", "ECU"]


def load_all(corpus_root: Path) -> list[dict]:
    out = []
    for beats in sorted(corpus_root.glob("*/beats.json")):
        try:
            data = json.loads(beats.read_text())
            data["_path"] = str(beats)
            out.append(data)
        except (json.JSONDecodeError, OSError) as e:
            print(f"WARN: skipping {beats}: {e}", file=sys.stderr)
    return out


def comic_metrics(data: dict) -> dict:
    pages = data.get("pages", [])
    total_pages = len(pages)
    growth_pages = sum(
        1
        for p in pages
        if p.get("growth_state") in GROWTH_STATES or p.get("role") == "active-growth"
    )

    panels = [pan for p in pages for pan in p.get("panels", [])]
    total_panels = len(panels)

    dist_hist = Counter(pan.get("shot_distance") for pan in panels if pan.get("shot_distance"))

    flat_panels = sum(
        1
        for pan in panels
        if pan.get("staging") and set(pan["staging"]) == {"flat-level"}
    )

    intensities = [
        pan["expression_intensity"]
        for pan in panels
        if isinstance(pan.get("expression_intensity"), int) and pan["expression_intensity"] > 0
    ]
    dead_faces = sum(
        1
        for pan in panels
        if isinstance(pan.get("expression_intensity"), int) and pan["expression_intensity"] == 1
    )

    # distance spread per page (distinct bands), averaged
    spreads = []
    for p in pages:
        bands = {pan.get("shot_distance") for pan in p.get("panels", []) if pan.get("shot_distance")}
        if bands:
            spreads.append(len(bands))

    devices = Counter()
    for sc in data.get("scene_breakdown", []):
        for d in sc.get("escalation_devices", []):
            devices[d] += 1

    growth_focus_panels = sum(1 for pan in panels if pan.get("growth_focus"))

    return {
        "comic_id": data.get("comic_id"),
        "total_pages": total_pages,
        "growth_pages": growth_pages,
        "growth_page_ratio": round(growth_pages / total_pages, 3) if total_pages else 0.0,
        "total_panels": total_panels,
        "panels_per_page": round(total_panels / total_pages, 2) if total_pages else 0.0,
        "distance_hist": {d: dist_hist.get(d, 0) for d in DISTANCE_ORDER},
        "mean_distance_spread": round(sum(spreads) / len(spreads), 2) if spreads else 0.0,
        "flat_panel_pct": round(100 * flat_panels / total_panels, 1) if total_panels else 0.0,
        "growth_focus_panel_pct": round(100 * growth_focus_panels / total_panels, 1) if total_panels else 0.0,
        "mean_expression_intensity": round(sum(intensities) / len(intensities), 2) if intensities else 0.0,
        "dead_face_pct": round(100 * dead_faces / total_panels, 1) if total_panels else 0.0,
        "escalation_devices": dict(devices.most_common()),
        "scores": data.get("scores", {}),
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Roll up comic-corpus beats.json into metrics.")
    p.add_argument("--corpus-root", required=True, type=Path)
    p.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = p.parse_args(argv)

    if not args.corpus_root.exists():
        print(f"ERROR: {args.corpus_root} does not exist", file=sys.stderr)
        return 2

    comics = load_all(args.corpus_root)
    if not comics:
        print(f"No beats.json found under {args.corpus_root}.", file=sys.stderr)
        return 1

    metrics = [comic_metrics(c) for c in comics]

    # corpus-wide device leaderboard
    corpus_devices = Counter()
    for m in metrics:
        for d, n in m["escalation_devices"].items():
            corpus_devices[d] += n

    summary = {
        "comic_count": len(metrics),
        "total_pages": sum(m["total_pages"] for m in metrics),
        "corpus_growth_page_ratio": round(
            sum(m["growth_pages"] for m in metrics) / sum(m["total_pages"] for m in metrics), 3
        )
        if sum(m["total_pages"] for m in metrics)
        else 0.0,
        "escalation_device_leaderboard": dict(corpus_devices.most_common()),
        "comics": metrics,
    }

    if args.json:
        print(json.dumps(summary, indent=2))
        return 0

    # human table
    print(f"\nCORPUS: {summary['comic_count']} comics, {summary['total_pages']} pages")
    print(f"Corpus growth-page ratio: {summary['corpus_growth_page_ratio']*100:.0f}%\n")
    hdr = f"{'comic':40} {'pg':>3} {'grow%':>6} {'dist↔':>6} {'flat%':>6} {'exprI':>6} {'dead%':>6}  scores(G/C/E/S)"
    print(hdr)
    print("-" * len(hdr))
    for m in metrics:
        s = m["scores"]
        scorestr = f"{s.get('growth_density_score','?')}/{s.get('camera_dynamism_score','?')}/{s.get('expression_intensity_score','?')}/{s.get('story_structure_score','?')}"
        print(
            f"{(m['comic_id'] or '?')[:40]:40} {m['total_pages']:>3} "
            f"{m['growth_page_ratio']*100:>5.0f}% {m['mean_distance_spread']:>6.2f} "
            f"{m['flat_panel_pct']:>5.1f}% {m['mean_expression_intensity']:>6.2f} "
            f"{m['dead_face_pct']:>5.1f}%  {scorestr}"
        )
    print(f"\nEscalation-device leaderboard (corpus-wide):")
    for d, n in summary["escalation_device_leaderboard"].items():
        print(f"  {n:>3}×  {d}")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
