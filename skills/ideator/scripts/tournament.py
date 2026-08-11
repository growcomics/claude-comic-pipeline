#!/usr/bin/env python3
"""tournament.py — the ideator's concept tournament (Stage 1). ENGINE BUILT.

Architecture rule: **judgment in Claude, mechanics in Python.**

The stub this replaced imagined generate_concepts()/score_concept() as Python
functions. That was the wrong shape: concept generation and rubric scoring are
JUDGMENT, and judgment lives in Claude (the session running the skill), not in
a subprocess. What Python owns is everything mechanical around that judgment —
feedstock digestion, the dedup memory, schema enforcement, scoring arithmetic,
ranking, archival — so Claude can never fudge the math, skip the schema, or
"forget" what prior slates already pitched.

The engine is a four-step checkpoint harness (SKILL.md walks the workflow):

  1. brief     -> emits the generation brief: seed, angle quotas, feedstock
                  status (graceful degrade when analytics/catalog are absent),
                  roster, and fingerprints of every concept in prior slates
                  (the dedup memory). Claude reads it + the cited feedstock
                  files, then GENERATES the draft slate (>= per-angle per
                  angle, deliberately different starting angles).
  2. ingest    -> validates the draft: per-concept schema conformance, angle
                  quotas, concept_id uniqueness, near-dupe detection vs prior
                  slates AND within the slate, F1 growth-ratio floors, cast
                  consistency. Exit 2 on failures with a precise report.
                  Claude then SCORES each concept against references/rubric.md
                  (read verbatim — canonical-rubric rule).
  3. finalize  -> re-runs every ingest check, requires all 7 axis scores,
                  recomputes weighted_total itself (Claude's arithmetic is
                  never trusted), ranks, enforces the flat-slate guard, stamps
                  + validates the full slate, writes concepts.json, and
                  archives a copy into slates/ (tomorrow's dedup memory).
                  Prints the top-3 table for the human gate.
  4. select    -> records the user's pick into selected_concept_id.
                  NEVER auto-selects — the human gate is the point.

Contract: concepts.json conforms to references/concept-schema.json — the
Ideator->Writer handoff (docs/PRODUCTION-SYSTEM-VISION.md §4). Scores are
produced against references/rubric.md (7 weighted axes; weights mirrored in
AXIS_WEIGHTS below).

Usage:
    tournament.py brief [--seed "..."] [--per-angle 2] [--out brief.json]
    tournament.py ingest --draft draft.json [--per-angle 2]
    tournament.py finalize --draft draft.json --out concepts.json [--seed "..."]
    tournament.py select --slate concepts.json --concept-id <id>
    tournament.py validate --slate concepts.json
    tournament.py print-contract
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL_ROOT = HERE.parent
SCHEMA_PATH = SKILL_ROOT / "references" / "concept-schema.json"
RUBRIC_PATH = SKILL_ROOT / "references" / "rubric.md"
SLATES_DIR = SKILL_ROOT / "slates"
ROSTER_PATH = SKILL_ROOT / "roster.json"

# Feedstock locations (relative to the repo root, two levels up from skills/).
REPO_ROOT = SKILL_ROOT.parent.parent
CORPUS_SYNTHESIS = REPO_ROOT / "research" / "comic-corpus" / "synthesis" / "success-elements.md"
CATALOG_DIR = REPO_ROOT / "research" / "comic-corpus" / "catalog"
CATALOG_SYNTHESIS = CATALOG_DIR / "SYNTHESIS.md"
CATALOG_SERIES = CATALOG_DIR / "series.json"
GRIBBLE_FORMULA = REPO_ROOT / "research" / "gribble-corpus" / "FORMULA.md"

SCHEMA_VERSION = "1.0"
RUBRIC_VERSION = "1.0"

# The four deliberately-different starting angles (SKILL.md "generation angles").
ANGLES = (
    "transformation-flavor-first",
    "character-first",
    "setting-first",
    "hook-first",
)

# Rubric axis weights — MUST stay in sync with references/rubric.md.
AXIS_WEIGHTS = {
    "growth_payoff_density": 3,
    "story_spine": 3,
    "hook": 2,
    "camera_staging_potential": 2,
    "cast_reuse": 1,
    "novelty": 1,
    "production_economy": 1,
}

# Corpus F1 growth-ratio floors by chapter type (success-elements.md Finding 1).
F1_FLOORS = {"transformation": 0.60, "climax": 0.70, "action": 0.30}

# Dedup thresholds (token-Jaccard on title+logline).
DEDUP_WARN = 0.35
DEDUP_FAIL = 0.50

# Flat-slate guard: a slate whose weighted totals barely differ carries no
# ranking information ("a flat slate where everything scores 4 is useless").
FLAT_STDEV_MIN = 4.0
FLAT_RANGE_MIN = 8.0

_STOPWORDS = {
    "the", "a", "an", "of", "and", "or", "to", "in", "on", "for", "with",
    "her", "his", "she", "he", "it", "its", "is", "at", "by", "as", "vs",
    "into", "from", "that", "who", "when", "one", "two", "gets", "but",
}


# --- feedstock -------------------------------------------------------------

def load_feedstock(roster_path: Path = ROSTER_PATH) -> dict:
    """Gather everything the tournament grounds in. Mechanical: reads files,
    reshapes numbers, reports what's missing. Degrades gracefully — the
    tournament runs corpus-only until the analytics flywheel exists."""
    fs: dict = {"missing": [], "files": {}}

    def _file(key: str, path: Path, required_note: str | None = None):
        if path.exists():
            fs["files"][key] = str(path)
        else:
            fs["missing"].append(f"{key} ({path})" + (f" — {required_note}" if required_note else ""))

    _file("corpus_findings", CORPUS_SYNTHESIS, "the ground truth; generation is weakly grounded without it")
    _file("catalog_synthesis", CATALOG_SYNTHESIS)
    _file("gribble_formula", GRIBBLE_FORMULA)
    _file("rubric", RUBRIC_PATH)
    _file("schema", SCHEMA_PATH)

    # Catalog series digest (top series by installments — revealed preference).
    fs["catalog_top_series"] = []
    if CATALOG_SERIES.exists():
        series = json.loads(CATALOG_SERIES.read_text())
        top = sorted(series.items(), key=lambda kv: -kv[1]["installments"])[:8]
        fs["catalog_top_series"] = [
            {"series": k, "installments": v["installments"],
             "total_page_images": v["total_page_images"],
             "total_comments": v["total_comments"]}
            for k, v in top
        ]
    else:
        fs["missing"].append(f"catalog series index ({CATALOG_SERIES})")

    # Roster: locked characters + locations (cheap reuse).
    fs["roster"] = {"characters": [], "locations": []}
    if roster_path.exists():
        roster = json.loads(roster_path.read_text())
        fs["roster"]["characters"] = roster.get("characters", [])
        fs["roster"]["locations"] = roster.get("locations", [])
    else:
        fs["missing"].append(f"roster ({roster_path}) — pass locked characters by hand")

    # Analytics flywheel: not live yet (vision §5). Always reported so the
    # degrade is visible, never silent.
    fs["analytics"] = None
    fs["missing"].append("publisher analytics (flywheel not live — corpus + catalog stand in)")
    return fs


def load_prior_concepts(slates_dir: Path = SLATES_DIR) -> list[dict]:
    """The dedup memory: every concept in every archived slate."""
    prior: list[dict] = []
    if not slates_dir.exists():
        return prior
    for f in sorted(slates_dir.glob("*.json")):
        try:
            slate = json.loads(f.read_text())
        except json.JSONDecodeError:
            continue
        for c in slate.get("concepts", []):
            prior.append({
                "concept_id": c.get("concept_id", "?"),
                "title": c.get("title", ""),
                "logline": c.get("logline", ""),
                "slate": f.name,
            })
    return prior


# --- dedup mechanics -------------------------------------------------------

def _tokens(*texts: str) -> set[str]:
    toks = set()
    for t in texts:
        for w in re.split(r"[^a-z0-9]+", (t or "").lower()):
            if len(w) >= 3 and w not in _STOPWORDS:
                toks.add(w)
    return toks


def similarity(a: dict, b: dict) -> float:
    """Token-set Jaccard over title+logline. Mechanical near-dupe signal."""
    ta = _tokens(a.get("title", ""), a.get("logline", ""))
    tb = _tokens(b.get("title", ""), b.get("logline", ""))
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def dedup_report(concepts: list[dict], prior: list[dict]) -> list[dict]:
    """Flag near-dupes: new-vs-prior-slates and new-vs-new (intra-slate)."""
    hits = []
    for c in concepts:
        for p in prior:
            s = similarity(c, p)
            if s >= DEDUP_WARN:
                hits.append({
                    "kind": "prior", "a": c.get("concept_id", "?"),
                    "b": f"{p['concept_id']} ({p['slate']})", "sim": round(s, 2),
                    "level": "fail" if s >= DEDUP_FAIL else "warn",
                })
    for i, c1 in enumerate(concepts):
        for c2 in concepts[i + 1:]:
            s = similarity(c1, c2)
            if s >= DEDUP_WARN:
                hits.append({
                    "kind": "intra", "a": c1.get("concept_id", "?"),
                    "b": c2.get("concept_id", "?"), "sim": round(s, 2),
                    "level": "fail" if s >= DEDUP_FAIL else "warn",
                })
    return hits


# --- schema + lint mechanics ----------------------------------------------

def _concept_schema() -> dict:
    schema = json.loads(SCHEMA_PATH.read_text())
    return {"definitions": schema["definitions"], "$ref": "#/definitions/concept"}


def validate_concept(concept: dict) -> list[str]:
    """One concept against the schema's concept definition. Uses jsonschema if
    installed; always also runs the structural checks (better messages)."""
    errs: list[str] = []
    cid = concept.get("concept_id", "?")
    try:
        import jsonschema  # type: ignore
        v = jsonschema.Draft7Validator(_concept_schema())
        for e in v.iter_errors(concept):
            errs.append(f"[{cid}] schema: {'/'.join(str(p) for p in e.path) or '<root>'}: {e.message}")
    except ModuleNotFoundError:
        req = ["concept_id", "title", "logline", "premise", "transformation",
               "cast", "setting", "hook", "est_page_count", "generation_angle"]
        for k in req:
            if k not in concept:
                errs.append(f"[{cid}] missing required field '{k}'")
    if concept.get("generation_angle") not in ANGLES:
        errs.append(f"[{cid}] generation_angle {concept.get('generation_angle')!r} not one of {ANGLES}")
    return errs


def lint_concepts(concepts: list[dict], per_angle: int) -> tuple[list[str], list[str]]:
    """All mechanical checks short of scoring. Returns (errors, warnings)."""
    errors: list[str] = []
    warnings: list[str] = []

    ids = [c.get("concept_id", "?") for c in concepts]
    for dup in {i for i in ids if ids.count(i) > 1}:
        errors.append(f"duplicate concept_id '{dup}'")

    for c in concepts:
        errors.extend(validate_concept(c))

    # Angle quotas: every angle contributes, so the slate isn't one thought.
    by_angle: dict[str, int] = {a: 0 for a in ANGLES}
    for c in concepts:
        a = c.get("generation_angle")
        if a in by_angle:
            by_angle[a] += 1
    for a, n in by_angle.items():
        if n < per_angle:
            errors.append(f"angle '{a}' has {n} concepts, needs >= {per_angle}")

    for c in concepts:
        cid = c.get("concept_id", "?")
        # F1 floors: a concept declaring a growth ratio under its chapter-type
        # floor is fighting the corpus — flag it (warn: the ratio is an estimate).
        floor = F1_FLOORS.get(c.get("chapter_type", ""))
        ratio = c.get("est_growth_page_ratio")
        if floor and isinstance(ratio, (int, float)) and ratio < floor:
            warnings.append(
                f"[{cid}] est_growth_page_ratio {ratio} under the F1 floor "
                f"{floor} for chapter_type '{c.get('chapter_type')}'")
        # Cast consistency.
        cast = c.get("cast", [])
        if "cast_size" in c and c["cast_size"] != len(cast):
            warnings.append(f"[{cid}] cast_size {c['cast_size']} != len(cast) "
                            f"{len(cast)} (finalize will recompute)")
        for m in cast:
            if m.get("reuse") and m.get("ref_status") == "new":
                warnings.append(f"[{cid}] cast '{m.get('name')}' is reuse=true "
                                f"but ref_status=new — pick one")
    return errors, warnings


def lint_scores(concepts: list[dict]) -> list[str]:
    errors = []
    for c in concepts:
        cid = c.get("concept_id", "?")
        scores = c.get("scores")
        if not isinstance(scores, dict):
            errors.append(f"[{cid}] has no scores{{}} — score against {RUBRIC_PATH.name} first")
            continue
        for axis in AXIS_WEIGHTS:
            v = scores.get(axis)
            if not isinstance(v, int) or not (0 <= v <= 5):
                errors.append(f"[{cid}] scores.{axis} = {v!r} (need int 0-5)")
    return errors


def flat_slate_check(concepts: list[dict]) -> tuple[list[str], list[str]]:
    """The rubric's own mandate, mechanized: 'a flat slate where everything
    scores 4 is useless. Spread the scores.'"""
    errors, warnings = [], []
    totals = [c["weighted_total"] for c in concepts]
    if len(totals) >= 3:
        spread = max(totals) - min(totals)
        stdev = statistics.pstdev(totals)
        if stdev < FLAT_STDEV_MIN or spread < FLAT_RANGE_MIN:
            errors.append(
                f"flat slate: weighted totals stdev {stdev:.1f} (min {FLAT_STDEV_MIN}), "
                f"range {spread:.1f} (min {FLAT_RANGE_MIN}) — re-score with "
                f"discrimination or pass --allow-flat")
    for axis in AXIS_WEIGHTS:
        vals = {c["scores"][axis] for c in concepts if "scores" in c}
        if len(vals) == 1:
            warnings.append(f"axis '{axis}' scored identically ({vals.pop()}) across "
                            f"the whole slate — it discriminated nothing")
    return errors, warnings


