# Story Gap Types — Stage 12 Story Doctor pass

This is the catalog the Story Doctor subagent uses to read a story-ordered (partial) sequence and find **narrative gaps** — the missing panels that would make the post read as a complete, smooth story. Output is a prioritized gap list plus a **ready-to-paste generation prompt** for each gap. Pass this file to the subagent verbatim.

The Story Doctor reasons about *story*, not pixels. It is the complement to Stage 11 (Defect QA = technical quality). Where Defect QA asks "is this panel broken?", the Story Doctor asks "what panel is *missing*?"

A gap is a **proposal to generate** — it is not a file and never enters the sequence on its own. Once the user generates the panel and drops it in, it comes back through Stage 8 (supplementary insertion); a GAP becomes a NEW-INSERT only when the file exists.

---

## Prerequisites the subagent needs

- **The scene-block breakdown** (Stage 3) — the intended high-level beats, in order. Gaps are far easier to spot against an intended outline.
- **The cast + outfit lock** — so generated prompts anchor to canonical look/colors.
- **A script or beat sheet if one exists** — the strongest signal for "a beat is missing" is "the script has it but the panels don't."
- The current ordered sequence with a one-line content read per panel (reuse the Stage 4 audit reads if fresh).

---

## Gap categories

Read the sequence **in order** and watch for these. Each gap is one row in the output.

### 1. Missing establishing / setting shot  (type: `establishing`)
A scene block opens mid-action with no wide shot to ground *where we are*. The reader is dropped into a close-up with no spatial anchor. → Propose a wide establishing panel at the top of the block.

### 2. Missing transition / bridge  (type: `transition`)
A hard cut between two scene blocks with no connective beat — location A to location B, or one TF scene to the next, with nothing easing the jump. → Propose a bridge panel (a doorway, a walk-in, a time-of-day cue, a "meanwhile").

### 3. Skipped beat / causal gap  (type: `skipped-beat`)  ← the big one for "75% complete"
An *effect* is shown with no *cause*. The classic: a character is suddenly transforming/grown with no trigger panel — no catalyst, no first-sign, no inciting moment. The story jumps over the step that makes the next panel make sense. → Propose the missing causal panel (the trigger, the first visible change, the decision).

