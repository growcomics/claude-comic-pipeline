# HANDOFF → mac mini: finish the margo-full comic

**Written 2026-08-12 by the laptop session. For the Claude Code session on the mac mini (or the night-shift worker).**
Owner is away. Standing mandate: keep working, don't publish anything outward, surface finals on the board.

## What this is

An 86-beat muscle-growth comic (Margo / Kress / investors serum arc) being produced through the
bakeoff lane: **anchor → over-generate → judge → select**. Roughly two-thirds generated, half judged.
Your job is to finish it without re-doing what's done.

- **Script (source of truth):** `runners/bakeoff/margo-full-beats.json` (86 beats, per-beat `chars`,
  dialogue lines ≤8 words, wardrobe/stage states) + readable `projects/margo-full/SCRIPT.md`
- **Run dir:** `runners/bakeoff/runs/margo-full-20260811/`
  (`state.json`, `sheets/*.jpg` contact sheets, `variants/<beat>/*.png`, `drive.py`)
- **Board (winners land here):** https://3dmusclecomics.com/studio/review.php?p=margo-full
- **Status at handoff:** 54 beats sheeted · 411 variants on disk · **42 winners picked**

## Do this, in order

1. `git pull` first. Run `python3 drive.py status` in the run dir to see exactly which beats have
   jobs/files/winners — trust that over this file, it may be stale by the time you read it.
2. **Judge every sheeted beat that has no winner yet**, then ingest. Do not regenerate a beat that
   already has variants on disk.
3. **Generate the remaining beats** (roughly b59–b86) at 8 variants each, sheet them, judge, ingest.
4. Checkpoint `git commit` + push every ~20 beats with a dated CHANGELOG entry.
5. When b86 is in: story-order contact strip, run stats, final commit, and a What's New entry
   (`admin/data/updates.json`, read-modify-write via the cPanel token — never print the token).

## Method (owner-set, do not "improve" it)

- **Model `nano_banana_2_lite` for everything**, 3:4, `count=4` per call (1 credit per call).
  Lite volume is effectively free — that's the owner's explicit policy.
- **8 variants per beat, SINGLE round.** No refinement rounds, no size ladders, no winner-anchors
  this pass (stage continuity rides on the stage-aware BODY block in the style string).
- Only exception: a beat with **zero** clean variants gets ONE corrective re-roll of 8
  (modest reframing if the cause was NSFW blocks).
- If a winner under-shoots on body scale, **take it and note the shortfall** — don't stall the run.

## Image-reading economy (hard rule — the run is ~900 images)

- **Never read images in your own context.** Two tiers only:
  - **Haiku** grades a whole contact sheet in one call: gross defects + keep/cull per tile.
  - **Sonnet** ranks only the 2–4 survivors per beat (paired composite), picks the winner + one-line reason.
- **Sanity-check the Haiku output.** One triage agent returned "all 36 tiles clean" from a single
  call; that was not a credible read and was discarded. If a triage comes back with zero culls and
  no per-tile detail, re-run it or escalate that beat to Sonnet.

## Judge contract (what kills a panel)

Insta-kill: skin rendered as torn fabric · **WARD-07 skin↔fabric gradient blend on a sleeved limb**
(legal: sleeve tears with frayed edges / rolled with a crisp edge / garment off — never a blend) ·
coverage violation (always_clothed: garments strain and tear, but breasts/groin stay covered) ·
headcount ≠ the beat's `chars` list · glitch/incoherent props · garbled OR blank speech bubbles
(dialogue is **baked in** per L19 — a specified line must render cleanly).
Then rank survivors on the vitality axes: **body scale vs the owner's standard** (his ⭐ Flow
favorites, not "realistic"), lighting drama, expression intensity, pose energy, frame-fill.
Rubrics by path, verbatim, never paraphrased:
`skills/continuity-check/qa-checklist.md`, `.../cinematic-framing.md`,
`research/owner-defect-feedback-2026-08-10.md` (+ its 2026-08-11 addendum),
`research/vitality-gap-2026-08-11.md` (style v2→v5 + the vitality gate).

## Camera doctrine (the owner's own words)

Import his prompt vocabulary **verbatim** from
`studio/extension/flow-studio-tools/content.js` (`pbFramingText`, `pbLightingText`, the
director/staging/detail block builders, the 19 lighting schemes). Vary angle per beat — never rut.
Payoff/flex beats favour the **elevated-intimate vantage**: camera ~1 ft above head height,
2–3 ft from the subject, looking down. Dialogue beats are torso-up two-shots with tilted eye-lines.
Groups use the anti-flat staging pyramid — never a same-height lineup.
Payoff beats also need wardrobe that **shows** the body: a baggy coat structurally caps how
colossal the silhouette can read (that lesson cost a whole 24-variant round).

## Known hazards in this run

- **`state.json` read-modify-write race.** Concurrent drivers silently drop each other's records.
  Verify job counts after every `record` call and re-issue if they don't match. Build contact
  sheets **from disk**, not from state, so bookkeeping races can't corrupt deliverables.
- **Rate limit:** roughly one group of 4 in flight. Cadence is submit-4 → poll to terminal →
  submit-4. Expect 429s; back off 30–45s. Keep concurrent drivers ≤3.
- `count=4` sometimes returns 3 images; isolated per-image failures are normal. Don't chase them
  unless a beat drops below ~6 variants.
- **b40-chalk**'s pool grew after a winner was already picked — re-judge that beat against the
  full 10-variant sheet.

## Rails

Bridge key `~/Documents/_imptest/bridgekey.txt`, deploy token `~/Documents/.3dmc-deploy-token` —
load into variables, **never print or commit them**. Never delete board images or projects.
Nothing publishes outward — Studio boards and drafts only.