# --- scoring math, ranking, emit (mechanics only) --------------------------

def weighted_total(scores: dict[str, int]) -> float:
    """Normalize per-axis 0-5 scores to 0-100 by the rubric weights."""
    raw = sum(scores.get(axis, 0) * w for axis, w in AXIS_WEIGHTS.items())
    return round(100 * raw / (5 * sum(AXIS_WEIGHTS.values())), 1)


def build_slate(seed: str | None, concepts: list[dict], roster: list[dict],
                generated_at: str) -> dict:
    ranking = [c["concept_id"] for c in concepts]
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "seed": seed,
        "rubric_version": RUBRIC_VERSION,
        "corpus_synthesis_version": "success-elements v2 + catalog C1-C6 v1",
        "roster_snapshot": roster,
        "concepts": concepts,
        "ranking": ranking,
        "top3": ranking[:3],
        "selected_concept_id": None,
    }


def validate_slate_obj(slate: dict) -> list[str]:
    errs: list[str] = []
    schema = json.loads(SCHEMA_PATH.read_text())
    try:
        import jsonschema  # type: ignore
        v = jsonschema.Draft7Validator(schema)
        for e in v.iter_errors(slate):
            errs.append(f"schema: {'/'.join(str(p) for p in e.path) or '<root>'}: {e.message}")
    except ModuleNotFoundError:
        errs.extend(f"missing required key '{k}'"
                    for k in schema.get("required", []) if k not in slate)
    # Weighted totals must be OUR arithmetic, not asserted numbers.
    for c in slate.get("concepts", []):
        if "scores" in c and "weighted_total" in c:
            want = weighted_total(c["scores"])
            if abs(c["weighted_total"] - want) > 0.05:
                errs.append(f"[{c.get('concept_id', '?')}] weighted_total "
                            f"{c['weighted_total']} != recomputed {want}")
    return errs


