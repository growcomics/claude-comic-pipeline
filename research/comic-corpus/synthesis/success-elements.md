# Success Elements — cross-corpus synthesis (v2)

**Corpus:** 9 comics, 209 pages, all GrowGetter Comics — *The Mysterious Book* Ch.1–3, *Ultragal* #2, *Ass Effect*, *Worst to First* #4, *The Curse 2*, *Muller* #1, *Breaker* Pt.1.
**Rubric:** v1.0. **Updated:** 2026-06-09 (v1 was 3 comics / 85pp). Re-run `scripts/corpus_stats.py --corpus-root corpus` after any new ingest.

> Still one publisher — but now **6 different stories across multiple writers** (Gribble, SuperCDR, uncredited) under one dominant artist (**Boogie** drew ~7 of 9). So "house style" now means "Boogie's style," and the findings that repeat across *different stories and writers* are the trustworthy ones. The patterns below held up when the corpus tripled — they line up hard with the pipeline's known failure modes, so they're actionable now.

## Snapshot

| Comic | pp | growth% | dist↔ | flat% | exprI | dead% | G/C/E/S | writer |
|---|---|---|---|---|---|---|---|---|
| Ass Effect | 23 | 52% | 1.87 | 25% | 3.67 | 0% | 5/3/4/3 | uncredited |
| Breaker Pt.1 | 19 | 21% | 2.21 | 14% | 3.50 | 0% | 3/4/3/2 | SuperCDR |
| Muller #1 | 20 | 45% | 2.55 | 21% | 2.76 | 6% | 2/3/2/2 | — |
| The Curse 2 | 22 | 68% | 2.55 | 11% | 3.64 | 0% | 5/4/4/2 | Gribble |
| TMB 1 Opening | 25 | 60% | 2.40 | 6% | 3.29 | 0% | 4/3/3/2 | Gribble |
| TMB 2 Beatdown | 29 | 28% | 2.59 | 0% | 3.53 | 1% | 3/4/3/2 | Gribble |
| TMB 3 Ascension | 31 | 77% | 2.03 | 8% | 3.62 | 0% | 5/3/3/2 | Gribble |
| Ultragal #2 | 22 | 27% | 2.27 | 0% | 3.39 | 6% | 4/4/3/3 | Gribble |
| Worst to First 4 | 18 | 67% | 3.22 | 20% | 3.35 | 1% | 5/4/3/2 | — |
| **Corpus** | **209** | **50%** | 2.34 | 11% | 3.42 | 1.8% | — | Boogie (art) |

Escalation-device leaderboard: **sfx-driven ×34**, reaction-intercut ×26, full-body-reveal ×25, size-comparison ×22, multi-panel-progressive ×20, zoom-escalation ×18, clothing-destruction ×17, slow-burn ×6.

---

## Finding 1 — Growth-page ratio tracks CHAPTER INTENT *(confirmed across 9 books, multiple writers)*

The band is now populated and the pattern is unmistakable. Sort the corpus by growth ratio and the *type* of chapter falls right out:

- **Fight / action chapters cluster low:** Breaker 21%, Ultragal 27%, TMB-Beatdown 28%.
- **Transformation chapters cluster high:** TMB-Ascension 77%, The Curse 68%, Worst to First 67%.
- **Origin / mixed in between:** Muller 45%, Ass Effect 52%, TMB-Opening 60%. Corpus median ~52%.

**Directive (feeds `script-breakdown` + `growth-density-mandate`):** set the per-chapter growth-ratio TARGET by chapter type — transformation chapter ≥60%, climax ≥70%, action/plot chapter don't drop under ~30%. Compute it at shotlist time and flag chapters under target before generation. This is now a 9-book, multi-writer norm, not a one-series fluke.

## Finding 2 — Empty, unlettered speech balloons are ENDEMIC *(the clearest publisher-wide defect)*

This is the single most consistent flaw in the corpus: **6 of 9 books ship with blank/placeholder balloons** — Ultragal, Worst to First, The Curse, Muller, Breaker, and TMB-3 all have empty bubbles, often the whole book. Plot, motive, and character voice never land; the reader is left inferring the story from pictures and SFX. It's the main reason Story scores sit at 2.

**This is the pipeline's biggest, cheapest competitive edge.** The standing `bake-dialogue` rule (render lettering into every panel, never ship empty bubbles) isn't just hygiene — it's a thing the *most successful books in the niche routinely fail at*. Shipping legible, lettered pages alone puts our output above the corpus median on the axis they're all weakest on.

## Finding 3 — Dead faces on money-shot ECUs — and the corpus contains its own fix

