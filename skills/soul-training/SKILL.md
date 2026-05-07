---
name: soul-training
description: Train Higgsfield Souls for comic characters from gathered references — validate angle and expression coverage, curate the training set, launch Soul training, monitor status, run a smoke test, and register Soul IDs back into the shotlist. Use when the user wants to train a Soul, build a Soul training set, register a character with the comic generator, assign Soul IDs to the cast, or check coverage of references before training. Trigger phrases include "train a Soul", "soul-train [character]", "register character", "assemble training images", "soul ID for X", "train the cast", "build the training set".
---

# Soul Training

Turn a folder of gathered references into a trained Higgsfield Soul that the panel generator can call by ID. One Soul per character (per outfit, if outfits change drastically). Runs after `reference-gathering` and before any panel generation.

## When this skill is the right tool

- "Train a Soul for Lara"
- "Register all the chapter-3 characters"
- "Build training sets for the cast"
- "Soul IDs for the shotlist cast"

If the references don't exist yet, hand off to `reference-gathering` first. If the user wants to *generate panels* using existing Souls, that's the comic-production / generation workflow, not this skill.

## Inputs

- `references/<character-slug>/` — built by `reference-gathering`
- `shotlist.json` — to know which characters need Souls (any cast entry with `soul_id: null`)
- Higgsfield MCP must be connected. Tools below are abbreviated `hf__*` (the actual prefix is the Higgsfield server's `mcp__<server-id>__*`).

## Required coverage

A Soul trained on a one-angle pool fails on the missing angles. Before training, verify the reference folder covers:

| Axis | Minimum | Strong |
|---|---|---|
| Angle | front + 3/4 | front + 3/4 + profile + back |
| Expression | neutral + 1 active | neutral + smile + action/intense |
| Framing | head-and-shoulders + full body | + medium shot + close-up |
| Wardrobe | the canonical outfit | canonical + 1 variant |
| Lighting | varied (not all night, not all flash) | natural daylight as majority |

**Run a coverage check** by `Read`-ing every JPG in the folder and tagging it against this matrix. Output a one-table report. If a row is empty under "Minimum", send the user back to `reference-gathering` with the specific gap — don't train on a thin set.

## Workflow

### 1. Pick characters

If the user named one ("train Lara"), do that. Otherwise read `shotlist.json` and process every cast entry where `soul_id == null`.

### 2. Coverage check per character

For each candidate image, `Read` it and tag:

```
references/lara/
  lara-01.jpg  → front, neutral, head-shoulders, daylight, canonical
  lara-02.jpg  → 3/4, smile, full-body, daylight, canonical
  lara-03.jpg  → profile, intense, medium, dusk, canonical
  ...
```

Build the coverage table. If any **minimum** row is empty, stop and report. Don't compensate by reusing one image's twin frame — Souls overfit on near-duplicates.

### 3. Curate the training set

Pick **8–15 images**. Bias toward:

- Clean backgrounds — the Soul learns the subject, not the environment
- Frontal lighting; reject heavy shadow or strong color cast
- Uniform wardrobe (one outfit unless training a multi-look Soul on purpose)
- Sharp focus, no motion blur, no overlay text
- One image per angle/expression cell — duplicates skew the Soul

Write the curated list to `references/<slug>/_training-set.md` so the choice is auditable. If you reject a candidate, note why ("rejected: heavy backlight; profile is silhouetted").

### 4. Upload and train

Use the Higgsfield MCP. Sequence:

1. `hf__list_workspaces` then `hf__select_workspace` to pick the project's workspace. Wrong workspace = Soul invisible to the generator.
2. `hf__media_upload` for each curated image; capture the returned media UUIDs.
3. `hf__media_confirm` to commit the uploads.
4. `hf__soul_train_wizard` with the media UUIDs and the character slug as the Soul name. Use the wizard rather than `soul_train` directly — it handles defaults the bare endpoint doesn't.
5. Capture the returned `soul_id`.

### 5. Monitor

Poll `hf__soul_status` until the Soul reports ready. Don't sleep-loop tightly — Souls usually finish in 5–20 minutes. Use `ScheduleWakeup` at 600–900 second intervals to check back without burning the prompt cache.

### 6. Smoke test

Generate one image with `hf__generate_image` using the new Soul ID and a known prompt:

> `<character name>, head and shoulders portrait, neutral expression, daylight, plain background`

`Read` the result. If the face doesn't clearly match the references, the training is bad. Most often the curation included off-target frames or near-duplicates. Re-curate (don't just retrain on the same set) and re-train. **Don't ship a bad Soul** — every panel using it inherits the error.

### 7. Register

Update `shotlist.json` in place: write the new `soul_id` into the matching `cast[].soul_id`. Append a one-line entry to `cast.md` (create if missing):

```
- lara — soul_id=hf_soul_abc123 — trained 2026-05-04 — refs: references/lara/ (12 images)
```

## Hard rules

- **Never train on uncurated references.** A 30-image dump always contains rejects; the Soul will pick up the worst patterns.
- **One Soul per outfit when outfits change drastically.** Training one Soul on "leather jacket" and "ballroom gown" produces a confused Soul that swaps wardrobe randomly. Train two and switch by panel.
- **Don't proceed past a failed smoke test.** A bad Soul propagates errors through every panel. Cheaper to retrain now than to regenerate the whole chapter.
- **Workspace context is load-bearing.** Souls are scoped per workspace. Always confirm workspace before upload.
- **Don't share Soul IDs across projects** without verifying the workspace matches.

## Common asks

- "Train all the cast" — loop the workflow per character; parallelize uploads where the MCP allows, but smoke-test each Soul before moving on.
- "Re-train Lara, the face drifted" — re-curate (the cause is almost always coverage, not training params), re-train, replace `soul_id` in `shotlist.json`. Note the old ID in the cast.md history line.
- "Just check coverage, don't train yet" — step 2 only; output the gap report.
- "Train a style Soul" — training Souls on style refs (not characters) is a `style-lock` concern, not this skill.

## Hand-off

After this skill, `shotlist.json` has `soul_id` set for every cast member. Generation can proceed. If `style-lock` hasn't run yet, do that next — generating without a style lock burns budget on panels that will need to be redone.
