# Patch: `skills/comic-production/references/shotlist-driven-flow.md` — Break Conditions

Replaces the "when to break the loop and ask the user" section with a config-driven version. Existing behavior preserved when no config exists; autopilot uses config values to decide whether to halt or continue.

> **Status (2026-06-10): applied.** The live section in `shotlist-driven-flow.md` is the source of truth and has evolved beyond this patch — it added the L12/L13 shotlist-warning halts, an anatomy policy, and was re-pointed at Flow's **Omni-agent chat UI**: one chat submit yields ONE image (the count setting doesn't fan out), so "all 4 variants" became "the full candidate set" — the first result plus an optional verbatim re-run fan-out (`flow-workflow.md` "Variant Strategy"). The replace-block below is kept aligned on those mechanics but is not re-expanded; the "Find this block" quote is the historical pre-patch text and stays as written.

## Find this block (lines ~234–239)

```markdown
## When to break the loop and ask the user

- **Content policy refusal**: Flow's safety filter triggered. Don't auto-retry with the same prompt. Ask before adjusting language. See `flow-workflow.md` "Content Policy Quirks" — the most common cause is celebrity names + body description; the second most common is heavy cleavage + "glistening/wet" stacked with size language.
- **3+ retries on one panel**: surface for user direction. Either the prompt fragment library has a bug, or the shotlist entry is wrong, or the chain anchor is incompatible with the target view in a way that needs a story-level decision.
- **All 4 variants drift to 2D illustration**: the prompt almost certainly has L7-violating content (some lettering instruction slipped through). Ask the user to confirm the prompt before continuing.
- **Variant has anatomy issue and so do 2+ of the others**: model is having an off run; brief pause + retry usually fixes; surface only if pattern continues.
```

## Replace with

```markdown
## When to break the loop

Behavior depends on whether `production-config.json` exists at project root.

**Without config** (legacy / `auto` mode): break and ask the user on the conditions below. This is the pre-2026-05-13 behavior.

**With config** (autopilot mode): each condition has a policy default; autopilot consults the config and either continues or halts cleanly. Halt = write reason to `<project>/.autopilot-halt-reason` and stop. The Stop hook respects the halt-reason file and allows the stop.

### Conditions

- **Content policy refusal** (Flow's safety filter triggered).
  - Config policy: not configurable — always halts. This is one of the 4 approved halt conditions.
  - Recovery: surface the refused prompt to the user with `flow-workflow.md` "Content Policy Quirks" guidance. Most common cause: celebrity names + body description (drop the celebrity name; face card carries likeness). Second most common: heavy cleavage + "glistening/wet" stacked with size language.

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
  - Config policy: same as "all candidates fail QA" above. If `on_all_bad=retry-with-cgi-anchor-boost`, the retry instead adds the L11 silhouette anchor and the "NOT realistic fitness, NOT athletic" negation, then retries.

### Default user-interaction mode: "narrate, don't ask"

When the conditions above are NOT triggered (the variant is clean, the chain is advancing), don't pause. Drive through the panels narrating progress.

- After each accepted panel: post a one-line status ("Panel 3 done — V2 picked, looks clean, advancing to Panel 4").
- Refresh `STATUS.md` after each accepted panel (per the build-comic.md status-surfacing table).
- Refresh `STATUS-generation-board.png` at end of stage.
- The user can interject at any time — they don't have to wait for the agent to ask. A `pause` or `stop` interjection halts the loop after the current panel completes. The Stop hook respects this — if a `.autopilot-halt-reason` file is present (which the agent should write on user interjection), the stop is allowed.
```

## Why

Before: 4 ad-hoc conditions where the per-panel loop pauses for human input. Each was useful in `auto` mode but breaks autopilot.

After: each condition has a config-keyed default. Autopilot reads the policy and either continues (with a retry-with-tweak) or halts cleanly. Legacy ask-the-user behavior is preserved when no config exists.

## Lines changed

~20 lines edited. Net change: section is longer (clearer policy semantics) but the underlying conditions are identical. No new failure modes introduced.
