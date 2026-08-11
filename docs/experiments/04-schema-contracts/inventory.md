# Experiment 04 — Pipeline-stage artifact inventory

**Date:** 2026-05-22
**Branch:** `experiment/04-schema-contracts`

## Why this exists

Magnamus's root-cause diagnosis of the four bugs fixed on 2026-05-22:

> "Every failure this whole thread traced back to layers of the pipeline disagreeing about vocabulary or convention — branch vs branch, caption shape, panel-storage layout, camera dialect vs map keys. Four bugs, one root cause: nothing enforces a single schema, so each part speaks its own dialect and the joins fail silently."

This experiment maps the producer/consumer contract at every stage boundary so we can write JSON Schemas that catch dialect drift *at the boundary* instead of letting it propagate.

## The 6 stages and their handoffs

| # | Producer | Artifact | Consumer | Writer | Reader |
|---|---|---|---|---|---|
| 0→1 | `production-briefing` | `production-config.json` | `script-breakdown` | `skills/production-briefing/SKILL.md` (hand-written by briefing skill) | `skills/script-breakdown/SKILL.md`, `skills/comic-production/scripts/next_panel.py` |
| 1→2,3 | `script-breakdown` | `shotlist.json` | `comic-production`, `reference-gathering`, `continuity-check`, `page-composer` | `skills/script-breakdown/SKILL.md` + `validate_shotlist.py` (post-write gate) | `skills/script-breakdown/scripts/validate_shotlist.py`, `next_panel.py`, `rules_audit.py` |
| 1→2 | `script-breakdown` | `references_required.json` | `reference-gathering` | `skills/script-breakdown/SKILL.md` | `skills/reference-gathering/SKILL.md` |
| 3→4 | `comic-production` | `pages/panels/panel-<id>/checks.json` (per-panel) | `continuity-check` | `skills/comic-production/scripts/checks_ledger.py` `write_checks_ledger()` | indirectly via `audit_panels.py` post-render write-back |
| 3→4 | `comic-production` / `continuity-check` | `defects.jsonl` (project-root, JSONL) | autopilot retry loop, page-composer (advisory) | `skills/comic-production/scripts/checks_ledger.py` `append_defects()` | `skills/comic-production/scripts/discover_defects.py` |
| 4→5 | `continuity-check` | `continuity-report.md` | `page-composer` (human-readable verdict) | `skills/continuity-check/scripts/rules_audit.py` | human + page-composer SKILL.md (prose) |

## Schema-relevant findings per artifact

### 1. `production-config.json` (Stage 0→1)

**Writer:** Hand-written by the briefing skill, format documented in `skills/production-briefing/SKILL.md` line 27 onward.

**Key fields the pipeline actually reads (canonical contract):**
- `version` (int, currently 3)
- `project.name`, `project.root`, `project.brand`
- `transformation_type` (string; `fmg | be | glute | mmg | mixed` per docs)
- `platform` (`flow | higgsfield`)
- `script_source.type` (`preset | text`), `script_source.value` (string)
- `mandatory_rules.active` (int array, the L-rules to enable)
- `references.policy` + `references.min_frames_per_character`
- `generation.max_panels`, `generation.pick_variant` (`claude | user`)
- `policies.content_policy_refusal`, `.missing_ref_guardrail`

**Drift seen in real samples:**
- `script_source.value` can be a long prose blob OR a slug
- Many projects add a `project_specific.{costume,tier_curve,splash_panels,...}` block that the canonical schema doesn't know about — currently treated as best-effort by `script-breakdown`

**Versioning field:** `"version": 3` (top-level int). No `schema_version`.

### 2. `shotlist.json` (Stage 1→{2,3,4,5})

**Writer:** Hand-written by `script-breakdown`. Post-write gate: `skills/script-breakdown/scripts/validate_shotlist.py`.

**Producer-side required (per validate_shotlist.py):**
- `pages[]` (array, must not be empty)
- `pages[].panels[]` (array, must not be empty)
- Per panel: `panel_id` (unique), `camera` (head token must be one of `KNOWN_VIEWS`), `tier` (int when present)
- Per dialogue line: must have `speaker` OR `character` when `type ∈ {balloon, thought, whisper, shout}`

**Consumer-side reads (next_panel.py):**
- `panel_id`, `tier`, `characters[]`, `location`, `camera`, `action`
- `hair_state`, `costume_state`, `psycho_power_state`, `expression`
- `dialogue[]` with both `speaker` and `character` (drift-tolerated by `_l19_lettering_block`)
- `captions[]` — items can be **bare strings** OR `{"text": "..."}` (drift-tolerated via `_as_obj()`)
- `sfx[]` — same shape drift

**Real-world drift across projects:**
- `chunli-issue-1/shotlist.json` — only `{project, title, pages}`, no `version`, no `cast`, no `locations`, no `transformation_metadata`. Old format.
- `checks-balances-demo-2026-05-16/shotlist.json` — has `acts[]` extension, also missing `version`, missing `panels_per_page`. Cast carries `{accessories, canonical, canonical_anchor, glamour_anchor, pronoun, sex}` (custom fields).
- `mira-five-sips-groa34/shotlist.json` — adds `format_notes`, `handoff_notes`, `mandatory_rules_block` at top level. Cast carries `{build_note, build_progression, face, must_appear_in_every_prompt_verbatim}` (project-specific).
- `chun-li-test/shotlist.json` — current canonical, has `transformation_metadata.{flavor, start_tier, end_tier, tier_curve_per_panel, splash_panels, bison_tier_curve_per_panel}`.

