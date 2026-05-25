#!/usr/bin/env python3
"""Vision-audit dispatcher — the missing post-render layer.

For each accepted panel it: loads the rendered image + the panel's checks.json,
finds every applicable rule that ships a `vision_rubric`, asks a vision model to
judge the image against that rubric + the canonical refs, and writes the verdict
back into checks.json under rules[RULE].post_render.{status,reason}. Rolls a
per-rule defect row into defects.jsonl for any post_render fail.

This is REPORT-ONLY by default. It never regenerates. With --emit-retry it also
prints retry_panel.py-style recommendations for the failures; it still does not
execute them. Auto-regen (phase 8) is intentionally NOT wired here — turning it
on should be a deliberate, separate step because it spends generation credits.

Usage:
    python3 audit_panels.py <project_root>                 # audit all accepted panels
    python3 audit_panels.py <project_root> --panel p07-01  # one panel
    python3 audit_panels.py <project_root> --rule L11      # one rule across panels
    python3 audit_panels.py <project_root> --dry-run       # list what WOULD be checked, no API
    python3 audit_panels.py <project_root> --emit-retry    # also print retry recommendations

Requires: ANTHROPIC_API_KEY in env, and the `anthropic` package
(`pip install anthropic`). Without either, runs in --dry-run automatically and
says so, so it degrades safely instead of crashing.

The vision model call is isolated in `_vision_judge()` — swap the backend there
(Anthropic, a local model, a human-review queue) without touching the dispatch.
"""
from __future__ import annotations
import argparse
import base64
import json
import os
import sys
from pathlib import Path

# Make the rules registry + ledger writer importable regardless of CWD.
HERE = Path(__file__).resolve().parent
SKILL_ROOT = HERE.parent  # skills/comic-production
sys.path.insert(0, str(SKILL_ROOT))
sys.path.insert(0, str(HERE))

try:
    from rules._registry import RULE_INSTANCES
except Exception as e:  # pragma: no cover - import diagnostics
    print(f"error: cannot import rules registry from {SKILL_ROOT}: {e}")
    sys.exit(2)

VALID = {"pass", "fail", "pending", "skipped", "blocked", "n/a", "refused"}

# Auto-regen policy modes. Mirrors `policies.regeneration` in
# production-config.schema.json; controls what happens to failed rules at the
# end of an audit run. The audit itself is always report-only — this policy
# governs the FOLLOW-UP step.
POLICY_MODES = {"never", "batch-end", "auto-on-hard", "halt-on-hard"}
DEFAULT_POLICY = "batch-end"


def _read_policy(project_root: Path) -> tuple[str, int, str]:
    """Return (mode, max_retries, retry_strategy) from production-config.json
    if present, else defaults. Never raises — bad config silently degrades to
    defaults so an audit run isn't blocked by config issues."""
    cfg = project_root / "production-config.json"
    if not cfg.is_file():
        return (DEFAULT_POLICY, 2, "same-prompt-new-seed")
    try:
        data = json.loads(cfg.read_text())
        block = (((data.get("policies") or {}).get("post_render_audit")) or {})
        mode = block.get("mode") or DEFAULT_POLICY
        if mode not in POLICY_MODES:
            mode = DEFAULT_POLICY
        return (mode, int(block.get("max_retries_per_panel", 2)),
                block.get("retry_strategy") or "same-prompt-new-seed")
    except Exception:
        return (DEFAULT_POLICY, 2, "same-prompt-new-seed")


# --------------------------------------------------------------------------- #
# Panel / image resolution — mirrors next_panel.py's accepted-state conventions
# --------------------------------------------------------------------------- #
def _ledger_dir(panels_root: Path, pid: str) -> Path:
    """checks.json lives in panel-<id>/ (the subfolder convention)."""
    return panels_root / f"panel-{pid}"


