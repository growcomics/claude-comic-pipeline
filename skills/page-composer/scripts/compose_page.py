#!/usr/bin/env python3
"""
compose_page.py — Pillow-based lettering pass for the comic pipeline.

Reads a project's shotlist.json + per-page panel PNGs and renders lettered
pages (speech balloons, captions, SFX) to pages/composed/page-NN.png.

Two modes, auto-detected from shotlist:
  - single-image-per-page: every page has exactly 1 panel. The panel image
    fills the whole page; lettering overlays directly on it.
  - multi-panel: pages have >1 panels. Grid layout is applied first, then
    lettering. Multi-panel mode is implemented as a simple even grid;
    layout polish (irregular grids, splash detection) is deferred — see
    UPGRADE-NOTES.md.

Usage:
  python compose_page.py --project /path/to/project [--pages 1-7] [--pdf]
  python compose_page.py --project /path/to/project --page 3   # single page

Outputs:
  <project>/pages/composed/page-NN.png    (one per page)
  <project>/pages/composed/_index.md      (page list)
  <project>/pages/<project>.pdf           (only with --pdf)

Defaults:
  page size 2048x3072 (2:3 portrait, ~300 DPI for 6.83x10.25" print)
  fonts: Comic Sans MS Bold (dialogue), Impact (SFX), Arial Bold (captions)
  override via env vars: COMIC_FONT_DIALOG, COMIC_FONT_SFX, COMIC_FONT_CAPTION
"""

import argparse
import json
import os
import sys
import textwrap
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


PAGE_W, PAGE_H = 2048, 3072
PAGE_MARGIN = 40
GUTTER = 20

# Font resolution: env var > repo-bundled font > macOS system font > Pillow default.
# Bundled fonts live next to this script under ../fonts/ and ship with the repo
# so output is identical across machines. See ../fonts/README.md for licensing.

_FONTS_DIR = (Path(__file__).resolve().parent.parent / "fonts")
_BUNDLED_DIALOG = _FONTS_DIR / "ComicNeue-Bold.ttf"
_BUNDLED_SFX = _FONTS_DIR / "Bangers-Regular.ttf"
_BUNDLED_CAPTION = _FONTS_DIR / "ComicNeue-Bold.ttf"

_SYSTEM_DIALOG = "/System/Library/Fonts/Supplemental/Comic Sans MS Bold.ttf"
_SYSTEM_SFX = "/System/Library/Fonts/Supplemental/Impact.ttf"
_SYSTEM_CAPTION = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"


def _resolve_font(env_var: str, bundled: Path, system: str) -> str:
    override = os.environ.get(env_var)
    if override and Path(override).exists():
        return override
    if bundled.exists():
        return str(bundled)
    if Path(system).exists():
        return system
    return ""  # Pillow load_default fallback handled in load_font()


FONT_DIALOG = _resolve_font("COMIC_FONT_DIALOG", _BUNDLED_DIALOG, _SYSTEM_DIALOG)
FONT_SFX = _resolve_font("COMIC_FONT_SFX", _BUNDLED_SFX, _SYSTEM_SFX)
FONT_CAPTION = _resolve_font("COMIC_FONT_CAPTION", _BUNDLED_CAPTION, _SYSTEM_CAPTION)

CAPTION_FILL = (255, 244, 184)
CAPTION_STROKE = (0, 0, 0)
BALLOON_FILL = (255, 255, 255)
BALLOON_STROKE = (0, 0, 0)
THOUGHT_FILL = (255, 255, 255)
WHISPER_STROKE_DASH = True
SFX_FILL = (255, 255, 255)
SFX_STROKE = (0, 0, 0)


# ---------------------------------------------------------------------------
# Font loading

_font_cache: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}

def load_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    key = (path, size)
    if key not in _font_cache:
        try:
            _font_cache[key] = ImageFont.truetype(path, size)
        except (OSError, IOError):
            print(f"[warn] font {path} not found, falling back to default", file=sys.stderr)
            _font_cache[key] = ImageFont.load_default()
    return _font_cache[key]


