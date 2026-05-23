#!/usr/bin/env python3
"""Vision audit — experimental holistic per-panel visual-defect detector.

Distinct from `audit_panels.py` (which dispatches per-rule vision rubrics keyed
off the rules registry). This script runs ONE holistic rubric per panel that
covers every defect category in the experiment taxonomy:

  composite_mismatch, hair_discontinuity, costume_discontinuity, scale_error,
  empty_speech_bubble, tier_visualization_mismatch, prompt_bloat_artifact,
  lettering_error, character_count_error, character_identity_swap.

Usage:
    # Score a labeled set + write metrics
    python3 vision_audit.py \
        --labeled-set docs/experiments/02-vision-audit-pilot/labeled-set-v1.json \
        --rubric       docs/experiments/02-vision-audit-pilot/rubric_v1.md \
        --out-dir      docs/experiments/02-vision-audit-pilot/runs/ \
        --run-tag      v1

    # Audit a single panel against canonical refs (no labels needed)
    python3 vision_audit.py \
        --panel projects/ultra-gal-origin/pages/panels/p04-04/v1_accepted.png \
        --rubric docs/experiments/02-vision-audit-pilot/rubric_v1.md

Requires: ANTHROPIC_API_KEY env + `anthropic` package. Without either, the
script exits with a clear error rather than guessing.

NOT WIRED INTO THE AUTOPILOT. This is the experiment's measurement tool; the
decision to wire it into the per-panel acceptance flow is deliberately
deferred to a separate task after the experiment ships its recommendation.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]

DEFAULT_MODEL = "claude-sonnet-4-5"  # cost-conscious choice for an experiment
MAX_TOKENS = 1500

DEFECT_CATEGORIES = [
    "composite_mismatch",
    "hair_discontinuity",
    "costume_discontinuity",
    "scale_error",
    "empty_speech_bubble",
    "tier_visualization_mismatch",
    "prompt_bloat_artifact",
    "lettering_error",
    "character_count_error",
    "character_identity_swap",
]

HIGH_PRIORITY = {
    "composite_mismatch",
    "hair_discontinuity",
    "costume_discontinuity",
    "scale_error",
}


def b64(p: Path) -> tuple[str, str]:
    media = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}.get(
        p.suffix.lower().lstrip("."), "image/png"
    )
    return base64.standard_b64encode(p.read_bytes()).decode(), media


def call_vision_model(rubric: str, image_path: Path, model: str) -> dict[str, Any]:
    try:
        import anthropic
    except ImportError:
        raise SystemExit(
            "vision_audit: `anthropic` package not installed. `pip install anthropic` and rerun."
        )
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("vision_audit: ANTHROPIC_API_KEY not set in env.")

    img_b64, img_media = b64(image_path)
    content = [
        {"type": "text", "text": "PANEL TO AUDIT:"},
        {"type": "image", "source": {"type": "base64", "media_type": img_media, "data": img_b64}},
        {"type": "text", "text": rubric},
    ]

    client = anthropic.Anthropic()
    resp = client.messages.create(
        model=model,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": content}],
    )
    text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
    return parse_verdict(text)


def parse_verdict(text: str) -> dict[str, Any]:
    """Extract the JSON object from the model output. Tolerates surrounding
    prose or code fences even though the rubric asks for raw JSON."""
    raw = text.strip()
    # Strip code fences if present
    if raw.startswith("```"):
        m = re.search(r"```(?:json)?\s*(.*?)```", raw, re.DOTALL)
        if m:
            raw = m.group(1).strip()
    # Find the first {...} block
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if not m:
        return {"_parse_error": True, "_raw": text[:500]}
    try:
        obj = json.loads(m.group(0))
    except json.JSONDecodeError as e:
        return {"_parse_error": True, "_raw": text[:500], "_error": str(e)}
    # Normalize: ensure all categories present
    out = {}
    for cat in DEFECT_CATEGORIES:
        v = obj.get(cat) or {}
        if not isinstance(v, dict):
            v = {"detected": False, "confidence": "low", "reason": "missing from model output"}
        out[cat] = {
            "detected": bool(v.get("detected", False)),
            "confidence": str(v.get("confidence", "low")).lower(),
            "reason": str(v.get("reason", ""))[:300],
        }
    return out


def score_panel(panel: dict, rubric: str, model: str, retries: int = 2) -> dict:
    img_path = REPO_ROOT / panel["path"]
    if not img_path.exists():
        return {"_error": f"image missing: {img_path}"}
    last_err = None
    for attempt in range(retries + 1):
        try:
            return call_vision_model(rubric, img_path, model)
        except Exception as e:
            last_err = e
            time.sleep(2 * (attempt + 1))
    return {"_error": f"vision call failed after {retries+1} attempts: {last_err}"}


def compute_metrics(labeled: list[dict], predictions: list[dict]) -> dict:
    """Per-category recall / precision + overall accuracy.

    Recall(C) = of panels labeled with C, how many had detected==True for C in the prediction?
    Precision(C) = of panels with detected==True for C in prediction, how many were labeled with C?
    Overall accuracy: GOOD predicted GOOD (no defects detected at high/medium confidence)
                      AND BAD predicted BAD (at least one labeled-category detected).
    """
    per_cat = {c: {"tp": 0, "fp": 0, "fn": 0, "tn": 0} for c in DEFECT_CATEGORIES}
    good_panels = 0
    bad_panels = 0
    good_predicted_good = 0
    bad_predicted_bad = 0

    for panel, pred in zip(labeled, predictions):
        if "_error" in pred or "_parse_error" in pred:
            continue
        labeled_set = set(panel.get("defects", []))
        is_bad = bool(labeled_set) and panel["label"] == "BAD"

        # Count any HIGH or MEDIUM confidence detection as a positive prediction
        detected_set = {
            c for c in DEFECT_CATEGORIES
            if pred.get(c, {}).get("detected") and pred[c].get("confidence") in ("high", "medium")
        }

        for c in DEFECT_CATEGORIES:
            labeled_c = c in labeled_set
            detected_c = c in detected_set
            if labeled_c and detected_c:
                per_cat[c]["tp"] += 1
            elif labeled_c and not detected_c:
                per_cat[c]["fn"] += 1
            elif (not labeled_c) and detected_c:
                per_cat[c]["fp"] += 1
            else:
                per_cat[c]["tn"] += 1

        if is_bad:
            bad_panels += 1
            # bad predicted bad if at least one of the labeled categories was detected
            if labeled_set & detected_set:
                bad_predicted_bad += 1
        else:
            good_panels += 1
            # good predicted good if NO category was high/medium detected
            if not detected_set:
                good_predicted_good += 1

    metrics = {"per_category": {}}
    for c in DEFECT_CATEGORIES:
        s = per_cat[c]
        tp, fp, fn, tn = s["tp"], s["fp"], s["fn"], s["tn"]
        recall = tp / (tp + fn) if (tp + fn) else None
        precision = tp / (tp + fp) if (tp + fp) else None
        metrics["per_category"][c] = {
            "tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "recall": recall, "precision": precision,
            "support_bad": tp + fn,
        }
    metrics["overall"] = {
        "good_panels": good_panels,
        "bad_panels": bad_panels,
        "good_correctly_predicted_good": good_predicted_good,
        "bad_correctly_predicted_bad": bad_predicted_bad,
        "good_accuracy": good_predicted_good / good_panels if good_panels else None,
        "bad_accuracy": bad_predicted_bad / bad_panels if bad_panels else None,
        "total_accuracy": (good_predicted_good + bad_predicted_bad) / (good_panels + bad_panels)
                          if (good_panels + bad_panels) else None,
    }
    return metrics


def write_metrics_md(metrics: dict, labeled_meta: dict, run_tag: str, rubric_path: Path,
                     predictions: list[dict], labeled_panels: list[dict]) -> str:
    lines = []
    lines.append(f"# Vision Audit — Metrics {run_tag}")
    lines.append("")
    lines.append(f"**Run tag:** `{run_tag}`")
    lines.append(f"**Rubric:** `{rubric_path}`")
    lines.append(f"**Labeled set:** {labeled_meta.get('labeled_set_version','?')} — "
                 f"{labeled_meta.get('split_summary',{}).get('total','?')} panels "
                 f"({labeled_meta.get('split_summary',{}).get('good','?')} GOOD / "
                 f"{labeled_meta.get('split_summary',{}).get('bad','?')} BAD)")
    lines.append("")
    o = metrics["overall"]
    lines.append("## Overall")
    lines.append("")
    lines.append(f"- Total panels: {o['good_panels'] + o['bad_panels']}")
    lines.append(f"- GOOD predicted GOOD: **{o['good_correctly_predicted_good']}/{o['good_panels']}** "
                 f"({pct(o['good_accuracy'])})")
    lines.append(f"- BAD predicted BAD:   **{o['bad_correctly_predicted_bad']}/{o['bad_panels']}** "
                 f"({pct(o['bad_accuracy'])})")
    lines.append(f"- Total accuracy:      **{pct(o['total_accuracy'])}**")
    lines.append("")
    lines.append("## Per-defect-category")
    lines.append("")
    lines.append("| Category | Priority | Support (BAD) | TP | FP | FN | Recall | Precision |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for cat in DEFECT_CATEGORIES:
        s = metrics["per_category"][cat]
        prio = "HIGH" if cat in HIGH_PRIORITY else "med/low"
        lines.append(f"| `{cat}` | {prio} | {s['support_bad']} | {s['tp']} | {s['fp']} | "
                     f"{s['fn']} | {pct(s['recall'])} | {pct(s['precision'])} |")
    lines.append("")
    lines.append("## HIGH-priority recall (stop-condition check)")
    lines.append("")
    lines.append("The experiment's stop condition is **recall ≥ 80% on every HIGH-priority "
                 "category** (composite_mismatch, hair_discontinuity, costume_discontinuity, scale_error).")
    lines.append("")
    fails = []
    skipped = []
    for cat in sorted(HIGH_PRIORITY):
        s = metrics["per_category"][cat]
        if s["support_bad"] == 0:
            skipped.append(cat)
            lines.append(f"- `{cat}`: **n/a** (0 BAD examples in labeled set — cannot measure)")
        else:
            r = s["recall"]
            status = "PASS" if (r is not None and r >= 0.8) else "FAIL"
            if status == "FAIL":
                fails.append(cat)
            lines.append(f"- `{cat}`: recall {pct(r)} ({s['tp']}/{s['tp']+s['fn']}) — **{status}**")
    lines.append("")
    if not fails and not skipped:
        lines.append("**Stop-condition: MET.**")
    elif fails:
        lines.append(f"**Stop-condition: NOT MET** — recall < 80% on: {', '.join(fails)}")
    elif skipped:
        lines.append(f"**Stop-condition: INCOMPLETE** — no examples to measure: {', '.join(skipped)}. "
                     "Cannot certify these categories from this labeled set.")
    lines.append("")

    # Per-panel detail
    lines.append("## Per-panel detail")
    lines.append("")
    lines.append("| Panel | Label | Labeled defects | Detected (high/med) | Notes |")
    lines.append("|---|---|---|---|---|")
    for panel, pred in zip(labeled_panels, predictions):
        if "_error" in pred or "_parse_error" in pred:
            err = pred.get("_error") or pred.get("_raw","parse_error")[:60]
            lines.append(f"| `{panel['panel_id']}` | {panel['label']} | "
                         f"{', '.join(panel.get('defects',[])) or '—'} | ERROR | {err} |")
            continue
        detected = []
        for c in DEFECT_CATEGORIES:
            v = pred.get(c, {})
            if v.get("detected") and v.get("confidence") in ("high", "medium"):
                detected.append(f"{c}({v['confidence'][0]})")
        match = ""
        labeled = set(panel.get("defects", []))
        detected_cats = {d.split("(")[0] for d in detected}
        if panel["label"] == "BAD":
            hits = labeled & detected_cats
            misses = labeled - detected_cats
            spurious = detected_cats - labeled
            if hits:
                match += f"hits: {','.join(hits)}; "
            if misses:
                match += f"missed: {','.join(misses)}; "
            if spurious:
                match += f"extra: {','.join(spurious)}"
        else:
            if detected_cats:
                match = f"FALSE ALARMS: {','.join(detected_cats)}"
            else:
                match = "clean"
        lines.append(f"| `{panel['panel_id']}` | {panel['label']} | "
                     f"{', '.join(panel.get('defects',[])) or '—'} | "
                     f"{', '.join(detected) or '(none)'} | {match} |")
    lines.append("")
    return "\n".join(lines) + "\n"


def pct(v) -> str:
    if v is None:
        return "n/a"
    return f"{v*100:.0f}%"


def run_labeled_set(labeled_set_path: Path, rubric_path: Path, out_dir: Path,
                    run_tag: str, model: str, dry_run: bool):
    labeled_meta = json.loads(labeled_set_path.read_text())
    panels = labeled_meta["panels"]
    rubric = rubric_path.read_text()

    out_dir.mkdir(parents=True, exist_ok=True)
    raw_out = out_dir / f"raw-predictions-{run_tag}.jsonl"
    metrics_md = out_dir / f"metrics-{run_tag}.md"
    metrics_json = out_dir / f"metrics-{run_tag}.json"

    if dry_run:
        print(f"DRY-RUN: would score {len(panels)} panels with {rubric_path.name} "
              f"on model {model}, writing to {out_dir}")
        return 0

    predictions: list[dict] = []
    print(f"# vision_audit run_tag={run_tag} model={model} panels={len(panels)} rubric={rubric_path.name}")
    with raw_out.open("w") as f:
        for i, panel in enumerate(panels, 1):
            print(f"  [{i:2d}/{len(panels)}] {panel['panel_id']} ({panel['label']}) ...", flush=True)
            t0 = time.time()
            pred = score_panel(panel, rubric, model)
            dt = time.time() - t0
            predictions.append(pred)
            f.write(json.dumps({"panel": panel, "prediction": pred, "dt_s": dt}) + "\n")
            if "_error" in pred:
                print(f"       error: {pred['_error']}")
            elif "_parse_error" in pred:
                print(f"       parse_error: {pred.get('_raw','')[:80]!r}")
            else:
                hits = [c for c in DEFECT_CATEGORIES
                        if pred.get(c, {}).get("detected") and pred[c].get("confidence") in ("high", "medium")]
                print(f"       detected({len(hits)}): {','.join(hits) or '(none)'}  ({dt:.1f}s)")

    metrics = compute_metrics(panels, predictions)
    metrics_json.write_text(json.dumps(metrics, indent=2))
    md = write_metrics_md(metrics, labeled_meta, run_tag, rubric_path, predictions, panels)
    metrics_md.write_text(md)
    print(f"\nwrote {metrics_md}")
    print(f"wrote {metrics_json}")
    print(f"wrote {raw_out}")
    return 0


def run_single(panel_path: Path, rubric_path: Path, model: str) -> int:
    rubric = rubric_path.read_text()
    pred = call_vision_model(rubric, panel_path, model)
    print(json.dumps(pred, indent=2))
    return 0


def score_from_existing(labeled_set_path: Path, predictions_path: Path, rubric_path: Path,
                        out_dir: Path, run_tag: str) -> int:
    """Compute metrics from an existing JSONL predictions file (no API calls).
    Each JSONL line: {"panel_id": "...", "defects": {<rubric output>}}.
    Useful when predictions were produced out-of-band (e.g., by a sub-agent run)."""
    labeled_meta = json.loads(labeled_set_path.read_text())
    panels = labeled_meta["panels"]
    pred_by_id: dict[str, dict] = {}
    for line in predictions_path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        pred_by_id[rec["panel_id"]] = rec.get("defects", {})

    predictions: list[dict] = []
    for panel in panels:
        raw = pred_by_id.get(panel["panel_id"])
        if raw is None:
            predictions.append({"_error": f"no prediction for {panel['panel_id']}"})
            continue
        # Normalize to ensure all categories present
        norm: dict[str, Any] = {}
        for cat in DEFECT_CATEGORIES:
            v = raw.get(cat) or {}
            if not isinstance(v, dict):
                v = {"detected": False, "confidence": "low", "reason": "missing"}
            norm[cat] = {
                "detected": bool(v.get("detected", False)),
                "confidence": str(v.get("confidence", "low")).lower(),
                "reason": str(v.get("reason", ""))[:300],
            }
        predictions.append(norm)

    out_dir.mkdir(parents=True, exist_ok=True)
    metrics = compute_metrics(panels, predictions)
    (out_dir / f"metrics-{run_tag}.json").write_text(json.dumps(metrics, indent=2))
    md = write_metrics_md(metrics, labeled_meta, run_tag, rubric_path, predictions, panels)
    (out_dir / f"metrics-{run_tag}.md").write_text(md)
    print(f"wrote {out_dir / f'metrics-{run_tag}.md'}")
    print(f"wrote {out_dir / f'metrics-{run_tag}.json'}")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--labeled-set", type=Path, help="path to labeled set JSON")
    ap.add_argument("--rubric", type=Path, required=True, help="path to rubric .md")
    ap.add_argument("--out-dir", type=Path, help="where to write metrics + raw predictions")
    ap.add_argument("--run-tag", default="v1", help="tag for this run (used in output filenames)")
    ap.add_argument("--panel", type=Path, help="audit a single panel image (no labels)")
    ap.add_argument("--score-from", type=Path,
                    help="score from an existing predictions JSONL (no API calls)")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.score_from:
        if not args.labeled_set or not args.out_dir:
            ap.error("--score-from requires --labeled-set and --out-dir")
        return score_from_existing(args.labeled_set, args.score_from, args.rubric,
                                   args.out_dir, args.run_tag)
    if args.panel:
        return run_single(args.panel, args.rubric, args.model)
    if not args.labeled_set or not args.out_dir:
        ap.error("--labeled-set and --out-dir required (or use --panel / --score-from)")
    return run_labeled_set(args.labeled_set, args.rubric, args.out_dir,
                           args.run_tag, args.model, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
