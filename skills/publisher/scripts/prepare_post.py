#!/usr/bin/env python3
"""
prepare_post.py — Stage 7 (PUBLISHER) bundle assembler.  PREP ONLY.

Assembles projects/<p>/posting/bundle/ from a reviewed, compiled comic:
destination-ordered publish checklist, per-platform caption skeletons,
per-platform image-crop SPECS (dimensions + page picks — v1 does NOT render
crops), site-side apply notes keyed to the property's publish runbook, a
What's-New entry draft, and posted.template.json.  Also seeds the per-project
analytics landing pad (analytics/engagement-stub.json).

STRUCTURAL NEVER-POST GUARANTEE
  This script imports nothing that can reach a network (no urllib, requests,
  socket, subprocess).  It reads project files and writes local text files
  under the project directory.  There is no flag, mode, or code path that
  posts, uploads, deploys, or fires anything outward.  Publishing is a human,
  deciding, on purpose — per feedback_never_post_without_permission and
  docs/PRODUCTION-SYSTEM-VISION.md §5 (PUBLISHER).

  It also NEVER writes posting/posted.json — that file existing is
  build-comic.md's "posting stage complete" sentinel, and only the human who
  actually posted may create it (by filling bundle/posted.template.json and
  saving it up one level).

Usage:
  python3 skills/publisher/scripts/prepare_post.py --project projects/<p> \
      --property growgetter [--title "Display Title"] [--comic-id <id>] \
      [--release-date YYYY-MM-DD] [--pages-dir <dir>] [--force]
"""

import argparse
import glob
import json
import os
import re
import struct
import sys
from datetime import date, datetime, timezone

BUNDLE_VERSION = 1
PLATFORM_KEYS = ["site", "patreon", "deviantart", "twitter", "instagram"]  # EXACT studio/posting.php chip keys

# Property table — CONFIRMED destinations only (memory: reference_patreon_api_tokens,
# project_posting_ops, project_3dmusclecomics_site).  Unknowns point at the live
# studio/data/cc-sites.json rather than guessing a URL wrong.
CC_SITES_NOTE = "account URL in studio/data/cc-sites.json"
PROPERTIES = {
    "growgetter": {
        "label": "GrowGetter",
        "site": "https://growgettercomics.com (WP, live) / comic-platform staging: https://3dmusclecomics.com/platform/backend/index.php?property=growgetter",
        "site_path": "comic-platform",  # publish/<property>/<id>.json runbook path
        "patreon": "https://www.patreon.com/growgetter",
        "deviantart": CC_SITES_NOTE + "; ~15.6k watchers",
        "twitter": CC_SITES_NOTE,
        "instagram": "growgettercomics (owner IG session confirmed 2026-07-25)",
        "notes": "Biggest property. FAF weekly on Patreon (Alternate posts). Paid tiers $1/$5/$15/$18/$40; ~500 paying.",
    },
    "maxxmuscle": {
        "label": "MaxxMuscle",
        "site": "https://maxxmusclecomics.com (WP, live) / comic-platform staging: https://3dmusclecomics.com/platform/backend/index.php?property=maxxmuscle",
        "site_path": "comic-platform",
        "patreon": "https://www.patreon.com/maxxmuscle",
        "deviantart": "official https://www.deviantart.com/maxxmusclegrowth (a legacy /maxxmuscle-comics also exists — post to OFFICIAL only)",
        "twitter": CC_SITES_NOTE,
        "instagram": CC_SITES_NOTE,
        "notes": "Paid tiers $3/$8/$15/$20/$35; ~333 paying. Spanish is the #2 site language — consider ES caption line.",
    },
    "bloombeauty": {
        "label": "BloomBeauty",
        "site": "https://bloombeautycomics.com (WP, live) / comic-platform staging: https://3dmusclecomics.com/platform/backend/index.php?property=bloombeauty",
        "site_path": "comic-platform",
        "patreon": "https://www.patreon.com/BloomBeautyComics",
        "deviantart": CC_SITES_NOTE + "; ~9.9k watchers",
        "twitter": CC_SITES_NOTE,
        "instagram": CC_SITES_NOTE,
        "notes": "Paid tiers $4.95/$5/$15; ~99 paying and declining — consistency matters most here.",
    },
    "3dmc": {
        "label": "3dMuscleComics",
        "site": "https://3dmusclecomics.com (admin CMS: /admin/ series→part→upload→publish)",
        "site_path": "3dmc-admin",
        "patreon": "https://www.patreon.com/3dMuscleComics",
        "deviantart": "https://www.deviantart.com/3dmusclecomics",
        "twitter": "@3dMuscleComics",
        "instagram": CC_SITES_NOTE,
        "notes": "Newest brand. DA cadence = several drops/week; Patreon 97 members (Feb 2026 launch).",
    },
}

