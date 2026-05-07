---
name: continuity-check
description: Cross-panel continuity audit for a comic — verify character wardrobe, props, location, and time-of-day stay consistent across panels against the shotlist; flag drift, mismatches, and broken running gags before pages are assembled. Use when the user wants to QA continuity across pages, check wardrobe drift, audit a chapter for continuity errors, verify the cast's appearance is consistent across a batch, or review generated panels before lettering. Trigger phrases include "continuity check", "check continuity", "wardrobe drift", "consistency across panels", "audit the chapter", "before I letter the pages", "did the props change", "scene continuity".
---

# Continuity Check

Audit a batch of generated panels against the shotlist. This is **distinct from per-image QA** (is this panel any good on its own — anatomy, artifacts, composition?). Continuity-check asks: **do these panels agree with each other and with the script?**

## When this skill is the right tool

- After generation, before `page-composer`
- "Check continuity across pages 1–8"
- "Does Lara's jacket stay the same?"
- "Audit chapter 2 before I letter it"
- "Did anything drift between scene 3 and scene 4?"

If the user wants single-image quality QA (composition, anatomy, generation artifacts), that's a different concern — the per-panel QA pass handles it. Run that first; this skill assumes panels are already individually approved.

## Inputs

- `shotlist.json` — the ground truth
- `pages/panels/<panel_id>.png` — generated and individually-approved panels, one per `panel_id`
- (optional) `style.md` — for expected color/line characteristics

## Categories of continuity

| Category | What can drift | How to check |
|---|---|---|
| **Character** | Face, body type, hair, age | Soul should ground identity, but Souls drift on extreme angles or unusual prompts |
| **Wardrobe** | Outfit pieces, colors, accessories | Compare panel to wardrobe baseline (the character's first appearance, or scene's establishing panel) |
| **Prop** | Recurring items (sword shape, hat color, scar location, side-of-body) | Track per-panel prop list against shotlist `props[]` |
| **Location** | Setting features (altar shape, window count, signage, doorways) | Match against the scene's establishing panel |
| **Time of day** | Lighting direction, color temperature, sky condition | Should match shotlist's `time_of_day` per panel |
| **Action** | Physical possibility (character at A in panel N, suddenly at B in N+1 with no transition) | Read action sequence end-to-end |

## Workflow

### 1. Build expected state

For each panel in `shotlist.json`, derive expected features:

```
p01-01: chars=[lara], wardrobe="leather jacket, brown trousers", location=forest-clearing, time=dawn (mist)
p01-02: chars=[lara], wardrobe=match(p01-01), location=forest-clearing, time=dawn (mist)
p01-03: chars=[lara, ranger], wardrobe(lara)=match(p01-01), wardrobe(ranger)=baseline, location=forest-clearing, time=dawn
...
```

The `continuity_refs` field in each panel tells you which earlier panel this one inherits from. If it's empty, the panel itself is the establishing reference for its scene.

### 2. Read each panel image

For every `pages/panels/<panel_id>.png`, use `Read` to inspect. Tag observed features at the level a reader would notice — don't try to OCR or pixel-measure:

- Wardrobe items present, dominant colors
- Props visible, their position and orientation
- Lighting direction, color temp, sky/window conditions
- Setting features that should be invariant within a scene (altar shape, doorway, signage)

### 3. Diff expected vs observed

Produce a row per disagreement:

```
| panel  | category | expected           | observed         | severity |
|--------|----------|--------------------|------------------|----------|
| p01-02 | wardrobe | leather jacket     | denim jacket     | hard     |
| p01-04 | time     | dawn (mist)        | midday (clear)   | hard     |
| p02-01 | prop     | sword on left hip  | sword on right   | soft     |
| p03-05 | location | altar carved runes | altar plain      | hard     |
```

Severity:

- **hard** — readers will notice on first read; must fix (wardrobe color flip, prop disappearance mid-scene, time-of-day jumps, location feature changes)
- **soft** — readers might notice on careful re-read; fix if cheap (mirror flips, minor accessory drift, prop side-of-body if not load-bearing)
- **info** — observation worth logging but not actionable (slight pose difference, gesture variation)

### 4. Group by scene

Continuity errors cluster. Group the table by location + time block. A wardrobe error in one panel of a 6-panel scene usually means regenerate that one panel. An error spanning every panel of a scene means the wardrobe baseline drifted at generation time — likely a missed prompt prefix or a swapped Soul.

### 5. Suggest action per error

Recommend, don't execute:

- **Regenerate panel** — when one panel disagrees with its scene
- **Update shotlist** — when the user wants the new look (canonize the change in `shotlist.json` so future panels match)
- **Accept** — when the cost of regenerating outweighs the drift (e.g. soft prop-side flip in a single distant panel)

### 6. Write the report

Save `continuity-report.md` next to `shotlist.json`:

```markdown
# Continuity Report — <project>

Audited <date>. <N> panels across <M> pages. <X> hard, <Y> soft, <Z> info.

## Summary
- 3 hard errors, all in scene 2 (page 4–5)
- Likely cause: scene-2 batch missed style.md prefix at generation time

## Errors
[the table from step 3, grouped by scene]

## Suggested actions
- Regenerate p04-02, p04-03, p05-01 with full prefix
- Update shotlist for p02-01 (sword side) — minor, accept

## Coverage
- Pages audited: 1–8 of 12
- Panels with no continuity_refs (no expected state): 4 — these panels can't be audited for continuity, only for shotlist match
```

### 7. Hand back to the user

In your final message, summarize the report inline (top 5 issues + counts) and ask which to fix. Don't auto-regenerate — that burns budget and the regen may have its own problems.

## Hard rules

- **Don't auto-regenerate.** Surface the report and let the user choose.
- **Don't conflate continuity with quality.** A panel can be technically beautiful and still continuity-wrong; a panel can be ugly but continuity-correct. Different skills.
- **Don't trust Soul IDs as a continuity guarantee.** Souls drift on extreme angles, occlusions, or unusual prompts. Visually verify.
- **Trace error clusters to root cause.** Three errors in one scene usually means one upstream issue (missed prompt prefix, swapped Soul, batch run with wrong params), not three independent bugs. Naming the root cause in the report saves the user from chasing symptoms.
- **Establishing-panel discipline.** If a panel sets the wardrobe baseline for a scene, it must itself match the cast's `wardrobe` field — otherwise everything that inherits from it inherits the drift.

## Common asks

- "Just check Lara's wardrobe" — filter to category=wardrobe and characters=lara
- "Check pages 5–8 only" — page-range filter
- "Compare to the previous chapter" — load that chapter's last-panel state as the baseline for this chapter's first-panel state
- "Did the cover match the interior?" — check character wardrobe and key props between the cover panel and chapter establishing panels

## Hand-off

After fixes, re-run `continuity-check` on the regenerated panels to confirm the regen didn't introduce new drift. Then `page-composer` for assembly.
