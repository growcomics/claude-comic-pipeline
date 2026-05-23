# Vision Audit Rubric — v4 (lower the floor for hair-drift detection)

Changes from v3:
- v3 detected hair drift on p06-04 (TP) but missed p02-04 (Mundy subtle lightening) and p07-01 (Heather subtle warm shift, flagged at LOW confidence only).
- v4 explicitly raises the floor: **if you see ANY hue, saturation, or brightness shift in a character's hair compared to their face card, mark `detected: true`** — calibrate `confidence` to the magnitude of the shift, but `detected: true` is the bar.
- Same defect categories and output format as v3. Same face card references.

You are auditing a single locked comic panel from a photoreal CGI comic. You have access to canonical face cards for Heather and Dr. Mundy. Compare each character in the panel directly against the face card.

Style note: this comic is rendered in photoreal DAZ3D-style CGI.

## Reference images you will receive

1. **REFERENCE — Heather face card** at `projects/ultra-gal-origin/references/characters/heather/face-card.png`. Canonical Heather civilian appearance.
2. **REFERENCE — Dr. Mundy face card** at `projects/ultra-gal-origin/references/characters/dr-mundy/face-card.png`. Canonical Mundy civilian appearance.

Lenny=DARK HAIR + BLUE OVERALLS. Carl=BLONDE HAIR + BROWN OVERALLS.

## Decision rule for hair_discontinuity (UPDATED)

The naive rubric asks "is the hair different?" — that lets the model excuse mild drift. v4 redefines:

> **Compare the panel character's hair to the face card.** If you can describe ANY perceptible shift in HUE (the color family — warm-red vs cool-red vs orange-red vs strawberry-blonde vs pure-blonde), or SATURATION (rich/deep vs washed-out), or BRIGHTNESS (dark vs medium vs light), set `detected: true`.
>
> - **`confidence: high`** when the shift is unmistakable (Heather rendered as full blonde / Heather's red shifted to pink-strawberry / Mundy lightened to medium brown).
> - **`confidence: medium`** when the shift is clearly visible but not extreme (Heather slightly lighter / slightly more orange-yellow than the face card).
> - **`confidence: low`** when you notice a subtle shift on close inspection (Heather marginally warmer / brighter than the face card; Mundy fractionally lighter).
> - **`detected: false`** only when the character's hair on the panel reads as a perceptual MATCH to the face card — same hue family, similar saturation, similar brightness.

The audit's purpose is to surface drift the deterministic checks can't see, so for hair specifically, lean toward flagging at LOW confidence rather than missing the drift.

(The other categories keep the v3 thresholding — be conservative on composite/scale/tier, balanced on costume/lettering/identity.)

## Canonical cast

- **Dr. Mundy** — civilian: white lab coat over modern blouse + slacks; SHORT JAW-LENGTH DEEP DARK BROWN HAIR (compare against the Mundy face card).
- **Heather** — civilian: GREEN crewneck + jeans + fitted top; LONG AUBURN-RED HAIR (compare against the Heather face card).
- **Lenny** — blue overalls + plain tee + work boots; SHORT DARK BROWN HAIR. Burly.
- **Carl** — brown overalls + plain tee + work boots; SHORT BLONDE HAIR. Burly.

## Defect categories

### 1. composite_mismatch
Foreground/background lighting, shadow, color-temp, or scale mismatch — compositing-artifact. Don't flag normal bokeh.

### 2. hair_discontinuity (see decision rule above)
Apply the v4 decision rule literally: any perceptible shift → `detected: true`, with confidence calibrated to magnitude.

### 3. costume_discontinuity
Any character's costume differs from canonical OR same-scene establishing. **Watch-outs:** Heather not in GREEN crewneck (e.g. navy); Lenny missing blue overalls; Carl missing brown overalls; Mundy missing lab coat in lab scenes.

**Precision note:** if the torso/wardrobe is cropped out of frame, set `detected: false` — don't guess.

### 4. scale_error
Background characters/props at wrong scale relative to foreground.

### 5. empty_speech_bubble
Bubble exists but: (a) contains no text, OR (b) tail points to wrong character. Trace each tail to its character.

### 6. tier_visualization_mismatch
Declared tier doesn't match rendered tier. For ultra-gal-origin pages 1-7, generally NOT detected (pre-transformation).

### 7. prompt_bloat_artifact
2D illustration drift in a photoreal panel — inked outlines, flat shading, comic-book color blocking.

### 8. lettering_error
Doubled words (e.g. "MAAM, MAAM"), missing apostrophes ("MAAM"), duplicate bubbles, repeated lines.

### 9. character_count_error
Cast member who should be in frame is missing entirely or only partially present.

### 10. character_identity_swap
Wrong character occupies a scripted role. Lenny ↔ Carl swap detected via hair color + overalls color mismatch.

## Output format

Return JSON object only (no markdown):

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
