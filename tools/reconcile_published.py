#!/usr/bin/env python3
"""Reconcile the posting/schedule board against what each property ACTUALLY published.

WHY THIS EXISTS
---------------
2026-08-23: the board showed "GrowGetter Weekly - dry / nothing booked" and that was reported to
the owner as fact. It was wrong. GrowGetter had been posting weekly pages every Monday for weeks
("Magna - Rise of an Ultra-Villainess", art by TMGF, colors by Chris). The board was simply
missing the rows, and because the "dry" badge is computed from the board's own data, an incomplete
board produced a confident false negative.

THE RULE THIS ENFORCES
----------------------
Never report a lane as empty/dry from board data alone. A lane is only dry if the property's
PUBLISHED OUTPUT is also silent. Both sources below are public and need no credentials, so there
is no excuse for skipping the check.

USAGE
-----
    python3 tools/reconcile_published.py            # report only
    python3 tools/reconcile_published.py --json     # machine-readable

Exit code 1 if any lane looks dry on the board while the property is actively publishing.
"""
import json, re, sys, urllib.request, datetime

UA = {"User-Agent": "3dmc-reconciler/1.0"}
LOOKBACK_DAYS = 90   # ~3 months: far enough back to catch a lane that quietly ran all summer

# property key on the board -> (WordPress site, DeviantArt gallery query)
# NOTE: giantessgirl was removed 2026-08-23 - no longer the owner's property. Do not re-add.
PROPERTIES = {
    "growgetter":   ("https://growgettercomics.com",   "growgetter"),
    "maxxmuscle":   ("https://maxxmusclecomics.com",   "maxxmuscle"),
    "bloombeauty":  ("https://bloombeautycomics.com",  "bloombeauty"),
}

def _get(url, timeout=25):
    try:
        return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout).read()
    except Exception:
        return b""

def wp_posts(site):
    """Recent posts via the public WP REST API. Returns [(date, title)]."""
    raw = _get(f"{site}/wp-json/wp/v2/posts?per_page=20&_fields=title,date")
    try:
        return [(p["date"][:10], re.sub(r"&#\d+;", "'", p["title"]["rendered"]))
                for p in json.loads(raw)]
    except Exception:
        return []

def da_posts(gallery):
    """Recent DeviantArt deviations via the public RSS feed. Returns [(date, title)]."""
    raw = _get(f"https://backend.deviantart.com/rss.xml?q=gallery%3A{gallery}&type=deviation").decode("utf8", "ignore")
    out = []
    for ti, pd in re.findall(r"<title>(.*?)</title>.*?<pubDate>(.*?)</pubDate>", raw, re.S)[1:]:
        try:
            out.append((datetime.datetime.strptime(pd[5:16].strip(), "%d %b %Y").date().isoformat(), ti.strip()))
        except Exception:
            pass
    return out

def board_coverage(items, prop, lane, since, until):
    """Weeks covered by board rows for this property+lane inside the window."""
    covered = set()
    for i in items:
        if i.get("property") != prop or i.get("lane") != lane:
            continue
        try:
            start = datetime.date.fromisoformat(i.get("slot") or "")
        except ValueError:
            continue
        for k in range(int(i.get("weeks") or 1)):
            wk = start + datetime.timedelta(weeks=k)
            if since <= wk <= until:
                covered.add(wk)
    return covered

def main():
    as_json = "--json" in sys.argv
    days = LOOKBACK_DAYS
    for a in sys.argv:
        if a.startswith("--days="): days = int(a.split("=",1)[1])
    board = json.load(open("/tmp/sched/posting.new6.json")) if "--local" in sys.argv else None
    if board is None:
        sys.stderr.write("Fetch posting.json from the host and pass --local, or wire the cPanel read in here.\n")
        return 2
    items = board["items"]
    today = datetime.date.today()
    since = today - datetime.timedelta(days=days)

    findings = []
    for prop, (site, gallery) in PROPERTIES.items():
        published = [(d, t) for d, t in (wp_posts(site) + da_posts(gallery)) if d >= since.isoformat()]
        if not published:
            continue                                   # genuinely quiet, or site unreachable
        for lane in ("faf", "weekly", "comic"):
            cov = board_coverage(items, prop, lane, since, today)
            if not cov:
                findings.append({
                    "property": prop, "lane": lane,
                    "board_says": "DRY (no rows in the window)",
                    "reality": f"{len(published)} published item(s) in the last {days} days",
                    "newest": sorted(published, reverse=True)[:6],
                })
    if as_json:
        print(json.dumps(findings, indent=1))
    else:
        if not findings:
            print("OK — no lane claims to be dry while its property is publishing.")
        for f in findings:
            print(f"\n⚠  {f['property']} / {f['lane']}: board says {f['board_says']}")
            print(f"   but the property published {f['reality']}:")
            for d, t in f["newest"]:
                print(f"     {d}  {t[:66]}")
            print("   -> the board is missing rows, OR this lane's work posts under another lane. Check before")
            print("      telling anyone this lane is empty.")
    return 1 if findings else 0

if __name__ == "__main__":
    sys.exit(main())
