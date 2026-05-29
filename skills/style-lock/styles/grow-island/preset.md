# Grow-Island — Style Preset

Slug: `grow-island`
Default: no
Trigger: put **`grow-island style`** (or `grow-island` / `GI style` / `#grow-island` / `style: grow-island`) anywhere in a build prompt to select this preset. Case-insensitive substring match — see `SKILL.md` → "Quick-select triggers".
Aesthetic: photoreal DAZ3D CGI rendered as a **reality-TV "cinematic still"** —
one full-bleed landscape splash per page, warm tropical-resort palette,
baked-in comic lettering (bubbles + ID caption plates + gradient SFX), and an
on-demand **before/after pose-reuse growth-reveal** grammar. Conversational,
eye-level, character-driven.

This preset shares the **render** of `photoreal-daz3d` (same DAZ3D Iray skin,
no ink lines, no cel shading) but overrides the **page construction, framing
grammar, palette, lettering, and transformation technique**. Pick it for
reality-show / dating-competition formats and any project that wants the
"one page = one wide cinematic still with baked dialogue" look instead of the
default 3:4 multi-panel-in-page-composer flow.

Derived from a full 63-page study of the *Grow Island* pilot (see
`notes.md` in this folder for the deep visual analysis, cast/locations/story
breakdown, and continuity audit it was reverse-engineered from).

## How to use

1. Copy the **Template** block below into `style.md` at the project root.
2. Fill the placeholders (`<project>`, `<date>`, cast wardrobe-accent table,
   location constants, growth tiers).
3. Lock the file. Every panel prompt must include the prefix and suffix
   verbatim, render ONE full-bleed landscape splash, and bake lettering in.

## Template — paste into `style.md`

```markdown
# Style Lock — <project>  (Grow-Island style)

Locked <date>. Every panel prompt must include the prefix and suffix below
verbatim. This project renders photoreal DAZ3D CGI as ONE full-bleed
landscape "cinematic still" per page, with comic lettering BAKED INTO the
render.

## Model
- Name: Nano Banana 2 Pro (Flash for draft/speed passes)
- Aspect: 16:9 landscape — ALL pages (one full-bleed splash per page)
- Resolution: 1K (2K only for cover/title splashes)
- Batch: Higgsfield 1/submit (paid) · Flow 4/submit (free); QA picks best
- Seed strategy: per-page deterministic seed = hash(page_id)

## Mandatory prompt prefix
> Hyperrealistic DAZ3D Studio 3D CGI render, ray-traced subsurface scattering
> on skin, physically-based rendering, single full-bleed widescreen comic
> splash, one cinematic still,

## Mandatory prompt suffix
> warm tropical-resort lighting, soft diffuse key with gentle specular
> sculpting, shallow depth of field with background softened to bokeh so the
> figure is the sharpest element, eye-level camera, photographic CGI,
> NO panel grid, NO interior gutters, single image only

## Mandatory negative prompt
> multi-panel grid, comic page with gutters, multiple framed panels,
> 2D illustration, cartoon, anime, cel shading, ink outlines on bodies,
> painterly, flat front-flash lighting, portrait/tall aspect, watermark,
> deformed hands, extra limbs, plastic skin, characters staring at camera
> (except hosts/confessionals)

## Page grammar (HARD rules — this is the identity of the style)
- ONE full-bleed landscape splash per page. Never a multi-panel grid, never
  interior gutters. One page = one cinematic still.
- Camera is EYE-LEVEL by default. Reserve angle changes for intent:
  low-angle to monumentalize a growing body/figure; slight high-angle for
  intimacy; dramatic high/dutch only in stair/transition beats; bird's-eye
  only for an exterior establishing finale.
- Shot-distance rhythm: MEDIUM / medium-close for dialogue (subject fills
  55–90% of frame); WIDE establishing for scene-setting & ensembles;
  EXTREME body-part crops (often faceless) for growth beats; FULL-BODY only
  for a transformation reveal.
- Compose simply: one dominant subject, centered or symmetrical. Leave clear
  negative space for the baked bubble stack. Use in-frame framing devices
  (doorways, a potted plant as a center divider, a foreground body as a
  framing column, architecture lines).
- Backgrounds are photoreal but SOFTENED / shallow-DOF on close & medium
  shots; only sharpen the environment on wide reveals.

## Color & lighting
- Warm tropical-resort base: tans, beige, cream, golden wood-brown, bronze
  tanned skin. Moderate saturation, low–moderate contrast.
- TWO lighting modes, switched by scene: (A) WARM interior/day — soft, flat,
  cozy amber lamp glow; (B) COOL night — navy/black sky, dark teal water,
  low-key drama, warm key on faces, optional neon magenta/lime deck accents.
- ONE high-chroma WARDROBE accent per character/arc is the focal pop against
  the neutral set (document per character below). Reuse the same accent every
  appearance — it is character identity, not mood.

## Cast wardrobe-accent table (project-specific — HARD rules)
- <character A>: <accent color + garment>   (e.g. "red ribbed bikini")
- <character B>: <accent color + garment>   (e.g. "cyan/turquoise trunks")
- ...keep stable across all appearances; clothing may tear/strain but the
  accent hue never changes.

## Growth-reveal technique (the signature device)
- On-demand, body-part-at-a-time, MONOTONIC (never shrinks back).
- Render each beat as a BEFORE/AFTER POSE-REUSE PAIR: two consecutive pages
  share an identical composition/pose; the second shows the localized size
  increase PLUS an SFX word placed adjacent to the changed body part.
- Chain the pair view-aware: the "after" page references the "before" page
  job + the canonical face ref (see comic-production Key Rule #8/#9).
- End a transformation on a FULL-BODY reveal page.

## Lettering — BAKED INTO THE RENDER (do not defer to page-composer)
- Speech: white oval/round bubbles, thin 2–3px black outline, short pointed
  tail to the speaker, ALL-CAPS bold comic sans-serif. Stack multiple bubbles
  vertically down one side for back-and-forth / monologue.
- Character-ID plates: small white rounded rectangle, thin black border, black
  ALL-CAPS "NAME – ROLE" (e.g. "VIVIAN – FITNESS INFLUENCER"). Intro pages.
- Title / time tab: small black box, white ALL-CAPS ("DAY 1", "NIGHT 1").
- SFX: bold ALL-CAPS block letters, ORANGE→YELLOW vertical gradient fill,
  black outline + drop shadow, slight italic, often a small red/orange jagged
  burst graphic, placed beside the changing body part ("GROW!", "BOOM",
  "TONED!", "CAKE", "POW!").
- Non-verbal sounds (*GASP*, *PHEW*, stretched vowels "EEEEE") go INSIDE
  ordinary speech bubbles, not as drawn SFX.
- Eyes look at each other / off-camera — NEVER at the viewer, EXCEPT a host
  addressing the show or a confessional aside (flat-wall backdrop).

## Title / chapter device
- Title pages: a flat white knockout SILHOUETTE of a muscular female in a
  double-biceps flex, splitting the logo "GROW [figure] ISLAND", over a
  photoreal villa establishing shot, with a black time-tab ("DAY 1").

## Banned
- Multi-panel grids / gutters / portrait aspect (this style is one wide splash).
- Ink outlines, cel shading, painterly or 2D-illustration rendering on bodies.
- Front-flat flash lighting; characters staring at camera in narrative beats.
- Lettering applied in post — text is baked at generation time here.

## Style sample reference
- Canonical reference set: the Grow-Island pilot pages (see notes.md).
- Lock-in re-test prompt: "<character> standing in the tropical villa lounge,
  medium eye-level shot, one full-bleed landscape splash, full prefix/suffix,
  baked white speech bubble reading '<line>'".
- Drift check: re-run every 10 pages; compare splash format, palette, bubble
  style, and that the figure is the sharpest element.
```

