---
name: continuity-check
description: Audit a comic project for continuity drift before lettering. Two-mode workflow — fast rules-based audit (asset presence, monotonic size/damage, missing refs) and vision-based audit (Claude reads each panel image, compares to shotlist intent + previous panels, catches costume drift, face identity drift, prop changes). Use before page-composer. Trigger phrases include "continuity check", "audit the issue", "check for drift", "wardrobe drift", "before I letter the pages".
---

# Continuity Check

Audit a batch of generated panels against the shotlist before lettering. Distinct from per-image QA (is this single panel any good?) — continuity-check asks **do the panels agree with each other and with the script?**

## Two-mode workflow

Run modes in this order:

1. **Rules-based** (`scripts/rules_audit.py`) — deterministic, instant, free. Catches the things a Python script can verify from `shotlist.json` and the file layout alone.
2. **Vision-based** — Claude (the agent) reads each panel image with the Read tool and compares it against the shotlist's intent + the previous panel. Catches pixel-level drift the rules audit can't see.

Rules-first because it's fast and surfaces structural problems (missing assets, regressions) that would otherwise make the vision pass waste tokens.

## When this skill is the right tool

- After generation, before `page-composer`
- "Audit the comic for continuity"
- "Did Supergirl's costume tearing stay consistent?"
- "Check pages 13–22 for costume drift"
- "Make sure Lex's face is the same across the issue"

If the user wants single-image quality QA (anatomy, generation artifacts, beauty of one image), that's per-panel QA — different concern, runs at generation time. This skill assumes panels are already individually accepted.

## Mode 1 — Rules audit

```sh
python skills/continuity-check/scripts/rules_audit.py --project /path/to/project [--pages 1-7] [--json]
```

What it checks:

- **Asset presence** — every panel in `shotlist.json` has an accepted image at `pages/panels/panel-<id>/v*_accepted.png` (or `v1.png`, or the flat fallback). HARD if missing.
- **Reference folders** — cast/locations/props declared in shotlist have their `ref_folder` on disk. HARD for cast, SOFT for locations, INFO for props.
- **Monotonic muscle_size_tier** — for the arc character (auto-inferred from cast wardrobe text mentioning "tear" / "size" / "growth" / "muscle", or set explicitly via top-level `"arc_character": "<id>"` in shotlist). Tier values must never regress unless the panel is marked `"continuity_break": true`. HARD on regression.
- **Costume damage rank non-regression** — same arc character. Coarse 3-level scale (intact / tight / damaged) derived from keyword matching on `costume_state` text. Carryover phrasing ("damage from page N carries forward", "same as page N") is recognized and skipped. SOFT on regression — the shotlist text is intent, not ground truth, so this is a hint to look more carefully, not a verdict.
- **Stage-change lineup ref** — pages flagged `"stage_change": true` should have a lineup reference image at `references/style/*lineup*`. SOFT if missing.
- **Field hygiene** — `costume_state` present per panel (SOFT). Characters in `panel.characters[]` declared in `cast[]` (SOFT).
- **Camera variety** — parses each panel's `camera` field against the categories in `comic-production/references/cinematic-framing.md`. HARD if any single (distance, angle) combo appears in >3 panels (the April-claudemade and Chun-Li failure mode — 7+ panels at the same shot signature). SOFT for distance-variety or angle-variety floors (≥5 / ≥4 per 10-panel sequence; intimate scenes legitimately violate this). SOFT for "no ECU" or "no wide-establish/splash" across a sequence ≥6 panels.
- **Body-region ECU frame-lockdown** — for any panel where `camera` parses as `ecu-region` and `costume_state` contains a bare-body-part claim ("bare", "exposed", "uncovered") and the named character's `cast[].wardrobe` mentions a torso garment (apron/dress/robe/shirt/cloak/armor/etc.), HARD if none of the panel's `notes`/`action`/`costume_state` includes a frame-lockdown clause naming what's OUT of frame. This is the L25 gate (lessons-learned.md L25) — flash variants widen `ecu-region` to a torso shot and omit the wardrobe; the lockdown clause prevents the widening drift. Set `continuity_break: true` to override.
- **Transformation beats** — only fires when shotlist declares `transformation_scenes[]`. For each scene, HARD if no setup beat (`consider`/`decide`/`trigger`/`first_sensation`), HARD if fewer than 3 distinct body-region beats (`chest`/`hips`/`rear`/`arms`/`abs`/`legs`/`back`/`shoulders`/`suit_fail`/`whole_body`) or any explicitly listed `required_body_regions` are missing, HARD if no reveal beat (`reveal`/`aftermath`). SOFT for unknown `transformation_beat` values (typo guard). This is the gate whose absence produced the April-claudemade failure (9 alley pose shots, zero body-region beats); the check now blocks that shape at script-breakdown time.

