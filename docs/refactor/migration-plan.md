# Migration plan — rules-as-categories

## New directory layout

```
skills/comic-production/rules/
├── _base.py                       # Rule base + Verification + STATUS_* + Category enum
├── _registry.py                   # Updated imports
├── attach/                        # Category A — reference-attaching (no text emission)
│   ├── __init__.py
│   ├── face_card.py               # NEW — formalizes face-card attachment
│   ├── body_tier.py               # NEW — formalizes lineup attachment
│   ├── tier_reinforcement.py      # NEW — consolidates L29/L30/L31/L32 attachment
│   ├── env_ref.py                 # NEW — formalizes env-ref attachment
│   ├── prior_panel.py             # NEW — formalizes prior-panel attachment (L1)
│   └── internet_3d_base.py        # NEW — the internet→3D base ref attachment
├── action/                        # Category B — action-descriptor (emits action text)
│   ├── __init__.py
│   ├── camera_directive.py        # was l20_camera.py
│   ├── environment_directive.py   # was l23_env_anchor.py (env fallback)
│   └── hair_state.py              # was l22_hair_state.py (STATE delta)
├── match/                         # Category C — match-directive (one-line "match the ref")
│   ├── __init__.py
│   ├── match_face_card.py         # was l10_render_directive.py + l17_canonical.py (consolidated)
│   ├── match_body.py              # was l11_muscular_build.py + L29/L30/L31/L32 text directives
│   ├── match_env.py               # NEW — paired with attach/env_ref.py
│   └── match_prior_panel.py       # NEW — paired with attach/prior_panel.py
└── safety/                        # Category D — negation-safety
    ├── __init__.py
    ├── ref_safety.py              # was l21_ref_safety.py
    ├── accessory_suppression.py   # was l24_accessory.py
    └── anatomy_coherence.py       # was l18_anatomy.py
```

## Per-rule disposition

| Old path | Action | New path | Notes |
|----------|--------|----------|-------|
| `l10_render_directive.py` | REWRITE → match | `match/match_face_card.py` (merged with L17) | Long L10 paragraph replaced with one-line "match attached refs" |
| `l11_muscular_build.py` | REWRITE → match | `match/match_body.py` | 1900-char tier prose → one line. Tier-specific text DELETED; the tier reinforcement PNGs carry the proportion truth |
| `l15_glamour.py` | DELETE | — | Face card carries beauty; do not regenerate beauty prose every panel |
| `l17_canonical.py` | REWRITE → match (merged into match_face_card) | `match/match_face_card.py` | Canonical text moves into the face-card asset itself; rule emits one-line "match canonical face card" when `cast[].canonical=true` |
| `l18_anatomy.py` | KEEP, MOVE | `safety/anatomy_coherence.py` | Already compliant negation-only |
| `l20_camera.py` | KEEP, MOVE | `action/camera_directive.py` | Already compliant action-only |
| `l21_ref_safety.py` | KEEP, MOVE | `safety/ref_safety.py` | Already compliant negation-only |
| `l22_hair_state.py` | KEEP, MOVE | `action/hair_state.py` | Reclassified: hair STATE is a per-panel delta (state-delta is action-class), hair STYLE is in the face card |
| `l23_env_anchor.py` | KEEP, MOVE | `action/environment_directive.py` | Compliant SAFETY-NET (only fires when env ref had to be dropped); documented as fallback |
| `l24_accessory.py` | KEEP, MOVE | `safety/accessory_suppression.py` | Already compliant negation-only |
| `female_anatomy.py` | DELETE | — | Face card + tier reinforcement PNGs carry female-ness now; rule was a band-aid |
| `l29_tier6_reinforcement.py` | SPLIT | attach part → `attach/tier_reinforcement.py`; text directive → `match/match_body.py` | Reinforcement PNGs continue to attach; 850-char directive collapses into one shared match line |
| `l30_tier7_reinforcement.py` | SPLIT (same as L29) | `attach/tier_reinforcement.py` + `match/match_body.py` | Tier-7 PNGs |
| `l31_tier8_reinforcement.py` | SPLIT (same as L29) | `attach/tier_reinforcement.py` + `match/match_body.py` | Tier-8 PNGs |
| `l32_tier9_reinforcement.py` | SPLIT (same as L29) | `attach/tier_reinforcement.py` + `match/match_body.py` | Tier-9 PNGs |

## New attach rules (no old equivalent)

