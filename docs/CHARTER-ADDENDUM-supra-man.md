# Charter addendum — "Not So Supra... Man" completion run (mac mini)

**Status:** owner-directed, scoped, time-limited. Recorded by the laptop session 2026-08-11 ~07:50 PDT.

## Why this exists

`~/Documents/night-shift/CHARTER.md` carries two guardrails that block this job:

- **Guardrail 3 — "No generation-credit spend. No Higgsfield/Flow generation calls."**
- **Guardrail 7 — "Never push to remotes."**

Those exist to stop an unsupervised worker spending money and mutating shared state. The owner gave a
direct, current instruction that overrides them **for this one task**:

> *"I'm leaving here soon, so I need you to continue driving this on the Mac Mini somehow. It should
> get all the way to completion on Mac Mini. Don't ask me stuff. Also, I think the generations you're
> doing are using the wrong model. everything needs to be nano banana 2 lite."*

## What is authorized

1. **Flow image generation for `projects/not-so-supra-man/` only**, model **Nano Banana 2 Lite**,
   via the mandatory `qa/` chain (compose → audit → submit → post-flight → bank). No freehand prompts.
2. **Pushing `feat/comic-corpus`** for this project's text + CHANGELOG, so progress survives.

## What is NOT authorized (all other guardrails stand)

- No writes to any live server, no deploys, no `bridge.php` claim/ingest/write/done.
- No posting or publishing anywhere.
- No purchases, no account changes.
- No `rm` of project files — move to `trash/`.
- No running `qa/integrity.py --rebless` (owner-only; report gate bugs with a diff instead).
- No touching `.git.backup-*`, no force-push, no history rewrite.

## Cost guard — read before bulk work

NB2 Lite renders at **0 credits on the ULTRA account** (`marrtrobinson2312`, the laptop). The mac
mini is signed into **`growcomics`, which is Plus** — Lite may NOT be free there. Before firing a
long run on the mini:

1. Confirm the active account (`/fx/api/auth/session`).
2. Open the model pill and read the **"Generating will use N credits"** line.
3. If N > 0: generate the **remaining character sheets only** (small, high value), then STOP and put
   the 29-page run in the outbox as `needs-human` with the credit cost per submit. Do not silently
   drain the balance — the owner's standing guardrail is about not spending, and they authorized the
   work, not the spend.
4. If N == 0: proceed to completion as instructed.

## Definition of done

`projects/not-so-supra-man/` reaches: all character turnarounds banked → scene ladders banked →
all 46 pages banked with chains → lettered via `scripts/letter_pages.py` → final PDF assembled.
`python3 qa/verify_chain.py` should show every new entry carrying a chain.
