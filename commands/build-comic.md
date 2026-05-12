Comic production orchestrator. Detects the current project state in cwd, surfaces the next stage, and chains the comic skills end-to-end with human-in-the-loop pauses at budget-heavy decisions.

Argument: `$ARGUMENTS`

## How to handle the argument

- **empty** → status mode: print the state table, recommend the next stage, ask before doing anything.
- **`auto`** → walk forward stage by stage until human input is required (ambiguous script, missing refs, before generation, continuity errors, before regeneration, before posting). Pause and ask between stages that cost money or time.
- **`status`** → print the state table only; no recommendation, no actions.
- **a stage name** (`script` | `references` | `generation` | `continuity` | `pages` | `pdf` | `posting`) → jump to that stage's skill, regardless of detected state. Useful for re-runs.

## Project state detection

Inspect the cwd for these artifacts. Build the state table from what you find. **Don't fabricate state** — if a file's missing, mark it pending; don't pretend it's done.

| Stage | Done when | Skill |
|---|---|---|
| 1. Script breakdown | `shotlist.json` exists at project root | `script-breakdown` |
| 2. References | every hero subject in `shotlist.json` (every `cast[]`, every `props[]` with a `ref_folder`, every `locations[]` with a `ref_folder`) points to a non-empty folder under the typed buckets (`references/characters/<id>/`, `references/props/<id>/`, `references/locations/<id>/`). For CGI comics, every hero `locations[]` folder also contains a `_source.jpg`. | `reference-gathering` |
| 3. Generation | every `panel_id` in `shotlist.json` has a matching `pages/panels/<panel_id>.png` | hand off to `comic-production` — for **Flow**, follow `references/shotlist-driven-flow.md` (deterministic per-panel loop, x4 default, Claude picks variant, per-panel accept/retry/modify checkpoint); for **Higgsfield**, translate shotlist → `panels.json` and run `runner.py` |
| 4. Continuity check | `continuity-report.md` exists and is newer than the panels folder | `continuity-check` |
| 5. Composition | every page in `shotlist.json` has a matching `pages/page-NN.png` | `page-composer` |
| 6. Posting | `posting/posted.json` exists (or the user has marked posting as manual) | manual today; stub for future automation |
| Done | all of the above + user confirms shipping | offer PDF export, cover, next chapter |

Print the table like:

```
Stage              | Status   | Notes
-------------------|----------|------------------------------------
1. Script          | done     | shotlist.json — 12 pages, 4 cast
2. References      | partial  | 2/4 cast have refs (lara, ranger missing); 1/2 hero locations missing _source.jpg
3. Generation      | pending  | -
4. Continuity      | pending  | -
5. Composition     | pending  | -
6. Posting         | pending  | -
```

## Workflow

### Status mode (no argument)

1. Detect state.
2. Print the table.
3. Recommend the next stage in one line: *"Next: gather refs for `lara` and `ranger` and source a `_source.jpg` for the `bisons-lair` location — run `/build-comic references` or invoke the `reference-gathering` skill directly."*
4. Stop. Wait for the user.

### Auto mode (`auto`)

1. Detect state.
2. Print the table.
3. Walk stages in order, invoking the matching skill for each pending stage.
4. **Pause and confirm before any of these:**
   - **Stage 3 (Generation)** — show panel count, platform (Higgsfield or Flow), and rough cost/time estimate; ask to proceed
   - **Any regeneration** — never auto-regenerate; surface the continuity report and ask which panels to redo
   - **Stage 6 (Posting)** — never auto-post; show the per-platform caption draft and ask the user to upload
5. After each skill returns, re-detect state and continue.
6. Stop on first error or first human-needed decision; report what's left.

### Direct stage mode (named stage)

