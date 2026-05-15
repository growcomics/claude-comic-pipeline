Comic production orchestrator. Detects the current project state in cwd, surfaces the next stage, and chains the comic skills end-to-end. Three operating modes: interactive (`status`, named stage), semi-auto (`auto`), and fully autonomous (`autopilot`). Human-in-the-loop pauses at budget-heavy decisions are configurable per mode.

Argument: `$ARGUMENTS`

## How to handle the argument

- **empty** → status mode: print the state table, recommend the next stage, ask before doing anything.
- **`status`** → print the state table only; no recommendation, no actions.
- **`auto`** → walk forward stage by stage until human input is required (ambiguous script, missing refs, before generation, continuity errors, before regeneration, before posting). Pause and ask between stages that cost money or time. **Default behavior, backward compatible with all prior usage.**
- **`autopilot`** → fully autonomous mode. Reads `production-config.json` at project root and runs stages 1-5 end-to-end without per-stage gates. Halts ONLY on the approved hard conditions (see "Autopilot mode" below). If no config exists, auto-invokes the `production-briefing` skill, writes the config, and exits — the user re-runs `/build-comic autopilot` to start the actual production. Posting (stage 6) remains manual.
- **a stage name** (`script` | `references` | `generation` | `continuity` | `pages` | `pdf` | `posting`) → jump to that stage's skill, regardless of detected state. Useful for re-runs.

## Project state detection

Inspect the cwd for these artifacts. Build the state table from what you find. **Don't fabricate state** — if a file's missing, mark it pending; don't pretend it's done.

| Stage | Done when | Skill |
|---|---|---|
| 1. Script breakdown | `shotlist.json` exists at project root **AND** `rules_audit.py` returns no HARD findings on the shotlist (camera same-combo overuse, transformation-beats coverage, required metadata: `style`, `location_strategy`, `transformation_metadata` when applicable). Surface SOFT findings but don't block. | `script-breakdown` |
| 2. References | every hero subject in `shotlist.json` (every `cast[]`, every `props[]` with a `ref_folder`, every `locations[]` with a `ref_folder`) points to a non-empty folder under the typed buckets (`references/characters/<id>/`, `references/props/<id>/`, `references/locations/<id>/`). For CGI comics, every hero `locations[]` folder also contains a `_source.jpg`. | `reference-gathering` |
| 3. Generation | every `panel_id` in `shotlist.json` has a matching `pages/panels/<panel_id>.png` | hand off to `comic-production` — for **Flow**, follow `references/shotlist-driven-flow.md` (deterministic per-panel loop, x4 default, Claude picks variant, per-panel accept/retry/modify checkpoint); for **Higgsfield**, translate shotlist → `panels.json` and run `runner.py`. **Act-boundary continuity gate**: at the end of every act (see *Act boundaries* below), run the rules continuity audit. In `auto` mode pause for sign-off; in `autopilot` mode use `policies.act_boundary_audit` from `production-config.json` to decide. |
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

In autopilot mode also print a second line below the table:

```
Autopilot active — config: production-config.json | next halt only on approved conditions
```

## Workflow

### Status mode (no argument)

1. Detect state.
2. Print the table.
3. Recommend the next stage in one line: *"Next: gather refs for `lara` and `ranger` and source a `_source.jpg` for the `bisons-lair` location — run `/build-comic references` or invoke the `reference-gathering` skill directly."*
4. Stop. Wait for the user.

### Auto mode (`auto`) — UNCHANGED FROM PRIOR VERSIONS

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

### Autopilot mode (`autopilot`) — NEW

Fully autonomous from script through PDF. No per-stage gates. Decisions previously asked in chat are read from `production-config.json` at project root.

**Setup phase (first invocation, no config exists):**

1. Detect state. Read `production-config.json` at project root.
2. If not present → invoke the `production-briefing` skill. That skill asks every setup question in one batch — including the Step 0 questionnaire normally surfaced by `script-breakdown` (style preset, location strategy, transformation flavor, baseline tiers) — writes the config, and exits. Print:
   ```
   Config written. Re-run `/build-comic autopilot` to start production.
   ```
   Exit. Do NOT chain into production immediately — the user might want to review/edit the config before starting work.

