# CHARTER.md addition — nightly bakeoff driver duty (DRAFT)

Drafted 2026-08-09 by the laptop session. **This file is a paste-source, not
the charter itself** — the night-shift worker's CHARTER.md lives on the mac
mini. Owner (or the mini's day session): paste the block below into the mini's
CHARTER.md under the nightly duties, adjusting priority order to taste. Delete
nothing here; this draft stays in the repo as the record of what was proposed.

---

## Duty: Bakeoff generation driver (nightly)

Every nightly run, after existing charter priorities:

1. **Sync + check the queue.** `cd ~/Documents/claude-comic-pipeline && git
   pull --ff-only`, then look for pending beat sheets at
   `runners/bakeoff/queue/*.json`. None pending → note "bakeoff queue empty"
   in the night report and move on. Before first use, read
   `runners/bakeoff/README.md` and `runners/bakeoff/queue/README.md`.
2. **Drain oldest-first.** Per sheet, follow HANDOFF-MACMINI.md §6 exactly:
   `bakeoff.py plan` → drive `jobsheet.json` on the sheet's backend
   (`higgsfield-mcp`: this machine's MCP session, nano_banana_flash · 1k ·
   count=1 sequential, check credits first; `flow-chrome`: this machine's
   growcomics Flow session, confirm account + model pill every submit;
   `flow-manual`: skip, it's the owner's) → `collect` → `judge` → `retry`
   loop until no beat is `retry` → `select` → `stats --credits <spent>`.
3. **Budget.** Honor the sheet's `creditCap`; default 100 paid generations
   per night total. Cap hit → stop driving, leave the run resumable, report.
4. **Stage B sanity.** Once per night before the first `judge`, verify
   `claude -p "say ok" --model sonnet` works. If not, write
   `<run>/stageb-verdicts.json` via a fresh Sonnet subagent instead (see
   HANDOFF §6) — never rank variants in main context.
5. **Close out.** Per completed sheet: `git mv` it to `queue/done/`
   (`failed/` + halt note only if zero beats cleared), commit run-state text
   with a dated CHANGELOG.md entry at top, push. Include in the night report:
   beats cleared / flagged-to-human count / clean-variant rate / credits
   spent (the yield numbers from `stats`).
6. **Hard limits.** Never touch `.git.backup-*`. Never modify `projects/*/qa`
   gate scripts. Flagged beats go to the human queue (`bakeoff,needs-human`)
   — never silently shipped, never re-judged past the retry cap. An
   owner-accepted panel in a beat's group is never overridden.
