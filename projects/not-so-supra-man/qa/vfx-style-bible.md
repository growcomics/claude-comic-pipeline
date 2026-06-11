# VFX Style Bible — human-made DAZ effect aesthetics

**Purpose.** Our energy effects look "too perfect": simulation-grade volumetrics, anatomy-conforming
filaments, physically correct light spill. That reads as AI. The target is what a skilled human DAZ
artist gets from **store-bought effect props + Photoshop postwork**: glowing geometry pasted into the
scene, a sprite at the contact point, uniform bloom slapped on at the end. The charm IS the crudeness.
Every effect in this comic should look like it was *added to* the render, not *simulated within* it.

**How humans actually build these effects (the four mechanisms behind every signature below):**

1. **Emissive tube/cone props** — beams are concentric cylinders, "inner brighter than the outer,"
   with bend/twist/wave morphs that visibly stretch the texture (Photo Props: Energy Beams, SY Energy
   Beams Iray). The beam is a rigid object: it gets posed, it does not flow.
2. **Emissive geoshells** — "energy on skin" is a second skin offset a few millimeters off the figure
   with a tiling emissive transparency map: flame/electric filigree in flat color presets, toggled
   per limb (PowerFist Plus geoshell, FPE Magic Effects skin shells with luminance-map masks).
3. **2D transmapped billboard cards** — impacts, explosions, bolts, sparks are flat alpha-mapped
   planes stood up in the scene (SY KABOOM "20 2D transmapped explosions," Electric VFX "16 2D bolts").
