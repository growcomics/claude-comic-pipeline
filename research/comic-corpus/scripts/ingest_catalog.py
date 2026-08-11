#!/usr/bin/env python3
"""ingest_catalog.py — GrowGetter catalog ingest over the WP REST API.

Supersedes the parked browser-login path (B2 in _queue.md): GrowGetterComics is
one of the user's OWN WordPress sites with admin app-password API access, so the
catalog is ingested over the REST API instead of a driven browser session.

CREDENTIAL RULE (project_credential_architecture): this script NEVER touches a
secret. Every request shells out to the `wp` wrapper in
~/Documents/.credentials/bin/, which reads the app password from the macOS
Keychain at call time and hands it straight to curl. No token is read, printed,
or stored here.

PACING: this is the user's own production site — requests are paced
(default 1.2s between calls) and use per_page=100, so a full catalog run is
~20 requests total.

What it fetches (metadata + text only — NO image binaries, ever):
  - categories + tags (id -> name maps)
  - all posts   (paginated; _fields-trimmed)
  - all pages   (paginated; there are few)
  - approved comments (paginated, capped) -> per-post engagement counts

What it writes under research/comic-corpus/catalog/:
  raw/            full API responses, gitignored (re-derivable, not committed)
  posts.jsonl     one derived catalog record per line       (COMMITTED)
  pages.jsonl     one derived record per site page          (COMMITTED)
  series.json     slug-clustered series index               (COMMITTED)
  INGEST.md       run log: when, counts, parameters         (COMMITTED)

Catalog facts the deriver is built around (verified on the 2026-08-10 pull):
  - 861/1091 posts are Patreon-gated: the plugin strips inline images and
    injects a `patreon-valid-patron-message` div, so gated single-page serial
    drops legitimately have page_image_count 0 — the featured_media id is the
    page pointer. Gating itself is recorded (it is the monetization signal).
  - Categories are sparse (950 Uncategorized); the real content taxonomy is
    derived per-post as `post_kind` (comic-chapter | serial-page | fan-art |
    pdf-bundle | blog | post) from category + slug + image-count heuristics.
  - Series names live in slug prefixes ("heidis-journey-page-88") and tags.

Usage:
  scripts/ingest_catalog.py --site growgetter              # full fetch + derive
  scripts/ingest_catalog.py --summarize                    # re-derive from raw/
  scripts/ingest_catalog.py --site growgetter --max-posts 200   # partial fetch
"""

from __future__ import annotations

import argparse
import collections
import datetime
import html
import json
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
CORPUS_ROOT = HERE.parent
CATALOG_DIR = CORPUS_ROOT / "catalog"
RAW_DIR = CATALOG_DIR / "raw"

WP_WRAPPER = Path.home() / "Documents" / ".credentials" / "bin" / "wp"

POST_FIELDS = ",".join([
    "id", "slug", "title", "date", "modified", "link", "status",
    "categories", "tags", "featured_media", "excerpt", "content",
])
PAGE_FIELDS = ",".join([
    "id", "slug", "title", "date", "modified", "link", "status", "parent",
])

IMG_RE = re.compile(r"<img[^>]+(?:data-lazy-src|data-src|src)=[\"']([^\"']+)[\"']", re.I)
TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")
# The Patreon WP plugin marks gated posts (admin auth still sees the text).
GATED_RE = re.compile(r"patreon-(?:valid-patron-message|locked)")
# Installment suffixes: -2, -issue-3, -part-1, -page-88, -pt-2-of-2 ...
SERIES_SUFFIX_RE = re.compile(
    r"-(?:issue|part|pt|chapter|ch|vol|volume|episode|ep|no|page|pages|p)?-?\d+$"
)
SERIES_WORD_RE = re.compile(r"-(?:page|pages|part|pt|chapter|ch|issue|episode|ep)$")


def wp_get(site: str, rest_path: str, pace: float) -> tuple[list | dict | None, str]:
    """One authenticated GET via the credential wrapper. Returns (json, err)."""
    time.sleep(pace)
    proc = subprocess.run(
        [str(WP_WRAPPER), site, "get", rest_path],
        capture_output=True, text=True, timeout=120,
    )
    body = proc.stdout.strip()
    if proc.returncode != 0:
        return None, f"wrapper exit {proc.returncode}: {proc.stderr.strip()[:200]}"
    try:
        return json.loads(body), ""
    except json.JSONDecodeError:
        return None, f"non-JSON response ({body[:120]!r})"


