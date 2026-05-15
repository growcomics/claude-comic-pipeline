#!/usr/bin/env python3
"""
run_tests.py — Fixture-based + inline unit tests for next_panel.py.

Mirrors skills/continuity-check/tests/run_tests.py. See ./README.md for the
fixture layout and expected.json schema.

Two modes wired into one runner:

  1. Fixtures (tests/fixtures/<name>/) — drive build_plan() against a
     synthetic project root and assert on the composed prompt + the
     refs_to_attach_in_order list.

  2. Inline tests (defined below) — exercise compose_prompt() and the
     helper functions directly with crafted inputs. Faster to write and
     read than fixtures when no on-disk state is needed.

Usage:
  python tests/run_tests.py
  python tests/run_tests.py --fixture <name>
  python tests/run_tests.py --inline-only
  python tests/run_tests.py --fixtures-only
  python tests/run_tests.py --verbose

Exit codes:
  0  all checks passed
  1  one or more checks failed
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
NEXT_PANEL_PATH = SCRIPT_DIR.parent / "scripts" / "next_panel.py"
FIXTURES_DIR = SCRIPT_DIR / "fixtures"

GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
DIM = "\033[2m"
RESET = "\033[0m"


def _import_next_panel():
    spec = importlib.util.spec_from_file_location("next_panel", NEXT_PANEL_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load next_panel.py at {NEXT_PANEL_PATH}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


NP = _import_next_panel()


# ---------------------------------------------------------------------------
# Result reporting

@dataclass
class CheckResult:
    name: str
    passed: bool
    failures: list[str] = field(default_factory=list)
    details: list[str] = field(default_factory=list)


def fmt(r: CheckResult, verbose: bool) -> str:
    head = f"{GREEN}PASS{RESET}" if r.passed else f"{RED}FAIL{RESET}"
    lines = [f"  {head}  {r.name}"]
    for f in r.failures:
        lines.append(f"        {RED}✗{RESET} {f}")
    if verbose:
        for d in r.details:
            lines.append(f"        {DIM}· {d}{RESET}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Fixture runner

def _refs_to_kinds(refs: list[dict]) -> list[str]:
    return [r.get("kind", "?") for r in refs]


def run_fixture(fixture_dir: Path) -> CheckResult:
    name = f"fixture/{fixture_dir.name}"
    expected_path = fixture_dir / "expected.json"
    shotlist_path = fixture_dir / "shotlist.json"
    if not expected_path.exists():
        return CheckResult(name, False, [f"missing expected.json"])
    if not shotlist_path.exists():
        return CheckResult(name, False, [f"missing shotlist.json"])
    expected = json.loads(expected_path.read_text())

    plan = NP.build_plan(fixture_dir)
    failures: list[str] = []
    details: list[str] = []

    if plan.get("error"):
        failures.append(f"build_plan returned error: {plan['error']}")
        return CheckResult(name, False, failures, details)

    if expected.get("expect_no_pending_panels"):
        if plan.get("next_panel") is not None:
            failures.append(
                f"expected no pending panels, got next_panel="
                f"{plan['next_panel'].get('panel_id')}"
            )
        return CheckResult(name, not failures, failures, details)

    np = plan.get("next_panel")
    if np is None:
        failures.append("expected a pending next_panel; got None")
        return CheckResult(name, False, failures, details)

    if "expect_panel_id" in expected:
        if np.get("panel_id") != expected["expect_panel_id"]:
            failures.append(
                f"expected panel_id={expected['expect_panel_id']!r}, "
                f"got {np.get('panel_id')!r}"
            )

    if "expect_stage_change" in expected:
        if plan.get("stage_change") != expected["expect_stage_change"]:
            failures.append(
                f"expected stage_change={expected['expect_stage_change']}, "
                f"got {plan.get('stage_change')}"
            )

    if "expect_aspect" in expected:
        if plan.get("aspect") != expected["expect_aspect"]:
            failures.append(
                f"expected aspect={expected['expect_aspect']!r}, "
                f"got {plan.get('aspect')!r}"
            )

    prompt = plan.get("composed_prompt", "")
    for needle in expected.get("expect_prompt_contains", []):
        if needle not in prompt:
            failures.append(f"prompt missing substring: {needle!r}")
    for needle in expected.get("expect_prompt_not_contains", []):
        if needle in prompt:
            failures.append(f"prompt should NOT contain: {needle!r}")

    refs = plan.get("refs_to_attach_in_order", [])
    kinds = _refs_to_kinds(refs)
    details.append(f"ref kinds in order: {kinds}")

    if "expect_ref_kinds_in_order" in expected:
        want = list(expected["expect_ref_kinds_in_order"])
        if kinds != want:
            failures.append(
                f"expected ref kinds (ordered) {want}, got {kinds}"
            )

    for kind in expected.get("expect_ref_kinds_present", []):
        if kind not in kinds:
            failures.append(f"expected ref kind missing: {kind!r}")

    for kind in expected.get("expect_ref_kinds_absent", []):
        if kind in kinds:
            failures.append(f"ref kind should be absent: {kind!r}")

    return CheckResult(name, not failures, failures, details + [
        f"composed_prompt={prompt[:200]}...",
    ])


# ---------------------------------------------------------------------------
# Inline test helpers

def _minimal_shotlist(cast: list[dict] | None = None,
                     locations: list[dict] | None = None) -> dict:
    return {
        "cast": cast or [],
        "locations": locations or [],
        "pages": [],
    }


def _panel(**overrides) -> dict:
    base = {
        "panel_id": "p1",
        "camera": "3q-full",
        "characters": ["ella"],
        "location": "dojo",
        "action": "stands ready",
        "muscle_size_tier": None,
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Inline tests
#
# Each test fn returns CheckResult. Name starts with "inline/" for clarity in
# the output stream.

def t_compose_style_prefix() -> CheckResult:
    name = "inline/compose_prompt/style_prefix_and_mandatory_rules"
    prompt = NP.compose_prompt(_panel(), _minimal_shotlist(), anchor=None,
                               stage_change=False, env_ref=None)
    fails: list[str] = []
    if "DAZ Studio Iray render" not in prompt:
        fails.append("missing DAZ Studio render anchor")
    if "Mandatory:" not in prompt:
        fails.append("missing mandatory rules block")
    if "Photographic CGI render, NOT illustrated." not in prompt:
        fails.append("missing closing CGI anchor")
    if "RENDER DIRECTIVE:" not in prompt:
        fails.append("missing RENDER DIRECTIVE sentence")
    return CheckResult(name, not fails, fails)


def t_compose_l21_when_refs_attached() -> CheckResult:
    name = "inline/compose_prompt/L21_ref_exclusion_when_any_ref"
    prompt = NP.compose_prompt(_panel(muscle_size_tier=3), _minimal_shotlist(),
                               anchor=None, stage_change=False,
                               env_ref=None, lineup_attached=True)
    fails: list[str] = []
    if "DO NOT render any reference image as a physical scene object" not in prompt:
        fails.append("L21 ref-exclusion clause missing when a ref is attached")
    return CheckResult(name, not fails, fails)


def t_compose_l21_absent_when_no_refs() -> CheckResult:
    name = "inline/compose_prompt/L21_absent_when_zero_refs"
    prompt = NP.compose_prompt(_panel(), _minimal_shotlist(),
                               anchor=None, stage_change=False, env_ref=None,
                               lineup_attached=False)
    fails: list[str] = []
    if "DO NOT render any reference image" in prompt:
        fails.append("L21 fired even with no refs attached")
    return CheckResult(name, not fails, fails)


def t_compose_hair_state_explicit() -> CheckResult:
    name = "inline/compose_prompt/L22_hair_state_explicit"
    panel = _panel(muscle_size_tier=3, hair_state="hair fully down, wild")
    prompt = NP.compose_prompt(panel, _minimal_shotlist(),
                               anchor=None, stage_change=True, env_ref=None,
                               lineup_attached=True)
    fails: list[str] = []
    if "Hair state: hair fully down, wild." not in prompt:
        fails.append("Hair state line not emitted for explicit hair_state")
    return CheckResult(name, not fails, fails)


def t_compose_hair_state_no_auto_derive() -> CheckResult:
    """L23 / memory feedback_dont_invent_state_changes regression: a tier bump
    plus a body-region beat MUST NOT cause compose_prompt to invent a hair
    state. The shotlist author owns this field."""
    name = "inline/compose_prompt/L22_hair_state_NOT_auto_derived"
    panel = _panel(muscle_size_tier=5, transformation_beat="suit_fail",
                   camera="ecu-region")
    # no hair_state in panel
    prompt = NP.compose_prompt(panel, _minimal_shotlist(),
                               anchor=None, stage_change=True, env_ref=None,
                               lineup_attached=True)
    fails: list[str] = []
    if "Hair state:" in prompt:
        fails.append(
            "Hair state line emitted despite no hair_state on panel "
            "(would imply auto-derivation from tier/beat)"
        )
    return CheckResult(name, not fails, fails)


def t_compose_l24_accessory_line() -> CheckResult:
    name = "inline/compose_prompt/L24_accessory_canonical_and_negation"
    cast = [{
        "id": "ella",
        "accessories": {
            "canonical": "white spiked wristbands on both wrists",
            "negation": ["watches", "bracelets", "dark cuffs"],
        },
    }]
    panel = _panel(camera="medium")
    prompt = NP.compose_prompt(panel, _minimal_shotlist(cast=cast),
                               anchor=None, stage_change=False, env_ref=None)
    fails: list[str] = []
    if "Accessories (ella):" not in prompt:
        fails.append("L24 per-character accessories line missing")
    if "white spiked wristbands on both wrists" not in prompt:
        fails.append("canonical accessory description missing")
    if "NO watches" not in prompt or "NO bracelets" not in prompt or "NO dark cuffs" not in prompt:
        fails.append("enumerated negation list missing or incomplete")
    return CheckResult(name, not fails, fails)


def t_compose_l24_absent_when_no_accessories() -> CheckResult:
    name = "inline/compose_prompt/L24_absent_when_no_accessories_block"
    cast = [{"id": "ella"}]  # no accessories block
    panel = _panel(camera="medium")
    prompt = NP.compose_prompt(panel, _minimal_shotlist(cast=cast),
                               anchor=None, stage_change=False, env_ref=None)
    fails: list[str] = []
    if "Accessories (" in prompt:
        fails.append("accessory line emitted with no cast accessories block")
    return CheckResult(name, not fails, fails)


def t_compose_female_anatomy_anchor_tier2_ecu_region() -> CheckResult:
    name = "inline/compose_prompt/female_anatomy_anchor_tier2_ecu_region"
    cast = [{"id": "ella", "sex": "f"}]
    panel = _panel(camera="ecu-region", muscle_size_tier=2,
                   characters=["ella"])
    prompt = NP.compose_prompt(panel, _minimal_shotlist(cast=cast),
                               anchor=None, stage_change=False, env_ref=None)
    fails: list[str] = []
    if "Female anatomy anchor:" not in prompt:
        fails.append("female anatomy anchor missing on tier 2 ecu-region female")
    if "no square male" not in prompt:
        fails.append("explicit negation 'no square male' missing")
    return CheckResult(name, not fails, fails)


def t_compose_female_anatomy_anchor_skipped_tier1() -> CheckResult:
    """Negative: tier 1 ecu-region does not need the anchor (baseline build is
    naturally female-coded; the anchor would be over-eager)."""
    name = "inline/compose_prompt/female_anatomy_anchor_skipped_tier1"
    cast = [{"id": "ella", "sex": "f"}]
    panel = _panel(camera="ecu-region", muscle_size_tier=1,
                   characters=["ella"])
    prompt = NP.compose_prompt(panel, _minimal_shotlist(cast=cast),
                               anchor=None, stage_change=False, env_ref=None)
    fails: list[str] = []
    if "Female anatomy anchor:" in prompt:
        fails.append("female anatomy anchor fired on tier 1 (should be tier>=2)")
    return CheckResult(name, not fails, fails)


def t_compose_female_anatomy_anchor_skipped_male() -> CheckResult:
    """Negative: explicit male sex disables the female anatomy anchor."""
    name = "inline/compose_prompt/female_anatomy_anchor_skipped_male"
    cast = [{"id": "victor", "sex": "m"}]
    panel = _panel(camera="ecu-region", muscle_size_tier=4,
                   characters=["victor"])
    prompt = NP.compose_prompt(panel, _minimal_shotlist(cast=cast),
                               anchor=None, stage_change=False, env_ref=None)
    fails: list[str] = []
    if "Female anatomy anchor:" in prompt:
        fails.append("female anatomy anchor fired despite sex=m")
    return CheckResult(name, not fails, fails)


def t_compose_female_anatomy_anchor_skipped_ecu_face() -> CheckResult:
    """Negative: ecu-FACE doesn't need the body anchor (the face is on-screen
    so the body isn't the failure surface)."""
    name = "inline/compose_prompt/female_anatomy_anchor_skipped_ecu_face"
    cast = [{"id": "ella", "sex": "f"}]
    panel = _panel(camera="ecu-face", muscle_size_tier=5,
                   characters=["ella"])
    prompt = NP.compose_prompt(panel, _minimal_shotlist(cast=cast),
                               anchor=None, stage_change=False, env_ref=None)
    fails: list[str] = []
    if "Female anatomy anchor:" in prompt:
        fails.append("female anatomy anchor fired on ecu-face (only ecu-region qualifies)")
    return CheckResult(name, not fails, fails)


