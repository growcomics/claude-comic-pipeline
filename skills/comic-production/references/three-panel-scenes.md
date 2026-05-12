# Three-Panel Scene Prompt Templates

Reference file for automatically generating 3-panel transformation sequence prompts.
All prompts use DAZ3D CGI style unless marked [PHOTO].

---

## How to Use This File

Each template has:
- **Placeholders** in `[BRACKETS]` — fill these in before generating
- **Orientation** — horizontal (side by side) or vertical (stacked top to bottom)
- **Focus** — what is transforming across the three panels
- **Rules block** — mandatory rules appended to every prompt

When building a prompt automatically:
1. Pick the correct template for the scene type
2. Fill in all `[BRACKET]` placeholders
3. Apply any modifiers from the Modifiers section at the bottom
4. Append the correct Rules Block for the style (CGI or Photo)

---

## Style Anchoring — Read This First

These templates were rewritten after a real failure mode (see `lessons-learned.md` L7): the original phrasings caused Nano Banana 2 to drift into 2D / illustration / comic-art aesthetics, despite the prompt explicitly saying "NOT illustration, NOT anime, NOT cartoon, NOT 2D drawn art." Three things were pulling the model toward illustration:

1. **"Comic SFX"** + ascending text overlays — maps directly to comic-book illustration training data.
2. **"Three-panel sequence"** with gutters — itself an illustration convention; CGI renders aren't normally structured this way.
3. **Stacked negations** — image models obey *described* concepts more reliably than *forbidden* ones. A list of four "NOT X" phrases gives the model four illustration concepts to think about.

Every template below is written in the corrected style:

- **Positive CGI anchoring up front**: render-engine vocabulary (DAZ Studio Iray, ray-traced subsurface scattering, specular highlights, photographic depth of field, 8K texture detail) — the model has a concrete photoreal target.
- **"Triptych" instead of "three-panel sequence"**: same layout — three side-by-side frames separated by thin black borders — but the vocabulary doesn't trigger comic-art training data.
- **"Frame 1 / Frame 2 / Frame 3"** instead of "PANEL 1 / PANEL 2 / PANEL 3": same idea, less comic-coded.
- **One concise negation only**: a single closing "Photographic CGI render, NOT illustrated." One negation lands; four dilute each other.
- **No comic SFX in the default templates**: SFX is opt-in via a modifier at the bottom, and the modifier requires it to be rendered as 3D-extruded letters with realistic lighting (so it exists as a physical object in the scene rather than an overlay).

If a template ever produces flat/illustrated output anyway, check the section "When 2D drift still happens" at the bottom for additional fixes.

---

## Cumulative State — Beats Within a Longer Comic

By default, every template starts the character at **baseline** for the body part being grown. That's correct for the **first** growth beat in a comic. For **later** beats — bicep growth that follows breast growth, ass growth that follows bicep growth, etc. — the prior beats' results must persist, otherwise the reader sees grown features visibly *un-grow* as the next beat begins.

**The rule**: all non-currently-growing features stay at their cumulative post-prior-beats size across **ALL three frames** of the new beat. Only the currently-growing feature changes across frames.

This works without consistency issues — see `lessons-learned.md` L8 for the full mechanism. The model handles "breasts already large, bicep growing from baseline" cleanly because each frame in the triptych is composed independently — cumulative state is just additional spatial information per frame, not a temporal dependency.

### How to apply

Add a **"CARRY FORWARD STATE"** block near the top of the scene description, before the per-frame breakdown. Spell out which features stay constant and at what size, and explicitly say they do NOT change across frames.

**Example — bicep beat following a prior breast growth scene**:

```
CARRY FORWARD STATE (constant and identical across ALL three frames — do not 
change between frames): [CHARACTER NAME]'s breasts are ALREADY at WOMAN 
NUMBER 5 size from a prior growth scene — large, full, with prominent 
cleavage straining the [GARMENT]. The [GARMENT]'s chest panels are already 
stretched tight from the prior growth. Breast size and chest fabric state are 
IDENTICAL in frame 1, frame 2, and frame 3 — only the bicep is growing.
```

**Example — quad beat following breast + bicep + glute growth (third or later beat)**:

```
CARRY FORWARD STATE (constant and identical across ALL three frames — do not 
change between frames): Breasts at WOMAN NUMBER 5, biceps at WOMAN NUMBER 5 
(visibly massive arms, sleeve already shredded at shoulders from prior 
growth), glutes at WOMAN NUMBER 5 (visibly enlarged from prior growth, qipao 
already split at the back side slits). All carry-forward features are 
IDENTICAL in frame 1, frame 2, and frame 3 — only the quad is growing.
```