def _slug(s: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (s or "unseeded").lower()).strip("-") or "unseeded"


def _utcnow() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


# --- commands --------------------------------------------------------------

def cmd_brief(args) -> int:
    fs = load_feedstock(Path(args.roster) if args.roster else ROSTER_PATH)
    prior = load_prior_concepts()
    lines: list[str] = []
    w = lines.append
    w(f"# Tournament brief — {'seed: ' + repr(args.seed) if args.seed else 'UNSEEDED (surprise me)'}")
    w("")
    w(f"Generate **>= {args.per_angle} concepts per angle** across the 4 angles "
      f"(>= {args.per_angle * len(ANGLES)} total), as a JSON draft:")
    w('`{"seed": <seed-or-null>, "concepts": [<concept>, ...]}` — each concept')
    w(f"conforming to the `concept` definition in `{SCHEMA_PATH}`.")
    w("")
    w("## Angles (each seeds a DIFFERENT region of the idea space)")
    for a in ANGLES:
        w(f"- `{a}`")
    w("")
    w("## Feedstock — READ these before generating (ground every concept)")
    for key, path in fs["files"].items():
        w(f"- {key}: `{path}`")
    if fs["missing"]:
        w("")
        w("## Degraded / absent feedstock (proceed without — never silently)")
        for m in fs["missing"]:
            w(f"- MISSING: {m}")
    if fs["catalog_top_series"]:
        w("")
        w("## Catalog top series (revealed continuation preference — C1)")
        for s in fs["catalog_top_series"]:
            w(f"- {s['series']}: {s['installments']} installments, "
              f"{s['total_page_images']} page-images, {s['total_comments']} comments")
    ro = fs["roster"]
    if ro["characters"]:
        w("")
        w("## Locked roster (cast reuse is CHEAP — prefer it; axis 5)")
        for c in ro["characters"]:
            w(f"- {c['name']} ({c.get('project', '?')}, {c.get('ref_status', '?')})"
              + (f" — {c['notes']}" if c.get("notes") else ""))
        for loc in ro["locations"]:
            w(f"- [location] {loc['name']} ({loc.get('project', '?')}, {loc.get('ref_status', '?')})")
    w("")
    if prior:
        w(f"## Prior-slate concepts ({len(prior)}) — do NOT near-duplicate these")
        for p in prior:
            w(f"- {p['concept_id']} [{p['slate']}]: {p['title']} — {p['logline']}")
    else:
        w("## Prior-slate concepts: none (first slate — dedup memory is empty)")
    w("")
    w("## Rules")
    w(f"- Chapter-type growth floors (F1): {F1_FLOORS} — set `est_growth_page_ratio` at/above the floor.")
    w("- Named cast only, no background extras; prefer locked roster (reuse=true, ref_status from roster).")
    w("- `corpus_grounding`: cite the findings each concept leans on (F1-F6, C1-C6).")
    w("- Do NOT fill `scores`/`weighted_total` yet — scoring is a separate pass "
      "against the rubric AFTER `ingest` passes.")
    w("")
    w(f"Next: write the draft, then `tournament.py ingest --draft <file> --per-angle {args.per_angle}`")
    print("\n".join(lines))
    if args.out:
        Path(args.out).write_text(json.dumps({
            "seed": args.seed, "per_angle": args.per_angle, "angles": list(ANGLES),
            "feedstock": fs, "prior_concepts": prior,
        }, indent=2) + "\n")
        print(f"\n(machine brief -> {args.out})", file=sys.stderr)
    return 0


