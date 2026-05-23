# Multi-Pass Build-Up Workflow

The workflow under test in this experiment. It is *the experiment's invention* — there is no canonical decomposition strategy in the pipeline today, every panel is one-shot.

The user's articulated intuition (Discord, May 2026):
> "Sometimes in order to make a good image, you have to pre-render a few images before because it's just way too much to ask in one shot."
>
> "I think the way to fix it would be to take the first image which is those three girls in the front and prompt it to modify the camera angle... The next thing would do take the scene I have and prompt the same thing with the camera angle, and generate that image. The last thing would be to take those two in the back and drop them in, when I have the aforementioned part completed."

That is — render each ingredient in its own simpler prompt (where the model has spare capacity), then compose the ingredients together in a final pass where the model's job is reduced to "place these elements according to this layout."

## Recipe

### Step 1 — Decompose the panel

Read the shotlist entry. Identify the ingredient set:

- **Foreground character(s):** the cast member(s) the camera is closest to / framed around
- **Background character(s) or BG limb(s):** any cast members further back, or partial body elements (e.g. mirroring arm in BG)
- **Scene plate:** the location with environmental elements but no cast
- **Prop with binding:** any object that needs to be in a specific character's hand
- **SFX / lettering:** rendered separately, composited last (out of scope for this experiment — handled by the lettering pass)

The decomposition isn't fixed — pick what the panel needs. For a 1-character ECU there may be only 1-2 ingredients (subject + scene plate). For a 4-character group shot there could be 5+.

### Step 2 — Generate ingredients

For each ingredient:

1. Open Flow, attach the canonical reference set for that ingredient (e.g. for a character ingredient: the face card + tier body sheet)
2. Prompt the ingredient at full quality, with the **camera angle and lighting of the final panel** specified
3. Pick the strongest variant from the 4-up
4. Save as a labeled ingredient reference (e.g. `p05-02_ingredient-mundy.png`)

The reason for "camera angle of the final panel" — the ingredients need to LOOK like they came from the final composition's camera, otherwise the composite pass has to do geometry-warping which it's bad at. If the final is low-angle-back, the Mundy ingredient is also low-angle-back.

### Step 3 — Composite pass

1. Open a new Flow project (or new prompt slot in the same one)
2. Attach all ingredient images as references
3. Prompt the final panel with the composition instruction: "place [INGREDIENT-A] in foreground at [POSITION], [INGREDIENT-B] in [POSITION] with [LIGHTING]" — NOT a full descriptive prompt. The descriptions go in the ingredients.
4. Pick the strongest variant of the composite

The composite prompt is intentionally lean. The model isn't asked to invent characters or locations — those are pre-baked in the ingredient refs. It just has to do compositing.

## Why this might work (theory)

A one-shot prompt asks the model to satisfy many constraints simultaneously: render character A with face fidelity, render character B with face fidelity, render the location, render the lighting, render the props, render the action, frame the camera. When constraints conflict (which is common in complex composites), something gets dropped — the audit log shows this clearly (cast-count violations, identity confusion, missing BG arms, etc.).

Multi-pass narrows each generation's job to one or two constraints at a time. The composite pass still has to do *something* hard — integrating the ingredients with consistent lighting — but it isn't *also* fighting face fidelity and prop binding and camera framing.

## Why this might fail (counter-theory)

1. **The composite pass might be its own one-shot.** If the model can't actually composite multiple refs cleanly — if it ignores the layout instruction and just re-imagines the scene — then we've replaced one one-shot with another one-shot plus three extra gens of overhead.
2. **Ingredient style drift.** If ingredient A is rendered with slightly different lighting from ingredient B, the composite shows visible seams.
3. **Composite drops cast-count anyway.** If the composite pass collapses two character refs into one composite character, we're back to the original failure mode.
4. **Cost.** 4-5× the gens per panel. Not a quality argument but a budget one — only worth it if quality clearly improves.

The A/B is designed to detect (1) and (3) — if multi-pass output is worse than or equal to one-shot output on the same panel, that's the answer.

## Decomposition strategies tried

For this experiment we'll test the simplest decomposition strategy ("character ingredients + scene plate + composite") on all test panels. If it works, future experiments can test alternative decompositions (e.g. dialogue-aware decomposition for panels with speech bubbles, or layered-FMG decomposition for transformation sequences).
