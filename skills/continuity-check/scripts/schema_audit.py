#!/usr/bin/env python3
"""Validate every pipeline-stage artifact in a project against its JSON Schema.

Phase 1 of the Experiment-04 schema-contracts work (see
docs/experiments/04-schema-contracts/). Read-only: it does NOT modify any
artifact, NOT regenerate, NOT gate the autopilot. It just reports.

Usage
-----
    # One project
    python3 schema_audit.py projects/chun-li-test/

    # Every project under projects/
    python3 schema_audit.py --all

    # Arbitrary external project (anything with a shotlist.json or
    # production-config.json)
    python3 schema_audit.py ~/Documents/chunli-issue-1/

    # Machine-readable
    python3 schema_audit.py --all --json > report.json

Exit codes:
    0  all artifacts pass (or there were no artifacts to validate)
    1  at least one artifact failed validation
    2  usage error / schemas missing

The schemas live in $REPO_ROOT/schemas/. The validator finds them by walking
up from this script's location.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import jsonschema  # type: ignore
    from jsonschema import Draft7Validator
except ImportError:
    print("ERROR: jsonschema package not installed. `pip install jsonschema`",
          file=sys.stderr)
    sys.exit(2)


REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_DIR = REPO_ROOT / "schemas"

# Map of (artifact-name → on-disk relpath glob, schema-file)
ARTIFACTS: dict[str, tuple[str, str]] = {
    "production-config": ("production-config.json", "production-config.schema.json"),
    "shotlist": ("shotlist.json", "shotlist.schema.json"),
    "references_required": ("references_required.json", "references_required.schema.json"),
    # checks.json is per-panel; the glob is handled specially.
    "checks": ("pages/panels/panel-*/checks.json", "checks.schema.json"),
    # defects.jsonl is JSONL; we validate each line against defects.schema.json.
    "defects": ("defects.jsonl", "defects.schema.json"),
    # continuity-report.md is markdown; we extract sections first, then
    # validate the extracted dict against continuity-report.schema.json.
    "continuity-report": ("continuity-report.md", "continuity-report.schema.json"),
}


@dataclass
class ArtifactResult:
    artifact: str
    path: Path
    status: str  # "pass" | "fail" | "missing" | "skip"
    violations: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact": self.artifact,
            "path": str(self.path),
            "status": self.status,
            "violations": self.violations,
            "notes": self.notes,
        }


@dataclass
class ProjectResult:
    project: str
    root: Path
    artifacts: list[ArtifactResult] = field(default_factory=list)

    @property
    def summary(self) -> dict[str, int]:
        c = {"pass": 0, "fail": 0, "missing": 0, "skip": 0}
        for a in self.artifacts:
            c[a.status] = c.get(a.status, 0) + 1
        return c

    @property
    def has_fail(self) -> bool:
        return any(a.status == "fail" for a in self.artifacts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "project": self.project,
            "root": str(self.root),
            "summary": self.summary,
            "artifacts": [a.to_dict() for a in self.artifacts],
        }


def load_schema(name: str) -> dict[str, Any]:
    schema_path = SCHEMA_DIR / name
    if not schema_path.is_file():
        raise FileNotFoundError(f"schema not found: {schema_path}")
    return json.loads(schema_path.read_text())


def _format_violation(err: jsonschema.ValidationError) -> str:
    path = ".".join(str(p) for p in err.absolute_path) or "<root>"
    return f"{path}: {err.message}"


def validate_json_file(path: Path, schema: dict[str, Any]) -> list[str]:
    """Validate a JSON file; return list of violation strings (empty = pass)."""
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        return [f"<file>: not valid JSON: {e}"]
    validator = Draft7Validator(schema)
    return [_format_violation(e) for e in validator.iter_errors(data)]


def validate_jsonl_file(path: Path, schema: dict[str, Any]) -> list[str]:
    """Validate each line of a JSONL file; collect violations across rows."""
    violations: list[str] = []
    validator = Draft7Validator(schema)
    for lineno, line in enumerate(path.read_text().splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as e:
            violations.append(f"line {lineno}: not valid JSON: {e}")
            continue
        for err in validator.iter_errors(row):
            violations.append(f"line {lineno} :: {_format_violation(err)}")
    return violations


# ---------------------------------------------------------------------------
# continuity-report.md → dict extractor

_H1_RE = re.compile(r"^#\s+(.+?)\s*$")
_RUN_RE = re.compile(r"^_Run:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})_?\s*$")
_VERDICT_HDR_RE = re.compile(r"^##\s*Verdict\s*$", re.IGNORECASE)
_PER_PANEL_HDR_RE = re.compile(r"^##\s*Per-panel notes\s*$", re.IGNORECASE)
_VERDICT_LINE_RE = re.compile(r"\*\*([A-Z][A-Z\-]*)\*\*")
_H3_PANEL_RE = re.compile(r"^###\s+(p[0-9]+-[0-9]+)\b", re.IGNORECASE)
_CHECK_LINE_RE = re.compile(r"^-\s*([✓✗⚠✔✘✌❌x?!])\s*(.+?)\s*$")
# ✓ = U+2713, ✗ = U+2717, ⚠ = U+26A0, ✔ = U+2714, ✘ = U+2718.


def _classify_check_glyph(g: str) -> str:
    if g in ("✓", "✔"):
        return "pass"
    if g in ("⚠", "!"):
        return "warn"
    if g in ("✗", "✘", "❌", "x"):
        return "fail"
    return "warn"  # unknown glyph → treat as soft


def extract_continuity_report(md_path: Path) -> dict[str, Any]:
    """Parse continuity-report.md into a dict matching continuity-report.schema.json."""
    out: dict[str, Any] = {"title": "", "run_date": None, "verdict": "", "panels": []}
    text = md_path.read_text()
    lines = text.splitlines()

    in_verdict = False
    in_panels = False
    current_panel: dict[str, Any] | None = None

    for raw in lines:
        line = raw.rstrip()
        if not out["title"]:
            m = _H1_RE.match(line)
            if m:
                out["title"] = m.group(1).strip()
                continue
        if out["run_date"] is None:
            m = _RUN_RE.match(line)
            if m:
                out["run_date"] = m.group(1)
                continue
        if _VERDICT_HDR_RE.match(line):
            in_verdict = True
            in_panels = False
            continue
        if _PER_PANEL_HDR_RE.match(line):
            in_verdict = False
            in_panels = True
            continue

        if in_verdict and not out["verdict"]:
            m = _VERDICT_LINE_RE.search(line)
            if m:
                out["verdict"] = m.group(1).strip()

        if in_panels:
            m_panel = _H3_PANEL_RE.match(line)
            if m_panel:
                if current_panel:
                    out["panels"].append(current_panel)
                current_panel = {"panel_id": m_panel.group(1).lower(), "checks": []}
                continue
            if current_panel is not None:
                m_check = _CHECK_LINE_RE.match(line)
                if m_check:
                    current_panel["checks"].append({
                        "status": _classify_check_glyph(m_check.group(1)),
                        "text": m_check.group(2).strip(),
                    })

    if current_panel:
        out["panels"].append(current_panel)
    return out


def validate_continuity_report(path: Path, schema: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Returns (violations, notes). Notes describe extraction outcomes."""
    notes: list[str] = []
    extracted = extract_continuity_report(path)
    notes.append(f"extracted {len(extracted['panels'])} panel sections, "
                 f"verdict={extracted.get('verdict') or '<unset>'}")
    validator = Draft7Validator(schema)
    violations = [_format_violation(e) for e in validator.iter_errors(extracted)]
    return violations, notes


