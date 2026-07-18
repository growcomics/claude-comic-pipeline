# Owner Feedback Loop — defect flags → frequency stats → new rules

*Added 2026-07-18. Design document (Studio PHP changes NOT yet built — deploy is a separate
step under `studio/DEPLOY-NOTES.md`'s fetch-live protocol). Companion to the canonical
defect taxonomy in `skills/comic-production/references/DEFECT-REGISTRY.md`.*

## Goal

The always-on producer (bridge.php worker protocol → `studio/docs/AI-RUNNER-SKETCH.md`)
only works if pages come out clean without a human art-directing every panel. Today every
page ships with defects a human can spot in seconds. This loop converts each of those
human observations into a permanent system improvement:

1. The owner looks at any generated panel in Studio and **flags a defect in seconds**
   (defect-class picker + optional free text on the panel card).
2. Every flag is **structured data** — panel, canonical defect ID, note, timestamp — not
   prose lost in a feedback textarea.
3. Flags accumulate into **per-defect frequency stats** that rank where the system
   actually bleeds (not where we guess it does).
4. Recurring flags on a defect with weak/no rule coverage **auto-draft a new
   lesson/rule** for owner approval — approved drafts land in this repo as L-lessons /
   rule modules / QA-gate lines.
5. **Success metric: defects-per-page trending down over time**, visible on a small chart.

The load-bearing decision: the AI scanner (`ck_ai_qa`) and the human flags feed the
**same registry IDs**, so auto-detection and human perception stay aligned — when the
human keeps flagging something the scanner passes, that *is* the scanner's bug report.

## 0. Shared taxonomy (the contract)

`DEFECT-REGISTRY.md` is the single source of truth for defect classes. Every defect
class has:

- a stable **registry ID** (`CAST-01`, `LET-02`, …) — used in docs, gap analysis, CHANGELOG
- a stable **slug** (`duplicate_character`, `garbled_text`, …) — used in every JSON payload

The live scanner's current 10-type enum maps onto registry slugs as follows (the scanner
keeps emitting its types; the Studio normalises to registry slugs at write time so old
analyses stay readable):

| ck_ai_qa `type` | registry ID | registry slug |
|---|---|---|
| `duplicate_character` | CAST-01 | `duplicate_character` |
| `extra_person` | CAST-02 | `extra_person` |
| `people_count` | CAST-03 | `people_count` |
| `wooden_face` | FACE-01 | `dead_face` |
| `wardrobe_drift` | WARD-01 | `wardrobe_drift` |
| `anachronism` | PROP-01 / PROP-02 | `anachronistic_prop` (or `ref_as_object` when the detail names a reference sheet) |
| `wrong_stage` | BODY-03 | `wrong_stage` |
| `anatomy` | BODY-05 | `malformed_anatomy` |
| `text_artifact` | LET-02 | `garbled_text` |
| `other` | MISC-00 | `other` |

The human picker exposes MORE classes than the scanner detects (style drift, dead
camera, under-sized tier, void background, …) — that asymmetry is intentional: human
flags on scanner-blind classes are the queue for expanding the scanner's checklist.

## 1. Flag UX (creator.php cockpit + review.php)

Where the owner already looks at panels, one extra control:

- **Lightbox / panel detail**: a compact `🏴 defect` row — a `<select>` grouped by
  registry category (Cast, Wardrobe, Body, Face, Lettering, Camera, Environment, Style,
  Continuity), options labelled with the human name from the registry (e.g. "Duplicate
  character — same person twice"), plus a 1-line optional note input and a Flag button.
  Two clicks for the common case, three with a note.
- **Quick-chips for the top-N**: above the select, chips for the owner's most-flagged
  classes (computed from the log, fallback: CAST-01, LET-02, FACE-01, BODY-01, WARD-01).
  One click = flag with no note.
- **Keyboard**: in review.php's existing keyboard-triage mode, `f` opens the picker on
  the focused tile; digits pick a chip.
- Flagging does NOT change the panel's rating/winner state — flag-and-keep is valid
  ("shippable but note the wardrobe slip"); rejection stays a separate act.
- The existing free-text `do=feedback` box stays for directorial notes ("warm the key
  light"); the flag path is for *defects* — the picker's last option "Other/unclassified"
  (MISC-00) catches anything the taxonomy misses and is itself a signal the registry
  needs a new row.

## 2. Storage (two writes per flag, both race-safe)

**a) Per-image, on the image's meta (same file the scanner writes):** append to a new
`flags[]` array via `s_with_lock(imeta_path($id))` — sibling of the existing `analysis`
field, never overwriting it:

```json
{"ts":"2026-07-18T09:12:00-07:00","by":"owner","defect":"CAST-01",
 "slug":"duplicate_character","note":"second Dana in the doorway","src":"human"}
```

**b) Global append-only event log** `data/defect-log.json` (array; `s_with_lock`), one
event per flag AND one per auto-detected defect, so stats never require walking every
project:

