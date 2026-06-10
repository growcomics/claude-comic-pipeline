# Shotlist-Driven Generation on Google Labs Flow

The deterministic, iterative way to run a multi-panel chain on Flow when a `shotlist.json` exists. Replaces the hand-driven mode (every panel = manual UI clicking + manual prompt typing) with a per-panel automated loop that **still preserves the iterative "see prior, retry until good, then chain" rhythm**.

## Design principle (non-negotiable)

The shotlist is **structural data, not pre-composed prompts**. Prompts are composed at runtime, after the prior panel has been observed. The chain advances only when the human accepts a rendered panel. Retries are effectively unlimited and free (Nano Banana 2 on the paid plan), and they do not move the chain.

Three things are decoupled:
- **Shotlist** = long-lived plan, updateable mid-run
- **Composed prompt** = regenerated each attempt based on currently observed state
- **Chain advancement** = only on human "accept"

Read alongside:
- `flow-workflow.md` — the underlying Flow mechanics (Omni-agent chat UI, Agent settings, variant strategy, reference attachment, downloads). **Read it first — it is the source of truth for UI mechanics**, including the Legacy Appendix if Flow ever rolls back to the pill UI.
- `prompt-templates.md` — the fragment library (style prefix, environment descriptions, character-size language)
- `cinematic-framing.md` — camera categories, prompt fragments per category, rhythm patterns
- `multi-character-variation.md` — anti-uniformity rules and the mandatory POSE VARIATION block
- `posing-and-expressions.md` — facial-acting mechanics
- `environment-references.md` — the DAZ3D-scene-ref trick (env attachment per panel)
- `lessons-learned.md` — especially **L1.5** (view-aware chaining), **L5** (lineup ref only on stage changes), **L7 Case B** (no baked-in lettering), **L9** (job_id capture discipline)

---

## Inputs

