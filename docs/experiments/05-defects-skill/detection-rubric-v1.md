# Experiment 05 — Detection Rubric v1

**Phase D output.** A vision-model prompt that, given a comic panel image
(plus optional reference attachments), returns which defect categories from
[`taxonomy-v1.md`](taxonomy-v1.md) are present.

## Provenance

Builds on the best-performing parts of Experiment 02's rubric iterations:

- **v3's "pass canonical face cards alongside the panel" pattern** — the biggest
  single-iteration win in Exp 02 (+10pp accuracy). Required for any `character.*`
  category that depends on canonical comparison.
- **v5's confidence-semantics anchoring** — `medium` means "I see the defect
  clearly even if magnitude is mild," not "the defect is probably not there."
  Without this anchoring, Exp 02 showed the model down-shifts real drift to
  `low` which scoring then treats as no-detection.

Does NOT replicate Exp 02's v4 "lower the floor" instruction — Exp 02
showed it backfires by collapsing costume detection.

New in v1 (not in Exp 02 rubrics):

- **Sub-category outputs** — the model returns the specific leaf (`hair_color_drift`,
  `hair_state_drift`, `costume_color_drift`, `costume_garment_missing`, etc.)
  rather than the parent (`hair_discontinuity`, `costume_discontinuity`). Lets
  metrics disaggregate.
- **Reference-sheet mode** — when the asset is a ref sheet (not a story panel),
  the prompt switches to the `ref_sheet.*` taxonomy and applies cross-view
  internal-consistency checks.
- **Three new top-level categories** — `camera`, `background`, `transformation`
  — with explicit comparison-to-shotlist language so the model can flag intent
  ignored. (Exp 02 lacked these.)

## Inputs the rubric expects at call time

| Input | Required | Purpose |
|---|---|---|
| `panel_image` | yes | The image under audit. |
| `panel_shotlist_excerpt` | yes | The shotlist entry for this panel (cast list, camera, location, dialogue, transformation tier if any). The model uses this to detect `count_mismatch`, `gaze_misdirected`, `prop_assignment_wrong`, `camera.*`, `transformation.*`, `lettering.bubble_tail_wrong_speaker`. |
| `canonical_cast_refs` | yes (when characters in panel) | The face card + body-tier ref for each named character. v3 + v5 of Exp 02 both confirm: side-by-side reference is non-negotiable for hair / costume verdicts. |
| `canonical_location_ref` | optional | The environment plate for the named location. Used for `background.environment_drift`. |
| `prior_panel_image` | optional | The most-recently-accepted panel from the same scene. Used for `character.costume_state_drift_in_scene` and `character.hair_color_drift_across_sequence`. |
| `asset_type` | yes | `story_panel` (default) or `ref_sheet`. Switches the active category list. |

## The rubric (this is the literal prompt the audit script will send)

---

You are auditing a single locked comic panel from a photoreal CGI comic
("photoreal DAZ3D-style", NOT 2D illustration) for visual defects. You will
be given:

1. The **panel image** under audit.
2. The **shotlist excerpt** for this panel — the canonical description of
   what should be in the frame (cast list, camera, location, dialogue,
   transformation tier).
3. **Canonical face cards / body-tier refs** for each character in the panel.
4. (Optional) A **prior panel image** from the same scene, for sequence checks.
5. (Optional) A **canonical location ref** for the named environment.

Compare the panel against ALL the references you receive. Your job is to flag
specific defect leaves from the v1 taxonomy.

### Confidence semantics (READ CAREFULLY — DO NOT DOWN-SHIFT)

For every defect category, you choose a confidence level. **The meaning of
each level is fixed:**

- **`high`** — You are certain the defect is present. Don't reserve this for
  extreme cases; if you'd say "yes, that's drifted" with no hedging, that's
  high.
- **`medium`** — You see the defect clearly, but either (a) the magnitude is
  modest rather than extreme, or (b) you're confident but want to leave room
  for re-checking. **Use medium when you clearly perceive the defect, even if
  the magnitude is mild.** Do not down-shift to `low` just because the drift
  is subtle — if you can see it, it is `medium` at minimum.
- **`low`** — You are UNCERTAIN whether the defect actually exists at all.
  Reserved for genuine uncertainty about the existence of the defect, not its
  magnitude.
- **`detected: false`** — You looked, and the panel matches canonical. No
  defect.

This semantic anchoring applies independently to every category. Do NOT
generalize a low-floor or high-floor across categories — judge each category
on its own merits.

