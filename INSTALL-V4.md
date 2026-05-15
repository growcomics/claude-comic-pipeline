# Comic Autopilot v4 — Install Guide

v4 adds **deterministic Python runners** that take Claude Code out of the per-panel generation loop entirely. Read `docs/ARCHITECTURE.md` for the why.

v4 sits on top of v2 + v3. If you have those installed, v4 adds (but does not replace) those layers:

| Layer | Source | Status |
|---|---|---|
| Briefing skill | v2, updated in v3 | Keep — captures upfront decisions |
| Stop hook | v2 | Keep — catches turn-end halts |
| PreToolUse hook | v3 | Keep — blocks AskUserQuestion |
| Build-comic.md autopilot prose | v3 | **Replaced in v4** — adds Stage 3 subprocess hand-off |
| Runners | NEW in v4 | Install — these are the structural guarantee |
| Updated production-config schema | NEW in v4 | Optional — adds `generation.variant_picker` and friends |

You can install v4 in two ways:

- **Full install** (recommended): drop in v4 runners + replace build-comic.md. Stage 3 becomes a subprocess call. Guarantee is structural.
- **Minimal install**: only the runners, keep the v3 prose. Lets you invoke runners manually from a terminal but doesn't change `/build-comic autopilot` orchestration. Use this to test runners without committing.

## Prerequisites

- v2 + v3 already installed (run `/hooks` in Claude Code — both `pre-tool-autopilot.py` and `stop-autopilot.py` should be listed)
- Python 3.10+
- `pip install -r runners/requirements.txt` ran successfully
- `playwright install chromium` (only if using `flow_runner.py`)
- For variant picker: `ANTHROPIC_API_KEY` env var set (`export ANTHROPIC_API_KEY=sk-ant-...`)

## Install steps

```bash
# 0. Unzip v4 patch
cd ~/Desktop/claude/comic-autopilot-v4

# 1. Back up first
cd ~/.claude
mkdir -p backups/2026-05-14-v4
cp -r skills/comic-production backups/2026-05-14-v4/comic-production-pre-v4 2>/dev/null || true
cp commands/build-comic.md backups/2026-05-14-v4/

# 2. Install runners as part of the comic-production skill
mkdir -p ~/.claude/skills/comic-production/scripts/runners
cp ~/Desktop/claude/comic-autopilot-v4/runners/*.py ~/.claude/skills/comic-production/scripts/runners/
cp ~/Desktop/claude/comic-autopilot-v4/runners/requirements.txt ~/.claude/skills/comic-production/scripts/runners/
cp ~/Desktop/claude/comic-autopilot-v4/runners/README.md ~/.claude/skills/comic-production/scripts/runners/

# 3. Install Python dependencies
cd ~/.claude/skills/comic-production/scripts/runners
pip install -r requirements.txt
# For Flow only:
playwright install chromium

# 4. Replace build-comic.md (adds Stage 3 subprocess hand-off + halt-reason mapping)
cp ~/Desktop/claude/comic-autopilot-v4/commands/build-comic.md ~/.claude/commands/build-comic.md

# 5. Set the Anthropic API key for variant picking (optional but recommended)
# Add to your shell profile (~/.zshrc or ~/.bashrc):
export ANTHROPIC_API_KEY="sk-ant-..."
```

That's it. Restart Claude Code so the updated `build-comic.md` re-registers.

## Verify install

```bash
# Runners are reachable
ls ~/.claude/skills/comic-production/scripts/runners/
# Should show: runner_core.py variant_picker.py flow_runner.py flow_selectors.py
# higgsfield_runner.py requirements.txt README.md

# Dependencies installed
python3 -c "import playwright; import anthropic; import requests; print('OK')"

# Tests pass (cd into the v4 patch, not into ~/.claude)
cd ~/Desktop/claude/comic-autopilot-v4
python3 tests/test_runner_loop.py
python3 tests/test_variant_picker.py
python3 tests/test_flow_runner_mock.py
# All three should print "All ... tests passed."
```

In Claude Code:

```
/build-comic autopilot
```

If no production-config.json exists, the briefing skill fires. If config exists, Claude reads state, then at Stage 3 you'll see:

```
Invoking flow_runner subprocess for Stage 3...
[12:34:56] Connecting to Chrome at http://localhost:9222
[12:34:57] Attached to existing Flow tab: https://labs.google/fx/tools/flow
[12:34:58] Platform OK: Flow ready
[12:35:01] Panel p01-01 (page 1) — camera=wide-establish attempt=1
...
```

Claude Code is now ONLY streaming runner stdout. It's not making per-panel decisions. AskUserQuestion is structurally inaccessible because Claude Code isn't doing anything per-panel.

## Update production-config.json for the new fields

v4 adds these optional fields. They have safe defaults if you don't set them:

