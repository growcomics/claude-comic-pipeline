# claude-comic-pipeline

A set of [Claude Code](https://claude.com/claude-code) skills + a slash command that turn the CLI into a comic-production agent. Targets [Higgsfield](https://higgsfield.ai/) and [Google Labs Flow](https://labs.google/fx/tools/flow) (Nano Banana 2) for panel generation.

The pipeline runs end-to-end: prose script → shotlist → references (typed buckets: characters / locations / props / style) → generated panels (with view-aware chaining + iterative per-panel review) → continuity audit → lettered pages → PDF. Every stage refreshes a project-root `STATUS.md` and surfaces it (plus checkpoint composite images) directly in chat.

## What's in here

| Path | Purpose |
|---|---|
| `skills/reference-gathering/` | Pull reference images for characters / locations / props / style with provenance and a mandatory subject-verification QA pass. Typed-bucket folder layout. |
| `skills/script-breakdown/` | Convert a prose script into a per-panel `shotlist.json` (camera, action, dialogue/captions/sfx as data, characters, location, size). |
| `skills/style-lock/` | **Preset library** of starter style templates (`photoreal-daz3d`, `ink-line`, …) that shotlist authors reference when authoring the shotlist's style block. Not a pipeline stage. |
| `skills/comic-production/` | The production engine — Higgsfield runner OR Flow UI driver. Handles prompt composition, reference attachment, view-aware chaining, the per-panel iterative loop, and all the L1–L9 lessons learned from real production. |
| `skills/continuity-check/` | Cross-panel audit (wardrobe / prop / location / time-of-day) against the shotlist; reports drift before page assembly. |
| `skills/page-composer/` | Assemble approved panels into pages with gutters, balloons, captions, SFX; export PDF. All lettering happens here, never in the render prompt. |
| `skills/comic-status-board/` | Generate and **surface in chat** project status — `STATUS.md` plus three checkpoint composite PNGs (`STATUS-references-board.png`, `STATUS-generation-board.png`, `STATUS-composition-board.png`) at the project root. Auto-invoked at every stage boundary so progress is visible without opening folders. |
| `commands/build-comic.md` | `/build-comic` orchestrator — detects project state in cwd, runs the next stage, pauses at budget gates, refreshes status after every stage. |

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

## Usage

From any project directory:

```
/build-comic                  # status: detect what stage you're at, recommend next
/build-comic auto             # walk forward through stages, pause at budget-heavy gates
/build-comic <stage>          # jump to a specific stage:
                              # script | references | generation | continuity | pages | pdf | posting
```

Or invoke individual skills by description match — e.g. asking *"break down this script into panels"* triggers `script-breakdown` directly. The status board auto-invokes at stage boundaries; you can also ask *"show me where we are"* / *"show me the references"* / *"production board"* to surface status on demand.

## Requirements

- **Claude Code** (skills + slash commands are CLI features)
- **For Flow production**: a Google AI Pro or Pro Ultra account (free generation; the `comic-in-chrome` MCP drives the UI). See `skills/comic-production/references/flow-workflow.md`.
- **For Higgsfield production**: a Higgsfield account with API access via the Higgsfield MCP. The Python runner needs the token bridge running. See `skills/comic-production/SKILL.md` Phases 1–3.
- **Chrome with the Claude-in-Chrome extension** for `reference-gathering` and for Flow UI driving.
- **Pillow** (Python) for `page-composer` and `comic-status-board` composite generation — `pip install Pillow` if not present.

## Hard rules baked in

These are non-negotiable rules encoded throughout the pipeline. Several came from real production failures documented in `skills/comic-production/references/lessons-learned.md`.

- **No baked-in lettering in the render** (L7 Case B). Speech bubbles, SFX text, captions, action lines — none of these go in the generation prompt. They cause 2D illustration drift in CGI panels. All lettering is added by `page-composer` post-render.
- **Every panel's job_id must be captured before submitting the next** (L9). For Higgsfield, the runner's `state.json` handles this automatically. For Flow, `job_ids.md` must be updated per panel. Missing IDs = silent chain break = state regression in subsequent panels.
- **View-aware chaining** (L1.5). When a new panel's view differs from the prior, walk backwards through the chain to find the most recent view-compatible panel for the state anchor — not blindly N−1.
- **Camera variety** (`comic-production/references/cinematic-framing.md`). Across any 10-panel sequence: ≥5 distinct distance categories, ≥4 distinct angle categories, ≤3 panels at the same combo, ≥1 ECU and ≥1 wide-establish/splash. Camera-static sequences are quality killers.
- **Env reference for hero locations** (`environment-references.md`). Attach the location's `_source.jpg` to every panel set there. Text-only environment descriptions drift.
- **Multi-character POSE VARIATION block** (`multi-character-variation.md`). Any panel with 2+ characters gets the anti-uniformity block.
- **`/build-comic auto` always pauses before generation and posting**, regardless of mode, since those have human-judgment moments worth pausing for.
- **Status is always surfaced in chat** — never just written to disk. After every stage, `comic-status-board` refreshes `STATUS.md` + the appropriate checkpoint composite, and Claude reads them back into the chat response so the user sees progress without opening folders.

## Project folder convention

Each comic project lives in its own directory with this layout (documented in full at `skills/comic-status-board/references/folder-convention.md`):

```
<project>/
├── shotlist.json              # script-breakdown
├── STATUS.md                  # comic-status-board (always current)
├── STATUS-*.png               # checkpoint composites
├── references/
│   ├── characters/<slug>/     # face-card.png, body-baseline.png, _provenance.md
│   ├── locations/<slug>/      # _source.jpg, _provenance.md
│   ├── props/<slug>/
│   └── style/<slug>/
├── pages/
│   ├── panels/
│   │   ├── panel-NN-<slug>/   # one folder per panel
│   │   │   ├── v1.png, v2.png, v3.png  # revision history
│   │   │   ├── _accepted.txt  # which version is accepted
│   │   │   └── vN.notes.md    # optional notes per revision
│   │   └── …
│   └── page-NN.png            # page-composer output
├── continuity-report.md
├── posting/posted.json
└── job_ids.md                 # chain log
```

Each panel is a **folder**, not a single file. Revisions accumulate inside; `_accepted.txt` marks the final choice. This preserves revision history and lets `comic-status-board` visualize "Panel 3 — v3 accepted (3 attempts)".

## Status

Post-L7 rewrite (May 2026): the pipeline shifted away from Higgsfield Souls training and post-generation stylization toward direct CGI rendering on Nano Banana 2 (Flow or Higgsfield Pro), anchored by face-card + body-ref chaining. All major lessons learned from real production runs are documented in `skills/comic-production/references/lessons-learned.md`. The chunli-growth-series project is the canonical post-mortem (`POSTMORTEM.md` in that folder).

Known limitations and gotchas live in the individual `SKILL.md` files. Active areas for improvement: a one-click composite contact-sheet for cross-comic comparison, automated posting per platform, deeper integration with Antigravity / Paperclip for parallel-agent dashboards, more layout templates in `page-composer`.

## License

MIT — see [LICENSE](LICENSE).

The skills are Claude Code prompts and Python scripts. They don't bundle any IP-protected content.
