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

Quick check after a deploy (run against the freshly-read on-disk file):
`grep -c 'ck_ai_polish\|polish_one\|ck_lineage\|b-adjust\|ck_ai_breakdown\|shotdone\|ck_letter_block\|pagestage\|review.php?p=' creator.php`
— expect hits for every group; a zero means something got clobbered.
Also: `grep -c 'ck_letter_block\|LETTER_SPEC_DEFAULT\|STAGE_OPTS\|ck_stage_eligible' inc/boot.php` (expect 4+) if you redeploy boot.php.
**And** (since 2026-10-01) `grep -c "ws_gate\|studio_lt\|workspace.php" inc/boot.php` (expect 3+): the lieutenant-workspace gate hook in `is_authed()` + the `require_once __DIR__ . '/workspace.php'` at the END of boot.php. Dropping them makes every lieutenant appear signed out (fail-closed, but the workspace stops working).

## 🧑‍✈️ Lieutenant workspace (2026-10-01) — hired helpers, magic links, brand-scoped

Files (all new, owned by this feature): `ws.php`, `ws-api.php`, `picker.php`, `team.php` (owner only), `ws-worker.php`
(worker API, own key), `inc/workspace.php` (gate, roles, brands, quotas, stores). Data: `data/ws/` (team.json, proj-/chat-/picks-<pid>.json,
jobs.json, usage.json, worker.json = keyHash only, worker-seen.json).

