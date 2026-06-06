---
name: comic-folder-organizer
description: Organize, sort, group, deduplicate, and rename a folder of AI-generated comic page images (Higgsfield, Midjourney, Nano Banana, etc.) using Claude Cowork's folder access. Use this whenever the user has a folder of comic pages, panels, or sequential art that needs to be put in story order, grouped by scene, or deduplicated — even if they don't say "organize" explicitly. Trigger phrases include "reorder my comic pages", "sort these panels", "I have a folder of comic generations", "rename these by scene", "find duplicates in my comic folder", "build a comparison sheet", "clean up my chapter folder", or any mention of cleaning up output from comic-generation tools. This is distinct from comic-production (which generates new comic art) — this skill organizes existing files. Requires Cowork folder mounting.
---

# Comic Folder Organizer

Help the user turn a messy folder of AI-generated comic pages into a clean, story-ordered, deduplicated sequence.

The user generates comic pages with tools like Higgsfield, Midjourney, Flow, or Nano Banana. They end up with folders full of images that have hash-based or timestamp-based names, are out of story order, and contain near-duplicate panels from re-rolling the same scene. This skill walks the user through a Cowork-based workflow to fix all of that.

For a long-form retrospective of how earlier sessions evolved this skill, see `LESSONS_LEARNED.md` in this directory.

## When this skill applies

The user has a folder of comic page images on their computer and wants to:
- Put them in story order
- Group them by scene or story beat
- Find and resolve duplicate generations
- Rename them to a clean sequential naming scheme (`001.png`, `002.png`, …)
- Place newly-generated supplementary panels into an existing numbered sequence
- Pull out non-story reference images (character sheets, lineups, model sheets)
- **Find panels with technical defects** — bad hands/fingers, melted faces, garbled SFX text, phantom background extras — that need cleanup or regeneration → **Defect QA pass** (Stage 11, see `defect-taxonomy.md`)
- **Figure out what's *missing* from a partial post** — story gaps, skipped beats, missing transitions or backstory — and get ready-to-generate prompts to fill them → **Story Doctor pass** (Stage 12, see `story-gap-types.md`)

If the user wants to *generate* comic pages rather than organize existing ones, that's the `comic-production` skill instead. Note that the two new passes (Defect QA, Story Doctor) **recommend** new generations and hand you ready-to-paste prompts — but the actual generating still happens in your generation tool (Higgsfield / Flow), then the new panels come back through the supplementary-insertion flow (Stage 8).

## Prerequisite: Cowork folder access

This workflow depends on Claude Cowork's ability to mount and manipulate a local folder. If the user isn't in Cowork, tell them this workflow needs the desktop Cowork feature and stop there.

## Standing operating principles

These bind every step of the workflow. Most of them came out of corrections during the Bay Watch session — see `LESSONS_LEARNED.md` for the full history.

1. **Composite-first for any bulk action.** Build a labeled preview composite and wait for the user to confirm BEFORE moving files to `trash/` or `refs/`, before renumbering, before repositioning batches. Single-file actions the user named explicitly ("011 goes to trash") don't need the preview — that's already explicit consent. Anything inferred, batched, or auto-paired needs the preview gate.

2. **Trash is a subfolder, never `rm`.** When the user says "delete" / "trash" / "throw away," interpret it as `mv` to `<chapter>/trash/`. Never use `rm`. Trashed files must remain recoverable.

3. **`refs/` is a first-class destination.** Non-story images — character sheets, lineups, single-character portraits, model sheets — go to `<chapter>/refs/`, NOT to `trash/`. They are still useful reference material.

4. **Use a Sonnet subagent for visual batch reads.** Opus is for synthesis, planning, scripting, and final composite work. Reading 50+ panels to extract content is exactly the kind of task Sonnet handles well at a fraction of the cost. Send the subagent the canonical cast spec, the list of files to read, and the expected output format.

5. **Confirm the cast and outfit lock with the user before any continuity audit.** Don't infer the canonical look from a single in-context panel — that panel may itself be the drift. Ask the user to point at a character sheet or confirm the lock verbally.

