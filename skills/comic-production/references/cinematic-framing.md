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

## Body-to-camera staging — L40

L34 blocks several bodies against each other. L40 (`lessons-learned.md`) blocks ONE body against the lens on a muscle beat, from the Deed Arts corpus study (`research/comic-corpus/synthesis/deed-arts-staging-study.md`). Four questions, answered in the prompt every time a solo figure flexes, grows, strikes, or is revealed:

| Question | Default | Never |
|---|---|---|
| Camera height relative to the body | chest height or lower, looking level or up; below the hips for the payoff reveal; hip height for a female reveal | above the head on a muscle beat |
| Body part nearest the lens | chest; else forearm, fist, open hand, back, glute | nothing (dialogue beats only) |
| Muscle the panel sells, and the crop that makes it the widest mass in frame | waist-up for a flex (both fists in), body-part-only for a growth ECU, full body only for the reveal | a full-body shot for an in-progress growth beat |
| Body line | c-curve, s-curve, x-spread, or diagonal lean; straight only for a front flex | a lineup silhouette |

Crosswalk to this guide's categories: the study's `worm`/`low` = `worms-eye`/`low-angle-front`/`low-angle-back`; its `camera_height` has no equivalent here and is the missing field; its `toward_camera` is the `foreshortening` composition modifier made mandatory.

### Appendable seed cards (L40)

Plain-speech sentences to APPEND after the continuation line and the refs. No appearance, no size words, no style. The full 76-card deck is `research/comic-corpus/synthesis/angle-deck.md` (`cards.json` for the Prompt Deck append mode).

- **Rear power pose:** "Camera down at worm's-eye level behind and below the figure, looking up a towering back with the arms crossed low in front of the body, the head tipped back and small at the top of the frame so the trapezius and rear-delt mass fills the panel."
- **Low reveal walk:** "Camera low, just below chest height, angled slightly upward as the figure strides forward with both arms flexed out to the sides in a lat-spread pose, filling nearly the whole frame."
- **Female reveal:** "Camera at hip height looking slightly up, she stands in a three-quarter power pose with one hand near the chin and the other on the hip, one knee crossed in front of the other so the thighs are the widest mass in the frame and the head sits small at the top."
- **Double fist at the lens:** "Camera close at chest height, both fists punched directly toward the lens in heavy foreshortening, the face visible just behind and above them."
- **Strike at the lens:** "Camera holds at chest height as a punching arm rockets toward the lens in extreme foreshortening, fist connecting just off-camera, hair swept back from the motion."
- **Over-the-shoulder glance:** "Camera set at hip height and slightly below looks up as she twists to glance back over her shoulder, the frame cropped from head to upper thigh so the back and glutes fill most of the panel."
- **Growth ECU with a face:** "Extreme close crop on a flexing bicep straining the sleeve, a small triumphant face inset in the upper corner of the frame."
- **Chest ECU:** "Camera pushes into an extreme close-up centred on the chest, filling the frame edge to edge with no background visible, the fabric straining across it."
- **Flex ladder rung:** "Same camera height, same crop, same front double-bicep pose as the previous panel, the figure now filling more of the frame, the grin wider, rim light harder."
- **Scale onlooker:** "Camera low behind the figure as one arm drives forward, a small startled onlooker in the corner of the frame for scale."

Page templates: **flex ladder** (identical pose and camera 3× down the page, biggest panel last and bled) and **body-part ECU column** (3–4 ECUs on different muscle groups, one motif, escalating SFX, face inset in the first). Use them on any three-panel growth scene.

---

## Prompt fragments per category

Drop these into the camera/shot section of a panel prompt. Combine distance × angle × modifier as needed.

### Distance fragments

**ecu-face**:
> "Extreme close-up on her face, framed eyes-to-chin. 85mm lens equivalent, shallow depth of field, background blurred to soft bokeh. Skin texture in focus."

**ecu-region**:
> "Extreme close-up on her right bicep flexed mid-growth, framed bicep-only. Macro 100mm lens, hyperdetailed muscle striation visible, skin-light catching on glistening surface, background completely defocused."

*Extended version (the 🔎 Detail button, Studio Tools v2.7.2) — same shot, with the light doing the describing:*

> "EXTREME CLOSE-UP — a detail shot. Fill the frame with [region], framed on that region alone and cropped tight, everything else out of frame. Macro 100–135mm lens at f/1.8: the background falls away into soft, creamy bokeh and [region] alone is tack-sharp. That defocus is optical depth of field from the lens, not a softening of the render — the region in focus is rendered at full hyperdetailed sharpness, skin texture and pore detail resolved. At this magnification the light does the describing: the key rakes across the muscle at a low grazing angle so every striation, every surface vein, and every tendon line casts its own fine micro-shadow, with tight speculars riding the highest points of the form and the glisten of sweat catching in the lit relief. A bright rim from behind and to the left traces the contour of the muscle in a clean edge highlight — separation only, never a glow, never an outline, never a halo. Hold the environment well below the subject in both brightness and detail so nothing in the frame competes with the region in focus."

