# Checks-and-Balances Rule Architecture — Design Document

**Status:** ratified 2026-05-16 — implementation pending · **Author:** session 2026-05-16 · **Companion:** [`docs/posts/2026-05-16-checks-and-balances.md`](posts/2026-05-16-checks-and-balances.md)

## 1. Problem statement

Today's pipeline treats the L1–L28 lesson set as a monolithic enforcement layer. Prompt contributions are baked into one ~290-line function (`compose_prompt`); pre-render checks live in a separate script (`rules_audit.py`) that runs once per shotlist and never sees a rendered pixel; post-render checks are a manual subagent invocation. The agent driving generation cannot ask "did L20 fire on this panel?" The user cannot see, panel-by-panel, which rules passed, which failed, which were skipped, and why. Retries are coarse: regenerate the whole panel and hope. We need each rule to be a discrete unit with its own contribution, its own verification, its own retry strategy, and an auditable per-panel ledger that a future GUI can render as a green/red status grid and that a defects log can mine for patterns.

## 2. Current architecture (citations)

- **`compose_prompt(panel, shotlist, anchor, stage_change, env_ref, env_anchor_from, lineup_attached, env_dropped)`** at [`skills/comic-production/scripts/next_panel.py:741`](../skills/comic-production/scripts/next_panel.py) — appends contributions to `parts: list[str]` in a hard-coded order; returns `" ".join(parts)`. No per-rule attribution is preserved.
- **`build_plan(root)`** at [`next_panel.py:1039`](../skills/comic-production/scripts/next_panel.py) — emits `WARNING_*` / `MISSING_*` entries into `refs_to_attach` as a side-channel for HALT decisions. The 3-ref ceiling drop (L23) mutates `refs_to_attach` imperatively.
- **`rules_audit.py`** (`check_required_metadata`, `check_references`, `check_reference_completeness`, `check_pages`, `check_camera_variety`, `check_camera_distance_bias`, `check_transformation_beats`) — returns `list[Finding]` with `(page, panel_id, category, severity, message, suggestion)` but no rule ID. Categories like `"camera_distance_bias"` correspond to one L-rule; `"shotlist"`, `"reference"`, `"required_metadata"` straddle multiple.
- **Stage gates in [`commands/build-comic.md`](../commands/build-comic.md)** key off HARD finding counts and substring matches in `refs_to_attach`. There is no rule-level pass/fail state and no record of post-render verification.

## 3. Proposed architecture

### A. Rule-as-module refactor

Each active L-rule becomes a module at `skills/comic-production/rules/<rule_id>_<slug>.py`. The module exposes:

```python
class Rule:
    id: str                    # "L10", "L11", "L20"
    title: str                 # one-line human-readable
    slot: str | list[str]      # ordering hint — see slot table
    severity: Literal["hard", "soft"]
    applicable_transformations: set[str]  # {"fmg"} | {"fmg","be","mmg",...} | {"*"}

    def should_apply(panel, ctx) -> bool: ...
    def compose_contribution(panel, ctx, slot) -> str | None: ...
    def verify_pre_render(panel, plan, ctx) -> Verification: ...
    def verify_post_render(panel, image_path, ctx) -> Verification: ...
    def retry_strategy(panel, ctx, failure) -> RetryAction: ...
```

`ctx` carries `shotlist`, `cast_lookup`, `accepted_history`, `production_config`, `refs_attached`, and `transformation_type` (read from `production-config.json` — defaults to `"fmg"` on legacy projects without a config). `Verification` = `{status: pass|fail|skipped|n/a|pending|blocked|refused, reason: str|None, evidence: dict|None}`.

**Genre/niche extensibility (per open question 1).** Every rule declares `applicable_transformations`. The registry skips rules whose set doesn't include `ctx.transformation_type`. FMG is the first-class implementation target; BE / glute / MMG / mixed are accommodated by the data model but not the initial rule contents.

- A rule that always applies (L10, L18, L21) sets `applicable_transformations = {"*"}`.
- A rule that's FMG-specific in its current vocabulary (L11 cartoony FMG anchor, L15 female beauty anchor, female-anatomy anchor) ships v1 with `applicable_transformations = {"fmg"}`, plus a stub in the module's docstring describing what the BE/glute/MMG variant would look like ("rule lives in this slot, vocabulary needs a male-anatomy variant").
- The registry's `compose_for_transformation_type(panel, ctx, type)` runs only matching rules. Adding MMG later = duplicate the FMG vocabulary module to `l11_mmg_silhouette.py`, change the rule's `applicable_transformations` to `{"mmg"}`, register, done. No surgery on existing rules.