Exit codes: `0` clean, `1` hard errors present, `2` script error.

The script writes nothing by default — use `--out path/to/report.md` to save, or `--json` for machine-readable output piped into another tool.

## Mode 2 — Vision audit (agent-driven)

The rules audit can't see pixels. For costume drift between visually-similar tear states, face identity drift, prop disappearance, or wrong lighting — Claude has to look.

This is a workflow, not a script. Follow it in order when asked to run the vision audit:

### 2.1 Establish baselines

For each cast member, read the canonical face card and body baseline:

```
references/characters/<id>/face-card.png  (or whatever the _provenance.md picked)
references/characters/<id>/body-baseline.png
```

Take a short mental snapshot: hair, face proportions, eye color, costume colors, distinguishing features. This is the **identity** the panels must hold.

### 2.2 Walk panels in page order

For each accepted panel image at `pages/panels/panel-<id>/v*_accepted.png` (or `v1.png`):

Read the image. Compare against three things:

1. **The shotlist intent** for this panel — does the image show what `action`, `camera`, `costume_state`, and `muscle_size_tier` describe? For `ecu-region` panels specifically: did the rendered framing match the requested camera distance (per the `cinematic-framing.md` distance categories), and if the framing widened from ECU to a body-region torso shot, are the wardrobe items declared in `cast[].wardrobe` (apron, dress, etc.) visible in the wider crop? This is the L25 vision check (lessons-learned.md L25) — HARD on framing widened + wardrobe absent from the now-visible torso. The bryn-anvil-of-ages p04-04 worked example: requested bicep+forearm ECU, rendered as chin-to-hip side-profile, apron and shift dress missing across the visible torso. The rules audit cannot see this — it requires the vision pass.
2. **The previous panel** for the same character(s) — does the costume damage logically continue (or progress as the costume_state allows)? Has the face changed beats? Has hair length jumped?
3. **The character baseline** — does the face still read as the same person?

Tag observations at reader-noticeable level. Don't try to pixel-measure.

### 2.3 Diff and report

Produce a row per disagreement:

```
| panel | category | expected | observed | severity |
|-------|----------|----------|----------|----------|
| 19    | costume  | major tears carry from p18 | shoulder tear missing | hard |
| 25    | face     | match face-card v3         | jaw looks softer       | soft |
| 22    | prop     | red-sun-emitter sparking   | emitter clean/pristine | hard |
| 14    | lighting | red wash dominant          | gray ambient           | hard |
```

Severity rubric:

- **hard** — readers notice on first read; must fix (color flip, prop disappearance mid-scene, time-of-day jumps, identity drift, costume regression visible in image)
- **soft** — readers might notice on careful re-read; fix if cheap
- **info** — observation worth logging but not actionable

### 2.4 Group by scene + name the root cause

Continuity errors cluster. If three errors fall in pages 13–17 with the same theme (lighting too pink, not red enough), that's one upstream cause — likely a missed env-ref instruction or wrong DAZ recolor adjective. Name the cluster's likely root cause in the report. Saves the user from chasing symptoms.

### 2.5 Write the report

Save `continuity-vision-report.md` at project root next to `shotlist.json`:

