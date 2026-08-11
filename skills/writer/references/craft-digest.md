# Craft Digest — writing to the pipeline's strengths

The compressed ruleset the Writer bakes into every script. Each rule cites its canonical source — the citation wins over this summary if they ever disagree. The point (vision §5): the writer *knows* what Stages 3–6 are good at — tier escalation, body-region ECUs, transformation triptychs, L34 staging, L35 expression beats, baked lettering — and structures the story so the big visual moments land where the pipeline is strongest.

---

## 1. Growth is the product

*Source: `feedback_growth_density_mandate`, corpus Finding 1.*

The audience buys transformation. Story exists to make the transformation land harder — not to crowd it out. Un-targeted scripts drift low on growth; count pages against the target while planning, not after.

## 2. Growth-page ratio targets (by chapter type)

*Source: `script-breakdown/SKILL.md` §4.6, corpus F1 (9 comics / 209 pages).*

| CHAPTER-TYPE | Growth-page floor |
|---|---|
| `transformation` | **≥ 60%** |
| `climax` | **≥ 70%** |
| `origin` / `mixed` | **≥ 45%** (aim 45–55) |
| `action` | **≥ 30%** (the niche-payload floor) |

A growth page = any panel with a beat in {`trigger`, `first_sensation`, body-region, `reveal`}. `validate_script.py` computes this and hard-fails under the floor.

## 3. The escalation curve (where growth goes in the script)

*Source: `studio/gribble.php` GR_FORMULA (measured, 41 scripts / 1,355 pages), `escalation-devices.md`.*