def _load_draft(path: Path) -> tuple[str | None, list[dict]]:
    data = json.loads(path.read_text())
    if isinstance(data, list):
        return None, data
    return data.get("seed"), data.get("concepts", [])


def cmd_ingest(args) -> int:
    seed, concepts = _load_draft(Path(args.draft))
    errors, warnings = lint_concepts(concepts, args.per_angle)
    dedup = dedup_report(concepts, load_prior_concepts())
    for h in dedup:
        line = (f"near-dupe ({h['kind']}) {h['a']} ~ {h['b']} sim={h['sim']}")
        (errors if h["level"] == "fail" else warnings).append(line)

    print(f"draft: {len(concepts)} concepts, seed={seed!r}")
    for msg in warnings:
        print(f"  WARN: {msg}")
    for msg in errors:
        print(f"  FAIL: {msg}")
    if errors:
        print(f"\nINGEST FAILED ({len(errors)} errors). Fix the draft and re-run.")
        return 2
    print(f"\nINGEST OK ({len(warnings)} warnings). Next: score every concept "
          f"against `{RUBRIC_PATH}` — read it VERBATIM (canonical-rubric rule), "
          f"fill `scores` (7 axes, int 0-5) + `score_rationale`, spread the "
          f"scores, then run finalize.")
    return 0


