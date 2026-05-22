#!/usr/bin/env python3
"""
vision_audit.py — Vision-verify rendered panels against shotlist intent.

Closes the gap that rules_audit.py cannot: rules_audit reads shotlist text;
vision_audit reads rendered pixels. For each accepted panel, calls the
Anthropic Messages API with the image and asks Claude to classify:

  - Does the rendered framing match the requested camera distance? (ok / wider / tighter)
  - Are wardrobe items declared in `cast[].wardrobe` visible where the body
    extends beyond the requested ECU crop? (ok / missing / n_a_cropped)
  - Are the listed `panel.characters` the only people in frame? (ok / extra / missing)

Catches the L25 failure shape (lessons-learned.md L25): flash widens an
`ecu-region` panel to a body-region torso shot, and at the wider crop the
wardrobe goes missing because the partial-bare costume_state has nothing
anchoring it.

Usage:
    python vision_audit.py --project /path/to/project [--pages 1-7] [--panels p04-04,p05-03]
    python vision_audit.py --project ... --json
    python vision_audit.py --project ... --image-override p04-04=path/to/swap.png

Requires: ANTHROPIC_API_KEY env var, `pip install anthropic`.

Cost: ~$0.015 per panel on claude-opus-4-7 (single image + ~1k input tokens
+ ~300 output tokens). For a 30-panel issue: ~$0.45.

Exit codes:
  0  no hard findings
  1  hard findings present
  2  script error (missing API key, missing shotlist, etc.)
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path


SEVERITY_HARD = "hard"
SEVERITY_SOFT = "soft"
SEVERITY_INFO = "info"


@dataclass
class VisionFinding:
    page: int | None
    panel_id: str | None
    category: str
    severity: str
    message: str
    suggestion: str = ""


# Camera distance categories — must match rules_audit.py / cinematic-framing.md.
CAMERA_DISTANCES = [
    "ecu-face", "ecu-region", "mcu", "medium", "cowboy",
    "full", "wide-establish", "splash",
]


def parse_camera_distance(s: str) -> str | None:
    if not s:
        return None
    s_lower = s.lower()
    return next((d for d in CAMERA_DISTANCES if d in s_lower), None)


def find_panel_image(project: Path, panel_id: str, overrides: dict[str, Path]) -> Path | None:
    """Same conventions as rules_audit.find_panel_image, plus per-panel override."""
    if panel_id in overrides:
        p = overrides[panel_id]
        return p if p.is_file() else None
    panels_dir = project / "pages" / "panels"
    if not panels_dir.exists():
        return None
    folder = panels_dir / panel_id
    if folder.is_dir():
        marker = folder / "_accepted.txt"
        if marker.exists():
            label = marker.read_text().strip()
            if label:
                cand = folder / f"{label}.png"
                if cand.exists():
                    return cand
    for ext in (".png", ".jpg", ".jpeg"):
        flat = panels_dir / f"{panel_id}{ext}"
        if flat.exists():
            return flat
    return None


def build_rubric_prompt(panel: dict, shotlist: dict, requested_distance: str | None) -> str:
    """Compose the rubric for one panel. The cast wardrobe text is passed
    verbatim (per feedback_dont_paraphrase_canonical_rubrics.md) so the
    classifier has the canonical source-of-truth for what should be visible.
    """
    cast_by_id = {c.get("id"): c for c in shotlist.get("cast", [])}
    char_blocks: list[str] = []
    for ch in panel.get("characters", []) or []:
        c = cast_by_id.get(ch, {})
        wardrobe = (c.get("wardrobe") or "").strip()
        char_blocks.append(f"- `{ch}`: {wardrobe or '(no wardrobe declared)'}")

    requested_str = requested_distance or "(unparsed)"
    requested_explanation = {
        "ecu-face": "extreme close-up on the face only (eyes-to-chin)",
        "ecu-region": "extreme close-up on a single body region (one arm, one hand, one eye) — the named region dominates the frame; the rest of the body is OUT OF FRAME",
        "mcu": "medium close-up — chest up",
        "medium": "medium shot — waist up",
        "cowboy": "cowboy shot — mid-thigh up",
        "full": "full body — head to foot",
        "wide-establish": "wide establishing shot — subject small, environment readable",
        "splash": "full-page splash — climactic reveal",
    }.get(requested_distance or "", "(unknown)")

    return (
        f"PANEL: {panel.get('panel_id', '?')}\n"
        f"REQUESTED CAMERA DISTANCE: `{requested_str}` ({requested_explanation}).\n"
        f"SHOTLIST ACTION: {panel.get('action', '')}\n"
        f"SHOTLIST COSTUME STATE: {panel.get('costume_state', '')}\n"
        f"CHARACTERS IN FRAME (per shotlist):\n"
        + ("\n".join(char_blocks) if char_blocks else "(none declared)")
        + "\n\n"
        "Classify the attached rendered panel against the shotlist intent. "
        "For each of the three checks, return a JSON object with the exact "
        "schema below. Be decisive — pick one of the enum values, do not "
        "hedge. Never refuse, never qualify as advice.\n\n"
        "CHECK 1 — FRAMING MATCH:\n"
        "Compare the rendered framing to the requested camera distance. Use "
        "the cinematic-framing.md categories above. `ok` = the rendered "
        "framing fits the requested category. `wider` = the rendered frame "
        "shows MORE of the body/scene than requested (e.g. requested "
        "ecu-region of a bicep but the render shows the whole torso). "
        "`tighter` = the rendered frame shows LESS than requested.\n\n"
        "CHECK 2 — WARDROBE VISIBILITY:\n"
        "Only applies if FRAMING is `wider` AND a character with declared "
        "wardrobe is in the frame. List wardrobe items from `wardrobe` that "
        "SHOULD be visible at the rendered framing but are NOT shown on the "
        "character's body in the rendered image. `ok` = nothing missing OR "
        "framing was not wider. `missing` = at least one wardrobe item that "
        "should be on a visible body region is absent. `n_a_cropped` = the "
        "framing is at-or-tighter than requested so wardrobe being out of "
        "frame is expected.\n\n"
        "CHECK 3 — CHARACTER COUNT:\n"
        "Compare the people visible in the frame to the `panel.characters` "
        "list. `ok` = exactly the declared characters are present (it is OK "
        "if a face/head is cropped — count the body). `extra` = an extra "
        "person appears who is not declared. `missing` = a declared "
        "character is absent.\n\n"
        "OUTPUT (JSON only, no preamble, no markdown fence):\n"
        "{\n"
        '  "framing_match": "ok" | "wider" | "tighter",\n'
        '  "rendered_distance_estimate": "ecu-face" | "ecu-region" | "mcu" | "medium" | "cowboy" | "full" | "wide-establish" | "splash",\n'
        '  "wardrobe_visibility": "ok" | "missing" | "n_a_cropped",\n'
        '  "wardrobe_missing_items": ["<item1>", "<item2>"],\n'
        '  "character_count": "ok" | "extra" | "missing",\n'
        '  "notes": "<one sentence describing what you observed>"\n'
        "}\n"
    )


def call_vision_api(image_path: Path, panel: dict, shotlist: dict) -> dict:
    """Send one panel image + rubric to Claude, return parsed JSON."""
    try:
        import anthropic  # type: ignore
    except ImportError as e:
        raise RuntimeError(
            "anthropic package not installed. Run `pip install anthropic` "
            "or `pip install -r runners/requirements.txt`."
        ) from e

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY env var not set.")

    model = os.environ.get("CLAUDE_VISION_AUDIT_MODEL", "claude-opus-4-7")
    client = anthropic.Anthropic(api_key=api_key)

    media_type = "image/png" if image_path.suffix.lower() == ".png" else "image/jpeg"
    with open(image_path, "rb") as f:
        b64 = base64.standard_b64encode(f.read()).decode("ascii")

    requested_distance = parse_camera_distance(panel.get("camera", "") or "")
    user_prompt = build_rubric_prompt(panel, shotlist, requested_distance)

    last_err: Exception | None = None
    for attempt in range(1, 4):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=600,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": b64}},
                        {"type": "text", "text": user_prompt},
                    ],
                }],
            )
            break
        except Exception as e:
            last_err = e
            if attempt < 3:
                time.sleep(2 ** attempt)
    else:
        raise RuntimeError(f"vision_audit API call failed after 3 attempts: {last_err}")

    text = "".join(
        getattr(b, "text", "") for b in response.content if getattr(b, "type", None) == "text"
    ).strip()
    if text.startswith("```"):
        lines = text.splitlines()[1:]
        for i, line in enumerate(lines):
            if line.strip() == "```":
                lines = lines[:i]
                break
        text = "\n".join(lines)
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"vision_audit returned unparseable JSON: {text[:500]}") from e


def classify_findings(panel: dict, page_num: int, verdict: dict) -> list[VisionFinding]:
    """Turn one panel's verdict dict into Finding rows."""
    pid = panel.get("panel_id", f"page-{page_num}")
    out: list[VisionFinding] = []

    framing = verdict.get("framing_match")
    rendered = verdict.get("rendered_distance_estimate")
    requested = parse_camera_distance(panel.get("camera", "") or "") or "?"
    notes = verdict.get("notes", "")

    if framing == "wider":
        out.append(VisionFinding(
            page_num, pid, "framing", SEVERITY_HARD,
            f"rendered framing wider than requested ({requested} → {rendered}). {notes}",
            "Regenerate with a frame-lockdown clause (lessons-learned.md L25) naming what should be OUT of frame, "
            "or accept and update the shotlist camera value to match the render.",
        ))
    elif framing == "tighter":
        out.append(VisionFinding(
            page_num, pid, "framing", SEVERITY_SOFT,
            f"rendered framing tighter than requested ({requested} → {rendered}). {notes}",
            "Usually acceptable — tighter framing rarely hurts. Regen if a wider establishing context is essential.",
        ))

    wardrobe = verdict.get("wardrobe_visibility")
    missing = verdict.get("wardrobe_missing_items") or []
    if wardrobe == "missing":
        out.append(VisionFinding(
            page_num, pid, "wardrobe", SEVERITY_HARD,
            f"wardrobe items absent from visible body region: {missing}. {notes}",
            "Regenerate with explicit wardrobe anchoring in the prompt ('apron remains visible covering the torso'). "
            "If the framing was wider than requested, tighten with a frame-lockdown clause first (L25).",
        ))

    chars = verdict.get("character_count")
    if chars == "extra":
        out.append(VisionFinding(
            page_num, pid, "character_count", SEVERITY_HARD,
            f"extra person in frame not in panel.characters ({panel.get('characters', [])}). {notes}",
            "Regenerate. The prompt likely under-anchored 'single character only' — add it as a NEGATIVE LOCK.",
        ))
    elif chars == "missing":
        out.append(VisionFinding(
            page_num, pid, "character_count", SEVERITY_HARD,
            f"declared character missing from frame. {notes}",
            "Regenerate. The prompt did not place this character in the action; rewrite the action to put them in shot.",
        ))

    if not out:
        # Record a clean PASS as INFO so the report is unambiguous about
        # what was verified vs what was skipped.
        out.append(VisionFinding(
            page_num, pid, "vision_audit", SEVERITY_INFO,
            f"vision audit clean — framing={framing}, wardrobe={wardrobe}, character_count={chars}. {notes}",
            "",
        ))
    return out


