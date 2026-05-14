# Changelog

All notable changes to the `claude-comic-pipeline` are tracked here.

This file is the **canonical source for what changed and why**. Any session (human or agent) editing this repo must append an entry here when it lands a meaningful change. Trivial cleanups can be skipped; anything that touches behavior, prompt architecture, the build-comic workflow, or a published reference doc must be logged.

Format: each entry is dated (YYYY-MM-DD), grouped in reverse-chronological order. Entries cite the relevant commit hash(es) and explain the *why* — what failure mode prompted the change, what the new behavior is, where readers can dig deeper.

Categories used per dated section: **Added** / **Changed** / **Fixed** / **Removed** / **Deprecated**. Skip categories with no entries.

---

## 2026-05-13

### Added
- **`CHANGELOG.md`** (this file) at repo root. From now on, every session that lands a meaningful change must append an entry here. See the header for the convention.
- **L12 — Dialogue panels need close framing.** Hard rule: on-screen dialogue (bubble types `balloon` / `thought` / `whisper` / `shout`) must be paired with a close camera (`ecu-face` / `mcu` / `medium` / `cowboy`). Wide + on-screen dialogue produces panels where the reader can't tell who's talking (reviewer note from Supergirl issue #1: *"It doesn't zoom in when the person's talking to a tight shot"*). Caption and off-panel are exempt. `next_panel.py` now emits `WARNING_DIALOGUE_CAMERA_CONFLICT` when it detects the conflict; build-comic hard rule says HALT same as `MISSING_*`.
- **L13 — Multi-speaker beats split into per-speaker panels.** Hard rule: any single panel with ≥3 dialogue lines from ≥2 distinct on-screen speakers must be split into one panel per beat. The cramped one-panel rendering is broken-by-design (reviewer note: *"if we feed in a comic that has four different dialogue lines on one image, instead of that it shows several different people individually with their dialog line"*). `next_panel.py` emits `WARNING_MULTI_SPEAKER_CROWDING`; fix the shotlist before generating.
- **L14 — Multi-view location references for shot-reverse-shot.** Single env anchors break when the camera reverses direction in a dialogue scene (the L10 env-chaining picks one canonical view; reversing the camera produces a scene the anchor doesn't depict). Hero locations that host facing-character dialogue should carry multiple env refs (`_source.jpg`, `_source-reverse.jpg`). Authoring guidance landed; multi-view extension of `pick_location_anchor()` is logged as a follow-up. Reviewer note: *"when two people are talking, the camera can face both directions of the people."*
- **L10 refinement — Identity-vs-pose distinction.** L10 says "delegate constants to refs" but does NOT say "describe nothing." Cleaner line: refs carry identity / costume design / location architecture / lighting baseline; the prompt carries camera / pose / gesture / facial expression / action / momentary lighting state / momentary costume state change. Validated on a Higgsfield She-Hulk splash where the user marked *"wardrobe: red top remnants..."* as L10 violation (constant in ref) but *"pose: full hero roaring stance..."* as load-bearing prompt content (delta, refs can't carry per-panel beats). The render directive in `compose_prompt()` now states the inverse explicitly: *"References override prompt text on visual identity; prompt overrides references on pose and action."*
- **Step 0 questionnaire for script-breakdown** (the other guy's work, landing now). The `script-breakdown` skill must poll the user on three high-stakes decisions before parsing the script: style preset (2D vs 3D — the April v2 run defaulted to 2D when 3D was wanted because nothing forced a choice), location strategy, and transformation flavor + baseline tiers if applicable. Required output: `style`, `location_strategy`, and (when `transformation_scenes` is present) `transformation_metadata` as top-level fields in `shotlist.json`. See `skills/script-breakdown/SKILL.md` § Workflow Step 0.
- **Transformation-scenes structure + rules_audit gate** (the other guy's work, landing now). Multi-page transformations (FMG, growth arc, mutation, dress-up, charge-up, expansion) must be declared as a `transformation_scenes[]` entry in `shotlist.json` and decomposed into per-body-region beats: setup beats (`consider` / `decide` / `trigger` / `first_sensation`), body-region beats (`chest` / `hips` / `rear` / `arms` / `abs` / `legs` / `back` / `shoulders` / `suit_fail` / `whole_body`), resolution beats (`reveal` / `aftermath`). `rules_audit.py` flags HARD findings when a transformation scene lacks ≥1 setup beat, ≥3 distinct body-region beats, or ≥1 reveal beat. This is the gate whose absence produced the April-claudemade failure (9 alley pose shots, zero body-region beats) — the check now blocks that shape at script-breakdown time, before any generation cost is paid.
- **Camera-variety enforcement in `rules_audit.py`** (the other guy's work, landing now). HARD finding when a single `(distance, angle)` combo appears in >3 panels (the Chun-Li + April-claudemade failure mode of 6–7 panels at the same shot signature). SOFT findings for distance-variety floor (≥5 distance categories per 10-panel sequence), angle-variety floor (≥4 angle categories), missing ECU across a ≥6-panel sequence, missing wide-establish/splash across the same. Intimate scenes legitimately violate the floors — those are SOFT for that reason. Sustained-intensity scenes can suppress the angle warning.
- **`continuity-check/tests/`** directory (the other guy's work, landing now). Unit tests for the rules audit.
- **L19 — Bake lettering into the CGI render (reverses L7 Case B's "never bake" rule).** New active lesson. L7 Case B previously deferred all lettering — speech bubbles, captions, SFX — to `page-composer` vector overlays, producing a "CGI panel + sticker overlay" look rather than a single cohesive rendered comic page. L7 Case B's diagnosis (comic-coded vocab pulls CGI prompts toward illustration training data) was correct; its prescription was over-corrected. L19 bakes lettering directly into the prompt AND counters the illustration pull via aggressive anchoring: open with concrete render-engine vocabulary (*"Hyperrealistic DAZ3D Studio 3D CGI render, ray-traced subsurface scattering, physically-based rendering, 8K texture detail"*), render lettering as physical scene objects (3D-extruded chrome SFX letters with real ray-traced shadows, semi-translucent 3D speech panels floating in space with tails pointing at speakers, in-scene caption plaques), and close with explicit negation (*"NOT a comic, NOT an illustration, NOT anime, NOT 2D drawn art. Photographic CGI render."*). Opening anchors the photoreal target; closing tells the model what to avoid; both are needed. Open question logged inside L19: whether `page-composer` survives as an optional vector-lettering fallback or gets retired entirely.
- **Master CGI prompt template + A/B run on Nano Banana 2 vs GPT Image 2.** Synthesized the prompt-level lessons (L4, L7, L10, L10-refinement, L11, L12, L13, L19) into a single canonical CGI panel prompt skeleton so future agents have a reference shape to compose against. Skeleton order: opening render-engine anchor → camera (close per L12 when dialogue is present) → subject identity + cartoony-FMG silhouette anchor (L11) → pose / action / expression delta (L10 refinement) → wardrobe state delta (L10) → baked SFX as physical scene object (L19) → baked speech bubble with positioning (L4 + L19) → environment delta (L10) → closing negation block (L7 / L19). Full template + rule-to-section mapping below.

  A/B test on Higgsfield (identical prompt, 1k, 3:2, count=1 each):
  - **Nano Banana 2** (`nano_banana_flash`) → job `785d664e-95f7-42ec-9ae5-9d3cfa68b383` → `skills/comic-production/references/master-prompt-template/nano-banana-2.png`
  - **GPT Image 2** (`gpt_image_2`, quality=medium) → job `538997bf-801d-40d1-a04f-62098e91d515` → `skills/comic-production/references/master-prompt-template/gpt-image-2.png`

  **Verdict: GPT Image 2 followed the prompt more faithfully on this run.** It nailed the cartoony hyper-FMG silhouette (clearly tier-4-ish proportions, shoulders wide, biceps massive), rendered the qipao-strain wardrobe delta (visible chest tension), and held the pose closer to spec (hand against her own enlarged body, shocked expression). Nano Banana 2 went photoreal CGI on the body but pulled the silhouette back toward realistic-fitness modelling (the L11 prior fights harder on this model), rendered the qipao basically intact (ignored the strain delta), and defaulted to a classic Chun-Li victory flex instead of the introspective "registering enlarged bicep" pose. **Both models held the CGI register — no 2D illustration drift**, which validates the L19 strategy (bake lettering AND anchor aggressively with opening render-engine vocabulary + closing negation block). Both models partially failed on the L19 "photoreal 3D speech bubble" instruction — both fell back to flat 2D comic-style bubbles despite the explicit physical-object framing. SFX "KRRRK" landed sculpturally on GPT Image 2 and flat-2D on Nano Banana 2.

  **Open finding**: even with explicit "photoreal semi-translucent 3D panel" framing, both models default to flat 2D comic-style bubbles. Either the concept isn't in either model's training, or the prompt language doesn't survive the trained association between speech bubbles and comic illustration. Worth trying alternate vocabulary on the next iteration: "floating glass plaque", "translucent acrylic dialogue panel", "engraved stone tablet". Logged as a follow-up.

  Template (canonical CGI panel prompt skeleton — fill the bracketed slots):

  ```text
  [opening — render-engine anchor, L7 / L19]
  Hyperrealistic DAZ3D Studio 3D CGI render, ray-traced subsurface scattering on skin, physically-based rendering, 8K texture detail, shallow depth of field with photographic bokeh. Shot in a virtual studio with three-point lighting: warm key light at 5500K from camera-left, fill at 4500K, cool rim light at 6500K from camera-right. Photographic CGI.

  [camera — close framing when dialogue is present, L12]
  Camera: [distance] ([abbreviation]), [angle], [lens]. [framing note].

  [subject — identity comes from refs in production; tier silhouette per L11]
  Subject: [identity description]. Cartoony hyper-FMG comic-book proportions, NOT realistic fitness modelling. Tier [N] silhouette: [explicit dimensional anchors — see peak-body-scale.md]. Comic-book exaggerated musculature where the silhouette is the storytelling element.

  [action delta — pose / expression / gesture per L10 refinement]
  Action and expression: [pose and angle to camera]. Expression [feeling] — [eyes] [mouth]. [arm and hand placement]. [body energy].

  [wardrobe state delta — only what changed, L10]
  Wardrobe state: [base costume from ref]. [explicit damage / strain delta].

  [baked SFX — physical scene object, L19]
  In-scene SFX: the word "[SFX]" rendered as a 3D-extruded [material] letter sculpture, positioned [location in frame]. Real ray-traced shadows cast on [surface]. Catches the same [lighting] as the rest of the scene. A real sculptural object sitting in the scene, NOT a 2D overlay, NOT a sticker.

  [baked speech bubble — physical 3D panel per L19, positioning per L4]
  In-scene speech bubble: a photoreal semi-translucent white 3D panel with rounded edges and an extruded tail, floating in [location] of the frame. Slightly glossy surface with subtle subsurface scattering. The tail extends [direction], pointing to [speaker]. Black extruded sans-serif text on the surface reads exactly: [DIALOGUE]. A physical object in 3D space, casting a real shadow on [background surface].

  [environment delta — beyond the env ref, L10]
  Environment: [scene description with lighting motivation and depth].

  [closing — negation block, L7 / L19]
  NOT a comic, NOT an illustration, NOT anime, NOT cartoon, NOT 2D drawn art. Photographic CGI render.
  ```

  Rule-to-section mapping:
  - **L7 / L19** — opening render-engine anchor + closing negation block. Bake lettering, but counter the illustration pull at both ends of the prompt.
  - **L11** — "Cartoony hyper-FMG ... NOT realistic fitness modelling" anchor + tier-N silhouette descriptor with explicit dimensional anchors. Resists the model's realistic-fitness prior at tier ≥ 2.
  - **L10 / L10 refinement** — identity, costume design, location architecture come from refs (not the prompt); pose, action, expression, momentary lighting state, momentary costume change live in the prompt delta.
  - **L4** — speech bubble: position in frame + tail direction + exact text in quotes + per-speaker attribution.
  - **L12** — close framing baked into the camera line whenever dialogue is present (`mcu` / `medium` / `cowboy` / `ecu-face`).
  - **L13** — one speaker per panel (single dialogue line in the template).
  - **L19** — SFX as 3D-extruded sculpture, speech bubble as photoreal 3D panel — both rendered as physical scene objects, not 2D overlays.

### Changed
- **Stage 1 (script breakdown) gate**: `build-comic.md` state table now requires `rules_audit.py` to return no HARD findings on the shotlist before stage 2 is unlocked. Surface SOFT findings but don't block. Encodes the lesson that re-planning a shotlist costs nothing while regenerating panels wastes the API budget.
- **`next_panel.py` build_plan output**: now includes `WARNING_DIALOGUE_CAMERA_CONFLICT` and `WARNING_MULTI_SPEAKER_CROWDING` entries in `refs_to_attach` when the relevant detectors fire. Same HALT semantics as `MISSING_*`.
- **`build-comic.md` hard rules**: added new `Script-breakdown-stage rules` section (Step 0 questionnaire, rules audit at end of script-breakdown, transformation decomposition); added L10 identity-vs-pose refinement, L12 dialogue-camera, L13 multi-speaker split, L14 multi-view location refs to `Generation-stage rules`.
- **L4 un-deprecated.** L4 (speech bubble positioning, tail direction, attribution) was marked DEPRECATED because L7 Case B deferred all bubbles to `page-composer`. With L19 reversing that prescription, L4 is back to active — bubble positioning, tail direction, and per-speaker attribution all matter again because bubbles are now in the render.
- **L7 Case B rule flipped from "never bake lettering" to "bake lettering + anchor aggressively."** Worked example rewritten to show baked SFX + speech bubble with full DAZ3D anchoring and `NOT a comic, NOT an illustration` negation rather than stripped-out lettering deferred to `page-composer`. "Where this rule does NOT apply" updated to drop the page-composer-deferral bullet that contradicted the new rule. Historical note retained inline so the reversal reads cleanly to future agents skimming the file.

---

## 2026-05-12

### Added
- **L11 — Cartoony FMG proportions need explicit anchoring or the model regresses to realistic fitness** (`78815c5`, `7905431`). New lesson + supporting reference doc at `skills/comic-production/references/peak-body-scale.md`. Diagnosed from the April-claudemade and Supergirl runs: generated tier-4+ panels were visibly *smaller* than declared because (1) the lineup ref was attached on too few panels, and (2) prompt vocabulary like "match the muscle proportions of figure N" was too gentle, letting the model regress to its realistic-fitness prior. Two-part fix:
  - **Attachment rule broadened (replaces L5)**: `should_attach_lineup()` in `next_panel.py` now returns True on **stage-change OR full-body camera** (`front-full`, `3q-full`, `side-full`, `back-full`, `low-angle-front`, `low-angle-back`, `splash`). ECU and mcu skip. On Flow refs are free; the silhouette consistency gain outweighs slight composition risk.
  - **Vocabulary upgrade**: for any tier ≥ 2 panel, `compose_prompt()` emits a "cartoony hyper-FMG comic-book proportions, NOT realistic fitness modelling" anchor before the action delta, a tier-specific silhouette descriptor with dimensional anchors (e.g. tier 4: "shoulders 2x normal width with clear deltoid mass, large defined biceps and triceps, full powerful chest, ridged abdominal definition, strong sculpted quads"), a "Render the silhouette TO MATCH the lineup figure — do not approximate to a smaller realistic build" directive, and an explicit "NOT realistic fitness, NOT athletic" negation.
- **`peak-body-scale.md` reference doc** (`78815c5`): tier-by-tier silhouette catalog (1–9), working vocabulary, vocabulary to avoid ("athletic" / "toned" pulls toward realistic fitness), failure modes. Tier 4 explicitly called out as "the friction zone" — the threshold between realistic and cartoony where the model fights the cartoony commit hardest.

### Changed
- **L11 surgical scoping** (`7905431`): the original L11 prompt told the model to "match the EXACT silhouette" of the lineup figure, which the model interpreted holistically — copying hair, face, costume, pose from the lineup figure (a brunette in white tank + gray shorts). Validated on a real Higgsfield generation of `comic-april-mutagen-v2` panel `p15-01` (tier-6 splash). The new prompt declares the lineup a "PROPORTION reference ONLY" with an explicit do-NOT-borrow list: face, hair, skin tone, clothing, costume, pose, facial expression, lighting, setting, background. Resubmit produced cartoony-big proportions WITHOUT the lineup figure's hair/clothing bleeding through. Validation: see chat session record from 2026-05-12 around 23:00 PT.
- **`panel_status()` in `next_panel.py` now recognizes both folder-naming conventions** (`7905431`):
  - `pages/panels/<panel_id>/` (older form)
  - `pages/panels/panel-<panel_id>/` (newer form used by April + Supergirl projects)
- **`panel_status()` now recognizes both accepted-image conventions** (`7905431`):
  - `_accepted.txt` (one line naming the variant, e.g. `v1`) + `v1.png`
  - `v*_accepted.png` filename suffix (used by `rules_audit` + `compose_page`)
  
  Without these fixes `next_panel.py` was silently inoperable on projects using the panel- prefix + v*_accepted.png shape — which is what the rest of the pipeline emits. The lineup-bug debugging session surfaced both.

### Fixed
- **`find_lineup()` path resolution** (`0b963c6`). Supergirl panel 13 (tier-4-tears) rendered without the muscle-size lineup attached because `find_lineup()` only looked at `~/.claude/skills/comic-production/assets/`, which doesn't exist on dev machines. The repo-bundled lineup at `skills/comic-production/assets/muscle-size-lineup.png` was invisible. Worse: the prompt composer still wrote *"match figure N in the attached muscle-size lineup reference"*, invoking a ref that was never attached — model fell back to text interpretation and produced an undersized build. Now `find_lineup()` tries, in order: project-local override (`<root>/references/style/<filename>`), repo-bundled (script-relative), user-installed (`~/.claude/...`), plugin-installed (`~/Library/.../Claude/...` glob).
- **No-phantom-refs guardrail** (`0b963c6`). `compose_prompt()` takes a `lineup_attached: bool` and only references the lineup in the prompt when it's actually attached; otherwise falls back to verbal-only growth instructions. `build_plan()` emits a loud `MISSING_lineup` entry in `refs_to_attach` when `find_lineup()` returns None on a panel that needs one; `build-comic.md` hard rule says HALT on any `MISSING_*` entry — never invoke a ref that isn't on disk.

---

## 2026-05-11

### Added
- **L10 — References are the truth, prompts are deltas** (`1202441`). Major prompt-architecture change. Diagnosed from Supergirl panels 02 vs 05 (same `lex-lab-redsun` location, env ref attached, but rendered as visibly different chambers). Root cause: per-panel prompts re-described constants (character features, location architecture, costume design) that were already encoded in attached references. Model treated text and refs as competing signals and interpolated.
  
  Fix: delta-only prompt skeleton. Prompt body describes ONLY camera, action, expression, lighting state change, costume state change. Constants delegated entirely to attached references. Every prompt ends with the load-bearing render directive: *"render the attached references exactly as shown. Do not reinterpret character appearance, costume design, or location architecture from the prompt text. References override prompt text on all visual identity."*
  
- **Env chaining (corollary of L10)** (`1202441`). First panel in a hero location attaches `_source.jpg` (the DAZ stand-in render). Once accepted, that panel becomes the location's canonical anchor — every subsequent panel in the location attaches the *accepted* establishing shot's PNG as env ref, NOT `_source.jpg`. The DAZ render did its job on the first panel; the accepted shot is more specific and prevents the model from re-interpolating architecture each panel. `next_panel.py`'s `pick_location_anchor()` walks `accepted_history` for prior panels in the same location.
- **`page-composer` script + bundled Pillow renderer** (`ccddfb9`). `skills/page-composer/scripts/compose_page.py` lettering pass. Auto-detects single-image-per-page vs multi-panel mode from shotlist. Renders balloons, thought ellipses, jagged shouts, dashed whispers, yellow caption boxes, stroked SFX. Defaults to short stub tails when `speaker_position` isn't given; optional `--pdf` via `img2pdf` (lossless). SKILL.md rewritten for single-image-per-page primary mode; multi-panel as fallback. Upgrade path logged (HTML/CSS via headless Chrome, face-aware bubble placement, smarter grids, bundled fonts, per-character styling).
- **`continuity-check` two-mode workflow** (`ccddfb9`). `skills/continuity-check/scripts/rules_audit.py` for the deterministic first pass (asset presence, monotonic muscle_size_tier, coarse 3-level costume damage non-regression with carryover phrasing recognition, stage-change lineup ref presence, field hygiene). Vision audit is agent-driven (workflow encoded in SKILL.md) — Claude Reads each panel image and diffs against shotlist intent + prior panel. Rules-first because it's fast and free; vision pass focuses on pixel-level drift the rules can't see.
- **Bundled fonts** (`e4b6bd1`). `skills/page-composer/fonts/`: Comic Neue Bold (dialogue/captions) + Bangers (SFX), both SIL OFL 1.1. Verified via Pillow. Output is now deterministic across machines. Resolution order: env var → bundled → macOS system → Pillow default.
- **Act-boundary continuity gate** (`e4b6bd1`). `/build-comic auto` now runs the rules audit at every act boundary inside Stage 3 (resolved from optional `shotlist.acts` field, or fallback every 8 pages). HARD findings pause for sign-off; clean passes continue. Stage 4 reframed as the full-issue vision audit. Hard rule added: never skip the per-act rules audit — it's free and fast.
- **`next_panel.py` helper** (`6a1d2a5`). Reads shotlist + walks `pages/panels/` for accepted-version history, applies view-aware chaining (L1.5) to pick a state anchor, identifies refs to attach (face card, env ref, muscle lineup if stage-change), maps camera category to Flow aspect ratio, composes a starter prompt. Output intended for Claude during the per-panel Flow UI loop documented in `references/shotlist-driven-flow.md`.
- **`comic-status-board` skill** (`533423a`). Surfaces project status in chat at stage boundaries via `generate_status.py` (markdown) and `generate_composite.py` (Pillow grid renderer with 3 modes: references / generation / composition). STATUS artifacts written at project root (not buried in subfolders) per user feedback, and surfaced inline via Read so the user sees them in chat.

### Changed
- **Post-L7 pipeline rewrite** (`acfb319`). Integrated `comic-production` skill; dropped `souls` stage (Higgsfield Souls training, no longer used — identity is anchored via face card + body ref chaining), dropped `style` stage (replaced by style-lock as a *preset library*, not a pipeline stage), dropped `stylize` stage (current CGI render path produces the right look directly). Added `posting` stage stub (manual today). Added hard rules: no baked-in lettering (L7 Case B), job_id capture (L9), view-aware chaining (L1.5), camera variety check, env reference for hero locations, multi-character POSE VARIATION block, single-line Flow prompts.

---

## 2026-05-09

### Added
- **`style-lock` as preset library** (`d2497c0`). `photoreal-DAZ3D` as the default preset; extensible `styles/` folder. Style-lock survives the post-L7 rewrite as a reference library for shotlist authoring, not a pipeline stage that produces `style.md`.

---

## Earlier history

Earlier commits (`311d322`, `80cea83`) predate this changelog. Initial repo bootstrap, first stylization skill draft, AI-bootstrap warning, Higgsfield-first principle. See `git log` for details.

---

## Convention for future entries

When you land a change:

1. Append under today's date heading (`## YYYY-MM-DD`). Create one if it's a new day. Reverse-chronological — newest dates at top.
2. Use **Added** / **Changed** / **Fixed** / **Removed** / **Deprecated** categories. Skip empty ones.
3. Cite the commit hash(es) in parentheses. Use the short hash form (7 chars).
4. Explain the **why** — what failure mode the change fixes or what capability it adds. Future readers (humans and agents) should be able to understand the rationale without `git log -p`.
5. Cross-reference reference docs (`peak-body-scale.md`, `lessons-learned.md` L-numbers) where relevant.
6. Keep entries scannable but complete. Multi-paragraph entries are fine when the change has real depth (like L10 / L11); one-liners are fine for narrow fixes.
7. Append the entry **before** committing, so the commit message and changelog land together.
