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

---

## ADDENDUM — laptop session, 2026-08-11 ~08:40 (READ THIS, it supersedes parts of the above)

Three defects were found and **fixed in code** today. Commits `54a511f`, `ab811ff`,
`76391b3`, `17ff18e` — all pushed to `origin/feat/comic-corpus`.

**1. Wardrobe never reached the model — 0 of 86 beats.** Beats carried a `wardrobe`
field; `fullPrompt` dropped it. The only clothing signal was the `margo` reference
image — a photo of her IN A LAB COAT — so the coat the story destroys at b17 kept
reappearing for the rest of the comic. Every prompt now carries a
`WARDROBE (exact ...)` block that explicitly outranks the reference.
*Proof: b40 and b43 were 0/4 and 0/7 before, 6/6 clean after.*
Pre-fix sheet preserved at `runners/bakeoff/margo-full-beats.json.bak-nowardrobe`.

**2. `drive.py winner` silently banked un-accepted panels.** `do=ingest` only returns
a `file` key on its dedupe path; the code read it unconditionally, so
`write_decisions`/`annotate` got `None` and no-opped. Uploads worked, then sat
`unrated`/`accepted:false`. That is why the board read 0 accepted despite successful
ingests. Now resolved by looking the `orig` name back up; fails loudly instead.

**3. The `state.json` race is FIXED — ignore the manual workaround above.** Mutating
commands (`record`/`fetch`/`fetchroll`/`winner`) now hold an exclusive `flock` on
`.state.lock` across the whole load→modify→save, with atomic temp+replace. You no
longer need to verify job counts after every `record`. Pre-lock copy at
`drive.py.bak-preflock`.

### The corrective queue lives in `runners/bakeoff/runs/margo-full-20260811/REROLL-QUEUE.md`
**12 beats**, with the exact corrective clauses that worked:
- **Lab coat, zero clean variants (7):** b18, b19, b22, b26, b48, b52, b53
- **Wrong action (1):** b18b-calipers — wardrobe fine, no tile shows calipers
- **Flat face (4, banked but should be replaced):** b02, b07, b13, b50

### Judge kill rule 9 — ADD THIS, it was missing
```
9. Flat face — blank, neutral, waxy, doll-like, or a mild expression on a beat that
   calls for something strong. A calm face on a dramatic beat is a KILL.
```
Face quality is in every prompt ("FACES: never blank or neutral") but was never a
kill rule, so 4 flat faces passed as KEEP and got banked.
**Text is NOT a problem:** all 42 banked pages audited, **0 text defects**.

### Two INPUT-level fixes to land BEFORE re-rolling (or defects reproduce)
1. **Scope the SLEEVES clause to Margo.** It is global and un-scoped, so KRESS's
   tracksuit shreds. Cost 6/8 tiles in b49, 3/8 in b06, killed b04 v02/v03.
2. **b45-tape identity bleed** — amulet + grey tank bound to INGRID in 3 of 4 tiles.
   Ref/staging attachment problem; do not re-roll blind.

### Two more gotchas
- **`registry.RETRY_INJECTION["WARD-01"]` is backwards here.** It says "match the
  attached reference images EXACTLY" — but the reference IS the source of the coat
  defect. Use the custom clause in REROLL-QUEUE.md.
- **`drive.py fetch` vNN numbering can collide** (two `v07`s). `winner` globs
  `<variant>-*.png` and takes the FIRST match, so banking by prefix can silently
  ingest a KILLED tile. Already bit b45 (caught) and b42. Check before banking:
  `ls variants/<beat>/ | sed 's/-.*//' | sort | uniq -d`

### Structure — settled, do not re-litigate
Owner confirmed: **each panel IS its own standalone page/image.** 86 beats = 86 pages.
No page-composition step. The Gribble 4-panel-grid figure does NOT apply to this run.

### Recovering images on the mini
`variants/**/*.png` are gitignored and laptop-local, but **`state.json` is now tracked**
and holds every job id. Recover any image via `show_generation_by_ids` (≤60/call) →
`results.rawUrl` → `python3 drive.py fetch <beat> <job_id> <rawUrl>`. Results persist
server-side; nothing already generated needs regenerating.

One junk board tile exists: `09db3a5283.png` (debug probe, prompt `test-probe`),
already marked rated=bad / tagged `probe-artifact`. Safe to delete.


---

## ADDENDUM 2 — owner review landed, 2026-08-11 (~this supersedes the corrective queue above)

Owner reviewed the 42 pages. Verdicts, ALL already applied to `margo-full-beats.json`
(backup `.bak-coatrespec`) — the night session executes, it does not re-decide:

1. **Flat faces PASSED** — b02/b07/b13/b50 stay. Keep kill rule 9 going forward.
2. **LAB COAT DITCHED from the entire comic.** All 86 wardrobe lines + the b13-b17
   coat-tear arc respec'd coatless (now a tank-strain arc; b14's line is now
   "THESE SEAMS ARE GETTING TIGHT!").
3. **Global SLEEVES clause DELETED (86/86)** — it was shredding Kress's and the
   investors' sleeves. Tearing lives only in Margo's wardrobe lines now.
4. **All 60 speaking beats now demand an OPEN MOUTH** under the balloon.
5. **Geography fixed:** the pitch is IN the gym; GEOGRAPHY clause on
   b23/b25/b26/b39/b41/b42/b45 and **b23 is now 16:9**.
6. **b45's "mystery girl" is INGRID** (investor) — identity bleed made her generic.
   Prompt now pins her to the investor blazer, no amulet. Verify refs, then roll.

**Work order changed:** REROLL-QUEUE.md is rewritten. 20 banked winners (b01-b17,
b41) are invalidated by the coat respec — their board panels are tagged
`respec-regen-pending` and stay accepted as placeholders until replacements land.
Net queue: 20 regen + 8 no-winner + b45 + 32 ungenerated ≈ 60 beats, ~120 credits.
