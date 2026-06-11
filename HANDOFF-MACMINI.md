# HANDOFF — Mac mini session bootstrap (comic pipeline)

You are Claude Code picking up the comic pipeline on this machine. The user will not open a
terminal — **you run every command below yourself** via Bash. Work top to bottom; stop and
report if any step fails. Written 2026-06-11 by the laptop session.

## 1. Sync the repo (source of truth)

```bash
# If the repo exists:
cd ~/Documents/claude-comic-pipeline && git fetch --all --prune && git checkout main && git pull --ff-only origin main && git log --oneline -1
# If it does NOT exist:
git clone git@github.com:growcomics/claude-comic-pipeline.git ~/Documents/claude-comic-pipeline && cd ~/Documents/claude-comic-pipeline && git log --oneline -1
```

Expected HEAD: `6765a8e` or newer. If the clone fails on SSH auth, retry with
`https://github.com/growcomics/claude-comic-pipeline.git`.

## 2. Load the law

If this session did not start inside the repo (so CLAUDE.md isn't auto-loaded), `Read` the
repo's `CLAUDE.md` now and obey it for the rest of the session. Non-negotiables it carries:

- **Local skills ONLY** — never the published `anthropic-skills:comic-production` (it's stale).
- **Generation protocol (MANDATORY)**: every Flow/Higgsfield submit = COMPOSE (`qa/compose.py`,
  the only legal prompt source) → AUDIT (`qa/audit_prompt.py`) → SUBMIT (receipt's attach list,
  each chip verified) → POST-FLIGHT (fresh-context subagent judges vs `qa/judge-rubric.md`) →
  BANK (`qa/bank.py`; refuses anything chainless). **Never freehand or edit a prompt** — the
  only exception is `projects/cheer-ascension/references/bootstrap-prompts.json`, whose
  pre-committed prompts are pasted VERBATIM for the job kinds compose can't express yet.
- Defaults: Nano Banana 2 · x4 · 16:9 · 1K (shows "0 credits"); photoreal DAZ/Iray, NOT 2D;
  `always_clothed: true`; NO background extras; muscle grows, height does NOT; refs carry
  appearance — prompts are pointers + action/camera only.
- Project TEXT commits with a CHANGELOG entry every time; binaries stay out of git; never
  touch `.git.backup-20260512-072853/`.

## 3. Gate status + the bless (READ CAREFULLY)

```bash
cd ~/Documents/claude-comic-pipeline/projects/not-so-supra-man && python3 qa/integrity.py
```

Expect **ALL GATES LOCKED** — the v2 gate upgrades (commit `9bd3390`) await the user's
re-bless. **You are prohibited from running `integrity.py --rebless` on your own initiative.**
The terminal-free approval flow is:

1. Show the user what changed: `git log --oneline f2338cc..main -- projects/not-so-supra-man/qa/`
   plus a one-paragraph summary (costume-state→turnaround mapping, prior-panel check,
   scene-rung enforcement, anti-reference-bleed negatives, progression rule, judge rubric).
2. Ask them plainly: "Approve the rebless?" and wait.
3. ONLY on an explicit yes in this session, run AS THEIR PROXY:
   `python3 qa/integrity.py --rebless --i-am-the-user`
   then commit + push the manifest:
   `git add qa/MANIFEST.sha256 && git commit -m "User re-bless: v2 gates (approved in-session on macmini)" && git push origin main`
4. Tell the user the laptop session needs a `git pull` to unlock too.

If they decline, the chained jobs stay blocked; bootstraps may continue.

## 4. Orient (read these, in order)

1. `projects/cheer-ascension/PROGRESS.md` — the active demo project (build order + status)
2. `projects/cheer-ascension/references/ref-ledger.json` — what's banked, Flow project id
3. `projects/not-so-supra-man/PROGRESS.md` — the 46-page main project (restart v2 state)
4. `skills/comic-production/references/qa-defect-doctrine.md` — D1–D14 + the three laws

State as of this handoff: **Cheer Ascension** is generating in Flow project `d8ff2c7c-7cd4-4daa-9e90-84cfd123f0db`
("Jun 10, 11:31 PM") — face card banked (`12c236a4…`, V2 of 4), t2 body card rendered and
awaiting gate-read/pick, then: field wide → medium → close rungs + shaker prop (bootstraps),
then the 6 chained sheets/pages per `references/turnaround-specs.json` once gates unlock.
**Not-So-Supra-Man** v2 has T9/T6-torn/T6-suit turnarounds banked; next are Dee-Dee/Supraman/
Doomer sheets, then scene ladders, then 46 pages — ALL chained.

## 5. Driving Flow from this machine

- Use Claude-in-Chrome on THIS browser (macmini, deviceId `2a9bd64b-caf7-4f66-9bd4-0a64ab7eb6ee`).
- Flow direct mode: the "Agent" chip on the prompt bar toggles agent mode OFF → the pill
  (model/aspect/count) appears. Verify **Nano Banana 2 · 16:9 · x4** before EVERY submit.
- Attach refs via `+` → asset picker (it resets to the current project each open; verify every
  chip in the preview pane). After attaching, **DOM-verify the chip**: run JS to read the chip
  img's `getMediaUrlRedirect?name=<uuid>` and match it against the intended ledger id.
- Harvest result ids with the same JS pattern (skip `left>1100 || width<150` thumbnails).
- Download picks WITHOUT cookies: navigate a scratch tab to
  `https://labs.google/fx/api/trpc/media.getMediaUrlRedirect?name=<uuid>` — the tab title
  becomes a signed `flow-content.google` URL — then `curl` it to the ledger's disk path.
- NB Pro rate-limits bulk runs; NB2 is unlimited (~40s per x4). Picks are recoverable from
  Flow ids in the ledgers — local PNGs are cache, git is truth for text.

## 6. After every banked item

Update the project's ref-ledger/pages-log (via `bank.py` for chained items; manual ledger
entry marked `"class": "bootstrap"` for bootstrap items, with variant ids + QA notes), update
PROGRESS.md, and commit project text + CHANGELOG entry, then push. The user red-pens via the
Flow Red-Pen extension (`tools/flow-review-extension/`) — its verdict exports are calibration
data for the post-flight judge.
