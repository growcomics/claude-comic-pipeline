# Prompt Templates
## Reusable Prompt Fragments for Higgsfield Comic Production

> **STATUS: PARTIALLY DEPRECATED — read before using.** Last reviewed 2026-05-11.
>
> Three sections in this file pre-date the discovery of **L7 Case B** in `lessons-learned.md` (lettering and SFX baked into the generation prompt cause 2D illustration drift in CGI panels — confirmed in the Chun-Li growth series). The following sections in THIS file conflict with that rule and are **DEPRECATED for any CGI / photoreal pipeline** (i.e., when `page-composer` will letter the panel post-render):
>
> - **Mandatory Rules Block** — the *speech bubble* and *dialogue* lines are obsolete (see L4 and L7 Case B). Specifically: drop "Speech bubbles show exactly the correct character speaking their correct line" and "Every speech bubble contains a unique line" from the rules block. The muscle-color / breast-persistence / clothing / expressive-faces / no-camera-eye-contact / anatomy / muscle-continuity rules are all still valid.
> - **Action Lines and SFX — MANDATORY FOR ALL GROWTH PANELS** — the whole section is now wrong. Comic-style SFX text ("RRRRIP!", "CRACK!", "THROB") baked into the generation prompt is exactly what causes L7 Case B 2D drift. SFX/action lines belong in `page-composer` post-render. If a dramatic splash genuinely needs in-render SFX, render it as a **physical scene object** (3D-extruded letters in the scene with real shadows) per the "After (held photoreal CGI)" example in L7 Case B's worked example.
> - **Dialogue Formatting** — obsolete. Speech bubbles, thought bubbles, and captions are NOT written into the generation prompt. They live in `shotlist.json`'s `dialogue[]` / `captions[]` arrays and are placed as vector overlays by `page-composer`.
>
> **What's still useful below**: Style Prefix (note: also see the newer CGI vocabulary in `cinematic-framing.md` and `environment-references.md` for chained sequential comics), Shot Types, Transformation Scene Templates Panels A–E (but drop the "Action Lines and SFX" appendage), Background Character Reactions, Environment Description Examples, Character Size Reference Language, Prompt Modifications That Help.

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

> ⚠️ **PARTIALLY DEPRECATED.** Per L4 and L7 Case B, the speech-bubble and dialogue lines below must NOT be included in any prompt where `page-composer` is doing the lettering. The other rules in this block (muscle color, breast persistence, clothing, expressive faces, no-camera-eye-contact, anatomy, muscle/breast continuity) are still valid. When pasting this block, edit out the obsolete lines first.

Paste this at the end of every panel prompt. Every rule, every time. The model has no memory between generations — it treats each panel as a fresh request. Rules from a previous panel's prompt do not carry forward.

```
Muscles are natural healthy skin tone — NOT red, NOT inflamed. Skin is wet, shiny, glistening with effort, like oiled skin catching warm light. Excellent muscle definition and visible tone throughout. Any character with enlarged muscles also has proportionally enlarged, full breasts with prominent cleavage visible — muscle growth and breast growth always occur together, and breasts NEVER shrink or revert to a smaller size once they have grown. All characters fully clothed at all times — clothes may be torn, stretched, or splitting at seams from muscle growth but always cover the body. Speech bubbles show exactly the correct character speaking their correct line — never the wrong character. Every speech bubble contains a unique line — no character repeats themselves. Every character has a vivid, animated, expressive face — mouth open mid-speech, gasping, laughing, or wide-eyed, never neutral or blank. All characters look at each other, never at the camera. Correct human anatomy — exactly two arms and exactly two legs per person, no extra limbs, no duplicate limbs, no third or fourth leg. Once a character has grown muscles they stay at that size or larger in all subsequent panels — muscles never revert. Once breasts have grown they stay at that size or larger — breasts never revert or shrink.
```

