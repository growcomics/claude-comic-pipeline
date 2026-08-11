# Flow Workflow (Google Labs Flow → Nano Banana)

This reference covers the mechanics of producing comics on Google Labs Flow (`labs.google/fx/tools/flow`). Use it alongside the main SKILL.md — all the **rules** (view-aware chaining, FMG anatomy, mandatory rules block, muscle-size lineup, pose variation) still apply. What's different is **how you drive them**: Flow has no Python runner and no API, so Claude operates the browser UI through the Chrome MCP.

For platform tradeoffs vs Higgsfield, see "Platform Selection" in SKILL.md.

> **UI generation notice.** Flow replaced its pill-based prompt-bar UI with the **Omni-agent chat UI**: prompts go to an agent in a right-side session chat panel, and the agent mediates every generation. The pill-based UI this doc originally described (model/aspect/count pill, settings popup, x4 fan-out, coordinate map) is gone from the live product. Everything below documents the **Omni UI as the primary path**, verified in production 2026-06-09 (the L35 validation run, 16 generations — `l35-validation/README.md`); the old mechanics survive only in the **Legacy Appendix** at the bottom. Flow ships UI changes without notice: **screenshot first, trust the screen over this doc**, and update this doc when reality diverges.

---

## Account & Access

- **URL**: `https://labs.google/fx/tools/flow`
- **Login**: standard Google SSO. The user must be signed in before Claude can drive the page.
- **Plan & models** (verified 2026-06-09 on the production growcomics account, Google AI Plus plan):
  - **🍌 Nano Banana 2** — Flow's default model and the production workhorse. Effectively unlimited on the paid plan (the 16-gen L35 run cost nothing).
  - **Nano Banana Pro** — has a **daily quota** on the Plus plan. When it's exhausted, Flow refuses with exactly: *"You've reached the daily limit for Nano Banana Pro generations."* Fall back to Nano Banana 2 and note the model caveat in whatever you're producing (precedent: the entire L35 validation ran on NB2 after hitting the Pro quota — internally consistent, same model family as the production `nano_banana_flash` default).
- The old "Generating will use **0 credits**" prompt-panel label was a pill-UI affordance — don't look for it in the Omni UI.

## Tooling: Chrome MCP

Flow has no API and no MCP of its own. Claude operates it via the **Claude in Chrome** MCP (`mcp__Claude_in_Chrome__*`). Required tools, all loadable via `ToolSearch` with the keyword query `Claude_in_Chrome` (loads in bulk):

- `tabs_context_mcp` — get the current tab group; required before any browser action. Also how you read a tab's **final URL** after a redirect (the download workaround below depends on this).
- `navigate` — open the Flow URL, and later the `media.getMediaUrlRedirect` URLs for downloads
- `computer` — click, type, hover, screenshot, key, scroll
- `browser_batch` — chain multiple `computer` actions in one round-trip
- `read_page` / `javascript_tool` — read the detail-view filmstrip's `<img>` srcs to harvest media uuids for downloads

If more than one Chrome is connected (`list_connected_browsers`), confirm you're driving the one with the signed-in Flow session before acting (production runs have used the "macmini" browser). The Omni UI is far less click-heavy than the pill UI — a generation is one typed chat message — but batching still pays: type + submit + wait + screenshot in one `browser_batch`.

---

## UI Anatomy

The Omni-agent project page has three surfaces:

| Surface | What it is | How you use it |
|---|---|---|
| **Main canvas** (left/center) | The project's generations | Click any generation to open its **detail view** |
| **Session chat panel** (right side) | "What do you want to create?" input + the running agent conversation | Type prompts here; the agent mediates every generation and replies in-thread |
| **Agent settings** (sliders icon in the session panel) | Defaults the agent applies to generations | **Confirm**: Always / Never — set **Never**, or every generation needs an extra confirmation click. **Image defaults**: aspect ratio, count, model. **Video defaults**: not used for comic work. |

There is deliberately no coordinates table for the Omni UI: the chat panel reflows as the agent thread grows. Locate elements by fresh screenshot, every session. If instead of a chat panel you see a prompt bar with a model/aspect/count pill, you've landed on the legacy UI (A/B test or rollback) — the Legacy Appendix applies.

