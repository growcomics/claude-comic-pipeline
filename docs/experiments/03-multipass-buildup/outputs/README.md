# Experiment 03 — A/B Outputs

## Where the outputs live

All gens were run in a single Google Flow project (Nano Banana Pro, count=4 default for Flow's free 4-up):

**Flow project:** https://labs.google/fx/tools/flow/project/ece3f3b6-e5fd-4809-931a-9cb1d5b90320

Flow image URLs require account auth, so they aren't embeddable here. To view the outputs, open the project URL above and scroll the gallery — newest at top, scrolling down gives older. The order matches the submit sequence (composite → lab plate → heather ingredient → mundy ingredient → control).

## What was generated for p05-02

A single A/B pair on panel p05-02 ("Both characters mid-growth, low-angle-back"). Five submits total, each producing a Flow 4-up:

| Slot | Submit order | Prompt summary | Variants | Used as |
|---|---|---|---|---|
| Control (Variant A) | 1st | One-shot full prompt — Mundy + Heather in lab, mid-growth tier 3, low-angle-back. No character refs attached (text-only character description; one lab ref `lab-mundy-a.jpg`). | 4 | Direct A/B output |
| Ingredient 1 | 2nd | Mundy alone, lab coat, mid-growth tier 3, low-angle-back, plain BG. No refs. | 4 | Picked variant 1 as ref for composite |
| Ingredient 2 | 3rd | Heather alone, green crewneck, mid-growth tier 3, low-angle-back, plain BG. No refs. | 3 (one filtered) | Picked variant 1 as ref for composite |
| Ingredient 3 | 4th | Empty lab interior, wide low-angle-back, all environmental elements. No refs. | 4 | Picked variant 1 as ref for composite |
| Composite (Variant B) | 5th | "Place Mundy figure at FG left, Heather figure at FG right in the lab" with the three ingredient outputs attached as refs. | 4 | Direct A/B output |

## Variance note

This run used **no character face-card refs** for either variant. The control had only the lab ref; the multi-pass ingredients used no refs at all (text-only). Both variants had the same reference constraint set, so the A/B is fair, but it's testing strategy difference WITHOUT character-anchor refs — which is a stricter test (text-only character description is harder than with face-card anchoring).

The reasoning: I tried attaching the 4 named character face cards earlier in the session and Flow's asset picker only reliably attached one at a time, with the asset-picker UI getting fragile after 2-3 attempts. The pragmatic call was to keep refs simple and uniform across A/B rather than ship a confounded comparison.

This is a real finding worth surfacing: **multi-ref attachment in Flow's UI is the bottleneck for scaling this experiment to all 5 panels.** A future run on Higgsfield (with the MCP) would avoid this.

## Cost

Free-tier Flow Nano Banana Pro. 5 submits × 4 variants = 19 gens total (one filtered). $0 in credits.

## Image manifest

Image URLs (authenticated; resolve from a logged-in browser session at labs.google):

### Variant A (control) — 4 outputs
- 5th gen on Flow gallery row 2 (older), positions 6-9 from left

### Variant B (multi-pass composite) — 4 outputs
- 1st gen on Flow gallery row 1, positions 1-4 from left

For an exact-link export of the 8 images, run `node export_flow_project.js` against the project ID — that's outside this experiment's scope.
