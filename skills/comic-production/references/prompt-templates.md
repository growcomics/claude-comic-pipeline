# Prompt Templates
## Reusable Prompt Fragments for Higgsfield Comic Production

> **STATUS: Active — updated for L19 (May 16, 2026 rewrite).** Last reviewed 2026-05-16.
>
> Per **L19** in `lessons-learned.md`, speech bubbles, captions, and SFX text are baked **directly into the generation prompt** as **flat 2D comic-book overlay graphics** composited onto the photoreal CGI scene. The 2D style is **scope-bounded explicitly to the bubble / caption / SFX graphics** — the bodies, costumes, skin, hair, environment, and lighting stay photoreal CGI. This defuses L7 Case B's failure mode (comic-coded vocab pulling the whole panel to 2D) by naming the scope of the 2D style rather than letting it bleed.
>
> The fix is three load-bearing pieces:
>
> 1. **Open every CGI prompt with concrete render-engine vocabulary** — *"Hyperrealistic DAZ3D Studio 3D CGI render, ray-traced subsurface scattering on skin, physically-based rendering, 8K texture detail, photographic CGI."*
> 2. **Inject the L19 lettering block** whenever the panel has dialogue, captions, or SFX. Bubbles render as flat 2D vector graphics — clean white rounded ovals with bold black outlines, comic display font ALL CAPS text, triangular tails to speakers. Captions render as yellow rounded rectangles with black outlines. SFX renders as flat 2D comic-style ALL CAPS text. **No 3D extrusion, no chrome, no semi-translucent floating panels, no ray-traced shadows on the scene from the bubble graphics.**
> 3. **Close every prompt with scope-bounded negation** — *"Photographic CGI render on the bodies, costumes, skin, hair, environment, and lighting; NOT a 2D illustration on the bodies, NOT cartoon-shaded skin. Only the bubble / caption / SFX graphics are flat 2D comic-book overlay."*
>
> **Auto-emission**: `next_panel.py` `_l19_lettering_block()` builds this block per panel from the shotlist's `dialogue[]` / `captions[]` / `sfx[]` arrays. You should not hand-author the L19 block per panel — let the composer do it. The phrasings below are the source-of-truth vocabulary the composer uses; reference them when authoring shotlist content (bubble types, caption text, SFX text + scale) so the auto-emitted prompt holds together.
>
> **Historical note**: L19's vocabulary evolved across three iterations. **(a)** Pre-L19 (and L7 Case B's original prescription): never bake lettering, defer all to `page-composer` vector overlay. Produced "sticker on top" look. **(b)** L19 introduced 2026-05-13: bake lettering as **physical 3D scene objects** (chrome-extruded SFX, semi-translucent photoreal floating speech panels). Held photoreal CGI but produced 3D bubbles that didn't match classic comic lettering. **(c)** L19 rewritten 2026-05-16 (current): bake as **flat 2D overlay graphics** with the 2D scope explicitly bounded to lettering only. Test render validating the new vocabulary: job `607cf047-23d2-453e` (May 16, two-character dialogue panel, photoreal CGI bodies + 2D comic bubbles + yellow caption box, no 2D drift on the body/scene).
>
> Section-by-section status (in this file):
>
> - **Mandatory Rules Block** — *active*. All ten rules apply. The per-speaker attribution and per-bubble-unique-line discipline matter because bubbles are baked.
> - **Action Lines and SFX** — *active, rewritten for the 2026-05-16 L19*. SFX text IS baked into the prompt, but rendered as **flat 2D comic-style ALL CAPS lettering with a solid black outline**, NOT as 3D-extruded chrome letter sculptures (the older 2026-05-13 prescription) and NOT as "action lines radiating outward" (the original 2D-comic-burst prescription that was a confirmed L7 Case B failure mode). See the section below.
> - **Dialogue Formatting** — *active, rewritten for the 2026-05-16 L19*. Speech bubbles, thought bubbles, and caption boxes are written into the generation prompt as **flat 2D comic-book overlay graphics** (per L19), with bubble shape, position, tail direction, and per-speaker attribution per **L4**'s rules. The `dialogue[]` / `captions[]` arrays in `shotlist.json` remain the source of truth for *what is said*; the prompt block describes *how the bubble renders as flat 2D overlay on the photoreal scene*.
>
> See the **L19 worked example** in `lessons-learned.md` § L19 and the **CHANGELOG 2026-05-16 entry** for the canonical skeleton (opening render-engine anchor → camera → subject + tier muscular build → action delta → wardrobe delta → L19 lettering block (auto-emitted) → environment delta → closing scope-bounded negation) and the rule-to-section mapping.

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

