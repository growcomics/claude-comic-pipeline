---
name: page-composer
description: Assemble approved comic panels into finished pages — pick a layout (grid, splash, irregular), arrange panels with gutters, place speech balloons and captions from the shotlist's dialogue, render SFX, save page images, and optionally export a print-ready PDF. Use when the user wants to compose pages, lay out panels, add speech bubbles, letter the comic, build the final pages, finalize the chapter, or export to PDF. Trigger phrases include "compose the pages", "layout the panels", "add speech balloons", "letter the comic", "finalize pages", "build the page", "export to PDF", "assemble the chapter".
---

# Page Composer

Final assembly. Take approved panel images plus the shotlist's dialogue and stage directions, lay panels into pages, place balloons and captions, render SFX, and write `pages/page-NN.png`. Optionally export a chapter PDF.

Runs last in the comic pipeline. Inputs come from `script-breakdown` (shotlist), generation (panel PNGs), `continuity-check` (clean panels), and `style-lock` (font and balloon styling).

## When this skill is the right tool

- "Compose the pages"
- "Letter the comic"
- "Add speech bubbles"
- "Build the final pages for chapter 3"
- "Export the chapter as a PDF"

If panels are still being generated or contain known continuity errors, push back: lettering on bad panels wastes work.

## Inputs

- `shotlist.json` — pages, panels, dialogue, captions, sfx, layout hints (`size`)
- `pages/panels/<panel_id>.png` — approved panels, one per shotlist panel_id
- `style.md` — font choice, balloon stroke/fill, SFX styling under "Lettering hints"
- (optional) `pages/_template.png` — page background, bleed marks, trim guides

## Output

- `pages/page-NN.png` — one PNG per page at print resolution
- `pages/_index.md` — page list with thumbnails
- `pages/<project>.pdf` — only if user asks

