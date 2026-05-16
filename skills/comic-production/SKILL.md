---
name: comic-production
description: |
  AI-assisted comic and graphic novel production using Nano Banana 2 image generation, available through two platforms: Higgsfield (paid, scriptable, batch runner via MCP) and Google Labs Flow (free on Pro, browser-only, manual driving). Use this skill whenever the user wants to create comic pages, graphic novel panels, sequential art, character transformation sequences, environment references, or batch-generate images. Trigger on any mention of: comic, graphic novel, panels, pages, Higgsfield, Flow, labs.google, Nano Banana, character sheet, DAZ3D style renders, transformation scenes, growth sequences, sequential art, or batch image generation. Also trigger when the user provides a script or story outline and wants it turned into generated comic pages, or when they mention generating environments/backgrounds for visual consistency across panels.
---

# Comic Production on Nano Banana 2 (Higgsfield + Flow)

This skill covers the complete workflow for producing AI-generated comics using Nano Banana 2. It's designed for DAZ3D-style sequential art where character consistency, environment continuity, and expressive storytelling matter.

Two platforms expose Nano Banana 2 and this skill supports both:

- **Higgsfield** — paid, but scriptable. Batch runner driven by Claude Code from the terminal via Python + MCP, full resume support, persistent state on disk. The default for production-scale work.
- **Google Labs Flow** (`labs.google/fx/tools/flow`) — free on a Google Pro/Pro Ultra subscription, but browser-only. Claude drives Flow's UI through the Chrome MCP — slower per panel than Higgsfield (no batch runner, manual ref attachment, no resume), but $0 marginal cost. Right for one-off pages, exploration, or when Higgsfield credits are constrained.

See the **Platform Selection** section below for the decision matrix.

The workflow has four phases: **Setup** (characters, environments, folders), **Bridge** (start the token relay — Higgsfield only) or **Browser session** (open the project in Chrome — Flow only), **Production** (write panels JSON and run the batch runner — Higgsfield; or drive the UI via Chrome MCP — Flow), and **QA** (check output against consistency rules).

## Before You Start: Reference Files

