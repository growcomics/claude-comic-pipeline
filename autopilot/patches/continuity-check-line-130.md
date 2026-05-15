# Patch: `skills/continuity-check/SKILL.md` — Hand-back paragraph (line ~130)

Tiny rewrite. The "ask which to fix" interrupt becomes config-driven.

## Find this paragraph (under section 2.6 "Hand back")

```markdown
### 2.6 Hand back

In your final message to the user, summarize the report inline (top 5 issues + counts) and ask which to fix. Don't auto-regenerate — that burns budget and may introduce new drift.
```

## Replace with

```markdown
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
```

## Why

Before: a hard "ask which to fix" interrupt at the end of stage 4. Even in `narrate-don't-ask` mode, this one is explicit ("ask which to fix").

After: four policy options covering the common stances. Default `batch-end` is the safest — the run completes to PDF and only halts at the end to let the user decide, which is the right behavior for an unattended overnight run.

## Lines changed

~10 lines edited inside section 2.6. The vision audit workflow itself (sections 2.1–2.5) is unchanged.
