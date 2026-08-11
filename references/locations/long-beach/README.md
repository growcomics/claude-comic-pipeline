# Long Beach — location-scout pack

City scout pack of 10 stylized 3D CGI background references for Long Beach, CA. Built `2026-06-08` via the `location-scout` skill. Source captures from Google Maps via Chrome MCP; CGI conversion via Google Flow Nano Banana Pro using the **v2 toned-down prompt** that explicitly anchors to "default DAZ3D / Iray render look, architectural visualization quality" — vs. the Vegas v1 pack which used a photoreal-heavy prompt and came out nearly indistinguishable from the source photographs.

Drop the `cgi/<id>-<slug>.png` files into a comic project's panel prompts as the env ref. The pack covers a spectrum of Long Beach–distinctive locations so any comic project set there can pull from this scout instead of generating per-project.

## Contents

| ID | Type | Where | What |
|---|---|---|---|
| `street-01-pine-avenue` | street | Downtown — Terrace Theater area | Civic / Convention Center building, palms (Pine Avenue rendered as the Terrace Theater area) |
| `street-02-2nd-street-belmont-shore` | street | Belmont Shore — 2nd Street | Sunset beach-town commercial strip, palms, storefront signage |
| `street-03-belmont-heights-residential` | street | Belmont Heights | Suburban residential street at sunset, balcony POV |
| `street-04-port-of-long-beach` | street | Port of Long Beach | Container terminal — gantry cranes, stacked containers, cargo ship at dock |
| `restaurant-01-hofs-hut-diner` | restaurant | East Long Beach | Iconic Hof's Hut diner exterior — red shield logo, striped awnings |
| `restaurant-02-555-east-steakhouse` | restaurant | East Village | Upscale steakhouse interior — dark wood paneling, warm lighting, wine wall |
| `restaurant-03-joe-josts` | restaurant | Anaheim Street | Joe Jost's since-1924 storefront — brick exterior, red awning |
| `landmark-01-queen-mary` | landmark | Long Beach Harbor | The Queen Mary historic ocean liner at dock |
| `landmark-02-aquarium-of-the-pacific` | landmark | Rainbow Harbor | Aquarium of the Pacific iconic curved blue glass facade |
| `specific-01-downtown-promenade` | specific | Downtown | Sunset palm-tree-silhouette street, warm sky |

## Folder layout

```
references/locations/long-beach/
├── README.md            # this file
├── _targets.json        # planning + provenance artifact
├── meta/
│   └── locations.json   # canonical consumer manifest
├── source/              # 10 raw Google Maps captures (JPG)
└── cgi/                 # 10 stylized 3D CGI conversions (PNG, 1376×768 / 16:9)
```

## Generation details

- **Source captures**: Google Maps photos panel, hero-image URL extracted in-page via the Chrome MCP `javascript_tool`, downloaded full-res. 8 of 10 sources came in at ≥1080 px high; Pine Avenue + Belmont Heights came in 608/810 px wide because Google returned a vertical Street View photo as the hero.
- **CGI converter**: Google Flow at `labs.google/fx/tools/flow`, model **Nano Banana Pro**, aspect `16:9`, count x4 per submit. Pro plan (0 credits per Flow gen).
- **Prompt (v2)**: explicitly anchors to stylized 3D render look:

  > Re-render this real-world photograph as a stylized 3D CGI scene — default DAZ3D / Iray render look, architectural visualization quality. It should clearly read as a 3D render, NOT a photograph. Cleaner shaders, smoother surfaces, slightly simplified geometry. ...

  See `skills/location-scout/scripts/cgi_convert.py` `PROMPT_BODY` for the full prompt and the comment explaining why "stylized" beats "photoreal" for background refs.

- **Cost**: $0 (Flow Pro free tier).

## Source provenance

| ID | Source URL |
|---|---|
| `street-01-pine-avenue` | https://www.google.com/maps/place/Pine+Ave,+Long+Beach,+CA/ |
| `street-02-2nd-street-belmont-shore` | https://www.google.com/maps/search/2nd+Street+Belmont+Shore+Long+Beach/ |
| `street-03-belmont-heights-residential` | https://www.google.com/maps/search/Belmont+Heights+Long+Beach/ |
| `street-04-port-of-long-beach` | https://www.google.com/maps/place/Long+Beach+Container+Terminal+(LBCT+LLC)/ |
| `restaurant-01-hofs-hut-diner` | https://www.google.com/maps/place/Hof's+Hut+Restaurant+%26+Bakery/ |
| `restaurant-02-555-east-steakhouse` | https://www.google.com/maps/search/555+East+American+Steakhouse+Long+Beach/ |
| `restaurant-03-joe-josts` | https://www.google.com/maps/search/Joe+Jost%27s+Long+Beach/ |
| `landmark-01-queen-mary` | https://www.google.com/maps/place/The+Queen+Mary/ |
| `landmark-02-aquarium-of-the-pacific` | https://www.google.com/maps/search/Aquarium+of+the+Pacific+Long+Beach/ |
| `specific-01-downtown-promenade` | https://www.google.com/maps/place/The+Promenade+N,+Long+Beach,+CA+90802/ |

## Substitutions / notes

- **Pine Avenue → Terrace Theater area**: Pine Avenue source was a vertical Street View shot of a generic tree-lined block, and Flow's render came back as a downtown civic-building scene (the Terrace Theater area is the closest match). Re-tagged honestly — still a usable downtown Long Beach ref, just not a Pine Ave–specific one.
- **Naples Island canals → Belmont Heights**: Naples Island returned no photos for any of its canal POIs; substituted with Belmont Heights (a nearby Long Beach residential neighborhood with similar suburban character).
- **East Village Arts District → The Promenade N**: arts-district query returned no photos; substituted with The Promenade N, a downtown pedestrian street nearby.

## Why this pack looks different from the Vegas v1 pack

The Vegas pack (`references/locations/las-vegas/`) used a photoreal prompt and the renders came back almost indistinguishable from the source photos — defeating the point of a "CGI" ref. This Long Beach pack uses the v2 prompt anchored to "default DAZ3D / Iray render look", "architectural visualization quality", "cleaner shaders / smoother surfaces / slightly simplified geometry", and "no photographic micro-detail". The result reads clearly as a 3D render — better matches the photoreal-CGI character renders the pipeline produces.

Going forward, all city packs should be built with the v2 prompt. The Vegas pack stays unchanged as the v1 baseline for comparison.

## Rebuilding / extending

```bash
python3 skills/location-scout/scripts/scout_city.py \
    --city "Long Beach" --count 10 --force
# Drive Chrome MCP → Maps → screenshot per slot
# Drive Flow → Nano Banana Pro → 16:9 x4 per slot
# Pick best variant, save to cgi/, run --emit-manifest
```

See `skills/location-scout/SKILL.md` for the full workflow.
