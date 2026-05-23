# Experiment 05 — Raw Defects Collection

**Phase A output.** This file inventories every human-observed defect surfaced
across the available sources in this checkout, the way a defect-detection skill
would have to recognize them. Each row is a discrete observation. The next
phases (taxonomy, labeled set, rubric) bucket and codify these.

Sources scoured:

1. `projects/ultra-gal-origin/audits/pages-01-07-audit-2026-05-16.md` — Comic-production QA subagent pass, committed by Matt without modification (so this is "Matt-validated, LLM-authored" — the same label-source provenance Experiment 02 used).
2. `projects/ultra-gal-origin/audits/ref-sheets-qa-2026-05-17.md` — Reference-sheet QA pass (a separate audit on the 6 multi-view ref sheets, not on rendered story panels). Same authorship pattern.
3. `projects/chun-li-test/continuity-report.md` — Continuity audit of the 10-panel chun-li-test arc on macmini Flow (2026-05-22). Same authorship pattern.
4. `docs/experiments/02-vision-audit-pilot/notebooklm-brief.md` §1 — explicit list of the defect classes the project lead **Magnamus** has surfaced in Discord notes. The notes themselves are not in the repo; the brief synthesizes the categories Magnamus has called out.
5. `CHANGELOG.md` — recent dated entries that document failure modes which drove new rules (L21/L22/L23/L24, L29-L32, L33, L34, etc.).
6. `MEMORY.md` (auto-memory feedback files) — codified human feedback on defect classes the user has explicitly flagged: in-scene ref rendering, anachronistic accessories, ref-sheet style propagation, etc.

