# Experiment 04 — Validation report

**Date:** 2026-05-22
**Validator:** `skills/continuity-check/scripts/schema_audit.py`
**Schemas:** `schemas/{production-config,shotlist,references_required,checks,defects,continuity-report}.schema.json`
**Raw JSON snapshot:** [validation-snapshot.json](validation-snapshot.json)

## Top-line numbers

| Metric | Value |
|---|---|
| Schemas written | 6 (production-config, shotlist, references_required, checks, defects, continuity-report) |
| Projects validated | 13 (4 in-repo + 9 external `~/Documents/*`) |
| Artifacts present on disk | 27 |
| Artifacts pass | **18** |
| Artifacts fail | **9** |
| Artifacts missing (expected absence — gitignored or pre-stage) | 51 |
| Projects with zero drift | 6 (chun-li-test, solo-fmg-001, mira-five-sips-groa34, chun-li-ascension, supergirl-muscular.archived-2026-05-12, + rogue-transformation has no artifacts) |
| Projects with at least one fail | **7** |

A `missing` status means the artifact for that stage is not on disk. That's not a failure — most projects don't yet have rendered panels (which gitignored `pages/panels/*/checks.json`), and projects without `transformation_metadata` legitimately skip `references_required.json`.

## Schema-level discoveries (fixed during this experiment)

The very first run of the validator surfaced two **schema bugs** (my schema being wrong, not the data being wrong). Both were fixed before reporting:

1. **`checks.json` status enum was too narrow.** I wrote `["pass", "fail", "skip", "n/a"]`. The canonical writer in `next_panel.py` actually emits `pass`, `fail`, `pending` (default post_render before vision-audit runs), `blocked` (post_render when pre_render failed), and `skipped` (rule not applicable). Schema updated to the writer's real vocabulary. *This is exactly the dialect-drift problem the experiment is targeting — and it lived in the schema-author's own head.*

2. **`shotlist.json:arc_character` was required-string.** The writer can emit `null` when the project has no single arc character. Loosened to `["string", "null"]`.

After fixes, 9 remaining failures across 13 projects are all genuine artifact drift.

## Top drift categories

Ranked by number of projects affected.

### 1. `shotlist.json` — fractional `muscle_size_tier` (2 projects)

`comic-april-mutagen-v2`, `moving-experience-v2` both emit tier values like `1.2`, `1.5`, `2.5`, `3.5`, `4.5`, `5.5`. The canonical contract per `validate_shotlist.py` line 84 is `tier: int when present`. Half-tiers were never part of the contract.

Two possibilities to resolve later:
- These projects intend to use fractional tiers and the canonical contract should be widened.
- These projects emitted bad data and should be normalized to whole tiers.

This is exactly the kind of latent ambiguity the schema is meant to surface.

### 2. `shotlist.json` — missing `panels[]` and `page_number=0` (2 projects)

`chunli-issue-1`, `chunli-growth-series-v2`. `pages[0]` is empty (no `panels` property) and `page_number=0`. The writer contract requires `page_number >= 1` and a non-empty `panels[]`. Likely artifacts of an old shotlist writer that wrote a sentinel "page 0" header.

### 3. `production-config.json` — missing canonical top-level fields (2 projects)

`chunli-ascension-15p-2026-05-16`, `checks-balances-demo-2026-05-16` both lack `version` and `script_source`. The current canonical writer (v3) requires both. These configs predate the current contract.

### 4. `shotlist.json` — `cast[].name` missing (2 projects)

`chunli-ascension-15p-2026-05-16`, `checks-balances-demo-2026-05-16`. The cast entries carry `id` but not `name`. `name` is read by `next_panel.py` for prompt assembly (e.g., `"Chun Li"` vs the slug `"chunli"`).

### 5. `production-config.json` — unknown enum values (1 project)

`ultra-gal-origin` has `project.brand: "3DMuscleComics"` (not in the canonical set `GrowGetterComics | BloomBeautyComics | MaxxMuscleComics`) and `script_source.type: "path"` (not in `preset | text`). Both look like genuine extensions that never made it into the documented vocabulary — the brand list and the script_source.type enum either need to grow to include them, or the project needs to migrate to a canonical value.

### 6. `shotlist.json` — `dialogue[].type: "sfx"` (1 project)

`chunli-ascension-15p-2026-05-16` puts SFX rows into the `dialogue[]` array with `type: "sfx"`. The canonical contract has a separate `sfx[]` array on each panel. The `_l19_lettering_block` would mis-letter these as speech bubbles. This is genuine drift that would cause a downstream rendering bug — exactly the kind of silent failure the experiment is meant to surface.

### 7. `shotlist.json` — `version: "v2"` (string) instead of int (1 project)

