# Peak Body Scale — Cartoony FMG Proportions

The intended aesthetic for this pipeline's transformation comics is **cartoony hyper-FMG** — exaggerated comic-book musculature, not realistic fitness modelling. Without explicit anchoring the model defaults to plausible-fitness proportions, which read as visibly *smaller* than the target on every tier ≥ 4.

This guide pairs with `assets/muscle-size-lineup.png` (tiers 1–6) and `assets/muscle-size-lineup-4-9.png` (tiers 4–9). Those are the canonical visual anchors for size — every stage-change panel and every full-body panel of the arc character must attach one of them.

---

## The two bundled lineups

| File | Tiers shown | When to attach |
|---|---|---|
| `assets/muscle-size-lineup.png` | 1, 2, 3, 4, 5, 6 | Default for tiers 1–6. Use for all comics targeting up to tier 6 peak. |
| `assets/muscle-size-lineup-4-9.png` | 4, 5, 6, 7, 8, 9 | For comics escalating beyond tier 6. Use on any panel where the arc character is at tier ≥ 7. |

Picking between them at runtime: `find_lineup(root, tier)` in `next_panel.py` returns the `1-6` file for `tier < 7` and the `4-9` file otherwise.

---

## What the tiers mean

Each tier is a *silhouette* target, not an inch-perfect dimension. Reading the lineup image left-to-right:

| Tier | What it shows | Real-world analog (very rough) |
|---|---|---|
| 1 | Baseline athletic — slim, healthy, no exaggerated musculature | normal fit civilian |
| 2 | Visibly more developed — defined shoulders, hint of bicep mass, tighter midsection | fitness-magazine athletic |
| 3 | Clearly muscular — broad shoulders, defined biceps and chest, visible abs | strong amateur athlete |
| 4 | **Cartoony threshold** — shoulders 2× normal width, large defined biceps, full chest, ridged abs, strong quads | hyper-developed comic-book hero |
| 5 | Massive — shoulders 2.5–3× normal width, huge sculpted biceps, deep chest, blocky abdominal definition, powerful quads | She-Hulk territory |
| 6 | Peak human-form — full hyper-muscular silhouette, fills frame width, every muscle group visibly developed | comic peak |
| 7 | Beyond peak — proportions deliberately exaggerated past realism, frame-filling silhouette | superpowered female |
| 8 | Super-peak — shoulders dwarf the head, biceps wider than the waist | full FMG fantasy |
| 9 | Maximum — pure FMG-comic exaggeration, cartoony scale, near-silhouette dominance over the frame | maximum cartoony |

**Tier 4 is the threshold the model usually fails to clear** without aggressive prompting. It's the tier most comics center on, and the one where "match the lineup" matters most. Tier 1–3 the model handles fine; tier 5+ is so visibly exaggerated that the lineup carries the day naturally. Tier 4 is the friction zone.

---

## How to anchor the proportions in a prompt

The wrong way:

> "Subject at SIZE 4. Match the muscle proportions, breast proportions, and waist of figure 4 in the lineup."

This is too gentle. The model interprets "match proportions" as "render a muscular character" and lands on a realistic-fitness build that visually reads as tier 2 or 3.

The right way:

> "Cartoony hyper-FMG proportions, tier 4. Match the EXACT silhouette of figure 4 in the attached lineup reference: shoulders 2× normal width with clear deltoid mass, large defined biceps and triceps, full powerful chest, ridged abdominal definition across the midriff, strong sculpted quads, sculpted hips. NOT realistic fitness, NOT athletic — cartoony FMG, comic-book proportions. The silhouette must match the lineup; do not approximate to a smaller realistic build."

Aggressive vocabulary that works:
- "cartoony hyper-FMG"
- "comic-book proportions"
- "match the EXACT silhouette of figure N"
- "shoulders Nx normal width" (specifically state a multiplier)
- "do not approximate to a smaller build"
- "NOT realistic fitness" (explicit negation of the model's default)

Vocabulary to avoid:
- "athletic" / "fit" / "toned" — pulls back toward realistic fitness
- "muscular" alone (too tame; pair with "hyper-" or "comic-book")
- Soft hedges ("a bit more developed", "stronger than before")

---

## Attachment rule (per L11)

The muscle-size lineup ref must be attached on:

1. **Every stage-change panel** (where `muscle_size_tier` differs from the prior accepted panel's tier). Always, no exception.
2. **Every full-body camera panel of the arc character.** Cameras that qualify: `front-full`, `3q-full`, `side-full`, `back-full`, `low-angle-front`, `low-angle-back`, `splash`. Reason: when the body is the focal subject, the lineup keeps the silhouette honest. ECU and mcu panels skip it (size isn't the focal element).

`next_panel.py`'s `should_attach_lineup()` decides this automatically.

The old rule (L5: "lineup only on stage-change") was a cost-cutting heuristic from the Higgsfield era when refs cost money. On Flow, refs are free and the consistency gain is enormous. The new rule trades a slight composition-influence risk for substantial silhouette consistency — the right trade.

---

## Failure modes to watch for

After generation, when reviewing a panel against its tier:

1. **Tier-target undershoot** — the rendered build looks one or two tiers smaller than declared. Most common at tier 4. Fix: regenerate with stronger size vocabulary and confirm the lineup was actually attached.
2. **Lineup ignored / interpolated** — the model rendered a build that splits the difference between two lineup figures. Indicates the prompt's "match the EXACT silhouette" directive was outweighed by competing language elsewhere. Fix: simplify the prompt; the silhouette directive must dominate.
3. **Tier drift across the issue** — first panel after the stage-change matches the target, but subsequent panels regress smaller as the chain carries forward an interpolated build. Fix: attach the lineup on every full-body panel, not just stage-change.
4. **Realistic-fitness regression** — the panel looks muscular but plausibly real, not cartoony. Indicates the "NOT realistic fitness, cartoony FMG" anchor was missing or buried. Fix: lead with the cartoony anchor before the camera fragment.

---

## Connection to the broader prompt skeleton

This guide updates the delta-only prompt skeleton from L10 with an explicit size-anchor sentence. The order in `compose_prompt()` is:

1. Render anchor (CGI vocabulary)
2. Camera fragment
3. **Cartoony FMG style anchor (NEW per L11)** — when the panel has a tier ≥ 2 for the arc character
4. Subjects + delta action
5. Lighting state change
6. Size tier with aggressive silhouette directive
7. Location / env chaining
8. State anchor
9. Render directive (refs are truth)
10. Mandatory rules
11. Closing CGI anchor

The L11 anchor is *additive* — it doesn't replace any existing block, and it slots between the camera fragment and the action delta so the model reads the style commitment before the action content.
