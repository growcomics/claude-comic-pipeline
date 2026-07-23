# Post-flight judge instructions — Heather & Mark fix pass

Per `CLAUDE.md`'s Generation protocol step 4 (POST-FLIGHT) and `feedback_audit_via_subagent.md`:
**a fresh-context subagent** — one with no memory of composing or submitting the job — judges
every downloaded pick before `qa/bank.py` is allowed to touch it. The generator never grades its
own work. This doc is that subagent's brief, scoped to this project's ~35-job fix pass.

Per `qa-scaffold-PLAN.md` section 4: this project does **not** get a ported `defect-registry.json`.
`qa-report.md` (already in hand, already fresh-context-audited) is the rubric directly — "does this
regenerated panel resolve the specific `qa-report.md` defect line it was assigned to fix, without
introducing a new one — camera/wardrobe/identity/tier held per the job's constraints?"

## Canonical rubric files (read verbatim, do not paraphrase from memory)

Per `feedback_dont_paraphrase_canonical_rubrics.md` / `feedback_audit_use_canonical_rubric.md`,
open and apply these by path, not from summary:

- `skills/continuity-check/qa-checklist.md` — general per-panel defect categories (only relevant
  where a job's `out_of_scope_defects_on_panel` doesn't already exempt the finding — see below).
- `skills/comic-production/references/cinematic-framing.md` — camera-variety rubric; only load-
  bearing for the **two new-beat jobs** (fix-new-a, fix-new-b), which exist specifically to flip
  Act 3b's camera-variety verdict from FAIL to PASS.
- `projects/heather-and-mark/qa-report.md` — the project's own fresh-context audit. This is the
  primary rubric for every retouch job: locate the panel's row (Blockers table or the SYSTEMIC
  should-fix row) and confirm THAT specific finding is resolved.
- `projects/heather-and-mark/fix-jobs.json` — the specific job's `defect_summary`, `constraints`,
  `corrected_dialogue`, and `out_of_scope_defects_on_panel`. This is the job's contract: only what
  it asks for should change.

## What to attach for judging

For every job, the judge needs, side by side:

1. The **original accepted panel** (`panels/<panel_id>.<ext>`, e.g. `panels/009.jpeg`) — the "before".
2. The **newly downloaded candidate pick** — the "after".
3. The job's exact entry in `fix-jobs.json` (match on `id` or `panel`).
4. The relevant `qa-report.md` row(s) for that panel number (Blockers table, or the SYSTEMIC row +
   any per-panel Should-fix/Cosmetic rows for the same panel).

Do not judge from the prompt or receipt alone — compare pixels. The receipt's `prompt_sha` is
already independently verified by `qa/audit_prompt.py` (Layer 2); the judge's job is visual, not
textual.

## Universal checks (every job, every fix_type)

1. **Targeted defect resolved.** The exact defect named in `fix-jobs.json`'s `defect_summary` (and
   the matching `qa-report.md` line) is gone. Quote what changed.
2. **Nothing else drifted.** Every `constraints` field that says "unchanged" must actually be
   unchanged versus the original panel: camera framing/crop, character poses, expressions,
   wardrobe/costume state, background, props, lighting mood, and — critically for the tier-lock
   jobs — muscle size/scale. A pick that fixes the named defect but recomposes the shot is a FAIL
   under this protocol (see PLAN section 6's whole reason for existing).
3. **No new defect introduced.** Check against the general categories in
   `skills/continuity-check/qa-checklist.md` even though this isn't a full continuity audit — a
   retouch that fixes one bubble but garbles another, adds an extra hand, or introduces a new
   duplicate character is a FAIL regardless of whether the targeted defect is fixed.
4. **`out_of_scope_defects_on_panel` is not a checklist.** Items listed there (e.g. 021's tape-prop
   morph, 042's missing-bottoms coverage gap, 053's gym extras) are KNOWN, PRE-EXISTING, and
   explicitly not this job's responsibility. Do not fail a job for not fixing them. Do note in the
   verdict's `notes` field if one of them got worse as a side effect of the retouch — that WOULD be
   a new-defect fail under check 3, just flag it as "pre-existing X, retouch made it worse" rather
   than "X unresolved."

## Fix-type-specific checks

### `i2i re-letter` (30 jobs: 009, 010, 014, 015, 017, 018, 020, 021, 023, 025, 027, 030, 035, 037,
038, 039, 042, 043, 046, 047, 049, 053, 056, 059, 060, 062, 063, 064, 065, 068)

- Read every baked bubble/caption in the candidate pick. Compare word-for-word against the job's
  `corrected_dialogue[].line` — exact text, no prefix (`HEATHER:`/`MARK:`/`MARK'S THOUGHTS:`), no
  stray quote marks, no doubled clauses, no truncation.