def t_compose_env_dropped_dense_anchor() -> CheckResult:
    """L23: when env_dropped=True and the shotlist has a location description,
    the dense verbal anchor must be injected into the prompt."""
    name = "inline/compose_prompt/L23_dense_env_anchor_on_drop"
    locations = [{
        "id": "dojo",
        "description": (
            "wooden dojo hall, polished cypress floorboards, paper sliding "
            "doors, hanging scrolls, weapon rack along far wall, late-"
            "afternoon amber light filtering through rice paper"
        ),
    }]
    panel = _panel(location="dojo")
    prompt = NP.compose_prompt(panel, _minimal_shotlist(locations=locations),
                               anchor=None, stage_change=False,
                               env_ref=None, env_dropped=True)
    fails: list[str] = []
    if "Background (no env ref attached this panel" not in prompt:
        fails.append("L23 dense anchor preamble missing on env_dropped=True")
    if "wooden dojo hall" not in prompt:
        fails.append("location description not embedded in dense anchor")
    return CheckResult(name, not fails, fails)


def t_compose_env_dropped_graceful_without_description() -> CheckResult:
    """Negative: env_dropped=True but no locations[] entry → no preamble.
    Prompt should remain well-formed (no crash, no half-rendered tag)."""
    name = "inline/compose_prompt/L23_graceful_when_no_location_description"
    panel = _panel(location="dojo")
    prompt = NP.compose_prompt(panel, _minimal_shotlist(),  # no locations
                               anchor=None, stage_change=False,
                               env_ref=None, env_dropped=True)
    fails: list[str] = []
    if "Background (no env ref attached this panel" in prompt:
        fails.append("dense anchor preamble fired without a description to attach")
    return CheckResult(name, not fails, fails)


