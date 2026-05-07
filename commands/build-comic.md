Comic production orchestrator. Detects the current project state in cwd, surfaces the next stage, and chains the comic skills end-to-end with human-in-the-loop pauses at budget-heavy decisions.

Argument: `$ARGUMENTS`

## How to handle the argument

- **empty** → status mode: print the state table, recommend the next stage, ask before doing anything.
- **`auto`** → walk forward stage by stage until human input is required (ambiguous script, missing refs, smoke-test failure, continuity errors, before generation, before regeneration). Pause and ask between stages that cost money or time.
- **`status`** → print the state table only; no recommendation, no actions.
- **a stage name** (`script` | `references` | `souls` | `style` | `generation` | `continuity` | `pages` | `pdf`) → jump to that stage's skill, regardless of detected state. Useful for re-runs.

## Project state detection

Inspect the cwd for these artifacts. Build the state table from what you find. **Don't fabricate state** — if a file's missing, mark it pending; don't pretend it's done.

| Stage | Done when | Skill |
|---|---|---|
| 1. Script breakdown | `shotlist.json` exists at project root | `script-breakdown` |
| 2. References | every `cast[].ref_folder` in shotlist.json points to a non-empty `references/<slug>/` | `reference-gathering` |
| 3. Soul training | every `cast[].soul_id` is non-null in shotlist.json | `soul-training` |
| 4. Style lock | `style.md` exists at project root | `style-lock` |
| 5. Generation | every `panel_id` in shotlist.json has a matching `pages/panels/<panel_id>.png` | hand off to `anthropic-skills:comic-production` |
| 6. Continuity check | `continuity-report.md` exists and is newer than the panels folder | `continuity-check` |
| 7. Composition | every page in shotlist.json has a matching `pages/page-NN.png` | `page-composer` |
| Done | all of the above + user confirms shipping | offer PDF export, cover, next chapter |

Print the table like:

```
Stage              | Status   | Notes
-------------------|----------|------------------------------------
1. Script          | done     | shotlist.json — 12 pages, 4 cast
2. References      | partial  | 2/4 cast have refs (lara, ranger missing)
3. Soul training   | pending  | 0/4 souls trained
4. Style lock      | pending  | -
5. Generation      | pending  | -
6. Continuity      | pending  | -
7. Composition     | pending  | -
```

## Workflow

### Status mode (no argument)

1. Detect state.
2. Print the table.
3. Recommend the next stage in one line: *"Next: gather refs for `lara` and `ranger` — run `/build-comic references` or invoke the `reference-gathering` skill directly."*
4. Stop. Wait for the user.

### Auto mode (`auto`)

1. Detect state.
2. Print the table.
3. Walk stages in order, invoking the matching skill for each pending stage.
4. **Pause and confirm before any of these:**
   - **Stage 3 (Soul training)** — show how many Souls will be trained and rough time estimate; ask to proceed
   - **Stage 5 (Generation)** — show panel count and rough cost estimate; ask to proceed
   - **Any regeneration** — never auto-regenerate; surface the continuity report and ask
   - **Style lock** when `style.md` already exists — ask before overwriting
5. After each skill returns, re-detect state and continue.
6. Stop on first error or first human-needed decision; report what's left.

### Direct stage mode (named stage)

1. Skip state detection.
2. Invoke the matching skill directly with whatever the skill expects (it'll read its own inputs from cwd).
3. Return.

Mapping:
- `script` → `script-breakdown` skill
- `references` → `reference-gathering` skill
- `souls` → `soul-training` skill
- `style` → `style-lock` skill
- `generation` → `anthropic-skills:comic-production` skill
- `continuity` → `continuity-check` skill
- `pages` → `page-composer` skill
- `pdf` → `page-composer` skill with PDF export

## Hard rules

- **Never run two stages in parallel.** Each stage's output feeds the next; parallel runs corrupt state.
- **Always pause before budget-heavy stages.** Soul training and panel generation cost real money/time. Show the count and ask before proceeding, even in `auto` mode.
- **Never auto-regenerate panels flagged by continuity-check.** Surface the report and let the user choose which panels to redo.
- **Detect inconsistency before acting.** If `shotlist.json` was edited after Souls were trained, or panels exist for panel_ids no longer in the shotlist, flag the inconsistency and ask before proceeding — don't try to "reconcile" silently.
- **Never overwrite `style.md` without confirmation.** Style changes invalidate every previously-generated panel.
- **Don't fabricate progress.** If you can't find an artifact, mark it pending. Don't claim a stage is done because "probably".
- **Stop on partial completeness.** If the references stage is partial (some cast have refs, some don't), pause and surface the gaps before training Souls — soul-training will fail coverage check on missing characters.

## Pipeline reference

| # | Skill | Reads | Writes |
|---|---|---|---|
| 1 | script-breakdown | source script | shotlist.json, shotlist.md |
| 2 | reference-gathering | cast slugs in shotlist | references/\<slug\>/ |
| 3 | soul-training | references/, shotlist | soul_ids back into shotlist, cast.md |
| 4 | style-lock | references/_style/ | style.md |
| 5 | comic-production | shotlist, style.md | pages/panels/\<panel_id\>.png |
| 6 | continuity-check | shotlist, panels/ | continuity-report.md |
| 7 | page-composer | shotlist, panels, style.md | pages/page-NN.png, optional PDF |

## Common asks

- **"What's the status?"** → status mode (no args)
- **"Just run everything"** → `auto`, but expect to pause for Souls and generation
- **"Re-run continuity for chapter 3"** → `continuity`
- **"I edited the shotlist, what's affected?"** → status mode; report which downstream artifacts are now stale (Souls if cast changed, panels if panel_ids changed, pages if dialogue changed)
- **"Start a new chapter"** → run from `script` stage in a new project subdirectory

## End-of-stage report

After each stage runs (in any mode), report:
- What the stage did (one line)
- What artifacts were written
- The next pending stage and how to invoke it

Keep these reports short. The user can `/build-comic status` any time for the full table.
