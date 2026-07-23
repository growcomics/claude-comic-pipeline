#!/usr/bin/env python3
"""3DMC cover/banner composer — v1 (compositing-only, zero generation credits).

Reads projects/<project>/references/cover/cover-spec.json:
  {
    "title": "Heather & Mark",
    "kicker": "3D MUSCLE COMICS PRESENTS",       # optional override; default house lockup
    "pre_image":  "panels/006.jpeg",             # non-muscular state (foreground, sharp)
    "post_image": "panels/057.jpeg",             # muscular state (background teaser)
    "accent": "#F5C4B3",                         # title color
    "pre_focus": 0.5,                            # horizontal focus 0..1 for the pre crop
    "post_focus": 0.5
  }
Outputs (same directory as the spec):  cover-3x4.jpg (900x1200), banner-16x9.jpg (1920x1080).
The muscular state reads as a dark, glowing tease behind the everyday self — the owner's
banner formula. Exact text is composited in post; never baked by a model.

Usage: python3 tools/cover-composer/compose_cover.py projects/<project>
"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

def font(size, bold=True):
    for cand in ("/System/Library/Fonts/HelveticaNeue.ttc", "/System/Library/Fonts/Helvetica.ttc"):
        try: return ImageFont.truetype(cand, size, index=1 if bold else 0)
        except Exception: continue
    return ImageFont.load_default()

def cover_crop(im, w, h, focus=0.5, focus_y=0.3, zoom=1.0):
    """Scale-fill and crop to w x h; focus/focus_y 0..1 position the crop window; zoom > 1 crops tighter."""
    r = max(w / im.width, h / im.height) * max(1.0, zoom)
    im2 = im.resize((int(im.width * r + 0.5), int(im.height * r + 0.5)), Image.LANCZOS)
    x = int((im2.width - w) * focus); y = int((im2.height - h) * focus_y)
    return im2.crop((x, y, x + w, y + h))

def tracked(dr, xy, text, f, fill, tracking=0):
    x, y = xy
    for ch in text:
        dr.text((x, y), ch, font=f, fill=fill)
        x += dr.textlength(ch, font=f) + tracking
    return x

def compose(spec_dir):
    spec = json.load(open(os.path.join(spec_dir, "cover-spec.json")))
    root = spec.get("_project_root", os.path.dirname(os.path.dirname(spec_dir.rstrip("/"))))
    pre  = Image.open(os.path.join(root, spec["pre_image"])).convert("RGB")
    post = Image.open(os.path.join(root, spec["post_image"])).convert("RGB")
    accent = spec.get("accent", "#F5C4B3")
    kicker = spec.get("kicker", "3D MUSCLE COMICS PRESENTS")
    title  = spec["title"]

    for W, H, name, banner in ((900, 1200, "cover-3x4.jpg", False), (1920, 1080, "banner-16x9.jpg", True)):
        # background: the muscular tease — dark, slightly blurred, looming
        bg = cover_crop(post, W, H, spec.get("post_focus", 0.5), spec.get("post_focus_y", 0.3), spec.get("post_zoom", 1.0))
        bg = bg.filter(ImageFilter.GaussianBlur(spec.get("post_blur", 4)))
        bg = ImageEnhance.Brightness(bg).enhance(spec.get("post_brightness", 0.55))
        bg = ImageEnhance.Color(bg).enhance(0.85)
        canvas = bg

        # foreground: the everyday self, sharp, framed
        if banner:
            fw, fh = int(W * 0.30), int(H * 0.86)
            fx, fy = int(W * 0.62), int(H * 0.07)
        else:
            fw, fh = int(W * 0.62), int(H * 0.60)
            fx, fy = int(W * 0.19), int(H * 0.06)
        fg = cover_crop(pre, fw, fh, spec.get("pre_focus", 0.5), spec.get("pre_focus_y", 0.3), spec.get("pre_zoom", 1.0))
        # soft glow edge behind the frame
        glow = Image.new("RGB", (fw + 28, fh + 28), accent)
        glow = glow.filter(ImageFilter.GaussianBlur(18))
        canvas.paste(glow, (fx - 14, fy - 14))
        frame = Image.new("RGB", (fw + 8, fh + 8), "#0B0C10")
        canvas.paste(frame, (fx - 4, fy - 4))
        canvas.paste(fg, (fx, fy))

        # bottom scrim for the lockup
        scrim = Image.new("L", (W, H), 0)
        sd = ImageDraw.Draw(scrim)
        top = int(H * (0.68 if not banner else 0.62))
        for i in range(top, H):
            sd.line([(0, i), (W, i)], fill=int(235 * (i - top) / max(1, H - top)))
        canvas = Image.composite(Image.new("RGB", (W, H), "#07080A"), canvas, scrim)

        dr = ImageDraw.Draw(canvas)
        kx = int(W * 0.06); base = int(H * (0.80 if not banner else 0.72))
        kf = font(int(H * 0.028)); tf = font(int(H * (0.075 if not banner else 0.10)))
        tracked(dr, (kx, base - int(H * 0.045)), kicker, kf, "#C7CAD4", tracking=int(H * 0.006))
        # title with soft shadow
        dr.text((kx + 3, base + 3), title.upper(), font=tf, fill="#000000")
        dr.text((kx, base), title.upper(), font=tf, fill=accent)
        dr.line([(kx, base + int(H * 0.10)), (kx + int(W * 0.3), base + int(H * 0.10))], fill=accent, width=3)

        out = os.path.join(spec_dir, name)
        canvas.save(out, quality=88)
        print("wrote", out, canvas.size)

if __name__ == "__main__":
    if len(sys.argv) != 2: sys.exit("usage: compose_cover.py projects/<project>")
    d = os.path.join(sys.argv[1], "references", "cover")
    compose(d)