# v1 crop SPECS (dimensions + which pages).  Rendering the crops is Wave-2;
# a human (or a later render step) executes these specs.
def crop_specs(cover, teasers):
    return {
        "_note": "SPECS only — v1 renders nothing. gravity=attention-center means crop around the "
                 "visual subject, not the geometric center. Teaser picks are SUGGESTIONS — human "
                 "verifies SFW + non-spoiler before use.",
        "site": {
            "treatment": "native",
            "pages": "all",
            "note": "The reader serves native full-resolution pages; no crops. Cover for the catalogue "
                    "record comes from the cover page as-is.",
        },
        "patreon": {
            "post_header": {"source": cover, "w": 1600, "h": 900, "gravity": "attention-center"},
            "attach_full_pages": [cover] + teasers,
            "note": "Header crop leads the post; attach cover + teasers full-res. Full comic stays "
                    "behind the paid tier / site link — never attach all pages to a public post.",
        },
        "deviantart": {
            "main_deviation": {"source": cover, "treatment": "native full-res"},
            "optional_teasers": teasers,
            "note": "DA takes native aspect at full res. Mature-content flag ON. Teasers as separate "
                    "deviations or a folder per house style.",
        },
        "twitter": {
            "single": {"source": cover, "w": 1600, "h": 900, "gravity": "attention-center"},
            "four_up": [{"source": p, "w": 1200, "h": 675, "gravity": "attention-center"}
                        for p in ([cover] + teasers)[:4]],
            "note": "Lead tweet: single 16:9 cover crop, or the 4-image set. Mark media sensitive if "
                    "the platform requires it for this content.",
        },
        "instagram": {
            "cover_slide": {"source": cover, "w": 1080, "h": 1350, "gravity": "attention-center"},
            "carousel": [{"source": p, "w": 1080, "h": 1350, "gravity": "attention-center"}
                         for p in teasers],
            "note": "4:5 portrait maximizes feed real estate. IG is the strictest platform — SFW "
                    "crops only; when in doubt, crop tighter or drop the slide.",
        },
    }


def png_dimensions(path):
    """Read w,h from the PNG IHDR without any imaging dependency."""
    try:
        with open(path, "rb") as f:
            head = f.read(24)
        if head[:8] != b"\x89PNG\r\n\x1a\n" or head[12:16] != b"IHDR":
            return None
        w, h = struct.unpack(">II", head[16:24])
        return [w, h]
    except OSError:
        return None


def discover_pages(project, pages_dir_override):
    """Find the final page set. Returns (label, dir, sorted file list)."""
    candidates = []
    if pages_dir_override:
        candidates.append(("override:" + pages_dir_override, pages_dir_override))
    candidates += [
        ("final/", os.path.join(project, "final")),
        ("pages/lettered/", os.path.join(project, "pages", "lettered")),
        ("pages/ (page-NN)", os.path.join(project, "pages")),
    ]
    for label, d in candidates:
        if not os.path.isdir(d):
            continue
        files = sorted(
            f for f in glob.glob(os.path.join(d, "*.png"))
            if re.search(r"(p\d+|page[-_]?\d+)", os.path.basename(f), re.I)
        )
        if files:
            return label, d, files
    return None, None, []


def titleize(slug):
    return " ".join(w.capitalize() for w in re.split(r"[-_]+", slug) if w)


def add_months(d, months):
    m = d.month - 1 + months
    y, m = d.year + m // 12, m % 12 + 1
    import calendar
    return date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def fill(name):
    return "[FILL-%s — Claude drafts this from the shotlist during the skill run; human may edit]" % name


