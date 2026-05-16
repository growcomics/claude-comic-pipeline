#!/usr/bin/env python3
"""Emit per-panel checks.json ledgers for an existing comic project.

Phase 1 deliverable of the checks-and-balances refactor. See
docs/checks-and-balances-design.md.

For every accepted panel in <project>/pages/panels/panel-*/, re-runs the
planning logic in build_plan() with that panel as the target and the
accepted history reconstructed for the moment the panel was composed.
Writes the ledger to checks.json next to the panel image, and appends
failure rows to <project>/defects.jsonl.

This tool does NOT regenerate images — it's a paper-only re-derivation
of the plan + trace as it would have been at compose time. Useful for:

  - retroactive auditing of comics that shipped before the ledger existed
  - re-verifying after a rule's verification logic changes
  - bootstrapping the defects log from historical data

Usage:
    python write_ledger.py <project_root>
    python write_ledger.py <project_root> --panel-id p07-01
    python write_ledger.py <project_root> --dry-run

Exits 0 on success, 1 if no panels were processed, 2 on script error.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Resolve sibling imports when run as a script.
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from next_panel import build_plan, read_shotlist, iter_panels, panel_status  # noqa: E402
from checks_ledger import write_checks_ledger, append_defects, _iso_now  # noqa: E402


def _list_accepted_panel_ids(project_root: Path) -> list[tuple[int, str]]:
    """Return [(page_number, panel_id), ...] for every accepted panel in
    story order."""
    shotlist = read_shotlist(project_root)
    if shotlist is None:
        return []
    out: list[tuple[int, str]] = []
    for page_num, panel in iter_panels(shotlist):
        status = panel_status(project_root, panel)
        if status["state"] != "accepted":
            continue
        pid = panel.get("panel_id") or panel.get("name")
        if pid:
            out.append((page_num, pid))
    return out


def _detect_accepted_variant_label(project_root: Path, panel_id: str) -> str | None:
    """Find which variant was accepted for this panel, if any.

    Mirrors panel_status() recognition: `_accepted.txt` first, then
    `v*_accepted.png`, then flat fallback.
    """
    folder = project_root / "pages" / "panels" / f"panel-{panel_id}"
    if not folder.is_dir():
        folder = project_root / "pages" / "panels" / panel_id
    if folder.is_dir():
        acc_txt = folder / "_accepted.txt"
        if acc_txt.exists():
            return acc_txt.read_text().strip()
        suffixed = sorted(folder.glob("v*_accepted.png"))
        if suffixed:
            # filename like v3_accepted.png → label "v3"
            return suffixed[-1].stem.split("_")[0]
    flat = project_root / "pages" / "panels" / f"{panel_id}.png"
    if flat.exists():
        return "v1 (flat)"
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("project_root", type=Path)
    ap.add_argument("--panel-id", help="Only emit ledger for this panel ID (default: all accepted panels)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Compose plans and print summary, but do not write checks.json or defects.jsonl")
    ap.add_argument("--verbose", action="store_true",
                    help="Print one line per panel with applied/skipped counts")
    args = ap.parse_args()

    root: Path = args.project_root.expanduser().resolve()
    if not root.exists():
        print(f"error: project root does not exist: {root}", file=sys.stderr)
        return 2

    shotlist = read_shotlist(root)
    if shotlist is None:
        print(f"error: shotlist.json not found at {root}", file=sys.stderr)
        return 2

    if args.panel_id:
        targets = [(None, args.panel_id)]  # page_number unknown until plan
    else:
        targets = _list_accepted_panel_ids(root)

    if not targets:
        print("no accepted panels to process")
        return 1

    n_written = 0
    n_defects_total = 0
    ts = _iso_now()
    for page_num, panel_id in targets:
        plan = build_plan(root, target_panel_id=panel_id)
        if plan.get("error") or plan.get("next_panel") is None:
            print(f"  skip {panel_id}: {plan.get('error') or plan.get('message')}", file=sys.stderr)
            continue
        trace = plan.get("_trace") or {}
        applied = sum(1 for e in trace.values() if e.get("applied"))
        n_total = len(trace)
        pre_fail = sum(1 for e in trace.values()
                       if (e.get("pre_render") or {}).get("status") == "fail")
        post_fail = sum(1 for e in trace.values()
                        if (e.get("post_render") or {}).get("status") == "fail")
        accepted_variant = _detect_accepted_variant_label(root, panel_id)

        if args.dry_run:
            print(f"  DRY  {panel_id} (p{plan['next_panel'].get('page_number')}): "
                  f"applied={applied}/{n_total}  pre_fail={pre_fail}  post_fail={post_fail}  "
                  f"accepted_variant={accepted_variant or '<none>'}")
            continue

        ledger_path = write_checks_ledger(root, plan,
                                          accepted_variant_label=accepted_variant,
                                          composed_at=ts)
        n_defects = append_defects(root, plan, ts=ts)
        n_written += 1
        n_defects_total += n_defects
        if args.verbose:
            print(f"  wrote {ledger_path.relative_to(root)}  "
                  f"applied={applied}/{n_total}  pre_fail={pre_fail}  post_fail={post_fail}  "
                  f"defects+={n_defects}  accepted_variant={accepted_variant or '<none>'}")

    if args.dry_run:
        print(f"\nDRY-RUN summary: {len(targets)} panel(s) would be ledger'd, none written")
        return 0

    print(f"\nwrote {n_written} ledger(s); appended {n_defects_total} defect rows to {root / 'defects.jsonl'}")
    return 0 if n_written else 1


if __name__ == "__main__":
    sys.exit(main())
