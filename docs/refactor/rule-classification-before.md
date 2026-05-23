# Rule Classification — BEFORE the refactor

Audit of every rule under `skills/comic-production/rules/` against L10
("references are the truth, prompts are deltas"). Captured 2026-05-23 on
branch `refactor/refs-are-truth-prompts-are-action`.

A rule **violates** L10 when its `directive()` method emits prose
*describing how the character or location looks*. The model is then being
told what to render instead of being pointed at a reference image to match.

A rule is **compliant** when it does one of:
- attaches a reference image (REFERENCE-ATTACHING),
- describes what the character is DOING / camera / lighting (ACTION-EMITTING),
- describes what NOT to render (NEGATION-SAFETY).

## Summary table

| Rule | File | Slot | Emits | Verdict |
|------|------|------|-------|---------|
| L10  | l10_render_directive.py | 11_render_directive | Meta-instruction: "refs are truth, prompt is delta" | REWRITE → match (one-line match-the-refs directive) |
| L11  | l11_muscular_build.py | 5_style_anchor + 8_tier_build | ~1900 char appearance-emitting body description (per tier) | REWRITE → match (one-line "match attached body-tier ref") |
| L15  | l15_glamour.py | 3_subject_identity | "vogue-cover face quality, sculpted cheekbones, magazine-cover finish" | DELETE (face card carries beauty) |
| L17  | l17_canonical.py | 3_subject_identity | "render the canonical published version of these IP characters EXACTLY..." + per-character canon prose | REWRITE → match (one-line "match attached face card") |
| L18  | l18_anatomy.py | 13_anatomy_guardrail | "torso, hips, abdomen, feet face same direction; no impossible twists" | KEEP — universal safety guardrail (negation-only) |
| L20  | l20_camera.py | 2_camera_strengthening | "EXTREME CLOSE-UP on the {region} filling 70%+ of the frame" | KEEP — camera framing (action-only) |
| L21  | l21_ref_safety.py | 12_ref_safety | "DO NOT render any reference image as a physical scene object..." | KEEP — ref-exclusion safety |
| L22  | l22_hair_state.py | 4_subject_state | "Hair state: {hair_state}." | KEEP — STATE DELTA (not appearance; hair STYLE is in face card, hair STATE is per-panel) |
| L23  | l23_env_anchor.py | 9_environment | Dense location description when env_ref dropped | KEEP — env action fallback (only fires when ref unavailable) |
| L24  | l24_accessory.py | 4_subject_state | "Accessories ({char_id}): {canonical} — ONLY these. NO watch, NO ring..." | KEEP — accessory negation safety |
| female_anatomy | female_anatomy.py | 4_subject_state | "the body is unambiguously FEMALE... visible breast contour... feminine waist taper..." | DELETE (face card + body-tier ref carry female-ness; tier-N reinforcement refs cover muscle-with-breasts) |
| L29  | l29_tier6_reinforcement.py | 8b_tier_reinforcement | ~850 chars describing tier-6 proportions to match | SPLIT — attach part KEEPS (consolidate into attach/tier_reinforcement.py), text part REWRITE (one-line match) |
| L30  | l30_tier7_reinforcement.py | 8b_tier_reinforcement | ~820 chars tier-7 proportions | SPLIT — same as L29 |
| L31  | l31_tier8_reinforcement.py | 8b_tier_reinforcement | ~790 chars tier-8 proportions | SPLIT — same as L29 |
| L32  | l32_tier9_reinforcement.py | 8b_tier_reinforcement | ~750 chars tier-9 proportions | SPLIT — same as L29 |

## Per-rule findings

### L10 — `l10_render_directive.py` — REWRITE

Emits a 298-char paragraph asserting "refs override prompt text on visual
identity; prompt overrides references on pose and action."

This is the META directive — it's literally the principle the entire
refactor is enforcing. Keep the SENTIMENT, drop the verbosity. One-line
match directive after refs are attached: "Match the attached references
exactly for identity; the prompt describes only what is new in this panel."

