#!/usr/bin/env python3
"""Pin the shared view-vocabulary JSON as the source of truth.

Both skills/comic-production/scripts/next_panel.py (VIEW_COMPATIBILITY +
_VIEW_ALIASES + _canon_view) and skills/script-breakdown/scripts/validate_shotlist.py
(KNOWN_VIEWS) must derive their tables from
skills/comic-production/data/view-vocabulary.json. These tests fail if either
script drifts from the JSON or if the JSON itself becomes internally
inconsistent.
"""
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
VOCAB_PATH = REPO_ROOT / "skills" / "comic-production" / "data" / "view-vocabulary.json"

sys.path.insert(0, str(REPO_ROOT / "skills" / "comic-production" / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "skills" / "script-breakdown" / "scripts"))

import next_panel  # noqa: E402
import validate_shotlist  # noqa: E402


def _vocab():
    return json.loads(VOCAB_PATH.read_text())


def test_runtime_uses_vocab_file():
    """VIEW_COMPATIBILITY + _VIEW_ALIASES in next_panel are populated from the JSON."""
    v = _vocab()
    assert next_panel.VIEW_COMPATIBILITY == {
        k: set(prior) for k, prior in v["compatibility"].items()
    }
    assert next_panel._VIEW_ALIASES == v["aliases"]


def test_validator_known_views_is_derived_union():
    """KNOWN_VIEWS = compatibility.keys ∪ aliases.keys ∪ aliases.values.

    These three sets together describe every head token the runtime will
    accept — anything else is genuinely unknown and should be rejected.
    """
    v = _vocab()
    expected = (
        set(v["compatibility"].keys())
        | set(v["aliases"].keys())
        | set(v["aliases"].values())
    )
    assert validate_shotlist.KNOWN_VIEWS == expected


def test_alias_values_are_valid_targets():
    """Every alias must point at either a compatibility key or one of the
    declared extra normalized targets (mcu/medium/medium-wide). An alias
    pointing at an unknown target would silently make _canon_view() emit a
    token that VIEW_COMPATIBILITY can never satisfy.
    """
    v = _vocab()
    valid_targets = set(v["compatibility"].keys()) | set(v["extra_alias_targets"])
    bad = {src: tgt for src, tgt in v["aliases"].items() if tgt not in valid_targets}
    assert not bad, f"alias targets not in valid_targets: {bad}"


def test_canon_view_round_trips_every_alias():
    """Every alias key, fed through _canon_view, must produce the alias's target.
    This is the runtime guarantee the validator relies on when it accepts an
    alias key as a valid camera head.
    """
    v = _vocab()
    misses = {}
    for src, tgt in v["aliases"].items():
        got = next_panel._canon_view(src)
        if got != tgt:
            misses[src] = (got, tgt)
    assert not misses, f"_canon_view mismatches (got, expected): {misses}"


def test_compatibility_targets_are_self_referential():
    """Every set in `compatibility` should contain views drawn from the
    compatibility key space — chain anchors are always full VIEW_COMPATIBILITY
    keys, never alias forms or extra targets.
    """
    v = _vocab()
    keys = set(v["compatibility"].keys())
    for key, prior in v["compatibility"].items():
        unknown = set(prior) - keys
        assert not unknown, f"{key}: compatible-prior views not in compat keys: {unknown}"


if __name__ == "__main__":
    test_runtime_uses_vocab_file()
    print("OK: runtime tables match vocab JSON")
    test_validator_known_views_is_derived_union()
    print("OK: validator KNOWN_VIEWS matches derived union")
    test_alias_values_are_valid_targets()
    print("OK: alias targets all valid")
    test_canon_view_round_trips_every_alias()
    print("OK: _canon_view round-trips every alias")
    test_compatibility_targets_are_self_referential()
    print("OK: compatibility sets reference only compat keys")
    print("\nAll tests passed.")
