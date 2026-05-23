# A/B Ratings — Experiment 03

Blind A/B ratings on the panels generated for this experiment. Variants are labeled `X` and `Y` in this doc so the rater doesn't know which is which until they finish. The mapping is in `outputs/README.md` (don't peek if you're the rater).

## Rating instructions

For each panel pair, give:

1. **Quality (1-5)** — overall quality of the panel. 5 = ship it.
2. **Composite coherence (1-5)** — does the foreground/background feel integrated, with consistent lighting and scale? Or does it look pasted together?
3. **Defects** — any audit-defect categories present: cast-count drop, identity confusion, FG/BG integration failure, wide-establish collapse, object-binding error, anachronistic accessories, posture-anatomy failures, hands.
4. **Preferred variant** — X or Y, or "tie."

Free-text notes welcome but optional.

---

## Panel p05-02 — Both characters mid-growth, low-angle-back

**Pair X (4 variants):** see Flow gallery row 1, positions 1-4 from left.
**Pair Y (4 variants):** see Flow gallery row 2, positions 6-9 from left.

### Rater: Matt

| Field | Pair X | Pair Y |
|---|---|---|
| Quality (1-5) | _ | _ |
| Composite coherence (1-5) | _ | _ |
| Defects | _ | _ |
| Preferred variant | _ |  |

Notes:
- _

### Rater: Magnamus

| Field | Pair X | Pair Y |
|---|---|---|
| Quality (1-5) | _ | _ |
| Composite coherence (1-5) | _ | _ |
| Defects | _ | _ |
| Preferred variant | _ |  |

Notes:
- _

### AI prelim assessment (Claude — NOT a substitute for human ratings)

Comparing the 4-up of Pair X to the 4-up of Pair Y across the 4 visual axes I can read from the gallery thumbnails:

| Axis | Pair X (4-up) | Pair Y (4-up) |
|---|---|---|
| Cast count adherence | 4/4 panels show both characters | 4/4 panels show both characters |
| Camera adherence to "low-angle-back" | 4/4 panels render back-view low-angle | 2/4 back-view, 2/4 facing-camera or 3q |
| Lab BG integration | Uniform lab plate across all 4 (periodic table left, solar-system right, lab benches, drop ceiling) | More variance — some panels have minimal lab elements, some have full BG |
| Style consistency within the 4-up | High — all 4 share identical lighting and framing | Moderate — 4 different reads |
| Character fidelity (no face refs in either variant) | Generic CGI faces; hair color holds | Generic CGI faces; hair color holds |
| Visible defects | None obvious | None obvious; one panel has a borderline hands-on-hips pose that drifts toward "hero pose" rather than the prompted mid-growth observation |

**My provisional read:** Pair X (multi-pass composite) wins on **camera adherence** and **BG consistency** — it locked the low-angle-back constraint and the lab plate across all 4 variants. Pair Y (one-shot) has more compositional variance, some of it desirable, some of it drift.

**But — this experiment's hypothesis ("multi-pass beats one-shot on hard composites") is only partially supported on this panel.** The one-shot did not fail catastrophically — both characters present, both in the lab, both at mid-growth. The audit's claim that this panel routinely drops a character was not reproducible on Nano Banana Pro / Flow in this run. Multi-pass produced a *more constrained* result; whether that's *better* depends on whether you value predictability or variance.

If the goal is "produce a panel that adheres to a specific camera and composition the first time" — multi-pass wins. If the goal is "give the picker variety to choose from" — one-shot may serve.

Provisional preferred: **X** (multi-pass), narrow margin. Confidence: low (single panel, single generation, no character-ref control).

---

## Panel p02-02 — *(not executed in this run; staged for follow-up)*

See `recipes.md` for the prompts. Run on the same Flow project; add another section below following the template above.

## Panel p05-04 — *(not executed in this run; staged for follow-up)*

See `recipes.md` for the prompts.

## Panel p03-03 — *(not executed in this run; staged for follow-up)*

See `recipes.md` for the prompts.

## Panel p01-01 — *(not executed in this run; staged for follow-up)*

See `recipes.md` for the prompts.

---

## Reveal (don't read until after rating)

<details>
<summary>Click to reveal X/Y → A/B mapping</summary>

- **Pair X** = Variant B (multi-pass build-up, composite of 3 ingredient passes)
- **Pair Y** = Variant A (one-shot control)

</details>