### Frame-by-frame language adjustment

In the per-frame breakdown, restate the carry-forward features each time you describe the growing feature, e.g. *"Frame 2: bicep grapefruit-sized. Chest UNCHANGED from frame 1 — still size 5."* The repetition costs prompt tokens but reliably keeps the carry-forward features stable. Without this, the model occasionally drifts the carry-forward features as it processes the active growth.

### When this DOESN'T apply

- The first growth beat in a comic — use the standard templates as-is.
- Standalone three-panel beats with no prior context.
- Beats where each scene shows an independent character or alternate-reality showcase (no shared continuity).

### Relationship to Template 6

Template 6 ("Pre-Grown Muscles + Breast Growth") is the specific case of "prior arm growth + currently-growing breasts." The cumulative-state rule above is the **general** version: any combination of prior-grown features + any currently-growing feature, applied to any template. Use Template 6 if the specific case matches; use the cumulative-state modifier with any template otherwise.

---

## Template 1: Bicep Growth — Single Character

**Orientation:** Horizontal (left to right)
**Focus:** One character's bicep growing across three frames

```
DAZ Studio Iray render of a real 3D scene. Ray-traced subsurface scattering on 
skin, specular highlights catching warm rim light, physically-accurate fabric 
weave with visible thread detail, 8K texture detail, shallow depth of field 
with photographic bokeh. Photographic CGI render, NOT illustrated.

TWO REFERENCES: First reference is the CHARACTER — match [CHARACTER NAME]'s face 
and identity. Second reference is the SIZE CHART — match body to WOMAN NUMBER [1–6].

Single image rendered as a TRIPTYCH — three side-by-side photographic frames of 
the same scene at three progressive moments, separated by thin black borders. 
Each frame is a fully photoreal CGI render in the same style.

Subject across all three frames: EXTREME CLOSEUP of [CHARACTER NAME]'s right 
bicep MID-GROWTH. Frame 1 (left): bicep softball-sized, [ACCESSORY] on her 
forearm intact, sleeve still whole. Frame 2 (middle): bicep grapefruit-sized, 
sleeve splitting at the shoulder seam, [ACCESSORY] cracking from forearm 
growth. Frame 3 (right): bicep larger than her head, sleeve fully torn at the 
shoulder, [ACCESSORY] shattered with shards mid-air. Skin glistening, 
stretched tight over expanding muscle.

[RULES BLOCK — CGI]
```

---

## Template 2: Bicep Growth — Three Characters Interacting

**Orientation:** Horizontal (left to right)
**Focus:** All three characters growing simultaneously, engaging with each other

```
DAZ Studio Iray render of a real 3D scene. Ray-traced subsurface scattering on 
skin, specular highlights, physically-accurate fabric weave, 8K texture detail, 
shallow depth of field with photographic bokeh. Photographic CGI render, 
NOT illustrated.

THREE REFERENCES: First reference is CHARACTER 1 — match [CHARACTER 1 NAME]'s 
face and identity. Second reference is CHARACTER 2 — match [CHARACTER 2 NAME]'s 
face and identity. Third reference is CHARACTER 3 — match [CHARACTER 3 NAME]'s 
face and identity.

Single image rendered as a TRIPTYCH — three side-by-side photographic frames of 
the same scene at three progressive moments, separated by thin black borders. 
Each frame is a fully photoreal CGI render in the same style. WIDE SHOT showing 
all three women side by side. All three characters are visible and interacting 
with each other in EVERY frame. Characters look at each other, react to each 
other, never at the camera.

Frame 1 (left): All three women standing together. [CHARACTER 1] is in the 
center raising her right arm into a flex, showing off to the others. 
[CHARACTER 2] on her left is leaning in to look at the bicep, eyebrows raised 
with curiosity. [CHARACTER 3] on her right is pointing at the arm with a 
surprised expression. All three making eye contact with each other. Biceps 
softball sized, just beginning to swell. Clothes beginning to tighten around 
the arms.

Frame 2 (middle): All three biceps noticeably larger — grapefruit sized, still 
growing. [CHARACTER 1] center laughing with delight at her own growing arm, 
turning her head to look at [CHARACTER 2]. [CHARACTER 2] grabbing 
[CHARACTER 1]'s arm with both hands in disbelief, eyes wide staring at the 
swelling muscle. [CHARACTER 3] stepping back with hands raised in shock, eyes 
darting between both other women. Sleeves splitting on all three. Teal energy 
crackling around all three.

Frame 3 (right): All three biceps massively enormous — bigger than their heads. 
[CHARACTER 1] center doing a full double bicep flex, head thrown back laughing 
triumphantly, glancing sideways at [CHARACTER 3]. [CHARACTER 2] flexing her 
own enormous arm next to [CHARACTER 1], the two bumping their flexed biceps 
together in celebration, both grinning wide at each other. [CHARACTER 3] 
staring at her own massive arm in pure disbelief, holding it up and looking 
directly at it, mouth wide open in a yell. All three women's sleeves completely 
destroyed, fabric shredded at the shoulders.

[RULES BLOCK — CGI]
```

