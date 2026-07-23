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

def font(size, weight="bold", condensed=False):
    cands = (["/System/Library/Fonts/Avenir Next Condensed.ttc"] if condensed else ["/System/Library/Fonts/Avenir Next.ttc"])
    cands += ["/System/Library/Fonts/HelveticaNeue.ttc", "/System/Library/Fonts/Helvetica.ttc"]
    # Avenir Next (Condensed) ttc indices: try to find Bold/Heavy face by probing names
    for cand in cands:
        for idx in ( (8,9,10,4,1) if weight=="heavy" else (1,2,8,4,0) ):
            try:
                f = ImageFont.truetype(cand, size, index=idx)
                nm = " ".join(f.getname()).lower()
                if weight == "heavy" and ("heavy" in nm or "bold" in nm): return f
                if weight == "bold" and ("bold" in nm or "demi" in nm or "medium" in nm): return f
            except Exception:
                continue
    try: return ImageFont.truetype(cands[-1], size)
    except Exception: return ImageFont.load_default()

def inset(im, box):
    """box = [top,right,bottom,left] fractions trimmed off the source before any cropping."""
    if not box: return im
    t, r, b, l = box
    return im.crop((int(im.width * l), int(im.height * t),
                    im.width - int(im.width * r), im.height - int(im.height * b)))

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

def auto_accent(im):
    """Bright, saturated representative color from the tease image."""
    small = im.resize((64, 64))
    best, score = (240, 184, 122), -1
    for r, g, b in small.getdata():
        mx, mn = max(r, g, b), min(r, g, b)
        s = (mx - mn) / mx if mx else 0
        v = mx / 255
        sc = s * v
        if sc > score and v > 0.45:
            score, best = sc, (r, g, b)
    # lift toward pastel so the title stays readable on dark scrim
    return tuple(min(255, int(c * 0.55 + 115)) for c in best)

def compose(spec_dir, suffix="", extra=None):
    spec = json.load(open(os.path.join(spec_dir, "cover-spec.json")))
    if extra: spec.update(extra)
    root = spec.get("_project_root", os.path.dirname(os.path.dirname(spec_dir.rstrip("/"))))
    pre  = inset(Image.open(os.path.join(root, spec["pre_image"])).convert("RGB"), spec.get("pre_inset"))
    post = inset(Image.open(os.path.join(root, spec["post_image"])).convert("RGB"), spec.get("post_inset"))
    if spec.get("formula_note"): print("NOTE:", spec["formula_note"])
    accent = spec.get("accent") or auto_accent(post)
    if isinstance(accent, list): accent = tuple(accent)
    kicker = spec.get("kicker", "3D MUSCLE COMICS PRESENTS")
    title  = spec["title"]

    for W, H, name, banner in ((900, 1200, "cover-3x4.jpg", False), (1920, 1080, "banner-16x9.jpg", True)):
        o = dict(spec)
        o.update(spec.get("banner_overrides" if banner else "cover_overrides", {}) or {})
        if o.get("layout") == "split":
            o.update(spec.get("split_overrides", {}) or {})
            o.update((spec.get("split_overrides", {}) or {}).get("banner" if banner else "cover", {}) or {})
        spec_r = o
        # background: the muscular tease — dark, slightly blurred, looming
        bg = cover_crop(post, W, H, spec_r.get("post_focus", 0.5), spec_r.get("post_focus_y", 0.3), spec_r.get("post_zoom", 1.0))
        bg = bg.filter(ImageFilter.GaussianBlur(spec_r.get("post_blur", 4)))
        bg = ImageEnhance.Brightness(bg).enhance(spec_r.get("post_brightness", 0.55))
        bg = ImageEnhance.Color(bg).enhance(0.85)
        topdim = spec_r.get("post_topdim", 0.25)     # darken top band where source captions/SFX live
        if topdim > 0:
            m = Image.new("L", (W, H), 0); md = ImageDraw.Draw(m)
            band = int(H * topdim)
            for i in range(band):
                md.line([(0, i), (W, i)], fill=int(200 * (1 - i / band)))
            bg = Image.composite(Image.new("RGB", (W, H), "#0A0B0E"), bg, m)
        if banner:
            ls = spec_r.get("left_scrim", 0.3)
            if ls > 0:
                m2 = Image.new("L", (W, H), 0); m2d = ImageDraw.Draw(m2)
                zone = int(W * 0.48)
                for x in range(zone):
                    m2d.line([(x, 0), (x, H)], fill=int(255 * ls * (1 - x / zone)))
                bg = Image.composite(Image.new("RGB", (W, H), "#07080A"), bg, m2)
        canvas = bg

        layout = spec_r.get("layout", "framed")
        if layout == "split":
            # full-bleed: pre occupies one side, blended into the tease with a soft diagonal gradient
            side = spec_r.get("split_side", "right")
            pw = int(W * spec_r.get("split_width", 0.52))
            fg_full = cover_crop(pre, pw, H, spec_r.get("pre_focus", 0.5), spec_r.get("pre_focus_y", 0.25), spec_r.get("pre_zoom", 1.0))
            mask = Image.new("L", (pw, H), 0); md = ImageDraw.Draw(mask)
            feather = int(pw * 0.35)
            for x in range(pw):
                if side == "right":
                    a = 255 if x > feather else int(255 * x / max(1, feather))
                else:
                    a = 255 if x < pw - feather else int(255 * (pw - x) / max(1, feather))
                md.line([(x, 0), (x, H)], fill=a)
            px = W - pw if side == "right" else 0
            canvas.paste(fg_full, (px, 0), mask)
        # foreground: the everyday self, sharp, framed
        if layout == "framed" and banner:
            fw, fh = int(W * 0.30), int(H * 0.86)
            fx, fy = int(W * 0.62), int(H * 0.07)
        elif layout == "framed":
            fw, fh = int(W * 0.62), int(H * 0.60)
            fx, fy = int(W * 0.19), int(H * 0.06)
        if layout == "framed":
            fg = cover_crop(pre, fw, fh, spec_r.get("pre_focus", 0.5), spec_r.get("pre_focus_y", 0.3), spec_r.get("pre_zoom", 1.0))
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
        kf = font(int(H * 0.026), "bold")
        tsize = int(H * (0.075 if not banner else 0.105))
        tf = font(tsize, "heavy", condensed=True)
        while dr.textlength(title.upper(), font=tf) > W * 0.88 and tsize > int(H * 0.04):
            tsize = int(tsize * 0.92); tf = font(tsize, "heavy", condensed=True)
        tracked(dr, (kx, base - int(H * 0.045)), kicker, kf, "#C7CAD4", tracking=int(H * 0.006))
        # title with soft shadow
        dr.text((kx + 3, base + 3), title.upper(), font=tf, fill="#000000")
        dr.text((kx, base), title.upper(), font=tf, fill=accent)
        dr.line([(kx, base + int(H * 0.10)), (kx + int(W * 0.3), base + int(H * 0.10))], fill=accent, width=3)

        out = os.path.join(spec_dir, name.replace(".jpg", suffix + ".jpg"))
        canvas.save(out, quality=88)
        print("wrote", out, canvas.size)

if __name__ == "__main__":
    if len(sys.argv) < 2: sys.exit("usage: compose_cover.py projects/<project> [--split]")
    d = os.path.join(sys.argv[1], "references", "cover")
    if len(sys.argv) > 2 and sys.argv[2] == "--split":
        compose(d, suffix="-split", extra={"layout": "split"})
    else:
        compose(d)
