---
name: stylization
description: Pass generated comic panels through an image-to-image stylization model to convert photoreal renders into a target comic art style — bold inked outlines, cel-shading, target line weight, and color palette — while preserving character identity, pose, wardrobe, and composition from the source panel. Use when the generation model produces photoreal output but the project needs a comic art style; when style-lock's prompt prefix didn't fully push the base model into the target style; when panels read as photographs rather than illustrations; or when the chapter mixes models and you need them to match. Trigger phrases include "stylize the panels", "convert to comic art", "make it look like a comic", "fix photoreal style", "stylization pass", "re-style the chapter".
---

# Stylization

Optional stage between generation and continuity-check. Takes panels from `pages/panels/<panel_id>.png` and runs each through an image-to-image stylization pass — same composition and identity, different art style. Writes back to the same path; the original is preserved at `pages/panels/_pre-style/<panel_id>.png`.

Many character-consistent generators (Higgsfield's `soul_v2`, for example) are tuned for photorealism. The style-lock prompt prefix asks for a comic look, but the model's underlying bias dominates. Stylization is the fix when the gap between what `style.md` describes and what the base model produces is too wide to close at generation time.

## When this skill is the right tool

- Panels come out photoreal but the project is supposed to be a comic
- Style drifted across the chapter; you want to re-stylize after the fact
- Mixing models in a chapter (some photoreal, some comic) and you need them to match
- "Convert these panels to inked comic style"

If the panels are already in the target style, skip this — running stylization on already-styled panels burns credits and risks identity drift. If only one or two panels drifted, regenerate those instead of running a chapter-wide pass.

## Inputs

- `pages/panels/<panel_id>.png` — generated panels (assumed approved at the per-panel quality level)
- `style.md` — to read the target style description
- (optional) `references/_style/*.{jpg,png}` — style reference images for image-to-image conditioning
- Higgsfield MCP for the stylization model (default: `nano_banana_2` for image-to-image)

## Workflow

### 1. Confirm need

Sample 2–3 panels via `Read`. If they already match the target style described in `style.md`, abort and tell the user: *"These panels look like they're already in the target style. Stylization would re-process for no gain. Skip?"*

### 2. Pick the stylization model

Use `hf__models_explore` with `action=recommend query="image-to-image stylization comic art"` to get a model that:

- Accepts an input image as `medias[role=image]`
- Honors stylization prompts well
- Produces output in the target medium

Default fallback: `nano_banana_2`. Lock the choice in `style.md` under a new `## Stylization model` section so future panels go through the same pipeline.

### 3. Build the stylization prompt

Pull from `style.md`'s prefix/suffix and rewrite as a stylization instruction:

> Convert this photograph into <target style — verbatim from style.md>. Preserve the subject's pose, identity, wardrobe colors, composition, framing, and lighting direction exactly. Apply: <line weight description>, <coloring approach>, <rendering approach>, <era/genre cue>. Do not change which character is in the panel. Do not add or remove any objects.

Mention every characteristic from `style.md` that the original generation missed — that's the whole point of running this stage.

### 4. Stylize each panel in parallel

For every `<panel_id>.png` in the panels folder:

1. `media_upload` the panel image (with `content_type=image/png`)
2. `media_confirm` to commit
3. `generate_image` with the stylization model, passing the panel as a `medias[]` reference (role: `image`) and the stylization prompt
4. Capture the new job_id

Watch the Higgsfield concurrent-job rate limit (typically 8). Batch in groups, poll between batches. After all jobs are queued, wait, then `show_generations` and download URLs.

### 5. Swap in place, preserving the originals

Move pre-stylization panels to `pages/panels/_pre-style/<panel_id>.png` (preserve, never delete). Save stylized versions as `pages/panels/<panel_id>.png`.

Update `pages/panels/_index.md` (or create) with a `styled` flag per panel so re-runs know what's already been processed:

```
| panel_id | styled | model        | timestamp           |
|----------|--------|--------------|---------------------|
| p01-01   | yes    | nano_banana_2| 2026-05-06T14:32:00 |
```

### 6. Sample-check

Read 3 stylized panels. Verify:

- **Character identity preserved** — same face, body type, wardrobe colors, hair
- **Style now matches style.md** — line weight, palette, rendering all look correct
- **No major composition drift** — no cropping, pose, or prop loss
- **Wardrobe color held** — stylization shouldn't flip blue to yellow under colored lighting

If identity drifted, the stylization model went too aggressive. Options: back off the prompt strength (lower stylization weight if model exposes one), try a different model, or accept the original photoreal panel for that one panel.

## Hard rules

- **Always preserve the originals.** Move to `_pre-style/`, never overwrite. Stylization can fail; you need to fall back without re-generating.
- **Don't stylize approved panels twice.** Track which panels have been through the stage in the `_index.md` styled flag.
- **Don't change composition or wardrobe colors.** The stylization prompt explicitly says "preserve" — but image-to-image models still drift if the prompt asks for changes. Keep the prompt focused on visual *style*, not visual *content*.
- **Verify identity after stylization.** A stylized panel that no longer reads as the same character is unusable. Regenerate, or fall back to the pre-style original.
- **Skip when not needed.** If panels already match style.md, running this stage costs credits for no gain.

## Common asks

- **"Stylize just the splash"** — stylize one panel only; useful as a test before full-chapter pass
- **"Re-stylize the second half of the chapter"** — file-name range filter (e.g. `p04-*` and later)
- **"Make pages 5–6 match pages 1–4"** — load page 1's first panel as the style reference; stylize 5–6 against it
- **"Undo the stylization"** — copy `_pre-style/*` back over `panels/*`; clear the styled flag

## Hand-off

After stylization:

1. Re-run `continuity-check` — the new style may surface different drift (wardrobe colors are especially fragile across image-to-image)
2. Then `page-composer` for assembly

If continuity-check flags issues introduced by stylization, fall back to the originals for those specific panels rather than re-running the full pass.
