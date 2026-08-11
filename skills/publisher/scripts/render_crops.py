#!/usr/bin/env python3
"""
render_crops.py — Stage 7 (PUBLISHER) Wave-2 crop renderer.  LOCAL ONLY.

Executes posting/bundle/crop-specs.json (written by prepare_post.py) into real
media files under posting/bundle/crops/<platform>/ so the human has a ready
per-platform upload kit sitting next to CHECKLIST.md.

  crop entries   ({source, w, h, gravity}) — center-crop v1: the largest region
      at the target aspect around the geometric center ("attention-center"
      subject detection is a later wave), downscaled to the spec size.  If the
      spec is LARGER than the source allows, the output keeps native resolution
      at the target aspect instead of upscaling (platforms scale up better than
      Lanczos does on CGI renders); --allow-upscale forces exact spec pixels.
      Either way the actual dimensions land in crops/RENDER-MANIFEST.json.
  native entries ({source, treatment: "native..."} and plain filename lists)
      — verbatim copies, so crops/<platform>/ is the complete media set for
      that platform (--skip-native to render true crops only).
  site           ("treatment": "native", "pages": "all") — nothing to render,
      by design: the reader serves full-resolution pages.

NEVER COMMITTED, NEVER POSTED
  Rendered files are project BINARIES: .gitignore excludes
  projects/*/posting/bundle/crops/ entirely (CLAUDE.md rule 5) — everything in
  crops/ is re-renderable from the committed specs + the page set.
  This script takes no outward action: it imports no urllib/requests/socket;
  subprocess exists solely to exec the LOCAL /usr/bin/sips binary when Pillow
  is unavailable.  It reads the final page set and writes under crops/ — that
  is all.  Publishing stays a human act (SKILL.md, THE RULE).

Usage:
  python3 skills/publisher/scripts/render_crops.py --project projects/<p> \
      [--pages-dir <dir>] [--engine auto|pillow|sips] [--allow-upscale] \
      [--skip-native] [--out-dir <dir>] [--force]
"""

import argparse
import json
import os
import shutil
import subprocess  # ONLY for the local /usr/bin/sips fallback — never network
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prepare_post import discover_pages

try:
    from PIL import Image
    HAVE_PIL = True
except ImportError:
    HAVE_PIL = False

SIPS = "/usr/bin/sips"
SKIP_KEYS = {"note", "_note", "treatment", "pages"}  # spec prose / by-design-native markers


def utcnow():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def crop_box(sw, sh, tw, th):
    """Largest centered region of (sw,sh) at aspect tw:th. v1 'attention-center' = center."""
    if sw * th >= sh * tw:  # source wider than target aspect — full height
        ch, cw = sh, min(sw, round(sh * tw / th))
    else:                   # source taller — full width
        cw, ch = sw, min(sh, round(sw * th / tw))
    left, top = (sw - cw) // 2, (sh - ch) // 2
    return left, top, cw, ch