**Run phase (config exists):**

1. Detect state.
2. Print the table + the autopilot active line.
3. Touch sentinel file `<project_root>/.autopilot-active` (one line with current ISO timestamp). The Stop hook reads this to know to force continuation if Claude tries to halt mid-pipeline.
4. Walk stages 1→5 in strict order. At each previously-gated decision, READ THE ANSWER FROM `production-config.json` INSTEAD OF ASKING:

   | Previously-gated decision | Now reads from |
   |---|---|
   | Step 0 questionnaire (style, location_strategy, transformation_metadata) | `script_breakdown.style_preset`, `script_breakdown.location_strategy`, `script_breakdown.transformation_metadata` — fed straight into `shotlist.json` at top level |
   | Mandatory rules block to apply | `mandatory_rules.active` + `mandatory_rules.extra_lines` |
   | Stage 1 audit gate behavior | `policies.script_breakdown_audit` (default `halt-on-hard`) — HARD findings halt, SOFT findings logged |
   | Stage 3 enter-generation gate | `policies.stage3_gate` (default `auto`) |
   | Act-boundary continuity halt | `policies.act_boundary_audit` |
   | Regeneration after vision audit | `policies.regeneration` |
   | Variant pick per panel | `generation.pick_variant` (default `claude`) |
   | Max retries before halt | `generation.max_retries_per_panel` (default 3) |
   | All-variants-bad behavior | `generation.on_all_bad` (default `retry-with-cgi-anchor-boost`) |
   | Reference gathering policy | `references.policy` (default `skip-if-populated`) |
   | Vision audit scope | `continuity.vision_audit_scope` |
   | PDF export | `page_composer.export_pdf` |

5. At each stage boundary: write current stage name to `<project_root>/.autopilot-stage`. Refresh status board per the surface table below. Continue.

**Stage 3 (Generation) — runner subprocess hand-off — NEW IN v4.** When the pipeline reaches Stage 3, do NOT enter a per-panel loop in Claude Code. Instead, hand off to a deterministic Python runner subprocess that drives Flow or Higgsfield without Claude Code involvement:

   ```bash
   python ~/.claude/skills/comic-production/scripts/runners/<platform>_runner.py \
       --project <project_root> \
       --config <project_root>/production-config.json \
       --max-panel-seconds 600
   ```

   where `<platform>` is `flow` or `higgsfield` (read from `production-config.json -> platform`).

   The runner:
   - Reads `shotlist.json` + `production-config.json`
   - For each pending panel: calls `next_panel.py --as-json` to get the per-panel plan (same composition logic, all L1-L13 lessons enforced)
   - Submits the panel to the platform (Playwright for Flow, HTTP API for Higgsfield)
   - Saves all 4 variants to `pages/panels/<panel_id>/v[1-4].png`
   - Calls the Claude API (not Claude Code) for variant picking — preserves quality with zero AskUserQuestion exposure since API calls don't have interactive tools
   - Copies the picked variant to the canonical `pages/panels/<panel_id>.png` (where `next_panel.py` looks for it on subsequent panels)
   - Updates `state.json` atomically after every panel
   - Loops to the next panel

   **During Stage 3, Claude Code's only job is to invoke the runner via Bash and stream its stdout to chat as status updates.** No per-panel decisions are made by Claude Code. The runner cannot call `AskUserQuestion` because it's a Python script, not a Claude session. This is a hard structural guarantee, not a probabilistic one.

   Runner exit codes:
   - `0`: all panels accepted → advance to Stage 4 (continuity check)
   - `1`: halted on an approved condition → read `state.json -> halt_reason` and `halt_detail`, surface to user, write `.autopilot-halt-reason`, stop cleanly
   - `2`: catastrophic error before any work started (e.g. missing `production-config.json`) → surface and stop

   The runner's `state.json` is canonical for resume. If the runner halts on panel `p01-05`, fixing the underlying issue (drop in the missing ref file, edit the refused prompt) and re-running `/build-comic autopilot` picks up at `p01-05` — earlier panels are already accepted on disk and `next_panel.py` skips them.

   **Continuity is preserved** because `next_panel.py` is the same composer as before. View-aware chaining (L1.5), env ref anchoring (L10), face card attachment per character, L11 lineup attachment, mandatory rules block — all enforced identically. The runner faithfully executes the plan; the runner is not a composer.

   **Variant picking quality is preserved** because the runner uses the Claude API directly to inspect all 4 variants and pick the best one per the same criteria documented in `shotlist-driven-flow.md` step 6 (face acting, anatomy, CGI fidelity, camera adherence, reference adherence, composition). The picker uses transformation-type-specific evaluation criteria (different anchors for FMG vs BE vs glute vs MMG vs mixed). See `docs/VARIANT-PICKING.md`.

   **Cost**: variant picker uses ~$0.02/panel via `claude-opus-4-7`. A 150-panel comic costs ~$3 for picking. Cheaper alternatives: set `generation.variant_picker = "heuristic"` (free, ~55-65% pick accuracy) or `"first"` (free, picks V1 always — for testing only).

