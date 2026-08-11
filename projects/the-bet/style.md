# Style Lock — the-bet ("THE BET")

Locked 2026-06-29. Every panel prompt MUST include the prefix, suffix and negative
below verbatim. This project is photorealistic DAZ3D 3D rendering on all bodies,
clothing, props and environment — NOT ink-line, NOT anime, NOT painterly.
The ONLY 2D element permitted is the flat comic speech bubbles / captions / SFX
(L19-baked — see Lettering in shotlist.json).

## Model
- Name: Nano Banana 2 / Pro (Flow, free on Pro). Use Nano Banana **Pro** for the two
  full-page splashes (P9, P13) and the REF stage-change panels (P5, P7, P12);
  Nano Banana 2 for the rest. Pro is daily-quota'd — if exhausted, fall back to NB2.
- Aspect: **3:4 portrait** default. P1 is **wide → 4:3**. P9 and P13 are full-page
  splashes → **3:4** (Flow fixed ratios; portrait splash). P12 extreme-closeup → 3:4.
- Count: one image per submit; fan out variants via verbatim re-run on weak results.

## Mandatory prompt prefix
> Hyperrealistic DAZ3D Studio Iray 3D CGI render, ray-traced subsurface scattering on skin, physically-based rendering, 8K texture detail, photographic CGI, 3D Muscle Comics house style,

## Mandatory prompt suffix
> photorealistic skin micro-detail with visible pores, soft cinematic lighting,
> dramatic key plus rim light, gentle bloom, shallow depth of field,
> no painterly softness, no cel shading, no watermarks, no logos.

## Mandatory negative prompt
> cartoon body, anime, 2D illustration of the figures, painting, watercolor, ink-line characters,
> cel-shaded skin, plastic skin, oversmoothed, flat front-on flash lighting, watermark, logo,
> deformed hands, extra limbs, child, teen, underage, nudity, exposed breasts.

## Aesthetic anchor — DAZ3D look
Bodies and rooms read like a rendered DAZ3D Iray scene: real skin SSS, soft global
illumination, modeled (slightly clean) furniture, realistic muscle/skin sheen.
Source real DAZ3D-style scene references from the web per environment-references.md,
build NEW original locations in Flow off that look — do not copy any source.

## Cast identity (HARD rules — identity, not mood)
- **CASSIE** — adult woman, 25 (NOT teen — rule_comic_adult_only). ~5'2" (short, the
  comedy of scale depends on her reading TINY early). Light-brown shoulder-length hair,
  freckles across nose/cheeks. Baseline size 1 (slim, no visible muscle). Grows 1 → 6.
  Wardrobe arc: oversized grey hoodie / baggy tee (P1–P4, swamped, sleeves past hands) →
  fitted tee (mid) → torn-tee remnants at top sizes. Damage = remnants only, always covers
  (rule 4 / L4). Never reverts a size once reached (rule 10).
- **NADIA** — adult woman, 25. Taller ~5'10", dark hair in a high ponytail, fitted
  athletic tank / activewear. **Size 3 the ENTIRE run — never grows, never shrinks.**
  She is the fixed ruler; Cassie is the only variable. Early she dwarfs Cassie; by the
  end Cassie dwarfs her — the contrast does the storytelling.

## Size control (muscle lineup ref method — Key Rule #7)
- Master size anchor = `assets/muscle-size-lineup.png` (numbered figures 1–6).
- Build a **Cassie-specific 1–6 lineup** up front (her face/hair/freckles on the 6 tiers)
  so identity holds across sizes; use it as the size ref on REF panels.
- Attach the lineup on the ⟶REF stage-change panels only: **P5, P7, P9, P12**. Call out
  the size number explicitly. Muscle + breast + waist read from the SAME tier (in sync).
- Size cadence (per panel): 1,1,1,1,2,2,3,3,4,4,4,(5→6),6,6,6.
- **No reversion** — once Cassie hits a size she never reads smaller (rule 10).

## Scale-constancy (L37 corollary)
Only Cassie's scale moves. Nadia stays a fixed real size (size-3 build, ~5'10") and is
scaled to room anchors (table height, bar counter, doorway) identically every panel —
she must NOT appear to shrink. The room/furniture is the fixed ruler; Cassie is the
only variable. Bake explicit clamps on contrast panels (P9, P11, P13, P14, P15).

## Body-orientation variety (L37 anti-AI)
Vary body orientation, not just camera. No more than ~2 consecutive front-facing panels.
Work in at least one 3q-rear / back and one profile / over-shoulder per ~5-panel run.
No direct camera eye contact (rule 8) — characters look at each other.

## Lettering
L19-baked — flat 2D comic bubbles + yellow caption boxes + 2D SFX rendered into each
panel at generation time. Bodies/rooms stay photoreal DAZ3D. One bubble per speaker,
minimal text, correct attribution (rule 5/6). See shotlist.json `lettering`.