**The f-stop is right here and wrong in a lighting pass — same words, opposite outcome.** The Hard-rules table below forbids "f/1.8, only her [X] tack-sharp" *in a lighting pass*, because there the shot already exists and that phrasing re-crops it into a macro ECU. That re-crop is precisely what this fragment is FOR, so used as a fresh shot (or as an i2i reframe with the panel as ref and **no** composition lock) it is doing its job rather than failing. Two things still carry over from that table and are folded in above: the region is **named**, never left as a bare `[placeholder]` the model has to hunt for (the button asks on click), and the rim is bright **with** the anti-glow guard rather than "strong, hot", which renders a literal glowing outline on ~half the variants. The `optical depth of field … not a softening of the render` clause exists to reconcile the bokeh with the `no added blur` sentence that closes every lighting scheme, so the two can ride in one prompt.

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

### One-click staging block — the anti-flat guard (L34 distilled)

A single append-able fragment for manual driving sessions: the three L34 staging moves compressed into one adaptive block that rides along with any action prompt (it prescribes NO camera, so it composes with everything except the i2i composition-lock sentence). Codified 2026-08-04 from storyboarding first principles — the ✓/✗ pairs storyboard artists teach: tilted eye-line vs level "static" eye-line for a 2-character face-off (tension-block), near/far with readable receding space vs same-plane "flat" (depth-staged), varied-scale V/pyramid vs a same-height lineup for 3+ (triangular). Available as the **📐 Staging** one-click button in 3DMC Studio Tools (v2.6.0).

> "STAGING — break the flat picture plane. Never arrange the characters in a flat lineup: standing side by side at the same height, the same scale, the same distance from the camera, with a level eye-line — that staging is forbidden. Instead: if TWO characters face each other, stage them on a diagonal — one face higher in frame and one lower, so the line connecting their eyes runs at a steep angle across the panel, bodies leaning in, faces close, the tension riding that tilted eye-line. When characters share a scene, stage them in DEPTH: one clearly nearer the camera and larger in frame, the other deeper in the scene and smaller by perspective, with readable space — floor, walls, a doorway, furniture — receding between them so the shot has a front and a back. With THREE or more characters, build a pyramid: every figure at a different scale and a different depth, one large in the near foreground cut by the frame edge, the others staggered behind at varied heights, their heads tracing a V or a diagonal across the panel — never a flat row of same-sized heads. Let the environment's perspective lines converge to support the depth, and keep every face readable."

The **tilted eye-line** is the piece the per-value fragments above under-specify: tension-block talks intent angles and forehead proximity, but the storyboard heuristic is simpler and stronger — if the line connecting the two characters' eyes is level, the panel is static; tilt it and the same blocking reads as tension. Use the eye-line as the QA check too: trace it on any 2-character panel; level ≈ flag.

---

## Lighting-pass fragments — the volume block

*Validated 2026-07-09 on Nano Banana 2 Lite via Flow (7 batches / 28 images, Chun-Li & Cammy growth chain, athletic tier through beyond-tier). Composition lock held 28/28. No anatomy inflation observed at any size tier — the block sculpts with light only, so it is safe to apply across a chapter regardless of growth tier.*

Muscle volume perception comes almost entirely from the highlight-to-shadow gradient across each muscle group — not from blur, not from re-describing the anatomy. This section is the validated wording for adding that gradient. Two uses:

1. **Post-hoc lighting pass (i2i)** — attach the accepted panel as the SOLE ref and submit the block alone. Same framing comes back with sculpted light.
2. **Inline lighting section** — drop the block minus its first sentence into the lighting section of a fresh panel prompt.

### Default volume block (golden hour + deep AO)

> "Keep the exact same camera angle, framing, character poses, expressions, speech bubbles, and composition as the source image — no zoom, crop, or recenter. Lighting pass only: low golden-hour sunlight skims across [both women's bodies / her body] from the left, modeling every muscle group with a bright highlight-to-shadow gradient. Push the sculpt: ambient-occlusion shadows one stop deeper in every crease where muscle heads meet, so each muscle reads as a distinct rounded volume. Glossy sweat highlights on the peaks, subtle warm rim light on [both silhouettes / her silhouette]. Background half a stop darker with light haze. Photoreal DAZ3D render, no restyling."

### Climax variant (warm chiaroscuro)

> "Keep the exact same camera angle, framing, character poses, expressions, speech bubbles, and composition as the source image — no zoom, crop, or recenter. Lighting pass only: dramatic high-contrast chiaroscuro keyed to the scene's existing [warm dusk / interior / night] palette — a single hard warm key light from the upper left rakes across the muscles, shadows one stop deeper in every muscle crease, hot specular highlights on the peaks, warm amber rim light separating the figures from the background. Keep the sky and environment at their original palette — do not shift the scene toward night or cool blue tones. Photoreal DAZ3D render, no restyling."