`moving-experience-v2`. `version` is stringified `"v2"` rather than the canonical integer. The reader code in `validate_shotlist.py` doesn't gate on version, so this slipped through.

### 8. `shotlist.json` — `panels[].camera` missing entirely (1 project, ~4+ panels)

`chunli-issue-1`. Pages 1–4 have panels without a `camera` field. `validate_shotlist.py` line 70 already enforces this as an error — these shotlists would have been rejected by the current write-time gate, but predate it.

### 9. `references_required.json` — `version` vs `schema_version` dialect (1 project)

`projects/ultra-gal-origin/references_required.json` uses `version: 1`. `chunli-ascension-15p-2026-05-16/references_required.json` and `checks-balances-demo-2026-05-16/references_required.json` use `schema_version: 1`. Two writers wrote the same artifact with two different version-key names. The validator accepts both (schema declares both as optional integers) but the audit notes the dialect choice so the drift is visible.

## Per-project results

### In-repo projects (`projects/`)

| Project | production-config | shotlist | references_required | checks | defects | continuity-report |
|---|---|---|---|---|---|---|
| chun-li-test | PASS | PASS | (missing) | (missing) | (missing) | PASS |
| rogue-transformation | (missing) | (missing) | (missing) | (missing) | (missing) | (missing) |
| solo-fmg-001 | PASS | PASS | (missing) | (missing) | (missing) | (missing) |
| **ultra-gal-origin** | **FAIL** | **FAIL** | PASS (legacy `version` dialect) | (missing) | (missing) | (missing) |

### External projects (`~/Documents/*`)

| Project | production-config | shotlist | references_required | checks | defects | continuity-report |
|---|---|---|---|---|---|---|
| **chunli-issue-1** | (missing) | **FAIL** | (missing) | (missing) | (missing) | (missing) |
| **chunli-ascension-15p-2026-05-16** | **FAIL** | **FAIL** | PASS (canonical) | PASS (6/6) | PASS | (missing) |
| **checks-balances-demo-2026-05-16** | **FAIL** | **FAIL** | PASS (canonical) | PASS (6/6) | PASS | (missing) |
| **comic-april-mutagen-v2** | (missing) | **FAIL** | (missing) | PASS (14/14) | PASS | (missing) |
| mira-five-sips-groa34 | (missing) | PASS | (missing) | (missing) | (missing) | (missing) |
| chun-li-ascension | (missing) | PASS | (missing) | (missing) | (missing) | (missing) |
| **chunli-growth-series-v2** | (missing) | **FAIL** | (missing) | (missing) | (missing) | (missing) |
| supergirl-muscular.archived-2026-05-12 | (missing) | PASS | (missing) | (missing) | (missing) | (missing) |
| **moving-experience-v2** | (missing) | **FAIL** | (missing) | (missing) | (missing) | (missing) |

## What the experiment proved

1. **The drift is real and live in current data.** 7 of 13 projects fail at least one schema. Several would silently produce wrong renders if the autopilot processed them today.
2. **The schemas double as documentation that the writers and the validator agree on.** The first run revealed *I* had drifted (status enum, arc_character) — a sample size of one schema-author, but enough to confirm that without an enforced contract, even the person writing the contract gets it wrong.
3. **`checks.json` is the closest to canonical.** It already uses `schema_version`, every panel writer obeys it, and after the enum fix every on-disk file passed across three projects (26 panels). This is the model.
4. **`shotlist.json` is the most drifted.** 8 of the 9 failures live there. It is also the most-read artifact (4 of 6 stages consume it), so this is exactly the artifact that most benefits from a hard gate.
5. **No drift in `defects.jsonl` rows.** All 26 rows across 3 projects validated cleanly. Format has been stable since the `append_defects()` writer landed.

## Drift-fix backlog (do NOT fix in this branch — per experiment constraints)

Each row is a candidate per-project spawn:

- `ultra-gal-origin` — `production-config.json`: brand and script_source.type — likely needs a canonical vocabulary update + a config patch.
- `chunli-issue-1` — `shotlist.json`: bring up to current writer format or archive.
- `chunli-ascension-15p-2026-05-16` — both config and shotlist need migration; the `dialogue.type: "sfx"` rows should be moved to the `sfx[]` array.
- `checks-balances-demo-2026-05-16` — same as above.
- `comic-april-mutagen-v2` — decide on whole-vs-fractional tiers as policy, then either widen the canonical contract or normalize the values.
- `chunli-growth-series-v2` — empty page-0 sentinel needs removal.
- `moving-experience-v2` — stringify→int `version`, and the half-tier decision applies here too.

## Next step

The follow-on (separate spawn, separate branch) is wiring `schema_audit.py` as a HARD gate in the autopilot. Proposal at [wiring-proposal.md](wiring-proposal.md).
