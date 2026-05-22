"""Demo L33 on an existing comic panel.

Applies the calibrated A2 + B2 (baseline) treatment from the SFX
calibration matrix to a real production panel from ultra-gal-origin:
p05-04 (arms beat, tier 2).

Output: demo-l33-side-by-side.png — original (left) vs L33-applied (right),
with the actual L33 prompt fragment printed underneath.
"""
from __future__ import annotations
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Reuse the calibration matrix's overlay functions
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import generate_matrix as gm  # noqa: E402
sys.path.insert(0, str(HERE.parent.parent))  # skills/comic-production/
from rules._registry import RULES  # noqa: E402

PANEL = Path(
    "/Users/mattmenashe/Documents/claude-comic-pipeline/projects/"
    "ultra-gal-origin/pages/panels/p05-04/v1_accepted.png"
)
OUT = HERE / "demo-l33-side-by-side.png"

IMPACT = "/System/Library/Fonts/Supplemental/Impact.ttf"
ARIAL_BLACK = "/System/Library/Fonts/Supplemental/Arial Black.ttf"

PANEL_INFO = {
    "panel_id": "p05-04",
    "transformation_beat": "arms",
    "muscle_size_tier": 2,
}


def apply_l33_overlay(src: Image.Image) -> Image.Image:
    """Apply the calibrated baseline A2 + B2 SFX treatment to a panel.

    The bicep peak for p05-04 sits roughly at the upper-center of the
    frame — override generate_matrix's CENTER to match.
    """
    W, H = src.size
    # Center the radial burst on the upper-center bicep peak
    gm.CENTER = (W // 2, int(H * 0.42))
    # A2: 11 lines, medium density, mixed thicknesses, white
    a2 = gm.draw_action_lines(
        src,
        count=11,
        inner_radius=int(min(W, H) * 0.22),
        outer_extra=80,
        thickness_range=(3, 6),
        color=(240, 240, 240, 200),
        seed=22,
    )
    # B2: medium FLEX, ~15% frame height, behind/beside bicep
    sfx_w, sfx_h = a2.size
    overlay = Image.new("RGBA", (sfx_w, sfx_h), (0, 0, 0, 0))
    font_size = int(sfx_h * 0.15)
    font = ImageFont.truetype(IMPACT, font_size)
    word_layer = Image.new("RGBA", (sfx_w, sfx_h), (0, 0, 0, 0))
    wd = ImageDraw.Draw(word_layer)
    bbox = wd.textbbox((0, 0), "FLEX", font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    # Position: right side of frame, slightly below bicep peak
    pos = (int(W * 0.55), int(H * 0.50) - th // 2)
    # Drop shadow
    wd.text((pos[0] + 4, pos[1] + 4), "FLEX", font=font, fill=(0, 0, 0, 200))
    # Thick black outline
    outline_w = 5
    for ox in range(-outline_w, outline_w + 1):
        for oy in range(-outline_w, outline_w + 1):
            if ox * ox + oy * oy <= outline_w * outline_w:
                wd.text((pos[0] + ox, pos[1] + oy), "FLEX", font=font, fill=(0, 0, 0, 255))
    # Yellow fill
    wd.text(pos, "FLEX", font=font, fill=(255, 230, 60, 240))
    # Slight tilt
    word_layer = word_layer.rotate(-8, resample=Image.BICUBIC, expand=False)
    return Image.alpha_composite(a2, word_layer)


def build_side_by_side(src: Image.Image, applied: Image.Image, prompt_line: str) -> Image.Image:
    PAD = 24
    LABEL_H = 36
    PROMPT_H = 360  # space underneath for the prompt fragment
    W, H = src.size
    sheet_w = W * 2 + PAD * 3
    sheet_h = H + PAD * 3 + LABEL_H + PROMPT_H
    sheet = Image.new("RGB", (sheet_w, sheet_h), (24, 24, 28))
    draw = ImageDraw.Draw(sheet)
    title_font = ImageFont.truetype(ARIAL_BLACK, 22)
    label_font = ImageFont.truetype(ARIAL_BLACK, 18)
    body_font = ImageFont.truetype(IMPACT, 16)

    draw.text((PAD, 12), "L33 DEMO — ultra-gal-origin/p05-04 (arms, tier 2, baseline calibration: A2 lines + B2 FLEX)",
              font=title_font, fill=(245, 245, 250))

    # Original (left)
    sheet.paste(src, (PAD, PAD + LABEL_H))
    draw.rectangle([(PAD, PAD + LABEL_H + H + 4), (PAD + W, PAD + LABEL_H + H + 4 + 28)],
                   fill=(40, 40, 50))
    draw.text((PAD + 8, PAD + LABEL_H + H + 8), "ORIGINAL (pre-L33)",
              font=label_font, fill=(255, 240, 120))

    # Applied (right)
    sheet.paste(applied.convert("RGB"), (PAD * 2 + W, PAD + LABEL_H))
    draw.rectangle([(PAD * 2 + W, PAD + LABEL_H + H + 4),
                    (PAD * 2 + W * 2, PAD + LABEL_H + H + 4 + 28)],
                   fill=(40, 40, 50))
    draw.text((PAD * 2 + W + 8, PAD + LABEL_H + H + 8),
              "WITH L33 APPLIED (PIL stand-in for model)",
              font=label_font, fill=(255, 240, 120))

    # Prompt fragment underneath
    prompt_y = PAD + LABEL_H + H + 4 + 28 + 20
    draw.text((PAD, prompt_y), "Prompt fragment the rendering model would receive:",
              font=label_font, fill=(180, 180, 200))
    # Wrap the prompt text
    import textwrap
    wrapped = textwrap.wrap(prompt_line, width=140)
    for i, line in enumerate(wrapped[:18]):
        draw.text((PAD, prompt_y + 28 + i * 18), line, font=body_font, fill=(220, 220, 230))

    return sheet


def main():
    src = Image.open(PANEL).convert("RGBA")
    print(f"Panel size: {src.size}")

    applied = apply_l33_overlay(src.copy())
    applied.save(HERE / "demo-l33-applied.png")

    # Get the actual L33 prompt fragment for p05-04
    l33 = RULES["L33"]
    ctx = {"_active_slot": "11_render_directive"}
    prompt_line = l33.compose_contribution(PANEL_INFO, ctx, "11_render_directive")
    print("\nL33 prompt fragment:")
    print(prompt_line)

    sheet = build_side_by_side(src, applied, prompt_line)
    sheet.save(OUT)
    print(f"\nSaved {OUT} ({sheet.size})")


if __name__ == "__main__":
    main()