This is the explicit ratification of open question 1: **build for FMG, but every rule module carries a `applicable_transformations` field from day one** so extending to BE / glute / MMG / mixed is additive, not a refactor.

**Slot table** (load-bearing — composition order is currently implicit in `compose_prompt`; the refactor makes it a registry concern):

| Slot | Owner | Rules |
|---|---|---|
| `0_opening_anchor` | composer | (DAZ Studio Iray opener) |
| `1_camera_fragment` | composer | (camera fragment from camera label) |
| `2_camera_strengthening` | L20 | body-region camera directive |
| `3_subject_identity` | L17, L15 | canonical anchor, glamour anchor |
| `4_subject_state` | L22, L24, female-anatomy | hair state, accessory canonical+negation, anatomy anchor |
| `5_style_anchor` | L11 | cartoony FMG style anchor (tier ≥ 2) |
| `6_action_delta` | composer | sanitized action line |
| `7_lighting` | composer | momentary lighting |
| `8_tier_silhouette` | L11 | tier silhouette with lineup language |
| `9_environment` | L10 env, L23 | env chaining language or dense verbal anchor |
| `10_state_anchor` | L1.5 | prior-panel state anchor line |
| `11_render_directive` | L10 | the load-bearing RENDER DIRECTIVE sentence |
| `12_ref_safety` | L21 | ref-exclusion clause |
| `13_anatomy_guardrail` | L18 | always-emit anatomy line |
| `14_mandatory_rules` | composer | closing mandatory rules block |
| `15_closing_anchor` | composer | "Photographic CGI render, NOT illustrated." |

A `compose_prompt()` facade walks the registry, asking each rule for its contribution at its slot(s), and concatenates the results. The output is a `ComposedPrompt` object: `{prompt: str, per_rule_contributions: dict[rule_id, str | None], slot_order: list[str]}` — the string is what gets sent, the dict is what the ledger writes.

**Walking four representative rules:**

- **L10 (refs are truth)** — `applicable_transformations = {"*"}`, `slot = "11_render_directive"`. `should_apply` always true. `compose_contribution` returns the long RENDER DIRECTIVE sentence at [`next_panel.py:996-1006`](../skills/comic-production/scripts/next_panel.py). `verify_pre_render` checks the action text doesn't redescribe wardrobe constants (greps `panel.action` against per-character `cast[].wardrobe` and flags overlap); fail = `"action describes 'blue cheongsam' which is already in chunli.wardrobe"`. `verify_post_render` = vision check: does rendered identity match attached refs? `retry_strategy` returns `auto_resubmit` with a strengthened directive when the action sanitization line was missing or the directive was truncated.

- **L11 (cartoony FMG)** — `applicable_transformations = {"fmg"}` initially; v2 ships `l11_mmg_silhouette.py` for `{"mmg"}` etc. `slot = ["5_style_anchor", "8_tier_silhouette"]` (a rule can contribute to multiple slots; the registry calls `compose_contribution(slot)` per slot). `should_apply` = `panel.muscle_size_tier >= 2`. `compose_contribution(5_style_anchor)` returns the "cartoony hyper-FMG ... NOT realistic fitness modelling" anchor at [`next_panel.py:849-854`](../skills/comic-production/scripts/next_panel.py). `compose_contribution(8_tier_silhouette)` returns the lineup-attached block or the verbal-only fallback, depending on `ctx.lineup_attached`. `verify_pre_render` = `should_attach_lineup(panel, stage_change)` and `find_lineup()` returns a real path. `verify_post_render` = vision check against `silhouette_by_tier` map. `retry_strategy` = `auto_resubmit` with one of three escalations: (1) re-attach lineup if dropped, (2) strengthen vocabulary, (3) flag for human if tier ≥ 7 (model ceiling territory).

- **L20 (camera distance bias)** — `applicable_transformations = {"*"}` (the rule applies to any transformation comic). `slot = "2_camera_strengthening"`. `should_apply` = `panel.transformation_beat in BODY_REGION_BEATS`. `compose_contribution` returns `_body_region_camera_directive()` output at [`next_panel.py:612`](../skills/comic-production/scripts/next_panel.py). `verify_pre_render` runs the per-beat ceiling check today inside `detect_camera_too_far_for_beat` AND the chapter-aggregate mean/middle-fraction check today inside `check_camera_distance_bias`. `verify_post_render` = vision check: does rendered framing show the region filling 70%+? `retry_strategy` = strengthen the "DOMINATES / cropped OUT" language if it was the auto-injection that failed, else flag the shotlist's camera label for tightening (human).

