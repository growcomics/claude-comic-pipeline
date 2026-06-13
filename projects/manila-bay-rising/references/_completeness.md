# manila-bay-rising — reference completeness

Reference-gathering pass: 2026-06-12 → 2026-06-13. Mode: manifest-driven (references_required.json).
Backend for generation half: **Flow** (Nano Banana) — pending Google sign-in on the driving Chrome.

## Locations — internet refs gathered (36 images)

| location | imgs | status | notes |
|---|---|---|---|
| manila-bay-sunset | 5 | ✅ | skyline reflection, dusk marina, clean Commons sunset, burning sky, silhouette |
| makati-skyline | 5 | ✅ | wide night, blue-hour+Greenbelt, close CBD, street-level, aerial |
| edsa | 4 | ✅ | tall gridlock+MRT, sea-of-cars, motorcycle gridlock, jeepney street |
| entertainment-city | 4 | ✅ | Solaire dusk/night ×3 + City of Dreams facade |
| manila-bay-dolomite-beach | 4 | ✅ | aerial, ground-level+skyline, sand texture, placement+barriers |
| manila-bay-outfall | 4 | ✅ | culvert mouths (key), breakwater pipe, estero canal, cordoned shore |
| up-manila-ermita | 3 | ✅ | building+sculpture (official), gate+street, gate seal |
| bayfront-hotel | 3 | ✅ | bay-view window sunset, bedroom, suite living area |
| poblacion-night | 2 | ⚠️ supplement | neon facade + neon street; most results IG/TripAdvisor (blocked). Top up at gen. |
| up-manila-lab | 2 | ⚠️ generic | generic research-lab interiors (no real UPM lab photos); fume hood present |

## Props
| prop | status | notes |
|---|---|---|
| bawal-lumangoy-sign | 2 style refs | BABALA-format typography refs; **generate** final `_source.png` per shotlist spec |
| compound-vial | not gathered (optional) | amber serum vial — **generate** directly; trivial object, no real ref needed |

## NEXT — generation half (needs Flow sign-in)
1. **DAZ-convert** each location's best internet ref → `_source.jpg` (DAZ3D establishing render) per environment-references.md. Reverse views for the 4 hero locations (up-manila-lab, manila-bay-outfall, manila-bay-dolomite-beach, bayfront-hotel).
2. **Generate props**: bawal-lumangoy-sign `_source.png` (using BABALA style refs), compound-vial `_source.png`.
3. **Character refs** (not yet started — needs Flow + tier manifest): hae-won, cel, dr-santos face-cards + body tiers 1–3 + views. Optional: gather real-world seed photos first (Korean tourist type / morena Filipina type / Filipina scientist type) to anchor identity.
4. Re-run `rules_audit.py check_reference_completeness()` (if present) — it hard-fails on any missing manifest path until generation fills `_source.*` + character refs.

## Provenance & QA
Every banked image has a `_provenance.md` (source, capture date, QA verdict) and each location a `_contact-sheet.md`. All full-res click-through/embedded sources — no Google thumbnails. Watermarked images are flagged (use for comp/lighting/typography, not final art).
