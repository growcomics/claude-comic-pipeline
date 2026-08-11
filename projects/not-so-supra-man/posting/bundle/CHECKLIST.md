# Publish checklist — Not So Supra... Man

**Property:** GrowGetter · **Pages:** 46 (override:/Users/mattmenashe/Documents/claude-comic-pipeline/projects/not-so-supra-man/pages/lettered) · **Prepared:** 2026-08-11 · bundle v1

> 🖐 **Every checkbox below is a HUMAN action.** Nothing in this bundle has posted, uploaded,
> or deployed anything. The pipeline prepares; you publish. (Per the never-post rule and
> PRODUCTION-SYSTEM-VISION §5 — publish stays human-fired even in Run mode.)

Platform order = canonical home first (everything links to it), then money, then reach:
site → patreon → deviantart → twitter → instagram — matching the posting.php chips.

## 0 · Preflight
- [ ] QA report reviewed and re-render decisions made (`/Users/mattmenashe/Documents/claude-comic-pipeline/projects/not-so-supra-man/qa-report.md` — open findings are the owner's call, none block the path)
- [ ] Final pages verified: 46/46 files in `/Users/mattmenashe/Documents/claude-comic-pipeline/projects/not-so-supra-man/pages/lettered`
- [ ] Compiled PDF present: not-so-supra-man.pdf
- [ ] Captions reviewed — every `[FILL-*]` slot in `captions/` resolved, no placeholder text left
- [ ] Board item exists on the 🗓 posting board (https://3dmusclecomics.com/studio/posting.php), lane = Monthly comic / GrowGetter

## 1 · Site — the canonical home (do this FIRST; steps 2-5 link to it)
- [ ] Follow `site-apply-notes.md` end to end (comic-platform path)
- [ ] Verify block: every line PASS (do not announce anywhere until it does)
- [ ] Paid gating confirmed (`uploading: 0 pages` for a paid comic — runbook step 2)
- [ ] **Record the live URL:** ____________________
- [ ] posting.php chip `site` → posted

## 2 · Patreon — paying members first (https://www.patreon.com/growgetter)
- [ ] New post from `captions/patreon.md`; attach images per `crop-specs.json` → patreon
- [ ] Tier gating correct; preview as a non-patron before publish
- [ ] **Post URL:** ____________________ · chip `patreon` → posted

## 3 · DeviantArt — biggest audience (account URL in studio/data/cc-sites.json; ~15.6k watchers)
- [ ] Deviation from `captions/deviantart.md`; MATURE flag ON; tags applied
- [ ] **Deviation URL:** ____________________ · chip `deviantart` → posted

## 4 · X / Twitter (account URL in studio/data/cc-sites.json)
- [ ] Tweet from `captions/twitter.md`; media per crop-specs; sensitive flag as needed
- [ ] **Tweet URL:** ____________________ · chip `twitter` → posted

## 5 · Instagram (growgettercomics (owner IG session confirmed 2026-07-25))
- [ ] Post from `captions/instagram.md`; SFW slides only (strictest platform)
- [ ] **Post URL:** ____________________ · chip `instagram` → posted

## 6 · Aftermath — close the loop
- [ ] Fill `posted.template.json` with the real URLs/dates above and save it as
      `projects/not-so-supra-man/posting/posted.json` — **this file appearing is what marks the
      posting stage complete** to build-comic; commit it (it's project text)
- [ ] Syndication ledger (comic-platform admin `syndication.html`): one entry per post,
      WITH proof URL — after you post, never before (runbook step 6)
- [ ] What's-New: `whats-new-draft.json` → prepend to live `admin/data/updates.json`
      (only if this release touches a 3dmc surface the team should know about)
- [ ] Schedule engagement capture: +7d and +30d passes into
      `projects/not-so-supra-man/analytics/engagement-stub.json` (see skills/publisher/references/analytics-capture.md)

_Anything not applicable: set that platform's chip to n/a on the board and strike the section._
