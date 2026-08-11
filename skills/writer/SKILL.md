---
name: writer
description: Stage 2 of the production line — expand ONE selected comic concept (from the ideator's concepts.json, or a hand-written pitch) into a full panel-ready script in the exact format script-breakdown consumes. Pipeline-aware writing: it pre-bakes growth-sequence order, escalation devices, growth-density targets, tier curves, transformation decomposition, L12 close-framed dialogue, L13 per-speaker splits, and L34 staging opportunities so Stage 3 drops the script straight into a shotlist. Use when the user wants to "write the script", "expand this concept", "script this pitch", "turn this concept into a script", "write chapter N from the pitch", or has a selected concept and wants the full script. NOT for breaking down an existing script (that's script-breakdown) and NOT for brainstorming premises (that's ideator / story-writers-room).
---

# Writer — pipeline-aware scriptwriting (Stage 2 of the seven-stage line)

This is **Stage 2** of the production-system vision (`docs/PRODUCTION-SYSTEM-VISION.md` §2, §5):

```
  IDEATOR ► WRITER ► STORYBOARD → REFERENCE → PAGE BUILD → REVIEWER → PUBLISHER
  (concept)  (script)  (shotlist)
```

Its one job: take **one selected concept** and expand it into a **complete, panel-ready script** that `script-breakdown` (Stage 3) digests with zero reformatting and zero invention. The script is the last cheap artifact in the line — re-writing a page here costs nothing; re-generating a page after Stage 5 costs credits. So the writer front-loads every decision the pipeline is opinionated about.

**Local skill — source of truth is this repo.** Per `CLAUDE.md`, never route comic work through `anthropic-skills:*`.

---

## I/O contract (the whole point)

**Input** — one of:
1. `concepts.json` conforming to `skills/ideator/references/concept-schema.json`, with `selected_concept_id` set. The writer expands **that concept only** — the slate's losers are dead.
2. A hand-written concept (prose pitch or a single concept object). Map it onto the same fields (logline, premise, transformation {flavor, trigger, arc, peak_state, tier_curve}, cast, setting, hook, est_page_count, chapter_type) before writing; ask for anything high-stakes that's missing rather than inventing it.

**Output** — `script.md` at the project root, in the format specified by **`references/script-format.md`** (read it before writing — it IS the Writer→Storyboard contract, vision §4). Page → panel beats, dialogue, transformation decomposition, tier curve, story spine, escalation devices — the same shape as the hand-fed scripts the pipeline already digests (Ultra-Gal lineage), plus the structured annotations that make Stage 3 mechanical.

**Consumer**: `skills/script-breakdown/SKILL.md`. Its input expectations are this skill's output contract. Everything the script declares in its header (style, location strategy, transformation metadata, tier curve, story spine) pre-answers script-breakdown's Step 0 questionnaire so the user confirms once instead of being re-interviewed.

---

## When this skill is the right tool

- "Write the script" / "expand this concept" / "script this pitch"
- "Turn concept #2 into a full script"
- "Write chapter 1 from the selected concept"
- A `concepts.json` exists with `selected_concept_id` set and the next step is a script

Distinct from:
- **`ideator`** (Stage 1) — produces the concept slate. If no concept is selected yet, run that first (or ask the user to pick).
- **`script-breakdown`** (Stage 3) — consumes a finished script. If the user already has a script, go there.
- **`story-writers-room`** — freeform develop/critique of one idea. A concept can detour there, then come back here.
- **`studio/gribble.php`** — the Studio's Gribble-voice script generator (server-side, headless-capable). See `references/gribble-alignment.md` for what this skill reuses from it vs does differently. If the user asks for "a Gribble script", that page is the tool; this skill is the *pipeline's* writer.

---

## The workflow

### 0. Load the concept + the craft

1. Read the concept (`concepts.json` → `selected_concept_id`, or the hand-written pitch).
2. Read **`references/craft-digest.md`** — the compressed ruleset of everything the pipeline is opinionated about (growth order, escalation devices, density targets, L12/L13/L34/L35, always-clothed, no-extras, per-type conventions). It cites the canonical files; when in doubt, follow the citation.
3. Read **`references/script-format.md`** — the output contract.
4. Pick the matching beat-sheet template from `templates/` by transformation type (`fmg` / `be` / `bg` / `mmg` — per `production-briefing`'s type table; `mixed` composes them in breasts → glutes → muscles order).

### 1. Poll the high-stakes choices (per `feedback_poll_on_high_stakes`)

Before writing, surface a tight multiple-choice poll for anything the concept doesn't already pin down:

```
== Writer setup ==
W1. Tone/voice?  a) triumphant-playful (house default)  b) camp/comedy
                 c) dominant/menacing (Gribble-shaped)   d) sensual-slow-burn
W2. Page count?  a) <concept's est_page_count> (default)  b) other
W3. Tier curve?  a) <concept's tier_curve> (default)      b) other  (start→end, lineup tiers)
W4. Ending?      a) landed (this chapter answers its own want)  b) cliffhanger (needs a hook)
```

Defaults come from the concept — never contradict a field the concept pins (`feedback_dont_invent_state_changes`: the tier curve and transformation flavor are the concept's; the writer may *place* the growth, not re-invent it). **Autonomous mode** (no user available): take the defaults, record every assumption in the script header's `NOTES:` block, and surface them at the human gate.

### 2. Structural pre-plan (the skeleton before any prose)

Fill in the chosen template. This is where the pipeline-awareness happens — lock the numbers first, write words second:

1. **Chapter type → growth-page target** (`craft-digest.md` §2): transformation ≥60%, climax ≥70%, origin/mixed ~45–55%, action ≥30% floor. Count your planned pages against it *before* writing.
2. **Place the growth runs**: first growth page inside the first ~15–20% of the script; **≥2 separate growth scenes, each 3+ growth panels** (`feedback_growgetter_size_and_growth_scenes`), escalating — each run lands bigger than the last; final escalation at ~80–90%.
3. **Tier curve**: map the concept's `start→end` onto the runs. Monotonic non-decreasing, never exceeding the declared end. Peak lands in the final scene.
4. **Per-scene decomposition**: each growth scene gets setup beat(s) → body-region beats in **breasts → glutes → muscles order** (`posing-and-expressions.md`) → reveal. Pick the regions the transformation type actually changes (template lists them).
5. **Devices**: ≥2 escalation devices per scene from `escalation-devices.md`'s ranked menu (more for the climax). Name them in the scene declaration; reflect them in the beats.
6. **Story spine**: want / obstacle / cost, promise page, payoff page, ending (landed or cliffhanger+hook). The corpus's universal weakness is story (Finding 5) — this is the differentiation axis, weight it like it.
7. **Staging + camera opportunities**: mark which beats are L34 set-pieces (tension-block confrontations, depth-staged reveals, size-comparison gauges) and which pages earn a splash (the Gribble grid-break: the full-page image IS the transformation device — see `references/gribble-alignment.md`).
8. **Situation registers (L39)**: name each beat's dramatic function with `[situation:]` — required on every 2+-character panel; budget multi-character `showcase`/`celebratory` to ~3 per chapter (`craft-digest.md` §11).

### 3. Write the script

Follow `references/script-format.md` exactly. While writing:

- **Action** lines: present tense, 1–2 sentences, one clear action (~18-word target, per the Gribble panel-economy numbers). Describe what's *seen*.
- **Dialogue**: ≤25 words per balloon; never ≥3 on-screen lines from ≥2 speakers on one panel (L13 — split into per-speaker panels); dialogue beats get close framing (L12 — mcu/medium or tighter); ~1 panel in 5 silent.
- **Expression**: name the emotion mechanically on every beat that has a face (`feedback_expression_intensity`, L35) — "eyes blown wide, mouth open in overwhelmed gasp", not "surprised".
- **Coverage**: `always_clothed` — garments strain and split at seams, coverage of breasts/buttocks/groin always preserved. Growth size is never the SFW problem; nudity is.
- **Cast**: named cast only, no background extras (`feedback_no_extra_characters`). Every character reads 25+.
- **Marks**: every cast member carries a named, non-wardrobe distinguishing mark (survives transformation; keeps leads tellable-apart at every size).

### 4. Validate mechanically (the gate)

```sh
python3 skills/writer/scripts/validate_script.py <project>/script.md
```

HARD failures (exit 1): parse errors, growth density under the chapter-type floor, L13 dialogue splits / >25-word balloons, non-monotonic or curve-violating tiers, missing scene decomposition (setup / ≥3 regions / reveal), coverage violations, header contract gaps. SOFT warnings: late first growth, faceless ECU runs, camera-hint issues, device shortfalls, extras-word smells.

**Repair loop** (the gribble.php pattern): fix exactly the named misses, re-run, repeat until clean. Do not hand a failing script to the human gate. Do not weaken the validator to pass a script — if you believe a check is wrong, surface it with a proposed diff instead (gate doctrine, `CLAUDE.md`).

### 5. Human gate

Surface to the user: the script + the validator's structure report (density %, runs, tier curve, devices, spine) + any autonomous-mode assumptions. **This is the last cheap point to change the story** (vision §5). Wait for approval or revisions; never auto-advance to Stage 3 in crawl/walk mode. On approval, hand off: `script-breakdown` reads `script.md`, its Step 0 pre-answered by the header.

---

## Hard rules

- **The concept is the spec.** Expand it; don't replace it. Flavor, trigger, arc, peak state, tier curve, cast, setting come from the concept. New inventions are limited to what expansion requires (scene business, dialogue, minor props).
- **Growth is the product** (`feedback_growth_density_mandate`) — hit the density target for the chapter type, and put growth ON the page (never between pages; never "before → after" in two panels).
- **Never skip the decomposition.** Every transformation scene: setup → body-region beats → reveal. The single most-confirmed pipeline failure is a transformation comic where the transformation never happens on-page (script-breakdown §4.5).
- **Escalation, not repetition.** No two capstone panels stage the same beat; each reveal re-pegs scale against a NEW gauge (person → doorframe → car → building).
- **Land the ending.** After the final payoff, at least one beat of consequence, then done. A cliffhanger is a declared hook, not a mid-swing stop.
- **Don't fabricate what Stage 3 owns.** Camera/size/staging annotations in the script are *recommendations* written to the pipeline's vocabulary; script-breakdown finalizes them. Everything else (beats, dialogue, tiers, spine, devices) is the writer's and Stage 3 transcribes it.

---

## Files

| File | What it is |
|---|---|
| `references/script-format.md` | **The Writer→Storyboard contract.** Exact output format + worked mini example. |
| `references/craft-digest.md` | The write-to-the-pipeline's-strengths ruleset, with citations to canonical sources. |
| `references/gribble-alignment.md` | What `studio/gribble.php` does; what this skill reuses vs does differently. |
| `templates/fmg-beat-template.md` | FMG beat-sheet skeleton (female muscle growth). |
| `templates/be-beat-template.md` | BE skeleton (breast expansion). |
| `templates/bg-beat-template.md` | BG skeleton (breast + glute, canonical Bloom type). |
| `templates/mmg-beat-template.md` | MMG skeleton (male muscle growth). |
| `scripts/validate_script.py` | Mechanical gate: parse + density + L13 + tier curve + decomposition. |
| `samples/spot-me/` | Worked example: concept → script → validated shotlist (all three gates run). |

## Feeds / fed-by

- **Fed by:** `ideator` (`concepts.json` → `selected_concept_id`) or a hand-written concept.
- **Feeds:** `script-breakdown` (Stage 3) via `script.md`. The header pre-answers Step 0; the beats map 1:1 onto shotlist fields (see the mapping table in `references/script-format.md`).

When this stage matures further, update `docs/PRODUCTION-SYSTEM-VISION.md` (Stage 2 status) + `CHANGELOG.md`, per the vision doc's standing instruction.