# ---------------------------------------------------------------------------
# Text measurement + wrapping

def measure(draw: ImageDraw.ImageDraw, text: str, font) -> tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def wrap_to_width(draw, text: str, font, max_w: int) -> list[str]:
    """Greedy word-wrap so each line fits within max_w pixels."""
    words = text.split()
    if not words:
        return [""]
    lines: list[str] = []
    cur = words[0]
    for w in words[1:]:
        trial = cur + " " + w
        tw, _ = measure(draw, trial, font)
        if tw <= max_w:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


# ---------------------------------------------------------------------------
# Bubble rendering

@dataclass
class Bubble:
    text: str
    type: str          # balloon | thought | whisper | shout | caption | off-panel
    speaker: str
    side: str          # "left" | "right" — which half of the panel the bubble lives on


def render_caption_box(draw: ImageDraw.ImageDraw, text: str, x: int, y: int, max_w: int, font) -> tuple[int, int, int, int]:
    """Yellow caption rectangle. Returns the bounding box used."""
    pad = 16
    lines = wrap_to_width(draw, text, font, max_w - 2 * pad)
    line_h = measure(draw, "Ag", font)[1] + 4
    box_w = max(measure(draw, l, font)[0] for l in lines) + 2 * pad
    box_h = line_h * len(lines) + 2 * pad
    x2, y2 = x + box_w, y + box_h
    draw.rounded_rectangle([x, y, x2, y2], radius=8, fill=CAPTION_FILL, outline=CAPTION_STROKE, width=3)
    cy = y + pad
    for line in lines:
        draw.text((x + pad, cy), line, font=font, fill=(0, 0, 0))
        cy += line_h
    return (x, y, x2, y2)


def render_balloon(draw: ImageDraw.ImageDraw, b: Bubble, x: int, y: int, max_w: int, font, tail_anchor: tuple[int, int] | None) -> tuple[int, int, int, int]:
    """Speech/thought/shout/whisper balloon. Returns bounding box of the body (not the tail).

    Tail logic:
      - If `tail_anchor` is explicit (from dialogue's optional speaker_position),
        the tail points at it.
      - Otherwise we draw a SHORT stub tail just below the bubble, leaning
        toward the speaker's side. Long tails crossing the panel look broken
        when we don't know where the speaker actually is.
      - Shouts get no tail by default — the jagged outline carries the energy.
    """
    # Shape-specific padding: shouts need room past their jagged spikes,
    # thoughts past their ellipse pinch.
    if b.type == "shout":
        pad_x, pad_y = 46, 36
    elif b.type == "thought":
        pad_x, pad_y = 42, 30
    else:
        pad_x, pad_y = 24, 18
    lines = wrap_to_width(draw, b.text, font, max_w - 2 * pad_x)
    line_h = measure(draw, "Ag", font)[1] + 4
    body_w = max(measure(draw, l, font)[0] for l in lines) + 2 * pad_x
    body_h = line_h * len(lines) + 2 * pad_y

    x2, y2 = x + body_w, y + body_h

    # Tail (drawn first so the bubble body covers the seam)
    explicit_anchor = tail_anchor is not None
    if b.type != "caption":
        if b.type == "thought":
            anchor = tail_anchor if explicit_anchor else _stub_anchor(x, y, x2, y2, b.side, kind="thought")
            _thought_tail(draw, x, y, x2, y2, anchor)
        elif b.type == "shout":
            if explicit_anchor:
                _balloon_tail(draw, x, y, x2, y2, tail_anchor, b.side)
            # else: no tail
        else:
            anchor = tail_anchor if explicit_anchor else _stub_anchor(x, y, x2, y2, b.side, kind="balloon")
            _balloon_tail(draw, x, y, x2, y2, anchor, b.side)

    # Body shape
    if b.type == "shout":
        pts = _starburst_points(x, y, x2, y2, spikes=18, depth=0.12)
        draw.polygon(pts, fill=BALLOON_FILL, outline=BALLOON_STROKE)
    elif b.type == "thought":
        draw.ellipse([x, y, x2, y2], fill=THOUGHT_FILL, outline=BALLOON_STROKE, width=3)
    elif b.type == "whisper":
        draw.rounded_rectangle([x, y, x2, y2], radius=28, fill=BALLOON_FILL, outline=None)
        _dashed_rounded_rect(draw, x, y, x2, y2, radius=28, dash=14, gap=10, color=BALLOON_STROKE, width=3)
    else:
        draw.rounded_rectangle([x, y, x2, y2], radius=28, fill=BALLOON_FILL, outline=BALLOON_STROKE, width=3)

    # Text
    cy = y + pad_y
    for line in lines:
        tw, _ = measure(draw, line, font)
        cx = x + (body_w - tw) // 2
        draw.text((cx, cy), line, font=font, fill=(0, 0, 0))
        cy += line_h

    return (x, y, x2, y2)


