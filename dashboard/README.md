# Comic Pipeline Dashboard — v0

A read-only FastAPI app that surfaces the state your comic pipeline is already
producing. No new state lives here; every widget reads files the existing
scripts emit (`shotlist.json`, `references/`, `pages/panels/`, `rules_audit.py
--json`, `posting/posted.json`).

If the dashboard ever needs new data, **add it to the pipeline script first,
then read it here.** Re-deriving state inside the dashboard is the failure mode
this design is built to prevent.

## What it shows

Three widgets, per-project tabs, polled live:

- **Stages** — the 6-stage table from `comic-status-board/generate_status.py`,
  rendered as HTML.
- **Panels** — every panel in shotlist order, with state dots (accepted /
  in-progress / missing) and a version chip. Click → modal with all `vN.png`
  variants + `vN.notes.md` notes.
- **Rules audit** — `rules_audit.py --json` grouped by severity (hard / soft /
  info), with the suggestion line expanded on click.

## Run locally

```bash
cd ~/Documents/claude-comic-pipeline
uv venv dashboard/.venv
source dashboard/.venv/bin/activate
uv pip install -r dashboard/requirements.txt
python dashboard/server.py
```

Then open <http://localhost:8765/> in a browser. The dashboard auto-discovers
every directory that contains a `shotlist.json` under the project globs in your
config.

## Config

The dashboard reads its config from
`~/Library/Application Support/comic-dashboard/config.toml` (or the path in
`COMIC_DASHBOARD_CONFIG`). If no config exists, sensible defaults kick in.
See [`config.example.toml`](config.example.toml) for the schema.

Tildes (`~`) are expanded. Globs like `My Drive/comic-projects/*` only match
directories that actually contain a `shotlist.json`.

## Environment

| Variable | Default | Purpose |
|---|---|---|
| `COMIC_DASHBOARD_HOST` | `0.0.0.0` | Bind address |
| `COMIC_DASHBOARD_PORT` | `8765` | Port |
| `COMIC_DASHBOARD_CONFIG` | `~/Library/Application Support/comic-dashboard/config.toml` | Config file location |
| `COMIC_DASHBOARD_CACHE` | `~/Library/Caches/comic-dashboard` | Thumbnail cache directory |

## Deployment (Mac mini + Tailscale)

See [`deploy/README.md`](deploy/README.md) for step-by-step setup of the
launchd service, Google Drive for Desktop sync, and Tailscale access.

## Architecture (the short version)

```
Browser  ──HTMX poll──►  FastAPI (server.py)  ──reads──►  project files on disk
                              │
                              ├─ generate_status.py   (imported)
                              ├─ rules_audit.py       (subprocess --json)
                              └─ Pillow               (thumbnail cache)
```

`server.py` is ~300 lines. Templates are ~150 lines total. CSS is ~250 lines.
There's intentionally no JS framework — HTMX swaps partials on a timer.

## Not in v0 (see `docs/dashboard-v0.md`)

Action buttons, references inventory grid, L-lesson sidebar, SSE push,
auth, live vision audit. We ship the read-only view first and use it for a
week before adding writes.
