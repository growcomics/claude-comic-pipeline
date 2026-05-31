# flow_runner.py — batch driver for Google Labs Flow

The piece that was missing. Several projects' `production-config.json` carry a note like:

> *"Pivoted from Flow to Higgsfield because Flow uploads can't be driven from this session and the flow_runner.py isn't installed."*

`flow_runner.py` is that tool. It drives `labs.google/fx/tools/flow` (Nano Banana 2) over the Chrome DevTools Protocol with Playwright, so a whole `shotlist.json` can be produced panel-by-panel — refs uploaded, prompt typed, x4 generated, variants downloaded — without hand-clicking the UI.

## Why this is now possible (and wasn't before)

The skill's Flow docs say drag-and-drop ref attachment is "flaky — don't attempt from automation." That was the blocker. The unlock: **every reference `next_panel.py` emits is a local file path** (the state anchor is the prior accepted PNG on disk; face card, env, and lineup are files). So instead of fighting the gallery, the driver uploads each ref through Flow's **"Upload image" file input** via Playwright's file chooser — which is deterministic. No hovering, no dragging, no coordinate guessing.

## Architecture — no duplicated brains

```
shotlist.json ──> next_panel.py --as-json ──> { prompt, aspect, count, refs[] }
                  (view-aware chaining L1.5,        │
                   ref selection, lineup/tier,      │  flow_runner.py only does MECHANICS:
                   prompt composition — UNCHANGED)   ▼
                                          connect CDP → set aspect/count →
                                          upload refs → type prompt → submit →
                                          wait → download v1..v4.png → STOP
                                                          │
                                          Claude looks at 4 PNGs, picks best,
                                          writes _accepted.txt (or `accept` cmd)
                                                          │
                                          re-run `next` → next_panel.py advances
```

`flow_runner.py` calls `next_panel.py` as a subprocess. All the hard-won logic (L1.5 view-aware chaining, lineup attachment on stage changes, tier reinforcement, prompt composition, aspect mapping, L12/L13 halt warnings) stays in `next_panel.py`. If those rules change, this driver inherits the change for free.

## One-time setup

### 1. Launch Chrome with the debugging port, sign into Flow

```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222
```

Then open `https://labs.google/fx/tools/flow`, sign in (Google AI Pro/Pro Ultra), and open or create the project for this comic. Confirm the prompt bar shows "Nano Banana 2" and "Generating will use 0 credits".

Verify the port:
```bash
curl http://127.0.0.1:9222/json/version
```

> Use `127.0.0.1`, not `localhost` — on macOS `localhost` can resolve to IPv6 `::1`, which Chrome's CDP does not bind. The runner defaults to `127.0.0.1` for this reason.

### 2. Install Playwright (client only — no browser download)

Because the runner connects to your *existing* Chrome via `connect_over_cdp`, you do **not** need `playwright install chromium`. Just the Python client:

```bash
uv venv ~/.flow-venv
uv pip install --python ~/.flow-venv/bin/python playwright
```

(Already done on this machine: `~/.flow-venv` has Playwright 1.60.)

Use `~/.flow-venv/bin/python` as the interpreter for every `flow_runner.py` call.

### 3. Calibrate selectors once (`probe`)

Flow's DOM class names are obfuscated and change. The runner keeps **all** DOM knowledge in a JSON selector config (`flow_selectors.json`) with ordered fallback strategies — never in the logic. `probe` connects to the live page and reports which selectors currently resolve, plus a screenshot and accessibility snapshot, so tuning is a config edit:

```bash
~/.flow-venv/bin/python flow_runner.py /path/to/project probe
```

This writes `<project>/.flow/probe-<ts>.png` and `probe-<ts>.json`. Open the JSON's `selectors_resolved` block. For any key showing `"matched": false`, find the right locator in the accessibility snapshot / screenshot and add an override to:

```
<project>/.flow/selectors.json
```

Only include the keys you're overriding — they merge over the defaults. Example:

```json
{
  "submit_button": [
    {"by": "css", "value": "button[aria-label='Generate']"}
  ],
  "result_images": [
    {"by": "css", "value": "div[data-media-index] img"}
  ]
}
```

Selector strategy kinds: `placeholder`, `role` (+ optional `name`, prefix with `(?i)` for a regex), `text`, `testid`, `css`, `xpath`, and `enter` (submit via Enter key). `{ASPECT}` / `{COUNT}` placeholders are substituted at runtime in `aspect_option` / `count_option`.