# ---------------------------------------------------------------------------
# Per-project audit

def audit_project(project_root: Path) -> ProjectResult:
    pr = ProjectResult(project=project_root.name, root=project_root)

    # 1. production-config
    pc_path = project_root / "production-config.json"
    if pc_path.is_file():
        schema = load_schema(ARTIFACTS["production-config"][1])
        violations = validate_json_file(pc_path, schema)
        pr.artifacts.append(ArtifactResult(
            artifact="production-config",
            path=pc_path,
            status="pass" if not violations else "fail",
            violations=violations,
        ))
    else:
        pr.artifacts.append(ArtifactResult(
            artifact="production-config", path=pc_path, status="missing",
            notes=["production-config.json absent — project may be pre-briefing"],
        ))

    # 2. shotlist
    sl_path = project_root / "shotlist.json"
    if sl_path.is_file():
        schema = load_schema(ARTIFACTS["shotlist"][1])
        violations = validate_json_file(sl_path, schema)
        pr.artifacts.append(ArtifactResult(
            artifact="shotlist",
            path=sl_path,
            status="pass" if not violations else "fail",
            violations=violations,
        ))
    else:
        pr.artifacts.append(ArtifactResult(
            artifact="shotlist", path=sl_path, status="missing",
            notes=["shotlist.json absent — project may be pre-breakdown"],
        ))

    # 3. references_required
    rr_path = project_root / "references_required.json"
    if rr_path.is_file():
        schema = load_schema(ARTIFACTS["references_required"][1])
        violations = validate_json_file(rr_path, schema)
        # Dialect note: which version field is in use?
        notes = []
        try:
            d = json.loads(rr_path.read_text())
            if "schema_version" in d:
                notes.append("uses `schema_version` (canonical)")
            elif "version" in d:
                notes.append("uses `version` (legacy dialect — should migrate to `schema_version`)")
            else:
                notes.append("MISSING both `version` and `schema_version` — unversioned")
        except Exception:
            pass
        pr.artifacts.append(ArtifactResult(
            artifact="references_required",
            path=rr_path,
            status="pass" if not violations else "fail",
            violations=violations,
            notes=notes,
        ))
    else:
        pr.artifacts.append(ArtifactResult(
            artifact="references_required", path=rr_path, status="missing",
            notes=["references_required.json absent — projects without "
                   "transformation_metadata legitimately skip this artifact"],
        ))

    # 4. checks.json (per panel — glob)
    checks_glob = sorted(project_root.glob("pages/panels/panel-*/checks.json"))
    if checks_glob:
        schema = load_schema(ARTIFACTS["checks"][1])
        # Aggregate: one ArtifactResult covering all panels, with per-file
        # violations prefixed by the panel-id.
        aggregate_violations: list[str] = []
        passed = 0
        for cp in checks_glob:
            v = validate_json_file(cp, schema)
            if v:
                panel = cp.parent.name  # 'panel-pNN-MM'
                for line in v:
                    aggregate_violations.append(f"{panel}: {line}")
            else:
                passed += 1
        status = "pass" if not aggregate_violations else "fail"
        pr.artifacts.append(ArtifactResult(
            artifact="checks",
            path=project_root / "pages/panels",
            status=status,
            violations=aggregate_violations,
            notes=[f"{passed}/{len(checks_glob)} panel checks.json files pass"],
        ))
    else:
        pr.artifacts.append(ArtifactResult(
            artifact="checks", path=project_root / "pages/panels",
            status="missing",
            notes=["no per-panel checks.json on disk — either pre-render or "
                   "gitignored (pages/ is in .gitignore)"],
        ))

    # 5. defects.jsonl
    def_path = project_root / "defects.jsonl"
    if def_path.is_file():
        schema = load_schema(ARTIFACTS["defects"][1])
        violations = validate_jsonl_file(def_path, schema)
        n_rows = sum(1 for ln in def_path.read_text().splitlines() if ln.strip())
        pr.artifacts.append(ArtifactResult(
            artifact="defects",
            path=def_path,
            status="pass" if not violations else "fail",
            violations=violations,
            notes=[f"{n_rows} JSONL rows scanned"],
        ))
    else:
        pr.artifacts.append(ArtifactResult(
            artifact="defects", path=def_path, status="missing",
            notes=["defects.jsonl absent — either no defects logged or gitignored"],
        ))

    # 6. continuity-report.md
    cr_path = project_root / "continuity-report.md"
    if cr_path.is_file():
        schema = load_schema(ARTIFACTS["continuity-report"][1])
        violations, notes = validate_continuity_report(cr_path, schema)
        pr.artifacts.append(ArtifactResult(
            artifact="continuity-report",
            path=cr_path,
            status="pass" if not violations else "fail",
            violations=violations,
            notes=notes,
        ))
    else:
        pr.artifacts.append(ArtifactResult(
            artifact="continuity-report", path=cr_path, status="missing",
            notes=["continuity-report.md absent — pre-audit"],
        ))

    return pr


