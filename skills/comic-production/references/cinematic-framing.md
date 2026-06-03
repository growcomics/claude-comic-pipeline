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
| `foreground-element` | Out-of-focus object frames the subject (see also `foreground-occlusion` under Subject staging — they're the same principle; `foreground-occlusion` is the L34-cited name) |
| `negative-space` | Subject small in frame, large empty area dominates (see also `negative-space-asymmetric` under Subject staging) |
| `dynamic-symmetry` | Subject at intersection of diagonal compositional lines |

---

## Subject staging — L34

What L20 doesn't cover: where the *subjects* are arranged in the frame. L20 sets the camera distance; this section governs subject blocking. The unified principle: **the camera plane is the enemy**. Anything that puts the action on a flat plane parallel to the camera flattens the image; anything that pushes the action off that plane (diagonal intent, Z-depth, varied scale, asymmetric placement, foreground occlusion) creates dynamism.

Five staging values are recognized. Each shotlist beat with 2+ named characters at `camera_distance ≥ 2` (medium or wider) MUST declare one of these via the `subject_staging` field (HARD `rules_audit` gate). Solo-subject beats SHOULD declare one when the camera_distance is medium or wider.

| Value | When to use | What it does |
|---|---|---|
| `tension-block` | 2-character confrontation, dialogue with conflict, rivalry beat | Diagonal intent between two figures; foreheads angled toward each other; the line connecting their heads forms the frame's main axis. Tension comes from intent angles + proximity, not from distance. |
| `depth-staged` | Lead + secondary in same panel, post-transformation reveal, dominance beat | Lead character foreground (50-60% of frame height); secondary character mid-ground or deep background at materially smaller scale by perspective. Three distinct depth layers: FG / midground / BG. Used to establish the lead's dominance via scale contrast. |
| `triangular` | 3+ characters, squad / crew / group panel | Lead at apex of compositional triangle (foreground, largest scale); supporting characters at lower base points at varied mid-depths and varied scales. Renaissance pyramidal composition (Raphael, Leonardo). Eye paths trace pyramid lines. **No two figures at the same scale or Z-depth.** |
| `negative-space-asymmetric` | Solo hero shots, reveal beats, splash panels | Lead subject occupies one third of the frame; the remaining two thirds dominated by empty space (sky / void / empty architecture / single shaft of light). Asymmetric composition emphasizes the lead's mass by contrast. |
| `foreground-occlusion` | Intimacy panels, voyeur-witness energy, lead seen through environmental element | Camera shoots past an out-of-focus FG element (barbell, archway, doorframe, weight rack) occupying the lower 20-25% of frame as a chunky bokeh element. Lead character sharp in midground framed by the FG element. |
| `parallel-acceptable` | Escape hatch — group reveal, formal portrait, ceremonial lineup | No directive emitted. SOFT-warns if used > 2× in a chapter. Should be exceptional, not default. |

**The principle's FMG payoff**: all five staging values amplify lead-character prominence — the focal subject in FMG comics is the lead's body proportions (muscle + bust + glutes). Tension blocking puts the lead foreground in confrontation panels; Z-depth keeps the lead foreground in reveal panels; triangular keeps the lead at apex in squad panels; negative-space gives the lead breathing room in hero panels; FG occlusion frames the lead like a target through environmental elements. **It's not "fancy composition" — it's "the lead dominates by being staged closer + larger + more central by intent angle."**

**Canonical reference figures**: `sketches/staging-examples/` contains 8 generated examples — three GOOD/BAD pairs plus two single-subject GOOD examples, all featuring an FMG-genre lead character at peak tier 8. See files `01-tension-good.png` through `08-fg-occlusion-good.jpeg`. These are the reference figures L34 cites.

See also: `composition-reading-list.md` for the annotated source reading (Wally Wood, Mateu-Mestre, Eisner, Mascelli, Block, Zhou, McCaig).

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

### Subject staging fragments (L34)

Emitted automatically by `next_panel.py` `_l34_staging_directive()` when the panel's `subject_staging` field is set. Operators can paste these manually as well.

**tension-block** (2-character confrontation):
> "TENSION BLOCKING: Both characters lean into each other along a diagonal axis from lower-left to upper-right. Foreheads nearly touching; shoulders thrust toward the other figure; weight forward on lead foot; bodies rotated three-quarter so the line connecting their heads forms the frame's main axis. They are visibly aimed at each other — intent angle is everything. Lead character occupies foreground / dominant focal position."

**depth-staged** (lead + secondary, dominance beat):
> "Z-DEPTH STAGING: Strong three-layer composition. LEAD character in the foreground at three-quarter angle, occupying ~50-60% of frame height — dominant focal subject. SECONDARY character placed deep in the background through architecture (doorway, corridor, archway) at materially smaller scale by perspective (~20-25% frame height). Clear perspective lines of the environment converging toward a vanishing point. Three distinct depth layers: foreground / midground / background, each with a different lighting tone."

**triangular** (3+ characters, group panel):
> "TRIANGULAR / PYRAMIDAL GROUPING: LEAD character at the APEX of a compositional triangle — foreground, largest scale in frame, three-quarter angle. Two supporting characters at the lower base points at varied mid-depths and varied scales. Eye paths trace pyramid lines from the apex down to each base point. NO two figures at the same scale or Z-depth. Lead's mass dominates by being closest + largest + most foreground."

**negative-space-asymmetric** (solo hero, splash, reveal):
> "NEGATIVE-SPACE DOMINANCE: Lead subject occupies only the lower-right (or lower-left) third of the frame. The upper two-thirds dominated by NEGATIVE SPACE — empty architecture / sky / void / single dramatic shaft of light catching dust motes. Asymmetric off-center composition; subject's mass amplified by contrast with the emptiness. Often combined with low-angle hero shot."

**foreground-occlusion** (intimacy, voyeur, framed-through-environment):
> "FOREGROUND-ELEMENT FRAMING: Camera shoots PAST an out-of-focus foreground element (barbell, weight rack, doorframe, archway, equipment bar) occupying the lower-left (or lower-right) 20-25% of the frame as a chunky dark bokeh shape. The LEAD character in sharp focus mid-ground, framed by the FG element. Creates layered depth and an intimate-witness energy — the viewer is positioned as an observer behind/through environmental architecture."

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
- **Cinematic variety without view-aware chaining.** If you're varying shots, you're also changing views — recheck L1.5's chaining compatibility. A worm's-eye following a profile chain breaks the state-anchor view compatibility; chain to a view-compatible prior or fall back to the canonical character ref + verbal state carry-forward.
- **Action lines in the prompt as overlays.** Motion blur, speed lines, action streaks should be requested as **physical scene elements** (dust kicked up, fabric mid-motion, sweat trailing, hair blown back) — never as overlay graphics. Per L7 Case B, overlay-style action lines drift toward 2D illustration.

---

## How to apply

1. **At script-breakdown**: assign each panel a `camera` value using the categories above (distance + angle, plus modifier if relevant). Run the variety check before finalizing.
2. **At prompt-writing**: paste the matching prompt fragment(s) from above into the panel's shot-type section. Combine distance and angle fragments.
3. **At QA**: scan the camera assignments across the full sequence. If a sequence violates the variety check, flag it before generation — or, if panels are already generated, flag for the next iteration.
