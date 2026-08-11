# HANDOFF — Mac mini session bootstrap (comic pipeline)

> ## 🔴 TOP PRIORITY (owner-directed 2026-08-11 ~07:50 PDT) — READ FIRST
> Owner, leaving the laptop: *"I need you to continue driving this on the Mac Mini somehow. It should
> get all the way to completion on Mac Mini. Don't ask me stuff. Also… everything needs to be nano
> banana 2 lite."*
>
> **The job:** finish **`projects/not-so-supra-man/`** — go read
> **`projects/not-so-supra-man/RUN-NOW.md`**, which is a complete self-contained runbook (state,
> remaining work in order, the proven Flow driving method, the verification discipline, and the
> bust-landing correction loop). Do not re-derive any of it.
>
> **Model is `Nano Banana 2 Lite` on every submit — no exceptions.** Re-verify the pill every time;
> it resets on reload.
>
> Status at handoff: 5 of 6 character turnarounds banked with full chains (`qa/verify_chain.py` → 5).
> Next: `dana-t4-blouse` → `dana-t9-ANCHOR-SWAP` (3 passes) → scene ladders → 29 pages → letter + PDF.
>
> ⚠️ **This work is NOT for the sandboxed night-shift worker.** `~/Documents/night-shift/CHARTER.md`
> guardrail 3 forbids Flow generation calls and guardrail 7 forbids pushing to remotes. The owner's
> instruction above overrides those *for this task only*; see `docs/CHARTER-ADDENDUM-supra-man.md`.
> Every other night-shift guardrail stays in force.


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

## 6. Nightly bakeoff driver duty (added 2026-08-09)

The bakeoff lane (`runners/bakeoff/` — read its README.md first) is the new
over-generate→judge→retry→select pipeline. **This machine is its generation
DRIVER**: every night-shift run, after charter priorities, drain the queue.

**Queue contract**: pending beat sheets live at `runners/bakeoff/queue/*.json`
(see `runners/bakeoff/queue/README.md`). Oldest first. On completion, `git mv`
the sheet to `queue/done/`; on unrecoverable halt, to `queue/failed/` with a
`<sheet>.halt.txt` note.

**Per sheet, the loop is:**

```bash
cd ~/Documents/claude-comic-pipeline && git pull --ff-only
python3 runners/bakeoff/bakeoff.py plan --sheet runners/bakeoff/queue/<sheet>.json
# -> runs/bo-.../jobsheet.json — now DRIVE it (see below)
python3 runners/bakeoff/bakeoff.py collect --run runners/bakeoff/runs/bo-...
python3 runners/bakeoff/bakeoff.py judge   --run ...
python3 runners/bakeoff/bakeoff.py retry   --run ...
# drive any new jobsheet entries, then collect+judge again, until no beat is 'retry'
python3 runners/bakeoff/bakeoff.py select  --run ...
python3 runners/bakeoff/bakeoff.py stats   --run ... --credits <paid gens spent>
```

**Driving the jobsheet** — per undone entry, attach `anchors[]` + `refs[]` as
images, submit `prompt` (+`style`) as text, save results to the `out[]` paths:

- `backend: higgsfield-mcp` — use THIS machine's Higgsfield MCP session.
  `nano_banana_flash`, `1k`, `count:1`, submitted **sequentially** `count`
  times per entry (house rule: 1 per paid submit). **Check credits before
  starting**; PAID.
- `backend: flow-chrome` — use THIS machine's growcomics Flow session via
  Claude-in-Chrome. Confirm the active account is **growcomics** before any
  submit (`skills/comic-production/references/flow-accounts.md`), and verify
  the model pill every submit.
- `backend: flow-manual` — not yours; skip the sheet (leave it pending).

**Credit cap**: honor the sheet's `"creditCap"`; default **100 paid
generations per night** across all sheets (Flow gens don't count). If the cap
hits mid-run, stop driving, leave state resumable (every subcommand is
idempotent), and note it in the wrap-up — do NOT move the sheet to `failed/`
unless zero beats cleared.

**Stage B judge prefers the `claude` CLI**: `judge` shells out to
`claude -p ... --model sonnet`. This machine has a live claude CLI, so it
should work — **verify once before the first judge of the night**
(`claude -p "say ok" --model sonnet`). If the CLI errors, `judge` still
completes: it falls back to first-clean with a logged note, and it checks
`<run>/stageb-verdicts.json` first — so the better degraded path is to rank
survivors yourself via a FRESH Sonnet subagent (rubrics by path, verbatim —
mirror `judge.py`'s prompt) and write that file before running `judge`.
Never rank in your own main context — the fresh-judge rule holds.

**Wrap-up per sheet**: `git mv` the sheet to `queue/done/`, commit run-state
text + the sheet move **with a dated CHANGELOG.md entry at the top** (per repo
law), push. Flagged beats (`bakeoff,needs-human`) are expected output, not
failures — mention their count in the night report.

**Hard limits**: never touch `.git.backup-*`; never modify `projects/*/qa`
gate scripts (bakeoff's judge is separate from the chained-protocol gates and
does not replace them).

## 7. After every banked item

Update the project's ref-ledger/pages-log (via `bank.py` for chained items; manual ledger
entry marked `"class": "bootstrap"` for bootstrap items, with variant ids + QA notes), update
PROGRESS.md, and commit project text + CHANGELOG entry, then push. The user red-pens via the
Flow Red-Pen extension (`tools/flow-review-extension/`) — its verdict exports are calibration
data for the post-flight judge.
