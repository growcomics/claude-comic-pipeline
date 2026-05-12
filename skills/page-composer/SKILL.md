---
name: page-composer
description: Letter the final comic — overlay speech balloons, captions, and SFX onto generated panel images and export composed pages and (optionally) a PDF. Use after panels are approved and continuity-check has passed. Supports single-image-per-page mode (one full-bleed image per page, lettering on top) and multi-panel mode (grid layout). Trigger phrases include "compose the pages", "letter the comic", "add speech balloons", "finalize pages", "export to PDF".
---

# Page Composer

Final assembly. Take approved panel images plus `shotlist.json` dialogue/caption/SFX data, overlay lettering, write `pages/composed/page-NN.png`, and optionally export a chapter PDF.

Runs last in the comic pipeline. Inputs come from `script-breakdown` (shotlist) and image generation (panel PNGs). Run `continuity-check` first — lettering on bad panels wastes work.

## Two modes (auto-detected from shotlist)

**Single-image-per-page** (default for modern issues): every page has exactly one panel. The panel image fills the whole page (fit-cover), lettering overlays directly on it. This is the dominant mode for "every page is one hero image" comics like the Supergirl issue.

**Multi-panel**: pages have multiple panels. The script applies a simple even grid layout (1/2/3/4 panels via 1×N, 2×2; 5–6 via 2×3) before lettering. Layout polish (irregular grids, splash detection within a page, hero panel sizing) is deferred — see Upgrade path below.

Mode is picked per page: a 30-page comic where page 22 has 1 panel and page 5 has 3 panels renders each page in its own mode.

## When this skill is the right tool

- "Compose the pages"
- "Letter the comic"
- "Add the dialogue / SFX overlay"
- "Finalize pages and export PDF"

## Inputs

- `shotlist.json` — pages[], each with panels[]; each panel has `dialogue[]`, `captions[]`, `sfx[]`
- `pages/panels/panel-<id>/v*_accepted.png` or `v1.png` — approved panel images (per the folder convention)
- (legacy fallback) `pages/panels/<panel_id>.png` — flat layout

The script resolves panel images in this order: `panel-<id>/v*_accepted.png` (most recent), `panel-<id>/v1.png`, then the flat fallback.

## Shotlist schema this script reads

```json
{
  "pages": [{
    "page_number": 3,
    "layout": "single-image",
    "panels": [{
      "panel_id": "03-lex-monologue",
      "captions": [{"text": "LEXCORP UNDERGROUND."}],
      "dialogue": [
        {"speaker": "lex", "type": "balloon", "text": "Hello, Kara."},
        {"speaker": "lex", "type": "thought", "text": "...the moment is here."},
        {"speaker": "kara", "type": "shout", "text": "LET ME OUT!"},
        {"speaker": "lex", "type": "whisper", "text": "Soon.",
         "speaker_position": {"x": 0.35, "y": 0.6}}
      ],
      "sfx": [{"text": "K-THUNK", "scale": "medium"}]
    }]
  }]
}
```

Bubble types: `balloon`, `thought`, `whisper`, `shout`, `caption`, `off-panel`.
SFX scales: `small`, `medium`, `large`.
`speaker_position` is **optional** — when present, the bubble's tail points at `(panel_x + w*sp.x, panel_y + h*sp.y)`. When absent, a short stub tail leans toward the bubble's column.

## Output

- `pages/composed/page-NN.png` — composed pages at 2048×3072 (override via env)
- `pages/composed/_index.md` — page list
- `pages/<project>.pdf` — only with `--pdf`

## Usage

```sh
python skills/page-composer/scripts/compose_page.py \
  --project /Users/<you>/Documents/<project> \
  [--pages 1-7]   # or --page 3 for a single page
  [--pdf]
```

Fonts default to macOS system fonts (Comic Sans MS Bold for dialogue, Impact for SFX, Arial Bold for captions). Override via env:
- `COMIC_FONT_DIALOG=/path/to/dialog.ttf`
- `COMIC_FONT_SFX=/path/to/sfx.ttf`
- `COMIC_FONT_CAPTION=/path/to/caption.ttf`

## Workflow

1. **Verify panels are approved.** If anything is still in `vN.notes.md` "revise" state, surface that and bail — don't letter a draft.
2. **Run continuity-check first.** Lettering on a panel with costume drift is wasted work.
3. **Run the script.** Compose a small batch (`--pages 1-3`) first to validate lettering placement, then the full run.
4. **Review composed pages inline.** Open each page-NN.png via Read and check: balloons cover faces? Captions over action? Tail going nowhere? If a tail is wrong, add `speaker_position` to that dialogue line in shotlist.json and rerun just that page.
5. **Export PDF** with `--pdf` once all pages look good.

## Hard rules

- **Don't letter on a continuity-flagged panel.** Run `continuity-check` first; address hard errors before composition.
- **Don't auto-rewrite dialogue to fit.** If a balloon overflows visibly, raise it to the user — splitting a line mid-sentence is a writing decision.
- **Reading order is sacred.** Within a panel the script renders dialogue in shotlist array order, stacked left/right by speaker. If the natural reading order conflicts with that stacking, the fix is to reorder the shotlist array, not to fight the layout.
- **No tails crossing the whole panel.** The script defaults to short stub tails when `speaker_position` is absent — if you need a long tail to a specific character, add `speaker_position` rather than letting a stub guess.
- **Never bake lettering into the generation prompt.** Lettering lives in shotlist data and is overlaid here — L7 Case B.

## Upgrade path (TODO, ranked)

The v1 Pillow renderer is intentionally simple. Logged upgrades:

1. **HTML/CSS + headless Chrome render** — real comic fonts, true curve tails, gradient SFX, CSS-templated balloon shapes. Adds a Chromium dependency. The biggest visual upgrade.
2. **Bubble auto-placement to avoid faces** — for single-image mode, run face detection on the panel and route bubbles away from detected faces. Pillow + OpenCV.
3. **Smart multi-panel layouts** — replace the even-grid fallback with irregular grids (hero panel + 3 small), splash detection, page-rhythm hints from shotlist.
4. **Custom comic fonts shipped in repo** — bundle a license-clean comic font (e.g. Bangers, Bowlby One) so cross-machine output matches without env var setup.
5. **Per-character bubble styling** — speaker-specific colors/borders (villain = sharper edges, narrator = different caption tint), driven by a `bubble_style` field on each cast entry.

These should land as separate skills/scripts, not as creep into compose_page.py.

## Hand-off

After composition, the chapter is shipping-ready as PNGs (and optionally PDF). For print prep (CMYK, ICC, bleed marks), suggest a separate pre-press pass — different concern.