# --- should_attach_lineup ----------------------------------------------------

def t_should_attach_lineup_l11_fullbody_no_stage_change() -> CheckResult:
    """L11 widening (regression test): attach the lineup on every full-body
    camera, even without a stage change. The old L5 stage-change-only rule
    is deprecated."""
    name = "inline/should_attach_lineup/L11_full_body_no_stage_change_TRUE"
    panel = _panel(camera="3q-full", muscle_size_tier=3)
    got = NP.should_attach_lineup(panel, stage_change=False)
    fails: list[str] = []
    if got is not True:
        fails.append(f"expected True (L11 attaches on every full-body); got {got}")
    return CheckResult(name, not fails, fails)


def t_should_attach_lineup_ecu_face_no_stage_change() -> CheckResult:
    """Negative: ecu-face without a stage change → no lineup (body isn't focal)."""
    name = "inline/should_attach_lineup/ecu_face_no_stage_change_FALSE"
    panel = _panel(camera="ecu-face", muscle_size_tier=3)
    got = NP.should_attach_lineup(panel, stage_change=False)
    fails: list[str] = []
    if got is not False:
        fails.append(f"expected False on ecu-face no-stage-change; got {got}")
    return CheckResult(name, not fails, fails)


def t_should_attach_lineup_stage_change_always() -> CheckResult:
    """Positive: stage_change=True forces attach regardless of camera."""
    name = "inline/should_attach_lineup/stage_change_TRUE_overrides_camera"
    panel = _panel(camera="mcu", muscle_size_tier=4)
    got = NP.should_attach_lineup(panel, stage_change=True)
    fails: list[str] = []
    if got is not True:
        fails.append(f"expected True (stage_change=True); got {got}")
    return CheckResult(name, not fails, fails)


