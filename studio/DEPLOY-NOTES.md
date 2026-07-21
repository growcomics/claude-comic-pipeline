# ⚠️ STUDIO DEPLOY COORDINATION — read before deploying any studio/*.php

Multiple Claude Code sessions edit + deploy the **live** Comic Studio
(`3dmusclecomics.com/studio/`) via the cPanel `Fileman/save_file_content` API.
That call **replaces the whole file** — there is NO merge. If you deploy a
`creator.php` built from a stale base, you **silently wipe every feature another
session added after your last fetch**. This has happened (2026-06-25).

`creator.php` is one ~94KB file holding MANY independently-built features. Treat
it as shared, append-only-in-spirit code.

## Deploy protocol (do this every time)

1. **Fetch-live immediately before editing** — pull the current
   `/home/dmusclecomics/public_html/studio/creator.php` (and `shots.php`, etc.)
   via `Fileman/get_file_content` and edit THAT exact copy. Do not reuse a mirror
   from earlier in the session.
2. **After deploying, re-read the on-disk file and grep for ALL feature markers
   below** — not just your own. If any are missing, you clobbered that feature;
   restore it before continuing.
3. **Live server = source of truth.** The git repo's `studio/` copy is stale —
   do not reconcile through it.

## Feature-marker checklist (all must survive every creator.php deploy)

