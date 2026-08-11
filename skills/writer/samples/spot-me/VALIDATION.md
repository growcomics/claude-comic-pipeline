# Spot Me — validation record (2026-08-10, re-run after rebase onto main@86841ac)

The Writer stage's zero-credit worked example, run end-to-end: `concept.json` (conforming to `skills/ideator/references/concept-schema.json`, `selected_concept_id` set) → Writer workflow → `script.md` → script-breakdown transcription (Step 0 pre-answered by the script header) → `shotlist.json` + `shotlist.md` + `references_required.json` → all gates. Originally validated against `main@feeca4d`; while the branch was in flight, main absorbed the ideator engine, the L38 story-spine gate, and L39 situation registers — everything below is the **re-run against that newer main**, with the sample upgraded to carry `panel_situation` and the L38-checked spine.

## Gate runs (all from repo root)

**Concept contract — `skills/ideator/scripts/tournament.py validate`** · exit 0

```
OK: skills/writer/samples/spot-me/concept.json validates (1 concepts, seed='closing-time gym rivalry', selected='spot-me-closing-time')
```

(The engine recomputes `weighted_total` itself — 73.8 here, matching Σ(score×weight)=48 / 65 at one decimal.)

**Writer gate — `skills/writer/scripts/validate_script.py`** · exit 0, 0 hard / 0 soft

```
== validate_script — Spot Me ==
pages: 6  panels: 26  growth: 5/6 (83.3% vs floor 60%)  first growth: p2  silent: 38.5%
tier dana: [2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 4, 4, 4, 5, 5, 5, 5, 5, 5]
camera: mean 2.23 over 26 annotated panels, middle 61.5%
scene first-surge: pages (1, 3), 7 growth panels, devices ['sfx-driven', 'zoom-escalation', 'reaction-intercut']
scene overload: pages (4, 6), 8 growth panels, devices ['multi-panel-progressive', 'clothing-destruction', 'size-comparison', 'reaction-intercut']
OK — no hard findings (0 soft)
```

**Gate A — `skills/script-breakdown/scripts/validate_shotlist.py`** · exit 0 — `OK — 26 panels valid`

**Gate B — `skills/continuity-check/scripts/rules_audit.py --project .`** · findings: 40 hard, **0 soft**

| Category | Count | Reading |
|---|---|---|
| `asset` (hard) | 26 | one per panel — *no accepted image on disk*. Inherent at script-breakdown time: panels are generated at Stage 5. |
| `reference_completeness` (hard) | 14 | one per manifest file — *missing required reference*. This IS Stage 4's work order (`references_required.json` walked by `reference-gathering`). |
| everything else | **0** | zero HARD and zero SOFT across `required_metadata`, `reference`, `shotlist`, `costume`, `size_tier`, `camera_variety`, `camera_distance_bias`, `transformation_beats`, `subject_staging`, **and the live L38 `story_spine` gate** (spine fields, promise→payoff ordering, final-page landing, capstone-interchangeability, climax `distinguishing_marks`). |

**Acceptance criterion** (documented here because the audit has no pre-generation mode): *zero HARD findings outside {`asset`, `reference_completeness`}* — those two categories enumerate downstream stages' pending work and are definitionally unfulfillable before generation. Every category the **script** controls is clean, with no soft findings either.

## Validator negative tests

`validate_script.py` was verified to *bite*, not just pass: 14 seeded-violation variants each exit 1 with the expected hard code — tier regression + peak-never-reached (`tier`), 3-lines-2-speakers + 26-word balloon + malformed dialogue line (`dialogue`), density under floor (`density`), missing reveal + growth-beat-outside-scene (`decomposition`), coverage violation (`coverage`), unknown beat (`beat`), body-region beat at wide camera (`camera`), stubbed spine (`spine`), multi-character panel without a register + unknown register value (`situation`).

## Re-run

```sh
cd <repo-root>
python3 skills/ideator/scripts/tournament.py validate --slate skills/writer/samples/spot-me/concept.json
python3 skills/writer/scripts/validate_script.py skills/writer/samples/spot-me/script.md
python3 skills/script-breakdown/scripts/validate_shotlist.py skills/writer/samples/spot-me
python3 skills/continuity-check/scripts/rules_audit.py --project skills/writer/samples/spot-me
```

(The `references/` subfolders here hold `.gitkeep` placeholders — the folders must exist for the audit's `reference` check; the files inside are Stage 4's job.)

## Notes for readers of this example

- The script's header pre-answered script-breakdown's Step 0 (style / location strategy / flavor / tiers) — that's the Writer→Storyboard contract working as designed.
- `story_spine` + `cast[].distinguishing_marks` are HARD-gated downstream by L38 (`check_story_spine`) — this shotlist passes that gate live. `panel_situation` (L39) is declared on every multi-character panel + the mirror/splash solos; multi-character showcase/celebratory count is 0 against the ~3 budget.
- The two capstones (`p06-01` whole_body medium vs `p06-02` reveal splash) differ on size, distance, and beat — no interchangeable-capstone run (L38 F5b).
- Kayla is non-arc but gets one `body-tier3` manifest entry: she's the living size gauge and needs a body ref at her fixed tier.
- Known gate-mismatch workarounds baked into this sample (both verified still present on main@86841ac and flagged upstream): `cowboy` avoided as a camera head (Gate A's KNOWN_VIEWS lacks it; expressed as `medium` + modifier), and `subject_staging` declared even though the audit's L34 check reads `panel.cast` (schema says `characters`) and so never fires.
