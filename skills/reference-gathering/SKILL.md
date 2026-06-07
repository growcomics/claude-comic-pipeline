---
name: reference-gathering
description: Gather visual reference images for characters, places, products, or styles by searching Google Images and YouTube, capturing high-quality stills with provenance. Use when the user asks to find reference photos, gather refs, build a character sheet from real footage, screenshot YouTube clips, collect mood-board imagery, or compile visual references for any creative project (comics, illustration, design, video). Trigger phrases include "find references for X", "gather refs", "screenshot Y from YouTube", "build a reference folder", "I need photos of X for the comic/scene/character".
---

# Reference Gathering

Build a structured `references/` folder of high-quality visual references for any creative project. Primary sources: YouTube (preferred — real footage, varied angles, controlled lighting) and Google Images (preferred for static subjects). Every saved image is logged with provenance.

## When this skill is the right tool

- "Find reference photos of [character / actor / location / product / style]"
- "Gather refs for the [comic / illustration / scene]"
- "Screenshot some clips of [show / video] for reference"
- Comic production, character-sheet building, mood-board assembly, style studies

If the user is describing a comic project end-to-end (script → panels), the comic-production skill drives the workflow — this skill handles only the reference-gathering subtask within it.

## Two operating modes

This skill runs in one of two modes depending on what it finds at the project root:

1. **Manifest-driven mode** (preferred — for comic projects, enforces L28). Triggered when `references_required.json` exists at project root. The skill reads the manifest and walks every missing item deterministically until the manifest is satisfied. Hard requirements apply (see L28 section below). `rules_audit.py` `check_reference_completeness()` is the gate.
2. **Freeform mode** (legacy / non-comic). No manifest at project root. The skill works from the user's natural-language request and the defaults below. Used for mood-boards, one-off character sheets, illustration references.

If you're handed a project with `shotlist.json` but no `references_required.json`, the manifest hasn't been generated yet — fall back to running `script-breakdown` (or its emit-manifest subroutine) first, then return to this skill. Do not attempt freeform mode on a comic project; you'll under-gather and stage 2 will reject.

---

## Manifest-driven mode (L28 — for comic projects)

Per **L28** in `comic-production/references/lessons-learned.md`, every comic project must have a complete set of references on disk before stage 3 generation can start. The manifest `references_required.json` (emitted by `script-breakdown` at project root) names every required file. This skill walks the manifest and produces every missing file.

### Schema reminder

```json
{
  "characters": {
    "<char_id>": {
      "face_card": "references/characters/<char_id>/face-card.png",
      "body_tiers": [
        {"tier": 1, "path": "references/characters/<char_id>/body-tier1.png", "lineup_required": false},
        {"tier": 3, "path": "references/characters/<char_id>/body-tier3.png", "lineup_required": true},
        {"tier": 5, "path": "references/characters/<char_id>/body-tier5.png", "lineup_required": true},
        {"tier": 6, "path": "references/characters/<char_id>/body-tier6.png", "lineup_required": true, "tier6_reinforcement_required": true}
      ]
    }
  },
  "locations": {
    "<loc_id>": {
      "establishing": "references/locations/<loc_id>/_source.jpg",
      "views": [
        {"name": "reverse", "path": "references/locations/<loc_id>/_source-reverse.jpg"}
      ]
    }
  }
}
```

### Walker workflow

For each character in the manifest:

1. **`face_card`** — if missing on disk, generate it. Use the Higgsfield MCP (`generate_image` with `nano_banana_2`) or Flow, depending on the project's `production-config.json` platform setting. Prompt is the character's canonical face description from `cast[].wardrobe` + a neutral expression anchor. Aspect 1:1. Save to the declared path.

