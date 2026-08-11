---
name: publisher
description: Stage 7 of the production line — take a compiled, reviewed comic and PREPARE everything for posting, then STOP for the human. Emits projects/<p>/posting/bundle/ (destination-ordered publish checklist, per-platform captions, crop specs, site apply notes, What's-New draft, posted.template.json) and seeds analytics/engagement-stub.json (the flywheel landing pad). NEVER posts, uploads, deploys, or fires anything outward — publishing is always a human action. Use when the user says "prepare the publish", "get this ready to post", "prep the posting bundle", "publish prep for <comic>", "make the posting checklist", or when build-comic reaches the posting stage.
---

# Publisher — prepare, never post (Stage 7 of the seven-stage line)

> ## 🚫 THE RULE, BEFORE ANYTHING ELSE: THIS SKILL NEVER POSTS.
> No exception, no mode, no flag. It does not post, upload, deploy, schedule-to-fire, or take
> any outward action — not to the site, not to Patreon/DeviantArt/X/Instagram, not to
> updates.json, not anywhere. It **prepares**; the **human publishes**. This holds even in
> future Walk/Run autonomy modes (VISION §5/§6: "publish stays a per-post or per-batch human
> approval, never silent") and even if the user seems to ask this skill to post — posting is a
> separate, per-action, human-approved act outside this skill
> (`feedback_never_post_without_permission`). `scripts/prepare_post.py` enforces this
> structurally: it imports nothing that can reach a network.

This is **Stage 7** of `docs/PRODUCTION-SYSTEM-VISION.md` (§2, §5) — the line's exit:

```
IDEATOR → WRITER → STORYBOARD → REFERENCE → PAGE BUILD → REVIEWER ► PUBLISHER
                                                           (QA)      (prep → 🖐 human posts)
```

**Input:** a compiled, lettered, reviewed comic (final page set + project metadata).
**Output:** an **un-posted** publish bundle at `projects/<p>/posting/bundle/` + the analytics
landing pad. The human walks `CHECKLIST.md`, fires each platform, then fills
`posted.template.json` → saves as `posting/posted.json` — and *that* file appearing is what
marks the posting stage complete to `build-comic.md`.

**Local skill — source of truth is this repo** (per `CLAUDE.md`, never route through
`anthropic-skills:*`).

---

## Triggers

- "prepare the publish" / "publish prep" / "get this ready to post"
- "prep the posting bundle" / "make the posting checklist" / "posting prep for `<comic>`"
- `build-comic` reaching the posting stage (it should invoke this skill for the PREP half,
  then stop — posting itself stays manual)

NOT triggers: "post it", "publish it", "upload to Patreon/DA" — those are requests for the
human act itself. Respond by preparing the bundle (this skill) and handing over the checklist;
the firing of posts is out of scope by design.

## Preconditions (check before running)

1. **The comic is through review.** A final page set exists — `final/`, `pages/lettered/`, or
   `pages/page-NN.png`. If pages live outside the checkout (Drive, another repo copy), pass
   `--pages-dir`. If there is no finished page set, the project isn't ready for Stage 7 — send
   it back to page-composer/reviewer instead of preparing a bundle from panels.
2. **You know the property** (`growgetter` / `maxxmuscle` / `bloombeauty` / `3dmc`). If
   ambiguous, ask — captions, URLs, and the site path all key off it.
3. **QA state is known.** If `qa-report.md` has open findings, the bundle still prepares (the
   runbook's own stance: findings are the owner's call), but the checklist surfaces them at
   step 0.

## Workflow

1. **Assemble the mechanical bundle:**

   ```bash
   python3 skills/publisher/scripts/prepare_post.py \
       --project projects/<p> --property <prop> \
       --title "Display Title" [--comic-id <id>] [--issue N] \
       [--release-date YYYY-MM-DD] [--pages-dir <dir>] [--already-on-staging]
   ```

   This writes `posting/bundle/` (CHECKLIST.md, captions/, crop-specs.json,
   site-apply-notes.md, whats-new-draft.json, posted.template.json, MANIFEST.json) and seeds
   `analytics/engagement-stub.json`. It refuses to overwrite an existing bundle and refuses to
   run at all if `posting/posted.json` already exists (the comic is already posted) — `--force`
   overrides both after you've checked why.

2. **Fill the `[FILL-*]` caption slots.** The script leaves prose slots (synopsis, Patreon
   body, DA description, tweet, IG caption, extra slugs, What's-New hook). Claude fills them
   **from the shotlist and project text** — hook first, growth payoff promised but not
   spoiled, cast named, links left as `[SITE-URL]` until the human records the live URL in
   step 1 of the checklist. House content rules apply: DA mature flag ON, IG strictly SFW,
   X sensitive-media per content. Keep every filled caption inside the file it belongs to.

3. **Sanity-pass the bundle** — page count matches the shotlist (the script warns on
   mismatch), crop sources exist in the page inventory, property URLs are the confirmed ones
   (unknowns deliberately say "see cc-sites.json" rather than guessing).

4. **STOP. Hand over the checklist.** Show the human `CHECKLIST.md` (inline, not just a
   path), note anything unusual (QA findings, page-count mismatch, missing PDF), and end the
   turn. Do not "helpfully" continue into posting, do not open platform tabs, do not draft a
   scheduled task that would fire a post. Offering to *also* create the posting-board item is
   fine **as an offer** — creating board items on studio/posting.php is state-tracking, not
   posting, but it still touches the live server, so it stays a separate approved action.

## The bundle, file by file

| File | What it is |
|---|---|
| `CHECKLIST.md` | The destination-ordered human publish checklist. Order: **site → patreon → deviantart → twitter → instagram** (canonical home first — everything links to it; then paying members; then biggest audience (DA, per the 2026-07-25 posting-ops research); then socials). Keys match studio/posting.php's chips exactly. |
| `captions/<platform>.md` | Per-platform title/caption/tags, auto-facts filled by the script, prose filled by Claude in workflow step 2. |
| `crop-specs.json` | Per-platform image-crop SPECS — dimensions + which pages (cover + suggested teasers). **v1 renders nothing**; a human or a Wave-2 render step executes the specs. Teaser picks are suggestions the human verifies for SFW + non-spoiler. |
| `site-apply-notes.md` | What to add where on the site, pre-filled with this project's values. For WP properties this maps to `comic-platform/docs/PUBLISH-A-COMIC.md` (manifest → new_comic.py → verify → paywall → OCR/translate → URLs → syndication → flip reminder → WP side); for 3dmc it maps to the admin CMS flow. |
| `whats-new-draft.json` | A ready-to-prepend entry for the live `admin/data/updates.json` (schema per `reference_whats_new_feed`) — DRAFT only, `ts` null until the human posts it. |
| `posted.template.json` | The unfilled posting record. Human fills real URLs/dates after firing, saves as `posting/posted.json`. Schema: `references/posted-schema.json`. **Never create `posting/posted.json` yourself** — its existence = "posting done" to build-comic. |
| `MANIFEST.json` | Bundle inventory + provenance: page inventory with dimensions, source dir, files written, platform order. |
| `../analytics/engagement-stub.json` | The flywheel landing pad (Publisher → Ideator contract, VISION §4). Empty `captures[]` + a capture plan. How each source is read: `references/analytics-capture.md`. Wiring is Wave-2. |

## Hard rules (repeated because they are the point)

- **Never post/upload/deploy/fire anything.** Prepare and stop. The checklist is the handoff.
- **Never create `posting/posted.json`** — only the human who posted does that.
- **Never render or attach full-comic content into public-platform captions** — full pages go
  to the site + paid tiers; public posts get cover/teasers per crop-specs.
- **Credentials:** this skill needs none. Analytics capture (later, separate act) uses ONLY
  the `~/Documents/.credentials/bin/` wrappers (`ga`, `patreon`) — never raw secrets
  (`project_credential_architecture`).
- **Bundle text is project text** — commit it (CLAUDE.md rule 5). Never commit page binaries.

## Related surfaces

- **🗓 Posting board** (`studio/posting.php`) — the live status board this bundle feeds; see
  `references/posting-board-alignment.md` for exactly what the board does vs. what this skill
  adds and how they hand off.
- **Syndication ledger** (comic-platform `admin/syndication.html`) — the after-the-fact
  proof-URL record; checklist step 6.
- **build-comic.md** — orchestrator; its posting-stage sentinel is `posting/posted.json`.
