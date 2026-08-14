# Script Format — the Writer → Storyboard contract

This file specifies the exact shape of `script.md`, the artifact the Writer (Stage 2) emits and `script-breakdown` (Stage 3) consumes. It is the "partly implicit" Writer→Storyboard contract from `docs/PRODUCTION-SYSTEM-VISION.md` §4, made explicit.

**Design intent.** Same fundamental shape as the hand-fed scripts the pipeline already digests (Page → Panel → art direction → dialogue, the Ultra-Gal / Gribble lineage), *plus* structured annotations for everything the pipeline downstream is opinionated about — transformation beats, tiers, camera intent, staging, story spine — so Stage 3 **transcribes** instead of inventing. A human reads it top-to-bottom as a comic script; `validate_script.py` and script-breakdown parse it mechanically.

Everything here maps 1:1 onto `shotlist.json` fields (mapping table at the end). Vocabularies are the pipeline's canonical ones — never invent new tokens; the sources of truth are cited per section.

---

## 1. Document skeleton

```
# <Title>
<one-line synopsis — concrete and specific, ≤25 words>

## Header
...KEY: value lines...

### Story spine
### Cast
### Locations
### Props            (optional)
### Transformation scenes
### Notes            (optional — assumptions, autonomous-mode picks)

## Page 1
PANEL 1.1 ...
...

## Page N
...
```

Section order is fixed. Pages are contiguous from 1. Nothing after the last page.

## 2. Header block

`KEY: value`, one per line, inside `## Header`. Required unless marked optional.

| Key | Value | Maps to |
|---|---|---|
| `TITLE:` | the title | `project` (slugified) |
| `CONCEPT-ID:` | the `concept_id` from `concepts.json`, or `hand-written` | provenance |
| `CHAPTER-TYPE:` | `transformation` \| `climax` \| `origin` \| `mixed` \| `action` | drives the growth-density floor (concept `chapter_type`) |
| `PAGES:` | integer — must equal the actual page count | `page_count` |
| `STYLE:` | preset slug from `skills/style-lock/styles/` (default `photoreal-daz3d`) | `style` (Step-0 Q1 pre-answer) |
| `LOCATION-STRATEGY:` | `single` \| `multi` \| `per-scene` | `location_strategy` (Step-0 Q2) |
| `TRANSFORMATION-FLAVOR:` | `body-region-progression` \| `single-axis` \| `other` — required when any transformation scene is declared | `transformation_metadata.flavor` (Step-0 Q3a) |
| `TIER-CURVE:` | `<cast-id> <start>→<end>` (e.g. `dana 2→5`), one line per arc character | `transformation_metadata.start_tier/end_tier` (Step-0 Q3b) + per-panel `muscle_size_tier` bounds |
| `ALWAYS-CLOTHED:` | `yes` (the house default; `no` requires explicit user direction) | coverage lint |
| `GROWTH-TARGET:` | *(optional)* override ratio like `0.60` — otherwise derived from CHAPTER-TYPE | validator target |

Tiers are the lineup vocabulary (`peak-body-scale.md`, lineup tiers 1–6, extended 4–9). Arrow may be `→` or `->`.

## 3. Story spine (`### Story spine`)

The corpus's universal weakness is story (Finding 5) — the spine is required, and stubs ("TBD", one-worders) fail validation. Maps 1:1 onto the shotlist `story_spine` object, which the **L38** gate (`rules_audit.py check_story_spine`) HARD-enforces downstream.

```
WANT: <what the protagonist wants, stated ordinarily, on page 1>
OBSTACLE: <what opposes them — with its own agenda>
COST: <what winning costs>
PROMISE-PAGE: <int — the page that makes the promise>
PAYOFF-PAGE: <int — the page that pays it; must be after PROMISE-PAGE>
ENDING: landed | cliffhanger
HOOK: <required when ENDING is cliffhanger — the specific unanswered question the last page plants>
```

## 4. Cast (`### Cast`)

One bullet per character. Named cast only — **no background extras ever** (`feedback_no_extra_characters`); everyone reads 25+ (`feedback_characters_read_25_plus`).

```
- <id> — <role> · tiers <start>→<end> | tier fixed <n> · marks: <named, non-wardrobe distinguishing marks> · wardrobe: <baseline outfit, one line>
```

- `id` is the slug used in panel CHARACTERS lists and dialogue speaker names (speaker = id uppercased).
- `role` is free-form (`protagonist`, `rival-witness`, `catalyst`, …).
- `tiers a→b` marks an **arc character** (transforms); `tier fixed n` marks a non-arc character. Every arc character needs a matching `TIER-CURVE:` line.
- `marks:` — named, non-wardrobe marks that survive transformation (scar, hair, tattoo, heritage). Required; distinct per character; vivid per `feedback_character_locks_must_be_vivid`. Maps to `cast[].distinguishing_marks`.
- `wardrobe:` — the baseline outfit continuity-check audits against. One line; wardrobe changes later are a new cast entry (`dana-formal`), not history in one row.