2. **Each `body_tiers` entry**:
   - Check if the file exists. If yes, skip.
   - If `tier == 1` (baseline), generate from the character's wardrobe description + a hands-at-sides front-full pose. Aspect 3:4. **No lineup ref attached** at tier 1 (the character's natural baseline build is the target).
   - If `tier ≥ 2`: **HARD REQUIREMENT — attach the muscle-size lineup PNG as a reference image during generation**. Use `muscle-size-lineup.png` for tiers 1–6 or `muscle-size-lineup-4-9.png` for tiers ≥ 7. The lineup is a PROPORTION reference ONLY (per L11 surgical scoping): the prompt must explicitly tell the model "use figure N from the lineup ONLY for (a) muscle mass and frame width AND (b) breast SIZE / FULLNESS / forward PROJECTION; do NOT borrow face, hair, costume, or pose from the lineup; identity comes from the character's wardrobe description + the face card." Breast scale is a LOAD-BEARING attribute the lineup conveys alongside muscle scale — figure 6 has visibly larger and more forward-projected breasts than figure 1 — so the body-tier ref generation must anchor both attributes, not just muscle.
   - If `tier == 6` AND the entry also has `tier6_reinforcement_required: true`: **L29 HARD REQUIREMENT — additionally attach BOTH tier-6 reinforcement PNGs** from `skills/comic-production/references/peak-body-scale/tier-6/` (`tier-6-full-body.png` + `tier-6-anatomical-detail.png`) alongside the muscle-size lineup. These are repo-bundled assets — NOT character-specific generated refs — so this skill does NOT generate them; it just attaches them at submit time. Resolve their paths via the same search order the comic-production code uses (project `references/style/` override first, then the repo-bundled `peak-body-scale/tier-6/` directory). The reinforcement refs sit ALONGSIDE the lineup, not in place of it; the surgical-scoping language for tier-6 reinforcement is in L29 (see `comic-production/rules/l29_tier6_reinforcement.py`'s `L29_DIRECTIVE`).
   - Compose the prompt with:
     - Render anchor (DAZ3D Iray, photoreal CGI, etc.)
     - Camera: front-full, eye-level, 28mm equivalent
     - Subject: the character's name + cartoony hyper-FMG style anchor for tier ≥ 2 (per L11)
     - The tier-specific **muscular-build** descriptor (per L11's `_BUILD_BY_TIER` table in `rules/l11_muscular_build.py`)
     - Costume: the character's canonical wardrobe (the BASELINE costume, NOT the torn-up version — the tier ref is the body, not the damage state)
     - Lineup instruction: "The attached muscle-size lineup is a 3D BODY CHART showing six figures with TWO progressively-scaled proportion attributes per tier: muscle scale AND breast scale — NOT a silhouette / outline reference, NOT a face / hair / costume reference. CRITICAL — MUSCLE: match the 3D MUSCLE VOLUME and DEFINITION of figure {tier}. CRITICAL — BREASTS: match the BREAST SIZE, FULLNESS, and forward PROJECTION of figure {tier} EXACTLY — do NOT default to average / conservative breast size; do NOT render tier {tier} muscle mass with breasts shrunk to tier 2 or 3 size. The lineup scales both attributes per tier; render both at figure {tier}'s level. Use the lineup ONLY for these two proportion attributes plus frame width."
     - Closing CGI anchor.
   - Generate at x4 on Flow (free), pick the best, save to the declared path. On Higgsfield: count=1, accept the result.

3. **Each `views` entry** (per **L16** — multi-angle character reference packs):
   - Check if the file exists. If yes, skip.
   - Generate at the named camera angle using the body-baseline costume + the character's canonical wardrobe + the face card as a ref (for identity).
   - Camera mapping:
     - `3q-full` → "three-quarter view at 45 degrees, full body, 35mm equivalent, eye-level"
     - `profile` → "pure profile view, camera perpendicular to subject's facing direction, 50mm equivalent, full body"
     - `back-full` → "back-full view, 28mm equivalent, subject's back as the focal point, full body"
     - `low-angle-front` → "low angle from hip height tilted up, subject towers, foreshortened legs in foreground, 24mm equivalent for slight wide-angle distortion, full body"
     - `ecu-region` → "macro 100mm lens equivalent, hyperdetailed texture on the torso/midsection, abdomen and chest filling the frame, background completely defocused"
   - **Lineup attached** (`lineup_required: true`) follows the same L28 rule as body-tier refs. For v1, views are baseline-tier (lineup not required). v2 may add tier-N views with lineup attached.
   - Save to the declared path. Aspect 3:4 for body views, 1:1 for ECU-region.

4. **Failures**:
   - If the model refuses (NSFW filter, content policy) on a high-tier body ref: retry with softer language. If still rejected, surface to the user — they may need to soften the project's muscular-build target or accept a lower tier reference.
   - If the result looks like realistic-fitness instead of cartoony-FMG: the lineup attachment failed. Re-check that the lineup PNG was actually in the medias list at submission time. Retry with more aggressive vocabulary (per L11).

For each location in the manifest:

1. **`establishing`** — if missing, source a DAZ3D-style render (see "Gathering refs for locations and environments" below) OR generate one via the comic-production model with the location description from `locations[].description`. Save to declared path.
2. **Each `views` entry**:
   - For `name: "reverse"` — generate or source a 180°-opposite-angle reference of the same location. This is the L14 multi-view rule made concrete.
   - For other named views (low-angle, high-angle, detail): generate with the appropriate camera anchor.

### Required output

After every file in the manifest exists on disk, write `references/_completeness.md`:

```markdown
# Reference completeness report

Manifest: references_required.json
Status: COMPLETE
Files generated this session: N
Files already on disk: M

## Per-character
- chunli: face_card ✓, body-tier1 ✓, body-tier3 ✓ (lineup attached), body-tier5 ✓ (lineup attached)

## Per-location
- lex-lab-redsun: establishing ✓, _source-reverse ✓
```

Then exit. `rules_audit.py` `check_reference_completeness()` will pass and stage 2 closes.

### Hard rules for manifest-driven mode

- **Never skip the body-tier lineup attachment.** Tier ≥ 2 body refs MUST be generated with the muscle-size lineup PNG attached as a reference image. The whole point of L28 is that the character's identity-at-tier-N must be pre-rendered with proper proportion anchoring along BOTH attributes the lineup conveys (muscle mass / definition AND breast size / fullness / projection — the lineup is a 3D body chart showing both, NOT an outline reference, NOT a face/hair/costume reference), not invented per-panel.
- **Never skip the tier-6 reinforcement attachment.** Tier-6 body refs (and every shotlist panel at `muscle_size_tier == 6`) MUST additionally attach the two repo-bundled tier-6 reinforcement PNGs from `skills/comic-production/references/peak-body-scale/tier-6/`. The reinforcement PNGs are NOT character-specific — they isolate canonical tier-6 anatomical proportions as a dedicated anchor against the multi-figure lineup's tendency to interpolate the tier-6 figure downward. Per L29.
- **Don't economize.** If the manifest says 5 refs and 3 are on disk, generate the other 2. Don't decide on the fly that 3 is "enough." `rules_audit` will HARD-fail on missing files anyway.
- **Provenance still applies.** Even for AI-generated refs (not gathered from external sources), write a `_provenance.md` entry: prompt used, model, timestamp, lineup attached y/n. Future audits depend on knowing how each ref was made.
- **Do NOT modify `references_required.json`.** That file is the source of truth from script-breakdown. If the manifest is wrong, regenerate it at the script-breakdown stage; don't edit it from here.

---

## Default behavior

Unless the user overrides:

1. **Save location**: `./references/<bucket>/<subject-slug>/` in the current working directory. `<bucket>` is one of:
   - `characters/` — people (real or fictional), costumed characters, animals-as-characters
   - `locations/` — settings, scenes, architectural environments
   - `props/` — recurring objects (weapons, vehicles, signature items)
   - `style/` — mood boards, aesthetic references not tied to a specific subject
   
   One folder per distinct subject within its bucket. Slugify names: `characters/pamela-anderson-baywatch-era/`, `locations/huntington-beach-pier/`, `props/lara-sword/`, `style/1990s-action-aesthetic/`.
   
   *Backward compat*: existing projects with flat `./references/<slug>/` layouts still work — the skill won't auto-migrate. Use typed buckets for new projects. When a shotlist exists with `ref_folder` paths, those win — write to whatever path is specified.
2. **Frame count**: 5 verified images per subject, varied (different angles, expressions, lighting, wardrobe). "Verified" means each saved image has been visually inspected and confirmed to actually show the target subject.
3. **Provenance**: every folder gets a `_provenance.md` logging source URL, capture timestamp, (for video) seek-time, and a one-line QA note per kept image.
4. **Contact sheet**: at the end of a gathering pass, build `references/<subject-slug>/_contact-sheet.md` with thumbnails inline, and report back to the user with the list so they can thumbs-up or request a re-pull.
5. **No mid-flight confirmation**: gather the full default set, then surface results.

## Mandatory: QA pass — verify the subject is in the frame

**This is the most important step. Skipping it produces garbage references.**

The naive pipeline (pick a "best of [character]" video, extract evenly-spaced frames) fails badly because:
- "Best of" / "ultimate" / "intro" / "compilation" videos cycle through the entire cast — most frames are *not* the target character.
- Credit overlays ("JOHN DOE as Character") often appear at predictable intervals — evenly-spaced extraction hits them.
- Wide establishing shots, transitions, and reaction-cuts to other characters are common at any given timestamp.

**Required workflow for every character/person subject:**

1. **Extract a candidate pool, not the final set.** Pull 12-20 candidate frames per subject (more if the source is montage-heavy), not 5.
2. **Visually inspect every candidate before saving.** Use the `Read` tool on each JPG. Apply your own visual recognition — for famous people you already know what they look like; for less-known subjects, first pull a Google Images anchor photo and use it as the comparison reference.
3. **Keep only frames where the target is clearly identifiable**, ideally as the *primary subject of the frame* (centered or prominent, not just visible in a crowd).
4. **Reject and delete** frames that have any of:
   - Wrong person, no person, or target only in background
   - Credit-text overlays ("ACTOR NAME as Character")
   - Title cards, transitions, fade-to-black, or motion blur covering the face
   - Wide establishing shots where faces aren't legible
   - Multiple people where target isn't clearly the focus
5. **If fewer than 5 candidates pass QA**, pull more candidates (different timestamps, different video, or pivot to Google Images) — do NOT pad with rejected frames.
6. **Note QA reasoning in provenance**, briefly. Example: `pamela-03.jpg — face 3/4, smiling, clear (confirmed: matches Pamela Anderson Baywatch-era likeness)`.

## Source priority — revised based on QA cost

For **famous, well-photographed people** (actors, celebrities, athletes), Google Images is the better default because:
- Most results are dedicated solo promo/press shots — high hit rate, low QA reject rate.
- Each result has a source page with metadata.
- YouTube is much higher-effort per usable frame for these subjects.

For **motion-based subjects, characters in costume not otherwise photographed, or scene-specific staging**, YouTube can be worth the extra QA work — but use precise queries (see below) and budget for the verification pass.

| Source | When to prefer | Caveats |
|---|---|---|
| **Google Images → source page** | Default for famous people, static subjects (locations, products, single iconic shots) | Always click through to the source page; never save the Google thumbnail itself (low res, sometimes mis-attributed) |
| **YouTube (specific scene clips, not compilations)** | When you need motion, costume shots, or scene-specific context that Google Images won't have | AVOID: "best of", "ultimate", "intro", "opening credits", "season N highlights" — these are montages cycling through all cast. PREFER: "<actor> <show> full scene", "<actor> interview", clip uploads of single specific scenes |
| **Wikimedia Commons / official press kits** | When you want license-clean references | Lower volume; check first for known subjects |
| **Stock photo previews** | Last resort | Watermarked, often staged-fake — note in provenance |

**Avoid**: Pinterest (re-uploads, mis-attributed), Yelp business pages (the og:image is almost always a dish, not the venue — see user memory note), AI-generated image sites (defeats the point of *reference*).

## YouTube query rules (when you do use YouTube)

- **Avoid montage-keyword traps**: "best of", "ultimate", "intro", "opening", "credits", "season highlights", "compilation", "tribute". These return videos that cycle through the whole cast.
- **Prefer scene-specific terms**: "full scene", "[character name] scene", "interview", "behind the scenes".
- **Prefer single-character solo content**: solo interviews, dedicated character clips, single-episode uploads.
- **After picking a video, re-check before extracting**: read the video title carefully. If it's a montage you missed, pivot to a different result.

## Sources, ranked

| Source | When to prefer | Caveats |
|---|---|---|
| **YouTube (official channel uploads)** | Characters from films/TV, motion-based subjects (sports, dance, real people in costume), anything where you need varied poses | Re-uploads and clip compilations have lower frame quality and watermarks — filter for official network/studio channels first |
| **Google Images → source page** | Static subjects (locations, products, single iconic shots), historical or pre-video subjects | Always click through to the source page and capture from there — do NOT save the Google Images thumbnail itself (low res, sometimes wrong subject) |
| **Wikimedia Commons / official press kits** | When you want license-clean references | Lower volume; check first for known subjects |
| **Stock photo previews** | Last resort | Watermarked, often staged-fake — note in provenance |

**Avoid**: Pinterest (re-uploads, mis-attributed), Yelp business pages (the og:image is almost always a dish, not the venue — see user memory note), AI-generated image sites (defeats the point of *reference*).

## Workflow

### 1. Clarify subjects with the user (only if ambiguous)

If the user says "the Baywatch cast," ask which characters specifically. If they list names, proceed without further questions. Do not interrogate them — assume their first list is complete unless obviously incomplete.

### 2. Plan the folders

Decide one slug per subject. Confirm the list back in one line before downloading anything:

> "Gathering 5 refs each for: pamela-anderson-baywatch, carmen-electra-baywatch, david-hasselhoff-baywatch, huntington-beach-pier. Sound right?"

### 3. Gather — Google Images path (default for famous people)

Use the `mcp__Claude_in_Chrome__*` tools.

1. **Navigate** to `https://www.google.com/search?tbm=isch&q=<actor>+<role>+<show>` — be specific. For an actor in a known role: `carmen electra baywatch lani mckenzie`. For an era-specific look: add the year range.
2. **Read the results page** with `read_page` or `get_page_text` to identify the top ~15-20 candidate images and their source URLs.
3. **Pull candidate image URLs.** Use `javascript_tool` to extract image `src` attributes from result thumbnails, or click through and grab the source-page URL. Aim for ~10-15 candidates pulled.
4. **Download the candidate images** to `/tmp/refs-candidates/<slug>/` via `curl` (preserve original extensions). Don't save the tiny Google thumbnail — follow to the source-page image when possible.
5. **QA pass (mandatory — see "QA pass" section above)**: `Read` each candidate, judge if it's clearly the target subject. Keep 5; delete the rest. If fewer than 5 pass QA, search again with a different query and pull more candidates.
6. **Move kept images** to `./references/<slug>/<slug>-NN.jpg`, normalize to JPG via `ffmpeg` if needed.
7. **Log provenance** for each kept image: source page URL, site name, and any visible photographer credit.

### 4. Gather — YouTube path (when Google Images is thin or motion is needed)

Use the `mcp__Claude_in_Chrome__*` tools (DOM-aware, much faster than computer-use for browser work).

1. **Search**: `navigate` to `https://www.youtube.com/results?search_query=<subject>+<context>` (e.g. `pamela+anderson+baywatch+1995`). Add filters via URL params for "this year": uploaded by official channels when possible.
2. **Pick 2-3 source videos** from official channels or high-resolution uploads. Read the page to identify uploader. Skip if uploader looks like a re-upload aggregator.
3. **Open each video**, then scrub to moments with clear, varied shots of the subject:
   - Different angles (front, 3/4, profile)
   - Different expressions / poses
   - Different wardrobe or setting if applicable
   - Avoid frames with overlays, transitions, motion blur
4. **Capture frames**. Two options, in order of quality:

   **Option A (preferred — clean frames)**: use `yt-dlp` + `ffmpeg` via Bash to extract high-res stills at chosen timestamps:
   ```bash
   yt-dlp -f "bestvideo[height<=1080]" -o "/tmp/clip.%(ext)s" "<youtube-url>"
   ffmpeg -ss 00:01:23 -i /tmp/clip.mp4 -frames:v 1 -q:v 2 \
     "./references/<slug>/<slug>-01.jpg"
   ```
   This gives you the actual video frame with no YouTube UI, no player chrome, no watermark. Repeat for each chosen timestamp.

   **Option B (fallback)**: pause the YouTube player, hide controls (move mouse off, or press `c` to toggle captions off and click body), then `screenshot` via Chrome MCP. Crop the player region. Lower quality but works without `yt-dlp` installed.

5. **Log provenance** as you go (write to `_provenance.md` after each capture):
   ```
   ## <slug>-01.jpg
   - Source: YouTube — "<video title>"
   - URL: https://www.youtube.com/watch?v=...
   - Channel: <channel name> (official: yes/no)
   - Timestamp in video: 00:01:23
   - Captured: <ISO datetime>
   - Notes: 3/4 angle, beach setting, lifeguard uniform
   ```

### 4. Gather — Google Images path (for static subjects)

1. **Search**: `navigate` to `https://www.google.com/search?tbm=isch&q=<query>`. Use specific queries — `huntington beach pier 1995` beats `huntington beach pier`.
2. **Inspect results** with `find` or `read_page` to identify candidate images and their source links.
3. **Click through to the source page** — never save the Google thumbnail directly. The thumbnail is low-res and Google sometimes mis-categorizes images.
4. **On the source page**, either right-click-save the full-res image (via Chrome MCP) or `screenshot` the relevant region if the image is embedded.
5. **Verify the subject**. Quick sanity check: does the image actually show the thing you searched for? Mis-attribution on Google Images is common, especially for "[place] [year]" queries.
6. **Log provenance** with source page URL (not the Google search URL), site name, and any visible photographer credit.

### Gathering refs for locations and environments (CGI comic projects)

For CGI / 3D-rendered comic projects (those using the `comic-production` skill), location refs benefit from a specific technique beyond standard photo gathering: the **DAZ3D-scene-reference trick** — source an existing DAZ3D-rendered scene with the right lighting/scale/render style, save it as `_source.jpg`, and use it as an environment reference image in the panel prompt with instructions to transform its content to your target location. The model anchors to the render's technical style (Iray lighting, photoreal materials, scale, depth) and substitutes the content.

Full workflow lives in the `comic-production` skill's `references/environment-references.md`. Brief summary for the gathering step:

1. **Slug into `references/locations/<location-slug>/`** per the typed-bucket convention above.
2. **Search DAZ3D gallery, Renderosity, Renderhub, ArtStation** with queries like `daz3d scene "<location keyword>"`, `daz studio iray render <keyword>`, `site:daz3d.com gallery <keyword>`. **Avoid Pinterest** — re-uploads and AI-generated mis-labels are common there and defeat the trick (the technique only works if the source is a genuine DAZ3D / Iray render).
3. **Save the chosen render as `_source.jpg`** in the location folder. Note source URL, original creator, and your QA note in `_provenance.md` per the standard convention.
4. **Optionally gather standard photo references** alongside, saved as `<slug>-NN.jpg`, for the writer/director to understand the real-world feel of the scene (color palette, scale, mood). These are for human consumption; only `_source.jpg` is the file the model will see.

**When NOT to use this trick**:
- Generic exteriors the model handles well without anchoring (forest clearings, generic streets, beaches at sunset).
- Non-CGI projects (illustrated comics, 2D animation references) — fall back to standard photo gathering.

### Location packs from `location-scout` (city-level reusable pre-renders)

If the project's setting is a real city and a **city-scout pack** exists for that city under `references/locations/<city-slug>/` (built by `skills/location-scout/SKILL.md`), prefer it over per-project location generation.

A city pack is a pre-built bundle of 8–15 photoreal CGI-style background refs covering the spectrum (downtown street, residential street, alley, diner, restaurant, casino exterior, rooftop, etc.) — all anchored to real Google Maps captures of the city. Pack location:

- Repo-level shared pack: `<repo>/references/locations/<city-slug>/` — usable by any project
- Project-private pack: `<project>/references/locations/<city-slug>/`

Walk `meta/locations.json` to find the closest match for a shotlist location:

1. Match by `type` (street / restaurant / landmark / specific) against the location's intent
2. Within type, match by `tags` overlap (e.g. shotlist wants "downtown neon street" → tags include `downtown` + `neon`)
3. Attach the pack entry's `cgi_image` path as the env ref for the project's `references_required.json` `establishing` slot — no generation needed

For locations the pack doesn't cover, fall back to standard generation. When a pack entry IS used, copy the CGI image into the project (don't symlink — packs are versioned independently and a project ref should be stable) and record provenance.

City packs preempt L23's verbal env-anchor fallback for the panel — the CGI ref is more specific than any 5-element verbal description. L23 still applies to projects with no available pack.

To build a new city pack: invoke `location-scout` with `--city "<name>" --count 11` and run end-to-end. ~$0.30–0.55 in Higgsfield credits per pack (default 11 × 1.5–2 credits / gen).

### Gathering refs for props

For recurring objects (weapons, vehicles, signature items, distinctive accessories), use the standard Google Images / YouTube workflow with the `props/` bucket: `references/props/<prop-slug>/`. Google Images is usually the right source — product photos for licensed objects, gallery shots for custom designs. YouTube can help for items shown in motion (a specific sword from a fight scene, a vehicle mid-chase).

2–3 clear views is usually sufficient (front, 3/4, detail) — 5 images is overkill for most props. Note in `_provenance.md` whether the prop is a real-world object (licensable) or a fictional design (one-off illustration / 3D model).

### 5. Build the contact sheet

After gathering, write `./references/<slug>/_contact-sheet.md`:

```markdown
# <Subject> — reference contact sheet

Gathered <date>. <count> images.

## Images

![01](./<slug>-01.jpg) — 3/4 angle, beach, uniform (YouTube clip)
![02](./<slug>-02.jpg) — front profile, indoor (Google Images)
...

## Sources used
- <video title> — youtube.com/...
- <article title> — example.com/...

## Provenance
See `_provenance.md` for full details per image.
```

### 6. Report back

In your final message, list each subject with image count and one-line notes. Offer to re-pull any subject the user isn't happy with. Don't auto-iterate — wait for direction.

## Hard rules

- **Provenance is non-negotiable.** Every image gets a `_provenance.md` entry. If a source can't be tracked, don't save the image.
- **No Google Images thumbnails.** Always go to source.
- **No Yelp og:images for venue references.** Yelp's default image is almost always a dish photo, not the venue itself.
- **No Pinterest as primary source.** Re-uploads are mis-attributed at high rates. If a Pinterest pin is the only lead, follow it back to the original source and capture from there.
- **License awareness.** These are *references for human-drawn or AI-generated derivative work*, not assets to redistribute. If the user's project will publish reference images directly (e.g. a mood board posted publicly), flag licensing concerns and prefer Wikimedia Commons / press kits.
- **Don't fabricate frames.** If a video doesn't have a good shot of what was requested, say so — don't grab a marginal frame and pretend it's good. Suggest an alternative search.

## Common asks and shortcuts

- **"Just get me 10 of [character]"** → one folder, 10 frames, mostly YouTube, varied angles. Skip the clarification step.
- **"Build a character sheet for [character]"** → 8-12 frames, deliberately covering: front / 3/4 / profile / back if available; neutral / smiling / action expressions; full body and head-and-shoulders. Note coverage gaps in the contact sheet.
- **"Mood board for [vibe]"** → looser. 15-20 images across multiple subjects/locations/textures sharing the aesthetic. One folder, no per-subject sub-slugs.
- **"References for the [scene/setting]"** → location-focused. Google Images first, YouTube second (b-roll from documentaries or vlogs is gold for setting refs).

## Tools you'll use most

- `mcp__Claude_in_Chrome__navigate`, `read_page`, `find`, `screenshot` — primary browser interaction
- `mcp__Claude_in_Chrome__javascript_tool` — for clicking specific YouTube timestamp links, hiding player UI, etc.
- `Bash` — `yt-dlp`, `ffmpeg`, `mkdir`, image inspection (`identify` from ImageMagick if available)
- `Write` — `_provenance.md`, `_contact-sheet.md`

If the Chrome extension isn't connected, ask the user to install it before falling back to computer-use (browsers are read-only tier under computer-use, so clicking and typing will fail).
