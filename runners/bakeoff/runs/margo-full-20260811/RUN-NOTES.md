# margo-full production run — protocol (compaction-resilient; re-read me after any context loss)

Owner directive 2026-08-12: produce the 86-beat margo-full comic (sheet:
`runners/bakeoff/margo-full-beats.json`, script: `projects/margo-full/SCRIPT.md`)
onto studio board **margo-full** (https://3dmusclecomics.com/studio/review.php?p=margo-full).

## Generation (Higgsfield MCP, this Claude session is the driver)
- Model `nano_banana_2_lite`, aspect 3:4, ONE `count:4` call per roll (proven distinct);
  connective beats = 2 rolls (8 variants) single round; payoff beats (beatKind=payoff) =
  3 rolls (12) + a refinement round (refinements may change structural choices).
- Append a distinct "COMPOSITION VARIANT: ..." line on roll 2/3 to avoid cross-call dupes.
- Prompt = beat's `fullPrompt` from the sheet VERBATIM (includes L19 lettering + stage-aware style).
- Medias (role `image_references`):
  margo=f7c7145e-85ed-4d0f-aada-d399bea568db, kress=9e240914-e0a6-42a2-9d12-f4cc43a97537,
  env-lab=9838c9cb-1848-4f2a-bdbe-f5f4c548ddf7, env-gym=3076de26-aaa7-4d7a-a8ee-dfbc6ac3be4a,
  investors=c4c0edc0-38f6-4d04-b79c-139227b23fa0.
- Beats with `anchors:[{winner:bXX}]` ALSO attach that beat's winner JOB ID as a media
  (job ids are valid media values) — stage identity anchors: b17→s2, b38→s3, b58→s4, b72/b74→s5.
- Waves (anchor deps): A=b01..b17, B=b18..b38, C=b39..b58, D=b59..b71b, E=b72..b76.
- NSFW block: reframe ×2 then skip the variant. 429: pause ~30s.
- Cost: 1 credit per count=4 call (~0.25/img). Started at balance 5617.06. Cap ~900 lite gens;
  pause + report if PAID-model spend would exceed ~200 credits (lite spend ≈200cr total is expected).

## Bookkeeping (`drive.py` in this dir)
- After each roll: `python3 drive.py record <beat> <round> <job_id>...`
- Poll with jobs_wait (12 max/call), then `python3 drive.py fetch <beat> <job> <url>` per result.
- `python3 drive.py sheet <beat>...` → sheets/<beat>.jpg contact sheet (Haiku triage input).
- `python3 drive.py pair <beat> v01 v05 ...` → sheets/<beat>-final.jpg (Sonnet ranking input).
- `python3 drive.py winner <beat> <variant> --notes "judge notes"` → ingests to board margo-full,
  accepted=true rating=good tags bakeoff,judge-pick + annotate note.
- `python3 drive.py status` for the rollup. State: state.json (never re-judge a judged image).

## Judging (SPOTTER MODE — NO image reads in main context, zero exceptions)
- Tier 1 Haiku subagent (model:"haiku"): reads sheets/<beat>.jpg (8-12 thumbs), grades tiles:
  extra people, blank-or-garbled bubble text, coverage break, gross anatomy, WARD-07
  skin-fabric gradient, wardrobe-state vs the beat's wardrobe line; returns keep/cull per tile.
  Batch 3-4 beats per agent. ≤1 sheet-read per beat.
- Tier 2 Sonnet subagent: ranks the 2-4 survivors from the -final.jpg composite; checks bubble
  text EXACTLY vs the beat's dialogue lines (LET-01 blank / LET-02 garbled = kill); vitality
  axes (camera/composition first, expression; body scale vs stage); ≤2 Sonnet reads per beat
  (composite rank + full-res winner confirm on variants/<beat>/<vNN>-*.png).
- Zero-clean beat → re-roll with registry.RETRY_INJECTION correctives (runners/bakeoff/registry.py),
  max 2 retries, then flag needs-human via bridge do=flag.
- Size ladder: if a growth/payoff beat under-shoots scale, re-roll with escalated BODY language.

## Checkpoints
- Ingest winners AS THEY ARE ACCEPTED (owner watches the board fill), story order.
- Commit + push every ~20 beats with CHANGELOG entries (re-pull first).
- Wrap: story-order contact strips → /tmp/dr/margo-full-strip-N.jpg; stats (per-stage clean
  rates, ladder usage, text-defect rate, spend); What's New entry (updates.json); final report
  with board link + per-act summary + commit hashes.