```json
{
  "platform": "flow",
  "generation": {
    "variant_picker": "claude_api",
    "max_retries_per_panel": 3,
    "on_all_bad": "retry-with-cgi-anchor-boost"
  },
  "higgsfield": {
    "mode": "external_script",
    "runner_script": "/path/to/your/runner.py",
    "folder_id": "your-folder-uuid"
  }
}
```

See `docs/HIGGSFIELD-INTEGRATION.md` for the full schema.

## Test the runner end-to-end (one-panel smoke test)

```bash
# 1. Create a minimal test project
mkdir -p ~/Desktop/claude/v4-smoketest
cd ~/Desktop/claude/v4-smoketest
# Drop in a minimal shotlist.json + production-config.json + references/
# (or copy from one of your existing projects)

# 2. Health check (no work done)
python3 ~/.claude/skills/comic-production/scripts/runners/flow_runner.py \
    --project . --dry-run
# Should print: health check: OK — Flow ready at https://labs.google/fx/tools/flow

# 3. Generate one panel
python3 ~/.claude/skills/comic-production/scripts/runners/flow_runner.py \
    --project . --max-panel-seconds 600 --verbose 2>&1 | tee runner.log

# Inspect output
ls pages/panels/
cat state.json
```

If state.json shows `halt_reason: null` and the panel PNG exists at `pages/panels/p01-01.png` plus 4 variants in `pages/panels/p01-01/v{1,2,3,4}.png`, the install is working.

## Rollback

```bash
cd ~/.claude
cp backups/2026-05-14-v4/build-comic.md commands/build-comic.md
rm -rf skills/comic-production/scripts/runners
```

Restart Claude Code. Back to v3 behavior. The runners are removed; Stage 3 reverts to the per-panel Claude-Code loop.

## What v4 changed vs v3 — at a glance

| Thing | v3 | v4 |
|---|---|---|
| Stage 3 generation | Claude Code per-panel loop | Python runner subprocess |
| Variant picking | Claude Code visual inspection | Claude API call |
| State persistence | Implicit (panel files on disk) | Explicit (`state.json` atomic writes) |
| Halt conditions | Documented in prose | Codified in `HaltReason` class |
| Resume after halt | Manual (re-run, hope Claude picks up where it left off) | Automatic (state.json drives resume; runner skips accepted panels) |
| AskUserQuestion mid-run | Blocked by hook (probabilistic) | Structurally impossible (Python script can't call Claude Code tools) |
| Cost per 150-panel comic | $0 in API beyond interactive Claude | ~$3 in variant picker API + same Higgsfield/Flow costs |
| Attended time | ~6-12 hours | ~1 hour pre-work + 2-4 hours unattended |
| Quality vs interactive | Identical | Identical (same `next_panel.py` plan composer, same Claude vision criteria) |
| Continuity preservation | All L1-L13 lessons in `next_panel.py` | Same — runner faithfully executes `next_panel.py` output |

## If something goes wrong

| Symptom | Cause | Fix |
|---|---|---|
| Runner exits with `health check: FAIL` | Chrome not running with `--remote-debugging-port=9222` (Flow) or token_relay not running (Higgsfield) | Start Chrome / start token_relay, re-run |
| `ANTHROPIC_API_KEY not set` | Variant picker can't call API | `export ANTHROPIC_API_KEY=...` OR set `generation.variant_picker = "heuristic"` in config |
| Runner halts on every panel with `MISSING_REF` | Refs not in expected paths | Check `state.json -> halt_detail` for the exact missing path |
| Variant grid not found | Flow UI changed | Update `flow_selectors.py` per `docs/FLOW-SELECTORS.md` |
| Higgsfield API returns 404 | API endpoints drifted | Update URL constants in `higgsfield_runner.py` per `docs/HIGGSFIELD-INTEGRATION.md` |
| Tests fail | Python version, missing pkg | Check `python3 --version` (need 3.10+), re-run `pip install -r requirements.txt` |

For deeper debugging:

```bash
python3 ~/.claude/skills/comic-production/scripts/runners/<platform>_runner.py \
    --project . --verbose --max-panel-seconds 600 2>&1 | tee runner.log
```

`--verbose` enables debug logging. `runner.log` will have the full transcript including which selector matched, which API endpoint was called, etc.

## What about my existing Higgsfield runner.py?

Keep using it. Set `higgsfield.mode = "external_script"` in your `production-config.json` and point `higgsfield.runner_script` at your existing runner. The v4 wrapper invokes your runner as a subprocess and handles variant picking + state.json on top. See `docs/HIGGSFIELD-INTEGRATION.md`.

If your existing runner.py CLI is different from the wrapper's expectation, edit `_ExternalScriptBackend.submit_panel()` in `higgsfield_runner.py` — clearly marked, ~15 lines of code.
