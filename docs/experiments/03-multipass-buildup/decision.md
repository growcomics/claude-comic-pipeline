# Decision — Experiment 03

## Status

**Preliminary / partial.** 1 panel of 5 was executed end-to-end. Rating round still pending (Matt + Magnamus). This document records the provisional read; it should be re-written after the remaining 4 panels are run and rated per `runbook.md`.

## Preliminary findings (smoke-test only)

On p05-02:
- Multi-pass produced **more constrained** outputs that adhered better to camera (low-angle-back) and BG (uniform lab plate) — 4/4 of multi-pass variants matched the camera intent vs 2/4 for control.
- Both variants successfully rendered **both characters** in 4/4 variants. The audit's claim that "p05-02 currently only shows Mundy's back" was *not reproducible* with Nano Banana Pro on Flow — that audit was against a different generator and/or earlier prompts.
- **Cost**: 19 generations × $0 (Flow free tier) = $0. A run of the full 5 panels through Higgsfield's MCP would be ~25-30 gens at nano_banana_pro = ~$2-3.

## What changed in my expectations

Before running: I expected multi-pass to clearly win the cast-count-violation case (p05-02). That's not what I found. The model didn't drop a character either way.

That **doesn't kill the hypothesis** — it shifts where the win might come from:

1. **Camera/composition adherence** is real and visible in the smoke test. Multi-pass forces the same camera across the ingredient set and the composite locks it in.
2. **BG consistency** is real. The lab plate ingredient anchors the environment for the composite.
3. **Identity confusion** (p02-02 Lenny↔Carl swap) — not yet tested. This is where multi-pass *should* shine, because the ingredient pass for Lenny would be locked dark-haired-blue-overalls before the composite sees Carl in the same prompt context. Run p02-02 to test.
4. **Object-character binding** (p03-03 bag-in-wrong-hand) — not yet tested. Similar — pre-binding the bag to Heather as an ingredient should beat one-shot.

## Decision (provisional)

**Do not yet ship the `composition_mode: "build_up"` flag.** Wait for the remaining 4 panels to be rated.

If, after the rating round, multi-pass wins clearly on the **identity-confusion** and **object-binding** panels (p02-02, p03-03) but ties on **straightforward composite** panels (p05-02): the recommendation is to make `composition_mode: "build_up"` a **per-panel opt-in flag** triggered by specific heuristics:

- Panel has ≥3 named characters → flag
- Panel has a prop with explicit character-binding ("X is holding Y") → flag
- Panel has two visually similar characters (e.g. two men, two women of similar build) → flag
- Otherwise → leave as one-shot

If multi-pass ties or loses across the board: ship NO change, document the negative result, and treat the build-up workflow as a manual escape hatch for individual hard panels (not a pipeline default).

## Cost / friction findings (worth recording regardless of the rating outcome)

- **Flow UI is the bottleneck.** Multi-ref attachment in Flow takes ~3-5 picker round-trips per gen; that compounds for the composite pass (3 ingredient refs + careful prompt). The runbook estimate is ~15 min per panel through the UI.
- **Higgsfield MCP would be ~10x faster** for this experiment because refs attach by ID, no UI driving. If this experiment is re-run, prefer Higgsfield + nano_banana_pro per memory `feedback_higgsfield_model_flash.md`.
- **Renamed refs.** Asset uploads with duplicate basenames (`face-card.png` × 4) can't be distinguished in Flow's picker. The pre-rename step (`/tmp/exp03-refs/`) is mandatory for any multi-character experiment.
