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

Quick check after a deploy (run against the freshly-read on-disk file):
`grep -c 'ck_ai_polish\|polish_one\|ck_lineage\|b-adjust\|ck_ai_breakdown\|shotdone\|ck_letter_block' creator.php`
— expect hits for every group; a zero means something got clobbered.
Also: `grep -c 'ck_letter_block\|LETTER_SPEC_DEFAULT' inc/boot.php` (expect 2+) if you redeploy boot.php.

## If you DID clobber a feature whose source you don't have

Reconstruct it from its caller's contract. Example: the polish endpoints were
restored from the live `shots.php` (which POSTs `do=polish_one{panel}->{ok,polished}`
and `do=polishedit{panel,text}`). The merged live file then has everything.

_Last updated: 2026-06-27 — added the per-project Lettering spec (`ck_letter_block` in inc/boot.php; `do=lettering` + polish append in creator.php; lettering card + style sheet in shots.php)._
