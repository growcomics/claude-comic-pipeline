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

## Default behavior

Unless the user overrides:

1. **Save location**: `./references/<subject-slug>/` in the current working directory
   - One folder per distinct subject (character, place, product). Slugify names: `pamela-anderson-baywatch-era`, `huntington-beach-pier`, `1995-baywatch-lifeguard-tower`.
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