| Feature | Markers (grep these) | Owner notes |
|---|---|---|
| Refs panel / bulk upload / AI sort | `ck_ai_classify` `aisort_one` `do === 'addref'` `do === 'uploadref'` `do === 'editgroup'` | refs.php is the workspace |
| Script → shotlist breakdown | `ck_ai_breakdown` `do === 'breakdown'` | claude-sonnet-4-6 |
| Production guide | `do === 'shotdone'` `do === 'style'` | shots.php renders it |
| ✨ Prompt-polish | `ck_ai_polish` `do === 'polish_one'` `do === 'polishedit'` | shots.php calls these |
| ✎ Iterative refinement / lineage | `ck_lineage` `ck_order_lineage` `ck_adjust_prompt` `do === 'adjust'` `do === 'adjustresult'` `do === 'adjustcancel'` `b-adjust` | bridge.php also has a `do=ingest` lineage passthrough (`parent`/`adjust`) — see studio/docs/ITERATIVE-REFINEMENT.md |
| 💬 Notes log (collapsible) | `class="ck-notes"` `notesOpen` `ck-note-badge` `id="notescopy"` | feedback HISTORY moved OUT of the run bar into a collapsed `<details>` (panel vs system badges + filter + 📋 Copy all). The `do === 'feedback'` handler + per-panel 💬 targeting (`act === 'note'`, `#fbtext`/`#fbpanel`) are UNCHANGED — don't revert the inline `.ck-fblog` list. |
| 💬 Lettering spec | creator.php: `do === 'lettering'` `ck_letter_block` + the cockpit `💬` display row; **inc/boot.php**: `ck_letter_block()` + `LETTER_SPEC_DEFAULT`; shots.php: `name="lettering"` card + `id="sheetsvg"` style sheet | Per-project speech-balloon/caption house style. The HELPER lives in `inc/boot.php` (shared by shots.php's template + creator.php's polish append) — if you deploy boot.php, keep `ck_letter_block`/`LETTER_SPEC_DEFAULT`. Appended ONLY to panels with non-empty `dialogue` (the block also carries the exact line). shots.php's `shot_prompt()` now takes a 3rd `$lettering` arg. |
| 🎚 Stage-aware refs | **inc/boot.php**: `STAGE_OPTS` + `ck_stage_norm`/`ck_stage_key`/`ck_stage_label`/`ck_stage_eligible`; creator.php: `do === 'pagestage'` + `ck_stage_key(` on addref/uploadref/editref/editgroup + `'stage'` in `ck_ai_breakdown` schema; refs.php: `STAGE_OPTS` + `rf-substage`; shots.php: `ck_stage_eligible` + `stage_gaps` + `do=pagestage` page-header select | Per-character progression stage (pre/mid/post or tier-1..5; `''`=stage-agnostic) on each REF, plus a per-PAGE `stage` on `$c['plan']`. `match_chars($names,$charRefs,$stage)` now takes a 3rd arg and filters via `ck_stage_eligible` so an early "pre" panel never pulls a "post" body. The 4 stage helpers live in **inc/boot.php** (shared by shots.php + the future worker) — if you deploy boot.php, keep them alongside `ck_letter_block`/`LETTER_SPEC_DEFAULT`. Different axis from the project pipeline stage `$c['stage']` (STAGES) — don't merge them. |
| 🖼 Review surface | creator.php: a single `review.php?p=` link in the Live-panels header (low-stakes — re-add if clobbered); **studio/review.php** (standalone, own file, low clobber risk); **bridge.php**: `ck_parse_refs_used` + `prompt`/`refs_used` stored in the `ingest` verb + the new `do=enrich` verb | Full-width, story-ordered, sortable review grid + per-panel DETAIL (prompt + refs-used + notes + rating). `review.php` is a pure renderer (like refs.php/shots.php): reuses `api.php` winner/rate/keep, has its own `do=note` JSON handler (annotation only — NO reshoot enqueue, unlike the cockpit's per-panel 💬). Prompt + `refs_used` are captured at ingest (bridge.php) and by the Flow auto-sync extension (`~/Documents/flow-studio-autosync`, v1.1.0 — sends `refs_used` + an `enrich` backfill batch). Legacy panels (no prompt) show an honest "not recorded" state until a re-sync backfills via `do=enrich` (fills MISSING fields only, unless `force=1`). |
| 🔎 QA defect scan | creator.php: `ck_qa_checklist`/`ck_qa_cast`/`ck_qa_match`/`ck_ai_qa` + `do === 'qascan_one'` + cockpit `an-tag` badge (`an-tag v-`/`data-defects`) + `ck-qabar` toolbar (`qascanbtn`) + `qa-hide` filter + `ck-lb-an` lightbox + `STUDIO_ANALYSIS`; **bridge.php**: `verdict`/`people`/`src` keys in the `annotate` analysis array | AI QA pass that auto-flags generation DEFECTS on panels — PRIORITY: **duplicate characters / unwanted extras** (owner Beat 48). One vision call/panel (reuses `ck_ai_classify` pattern + `data/ai.json` key); `qascan_one` writes the image `analysis` field race-safe via `s_with_lock(imeta_path)`. Same `analysis` shape as `annotate`, so it lights the organizer badge AND can feed review.php's flagged filter. KEEP `ck_ai_qa`/`qascan_one`/`ck-qabar`/`qa-hide` on any creator.php deploy. |

| 📈 Patron Analytics (Creator Pulse) | **cc.php**: the `href="pulse/"` tile in the Work grid + the `📈 Analytics` topbar link; **studio/pulse/** (own directory — low clobber risk): `index.php` auth shell + `css/style.css` + `js/data.js` + `js/app.js` | Deployed 2026-07-06. Source app lives at `~/Documents/creator-pulse`; deploy ONLY via its `tools/deploy_3dmc.sh` (regenerates `pulse/index.php` from `index.html` — never hand-edit the PHP; it joins the session with cookie path `/studio` and redirects anon → `../login.php`). If you redeploy cc.php, KEEP the `pulse/` tile + topbar link. Do NOT upload `data/*.json` (synced real Patreon revenue) into `pulse/` — static JSON there is publicly fetchable; an auth-gated passthrough must exist first. |

| 🎲 GrowGetter generator | **studio/growgetter.php** (standalone, own file — low clobber risk): `gg_premise` `gg_create` `gg_refplan` `gg_qa` `gg_images` `GG_FORMULA` `GG_SFW_RULES`; **index.php**: the `growgetter.php` button in the top button row | One-click random GrowGetter-style comic, ALWAYS SFW: seeded AI premise+script → project (tags growgetter/sfw) → browser calls creator.php `do=breakdown` → AI reference plan (face cards + stage-aware pre/mid/post bodies + env plates, SFW-locked prompts) stored as `$c['refplan']` + enqueued as a `kind=refs` worker job → per-image SFW QA (`gg_qa`, writes the same `analysis` shape as `qascan_one`, src=`ggqa`). JSON verbs accept the BRIDGE KEY (data/bridge.json) as an alternative to session auth (key skips CSRF, same trust as bridge.php) so headless sessions/workers can drive it. If you redeploy index.php, KEEP the `growgetter.php` link. ALSO: bridge.php `do=ingest` now honors `accepted=0|1` POST + a per-project `autoApprove` creator-config flag (gg_create sets it) — panels land APPROVED (veto-only review, owner ask 2026-07-04); keep the `$acc` block in ingest. |

Quick check after a deploy (run against the freshly-read on-disk file):
`grep -c 'ck_ai_polish\|polish_one\|ck_lineage\|b-adjust\|ck_ai_breakdown\|shotdone\|ck_letter_block\|pagestage\|review.php?p=' creator.php`
— expect hits for every group; a zero means something got clobbered.
Also: `grep -c 'ck_letter_block\|LETTER_SPEC_DEFAULT\|STAGE_OPTS\|ck_stage_eligible' inc/boot.php` (expect 4+) if you redeploy boot.php.

## If you DID clobber a feature whose source you don't have

Reconstruct it from its caller's contract. Example: the polish endpoints were
restored from the live `shots.php` (which POSTs `do=polish_one{panel}->{ok,polished}`
and `do=polishedit{panel,text}`). The merged live file then has everything.

_Last updated: 2026-06-27 — added the per-project Lettering spec (`ck_letter_block` in inc/boot.php; `do=lettering` + polish append in creator.php; lettering card + style sheet in shots.php)._
_Also 2026-06-27 — added **Stage-aware references** (character progression pre/mid/post/tiers): 4 `ck_stage_*` helpers + `STAGE_OPTS` in inc/boot.php; `stage` on refs (addref/uploadref/editref/editgroup) + `do=pagestage` + page-stage in `ck_ai_breakdown` in creator.php; stage UI (sub-grouped by stage) in refs.php; stage-aware `match_chars`/`stage_gaps` + per-page stage select in shots.php. Resolution verified on-server (early "pre" panel excludes the post/muscular body)._
_Also 2026-06-27 — added the **🖼 Review surface** (`studio/review.php`): full-width, story-ordered, sortable review grid + per-panel detail (prompt + refs-used + notes + rating). New standalone file (low clobber risk); the only creator.php touch is one `review.php?p=` link in the Live-panels header. bridge.php gained `ck_parse_refs_used` + `prompt`/`refs_used` capture in `ingest` + a `do=enrich` backfill verb (matched by gen/genkey/file, fills MISSING fields only unless `force=1`). The Flow auto-sync extension (v1.1.0) now sends `refs_used` (Flow input refs) + an enrich batch. Verified on-server: ingest stores prompt+refs_used, enrich no-clobber/force both correct (throwaway project, then removed); review.php renders 98 muller panels with embedded JSON parsing clean; adversarially reviewed XSS/CSRF/traversal → GO._
_Also 2026-06-27 — added the **🔎 QA defect scan** (auto-flags generation defects, esp. **DUPLICATE characters / unwanted EXTRAS** — owner Beat 48). creator.php: `ck_qa_checklist`/`ck_qa_cast`/`ck_qa_match`/`ck_ai_qa` (vision call, reuses the `ck_ai_classify` + `ai.json` pattern) + `do === 'qascan_one'` (JSON per-panel, race-safe `s_with_lock(imeta_path)`) + cockpit `an-tag` defect badge / `ck-qabar` "🔎 QA scan" + "↻ rescan all" toolbar / `qa-hide` flagged-only filter / `ck-lb-an` lightbox analysis / `STUDIO_ANALYSIS`. bridge.php `annotate` now also stores `verdict`/`people`/`src` (same shape). Writes the image `analysis` field → feeds the organizer badge AND review.php's flagged filter (coordinate: QA writes, review.php renders). If you redeploy creator.php, KEEP `ck_ai_qa`/`qascan_one`/`ck-qabar`/`qa-hide`. Verified on-server: real panel→pass; synthetic duplicate→"DUPLICATE CHARACTER" high/fail; key never echoed; defect text h()/escapeHtml-escaped → GO._

## review.php (full-width Review surface) — now MULTI-SESSION, same as creator.php
`studio/review.php` is being edited by more than one session (image-zoom + URL-hash view-state from one; defect-scan + keyboard-triage + bulk-actions + reference-thumbnails from another). Treat it like creator.php: **fetch-live immediately before editing, and after deploy grep for ALL these markers.** A whole-file save with a stale base WILL wipe the other session's additions (observed 2026-06-28 — toolbar HTML got clobbered repeatedly).

| review.php feature | markers (grep) |
|---|---|
| Sorts/filters/detail (prompt+refs) | `class="rv-grid"` `detaildata` `rv-tile` |
| Image zoom + URL-hash view state + next-unrated | `zoomed` `writeHash` `readHash` `stepUnrated` |
| AI defect scan + keyboard triage + bulk + ref thumbnails | `id="scanbtn"` `id="approveshown"` `id="delrejects"` `function visTiles` `qascan_one` `rv-kbhint` `.rv-act{` `data-aion` |

bridge.php also gained `do=ingest_refcache` (caches a refs_used image as a studio thumbnail; deduped by `refkey`) alongside `do=enrich` + the `ingest` prompt/refs_used capture + the sibling's `adjustResolved` idempotency — keep ALL of them. api.php gained `action === 'bulk'`; export.php gained `?only=approved` + isref exclusion.

## ⌘ Command Center (added 2026-07-06) — cc.php / ops.php / ops-api.php / site.php / inc/ops.php + login.php edit

The Monday.com replacement: ops board (one-time import of the owner's Monday "Operations"
export — 372 tasks + 511 update threads), Command Center landing, per-site overview pages.
All NEW standalone files except **login.php**, which gained the studio-only collaborator
login fallback (Magnamus). Data: `data/ops-tasks.json`, `data/ops-updates.json`,
`data/cc-sites.json`, `data/users-studio.json` (all under the data/ `.htaccess` deny).
Local importer: `tools/monday-import.py` (not deployed).

| File | Markers (grep) | Notes |
|---|---|---|
| inc/ops.php | `OPS_GROUPS` `OPS_TASKS_FILE` `ops_open` | shared constants/wrappers; deliberately NOT in inc/boot.php so boot.php never redeploys for CC work |
| ops-api.php | `action === 'bulk'` `action === 'note'` `ops_clean_patch` `sitelinks` | all task writes via `s_with_lock(OPS_TASKS_FILE)`; update threads in a SEPARATE file (`OPS_UPDATES_FILE`) so note-adds never contend with status flips |
| ops.php | `const OPS =` `dwWrap` `writeHash` `bulkBar` `quickAdd` | pure renderer; threads lazy-fetched (`action=updates`); `ops.php#task=<id>` deep links; `#ai=ai-now` etc. shareable filters |
| cc.php | `cc-tile` `Cross-property` `Coming next` | open counts computed in one PHP pass; grayed v2 tiles (calendar/analytics/SOPs) |
| site.php | `sp-links` `sitenote` `editLinks` | `?s=<key>` against cc-sites.json; bad key → cc.php redirect |
| **login.php** | `studio_login_local` `users-studio.json` | ⚠ now a SHARED EDITED file — fetch-live before touching; the fallback must survive any redeploy. Magnamus is NOT in admin/data/users.json (main-site admin) by design. |

Known/accepted: index.php still shows the bridge key to ANY studio session, including
collaborator logins — acceptable for a trusted collaborator (owner decision 2026-07-06).

**🧭 Attribution section (added 2026-07-09).** New standalone `attribution.php` — cross-property
MULTI-TOUCH attribution fed by the **ATS v5 WordPress plugin** (live on growgettercomics.com since
2026-07-09; plugin source: `~/Documents/ats-v5/plugin/attribution-tracking-system-v5/`). Each WP
property exposes key-gated `/wp-json/ats/v1/rollup` (aggregates only, NO PII); `attribution.php?do=sync`
(session-auth POST or BRIDGE-KEY GET, same trust as bridge.php) pulls every site in
`data/attribution-sites.json` (SECRET — holds rollup keys; data/ deny; NOT in git) into
`data/attribution/<site>.json`. Markers: attribution.php `do=sync` `attr_bridge_ok` `MODELS =`
`at-card` `Patron journeys`; **cc.php now ALSO carries** the `🧭 Attribution` tile + topbar link +
`$atMonthly`/`glob(SDATA . '/attribution/*.json')` headline read. ⚠ cc.php fetch-live grep after ANY
redeploy: `pulse/` (≥4), `Patron Analytics` (2), `analytics.php` (2), `Site Traffic` (1),
`attribution.php` (≥3), `🧭 Attribution` (≥2). DISTINCT from analytics.php (GA4 snapshots) and
pulse/ (Patreon revenue): attribution answers "which channel produced the money".

**📊 Site Traffic analytics section (added 2026-07-07).** New standalone `analytics.php`
(GA4 + Search Console web-traffic snapshots + INSIGHTS/ACTIONS) reading `data/analytics-snapshots.json`.
DISTINCT from `pulse/` (Creator Pulse = Patreon revenue). Markers: analytics.php `Insights &amp; actions`
`class="ins"` `analytics-snapshots`; data file `analytics-snapshots.json` (data/ deny — not web-readable).
⚠ **cc.php is now SHARED between this session and the Creator-Pulse session** — it carries BOTH the
`pulse/` "Patron Analytics" tile+link AND my `analytics.php` "Site Traffic" tile+link (`$anSess`/`$anMonth`
read of the snapshots file). Fetch-live before editing cc.php and after deploy grep: `pulse/` (≥4),
`Patron Analytics` (2), `analytics.php` (2), `Site Traffic` (1). Snapshots are appended by Claude during
an analytics session (needs the owner's live Google login — not headless).

**🏴 Defect flags + shared defect log (added 2026-07-18).** The owner-feedback loop's data
layer (design: pipeline repo `docs/DEFECT-FEEDBACK-LOOP.md`; taxonomy: `DEFECT-REGISTRY.md` —
registry IDs like `CAST-01`/`duplicate_character` are the SHARED CONTRACT between the 🔎 QA
scan, gg_qa, bridge writers and human 🏴 flags). New: **inc/defect-taxonomy.php** (GENERATED
from the pipeline repo's `defect-registry.json` by `gen_defect_taxonomy.py` — never hand-edit;
marker `DEFECT_TAXONOMY`) + **inc/defects.php** (`ck_defect_event` `ck_defect_norm`
`ck_defect_log_analysis` `ck_defect_options` `DEFECT_LOG_FILE`) + **data/defect-log.json**
(append-only event log, newest-20k cap, under the data/ deny). Every flag/scan defect writes
one event {ts,project,file,panel,defect,slug,sev,src:human|qa|ggqa|gate,by,note,verdict}.

| File | New markers (grep after ANY redeploy) | What was added |
|---|---|---|
| creator.php | `flag_defect` (≥4) `ck-flagrow`/`ckflag` (≥3) `showFlagRow` (≥3) `ck_defect_log_analysis` (1) `'typed'` (2) `inc/defects.php` (1) | `do=flag_defect` JSON handler (image `flags[]` + log event); 🏴 lightbox row (grouped registry picker + note); `qascan_one` now also appends log events; `ck_ai_qa` returns `typed[]` alongside the flat labels |
| review.php | `flag_defect` (≥3) `submitFlag` (≥2) `DEFECT_OPTIONS` (≥2) | own `do=flag_defect` endpoint (same contract); 🏴 Flag-a-defect section in the detail pane (buildInfo) |
| bridge.php | `do === 'flag'` (1) `ck_defect_log_analysis` (1) `ck_defect_event` (1) | key-gated headless flag verb (accepts id OR slug; `src` defaults `gate`); `annotate` now logs events too |
| growgetter.php | `ck_defect_log_analysis` (1) `typed` (≥2) | `gg_qa` logs events (src `ggqa`; its `nsfw` type → WARD-06) |

Verified live 2026-07-18: parse-probes 302/403 on all four; ALL pre-existing marker tables
intact after deploy (byte-identical fetch-backs); bridge `do=flag` roundtrip — canonical id,
slug lookup, invalid-id rejection, panel resolution, image `flags[]` + log event — then
self-test data removed. If you redeploy creator.php/review.php/bridge.php/growgetter.php,
KEEP all of the above, and remember inc/defect-taxonomy.php regenerates from the repo.

**🔎 Auto-scan + headless qascan (added 2026-07-18, same day as 🏴).** The QA-scan ENGINE
(`ck_ai_cfg` + `ck_qa_checklist`/`ck_qa_cast`/`ck_qa_match`/`ck_ai_qa`) **moved from
creator.php into inc/defects.php** (inside a `function_exists('ck_ai_qa')` guard for
rolling-deploy safety) so bridge.php's new key-gated **`do=qascan`** verb runs the exact
same scan headlessly (writes `analysis` + defect-log events; used for fleet sweeps).
creator.php keeps a pointer comment; do NOT re-add local copies. Both UIs now **AUTO-SCAN
on open**: unscanned panels kick the existing scan automatically, **capped at 120 unscanned**
(bulk archives like muller's 9k raw Flow gens stay manual — above the cap a hint shows
instead). review.php's DATA gained a `scanned` flag; its scan loop refactored into
`scanFiles(files)` (button = shown tiles, auto = unscanned only).

| File | Markers (grep after ANY redeploy) |
|---|---|
| inc/defects.php | `function_exists('ck_ai_qa')` `ck_ai_cfg` `ck_qa_checklist` `ck_qa_cast` `ck_qa_match` `ck_ai_qa` (engine lives HERE now) |
| creator.php | `MOVED to inc/defects.php` (2: pointer comments) `AUTO-SCAN on open` `autoUnN` — and NO local `function ck_qa_*`/`function ck_ai_cfg` definitions (re-adding them fatals against the include's guard-free future) |
| bridge.php | `do === 'qascan'` (1) |
| review.php | `scanFiles` `'scanned'` `AUTO-SCAN on open` |

Verified live 2026-07-18: parse probes on creator/review/bridge/growgetter/refs/shots;
full marker sweep (pre-existing + 🏴 + these) clean; bridge `do=qascan` real-scan roundtrip
(2.4s, analysis + verdict + log event). Production-wide sweep run via `do=qascan`
(all projects except the muller raw archive — owner-scoped 2026-07-18).

_Also 2026-07-20 — added the **⭐ Flow-favorite pick loop**: bridge.php `do=flowfav` (additive, idempotent pick marker: +tag `flow-fav`, `unrated→good`, `accepted` only when the beat has no owner-kept winner — owner's manual rating ALWAYS wins) + `addtags` (additive tag merge) in `do=write`; review.php `flowfav` in the detail payload + `data-flowfav` + `.rv-flag.fav` ⭐ tile badge + `togfav` "⭐ Flow favs" toolbar filter (state/hash key `flowfav`) + `.rv-chip.fav` detail chip; creator.php `$isFav`/`.ck-favbadge` ⭐ board badge. Fed by flow-studio-autosync v1.2.0 (posts favorited workflow ids each sync; favorites live on Flow's `projectContents.workflows[].metadata.favorited`, wf name = the bridge `gen` id). KEEP markers on redeploy: bridge `do === 'flowfav'`/`addtags`; review `togfav`/`flowfav`/`rv-flag fav`; creator `ck-favbadge`._