### L11 — `l11_muscular_build.py` — REWRITE (the worst offender)

Two slots; biggest single contribution in the entire composer.

**Slot `5_style_anchor`** emits `L11_STYLE_ANCHOR` (~600 chars):
> "Style anchor for the body: cartoony hyper-FMG comic-book proportions
> with HEAVY 3D muscle volume AND tier-scaled breast proportions — NOT
> realistic fitness modelling, NOT a fitness-model build at wider scale,
> NOT a smaller-breasted body grafted onto bigger muscles..."

Pure appearance description. Violates L10.

**Slot `8_tier_build`** is the most bloated emission in the whole composer:
~1900 chars when `lineup_attached=True`, describing muscle volume,
breast scale, over-spec compensation, etc. Every word of this is the
model being TOLD what muscles and breasts to render. The lineup PNG is
attached and is the canonical truth for proportion — the model should
MATCH it, not be re-described in 1900 chars of prose.

REWRITE both slots into a one-line `match/match_body.py` directive:
"Body proportions: match the attached body-tier reference exactly."

### L15 — `l15_glamour.py` — DELETE

Emits `L15_FEMALE_BEAUTY_ANCHOR` describing the face the model should
render ("vogue-cover face quality, sculpted cheekbones, refined jawline,
expressive eyes with long natural lashes, magazine-cover finish").

This is exactly what the face card is for. If the face card depicts a
beautiful character, the model matches it. If it doesn't, the fix is to
regenerate the face card — not pile prose into every panel prompt.

DELETE. Beauty migrates entirely to the face-card asset.

### L17 — `l17_canonical.py` — REWRITE

Emits "L17 canonical anchor: render the canonical published versions of
these IP characters EXACTLY..." plus per-character canon strings pulled
from `cast[].canonical_anchor`.

This is text-describing what Chun Li / Supergirl / Lex Luthor look like.
That belongs in the face card asset. REWRITE: one-line match directive
in `match/match_face_card.py`. The `canonical: true` flag stays on the
cast entry (it gates whether the match line fires), but the verbose
anchor prose moves to the asset itself.

### L18 — `l18_anatomy.py` — KEEP

Emits anatomy coherence guardrail: "torso, hips, abdomen, feet face the
same direction; no impossible twists; all limbs attach naturally."

This is NEGATION-SAFETY — describing what's WRONG to render, not what
the character looks like. Compliant. Move to `safety/anatomy_coherence.py`.

### L20 — `l20_camera.py` — KEEP

Emits "EXTREME CLOSE-UP on the {region} filling 70%+ of the frame.
Macro 100mm lens equivalent."

Pure camera/framing description — ACTION-EMITTING. Compliant. Move to
`action/camera_directive.py`.

### L21 — `l21_ref_safety.py` — KEEP

Emits "DO NOT render any reference image as a physical scene object."

NEGATION-SAFETY. Compliant. Move to `safety/ref_safety.py`.

### L22 — `l22_hair_state.py` — KEEP (reclassified)

Emits "Hair state: {hair_state}." per panel.

Subtle but important: the hair STYLE (Chun Li's twin buns shape, color,
length, ribbon design) belongs in the face card. The hair STATE per
panel (up/down/wet/dry/intact-through-burst) is a DELTA the panel
describes. Hair state is to hair what costume tear is to costume — a
per-panel state change, not identity.

KEEP, but move to `action/hair_state.py` (not `match/`). The rule is
fine as-is; it just lives in the wrong category in the old taxonomy.

### L23 — `l23_env_anchor.py` — KEEP

Emits a dense verbal location description WHEN AND ONLY WHEN the env
ref had to be dropped due to the 3-ref ceiling.

This IS appearance description, but it's a fallback when the
reference-attachment path failed. In the new architecture this should
ideally never fire because env attachment should always succeed; but
when it can't, the verbal fallback is better than a void background.

KEEP, move to `action/environment_directive.py`. Document that this is
a SAFETY NET — the preferred path is attaching the env ref.

### L24 — `l24_accessory.py` — KEEP

Emits "NO watch, NO ring, NO earrings..." enumeration from
`cast[].accessories.negation`.

NEGATION-SAFETY. Compliant. Move to `safety/accessory_suppression.py`.

### `female_anatomy.py` — DELETE

Emits "the body is unambiguously FEMALE despite the hyper-developed
muscle. Feminine bone structure, visible breast contour, feminine
waist taper, smaller hands and wrists, soft feminine collarbone."

This was a band-aid for tier-5+ body-region ECUs regressing to male
anatomy when only the multi-figure lineup was attached. The proper fix
is the tier reinforcement refs (L29-L32) — those PNGs depict
unambiguously female tier-N bodies. The face card carries
female-ness as identity. The body-tier reinforcement carries
female-ness as proportion.

DELETE. The reinforcement refs do the work this rule's prose was
trying to do.

### L29-L32 — Tier 6/7/8/9 reinforcement — SPLIT

Each emits ~800 chars describing the proportions to match. Each ALSO
attaches two PNG reinforcement refs.

The PNG attachment is the load-bearing part — that's L10-compliant
(reference-attaching). The 800-char directive describing what the PNG
contains is L10-violating.

SPLIT:
- ATTACHMENT path → consolidate into `attach/tier_reinforcement.py`
  (one module covering all four tiers; the ref-set is the only thing
  that varies per tier)
- TEXT path → DELETE. The one-line `match/match_body.py` directive
  ("match the attached body-tier references exactly") covers both
  lineup and reinforcement refs — the model is told to match what's
  attached, period.

## What lives outside the rules dir and also emits appearance text

The composer in `next_panel.py` (`compose_prompt`) has several inline
hard-coded sections that emit prose. Audited:

| Inline section | Slot | Verdict |
|----------------|------|---------|
| `RENDER STYLE — Iray photoreal` | 1 | KEEP — render quality / style, not character appearance |
| `CAMERA — base framing` | 2 | KEEP — camera, action-only |
| `SUBJECTS` | 3 | KEEP — name list only, no appearance prose |
| `ACTION DELTA` | 4 | KEEP — action description, compliant |
| `LIGHTING STATE` | 5 | KEEP — momentary lighting, action-only |
| `ENVIRONMENT — ref anchor` | 9 | KEEP — instructs model to USE the attached env ref |
| `STATE ANCHOR — L1.5` | (prior panel) | KEEP — instructs to PRESERVE state from attached prior panel; this is the prior-panel-as-ref pattern; formalize as `attach/prior_panel.py` |
| `MANDATORY ANCHORS` | 10 | GUT — current text emits skin/muscle/face appearance ("muscles natural healthy skin tone", "skin subtle healthy sheen", "vivid expressive face"). Strip appearance bits; keep size-monotonicity (state continuity) and remove the rest (L18 covers anatomy) |
| `LETTERING — L19 2D overlay` | 10a | KEEP — bubble/SFX layer description, not character appearance |
| `CLOSING ANCHOR — CGI scope` | 11 | KEEP — render-style scope, not appearance |

## Concrete proof: the chun-li-test p06-01 prompt

The largest realistic emission today. Captured live by running
`compose_prompt` against `projects/chun-li-test/shotlist.json` at tier-6,
peak conditions (lineup + tier-6 reinforcement + env ref + prior anchor):

```
11,509 chars
 1,770 words
    53 lines
```

Of that, the appearance-emitting rules contribute roughly:
- L15 glamour: 53 words
- L11 style anchor: 160 words
- L11 lineup proportions: ~700 words (single biggest emission)
- L29 tier-6 reinforcement: ~210 words
- L17 canonical: variable, ~30-50 words

That's ~1,150 words of pure appearance description per panel. The model
is being asked to memorize ~1,150 words of "what Chun Li at tier 6
looks like" every single panel, when the answer is on disk: the face
card, the body-tier-6 lineup figure, the tier-6 reinforcement PNGs.

See `docs/refactor/yuna-prompt-exhibit.md` for the full BEFORE prompt
and the projected AFTER size.
