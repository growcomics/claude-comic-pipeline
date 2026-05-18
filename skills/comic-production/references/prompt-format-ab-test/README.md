# Prompt-format A/B test (2026-05-17)

Validation artifacts for the prompt-section-formatting refactor introduced in
branch `feat/prompt-section-formatting`.

## What changed

`compose_prompt()` in `scripts/next_panel.py` previously concatenated every
rule's directive into one long unbroken paragraph (space-separated). The new
output emits each directive as a labeled `[SECTION HEADER]\n<body>` block
with blank lines between sections. Same semantic content; image models
tokenize whitespace fine, so this is a presentation refactor only.

## Files

- `old.prompt.txt` — same content as `new.prompt.txt` but with `[LABEL]\n`
  headers stripped and blank lines collapsed to single spaces. Byte-
  equivalent to what the old code path would have produced.
- `new.prompt.txt` — output of the new formatted composer for the same panel.
- `metadata.json` — panel id, camera, refs to attach, lengths.

## How to run the A/B test (user-driven)

The Higgsfield MCP wasn't connected in the session that produced this branch,
so the model couldn't render the actual A/B images itself. To validate
manually:

1. With Higgsfield MCP connected, attach the refs listed in `metadata.json`
   in order (face cards for `lenny` and `carl`, env_anchor for
   `mundy-lab-a`).
2. Submit `old.prompt.txt` to Higgsfield with `nano_banana_flash`, 1k, 3:4,
   count=1.
3. Submit `new.prompt.txt` with identical params.
4. Spot-check: do the two outputs look visually equivalent (same camera,
   same character anchoring, same env)? If yes, the refactor is a no-op on
   model behavior. If the new format somehow drifted output, debug —
   likely a stray whitespace issue or a missing label edge case, not a
   tokenization issue.

Total expected cost: ~$0.10 across two generations.

## Why we have to A/B at all

The user spec for this refactor calls out: "Image models tokenize whitespace
fine, so we're not changing what the model sees in any meaningful way." That
is the working theory, and the addition of `[CHARACTER — L17 ...]` headers
is small relative to the prompt length (+323 chars on a 4351-char baseline,
+7.4%). But "small enough not to drift" isn't the same as "verified not to
drift," so an actual A/B render is the guardrail before we ship the new
format into every future generation.

## Panel chosen

Ultra-Gal Origin, `p01-01` — Page 1 Panel 1, a wide establishing shot. It
fires a manageable subset of rules (L15 beauty, L18 anatomy, L21 ref safety,
L10 render directive, L19 lettering) but skips the heavy tier-build/tier-
reinforcement rules. A good baseline for "does the section formatting
change anything for a typical panel?" If the user wants more coverage, run
a second A/B on a tier-6 stage-change panel (e.g. anywhere `muscle_size_tier=6`
fires L11+L29) where the prompt is much longer and the label density is
higher.
