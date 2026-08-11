# Style Lock — goth-witch-growth ("Bigger Plans")

Locked 2026-06-22. Every panel prompt MUST include the prefix and suffix below
verbatim. This project is photorealistic DAZ3D 3D rendering on all bodies,
clothing, props and environment — NOT ink-line, NOT anime, NOT painterly.
The ONLY 2D element permitted is the flat black-and-white comic speech bubbles
(L19-baked — see Lettering).

## Model
- Name: Nano Banana 2 / Pro (Flow). Use Nano Banana Pro for hero/splash panels (p05, p07, p09), Nano Banana 2 for the rest.
- Aspect: 3:4 portrait for standard/close panels; the splash p09 may use 3:4 as well (Flow fixed ratios). Wides (p01,p06,p08,p10) use 4:3.
- Count: one image per submit; fan out variants via verbatim re-run on weak first results.

## Mandatory prompt prefix
> Hyperrealistic DAZ3D Studio Iray 3D CGI render, ray-traced subsurface scattering on skin, physically-based rendering, 8K texture detail, photographic CGI, 3D Muscle Comics house style,

## Mandatory prompt suffix
> photorealistic skin micro-detail with visible pores, soft cinematic indoor lighting,
> warm candle key light plus cool violet rim light, gentle bloom, shallow depth of field,
> no painterly softness, no cel shading, no watermarks, no logos.

## Mandatory negative prompt
> cartoon body, anime, 2D illustration of the figures, painting, watercolor, ink-line characters,
> cel-shaded skin, plastic skin, oversmoothed, flat front-on flash lighting, watermark, logo,
> deformed hands, extra limbs, child, teen, underage.

## Aesthetic anchor — DAZ3D look
Bodies and room read like a rendered DAZ3D Iray scene: real skin SSS, soft global
illumination, modeled (slightly clean/uncluttered) furniture, gentle bloom on candle
flames. Source one real DAZ3D interior render from the web as an environment reference,
then build a NEW original gothic loft in Flow off that look — do not copy the source.

## Character identity colors (HARD rules — identity, not mood)
- **Luna's** magic / eye glow / aura: **violet-purple** (#7A2BE2–#B06CF0). Every powered
  panel (p03, p04, p05, p07, p09) must name the violet glow explicitly. Never another color.
- Luna is an ADULT woman, 25. Ethan is an ADULT man, 25. Every prompt states adult.

## Scale continuity (size arc — this project's tiers)
Macro / giantess size growth. Tiers per `shotlist.json` transformation_metadata:
1 baseline → 2 head-taller → 3 ~2.5m → 4 ~3.5m → 5 ~5m (hunched under beams) → 6 room-filling.
Monotonic: a panel's tier is always >= the previous panel's. Luna NEVER shrinks.
Growth is curvy/sexy (fuller bust, hips, thighs; hourglass kept) — NO muscle, NO red skin.
Use the burgundy couch and the ceiling beams as in-frame scale anchors.

## Wardrobe state
Luna: black corset minidress (lace-up front), pentacle choker, fishnet sleeves, platform
boots. As tier rises the dress stretches and strains at the seams, laces pull tight, hem
rides up — but ALWAYS fully covers her (L4). Ethan: grey hoodie, tee, jeans, sneakers,
round glasses — unchanged; cheeks get progressively redder.

## Lettering — L19 BAKED (this project, per user request)
Speech bubbles ARE baked into each render at generation time (NOT post-composited).
- Style: classic black-and-white 2D comic balloons — clean WHITE rounded ovals, bold
  3–4px solid BLACK outline, ALL-CAPS bold black comic display font (Bangers-style),
  short triangular black-outlined tail pointing to the correct speaker's mouth.
- Flat 2D overlay ONLY: no 3D shading, no bevel, no translucency, no drop shadow onto the scene.
- Bubble shape by type: balloon = rounded oval; thought = cloud w/ trail; shout = jagged starburst.
- SFX: flat 2D bold black or white ALL-CAPS comic display lettering, solid black outline — NOT 3D extruded.
- Scope rule (append to every dialogued prompt): photoreal DAZ3D CGI on bodies, costumes,
  skin, hair, environment and lighting; ONLY the bubble / SFX graphics are flat 2D
  black-and-white comic overlay. Correct speaker per bubble; each bubble a unique line.

## Banned
- Ink outlines / cel shading / anime / painterly rendering on the figures or room.
- Any color other than violet for Luna's magic.
- Luna shrinking below a previously reached tier.
- Nudity — clothes may tear/strain but always cover (L4).
- Eye contact with the camera in narrative panels (characters look at each other).
