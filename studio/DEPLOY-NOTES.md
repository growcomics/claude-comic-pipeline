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