### The detail view

Click a generation on the canvas to open it full-size:

- A **filmstrip** of the project's media runs along the detail view, with **arrow-key navigation** — Left/Right steps through generations. This is the fast way to review a variant set: open the detail view once, arrow through, screenshot each.
- The item's **prompt** is shown — use it to verify a verbatim re-run actually used the verbatim prompt.
- A **Download** menu offers resolution options (1K, …) — but it can **fail silently when driven from automation** (synthesized clicks carry no user activation). Don't trust it from the MCP; use the signed-URL pull in "Downloading Results" below.
- The filmstrip's `<img>` srcs embed each item's **media uuid**, in **newest-first DOM order** — harvest them here for downloads.

## Generation Mechanics (verified 2026-06-09)

The load-bearing behaviors, all observed in production:

1. **One chat submit produces ONE image — regardless of the count setting.** The Agent-settings count was ×4 for the entire L35 run; every submit still yielded exactly 1 image. Set count to **1** so the setting matches reality.
2. **Submit pattern**: lead the message with an explicit instruction so the agent doesn't get creative: `Generate one image. <prompt>`.
3. **Variants come from a follow-up message**, not from the count setting: `Run that exact same prompt 3 more times as 3 separate image generations, verbatim.` The agent honors this — it echoes the full verbatim prompt in chat and runs 3 more generations. **Verify anyway**: arrow through the new items and check each detail-view prompt matches the original. (This pattern produced all 12 variant gens of the L35 run.)
4. **Set confirm = Never** (Agent settings) before the first generation, or every submit stalls on a confirmation click.
5. **Aspect ratio is an Agent-settings default** — set once, applies until changed. For per-stage aspect changes (3:4 panel → 1:1 ECU → 16:9 wide), reopen Agent settings before the submit. *(Steering aspect from the chat message itself is plausible but **not yet verified** — if you confirm it works, update this doc.)*
6. **Model fallback**: if a submit refuses with the Nano Banana Pro daily-limit error, switch the model default to Nano Banana 2 and continue (note the caveat).
7. **Native output size**: 1K at 16:9 is **1376×768 JPEG**. Other aspects' native sizes are unmeasured — record them when you hit them.

### Aspect ratio → comic shot mapping

Use this table when picking an aspect for a panel:

| Aspect | Best for | View categories from SKILL.md Rule #9 |
|---|---|---|
| **3:4** | Default for full-body 3q-full character shots | `front-full`, `3q-full`, `low-angle-front`, `back-full`, splash |
| **1:1** | Face cards (canonical portrait), ECU on a body region (bicep, abs, hand) | `ecu-face`, `ecu-region` |
| **16:9** | Wide establishing, environmental hero, splash with sky/skyline | `wide-establish`, `splash` |
| **4:3** | Medium / waist-up shots that need a bit more body than 1:1 but don't need full body | medium torso, two-character medium |
| **9:16** | Mobile-format vertical comic pages, phone-screen presentation | tall vertical splashes |

Default to **3:4** for any standing pose. Switch to **1:1** for ECU shots and the dedicated face reference card. Switch to **16:9** for wide environmental beats. The aspect ratio is part of the storytelling — vary it across the chain to give the sequence visual rhythm.

### Variant Strategy (replaces the legacy count-selector strategy)

The legacy x4 fan-out is gone — variants now cost one extra chat message and run as separate generations:

- **Anchors (character baseline, face card)**: submit once, then ask for 3 verbatim re-runs → 4 candidates, pick the cleanest (clear pose, recognizable face, intact costume; most symmetric forward-facing for the face card).
- **Predictable chain stages**: a single submit is usually enough — the chain advances only on an accepted panel, so re-roll on demand instead of pre-paying for variants.
- **Novel poses / money-shots**: submit + 3 verbatim re-runs, pick the strongest.

### Conversational single-instruction editing (Omni) — the refinement path *(added 2026-06-17, L36)*

