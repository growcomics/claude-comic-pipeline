# Slate archive — the tournament's dedup memory

Every `tournament.py finalize` auto-archives the finalized slate here as
`<UTC-stamp>-<seed-slug>.concepts.json`. The `brief` and `ingest` steps read
ALL slates in this directory and flag near-duplicate concepts (token-Jaccard
on title+logline: warn ≥ 0.35, fail ≥ 0.50), so the tournament never re-pitches
what a prior slate already covered.

- Committed to git — the memory must survive across sessions/machines.
- `select` keeps archived copies' `selected_concept_id` in sync (matched by
  `generated_at`).
- Deleting a file here deliberately forgets those concepts (e.g. to allow a
  theme to be re-pitched). Prefer keeping them.