The failure persists (Muller E2 / 6% dead faces; Ultragal's *hero* peak goes faceless on p3–4; Worst to First crops the face out of its biggest back-bursts). **But two books prove the fix in-genre:** Ass Effect (E4) and The Curse 2 (E4) *lead* their transformations with intensity-5 strain/ecstasy faces, and both score a full point higher on expression — and read as more intense.

**Directive (`expression-intensity` + QA):** pair every growth ECU/CU with a named intensity-4+ face (in-panel or intercut). The corpus now shows both sides — faceless money shots underperform, face-led ones land — so this isn't taste, it's the difference between the corpus's E2 books and its E4 books.

## Finding 4 — The escalation toolkit (the steal list, re-ranked on 209 pages)

| device | × | the move |
|---|---|---|
| **sfx-driven** | 34 | the genre workhorse — tiered SFX (cloth→impact→city→cosmic) carry the sensation with zero dialogue; especially vital here *because the dialogue is so often missing* (Finding 2) |
| reaction-intercut | 26 | cut to a face between growth beats so the change always has a witness |
| full-body-reveal | 25 | splash that caps a scene with the complete result |
| size-comparison | 22 | re-peg each new scale to a fixed gauge (man, car, ship, skyline, planet) — Ass Effect p18 (ship-vs-thigh), The Curse p19 (EWS man) are masterclasses |
| multi-panel-progressive | 20 | the gold standard — same body part across 3+ panels growing stage→stage with stacked SFX; The Curse runs the same arms→abs→glutes→legs ECU grid every transformation |
| zoom-escalation | 18 | push tighter as intensity climbs |
| clothing-destruction | 17 | continuous ambient growth tell |
| slow-burn | 6 | rare and underused — spreading growth across many pages; the books that do it (Worst to First's rotating cast) feel the most growth-dense |

## Finding 5 — Story is the universal weak axis — and the real differentiation opportunity

**No book in the corpus scores above 3 on story; the median is 2.** Recurring failures: thin/absent plot spine (The Curse is a potion tit-for-tat that just stops; Muller stalls then pivots to a new character), escalation-by-repetition padding the climax (Ass Effect's three near-identical cosmic splashes; TMB-3's interchangeable space splashes), abrupt momentum-only endings (Breaker stops mid-swing), and identity confusion (two The Curse leads both end in matching armor).

**The takeaway for production:** craft (growth + camera + SFX) is *table stakes* in this niche — most books do it competently. **Story coherence is where almost everyone fails.** A book that is both craft-strong AND story-legible (real stakes, a spine, a paid-off ending, lettered) would stand at the top of this corpus. That's the pipeline's strategic target, not just matching the visuals.

## Finding 6 — Even good books default to flat camera in stretches

Confirmed again: Ass Effect is 25% flat (its p3 is five flat-level talking-head panels — the exact default-failure shape) and repeats one low-hero angle through its finale; TMB-3 has the lowest distance spread despite the highest growth ratio. The corpus standout is **Worst to First (dist-spread 3.22)** — proof the genre *can* sustain wide per-page distance variety.

**Directive (`overshoot-camera-dynamism` + QA):** force a wide shot-distance spread per page (target dist↔ ≥3, the Worst-to-First level), and kill flat-level talking-head rows with diagonals / depth / OTS. The reference books under-vary; overshoot past them.

---

## What's now confirmed vs. still open

**Confirmed (held when the corpus tripled, across multiple writers):** growth-ratio-by-intent (F1); empty-balloon epidemic (F2); dead-face-vs-face-led expression gap (F3); SFX + progressive-ECU as the core devices (F4); story as the universal floor (F5); flat-camera default (F6).

**Still open:**
- **One artist.** Boogie drew ~7 of 9 — the visual findings (camera, staging) could still be Boogie's habits, not genre law. The next expansion needs a **different studio/artist entirely** to separate the two.
- **No popularity signal.** All GrowGetter, Patreon-gated — these are *craft* scores, not *what sells*. Need comics from sources with public view/comment/like counts to correlate craft with engagement.
- **A pro control** to calibrate the camera/expression axes against best-in-class work.

## How this routes back into production

- `script-breakdown`: growth-ratio targets (F1) + the re-ranked device menu (F4) seed shotlist defaults; **enforce baked lettering** (F2).
- `story-writers-room`: the Genre Expert now has hard data — "the niche's floor is story (median 2/5); your spine has to beat that," plus the growth-ratio and empty-balloon norms.
- `continuity-check` / QA: F2/F3/F6 become numeric audits — empty-balloon count (must be 0), dead-face % on growth ECUs, per-page distance spread, flat-panel %.
- Memory directives now backed by 209 pages of data: [[overshoot-camera-dynamism]], [[growth-density-mandate]], [[expression-intensity]], [[bake-dialogue]].