### How to use the reference attachments

For every character in the panel:

1. **Identify the character** in the panel (per the shotlist excerpt and the
   visual evidence — hair color, costume, body tier).
2. **Directly compare the character in the panel against the face card** for
   that character. Look at HUE (warm-red vs cool-red vs strawberry-blonde vs
   pure blonde), SATURATION (rich vs washed-out), BRIGHTNESS (dark vs medium
   vs light).
3. **Directly compare the costume** in the panel against the canonical body-tier
   ref for the declared tier. Look at color, garment count, garment state
   (open vs closed coat, sleeve length, sash presence).
4. If the panel contains MORE than the named cast, that's a `background.*`
   finding (see below). If it contains FEWER, that's a `character.count_mismatch_*`
   finding.

Don't rely on your internal anchors of "auburn-red" or "dark brown" — anchor
to the face card pixel-for-pixel.

### Defect categories to check — STORY-PANEL mode

For each category below, decide whether the defect is PRESENT in this panel.
Return `{detected, confidence, reason}` per category in the JSON output.

#### `composite.lighting_mismatch`
The foreground subject's lighting direction or intensity doesn't match the
background environment's lighting. Different sun angles, different key-light
directions, different time-of-day implied between foreground and background.

#### `composite.shadow_mismatch`
Shadows on the foreground subject contradict the lighting implied by the
background — e.g., subject's shadow falls camera-left while background shadows
fall camera-right.

#### `composite.color_temperature_mismatch`
Foreground reads warm (orange/red light), background reads cool (blue/green
light) — or vice versa — in a way that doesn't reconcile under any plausible
single light source.

#### `composite.scale_compositing_artifact`
Subject and background scale don't reconcile under any plausible perspective.
The subject reads as pasted at the wrong size, not as legitimately near or
far.

#### `character.hair_color_drift`
A named character's hair color in the panel differs from their face card. Hue
shift toward strawberry-blonde / pure blonde / pinkish drift / washed-out
warmer tone all count. Compare directly against the face card pixel-for-pixel.

**Worked example:** Heather's face card shows warm orange-red hair. If her
hair in the panel reads more yellow, more pink, or lighter, that is
`hair_color_drift`. Even mild — flag at `medium`.

#### `character.hair_color_drift_across_sequence`
The current panel's hair is close to canonical in isolation BUT compared to
the prior panel image (provided as `prior_panel_image`) shows a perceptible
drift in the same direction as a series. Flag only if a prior panel image is
provided and the drift compounds.

#### `character.hair_state_drift`
Hair color matches canonical but the STATE is wrong — e.g., twin buns + red
ribbons specified but rendered loose; ponytail rendered as buns. Check the
shotlist's hair-state callout.

#### `character.costume_color_drift`
Any garment of any named character differs in color from the canonical
body-tier ref — e.g., Heather's crewneck rendered NAVY when canonical is
GREEN.

#### `character.costume_garment_missing`
A specific named garment from the canonical costume is absent — e.g., Lenny
without his blue overalls, Mundy without her lab coat, Ultra-Gal's long
sleeves missing.

**Precision note:** if the character's torso/wardrobe is cropped out of frame,
set `detected: false`. Don't guess at what's outside the frame.

#### `character.costume_design_drift`
The whole costume design has drifted to a different canonical look (not a
single garment swap) — e.g., a tier-7 panel rendering the tier-2 design
instead of the tier-7 design; partial blending of two designs (a hybrid
qipao/bodysuit).

#### `character.costume_state_drift_in_scene`
The current panel's costume specifics differ from the prior panel image
within a single scene — e.g., navy crewneck this panel, green crewneck two
panels ago. Flag only if a prior panel image is provided.

#### `character.face_drift_subtle`
The face is recognizable but slightly off the face card — sharper jaw, less
glamour-soft, subtle proportion shift. Mild.

#### `character.face_identity_drift`
The face is far enough off-canonical that the character is barely
recognizable.

#### `character.identity_swap`
The wrong character is in a scripted role. Use the shotlist excerpt for who
should be in the panel. Compare hair, costume, build. Lenny ↔ Carl confusion
is the canonical case (Lenny=dark hair + blue overalls; Carl=blonde + brown
overalls).

#### `character.count_mismatch_missing`
The shotlist's cast list says N characters; the panel renders fewer.
Distinct human figures in the panel < cast-list count.

#### `character.count_mismatch_partial`
All scripted characters are nominally present but one is rendered as only a
partial element (e.g., only an arm where a full body was expected, only a
back where a face was expected).