- Tail direction matches `tail_target` (note fix-015's explicit tail RETARGET from Mark to Heather,
  fix-017's conversion from a parenthetical stage-direction to a normal tail, fix-059's box 2
  conversion from a mis-tailed bubble to an untailed caption, fix-062's stripped prefix).
- **fix-059 only**: confirm the THIRD box (`HEATHE: grace.`) is gone entirely — not re-lettered,
  deleted. Verify all three lettering operations landed (edit + retype-as-caption + delete), not
  just the most visible one — this job's own `risk_notes` warns partial application is the likely
  failure mode.
- **fix-062 only**: the stat box number is a **narrative decision the owner must confirm before
  generation**, not a pure transcription fix — see the job's `note`. Before judging pass/fail on
  content, confirm the number actually baked matches whatever number is recorded in this job's
  `corrected_dialogue` at generation time. If that number is still the plan's placeholder and
  wasn't updated after an owner decision, flag it in `notes` and lean FAIL rather than guess.
- **fix-020 only**: the completion "than her" is flagged in the job as an editorial judgment call.
  Judge only whether the BAKED text matches what's in `corrected_dialogue` — do not re-litigate the
  wording choice; that's a pre-generation decision, out of scope for this post-flight pass.
- Anatomy/pose/camera/wardrobe must be pixel-stable versus the original — these are text-region-
  only edits per every one of these jobs' `camera_lock`.
- Bundled non-lettering changes ARE in scope when the job explicitly bundles them (fix-015's tail
  retarget) — verify those too, they're part of this job's contract, not scope creep.

### `i2i re-render` (3 jobs: 007, 032, 033)

- **007**: exactly ONE Heather in frame (the standing figure); the duplicate bent-over figure is
  gone; the admiring line is baked exactly once (single tailed bubble, bottom-center) — the
  floating top-right duplicate caption is gone; the background group (4 flexing women + 2
  photographing boys) is untouched; no new extras were introduced while removing the duplicate.
- **032**: Heather's arm/torso muscle scale now reads consistent with panels 030-031's established
  huge tier (compare directly against those two panels, attached per the job's `attach_hint`) — not
  merely "bigger than before," but scale-matched to its neighbors. The already-clean "Oops." bubble
  is untouched. Sales clerk, mirror reflections, and fitting-room framing are untouched.
  **Cross-check note for the judge**: `qa-report.md`'s own text for 032 calls the pre-fix render
  "slim-toned (arms ~baseline athletic)" — confirm the fix is a visible jump to the 18in-chapter
  scale, not a marginal touch-up that still under-shoots 030-031.
  **Cross-check note for the judge**: `qa-report.md`'s own text for 032 calls the pre-fix render
  "slim-toned (arms ~baseline athletic)" — confirm the fix is a visible jump to the 18in-chapter
  scale, not a marginal touch-up that still under-shoots 030-031.
- **033**: ONLY the bicep sub-panel's muscle rendering changes to read as an 18-inch scale. The
  thigh and glutes sub-panels, and ALL 5 baked text elements (2 captions + 3 tape labels: "Biceps:
  18 inches. Butt: 55 inches. Thighs: 26 inches." / "Curves and power together." / the 3 tape
  numerals), must be pixel-identical to the original — verify every one of the 5 text elements
  individually, this job's own `risk_notes` flags partial-survival as the likely failure mode.

### `new beat` (2 jobs: fix-new-a, fix-new-b)

There is no prior "before" image and no `qa-report.md` defect line — these resolve a **verdict**
(Act 3b's camera-variety FAIL), not a per-panel defect. Judge against:

- The job's own `constraints` (identity/tier/wardrobe/camera_lock) — identity must match the
  established Act 3b Heather+Mark appearance from neighboring panels 018-028; tier must match
  020-023's 14.5in-chapter scale, not baseline and not any later act's larger tiers; wardrobe is
  the job's own flagged editorial guess (confirm it was owner-approved before generation, per the
  job's "needs owner confirmation" note — same pattern as fix-062, flag if ungrounded).
- Camera: genuinely wide-establish, environment fully readable (per L23's naming-5+-elements
  standard) — this is the entire point of the job, judge it as strictly as any other rubric item.
- No new caption/stat text, no invented canon beyond what the job describes — per the house rule in
  `feedback_dont_invent_state_changes.md`.
- fix-new-b is explicitly optional/skippable if fix-new-a alone already flips the Act 3b verdict —
  if fix-new-b was generated anyway, judge it on its own merits (it isn't automatically a fail for
  being "extra"), but note in `notes` whether it was actually needed.
- After banking, a fresh camera-variety re-check against `cinematic-framing.md`'s scaled rubric
  (≥1 wide-establish-or-splash per act) is the real acceptance test for the FAIL→PASS flip, not
  just this one panel's individual quality — flag this as an owner follow-up in the verdict notes,
  it's outside a single-panel judge's scope to re-run the whole act's audit.

## Verdict output — `qa/receipts/<job>.verdict.json`

`qa/bank.py` refuses anything without a verdict file where `pass` is `true`, and records
`verdict.get("tags", [])` verbatim into the ledger/pages-log chain. Write:

```json
{
  "job": "<same job string used in --job, e.g. edit:009>",
  "pass": true,
  "tags": ["short-hyphenated-descriptors", "e.g-lettering-clean", "e.g-camera-unchanged", "e.g-identity-match"],
  "notes": "One or two sentences: what was checked, what changed, anything flagged for the owner."
}
```

`pass: false` for ANY universal-check failure or fix-type-specific failure above — there is no
partial credit; a re-roll is cheaper than a downstream drift no one caught. Tags should name what
was verified (mirrors the donor project's own `verdict_tags` style, e.g. `identity-match-lois`,
`no-baked-text`, `anatomy-clean` — adapt the vocabulary to what this job actually checked, e.g.
`lettering-text-exact`, `tail-retargeted`, `third-box-deleted`, `tier-matches-030-031`,
`triptych-other-subpanels-untouched`).

## What this doc deliberately does NOT cover

- Pre-generation sign-off on invented/uncertain text (fix-020's "than her" completion, fix-062's
  proposed 29in figure, fix-new-a/b's wardrobe guesses) — those are owner decisions that should
  happen BEFORE a job is composed and submitted, not discovered here after the fact. If one reaches
  this post-flight step still unconfirmed, flag it in `notes` and lean toward `pass: false` rather
  than rubber-stamp an unconfirmed story fact into the permanent ledger/pages-log.
- Re-running the full `qa-report.md`-style audit on panels this batch does NOT touch. Scope is
  strictly the ~35 jobs in `fix-jobs.json`.