> **Active — all ten rules.** Per **L19** (May 16, 2026 rewrite), classic 2D comic-book lettering is baked into the CGI render with the 2D scope explicitly bounded to bubble/caption/SFX graphics; the bodies and scene stay photoreal CGI. The dialogue lines below apply alongside the rest of the block. Paste the full block — and pair it with the L19 opening render-engine anchor and the closing scope-bounded negation block: *"Photographic CGI render on the bodies, costumes, skin, hair, environment, and lighting; NOT a 2D illustration on the bodies, NOT cartoon-shaded skin. Only the bubble / caption / SFX graphics are flat 2D comic-book overlay."*

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

> **Active — rendering language updated for L19 (May 16, 2026 rewrite).** SFX text IS baked into the generation prompt, but rendered as **flat 2D comic-style ALL CAPS lettering with a solid black outline** — classic comic-book SFX overlay graphics composited onto the photoreal scene, NOT 3D-extruded chrome letter sculptures (the 2026-05-13 prescription) and NOT "radiating action lines" / "red and yellow burst text" (the original L7 Case B failure mode confirmed in the Chun-Li growth series). Pair the SFX with the L19 opening render-engine anchor and the closing scope-bounded negation — see the file header.

**CRITICAL: In-scene SFX MUST be included in EVERY panel where growth or transformation is occurring. These are NOT optional. Skipping them makes growth panels look static and lifeless. Include this block in every growth panel — no exceptions.** (The `next_panel.py` composer auto-emits SFX from `panel.sfx[]` in the shotlist; the rule here is to populate `sfx[]` for every growth panel.)

Transformation scenes must include visual storytelling cues that help the reader's eye focus on what's changing. Render the SFX as flat 2D comic-book lettering overlaid on the photoreal scene; render the physical motion cues (sweat beading, fabric fibers tearing, motion blur on the growing region) as part of the photoreal render itself.

Include this in EVERY transformation/growth prompt — paste it directly, do not summarize or skip (or populate `sfx[]` and let `_l19_lettering_block()` emit it for you):
```
SFX (flat 2D comic-book overlay): the words "RRRRIP" (positioned near the tearing fabric), "CRACK" (positioned where seams are splitting), and "THROB" or "PULSE" (positioned near swelling muscles) rendered as bold flat 2D comic-book lettering overlaid on the scene — bold black or yellow comic display font ALL CAPS, with a solid black outline. Flat 2D vector lettering only — NO 3D extrusion, NO chrome letter sculptures, NO ray-traced shadows on the scene. The SFX is part of the comic-lettering overlay layer, not the photoreal layer. Separately, in the photoreal render itself: sweat beading and flying, fabric fibers tearing, fine dust kicked up by the expansion, subtle motion blur on the growing region.
```

When to include in-scene SFX:
- Any panel where muscles are growing: **YES, ALWAYS**
- Any panel where clothes are tearing: **YES, ALWAYS**
- Any panel where breasts are swelling: **YES, ALWAYS**
- Any panel where the character is flexing and showing off: **YES**
- Post-transformation dialogue-only panels: No (but still include if muscles are at peak size and being shown off)

---

## Dialogue Formatting