def build_captions(ctx):
    """Per-platform caption skeleton files. Auto-facts filled; prose left as [FILL-*] slots
    the SKILL workflow (Claude) completes from shotlist content before handing to the human."""
    t, prop = ctx["title"], ctx["prop"]
    cast = ", ".join(ctx["cast"]) if ctx["cast"] else "[cast]"
    base_tags = ["musclegrowth", "femalemusclegrowth", "fmg", "transformation", "comic", "3dcomic"]
    caps = {}
    caps["site"] = "\n".join([
        "# Site — catalogue copy",
        "",
        "**Title:** %s" % t,
        "**Issue:** %s · **Pages:** %d · **Property:** %s" % (ctx["issue"], ctx["page_count"], prop["label"]),
        "**Release:** %s · **Status:** paid (flips to free %s)" % (ctx["release_date"] or "[TBD]", ctx["flip_date"] or "[release+6mo]"),
        "",
        "**Synopsis (catalogue blurb, 2–3 sentences):**",
        fill("SYNOPSIS"),
        "",
        "**Slugs to register** (every URL you intend to hand out — runbook step 1a):",
        "- `%s`" % ctx["comic_id"],
        "- " + fill("EXTRA-SLUGS e.g. <id>-female-muscle-growth-comic"),
    ])
    caps["patreon"] = "\n".join([
        "# Patreon — %s" % prop["patreon"],
        "",
        "**Post title:** %s — new %d-page comic!" % (t, ctx["page_count"]),
        "**Access:** paid tiers (verify tier gating before publish)",
        "",
        "**Body:**",
        fill("PATREON-BODY: 2 short paragraphs — the hook, the growth payoff promise (no spoilers), what tier gets what"),
        "",
        "Read it here: [SITE-URL — from checklist step 1]",
        "",
        "**Attach:** patreon crop-spec images (header 1600x900 + cover/teasers full-res).",
        "**Tags:** " + ", ".join(base_tags),
    ])
    caps["deviantart"] = "\n".join([
        "# DeviantArt — %s" % prop["deviantart"],
        "",
        "**Deviation title:** %s (cover)" % t,
        "**Mature content:** ON",
        "",
        "**Description:**",
        fill("DA-BODY: hook + cast line (%s) + 'full %d-page comic at' + site/patreon links" % (cast, ctx["page_count"])),
        "",
        "**Tags:** " + ", ".join(base_tags + ["fmgcomic", "growth"]),
        "",
        "_DA is this property's biggest audience — this post matters most. Folder/gallery per house style._",
    ])
    caps["twitter"] = "\n".join([
        "# X / Twitter — %s" % prop["twitter"],
        "",
        "**Tweet (<=280 chars incl. link):**",
        fill("TWEET: one-line hook + emoji + link"),
        "",
        "**Media:** twitter crop-spec (single 16:9 cover, or 4-up set). Sensitive-media flag per content.",
        "**Hashtags (2-3 max):** #musclegrowth #fmg #comic",
    ])
    caps["instagram"] = "\n".join([
        "# Instagram — %s" % prop["instagram"],
        "",
        "**Caption:**",
        fill("IG-CAPTION: hook + 'link in bio' (IG strips URLs) + line breaks"),
        "",
        "**Media:** instagram crop-spec (4:5 cover slide + teaser carousel). STRICTEST platform — SFW slides only.",
        "**Hashtags (block at end, 10-15):** #musclegrowth #fmg #transformation #comicart #3dart "
        "#musclewoman #fitnessart #comics #digitalart #sequentialart",
    ])
    return caps