6. **Approved halt conditions** — autopilot is permitted to stop ONLY on these. Everything else continues with config defaults.

   | Halt condition | Trigger | Action |
   |---|---|---|
   | Content-policy refusal | Flow safety filter rejects a prompt (runner returns `state.halt_reason = "CONTENT_POLICY_REFUSAL"`) | Read `state.json` → `halt_detail` for the refusal text. Surface the refused prompt + suggested edit in chat. Write reason to `.autopilot-halt-reason`, delete `.autopilot-active`, stop cleanly. |
   | `MISSING_*` ref guardrail | `next_panel.py` returns `MISSING_lineup` or any other `MISSING_*` (runner returns `state.halt_reason = "MISSING_REF"`) | Read `state.halt_detail`, surface the missing asset path + where to drop the file. Same cleanup. |
   | `WARNING_DIALOGUE_CAMERA_CONFLICT` (L12) | `next_panel.py` detects on-screen dialogue with wide-establish or far camera | Same. Surface offending panel + camera. Fix shotlist before resuming. |
   | `WARNING_MULTI_SPEAKER_CROWDING` (L13) | `next_panel.py` detects panel with ≥3 dialogue lines from ≥2 on-screen speakers | Same. Surface offending panel. Split into per-speaker beats in the shotlist before resuming. |
   | Stage 1 audit HARD finding | `rules_audit.py` returns HARD findings at end of script-breakdown | Surface the audit report. User edits shotlist; re-run autopilot. |
   | Environmental failure | Chrome dead, token bridge dead, filesystem unwritable (runner returns `AUTH_EXPIRED`, `BROWSER_CRASH`, `FILESYSTEM_ERROR`, or `CREDITS_EXHAUSTED`) | Surface the error + recovery steps from `state.halt_detail`. |
   | Script-level ambiguity | Shotlist references a slug not in cast[], unknown camera category, etc. (runner returns `SCRIPT_AMBIGUITY`) | Surface the offending shotlist entry. |
   | Variant picker API key missing | `ANTHROPIC_API_KEY` env var unset and `variant_picker=claude_api` (runner returns `API_KEY_MISSING`) | Tell user to `export ANTHROPIC_API_KEY=...` OR change `generation.variant_picker` to `heuristic` in config. |
   | Max retries on a single panel | Same error N times in a row (runner returns `MAX_RETRIES_EXCEEDED`) | Read `state.halt_detail` for the recurring error. Surface it. |

   These conditions are not user-configurable in the schema — they're listed in `halt_conditions.*` for transparency but are always-on. Reasoning: every other decision can be defaulted via the config; these are stop-and-fix.