def t_should_attach_lineup_no_tier() -> CheckResult:
    """Negative: no muscle_size_tier → no lineup ever."""
    name = "inline/should_attach_lineup/no_tier_FALSE"
    panel = _panel(camera="3q-full")  # tier=None by default
    got = NP.should_attach_lineup(panel, stage_change=True)
    fails: list[str] = []
    if got is not False:
        fails.append(f"expected False (no tier); got {got}")
    return CheckResult(name, not fails, fails)


# --- find_lineup -------------------------------------------------------------

def t_find_lineup_returns_none_when_tier_none() -> CheckResult:
    name = "inline/find_lineup/tier_None_returns_None"
    got = NP.find_lineup(SCRIPT_DIR, None)
    fails: list[str] = []
    if got is not None:
        fails.append(f"expected None; got {got}")
    return CheckResult(name, not fails, fails)


def t_find_lineup_resolves_repo_asset() -> CheckResult:
    """Positive: tier 3 falls through to the repo-bundled asset.
    Asserts the no-phantom-refs rule — the returned path actually exists."""
    name = "inline/find_lineup/tier3_resolves_repo_asset"
    got = NP.find_lineup(SCRIPT_DIR / "nonexistent-project-root", 3)
    fails: list[str] = []
    if got is None:
        fails.append("find_lineup returned None for tier 3 (expected repo-bundled asset)")
    elif not got.exists():
        fails.append(f"find_lineup returned non-existent path: {got}")
    elif got.name != "muscle-size-lineup.png":
        fails.append(f"expected muscle-size-lineup.png, got {got.name}")
    return CheckResult(name, not fails, fails)


