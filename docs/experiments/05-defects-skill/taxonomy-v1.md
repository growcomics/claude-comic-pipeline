# Experiment 05 — Defect Taxonomy v1

**Phase B output.** Buckets the 57 raw defects from [`raw-defects.md`](raw-defects.md)
into a structured category tree. Each leaf carries:

- A **stable category id** (used in `labeled-defects.json` and the rubric).
- A **one-line detection description** in plain English (used verbatim in the rubric).
- The **default severity** (`blocking` / `cosmetic` / `nitpick`).
- The **priority** for the audit pipeline (`HIGH` / `MED` / `LOW`) — same convention
  Experiment 02 used.
- A **support count** = how many raw observations from Phase A fall under it.

## Design choices vs Experiment 02

Experiment 02 shipped 10 flat categories. This taxonomy extends them into
sub-categories so the rubric can give specific guidance and the metrics can
disaggregate (`hair_color_drift` vs `hair_state_drift`, `costume_color_drift`
vs `costume_garment_missing`, etc.). **Every Experiment 02 category maps
forward into this taxonomy** — the labeled set carries Exp 02's labels through
verbatim as the parent category, with new sub-category labels added where the
audit doc supports them. No labels are dropped; this is a refinement, not a
replacement.

New top-level buckets added in v1:

- **`camera`** — defects where the rendered camera distance/angle ignores the
  shotlist's intent (e.g., asked Dutch tilt, got eye-level). Source 1 surfaced
  8 of these. Source 3 surfaced 1. Not present in Exp 02's taxonomy.
- **`background`** — extras count, environment-drift, named-element-dropped. Exp
  02 had `scale_error` as a single bucket; this taxonomy splits it.
- **`transformation`** — tier under/over-delivered AND in-scene state drift. Exp
  02 had a single `tier_visualization_mismatch`; this taxonomy splits over- vs
  under-delivery (chun-li-test surfaces both).
- **`ref_sheet`** — multi-view reference-sheet internal-inconsistency class
  (Source 2). Exp 02 didn't audit reference sheets so the taxonomy had no
  bucket for this — but the audit pipeline must handle them because they
  become L17 anchors that propagate.
- **`prompt_artifact`** has 3 leaves (`style_drift_2d`,
  `ref_rendered_in_scene`, `anachronistic_accessory`). Exp 02 had 1 leaf
  (`prompt_bloat_artifact`). The new leaves are the L21 / L24 rule classes.

## The taxonomy

### `composite`

| Category id | Detection description | Severity | Priority | Support |
|---|---|---|---|---|
| `composite.lighting_mismatch` | The foreground subject's lighting direction or intensity doesn't match the background environment's — different sun angle, different key-light direction, different time-of-day implied. | blocking | HIGH | 1 (pattern) |
| `composite.shadow_mismatch` | Shadows on the foreground subject contradict the lighting implied by the background — e.g., subject lit from camera-right, background lit from camera-left. | blocking | HIGH | 0 |
| `composite.color_temperature_mismatch` | Foreground and background color temperatures don't match — foreground reads warm, background reads cool, looks composited. | blocking | HIGH | 0 |
| `composite.scale_compositing_artifact` | Subject and background scale don't reconcile under any plausible perspective — looks like the subject was pasted at the wrong size. | blocking | HIGH | 0 |

(All four are present in the Magnamus pattern "looks copy-pasted". The audit
script may treat them as a single signal in v1 of the rubric and split them
when labeled examples accumulate.)

### `character`

| Category id | Detection description | Severity | Priority | Support |
|---|---|---|---|---|
| `character.hair_color_drift` | A named character's hair color is visibly different from their canonical face card or canonical text spec — e.g., auburn-red drifting toward strawberry-blonde, deep dark brown drifting lighter. | blocking | HIGH | 5 |
| `character.hair_color_drift_across_sequence` | Same as `hair_color_drift` but only visible when comparing across panels — single panels look acceptable in isolation but the trend is wrong. (Score this as a sequence-level finding, not per-panel.) | blocking | HIGH | 1 |
| `character.hair_state_drift` | Hair is the right color but the wrong state — e.g., twin buns + red ribbons specified but rendered loose, ponytail rendered as buns. | cosmetic | MED | 1 |
| `character.costume_color_drift` | Costume color differs from canonical — e.g., Heather in NAVY where canonical is GREEN, Domina's lower-body palette shifted from blue boots to green leggings. | blocking | HIGH | 4 |
| `character.costume_garment_missing` | A specific named garment is missing — e.g., Lenny without his blue overalls, Mundy without her lab coat, Ultra-Gal's long sleeves missing from a tier where they're canonical. | blocking | HIGH | 3 |
| `character.costume_design_drift` | The whole costume design has drifted to a different canonical look — e.g., chun-li tier-7 panel rendering the SF2 qipao instead of the new-outfit bodysuit; partial blending of two designs. | blocking | HIGH | 2 |
| `character.costume_state_drift_in_scene` | Costume specifics flip-flop within consecutive panels of a single scene — e.g., green→navy→green→navy across 4 panels. | blocking | HIGH | 2 |
| `character.face_drift_subtle` | Face is recognizable but slightly off the face card — sharper jaw, less glamour-soft, subtle proportion shift. | nitpick | LOW | 1 |
| `character.face_identity_drift` | Face is far enough off-canonical that the character is barely recognizable. | blocking | HIGH | 0 |
| `character.identity_swap` | Wrong character occupies the scripted role — Lenny replaced by Carl, etc. | blocking | HIGH | 1 |
| `character.count_mismatch_missing` | The scripted cast includes N characters; the panel renders fewer (one or more entirely absent from the frame). | blocking | HIGH | 1 |
| `character.count_mismatch_partial` | All scripted characters are nominally present but one is rendered as only a partial body element (e.g., a single arm where a full body was expected). | blocking | MED | 1 |
| `character.gaze_misdirected` | Character eye direction violates the scripted blocking — e.g., character looking at camera when script says looking at another character. | blocking | MED | 1 |
| `character.prop_assignment_wrong` | A scripted prop is held by the wrong character. | blocking | MED | 1 |
| `character.scale_normalization_drift` | Character anatomy normalizes toward average vs the off-distribution canonical (e.g., chest scale rendered smaller than ref). | cosmetic | MED | 1 |
| `character.coverage_risk` | Coverage borderline (sweater hem hiked above waistband, exposed strip of midriff) on a canonically always-clothed character — borderline L33 concern. | blocking | HIGH | 1 |

