"""Programmatic SFX calibration matrix.

Generates 13 variants from the source bicep by compositing 2D comic-book
action-lines + SFX text overlays at varying intensities. The matrix
isolates each dimension (action lines, SFX text) so the user can pick a
sweet-spot level for the L-rule.

Output: variants/{A0..A4,B0..B4,C1..C3}.png + contact-sheet.png
"""
from __future__ import annotations
import math
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = Path(__file__).parent
SRC = HERE / "source-bicep.png"
OUT = HERE / "variants"
OUT.mkdir(exist_ok=True)

# Bicep peak — eyeball center for radial action lines.
# Source is 1200x896; the bicep apex sits roughly in the upper-left third.
CENTER = (520, 410)

IMPACT = "/System/Library/Fonts/Supplemental/Impact.ttf"
ARIAL_BLACK = "/System/Library/Fonts/Supplemental/Arial Black.ttf"


def _radial_endpoint(cx: int, cy: int, angle_deg: float, length: int) -> tuple[int, int]:
    rad = math.radians(angle_deg)
    return (int(cx + math.cos(rad) * length), int(cy + math.sin(rad) * length))


def draw_action_lines(
    base: Image.Image,
    *,
    count: int,
    inner_radius: int,
    outer_extra: int,
    thickness_range: tuple[int, int],
    color: tuple[int, int, int, int],
    chromatic: bool = False,
    chaos: bool = False,
    seed: int = 0,
) -> Image.Image:
    """Draw radial action lines on a transparent overlay, paste on base."""
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    rng = random.Random(seed)
    W, H = base.size
    cx, cy = CENTER
    # Max distance from center to frame corner — guarantees lines exit the frame
    max_dist = int(math.hypot(max(cx, W - cx), max(cy, H - cy))) + outer_extra
    for i in range(count):
        if chaos:
            # multiple impact bursts: random center offsets
            ocx = cx + rng.randint(-80, 80)
            ocy = cy + rng.randint(-80, 80)
        else:
            ocx, ocy = cx, cy
        angle = rng.uniform(0, 360) if chaos else (360 * i / count + rng.uniform(-6, 6))
        thickness = rng.randint(*thickness_range)
        inner_off = inner_radius + rng.randint(-20, 20)
        sx, sy = _radial_endpoint(ocx, ocy, angle, max(0, inner_off))
        ex, ey = _radial_endpoint(ocx, ocy, angle, max_dist)
        if chromatic:
            # Slight cyan/magenta fringes for energetic accent
            cyan = (80, 200, 240, color[3])
            magenta = (240, 80, 200, color[3])
            draw.line([(sx - 2, sy), (ex - 2, ey)], fill=cyan, width=max(1, thickness - 1))
            draw.line([(sx + 2, sy), (ex + 2, ey)], fill=magenta, width=max(1, thickness - 1))
        draw.line([(sx, sy), (ex, ey)], fill=color, width=thickness)
    return Image.alpha_composite(base.convert("RGBA"), overlay)