```markdown
# Continuity vision audit — <project>

Audited <date>. <N> panels across <M> pages. <X> hard, <Y> soft, <Z> info.

## Summary
- 3 hard errors clustered in scene 2 (pages 13-15) — root cause: red-wash lighting prompt too weak
- 1 hard prop error on page 22 — emitter looks pristine in a "ruined emitter" beat
- 1 soft face drift on page 25 ECU — jaw softer than face card

## Errors
[table grouped by page range / scene]

## Root causes & suggested fixes
- Pages 13–15: regenerate with stronger red-wash directive ("red light floods every surface; no gray fallback")
- Page 22: prop_state for emitter says "sparking ruins" but generation read it as default — re-prompt with explicit "sparking ruined emitter, broken glass tubes, smoking debris"
- Page 25: re-anchor face card more aggressively; identity drift on ECU is the textbook scenario for FC-only attachment

## Suggested actions (don't execute — surface to user)
- Regenerate p13, p14, p15
- Regenerate p22
- Re-chain p25 with FC-only attachment
```

### 2.6 Hand back

In your final message to the user, summarize the report inline (top 5 issues + counts) and write the full report to `continuity-vision-report.md` at project root.

What happens next depends on whether autopilot is active.

**Without `production-config.json`** (legacy / `auto` mode): ask the user which to fix. Don't auto-regenerate — that burns budget and may introduce new drift.

**With `production-config.json`** (autopilot mode): read `policies.regeneration` and act accordingly:

- `never` → log the report, advance to stage 5 (composition). The user reviews the report manually after the run finishes.
- `batch-end` (default) → log the report. After stage 5 completes, halt cleanly with the report path in `.autopilot-halt-reason` so the user can decide what to regenerate. This is the safest autopilot default: the comic is fully composed and viewable, the user just has to decide if any flagged panels need a re-run.
- `auto-on-hard` → write a list of HARD-severity panels to `regen-queue.md` at project root, then auto-invoke `comic-production` to regenerate them, then re-run the vision audit. This can loop — cap at 2 regen passes to prevent runaway. Risky because regenerations can introduce new drift; only use this for projects where consistency is critical and budget isn't a concern.
- `halt-on-hard` → halt cleanly on the first HARD finding without composing pages. Preserves the pre-autopilot behavior.

In all autopilot cases, the final report is at `continuity-vision-report.md` regardless of which policy fired — the user's audit trail is preserved.

## Hard rules

- **Run rules audit first.** If hard errors exist (missing assets), fix those before spending tokens on the vision pass.
- **Don't auto-regenerate.** Surface the report and let the user choose what to fix.
- **Don't conflate continuity with quality.** A panel can be technically beautiful but continuity-wrong; a panel can be ugly but continuity-correct. Different skills.
- **Identity drift on ECU panels is a top-priority signal.** ECU-face panels are where Soul drift shows. If the face changes, the chain attachment strategy is wrong — fix the workflow, not just this one panel.
- **Establishing-panel discipline.** If a panel is the visual baseline for a scene (first appearance of a location, first costume tear), it must match the shotlist's text exactly — every later panel inherits its drift.
- **Trace error clusters to root cause.** Three errors in one scene usually means one upstream issue (missed prompt prefix, swapped face card, wrong env-ref attached). Naming the root cause saves you from chasing symptoms.

## Vision-audit shortcuts

When the user wants a partial pass:

- "Just check costume drift" — vision audit, filter to category=costume
- "Just verify Lex's face" — vision audit on every page Lex appears, compare each to his face card
- "Pages 5–8 only" — limit the page walk
- "Compare cover to interior" — read p01 against the establishing panel for that scene
- "Did the lighting hold across Act II?" — vision audit limited to category=lighting on pages 8–22

## Hand-off

After audit:

1. User decides what to fix (regenerate, accept, update shotlist)
2. Run those fixes
3. Re-run continuity-check (rules + vision on changed panels)
4. Then `page-composer` for lettering and PDF
