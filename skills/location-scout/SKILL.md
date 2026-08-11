---
name: location-scout
description: Scout a city via Google Maps and build a reusable pack of photoreal CGI / DAZ3D background reference images for comic production. Use when the user wants to "scout locations in X city", "build a ref pack for X", "I need backgrounds for a X-set comic", or asks for a "Google Maps reference scout." Drives Google Maps via the Chrome MCP to capture random street scenes, restaurants, landmarks, and generic-utility scenes (alleys, rooftops); runs each capture through Higgsfield Nano Banana 2 to convert to photoreal CGI; outputs an organized pack under `references/locations/<city-slug>/` consumable by any comic project. Pre-scouted city packs eliminate manual screenshotting per-project and eliminate the text-prompt-location drift L23 was written to compensate for.
---

# Location Scout — city → reusable CGI ref pack

Pre-scout a city ONCE and get 8–15 photoreal CGI-style location refs covering the spectrum (downtown street, residential street, alley, diner, restaurant, gym, rooftop, casino exterior, etc.). Any comic project set in that city can attach the right pack image as the env ref without re-scouting.

Without a pack: per-project manual screenshots (slow) OR text-prompt-only locations (the model invents architecture; L23's verbal 5-element env anchor exists to compensate). With a pack: attach the pack's CGI ref; the env is anchored to real architecture; L23's verbal anchor becomes a fallback, not a load-bearing rule.

## When this skill is the right tool

- "Scout locations in Las Vegas / Tokyo / Lagos for a comic set there"
- "Build me a Vegas ref pack"
- "I need background refs for a downtown LA story — 10 locations"
- "Google Maps reference scout for [city]"
- Any pre-production phase where a city is named and the project will need multiple env refs

If the user wants refs for a SINGLE location (not a whole city), use `reference-gathering` in `locations/` bucket instead — this skill is for sweeping a city. If the user needs character refs, use `reference-gathering`. If the user is mid-production on a project and just needs a quick env ref for one panel, use the comic-production env workflow.

## Pre-flight checklist (run before any work)

1. **Chrome MCP connected.** If not, halt and ask the user to install the extension. Don't fall through to computer-use (browsers are read-tier).
2. **Higgsfield MCP connected on the right account.** `balance` must return enough credits for the planned conversions (default 11 × 2 credits for `nano_banana_pro`, or 11 × 1.5 for `nano_banana_2`). If credits low, surface to the user before burning the captures.
3. **CWD is the repo or a project that already has a `references/` folder convention.** Default `--output-root` is `references/locations/`. For repo-level shared packs invoke from the repo root; for project-private packs invoke from the project root.

## Phase A — Plan

Run `scripts/scout_city.py --city "<city>" [--count N] [--types streets,restaurants,landmarks,specific]`.

Default scope (count=11):

| Type | Count | Notes |
|---|---|---|
| `street` | 4 | random street view captures spread across the city — downtown, residential, industrial, scenic |
| `restaurant` | 3 | one fancy interior, one diner interior, one street-level exterior |
| `landmark` | 2 | local-distinctive (e.g. for Vegas: a casino exterior, Fremont Street) |
| `specific` | 2 | alleys, rooftops, parking lots — generic-utility shots most projects need |

`--count N` scales every type proportionally (with rounding to keep at least 1 per type). `--types` filters to a subset and rebalances within.

The planner emits `<output-root>/<city-slug>/_targets.json` with an entry per target slot. Each slot has:

```json
{
  "id": "street-01",
  "type": "street",
  "intent": "downtown pedestrian street with neon signage",
  "google_maps_query": null,
  "source_image": null,
  "cgi_image": null,
  "tags": ["downtown", "neon", "pedestrian"]
}
```

`google_maps_query` is `null` after planning — the planner doesn't know the city. **You (Claude) fill it in** for each slot based on the city + intent. Examples for Las Vegas:

- intent `downtown pedestrian street with neon signage` → `Fremont Street Las Vegas`
- intent `residential street` → `Summerlin Las Vegas residential street`
- intent `iconic local landmark` → `Welcome to Las Vegas Sign`
- intent `diner interior` → `Peppermill Fireside Lounge Las Vegas`

Pick queries that resolve to a real, visit-able Google Maps POI for the city.

## Phase B — Capture (Chrome MCP)

For each slot in `_targets.json`:

1. **Navigate** to `https://www.google.com/maps/search/<url-encoded-query>` in a fresh MCP tab.
2. **Find the right result.** Maps usually drops you into a search result panel; for landmarks and businesses, the first result is the right one. For street searches, click the map to enter Street View at a representative point.
3. **Pick a frame**:
   - **Street View available** (street, exterior landmark, exterior restaurant): drop Pegman, pan to face the architecture at eye level (~90° tilt), confirm no people fill the foreground.
   - **Street View not available** (interior restaurant, interior landmark): open the Photos panel of the POI, pick a high-quality professional photo (avoid user phone-quality shots; prefer "Latest" or business-supplied photos).
4. **Screenshot the viewport** at ≥1280×720, save it to a temp path, then register it: `maps_capture.py --pack-dir <pack-dir> --slot-id <id> --query "<maps-query>" --url "<current-url>" --screenshot <temp-path>`. The helper writes the screenshot to `source/<id>-<slug>.jpg` and updates `_targets.json` with `source_image` + `google_maps_query` (the URL is the provenance).
5. **Repeat** for all slots.

If a capture fails (Maps blocks, Street View unavailable, NSFW/private business): substitute with a different POI matching the same intent. The skill ships a *complete* pack — every slot in the plan is filled with a source.

**Suppression rules during capture**:

- **Avoid frames with prominent people.** Pedestrians in the distance are OK; a face filling the frame is not. If unavoidable, the CGI conversion prompt will explicitly suppress them (`no people in frame, only the empty location/setting`).
- **Avoid frames with timestamps, watermarks, Google overlays in the focal zone.** The Street View brand/year stamp at corners is acceptable (the CGI conversion strips it).
- **Avoid blurry / motion-blurred frames.** Pan to settle.

## Phase C — CGI conversion (Higgsfield MCP)

For each entry in `_targets.json` with `source_image` populated:

1. Upload the source via `mcp__c26fa20c-...__media_upload` (single file mode).
2. Call `cgi_convert.py --pack-dir <pack-dir> --slot-id <id> --emit-prompt` to get the structured prompt + Higgsfield params (model, aspect, count, role mappings).
3. Call `mcp__c26fa20c-...__generate_image` with `model=nano_banana_pro` (default — top quality + image-to-image is its strong suit) and the uploaded source as the `image` role. Aspect matches the source (default 16:9 for landscape, 4:3 for interiors). `count: 1`. Resolution default 1k.
4. Poll the job; once complete, fetch the result URL.
5. Run `cgi_convert.py --pack-dir <pack-dir> --slot-id <id> --download "<result-url>"` to download → save as `cgi/<id>-<slug>.png` → update `_targets.json` with `cgi_image`.

### CGI conversion prompt template

The conversion prompt (rendered by `cgi_convert.py`) is:

> Re-render this real-world photograph as a stylized 3D CGI scene — default DAZ3D / Iray render look, architectural visualization quality, video-game cinematic. It should clearly read as a 3D render, NOT a photograph. Cleaner shaders, smoother surfaces, slightly simplified geometry. Match the composition, architecture, lighting direction, time of day, and overall color palette of the source. Do NOT match photographic micro-detail (no skin pores, no dust speckles, no film grain) — keep it CG-clean. Do NOT change the camera angle, framing, focal length, or perspective. Do NOT add or remove buildings, signs, vehicles, or signage text. SAME scene, SAME composition, CGI re-render. No people in frame — only the empty location/setting. If any people appear in the source, render the same scene without them. Remove Google Maps watermarks, Street View brand stamps, and any UI overlays. Render at 1k, stylized 3D CGI look.

The prompt is appended with the slot's `intent` as a one-line scene anchor for the model.

**Why "stylized" instead of "photoreal"**: Nano Banana / GPT Image / similar models default to hyper-photoreal output, which makes the CGI quality vanish — the result reads as a photograph, not a render. Comic background refs benefit from looking clearly CG so they match the photoreal-CGI-styled character renders the pipeline produces. The Vegas v1 pack (June 2026, photoreal prompt) came out so realistic it was indistinguishable from the source photographs; v2 of the prompt (Long Beach pack onwards) explicitly anchors to "default DAZ3D Iray render" + "architectural visualization" + "clearly rendered, not photographic" to claw the CGI look back.

### Model selection

- **`nano_banana_pro` (DEFAULT)** — top quality, best image-to-image fidelity, 2 credits / gen. Use for production city packs.
- **`nano_banana_2`** — fast variant, 1.5 credits / gen, slightly lower fidelity. Use when credit budget tight OR `--fast` is passed.
- **`gpt_image_2`** — alternative when the conversion needs explicit text-rendering preservation (e.g. signage in the scene must stay legible). Per L33, GPT Image 2 has stricter NSFW; the conversion prompt is SFW so this isn't an issue.

Per memory `feedback_higgsfield_model_flash.md`, `nano_banana_flash` is retired; do not use it.

## Phase D — Manifest + README

After all conversions complete, run `cgi_convert.py --emit-manifest`. This writes:

### `meta/locations.json`

```json
{
  "city": "Las Vegas",
  "city_slug": "las-vegas",
  "scouted_at": "2026-06-07T...",
  "count": 8,
  "locations": [
    {
      "id": "street-01-fremont-street",
      "type": "street",
      "name": "Fremont Street",
      "neighborhood": "Downtown",
      "intent": "downtown pedestrian street with neon signage",
      "google_maps_url": "https://www.google.com/maps/search/...",
      "source_image": "source/street-01-fremont-street.jpg",
      "cgi_image": "cgi/street-01-fremont-street.png",
      "tags": ["downtown", "neon", "pedestrian", "night-friendly"]
    },
    ...
  ]
}
```

### `README.md`

A short pack description: what city, when scouted, list of locations with thumbnails, how to use. The README is what shows up when someone opens the pack folder.

The `_targets.json` plan file is kept (provenance) but the canonical consumer file is `meta/locations.json`.

## Output structure

```
references/locations/<city-slug>/
├── README.md
├── _targets.json           # planning artifact (kept for provenance)
├── meta/
│   └── locations.json      # canonical consumer manifest
├── source/                 # raw Google Maps captures (jpg, ~1280×720)
│   ├── street-01-fremont-street.jpg
│   └── ...
└── cgi/                    # CGI-converted refs (png, 1k)
    ├── street-01-fremont-street.png
    └── ...
```

The `cgi/` folder is what gets attached to panel prompts as the env ref. The `source/` folder is provenance + fallback if a CGI conversion is unusable.

## Hard rules

- **No people in CGI output.** Even if the source has pedestrians, the conversion prompt suppresses them. Cast member appearances are handled by character refs, NOT env refs. Per `feedback_no_extra_characters.md`.
- **Always-clothed default applies.** Per the project-wide `always_clothed: true` (L29) — if any partial figure DOES appear (e.g. a distant pedestrian the model couldn't fully suppress), they must be fully clothed.
- **Match source composition exactly.** The conversion prompt forbids camera angle / framing / signage changes. The whole point is to anchor to a real space.
- **Strip Google overlays.** Brand stamps, year tags, search-result chrome — all out. The prompt covers this.
- **Provenance is required.** Every source image's Google Maps URL is recorded in `_targets.json` and `meta/locations.json`. Don't ship a pack without provenance.
- **Photoreal CGI throughout.** Per `feedback_comic_style_3d.md`. The conversion prompt anchors this; don't dilute it.
- **Default `nano_banana_pro` 1k count=1.** Per memory defaults. `--fast` switches to `nano_banana_2`.

## Reuse — how other skills consume city packs

`reference-gathering` (manifest-driven mode): when a project's `references_required.json` declares a `locations[<loc_id>].establishing` and a city-scout pack exists for that city, the manifest walker can resolve "any Vegas downtown street" → pick the closest match from the pack instead of generating from scratch. Match by `type` + tags. See `reference-gathering/SKILL.md` "Location packs from location-scout" section.

`script-breakdown`: when the shotlist has a `setting.city` field AND a pack exists, the emitted `references_required.json` references pack entries by `id` rather than declaring per-project paths.

`comic-production` (panel generation): when a panel's location resolves to a pack entry, attach `cgi/<id>-<slug>.png` as the env ref instead of relying on text-only env description. This is the L23 fallback path.

## Tools used

- `mcp__Claude_in_Chrome__*` — `tabs_context_mcp`, `tabs_create_mcp`, `navigate`, `computer` (screenshot/click), `find`, `read_page`, `browser_batch`, `javascript_tool`
- `mcp__c26fa20c-...__media_upload`, `generate_image`, `job_display`, `balance`
- `Bash` — invoke `scripts/scout_city.py`, `scripts/maps_capture.py`, `scripts/cgi_convert.py`
- `Write` — README.md

## Failure modes

| Failure | Recovery |
|---|---|
| Chrome extension not connected | Halt; ask user to install. Don't fall back to computer-use. |
| Higgsfield credits exhausted mid-pack | Halt the conversion phase; keep `source/` complete; surface to user to top up; resume by running `cgi_convert.py --list-pending-cgi` (lists slots with `source_image` set and `cgi_image` null) and converting each pending slot. |
| Google Maps blocks a query (rate limit) | Wait 10s, retry. If second retry fails, substitute target with a different POI of the same intent. |
| Street View unavailable for target | Fall back to the Photos panel of the POI. If no good photos, substitute a different POI. |
| CGI conversion adds invented buildings / changes framing | Re-render with stricter prompt language ("ZERO new buildings, ZERO new signage, IDENTICAL framing"). If still drifts, accept source-only and flag in README. |
| Pack shipped with broken / drift-y conversion | Source images are kept under `source/` as fallback — projects can attach those directly. |
