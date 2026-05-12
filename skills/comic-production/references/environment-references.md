# Environment References — DAZ3D Scene Conversion

Backgrounds are the single biggest "AI tell" in CGI comics. Characters benefit from refs (face, body, lineup); environments usually don't. Without a reference, the model invents the location each panel — the same alleyway gets different lanterns every time, the temple has different pillars, the lair renders generically.

This guide documents a technique that produces dramatically better, more consistent environments: **find an existing DAZ3D-rendered scene online, save it, and use it as a reference image with instructions to transform it into your target location.**

**Confirmed in production**: produces backgrounds that read as real 3D-rendered scenes (consistent lighting, plausible scale, photographic depth) instead of AI-invented blur.

---

## Why this works

The model has been trained on a lot of DAZ3D / Iray renders. When you pass one as a reference image with edit instructions, the model anchors to that render's:

- Lighting setup (key, fill, rim)
- Scale and depth
- Material physical behavior (specular highlights, subsurface scattering)
- Rendering style (Iray-specific look)

You're saying: *"render in this exact style, but reskin the content to be [target]."* The model holds the technical render character and substitutes the content.

Without a reference, the model invents the location each call. With a reference, the location stays anchored panel-to-panel.

---

## When to use this technique

**Use it for**:
- **Hero locations** that appear in multiple panels — Bison's Lair, the training dojo, the temple sanctum, the underground arena, the corporate boardroom. Anywhere consistency matters.
- **Stylized environments** where AI usually produces generic blur — futuristic interiors, fantasy throne rooms, sci-fi corridors, mythological architecture.
- **Establishing shots** where the environment is the focal point.
- **Splash panels** where backgrounds are visible in full detail.

**Don't bother for**:
- Generic exteriors the model handles well (forest clearings, generic city streets, beaches at sunset).
- Tight character shots where the background is heavily defocused.
- Pure black/void backgrounds.

---

## Workflow

### 1. Find the source reference

Google image searches that surface DAZ3D scene renders:

- `daz3d scene "throne room"` — replace the quoted term with your target
- `daz studio iray render <location keyword>`
- `renderosity scene render <keyword>`
- `daz studio environment <keyword>`
- `site:renderhub.com <keyword>`
- `site:daz3d.com gallery <keyword>`

**Avoid** Pinterest results (often re-uploaded AI art mislabeled as DAZ3D — defeats the technique). **Avoid** generic stock photo previews.

**Prefer**:
- DAZ3D's own gallery (`daz3d.com/gallery`)
- Renderosity gallery
- Renderhub product previews
- ArtStation users who tag DAZ3D / Iray in their workflow
- Reddit `r/Daz3D` and `r/Renderosity`

What you want: a single still render with clear lighting and depth, decent resolution, and a *vibe* close to your target scene. The composition doesn't need to match — you'll instruct the model to change content. The render *style* does.

### 2. Save with provenance

Save the source image to `references/locations/<location-slug>/_source.jpg`. Add a `_provenance.md` note (same convention as `reference-gathering`):

```
# _provenance.md for references/locations/bisons-lair/

## _source.jpg
- Source: https://www.daz3d.com/gallery/example-throne-render
- Captured: 2026-05-11
- Original scene: "Gothic Throne Room" — DAZ Studio Iray render by [creator]
- Used as: visual anchor for Bison's Lair in [project-name]
- QA note: clean Iray render, dramatic chiaroscuro lighting, scale and depth read clearly — good anchor for stylized villain interior.
```

### 3. Use as a reference image in the panel prompt

When generating a panel that includes this location, pass the source image as a `medias[]` entry alongside the character refs. In the prompt, use this pattern:

```
[character description with face/body refs attached]

ENVIRONMENT: Bison's Lair — a Shadaloo command bunker carved into rock, dimly lit by overhead spotlights and the cold glow of monitor banks. Use the attached reference image for the SCENE STYLE — the lighting setup (dramatic chiaroscuro, cold key from above, warm rim from screens), the depth, the scale of the architecture, and the Iray render quality. Replace the gothic throne room content with Bison's Lair content: rusted steel pillars instead of stone columns, military command screens on the walls, the iconic Shadaloo emblem etched into the floor, Bison's throne at the center — a metal-and-leather command chair on a raised dais.

Keep the same render style: photographic CGI render, ray-traced lighting, physically-accurate materials, deep cinematic shadows.

[mandatory rules block, ending in "Photographic CGI render, NOT illustrated."]
```

### 4. Reuse across the comic