6. **Confirm scene-block boundaries and character nicknames.** A chapter is rarely one flat sequence — it's usually 3–6 scene blocks (opening, TF scene A, TF scene B, antagonist scene, closing). User vocabulary may differ from how the cast appears in panels ("the lesbians" might mean a specific NPC pair, not the main duo). Build a scene-cast dictionary at the start.

7. **REPOSITION is a first-class action, not a special case.** The full action vocabulary is KEEP / TRASH / REFS / **REPOSITION** / NEW-INSERT / **FIX** / **GAP**. Some panels are keepers in the wrong slot (REPOSITION). Some are keepers with a fixable technical defect (FIX) — they stay in the sequence, but get logged for cleanup or regeneration, not trashed. GAP is not a file at all — it's a *missing* panel the Story Doctor proposes generating.

8. **One composite per question.** Don't bundle "everything I trashed," "the keepers next to the drops," and "ambiguous flags I need you to resolve" into one mega-image. Build a focused composite per decision the user is making.

9. **Default to user judgment on conflicts.** If a sub-agent's content read disagrees with what the user says is in a panel, the user is right. Flag the discrepancy and proceed on their model.

10. **Use `AskUserQuestion` when a directive is structurally ambiguous.** "n10 is after 069" and "069 belongs in scene X" can be read two ways — ask which.

11. **Generative passes propose, the user disposes — same as every other action.** The Defect QA and Story Doctor passes (Stages 11–12) are the most "opinionated" steps: they recommend regenerating panels and generating brand-new ones, which costs the user real credits. Treat their output exactly like an audit: a structured proposal, surfaced in a labeled composite, that the user vetoes line-by-line before anything is acted on. Never silently fold a Story-Doctor GAP into the renumber, and never tell the user a panel is broken without showing it to them next to *why*.

12. **Never flag an intended feature as a defect.** This cast is deliberately off-distribution — heavy musculature, large chest sizes, photoreal CGI/3D rendering, and intended transformation states (costume destruction at a TF tier) are all *on purpose*. The Defect QA pass hunts for *unintended* technical failures (extra fingers, melted faces, garbled text), not for the project's stylistic locks. When unsure whether something is an intended feature or a defect, flag it as a question, don't auto-mark it FIX. See the guardrails in `defect-taxonomy.md`.

## The workflow

Work through these steps with the user. Don't rush ahead — pause for their input at each decision point.

### 1. Mount the folder

Trigger the folder picker so the user can select the folder containing their comic pages. If the user is going to organize multiple folders, do them one at a time — finish a folder, then prompt for the next one.

### 2. Initial numeric rename (timestamp order)

Most AI-generation tools embed timestamps in filenames (e.g., `hf_20260406_194321_0d4500e0.png`). Rename all the files to `001.png`, `002.png`, `003.png`, … in timestamp order using **3-digit zero-padded** numbers. Chapters routinely exceed 100 panels — start with 3 digits to avoid a second renumbering pass.

If the folder is a re-organize of an already-numbered sequence, skip this step.

### 3. Get the story breakdown from the user

Ask for the scene block list — typically 3–6 high-level beats. Examples:

- "Apartment intro → Flying out → Beach landing → Asian (Kay) TF → Lesbian TF (other lifeguards) → Ritchie scene → Closing"
- "Venice gym → Bodybuilding contest → Boardwalk → Beach growth → Sunset"

Also nail down:
- The full canonical cast (names + a one-line visual description per character)
- The outfit lock per character (color, style, key accessories)
- Any nickname mapping the user uses ("the lesbians" = redhead + ponytail brunette pair)

Write this down in the conversation so subagents you spawn later can be briefed verbatim.

### 4. Visual audit via Sonnet subagent

Spawn a Sonnet subagent with the cast spec and the file list. Have it:

1. Open every image in batch.
2. Output a structured per-file action list:
   ```
   NNN.ext | KEEP | one-line content + scene block
   NNN.ext | TRASH | reason
   NNN.ext | REFS  | reason (character sheet / lineup)
   NNN.ext | DUPE-OF NNN | reason
   NNN.ext | REPOSITION → near MMM | reason
   ```
3. Flag duplicate clusters at the bottom: which keeper wins, which drop, why.
4. Flag any cast-count violations (extra people, missing characters) and outfit drift against the lock.