def _stub_anchor(x, y, x2, y2, side: str, kind: str) -> tuple[int, int]:
    """A short tail anchor just below the bubble, leaning toward `side`."""
    body_w = x2 - x
    body_h = y2 - y
    drop = max(50, body_h // 2) if kind == "balloon" else max(80, body_h)
    if side == "left":
        ax = x + body_w // 4 - 10
    else:
        ax = x2 - body_w // 4 + 10
    ay = y2 + drop
    return (ax, ay)


def _balloon_tail(draw, x, y, x2, y2, anchor, side):
    cx = (x + x2) // 2
    cy = (y + y2) // 2
    # Tail origin: edge of bubble closest to anchor, on the speaker side
    if side == "left":
        base_x = x + (x2 - x) // 4
    else:
        base_x = x2 - (x2 - x) // 4
    base_y = y2 - 4
    # Triangle: two base points + anchor
    spread = 22
    pts = [
        (base_x - spread, base_y),
        (base_x + spread, base_y),
        anchor,
    ]
    draw.polygon(pts, fill=BALLOON_FILL, outline=BALLOON_STROKE)
    # Re-draw the base segment in fill color to hide the seam with bubble body
    draw.line([(base_x - spread + 2, base_y), (base_x + spread - 2, base_y)], fill=BALLOON_FILL, width=4)


def _thought_tail(draw, x, y, x2, y2, anchor):
    # Three shrinking circles from bubble edge toward anchor
    bx = (x + x2) // 2
    by = y2
    ax, ay = anchor
    steps = 3
    for i in range(1, steps + 1):
        t = i / (steps + 1)
        px = int(bx + (ax - bx) * t)
        py = int(by + (ay - by) * t)
        r = max(6, int(18 * (1 - t * 0.6)))
        draw.ellipse([px - r, py - r, px + r, py + r], fill=BALLOON_FILL, outline=BALLOON_STROKE, width=2)


def _starburst_points(x1, y1, x2, y2, spikes=16, depth=0.15):
    """Jagged-edge points around an ellipse-like bubble for shouts."""
    import math
    cx = (x1 + x2) / 2
    cy = (y1 + y2) / 2
    rx = (x2 - x1) / 2
    ry = (y2 - y1) / 2
    pts = []
    for i in range(spikes * 2):
        t = (i / (spikes * 2)) * 2 * math.pi
        r_scale = 1.0 if i % 2 == 0 else (1.0 - depth)
        pts.append((cx + rx * r_scale * math.cos(t), cy + ry * r_scale * math.sin(t)))
    return pts


def _dashed_rounded_rect(draw, x1, y1, x2, y2, radius, dash, gap, color, width):
    """Approximation: draw the four straight sides with dashes; corners stay as solid arcs."""
    # Top
    cur = x1 + radius
    while cur < x2 - radius:
        end = min(cur + dash, x2 - radius)
        draw.line([(cur, y1), (end, y1)], fill=color, width=width)
        cur = end + gap
    # Bottom
    cur = x1 + radius
    while cur < x2 - radius:
        end = min(cur + dash, x2 - radius)
        draw.line([(cur, y2), (end, y2)], fill=color, width=width)
        cur = end + gap
    # Left
    cur = y1 + radius
    while cur < y2 - radius:
        end = min(cur + dash, y2 - radius)
        draw.line([(x1, cur), (x1, end)], fill=color, width=width)
        cur = end + gap
    # Right
    cur = y1 + radius
    while cur < y2 - radius:
        end = min(cur + dash, y2 - radius)
        draw.line([(x2, cur), (x2, end)], fill=color, width=width)
        cur = end + gap
    # Corner arcs (solid)
    draw.arc([x1, y1, x1 + 2 * radius, y1 + 2 * radius], 180, 270, fill=color, width=width)
    draw.arc([x2 - 2 * radius, y1, x2, y1 + 2 * radius], 270, 360, fill=color, width=width)
    draw.arc([x1, y2 - 2 * radius, x1 + 2 * radius, y2], 90, 180, fill=color, width=width)
    draw.arc([x2 - 2 * radius, y2 - 2 * radius, x2, y2], 0, 90, fill=color, width=width)


# ---------------------------------------------------------------------------
# SFX rendering

def render_sfx(draw: ImageDraw.ImageDraw, text: str, x: int, y: int, scale: str, font_path: str):
    sizes = {"small": 56, "medium": 96, "large": 156}
    size = sizes.get(scale, 96)
    font = load_font(font_path, size)
    # Stroke + fill for chunky comic SFX
    draw.text((x, y), text.upper(), font=font, fill=SFX_FILL,
              stroke_width=max(3, size // 16), stroke_fill=SFX_STROKE)


# ---------------------------------------------------------------------------
# Page composition

def compose_single_image_page(panel_img_path: Path, panel: dict, out_path: Path) -> None:
    """Single-image-per-page: panel fills the page, lettering overlays."""
    src = Image.open(panel_img_path).convert("RGB")
    # Fit-cover into PAGE_W x PAGE_H
    page = _fit_cover(src, PAGE_W, PAGE_H)
    draw = ImageDraw.Draw(page)
    _letter_panel(draw, panel, x=PAGE_MARGIN, y=PAGE_MARGIN,
                  w=PAGE_W - 2 * PAGE_MARGIN, h=PAGE_H - 2 * PAGE_MARGIN)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    page.save(out_path, "PNG")


def compose_multi_panel_page(page_data: dict, panel_imgs: dict, out_path: Path) -> None:
    """Multi-panel page with simple even grid layout. Polish deferred (UPGRADE-NOTES.md)."""
    page = Image.new("RGB", (PAGE_W, PAGE_H), (255, 255, 255))
    panels = page_data["panels"]
    n = len(panels)
    cols, rows = _pick_grid(n)
    cell_w = (PAGE_W - 2 * PAGE_MARGIN - (cols - 1) * GUTTER) // cols
    cell_h = (PAGE_H - 2 * PAGE_MARGIN - (rows - 1) * GUTTER) // rows
    draw = ImageDraw.Draw(page)
    for idx, panel in enumerate(panels):
        c, r = idx % cols, idx // cols
        x = PAGE_MARGIN + c * (cell_w + GUTTER)
        y = PAGE_MARGIN + r * (cell_h + GUTTER)
        img_path = panel_imgs[panel["panel_id"]]
        src = Image.open(img_path).convert("RGB")
        fit = _fit_cover(src, cell_w, cell_h)
        page.paste(fit, (x, y))
        # Black border
        draw.rectangle([x, y, x + cell_w, y + cell_h], outline=(0, 0, 0), width=4)
        _letter_panel(draw, panel, x=x, y=y, w=cell_w, h=cell_h)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    page.save(out_path, "PNG")


def _fit_cover(src: Image.Image, w: int, h: int) -> Image.Image:
    sw, sh = src.size
    src_aspect = sw / sh
    target_aspect = w / h
    if src_aspect > target_aspect:
        new_h = h
        new_w = int(h * src_aspect)
    else:
        new_w = w
        new_h = int(w / src_aspect)
    resized = src.resize((new_w, new_h), Image.LANCZOS)
    crop_x = (new_w - w) // 2
    crop_y = (new_h - h) // 2
    cropped = resized.crop((crop_x, crop_y, crop_x + w, crop_y + h))
    bg = Image.new("RGB", (w, h), (255, 255, 255))
    bg.paste(cropped, (0, 0))
    return bg


def _pick_grid(n: int) -> tuple[int, int]:
    return {1: (1, 1), 2: (1, 2), 3: (1, 3), 4: (2, 2),
            5: (2, 3), 6: (2, 3), 7: (3, 3), 8: (3, 3), 9: (3, 3)}.get(n, (3, 3))


# ---------------------------------------------------------------------------
# Letter a single panel rectangle

def _letter_panel(draw: ImageDraw.ImageDraw, panel: dict, x: int, y: int, w: int, h: int):
    dialog_font = load_font(FONT_DIALOG, 36)
    caption_font = load_font(FONT_CAPTION, 32)

    # Captions: stack at top
    cy = y + 16
    for cap in panel.get("captions", []):
        text = cap.get("text", "").strip()
        if not text:
            continue
        # Captions span ~70% of panel width, left-aligned
        cap_w = int(w * 0.70)
        box = render_caption_box(draw, text, x + 16, cy, cap_w, caption_font)
        cy = box[3] + 12

    # Dialogue: stack two sides
    left_cursor = cy + 8
    right_cursor = cy + 8
    speakers_seen: list[str] = []
    for d in panel.get("dialogue", []):
        text = d.get("text", "").strip()
        if not text:
            continue
        speaker = d.get("speaker", "")
        if speaker not in speakers_seen:
            speakers_seen.append(speaker)
        # First speaker → left, second → right, alternate after
        side = "left" if speakers_seen.index(speaker) % 2 == 0 else "right"
        max_w = int(w * 0.42)
        cur_y = left_cursor if side == "left" else right_cursor
        bx = x + 24 if side == "left" else x + w - max_w - 24
        # Optional explicit speaker_position from shotlist: {x: 0.0..1.0, y: 0.0..1.0}
        # relative to the panel rect. When absent, render_balloon draws a short stub tail.
        sp = d.get("speaker_position")
        tail = None
        if isinstance(sp, dict) and "x" in sp and "y" in sp:
            tail = (x + int(w * float(sp["x"])), y + int(h * float(sp["y"])))
        bubble = Bubble(text=text, type=d.get("type", "balloon"),
                        speaker=speaker, side=side)
        box = render_balloon(draw, bubble, bx, cur_y, max_w, dialog_font, tail)
        if side == "left":
            left_cursor = box[3] + 14
        else:
            right_cursor = box[3] + 14

    # SFX: bottom strip, left-aligned (each on its own row)
    sfx_y = y + h - 200
    sfx_x = x + 40
    for sfx in panel.get("sfx", []):
        text = sfx.get("text", "").strip()
        if not text:
            continue
        scale = sfx.get("scale", "medium")
        render_sfx(draw, text, sfx_x, sfx_y, scale, FONT_SFX)
        # Move down for next SFX
        sfx_y += {"small": 70, "medium": 110, "large": 170}.get(scale, 110)


# ---------------------------------------------------------------------------
# Project resolution + orchestration

def find_panel_image(project: Path, panel_id: str) -> Path | None:
    """Resolve panel_id to its accepted PNG.

    Lookup order:
      pages/panels/panel-<id>/v*_accepted.png  (most recent)
      pages/panels/panel-<id>/v1.png
      pages/panels/<panel_id>.png              (legacy flat layout)
    """
    panels_dir = project / "pages" / "panels"
    candidates = []
    # Try folder-with-slug convention
    for sub in panels_dir.glob(f"panel-{panel_id}*"):
        if sub.is_dir():
            accepted = sorted(sub.glob("v*_accepted.png"))
            if accepted:
                candidates.append(accepted[-1])
            elif (sub / "v1.png").exists():
                candidates.append(sub / "v1.png")
    # Flat fallback
    flat = panels_dir / f"{panel_id}.png"
    if flat.exists():
        candidates.append(flat)
    return candidates[0] if candidates else None


def resolve_pages_arg(arg: str | None, total: int) -> list[int]:
    if arg is None:
        return list(range(1, total + 1))
    out: set[int] = set()
    for part in arg.split(","):
        part = part.strip()
        if "-" in part:
            lo, hi = part.split("-", 1)
            out.update(range(int(lo), int(hi) + 1))
        else:
            out.add(int(part))
    return sorted(out)


def compose_project(project: Path, pages_filter: str | None, make_pdf: bool, single_page: int | None) -> None:
    shotlist_path = project / "shotlist.json"
    if not shotlist_path.exists():
        sys.exit(f"shotlist.json not found at {shotlist_path}")
    with open(shotlist_path) as f:
        shotlist = json.load(f)
    pages = shotlist.get("pages", [])
    if not pages:
        sys.exit("shotlist.json has no pages[]")

    total = len(pages)
    if single_page is not None:
        target_pages = [single_page]
    else:
        target_pages = resolve_pages_arg(pages_filter, total)

    composed: list[Path] = []
    out_dir = project / "pages" / "composed"
    out_dir.mkdir(parents=True, exist_ok=True)
    index_rows: list[str] = []

    for page in pages:
        n = page["page_number"]
        if n not in target_pages:
            continue
        panels = page["panels"]
        panel_imgs: dict[str, Path] = {}
        missing: list[str] = []
        for p in panels:
            img = find_panel_image(project, p["panel_id"])
            if img is None:
                missing.append(p["panel_id"])
            else:
                panel_imgs[p["panel_id"]] = img
        if missing:
            print(f"[page {n}] SKIP — missing panel images: {', '.join(missing)}", file=sys.stderr)
            continue

        out_path = out_dir / f"page-{n:02d}.png"
        if len(panels) == 1:
            compose_single_image_page(panel_imgs[panels[0]["panel_id"]], panels[0], out_path)
        else:
            compose_multi_panel_page(page, panel_imgs, out_path)
        composed.append(out_path)
        index_rows.append(f"| {n:02d} | {len(panels)} | {page.get('layout', '?')} | ![](page-{n:02d}.png) |")
        print(f"[page {n}] composed → {out_path.relative_to(project)}")

    # Update index
    index_md = out_dir / "_index.md"
    with open(index_md, "w") as f:
        f.write(f"# Composed pages — {shotlist.get('title', shotlist.get('project', 'untitled'))}\n\n")
        f.write("| Page | Panels | Layout | Image |\n|------|--------|--------|-------|\n")
        f.write("\n".join(index_rows) + "\n")

    # PDF
    if make_pdf and composed:
        try:
            import img2pdf  # type: ignore
            pdf_name = shotlist.get("project", project.name) + ".pdf"
            pdf_path = project / "pages" / pdf_name
            with open(pdf_path, "wb") as f:
                f.write(img2pdf.convert([str(p) for p in sorted(composed)]))
            print(f"[pdf] wrote {pdf_path.relative_to(project)}")
        except ImportError:
            print("[pdf] img2pdf not installed — pip install img2pdf", file=sys.stderr)


# ---------------------------------------------------------------------------
# CLI

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", required=True, type=Path, help="Path to project root (contains shotlist.json)")
    ap.add_argument("--pages", help="Page range, e.g. '1-7' or '1,3,5'")
    ap.add_argument("--page", type=int, help="Compose only this page number (overrides --pages)")
    ap.add_argument("--pdf", action="store_true", help="Also write a stitched PDF of all composed pages")
    args = ap.parse_args()
    compose_project(args.project.resolve(), args.pages, args.pdf, args.page)


if __name__ == "__main__":
    main()
