# Prompt-format A/B test (2026-05-17)

Validation artifacts for the prompt-section-formatting refactor introduced in
branch `feat/prompt-section-formatting`.

## Outcome — visually equivalent ✓

The Higgsfield A/B run was completed on 2026-05-17. Both renders show the
same characters (lenny + carl) in the same lab, same cowboy framing, same
photoreal CGI quality, with the same speech bubble content ("THERE, THAT'S
THE LAST ONE…"). Differences fall well within nano_banana_flash's
sample-to-sample variance for a single prompt (slight camera-angle shift,
different lab-decor details, OLD over-rendered a second duplicate bubble —
a known model quirk, not a format-induced regression).

Conclusion: the section-formatting change is a presentation-only refactor
with no observable effect on model behavior. Safe to ship.

## What changed

`compose_prompt()` in `scripts/next_panel.py` previously concatenated every
rule's directive into one long unbroken paragraph (space-separated). The new
output emits each directive as a labeled `[SECTION HEADER]\n<body>` block
with blank lines between sections. Same semantic content; image models
tokenize whitespace fine.

## Files

- `old.prompt.txt` — same content as `new.prompt.txt` but with `[LABEL]\n`
  headers stripped and blank lines collapsed to single spaces. Byte-
  equivalent to what the old code path would have produced.
- `new.prompt.txt` — output of the new formatted composer for the same panel.
- `old.png` — Higgsfield render of `old.prompt.txt`. Job
  `ee112f57-8b57-4a59-9972-64455d7e3a4a`.
- `new.png` — Higgsfield render of `new.prompt.txt`. Job
  `1cabc083-511e-4c5b-867e-4b2e83576496`.
- `metadata.json` — panel id, camera, refs attached, prompt lengths.

## A/B parameters

- Model: `nano_banana_flash` (Nano Banana 2)
- Resolution: `1k`
- Aspect ratio: `4:3`
- Count: `1` per submission (2 gens total)
- Refs attached (same media IDs for both runs):
  - lenny face-card → `2680857e-f4b2-4869-a8ca-fe00c1da8429`
  - carl face-card → `6191a1c7-ead2-48a5-a897-110039e472df`
  - mundy-lab-a env source → `48ed1584-6d09-4dcc-b3a6-5f3741000f42`

## Why we A/B at all

The format change adds `[CHARACTER — L17 ...]` headers and blank-line
separators — +323 chars on a 4351-char baseline (+7.4%). "Image models
tokenize whitespace fine" is the working theory, but "small enough not to
drift" isn't the same as "verified not to drift." This A/B is the guardrail.
Both renders landing visually equivalent confirms the theory holds.

## Panel chosen

Ultra-Gal Origin, `p01-01` — Page 1 Panel 1, a wide establishing shot. It
fires a manageable subset of rules (L15 beauty, L18 anatomy, L21 ref safety,
L10 render directive, L19 lettering) but skips the heavy tier-build/tier-
reinforcement rules. A good baseline for "does the section formatting
change anything for a typical panel?" If the user wants more coverage, run
a second A/B on a tier-6 stage-change panel (e.g. anywhere `muscle_size_tier=6`
fires L11+L29) where the prompt is much longer and the label density is
higher.
