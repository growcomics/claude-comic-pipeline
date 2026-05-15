#!/usr/bin/env python3
"""Mock test for flow_runner.FlowBackend.

Verifies the FlowBackend class structure without requiring Playwright + a real
Chrome instance. Real browser testing has to happen on the user's machine.

Covers:
  - FlowBackend can be instantiated
  - check_health surfaces clean errors when Playwright isn't installed or CDP
    is unreachable (the most common deployment failure modes)
  - submit_panel correctly rejects MISSING_ refs reaching it
  - try_locators returns None when no selectors match
"""
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / "runners"))


def test_instantiate_flow_backend():
    from flow_runner import FlowBackend
    b = FlowBackend(cdp_url="http://localhost:9222")
    assert b.cdp_url == "http://localhost:9222"
    assert b._page is None
    print("OK: FlowBackend instantiates")


def test_flow_backend_no_playwright():
    """If playwright isn't installed, check_health returns a clean error."""
    from flow_runner import FlowBackend
    b = FlowBackend(cdp_url="http://localhost:9222")
    # Patch the import inside _ensure_browser to fail
    with patch.dict(sys.modules, {"playwright.sync_api": None}):
        # Force an ImportError by removing the module
        sys.modules.pop("playwright.sync_api", None)
        sys.modules["playwright.sync_api"] = None
        # The actual check happens inside _ensure_browser via from-import
        # We can't easily test the ImportError path without a real env, but we can
        # at least verify check_health returns (False, ...) rather than crashing
        ok, msg = b.check_health()
        # Either playwright really isn't installed (False, useful message), or
        # it is installed and we get a CDP-unreachable error (also False).
        # Either way, no crash.
        assert ok is False
        assert isinstance(msg, str) and len(msg) > 0
    print("OK: check_health returns clean error (no crash)")


def test_flow_backend_cdp_unreachable():
    """If CDP isn't reachable, check_health returns a clean error."""
    from flow_runner import FlowBackend
    b = FlowBackend(cdp_url="http://localhost:55555")  # nothing listening
    ok, msg = b.check_health()
    assert ok is False
    # Message should mention the CDP URL or Chrome
    assert (
        "55555" in msg
        or "Chrome" in msg
        or "playwright" in msg.lower()
        or "connect" in msg.lower()
    ), f"unexpected health-check message: {msg}"
    print("OK: CDP unreachable returns clean error")


def test_try_locators_none_match():
    """try_locators returns None when no selectors match (mocked page)."""
    from flow_runner import try_locators

    mock_loc = MagicMock()
    # wait_for raises -> not visible
    mock_loc.wait_for.side_effect = Exception("not found")

    mock_locator_chain = MagicMock()
    mock_locator_chain.first = mock_loc

    mock_page = MagicMock()
    mock_page.locator.return_value = mock_locator_chain

    result = try_locators(
        mock_page,
        ["role=button[name=/nope/i]", 'text=/also nope/i'],
        timeout_ms=200,
    )
    assert result is None
    print("OK: try_locators returns None when no match")


def test_try_locators_first_match():
    """try_locators returns the locator that matches first."""
    from flow_runner import try_locators

    call_count = {"n": 0}

    def make_loc(selector):
        m = MagicMock()
        m.first = MagicMock()

        def wait_for(*a, **kw):
            call_count["n"] += 1
            if call_count["n"] >= 2:  # second selector wins
                return
            raise Exception("not visible")

        m.first.wait_for.side_effect = wait_for
        return m

    mock_page = MagicMock()
    mock_page.locator.side_effect = make_loc

    result = try_locators(
        mock_page,
        ["sel-A", "sel-B", "sel-C"],
        timeout_ms=2000,
    )
    assert result is not None
    print("OK: try_locators returns first matching locator")


def test_attach_refs_rejects_missing():
    """_attach_refs raises if a MISSING_ ref reaches it (defense in depth — caller
    should have detected it earlier)."""
    from flow_runner import FlowBackend
    b = FlowBackend()
    # Mock the page so we don't need a real browser
    b._page = MagicMock()
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        refs = [
            {"kind": "MISSING_lineup", "path": None, "reason": "lineup absent"},
        ]
        try:
            b._attach_refs(b._page, root, refs)
        except RuntimeError as e:
            assert "MISSING_" in str(e)
            print("OK: _attach_refs rejects MISSING_ refs")
            return
        raise AssertionError("expected RuntimeError for MISSING_ ref")


def test_attach_refs_skips_notes():
    """_attach_refs skips kind=note entries (informational, no file)."""
    from flow_runner import FlowBackend
    b = FlowBackend()
    b._page = MagicMock()
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        refs = [
            {"kind": "note", "path": None, "reason": "ecu-face: face card alone"},
        ]
        # Should return 0 attachments without trying to interact with UI
        n = b._attach_refs(b._page, root, refs)
        assert n == 0
        print("OK: _attach_refs skips kind=note")


def test_attach_refs_missing_file_on_disk():
    """If a non-MISSING ref's file isn't on disk, raise with the absolute path."""
    from flow_runner import FlowBackend
    b = FlowBackend()
    b._page = MagicMock()
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        refs = [
            {"kind": "face_card", "path": "references/characters/lara/face.png",
             "reason": "canonical face anchor for lara"},
        ]
        try:
            b._attach_refs(b._page, root, refs)
        except RuntimeError as e:
            assert "not found on disk" in str(e)
            assert "lara" in str(e) or "face.png" in str(e)
            print("OK: _attach_refs raises clear error when ref file missing")
            return
        raise AssertionError("expected RuntimeError for missing file")


if __name__ == "__main__":
    test_instantiate_flow_backend()
    test_flow_backend_no_playwright()
    test_flow_backend_cdp_unreachable()
    test_try_locators_none_match()
    test_try_locators_first_match()
    test_attach_refs_rejects_missing()
    test_attach_refs_skips_notes()
    test_attach_refs_missing_file_on_disk()
    print("\nAll flow_runner mock tests passed.")