def build_checklist(ctx):
    """The destination-ordered human publish checklist — the bundle's centerpiece.
    Order: site (canonical home; everything else links to it) -> patreon (paying members)
    -> deviantart (biggest audience) -> twitter -> instagram, per the 2026-07-25
    posting-ops research and studio/posting.php's chip order."""
    p = ctx["prop"]
    qa_line = ("- [ ] QA report reviewed and re-render decisions made (`%s` — open findings are the "
               "owner's call, none block the path)" % ctx["qa_report"]) if ctx["qa_report"] else \
              "- [ ] QA/continuity pass confirmed done (no qa-report.md found in project)"
    L = [
        "# Publish checklist — %s" % ctx["title"],
        "",
        "**Property:** %s · **Pages:** %d (%s) · **Prepared:** %s · bundle v%d" % (
            p["label"], ctx["page_count"], ctx["pages_label"], ctx["prepared_at"][:10], BUNDLE_VERSION),
        "",
        "> 🖐 **Every checkbox below is a HUMAN action.** Nothing in this bundle has posted, uploaded,",
        "> or deployed anything. The pipeline prepares; you publish. (Per the never-post rule and",
        "> PRODUCTION-SYSTEM-VISION §5 — publish stays human-fired even in Run mode.)",
        "",
        "Platform order = canonical home first (everything links to it), then money, then reach:",
        "site → patreon → deviantart → twitter → instagram — matching the posting.php chips.",
        "",
        "## 0 · Preflight",
        qa_line,
        "- [ ] Final pages verified: %d/%s files in `%s`" % (
            ctx["page_count"], ctx["expected_pages"] or "?", ctx["pages_dir"]),
        "- [ ] Compiled PDF present: %s" % (ctx["pdf"] or "NO — compose one if a PDF deliverable is planned"),
        "- [ ] Captions reviewed — every `[FILL-*]` slot in `captions/` resolved, no placeholder text left",
        "- [ ] Board item exists on the 🗓 posting board (https://3dmusclecomics.com/studio/posting.php),"
        " lane = Monthly comic / %s" % p["label"],
        "",
        "## 1 · Site — the canonical home (do this FIRST; steps 2-5 link to it)",
        "- [ ] Follow `site-apply-notes.md` end to end (%s path)" % p["site_path"],
        "- [ ] Verify block: every line PASS (do not announce anywhere until it does)",
        "- [ ] Paid gating confirmed (`uploading: 0 pages` for a paid comic — runbook step 2)",
        "- [ ] **Record the live URL:** ____________________",
        "- [ ] posting.php chip `site` → posted",
        "",
        "## 2 · Patreon — paying members first (%s)" % p["patreon"],
        "- [ ] New post from `captions/patreon.md`; attach images per `crop-specs.json` → patreon",
        "- [ ] Tier gating correct; preview as a non-patron before publish",
        "- [ ] **Post URL:** ____________________ · chip `patreon` → posted",
        "",
        "## 3 · DeviantArt — biggest audience (%s)" % p["deviantart"],
        "- [ ] Deviation from `captions/deviantart.md`; MATURE flag ON; tags applied",
        "- [ ] **Deviation URL:** ____________________ · chip `deviantart` → posted",
        "",
        "## 4 · X / Twitter (%s)" % p["twitter"],
        "- [ ] Tweet from `captions/twitter.md`; media per crop-specs; sensitive flag as needed",
        "- [ ] **Tweet URL:** ____________________ · chip `twitter` → posted",
        "",
        "## 5 · Instagram (%s)" % p["instagram"],
        "- [ ] Post from `captions/instagram.md`; SFW slides only (strictest platform)",
        "- [ ] **Post URL:** ____________________ · chip `instagram` → posted",
        "",
        "## 6 · Aftermath — close the loop",
        "- [ ] Fill `posted.template.json` with the real URLs/dates above and save it as",
        "      `projects/%s/posting/posted.json` — **this file appearing is what marks the" % ctx["slug"],
        "      posting stage complete** to build-comic; commit it (it's project text)",
        "- [ ] Syndication ledger (comic-platform admin `syndication.html`): one entry per post,",
        "      WITH proof URL — after you post, never before (runbook step 6)",
        "- [ ] What's-New: `whats-new-draft.json` → prepend to live `admin/data/updates.json`",
        "      (only if this release touches a 3dmc surface the team should know about)",
        "- [ ] Schedule engagement capture: +7d and +30d passes into",
        "      `projects/%s/analytics/engagement-stub.json` (see skills/publisher/references/analytics-capture.md)" % ctx["slug"],
        "",
        "_Anything not applicable: set that platform's chip to n/a on the board and strike the section._",
    ]
    return "\n".join(L)