- **L25 (sticky reveals)** — `applicable_transformations = {"*"}`. `slot = "6_action_delta"` extension. `should_apply` = any prior accepted panel revealed a body region that's in this panel's camera frame. `compose_contribution` returns `"<region> still exposed from p<id>'s reveal — costume must NOT re-cover"`. `verify_pre_render` checks the shotlist's `costume_state` preserves the exposure. `verify_post_render` = vision diff against the prior reveal panel. `retry_strategy` = auto_resubmit with strengthened "still exposed" language.

**Migration approach:** keep `compose_prompt()` as a thin facade that walks the rule registry. The existing helpers (`_body_region_camera_directive`, etc.) move bodily into their rule modules and get wrapped in the `Rule` interface. The string output of the facade should be byte-for-byte identical to today's output once all FMG rules are migrated, validated against a synthetic shotlist + golden-output test.

### B. Per-panel checks ledger

Every panel gets a `pages/panels/panel-<id>/checks.json` file (alongside the existing `v*.png` variants and `_accepted.txt`). Single file per panel — one-file-per-rule-per-panel would be a filesystem explosion (28 rules × 150 panels = 4200 files).

**Per open question 2: the ledger tracks the ACCEPTED variant only.** The runner generates 4 variants per panel; the variant picker selects one; that variant's index gets recorded as `accepted_variant_label` and post-render verification runs against only that image. Rejected variants are not vision-audited (cost saving, also keeps the ledger focused on what shipped). The accepted-variant path is the source of truth.

**Schema:**

```json
{
  "schema_version": 1,
  "panel_id": "p07-01",
  "page_number": 7,
  "transformation_type": "fmg",
  "shotlist_snapshot_sha": "abc123...",
  "composed_at": "2026-05-16T14:32:00Z",
  "composed_prompt": "DAZ Studio Iray render ... NOT illustrated.",
  "accepted_variant_label": "v3",
  "rules": {
    "L10": {
      "applied": true,
      "slot": "11_render_directive",
      "compose_contribution": "RENDER DIRECTIVE: render the attached references...",
      "pre_render": {"status": "pass", "reason": "action sanitization line present", "evidence": null},
      "post_render": {"status": "pending", "reason": null, "evidence": null},
      "verified_at": null
    },
    "L20": {
      "applied": true,
      "slot": "2_camera_strengthening",
      "compose_contribution": "L20 framing directive: EXTREME CLOSE-UP on the chest filling 70%+...",
      "pre_render": {"status": "pass", "reason": "beat=chest, camera=ecu-region (score 1, ceiling 3)"},
      "post_render": {"status": "fail", "reason": "rendered framing is medium-distance; chest does not fill 70% of frame", "evidence": {"vision_audit_at": "2026-05-16T14:45:00Z", "subagent_id": "..."}}
    },
    "L15": {
      "applied": false,
      "reason": "skipped — no female cast member in panel",
      "slot": null
    },
    "L11": {
      "applied": false,
      "reason": "n/a — rule applicable_transformations={'fmg'} but project transformation_type='mmg'",
      "slot": null
    },
    "L13": {
      "applied": true,
      "slot": null,
      "compose_contribution": null,
      "pre_render": {"status": "fail", "reason": "4 dialogue lines from 2 speakers — should be split into 4 panels"},
      "post_render": {"status": "blocked", "reason": "pre_render failed"}
    }
  }
}
```

Status values: `pass | fail | pending | skipped | blocked | n/a | refused`. `n/a` = rule doesn't apply to this `transformation_type`. `skipped` = `should_apply` returned false. `blocked` = a prior gate failed so this verification was not run. `refused` = post-submit platform refusal (L2 safety filter response).

**Tracking every rule, including non-applied ones, is important** — the GUI grid needs a complete row, and "rule was skipped because X" is information the user wants. Marginal cost is ~28 dict entries per panel — trivial.

**Writing the ledger:** a separate `write_checks_ledger(panel_id, composed: ComposedPrompt, verifications: dict)` function, called by the runner after `compose_prompt`. Keeps `compose_prompt` pure-functional and testable; lets resume scenarios and verify-only mode re-write the ledger without regenerating the panel.