def format_report_md(project: Path, findings: list[VisionFinding], shotlist: dict, panels_checked: int) -> str:
    hard = sum(1 for f in findings if f.severity == SEVERITY_HARD)
    soft = sum(1 for f in findings if f.severity == SEVERITY_SOFT)
    info = sum(1 for f in findings if f.severity == SEVERITY_INFO)
    title = shotlist.get("title") or shotlist.get("project") or project.name
    lines = [
        f"# Continuity vision audit — {title}",
        "",
        f"Project: `{project}`",
        f"Panels checked: {panels_checked}",
        f"Findings: **{hard} hard**, {soft} soft, {info} info",
        f"Run at: {time.strftime('%Y-%m-%d %H:%M', time.localtime())}",
        "",
    ]
    if not findings:
        lines.append("No panels checked (project may have no accepted panels yet).")
        return "\n".join(lines)

    by_sev = {SEVERITY_HARD: [], SEVERITY_SOFT: [], SEVERITY_INFO: []}
    for f in findings:
        by_sev[f.severity].append(f)
    for sev in (SEVERITY_HARD, SEVERITY_SOFT, SEVERITY_INFO):
        bucket = by_sev[sev]
        if not bucket:
            continue
        lines.append(f"## {sev.upper()} ({len(bucket)})")
        lines.append("")
        lines.append("| Page | Panel | Category | Issue | Suggestion |")
        lines.append("|------|-------|----------|-------|------------|")
        for f in bucket:
            page = f.page if f.page is not None else "-"
            panel = f.panel_id or "-"
            msg = f.message.replace("\n", " ").replace("|", "/")
            sug = f.suggestion.replace("\n", " ").replace("|", "/")
            lines.append(f"| {page} | {panel} | {f.category} | {msg} | {sug} |")
        lines.append("")
    return "\n".join(lines)


