"""Test fixtures for the dashboard.

Sets environment variables before importing the server module so the server
points at a temp config + temp cache for the duration of the test run.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

import pytest
from PIL import Image

# Resolve test-time paths before importing server so the server picks up
# the temp config and temp cache via env vars.
_TMP_ROOT = Path(tempfile.mkdtemp(prefix="dashboard-tests-"))
_PROJECTS_ROOT = _TMP_ROOT / "projects"
_PROJECTS_ROOT.mkdir()
_CONFIG_FILE = _TMP_ROOT / "config.toml"
_CONFIG_FILE.write_text(
    f'project_globs = ["{_PROJECTS_ROOT}/*"]\n'
)
_CACHE_DIR = _TMP_ROOT / "cache"
_CACHE_DIR.mkdir()

os.environ["COMIC_DASHBOARD_CONFIG"] = str(_CONFIG_FILE)
os.environ["COMIC_DASHBOARD_CACHE"] = str(_CACHE_DIR)

# Make `dashboard/` importable so `import server` works from inside tests/.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture(scope="session", autouse=True)
def _cleanup_tmp_root():
    """Wipe the entire temp root at end of test session."""
    yield
    shutil.rmtree(_TMP_ROOT, ignore_errors=True)


@pytest.fixture(autouse=True)
def clean_projects_root():
    """Wipe project tmp dirs between tests so each starts clean."""
    yield
    for child in _PROJECTS_ROOT.iterdir():
        if child.is_dir():
            shutil.rmtree(child, ignore_errors=True)
        else:
            child.unlink(missing_ok=True)


@pytest.fixture
def projects_root() -> Path:
    return _PROJECTS_ROOT


@pytest.fixture
def cache_dir() -> Path:
    return _CACHE_DIR


def _make_png(path: Path, *, color=(180, 200, 220), size=(64, 48)) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, color).save(path, "PNG")


@pytest.fixture
def make_project(projects_root: Path):
    """Factory: create a project under projects_root with configurable state."""

    def _factory(
        name: str = "tiny",
        *,
        with_shotlist: bool = True,
        pages: int = 1,
        panels_per_page: int = 2,
        accepted: set[str] | None = None,
        layout: str = "folder",  # "folder" (panel-id/vN.png) or "flat" (panel-id.png)
        project_field: str | None = None,
    ) -> Path:
        root = projects_root / name
        root.mkdir()

        if with_shotlist:
            pages_data = []
            for pn in range(1, pages + 1):
                pages_data.append(
                    {
                        "page_number": pn,
                        "panels": [
                            {
                                "panel_id": f"p{pn:02d}-{i:02d}",
                                "size": "wide",
                                "characters": ["alice"],
                                "location": "lab",
                                "camera": "wide",
                                "action": f"panel {pn}-{i}",
                            }
                            for i in range(1, panels_per_page + 1)
                        ],
                    }
                )
            shotlist = {
                "project": project_field or name,
                "version": "test-1",
                "page_count": pages,
                "cast": [{"slug": "alice", "name": "Alice"}],
                "locations": [],
                "props": [],
                "pages": pages_data,
            }
            (root / "shotlist.json").write_text(json.dumps(shotlist, indent=2))

        accepted = accepted or set()
        if with_shotlist and panels_per_page > 0:
            panels_root = root / "pages" / "panels"
            panels_root.mkdir(parents=True)
            for pn in range(1, pages + 1):
                for i in range(1, panels_per_page + 1):
                    pid = f"p{pn:02d}-{i:02d}"
                    if layout == "flat":
                        _make_png(panels_root / f"{pid}.png")
                    else:
                        panel_dir = panels_root / pid
                        _make_png(panel_dir / "v1.png")
                        if pid in accepted:
                            (panel_dir / "_accepted.txt").write_text("v1")
        return root

    return _factory


@pytest.fixture
def client():
    """A FastAPI TestClient with the test config in effect.

    Imported lazily so the env vars set at module load are honored.
    """
    from fastapi.testclient import TestClient

    import server

    return TestClient(server.app)


@pytest.fixture
def server_module():
    """Direct access to the imported server module for unit tests."""
    import server

    return server
