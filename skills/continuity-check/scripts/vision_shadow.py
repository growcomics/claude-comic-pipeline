#!/usr/bin/env python3
"""vision_shadow.py — ADVISORY vision-audit shadow sidecar.

Runs experiment 02's vision audit (rubric v3 categories + v5 confidence semantics +
canonical face cards) as a SHADOW alongside the banked production chain, and measures
agreement against the fresh-subagent verdicts that real production already banked.

HARD CONSTRAINTS (by design — see docs/experiments/02-vision-audit-pilot/):
  * ZERO writes to any gate script, MANIFEST.sha256, ledger, pages-log, or receipt
    produced by the compose→audit→bank chain. This sidecar READS banked state and
    WRITES advisory files only:
        <project>/qa/vision-shadow/            rubric, batches, raw verdicts, GT, metrics
        <project>/qa/receipts/<job>.vision.json   ADVISORY per-panel verdict (new file)
        <project>/qa/vision-shadow-report.md   agreement report
  * It never imports or executes anything from <project>/qa/*.py (gates may be
    integrity-locked; this script must work regardless of gate lock state).
  * Advisory receipts carry {"advisory": true} and a plain-language note; nothing in
    bank.py / verify_chain.py consumes *.vision.json files.

Vision verdicts are produced by Claude-Code subagents (SPOTTER MODE: cheap vision
models read panels in batches), not by an in-process API call — the harness blanks
ANTHROPIC_API_KEY, same constraint experiment 02 hit. So the flow is three commands:

  1) plan    — walk banked logs, resolve local images, assemble the per-project rubric
               (core verbatim + cast canon), emit batch manifests for subagents.
  2) ingest  — validate + normalize the raw per-panel JSONs the subagents wrote, map
               detections to canonical registry IDs, write advisory receipts.
  3) report  — join vision verdicts against ground truth (banked chain verdicts +
               optional notes-classification, or a qa-report.md defect table), compute
               per-category agreement vs the ship bar (recall>=80%, precision>=70%),
               write qa/vision-shadow-report.md + agreement.json.

Usage (from repo root):
  python3 skills/continuity-check/scripts/vision_shadow.py plan \
      --project projects/scientists --log pages-log.json --batch-size 9
  python3 skills/continuity-check/scripts/vision_shadow.py plan \
      --project projects/not-so-supra-man --log hf-log-A.json --log hf-log-B.json \
      --log hf-log-C.json --report-gt qa-report.md
  python3 skills/continuity-check/scripts/vision_shadow.py ingest \
      --project projects/scientists --model-note "sonnet subagents"
  python3 skills/continuity-check/scripts/vision_shadow.py report \
      --project projects/scientists
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CORE_RUBRIC = REPO_ROOT / "skills/continuity-check/references/vision-shadow-rubric-core.md"
CANON_REGISTRY = REPO_ROOT / "skills/comic-production/references/defect-registry.json"

SHIP_RECALL = 0.80
SHIP_PRECISION = 0.70
MIN_SUPPORT_FOR_PROMOTE = 5  # experiment 02 lesson: 0-support categories are uncertifiable

CATEGORIES = [
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
    "location_mismatch",  # SHADOW EXTENSION (ENV-01)
]

# --- canonical registry mapping -------------------------------------------------
# Vision category -> canonical registry IDs. `refine` adds IDs when the verdict's
# free-text reason matches; comparison happens at GROUP level so sub-ID ambiguity
# (WARD-01 vs WARD-04 vs WARD-05) never breaks agreement scoring.
VISION2REG = {
    "composite_mismatch": {
        "base": ["ENV-03"],
        "refine": [(r"disembodied|floating|headless|without a body|missing (?:a )?body|anatom", ["BODY-05"])],
    },
    "hair_discontinuity": {"base": ["HAIR-01"], "refine": []},
    "costume_discontinuity": {
        "base": ["WARD-01"],
        "refine": [
            (r"emblem|chevron|insignia|logo|shield|glyph", ["WARD-05"]),
            (r"too early|wrong stage|hero suit|scripted (?:costume|state)|should still", ["WARD-04"]),
            (r"coverage|exposed|nude|topless", ["WARD-06"]),
        ],
    },
    "scale_error": {
        "base": ["BODY-02"],
        "refine": [(r"too (?:large|big)|giant|inflat|oversized", ["BODY-07"]),
                   (r"composit|pasted", ["ENV-03"])],
    },
    "empty_speech_bubble": {
        "base": ["LET-01"],
        "refine": [(r"tail|attribut|wrong (?:character|speaker)", ["LET-03"])],
    },
    "tier_visualization_mismatch": {"base": ["BODY-01"], "refine": [(r"above|over", ["BODY-07"])]},
    "prompt_bloat_artifact": {"base": ["STYLE-01"], "refine": []},
    "lettering_error": {"base": ["LET-02"], "refine": []},
    "character_count_error": {
        "base": ["CAST-03"],
        "refine": [(r"extra|additional|background|more figures|unscripted", ["CAST-02"])],
    },
    "character_identity_swap": {"base": ["IDENT-01"], "refine": []},
    "location_mismatch": {"base": ["ENV-01"], "refine": []},
}

# Registry ID -> comparison group. Agreement is computed per GROUP: both the vision
# side and the ground-truth side map into this space, so "did the shadow notice the
# same problem" is measured without taxonomy hair-splitting between sibling IDs.
def group_of_id(rid: str) -> str:
    fam, _, num = rid.partition("-")
    if fam == "WARD":
        return "WARD"
    if fam == "HAIR":
        return "HAIR"
    if fam == "IDENT" or rid == "CAST-01":
        return "IDENT"
    if rid in ("CAST-02", "CAST-03"):
        return "COUNT"
    if rid in ("BODY-01", "BODY-02", "BODY-03", "BODY-07"):
        return "SIZE"
    if rid in ("BODY-05", "BODY-09", "BODY-06", "BODY-08"):
        return "ANATOMY"
    if rid == "ENV-01":
        return "ENV"
    if rid in ("ENV-03",):
        return "COMPOSITE"
    if fam == "STYLE":
        return "STYLE"
    if fam == "LET":
        return "LETTER"
    if fam == "PROP":
        return "PROP"
    if fam == "FACE":
        return "FACE"
    if fam == "CAM":
        return "CAMERA"
    return "OTHER"

GROUP_ORDER = ["WARD", "HAIR", "IDENT", "COUNT", "SIZE", "ANATOMY", "ENV", "COMPOSITE",
               "STYLE", "LETTER", "PROP", "FACE", "CAMERA", "OTHER"]

# Ground-truth keyword rules for qa-report.md style defect tables: issue text -> IDs.
GT_RULES = [
    (r"chevron|emblem|insignia|s-shield|\bglyph\b", "WARD-05"),
    (r"wardrobe too early|blue (?:hero )?suit", "WARD-04"),
    (r"wrong location|should be (?:doomer-)?lab", "ENV-01"),
    (r"barefoot|boots|wardrobe slip", "WARD-01"),
    (r"style drift|anime|cel-shaded|2d illustration", "STYLE-01"),
    (r"off-model", "IDENT-01"),
    (r"literaliz", "PROP-03"),
    (r"size regression|downsized|below tier|only modestly larger|reads ~tier", "BODY-01"),
    (r"hyper-massive|bodybuilder bulk", "BODY-07"),
    (r"doll|figurine|toy", "BODY-02"),
    (r"floating head|disembodied", "BODY-05"),
    (r"floating head|disembodied|compositing artifact", "ENV-03"),
    (r"unintended extra|human figure", "CAST-02"),
]


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_registry() -> dict:
    try:
        d = json.loads(CANON_REGISTRY.read_text())
        return {c["id"]: c.get("slug", "") for c in d.get("defects", []) if isinstance(c, dict) and c.get("id")}
    except Exception:
        return {}


# --- banked-log walking ---------------------------------------------------------

def load_log_entries(project: Path, log_name: str) -> dict[str, dict]:
    """Supports both log shapes seen in production:
      pages-log.json:  {"done": {panel_id: {"disk": ..., "chain": {...}}}, "pending": ...}
      hf-log-X.json:   {panel_id: {"page": N, "job": ..., "status": "done", "note": ...}}
    Returns {panel_id: entry} for DONE entries only."""
    data = json.loads((project / log_name).read_text())
    out: dict[str, dict] = {}
    pid_re = re.compile(r"^p\d+-\d+$")

    def take(mapping: dict):
        for pid, entry in mapping.items():
            if not pid_re.match(pid) or not isinstance(entry, dict):
                continue
            if entry.get("status", "done") not in ("done", "completed"):
                continue
            e = dict(entry)
            e["_log"] = log_name
            out[pid] = e

    if isinstance(data, dict):
        if isinstance(data.get("done"), dict):
            take(data["done"])
        elif isinstance(data.get("entries"), dict):
            take(data["entries"])
        else:
            take(data)
    return out


def resolve_image(project: Path, pid: str, entry: dict) -> Path | None:
    cands = []
    for key in ("disk", "file"):
        if entry.get(key):
            cands.append(project / entry[key])
    cands += [
        project / "pages" / f"{pid}.png",
        project / "pages" / "panels-hf" / f"{pid}.png",
        project / "pages" / "panels" / f"{pid}.png",
        project / "pages" / "panels-laptop" / f"{pid}.png",
    ]
    for c in cands:
        if c.exists():
            return c
    return None


def load_shotlist_context(project: Path) -> dict[str, dict]:
    sl_path = project / "shotlist.json"
    if not sl_path.exists():
        return {}
    sl = json.loads(sl_path.read_text())
    pages = []
    if isinstance(sl, list):
        pages = sl
    elif isinstance(sl, dict):
        for key in ("pages", "panels", "shots"):
            if isinstance(sl.get(key), list):
                pages = sl[key]
                break
    ctx: dict[str, dict] = {}
    for page in pages:
        for panel in page.get("panels", []):
            pid = panel.get("panel_id")
            if not pid:
                continue
            c = {
                "characters": panel.get("characters", []),
                "location": panel.get("location", ""),
                "time_of_day": panel.get("time_of_day", ""),
                "camera": panel.get("camera", ""),
                "action": (panel.get("action") or "")[:600],
            }
            for opt in ("costume_state", "muscle_size_tier", "size", "notes"):
                if panel.get(opt):
                    c[opt] = panel[opt] if not isinstance(panel[opt], str) else panel[opt][:300]
            dial = panel.get("dialogue") or []
            caps = panel.get("captions") or []
            c["scripted_dialogue"] = dial
            c["scripted_captions"] = caps
            c["expected_named_cast_size"] = len(c["characters"])
            ctx[pid] = c
    return ctx


def resolve_reference_images(project: Path, cast_ids: list[str]) -> list[dict]:
    refs = []
    lineup = project / "references" / "characters" / "cast-lineup.png"
    if lineup.exists():
        refs.append({"label": "cast-lineup", "path": str(lineup.relative_to(REPO_ROOT))})
    for cid in cast_ids:
        cdir = project / "references" / "characters" / cid
        for name in ("face-card.png", "identity-sheet.png"):
            p = cdir / name
            if p.exists():
                refs.append({"label": f"{cid} ({name.split('.')[0]})",
                             "path": str(p.relative_to(REPO_ROOT))})
                break
    return refs


# --- plan -----------------------------------------------------------------------

def cmd_plan(args) -> int:
    project = (REPO_ROOT / args.project).resolve() if not Path(args.project).is_absolute() else Path(args.project)
    shadow_dir = project / "qa" / "vision-shadow"
    (shadow_dir / "batches").mkdir(parents=True, exist_ok=True)
    (shadow_dir / "raw").mkdir(parents=True, exist_ok=True)

    entries: dict[str, dict] = {}
    for log in args.log:
        entries.update(load_log_entries(project, log))
    if not entries:
        print(f"plan: no done entries found in {args.log}", file=sys.stderr)
        return 2

    ctx = load_shotlist_context(project)

    resolved, missing = {}, []
    for pid in sorted(entries):
        img = resolve_image(project, pid, entries[pid])
        if img is None:
            missing.append(pid)
        else:
            resolved[pid] = img
    coverage = len(resolved) / len(entries) * 100 if entries else 0.0

    # Assemble the per-project rubric: core (verbatim) + cast canon insert.
    canon_path = shadow_dir / "cast-canon.md"
    rubric_text = CORE_RUBRIC.read_text()
    if canon_path.exists():
        rubric_text += "\n\n---\n\n# CAST CANON (per-project insert)\n\n" + canon_path.read_text()
    else:
        print(f"plan: WARNING no cast-canon.md at {canon_path} — rubric will lack cast specifics",
              file=sys.stderr)
    rubric_path = shadow_dir / "rubric.md"
    rubric_path.write_text(rubric_text)

    all_cast: list[str] = []
    for pid in resolved:
        for c in ctx.get(pid, {}).get("characters", []):
            if c not in all_cast:
                all_cast.append(c)

    pids = sorted(resolved)
    batches = [pids[i:i + args.batch_size] for i in range(0, len(pids), args.batch_size)]
    manifest_paths = []
    for i, chunk in enumerate(batches, 1):
        cast_in_batch: list[str] = []
        for pid in chunk:
            for c in ctx.get(pid, {}).get("characters", []):
                if c not in cast_in_batch:
                    cast_in_batch.append(c)
        m = {
            "batch_id": f"batch-{i:02d}",
            "project": str(project.relative_to(REPO_ROOT)),
            "rubric": str(rubric_path.relative_to(REPO_ROOT)),
            "reference_images": resolve_reference_images(project, cast_in_batch),
            "panels": [
                {
                    "panel_id": pid,
                    "image": str(resolved[pid].relative_to(REPO_ROOT)),
                    "out": str((shadow_dir / "raw" / f"{pid}.json").relative_to(REPO_ROOT)),
                    "context": ctx.get(pid, {}),
                }
                for pid in chunk
            ],
        }
        mp = shadow_dir / "batches" / f"batch-{i:02d}.json"
        mp.write_text(json.dumps(m, indent=2))
        manifest_paths.append(mp)

    plan_meta = {
        "generated": now_iso(),
        "logs": args.log,
        "entries_in_logs": len(entries),
        "images_resolved": len(resolved),
        "images_missing": missing,
        "coverage_pct": round(coverage, 1),
        "batches": [str(p.relative_to(REPO_ROOT)) for p in manifest_paths],
        "rubric_sha256": sha256_file(rubric_path),
        "report_gt": args.report_gt,
    }
    (shadow_dir / "plan.json").write_text(json.dumps(plan_meta, indent=2))
    print(json.dumps(plan_meta, indent=2))
    return 0


# --- ingest ---------------------------------------------------------------------

def normalize_verdict(raw: dict) -> dict:
    out = {}
    for cat in CATEGORIES:
        v = raw.get(cat) or {}
        if not isinstance(v, dict):
            v = {}
        conf = str(v.get("confidence", "low")).lower()
        if conf not in ("high", "medium", "low"):
            conf = "low"
        out[cat] = {
            "detected": bool(v.get("detected", False)),
            "confidence": conf,
            "reason": str(v.get("reason", ""))[:400],
        }
    return out


def registry_ids_for(cat: str, reason: str) -> list[str]:
    spec = VISION2REG[cat]
    ids = list(spec["base"])
    low = reason.lower()
    for pattern, extra in spec["refine"]:
        if re.search(pattern, low):
            for rid in extra:
                if rid not in ids:
                    ids.append(rid)
    return ids


def cmd_ingest(args) -> int:
    project = (REPO_ROOT / args.project).resolve() if not Path(args.project).is_absolute() else Path(args.project)
    shadow_dir = project / "qa" / "vision-shadow"
    receipts = project / "qa" / "receipts"
    receipts.mkdir(parents=True, exist_ok=True)
    plan = json.loads((shadow_dir / "plan.json").read_text())
    registry = load_registry()

    raw_dir = shadow_dir / "raw"
    written, missing, parse_errors = [], [], []
    expected = []
    for bp in plan["batches"]:
        m = json.loads((REPO_ROOT / bp).read_text())
        expected += [(p["panel_id"], p["image"]) for p in m["panels"]]

    for pid, image in expected:
        rp = raw_dir / f"{pid}.json"
        if not rp.exists():
            missing.append(pid)
            continue
        try:
            raw = json.loads(rp.read_text())
        except json.JSONDecodeError as e:
            parse_errors.append((pid, str(e)))
            continue
        verdict = normalize_verdict(raw)
        flags = []
        for cat in CATEGORIES:
            v = verdict[cat]
            if v["detected"] and v["confidence"] in ("high", "medium"):
                rids = registry_ids_for(cat, v["reason"])
                flags.append({
                    "category": cat,
                    "confidence": v["confidence"],
                    "registry_ids": rids,
                    "registry_slugs": [registry.get(r, "") for r in rids],
                    "groups": sorted({group_of_id(r) for r in rids}),
                    "reason": v["reason"],
                })
        receipt = {
            "advisory": True,
            "sidecar": "vision-shadow",
            "note": ("ADVISORY ONLY — shadow vision verdict. Not a gate artifact: not "
                     "produced by, consumed by, or able to alter compose/audit/bank/"
                     "verify_chain. Registry IDs cite skills/comic-production/"
                     "references/defect-registry.json."),
            "panel_id": pid,
            "image": image,
            "generated": now_iso(),
            "model_note": args.model_note,
            "rubric_sha256": plan.get("rubric_sha256", ""),
            "flags": flags,
            "categories": verdict,
        }
        out = receipts / f"page_{pid}.vision.json"
        out.write_text(json.dumps(receipt, indent=2))
        written.append(pid)

    summary = {
        "written": len(written),
        "missing_raw": missing,
        "parse_errors": parse_errors,
        "flagged_panels": sum(
            1 for pid in written
            if json.loads((receipts / f"page_{pid}.vision.json").read_text())["flags"]
        ),
    }
    print(json.dumps(summary, indent=2))
    return 0 if not parse_errors else 1


# --- ground truth ---------------------------------------------------------------

def gt_from_report_md(project: Path, report_name: str) -> dict[str, dict]:
    """Parse a qa-report.md defect table: | pNN | SEVERITY | issue |  ->  panel GT.
    Pages absent from the table are CLEAN ground truth."""
    text = (project / report_name).read_text()
    gt: dict[str, dict] = {}
    for line in text.splitlines():
        m = re.match(r"^\|\s*(p\d+)\s*\|\s*(BLOCKER|HIGH|LOW)\s*\|\s*(.+?)\s*\|\s*$", line)
        if not m:
            continue
        page, sev, issue = m.group(1), m.group(2), m.group(3)
        pid = f"{page}-01"
        ids = []
        low = issue.lower()
        for pattern, rid in GT_RULES:
            if re.search(pattern, low) and rid not in ids:
                ids.append(rid)
        if not ids:
            ids = ["MISC-00"]
        gt[pid] = {
            "source": f"{report_name} row {page}",
            "severity": sev,
            "issue": issue,
            "registry_ids": ids,
            "groups": sorted({group_of_id(r) for r in ids}),
        }
    return gt


def gt_from_chain(project: Path, entries: dict[str, dict]) -> dict[str, dict]:
    """Ground truth from the banked chain verdict.json files (+ optional
    notes-classification.json produced by a text subagent over verdict notes)."""
    cls_path = project / "qa" / "vision-shadow" / "notes-classification.json"
    cls = json.loads(cls_path.read_text()) if cls_path.exists() else {}
    gt: dict[str, dict] = {}
    for pid, entry in entries.items():
        chain = entry.get("chain") or {}
        vpath = chain.get("verdict")
        rec = {"source": vpath or "(no chain verdict)", "severity": None,
               "issue": "", "registry_ids": [], "groups": []}
        if vpath and (project / vpath).exists():
            v = json.loads((project / vpath).read_text())
            rec["banked_pass"] = bool(v.get("pass"))
            rec["issue"] = str(v.get("notes", ""))[:400]
            obs = (cls.get(pid) or {}).get("observations", [])
            ids = [o["registry_id"] for o in obs if o.get("kind") == "defect" and o.get("registry_id")]
            soft = [o["registry_id"] for o in obs
                    if o.get("kind") == "noted-acceptable" and o.get("registry_id")]
            rec["registry_ids"] = sorted(set(ids))
            rec["soft_ids"] = sorted(set(soft))
            rec["groups"] = sorted({group_of_id(r) for r in rec["registry_ids"]})
            rec["soft_groups"] = sorted({group_of_id(r) for r in rec["soft_ids"]})
        gt[pid] = rec
    return gt


# --- report ---------------------------------------------------------------------

def pct(v):
    return "n/a" if v is None else f"{v * 100:.0f}%"


def cmd_report(args) -> int:
    project = (REPO_ROOT / args.project).resolve() if not Path(args.project).is_absolute() else Path(args.project)
    shadow_dir = project / "qa" / "vision-shadow"
    receipts = project / "qa" / "receipts"
    plan = json.loads((shadow_dir / "plan.json").read_text())

    entries: dict[str, dict] = {}
    for log in plan["logs"]:
        entries.update(load_log_entries(project, log))

    vision: dict[str, dict] = {}
    for pid in sorted(entries):
        rp = receipts / f"page_{pid}.vision.json"
        if rp.exists():
            vision[pid] = json.loads(rp.read_text())

    if plan.get("report_gt"):
        gt = gt_from_report_md(project, plan["report_gt"])
        gt_mode = f"qa-report table: {plan['report_gt']}"
        clean_default = True   # pages absent from the defect table are labeled clean
    else:
        gt = gt_from_chain(project, entries)
        gt_mode = "banked chain verdict.json (+ notes-classification.json soft labels)"
        clean_default = False

    scope = sorted(set(vision) & (set(entries)))
    conf = {g: {"tp": 0, "fp": 0, "fn": 0, "tn": 0,
                "tp_panels": [], "fp_panels": [], "fn_panels": []} for g in GROUP_ORDER}
    panel_rows = []
    for pid in scope:
        vgroups = set()
        for f in vision[pid]["flags"]:
            vgroups |= set(f["groups"])
        g_rec = gt.get(pid)
        if g_rec is None:
            if not clean_default:
                continue
            g_rec = {"groups": [], "severity": None, "issue": "(clean per GT)"}
        ggroups = set(g_rec.get("groups", []))
        for g in GROUP_ORDER:
            in_v, in_g = g in vgroups, g in ggroups
            if in_v and in_g:
                conf[g]["tp"] += 1
                conf[g]["tp_panels"].append(pid)
            elif in_v:
                conf[g]["fp"] += 1
                conf[g]["fp_panels"].append(pid)
            elif in_g:
                conf[g]["fn"] += 1
                conf[g]["fn_panels"].append(pid)
            else:
                conf[g]["tn"] += 1
        panel_rows.append({
            "panel_id": pid,
            "image": vision[pid]["image"],
            "gt_groups": sorted(ggroups),
            "gt_severity": g_rec.get("severity"),
            "gt_issue": (g_rec.get("issue") or "")[:200],
            "vision_groups": sorted(vgroups),
            "agree_fail": sorted(vgroups & ggroups),
            "vision_only": sorted(vgroups - ggroups),
            "subagent_only": sorted(ggroups - vgroups),
        })

    # Panel-level: GT bad = any GT group (HIGH/BLOCKER only when severity known).
    def panel_bad_gt(r):
        if r["gt_severity"] in ("HIGH", "BLOCKER"):
            return True
        if r["gt_severity"] is None and r["gt_groups"]:
            return True
        return False

    bad = [r for r in panel_rows if panel_bad_gt(r)]
    clean = [r for r in panel_rows if not r["gt_groups"]]
    bad_caught = [r for r in bad if set(r["gt_groups"]) & set(r["vision_groups"])]
    bad_any_flag = [r for r in bad if r["vision_groups"]]
    clean_clean = [r for r in clean if not r["vision_groups"]]

    per_group = {}
    for g in GROUP_ORDER:
        s = conf[g]
        support = s["tp"] + s["fn"]
        flagged = s["tp"] + s["fp"]
        recall = s["tp"] / support if support else None
        precision = s["tp"] / flagged if flagged else None
        if support == 0 and flagged == 0:
            verdict = "no-signal"
        elif support < MIN_SUPPORT_FOR_PROMOTE:
            verdict = "insufficient-support"
        elif recall is not None and recall >= SHIP_RECALL and (precision or 0) >= SHIP_PRECISION:
            verdict = "PROMOTE-CANDIDATE"
        elif recall is not None and recall >= SHIP_RECALL:
            verdict = "advisory (recall ok, precision low)"
        else:
            verdict = "iterate/park (recall below bar)"
        per_group[g] = {**{k: s[k] for k in ("tp", "fp", "fn", "tn")},
                        "support": support, "recall": recall, "precision": precision,
                        "verdict": verdict}

    metrics = {
        "generated": now_iso(),
        "project": str(project.relative_to(REPO_ROOT)),
        "gt_mode": gt_mode,
        "scope_panels": len(scope),
        "coverage_pct": plan.get("coverage_pct"),
        "ship_bar": {"recall": SHIP_RECALL, "precision": SHIP_PRECISION,
                     "min_support": MIN_SUPPORT_FOR_PROMOTE},
        "per_group": per_group,
        "panel_level": {
            "gt_bad_panels": len(bad),
            "gt_bad_caught_same_group": len(bad_caught),
            "gt_bad_flagged_any_group": len(bad_any_flag),
            "gt_clean_panels": len(clean),
            "gt_clean_predicted_clean": len(clean_clean),
        },
    }
    (shadow_dir / "agreement.json").write_text(json.dumps(metrics, indent=2))

    # ---- markdown report ----
    L = []
    L.append(f"# Vision-Shadow Agreement Report — `{project.name}`")
    L.append("")
    L.append("> **ADVISORY SIDECAR.** Nothing in this report gates anything. The shadow reads")
    L.append("> banked state and writes `qa/receipts/*.vision.json` advisory files only; the")
    L.append("> compose→audit→bank→verify chain and its integrity manifest are untouched.")
    L.append("")
    L.append(f"- Generated: {metrics['generated']}  ·  Scope: **{len(scope)} panels**"
             f"  ·  Image coverage of banked logs: **{plan.get('coverage_pct')}%**")
    L.append(f"- Ground truth: {gt_mode}")
    L.append(f"- Vision side: rubric v3 categories + v5 confidence semantics + face cards"
             f" (`qa/vision-shadow/rubric.md`, sha256 `{plan.get('rubric_sha256','')[:16]}…`),"
             f" detections counted at confidence high+medium.")
    L.append(f"- Agreement is scored per COMPARISON GROUP (canonical registry IDs bucketed —"
             f" see `vision_shadow.py group_of_id`); registry IDs are cited per flag in the"
             f" advisory receipts.")
    L.append("")
    L.append("## Headline")
    L.append("")
    pl = metrics["panel_level"]
    if pl["gt_bad_panels"]:
        L.append(f"- Defective panels (per ground truth): **{pl['gt_bad_panels']}** — shadow"
                 f" flagged the SAME defect group on **{pl['gt_bad_caught_same_group']}**"
                 f" ({pct(pl['gt_bad_caught_same_group']/pl['gt_bad_panels'])}), flagged"
                 f" anything at all on {pl['gt_bad_flagged_any_group']}.")
    if pl["gt_clean_panels"]:
        L.append(f"- Clean panels (per ground truth): **{pl['gt_clean_panels']}** — shadow"
                 f" agreed clean on **{pl['gt_clean_predicted_clean']}**"
                 f" ({pct(pl['gt_clean_predicted_clean']/pl['gt_clean_panels'])}).")
    L.append("")
    L.append(f"## Per-group agreement (ship bar: recall ≥ {pct(SHIP_RECALL)},"
             f" precision ≥ {pct(SHIP_PRECISION)}, support ≥ {MIN_SUPPORT_FOR_PROMOTE})")
    L.append("")
    L.append("| Group | Support | agree-fail (TP) | vision-only (FP) | subagent-only (FN) |"
             " agree-pass (TN) | Recall | Precision | Verdict |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for g in GROUP_ORDER:
        s = per_group[g]
        if s["verdict"] == "no-signal":
            continue
        L.append(f"| {g} | {s['support']} | {s['tp']} | {s['fp']} | {s['fn']} | {s['tn']} |"
                 f" {pct(s['recall'])} | {pct(s['precision'])} | {s['verdict']} |")
    L.append("")

    dis_v = [r for r in panel_rows if r["vision_only"]]
    dis_s = [r for r in panel_rows if r["subagent_only"]]
    L.append(f"## Disagreements — vision-only flags ({len(dis_v)} panels)")
    L.append("")
    L.append("Vision flagged a group the banked verdict didn't. Each is either a vision false")
    L.append("positive or a defect that ESCAPED the banked QA — the drill-down below says which")
    L.append("after human/orchestrator review of the flagged panels.")
    L.append("")
    L.append("| Panel | Image | Vision-only groups | Vision reason (first) |")
    L.append("|---|---|---|---|")
    for r in dis_v:
        reasons = [f["reason"] for f in vision[r["panel_id"]]["flags"]
                   if set(f["groups"]) & set(r["vision_only"])]
        L.append(f"| `{r['panel_id']}` | `{r['image']}` | {', '.join(r['vision_only'])} |"
                 f" {(reasons[0] if reasons else '')[:160]} |")
    L.append("")
    L.append(f"## Disagreements — subagent-only flags ({len(dis_s)} panels)")
    L.append("")
    L.append("The banked verdict recorded a defect group the shadow missed (vision false")
    L.append("negatives — these cap recall).")
    L.append("")
    L.append("| Panel | Image | Missed groups | GT severity | GT issue |")
    L.append("|---|---|---|---|---|")
    for r in dis_s:
        L.append(f"| `{r['panel_id']}` | `{r['image']}` | {', '.join(r['subagent_only'])} |"
                 f" {r['gt_severity'] or '—'} | {r['gt_issue'][:140]} |")
    L.append("")
    L.append("## Full panel matrix")
    L.append("")
    L.append("| Panel | GT groups (sev) | Vision groups | agree-fail | vision-only | subagent-only |")
    L.append("|---|---|---|---|---|---|")
    for r in panel_rows:
        sev = f" ({r['gt_severity']})" if r["gt_severity"] else ""
        L.append(f"| `{r['panel_id']}` | {', '.join(r['gt_groups']) or 'clean'}{sev} |"
                 f" {', '.join(r['vision_groups']) or 'clean'} |"
                 f" {', '.join(r['agree_fail']) or '—'} | {', '.join(r['vision_only']) or '—'} |"
                 f" {', '.join(r['subagent_only']) or '—'} |")
    L.append("")
    if plan.get("report_gt"):
        L.append("## Appendix — parsed ground truth (auditable keyword mapping)")
        L.append("")
        L.append("| Panel | Severity | Registry IDs | Groups | Issue (source row) |")
        L.append("|---|---|---|---|---|")
        for pid in sorted(gt):
            g = gt[pid]
            L.append(f"| `{pid}` | {g['severity']} | {', '.join(g['registry_ids'])} |"
                     f" {', '.join(g['groups'])} | {g['issue'][:140]} |")
        L.append("")
    for fn in args.footnote or []:
        L.append(f"> {fn}")
    L.append("")
    (project / "qa" / "vision-shadow-report.md").write_text("\n".join(L))
    print(json.dumps({"report": str((project / 'qa' / 'vision-shadow-report.md').relative_to(REPO_ROOT)),
                      "agreement_json": str((shadow_dir / 'agreement.json').relative_to(REPO_ROOT)),
                      "panel_level": metrics["panel_level"]}, indent=2))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("plan", help="walk banked logs, emit rubric + batch manifests")
    p.add_argument("--project", required=True)
    p.add_argument("--log", action="append", required=True,
                   help="log file name relative to project (repeatable)")
    p.add_argument("--batch-size", type=int, default=8)
    p.add_argument("--report-gt", default=None,
                   help="use this qa-report.md defect table as ground truth instead of chain verdicts")
    p.set_defaults(func=cmd_plan)

    p = sub.add_parser("ingest", help="normalize raw subagent verdicts into advisory receipts")
    p.add_argument("--project", required=True)
    p.add_argument("--model-note", default="claude subagent (vision)")
    p.set_defaults(func=cmd_ingest)

    p = sub.add_parser("report", help="agreement analysis vs banked ground truth")
    p.add_argument("--project", required=True)
    p.add_argument("--footnote", action="append", default=[])
    p.set_defaults(func=cmd_report)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
