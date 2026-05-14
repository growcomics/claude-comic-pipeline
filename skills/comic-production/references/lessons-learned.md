# Lessons Learned — Comic Production

Hard-won lessons from production. Each lesson is a real failure mode observed in output, the root cause, and the fix. Read this when something looks wrong, before you assume the prompt was the problem.

---

## L1 — Progressive sequences must be chained, never parallelized

**Symptom**: In a transformation, growth, dressing, or charge-up sequence, state regresses panel-to-panel:
- A qipao that was torn at the shoulder seam in panel T5 looks intact again in T6.
- A body at muscle size 5 in panel T4 shrinks back toward size 4 in T5.
- Hair that came loose from a bun in T3 re-pins itself in T4.
- Energy aura intensity flickers up and down instead of building.

**Root cause**: The model has no memory between calls. If you submit T1…TN in parallel — even with rich text descriptions like *"more torn than the previous panel"* or *"size 5 transitioning to 5.5"* — the model cannot see what "the previous panel" looks like. Every panel re-derives state from the baseline character ref + text alone. Text-described *progress* is interpreted independently each call, and you get non-monotonic output.

**Fix**: Generate progressive sequences **sequentially**. Each panel must take the immediately previous panel's job ID as a reference image (`medias[].value` = prior `job_id`, role `image`). Always pair it with the canonical face/portrait ref so the face doesn't drift across the chain.

```
T1: refs = [base_body, portrait, gauntlet]
T2: refs = [T1_job_id, portrait, gauntlet]
T3: refs = [T2_job_id, portrait]
…
T10: refs = [T9_job_id, portrait, bison_ref]
```

Wait for each job to complete before submitting the next. There is no parallel shortcut for chained sequences — accept the wall-clock time.

**Why pair the prior-panel ref with the portrait ref**: the prior panel carries body + clothing + pose state, but its face is usually mid-shout, mid-impact, or eyes-closed. Chaining face state across many panels accumulates drift (the model averages successive distorted faces and the character stops looking like themselves). The canonical portrait anchors the face every step.

**When this rule applies**:
- Transformation sequences (FMG, transformation arcs, alternate forms)
- Putting on or taking off a garment across multiple panels
- Charging up an attack with VFX intensity progression
- Taking damage across a fight (clothing tears, blood, bruising)
- Weather/lighting changes across a montage (rain begins → storm → flood)
- Any case where panel N+1's state depends on panel N's state, and parallel generation would break continuity

**When this rule does NOT apply**:
- Independent panels in the same scene that don't share evolving state (separate dialogue beats, reverse-angle ECUs of the same exchange) — these can parallelize.
- Establishing shots, environment refs, character refs — independent by definition.

**Worked example — Chun-Li transformation T1→T10 (correct)**:
```python
t1 = generate(prompt=T1_prompt, medias=[base_body, portrait, gauntlet])
wait(t1)
t2 = generate(prompt=T2_prompt, medias=[t1.id, portrait, gauntlet])
wait(t2)
t3 = generate(prompt=T3_prompt, medias=[t2.id, portrait])
# … and so on
```

**The wrong way (causes the symptoms above)**:
```python
# DON'T do this for a transformation arc
results = parallel([
    generate(prompt=T1_prompt, medias=[base_body, portrait]),
    generate(prompt=T2_prompt, medias=[base_body, portrait]),  # no T1 ref
    generate(prompt=T3_prompt, medias=[base_body, portrait]),  # no T2 ref
    # …
])
```

---

## L1.5 — Chain view-aware, not blindly to N−1

**Symptom** (the second-order failure after L1 is fixed): chaining is on, panels are generated sequentially, but specific transitions in the sequence still produce visibly worse output than their neighbors. Common cases:
- A front-view panel following a back-view panel: the front face/body looks subtly off-axis, like the model is fighting between "show the front" and "match the silhouette in the reference"
- A face ECU following a panel where the face was off-camera: facial features come out homogenized or drift away from the canonical look
- A wide body shot following an arm ECU: the body proportions feel reconstructed rather than continuous, because the prior reference only showed an arm

**Root cause**: The prior-panel ref carries two distinct things — *state* (body size, clothing damage, hair, aura) and *view* (camera angle, framing, body orientation). State is durable and what you want to preserve. View is situational. If the new panel's view doesn't match the prior, the model still tries to honor the silhouette of the reference, which actively interferes with the target composition.

**Fix**: Don't always chain to T_{N−1}. Walk backwards through the prior panels and pick the most recent one whose *view category* is compatible with the new panel. That becomes the state anchor. If no compatible prior exists, fall back to the canonical character ref that matches the target view (e.g., back ref for a back panel) + a verbal state carry-forward in the prompt.

**View categories**: `front-full | 3q-full | back-full | side-full | ecu-face | ecu-region | low-angle-front | low-angle-back | high-angle | square-impact | wide-establish | splash`

**Compatibility table** (state anchor for a target view can come from any of these):

| Target | Compatible priors |
|---|---|
| front-full, 3q-full | front-full, 3q-full, low-angle-front, wide-establish (front), splash (front) |
| back-full | back-full, low-angle-back |
| ecu-face | another ecu-face, or any panel where the face was clearly visible |
| ecu-region (arm/hand/etc.) | another panel where that region was prominent and unobscured |
| wide-establish, splash | another wide/splash with the same body orientation |

**Worked example from production** (Chun-Li T1–T10 transformation, naive chain → view-aware chain):

| # | View | Naive (wrong) | View-aware (correct) |
|---|---|---|---|
| T1 | front-full | base refs | base refs |
| T2 | ecu-region (arm) | T1 ✓ | T1 ✓ |
| T3 | front-full | T2 ✗ (arm only) | **T1** + portrait + verbal state from T2 |
| T4 | front-full | T3 ✓ | T3 ✓ |
| T5 | front-full | T4 ✓ | T4 ✓ |
| T6 | low-angle-front | T5 ✓ | T5 ✓ |
| T7 | back-full | T6 ✗ (front view) | **canonical back ref** + portrait + verbal state from T6 |
| T8 | ecu-face | T7 ✗ (face not visible from behind) | **portrait** + verbal state from T6 |
| T9 | front-full | T8 ✗ (face only, no body) | **T6** (last front-full) + portrait + verbal state from T7–T8 |
| T10 | splash (front) | T9 ✓ | T9 ✓ |

