---
name: ideator
description: Stage 1 of the production line — turn a seed (a theme, a character, "do something with X", or nothing at all) into a ranked slate of comic concept pitches via a concept tournament scored against a corpus-grounded rubric. Surfaces the top 3 with rationale for the user to pick from, and emits concepts.json (the Ideator→Writer contract). Use when the user wants to "ideate a comic", "give me concepts", "pitch me some comics", "what should we make next", "brainstorm what to build", or asks for new comic ideas grounded in what actually works. NOTE: this is a SHELL — the generate-and-score engine is a documented stub awaiting a stronger model; the scaffold, schema, and rubric are real.
---

# Ideator — concept tournament (Stage 1 of the seven-stage line)

> **STATUS: SHELL.** The scaffold, the `concepts.json` contract, and the scoring rubric are real and built to spec. The **tournament engine itself (concept generation + rubric scoring) is a documented stub** in `scripts/tournament.py` — marked `BUILD ME (stronger model)`. Do not pretend the engine runs. Until it's built, ideation is done by Claude reading this SKILL + `references/rubric.md` and producing a slate by hand against the same contract.

This is **Stage 1** of the production-system vision (`docs/PRODUCTION-SYSTEM-VISION.md` §2, §5). It sits at the front of the line:

```
► IDEATOR ► WRITER → STORYBOARD → REFERENCE → PAGE BUILD → REVIEWER → PUBLISHER
  (concept)  (script)
```

Its one job: take a spark (or nothing) and return a **ranked slate of comic concept pitches**, each grounded in what the corpus says actually works — so we build from evidence, not a vacuum. The user picks one; that selected concept becomes the Writer's input.

**Local skill — source of truth is this repo.** Per `CLAUDE.md`, never route comic work through `anthropic-skills:*`. This skill is part of the local pipeline.

---

## When this skill is the right tool

Triggers:
- "ideate a comic" / "give me concepts" / "pitch me some comics"
- "what should we make next?" / "brainstorm what to build"
- "I have a character / theme / seed — what could we do with it?"
- any time the user wants a *menu of concept pitches to choose from* before committing to a script

Distinct from:
- **`story-writers-room`** — that's a freeform brainstorm/critique room for developing ONE idea. The ideator is the upstream *tournament* that produces the slate the user picks from; a chosen concept can then go to the writers room or straight to the Writer.
- **`script-breakdown`** (Stage 3) — consumes a finished script, not a seed.

---

## The concept tournament (the shape)

One-shot ideation loses because the solution space is wide. Instead the ideator runs a **tournament**: generate many concepts from deliberately different starting angles, score each against a corpus-grounded rubric, surface the best.

```
seed (optional) + roster + corpus findings
        │
        ▼
 ┌──────────────── generate N concepts, one batch per ANGLE ────────────────┐
 │  transformation-flavor-first   character-first   setting-first   hook-first│
 └──────────────────────────────────┬───────────────────────────────────────┘
        ▼
 score each concept against references/rubric.md  (7 weighted axes, 0–5)
        ▼
 rank → surface TOP 3 with rationale + score breakdown
        ▼
 HUMAN GATE: user picks 1 of 3  (or "fresh slate" / "more like #2")
        ▼
 emit concepts.json  (full slate + ranking + selected_concept_id)
```

### The four generation angles
Each angle seeds a different region of the idea space so the slate isn't seven variations of one thought:
1. **transformation-flavor-first** — start from the growth mechanic (potion / curse / latent power / tech / rivalry-driven / ambient field) and build a story around the best version of that transformation.
2. **character-first** — start from a **locked character in the roster** (cheap to produce — refs already exist) and ask what transformation story they're owed.
3. **setting-first** — start from a world/location (a city pack we already have, a gym, a lab, a beach) and find the transformation the setting wants.
4. **hook-first** — start from a one-line hook that would stop a scroll, then reverse-engineer the comic that delivers it.

