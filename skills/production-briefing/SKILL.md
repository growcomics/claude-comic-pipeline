---
name: production-briefing
description: One-shot pre-flight briefing for a comic project. Asks transformation type first (FMG / BE / Glute / MMG / Mixed), then the Step 0 questionnaire normally surfaced by script-breakdown (style preset, location strategy, transformation flavor, baseline tiers), then every other setup question in a single batch, then writes `production-config.json` at the project root. Run this once before invoking `/build-comic autopilot`. Triggers on phrases like "production briefing", "set up the project", "start a new comic project", "configure autopilot", "new breast expansion comic", "new male muscle comic", "new glute comic", or auto-invoked by `/build-comic autopilot` when no config exists. NOT a generation skill — does not gather refs, break down scripts, or generate panels. Produces only the config.
---

# Production Briefing

Single-pass setup interview. Collects every decision the rest of the pipeline would otherwise interrupt the run to ask about. Writes one file: `<project_root>/production-config.json`.

Why: today the pipeline asks questions at stage 0 (script-breakdown Step 0 questionnaire — style preset, location strategy, transformation flavor, baseline tiers), stage 1 (script), stage 2 (refs), stage 3 (rules block, budget), stage 3.5 (act-boundary continuity), stage 4 (regen), stage 6 (posting). This skill collapses all of it to one conversation before any work starts. Once written, `/build-comic autopilot` runs to completion without prompting.

## When to use this skill

- User says "start a new comic project", "set up a new project", "production briefing", "configure autopilot", "new BE comic", "new male muscle comic", etc.
- `/build-comic autopilot` is invoked but no `production-config.json` exists at cwd
- User wants to re-configure an existing project (delete the old config and re-run this)

Do NOT use this skill for: actually generating anything (that's `comic-production`), re-reading an existing config (that's just `Read` on the file), or modifying one field in an existing config (use `Edit`).

## Output

One file: `<project_root>/production-config.json`. Schema: `production-config.schema.json` (v3).

## Transformation types supported

The pipeline supports four primary transformation arcs plus a mixed mode. Each drives different rule-block defaults and lineup-file selection. **Pick the type FIRST** — every other default cascades from it.

| Type | What it is | Brand | Default rules ON | Lineup file |
|---|---|---|---|---|
| `fmg` | Female Muscle Growth | GrowGetterComics | **all 10** | `muscle-size-lineup.png` |
| `bg` | Breast + Glute combined (canonical) | BloomBeautyComics | 2, 4, 5, 6, 7, 8, 9 + BE+glute extras | `breast-glute-size-lineup.png` |
| `be` | Breast Expansion only (legacy) | BloomBeautyComics | 2, 4, 5, 6, 7, 8, 9 + BE-specific extras | `breast-size-lineup.png` |
| `glute` | Glute / butt expansion only (legacy) | BloomBeautyComics | 2, 4, 5, 6, 7, 8, 9 + glute-specific extras | `glute-size-lineup.png` |
| `mmg` | Male Muscle Growth | MaxxMuscleComics, male 3DMC | 1, 2, 4, 5, 6, 7, 8, 9, 10 (drop 3 = muscle≡breasts) + male-anatomy extras | `male-muscle-lineup.png` |
| `mixed` | Multi-arc (BG+FMG or any combo) | any | all 10 + multi-arc extras | depends on active stage |

### Per-type rule defaults

The 10 mandatory rules (from `comic-production/SKILL.md`):
1. Muscles natural healthy skin tone, NOT red/inflamed
2. Skin wet, shiny, glistening with effort
3. Enlarged muscles = proportionally enlarged breasts with cleavage
4. Characters fully clothed (may be torn/stretched, never absent)
5. Speech bubbles correctly attributed
6. Every bubble unique (no echo)
7. Every face vivid/animated/expressive (never neutral)
8. Characters look at each other, never at camera
9. Correct anatomy (two arms, no extra limbs)
10. Muscles never revert (size monotonic)

**FMG default**: ALL 10 rules. This is the current default behavior of the pipeline. No drops, no additions, no surprises.

