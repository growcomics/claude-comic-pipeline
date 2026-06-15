# Ideator Concept Rubric v1.0

**This rubric scores comic CONCEPTS (pitches), not finished pages.** It is the upstream sibling of `research/comic-corpus/analysis-rubric.md` (which scores rendered comics). Where the corpus rubric measures *what a comic did*, this rubric predicts *whether a concept will do it well* — so its axes are **derived from the corpus findings**, never invented to contradict them.

**Canonical — pass verbatim to a scoring agent; never paraphrase** (`feedback_dont_paraphrase_canonical_rubrics.md`). Bump the version on any change so slates stay comparable.

**Ground truth:** `research/comic-corpus/synthesis/success-elements.md` (Findings F1–F6) + the standing memory directives (`growth-density-mandate`, `overshoot-camera-dynamism`, `expression-intensity`, `bake-dialogue`). Every axis below cites the finding it leans on. If the corpus synthesis is re-run and a finding changes, update this rubric.

---

## How to score a concept

For each concept, score the 7 axes 0–5, multiply by the axis weight, sum, and normalize to 0–100:

```
weighted_total = round( 100 * Σ(axis_score × weight) / (5 × Σ weights) )
```

with `Σ weights = 13` (so max raw = 65). Rank the slate by `weighted_total`; surface the top 3. Be a discerning critic — a flat slate where everything scores 4 is useless. Spread the scores; make the tournament mean something.

| Axis | Weight | The question it answers |
|---|---:|---|
| 1. Growth / transformation payoff density | **3** | Does it have a growth spine the genre lives on? |
| 2. Story spine / coherence | **3** | Does it have a real plot, stakes, and a paid-off ending? |
| 3. Hook strength | 2 | Does the premise stop a scroll? |
| 4. Camera / staging potential | 2 | Does the story *create* chances for dynamic, cinematic panels? |
| 5. Cast reuse | 1 | Does it reuse locked characters (cheaper) vs needing new ref packs? |
| 6. Novelty vs proven | 1 | Fresh enough to stand out, proven enough to land? |
| 7. Production economy | 1 | Is it efficient to produce (page count × new-asset load)? |

