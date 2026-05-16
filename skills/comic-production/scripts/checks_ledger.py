#!/usr/bin/env python3
"""Per-panel checks.json ledger + project-level defects.jsonl log.

Phase 1 of the checks-and-balances refactor. See
docs/checks-and-balances-design.md for the full design. This module is the
"emit-only" half — it writes the ledger and defects log from a plan dict
produced by `next_panel.build_plan()`. It does NOT change generation behavior.

Two functions:

- `write_checks_ledger(project_root, plan, *, accepted_variant_label=None,
                       composed_at=None) -> Path`
  Writes `pages/panels/panel-<panel_id>/checks.json`. Returns the path.

- `append_defects(project_root, plan, *, ts=None) -> int`
  Appends one JSONL row per failed (status=fail) verification in the trace
  to `defects.jsonl` at the project root. Returns the number of rows added.

CLI usage (verify-only mode is in write_ledger.py — this module is the
library used by both that CLI and the runner integration in later phases).
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


SCHEMA_VERSION = 1


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _shotlist_snapshot_sha(project_root: Path) -> str | None:
    p = project_root / "shotlist.json"
    if not p.is_file():
        return None
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def _ledger_path(project_root: Path, panel_id: str) -> Path:
    return project_root / "pages" / "panels" / f"panel-{panel_id}" / "checks.json"


def write_checks_ledger(
    project_root: Path,
    plan: dict,
    *,
    accepted_variant_label: str | None = None,
    composed_at: str | None = None,
) -> Path:
    """Serialize the per-panel trace from `plan` to checks.json.

    `plan` is the dict returned by `build_plan()` (or `_compose_with_trace`).
    Must contain `next_panel`, `_trace`, `composed_prompt`, and
    `transformation_type`.

    `accepted_variant_label` should be set by the runner after a variant is
    picked (e.g. "v3"). Left None for compose-time ledger writes.

    Creates the panel folder if needed (it normally exists from prior runs,
    but verify-only mode may write ledgers for panels whose folder used the
    older `<panel_id>/` shape — we tolerate both by writing under the
    canonical `panel-<id>/` form, alongside whatever's already there).
    """
    project_root = Path(project_root)
    next_panel = plan.get("next_panel") or {}
    panel_id = next_panel.get("panel_id")
    if not panel_id:
        raise ValueError("plan.next_panel.panel_id is required to write a ledger")

    trace = plan.get("_trace") or {}
    transformation_type = plan.get("transformation_type") or "fmg"

    out_path = _ledger_path(project_root, panel_id)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    ledger = {
        "schema_version": SCHEMA_VERSION,
        "panel_id": panel_id,
        "page_number": next_panel.get("page_number"),
        "transformation_type": transformation_type,
        "shotlist_snapshot_sha": _shotlist_snapshot_sha(project_root),
        "composed_at": composed_at or _iso_now(),
        "composed_prompt": plan.get("composed_prompt"),
        "accepted_variant_label": accepted_variant_label,
        "rules": trace,
    }

    out_path.write_text(json.dumps(ledger, indent=2, ensure_ascii=False) + "\n")
    return out_path


def _defects_path(project_root: Path) -> Path:
    return Path(project_root) / "defects.jsonl"


def append_defects(
    project_root: Path,
    plan: dict,
    *,
    ts: str | None = None,
) -> int:
    """Append one JSONL row per pre_render=fail entry in the trace.

    Returns the count of rows appended. Defect rows include:
      ts, panel_id, page_number, rule_id, severity, reason, retry_history.

    `severity` is "hard" for pre_render fail and "soft" for skipped-with-
    reason that contains "violation" or "warning" wording. The discovery
    layer (later phase) can re-classify.
    """
    project_root = Path(project_root)
    next_panel = plan.get("next_panel") or {}
    panel_id = next_panel.get("panel_id")
    page_number = next_panel.get("page_number")
    trace = plan.get("_trace") or {}
    ts = ts or _iso_now()

    rows: list[dict] = []
    for rule_id, entry in trace.items():
        pre = entry.get("pre_render") or {}
        post = entry.get("post_render") or {}
        if pre.get("status") == "fail":
            rows.append({
                "ts": ts,
                "panel_id": panel_id,
                "page_number": page_number,
                "rule_id": rule_id,
                "severity": "hard",
                "verification": "pre_render",
                "reason": pre.get("reason"),
                "retry_history": [],
            })
        if post.get("status") == "fail":
            rows.append({
                "ts": ts,
                "panel_id": panel_id,
                "page_number": page_number,
                "rule_id": rule_id,
                "severity": "hard",
                "verification": "post_render",
                "reason": post.get("reason"),
                "retry_history": [],
            })

    if not rows:
        return 0

    out = _defects_path(project_root)
    with out.open("a") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return len(rows)


# ---------------------------------------------------------------------------
# Convenience: combined write (used by the next_panel.py runner integration
# when phase 4 hooks the ledger into the pipeline). Phase 1 callers (the
# write_ledger.py CLI) call write_checks_ledger and append_defects
# separately.


def write_ledger_and_defects(
    project_root: Path,
    plan: dict,
    *,
    accepted_variant_label: str | None = None,
) -> tuple[Path, int]:
    ts = _iso_now()
    ledger_path = write_checks_ledger(
        project_root, plan,
        accepted_variant_label=accepted_variant_label,
        composed_at=ts,
    )
    n_defects = append_defects(project_root, plan, ts=ts)
    return ledger_path, n_defects
