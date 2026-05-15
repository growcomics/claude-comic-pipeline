#!/usr/bin/env python3
"""Tests for variant_picker.py.

Covers:
  - heuristic strategy: file-size ranking, duplicate detection, all-bad detection
  - first strategy: trivially picks v1
  - claude_api strategy: mocked Anthropic client, verifies prompt construction
    and JSON response parsing
  - _extract_json: parsing JSON from markdown-fenced or bare text
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / "runners"))

from variant_picker import (
    VariantPickResult,
    _extract_json,
    _pick_first,
    _pick_heuristic,
    pick_variant,
)


def write_variants(d: Path, sizes: list[int]) -> list[Path]:
    """Write fake PNG files with the given byte sizes. Returns the paths in order."""
    paths = []
    for i, sz in enumerate(sizes, start=1):
        p = d / f"v{i}.png"
        # Use deterministic content but include i so duplicates don't happen by accident
        p.write_bytes(bytes([i]) * sz)
        paths.append(p)
    return paths


def test_heuristic_picks_largest():
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        paths = write_variants(d, [100, 500, 300, 200])
        r = _pick_heuristic(paths)
        assert r.picked == 2, f"expected 2, got {r.picked}"
        assert r.strategy_used == "heuristic"
        assert not r.all_bad
        print("OK: heuristic picks largest")


def test_heuristic_detects_duplicates():
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        # Two duplicates (v1 and v3 identical), v2 unique smaller, v4 unique largest
        p1 = d / "v1.png"; p1.write_bytes(b"X" * 200)
        p2 = d / "v2.png"; p2.write_bytes(b"Y" * 100)
        p3 = d / "v3.png"; p3.write_bytes(b"X" * 200)  # dup of v1
        p4 = d / "v4.png"; p4.write_bytes(b"Z" * 300)
        r = _pick_heuristic([p1, p2, p3, p4])
        # v4 wins on size after duplicate elimination
        assert r.picked == 4
        # Concern note about reduced candidate set
        assert any("only" in c.lower() for c in r.concerns)
        print("OK: heuristic detects duplicates")


def test_heuristic_all_missing():
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        ghost_paths = [d / f"v{i}.png" for i in range(1, 5)]
        r = _pick_heuristic(ghost_paths)
        assert r.all_bad is True
        assert r.picked == 1
        print("OK: heuristic flags all-bad when all missing")


def test_first_picker():
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        paths = write_variants(d, [100, 999, 999, 999])
        r = _pick_first(paths)
        assert r.picked == 1
        assert r.strategy_used == "first"
        print("OK: first strategy")


def test_extract_json_bare():
    out = _extract_json('{"picked": 2, "reason": "foo"}')
    assert out == {"picked": 2, "reason": "foo"}
    print("OK: extract_json bare")


def test_extract_json_fenced():
    text = '```json\n{"picked": 3, "reason": "bar", "concerns": []}\n```'
    out = _extract_json(text)
    assert out == {"picked": 3, "reason": "bar", "concerns": []}
    print("OK: extract_json fenced")


def test_extract_json_with_preamble():
    text = (
        "Here is my analysis:\n"
        'The answer is {"picked": 1, "reason": "good face"} based on the criteria.'
    )
    out = _extract_json(text)
    assert out == {"picked": 1, "reason": "good face"}
    print("OK: extract_json with preamble")


def test_extract_json_invalid():
    assert _extract_json("not json at all") is None
    assert _extract_json("") is None
    print("OK: extract_json returns None on invalid")


def test_claude_api_mocked():
    """Mock anthropic.Anthropic so we don't make a real API call."""
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        paths = write_variants(d, [100, 200, 300, 400])

        # Build a fake response: a list of content blocks with .type and .text
        mock_block = MagicMock()
        mock_block.type = "text"
        mock_block.text = '{"picked": 3, "reason": "best face acting", "concerns": ["v1 has flat expression"], "all_bad": false}'
        mock_response = MagicMock()
        mock_response.content = [mock_block]

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response

        # Patch the anthropic module
        fake_anthropic = MagicMock()
        fake_anthropic.Anthropic.return_value = mock_client

        plan = {
            "next_panel": {
                "panel_id": "p01-03",
                "camera": "front-full",
                "action": "Kara strikes the Forge-Heart",
            },
            "page_number": 1,
            "stage_change": True,
            "anchor_panel_id": "p01-02",
        }
        config = {
            "transformation_type": "fmg",
            "mandatory_rules": {"active": [1, 2, 3, 4, 5, 6, 7, 9]},
        }

        with patch.dict(sys.modules, {"anthropic": fake_anthropic}):
            with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test"}):
                r = pick_variant(paths, plan, config, strategy="claude_api")

        assert r.picked == 3, f"expected 3, got {r.picked}"
        assert r.reason == "best face acting"
        assert r.concerns == ["v1 has flat expression"]
        assert not r.all_bad
        assert r.strategy_used == "claude_api"
        assert r.api_cost_usd is not None

        # Verify the API was called with vision content (images + text)
        call_args = mock_client.messages.create.call_args
        assert call_args is not None
        msgs = call_args.kwargs.get("messages", [])
        assert len(msgs) == 1
        user_content = msgs[0]["content"]
        # Should have 4 image blocks + 4 "Variant N" labels + 1 prompt = 9 blocks
        image_blocks = [b for b in user_content if b.get("type") == "image"]
        assert len(image_blocks) == 4, f"expected 4 images, got {len(image_blocks)}"
        # System prompt should mention FMG specifically per transformation_type
        system = call_args.kwargs.get("system", "")
        assert "FMG" in system or "fmg" in system or "muscle" in system.lower()
        print("OK: claude_api strategy (mocked) — selection, parsing, prompt build")


