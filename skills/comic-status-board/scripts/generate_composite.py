#!/usr/bin/env python3
"""Generate a composite board PNG at the project root.

Modes:
  references    Grid of all character/location/prop/style refs, grouped by
                bucket with section headers and labels per slug.
  generation    Panel sequence in story order, each panel shown at thumbnail
                size with an overlay strip showing the accepted version + attempt count.
  composition   Final lettered pages laid out in reading order.

All output is written to `<project_root>/STATUS-<mode>-board.png` (project
root — never buried in a subfolder).

Requires Pillow: `pip install Pillow`.

Usage:
    python generate_composite.py <project_root> --mode references
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("error: Pillow is required. Install with: pip install Pillow", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Configurable layout constants

WIDTH = 1600                # composite canvas width
CELL_W, CELL_H = 300, 375   # per-thumbnail cell (image area)
LABEL_H = 36                # label strip below each thumbnail
SECTION_HEADER_H = 56       # height of section headers (references mode)
PADDING = 24                # padding around the grid
GUTTER = 16                 # gutter between cells
BG = (16, 16, 18)           # composite background
CELL_BG = (32, 32, 36)
LABEL_BG = (24, 24, 28)
LABEL_FG = (220, 220, 220)
HEADER_BG = (44, 44, 52)
HEADER_FG = (255, 255, 255)
ACCENT = (255, 198, 102)    # accent color for accepted markers


def _font(size: int) -> ImageFont.ImageFont:
    """Best-effort font load with fallback to default."""
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
    ]
    for p in candidates:
        try:
            return ImageFont.truetype(p, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


# ---------------------------------------------------------------------------
# Helpers


def cols_for_width(width: int) -> int:
    """How many cells fit per row given WIDTH and PADDING/GUTTER."""
    usable = width - 2 * PADDING
    return max(1, (usable + GUTTER) // (CELL_W + GUTTER))


def thumbnail(src: Path, w: int, h: int) -> Image.Image:
    """Open an image and fit it into (w, h) preserving aspect — letterboxed."""
    try:
        img = Image.open(src).convert("RGB")
    except Exception:
        # Placeholder
        img = Image.new("RGB", (w, h), (60, 30, 30))
        d = ImageDraw.Draw(img)
        d.text((w // 2 - 30, h // 2 - 6), "(missing)", fill=(220, 180, 180), font=_font(14))
        return img
    img.thumbnail((w, h), Image.LANCZOS)
    canvas = Image.new("RGB", (w, h), CELL_BG)
    canvas.paste(img, ((w - img.width) // 2, (h - img.height) // 2))
    return canvas


def draw_label_strip(draw: ImageDraw.ImageDraw, x: int, y: int, w: int,
                     primary: str, secondary: str = "",
                     accent: bool = False):
    """Draw the label strip under a thumbnail."""
    draw.rectangle([x, y, x + w, y + LABEL_H], fill=LABEL_BG)
    font_a = _font(14)
    font_b = _font(11)
    draw.text((x + 8, y + 4), primary, fill=ACCENT if accent else LABEL_FG, font=font_a)
    if secondary:
        draw.text((x + 8, y + 20), secondary, fill=(160, 160, 165), font=font_b)


def draw_section_header(canvas: Image.Image, y: int, text: str) -> int:
    """Draw a section header at y. Returns new y after the header."""
    d = ImageDraw.Draw(canvas)
    d.rectangle([PADDING, y, canvas.width - PADDING, y + SECTION_HEADER_H], fill=HEADER_BG)
    d.text((PADDING + 16, y + 14), text, fill=HEADER_FG, font=_font(22))
    return y + SECTION_HEADER_H + GUTTER


# ---------------------------------------------------------------------------
# Mode: references


def render_references_mode(root: Path) -> Image.Image:
    refs_root = root / "references"
    if not refs_root.exists():
        return _empty_composite("No references/ folder yet.")

    # Collect items by bucket, deterministic order
    bucket_order = ["characters", "locations", "props", "style"]
    items_by_bucket: dict[str, list[tuple[str, Path]]] = {}
    for bucket in bucket_order:
        bdir = refs_root / bucket
        if not bdir.exists():
            continue
        items: list[tuple[str, Path]] = []
        for slug_dir in sorted(bdir.iterdir()):
            if not slug_dir.is_dir():
                continue
            primary = _pick_primary_ref(slug_dir, bucket)
            if primary is None:
                continue
            items.append((slug_dir.name, primary))
        if items:
            items_by_bucket[bucket] = items

    if not items_by_bucket:
        return _empty_composite("No references found in any bucket.")

    cols = cols_for_width(WIDTH)
    # Pre-compute height
    height = PADDING
    for bucket, items in items_by_bucket.items():
        rows = (len(items) + cols - 1) // cols
        height += SECTION_HEADER_H + GUTTER + rows * (CELL_H + LABEL_H + GUTTER)
    height += PADDING

    canvas = Image.new("RGB", (WIDTH, height), BG)
    draw = ImageDraw.Draw(canvas)

    y = PADDING
    for bucket, items in items_by_bucket.items():
        y = draw_section_header(canvas, y, f"{bucket.capitalize()} ({len(items)})")
        col = 0
        x = PADDING
        for slug, image_path in items:
            thumb = thumbnail(image_path, CELL_W, CELL_H)
            canvas.paste(thumb, (x, y))
            draw_label_strip(draw, x, y + CELL_H, CELL_W,
                             primary=slug,
                             secondary=f"{bucket}/{slug}")
            col += 1
            if col >= cols:
                col = 0
                x = PADDING
                y += CELL_H + LABEL_H + GUTTER
            else:
                x += CELL_W + GUTTER
        # End of bucket row
        if col != 0:
            y += CELL_H + LABEL_H + GUTTER

    return canvas


def _pick_primary_ref(slug_dir: Path, bucket: str) -> Path | None:
    """Choose the canonical image for a ref slug."""
    # Locations use _source.jpg as the env anchor
    if bucket == "locations":
        src = slug_dir / "_source.jpg"
        if src.exists():
            return src
    # Characters prefer face-card.png
    if bucket == "characters":
        for candidate in ("face-card.png", "face.png", "face-card.jpg"):
            p = slug_dir / candidate
            if p.exists():
                return p
    # Fall back to first image alphabetically
    for p in sorted(slug_dir.iterdir()):
        if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"} and not p.name.startswith("_"):
            return p
    # Last resort: any image including _-prefixed
    for p in sorted(slug_dir.iterdir()):
        if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
            return p
    return None


# ---------------------------------------------------------------------------
# Mode: generation


def render_generation_mode(root: Path) -> Image.Image:
    panels_root = root / "pages" / "panels"
    if not panels_root.exists():
        return _empty_composite("No pages/panels/ folder yet.")

    items: list[dict] = []
    for panel_dir in sorted(panels_root.iterdir()):
        if panel_dir.is_dir():
            versions = sorted(
                p for p in panel_dir.iterdir()
                if p.suffix.lower() in {".png", ".jpg"}
                and p.stem.startswith("v") and p.stem[1:].isdigit()
            )
            if not versions:
                continue
            accepted_marker = panel_dir / "_accepted.txt"
            accepted_label = None
            accepted_path = None
            if accepted_marker.exists():
                accepted_label = accepted_marker.read_text().strip()
                candidates = [v for v in versions if v.stem == accepted_label]
                if candidates:
                    accepted_path = candidates[0]
            display_image = accepted_path or versions[-1]
            items.append({
                "name": panel_dir.name,
                "attempts": len(versions),
                "accepted": accepted_label,
                "image": display_image,
            })
        elif panel_dir.suffix.lower() in {".png", ".jpg"}:
            # Flat layout — single revision
            items.append({
                "name": panel_dir.stem,
                "attempts": 1,
                "accepted": "v1",
                "image": panel_dir,
            })

    if not items:
        return _empty_composite("No panels generated yet.")

    cols = cols_for_width(WIDTH)
    rows = (len(items) + cols - 1) // cols
    height = PADDING + SECTION_HEADER_H + GUTTER + rows * (CELL_H + LABEL_H + GUTTER) + PADDING

    canvas = Image.new("RGB", (WIDTH, height), BG)
    draw = ImageDraw.Draw(canvas)

    accepted_count = sum(1 for it in items if it["accepted"])
    y = PADDING
    y = draw_section_header(canvas, y, f"Generation — {accepted_count}/{len(items)} accepted")

    col = 0
    x = PADDING
    for it in items:
        thumb = thumbnail(it["image"], CELL_W, CELL_H)
        canvas.paste(thumb, (x, y))
        attempts = it["attempts"]
        if it["accepted"]:
            primary = f"{it['name']}"
            secondary = f"accepted {it['accepted']} · {attempts} attempt{'s' if attempts != 1 else ''}"
            accent = True
        else:
            primary = f"{it['name']}"
            secondary = f"in progress · {attempts} variant{'s' if attempts != 1 else ''}"
            accent = False
        draw_label_strip(draw, x, y + CELL_H, CELL_W,
                         primary=primary, secondary=secondary, accent=accent)
        col += 1
        if col >= cols:
            col = 0
            x = PADDING
            y += CELL_H + LABEL_H + GUTTER
        else:
            x += CELL_W + GUTTER

    return canvas


# ---------------------------------------------------------------------------
# Mode: composition


def render_composition_mode(root: Path) -> Image.Image:
    pages_dir = root / "pages"
    if not pages_dir.exists():
        return _empty_composite("No pages/ folder yet.")
    pages = sorted(p for p in pages_dir.iterdir()
                   if p.is_file() and p.stem.startswith("page-") and p.suffix.lower() == ".png")
    if not pages:
        return _empty_composite("No composed pages yet.")

    # Use slightly larger cells for pages (they're the final product)
    page_w, page_h = 380, 540

    def thumb_page(src: Path) -> Image.Image:
        return thumbnail(src, page_w, page_h)

    cols = max(1, (WIDTH - 2 * PADDING + GUTTER) // (page_w + GUTTER))
    rows = (len(pages) + cols - 1) // cols
    height = PADDING + SECTION_HEADER_H + GUTTER + rows * (page_h + LABEL_H + GUTTER) + PADDING

    canvas = Image.new("RGB", (WIDTH, height), BG)
    draw = ImageDraw.Draw(canvas)
    y = PADDING
    y = draw_section_header(canvas, y, f"Composition — {len(pages)} pages")

    col = 0
    x = PADDING
    for p in pages:
        canvas.paste(thumb_page(p), (x, y))
        draw_label_strip(draw, x, y + page_h, page_w,
                         primary=p.stem, secondary=str(p.name))
        col += 1
        if col >= cols:
            col = 0
            x = PADDING
            y += page_h + LABEL_H + GUTTER
        else:
            x += page_w + GUTTER

    return canvas


# ---------------------------------------------------------------------------
# Empty placeholder


def _empty_composite(message: str) -> Image.Image:
    canvas = Image.new("RGB", (WIDTH, 240), BG)
    draw = ImageDraw.Draw(canvas)
    draw.text((PADDING, PADDING), message, fill=LABEL_FG, font=_font(20))
    return canvas


# ---------------------------------------------------------------------------
# CLI


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--mode", required=True,
                        choices=["references", "generation", "composition"])
    args = parser.parse_args()

    root = args.project_root.expanduser().resolve()
    if not root.exists():
        print(f"error: project root does not exist: {root}", file=sys.stderr)
        sys.exit(1)

    renderers = {
        "references": render_references_mode,
        "generation": render_generation_mode,
        "composition": render_composition_mode,
    }
    canvas = renderers[args.mode](root)
    out = root / f"STATUS-{args.mode}-board.png"
    canvas.save(out, optimize=True)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
