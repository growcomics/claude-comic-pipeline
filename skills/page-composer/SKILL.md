---
name: page-composer
description: Assemble accepted panel images into composed pages and optionally export a PDF. Runs after panels are approved and continuity-check has passed. Single-image-per-page is the default mode; multi-panel grid layouts are supported. Does NOT letter — speech bubbles, captions, and SFX are baked into the panels at generation time per L19 (unconditional as of 2026-05-25). Trigger phrases include "compose the pages", "finalize pages", "build the pages", "export to PDF", "assemble the chapter".
---

# Page Composer

Final layout + PDF export. Take accepted panel images (which already contain baked lettering from generation) and assemble them into composed pages. Optionally export a chapter PDF.

Runs last in the comic pipeline. Inputs come from `script-breakdown` (shotlist for page structure) and image generation (panel PNGs that already include speech bubbles, captions, and SFX baked in per L19). Run `continuity-check` first — layout on bad panels wastes work.

## What changed (2026-05-25)

This skill **no longer adds lettering** to panels. The earlier vector-overlay lettering path was retired alongside the `mandatory_rules.skip_baked_lettering` opt-out. As of 2026-05-25, lettering bakes at panel-generation time per L19; the accepted PNGs already contain speech bubbles, captions, and SFX as flat 2D comic-book overlay graphics composited onto the photoreal CGI scene.

`page-composer` is now strictly:

1. **Layout** — place panels onto pages (single-image-per-page or multi-panel grid).
2. **PDF export** — optionally bundle pages into a chapter PDF.

If you want to letter a generated panel, that happens at the generation step. To re-letter an approved panel, regenerate it with updated `dialogue[]` / `captions[]` / `sfx[]` arrays in the shotlist — the per-panel render is fast enough that this is the right path.

## Two modes (auto-detected from shotlist)

**Single-image-per-page** (default for modern issues): every page has exactly one panel. The panel image fills the whole page (fit-cover). This is the dominant mode for "every page is one hero image" comics. The panel's already-baked lettering is preserved as-is in the page output.

**Multi-panel**: pages have multiple panels. The script applies a simple even grid layout (1/2/3/4 panels via 1×N, 2×2; 5–6 via 2×3). Layout polish (irregular grids, splash detection within a page, hero panel sizing) is deferred — see Upgrade path below.

Mode is picked per page: a 30-page comic where page 22 has 1 panel and page 5 has 3 panels renders each page in its own mode.

## When this skill is the right tool

- "Compose the pages"
- "Assemble the chapter"
- "Finalize pages and export PDF"
- "Lay out the panels into pages"
- "Build the chapter PDF"

## When this skill is NOT the right tool

- "Add speech balloons to this panel" — that's not this skill anymore. Lettering is baked at generation. Regenerate the panel with the dialogue in the shotlist.
- "Letter the comic" — same answer; this skill no longer adds lettering. Per L19, lettering is part of the generated panel.
- "Fix a typo in this bubble" — regenerate the panel with the corrected text in `dialogue[]`. The single-stage workflow trades editability for visual integration.

## Inputs

- `shotlist.json` — pages[], each with panels[] for page-structure; the panel's `dialogue[]` / `captions[]` / `sfx[]` are NOT read by this skill (they were read at generation time by `comic-production`)
- `pages/panels/panel-<id>/v*_accepted.png` or `v1.png` — accepted panel images **including baked lettering**
- (legacy fallback) `pages/panels/<panel_id>.png` — flat layout

The script resolves panel images in this order: `panel-<id>/v*_accepted.png` (most recent), `panel-<id>/v1.png`, then the flat fallback.

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

## What the script does NOT do anymore

The pre-2026-05-25 script supported vector lettering overlays — Pillow-rendered speech bubbles, captions, SFX laid onto clean panels. That code path is retired:

- `--no-lettering` flag: removed (lettering was never added by this skill anymore).
- `mandatory_rules.skip_baked_lettering`: removed from `production-config.json` schema.
- Pillow text rendering: code remains in the script for potential future restoration but is no longer invoked. Marked deprecated in the source.

If you encounter a project written before 2026-05-25 that has clean (unlettered) panels expecting page-composer to add bubbles, the right migration is to regenerate the panels with the same shotlist on the current pipeline — the dialogue/caption/SFX arrays are already in the shotlist, the new generation pass bakes them in.

## Single-image-per-page mode details

For each page:
1. Read the page entry from `shotlist.json`.
2. Resolve the single panel's accepted PNG.
3. Place onto a 2048×3072 page canvas, fit-cover (the panel may be wider or taller than the page; crop to fill or letterbox per panel `aspect_ratio` and `crop_strategy` fields).
4. Save as `pages/composed/page-NN.png`.

No lettering pass. The panel already contains it.

## Multi-panel mode details

For each page:
1. Read all panels in the page entry.
2. Pick a grid layout based on count (1 → full bleed, 2 → 1×2, 3 → 1×3, 4 → 2×2, 5–6 → 2×3).
3. Place each accepted panel into its grid cell with a configurable gutter (default 24px).
4. Save as `pages/composed/page-NN.png`.

Each panel already contains its lettering. Gutters do not include any lettering — captions and bubbles live inside their panel.

## PDF export

With `--pdf`, after all pages are composed, bundle them into a single PDF at `pages/<project>.pdf`. Page order follows `shotlist.json`'s `pages[]` order. Per-page aspect ratios are preserved (PDF page sizes can vary).

## Fonts

The legacy lettering code referenced these env vars. They are no longer functional but the variables are documented for transparency:
- `COMIC_FONT_DIALOG`, `COMIC_FONT_SFX`, `COMIC_FONT_CAPTION` — IGNORED as of 2026-05-25.

Fonts in the panel images are determined by the generation model (Nano Banana / GPT Image), not by this skill.

## Upgrade path

Future work to consider (not currently in scope):
- **Irregular grids** — splash + 3 grid panels on the same page (e.g. 1 large + 3 small).
- **Bleed and trim marks** — print-spec page output.
- **Per-page background paper texture** — a flat off-white paper layer behind the panels for issue-style finish.
- **Cover composition** — full-bleed cover with title overlay (cover-specific, not panel-derived).

None of these involve lettering. If a future need surfaces for post-render lettering corrections, build it as a separate `lettering-patch` skill rather than reintroducing the dual-path complexity here.