def discover_all_projects() -> list[Path]:
    """Find every project directory under projects/ in the repo."""
    base = REPO_ROOT / "projects"
    if not base.is_dir():
        return []
    return sorted(p for p in base.iterdir() if p.is_dir() and not p.name.startswith("."))


# ---------------------------------------------------------------------------
# Output formatting

GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
GRAY = "\033[90m"
BOLD = "\033[1m"
RESET = "\033[0m"


def _colorize(status: str, use_color: bool) -> str:
    if not use_color:
        return status.upper()
    if status == "pass":
        return f"{GREEN}PASS{RESET}"
    if status == "fail":
        return f"{RED}FAIL{RESET}"
    if status == "missing":
        return f"{GRAY}MISSING{RESET}"
    return f"{YELLOW}SKIP{RESET}"


def print_human(results: list[ProjectResult], use_color: bool = True) -> None:
    total = {"pass": 0, "fail": 0, "missing": 0, "skip": 0}
    fail_projects: list[str] = []
    for pr in results:
        title = f"{BOLD}{pr.project}{RESET}" if use_color else pr.project
        print(f"\n=== {title} ({pr.root}) ===")
        for a in pr.artifacts:
            total[a.status] = total.get(a.status, 0) + 1
            label = _colorize(a.status, use_color)
            print(f"  [{label}] {a.artifact:<22} {a.path.relative_to(pr.root) if a.path.is_relative_to(pr.root) else a.path}")
            for n in a.notes:
                print(f"           - note: {n}")
            for v in a.violations:
                print(f"           - {v}")
        if pr.has_fail:
            fail_projects.append(pr.project)
    print(f"\n{BOLD if use_color else ''}Summary{RESET if use_color else ''}: "
          f"pass={total['pass']} fail={total['fail']} "
          f"missing={total['missing']} skip={total['skip']}")
    if fail_projects:
        print(f"Projects with at least one FAIL: {', '.join(fail_projects)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("project", nargs="?", help="path to a single project root")
    g.add_argument("--all", action="store_true",
                   help="audit every project under projects/")
    parser.add_argument("--external", nargs="*", default=[],
                        help="extra external project roots to audit "
                             "(any directory containing shotlist.json or "
                             "production-config.json)")
    parser.add_argument("--json", action="store_true",
                        help="emit JSON instead of human-readable text")
    parser.add_argument("--no-color", action="store_true",
                        help="disable ANSI colors")
    args = parser.parse_args()

    if not SCHEMA_DIR.is_dir():
        print(f"ERROR: schemas/ not found at {SCHEMA_DIR}", file=sys.stderr)
        return 2

    project_roots: list[Path] = []
    if args.all:
        project_roots.extend(discover_all_projects())
    elif args.project:
        project_roots.append(Path(args.project).expanduser().resolve())
    for ext in args.external:
        project_roots.append(Path(ext).expanduser().resolve())

    if not project_roots:
        print("no projects to audit", file=sys.stderr)
        return 2

    results = [audit_project(pr) for pr in project_roots]

    if args.json:
        payload = {
            "schema_dir": str(SCHEMA_DIR),
            "projects": [r.to_dict() for r in results],
            "exit_code": 1 if any(r.has_fail for r in results) else 0,
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print_human(results, use_color=not args.no_color and sys.stdout.isatty())

    return 1 if any(r.has_fail for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
