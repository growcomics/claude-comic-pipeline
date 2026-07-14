# Goth-loft env reference — DAZ3D look provenance

Per `environment-references.md` "DAZ3D scene reference" trick: we study the canonical DAZ3D
gothic interior look, then build a NEW original loft in Flow off that look (NOT a copy).

## What "DAZ3D Iray gothic interior" looks like (research notes)
Source products studied (visual reference only — not reproduced):
- DAZ3D "FG Gothic Apartment" — dark/dramatic, ornate furniture, stained glass, dark palette,
  optimized for Iray; 434 PBR maps (bump/normal/roughness/transparency) up to 4096px.
- DAZ3D "Gothic Bedroom", "Gothic Room for Daz Studio" (powerage) — similar mood.

### Rendered-look fingerprint to reproduce in Flow
- Iray path-traced **soft global illumination**, gentle ambient occlusion in corners.
- **Photoreal PBR materials**: velvet with real sheen, aged wood grain, candle wax translucency,
  subtle roughness variation — never flat/matte cartoon surfaces.
- **Warm candle key light + cool rim** (we add a violet rim for Luna's magic).
- Gentle **bloom** on candle flames, slight **depth-of-field** falloff.
- Staging is **clean and uncluttered** (a few hero props, not a hoarder room) — characteristic
  of marketing renders. This is our "simple background" requirement.

## Our ORIGINAL loft (built in Flow, not from any product)
Top-floor goth loft: plum/charcoal walls, burgundy velvet tufted couch, Persian rug, tall
arched window w/ sheer black curtains + city dusk, dozens of dripping candles, dead roses,
occult bookshelf, pentagram tapestry, fairy lights, EXPOSED WOODEN CEILING BEAMS (the height
gag marker). Keep it simple/uncluttered per the marketing-render aesthetic above.

Sources:
- https://www.daz3d.com/gothic-bedroom
- https://delorean.daz3d.com/fg-gothic-apartment
- https://render-state.to/3d/gothic-room-for-daz-studio/
