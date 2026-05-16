#!/usr/bin/env python3
"""Phase 6 — per-rule retry CLI.

For a panel whose ledger shows one or more failed rules, look up each rule's
retry_strategy() and print the recommended actions. Does NOT execute the
retries (regeneration is the runner's job). Use this CLI when the panel's
checks.json shows pre_render fail or post_render fail and you want to know
"what would the rule recommend doing?"

Usage:
    python retry_panel.py <project_root> <panel_id>
    python retry_panel.py <project_root> <panel_id> --rule L20
    python retry_panel.py <project_root> <panel_id> --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
COMIC_PRODUCTION_DIR = SCRIPT_DIR.parent
if str(COMIC_PRODUCTION_DIR) not in sys.path:
    sys.path.insert(0, str(COMIC_PRODUCTION_DIR))

from rules._registry import get_rule  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("project_root", type=Path)
    ap.add_argument("panel_id")
    ap.add_argument("--rule", help="Only inspect this rule (default: all failed rules)")
    ap.add_argument("--json", action="store_true", help="Emit JSON instead of markdown")
    args = ap.parse_args()

    project_root: Path = args.project_root.expanduser().resolve()
    ledger = project_root / "pages" / "panels" / f"panel-{args.panel_id}" / "checks.json"
    if not ledger.is_file():
        print(f"error: no ledger at {ledger}", file=sys.stderr)
        return 2

    data = json.loads(ledger.read_text())
    panel = {"panel_id": data.get("panel_id"),
             "page_number": data.get("page_number"),
             "muscle_size_tier": None,
             "transformation_beat": None,
             "characters": [], "hair_state": None}
    # We don't have full panel data here without re-running build_plan; the
    # retry strategies that READ panel state (like L11 model-ceiling check)
    # will return generic recommendations. Re-run build_plan(target_panel_id)
    # for richer ctx.
    ctx = {"transformation_type": data.get("transformation_type", "fmg")}

    out: list[dict] = []
    for rule_id, entry in data.get("rules", {}).items():
        if args.rule and rule_id != args.rule:
            continue
        pre = entry.get("pre_render") or {}
        post = entry.get("post_render") or {}
        failed_in = []
        failure = None
        if pre.get("status") == "fail":
            failed_in.append("pre_render")
            failure = {"verification": "pre_render", "reason": pre.get("reason")}
        if post.get("status") == "fail":
            failed_in.append("post_render")
            failure = {"verification": "post_render", "reason": post.get("reason"),
                       "evidence": post.get("evidence")}
        if not failed_in:
            continue

        rule = get_rule(rule_id)
        if rule is None:
            out.append({"rule_id": rule_id, "failed_in": failed_in, "failure": failure,
                        "retry": {"kind": "rule_not_in_registry",
                                  "note": "rule is tracked in trace but not yet a per-rule module"}})
            continue
        strategy = rule.retry_strategy(panel, ctx, failure or {})
        out.append({"rule_id": rule_id, "failed_in": failed_in, "failure": failure,
                    "retry": strategy})

    if not out:
        print(f"No failed rules on panel {args.panel_id}.")
        return 0

    if args.json:
        print(json.dumps(out, indent=2))
        return 0

    print(f"# Retry recommendations for panel {args.panel_id}\n")
    for row in out:
        print(f"## {row['rule_id']} — failed at {' + '.join(row['failed_in'])}")
        if row["failure"] and row["failure"].get("reason"):
            print(f"\n**Failure reason:** {row['failure']['reason']}\n")
        retry = row["retry"]
        print(f"**Retry kind:** `{retry.get('kind')}`")
        if retry.get("strengthening"):
            print(f"\n**Strengthening:** {retry['strengthening']}\n")
        if retry.get("suggestion"):
            print(f"\n**Suggestion:** {retry['suggestion']}\n")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