**Versioning field:** `"version": 1`. No `schema_version`.

### 3. `references_required.json` (Stage 1→2)

**Writer:** `script-breakdown` (when `transformation_metadata` present, per the skill).

**Real-world shape (`projects/ultra-gal-origin/`):**
- Top-level: `version` (int) + `generated_from_shotlist` (bool) + `characters` (map) + `locations` (map) + `props` (map, optional)
- Per character: `face_card` (path string), optional `body_tiers[]`, optional `views[]`
  - `body_tiers[i]` = `{tier: int, path: string, lineup_required: bool, tier6_reinforcement_required: bool (optional)}`
  - `views[i]` = `{name: string, tier: int, path: string, lineup_required: bool}`
- Per location: `establishing` (path string), optional `views[]`

**Drift between two real samples:**
- `projects/ultra-gal-origin/references_required.json` uses `"version": 1`
- `chunli-ascension-15p-2026-05-16/references_required.json` uses `"schema_version": 1` ← already a dialect mismatch in the wild

**Versioning field:** **drift** — `version` OR `schema_version` depending on which writer wrote it.

### 4. `pages/panels/panel-<id>/checks.json` (Stage 3→4)

**Writer:** `skills/comic-production/scripts/checks_ledger.py::write_checks_ledger()` line 49.

**Canonical contract (from the writer code):**
```json
{
  "schema_version": 1,
  "panel_id": "p01-01",
  "page_number": 1,
  "transformation_type": "fmg",
  "shotlist_snapshot_sha": "abc123...",
  "composed_at": "2026-05-22T14:30:00+00:00",
  "composed_prompt": "<full generation prompt>",
  "accepted_variant_label": "v3",
  "rules": {
    "L17": {"applied": true, "pre_render": {"status": "pass", "reason": "..."}, "post_render": null},
    "L22": {"applied": true, "pre_render": null, "post_render": {"status": "fail", "reason": "..."}}
  }
}
```

**Versioning field:** `"schema_version": 1` — **the only artifact that already uses `schema_version`**. This is the canonical convention to standardize on.

**On-disk presence:** `pages/` is gitignored, so most committed projects have ZERO checks.json files. The validator must handle absence gracefully (skip vs flag).

### 5. `defects.jsonl` (Stage 3→{4, autopilot})

**Writer:** `skills/comic-production/scripts/checks_ledger.py::append_defects()` line 102.

**Per-row shape (one JSON object per line):**
```json
{"ts": "2026-05-16T17:36:41+00:00", "panel_id": "p02-01", "page_number": 2, "rule_id": "L1.5", "severity": "hard", "verification": "pre_render", "reason": "...", "retry_history": []}
```

Required: `ts`, `panel_id`, `page_number`, `rule_id`, `severity` (`hard | soft`), `verification` (`pre_render | post_render`), `reason` (string), `retry_history` (array).

**Versioning field:** none. JSONL has no header row, so version lives implicitly in the producer.

**Gitignore status:** `defects.jsonl` is in `.gitignore`. Most committed projects lack it.

### 6. `continuity-report.md` (Stage 4→5)

**Writer:** `skills/continuity-check/scripts/rules_audit.py`.

**Structural contract (observed in `chun-li-test/continuity-report.md`):**
- H1: `# <project> — Continuity audit`
- Optional italic: `_Run: YYYY-MM-DD_`
- Required H2: `## Verdict` followed by a one-line verdict (`**PASS**`, `**SOFT-FAIL**`, or `**HARD-FAIL**`)
- Required H2: `## Per-panel notes`
- Per panel: H3 `### p<NN>-<MM> (...)` followed by bulleted checks (`- ✓ ...` / `- ⚠ ...` / `- ✗ ...`)

**Not JSON.** The schema-audit step extracts these sections from markdown and validates the *extracted* dict against a JSON Schema.

## Versioning convention going forward

Three different conventions live in the repo today:
- `"version": 1` (shotlist, references_required-flavor-A, production-config uses 3)
- `"schema_version": 1` (checks.json, references_required-flavor-B)
- *(none)* (defects.jsonl rows, continuity-report.md)

**Recommendation:** All five schemas standardize on `"schema_version": <int>` at the top level. The validator accepts the existing `version` field as a fallback (with a warning) so legacy projects don't break overnight. Long-term, a one-shot migration script normalizes.

## Schema-required field map (cheat sheet)

| Artifact | Required top-level | Required per-element |
|---|---|---|
| production-config | `version`, `project.{name,root,brand}`, `transformation_type`, `platform`, `script_source`, `mandatory_rules.active` | — |
| shotlist | `project`, `version` (or `schema_version`), `pages[]` | per-panel: `panel_id`, `camera`, `characters[]`, `location`, `action` |
| references_required | `version` or `schema_version`, `characters{}` | per-character: `face_card` |
| checks (per panel) | `schema_version`, `panel_id`, `transformation_type`, `composed_at`, `composed_prompt`, `rules{}` | per-rule: `applied` (bool) and either `pre_render` or `post_render` (or null) |
| defects (per JSONL row) | `ts`, `panel_id`, `page_number`, `rule_id`, `severity`, `verification`, `reason`, `retry_history[]` | — |
| continuity-report (extracted) | `verdict` (string), `panels[]` | per-panel: `panel_id`, `checks[]` |

This is the contract the schemas codify in Phase B.