def build_site_apply_notes(ctx):
    p = ctx["prop"]
    common = [
        "# Site apply notes — %s → %s" % (ctx["title"], p["label"]),
        "",
        "_What to add where. Pointers into the runbook, pre-filled with this project's values._",
        "_Every step is run by the human (or by Claude WITH per-action approval) — this file only maps the path._",
        "",
    ]
    if p["site_path"] == "comic-platform":
        rel = ctx["release_date"] or "[YYYY-MM-DD]"
        body = [
            "**Runbook:** `~/Documents/comic-platform/docs/PUBLISH-A-COMIC.md` (walked 2026-07-30 with",
            "Not So Supra... Man — this skill mechanizes the PREP half; the runbook is the APPLY half).",
            "",
            "1. **Manifest** — `publish/%s/%s.json`:" % (ctx["property"], ctx["comic_id"]),
            "   ```json",
            json.dumps({
                "id": ctx["comic_id"], "property": ctx["property"], "title": ctx["title"],
                "issue": ctx["issue"], "series": ctx["comic_id"], "seriesTitle": ctx["title"],
                "releaseDate": rel, "status": "paid",
                "slugs": [ctx["comic_id"]],
                "artworkDir": ctx["pages_dir"], "artworkGlob": "*.png",
            }, indent=2),
            "   ```",
            "   Add every slug you intend to hand out NOW (step 1a note) — e.g. the long-form",
            "   `%s-female-muscle-growth-comic` house shape." % ctx["comic_id"],
            "2. **Send:** `python3 tools/publish/new_comic.py publish/%s/%s.json --dry-run` — read the"
            % (ctx["property"], ctx["comic_id"]),
            "   `uploading: 0 pages` line (paid comics upload NO pages — structurally enforced), then run",
            "   without `--dry-run`, then `--verify-only` until every line is PASS.",
            "3. **Paywall check** (runbook step 2) — paid comic must have zero publicly fetchable pages.",
            "4. **Dialogue + translations** (steps 3-4) if this comic has balloons: OCR with",
            "   `tools/ocr/ocr_comic.py --local-dir %s`, review, then ONE translate subagent per language." % ctx["pages_dir"],
            "5. **URLs/SEO** (step 5) — verify slugs resolve; canonical/hreflang come from the router.",
            "6. **After posting elsewhere**, record syndication (step 6) — never before.",
            "7. **Flip reminder:** paid → free flip is release + 6 months = **%s**. The flip does NOT fire"
            % (ctx["flip_date"] or "[release+6mo]"),
            "   on its own (project_platform_flip_never_fires) — `tools/flip/flip_platform.py` runs monthly, human-driven.",
            "8. **WP side** (step 8) — the old system needs its matching post until cutover.",
        ]
        if ctx.get("already_on_staging"):
            body = ["> ⚠️ **This comic is ALREADY on comic-platform staging** (ingested 2026-07-30 per",
                    "> runbook Appendix A). Steps 1-5 are DONE — re-run `--verify-only` to confirm,",
                    "> then this file's remaining work is steps 6-8 + the WP-side post.", ""] + body
    else:  # 3dmc-admin
        body = [
            "**Path:** 3dmusclecomics.com admin CMS (https://3dmusclecomics.com/admin/).",
            "",
            "1. Admin → series: create/select the series for **%s**." % ctx["title"],
            "2. Add part → drag-drop the %d pages from `%s` (uploader chunks at 15 files/40MB" % (ctx["page_count"], ctx["pages_dir"]),
            "   automatically — sequential, don't parallel-drop).",
            "3. Set access (free / members + freeAfter date) per the release plan.",
            "4. Publish (or schedule) — the admin rewrites data/comics.js + feed.xml itself.",
            "5. What's-New: prepend `whats-new-draft.json` to admin/data/updates.json (read-modify-write,",
            "   NEVER write a fresh array — reference_whats_new_feed).",
        ]
    return "\n".join(common + body)


def build_whats_new_draft(ctx):
    slug = re.sub(r"[^a-z0-9-]", "", ctx["comic_id"].lower())
    return {
        "_draft_note": "DRAFT ONLY — not posted. Human (or approved session) prepends this to the LIVE "
                       "admin/data/updates.json per reference_whats_new_feed (read-modify-write, insert at "
                       "index 0, never overwrite the array). Set ts at post time.",
        "id": "upd-comic-%s" % slug,
        "type": "feature",
        "title": "New comic: %s (%d pages)" % (ctx["title"], ctx["page_count"]),
        "date": ctx["release_date"] or "[POST-DATE]",
        "pinned": False,
        "body": "**%s** is out — %d pages, %s.\n\n%s\n\n- Read: [SITE-URL]\n- Patreon: %s" % (
            ctx["title"], ctx["page_count"], ctx["prop"]["label"],
            fill("ONE-LINE-HOOK"), ctx["prop"]["patreon"]),
        "images": [],
        "author": "Claude (publisher bundle)",
        "ts": None,
    }