---

## Template 3: Breast Growth — Horizontal, Face Always Visible

**Orientation:** Horizontal (left to right)
**Focus:** Breast growth with face visible in every frame

```
DAZ Studio Iray render of a real 3D scene. Ray-traced subsurface scattering on 
skin, specular highlights catching warm rim light, physically-accurate fabric 
weave with visible thread detail, 8K texture detail, shallow depth of field 
with photographic bokeh. Photographic CGI render, NOT illustrated.

TWO REFERENCES: First reference is the CHARACTER — match [CHARACTER NAME]'s face 
and identity. Second reference is the SIZE CHART — match body to WOMAN NUMBER [1–6].

Single image rendered as a TRIPTYCH — three side-by-side photographic frames of 
the same scene at three progressive moments, separated by thin black borders. 
Each frame is a fully photoreal CGI render in the same style. Camera angle is 
consistent across all three frames — MEDIUM SHOT from chest up of 
[CHARACTER NAME]. Face fully visible in every frame, never cropped, never cut 
off. Eyes never directly at camera — looking off-frame in shocked reaction.

Subject across all three frames: progressive breast growth.

Frame 1 (left): Starting size. Clothing intact. Face shows first hint of 
surprise — brows slightly raised, eyes widening, mouth just beginning to open.

Frame 2 (middle): Noticeably larger. Fabric visibly stretching and pulling 
tight. Face shows growing shock — brows fully arched, eyes wide open, mouth 
open in a gasp, head tilting back slightly.

Frame 3 (right): Massively enlarged. Fabric bursting at seams, deep cleavage 
exposed but still framed by the bursting fabric. Face shows peak reaction — 
eyes wide, mouth fully open in a loud exclamation, cheeks flushed, head 
thrown back.

[RULES BLOCK — CGI]
```

---

## Template 4: Breast Growth — Vertical, Escalating Effects

**Orientation:** Vertical (top to bottom, smallest at top)
**Focus:** Breast growth with increasing visual effects per frame

```
DAZ Studio Iray render of a real 3D scene. Ray-traced subsurface scattering on 
skin, specular highlights, physically-accurate fabric weave with visible thread 
detail, 8K texture detail, shallow depth of field with photographic bokeh. 
Photographic CGI render, NOT illustrated.

TWO REFERENCES: First reference is the CHARACTER — match [CHARACTER NAME]'s face 
and identity. Second reference is the SIZE CHART — match body to WOMAN NUMBER [1–6].

Single image rendered as a VERTICAL TRIPTYCH — three stacked photographic frames 
of the same scene at three progressive moments, separated by thin black 
borders, smallest on top, largest on bottom. Each frame is a fully photoreal 
CGI render in the same style.

Subject across all three frames: EXTREME CLOSEUP of [CHARACTER NAME]'s chest, 
breasts actively swelling larger from top to bottom.

TOP FRAME: Starting size. No effects. Clean fabric, slight tension lines 
beginning.

MIDDLE FRAME: Noticeably larger. Skin glistening, fabric creasing hard under 
strain, seam threads visibly pulling. Faint warm glow effect along the edges.

BOTTOM FRAME: Massively enlarged. Skin wet and shiny, fabric torn open at 
center revealing deep cleavage, soft radial light burst emanating outward, 
photographic motion blur on expanding flesh, sweat droplets mid-air. Face 
visible — eyes wide open, brows arched high, mouth fully open in a gasp.

[RULES BLOCK — CGI]
```

---

## Template 5: Ass Growth — Single Character

**Orientation:** Horizontal (left to right)
**Focus:** Glute growth with clothing destruction

