"""Tests for path-traversal guard."""

from __future__ import annotations

import pytest
from fastapi import HTTPException


def test_safe_relative_path_resolves_inside_project(make_project, server_module):
    root = make_project("safe", pages=1, panels_per_page=1)
    out = server_module.safe_relative_path(root, "pages/panels/p01-01/v1.png")
    assert out.exists()
    # Compare resolved paths — on macOS /var is a symlink to /private/var, so
    # `.resolve()` on `out` returns /private/var/... while the fixture's `root`
    # may still be /var/...
    assert str(out).startswith(str(root.resolve()))


def test_safe_relative_path_rejects_dotdot(make_project, server_module):
    root = make_project("safe-dotdot", pages=1, panels_per_page=1)
    with pytest.raises(HTTPException) as exc:
        server_module.safe_relative_path(root, "../../etc/passwd")
    assert exc.value.status_code == 400


def test_safe_relative_path_rejects_absolute_outside_project(
    make_project, server_module
):
    root = make_project("safe-abs", pages=1, panels_per_page=1)
    with pytest.raises(HTTPException) as exc:
        server_module.safe_relative_path(root, "/etc/passwd")
    # Either 400 (escapes project root) or 404 (file not found) is acceptable;
    # both block the read.
    assert exc.value.status_code in (400, 404)


def test_safe_relative_path_404_for_missing_file(make_project, server_module):
    root = make_project("safe-missing", pages=1, panels_per_page=1)
    with pytest.raises(HTTPException) as exc:
        server_module.safe_relative_path(root, "pages/panels/p99-99/v1.png")
    assert exc.value.status_code == 404