The chun-li panel PNGs are NOT in this checkout (they live in Matt's Flow project on macmini). They are still recorded here as defect observations and will be carried into the labeled set as labels-only entries — usable as ground-truth for a future cross-project measurement when the PNGs are pulled down.

---

## Per-defect log

Format per row: **source • project • panel-or-asset • description • proposed-category • severity • labeler**.

`labeler` follows Experiment 02's convention: `"matt-mapped-from-audit"` for defects extracted from the per-project audit docs (which Matt committed/validated), `"magnamus-discord-pattern"` for the defect classes Magnamus has surfaced as recurring patterns (the actual flagged panels are not always specifiable from the brief — those entries are pattern-only, not panel-specific), `"matt-direct"` for defects Matt flagged in-line in audits in his own voice (e.g. the "USER-FLAGGED" tag in p03-01).

### Source 1 — ultra-gal-origin pages 01-07 audit (Matt-validated)

| # | Panel | Description | Proposed category | Severity | Labeler |
|---|---|---|---|---|---|
| 1 | p01-03 | "MA'AM, MAAM" — doubled word within a single bubble, second instance missing apostrophe | `lettering.typo_or_doubled_word` | blocking | matt-mapped-from-audit |
| 2 | p01-03 | Speech bubble tail visually attaches to BLONDE Carl while dialogue script-attributes the line to dark-haired Lenny | `lettering.bubble_tail_wrong_speaker` | blocking | matt-mapped-from-audit |
| 3 | p02-02 | Lenny replaced by Carl (blonde instead of dark-haired) in scripted Lenny role | `character.identity_swap` | blocking | matt-mapped-from-audit |
| 4 | p02-02 | "REALLY? WHAT DO YOU DO?" rendered as two identical bubbles in one panel | `lettering.duplicate_bubble` | blocking | matt-mapped-from-audit |
| 5 | p02-03 | Lenny rendered without his canonical blue overalls — wearing just a plain tee | `character.costume_garment_missing` | blocking | matt-mapped-from-audit |
| 6 | p02-04 | Mundy hair tone subtle lightening (drift from canonical deep dark brown toward lighter brown) | `character.hair_color_drift` | cosmetic | matt-mapped-from-audit |
| 7 | p03-01 | Heather looking AT camera; should be looking at Dr. Mundy (eye-direction) | `character.gaze_misdirected` | blocking | matt-direct (USER-FLAGGED in audit) |
| 8 | p03-03 | Wrong character holds the staged prop — Mundy holds the paper bag; Heather should | `character.prop_assignment_wrong` | blocking | matt-mapped-from-audit |
| 9 | p04-01 | Duplicate "OH." bubble on Heather (two identical adjacent bubbles) | `lettering.duplicate_bubble` | nitpick | matt-mapped-from-audit |
| 10 | p04-04 | Heather in NAVY crewneck; canonical body-tier2 is GREEN | `character.costume_color_drift` | blocking | matt-mapped-from-audit |
| 11 | p05-01 | Heather in NAVY crewneck (continuation of p04-04 drift) | `character.costume_color_drift` | blocking | matt-mapped-from-audit |
| 12 | p05-02 | Only Mundy's back visible — Heather entirely missing from frame. Script needs 2 chars, panel shows 1. | `character.count_mismatch_missing` | blocking | matt-mapped-from-audit |
| 13 | p05-04 | Heather's mirroring-arm in BG missing — only one arm visible where script needs two characters | `character.count_mismatch_partial` | blocking | matt-mapped-from-audit |
| 14 | p06-02 | Mundy's white lab coat possibly missing or cropped (canonical Mundy wears lab coat over blouse) | `character.costume_garment_missing` | cosmetic | matt-mapped-from-audit |
| 15 | p06-04 | Heather hair drifted from canonical auburn-red toward strawberry-blonde | `character.hair_color_drift` | blocking | matt-mapped-from-audit |
| 16 | p07-01 | Heather's auburn-red drift continues into strawberry-blonde territory at the climactic super-form reveal | `character.hair_color_drift` | blocking | matt-mapped-from-audit |
| 17 | (sequence p04-04 → p05-03) | Heather wardrobe flip-flops green → navy → navy → green within 4 consecutive panels | `character.costume_state_drift_in_scene` | blocking | matt-mapped-from-audit |
| 18 | (sequence p01-01 → p07-01) | Heather hair auburn-red → strawberry-blonde drift across 6 panels (gradual, not single-panel) | `character.hair_color_drift_across_sequence` | blocking | matt-mapped-from-audit |
| 19 | (sequence p01-01..p07-01) | Camera intent routinely ignored by renderer — shotlist asks Dutch tilts / worms-eye / OTS / birds-eye but render defaults to mcu-eye-level-3q for ~8-10 of 25 panels | `camera.intent_ignored` | cosmetic-systemic | matt-mapped-from-audit |
| 20 | (sequence pages 1-3) | Solar-system wall poster missing from BG of most lab panels (only visible p06-04 + p03-01) | `background.named_element_dropped` | nitpick | matt-mapped-from-audit |
| 21 | (sequence pages 5-6) | Workout-corner setting elements (barbell/plates) only render in p01-01 and p01-02; absent in later lab panels | `background.named_element_dropped` | nitpick | matt-mapped-from-audit |
| 22 | p01-01 | Restage as TRUE wide-establish of the lab + workout corner; currently medium 3-shot | `camera.distance_underdelivered` | cosmetic | matt-mapped-from-audit |
| 23 | p01-04 | Restage as TRUE ecu-face on Mundy; currently mcu | `camera.distance_underdelivered` | cosmetic | matt-mapped-from-audit |
| 24 | p02-02 | Restage with TRUE high-angle (camera elevated 4-5 ft above) | `camera.angle_underdelivered` | cosmetic | matt-mapped-from-audit |
| 25 | p02-03 | Restage with TRUE worms-eye | `camera.angle_underdelivered` | cosmetic | matt-mapped-from-audit |
| 26 | p03-02 | Restage as TRUE ECU-face on Mundy | `camera.distance_underdelivered` | cosmetic | matt-mapped-from-audit |
| 27 | p03-03 | Restage as TRUE birds-eye (directly overhead, 90°) | `camera.angle_underdelivered` | cosmetic | matt-mapped-from-audit |
| 28 | p05-01 | Restage with TRUE Dutch tilt | `camera.angle_underdelivered` | cosmetic | matt-mapped-from-audit |
| 29 | p07-01 | Restage as TRUE splash composition at page-bleed scale | `camera.distance_underdelivered` | cosmetic | matt-mapped-from-audit |

### Source 2 — ultra-gal-origin reference-sheet QA (Matt-validated)

These defects are on REFERENCE SHEETS (not story panels), but they encode the same defect classes that the vision audit must learn to detect when ref sheets are used as L17 anchors.

| # | Asset | Description | Proposed category | Severity | Labeler |
|---|---|---|---|---|---|
| 30 | Ultra-Gal tier-4 sheet, panels 1/2/3 | White top has SHORT sleeves stopping at deltoid; canonical Ultra-Gal tier-5 has FULL-LENGTH long sleeves meeting wrist-length red gloves seamlessly | `ref_sheet.costume_garment_short_vs_canonical_long` | blocking | matt-mapped-from-audit |
| 31 | Ultra-Gal tier-4 sheet, panels 1 vs 5 | Sheet internally self-inconsistent: panel 1 short sleeves, panel 5 long sleeves | `ref_sheet.internal_inconsistency` | blocking | matt-mapped-from-audit |
| 32 | Dr. Mundy tier-2 sheet, panels 1/2/6 | Lab coat rendered CLOSED/buttoned in 3 of 4 coat-visible panels; canonical body-tier2 shows coat WORN OPEN | `ref_sheet.costume_state_wrong` | blocking | matt-mapped-from-audit |
| 33 | Dr. Mundy tier-3 sheet, panel 3 | White lab coat ENTIRELY MISSING from rear view; body shows only teal turtleneck + grey trousers | `ref_sheet.costume_garment_missing` | blocking | matt-mapped-from-audit |
| 34 | Dr. Mundy tier-3 sheet, panels 1/2/3 | Internal inconsistency: panel 1 coat OPEN, panel 2 coat CLOSED, panel 3 coat MISSING | `ref_sheet.internal_inconsistency` | blocking | matt-mapped-from-audit |
| 35 | Heather tier-3 sheet, panel 1 | Rendered as aggressive double-bicep flex; prompt asked for neutral half-flex. Sweater hem possibly hiked up over enlarged torso (borderline L33 concern). | `ref_sheet.pose_intent_ignored` + `character.coverage_risk` | cosmetic | matt-mapped-from-audit |
| 36 | Dr. Mundy tier-3 sheet, panel 6 | Strain intent under-delivered — turtleneck doesn't show dramatic stretch lines or seam stress | `ref_sheet.transformation_state_underdelivered` | cosmetic | matt-mapped-from-audit |
| 37 | Mundy tier-3 sheet, panels 1/2 | Tier-2 → tier-3 differentiation weak in front-facing views — subtle size increase a casual viewer might miss | `tier.underdelivered` | cosmetic | matt-mapped-from-audit |
| 38 | Domina tier-4 sheet, panels 1/2 | Green color extends above-knee like leggings; canonical Domina has blue pointed-toe boots ending mid-thigh-to-knee | `character.costume_color_drift` (lower-body palette) | cosmetic | matt-mapped-from-audit |

### Source 3 — chun-li-test continuity report (Matt-validated, NO LOCAL PNGS)

| # | Panel | Description | Proposed category | Severity | Labeler |
|---|---|---|---|---|---|
| 39 | p10-01 | Outfit drift: tier-7 splash renders a HYBRID — cobalt+gold sleeveless top + white sash belt + flowing blue side-slit skirt drape, closer to fanwork-qipao than pure cobalt bodysuit from new-outfit-tier-7.jpg | `character.costume_design_drift` | blocking | matt-mapped-from-audit |
| 40 | p08-01 | ECU collar reads as classic SF2 blue qipao with gold trim/lapel/closure — NOT the cobalt-blue bodysuit V-neck from the new-outfit ref | `character.costume_design_drift` (ECU-region) | cosmetic | matt-mapped-from-audit |
| 41 | p03-01 | Psycho Power iris glow already at tier-6/7 intensity at tier 3; shotlist asked for "subtle purple shimmer" | `transformation.state_overdelivered` | cosmetic | matt-mapped-from-audit |
| 42 | p04-01 | Costume tear under-render — shotlist asked "first small tears at sleeve caps and side seams"; output shows tight fabric with minimal visible tears | `transformation.state_underdelivered` | cosmetic | matt-mapped-from-audit |
| 43 | p07-01 | Camera under-delivered — shotlist asked low-angle hero stance; output reads closer to eye-level / slight-low, towering effect muted | `camera.angle_underdelivered` | cosmetic | matt-mapped-from-audit |
| 44 | p02-01 | Face slightly off face-card — jaw sharper / less glamour-soft than canonical | `character.face_drift_subtle` | nitpick | matt-mapped-from-audit |
| 45 | (cross-panel p10 vs p07,p09) | p10 splash contradicts p07 + p09 outfit lock — introduces a second design at the FINAL splash | `character.costume_state_drift_in_scene` | blocking | matt-mapped-from-audit |

### Source 4 — Magnamus Discord patterns (no per-panel attribution; pattern-only)

The vision-audit notebook brief documents these as recurring patterns Magnamus has flagged across the project lifetime. Each is a defect CLASS, not a panel-specific observation. They feed the taxonomy as known-real classes regardless of whether a panel example happens to be in the labeled set.

| # | Description | Proposed category | Labeler |
|---|---|---|---|
| 46 | Empty speech-bubble tails — bubble exists but contains no text, OR tail points to wrong character | `lettering.empty_bubble` + `lettering.bubble_tail_wrong_speaker` | magnamus-discord-pattern |
| 47 | Hair color jumps between panels (auburn-red → strawberry-blonde) | `character.hair_color_drift` | magnamus-discord-pattern |
| 48 | Costume color discontinuity (green crewneck → navy → green again) | `character.costume_state_drift_in_scene` | magnamus-discord-pattern |
| 49 | Background extras at wrong scale (bystander rendered too small/large for distance from camera) | `background.extra_at_wrong_scale` | magnamus-discord-pattern |
| 50 | "Copy-pasted" composites — foreground subject and background don't share lighting direction, color temperature, or shadow logic | `composite.coherence_failure` | magnamus-discord-pattern |

### Source 5 — CHANGELOG + MEMORY-derived failure modes

These are defect classes the team has codified as RULES (named L21, L22, L23, L24, etc.) because real production cases produced them. Each is a known defect class the audit must recognize even if examples in the current labeled set are sparse.

| # | Description | Proposed category | Origin | Labeler |
|---|---|---|---|---|
| 51 | In-scene rendering of a face-card or lineup as a physical object inside the panel | `prompt_artifact.ref_rendered_in_scene` | L21 (see `MEMORY.md` → `feedback_comic_l21_ref_exclusion.md`) | matt-direct (feedback memory) |
| 52 | Hair-state inconsistency (twin buns + red ribbons vs loose) when head is in frame | `character.hair_state_drift` | L22 (see `MEMORY.md` → `feedback_comic_l22_hair_anchor.md`) | matt-direct (feedback memory) |
| 53 | Verbal env anchor dropped — location reads as an invented chamber instead of the named one | `background.environment_drift` | L23 (see `MEMORY.md` → `feedback_comic_l23_env_verbal_anchor.md`) | matt-direct (feedback memory) |
| 54 | Anachronistic accessories (watches, modern earrings, rings on canonical-bare characters) | `prompt_artifact.anachronistic_accessory` | L24 (see `MEMORY.md` → `feedback_comic_l24_accessory_suppression.md`) | matt-direct (feedback memory) |
| 55 | Background extras not in the named cast (e.g. extra figures in a solo scene) | `background.unsanctioned_extra` | (see `MEMORY.md` → `feedback_no_extra_characters.md`) | matt-direct (feedback memory) |
| 56 | 2D-illustration drift in a photoreal panel (visible ink outlines, flat shading, comic-book color blocking) | `prompt_artifact.style_drift_2d` | (see `MEMORY.md` → `feedback_comic_style_3d.md`) | matt-direct (feedback memory) |
| 57 | Chest-scale rendered smaller than ref (model normalizes off-distribution features toward average) | `character.scale_normalization_drift` | (see `MEMORY.md` → `feedback_chest_oversize_compensate.md`) | matt-direct (feedback memory) |

---

## Summary

- **57 defect observations** collected (Source 1: 29; Source 2: 9; Source 3: 7; Source 4: 5; Source 5: 7).
- **3 sources have panel-level attributions**: Source 1 (ultra-gal-origin pages 01-07 → 16 panels), Source 2 (ref sheets), Source 3 (chun-li-test → 7 panel-level + 1 cross-panel observation).
- **2 sources have class-level attributions only**: Source 4 (Magnamus Discord patterns), Source 5 (CHANGELOG/MEMORY-derived rules).
- **By severity**: blocking ≈ 26, cosmetic ≈ 22, nitpick ≈ 4, cosmetic-systemic ≈ 1, plus 4 with mixed severity.
- **By labeler**: matt-mapped-from-audit dominates (44); matt-direct = 8; magnamus-discord-pattern = 5.

The next file (`taxonomy-v1.md`) collapses these proposed categories into a structured hierarchy that the rubric and labeled set will use.
