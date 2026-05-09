# Ink-line — Style Preset (secondary)

Slug: `ink-line`
Default: no
Aesthetic: modern indie / Eurocomic ink-line look. Heavy outer line, medium
interior detail, cel-shaded with hard directional shadows. Limited palette.
NOT photoreal.

This preset is kept as a secondary example to demonstrate the folder shape
and to support stylized projects (flashbacks, dream sequences, side stories).
For the default photoreal-DAZ3D look used by Bay Watch / Lana & Lacy, see
`styles/photoreal-daz3d/preset.md`.

## How to use

1. Copy the **Template** block below into `style.md` at the project root.
2. Fill the placeholders.
3. Lock the file. Every panel prompt must include the prefix and suffix
   verbatim.

## Template — paste into `style.md`

```markdown
# Style Lock — <project>

Locked <date>. Every panel prompt must include the prefix and suffix below
verbatim.

## Model
- Name: <higgsfield-model-id>
- CFG / guidance: 6.5
- Sampler: <sampler>
- Seed strategy: per-panel deterministic seed = hash(panel_id)
- Resolution: 1536×1024 (landscape) | 1024×1536 (tall) | 2048×2048 (splash)

## Mandatory prompt prefix
> dynamic comic panel, heavy 2pt outer line with medium interior detail,
> cel-shaded with hard 35° shadows, modern indie comic aesthetic

## Mandatory prompt suffix
> directional key light from upper-left, no rim light, 35mm lens equivalent,
> no painterly softness

## Mandatory negative prompt
> photoreal skin texture, instagram filter, watermark, text artifacts,
> deformed hands, extra fingers, cropped face, 3D render, DAZ artifacts,
> stock-flash lighting

## Color palette
- Hex: #1a1a2e, #f5deb3, #c44536, #2e8b57, #f0f0f0
- Rule: max 4 dominant hues per panel; cool palette for night scenes,
  warm for action

## Line weight
- Outer silhouette: heavy (2pt equivalent)
- Interior detail: medium (1pt)
- Background: light (0.5pt)

## Rendering
- Cel-shaded, minimal gradients
- Hard shadows at 35° from upper-left
- No painterly softness, no airbrush

## Lettering hints (read by page-composer)
- Font: WildWords-Bold (./assets/fonts/WildWords-Bold.ttf)
- Balloon stroke: 2px black, white fill
- Caption: yellow tint #FFF4B8
- SFX: black with 2px red drop shadow

## Banned
- Photoreal skin pores
- 3D render look (DAZ artifacts)
- Stock-art front-flash lighting
- Anime-style giant eyes (unless this is an anime project)

## Sample shot
- Reference panel: pages/_style-sample.png
- Re-test prompt: "<character> standing in <location>, neutral pose, full
  prefix and suffix"
- Drift check: re-run weekly or every 10 panels; compare to baseline.
```

## When to pick this preset

- Stylized / illustrated comic projects (not photoreal).
- Flashback or dream-sequence chapters within an otherwise photoreal book.
- Eurocomic / modern indie aesthetics where heavy outer line and limited
  palette are core to the visual identity.

For mixed-style projects, tag panels with `"style": "ink-line"` in
`shotlist.json` so the panel-prompt builder loads this preset instead of the
project's default.
