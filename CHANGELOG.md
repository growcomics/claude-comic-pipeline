# Changelog

All notable changes to the `claude-comic-pipeline` are tracked here.

This file is the **canonical source for what changed and why**. Any session (human or agent) editing this repo must append an entry here when it lands a meaningful change. Trivial cleanups can be skipped; anything that touches behavior, prompt architecture, the build-comic workflow, or a published reference doc must be logged.

Format: each entry is dated (YYYY-MM-DD), grouped in reverse-chronological order. Entries cite the relevant commit hash(es) and explain the *why* — what failure mode prompted the change, what the new behavior is, where readers can dig deeper.

Categories used per dated section: **Added** / **Changed** / **Fixed** / **Removed** / **Deprecated**. Skip categories with no entries.

---

## v5 — 2026-05-14 (evening sync)

This release lands the autopilot mode, the production-briefing skill, the runner infrastructure, and a Windows-compat fix. Backward compatible: existing modes (`status`, `auto`, named stage) work exactly as before. FMG-only behavior is preserved when no `production-config.json` exists.

Rollback tag: `v4` (= commit `533ec3d`). To revert: `git reset --hard v4 && git push --force-with-lease origin main` (or use GitHub's "Revert" UI on each commit). Local backup also lives at `Desktop\Claude\comic pipeline.local-original\` on the original author's machine.

### Added

- **Autopilot mode** (`/build-comic autopilot`) — runs stages 1–5 end-to-end without per-stage human gates, driven by `production-config.json` at project root. Halts only on approved hard conditions: content-policy refusal, missing required references, L12/L13 warnings, max-retries exceeded, configurable `on_all_bad` / `on_size_regression` policies. Posting (stage 6) remains manual. Sentinel files (`.autopilot-active`, `.autopilot-stage`, `.autopilot-halt-reason`) coordinate with the optional Stop hook. Commit `5359035`.

- **`production-briefing` skill** — one-shot pre-flight interview that collects every decision the rest of the pipeline would otherwise interrupt for (transformation type, style preset, location strategy, mandatory-rule modifications, lineup files, generation policies, continuity policies) and writes `production-config.json` v3. Auto-invokes when `/build-comic autopilot` finds no config. Also triggers on natural-language phrases like "start a new BE comic" / "configure autopilot". Lives at `skills/production-briefing/`. Commit `5359035`.

- **`autopilot/` directory at repo root** — centralizes the autopilot infrastructure for discoverability:
  - `autopilot/configs/production-config.schema.json` — v3 schema.
  - `autopilot/configs/example-{fmg,be,glute,mmg,mixed}.json` — per-transformation-type starter configs.
  - `autopilot/hooks/stop-autopilot.py` + `pre-tool-autopilot.py` + `INSTALL.md` + `settings-snippet.json` — opt-in Claude Code hooks for fully silent runs.
  - `autopilot/patches/` — per-file patch documentation (informational; patches are already applied in this release).

- **Runner infrastructure under `runners/`** — Python orchestrator + Flow / Higgsfield backends + variant picker that build-comic's generation stage drives:
  - `runner_core.py` — shared orchestrator loop with halt-detection, per-panel retry budget, state.json persistence, resume support.
  - `flow_runner.py` + `flow_selectors.py` — Chrome MCP-driven Flow backend.
  - `higgsfield_runner.py` — direct HTTP backend via `token_relay.js`.
  - `variant_picker.py` — heuristic + Anthropic-API strategies for picking the best variant per panel.
  - `requirements.txt` + `README.md`.
  - Commit `d1fec10`.

- **Test infrastructure under `tests/`** — three runnable test scripts (no `pytest` dependency):
  - `test_runner_loop.py` — end-to-end resume + halt + retry with a mock backend.
  - `test_flow_runner_mock.py` — Flow backend instantiation, CDP-unreachable cleanup, locator fallback, ref-attach error handling.
  - `test_variant_picker.py` — heuristic + claude_api strategies, JSON extraction, API-key-missing fallback.
  - Commit `d1fec10`.

- **Integration docs under `docs/`** — `ARCHITECTURE.md`, `FLOW-SELECTORS.md`, `HIGGSFIELD-INTEGRATION.md`, `VARIANT-PICKING.md`, plus a refreshed `INSTALL-V4.md` at repo root covering the v5 setup. Commit `d1fec10`.

- **Per-transformation-type rule defaults** in `skills/comic-production/SKILL.md` — five-row table mapping `transformation_type` (FMG / BE / Glute / MMG / Mixed) to its default `mandatory_rules.active` set, with rationale per rule. `production-briefing` writes the right defaults into the config; comic-production reads them. Commit `5359035`.

- **`L19 baked-lettering opt-in`** documented in `skills/comic-production/SKILL.md` — when `mandatory_rules.allow_baked_lettering` is true, prompts open with the L19 render-engine anchor, render lettering as physical 3D scene objects, and close with the negation block. Default is false (clean panels to page-composer for vector lettering). Commit `5359035`.

- **Per-project lineup file resolution** in `skills/comic-production/scripts/next_panel.py` — `_read_production_config()` helper + `find_lineup()` now resolves `lineup_files.tier_low / tier_high / active_range` from `production-config.json` so BE / glute / MMG projects can ship their own size-anchor PNGs under `<project>/references/style/`. Falls back to the FMG defaults (`muscle-size-lineup.png` / `muscle-size-lineup-4-9.png`) when the config block is missing. Commit `5359035`.

### Changed

- **`skills/comic-production/references/shotlist-driven-flow.md` per-panel break conditions are now policy-keyed** via `production-config.json`. Default `generation.on_all_bad: retry-with-cgi-anchor-boost`, `generation.on_size_regression: retry-with-aggressive-anchor`, `generation.on_anatomy_failures: pick-best-and-flag`. Without config, falls back to the legacy "ask the user" behavior. Commit `5359035`.

- **`skills/continuity-check/SKILL.md` § 2.6 hand-back is now policy-driven** via `policies.regeneration` — four options (`never` / `batch-end` / `auto-on-hard` / `halt-on-hard`). Default `batch-end`: log report, complete composition, halt at end with report path so the user picks what to regenerate. Without config, falls back to the legacy "ask which to fix" interrupt. Commit `5359035`.

- **`commands/build-comic.md`** rewritten to support three operating modes (`status`, `auto`, `autopilot`) and to document the autopilot halt conditions, sentinel files, and briefing auto-invocation flow. The interactive and `auto` modes are unchanged in behavior. Commit `5359035`.

### Fixed

- **`skills/continuity-check/tests/run_tests.py` Windows compat.** The fixture test runner subprocess-invoked `python3`, which doesn't exist on PATH on Windows (the Microsoft Store shim intercepts and prompts to install Python). Now uses `sys.executable`. After the fix all 9 fixtures pass on Windows. Commit `e4e15e3`.

### Notes

- The patches and the new files in this release have been smoke-tested against two real comic projects (Aria Stellaris FMG + Mike Reeves MMG, 6 panels each, 1:1 photoreal CGI on nano_banana_2) and all 12 panels composed successfully with the lettered pages exported as PDF. The runner test suite (9 + 3 = 12 scripts) passes clean on Windows 11.
- The `~/.claude/hooks/` Stop and PreToolUse hooks are opt-in: install them only if you want autopilot runs to suppress mid-pipeline halts. Without the hooks, autopilot still works; you just see the natural Claude `Stop` events in chat. See `autopilot/hooks/INSTALL.md`.

---

## 2026-05-14

### Added
- **L21 — Suppress in-scene rendering of reference images.** New lesson. nano_banana_flash occasionally renders an attached face-card or lineup ref as a literal physical scene object — a tiny photo stuck to fabric, a badge, a poster. Caught on chun-li-ascension v2 p05 (arms beat ECU): the face card rendered as a small photo tucked into the torn sleeve seam. Fix: every panel prompt that attaches an `image`-role ref must include the exclusion clause *"DO NOT render any reference image as a physical photo, badge, poster, or scene object."* Enforcement layer (auto-injection in `compose_prompt()`) logged as a follow-up.
- **L22 — Hair state must be explicit in every face-visible panel.** New lesson. Hair accessories (twin buns + red ribbons) drift across panels when relying on state-anchor inheritance alone. Caught on chun-li-ascension v2: p04 rendered a single decorative updo, p06 rendered a single back-of-head bun, p03 ribbons drifted from red to grey — all panels described hair only implicitly via the state anchor. Fix: every panel where the head is in frame must include an explicit hair line derived from tier + transformation_beat (`pre-suit-fail` → twin buns + ribbons; `suit_fail` → shaking loose; `post-suit-fail` → fully loose). `compose_prompt()` needs a `hair_state` derivation step; logged as a follow-up.
- **L23 — When env ref is dropped, add a dense verbal env anchor.** New lesson. Stage-change full-body panels need lineup ref attached (L11), which combined with face card + state anchor hits the 3-ref ceiling and forces the env ref to be dropped. Without explicit verbal env anchoring, the background collapses to a grey/blurry studio void. Caught on chun-li-ascension v2 p06: hyper-FMG Chun Li rendered against a neutral grey void instead of the dojo every other panel shows cleanly. Fix: when `compose_prompt()` drops the env ref, it must inject 5+ named location elements with concrete adjectives into the prompt body. Auto-injection of `locations[].description` logged as a follow-up.
- **L24 — Suppress anachronistic accessories explicitly.** New lesson. Models hallucinate modern accessories — wristwatches, bracelets, rings, earrings, necklaces — on characters even when the canonical character has none. Wrists, neck, ears, and ring fingers are hot spots. Caught on chun-li-ascension v2 p02: Chun Li rendered with a dark wristwatch on her right wrist alongside the canonical white spiked wristband. Fix: when those body parts may be in frame, include both a canonical-inventory line AND an explicit negation list — the negation list is the load-bearing part. Per-character accessory inventory derivation in `compose_prompt()` logged as a follow-up.
- **Load-bearing index** in `lessons-learned.md` updated to include L21–L24.

### Changed
- **Continuity audit must walk a structured rubric, not free-form.** Documented in the root-cause sections of L21–L24. The chun-li-ascension v2 audit ran inline at the end of generation and free-form ("does this panel look right?"), passed all 14 panels, and was wrong: user spotted 6 distinct issues across 4 panels (identity drift at p12, hair drift at p03/p04/p06, env void at p06, ref artifact at p05, wristwatch at p02). All would have been caught by a structured per-panel rubric pass with the canonical refs open. Going forward the audit pass should be delegated to a fresh subagent with the rubric as its prompt and a markdown-table return format, NOT run inline by the agent that produced the generations.

### Added (later in the same day — Grok validation + L21-L24 auto-injection landed)
- **`compose_prompt()` auto-injection for L21–L24 landed in `next_panel.py`.** Was logged as a follow-up at the top of this 2026-05-14 entry; now done. New helpers `L21_REF_EXCLUSION`, `_hair_state_line`, `_env_dense_anchor`, `_l24_accessory_line`, `_female_anatomy_anchor_needed` + `FEMALE_ANATOMY_ANCHOR`. `compose_prompt()` calls them in the appropriate slots: L21 after the render-directive sentence when any ref is attached; L22 in subjects/style section when `panel.hair_state` is explicitly set (NOT auto-derived — see "Don't invent transformation state changes" below); L23 in the env slot when env_ref is None but location_slug is set and env_dropped=True; L24 in subjects section when camera might show wrists/neck/etc and the character has an `accessories` block in cast[]. Female-anatomy anchor injected on body-region ECUs (camera=`ecu-region`) at tier ≥ 2 for female arc characters (heuristic: `cast[].sex == "f"` or `pronoun in {"she", "her"}`, default true). All five injections smoke-tested via synthetic shotlist; L21–L24 + female-anatomy all fire correctly.
- **3-ref ceiling enforcement in `build_plan()`.** When face_card(s) + state_anchor + lineup + env would exceed 3 refs (per `chun-li-ascension v2 p06`-style stage-change full-body panels), `build_plan` now drops the env_ref and passes `env_dropped=True` to `compose_prompt()` so the dense verbal anchor (L23) fires automatically. The env entry in `refs_to_attach` is relabeled `env_*_dropped_for_ceiling` with a reason so the production driver knows the prompt is carrying the verbal fallback.
- **`MODEL_MUSCULARITY_CEILING` table + WARNING in `build_plan`.** Per-model cap on female muscularity that the model actually delivers in practice. Currently `{ "grok_image": 3 }` — Grok refuses tier 4+ female silhouettes regardless of prompt or lineup attachment. When `panel.muscle_size_tier > ceiling`, `build_plan` emits a `WARNING_MODEL_MUSCULARITY_CEILING` entry with a routing recommendation (use `nano_banana_flash` or `nano_banana_2` for that panel). Empirical basis: the chun-li-grok-validation run on 2026-05-14 (see `chun-li-grok-validation/comparison-report.md`).
- **3-way model comparison report.** `chun-li-grok-validation/comparison-report.md`. Same 6-panel shotlist on Grok, Nano Banana 2 Flash, GPT Image 2 (medium quality) using the new face-card-beauty.png. Findings: (a) NB2 wins on pipeline obedience (tier scale, ECU framing, pose deltas all on-spec); (b) GPT2 wins on raw face/aesthetic quality but its safety filter hard-blocks FMG body-region ECUs even on reframed prompts (matches memory `feedback_gpt_image_2_nsfw_strict`); (c) Grok's tier-4+ female-muscularity ceiling confirmed across multiple panels and tries. Recommendation matrix: tier-1 dialogue/intro panels → GPT2 or NB2; body-region ECUs at tier ≥ 2 → NB2 only; stage-change full-body at tier ≥ 4 → NB2 primary, GPT2 alternate for more aggressive scale; skip Grok on anything beyond tier 2-3.
- **New face card `face-card-beauty.png` regenerated.** Higgsfield job `485d3e78-3541-4964-917f-005e90143ee0`. The v1 face card had a white cloth wrap around the twin buns that propagated as drift into every panel of chun-li-ascension v2 and the chun-li-grok-validation run. The regen has clean dark buns + two visible bright red ribbons. Old face card archived alongside as `face-card-beauty-v1-archived-20260514.png`. Provenance updated. Memory `project_chun_li_beauty.md` notes the regen so future sessions know.
- **New feedback memory: "Don't invent transformation state changes."** `~/.claude/projects/-Users-mattmenashe-Documents/memory/feedback_dont_invent_state_changes.md`. "Stage change at tier N" = tier bump only; do NOT auto-add `suit_fail` beat / hair-down state / costume-destruction language unless the user explicitly named them. Caught during the Grok validation when I autonomously escalated the user's "tier 4 stage change" to `suit_fail` + hair shaking loose, then the audit graded Grok's intact-buns rendering as L22 HARD-FAIL — but the buns staying up was actually CORRECT given the actual brief.

### Open (logged for future work)
- `rules_audit.py` / `continuity-check` skill: add a vision-audit subroutine that takes canonical refs + generated panels and returns a pass/fail rubric per panel. Today `continuity-check` enforces script-time structural rules only; the per-panel vision audit is still a manual step run by the agent.
- Add GPT Image 2 to `MODEL_MUSCULARITY_CEILING` (or a separate "MODEL_BODY_REGION_NSFW_BLOCK" table) once we have a confirmed threshold. Currently we know GPT2 hard-blocks tier-5 body-region ECU on FMG; we don't yet know the lower bound.
- Multi-view location refs (L14) extension of `pick_location_anchor()` still pending — not addressed in this round.

---

## 2026-05-13

### Added
- **`CHANGELOG.md`** (this file) at repo root. From now on, every session that lands a meaningful change must append an entry here. See the header for the convention.
- **L20 — Camera distance bias for transformation comics.** New lesson with empirical basis: hand-made April mean camera distance **2.4** (between MCU and medium); AI-generated April **4.1** (between cowboy and full body), bimodal with zero panels in the middle distances {MCU, medium, cowboy}. The transformation event never *happens* on the AI version because the camera is too far to show body-region beats — chest growth at full-body framing reads as "before/after" not "the change happening now." Fix: default body-region beats to MCU / ecu-region; reserve `full` for the `reveal` beat; aim for chapter mean ≤ 3.0 and ≥ 30% of panels in middle distances. See `skills/comic-production/references/camera-distance-analysis/README.md` for the source data and full per-page scoring.
- **L20 enforcement layer.** `rules_audit.py` `check_camera_distance_bias`: HARD if chapter mean distance > 3.0; HARD if middle-distance fraction < 30%; SOFT per-beat finding when a non-`reveal` transformation beat is shot at a distance wider than the per-beat ceiling in `script-breakdown/SKILL.md` § Step 4.5. `next_panel.py` emits `WARNING_CAMERA_TOO_FAR_FOR_BEAT` at planning time. `build-comic.md` hard rule cites L20 with the gates as HALT conditions. Smoke-tested: AI-failure shape produces 2 HARD + 7 SOFT; hand-made shape is clean.
- **Top-of-file load-bearing index** in `lessons-learned.md`. Eleven lessons (L1, L1.5, L9, L10, L10 refinement, L11–L14, L19, L20) listed with one-line summaries at the top of the file. L-numbers remain chronological (no renumbering); importance is signaled via the index + build-comic.md hard-rule citations.
- **`skills/comic-production/references/camera-distance-analysis/`** directory with `README.md` (the empirical write-up) plus two infographic JPEGs. Source for L20.
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
- **Second A/B run: L-lesson index table rendering (text-heavy artifact).** Generated an image of the L-Lesson Index reference table itself (17 rows × 4 columns: #, Title, Summary, Status — pulled straight from `lessons-learned.md`) on both models, 1k / 2:3 / count=1 each. Artifacts stored at `skills/comic-production/references/master-prompt-template/l-lesson-index-nano-banana-2.png` and `l-lesson-index-gpt-image-2.png`.
  - Nano Banana 2 (`nano_banana_flash`) → job `bb817a0e-5897-4d35-b0a4-b1ea16c9fc37`
  - GPT Image 2 (`gpt_image_2`, quality=medium) → job `8b3f9d74-0366-4a71-8ef8-b49b8cc8aae6`

  **Verdict (surprising): Nano Banana 2 won this round.** Crisper text rendering at 1k, correct status pill color coding (green for `active`, amber for `superseded by L11` on L5). GPT Image 2 rendered the same table at slightly softer / fuzzier resolution and appears to have rendered all status pills green — missed the amber pill for L5. Both models nailed the overall layout: 18-row table, four-column structure, header row, title row. GPT Image 2 is tagged for text-rendering in its model description and almost certainly wins at `quality=high` + `resolution=2k`, but at the matched 1k / medium settings Nano Banana 2 delivered the better artifact.

  **Implication for the pipeline**: for text-heavy reference graphics (status boards, lesson indexes, shotlist tables, panel cheat-sheets), don't reflexively reach for GPT Image 2 at default settings. At 1k / quality=medium Nano Banana 2 is competitive and faster. Reserve GPT Image 2 for jobs where you'd actually pay for `quality=high` + `resolution=2k`, or where the typography is the primary deliverable (e.g. a hero infographic, not an internal reference).

### Changed
- **Stage 1 (script breakdown) gate**: `build-comic.md` state table now requires `rules_audit.py` to return no HARD findings on the shotlist before stage 2 is unlocked. Surface SOFT findings but don't block. Encodes the lesson that re-planning a shotlist costs nothing while regenerating panels wastes the API budget.
- **`next_panel.py` build_plan output**: now includes `WARNING_DIALOGUE_CAMERA_CONFLICT` and `WARNING_MULTI_SPEAKER_CROWDING` entries in `refs_to_attach` when the relevant detectors fire. Same HALT semantics as `MISSING_*`.
- **`build-comic.md` hard rules**: added new `Script-breakdown-stage rules` section (Step 0 questionnaire, rules audit at end of script-breakdown, transformation decomposition); added L10 identity-vs-pose refinement, L12 dialogue-camera, L13 multi-speaker split, L14 multi-view location refs to `Generation-stage rules`.
- **L4 un-deprecated.** L4 (speech bubble positioning, tail direction, attribution) was marked DEPRECATED because L7 Case B deferred all bubbles to `page-composer`. With L19 reversing that prescription, L4 is back to active — bubble positioning, tail direction, and per-speaker attribution all matter again because bubbles are now in the render.
- **L7 Case B rule flipped from "never bake lettering" to "bake lettering + anchor aggressively."** Worked example rewritten to show baked SFX + speech bubble with full DAZ3D anchoring and `NOT a comic, NOT an illustration` negation rather than stripped-out lettering deferred to `page-composer`. "Where this rule does NOT apply" updated to drop the page-composer-deferral bullet that contradicted the new rule. Historical note retained inline so the reversal reads cleanly to future agents skimming the file.
- **`prompt-templates.md` reconciled with L19.** Three deprecation notices in `skills/comic-production/references/prompt-templates.md` still pointed at L7 Case B's old "never bake lettering" rule (file header `STATUS: PARTIALLY DEPRECATED`, the Mandatory Rules Block `⚠️ PARTIALLY DEPRECATED` notice, and two `(⚠️ deprecated per L7 Case B)` bullets in the "Why each rule exists" list). All three now reflect L19: lettering IS baked into the CGI render, paired with the opening render-engine anchor and closing `NOT a comic, NOT an illustration` negation block. The **Action Lines and SFX** section's prompt block was rewritten from comic-burst phrasing ("RRRRIP! as red/yellow burst text", "action lines radiating outward") to L19's physical-scene-object phrasing (3D-extruded chrome letter sculptures with real ray-traced shadows, motion told through sweat/fiber/dust/blur instead of 2D overlays). The **Dialogue Formatting** section was promoted from "obsolete" to "active — applies whenever you bake a bubble," with a new long-form CGI/L19 bubble template alongside the legacy shorthand and a reference to L4's positioning rules.

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

---

## 2026-05-14

### Added
- **L25 — Body-region reveals are sticky.** New lesson. Once a body region is exposed in any panel (e.g., Susan's abs in p3-04 ecu-region with blouse riding up), every subsequent post-reveal panel whose camera includes that region must include explicit costume directives that PRESERVE the exposure. Drifted in moving-experience-v2 p4-01 first take (long full blouse covered the abs that were canonical from p3-04). Fix: costume_state in post-reveal panels must specify "knotted blouse CROPPED above the abs at the ribcage, full hyper-muscular abdomen visible between the knot and the skirt waistband" rather than vague "tied at chest" phrasing.
- **L26 — Costume identity must be canonical across panels.** New lesson. Vague costume description ("white top tied at chest") lets the model interchange garment FAMILIES across panels — p4-01 first take rendered as strapless bandeau wrap, p4-02 rendered as collared sleeveless button-up blouse, both technically "tied at chest." Fix: name the garment family explicitly — "knotted button-up collared sleeveless blouse with the original collar visible at the neck and the original blouse buttons visible on the cropped fabric." For remnant costumes: name the intact garment + the destruction state.
- **L27 — Skin sheen / texture continuity across panels.** New lesson. Hyper-muscular silhouettes amplify skin specular drift — p4-02 rendered with oiled-bodybuilder competition shine while p4-01 (immediately preceding) was matte natural. Fix: name skin sheen explicitly with consistent vocabulary on every prompt — "natural healthy MATTE skin (subtle subsurface scattering only, NOT oiled, NOT wet, NOT bodybuilder competition shine)." Allowable per-panel variation: lighting + exertion sweat; not allowable: bodybuilder-grease that tracks muscle topography.
- **moving-experience-v2 chapter** at `/Users/mattmenashe/Documents/moving-experience-v2/` — 26-panel v2 retry of Gribble's "A Moving Experience" script. Surfaced L25/L26/L27 during the audit pass; p4-01 regenerated to verify the canonical "knotted button-up collared blouse cropped at ribcage + matte skin" prescription holds.
- **`the-rules-explained.md`** — plain-English explainer article in `skills/comic-production/references/` that walks every active L-lesson (L1 through L27 plus L1.5 and L10-refinement) for a general audience. Grouped by theme: chaining & state / refs vs prompts / bodies & proportions / cameras & framing / dialogue & lettering / environments / anti-hallucination / cumulative state. Includes a "lessons proposed but not yet enforced" callout for L15–L18 (still in the running feedback list) and short notes on superseded/historical lessons (L2–L8). Paired with 8 infographic graphics generated via GPT Image 2 on Higgsfield, saved under `references/the-rules-explained-graphics/`: pipeline flow, refs vs prompts split, silhouette ladder (L11), dialogue framing comparison (L12), camera distance scale with the April benchmark (L20), baked-vs-overlay lettering (L19), anti-hallucination collage (L21-L24), multi-speaker split (L13).

### Open (logged for future work)
- `compose_prompt()` enforcement layer for L25/L26/L27: derive per-character canonical post-transformation costume from cast[] entry + transformation_metadata + auto-inject in post-reveal panels; auto-inject skin sheen vocabulary on every prompt of any character with `muscle_size_tier` >= 2.
