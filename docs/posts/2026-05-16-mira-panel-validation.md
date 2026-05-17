# Mira panel-render validation — L30/L31/L32 confirmed end-to-end

**Date**: 2026-05-16 evening
**Subject**: L30 (tier 7), L31 (tier 8), L32 (tier 9) — the post-tier-6 reinforcement rule modules
**Commits validated**: [`7336f7b`](https://github.com/growcomics/claude-comic-pipeline/commit/7336f7b) (L30), [`fe098d0`](https://github.com/growcomics/claude-comic-pipeline/commit/fe098d0) (L31), [`b9d9833`](https://github.com/growcomics/claude-comic-pipeline/commit/b9d9833) (L32)
**Credit burn**: ~72 (24 gens × ~3 credits, nano_banana_flash 1k 3:4)
**Result**: 23/24 successful (one tier-7 still rendering at writeup time); all 23 land at their target tier proportions; surgical scoping holds across the board; 3 promoted to canonical-cast.

---

## Why this run

The L30/L31/L32 commits validated the *reference sheets* — they confirmed Higgsfield could produce annotated tier-7/8/9 anatomical character sheets. They did NOT confirm the rules actually produce tier-N *panel output* through the full pipeline ref stack at panel-render time. This run closes that gap.

For each of tiers 7/8/9, the test was: compose a synthetic Mira panel through the full L30/L31/L32 stack (face card + lineup-4-9 + tier-N-full-body + tier-N-anatomical-detail = 4 refs), generate 8 candidates, verify they land at the target tier with the L11 surgical-scoping intact and no leakage from the reinforcement sheets' clothing/hair/face/background.

## Setup

- **Character**: Mira (identity from local `mira_front_full.jpeg`, the user-confirmed identity anchor)
- **All 7 reinforcement refs uploaded to Higgsfield this run** — `muscle-size-lineup-4-9.png` + tier-7/8/9 full-body + tier-7/8/9 anatomical-detail. NSFW upload filter cleared all 7 this time (a contrast with the L29 run where tier-6-anatomical-detail was blocked at upload — suggests the filter is content-dependent and may behave differently from session to session).
- **Per-tier prompt**: synthetic panel composed to exercise the full L11 + L3X stack. Mira standing center frame at the absolute peak of her transformation, fists clenched, chest pushed forward, taking a deep proud breath. Sage-green sleeveless one-piece swimsuit, bare feet. Polished training arena at dusk, soft warm overhead lighting.
- **Model**: `nano_banana_flash`, 1k, 3:4, count=1 per submit. 8 submits per tier.

## Findings

### Finding 1 — 23/24 generations land at target tier proportions

Across all three tiers, every successful candidate reads at its declared tier. The tier ladder is unambiguously distinct:

- **Tier 7 (7/8 successful, one still rendering)**: beyond-peak — deltoids 3x normal mass dwarfing the head, biceps approaching waist width, blocky 8-pack abdominal definition, broad lats with V-taper. Bust scale at tier-7 forward projection.
- **Tier 8 (8/8 successful)**: super-peak — deltoids 3.5x normal mass dwarfing the head MORE noticeably, biceps clearly wider than the waist, deep cavernous pectoral mass, tree-trunk quads. Bust scale visibly larger and more projecting than tier-7.
- **Tier 9 (8/8 successful)**: maximum — pure FMG-comic exaggeration, near-total muscle dominance over the frame, biceps wider than the waist by a lot, frame-filling muscle MASS approaching comic-superhero exaggeration. Bust scale at MAXIMUM comic-fantasy.

This is the first time the per-tier rules have been verified through real panel rendering, not just sheet-style ingest. The L30/L31/L32 architecture **works end-to-end**.

### Finding 2 — Surgical scoping holds across all tiers

Zero leakage from the reinforcement sheets into the panel output:
- **Costume**: All 23 rendered Mira in the sage-green one-piece swimsuit specified in the prompt. No tier-N reinforcement sheet's grey training top bled through.
- **Hair**: All 23 rendered Mira's auburn high ponytail. No leakage from the reinforcement sheets' hairstyles.
- **Face**: Mira's natural-athletic face survived. The L15 glamour anchor (vogue-cover finish) came through cleanly.
- **Background**: Each panel rendered a gym/training arena per prompt — not the plain studio backdrop of the reinforcement sheets.
- **Overlay text / annotations**: No annotated-overlay text rendered as watermarks in any panel.

The L11 surgical-scoping pattern (PROPORTION REFERENCE ONLY + do-NOT-borrow list) **holds across 4-ref stacks at all peak tiers**.

### Finding 3 — Higgsfield's NSFW upload filter is non-deterministic

Tier-6-anatomical-detail.png was blocked at upload during the L29 validation (2026-05-16 afternoon). The same shape of content (tier-7/8/9 anatomical-detail sheets with breast-volume zoom panels) cleared the filter this run. Possible explanations: (a) per-session randomness in the filter, (b) per-content variance based on specific composition / aspect / surrounding content, (c) the filter improved between sessions. Either way: don't treat NSFW upload blocks as deterministic — the same file may upload cleanly on a later attempt.

### Finding 4 — 4-ref stack is reliable at all three tiers

Per the L23 docs, Higgsfield's "3-ref ceiling" is an empirical observation about model coherence. This run used 4 refs (face + lineup + 2 reinforcement sheets) and got 23/24 clean results. Either the ceiling is per-model (nano_banana_flash handles 4 reliably) or the ceiling was always softer than "3 max." Worth re-examining the L23 doc in light of this empirical evidence.

## Per-tier picks

User reviewed all candidates and picked one per tier (all matched my recommendations):

| Tier | Pick | Asset | Notes |
|---|---|---|---|
| 7 | `6959196c` | [tier-7/08](./2026-05-16-mira-panel-validation/tier-7/08-6959196c.png) | Modern training space, beautiful face, balanced tier-7 read |
| 8 | `d5fa091e` | [tier-8/02](./2026-05-16-mira-panel-validation/tier-8/02-d5fa091e.png) | Bright modern gym, most dramatic of the 8 |
| 9 | `2e735ea5` | [tier-9/04](./2026-05-16-mira-panel-validation/tier-9/04-2e735ea5.png) | Most extreme bust + muscle, cleanest gym setting |

All three promoted to:
- [`skills/comic-production/references/canonical-cast/mira/body-tier{7,8,9}.png`](../../skills/comic-production/references/canonical-cast/mira/) (pipeline-level canonical)
- `/Users/mattmenashe/Documents/growcomics-references/series/characters/mira/body-tier{7,8,9}.png` (cross-project canonical mirror, with fuller `_provenance.md`)

All 23 successful candidates archived at [`docs/posts/2026-05-16-mira-panel-validation/`](./2026-05-16-mira-panel-validation/) for reference.

## What this means

- **L30/L31/L32 ship validated end-to-end**. Future tier-7/8/9 FMG comics can chain off these refs with confidence that the rules actually produce panel output at the declared tier.
- **canonical-cast pattern proven** for a second character. Chun Li at tier 6 was the founder; Mira at tier 7/8/9 demonstrates the pattern scales to character + multi-tier coverage. Future canonical character refs land in the same shape.
- **Mira's tier ladder is now half-populated** — tier 7/8/9 are canonical. Tier 1-6 for Mira would close her ladder; same validation procedure would work.

## How to reproduce

```bash
# Per tier (7, 8, or 9):
# 1. Upload refs to Higgsfield: face card + lineup-4-9 + tier-N-full-body + tier-N-anatomical-detail
# 2. Submit 8 generations of a synthetic tier-N Mira panel through nano_banana_flash 1k 3:4
# 3. Download all 8, present, pick one as canonical
# 4. Save to canonical-cast/<character>/body-tier<N>.png + growcomics-references mirror
```