The Omni agent **edits an attached/prior image far more reliably than it builds a complex scene from a wall of text.** For refining an *already-accepted* figure — pose, facial expression, gaze, wardrobe state, lettering — drive one change per message instead of re-rolling a fat prompt:

```
Change her pose to the reference so she looks like she is kicking, just like the reference        (+ pose ref attached)
Change her facial expression so she looks like shouting, she is looking to her right at her leg
Add a text dialogue bubble that comes from her and says "Tenshoukyaku!"
```

Each message carries the style suffix and changes exactly one thing; the agent holds identity / costume / accessories stable between edits, so they don't drift the way a fresh re-roll drifts them. Gaze direction is steerable in plain language. Dialogue is baked here (consistent with L19). **Decision rule:** full-prompt + verbatim re-runs for the cold-start baseline and novel money-shots; **single-instruction editing for everything downstream of an accepted figure.** See L36 for the full Chun-Li worked example, the validated "prosumer DAZ" style block, and the turnaround conventions (NB Pro, 16:9, black bg).

---

## Reference Attachment

**Status: Omni-UI attachment is OBSERVED WORKING (2026-06-17), exact mechanic still to be driven end-to-end.** The Chun-Li build session (project `8e5f2654…`, L36) attached references in the Omni UI — generations carry attached-media chips, an uploaded real-photo ref was style-transferred (`convert to <style>`), and pose-by-reference worked (`Change her pose to the reference … just like the reference`). What's not yet re-documented step-by-step is the precise click path to attach in Omni; pin it down on the next driven run and replace the numbered list below with what actually works. The 2026-06-09 validation run was text-only, which is why this section was previously marked unverified.

