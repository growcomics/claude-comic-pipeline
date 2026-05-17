# Canonical cast — character references that survived validation

This folder holds **per-character, per-tier canonical references** that have passed real-world validation in the pipeline. Distinct from:

- [`peak-body-scale/tier-N/`](../peak-body-scale/) — *anatomy-only* tier reinforcement sheets (no character identity); used by L29/L30/L31/L32 as proportion anchors regardless of which character is in the panel.
- [`../assets/`](../../assets/) — pipeline-canonical assets (lineup PNGs, quality-standards JSON) used everywhere.
- Project-specific `references/characters/<id>/` — per-project copies that may or may not match the canonical version.

## When to use canonical-cast refs

Any new project rendering a character at a tier this folder covers should **chain off the canonical image** (attach as ref + verbal anchor "same exact character as the attached reference") rather than regenerate from scratch. Skip the regenerate-and-pray cycle.

## Provenance bar

To qualify as canonical-cast:

1. **Generated through the full pipeline ref stack** (face card + lineup + tier reinforcement, per L29-L32).
2. **User-confirmed best** of a multi-candidate batch — not a one-shot. Document the candidate count and pick rationale.
3. **Provenance file** alongside the image: source job ID, prompt, refs attached, pick context, link to the validation log if applicable.

## Current canonical entries

### `chunli/body-tier6.png`

- **Source**: Higgsfield generation `a3949787-e4d4-4ab5-a534-22bdae0b6763`
- **Date added**: 2026-05-16 evening
- **Validation**: gen-05 of 8 L29 validation candidates; user-confirmed best — see [docs/posts/2026-05-16-l29-validation.md](../../../../docs/posts/2026-05-16-l29-validation.md)
- **All 8 candidates archived**: [docs/posts/2026-05-16-l29-validation-assets/](../../../../docs/posts/2026-05-16-l29-validation-assets/)
- **Refs stack used at generation**: face card + `muscle-size-lineup.png` + `tier-6-full-body.png` (the full L29 stack minus the anatomical-detail PNG which was blocked by Higgsfield's NSFW upload filter)
- **What it shows**: Chun Li at tier-6 cartoony FMG proportions, blue cheongsam with high slit, twin buns with red ribbons, fists clenched at sides, courtyard background
- **Cross-project copy**: also lives at `/Users/mattmenashe/Documents/growcomics-references/series/characters/chunli/body-tier6.png` with a fuller provenance note

### `mira/body-tier7.png`

- **Source**: Higgsfield generation `6959196c-5f75-41dc-8a60-28d3fad4800b`
- **Date added**: 2026-05-16 evening
- **Validation**: #8 of 7 successful tier-7 candidates (24-gen panel-render batch across tiers 7/8/9); user-confirmed best — see [docs/posts/2026-05-16-mira-panel-validation.md](../../../../docs/posts/2026-05-16-mira-panel-validation.md)
- **Refs stack used at generation**: Mira identity ref + `muscle-size-lineup-4-9.png` + `tier-7-full-body.png` + `tier-7-anatomical-detail.png` (full 4-ref L30 stack)
- **What it shows**: Mira at tier-7 beyond-peak cartoony FMG proportions, sage-green sleeveless one-piece swimsuit, fists clenched at sides, chest pushed forward, modern training space backdrop

### `mira/body-tier8.png`

- **Source**: Higgsfield generation `d5fa091e-c6d3-44a1-bc50-a05c6ad8dff8`
- **Validation**: #2 of 8 tier-8 candidates; user-confirmed best
- **Refs stack used at generation**: Mira identity ref + `muscle-size-lineup-4-9.png` + `tier-8-full-body.png` + `tier-8-anatomical-detail.png` (full 4-ref L31 stack)
- **What it shows**: Mira at tier-8 super-peak proportions (deltoids dwarfing head, biceps wider than waist, blocky 8-pack abs), same costume + pose, bright modern gym backdrop

### `mira/body-tier9.png`

- **Source**: Higgsfield generation `2e735ea5-63ac-4833-b4a9-5bbbdf77cedb`
- **Validation**: #4 of 8 tier-9 candidates; user-confirmed best
- **Refs stack used at generation**: Mira identity ref + `muscle-size-lineup-4-9.png` + `tier-9-full-body.png` + `tier-9-anatomical-detail.png` (full 4-ref L32 stack; both tier-9 ref slots are intentionally the same Grok-edited composite per L32's design)
- **What it shows**: Mira at tier-9 maximum cartoony FMG (most extreme bust scale + muscle proportions of the validation run), same costume + pose, clean gym backdrop
- **Sibling note**: tier-7/8/9 form a coherent growth sequence with the same identity + costume + pose; chain off all three as a sequential tier ladder for Mira transformation comics escalating beyond tier 6. Cross-project copies + full provenance at `/Users/mattmenashe/Documents/growcomics-references/series/characters/mira/`.

## Future canonical entries

When a tier-N reference of any character clears the same provenance bar, add it here with the same shape (file + entry in this README). The pattern is established — Chun Li at tier 6 + Mira at tier 7/8/9 demonstrate the workflow. Likely next: Chun Li at tier 7/8/9 (same panel-render validation procedure), Mira at tier 6 (to close her tier ladder).
