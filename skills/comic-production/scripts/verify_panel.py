#!/usr/bin/env python3
"""Phase 7 — verify-only mode for a single panel.

Re-runs all pre_render verifications (and prints the rendered-image path
for any rule that has a vision_rubric, so the orchestrator can dispatch
post-render vision audits via a subagent).

Usage:
    python verify_panel.py <project_root> <panel_id>
    python verify_panel.py <project_root> <panel_id> --json
    python verify_panel.py <project_root> <panel_id> --vision-rubrics
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

from next_panel import build_plan  # noqa: E402
from checks_ledger import write_checks_ledger, append_defects, _iso_now  # noqa: E402
from rules._registry import get_rule, iter_rules  # noqa: E402


def _detect_accepted_variant_label(project_root: Path, panel_id: str) -> str | None:
    folder = project_root / "pages" / "panels" / f"panel-{panel_id}"
    if not folder.is_dir():
        folder = project_root / "pages" / "panels" / panel_id
    if folder.is_dir():
        acc_txt = folder / "_accepted.txt"
        if acc_txt.exists():
            return acc_txt.read_text().strip()
        suffixed = sorted(folder.glob("v*_accepted.png"))
        if suffixed:
            return suffixed[-1].stem.split("_")[0]
    flat = project_root / "pages" / "panels" / f"{panel_id}.png"
    if flat.exists():
        return "v1 (flat)"
    return None


def _accepted_image_path(project_root: Path, panel_id: str,
                         variant_label: str | None) -> Path | None:
    folder = project_root / "pages" / "panels" / f"panel-{panel_id}"
    if not folder.is_dir():
        folder = project_root / "pages" / "panels" / panel_id
    if not folder.is_dir():
        flat = project_root / "pages" / "panels" / f"{panel_id}.png"
        return flat if flat.exists() else None
    if variant_label:
        cand = folder / f"{variant_label}_accepted.png"
        if cand.exists():
            return cand
        cand2 = folder / f"{variant_label}.png"
        if cand2.exists():
            return cand2
    matches = sorted(folder.glob("v*_accepted.png"))
    if matches:
        return matches[-1]
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("project_root", type=Path)
    ap.add_argument("panel_id")
    ap.add_argument("--json", action="store_true", help="JSON output")
    ap.add_argument("--vision-rubrics", action="store_true",
                    help="Print each rule's vision_rubric (for orchestrator-side audits)")
    args = ap.parse_args()

    project_root: Path = args.project_root.expanduser().resolve()
    plan = build_plan(project_root, target_panel_id=args.panel_id)
    if plan.get("error") or plan.get("next_panel") is None:
        msg = plan.get("error") or plan.get("message")
        print(f"error: {msg}", file=sys.stderr)
        return 2

    accepted_variant = _detect_accepted_variant_label(project_root, args.panel_id)
    image_path = _accepted_image_path(project_root, args.panel_id, accepted_variant)

    ts = _iso_now()
    ledger_path = write_checks_ledger(project_root, plan,
                                      accepted_variant_label=accepted_variant,
                                      composed_at=ts)
    n_defects = append_defects(project_root, plan, ts=ts)

    trace = plan.get("_trace") or {}

    if args.json:
        out = {
            "ledger_path": str(ledger_path.relative_to(project_root)),
            "image_path": str(image_path.relative_to(project_root)) if image_path else None,
            "defects_appended": n_defects,
            "trace": trace,
        }
        if args.vision_rubrics:
            rubrics = {}
            for rule in iter_rules():
                if rule.vision_rubric and rule.id in trace and trace[rule.id].get("applied"):
                    rubrics[rule.id] = rule.vision_rubric
            out["vision_rubrics"] = rubrics
        print(json.dumps(out, indent=2, default=str))
        return 0

    print(f"# Verify panel {args.panel_id}\n")
    print(f"- Ledger: `{ledger_path.relative_to(project_root)}`")
    print(f"- Accepted variant: `{accepted_variant or '<none>'}`")
    print(f"- Image: `{image_path.relative_to(project_root) if image_path else '<missing>'}`")
    print(f"- Defects appended: {n_defects}\n")

    applied = sum(1 for e in trace.values() if e.get("applied"))
    pre_fail = sum(1 for e in trace.values()
                   if (e.get("pre_render") or {}).get("status") == "fail")
    print(f"## Trace summary\n")
    print(f"- Rules applied: {applied}/{len(trace)}")
    print(f"- Pre-render fails: {pre_fail}\n")

    if pre_fail:
        print("## Pre-render failures\n")
        for rid, entry in trace.items():
            if (entry.get("pre_render") or {}).get("status") == "fail":
                print(f"- **{rid}**: {entry['pre_render'].get('reason')}")
        print()

    if args.vision_rubrics:
        print("## Vision rubrics (orchestrator dispatches subagents per rule)\n")
        for rule in iter_rules():
            if not rule.vision_rubric:
                continue
            entry = trace.get(rule.id) or {}
            if not entry.get("applied"):
                continue
            print(f"### {rule.id} — {rule.title}\n")
            print(f"```\n{rule.vision_rubric}\n```\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