def cmd_finalize(args) -> int:
    draft_path = Path(args.draft)
    seed, concepts = _load_draft(draft_path)
    if args.seed is not None:
        seed = args.seed

    errors, warnings = lint_concepts(concepts, args.per_angle)
    dedup = dedup_report(concepts, load_prior_concepts())
    for h in dedup:
        line = f"near-dupe ({h['kind']}) {h['a']} ~ {h['b']} sim={h['sim']}"
        if h["level"] == "fail" and not args.allow_dupes:
            errors.append(line)
        else:
            warnings.append(line)
    errors.extend(lint_scores(concepts))
    if errors:
        for msg in errors:
            print(f"  FAIL: {msg}")
        print(f"\nFINALIZE REFUSED ({len(errors)} errors).")
        return 2

    # Mechanics own the arithmetic and the derived fields.
    for c in concepts:
        c["cast_size"] = len(c.get("cast", []))
        c["weighted_total"] = weighted_total(c["scores"])
    concepts.sort(key=lambda c: c["weighted_total"], reverse=True)

    flat_errs, flat_warns = flat_slate_check(concepts)
    warnings.extend(flat_warns)
    if flat_errs and not args.allow_flat:
        for msg in flat_errs:
            print(f"  FAIL: {msg}")
        return 2

    fs = load_feedstock(Path(args.roster) if args.roster else ROSTER_PATH)
    roster_snapshot = [
        {"name": c["name"], "project": c.get("project", ""),
         "ref_status": c.get("ref_status", "locked")}
        for c in fs["roster"]["characters"]
    ]
    now = _utcnow()
    slate = build_slate(seed, concepts, roster_snapshot,
                        now.isoformat(timespec="seconds"))

    slate_errs = validate_slate_obj(slate)
    if slate_errs:
        for msg in slate_errs:
            print(f"  FAIL: {msg}")
        return 2

    out = Path(args.out)
    out.write_text(json.dumps(slate, indent=2, ensure_ascii=False) + "\n")
    archived = None
    if not args.no_archive:
        SLATES_DIR.mkdir(exist_ok=True)
        archived = SLATES_DIR / f"{now.strftime('%Y%m%dT%H%M%SZ')}-{_slug(seed)}.concepts.json"
        archived.write_text(out.read_text())

    for msg in warnings:
        print(f"  WARN: {msg}")
    print(f"\nFINALIZED: {len(concepts)} concepts -> {out}"
          + (f" (archived: {archived.name})" if archived else ""))
    print("\nTOP 3 (surface these at the human gate — never auto-select):")
    for c in concepts[:3]:
        s = c["scores"]
        axes = " ".join(f"{k.split('_')[0][:4]}={s[k]}" for k in AXIS_WEIGHTS)
        print(f"  {c['weighted_total']:5.1f}  {c['concept_id']:32s} [{c['generation_angle']}] {axes}")
        print(f"         {c['logline']}")
    print(f"\nNext: user picks, then `tournament.py select --slate {out} --concept-id <id>`")
    return 0