### 4. Missing reaction shot  (type: `reaction`)
A big moment lands (a growth beat, a reveal, a transformation peak) and **no one reacts** — the camera never cuts to a face registering it. Reaction shots are what give a beat weight. → Propose a reaction panel (the character's own face, or an onlooker).

### 5. Thin backstory / setup  (type: `backstory`)
A relationship, motivation, or stakes is assumed but never established on the page. The reader doesn't know *why* this matters. → Propose a setup panel earlier in the sequence (an establishing character moment, a "before" state, a motivating detail).

### 6. Pacing compression  (type: `pacing`)
A beat that should breathe across 2–3 panels is crammed into one — a transformation that should escalate is a single jump-cut. → Propose intermediate panels that stage the escalation (tier 1 → tier 2 → tier 3 instead of nothing → everything).

### 7. Weak opening  (type: `weak-open`)
The post starts with no hook — a flat mid-action panel instead of a grabbing first image. → Propose a stronger opening panel (a striking wide, an intriguing close, a question-raising image).

### 8. Weak / missing closing  (type: `weak-close`)
The post just stops — no button, no resolution, no final beat that lands the scene. → Propose a closing panel (a payoff, a final pose, a hook to the next chapter).

### 9. Camera / scale monotony  (type: `framing`)
Every panel is the same shot size (all medium shots), so the sequence reads flat. Missing an ECU for impact or a wide for scale at the moments that need them. → Propose a panel with the missing framing at a key beat. (Ties to the project's cinematic-framing rules — vary shot size for rhythm.)

---

## Priority scale

| Pri | Meaning |
|---|---|
| **P1** | **Comprehension-breaking.** Without this panel the story doesn't make sense — the reader can't follow what happened (most `skipped-beat` and some `transition` gaps). These are what's *actually* blocking a "75%" post from reading as complete. |
| **P2** | **Flow-hurting.** The story is followable but rough — a missing reaction, a hard cut, a compressed beat. Fixing these makes it read smoothly. |
| **P3** | **Polish.** Nice-to-have — a stronger opener, more framing variety, extra backstory richness. |

Lead with P1 in every report. The user's "75% complete" feeling is almost always a pile of P1 `skipped-beat` gaps.

---

## Completeness score rubric

Give the user a rough read on how done the post is:

1. For each scene block, estimate the **expected beats** (a TF scene typically wants: setup → trigger → escalation → peak → reaction → aftermath ≈ 5–6 beats; a simple transition block wants 1–2).
2. Count how many expected beats are **present** in the panels.
3. `completeness ≈ present_beats / expected_beats` across all blocks, as a rough %.
4. Report it tied to the gaps: *"This post reads ~75% complete. The three P1 `skipped-beat` gaps (Kay's trigger, the locker-room bridge, the final reaction) are what's blocking the other 25% — fill those first."*

Keep it honest and rough; it's a guide, not a metric.

---

## Generation-prompt template (the deliverable)

For **each gap**, produce a prompt the user can paste straight into Higgsfield/Flow. Anchor it to the canonical cast + outfit lock, and bake in the project's known generation guardrails so the output lands on-model. Fill this template:

```
GAP after <NNN>  ·  <type>  ·  <P#>
WHAT'S MISSING: <one line — the beat that isn't on the page and why it's needed>

PROMPT:
<camera/framing — e.g. "wide establishing shot" / "tight ECU on face"> of <cast present, each named with their LOCKED outfit + colors>, <action/expression that delivers the missing beat>, <location named with 5+ concrete elements>, <lighting/time-of-day to match neighbors>, photoreal CGI/3D render, <hair state named per character in frame>.

ATTACH:
- cast lineup + muscle-size guide (always, after page-0 lock-in)
- env ref for <location> (always for location-establishing panels)
- face card for <character> if a clean close-up
SUPPRESS (negative / do-not-render):
- any attached ref appearing as a physical object in the scene
- anachronistic accessories (watches, jewelry, phones) on visible wrists/necks
- background extras beyond the named cast
NOTES:
- oversize chest/muscle vs the ref so the model's scale-down lands at parity
- match the lighting + outfit of panels <NNN-1> and <NNN+1> so it cuts cleanly
```

Why these guardrails are baked in (all are standing project lessons):
- **Name the locked outfit + colors** — text-only descriptions drift; the lock is the spec.
- **Attach the env ref + name 5+ location elements** — text-only locations invent a fresh room every panel.
- **Suppress in-scene ref rendering** — attached face cards/lineups otherwise show up as a physical poster/photo in the scene.
- **Name the hair state** — buns/loose/ribbons must be stated per panel or they drift.
- **Suppress anachronistic accessories** — models hallucinate watches/jewelry onto visible wrists.
- **No background extras** — every panel contains only the named cast.
- **Oversize chest/muscle** — the model normalizes off-distribution features toward average; prompt larger so output lands at parity.
- **Match neighbor lighting/outfit** — a generated insert has to *cut* between its neighbors, so it must match their look.

---

## Output format (subagent → orchestrator)

First the gap list (one row each), then the per-gap prompt blocks, then the completeness score:

```
GAP after 012 | P1 | skipped-beat | Kay starts transforming with no trigger — show the catalyst
GAP after 027 | P2 | transition   | hard cut beach→locker room; needs an establishing bridge
GAP before 001 | P3 | weak-open   | flat opener; a striking wide would hook the reader
GAP after 045 | P2 | reaction     | growth peak lands with no one reacting

--- PROMPTS ---
[one filled template block per gap, in priority order]

--- COMPLETENESS ---
~75% complete. P1 gaps (Kay trigger @012) are the blockers; fill those first.
```

The orchestrator then builds `_story_gaps.png` (rows of `[BEFORE | yellow-dashed GAP placeholder | AFTER]`, labeled with type + priority) for the veto gate, and writes `_story_gaps.md` (the gap list + full prompts + score) as the user's generation worklist. Nothing enters the sequence until the user generates a panel and drops it in via Stage 8.
