# Alignment: studio/posting.php (the board) vs. skills/publisher (this skill)

_Two halves of the same never-post doctrine. Neither posts; humans fire. This note says who
does what and how they hand off, so the two don't grow overlapping features._

## What posting.php already does (the STATUS side)

The 🗓 posting board (LIVE at `https://3dmusclecomics.com/studio/posting.php`, state in
server-side `studio/data/posting.json`, gitignored live data):

- **Queue lanes** — FAF (next-4-Fridays fill-me slots), Monthly comic (per-property grid,
  current + next month), Side content, plus archive.
- **Per-platform chips** — `site / patreon / deviantart / twitter / instagram`, each cycling
  `todo → scheduled → posted → n/a` by hand.
- **🔒 locked & loaded** — an item glows when marked *ready* and every platform is armed.
  That state is the board's whole point: the owner sees what's ready to fire at a glance.
- **Art upload onto the card** (files only), Patreon member-count strip (patreon-sync cache),
  studio-session or bridge-key auth.
- **What it deliberately does NOT do:** post anything, generate captions, know about page
  files, crops, site manifests, or per-comic records.

## What this skill adds (the PREP side)

Everything a board item needs to actually become "ready", produced mechanically per comic:

- `CHECKLIST.md` — the ordered walk (site → patreon → deviantart → twitter → instagram; same
  keys as the chips, on purpose).
- `captions/<platform>.md` — the text the human pastes when firing each chip.
- `crop-specs.json` — which image, what dimensions, per platform (specs, not renders, in v1).
- `site-apply-notes.md` — the site half, mapped to the property's runbook
  (`comic-platform/docs/PUBLISH-A-COMIC.md` or the 3dmc admin CMS).
- `posted.template.json` → `posting/posted.json` — the durable per-comic record (the board's
  chip states are live-server ops state; `posted.json` is the in-repo, per-project history
  with proof URLs — they answer different questions and both stay).
- `analytics/engagement-stub.json` — the flywheel landing pad the board has no concept of.
- `scripts/board_item.py` — files the board card itself FROM the bundle (MANIFEST.json →
  title / Monthly-comic lane / slot; chips arrive server-initialized `todo`). Dry-run by
  default; the live write is a separate per-action owner-approved act
  (`--execute --approved-by`), receipted at `posting/board-item.json`. It reads live state
  first (`post/index.php?do=state` — live is truth per the deploy-clobber hazard) and its
  only verbs are `add`/`update`, so chip state is unreachable from it.

## The handoff (comic release, end to end)

1. Reviewer finishes → **this skill** prepares `posting/bundle/` and STOPS.
2. Human — or an approved session running `scripts/board_item.py` (dry-run first, then
   `--execute --approved-by "<owner ok>"` once the owner approves that run) — creates the
   board item in the property's Monthly-comic lane. This realizes the board's own
   "book done → board item" NEXT-candidate, fed from the bundle's MANIFEST.json.
3. Human walks `CHECKLIST.md`: fires each platform using the bundle's captions/crops, flips
   the matching **chip** to `posted` as they go, pastes the live URL into the checklist.
4. All chips resolved → item is done on the board; human fills `posted.template.json` → saves
   as `posting/posted.json` (build-comic's stage-complete sentinel), commits, and records the
   syndication-ledger entries on comic-platform (proof URLs).
5. +7d / +30d: engagement captures append to the stub per `analytics-capture.md`.

## Division-of-labor rules

- Caption/crop/checklist logic lives HERE, never in posting.php — the board stays a thin
  status surface (it's live-server PHP under the concurrent-deploy-clobber hazard; the less it
  knows, the less it drifts).
- Chip states live on the BOARD, never mirrored into the bundle — the bundle records what to
  do; `posted.json` records what happened; the board shows where things stand right now.
  (`board_item.py` keeps this literal: `add`/`update` are its only verbs, so it cannot reach
  chip state — posting.php itself initializes a new card's chips to `todo`.)
- If the board ever grows a "pull bundle" feature (fetch a project's CHECKLIST/captions via
  bridge key), it reads the committed bundle — the skill's output format is the contract.
