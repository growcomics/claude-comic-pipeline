#!/usr/bin/env python3
"""Test the runner_core panel loop end-to-end with a mocked backend.

Verifies:
  - Panels processed in order
  - State.json updated atomically per panel
  - Picked variant copied to canonical accepted location
  - Halt reasons set correctly
  - Resume from partial state skips already-accepted panels
"""

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

# Add runners to path
sys.path.insert(0, str(Path(__file__).parent.parent / "runners"))

from runner_core import (
    GenerationResult,
    HaltReason,
    RunOptions,
    RunnerBackend,
    load_state,
    run,
)


class MockBackend(RunnerBackend):
    """Generates fake PNGs of varying sizes so the heuristic picker works."""

    def __init__(self, refuse_on_panel: str | None = None, healthy: bool = True):
        self.refuse_on_panel = refuse_on_panel
        self.healthy = healthy
        self.submitted: list[str] = []

    def check_health(self) -> tuple[bool, str]:
        return (self.healthy, "mock OK" if self.healthy else "mock unhealthy")

    def submit_panel(self, plan, project_root, count, timeout_s):
        panel_id = plan["next_panel"]["panel_id"]
        self.submitted.append(panel_id)
        if panel_id == self.refuse_on_panel:
            return GenerationResult(
                variant_paths=[], raw_metadata={}, refusal=True,
                refusal_reason="mock content policy refusal",
            )
        out_dir = project_root / "pages" / "panels" / panel_id
        out_dir.mkdir(parents=True, exist_ok=True)
        paths = []
        for i in range(1, count + 1):
            p = out_dir / f"v{i}.png"
            # Each variant a different size so heuristic picker can differentiate
            p.write_bytes(os.urandom(1000 + i * 200))
            paths.append(p)
        return GenerationResult(variant_paths=paths, raw_metadata={}, refusal=False)

    def close(self):
        pass


def write_minimal_project(root: Path):
    """Create a minimal project with shotlist.json + config so the loop runs."""
    config = {
        "version": 2,
        "project": {"name": "test", "root": str(root)},
        "transformation_type": "fmg",
        "platform": "flow",
        "mandatory_rules": {"active": [1, 2, 3], "extra_lines": []},
        "policies": {"stage3_gate": "auto", "regeneration": "batch-end", "posting": "never"},
        "halt_conditions": {
            "content_policy_refusal": True, "missing_ref_guardrail": True,
            "environmental_failure": True, "script_ambiguity": True,
        },
        "generation": {
            "max_retries_per_panel": 3,
            "on_all_bad": "halt",  # halt for predictable test
            "pick_variant": "claude",
            "variant_picker": "heuristic",  # no API call in tests
        },
    }
    (root / "production-config.json").write_text(json.dumps(config))

    # Minimal shotlist with 3 panels across 2 pages
    shotlist = {
        "pages": [
            {
                "page_number": 1,
                "panels": [
                    {"panel_id": "p01-01", "camera": "wide-establish",
                     "characters": [], "action": "establish",
                     "location": "loc-a"},
                    {"panel_id": "p01-02", "camera": "front-full",
                     "characters": [], "action": "speak",
                     "location": "loc-a"},
                ],
            },
            {
                "page_number": 2,
                "panels": [
                    {"panel_id": "p02-01", "camera": "ecu-face",
                     "characters": [], "action": "react",
                     "location": "loc-a"},
                ],
            },
        ],
    }
    (root / "shotlist.json").write_text(json.dumps(shotlist))


# Create a minimal next_panel.py stub that mirrors the real one's interface
NEXT_PANEL_STUB = r'''#!/usr/bin/env python3
"""Stub next_panel.py for testing. Walks shotlist.json + pages/panels/."""
import argparse, json, sys
from pathlib import Path

def main():
    p = argparse.ArgumentParser()
    p.add_argument("project_root")
    p.add_argument("--as-json", action="store_true")
    p.add_argument("--config", default=None)
    args = p.parse_args()

    root = Path(args.project_root)
    sl = json.loads((root / "shotlist.json").read_text())
    panels_dir = root / "pages" / "panels"

    accepted = []
    next_p = None
    next_page = None
    for page in sl["pages"]:
        for panel in page["panels"]:
            pid = panel["panel_id"]
            if (panels_dir / f"{pid}.png").is_file():
                accepted.append({"panel_id": pid, "page_number": page["page_number"]})
            elif next_p is None:
                next_p = panel
                next_page = page["page_number"]

    if next_p is None:
        out = {"project_root": str(root), "next_panel": None,
               "message": "all accepted", "accepted_count": len(accepted)}
        print(json.dumps(out))
        return

    aspect = {"wide-establish": "16:9", "front-full": "3:4", "ecu-face": "1:1"}.get(
        next_p["camera"], "3:4")
    plan = {
        "project_root": str(root),
        "next_panel": next_p,
        "page_number": next_page,
        "aspect": aspect,
        "count": 4,
        "stage_change": False,
        "anchor_panel_id": None,
        "accepted_count": len(accepted),
        "remaining_count": 1,
        "refs_to_attach_in_order": [],
        "composed_prompt": f"Mock prompt for {next_p['panel_id']}: {next_p['action']}",
    }
    print(json.dumps(plan))

if __name__ == "__main__":
    main()
'''