The **`result_images`** selector is the one most worth getting right first — it's how the runner detects completion and downloads variants. The **upload path** (`add_ref_button` / `upload_image` / `file_input`) is the most important to *function* but the least likely to drift, since it keys off the OS file chooser.

## Per-panel loop

```bash
PY=~/.flow-venv/bin/python
RUNNER=~/.claude/skills/comic-production/scripts/flow_runner.py
PROJ=/path/to/project

# See what's next without touching the browser:
$PY $RUNNER $PROJ status
$PY $RUNNER $PROJ next --dry-run      # full composed prompt + resolved ref paths

# Generate the next pending panel (uploads refs, types prompt, x4, downloads):
$PY $RUNNER $PROJ next
#   -> writes pages/panels/<panel_id>/v1.png .. v4.png
#   -> prints {"status":"awaiting_pick", "variants":[...], ...} and STOPS
```

At the `awaiting_pick` checkpoint **Claude reads the four variant PNGs** and picks the best per the QA criteria in `references/shotlist-driven-flow.md` step 6 (no 2D drift → face match → view/pose → costume continuity → size continuity → clean anatomy → no baked lettering → expressive face → composition). Then:

```bash
$PY $RUNNER $PROJ accept <panel_id> v3   # writes _accepted.txt naming the winner
$PY $RUNNER $PROJ next                    # advances to the next pending panel
```

`accept` writes `pages/panels/<panel_id>/_accepted.txt` — exactly the convention `next_panel.py` reads to mark a panel done, so the chain advances naturally and the run is fully resume-safe. Retries (re-running `next` before accepting) never advance the chain.

### Flags

| Flag | Effect |
|---|---|
| `--dry-run` | Print the composed plan + resolved refs; never opens the browser. |
| `--count x1` | Override variant count (default comes from the plan: `x4` on Flow). |
| `--timeout 240` | Per-panel generation timeout in seconds (default 180). |
| `--auto-pick v1` | Skip the Claude checkpoint, auto-accept that variant. For the "QA-at-end" mode rather than per-panel vision. |
| `--cdp-url URL` | Override CDP endpoint (default `http://127.0.0.1:9222`, or `$FLOW_CDP_URL`). |

## Exit codes & statuses

| Exit | `status` | Meaning |
|---|---|---|
| 0 | `awaiting_pick` | Variants downloaded; Claude should pick. |
| 0 | `auto_accepted` | `--auto-pick` accepted a variant; advance. |
| 0 | `complete` | No pending panels — chapter done. |
| 0 | `dry_run` / `probed` / `accepted` / `pending` | Informational commands. |
| 2 | `halt` | `next_panel.py` raised a hard-halt (L12 dialogue/camera or L13 multi-speaker). Fix the shotlist entry. |
| 3 | `timeout` | Generation didn't finish (or `result_images` needs calibration). See `_post-gen.png`, re-run `probe`. |
| 1 | `error` | CDP unreachable / Playwright missing / `next_panel.py` failed. Message has the fix. |

## Artifacts written per panel

```
pages/panels/<panel_id>/
  _pre-submit.png   # screenshot after refs+prompt, before submit (debug)
  _post-gen.png     # screenshot after generation (debug / timeout diagnosis)
  v1.png .. v4.png  # the downloaded variants
  _accepted.txt     # written on accept — names the winning variant (e.g. "v3")
```

## What this does NOT do

- **It does not pick variants.** That's Claude's vision job at the checkpoint (by design).
- **It does not letter.** Lettering is baked at generation time per L19, or handled by `page-composer`. The runner only generates and downloads.
- **It does not log in.** It reuses your already-signed-in Chrome session over CDP.
- **It does not run headless.** It attaches to your visible Chrome so you can watch and interject.

## Troubleshooting

- **`error` / ECONNREFUSED** → Chrome isn't on the debug port. Relaunch with `--remote-debugging-port=9222`; verify with the curl above.
- **`timeout` every panel** → the `result_images` selector doesn't match. Run `probe`, find the real result-tile `<img>` in the snapshot, override `result_images` in `.flow/selectors.json`.
- **Refs not attaching** (`failed_refs` non-empty) → the upload control moved. Override `add_ref_button` / `upload_image` / `file_input` after a `probe`.
- **Prompt typed but not submitted** → set `submit_button` to `[{"by":"enter"}]` (single-line prompts submit on Enter in Flow) or to the real button's `aria-label`.
- **Content-policy refusal** → not auto-recoverable; see `references/flow-workflow.md` "Content Policy Quirks" (drop celebrity names; soften cleavage/"wet" language). Re-run `next` with the shotlist edited.