> **Active — applies on every CGI panel with dialogue/captions per L19 (May 16, 2026 rewrite).** Speech bubbles, thought bubbles, and caption boxes are written into the generation prompt as **flat 2D comic-book overlay graphics** — clean white rounded ovals with bold black outlines, comic display font ALL CAPS text, triangular tails pointing at speakers. **NOT physical 3D scene objects** (the older 2026-05-13 prescription, which produced literal-3D bubbles that don't match classic comic lettering). The 2D scope is explicitly bounded to the bubble graphics; the bodies and scene stay photoreal CGI. Pair every baked bubble with **L4**'s positioning rules: bubble shape per dialogue type, position in frame, tail direction, exact text in quotes, and per-speaker attribution.
>
> **You should not hand-author the L19 lettering block per panel.** Populate `dialogue[]` / `captions[]` / `sfx[]` in `shotlist.json` and let `_l19_lettering_block()` emit the prompt block automatically. The phrasings below are reference: the source-of-truth vocabulary the composer uses + the bubble-shape table per dialogue type.

### Bubble shape per `dialogue[].type`

| `type` | Shape |
|---|---|
| `balloon` | clean white rounded oval with a bold 3-4 pixel solid black outline |
| `thought` | clean white cloud-shaped outline with a bold solid black border, small cloud-bubble trail of three round dots leading to the thinker |
| `whisper` | clean white rounded oval with a thin DASHED black outline (broken/dashed, not solid) |
| `shout` | white JAGGED-EDGED starburst shape with a bold solid black outline (spiky/zig-zag, not smooth) |
| `off-panel` | standard rounded-oval shape but drawn at the edge of the frame, tail pointing OFF the panel |

Captions (separate `captions[]` array, not `dialogue[]`): yellow rounded-corner rectangle with a bold 3-4 pixel solid black outline, sitting at the bottom edge of the panel.

Text inside every bubble / caption: **bold black sans-serif comic display font ALL CAPS (Bangers-style lettering), no shading, no extrusion.**

### Long form (L19 May 16 — what the composer emits)

If you must hand-author (e.g. one-off override), use this exact phrasing — it's what the test render validated:

```
Bubble: classic comic-book speech balloon — clean white rounded oval shape
with a bold 3-4 pixel solid black outline, positioned [upper-left /
upper-right / lower-left / lower-right] over [SPEAKER]'s side of the frame
so the tail attribution is unambiguous; short triangular black-outlined
tail pointing directly to [SPEAKER]'s mouth. Bold black sans-serif comic
display font ALL CAPS text inside (Bangers-style lettering, no shading,
no extrusion) reads exactly: "[DIALOGUE]". Flat 2D vector graphic — NO 3D
shading, NO bevel/extrusion, NO translucency, NO chrome, NO drop shadow
onto the scene.
```

```
Caption box: classic comic-book caption — yellow rounded-corner rectangle
with a bold 3-4 pixel solid black outline, positioned at the bottom edge
of the panel. Bold black sans-serif comic display font ALL CAPS text
inside reads exactly: "[CAPTION TEXT]". Flat 2D vector graphic — NO 3D
shading, NO bevel, NO drop shadow on the scene.
```

### Short form (legacy shorthand — DO NOT USE for CGI panels)

```
Comic speech bubble — JILL: "Exact line of dialogue here."
Comic text box: "Narration or scene setting text here."
```

This shorthand was used pre-L19. It still composes but it does NOT bound the 2D scope — the model is likely to interpret "comic" as ambient and pull the whole panel toward 2D illustration (the L7 Case B failure mode). Use the L19 long form OR populate the shotlist and let `_l19_lettering_block()` emit the long form for you.

For multi-character panels, the composer emits one bubble fragment per dialogue entry in shotlist array order, each with explicit position and tail direction. Be explicit in the shotlist about speaker IDs — `dialogue[].speaker` must match a `cast[].id` so attribution is unambiguous. Per **L4**, vary bubble shape to match the line type (`shout` for yells, `whisper` for soft voices, `thought` for internal monologue) — the composer reads `type` per entry and emits the right shape.

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