def fetch_all(site: str, endpoint: str, fields: str, pace: float,
              max_items: int | None = None) -> list[dict]:
    """Drain a paginated collection endpoint. Stops on empty page or WP's
    rest_*_invalid_page_number error."""
    items: list[dict] = []
    page = 1
    while True:
        path = f"{endpoint}?per_page=100&page={page}&_fields={fields}"
        data, err = wp_get(site, path, pace)
        if err:
            print(f"  ! {endpoint} page {page}: {err}", file=sys.stderr)
            break
        if isinstance(data, dict):  # error object, e.g. invalid page number
            if not data.get("code", "").endswith("invalid_page_number"):
                print(f"  ! {endpoint} page {page}: {data.get('code')}", file=sys.stderr)
            break
        if not data:
            break
        items.extend(data)
        print(f"  {endpoint}: page {page} -> {len(items)} total", file=sys.stderr)
        if len(data) < 100:
            break
        if max_items and len(items) >= max_items:
            items = items[:max_items]
            break
        page += 1
    return items


def strip_html(s: str) -> str:
    return WS_RE.sub(" ", html.unescape(TAG_RE.sub(" ", s or ""))).strip()


def series_key(slug: str) -> str:
    """Cluster slugs into a series key by stripping installment-number suffixes
    and trailing installment words: heidis-journey-page-88 -> heidis-journey."""
    s = slug
    prev = None
    while prev != s:
        prev = s
        s = SERIES_SUFFIX_RE.sub("", s)
        s = SERIES_WORD_RE.sub("", s)
    return s or slug


def classify_post(slug: str, categories: list[str], page_image_count: int,
                  gated: bool) -> str:
    """Deterministic post_kind heuristic (documented in the module docstring)."""
    if "Blog" in categories or slug.startswith("blog-"):
        return "blog"
    if "fan-art" in slug:
        return "fan-art"
    if "Pdf" in categories:
        return "pdf-bundle"
    if "Comics" in categories or "Free Comics" in categories or page_image_count >= 8:
        return "comic-chapter"
    if gated and page_image_count <= 2:
        return "serial-page"
    return "post"


def derive_post_record(p: dict, cat_map: dict, tag_map: dict,
                       comment_counts: dict) -> dict:
    content = (p.get("content") or {}).get("rendered", "")
    imgs = IMG_RE.findall(content)
    slug = p.get("slug", "")
    categories = [cat_map.get(c, str(c)) for c in p.get("categories", [])]
    gated = bool(GATED_RE.search(content))
    return {
        "record_type": "catalog-post",
        "id": p.get("id"),
        "slug": slug,
        "title": strip_html((p.get("title") or {}).get("rendered", "")),
        "date": p.get("date"),
        "modified": p.get("modified"),
        "link": p.get("link"),
        "status": p.get("status"),
        "categories": categories,
        "tags": [tag_map.get(t, str(t)) for t in p.get("tags", [])],
        "series": series_key(slug),
        "post_kind": classify_post(slug, categories, len(imgs), gated),
        "patreon_gated": gated,
        "free_comic": "Free Comics" in categories,
        "page_image_count": len(imgs),
        "image_urls_sample": imgs[:2] + (imgs[-1:] if len(imgs) > 3 else []),
        "featured_media": p.get("featured_media"),
        "excerpt_text": strip_html((p.get("excerpt") or {}).get("rendered", ""))[:500],
        "comment_count": comment_counts.get(p.get("id"), 0),
    }