def _accepted_image(panels_root: Path, pid: str) -> Path | None:
    """Find the accepted render. Priority mirrors next_panel.detect_state:
    panel-<id>/_accepted.txt -> v*_accepted.png -> flat <id>.{png,jpg,jpeg}."""
    folder = panels_root / f"panel-{pid}"
    marker = folder / "_accepted.txt"
    if marker.exists():
        label = marker.read_text().strip()
        for ext in (".png", ".jpg", ".jpeg"):
            cand = folder / f"{label}{ext}"
            if cand.exists():
                return cand
    suffix = sorted(folder.glob("v*_accepted.*"))
    if suffix:
        return suffix[-1]
    for ext in (".png", ".jpg", ".jpeg"):
        flat = panels_root / f"{pid}{ext}"
        if flat.exists():
            return flat
    return None


def _canonical_refs(project_root: Path, limit: int = 3) -> list[Path]:
    """Best-effort: a couple of character face cards as identity anchors for the
    judge. Not exhaustive — the rubric does most of the work."""
    refs: list[Path] = []
    chars = project_root / "references" / "characters"
    if chars.is_dir():
        for cdir in sorted(chars.iterdir()):
            for name in ("face-card.png", "face-card.jpg", "face.png", "face.jpg"):
                p = cdir / name
                if p.exists():
                    refs.append(p)
                    break
            if len(refs) >= limit:
                break
    return refs


def _b64(p: Path) -> tuple[str, str]:
    media = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}.get(
        p.suffix.lower().lstrip("."), "image/png")
    return base64.standard_b64encode(p.read_bytes()).decode(), media


# --------------------------------------------------------------------------- #
# Vision backend — the only model-specific code. Swap freely.
# --------------------------------------------------------------------------- #
def _vision_judge(rubric: str, image: Path, refs: list[Path]) -> tuple[str, str]:
    """Return (status, reason). Asks the model to answer the rubric as PASS/FAIL
    with a one-line reason. Isolated so the rest of the script is backend-free."""
    try:
        import anthropic
    except ImportError:
        return ("pending", "anthropic package not installed — audit skipped")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return ("pending", "ANTHROPIC_API_KEY not set — audit skipped")

    content: list[dict] = []
    img_b64, img_media = _b64(image)
    content.append({"type": "text", "text": "PANEL TO JUDGE:"})
    content.append({"type": "image", "source": {
        "type": "base64", "media_type": img_media, "data": img_b64}})
    for r in refs:
        rb64, rmedia = _b64(r)
        content.append({"type": "text", "text": f"REFERENCE ({r.parent.name}):"})
        content.append({"type": "image", "source": {
            "type": "base64", "media_type": rmedia, "data": rb64}})
    content.append({"type": "text", "text": (
        f"{rubric}\n\n"
        "Answer in this exact format, nothing else:\n"
        "VERDICT: PASS or FAIL\n"
        "REASON: <one sentence>")})

    try:
        client = anthropic.Anthropic()
        resp = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=200,
            messages=[{"role": "user", "content": content}],
        )
        text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
    except Exception as e:
        return ("pending", f"vision call failed: {e}")

    verdict, reason = "pending", text.strip().replace("\n", " ")[:300]
    for line in text.splitlines():
        u = line.upper()
        if u.startswith("VERDICT:"):
            verdict = "fail" if "FAIL" in u else ("pass" if "PASS" in u else "pending")
        elif u.startswith("REASON:"):
            reason = line.split(":", 1)[1].strip()
    return (verdict, reason)


# --------------------------------------------------------------------------- #
# Dispatch
# --------------------------------------------------------------------------- #
def _rules_with_rubrics(rule_filter: str | None):
    out = []
    for r in RULE_INSTANCES:
        rubric = getattr(r, "vision_rubric", None)
        if not rubric:
            continue
        if rule_filter and r.id != rule_filter:
            continue
        out.append((r.id, rubric))
    return out


