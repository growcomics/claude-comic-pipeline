#!/usr/bin/env python3
"""Generate the Studio defect-taxonomy PHP include from the canonical registry JSON.

Canonical source: ../references/defect-registry.json (edit that + DEFECT-REGISTRY.md).
Output:           studio/inc/defect-taxonomy.php  (GENERATED — never hand-edit)

The include carries:
  $DEFECT_TAXONOMY  id => [slug, label, category, category_label, severity, pick]
  $DEFECT_CATEGORIES  category => label (picker group headers, registry order)
  $DEFECT_CK_MAP    live ck_ai_qa enum type => canonical id (anachronism maps to
                    PROP-01 here; inc/defects.php refines to PROP-02 when the defect
                    detail names a reference sheet)
  $DEFECT_ID_BY_SLUG  slug => id

Also: --checklist prints the ck_qa_checklist() lines derivable from the registry
(vision=live -> current wording; vision=feasible -> proposed Phase-2 additions), so
the scanner checklist can be regenerated instead of hand-drifted.

Usage:
  python3 gen_defect_taxonomy.py            # validate + write the PHP include
  python3 gen_defect_taxonomy.py --check    # validate only (CI-style), no write
  python3 gen_defect_taxonomy.py --checklist
"""
import json, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "references", "defect-registry.json")
OUT = os.path.join(HERE, "..", "..", "..", "studio", "inc", "defect-taxonomy.php")

SEVERITIES = {"blocker", "major", "minor"}
FREQUENCIES = {"VH", "H", "M", "L"}
VISIONS = {"live", "feasible", "partial", "no"}


def load():
    with open(SRC, encoding="utf-8") as f:
        data = json.load(f)
    cats = data["_meta"]["categories"]
    defects = data["defects"]
    errs = []
    seen_id, seen_slug = set(), set()
    for d in defects:
        did = d.get("id", "?")
        for field in ("id", "slug", "label", "category", "severity", "frequency", "vision", "pick"):
            if field not in d:
                errs.append(f"{did}: missing field '{field}'")
        if d["id"] in seen_id:
            errs.append(f"duplicate id {d['id']}")
        if d["slug"] in seen_slug:
            errs.append(f"duplicate slug {d['slug']} ({did})")
        seen_id.add(d["id"]); seen_slug.add(d["slug"])
        if d["category"] not in cats:
            errs.append(f"{did}: unknown category {d['category']}")
        if d["severity"] not in SEVERITIES:
            errs.append(f"{did}: bad severity {d['severity']}")
        if d["frequency"] not in FREQUENCIES:
            errs.append(f"{did}: bad frequency {d['frequency']}")
        if d["vision"] not in VISIONS:
            errs.append(f"{did}: bad vision {d['vision']}")
        if d["vision"] == "live" and not d.get("ck_type"):
            errs.append(f"{did}: vision=live requires ck_type")
        if d["vision"] in ("feasible", "live") and d.get("scanner_line") is None and d["id"] != "MISC-00":
            errs.append(f"{did}: vision={d['vision']} should carry a scanner_line")
    if errs:
        for e in errs:
            print("VALIDATION:", e, file=sys.stderr)
        sys.exit(1)
    return cats, defects


def php_str(s):
    return "'" + s.replace("\\", "\\\\").replace("'", "\\'") + "'"


def emit_php(cats, defects):
    lines = []
    lines.append("<?php")
    lines.append("// defect-taxonomy.php — GENERATED from claude-comic-pipeline")
    lines.append("//   skills/comic-production/references/defect-registry.json")
    lines.append("//   by skills/comic-production/scripts/gen_defect_taxonomy.py")
    lines.append("// DO NOT HAND-EDIT — regenerate and redeploy instead.")
    lines.append("// Marker for DEPLOY-NOTES greps: DEFECT_TAXONOMY")
    lines.append("declare(strict_types=1);")
    lines.append("")
    lines.append("$DEFECT_CATEGORIES = [")
    for k, v in cats.items():
        lines.append(f"    {php_str(k)} => {php_str(v)},")
    lines.append("];")
    lines.append("")
    lines.append("$DEFECT_TAXONOMY = [")
    for d in defects:
        lines.append(
            "    %s => ['slug'=>%s, 'label'=>%s, 'cat'=>%s, 'sev'=>%s, 'pick'=>%s]," % (
                php_str(d["id"]), php_str(d["slug"]), php_str(d["label"]),
                php_str(d["category"]), php_str(d["severity"]),
                "true" if d["pick"] else "false",
            )
        )
    lines.append("];")
    lines.append("")
    ck_map = {}
    for d in defects:
        ck = d.get("ck_type")
        if ck and ck not in ck_map:  # first (primary) mapping wins; defects.php refines anachronism
            ck_map[ck] = d["id"]
    lines.append("$DEFECT_CK_MAP = [")
    for ck, did in ck_map.items():
        lines.append(f"    {php_str(ck)} => {php_str(did)},")
    lines.append("];")
    lines.append("")
    lines.append("$DEFECT_ID_BY_SLUG = [];")
    lines.append("foreach ($DEFECT_TAXONOMY as $ck_did => $ck_dd) { $DEFECT_ID_BY_SLUG[$ck_dd['slug']] = $ck_did; }")
    lines.append("unset($ck_did, $ck_dd);")
    lines.append("")
    return "\n".join(lines) + "\n"


def main():
    cats, defects = load()
    if "--checklist" in sys.argv:
        print("// ck_qa_checklist() lines derivable from the registry")
        print("// -- LIVE today --")
        for d in defects:
            if d["vision"] == "live" and d.get("scanner_line"):
                print(d["scanner_line"])
        print("// -- PROPOSED Phase-2 additions (vision=feasible) --")
        for d in defects:
            if d["vision"] == "feasible" and d.get("scanner_line"):
                print(d["scanner_line"])
        return
    if "--check" in sys.argv:
        print(f"OK: {len(defects)} defect classes validate clean")
        return
    php = emit_php(cats, defects)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(php)
    print(f"OK: wrote {os.path.relpath(OUT, os.path.join(HERE, '..', '..', '..'))} "
          f"({len(defects)} classes, {len(cats)} categories)")


if __name__ == "__main__":
    main()
