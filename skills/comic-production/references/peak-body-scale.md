# Peak Body Scale — Cartoony FMG Muscular Build

The intended aesthetic for this pipeline's transformation comics is **cartoony hyper-FMG** — exaggerated comic-book musculature with heavy 3D muscle volume, not realistic fitness modelling. Without explicit anchoring the model defaults to plausible-fitness proportions, which read as visibly *smaller* than the target on every tier ≥ 4.

This guide pairs with `assets/muscle-size-lineup.png` (tiers 1–6) and `assets/muscle-size-lineup-4-9.png` (tiers 4–9). Those are the canonical visual anchors — every stage-change panel and every full-body panel of the arc character must attach one of them.

---

## What the lineup actually is

![Muscle-size lineup — 6 figures, tier 1 through tier 6](../assets/muscle-size-lineup.png)

**The lineup is a 3D body chart with six figures showing progressive muscle development.** Each figure is a DAZ3D-style render in a double-bicep pose, showing visible:

- Deltoid mass and separation
- Bicep peak and thickness
- Chest depth
- Abdominal definition
- Lat width / V-taper
- Quad mass
- Frame width and shoulder-to-waist ratio

**It is NOT a silhouette reference.** A silhouette is a flat outline against a background — that would tell the model "match the outline shape, ignore the muscle." This is the opposite: a chart of rendered 3D muscle volume that the model is supposed to MATCH, in mass and definition, not just in outline width.

This distinction is load-bearing. Vocabulary like *"match the silhouette of figure N"* causes nano_banana_flash to interpret the reference as outline-only — getting the shoulder width roughly right while skipping the actual muscle mass. The vocabulary that works points at muscle VOLUME and DEFINITION directly: *"match the 3D muscle mass of figure N, not just the outline width."*

---

## The two bundled lineups

| File | Tiers shown | When to attach |
|---|---|---|
| `assets/muscle-size-lineup.png` | 1, 2, 3, 4, 5, 6 | Default for tiers 1–6. Use for all comics targeting up to tier 6 peak. |
| `assets/muscle-size-lineup-4-9.png` | 4, 5, 6, 7, 8, 9 | For comics escalating beyond tier 6. Use on any panel where the arc character is at tier ≥ 7. |

Picking between them at runtime: `find_lineup(root, tier)` in `next_panel.py` returns the `1-6` file for `tier < 7` and the `4-9` file otherwise.

---

## What the tiers mean

Each tier is a **muscular-build target** — what muscle mass, definition, and frame width does figure N show? Reading the lineup left-to-right:

| Tier | What it shows | Real-world analog (very rough) |
|---|---|---|
| 1 | Baseline athletic — slim, healthy, no developed muscle mass | normal fit civilian |
| 2 | Visibly developed — defined deltoid mass beginning to show, small bicep peak, tighter midsection with hint of abdominal definition | fitness-magazine athletic |
| 3 | Clearly muscular — broad deltoids with clear separation, defined bicep peaks, full chest, visible abdominal definition, noticeable quad mass | strong amateur athlete |
| 4 | **Cartoony threshold** — deltoids 2× normal mass with clear striation, biceps with visible peaks and triceps mass, full powerful chest pushing fabric, ridged 6-pack abdominal definition, strong sculpted quads, hip flare. THICK 3D muscle volume, not just a wider outline | hyper-developed comic-book hero |
| 5 | Massive — deltoids 2.5× normal mass, huge sculpted biceps with deep peaks and visible vascularity, deep powerful chest with separation, blocky 8-pack abdominal definition, powerful sculpted quads with hamstring detail. HEAVY 3D muscle volume visible from every angle | She-Hulk territory |
| 6 | Peak — deltoids 3× normal mass dwarfing the head, biceps as wide as the waist, full hyper-muscular build with every muscle group visibly developed and individually defined. MAXIMAL 3D muscle volume | comic peak |
| 7 | Beyond peak — proportions exaggerated past realism, frame-filling cartoony FMG muscle mass, biceps approach waist width, every muscle group massively developed with clear striation | superpowered female |
| 8 | Super-peak — deltoids dwarf the head, biceps wider than the waist, pure comic-fantasy proportions with maximal muscle volume | full FMG fantasy |
| 9 | Maximum — pure FMG-comic exaggeration, near-total muscle dominance over the frame, every muscle group at maximal volume and definition | maximum cartoony |

**Tier 4 is the threshold the model usually fails to clear** without aggressive prompting. It's the tier most comics center on, and the one where "match the lineup figure's muscle mass" matters most. Tier 1–3 the model handles fine; tier 5+ is so visibly exaggerated that the lineup carries the day naturally **when the prompt vocabulary points at muscle volume**. Tier 4 is the friction zone.

---

## How to anchor the muscular build in a prompt

### The wrong way (legacy "silhouette" vocabulary, do NOT use)

> "Subject at tier 4. Match the silhouette of figure 4 in the attached lineup."

This causes a documented failure mode: the model reads "silhouette" as *outline shape*, gets the shoulder width roughly right, and renders a fitness-model body at wider proportions. The muscle mass, definition, and 3D volume that figure 4 actually shows on the chart get skipped. **Verified across multiple test runs in 2026-05** — every tier ≥ 4 panel rendered this way regressed toward "athletic at wider scale" instead of "cartoony FMG."

### The right way (current vocabulary)

> "Cartoony hyper-FMG muscular build, tier 4. The attached lineup is a 3D BODY CHART showing six figures with progressive muscle development. It is a MUSCULAR-BUILD reference ONLY (NOT an outline reference). Match the 3D MUSCLE VOLUME of figure 4: deltoids 2× normal MASS (not just 2× outline width) with visible striation, biceps with peaks and triceps mass, full powerful chest, ridged abdominal definition, strong sculpted quads. Render with the SAME thick muscle mass, same striation, same chest depth, same arm thickness that figure 4 shows. NOT realistic fitness, NOT athletic, NOT a fitness model at wider scale — cartoony FMG with HEAVY 3D muscle mass."

