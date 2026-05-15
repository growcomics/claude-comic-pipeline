# Comic Pipeline v4 — Runners

Deterministic Python runners that drive Flow and Higgsfield for unattended comic-panel generation. Read `docs/ARCHITECTURE.md` for the why.

```
runners/
├── runner_core.py        # Shared scaffolding: state, panel loop, halts
├── variant_picker.py     # Claude API vision for variant selection (or heuristic)
├── flow_runner.py        # Playwright-based Google Flow driver
├── flow_selectors.py     # Flow UI selectors (user-editable when Google changes Flow)
├── higgsfield_runner.py  # Higgsfield runner (API mode or external-script adapter)
└── requirements.txt
```

## Install

```bash
pip install -r requirements.txt

# Only if using flow_runner.py:
playwright install chromium

# Only if using variant_picker.py with strategy=claude_api (the default):
export ANTHROPIC_API_KEY="sk-ant-..."
```

The runners live at `~/.claude/skills/comic-production/scripts/runners/` once installed. They're invoked by `/build-comic autopilot` Stage 3 as a subprocess.

## Running standalone (for testing)

```bash
# Flow
python flow_runner.py \
    --project ~/Desktop/claude/devotion-2 \
    --dry-run   # health check only, doesn't submit anything

python flow_runner.py \
    --project ~/Desktop/claude/devotion-2 \
    --max-panel-seconds 600

# Higgsfield (API mode)
python higgsfield_runner.py \
    --project ~/Desktop/claude/ring-of-hercules-vol-2 \
    --dry-run

# Higgsfield (external-script mode — invokes your existing runner.py)
# Configure higgsfield.runner_script in production-config.json first.
python higgsfield_runner.py \
    --project ~/Desktop/claude/ring-of-hercules-vol-2
```

## Tests

```bash
cd tests
python test_runner_loop.py        # end-to-end panel loop with mocked backend
python test_variant_picker.py     # variant picking strategies (incl. mocked API)
python test_flow_runner_mock.py   # FlowBackend structure without real browser
```

All three should print `All ... tests passed.` Tests use no network and no real browser.

## Configuration

Both runners read `production-config.json` at the project root. The relevant block:

```json
{
  "platform": "flow",                  // or "higgsfield"
  "transformation_type": "fmg",        // or "be", "glute", "mmg", "mixed"
  "generation": {
    "variant_picker": "claude_api",    // or "first", "heuristic"
    "max_retries_per_panel": 3,
    "on_all_bad": "retry-with-cgi-anchor-boost"  // or "halt", "skip-with-flag"
  },
  "higgsfield": {
    "mode": "api",                     // or "external_script"
    "token_relay_url": "http://localhost:7878/token",
    "api_base": "https://higgsfield.ai/api/v1",
    "folder_id": "<your-folder-id>"
  }
}
```

For the `external_script` mode, point `higgsfield.runner_script` at your existing `runner.py`. See `docs/HIGGSFIELD-INTEGRATION.md`.

## State / resume

Runners write `state.json` at the project root. After every accepted panel the file is updated atomically (write tmp + fsync + replace). On crash or halt, re-running the runner picks up at the first non-accepted panel. No work is lost.

Halt reasons (the complete list — anything else is retried):

- `MISSING_REF` — `next_panel.py` flagged a required ref absent
- `CONTENT_POLICY_REFUSAL` — platform safety filter rejected the prompt
- `AUTH_EXPIRED` — token / cookies invalid, can't recover
- `MAX_RETRIES_EXCEEDED` — same error N times
- `FILESYSTEM_ERROR` — can't write panels/state
- `API_KEY_MISSING` — `ANTHROPIC_API_KEY` unset for `variant_picker=claude_api`
- `CREDITS_EXHAUSTED` — platform out of credits
- `BROWSER_CRASH` — CDP connection lost beyond reconnect
- `SCRIPT_AMBIGUITY` — `next_panel.py` returned an error in the shotlist
- `USER_INTERRUPT` — SIGINT

Each halt writes a clean state.json + prints a one-line reason. Fix the underlying issue, re-run.

## Continuity preservation

The runners do not reimplement continuity logic. `next_panel.py` composes the per-panel plan with all L1-L13 enforcement (view-aware chaining, env ref anchoring, lineup attachment, mandatory rules block, L7 no-baked-lettering). The runner faithfully executes the plan. Quality is identical to interactive Claude-Code-driven generation; the only difference is *who clicks Generate*.

See `docs/ARCHITECTURE.md` for the full continuity-preservation breakdown.