4. **Photoshop postwork** — lightning brushes stamped in Screen mode with an outer-glow layer style
   (Ron's Lightning FX: 240 brushes + 22 layer styles), plus one uniform screen-space bloom pass at the
   very end (Electric VFX ships bloom presets OFF/Low/Medium/High "to match the promo artwork").

Community ground truth: "DAZ Studio is very limited for effects… postwork is your best bet for this
sort of thing" (Daz forums, aura thread). That limitation is the aesthetic.

---

## 1. Effect taxonomy (this comic)

| # | Effect | Where it appears in Not-So-Supra-Man | Human-DAZ mechanism |
|---|--------|--------------------------------------|---------------------|
| T1 | **Energy beam (ray-cannon)** | Disinto-Ray firing (p17 beat, prototype beam, final pour-in) | Emissive tube prop + impact-tip sprite |
| T2 | **Body electricity / skin shimmer** | Teal shimmer on Dana's forearms, shoulders; stage-2/3 arm crackle | Emissive geoshell + a few brush-stamped bolts |
| T3 | **Power-up aura** | Dana rising in the beam-glow, haloed; energy wash | Scaled duplicate-figure glow / postwork outer glow |
| T4 | **Force field** | (reserve — Destroya fight, beam-haze shielding) | Concentric transparent sphere layers |
| T5 | **Impact flash / shockwave** | Beam striking Supraman's back; Dana catching the haymaker | 2D transmapped starburst card + postwork ring |

---

## 2. Visual signature of human DAZ versions

### T1 — Energy beam (ray-cannon)

- **Geometry-prop look**: the beam is a straight (or single-curve) glowing TUBE with a visible
  cylindrical cross-section — "concentric cylinders with diminishing strength" (Photo Props: Energy
  Beams). Constant diameter along its whole length, or one simple taper. It looks like a posed object.
- **Core/rim structure**: hard white-hot core cylinder + ONE colored outer sleeve (teal), inner
  visibly brighter than the outer (the canonical two-emissive-cylinder forum recipe). No graduated
  plasma gradient — two discrete layers, you can see the seam between them.
- **Edge quality**: crisp, almost vector-clean tube edges; the outer sleeve has a slightly granular
  transparency texture if anything. When the prop was bent with a morph the texture visibly stretches
  (a documented limitation of the morphing beams).
- **Contact point**: a separate **impact-tip prop** — a small sphere or simple spiked starburst sprite
  sitting AT the surface (SY Energy Beams' toggleable tip + "plain impact prop"). It hides the
  beam-end intersection. It does not splash, wrap, or scatter across the surface.
- **Flares**: at the muzzle, a flat lens-flare-ish starburst card; 4–8 spikes, perfectly symmetric.
- **Bloom**: ONE uniform soft halo around the whole beam, identical radius everywhere — screen-space
  bloom or a gaussian-blurred duplicate layer in Screen mode. The halo does NOT get occluded
  correctly: it can faintly cross in front of a shoulder that passes in front of the beam.
- **Scene lighting**: the beam barely illuminates anything. Maybe one modest teal tint on the nearest
  surfaces (artists fake it with a single colored point light near the prop, or skip it). Character
  shadows still come from the room's key light, not the beam. Thin beams were notoriously dim in
  Iray — under-lit surroundings are period-correct.
- **Compositing artifacts (desirable)**: beam reads as a layer OVER the render; where it meets bodies
  or props there's a clean hard intersection line, no contact glow gradient.

### T2 — Body electricity / skin shimmer

- **Geoshell look**: the glow is a SECOND SKIN floating ~2–3 mm off the body (PowerFist Plus geoshell,
  FPE Magic Effects skin shells). You can read the offset at silhouette edges — the glowing pattern
  hovers just above the skin rather than being IN it.
- **Pattern is a texture, not a simulation**: a repeating flame/electric filigree transparency map in
  ONE flat emissive color preset (PowerFist's Blue Flame / White Flame etc.). Uniform brightness across
  the whole patch — no hot spots, no energy "flowing." A tiling repeat is acceptable and authentic.
- **Hard alpha edges**: the filigree shapes cut off sharply (transparency map), with the bloom halo
  added on top as a separate uniform glow.
- **Zoned, not anatomical**: coverage follows toggle zones — left arm on/off, right arm on/off
  (PowerFist per-limb toggles; FPE LIE visibility masks "target specific areas of the body"). The
  pattern does NOT trace muscle striations, veins, or bone lines; it sits on the surface like a
  glowing sleeve and stops at a seam.
- **Discrete bolts, if any**: 2–5 separate small lightning bolts stamped near the limb — generic
  zigzag bolt shapes (Ron's Lightning FX brushes, Electric VFX 2D bolts), each a white core with a
  teal outer-glow layer style. They float a touch off the skin, don't connect end-to-end, and don't
  branch realistically. Identical bolt shapes may repeat at different scales/rotations.
- **Scene lighting**: the shimmer casts almost no light — a faint teal tint on the immediately
  adjacent skin at most. Ropes, clothing, the chair: unlit by it.

### T3 — Power-up aura

- **Duplicate-silhouette glow**: the classic in-render method is the character's own mesh duplicated,
  scaled up a few percent, emissive shader applied, sitting BEHIND the figure — so the aura is a
  glowing rim that exactly copies the body outline, evenly thick all the way around.
- **Postwork outer glow**: equally common is a pure Photoshop outer-glow layer style around the
  figure cutout — a soft, even, airbrushed halo in one color, like a sticker glow. Uniform width,
  no flicker structure, no licking flames unless individually brush-stamped.
- **Vertical streaks optional**: a few hand-placed plasma streaks rising off shoulders/hair (Ron's
  "plasma type streams" brushes) — discrete strokes, countable, not a continuous field.
- **Hair/cloth do NOT respond**: hair may be posed "floating" but it is not lit strand-by-strand and
  there's no field distortion. The aura is strictly an outline treatment.
- **Bloom**: same single uniform bloom pass as everything else; the aura and the beam share the
  identical halo radius because they went through the same filter.

### T4 — Force field

- **Concentric sphere layers**: 2–3 nested transparent SPHERES around the figure ("the layers are
  all 3d geometry, mostly spheres" — 3dxg Sci-fi Force Field, 24 items in 3 layers, sized to DAZ
  figures). Visibly geometric: you can see the sphere's curvature and where it intersects the floor.
- **Surface texture**: hex grid, ripple rings, or scanline transparency maps on the shells; one flat
  emissive color; brighter at the silhouette edge only because more layers overlap there — a fake,
  geometry-driven "fresnel," not a shaded one.
- **Hard floor intersection**: the sphere slices into the ground plane with a clean circle — no
  energy dissipation at the contact ring (an authentic tell).
- **Character inside reads normally lit** — the field tints them barely or not at all.

### T5 — Impact flash / shockwave

- **Flat transmapped card**: the flash is a 2D billboard — a symmetric starburst / spiky flare PNG
  standing at the impact point (SY KABOOM's 2D transmapped props; Energy Weapon Effects Vfx's 15
  "shots/muzzle effects" elements). From the camera it's a perfect flat sprite; it does not wrap the
  struck surface.
- **Spike structure**: 4, 6, or 8 clean symmetric spikes + a hot white center disc + teal fringe.
  Comic-poster, not photographic.
- **Shockwave**: a single thin glowing RING, perfectly circular, lying on one plane (ground or
  air), hard-edged with a touch of bloom — drawn in postwork or a flat torus prop. Plus brush-stamped
  debris specks/sparks (Electric VFX "sparks, embers") that are discrete dots, not motion-blurred.
- **No environmental response**: the flash doesn't blow out the exposure, doesn't cast shadows away
  from the impact, doesn't kick up correctly-lit dust. Maybe one stamped smoke billboard.

---

## 3. AI tells to avoid — BANNED LOOKS

Anything on this list = reject the panel and re-roll with the vocabulary blocks in §4.

1. **Volumetric beams** — participating media, visible light shafts with dust scatter, god-rays,
   internal turbulence, plasma "flow" along the beam.
2. **Anatomy-conforming electricity** — lightning that traces muscle contours, wraps around forearms
   like a wire, bridges finger-to-finger with physically plausible arcing, or branches fractally with
   correct dielectric-breakdown structure.
3. **Thousands of micro-filaments** — dense hair-fine energy tendrils with depth-of-field falloff.
   Human props max out at a handful of discrete, countable bolt shapes.
4. **Physically correct light spill** — the effect realistically illuminating faces with soft
   falloff, accurate colored bounce light, subsurface scatter glow through skin/ears, contact
   shadows cast BY the effect.
5. **Correct occlusion of glow** — halo precisely masked by foreground objects. (The human version's
   bloom leaks over occluders; a perfectly occluded glow is suspiciously right.)
6. **Fresnel-shaded force fields** — smooth view-angle-dependent shimmer, refraction of the
   background through the field, energy dissolving realistically where it meets surfaces.
7. **Cinematic grading driven by the effect** — teal-and-orange split toning, anamorphic streak
   flares, chromatic aberration on the flare, film-look halation tuned per shot.
8. **Continuous energy "wash"** — fields/auras as a coherent simulated fluid wrapping the figure,
   cloth and hair reacting to the field, strand-level rim lighting.
9. **Asymmetric, "directed" detail** — flares and impacts with naturalistic randomness and motion
   blur. Human sprites are symmetric, static, and reused.
10. **Exposure response** — the flash blooming the camera, auto-exposure dip, lens dirt catching
    the light.

Rule of thumb: **if the effect looks like it obeys physics, it's wrong. If it looks like a glowing
object somebody parented to the scene and then airbrushed, it's right.**

---

## 4. PROMPT VOCABULARY BLOCKS

Paste the positive block into the panel's action/effect fragment; append the negative block at the
prompt tail. Keep camera/lighting fragments untouched — these blocks describe the EFFECT ONLY.
(Refs-are-truth note: these are action/effect descriptors, not appearance walls — they describe what
the effect object is doing in frame.)

### T1 — Energy beam (ray-cannon)

**Positive:**
> a straight glowing emissive 3D prop tube of teal energy, hard-edged cylinder with a white-hot core
> and a single teal outer sleeve, constant thickness, like a DAZ Studio store effect prop posed in the
> scene; a simple symmetric sprite starburst flare at the muzzle and a small spiked impact-tip sprite
> where it touches; uniform soft postwork bloom halo around the whole beam; the glow barely
> illuminates the surroundings, faint flat teal tint on the nearest surfaces only, room lighting
> unchanged; the beam reads as a composited overlay layer on the render

**Negative:**
> not volumetric, no light shafts or god-rays, no plasma turbulence inside the beam, not physically
> accurate lighting, the beam does not realistically illuminate the characters, no cinematic VFX, no
> anamorphic lens flare, no chromatic aberration, no simulation-grade energy

### T2 — Body electricity / skin shimmer

**Positive:**
> a faint teal emissive geoshell glow hovering a few millimeters off the skin, a repeating hard-edged
> electric filigree pattern in one flat teal color like a glowing second-skin texture from a DAZ
> effect shell product, uniform brightness, covering the [forearms/shoulders] as a simple zone with a
> visible seam where it stops; two or three small separate stamped lightning bolt shapes floating just
> off the skin, white core with a teal outer-glow layer style, like Photoshop lightning brushes added
> in postwork; soft uniform bloom; the shimmer casts no light on clothing, ropes, or surroundings

**Negative:**
> not anatomy-conforming, the energy does not trace muscles or veins, no branching realistic
> lightning, no dense micro-filaments, not volumetric, no subsurface glow through the skin, the glow
> does not illuminate the scene, no cinematic color grading

### T3 — Power-up aura

**Positive:**
> an even teal outer-glow halo tracing the character's whole silhouette at constant width, like a
> scaled-up emissive duplicate of the figure placed behind her, plus a soft airbrushed postwork glow;
> three or four discrete hand-placed plasma streaks rising off the shoulders, countable separate
> strokes like Photoshop brush stamps; uniform bloom over the halo; the aura is an outline treatment
> only — her body, hair, and the floor stay lit by the room lights

**Negative:**
> not a simulated energy field, hair and cape do not react to the energy, no strand-level rim light,
> no swirling continuous plasma wrap, not volumetric, no physically accurate glow falloff, no
> cinematic grading

### T4 — Force field

**Positive:**
> two or three nested transparent glowing spheres around the figure, visible 3D geometry with a flat
> teal hex-grid transparency texture, brighter at the silhouette rim only where the layers overlap,
> like a DAZ store force-field prop scaled to the character; the sphere intersects the floor in a
> clean hard circle; mild uniform bloom on the shell edges; the character inside is lit normally by
> the room, the field adds almost no tint

**Negative:**
> no fresnel shading, no refraction or distortion of the background through the field, the field does
> not dissolve or ripple where objects touch it, not volumetric, no energy dissipation effects, not
> physically accurate

### T5 — Impact flash / shockwave

**Positive:**
> a flat symmetric sprite starburst at the impact point, six clean spikes, hot white center disc with
> a teal fringe, like a 2D transmapped effect card stood up in the scene facing camera; a single thin
> perfectly circular glowing shockwave ring on one flat plane, hard edge with slight bloom; a few
> discrete stamped spark dots; the flash does not change the scene's exposure or cast its own shadows

**Negative:**
> not a realistic explosion, no motion blur on the flash, no camera exposure bloom-out, no debris
> simulation, no volumetric dust catching light, the flash does not realistically illuminate the
> characters, no cinematic VFX

---

## 5. Three worked rewrites (this comic's beats)

### (a) Teal ray-cannon beam striking the hero's back — p17 beat (`pages-plan.json` /pages/3)

**BEFORE (current, AI-ish):**
> medium profile shot, depth-staged. A bald villain in a grey suit fires a chrome ray cannon; a male
> superhero in a blue chevron suit throws himself in front of a black-bob woman roped to a chair, a
> teal energy beam striking his back and refracting through his chest into her, both lit by the teal
> discharge. Concrete laboratory.

*Why it reads AI: "refracting through his chest" invites simulated transmission/scatter; "both lit by
the teal discharge" demands physically correct light spill — the two biggest tells.*

**AFTER (DAZ-prop):**
> medium profile shot, depth-staged. A bald villain in a grey suit fires a chrome ray cannon; a male
> superhero in a blue chevron suit throws himself in front of a black-bob woman roped to a chair. The
> beam is a straight glowing emissive 3D prop tube of teal energy, hard-edged with a white-hot core
> and one teal outer sleeve, constant thickness, like a DAZ Studio store effect prop posed in the
> scene; a simple symmetric sprite starburst where it hits his back, and a second shorter prop tube
> continuing from his chest toward her at a naive straight angle with a small spiked impact-tip
> sprite at her shoulder; uniform soft postwork bloom on both tubes; the glow barely illuminates
> them — a faint flat teal tint on his back and her face only, the lab's overhead floods stay the key
> light. Concrete laboratory. Not volumetric, no light shafts, not physically accurate lighting, the
> beam does not realistically illuminate the characters, no cinematic VFX.

### (b) Faint teal shimmer on bound Dana's forearms (`pages-plan.json` /pages/5)

**BEFORE (current, AI-ish):**
> tight medium-close-up, eye-level, asymmetric negative space. A beautiful black-bob woman with hazel
> eyes roped to a chair, flushed cheeks, wide eyes, breath caught, a faint teal shimmer crawling
> along her forearms under the ropes. Dim laboratory.

*Why it reads AI: "shimmer crawling along her forearms" generates anatomy-conforming micro-filaments
flowing over the skin — the signature banned look.*

**AFTER (DAZ-prop):**
> tight medium-close-up, eye-level, asymmetric negative space. A beautiful black-bob woman with hazel
> eyes roped to a chair, flushed cheeks, wide eyes, breath caught. On her forearms, a faint teal
> emissive geoshell glow hovering just off the skin: a repeating hard-edged electric filigree pattern
> in one flat teal color, uniform brightness, like a glowing second-skin effect shell from a DAZ
> store product, covering the forearms as a simple zone and stopping at the wrists; one or two tiny
> separate stamped lightning bolt shapes floating off the skin, white core with a teal outer-glow;
> soft uniform bloom; the shimmer casts no light on the ropes or her blouse. Dim laboratory. Not
> anatomy-conforming, no realistic branching lightning, not volumetric, the glow does not illuminate
> the scene.

### (c) Teal energy crackling across Dana's shoulders mid-embrace (`pages-plan.json` /pages/10)

**BEFORE (current, AI-ish):**
> medium-close-up three-quarter shot, mid-embrace. An athletic-muscular black-bob woman's eyes fly
> wide open against a male superhero's cheek, a teal shimmer reigniting and crawling along her
> shoulders, stronger. Dim laboratory.

*Why it reads AI: "reigniting and crawling… stronger" implies a continuous simulated field ramping in
intensity and flowing across anatomy, with implied light on both faces.*

**AFTER (DAZ-prop):**
> medium-close-up three-quarter shot, mid-embrace. An athletic-muscular black-bob woman's eyes fly
> wide open against a male superhero's cheek. Across her shoulders and upper arms, a brighter teal
> emissive geoshell glow: the same hard-edged flat-teal filigree pattern as before but denser, hovering
> just off the skin, uniform brightness, ending in a clean seam at her shoulder blades; three or four
> small separate stamped lightning bolts arcing a finger-width above her shoulders, generic zigzag
> shapes with white cores and teal outer-glow layer styles, like Photoshop lightning brushes added in
> postwork, two of them visibly the same shape at different sizes; soft uniform bloom; the crackle
> throws no light on his face or the room — the dim lab lighting is unchanged. Dim laboratory. Not
> anatomy-conforming, no realistic arcing between bodies, no micro-filaments, not volumetric, no
> cinematic VFX.

---

## Sources (key product/forum references)

- [SY Energy Beams Iray (Daz3D)](https://www.daz3d.com/sy-energy-beams-iray) — superposing beam prop,
  finger/palm/eye wearables, toggleable impact tip, color presets (arcane/blue/white/violet…), attack+hit poses
- [Photo Props: Energy Beams](https://posercontent.com/props-for-daz-studio-and-poser/photo-props-energy-beams) —
  "concentric cylinders with diminishing strength," fully emissive, bend/twist/wave morphs stretch textures, "render even better if you add a bloom post effect"
- [Raw Energy Effects (Daz3D)](https://www.daz3d.com/raw-energy-effects) — rigged stream figure + fireball prop,
  12 transparency-map styles (Electric, Energy, Plasma, Sparks…), Poser-era no-emission glow
- [PowerFist Plus for Genesis 3 (Daz3D)](https://www.daz3d.com/powerfist-plus-for-genesis-3) — emissive geoshell
  per-limb toggles, 8 flat flame colors, fireball prop (Electric/Fireball/Plasma), full-body shield mode
- [FPE Magic Effects for Genesis 9 (Daz3D)](https://www.daz3d.com/fpe-magic-effects-for-genesis-9) — magic skin
  shells, custom luminance maps, 14 emission colors, LIE zone masks
- [Electric VFX (Daz3D)](https://www.daz3d.com/electric-vfx) — 16 2D bolts / 14 3D props / sparks / VDB,
  bloom presets OFF–High "to match the promotional artwork"
- [Power Blast Props (Daz3D)](https://www.daz3d.com/power-blast-props-for-victoria-7-and-8-and-michael-7-and-8) —
  hand-parented smart props, Electric/Organic/Standard transparency-map styles
- [SY KABOOM Iray (Daz3D)](https://www.daz3d.com/sy-kaboom-iray) — "20 2D transmapped explosion" billboard cards + smoke props
- [Ron's Lightning FX (Daz3D / deviney)](https://www.daz3d.com/rons-lightning-fx) — 240 Photoshop brushes +
  22 "charged up" layer styles; sparks and "plasma type streams" stamped in postwork
- [Sci-fi Force Field (3dxg / RenderHub)](https://posercontent.com/sci-fi-force-field) — "layers are all 3d
  geometry, mostly spheres," 24 items in 3 nested scalable layers sized to DAZ figures
- [Energy Weapon Effects Vfx (3dexgraphics / Renderosity)](https://www.renderosity.com/marketplace/products/170920/energy-weapon-effects-vfx) —
  15 placeable shot/muzzle effect elements
- [Daz forum: laser light effects](https://www.daz3d.com/forums/discussion/631151/best-method-or-product-to-produce-spectacular-laser-light-effects) —
  "two emissive cylinders with the inner brighter than the outer and a subtle bloom effect"; thin beams barely light scenes
- [Daz forum: aura glow](https://www.daz3d.com/forums/discussion/226606/how-to-make-an-aura-type-glow-around-a-character) —
  "DAZ Studio is very limited for effects"; postwork brushes "your best bet"; scaled emissive duplicate method
- [Daz forum: Energy FX for Iray](https://www.daz3d.com/forums/discussion/64587/energy-fx-for-iray) — emissive-glow-match
  demand, bloom utility presets
- DeviantArt: [muscle-fan-comics](https://www.deviantart.com/muscle-fan-comics/art/Female-Muscle-Growth-Contamination-Spread-1125414121) and the
  [musclegrowthcomic tag](https://www.deviantart.com/tag/musclegrowthcomic) — genre covers composite exactly these store
  effects: brush-stamped bolts + outer-glow auras over DAZ renders