- **`shotlist.json`** at project root, produced by `script-breakdown`. Per panel:
  - `panel_id`, `page_number`, `size` (panel size: splash/wide/tall/standard — different from muscle size)
  - `characters[]` (slugs into `cast[]`)
  - `location` (slug into `locations[]`)
  - `time_of_day`, `weather`
  - `camera` (distance + angle + optional modifier, per `cinematic-framing.md`)
  - `action` (one or two short sentences, present tense, what's seen)
  - `dialogue[]`, `captions[]`, `sfx[]` (**data only — NEVER baked into the generation prompt** per L7 Case B; consumed later by `page-composer`)
  - `continuity_refs[]` (panel_ids this panel inherits state from — e.g., scene's establishing panel)
  - `muscle_size_tier` (1–6, where applicable for transformation arcs)
- **Reference cards already built and uploaded in Flow** (per `flow-workflow.md`):
  - `cast[].ref_folder` populated with a face card per character
  - `locations[].ref_folder` populated with `_source.jpg` per hero location (per `environment-references.md`)
  - `muscle-size-lineup.png` and/or `muscle-size-lineup-4-9.png` uploaded as assets
- **Chain log** at `<project>/job_ids.md` (or equivalent) — accepted-panel record. Initially has the baseline body ref and face card IDs.

## Outputs

- `<project>/pages/panels/<panel_id>.png` — one image per accepted panel
- Updated `<project>/job_ids.md` — accepted-panel chain log
- All unused fan-out candidates archived in Flow at end of run

---

## Defaults on Flow

- **Agent settings first** (sliders icon in the session chat panel — `flow-workflow.md` "UI Anatomy"): **confirm = Never** (or every submit stalls on a confirmation click), **model = Nano Banana 2** (Pro only if explicitly wanted and its daily quota allows), **count = 1** (one chat submit produces exactly ONE image regardless of this setting — keep the setting honest).
- **Variants on demand — the x4-always strategy is dead.** A submit yields one image no matter what count says; variants now cost a follow-up chat message (`flow-workflow.md` "Variant Strategy"):
  - **Predictable chain stages**: submit once and evaluate. The chain advances only on an accepted panel, so re-roll on demand instead of pre-paying for variants.
  - **Novel panels** (new pose category, stage change, money-shot) **or a weak first result**: fan out with `Run that exact same prompt 3 more times as 3 separate image generations, verbatim.` → up to 4 candidates, pick the best. Verify each re-run's detail-view prompt actually matches the original. Unused candidates are archived at end of run (see "End-of-run cleanup" below).
- **Aspect ratio** derived from `camera` and panel `size`:

  | camera category | shotlist `size` | Flow aspect |
  |---|---|---|
  | `ecu-face`, `ecu-region` | any | **1:1** |
  | `front-full`, `3q-full`, `back-full`, `low-angle-front`, `low-angle-back`, `profile` | standard | **3:4** |
  | `wide-establish`, `splash` (front-facing) | any | **16:9** |
  | tall vertical | tall | **9:16** |
  | medium / mcu / cowboy (waist-up) | standard | **4:3** |
  | splash (portrait composition) | splash | **3:4** |

  Aspect is an Agent-settings default — it persists until changed. When a panel's aspect differs from the previous submit, reopen Agent settings and change it before submitting.

- **No baked lettering.** Dialogue, captions, and SFX are data in the shotlist; they are NEVER written into the generation prompt. The render must be clean (L7 Case B). Lettering happens in `page-composer`.

---

## The helper script — `scripts/next_panel.py`

This script does the deterministic part of the per-panel loop for you. It reads the shotlist + the on-disk accepted-panel history, runs the view-aware chaining logic from L1.5, picks the right refs to attach, maps the camera category to the Flow aspect ratio, and emits a starter plan with a composed prompt. You then drive Flow's UI with that plan.

```bash
python ~/.claude/skills/comic-production/scripts/next_panel.py <project_root>
```

Output is human-readable text. Add `--as-json` for machine-readable JSON.

What it handles for you:
- Identifying the next pending panel (first shotlist entry without an `_accepted.txt` marker or flat-layout file at `pages/panels/<panel_id>.png`)
- Walking accepted history backwards to find the most recent view-compatible state anchor (per L1.5's compatibility table)
- Detecting stage-change panels (when `muscle_size_tier` differs from the prior accepted panel's tier) and attaching the lineup ref per **L5**
- Mapping the panel's camera category to the Flow aspect ratio
- Resolving each character's face card path and each hero location's `_source.jpg`
- Composing a starter prompt that's L7-compliant: positive CGI anchor up front, no baked-in lettering, single closing `Photographic CGI render, NOT illustrated.` negation
- Including a state-anchor reference to the chosen prior panel in the prompt so chain continuity is explicit

What stays as Claude's work:
- Driving the Flow Omni chat (Agent settings, ref attachment, chat submits, fan-out decisions) per the per-panel loop below
- Observing the prior accepted panel and tweaking the prompt for state carry-forward observations (cumulative damage, hair state) the script can't infer from the shotlist alone
- Evaluating the result — and picking among candidates when a fan-out was run — per the criteria below
- Deciding retry vs accept at the per-panel checkpoint

Use the script's output as the starting point. Read it, observe the prior panel's actual rendered output, then refine the prompt with any state-carry-forward language and submit.

---

## The per-panel loop

For each panel N in shotlist order:

### 1. Pick the state anchor (view-aware, per L1.5)

- Tag panel N's view category from its `camera` field.
- Walk backwards through accepted panels (N−1, N−2, …) and stop at the most recent one whose view is in the compatibility set for N's view. Compatibility table is in `lessons-learned.md` L1.5.
- If no prior accepted panel is compatible, fall back to the canonical character ref that matches the target view (e.g., back ref for a `back-full`), plus verbal state carry-forward in the prompt.
- For `ecu-face` panels: the face card alone is the canonical anchor (no body ref needed).

### 2. Identify the refs to attach

Order them in this priority (attach all that apply):

1. **State anchor** (from step 1)
2. **Face card** — `cast[N's primary character].ref_folder/face-card.png` (canonical portrait)
3. **Environment ref** — `locations[N's location].ref_folder/_source.jpg` — only if the location is a "hero location" with a `_source.jpg` saved (per `environment-references.md`)
4. **Muscle-size lineup** — **only on stage-change panels** (per L5). A panel is "stage-change" if `muscle_size_tier` is different from the prior accepted panel's tier. Attach `muscle-size-lineup.png` (sizes 1–6) or `muscle-size-lineup-4-9.png` (sizes 4–9) depending on which range applies. **Never attach both lineups** — overlapping size numbers confuse the model.
5. **Specialized prop refs** — `props[id].ref_folder/_source.jpg` if the panel references a hero prop with a ref folder

**Attachment mechanics under the Omni UI are not yet re-verified** — see `flow-workflow.md` "Reference Attachment" for the verify-first checklist (attach affordance on the chat input, in-thread selection by the agent, surviving legacy surfaces). Burn a couple of throwaway gens to pin the mechanic down before starting the loop. Assume refs do NOT persist between submits — re-attach the full set on every panel — and confirm which images the agent actually used (detail-view prompt plus a visual check against the intended anchor).

### 3. Compose the prompt at runtime

Compose the prompt as a single line (newline-as-submit was a legacy prompt-bar behavior; multi-line in the Omni chat input is unverified — single-line stays the safe default). The chat message leads with `Generate one image. ` so the agent doesn't get creative (`flow-workflow.md` submit pattern), then concatenates these fragments in order:

```
[1. positive CGI anchor]
[2. camera fragment from cinematic-framing.md per panel's `camera` value]
[3. character description with size language]
[4. action sentence from shotlist's `action` field, in present tense]
[5. environment description — minimal if env ref is attached; richer if not]
[6. lighting fragment matching scene's time_of_day]
[7. observed state carry-forward — see "state observation" below]
[8. mandatory rules block — the VALID portion (no speech-bubble lines)]
[9. closing CGI anchor: "Photographic CGI render, NOT illustrated."]
```

**Fragment sources**:
- Positive CGI anchor: `prompt-templates.md` "Style Prefix" (use the newer positive-anchoring vocabulary from L7 Case B worked example, not the stacked-negation version)
- Camera fragment: `cinematic-framing.md` "Prompt fragments per category"
- Character description: per character's `cast[].wardrobe` + current size description per `prompt-templates.md` "Character Size Reference Language"
- Action: verbatim from `shotlist.json` `action`
- Environment: `prompt-templates.md` "Environment Description Examples" (templates per location type) or `locations[id].description` from shotlist
- Lighting: derived from `time_of_day` + scene mood
- Rules block: `prompt-templates.md` "Mandatory Rules Block" with the **deprecated speech-bubble/dialogue lines removed**
- Closing anchor: `Photographic CGI render, NOT illustrated.`

**State observation** (the critical iterative step): before composing the prompt, look at the prior accepted panel's actual rendered output via the Flow gallery thumbnail (or `Read` the saved PNG). Note:
- Cumulative costume damage (tear locations, intactness)
- Hair state (buns intact, ribbons loose, hair down, etc.)
- Body position relative to environment (where she stands in the alley, etc.)
- Any continuity detail that the shotlist doesn't pre-specify

Carry this forward verbally: *"By this panel her qipao has cumulative tears at: shoulder seam (from prior), side slits (from prior). One ribbon already loose. Body at size 5."*

This is the iteration loop the user identified — you can only compose a strong panel N prompt after seeing what panel N−1 actually rendered.

**Multi-character panels**: also paste the POSE VARIATION block from `multi-character-variation.md`.

**Never write lettering into the prompt.** No `Comic SFX:` lines. No `speech bubble containing:` lines. No `caption:` lines. The render is clean.

### 4. Drive the Omni chat (per `flow-workflow.md` mechanics)

1. If this panel's aspect differs from the previous submit: open Agent settings (sliders icon) → change aspect → close
2. Attach the refs from step 2 (mechanics per `flow-workflow.md` "Reference Attachment" — re-verify on first use; re-attach every panel)
3. Type into the session chat: `Generate one image. <composed prompt>` → submit
4. Batch what you can (`browser_batch`: type + submit + wait + screenshot), but locate elements by fresh screenshot — the chat panel reflows as the agent thread grows; there is no stable coordinate map

### 5. Wait + collect

The legacy ~22 s wall-clock is dead — the Omni agent adds chat turnaround on top of generation, per submit and per re-run. Poll with screenshots until the result lands; re-measure before promising wall-clock times on a long chain. Then verify the result in the detail view — content AND prompt (especially after verbatim re-runs).

### 6. Claude evaluates — and fans out only when needed (this is Claude's job, not the user's)

Default behavior: **Claude evaluates without asking the user**, per the autonomous-production memory.

- **First result passes and the panel is a predictable chain stage** → accept it. No fan-out.
- **The panel is novel** (new pose category, stage change, money-shot) **or the first result fails the criteria** → send `Run that exact same prompt 3 more times as 3 separate image generations, verbatim.`, verify each re-run's detail-view prompt, arrow-key through the candidates in the detail view, and pick the best.

Evaluation criteria, in order:

1. **No 2D / illustration drift** — must be photoreal CGI (reject any candidate that drifted; if every candidate drifted, that's a prompt issue → retry with stronger CGI anchoring)
2. **Face matches canonical face card** — the character must look like the same person across the chain
3. **View / pose matches the requested category** — if Claude asked for `low-angle-front` but a candidate rendered `eye-level`, reject that candidate
4. **Costume continuity** — fabric state evolves monotonically from the prior accepted panel (per L1 — torn seams don't heal)
5. **Size continuity** — muscle/breast size is at or above the prior tier (per the "muscles never revert" rule)
6. **Anatomy clean** — exactly two arms, two legs, no extra/missing limbs
7. **No baked-in lettering** — no speech bubbles, SFX text, caption boxes in the render. (Should be ruled out by prompt design, but check.)
8. **Expressive face** — vivid, readable expression that fits the action beat
9. **Composition quality** — readable body framing, focal point clear

If two candidates tie on these, pick the one with the most direct face visibility (per `flow-workflow.md` face-card guidance).

If **zero candidates** pass the threshold: go to step 7 with "retry" automatically (don't ask the user).

### 7. Checkpoint — present the chosen result

Show the chosen result to the user with one-line reasoning ("V3 — cleanest face, costume continuity matches prior, no anatomy issues"). The user can:

- **Accept** (default; usually just continue without explicit OK) → it becomes the chain anchor for subsequent panels. Save to disk as `pages/panels/<panel_id>.png`. Log to `job_ids.md`.
- **Retry** → resubmit the same prompt (optionally with a tweak the user dictates), back to step 5. Retries don't move the chain.
- **Try a different candidate** → from the fanned-out set (when one exists), the user picks one Claude didn't pick. Same accept behavior.
- **Modify** → user edits the shotlist entry (camera, size, action, etc.), then back to step 3.
- **Skip** → advance without a new anchor (rare; falls back to last view-compatible accepted panel for downstream chaining).

If the user is silent and the result is clean, advance to panel N+1 (continue mode).

### 8. Advance to N+1

Update the chain log:
- `job_ids.md` adds an entry for panel N with the chosen result's auto-title and a saved path
- Any unused fan-out candidates are remembered for end-of-run archive cleanup

Loop back to step 1 for panel N+1.

---

## Default user-interaction mode: "narrate, don't ask"

Per the `autonomous_production_picks` memory, Claude should drive through the panels narrating progress, not asking permission per panel. Specifically:

- After each panel: post a one-line status ("Panel 3 done — V2 picked, looks clean, advancing to Panel 4")
- Only stop and ask when something genuinely needs judgment:
  - Content policy refusal (Flow's safety filter triggered)
  - The full candidate set fails the same way (prompt likely wrong, not a roll-of-the-dice)
  - A panel takes 3+ retries to land — surface for user direction
  - The shotlist's `action` is ambiguous or the camera doesn't have a sensible reading
  - Stage-change panels where the model didn't escalate size despite the lineup ref

The user can interject at any time — they don't have to wait for Claude to ask. A `pause` or `stop` interjection halts the loop after the current panel completes.

---

## When to break the loop

Behavior depends on whether `production-config.json` exists at project root.

**Without config** (legacy / `auto` mode): break and ask the user on the conditions below. This is the pre-2026-05-13 behavior.

**With config** (autopilot mode): each condition has a policy default; autopilot consults the config and either continues or halts cleanly. Halt = write reason to `<project>/.autopilot-halt-reason` and stop. The Stop hook respects the halt-reason file and allows the stop.

### Conditions

- **Content policy refusal** (Flow's safety filter triggered).
  - Config policy: not configurable — always halts. This is one of the approved halt conditions.
  - Recovery: surface the refused prompt to the user with `flow-workflow.md` "Content Policy Quirks" guidance. Most common cause: celebrity names + body description (drop the celebrity name; face card carries likeness). Second most common: heavy cleavage + "glistening/wet" stacked with size language.
  - Under the Omni UI a refusal arrives as a normal agent chat message. Don't confuse the **Nano Banana Pro daily-quota refusal** ("You've reached the daily limit for Nano Banana Pro generations.") with a policy trip — quota exhaustion is NOT a halt condition; switch the model default to Nano Banana 2 and continue (`flow-workflow.md` "Generation Mechanics").

- **`WARNING_DIALOGUE_CAMERA_CONFLICT` (L12) raised by `next_panel.py`**.
  - Trigger: on-screen dialogue paired with wide-establish or far camera. Reader can't tell who's talking.
  - Config policy: not configurable — always halts.
  - Recovery: edit the panel's `camera` in the shotlist to a close framing (`ecu-face` / `mcu` / `medium` / `cowboy`). Re-run autopilot.

- **`WARNING_MULTI_SPEAKER_CROWDING` (L13) raised by `next_panel.py`**.
  - Trigger: a panel has ≥3 dialogue lines from ≥2 distinct on-screen speakers.
  - Config policy: not configurable — always halts.
  - Recovery: split the panel into per-speaker beats in the shotlist. Re-run autopilot.

- **Max retries on one panel exceeded**.
  - Threshold: `generation.max_retries_per_panel` from config (default 3 when no config).
  - Config policy: halt cleanly when exceeded — counts as a script-ambiguity halt (the shotlist entry is producing unrecoverable results).
  - Recovery: the user inspects the panel in the project's panel folder, edits the shotlist entry (camera, action, characters), and reruns.

- **All candidates fail QA** (e.g. the full candidate set — the first result plus any verbatim re-run fan-out — drifts to 2D illustration, or every candidate has anatomy issues).
  - Config policy: read `generation.on_all_bad` (default `retry-with-cgi-anchor-boost`).
    - `halt` → write reason, stop cleanly.
    - `retry-with-cgi-anchor-boost` → resubmit ONCE with a strengthened CGI anchor prefix prepended to the prompt: "PHOTOGRAPHIC CGI render, photoreal 3D, NOT illustrated, NOT cel-shaded, NOT 2D. Octane-style materials, ray-traced lighting." This consumes one of the `max_retries_per_panel` budget. If still all-bad after the retry, halt.
    - `skip-with-flag` → save the best of the bad candidates as `pages/panels/<panel_id>/v1.png` with `_accepted.txt` noting the flag, log to `continuity-vision-report.md`'s suggested-actions list for end-of-run human review, advance to next panel.

- **Stage-change panels where the model didn't escalate size despite the lineup ref**.
  - Detection: the panel's `muscle_size_tier` is N+1 but the rendered body looks closer to tier N. This is the L11 cartoony-FMG regression.
  - Config policy: read `generation.on_size_regression` (default `retry-with-aggressive-anchor`).
    - `halt` → write reason, stop cleanly. User decides whether to retry manually or accept the underescalated render.
    - `retry-with-aggressive-anchor` → resubmit ONCE with the aggressive muscular-build anchor prepended (`compose_prompt`'s tier-N muscular-build block from `next_panel.py`, slot `8_tier_build`). Consumes one retry budget. If still underescalated, halt.

- **Anatomy issue across multiple sibling candidates** (extra limbs, weird hands, fused fingers on 2+ candidates of a fanned-out set).
  - Config policy: read `generation.on_anatomy_failures` (default `pick-best-and-flag`).
    - `pick-best-and-flag` → accept the least-bad candidate, save with `_anatomy_flag.txt` noting which body part needs touch-up, advance.
    - `halt` → stop and surface.

---

## End-of-run cleanup

After the user marks the comic complete (or the last panel is accepted):

1. **Inventory accepted panels** by reading `job_ids.md` — these are the keepers.
2. **For each panel that was fanned out**: its unused sibling candidates need archiving. Verbatim re-runs share the original prompt, so siblings share an auto-title and sit adjacent in the detail-view filmstrip (newest-first order).
3. **Archive unused candidates** — don't delete; archive is reversible. **Archive mechanics are not yet re-verified under the Omni UI**: the legacy path was hover thumbnail → 3-dots → "Archive" (see `flow-workflow.md` Legacy Appendix — that surface may have survived). Verify on one item before batch-archiving.
4. **Keep these without archiving**:
   - Baseline body ref (submit + 3 verbatim re-runs = 4 candidates; the accepted one is the canonical body — keep all 4 or archive the 3 unused; user's call)
   - Face card (same: keep all 4 or archive the 3 unused)
   - Env refs and lineup uploads (always keep)
   - All accepted panels
5. **Verify the final folder** at `<project>/pages/panels/` has one PNG per accepted panel, named per `panel_id`.

If Flow's project becomes heavy with 25+ active generations and the page slows, archive in batches as you go (every 10 panels) rather than waiting until the end. (We hit a frozen-page bug on the Chun-Li v2 run; archiving prevents accumulation.)

---

## Higgsfield equivalent (briefly)

If the project is using Higgsfield instead of Flow, this whole document is replaced by the existing `runner.py` workflow in the comic-production skill, plus a thin translator that converts `shotlist.json` to `panels.json`. The per-panel iterative loop is the same; the UI driving is replaced by the Python runner reading `panels.json` and the runner already captures job IDs into `state.json`. Variant handling differs on Higgsfield: each `panels.json` entry produces one image and there is no fan-out follow-up — the candidate-pick step doesn't apply; retries are explicit re-runs with `--start N`.

That translator is a separate piece of work; see `build-comic.md` for the orchestrator that routes to either platform.

---

## Quick reference: per-panel actions in order

```
1. Read shotlist[N], identify view category, time_of_day, location
2. Walk backwards through accepted panels for view-compatible state anchor
3. Observe prior accepted panel's actual output (cumulative damage, hair state, etc.)
4. Compose prompt at runtime:
   - positive CGI anchor + camera fragment + character + action + env + lighting
     + observed state carry-forward + valid rules block + closing "Photographic CGI render, NOT illustrated"
   - NO speech bubbles, NO SFX text, NO captions, NO action lines
5. Attach refs (state anchor → face card → env ref [if hero location] → lineup [if stage change])
   — re-attach every panel; mechanics per flow-workflow.md "Reference Attachment" (re-verify on first use)
6. Aspect via Agent settings if it changed (count stays 1; confirm=Never set once at session start)
7. Chat: "Generate one image. <composed prompt>" — poll with screenshots (legacy ~22s no longer holds)
8. Evaluate the result (criteria above); novel panel or weak result → "Run that exact same prompt
   3 more times as 3 separate image generations, verbatim." → verify prompts, pick the best candidate
9. Post one-line status to user: "Panel N done — V[X] picked, [one-line reason], advancing"
10. Save chosen result to pages/panels/<panel_id>.png, log to job_ids.md
11. Advance to N+1
12. At end of comic: archive unused candidates
```

If the user interjects, pause after the current panel completes and follow their direction.
