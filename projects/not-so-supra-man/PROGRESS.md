# Not So Supra... Man — Autonomous Build Progress

## 🔁 RESTART v2 (2026-06-10, user-ordered full rebuild)
v1's 17 pages had systemic defects (D1–D14, see qa/defect-registry.json) — user ordered a clean
rebuild in a NEW Flow project, references-first, all gates enforced. Execution order:
`references/restart-plan-v2.md`. Pre-submit gate: `qa/preflight.py`.
**STATUS: blocked at Phase 0 — growcomics Google account is SIGNED OUT on the macmini Chrome**
(account chooser open in the Flow tab; agent cannot enter credentials — user must sign in, then say go).
v1 assets remain on disk + in the old Flow project ("Jun 09, 11:25 PM") for cross-project reuse.

_Live log — Claude updates this as it goes. Started 2026-06-10._

## Status: PAGE GENERATION in progress — 9 story pages banked, foundation 100% done

## 🔴 REFS-ARE-TRUTH REFIT (user QA feedback 2026-06-10 — supersedes recipe below)
User-confirmed root causes on the first 17 pages: (1) too few refs per page, (2) flat expressions, (3) characters default front-facing, (4) outfits vary per variant because costume lived in PROSE, and there is no canonical image of several wardrobe states (e.g. Dana torn-T6) — anything not pinned by a reference re-rolls per variant.
**Fix (recipe v3 — supersedes v2):** generate HEIGHT-PINNED TURNAROUND SHEETS (front/3q/profile/back + grey scale-silhouette + grid, one 16:9 image) per character per wardrobe state (`references/turnaround-specs.json`, heights from `references/height-chart.json`) + SCENE LADDERS per location (wide → medium → close rungs, chained; attach the rung matching the shot's camera distance — D8 basketball-court rule) + STAGING REFS for novel poses (D9). Per page attach: [state turnaround]+[face card]+[matching scene rung]+[staging ref if novel pose]+[prior accepted panel]; prompt = camera FIRST → action → expression block → "outfit/damage/HEIGHT exactly as attached refs". Size language always pairs with height clamp ("muscle mass increases, height does NOT" — D7, p12 rendered giantess wrongly). Defect taxonomy: `qa/defect-registry.json` (D1–D13); user reviews via Flow Red-Pen extension (`tools/flow-review-extension/`, tags regenerated from registry).
**RECIPE v4 (supersedes v3, adds D11/D12/D13):** prompts are MAXIMAL structured JSON specs per `qa/prompt-template-v4.json` (submitted single-line) — camera/scene-continuity/per-character position+orientation+per-limb pose+expression/spatial_rules/lighting/negatives. Appearance = pointer-only to attached refs (THE LAW: prose-appearance allowed solely when bootstrapping a character with zero refs). EVERY character in frame has face+turnaround attached. Per-hand accounting + total-hands line mandatory. Staging refs are inspected/perfected BEFORE the page consumes them.

## ⭐ RESUME INSTRUCTIONS (read this first)
**Everything hard is solved. Remaining work = mechanical page generation using the proven recipe.**
1. **MODEL: use Nano Banana 2, NOT Pro.** Nano Banana Pro hit a sustained generation rate limit ("requesting generations too quickly") after ~200 images this session. Switching the model pill → Nano Banana 2 (the unlimited workhorse, same family, L35-validated) BYPASSES it and is faster. The pill is currently set to NB2.
2. **Per-page recipe** (one `browser_batch`): click pill→set aspect→click input; click `+`→search term→click 1st result→"Add to Prompt" (repeat per ref); click input→type prompt→click submit arrow (1037,728). Aspect btns in pill popup: 16:9(788,548) 4:3(839) 1:1(890) 3:4(940). Picker search field y≈123 (no ref attached) / y≈67 (ref attached); "Add to Prompt" y≈619 / y≈562.
3. **Refs**: attach the foreground character's body-tier card (embeds face+size). Search terms in cheat-sheet below. For Dana T6/T9 ("super-suit" — shared title) verify size in preview pane (T6 amazon, T9 colossal). **Tier-9 Dana pages (39-46): ALSO attach anchor (search "lana") + 4-axis no-downsize gate vs anchor.**
4. **Harvest after completion**: wait ~40s, then JS-harvest newest valid uuids (filter `getMediaUrlRedirect`, left<1100, width>150) → newest 4 = the page (16:9 wraps 3+1). Record flow_id in pages-log.json. Download later via scratch-tab navigate→signed URL→curl.
5. **Prompts for all 46 pages are pre-written in `pages-plan.json`** (refs + aspect + action prompt, L7-clean no lettering). Pending pages listed in `pages-log.json`.
6. Then: comic-status-board → continuity-check (subagent, canonical rubric) → page-composer (bake shotlist dialogue/SFX as overlays) → pages/page-NN.png → PDF.

## DONE (banked to disk, pages/panels/) — ACT 1 COMPLETE + interlude/transition
p03–p19 = **17 story pages**, all on-model & banked. Covers: rescue (p3-5), first-sensation (p6), Dana tier-4 growth (p7-9 incl. progressive arm/abs), aftermath (p10-11), tier-6 amazon surge (p12) + progressive chest/back/legs (p13-15), tier-6 aftermath/chin-lift (p16), bridal-carry interlude (p17), lab-exterior cutaway gag (p18), morning-after locker (p19). pages-log.json = source of truth (flow_id per page).
- NSFW note: p13 (progressive chest) — 3/4 variants hit the policy filter; used the sole survivor. Other sensitive pages (p41 tier-9 chest) will likely also need the soften-and-retry; keep "coverage fully intact / muscular chest", drop cleavage words.
- p02 generated (in Flow gallery, NOT downloaded — recoverable via search/scroll).
**PENDING: p01 (cover, hardest), p02 (download only), p16–p46 = 32 pages + p02.** See pages-log.json `pending`.
- p16-19: tier-6 aftermath + lab-quarters + locker (use danaT4/danaT6 super-suit per wardrobe). **p20-37: Dana in BLUE super-suit → use danaT6 "super-suit" card** (verify amazon size in preview). p22-27 Dee-Dee arc (deedeeT3 "lab coat" → deedeeT8 "standing villain"). p31-37 city battle (deedeeT8 + danaT6 + loc:city). **p38-46 tier-9 finale → danaT9 "super-suit" (colossal) + anchor "lana" + 4-axis no-downsize gate.** p39-42 progressive (tier-9 growth). p43-44 Dana>Destroya reveal+uppercut. p45-46 + cover p1 = final-form composites.

## (earlier log) Status: REFERENCE GENERATION — body-tier ladder

## Verified workflow (locked)
- **Generate**: type prompt in bottom input → submit arrow → **x4 variants in ~75s** (direct pill mode; no "Generate one image." prefix needed). Pill = aspect/count/model.
- **Attach refs**: `+` (bottom-left of input) → asset picker → click asset → "Add to Prompt"; repeat to STACK multiple; `×` clears. Refs assumed non-persistent — re-attach per gen.
- **Aspect**: click pill → 1:1 (faces/ECU) / 3:4 (full body) / 16:9 (wide) / 4:3 (medium).
- **Harvest+download**: JS harvest img `getMediaUrlRedirect?name=<uuid>` (newest-first = gallery left→right). Resolve signed URL by navigating scratch tab → curl. Download only the chosen variant.
- **Face cards LOCKED**: Dana `01b9bbf0`, Supraman `8bf6a23e`, Dee-Dee `d8a98176`, Doomer `264c9a99`.

## Locked facts (verified this run)
- **Flow**: macmini browser connected; project "Jun 09, 11:25 PM" open; signed in growcomics (PLUS).
- **Model**: Nano Banana Pro · x4 (pill confirmed). Aspect set per shot.
- **SIZE ANCHOR (tier-9 truth)**: Flow media `4d81c347-a431-44f7-9bf3-c3c53ff8b46b` ("Super-Lana Lang" 3-view model sheet — arms wider than head, boulder delts, deep chest shelf). NOTE: task's `da8fec25…` id was stale; `4d81c347` is the real one. Saved local copy in `.flow-scratch/anchor-4d81c347.jpg`. Attach on EVERY tier-9 Dana gen + hard no-downsize gate.
- **Download pipeline**: navigate scratch tab → `media.getMediaUrlRedirect?name=<uuid>` → read signed `flow-content.google` URL from tab title → `curl` to disk. Works.
- **Pre-existing gallery media**: anchor (4d81c347) + 4 Dee-Dee/Destroya tier-8 body-card candidates (6fd24c37, b02d4e7e, 778ec7fc, 68caf1eb) + 4 landscape L35 leftovers (f555c148, 7b16ff95, 1bee548e, 0d71fb5d).

## Plan
1. Pin down Omni-UI **reference attachment** mechanic (make-or-break) + upload repo lineup/reinforcement assets into Flow.
2. **Reference set** (per references_required.json + size-ladder): face cards (4 cast) → body-tier cards locked bottom-up (Dana 2→4→6→7→9, Dee-Dee 3→8, Supraman/Doomer base) → views → locations → props.
3. **46 pages** — deterministic per-panel loop, best-of-4, tier-9 no-downsize gate, growth-progressive 3-substage pages.
4. Status board → continuity-check → page-composer (bake dialogue/SFX overlays) → 46 `pages/page-NN.png` → PDF.

## Reference progress
- **Face cards** (4/4): Dana `01b9bbf0`, Supraman `8bf6a23e`, Dee-Dee `d8a98176`, Doomer `264c9a99`.
- **Body ladder LOCKED** (no-downsize verified):
  - Dana T2 `53ae3c76` → T4 `3c004457` → T6 `bba21ce4` → **T9 `270c06dc`** (passed 4-axis gate vs anchor)
  - Dee-Dee T3 `c7ec4291` → T8 `2f4e1204`
  - Supraman base `74c0857f`, Doomer base `5e32792d`
  - Tier-7 (Dana) skipped — only 1 transitional panel (p39); rendered inline from T6→T9 + anchor.
- All saved to references/characters/<id>/ + ref-ledger.json. Repo lineup/reinforcement could NOT be uploaded (file_upload allowlist); held the ladder via anchor + tier chaining + escalation instead.
- **PER-PAGE REF SHORTCUT**: body-tier cards already embed the locked face → attach just the current tier card per character (1 ref/char). Anchor `4d81c347` (search "lana") re-attached on every tier-9 Dana page.

## Reference attachment cheat-sheet (picker auto-titles)
- Dana face "young woman beauty" · Dana T2 "white blouse" · Dana T4 "flexing muscular" · Dana T6/T9 "blue super-suit / muscular woman"
- Dee-Dee face "blonde hair" · Dee-Dee T3 "lab coat" · Dee-Dee T8/Destroya "villainess"/"corset"
- Supraman base "blue superhero" · Doomer "bald man" · Anchor "lana"
- Picker: `+` → search field (y≈67 when a ref is already attached, y≈123 when none) → click result → "Add to Prompt". Verify in preview pane. Search is word/prefix-based.
- VERIFIED picker search terms: Dana face "young woman beauty" · Dana T2 "white blouse" · Dana T4 "flexing" · Dana T6+T9 "super-suit" (BOTH share title — verify size in preview: T6 amazon, T9 colossal; T9 newer = higher) · Dee-Dee face "blonde" · Dee-Dee T3 "lab coat" · Dee-Dee T8 "standing villain" · Supraman "male superhero" · Doomer "bald man" · hq-gym "training hall" · city "city avenue" · doomer-lab-2 "backup villain" · doomer-lab "underground villain" · barbell "barbell" · ray "ray cannon" · anchor "lana"
- Page exec: pages-plan.json (prompts+refs+aspect) + pages-log.json (status). Cover p1 deferred to end (hardest 3-char composite).

## Page progress
- **RATE LIMIT**: firing ~5-6 batches concurrently triggers "requesting generations too quickly" (whole batch fails, no uuid). FIX: process ONE page at a time — fire → wait ~75s for completion → harvest 4 newest uuids → pick best → download → log → next. ~1-2 in flight max.
- Fired p2-p5 (look great), p6 re-firing after rate-limit recovery, p7 failed (re-fire pending).
- p2 lab-establish ✓, p3 Supraman wall-smash ✓, p4 ray-shield ✓, p5 kneeling-drained ✓ (all in gallery, not yet downloaded).
0 / 46 downloaded

## Notes / blockers
- none yet