**Project-level defects log (per open question 3).** A `<project_root>/defects.jsonl` file logs every failed verification across all panels in append-only form. One JSON object per line: `{ts, panel_id, rule_id, severity, reason, image_path, retry_history}`. The pipeline writes to it as a side-effect of `write_checks_ledger`. A future defect-discovery tool (CLI or web view) reads `defects.jsonl` across the project and answers questions like "which rules failed most across this chapter?" / "which rules failed across multiple chapters?" / "did a recent rule change correlate with more failures?" That last question is the discovery payoff — pattern mining across runs needs a structured log, not free-form prose. The log is open-ended; v1 just collects rows. v2 (later) builds the discovery process on top.

### C. Verification layer

Three classes:

1. **Deterministic pre-render** — `should_apply()` and `verify_pre_render()` run at shotlist time, no image needed. Examples: L13 multi-speaker (count `dialogue[]`), L20 chapter-aggregate mean (compute from shotlist cameras), L28 file existence, L16 `views[]` presence in manifest, L24 enumerated-negation present in prompt. The bulk of today's `rules_audit.py` checks live here, just re-keyed per rule.

2. **Deterministic post-render** — runs after generation, no vision needed, just file/state inspection. Examples: L1 (was prior-panel job_id passed as a ref? — check `state.json` request log), L9 (job_id captured? — check `state.json`), L28 post-gen provenance (was lineup attached during ref generation? — check `_provenance.md`). Cheap.

3. **Vision-based post-render** — needs the rendered image read. Examples: L11 (silhouette matches lineup), L15 (face quality), L17 (matches canonical), L18 (anatomy coherent), L20 (rendered framing matches declared camera), L21 (no inset ref images), L22 (hair matches declared state), L25 (previously revealed region still exposed). 6–10 rules need this.

**Vision verification protocol:** per panel per vision-bearing rule, spawn a fresh subagent. The subagent receives only the canonical refs, the rendered image, and the rubric for that specific rule. Single-purpose narrow rubric outperforms broad audits (see memory `feedback_audit_via_subagent` + the May 14 inline-audit failure). Return format: `{status: pass|fail, reason: str, evidence: dict}`. The "fresh subagent" matters — inline audits drift toward "looks fine."

**Cost — user has stated cost is not the constraint.** Vision verification fires for every applicable vision-bearing rule on the accepted variant. No per-project opt-out is built; the verification pass runs as part of stage 3 panel acceptance.

### D. Retry semantics

`retry_strategy(panel, ctx, failure) -> RetryAction` per rule. RetryAction kinds:

- **`auto_resubmit_with_stronger_contribution`** — the rule's `compose_contribution` gets called with `failure` as context, producing strengthened language (e.g., L11 escalates "cartoony hyper-FMG" → "exaggerated comic-book proportions, 3x normal shoulder width, NOT athletic, NOT realistic, NOT fitness-model"). Composer re-builds, runner re-submits. L18, L20, L21, L22, L23, L24 — most rules.
- **`auto_resubmit_with_corrected_refs`** — fix the ref set, not the prompt (L1 missing prior-panel ref, L10 missing face card, L11 missing lineup).
- **`auto_resubmit_with_different_face_card`** — for L17 drift on a canonical character, swap to an alternate canon-sourced ref before resubmit.
- **`shotlist_edit_required`** — human in the loop. L12 (split the dialogue panel), L13 (split multi-speaker), L26 (name the garment family), L27 (lock skin sheen vocabulary). The system surfaces the suggested edit; the user applies it.
- **`ref_generation_required`** — kick back to stage 2. L16 missing view ref, L28 missing manifest file. Cannot retry a panel until the ref exists.
- **`accept_and_log`** — explicit user override. Some rules legitimately have false-positive failure modes (L18 anatomy on intentionally surreal poses, L20 wide framing on a beat that doubles as an establishing shot).

The future GUI's per-rule retry button calls `retry_strategy()`, applies the action, updates the ledger, and writes the attempt into `defects.jsonl` for trend tracking. Even before the GUI ships, a CLI tool (`retry_panel.py <panel_id> --rule L20`) exposes the same surface.

### E. Verify-only mode (per open question 3)