### `background`

| Category id | Detection description | Severity | Priority | Support |
|---|---|---|---|---|
| `background.extra_at_wrong_scale` | A background figure (extra) is rendered at a scale incompatible with their distance from camera. | cosmetic | MED | 1 (pattern) |
| `background.unsanctioned_extra` | The frame contains figures beyond the named cast for that panel. | blocking | MED | 1 |
| `background.environment_drift` | The location reads as a different chamber/scene than the named environment — invented backdrop instead of the canonical one. | cosmetic | MED | 1 |
| `background.named_element_dropped` | A named environmental element (solar-system poster, workout corner, banner) is canonical to the location but missing from the render. | nitpick | LOW | 2 |

### `camera`

| Category id | Detection description | Severity | Priority | Support |
|---|---|---|---|---|
| `camera.angle_underdelivered` | Shotlist specifies a strong angle (Dutch tilt, worms-eye, birds-eye, high-angle) but the render delivers near-eye-level. | cosmetic | LOW | 5 |
| `camera.distance_underdelivered` | Shotlist specifies a distance category (ECU-face, wide-establish, splash) but the render lands a step less extreme (mcu instead of ECU, medium instead of wide). | cosmetic | LOW | 4 |
| `camera.intent_ignored_systemic` | Over a sequence, the renderer collapses most panels to the same combo (mcu × eye-level × 3q) regardless of shotlist variety. Sequence-level finding, not per-panel. | cosmetic-systemic | LOW | 1 |

### `lettering`

| Category id | Detection description | Severity | Priority | Support |
|---|---|---|---|---|
| `lettering.typo_or_doubled_word` | A baked-in bubble contains a typo or duplicated word inside one bubble — e.g., "MA'AM, MAAM". | blocking | MED | 1 |
| `lettering.duplicate_bubble` | A panel contains two identical bubbles or two adjacent bubbles with the same text. | blocking | MED | 2 |
| `lettering.empty_bubble` | A bubble shape exists but contains no text. | blocking | MED | 1 (pattern) |
| `lettering.bubble_tail_wrong_speaker` | A bubble's tail visually attaches to character X but the dialogue script-attributes the line to character Y. | blocking | HIGH | 1 |
| `lettering.sfx_inappropriate_for_genre` | An SFX rendered in a style incompatible with the panel's tone (e.g., comic-book BAM! in a photoreal noir page). | nitpick | LOW | 0 |

### `transformation`

| Category id | Detection description | Severity | Priority | Support |
|---|---|---|---|---|
| `transformation.state_underdelivered` | Shotlist declares a transformation state (tier 5, first tears, full strain) but the render lands closer to a less-advanced state. | cosmetic | MED | 2 |
| `transformation.state_overdelivered` | Shotlist declares a mild transformation state but the render lands closer to a peak state (e.g., tier-3 iris glow rendered at tier-7 intensity). | cosmetic | MED | 1 |
| `transformation.tier_mismatch` | Declared tier doesn't match the rendered body mass / costume change — broad miss spanning multiple visible cues (vs the narrower state under/over). | blocking | HIGH | 1 |
| `transformation.in_scene_costume_state_drift` | Same as `character.costume_state_drift_in_scene` but specifically when the drift is between transformation tiers within a single scene. | blocking | HIGH | 0 (subsumed by character.costume_state_drift_in_scene) |

### `prompt_artifact`