Axes 1 and 2 share the top weight on purpose: **growth is the table-stakes floor (you must have it) and story is the differentiation ceiling (it's how you win)** — see F1 and F5.

---

## AXIS 1 — Growth / transformation payoff density *(weight 3 — the niche axis)*
**Grounds:** corpus **F1** (growth-ratio tracks chapter intent) + `growth-density-mandate` + corpus Axis 1. Growth IS the product.

Score the concept on whether its structure can *sustain* growth, not just contain it. The corpus targets a growth-page ratio by chapter type: **transformation ≥60%, climax ≥70%, action/plot ≥30%.** A concept whose arc is "one-and-done potion on page 3 then 18 pages of aftermath" cannot hit those numbers; a concept built as a slow-burn or a multi-stage escalation can.

- **0** — growth is incidental/garnish; no real transformation spine.
- **2** — single one-and-done transformation; no room for zoom coverage or multi-stage escalation.
- **3** — a solid transformation the concept could carry to ~30–50% growth pages; at least one clear money sequence.
- **4** — growth-forward: a multi-stage arc, room for long transformation set-pieces, ≥2 escalation devices implied (`planned_escalation_devices`).
- **5** — growth IS the spine: the concept is engineered for a high growth ratio, progressive multi-panel escalation, heavy ECU coverage, ≥4 devices. The kind of concept that hits TMB-3 / The Curse density (corpus 68–77%).

Reward concepts that name the escalation devices they'll use (`multi-panel-progressive`, `size-comparison`, `clothing-destruction`, `sfx-driven`, …) — F4's steal-list.

## AXIS 2 — Story spine / coherence *(weight 3 — the differentiation axis)*
**Grounds:** corpus **F5** — *no book in the 9-comic corpus scores above 3 on story; the median is 2.* Story coherence is where almost everyone in the niche fails, which makes it **the single biggest competitive opportunity.** A concept that is craft-strong AND story-legible would top the corpus.

Score whether the concept has the bones the corpus consistently lacks:
- a real **spine** (a through-line, not a tit-for-tat that just stops),
- genuine **stakes** (something is at risk beyond the next size-up),
- **tease → payoff** structure (builds anticipation, then delivers — vs dumping everything at once),
- an **ending that pays off** (not "stops mid-swing"),
- legible **cause→effect** the reader can follow.

- **0** — no spine; a premise, not a story.
- **2** — corpus-typical: a thin excuse-plot to string growth scenes together (what most of the niche ships).
- **3** — a clear arc with stakes, but a familiar shape.
- **4** — real stakes + a tease/payoff structure + a paid-off ending; would read as *story*, not just transformation.
- **5** — a spine strong enough that the comic would stand out *even before* the growth — the craft-strong-AND-story-legible target F5 names as the top of the corpus.

This axis is the strategic edge. Weight it like it.

## AXIS 3 — Hook strength *(weight 2)*
**Grounds:** corpus Axis 4 (hook) + vision §5. How fast and hard does the premise grab? What's the page-1 promise that stops a scroll?
- **0** — no discernible hook. **2** — generic ("a girl gets strong"). **3** — a clear, specific hook. **4** — a hook with a twist or tension that demands you open it. **5** — a one-line hook you can't *not* click.

## AXIS 4 — Camera / staging potential *(weight 2)*
**Grounds:** corpus **F4** (device toolkit) + **F6** (even good books default to flat) + `overshoot-camera-dynamism` + L34 staging. Some stories *invite* dynamic panels (size-comparison gauges, reveal splashes, towering low-hero angles, ECU growth grids); others trap you in talking heads.
- **0** — inherently static (two people talking in a room). **2** — occasional visual opportunity. **3** — several natural set-pieces. **4** — the premise keeps handing you scale-contrast, depth, and reveal moments. **5** — engineered for spectacle: every beat wants a dynamic frame; built-in size gauges (skyline, vehicles, crowd) for the F4 `size-comparison` device.

## AXIS 5 — Cast reuse *(weight 1)*
**Grounds:** production economy. Locked characters (refs already built) are dramatically cheaper than a new cast needing full ref packs (face cards, body-tier lineups, turnarounds).
- **0** — all-new cast, every ref from scratch. **3** — mix of reused + 1 new. **5** — entirely locked roster; zero new ref-pack cost.

## AXIS 6 — Novelty vs proven *(weight 1)*
**Grounds:** the corpus patterns are *proven* (growth devices, SFX, the niche beats) but F5 says story-coherence is the *unexploited* gap. Reward concepts that ride proven craft while doing something fresh on the axis the corpus is weak on.
- **0** — a straight retread of an existing comic (ours or the corpus's). **3** — a fresh combination of proven elements. **5** — a genuinely novel angle (esp. a novel *story* shape) that still rests on proven craft. Penalize novelty-for-its-own-sake that abandons what works.

## AXIS 7 — Production economy *(weight 1)*
**Grounds:** cost realism. Estimate load = `est_page_count` × ref complexity × new-asset count (new characters, new locations, new tiers, VFX-heavy sequences).
- **0** — sprawling: high page count, all-new cast + locations + heavy VFX. **3** — moderate. **5** — tight: short-to-medium, reuses cast + an existing env pack, no exotic assets.

---

## Two free wins — design for them, don't score them
Every concept inherits these from the pipeline; they are **not** scored axes, but a good pitch is built to exploit them because the corpus shows the niche routinely fails at both:

- **Baked, legible dialogue** — corpus **F2**: 6 of 9 corpus books ship empty/placeholder balloons. The `bake-dialogue` rule means our output clears the niche's weakest axis for free. Favor concepts with real character voice to cash this in.
- **Face-led growth ECUs** — corpus **F3**: faceless money-shots underperform; face-led transformations (Ass Effect, The Curse) score a full point higher on expression. Favor concepts whose protagonist is *present and emoting* through the growth (`expression-intensity`).

---

## Output
Write each concept's per-axis scores + `weighted_total` into `concepts.json` (`scores` + `weighted_total`, schema: `concept-schema.json`). Record which findings each concept leans on in `corpus_grounding`. Surface the top 3 with a one-line per-axis justification at the human gate.

> **Engine status:** the automatic scorer that applies this rubric lives in `scripts/tournament.py` and is a **STUB** (`BUILD ME (stronger model)`). Until it's built, apply this rubric by hand — read it verbatim, score honestly, spread the scores.