The naive chain produces drift at T3, T7, T8, T9 (four of the ten panels). The view-aware chain preserves continuity at all of them.

**Verbal state carry-forward** when you can't use a visual anchor: spell it out in the prompt. *"By this panel her qipao has cumulative tears at: side slits (from earlier), shoulder seam (from earlier), back seam (from earlier). Hair fully loose. Body at size 6 hyper-muscular. Right wrist still has the gauntlet, now stable."* Verbal is weaker than visual but stronger than silent.

**Implementation in panels.json**: add a `view` field to each panel and a `chain_input` field that the runner (or you, if calling MCP directly) populates by scanning backwards through the chain for the most recent compatible view. The deprecated_parallel_id pattern is also useful for tracking which earlier (worse) generation each chained panel supersedes.

---

## L2 — Higgsfield safety filter rejections during FMG splash panels

**Symptom**: A `generate_image` call returns with `status: "nsfw"` instead of `completed`. No image is produced. The job ID is still returned but the result is empty.

**Root cause (observed pattern)**: The auto-filter is most likely to fire on panels that combine *all* of:
- Maximum-size FMG body (size 5–6)
- Heavily tattered/shredded clothing exposing skin
- Bicep flex pose with chest emphasis
- Tight close framing

Any one or two of these is fine. All four together pushes past the filter threshold.

**Fix**: For climactic max-size reveals, dial back exactly one of the four:
- Replace bicep flex with a relaxed hero stance (palms open, arms at sides)
- Keep the qipao "stretched tight and straining at seams" rather than "tattered remnants"
- Pull the camera back to medium/wide rather than tight
- Move the cleavage emphasis into the same prompt as a "full bodice covering, slight tear" detail

The retry typically passes with the same character size and body intent — only the styling/framing changes. The story moment is preserved.

**Prompt hardening that reliably passes**:
```
"qipao stretched tight over her enlarged frame but MOSTLY INTACT — straining at seams with small tears at side slits and shoulders, but the full bodice still covers her completely"
"confident hero pose — arms held out and slightly down at her sides with palms turned forward (NOT a bicep flex)"
"strong powerful but tasteful pose, suitable for a published superhero comic"
```

**Don't argue with the filter** — retry with adjusted styling. The filter is opaque and there is no appeal mechanism.

---

## L3 — Always use the `.png` URL, never `_min.webp`

**Symptom**: Character likeness drifts panel-to-panel even with rich face references. Subtle features (eye shape, nose) come out slightly different each time.

**Root cause**: Every Higgsfield asset has both a full-resolution `.png` URL and a thumbnail `_min.webp`. The thumbnail is upscaled internally if you pass it as a ref, and the upscaling introduces face drift.

**Fix**: Always pass the `.png` URL as the ref, never the `_min.webp`. When in doubt, look at the URL — if it ends in `_min.webp`, don't use it.

---

## L4 — Speech bubbles need explicit positioning and tail direction

> **Status: Active.** Per L19, lettering IS baked into the CGI render (paired with aggressive CGI anchoring vocabulary to prevent 2D drift). L4's positioning, tail-direction, and attribution guidance applies whenever you bake a bubble — which is now the default for CGI comic production.

**Symptom**: Speech bubbles appear in random locations, sometimes overlapping faces or important visual content. Tails point at the wrong character. Multiple characters' bubbles get merged or attributed wrong.

**Fix**: In the prompt, specify:
- Bubble shape ("white speech bubble", "jagged-edged white speech bubble for yelling", "rectangular yellow caption box for narration", "wavering broken-edged outline for weak voice")
- Position ("upper-left of frame", "upper-right with a tail pointing toward Bison's mouth")
- Exact text in quotes
- Character attribution ("contains the line for Chun-Li:", "for Bison:")

For panels with multiple speakers, place each bubble's position explicitly and describe the tail direction for each — don't leave attribution implicit.

---

## L5 — Lineup ref only on stage changes, not every panel

**Symptom**: Character body proportions warp when the muscle-size lineup ref is attached to every panel in a sequence. The model averages across the lineup figures and drifts away from the specific size you want.

**Fix**: Only attach the lineup ref on **stage-change panels** — the moments when the character transitions to a new size tier (e.g., 4→5 transition panel). Between stage changes, use only the character face/body ref + sequential chaining for continuity. Always include the size-matching text in every prompt regardless of whether the lineup is attached. See SKILL.md "Muscle Size Control" for the full rule.

---

## L6 — Display widget result vs. tool-result truncation

**Symptom**: When displaying many image jobs at once (10+) via `job_display`, the tool result returns "exceeds maximum allowed tokens" and the assistant's context loses the result data.

**Root cause**: Each completed job in `job_display` echoes back the full prompt that was used. With 20+ panels at long prompts, the result balloons past the per-tool-call token cap.

**Fix**: For large batches, display in chunks of ~5 jobs per `job_display` call (split into multiple parallel calls). The widget UI still shows them all to the user — only the assistant's context view is affected. Splitting also makes it easier to spot a single failed job in the mix.

---

## L7 — 2D / illustration drift in CGI renders (triptychs AND single panels with rendered lettering)

**Symptom**: A three-panel growth beat (bicep, breast, ass, quad, abs — the templates in `three-panel-scenes.md`) renders as a flat 2D comic-book illustration, despite the prompt explicitly listing "NOT an illustration, NOT anime, NOT cartoon, NOT 2D drawn art." The output looks more like a comic page than a CGI render. Confirmed in production on the Chun-Li abs beat (job `3d0659ff-5371-4f01-8bb4-a87c56edde35`) and consistent across all five body-part beats from the same batch.

**Root cause**: Three things in the prompt were jointly pulling the model into illustration training data, and the negations weren't strong enough to override them:

1. **"Comic SFX" + ascending text overlays.** The phrase "Comic SFX" maps directly to comic-book illustration training data. The moment the model reads it, the entire scene's render style gets pulled toward whatever the model associates with "comic SFX" pages — i.e., 2D illustration. This is the single largest contributor.
2. **"Three-panel sequence" + gutters.** Multi-panel layouts with gutter lines are themselves an illustration convention. CGI renders aren't normally structured as comic pages. Asking for that layout while also asking for CGI puts the two style cues in tension, and the layout cue often wins.
3. **Stacked negations.** Image models obey *described* concepts much more reliably than *forbidden* ones. "NOT illustration, NOT anime, NOT cartoon, NOT 2D drawn" gives the model four illustration concepts to think about. Negations dilute each other — one strong "NOT illustrated" lands; four compete.

