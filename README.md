# claude-comic-pipeline

A set of [Claude Code](https://claude.com/claude-code) skills + a slash command that turn the CLI into a comic-production agent. Designed around [Higgsfield](https://higgsfield.ai/) for character training and panel generation.

The pipeline runs end-to-end: prose script → shotlist → references → trained character Souls → locked visual style → generated panels → continuity audit → lettered pages → PDF.

## What's in here

| Path | Purpose |
|---|---|
| `skills/reference-gathering/` | Pull reference images for characters / locations / style with provenance and a mandatory subject-verification QA pass |
| `skills/script-breakdown/` | Convert a prose script into a per-panel `shotlist.json` (camera, action, dialogue, captions, SFX) |
| `skills/soul-training/` | Validate reference coverage, curate a training set, train a Higgsfield Soul, smoke-test, register the Soul ID in the shotlist |
| `skills/style-lock/` | Distill style refs into a project-wide mandatory prompt prefix/suffix, lock model + parameters, write `style.md` |
| `skills/continuity-check/` | Cross-panel audit (wardrobe / prop / location / time-of-day) against the shotlist; reports drift before page assembly |
| `skills/page-composer/` | Assemble approved panels into pages with gutters, balloons, captions, SFX; export PDF |
| `commands/build-comic.md` | `/build-comic` orchestrator — detects project state in cwd, runs the next stage, pauses at budget gates |

## How it fits together

```
script → script-breakdown → shotlist.json
                            │
              reference-gathering ──► references/<slug>/
                            │
                  soul-training ──► soul_id back into shotlist
                            │
                     style-lock ──► style.md
                            │
              (panel generation via Higgsfield) ──► pages/panels/
                            │
              continuity-check ──► continuity-report.md
                            │
                page-composer ──► pages/page-NN.png + PDF
```

`shotlist.json` is the spine. Every stage either reads it, writes back into it, or audits against it.

## Install

These are user-level Claude Code artifacts. Copy them into your `~/.claude/` directory:

```bash
git clone https://github.com/<your-username>/claude-comic-pipeline.git
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
/build-comic               # status: detect what stage you're at, recommend next
/build-comic auto          # walk forward through stages, pause at budget-heavy gates
/build-comic <stage>       # jump to a specific stage:
                           # script | references | souls | style | generation | continuity | pages | pdf
```

Or invoke individual skills by description match — e.g. asking *"break down this script into panels"* triggers `script-breakdown` directly.

## Requirements

- **Claude Code** (skills + slash commands are CLI features)
- **Higgsfield account** with API access — `soul-training` and panel generation rely on the Higgsfield MCP server. Soul training takes ~10–20 minutes per character; panel generation costs credits per render.
- **Chrome with the Chrome-in-Chrome extension** *(optional)* — `reference-gathering` defaults to browser automation for Google Images / YouTube. Without it, references can be bootstrapped via Higgsfield text-to-image (slightly recursive but works).
- **Pillow** (Python) for `page-composer` — `pip install Pillow` if not present.

## Hard rules baked in

- `shotlist.json` is canonical. Every stage either writes to it or reads from it.
- `style-lock`'s prompt prefix/suffix goes on **every** panel prompt — no exceptions.
- `soul-training` requires a smoke-test render before a Soul is considered shipped.
- `continuity-check` never auto-regenerates panels — it surfaces a report and lets the user decide.
- `/build-comic auto` always pauses before Soul training and panel generation, regardless of mode, since those cost real money.

## Status

The pipeline has been used end-to-end for one production run (6-page short with two-Soul body-transformation handoff). Known limitations and gotchas live in the individual SKILL.md files.

This repo is the place to push improvements: better balloon placement in `page-composer`, more layout templates, smarter continuity diffing, alternative model integrations (non-Higgsfield), additional skills (lettering refinement, cover generation, pre-press CMYK pass).

## License

MIT — see [LICENSE](LICENSE).

The skills are Claude Code prompts and Python scripts. They don't bundle any IP-protected content.
