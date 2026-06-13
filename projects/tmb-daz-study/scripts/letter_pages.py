#!/usr/bin/env python3
"""letter_pages.py — lettering-patch for clean (unlettered) photoreal panels.

The Higgsfield panels for this project were generated CLEAN (text forbidden in
the prompt) because the build-comic orchestrator's "no baked lettering" rule was
followed. page-composer (post-2026-05-25 / L19) no longer letters. So this is the
separate "lettering-patch" the page-composer SKILL upgrade note anticipates:
it overlays the shotlist's dialogue[] / captions[] / sfx[] onto each clean panel
as flat 2D comic-book graphics composited on the photoreal CGI scene.

Reads shotlist.json + pages/panels-hf/<panel_id>.png -> pages/lettered/<panel_id>.png.

Usage:
  letter_pages.py --project . [--page 43]          # one page
  letter_pages.py --project .                       # all pages
"""
from __future__ import annotations
import argparse, json, math, os, textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# --- font discovery ---------------------------------------------------------
def _find_font(cands):
    for p in cands:
        if os.path.exists(p):
            return p
    return None

DIALOG_FONT = _find_font([
    "/System/Library/Fonts/Supplemental/Comic Sans MS Bold.ttf",
    "/System/Library/Fonts/Supplemental/Comic Sans MS.ttf",
    "/Library/Fonts/Comic Sans MS.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
])
SFX_FONT = _find_font([
    "/System/Library/Fonts/Supplemental/Impact.ttf",
    "/Library/Fonts/Impact.ttf",
    "/System/Library/Fonts/Supplemental/Arial Black.ttf",
    DIALOG_FONT or "",
])

def font(path, size):
    try: return ImageFont.truetype(path, size)
    except Exception: return ImageFont.load_default()

# --- text helpers -----------------------------------------------------------
def wrap(draw, text, fnt, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=fnt) <= max_w or not cur:
            cur = t
        else:
            lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

def text_block_size(draw, lines, fnt, lh):
    w = max((draw.textlength(l, font=fnt) for l in lines), default=0)
    return w, lh * len(lines)

# --- bubble drawing ---------------------------------------------------------
def draw_balloon(img, draw, text, center, max_w, kind, tail_to, scale):
    fs = max(20, int(34 * scale))
    fnt = font(DIALOG_FONT, fs); lh = int(fs * 1.18)
    lines = wrap(draw, text.upper() if kind == "shout" else text, fnt, max_w)
    tw, th = text_block_size(draw, lines, fnt, lh)
    padx, pady = int(fs * 0.9), int(fs * 0.7)
    bw, bh = tw + 2 * padx, th + 2 * pady
    cx, cy = center
    x0, y0 = int(cx - bw / 2), int(cy - bh / 2)
    x1, y1 = x0 + bw, y0 + bh
    # tail
    if tail_to:
        tx, ty = tail_to
        bxc, byc = (x0 + x1) / 2, y1
        base = max(14, int(fs * 0.5))
        draw.polygon([(bxc - base, byc - 4), (bxc + base, byc - 4), (tx, ty)],
                     fill="white", outline="black")
    out = max(3, int(fs * 0.12))
    if kind == "thought":
        draw.ellipse([x0, y0, x1, y1], fill="white", outline="black", width=out)
    elif kind == "shout":
        # jagged star-ish burst
        pts = []
        n = 20
        for i in range(n):
            a = (i / n) * 2 * math.pi
            r = (bw / 2 if i % 2 == 0 else bw / 2 * 0.82)
            ry = (bh / 2 if i % 2 == 0 else bh / 2 * 0.82)
            pts.append((cx + r * math.cos(a), cy + ry * math.sin(a)))
        draw.polygon(pts, fill="white", outline="black")
    else:
        draw.rounded_rectangle([x0, y0, x1, y1], radius=int(bh * 0.45),
                               fill="white", outline="black", width=out)
    # text
    ty = y0 + pady
    for l in lines:
        lw = draw.textlength(l, font=fnt)
        draw.text((cx - lw / 2, ty), l, font=fnt, fill="black")
        ty += lh
    return (x0, y0, x1, y1)