def cmd_select(args) -> int:
    path = Path(args.slate)
    slate = json.loads(path.read_text())
    ids = [c["concept_id"] for c in slate.get("concepts", [])]
    if args.concept_id not in ids:
        print(f"FAIL: '{args.concept_id}' not in slate ({', '.join(ids)})")
        return 2
    slate["selected_concept_id"] = args.concept_id
    path.write_text(json.dumps(slate, indent=2, ensure_ascii=False) + "\n")
    # Keep the archived copy in sync (matched by generated_at).
    if SLATES_DIR.exists():
        for f in SLATES_DIR.glob("*.json"):
            try:
                arch = json.loads(f.read_text())
            except json.JSONDecodeError:
                continue
            if arch.get("generated_at") == slate.get("generated_at"):
                arch["selected_concept_id"] = args.concept_id
                f.write_text(json.dumps(arch, indent=2, ensure_ascii=False) + "\n")
    print(f"SELECTED: {args.concept_id} (the Writer reads this from {path.name})")
    return 0


def cmd_validate(args) -> int:
    slate = json.loads(Path(args.slate).read_text())
    errs = validate_slate_obj(slate)
    for c in slate.get("concepts", []):
        errs.extend(validate_concept(c))
    if errs:
        for msg in errs:
            print(f"  FAIL: {msg}")
        return 2
    print(f"OK: {args.slate} validates ({len(slate.get('concepts', []))} concepts, "
          f"seed={slate.get('seed')!r}, selected={slate.get('selected_concept_id')!r})")
    return 0


