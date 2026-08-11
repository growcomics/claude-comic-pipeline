---
name: ideator
description: Stage 1 of the production line — turn a seed (a theme, a character, "do something with X", or nothing at all) into a ranked slate of comic concept pitches via a concept tournament scored against a corpus-grounded rubric. Surfaces the top 3 with rationale for the user to pick from, and emits concepts.json (the Ideator→Writer contract). Use when the user wants to "ideate a comic", "give me concepts", "pitch me some comics", "what should we make next", "brainstorm what to build", or asks for new comic ideas grounded in what actually works.
---

# Ideator — concept tournament (Stage 1 of the seven-stage line)

> **STATUS: ENGINE BUILT (2026-08-10).** The tournament runs as a four-step checkpoint harness in `scripts/tournament.py` under one architecture rule: **judgment in Claude, mechanics in Python.** Claude generates the concepts and scores them against the rubric; Python owns everything mechanical — feedstock digestion, the cross-slate dedup memory, schema enforcement, scoring arithmetic, ranking, the flat-slate guard, archival — so the judgment can never skip the contract or fudge the math. Two validated example slates live in `slates/`.

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

## Running the tournament (the four-step harness)

All commands from `skills/ideator/`:

```
1. GENERATION BRIEF                                              (mechanics)
   python3 scripts/tournament.py brief [--seed "..."] [--per-angle 2]
   → prints the brief: the feedstock file list (read them ALL before
     generating), catalog top-series digest, locked roster, and fingerprints
     of every concept in prior slates (the dedup memory). Missing feedstock is
     reported explicitly — the tournament degrades gracefully to corpus-only
     grounding until the analytics flywheel exists.

2. GENERATE                                               (judgment — Claude)
   Read the feedstock files the brief cites. Write a draft slate
   {"seed": ..., "concepts": [...]} with >= per-angle concepts per angle,
   each conforming to references/concept-schema.json. Ground every concept:
   cite findings in corpus_grounding (F1–F6 visual corpus, C1–C6 catalog).
   Do NOT fill scores yet — generation and scoring are separate passes.

   python3 scripts/tournament.py ingest --draft draft.json       (mechanics)
   → per-concept schema conformance, angle quotas, concept_id uniqueness,
     near-dupe detection (vs prior slates AND intra-slate), F1 growth floors,
     cast consistency. Exit 2 with a precise report on failure; fix, re-run.

3. SCORE                                                  (judgment — Claude)
   Read references/rubric.md VERBATIM (canonical-rubric rule — never
   paraphrase) and score every concept 0–5 on all 7 axes, with a
   score_rationale. Be a discerning critic; spread the scores.

   python3 scripts/tournament.py finalize --draft draft.json \
       --out concepts.json [--seed "..."]                        (mechanics)
   → re-runs every ingest check, recomputes cast_size + weighted_total itself
     (Claude's arithmetic is never trusted), ranks, enforces the FLAT-SLATE
     GUARD (weighted-total stdev < 4 or range < 8 = refusal — a slate that
     doesn't discriminate is useless), validates the assembled slate, writes
     concepts.json, auto-archives a copy into slates/ (tomorrow's dedup
     memory), and prints the top-3 table.

4. HUMAN GATE
   Surface the top 3 with per-axis rationale. The user picks (or asks for a
   fresh slate / "more like #2"). NEVER auto-select. Then:
   python3 scripts/tournament.py select --slate concepts.json --concept-id <id>
```

`validate --slate <file>` re-checks any slate (schema + recomputed totals);
`print-contract` dumps a schema-shaped example concept.

---

## I/O contract

**Input** (all optional except the system can run with none):
- `seed` — a theme, character name, phrase, or null ("surprise me").
- `roster` — the locked character roster (names + ref status), so the tournament can prefer cast reuse. Lives in `roster.json` (built 2026-08-10 from the project ref ledgers; the brief reads it automatically). Keep it current as projects bank new casts.
- `corpus_findings` — `research/comic-corpus/synthesis/success-elements.md` conclusions (what works, F1–F6). This is the **ground truth** the rubric scores against.
- `catalog_findings` — `research/comic-corpus/catalog/SYNTHESIS.md` (C1–C6): the full GrowGetter catalog ingested over the WP REST API — the corpus's first popularity/monetization signal (serial legs, engagement leaders, the freemium funnel).
- `analytics` — *(future)* publisher engagement data, once Stage 7 + the flywheel exist. Until then, corpus + catalog findings stand in; the brief reports the degrade explicitly.

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

## Component map (engine built 2026-08-10)

| Piece | State |
|---|---|
| `SKILL.md` (this file) — the workflow + contract | ✅ real |
| `references/concept-schema.json` — the Ideator→Writer contract | ✅ real (unchanged by the engine build — the Writer can rely on it) |
| `references/rubric.md` — corpus-grounded scoring rubric | ✅ real (v1.0) |
| `scripts/tournament.py` — brief / ingest / finalize / select harness | ✅ **ENGINE** — mechanics in Python |
| Concept generation + rubric scoring | ✅ **ENGINE** — judgment in Claude, per the workflow above |
| `roster.json` — locked-character roster feedstock | ✅ real (keep current) |
| `slates/` — archived slates = the dedup memory | ✅ real (auto-appended by finalize) |
| Analytics flywheel feedstock | ⛔ not live — corpus + catalog stand in (brief reports the degrade) |

Where judgment happens, this SKILL is the spec; where mechanics happen, `tournament.py` refuses bad inputs. Neither side trusts the other's promises — that's the design.

---

## Feeds / fed-by

- **Fed by:** `research/comic-corpus/` (the corpus — what works), the locked character roster, and *(future)* publisher analytics.
- **Feeds:** the **Writer** (Stage 2) via `concepts.json`. Build the Writer to read `selected_concept_id` from this artifact.

When this stage matures, update `docs/PRODUCTION-SYSTEM-VISION.md` (Stage 1 status) and `CHANGELOG.md`, per the vision doc's standing instruction.
