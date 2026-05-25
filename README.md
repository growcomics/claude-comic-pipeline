# claude-comic-pipeline

A set of [Claude Code](https://claude.com/claude-code) skills + a slash command that turn the CLI into a comic-production agent. Targets [Higgsfield](https://higgsfield.ai/) and [Google Labs Flow](https://labs.google/fx/tools/flow) (Nano Banana 2) for panel generation.

The pipeline runs end-to-end: prose script → shotlist → references (typed buckets: characters / locations / props / style) → generated panels (with view-aware chaining + iterative per-panel review) → continuity audit → lettered pages → PDF. Every stage refreshes a project-root `STATUS.md` and surfaces it (plus checkpoint composite images) directly in chat.

**Version 5 adds an `autopilot` mode** that runs the full pipeline end-to-end without per-stage gates, driven by a `production-config.json` that the `production-briefing` skill writes during a one-shot pre-flight interview. See [What's new in v5](#whats-new-in-v5) below.

## What's in here

### Skills

| Path | Purpose |
|---|---|
| `skills/reference-gathering/` | Pull reference images for characters / locations / props / style with provenance and a mandatory subject-verification QA pass. Typed-bucket folder layout. |
| `skills/script-breakdown/` | Convert a prose script into a per-panel `shotlist.json` (camera, action, dialogue/captions/sfx as data, characters, location, size). |
| `skills/style-lock/` | Preset library of starter style templates (`photoreal-daz3d`, `ink-line`, …) that shotlist authors reference when authoring the shotlist's style block. Not a pipeline stage. |
| `skills/comic-production/` | The production engine — Higgsfield runner OR Flow UI driver. Handles prompt composition, reference attachment, view-aware chaining, the per-panel iterative loop, and all the L1–L24 lessons learned from real production. |
| `skills/continuity-check/` | Cross-panel audit (wardrobe / prop / location / time-of-day) against the shotlist; reports drift before page assembly. |
| `skills/page-composer/` | Assemble approved panels into pages with gutters, balloons, captions, SFX; export PDF. All lettering happens here, never in the render prompt (when L19 baked-lettering is opt-out, which is the default). |
| `skills/comic-status-board/` | Generate and surface in chat project status — `STATUS.md` plus three checkpoint composite PNGs (`STATUS-references-board.png`, `STATUS-generation-board.png`, `STATUS-composition-board.png`) at the project root. Auto-invoked at every stage boundary. |
| `skills/production-briefing/` *(new in v5)* | One-shot pre-flight interview that collects every decision the rest of the pipeline would otherwise interrupt for. Writes `production-config.json` at the project root. Triggered by `/build-comic autopilot` when no config exists, or by phrases like "start a new comic project" / "configure autopilot". |
| `commands/build-comic.md` | `/build-comic` orchestrator — detects project state in cwd, runs the next stage, pauses at budget gates, refreshes status after every stage. Now supports three operating modes (`status`, `auto`, `autopilot`). |

### Runner infrastructure *(new in v5 — see `runners/`)*

| File | Purpose |
|---|---|
| `runners/runner_core.py` | Shared orchestrator loop with halt-detection, per-panel retry budget, `state.json` persistence, resume support. |
| `runners/flow_runner.py` | Chrome MCP-driven Flow backend; clicks, types, attaches refs, submits, picks variants. Pairs with `flow_selectors.py`. |
| `runners/higgsfield_runner.py` | Direct HTTP backend via `token_relay.js` (Node process serving the current Higgsfield browser session token at `localhost:7878/token`). For unattended overnight runs. |
| `runners/variant_picker.py` | Per-panel variant selection — heuristic strategy + Anthropic-API strategy. Fallback to heuristic when `ANTHROPIC_API_KEY` is unset. |

### Autopilot infrastructure *(new in v5 — see `autopilot/`)*

| Path | Purpose |
|---|---|
| `autopilot/configs/production-config.schema.json` | v3 schema for `production-config.json`. |
| `autopilot/configs/example-{fmg,be,glute,mmg,mixed}.json` | Per-transformation-type starter configs to copy and tweak. |
| `autopilot/hooks/stop-autopilot.py` | Claude Code `Stop` hook — forces continuation when `.autopilot-active` sentinel exists. |
| `autopilot/hooks/pre-tool-autopilot.py` | Claude Code `PreToolUse` hook — suppresses `AskUserQuestion` prompts during an autopilot run. |
| `autopilot/hooks/INSTALL.md` | How to wire the hooks into `~/.claude/settings.json`. |
| `autopilot/hooks/settings-snippet.json` | Drop-in JSON to paste into `~/.claude/settings.json`. |
| `autopilot/patches/` | Per-file patch documentation describing every autopilot integration touchpoint (purely informational — the patches are already applied in this branch). |

## What's new in v5

### Autopilot mode

`/build-comic autopilot` runs stages 1–5 (script → references → generation → continuity → composition) end-to-end without per-stage human gates. It reads `production-config.json` at project root and halts only on the approved hard conditions:

- Content-policy refusal from the upstream model
- Missing required references (face card, lineup, env source)
- `WARNING_DIALOGUE_CAMERA_CONFLICT` (L12) or `WARNING_MULTI_SPEAKER_CROWDING` (L13) raised by `next_panel.py`
- `generation.max_retries_per_panel` exceeded on a single panel
- All-variants-fail-QA when `generation.on_all_bad: halt`
- Stage-change size regression when `generation.on_size_regression: halt`

Other failures route through configurable policies (retry-with-cgi-anchor-boost, pick-best-and-flag, skip-with-flag, etc — see `autopilot/configs/production-config.schema.json`).

Posting (stage 6) remains manual. The hook system writes `.autopilot-active` and `.autopilot-stage` sentinels so the `Stop` hook can force continuation if Claude tries to halt mid-pipeline.

### Production-briefing skill

`production-briefing` is a one-shot pre-flight interview. It collects every decision the pipeline would otherwise interrupt the run to ask about: transformation type (FMG / BE / Glute / MMG / Mixed), style preset, location strategy, mandatory-rule modifications, lineup files, generation policies, continuity policies. It writes the answers into `<project>/production-config.json` v3.

After running the briefing once, `/build-comic autopilot` runs to completion without prompting.

The skill auto-invokes when `/build-comic autopilot` finds no config at project root. It also triggers on natural-language phrases like "start a new BE comic" / "configure autopilot" / "set up the project".

### Per-transformation-type rule defaults

`production-briefing` writes the right `mandatory_rules.active` defaults based on the project's `transformation_type`:

| Type | Active rules | Why these defaults |
|---|---|---|
| `fmg` | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 (all) | The historical default — the whole rule set was authored for FMG. |
| `be` | 2, 4, 5, 6, 7, 8, 9 | Rule 1 (muscle skin tone) N/A, Rule 3 (muscle=breasts) redundant, Rule 10 (no muscle reversion) replaced by BE-specific monotonicity. |
| `glute` | 2, 4, 5, 6, 7, 8, 9 | Same as BE. |
| `mmg` | 1, 2, 4, 5, 6, 7, 8, 9, 10 | Rule 3 off (no breasts). All other rules apply. |
| `mixed` | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 (all) | Multi-arc — every rule may apply on some panel. |

Plus per-type `extra_lines` for monotonic-size language, hourglass figure, V-taper, body-hair continuity, etc.

### Configurable lineup files

`next_panel.py`'s `find_lineup()` now reads `lineup_files.tier_low` / `lineup_files.tier_high` from `production-config.json`, so BE / glute / MMG projects can ship their own size-anchor lineups (place them under `<project>/references/style/`). Falls back to the FMG defaults (`muscle-size-lineup.png` / `muscle-size-lineup-4-9.png`) when the config block is missing.

### Continuity-check regeneration policies

`continuity-check` stage 2.6 hand-back is now policy-driven via `policies.regeneration`:

- `never` — log report, advance to composition. User reviews manually after the run.
- `batch-end` (default) — log report. After composition, halt cleanly with report path so the user picks what to regenerate.
- `auto-on-hard` — auto-regenerate HARD-severity panels (max 2 passes). Risky; only for budget-flexible projects.
- `halt-on-hard` — halt cleanly on the first HARD finding without composing pages.

### Runner infrastructure

The Python runner stack that drives Flow and Higgsfield from the build-comic orchestrator now lives in the repo. Three test scripts under `tests/` cover variant-picker, runner-loop, and flow-runner-mock behavior end-to-end (stdlib `unittest.mock`, no `pytest` dependency — run with `python tests/<name>.py`).

### Windows compatibility fix

`skills/continuity-check/tests/run_tests.py` now uses `sys.executable` instead of a hardcoded `python3` subprocess invocation, so the 9-fixture test suite runs on Windows (where `python3` may not be on PATH).

## How it fits together

```
script ──► script-breakdown ──► shotlist.json
                                 │
            reference-gathering ──► references/characters/ , locations/ , props/ , style/
                                 │                                        │
                                 │                                        ▼
                                 │                              comic-status-board
                                 │                              ──► STATUS.md
                                 │                              ──► STATUS-references-board.png
                                 │
              comic-production ──► pages/panels/panel-NN-<slug>/
                                 │   ├── v1.png, v2.png, v3.png …
                                 │   ├── _accepted.txt
                                 │   └── (optional) vN.notes.md, prompt-vN.txt
                                 │                                        │
                                 │                                        ▼
                                 │                              comic-status-board
                                 │                              ──► STATUS.md (per accepted panel)
                                 │                              ──► STATUS-generation-board.png (end of stage)
                                 │
                continuity-check ──► continuity-report.md
                                 │
                  page-composer ──► pages/page-NN.png + optional <project>.pdf
                                 │                                        │
                                 │                                        ▼
                                 │                              comic-status-board
                                 │                              ──► STATUS-composition-board.png
                                 │
                       (manual) ──► posting/posted.json
```

`shotlist.json` is the spine — every stage reads it, writes back into it, or audits against it. `STATUS.md` is the always-current human view, regenerated after every change.

With v5 autopilot, `production-config.json` becomes a second top-level artifact: every skill that previously paused to ask the user a question now reads its answer from there.

## Install

These are user-level Claude Code artifacts. Copy them into your `~/.claude/` directory:

```bash
git clone https://github.com/growcomics/claude-comic-pipeline.git
cd claude-comic-pipeline

# Skills go to ~/.claude/skills/
mkdir -p ~/.claude/skills
cp -R skills/* ~/.claude/skills/

# Slash command goes to ~/.claude/commands/
mkdir -p ~/.claude/commands
cp commands/build-comic.md ~/.claude/commands/
```

Restart Claude Code (or start a new session). The skills will appear in the available-skills list and `/build-comic` will be invokable.

### Optional: enable autopilot hooks

Autopilot's Stop and PreToolUse hooks let Claude continue past natural stopping points when an autopilot run is active. They are opt-in:

```bash
# Copy the hooks
mkdir -p ~/.claude/hooks
cp autopilot/hooks/*.py ~/.claude/hooks/

# Merge the snippet into ~/.claude/settings.json — see autopilot/hooks/INSTALL.md
```

Without the hooks, autopilot still works but each `Stop` event surfaces in chat (the run continues; it just isn't fully silent). Most users find this acceptable.

### Optional: variant-picker via Anthropic API

For vision-grade variant picking (better than the heuristic fallback), export an Anthropic API key:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

When unset, `variant_picker.py` falls back to the heuristic strategy (largest body build wins) and prints a one-line warning per panel.

## Usage

### Interactive / semi-auto (v4 and earlier)

```
/build-comic                  # status: detect what stage you're at, recommend next
/build-comic auto             # walk forward through stages, pause at budget-heavy gates
/build-comic <stage>          # jump to a specific stage:
                              # script | references | generation | continuity | pages | pdf | posting
```

### Autopilot (v5)

```
# 1. Run the production briefing once per project. Auto-invokes if no config exists.
/build-comic autopilot        # first run: production-briefing collects answers, writes config, exits

# 2. Run autopilot.
/build-comic autopilot        # reads config, runs stages 1–5 end-to-end
```

Or kick off natural-language: *"start a new BE comic"* → triggers production-briefing → writes config → ready for `/build-comic autopilot`.

## Requirements

- **Claude Code** (skills + slash commands are CLI features)
- **For Flow production**: a Google AI Pro or Pro Ultra account (free generation; the `comic-in-chrome` MCP drives the UI). See `skills/comic-production/references/flow-workflow.md`.
- **For Higgsfield production**: a Higgsfield account with API access via the Higgsfield MCP. The Python runner needs the token bridge running. See `skills/comic-production/SKILL.md` Phases 1–3.
- **Chrome with the Claude-in-Chrome extension** for `reference-gathering` and for Flow UI driving.
- **Pillow** (Python) for `page-composer` and `comic-status-board` composite generation — `pip install Pillow` if not present.
- **Optional, for runner stack**: `pip install requests anthropic` (see `runners/requirements.txt`).

## Hard rules baked in

These are non-negotiable rules encoded throughout the pipeline. Several came from real production failures documented in `skills/comic-production/references/lessons-learned.md`.

- **Lettering is always baked at generation time (L19, unconditional as of 2026-05-25).** Speech bubbles, captions, and SFX are composed into the generation prompt as flat 2D comic-book overlay graphics scope-bounded to the lettering only (the bodies/scene stay photoreal CGI). `next_panel.py` `_l19_lettering_block()` auto-emits whenever the panel has `dialogue[]` / `captions[]` / `sfx[]`. The earlier `allow_baked_lettering` opt-in (2026-05-13) and `skip_baked_lettering` opt-out (May 16 transition) are both retired — there is only one path. `page-composer` is layout + PDF only; it does not letter.
- **Every panel's job_id must be captured before submitting the next** (L9). For Higgsfield, the runner's `state.json` handles this automatically. For Flow, `job_ids.md` must be updated per panel. Missing IDs = silent chain break = state regression in subsequent panels.
- **View-aware chaining** (L1.5). When a new panel's view differs from the prior, walk backwards through the chain to find the most recent view-compatible panel for the state anchor — not blindly N−1.
- **Camera variety** (`comic-production/references/cinematic-framing.md`). Across any 10-panel sequence: ≥5 distinct distance categories, ≥4 distinct angle categories, ≤3 panels at the same combo, ≥1 ECU and ≥1 wide-establish/splash.
- **Camera distance for transformation beats** (L20). Body-region beats default to MCU / ecu-region; `full` is reserved for the `reveal` beat. Chapter-mean distance ≤ 3.0 and ≥ 30% of panels in middle distances {MCU, medium, cowboy}.
- **3-ref attachment ceiling** (effective limit on Flow nano-banana-2). When face card + state anchor + lineup forces the env ref to drop, `compose_prompt()` injects a dense verbal env anchor (L23) instead.
- **L21–L24 prompt-injection rules** are now auto-emitted by `compose_prompt()` in `next_panel.py` — reference-as-scene-object exclusion (L21), hair state per face-visible panel (L22), verbal env anchor on drop (L23), accessory negation list (L24).
- **Env reference for hero locations** (`environment-references.md`). Attach the location's `_source.jpg` to every panel set there. Text-only environment descriptions drift.
- **Multi-character POSE VARIATION block** (`multi-character-variation.md`). Any panel with 2+ characters gets the anti-uniformity block.
- **Status is always surfaced in chat** — never just written to disk.

## Project folder convention

Each comic project lives in its own directory with this layout:

```
<project>/
├── shotlist.json              # script-breakdown
├── production-config.json     # production-briefing (v5 only; optional for legacy / auto mode)
├── STATUS.md                  # comic-status-board (always current)
├── STATUS-*.png               # checkpoint composites
├── .autopilot-active          # autopilot sentinel (only present during a run)
├── .autopilot-stage           # current stage name (autopilot writes per stage)
├── .autopilot-halt-reason     # populated on clean autopilot halt (read by Stop hook)
├── references/
│   ├── characters/<slug>/     # face-card.png, body-baseline.png, _provenance.md
│   ├── locations/<slug>/      # _source.jpg, _provenance.md
│   ├── props/<slug>/
│   └── style/<slug>/          # custom lineup PNGs go here (lineup_files config)
├── pages/
│   ├── panels/
│   │   ├── panel-NN-<slug>/   # one folder per panel
│   │   │   ├── v1.png, v2.png, v3.png  # revision history
│   │   │   ├── _accepted.txt  # which version is accepted
│   │   │   └── vN.notes.md    # optional notes per revision
│   │   └── …
│   └── page-NN.png            # page-composer output
├── continuity-report.md
├── continuity-vision-report.md (when continuity-check vision pass runs)
├── regen-queue.md             # auto-on-hard regeneration queue (autopilot)
├── posting/posted.json
└── job_ids.md                 # chain log
```

Each panel is a folder, not a single file. Revisions accumulate inside; `_accepted.txt` marks the final choice.

## Version history

- **v5** (2026-05-14) — autopilot mode + production-briefing skill + runner infrastructure + L20-L24 lessons. **This release.**
- **v4** (2026-05-13) — L20 camera-distance bias gates; transformation-scenes structure + audit; camera-variety enforcement; L12/L13/L14 dialogue + multi-view env refs.
- **v3** and earlier — post-L7 rewrite (May 2026): pipeline shifted away from Higgsfield Souls training and post-generation stylization toward direct CGI rendering on Nano Banana 2.

Full per-change history is in [`CHANGELOG.md`](CHANGELOG.md).

## License

MIT — see [LICENSE](LICENSE).

The skills are Claude Code prompts and Python scripts. They don't bundle any IP-protected content.