Default page size: **2048×3072** (2:3 portrait, print-friendly at ~300 DPI for 6.83×10.25"). Override via `style.md` or user request.

## Layout strategies

Pick layout per page based on panel count and `size` hints in shotlist:

| Panels per page | size hints                | Layout                                  |
|---|---|---|
| 1 | `splash`                  | Full-page bleed                         |
| 2 | `wide` × 2                | Two horizontal stacks                   |
| 2 | `tall` × 2                | Two vertical columns                    |
| 3 | `wide` + 2 `standard`     | Wide top row, two `standard` below      |
| 4 | all `standard`            | 2×2 grid                                |
| 5 | mixed                     | Wide top, 2×2 below — or hero + 4       |
| 6 | all `standard`            | 2×3 or 3×2 grid                         |
| 7+ | dense                    | 3×3 truncated, or irregular Z-grid      |

Default gutter: **20px** between panels, **40px** page margin. Override via `style.md`.

## Workflow

### 1. Group panels by page

Read `shotlist.json`. Group `panels[]` by `page_number`. Verify each panel image exists at `pages/panels/<panel_id>.png` — bail with a clear error listing missing panels rather than composing a half-page.

### 2. Pick the layout

Use the table above. If the user has a per-page layout file (`pages/layouts/page-NN.json`), prefer that.

### 3. Render the page background

Open a blank canvas at page size. Apply `style.md` page color (default white) and any template overlay (trim, bleed, page-number area).

### 4. Place panels

For each panel:

1. Compute its target rectangle in the layout
2. Resize the panel image to fit. Preserve aspect; for `splash` use bleed (cover whole page), for `standard` fit-with-letterbox or center-crop based on shotlist `camera` cue
3. Stroke a black 4px border (overridable via `style.md`)
4. Paste

### 5. Place balloons

For each panel's `dialogue[]`:

1. **Choose a position.** Default: top-left for the first speaker in `dialogue[]`, top-right for the second, descending if more. Avoid covering the speaker's face — the shotlist's `characters[]` order is left-to-right, so place tails near the matching side of the panel.
2. **Word-wrap** the text at ~16px font height, ~25 chars per line. Balloons grow to fit; should not exceed 35% of the panel's height. If a balloon would exceed, raise it back to the user — splitting a single dialogue line mid-sentence is a writing decision, not a layout one.
3. **Render shape by `type`:**
   - `balloon` — round/oval with smooth tail
   - `thought` — cloud-shaped, tail of small bubbles
   - `whisper` — dashed border
   - `shout` — jagged star outline
   - `caption` — rectangular, top-corner of panel
   - `off-panel` — balloon with tail pointing past the panel edge
4. **Stroke** 2px black, **fill** white. Caption boxes use yellow tint per `style.md` (default #FFF4B8).
5. **Tail** points from the balloon to the speaker's approximate mouth. Without an explicit position, point to the upper-third of the speaker's region of the panel.

Reading order: balloons within a panel read top-to-bottom, left-to-right. The shotlist `dialogue[]` array order wins on ambiguity; chain balloons visually so the tail-line implies sequence (avoid crossing tails).

### 6. Place captions

`captions[]` go in a yellow-tinted rectangle, top-left or top-right, never overlapping a balloon. If the panel already has a caption from the previous panel's continuation, place the new one below it.

### 7. Place SFX

For each `sfx[]`:

- Render the text in the display font from `style.md` (default WildWords-Bold or a free comic font)
- Default position: lower-third of the panel, away from balloons
- Scale: short SFX (3–5 chars) → 60–80px; long SFX → 40–60px
- Color: per `style.md` SFX palette; default black with red 2px drop shadow for impact

### 8. Save the page

Write `pages/page-NN.png`. Append a row to `pages/_index.md`:

```markdown
| Page | Panels | Layout | Image |
|------|--------|--------|-------|
| 01   | 4      | 2x2    | ![](page-01.png) |
```

### 9. Export PDF (optional)

If the user asked, stitch all pages into `pages/<project>.pdf`. Use `img2pdf` (no recompression — preserves source quality) over ImageMagick (re-rasters and degrades).

## Tools

- **Python + Pillow** via Bash for canvas, panel placement, and balloon rendering. `ImageDraw` handles ellipses, polygons (jagged shouts), and rounded rects (captions).
- **`textwrap` + Pillow's `getbbox`** for balloon sizing
- **ImageMagick** when Pillow hits a limit (gradients, complex filters)
- **`img2pdf`** for PDF export
- A comic-style font file (WildWords, Komika Axis, or a free alt). Path in `style.md`.

Write a small script at `scripts/compose-page.py` rather than embedding everything in shell — it's easier to debug and re-run per-page.

## Hard rules

- **Don't compose with missing panels.** A blank slot looks worse than no page. List the missing panel_ids and stop.
- **Don't auto-rewrite dialogue to fit.** If a balloon's text is too long, raise it back to the user — splitting dialogue mid-sentence is a writing decision.
- **Reading order is sacred.** A page where balloons read out of order is broken regardless of how good the art is.
- **Never letter on a continuity-flagged panel.** Run `continuity-check` first.
- **Don't crop faces or hands to fit a layout.** Adjust the layout instead. Faces and hands are the readers' anchor; cropping them ruins the page.
- **No balloons covering action-critical objects.** If the panel's action depends on the sword being visible, route the balloon away from the sword even if it means an unusual placement.

## Common asks

- "Just splash pages" — set every page's layout to splash; one panel per page; ignore mixed-size hints
- "Tighter gutter" — reduce gutter to 12px in the script call
- "Change the font" — update `style.md` font path; re-run
- "Black-and-white version" — desaturate panels before placement; balloons unchanged
- "Print prep" — flag a separate pre-press pass (CMYK conversion, ICC profile, bleed/trim marks); don't bundle that into composition

## Hand-off

After this skill, the chapter is shipping-ready as PNGs (and optionally PDF). For print-prep (CMYK, ICC, bleed marks), suggest a separate pre-press pass — that's a different concern from composition.
