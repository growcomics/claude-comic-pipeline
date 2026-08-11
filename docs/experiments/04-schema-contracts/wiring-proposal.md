# Experiment 04 — Wiring proposal: schema_audit as a HARD gate

**Status:** PROPOSAL ONLY. Do not implement in this branch (per Experiment 04 constraints — the experiment ships schemas + validator + report only, wiring is a follow-on decision after the user reviews drift).

## Goal

Make every pipeline stage that produces a stage-boundary artifact fail loudly when the artifact doesn't conform to its schema, instead of letting drifted artifacts propagate downstream and produce silent rendering failures.

## Where to wire

The pipeline has two main orchestrators: `/build-comic` (the human-facing slash command in `commands/build-comic.md`) and per-skill scripts that produce artifacts (`script-breakdown`, `reference-gathering`, `comic-production`, `continuity-check`, `page-composer`).

The wiring needs to happen at three levels:

### Level 1 — Write-time gate (REQUIRED for the experiment to bite)

Every script that writes a stage-boundary artifact runs `schema_audit.py` against the freshly-written artifact and HARD-fails if it doesn't validate.

| Producer | Hook point | Behavior |
|---|---|---|
| `production-briefing` (writes `production-config.json`) | End of skill, just before "Config written" message | Run `schema_audit.py <project> --artifact production-config`. On fail, print violations and abort the skill — do NOT chain into the next stage. |
| `script-breakdown` (writes `shotlist.json`, optionally `references_required.json`) | After both files are written, before `validate_shotlist.py` runs its existing camera-vocab check | Run `schema_audit.py <project> --artifact shotlist[,references_required]`. On fail, print violations and exit non-zero. `validate_shotlist.py` becomes the *second* check (the camera-vocabulary enforcement layer on top of the structural schema). |
| `comic-production` `next_panel.py` (writes `pages/panels/panel-<id>/checks.json` via `checks_ledger.write_checks_ledger()`) | At the end of `write_checks_ledger()`, immediately after `out_path.write_text(...)` | Run schema validation in-process (don't shell out) using `Draft7Validator`. On fail, raise `SchemaContractError` and surface in the runner's log. |
| `comic-production` `next_panel.py` (appends `defects.jsonl` via `checks_ledger.append_defects()`) | Per row, before `f.write(json.dumps(row))` | Validate each row in-memory; on fail, raise rather than corrupting the JSONL. |
| `continuity-check` `rules_audit.py` (writes `continuity-report.md`) | After write, before the skill returns | Run `schema_audit.py <project> --artifact continuity-report`. On fail (e.g., extraction couldn't find the verdict line), surface the structural issue. |

**New CLI flag for schema_audit.py:** `--artifact <name>` to validate just one artifact. Cheap to add; the dispatch table is already keyed by artifact name in the validator.

### Level 2 — Stage-progression gate in `/build-comic auto` and `autopilot`

`commands/build-comic.md` already runs `rules_audit.py` between stages. Insert `schema_audit.py` calls at the same checkpoints:

| Checkpoint | Run | On fail |
|---|---|---|
| Before stage 1 → 2 (`script-breakdown` → `reference-gathering`) | `schema_audit.py <project>` (validates `production-config` + `shotlist` + `references_required`) | HARD halt with the violation list. In `auto` mode ask the user to fix or escape; in `autopilot` halt unconditionally — this is one of the new halt conditions. |
| Before stage 3 → 4 (`comic-production` → `continuity-check`) | `schema_audit.py <project>` (revalidates the above + every panel's `checks.json` + `defects.jsonl`) | Same. |
| Before stage 4 → 5 (`continuity-check` → `page-composer`) | `schema_audit.py <project>` (full sweep) | Same. |

Pseudocode for the gate (lives in the `build-comic` skill instructions):

```
run("python3 skills/continuity-check/scripts/schema_audit.py <project>")
if exit_code != 0:
    if mode == "autopilot":
        HALT — print "Schema-contract violation. See above. Schema gate is a hard halt."
        exit
    else:  # auto / interactive
        ASK user: "Schema violations found. Fix and re-run, OR escape to bypass (records the drift in defects.jsonl)?"
```

### Level 3 — Halt-condition entry in `production-config.json`

Add to the canonical config (and `production-config.schema.json` requires):

```json
"halt_conditions": {
  ...,
  "schema_contract_violation": true
}
```

This makes the gate opt-out at the project level — useful for one-off "I know this drift exists, let me through" workflows. Default `true`.

## Handling legacy projects with existing drift

Per [validation-report.md](validation-report.md), 7 of 13 projects fail at least one schema today. Wiring the gate without preparing them would lock the autopilot out of every project that hasn't been migrated.

### Option A — One-shot migration script

Write `scripts/migrate_schema.py` (separate spawn, separate branch). For each known drift category, the script applies a deterministic fix:

- `production-config` missing `version` → add `"version": 3`.
- `production-config` missing `script_source` → infer from existing project layout, or `{"type": "text", "value": "<MIGRATED — original prose not captured>"}`.
- `shotlist` `version: "v2"` → `version: 1`.
- `shotlist` empty page-0 → drop it.
- `shotlist` `cast[].name` missing → use `id` titlecased as a fallback.
- `shotlist` `panel.camera` missing → add `"camera": "<MIGRATION_TODO>"` and emit a warning so the user fixes manually.
- `shotlist` half-tier `muscle_size_tier` → policy decision (see Open question 1 below).
- `references_required` legacy `version` → rename to `schema_version`.
- `shotlist` `dialogue.type: "sfx"` → move row from `dialogue[]` to `sfx[]`.

The migrator is a separate spawn because (a) each fix is per-category, (b) `--dry-run` and review are required, and (c) some categories need a policy decision before a fix can be picked.

### Option B — Per-project escape hatch

Until each project is migrated, add a `.schema-bypass` file at the project root containing a list of accepted violations. The validator reads it and downgrades those specific violations to warnings. This is the bridge while the migrator catches up.

### Option C — Soft-launch the gate

Land the wiring with the gate emitting WARN rather than HARD-FAIL for the first week. Watch which violations surface most often in real autopilot runs. Promote to HARD-FAIL once each pattern has either been fixed in the writer or accepted in the schema. This is the lowest-risk path.

**Recommended path:** A + C in parallel. Write the migrator and run it against all known projects (one PR per project so each change is reviewable). Soft-launch the gate as WARN. After the migration sweep, flip to HARD-FAIL.

## Open questions for the user before wiring

1. **Are fractional muscle-size tiers (1.2, 2.5, etc.) legitimate?** Two projects use them. If yes, the canonical contract widens to `number` instead of `integer`; if no, the migrator normalizes to nearest int. Need a policy call.
2. **Do `3DMuscleComics` and `script_source.type: "path"` need to enter the canonical vocabulary?** `ultra-gal-origin` uses both. Either expand the enums or migrate the project.
3. **Should `sfx` ever be allowed as a `dialogue[].type`?** I read the existing writer code as "no, sfx lives in `sfx[]`" — but `chunli-ascension-15p-2026-05-16` puts it in `dialogue[]`. Confirm before the migrator rewrites those rows.

## Non-goals

- No NEW rule logic. Schemas codify the contract that already exists; they don't add new constraints.
- No replacing `validate_shotlist.py`. That script enforces the camera-vocabulary check, which is a domain rule on top of the structural schema. Keep both.
- No replacing `rules_audit.py`. That script is the per-panel continuity audit — different layer.

## Effort estimate

- Level 1 (write-time gates in each producer): ~1 day. Each producer needs ~10 lines of glue.
- Level 2 (build-comic checkpoints): ~2 hours. Edit `commands/build-comic.md` and the autopilot config keys.
- Level 3 (halt-condition wiring): ~30 min. Schema update + config-reader patch.
- Migrator (Option A): ~1 day per drift category, with `--dry-run` and per-project review. Roughly 3–5 days total.

## Sequencing

1. (this experiment) Schemas + validator + report. **DONE in `experiment/04-schema-contracts`.**
2. Review report with user. Resolve Open questions 1–3.
3. Spawn: migrator (Option A) — one PR per project.
4. Spawn: Level 1 wiring — one commit per producer.
5. Spawn: Level 2 wiring — single commit in `build-comic.md`.
6. Soft-launch (Option C): all wiring lands with WARN. Watch for ~5 real runs.
7. Promote to HARD-FAIL once warnings hit zero on green projects.
