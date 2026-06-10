# Success Elements — cross-corpus synthesis (v1)

**Corpus:** 3 comics, 85 pages — *The Mysterious Book* Ch.1–3 (GrowGetter Comics, Boogie / Gribble).
**Rubric:** v1.0. **Generated:** 2026-06-09. Re-run `scripts/corpus_stats.py --corpus-root corpus` after any new ingest.

> One series is not a law of the genre — it's the first data point. Treat every finding below as a hypothesis to confirm as the corpus grows (more publishers, popularity signal). But the patterns already line up hard with the production complaints, so they're actionable now.

## Snapshot

| Comic | pp | growth% | dist↔ | flat% | exprI | dead% | G/C/E/S |
|---|---|---|---|---|---|---|---|
| Ch.1 The Opening | 25 | **60%** | 2.40 | 5.8% | 3.29 | 0% | 4/3/3/2 |
| Ch.2 The Beatdown | 29 | **28%** | 2.59 | 0% | 3.53 | 0.9% | 3/4/3/2 |
| Ch.3 Ascension | 31 | **77%** | 2.03 | 8.1% | 3.62 | 0% | 5/3/3/2 |
| **Corpus** | **85** | **55%** | 2.34 | 4.6% | 3.48 | 0.3% | — |

Escalation-device leaderboard: **sfx-driven ×10**, full-body-reveal ×8, reaction-intercut ×7, size-comparison ×7, clothing-destruction ×6, multi-panel-progressive ×5, zoom-escalation ×5, slow-burn ×3.

---

## Finding 1 — Growth-page ratio tracks CHAPTER INTENT, and the band is 28–77%

The community "count the growth pages" metric is real and measurable, and it swings with what the chapter is *for*:
- a transformation chapter ("Ascension") runs **77%**,
- an origin/setup chapter ("The Opening") runs **60%**,
- a fight chapter ("The Beatdown") drops to **28%** — the brawl crowds out the growth.

**Production directive (feeds `script-breakdown` + `growth-density-mandate`):** set a per-chapter growth-ratio TARGET by chapter type. Growth-focused chapter → **≥60%**, peak/climax chapter → **70%+**, action/plot chapter → don't fall below ~30% or the niche payload vanishes. Compute the ratio at shotlist time and flag chapters under target *before* generation.

## Finding 2 — The universal weakness is the FACE on the money shot  *(your expression complaint, confirmed in a popular comic)*

Every chapter scored Expression **3/5**. The repeated, specific defect: **growth-money-shot ECUs have dead or cropped faces** — the body bulges but no face registers the sensation (Ch.2 P5.2–4, P12.2–3, P16.1–3; the body-sweep ECUs sacrifice the face). The fix is proven *inside the same comic*: Ch.2 P17's transformation keeps 5/5 faces and lands far harder.

**This is the single clearest place the pipeline can BEAT the reference.** Directive (feeds `expression-intensity` + QA): every growth ECU/CU must be paired with a named intensity-4+ face (strain / ecstasy / awe) — either in-panel or as an intercut reaction beat. Audit flags any peak-growth panel with a neutral/cropped face.

## Finding 3 — Even the best growth chapter defaults to FLAT camera  *(your overshoot directive, validated)*

Counter-intuitively, Ch.3 — the strongest growth chapter — has the **lowest** per-page distance spread (2.03) and the **highest** flat % (8.1%), because it repeats low-hero splash poses and interchangeable "big body in space" shots (P24/25/26/30). The growth is great; the camera coverage is monotonous. The whole series leans on one move (low-hero looking up at the grower) and a narrow distance band.

**Directive (feeds `overshoot-camera-dynamism` + QA):** the pipeline's edge is *wider distance spread per page* (force ECU↔WS contrast on the same page; target dist↔ ≥3) and *breaking the low-hero default* with diagonals, depth-fg-bg, and scale-contrast (your ✓ storyboard set). The reference comic under-varies — overshoot past it.

## Finding 4 — The escalation toolkit (the STEAL list)

These devices recur and work; they're the menu `script-breakdown` should offer for any transformation scene:

1. **SFX-driven growth (×10, the signature)** — a *tiered* SFX vocabulary that scales with the transformation: body/cloth (KREEEEK, RIPPP) → impact (WHAAM) → city-leveling → cosmic energy. Carries the sensation with **zero dialogue**. Cheapest, most transferable win in the corpus. (Ch.1 P13's 7-panel pure-SFX cascade; Ch.3's scale-tiered SFX.)
2. **Multi-panel-progressive (×5, the gold standard)** — same body part across 3 panels growing stage→stage→stage with stacked SFX (Ch.2 P5 & P12 ECU body-sweeps). This is exactly the device you asked for more of.
3. **Size-comparison / fixed-gauge anchoring (×7)** — re-anchor every new scale ceiling against a fixed reference: hand-vs-car → body-vs-truck → body-vs-skyline → body-vs-Earth → body-vs-galaxy (Ch.3). Makes magnitude legible.
4. **Clothing-destruction (×6)** as a continuous growth tell; **reaction-intercut (×7)** to keep faces in the cut; **full-body-reveal (×8)** splash to cap a scene; **zoom-escalation (×5)** pushing tighter as intensity rises.

## Finding 5 — Pacing: don't flatline between growth beats

Story scored **2/5** everywhere — the corpus's weakest axis. Two failure shapes to avoid:
- **mid-chapter stall:** Ch.1 P18–21 = four straight dialogue pages between two growth peaks (dead air).
- **one-note tail:** Ch.2 P19–28 = ten pages of "villain hits hero → hero reels" with no reversal (tension drains).

**Directive:** between growth beats, keep micro-escalation alive (reaction-intercut, a new device, a reversal) — never coast. Directly relevant to the **redhead-houseguest edging structure**: the GOOD version of delay keeps small escalations firing; it doesn't go quiet. Edging ≠ flatlining.

## Finding 6 — Lettering is a real failure mode

Ch.3 ships with **blank/empty speech balloons and captions throughout** (incl. the P31 cliffhanger caption), making the plot unreadable — a major drag on its Story score. Confirms the standing rule `bake-dialogue`: never ship a comic with empty bubbles. The pipeline already mandates baked-in lettering; this is the reference comic showing the cost of not doing it.

---

## What to add to strengthen this synthesis

- **Popularity signal** — all three are Patreon-gated; no public engagement numbers. Craft scores ≠ popularity. Adding comics with visible view/comment/like counts (DeviantArt, Reddit, web galleries) lets synthesis *correlate* craft elements with engagement — the real "successful" signal.
- **More publishers/artists** — one series can't separate house style from genre norm. Ingest 3–5 more creators before treating any number as a genre law.
- **A non-growth control** — one or two high-craft mainstream comics to calibrate the camera/expression axes against pro work.

## How this routes back into production

- `script-breakdown`: seed growth-ratio targets (Finding 1) + the escalation-device menu (Finding 4) into shotlist defaults.
- `story-writers-room`: the Genre Expert critic cites Findings 1, 5 ("your pitch is at 12% growth and stalls mid-act").
- `continuity-check` / QA: Findings 2 & 3 become audit checks (dead-face % on growth ECUs; per-page distance spread; flat %).
- Memory directives backed by this data: [[overshoot-camera-dynamism]], [[growth-density-mandate]], [[expression-intensity]], [[bake-dialogue]].
