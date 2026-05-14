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
| 1. Script breakdown | `shotlist.json` exists at project root **AND** `rules_audit.py` returns no HARD findings on the shotlist (camera same-combo overuse, transformation-beats coverage). Surface SOFT findings but don't block. | `script-breakdown` |
| 2. References | every hero subject in `shotlist.json` (every `cast[]`, every `props[]` with a `ref_folder`, every `locations[]` with a `ref_folder`) points to a non-empty folder under the typed buckets (`references/characters/<id>/`, `references/props/<id>/`, `references/locations/<id>/`). For CGI comics, every hero `locations[]` folder also contains a `_source.jpg`. | `reference-gathering` |
| 3. Generation | every `panel_id` in `shotlist.json` has a matching `pages/panels/<panel_id>.png` | hand off to `comic-production` — for **Flow**, follow `references/shotlist-driven-flow.md` (deterministic per-panel loop, x4 default, Claude picks variant, per-panel accept/retry/modify checkpoint); for **Higgsfield**, translate shotlist → `panels.json` and run `runner.py`. **Act-boundary continuity gate**: at the end of every act (see *Act boundaries* below), run the rules continuity audit, surface findings inline, and pause for user sign-off before continuing to the next act. |
| 4. Continuity check | `continuity-vision-report.md` exists and is newer than the panels folder | `continuity-check` (full-issue vision audit; rules audit has already run at each act boundary during stage 3) |
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
   - **At every act boundary inside Stage 3** — run the rules continuity audit, surface findings inline, ask the user whether to fix flagged panels or continue (see *Act boundaries* below)
   - **Any regeneration** — never auto-regenerate; surface the continuity report and ask which panels to redo
   - **Stage 6 (Posting)** — never auto-post; show the per-platform caption draft and ask the user to upload
5. After each skill returns, re-detect state and continue.
6. Stop on first error or first human-needed decision; report what's left.

### Act boundaries

The continuity check should run **early and often**, not just once at the end. Production failures compound — a costume drift on page 13 silently propagates through pages 14–22 if no one looks until the whole issue is done.

**Resolving act ranges**, in priority order:

1. `acts` field at the top level of `shotlist.json`, if present:
   ```json
   "acts": [
     {"name": "Act I", "pages": [1, 7]},
     {"name": "Act II", "pages": [8, 22]},
     {"name": "Act III", "pages": [23, 30]}
   ]
   ```
2. If absent, fall back to a checkpoint every 8 pages (so a 30-page comic gets gates after pages 8, 16, 24, and at the end).

**At each boundary:**