## Why these choices

- **One full-bleed landscape splash per page** is the single most defining
  trait of the source comic — all 63 pages are one wide cinematic still with
  zero multi-panel grids or gutters. The negative prompt explicitly bans
  `multi-panel grid` and `portrait aspect` because Nano Banana defaults to
  taller framing and will invent gutters if not suppressed.
- **Render prefix names "DAZ3D Studio 3D CGI" + "single full-bleed widescreen
  comic splash"** — the render half matches `photoreal-daz3d`; the structural
  half is what carries this preset's identity.
- **Baked lettering** — unlike the default preset (lettering deferred to
  `page-composer`), Grow-Island bakes bubbles, ID plates, and gradient SFX
  into the render. This matches comic-production **L19** (baked lettering,
  unconditional as of 2026-05-25). The SFX recipe (orange→yellow gradient +
  black outline + drop shadow, adjacent to the changing body part) is specific
  because vague "comic SFX" under-renders.
- **Single high-chroma wardrobe accent per character** — the source leans hard
  on this (red bikini, cyan trunks, mauve-pink sweater, red-and-white stripes)
  to keep characters legible against a deliberately neutral tan/cream set.
  Documented as a hard rule so `continuity-check` can flag accent swaps.
- **Before/after pose-reuse growth pairs** — the source renders transformations
  as identical-composition page pairs with a localized change + adjacent SFX,
  rather than a single morph panel. This is reproducible and reads cleanly;
  chain it view-aware (Key Rule #9) so the body state carries forward.
- **Eye-level conversational grammar with softened backgrounds** — pushes the
  generator off cinematic clutter toward the source's portrait-driven,
  one-subject-dominant staging where the body is always the sharpest element.

## When to pick this preset

- Reality-TV / dating-competition / "house" formats and ensembles of named
  contestants delivered through dialogue.
- Projects that want wide cinematic single-splash pages with baked dialogue
  instead of the default 3:4 multi-panel-in-page-composer flow.
- On-demand, body-part-at-a-time transformation arcs that benefit from the
  before/after pose-reuse reveal grammar.

For a different render (ink/illustrated) use `ink-line`; for the standard
photoreal multi-panel book use the default `photoreal-daz3d`.