**Fix**: Rewrite around positive CGI anchoring rather than negation:

1. **Lead with concrete render-engine vocabulary.** Replace "Hyperrealistic DAZ3D Studio 3D CGI render, physically-based rendering — NOT an illustration, NOT anime, NOT cartoon, NOT 2D drawn art" with: *"DAZ Studio Iray render of a real 3D scene. Ray-traced subsurface scattering on skin, specular highlights catching warm rim light, physically-accurate fabric weave with visible thread detail, 8K texture detail, shallow depth of field with photographic bokeh. Photographic CGI render, NOT illustrated."* The model now has a concrete photoreal target instead of a list of forbidden styles.
2. **Replace "three-panel sequence" with "TRIPTYCH — three side-by-side photographic frames of the same scene at three progressive moments, separated by thin black borders. Each frame is a fully photoreal CGI render in the same style."** Same layout, different vocabulary, no comic-art association.
3. **Use "Frame 1 / Frame 2 / Frame 3"**, not "PANEL 1 / PANEL 2 / PANEL 3". Same idea, less comic-coded.
4. **Drop the comic SFX line entirely** for default templates. The growth progression is self-explanatory. If SFX is genuinely required, render it as an in-scene physical object: *"In each frame, an SFX word appears as a 3D-extruded chrome letter sculpture sitting in the scene as a physical object, casting a real ray-traced shadow on the ground and catching the same warm rim light as the rest of the render."* This forces SFX into the photoreal register instead of overlay graphics.
5. **One negation, not four.** End the prompt with a single closing line: *"Photographic CGI render, NOT illustrated."* Drop the rest.

**Worked example — Chun-Li abs beat, before vs. after**:

Before (drifted to 2D):
```
Hyperrealistic DAZ3D Studio 3D CGI render, physically-based rendering — NOT an
illustration, NOT anime, NOT cartoon, NOT 2D drawn art. Dark dramatic lighting...
[scene description with PANEL 1 / PANEL 2 / PANEL 3 structure]
Comic SFX: "GROW... GROW... GROW" in ascending size text, one per panel.
[10-rule mandatory block]
```

After (held photoreal CGI):
```
DAZ Studio Iray render of a real 3D scene. Ray-traced subsurface scattering on
skin, specular highlights catching warm sunset rim light, physically-accurate
fabric weave with visible thread detail, 8K texture detail, shallow depth of
field with photographic bokeh. Photographic CGI render, NOT illustrated.
[references]
Single image rendered as a TRIPTYCH — three side-by-side photographic frames
of the same scene at three progressive moments, separated by thin black
borders. Each frame is a fully photoreal CGI render in the same style.
[Frame 1 / Frame 2 / Frame 3 description, no SFX line]
[concise CGI rules block ending in "Photographic CGI render, NOT illustrated."]
```

### Case B — Single-panel CGI render with rendered SFX or speech bubbles

**Symptom (the second case L7 covers)**: A regular single-panel CGI generation — not a triptych, just one panel in a longer sequential comic — renders in flat 2D comic illustration style despite the prompt asking for photoreal DAZ3D / CGI. Often happens to a *subset* of panels in a sequence while other panels in the same sequence render correctly as CGI. The drifted panels share a common feature: their prompts asked the model to render **comic SFX text overlays** (e.g., "RRRIP", "KRRK", "BWOOM") and/or **inline speech bubbles** ("a white speech bubble containing the line: '...'") as part of the image itself.

**Root cause**: Same as Case A — comic-coded vocabulary pulls the model toward illustration training data. SFX text overlays and speech bubbles are illustration conventions; asking the model to render them *inside* the CGI image creates style tension, and the lettering cue often wins. The bigger the lettering presence in the prompt, the harder the pull. Panels with heavy SFX + speech bubble + caption drift hardest; panels with no in-prompt lettering hold CGI.

**Fix — the rule (revised per L19)**: **Bake lettering into the prompt, but pair it with aggressive CGI anchoring.** Open with concrete render-engine vocabulary (*"Hyperrealistic DAZ3D Studio 3D CGI render, ray-traced subsurface scattering, physically-based rendering, 8K texture detail"*) and close with explicit negation (*"NOT a comic, NOT an illustration, NOT anime, NOT 2D drawn art. Photographic CGI render."*). Without that anchoring, baked lettering still drifts to 2D; with it, the model holds photoreal CGI while rendering the comic elements.

Render lettering as **physical scene objects**, not 2D overlays:
```
"In the scene, the SFX word 'BWOOM' appears as a 3D-extruded chrome letter sculpture sitting in the scene as a physical object, casting a real ray-traced shadow on the ground and catching the same warm rim light as the rest of the render. The speech bubble is a photoreal semi-translucent 3D surface with extruded text, floating in 3D space, tail pointing to the speaker. NOT a comic, NOT an illustration. Photographic CGI render."
```

Same trick used in Case A's triptych fix.

**Historical note**: L7 Case B previously prescribed *never* baking lettering, deferring all of it to `page-composer` vector overlays. That was avoidance, not control. The diagnosis (comic vocab pulls CGI toward 2D) still holds; the prescription changed in L19.

**Confirmed in production**: Chun-Li growth series — panels 3 (first surge), 4 (bicep close-up), and 5 (full body reveal) all drifted to 2D illustration while panels 1, 2, and 6–10 held photoreal CGI. The three drifted panels had prompted comic SFX text ("RRRIP", "KRRK", "BWOOM", "KRRSH") and inline speech bubbles ("a white speech bubble containing the line: '...'") in the prompt. The non-drifted panels did not. Removing the lettering from those prompts and letting `page-composer` handle dialogue/SFX in post would have held the photoreal style.

**Worked example — Chun-Li first-surge panel, before vs. after**:

Before (drifted to 2D illustration):
```
[CGI render description...]
SFX: "RRRIP" and "KRRK" appear as red and yellow comic-book burst lettering near the seams.
Speech bubble in lower right: white bubble with tail pointing to Chun-Li's mouth, containing the line: "Muscles swelling… clothes getting tight… a rush of strength! What is this?!"
[mandatory rules block]
```