**Tool-use prohibitions during autopilot** — these aren't suggestions, they're hard rules. The `pre-tool-autopilot.py` PreToolUse hook enforces the first one; the rest are prose-enforced. Violating them defeats the entire point of autopilot.

   - **NEVER call `AskUserQuestion` while `.autopilot-active` exists.** Not for strategic decisions, not for "honest checkpoints", not for "how should I proceed?", not for time-budget framing, not for variant picks, not for anything. If you find yourself reaching for AskUserQuestion mid-run, stop and ask three questions in your own head first:
     1. *Is this decision answered somewhere in `production-config.json`?* — almost always yes. `policies.*` covers continuation/halt/regen decisions; `generation.*` covers retry/variant/all-bad decisions; `mandatory_rules.*` covers what to bake into prompts. Read the config, decide accordingly, continue.
     2. *Is this one of the approved hard-halt conditions?* — if yes, write the reason to `.autopilot-halt-reason` and stop. Don't ask the user about it — they'll see the halt-reason file and the explanation in chat when they come back.
     3. *Is this a meta-strategic question (e.g. "should we pivot platforms", "should I stop now since this is taking long", "want me to finish only this niche")?* — the answer is ALWAYS continue per the configured platform and full scope. The user chose autopilot specifically to walk away from these questions. Don't second-guess that choice mid-run. If you genuinely believe a pivot is warranted (rare), write your reasoning to `.autopilot-halt-reason` as a script-ambiguity halt and stop — the user reviews it next session.
   - **NEVER write a chat message that ends with a question and waits for the user.** That's a stop-and-ask in disguise. The Stop hook will catch it and shove you back to work, but the user sees the dangling question — looks broken. Frame everything as a decision-made statement: *"Variant V3 picked for panel 04 (best face acting). Continuing to panel 05."*
   - **NEVER pause "for user check-in" or "to confirm direction."** Status board surfaces are silent — they refresh `STATUS.md` and read it back into chat for the transcript record, then continue. No confirmation needed.
   - **Status updates are one-line declarations, not invitations to interject.** Good: *"Panel 12 done (V1 picked, accepted on first try). Advancing to panel 13."* Bad: *"Panel 12 looks good — should I continue to 13 or do you want to review?"* The bad version is exactly what triggers the user's installed autopilot to feel broken.

   If you violate any of the above, the pre-tool-use hook blocks the AskUserQuestion call with a `permissionDecision: deny` and a strongly-worded reason explaining that autopilot is active and you should consult the config instead. Then the Stop hook catches any resulting halt. But two hooks shouldn't have to clean up after a prompt-side violation — the prose above is the primary defense.

   **One legitimate exception**: if `.autopilot-halt-reason` already exists (autopilot is winding down on an approved hard-halt), `AskUserQuestion` is allowed for a final clarification about the halt cause. The pre-tool-use hook checks for the halt-reason file and lets the call through in that case.

7. On reaching stage 5 done (page-composer output + optional PDF) → delete `.autopilot-active`, delete `.autopilot-stage`, stop cleanly. Print final status board with composition checkpoint composite inline. Mention posting is the user's job per the policy.

**Status surface during autopilot:**

After every stage AND after every accepted panel during stage 3, invoke `comic-status-board` to refresh `STATUS.md`. Read it back into chat per the surface table below. Surfacing is mandatory in autopilot too — the user is presumably away; they'll catch up by reading the chat history.

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

**At each boundary, behavior depends on mode:**

