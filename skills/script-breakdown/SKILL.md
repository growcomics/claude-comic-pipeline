---
name: script-breakdown
description: Convert a comic script, prose story, or beat sheet into a structured per-panel shotlist that captures characters, location, camera, action, dialogue, captions, and SFX for every panel. Use when the user wants to break down a comic script, plan panels for a chapter, generate a shotlist, prep prose for panel generation, or sequence a story into pages and panels. Trigger phrases include "break down this script", "turn this into panels", "plan the shotlist", "shotlist for chapter X", "how many panels", "plan the pages", "script to panels".
---

# Script Breakdown

Convert a script or beat sheet into a `shotlist.json` (machine-readable) and `shotlist.md` (human-readable) that the rest of the comic pipeline consumes — `reference-gathering` reads cast slugs, `soul-training` writes Soul IDs back, `style-lock` runs alongside, image generation reads each panel's prompt fields, `continuity-check` audits against this shotlist, and `page-composer` reads dialogue and layout hints.

## When this skill is the right tool

- "Break down chapter 3 into panels"
- "Turn this prose into a comic"
- "How many panels does this script need?"
- "Plan the shotlist for the next 12 pages"
- "Sequence this beat sheet into pages and panels"

If the user wants to *write* a script (not break one down), this skill is not the right tool — ask for the script first. If they only have a one-paragraph idea, push back and ask for a beat sheet rather than fabricating one.

## Output

Write both:

- `shotlist.json` — canonical machine format. Every other skill in the pipeline reads this.
- `shotlist.md` — human review version with the same content prettified.

### shotlist.json schema

```json
{
  "project": "lara-and-the-altar",
  "version": 1,
  "page_count": 12,
  "cast": [
    {
      "id": "lara",
      "name": "Lara",
      "ref_folder": "references/characters/lara/",
      "soul_id": null,
      "wardrobe": "leather adventurer's jacket, brown trousers, sword belt"
    }
  ],
  "props": [
    {
      "id": "altar-stone",
      "description": "rune-carved stone altar, glowing faintly blue",
      "ref_folder": "references/props/altar-stone/"
    }
  ],
  "locations": [
    {
      "id": "forest-clearing",
      "description": "ring of pines around a moss-covered altar",
      "ref_folder": "references/locations/forest-clearing/"
    }
  ],
  "pages": [
    {
      "page_number": 1,
      "panels": [
        {
          "panel_id": "p01-01",
          "size": "splash | wide | tall | standard",
          "characters": ["lara"],
          "location": "forest-clearing",
          "time_of_day": "dawn",
          "weather": "mist",
          "camera": "low angle, three-quarter",
          "action": "Lara steps into the clearing, sword hand twitching.",
          "dialogue": [
            {"character": "lara", "text": "What is this place?", "type": "balloon"}
          ],
          "captions": ["Day one of the long road home."],
          "sfx": [{"text": "CRUNCH", "source": "footstep on twigs"}],
          "notes": "First reveal of the altar — keep it foreboding, not hostile.",
          "continuity_refs": []
        }
      ]
    }
  ]
}
```

Field rules:

- `panel_id` is unique across the project: format `pNN-NN` (page-panel).
- `size`: `splash` = whole page; `wide` = full row; `tall` = full column; `standard` = grid cell.
- `dialogue.type`: one of `balloon` (spoken), `thought` (internal), `whisper` (dashed border), `shout` (jagged), `caption` (rectangular box, narration), `off-panel` (from outside the panel).
- `continuity_refs`: panel_ids this panel must match for wardrobe/prop/time-of-day continuity. Usually points back to the scene's establishing panel.
- `cast[].ref_folder` / `props[].ref_folder` / `locations[].ref_folder`: relative paths from the project root to the reference-gathering folder for that subject. Use the typed-bucket convention from `reference-gathering`: `references/characters/<id>/`, `references/props/<id>/`, `references/locations/<id>/`. **Required** for hero subjects (named characters, recurring props, locations appearing in 2+ panels). **Optional** for one-off backgrounds or single-appearance props — omit the field entirely rather than setting it to a folder that won't be populated.
- `locations[].ref_folder` for CGI comic projects should contain a `_source.jpg` (DAZ3D-scene-reference render) per `comic-production`'s `references/environment-references.md` — this is what generation attaches as an environment ref via `medias[]`.
- `camera`: a distance + angle pair using the categories defined in `comic-production`'s `references/cinematic-framing.md` (e.g., `"low-angle-front, three-quarter"`, `"ecu-face"`, `"wide-establish"`). Run the variety check (≥5 distance + ≥4 angle categories, ≤3 panels at the same combo, ≥1 ECU and ≥1 wide-establish/splash per 10-panel sequence) during validation.

