# Prompt Templates
## Reusable Prompt Fragments for Higgsfield Comic Production

> **STATUS: Active — updated for L19.** Last reviewed 2026-05-13.
>
> Per **L19** in `lessons-learned.md` (which reverses L7 Case B's "never bake lettering" prescription), speech bubbles, captions, and SFX text are baked **directly into the generation prompt** for CGI / photoreal panels — not deferred to `page-composer` overlays. L7 Case B's diagnosis still holds (comic-coded vocab pulls CGI prompts toward 2D illustration training data); the fix changed. The L19 fix is aggressive anchoring at both ends of the prompt:
>
> 1. **Open every CGI prompt with concrete render-engine vocabulary** — *"Hyperrealistic DAZ3D Studio 3D CGI render, ray-traced subsurface scattering on skin, physically-based rendering, 8K texture detail, photographic CGI."*
> 2. **Render lettering as physical 3D scene objects** — SFX as 3D-extruded chrome / stone / energy letter sculptures with real ray-traced shadows; speech bubbles as photoreal semi-translucent 3D panels floating in space with tails pointing at speakers; captions as in-scene plaques.
> 3. **Close every prompt with the negation block** — *"NOT a comic, NOT an illustration, NOT anime, NOT 2D drawn art. Photographic CGI render."*
>
> Without both ends of that anchor, baked lettering still drifts to 2D. With it, the model holds photoreal CGI while rendering the comic elements as part of the scene.
>
> Section-by-section status (in this file):
>
> - **Mandatory Rules Block** — *active*. All ten rules apply, including the speech-bubble and dialogue lines. Bubbles are baked, so per-speaker attribution and per-bubble-unique-line discipline are back to mattering.
> - **Action Lines and SFX** — *active, but the rendering language was rewritten*. SFX text IS baked into the prompt, but rendered as 3D-extruded letter sculptures with real ray-traced shadows — not flat 2D burst lettering or "action lines radiating outward." See the section below for the L19-conformant phrasing.
> - **Dialogue Formatting** — *active*. Speech bubbles, thought bubbles, and caption boxes are written into the generation prompt as physical 3D scene objects (per L19), with bubble shape, position, tail direction, and per-speaker attribution per **L4**'s rules. The `dialogue[]` / `captions[]` arrays in `shotlist.json` remain the source of truth for *what is said*; the prompt is where you describe *how the bubble renders in the photoreal scene*.
>
> See the **Master CGI prompt template** in `CHANGELOG.md`'s 2026-05-13 entry for the canonical skeleton (opening render-engine anchor → camera → subject + tier silhouette → action delta → wardrobe delta → baked SFX as physical object → baked bubble as physical object → environment delta → closing negation block) and the rule-to-section mapping.

Copy and paste these directly into panel prompts. Do not rewrite from memory — the exact wording has been tested and refined. Seemingly minor word changes (e.g., "glistening" vs "shiny") can meaningfully affect output quality because the model latches onto specific vocabulary.

---

## Style Prefix

Start every single prompt with this. No exceptions. It anchors the visual style and prevents the model from drifting into illustration, anime, or painterly aesthetics.

```
Hyperrealistic DAZ3D Studio 3D CGI render, physically-based rendering — NOT an illustration, NOT anime, NOT cartoon, NOT 2D drawn art.
```

> **Note (post-L7):** for chained sequential comic panels, prefer the longer positive-anchoring vocabulary used in the L7 Case B worked example and in `cinematic-framing.md` / `environment-references.md`. Lead with concrete render-engine vocabulary (Iray, ray-traced subsurface scattering, specular highlights catching warm rim light, physically-accurate fabric weave, 8K texture detail, photographic bokeh) rather than a list of "NOT X" negations. Stacked negations dilute each other; one positive anchor + one closing "Photographic CGI render, NOT illustrated" works better.

---

## Mandatory Rules Block

> **Active — all ten rules.** Per **L19**, lettering is baked into the CGI render (paired with aggressive anchoring vocabulary to prevent 2D drift), so the speech-bubble and dialogue lines below apply alongside the rest of the block. The block was partially deprecated under L7 Case B's older "never bake lettering" rule; that prescription has been reversed. Paste the full block — and pair it with the L19 opening render-engine anchor and closing `NOT a comic, NOT an illustration, NOT anime, NOT 2D drawn art. Photographic CGI render.` negation block (see the file header above and the Master CGI prompt template in `CHANGELOG.md` 2026-05-13).

Paste this at the end of every panel prompt. Every rule, every time. The model has no memory between generations — it treats each panel as a fresh request. Rules from a previous panel's prompt do not carry forward.

```
Muscles are natural healthy skin tone — NOT red, NOT inflamed. Skin is wet, shiny, glistening with effort, like oiled skin catching warm light. Excellent muscle definition and visible tone throughout. Any character with enlarged muscles also has proportionally enlarged, full breasts with prominent cleavage visible — muscle growth and breast growth always occur together, and breasts NEVER shrink or revert to a smaller size once they have grown. All characters fully clothed at all times — clothes may be torn, stretched, or splitting at seams from muscle growth but always cover the body. Speech bubbles show exactly the correct character speaking their correct line — never the wrong character. Every speech bubble contains a unique line — no character repeats themselves. Every character has a vivid, animated, expressive face — mouth open mid-speech, gasping, laughing, or wide-eyed, never neutral or blank. All characters look at each other, never at the camera. Correct human anatomy — exactly two arms and exactly two legs per person, no extra limbs, no duplicate limbs, no third or fourth leg. Once a character has grown muscles they stay at that size or larger in all subsequent panels — muscles never revert. Once breasts have grown they stay at that size or larger — breasts never revert or shrink.
```

Why each rule exists:
- **Muscle color**: Without this, the model renders muscles as red/inflamed during growth. The "wet, shiny, glistening" language gives it a positive visual alternative to "straining."
- **Muscles = breasts**: The model won't add both unless told. Every time.
- **Breast persistence**: The model reverts breasts to the base reference size unless explicitly told they've grown AND told they must not shrink. This is stated twice (growth rule + revert rule) because a single mention is often ignored.
- **Clothing**: Prevents nudity while allowing dramatic clothing destruction.
- **Dialogue attribution** *(active per L19 — lettering is baked into the render)*: The model decides bubble placement based on character positioning. Without explicit attribution, bubbles end up above the wrong character. See L4 for the full bubble-shape / position / tail-direction rules.
- **No repeated dialogue** *(active per L19)*: Without this, characters echo each other or repeat lines across panels.
- **Expressive faces**: The model defaults to neutral/blank expressions. This is one of the biggest quality killers — lifeless faces break immersion no matter how good the rest of the panel is.
- **No camera eye contact**: Characters looking at the viewer breaks the fourth wall and feels awkward in narrative panels.
- **Anatomy (arms AND legs)**: Prevents extra limbs. The model generates extra legs more often than extra arms, so both must be specified explicitly. "No extra limbs" alone is not sufficient — the model needs the exact count stated.
- **Muscle continuity**: The model reverts characters to their reference image size unless explicitly told they've grown.

---

## Shot Types

### Wide establishing shot
```
Wide shot — full environment visible, characters small within the space, setting is the focus.
```

### Medium shot (most common for dialogue)
```
Medium shot — characters from waist up, facial expressions clearly visible, background partially visible.
```

### Close-up (face/reaction)
```
Close-up — face and upper chest only, full emotional expression, background blurred.
```

### Over-the-shoulder
```
Over-the-shoulder shot — camera behind one character looking toward the other, conversational framing.
```

### Low angle (power/intimidation)
```
Low angle shot looking up — subject appears dominant and powerful, ceiling or sky visible above.
```

### Extreme closeup (transformation detail)
```
EXTREME CLOSEUP — [specific body part, e.g. bicep / shoulder / forearm / quad] swelling and growing, skin glistening, veins visible beneath the surface, fabric of [shirt sleeve / pant leg / lab coat] splitting at the seam from the pressure of expanding muscle.
```

### Rear view / Back pose
```
Rear view — character seen from behind, back muscles and glutes visible, looking over shoulder. NOTE: Tag this panel as view_angle: "rear" so the runner skips it when chaining to front-facing panels.
```

> **Note (post-L7):** for richer cinematic variety, see `cinematic-framing.md` — full distance × angle × modifier matrix plus rhythm patterns (pull-in, pull-out, alternating field, orbit) and a quantitative variety check.

---

## Transformation Scene Templates

Use these in sequence for any character transformation. Compressing a transformation into one panel makes it feel rushed and cheap. Expanding it into multiple panels — with closeups of the specific body part changing — makes it feel cinematic and earned.

### Panel A — Growth begins
```
[CHARACTER NAME] standing, suddenly overcome — eyes wide, mouth dropping open in shock and then pleasure, body beginning to change. Clothes visibly tightening across shoulders and chest, fabric pulling taut. The very beginning of something enormous.
```

### Panel B — Growth accelerating (mid-transformation)
```
[CHARACTER NAME] mid-transformation — muscles surging visibly beneath skin and clothes, fabric tearing along shoulder seams and sleeve seams, breasts swelling and pressing forward, expression shifting from shock to pure ecstatic joy, head tilting back.
```

### Panel C — Extreme closeup of specific muscle
```
EXTREME CLOSEUP — [CHARACTER NAME]'s [bicep / shoulder / forearm] ballooning outward in real time, sleeve fabric splitting and peeling back, skin flushed and glistening with a wet sheen, muscle fibers visibly defined beneath smooth shining skin, the fabric losing the fight completely.
```

### Panel D — Torso laughing shot (use ~50% of the time)
```
Torso shot — [CHARACTER NAME] from waist to chin, head thrown back laughing with pure joy and disbelief at what is happening to their body, both hands raised slightly, enormous chest heaving, shredded clothing barely clinging to their transformed physique.
```

### Panel E — Transformation complete
```
Full body shot — [CHARACTER NAME] standing with hands on hips or arms raised in a flex, transformation complete, new physique fully revealed. [Describe final size relative to other characters or objects in the scene.] Expression: triumphant, thrilled, powerful. Clothes destroyed — only scraps remaining but still covering the body.
```

### Action Lines and SFX — MANDATORY FOR ALL GROWTH PANELS

> **Active — rendering language updated for L19.** SFX text IS baked into the generation prompt, but rendered as **3D-extruded letter sculptures** (chrome, stone, energy) with real ray-traced shadows and the same scene lighting as the rest of the render — never as flat 2D comic-burst text or radiating action lines. The old "RRRRIP! as red/yellow burst text" / "action lines radiating outward" phrasing pulled the CGI render toward 2D illustration (the L7 Case B failure mode confirmed in the Chun-Li growth series panels 3/4/5); the physical-scene-object framing holds CGI while still delivering the SFX punch. This section's prompt block is the L19-conformant version. Pair it with the L19 opening render-engine anchor and closing `NOT a comic, NOT an illustration, NOT anime, NOT 2D drawn art. Photographic CGI render.` negation block — see the file header.

**CRITICAL: In-scene SFX MUST be included in EVERY panel where growth or transformation is occurring. These are NOT optional. They are NOT a nice-to-have. Skipping them makes growth panels look static and lifeless. Include this block in every growth panel — no exceptions.**

Transformation scenes must include visual storytelling cues that help the reader's eye focus on what's changing. Without these, panels feel static even when dramatic growth is happening. Render those cues as physical scene elements, not as 2D overlays.

Include this in EVERY transformation/growth prompt — paste it directly, do not summarize or skip:
```
In-scene SFX: the words "RRRRIP" (positioned near the tearing fabric), "CRACK" (positioned where seams are splitting), and "THROB" or "PULSE" (positioned near swelling muscles) appear as 3D-extruded chrome letter sculptures sitting in the scene as physical objects. Each casts a real ray-traced shadow on the nearest surface and catches the same warm rim light as the rest of the render. Motion in the scene is told through physical cues — sweat beading and flying, fabric fibers tearing, fine dust kicked up by the expansion, subtle motion blur on the growing region — NOT through 2D action-line overlays.
```

When to include in-scene SFX:
- Any panel where muscles are growing: **YES, ALWAYS**
- Any panel where clothes are tearing: **YES, ALWAYS**
- Any panel where breasts are swelling: **YES, ALWAYS**
- Any panel where the character is flexing and showing off: **YES**
- Post-transformation dialogue-only panels: No (but still include if muscles are at peak size and being shown off)

---

## Dialogue Formatting

> **Active — applies whenever you bake a bubble (the default for CGI panels per L19).** Speech bubbles, thought bubbles, and caption boxes are written into the generation prompt as **physical 3D scene objects** — photoreal semi-translucent floating panels with extruded text and tails pointing at speakers — not as flat 2D comic overlays. Pair every baked bubble with **L4**'s positioning rules: bubble shape (`white speech bubble` / `jagged-edged for yelling` / `wavering broken-edged for weak voice` / `rectangular yellow caption box for narration`), position in frame, tail direction, exact text in quotes, and per-speaker attribution. The `dialogue[]` / `captions[]` arrays in `shotlist.json` remain the source of truth for *what is said*; this section describes *how the bubble renders in the photoreal scene*. The short-form shorthand below still composes correctly, but for CGI panels prefer the long-form phrasing (it survives the model's "speech bubble → comic illustration" association better).