def resolve_pages_arg(arg: str | None) -> set[int] | None:
    if arg is None:
        return None
    out: set[int] = set()
    for part in arg.split(","):
        part = part.strip()
        if "-" in part:
            lo, hi = part.split("-", 1)
            out.update(range(int(lo), int(hi) + 1))
        else:
            out.add(int(part))
    return out


def parse_image_overrides(args: list[str]) -> dict[str, Path]:
    """`--image-override p04-04=path/to/file.png` repeated. Used to vision-audit
    a backup image (e.g. p04-04.v1.original.png) without renaming the accepted
    file. Order-stable per panel_id (last value wins)."""
    out: dict[str, Path] = {}
    for s in args or []:
        if "=" not in s:
            sys.exit(f"--image-override needs `panel_id=path`, got: {s}")
        pid, p = s.split("=", 1)
        out[pid.strip()] = Path(p.strip())
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", required=True, type=Path)
    ap.add_argument("--pages", help="Page range to audit, e.g. '1-7' or '3,5'")
    ap.add_argument("--panels", help="Comma-separated panel_id list (e.g. 'p04-04,p05-03'). Overrides --pages.")
    ap.add_argument("--image-override", action="append", default=[],
                    help="Override the accepted image for a panel: `p04-04=path/to/swap.png`. Repeatable.")
    ap.add_argument("--json", action="store_true", help="Emit JSON instead of markdown")
    ap.add_argument("--out", type=Path, help="Write report to file. Defaults to <project>/continuity-vision-report.md")
    args = ap.parse_args()

    project = args.project.resolve()
    shotlist_path = project / "shotlist.json"
    if not shotlist_path.exists():
        sys.exit(f"shotlist.json not found at {shotlist_path}")
    with open(shotlist_path) as f:
        shotlist = json.load(f)

    pages_filter = resolve_pages_arg(args.pages)
    panel_filter: set[str] | None = None
    if args.panels:
        panel_filter = {p.strip() for p in args.panels.split(",") if p.strip()}
    overrides = parse_image_overrides(args.image_override)

    all_findings: list[VisionFinding] = []
    panels_checked = 0
    for page in shotlist.get("pages", []):
        n = page.get("page_number")
        if pages_filter is not None and n not in pages_filter:
            continue
        for panel in page.get("panels", []):
            pid = panel.get("panel_id") or f"page-{n}"
            if panel_filter is not None and pid not in panel_filter:
                continue
            img = find_panel_image(project, pid, overrides)
            if img is None:
                all_findings.append(VisionFinding(
                    n, pid, "asset", SEVERITY_SOFT,
                    "no accepted image on disk — skipping vision check",
                    "Generate and accept the panel before running the vision audit.",
                ))
                continue
            try:
                verdict = call_vision_api(img, panel, shotlist)
            except RuntimeError as e:
                all_findings.append(VisionFinding(
                    n, pid, "vision_audit", SEVERITY_SOFT,
                    f"vision API call failed: {e}",
                    "Check ANTHROPIC_API_KEY and rerun. SOFT severity so the run keeps going.",
                ))
                continue
            all_findings.extend(classify_findings(panel, n, verdict))
            panels_checked += 1

    if args.json:
        payload = {
            "project": str(project),
            "panels_checked": panels_checked,
            "findings": [asdict(f) for f in all_findings],
        }
        output = json.dumps(payload, indent=2)
    else:
        output = format_report_md(project, all_findings, shotlist, panels_checked)

    out_path = args.out or (project / "continuity-vision-report.md")
    if not args.json:
        out_path.write_text(output)
        print(f"wrote {out_path}")
    print(output)

    hard_count = sum(1 for f in all_findings if f.severity == SEVERITY_HARD)
    sys.exit(1 if hard_count else 0)


if __name__ == "__main__":
    main()