After (holds photoreal CGI with baked lettering, per L19):
```
Hyperrealistic DAZ3D Studio 3D CGI render, ray-traced subsurface scattering on skin, physically-based rendering, 8K texture detail, photographic CGI.
[CGI render description...]
SFX: "RRRIP" and "KRRK" rendered as 3D-extruded chrome letter sculptures near the tearing seams, casting real ray-traced shadows, catching the same warm rim light as the rest of the scene.
Speech bubble in lower right: photoreal semi-translucent 3D panel with extruded text, floating in space, tail pointing to Chun-Li's mouth, containing the line: "Muscles swelling… clothes getting tight… a rush of strength! What is this?!"
NOT a comic, NOT an illustration, NOT anime, NOT 2D drawn art. Photographic CGI render.
```

The dialogue stays in `shotlist.json`'s `dialogue[]` array as the source of truth, but the render bakes it in directly — single cohesive image, no overlay layer.

---

**Where this rule applies**:
- Single-image multi-frame growth beats / triptychs (Case A — the templates in `three-panel-scenes.md`).
- Any single-panel CGI render whose prompt includes SFX text overlays, speech bubbles, captions, or other lettering elements (Case B).
- Any CGI prompt that uses comic-coded vocabulary like "comic SFX", "comic-style layout", "PANEL 1 / PANEL 2", or rendered word art.

**Where this rule does NOT apply**:
- Genuinely illustrated comics where the user *wants* the comic-book aesthetic. The whole point of L7 is that the model defaults toward illustration; don't fight it if illustration is the goal.

**If 2D drift persists despite L7's fixes**:
- Check the character reference image — if the ref itself is a 2D illustration, the model will inherit its aesthetic regardless of prompt language. Use a CGI character ref for CGI prompts.
- Drop the triptych structure entirely and render a single CGI frame at the peak moment. Sometimes the multi-frame layout itself is the issue.
- Add explicit virtual-studio lighting vocabulary: *"shot in a virtual studio with three-point lighting, key light at 5500K, fill at 4500K, rim light at 6500K, rendered in DAZ Studio with Iray at 8K resolution."* The more concrete the rendering vocabulary, the harder the model has to work to drop into illustration.

---

## L8 — Cumulative state in multi-beat growth comics

**Symptom**: A comic has multiple sequential growth beats — say breast growth in scene 3, glute growth in scene 5, bicep growth in scene 7 — each rendered as its own three-panel triptych. By scene 7, the character's bicep beat shows her at full baseline for chest and glutes despite both having been grown earlier. The reader sees the prior-grown features visibly *un-grow* as each new beat begins, breaking continuity across the comic.

**Root cause**: The default three-panel templates start frame 1 at "baseline for the growing feature." That's the right behavior for the **first** growth beat in a comic (no prior state to preserve), but it's wrong for every later beat. The templates don't carry accumulated state forward by default — each beat is a fresh canvas.

**Fix**: For any growth beat that is the 2nd or later in a longer comic, add an explicit **CARRY FORWARD STATE** block at the top of the scene description that:
1. Lists every feature grown in prior beats and its current size.
2. States that those features are IDENTICAL across all three frames of the new beat.
3. Is repeated/reinforced in each per-frame description as *"chest UNCHANGED from frame 1 — still size 5"*, etc.

The growing feature is described normally (frame 1 small → frame 3 large). Everything else is locked.

**Worked example — comic with scene order [breast → glutes → biceps → quads]**:

By the time the **bicep beat** arrives:

```
CARRY FORWARD STATE (constant and identical across ALL three frames — do not 
change between frames): Chun-Li's breasts are ALREADY at size 5 from the earlier 
breast growth scene. Her glutes are ALREADY at size 5 from the earlier ass 
growth scene. The qipao is already stretched tight at the chest, frog-buttons 
already strained, side slits already torn from prior glute growth. All carry-
forward features are IDENTICAL in frame 1, frame 2, and frame 3 — only the 
bicep is growing.

[per-frame description of bicep growth from size 1 → size 5, with each frame 
restating the chest and glutes as unchanged]
```

By the time the **quad beat** arrives, the carry-forward block adds biceps to the list, and only the quad varies across frames.

**Why this works without a consistency issue**: Each frame in a triptych is composed independently — the model isn't tracking temporal state across frames the way a video model would. Cumulative state is just additional *spatial* information the model places into each frame independently. Telling it "chest is size 5 in this frame" three times produces three frames with size-5 chests; the chest doesn't drift because there's no frame-to-frame dependency to drift through. The growing feature varies because it's the *only* feature with different per-frame instructions.

**Why the repetition matters**: Without restating the carry-forward features in each per-frame description, the model sometimes drifts them as it processes the active growth (frame 3's "massive bicep" can subtly inflate or deflate the chest if the chest size isn't re-pinned). The redundancy costs prompt tokens but reliably locks the carry-forward features.

**Relationship to existing templates**: This generalizes Template 6 ("Pre-Grown Muscles + Breast Growth") in `three-panel-scenes.md`. Template 6 is the specific case of "pre-grown arms + currently-growing breasts." The general rule is "any pre-grown features + any currently-growing feature." Encoded as a modifier in the templates file rather than 36+ specific templates.

**Where this rule applies**:
- Any three-panel beat that is the 2nd or later growth beat in a longer comic narrative.
- Multi-beat character arcs where features accumulate (FMG transformations, charge-up sequences with retained VFX, weather progressions where each scene adds to the prior).

**Where this rule does NOT apply**:
- The **first** growth beat in a comic — use the standard templates as-is.
- Standalone three-panel beats with no prior story context.
- Independent showcases — alternate-reality character variants, separate characters per beat, "what-if" panels.

**Validation case**: Confirmed in production — Chun-Li bicep growth beat with breasts pre-set to size 5, biceps growing from size 1 → 5 across three frames. Job `c22d8d7f-4446-444e-98b0-776f9fe02b9a`. The chest stays locked at size 5 across all three frames; only the bicep varies. Prior to this pattern, generating a "later beat" with baseline framing produced a chest visibly *smaller* in frame 1 than in the previous scene's final panel, breaking the comic's visual continuity.

---