def test_full_loop():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        write_minimal_project(root)
        stub_path = root / "next_panel_stub.py"
        stub_path.write_text(NEXT_PANEL_STUB)
        os.chmod(stub_path, 0o755)

        backend = MockBackend()
        opts = RunOptions(
            project_root=root,
            config=json.loads((root / "production-config.json").read_text()),
            next_panel_script=stub_path,
            backend=backend,
        )
        final = run(opts)

        assert final.halt_reason is None, f"unexpected halt: {final.halt_reason}"
        assert backend.submitted == ["p01-01", "p01-02", "p02-01"], (
            f"unexpected order: {backend.submitted}"
        )
        # All 3 panels should be accepted
        assert len(final.panels) == 3
        for pid in ["p01-01", "p01-02", "p02-01"]:
            ps = final.panels[pid]
            assert ps.state == "accepted", f"{pid}: {ps.state}"
            assert ps.picked_variant in (1, 2, 3, 4)
            # The accepted PNG should be at the canonical location
            assert (root / "pages" / "panels" / f"{pid}.png").is_file()
        print("OK: full loop")


def test_refusal_halt():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        write_minimal_project(root)
        stub_path = root / "next_panel_stub.py"
        stub_path.write_text(NEXT_PANEL_STUB)
        os.chmod(stub_path, 0o755)

        # Refuse on the second panel
        backend = MockBackend(refuse_on_panel="p01-02")
        opts = RunOptions(
            project_root=root,
            config=json.loads((root / "production-config.json").read_text()),
            next_panel_script=stub_path,
            backend=backend,
        )
        final = run(opts)

        assert final.halt_reason == HaltReason.CONTENT_POLICY_REFUSAL
        assert final.halt_panel_id == "p01-02"
        # First panel should be accepted, second halted, third never attempted
        assert final.panels["p01-01"].state == "accepted"
        assert backend.submitted == ["p01-01", "p01-02"]
        # state.json should persist
        s = load_state(root)
        assert s.halt_reason == HaltReason.CONTENT_POLICY_REFUSAL
        print("OK: refusal halt")


def test_resume():
    """After a halt, re-running picks up where we left off."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        write_minimal_project(root)
        stub_path = root / "next_panel_stub.py"
        stub_path.write_text(NEXT_PANEL_STUB)
        os.chmod(stub_path, 0o755)

        # First run: refuse on second
        backend1 = MockBackend(refuse_on_panel="p01-02")
        opts1 = RunOptions(
            project_root=root,
            config=json.loads((root / "production-config.json").read_text()),
            next_panel_script=stub_path,
            backend=backend1,
        )
        run(opts1)
        assert backend1.submitted == ["p01-01", "p01-02"]

        # User "fixes" the issue; clear halt-reason from state.json
        s = load_state(root)
        s.halt_reason = None
        s.halt_panel_id = None
        from runner_core import save_state
        save_state(root, s)

        # Second run: no refusal this time, should resume from p01-02
        backend2 = MockBackend()
        opts2 = RunOptions(
            project_root=root,
            config=json.loads((root / "production-config.json").read_text()),
            next_panel_script=stub_path,
            backend=backend2,
        )
        final = run(opts2)
        assert final.halt_reason is None
        # The next_panel.py stub auto-skips accepted panels, so resume starts
        # from p01-02
        assert backend2.submitted == ["p01-02", "p02-01"]
        print("OK: resume after halt")


def test_health_fail():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        write_minimal_project(root)
        stub_path = root / "next_panel_stub.py"
        stub_path.write_text(NEXT_PANEL_STUB)
        os.chmod(stub_path, 0o755)

        backend = MockBackend(healthy=False)
        opts = RunOptions(
            project_root=root,
            config=json.loads((root / "production-config.json").read_text()),
            next_panel_script=stub_path,
            backend=backend,
        )
        final = run(opts)
        assert final.halt_reason == HaltReason.AUTH_EXPIRED
        assert backend.submitted == []  # never attempted
        print("OK: health-fail halt")


if __name__ == "__main__":
    test_full_loop()
    test_refusal_halt()
    test_resume()
    test_health_fail()
    print("\nAll tests passed.")