def t_find_lineup_high_tier_resolves_4_9_asset() -> CheckResult:
    """Positive: tier 7 falls through to the muscle-size-lineup-4-9.png asset."""
    name = "inline/find_lineup/tier7_resolves_4_9_asset"
    got = NP.find_lineup(SCRIPT_DIR / "nonexistent-project-root", 7)
    fails: list[str] = []
    if got is None:
        fails.append("find_lineup returned None for tier 7 (expected -4-9 asset)")
    elif not got.exists():
        fails.append(f"find_lineup returned non-existent path: {got}")
    elif got.name != "muscle-size-lineup-4-9.png":
        fails.append(f"expected muscle-size-lineup-4-9.png, got {got.name}")
    return CheckResult(name, not fails, fails)


def t_find_lineup_no_phantom_refs() -> CheckResult:
    """Regression: the Supergirl panel-13 fix. find_lineup must NEVER return
    a path that doesn't exist on disk. Sweep all integer tiers 1..9 and
    assert every returned Path exists."""
    name = "inline/find_lineup/no_phantom_refs_rule"
    fails: list[str] = []
    for tier in range(1, 10):
        got = NP.find_lineup(SCRIPT_DIR / "nonexistent-project-root", tier)
        if got is not None and not got.exists():
            fails.append(f"tier {tier}: returned phantom path {got}")
    return CheckResult(name, not fails, fails)