Use the same `_source.jpg` reference on every panel set in that location. The location stays visually consistent — same lighting, same scale, same render character — across the entire comic, instead of the model re-inventing it each time.

For *variation within* the location (different angles, time-of-day shifts), pair the location ref with verbal instructions for the change:

> "Same Bison's Lair location as the attached reference, but now lit only by the emergency red strobes — the overhead spotlights are off. The Shadaloo emblem visible on the floor in red emergency lighting."

The lighting changes; the location identity holds.

---

## Worked example — Bison's Lair

1. **Search**: `daz3d gallery "throne room" gothic` → find a DAZ3D-rendered gothic throne room with dramatic uplighting.
2. **Save**: `references/locations/bisons-lair/_source.jpg` plus `_provenance.md`.
3. **First panel using it — wide establish**:
   ```
   [character refs attached: Chun-Li portrait]
   [environment ref attached: bisons-lair/_source.jpg]
   
   Wide establishing shot. Camera at floor level looking down the central aisle of BISON'S LAIR — Shadaloo command bunker. Use the attached environment reference for the SCENE STYLE: the dramatic chiaroscuro lighting (cold overhead key, warm rim from background screens), the deep architectural recession, the Iray render quality. Replace the gothic content with Bison's Lair content — rusted steel pillars lining the aisle, banks of command monitors glowing cyan against the walls, the Shadaloo skull emblem inlaid in the dark stone floor, Bison's throne at the far end on a raised dais.
   
   Chun-Li in the foreground, full body, facing away from camera toward the throne. Reduced-baseline build (size 1 from lineup), classic blue qipao intact.
   
   Photographic CGI render, NOT illustrated. Iray-style ray-traced lighting, physically-accurate materials, deep cinematic shadows.
   ```
4. **Subsequent panels in the same location**: re-attach `bisons-lair/_source.jpg` as an environment ref every time. Even on close-ups where the background is mostly blurred — the reference still anchors the wall material, the lighting color temperature, and the ambient depth cues.

---

## How this combines with other references

This is **additive** to the character ref + prior-panel chain. A typical multi-character panel set in a location uses:

- **Prior-panel job_id ref** (state continuity, per L1 + L9)
- **Character face/body refs** (face anchor, per L1.5 chaining)
- **Muscle lineup ref** (on stage-change panels only, per L5)
- **Environment ref** (this guide) — every panel in the location

Higgsfield's `medias[]` array accepts multiple references. Order them:
1. Prior-panel job_id first (state)
2. Character portrait (face anchor)
3. Environment ref (location anchor)
4. Specialized refs (lineup, props)

---

## When the technique fails

- **Wrong reference choice.** If the source render is itself low-quality, low-resolution, or stylistically off, the model inherits its weaknesses. Pick well-rendered, well-lit references.
- **Asking the model to change too much.** If you ask it to change lighting, scale, content, AND materials, the reference has nothing to anchor on and you may as well not attach it. Change content; preserve render style.
- **Conflicting style vocabulary.** Asking for "illustrated comic book art" in the prompt while attaching a photoreal CGI reference confuses the model. Match prompt vocabulary to reference style.
- **Reference is itself AI-generated.** Many "DAZ3D"-tagged images on Pinterest and image aggregators are actually AI renders. They lack the technical render character that makes this trick work. Verify the source — DAZ3D gallery, Renderosity, named artist portfolios are reliable.

---

## Storage convention

In a project folder:

```
references/
  locations/
    bisons-lair/
      _source.jpg          # the DAZ3D reference render
      _provenance.md       # source URL, capture date, notes
      [optional: _source-night.jpg, _source-emergency.jpg for variants]
    training-dojo/
      _source.jpg
      _provenance.md
    chinese-alley/
      _source.jpg
      _provenance.md
```

`shotlist.json`'s `locations[]` array should reference these folders so the orchestrator can verify coverage before generation.

---

## How to apply

1. **At script-breakdown / location mapping**: identify hero locations that will appear in multiple panels. For each, search for a DAZ3D scene reference matching the vibe.
2. **At reference-gathering**: save each to `references/locations/<slug>/_source.jpg` with provenance.
3. **At prompt-writing**: attach the location's `_source.jpg` to every panel set in that location. Use the env-anchor language pattern above.
4. **At QA**: check that the location reads consistently across panels (lighting, scale, material). If a panel drifted, regenerate with the env ref re-attached.

This guide pairs with `reference-gathering`'s default workflow for character refs. Both produce `_provenance.md` so the source of every reference is auditable.