```
DAZ Studio Iray render of a real 3D scene. Ray-traced subsurface scattering on 
skin, specular highlights catching warm rim light, physically-accurate fabric 
weave with visible thread detail, 8K texture detail, shallow depth of field 
with photographic bokeh. Photographic CGI render, NOT illustrated.

TWO REFERENCES: First reference is the CHARACTER — match [CHARACTER NAME]'s face 
and identity. Second reference is the SIZE CHART — match body to WOMAN NUMBER [1–6].

Single image rendered as a TRIPTYCH — three side-by-side photographic frames of 
the same scene at three progressive moments, separated by thin black borders. 
Each frame is a fully photoreal CGI render in the same style.

Subject across all three frames: EXTREME CLOSEUP of [CHARACTER NAME]'s glutes 
from a low rear three-quarter angle, MID-GROWTH. Frame 1 (left): glutes 
athletic-sized, [CLOTHING, e.g. "shorts" / "spandex" / "skirt"] intact. 
Frame 2 (middle): glutes noticeably larger and rounder, [CLOTHING] tearing at 
the seams, fabric pulling tight. Frame 3 (right): glutes massively enlarged, 
[CLOTHING] split wide at the seams, skin glistening, stretched tight over 
expanding muscle.

[RULES BLOCK — CGI]
```

---

## Template 6: Pre-Grown Muscles + Breast Growth

**Orientation:** Horizontal (left to right)
**Focus:** Muscles already enormous from frame 1 — only breasts grow across frames

```
DAZ Studio Iray render of a real 3D scene. Ray-traced subsurface scattering on 
skin, specular highlights catching [ENERGY COLOR, e.g. "teal/cyan"] energy 
glow, physically-accurate fabric weave with visible thread detail, 8K texture 
detail, shallow depth of field with photographic bokeh. Photographic CGI 
render, NOT illustrated.

TWO REFERENCES: First reference is the CHARACTER — match [CHARACTER NAME]'s face 
and identity. Second reference is the SIZE CHART — match body to WOMAN NUMBER [1–6].

Single image rendered as a TRIPTYCH — three side-by-side photographic frames of 
the same scene at three progressive moments, separated by thin black borders. 
Each frame is a fully photoreal CGI render in the same style. MEDIUM SHOT from 
chest up of [CHARACTER NAME]. Her arms and muscles are ALREADY MASSIVELY HUGE 
in frame 1 — biceps the size of her head, thick powerful forearms, already 
fully grown. The muscles DO NOT change across frames. Only her breasts grow 
across the three frames.

Frame 1 (left): Arms and muscles already enormous. Breasts starting size. 
Clothing already shredded across arms and shoulders from prior muscle growth. 
Face shows first hint of surprise at something new happening — brows slightly 
raised, eyes widening, mouth just beginning to open.

Frame 2 (middle): Arms unchanged — still massive. Breasts noticeably larger, 
remaining chest fabric visibly stretching and pulling tight. [ENERGY COLOR] 
lightning energy crackling around her body. Face shows growing shock — brows 
fully arched, eyes wide, mouth open in a gasp.

Frame 3 (right): Arms unchanged — still massive. Breasts massively enlarged, 
chest fabric burst open at center, deep cleavage. [ENERGY COLOR] energy 
lightning intensifying. [ACCESSORY, e.g. "spiked metal wristbands"] remain 
intact. Face shows peak reaction — eyes wide, mouth fully open, head thrown 
back in exclamation.

[RULES BLOCK — CGI]
```

---

## Template 7: Breast Growth — Realistic Photo Style

**Orientation:** Horizontal (left to right)
**Focus:** Realistic photographic breast growth, no CGI

```
Hyperrealistic photograph shot on Canon EOS R5, 85mm f/1.4 lens, shallow depth 
of field, natural cinematic lighting, sharp focus on the subject, soft 
photographic bokeh in the background. Photographic capture, NOT illustrated.

ONE REFERENCE: Match [CHARACTER NAME]'s face and identity exactly.

Single image presented as a TRIPTYCH — three side-by-side photographic frames 
of the same subject at three progressive moments, separated by thin black 
borders. Each frame is a fully photoreal photograph in the same style. Camera 
angle consistent across all three frames — MEDIUM SHOT from chest up of 
[CHARACTER NAME]. Face fully visible in every frame, never cropped, never cut 
off. Eyes never directly at camera — looking off-frame in shocked reaction.

Subject across all three frames: progressive breast growth.

Frame 1 (left): Starting size. Face shows first hint of surprise — brows 
slightly raised, eyes widening, mouth just beginning to open.

Frame 2 (middle): Noticeably larger. Fabric visibly stretching and pulling 
tight. Face shows growing shock — brows fully arched, eyes wide open, mouth 
open in a gasp, head tilting back slightly.

Frame 3 (right): Massively enlarged. Fabric bursting at seams, deep cleavage. 
Face shows peak reaction — eyes wide, mouth fully open, cheeks flushed, head 
thrown back.

[RULES BLOCK — PHOTO]
```

