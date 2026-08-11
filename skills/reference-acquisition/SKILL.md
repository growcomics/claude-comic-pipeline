---
name: reference-acquisition
description: Convert an internet-sourced character image into a photoreal 3D base reference. Use when bootstrapping a NEW character — start from official art, a game screenshot, a show capture, or fan reference and produce a clean 3D-rendered anchor at references/characters/<slug>/internet-3d-base.png that all subsequent reference and panel generation matches against. Trigger phrases include "bootstrap a new character", "convert this image to a 3D ref", "make a base ref from this internet image", "I have an internet image of X — make me a starter ref", "set up a new character from this screenshot".
---

# reference-acquisition

Converts an internet character image into the photoreal 3D base reference
that anchors everything generated for that character afterwards.

(Ported 2026-08-10 from the parked `refactor/refs-are-truth-prompts-are-action`
branch and updated for the current pipeline — see CHANGELOG. The branch's
`rules/attach/internet_3d_base.py` auto-attach rule does NOT exist on main;
the downstream wiring below reflects what main actually runs.)

## Why this skill exists

Per **L10 — references are the truth, prompts are deltas**
(`skills/comic-production/references/lessons-learned.md`): appearance lives in
attached IMAGES; prompts carry action, camera, lighting. For that to work,
every character needs one strong identity image before anything else is
generated. The canonical bootstrap:

1. **Find a good internet image.** Official art, a game screenshot, a show
   capture, fan reference. Clear depiction, full or 3/4 body, neutral-ish
   pose, well-lit, high resolution. (Finding it is `reference-gathering`'s
   job — that skill owns search + provenance for characters, locations,
   props.)
2. **Convert it to a photoreal 3D render.** A content-preserving conversion
   that keeps identity (face, hair, costume, colors, proportions) and strips
   the source's style/lighting/composition baggage. This is the
   character-side twin of `reference-gathering`'s real-photos → CGI location
   plates (§ "Real photos → CGI plates").
3. **Save at the canonical path** —
   `references/characters/<slug>/internet-3d-base.png`.

The result is the COMPLETE canonical character in one image — face + body +
costume + proportions — the strongest single-image identity anchor for
downstream generation.

## Where it sits in the pipeline

- `reference-gathering` FINDS and saves source images (and already handles
  the location/prop conversions).
- **This skill** converts ONE chosen character source into the 3D base
  anchor.
- `reference-sheets` / `comic-production` then generate the face card,
  body-tier refs, turnarounds, and cast lineup **with the base ref
  attached** — dependency chaining, per `reference-sheets` Step 3 (variants
  are generated WITH their base). `reference-gathering`'s manifest mode
  declares those paths (`face-card.png`, `body-tierN.png`); generate them
  against this anchor, not from prose.
- After a project locks its cast, generated refs (cast lineup + size guide)
  take over as the day-to-day anchors per
  `feedback_use_generated_refs_after_lockin` — the internet-3d-base remains
  the identity ground truth to return to when drift appears.

## Gate boundary (read before generating)

This skill covers **repo-level bootstrap only** — a character being set up
under `references/characters/` before or outside any project. Inside a
project that has the `qa/` protocol chain, ALL generation — reference sheets
included — goes through `qa/compose.py` → audit → submit → post-flight →
bank (CLAUDE.md § Generation protocol). Never use this skill's inline prompt
as a freehand bypass in project context; wire the character into the
project's staging and let the chain compose.

## Workflow

### Step 1 — get the source image

The user provides a URL, a local path, or an uploaded image. Save it to
`references/characters/<slug>/_source.<ext>`. If URL-only: download, then
verify the saved file is a real image (non-zero bytes, valid header) before
proceeding. If it isn't, stop and ask for an alternate source.

### Step 2 — slug + folder + provenance

The slug is the character's machine-friendly name: lowercase, hyphenated, no
spaces (`chun-li`, `emma-frost`, `bryn`). Create:

```
references/characters/<slug>/
  _source.<ext>     (the internet source image — stays OUT of git)
  _provenance.md    (committed — same convention as references/locations/*/_provenance.md)
```

`_provenance.md` template:

