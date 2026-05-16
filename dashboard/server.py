"""Comic Pipeline Dashboard — v0.

Read-only FastAPI app that surfaces state from the existing pipeline scripts.
The dashboard owns no state of its own; every widget reads files the pipeline
already emits (shotlist.json, references/, pages/panels/, rules_audit.py output,
posting/posted.json).

If the dashboard ever needs new data, add it to the pipeline script first, then
read it here — never re-derive state inside the dashboard.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tomllib
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from PIL import Image

HERE = Path(__file__).resolve().parent
PIPELINE_ROOT = HERE.parent

# Re-use the same project-state readers that generate_status.py uses, so the
# Stages widget can never drift from `comic-status-board`.
sys.path.insert(0, str(PIPELINE_ROOT / "skills" / "comic-status-board" / "scripts"))
import generate_status as status_lib  # noqa: E402

RULES_AUDIT_SCRIPT = (
    PIPELINE_ROOT / "skills" / "continuity-check" / "scripts" / "rules_audit.py"
)

CONFIG_PATH = Path(
    os.environ.get(
        "COMIC_DASHBOARD_CONFIG",
        Path.home() / "Library/Application Support/comic-dashboard/config.toml",
    )
)
CACHE_DIR = Path(
    os.environ.get(
        "COMIC_DASHBOARD_CACHE",
        Path.home() / "Library/Caches/comic-dashboard",
    )
)
THUMB_DIR = CACHE_DIR / "thumbs"
THUMB_DIR.mkdir(parents=True, exist_ok=True)

THUMB_WIDTH = 320
DEFAULT_GLOBS = [
    # Google Drive for Desktop on macOS
    str(Path.home() / "Library/CloudStorage/GoogleDrive-*/My Drive/comic-projects/*"),
    str(Path.home() / "Library/CloudStorage/GoogleDrive-*/Shared drives/*/comic-projects/*"),
    # Local fallbacks for pre-migration use
    str(Path.home() / "comics/*"),
    str(Path.home() / "Documents/*"),
]


# --------------------------------------------------------------------------- #
# Config & project discovery
# --------------------------------------------------------------------------- #


def load_config() -> dict:
    if CONFIG_PATH.exists():
        return tomllib.loads(CONFIG_PATH.read_text())
    return {"project_globs": DEFAULT_GLOBS}


def _slugify(name: str) -> str:
    out = "".join(c if c.isalnum() or c in "-_" else "-" for c in name)
    return out.strip("-").lower() or "unnamed"


def discover_projects() -> list[dict]:
    cfg = load_config()
    seen: dict[str, dict] = {}
    for pattern in cfg.get("project_globs", DEFAULT_GLOBS):
        expanded = os.path.expanduser(pattern)
        for path in sorted(Path("/").glob(expanded.lstrip("/"))):
            shotlist = path / "shotlist.json"
            if not shotlist.exists():
                continue
            slug = _slugify(path.name)
            if slug in seen:
                continue
            try:
                title = json.loads(shotlist.read_text()).get("project") or path.name
            except (OSError, json.JSONDecodeError):
                title = path.name
            seen[slug] = {
                "slug": slug,
                "title": title,
                "name": path.name,
                "root": path,
            }
    return list(seen.values())


def resolve_project(slug: str) -> Path:
    for p in discover_projects():
        if p["slug"] == slug:
            return p["root"]
    raise HTTPException(status_code=404, detail=f"unknown project: {slug}")


def safe_relative_path(project_root: Path, rel: str) -> Path:
    """Resolve `rel` under `project_root`, refusing traversal outside it."""
    target = (project_root / rel).resolve()
    try:
        target.relative_to(project_root.resolve())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="path escapes project root") from exc
    if not target.exists():
        raise HTTPException(status_code=404, detail="file not found")
    return target


# --------------------------------------------------------------------------- #
# Project state (shared helpers)
# --------------------------------------------------------------------------- #


STATUS_ICON = {
    "done": "✓",
    "partial": "◐",
    "in_progress": "◑",
    "pending": "○",
    "blocked": "✕",
}


def project_state(root: Path) -> dict:
    """Single pass over the project disk state, shared by all widgets."""
    shotlist = status_lib.read_shotlist(root)
    refs = status_lib.enumerate_refs(root)
    panels = status_lib.enumerate_panels(root)
    stages = status_lib.detect_stages(root, shotlist, refs, panels)
    return {"shotlist": shotlist, "refs": refs, "panels": panels, "stages": stages}


def panel_grid_entries(state: dict) -> list[dict]:
    """Walk shotlist in reading order; map each declared panel to a disk folder."""
    shotlist = state["shotlist"] or {}
    by_folder_name: dict[str, dict] = {p["name"]: p for p in state["panels"]}

    entries: list[dict] = []
    for page in shotlist.get("pages", []):
        page_no = page.get("page_number") or page.get("page")
        for panel in page.get("panels", []):
            panel_id = panel.get("panel_id") or ""
            # Match: exact, then endswith (handles `panel-p01-01` style folders)
            match = by_folder_name.get(panel_id)
            if match is None:
                for fname, pdata in by_folder_name.items():
                    if fname.endswith(panel_id) and panel_id:
                        match = pdata
                        break
            if match is None:
                state_label = "missing"
                thumb_src: Path | None = None
            elif match["accepted"]:
                state_label = "accepted"
                thumb_src = match["accepted"]
            else:
                state_label = "in_progress"
                thumb_src = match["versions"][-1] if match["versions"] else None
            entries.append(
                {
                    "panel_id": panel_id,
                    "page_no": page_no,
                    "folder_name": match["name"] if match else None,
                    "state": state_label,
                    "thumb_rel": str(thumb_src) if thumb_src else None,
                    "n_versions": len(match["versions"]) if match else 0,
                    "size": panel.get("size", ""),
                    "characters": panel.get("characters", []),
                    "camera": panel.get("camera", ""),
                }
            )
    return entries


# --------------------------------------------------------------------------- #
# Rules audit
# --------------------------------------------------------------------------- #


def run_rules_audit(root: Path) -> dict:
    """Shell out to rules_audit.py --json. Returns parsed payload or error info."""
    if not RULES_AUDIT_SCRIPT.exists():
        return {"error": f"rules_audit.py not found at {RULES_AUDIT_SCRIPT}", "findings": []}
    proc = subprocess.run(
        [sys.executable, str(RULES_AUDIT_SCRIPT), "--project", str(root), "--json"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    # rules_audit exits 1 when hard findings exist — that's expected, not an error
    if proc.returncode not in (0, 1):
        return {
            "error": f"rules_audit exited {proc.returncode}: {proc.stderr.strip()[:400]}",
            "findings": [],
        }
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        return {"error": f"could not parse rules_audit output: {exc}", "findings": []}


def group_findings(payload: dict) -> dict:
    findings = payload.get("findings", [])
    groups: dict[str, list[dict]] = {"hard": [], "soft": [], "info": []}
    for f in findings:
        groups.setdefault(f.get("severity", "info"), []).append(f)
    return {
        "error": payload.get("error"),
        "groups": groups,
        "counts": {k: len(v) for k, v in groups.items()},
        "total": sum(len(v) for v in groups.values()),
    }


# --------------------------------------------------------------------------- #
# Thumbnails
# --------------------------------------------------------------------------- #


def thumbnail_for(project_root: Path, rel: str, width: int = THUMB_WIDTH) -> Path:
    src = safe_relative_path(project_root, rel)
    mtime = src.stat().st_mtime_ns
    key_raw = f"{project_root}|{rel}|{mtime}|{width}".encode()
    key = hashlib.sha256(key_raw).hexdigest()[:24]
    out = THUMB_DIR / f"{key}.jpg"
    if out.exists():
        return out
    with Image.open(src) as im:
        im = im.convert("RGB")
        ratio = width / im.width
        im.thumbnail((width, int(im.height * ratio)))
        im.save(out, "JPEG", quality=78, optimize=True)
    return out


# --------------------------------------------------------------------------- #
# FastAPI app
# --------------------------------------------------------------------------- #


app = FastAPI(title="Comic Pipeline Dashboard")
app.mount("/static", StaticFiles(directory=str(HERE / "static")), name="static")
templates = Jinja2Templates(directory=str(HERE / "templates"))


@app.get("/healthz", response_class=Response)
def healthz() -> Response:
    return Response("ok", media_type="text/plain")


@app.get("/api/projects", response_class=JSONResponse)
def api_projects() -> list[dict]:
    return [
        {"slug": p["slug"], "title": p["title"], "name": p["name"], "root": str(p["root"])}
        for p in discover_projects()
    ]


@app.get("/", response_class=HTMLResponse)
def index(request: Request, project: str | None = None) -> HTMLResponse:
    projects = discover_projects()
    active_slug = project or (projects[0]["slug"] if projects else None)
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "projects": projects,
            "active_slug": active_slug,
            "now": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        },
    )


@app.get("/widgets/stages", response_class=HTMLResponse)
def widget_stages(request: Request, project: str) -> HTMLResponse:
    root = resolve_project(project)
    state = project_state(root)
    return templates.TemplateResponse(
        request,
        "_stages.html",
        {
            "stages": state["stages"],
            "icons": STATUS_ICON,
            "now": datetime.now(timezone.utc).strftime("%H:%M:%S UTC"),
        },
    )


@app.get("/widgets/panels", response_class=HTMLResponse)
def widget_panels(request: Request, project: str) -> HTMLResponse:
    root = resolve_project(project)
    state = project_state(root)
    entries = panel_grid_entries(state)
    return templates.TemplateResponse(
        request,
        "_panels.html",
        {
            "project": project,
            "entries": entries,
            "now": datetime.now(timezone.utc).strftime("%H:%M:%S UTC"),
        },
    )


@app.get("/widgets/panel-versions", response_class=HTMLResponse)
def widget_panel_versions(request: Request, project: str, folder: str) -> HTMLResponse:
    root = resolve_project(project)
    state = project_state(root)
    match = next((p for p in state["panels"] if p["name"] == folder), None)
    if match is None:
        raise HTTPException(status_code=404, detail=f"panel folder not found: {folder}")
    return templates.TemplateResponse(
        request,
        "_panel_versions.html",
        {"project": project, "panel": match},
    )


@app.get("/widgets/findings", response_class=HTMLResponse)
def widget_findings(request: Request, project: str) -> HTMLResponse:
    root = resolve_project(project)
    payload = run_rules_audit(root)
    grouped = group_findings(payload)
    return templates.TemplateResponse(
        request,
        "_findings.html",
        {
            "grouped": grouped,
            "now": datetime.now(timezone.utc).strftime("%H:%M:%S UTC"),
        },
    )


@app.get("/thumb")
def thumb(project: str, path: str, w: int = THUMB_WIDTH) -> FileResponse:
    root = resolve_project(project)
    out = thumbnail_for(root, path, width=w)
    return FileResponse(out, media_type="image/jpeg")


@app.get("/image")
def image(project: str, path: str) -> FileResponse:
    root = resolve_project(project)
    src = safe_relative_path(root, path)
    return FileResponse(src)


if __name__ == "__main__":
    import uvicorn

    host = os.environ.get("COMIC_DASHBOARD_HOST", "0.0.0.0")
    port = int(os.environ.get("COMIC_DASHBOARD_PORT", "8765"))
    uvicorn.run(app, host=host, port=port, log_level="info")