1. Skip state detection.
2. Invoke the matching skill directly with whatever the skill expects (it'll read its own inputs from cwd).
3. Return.

Mapping:
- `script` → `script-breakdown` skill
- `references` → `reference-gathering` skill
- `generation` → `comic-production` skill
- `continuity` → `continuity-check` skill
- `pages` → `page-composer` skill
- `pdf` → `page-composer` skill with PDF export
- `posting` → guided manual posting workflow (stub; future automation per-platform)

## Hard rules

These rules are non-negotiable. Every stage must respect them. Several encode lessons-learned that took real production failures to discover — don't relax them.

### Generation-stage rules (per `comic-production` skill)

- **No baked-in lettering in the render.** Speech bubbles, SFX text, action lines, captions — NONE of these go in the generation prompt. They are added by `page-composer` as vector overlays. Baked-in lettering causes 2D illustration drift in CGI panels (lessons-learned **L7 Case B**, confirmed in the Chun-Li growth series). The render must be clean.
- **Capture every panel's job_id before submitting the next.** For Higgsfield: the runner does this in `state.json` — don't bypass it. For Flow: maintain `job_ids.md` (or equivalent) and write each ID before composing the next prompt. Missing IDs = silently broken chain = state regression in subsequent panels (**L9**).
- **View-aware chaining.** When a new panel's view category differs from the prior panel's, walk backwards through the chain and use the most recent view-compatible panel as the state anchor — not blindly N−1. See L1.5 in `comic-production/references/lessons-learned.md` for the compatibility table.
- **Camera variety enforcement.** Run the variety check from `comic-production/references/cinematic-framing.md` against any 10-panel sequence (≥5 distance categories, ≥4 angle categories, ≤3 panels at the same combo, ≥1 ECU + ≥1 wide-establish/splash). Camera-static sequences are a quality killer.
- **Env reference for hero locations.** For every panel set in a hero location, attach the location's `_source.jpg` per `comic-production/references/environment-references.md`. Text-only environment descriptions drift.
- **Multi-character POSE VARIATION block.** For any panel with 2+ characters, paste the mandatory POSE VARIATION block from `comic-production/references/multi-character-variation.md` to prevent "police lineup" failures.
- **Muscle-size lineup ref on stage-change panels only.** Per **L5**, attach the lineup ref only on the panels that transition to a new size tier — not every panel. Always include the size number in the prompt regardless.
- **Single-line prompts on Flow.** Flow treats `\n` in the prompt input as ENTER/submit. Use one continuous string with sentence breaks, never paragraph breaks (confirmed footgun, May 2026).

### Orchestrator rules

- **Never run two stages in parallel.** Each stage's output feeds the next; parallel runs corrupt state.
- **Always pause before budget-heavy stages.** Generation costs real money/time. Show the panel count and ask before proceeding, even in `auto` mode.
- **Never auto-regenerate panels flagged by continuity-check.** Surface the report and let the user choose which panels to redo.
- **Detect inconsistency before acting.** If `shotlist.json` was edited after panels exist, or panels exist for panel_ids no longer in the shotlist, flag the inconsistency and ask before proceeding — don't try to "reconcile" silently.
- **Don't fabricate progress.** If you can't find an artifact, mark it pending. Don't claim a stage is done because "probably".
- **Stop on partial completeness.** If the references stage is partial (some hero subjects have refs, some don't), pause and surface the gaps before generation — the generation stage will produce inconsistent results on missing-ref subjects.
- **Posting is never automated.** This stage prepares per-platform caption drafts and a checklist; the user uploads.

## Pipeline reference

| # | Skill | Reads | Writes |
|---|---|---|---|
| 1 | `script-breakdown` | source script | `shotlist.json`, `shotlist.md` |
| 2 | `reference-gathering` | `cast[]` / `props[]` / `locations[]` slugs in shotlist | `references/<bucket>/<slug>/` with `_provenance.md` and (for locations) `_source.jpg` |
| 3 | `comic-production` | shotlist, references, env refs, lineup refs | `pages/panels/<panel_id>.png` |
| 4 | `continuity-check` | shotlist, panels/ | `continuity-report.md` |
| 5 | `page-composer` | shotlist, panels, dialogue/captions/sfx arrays, style block | `pages/page-NN.png`, optional PDF |
| 6 | (manual posting) | pages, captions | `posting/posted.json` (log of URLs posted to each platform) |

## Common asks

- **"What's the status?"** → status mode (no args)
- **"Just run everything"** → `auto`, but expect to pause for generation and posting
- **"Re-run continuity for chapter 3"** → `continuity`
- **"I edited the shotlist, what's affected?"** → status mode; report which downstream artifacts are now stale (panels if panel_ids changed, pages if dialogue/sfx changed, posting if pages changed)
- **"Start a new chapter"** → run from `script` stage in a new project subdirectory
- **"Re-letter the pages"** → `pages` (composition only; doesn't touch panels)

## Status surfacing (mandatory after every stage)

After each stage completes — in any mode (status, auto, or direct) — invoke the `comic-status-board` skill to refresh project status artifacts at the project root, then **read them back and display them inline in the chat response**. Files live on disk for persistence; the chat is the user's primary surface. Never end a stage without surfacing what changed.

| Stage just completed | Invoke `comic-status-board` to produce | Surface in chat |
|---|---|---|
| Script breakdown | `STATUS.md` | Stages summary + 1–2 sentence shotlist overview (page count, cast, locations) |
| References (each new ref) | `STATUS.md` | The References section of STATUS.md |
| References (stage end) | `STATUS.md` + `STATUS-references-board.png` | Stages summary + references-board image (use `Read` tool on the PNG so it shows inline) |
| Generation (each accepted panel) | `STATUS.md` | One-line status update referencing the panel, its accepted version, and attempt count |
| Generation (stage end) | `STATUS.md` + `STATUS-generation-board.png` | Stages summary + generation-board image inline |
| Continuity | `STATUS.md` (continuity report is its own file) | Stages summary + top 5 continuity issues if any |
| Composition (stage end) | `STATUS.md` + `STATUS-composition-board.png` | Stages summary + composition-board image inline |
| Posting | `STATUS.md` | Final stages summary + per-platform upload checklist |

**To invoke** (from the project root):

```bash
python ~/.claude/skills/comic-status-board/scripts/generate_status.py .
python ~/.claude/skills/comic-status-board/scripts/generate_composite.py . --mode references
python ~/.claude/skills/comic-status-board/scripts/generate_composite.py . --mode generation
python ~/.claude/skills/comic-status-board/scripts/generate_composite.py . --mode composition
```

(Or `Skill` invoke the `comic-status-board` skill, which handles selection.)

**Hard rule**: composite images at the project root are not optional decorations — they're the at-a-glance view of the comic's state at stage boundaries. Always generate them at their trigger moment and always surface the actual image in the chat (don't just mention that the file exists).

## End-of-stage report

After each stage runs (in any mode), report:
- What the stage did (one line)
- What artifacts were written
- **The status artifacts that were just refreshed** (STATUS.md, any composite PNGs), surfaced inline in the response per the table above
- The next pending stage and how to invoke it

Keep these reports short, but always include the status surface — the user shouldn't have to ask "where are we?" after every stage. The status view is part of the report.

## What changed from prior versions (May 2026)

This orchestrator has been simplified to reflect the post-L7 production workflow:

- **Removed stages**: `souls` (Higgsfield Souls training — no longer used; identity is anchored via face card + body ref chaining in the `comic-production` skill), `style` (no longer a pipeline stage that writes `style.md`; the `style-lock` skill folder *survives* as a **preset library** — `skills/style-lock/styles/photoreal-daz3d/`, `styles/ink-line/`, etc. — that you reference when authoring a shotlist's `style` block), `stylize` (post-production stylization — the current CGI render path produces the right look directly without a stylization pass).
- **Added stage**: `posting` (currently a manual workflow; stub for future automation).
- **Added hard rules**: no baked-in lettering (L7 Case B), job_id capture (L9), view-aware chaining (L1.5), camera variety check, env reference for hero locations, multi-character POSE VARIATION block, single-line Flow prompts.
- **Updated references stage**: now uses typed buckets (`characters/` / `locations/` / `props/`) and requires `_source.jpg` for hero CGI locations.

If you're picking up an older project that has `style.md` and trained Souls, those artifacts are inert — they won't break anything but they're not used by the new generation path. The new workflow expects style data inside `shotlist.json`'s style block and identity via the comic-production skill's face card + body ref chain.
