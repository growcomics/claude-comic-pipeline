#!/usr/bin/env python3
"""ingest.py — register a comic into the corpus and (where possible) fetch pages.

Two acquisition paths:

  --local <dir-or-file>   Register a local image folder, CBZ, or PDF. Image
                          folders and CBZ are copied/extracted into pages/.
                          PDFs are noted for the caller to rasterize.

  --web <url>             Register a web source. For KNOWN hosts (currently
                          growgettercomics.com) the page-image URL pattern is
                          derived and fetched automatically. For unknown hosts,
                          a meta.json skeleton is written and the caller (Claude)
                          drives the Chrome MCP to capture pages into pages/
                          (same blob-fetch pattern as the Flow bulk-downloader).

Either way it creates:
    corpus/<slug>/
        pages/        (gitignored — raw third-party pages)
        meta.json     (source, creators, popularity, ingest date)

Then the caller runs the analysis agent against pages/ using analysis-rubric.md.

Usage:
    ingest.py --web "https://growgettercomics.com/the-mysterious-book-..." --slug the-mysterious-book-1
    ingest.py --local ~/Downloads/some-comic/ --slug some-comic --title "Some Comic"
    ingest.py --list           # show corpus contents + analysis status
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

CORPUS_ROOT = Path(__file__).resolve().parent.parent / "corpus"
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
DOWNLOAD_TIMEOUT_S = 60
MAX_PAGE_BYTES = 25 * 1024 * 1024


def slugify(text: str) -> str:
    s = text.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[-\s]+", "-", s)
    return s.strip("-")


def meta_skeleton(slug: str, source: str, title: str | None) -> dict:
    return {
        "comic_id": slug,
        "title": title or slug.replace("-", " ").title(),
        "source": source,
        "creators": {"art": None, "story": None},
        "popularity": {"available": False},
        "ingested_at": datetime.now(timezone.utc).isoformat(),
        "analysis_status": "pending",
        "rubric_version": "1.0",
    }


def write_meta(pack: Path, meta: dict) -> None:
    (pack / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")


def _is_image(data: bytes) -> bool:
    return (
        data.startswith(b"\x89PNG\r\n\x1a\n")
        or data.startswith(b"\xff\xd8\xff")
        or data[:4] == b"RIFF"  # webp
        or data[:6] in (b"GIF87a", b"GIF89a")
    )


def fetch(url: str, dst: Path) -> bool:
    if urlparse(url).scheme not in ("http", "https"):
        raise ValueError(f"refusing non-http(s) URL: {url}")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=DOWNLOAD_TIMEOUT_S) as resp:
            data = resp.read(MAX_PAGE_BYTES + 1)
    except Exception as e:  # noqa: BLE001 — report and skip, don't abort the batch
        print(f"  miss: {url} ({e})", file=sys.stderr)
        return False
    if len(data) > MAX_PAGE_BYTES or not _is_image(data):
        print(f"  miss: {url} (not an image / too big)", file=sys.stderr)
        return False
    dst.write_bytes(data)
    return True


# --- known-host page-URL derivation ---------------------------------------

def growgetter_urls(html_url: str) -> list[str] | None:
    """Derive page-image URLs for a growgettercomics.com chapter page.

    The site serves full-res pages at predictable wp-content/uploads paths
    (e.g. TMB1.jpg, TMB12.jpg ... TMB125.jpg). We fetch the chapter HTML and
    scrape the uploads image URLs, collapsing WP size-variant suffixes and
    dropping site chrome (logos, avatars, icons).
    """
    if "growgettercomics.com" not in html_url:
        return None
    req = urllib.request.Request(html_url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=DOWNLOAD_TIMEOUT_S) as resp:
        html = resp.read().decode("utf-8", "replace")
    raw = re.findall(r'https://growgettercomics\.com/wp-content/uploads/[^"\'\s]+?\.(?:jpg|jpeg|png)', html)
    # collapse -WxH and -scaled variants to the canonical upload
    canon = []
    seen = set()
    for u in raw:
        c = re.sub(r"-\d+x\d+(\.\w+)$", r"\1", u)
        if c in seen:
            continue
        seen.add(c)
        canon.append(c)
    # keep only comic pages: filename starts with TMB and is not chrome
    pages = [
        u for u in canon
        if re.search(r"/TMB\d", u) and not re.search(r"avatar|logo|favicon|instagram|twitter|devianart|patreon", u, re.I)
    ]

    def page_key(u: str):
        m = re.search(r"/TMB(\d+?)(?:-scaled)?\.\w+$", u)
        return int(m.group(1)) if m else 0

    return sorted(set(pages), key=page_key) or None


# --- local ingestion -------------------------------------------------------

def ingest_local(src: Path, pages: Path) -> int:
    if src.is_dir():
        imgs = sorted(f for f in src.iterdir() if f.suffix.lower() in IMAGE_EXTS)
        for i, f in enumerate(imgs, 1):
            shutil.copy(f, pages / f"page-{i:02d}{f.suffix.lower()}")
        return len(imgs)
    if src.suffix.lower() == ".cbz" or src.suffix.lower() == ".zip":
        with zipfile.ZipFile(src) as z:
            names = sorted(n for n in z.namelist() if Path(n).suffix.lower() in IMAGE_EXTS)
            for i, n in enumerate(names, 1):
                with z.open(n) as fp:
                    (pages / f"page-{i:02d}{Path(n).suffix.lower()}").write_bytes(fp.read())
        return len(names)
    if src.suffix.lower() == ".pdf":
        print(f"  PDF registered but not rasterized: {src}", file=sys.stderr)
        print("  Caller should rasterize pages into pages/ (e.g. via the pdf skill).", file=sys.stderr)
        return 0
    raise ValueError(f"unsupported local source: {src}")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Ingest a comic into the corpus.")
    p.add_argument("--web", help="Web source URL")
    p.add_argument("--local", type=Path, help="Local dir / CBZ / PDF")
    p.add_argument("--slug", help="Corpus slug (default: derived)")
    p.add_argument("--title", help="Human title")
    p.add_argument("--list", action="store_true", help="List corpus contents + status")
    args = p.parse_args(argv)

    if args.list:
        if not CORPUS_ROOT.exists():
            print("corpus empty")
            return 0
        for pack in sorted(CORPUS_ROOT.iterdir()):
            if not pack.is_dir():
                continue
            n = len(list((pack / "pages").glob("page-*"))) if (pack / "pages").exists() else 0
            status = "?"
            mp = pack / "meta.json"
            if mp.exists():
                try:
                    status = json.loads(mp.read_text()).get("analysis_status", "?")
                except json.JSONDecodeError:
                    pass
            analyzed = "✓beats" if (pack / "beats.json").exists() else "—"
            print(f"  {pack.name:46} {n:>3} pages  status={status:9} {analyzed}")
        return 0

    if not (args.web or args.local):
        print("ERROR: pass --web URL, --local PATH, or --list", file=sys.stderr)
        return 2

    source = args.web or str(args.local)
    slug = args.slug or slugify(Path(source).stem if args.local else urlparse(source).path.strip("/").split("/")[-1])
    if not slug:
        print("ERROR: could not derive slug; pass --slug", file=sys.stderr)
        return 2

    pack = CORPUS_ROOT / slug
    pages = pack / "pages"
    pages.mkdir(parents=True, exist_ok=True)

    meta = meta_skeleton(slug, source, args.title)
    write_meta(pack, meta)

    fetched = 0
    if args.local:
        fetched = ingest_local(args.local, pages)
        print(f"Ingested {fetched} local pages → {pages}")
    else:
        urls = growgetter_urls(args.web)
        if urls is None:
            print(f"Registered web source (unknown host). meta.json written to {pack}.")
            print("Next: drive Chrome MCP to capture pages into pages/ (blob-fetch pattern),")
            print("      then run the analysis agent with analysis-rubric.md.")
            return 0
        print(f"Derived {len(urls)} page URLs from {args.web}; fetching…")
        for i, u in enumerate(urls, 1):
            ext = Path(urlparse(u).path).suffix.lower() or ".jpg"
            if fetch(u, pages / f"page-{i:02d}{ext}"):
                fetched += 1
        print(f"Fetched {fetched}/{len(urls)} pages → {pages}")

    meta["page_count"] = fetched
    write_meta(pack, meta)
    print(f"meta.json → {pack / 'meta.json'}")
    print(f"Next: analyze pages/ against analysis-rubric.md, write beats.json + notes.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
