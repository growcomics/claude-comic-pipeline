# comic-corpus

A growing, re-analyzable library of reference comics (focus: female-muscle-growth) studied to extract what makes them work — and feed those lessons back into the production pipeline.

**Dump links or files → ingest → analyze each page against a canonical rubric → synthesize patterns.** Built so a future, smarter model can re-synthesize the whole corpus over the stored analysis without re-reading a single page.

## Quick start

```bash
# from research/comic-corpus/
scripts/ingest.py --web "https://growgettercomics.com/..." --slug my-comic   # fetch a known host
scripts/ingest.py --local ~/Downloads/comic/ --slug my-comic                 # local folder / CBZ / PDF
scripts/ingest.py --list                                                     # corpus + analysis status
scripts/corpus_stats.py --corpus-root corpus                                 # roll up the numbers
```

Then run the **`comic-corpus` skill** to analyze (spawns a fresh subagent per comic) and update the synthesis. See `SKILL.md` for the full pipeline and `analysis-rubric.md` for the scoring rubric.

## Layout

- `SKILL.md` — the skill (ingest → analyze → synthesize)
- `analysis-rubric.md` — **canonical** scoring rubric (4 axes: growth density, camera dynamism, expression intensity, story); passed verbatim to analysis agents
- `schema/beats.schema.json` — machine schema for per-comic `beats.json` (rendered comics)
- `schema/script-record.schema.json` — machine schema for `script-record.json` (B1 — user scripts)
- `scripts/` — `ingest.py` (rendered comics), `ingest_script.py` (B1 — user scripts), `corpus_stats.py`; `helpers/` holds the user's accelerator scripts (B3)
- `scripts-raw/` — drop the user's SCRIPTS here (gitignored; see its README)
- `_queue.md` — dump comic links/paths here (+ the premium/authenticated B2 catalog section)
- `corpus/<slug>/` — per entry. Rendered comic: `pages/` (**gitignored**), `meta.json`, `beats.json`, `notes.md`. Script (B1): `source.txt`/`source.<ext>` (**gitignored**), `meta.json` (`record_type: script`), `script-record.json`, `notes.md`
- `synthesis/success-elements.md` — cross-corpus digest

## Feedstock sources (what the corpus ingests)

The corpus pools multiple feedstock types into one studied library the **ideator** reads (`skills/ideator/`):

1. **Rendered reference comics** — page images fetched/captured, scored on all four visual axes. `ingest.py` + an analysis subagent. (The 9 comics above.)
2. **The user's own scripts (B1)** — text story scripts normalized into `script-record.json` by `ingest_script.py` (drop them in `scripts-raw/`). Scored only on the two TEXT-assessable axes (growth density, story structure); the visual axes (camera dynamism, expression intensity) defer to storyboard/render. Reuses this rubric's vocabulary so scripts and comics pool together.
3. **Premium catalog via the authenticated session (B2)** — comics visible only to the user's logged-in premium account, read through the **Chrome MCP** (blob-fetch). **The user handles all auth; Claude never creates an account or logs in.** See `_queue.md` → Premium catalog.
4. **The user's helper scripts (B3)** — accelerator tooling (scrapers/parsers/normalizers) integrated into the ingest paths. Lives in `scripts/helpers/`.

## Copyright

Raw pages under `corpus/*/pages/` are **gitignored and never committed or pushed**. Only the analysis (beats/notes/meta) and synthesis are versioned. The analysis is transformative commentary for production R&D.

## Current corpus

9 comics / 209 pages — GrowGetter Comics (*The Mysterious Book* Ch.1–3, *Ultragal* #2, *Ass Effect*, *Worst to First* 4, *The Curse 2*, *Muller* #1, *Breaker* Pt.1). Corpus growth-page ratio 50%; ~7 of 9 drawn by Boogie. See `synthesis/success-elements.md`.
