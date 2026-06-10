# Escalation Devices — the growth-scene toolkit (L35)

Ranked menu of the techniques that make a female-muscle-growth transformation *land*, derived from the `comic-corpus` study (9 comics / 209 pages — `research/comic-corpus/synthesis/success-elements.md` v2). The number is corpus frequency: how often each device appeared across the analyzed transformation scenes.

**How to use this**: at `script-breakdown`, every declared `transformation_scenes` entry should consciously select **≥2 devices** (more for a climax) and reflect them in the per-panel beats. At generation, L35 (`rules/l35_growth_intensity.py`) reinforces the physical manifestation; the device *selection* is a shotlist decision, not an automatic one.

**Hard constraint — L7 compliance**: all visual cues are *physical scene phenomena* (sweat, fabric, dust, particles, motion). **No baked-in comic SFX text or action lines** — those are added by `page-composer` as vector overlays post-render. "sfx-driven" below means the *sensation* is carried by physical phenomena + (post-render) lettering, not by typing "RRRIP" into the image prompt.

---

## The menu (ranked by corpus frequency)

| # | Device | corpus× | What it does | When to reach for it |
|---|---|---|---|---|
| 1 | **sfx-driven** | 34 | The growth *sensation* carried by escalating physical phenomena (fabric strain → seam split → displaced air) + post-render SFX lettering. The genre workhorse — and doubly vital here because the corpus's dialogue is so often missing. | Every transformation beat. |
| 2 | **reaction-intercut** | 26 | Cut to a face — the grower's or a witness's — between growth beats, so the change always has an emotional witness. **This is the structural fix for faceless money-shot ECUs (L35 Finding 2).** | Any run of body-region ECUs; reveals. |
| 3 | **full-body-reveal** | 25 | A splash/wide that caps the scene with the complete transformed result. | End of a transformation scene. |
| 4 | **size-comparison** | 22 | Re-peg each new scale against a fixed gauge — a man, a car, a doorframe, a truck, a skyline, a planet. Makes magnitude legible. | Whenever the size ceiling jumps; climaxes. |
| 5 | **multi-panel-progressive** | 20 | The gold standard: the *same body part* across 3+ panels growing stage → stage → stage with stacked physical cues. | The core of any body-region growth beat. |
| 6 | **zoom-escalation** | 18 | Camera pushes tighter (MS → CU → ECU) as intensity climbs. | Building to a growth peak. |
| 7 | **clothing-destruction** | 17 | Garments straining and splitting as a continuous, ambient growth tell. | Any beat with growth under clothing. |
| 8 | **slow-burn** | 6 | Spread the transformation across many pages instead of one. Rare and underused — the books that do it feel the most growth-dense. | Long-form / hero transformations. |

---

## Per-device prompt fragments (physical phenomena only — drop into the panel `action`)

- **sfx-driven** → "fabric audibly straining and splitting at the seams, the swelling muscle taut and sweat-slick, a shock of displaced air rippling outward." *(SFX lettering added post-render by page-composer.)*
- **reaction-intercut** → (a separate panel) "tight on her face — eyes blown wide, mouth open in overwhelmed gasp, hands flying to her transforming body" OR "a bystander recoils, eyes huge, stepping back."
- **full-body-reveal** → "wide splash, the fully transformed figure dominating the frame, low hero angle, dramatic rim light raking the new mass."
- **size-comparison** → "the figure dwarfs the [car / doorway / man / skyline] beside her — the fixed object tiny against her new scale."
- **multi-panel-progressive** → (across 3 panels of the same region) panel 1 "toned and tensing", panel 2 "visibly larger, seams beginning to give, veins surfacing", panel 3 "enormous, fabric burst, veined and glistening".
- **zoom-escalation** → set the panel `camera` tighter each beat: `medium` → `mcu` → `ecu-region`.
- **clothing-destruction** → "the [garment] strains across the expanding [region], threads snapping, fabric peeling back from the swelling muscle." (Coverage of breasts/buttocks/groin is preserved per `always_clothed` — fabric tears at seams, not into nudity.)
- **slow-burn** → distribute the body-region beats across multiple pages; don't resolve to full-body until the scene's final page.

---

## Anti-patterns (what the corpus did wrong — don't replicate)

- **Faceless money-shots.** A body-region ECU run with no interleaved face panel (corpus Finding 2 — the #1 weakness). Always pair with reaction-intercut.
- **Escalation-by-repetition.** Three near-identical "big body" splashes in a row to pad a climax (corpus: Ass Effect, TMB-3). Each reveal must change scale, angle, or stakes — use size-comparison to re-anchor.
- **One-and-done growth.** Skipping from "before" to "after" in two panels. Decompose per the transformation-beats rule (`script-breakdown` §4.5).
- **Empty balloons.** Out of scope here (handled by L19 / bake-dialogue), but noted: 6 of 9 corpus books shipped unlettered — never do that.

See also: `lessons-learned.md` § L35, `cinematic-framing.md` (camera distance + L34 staging), `research/comic-corpus/synthesis/success-elements.md`.