- **First growth lands early** — inside the first ~15–20% of pages (Gribble's median: 11%). Fire the engine before the reader can put the book down.
- **≥2 separate growth scenes, each 3+ growth panels** (`feedback_growgetter_size_and_growth_scenes`) — growth recurs the whole way, not one act-two set-piece. Full chapters want 3+ runs.
- **Each run tops the last.** New proof of scale each time: a heavier prop, a bigger reaction, a place she no longer fits. The scale ladder runs person → doorframe → car → building. **Escalation-by-repetition is the corpus's padding habit** — never two near-identical capstone panels in a row.
- **Final escalation at ~80–90%**, then land the ending: at least one beat of consequence after the last payoff (the rival's face, the new status quo, a closing line). Never stop mid-swing; a cliffhanger is a declared hook, not an accident.

## 4. Growth-sequence order within a transformation

*Source: `posing-and-expressions.md` § Growth Sequence Order.*

**Breasts → glutes → muscles.** Softness to power; each stage raises the stakes differently. Default for structuring any multi-region sequence (a mid-sequence closeup can show what it needs). Per-type region menus are in the templates.

## 5. Transformation decomposition (never before→after)

*Source: `script-breakdown/SKILL.md` §4.5 — the single most-confirmed pipeline failure.*

Every growth scene decomposes: setup beat(s) → one beat per changing body region, crop migrating through the body — → reveal (full body, close to camera). Visual weight migrates through the body; each region gets its own beat with its own crop. The reveal closes the loop — a scene without one has no payoff. `rules_audit.py` hard-fails scenes missing setup / ≥3 regions (or the declared list) / reveal, so write them in from the start.

## 6. Escalation devices (≥2 per scene, named)

*Source: `escalation-devices.md` (ranked by corpus frequency).*

`sfx-driven` (34×) · `reaction-intercut` (26×) · `full-body-reveal` (25×) · `size-comparison` (22×) · `multi-panel-progressive` (20×) · `zoom-escalation` (18×) · `clothing-destruction` (17×) · `slow-burn` (6×, underused — the densest-feeling books use it).

Declare ≥2 per scene (more for the climax) and *reflect them in the beats*: multi-panel-progressive = same region across 3 panels; size-comparison = a fixed gauge in the reveal; zoom-escalation = camera tightens each beat. All visual cues are physical phenomena (fabric strain, sweat, displaced air) — SFX text is shotlist data, never prose asking for baked lettering (L7).

## 7. Tier curve — declare it, respect it

*Source: `peak-body-scale.md` (lineup tiers), `feedback_dont_invent_state_changes`.*

- Header declares `TIER-CURVE: <id> start→end` per arc character; the concept's `transformation.tier_curve` is the spec — the writer *places* the growth, never re-invents it.
- Per-panel `[tier: N]` is **monotonic non-decreasing**, starts at the declared start, ends at the declared end, never exceeds it. Tier bumps happen inside growth beats, on the page.
- Tiers ≥6 invoke the peak-scale reinforcement machinery downstream (L29–L32) — fine, but deliberate.

## 8. Faces during growth (the money-shot rule)

*Source: L35 (`lessons-learned.md`), corpus F2/F3, `feedback_expression_intensity`, `posing-and-expressions.md`.*

- The corpus's #1 weakness: faceless or dead-faced money shots. **No more than ~2 consecutive faceless body-region crops without a face cut** — interleave the grower's ecstatic/strained face or a witness recoiling (`reaction-intercut`).
- Every face-bearing beat names the emotion **mechanically**: eyelid position, cheek lift, brow angle, mouth shape, head tilt ("eyes shut tight, cheeks pushed high, mouth wide open in a laugh" — not "happy"). The facial-acting table in `posing-and-expressions.md` is the palette.
- Lifeless expressions are actively bad, not neutral — the reader mirrors the face they see.

## 9. Dialogue framing (L12) and speaker splits (L13)

*Source: `lessons-learned.md` L12, L13.*

- **L12**: a panel with on-screen dialogue (balloon/thought/whisper/shout) frames the speaker close — `mcu`/`medium` or tighter. Captions and off-panel voices are exempt (narration over a wide establish is canonical).
- **L13**: ≥3 dialogue lines from ≥2 speakers on one panel = a broken panel. Split into one panel per beat, framing whoever is talking. 2 lines/2 speakers only as a tight close-framed back-and-forth. One speaker may take 2 balloons.
- ≤25 words per balloon, ~8–12 typical. ~1 panel in 5 silent (reaction beats and growth images carry themselves — Gribble runs 18%).
- Dialogue is a **free win**: 6 of 9 corpus books ship empty balloons; our baked lettering (L19) clears the niche's weakest axis just by giving characters real voice. Write lines worth lettering.

## 10. Staging opportunities, named at script level (L34)

*Source: `staging-and-composition.md`, `cinematic-framing.md` § Subject staging.*

The camera plane is the enemy — flat parade-line blocking is the default failure. The *writer* creates the staging opportunities and names them with `[staging:]`:

- 2-character conflict/charged dialogue → `tension-block`
- Lead dominating a smaller figure, reveal beats → `depth-staged` (also the size-comparison delivery vehicle)
- 3+ characters → `triangular` (lead at apex)
- Solo hero / reveal / splash → `negative-space-asymmetric`
- Intimate or voyeur-witness framing → `foreground-occlusion` (shoot past a barbell, doorframe, rack)

Downstream hard-gates multi-character panels at medium+ with no staging value — declare it here so Stage 3 transcribes. Write scenes that *hand* the pipeline depth: witnesses at doorways, mirrors, gauges in frame, foreground clutter to shoot past.

## 11. Situation registers per beat (L39)

*Source: L39 (`lessons-learned.md`), `situation-expression-registers.md`, `script-breakdown/SKILL.md` §4.8.*

Anti-uniformity demands every character do something different; L39 demands different *within the situation's register*. The writer names each beat's dramatic function with `[situation:]` — one of `showcase`, `celebratory`, `confrontation`, `mid-action`, `surprise-reveal`, `aftermath-victory`, `aftermath-defeat`, `dialogue-tense`, `intimate`. Ask "what is this beat FOR?" — a flex at the mirror is `showcase`; the same flex as a rival watches is `confrontation`; the first time it happens is `surprise-reveal`. **Required on every 2+-character panel** (that's where register leaks and pair duplication happen), encouraged on solos. Budget multi-character `showcase`/`celebratory` to ~3 per chapter — confrontations, reveals, and aftermaths are where the story lives. On active growth beats L35 owns the grower's face; the register governs the witnesses.

## 12. Camera dynamism, pre-planned

*Source: `cinematic-framing.md`, L20, `feedback_overshoot_camera_dynamism`.*

The script's `[camera:]` hints should already satisfy what Gate B hard-checks: body-region beats at `mcu`/`ecu-region` (a region crop at `full`+ renders as before/after, not transformation); transformation-chapter mean distance ≤2.5; ≥30% of panels at middle distances; ≤3 panels per distance×angle combo; ≥1 ECU and ≥1 wide per 10-panel stretch. Overshoot on dynamism — diagonals, FG/BG depth, varied scales — the model under-delivers whatever you specify.

## 13. Coverage and cast discipline

*Source: `CLAUDE.md` generation defaults, `feedback_no_extra_characters`, `feedback_characters_read_25_plus`, `feedback_wardrobe_drift_from_anatomy_keywords`.*

- **`ALWAYS-CLOTHED: yes` is the default.** Garments strain, stretch, split at seams — coverage of breasts/buttocks/groin always preserved; nothing tears away entirely. Muscle/curve *size* is never the SFW problem. SFW does not mean nice — menace, dominance, gloating are story, not rating (gribble.php GR_SFW).
- **Named cast only.** No background extras, no crowds, no passersby — write scenes that are *better because* they're intimate (a closing-time gym beats a busy one).
- **Everyone reads 25+.** No cute/young-coded descriptors.
- **Lock garment state per panel** (`COSTUME:` line) — damage accumulates, never silently regresses; anatomy keywords near wardrobe wording cause drift downstream, so state garment + state explicitly.

## 14. Story spine (the differentiation axis)

*Source: corpus F5 (no book above 3/5 on story; median 2), `ideator/references/rubric.md` Axis 2, gribble.php STORY DISCIPLINE.*

- She WANTS something ordinary on page 1; the ending ANSWERS that want. Growth is how the answer arrives, not the answer itself.
- Every run changes her **situation** — someone's mind, her standing, the plan — not just her measurements.
- Real stakes, tease → payoff, legible cause→effect, an ending that lands.
- Spine fields (want/obstacle/cost, promise/payoff pages, ending) are required in the header — stubs fail validation.

## 15. What the prose must NOT do

*Source: `feedback_always_use_refs_not_description`, L7/L19, refs-are-truth.*

- **Appearance constants stay out of action prose.** Faces, costume *design*, room architecture are carried by refs downstream; the script describes ACTION, POSE, EXPRESSION, and momentary state (garment strain, sweat, lighting shifts). Marks/wardrobe live once in the Cast block.
- **Never ask for lettering in prose.** Dialogue/SFX/captions are labeled data lines; the render pipeline bakes them (L19). Don't write "the word RIIIP appears" — write `SFX: RIIIP — seams giving`.
- **Growth happens on the page.** Never between pages, never implied off-panel.

## 16. Per-type conventions (FMG / BE / BG / MMG)

*Source: `production-briefing/SKILL.md` (type table + per-type rule adjustments); templates in `skills/writer/templates/`.*

| Type | Focus | Script-level conventions |
|---|---|---|
| `fmg` | female muscle | Full region menu; muscles read as power beats (arms/chest/abs/back/legs + suit_fail); chest scales with muscle per the lineup. |
| `be` | breast expansion | Chest-led beats (`chest`, `suit_fail`, `whole_body`); hourglass maintained throughout; no muscle-region beats unless the concept says so; strain/button/seam business is the ambient tell. |
| `bg` | breast + glute (canonical Bloom type) | Two-front escalation: chest beats then hips/rear beats (order per §4); `rear` three-quarter staging; thighs scale with glutes. |
| `mmg` | male muscle | Male cast arc; never feminize during growth; region menu = arms/chest/shoulders/back/abs/legs + suit_fail; dominance/feat beats carry the payoff. |
| `mixed` | multi-arc | Compose the templates in **breasts → glutes → muscles** order; each completed arc stays at its peak. |

The transformation type also picks the size-lineup asset downstream (`production-briefing` `lineup_files`) — the writer just needs the type named in the concept and the right template picked.

---

*Companion files: `script-format.md` (the output grammar these rules are written into), `templates/` (per-type skeletons), `gribble-alignment.md` (what the measured Gribble formula contributes). Canonical sources: `skills/comic-production/references/` (`posing-and-expressions.md`, `escalation-devices.md`, `staging-and-composition.md`, `cinematic-framing.md`, `lessons-learned.md` L12/L13/L20/L34/L35/L38/L39, `situation-expression-registers.md`, `peak-body-scale.md`), `skills/script-breakdown/SKILL.md`, `skills/production-briefing/SKILL.md`, `studio/gribble.php`.*
