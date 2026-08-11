# Catalog ingest log

- **Derived:** 2026-08-11T06:00:01+00:00  (re-derived from raw/ (no refetch))
- **Site:** growgetter (growgettercomics.com) via WP REST API, `wp` credential wrapper
- **Pacing:** n/a (re-derive from raw/)
- **Posts:** 1091 — kinds {'serial-page': 655, 'fan-art': 184, 'comic-chapter': 105, 'post': 101, 'pdf-bundle': 27, 'blog': 19}
- **Patreon-gated:** 861/1091
- **Pages:** 27
- **Categories:** 9 · **Tags:** 59
- **Comments sampled:** 702 (cap 3000) across 150 posts
- **Series clustered:** 625 (comic-chapter + serial-page posts only)

Raw API responses live in `raw/` (gitignored, re-derivable). Committed records
carry text + URLs/ids only — **no image binaries** (house corpus rule).
Re-fetch: `scripts/ingest_catalog.py --site growgetter` · re-derive only:
`scripts/ingest_catalog.py --summarize`.