## Workflow

### 1. Read the source

Read the script or beat sheet. If pasted inline, work from that. If a path was given, `Read` it. If neither, ask once and stop.

### 2. Identify the cast, props, and locations

First pass: extract every named character (speakers + referenced), every recurring prop, every location.

For each **cast** entry:
- Slugify the name as `id` (`lara`, `night-king`, `thug-a`)
- Set `ref_folder` to `references/characters/<id>/`. If that folder already exists in the working directory, `reference-gathering` will write into it next; if not, gathering will create it.
- Leave `soul_id: null` — `soul-training` fills it later (when that stage runs)
- Capture wardrobe in one line; this is the wardrobe baseline that `continuity-check` audits against

For each **prop** entry:
- Slugify the name as `id` (`altar-stone`, `lara-sword`, `signal-flare`)
- One-line `description`
- Set `ref_folder` to `references/props/<id>/` for recurring or signature props. **Omit the field entirely** for one-off / disposable props — don't set an empty folder path.

For each **location** entry:
- Slugify the name as `id` (`forest-clearing`, `bisons-lair`, `chinese-alley`)
- One-line `description` (furniture, props, lighting, colors, time-of-day baseline)
- Set `ref_folder` to `references/locations/<id>/` for hero locations. For CGI comic projects, this folder should contain a `_source.jpg` (DAZ3D-scene-reference render) per `comic-production`'s `references/environment-references.md`. For one-off or generic outdoor settings, omit the field.

### 3. Sequence pages, then panels

Decide page count using these defaults (override if the user specifies):

- Short story: 6–12 pages
- Chapter: 18–24 pages
- Issue: 22–32 pages

Per page, plan **3–6 panels** as the workhorse rhythm. Use 1 (splash), 2 (huge moment), or 7+ (action-dense) sparingly and only with story justification.

### 4. Per-panel breakdown

Fill every required field. **Don't leave fields blank.** A missing `camera` becomes a generic shot at generation time; a missing `time_of_day` causes lighting drift across pages.

- **Camera** is a distance + angle pair (plus an optional composition modifier) drawn from the categories in `comic-production`'s `references/cinematic-framing.md` — e.g., `"low-angle-front, three-quarter"`, `"ecu-face"`, `"wide-establish, dutch"`. Vary the camera deliberately across the sequence using one of the rhythm patterns (pull-in, pull-out, alternating field, orbit). Don't default every panel to medium-eye-level-front — that produces a camera-static comic regardless of how good the action is.
- **Action** is one or two short sentences in present tense. Describe what's seen, not what's felt.
- **Dialogue** stays under 25 words per balloon. Split long speeches into multiple balloons; `page-composer` chains them. Dialogue lines live in the shotlist as data — generation never renders speech bubbles into the image (see L7 Case B in `comic-production`'s `references/lessons-learned.md`; that's what causes 2D drift in CGI panels).
- **SFX** go on the panel they sound on, not the next. SFX is also data in the shotlist — `page-composer` letters it on top of the clean render. **Never write SFX text into the panel's generation prompt** — same L7 Case B failure mode. If a dramatic splash needs an in-render SFX cue, render it as a physical scene object (extruded chrome letters in the scene), per the `environment-references.md` / `cinematic-framing.md` guidance.
- **Captions** carry narration or time-jump cues ("Three days later."). Lettered by `page-composer`, never baked into the generation.
- **continuity_refs** chains a panel to the scene's establishing panel — this is what makes wardrobe drift detectable later.

