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

## Future canonical entries

When a tier-N reference of any character clears the same provenance bar, add it here with the same shape (file + entry in this README). Likely next: Mira at tier 7/8/9 after a real panel-render validation pass against the L30/L31/L32 sheets.