def draw_sfx(
    base: Image.Image,
    *,
    text: str,
    font_path: str,
    size_pct: float,
    pos: str,  # "corner", "behind", "center", "stacked"
    fill: tuple[int, int, int, int],
    outline: tuple[int, int, int, int] | None,
    outline_w: int = 0,
    italic_skew: bool = False,
    rotation: float = 0,
    shadow_offset: tuple[int, int] = (0, 0),
    extra_lines: list[tuple[str, float, tuple[int, int]]] | None = None,
) -> Image.Image:
    """Draw SFX text overlay. extra_lines is for stacked B4 variant."""
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    W, H = base.size

    def render_word(word: str, size_pct_w: float, pos_xy: tuple[int, int], fill_c, outline_c, outline_wd, rot):
        font_size = int(H * size_pct_w)
        font = ImageFont.truetype(font_path, font_size)
        bbox = draw.textbbox((0, 0), word, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        word_layer = Image.new("RGBA", (text_w + outline_wd * 2 + 30, text_h + outline_wd * 2 + 30), (0, 0, 0, 0))
        word_draw = ImageDraw.Draw(word_layer)
        # Drop shadow
        if shadow_offset != (0, 0):
            word_draw.text((outline_wd + 15 + shadow_offset[0], outline_wd + 5 + shadow_offset[1]), word, font=font, fill=(0, 0, 0, 200))
        # Stroke (multi-pass for thicker outline)
        if outline_c and outline_wd:
            for ox in range(-outline_wd, outline_wd + 1):
                for oy in range(-outline_wd, outline_wd + 1):
                    if ox * ox + oy * oy <= outline_wd * outline_wd:
                        word_draw.text((outline_wd + 15 + ox, outline_wd + 5 + oy), word, font=font, fill=outline_c)
        # Main fill
        word_draw.text((outline_wd + 15, outline_wd + 5), word, font=font, fill=fill_c)
        if rot:
            word_layer = word_layer.rotate(rot, resample=Image.BICUBIC, expand=True)
        overlay.paste(word_layer, pos_xy, word_layer)

    if pos == "corner":
        # B1: small lowercase italic in bottom-right corner
        font_size = int(H * size_pct)
        font = ImageFont.truetype(font_path, font_size)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        pos_xy = (W - text_w - 60, H - font_size - 60)
        render_word(text, size_pct, pos_xy, fill, outline, outline_w, rotation)
    elif pos == "behind":
        # B2: medium SFX placed behind/beside the bicep, slightly tilted
        font_size = int(H * size_pct)
        font = ImageFont.truetype(font_path, font_size)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        # Position: right side of bicep, slightly below peak
        pos_xy = (650, 420 - text_h // 2)
        render_word(text, size_pct, pos_xy, fill, outline, outline_w, rotation)
    elif pos == "center":
        # B3: dominating, centered behind bicep
        font_size = int(H * size_pct)
        font = ImageFont.truetype(font_path, font_size)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        pos_xy = ((W - text_w) // 2, (H - text_h) // 2 - 30)
        render_word(text, size_pct, pos_xy, fill, outline, outline_w, rotation)
    elif pos == "stacked":
        # B4: multiple words stacked, dominating
        for (word, sz, xy) in extra_lines or []:
            render_word(word, sz, xy, fill, outline, outline_w, rotation)

    return Image.alpha_composite(base.convert("RGBA"), overlay)


def generate_all():
    src = Image.open(SRC).convert("RGBA")
    print(f"Source: {src.size}")

    # ---- A0: control (no overlay) ----
    src.save(OUT / "A0.png")
    print("A0 saved")

    # ---- A1: subtle action lines (4-6 thin, low contrast grey) ----
    a1 = draw_action_lines(
        src,
        count=5,
        inner_radius=180,
        outer_extra=60,
        thickness_range=(2, 4),
        color=(220, 220, 220, 140),
        seed=11,
    )
    a1.save(OUT / "A1.png")
    print("A1 saved")

    # ---- A2: medium action lines (10-12 mixed) ----
    a2 = draw_action_lines(
        src,
        count=11,
        inner_radius=170,
        outer_extra=80,
        thickness_range=(3, 6),
        color=(240, 240, 240, 200),
        seed=22,
    )
    a2.save(OUT / "A2.png")
    print("A2 saved")

    # ---- A3: heavy (18-25 dense, bold + chromatic accent) ----
    a3 = draw_action_lines(
        src,
        count=22,
        inner_radius=160,
        outer_extra=100,
        thickness_range=(4, 9),
        color=(255, 255, 255, 230),
        chromatic=True,
        seed=33,
    )
    a3.save(OUT / "A3.png")
    print("A3 saved")

    # ---- A4: overdone (30+ chaotic, multi-burst) ----
    a4 = draw_action_lines(
        src,
        count=38,
        inner_radius=140,
        outer_extra=140,
        thickness_range=(3, 10),
        color=(255, 255, 255, 235),
        chromatic=True,
        chaos=True,
        seed=44,
    )
    a4.save(OUT / "A4.png")
    print("A4 saved")

    # ---- B0: control ----
    src.save(OUT / "B0.png")
    print("B0 saved")

    # ---- B1: subtle "*flex*" lowercase italic in corner ----
    b1 = draw_sfx(
        src,
        text="*flex*",
        font_path=IMPACT,
        size_pct=0.045,
        pos="corner",
        fill=(240, 240, 240, 200),
        outline=None,
        italic_skew=True,
        rotation=-5,
    )
    b1.save(OUT / "B1.png")
    print("B1 saved")

    # ---- B2: medium "FLEX" classic comic-burst, ~15% frame height ----
    b2 = draw_sfx(
        src,
        text="FLEX",
        font_path=IMPACT,
        size_pct=0.15,
        pos="behind",
        fill=(255, 230, 60, 240),
        outline=(0, 0, 0, 255),
        outline_w=5,
        rotation=-8,
        shadow_offset=(4, 4),
    )
    b2.save(OUT / "B2.png")
    print("B2 saved")

    # ---- B3: heavy "FLEX" dominating, ~30% frame height, multi-color outlined ----
    b3 = draw_sfx(
        src,
        text="FLEX",
        font_path=IMPACT,
        size_pct=0.32,
        pos="center",
        fill=(255, 220, 30, 245),
        outline=(180, 30, 30, 255),
        outline_w=10,
        rotation=-10,
        shadow_offset=(6, 6),
    )
    b3.save(OUT / "B3.png")
    print("B3 saved")

    # ---- B4: overdone stacked words dominating ----
    b4 = draw_sfx(
        src,
        text="",
        font_path=IMPACT,
        size_pct=0,
        pos="stacked",
        fill=(255, 220, 30, 245),
        outline=(180, 30, 30, 255),
        outline_w=8,
        rotation=-7,
        shadow_offset=(5, 5),
        extra_lines=[
            ("FLEX!", 0.28, (40, 80)),
            ("POMF!", 0.22, (250, 380)),
            ("GRRRR!", 0.20, (600, 620)),
        ],
    )
    b4.save(OUT / "B4.png")
    print("B4 saved")

    # ---- C1: A1 + B1 (subtle both) ----
    c1_base = draw_action_lines(src, count=5, inner_radius=180, outer_extra=60,
                                 thickness_range=(2, 4), color=(220, 220, 220, 140), seed=11)
    c1 = draw_sfx(c1_base, text="*flex*", font_path=IMPACT, size_pct=0.045,
                   pos="corner", fill=(240, 240, 240, 200), outline=None,
                   italic_skew=True, rotation=-5)
    c1.save(OUT / "C1.png")
    print("C1 saved")

    # ---- C2: A2 + B2 (medium both — likely sweet spot) ----
    c2_base = draw_action_lines(src, count=11, inner_radius=170, outer_extra=80,
                                 thickness_range=(3, 6), color=(240, 240, 240, 200), seed=22)
    c2 = draw_sfx(c2_base, text="FLEX", font_path=IMPACT, size_pct=0.15,
                   pos="behind", fill=(255, 230, 60, 240),
                   outline=(0, 0, 0, 255), outline_w=5,
                   rotation=-8, shadow_offset=(4, 4))
    c2.save(OUT / "C2.png")
    print("C2 saved")

    # ---- C3: A3 + B2 (heavy lines, medium SFX) ----
    c3_base = draw_action_lines(src, count=22, inner_radius=160, outer_extra=100,
                                 thickness_range=(4, 9), color=(255, 255, 255, 230),
                                 chromatic=True, seed=33)
    c3 = draw_sfx(c3_base, text="FLEX", font_path=IMPACT, size_pct=0.15,
                   pos="behind", fill=(255, 230, 60, 240),
                   outline=(0, 0, 0, 255), outline_w=5,
                   rotation=-8, shadow_offset=(4, 4))
    c3.save(OUT / "C3.png")
    print("C3 saved")


def build_contact_sheet():
    """4-col grid: A0..A4 (5 cells), B0..B4 (5 cells), C1..C3 (3 cells + 2 spacers).
    Resize each variant to 360x270 thumb, add label band.
    """
    THUMB_W, THUMB_H = 360, 270
    LABEL_H = 40
    GAP = 16
    COLS = 5
    ROWS = 3
    sheet_w = COLS * THUMB_W + (COLS + 1) * GAP
    sheet_h = ROWS * (THUMB_H + LABEL_H) + (ROWS + 1) * GAP + 60
    sheet = Image.new("RGB", (sheet_w, sheet_h), (24, 24, 28))
    draw = ImageDraw.Draw(sheet)
    title_font = ImageFont.truetype(ARIAL_BLACK, 28)
    label_font = ImageFont.truetype(ARIAL_BLACK, 22)
    sub_font = ImageFont.truetype(IMPACT, 18)

    draw.text((GAP, 16), "SFX CALIBRATION MATRIX  |  source: bicep flex  |  13 variants",
              font=title_font, fill=(245, 245, 250))

    rows = [
        # (label, variants, sub-descriptions)
        ("Row A — action lines only", ["A0", "A1", "A2", "A3", "A4"],
         ["off", "subtle (5 lines)", "medium (11 lines)", "heavy (22 + chromatic)", "overdone (38 chaotic)"]),
        ("Row B — SFX text only",     ["B0", "B1", "B2", "B3", "B4"],
         ["off", "subtle *flex*", "medium FLEX 15%", "heavy FLEX 32%", "overdone stacked"]),
        ("Row C — combined sweet-spot candidates", ["C1", "C2", "C3", "", ""],
         ["A1+B1 subtle both", "A2+B2 medium both", "A3+B2 heavy lines / medium SFX", "", ""]),
    ]

    y = 60
    for row_label, variants, subs in rows:
        draw.text((GAP, y), row_label, font=label_font, fill=(255, 255, 200))
        y += 30
        for col, (name, sub) in enumerate(zip(variants, subs)):
            x = GAP + col * (THUMB_W + GAP)
            if not name:
                continue
            im = Image.open(OUT / f"{name}.png").convert("RGB")
            im.thumbnail((THUMB_W, THUMB_H))
            # Center inside the thumb box
            tx = x + (THUMB_W - im.width) // 2
            ty = y + (THUMB_H - im.height) // 2
            sheet.paste(im, (tx, ty))
            # Label band beneath
            band_y = y + THUMB_H + 4
            draw.rectangle([(x, band_y), (x + THUMB_W, band_y + LABEL_H)], fill=(40, 40, 50))
            draw.text((x + 10, band_y + 4), name, font=label_font, fill=(255, 240, 120))
            draw.text((x + 60, band_y + 10), sub, font=sub_font, fill=(220, 220, 230))
        y += THUMB_H + LABEL_H + GAP

    sheet.save(HERE / "contact-sheet.png")
    print(f"Contact sheet saved: {sheet.size}")


if __name__ == "__main__":
    generate_all()
    build_contact_sheet()