| Where | Markers (grep these) | Why it matters |
|---|---|---|
| inc/boot.php | `studio_lt` + `ws_gate()` inside `is_authed()`; `require_once __DIR__ . '/workspace.php'` as the LAST line | Lieutenant sessions carry `studio_lt`, never `studio_ok`. The hook is the ONLY thing that lets them in, and `ws_gate()` confines them to ws.php / ws-api.php / picker.php / img.php / help.php / login.php for their brand's comics. |
| inc/boot.php `store_image()` | `$keep = function` (rename/copy for non-uploaded temp files) | The worker's `ingest_url` stores server-side downloads; `move_uploaded_file` alone would drop them. |
| index.php | `ws_is_owner()` → 🧑‍✈️ Workspace + 👥 Team links | Owner-only links in the topbar. |
| index.php (2026-10-02) | `master Studio key: owner only` wrapping the ⚙ Flow import `<details>` | The bridge key is shown to the OWNER only (staff like THOR + collab logins don't see it). |
| inc/boot.php + inc/workspace.php (2026-10-02) | `ws_staff_gate()` called from the `studio_ok` branch of `is_authed()`; `WS_OWNER_ONLY` (= finance.php) | finance.php is owner-only for every login, so it can't be claimed by staff. |
| img.php (2026-10-02) | `m=1` viewing copy (`uploads/<id>/mid/<name>.jpg`) + PNG thumb JPEG twin (`mid/<name>.t.jpg`); `max-age=2592000, immutable` | Picker lightbox loads ~6× lighter images and shows the thumbnail instantly; project.php delete also clears `mid/`. |
| creator.php / project.php | `JSON_HEX_TAG \| JSON_HEX_AMP` on the `window.STUDIO_ANALYSIS = …` line | Lieutenant uploads feed image analysis text; without HEX_TAG a `</script>` in a caption breaks out on owner pages. Keep the flags if you touch that line. |

Rules: a lieutenant must never get studio_ok, never be added to admin users.json or users-studio.json, and never reach
publish/port/posting/finance. The opsbox job `ws-worker` (orchestrator ops/opsbox/jobs/ws-worker.*) is the only generator for this queue;
its PreToolUse hook (`ops/opsbox/ws/ws_hook.py`) is what bounds Higgsfield spend. Plan + decisions: claude-comic-pipeline
`studio/docs/LIEUTENANT-WORKSPACE.md`. Tests: `node studio/tests/ws/run.mjs` (PHP-wasm, 374 checks) — never deploy `studio/tests/` or `studio/worker/`.

## 🔒 Locked writes in the legacy pages (2026-10-01) — never reintroduce `images_save()` / `projects_save()`

The workspace, the worker and the legacy pages all write `data/images-<pid>.json`, `data/projects.json` and
`data/creator-<pid>.json`. Every write is a LOCKED read-modify-write: the file is read INSIDE `s_with_lock()` /
`images_update()`, never earlier in the request. Wrapping only the save in a lock does NOT fix lost updates.
Redeploying a page from a pre-2026-10-01 copy brings the races back (silently erased picks, ratings, ingests, projects).

| Where | Markers (grep these) | Rule |
|---|---|---|
| api.php | `api_image_edit` `api_project_patch` | no `images_save(` / `projects_save(` anywhere |
| bridge.php | `s_with_lock(imeta_path($pid)` (ingest: lineage + auto-group + append in one pass) | same |
| creator.php | `ck_cfg_commit` `ck_cfg_merge3` (`$c0` = what the request read) | creator-<id>.json is saved ONLY via `ck_cfg_commit($cfile, $c0, $c)`, never `s_write($cfile, …)` |
| index.php, project.php, gribble.php, growgetter.php | `s_with_lock(PROJECTS_FILE` | project ids are picked inside the lock |
| port.php | `images_update($id` | the `ported_to` stamp |

Quick check: `grep -n "images_save(\|projects_save(\|s_write(\$cfile" studio/*.php` must print nothing.
Never nest these locks (slow work such as `store_image()`, hashing and AI calls stays outside them; picks → images
and jobs → usage are the only allowed nestings). Tests: `node studio/tests/locks/run.mjs` (73 checks).

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

## posting.php / schedule.php (the release board) — markers to keep
_Added 2026-08-23 by the posting-board refresh._

Both pages read and write the SAME store, `studio/data/posting.json`. It went from
425 items (415 of them in the past, 2 in the future) to 606, and now carries a real
forward schedule. Two view fixes went out with that data — both were latent bugs
that were invisible only while the forward lanes were empty:

| feature | file | markers (grep) |
|---|---|---|
| Runway measured as a HORIZON, not consecutive weeks | schedule.php | `CK-RUNWAY-HORIZON` `runwayCls(` `rw.slots` |
| Weekly-serial section bounded to the near horizon | posting.php | `CK-WEEKLY-WINDOW` `$weeklyHorizon` `$weeklyLater` |

**Why they matter.** `runway()` v1 counted consecutive covered weeks and stopped at
the first empty one. That only ever worked for Fan Art Friday: for a monthly comic
lane the gap between slots IS the cadence, so the moment real monthly and bi-weekly
slots existed, 7 of the 9 lanes rendered "dry now" in red while booked into 2027.
v2 measures weeks out to the last non-missed future slot and carries the slot count
alongside. Thresholds live in `runwayCls` so the top strip and the row chips cannot
drift apart — change them in one place.

The Weekly serial section on posting.php took every open `weekly` item with no date
filter (unlike the FAF and Monthly sections, which window to 4 Fridays / 2 months).
With 24 bi-weekly slots booked it would have put two dozen cards on a page whose job
is "what fires this week". It now hides only what is beyond `$weeklyHorizon` (+28d)
and prints a count linking to schedule.php. **Undated and OVERDUE cards are kept on
purpose** — an open slot whose date has passed must stay visible until someone closes
it. Do not "simplify" that into a plain future-window filter.

**Store conventions introduced.** Rows carry a `source` tag: `sheet-import` /
`sheet-backlog` (the owner's Google Sheet), `evidence-backfill-2026-08-23`
(reconstructed from what actually published), `cadence-seed-2026-08-23` (recurring
forward slots). The seeds are safe to bulk-delete by that tag if the cadence changes.
Every reconciled row carries its evidence (URL + channel + date) in `notes`.
`giantessgirl` is archived in both views (transferred away 2026-07-25) and is never
a target for new scheduling — do not "fix" its empty forward lanes.