- `attach/face_card.py` — every panel, attach the face card for every
  named character.
- `attach/body_tier.py` — based on shotlist `muscle_size_tier`, attach
  the appropriate lineup (low / high).
- `attach/env_ref.py` — based on shotlist location, attach the env ref.
- `attach/prior_panel.py` — every panel after the first, attach panel
  N-1 (or the most-recent accepted panel of the same character) as a
  state-continuity anchor. Formalizes the L1 chaining the composer
  was doing inline.
- `attach/internet_3d_base.py` — if a character has an
  `internet-3d-base.png` ref at
  `references/characters/<slug>/internet-3d-base.png`, attach it.
  Soft-warns when missing so new characters get a clear "you need a
  base ref" signal.

## Categories on the Rule base class

`_base.py` extends with:

```python
class Category:
    ATTACH = "attach"
    ACTION = "action"
    MATCH  = "match"
    SAFETY = "safety"
```

Every Rule sets `category: str = ""`. The composer can filter or order
by category without inspecting module paths. Audit and reporting tools
can group rules by category.

Existing schemas that key off `rule.id` are unchanged — IDs persist
across the move. The category field is additive.

## Composer changes (`skills/comic-production/scripts/next_panel.py`)

The composer's `compose_prompt` continues to assemble sections in slot
order. Specific changes:

1. **Drop L15 invocation.** Glamour anchor section is removed entirely.
2. **L11 5_style_anchor and 8_tier_build → match/match_body.py.** Both
   slots now emit one short line ("match the attached body-tier
   references") instead of the ~1900-char tier prose.
3. **L17 → match/match_face_card.py.** Canonical anchor reduces to one
   line ("match the attached canonical face card for these IP
   characters") when any character has `cast[].canonical=true`.
4. **L29-L32 → consolidated.** `8b_tier_reinforcement` slot now emits
   one shared line referencing the attached tier reinforcement refs
   (the actual PNG attachment still happens via
   `attach/tier_reinforcement.py`).
5. **female_anatomy invocation deleted.**
6. **MANDATORY ANCHORS section gutted.** Strip appearance bits ("muscles
   natural healthy skin tone", "skin subtle healthy sheen"); keep
   size-monotonicity ("once grown to a size they stay at that size or
   larger") which is a state-continuity rule.
7. **STATE ANCHOR — L1.5 → attach/prior_panel.py.** Inline anchor section
   becomes a routed attach rule.

## Persistence fix (`runners/runner_core.py`)

`_commit_accepted()` extended to also write per-panel:
- `prompt.txt` — the composed prompt that was used
- `attached_refs.json` — the list of ref dicts attached
- `panel-plan.json` — the full plan dict from `build_plan`

The runner's outer loop already has access to all three; the call
signature of `_commit_accepted` extends with the plan dict.

Without this fix, future drift cannot be diagnosed because we never know
what the model was actually told.

## Backward-compat statement for existing projects

- **Accepted panels stay as-is.** Already-rendered PNGs are not
  retouched. Their commit-time `_accepted.txt` markers stay valid.
- **Existing project configs parse unchanged.** No shotlist field is
  renamed; no production-config key is moved.
- **Re-running `next_panel.py` against any existing project produces a
  DIFFERENT prompt.** This is the point of the refactor. If a project
  is mid-flight and depends on getting the same prompt structure on
  re-render, finish that project before merging this refactor.
- **Rule IDs are unchanged.** `L21`, `L18`, etc. continue to identify
  the same logical rule even though the module path moves. Audit
  ledgers and checks.json files written by the old code remain
  interpretable.

## Open issues deferred from this refactor

- **Detailed `action/lighting_directive.py` / `action/mood_directive.py` /
  `action/action_directive.py` modules.** The composer currently emits
  these inline sections directly. The refactor leaves them inline (they
  are already action-compliant) and adds the module files only when a
  rule-driven version is needed. Documented as a future extraction.
- **`safety/clothing_coverage.py`.** L29 "always-clothed" (L33 in some
  configs) is currently encoded per-project in `production-config.json`
  `mandatory_rules.extra_lines`. Promoting it to a rule module is a
  separate refactor; this branch documents the slot but doesn't
  populate it.
- **Vision-rubric verification.** The `vision_rubric` attributes on the
  old rule classes carry forward to the new module locations unchanged.
  The verify_post_render pathway is unaffected by the refactor.
