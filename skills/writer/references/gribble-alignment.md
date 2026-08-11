# Gribble Alignment — what `studio/gribble.php` does, what the Writer reuses, what it does differently

A script writer already exists in this ecosystem: the Studio's **Gribble Script Writer** (`studio/gribble.php`, browser + bridge-key headless). This note keeps the two honest about their relationship so neither silently drifts into the other's job.

## What gribble.php is

A server-side generator that writes full comic scripts **in Gribble's voice and — more importantly — his measured STRUCTURE**, then mechanically verifies the result:

- **The measured profile (GR_FORMULA).** Every number comes from a real parse of the 41-script corpus (`~/Documents/gribble stories/`, 1,355 pages / 5,397 panels; `research/gribble-corpus/`): 28.9% of pages are growth pages in ~5 separate runs; first growth at ~11%; **the grid break** — 98.4% of pages are worth four panels but 30.8% collapse into one full-page image, and those merged pages are 70.3% growth vs 1.7% for ordinary panels, a **41× enrichment. The grid break IS the transformation device.** Panel economy: ~18-word art directions, ~8–10-word lines, 18% silent panels. Story shape: contested power source, power changes hands, one-upmanship sized against people, dominance climax, apotheosis-or-deflation ending.
- **The loop: write → parse → score → one repair pass** naming the exact misses (`gr_report()` is a PHP port of the corpus parser). The owner sees the structure report next to the script.
- **Calibrated gates.** The scoring rules were validated by running them over Gribble's own scripts (`validate_targets.py`, `validate_story_gates.py`): 70% of his full-length scripts pass; any rule that rejected his good work was measuring the wrong thing and got loosened. Two floors are deliberately held *above* his median (growth density, grid-break) because growth is the product — the generator imitates his best scripts, not his average.
- **A library** (every generated script auto-saved) and **mandatory attribution** — scripts are `AI-generated · Gribble-inspired`, never credited to the real person.

## What the Writer (Stage 2) reuses

1. **The validate-then-repair pattern.** `validate_script.py` plays `gr_report()`'s role: parse the output mechanically, score against measured targets, name exact misses, repair until clean. Claude's promises are not load-bearing; in-path gates are (CLAUDE.md doctrine).
2. **The growth-structure numbers**, as floors and warnings: growth density targeted by intent (the Writer uses the corpus chapter-type table, which brackets Gribble's 25–35%), first growth early (warn past ~25%; his median is 11%), multiple escalating runs with at least one 3+-panel run, ~1-in-5 silent panels, terse art direction (~18-word target).
3. **The grid break, translated.** Gribble's merged full-page image maps to our `SPLASH` page flag / `[size: splash]` + `reveal`/`whole_body` beats: run a tight panel rhythm for story, then give the transformation the whole page. A script of uniform four-panel pages is structurally flat in either format.
4. **Story discipline**: ordinary want on page 1 answered by the ending; escalation-not-repetition (each capstone re-pegs scale against a new gauge); land the ending with a beat of consequence; keep leads tellable-apart at every size (→ `marks:` in the cast block).
5. **SFW ≠ nice.** Coverage constraints never sand off menace, gloating, or dominance — those are story, not rating.

## What the Writer does differently — and why

1. **Not locked to Gribble's story shape.** gribble.php *enforces* his signature (contested artifact, hostile takeover, apotheosis/deflation, 88% dominance climax) because imitating him is its brief. The Writer serves whatever concept the ideator selected — tone is a polled choice (`triumphant-playful` house default; `dominant/menacing` is the Gribble-shaped option, not the only one). Its structure gates are corpus-derived (9 published comics) + Gribble-derived where structural, but its *story* gates are the spine fields, not his villain-turn formula.
2. **Different output format.** Gribble format is a prose artist script (`Page 1` / `Panel 2- …` / `Susan- "…"`) — script-breakdown can digest it, but Stage 3 then has to *infer* beats, tiers, cameras, scenes. The Writer's `script.md` (see `script-format.md`) carries those as first-class annotations so Stage 3 transcribes instead of inferring. gribble.php's `gr_create` hands its scripts to the same Stage 3; they just arrive lossier.
3. **Pipeline vocabulary.** Tier curves, transformation beats, staging values, camera tokens, story-spine fields, device declarations — none exist in the Gribble format; all are required by our downstream gates.
4. **Different validation targets.** gr_report scores Gribble-likeness (merged-page %, growth-merge alignment, dominance probe, apotheosis/deflation ending). validate_script.py scores pipeline-readiness (density floor by chapter type, L13 splits, tier monotonicity, scene decomposition, coverage lint). A script can pass one and fail the other — correctly.

## Where the imitation-gate lesson applies here

The transferable meta-lesson (per `project_gribble_script_writer`): **validate imitation/structure gates against the real corpus before trusting them.** An early gr_report draft rejected three of Gribble's own best scripts; the calibrated version passes 70% of his corpus, and every deliberate divergence from his median is documented as a choice.

For the Writer that means: `validate_script.py`'s floors are anchored to *measured* sources (the corpus study's chapter-type table, Gribble's structural numbers, the L-lesson thresholds that Gate B enforces downstream) — not invented. If a floor starts rejecting scripts the owner judges good, the gr_report precedent is the playbook: run the gate over known-good scripts (the digested hand-fed scripts in `projects/`, the Gribble corpus for structural rules), find which rule rejects known-good work, and loosen *that rule* with a comment citing the calibration — never bypass the gate. When a hand-written script the pipeline already produced well fails a Writer check, the check is the suspect first.

## Interop

- A gribble.php script can enter the pipeline as-is (Stage 3 digests prose scripts) — or be *upgraded* by running the Writer in "annotate" mode: keep the text, add the header/beat/tier annotations, then validate. Worth doing when a Gribble-library script is picked for full production.
- The Writer does not save into the Studio's gribble library, does not imitate Gribble's voice unless the polled tone says so, and never credits any real person. gribble.php remains the tool for "write me a Gribble script"; the Writer is the tool for "script this concept for the line."