def test_claude_api_missing_key():
    """Without ANTHROPIC_API_KEY, pick_variant falls back to heuristic."""
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        paths = write_variants(d, [100, 500, 300, 200])
        plan = {"next_panel": {"panel_id": "p01-01", "camera": "front-full", "action": ""}}
        config = {"transformation_type": "fmg"}

        # Ensure no API key in env
        with patch.dict(os.environ, {}, clear=True):
            # Strip the env vars that could leak
            for k in ("ANTHROPIC_API_KEY", "CLAUDE_VARIANT_MODEL"):
                os.environ.pop(k, None)
            r = pick_variant(paths, plan, config, strategy="claude_api")
        # Fall back to heuristic
        assert r.strategy_used == "heuristic"
        assert r.picked == 2  # largest
        print("OK: claude_api falls back to heuristic when ANTHROPIC_API_KEY missing")


def test_claude_api_all_bad_propagation():
    """When the API returns all_bad=true, the picker surfaces it for halt policy."""
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        paths = write_variants(d, [100, 200, 300, 400])

        mock_block = MagicMock()
        mock_block.type = "text"
        mock_block.text = json.dumps({
            "picked": 1,
            "reason": "least-bad of a bad batch",
            "concerns": ["all four drifted to 2D illustration",
                         "all four have anatomy issues"],
            "all_bad": True,
        })
        mock_response = MagicMock()
        mock_response.content = [mock_block]
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        fake_anthropic = MagicMock()
        fake_anthropic.Anthropic.return_value = mock_client

        plan = {"next_panel": {"panel_id": "p01-01", "camera": "front-full", "action": ""}}
        config = {"transformation_type": "be"}

        with patch.dict(sys.modules, {"anthropic": fake_anthropic}):
            with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test"}):
                r = pick_variant(paths, plan, config, strategy="claude_api")

        assert r.all_bad is True
        assert len(r.concerns) == 2
        print("OK: all_bad propagates from API response")


if __name__ == "__main__":
    test_heuristic_picks_largest()
    test_heuristic_detects_duplicates()
    test_heuristic_all_missing()
    test_first_picker()
    test_extract_json_bare()
    test_extract_json_fenced()
    test_extract_json_with_preamble()
    test_extract_json_invalid()
    test_claude_api_mocked()
    test_claude_api_missing_key()
    test_claude_api_all_bad_propagation()
    print("\nAll variant_picker tests passed.")
