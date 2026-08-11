#!/usr/bin/env python3
"""
capture_engagement.py — Stage 7 (PUBLISHER) Wave-2 engagement capture.

Appends REAL capture entries to projects/<p>/analytics/engagement-stub.json
(schema: skills/publisher/references/engagement-stub-schema.json) for the
wrapper-capable sources: ga4 and patreon.  This is the flywheel's read side
(references/analytics-capture.md) — deviantart / twitter / instagram /
site-admin remain Tier-2 / manual captures appended by hand.

THE CREDENTIAL RULE, STRUCTURALLY
  A secret must never enter context (project_credential_architecture).  This
  script reads NOTHING from ~/Documents/.credentials/ except by EXECUTING the
  two fixed wrapper binaries ~/Documents/.credentials/bin/{ga,patreon}, which
  return results, not secrets.  It never cats a token file, never touches the
  Keychain, takes no token arguments, and sets no credential env vars.

READ / LOCAL-WRITE ONLY
  Every wrapper call is a read (GA runReport via `ga`; Patreon GET paths via
  `patreon`).  The only write is the local append to engagement-stub.json —
  append-only, existing captures are never modified, so deltas stay computable
  (analytics-capture.md).  Nothing posts, uploads, or deploys.

What lands per source:
  ga4     — unique_readers = activeUsers summed over top-pagePath rows whose
            path matches the comic's slugs.  The wrapper reports only the top
            rows by activeUsers, so "no matching row" is recorded as null with
            a note (below the wrapper's cutoff is NOT zero).  pageviews: null
            (the wrapper exposes activeUsers only).
  patreon — paying_patrons_total (patron_status=='active_patron' AND entitled
            cents > 0 — headline member counts are mostly free followers),
            new_patrons (paying members whose pledge started on/after the
            release date), patron_delta + revenue_delta_usd vs the most recent
            prior patreon capture in the stub when one exists.  Only aggregate
            counts are computed; no per-member data is stored.

Usage:
  python3 skills/publisher/scripts/capture_engagement.py --project projects/<p> \
      [--sources ga4,patreon] [--window-days N] [--slug extra-slug ...] \
      [--notes "..."] [--dry-run]

  window defaults to days-since-release from the stub's release_date.
Exit: 0 all requested sources captured · 2 some source failed (successes still
appended) · 1 hard error, nothing written.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import date, datetime, timezone

WRAP_DIR = os.path.expanduser("~/Documents/.credentials/bin")
GA_BIN = os.path.join(WRAP_DIR, "ga")
PATREON_BIN = os.path.join(WRAP_DIR, "patreon")
PATREON_API_PREFIX = "https://www.patreon.com/api/oauth2/v2"

# Property wiring per references/analytics-capture.md (memory: reference_ga_api_access,
# reference_patreon_api_tokens).  None = documented gap, not an error in the map.
GA_PROPERTY = {"growgetter": "303340242", "maxxmuscle": "329224171",
               "bloombeauty": None,  # BloomBeauty has NO GA4 property — known gap
               "3dmc": None}         # no GA4 property on file for 3dmc
PATREON_CAMPAIGN = {"growgetter": "3138139", "maxxmuscle": "8794850",
                    "bloombeauty": "11913067", "3dmc": "15535167"}

MEMBER_FIELDS = "patron_status,currently_entitled_amount_cents,pledge_relationship_start"
MAX_ROSTER_PAGES = 30  # 1000/page — far above any current campaign; runaway guard

GA_ROW_RE = re.compile(r"^\s+(/\S*)\s+([\d,]+)\s*$")
RUN_RATE_RE = re.compile(r"entitled_run_rate_usd_month=([\d.]+)")


class CaptureError(Exception):
    pass


def utcnow():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run_wrapper(binary, args, timeout=180):
    """Execute a credential wrapper. The wrappers print results, never secrets."""
    if os.path.dirname(os.path.realpath(binary)) != os.path.realpath(WRAP_DIR):
        raise CaptureError("refusing to execute %s — wrappers live in %s only" % (binary, WRAP_DIR))
    if not os.access(binary, os.X_OK):
        raise CaptureError("wrapper missing/not executable: %s (see project_credential_architecture)" % binary)
    try:
        r = subprocess.run([binary] + args, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise CaptureError("%s %s timed out after %ds" % (os.path.basename(binary), args[:2], timeout))
    if r.returncode != 0:
        raise CaptureError("%s %s failed (rc=%d): %s" % (
            os.path.basename(binary), args[:2], r.returncode, (r.stderr or r.stdout).strip()[:300]))
    return r.stdout


def capture_ga4(prop, window_days, slugs):
    prop_id = GA_PROPERTY.get(prop)
    if not prop_id:
        raise CaptureError("no GA4 property for '%s' (BloomBeauty has none — documented gap; "
                           "3dmc has none on file)" % prop)
    out = run_wrapper(GA_BIN, [prop_id, "pagePath", str(window_days)])
    rows = [(m.group(1), int(m.group(2).replace(",", ""))) for m in map(GA_ROW_RE.match, out.splitlines()) if m]
    matched = [(p, n) for p, n in rows if any(s in p.lower() for s in slugs)]
    metrics = {"pageviews": None,  # wrapper exposes activeUsers only
               "unique_readers": sum(n for _, n in matched) if matched else None}
    if matched:
        note = "bin/ga pagePath activeUsers, matched: " + ", ".join("%s %d" % m for m in matched)
    else:
        cutoff = min((n for _, n in rows), default=None)
        note = ("no slug-matching row in bin/ga's top-%d pagePath rows (cutoff ~%s activeUsers) — "
                "below the wrapper's top-N, NOT zero" % (len(rows), cutoff))
    note += "; pageviews unavailable from wrapper. slugs tried: %s" % ", ".join(sorted(slugs))
    return {"source": "ga4",
            "source_detail": "GA4 property %s via bin/ga (pagePath, last %dd)" % (prop_id, window_days),
            "metrics": metrics, "notes": note}


def latest_prior(stub, source):
    for cap in reversed(stub.get("captures", [])):
        if cap.get("source") == source:
            return cap
    return None


def capture_patreon(prop, window_days, release_date, stub):
    campaign_id = PATREON_CAMPAIGN[prop]
    cam = json.loads(run_wrapper(PATREON_BIN, [prop, "campaign"]))
    headline = cam["data"][0]["attributes"].get("patron_count")

    total = paying = new_paying = run_rate_cents = pages = 0
    path = ("/campaigns/%s/members?page%%5Bcount%%5D=1000&fields%%5Bmember%%5D=%s"
            % (campaign_id, MEMBER_FIELDS))
    while path and pages < MAX_ROSTER_PAGES:
        j = json.loads(run_wrapper(PATREON_BIN, [prop, "raw", path]))
        for m in j.get("data", []):
            a = m.get("attributes", {})
            total += 1
            if a.get("patron_status") == "active_patron" and (a.get("currently_entitled_amount_cents") or 0) > 0:
                paying += 1
                run_rate_cents += a["currently_entitled_amount_cents"]
                start = (a.get("pledge_relationship_start") or "")[:10]
                if release_date and start >= release_date:
                    new_paying += 1
        pages += 1
        nxt = j.get("links", {}).get("next")
        path = nxt[len(PATREON_API_PREFIX):] if nxt and nxt.startswith(PATREON_API_PREFIX) else None

    run_rate_usd = run_rate_cents / 100.0
    prior = latest_prior(stub, "patreon")
    patron_delta = revenue_delta = None
    if prior:
        prev_paying = (prior.get("metrics") or {}).get("paying_patrons_total")
        if isinstance(prev_paying, int):
            patron_delta = paying - prev_paying
        m = RUN_RATE_RE.search(prior.get("notes") or "")
        if m:
            revenue_delta = round(run_rate_usd - float(m.group(1)), 2)

    metrics = {"paying_patrons_total": paying,
               "new_patrons": new_paying if release_date else None,
               "patron_delta": patron_delta,
               "revenue_delta_usd": revenue_delta}
    note = ("roster %d members over %d pages; paying = active_patron AND entitled cents>0; "
            "headline patron_count=%s (incl. free/former); entitled_run_rate_usd_month=%.2f; "
            "new_patrons = paying whose pledge started on/after release%s"
            % (total, pages, headline, run_rate_usd,
               "" if prior else "; deltas null (no prior patreon capture to diff)"))
    return {"source": "patreon",
            "source_detail": "Patreon campaign %s via bin/patreon (full roster paged)" % campaign_id,
            "metrics": metrics, "notes": note}


def main():
    ap = argparse.ArgumentParser(description="Append real ga4/patreon engagement captures to a project's "
                                             "engagement stub. Wrapper reads + local append ONLY — never posts.")
    ap.add_argument("--project", required=True, help="projects/<p> directory")
    ap.add_argument("--sources", default="ga4,patreon",
                    help="Comma list of ga4,patreon (default both). Other stub sources are Tier-2/manual — "
                         "append those by hand per references/analytics-capture.md.")
    ap.add_argument("--window-days", type=int, help="Override capture window (default: days since release_date)")
    ap.add_argument("--slug", action="append", default=[],
                    help="Extra site path slug(s) to match in GA rows (repeatable; comic_id + project always tried)")
    ap.add_argument("--notes", help="Extra note appended to every capture written this run")
    ap.add_argument("--dry-run", action="store_true", help="Read + print the entries; write nothing")
    args = ap.parse_args()

    project = os.path.abspath(args.project)
    stub_path = os.path.join(project, "analytics", "engagement-stub.json")
    if not os.path.exists(stub_path):
        sys.exit("No engagement stub at %s — prepare_post.py seeds it." % stub_path)
    stub = json.load(open(stub_path))
    if stub.get("schema_version") != 1:
        sys.exit("Unexpected schema_version %r in %s" % (stub.get("schema_version"), stub_path))

    prop = stub.get("property")
    if prop not in PATREON_CAMPAIGN:
        sys.exit("Unknown property %r in stub" % prop)

    sources = [s.strip() for s in args.sources.split(",") if s.strip()]
    bad = [s for s in sources if s not in ("ga4", "patreon")]
    if bad:
        sys.exit("Unsupported source(s) %s — this script wires ga4+patreon only; other sources are "
                 "Tier-2/manual (references/analytics-capture.md)." % ", ".join(bad))

    release = stub.get("release_date")
    if args.window_days:
        window = args.window_days
    elif release:
        window = (date.today() - date.fromisoformat(release)).days
        if window < 1:
            sys.exit("release_date %s is not in the past — pass --window-days explicitly" % release)
    else:
        sys.exit("Stub has no release_date — pass --window-days")

    slugs = {s.lower() for s in [stub.get("comic_id"), stub.get("project")] + args.slug if s}

    entries, failures = [], []
    for src in sources:
        try:
            if src == "ga4":
                e = capture_ga4(prop, window, slugs)
            else:
                e = capture_patreon(prop, window, release, stub)
            e = {"captured_at": utcnow(), "source": e["source"], "source_detail": e["source_detail"],
                 "window_days": window, "metrics": e["metrics"],
                 "notes": e["notes"] + ("; " + args.notes if args.notes else "")}
            entries.append(e)
            print("capture ok: %s — %s" % (src, json.dumps(e["metrics"])))
        except CaptureError as err:
            failures.append((src, str(err)))
            print("capture FAILED: %s — %s" % (src, err), file=sys.stderr)

    if args.dry_run:
        print("\nDRY RUN — nothing written. Entries that would append:")
        print(json.dumps(entries, indent=2, ensure_ascii=False))
    elif entries:
        stub["captures"] = stub.get("captures", []) + entries  # append-only: prior entries untouched
        tmp = stub_path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(stub, f, indent=2, ensure_ascii=False)
            f.write("\n")
        os.replace(tmp, stub_path)
        print("Appended %d capture(s) -> %s (now %d total; append-only, nothing else modified)"
              % (len(entries), stub_path, len(stub["captures"])))
        print("Reminder: read-only capture — nothing was posted to any platform.")

    sys.exit(2 if failures else 0)


if __name__ == "__main__":
    main()