1. Run the rules audit: `python skills/continuity-check/scripts/rules_audit.py --project . --pages <act-range>`
2. Surface the findings inline (top 5 HARD + counts).
3. If there are HARD findings, **pause** and ask whether to:
   - Fix the flagged panels before continuing
   - Skip and continue (user accepts the drift, e.g. it's an intentional `continuity_break`)
   - Run the full vision audit on this act for closer inspection
4. If clean, surface "Act N continuity gate clean" and continue.
5. After the *final* act, the full-issue vision audit becomes part of stage 4 — by then the rules pass has already swept everything, so the vision pass focuses on pixel-level drift the rules can't see.

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

### Script-breakdown-stage rules (per `script-breakdown` skill)

- **Run the Step 0 questionnaire before parsing the script.** The script-breakdown skill must poll the user on three high-stakes decisions (style preset, location strategy, transformation flavor + baseline tiers if applicable) before writing the shotlist. The model has latitude on these and downstream generation cannot recover from a silent wrong guess (the v2-April run defaulted to 2D when 3D was wanted because nothing forced a choice). See script-breakdown SKILL.md § Workflow Step 0 for the questionnaire text. Required output: `style`, `location_strategy`, and (when transformation_scenes is present) `transformation_metadata` as top-level fields in shotlist.json.
- **Run the rules audit at the end of script-breakdown.** After writing `shotlist.json`, run `python skills/continuity-check/scripts/rules_audit.py --project .` and surface HARD findings inline. HARD findings include: missing required metadata (`style`, `location_strategy`, transformation metadata), same camera (distance × angle) combo used in more than 3 panels, and (when `transformation_scenes` is declared) missing setup beat / fewer than 3 body-region beats / missing reveal beat. Block stage 2 until HARD findings are resolved — re-planning the shotlist costs nothing, regenerating panels after the fact wastes the API budget. This rule encodes the April-claudemade lesson: the failure was visible in the shotlist before any image was generated; the gate didn't exist to catch it.
- **Decompose transformation scenes into body-region beats.** Any multi-page transformation (FMG, growth arc, mutation, dress-up, charge-up, expansion) must be declared as a `transformation_scenes` entry and decomposed into per-body-region panels per the table in `script-breakdown/SKILL.md` § "Transformation decomposition." Each beat gets its own panel with a `transformation_beat` value. The aspect ratio is selected per-beat (chest → landscape, full-body reveal → portrait, ECU body region → portrait). Visual weight migrates through the body across the beats; the reveal pulls back but stays close to the figure.

### Generation-stage rules (per `comic-production` skill)

- **No baked-in lettering in the render.** Speech bubbles, SFX text, action lines, captions — NONE of these go in the generation prompt. They are added by `page-composer` as vector overlays. Baked-in lettering causes 2D illustration drift in CGI panels (lessons-learned **L7 Case B**, confirmed in the Chun-Li growth series). The render must be clean.
- **References are the truth, prompts are deltas (L10).** The prompt body describes only what is *new* in this panel: camera, action, expression, lighting state change, costume state change. Everything *constant* — character identity, costume design, location architecture — is delegated to the attached references. Every composed prompt must include the literal render directive: *"render the attached references exactly as shown. Do not reinterpret character appearance, costume design, or location architecture from the prompt text. References override prompt text on all visual identity."* This is the most important rule on this list — when the prompt re-describes constants, the model treats text and ref as competing signals and you get drift across panels (confirmed in Supergirl issue #1, panels 02 vs 05). The `next_panel.py` composer implements this skeleton.
- **Env chaining: establish-then-chain (corollary of L10).** First panel in a hero location attaches `_source.jpg` (the DAZ stand-in render). Once that first panel is accepted, it becomes the location's canonical anchor — every subsequent panel in that location attaches the *accepted* establishing shot's PNG as the env ref, **not** `_source.jpg`. The DAZ render did its job on the first panel; the accepted shot is more specific and prevents the model from re-interpolating the architecture each panel. `next_panel.py`'s `pick_location_anchor()` implements this automatically.
- **Identity-vs-pose distinction inside L10 (refinement).** L10 says "delegate constants to refs" but it does *not* say "describe nothing." The cleanest line: refs carry **identity / costume design / location architecture / lighting baseline**; the prompt carries **camera / pose / gesture / facial expression / action / momentary lighting state / momentary costume state change**. A shotlist `action` field that describes the pose is correct; one that describes the suit's color or the wall material is bleeding constants into the delta. See lessons-learned "L10 refinement" for the full table of which side each attribute lives on. Validated on a Higgsfield She-Hulk splash where the user marked "wardrobe: red top remnants..." as L10 violation but "pose: full hero roaring stance..." as load-bearing prompt content.
- **Dialogue panels must be close-framed (L12).** If a panel has on-screen dialogue (bubble types `balloon` / `thought` / `whisper` / `shout`), the camera must be close enough that the speaker is the focal point — `ecu-face` / `mcu` / `medium` / `cowboy`. Wide-establish + on-screen dialogue produces panels where the reader can't tell who's talking. `next_panel.py` emits `WARNING_DIALOGUE_CAMERA_CONFLICT` when it detects the conflict. Caption and off-panel dialogue are exempt (narration / off-screen). HALT on this warning the same way as `MISSING_*` entries.
- **Multi-speaker beats split into per-speaker panels (L13).** Any single panel with ≥3 dialogue lines from ≥2 distinct on-screen speakers must be split into one panel per beat in the shotlist — the cramped one-panel rendering is broken by design. `next_panel.py` emits `WARNING_MULTI_SPEAKER_CROWDING`. Fix the shotlist before generating; do not "just render it" with the warning visible.
- **Multi-view location references for shot-reverse-shot (L14).** Single env anchors break when the camera reverses direction in a dialogue scene. Hero locations that host facing-character dialogue should carry multiple env refs (`_source.jpg`, `_source-reverse.jpg`, etc.) and the env-chaining picks the side that matches the panel's camera direction. The current `pick_location_anchor()` is single-view aware; the multi-view extension is logged as a follow-up. Authoring guidance for now: when sourcing a hero location for a dialogue scene, capture at least one A-side and one B-side reference up front.
- **Capture every panel's job_id before submitting the next.** For Higgsfield: the runner does this in `state.json` — don't bypass it. For Flow: maintain `job_ids.md` (or equivalent) and write each ID before composing the next prompt. Missing IDs = silently broken chain = state regression in subsequent panels (**L9**).
- **View-aware chaining.** When a new panel's view category differs from the prior panel's, walk backwards through the chain and use the most recent view-compatible panel as the state anchor — not blindly N−1. See L1.5 in `comic-production/references/lessons-learned.md` for the compatibility table.
- **Camera variety enforcement.** Run the variety check from `comic-production/references/cinematic-framing.md` against any 10-panel sequence (≥5 distance categories, ≥4 angle categories, ≤3 panels at the same combo, ≥1 ECU + ≥1 wide-establish/splash). Camera-static sequences are a quality killer.
- **Env reference for hero locations.** For every panel set in a hero location, attach the location's `_source.jpg` per `comic-production/references/environment-references.md`. Text-only environment descriptions drift.
- **Multi-character POSE VARIATION block.** For any panel with 2+ characters, paste the mandatory POSE VARIATION block from `comic-production/references/multi-character-variation.md` to prevent "police lineup" failures.
- **Muscle-size lineup ref on stage-change panels only.** Per **L5**, attach the lineup ref only on the panels that transition to a new size tier — not every panel. Always include the size number in the prompt regardless.
- **No phantom refs.** If `next_panel.py`'s plan lists a `MISSING_lineup` (or any other `MISSING_*`) entry, HALT generation. The prompt was composed assuming a ref that isn't on disk; rendering would invoke the model's text-interpretation fallback and produce inconsistent results. Locate the missing asset (the plan tells you where it tried to look), drop it into one of those paths, and rerun `next_panel.py`. The first appearance of this bug (Supergirl tier-4 panel rendered without a lineup ref because `find_lineup` was looking at a path that didn't exist) produced a visibly-undersized panel that needed regenerating. Don't repeat it.
- **Verify ref count matches the plan before submitting.** When `next_panel.py` says "attach 3 refs in this order" and you've only attached 2, you have a workflow bug — stop and figure out which one was dropped before generating. The render is significantly cheaper to re-do than to live with.
- **Single-line prompts on Flow.** Flow treats `\n` in the prompt input as ENTER/submit. Use one continuous string with sentence breaks, never paragraph breaks (confirmed footgun, May 2026).

### Orchestrator rules

- **Never run two stages in parallel.** Each stage's output feeds the next; parallel runs corrupt state.
- **Always pause before budget-heavy stages.** Generation costs real money/time. Show the panel count and ask before proceeding, even in `auto` mode.
- **Never auto-regenerate panels flagged by continuity-check.** Surface the report and let the user choose which panels to redo.
- **Run the rules audit at every act boundary, not just at end of issue.** Drift compounds — catching a costume regression after Act I is cheap; catching it after all 30 pages are generated is expensive. The rules audit is free and fast (no API calls); there's no excuse to skip it mid-run.
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
| 3.5 | `continuity-check` (rules, per-act) | shotlist, panels/ | stdout findings + optional `continuity-rules-act-N.md` |
| 4 | `continuity-check` (vision, full-issue) | shotlist, panels/, character refs | `continuity-vision-report.md` |
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
