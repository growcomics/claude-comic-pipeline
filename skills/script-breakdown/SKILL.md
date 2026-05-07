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
      "ref_folder": "references/lara/",
      "soul_id": null,
      "wardrobe": "leather adventurer's jacket, brown trousers, sword belt"
    }
  ],
  "props": [
    {"id": "altar-stone", "description": "rune-carved stone altar, glowing faintly blue"}
  ],
  "locations": [
    {"id": "forest-clearing", "description": "ring of pines around a moss-covered altar"}
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

## Workflow

### 1. Read the source

Read the script or beat sheet. If pasted inline, work from that. If a path was given, `Read` it. If neither, ask once and stop.

### 2. Identify the cast, props, and locations

First pass: extract every named character (speakers + referenced), every recurring prop, every location. For each cast entry:

- Slugify the name as `id` (`lara`, `night-king`, `thug-a`)
- If `references/<slug>/` exists in the working directory, set `ref_folder`
- Leave `soul_id: null` — `soul-training` fills it later
- Capture wardrobe in one line; this is the wardrobe baseline that `continuity-check` audits against

### 3. Sequence pages, then panels

Decide page count using these defaults (override if the user specifies):

- Short story: 6–12 pages
- Chapter: 18–24 pages
- Issue: 22–32 pages

Per page, plan **3–6 panels** as the workhorse rhythm. Use 1 (splash), 2 (huge moment), or 7+ (action-dense) sparingly and only with story justification.

### 4. Per-panel breakdown

Fill every required field. **Don't leave fields blank.** A missing `camera` becomes a generic shot at generation time; a missing `time_of_day` causes lighting drift across pages.

- **Action** is one or two short sentences in present tense. Describe what's seen, not what's felt.
- **Dialogue** stays under 25 words per balloon. Split long speeches into multiple balloons; `page-composer` chains them.
- **SFX** go on the panel they sound on, not the next.
- **Captions** carry narration or time-jump cues ("Three days later.").
- **continuity_refs** chains a panel to the scene's establishing panel — this is what makes wardrobe drift detectable later.

### 5. Validate

Before saving:

- Every named character in dialogue or action appears in `cast`.
- Every panel has at least: `characters` (or empty for setting-only), `location`, `camera`, `action`.
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

- `reference-gathering` reads `cast[].ref_folder` to know where new refs go
- `soul-training` consumes `cast[]` and writes `soul_id` back into this same file
- `style-lock` writes `style.md` separately, referenced at generation time
- Generation reads each panel's prompt fields plus `style.md`'s prefix/suffix
- `continuity-check` audits every panel against this shotlist
- `page-composer` reads `pages[]` for layout, `dialogue` for balloons, `sfx` for placement
