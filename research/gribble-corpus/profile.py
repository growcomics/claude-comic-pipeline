#!/usr/bin/env python3
"""Profile the Gribble script corpus into a structural fingerprint.

Gribble's scripts (53 .txt files in ~/Documents/gribble stories/) share one rigid
format:

    Page 3
    Panel 2- <art direction, prose>
    Susan- "dialogue"

This script parses every script, drops exact duplicates, and measures the things a
generator has to imitate to sound like him:

  * panels-per-page distribution     (the owner's note: it is NOT always 4)
  * growth density                   (share of pages that are transformation pages)
  * growth RUNS                      (consecutive growth pages = "pages of growth")
  * where growth sits in the arc     (normalized position of each growth page)
  * dialogue load                    (silent panels, lines per panel, words per line)
  * description length               (words per panel direction)
  * cast size + speaker distribution
  * SFX / escalation vocabulary

Output: gribble-profile.json (machine) + a printed human summary.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import statistics
import sys
from collections import Counter

CORPUS = os.path.expanduser("~/Documents/gribble stories")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gribble-profile.json")

PAGE_RE = re.compile(r"^\s*page\s*(\d+)\s*$", re.I)
# A "slot" header. Gribble writes either one panel per slot ("Panel 3- ...") or a
# MERGED block spanning several panels ("Panels 1, 2, 3 and 4- ..." / "(Full page
# panel)- ..."). The merged form is his transformation device, so the span must be
# captured, not flattened — matching only /panel (\d+)/ silently drops the plural
# form and mis-attributes the page.
PANEL_RE = re.compile(
    r"^\s*\(?\s*panels?\s*((?:\d+\s*(?:,|and|&|-|\+)?\s*)+)\)?\s*[-:.]\s*(.*)$", re.I)
FULLPAGE_RE = re.compile(r"^\s*\(?\s*full[- ]?page(?:\s+panel)?\s*\)?\s*[-:.]\s*(.*)$", re.I)
NUM_RE = re.compile(r"\d+")
# "Susan- \"line\"" or "Amy: \"line\"" — speaker is short, capitalized, no sentence punctuation
SPEAK_RE = re.compile(r"^\s*([A-Z][A-Za-z0-9'’.& /]{0,28}?)\s*[-:]\s*[\"“](.*)$")

# growth-IN-PROGRESS vocabulary: the transformation is happening on-panel
GROWTH = re.compile(
    r"\b(grow|growing|grew|grows|growth|swell|swelling|swells|expand|expanding|"
    r"bigger|larger|taller|bulge|bulging|balloon|ballooning|inflat|surg|"
    r"ripping|rips|tearing|tears|split|splitting|strain|straining|burst|bursting|"
    r"muscles?|muscular|bicep|triceps?|pecs?|abs\b|quads?|lats\b|physique|"
    r"transform|transformation|massive|enormous|huge|towering|gigantic)\b", re.I)
# tighter: active transformation, not just "she is muscular"
ACTIVE = re.compile(
    r"\b(grow|growing|grew|grows|growth|swell|swelling|swells|expand|expanding|"
    r"bulging|ballooning|inflating|surging|ripping|tearing|splitting|straining|"
    r"bursting|transform|transforming|getting (?:bigger|larger|taller)|"
    r"continues? to|even (?:bigger|larger|more))\b", re.I)
SFX_RE = re.compile(r"\b(SFX|sound effect|RIIIP|RIP+\b|KRAK|BOOM|CRASH|SNAP|POP)\b")


def read(path: str) -> str:
    with open(path, encoding="utf-8", errors="ignore") as fh:
        return fh.read().replace("﻿", "")


def parse(text: str) -> dict:
    """Return {title, pages: [[slot, ...], ...]}.

    slot = {span, desc, lines:[(who,what)], merged:bool} — span is how many panels
    of the page's grid the slot occupies (1 for a normal panel, 2-4 for a merged
    growth block, 4 for a declared full-page panel).
    """
    lines = text.splitlines()
    title = ""
    for ln in lines[:6]:
        s = ln.strip()
        if s and not s.lower().startswith("by "):
            title = s
            break

    pages: list[list[dict]] = []
    cur_page: list[dict] | None = None
    cur_panel: dict | None = None

    for raw in lines:
        s = raw.strip()
        if not s:
            continue
        m = PAGE_RE.match(s)
        if m:
            if cur_page is not None:
                pages.append(cur_page)
            cur_page = []
            cur_panel = None
            continue
        m = FULLPAGE_RE.match(s)
        if m:
            if cur_page is None:
                cur_page = []
            cur_panel = {"desc": m.group(1).strip(), "lines": [], "span": 4,
                         "merged": True, "fullpage": True}
            cur_page.append(cur_panel)
            continue
        m = PANEL_RE.match(s)
        if m:
            if cur_page is None:          # panels before any "Page" header
                cur_page = []
            span = max(1, len(NUM_RE.findall(m.group(1))))
            cur_panel = {"desc": m.group(2).strip(), "lines": [], "span": span,
                         "merged": span > 1, "fullpage": False}
            cur_page.append(cur_panel)
            continue
        if cur_panel is None:
            continue
        m = SPEAK_RE.match(s)
        if m:
            who = m.group(1).strip().rstrip("-:")
            what = m.group(2).rstrip().rstrip('"”')
            cur_panel["lines"].append((who, what))
        else:
            cur_panel["desc"] = (cur_panel["desc"] + " " + s).strip()

    if cur_page:
        pages.append(cur_page)
    return {"title": title, "pages": [p for p in pages if p]}


def page_text(page: list[dict]) -> str:
    return " ".join(p["desc"] + " " + " ".join(w for _, w in p["lines"]) for p in page)


def main() -> int:
    seen: set[str] = set()
    scripts = []
    for fn in sorted(os.listdir(CORPUS)):
        if not fn.endswith(".txt"):
            continue
        text = read(os.path.join(CORPUS, fn))
        h = hashlib.sha1(text.encode("utf-8", "ignore")).hexdigest()
        if h in seen:                      # Crown of Abuul x3, Gamma Babes x2, ...
            continue
        seen.add(h)
        doc = parse(text)
        if len(doc["pages"]) < 4:          # prose pieces with no page/panel markup
            continue
        doc["file"] = fn
        scripts.append(doc)

    ppp = Counter()                        # panels per page (sum of slot spans)
    spp = Counter()                        # SLOTS per page (drawn frames)
    layouts = Counter()                    # span signature, e.g. (1,1,1,1) or (4,)
    per_script = []
    growth_runs_all = []
    growth_pos_all = []
    desc_words = []
    lines_per_panel = []
    line_words = []
    silent = 0
    total_panels = 0
    total_slots = 0
    merged_slots = 0
    merged_growth = 0                      # merged slots whose text is growth
    single_growth = 0
    single_slots = 0
    merged_pages = 0
    speakers_per_script = []
    first_growth_frac = []

    def is_growth(txt: str) -> bool:
        return len(ACTIVE.findall(txt)) >= 2 or (
            len(ACTIVE.findall(txt)) >= 1 and len(GROWTH.findall(txt)) >= 3)

    for doc in scripts:
        pages = doc["pages"]
        n = len(pages)
        gflags = []
        for i, page in enumerate(pages):
            spans = [p.get("span", 1) for p in page]
            ppp[sum(spans)] += 1
            spp[len(page)] += 1
            layouts[tuple(spans)] += 1
            if any(s > 1 for s in spans):
                merged_pages += 1
            txt = page_text(page)
            # a growth page = transformation actively depicted, OR a merged block
            # (Gribble merges the grid precisely to stage a transformation)
            g = is_growth(txt) or (any(s > 1 for s in spans) and len(GROWTH.findall(txt)) >= 1)
            gflags.append(g)
            if g:
                growth_pos_all.append(round((i + 0.5) / n, 3))
            for p in page:
                total_slots += 1
                total_panels += p.get("span", 1)
                if p.get("span", 1) > 1:
                    merged_slots += 1
                    if is_growth(p["desc"]) or len(GROWTH.findall(p["desc"])) >= 1:
                        merged_growth += 1
                else:
                    single_slots += 1
                    if is_growth(p["desc"]):
                        single_growth += 1
                desc_words.append(len(p["desc"].split()))
                lines_per_panel.append(len(p["lines"]))
                if not p["lines"]:
                    silent += 1
                for _, what in p["lines"]:
                    line_words.append(len(what.split()))

        # consecutive growth pages
        runs, cur = [], 0
        for g in gflags:
            if g:
                cur += 1
            elif cur:
                runs.append(cur)
                cur = 0
        if cur:
            runs.append(cur)
        growth_runs_all += runs

        gp = sum(gflags)
        if gp:
            first_growth_frac.append(round((gflags.index(True) + 1) / n, 3))

        spk = Counter()
        for page in pages:
            for p in page:
                for who, _ in p["lines"]:
                    spk[who] += 1
        speakers_per_script.append(len([s for s, c in spk.items() if c >= 3]))

        per_script.append({
            "file": doc["file"], "title": doc["title"], "pages": n,
            "panels": sum(p.get("span", 1) for pg in pages for p in pg),
            "merged_pages": sum(1 for pg in pages if any(p.get("span", 1) > 1 for p in pg)),
            "growth_pages": gp, "growth_ratio": round(gp / n, 3),
            "growth_runs": runs, "longest_run": max(runs) if runs else 0,
            "cast": len([s for s, c in spk.items() if c >= 3]),
        })

    def pct(c: Counter, k) -> float:
        return round(100.0 * c[k] / sum(c.values()), 1)

    tot_pages = sum(ppp.values())
    dist = {str(k): {"pages": v, "pct": round(100.0 * v / tot_pages, 1)}
            for k, v in sorted(ppp.items()) if k <= 12}
    lay = {"+".join(str(x) for x in k): {"pages": v, "pct": round(100.0 * v / tot_pages, 1)}
           for k, v in layouts.most_common(14)}

    profile = {
        "corpus": {"files": len(scripts), "pages": tot_pages, "panels": total_panels,
                   "slots": total_slots},
        "panels_per_page": {
            "distribution": dist,
            "mean": round(statistics.mean(ppp.elements()), 2),
            "median": statistics.median(sorted(ppp.elements())),
            "mode": ppp.most_common(1)[0][0],
            "pct_exactly_4": pct(ppp, 4),
            "pct_3_to_5": round(pct(ppp, 3) + pct(ppp, 4) + pct(ppp, 5), 1),
        },
        "layout": {
            "signatures": lay,
            "slots_per_page_mean": round(statistics.mean(spp.elements()), 2),
            "merged_page_pct": round(100.0 * merged_pages / tot_pages, 1),
            "merged_slot_pct": round(100.0 * merged_slots / total_slots, 1),
            "merged_slot_growth_pct": round(100.0 * merged_growth / merged_slots, 1) if merged_slots else 0,
            "single_slot_growth_pct": round(100.0 * single_growth / single_slots, 1) if single_slots else 0,
        },
        "growth": {
            "page_ratio_mean": round(statistics.mean(s["growth_ratio"] for s in per_script), 3),
            "page_ratio_median": round(statistics.median(s["growth_ratio"] for s in per_script), 3),
            "run_len_mean": round(statistics.mean(growth_runs_all), 2) if growth_runs_all else 0,
            "run_len_max": max(growth_runs_all) if growth_runs_all else 0,
            "runs_per_script_mean": round(len(growth_runs_all) / len(scripts), 2),
            "runs_ge_3_pages_pct": round(100.0 * len([r for r in growth_runs_all if r >= 3]) / len(growth_runs_all), 1) if growth_runs_all else 0,
            "first_growth_at_frac_median": round(statistics.median(first_growth_frac), 3) if first_growth_frac else None,
            "position_histogram": {
                f"{lo/10:.1f}-{(lo+1)/10:.1f}": len([p for p in growth_pos_all if lo/10 <= p < (lo+1)/10])
                for lo in range(10)
            },
        },
        "dialogue": {
            "silent_panel_pct": round(100.0 * silent / total_panels, 1),
            "lines_per_panel_mean": round(statistics.mean(lines_per_panel), 2),
            "words_per_line_mean": round(statistics.mean(line_words), 1),
            "words_per_line_median": statistics.median(line_words),
            "long_lines_over_25w_pct": round(100.0 * len([w for w in line_words if w > 25]) / len(line_words), 1),
        },
        "description": {
            "words_per_panel_mean": round(statistics.mean(desc_words), 1),
            "words_per_panel_median": statistics.median(desc_words),
            "p90": sorted(desc_words)[int(0.9 * len(desc_words))],
        },
        "cast": {
            "named_speakers_mean": round(statistics.mean(speakers_per_script), 2),
            "named_speakers_median": statistics.median(speakers_per_script),
        },
        "scripts": sorted(per_script, key=lambda s: -s["pages"]),
    }

    with open(OUT, "w") as fh:
        json.dump(profile, fh, indent=2)

    p = profile
    print(f"corpus: {p['corpus']['files']} scripts · {p['corpus']['pages']} pages · {p['corpus']['panels']} panels")
    print("\nPANELS PER PAGE")
    for k, v in p["panels_per_page"]["distribution"].items():
        print(f"  {k:>2} panels  {v['pages']:5d} pages  {v['pct']:5.1f}%  {'#' * int(v['pct'] / 2)}")
    print(f"  mean {p['panels_per_page']['mean']} · median {p['panels_per_page']['median']} · "
          f"exactly-4 = {p['panels_per_page']['pct_exactly_4']}%")
    print("\nPAGE LAYOUT (slot spans — 1+1+1+1 = normal grid, 4 = merged full page)")
    for k, v in p["layout"]["signatures"].items():
        print(f"  {k:<12} {v['pages']:5d} pages  {v['pct']:5.1f}%")
    print(f"  merged-layout pages: {p['layout']['merged_page_pct']}% · "
          f"merged slots that are GROWTH: {p['layout']['merged_slot_growth_pct']}% "
          f"vs single panels {p['layout']['single_slot_growth_pct']}%")
    print("\nGROWTH")
    for k, v in p["growth"].items():
        if k != "position_histogram":
            print(f"  {k}: {v}")
    print("  position histogram (start→end of script):")
    for k, v in p["growth"]["position_histogram"].items():
        print(f"    {k}  {v:4d}  {'#' * int(v / 4)}")
    print("\nDIALOGUE"); [print(f"  {k}: {v}") for k, v in p["dialogue"].items()]
    print("\nDESCRIPTION"); [print(f"  {k}: {v}") for k, v in p["description"].items()]
    print("\nCAST"); [print(f"  {k}: {v}") for k, v in p["cast"].items()]
    print("\ntop scripts by growth ratio:")
    for s in sorted(per_script, key=lambda s: -s["growth_ratio"])[:8]:
        print(f"  {s['growth_ratio']:.2f}  runs={s['growth_runs']}  {s['pages']}pp  {s['title'][:44]}")
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
