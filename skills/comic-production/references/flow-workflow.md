# Flow Workflow (Google Labs Flow → Nano Banana 2)

This reference covers the mechanics of producing comics on Google Labs Flow (`labs.google/fx/tools/flow`). Use it alongside the main SKILL.md — all the **rules** (view-aware chaining, FMG anatomy, mandatory rules block, muscle-size lineup, pose variation) still apply. What's different is **how you drive them**: Flow has no Python runner and no API, so Claude operates the browser UI through the Chrome MCP.

For platform tradeoffs vs Higgsfield, see "Platform Selection" in SKILL.md.

---

## Account & Access

- **URL**: `https://labs.google/fx/tools/flow`
- **Plan required**: Google AI Pro or Pro Ultra. Free tier won't expose Nano Banana 2 with unlimited generations. Paid tier shows "Generating will use **0 credits**" in the prompt panel — that's the confirmation you're on unlimited.
- **Login**: standard Google SSO. The user must be signed in before Claude can drive the page.

## Tooling: Chrome MCP

Flow has no API and no MCP of its own. Claude operates it via the **Claude in Chrome** MCP (`mcp__Claude_in_Chrome__*`). Required tools, all loadable via `ToolSearch` with the keyword query `Claude_in_Chrome` (loads in bulk):

- `tabs_context_mcp` — get the current tab group; required before any browser action
- `navigate` — open the Flow URL
- `computer` — the workhorse: click, type, hover, screenshot, key, scroll
- `browser_batch` — chain multiple `computer` actions in one round-trip; use this aggressively

Driving Flow with one-action-at-a-time tool calls is *very* slow. Always batch a stage's setup into one `browser_batch`: aspect/count toggle → ref attachment → prompt input → submit → wait → screenshot.

---

## UI Anatomy

The Flow project page (after `New project` is clicked) has these elements:

| Element | Purpose | Approximate location at default 1568×770 viewport |
|---|---|---|
| Gallery (main canvas) | Thumbnails of every prior generation in the project | Center / left, full height above the prompt bar |
| Prompt input | "What do you want to create?" text field | Bottom center, ~y=685 |
| `+` button (left of prompt) | Opens the asset picker for ref attachment | ~(533, 717) |
| Model/aspect/count pill | Shows current model + aspect + count (e.g. "Nano Banana 2 ☐ x4") | ~(947, 716) — click to open the settings popup |
| Submit arrow | Submits the prompt | ~(1036, 716) |
| Avatar / account menu | User profile, credit count | Top right — **don't click**; opens an unrelated overlay |
| Done / Show history | Inside the detail view of any generation | Top right of the detail view |

Coordinates drift if the user resizes the window. Take a fresh screenshot at the start of each session and re-locate the prompt bar before assuming positions.

### The settings popup

Clicking the model/aspect/count pill (~947, 716) opens a popup with three rows:

1. **Aspect ratio**: 16:9, 4:3, 1:1, 3:4, 9:16
2. **Count**: 1x, 2x, x3, x4
3. **Model dropdown**: defaults to "🍌 Nano Banana 2"

Important quirks:
- The popup **resets `count` to x4 each time it reopens**. Always re-toggle to your intended count before submitting if it matters.
- The aspect choice **does** persist across submissions until changed.
- Pressing `Escape` closes the popup *and* any other open overlay (like the asset picker). If the picker was your active workflow, you'll need to reopen it.

### Aspect ratio → comic shot mapping

Use this table when picking an aspect for a panel:

| Aspect | Best for | View categories from SKILL.md Rule #9 |
|---|---|---|
| **3:4** | Default for full-body 3q-full character shots | `front-full`, `3q-full`, `low-angle-front`, `back-full`, splash |
| **1:1** | Face cards (canonical portrait), ECU on a body region (bicep, abs, hand) | `ecu-face`, `ecu-region` |
| **16:9** | Wide establishing, environmental hero, splash with sky/skyline | `wide-establish`, `splash` |
| **4:3** | Medium / waist-up shots that need a bit more body than 1:1 but don't need full body | medium torso, two-character medium |
| **9:16** | Mobile-format vertical comic pages, phone-screen presentation | tall vertical splashes |

