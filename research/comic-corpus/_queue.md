# Ingest queue

Dump comic sources here — one per line, web URL or local path. Then run the
`comic-corpus` skill to drain the queue: ingest → analyze → synthesize.

Lines starting with `#` are comments. Lines starting with `- [x]` are done.

## Pending

(empty — add links/paths below)

## Done

- [x] https://growgettercomics.com/the-mysterious-book-the-opening-2/   → the-mysterious-book-1-the-opening (25pp)
- [x] https://growgettercomics.com/the-mysterious-book-2-the-beatdown/  → the-mysterious-book-2-the-beatdown (29pp)
- [x] https://growgettercomics.com/the-mysterious-book-3-ascension-2/   → the-mysterious-book-3-ascension (31pp)
- [x] https://growgettercomics.com/ultragal-issue-2-dominas-deception-2/ → ultragal-2-dominas-deception (22pp)
- [x] https://growgettercomics.com/ass-effect/                          → ass-effect (23pp)
- [x] https://growgettercomics.com/worst-to-first-4-colored/            → worst-to-first-4 (18pp)
- [x] https://growgettercomics.com/the-curse-2-curse-control-2/         → the-curse-2-curse-control (22pp)
- [x] https://growgettercomics.com/muller-issue-1/                      → muller-1 (20pp)
- [x] https://growgettercomics.com/breaker-part-1-2/                    → breaker-1 (19pp)

## Catalog (GrowGetter, 1088 posts — not yet ingested; full readable comics found in survey)

Available full comics (≥15pp) for future runs: angela-issue-1 (75pp, naturalman), nami (24pp), the-magic-cloak-5-betrayal-2 (21pp), superior-part_1 (15pp). Teasers/partial (skip): rivalry, crystal-peaks, seven-idols, mary-sue-part-2. NOTE: next expansion should target a DIFFERENT studio/artist than Boogie to separate genre norm from house style.

## Premium / authenticated catalog  (B2 — BLOCKED on user login; Claude must NOT log in)

The 9 comics above were pulled from PUBLIC chapter pages via the cookieless
`ingest.py --web` path. **Premium content needs the authenticated session** — and the
auth constraint is non-negotiable: **the USER** creates the account, grants their own
premium, and logs in to the driven Chrome profile; **Claude never creates an account
or enters a password.** Once the user confirms they're logged in, ingest premium-visible
comics by **reading the authenticated session via the Chrome MCP** (the blob-fetch
pattern in `SKILL.md` Phase 1 / `feedback_flow_bulk_download_blob.md`) — NOT the
cookieless urllib path (it can't see premium pages).

Priority once the session is live (corpus's #1 open question — separate genre law from
Boogie's house style → target a DIFFERENT artist):
- [ ] angela-issue-1 (75pp, **naturalman** — different artist ✓)
- [ ] nami (24pp)
- [ ] the-magic-cloak-5-betrayal-2 (21pp)
- [ ] superior-part_1 (15pp)
- [ ] premium-only titles — TBD once the authenticated catalog is visible

## Scripts (B1 — the user's own story scripts)

Not URLs — drop script files in `scripts-raw/` and run `scripts/ingest_script.py`
(see `scripts-raw/README.md`). Tracked separately from this URL queue.
