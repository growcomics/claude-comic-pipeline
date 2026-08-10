# Bakeoff queue — beat-sheet drop location

This directory is the agreed handoff point between beat-sheet authors (laptop
session, studio, owner) and the generation DRIVER (the night-shift worker on
the mac mini).

## Contract

- **Pending** — any `*.json` file directly in this directory is a pending beat
  sheet. It must validate against `../beatsheet.schema.json`. Drop it here,
  commit, push. Filenames: `<project>-<slug>.json` (e.g. `cinder-ch3-beats.json`).
- **Claim + completion** — the driver processes pending sheets oldest-first
  (by git commit date, falling back to mtime). After `select` + `stats`
  complete, the driver `git mv`s the sheet to `done/` in the same commit as its
  CHANGELOG entry — the move is the claim/completion record. Sheets that halt
  unrecoverably (backend down, schema invalid, credit cap hit before any beat
  cleared) move to `failed/` with a `<sheet>.halt.txt` note beside them.
- **One driver** — only the mini drains this queue. Other sessions may run
  bakeoff.py manually on sheets OUTSIDE this directory; anything placed here is
  the mini's to claim.
- **Backend field** — `"backend"` in the sheet picks the driver mode:
  `higgsfield-mcp` (paid, mini's MCP session, nano_banana_flash 1k count=1
  sequential), `flow-chrome` (free, mini's growcomics Flow session), or
  `flow-manual` (driver skips it; the jobsheet is for the owner).
- **Credit cap** — a sheet may set a top-level `"creditCap": <int>` (max paid
  generations including retries). Absent that, the driver's nightly default cap
  applies (see HANDOFF-MACMINI.md §7).

Run artifacts land in `../runs/bo-*/` as usual; this directory holds only the
sheets themselves.