# --- pick_location_anchor ----------------------------------------------------

def t_pick_location_anchor_empty_history() -> CheckResult:
    """Negative: empty history → None (first panel has no anchor candidate)."""
    name = "inline/pick_location_anchor/empty_history_None"
    got = NP.pick_location_anchor(SCRIPT_DIR, "dojo", [])
    fails: list[str] = []
    if got is not None:
        fails.append(f"expected None on empty history; got {got}")
    return CheckResult(name, not fails, fails)


def t_pick_location_anchor_no_location_slug() -> CheckResult:
    name = "inline/pick_location_anchor/no_location_slug_None"
    history = [{
        "panel": {"panel_id": "p1", "location": "dojo"},
        "page_number": 1,
        "status": {"state": "accepted", "image": Path("/tmp/fake.png")},
    }]
    got = NP.pick_location_anchor(SCRIPT_DIR, "", history)
    fails: list[str] = []
    if got is not None:
        fails.append(f"expected None on empty location_slug; got {got}")
    return CheckResult(name, not fails, fails)


def t_pick_location_anchor_returns_first_match() -> CheckResult:
    """Positive: subsequent panel at the same location returns the prior item."""
    name = "inline/pick_location_anchor/subsequent_panel_returns_prior"
    fake_img = Path("/tmp/fake-accepted.png")
    history = [{
        "panel": {"panel_id": "p1", "location": "dojo"},
        "page_number": 1,
        "status": {"state": "accepted", "image": fake_img, "label": "v1"},
    }]
    got = NP.pick_location_anchor(SCRIPT_DIR, "dojo", history)
    fails: list[str] = []
    if got is None:
        fails.append("expected the history item; got None")
    elif got["panel"].get("panel_id") != "p1":
        fails.append(f"wrong history item returned: {got}")
    return CheckResult(name, not fails, fails)


def t_pick_location_anchor_skips_no_image() -> CheckResult:
    """An accepted history item without an image cannot serve as anchor."""
    name = "inline/pick_location_anchor/skips_history_without_image"
    history = [{
        "panel": {"panel_id": "p1", "location": "dojo"},
        "page_number": 1,
        "status": {"state": "accepted", "image": None, "label": "v1"},
    }]
    got = NP.pick_location_anchor(SCRIPT_DIR, "dojo", history)
    fails: list[str] = []
    if got is not None:
        fails.append("returned a history item with image=None")
    return CheckResult(name, not fails, fails)


# --- MODEL_MUSCULARITY_CEILING ----------------------------------------------

def t_model_muscularity_ceiling_grok_has_cap() -> CheckResult:
    """Positive: grok_image is in the table with a cap of 3."""
    name = "inline/MODEL_MUSCULARITY_CEILING/grok_image_capped"
    table = NP.MODEL_MUSCULARITY_CEILING
    fails: list[str] = []
    if "grok_image" not in table:
        fails.append("grok_image absent from MODEL_MUSCULARITY_CEILING table")
    elif table["grok_image"] != 3:
        fails.append(
            f"expected grok_image cap = 3, got {table['grok_image']}"
        )
    return CheckResult(name, not fails, fails)


def t_model_muscularity_ceiling_nb2_not_capped() -> CheckResult:
    """Negative: nano_banana_2 must NOT be in the table (no observed ceiling)."""
    name = "inline/MODEL_MUSCULARITY_CEILING/nano_banana_2_not_capped"
    table = NP.MODEL_MUSCULARITY_CEILING
    fails: list[str] = []
    if "nano_banana_2" in table:
        fails.append("nano_banana_2 should not have a ceiling (no failure evidence)")
    return CheckResult(name, not fails, fails)


