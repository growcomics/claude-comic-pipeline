# Analytics capture — how the engagement stub gets filled

_The flywheel's read side. The stub (`analytics/engagement-stub.json`, schema in
`engagement-stub-schema.json`) is the landing pad; this doc is how numbers land in it.
**ga4 + patreon are WIRED — `scripts/capture_engagement.py` appends them (wrapper-only
reads); the other sources stay Tier-2/manual. Every capture is a deliberate, read-only act**
— nothing here posts or mutates any platform._

## The one credential rule

Reads go through the `~/Documents/.credentials/bin/` wrappers ONLY (`project_credential_architecture`):
**never** `cat` a token file, never `secretctl get` into context, never `curl -u "$(cat …)"`.
If a source has no wrapper yet, write the wrapper first.

## The wired path (ga4 + patreon)

```bash
python3 skills/publisher/scripts/capture_engagement.py --project projects/<p> \
    [--sources ga4,patreon] [--window-days N] [--slug extra-site-slug] [--dry-run]
```

Window defaults to days-since-release from the stub. Appends one entry per source,
append-only — prior captures are never touched. Patron/revenue deltas compute automatically
against the most recent prior patreon capture (the entitled run-rate is embedded
machine-readably in each capture's notes for exactly this). GA caveat: the `ga` wrapper
reports only the TOP pagePath rows by activeUsers — a comic below that cutoff records
**null with a note** (below-top-N is NOT zero; don't read null as failure), and `pageviews`
stays null until the wrapper exposes a pageviews metric. Patreon pages the full roster with
restricted fields (status/cents/pledge-start) — aggregates only, no per-member data stored.
First validated run: not-so-supra-man, 2026-08-11 (release +11d).

## Source by source

| Source | How to read it (today) | Feeds metrics |
|---|---|---|
| **ga4** | `~/Documents/.credentials/bin/ga <growgetter\|maxx\|PROPERTY_ID> [dimension] [days]` — service-account, browser-free. Properties: GrowGetter **303340242**, MaxxMuscle **329224171** (primary; 368156104 is the smaller secondary). **BloomBeauty has NO GA4 property** — site metrics for Bloom are a known gap. For per-comic pageviews, query with a page-path dimension filtered to the comic's slugs. | `pageviews`, `unique_readers` |
| **patreon** | `~/Documents/.credentials/bin/patreon <growgetter\|maxxmuscle\|bloombeauty\|3dmc> <campaign\|members\|raw PATH>` — API v2 creator tokens. Campaigns: GG **3138139**, Maxx **8794850**, Bloom **11913067**, 3DMC **15535167**. "Paying" = `patron_status=='active_patron'` AND a paid tier — headline member counts are mostly free followers; count paying. | `paying_patrons_total`, `patron_delta`, `new_patrons`, `revenue_delta_usd` |
| **site-admin** | comic-platform / 3dmc admin per-part analytics where they exist (3dmc admin has per-part open counts). Read from the admin UI or its JSON; no wrapper needed (session auth, owner-driven). | `pageviews`, `avg_read_depth_pages` |
| **deviantart** | No API token on file (Tier-2: owner signs in, Claude drives the live session — or the owner reads the numbers off the deviation page). Point-in-time counters. | `favourites`, `comments`, `impressions` ("views"), `watchers_delta` (diff two dated captures) |
| **twitter / instagram** | Same Tier-2 story — live-session reads or owner-reported. IG = `growgettercomics` session confirmed on the laptop. | `likes`, `shares`, `comments`, `impressions` |
| **manual** | Owner types numbers in. Always valid — a manual capture beats an empty stub. | anything |

## Cadence

The stub seeds a `capture_plan` of **release +7d** (all sources) and **release +30d**
(ga4/patreon/deviantart). Run `capture_engagement.py` for the ga4/patreon share of each pass
and append the rest by hand; never edit old captures —
the record is append-only so deltas stay computable. A plan entry with no matching capture is a
pass still owed; `window_days` says what a capture covers.

## Where it flows next

The Ideator (Stage 1) reads these stubs across projects as its "what performed" feedstock
(VISION §4: Publisher → Ideator). Until enough captures exist, the corpus remains the ground
truth — that's expected; don't fake density. When several comics have +30d captures, a small
aggregator (Wave-2) can rank transformation flavors / cast / formats by engagement — that
ranking is the flywheel actually turning.
