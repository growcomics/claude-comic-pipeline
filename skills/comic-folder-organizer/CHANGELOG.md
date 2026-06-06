# Changelog — comic-folder-organizer

## 2026-06-04

### Added — two optional generative passes
- **Stage 11 — Defect QA pass.** Vision-scans a story-ordered sequence for *within-panel* technical defects (distinct from the `continuity-check` skill's cross-panel drift). New `defect-taxonomy.md` reference: 9 defect categories, S1/S2/S3 severity scale, per-panel REGEN/INPAINT/KEEP/ASK triage, and do-NOT-flag guardrails for the project's intended features (muscle/chest size, CGI style, intended TF costume states). Outputs `_defects_review.png` (veto gate) + `_defects_report.md` (regen worklist); FIX panels stay in the sequence as keepers.
- **Stage 12 — Story Doctor pass.** Reads the sequence in order against the scene-block breakdown to find narrative gaps, computes a rough completeness score, and emits a ready-to-paste generation prompt per gap. New `story-gap-types.md` reference: 9 gap types, P1/P2/P3 priority scale, completeness rubric, and a cast/outfit-anchored prompt template with the project's generation guardrails baked in. Outputs `_story_gaps.png` + `_story_gaps.md`.

### Changed — SKILL.md
- "When this skill applies" lists both new passes.
- Action vocabulary extended: **FIX** (defective keeper, advisory) and **GAP** (missing panel to generate, not a file).
- New standing principles: #11 (generative passes propose, user disposes — they cost credits) and #12 (never flag an intended feature as a defect).
- Composite color key extended: **CYAN = FIX**, **YELLOW-dashed = GAP placeholder**.
- "What done looks like" notes the two optional worklist artifacts.