A standalone CLI: `verify_panel.py <project_root> <panel_id>` re-runs all `verify_pre_render` and `verify_post_render` checks against the accepted variant on disk without regenerating. Updates `checks.json` and appends any new failures to `defects.jsonl`. Used for:

- **Retroactive audits** when a rule's verification logic changes — re-run on every accepted panel in past chapters to see which rules retroactively fail.
- **Stale-ledger refresh** — if the shotlist or refs change after panels are accepted, re-verify without paying for regeneration.
- **Discovery harness** — point at every accepted panel in every project, dump all defects into the project's `defects.jsonl`, mine the aggregate for systematic failure patterns.

A `--all-panels` variant runs across every accepted panel in the project. A `--rule=L20` variant restricts to one rule. A `--write-defects-only` variant skips ledger writes and just appends to the defects log (cheap, useful for "scan everything" runs).

### F. Ledger as stage gate (per open question 4)

Stage 1 closure today: `rules_audit.py` returns no HARD findings. Under the new model: stage 1 closes when every panel's pre-render verifications are `pass` or `n/a` or `skipped` for every applicable rule with `severity=hard`. The flat findings list is replaced by the per-rule, per-panel ledger as the gate. The CLI output format of `rules_audit.py` is preserved for backwards compatibility with `build-comic.md`'s existing string-match HALT logic, but the underlying data structure becomes the ledger.

Stage 2 closure (L28 reference completeness) operates the same way — gate on per-panel ledger rather than on a separate findings list.

### G. GUI integration sketch (deferred per user direction)

The per-panel ledger schema is exactly what a GUI would need. Grid view: rows = panels (story order), columns = rules (L1...L28). Cell color from `rules.<id>.post_render.status` falling back to `pre_render.status` falling back to `applied: false → skipped/n-a`. Click a cell → side panel shows `compose_contribution`, both verification objects, and a "retry" button that invokes the rule's `retry_strategy`. Aggregate view: per-rule pass-rate across all panels in the chapter — surfaces which rules systematically fail and need vocabulary work.

This is sketched only. The GUI itself is deferred per user direction; the per-panel ledger schema is the design contract. As long as the ledger conforms, any GUI implementation can read it.

## 4. Migration plan

Each phase ships independently. Per open question 5, the legacy `compose_prompt` flat-output path stays alongside the registry walker through phase 3 and gets removed at the end of phase 3 once golden-output tests are clean against the historical corpus.

Per open question 6, comic tests run when warranted — the assistant proposes a test point and the user confirms before paying API spend.

1. **Ledger emit-only.** `compose_prompt()` unchanged. Add `write_checks_ledger()` that infers per-rule application from the current helper invocations (each helper sets a sentinel on a context dict). Add `defects.jsonl` append on any inferred fail. Smoke-test by running on an existing comic and inspecting the JSON. Zero behavior change to the prompt itself. **Proposed test point at end of phase 1.**
2. **Extract one rule.** L21 is the smallest — single clause inject when any ref attached. Build the `Rule` interface, the registry, and migrate L21. `compose_prompt` becomes a facade for just L21 + the existing helpers for everything else. Golden-output test guarantees byte-identical prompt.
3. **Migrate remaining rules iteratively.** L18 next (always-emit, also small). Then L20, L15, L17, L22, L23, L24, L11, L10. Each migration carries its `applicable_transformations` field. End state: `compose_prompt` is purely a registry walker; legacy path removed. **Proposed test point at end of phase 3.**
4. **Pre-render verification per rule.** Migrate the relevant `rules_audit.py` checks into rule modules. `rules_audit.py` becomes a registry walker over `verify_pre_render` returns. Keep the CLI output format identical for compatibility with `build-comic.md` stage gates.
5. **Post-render vision verification.** Start with L20 (highest empirical-failure rate per the strengthening note). Add L11, L17, L18 sequentially. Subagent invocation pattern documented per rule. **Proposed test point at end of phase 5 — first end-to-end run with vision verification firing.**
6. **Retry per rule.** Implement `retry_strategy` per rule. Initially exposed via CLI tool (`retry_panel.py <panel_id> --rule L20`) so it can be smoke-tested before any GUI exists.
7. **Verify-only mode + defects discovery.** Ship `verify_panel.py` and a `discover_defects.py` tool that summarizes `defects.jsonl` across one or many projects.
8. **GUI (deferred).** Out of scope for this design.

## 5. Risks and tradeoffs