Trim the subagent's output to actions only — passes can be omitted.

### 5. Build the proposed-changes composite

Before any file moves. The composite should have sections:

- **REFS** (each panel labeled with "→ refs/" + reason)
- **HARD TRASH** (broken renders, cast violations, user-flagged)
- **DUPE GROUPS** — **show the keeper next to its drops** in the same row. Layout: `[KEEPER (green border) | DROP | DROP | DROP]`. Never show drops without their winning keeper visible alongside.
- **REPOSITION** (each panel with current slot vs proposed slot)
- **NEW INSERTIONS** (when adding supplementary files): `[existing BEFORE | NEW panel | existing AFTER]` rows.

Save to `_qa_review.png` or a per-step name like `_restructure_proposal.png`. Show it to the user and wait for confirmation or exceptions.

### 6. Handle ambiguities with a flags-resolution composite

If after the proposed-changes composite there are still unresolved questions ("is 019 a dupe of 015?", "which panel has the KRA-KOOM SFX?"), build a focused side-by-side composite where each flag occupies one row with the candidates visible. Save to `_flags_resolution.png`. Ask the user to answer each flag in one short message.

Do NOT proceed with execution while flags are open.

### 7. Apply the user's decisions

When the user says "apply" (or equivalent), and only then:

1. Move REFS files to `<chapter>/refs/` (create dir if missing).
2. Move TRASH and DUPE-DROP files to `<chapter>/trash/` (create dir if missing).
3. Resolve REPOSITION moves into the keeper ordering.
4. Two-stage rename to the final `001.{ext}`–`NNN.{ext}` sequence — see "Two-stage rename" below.
5. Print the final count.

Preserve each file's original extension on rename (`.png`, `.jpg`, `.jpeg` may all coexist).

### 8. Supplementary insertions (new generations dropped in mid-session)

When the user adds more files into an already-numbered chapter:

1. List the new descriptive-name files (anything not matching `^\d+(\.\d+)?\.(png|jpg|jpeg)$`).
2. **Rename them immediately to `n01`–`nNN` short labels** so the user can type "n03 belongs in the lesbian TF area" without typing the full Higgsfield filename. Use a script that maps original → `nNN` and report the mapping.
3. Use a Sonnet subagent to read each `n*` file and propose insertion points based on scene-block context. Output: `n0X | INSERT AFTER NNN | scene block, reason`.
4. Flag suspect thumbnails: any file under ~150KB with a double-stamped filename (e.g. `Foo_..._.jpeg_..._timestamp.jpeg`) is almost certainly a downscaled re-save. Default to `SKIP-THUMB` (→ trash); compare against the higher-res original if found.
5. Build a `[BEFORE | NEW | AFTER]` composite for confirmation.
6. Apply, then renumber the full sequence.

### 9. Manual fractional inserts (`074.5.jpeg`)

The user may insert files into Finder/Explorer with fractional names — `074.5.jpeg`, `009.4.jpeg` — to slot between existing panels. The renumber routine must:

- Sort using natural/version ordering: `009 < 009.4 < 009.5 < 010`.
- Treat any `^\d+(\.\d+)?\.(png|jpg|jpeg)$` filename as a story panel candidate.
- Collapse the result to clean integers (`001`, `002`, …) preserving the natural-sort order.

### 10. Restoration

If the user wants something back from `trash/`, find it by stem (allowing for `__N` collision suffixes from previous moves), pull it back into the root, and re-slot it. Renumber afterwards.

### 11. Defect QA pass (optional — "which panels are broken?")

Run this on a story-ordered sequence to find panels with **technical render defects** — the kind that need cleanup or regeneration before the post ships. This is distinct from the `continuity-check` skill, which checks *cross-panel* drift (wardrobe/prop/location consistency). Defect QA checks *within-panel* technical quality.

Before you start, read **`defect-taxonomy.md`** in this directory — it's the full defect catalog, the S1/S2/S3 severity scale, the regen-vs-inpaint-vs-keep triage rules, and (critically) the **do-not-flag guardrails** for the project's intended features (muscle/chest size, CGI style, intended TF costume states). Pass the taxonomy to the subagent verbatim; don't paraphrase it from memory.