### Aggressive vocabulary that works

- "cartoony hyper-FMG muscular build"
- "comic-book proportions with HEAVY 3D muscle mass"
- "match the 3D MUSCLE VOLUME of figure N"
- "the lineup is a 3D BODY CHART, NOT an outline reference"
- "deltoids Nx normal MASS (not just Nx outline width)"
- "thick muscle mass, visible striation, deep chest, defined abs"
- "NOT realistic fitness, NOT a fitness model at wider scale"
- Explicit muscle-group enumeration: deltoids, biceps, triceps, chest, lats, abs, quads

### Vocabulary to avoid

- **"silhouette" anywhere it points at the body reference** — the model reads it as outline-only. Use "muscular build" or "physique" or "3D muscle volume" instead.
- "athletic" / "fit" / "toned" — pulls back toward realistic fitness modelling.
- "muscular" alone (too tame; pair with "hyper-" or "cartoony" or "comic-book").
- Soft hedges ("a bit more developed", "stronger than before").
- "Outline" or "shape" when describing what to match — the chart shows volume, not shape.

---

## Attachment rule (per L11)

The muscle-size lineup must be attached on:

1. **Every stage-change panel** (where `muscle_size_tier` differs from the prior accepted panel's tier). Always, no exception.
2. **Every full-body camera panel of the arc character.** Cameras that qualify: `front-full`, `3q-full`, `side-full`, `back-full`, `low-angle-front`, `low-angle-back`, `splash`. Reason: when the body is the focal subject, the lineup keeps the muscular build honest. ECU and mcu panels skip it (size isn't the focal element).

`next_panel.py`'s `should_attach_lineup()` decides this automatically.

The old rule (L5: "lineup only on stage-change") was a cost-cutting heuristic from the Higgsfield era when refs cost money. On Flow, refs are free and the consistency gain is enormous. The new rule trades a slight composition-influence risk for substantial muscular-build consistency — the right trade.

---

## Failure modes to watch for

After generation, when reviewing a panel against its tier:

1. **Tier-target undershoot** — the rendered build looks one or two tiers smaller than declared (e.g. tier 5 reads as tier 3-4 fitness model). Most common at tier 4-6. **The 2026-05 diagnosis**: this is almost always a vocabulary failure — the prompt used "silhouette" instead of "muscular build," and the model matched the outline width while skipping the muscle volume. Fix: ensure the prompt uses muscle-mass / 3D-volume language and the explicit framing *"the lineup is a 3D body chart, NOT an outline reference."*

2. **Lineup ignored / interpolated** — the model rendered a build that splits the difference between two lineup figures. Indicates the prompt's "match the muscle mass of figure N" directive was outweighed by competing language elsewhere. Fix: simplify the prompt; the muscle-mass directive must dominate.

3. **Tier drift across the issue** — first panel after the stage-change matches the target, but subsequent panels regress smaller as the chain carries forward an interpolated build. Fix: attach the lineup on every full-body panel, not just stage-change.

4. **Realistic-fitness regression** — the panel looks muscular but plausibly real, not cartoony. The muscle volume is there but it reads as a real bodybuilder rather than comic-book exaggerated. Indicates the "NOT realistic fitness, NOT a fitness model at wider scale" anchor was missing or buried. Fix: lead with the cartoony anchor and include the explicit negation.

---

## Connection to the broader prompt skeleton

This guide updates the delta-only prompt skeleton from L10 with an explicit muscular-build anchor. The order in `compose_prompt()` is:

1. Render anchor (CGI vocabulary)
2. Camera fragment
3. **Cartoony FMG style anchor (L11)** — when the panel has a tier ≥ 2 for the arc character (slot `5_style_anchor`)
4. Subjects + delta action
5. Lighting state change
6. **Muscular-build directive (L11)** — tier-specific build descriptor with explicit 3D-body-chart framing (slot `8_tier_build`)
7. Location / env chaining
8. State anchor
9. Render directive (refs are truth)
10. Mandatory rules
11. Closing CGI anchor

The L11 anchors are *additive* — they don't replace any existing block. The style anchor slots between the camera fragment and the action delta (so the model commits to the cartoony aesthetic before reading action content); the muscular-build directive slots after the action delta and lighting (so the model has all the per-panel context before being given the muscle-mass target).

---

## History — the "silhouette" purge (2026-05-16)

The original L11 reference doc (and the L11 module, and every doc that cited L11) used the word **"silhouette"** to describe what the lineup was showing. That word was load-bearing in the wrong direction: nano_banana_flash interpreted it as *outline shape*, which is exactly what the lineup is NOT. Every tier ≥ 4 panel rendered with the "silhouette" vocabulary regressed toward fitness-model proportions with the right outline width but missing muscle mass.

Diagnosed during the running comic-test-log thread on 2026-05-16 (Test 1 + Test 2 both showed the same failure pattern; user review pointed out the lineup is a 3D body chart, not a silhouette). Validated on the 3 worst L11 fails (p13/p14/p15 of Test 2) — same character, same lineup attached, same camera, only the prompt vocabulary changed from "silhouette" to "muscular build / 3D muscle volume" — and the muscle mass landed visibly closer to the lineup figure on the v3 re-render.

171 occurrences of "silhouette" were swept across the pipeline as part of the purge. The full diff is in the [comic-test-log thread, alignment diff #2](../../../docs/posts/2026-05-16-comic-test-log.md#alignment-diff-2-after-user-review-2).
