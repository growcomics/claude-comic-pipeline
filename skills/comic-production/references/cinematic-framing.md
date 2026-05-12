# Cinematic Framing Guide

Most failure modes in comic panel sequences are technical — character drift, costume regression, 2D drift (see `lessons-learned.md`). One failure mode is *aesthetic*: every panel sits at the same camera distance, angle, and framing, and the comic feels static even when the action is intense.

A cinematic comic varies its shots deliberately. This guide covers the view categories, the rhythm rules for combining them, and the prompt fragments that produce each category reliably.

**Confirmed in production**: Chun-Li growth series. Across 10 panels, ~6 were medium torso shots from a near-front angle. No worm's-eye, no over-the-shoulder, no profile, no top-down, no extreme face ECU. Result: a 10-panel transformation that feels camera-static even though the character is changing dramatically.

---

## When to read this guide

- Before assigning per-panel `camera` values during script-breakdown
- When writing the shot-type section of a panel prompt
- During QA — check the camera assignments across the sequence as a whole, not just per-panel

Pairs with **L1.5** in `lessons-learned.md` (view-aware chaining). L1.5 tells you which prior panel a new view can chain from; this guide tells you what view to assign in the first place.

---

## The view categories

### Distance / framing

| Category | Distance | Use for |
|---|---|---|
| `ecu-face` | Eyes-to-chin | Emotional climax, dialogue beat where one word lands |
| `ecu-region` | Single body region (arm, hand, eye) | Detail beat — a tear forming, a fist clenching, a vein appearing |
| `mcu` (medium close-up) | Chest up | Dialogue, reaction shots |
| `medium` | Waist up | Conversational scenes, character vs. character |
| `cowboy` | Mid-thigh up | Western-style standoff, dramatic confrontation |
| `full` | Head to foot | Pose reveal, costume reveal, action stance |
| `wide-establish` | Subject small in scene, environment readable | Scene opener, location reset, scale moment |
| `splash` | Full-page bleed | Climax, big reveal, end-of-issue moment |

### Angle

| Category | Camera position | Emotional effect |
|---|---|---|
| `eye-level` | At subject's eye height | Neutral, conversational, default |
| `low-angle-front` | Below subject, looking up at front | Heroic, powerful, intimidating |
| `low-angle-back` | Below subject, looking up at back | Mysterious, looming, departure |
| `high-angle` | Above subject, looking down | Vulnerable, small, defeated, surveying |
| `worms-eye` | Extreme low, near ground | Monumental, towering, otherworldly |
| `birds-eye` | Directly overhead, 90° down | Diagrammatic, fated, observed |
| `dutch` | Camera tilted 10–30° off vertical | Tension, unease, instability |
| `over-shoulder` (OTS) | Behind one character's shoulder, framing another | Conversation, confrontation, surveillance |
| `profile` | Perpendicular to subject's facing | Silhouette emphasis, anatomical clarity, classical poise |
| `three-quarter` (3q) | 45° between front and side | Most flattering for figure work; default hero angle |

### Composition modifiers

| Modifier | Effect |
|---|---|
| `silhouette` | Subject backlit, features dark — for mystery, scale, or reveal-deferral |
| `reflection` | Subject seen reflected in mirror, water, polished armor, screen |
| `foreground-element` | Out-of-focus object frames the subject |
| `negative-space` | Subject small in frame, large empty area dominates |
| `dynamic-symmetry` | Subject at intersection of diagonal compositional lines |

---

## Prompt fragments per category

Drop these into the camera/shot section of a panel prompt. Combine distance × angle × modifier as needed.

### Distance fragments

**ecu-face**:
> "Extreme close-up on her face, framed eyes-to-chin. 85mm lens equivalent, shallow depth of field, background blurred to soft bokeh. Skin texture in focus."

**ecu-region**:
> "Extreme close-up on her right bicep flexed mid-growth, framed bicep-only. Macro 100mm lens, hyperdetailed muscle striation visible, skin-light catching on glistening surface, background completely defocused."

**mcu**:
> "Medium close-up from chest up. Standard 50mm lens equivalent, eye-level. Character occupies upper two-thirds of frame."

**medium**:
> "Medium shot waist-up. 35mm equivalent, conversational distance."

**cowboy**:
> "Cowboy shot — character framed from mid-thigh up, classic Western standoff framing. 35mm equivalent. Negative space around shoulders."

**full**:
> "Full body shot, character occupies the full vertical of the frame, 28mm equivalent."

**wide-establish**:
> "Wide establishing shot. Character is small in frame, environment fully visible — [location description] reads clearly. 24mm equivalent, deep focus, atmospheric perspective on distant elements."

**splash**:
> "Splash composition — single dramatic image. Character is the focal point, framed to fill the panel, with the environment compressed around her. Cinematic full-bleed framing."

### Angle fragments

**low-angle-front**:
> "Low angle — camera placed at hip height tilted up. Subject towers over the lens. Foreshortened legs in foreground, head against sky. 24mm equivalent for slight wide-angle distortion."

**low-angle-back**:
> "Low angle from behind — camera at knee height, subject's back fills the upper frame, head silhouetted against [skybox/setting]. 28mm equivalent."

**high-angle**:
> "High angle — camera elevated 4–5 feet above the subject, looking down. Subject appears smaller, surrounded by environment from above."

**worms-eye**:
> "Worm's-eye view — camera at ground level looking straight up. Subject's full body towers into frame, perspective extremely foreshortened, foreground feet large, head distant. 16mm equivalent. Sky/ceiling fills upper third."