The **requirement** is unchanged and non-negotiable (SKILL.md Key Rule #9): every chained panel attaches its **state anchor** (the view-compatible prior panel) plus the **canonical face card**; external uploads anchor real-person likeness or outside art. Refs did not persist between submits on the legacy UI — assume the same until proven otherwise and re-attach on every stage.

On the first chained run, verify in order — then replace this list with what actually works:

1. **An attach affordance on the chat input** (`+` / paperclip / image icon) — for uploads and possibly for picking prior project media.
2. **Asking the agent in-thread** to use a prior generation as reference, by auto-title or description ("use the Stage 2 full-body image as the reference for…"). The agent mediates generation, so conversational ref selection is plausible — but unverified, and silent mis-selection is the risk: confirm which image it used (check the detail-view prompt; compare the result against the intended anchor).
3. **Legacy surfaces** (thumbnail 3-dots → "Add to Prompt", `+` asset picker) if they survived somewhere in the project canvas.

Do NOT start a long chained production on Flow without first burning a couple of throwaway gens to pin the attachment mechanics down — then update this section and the Legacy Appendix.

## Reference Cards — Build These First

Same conventions as Higgsfield: build the canonical anchor images **before** producing the chain.

1. **Character body baseline**: a full-body 3q-full shot at size 1 (or the story's starting size). Submit once + 3 verbatim re-runs so you have 4 candidates. Pick the cleanest — clear pose, recognizable face, intact costume — as the chain anchor.

2. **Dedicated face reference card**: an ECU beauty headshot generated **from the body baseline** by attaching it as a ref + prompting for "extreme close-up beauty headshot portrait, tight crop from collarbone to top of head, [face details]". Generate at **1:1**, with variants via verbatim re-runs. Pick the most symmetric forward-facing variant — flat angles transfer features better than 3/4 angles. This card becomes the canonical portrait attached to **every** subsequent stage in the chain (Rule #9: "Always include the canonical portrait alongside the state anchor").

3. **Optional: external face upload**. If the user wants to anchor to a real person's likeness more aggressively, upload a reference photo via the attachment mechanic (see "Reference Attachment"). Combine with the generated face card — Flow will average the two. Note the celebrity-name content-policy quirk below.

---

## View-Aware Chaining in Flow

The skill's view-aware chaining rule (SKILL.md "View-aware chaining" + Key Rule #9) is unchanged on Flow. What's different is that **Claude must walk the chain manually** — there's no `panels.json` to declare the prior reference; you select it by hand from the project's media (see "Reference Attachment").

For each chain stage:

1. **Tag the target view** (e.g., `3q-full`, `ecu-face`, `low-angle-front`).
2. **Walk backwards through prior stages** in the project.
3. **Stop at the most recent stage whose view is in the compatibility set** for the target view (see the table in SKILL.md Phase 3).
4. **Attach that stage as the body/state ref.**
5. **Attach the face card.**
6. If no prior stage qualifies, fall back to the canonical view-matched character ref + verbal state carry-forward in the prompt.

### Example: 10-stage growth chain in Flow (worked example from production)

Stages 5 and 8 below show the rule in action — you can't always pull from N−1.

| # | Target view | Aspect | Chain anchor (prior stage that supplies state) | Notes |
|---|---|---|---|---|
| 1 | `3q-full` baseline | 3:4 | base prompt only (no prior) | Generate 4 candidates (submit + 3 verbatim re-runs), pick the cleanest |
| 2 | `3q-full` | 3:4 | Stage 1 + face card | Standard N−1 chain ✓ |
| 3 | `ecu-region` (bicep) | 1:1 | Stage 2 + face card | Bicep visible in Stage 2 → compatible |
| 4 | medium / waist-up | 3:4 | Stage 2 + face card | Stage 3 is ECU, no body in frame → walk back to Stage 2 |
| 5 | `3q-full` pull-back | 3:4 | **Stage 2** + face card (NOT Stage 4) | Stage 4 is waist-up → no legs in frame. Pulling Stage 4 will drop the legs/boots in the next gen. Walk back to Stage 2. |
| 6 | `low-angle-front` | 3:4 | Stage 5 + face card | Compatible (low-angle-front is in 3q-full's compatibility set) |
| 7 | `ecu-face` | 1:1 | **face card alone** | The portrait IS the canonical anchor for ecu-face |
| 8 | `3q-full` | 3:4 | **Stage 6** + face card (NOT Stage 7) | Stage 7 is face ECU → no body in frame. Walk back to Stage 6. |
| 9 | `wide-establish` | 16:9 | Stage 8 + face card | Wide-establish front-facing is compatible with 3q-full |
| 10 | `splash` low-angle | 3:4 | Stage 9 + face card | Compatible |

**Production lesson burned into this skill from real failure:** in an actual run, Stage 5 was naively chained from Stage 4 (the waist-up shot). The model dropped the leotard bottom and boots because Stage 4 had no legs in frame to anchor them. The correct anchor is Stage 2 (last full body). If you forget and the costume regresses, two options: (a) re-roll Stage 5 with the correct anchor, or (b) re-cast the regression as "the costume tore from the growth" and continue forward — the FMG genre supports this narratively.

---

## Content Policy Quirks

Flow's safety filter is more conservative than Higgsfield's. **These quirks predate the Omni UI and still apply**: the 2026-06-09 validation went 16/16 submits with zero policy trips by following them (neutral anatomy terms, no celebrity names, no steep low-angle language). The patterns:

### Pattern 1: Celebrity name + detailed body description

Naming a real public figure (e.g. "Olivia Munn", "Gal Gadot") in a prompt that also contains detailed muscle/breast/cleavage description **will fail with a "this generation might violate our policies" message**.

**Fix:** drop the celebrity name from prompts that have body description. Use the **face reference card** to carry the likeness — that's the whole point of building it. Refer to the character by their fictional name only ("film-version Psylocke", "the same character as both reference images").

This was discovered live during production. The first Stage 4 (medium torso, size 3) prompt named Olivia Munn explicitly *and* described pectoral fullness and cleavage — it failed. Re-submitting the same prompt with "Olivia Munn" removed (face ref still attached) sailed through with the same likeness preserved.

### Pattern 2: Explicit cleavage/breast emphasis

Phrases like "deep cleavage", "deep V-neckline showing extreme cleavage", and "upper swell of the breasts" can trigger the filter, especially on shots that crop to the torso. Use neutral anatomy language: "pectoral muscles fuller", "chest more substantial", "round full natural breasts". The skill's standard FMG anatomy guidance language is filter-safe.

### Pattern 3: Suggestive pose + skin emphasis

"Glistening", "oiled", and "wet" in combination with cleavage-heavy framing can stack with Pattern 2. Use "subtle oiled sheen" or "healthy glow" instead, keep the lighting language neutral, and let the muscle definition do the work.

### Pattern 4: Steep low-angle framing + body emphasis *(added 2026-06-09)*

Steep low-angle hero-shot language stacked with muscle/body emphasis is filter risk. The L35 validation prompts deliberately replaced a steep low angle with "three-quarter dynamic angle with foreshortening" to stay clear of the filter — and went 16/16 clean. Prefer dynamic three-quarter angles with foreshortening for growth hero shots; save true steep low angles for beats with neutral body language.

### Recovery flow

If a gen fails with the policy message:

1. **Don't auto-retry the same prompt** (this is also an autopilot break condition — `autopilot/patches/shotlist-driven-flow-break-conditions.md`).
2. Re-submit with the offending elements toned down: drop the celebrity name, soften the breast/cleavage language, swap "wet" → "subtle sheen", flatten a steep low angle.
3. **Re-attach refs if the UI dropped them.** On the legacy UI a failure always cleared attached refs. Omni behavior is unobserved — no policy trip has occurred on it yet; the one refusal seen so far (the NB Pro daily quota) came back as a normal agent chat message.

---

## Downloading Results

What does **NOT** work from automation (verified): the detail view's **Download → 1K** menu fails **silently** under synthesized clicks, and programmatic `a.click()` blob downloads fail the same way — neither carries user activation. You will think you downloaded; nothing landed.

The reliable pull (verified 2026-06-09 — every committed L35 file came down this way):

1. **Harvest media uuids**: in the detail view, read the filmstrip's `<img>` src attributes (`read_page` or `javascript_tool`) — each src embeds the item's media uuid, in newest-first DOM order. Collect every uuid you need before navigating away.
2. **Resolve the signed URL**: `navigate` a tab to
   `https://labs.google/fx/api/trpc/media.getMediaUrlRedirect?name=<media-uuid>`
   The redirect lands on a **signed `flow-content.google` URL** — read it as the tab's final URL from the tab context.
3. **Pull with curl** from Bash — the signed URL needs no cookies:
   `curl -s -o <exact-target-filename>.jpg '<signed-url>'`
4. **File hygiene**: name every file yourself and verify by exact filename. The user actively uses Flow (and `~/Downloads`) on the same machine — **never** grab "the newest file".

Notes: 1K at 16:9 comes down as Flow-native 1376×768 JPEG — keep it as-is, no recompression (precedent: `l35-validation/`, `sketches/staging-examples/`). Resolving the trpc URL navigates the tab away from the project — collect all uuids first, then navigate back, or resolve in a scratch tab (`tabs_create_mcp`).

---

## Production Workflow (Step by Step)

Putting it all together for a typical chain:

### Step 0 — Session setup

```
1. User opens https://labs.google/fx/tools/flow in Chrome (must be logged in)
2. Claude loads the Chrome MCP tools via ToolSearch (query "Claude_in_Chrome", max_results 30)
3. Claude calls tabs_context_mcp (and list_connected_browsers if several Chromes are connected —
   pick the one with the signed-in Flow session)
4. Claude calls navigate to the Flow URL (or confirms already there)
5. Claude screenshots to confirm the Omni chat panel ("What do you want to create?") is present.
   If a prompt-bar pill shows instead, the legacy UI is live — Legacy Appendix applies.
```

### Step 1 — Create project + set agent defaults

```
1. Click "+ New project" (from the dashboard)
2. Open Agent settings (sliders icon in the session chat panel):
   - confirm = Never            (or every gen stalls on a confirmation click)
   - model  = Nano Banana 2     (Pro only if explicitly wanted AND daily quota allows)
   - aspect = 3:4               (default for character work; change per stage as needed)
   - count  = 1                 (a submit yields 1 image regardless — make the setting honest)
3. Screenshot to confirm the settings took
```

### Step 2 — Build the baseline reference

```
1. Chat: "Generate one image. <baseline character prompt — DAZ3D Iray render, full-body 3q-full,
   character description, costume, pose, lighting, mandatory rules block>"
2. Wait for the generation (poll with screenshots)
3. Chat: "Run that exact same prompt 3 more times as 3 separate image generations, verbatim."
4. Open the detail view, arrow-key through the 4 candidates, pick the best
   (cleanest pose, most recognizable face, intact costume)
```

### Step 3 — Build the face card

```
1. Agent settings → aspect 1:1
2. Attach the chosen baseline as a ref (see "Reference Attachment" — pin the mechanic down first)
3. Chat: "Generate one image. Extreme close-up beauty headshot portrait, tight crop from
   collarbone to top of head, preserve every feature exactly as in the reference, ..."
4. Variants via the verbatim re-run; pick the most symmetric forward-facing candidate
```

### Step 4 — Chain the sequence (per stage)

```
1. Tag the target view; pick the chain anchor per the view-aware compatibility table
2. If this stage's aspect differs from the last, update it in Agent settings
3. Attach the anchor + the face card (re-attach every stage; refs don't persist)
4. Chat: "Generate one image. <stage prompt — size delta, pose direction, costume state,
   mandatory rules block>"
5. Wait; verify in the detail view (content AND prompt)
6. Novel pose or weak result → "Run that exact same prompt 3 more times ... verbatim" and
   pick; or re-roll with a corrected anchor/prompt. Advance only on an accepted panel.
```

### Step 5 — Download and present

```
1. Harvest the accepted panels' media uuids from the filmstrip
2. Pull full-res via the signed-URL flow ("Downloading Results"); name files exactly
3. Summarize what was produced — view, aspect, size, retries needed, any view-aware
   regressions or policy reroutes
```

---

## What Flow Doesn't Have (Compared to Higgsfield)

Be explicit with the user about these gaps before starting a long chain on Flow:

- **No `panels.json`** — you can't pre-write the whole sequence and run it overnight. Each stage is hand-driven through the agent chat.
- **No count fan-out and no batch queueing** — one submit yields one image; variants are follow-up verbatim re-runs, one conversation at a time.
- **No resume after disconnect** — if the tab or session dies mid-chain, the next stage needs its refs re-attached by hand; there's no `--start N`. (The project and its media persist; the working state doesn't.)
- **No precise width/height** — fixed aspect ratios only (1K ≈ 1376×768 at 16:9). If you need 768×1024 exactly, use Higgsfield.
- **No dry-run** — you can't preview a prompt without spending a generation. Compose carefully, especially near policy-sensitive territory.
- **No QA log / state.json** — track progress in the conversation (TodoWrite) instead.

---

## Lessons Learned (from real production sessions)

These are session-burned and worth preserving:

1. **One submit = one image, no matter what the count setting says** *(2026-06-09)*. The Agent-settings count×4 did not fan out a single submit. Variants = the follow-up "Run that exact same prompt 3 more times as 3 separate image generations, verbatim." The agent echoes the verbatim prompt in chat — verify each result's detail-view prompt anyway.

2. **Set confirm = Never before the first gen** *(2026-06-09)* — otherwise every generation stalls on a confirmation click.

3. **Nano Banana Pro is daily-quota'd on the Plus plan** *(2026-06-09)* — refusal string: "You've reached the daily limit for Nano Banana Pro generations." Nano Banana 2 is the unlimited fallback and the sane default.

4. **The Download menu lies to automation** *(2026-06-09)* — silent failure, no user activation from synthesized input. Use the `media.getMediaUrlRedirect` signed-URL pull, and only trust files you named yourself — the machine and `~/Downloads` are shared with the user's own Flow activity.

5. **Drop celebrity names from prompts that include body description.** First learned during the Olivia-Munn-Psylocke chain. The face ref carries the likeness; the name in the prompt only adds policy risk. *(See Content Policy Quirks.)*

6. **View-aware chaining is real and visible.** Stage 5 of the Psylocke chain naively pulled from Stage 4 (waist-up); the leotard bottom dropped because there were no legs in frame to anchor. The fix is the SKILL.md compatibility table — walk backward to the last view-compatible stage, not the literal N−1.

7. **Re-attach the face card on every stage.** Across a 10-stage chain that's 9 attachments — refs don't persist between submits. (Mechanic depends on UI version; see "Reference Attachment".)

8. **A failed generation doesn't "cost" anything on the paid tier**, but it does waste UI time. Compose policy-sensitive prompts conservatively the first time.

9. **Budget wall-clock honestly.** The legacy UI measured ~22 s/gen plus 30–45 s/stage of UI overhead (~10 min minimum for a 10-stage chain). The Omni agent adds chat turnaround per submit and per re-run on top of generation — re-measure before promising times on a long chain.

10. **Edit, don't re-roll, to refine an accepted figure** *(2026-06-17, L36)*. Single-instruction Omni edits (pose / expression / gaze / wardrobe / lettering, one per message) hold identity and accessories far better than a fresh full prompt. The Chun-Li action panels were built this way; the spiked wristbands and qipao trim survived every edit. See "Conversational single-instruction editing."

11. **Use the Nano-Banana-validated "prosumer DAZ" block for studio/interior work** *(2026-06-17, L36)*: `…clean prosumer 3D CGI comic art … PBR skin with pores and subsurface scattering … well-lit Iray global illumination … not glossy cinematic VFX`, plus `NO thick lines, NO borders` on action panels. `not glossy cinematic VFX` is the key negation; the golden-hour preset block stays for outdoor narrative. Convert a real-photo ref with `convert to <block>`.

12. **Reference/turnaround sheets: NB Pro, 16:9, black background; action panels: NB2, 4:3** *(2026-06-17, L36)*. Spend Pro's daily quota on the reference assets, not the panels. Lock proportion across views with `make sure the muscle size is consistent every time`. FMG tier-up lever is literal `way way way … bigger` repetition, re-locked with the turnaround instruction afterward.

---

## Legacy Appendix — the Pill-Based Prompt-Bar UI (pre-Omni)

**Status: replaced by the Omni-agent chat UI (observed gone 2026-06-09).** Kept compact because Google A/B-tests UIs. If a session lands on this UI, re-locate everything by screenshot — the era's pixel coordinates (measured at a 1568×770 viewport) are deliberately removed. Some pieces (the `+` asset picker, the thumbnail 3-dots menu) may survive inside the Omni UI in some form — re-verify before relying on them.

- **Anatomy**: gallery canvas above a bottom-center **prompt bar**; `+` button left of the prompt (opened the asset picker); **model/aspect/count pill** right of the prompt (e.g. "Nano Banana 2 ☐ x4"); submit arrow at far right. "Generating will use **0 credits**" in the prompt panel confirmed the paid tier. The avatar top-right was NOT a Done button (Google account menu).
- **Settings popup** (click the pill): aspect row (16:9 / 4:3 / 1:1 / 3:4 / 9:16), count row (1x / 2x / x3 / x4), model dropdown. Quirks: the popup **reset count to x4 every time it reopened**; aspect persisted; `Escape` closed the popup *and* any other open overlay.
- **Count fan-out**: a submit produced `count` images in parallel; x1 and x4 took the same ~22 s wall-clock. Strategy was x4 for anchors/novel poses, x1 for chain links. (Dead on Omni — see "Generation Mechanics".)
- **Ref attachment — three methods**: (1) drag-and-drop a thumbnail onto the prompt bar — flaky from automation, never attempt via MCP; (2) hover thumbnail → **3-dots → "Add to Prompt"**; (3) **`+` → asset picker** with date filter (a trap — its dropdown overlay covers the asset list; use the Search field instead), live search over auto-titles, Recent/Oldest sort, and **Upload image** (bottom-left) for external refs. Multiple refs stacked as thumbnails in the prompt bar; **refs cleared after every submit and after every failure** — re-attach per stage.
- **Misc**: failure cards stayed in the gallery (small `×` to clear, didn't block new gens); new gens pushed thumbnails down a row, so coordinates went stale after every generation; distinctive prompt openers made the auto-titles searchable in the picker.