def audit_panel(project_root: Path, pid: str, rules, dry_run: bool):
    panels_root = project_root / "pages" / "panels"
    ledger_path = _ledger_dir(panels_root, pid) / "checks.json"
    if not ledger_path.exists():
        return {"panel": pid, "status": "no-ledger", "results": []}
    image = _accepted_image(panels_root, pid)
    if image is None:
        return {"panel": pid, "status": "no-image", "results": []}

    ledger = json.loads(ledger_path.read_text())
    refs = _canonical_refs(project_root)
    results = []
    skipped = []  # (rid, why) — visible in --verbose / summary, not per-panel noise

    for rid, rubric in rules:
        entry = ledger.get("rules", {}).get(rid)
        if entry is None:
            skipped.append((rid, "not in ledger"))
            continue
        # Vision-audit is a verifier of pre-render-PASSED compositions. If the
        # rule didn't fire, or pre-render didn't pass, an image-side verdict
        # adds no signal — and a live run wastes one API call per rule per
        # panel. Only audit when applied=True AND pre_render.status == "pass".
        if not entry.get("applied"):
            skipped.append((rid, "did not apply"))
            continue
        pre_status = (entry.get("pre_render") or {}).get("status")
        if pre_status != "pass":
            skipped.append((rid, f"pre_render={pre_status or 'missing'}"))
            continue
        if dry_run:
            results.append((rid, "would-check", rubric[:60]))
            continue
        status, reason = _vision_judge(rubric, image, refs)
        if status not in VALID:
            status = "pending"
        entry.setdefault("post_render", {})
        entry["post_render"]["status"] = status
        entry["post_render"]["reason"] = reason
        results.append((rid, status, reason))

    if not dry_run:
        ledger_path.write_text(json.dumps(ledger, indent=2))
        # roll fails into defects.jsonl
        import time
        ts = time.strftime("%Y-%m-%dT%H:%M:%S")
        defects = project_root / "defects.jsonl"
        with defects.open("a") as f:
            for rid, status, reason in results:
                if status == "fail":
                    f.write(json.dumps({
                        "ts": ts, "panel_id": pid, "rule_id": rid,
                        "stage": "post_render", "reason": reason}) + "\n")

    return {"panel": pid, "status": "audited", "image": str(image),
            "results": results, "skipped": skipped}