def sips_run(args):
    r = subprocess.run([SIPS] + args, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("sips failed (%s): %s" % (" ".join(args[:2]), (r.stderr or r.stdout).strip()[:300]))
    return r.stdout


def sips_dims(path):
    out = sips_run(["-g", "pixelWidth", "-g", "pixelHeight", path])
    vals = {}
    for line in out.splitlines():
        parts = line.split(":")
        if len(parts) == 2 and parts[0].strip() in ("pixelWidth", "pixelHeight"):
            vals[parts[0].strip()] = int(parts[1])
    return vals["pixelWidth"], vals["pixelHeight"]


def render_crop_pillow(src, dst, tw, th, allow_upscale):
    img = Image.open(src)
    if img.mode == "P":
        img = img.convert("RGBA")
    sw, sh = img.size
    left, top, cw, ch = crop_box(sw, sh, tw, th)
    region = img.crop((left, top, left + cw, top + ch))
    if cw >= tw or allow_upscale:
        region = region.resize((tw, th), Image.LANCZOS)
    icc = img.info.get("icc_profile")
    region.save(dst, **({"icc_profile": icc} if icc else {}))
    return region.size


def render_crop_sips(src, dst, tw, th, allow_upscale):
    sw, sh = sips_dims(src)
    _, _, cw, ch = crop_box(sw, sh, tw, th)
    shutil.copy2(src, dst)
    sips_run(["--cropToHeightWidth", str(ch), str(cw), dst])  # sips crops around center
    if cw >= tw or allow_upscale:
        sips_run(["--resampleHeightWidth", str(th), str(tw), dst])
        return tw, th
    return cw, ch


def plan_jobs(specs):
    """Walk the spec file generically: dicts with w+h render as crops, native
    picks (treatment dicts / bare filename lists) copy verbatim, prose keys skip.
    Anything unrecognized is REPORTED, never silently dropped."""
    jobs, skips = [], []
    for platform, spec in specs.items():
        if platform.startswith("_"):
            continue
        if not isinstance(spec, dict):
            skips.append({"platform": platform, "entry": None, "reason": "unrecognized platform value"})
            continue
        renderable = [k for k in spec if k not in SKIP_KEYS]
        if not renderable:
            skips.append({"platform": platform, "entry": None,
                          "reason": "native by design — no files to render (reader serves full pages)"})
            continue
        for key in renderable:
            val = spec[key]
            items = list(enumerate(val, 1)) if isinstance(val, list) else [(None, val)]
            for idx, item in items:
                if isinstance(item, str):
                    jobs.append({"platform": platform, "key": key, "index": idx,
                                 "mode": "copy", "source": item, "w": None, "h": None})
                elif isinstance(item, dict) and "source" in item:
                    if isinstance(item.get("w"), int) and isinstance(item.get("h"), int):
                        jobs.append({"platform": platform, "key": key, "index": idx,
                                     "mode": "crop", "source": item["source"],
                                     "w": item["w"], "h": item["h"]})
                    else:
                        jobs.append({"platform": platform, "key": key, "index": idx,
                                     "mode": "copy", "source": item["source"], "w": None, "h": None})
                else:
                    skips.append({"platform": platform, "entry": "%s[%s]" % (key, idx),
                                  "reason": "unrecognized entry shape — NOT rendered"})
    return jobs, skips


def resolve_pages_dir(project, override):
    if override:
        return os.path.abspath(override)
    man_path = os.path.join(project, "posting", "bundle", "MANIFEST.json")
    if os.path.exists(man_path):
        try:
            d = json.load(open(man_path)).get("pages", {}).get("dir")
            if d and os.path.isdir(d):
                return d
        except (ValueError, OSError):
            pass
    _, d, files = discover_pages(project, None)
    return d if files else None


def main():
    ap = argparse.ArgumentParser(description="Render posting/bundle/crop-specs.json into local files "
                                             "under posting/bundle/crops/. LOCAL ONLY — never posts, "
                                             "outputs are gitignored binaries.")
    ap.add_argument("--project", required=True, help="projects/<p> directory")
    ap.add_argument("--pages-dir", help="Final-pages dir (default: bundle MANIFEST's recorded dir, "
                                        "then final/, pages/lettered/, pages/)")
    ap.add_argument("--engine", choices=["auto", "pillow", "sips"], default="auto")
    ap.add_argument("--allow-upscale", action="store_true",
                    help="Force exact spec dimensions even when that upscales the source")
    ap.add_argument("--skip-native", action="store_true",
                    help="Render true crops only; skip verbatim copies of native/full-res picks")
    ap.add_argument("--out-dir", help="Override output dir (default: <project>/posting/bundle/crops)")
    ap.add_argument("--force", action="store_true", help="Render into a non-empty crops/ dir")
    args = ap.parse_args()

    project = os.path.abspath(args.project)
    specs_path = os.path.join(project, "posting", "bundle", "crop-specs.json")
    if not os.path.exists(specs_path):
        sys.exit("No crop-specs.json at %s — run prepare_post.py first." % specs_path)
    specs = json.load(open(specs_path))

    engine = args.engine
    if engine == "auto":
        engine = "pillow" if HAVE_PIL else "sips"
    if engine == "pillow" and not HAVE_PIL:
        sys.exit("Pillow not importable — install it or use --engine sips.")
    if engine == "sips" and not os.path.exists(SIPS):
        sys.exit("%s not found (macOS only) — install Pillow instead." % SIPS)

    pages_dir = resolve_pages_dir(project, args.pages_dir)
    if not pages_dir:
        sys.exit("No page set found — pass --pages-dir (binaries often live outside the checkout).")

    out_dir = os.path.abspath(args.out_dir) if args.out_dir else os.path.join(project, "posting", "bundle", "crops")
    if os.path.isdir(out_dir) and any(f != "RENDER-MANIFEST.json" for f in os.listdir(out_dir)) and not args.force:
        sys.exit("crops/ already has files at %s — --force to re-render over them (files this run "
                 "doesn't produce are reported as stale, never deleted)." % out_dir)

    jobs, skips = plan_jobs(specs)
    render_crop = render_crop_pillow if engine == "pillow" else render_crop_sips

    results, errors, produced = [], [], set()
    for job in jobs:
        src = os.path.join(pages_dir, job["source"])
        rec = {"platform": job["platform"], "key": job["key"], "index": job["index"],
               "mode": job["mode"], "source": job["source"],
               "requested": [job["w"], job["h"]] if job["mode"] == "crop" else None}
        if not os.path.exists(src):
            rec["error"] = "source not found in pages dir"
            errors.append(rec)
            continue
        pdir = os.path.join(out_dir, job["platform"])
        os.makedirs(pdir, exist_ok=True)
        stem = os.path.splitext(os.path.basename(job["source"]))[0]
        try:
            if job["mode"] == "copy":
                if args.skip_native:
                    rec["note"] = "native copy skipped (--skip-native)"
                    results.append(rec)
                    continue
                name = os.path.basename(job["source"])
                shutil.copy2(src, os.path.join(pdir, name))
                rec["file"] = os.path.join(job["platform"], name)
            else:
                name = "%s%s-%s-%dx%d.png" % (job["key"], "-%02d" % job["index"] if job["index"] else "",
                                              stem, job["w"], job["h"])
                aw, ah = render_crop(src, os.path.join(pdir, name), job["w"], job["h"], args.allow_upscale)
                rec["file"] = os.path.join(job["platform"], name)
                rec["actual"] = [aw, ah]
                if [aw, ah] != [job["w"], job["h"]]:
                    rec["note"] = "kept native resolution at target aspect (upscale avoided; --allow-upscale to force)"
            produced.add(rec.get("file"))
            results.append(rec)
        except Exception as e:  # keep going — every failure is reported at the end
            rec["error"] = str(e)[:300]
            errors.append(rec)

    stale = []
    for root, _dirs, files in os.walk(out_dir):
        for f in files:
            rel = os.path.relpath(os.path.join(root, f), out_dir)
            if rel != "RENDER-MANIFEST.json" and rel not in produced:
                stale.append(rel)

    manifest = {
        "_note": "Provenance for LOCALLY RENDERED media. Everything under crops/ is a gitignored, "
                 "re-renderable binary (specs + pages are the committed truth). Nothing here has "
                 "been posted anywhere.",
        "rendered_at": utcnow(),
        "engine": engine,
        "project": os.path.basename(project.rstrip("/")),
        "pages_dir": pages_dir,
        "specs": os.path.relpath(specs_path, project),
        "allow_upscale": args.allow_upscale,
        "results": results,
        "skipped": skips,
        "errors": errors,
        "stale_files_not_from_this_run": stale,
    }
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "RENDER-MANIFEST.json"), "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
        f.write("\n")

    n_crops = sum(1 for r in results if r["mode"] == "crop" and "file" in r)
    n_copies = sum(1 for r in results if r["mode"] == "copy" and "file" in r)
    print("Rendered %d crops + %d native copies -> %s  (engine: %s)" % (n_crops, n_copies, out_dir, engine))
    for r in results:
        if "file" in r:
            dims = "%dx%d" % tuple(r["actual"]) if r.get("actual") else "native"
            flag = "  [native-res fallback]" if r.get("note", "").startswith("kept native") else ""
            print("  %-11s %-28s %s%s" % (r["platform"], r["file"].split("/", 1)[-1], dims, flag))
    for s in skips:
        print("  skip: %s — %s" % (s["platform"] + (":" + s["entry"] if s.get("entry") else ""), s["reason"]))
    if stale:
        print("  STALE (earlier render, not produced this run, NOT deleted): %s" % ", ".join(stale))
    for e in errors:
        print("  ERROR: %s/%s %s — %s" % (e["platform"], e["key"], e["source"], e["error"]))
    print("Reminder: crops/ is gitignored — these binaries are never committed, and nothing was posted.")
    sys.exit(2 if errors else 0)


if __name__ == "__main__":
    main()