def draw_caption(img, draw, text, corner, scale, W, H):
    fs = max(18, int(28 * scale)); fnt = font(DIALOG_FONT, fs); lh = int(fs * 1.15)
    margin = int(0.03 * W); max_w = int(0.46 * W)
    lines = wrap(draw, text, fnt, max_w)
    tw, th = text_block_size(draw, lines, fnt, lh)
    padx, pady = int(fs * 0.6), int(fs * 0.45)
    bw, bh = tw + 2 * padx, th + 2 * pady
    x0 = margin if corner[0] == "l" else W - margin - bw
    y0 = margin if corner[1] == "t" else H - margin - bh
    draw.rectangle([x0, y0, x0 + bw, y0 + bh], fill=(247, 235, 178), outline="black", width=3)
    ty = y0 + pady
    for l in lines:
        draw.text((x0 + padx, ty), l, font=fnt, fill=(30, 20, 0)); ty += lh

def draw_sfx(img, draw, text, pos, scale, W):
    fs = max(40, int(96 * scale)); fnt = font(SFX_FONT, fs)
    t = text.upper()
    x, y = pos
    ow = max(4, int(fs * 0.08))
    for dx in range(-ow, ow + 1, 2):
        for dy in range(-ow, ow + 1, 2):
            draw.text((x + dx, y + dy), t, font=fnt, fill="black")
    draw.text((x, y), t, font=fnt, fill=(255, 210, 40))

# --- per-page layout --------------------------------------------------------
def letter_page(panel_path, page, out_path):
    img = Image.open(panel_path).convert("RGB")
    W, H = img.size
    draw = ImageDraw.Draw(img)
    scale = W / 1100.0
    pan = page["panels"][0]
    dlg = [d for d in (pan.get("dialogue") or []) if d.get("text")]
    caps = pan.get("captions") or []
    sfx = pan.get("sfx") or []

    # captions -> alternate top corners
    for i, c in enumerate(caps):
        draw_caption(img, draw, c, ("l", "t") if i % 2 == 0 else ("r", "t"), scale, W, H)

    # dialogue balloons -> distribute across the top band, tails toward speaker side
    n = len(dlg)
    max_w = int(0.40 * W)
    for i, d in enumerate(dlg):
        kind = d.get("type", "balloon")
        kind = "shout" if kind == "shout" else "thought" if kind in ("thought", "whisper") else "balloon"
        # horizontal slot
        if n == 1: fx = 0.5
        else: fx = 0.26 + (0.48) * (i / max(1, n - 1))
        cx = int(fx * W)
        cy = int((0.13 + 0.12 * (i % 2)) * H)
        # tail toward the lower third on the speaker's side
        tail = (int(fx * W), int(0.42 * H))
        draw_balloon(img, draw, d["text"], (cx, cy), max_w, kind, tail, scale)

    # sfx -> place along right/lower edge, staggered
    for i, s in enumerate(sfx):
        t = s.get("text") if isinstance(s, dict) else str(s)
        if not t: continue
        x = int((0.46 + 0.10 * (i % 2)) * W)
        y = int((0.55 + 0.14 * i) * H)
        draw_sfx(img, draw, t, (x, y), scale, W)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    return len(dlg), len(caps), len(sfx)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=".")
    ap.add_argument("--page", type=int, default=None)
    args = ap.parse_args()
    proj = Path(args.project).resolve()
    sl = json.load(open(proj / "shotlist.json"))
    out_dir = proj / "pages" / "lettered"
    done = 0
    for pg in sl["pages"]:
        if args.page and pg["page_number"] != args.page: continue
        pid = pg["panels"][0]["panel_id"]
        panel = proj / "pages" / "panels" / f"{pid}.png"
        if not panel.exists():
            print(f"skip {pid}: no panel"); continue
        d, c, s = letter_page(panel, pg, out_dir / f"{pid}.png")
        print(f"lettered {pid}: {d} balloons, {c} caps, {s} sfx")
        done += 1
    print(f"== {done} pages lettered -> {out_dir} ==")
    print(f"fonts: dialog={DIALOG_FONT}  sfx={SFX_FONT}")

if __name__ == "__main__":
    main()