def build_series_index(records: list[dict]) -> dict:
    """Cluster comic content into series with the signals the ideator reads:
    how long a series ran (revealed continuation preference), sizes, cadence,
    gating share, engagement. Blog/fan-art/pdf posts are excluded (pdf bundles
    duplicate comic releases and would double-count)."""
    by_series: dict[str, list[dict]] = collections.defaultdict(list)
    for r in records:
        if r["post_kind"] not in ("comic-chapter", "serial-page"):
            continue
        by_series[r["series"]].append(r)
    series = {}
    for key, posts in sorted(by_series.items()):
        posts.sort(key=lambda r: r["date"] or "")
        page_counts = [r["page_image_count"] for r in posts]
        series[key] = {
            "installments": len(posts),
            "first_post": posts[0]["date"],
            "last_post": posts[-1]["date"],
            "kinds": dict(collections.Counter(r["post_kind"] for r in posts)),
            "gated_installments": sum(1 for r in posts if r["patreon_gated"]),
            "total_page_images": sum(page_counts),
            "median_page_images": sorted(page_counts)[len(page_counts) // 2],
            "total_comments": sum(r["comment_count"] for r in posts),
            "slugs": [r["slug"] for r in posts],
        }
    return series


def load_raw() -> tuple[list, list, list, list, list]:
    posts = json.loads((RAW_DIR / "posts.json").read_text())
    pages = json.loads((RAW_DIR / "pages.json").read_text())
    cats = json.loads((RAW_DIR / "categories.json").read_text())
    tags = json.loads((RAW_DIR / "tags.json").read_text())
    comments = json.loads((RAW_DIR / "comments.json").read_text())
    return posts, pages, cats, tags, comments


def write_outputs(site: str, posts: list, pages: list, cats: list, tags: list,
                  comments: list, pace: float | None, comment_cap: int,
                  fetched_note: str) -> None:
    cat_map = {c["id"]: c["name"] for c in cats}
    tag_map = {t["id"]: t["name"] for t in tags}
    comment_counts = collections.Counter(
        c["post"] for c in comments if c.get("post"))

    records = [derive_post_record(p, cat_map, tag_map, comment_counts)
               for p in posts]
    with (CATALOG_DIR / "posts.jsonl").open("w") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with (CATALOG_DIR / "pages.jsonl").open("w") as f:
        for p in pages:
            f.write(json.dumps({
                "record_type": "catalog-page", "id": p.get("id"),
                "slug": p.get("slug"),
                "title": strip_html((p.get("title") or {}).get("rendered", "")),
                "date": p.get("date"), "link": p.get("link"),
                "parent": p.get("parent"),
            }, ensure_ascii=False) + "\n")

    series = build_series_index(records)
    (CATALOG_DIR / "series.json").write_text(
        json.dumps(series, indent=1, ensure_ascii=False) + "\n")

    stamp = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    kinds = collections.Counter(r["post_kind"] for r in records)
    gated = sum(1 for r in records if r["patreon_gated"])
    (CATALOG_DIR / "INGEST.md").write_text(f"""# Catalog ingest log

- **Derived:** {stamp}  ({fetched_note})
- **Site:** {site} (growgettercomics.com) via WP REST API, `wp` credential wrapper
- **Pacing:** {pace if pace is not None else 'n/a (re-derive from raw/)'}
- **Posts:** {len(records)} — kinds {dict(kinds.most_common())}
- **Patreon-gated:** {gated}/{len(records)}
- **Pages:** {len(pages)}
- **Categories:** {len(cats)} · **Tags:** {len(tags)}
- **Comments sampled:** {len(comments)} (cap {comment_cap}) across {len(comment_counts)} posts
- **Series clustered:** {len(series)} (comic-chapter + serial-page posts only)

Raw API responses live in `raw/` (gitignored, re-derivable). Committed records
carry text + URLs/ids only — **no image binaries** (house corpus rule).
Re-fetch: `scripts/ingest_catalog.py --site {site}` · re-derive only:
`scripts/ingest_catalog.py --summarize`.
""")
    print(f"OK: {len(records)} post records, {len(series)} series -> "
          f"{CATALOG_DIR.relative_to(CORPUS_ROOT)}/", file=sys.stderr)


def run_ingest(site: str, pace: float, max_posts: int | None,
               comment_page_cap: int) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    print("== taxonomies ==", file=sys.stderr)
    cats = fetch_all(site, "wp/v2/categories", "id,name,slug,count", pace)
    tags = fetch_all(site, "wp/v2/tags", "id,name,slug,count", pace)
    (RAW_DIR / "categories.json").write_text(json.dumps(cats, indent=1))
    (RAW_DIR / "tags.json").write_text(json.dumps(tags, indent=1))

    print("== comments (approved, capped) ==", file=sys.stderr)
    comments = fetch_all(site, "wp/v2/comments", "id,post,date", pace,
                         max_items=comment_page_cap * 100)
    (RAW_DIR / "comments.json").write_text(json.dumps(comments, indent=1))

    print("== posts ==", file=sys.stderr)
    posts = fetch_all(site, "wp/v2/posts", POST_FIELDS, pace, max_items=max_posts)
    (RAW_DIR / "posts.json").write_text(json.dumps(posts, indent=1))

    print("== pages ==", file=sys.stderr)
    pages = fetch_all(site, "wp/v2/pages", PAGE_FIELDS, pace)
    (RAW_DIR / "pages.json").write_text(json.dumps(pages, indent=1))

    write_outputs(site, posts, pages, cats, tags, comments, pace,
                  comment_page_cap * 100, "fresh fetch")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="GrowGetter WP catalog -> corpus records")
    ap.add_argument("--site", default="growgetter",
                    help="wp wrapper site key (default: growgetter)")
    ap.add_argument("--pace", type=float, default=1.2,
                    help="seconds between API requests (default 1.2)")
    ap.add_argument("--max-posts", type=int, default=None)
    ap.add_argument("--comment-page-cap", type=int, default=30,
                    help="max 100-comment pages to sample (default 30)")
    ap.add_argument("--summarize", action="store_true",
                    help="rebuild derived files from raw/ without refetching")
    args = ap.parse_args(argv)

    if args.summarize:
        posts, pages, cats, tags, comments = load_raw()
        write_outputs(args.site, posts, pages, cats, tags, comments, None,
                      args.comment_page_cap * 100,
                      "re-derived from raw/ (no refetch)")
        return 0

    if not WP_WRAPPER.exists():
        print(f"FATAL: credential wrapper missing at {WP_WRAPPER}", file=sys.stderr)
        return 1

    run_ingest(args.site, args.pace, args.max_posts, args.comment_page_cap)
    return 0


if __name__ == "__main__":
    sys.exit(main())
