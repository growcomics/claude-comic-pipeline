#!/usr/bin/env python3
"""tournament.py — the ideator's concept tournament (Stage 1).

╔══════════════════════════════════════════════════════════════════════════╗
║  SHELL ONLY.  The two reasoning steps — generate_concepts() and           ║
║  score_concept() — are STUBS.  They raise NotImplementedError with a       ║
║  `BUILD ME (stronger model)` marker.  Everything around them (feedstock    ║
║  loading, the data shapes, JSON emit, schema validation, the CLI, the      ║
║  orchestration order) is REAL plumbing, so a stronger model can drop the   ║
║  engine in behind a stable contract without re-deriving the scaffold.      ║
║                                                                            ║
║  Do NOT write the generate-and-score logic here as a side effect of some   ║
║  other task.  It is deliberately deferred (see SKILL.md "What's real vs    ║
║  stubbed").  Build it on purpose, with the corpus in context, and ship it  ║
║  with its own CHANGELOG entry + a refreshed PRODUCTION-SYSTEM-VISION §2.    ║
╚══════════════════════════════════════════════════════════════════════════╝

Contract: emits concepts.json conforming to references/concept-schema.json —
the Ideator->Writer handoff (docs/PRODUCTION-SYSTEM-VISION.md §4). Scores are
produced against references/rubric.md (corpus-grounded, 7 weighted axes).

Pipeline (when the engine is built):
    feedstock ─► generate (N per angle) ─► score (rubric) ─► rank ─► top3 ─► emit

Usage (today — shell):
    tournament.py --print-contract        # dump a schema-shaped example concept
    tournament.py --validate concepts.json # validate a slate against the schema
    tournament.py --run --seed "..."       # raises NotImplementedError (engine is a stub)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
SKILL_ROOT = HERE.parent
SCHEMA_PATH = SKILL_ROOT / "references" / "concept-schema.json"
RUBRIC_PATH = SKILL_ROOT / "references" / "rubric.md"

# Default feedstock locations (relative to the repo root, two levels up from skills/).
REPO_ROOT = SKILL_ROOT.parent.parent
CORPUS_SYNTHESIS = REPO_ROOT / "research" / "comic-corpus" / "synthesis" / "success-elements.md"

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


# --- REAL plumbing: feedstock loading --------------------------------------

def load_feedstock(
    corpus_synthesis: Path = CORPUS_SYNTHESIS,
    roster: list[dict] | None = None,
    analytics: Any = None,
) -> dict:
    """Load the inputs the tournament scores against. REAL — no reasoning here.

    Returns a dict the (future) engine consumes:
        {
          "corpus_findings": <text of success-elements.md, the ground truth>,
          "roster": [{name, project, ref_status}, ...],   # locked characters
          "analytics": <future: publisher engagement data, or None>,
        }

    The corpus synthesis is the ground truth until Stage-7 analytics exist.
    """
    findings = corpus_synthesis.read_text() if corpus_synthesis.exists() else ""
    return {
        "corpus_findings": findings,
        "roster": roster or [],
        "analytics": analytics,
    }


# --- STUB: the engine (generation) -----------------------------------------

def generate_concepts(
    seed: str | None,
    feedstock: dict,
    angles: tuple[str, ...] = ANGLES,
    per_angle: int = 2,
) -> list[dict]:
    """Generate the slate: >= `per_angle` concepts per ANGLE, grounded in feedstock.

    BUILD ME (stronger model): the actual generate-from-N-angles loop goes here.
    For each angle, produce `per_angle` concept dicts conforming to the `concept`
    definition in concept-schema.json — logline, transformation arc, cast (prefer
    feedstock["roster"] for cheap reuse), setting, hook, est_page_count,
    chapter_type + est_growth_page_ratio (corpus F1 targets), planned escalation
    devices (F4), generation_angle, why_itll_perform, and corpus_grounding.

    The angles intentionally seed different regions of the idea space so the slate
    isn't N variations of one thought. See SKILL.md "The four generation angles".
    """
    raise NotImplementedError(
        "BUILD ME (stronger model): concept generation is a stub. "
        "See SKILL.md 'What's real vs stubbed'. Until built, produce the slate by hand."
    )


# --- STUB: the engine (scoring) --------------------------------------------

def score_concept(concept: dict, feedstock: dict, rubric_path: Path = RUBRIC_PATH) -> dict:
    """Score ONE concept 0-5 on each rubric axis, against the corpus findings.

    BUILD ME (stronger model): apply references/rubric.md (read it verbatim — do
    not paraphrase, per feedback_dont_paraphrase_canonical_rubrics) to fill
    concept["scores"] for all 7 axes, then concept["weighted_total"] via
    weighted_total(). Be a discerning critic and spread the scores — a flat slate
    is useless. Reward growth-spine (F1) and story-coherence (F5 — the
    differentiation axis) most; they carry the top weight.
    """
    raise NotImplementedError(
        "BUILD ME (stronger model): rubric scoring is a stub. "
        f"Apply {rubric_path.name} by hand until the engine is built."
    )


# --- REAL plumbing: scoring math, ranking, emit, validate ------------------

def weighted_total(scores: dict[str, int]) -> float:
    """Normalize per-axis 0-5 scores to 0-100 by the rubric weights. REAL."""
    raw = sum(scores.get(axis, 0) * w for axis, w in AXIS_WEIGHTS.items())
    return round(100 * raw / (5 * sum(AXIS_WEIGHTS.values())), 1)


def run_tournament(
    seed: str | None = None,
    roster: list[dict] | None = None,
    per_angle: int = 2,
    out: Path | None = None,
) -> dict:
    """Orchestrate: feedstock -> generate -> score -> rank -> top3 -> emit.

    The orchestration order is REAL; it just drives two stubbed steps, so calling
    it today raises NotImplementedError from generate_concepts(). This is the
    function the engine-builder fills out from both ends meeting in the middle.
    """
    feedstock = load_feedstock(roster=roster)
    concepts = generate_concepts(seed, feedstock, per_angle=per_angle)   # STUB
    for c in concepts:                                                   # STUB
        c["scores"] = score_concept(c, feedstock)["scores"]
        c["weighted_total"] = weighted_total(c["scores"])
    concepts.sort(key=lambda c: c.get("weighted_total", 0), reverse=True)
    slate = build_slate(seed, concepts, roster)
    if out:
        emit_concepts_json(slate, out)
    return slate


def build_slate(seed: str | None, concepts: list[dict], roster: list[dict] | None) -> dict:
    """Assemble the top-level concepts.json object. REAL."""
    ranking = [c["concept_id"] for c in concepts]
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": "",  # caller stamps an ISO-8601 time (Date.now is unavailable in some harnesses)
        "seed": seed,
        "rubric_version": RUBRIC_VERSION,
        "corpus_synthesis_version": "success-elements v2",
        "roster_snapshot": roster or [],
        "concepts": concepts,
        "ranking": ranking,
        "top3": ranking[:3],
        "selected_concept_id": None,
    }


def emit_concepts_json(slate: dict, out: Path) -> None:
    """Write the slate to disk. REAL."""
    out.write_text(json.dumps(slate, indent=2) + "\n")


def validate(slate_path: Path) -> bool:
    """Validate a concepts.json against concept-schema.json. REAL.

    Uses jsonschema if installed; otherwise does a minimal required-keys check so
    the shell stays dependency-light.
    """
    slate = json.loads(slate_path.read_text())
    schema = json.loads(SCHEMA_PATH.read_text())
    try:
        import jsonschema  # type: ignore
        jsonschema.validate(slate, schema)
        print(f"OK: {slate_path.name} validates against {SCHEMA_PATH.name} (jsonschema)")
        return True
    except ModuleNotFoundError:
        missing = [k for k in schema.get("required", []) if k not in slate]
        if missing:
            print(f"INVALID: missing required keys {missing}", file=sys.stderr)
            return False
        print(f"OK (shallow — install jsonschema for full validation): {slate_path.name}")
        return True
    except Exception as e:  # noqa: BLE001
        print(f"INVALID: {e}", file=sys.stderr)
        return False


def example_concept() -> dict:
    """A schema-shaped EXAMPLE concept — a documentation fixture, NOT generation.

    Demonstrates the contract shape for readers/tests. Hand-written; the engine
    must produce concepts like this, grounded in real feedstock.
    """
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
        "weighted_total": 0.0,  # caller computes via weighted_total(scores)
        "score_rationale": "EXAMPLE only — illustrates the shape, not a real evaluation.",
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Ideator concept tournament (SHELL — engine stubbed).")
    p.add_argument("--run", action="store_true", help="Run the tournament (raises NotImplementedError — engine is a stub).")
    p.add_argument("--seed", help="The spark to ideate from.")
    p.add_argument("--print-contract", action="store_true", help="Dump a schema-shaped example concept.")
    p.add_argument("--validate", type=Path, help="Validate a concepts.json against the schema.")
    args = p.parse_args(argv)

    if args.print_contract:
        ex = example_concept()
        ex["weighted_total"] = weighted_total(ex["scores"])
        print(json.dumps(ex, indent=2))
        return 0
    if args.validate:
        return 0 if validate(args.validate) else 1
    if args.run:
        run_tournament(seed=args.seed)  # raises NotImplementedError by design
        return 0

    p.print_help()
    print("\nNOTE: this is a SHELL. The generate+score engine is a stub "
          "(`BUILD ME (stronger model)`). See SKILL.md.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