## L9 — Capture every panel's job_id before submitting the next, or chaining silently breaks

**Symptom**: A multi-panel sequence was generated *sequentially* (not in parallel), but the output still shows L1-style state regression between adjacent panels — clothing damage patterns reset or change shape, body size flickers down, hair re-pins, accumulated tears disappear. The panels look individually fine; the discontinuity is *between* them. Most visible on costume damage: the qipao's tear pattern changes location, shape, or coverage from panel to panel rather than accumulating monotonically.

**Root cause**: Without a recorded `job_id` from panel T_{N−1}, panel T_N can't reference T_{N−1} as a `medias[]` input. The `generate_image` MCP call still completes — but the panel is being composed from the baseline character ref only. The chain is silently broken, even though you submitted in order. There is no error and no warning at submit time. You only see the failure in the output, sometimes pages later when the cumulative drift becomes obvious.

This is **distinct from L1** (which is about parallelizing a chain that *should* be sequential). L9 is what happens when you *intend* to chain sequentially but the workflow loses track of the job IDs. The output symptom looks identical to L1 because the model has no memory either way.

**Common workflow gaps that cause this**:
- Using `generate_image` MCP directly (not the runner) and forgetting to record each returned `job_id` *before* composing the next panel's prompt.
- Recording only the first few job IDs and leaving the rest as `—` "to fill in later" — by the time you go back, the chain has already broken from the first missing ID forward.
- The runner crashes mid-batch and the user retries individual panels ad-hoc via MCP without consulting `state.json` for the prior-panel job_id.
- Confusing `job_id` (per-generation result, what you chain from) with `ref_id` (per-asset uploaded to Higgsfield, what you attach as a static reference). Passing a `ref_id` where the chain expects a prior `job_id` doesn't error but doesn't chain.

