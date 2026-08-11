# Catalog synthesis — GrowGetter full-catalog signals (v1)

**Source:** 1,091 posts / 27 site pages / 9 categories / 59 tags / 702 approved
comments, ingested 2026-08-10 over the WP REST API (`scripts/ingest_catalog.py`,
admin app-password via the `wp` credential wrapper). Derived records:
`posts.jsonl`, `series.json`. **This is the corpus's first popularity /
monetization signal** — the visual corpus (`../synthesis/success-elements.md`)
explicitly listed "no popularity signal" as an open gap; these findings
partially close it. Catalog findings are numbered **C1–C6** so they can be
cited alongside the visual corpus's F1–F6.

Post kinds (derived): 655 gated serial pages · 184 fan-art posts ·
105 comic chapters · 27 PDF bundles · 19 blog posts · 101 other.

---

## C1 — The modern flagship is a character-universe serial (the Heidi franchise)

The largest content cluster by far: **Heidi** — `heidi` (257 page-images),
`heidi-and-mia` (197), `mia-a-heidi-story` (165), `heidi-a-spoiled-girls-journey-continued`
(120), plus **`heidis-journey`: 84 gated single-page drops**. That is roughly
**800+ pages in one character universe**, still the active publishing lane in
2026 (latest post: "Heidi and Mia", 2026-08-09). The publisher's revealed
preference: once a character lands, KEEP FEEDING HER — spin-offs, team-ups,
page-a-day serials.

**Ideator implication:** favor concepts with **serial legs** — a recurring
protagonist, an engine that supports episodic escalation, spin-off-able side
cast. A one-shot with no continuation surface leaves the catalog's dominant
business pattern on the table.

## C2 — Engagement leaders are mundane-institution premise hooks

Top comment-getters among comics: `influencers` (34), `gg-industries` (23),
`heidi-and-mia` (22), `not-exactly-as-planned` (20), `the-power-belt` (18),
`super-ceos` (17), `the-bar-issue-2` (15), `doom-girl` (15). The pattern: a
**contemporary mundane institution + a power twist** — an influencer house, a
workplace/industrial empire, a CEO suite, a neighborhood bar. This validates
the GG_FORMULA's "mundane contemporary setting" and short-punchy-title rules
with engagement data, not just catalog presence.

**Cross-validation:** `not-exactly-as-planned` is one of the source author's
three highest-growth-density scripts (gribble-corpus profiling) AND a top
engagement leader here — growth density and audience response line up.

## C3 — The freemium funnel: free chapters acquire, gated dailies retain

52 posts are categorized **Free Comics**; **655 serial pages are
Patreon-gated** (79% of all posts carry the gate marker), plus 27 PDF bundles.
The model: free standalone chapters as acquisition, page-a-day gated serials +
PDF compilations as the paid product.

**Ideator implication:** a strong concept should work as BOTH — a free
standalone chapter (complete arc, paid-off ending, per corpus F5) that can
continue as a gated serial (cliffhanger tease, next rung of the escalation
ladder). Score concepts down if they can only be one or the other.

## C4 — Chapter length norms confirm the corpus

Comic-chapter medians per series: `the-bar` 31pp, `ultragal` 23pp,
`from-worst-to-first` 22pp, `growth-gun-cheaters` 18pp — right on the visual
corpus's 209pp/9-book ≈ 23pp norm. **Est. page counts of 16–32 are the
catalog-validated band** for a chapter; the serial lane runs 1pp/day instead.
(Gated serial pages have `page_image_count` 0 — the gate strips inline images —
so gated page counts undercount; the featured_media id is the page pointer.)

## C5 — Community ritual: Fan-Art Friday

184 fan-art posts; the hub post has the site's highest comment count (88).
A posting-ops signal more than an ideation one, but it shows the audience
participates when given a recurring ritual. (Routes to `project_posting_ops`.)

## C6 — The production gap the pipeline exists to fill

Output by year: 2021 ≈ 296 posts, 2022 ≈ 351, then decline — 2025: 66,
2026: 14 in seven months. The catalog documents a production-capacity cliff,
not a demand cliff (the gated-serial model kept running). This is the
motivation baseline for the seven-stage line; re-measure after the pipeline
ships comics.

---

## Caveats (read before citing)

- **Comments are approved-only and low-N** (702 total) — a real but weak
  engagement proxy; treat ordering, not magnitudes, as signal.
- **Gating is near-uniform on serials**, so "gated" is a format marker, not
  per-title price discrimination.
- **Series clustering is slug-heuristic** (`series_key()` in
  `ingest_catalog.py`); tags are the cleaner series names where present.
- No view/like data — WordPress does not expose it; GA4 (see
  `reference_ga_api_access`) is the future upgrade path for real traffic
  per title.

## How this feeds the ideator

`skills/ideator/scripts/tournament.py brief` digests `series.json` +
these findings automatically (top series, engagement leaders, the C1–C3
implications). Concepts should cite catalog findings in `corpus_grounding`
(e.g. `"C1 serial-legs"`, `"C2 mundane-institution-hook"`, `"C3 freemium-funnel"`)
alongside F1–F6.
