---
name: reference-sheets
description: Generate turnaround/reference sheets for any asset that appears on 2+ pages of a comic script (characters, character transformation states, props, prop states, environments), and produce a per-page ATTACH plan so every generated page uses the right references. Use this skill BEFORE batch-generating pages whenever a script is finalized, when a story contains transformations (growth, drain, damage), or when the user asks for consistency references, character sheets, prop turnarounds, or environment sheets.
---

# Reference Sheets for Comic Consistency

## Why this exists

AI image generation drifts. Faces mutate, props change design, rooms rearrange
between pages. The fix: every recurring asset gets ONE canonical reference
sheet, and every page generation attaches the sheets for the assets in that
shot. Workflow: audit -> sheet prompts -> generation order -> per-page ATTACH plan.

## Step 1 - Asset audit

Scan the finalized script page by page. Build a table of every asset and the
page ranges where it appears:

- **Characters** - every named or recurring character.
- **Character STATES** - the one everyone misses. In transformation comics,
  each stable state of a character is a SEPARATE asset needing its own sheet:
  base form, drained form, giant form, reborn/glowing form, defeated form.
  A state that persists 2+ pages gets a sheet. Transient mid-transformation
  frames do NOT get sheets - they use the nearest state sheet as target plus
  the muscle size lineup at the stated intermediate size.
- **Props** - weapons, devices, artifacts. Prop STATES count too:
  charged (color change), broken, upgraded.
- **Environments** - every location. Environment STATES count: intact vs
  ruined versions of the same room are two sheets.

Rule: **appears on 2+ pages -> needs a sheet.** Appears once -> describe it
in the page prompt, no sheet.

## Step 2 - Sheet formats (three templates)

### Character sheet
Beige grid background, labeled panels. Title text in the image:
"NAME - STATE". FRONT VIEW, SIDE VIEW, BACK VIEW in neutral standing pose,
plus "CLOSE-UP: FACE" panel showing the state's signature expression, plus
"CLOSE-UP: TORSO" when clothing/glow/damage detail matters. Always state:
exact size number from the muscle lineup, exact height in meters, exact
clothing condition (intact / stretched / split at seams but covering /
oversized and sagging). End with: photorealistic 3D render, DAZ3D Iray
quality, soft studio lighting, correct anatomy, exactly two arms.

### Prop turnaround
Light grey background, product photography lighting. Title text:
"PROP NAME - Turnaround" (or "- STATE"). Four views minimum: left profile,
right profile, front, top-down. One detail inset panel of the most important
surface detail (runes, glow, break point). Material callout labels along the
bottom: "MATERIAL - MATERIAL - MATERIAL".

### Environment sheet
Grey background, six labeled panels: FRONT VIEW, BACK VIEW, LEFT VIEW,
RIGHT VIEW, TOP VIEW, PERSPECTIVE VIEW. State the lighting condition
explicitly (golden hour, warm interior, red emergency) and keep it consistent
across all six panels. Architectural visualization quality.

## Step 3 - Generation order (dependency chaining)

Variant sheets must be generated WITH their base sheet attached, or the
variant will not match:

1. Base character sheets first.
2. State variants second - attach the base sheet: "match the face and hair
   of the attached reference exactly, but body now..."
3. Base prop turnaround first, then charged/broken variants with base attached.
4. Intact environment first, then ruined variant with intact attached:
   "the SAME room as the attached reference, now destroyed - ...
   Layout and architecture identical to the intact version."

Write the dependency in each variant prompt:
"ATTACH when generating: <base sheet>".

## Step 4 - Naming convention

`REF-XX - Asset STATE (pages N-M)`. Short ATTACH names for the script:
PRYA-BASE, GUN-A7, GUN-GOLD, LIVINGROOM-RUINED, LINEUP. Keep a legend table
mapping short names to files.

## Step 5 - Per-page ATTACH plan

Go back through the script and add one line to every page that needs
generation, directly under the aspect ratio:

**ATTACH:** CHARACTER-STATE (REF-XX) + PROP-STATE (REF-YY) + ENVIRONMENT (REF-ZZ) + LINEUP (size N)

Rules:
- Attach the sheet for every asset visibly in the shot.
- Attach LINEUP on every page where a size number is stated.
- Mid-transformation pages: attach the TARGET state sheet + LINEUP at the
  intermediate size ("between size 2 and 3").
- Transition pages that change an environment or prop state (roof breach
  forming, gun being snapped): attach BOTH the before and after sheets.
- Cap ~5 attachments per generation. Mark background/blurred-figure refs as
  "optional" - drop those first if the model degrades with too many references.
- Existing already-generated pages need no ATTACH line - mark the section
  "no attachments needed".
- Early pages of a location with no sheet yet can chain:
  "original page N image as environment ref".

## Step 6 - Usage map

End the reference document with a table: sheet -> page ranges where it gets
attached. This is the QC checklist during batch generation.

## Integration with the rest of the pipeline

- The GLOBAL RULES block still goes at the end of every page prompt. For
  stories with drains/reductions, replace the "sizes never revert" rule with
  "sizes must match EXACTLY the size stated in this prompt" and state exact
  sizes on every page.
- Keep the size continuity cheat sheet (page ranges x character x size/height)
  next to the usage map; the two tables together catch 95% of continuity
  errors before generation.
- Face-heavy shots: use a close-up page/panel as the character ref instead of
  the full sheet; full-body sheets weaken face fidelity in extreme close-ups.

## Worked example (from "Ritual Gone Wrong")

Script audit of a 43-page act produced 12 sheets: 2 characters x 3 states
each (goddess/drained/reborn) = 6, villain x 2 extra states (giant/defeated)
= 2, gun x 2 states (charged/broken) = 2, environments = 4 (mansion ext,
pool, living room intact, living room ruined) - plus a runestone prop
turnaround discovered by auditing Act 1. Pages 50 and 65 attached
before+after sheets (roof breach forming; gun mid-snap). Page 41 attached
goddess FACE refs only + LINEUP size 4, because the bodies were mid-drain
and matched neither state sheet.
