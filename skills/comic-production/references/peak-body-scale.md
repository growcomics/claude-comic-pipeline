# Peak Body Scale — Cartoony FMG Muscular Build

The intended aesthetic for this pipeline's transformation comics is **cartoony hyper-FMG** — exaggerated comic-book musculature with heavy 3D muscle volume, not realistic fitness modelling. Without explicit anchoring the model defaults to plausible-fitness proportions, which read as visibly *smaller* than the target on every tier ≥ 4.

This guide pairs with `assets/muscle-size-lineup.png` (tiers 1–6) and `assets/muscle-size-lineup-4-9.png` (tiers 4–9). Those are the canonical visual anchors — every stage-change panel and every full-body panel of the arc character must attach one of them.

---

## What the lineup actually is

![Muscle-size lineup — 6 figures, tier 1 through tier 6](../assets/muscle-size-lineup.png)

**The lineup is a 3D body chart with six figures showing TWO progressively-scaled proportion attributes per tier.** Each figure is a DAZ3D-style render in a double-bicep pose, showing visible:

**Attribute 1: muscle scale**

- Deltoid mass and separation
- Bicep peak and thickness
- Chest depth
- Abdominal definition
- Lat width / V-taper
- Quad mass
- Frame width and shoulder-to-waist ratio

**Attribute 2: breast scale (anchored as of 2026-05-16 afternoon, Alignment Diff #3)**

- Breast size (visible volume from the chest)
- Breast fullness (rounded vs. flat profile)
- Breast forward projection (how far they project forward from the rib cage)

Both attributes scale per tier — figure 6 has visibly larger and more forward-projected breasts than figure 1 IN ADDITION TO larger muscle mass. The chart conveys breast scaling more subtly than muscle scaling (the figures wear shirts that partially cover the breast contour), so the prompt vocabulary must compensate by explicitly telling the model that breasts are a load-bearing attribute the lineup encodes — see "How to anchor" below.

**It is NOT a silhouette reference.** A silhouette is a flat outline against a background — that would tell the model "match the outline shape, ignore the muscle." This is the opposite: a chart of rendered 3D body proportions (muscle volume AND breast scale) that the model is supposed to MATCH, in mass and definition and breast scale, not just in outline width.

**It is NOT a face / hair / costume / pose reference.** All six figures share the same face, hair, t-shirt, shorts, and double-bicep pose. Those are constants in the chart, not anchored attributes. The lineup conveys ONLY the two proportion attributes above; everything else comes from the character's own face card / wardrobe description / shotlist.

This distinction is load-bearing. Vocabulary like *"match the silhouette of figure N"* causes nano_banana_flash to interpret the reference as outline-only — getting the shoulder width roughly right while skipping the actual muscle mass. Vocabulary that mentions breasts only as a passing list item ("the size, fullness, and shape of the breasts") causes nano_banana_2 to default to average / conservative breast size even at tier 4-6. The vocabulary that works points at BOTH attributes with caps-lock framing and explicit "do not regress" guards: *"CRITICAL — MUSCLE: match the 3D muscle mass of figure N, not just the outline width"* AND *"CRITICAL — BREASTS: match the BREAST SIZE, FULLNESS, and forward PROJECTION of figure N — do NOT regress to a smaller tier's breast proportions."*

---

## The two bundled lineups

| File | Tiers shown | When to attach |
|---|---|---|
| `assets/muscle-size-lineup.png` | 1, 2, 3, 4, 5, 6 | Default for tiers 1–6. Use for all comics targeting up to tier 6 peak. |
| `assets/muscle-size-lineup-4-9.png` | 4, 5, 6, 7, 8, 9 | For comics escalating beyond tier 6. Use on any panel where the arc character is at tier ≥ 7. |

Picking between them at runtime: `find_lineup(root, tier)` in `next_panel.py` returns the `1-6` file for `tier < 7` and the `4-9` file otherwise.

---

## Tier-6 reinforcement refs (L29, added 2026-05-16)

Empirically, the multi-figure lineup alone under-renders tier-6 proportions: the model averages across the six visible figures and the rendered tier-6 body lands closer to tier 4-5. To fix this, every panel at `muscle_size_tier == 6` attaches two dedicated tier-6 reference sheets ALONGSIDE the lineup.

| File | What it shows | Role |
|---|---|---|
| `peak-body-scale/tier-6/tier-6-full-body.png` | Front + rear full-body refs with annotated proportion stats (biceps profile, chest / thoracic detail, waist narrowness, leg musculature) | Overall tier-6 proportions and frame-width anchor |
| `peak-body-scale/tier-6/tier-6-anatomical-detail.png` | Close-up anatomical detail sheet — biceps anatomy, breast volume / shape, waistline metrics, full rear view + posterior musculature | Detail anchor for the muscle groups the lineup conveys less precisely |

### Why they exist alongside the lineup

The lineup still attaches — L11 is unchanged. Without the lineup the model loses tier *context* (figure 6 relative to figures 1-5). The reinforcement sheets supply the *isolated* tier-6 anatomical truth that the multi-figure chart can't carry on its own. Both anchors together: the lineup says "tier 6 is the right step on the ladder," and the reinforcement refs say "this is what step 6 actually looks like, in detail."

### Attachment rule (per L29)

When `panel.muscle_size_tier == 6`, BOTH reinforcement PNGs attach automatically in addition to the lineup. `next_panel.py`'s `should_attach_tier6_reinforcement()` decides this; `find_tier6_reinforcement_refs()` resolves them from (in order): project `references/style/` override, repo-bundled `skills/comic-production/references/peak-body-scale/tier-6/`, user-installed skill path, plugin-installed skill path.

The reinforcement refs are repo-bundled, not character-specific generated assets. They do NOT go through `reference-gathering` generation — the manifest just flags that the panel-level renderer must attach them.

### Surgical-scoping language (L29 directive)

The reinforcement refs inherit the L11 surgical-scoping pattern verbatim. The directive emitted at slot `8b_tier_reinforcement` says, in essence:

> TIER-6 PROPORTION REINFORCEMENT: Two additional reference images attached showing canonical tier-6 muscle proportions. Match the bust volume and forward projection, deltoid mass, pectoral development, lat spread, oblique definition, bicep peak / thickness, and quad size shown in these references — and **over-render**: the model normalizes off-distribution features toward average, so target the SAME or LARGER scale than the reinforcement refs show, never smaller. **PROPORTION REFERENCE ONLY** — do NOT adopt the clothing, hair, hairstyle, hair color, skin tone, face, pose, lighting, background, or setting from these references. Do NOT render the reference images as physical scene objects (no inset photos, no annotated overlays, no figure labels, no proportion stats text floating in the frame). Borrow scale and mass only.

The do-NOT-borrow list is identical in shape to the L11 list — single-figure refs are even more prone to leakage than the 6-figure chart, so the surgical scoping has to be at least as strict.

### Over-spec is intentional

Per the `feedback_chest_oversize_compensate` lesson, the model normalizes off-distribution features (heavy musculature, large breasts) toward the population average. To land at parity, the prompt asks for *larger* than the ref shows. The L29 directive explicitly tells the model "target the SAME or LARGER scale than the reinforcement refs show, never smaller" — over-spec, not match.

### Audit gate

`rules_audit.py` HARD-fails when any panel has `muscle_size_tier == 6` and the reinforcement PNGs aren't findable on disk via the canonical search order. This blocks the render plan; it doesn't just warn. Reason: tier-6 lineup-only fallback has a known regression that the reinforcement refs exist to fix, so rendering tier-6 without them ships a known failure.

---

## Tier-7 reinforcement refs (L30, added 2026-05-16 evening)

The same multi-figure interpolation failure exists at tier 7 on the `muscle-size-lineup-4-9.png` chart. L30 fixes it the same way L29 fixed tier 6: keep the lineup attached, additionally attach two dedicated tier-7 reference sheets generated 2026-05-16 evening using Mira as the source character.

| File | What it shows | Role |
|---|---|---|
| `peak-body-scale/tier-7/tier-7-full-body.png` | Front + rear full-body refs with annotated proportion stats (TIER 7 / REAR VIEW headers, biceps profile, chest / thoracic detail, waist narrowness, leg musculature) | Beyond-peak proportions and frame-width anchor |
| `peak-body-scale/tier-7/tier-7-anatomical-detail.png` | Close-up anatomical detail sheet — biceps anatomy, breast volume / shape, waistline metrics with dimensional callouts, full rear view + posterior musculature | Detail anchor for the muscle groups the lineup-4-9 chart can't isolate |

Generation procedure: 16 Higgsfield gens (8 per sheet) using `nano_banana_flash` 1k with Mira's character ref as identity anchor and the tier-6-full-body sheet as STYLE anchor (per L11 surgical scoping — borrow style only, never proportions). User picked 1 of 8 per sheet manually. Picks: Sheet A `fb14428d`, Sheet B `3beb5bbd`. Yield was 11/16 successful (2 NSFW filtered at gen time, 3 platform-failed). 5 unsuccessful gens are documented in [`docs/posts/2026-05-16-tier-7-candidates/`](../../../docs/posts/2026-05-16-tier-7-candidates/) for reference. Credit cost: ~50.

### Attachment + audit gates

Mirror L29 exactly: `should_attach_tier7_reinforcement()` fires at `muscle_size_tier == 7`, `find_tier7_reinforcement_refs()` resolves via project override → repo-bundled → user-installed → plugin-installed paths, `rules_audit.py` HARD-fails on missing PNGs at the per-panel and manifest-level gates.

### Open question for future tiers (8, 9)

Same pattern — sibling rule modules (L31 tier-8, L32 tier-9) with dedicated reference sheets. Generation batches in flight using the same Mira source character + recipe. Empirical validation per tier before declaring each one shipped.

---

## Tier-8 reinforcement refs (L31, added 2026-05-16 evening)

Same multi-figure interpolation failure at tier 8. L31 fixes it the same way L29/L30 fixed tier 6/7 — keep the lineup attached, additionally attach two dedicated tier-8 reference sheets.

| File | What it shows | Role |
|---|---|---|
| `peak-body-scale/tier-8/tier-8-full-body.png` | Front + rear full-body with annotated proportion stats: DELTOIDS Massive 3x, MAXIMAL Quad Volume, Bicep Profile, Waist Narrowness, Leg Musculature | Super-peak proportions anchor |
| `peak-body-scale/tier-8/tier-8-anatomical-detail.png` | Close-up sheet with VANISHINGLY NARROW WAIST callout, Tier 8 breast detail (larger, fuller, more projected), bicep close-up, full rear posterior detail | Detail anchor with extreme proportion callouts |

Generation procedure mirrors tier 7. 16 gens (8 per sheet) on `nano_banana_flash` 1k with Mira as identity anchor and tier-6-full-body sheet as STYLE anchor; prompt instructs "render TWO TIERS bigger than reference #2 (tier-6 baseline)." User picked Sheet A `7c0d52dd`, Sheet B `6072b6d6` from 14 successful candidates (1 NSFW filtered, 1 platform-failed). Credit cost: ~50.

### Attachment + audit gates

Same shape as L29/L30: `should_attach_tier8_reinforcement()` fires at `muscle_size_tier == 8`, `find_tier8_reinforcement_refs()` resolves via the shared `_find_peak_reinforcement_refs(root, 8)` helper, HARD audit gate in `rules_audit.py`.

### Open question for tier 9

Sibling L32 module. Same recipe; will execute next.

---

## What the tiers mean

Each tier is a **muscular-build target** — what muscle mass, definition, and frame width does figure N show? Reading the lineup left-to-right:

| Tier | What it shows | Real-world analog (very rough) |
|---|---|---|
| 1 | Baseline athletic — slim, healthy, no developed muscle mass | normal fit civilian |
| 2 | Visibly developed — defined deltoid mass beginning to show, small bicep peak, tighter midsection with hint of abdominal definition | fitness-magazine athletic |
| 3 | Clearly muscular — broad deltoids with clear separation, defined bicep peaks, full chest, visible abdominal definition, noticeable quad mass | strong amateur athlete |
| 4 | **Cartoony threshold** — deltoids 2× normal mass with clear striation, biceps with visible peaks and triceps mass, full powerful chest pushing fabric, ridged 6-pack abdominal definition, strong sculpted quads, hip flare. THICK 3D muscle volume, not just a wider outline | hyper-developed comic-book hero |
| 5 | Massive — deltoids 2.5× normal mass, huge sculpted biceps with deep peaks and visible vascularity, deep powerful chest with separation, blocky 8-pack abdominal definition, powerful sculpted quads with hamstring detail. HEAVY 3D muscle volume visible from every angle | She-Hulk territory |
| 6 | Peak — deltoids 3× normal mass dwarfing the head, biceps as wide as the waist, full hyper-muscular build with every muscle group visibly developed and individually defined. MAXIMAL 3D muscle volume | comic peak |
| 7 | Beyond peak — proportions exaggerated past realism, frame-filling cartoony FMG muscle mass, biceps approach waist width, every muscle group massively developed with clear striation | superpowered female |
| 8 | Super-peak — deltoids dwarf the head, biceps wider than the waist, pure comic-fantasy proportions with maximal muscle volume | full FMG fantasy |
| 9 | Maximum — pure FMG-comic exaggeration, near-total muscle dominance over the frame, every muscle group at maximal volume and definition | maximum cartoony |

**Tier 4 is the threshold the model usually fails to clear** without aggressive prompting. It's the tier most comics center on, and the one where "match the lineup figure's muscle mass" matters most. Tier 1–3 the model handles fine; tier 5+ is so visibly exaggerated that the lineup carries the day naturally **when the prompt vocabulary points at muscle volume**. Tier 4 is the friction zone.

---

## How to anchor the muscular build in a prompt

### The wrong way (legacy "silhouette" vocabulary, do NOT use)

> "Subject at tier 4. Match the silhouette of figure 4 in the attached lineup."

This causes a documented failure mode: the model reads "silhouette" as *outline shape*, gets the shoulder width roughly right, and renders a fitness-model body at wider proportions. The muscle mass, definition, and 3D volume that figure 4 actually shows on the chart get skipped. **Verified across multiple test runs in 2026-05** — every tier ≥ 4 panel rendered this way regressed toward "athletic at wider scale" instead of "cartoony FMG."

### The right way (current vocabulary, two parallel CRITICAL blocks)

> "Cartoony hyper-FMG comic-book proportions with HEAVY 3D muscle volume AND tier-scaled breast proportions, tier 4. The attached lineup is a 3D BODY CHART showing six figures with TWO progressively-scaled proportion attributes per tier: muscle mass AND breast scale. It is a PROPORTION reference ONLY (NOT an outline reference, NOT a face / hair / costume reference). CRITICAL — MUSCLE: Match the 3D MUSCLE VOLUME of figure 4: deltoids 2× normal MASS (not just 2× outline width) with visible striation, biceps with peaks and triceps mass, full powerful chest, ridged abdominal definition, strong sculpted quads. Render with the SAME thick muscle mass, same striation, same chest depth, same arm thickness that figure 4 shows. CRITICAL — BREASTS: Match the BREAST SIZE, FULLNESS, and forward PROJECTION of figure 4 EXACTLY. The lineup scales breasts proportionally to muscle tier — render the breasts at the SAME visible volume, SAME fullness, SAME forward projection that figure 4 shows. Do NOT default to average / conservative breast size; do NOT render the body at tier 4 muscle mass with breasts shrunk to tier 2 size. NOT realistic fitness, NOT athletic, NOT a fitness model at wider scale, NOT bigger muscles with conservative breasts — cartoony FMG with HEAVY 3D muscle mass AND lineup-matched breast scale."

### Aggressive vocabulary that works

**For muscle scale:**

- "cartoony hyper-FMG muscular build"
- "comic-book proportions with HEAVY 3D muscle mass"
- "CRITICAL — MUSCLE: match the 3D MUSCLE VOLUME of figure N"
- "the lineup is a 3D BODY CHART, NOT an outline reference"
- "deltoids Nx normal MASS (not just Nx outline width)"
- "thick muscle mass, visible striation, deep chest, defined abs"
- "NOT realistic fitness, NOT a fitness model at wider scale"
- Explicit muscle-group enumeration: deltoids, biceps, triceps, chest, lats, abs, quads

**For breast scale (added 2026-05-16 afternoon, Alignment Diff #3):**

- "tier-scaled breast proportions"
- "CRITICAL — BREASTS: match the BREAST SIZE, FULLNESS, and forward PROJECTION of figure N"
- "the lineup scales breasts proportionally to muscle tier"
- "render the breasts at the SAME visible volume, SAME fullness, SAME forward projection that figure N shows"
- "do NOT default to average / conservative breast size"
- "do NOT render tier N muscle mass with breasts shrunk to tier 2 or 3 size"
- "breast scale is a LOAD-BEARING attribute of the lineup, not an afterthought"
- "NOT bigger muscles with conservative breasts"

### Vocabulary to avoid

- **"silhouette" anywhere it points at the body reference** — the model reads it as outline-only. Use "muscular build" or "physique" or "3D muscle volume" instead.
- "athletic" / "fit" / "toned" — pulls back toward realistic fitness modelling.
- "muscular" alone (too tame; pair with "hyper-" or "cartoony" or "comic-book").
- Soft hedges ("a bit more developed", "stronger than before", "natural-sized breasts", "modest").
- "Outline" or "shape" when describing what to match — the chart shows volume, not shape.
- Breasts mentioned only as a passing list item ("the size, fullness, and shape of the breasts") with no CAPS-LOCK framing and no "do not regress" guard — the pre-2026-05-16-afternoon vocabulary did this and nano_banana_2 still defaulted to average breast scale.

---

## Attachment rule (per L11)

The muscle-size lineup must be attached on:

1. **Every stage-change panel** (where `muscle_size_tier` differs from the prior accepted panel's tier). Always, no exception.
2. **Every full-body camera panel of the arc character.** Cameras that qualify: `front-full`, `3q-full`, `side-full`, `back-full`, `low-angle-front`, `low-angle-back`, `splash`. Reason: when the body is the focal subject, the lineup keeps the muscular build honest. ECU and mcu panels skip it (size isn't the focal element).

`next_panel.py`'s `should_attach_lineup()` decides this automatically.

The old rule (L5: "lineup only on stage-change") was a cost-cutting heuristic from the Higgsfield era when refs cost money. On Flow, refs are free and the consistency gain is enormous. The new rule trades a slight composition-influence risk for substantial muscular-build consistency — the right trade.

---

## Failure modes to watch for

After generation, when reviewing a panel against its tier:

1. **Muscle-tier undershoot** — the rendered build looks one or two tiers smaller than declared (e.g. tier 5 reads as tier 3-4 fitness model). Most common at tier 4-6. **The 2026-05-16 morning diagnosis**: this is almost always a vocabulary failure — the prompt used "silhouette" instead of "muscular build," and the model matched the outline width while skipping the muscle volume. Fix: ensure the prompt uses muscle-mass / 3D-volume language and the explicit framing *"the lineup is a 3D body chart, NOT an outline reference."*

2. **Breast-scale undershoot (added 2026-05-16 afternoon, Alignment Diff #3)** — the rendered body has the correct tier-N muscle mass but the breasts render at tier 2-3 size (visibly smaller, less full, less forward-projected than figure N in the lineup shows). Common when the prompt mentions breasts only as a passing list item without CAPS-LOCK framing or "do not regress" guards. **The 2026-05-16 afternoon diagnosis** (after user test): even the user's explicit prompt *"match the breast size of the sixth person in the muscle comparison chart"* landed with smaller breasts than figure 6 shows, because the surgical-scoping pattern that fixed muscle hadn't yet been applied to breasts. Fix: use the parallel **CRITICAL — BREASTS** directive in the prompt — *"match the BREAST SIZE, FULLNESS, and forward PROJECTION of figure N EXACTLY; do NOT default to average / conservative breast size; do NOT render tier N muscle mass with breasts shrunk to tier 2 or 3 size; breast scale is a LOAD-BEARING attribute of the lineup, not an afterthought."*

3. **Lineup ignored / interpolated** — the model rendered a build that splits the difference between two lineup figures. Indicates the prompt's "match figure N" directive was outweighed by competing language elsewhere. Fix: simplify the prompt; the two CRITICAL directives (muscle + breasts) must dominate.

4. **Tier drift across the issue** — first panel after the stage-change matches the target, but subsequent panels regress smaller as the chain carries forward an interpolated build. Fix: attach the lineup on every full-body panel, not just stage-change.

5. **Realistic-fitness regression** — the panel looks muscular but plausibly real, not cartoony. The muscle volume is there but it reads as a real bodybuilder rather than comic-book exaggerated. Indicates the "NOT realistic fitness, NOT a fitness model at wider scale" anchor was missing or buried. Fix: lead with the cartoony anchor and include the explicit negation.

6. **Bigger muscles with conservative breasts** — the rendered body has tier-N muscle mass AND a realistic-fitness model's breasts. Distinct from #2 (where breasts undershoot tier-N) — this is the model averaging breast scale to "what would look natural on this muscular body" instead of "what the lineup figure N shows." Same fix as #2: use the **CRITICAL — BREASTS** directive AND the explicit negation *"NOT bigger muscles with conservative breasts."*

---

## Connection to the broader prompt skeleton

This guide updates the delta-only prompt skeleton from L10 with an explicit muscular-build anchor. The order in `compose_prompt()` is:

1. Render anchor (CGI vocabulary)
2. Camera fragment
3. **Cartoony FMG style anchor (L11)** — when the panel has a tier ≥ 2 for the arc character (slot `5_style_anchor`)
4. Subjects + delta action
5. Lighting state change
6. **Muscular-build directive (L11)** — tier-specific build descriptor with explicit 3D-body-chart framing (slot `8_tier_build`)
7. Location / env chaining
8. State anchor
9. Render directive (refs are truth)
10. Mandatory rules
11. Closing CGI anchor

The L11 anchors are *additive* — they don't replace any existing block. The style anchor slots between the camera fragment and the action delta (so the model commits to the cartoony aesthetic before reading action content); the muscular-build directive slots after the action delta and lighting (so the model has all the per-panel context before being given the muscle-mass target).

---

## History — the "silhouette" purge (2026-05-16 morning)

The original L11 reference doc (and the L11 module, and every doc that cited L11) used the word **"silhouette"** to describe what the lineup was showing. That word was load-bearing in the wrong direction: nano_banana_flash interpreted it as *outline shape*, which is exactly what the lineup is NOT. Every tier ≥ 4 panel rendered with the "silhouette" vocabulary regressed toward fitness-model proportions with the right outline width but missing muscle mass.

Diagnosed during the running comic-test-log thread on 2026-05-16 (Test 1 + Test 2 both showed the same failure pattern; user review pointed out the lineup is a 3D body chart, not a silhouette). Validated on the 3 worst L11 fails (p13/p14/p15 of Test 2) — same character, same lineup attached, same camera, only the prompt vocabulary changed from "silhouette" to "muscular build / 3D muscle volume" — and the muscle mass landed visibly closer to the lineup figure on the v3 re-render.

171 occurrences of "silhouette" were swept across the pipeline as part of the purge. The full diff is in the [comic-test-log thread, alignment diff #2](../../../docs/posts/2026-05-16-comic-test-log.md#alignment-diff-2-after-user-review-2).

## History — the breast-scale anchoring (2026-05-16 afternoon, Alignment Diff #3)

Even after the silhouette purge, the breast scale of generated panels still landed visibly smaller than what figure N in the lineup shows. User-confirmed observation: *"There is a problem with the generations in that it seldom matches the breast size of the reference attached. I did a prompt where I asked it to match the breast size of the sixth person in the muscle comparison chart and the rendered output still landed with smaller breasts than the lineup figure shows."* Tested on Higgsfield with nano_banana_2 at 1k, with the user's explicit `"Make sure the breast size of Chun Li matches that exactly of the sixth person in the muscle comparison chart"` prompt — muscular build came through correctly at tier 6 (the silhouette purge was holding) but breasts rendered at tier 2-3 size.

Diagnosis: the lineup conveys TWO proportion attributes (muscle scale AND breast scale), but the post-silhouette-purge vocabulary called out only muscle with caps-lock framing and "do not regress" guards. Breasts were mentioned as a passing list item ("(b) the size, fullness, and shape of the breasts") buried inside a three-part list and never given the same surgical-scoping treatment muscle got. nano_banana_2 reliably matched muscle scale at tier 4-6 but defaulted to average / conservative breast scale.

Fix: promote breast scale to a first-class anchor with the same surgical-scoping pattern that worked for muscle:

1. Style anchor mention — *"cartoony hyper-FMG comic-book proportions with HEAVY 3D muscle volume AND tier-scaled breast proportions"*.
2. Re-framing of what the lineup is — *"a 3D BODY CHART showing TWO progressively-scaled attributes per tier: muscle mass AND breast scale"*.
3. Parallel **CRITICAL — BREASTS** block alongside the existing **CRITICAL — MUSCLE** block.
4. Explicit "do not regress" guard — *"do NOT default to average / conservative breast size; do NOT render tier N muscle mass with breasts shrunk to tier 2 or 3 size"*.
5. Stage-change verbal-fallback mention.
6. Vision-rubric verification of BOTH attributes.

Files swept: `rules/l11_muscular_build.py` (style anchor + lineup-attached block + stage-change block + vision rubric + retry strategy), `references/lessons-learned.md` (L11 section), `references/peak-body-scale.md` (this doc), `references/the-rules-explained.md` (L11 section), `skills/reference-gathering/SKILL.md` (Step 2 lineup instruction), `commands/build-comic.md` (L11 bullet).