Short form (legacy shorthand — readable, but the model often renders this as a flat 2D bubble):

```
Comic speech bubble — JILL: "Exact line of dialogue here."
Comic speech bubble — ROCHELLE: "Her exact line here."
Comic thought bubble — ROCHELLE'S THOUGHTS: "Her internal monologue here."
Comic text box: "Narration or scene setting text here."
```

Long form (CGI / L19 — bakes the bubble as a physical 3D object so it holds the photoreal register):

```
In-scene speech bubble: a photoreal semi-translucent white 3D panel with rounded edges and an extruded tail, floating in the [upper-left / upper-right / lower-left / lower-right] of the frame. Slightly glossy surface with subtle subsurface scattering. The tail extends [direction], pointing to [SPEAKER]'s mouth. Black extruded sans-serif text on the surface reads exactly: "[DIALOGUE]". A physical object in 3D space, casting a real shadow on [background surface].
```

For multi-character panels, list each bubble separately. Be explicit about which character is on which side of the frame and who is speaking — this directly affects where the model places the speech bubbles. Per **L4**, also vary bubble shape to match the line (jagged for yells, wavering for weak voices, rectangular yellow caption box for narration), and give each tail an explicit direction so attribution is unambiguous.

---

## Background Character Reactions

Use this whenever something dramatic is happening and background characters are present:

