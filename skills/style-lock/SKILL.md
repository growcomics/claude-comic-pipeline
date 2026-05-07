---
name: style-lock
description: Lock a single visual style across an entire comic project — distill style references into a mandatory prompt prefix and suffix, pick the model and parameters, define the color palette and line weight, and write a project-level style guide that every generated panel must follow. Use when the user wants a consistent look across pages, define the style of a comic, prevent style drift between panels, build a style guide, lock model parameters, or pick a model for the project. Trigger phrases include "lock the style", "style guide for the comic", "consistent look", "style across panels", "no style drift", "pick the model", "match the style of X".
---

# Style Lock

Lock a project's visual style up front and enforce it on every panel prompt. Without this, generated panels drift across pages — different line weights, different palettes, different rendering — even when the same Soul is used. `style-lock` produces a `style.md` that the generator and `page-composer` both read.

## When this skill is the right tool

- Start of a new comic project, before any panels are generated
- "Make sure all panels look the same"
- "Lock the style"
- "Match the style of [reference comic / artist]"
- Mid-project rescue: pages 1–4 look fine, pages 5–8 drifted

If a `style.md` already exists, this skill updates it; it doesn't overwrite without explicit confirmation. If only one or two panels drifted, that's a generation-prompt bug, not a style-lock issue — fix the prompt, don't relock.

## Output: `style.md` at project root

```markdown
# Style Lock — <project>

Locked <date>. Every panel prompt must include the prefix and suffix below verbatim.

## Model
- Name: <higgsfield-model-id>
- CFG / guidance: 6.5
- Sampler: <sampler>
- Seed strategy: per-panel deterministic seed = hash(panel_id)
- Resolution: 1536×1024 (landscape standard) | 1024×1536 (tall) | 2048×2048 (splash)

## Mandatory prompt prefix
> dynamic comic panel, heavy 2pt outer line with medium interior detail, cel-shaded with hard 35° shadows, modern indie comic aesthetic

## Mandatory prompt suffix
> directional key light from upper-left, no rim light, 35mm lens equivalent, no painterly softness

## Mandatory negative prompt
> photoreal skin texture, instagram filter, watermark, text artifacts, deformed hands, extra fingers, cropped face, 3D render, DAZ artifacts, stock-flash lighting

## Color palette
- Hex: #1a1a2e, #f5deb3, #c44536, #2e8b57, #f0f0f0
- Rule: max 4 dominant hues per panel; cool palette for night scenes, warm for action

## Line weight
- Outer silhouette: heavy (2pt equivalent)
- Interior detail: medium (1pt)
- Background: light (0.5pt)

## Rendering
- Cel-shaded, minimal gradients
- Hard shadows at 35° from upper-left
- No painterly softness, no airbrush

## Lettering hints (read by page-composer)
- Font: WildWords-Bold (./assets/fonts/WildWords-Bold.ttf)
- Balloon stroke: 2px black, white fill
- Caption: yellow tint #FFF4B8
- SFX: black with 2px red drop shadow

## Banned
- Photoreal skin pores
- 3D render look (DAZ artifacts)
- Stock-art front-flash lighting
- Anime-style giant eyes (unless this is an anime project)

## Sample shot
- Reference panel: pages/_style-sample.png
- Re-test prompt: "<character> standing in <location>, neutral pose, full prefix and suffix"
- Drift check: re-run weekly or every 10 panels; compare to baseline
```

## Workflow

### 1. Gather style refs

If style refs aren't already in `references/_style/`, delegate to `reference-gathering`: *"mood-board, 12 images, [genre + era + artist] aesthetic"*. Don't proceed without 5+ style refs — single-image style anchors don't generalize.

### 2. Distill the style

Read all style refs. Write a 5–10 attribute distillation. Be **specific**. Vague descriptions ("modern", "dynamic") produce drift; specific ones ("heavy 2pt outer line, no rim light, 35° hard shadows from upper-left") hold.

Attributes to capture:

- Line weight (outer vs interior, in approximate point sizes)
- Color approach (palette breadth, saturation, dominant hues)
- Lighting (key light direction, hardness, presence/absence of rim)
- Rendering (cel-shade / painterly / inked / screentone / mixed)
- Era/genre cue (90s manga, 70s underground, modern indie, retro Eurocomic, etc.)
- Forbidden traits (photoreal, 3D, stock-flash, anime-eyes if not anime)

### 3. Pick the model

Use `hf__models_explore` to see available models. Choose by:

- Genre fit — some models are tuned for stylized output, others for photoreal; pick the one whose default look is closest to your distillation
- Aspect ratio support — must handle 1.5:1 landscape for standard panels
- Soul compatibility — the model must accept the Soul IDs you trained (or will train)

Lock the model name and parameters in `style.md`. **Don't change the model mid-project** — model swaps cause maximum drift.

### 4. Test on a known shot

Pick a representative panel from `shotlist.json` (a character + a location, preferably with a Soul already trained). Generate it with full prefix + suffix + negative. `Read` the result.

- If it matches the style refs and looks like the character: lock the parameters; save as `pages/_style-sample.png` for later drift checks.
- If it drifts: tighten the prefix/suffix wording, retry. Most drift comes from vague style descriptors that the model under-weights. Strong cues ("heavy 2pt outer line") survive better than weak ones ("bold lines").

### 5. Wire into generation

Generation must:

1. Read `style.md`
2. Prepend the prefix to every panel prompt verbatim
3. Append the suffix verbatim
4. Pass the negative prompt
5. Use the locked model + parameters

Document this contract in `style.md` so it survives handoffs to other workflows or re-runs.

## Drift detection

Re-run the sample shot every ~10 panels generated, or any time the user notices "this page looks off". Compare to `_style-sample.png`. If the new render diverges in line weight, palette, or lighting:

- **Sample also drifted** → the model was bumped (provider change), or parameters changed. Investigate root cause.
- **Sample is fine, only page 7 drifted** → the prompt skipped the prefix/suffix, or the panel-prompt builder has a bug.

Fix the root cause; don't paper over by tweaking prompts panel-by-panel.

## Hard rules

- **Lock once, change deliberately.** Mid-project parameter changes invalidate every previous panel's continuity.
- **Prefix and suffix go on every panel — no exceptions.** "Quick test" panels still need them or they'll look wrong sitting next to locked panels.
- **No "match this random image" without distillation.** Pinning aesthetic to a single image works for one panel, not 50.
- **The negative prompt is load-bearing.** Don't drop it for terseness — banning photoreal skin and stock-flash is what keeps the generator from defaulting to ad-stock aesthetics.
- **One style.md per chapter at most.** If chapter 4 needs a different style for a flashback, write `style-flashback.md` and tag those panels — don't rewrite `style.md`.

## Common asks

- "Match [artist]'s style" — gather 8–12 of that artist's panels via `reference-gathering`, distill, test. Note: if the artist is alive and copyrighted, the user is responsible for the licensing call; flag it.
- "Different style for the flashback pages" — write `style-flashback.md` and add `"style": "flashback"` to those panels in `shotlist.json`.
- "Style drifted on page 7" — run the sample-shot drift check first to localize the problem (model vs. prompt vs. parameters).
- "I don't have refs, just a vibe" — push back; gather 5+ refs first. A vibe-only style spec drifts within 3 panels.

## Hand-off

After `style.md` is locked, generation can begin. `page-composer` will also read this file for font/balloon/caption/SFX styling — those keys live under "Lettering hints".
