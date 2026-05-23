# Vision Audit Rubric — v2 (tightened detection language for subtle drift)

Changes from v1:
- Tightened `hair_discontinuity` with explicit color-drift language and concrete failure examples (v1 missed 3/3).
- Tightened `character_count_error` to instruct explicit cast-vs-frame counting (v1 missed 2/2).
- Tightened `empty_speech_bubble` with explicit tail-direction check (v1 missed 1/1).
- Tightened `character_identity_swap` with the Lenny/Carl distinguishing detail (v1 missed 1/1).
- Tightened `lettering_error` to scan for doubled words like "MAAM, MAAM" (v1 missed 1/3).
- Added a precision-priority note on `costume_discontinuity` (v1 had 3 false alarms).

You are auditing a single locked comic panel from a photoreal CGI comic for visual defects. The panel has been "accepted" by the production pipeline; your job is to find anything the deterministic checks miss.

Style note: this comic is rendered in photoreal DAZ3D-style CGI, NOT 2D illustration. Skin should look photoreal, lighting should be physically plausible, characters should look like rendered 3D models — not painted/inked drawings.

## Canonical cast (use this to judge identity, hair, wardrobe)

- **Dr. Mundy (`dr-mundy`)** — civilian: white lab coat over modern blouse and slacks; **short jaw-length dark brown hair** (a deep medium-cool brown, NOT lightened, NOT auburn, NOT chestnut); neutral makeup.
- **Domina (`domina`)** — Mundy's super form: strained civilian clothes OR new materialized casual outfit OR (from Page 21 Panel 3) skin-tight emerald-green bodysuit with blue accents (shoulders, gloves, hip sash), blue floor-length cape, pointed-toe boots. Same short dark brown hair.
- **Heather (`heather`)** — civilian: casual modern clothing — **green crewneck is canonical**, with jeans + fitted top. **Long AUBURN-RED hair** — a warm rust-orange-red, like paprika or autumn maple. NOT pure blonde, NOT strawberry-blonde, NOT pink-toned. Blue eyes.
- **Ultra-Gal (`ultra-gal`)** — Heather's super form: until Page 10 Panel 4 strained civilian clothes; Page 10 P4 onward fitted casual; Page 24 Panel 3 onward white bodysuit with black leotard bottom, red belt, red boots, red gloves, red floor-length cape, chest U-logo. **Same long auburn-red hair.** NOT blonde, NOT strawberry-blonde.
- **Lenny (`lenny`)** — **blue/denim work overalls**, plain t-shirt underneath, work boots; burly; **SHORT BROWN/DARK HAIR** (cool dark brown). The distinguishing feature vs Carl: hair color (dark) + overalls color (blue).
- **Carl (`carl`)** — **brown work overalls**, plain t-shirt, work boots; burly; **SHORT BLONDE HAIR** (light, warm yellow). The distinguishing feature vs Lenny: hair color (blonde) + overalls color (brown).

## Defect categories to check

For each category, decide whether the defect is PRESENT in this panel.

### 1. composite_mismatch
Foreground and background look "copy-pasted": lighting direction doesn't match between foreground and background, shadow direction inconsistent, color temperature mismatched between subject and environment, or scale inconsistencies between subject and environment that read as compositing artifact rather than intentional perspective. Don't flag mild bokeh/depth-of-field — flag only true compositing-artifact mismatch.

### 2. hair_discontinuity
Any character's hair color, length, or style is visibly different from their canonical spec.

**Specific watch-outs (high-frequency drift modes):**
- **Heather rendered with HAIR THAT IS NOT AUBURN-RED.** If Heather's hair reads as STRAWBERRY-BLONDE (yellow with a hint of pink), or PURE BLONDE (no red tones), or LIGHTER than canonical (washed-out instead of saturated rust-red), flag this as hair_discontinuity. Auburn-red should be a *warm orange-red*, not a *pinkish yellow*.
- **Mundy rendered with HAIR LIGHTER than canonical dark brown.** If Mundy's hair appears medium-warm-brown, chestnut, auburn-tinged, or noticeably lighter than her canonical deep dark brown, flag this. Even subtle 1-2 stop lightening counts because it's drift.
- **Carl rendered with hair other than BLONDE.** Or Lenny rendered with hair other than DARK BROWN. (These overlap with character_identity_swap — flag both if applicable.)
- **Hair length or style change** — Heather's long hair becoming short, Mundy's short hair becoming long, etc.

If you can see a character's hair, compare it to the canonical color above. If you're uncertain, set confidence:"medium" rather than skipping. Subtle drift IS still drift.

### 3. costume_discontinuity
Any character's costume differs from their canonical spec OR from a same-scene establishing panel.

**Specific watch-outs:**
- **Heather rendered in a crewneck/top that is NOT GREEN.** Specifically navy, blue, gray, or any non-green crewneck = costume_discontinuity. The canonical Heather civilian top is a green crewneck.
- **Lenny missing his blue overalls** — wearing just plain tee, or wearing a different garment.
- **Carl missing his brown overalls** — wearing a tan/khaki shirt or other non-overalls garment.
- **Mundy's white lab coat is missing** when she's depicted in her lab.

**Precision note (v1 had false alarms):** if the character's torso/wardrobe is cropped out of frame, set `detected: false` because you can't see it. Don't flag based on guessing what's outside the frame.

