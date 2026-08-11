"""L38 story-spine gate — one test per corpus failure mode.

The gate is only worth having if it discriminates. A clean shotlist must pass
silently; each of the four failures from research/comic-corpus Finding 5 must
produce a HARD finding on its own. Run: python3 tests/test_story_spine.py
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "continuity-check" / "scripts"))

from rules_audit import SEVERITY_HARD, check_story_spine  # noqa: E402


def _clean() -> dict:
    """A shotlist that satisfies every L38 condition."""
    return {
        "story_spine": {
            "want": "Vesna wants to buy her brother out of the Order's indenture.",
            "obstacle": "The Order only releases a conduit who names a replacement.",
            "cost": "She has to become the thing she was trying to free him from.",
            "promise_page": 1,
            "payoff_page": 4,
            "ending": "landed",
        },
        "cast": [
            {"id": "vesna", "distinguishing_marks": "ember-tipped short coils, burn scar across the left collarbone"},
            {"id": "cantor", "distinguishing_marks": "cold silver-blue eyes, shaved left temple"},
        ],
        "pages": [
            {"page_number": 1, "panels": [
                {"panel_id": "p01-01", "camera": "wide-establish", "characters": ["vesna"],
                 "dialogue": [{"character": "vesna", "text": "Four more years of this."}]},
            ]},
            {"page_number": 2, "panels": [
                {"panel_id": "p02-01", "camera": "ecu-region", "transformation_beat": "chest", "characters": ["vesna"]},
            ]},
            {"page_number": 3, "panels": [
                {"panel_id": "p03-01", "size": "splash", "camera": "full", "transformation_beat": "whole_body",
                 "location": "chapter-hall", "characters": ["vesna", "cantor"]},
                {"panel_id": "p03-02", "size": "wide", "camera": "mcu", "transformation_beat": "reveal",
                 "location": "gantry", "characters": ["vesna"]},
            ]},
            {"page_number": 4, "panels": [
                {"panel_id": "p04-01", "camera": "medium", "transformation_beat": "aftermath",
                 "characters": ["vesna"], "captions": ["The ledger balanced. Just not the way she wrote it."]},
            ]},
        ],
    }


def _hards(shotlist: dict) -> list[str]:
    return [f.message for f in check_story_spine(shotlist) if f.severity == SEVERITY_HARD]


def _check(name: str, shotlist: dict, *, expect_hard: bool) -> bool:
    hards = _hards(shotlist)
    ok = bool(hards) == expect_hard
    print(f"  {'PASS' if ok else 'FAIL'}  {name}"
          f"{'' if ok else f'  -> expected_hard={expect_hard}, got {len(hards)}: {hards[:1]}'}")
    return ok


def main() -> int:
    results: list[bool] = []
    print("L38 story-spine gate")

    results.append(_check("clean shotlist passes", _clean(), expect_hard=False))

    # F5a — thin/absent spine.
    no_spine = _clean()
    del no_spine["story_spine"]
    results.append(_check("F5a missing story_spine", no_spine, expect_hard=True))

    stub = _clean()
    stub["story_spine"]["want"] = "TBD"
    results.append(_check("F5a stub `want` rejected", stub, expect_hard=True))

    thin = _clean()
    thin["story_spine"]["cost"] = "a lot"
    results.append(_check("F5a one-word `cost` rejected", thin, expect_hard=True))

    # F5b — escalation-by-repetition at the climax.
    repeated = _clean()
    repeated["pages"][2]["panels"] = [
        {"panel_id": f"p03-0{i}", "size": "splash", "camera": "full", "transformation_beat": "whole_body",
         "location": "chapter-hall", "characters": ["vesna", "cantor"]}
        for i in (1, 2, 3)
    ]
    results.append(_check("F5b three interchangeable splashes", repeated, expect_hard=True))

    varied = _clean()
    varied["pages"][2]["panels"] = [
        {"panel_id": "p03-01", "size": "splash", "camera": "full", "transformation_beat": "whole_body",
         "location": "chapter-hall", "characters": ["vesna", "cantor"]},
        {"panel_id": "p03-02", "size": "splash", "camera": "wide-establish", "transformation_beat": "whole_body",
         "location": "city-roofline", "characters": ["vesna"]},
        {"panel_id": "p03-03", "size": "splash", "camera": "mcu", "transformation_beat": "reveal",
         "location": "gantry", "characters": ["vesna"]},
    ]
    results.append(_check("F5b varied capstones pass", varied, expect_hard=False))

    # F5c — setup/payoff and the ending.
    inverted = _clean()
    inverted["story_spine"]["payoff_page"] = 1
    inverted["story_spine"]["promise_page"] = 3
    results.append(_check("F5c payoff before promise", inverted, expect_hard=True))

    off_range = _clean()
    off_range["story_spine"]["payoff_page"] = 99
    results.append(_check("F5c payoff page out of range", off_range, expect_hard=True))

    bare_cliff = _clean()
    bare_cliff["story_spine"]["ending"] = "cliffhanger"
    results.append(_check("F5c cliffhanger without hook", bare_cliff, expect_hard=True))

    good_cliff = _clean()
    good_cliff["story_spine"]["ending"] = "cliffhanger"
    good_cliff["story_spine"]["hook"] = "The replacement she named has not been told yet."
    results.append(_check("F5c cliffhanger with hook passes", good_cliff, expect_hard=False))

    mid_swing = _clean()
    mid_swing["pages"][3]["panels"] = [
        {"panel_id": "p04-01", "camera": "medium", "characters": ["vesna"], "action": "She swings."},
    ]
    results.append(_check("F5c final page stops mid-swing", mid_swing, expect_hard=True))

    # F5d — identity confusion at the climax.
    unmarked = _clean()
    del unmarked["cast"][1]["distinguishing_marks"]
    results.append(_check("F5d climax character without marks", unmarked, expect_hard=True))

    twinned = _clean()
    twinned["cast"][1]["distinguishing_marks"] = copy.copy(twinned["cast"][0]["distinguishing_marks"]).upper()
    results.append(_check("F5d identical marks (case-insensitive)", twinned, expect_hard=True))

    solo = _clean()
    solo["cast"] = [solo["cast"][0]]
    solo["pages"][2]["panels"][0]["characters"] = ["vesna"]
    results.append(_check("F5d single-lead climax exempt", solo, expect_hard=False))

    passed, total = sum(results), len(results)
    print(f"\n{passed}/{total} passed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