**BE default**: rules 2, 4, 5, 6, 7, 8, 9 ON. Rules 1, 3, 10 OFF (they're FMG-specific). Recommended `extra_lines`:
- "Breast size monotonic across panels — once larger, never smaller, no reversion across the full chain."
- "Hourglass figure maintained throughout — small waist, broad hips, regardless of breast tier."
- "Cleavage visible at tier 2+ — neckline appropriate to the scene, but cleavage always readable."
- "Round (not teardrop) breast shape; symmetric; no veining unless explicitly noted at tier 5+."
- "When a clothing item strains or splits, it splits along the seam, never magically vanishes."

**Glute default**: rules 2, 4, 5, 6, 7, 8, 9 ON. Rules 1, 3, 10 OFF. Recommended `extra_lines`:
- "Glute size and hip-to-waist ratio monotonic across panels — once curvier, never narrower."
- "Hourglass figure emphasized: narrow waist, broad hips, prominent rear regardless of camera angle."
- "Glute shape rounded and full (not flat, not square); side-profile shows clear curve."
- "Thigh-to-glute proportion balanced — thighs scale with glutes, not dramatically thinner."
- "Wardrobe stretches at the seat and waistband first; tearing always along the seam."

**MMG default**: rules 1, 2, 4, 5, 6, 7, 8, 9, 10 ON. Rule 3 OFF (no breasts on male characters). Recommended `extra_lines`:
- "Male anatomy throughout — never feminize the figure during growth. No breasts, no hourglass waist."
- "Pectoral muscles, not chest curves — pec separation visible, square chest geometry, clear sternum line."
- "Broad shoulders, narrow hips — V-taper build emphasized at tier 3+."
- "Facial structure stays masculine through growth (strong jaw, brow ridge); no softening."
- "Body hair appropriate to the character — once established, maintained across the chain."

**Mixed default**: all 10 rules ON. Recommended `extra_lines`:
- "Multi-arc comic — characters may go through BE, glute, and FMG progressions in sequence per the script."
- "Growth order is breasts → glutes → muscles (per posing-and-expressions.md)."
- "Each completed arc stays at its peak: once breasts grow they stay; once glutes grow they stay; once muscles grow they stay."
- "When multiple arcs run simultaneously on the same character, the panel's primary lineup ref is the one for the CURRENTLY ACTIVE growth stage; the other arcs are described verbally in the prompt only."

The user can override any of these — these are starting defaults, not commandments.

### Lineup files

The `lineup_files` block in the config points to the size-anchor PNG used by `next_panel.py`. Each transformation type expects a different file. The pipeline's `find_lineup()` searches these locations in order: `<project>/references/style/<filename>`, repo-bundled `assets/`, `~/.claude/skills/comic-production/assets/`.

**Today only the FMG lineups ship with the pipeline.** For BE, glute, or MMG runs, the user must create the equivalent lineup file (numbered 1-6 figures in identical pose, progressive growth of the relevant attribute, same outfit / hair / background) and drop it in `<project>/references/style/`. If the file is missing, `next_panel.py` emits `MISSING_lineup` and autopilot halts cleanly per the missing-ref-guardrail policy. This is by design — phantom refs are worse than no refs.

If no lineup file exists for the chosen type yet, that's fine — proceed with the briefing, set `lineup_files.tier_low` to the expected filename, and create the PNG before starting generation. The briefing will warn about missing lineups but not block.

## Step 0 absorption (NEW)

The pipeline's `script-breakdown` skill now opens with a Step 0 questionnaire that polls the user on three high-stakes decisions before parsing any script:

1. **Visual style** (a) `photoreal-daz3d` / (b) `ink-line` / (c) other
2. **Location strategy** (a) `single` / (b) `multi` / (c) `per-scene`
3. **Transformation flavor + baseline tiers** when applicable

Without autopilot, script-breakdown interrupts mid-pipeline to ask. With autopilot, the briefing collects these answers up front and writes them into `production-config.json`'s `script_breakdown.*` block. script-breakdown then reads from the config and does NOT re-prompt.

The briefing batches Step 0 into the same single-message interview as the rest of the questions — no second round trip.

## Workflow

### 1. Locate or set the project root

If the user already specified a path, use it. Otherwise default to cwd. Common conventions:
- Per-project subfolder under a working directory (e.g. `~/Desktop/claude/devotion-2/`). The user's working folder is `~/Desktop/claude/` — comic projects live inside it.
- Confirm the path with the user before writing. This becomes `project.root`.

### 2. Run the interview — ONE message, every question

Bundle all questions into a single message to the user. Format as a structured list with defaults clearly marked. The user replies once. Don't iterate.

The interview template:

```
Setting up production-config.json for this project. Answer once, autopilot runs without further questions afterwards.

TRANSFORMATION TYPE (drives every other default — answer this first)
  1. Type [fmg / be / glute / mmg / mixed]:
       fmg     = Female Muscle Growth (GrowGetter default)
       be      = Breast Expansion (Bloom Beauty BE arcs)
       glute   = Glute / butt expansion (Bloom Beauty glute arcs)
       mmg     = Male Muscle Growth (MaxxMuscle, male 3DMC)
       mixed   = Multi-arc comic (BE+glute+FMG or any combo)
  2. Subtype [optional, free-form; e.g. 'be-hyperbreast', 'mmg-bodybuilder', 'fmg-hyperreal']:

PROJECT BASICS
  3. Project name (display, e.g. "devotion-2"):
  4. Project root path [default: <cwd>]:
  5. Brand [GrowGetter / Bloom / MaxxMuscle / 3DMC / MGAI / other]:

PLATFORM
  6. Platform [higgsfield / flow / hybrid]:
  7. If higgsfield: folder ID? Default ref_type [nano_banana_2_job slow-free / nano_banana_flash_job fast-paid]?
  8. If flow: count per panel [x1 / x4 default x4]? Aspect override [none / 1:1 / 3:4 / 4:3 / 9:16 / 16:9]?

SCRIPT
  9. Script source: [path to file / paste inline / existing shotlist.json to reuse]:
  10. (If pasting inline, paste below this question.)

STEP 0 QUESTIONNAIRE (absorbed from script-breakdown — answers feed shotlist.json top-level)
  11. Visual style [photoreal-daz3d default / ink-line / other-slug]:
        photoreal-daz3d = DAZ3D Iray photorealistic 3D render (default)
        ink-line        = modern indie / Eurocomic ink-line, cel-shaded
        other-slug      = any folder name under skills/style-lock/styles/
  12. Location strategy [single default / multi / per-scene]:
        single    = one chapter location locked everywhere
        multi     = multiple locations, each locked per scene
        per-scene = confirm each detected location individually
  13. Is this a transformation comic? [yes / no / partial]
        yes     = declare transformation_scenes; body-region beats required
        no      = standard comic; transformation gates skip
        partial = some scenes transform, others don't
  14. (if 13=yes/partial) Transformation flavor [body-region-progression default / single-axis / other-free-form]:
  15. (if 13=yes/partial) Baseline tier → endpoint tier (1-6 lineup scale): e.g. "3→5"

LINEUP FILES (auto-populated from transformation type; override if needed)
  16. tier_low filename [default per type — see table]:
  17. tier_high filename [default per type, optional]:

MANDATORY RULES BLOCK
  Defaults are auto-populated from transformation type (see briefing skill for the per-type table).
  18. Override default rule set? Either:
       (a) accept the type's defaults (most common — just say "accept defaults")
       (b) list which rule numbers to drop FROM the type default
       (c) list which rule numbers to add TO the type default
  19. Allow baked lettering (L19 experimental)? [no default / yes]:
        no  = strip all bubbles/SFX/captions from prompts (L7 Case B canonical rule)
        yes = bake lettering as physical scene objects with aggressive anchoring (L19)
  20. Additional project-specific extra_lines [optional, any]:

REFERENCES
  21. Reference policy [skip-if-populated default / refresh-always / rebuild]:
  22. Frames per character [default 5, min 3]:

GENERATION
  23. Max panel cap [empty = no cap]:
  24. Max retries per panel [default 3]:
  25. On all-variants-bad [retry-with-cgi-anchor-boost default / halt / skip-with-flag]:
  26. Pick variant [claude default / user — user mode adds back per-panel gates]:

CONTINUITY
  27. Stage 1 audit policy [halt-on-hard default / log-only]:
  28. Act-boundary audit policy [halt-on-hard default / always-halt / halt-on-hard-or-soft / log-only]:
  29. Vision audit scope [full-issue default / skip / act-only]:
  30. Arc character slug [empty = auto-infer]:

REGENERATION
  31. Regeneration policy [batch-end default / never / auto-on-hard / halt-on-hard]:

PAGE COMPOSER
  32. Export PDF at end [yes default / no]:
  33. Page size px [default 2048×3072]:

The approved halt conditions are non-negotiable: content-policy refusal, MISSING_* ref guardrail, WARNING_DIALOGUE_CAMERA_CONFLICT (L12), WARNING_MULTI_SPEAKER_CROWDING (L13), Stage 1 audit HARD, environmental failure, script-level ambiguity. Autopilot stops on these. Everything else is policy-driven from your answers.

Reply with your numbered answers (skip any to accept defaults).
```

**Hot path** — when the user just wants a typical run for one of the standard brands, accept "use Bloom Beauty BE defaults" / "use GrowGetter defaults" / "use MaxxMuscle defaults" as a one-line answer. Map:
- "GrowGetter defaults" → fmg + brand=GrowGetterComics + all defaults + style=photoreal-daz3d + location_strategy=single + no transformation_scenes unless script forces it
- "Bloom Beauty BE defaults" → be + brand=BloomBeautyComics + BE rule defaults + breast-size-lineup.png + style=photoreal-daz3d + location_strategy=single + transformation_metadata={flavor:body-region-progression, start_tier:1, end_tier:5}
- "Bloom Beauty glute defaults" → glute + brand=BloomBeautyComics + glute rule defaults + glute-size-lineup.png + style=photoreal-daz3d + location_strategy=single + transformation_metadata={flavor:single-axis-glute, start_tier:1, end_tier:5}
- "MaxxMuscle defaults" → mmg + brand=MaxxMuscleComics + MMG rule defaults + male-muscle-lineup.png + style=photoreal-daz3d + location_strategy=single + transformation_metadata={flavor:body-region-progression, start_tier:1, end_tier:6}
- "3DMC male defaults" → mmg + brand=3DMuscleComics + MMG rule defaults + male-muscle-lineup.png
- "3DMC female defaults" → fmg + brand=3DMuscleComics + FMG defaults + muscle-size-lineup.png

Still confirm the project root, platform, and script source individually — those are project-specific even on the hot path.

### 3. Validate

Before writing the file:

- `project.root` exists as a directory (or was just created)
- `transformation_type` is one of fmg / be / glute / mmg / mixed
- `platform` is one of higgsfield / flow / hybrid
- If platform=higgsfield: folder_id is present (warn if empty)
- `mandatory_rules.active` is a subset of {1..10}, post-applying any drops/adds
- If `mandatory_rules.allow_baked_lettering=true`: surface a warning that this opts into L19 experimental territory and that the generation prompt will compose bubbles/SFX as physical scene objects instead of clean renders.
- If script_source.type=path: the path resolves to a file
- If `arc_character` is set and script_source = existing-shotlist: confirm it appears in cast[]
- `max_retries_per_panel` ≥ 1
- `lineup_files.tier_low` — check if the file actually exists in any of the search paths. Warn (don't block) if missing — the user may be planning to create it before generation starts.
- `script_breakdown.style_preset` must match a folder under `skills/style-lock/styles/`. Default `photoreal-daz3d` always passes.
- `script_breakdown.location_strategy` is one of `single` / `multi` / `per-scene`.
- If `script_breakdown.transformation_metadata` is non-null: `flavor` is a non-empty string, `start_tier` and `end_tier` are integers in [1,9], `start_tier ≤ end_tier`.

Surface any warnings before writing. Don't write a broken config.

### 4. Write `production-config.json`

Single file at `<project.root>/production-config.json`. Schema field order for readability. Pretty-print, 2-space indent. Include `version: 3`.

### 5. Confirm + next step

Final message:

```
Config written: <project.root>/production-config.json

Transformation type: <type>
Rules block: <N>/10 rules active + <M> extra_lines
Allow baked lettering: <yes/no>
Lineup: <tier_low> (file <found / NOT FOUND — drop in references/style/ before generation>)
Step 0:
  style_preset: <style>
  location_strategy: <strategy>
  transformation_metadata: <metadata or "n/a">

Next: /build-comic autopilot
  → walks stages 1-5 (script → references → generation → continuity → composition)
  → no per-stage gates, no questions per panel
  → halts only on the approved hard conditions
  → stops cleanly after PDF export; posting stays manual

To re-configure: delete production-config.json and run this skill again.
To edit one field: open the JSON and edit it.
```

Do NOT auto-invoke `/build-comic autopilot`. User may want to review.

## Hard rules

- **Single round trip.** One interview message. One reply with answers. Don't decompose across multiple messages.
- **Transformation type drives defaults.** Don't ask the rules-block question without first knowing the type — the table maps it.
- **Step 0 lives here, not in script-breakdown.** When autopilot is active, briefing collects style preset / location strategy / transformation metadata so script-breakdown doesn't have to. The values land in `production-config.json`'s `script_breakdown.*` block; script-breakdown reads them at run time.
- **No work beyond the config.** Writes ONE file. Doesn't break down scripts, gather refs, or anything else.
- **Defaults are real defaults.** If the user skips a question, write the documented default into the JSON — don't omit the field.
- **Never overwrite an existing config without confirming.** If `production-config.json` exists at the chosen root, show a diff and ask before overwriting.
- **Don't read the script.** That's `script-breakdown`'s job. The briefing just records WHERE.
- **Validate lineup file existence as a warning, not a block.** The user may know the file will exist by the time generation runs.

## Hand-off

After writing `production-config.json`:

1. `script-breakdown` reads `script_breakdown.style_preset` / `script_breakdown.location_strategy` / `script_breakdown.transformation_metadata` and writes them into shotlist.json's top-level fields. Skips the Step 0 questionnaire entirely when config is present.
2. `comic-production` reads `mandatory_rules.active` + `mandatory_rules.extra_lines` + `mandatory_rules.allow_baked_lettering` at panel-prompt time
3. `next_panel.py` reads `lineup_files.tier_low` / `tier_high` (when `--config` flag is added) or uses the file under the per-type filename
4. `/build-comic autopilot` reads `policies.*` at each previously-gated decision
5. `continuity-check` reads `policies.regeneration`, `continuity.monotonic_attribute`, `continuity.arc_character`
6. `page-composer` reads `page_composer.*`
7. The Stop hook doesn't read the config — it just checks `.autopilot-active` sentinel

## Common asks

- **"Set up a Bloom Beauty BE comic"** → transformation_type=be, brand=BloomBeautyComics, lineup=breast-size-lineup.png, rules per BE defaults, style_preset=photoreal-daz3d, location_strategy=single, transformation_metadata pre-filled. Confirm script source + Flow vs Higgsfield. Write.
- **"Set up a male muscle growth comic"** → transformation_type=mmg, brand=MaxxMuscleComics, lineup=male-muscle-lineup.png, rules per MMG defaults. Confirm platform + script. Write.
- **"Same as devotion-2 but different script"** → ask for the prior config path, read it, swap project + script_source, write to new path.
- **"I want to keep per-panel gates"** → set `generation.pick_variant=user`. Autopilot still runs but pauses for variant pick per panel.
- **"Try the L19 baked-lettering experiment"** → set `mandatory_rules.allow_baked_lettering=true`. comic-production will bake SFX + speech bubbles as physical scene objects per L19; expect higher 2D-drift risk on weaker models, mitigated by the L19 anchoring suffix.

## What this does NOT do

- Doesn't start generation.
- Doesn't gather references.
- Doesn't break down scripts.
- Doesn't start the token bridge (Higgsfield).
- Doesn't open Flow in Chrome.
- Doesn't install the Stop hook (one-time `~/.claude/hooks/` setup).
- Doesn't create the lineup PNG if one is missing — the user does that.

All downstream of the config. Briefing writes the config and exits.