def example_concept() -> dict:
    """A schema-shaped EXAMPLE concept — a documentation fixture, NOT generation."""
    return {
        "concept_id": "example-gym-rivals",
        "title": "(EXAMPLE) Spotter's Honor",
        "logline": "Two gym rivals discover the pre-workout was spiked — and only one of them reads the warning label in time.",
        "premise": "EXAMPLE fixture demonstrating concept-schema.json. Not a real pitch.",
        "transformation": {
            "flavor": "tech/supplement",
            "trigger": "spiked pre-workout, mid-set",
            "arc": "skeptical sip -> creeping pump -> runaway escalation on the squat rack -> peak -> aftermath standoff",
            "peak_state": "the rival towers, the protagonist must choose to drink or not",
            "tier_curve": "tier 2 -> 6",
        },
        "cast": [
            {"name": "PLACEHOLDER-A", "role": "protagonist", "reuse": False, "ref_status": "new"},
            {"name": "PLACEHOLDER-B", "role": "rival", "reuse": False, "ref_status": "new"},
        ],
        "cast_size": 2,
        "setting": "a closed late-night gym",
        "hook": "the warning label is the whole plot",
        "est_page_count": 16,
        "chapter_type": "transformation",
        "est_growth_page_ratio": 0.62,
        "planned_escalation_devices": ["multi-panel-progressive", "clothing-destruction", "size-comparison", "sfx-driven"],
        "generation_angle": "setting-first",
        "why_itll_perform": "EXAMPLE: high growth ratio (F1), built-in size gauge via gym equipment (F4 size-comparison), and a real stakes/choice spine (F5).",
        "corpus_grounding": ["F1 growth-ratio-by-intent", "F4 device-toolkit", "F5 story-as-differentiator"],
        "scores": {
            "growth_payoff_density": 4, "story_spine": 4, "hook": 4,
            "camera_staging_potential": 4, "cast_reuse": 0, "novelty": 3, "production_economy": 3,
        },
        "weighted_total": 0.0,
        "score_rationale": "EXAMPLE only — illustrates the shape, not a real evaluation.",
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Ideator concept tournament — judgment in Claude, mechanics here.")
    sub = p.add_subparsers(dest="cmd")

    b = sub.add_parser("brief", help="emit the generation brief (feedstock + dedup memory)")
    b.add_argument("--seed", default=None)
    b.add_argument("--per-angle", type=int, default=2)
    b.add_argument("--roster", default=None)
    b.add_argument("--out", default=None, help="also write the machine-readable brief JSON")

    i = sub.add_parser("ingest", help="validate a draft slate (schema, quotas, dedup)")
    i.add_argument("--draft", required=True)
    i.add_argument("--per-angle", type=int, default=2)

    f = sub.add_parser("finalize", help="recompute, rank, guard, archive, emit concepts.json")
    f.add_argument("--draft", required=True)
    f.add_argument("--out", required=True)
    f.add_argument("--seed", default=None)
    f.add_argument("--per-angle", type=int, default=2)
    f.add_argument("--roster", default=None)
    f.add_argument("--allow-flat", action="store_true")
    f.add_argument("--allow-dupes", action="store_true")
    f.add_argument("--no-archive", action="store_true")

    s = sub.add_parser("select", help="record the user's pick (the human gate)")
    s.add_argument("--slate", required=True)
    s.add_argument("--concept-id", required=True)

    v = sub.add_parser("validate", help="validate a concepts.json against the schema")
    v.add_argument("--slate", required=True)

    sub.add_parser("print-contract", help="dump a schema-shaped example concept")

    args = p.parse_args(argv)
    if args.cmd == "brief":
        return cmd_brief(args)
    if args.cmd == "ingest":
        return cmd_ingest(args)
    if args.cmd == "finalize":
        return cmd_finalize(args)
    if args.cmd == "select":
        return cmd_select(args)
    if args.cmd == "validate":
        return cmd_validate(args)
    if args.cmd == "print-contract":
        ex = example_concept()
        ex["weighted_total"] = weighted_total(ex["scores"])
        print(json.dumps(ex, indent=2))
        return 0
    p.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