```
Background characters react visibly to the impossible scene unfolding — wide eyes, open mouths, hands raised to faces in shock, some stumbling backward, some pointing. No one in the background stands neutrally — every person within sight is reacting with genuine stunned disbelief.
```

This matters because the model defaults to neutral bystanders during dramatic moments, which breaks immersion badly. If all characters of a group have transformed, say so explicitly: "All [N] characters are [transformed state] — there are NO normal-sized characters anywhere in this scene."

---

## Environment Description Examples

Use these as templates. Replace details to match your story's locations. The key is specificity — generic descriptions produce generic, inconsistent rooms.

### Science lab
```
College science laboratory interior — long white bench counters running the length of the room, beakers and test tubes and bunsen burners covering every surface, two coffee cups visible on the right bench, overhead fluorescent lighting, clinical white walls, faint blue glow from computer screens, DAZ3D Iray render.
```

### Home kitchen (morning)
```
Nice suburban kitchen interior — round wooden breakfast table with a plate of donuts, morning sunlight coming through a window above the sink, warm wood cabinets, granite countertops, coffee maker on the counter, cheerful and domestic, DAZ3D Iray render.
```

### Upscale living room
```
Upscale modern living room — large flat screen TV on the wall, long grey sectional sofa, glass coffee table, warm ambient lighting, city view through floor-to-ceiling windows, tasteful and expensive looking, DAZ3D Iray render.
```