| File | When to read it |
|---|---|
| `assets/muscle-size-lineup.png` | **CRITICAL** — The master muscle size reference image (sizes 1–6). Upload to Higgsfield once per account. Attach as reference image + call out the size number in the prompt. See "Muscle Size Control" below. |
| `assets/muscle-size-lineup-4-9.png` | **HYPERMUSCULAR ONLY** — Extended lineup covering sizes 4–9. Use only when a story tier reaches size 7+ (beyond what the 1–6 lineup covers). Upload once per account. When used, prompts must reference numbers in the 4–9 image, not 1–6 — the two lineups have overlapping numbering and the model will mismatch if both are attached. |
| `assets/visual-quality-standards.json` | During QA — gold-standard benchmark images for muscles, veins, abs. Compare against these. |
| `references/fmg-anatomy-guide.md` | When writing FMG character descriptions — body-region prompt language, DO/DON'T rules, anti-patterns, and a full template fragment for muscle size 5–6. |
| `references/prompt-templates.md` | When writing panel prompts — style prefix, shot types, transformation scene templates (A–E), environment description examples, character-size language, prompt modifications. **PARTIALLY DEPRECATED**: the Mandatory Rules Block's speech-bubble lines, the Action Lines and SFX section, and the Dialogue Formatting section all conflict with L7 Case B (lettering goes to `page-composer`, never baked into the render). The file has inline ⚠️ markers on the obsolete sections — read the banner at the top before pasting anything. |
| `references/posing-and-expressions.md` | When writing character poses, facial expressions, or transformation showcase prompts. Covers: the core principle (lifeless expressions are actively bad, not neutral), the **growth sequence order** for multi-stage transformations (breasts → glutes → muscles), a **universal multi-character pose template**, three complete copy-paste prompts (BE / muscle-flex / glute-growth four-woman lineups), and the **facial acting mechanics table** (mechanical descriptions for triumphant pride, ecstatic joy, fierce intensity, smug satisfaction, etc.). The lineup templates extract cleanly to single-character panels — pick one pose angle + one emotional beat. |
| `references/multi-character-variation.md` | When writing ANY panel with 2+ characters — anti-uniformity rules to prevent the "police lineup" failure mode where the model makes everyone face the same direction, hold the same pose, share the same expression. Provides: the character-by-character prompt method, pose/arm/leg/gaze libraries to mix-and-match, scenario templates (group flexing, transformation, confrontation, casual), the mandatory POSE VARIATION block to paste into multi-character prompts, and a QA checklist. Pairs with `posing-and-expressions.md` (per-character mechanics) and `cinematic-framing.md` (camera variety). |
| `references/cinematic-framing.md` | When assigning per-panel camera/shot variety — distance categories (ECU through splash), angles (worm's-eye through bird's-eye), rhythm patterns (pull-in, pull-out, alternating field, orbit), and the variety check that catches camera-static sequences. Apply during script-breakdown AND during QA. Pairs with L1.5 in `lessons-learned.md` for chaining compatibility. |
| `references/environment-references.md` | When setting up hero locations (Bison's Lair, training dojo, sci-fi corridors, etc.) — the "DAZ3D scene reference" trick. Source a DAZ3D-rendered scene, save to `references/locations/<slug>/_source.jpg` with provenance, attach as an environment ref alongside character refs with transform instructions. Produces consistent, photoreal location backgrounds across the comic instead of the model re-inventing the location each panel. |
| `references/qa-checklist.md` | After generating panels — run before handing off to `page-composer` for lettering. Covers character consistency, environment consistency, facial expressions, camera variety check (post-L7 addition), transformation-scene QA (no-baked-lettering check, stage-change lineup-ref check), anatomy (incl. FMG-specific via `fmg-anatomy-guide.md`), and chained-sequence continuity (L1/L1.5/L9). **PARTIALLY DEPRECATED**: the original Dialogue and Text section is obsolete (lettering is post-render per L7 Case B); the "Action lines and SFX present" check is replaced with a "no baked-in lettering" check. Inline ⚠️ markers flag the obsolete items. |
| `references/lessons-learned.md` | When debugging failures — every known API gotcha, visual quality fix, and pitfall with solutions. |
| `references/three-panel-scenes.md` | When sprinkling a **single-image three-panel growth beat** into a longer story — bicep/breast/glute growth shown as 3 sub-panels rendered as one image. Distinct from chained multi-panel transformation arcs (see "Transformation scenes" in Phase 3). Has fillable templates for 1-character and 3-character interactions, horizontal and vertical orientations, CGI and photo styles, plus rules blocks and modifiers. |
| `references/flow-workflow.md` | When producing on **Google Labs Flow** instead of Higgsfield — UI mechanics, aspect/count selectors, the three reference-attachment methods (drag-drop, 3-dots → "Add to Prompt", `+` asset picker with Upload), Chrome MCP automation pattern, content-policy quirks, and how to apply view-aware chaining manually through the Flow UI. Read this first if the user names Flow or `labs.google/fx/tools/flow`, or if Higgsfield is unavailable. |
| `references/shotlist-driven-flow.md` | When a `shotlist.json` exists and the project is being generated on Flow — the **deterministic per-panel loop** that replaces hand-driven prompt typing. Covers: runtime prompt composition (from shotlist data + observed prior-panel state, NOT pre-composed batches), automatic state-anchor selection (view-aware per L1.5), ref attachment order, x4-always default on Flow (Pro is free), **Claude picks the variant** (per the autonomous-production memory), per-panel checkpoints (accept/retry/modify/skip), narrate-don't-ask interaction mode, when to actually interrupt for user judgment, and end-of-run archive cleanup. **The chain advances only when a panel is accepted**, so retries are free and unlimited. Pairs with `flow-workflow.md` (UI mechanics) and `lessons-learned.md` L1.5/L5/L7/L9. |

---

## Platform Selection: Higgsfield vs Flow

Both platforms run Nano Banana 2 and produce comparable image quality. They differ on **cost**, **driving model**, and **per-panel speed**. Pick the right one before you start.

| Concern | Higgsfield | Flow (`labs.google/fx/tools/flow`) |
|---|---|---|
| **Cost per panel** | Paid (Flash credits) or unlimited tier (slow) | Free on Pro/Pro Ultra plan ("0 credits") |
| **Driving model** | Python runner (`scripts/runner.py`) reads `panels.json` and calls the API | Claude drives the browser via Chrome MCP — clicks, types, attaches refs, submits |
| **Throughput** | High — one terminal command runs an entire script overnight | Low — every panel is hand-driven; ~30–45 sec UI overhead per panel on top of ~22 sec generation |
| **Resume after crash** | Yes — `state.json` records every completed panel; restart with `--start N` | No — if browser dies mid-chain you re-attach refs manually for the next stage |
| **Reference attachment** | Asset IDs / `.png` URLs in `panels.json` | Three UI methods: drag-drop, 3-dots → "Add to Prompt", `+` button → asset picker |
| **Multi-ref support** | Native — `medias[]` array per panel | Native — attach multiple refs to one prompt; both refs visible as thumbnails in prompt bar |
| **Aspect ratios** | Any width/height (e.g. 768×1024) | Five fixed ratios: 16:9, 4:3, 1:1, 3:4, 9:16 |
| **Output count per submit** | One per panel (multiples need multiple panels) | x1, x2, x3, x4 — same wall-clock for all (parallelized) |
| **Content policy** | Permissive enough for FMG with the standard rules block | Stricter — drop celebrity names from prompts that have detailed body description (the face ref handles likeness on its own); see flow-workflow.md "Content Policy Quirks" |
| **View-aware chaining (Rule #9)** | Reference prior job ID via `medias[]` | Same logic, but you select the prior gen via the `+` picker or 3-dots menu — no automation, you must walk the chain mentally |

### Decision rules

- **Default to Higgsfield** for any production-scale comic (3+ pages, dozens of panels, overnight batch).
- **Use Flow** when: (a) Higgsfield credits exhausted, (b) one-off page or quick exploration, (c) testing prompt variations cheaply, (d) the user explicitly names Flow or `labs.google/fx/tools/flow`.
- **Hybrid is allowed**: explore in Flow, then port the winning prompts into a `panels.json` for Higgsfield production.
- **The skill rules don't change between platforms.** All view-aware chaining (Key Rule #9), FMG anatomy guidance, mandatory rules block, muscle-size lineup attachment, and pose-variation conventions apply identically. The only differences are mechanical (how you attach a ref, where you set the aspect ratio).

For the full Flow UI guide — including the three reference-attachment methods, Chrome MCP automation, and the content-policy lessons learned — see `references/flow-workflow.md`.

---

## Muscle Size Control (Visual Reference Method)

**Never rely on text alone to control muscle/breast/body size.** The model interprets text descriptions of size inconsistently — what "very muscular" means to the model varies wildly between generations. Instead, use the **numbered muscle size lineup image** as a visual anchor.

### The Lineup Images

Two lineup files ship with this skill, covering different size ranges. **Default to the 1–6 lineup.** Only reach for the 4–9 lineup when a story tier exceeds size 6.

**`assets/muscle-size-lineup.png`** — 6 figures in identical double-bicep flex pose, labeled 1–6 above their heads, progressive growth:

| Size | Build | Clothing State | Breasts |
|---|---|---|---|
| **1** | Baseline/normal — slim, no visible muscle | Intact | Normal |
| **2** | Lightly toned — slightly broader shoulders, subtle arm definition | Intact | Slightly larger |
| **3** | Noticeably muscular — defined biceps and shoulders | Starting to strain, first small tears | Noticeably enlarged |
| **4** | Very muscular — prominent biceps/delts/quads | Visibly torn | Large, prominent |
| **5** | Massively muscular — huge biceps and quads, visible veins/striations | Shredded | Very large |
| **6** | Maximum — enormous proportions across all muscle groups, heavy vein detail | Barely holding together | Maximum size |

All six figures share the same outfit (white t-shirt, dark shorts), pose (double-bicep flex), hair (brown, shoulder-length), and background (rooftop cityscape). The ONLY variable is progressive muscle/breast/body growth.

**`assets/muscle-size-lineup-4-9.png`** — 6 figures labeled 4–9, extending the scale into hypermuscular territory:

| Size | Build | Clothing State | Breasts |
|---|---|---|---|
| **4** | Very muscular (overlaps with size 4 in the 1–6 lineup) | Visibly torn | Large, prominent |
| **5** | Massively muscular | Shredded | Very large |
| **6** | Maximum of the standard scale | Barely holding together | Maximum |
| **7** | Hypermuscular — bodybuilder-competition proportions, biceps wider than head | Destroyed/disintegrating | Hyper-enlarged |
| **8** | Extreme hypermuscular — cartoonishly massive, deep separation between every muscle group | Mostly absent — only fragments remain | Extreme |
| **9** | Maximum hyper — peak comic-book scale, towering over original baseline | Effectively gone — body fills the frame | Peak |

**Lineup-selection rule**: pick ONE lineup per panel and stick with it for the panel's prompt. Do NOT attach both lineups to the same panel — the overlapping 4/5/6 numbers will confuse the model. If a story arc spans both ranges (e.g., starts at size 2, ends at size 8), use the 1–6 lineup for early panels and switch to the 4–9 lineup once the character crosses size 6. Note the switch explicitly in the prompt: *"From this panel forward, size numbers refer to the 4–9 hypermuscular lineup."*

### How to Use It

1. **Upload the lineup image to Higgsfield once** as an asset. Note its `ref_id` and `.png` URL.
2. **Attach it as the muscle reference image** on any panel where muscle size matters.
3. **In the prompt, call out the number**: *"Character's muscle size, breast size, and waist proportions must match **size [N]** in the reference image."*

The numbers are baked into the image above each figure — the model can see them and match against the specific tier. **One image, all six sizes** — just change the number in the prompt.

### Why This Replaces Text-Based Size Descriptions

- The model has a **concrete visual target** — no ambiguity about what "very muscular" means
- Breast size, waist ratio, and muscle mass stay **in sync** (all from the same visual)
- Prevents the **reversion problem** — the model can't silently shrink when it has a visible benchmark
- **Consistent across all panels** — same reference image every time, different number
- Eliminates increasingly elaborate text descriptions the model may ignore anyway

### Prompt Fragments

For a character at a stable size:
```
Character's muscle size, breast size, and waist proportions must match size [N] in the reference image. Do not make the character smaller or less muscular than size [N].
```

For active growth (mid-transition):
```
Character is actively growing — transitioning from size [N] to size [N+1] in the reference image. Muscle mass, breast size, and waist proportions should be between these two sizes, closer to size [N+1]. Body is visibly swelling and expanding.
```

### When to Attach the Lineup

Per COMIC_PRODUCTION_GUIDE_V3: use the muscle lineup ref **only on stage changes** (when the character transitions to a new size tier), not necessarily on every panel. Between stage changes, the character face ref + sequential chaining handles continuity. But always include the size-matching text in the prompt regardless.

### Multiple References Per Panel

When a panel needs BOTH a character face ref AND the muscle size lineup:
- Character face/body ref → primary `ref_id`/`ref_url` (facial consistency)
- Muscle size lineup → additional reference (body proportions)
- Prompt: *"Match the face from the character reference. Match the muscle/breast/waist size from size [N] in the muscle lineup reference."*

### Size Rules

- Once a character reaches a size number, they **never go below it** in subsequent panels
- The lineup `.png` URL must be used — never `_min.webp`
- Before any transformation begins (panel 1), use the character's base asset alone — no lineup needed

---

## Architecture Overview (Higgsfield)

> **Using Flow instead?** Skip this section and Phases 2–3. Flow has no token bridge, no `panels.json`, and no Python runner — Claude drives the browser UI directly via the Chrome MCP. See `references/flow-workflow.md` "Tooling: Chrome MCP" and "UI Anatomy" for the equivalent.

```
Browser Tab (higgsfield.ai)
  └── token_bridge.js injected once
        └── exposes window.__getHiggsfieldToken()

Node.js Process (terminal, always running during batch)
  └── token_relay.js
        └── connects to Chrome via CDP on port 9222
        └── serves fresh tokens on http://localhost:9999/token

Python Process (Claude Code drives this)
  └── runner.py
        └── reads panels from panels.json
        └── GETs tokens from localhost:9999 before every API call
        └── writes state.json after every panel (resume-safe)
        └── calls fnf.higgsfield.ai/jobs/nano-banana-2
```

---

## Phase 1: Setup

> **Flow vs Higgsfield in Phase 1**: substeps 1.1, 1.2 (asset URLs), and 1.4 are Higgsfield-only. For Flow, skip 1.1 (no Chrome CDP needed), skip 1.4 (no folder ID required — every gen lives inside one project), and substitute 1.2's "asset ID + `.png` URL" with "build the baseline + face card per `flow-workflow.md` Step 2–3". Substep **1.3 Map Locations applies to both platforms.**

### 1.1 One-Time Chrome Configuration *(Higgsfield only)*

Chrome must be started with the CDP debugging port enabled. Do this once — add it to your Chrome launch script or shortcut:

```bash
# Mac
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222

# Linux
google-chrome --remote-debugging-port=9222

# Windows
chrome.exe --remote-debugging-port=9222
```

Verify it's working: `curl http://localhost:9222/json` should return a list of open tabs.

### 1.2 Gather Project Inputs

Before generating anything, collect from the user:

- **The script/story**: What happens on each page? Who are the characters? What locations appear?
- **Character reference images**: Must already exist on Higgsfield. Get the asset ID and full `.png` URL for each character state.
- **Art style**: Defaults to DAZ3D/Iray style. Adjust the style prefix if user wants something different.
- **Aspect ratio**: Default is 3:4 portrait (768×1024). Landscape (16:9) or square for specific panels.

**Image URL rule**: Always use the `.png` URL, never `_min.webp`. The thumbnail degrades output quality. Every asset has both — always pick the one ending in `.png`.

### 1.3 Map Locations

List every unique location in the script. Write a detailed verbal description (furniture, props, lighting, colors, time of day) for each. Store them as constants — paste identically into every panel prompt in that location. The model has no memory; inconsistent descriptions produce inconsistent rooms.

### 1.4 Create Higgsfield Project Folder *(Higgsfield only)*

Create a folder on Higgsfield before starting any generation. Name it clearly (e.g., "Comic Name — Vol 1"). Note the folder ID — it's a required argument to the runner.

For Flow, the equivalent is creating a Flow Project from the dashboard (`labs.google/fx/tools/flow` → "+ New project"). No ID is needed — every generation in the chain lives inside that one project automatically. See `flow-workflow.md` Step 1.

---

## Phase 2: Start the Token Bridge *(Higgsfield only)*

> **Flow users: skip this entire phase.** Flow has no token bridge — authentication is handled by the user's browser session. Make sure the Flow tab is open and signed in, then jump to `references/flow-workflow.md` "Production Workflow (Step by Step)".

The token bridge lets Claude Code call the Higgsfield API without touching the browser during the batch. Set it up once per session.

### Step 1: Inject token_bridge.js into the Higgsfield tab

1. Open `https://higgsfield.ai/image/nano_banana_2` and log in
2. Open DevTools → Console
3. Paste the contents of `scripts/token_bridge.js` and press Enter
4. You should see: `[TokenBridge] Running. Token available at window.__currentToken`

### Step 2: Install and start the relay

```bash
cd scripts/
npm install chrome-remote-interface   # one-time install
node token_relay.js
```

Expected output:
```
[Relay] Token relay running on http://localhost:9999
[Relay] Found Higgsfield tab: <tab-id>
```

### Step 3: Verify end-to-end

```bash
curl http://localhost:9999/token
# → {"token":"eyJ...","cached_age_seconds":0,"expires_in_seconds":45}
```

If this works, the Python runner can reach Higgsfield. If it fails, see troubleshooting below.

---

## Phase 3: Production

> **Phase 3 = Higgsfield production** (panels.json + Python runner). For **Flow production**, see `references/flow-workflow.md` "Production Workflow (Step by Step)" instead — the prompt-writing rules in **Section 3.1's "Prompt structure"** below still apply identically (style prefix, shot type, environment, character description, action/emotion, dialogue, mandatory rules block), as do the **Transformation scenes** and **View-aware chaining** sections later in Phase 3 (3.1 cont.). When working on Flow, read 3.1 for prompt structure, 3.1's view-aware chaining table, then jump to `flow-workflow.md` for the mechanics. Skip 3.2 (dry run), 3.3 (batch run), 3.4 (resume), 3.5 (retry) — these are runner-specific.

### 3.1 Write the Panels JSON *(Higgsfield-specific format; Flow uses the prompt bar directly)*

Create `panels.json` for the current comic. Each panel is an object with these fields:

```json
{
  "name":         "page_01_establishing",   // used in state.json and logs
  "prompt":       "...",                    // full prompt — see prompt structure below
  "ref_id":       "asset-uuid",             // character reference asset ID
  "ref_url":      "https://.../.png",       // character reference .png URL (NOT _min.webp)
  "ref_type":     "nano_banana_flash_job",  // for fixed refs; use nano_banana_2_job for chaining
  "width":        768,                      // optional, default 768
  "height":       1024,                     // optional, default 1024
  "aspect_ratio": "3:4"                     // optional, default "3:4"
}
```

See `scripts/panels_template.json` for a complete example. See `references/prompt-templates.md` for tested prompt fragments.

**Prompt structure** (every panel, in this order):
1. Style prefix (always first — copy verbatim from prompt-templates.md)
2. Shot type (wide, medium, close-up, extreme closeup)
3. Environment description (paste from your location constants)
4. Character description — list each character separately, in order of visual prominence. For each: name, current physical state, clothing. If a character appears in the panel but has no `ref_id`, note them anyway in the prompt — the runner will flag the missing ref. **For FMG characters**, use the body-region language from `references/fmg-anatomy-guide.md` — it provides DO/DON'T rules, anti-pattern avoidance (drumstick forearms, blocky abs, reverse-triangle figures), and a full template fragment for high muscle sizes. At minimum, every FMG character description should specify: hourglass figure, small head/hands/feet, round (not teardrop) breasts, pillowy (not blocky) abs, and asymmetric leg contours.
5. Action and emotion — describe what is physically happening, then describe every character's face in mechanical terms. Do not use emotion names alone. Specify: eyelid position, brow angle, cheek lift, mouth shape, mouth openness, and head tilt. Each character in the panel must have a distinct emotional beat — no repeated expressions, no neutral faces.

   Quick reference:
   | Emotion | Mechanical description |
   |---|---|
   | Triumphant pride | Chin slightly raised, lips closed in a satisfied smile, eyes alert and bright |
   | Ecstatic joy | Eyes shut tight, cheeks pushed high, mouth wide open in a laugh |
   | Shocked delight | Eyes wide, brows fully raised, mouth dropped open, head tilted back slightly |
   | Fierce intensity | Eyes narrowed, brows drawn together, jaw set, lips pulled back in a rallying grin |
   | Smug satisfaction | Eyes nearly closed in contentment, one corner of the mouth raised higher than the other |
   | Overwhelmed excitement | Head tipped slightly to one side, eyes wide, mouth open in a breathless gasp |
   | Playful self-admiration | Eyes directed at own body, brows raised, grin wide and mischievous |
   | Amused confidence | Relaxed full smile, eyes steady and direct, head held level |

   For the full posing guide and lineup templates, see `references/posing-and-expressions.md`.
6. Dialogue (exact speech bubble text with character attribution)
7. Mandatory rules block — read which rules apply from `production-config.json` at the project root if it exists. Compose the block from rules 1–10 minus any not in `mandatory_rules.active`, plus any `mandatory_rules.extra_lines`. Check `mandatory_rules.allow_baked_lettering` — when true, opt into L19 baked-lettering composition (physical-scene-object SFX + photoreal 3D speech panels with the L19 anchoring suffix); when false (default), strip all bubbles/SFX/captions from the generation prompt per L7 Case B. Copy the resulting block verbatim into every panel prompt.

   The pipeline supports five transformation types via the config's `transformation_type` field. Each has its own default rule set. The `production-briefing` skill writes the right defaults at project setup; this skill just reads them.

   If no config exists (legacy projects), fall back to pre-2026-05-13 behavior: present the full rules list at project start and ask which to drop. The ask happens ONCE per project, not per panel.

   **The 10 rules** — same as before, transformation-type-agnostic. The transformation type only determines which are default-ON; the rules themselves don't change.

   | # | Rule | Why it exists |
   |---|---|---|
   | 1 | Muscles are natural healthy skin tone — NOT red, NOT inflamed | Model renders muscles as red/inflamed during growth without this |
   | 2 | Skin is wet, shiny, glistening with effort, like oiled skin catching warm light | Gives the model a positive visual alternative to "straining" |
   | 3 | Any character with enlarged muscles also has proportionally enlarged, full breasts with prominent cleavage visible | Model won't add both unless explicitly told, every time |
   | 4 | All characters fully clothed at all times — clothes may be torn, stretched, or splitting at seams but always cover the body | Prevents nudity while allowing dramatic clothing destruction |
   | 5 | Speech bubbles show exactly the correct character speaking their correct line — never the wrong character | Model assigns bubbles by character position — wrong attribution breaks the story |
   | 6 | Every speech bubble contains a unique line — no character repeats themselves | Without this, characters echo each other or repeat lines across panels |
   | 7 | Every character has a vivid, animated, expressive face — never neutral or blank | Model defaults to lifeless expressions — the single biggest quality killer |
   | 8 | All characters look at each other, never at the camera | Eye contact with viewer breaks the fourth wall in narrative panels |
   | 9 | Correct human anatomy — exactly two arms per person, no extra limbs | Model occasionally generates extra limbs |
   | 10 | Once a character has grown muscles they stay at that size or larger in all subsequent panels — muscles never revert | Model reverts characters to reference image size without this |

   **Per-transformation-type defaults** (written automatically by `production-briefing` based on `transformation_type`):

   | Type | Active rules | Why these defaults |
   |---|---|---|
   | `fmg` | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 (all) | The historical default. The whole rule set was authored for FMG. |
   | `be` | 2, 4, 5, 6, 7, 8, 9 | Rule 1 (muscle skin tone) is N/A — no muscle growth. Rule 3 (muscle=breasts) is redundant — this IS the breast arc. Rule 10 (muscles never revert) is N/A — BE has its own monotonicity (in `extra_lines`). |
   | `glute` | 2, 4, 5, 6, 7, 8, 9 | Same reasoning as BE. Glute-specific monotonicity goes in `extra_lines`. |
   | `mmg` | 1, 2, 4, 5, 6, 7, 8, 9, 10 | Rule 3 OFF — male characters, no breasts. All other rules apply identically. |
   | `mixed` | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 (all) | Multi-arc — every rule may apply on some panel. Manual emphasis via `extra_lines`. |

   **Recommended `extra_lines` per type** — these aren't rules from the table above; they're project-specific addendums the briefing appends to the rules block:

   - **FMG**: usually none. The rule table itself is FMG-tuned.
   - **BE**: monotonic breast size, hourglass figure, round shape, seam-tearing clothing. See `production-briefing/SKILL.md` for the canonical BE extras.
   - **Glute**: monotonic glute size, hourglass figure, rounded shape, balanced thighs, seam-tearing wardrobe.
   - **MMG**: male anatomy throughout, pectorals (not breasts), V-taper, masculine facial structure, body-hair continuity.
   - **Mixed**: which arcs apply to which characters, growth order, current-active-stage lineup convention.

   **L19 baked-lettering opt-in.** When `mandatory_rules.allow_baked_lettering` is true:
   - Append the L19 opening anchor to the prompt: *"Hyperrealistic DAZ3D Studio 3D CGI render, ray-traced subsurface scattering on skin, physically-based rendering, 8K texture detail. Photographic CGI."*
   - Compose SFX as physical scene objects ("the word 'KRRRK' rendered as a 3D-extruded chrome letter sculpture, positioned upper-left of frame; real ray-traced shadows on the surface beneath; catches the same key light as the scene").
   - Compose speech bubbles as photoreal semi-translucent 3D panels ("a photoreal semi-translucent white 3D panel with rounded edges and an extruded tail, floating in the upper-right; tail extends down-left, pointing to the speaker; black extruded sans-serif text on the surface reads exactly: 'LINE'").
   - Append the L19 closing negation: *"NOT a comic, NOT an illustration, NOT anime, NOT cartoon, NOT 2D drawn art. Photographic CGI render."*
   - When false (default), pass the clean panel to `page-composer` for vector lettering per L7 Case B canonical. **Default is false** because the L19 reversal is still experimental and the failure mode on weaker models is silent 2D drift.

   **Common one-off drops** (overrides on top of the type default):
   - Rule 3 (muscles = breasts): drop for any male-only comic regardless of type
   - Rule 8 (no camera eye contact): drop for cover panels or direct-address moments
   - Rule 10 (no reversion): drop if the story includes an intentional de-transformation arc

**Reference images and multiple characters**:
- Every character who appears in a panel should have their own `ref_id` and `ref_url`. Add them as an array in the panel definition when multiple characters are present.
- If a character has no ref image yet, leave their entry as `null` — the runner will detect this, warn you, and continue without it. The panel will be flagged in the QA log.
- `nano_banana_2_job` — slow, free under Higgsfield's unlimited plan. Use for overnight batch runs when you're not at the computer and cost matters.
- `nano_banana_flash_job` — fast, costs credits. Use when you're at the computer and don't want to wait.

**Transformation scenes**: Never compress a *story-beat* transformation into one panel. Expand into: growth beginning → extreme closeup of focal body part → optionally a torso/reaction shot → full-body reveal. See `references/posing-and-expressions.md` for the growth sequence order (breasts first, glutes second, muscles third).

**Three-panel single-image growth beats** are a separate, deliberately compressed format — a single generated image rendered as three sub-panels showing fast progressive growth, used as a *decorative beat* between full transformation arcs (e.g., a quick bicep-flex moment between two longer story scenes). These are NOT a substitute for a chained transformation arc. When the user asks for one — or when a script calls for a punchy, montage-style growth moment — pull the right template from `references/three-panel-scenes.md`, fill in the `[BRACKET]` placeholders, append the correct Rules Block (CGI or PHOTO), and apply any Modifiers. The file's "Quick Reference: Template Selection" table picks the template by scene type, character count, and orientation.

**Sequential chaining is MANDATORY for transformation sequences (and any progressive multi-panel arc)**. The model has no memory between calls — if you generate panels T1…T10 in parallel using only the original baseline character ref, every panel re-derives state from text alone. The result is non-monotonic: a torn garment "heals" in the next panel, a size-5 body shrinks back to size-4, a hair bun re-forms after coming loose. Text descriptions of *progress* ("more torn than before", "larger than the previous panel") are unreliable because the model cannot see "before."

The fix: **each panel in the sequence must take a prior panel's job ID as a reference image**, in addition to the canonical face/portrait anchor. Generate sequentially — wait for each job to complete before submitting the next. Yes, it's slower; no, there is no shortcut. The runner handles this correctly when `ref_type: "nano_banana_2_job"` is used and the panel definition references the prior panel's job ID; if you are calling generate_image directly via MCP, pass the prior job ID as a `medias[]` entry with role `image`.

Always also pass the canonical portrait/face ref alongside the prior-panel ref. Without it, the face drifts over a long chain (the prior-panel ref carries body and clothing state but the face shows mid-shout, mid-impact, eyes-closed, etc., and chaining accumulates that drift).

### View-aware chaining (don't always pull from N−1)

The prior-panel ref carries forward two things:
- **State** — body size, clothing damage, hair, aura intensity. Durable, what you want to preserve.
- **View / body framing** — camera angle, framing, body orientation. Situational, only useful if the new panel shares it.

If the new panel is a *different view* than the prior, the prior-panel ref's body framing becomes a liability — the model partially obeys the prior framing and you get a malformed composite. Front view trying to inherit a back view's body. Face ECU trying to derive eyes from a panel where the face was off-screen. The result is worse than not chaining at all.

**Rule**: tag each panel with a view category. When chaining, scan back through prior panels and pick the most recent one whose view is *compatible*. That's your state anchor — not blindly N−1.

**View categories**: `front-full | 3q-full | back-full | side-full | ecu-face | ecu-region | low-angle-front | low-angle-back | high-angle | square-impact | wide-establish | splash`

**Compatibility (state anchor can come from any of these for the target view)**:

| Target view | Compatible prior views |
|---|---|
| `front-full`, `3q-full` | front-full, 3q-full, low-angle-front, wide-establish (front-facing), splash (front) |
| `back-full` | back-full, low-angle-back |
| `ecu-face` | another ecu-face, or any panel where the face was clearly visible |
| `ecu-region` (arm/hand/etc.) | another panel where that region was prominent and unobscured |
| `wide-establish`, `splash` | another wide/splash showing the same body orientation |

**Decision algorithm for panel N**:

1. Tag panel N's view.
2. Walk backwards N−1, N−2, … T1.
3. Stop at the most recent panel whose view is in N's compatibility set. Use it as the state anchor.
4. If none found in the chain, fall back to: the canonical character ref that *matches* the target view (e.g., back ref for a back panel, portrait for a face ECU). Then carry state forward verbally in the prompt — describe the cumulative damage / size / hair state explicitly, since the model can't see it.
5. Always include the canonical portrait alongside, regardless of which state anchor you chose.

**Worked example** — a 10-panel transformation that mixes views:

| # | View | Naive chain (wrong) | View-aware chain (correct) |
|---|---|---|---|
| T1 | front-full | base refs | base refs |
| T2 | ecu-region (arm) | T1 ✓ | T1 ✓ (T1 shows the arm clearly) |
| T3 | front-full | T2 ✗ (arm only — body view absent) | **T1** + portrait + verbal state from T2 |
| T4 | front-full | T3 ✓ | T3 ✓ |
| T5 | front-full | T4 ✓ | T4 ✓ |
| T6 | low-angle-front | T5 ✓ | T5 ✓ |
| T7 | back-full | T6 ✗ (front view) | **canonical back ref** + portrait + verbal state from T6 |
| T8 | ecu-face | T7 ✗ (face not visible from behind) | **portrait** + verbal state from T6 (last front-facing) |
| T9 | front-full | T8 ✗ (face only — body view absent) | **T6** (last front-full body) + portrait + verbal state from T7-T8 |
| T10 | splash (front) | T9 ✓ | T9 ✓ |

The naive chain produces visible drift at T3, T7, T8, T9. The view-aware chain preserves continuity throughout.

**State carry-forward in the prompt** when you can't use the prior panel as a visual anchor: spell it out. *"By this panel her qipao has cumulative tears at: side slits (from T3), shoulder seam (from T5), back seam (from T7). Hair fully loose. Body at size 6 hyper-muscular."* The verbal description is weaker than a visual anchor but stronger than nothing.

The same chaining rule applies to any **progressive sequence**: putting on/taking off a garment, charging up an attack, taking damage across a fight, weather changes across a montage. If continuity matters between adjacent panels and parallel generation would break it, chain — but chain *view-aware*, not blindly to N−1.

### 3.2 Dry Run (always do this first)

```bash
python scripts/runner.py --panels panels.json --folder YOUR_FOLDER_ID --dry-run
```

This prints every prompt and ref without generating anything. Review for:
- Missing mandatory rules block
- Wrong `.png` vs `_min.webp` URLs
- Panels that compress a transformation (should be 3-4 panels)
- Dialogue that would repeat across panels
- Characters with missing ref images — the runner will print a warning for each:

```
⚠️  panel_03_gym: 2 characters detected, only 1 ref_id provided.
    Missing ref for: Jack. Panel will generate without it — flagged for QA.
```

Missing refs do not stop the batch. They are logged to `state.json` under a `missing_refs` key and surfaced again in the QA summary at the end of the run.

### 3.3 Run the Batch

```bash
python scripts/runner.py --panels panels.json --folder YOUR_FOLDER_ID
```

The runner:
- Fetches a fresh token before every panel (token expiry is not a failure mode)
- Retries each panel up to 3 times before marking it failed
- Writes `state.json` after every panel (crash-safe)
- Adds completed images to the folder immediately
- Logs progress every 5 panels

### 3.4 Resume After a Crash

Read `state.json` to find the last completed index:

```bash
python -c "import json; s=json.load(open('state.json')); print('last:', s['last_index'], '| done:', len(s['completed']), '| failed:', len(s['failed']))"
```

Resume from the next panel:

```bash
python scripts/runner.py --panels panels.json --folder YOUR_FOLDER_ID --start N
```

Where N is `last_index + 1`. Completed panels in `state.json` are not re-generated.

### 3.5 Retry Failed Panels

Option A — retry specific panels by index:
```bash
python scripts/runner.py --panels panels.json --folder YOUR_FOLDER_ID --start FAILED_INDEX
```
(And stop after that panel by Ctrl+C, then move to the next failed index.)

Option B — create a `retry.json` with only the failed panels and run fresh:
```bash
python scripts/runner.py --panels retry.json --folder YOUR_FOLDER_ID
```

---

## Phase 4: Quality Assurance

After generating pages, run the QA checklist in `references/qa-checklist.md` against each output. Fix issues by adjusting the prompt and regenerating the specific panel using `--start INDEX`.

---

## Troubleshooting

### "Cannot reach token relay at localhost:9999"
- Make sure `node token_relay.js` is running in a separate terminal
- Check it's not blocked by firewall or port conflict: `lsof -i :9999`

### "Cannot connect to Chrome on port 9222"
- Chrome must be launched with `--remote-debugging-port=9222`
- Verify: `curl http://localhost:9222/json`
- If Chrome is already open without the flag, close it fully and relaunch with the flag

### "No Higgsfield tab found"
- Make sure `https://higgsfield.ai/image/nano_banana_2` is open in Chrome
- Make sure `token_bridge.js` has been injected in the console
- The relay searches for a tab URL containing `higgsfield.ai/image/nano_banana_2`

### 403 `not_enough_credits` errors
- Check that the panel's `ref_type` is correct — the runner sets `use_unlim` automatically based on this
- `nano_banana_2_job` = unlimited (free), `nano_banana_flash_job` = paid credits
- If you're out of Flash credits, switch panels to `nano_banana_2_job` and accept slower generation
- Check that your Higgsfield account still has unlimited mode active

### Jobs timing out (> 10 min)
- Higgsfield is under load — this is normal during peak hours
- The runner has a 10-min timeout per panel; increase `JOB_TIMEOUT_S` in runner.py if needed
- Failed panels are logged to state.json and can be retried

### Browser tab closed mid-batch
- The runner will get token errors once the tab closes
- Reopen the tab, re-inject `token_bridge.js`, restart `token_relay.js`
- Resume with `--start` from the last completed panel — state.json tells you where to restart

---

## Project File Structure *(Higgsfield only)*

> **Flow has no project files.** Everything lives inside the Flow project on `labs.google` — no panels.json, no state.json, no scripts. Track per-stage progress with `TodoWrite` in the conversation. Lessons & rules from this skill still apply; only the file artifacts are absent.

```
my-comic-project/
├── panels.json                  # Panel definitions for this comic
├── state.json                   # Auto-generated — runner state and progress
├── scripts/
│   ├── token_bridge.js          # Inject once into Higgsfield browser tab
│   ├── token_relay.js           # Run in terminal — serves tokens on :9999
│   ├── runner.py                # Claude Code runs this to execute the batch
│   └── panels_template.json     # Copy and fill in for new comics
└── references/                  # (from this skill — read as needed)
    └── fmg-anatomy-guide.md     # FMG body-region prompt language and anti-patterns
```

---

## Key Rules (Never Skip These)

> **Rules 1–4 are Higgsfield-only** (they describe runner behavior). **Rules 5–9 apply to both platforms** — the *mechanism* differs on Flow (described in `flow-workflow.md`) but the *rule* is identical. When working on Flow, treat rules 5–9 as the contract.

### Higgsfield-specific (runner mechanics)

1. **`use_unlim` is set automatically by the runner** based on `ref_type` — do not set it manually. `nano_banana_2_job` → `use_unlim: true` (free, slow, unlimited plan). `nano_banana_flash_job` → `use_unlim: false` (paid credits, fast). It must appear at top level AND inside `params` — the runner handles both. If you get a 403 `not_enough_credits` error, check that your panel's `ref_type` is correct, not the `use_unlim` value directly.
2. **Always use `.png` URLs**, never `_min.webp`. Thumbnails degrade character consistency. *(Flow equivalent: pick prior gens through the `+` picker or 3-dots → "Add to Prompt"; Flow handles the asset path internally.)*
3. **Token is refreshed before every panel** — the runner handles this automatically. Don't cache tokens manually. *(Flow uses the user's browser session; no token handling needed.)*
4. **State is on disk** — `state.json` is the source of truth. If you lose the terminal, read it to know where you are. *(Flow: track progress with `TodoWrite` in the conversation.)*

### Universal (apply to both Higgsfield and Flow)

5. **Transformation = multiple panels** — never one panel. Growth beginning, extreme closeup, reveal.
6. **Mandatory rules block in every prompt** — copy from prompt-templates.md. Omitting it produces red skin, repeated dialogue, wrong bubble placement.
7. **Use the muscle size lineup image for body size control** — never rely on text descriptions alone. Attach `assets/muscle-size-lineup.png` (sizes 1–6) as a reference and specify the size number in the prompt. For hypermuscular arcs reaching size 7+, switch to `assets/muscle-size-lineup-4-9.png`. Never attach both lineups to the same panel — the overlapping 4/5/6 numbering confuses the model. The model matches against the numbered figure visually. *(Flow mechanic: upload the lineup PNG once via `+` → "Upload image" — it then appears in the asset picker for re-use across all subsequent stages.)* See "Muscle Size Control" section above.
8. **Chain progressive sequences sequentially — never parallelize a transformation, growth, dressing, or charge-up arc.** Each panel must reference a prior panel's job ID (plus the canonical face anchor). Parallel generation with only the baseline ref produces non-monotonic state: garment tears revert, body size shrinks back, hair re-pins. Wait for each panel to complete before submitting the next. *(Flow mechanic: 3-dots → "Add to Prompt" on the prior gen + `+` picker for the face card. Submit, wait for the result, then attach the new prior gen for the next stage.)* See the "Transformation scenes" paragraph in Phase 3 above and `references/lessons-learned.md` for the full mechanism and a worked example.
9. **Chain view-aware, not blindly to N−1.** When the new panel's view differs from the prior panel's (e.g., front view following a back view, or a face ECU following a back-body shot), the prior-panel ref's body framing becomes a liability — the model partially obeys it and you get a malformed composite. Tag each panel with a view category, walk backwards from the current panel, and pick the most recent panel whose view is in the *compatibility set* for the target view. If none qualifies, fall back to the canonical view-matched character ref + verbal state carry-forward in the prompt. See "View-aware chaining" in Phase 3 for the compatibility table and decision algorithm. *(Flow mechanic: see `flow-workflow.md` "View-Aware Chaining in Flow" — same logic, walked manually through the gallery via 3-dots / `+` picker.)*

### Content policy *(Flow-specific addition)*

10. **On Flow, drop celebrity names from prompts that include detailed body description.** The face reference card carries the likeness — the celebrity name in the prompt only adds policy risk and triggers Flow's safety filter. (Higgsfield's filter is more permissive and this rule doesn't apply there.) See `flow-workflow.md` "Content Policy Quirks" for the full pattern set and recovery flow.