| Category id | Detection description | Severity | Priority | Support |
|---|---|---|---|---|
| `prompt_artifact.style_drift_2d` | A photoreal-spec panel renders with visible ink outlines, flat shading, or comic-book color blocking instead of photoreal CGI. | blocking | HIGH | 1 |
| `prompt_artifact.ref_rendered_in_scene` | A face card or character lineup is rendered as a physical object inside the panel (poster, mirror, framed photo) instead of being used only as a reference. | blocking | HIGH | 1 |
| `prompt_artifact.anachronistic_accessory` | A canonical-bare character is rendered with anachronistic accessories (watch, modern earrings, ring) — model hallucination. | cosmetic | MED | 1 |
| `prompt_artifact.directive_collision_visible` | Two contradictory prompt directives produce a visible artifact (text leaked into render, repeated negation visible). | blocking | HIGH | 0 |

### `ref_sheet`

Scope note: these apply when the asset under audit is a multi-view reference
sheet, not a story panel. They DO NOT apply to story panels even if a panel
shows a similar surface defect. (For story panels, use the corresponding
`character.*` category.)

| Category id | Detection description | Severity | Priority | Support |
|---|---|---|---|---|
| `ref_sheet.costume_garment_missing` | A reference sheet renders a canonical garment as missing in one or more of its views. | blocking | HIGH | 1 |
| `ref_sheet.costume_garment_short_vs_canonical_long` | A reference sheet renders a garment shorter than canonical (e.g., short sleeves where canonical long). | blocking | HIGH | 1 |
| `ref_sheet.costume_state_wrong` | A reference sheet renders a costume state (closed vs open coat) different from canonical. | blocking | HIGH | 1 |
| `ref_sheet.internal_inconsistency` | The views inside a single sheet disagree with each other (panel 1 short sleeves, panel 5 long sleeves). | blocking | HIGH | 2 |
| `ref_sheet.pose_intent_ignored` | The sheet's pose differs from the requested pose (neutral A-pose requested, double-bicep flex rendered). | cosmetic | MED | 1 |
| `ref_sheet.transformation_state_underdelivered` | The sheet's transformation cues (strain, stretch lines, seam stress) are weaker than requested. | cosmetic | MED | 1 |
| `ref_sheet.tier_differentiation_weak` | Tier-N and tier-N+1 versions of a character look too similar — the size jump isn't readable. | cosmetic | MED | 1 |

---

## Mapping from Experiment 02's flat taxonomy to v1

Every Exp 02 category has a forward-compatible mapping. Existing Exp 02 labels
are carried into the v1 labeled set under both the legacy category and the
refined leaf where the audit-doc note supports it.

| Exp 02 category | v1 mapping |
|---|---|
| `composite_mismatch` | `composite.*` (any sub-category triggers this; default `composite.lighting_mismatch` if unspecified) |
| `hair_discontinuity` | `character.hair_color_drift` (default) or `character.hair_state_drift` if state-only |
| `costume_discontinuity` | `character.costume_color_drift` / `character.costume_garment_missing` / `character.costume_design_drift` / `character.costume_state_drift_in_scene` per the specific defect |
| `scale_error` | `background.extra_at_wrong_scale` (if about an extra) or `character.scale_normalization_drift` (if about the main character) |
| `empty_speech_bubble` | `lettering.empty_bubble` / `lettering.bubble_tail_wrong_speaker` |
| `tier_visualization_mismatch` | `transformation.tier_mismatch` / `transformation.state_under/overdelivered` |
| `prompt_bloat_artifact` | `prompt_artifact.style_drift_2d` (default) or `prompt_artifact.directive_collision_visible` |
| `lettering_error` | `lettering.typo_or_doubled_word` / `lettering.duplicate_bubble` (subtype determined by note) |
| `character_count_error` | `character.count_mismatch_missing` (default) or `character.count_mismatch_partial` |
| `character_identity_swap` | `character.identity_swap` |

(No Exp 02 category drops out of v1. The 10 Exp 02 categories expand into 32
v1 leaves; 30 of those leaves trace back to an Exp 02 ancestor, 12 are
genuinely new — concentrated in `camera`, `background`, `transformation`,
`prompt_artifact`, and `ref_sheet`.)

---

## Priority assignments

`HIGH` = the audit pipeline must catch this reliably or the panel is unshippable.
`MED` = the audit pipeline should surface this for human review.
`LOW` = the audit pipeline can flag this as a soft note but it's not blocking.

The HIGH set (the rubric should be tuned to maximize recall on these):

- `composite.*` — all 4 sub-categories
- `character.hair_color_drift` and `_across_sequence`
- `character.costume_color_drift` / `_garment_missing` / `_design_drift` / `_state_drift_in_scene`
- `character.face_identity_drift`
- `character.identity_swap`
- `character.count_mismatch_missing`
- `character.coverage_risk`
- `lettering.bubble_tail_wrong_speaker`
- `transformation.tier_mismatch`
- `prompt_artifact.style_drift_2d`
- `prompt_artifact.ref_rendered_in_scene`
- `prompt_artifact.directive_collision_visible`
- All 4 `ref_sheet.*` non-pose categories (when auditing ref sheets, all are blocking)
