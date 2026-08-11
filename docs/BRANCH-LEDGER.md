# Branch Ledger — stale-branch triage, 2026-08-11 reconciliation

Disposition record for the seven pre-reconciliation branches, produced during the
main ↔ `feat/comic-corpus` reconciliation (merge `77c1913`, main previously at
`feeca4d`). **Policy: no branch was deleted** — this ledger documents; the user
decides retirement. Branches outside this list (e.g. `feat/flow-runner`,
`docs/dashboard-v0-proposal`, `groa-19-tests`, stage-worktree branches) were out
of triage scope.

Stacking note: `experiment/05` **contains** `experiment/02` (commit `b752f4d`),
and `feat/yuna-rerun-refactor-validation` **contains** all of
`refactor/refs-are-truth-prompts-are-action` plus one validation commit.

| Branch | Status | Why | Unique content pointer |
|---|---|---|---|
| `experiment/01-generalization-smoke-test` | **MERGED** → `7445dca` | Docs + read-only smoke-test validator, text-clean (blog PNGs are conventional `docs/blog/assets/`), still-relevant; prior report marked merge-ready. 15/15 hard-pass results. | now on main: `docs/experiments/01-generalization-smoke-test/`, `docs/blog/2026-05-22-when-layers-dont-speak-the-same-language.md` |
| `experiment/02-vision-audit-pilot` | **KEEP (unmerged)** | Prior report: keep and iterate later — its labeled set + 5-iteration rubric feeds the vision-shadow work (`feat/audit-vision-gap-*` line). Not superseded, not yet productionized. | `git show experiment/02-vision-audit-pilot:` … labeled set + rubric iterations + script (30 files) |
| `experiment/03-multipass-buildup` | **KEEP (unmerged)** | Partial per prior report: the A/B **rating round never happened** (`ab-ratings.md` unfilled), so its recommendation is unvalidated. The multipass idea later landed independently (multi-pass layered-correction feedback, Jul 2026) — merging the stale protocol docs now would only confuse provenance. | `docs/experiments/03-multipass-buildup/{runbook,recipes,workflow}.md` on the branch (8 text files) |
| `experiment/04-schema-contracts` | **MERGED** → `cf07a32` | Six JSON Schemas for every stage boundary + inventory/wiring docs + read-only `schema_audit.py`; text-clean, no gate paths; prior report marked merge-ready. | now on main: `schemas/*.schema.json`, `skills/continuity-check/scripts/schema_audit.py`, `docs/experiments/04-schema-contracts/` |
| `experiment/05-defects-skill` | **KEEP (unmerged)** | Superseded as a mechanism: the canonical `DEFECT-REGISTRY.md` + per-project `defect-registry.json` became the QA contract; this branch's taxonomy/rubric was its seed. Carries **42 binaries** (overnight Yuna harvest renders) that violate current projects-text-only hygiene. Also contains exp/02 wholesale. | `git show experiment/05-defects-skill:` … labeled defect corpus + taxonomy + overnight-run scaffolds (95 files) |
| `feat/yuna-rerun-refactor-validation` | **KEEP (unmerged)** | = refactor branch + one validation commit `f67d741`, whose own record is a **pre-flight hard stop (shotlist schema mismatch)** — the refactor never validated green. Valuable as the honest record of why the refactor didn't land. | `git show f67d741` (validation stop), branch tip for the full attempt |
| `refactor/refs-are-truth-prompts-are-action` | **KEEP (unmerged)** | Structural restructure of the rules registry (attach/action/match/safety) from 2026-05-23; 11 weeks of rules evolution since (L34–L38, phase-1 registry) makes a wholesale merge regressive, and its validation failed (see yuna branch). `skills/reference-acquisition/` was **ported to main 2026-08-10** in updated form (fresh assessment done; see CHANGELOG 2026-08-10 — attach-rule integration replaced with main's real wiring, stale model defaults → CLAUDE.md pointer, `_provenance.md` convention, gate-boundary + reads-25+/coverage clauses added). Remaining unique value: the attach/action/match/safety registry restructure itself + the blog draft. | `git show refactor/refs-are-truth-prompts-are-action:skills/reference-acquisition/SKILL.md`; blog draft `0464882`; core refactor `84ab980` |
