# Deploying the dashboard on the Mac mini

This walks the Mac mini from blank slate to "open `http://<hostname>:8765/`
from anywhere on the tailnet and see live comic state."

## Prerequisites

- Python 3.11+ (`python3 --version` — 3.13 is current here, fine)
- [uv](https://docs.astral.sh/uv/) (`uv --version`)
- A Google account (for Drive) and Tailscale account (free, up to 3 users)
- This repo cloned at `~/Documents/claude-comic-pipeline`

The paths in `com.growcomics.dashboard.plist` are absolute and hard-coded to
this user (`resedaclawdbot`). If you move the repo or run as a different user,
edit the plist's `WorkingDirectory` and both absolute `ProgramArguments` paths.

## 1 · Tailscale

```sh
brew install --cask tailscale
open -a Tailscale          # menu-bar app opens
```

Click the menu-bar icon → **Log in…** → finish the browser auth.

Note the Tailscale name shown next to your Mac mini in the admin console at
<https://login.tailscale.com/admin/machines>. It looks like
`mac-mini.<your-tailnet>.ts.net`. That's the hostname the dashboard will live
at.

Install Tailscale on each other device that needs to view the dashboard
(your laptop, your colleague's Mac, your phone), and log them into the same
tailnet.

## 2 · Google Drive for Desktop + project layout

```sh
brew install --cask google-drive
open -a "Google Drive"
```

Sign in with the Google account that will own the shared `comic-projects/`
folder. Pick **"Stream files"** (cheaper on disk) unless you need offline; the
dashboard re-reads files on every poll so either mode works.

Once it's running, the mount appears at
`~/Library/CloudStorage/GoogleDrive-<email>/`. Create the canonical layout:

```sh
mkdir -p ~/Library/CloudStorage/GoogleDrive-*/My\ Drive/comic-projects
```

**Copy** (don't move yet) the two existing projects into Drive:

```sh
DRIVE=~/Library/CloudStorage/GoogleDrive-*/My\ Drive/comic-projects
rsync -av ~/comics/chun-li-iron-discipline           "$DRIVE"/
rsync -av ~/Documents/supergirl-overcharged          "$DRIVE"/
```

Wait until the Google Drive menu-bar app says "Up to date" — that confirms the
upload completed. Verify in <https://drive.google.com/> that both folders show
up under My Drive › comic-projects.

Share `comic-projects` with your colleague's Google account (right-click in
the web UI → **Share** → editor).

Leave the originals at `~/comics/` and `~/Documents/` as backups for a few
days. Once we've confirmed the dashboard reads cleanly from Drive and nothing
is missing, delete the originals and remove the `~/comics/*` and
`~/Documents/*` globs from `config.toml`.

## 3 · Install the dashboard config

```sh
mkdir -p "$HOME/Library/Application Support/comic-dashboard"
cp dashboard/config.example.toml \
   "$HOME/Library/Application Support/comic-dashboard/config.toml"
```

Edit if your Drive account email needs disambiguation (the wildcard
`GoogleDrive-*` should match on its own).

## 4 · Install Python deps

```sh
cd ~/Documents/claude-comic-pipeline
uv venv dashboard/.venv
uv pip install --python dashboard/.venv/bin/python -r dashboard/requirements.txt
```

## 5 · One-shot smoke test (before installing the service)

```sh
dashboard/.venv/bin/python dashboard/server.py
```

In another terminal:

```sh
curl http://localhost:8765/healthz                    # → ok
curl -s http://localhost:8765/api/projects | jq       # → list of projects
open http://localhost:8765/                            # → dashboard in browser
```

You should see project tabs for both Chun-Li and Supergirl, panels rendering
with thumbnails, and the rules-audit widget populated. Ctrl-C when done.

## 6 · Install as a launchd service

```sh
mkdir -p "$HOME/Library/Logs/comic-dashboard"

cp dashboard/deploy/com.growcomics.dashboard.plist \
   "$HOME/Library/LaunchAgents/"

launchctl bootstrap "gui/$(id -u)" \
   "$HOME/Library/LaunchAgents/com.growcomics.dashboard.plist"

launchctl print "gui/$(id -u)/com.growcomics.dashboard" | head -20
```

The last command should report `state = running`. Tail the log to confirm
uvicorn started:

```sh
tail -f ~/Library/Logs/comic-dashboard/stderr.log
```

You're looking for `Uvicorn running on http://0.0.0.0:8765`.

## 7 · Verify Tailscale access

From your laptop (also on the tailnet):

```sh
open http://<mac-mini-tailscale-name>:8765/
```

E.g. `http://mac-mini.tail-1234.ts.net:8765/`. Confirm the dashboard renders,
the panel thumbnails load, and clicking a panel opens the version modal.

From your colleague's machine: same URL. Tailscale handles the auth — they
need to be logged in to the same tailnet.

## 8 · Managing the service

```sh
# Stop and unload
launchctl bootout "gui/$(id -u)" \
   "$HOME/Library/LaunchAgents/com.growcomics.dashboard.plist"

# Restart (after code changes)
launchctl kickstart -k "gui/$(id -u)/com.growcomics.dashboard"

# Logs
tail -f ~/Library/Logs/comic-dashboard/stdout.log
tail -f ~/Library/Logs/comic-dashboard/stderr.log
```

`KeepAlive=true` in the plist means launchd restarts the service automatically
if it crashes, and at every login/reboot.

## 9 · Adding Cloudflare Tunnel later (deferred)

When you want a public URL (e.g. to share a single panel with someone not on
the tailnet):

```sh
brew install cloudflared
cloudflared tunnel login
cloudflared tunnel create comics-dashboard
cloudflared tunnel route dns comics-dashboard comics.<your-domain>
cloudflared tunnel run --url http://127.0.0.1:8765 comics-dashboard
```

Then create a separate launchd plist for `cloudflared`. Until then, Tailscale
is enough.

## Troubleshooting

**Service won't start.** Check `~/Library/Logs/comic-dashboard/stderr.log`.
Common causes: venv path wrong in plist, port 8765 already in use, missing
Python deps.

**Dashboard shows "no projects discovered".** Verify Google Drive has finished
syncing (menu-bar app says "Up to date"), and that
`~/Library/CloudStorage/GoogleDrive-*/My Drive/comic-projects/<project>/shotlist.json`
actually exists on disk (not just in the cloud — Drive may need to download it
locally first).

**Panel thumbnails are blank.** Check
`~/Library/Caches/comic-dashboard/thumbs/` is writable. `rm -rf` it to force
regeneration.

**Tailscale URL doesn't load.** From the Mac mini: `tailscale status` — your
laptop should appear. From the laptop: `curl http://<mac-mini-name>:8765/healthz`.
If `curl` works but the browser doesn't, it's a browser/DNS issue. If `curl`
also fails, check the Tailscale ACLs (default allow-all should be fine for
small tailnets).