def build_posted_template(ctx):
    return {
        "_template_note": "FILL AND MOVE UP ONE LEVEL. This is a TEMPLATE — while it lives in bundle/ "
                          "nothing is posted. When you have actually posted, fill each entry (url, "
                          "posted_at, posted_by), delete or n/a the rest, set completed:true, and save "
                          "as projects/<p>/posting/posted.json. THAT file existing is build-comic.md's "
                          "'posting complete' sentinel — never create it before posting is real. "
                          "Schema: skills/publisher/references/posted-schema.json",
        "schema_version": 1,
        "project": ctx["slug"],
        "property": ctx["property"],
        "comic_id": ctx["comic_id"],
        "title": ctx["title"],
        "bundle_version": BUNDLE_VERSION,
        "prepared_at": ctx["prepared_at"],
        "completed": False,
        "posts": [
            {"platform": k, "status": "todo", "url": "", "posted_at": None,
             "posted_by": "", "scope": ("full" if k == "site" else "announcement"), "notes": ""}
            for k in PLATFORM_KEYS
        ],
    }


def build_engagement_stub(ctx):
    return {
        "_note": "Flywheel landing pad (Publisher → Ideator contract, VISION §4). Wiring is Wave-2; "
                 "capture is manual/wrapper-driven for now — see skills/publisher/references/"
                 "analytics-capture.md. NEVER read raw credential files; use ~/Documents/.credentials/bin/ "
                 "wrappers (ga, patreon) only. Schema: skills/publisher/references/engagement-stub-schema.json",
        "schema_version": 1,
        "project": ctx["slug"],
        "property": ctx["property"],
        "comic_id": ctx["comic_id"],
        "release_date": ctx["release_date"],
        "captures": [],
        "capture_plan": [
            {"when": "release +7d", "sources": ["ga4", "patreon", "deviantart", "twitter", "instagram"]},
            {"when": "release +30d", "sources": ["ga4", "patreon", "deviantart"]},
        ],
    }


