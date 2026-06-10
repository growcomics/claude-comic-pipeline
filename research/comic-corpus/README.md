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
- `schema/beats.schema.json` — machine schema for per-comic `beats.json`
- `scripts/` — `ingest.py`, `corpus_stats.py`
- `_queue.md` — dump links/paths here
- `corpus/<slug>/` — per comic: `pages/` (**gitignored** — third-party copyrighted), `meta.json`, `beats.json`, `notes.md`
- `synthesis/success-elements.md` — cross-corpus digest

## Copyright

Raw pages under `corpus/*/pages/` are **gitignored and never committed or pushed**. Only the analysis (beats/notes/meta) and synthesis are versioned. The analysis is transformative commentary for production R&D.

## Current corpus

3 comics / 85 pages — *The Mysterious Book* Ch.1–3 (GrowGetter Comics). Corpus growth-page ratio 55%. See `synthesis/success-elements.md`.
