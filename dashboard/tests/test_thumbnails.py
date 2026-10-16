"""Tests for thumbnail generation and disk caching."""

from __future__ import annotations

import os
import time
from pathlib import Path

from PIL import Image


def test_thumbnail_for_creates_jpeg(make_project, server_module):
    root = make_project("thumb-create", pages=1, panels_per_page=1)
    # Replace the fixture's small PNG with one wide enough that Pillow's
    # thumbnail() actually has to scale down to 128px.
    src = root / "pages" / "panels" / "p01-01" / "v1.png"
    Image.new("RGB", (640, 480), (200, 220, 180)).save(src, "PNG")
    out = server_module.thumbnail_for(root, "pages/panels/p01-01/v1.png", width=128)
    assert out.exists()
    assert out.suffix == ".jpg"
    with Image.open(out) as im:
        assert im.format == "JPEG"
        assert im.width == 128


def test_thumbnail_for_uses_cache_when_mtime_unchanged(make_project, server_module):
    root = make_project("thumb-cache", pages=1, panels_per_page=1)
    first = server_module.thumbnail_for(root, "pages/panels/p01-01/v1.png", width=96)
    mtime_first = first.stat().st_mtime_ns
    time.sleep(0.01)
    second = server_module.thumbnail_for(root, "pages/panels/p01-01/v1.png", width=96)
    assert first == second
    # Cached file should not have been rewritten.
    assert second.stat().st_mtime_ns == mtime_first


def test_thumbnail_for_regenerates_on_source_mtime_change(
    make_project, server_module
):
    root = make_project("thumb-bust", pages=1, panels_per_page=1)
    src = root / "pages" / "panels" / "p01-01" / "v1.png"
    first = server_module.thumbnail_for(root, "pages/panels/p01-01/v1.png", width=96)

    # Mutate source: change the image and force a new mtime.
    Image.new("RGB", (32, 32), (255, 0, 0)).save(src, "PNG")
    new_mtime = first.stat().st_mtime_ns + 1_000_000_000
    os.utime(src, ns=(new_mtime, new_mtime))

    second = server_module.thumbnail_for(root, "pages/panels/p01-01/v1.png", width=96)
    assert second != first
    assert second.exists()
