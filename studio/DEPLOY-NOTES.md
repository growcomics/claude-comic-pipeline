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
