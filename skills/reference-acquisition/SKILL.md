---
name: reference-acquisition
description: Convert an internet-sourced character image into a photoreal 3D base reference. Use when bootstrapping a NEW character — start from official art, a game screenshot, a show capture, or fan reference and produce a clean 3D-rendered anchor at references/characters/<slug>/internet-3d-base.png that all subsequent panel generation matches against. Trigger phrases include "bootstrap a new character", "convert this image to a 3D ref", "make a base ref from this internet image", "I have an internet image of X — make me a starter ref", "set up a new character from this screenshot".
---

# reference-acquisition

Converts an internet character image into a photoreal 3D base
reference. The output is the `internet-3d-base.png` ref that
`attach/internet_3d_base.py` picks up automatically.

## Why this skill exists

In the user's canonical workflow, every character starts the same way:

1. **Find a good internet image.** Official art, a game screenshot, a
   show capture, fan reference. The source needs to depict the
   character clearly — full body or 3/4 body, neutral pose, well-lit,
   high resolution.
2. **Convert it to a 3D photoreal render.** Feed the source image to
   Higgsfield Nano Banana 2 or GPT Image 2 with a tightly-scoped
   "render this character as a photoreal 3D model, A-pose, plain
   background" prompt. The model preserves the character's identity
   but strips the source image's lighting/composition baggage.
3. **Save the output at the canonical path.** The base ref lives at
   `references/characters/<slug>/internet-3d-base.png` so the comic
   pipeline's `attach/internet_3d_base.py` rule auto-attaches it for
   every panel the character is in.

This ref is the COMPLETE canonical character — face + body + costume
+ proportions, in one image. It's the strongest single-image anchor
for downstream generation. Paired with the face card (close-up of the
face only) and the body-tier lineup (proportion truth across tiers),
it gives the model unambiguous identity to match.

## When to invoke

- The user has an internet image and wants to set up a new character.
- A `should_apply` check on `attach/internet_3d_base.py` returned
  MISSING for a character — the pipeline is asking for this ref.
- The user says any of: "make me a base ref", "convert this to 3D",
  "bootstrap from this screenshot", "I have official art of X, set up
  the character".

## Workflow

### Step 1 — get the source image

The user provides:
- A URL to an internet image, OR
- A local path to a downloaded image, OR
- An uploaded image in the chat.

Save the source to `references/characters/<slug>/_source.<ext>` so
provenance is preserved.

If the user provides only a URL, download it via `curl -O` or
similar. Verify the saved file is a real image (non-zero bytes, valid
header). If it's not, stop and ask the user for an alternate source.

### Step 2 — pick the slug + create the folder

The slug is the character's machine-friendly name: lowercase,
hyphenated, no spaces. Examples: `chun-li`, `yuna-hoshino`,
`april-oneill`, `bryn`, `emma-frost`.

Create:

```
references/characters/<slug>/
  _source.<ext>         (the downloaded internet image)
  source-metadata.json  (provenance — URL, retrieval date, source notes)
```

### Step 3 — run the 3D conversion via Higgsfield

Per `feedback_higgsfield_*` memories:
- Default model: `nano_banana_pro` (flash retired 2026-05-21)
- Default resolution: 1k unless user specifies otherwise
- Default count: 1 (paid platform; don't burn 4 variants)

Submit a `generate_image` call to the Higgsfield MCP with the source
image attached as a reference. Prompt template (adjust per character):

> Render the attached character as a photoreal 3D model in a clean
> neutral A-pose, three-quarter view, plain studio background, soft
> directional studio lighting. Preserve the character's face, hair,
> costume, and proportions exactly as shown in the reference. The
> output should look like a high-quality DAZ Studio Iray render —
> ray-traced subsurface scattering on skin, physically-accurate fabric,
> 8K texture detail. Full body in frame, head to feet. No environment
> details; just the character against the plain background.

If the reference image is anime/cartoon-styled, add:
> Translate the character from 2D/anime styling to photoreal 3D — the
> identity (face, hair, costume, colors) stays the same but the
> rendering style becomes photoreal CGI, not illustrated.

### Step 4 — review and save

Display the result to the user. Confirm it captures the character:
- Face matches the source
- Hair matches (style, color, length)
- Costume matches (garment, colors, accessories)
- Proportions are reasonable (the body-tier lineup later refines this;
  for the base ref, a baseline athletic build is fine)

If the user approves, save as:

```
references/characters/<slug>/internet-3d-base.png
```

If the user wants iteration, retry with prompt tweaks (more weight on
problematic attributes, explicit negation of drift). Per
`feedback_multipass_image_generation`, multi-pass regen is normal —
3-5 attempts to lock the ref is fine and expected.

If the source image is NSFW or content-policy-blocked, per
`feedback_nsfw_retry_policy` retry the same prompt 4 times before
reframing — filter variance often clears on retry.

### Step 5 — downstream integration

Once the base ref is saved at the canonical path, the comic pipeline
picks it up automatically:

- `attach/internet_3d_base.py` returns `{"kind": "internet_3d_base",
  "path": "references/characters/<slug>/internet-3d-base.png"}` for
  every panel the character is in.
- `attach/face_card.py` continues to look for `face-card.png` (a
  separate close-up of the face). If absent, that's a soft warning;
  generate one separately via the existing `comic-production`
  workflow's face-card sub-step.

## Source-metadata schema

`source-metadata.json` captures provenance:

```json
{
  "character_slug": "yuna-hoshino",
  "source_url": "https://example.com/yuna-art.jpg",
  "source_type": "official_art | game_screenshot | show_capture | fan_art",
  "retrieved_at": "2026-05-23",
  "license_note": "Reference for fan-production / non-commercial creative work.",
  "rendered_at": "2026-05-23",
  "rendered_via": "higgsfield nano_banana_pro",
  "rendered_count": 1,
  "rendered_selection": "the single output (count=1) selected by user"
}
```

## Anti-patterns

- **Don't paraphrase the character into prose.** This skill exists so
  appearance lives in an IMAGE, not in prompt text. Per L10
  ("references are the truth"), the more the appearance ends up in
  prose, the less the model trusts the ref.
- **Don't generate the ref from scratch.** The whole point is to
  anchor against an existing internet image. If there's no source, the
  character should be generated via the `comic-production` skill's
  face-card flow instead.
- **Don't skip provenance.** `source-metadata.json` matters for IP
  attribution and for the user to re-find the source later.
- **Don't burn 4 Higgsfield variants.** The base ref is one image; 1
  generation is enough. If you need iteration, regenerate with a
  better prompt, don't fan out variants.
- **Don't save to a non-canonical path.** The `internet-3d-base.png`
  filename and the `references/characters/<slug>/` location are how
  `attach/internet_3d_base.py` finds the file. If you save elsewhere,
  downstream auto-attachment breaks.