### 5. Validate

Before saving:

- Every named character in dialogue or action appears in `cast`.
- Every panel has at least: `characters` (or empty for setting-only), `location`, `camera`, `action`.
- Every panel's `location` exists in `locations[]`.
- Every panel's referenced props (if any) exist in `props[]`.
- Hero subjects (named characters, recurring props, hero locations) have a `ref_folder` set. The folder doesn't need to be populated yet — `reference-gathering` runs next — but the path must be recorded so downstream coverage checks have something to verify.
- **Camera variety check** (see `comic-production`'s `references/cinematic-framing.md`): for any 10-panel sequence, the panel `camera` values must include ≥5 distinct distance categories, ≥4 distinct angle categories, ≤3 panels at the same distance × angle combo, ≥1 ECU (face or region) and ≥1 wide-establish or splash. Document an intentional violation in the project notes (e.g., a sustained intimate dialogue beat that legitimately holds on mcu — still flag it explicitly).
- Page numbers are contiguous starting at 1.
- Total panel count roughly matches pages × 4 (sanity check, not a rule).
- No dialogue balloon exceeds 25 words.

### 6. Save

Write `./shotlist.json` and `./shotlist.md` at the project root. Report panel and page counts back to the user with one or two notable decisions ("treated p7 as a splash for the altar reveal — flag if you want it broken into 3 panels"). Don't auto-iterate; wait for direction.

## Hard rules

- **Don't fabricate dialogue.** If the script doesn't give a line, leave dialogue empty for that panel — let `action` carry it.
- **Don't pad pages.** If the story fits in 8 pages, deliver 8.
- **Don't merge unnamed characters.** If two thugs are present, list them as `thug-a`, `thug-b` — the generator needs distinct identities or it'll produce one face for both.
- **Don't skip the cast pass.** Generation will produce wrong faces if the cast list is incomplete or imprecise.
- **Wardrobe baseline is set on first appearance.** If a character changes outfits later, that's a new cast entry (`lara-formal`) — don't try to encode wardrobe history in one row.

## Common asks

- "Just give me the rough beats" — fill `action` and `characters` per panel; leave camera/dialogue empty. Note the partial-fill in the project-level `notes`.
- "Fewer pages" — cut panels first, then merge pages. Don't compress dialogue.
- "More pages" — expand action panels, not dialogue panels.
- "Different layout for the climax" — use `size` hints (splash on the climax panel) rather than reshaping the whole shotlist.

## Hand-off

After `shotlist.json` is written:

- `reference-gathering` reads `cast[].ref_folder`, `props[].ref_folder`, and `locations[].ref_folder` to know where new refs go (one folder per subject, typed buckets: `characters/`, `props/`, `locations/`)
- `soul-training` (when that stage runs) consumes `cast[]` and writes `soul_id` back into this same file
- `style-lock` writes `style.md` separately, referenced at generation time
- Generation reads each panel's prompt fields plus `style.md`'s prefix/suffix; attaches `medias[]` references from `cast[].ref_folder` (character anchors), `locations[].ref_folder` (environment anchor — for hero locations using the DAZ3D-scene-reference trick from `comic-production`'s `references/environment-references.md`), and `props[].ref_folder` (when the panel calls for a recurring prop)
- `continuity-check` audits every panel against this shotlist
- `page-composer` reads `pages[]` for layout, `dialogue` for balloons, `captions` for caption boxes, `sfx` for SFX placement — **all lettering happens here, never in the generation prompt** (per L7 Case B in `comic-production`'s lessons-learned, baked-in lettering causes 2D drift in CGI panels)
