# Las Vegas — location-scout pack

City scout pack of 8 photoreal CGI background references for Las Vegas. Built `2026-06-07` via the `location-scout` skill. Source captures from Google Maps via Chrome MCP; CGI conversion via Google Flow Nano Banana 2.

Drop the `cgi/<id>-<slug>.png` files into a comic project's panel prompts as the env ref. The pack covers a spectrum of Vegas-distinctive locations so any project set in Vegas can pull from this once-built scout instead of generating per-project.

## Contents

| ID | Type | Where | What |
|---|---|---|---|
| `street-01-fremont-street` | street | Downtown — Fremont East District | Iconic neon arch on Fremont Street at night |
| `street-02-bellagio-strip` | street | Las Vegas Strip — Bellagio | Bellagio hotel + lit fountains at evening |
| `street-03-montelago-residential` | street | Lake Las Vegas — MonteLago Village | Aerial view of Mediterranean-style resort village |
| `restaurant-01-peppermill-diner` | restaurant | Strip — Peppermill | Iconic mid-century diner exterior at dusk |
| `restaurant-02-eiffel-tower-restaurant` | restaurant | Strip — Paris Las Vegas | Open commercial kitchen interior, white tile / stainless steel |
| `restaurant-03-heart-attack-grill` | restaurant | Downtown Fremont — Heart Attack Grill | Corner storefront with neon signage at night |
| `landmark-01-welcome-to-las-vegas-sign` | landmark | S. Las Vegas Blvd | The Welcome to Fabulous Las Vegas Nevada sign at dusk |
| `specific-01-container-park-alley` | specific | Downtown Fremont East — Container Park | Shipping-container retail courtyard, midday |

## Folder layout

```
references/locations/las-vegas/
├── README.md            # this file
├── _targets.json        # planning + provenance artifact
├── meta/
│   └── locations.json   # canonical consumer manifest (machine-readable)
├── source/              # 8 raw Google Maps captures (JPG)
└── cgi/                 # 8 photoreal CGI conversions (PNG)
```

## How to use the pack

### As env refs in comic panels

Attach the `cgi/<id>-<slug>.png` matching a panel's location as the env reference image at generation time. The CGI ref carries:

- Real architecture from the actual Vegas location (no model invention)
- Photoreal DAZ3D / Iray render style matching the comic pipeline's house style
- No people in frame (CGI conversion prompt suppresses them)
- 16:9 aspect (4:3 for the interior restaurant ref; 3:4 for the Fremont neon arch which was rendered portrait)

This preempts L23's "verbal env anchor" fallback for any panel where one of these locations applies. Attaching the CGI ref is more specific than any 5-element verbal description.

### As lookup by tags

`meta/locations.json` carries `type` + `tags` per entry. A `reference-gathering` walker can resolve a shotlist's location intent ("downtown street with neon") to the matching pack entry by tag overlap. See `skills/reference-gathering/SKILL.md` "Location packs from location-scout" section.

## Generation details

- **Source captures**: Google Maps photos panel, hero-image URL extracted in-page, downloaded full-res (1280–1920 px wide).
- **CGI converter**: Google Flow at `labs.google/fx/tools/flow`, model **Nano Banana 2**, aspect `16:9` (default) or `3:4` (Fremont), Pro plan (0 credits per Flow gen).
- **Prompt**: photoreal DAZ3D / Iray CGI re-render, match composition + lighting + materials exactly, do NOT change framing, no people in frame, PBR materials, scene anchor sentence appended per-slot.
- **Cost**: $0 (Flow Pro free tier).

## Source provenance

| ID | Source URL |
|---|---|
| `street-01-fremont-street` | https://www.google.com/maps/place/E+Fremont+St,+Las+Vegas,+NV/ |
| `street-02-bellagio-strip` | https://www.google.com/maps/search/Bellagio+Hotel+and+Casino+Las+Vegas/ |
| `street-03-montelago-residential` | https://www.google.com/maps/search/MonteLago+Village+Lake+Las+Vegas/ |
| `restaurant-01-peppermill-diner` | https://www.google.com/maps/search/Peppermill+Restaurant+and+Fireside+Lounge+Las+Vegas/ |
| `restaurant-02-eiffel-tower-restaurant` | https://www.google.com/maps/place/Eiffel+Tower+Restaurant/ |
| `restaurant-03-heart-attack-grill` | https://www.google.com/maps/place/Heart+Attack+Grill/ |
| `landmark-01-welcome-to-las-vegas-sign` | https://www.google.com/maps/search/Welcome+to+Fabulous+Las+Vegas+Sign/ |
| `specific-01-container-park-alley` | https://www.google.com/maps/place/Downtown+Container+Park/ |

Each `cgi/<id>-<slug>.png` is a CGI re-render of the corresponding `source/<id>-<slug>.jpg` capture. The CGI ref is the canonical one for projects; the source is kept for provenance and as a fallback if the CGI conversion is unusable for a particular project's needs.

## Known artifacts

- **`restaurant-02-eiffel-tower-restaurant.png`**: the source was a real Eiffel Tower Restaurant kitchen photo with chefs on the line. The CGI conversion suppressed the people as intended, but the model bled "CONTAINER PARK" signage into the kitchen ceiling area — a hallucination influenced by the other refs in the project. The base scene (white subway tile kitchen, stainless steel, plate stacks, Eiffel Tower Restaurant sign on island) is correct; the ceiling carries an extraneous element. Usable as a background ref if framed below the ceiling.
- **`street-01-fremont-street.png`** is 3:4 portrait (rest of pack is 16:9). The Fremont conversion happened at 3:4 before the aspect was switched to 16:9 for subsequent slots. The shot is iconic and clean — kept as-is.

## Rebuilding / extending

To rebuild from scratch or add more slots:

```bash
python3 skills/location-scout/scripts/scout_city.py \
    --city "Las Vegas" --count 11 --force
# Then drive Chrome MCP → Maps → screenshot per slot
# Then run cgi_convert.py per slot or batch through Flow

# Final manifest emit:
python3 skills/location-scout/scripts/cgi_convert.py \
    --pack-dir references/locations/las-vegas/ --emit-manifest
```

See `skills/location-scout/SKILL.md` for the full workflow.
