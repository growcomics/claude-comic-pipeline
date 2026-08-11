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

## Premium / authenticated catalog  (B2 — ✅ SUPERSEDED 2026-08-10 by the WP REST API path)

**The browser-login plan below is obsolete.** GrowGetterComics is one of the user's
OWN WordPress sites with admin app-password API access via the credential wrappers
(`~/Documents/.credentials/bin/wp` — see `reference_wp_admin_credentials`). The full
catalog (1,091 posts / 27 pages / taxonomies / comment counts) is now ingested over
the REST API by **`scripts/ingest_catalog.py`** → `catalog/` (posts.jsonl,
series.json, SYNTHESIS.md with findings C1–C6). No browser session, no login, no
secrets in context — the wrapper reads the Keychain at call time. Re-run:
`scripts/ingest_catalog.py --site growgetter` (paced; ~20 requests).

What the catalog path does NOT cover: **page-image ANALYSIS** (beats.json scoring
needs the rendered pages). For full visual ingests of specific comics, `ingest.py
--web` still works on public chapter pages; gated serials strip inline images from
content, so a gated visual ingest would pull via media ids — build that only when a
specific comic is queued for full analysis.

Priority for the next FULL VISUAL ingests (corpus's #1 open question — separate
genre law from Boogie's house style → target a DIFFERENT artist):
- [ ] angela-issue-1 (75pp, **naturalman** — different artist ✓)
- [ ] nami (24pp)
- [ ] the-magic-cloak-5-betrayal-2 (21pp)
- [ ] superior-part_1 (15pp)
- [ ] premium-only titles — TBD once the authenticated catalog is visible

## Scripts (B1 — the user's own story scripts)

Not URLs — drop script files in `scripts-raw/` and run `scripts/ingest_script.py`
(see `scripts-raw/README.md`). Tracked separately from this URL queue.