```json
{"ts":"...","project":"reseda","file":"p3-2_a.png","panel":"p3-2",
 "defect":"CAST-01","slug":"duplicate_character","sev":"high",
 "src":"human|qa|ggqa|gate","by":"owner","note":"...","verdict":"fail"}
```

Writers of `src:qa|ggqa` events: `qascan_one` and `gg_qa` append at the same moment they
write `analysis` (normalising type→slug per §0). `src:gate` is reserved for repo-side QA
gates (post-flight verdicts) if/when they report back through bridge.php. Panels-ingested
counts (the denominator for defects-per-page) come from the ingest events already stored
per project — no new counter needed.

## 3. Stats + trend chart

A small **🏴 Defects** section (either `studio/defects.php` standalone — low clobber
risk — or a card on `cc.php`):

- **Per-defect frequency table**: count by registry ID over 7/30/all days, split
  human vs auto columns. The human≫auto rows are the scanner's blind spots, ranked by
  real frequency — this table IS the living gap analysis (supersedes the static estimate
  in DEFECT-REGISTRY.md §gap-analysis as data accumulates).
- **Defects-per-page trend**: weekly buckets of (defect events ÷ panels ingested),
  one line for human flags, one for auto — a simple inline SVG/canvas sparkline. This is
  the loop's success metric: both lines trending down; the human line approaching zero
  is "unattended-ready".
- **Per-project breakdown** so a regression in one pipeline (e.g. GrowGetter generator
  vs import.php i2i) is visible instead of averaged away.

## 4. Flags → new rules (the improvement arm)

Two timescales:

**Fast loop (per-run, automatic, no repo change):** when a project's recent log (last
K panels) shows ≥2 events of one defect class, the genspec/reshoot prompt for the next
panels in that project auto-prepends the registry row's *prevention recipe* (each
registry row carries prompt-injectable prevention text). This is the same mechanism as
the existing targeted-feedback reshoot (`do=feedback` with panel → enqueue), but driven
by structured flags and scoped to the defect's known fix. No approval needed — it only
strengthens prompts.

**Slow loop (permanent, owner-gated):** a threshold rule — defect class X accumulates
≥N human flags (default N=5) in 30 days AND the registry marks its coverage as GAP or
PARTIAL — triggers a **rule-draft task**:

1. The Studio enqueues a `kind:'lesson-draft'` job (bridge.php) or an Ops task
   (`ownerType:'ai'`), carrying the defect ID, the flagged panels' files/notes, and the
   registry row.
2. A Claude session (the ops runner's executor, or a manual session) drafts: a new
   L-lesson section (symptom = the owner's own notes, verbatim-quoted), a rule-module
   sketch if prompt-composable, a qa-checklist line, and a `ck_qa_checklist()` line if
   vision-detectable.
3. The draft is posted as a task note / board note — **the owner approves before
   anything lands** (per `feedback_never_post_without_permission` and the gate-integrity
   rule: `qa/` gate-script changes are proposed as diffs, never patched-and-proceeded).
4. On approval, a session commits the lesson/rule + CHANGELOG to this repo and (if the
   scanner checklist changed) deploys creator.php per DEPLOY-NOTES.

Closing the loop: the commit adds the new coverage links to DEFECT-REGISTRY.md, flipping
the class from GAP → covered; subsequent flags of that class now measure whether the fix
*worked* (frequency should fall — visible on the §3 table).

## 5. Alignment maintenance

- `ck_qa_checklist()` (creator.php) should be regenerated from the registry whenever a
  vision-detectable class is added — the registry row's "symptom" text is written to
  double as the checklist line. Until the scanner is data-driven, the mapping table in
  §0 is the contract; any edit to either side updates both + DEPLOY-NOTES markers.
- The per-project QA chains (`projects/*/qa/`) and post-flight verdict subagents should
  cite registry IDs in their findings so `src:gate` events join the same stats. Gate
  scripts are integrity-protected — those changes are proposed diffs for user re-blessing.

## 6. Deploy plan (separate session, NOT this commit)

Order of work, smallest first, all under the fetch-live protocol:

1. `defect-log.json` writers: extend `qascan_one` + `gg_qa` to append events (§2b). No UI.
2. Flag UI + `do=flag_defect` handler in creator.php lightbox; mirror in review.php
   (its own `do=note`-style JSON handler). New feature markers for DEPLOY-NOTES:
   `flag_defect`, `ck-flagrow`, `DEFECT_TAXONOMY` (the PHP const holding the id/slug/label
   list), `defect-log.json`.
3. `defects.php` stats page (standalone file, low clobber risk) + one link/tile on cc.php.
4. Fast-loop prevention-injection in the genspec path; then the slow-loop draft trigger.

Verification per the concurrent-deploy rule: after ANY creator.php deploy, grep both the
new markers and every existing marker table row in DEPLOY-NOTES.md.

## Non-goals

- No auto-committing rules without owner approval; no auto-deploys of gate scripts.
- Not a rating system — ratings/winners already exist; flags are orthogonal defect data.
- No attempt to make the scanner detect every class — human-only classes are first-class
  citizens of the same log; the stats decide which ones earn automation next.
