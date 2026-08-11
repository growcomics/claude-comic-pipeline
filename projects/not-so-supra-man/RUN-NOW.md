# ▶ RUN NOW — "Not So Supra... Man" 46-page build (gates UNLOCKED 2026-08-10 22:54 PDT)

Owner approved the gate re-bless **in-session**; the mandatory chain is OPEN. Any mac-mini
session that pulls this: **resume the 46-page generation now.** Written from the laptop.

## 0. Confirm unlock
```bash
cd ~/Documents/claude-comic-pipeline && git pull --ff-only
cd projects/not-so-supra-man && python3 qa/integrity.py   # must print: gates intact ✓ (fingerprint 49197e3f…)
```

## 1. Run settings (owner-set)
- **MODEL: Nano Banana 2 Lite** — owner's pick, fastest generator. Verify the Flow pill reads
  **NB2 Lite** before EVERY submit (it resets on reload/clear). x4 variants; aspect per shot.
- **ACCOUNT: growcomics** (this mini). Confirm the active Flow account before any submit/upload/download.

## 2. Refs — banked and ready (don't regenerate what's locked)
- Ledger: `dana-lane` {face, body, turnaround_t9, turnaround_t6_torn, turnaround_t6_suit};
  `supraman` / `dee-dee` / `dex-doomer` {face, body}.
- **Dee-Dee T8 (Destroya)**: `qa/receipts/sheet_deedee-t8-destroya.{receipt.json,audit-pass}` exist but
  it is **NOT yet banked**. Post-flight-judge it, then `python3 qa/bank.py --job sheet:deedee-t8-destroya
  --flow-id <uuid> --disk references/characters/dee-dee/turnaround-t8.png --ledger-key dee-dee.turnaround_t8`
  BEFORE any Destroya page (p22-27, p31-46). Same for scene-ladder rungs a page calls for.

## 3. The chain — every page, NO freehand (CLAUDE.md law)
`pages-log.json`: **29 pending** (the 17 "done" are stale v1 — supersede per restart-v2). Per pending page:
```bash
python3 qa/compose.py --job page:<panel>                                  # ONLY legal prompt source
python3 qa/audit_prompt.py --receipt qa/receipts/page_<panel>.receipt.json --prompt-file /tmp/p.txt
# SUBMIT in Flow: attach EXACTLY the receipt's list (DOM-verify each chip vs the ledger id), paste composed prompt
# POST-FLIGHT: FRESH-context subagent judges the pick vs the qa judge rubric -> qa/receipts/page_<panel>.verdict.json
python3 qa/bank.py --job page:<panel> --flow-id <uuid> --disk pages/panels/<panel>.png
```
NSFW pages (e.g. p13 chest, p41 tier-9 chest): soften-and-retry, coverage intact, drop cleavage words.
Tier-9 Dana (p38-46): attach the `lana` anchor + run the 4-axis no-downsize gate.

## 4. Make it watchable — owner is watching
- **Post the Flow project URL into `PROGRESS.md` the instant you open/create the run's project.** The
  owner explicitly wants the live watch link; the laptop is polling PROGRESS.md for it.
- **Bring the dashboard back up on this mini** — the project view at
  `resedas-mac-mini.tailf37470.ts.net:8765` is currently DOWN (mini reachable, nothing serving that port).
  Start the dashboard server so it auto-discovers `projects/` again.

## 5. After each bank
`bank.py` writes the log; update `PROGRESS.md`, commit project TEXT + a dated `CHANGELOG.md` entry, push.
Never touch `.git.backup-*`; never edit `qa/` gate scripts (re-locks ALL gates — owner-only re-bless).
