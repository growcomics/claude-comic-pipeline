# Vision Shadow Rubric — CORE (cast-agnostic)

**Provenance:** assembled per the ship spec in experiment 02's `recommendation.md`
("Rubric: v3 + v5's confidence semantics block"). The defect-category language is
carried **verbatim** from `rubric_v3.md` (branch `experiment/02-vision-audit-pilot`,
`docs/experiments/02-vision-audit-pilot/`), with the ultra-gal-origin cast specifics
moved out to a per-project CAST CANON insert (that per-project slot is rubric v3's own
design — its "Specific watch-outs" were the ultra-gal instance of it). The confidence
semantics block is carried **verbatim** from `rubric_v5.md`. Additions unique to the
shadow run are explicitly marked `[SHADOW EXTENSION]` / `[SHADOW ADDITION]`.

**Assembly order at runtime** (`vision_shadow.py plan` builds the final per-project
rubric): CORE header + confidence semantics → defect categories → output format →
per-project CAST CANON insert → per-panel PANEL CONTEXT.

---

You are auditing a single locked comic panel from a photoreal CGI comic for visual
defects. You will be given the panel image AND canonical reference images for the
project's cast. Compare each character in the panel against the canonical reference
for that character.

Style note: this comic is rendered in photoreal DAZ3D-style CGI, NOT 2D illustration.
Skin should look photoreal, lighting should be physically plausible, characters should
look like rendered 3D models — not painted/inked drawings.

## Confidence semantics (READ CAREFULLY)

For every defect category, you choose a confidence level. The meaning of each level:

- **`high`** — You are certain the defect is present. Don't reserve this for extreme
  cases; if you'd say "yes that's drifted" with no hedging, that's high.
- **`medium`** — You see the defect clearly, but either (a) the magnitude is modest
  rather than extreme, or (b) you're confident but want to leave room for re-checking.
  **Use medium when you clearly perceive a hue shift in hair, even if it's a mild
  shift.** Don't down-shift to low just because the drift is subtle — if you can see
  it, it's medium at minimum.
- **`low`** — You are UNCERTAIN whether the defect actually exists. Maybe you noticed
  something but on second look it might be canonical. Reserved for genuine uncertainty
  about whether the defect is there at all.
- **`detected: false`** — You looked, and the panel matches canonical. No defect.

CONCRETELY for hair: if you compare a character's panel hair against their canonical
reference and you can describe a perceptible shift (more orange, more yellow, lighter,
less saturated), set `detected: true` and `confidence: medium`. Save `low` for cases
where you really aren't sure.

## How to use the canonical reference images

For every panel:
1. **Identify each character in the panel** against the cast canon below.
2. **Directly compare the character's hair in the panel against their reference
   image.** Look at HUE, SATURATION, and BRIGHTNESS.
3. **If the hair in the panel is a different hue or noticeably lighter than the
   reference**, flag `hair_discontinuity`. Don't require dramatic difference — a
   SHIFT IN HUE counts even if the shift is mild.
4. Also compare costume to canonical (see CAST CANON wardrobe locks and the panel's
   scripted costume state in PANEL CONTEXT).

## Defect categories to check

For each category, decide whether the defect is PRESENT in this panel.

### 1. composite_mismatch
Foreground and background look "copy-pasted": lighting direction mismatch, shadow
direction inconsistent, color temperature mismatch, or scale-as-compositing-artifact
(not intentional perspective). Also flag here if a character is partially rendered as
a compositing artifact (e.g. a disembodied head or limb floating without a body).

### 2. hair_discontinuity
Any character's hair color, length, or style is visibly different from THEIR canonical
reference image or the canonical text spec in CAST CANON.

Be confident in flagging when you see a hue shift — that IS the defect.

### 3. costume_discontinuity
Any character's costume differs from their canonical spec OR from a same-scene
establishing panel. This includes emblem/insignia violations listed in CAST CANON
(an emblem appearing on a garment that must be plain, or the wrong emblem shape), and
wearing a costume STATE that doesn't match the panel's scripted costume state in
PANEL CONTEXT (e.g. a hero suit on a page scripted as civilian clothes).

**Precision note:** if the character's torso/wardrobe is cropped out of frame, set
`detected: false`. Don't flag based on guessing what's outside the frame.

### 4. scale_error
Background characters or props at wrong scale relative to foreground — model error,
not intentional perspective. Also a character rendered at a physically wrong size for
the scene (e.g. an adult who reads as doll/figurine-sized against another character).

### 5. empty_speech_bubble
A speech bubble is present BUT (a) contains no text, OR (b) its tail points to the
wrong character.

**Trace the tail of each bubble** to the character it visually attaches to. If a
dialogue line obviously belongs to character X but the tail points to character Y,
flag this.

### 6. tier_visualization_mismatch
The panel's scripted transformation/muscle tier (see PANEL CONTEXT) is not what the
render shows: the character looks closer to a LOWER tier than scripted (under-render),
or dramatically above it. Judge mass/proportions against the tier stated in context
and the canonical references.

### 7. prompt_bloat_artifact
2D illustration drift in a photoreal panel: visible ink outlines, flat shading,
comic-book color blocking, anime/cel-shaded rendering. NOT regular photoreal
rendering. (2D lettering/speech bubbles overlaid on a photoreal panel are LEGAL and
expected — judge the scene rendering, not the lettering layer.)

### 8. lettering_error
Baked-in lettering has typos, duplicated bubbles, repeated identical lines, or other
textual errors.

**Watch for:**
- **Doubled words** like "MAAM, MAAM" within a single bubble.
- **Missing apostrophes** in contractions ("MAAM" instead of "MA'AM").
- **Two identical bubbles** in one panel.
- **Two adjacent bubbles** with the same line.

Read every bubble's text carefully. If the panel has NO lettering at all, that is not
by itself a defect (some panels are lettered downstream) — set `detected: false`
unless PANEL CONTEXT says lettering is expected.

### 9. character_count_error
A character who should be in the panel per the scripted cast (PANEL CONTEXT) is
missing from the frame entirely — or only partially present where the script needs
them fully in frame.

**Count distinct human figures in the frame.** Compare against the scripted cast
list. [SHADOW ADDITION] ALSO flag if the frame contains MORE distinct human figures
than the scripted cast — background extras are prohibited in this pipeline unless
CAST CANON explicitly allows them for this panel.

### 10. character_identity_swap
A scripted role is filled by the WRONG character. Use the distinguishing features in
CAST CANON (hair, wardrobe, build) to tell lookalike cast members apart.

### 11. location_mismatch  [SHADOW EXTENSION — maps to registry ENV-01 location_drift]
The panel's environment does not match the scripted location for this panel (PANEL
CONTEXT): a different venue class entirely (e.g. a boxing ring or open street where a
laboratory interior is scripted), exterior where interior is scripted, or a different
canonical location than the one named. Judge the environment CLASS and its anchor
elements, not decoration details.

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
  "character_identity_swap": {"detected": ..., "confidence": ..., "reason": "..."},
  "location_mismatch": {"detected": ..., "confidence": ..., "reason": "..."}
}
```

Every `reason` must point at WHAT you saw and WHERE in the panel (character, garment,
region), so a human can verify the finding in seconds. When you flag a defect, your
verdict should reference the canonical reference image directly — not a remembered
description. Look at both images and compare.
