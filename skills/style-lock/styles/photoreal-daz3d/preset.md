# Photoreal-DAZ3D — Style Preset (default)

Slug: `photoreal-daz3d`
Default: **yes**
Aesthetic: photorealistic 3D-rendered comic in the "DAZ3D Iray / 3D Muscle Comics"
house style. Skin micro-detail, golden-hour outdoor lighting, no ink lines, no
cel shading, no text or speech bubbles baked into the image.

This is the canonical preset for the Lana & Lacy / Bay Watch product. It is
also a sensible default for any photoreal-3D comic project. If you want a
stylized, illustrated look instead, see `styles/ink-line/preset.md` or add a
new preset (instructions in `styles/README.md`).

## How to use

1. Copy the **Template** block below into `style.md` at the project root.
2. Fill the placeholders (`<project>`, `<date>`, character energy-color rules,
   suit/wardrobe state by chapter, sample-shot reference page).
3. Lock the file. From this point, every panel prompt must include the prefix
   and suffix verbatim, and every powered panel must name the character's
   energy color explicitly.

## Template — paste into `style.md`

```markdown
# Style Lock — <project>

Locked <date>. Every panel prompt must include the prefix and suffix below
verbatim. This project uses photorealistic 3D rendering, NOT ink-line comic
style.

## Model
- Name: Nano Banana 2 Pro (use Flash for draft / speed passes)
- Aspect: 3:4 portrait — ALL panels without exception
- Resolution: 1K
- Batch: 4/4 (always generate 4 variants; QA selects best)
- Seed strategy: per-panel deterministic seed = hash(panel_id)

## Mandatory prompt prefix
> DAZ3D Iray photorealistic render, 3D Muscle Comics house style,

## Mandatory prompt suffix
> photorealistic skin micro-detail, golden-hour warm outdoor lighting,
> natural pore detail, no painterly softness, no watermarks
>
> (Lettering is baked via the L19 block — see the Lettering section. Body-photoreal
> is held by the L19 closing scope-bounded negation, not by a "no text" suffix.)

## Mandatory negative prompt
> cartoon-shaded skin, anime, painting, watercolor, ink lines on the bodies,
> watermark, plastic skin, oversmoothed, stock-flash front-lit
>
> (Body-photoreal is protected by the **L19 closing scope-bounded negation** in the
> positive prompt — *"NOT a 2D illustration on the bodies, NOT cartoon-shaded skin;
> only the bubble / caption / SFX graphics are flat 2D comic-book overlay."* Do NOT
> put `2D illustration` / `speech bubbles` / `text overlay` in the global negative —
> that suppresses the baked L19 lettering. See L19 in lessons-learned.)

## Elemental color rules (project-specific — HARD rules, not style hints)
- <character A>'s aura / lightning / eye glow: <COLOR A> (hex range)
- <character B>'s aura / lightning / eye glow: <COLOR B> (hex range)
- These colors are character identity, not mood lighting. Never swap them.
- Every powered panel must name the correct color explicitly in the prompt
  (e.g. "blue-white lightning crackling around <character A>").

## Scale continuity
Match scale to adjacent pages in the same chapter. Document the scale tiers
your project uses (e.g. baseline / charged / titan / goddess) and which
chapters each tier appears in.

## Wardrobe / suit state by chapter
Document each chapter's wardrobe state. Suits and outfits should evolve
deliberately, not jump between panels.

## Lettering — BAKED INTO THE RENDER (L19)
- Speech bubbles, captions, and SFX are **baked into the generated panel** as flat
  2D comic-book overlay graphics (auto-emitted by `next_panel.py`'s
  `_l19_lettering_block()` from the shotlist `dialogue[]` / `captions[]` / `sfx[]`),
  paired with the L19 closing scope-bounded negation so the bodies/scene stay
  photoreal CGI. `page-composer` is **layout + PDF only** — it does not letter.
- Baked-overlay style targets the model should render:
  - Font: bold comic display (e.g. WildWords-Bold or Comic Neue Bold), ALL CAPS
  - Balloon: clean white fill, bold black outline, tail to the speaker
  - Thought bubbles: round cloud shape with trailing circles
  - Captions: rounded rectangle, yellow tint, black outline
  - SFX: bold flat 2D, black or color matching the character's energy color

## Banned
- Ink outlines / cel shading / non-photorealistic rendering **on the bodies/scene** (the lettering overlay is the only 2D element)
- Front-facing flat flash lighting (all panels use directional natural light)
- Anime-style eyes or proportions
- Visible DAZ3D UI artifacts or render noise

## Style sample reference
- Canonical full-body / face reference image(s): <path or attachment>
- Lock-in re-test prompt: "<character> standing in <location>, neutral pose,
  full prefix and suffix"
- Drift check: re-run weekly or every 10 panels; compare to the locked sample.
```

## Why these choices

- **Nano Banana 2 (Pro / Flash) at 3:4, 1K** — the model whose default look is
  closest to DAZ3D photoreal output and which honors reference-image
  attachment most reliably. 3:4 portrait is the canonical Bay Watch aspect
  and mixes cleanly with multi-panel layouts in `page-composer`.
- **Prefix names "DAZ3D Iray photorealistic render"** — strong, specific cue
  that survives prompt-weighting. Vague terms ("photoreal", "3D") under-weight.
- **Suffix names "golden-hour warm outdoor lighting" + "natural pore detail"**
  — pushes the generator off its default stock-flash-lit ad aesthetic and
  toward the established Bay Watch look.
- **Negative prompt is load-bearing for the BODIES** — bans `cartoon-shaded skin`,
  `anime`, `ink lines`, `watermark`, `plastic skin`. It no longer bans
  `speech bubbles` / `2D illustration` globally (that would suppress the baked L19
  lettering); body-photoreal is held by the L19 scope-bounded negation in the
  positive prompt instead.
- **Elemental color rules** — character-identity colors (e.g. Lana=blue,
  Lacy=gold for Bay Watch) under-render unless named explicitly in the
  prompt. Documented as a project-level hard rule, not a style hint, so
  `continuity-check` can flag swaps.
- **Lettering is baked into the render (L19)** — bubbles/captions/SFX are part of
  the panel as scope-bounded flat 2D overlay, so each accepted panel is final and
  the text integrates with the scene instead of looking pasted on. `page-composer`
  is layout + PDF only. (Watch for AI-garbled text — re-roll the panel if a bubble
  is scrambled.)

## Reference-image attachment is required, not optional

Empirically (GROA-2 audit, 2026-05-09), reference-image attachment is the
primary character-identity lever in this pipeline — Higgsfield Souls are a
safety net, not the guarantee. Every panel that features a recurring
character must attach:

1. The canonical face/hair reference (e.g. `head-reference-sheet.jpeg`)
2. The closest canonical full-body shot for the current chapter

Without ref attachment, likeness drifts to a generic face even when the Soul
is loaded. Bake this into the panel-prompt builder, not into prose.

## Bay Watch / Lana & Lacy usage

The `lana-lacey-skill` repo's `series-profile.md` §2 ships a pre-filled
version of the **Template** above with Bay Watch energy-color and suit-state
rules already populated. For Bay Watch chapters, copy that block instead of
filling the template by hand.

## Banned for this preset

- Ink outlines, cel shading, painterly rendering, watercolor — those belong
  in a different preset (e.g. `styles/ink-line/preset.md`).
- Mixing photoreal and illustrated panels within the same chapter unless the
  script explicitly calls for it (flashbacks, dream sequences). For mixed
  styles, follow the per-panel `"style": "<slug>"` tagging convention in
  `shotlist.json` rather than rewriting `style.md`.