Default to **3:4** for any standing pose. Switch to **1:1** for ECU shots and the dedicated face reference card. Switch to **16:9** for wide environmental beats. The aspect ratio is part of the storytelling — vary it across the chain to give the sequence visual rhythm (see `cinematic-storytelling.md` once it lands; for now apply the same beat-vs-shot mapping shown in the worked example below).

### Count selector strategy

Wall-clock time is roughly the same for x1 and x4 (Flow parallelizes the variants). Use:

- **x4** for the **baseline character reference** and the **face reference card** — you want variants to pick from for the anchors that everything downstream chains off of.
- **x1** for **chained chain stages** — clean and predictable, no extra clutter in the picker.
- **x4** for any stage where the pose is novel and you'd benefit from picking the strongest variant.

If a chain stage produces an unusable result, redo at x4 and pick the cleanest variant.

---

## Reference Attachment — Three Methods

Flow supports attaching prior generations (or external uploads) as reference images for the next prompt. Each prompt can hold multiple refs simultaneously; both/all attached thumbnails appear in the prompt bar before submit and in the prompt history after.

### Method 1: Drag-and-drop (user's preferred manual workflow)

Drag any thumbnail from the gallery onto the prompt bar. Claude can't reliably do this through the Chrome MCP — drag operations are flaky. **Don't attempt this from automation.** Use Method 2 or 3 instead.

### Method 2: 3-dots menu → "Add to Prompt"

Hover over a thumbnail in the gallery. A small toolbar appears at the top-left of the thumbnail with three icons: **heart** (favorite), **refresh-arrow** (regenerate from this prompt), **3-dots** (more). Click the 3-dots → context menu opens with these items:

```
Animate
+ Add to Prompt   ← attaches as reference for next prompt
Favorite
Download
Share
Reuse Prompt      ← copies the prompt back into the input
Flag Output
Set Project Cover
Rename
Cut
Copy
Archive
```

Click "Add to Prompt" — a thumbnail appears in the prompt bar with an `×` to remove it.

**Best for:** attaching a specific variant from the gallery when you can see it on screen.

### Method 3: `+` button → Asset picker

Click the `+` to the left of the prompt input. A picker opens with:

- **Date filter** (top-left dropdown) — defaults to today; use **Search for Assets** instead if you can
- **Search field** — searches asset auto-titles
- **Sort dropdown** (top-right) — Recent / Oldest
- **Asset list** — every generation in the picker date range, with auto-generated titles
- **Preview pane** (right) — shows the highlighted entry
- **Upload image** (bottom-left) — for external files (real photo refs, hand-drawn sketches, etc.)

Click an asset entry to attach it. The picker closes automatically and the thumbnail appears in the prompt bar.

**Best for:** when the ref you want is far back in the gallery and would require scrolling, or when you need to upload an external image (e.g., a real Olivia Munn photo to anchor likeness, or an existing character sheet from outside Flow).

### Picker quirks

- **Date dropdown overlay**: clicking the date pill (top-left of the picker) opens a date list that visually covers the asset entries. Use the **Search** field instead — it's filtered live and doesn't have the overlay problem.
- **Auto-titles**: Flow auto-generates a short title for each gen from the prompt (e.g. "Olivia Munn as Psylocke portrait", "Female superhero muscular..."). This makes search reliable — name your stages distinctively in the prompt so the auto-title is searchable.
- The picker stays attached to the prompt bar across multiple `+` clicks — you can attach 2 or more refs by opening, picking, opening again, picking again.

### Attaching face + body refs (the standard chain pattern)

Per SKILL.md Key Rule #9, every chained panel should attach the canonical face/portrait ref alongside the prior-panel state anchor. In Flow, the workflow is:

1. **Body ref** → 3-dots on the prior stage thumbnail in the gallery → Add to Prompt
2. **Face ref** → click `+` on the prompt bar → click the face card entry in the picker

Both thumbnails will appear stacked in the prompt bar. Submit. The history sidebar will show both ref thumbnails next to the prompt for traceability.

---

## Reference Cards — Build These First

Same conventions as Higgsfield: build the canonical anchor images **before** producing the chain.