**Refactor risk on the generation step.** `compose_prompt` is the load-bearing function — every comic depends on it. A bug means every panel for every project, until detected. Mitigation: byte-identical golden-output tests per phase, run against a corpus of past comics (`comic-april-mutagen-v2`, `chun-li-ascension`, `chun-li-grok-validation`, `moving-experience-v2`). Don't ship phase 3 until phase 2's golden output is clean against every chapter in that corpus.

**Abstraction cost.** A new lesson today = add a helper to `next_panel.py` + add a check to `rules_audit.py`. Two files. Under the new architecture: new module, register it, write tests for `compose_contribution` + `verify_pre_render` + `verify_post_render` + `retry_strategy`. Five times the surface area. The payoff is testability, visibility, and the defects-discovery process. Worth saying out loud — this is the cost of buying in.

**Failure attribution.** When a panel fails post-render vision, the failure may not cleanly attribute to one rule. A tier-5 ECU rendered with male anatomy on a flat chest has failed L11 + L15-glamour + female-anatomy-anchor + L18 simultaneously. The vision subagent will pick whichever rule it was asked about and confirm fail; the ledger will show four reds; the retry will fire the strongest one's strategy. Acceptable — the system errs toward over-flagging — but the defects log will reflect this overcount, and the discovery process should treat correlated rule failures across the same panel as evidence of the same underlying defect, not four distinct defects.

**Ledger schema evolution.** New rules will keep landing. The schema needs to be additive: `rules.{new_id}` keys just appear; old ledgers without the new key are not invalid, the GUI shows them as `applied: false, reason: "rule did not exist when ledger was written"`. Version the schema (`schema_version: 1`) and document the additive rule.

**Rules that don't fit the per-panel model.** L2 (Higgsfield safety filter) is platform-runtime, not per-panel-prompt — model it as a post-submit deterministic check on the generation response payload (`response.status == "nsfw"`), tracked in the ledger under status `refused`. L3 (.png not .webp) is infrastructure — exemption, not a rule module. L5, L6, L7, L8 are historical / superseded — not migrated, not in the registry, listed explicitly in the README of the rules directory so the "I checked every rule" guarantee is honest about its scope.

**Genre vocabulary drift over time.** The `applicable_transformations` field is the right primitive, but vocabulary in shared rule modules will accumulate FMG bias if no one writes the MMG variants. When a non-FMG project finally runs, the assistant should fail loudly if a rule has no module for that `transformation_type` rather than silently skip — making the gap visible drives the next round of module additions instead of hiding it.

## 6. Ratified answers to open questions

1. **Per-project rule enable/disable.** Build FMG-first. Every rule module declares an `applicable_transformations` field. Registry filters on `production-config.json -> transformation_type`. Adding BE/glute/MMG later = new modules, not surgery on existing ones.
2. **Variant picker integration.** Ledger tracks the accepted variant only. Rejected variants don't get vision-audited.
3. **Verify-only mode.** Yes. `verify_panel.py` ships in phase 7. Project-level `defects.jsonl` collects every failure for later mining; defect-discovery tooling builds on top.
4. **Ledger as shotlist gate.** Yes. Stage 1 and Stage 2 closure both gate on the per-panel ledger rather than on flat findings lists. CLI output of `rules_audit.py` preserved for compatibility.
5. **Backwards compatibility window.** Legacy `compose_prompt` path stays through phase 3, then removed when golden-output tests are clean against the historical corpus.
6. **Migration cost / comic tests.** Phased plan accepted. Assistant proposes a test point at the end of phases 1, 3, and 5; user confirms before paying for the test run.

## 7. References

- [`CHANGELOG.md`](../CHANGELOG.md) — see 2026-05-16 entry for ratification.
- [`docs/posts/2026-05-16-checks-and-balances.md`](posts/2026-05-16-checks-and-balances.md) — companion blog article.
- [`skills/comic-production/references/lessons-learned.md`](../skills/comic-production/references/lessons-learned.md) — canonical rule definitions.
- [`skills/comic-production/references/the-rules-explained.md`](../skills/comic-production/references/the-rules-explained.md) — plain-English tour of every rule.
- [`skills/comic-production/scripts/next_panel.py`](../skills/comic-production/scripts/next_panel.py) — current `compose_prompt`.
- [`skills/continuity-check/scripts/rules_audit.py`](../skills/continuity-check/scripts/rules_audit.py) — current deterministic audit.
- [`commands/build-comic.md`](../commands/build-comic.md) — current stage gates.
