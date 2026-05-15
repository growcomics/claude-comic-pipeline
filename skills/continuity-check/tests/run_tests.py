#!/usr/bin/env python3
"""
run_tests.py — Fixture-based test suite for rules_audit.py.

Each fixture is a folder under tests/fixtures/ containing:
  - shotlist.json: a synthetic shotlist (looks like a real project root)
  - expected.json: assertions about which findings should/shouldn't fire

expected.json schema:
  {
    "description": "...",
    "ignore_categories": ["asset", ...],  # categories of finding to drop entirely
    "expect_hard": [                       # findings that MUST appear as HARD
      {"category": "camera_variety", "message_contains": "same camera combo"},
      ...
    ],
    "expect_no_hard_in_categories": ["transformation_beats", ...],  # categories that MUST NOT have HARD
    "expect_no_hard_with_message": [       # specific HARD findings that MUST NOT appear
      {"category": "transformation_beats", "message_contains": "no setup beat"}
    ]
  }

Runs in under a second on the whole suite. Use this whenever you change a
rule in rules_audit.py to catch regressions before they cost generation
budget.

Usage:
  python tests/run_tests.py                      # run all fixtures
  python tests/run_tests.py failure-april-claudemade-shape    # one fixture
  python tests/run_tests.py --verbose            # show all findings per fixture

Exit codes:
  0 all pass
  1 one or more fixtures failed assertions
"""

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
RULES_AUDIT = SCRIPT_DIR.parent / "scripts" / "rules_audit.py"
FIXTURES_DIR = SCRIPT_DIR / "fixtures"

GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
DIM = "\033[2m"
RESET = "\033[0m"


@dataclass
class FixtureResult:
    name: str
    passed: bool
    failures: list[str]
    findings: list[dict]


def run_audit(project_dir: Path) -> list[dict]:
    """Invoke rules_audit.py --json and return the findings list."""
    result = subprocess.run(
        [sys.executable, str(RULES_AUDIT), "--project", str(project_dir), "--json"],
        capture_output=True,
        text=True,
    )
    if result.returncode not in (0, 1):
        raise RuntimeError(
            f"rules_audit.py crashed (exit {result.returncode}) on {project_dir}:\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
    payload = json.loads(result.stdout)
    return payload["findings"]


def check_fixture(fixture_dir: Path) -> FixtureResult:
    expected_path = fixture_dir / "expected.json"
    if not expected_path.exists():
        return FixtureResult(
            fixture_dir.name, False, [f"missing expected.json"], []
        )
    expected = json.loads(expected_path.read_text())
    findings = run_audit(fixture_dir)

    ignore = set(expected.get("ignore_categories", []))
    filtered = [f for f in findings if f["category"] not in ignore]

    failures: list[str] = []

    # 1. Each expect_hard must match at least one HARD finding.
    for spec in expected.get("expect_hard", []):
        cat = spec["category"]
        needle = spec["message_contains"]
        match = any(
            f["severity"] == "hard"
            and f["category"] == cat
            and needle in f["message"]
            for f in filtered
        )
        if not match:
            failures.append(
                f"expected HARD finding not present: category={cat}, message_contains='{needle}'"
            )

    # 2. expect_no_hard_in_categories: zero HARD findings in those categories.
    for cat in expected.get("expect_no_hard_in_categories", []):
        bad = [f for f in filtered if f["severity"] == "hard" and f["category"] == cat]
        if bad:
            sample = "; ".join(f["message"][:80] for f in bad[:2])
            failures.append(
                f"unexpected HARD finding(s) in category '{cat}' ({len(bad)} total): {sample}"
            )

    # 3. expect_no_hard_with_message: specific HARDs that must NOT appear.
    for spec in expected.get("expect_no_hard_with_message", []):
        cat = spec["category"]
        needle = spec["message_contains"]
        bad = [
            f for f in filtered
            if f["severity"] == "hard"
            and f["category"] == cat
            and needle in f["message"]
        ]
        if bad:
            failures.append(
                f"unexpected HARD finding present: category={cat}, message_contains='{needle}'"
            )

    return FixtureResult(fixture_dir.name, not failures, failures, findings)


def format_result(r: FixtureResult, verbose: bool) -> str:
    head = f"{GREEN}PASS{RESET}" if r.passed else f"{RED}FAIL{RESET}"
    lines = [f"  {head}  {r.name}"]
    if not r.passed:
        for fail in r.failures:
            lines.append(f"        {RED}✗{RESET} {fail}")
    if verbose:
        non_asset = [f for f in r.findings if f["category"] != "asset"]
        for f in non_asset:
            color = RED if f["severity"] == "hard" else YELLOW if f["severity"] == "soft" else DIM
            lines.append(f"        {color}{f['severity']:<4}{RESET} {f['category']:<22} {f['message'][:90]}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("fixture", nargs="?", help="Run a single fixture (folder name under fixtures/)")
    ap.add_argument("--verbose", "-v", action="store_true", help="Show all findings per fixture")
    args = ap.parse_args()

    if not RULES_AUDIT.exists():
        sys.exit(f"rules_audit.py not found at {RULES_AUDIT}")
    if not FIXTURES_DIR.exists():
        sys.exit(f"fixtures dir not found at {FIXTURES_DIR}")

    if args.fixture:
        target = FIXTURES_DIR / args.fixture
        if not target.is_dir():
            sys.exit(f"fixture not found: {target}")
        fixtures = [target]
    else:
        fixtures = sorted(p for p in FIXTURES_DIR.iterdir() if p.is_dir())

    print(f"\nRunning {len(fixtures)} fixture(s) from {FIXTURES_DIR}\n")

    results = [check_fixture(f) for f in fixtures]
    for r in results:
        print(format_result(r, args.verbose))

    passed = sum(1 for r in results if r.passed)
    failed = len(results) - passed
    summary_color = GREEN if failed == 0 else RED
    print(f"\n{summary_color}{passed}/{len(results)} passed{RESET}")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