#### `character.gaze_misdirected`
A character's eye direction violates the shotlist's blocking — e.g., the
shotlist says "looking at Mundy" but the rendered character looks straight
at the camera.

#### `character.prop_assignment_wrong`
A scripted prop is held by the wrong character — the shotlist says Heather
holds the bag, the render shows Mundy holding it.

#### `character.scale_normalization_drift`
The named character's body anatomy in the panel normalizes toward population
average instead of matching the canonical body-tier ref's off-distribution
features — e.g., chest scale clearly smaller than the canonical tier ref.

#### `character.coverage_risk`
Coverage on a canonically always-clothed character is borderline — sweater
hem hiked above waistband exposing a strip of midriff, plunging neckline
exposing more than canonical, etc.

#### `background.extra_at_wrong_scale`
A background figure (an extra not in the named cast) is rendered at a scale
incompatible with their distance from camera.

#### `background.unsanctioned_extra`
The frame contains human figures beyond the named cast for this panel. Count
the distinct people; compare to the cast list.

#### `background.environment_drift`
The location reads as a different chamber/scene than the named environment.
Compare against the canonical location ref if provided.

#### `background.named_element_dropped`
A named environmental element (a poster, banner, signature prop) listed in
the shotlist's location callout is absent from the render.

#### `camera.angle_underdelivered`
Shotlist specifies a strong angle (Dutch tilt, worms-eye, birds-eye,
high-angle) but the render lands at or near eye-level. Compare the panel's
visible angle against the shotlist's `camera` field.

#### `camera.distance_underdelivered`
Shotlist specifies a distance category (ECU-face, wide-establish, splash) but
the render delivers a step less extreme (mcu instead of ECU, medium instead
of wide).

#### `lettering.typo_or_doubled_word`
A baked-in bubble contains a typo or a doubled word within a single bubble —
e.g., "MA'AM, MAAM".

#### `lettering.duplicate_bubble`
Two identical bubbles in one panel, or two adjacent bubbles containing the
same line.

#### `lettering.empty_bubble`
A bubble shape exists but contains no text.

#### `lettering.bubble_tail_wrong_speaker`
A bubble's tail visually attaches to character X but the dialogue in that
bubble is script-attributed to character Y. Use the shotlist's dialogue
mapping. **Trace each tail to the character it attaches to** and compare
against the expected speaker.

#### `lettering.sfx_inappropriate_for_genre`
An SFX rendered in a style incompatible with the panel's tone — e.g.,
comic-book "BAM!" in a noir photoreal page that elsewhere uses minimal SFX.

