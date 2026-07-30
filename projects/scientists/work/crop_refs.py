#!/usr/bin/env python3
"""Crop reference panels from source pages per spotter picks.
Boxes are (x0,y0,x1,y1) as fractions of page size. Verified via contact sheet."""
import os
from PIL import Image

SRC = os.path.join(os.path.dirname(__file__), "..", "source")
OUT = os.path.join(os.path.dirname(__file__), "..", "references", "harvest")
os.makedirs(OUT, exist_ok=True)

CROPS = [
    # id, page, (x0,y0,x1,y1)
    ("rochelle-face-sfw-p22",    22, (0.00, 0.42, 1.00, 0.75)),
    ("rochelle-face-vials-p18",  18, (0.45, 0.30, 1.00, 0.68)),
    ("rochelle-flex-p16",        16, (0.00, 0.00, 0.58, 0.36)),
    ("rochelle-drink-p14",       14, (0.00, 0.62, 1.00, 1.00)),
    ("rochelle-pour-p34",        34, (0.00, 0.00, 1.00, 0.32)),
    ("rochelle-arms-p39",        39, (0.00, 0.33, 0.52, 0.70)),
    ("rochelle-titan-p44",       44, (0.00, 0.00, 1.00, 1.00)),
    ("rochelle-titan-p42",       42, (0.00, 0.58, 1.00, 1.00)),
    ("jill-baseline-p02",         2, (0.42, 0.00, 1.00, 0.36)),
    ("jill-face-p07",             7, (0.45, 0.00, 1.00, 0.34)),
    ("jill-grown-p09",            9, (0.00, 0.58, 1.00, 1.00)),
    ("jill-super-p33",           33, (0.00, 0.30, 0.55, 0.72)),
    ("jill-super-p40",           40, (0.00, 0.60, 1.00, 1.00)),
    ("jim-face-p01",              1, (0.48, 0.00, 1.00, 0.32)),
    ("jim-standing-p26",         26, (0.28, 0.00, 0.75, 0.40)),
    ("jim-grown-p12",            12, (0.00, 0.34, 1.00, 0.66)),
    ("donny-face-p22",           22, (0.00, 0.72, 1.00, 1.00)),
    ("donny-grown-p23",          23, (0.00, 0.58, 1.00, 1.00)),
    ("dan-baseline-p19",         19, (0.00, 0.00, 1.00, 0.30)),
    ("dan-grown-p20",            20, (0.00, 0.62, 1.00, 1.00)),
    ("assistant-face-p16",       16, (0.55, 0.00, 1.00, 0.30)),
    ("assistant-body-p17",       17, (0.00, 0.30, 0.52, 0.68)),
    ("blonde-entry-p25",         25, (0.00, 0.00, 0.55, 0.36)),
    ("blonde-face-p25",          25, (0.45, 0.58, 1.00, 1.00)),
    ("cheer-field-p34",          34, (0.00, 0.00, 1.00, 0.30)),
    ("cheer-buns-p34",           34, (0.00, 0.58, 0.55, 1.00)),
    ("cheer-lineup-p36",         36, (0.00, 0.28, 1.00, 0.62)),
    ("cheer-ponytail-p37",       37, (0.00, 0.00, 0.55, 0.28)),
    ("env-lab-p02",               2, (0.00, 0.58, 1.00, 1.00)),
    ("env-kitchen-p01",           1, (0.00, 0.30, 1.00, 0.62)),
    ("env-city-p43",             43, (0.00, 0.45, 1.00, 0.85)),
]

def main():
    for cid, page, (x0, y0, x1, y1) in CROPS:
        img = Image.open(os.path.join(SRC, f"page-{page:02d}.jpg"))
        w, h = img.size
        crop = img.crop((int(x0*w), int(y0*h), int(x1*w), int(y1*h)))
        crop.save(os.path.join(OUT, f"{cid}.jpg"), quality=92)
        print(f"{cid}: {crop.size}")

    # contact sheet: thumbnails in a grid with labels
    from PIL import ImageDraw
    files = [f"{c[0]}.jpg" for c in CROPS]
    cols, cell = 6, 360
    rows = (len(files) + cols - 1) // cols
    sheet = Image.new("RGB", (cols*cell, rows*(cell+24)), "white")
    d = ImageDraw.Draw(sheet)
    for i, f in enumerate(files):
        im = Image.open(os.path.join(OUT, f))
        im.thumbnail((cell-8, cell-8))
        x, y = (i % cols)*cell, (i // cols)*(cell+24)
        sheet.paste(im, (x+4, y+4))
        d.text((x+6, y+cell+2), f[:-4], fill="black")
    sheet.save(os.path.join(OUT, "..", "..", "work", "harvest-contact-sheet.png"))
    print("contact sheet written")

if __name__ == "__main__":
    main()