Why each rule exists:
- **Muscle color**: Without this, the model renders muscles as red/inflamed during growth. The "wet, shiny, glistening" language gives it a positive visual alternative to "straining."
- **Muscles = breasts**: The model won't add both unless told. Every time.
- **Breast persistence**: The model reverts breasts to the base reference size unless explicitly told they've grown AND told they must not shrink. This is stated twice (growth rule + revert rule) because a single mention is often ignored.
- **Clothing**: Prevents nudity while allowing dramatic clothing destruction.
- **Dialogue attribution** *(⚠️ deprecated per L7 Case B — lettering goes to `page-composer`)*: The model decides bubble placement based on character positioning. Without explicit attribution, bubbles end up above the wrong character.
- **No repeated dialogue** *(⚠️ deprecated per L7 Case B)*: Without this, characters echo each other or repeat lines across panels.
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

> ⚠️ **DEPRECATED** — this entire section is now obsolete per L7 Case B in `lessons-learned.md`.
>
> Comic-style SFX text ("RRRRIP!", "CRACK!", "THROB") and "action lines radiating outward" baked into the generation prompt are exactly what causes 2D illustration drift in CGI panels. Confirmed failure mode in the Chun-Li growth series panels 3/4/5.
>
> The correct workflow is:
> 1. **Render clean, lettering-free panels** with the visual storytelling cues coming from physical scene elements only (sweat, fabric strain, dust, motion blur, particle effects baked into the lit scene — described in non-comic-coded language).
> 2. **Add SFX and action lines as vector overlays in `page-composer`** post-render. This is also where speech bubbles, captions, and dialogue go.
> 3. **If a dramatic splash truly needs in-render SFX** (rare), render it as a **physical scene object**: *"In the scene, the SFX word 'BWOOM' appears as a 3D-extruded chrome letter sculpture sitting in the scene as a physical object, casting a real ray-traced shadow on the ground and catching the same warm rim light as the rest of the render."* — see L7 Case B's worked example.
>
> The text below is preserved for historical reference only. Do NOT paste it into prompts.

**CRITICAL: Action lines and SFX text MUST be included in EVERY panel where growth or transformation is occurring. These are NOT optional. They are NOT a nice-to-have. Skipping them makes growth panels look static and lifeless. Include this block in every growth panel — no exceptions.**

Transformation scenes must include visual storytelling cues that help the reader's eye focus on what's changing. Without these, panels feel static even when dramatic growth is happening.

Include this in EVERY transformation/growth prompt — paste it directly, do not summarize or skip:
```
Action lines radiating outward from the growing [body part], emphasizing the explosive expansion. SFX text like "RRRRIP!" near tearing fabric, "CRACK!" for seams splitting, "THROB" or "PULSE" near swelling muscles. These visual effects draw the reader's eye to the focal point of the transformation.
```

When to include action lines and SFX:
- Any panel where muscles are growing: **YES, ALWAYS**
- Any panel where clothes are tearing: **YES, ALWAYS**
- Any panel where breasts are swelling: **YES, ALWAYS**
- Any panel where the character is flexing and showing off: **YES**
- Post-transformation dialogue-only panels: No (but still include if muscles are at peak size and being shown off)

---

## Dialogue Formatting

> ⚠️ **DEPRECATED** — speech bubbles, thought bubbles, and caption boxes are NOT written into the generation prompt per L4 (deprecated) and L7 Case B in `lessons-learned.md`. They live in `shotlist.json`'s `dialogue[]` and `captions[]` arrays and are placed by `page-composer` as vector overlays. The text below is preserved for historical reference only.

Always write dialogue in this format inside prompts:

```
Comic speech bubble — JILL: "Exact line of dialogue here."
Comic speech bubble — ROCHELLE: "Her exact line here."
Comic thought bubble — ROCHELLE'S THOUGHTS: "Her internal monologue here."
Comic text box: "Narration or scene setting text here."
```

For multi-character panels, list each line separately. Be explicit about which character is on which side of the frame and who is speaking — this directly affects where the model places the speech bubbles.

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
