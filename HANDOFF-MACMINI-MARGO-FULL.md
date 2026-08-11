# HANDOFF — margo-full, Mac mini continuation (2026-08-11 ~08:30 PDT)

> Owner closed the laptop mid-run. `HANDOFF-MACMINI.md` (sibling session) covers
> **not-so-supra-man** and mentions margo-full ZERO times — this file is the
> margo-full half. Read both.

## Where it stands

| | |
|---|---|
| Board | https://3dmusclecomics.com/studio/review.php?p=margo-full |
| Pages accepted + annotated on the board | **42 of 86** |
| Beats with variants but no winner | 12 (see corrective queue) |
| Beats never generated | 32 |
| Model | `nano_banana_2_lite`, aspect `3:4`, 8 variants/beat (2 rolls of count=4) |
| Credits | ~5350 at last check; whole remaining run is ~50-70 credits |

**The 42 accepted pages are already on the remote board, so they are safe and
machine-independent.** Nothing on the laptop is needed to preserve them.

## STRUCTURE — settled, do not re-litigate
Owner confirmed: **each panel IS its own standalone page/image.** 86 beats = 86
pages. There is NO page-composition / multi-panel-grid step, and the Gribble
4-panel-grid figure in `research/gribble-corpus/FORMULA.md` does NOT apply to this
run. An earlier session (mine) wrongly flagged this as a structural mismatch.

## Recovering the images on the mini

`variants/**/*.png` are gitignored and live only on the laptop. **`state.json` is
now tracked (force-added in this commit) and holds every job id** — that is the
recovery key. For any beat you need pixels for:

1. Collect its job ids from `state.json` (`beats.<id>.jobs`).
2. `show_generation_by_ids` (≤60 per call) → each completed item has `results.rawUrl`.
3. `python3 drive.py fetch <beat> <job_id> <rawUrl>`

Job results persist server-side on CloudFront. You do NOT need to re-generate
anything already generated. Note many older jobs are `failed`/`nsfw` — of one
40-job sample, 20 failed, 7 nsfw, 8 completed; that is normal, not data loss.

## Fixes already landed (do not redo)
- `54a511f` — **wardrobe now injected into all 86 prompts.** It was missing from
  0/86, so the only clothing signal was the `margo` ref image (in a lab coat), and
  the coat kept reappearing after b17 destroys it. Also fixed `drive.py winner`
  silently banking un-accepted panels, and added `flock` on `state.json`.
- `ab811ff` — re-roll queue; renumbered colliding variant files.
- `76391b3` — flat-face findings + face kill rule.

Proof the wardrobe fix works: b40 and b43 were 0/4 and 0/7 before, **6/6 clean** after.

## DO THESE TWO INPUT FIXES FIRST
Re-rolling before these will reproduce the same defects.

1. **Scope the SLEEVES clause to Margo.** Every prompt carries a global "when a
   muscle flexes inside a sleeved garment the sleeve seam splits open" line. It is
   not character-scoped or stage-scoped, so KRESS's tracksuit shreds. Cost 6/8
   tiles in b49-kress-protest, 3/8 in b06, and killed b04 v02/v03. One-line change
   in the beat builder; protects all 32 ungenerated beats.
2. **b45-tape identity bleed.** The amulet + grey tank bound to INGRID instead of
   Margo in 3 of 4 tiles, and the coat appeared on Ingrid in 2 of 4. Ref/staging
   attachment problem — fix the inputs, don't re-roll blind.

## Corrective queue — 12 beats
Full detail in `runners/bakeoff/runs/margo-full-20260811/REROLL-QUEUE.md`.

**Lab coat, zero clean variants (7):** b18-doorframe, b19-crate, b22-tomorrow,
b26-margo-watches, b48-terms, b52-amulet-blaze, b53-quads
**Wrong action (1):** b18b-calipers — wardrobe fine, but no tile shows calipers on the bicep
**Flat face (4, banked but should be replaced):** b02-vial, b07-stay-out,
b13-sleeve-tight, b50-clipboard-back

Corrective clauses that worked:
```
CRITICAL FIX: the previous roll dressed MARGO in a white lab coat. There is NO lab
coat, jacket, cardigan or any white over-garment in this scene — that coat was
destroyed earlier in the story. She wears the grey tank top ONLY.

CRITICAL FIX: the face was wooden last roll. The named emotion must visibly
transform the WHOLE face — brows driven, eyes wide or narrowed, mouth open or set.
Theatrical intensity, not a neutral expression.
```

## Judging — kill rules
The 8 standard rules PLUS the one that was missing:
```
9. Flat face — blank, neutral, waxy, doll-like, or a mild expression on a beat that
   calls for something strong. A calm face on a dramatic beat is a KILL.
```
Face quality was in every prompt but was never a kill rule, so 4 flat faces got
banked. Text is NOT a problem: all 42 banked pages audited, **0 text defects**.

## Gotchas that cost this session real time
- **`registry.RETRY_INJECTION["WARD-01"]` is backwards for this run.** It says
  "match the attached reference images EXACTLY" — but the reference IS the source
  of the lab-coat defect. Use the custom clause above instead.
- **`drive.py fetch` numbers files `vNN` from a non-collision-safe count.** If files
  arrive out of band you get two `v07`s. `winner` globs `<variant>-*.png` and takes
  the FIRST match — so banking by prefix can silently ingest a KILLED tile. Already
  bit b45 (caught) and b42. Check `ls variants/<beat>/ | sed 's/-.*//' | sort | uniq -d`
  before banking.
- **`count:4` sometimes returns only 3 jobs.** Always record what you actually got.
- **429 rate_limit_reached** if two drivers submit concurrently. Pause ~75s and retry.
- **Never run `integrity.py --rebless`** — owner-only.
- One junk board tile exists: `09db3a5283.png`, a debug probe ingested with prompt
  `test-probe`. Already marked rated=bad / tagged `probe-artifact`. Safe to delete.

## Suggested order on the mini
1. Two input fixes above.
2. Generate the 32 missing beats (~64 credits), judge with rules 1-9, bank winners.
3. Run the 12 corrective re-rolls.
4. Final pass: story-order strip + stats + CHANGELOG entry.