In **`auto` mode** (unchanged):
1. Run the rules audit: `python skills/continuity-check/scripts/rules_audit.py --project . --pages <act-range>`
2. Surface the findings inline (top 5 HARD + counts).
3. If there are HARD findings, **pause** and ask whether to:
   - Fix the flagged panels before continuing
   - Skip and continue (user accepts the drift, e.g. it's an intentional `continuity_break`)
   - Run the full vision audit on this act for closer inspection
4. If clean, surface "Act N continuity gate clean" and continue.

In **`autopilot` mode**:
1. Same rules audit.
2. Surface findings inline.
3. Read `policies.act_boundary_audit` and act accordingly:
   - `always-halt` → stop and report, regardless of severity
   - `halt-on-hard` → continue silently if clean or SOFT-only; halt and report if any HARD
   - `halt-on-hard-or-soft` → halt and report on any finding
   - `log-only` → log findings to `continuity-rules-act-N.md`, continue regardless
4. After the *final* act, the full-issue vision audit becomes part of stage 4 — by then the rules pass has already swept everything, so the vision pass focuses on pixel-level drift the rules can't see.

## Hard rules

These rules are non-negotiable. Every stage must respect them. Several encode lessons-learned that took real production failures to discover — don't relax them.

### Script-breakdown-stage rules (per `script-breakdown` skill)

- **Run the Step 0 questionnaire before parsing the script.** The script-breakdown skill must poll the user on three high-stakes decisions (style preset, location strategy, transformation flavor + baseline tiers if applicable) before writing the shotlist. The model has latitude on these and downstream generation cannot recover from a silent wrong guess (the v2-April run defaulted to 2D when 3D was wanted because nothing forced a choice). See script-breakdown SKILL.md § Workflow Step 0 for the questionnaire text. Required output: `style`, `location_strategy`, and (when transformation_scenes is present) `transformation_metadata` as top-level fields in shotlist.json. **In autopilot mode**, these answers come from `production-config.json`'s `script_breakdown.*` block — the briefing collected them at project setup, so script-breakdown does NOT re-prompt.
- **Run the rules audit at the end of script-breakdown.** After writing `shotlist.json`, run `python skills/continuity-check/scripts/rules_audit.py --project .` and surface HARD findings inline. HARD findings include: missing required metadata (`style`, `location_strategy`, transformation metadata), same camera (distance × angle) combo used in more than 3 panels, and (when `transformation_scenes` is declared) missing setup beat / fewer than 3 body-region beats / missing reveal beat. Block stage 2 until HARD findings are resolved — re-planning the shotlist costs nothing, regenerating panels after the fact wastes the API budget. **In autopilot mode**, behavior is governed by `policies.script_breakdown_audit`: `halt-on-hard` (default) stops cleanly on HARD findings; `log-only` records the report and continues.
- **Decompose transformation scenes into body-region beats.** Any multi-page transformation (FMG, growth arc, mutation, dress-up, charge-up, expansion) must be declared as a `transformation_scenes` entry and decomposed into per-body-region panels per the table in `script-breakdown/SKILL.md` § "Transformation decomposition." Each beat gets its own panel with a `transformation_beat` value. The aspect ratio is selected per-beat (chest → landscape, full-body reveal → portrait, ECU body region → portrait). Visual weight migrates through the body across the beats; the reveal pulls back but stays close to the figure.

### Generation-stage rules (per `comic-production` skill)

- **No baked-in lettering in the render.** Speech bubbles, SFX text, action lines, captions — NONE of these go in the generation prompt. They are added by `page-composer` as vector overlays. Baked-in lettering causes 2D illustration drift in CGI panels (lessons-learned **L7 Case B**, confirmed in the Chun-Li growth series). The render must be clean. *(Note: lessons-learned.md L19 records an experimental reversal of this rule with aggressive anchoring; the build-comic hard rule remains "no baked lettering" pending validation. If a project opts into L19, set `mandatory_rules.allow_baked_lettering=true` in production-config.json.)*
- **References are the truth, prompts are deltas (L10).** The prompt body describes only what is *new* in this panel: camera, action, expression, lighting state change, costume state change. Everything *constant* — character identity, costume design, location architecture — is delegated to the attached references. Every composed prompt must include the literal render directive: *"render the attached references exactly as shown. Do not reinterpret character appearance, costume design, or location architecture from the prompt text. References override prompt text on all visual identity."* This is the most important rule on this list — when the prompt re-describes constants, the model treats text and ref as competing signals and you get drift across panels (confirmed in Supergirl issue #1, panels 02 vs 05). The `next_panel.py` composer implements this skeleton.
- **Env chaining: establish-then-chain (corollary of L10).** First panel in a hero location attaches `_source.jpg` (the DAZ stand-in render). Once that first panel is accepted, it becomes the location's canonical anchor — every subsequent panel in that location attaches the *accepted* establishing shot's PNG as the env ref, **not** `_source.jpg`. The DAZ render did its job on the first panel; the accepted shot is more specific and prevents the model from re-interpolating the architecture each panel. `next_panel.py`'s `pick_location_anchor()` implements this automatically.
- **Identity-vs-pose distinction inside L10 (refinement).** L10 says "delegate constants to refs" but it does *not* say "describe nothing." The cleanest line: refs carry **identity / costume design / location architecture / lighting baseline**; the prompt carries **camera / pose / gesture / facial expression / action / momentary lighting state / momentary costume state change**. A shotlist `action` field that describes the pose is correct; one that describes the suit's color or the wall material is bleeding constants into the delta. See lessons-learned "L10 refinement" for the full table of which side each attribute lives on. Validated on a Higgsfield She-Hulk splash where the user marked "wardrobe: red top remnants..." as L10 violation but "pose: full hero roaring stance..." as load-bearing prompt content.
- **Dialogue panels must be close-framed (L12).** If a panel has on-screen dialogue (bubble types `balloon` / `thought` / `whisper` / `shout`), the camera must be close enough that the speaker is the focal point — `ecu-face` / `mcu` / `medium` / `cowboy`. Wide-establish + on-screen dialogue produces panels where the reader can't tell who's talking. `next_panel.py` emits `WARNING_DIALOGUE_CAMERA_CONFLICT` when it detects the conflict. Caption and off-panel dialogue are exempt (narration / off-screen). HALT on this warning the same way as `MISSING_*` entries — in autopilot mode this is an approved halt condition.
- **Multi-speaker beats split into per-speaker panels (L13).** Any single panel with ≥3 dialogue lines from ≥2 distinct on-screen speakers must be split into one panel per beat in the shotlist — the cramped one-panel rendering is broken by design. `next_panel.py` emits `WARNING_MULTI_SPEAKER_CROWDING`. Fix the shotlist before generating; do not "just render it" with the warning visible. HALT on this warning the same way as `MISSING_*` — in autopilot mode this is an approved halt condition.
- **Multi-view location references for shot-reverse-shot (L14).** Single env anchors break when the camera reverses direction in a dialogue scene. Hero locations that host facing-character dialogue should carry multiple env refs (`_source.jpg`, `_source-reverse.jpg`, etc.) and the env-chaining picks the side that matches the panel's camera direction. The current `pick_location_anchor()` is single-view aware; the multi-view extension is logged as a follow-up. Authoring guidance for now: when sourcing a hero location for a dialogue scene, capture at least one A-side and one B-side reference up front.
- **Capture every panel's job_id before submitting the next.** For Higgsfield: the runner does this in `state.json` — don't bypass it. For Flow: maintain `job_ids.md` (or equivalent) and write each ID before composing the next prompt. Missing IDs = silently broken chain = state regression in subsequent panels (**L9**).
- **View-aware chaining.** When a new panel's view category differs from the prior panel's, walk backwards through the chain and use the most recent view-compatible panel as the state anchor — not blindly N−1. See L1.5 in `comic-production/references/lessons-learned.md` for the compatibility table.
- **Camera variety enforcement.** Run the variety check from `comic-production/references/cinematic-framing.md` against any 10-panel sequence (≥5 distance categories, ≥4 angle categories, ≤3 panels at the same combo, ≥1 ECU + ≥1 wide-establish/splash). Camera-static sequences are a quality killer.
- **Env reference for hero locations.** For every panel set in a hero location, attach the location's `_source.jpg` per `comic-production/references/environment-references.md`. Text-only environment descriptions drift.
- **Multi-character POSE VARIATION block.** For any panel with 2+ characters, paste the mandatory POSE VARIATION block from `comic-production/references/multi-character-variation.md` to prevent "police lineup" failures.
- **Muscle-size lineup ref on full-body or stage-change panels (L11).** Per L11 (expanded from L5), attach the lineup ref on every full-body camera panel of the arc character AND on every stage-change panel — not just stage changes. ECU and mcu panels skip the lineup. Always include the size number in the prompt regardless.
- **No phantom refs.** If `next_panel.py`'s plan lists a `MISSING_lineup` (or any other `MISSING_*`) entry, HALT generation. The prompt was composed assuming a ref that isn't on disk; rendering would invoke the model's text-interpretation fallback and produce inconsistent results. Locate the missing asset (the plan tells you where it tried to look), drop it into one of those paths, and rerun `next_panel.py`. In autopilot mode this triggers the missing-ref-guardrail halt — write the path to `.autopilot-halt-reason` and stop cleanly.
- **Verify ref count matches the plan before submitting.** When `next_panel.py` says "attach 3 refs in this order" and you've only attached 2, you have a workflow bug — stop and figure out which one was dropped before generating.
- **Single-line prompts on Flow.** Flow treats `\n` in the prompt input as ENTER/submit. Use one continuous string with sentence breaks, never paragraph breaks (confirmed footgun, May 2026).
- **Mandatory rules block source.** If `production-config.json` exists, read `mandatory_rules.active` and `mandatory_rules.extra_lines` from it. Compose the block from rules 1-10 minus any not in `active`, plus any `extra_lines`. If no config exists, fall back to the legacy behavior: present the full rules list at project start and ask which to drop.

### Orchestrator rules

- **Never run two stages in parallel.** Each stage's output feeds the next; parallel runs corrupt state.
- **Always pause before budget-heavy stages in `auto` mode.** Generation costs real money/time. Show the panel count and ask before proceeding. In `autopilot` mode this gate reads `policies.stage3_gate` from the config; default `auto` skips the gate. To preserve the legacy ask-before-generate behavior in autopilot, set `policies.stage3_gate=halt`.
- **Never auto-regenerate panels flagged by continuity-check in `auto` mode.** In `autopilot` mode, read `policies.regeneration`:
  - `never` → log only, never regenerate
  - `batch-end` → collect flagged panels, halt after stage 5 for user review (default)
  - `auto-on-hard` → regenerate HARD findings without asking (risky — can introduce new drift)
  - `halt-on-hard` → stop on first HARD finding (legacy behavior)
- **Run the rules audit at every act boundary, not just at end of issue.** Drift compounds — catching a costume regression after Act I is cheap; catching it after all 30 pages are generated is expensive. The rules audit is free and fast (no API calls); there's no excuse to skip it mid-run. The act-boundary policy controls halt behavior, not whether to run the audit at all.
- **Detect inconsistency before acting.** If `shotlist.json` was edited after panels exist, or panels exist for panel_ids no longer in the shotlist, flag the inconsistency and ask before proceeding — don't try to "reconcile" silently. In autopilot mode this is a script-ambiguity halt.
- **Don't fabricate progress.** If you can't find an artifact, mark it pending. Don't claim a stage is done because "probably".
- **Stop on partial completeness.** If the references stage is partial (some hero subjects have refs, some don't), pause and surface the gaps before generation — the generation stage will produce inconsistent results on missing-ref subjects. In autopilot mode this is a script-ambiguity halt.
- **Posting is never automated, in any mode.** This stage prepares per-platform caption drafts and a checklist; the user uploads. Autopilot stops cleanly after stage 5.

## Pipeline reference

| # | Skill | Reads | Writes |
|---|---|---|---|
| 0 | `production-briefing` (new) | user interview, including Step 0 (style preset, location strategy, transformation flavor + baseline tiers) | `production-config.json` |
| 1 | `script-breakdown` | source script, `production-config.json` (Step 0 answers when present) | `shotlist.json`, `shotlist.md` |
| 2 | `reference-gathering` | `cast[]` / `props[]` / `locations[]` slugs in shotlist | `references/<bucket>/<slug>/` with `_provenance.md` and (for locations) `_source.jpg` |
| 3 | `comic-production` | shotlist, references, env refs, lineup refs, **production-config.json** | `pages/panels/<panel_id>.png` |
| 3.5 | `continuity-check` (rules, per-act) | shotlist, panels/ | stdout findings + optional `continuity-rules-act-N.md` |
| 4 | `continuity-check` (vision, full-issue) | shotlist, panels/, character refs | `continuity-vision-report.md` |
| 5 | `page-composer` | shotlist, panels, dialogue/captions/sfx arrays, style block | `pages/page-NN.png`, optional PDF |
| 6 | (manual posting) | pages, captions | `posting/posted.json` (log of URLs posted to each platform) |

## Common asks

- **"What's the status?"** → status mode (no args)
- **"Just run everything"** → `auto` if you want gates, `autopilot` if you want full autonomy
- **"Set up a new comic"** → `autopilot` on a fresh project root → triggers `production-briefing` first
- **"Re-run continuity for chapter 3"** → `continuity`
- **"I edited the shotlist, what's affected?"** → status mode; report which downstream artifacts are now stale (panels if panel_ids changed, pages if dialogue/sfx changed, posting if pages changed)
- **"Start a new chapter"** → run from `script` stage in a new project subdirectory (and write a new `production-config.json` for that subdirectory if using autopilot)
- **"Re-letter the pages"** → `pages` (composition only; doesn't touch panels)
- **"I want autopilot but I want to pick variants per panel"** → set `generation.pick_variant=user` in the config. Autopilot still consolidates everything else.
- **"Resume autopilot after a halt"** → fix the underlying issue (drop the missing lineup file, edit the offending shotlist entry, etc.), then re-run `/build-comic autopilot`. State detection picks up where it left off; the sentinel files are reset.

## Status surfacing (mandatory after every stage)

After each stage completes — in any mode (status, auto, autopilot, or direct) — invoke the `comic-status-board` skill to refresh project status artifacts at the project root, then **read them back and display them inline in the chat response**. Files live on disk for persistence; the chat is the user's primary surface. Never end a stage without surfacing what changed.

| Stage just completed | Invoke `comic-status-board` to produce | Surface in chat |
|---|---|---|
| Briefing (autopilot setup phase) | n/a — config file path printed | Path to config + "next: re-run autopilot" |
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

**Hard rule**: composite images at the project root are not optional decorations — they're the at-a-glance view of the comic's state at stage boundaries. Always generate them at their trigger moment and always surface the actual image in the chat (don't just mention that the file exists). This is true in autopilot mode too — even though no one is watching live, the chat transcript becomes the user's post-hoc audit trail.

## End-of-stage report

After each stage runs (in any mode), report:
- What the stage did (one line)
- What artifacts were written
- **The status artifacts that were just refreshed** (STATUS.md, any composite PNGs), surfaced inline in the response per the table above
- The next pending stage and how to invoke it (in autopilot mode: just "continuing to stage N")

Keep these reports short, but always include the status surface — the user shouldn't have to ask "where are we?" after every stage. The status view is part of the report.

## What changed from prior versions (May 2026)

- **Added autopilot mode**: fully autonomous end-to-end run, decisions read from `production-config.json` instead of asked per-stage. Triggered by `/build-comic autopilot`. Halts only on the approved conditions: content-policy refusal, MISSING_* ref guardrail, WARNING_DIALOGUE_CAMERA_CONFLICT, WARNING_MULTI_SPEAKER_CROWDING, Stage 1 audit HARD, environmental failure, script ambiguity.
- **Added `production-briefing` skill**: one-shot pre-flight interview that writes `production-config.json`. Auto-invoked by autopilot when no config exists. Absorbs the Step 0 questionnaire from script-breakdown so autopilot never has to stop mid-pipeline for it.
- **Stage 1 gate** now requires `rules_audit.py` clean on the shotlist before stage 2 unlocks. Catches camera same-combo overuse, missing required metadata (style, location_strategy, transformation_metadata), and (when transformation_scenes declared) missing setup / body-region / reveal beats. Re-planning the shotlist costs nothing; regenerating panels does not.
- **L12/L13/L14 + L10 refinement** added to generation-stage hard rules. `next_panel.py` emits `WARNING_DIALOGUE_CAMERA_CONFLICT` and `WARNING_MULTI_SPEAKER_CROWDING` — same HALT semantics as `MISSING_*`.
- **Removed legacy stages**: `souls` (no longer used; identity via face card + body ref chaining), `style` (now a preset library not a pipeline stage), `stylize` (current CGI path produces the right look directly).
- **Added stage**: `posting` (currently a manual workflow; stub for future automation).
- **Updated references stage**: typed buckets (`characters/` / `locations/` / `props/`); `_source.jpg` for hero CGI locations.

If you're picking up an older project that has `style.md` and trained Souls, those artifacts are inert — they won't break anything but they're not used by the new generation path. The new workflow expects style data inside `shotlist.json`'s style block and identity via the comic-production skill's face card + body ref chain.

If you're picking up a project without `production-config.json`, all three modes (status, auto, named stage) work exactly as before — no config required. Autopilot requires the config (or auto-invokes briefing to write one).