Reserve the chiaroscuro variant for climax / dominance beats — it is the moodiest grade, and over-use flattens the chapter's lighting arc. ALWAYS name the palette to preserve ("existing warm dusk palette"): the un-keyed version reliably drifted dusk → cool night, breaking time-of-day continuity with neighboring panels.

### Hard rules (each bought with a failure)

| Rule | Failure mode it prevents |
|---|---|
| Composition lock is the FIRST clause, verbatim | Edit models weight the opening clause heavily; lock-last or lock-free versions recompose the shot |
| Emphasis stays PLURAL — "every muscle group", "both silhouettes" | Naming one muscle as the sharp/focal subject recrops the panel into a macro ECU of that muscle |
| No f-stop or bokeh language in a lighting pass; at most "background very slightly softened" | "f/1.8, only her [X] tack-sharp" re-shoots the panel as an isolated macro crop — and an unfilled `[placeholder]` makes it hunt even harder |
| Rim light is "subtle warm", never "strong, hot" | "Strong hot rim" renders a literal glowing outline around the silhouette (sticker/aura look) on ~half the variants |
| The volume dial is shadow depth, not blur | If a pass reads flat, push "shadows one stop deeper in the creases" on the next pass; adding DOF instead triggers recompose |
| In-image footer/watermark strips do NOT survive re-renders | The fake DAZ footer text mutated across passes (GHUN-LI → SHUN-LI → CHUN-U); render-carried micro-text is unstable — letter footer strips at L19 / composition stage |

Interactions: pairs with **L19** (SFX stays scope-bounded 2D overlay — max one SFX word + 2–3 short radial burst clusters per panel; full-frame speed lines re-trigger 2D drift) and **L20** (get close first — the block sculpts whatever the framing gives it, so a chest-up panel gains more perceived volume than a full-body one).

---

## Director's-choice reframe — scene-adaptive camera

The fixed hero-framing fragments above always produce the same setup (three-quarter, mid-thigh-up, mild low angle) — reliable, but a chapter shot only with them ruts into low-and-heroic. The Director block inverts the contract: instead of prescribing the camera, it hands the model the *cinematographer's job* — study the attached source panel and choose the move (dolly, orbit, height change, tighter/wider) that serves that specific beat. Use it i2i: attach the source panel as the sole ref, then this block IS the prompt.

> "You are the film director and cinematographer for this scene. Study the source image — who is in it, what they are doing, the emotion of the beat, and the space around them — then re-stage the CAMERA ONLY for maximum cinematic impact: dolly in or out, orbit around the subjects to a new angle, raise or lower the camera height, tilt it, frame tighter or wider — whatever this specific moment calls for. Keep the scene itself untouched: the same characters with the same faces, bodies, proportions, costumes, poses, expressions, action, speech bubbles, environment, and time of day — only the camera changes. Choose like a director: if the beat is emotional, move close on the faces; if it is a power moment, get low; if scale is the story, pull wide; if the tension lives between two characters, shoot past one onto the other; if one body region carries the beat, fill the frame with it. Vary your choice — do NOT default to a low hero angle: high angles looking down, pure profiles, over-the-shoulder, three-quarter rear, and top-down are all in play when they serve the beat. Strongly avoid the source image's exact framing — pick a meaningfully different distance AND a meaningfully different angle — and avoid flat, front-on, eye-level staging: put the subjects on diagonals, stage depth between foreground and background, let the physiques dominate the composition from whatever angle you choose. Do not re-light the scene: keep the existing lighting scheme and mood, re-rendered correctly and consistently from the new camera position. Photoreal DAZ3D CGI render, no restyling, no illustration drift."

Rules of engagement:

- **Never pair it with the composition-lock sentence** — its whole job is to move the camera; the lock's whole job is to forbid that. (The fixed framing fragments have the same conflict; the lighting-pass volume block is the only one that rides with the lock.)
- **It deliberately does not carry the volume-lighting language** — it preserves whatever lighting the source has ("do not re-light"), so run it on panels that already carry the grade you want, or follow it with a volume pass.
- **Per-batch variance is real but per-submit convergence is possible** — the block asks the model to justify the choice from the scene, and x4 batches typically return 2–3 distinct setups; if a batch converges on one angle you don't want, resubmit with a nudge appended ("this beat reads best from above" / "favor the over-the-shoulder option").
- **QA against the Variety check below as usual** — the block is a per-panel tool; the chapter-level distance × angle quotas still apply.
- Available as the **🎥 Director** one-click button in the 3DMC Studio Tools Flow panel (v2.3.0), alongside Cine+Light / Framing / DAZ style.

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
