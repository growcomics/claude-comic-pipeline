# Bigger Plans — Pages Ledger (goth-witch-growth)

Flow project: `7103f1eb-7899-4c2d-bde5-2a50737b7717`
URL: https://labs.google/fx/tools/flow/project/7103f1eb-7899-4c2d-bde5-2a50737b7717
Model: Nano Banana 2 (Flow, free tier). Generated 2026-06-22.
All accepted panels are **favorited** in the Flow project. Renders are recoverable from the Flow
media ids below (per CLAUDE.md — binaries not committed).

## Accepted panels (media id = Flow /edit/<id>)

| Panel | Tier | View / Aspect | Media id | Notes |
|-------|------|---------------|----------|-------|
| p01 | 1 | wide-establish / 16:9 | (favorited "Woman beckoning man inside") | Doorway invite. Both baseline. Refs: env+Luna body+Ethan |
| p02 | 1 | mcu / 4:3 | a12fa7ab-662d-41c9-aefe-f95747a2e64b | Couch two-shot. "party trick" setup. Anchor: p01 |
| p03 | 1 | ecu-region / 1:1 | 7a628ab5-7b5e-4b9a-90d2-aeac9bbe9f38 | SOLO Luna, violet magic ignites + FWOOMM. Anchor: p02+facecard |
| p04 | 2 | mcu low-angle / 3:4 | 0c7dc915-7c29-4a25-901a-0c452d338cce | Growth starts, dress snug, FWMP. Anchor: p02+facecard |
| p05 | 3 | ecu-face / 1:1 | c334fbea-09d3-446c-bbaa-76f13b35ab16 | SOLO Luna glamour, glowing violet eyes. Anchor: facecard+p03 |
| p06 | 4 | full low-angle / 3:4 | 0c8c5a98-406c-488f-ac55-3c98fe300c1e | Towers over tiny Ethan, CREEEAK. Anchor: p04 |
| p07 | 5 | cowboy 3q / 3:4 | 85871f3a-f7ba-4aa8-aaf8-b53bb23ef089 | SOLO Luna pin-up under beams. Anchor: p06+facecard |
| p08 | 5 | mcu low-angle / 4:3 | c712e30c-cc03-4024-84f2-c842ddc0cce9 | Ankle-height gag, fingertip reach, GULP. Anchor: p06+facecard |
| p09 | 6 | splash dutch / 3:4 | 4d1b16c0-fbf3-471f-acb9-225be3401447 | SOLO Luna max giantess reveal, VWOOOSH. Anchor: p08+facecard |
| p10 | 6 | medium low-angle / 4:3 | 6d31ff07-8d16-4570-86e4-41c923847618 | Flirty wink button gag. Anchor: p08+facecard |

## Reference assets (favorited)
- Luna face card (canonical portrait) — "Woman headshot portrait dark makeup"
- Luna body baseline tier1 — "Woman standing studio backdrop"
- Ethan baseline tier1 — "Man standing studio backdrop"
- Env goth-loft (16:9) — "Gothic loft apartment interior" (id 3feabc61-bcf7-4985-bc51-aaa5d814eb47)

## QA notes (visual review during generation)
- Size monotonic across the chain: tiers 1,1,1,2,3,4,5,5,6,6 — never shrinks. PASS.
- Character consistency: Luna goth look + Ethan hoodie/glasses held across all panels (face card + chaining). PASS.
- Magic identity color: violet-purple on every powered panel (p03,p04,p05,p06,p07,p08,p09,p10). PASS.
- Coverage (L4): dress strains/tears at seams but always covers. PASS.
- Lettering: flat 2D black-and-white comic balloons + comic font (Bangers-style) baked on photoreal DAZ3D scene; SFX FWOOMM/FWMP/CREEEAK/GULP/VWOOOSH. Correct speakers/tails. PASS.
- Woman-forward: p03,p05,p07,p09 solo Luna; she dominates every shared frame. PASS.
- Adults only (25). PASS.

## To download full-res
Either use the Flow Downloader userscript ("Download ALL" on this project), or per
flow-workflow.md: open each favorited panel → harvest media id → navigate
`labs.google/fx/api/trpc/media.getMediaUrlRedirect?name=<id>` → curl the signed URL.