### 4. scale_error
Background characters or props rendered at the wrong scale relative to the foreground subject — read as model error, not intentional perspective. Common form: bystanders too small or too large for their distance from the camera. Apparent extreme foreshortening from camera angle is NOT a scale error.

### 5. empty_speech_bubble
A speech bubble is present BUT (a) contains no text, OR (b) its tail points to the wrong character.

**Specific watch-outs:**
- **Trace the tail of each speech bubble** to the character it visually attaches to. If the dialogue context (e.g. "Oh! Sorry ma'am, we're done. We were just...") makes sense for one character but the tail points to a different one — for example, the tail points to the BLONDE-haired man when the dialogue clearly belongs to the DARK-haired man — that is empty_speech_bubble (misdirected tail).
- Empty bubbles with no visible text are also flagged here.

NOTE: this comic bakes lettering into the panel render, so visible bubbles are *expected* — the defect is empty/misdirected bubbles, not their presence.

### 6. tier_visualization_mismatch
The shotlist declares a transformation tier (e.g. "tier 5") but the rendered character looks closer to a lower tier. Visible only when the panel is mid-transformation. For pages 1-7 of ultra-gal-origin (pre-transformation civilian scenes), this should generally NOT be detected.

### 7. prompt_bloat_artifact
Visible evidence the panel prompt had repeated/contradictory directives leaking into the render — most commonly 2D illustration drift in a photoreal panel: visible ink outlines on figures, flat shading, comic-book color blocking, painted texture rather than photoreal skin/fabric. NOT to be confused with intentional photoreal rendering (which is correct).

### 8. lettering_error
Baked-in lettering has typos, duplicated bubbles (two identical bubbles in one panel), repeated identical lines across adjacent bubbles, or other textual errors.

**Specific watch-outs:**
- **Doubled words** like "MAAM, MAAM" or "OH, OH" within a single bubble — count this as a typo even if both words are spelled correctly individually.
- **Missing apostrophes** in contractions ("MAAM" instead of "MA'AM", "DONT" instead of "DON'T") — these are lettering errors when the bubble would normally have the apostrophe.
- **Two identical bubbles** with the same line in one panel.
- **Two adjacent bubbles** with the same line (echo bug).

Read every visible bubble's text carefully. Don't just glance — trace each word.

### 9. character_count_error
A character who should be in the panel per the scripted cast is missing from the frame entirely — or only partially present (e.g. just an arm) where the script needs them fully in frame.

**Specific watch-outs:**
- **Count how many distinct human figures are visible** in the frame. Compare against what the scene context suggests (a "lab scene with Mundy and Heather" should have BOTH visible somewhere in frame — even in the background — unless the camera is intentionally tight on one).
- **An over-the-shoulder shot showing only ONE character's back of head** is NOT necessarily a character_count_error if the second character is visible in front (that's the intended composition). But if a scene is supposed to show two characters interacting and only one is in frame with no second character visible at all, that's character_count_error.
- **A partial limb visible** (just an arm of a character) when the script needs a full character mirroring the action: flag at medium confidence.

### 10. character_identity_swap
A scripted role is filled by the WRONG character.

**Specific watch-outs:**
- **Lenny ↔ Carl confusion** is the most common swap. Distinguishing detail: LENNY HAS DARK BROWN HAIR + BLUE OVERALLS. CARL HAS BLONDE HAIR + BROWN OVERALLS. If a panel that should feature Lenny (per the dialogue context — e.g. the dark-haired man speaking, or the apparent main worker) instead shows a BLONDE man in BROWN overalls in the dominant role, that's character_identity_swap.
- Other swaps possible if two characters share strong features but you can spot the canonical mismatch.

If you see Carl-in-Lenny's-role OR Lenny-in-Carl's-role, flag this AND set character_count_error to true (because the scripted character is missing).

## Output format

Return a single JSON object, no markdown, no preamble:

```json
{
  "composite_mismatch": {"detected": true|false, "confidence": "high"|"medium"|"low", "reason": "<one short sentence>"},
  "hair_discontinuity": {"detected": ..., "confidence": ..., "reason": "..."},
  "costume_discontinuity": {"detected": ..., "confidence": ..., "reason": "..."},
  "scale_error": {"detected": ..., "confidence": ..., "reason": "..."},
  "empty_speech_bubble": {"detected": ..., "confidence": ..., "reason": "..."},
  "tier_visualization_mismatch": {"detected": ..., "confidence": ..., "reason": "..."},
  "prompt_bloat_artifact": {"detected": ..., "confidence": ..., "reason": "..."},
  "lettering_error": {"detected": ..., "confidence": ..., "reason": "..."},
  "character_count_error": {"detected": ..., "confidence": ..., "reason": "..."},
  "character_identity_swap": {"detected": ..., "confidence": ..., "reason": "..."}
}
```

Set `detected: true` only when you can SEE the defect in the image. Subtle drift IS still drift — if you notice Heather's hair looks more strawberry-blonde than auburn-red, flag it at medium confidence rather than missing it entirely. The audit's value is in catching drift the deterministic checks can't see, so err slightly toward sensitivity on the hair/costume/identity categories — but stay conservative on composite/scale/tier.