Generate ≥2 concepts per angle (≥8 total) so the tournament has real competition, then rank.

---

## I/O contract

**Input** (all optional except the system can run with none):
- `seed` — a theme, character name, phrase, or null ("surprise me").
- `roster` — the locked character roster (names + ref status), so the tournament can prefer cast reuse. Today this lives across project ref ledgers + character sheets; a consolidated `roster.json` is a future input. Until it exists, pass the known locked characters by hand.
- `corpus_findings` — `research/comic-corpus/synthesis/success-elements.md` conclusions (what works). This is the **ground truth** the rubric scores against.
- `analytics` — *(future)* publisher engagement data, once Stage 7 + the flywheel exist. Until then, corpus findings stand in.

**Output**:
- `concepts.json` — the full ranked slate, conforming to `references/concept-schema.json`. **This is the Ideator→Writer contract** (vision §4). It carries every concept's logline, transformation arc, cast, setting, hook, est. page count, growth-ratio target, why-it'll-perform rationale, and per-axis score breakdown — plus `ranking`, `top3`, and (once the user picks) `selected_concept_id`.
- a chat-surfaced **top-3 with rationale** for the human gate.

The Writer (Stage 2) consumes `concepts.json` → reads `selected_concept_id` → expands that one concept into a panel-ready script.

---

## The rubric (grounded in the corpus, not invented)

Scoring axes live in `references/rubric.md`. They are derived from — and cite — the `comic-corpus` findings (`research/comic-corpus/synthesis/success-elements.md`) and the standing memory directives. The headline alignments:

- **Growth/transformation payoff density** (highest weight) — growth IS the product (`growth-density-mandate`); corpus Finding 1 sets growth-ratio targets by chapter type.
- **Story spine / coherence** (highest weight) — corpus Finding 5: *story is the universal weak axis in the niche (median 2/5) and therefore the single biggest differentiation opportunity.* A concept with a real spine and a paid-off ending is how we win, not just match.
- **Hook, camera/staging potential, cast reuse, novelty, production economy** — the rest, each tied to a finding or directive.

Two **free wins the pipeline already banks** (not scored, but every concept should be designed to exploit them): **baked legible dialogue** (Finding 2 — empty balloons are endemic in the corpus; lettering alone beats the median) and **face-led growth ECUs** (Finding 3). See the rubric for how each axis maps to a finding.

---

## Human gate

The user picks **1 of the top 3**, or asks for a fresh slate / a variation on one. This is a high-leverage, low-effort approval — the cheapest possible point to steer the whole production. Never auto-select; surface and wait.

---

## What's real vs stubbed (read before you "run" this)

| Piece | State |
|---|---|
| `SKILL.md` (this file) — the workflow + contract | ✅ real |
| `references/concept-schema.json` — the Ideator→Writer contract | ✅ real |
| `references/rubric.md` — corpus-grounded scoring rubric | ✅ real |
| `scripts/tournament.py` — feedstock loading + JSON emit + schema validate | ✅ real plumbing |
| `scripts/tournament.py` — `generate_concepts()` + `score_concept()` | ⛔ **STUB** — `BUILD ME (stronger model)` |

Until the engine lands, produce the slate **by hand**: read `references/rubric.md`, generate ≥2 concepts per angle, score honestly against the axes, write a schema-valid `concepts.json`, surface the top 3. The contract is what matters — keep it stable so the engine can drop in behind it without breaking the Writer.

---

## Feeds / fed-by

- **Fed by:** `research/comic-corpus/` (the corpus — what works), the locked character roster, and *(future)* publisher analytics.
- **Feeds:** the **Writer** (Stage 2) via `concepts.json`. Build the Writer to read `selected_concept_id` from this artifact.

When this stage matures, update `docs/PRODUCTION-SYSTEM-VISION.md` (Stage 1 status) and `CHANGELOG.md`, per the vision doc's standing instruction.
