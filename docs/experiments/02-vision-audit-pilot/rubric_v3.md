# Vision Audit Rubric — v3 (canonical face cards as side-by-side reference)

Changes from v2:
- **Pass canonical face cards alongside the panel image** so the model can do direct color/identity comparison rather than relying on text descriptions of "auburn-red" or "dark brown". v2 confidently called hair canonical for panels the audit flagged as drifted — likely because the model's internal anchor of "auburn-red" doesn't match the production canonical exactly. The fix: anchor the model with the actual canonical face card image.
- Same defect categories and output format as v2.

You are auditing a single locked comic panel from a photoreal CGI comic for visual defects. You will be given the panel image AND two canonical face card references. Compare each character in the panel against the canonical face card for that character.

Style note: this comic is rendered in photoreal DAZ3D-style CGI, NOT 2D illustration. Skin should look photoreal, lighting should be physically plausible, characters should look like rendered 3D models — not painted/inked drawings.

## Reference images you will receive

1. **REFERENCE — Heather face card** at `projects/ultra-gal-origin/references/characters/heather/face-card.png`. This is the CANONICAL appearance of Heather (civilian form) for this project: hair color, length, eye color, skin tone, neutral expression. If a panel shows Heather, her appearance should match THIS image — not a separate idea of "auburn-red".

2. **REFERENCE — Dr. Mundy face card** at `projects/ultra-gal-origin/references/characters/dr-mundy/face-card.png`. This is the CANONICAL appearance of Mundy (civilian form). If a panel shows Mundy, her appearance should match THIS image.

Lenny and Carl don't have face cards loaded here, so judge them by description:
- **Lenny**: SHORT BROWN/DARK HAIR + BLUE/DENIM OVERALLS + plain tee underneath. Burly.
- **Carl**: SHORT BLONDE HAIR + BROWN OVERALLS + plain tee underneath. Burly. Distinguishing feature vs Lenny: hair color (blonde) + overalls color (brown).

## How to use the face cards

For every panel that contains Heather or Mundy:
1. **Identify the character in the panel** (e.g., the redhead is Heather, the dark-haired professor is Mundy).
2. **Directly compare the character's hair in the panel against the face card.** Look at HUE (warm-red vs cool-red vs pink-tinted vs strawberry-blonde vs pure blonde), SATURATION (rich vs washed out), and BRIGHTNESS (dark vs medium vs light).
3. **If the hair in the panel is a different hue or noticeably lighter than the face card**, flag `hair_discontinuity`. Don't require dramatic difference — a SHIFT IN HUE (auburn-red → strawberry-blonde) counts even if the shift is mild.
4. Also compare costume to canonical — Mundy's lab coat, Heather's green crewneck.

## Defect categories to check

For each category, decide whether the defect is PRESENT in this panel.

### 1. composite_mismatch
Foreground and background look "copy-pasted": lighting direction mismatch, shadow direction inconsistent, color temperature mismatch, or scale-as-compositing-artifact (not intentional perspective).

### 2. hair_discontinuity
Any character's hair color, length, or style is visibly different from THEIR FACE CARD (Heather, Mundy) or the canonical text spec (Lenny=dark, Carl=blonde).

**Specific watch-outs:**
- **Heather rendered with hair LIGHTER, MORE YELLOW, or LESS RED than her face card.** Strawberry-blonde drift, pink-tinted drift, washed-out drift all count.
- **Mundy rendered with hair LIGHTER than her face card.** If she looks medium brown or chestnut instead of the deep dark brown of the face card, flag this.
- **Carl-hair on Lenny or Lenny-hair on Carl** (cross-references with character_identity_swap).
- **Hair length or style change.**

Be confident in flagging when you see a hue shift — that IS the defect.

### 3. costume_discontinuity
Any character's costume differs from their canonical spec OR from a same-scene establishing panel.

**Specific watch-outs:**
- **Heather rendered in a crewneck/top that is NOT GREEN.** Specifically navy, blue, gray, or any non-green crewneck = costume_discontinuity.
- **Lenny missing blue overalls** OR **Carl missing brown overalls** (e.g. wearing just plain tee).
- **Mundy missing her white lab coat** when in lab.

**Precision note:** if the character's torso/wardrobe is cropped out of frame, set `detected: false`. Don't flag based on guessing what's outside the frame.

### 4. scale_error
Background characters or props at wrong scale relative to foreground — model error, not intentional perspective.

### 5. empty_speech_bubble
A speech bubble is present BUT (a) contains no text, OR (b) its tail points to the wrong character.

**Trace the tail of each bubble** to the character it visually attaches to. If a dialogue line obviously belongs to character X but the tail points to character Y, flag this.

### 6. tier_visualization_mismatch
Shotlist declares a transformation tier but the rendered character looks closer to a lower tier. For pages 1-7 of ultra-gal-origin, this should generally NOT be detected.

### 7. prompt_bloat_artifact
2D illustration drift in a photoreal panel: visible ink outlines, flat shading, comic-book color blocking. NOT regular photoreal rendering.

### 8. lettering_error
Baked-in lettering has typos, duplicated bubbles, repeated identical lines, or other textual errors.

**Watch for:**
- **Doubled words** like "MAAM, MAAM" within a single bubble.
- **Missing apostrophes** in contractions ("MAAM" instead of "MA'AM").
- **Two identical bubbles** in one panel.
- **Two adjacent bubbles** with the same line.

Read every bubble's text carefully.

### 9. character_count_error
A character who should be in the panel per the scripted cast is missing from the frame entirely — or only partially present where the script needs them fully in frame.

**Count distinct human figures in the frame.** If a scene context suggests 2 characters (a lab scene with Mundy and Heather) and you see only ONE in frame with no second character anywhere visible, that's character_count_error.

### 10. character_identity_swap
A scripted role is filled by the WRONG character.

**Lenny ↔ Carl confusion** is the most common swap. LENNY=DARK HAIR + BLUE OVERALLS. CARL=BLONDE HAIR + BROWN OVERALLS. If a worker who should be Lenny is BLONDE in BROWN overalls, that's character_identity_swap.

## Output format

Return a single JSON object, no markdown:

```json
{
  "composite_mismatch": {"detected": ..., "confidence": ..., "reason": "..."},
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

When the panel contains Heather or Mundy, your hair_discontinuity / costume_discontinuity verdict for that character should reference the face card image directly — not a remembered description of "auburn-red". Look at both images and compare.