---

## Rules Blocks

Append the correct rules block at the end of every prompt.

### CGI Rules Block

```
Skin is wet, shiny, glistening with healthy natural tone. Skin is smooth over 
the muscle, no visible veins. Muscles are natural and healthy in tone — never 
red, never inflamed. Any character with enlarged muscles also has 
proportionally enlarged, full breasts with prominent cleavage. All characters 
fully clothed — clothes may be torn or stretched but always cover the body. 
Correct human anatomy, exactly two arms per character. Every character has a 
vivid, animated, expressive face visible at all times. Characters look at each 
other, never at the camera. No background characters. Once muscles have grown, 
they stay grown. Photographic CGI render, NOT illustrated.
```

### Photo Rules Block

```
Skin is natural healthy tone with realistic photographic texture. All 
characters fully clothed — clothes may be torn or stretched but always cover 
the body. Correct human anatomy. Every character has a vivid, animated, 
expressive face visible at all times. Once grown, they stay grown. 
Photographic capture, NOT illustrated.
```

---

## Modifiers

Apply these additions to any template when needed. Append to the scene description.

| Modifier | Add this line |
|---|---|
| No background people | `No background characters.` |
| Specific energy effect | `[COLOR] lightning energy crackling around her body.` |
| Characters interact | `Characters look at each other and react to each other in every frame — never at the camera.` |
| Specific costume detail | Describe the costume fully after the character description line. |
| Vertical orientation | Replace "TRIPTYCH — three side-by-side photographic frames" with "VERTICAL TRIPTYCH — three stacked photographic frames, smallest on top, largest on bottom." |
| Face always visible | Use "MEDIUM SHOT from chest up" — replaces EXTREME CLOSEUP. Face fully visible in every frame — never cropped. |
| Pre-grown muscles | `Her [BODY PART] are ALREADY MASSIVELY HUGE in frame 1 — they DO NOT change across frames.` |
| **Carry forward prior growth** (use for any beat that's not the FIRST growth scene in a longer comic) | Add a `CARRY FORWARD STATE` block at the top of the scene description listing all features grown in prior beats, their sizes, and the explicit instruction that they are IDENTICAL across all three frames. Restate the carry-forward features in each per-frame description as "UNCHANGED from frame N — still size [X]." See "Cumulative State — Beats Within a Longer Comic" above for full template. |
| Add comic SFX | `In each frame, an SFX word appears as a 3D-extruded chrome letter sculpture sitting in the scene as a physical object, casting a real ray-traced shadow on the ground and catching the same warm rim light as the rest of the render. Frame 1: "GROW" small. Frame 2: "GROW" medium. Frame 3: "GROW" large.` Use sparingly — even with this phrasing, SFX text increases the risk of 2D drift. |
| Specific setting | Append `Setting: [DETAILED LOCATION DESCRIPTION].` after the triptych framing line, before the per-frame breakdown. |

---

## When 2D Drift Still Happens

If a template still produces flat / illustrated / cartoon-looking output despite using the corrected style:

1. **Check the reference images.** If the character ref is itself a 2D illustration or anime-style render, the model will inherit that aesthetic regardless of prompt language. Use a CGI character ref for CGI prompts.
2. **Drop the SFX modifier entirely.** Even with the 3D-extruded phrasing, comic SFX is the single biggest puller toward illustration. The growth progression is self-explanatory; SFX is decorative.
3. **Remove the triptych structure** and render a single CGI frame instead — sometimes the multi-frame layout itself is the issue. The decorative beat lands almost as well as a single dramatic frame at a peak moment.
4. **Add explicit lens / sensor / lighting language** beyond the default opener: *"shot in a virtual studio with three-point lighting, key light at 5500K, fill at 4500K, rim light at 6500K, rendered in DAZ Studio with Iray at 8K resolution."* The more concrete the rendering vocabulary, the harder the model has to work to drop into illustration.
5. **See `lessons-learned.md` L7** for the full diagnosis and the original failure case.

---

## Quick Reference: Template Selection

| Scene Type | Characters | Orientation | Template |
|---|---|---|---|
| Bicep growth | 1 | Horizontal | Template 1 |
| Bicep growth | 3 interacting | Horizontal | Template 2 |
| Breast growth, face visible | 1 | Horizontal | Template 3 |
| Breast growth, escalating FX | 1 | Vertical | Template 4 |
| Ass growth | 1 | Horizontal | Template 5 |
| Pre-grown muscles + breast growth | 1 | Horizontal | Template 6 |
| Breast growth, realistic photo | 1 | Horizontal | Template 7 |
