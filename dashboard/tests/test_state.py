"""Tests for panel_grid_entries and group_findings — pure data transforms."""

from __future__ import annotations


def test_panel_grid_entries_orders_by_shotlist(make_project, server_module):
    root = make_project("ord", pages=2, panels_per_page=2)
    state = server_module.project_state(root)
    entries = server_module.panel_grid_entries(state)
    ids = [e["panel_id"] for e in entries]
    assert ids == ["p01-01", "p01-02", "p02-01", "p02-02"]


def test_panel_grid_entries_state_labels(make_project, server_module):
    root = make_project(
        "states",
        pages=1,
        panels_per_page=3,
        accepted={"p01-01"},  # only the first is accepted
    )
    # p01-03 has no folder at all → should show "missing"
    import shutil

    shutil.rmtree(root / "pages" / "panels" / "p01-03")

    state = server_module.project_state(root)
    entries = server_module.panel_grid_entries(state)
    by_id = {e["panel_id"]: e for e in entries}
    assert by_id["p01-01"]["state"] == "accepted"
    assert by_id["p01-02"]["state"] == "in_progress"
    assert by_id["p01-03"]["state"] == "missing"


def test_panel_grid_entries_flat_layout(make_project, server_module):
    root = make_project("flat", pages=1, panels_per_page=2, layout="flat")
    state = server_module.project_state(root)
    entries = server_module.panel_grid_entries(state)
    # Flat-layout panels are treated as accepted v1.
    assert all(e["state"] == "accepted" for e in entries)
    assert all(e["folder_name"] is not None for e in entries)


def test_group_findings_buckets_by_severity(server_module):
    payload = {
        "findings": [
            {"severity": "hard", "message": "x", "page": 1, "panel_id": "p01-01"},
            {"severity": "hard", "message": "y", "page": 2, "panel_id": None},
            {"severity": "soft", "message": "z", "page": None, "panel_id": None},
            {"severity": "info", "message": "i", "page": None, "panel_id": None},
        ]
    }
    grouped = server_module.group_findings(payload)
    assert grouped["counts"] == {"hard": 2, "soft": 1, "info": 1}
    assert grouped["total"] == 4
    assert grouped["error"] is None


def test_group_findings_propagates_error(server_module):
    grouped = server_module.group_findings({"error": "boom", "findings": []})
    assert grouped["error"] == "boom"
    assert grouped["total"] == 0