```markdown
# <Character> — source provenance
- source_url: <url>
- source_type: official_art | game_screenshot | show_capture | fan_art
- retrieved: YYYY-MM-DD
- license_note: reference for fan-production / non-commercial creative work
- converted: YYYY-MM-DD via <backend + the model id the job actually returned>
- attempts: N (which output was selected, why)
```

(The parked branch used `source-metadata.json`; main's living convention for
ref provenance is `_provenance.md` — use that.)

### Step 3 — run the 3D conversion

Backend, model, count, resolution: per **CLAUDE.md § Generation defaults** —
Higgsfield direct via MCP, the current fast default model, count 1,
resolution 1k. Do NOT hardcode model ids into prompts or notes from memory;
the catalog shifts (this skill's branch version defaulted to
`nano_banana_pro` and carried a "flash retired" note — both stale within
weeks). Verify the `model` field the job actually returns and record it in
`_provenance.md`.

Attach the source image as the reference. Prompt template (adjust per
character — the prompt carries CONVERSION instructions, not an appearance
wall; the source image carries the appearance):

> Render the attached character as a photoreal 3D model in a clean neutral
> A-pose, three-quarter view, plain studio background, soft directional
> studio lighting. Preserve the character's face, hair, costume, and
> proportions exactly as shown in the reference. The output should look like
> a high-quality DAZ Studio Iray render — ray-traced subsurface scattering on
> skin, physically-accurate fabric, 8K texture detail. Full body in frame,
> head to feet. No environment details; just the character against the plain
> background.

If the source is anime/cartoon-styled, add:

> Translate the character from 2D/anime styling to photoreal 3D — the
> identity (face, hair, costume, colors) stays the same but the rendering
> style becomes photoreal CGI, not illustrated.

Two current rules bite hard on 2D-source conversions — add both explicitly
when converting stylized sources:

- **Reads 25+** (`feedback_characters_read_25_plus`): the converted character
  must read as a clear adult, 25 or older — big-eye / cute-seed proportions
  inherited from anime sources are a known failure. Add "adult in their late
  20s, mature facial structure" when the source skews young.
- **Coverage** (CLAUDE.md `always_clothed` default): coverage of
  breasts/buttocks/groin is preserved; skimpy source costumes render with
  coverage intact.

### Step 4 — review and save

Display the result. Checklist:

- Face matches the source
- Hair matches (style, color, length)
- Costume matches (garment, colors, accessories)
- Proportions reasonable (baseline athletic is fine — body-tier refs refine
  proportions later)
- Reads 25+
- Coverage intact
- Style is photoreal CGI, not 2D (per `feedback_comic_style_3d`)

Iteration is normal — 3-5 passes to lock a ref, per
`feedback_multipass_image_generation`. Content-filter blocks: per
`feedback_content_filter_playbook`, retry the same prompt 4× before
reframing — filter variance often clears on retry.

On approval, save as `references/characters/<slug>/internet-3d-base.png` and
fill in the conversion lines of `_provenance.md`.

### Step 5 — downstream wiring

- Generate the character's face card / body-tier refs / sheets WITH this ref
  attached (see "Where it sits in the pipeline").
- In project context: add the ref to the project's staging so
  `qa/compose.py` can require and attach it.
- The canonical filename matters: the parked refactor branch's rule registry
  auto-attaches exactly `references/characters/<slug>/internet-3d-base.png`
  (`rules/attach/internet_3d_base.py`). Keep the name so that wiring works
  as-is if the registry restructure ever lands.

## Anti-patterns

- **Don't paraphrase the character into prose.** The skill exists so
  appearance lives in an IMAGE (L10). The prompt describes the conversion,
  never the character.
- **Don't generate from scratch.** No source image → this is not the skill;
  originate the character via the `comic-production` face-card flow instead.
- **Don't skip provenance.** `_provenance.md` is the committed record — IP
  attribution plus the ability to re-find the source later.
- **Don't fan out variants.** One paid generation; iterate by re-prompting,
  not count>1. (The bakeoff-lane count exception is for panel beats, not
  base refs.)
- **Don't save to a non-canonical path.** `internet-3d-base.png` under
  `references/characters/<slug>/` is the contract downstream wiring keys on.
