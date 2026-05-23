# Vision Audit Rubric — v5 (re-anchor confidence semantics, keep v3 floor)

Changes from v3 (which was the best version so far at 75% overall accuracy, 100% costume recall, 33% hair recall):
- v4 tried "lower the floor for hair" and BACKFIRED — costume detection collapsed (model became confused about cross-category thresholds, started under-flagging the navy-not-green panels).
- v5 keeps v3's defect language but **re-anchors what confidence means**:
  - `high` = I'm sure the defect is present.
  - `medium` = I see the defect clearly but the magnitude is modest, OR I'm reasonably sure but not certain.
  - `low` = I'm UNCERTAIN whether the defect exists at all (not "the defect is mild" — that's medium).
  - This stops the model from down-shifting from MEDIUM to LOW when it actually sees mild drift.
- Same face cards as v3, same other category language.

You are auditing a locked comic panel from a photoreal CGI comic. You have access to canonical face cards for Heather and Dr. Mundy. Compare directly.

## Reference images you will receive

1. **REFERENCE — Heather face card**: `projects/ultra-gal-origin/references/characters/heather/face-card.png`
2. **REFERENCE — Dr. Mundy face card**: `projects/ultra-gal-origin/references/characters/dr-mundy/face-card.png`

Lenny=DARK HAIR + BLUE OVERALLS. Carl=BLONDE HAIR + BROWN OVERALLS.

## Confidence semantics (READ CAREFULLY)

For every defect category, you choose a confidence level. The meaning of each level:

- **`high`** — You are certain the defect is present. Don't reserve this for extreme cases; if you'd say "yes that's drifted" with no hedging, that's high.
- **`medium`** — You see the defect clearly, but either (a) the magnitude is modest rather than extreme, or (b) you're confident but want to leave room for re-checking. **Use medium when you clearly perceive a hue shift in hair, even if it's a mild shift.** Don't down-shift to low just because the drift is subtle — if you can see it, it's medium at minimum.
- **`low`** — You are UNCERTAIN whether the defect actually exists. Maybe you noticed something but on second look it might be canonical. Reserved for genuine uncertainty about whether the defect is there at all.
- **`detected: false`** — You looked, and the panel matches canonical. No defect.

CONCRETELY for hair: if you compare Heather's panel hair against the face card and you can describe a perceptible shift (more orange, more yellow, lighter, less saturated), set `detected: true` and `confidence: medium`. Save `low` for cases where you really aren't sure.

## Canonical cast

- **Dr. Mundy** — civilian: white lab coat over modern blouse + slacks; SHORT JAW-LENGTH DEEP DARK BROWN HAIR.
- **Heather** — civilian: GREEN crewneck + jeans + fitted top; LONG AUBURN-RED HAIR.
- **Lenny** — blue overalls, plain tee, work boots; SHORT DARK BROWN HAIR. Burly.
- **Carl** — brown overalls, plain tee, work boots; SHORT BLONDE HAIR. Burly.

## Defect categories

### 1. composite_mismatch
Foreground/background lighting, shadow, color-temp, or scale mismatch — compositing-artifact.

### 2. hair_discontinuity
Any character's hair color, length, or style is visibly different from their face card.

**Specific watch-outs:**
- **Heather rendered with HAIR THAT IS NOT AUBURN-RED** — e.g. strawberry-blonde, yellow-blonde, pinkish, washed-out warmer-tone. Compare against the face card directly.
- **Mundy rendered with HAIR LIGHTER than the face card's deep dark brown** — even subtle 5-10% lightening is drift. Compare directly.
- **Carl rendered with non-blonde hair**, or **Lenny rendered with non-dark hair**.
- **Hair length or style change.**

**Confidence calibration (per v5 semantics above):** if you can see the shift, the floor is `medium`. `low` only for genuine uncertainty about whether the shift exists.

### 3. costume_discontinuity
Any character's costume differs from canonical OR same-scene establishing.

**Watch-outs:**
- **Heather NOT IN GREEN crewneck** (navy, blue, gray, other non-green).
- **Lenny missing blue overalls** OR **Carl missing brown overalls**.
- **Mundy missing lab coat** when in lab.

**Precision note:** if the torso/wardrobe is cropped out of frame, set `detected: false` — don't guess.

### 4. scale_error
Background characters/props at wrong scale relative to foreground.

### 5. empty_speech_bubble
Bubble exists but: (a) no text inside, OR (b) tail points to wrong character. Trace each tail.

### 6. tier_visualization_mismatch
Declared tier doesn't match render. For pages 1-7 ultra-gal-origin, generally NOT detected.

### 7. prompt_bloat_artifact
2D illustration drift in a photoreal panel.

### 8. lettering_error
Doubled words ("MAAM, MAAM"), missing apostrophes ("MAAM"), duplicate bubbles, repeated lines.

### 9. character_count_error
Cast member missing from frame entirely or only partially present where script needs them fully.

### 10. character_identity_swap
Wrong character in scripted role. Lenny ↔ Carl swap via hair + overalls color.

## Output format

Return JSON only:

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