**Fix**:
1. **Prefer the runner for any chained sequence.** `state.json` captures every `job_id` automatically and crash-resume picks up where you left off. Don't bypass it for "quick" chained runs.
2. **When using `generate_image` MCP directly for a chain**:
   - Before submitting panel N, confirm the job_id you intend to chain from (per L1.5's view-aware compatibility table) is in hand.
   - Immediately after each `generate_image` returns, write the job_id to `job_ids.md` (or a `chain.json`) **before composing the next prompt**. Not at the end of the session — right now.
   - Treat a partially-filled `job_ids.md` as a broken chain. The only recovery is to re-run from the first missing ID forward.
3. **Validation check before composing panel N's prompt**: read `job_ids.md`. If the panel you need to chain from has no recorded ID, stop. Either find the missing job in the Higgsfield UI and record it, or accept the chain is broken from this point and start a fresh chain.

**Confirmed in production**: Chun-Li growth series. `job_ids.md` recorded only panel 1's job_id; panels 2–10 were left as `—`. Panels 8, 9, and 10 show visible costume-damage drift between adjacent panels (different bodice tear patterns, different leg-slit positions, different intactness levels) — the classic L1 symptom even though the panels were generated sequentially. Root cause: each panel was generated from the baseline character ref alone because no prior `job_id` was available to pass into `medias[]`. The model had no way to see what the previous panel ended on.

**Worked example — correct discipline via MCP**:
```python
# Each panel: generate, then IMMEDIATELY record the job_id before the next call.

t1 = generate_image(prompt=T1_prompt, medias=[portrait, body_ref])
log_to_job_ids_md(panel="T1", job_id=t1.job_id)        # <-- before T2

t2 = generate_image(prompt=T2_prompt, medias=[t1.job_id, portrait])
log_to_job_ids_md(panel="T2", job_id=t2.job_id)        # <-- before T3

t3 = generate_image(prompt=T3_prompt, medias=[t2.job_id, portrait])
log_to_job_ids_md(panel="T3", job_id=t3.job_id)
# ...
```

The discipline: **no `generate_image` call for a chained panel without the prior job_id in hand, and no next `generate_image` call without the current job_id recorded.**

**Recovery if a chain has already broken**: there is no way to retroactively chain panels generated without their predecessor's ID. The model has no memory; if T5 was generated from baseline instead of T4, T5's costume state is whatever the baseline implied plus prompt text, not what T4 ended on. Two recovery paths:
- **Accept the break** and start a fresh chain from T_break (record T_break's job_id, chain T_break+1 to it, etc.) — the resulting comic has a visible discontinuity at the break, but the rest holds.
- **Re-run from the break point** — regenerate T_break with T_{break−1}'s job_id as input (if you can find that ID in the Higgsfield UI), then T_break+1 from the new T_break, etc. Burns time and credits but produces a clean comic.

**Where this rule applies**:
- Any multi-panel chained sequence using `generate_image` MCP directly.
- Any time the runner is bypassed mid-batch (manual retries, ad-hoc improvements to a single panel in a chain, switching from runner to MCP partway through).

**Where this rule does NOT apply**:
- One-off standalone panels with no chain dependency.
- Independent panels in the same scene that don't share evolving state (parallelizable per L1).
- Runner-driven batch production — `state.json` handles ID capture automatically and the runner won't proceed without it.

---

## L10 — References are the truth, prompts are deltas

**Symptom**: The same location renders as visibly different rooms across panels of the same scene. The same character drifts in costume detail, hair length, facial proportions across the issue even though face cards are attached. Bigger picture: anything the prompt re-describes — character appearance, costume design, location architecture — comes out *slightly different each time*, because the model is interpolating between the text it reads and the references it sees attached.

Confirmed in production: Supergirl issue #1 panels 02 vs 05 — same location (`lex-lab-redsun`), DAZ env ref attached in both cases, but the prompt phrasing differed ("industrial chamber with computer banks" vs "chamber bathed in red flood with pipes") and the model produced two visibly different rooms.

**Root cause**: When the prompt and the reference both describe the same thing, the model treats them as two competing signals and interpolates. Text is unambiguous; refs are interpretive. So when the prompt says "Lex is bald, mid-40s, sharp-featured" *and* the face card is attached, the text wins on details where the two disagree — and the disagreement is invisible until you compare panels side by side.

This compounds with paraphrasing: every panel's prompt is composed at runtime, and each panel describes the same constants differently ("industrial chamber" / "underground lab" / "warehouse-aesthetic interior"). Each paraphrase gives the model a fresh interpretation of constant data, and the constant drifts.

**Fix**: Adopt a delta-only prompt skeleton.

The prompt body should describe only what is *new* in this panel:
- Camera (distance, angle, lens)
- Action (pose, gesture, expression)
- Lighting state *change* (the change from baseline, not the baseline itself)
- Costume state *change* (the new tear / new damage, not the costume design)
- Size tier (only if changed)

Everything *constant* lives in the attached references:
- Character identity → face card
- Character body baseline → body baseline
- Costume design → body baseline + cumulative state from prior accepted panel
- Location architecture → env reference (DAZ `_source.jpg` for the first panel; the first **accepted** panel in that location for every panel after — see env chaining below)

Add a literal "render directive" sentence to every prompt:

> *Render the attached references exactly as shown. Do not reinterpret character appearance, costume design, or location architecture from the prompt text — those are fixed by the references. The delta describes only what is new in this panel: camera, action, expression, momentary lighting state, momentary costume change.*

This sentence is load-bearing. It tells the model the priority: refs > text on visual identity.

**Env chaining (a corollary of L10 applied to environments)**:

The DAZ3D `_source.jpg` is a *starting* env reference. The first time a hero location appears in a panel, attach `_source.jpg` and instruct the model to use it for "scene style, lighting setup, scale, depth, render quality." Once that first panel is accepted, **it becomes the location's canonical anchor**. Every subsequent panel in that location attaches the accepted panel's PNG as the env reference, not `_source.jpg`.

Why: the accepted panel is more specific (it shows your exact chamber, not a stand-in throne room), and the model can carry forward your actual architecture rather than re-interpolating between a stand-in scene and prose descriptions.

The runtime composer (`next_panel.py`) implements this by checking accepted_history for any prior panel in the same location and preferring its image to `_source.jpg`.

**Don't redescribe in shotlist `action` either**:

The `action` field is where description bleed sneaks in. Resist writing:

> "Wide establishing of the underground lab. Supergirl chained in the center of the chamber, hands and ankles cuffed. Lex stands at his terminal mid-distance camera-right, suit immaculate."

The bolded parts re-describe constants that are already in refs:
- "underground lab" → in env ref
- "Lex's suit" → in Lex's body baseline
- "Supergirl chained" → if cuffs are a recurring prop, ref them; otherwise mention them as a *delta*

Better `action`:
> "Wide establishing camera. Kara at center, restrained. Lex at his terminal mid-distance camera-right, hands behind his back, watching her with anticipation."

Camera, action, pose, expression. No architecture, no costume design, no character features. The composer adds those via refs.

**Where this rule applies**:
- Every per-panel prompt in shotlist-driven Flow production
- Every Higgsfield panel prompt the runner composes
- Every reference doc that gives prompt skeletons (cinematic-framing, multi-character-variation, etc.)

**Where this rule does NOT apply**:
- The shotlist's top-level `cast[]`, `locations[]`, `props[]` description fields. Those are *documentation* and *generation instructions for the reference itself* (used when generating face cards, env refs from scratch). They're correctly redundant with refs because they explain *what the ref should depict*. They should never be pasted into a per-panel prompt.

**Detection / linting hint**: a composed panel prompt that mentions costume colors, hair colors, building materials, wall types, ceiling height, or character age is probably violating L10. The runtime composer should suppress these terms when refs are attached; the SKILL's QA pass should flag them.

---

## L11 — Cartoony FMG proportions need explicit anchoring or the model regresses to realistic fitness

**Symptom**: Generated characters are visibly *smaller* than their declared tier. A tier-4 panel that should show cartoony hyper-FMG proportions (shoulders 2× normal width, massive biceps, ridged abs, sculpted quads — i.e. the silhouette of figure 4 in `assets/muscle-size-lineup.png`) renders instead as a fitness-magazine athletic build — closer to tier 2 or 3. Drift compounds: a panel that under-renders the tier on the stage-change shot anchors every carryover panel after it at the smaller build.

Confirmed in production:
- April-claudemade: peak panels rendered visibly smaller than the hand-made comparison comic and noticeably smaller than the user's target aesthetic.
- Supergirl panel 13 (tier-4-tears): the lineup ref wasn't attached at all due to the `find_lineup` path bug (fixed earlier; see commit `0b963c6`), so the model rendered tier 4 from verbal cues alone and produced an undersized build.

**Root cause**: Two failures stacking.

1. **Lineup ref not attached** (or attached on too few panels). The L5 heuristic ("lineup only on stage-change") was inherited from the Higgsfield era where every ref attachment cost money. On Flow refs are free; the lineup belongs on every panel where the body is the focal subject, not just transitions.
2. **Size language too gentle.** "Match the muscle proportions of figure N" reads to the model as "render a muscular character" and the model commits to its prior of plausible-fitness anatomy. The lineup image shows comic-book proportions but the prompt's mild vocabulary doesn't commit to that aesthetic, so the model interpolates between the lineup (cartoony) and its default (realistic), landing on a realistic-fitness build.

The model has a strong prior toward realistic anatomy. Without aggressive vocabulary it pulls back toward that prior every time.

**Fix**: Two parts.

**Attachment rule (replaces L5)**: Attach the muscle-size lineup ref on **stage-change panels AND on every full-body camera panel of the arc character**. Full-body cameras: `front-full`, `3q-full`, `side-full`, `back-full`, `low-angle-front`, `low-angle-back`, `splash`. ECU-face / ECU-region / mcu / medium skip the lineup (size isn't the focal element there). `next_panel.py`'s `should_attach_lineup()` enforces this.

**Vocabulary upgrade**: The size-tier block of the composed prompt must include:

1. A style anchor sentence BEFORE the action delta: *"Style anchor for the body: cartoony hyper-FMG comic-book proportions, NOT realistic fitness modelling. Exaggerated comic musculature where the silhouette is the storytelling element."*
2. A tier-specific silhouette descriptor with explicit dimensional anchors (e.g. tier 4: *"shoulders 2x normal width with clear deltoid mass, large defined biceps and triceps, full powerful chest, ridged abdominal definition, strong sculpted quads"*).
3. A "match the silhouette, don't approximate" directive: *"Render the silhouette TO MATCH the lineup figure — do not approximate to a smaller realistic build."*
4. An explicit negation of the model's default: *"NOT realistic fitness, NOT athletic — cartoony FMG, comic-book proportions."*

See `peak-body-scale.md` for the full tier-by-tier silhouette catalog and worked examples of vocabulary that survives the model's prior.

**Where this rule applies**:
- Every transformation-comic project (any project whose shotlist has a `muscle_size_tier` field on its panels).
- Every full-body panel of any arc character at tier ≥ 2.

**Where this rule does NOT apply**:
- Tier 1 panels (realistic baseline — the cartoony anchor would hurt).
- Non-transformation comics where size isn't a story element.
- ECU-face / ECU-region panels (size isn't the focal element).

**Detection / linting hint**: When reviewing accepted panels against their declared tier, compare side-by-side with the figure of the same tier in the lineup. If the silhouette is visibly smaller than the lineup figure (especially shoulder width and overall mass), the panel undershot. Common at tier 4 specifically (the threshold between realistic and cartoony — the model crosses tier 3 fine and commits to tier 5+ readily, but tier 4 is where the prior fights hardest).

---

## L10 refinement — Identity-vs-pose: drawing the line where deltas legitimately describe

Reviewing a Higgsfield-generated She-Hulk splash, the user marked two adjacent prompt fragments with opposite verdicts:

- *"Wardrobe: red top remnants tied across her chest, dark fabric skirt-remnants over her hips (NOT pants)"* → **"this text is completely unnecessary."** Costume design is a constant — it's in the ref. Redescribing it is L10 violation.
- *"Pose: full hero roaring stance, arms partly raised at sides, fists clenched, mouth wide open in a powerful triumphant roar showing teeth, body coiled with energy."* → **"this pose prompt is needed, because the ref image doesn't have this pose, and that's the way to change her pose."**

So the L10 line isn't "describe nothing." It's:

| Goes in the **reference** | Goes in the **prompt delta** |
|---|---|
| Character identity (face, hair baseline) | Camera (distance, angle, lens) |
| Costume design (colors, cut, accessories) | Pose / gesture / stance |
| Body baseline proportions | Facial expression |
| Location architecture | Action (what's happening) |
| Lighting baseline / motivation | Momentary lighting state (eg "now bathed in red") |
| Static props (chair shape, banner) | Momentary costume state CHANGE (eg "new tear at shoulder") |
| Recurring SFX placement intent | Eye-line / gaze direction |

The render directive in `compose_prompt()` already says "Do not reinterpret character appearance, costume design, or location architecture from the prompt text." This addendum adds the *positive* side: **pose, action, expression, momentary lighting state, and momentary costume state change MUST be in the prompt** — refs can't carry per-panel beats, so the prompt is the only place to put them. A shotlist `action` field that describes the pose and expression is doing the right thing; an `action` field that describes the suit and the wall material is leaking constants into the delta.

This refinement does not change `next_panel.py`'s composer logic — the current skeleton already puts pose/action/expression in the DELTA section. What changes is the **authoring guidance**: when reviewing a shotlist or a generation prompt, scan for description bleed using the table above. Anything in the left column should be in refs, not text.

---

## L12 — Dialogue panels need close framing

**Symptom**: Comic pages where one character speaks 30 words of dialogue at wide-establish distance. The speaker's face is unreadable; the reader can't tell who's talking; the page reads like a script with art, not a comic. Confirmed by reviewer note on Supergirl issue #1: *"It doesn't zoom in when the person's talking to a tight shot."*

**Root cause**: The shotlist `camera` field is authored independently of `dialogue[]`. A scene can carry "establish the lab" intent (wide camera) and "Lex monologues at his terminal" intent (long dialogue line) on the *same panel*. The composer doesn't notice the conflict; the model renders the wide shot faithfully; the dialogue gets bubble-attached on top of a small speaker who's not the focal point.

**Fix**: Hard rule — if a panel has on-screen dialogue (`type` in `balloon` / `thought` / `whisper` / `shout`), the camera must be close enough that the speaker is the focal point. Acceptable: `ecu-face`, `mcu`, `medium`, `cowboy`. Marginal: `3q-full` if there's a single short line. Wrong: `wide-establish`, `splash` (unless the dialogue is `caption` or `off-panel` — narration/off-screen voice doesn't compete with camera distance for focal point).

Implementation paths (cheapest first):

1. **`next_panel.py` planning-time warning**: when `compose_prompt` sees on-screen dialogue + wide camera, surface a `WARNING_DIALOGUE_CAMERA_CONFLICT` entry in the plan and ask the user to either tighten the camera or convert the dialogue to a caption.
2. **`rules_audit.py` script-breakdown gate**: HARD finding for shotlist panels with wide camera + on-screen dialogue. Blocks at script-breakdown time before generation cost is spent.
3. **Composer auto-tighten** (riskier): override the camera to `mcu` when conflict detected. Loses authoring intent; only safe if the user opts in.
4. **PreToolUse hook on `generate_image`** (per the other guy's research on Claude Code hooks): hard enforcement at the call site. Strongest but requires the hook infrastructure.

**Where this rule applies**:
- Every panel of every comic. Universal.

**Where this rule does NOT apply**:
- Caption boxes (narration). Wide establishing shot with "TWO HOURS LATER" caption is canonical.
- Off-panel dialogue (`type: off-panel`). The speaker isn't on-screen so the camera distance is independent of the dialogue.

---

## L13 — Multi-speaker beats split into per-speaker panels

**Symptom**: One panel renders three or four characters in a cramped lineup, each with a balloon. The page looks like a sitcom freeze-frame; reading order is ambiguous; no individual character is the focal point. Confirmed by reviewer note: *"If we feed in a comic that has four different dialogue lines on one image, instead of that it shows several different people individually with their dialog line."*

**Root cause**: The shotlist treats "scene with N speakers" as one panel because the *action beat* is one continuous exchange. That conflation produces visually-broken comics. A two-character argument with eight back-and-forth lines is NOT one panel — it's six to eight panels.

**Fix**: At script-breakdown time, detect any panel with **≥3 dialogue entries from ≥2 distinct speakers** (excluding captions and off-panel). Surface as a HARD finding with the suggestion: split into one panel per beat, with each panel framing the speaker who's talking on it. Reading order follows the page's panel order; the visual rhythm of cutting between speakers carries the conversation.

Threshold tunings:
- 1 dialogue entry, 1 speaker → fine, single panel
- 2 dialogue entries, 1 speaker → fine (one speaker says two things), single panel works
- 2 dialogue entries, 2 speakers → marginal, prefer 2 panels but can keep as 1 (back-and-forth at close framing)
- ≥3 entries, ≥2 speakers → split

**Implementation**: `rules_audit.py` gate at script-breakdown time. Also surface in `next_panel.py` planning output. Hooks layer if/when built.

**Where this rule applies**:
- Dialogue-heavy scenes (interrogation, argument, council meeting, exposition).

**Where this rule does NOT apply**:
- Crowd shouts / chorus (one collective beat across many speakers).
- Caption-only beats (narration over a scene where multiple characters are physically present but not speaking).
- Splash pages whose explicit intent is to show the cast together (cover, opening lineup, finale). These are visual showcases, not conversational beats.

---

## L14 — Multi-view location references for shot-reverse-shot scenes

**Symptom**: A two-character dialogue scene reads as if the characters are in two different rooms because every panel uses the same establishing-shot anchor (per L10 env chaining) and the model can't reconstruct a coherent reverse angle from one A-side reference. The user wants to cut between facing Lex (camera looks east) and facing Kara (camera looks west) — but our env anchor is only the eastern view, so reverse-angle panels lose the location identity. Confirmed by reviewer note: *"We'll have to build up more references that show the character's face and also show a 360 view of the scene. This way when two people are talking, the camera can face both directions of the people."*

**Root cause**: L10 env chaining assumes one canonical view per location. That works for sustained-POV scenes (the supergirl chamber establishing shot reused across all act II panels). It breaks for shot-reverse-shot because the canonical view is by definition a *single direction*, and reversing the camera produces a scene the env anchor doesn't depict.

**Fix**: Hero locations that host shot-reverse-shot scenes should carry **multiple env references**, keyed by camera direction:

```
references/locations/lex-lab-redsun/
  _source.jpg              # default establishing (DAZ stand-in)
  _source-reverse.jpg      # 180° opposite angle
  _source-overhead.jpg     # optional, high-angle / bird's-eye
  _provenance.md
```

`pick_location_anchor` in `next_panel.py` extends to:

1. If the panel's camera direction is compatible with the most recently accepted shot in this location → use that accepted shot (current behavior).
2. If the camera direction is the **reverse** of the most recent accepted shot, walk `accepted_history` backwards for any prior reverse-angle shot in this location and use it.
3. If no reverse-angle accepted shot exists yet, fall back to `_source-reverse.jpg` if present.
4. If neither exists, fall back to `_source.jpg` with a `WARNING_REVERSE_VIEW_MISSING` note in the plan.

Detecting "reverse" from camera string: when the panel's camera contains directional cues (e.g. `over-shoulder Lex looking at Kara` vs the prior accepted's `over-shoulder Kara looking at Lex`), or when the angle flips between `front-full` (one character) and `back-full` (same character, reverse perspective).

Authoring guidance: when a shotlist has a multi-page dialogue scene with on-screen speakers, the **first establishing shot** locks the A-side, the **first reverse-angle shot** locks the B-side, and subsequent panels in that scene chain off whichever side matches their direction.

**Where this rule applies**:
- Scenes with ≥2 panels showing facing characters from different sides (interview, interrogation, argument, ritual exchange).

**Where this rule does NOT apply**:
- Single-direction scenes (the supergirl chamber transformation — every panel faces the platform).
- Splash pages and establishing wides that are visually self-sufficient.

---

## L19 — Bake lettering into the CGI render (reverses L7 Case B's "never bake" rule)

**Symptom**: The L7 Case B workflow deferred all lettering — speech bubbles, captions, SFX — to `page-composer`, which applied vector overlays on top of clean CGI renders. The result reads as "CGI panel + sticker overlay" — lettering looks pasted on rather than part of the rendered scene. The desired output is a single cohesive rendered comic page where the lettering is part of the photoreal world.

**Root cause**: L7 Case B over-corrected on a real observation (comic-coded vocab in lettering prompts pulls CGI toward illustration training data). Its prescribed fix — never bake lettering — was avoidance, not control. The right fix is to bake the lettering AND aggressively counter the illustration pull at the prompt level.

**Fix**:

1. **Open every CGI panel prompt with concrete render-engine vocabulary**:
   > *"Hyperrealistic DAZ3D Studio 3D CGI render, ray-traced subsurface scattering on skin, physically-based rendering, 8K texture detail, photographic CGI."*
2. **Bake all lettering directly into the prompt** — speech bubbles (per L4 positioning rules), SFX, captions.
3. **Render lettering as physical scene objects**, not 2D overlays:
   - SFX words → 3D-extruded chrome / stone / energy letter sculptures with real ray-traced shadows, catching scene rim light
   - Speech bubbles → photoreal semi-translucent 3D panels floating in space, tails pointing at speakers
   - Caption boxes → in-scene plaques or rendered textured panels with extruded text
4. **Close every prompt with explicit negation**:
   > *"NOT a comic, NOT an illustration, NOT anime, NOT 2D drawn art. Photographic CGI render."*

The opening anchors the photoreal target; the closing tells the model what to avoid. Both are needed — neither alone holds.

**Relationship to other lessons**:
- **Reverses L7 Case B's prescription.** The diagnosis (comic vocab pulls toward 2D) still applies, but the fix is now "bake AND anchor," not "never bake."
- **Restores L4 to active status.** Bubble shape, position, tail direction, and per-speaker attribution all matter again because bubbles are in the render.
- **Open question**: whether `page-composer` survives as an optional fallback for projects that prefer vector lettering (legibility, edit-ability), or gets retired entirely. Decide per-project.

**Where this rule applies**:
- All CGI comic production where the user wants a single cohesive rendered look (the current default).

**Where this rule does NOT apply**:
- Projects that explicitly opt for vector lettering in post (rare).
- Genuinely 2D-illustrated comics where illustration IS the goal.

---

## How to add a lesson

When you observe a new failure mode that recurs, append a new entry following the structure above:
- **Symptom** (what the output looks like)
- **Root cause** (the mechanism)
- **Fix** (the concrete prompt or workflow change)
- Optional: worked example, prompt fragments that reliably work

Keep entries punchy. If a lesson grows past ~150 lines it probably wants its own dedicated reference file.