def main():
    ap = argparse.ArgumentParser(description="Assemble the un-posted publish bundle for a finished comic. PREP ONLY — never posts.")
    ap.add_argument("--project", required=True, help="projects/<p> directory")
    ap.add_argument("--property", required=True, choices=sorted(PROPERTIES))
    ap.add_argument("--title", help="Display title (default: titleized slug)")
    ap.add_argument("--comic-id", help="URL id (default: project slug)")
    ap.add_argument("--issue", type=int, default=1)
    ap.add_argument("--release-date", help="YYYY-MM-DD if known/decided")
    ap.add_argument("--pages-dir", help="Override final-pages dir (e.g. when binaries live outside the checkout)")
    ap.add_argument("--aux-root", help="Alternate copy of the project root to ALSO scan for gitignored "
                                       "artifacts (*.pdf, qa-report.md) — e.g. the main checkout when "
                                       "running from a worktree")
    ap.add_argument("--already-on-staging", action="store_true",
                    help="Comic was already ingested to comic-platform (apply notes flip to verify-only mode)")
    ap.add_argument("--force", action="store_true", help="Overwrite an existing bundle")
    args = ap.parse_args()

    project = os.path.abspath(args.project)
    if not os.path.isdir(project):
        sys.exit("No such project dir: %s" % project)
    slug = os.path.basename(project.rstrip("/"))

    # Refuse to run if posting already happened — prep after the fact is nonsense.
    posted_path = os.path.join(project, "posting", "posted.json")
    if os.path.exists(posted_path) and not args.force:
        sys.exit("posting/posted.json already exists — this comic is posted. --force to re-prep anyway.")

    shotlist = {}
    sl_path = os.path.join(project, "shotlist.json")
    if os.path.exists(sl_path):
        try:
            shotlist = json.load(open(sl_path))
        except (ValueError, OSError) as e:
            print("WARN: shotlist.json unreadable (%s) — captions will be thinner" % e)

    pages_label, pages_dir, page_files = discover_pages(project, args.pages_dir)
    if not page_files:
        sys.exit("No final pages found (tried --pages-dir, final/, pages/lettered/, pages/). "
                 "The publisher runs AFTER review — there must be a finished page set.")

    pages = []
    for f in page_files:
        pages.append({"file": os.path.basename(f), "dims": png_dimensions(f)})

    expected = shotlist.get("page_count")
    if expected and expected != len(page_files):
        print("WARN: shotlist says %d pages, found %d files — checklist flags this" % (expected, len(page_files)))

    roots = [project] + ([os.path.abspath(args.aux_root)] if args.aux_root else [])
    pdfs = [p for r in roots for p in glob.glob(os.path.join(r, "*.pdf"))]
    qa_report = next((r for r in roots if os.path.exists(os.path.join(r, "qa-report.md"))), None)
    cover = pages[0]["file"]
    teasers = [p["file"] for p in pages[1:4]]

    cast = []
    for c in shotlist.get("cast", []):
        cast.append(c.get("name", c) if isinstance(c, dict) else str(c))

    rel = args.release_date
    flip = None
    if rel:
        try:
            flip = add_months(date.fromisoformat(rel), 6).isoformat()
        except ValueError:
            sys.exit("--release-date must be YYYY-MM-DD")

    ctx = {
        "slug": slug,
        "property": args.property,
        "prop": PROPERTIES[args.property],
        "title": args.title or titleize(slug),
        "comic_id": args.comic_id or slug,
        "issue": args.issue,
        "release_date": rel,
        "flip_date": flip,
        "page_count": len(page_files),
        "expected_pages": expected,
        "pages_label": pages_label,
        "pages_dir": pages_dir,
        "pdf": os.path.basename(pdfs[0]) if pdfs else None,
        "cast": cast,
        "qa_report": (os.path.join(qa_report, "qa-report.md") if qa_report and qa_report != project
                      else ("qa-report.md" if qa_report else None)),
        "prepared_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "already_on_staging": args.already_on_staging,
    }

    bundle = os.path.join(project, "posting", "bundle")
    if os.path.isdir(bundle) and os.listdir(bundle) and not args.force:
        sys.exit("Bundle already exists at %s — --force to regenerate." % bundle)
    os.makedirs(os.path.join(bundle, "captions"), exist_ok=True)
    os.makedirs(os.path.join(project, "analytics"), exist_ok=True)

    written = []

    def w(relpath, content):
        p = os.path.join(bundle, relpath) if not relpath.startswith("../") else \
            os.path.join(project, relpath[3:])
        with open(p, "w") as f:
            if isinstance(content, str):
                f.write(content.rstrip() + "\n")
            else:
                json.dump(content, f, indent=2, ensure_ascii=False)
                f.write("\n")
        written.append(os.path.relpath(p, project))

    w("CHECKLIST.md", build_checklist(ctx))
    for k, text in build_captions(ctx).items():
        w(os.path.join("captions", "%s.md" % k), text)
    w("crop-specs.json", crop_specs(cover, teasers))
    w("site-apply-notes.md", build_site_apply_notes(ctx))
    w("whats-new-draft.json", build_whats_new_draft(ctx))
    w("posted.template.json", build_posted_template(ctx))
    w("MANIFEST.json", {
        "_note": "Bundle inventory + provenance. Nothing here has been posted anywhere.",
        "bundle_version": BUNDLE_VERSION,
        "prepared_at": ctx["prepared_at"],
        "project": slug, "property": args.property, "comic_id": ctx["comic_id"],
        "title": ctx["title"], "release_date": rel, "flip_date": flip,
        "pages": {"count": len(pages), "source": pages_label, "dir": pages_dir,
                  "expected_from_shotlist": expected, "inventory": pages},
        "pdf": ctx["pdf"],
        "platform_order": PLATFORM_KEYS,
        "files": sorted(written),
    })

    stub_path = os.path.join(project, "analytics", "engagement-stub.json")
    if not os.path.exists(stub_path) or args.force:
        with open(stub_path, "w") as f:
            json.dump(build_engagement_stub(ctx), f, indent=2, ensure_ascii=False)
            f.write("\n")
        written.append(os.path.relpath(stub_path, project))

    print("Prepared publish bundle (NOTHING POSTED — human fires every platform):")
    for p in sorted(written):
        print("  " + p)
    print("\nNext: Claude fills the [FILL-*] caption slots per SKILL.md, then STOP — hand "
          "CHECKLIST.md to the human.")


if __name__ == "__main__":
    main()