def t_model_muscularity_ceiling_gpt_image_2_not_capped() -> CheckResult:
    """Negative: gpt_image_2 must NOT be in the table."""
    name = "inline/MODEL_MUSCULARITY_CEILING/gpt_image_2_not_capped"
    table = NP.MODEL_MUSCULARITY_CEILING
    fails: list[str] = []
    if "gpt_image_2" in table:
        fails.append("gpt_image_2 should not have a ceiling (no failure evidence)")
    return CheckResult(name, not fails, fails)


# --- Inline registry ---------------------------------------------------------

INLINE_TESTS = [
    t_compose_style_prefix,
    t_compose_l21_when_refs_attached,
    t_compose_l21_absent_when_no_refs,
    t_compose_hair_state_explicit,
    t_compose_hair_state_no_auto_derive,
    t_compose_l24_accessory_line,
    t_compose_l24_absent_when_no_accessories,
    t_compose_female_anatomy_anchor_tier2_ecu_region,
    t_compose_female_anatomy_anchor_skipped_tier1,
    t_compose_female_anatomy_anchor_skipped_male,
    t_compose_female_anatomy_anchor_skipped_ecu_face,
    t_compose_env_dropped_dense_anchor,
    t_compose_env_dropped_graceful_without_description,
    t_should_attach_lineup_l11_fullbody_no_stage_change,
    t_should_attach_lineup_ecu_face_no_stage_change,
    t_should_attach_lineup_stage_change_always,
    t_should_attach_lineup_no_tier,
    t_find_lineup_returns_none_when_tier_none,
    t_find_lineup_resolves_repo_asset,
    t_find_lineup_high_tier_resolves_4_9_asset,
    t_find_lineup_no_phantom_refs,
    t_pick_location_anchor_empty_history,
    t_pick_location_anchor_no_location_slug,
    t_pick_location_anchor_returns_first_match,
    t_pick_location_anchor_skips_no_image,
    t_model_muscularity_ceiling_grok_has_cap,
    t_model_muscularity_ceiling_nb2_not_capped,
    t_model_muscularity_ceiling_gpt_image_2_not_capped,
]


# ---------------------------------------------------------------------------
# Main

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fixture", help="Run a single fixture by folder name")
    ap.add_argument("--inline-only", action="store_true")
    ap.add_argument("--fixtures-only", action="store_true")
    ap.add_argument("--verbose", "-v", action="store_true")
    args = ap.parse_args()

    if not NEXT_PANEL_PATH.exists():
        sys.exit(f"next_panel.py not found at {NEXT_PANEL_PATH}")

    results: list[CheckResult] = []

    # Fixtures
    if not args.inline_only:
        if not FIXTURES_DIR.exists():
            sys.exit(f"fixtures dir not found at {FIXTURES_DIR}")
        if args.fixture:
            target = FIXTURES_DIR / args.fixture
            if not target.is_dir():
                sys.exit(f"fixture not found: {target}")
            fixtures = [target]
        else:
            fixtures = sorted(p for p in FIXTURES_DIR.iterdir() if p.is_dir())
        print(f"\nFixtures: {len(fixtures)} from {FIXTURES_DIR}\n")
        for f in fixtures:
            r = run_fixture(f)
            results.append(r)
            print(fmt(r, args.verbose))

    # Inline tests
    if not args.fixtures_only and not args.fixture:
        print(f"\nInline tests: {len(INLINE_TESTS)}\n")
        for fn in INLINE_TESTS:
            try:
                r = fn()
            except Exception as e:
                r = CheckResult(fn.__name__, False, [f"raised {type(e).__name__}: {e}"])
            results.append(r)
            print(fmt(r, args.verbose))

    passed = sum(1 for r in results if r.passed)
    failed = len(results) - passed
    summary_color = GREEN if failed == 0 else RED
    print(f"\n{summary_color}{passed}/{len(results)} passed{RESET}\n")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
