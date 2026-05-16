#!/usr/bin/env python3
"""Phase 7 — defects.jsonl discovery tool.

Reads <project>/defects.jsonl and produces a summary report. Three views:

  - by-rule:   which rules fail most in this chapter
  - by-panel:  which panels have the most failures
  - timeline:  recent vs. older defects (correlation with rule changes)

Usage:
    python discover_defects.py <project_root>
    python discover_defects.py <project_root> --by panel
    python discover_defects.py <project_root> --rule L20
    python discover_defects.py <project_root> --markdown > defects-report.md
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


def read_defects(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    rows: list[dict] = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def by_rule(rows: list[dict]) -> dict[str, int]:
    return dict(Counter(r["rule_id"] for r in rows))


def by_panel(rows: list[dict]) -> dict[str, int]:
    return dict(Counter(r["panel_id"] for r in rows))


def by_rule_and_verification(rows: list[dict]) -> dict[tuple[str, str], int]:
    return dict(Counter((r["rule_id"], r.get("verification") or "?") for r in rows))


def by_ts(rows: list[dict]) -> dict[str, int]:
    # Group by day
    out: Counter = Counter()
    for r in rows:
        ts = r.get("ts") or ""
        day = ts[:10] if ts else "unknown"
        out[day] += 1
    return dict(out)


def reasons_for_rule(rows: list[dict], rule_id: str) -> list[tuple[str, str]]:
    """Return list of (panel_id, reason) for the given rule."""
    return [(r["panel_id"], r.get("reason") or "") for r in rows if r["rule_id"] == rule_id]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("project_root", type=Path)
    ap.add_argument("--by", choices=["rule", "panel", "ts", "rule_verification"],
                    default="rule", help="Grouping for the summary")
    ap.add_argument("--rule",
                    help="Drill into one rule — print every defect row for it")
    ap.add_argument("--markdown", action="store_true",
                    help="Markdown output (default)")
    ap.add_argument("--json", action="store_true",
                    help="JSON output instead of markdown")
    args = ap.parse_args()

    project_root: Path = args.project_root.expanduser().resolve()
    defects_path = project_root / "defects.jsonl"
    rows = read_defects(defects_path)

    if not rows:
        print(f"no defects.jsonl rows at {defects_path}")
        return 1

    if args.rule:
        reasons = reasons_for_rule(rows, args.rule)
        if args.json:
            print(json.dumps([{"panel_id": p, "reason": r} for p, r in reasons], indent=2))
        else:
            print(f"# Defects for {args.rule} — {len(reasons)} entries\n")
            for p, r in reasons:
                print(f"- **{p}** — {r}")
        return 0

    if args.by == "rule":
        counts = by_rule(rows)
    elif args.by == "panel":
        counts = by_panel(rows)
    elif args.by == "ts":
        counts = by_ts(rows)
    elif args.by == "rule_verification":
        kv = by_rule_and_verification(rows)
        counts = {f"{r}/{v}": n for (r, v), n in kv.items()}
    else:
        counts = by_rule(rows)

    if args.json:
        payload = {
            "project": str(project_root),
            "total_defects": len(rows),
            "grouping": args.by,
            "counts": counts,
        }
        print(json.dumps(payload, indent=2))
        return 0

    title = project_root.name
    print(f"# Defects report — {title}\n")
    print(f"Total defect rows: **{len(rows)}** (from `{defects_path.relative_to(project_root)}`)\n")
    print(f"## Grouped by {args.by}\n")
    print("| Key | Count |")
    print("|---|---|")
    for key, n in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"| `{key}` | {n} |")
    print()
    # Top 3 rules — print their top reasons
    if args.by == "rule":
        top = sorted(counts.items(), key=lambda x: -x[1])[:3]
        for rule_id, n in top:
            print(f"### Top reasons for {rule_id} ({n} defects)\n")
            reasons = Counter(r.get("reason") or "" for r in rows if r["rule_id"] == rule_id)
            for reason, m in reasons.most_common(3):
                print(f"- ({m}×) {reason}")
            print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