1. **Confirm the cast + outfit lock first** (same as a continuity audit — principle 5). The subagent needs to know what "correct" looks like so it doesn't flag an intended feature.
2. **Spawn a Sonnet subagent** with the panel list + the full `defect-taxonomy.md`. Have it open every panel and output, defects only (clean panels omitted):
   ```
   NNN.ext | FIX | S2 | hands  | left hand has 6 fingers, mid-frame | REGEN
   NNN.ext | FIX | S3 | accessory | phantom wristwatch on Lana, edge of frame | INPAINT
   NNN.ext | FIX | S1 | face   | Lacy's face melted/asymmetric, central subject | REGEN
   NNN.ext | FIX | S2 | text   | SFX reads "KRAA-KOOOM" garbled letterforms | INPAINT
   NNN.ext | ?   | S2 | anatomy | unusually large arm — intended muscle or defect? | ASK
   ```
   Columns: panel · action · severity · category · one-line description with frame location · recommended remedy (REGEN / INPAINT / KEEP / ASK).
3. **Triage default is per-panel** (not "regen everything"): structural defects on the central subject → REGEN; localized/peripheral defects → INPAINT; cosmetic defects that won't read at post size → KEEP. The taxonomy spells out the decision rules.
4. **Build a `_defects_review.png` composite** — one row per flagged panel: `[panel (cyan border) | zoom/crop on the defect if helpful | label: severity + category + remedy]`. Group by severity (S1 first). This is the veto gate — the user confirms which to fix, downgrades false positives, and resolves any `ASK` rows.
5. **Write the surviving list to `_defects_report.md`** — a checklist worklist: `[ ] 034 — REGEN — Lacy face melt (S1)`. The FIX panels **stay in the sequence as keepers** (don't trash them — a broken panel in the right slot beats a hole). The report is the user's regeneration to-do.
6. When the user regenerates a fix and drops the new file in, it comes back through **Stage 8 (supplementary insertion)** or as a fractional replacement (e.g. `034.1.jpeg` to replace `034`), then renumber.

> Defect QA never moves or deletes files on its own. Its only outputs are the review composite and the `_defects_report.md` worklist. A FIX flag is advisory until the user acts on it.

### 12. Story Doctor pass (optional — "what's missing / what else should I generate?")

Run this when the user has a partial post (e.g. "this is ~75% of a complete scene") and wants help finding **narrative gaps** and getting **ready-to-paste generation prompts** to fill them. Read **`story-gap-types.md`** in this directory first — it has the gap taxonomy, the P1/P2/P3 priority scale, the completeness-score rubric, and the generation-prompt template.

1. **Get/confirm the scene-block breakdown, cast, and outfit lock** (Stage 3). The Story Doctor reasons about *story*, so it needs to know the intended beats. If the user has a script or beat sheet, get it — gaps are much easier to spot against the intended outline.
2. **Spawn a Sonnet subagent** with the ordered sequence + scene blocks + `story-gap-types.md`. Have it read the panels *in order* and identify gaps:
   ```
   GAP after 012 | P1 | skipped-beat   | Kay starts transforming with no trigger panel — show the catalyst
   GAP after 027 | P2 | transition     | hard cut from beach to locker room; needs an establishing bridge
   GAP before 001 | P3 | weak-open     | no hook; a wide establishing shot would ground the location
   GAP after 045 | P2 | reaction-shot  | big growth beat lands with no one reacting
   ```
   Columns: slot · priority · gap-type · what's missing & why.
3. **For each gap, produce a ready-to-paste generation prompt** built from the template in `story-gap-types.md`, anchored to the canonical cast + outfit lock: it names the camera/framing, the cast present (with their locked outfit/colors), which refs to attach (cast lineup, env ref, face card), and bakes in the project's known generation guardrails (suppress in-scene ref rendering, name the hair state, suppress anachronistic accessories, attach the env ref for location panels, oversize chest to compensate for model scale-down, etc.). The goal: the user copies the prompt straight into Higgsfield/Flow and generates.
4. **Compute a completeness score** per the rubric (rough %: how many of the expected beats per scene block are present). Report it as "this post reads ~75% complete — the 3 P1 gaps are what's blocking the other 25%."
5. **Build a `_story_gaps.png` composite** — one row per gap: `[existing BEFORE (green) | GAP placeholder (yellow dashed) | existing AFTER (green)]`, labeled with the gap-type, priority, and a one-line of the proposed panel. The yellow-dashed placeholder visually marks "panel to be generated, doesn't exist yet." This is the veto gate: the user picks which gaps to actually fill.
6. **Write `_story_gaps.md`** — the prioritized gap list, each with its slot, gap-type, rationale, and the full ready-to-paste prompt. As the user generates each one, it enters via Stage 8 (a GAP becomes a NEW-INSERT once the file exists), then renumber.

> A GAP is a *proposal to generate*, not a file. The Story Doctor's job ends at the prompt + composite; nothing enters the sequence until the user has generated the panel and dropped it in.

## Composite-building reference

Always:

- Save composites to the chapter root with underscore-prefix names (`_qa_review.png`, `_restructure_proposal.png`, `_flags_resolution.png`, `_defects_review.png`, `_story_gaps.png`, `_final_sequence.png`) so they sort to the top in Finder and are easy to find.
- Use a fixed color key across composites: **GREEN = current/keeper**, **YELLOW (solid) = new insertion**, **YELLOW (dashed) = GAP placeholder (panel to be generated, doesn't exist yet)**, **ORANGE = moved/repositioned**, **RED = trashed**, **BLUE = refs**, **PURPLE = flag/ambiguity**, **CYAN = FIX (defective keeper to clean up/regenerate)**.
- Label every cell with: original panel ID (e.g. "orig 029"), the action ("→ trash/", "NEW — Asian TF"), and a one-line reason. Don't leave the user guessing.
- For paired keepers-vs-drops layout, the keeper is always the leftmost cell in the row.
- Cap thumbnail rows at 4–6 cells wide so the composite stays scrollable in Preview at 100%.

## Two-stage rename (anti-collision pattern)

Direct rename can clobber files when target names overlap source names. Always use a two-stage temp-prefix scheme:

```python
# Stage 1: every keeper → __tmp_NNN.ext
for i, src in enumerate(ordered_sources, start=1):
    shutil.move(src, FOLDER / f"__tmp_{i:03d}{src.suffix}")
# Stage 2: strip prefix → NNN.ext
for tmp in sorted(temps):
    shutil.move(tmp, FOLDER / tmp.name.removeprefix("__tmp_"))
```

Verify all source files exist before stage 1 — bail with a list of missing files if not. Never let the renumber run partial.

## Working style

- **Be specific in reports.** "06.png — Steve and Vince mid-flex on gym floor, sun behind them" beats "shows two characters." The user scans for misplacements; specificity is what enables that.
- **Treat the user's scene breakdown and cast spec as authoritative.** If an image seems to belong elsewhere, raise it as a question, don't silently move it.
- **Maintain scene-name vocabulary across the session.** Once the user names a scene ("the begging scene," "Asian TF area"), use that name in your composites and reports back.
- **Move chapter by chapter.** Finish one folder cleanly before starting the next.
- **Don't compress the audit → compose → veto loop.** Skipping the compose step is what triggers "you trashed things without showing me" pushback.

## What "done" looks like

```
chapter5/
  001.png   ← opening
  002.png
  …
  070.jpeg  ← closing splash
  refs/
    046.jpg ← redhead lifeguard character sheet
    047.jpg ← dark-ponytail lifeguard character sheet
    …
  trash/
    029.jpg ← broken render
    050.jpg ← user-flagged
    …
  _final_sequence.png   ← optional review composite kept for reference
  _defects_report.md    ← optional (Stage 11) regeneration to-do list
  _story_gaps.md        ← optional (Stage 12) gaps + ready-to-paste prompts
```

Clean sequential numbering, no gaps, no fractional names, no descriptive-name leftovers in the root, story order matches the user's scene breakdown, and every trashed or reffed file is recoverable.

If the optional passes were run, the user also walks away with two worklists: `_defects_report.md` (which panels to regenerate/touch up and how) and `_story_gaps.md` (what to generate to finish the story, each with a paste-ready prompt). Both are advisory — the panels they reference re-enter the sequence through Stage 8 once the user generates them.