**birds-eye**:
> "Bird's-eye view — camera directly overhead, 90° down. Subject seen from above, environment visible as ground plane."

**dutch**:
> "Dutch tilt — camera rotated 20° clockwise off horizontal. Horizon and architecture tilted, creating visual instability and tension."

**over-shoulder**:
> "Over-the-shoulder shot from [character A]'s right shoulder, framing [character B] in front. A's blurred shoulder/hair occupies the left 25% of the frame in soft focus; B is sharp, facing the camera. 50mm equivalent."

**profile**:
> "Pure profile — camera perpendicular to subject's facing direction. Side-on silhouette emphasized, single eye visible, classical anatomical clarity."

**three-quarter**:
> "Three-quarter view — subject angled 45° between front and side. The dominant flattering angle for figure work. 50mm equivalent."

### Modifier fragments

**silhouette**:
> "Subject in full silhouette — backlit by [light source], features dark, outline crisp against bright background. Only the shape and stance read."

**reflection**:
> "Subject seen reflected in [mirror / puddle / polished marble floor / shop window]. Both the reflection and the real subject visible in frame."

**foreground-element**:
> "[Object — sword blade / archway / banner / leaning figure] in out-of-focus foreground occupies the front 20% of the frame, framing the subject who is sharply in focus mid-ground."

**negative-space**:
> "Subject small in frame, occupying only the lower-right quadrant. The upper three-quarters of the frame is empty [sky / void / vast architecture] — negative space dominates."

---

## Rhythm patterns — how to actually vary shots across a sequence

Variety isn't randomness. Cinematic comics follow patterns. Four reliable ones:

### Pattern 1 — The pull-in (build to a beat)
```
wide-establish → medium → mcu → ecu-face
```
A scene builds toward a single emotional moment — a confession, a realization, a power-up reveal. Each shot tighter than the last. The ECU is the payoff.

### Pattern 2 — The pull-out (reveal)
```
ecu-region → mcu → full → wide-establish
```
A small detail expands to a huge implication. Start on a hand clenching, pull out to reveal the character is now ten feet tall and the entire arena is watching. The wide is the payoff.

### Pattern 3 — Alternating field (conversation)
```
ots-on-A → ots-on-B → medium-both → ots-on-A → mcu-B
```
Two-character scenes. Don't shoot the whole conversation from one side. Cut across the line.

### Pattern 4 — The orbit (action)
```
front-medium → profile → 3q-back → low-angle-front → ecu-region → splash
```
Action / transformation sequences. Move the camera around the subject as the action unfolds — each shot a different angle on the same beat.

---

## Variety check (apply during script-breakdown and during QA)

For any 10-panel sequence, the `camera` values should include at least:

- **5 distinct distance categories** from {ecu-face, ecu-region, mcu, medium, cowboy, full, wide-establish, splash}
- **4 distinct angle categories** from {eye-level, low-angle-front, low-angle-back, high-angle, worms-eye, birds-eye, dutch, over-shoulder, profile, three-quarter}
- **At most 3 panels** at the same distance × angle combo
- **At least 1 ECU** (face or region) and **at least 1 wide-establish or splash**

If a 10-panel sequence violates these, the comic is camera-static. Either accept and document (some sequences genuinely demand sustained intimacy or sustained scale — a long dialogue beat in mcu can be intentional), or rewrite the camera assignments.

For sequences longer than 10 panels, scale the requirements proportionally.

---

## Lens choice as emotional shorthand

The model responds to lens vocabulary. Use it.

| Lens | Effect | When to use |
|---|---|---|
| 16–24mm (wide) | Foreshortening, distortion at edges, intimacy with distortion | Worm's-eye, scale shots, claustrophobic interiors |
| 28–35mm | Slight wide, environmental | Establishing shots, full body in scene |
| 50mm (normal) | Human-eye perspective, neutral | Conversational shots, mediums |
| 85mm (portrait) | Flattering compression, subject pops from background | Hero shots, mcu, ecu-face |
| 100mm+ (macro/telephoto) | Heavy compression, background flattens to texture | ECU-region, isolation, dreamy |

Mention the lens equivalent in the prompt and the model adjusts depth, distortion, and compression accordingly.

---

## Anti-patterns

- **Repeated identical framing.** Never shoot four consecutive panels at medium-eye-level-front. Pick any other category for at least one of them.
- **Random framing.** Variety with no rhythm is noise. Pick a pattern (1–4 above) before assigning per-panel cameras.
- **Cinematic variety without view-aware chaining.** If you're varying shots, you're also changing views — recheck L1.5's chaining compatibility. A worm's-eye following a profile chain breaks the silhouette anchor; chain to a view-compatible prior or fall back to the canonical character ref + verbal state carry-forward.
- **Action lines in the prompt as overlays.** Motion blur, speed lines, action streaks should be requested as **physical scene elements** (dust kicked up, fabric mid-motion, sweat trailing, hair blown back) — never as overlay graphics. Per L7 Case B, overlay-style action lines drift toward 2D illustration.

---

## How to apply

1. **At script-breakdown**: assign each panel a `camera` value using the categories above (distance + angle, plus modifier if relevant). Run the variety check before finalizing.
2. **At prompt-writing**: paste the matching prompt fragment(s) from above into the panel's shot-type section. Combine distance and angle fragments.
3. **At QA**: scan the camera assignments across the full sequence. If a sequence violates the variety check, flag it before generation — or, if panels are already generated, flag for the next iteration.
