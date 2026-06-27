# Stage-aware references (character progression)

**Problem (owner feedback, muller pages).** A transformation comic's character changes
over the arc, but a locked reference is ONE look. Andrea's turnaround sheet shows her
*post*-transformation (muscular), so early panels rendered her "way too muscular — she's
not supposed to be muscular yet." References were a single static look per character.

**Fix.** A character's refs and a comic's pages can carry a **stage** so each panel pulls
the stage-appropriate version of a character.

## Data model

- **Per reference** — `$c['refs'][i]['stage']`: one of `STAGE_OPTS` (`pre` · `mid` · `post`
  · `tier-1`…`tier-5`) or `''` = **stage-agnostic** (used at every stage, e.g. a face that
  doesn't change, a prop, a scene). Scenes/props ignore stage entirely.
- **Per page** — `$c['plan'][p]['stage']`: the page's progression stage. A panel may also
  carry `$c['plan'][p]['panels'][q]['stage']` to override; the **effective** stage is
  `panel.stage ?: page.stage ?: ''`.
- Both axes are **different from** the project pipeline stage `$c['stage']` (`STAGES` =
  ideator/writer/…). Don't conflate them.

## Resolution (the core)

`inc/boot.php` → `ck_stage_eligible(array $refs, string $stage): array`
- Panel stage `''` → no filtering (unchanged behavior; zero change for non-transformation
  projects).
- Panel stage set → keep refs whose stage is `''` (agnostic) **or** equals the panel stage;
  drop refs tagged with a *different* stage. So a `pre` panel keeps the shared face + the
  `pre` body and **excludes the `post` (muscular) body**.
- If filtering would leave **zero** refs, fall back to all of them (never strand a panel) —
  the production guide flags this as "no `<stage>` ref for X" via `stage_gaps()`.

`shots.php` → `match_chars($names, $charRefs, $stage)` runs `ck_stage_eligible` before the
face→view→body priority sort and the 4-ref cap. The same helper is meant to back the future
generation worker so it resolves identically.

## UI

- **References workspace (`refs.php`)** — every character ref card has a `stage` select
  (`stage: any` + the presets); the upload form and each group header can set a stage for a
  whole batch/group; cards are **sub-grouped by stage** within each character, with a stage
  pill on each. Stage UI is hidden for scenes/props.
- **Production guide (`shots.php`)** — each page header has a **progression stage** select
  (auto-submits → `do=pagestage`). Each panel shows the stage in effect, attaches the
  stage-right refs (stage pill on each), and warns when only a wrong-stage fallback exists.
- **AI breakdown** — `ck_ai_breakdown` tags each page's `stage` from the script, but ONLY
  when it's clearly a transformation arc (else `''`); fully overridable. It does **not**
  auto-invent transformation beats (per the "don't invent state changes" rule).

## Verified

On-server assertion run (13/13): `pre` panel includes shared face + `pre` body and excludes
the `post` body; `post` excludes `pre`; untagged = no filter; fallback never strands;
`ck_stage_key` normalizes (`Pre`→`pre`, `tier 1`→`tier-1`) and rejects unknown tokens.

_Backward compatible: refs/pages without a `stage` key resolve to `''` (agnostic / no filter)._