### Bedroom
```
Modern bedroom — king bed with white linen, bedside tables with lamps, warm evening light, curtains partially drawn, wooden floor, DAZ3D Iray render.
```

### Sports field sideline
```
College football field sideline — green turf stretching to the horizon, large orange sports drink cooler/dispenser on a folding table, bleachers packed with spectators in the background, afternoon sun casting long shadows, goalposts visible in the distance, DAZ3D Iray render.
```

### Locker room
```
College sports locker room interior — rows of metal lockers, wooden benches running between them, overhead fluorescent lighting, tiled floor, motivational banners on the walls, DAZ3D Iray render.
```

### Campus exterior
```
College campus exterior — red brick academic buildings, wide stone paths, mature trees lining the walkways, students crossing in the background, clear daytime sky, DAZ3D Iray render.
```

> **Note (post-L7):** for hero locations that recur across multiple panels, also see `environment-references.md` — the DAZ3D-scene-reference trick (source a real DAZ3D-rendered scene, attach it as an env ref + transform instructions). Produces dramatically more consistent location anchoring than text-only environment descriptions.

---

## Character Size Reference Language

Use these consistently to describe each character's transformation stage so the model understands the intended scale:

| Stage | Description to use in prompt |
|---|---|
| Baseline (soft/untrained) | "slightly out of shape, soft figure, no visible muscle definition, normal breasts" |
| Baseline (fit/athletic) | "fit and athletic, visible muscle tone, competitive bodybuilder level fitness, normal breasts" |
| First transformation | "noticeably muscular, arms and shoulders clearly defined, clothes tight and straining, breasts noticeably enlarged and pressing against fabric" |
| Super transformation | "hugely muscular, female competitive bodybuilder size or larger, clothes torn and barely holding, large prominent breasts with deep visible cleavage overflowing any remaining fabric" |
| Ultra / Goddess level | "impossibly massive, muscles beyond any human scale, towering and overwhelming, clothes completely destroyed, dominant presence filling the frame, absolutely enormous breasts — massive, prominent, impossible to miss, with deep cleavage" |

