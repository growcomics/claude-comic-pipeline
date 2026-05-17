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
  "style": "photoreal-daz3d",
  "location_strategy": "single",
  "transformation_metadata": {
    "flavor": "body-region-progression",
    "start_tier": 3,
    "end_tier": 5
  },
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
  "transformation_scenes": [
    {
      "name": "april_mutagen_dip",
      "pages": [1, 13],
      "required_body_regions": ["chest", "hips", "suit_fail", "arms", "abs"]
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
          "camera": "low-angle-front, three-quarter",
          "action": "Lara steps into the clearing, sword hand twitching.",
          "dialogue": [
            {"character": "lara", "text": "What is this place?", "type": "balloon"}
          ],
          "captions": ["Day one of the long road home."],
          "sfx": [{"text": "CRUNCH", "source": "footstep on twigs"}],
          "notes": "First reveal of the altar — keep it foreboding, not hostile.",
          "continuity_refs": [],
          "transformation_beat": null
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
- `transformation_beat`: optional. Set on panels that are part of a transformation scene. Allowed values: setup beats (`consider`, `decide`, `trigger`, `first_sensation`), body-region beats (`chest`, `hips`, `rear`, `arms`, `abs`, `legs`, `back`, `shoulders`, `suit_fail`, `whole_body`), or resolution beats (`reveal`, `aftermath`). Used by `rules_audit.py` to verify a transformation scene decomposes into body-region beats rather than skipping from "before" to "after". See "Transformation decomposition" below.
- `transformation_scenes` (top-level, optional): array of scene declarations. Each entry: `{name, pages: [start, end], required_body_regions?: [...], requirements?: {min_setup_beats, min_body_region_beats, min_reveal_beats}}`. Triggers the transformation-beats check at validation time. Use this whenever the script contains a multi-page transformation (FMG, growth arc, mutation, dress-up sequence, charge-up). See "Transformation decomposition" below.
- `style` (top-level, **required**): slug of the visual style preset to lock for the project. Must match a folder name under `skills/style-lock/styles/` (e.g. `photoreal-daz3d`, `ink-line`). Decided via the Step 0 questionnaire — never picked silently by the model. The May 2026 lesson driving this: an earlier April-transformation run defaulted to 2D illustration when 3D CGI was wanted; nothing had asked or required a choice. `rules_audit.py` HARD-fails if missing.
- `location_strategy` (top-level, **required**): one of `single` (one chapter location locked everywhere), `multi` (multiple locations, each locked per scene), or `per-scene` (confirm each detected location individually). Determines how the location-lock invariant is enforced downstream. Decided via the Step 0 questionnaire.
- `transformation_metadata` (top-level, **required when `transformation_scenes` is non-empty**): object with `{flavor: "body-region-progression" | "single-axis" | "other", start_tier: number, end_tier: number}`. Captures the high-stakes transformation choices that the model would otherwise default silently. Decided via the Step 0 questionnaire.

## Workflow

### 0. Project setup questionnaire (BEFORE reading the source)

**Run this FIRST, before parsing the script.** The model has latitude on a few high-stakes decisions that downstream generation cannot recover from if guessed wrong (style being the canonical example — wrong style means *every* generated panel is wrong and the budget is burnt). Each request begins by polling the user with a tight multiple-choice questionnaire, capturing the answers, and writing them into the shotlist's top-level metadata.

Present this block verbatim (drop sections that don't apply once you've read the script — but Q1 and Q2 always apply, even before reading):

```
== Project setup ==

Q1. Visual style?
   a) photoreal-daz3d — DAZ3D Iray photorealistic 3D render (default;
      matches Bay Watch / Lana & Lacy / hand-made April aesthetic)
   b) ink-line — modern indie / Eurocomic ink-line, cel-shaded
   c) other — specify a slug from skills/style-lock/styles/

Q2. Location strategy?
   a) single — one chapter location, locked everywhere (default)
   b) multi — multiple locations, each locked per scene
   c) per-scene — confirm each detected location individually before lock

Q3. Is this a transformation comic?
   a) yes — declare transformation_scenes; body-region beats required
   b) no — standard comic; transformation gates skip
   c) partial — some scenes transform, others don't

(only if Q3 = a or c)

Q3a. Transformation flavor?
   a) body-region-progression — chest → hips → arms → abs etc.
   b) single-axis — single-feature growth (muscle only / size only)
   c) other — describe in source script

Q3b. Character baseline → endpoint? (size tiers 1-6 from the lineup ref)
   Format: "<start>→<end>" — examples: "3→5", "1→6", "custom"

Reply with your choices, e.g.: 1=a, 2=a, 3=a, 3a=a, 3b=3→5
Or say "default" to take all defaults (italicized above).
```

After the user replies, capture the answers into shotlist.json as top-level fields:
- `style`: the slug from Q1
- `location_strategy`: the value from Q2 (`single` / `multi` / `per-scene`)
- `transformation_metadata`: if Q3 is `yes` or `partial`, set `{flavor: ..., start_tier: ..., end_tier: ...}` from Q3a/Q3b; if Q3 is `no`, omit this field

If the user says "default", take all the (a) options: `style=photoreal-daz3d`, `location_strategy=single`, no transformation (set `transformation_metadata` only if the source script obviously demands it; flag this for confirmation at the end).

**Don't infer past the questionnaire.** If the user gave partial answers, ask the missing ones — don't fill them with defaults silently. Polling is the entire point of this step.

**Don't repeat this on re-runs.** If a `shotlist.json` already exists with all three fields populated, skip the questionnaire (and acknowledge that you read the prior choices). If the user wants to change a choice, they'll tell you.

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

### 4.5. Transformation decomposition (when the script has a transformation)

If the source script contains a multi-page transformation — FMG, growth arc, mutation, dress-up, charge-up, expansion sequence — **do not skip from "before" to "after"**. This is the single most-confirmed failure mode of the generation pipeline: a 9-page transformation comic in which the transformation event itself never happens on the page. The hand-made vs Claude-made April comparison (May 2026, `~/Downloads/april-lessons.md`) is the canonical example.

**The unifying principle:** during a transformation, visual weight migrates through the body. Each body region gets its own beat with its own crop. The reveal pulls back but stays close enough for the figure to carry the panel.

**Decomposition steps:**

1. Declare a `transformation_scenes` entry at the top of the shotlist with the page range and (optionally) the specific body regions you'll cover.

2. For each transformation, plan beats in roughly this order:

   | Beat                | Typical framing                  | Typical SFX            | Aspect    |
   |---------------------|----------------------------------|------------------------|-----------|
   | `consider`          | mcu + canister/trigger object    | —                      | portrait  |
   | `decide`            | medium                           | —                      | portrait  |
   | `trigger`           | medium, low-angle-front          | SPLOOSH / CRACK / SNAP | portrait  |
   | `first_sensation`   | medium                           | THROB… THROB…          | portrait  |
   | `chest`             | chest crop (mcu or ecu-region)   | CRRIREEAK + THROB      | landscape |
   | `hips`              | hip crop, rear or three-quarter  | STRRRETCH              | portrait  |
   | `rear`              | rear three-quarter               | —                      | portrait  |
   | `suit_fail`         | rear or side three-quarter       | RRRRIP! / SNAP!        | portrait  |
   | `arms`              | arm close-up (ecu-region)        | RRRRIP + THROB + PULSE | portrait  |
   | `abs`               | torso crop (ecu-region or mcu)   | CRUNCH + RRRRIP        | landscape |
   | `legs`              | leg/thigh crop                   | STRRRETCH              | portrait  |
   | `reveal`            | full body, **close to camera**   | —                      | portrait  |

3. **Not every transformation needs every beat** — pick the body regions that the script's transformation actually affects. A muscle-only transformation might use {arms, chest, abs, suit_fail, reveal}. A whole-body expansion might use {chest, hips, rear, suit_fail, reveal}. The rule is: cover the regions that change, give each its own panel, and end on a close reveal.

4. **Aspect ratio per beat, not per chapter.** Chest expansion → landscape (chest reads across the page). Full-body reveal → portrait (figure fills vertically). ECU body part → portrait. This is set per-panel via `size` and per-prompt at generation time.

5. **Crop migrates through the body.** Successive beats should crop into the region being transformed. Don't pull back to full body until the reveal — and even then, frame close enough that the figure carries the panel.

6. **The reveal closes the loop.** A transformation scene without a reveal beat has no payoff. The reveal is always full-body but tight, typically with a dialogue line ("Look at me!" / equivalent).

**Validation enforces this.** The `rules_audit.py` `check_transformation_beats` test will HARD-fail the shotlist if a declared `transformation_scenes` entry is missing setup, body-region beats (≥3 by default, or the explicit `required_body_regions` list), or a reveal. Don't skip the decomposition and try to ship a transformation as two panels — the gate will reject it before generation.

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
- **Transformation-beats check** (when `transformation_scenes` is declared): each scene must include ≥1 setup beat, ≥3 distinct body-region beats (or all of `required_body_regions` if explicitly listed), and ≥1 reveal beat. The gate that enforces this is `rules_audit.py` — see the script-level enforcement below.

**Script-level enforcement.** After writing `shotlist.json`, run the rules audit on the new file:

```sh
python skills/continuity-check/scripts/rules_audit.py --project .
```

The audit will return HARD findings for camera same-combo overuse (>3 panels at the same distance × angle combo) and for any transformation scene missing setup, body-region beats, or a reveal. If HARD findings exist, surface them inline and revise the shotlist *before* moving to references/generation. Soft findings (variety floor, missing ECU/wide) are hints — review them with the user but don't auto-block.

This pre-generation gate is the cheapest place to catch the failure: re-planning the shotlist costs nothing; regenerating panels after they've been produced wastes the API budget.

### 6. Save

Write `./shotlist.json` and `./shotlist.md` at the project root. Run the rules audit (above). Report panel and page counts back to the user with one or two notable decisions ("treated p7 as a splash for the altar reveal — flag if you want it broken into 3 panels"). If the audit returned HARD findings, also report those and pause for direction. Don't auto-iterate; wait for direction.

### 7. Emit `references_required.json` (L28 — manifest for reference-gathering)

Per **L28** in `comic-production/references/lessons-learned.md`, every comic project must have a complete reference manifest that the `reference-gathering` skill walks. Derive the manifest from the shotlist and write it at project root.

**Per character in `cast[]`:**

- `face_card`: `references/characters/<char_id>/face-card.png`
- `body_tiers`: one entry per distinct `muscle_size_tier` value appearing in any panel's `characters[]` involving this character. Each entry:
  - `tier`: the numeric tier
  - `path`: `references/characters/<char_id>/body-tier{N}.png`
  - `lineup_required`: `false` if `tier == 1`, `true` if `tier >= 2`. **This is the L28 hard rule — tier ≥ 2 body refs MUST be generated with the muscle-size lineup PNG attached as a reference image at generation time.**
  - `tier6_reinforcement_required`: `true` when `tier == 6`, otherwise omit (or `false`). **This is the L29 hard rule** — tier-6 body refs AND every shotlist panel at `muscle_size_tier == 6` MUST attach the two dedicated tier-6 reinforcement PNGs at generation time, IN ADDITION TO the muscle-size lineup. The reinforcement PNGs are repo-bundled at `skills/comic-production/references/peak-body-scale/tier-6/` — they are NOT character-specific generated assets and do NOT go through the `reference-gathering` generation flow; the manifest just flags that the panel-level renderer must attach them.
- `views` (NEW per **L16** — multi-angle character reference packs): for any character with `body_tiers` (i.e. arc characters), emit a `views` array with these 5 entries at the baseline tier:
  - `{"name": "3q-full", "tier": 1, "path": "references/characters/<char_id>/view-3q-full.png", "lineup_required": false}`
  - `{"name": "profile", "tier": 1, "path": "references/characters/<char_id>/view-profile.png", "lineup_required": false}`
  - `{"name": "back-full", "tier": 1, "path": "references/characters/<char_id>/view-back-full.png", "lineup_required": false}`
  - `{"name": "low-angle-front", "tier": 1, "path": "references/characters/<char_id>/view-low-angle-front.png", "lineup_required": false}`
  - `{"name": "ecu-region", "tier": 1, "path": "references/characters/<char_id>/view-ecu-region.png", "lineup_required": false}`

  Non-arc characters (no `body_tiers`) skip the `views` block — face_card only.

If a character has no `muscle_size_tier` values in the shotlist (non-transformation comic), emit only `face_card` for that character.

**Per location in `locations[]`:**

- `establishing`: `references/locations/<loc_id>/_source.jpg`
- `views`: derived from camera direction analysis. For v1: detect shot-reverse-shot patterns. If any two adjacent panels in the same location have cameras with opposing directional cues (e.g. `over-shoulder Lex` followed by `over-shoulder Kara`; or `front` followed by `back-full` of the same scene), add `{"name": "reverse", "path": "references/locations/<loc_id>/_source-reverse.jpg"}`. Otherwise leave `views` empty.

**Per prop in `props[]`** (v1): emit only an `establishing` entry. Prop-state refs are v2.

**Schema example:**

```json
{
  "version": 1,
  "generated_from_shotlist": true,
  "characters": {
    "chunli": {
      "face_card": "references/characters/chunli/face-card.png",
      "body_tiers": [
        {"tier": 1, "path": "references/characters/chunli/body-tier1.png", "lineup_required": false},
        {"tier": 3, "path": "references/characters/chunli/body-tier3.png", "lineup_required": true},
        {"tier": 5, "path": "references/characters/chunli/body-tier5.png", "lineup_required": true},
        {"tier": 6, "path": "references/characters/chunli/body-tier6.png", "lineup_required": true, "tier6_reinforcement_required": true}
      ],
      "views": [
        {"name": "3q-full", "tier": 1, "path": "references/characters/chunli/view-3q-full.png", "lineup_required": false},
        {"name": "profile", "tier": 1, "path": "references/characters/chunli/view-profile.png", "lineup_required": false},
        {"name": "back-full", "tier": 1, "path": "references/characters/chunli/view-back-full.png", "lineup_required": false},
        {"name": "low-angle-front", "tier": 1, "path": "references/characters/chunli/view-low-angle-front.png", "lineup_required": false},
        {"name": "ecu-region", "tier": 1, "path": "references/characters/chunli/view-ecu-region.png", "lineup_required": false}
      ]
    }
  },
  "locations": {
    "lex-lab-redsun": {
      "establishing": "references/locations/lex-lab-redsun/_source.jpg",
      "views": [
        {"name": "reverse", "path": "references/locations/lex-lab-redsun/_source-reverse.jpg"}
      ]
    }
  }
}
```

Save to `./references_required.json` at project root, next to `shotlist.json`. After saving, the next stage (`reference-gathering`) reads this manifest and walks every missing file. **Stage 2 will not close until `rules_audit.py` `check_reference_completeness()` reports clean.**

### Coda

When the user re-runs `script-breakdown` on a project that already has `references_required.json`: regenerate the manifest. The shotlist is the source of truth; the manifest is derived. If the shotlist changed (different tiers, new locations, new shot-reverse-shot scenes), the manifest must regenerate to match. `reference-gathering` will then walk it and produce any missing refs.

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