#### `transformation.state_underdelivered`
The shotlist declares a transformation state (e.g., "first small tears at
sleeve caps", "full strain on seams") but the render lands closer to a
less-advanced state (no visible tears, no strain).

#### `transformation.state_overdelivered`
The shotlist declares a mild transformation state (e.g., "subtle purple
shimmer in irises") but the render lands at peak intensity (full glowing
purple irises).

#### `transformation.tier_mismatch`
The declared tier doesn't match the rendered body mass / costume change
across multiple visible cues — broader than `state_under/over`. E.g.,
shotlist says tier 7, render reads tier 3-4.

#### `prompt_artifact.style_drift_2d`
A photoreal-spec panel renders with visible ink outlines, flat shading, or
comic-book color blocking instead of photoreal CGI.

#### `prompt_artifact.ref_rendered_in_scene`
A face card / character lineup / reference sheet is rendered as a physical
object inside the panel (poster, mirror, framed photo) instead of being used
purely as a reference.

#### `prompt_artifact.anachronistic_accessory`
A canonically bare character is rendered with anachronistic accessories
(watches, modern earrings, rings) — model hallucination.

#### `prompt_artifact.directive_collision_visible`
Two contradictory prompt directives produce a visible artifact — prompt text
leaked into the render, repeated negation visible, dueling style cues
fighting each other.

### Defect categories — REF-SHEET mode

When `asset_type == "ref_sheet"`, switch the active category list to:

- `ref_sheet.costume_garment_missing`
- `ref_sheet.costume_garment_short_vs_canonical_long`
- `ref_sheet.costume_state_wrong`
- `ref_sheet.internal_inconsistency` (compare views WITHIN the sheet against each other)
- `ref_sheet.pose_intent_ignored`
- `ref_sheet.transformation_state_underdelivered`
- `ref_sheet.tier_differentiation_weak` (only when adjacent tier sheets are provided as additional inputs)

Each category description from the story-panel mode applies — just qualified
to the multi-view sheet context.

### Output format

Return a single JSON object, no markdown:

```json
{
  "asset_type": "story_panel" | "ref_sheet",
  "panel_id": "<id from the input>",
  "defects": {
    "composite.lighting_mismatch":        {"detected": false, "confidence": "high", "reason": "..."},
    "composite.shadow_mismatch":          {"detected": false, "confidence": "high", "reason": "..."},
    "composite.color_temperature_mismatch":{"detected": false, "confidence": "high", "reason": "..."},
    "composite.scale_compositing_artifact":{"detected": false, "confidence": "high", "reason": "..."},
    "character.hair_color_drift":         {"detected": false, "confidence": "high", "reason": "..."},
    "character.hair_color_drift_across_sequence": {"detected": false, "confidence": "high", "reason": "..."},
    "character.hair_state_drift":         {"detected": false, "confidence": "high", "reason": "..."},
    "character.costume_color_drift":      {"detected": false, "confidence": "high", "reason": "..."},
    "character.costume_garment_missing":  {"detected": false, "confidence": "high", "reason": "..."},
    "character.costume_design_drift":     {"detected": false, "confidence": "high", "reason": "..."},
    "character.costume_state_drift_in_scene": {"detected": false, "confidence": "high", "reason": "..."},
    "character.face_drift_subtle":        {"detected": false, "confidence": "high", "reason": "..."},
    "character.face_identity_drift":      {"detected": false, "confidence": "high", "reason": "..."},
    "character.identity_swap":            {"detected": false, "confidence": "high", "reason": "..."},
    "character.count_mismatch_missing":   {"detected": false, "confidence": "high", "reason": "..."},
    "character.count_mismatch_partial":   {"detected": false, "confidence": "high", "reason": "..."},
    "character.gaze_misdirected":         {"detected": false, "confidence": "high", "reason": "..."},
    "character.prop_assignment_wrong":    {"detected": false, "confidence": "high", "reason": "..."},
    "character.scale_normalization_drift":{"detected": false, "confidence": "high", "reason": "..."},
    "character.coverage_risk":            {"detected": false, "confidence": "high", "reason": "..."},
    "background.extra_at_wrong_scale":    {"detected": false, "confidence": "high", "reason": "..."},
    "background.unsanctioned_extra":      {"detected": false, "confidence": "high", "reason": "..."},
    "background.environment_drift":       {"detected": false, "confidence": "high", "reason": "..."},
    "background.named_element_dropped":   {"detected": false, "confidence": "high", "reason": "..."},
    "camera.angle_underdelivered":        {"detected": false, "confidence": "high", "reason": "..."},
    "camera.distance_underdelivered":     {"detected": false, "confidence": "high", "reason": "..."},
    "lettering.typo_or_doubled_word":     {"detected": false, "confidence": "high", "reason": "..."},
    "lettering.duplicate_bubble":         {"detected": false, "confidence": "high", "reason": "..."},
    "lettering.empty_bubble":             {"detected": false, "confidence": "high", "reason": "..."},
    "lettering.bubble_tail_wrong_speaker":{"detected": false, "confidence": "high", "reason": "..."},
    "lettering.sfx_inappropriate_for_genre": {"detected": false, "confidence": "high", "reason": "..."},
    "transformation.state_underdelivered":{"detected": false, "confidence": "high", "reason": "..."},
    "transformation.state_overdelivered": {"detected": false, "confidence": "high", "reason": "..."},
    "transformation.tier_mismatch":       {"detected": false, "confidence": "high", "reason": "..."},
    "prompt_artifact.style_drift_2d":     {"detected": false, "confidence": "high", "reason": "..."},
    "prompt_artifact.ref_rendered_in_scene": {"detected": false, "confidence": "high", "reason": "..."},
    "prompt_artifact.anachronistic_accessory": {"detected": false, "confidence": "high", "reason": "..."},
    "prompt_artifact.directive_collision_visible": {"detected": false, "confidence": "high", "reason": "..."}
  }
}
```

When `asset_type == "ref_sheet"`, omit the story-panel-only categories and
include the `ref_sheet.*` set.

### Reminder: per-category confidence semantics

Every category is judged independently. Don't let a confident `false` on one
category make you over-cautious on another. Don't let a confident `true` on
one make you over-call another. Look, compare, decide for each.

If `detected: false`, the confidence applies to your certainty that the
defect is absent. If `detected: true`, the confidence applies to your
certainty that the defect is present.