def all_panels(project_root: Path) -> list[str]:
    panels_root = project_root / "pages" / "panels"
    pids = set()
    if panels_root.is_dir():
        for child in panels_root.iterdir():
            if child.is_dir() and child.name.startswith("panel-"):
                pids.add(child.name[len("panel-"):])
            elif child.suffix.lower() in (".png", ".jpg", ".jpeg"):
                pids.add(child.stem)
    return sorted(pids)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project_root")
    ap.add_argument("--panel", help="audit a single panel id (e.g. p07-01)")
    ap.add_argument("--rule", help="restrict to one rule id (e.g. L11)")
    ap.add_argument("--dry-run", action="store_true",
                    help="list what would be checked; no API calls")
    ap.add_argument("--emit-retry", action="store_true",
                    help="also print retry recommendations for fails (does not execute)")
    ap.add_argument("--show-skipped", action="store_true",
                    help="list every skipped rule per panel (off by default — usually noise)")
    ap.add_argument("--policy",
                    help=f"override the post_render_audit mode (one of: {', '.join(sorted(POLICY_MODES))}). "
                         "Default reads production-config.json policies.post_render_audit.mode, "
                         f"falling back to {DEFAULT_POLICY!r}.")
    args = ap.parse_args()

    root = Path(args.project_root).expanduser()
    rules = _rules_with_rubrics(args.rule)
    if not rules:
        print(f"no rules with vision_rubric matched (filter={args.rule!r})")
        return 1

    # Degrade safely: no key / no package -> force dry-run with a clear notice.
    dry = args.dry_run
    if not dry:
        try:
            import anthropic  # noqa: F401
            if not os.environ.get("ANTHROPIC_API_KEY"):
                print("notice: ANTHROPIC_API_KEY not set — running --dry-run instead.\n")
                dry = True
        except ImportError:
            print("notice: anthropic package not installed — running --dry-run instead.")
            print("        `pip install anthropic` then re-run to do the real audit.\n")
            dry = True

    pids = [args.panel] if args.panel else all_panels(root)
    if not pids:
        print(f"no panels found under {root}/pages/panels/")
        return 1

    policy_mode, policy_max_retries, policy_strategy = _read_policy(root)
    if args.policy:
        if args.policy not in POLICY_MODES:
            print(f"error: --policy must be one of: {', '.join(sorted(POLICY_MODES))}")
            return 2
        policy_mode = args.policy
    print(f"# Vision audit — {root.name}")
    print(f"rules with rubrics: {', '.join(r for r, _ in rules)}")
    print(f"mode: {'DRY-RUN (no API)' if dry else 'LIVE'} | panels: {len(pids)} | "
          f"policy: {policy_mode} (max_retries={policy_max_retries}, strategy={policy_strategy})\n")

    n_fail = n_pass = n_pending = n_skipped = n_would_check = 0
    retry_lines = []
    failures: list[tuple[str, str, str, str]] = []  # (panel_id, rule_id, reason, image_path)
    for pid in pids:
        out = audit_panel(root, pid, rules, dry)
        if out["status"] != "audited":
            print(f"{pid}: {out['status']}")
            continue
        print(f"{pid}  ({Path(out['image']).name})")
        for rid, status, reason in out["results"]:
            mark = {"pass": "ok ", "fail": "XX ", "would-check": "?? "}.get(status, ".. ")
            print(f"   {mark}{rid:<14} {status:<11} {reason}")
            if status == "fail":
                n_fail += 1
                retry_lines.append(f"   {pid} {rid}: see retry_panel.py {root.name} {pid} --rule {rid}")
                failures.append((pid, rid, reason, out["image"]))
            elif status == "pass":
                n_pass += 1
            elif status == "pending":
                n_pending += 1
            elif status == "would-check":
                n_would_check += 1
        panel_skipped = out.get("skipped", [])
        n_skipped += len(panel_skipped)
        if panel_skipped:
            if args.show_skipped:
                for rid, why in panel_skipped:
                    print(f"   -- {rid:<14} skipped     {why}")
            else:
                print(f"   ({len(panel_skipped)} rule(s) skipped — pass --show-skipped to list)")
        print()

    if dry:
        print(f"DRY-RUN summary: {n_would_check} would-check (audit cost), "
              f"{n_skipped} skipped (no signal)")
    else:
        print(f"summary: {n_pass} pass, {n_fail} fail, {n_pending} pending, {n_skipped} skipped")
    if args.emit_retry and retry_lines and not dry:
        print("\nretry recommendations (NOT executed):")
        print("\n".join(retry_lines))

    # Policy follow-up: write regen-queue.md when there are real failures and
    # mode requests a pickup artifact. Dry-runs and zero-fail runs never emit.
    if failures and not dry and policy_mode in ("batch-end", "auto-on-hard", "halt-on-hard"):
        queue_path = root / "regen-queue.md"
        import time as _time
        ts = _time.strftime("%Y-%m-%dT%H:%M:%S")
        lines = [
            f"# Regeneration queue — vision audit ({ts})",
            "",
            f"Generated by `audit_panels.py` per policy `{policy_mode}` "
            f"(max_retries={policy_max_retries}, strategy={policy_strategy}).",
            "",
            f"{len(failures)} panel/rule pair(s) failed post-render vision verification. "
            "Each row below is a candidate for re-rendering. The audit itself "
            "never re-renders — execution is the runner's job (or yours, via "
            "`retry_panel.py` / a manual next_panel.py invocation).",
            "",
            "| panel | rule | reason | image |",
            "|---|---|---|---|",
        ]
        for pid, rid, reason, img in failures:
            short_reason = (reason or "").replace("\n", " ").replace("|", "\\|")[:120]
            lines.append(f"| `{pid}` | `{rid}` | {short_reason} | `{img}` |")
        lines.append("")
        queue_path.write_text("\n".join(lines))
        print(f"\nwrote regen queue: {queue_path}  ({len(failures)} entries)")

    # halt-on-hard exits non-zero so a calling orchestrator (autopilot) can
    # detect the halt condition without parsing stdout. Other modes return 0
    # even on failures — the queue file is the signal.
    if failures and policy_mode == "halt-on-hard" and not dry:
        print("\nhalt: policy=halt-on-hard and post-render fails present — exiting 1")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