## 5. Locations / Props

```
- <id> — <one-line description: furniture, lighting, colors, time-of-day baseline>
```

Props section optional; list only recurring/signature props. One-off props stay in action prose.

## 6. Transformation scenes (`### Transformation scenes`)

One bullet per scene. Every growth run in the script must belong to a declared scene.

```
- <name> — pages <a>–<b> · regions: <region, region, …> · devices: <device, device, …> · reveal: <page>
```

- `regions:` — the body-region beats this scene will cover, from the canonical set (§8). This list becomes the scene's `required_body_regions`; the validator requires each listed region to appear as a beat inside the page range.
- `devices:` — **≥2** from the ranked menu in `comic-production/references/escalation-devices.md`: `sfx-driven`, `reaction-intercut`, `full-body-reveal`, `size-comparison`, `multi-panel-progressive`, `zoom-escalation`, `clothing-destruction`, `slow-burn`. More for a climax.
- `reveal:` — the page carrying the scene's reveal/aftermath beat (inside the range).

Maps to `transformation_scenes[]` (`{name, pages: [a, b], required_body_regions, devices}`).

## 7. Page and panel grammar

### Page header

```
## Page <n> · <optional flags> · scene: <scene-name when inside a declared scene>
```

Optional flags: `GROWTH` (author's declared intent — the validator recomputes growth from beats and cross-checks), `SPLASH` (the whole page is one full-page image — the grid-break; its single panel gets `[size: splash]`).

### Panel line

```
PANEL <page>.<panel> [key: value] [key: value] …
```

Bracket annotations, any order. All optional except where noted:

| Annotation | Value | Maps to |
|---|---|---|
| `[beat: X]` | a transformation beat (§8) — required on every panel that is part of a growth run | `transformation_beat` |
| `[tier: N]` or `[tier: <id> N]` | the arc character's lineup tier in this panel. Bare form allowed only with a single arc character. Integer. | `muscle_size_tier` |
| `[camera: distance, angle]` | camera intent in the canonical vocabulary (§9) — recommended everywhere; expected on body-region beats (they are *conceived* as crops) | `camera` (Stage 3 finalizes) |
| `[size: X]` | `splash` \| `wide` \| `tall` \| `standard` | `size` |
| `[staging: X]` | L34 value: `tension-block` \| `depth-staged` \| `triangular` \| `negative-space-asymmetric` \| `foreground-occlusion` \| `parallel-acceptable` — expected on multi-character panels at medium-or-wider camera and on hero/reveal solos | `subject_staging` |
| `[situation: X]` | L39 situation register — the beat's dramatic function, naming the pose/emotion menus downstream: `showcase` \| `celebratory` \| `confrontation` \| `mid-action` \| `surprise-reveal` \| `aftermath-victory` \| `aftermath-defeat` \| `dialogue-tense` \| `intimate` (menus: `comic-production/references/situation-expression-registers.md`). **Required on panels with 2+ characters**; encouraged on solos. Budget multi-character `showcase`/`celebratory` to ~3 per chapter. | `panel_situation` |
| `[chars: a, b]` | cast ids in frame — required when it differs from "everyone the panel's text names"; use `[chars: —]` for a character-free panel. Also powers the 2+-character checks (`[staging:]`, `[situation:]`). | `characters` |

### Panel body

After the PANEL line, in order:

1. **Action** — one or more plain lines (no label). Present tense, 1–2 sentences, one clear action (~18-word target). What is *seen*, not felt. Pose + expression live here, described mechanically (eyes/brow/cheeks/mouth — `posing-and-expressions.md`); appearance constants (faces, costume design, room architecture) do NOT — refs carry those (`feedback_always_use_refs_not_description`).
2. **Labeled lines**, each on its own line:

```
<SPEAKER> (<type>): "<line>"       dialogue — type: balloon | thought | whisper | shout | off-panel
CAPTION: <narration or time-jump text>
SFX: <TEXT> — <source>             the sound and what makes it
COSTUME: <state>                   arc character's garment state (see below)
NOTE: <free direction for Stage 3>
```

Dialogue rules: SPEAKER is a cast id in caps (`DANA`). ≤25 words per balloon (hard). Max 2 on-screen lines per panel, and 2 lines from 2 different speakers only as a tight back-and-forth at close framing — ≥3 lines from ≥2 speakers is a hard fail; split into per-speaker panels (L13). On-screen dialogue implies close framing — mcu/medium or tighter (L12); captions and off-panel lines are exempt. Aim for roughly 1 panel in 5 with no dialogue at all.

`COSTUME:` — the arc character's garment state, using the continuity vocabulary (`intact` → `tight/straining/stretched` → `torn/ripped/split seams`). Recommended on every panel of a transformation scene; damage only accumulates (never regresses without an explicit story reason). Coverage of breasts/buttocks/groin is always preserved when `ALWAYS-CLOTHED: yes` — seams split, garments never tear away entirely. Maps to `costume_state`.

## 8. Beat vocabulary (canonical — mirrors `script-breakdown` §4.5 / `rules_audit.py`)

- **Setup**: `consider`, `decide`, `trigger`, `first_sensation`
- **Body-region**: `chest`, `hips`, `rear`, `arms`, `abs`, `legs`, `back`, `shoulders`, `suit_fail`, `whole_body`
- **Resolution**: `reveal`, `aftermath`

Growth-page arithmetic: a page is a **growth page** when any panel carries a beat in {`trigger`, `first_sensation`, any body-region, `reveal`} — `consider`/`decide`/`aftermath` are story beats. Every scene needs ≥1 setup beat, every region it declared, and ≥1 reveal/aftermath. Multi-panel body-region beats present the regions in **breasts → glutes → muscles order** across the scene (`posing-and-expressions.md`).

## 9. Camera vocabulary (canonical — mirrors `cinematic-framing.md` + the Gate A token set)

`[camera:]` is `distance, angle` (+ optional modifier in parentheses).

- **Distance**: `ecu-face`, `ecu-region`, `mcu`, `medium`, `cowboy`, `full`, `wide-establish`, `splash` — *lead with one of these exact tokens*; they are what Gate A (`validate_shotlist.py`) accepts as head tokens. (`cowboy` = mid-thigh up, per `cinematic-framing.md`; accepted by Gate A since the 2026-08-13 gate convergence.)
- **Angle**: `eye-level`, `low-angle-front`, `low-angle-back`, `high-angle`, `worms-eye`, `birds-eye`, `dutch`, `over-shoulder`, `profile`, `three-quarter`
- Distance discipline the script should already respect (L20, hard downstream): body-region beats at `mcu`/`ecu-region` (never `full` or wider); chapter mean distance ≤2.5 for transformation comics; ≥30% of panels at middle distances; ≤3 panels at the same distance × angle combo.

## 10. Worked mini example (one page)

```
## Page 2 · GROWTH · scene: first-surge

PANEL 2.1 [beat: trigger] [tier: 2] [camera: mcu, low-angle-front]
Dana upends the chrome vial, throat working, eyes locked on the record board.
DANA (balloon): "Bottoms up."
SFX: GLUG — the last of the vial
COSTUME: intact

PANEL 2.2 [beat: first_sensation] [tier: 2] [camera: ecu-face, dutch]
Her pupils blow wide; a flush climbs her neck. Breath catches — half gasp, half grin.
DANA (thought): "Oh. Oh, that's warm."
SFX: THRRUM — under her skin

PANEL 2.3 [beat: chest] [tier: 3] [camera: ecu-region, eye-level]
Her chest swells against the grey tank, cotton pulling taut, the hem lifting off her waistband.
SFX: CRRK — seams taking the strain
COSTUME: tank straining across the chest

PANEL 2.4 [beat: arms] [tier: 3] [camera: ecu-region, profile]
Her bicep rounds and rises as she curls a fist, a vein surfacing along the peak.
DANA (balloon): "Okay. Okay okay okay—"
COSTUME: sleeves tight, cuffs biting in
```

## 11. Script → shotlist mapping (what Stage 3 transcribes)

| Script element | shotlist.json |
|---|---|
| Header STYLE / LOCATION-STRATEGY | `style`, `location_strategy` (Step-0 pre-answers — confirm with the user, don't re-interview) |
| Header TRANSFORMATION-FLAVOR + TIER-CURVE | `transformation_metadata {flavor, start_tier, end_tier}` |
| Story spine block | `story_spine {want, obstacle, cost, promise_page, payoff_page, ending, hook}` (L38) |
| Cast bullets | `cast[] {id, name, wardrobe, distinguishing_marks, ref_folder: references/characters/<id>/}` |
| Location / prop bullets | `locations[]` / `props[]` (+ typed ref_folder buckets) |
| Transformation scene bullets | `transformation_scenes[] {name, pages, required_body_regions, devices}` |
| `PANEL a.b` | `panel_id: p0a-0b` (zero-padded) |
| `[beat:] [tier:] [camera:] [size:] [staging:] [situation:] [chars:]` | `transformation_beat`, `muscle_size_tier`, `camera`, `size`, `subject_staging`, `panel_situation`, `characters` |
| Action lines | `action` |
| Dialogue / CAPTION / SFX / COSTUME / NOTE | `dialogue[] {character, text, type}`, `captions[]`, `sfx[] {text, source}`, `costume_state`, `notes` |

Stage 3 still owns: final camera strings, `continuity_refs` chains, `time_of_day`/`weather`, ref-folder paths + `references_required.json`, and the Gate A/B runs. It must not need to invent beats, dialogue, tiers, spine, or scene structure — if it has to, the script is incomplete; fix it here.

---

*Validation: `python3 skills/writer/scripts/validate_script.py <script.md>` enforces this grammar plus the craft floors (growth density, L13, tier monotonicity, scene decomposition). See `samples/spot-me/` for a complete conforming script with its gate outputs.*
