---
name: comic-corpus
description: Ingest popular/reference comics (especially female-muscle-growth) from web links or local files, analyze each page against a canonical rubric, and synthesize what makes them work — growth-page ratio, camera dynamism, expression intensity, story structure. Use when the user wants to "study these comics", "analyze what works in X", "ingest these links", "build a reference corpus", "take notes on these comics", "find common elements across successful comics", or dumps a batch of comic URLs/files to learn from. Produces machine-readable beats.json + human notes per comic and a cross-corpus success-elements digest that feeds back into story-writers-room, script-breakdown, and QA.
---

# Comic Corpus — learn what makes FMG comics work

Dump comic links (web) or files (local), and this builds a growing, re-analyzable library: every comic is read page-by-page, scored against `analysis-rubric.md`, and rolled into a cross-corpus synthesis of the elements that work. The point is to feed real patterns back into production instead of guessing — and to do it in a form a future, smarter model can re-synthesize over the stored corpus for free, without re-reading a page.

This is a NICHE study tool for female-muscle-growth (FMG) comics specifically. The rubric weights the things the pipeline most often fumbles: **growth density** (the niche payload), **camera dynamism** (the flatness problem), **expression intensity** (dead faces), and **story structure** (tease vs payoff).

## When this skill is the right tool

- "Study / analyze these comics" — user dumps URLs or file paths
- "What makes X comic work?" / "take notes on this"
- "Build me a corpus of FMG references"
- "Find the common elements across the successful ones"
- Any time the user wants the pipeline to *learn from* existing comics rather than generate new ones

This is distinct from `comic-folder-organizer` (organizes YOUR generated output) and `reference-gathering` (gathers visual refs for a project). This skill *studies third-party comics to extract craft lessons.*

## Hard rule — copyright

Ingested pages are third-party copyrighted material. `corpus/<slug>/pages/` is **gitignored** — raw pages NEVER get committed or pushed. Only the *analysis* (`beats.json`, `notes.md`, `meta.json`) is versioned. Never paste full pages into an external service. The analysis is transformative commentary; the raw pages stay local.

## Pipeline

### Phase 1 — Ingest

Dump sources into `_queue.md` (one per line, web URL or local path), or pass directly:

```bash
# web (known host auto-fetches; unknown host writes a skeleton for Chrome-MCP capture)
scripts/ingest.py --web "https://growgettercomics.com/the-mysterious-book-..." --slug the-mysterious-book-1

# local folder / CBZ / PDF
scripts/ingest.py --local ~/Downloads/some-comic/ --slug some-comic --title "Some Comic"

# see corpus state + analysis status
scripts/ingest.py --list
```

- **Known hosts** (currently `growgettercomics.com`): the page-image URL pattern is derived from the chapter HTML and fetched automatically.
- **Unknown hosts**: `ingest.py` writes the folder + `meta.json` skeleton; then drive the **Chrome MCP** to capture pages into `pages/` using the blob-fetch pattern (`feedback_flow_bulk_download_blob.md`) — scroll the gallery, collect media IDs, fetch each blob in-page. Logged-in/paywalled sites work this way.
- **Local files**: image folders and CBZ are copied/extracted into `pages/`; PDFs are rasterized via the `pdf` skill.

Each ingest creates `corpus/<slug>/` with `pages/` (gitignored) and `meta.json` (source, creators, popularity, ingest date).

### Phase 2 — Analyze  *(one fresh subagent per comic — never inline)*

Per `feedback_audit_via_subagent.md`, spawn a FRESH subagent for each comic's analysis — the main agent shortcuts to "looks fine." Give the subagent:
- the comic's `pages/` path
- `analysis-rubric.md` **by path, read verbatim** (per `feedback_dont_paraphrase_canonical_rubrics.md`)
- instruction to write `beats.json` (validate against `schema/beats.schema.json`) and `notes.md` into the comic folder, then set `meta.json` `analysis_status: "done"`.

The subagent reads EVERY page (the growth-page ratio needs a complete count) and scores per the rubric's four axes. Multiple comics analyze in parallel (independent subagents).

### Phase 3 — Synthesize

```bash
scripts/corpus_stats.py --corpus-root corpus            # human table
scripts/corpus_stats.py --corpus-root corpus --json     # machine rollup
```

Computes the derived metrics (growth-page ratio, shot-distance histogram, flat-panel %, expression averages, escalation-device leaderboard) and the 0–5 axis scores side by side. Then write/update `synthesis/success-elements.md` — the living digest of what works, cited to corpus entries. This is the artifact a future model re-runs over the stored `beats.json` to find deeper patterns.

## Output structure

```
research/comic-corpus/
├── SKILL.md
├── analysis-rubric.md          # CANONICAL — passed verbatim to analysis agents
├── schema/beats.schema.json    # machine schema for beats.json
├── scripts/
│   ├── ingest.py               # drain links/files → pages/ + meta.json
│   └── corpus_stats.py         # roll up beats.json → metrics
├── _queue.md                   # dump links/paths here
├── corpus/<slug>/
│   ├── pages/                  # GITIGNORED raw pages
│   ├── meta.json               # source, creators, popularity, status
│   ├── beats.json              # machine-readable analysis (versioned)
│   └── notes.md                # human-readable analysis (versioned)
└── synthesis/
    └── success-elements.md     # cross-corpus digest (versioned)
```

## How production consumes the corpus

The synthesis is not a dead document — it feeds the generators:
- **`story-writers-room`** — the Genre Expert critic cites corpus patterns ("FMG readers expect the growth-page ratio above ~30%; your pitch is at 12%").
- **`script-breakdown`** — pacing defaults (transformation-scene length, growth-page targets, escalation-device menu) seed from corpus norms.
- **`continuity-check` / QA** — the rubric's camera-dynamism and expression-intensity axes become production audit checks (flat-panel %, dead-face %). This is the data backing for the standing directives in memory: `overshoot-camera-dynamism`, `growth-density-mandate`, `expression-intensity`.

## Notes on "successful"

Craft scores (0–5) measure quality, not popularity. The *ground-truth* success signal is engagement (views, comments, Patreon tier, rankings) — recorded in `meta.json` `popularity` when available, never invented. As the corpus grows and popularity data accumulates, synthesis can correlate craft elements with engagement. Until then, treat scores as "well-made," and weight by whatever popularity signal exists.

## Scripts

- `scripts/ingest.py` — register + fetch a comic (`--web` / `--local` / `--list`)
- `scripts/corpus_stats.py` — roll up `beats.json` across the corpus (`--json` for machine output)
