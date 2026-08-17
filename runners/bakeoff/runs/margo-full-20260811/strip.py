#!/usr/bin/env python3
"""Story-order contact strip(s) of the banked winners.

  python3 strip.py <outdir> [--from BEAT] [--to BEAT] [--per 24] [--tw 260]

Builds sheets from DISK (variants/<beat>/<winner>-*.png), labelled with the beat id,
so bookkeeping races cannot corrupt the deliverable.
"""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw

RUN = Path(__file__).resolve().parent
S = json.loads((RUN / "../../margo-full-beats.json").read_text())
ORDER = [b["id"] for b in S["beats"]]
st = json.loads((RUN / "state.json").read_text())


def winners(a=None, b=None):
    lo = ORDER.index(a) if a else 0
    hi = ORDER.index(b) + 1 if b else len(ORDER)
    out = []
    for bid in ORDER[lo:hi]:
        w = st["beats"].get(bid, {}).get("winner")
        if not w:
            continue
        g = sorted((RUN / "variants" / bid).glob(f"{w['variant']}-*.png"))
        if g:
            out.append((bid, w["variant"], g[0]))
    return out


def build(rows, outdir, per, tw):
    outdir = Path(outdir); outdir.mkdir(parents=True, exist_ok=True)
    paths = []
    for n, i in enumerate(range(0, len(rows), per), 1):
        chunk = rows[i:i + per]
        thumbs = []
        for bid, v, f in chunk:
            im = Image.open(f).convert("RGB"); im.thumbnail((tw, tw * 2))
            thumbs.append((f"{bid} {v}", im))
        cols = 6
        rws = (len(thumbs) + cols - 1) // cols
        ch = max(t.size[1] for _, t in thumbs) + 20
        canvas = Image.new("RGB", (cols * (tw + 8) + 8, rws * (ch + 8) + 8), (18, 18, 18))
        dr = ImageDraw.Draw(canvas)
        for k, (lab, t) in enumerate(thumbs):
            x = 8 + (k % cols) * (tw + 8); y = 8 + (k // cols) * (ch + 8)
            canvas.paste(t, (x, y + 18))
            dr.text((x + 2, y + 3), lab, fill=(255, 220, 80))
        p = outdir / f"margo-full-final-strip-{n}.jpg"
        canvas.save(p, quality=86)
        paths.append(str(p)); print(p)
    return paths


if __name__ == "__main__":
    a = sys.argv[1:]
    outdir = a[0]
    def opt(k, d=None):
        return a[a.index(k) + 1] if k in a else d
    rows = winners(opt("--from"), opt("--to"))
    print(f"{len(rows)} winners on disk")
    build(rows, outdir, int(opt("--per", 24)), int(opt("--tw", 260)))