After a character transforms, include their current stage description in every subsequent panel prompt. The model reverts to the reference image's body type if you don't explicitly state the character has grown.

**CRITICAL — Breast Size in Later Panels:** From the midpoint of any transformation story onward, ALWAYS use at minimum the "Super transformation" breast description or larger. Never drop below it. The model has a strong tendency to revert breasts to baseline size even when muscles remain large. You must explicitly state the current breast size in every single panel — do not rely on the reference image alone.

---

## Prompt Modifications That Help

- For back/shoulder shots, standard portrait ratios (2:3) can be too narrow. Switch to **4:5** and add width emphasis language: "incredibly wide taking up most of the frame", "enormous lats that flare dramatically", "filling the width of the frame"
- To anchor muscle size to a previous panel, reference it explicitly: "at the muscle size shown in reference image [N]"
- For NSFW filter avoidance: "swimsuit" triggers less than "bikini". Bare skin (back/shoulder scenes) may get flagged — expect some images to be filtered and plan for 1-2 usable out of 4
- **Anatomy safety net**: If a panel keeps generating extra legs despite the mandatory rules block, add this as a separate reinforcement line near the end of the prompt: `IMPORTANT: This character has exactly TWO legs. Do not generate a third or fourth leg under any circumstances.`
- **Breast size safety net**: If breasts keep reverting despite the mandatory rules block, add this near the character description: `[CHARACTER]'s breasts are at their MAXIMUM enlarged size — they have already grown and must NOT be drawn smaller than in the previous panel.`