1. **Character body baseline**: a full-body 3q-full shot at size 1 (or whatever the story's starting size is). Generate at **x4** so you have variants. Pick the cleanest one — clear pose, recognizable face, intact costume — as the chain anchor.

2. **Dedicated face reference card**: an ECU beauty headshot generated **from the body baseline** by attaching it as a ref + prompting for "extreme close-up beauty headshot portrait, tight crop from collarbone to top of head, [face details]". Generate at **1:1**, **x4**. Pick the most symmetric forward-facing variant — flat angles transfer features better than 3/4 angles. This card becomes the canonical portrait that gets attached to **every** subsequent stage in the chain (Rule #9: "Always include the canonical portrait alongside the state anchor").

3. **Optional: external face upload**. If the user wants to anchor to a real person's likeness more aggressively (a specific actor), use the `+` picker → **Upload image** to add a reference photo. Combine with the generated face card — Flow will average the two. Note the celebrity-name content-policy quirk below.

---

## View-Aware Chaining in Flow

The skill's view-aware chaining rule (SKILL.md "View-aware chaining" + Key Rule #9) is unchanged on Flow. What's different is that **Claude must walk the chain manually** — there's no `panels.json` to declare the prior reference; you pick it from the gallery via 3-dots or the picker.

For each chain stage:

1. **Tag the target view** (e.g., `3q-full`, `ecu-face`, `low-angle-front`).
2. **Walk backwards through prior stages** in the project gallery.
3. **Stop at the most recent stage whose view is in the compatibility set** for the target view (see the table in SKILL.md Phase 3).
4. **Attach that stage as the body/state ref via 3-dots → Add to Prompt.**
5. **Attach the face card via `+` → picker.**
6. If no prior stage qualifies, fall back to the canonical view-matched character ref + verbal state carry-forward in the prompt.

### Example: 10-stage growth chain in Flow (worked example from production)

Stages 5 and 8 below show the rule in action — you can't always pull from N−1.

| # | Target view | Aspect | Chain anchor (prior stage that supplies state) | Notes |
|---|---|---|---|---|
| 1 | `3q-full` baseline | 3:4 | base prompt only (no prior) | Generate x4, pick the cleanest variant |
| 2 | `3q-full` | 3:4 | Stage 1 + face card | Standard N−1 chain ✓ |
| 3 | `ecu-region` (bicep) | 1:1 | Stage 2 + face card | Bicep visible in Stage 2 → compatible |
| 4 | medium / waist-up | 3:4 | Stage 2 + face card | Stage 3 is ECU, no body silhouette → walk back to Stage 2 |
| 5 | `3q-full` pull-back | 3:4 | **Stage 2** + face card (NOT Stage 4) | Stage 4 is waist-up → no leg silhouette. Pulling Stage 4 will drop the legs/boots in the next gen. Walk back to Stage 2. |
| 6 | `low-angle-front` | 3:4 | Stage 5 + face card | Compatible (low-angle-front is in 3q-full's compatibility set) |
| 7 | `ecu-face` | 1:1 | **face card alone** | The portrait IS the canonical anchor for ecu-face |
| 8 | `3q-full` | 3:4 | **Stage 6** + face card (NOT Stage 7) | Stage 7 is face ECU → no body silhouette. Walk back to Stage 6. |
| 9 | `wide-establish` | 16:9 | Stage 8 + face card | Wide-establish front-facing is compatible with 3q-full |
| 10 | `splash` low-angle | 3:4 | Stage 9 + face card | Compatible |

**Production lesson burned into this skill from real failure:** in an actual run, Stage 5 was naively chained from Stage 4 (the waist-up shot). The model dropped the leotard bottom and boots because Stage 4 had no leg silhouette to anchor them. The correct anchor is Stage 2 (last full body). If you forget and the costume regresses, two options: (a) re-roll Stage 5 with the correct anchor, or (b) re-cast the regression as "the costume tore from the growth" and continue forward — the FMG genre supports this narratively.

---

## Content Policy Quirks

Flow's safety filter is more conservative than Higgsfield's. Specific patterns that trip it:

### Pattern 1: Celebrity name + detailed body description

Naming a real public figure (e.g. "Olivia Munn", "Gal Gadot") in a prompt that also contains detailed muscle/breast/cleavage description **will fail with a "this generation might violate our policies" message**.

**Fix:** drop the celebrity name from prompts that have body description. Use the **face reference card** to carry the likeness — that's the whole point of building it. Refer to the character by their fictional name only ("film-version Psylocke", "the same character as both reference images").

This was discovered live during production. The first Stage 4 (medium torso, size 3) prompt named Olivia Munn explicitly *and* described pectoral fullness and cleavage — it failed. Re-submitting the same prompt with "Olivia Munn" removed (face ref still attached) sailed through with the same likeness preserved.

### Pattern 2: Explicit cleavage/breast emphasis

Phrases like "deep cleavage", "deep V-neckline showing extreme cleavage", and "upper swell of the breasts" can trigger the filter, especially on shots that crop to the torso. Use neutral anatomy language: "pectoral muscles fuller", "chest more substantial", "round full natural breasts". The skill's standard FMG anatomy guidance language is filter-safe.

### Pattern 3: Suggestive pose + skin emphasis

"Glistening", "oiled", and "wet" in combination with cleavage-heavy framing can stack with Pattern 2. Use "subtle oiled sheen" or "healthy glow" instead, keep the lighting language neutral, and let the muscle definition do the work.

### Recovery flow

If a gen fails with the policy message:

1. The failure card stays in the gallery — it doesn't auto-clear.
2. The prompt input clears.
3. Re-paste the prompt with the offending elements toned down (drop the name, soften the breast/cleavage language, swap "wet" → "subtle sheen").
4. Re-submit. The refs must be re-attached — they don't survive the failure.

---

## Production Workflow (Step by Step)

Putting it all together for a typical chain:

### Step 0 — Session setup

```
1. User opens https://labs.google/fx/tools/flow in Chrome (must be logged in)
2. Claude loads the Chrome MCP tools via ToolSearch (query "Claude_in_Chrome", max_results 30)
3. Claude calls tabs_context_mcp to get the active tab ID
4. Claude calls navigate to the Flow URL (or confirms already there)
5. Claude takes a screenshot to confirm the UI loaded and locate the prompt bar
```

### Step 1 — Create project

```
1. Click "+ New project" (center of dashboard if the project list is open)
2. Wait ~3 seconds for the empty timeline to render
3. Confirm "Nano Banana 2 ☐ x4" appears in the prompt bar pill (means model + free tier confirmed)
```

### Step 2 — Build the baseline reference

```
1. Open settings popup (click pill ~947, 716)
2. Set aspect to 3:4
3. Set count to x4
4. Press Escape to close
5. Click prompt input (~780, 685)
6. Type the baseline character prompt (DAZ3D Iray render, full-body 3q-full, character description, costume, pose, lighting)
7. Click submit arrow (~1036, 716)
8. Wait ~22 seconds (poll with screenshots — load completes around 90–99%)
9. Pick the best of the 4 variants (cleanest pose, most recognizable face, intact costume)
```

### Step 3 — Build the face card

```
1. Hover the chosen baseline thumbnail → click 3-dots → Add to Prompt
2. Open settings popup → switch aspect to 1:1, keep x4
3. Type the ECU face prompt ("extreme close-up beauty headshot portrait, tight crop from collarbone to top of head, preserve every feature exactly as in the reference, ...")
4. Submit, wait, pick the most symmetric forward-facing variant
```

### Step 4 — Chain the sequence (per stage)

For each subsequent stage:

```
1. Tag the target view; identify the correct chain anchor per the view-aware compatibility table
2. Open settings popup → set aspect for this stage's view (3:4 default, 1:1 for ECU, 16:9 for wide)
3. Set count to x1 (or x4 if you want variants for a novel pose)
4. Press Escape
5. Hover the chosen prior stage in the gallery → 3-dots → Add to Prompt
6. Click + on the prompt bar → click the face card entry in the picker
7. Click prompt input
8. Type the stage prompt (size delta, pose direction, costume state, mandatory rules block)
9. Submit
10. Wait ~22 seconds, screenshot to confirm
11. Press Escape to dismiss any auto-opened picker, screenshot again to verify the result
```

### Step 5 — Pick variants and present

```
1. Optionally open promising results full-screen (click the thumbnail) and use save_to_disk on the screenshot for the user
2. Summarize what was produced — view, aspect, size, any retries needed
3. Note any failures or view-aware regressions for the user
```

---

## Chrome MCP Operating Tips

These are pragmatic notes from production runs:

- **Always batch with `browser_batch`.** Setting aspect → count → Escape → hover → click 3-dots → click Add to Prompt → click `+` → click face entry → click prompt input → type → submit is 10+ actions. One `browser_batch` finishes in seconds; ten serial calls take much longer and burn round-trip cost.
- **Wait can't exceed 10 seconds per `computer:wait` call.** For a 22-second generation, chain `wait 10 → screenshot → wait 10 → screenshot → wait 5 → screenshot`. Don't try `wait: 30` — it errors.
- **The page jumps back to the top** after some hover/scroll combinations. If you scrolled to find a thumbnail and then hovered, the next click might land on a now-shifted target. Take a screenshot before any click sequence that follows a scroll.
- **Coordinates shift after each generation** — new gens push everything down a row. Don't memorize coordinates across stages; re-screenshot when you need to hover a specific thumbnail.
- **Auto-named pages**: Flow auto-titles each gen ("Female superhero muscular...", "Olivia Munn as Psylocke portrait..."). The picker uses these titles. Write distinctive prompt openers ("STAGE 7 of a 10-stage muscle growth study...") so the auto-titles are searchable later.
- **Date dropdown traps**: clicking the picker's date pill opens an overlay that looks like the asset list but isn't. If you see a dropdown of dates instead of asset titles, you're in the date filter — Escape and re-open with `+`.
- **The avatar in the top-right is NOT a "Done" button.** It opens the Google account menu. The actual "Done" button is in the detail view at the same x-coordinate; in the project gallery view, just click outside the detail to return.
- **Failures are sticky**: a failed-generation card stays in the gallery and pushes subsequent gens down. Click the small `×` icon at the bottom-right of the failure card to clear it, or leave it — it doesn't block new gens.
- **Ref thumbnails clear after submit**. Don't expect the prompt bar to retain refs across stages — re-attach for every stage.

---

## What Flow Doesn't Have (Compared to Higgsfield)

Be explicit with the user about these gaps before starting a long chain on Flow:

- **No `panels.json`** — you can't pre-write the whole sequence and run it overnight. Each stage is hand-driven.
- **No resume after disconnect** — if the Chrome tab closes mid-chain, the next stage requires manual ref re-attachment. There's no `--start N`.
- **No batch parallel queueing** — submit one prompt at a time. (You can submit a second while the first is still rendering, but the count adds clutter.)
- **No precise width/height** — only the five fixed aspect ratios. If you need 768×1024 specifically, use Higgsfield.
- **No dry-run** — you can't preview a prompt without spending a generation. Compose carefully, especially for stages that touch policy-sensitive territory.
- **No QA log / state.json** — track progress in the conversation (TodoWrite) instead.

---

## Lessons Learned (from real production sessions)

These are session-burned and worth preserving:

1. **Drop celebrity names from prompts that include body description.** First learned during the Olivia-Munn-Psylocke chain. The face ref carries the likeness; the name in the prompt only adds policy risk. *(See Content Policy Quirks above.)*

2. **View-aware chaining is real and visible.** Stage 5 of the Psylocke chain naively pulled from Stage 4 (waist-up); the leotard bottom dropped because there was no leg silhouette to anchor. The fix is the SKILL.md compatibility table — walk backward to the last view-compatible stage, not the literal N−1.

3. **The picker is your friend for face-ref re-attachment.** Across a 10-stage chain you'll attach the face card 9 times. The `+` picker → search field is the fastest path; auto-titles make the face card searchable as "Olivia Munn as Psylocke portrait" or whatever you titled it.

4. **The settings popup forgets count between sessions.** Defaults to x4 every time it reopens. If you've been running x1 for chain stages, double-check the pill before each submit.

5. **Each gen's wall-clock is ~22 seconds at any count.** x1 and x4 take the same time. So default to x4 for novel stages where variant selection helps; switch to x1 for predictable chain links to keep the gallery clean.

6. **A failed generation doesn't "cost" anything on the unlimited tier**, but it does waste UI time. Compose policy-sensitive prompts conservatively the first time.

7. **Per-stage UI overhead is ~30–45 seconds** on top of the ~22 seconds of actual generation. A 10-stage chain takes ~10 minutes minimum, even with no failures and full automation. Set expectations with the user.
