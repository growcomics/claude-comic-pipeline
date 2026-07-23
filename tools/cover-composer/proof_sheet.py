#!/usr/bin/env python3
"""Combine every projects/*/references/cover/{cover-3x4,banner-16x9}.jpg into one review sheet."""
import glob, os, sys
from PIL import Image, ImageDraw
outs=[]
for d in sorted(glob.glob('projects/*/references/cover')):
    pj=d.split('/')[1]
    for n in ('cover-3x4.jpg','banner-16x9.jpg'):
        p=os.path.join(d,n)
        if os.path.exists(p): outs.append((pj,n,p))
COLW=640
rows=[]
H=30
for pj,n,p in outs:
    im=Image.open(p); r=COLW/im.width
    rows.append((pj,n,im.resize((COLW,int(im.height*r))),))
W=COLW*2+30
col_h=[30,30]
for i,(pj,n,im) in enumerate(rows):
    col_h[i%2]+=im.height+34
sheet=Image.new('RGB',(W,max(col_h)),(12,13,17)); dr=ImageDraw.Draw(sheet)
ys=[30,30]
for i,(pj,n,im) in enumerate(rows):
    c=i%2; x=10+c*(COLW+10)
    dr.text((x,ys[c]-16),f'{pj} / {n}',fill=(255,255,255))
    sheet.paste(im,(x,ys[c])); ys[c]+=im.height+34
sheet.save(sys.argv[1] if len(sys.argv)>1 else '/tmp/cover-proof.jpg',quality=80)
print('proof sheet:', sys.argv[1] if len(sys.argv)>1 else '/tmp/cover-proof.jpg')
