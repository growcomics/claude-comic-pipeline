#!/usr/bin/env python3
"""validate_script.py — mechanical gate for the Writer stage (Stage 2).

Validates a `script.md` written to skills/writer/references/script-format.md:

  HARD (exit 1)  parse errors / contract gaps; growth-density under the
                 chapter-type floor; L13 dialogue violations (>25-word balloons,
                 >=3 on-screen lines from >=2 speakers on one panel); tier curve
                 not monotonic or violating the declared start/end; missing
                 transformation-scene decomposition (setup / declared regions /
                 reveal); growth beats outside any declared scene; body-region
                 beats annotated at full-or-wider camera; coverage violations
                 when ALWAYS-CLOTHED; unknown beat/staging vocabulary.
  SOFT           late first growth; <2 growth scenes with 3+ growth panels;
                 faceless body-region runs (L35); wide-camera dialogue (L12);
                 camera-aggregate drift (L20 pre-check); background-extras
                 smells; capstone repetition; device shortfalls; zero silent
                 panels.

Floors and thresholds are anchored to measured sources (corpus chapter-type
table via script-breakdown SKILL.md §4.6; Gribble structural profile via
studio/gribble.php GR_FORMULA; L-lesson thresholds mirrored from
skills/continuity-check/scripts/rules_audit.py). Per the gribble.php
calibration doctrine (see references/gribble-alignment.md): if a rule rejects
known-good scripts, recalibrate that rule against the corpus — never bypass
the gate.

Usage:
    python3 validate_script.py <script.md> [--json]

Exit 0 = clean (warnings allowed) · 1 = HARD failures · 2 = usage.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# --------------------------------------------------------------------------
# Canonical vocabularies (mirror script-breakdown SKILL.md / rules_audit.py —
# keep in sync; the shotlist gates are the downstream source of truth)

SETUP_BEATS = {"consider", "decide", "trigger", "first_sensation"}
BODY_REGION_BEATS = {"chest", "hips", "rear", "arms", "abs", "legs",
                     "back", "shoulders", "suit_fail", "whole_body"}
RESOLUTION_BEATS = {"reveal", "aftermath"}
ALL_BEATS = SETUP_BEATS | BODY_REGION_BEATS | RESOLUTION_BEATS
# A page is a growth page when any panel carries one of these (L35 §4.6):
GROWTH_BEATS = {"trigger", "first_sensation", "reveal"} | BODY_REGION_BEATS

CHAPTER_FLOORS = {"transformation": 0.60, "climax": 0.70,
                  "origin": 0.45, "mixed": 0.45, "action": 0.30}

DEVICES = {"sfx-driven", "reaction-intercut", "full-body-reveal",
           "size-comparison", "multi-panel-progressive", "zoom-escalation",
           "clothing-destruction", "slow-burn"}

STAGING_VALUES = {"tension-block", "depth-staged", "triangular",
                  "negative-space-asymmetric", "foreground-occlusion",
                  "parallel-acceptable"}

# L39 situation registers (mirror comic-production/references/
# situation-expression-registers.md + script-breakdown SKILL.md §4.8)
REGISTERS = {"showcase", "celebratory", "confrontation", "mid-action",
             "surprise-reveal", "aftermath-victory", "aftermath-defeat",
             "dialogue-tense", "intimate"}
CELEBRATION_REGISTERS = {"showcase", "celebratory"}

SIZES = {"splash", "wide", "tall", "standard"}

ON_SCREEN_TYPES = {"balloon", "thought", "whisper", "shout"}
DIALOGUE_TYPES = ON_SCREEN_TYPES | {"off-panel"}

# Distance scoring mirrors rules_audit.DISTANCE_SCORE (cowboy intentionally
# absent — Gate A rejects it as a head token; see script-format.md §9).
DISTANCE_SCORE = {"ecu-face": 0, "ecu-region": 1, "mcu": 2, "medium": 3,
                  "full": 5, "wide-establish": 6, "splash": 5}
MIDDLE_DISTANCES = {"mcu", "medium"}
WIDE_OR_FULL = {"full", "wide-establish", "splash"}
ANGLES = {"eye-level", "low-angle-front", "low-angle-back", "high-angle",
          "worms-eye", "birds-eye", "dutch", "over-shoulder", "profile",
          "three-quarter"}
MEAN_DISTANCE_MAX_TRANSFORMATION = 2.5
MIDDLE_FRAC_MIN = 0.30
SAME_COMBO_MAX = 3

LOCATION_STRATEGIES = {"single", "multi", "per-scene"}
FLAVORS = {"body-region-progression", "single-axis", "other"}
CHAPTER_TYPES = set(CHAPTER_FLOORS)
ENDINGS = {"landed", "cliffhanger"}

STUB_VALUES = {"tbd", "todo", "n/a", "none", "-", "?"}

COVERAGE_HARD_RE = re.compile(
    r"\b(naked|nude|topless|nipples?|areolae?|bare-breasted"
    r"|fully exposed|tears? (?:away|off) (?:entirely|completely))\b", re.I)
COVERAGE_SOFT_RE = re.compile(r"\b(shirtless|bare-chested)\b", re.I)
EXTRAS_RE = re.compile(
    r"\b(crowds?|onlookers?|bystanders?|passers-?by|patrons|spectators"
    r"|audience|people)\b", re.I)

DIALOGUE_RE = re.compile(
    r"^([A-Z][A-Z0-9 .'\-]{0,30}?)\s*\((balloon|thought|whisper|shout|off-panel)\)"
    r"\s*:\s*[\"“](.*)[\"”]\s*$")
DIALOGUE_SHAPE_RE = re.compile(r"^[A-Z][A-Z0-9 .'\-]{0,30}?\s*\([^)]*\)\s*:")
PANEL_RE = re.compile(r"^PANEL\s+(\d+)\.(\d+)((?:\s*\[[^\]]+\])*)\s*$")
ANNOT_RE = re.compile(r"\[\s*([a-z]+)\s*:\s*([^\]]+?)\s*\]")
PAGE_RE = re.compile(r"^##\s+Page\s+(\d+)\s*(?:·\s*(.*))?$")
ARROW_SPLIT = re.compile(r"\s*(?:→|->)\s*")
DASH_SPLIT = re.compile(r"\s+(?:—|--)\s+")
DOT_SPLIT = re.compile(r"\s*[·|]\s*")
RANGE_RE = re.compile(r"pages?\s+(\d+)\s*(?:–|—|-|to)\s*(\d+)", re.I)
WORD_RE = re.compile(r"[a-z']{3,}")


def words(text: str) -> int:
    return len(text.split())


class Findings:
    def __init__(self):
        self.rows: list[dict] = []

    def hard(self, code, where, msg):
        self.rows.append({"severity": "hard", "code": code, "where": where, "message": msg})

    def soft(self, code, where, msg):
        self.rows.append({"severity": "soft", "code": code, "where": where, "message": msg})

    @property
    def hard_count(self):
        return sum(1 for r in self.rows if r["severity"] == "hard")


# --------------------------------------------------------------------------
# Parse

def parse_script(text: str, f: Findings) -> dict:
    doc = {"title": None, "synopsis": None, "header": {}, "tier_curves": {},
           "spine": {}, "cast": [], "locations": [], "props": [],
           "scenes": [], "pages": []}
    lines = text.splitlines()
    section = None          # header | spine | cast | locations | props | scenes | notes | page
    page = None
    panel = None

    def close_panel():
        nonlocal panel
        if panel is not None:
            page["panels"].append(panel)
            panel = None

    def close_page():
        nonlocal page
        close_panel()
        if page is not None:
            doc["pages"].append(page)
            page = None

    for ln, raw in enumerate(lines, 1):
        line = raw.rstrip()
        stripped = line.strip()

        if stripped.startswith("# ") and doc["title"] is None and not stripped.startswith("## "):
            doc["title"] = stripped[2:].strip()
            section = "synopsis"
            continue

        m = PAGE_RE.match(stripped)
        if m:
            close_page()
            section = "page"
            meta = m.group(2) or ""
            flags = {"growth": False, "splash": False, "scene": None}
            for part in DOT_SPLIT.split(meta):
                part = part.strip()
                if not part:
                    continue
                low = part.lower()
                if low == "growth":
                    flags["growth"] = True
                elif low == "splash":
                    flags["splash"] = True
                elif low.startswith("scene:"):
                    flags["scene"] = part.split(":", 1)[1].strip()
                else:
                    f.soft("page-flag", f"line {ln}", f"unknown page flag {part!r}")
            page = {"n": int(m.group(1)), "line": ln, "panels": [], **flags}
            continue

        if stripped.startswith("## Header"):
            close_page(); section = "header"; continue
        if stripped.startswith("### Story spine"):
            section = "spine"; continue
        if stripped.startswith("### Cast"):
            section = "cast"; continue
        if stripped.startswith("### Locations"):
            section = "locations"; continue
        if stripped.startswith("### Props"):
            section = "props"; continue
        if stripped.startswith("### Transformation scenes"):
            section = "scenes"; continue
        if stripped.startswith("### Notes"):
            section = "notes"; continue
        if stripped.startswith("### ") or stripped.startswith("## "):
            f.soft("section", f"line {ln}", f"unrecognized section header {stripped!r}")
            section = None
            continue

        if not stripped:
            continue

        if section == "synopsis":
            doc["synopsis"] = stripped
            section = None
            continue

        if section in ("header", "spine"):
            km = re.match(r"^([A-Z][A-Z0-9\- ]+):\s*(.*)$", stripped)
            if not km:
                f.soft("header", f"line {ln}", f"unparsed line in {section}: {stripped!r}")
                continue
            key, val = km.group(1).strip().upper(), km.group(2).strip()
            if section == "header" and key == "TIER-CURVE":
                cm = re.match(r"^(\S+)\s+(\d+)\s*(?:→|->)\s*(\d+)$", val)
                if not cm:
                    f.hard("tier-curve", f"line {ln}",
                           f"TIER-CURVE not parseable (want '<cast-id> <start>→<end>'): {val!r}")
                else:
                    doc["tier_curves"][cm.group(1)] = (int(cm.group(2)), int(cm.group(3)))
            elif section == "header":
                doc["header"][key] = val
            else:
                doc["spine"][key] = val
            continue

        if section in ("cast", "locations", "props", "scenes"):
            if not stripped.startswith("- "):
                f.soft("list", f"line {ln}", f"unparsed line in {section}: {stripped!r}")
                continue
            body = stripped[2:].strip()
            halves = DASH_SPLIT.split(body, maxsplit=1)
            if len(halves) != 2:
                f.hard("list", f"line {ln}",
                       f"{section} entry needs '<id> — <details>': {body!r}")
                continue
            ident, rest = halves[0].strip(), halves[1].strip()
            if section == "locations":
                doc["locations"].append({"id": ident, "desc": rest, "line": ln})
                continue
            if section == "props":
                doc["props"].append({"id": ident, "desc": rest, "line": ln})
                continue
            parts = [p.strip() for p in DOT_SPLIT.split(rest) if p.strip()]
            if section == "cast":
                entry = {"id": ident, "role": None, "arc": None, "fixed_tier": None,
                         "marks": None, "wardrobe": None, "line": ln}
                for i, part in enumerate(parts):
                    low = part.lower()
                    if low.startswith("marks:"):
                        entry["marks"] = part.split(":", 1)[1].strip()
                    elif low.startswith("wardrobe:"):
                        entry["wardrobe"] = part.split(":", 1)[1].strip()
                    elif low.startswith("tiers "):
                        tm = re.match(r"^tiers\s+(\d+)\s*(?:→|->)\s*(\d+)$", low)
                        if tm:
                            entry["arc"] = (int(tm.group(1)), int(tm.group(2)))
                        else:
                            f.hard("cast", f"line {ln}", f"unparseable tiers clause: {part!r}")
                    elif low.startswith("tier fixed"):
                        tm = re.match(r"^tier fixed\s+(\d+)$", low)
                        if tm:
                            entry["fixed_tier"] = int(tm.group(1))
                        else:
                            f.hard("cast", f"line {ln}", f"unparseable fixed-tier clause: {part!r}")
                    elif i == 0:
                        entry["role"] = part
                    else:
                        f.soft("cast", f"line {ln}", f"unrecognized cast clause: {part!r}")
                doc["cast"].append(entry)
            else:  # scenes
                entry = {"name": ident, "pages": None, "regions": [], "devices": [],
                         "reveal_page": None, "line": ln}
                for part in parts:
                    low = part.lower()
                    rm = RANGE_RE.match(part)
                    if rm:
                        entry["pages"] = (int(rm.group(1)), int(rm.group(2)))
                    elif low.startswith("regions:"):
                        entry["regions"] = [r.strip().lower() for r in
                                            part.split(":", 1)[1].split(",") if r.strip()]
                    elif low.startswith("devices:"):
                        entry["devices"] = [d.strip().lower() for d in
                                            part.split(":", 1)[1].split(",") if d.strip()]
                    elif low.startswith("reveal:"):
                        rv = part.split(":", 1)[1].strip()
                        if rv.isdigit():
                            entry["reveal_page"] = int(rv)
                        else:
                            f.hard("scene", f"line {ln}", f"reveal page not an int: {rv!r}")
                    else:
                        f.soft("scene", f"line {ln}", f"unrecognized scene clause: {part!r}")
                doc["scenes"].append(entry)
            continue

        if section == "page":
            pm = PANEL_RE.match(stripped)
            if pm:
                close_panel()
                pno, idx = int(pm.group(1)), int(pm.group(2))
                if page is None or pno != page["n"]:
                    f.hard("panel", f"line {ln}",
                           f"PANEL {pno}.{idx} numbered for page {pno} but appears under page "
                           f"{page['n'] if page else '?'}")
                annots = {}
                for am in ANNOT_RE.finditer(pm.group(3) or ""):
                    annots[am.group(1).lower()] = am.group(2).strip()
                panel = {"page": pno, "idx": idx, "line": ln, "annots": annots,
                         "action": [], "dialogue": [], "captions": [], "sfx": [],
                         "costume": None, "notes": []}
                continue
            if panel is None:
                f.soft("page", f"line {ln}", f"text before first PANEL on page: {stripped!r}")
                continue
            dm = DIALOGUE_RE.match(stripped)
            if dm:
                panel["dialogue"].append({"speaker": dm.group(1).strip(),
                                          "type": dm.group(2), "text": dm.group(3),
                                          "line": ln})
                continue
            if DIALOGUE_SHAPE_RE.match(stripped):
                f.hard("dialogue", f"line {ln}",
                       f"dialogue-shaped line doesn't parse (check type ∈ {sorted(DIALOGUE_TYPES)} "
                       f"and double quotes): {stripped!r}")
                continue
            for label, target in (("CAPTION:", "captions"), ("SFX:", "sfx"), ("NOTE:", "notes")):
                if stripped.upper().startswith(label):
                    panel[target].append(stripped.split(":", 1)[1].strip())
                    break
            else:
                if stripped.upper().startswith("COSTUME:"):
                    panel["costume"] = stripped.split(":", 1)[1].strip()
                else:
                    panel["action"].append(stripped)
            continue

        if section == "notes":
            continue
        if section is None and stripped:
            f.soft("stray", f"line {ln}", f"line outside any section: {stripped[:60]!r}")

    close_page()
    return doc


# --------------------------------------------------------------------------
# Checks

def check(doc: dict, f: Findings) -> dict:
    hdr = doc["header"]
    metrics: dict = {}

    # ---- header contract ---------------------------------------------------
    if not doc["title"]:
        f.hard("header", "document", "missing '# <Title>' line")
    if not doc["synopsis"]:
        f.soft("header", "document", "missing one-line synopsis under the title")
    for key in ("TITLE", "CHAPTER-TYPE", "PAGES", "STYLE", "LOCATION-STRATEGY",
                "ALWAYS-CLOTHED"):
        if key not in hdr:
            f.hard("header", "## Header", f"missing required key {key}:")
    ctype = hdr.get("CHAPTER-TYPE", "").lower()
    if ctype and ctype not in CHAPTER_TYPES:
        f.hard("header", "## Header",
               f"CHAPTER-TYPE {ctype!r} not in {sorted(CHAPTER_TYPES)}")
    strategy = hdr.get("LOCATION-STRATEGY", "").lower()
    if strategy and strategy not in LOCATION_STRATEGIES:
        f.hard("header", "## Header",
               f"LOCATION-STRATEGY {strategy!r} not in {sorted(LOCATION_STRATEGIES)}")

    pages = doc["pages"]
    n_pages = len(pages)
    metrics["pages"] = n_pages
    declared_pages = hdr.get("PAGES")
    if declared_pages is not None:
        if not declared_pages.isdigit():
            f.hard("header", "## Header", f"PAGES not an int: {declared_pages!r}")
        elif int(declared_pages) != n_pages:
            f.hard("header", "## Header",
                   f"PAGES declares {declared_pages} but the script has {n_pages} '## Page' sections")

    numbers = [p["n"] for p in pages]
    if numbers != list(range(1, n_pages + 1)):
        f.hard("pages", "document",
               f"pages must be contiguous from 1; got {numbers}")

    scenes = doc["scenes"]
    if scenes:
        flavor = hdr.get("TRANSFORMATION-FLAVOR", "").lower()
        if not flavor:
            f.hard("header", "## Header",
                   "transformation scenes declared but TRANSFORMATION-FLAVOR missing")
        elif flavor not in FLAVORS:
            f.hard("header", "## Header",
                   f"TRANSFORMATION-FLAVOR {flavor!r} not in {sorted(FLAVORS)}")
        if not doc["tier_curves"]:
            f.hard("header", "## Header",
                   "transformation scenes declared but no TIER-CURVE line")

    # ---- story spine -------------------------------------------------------
    spine = doc["spine"]
    for key in ("WANT", "OBSTACLE", "COST"):
        val = spine.get(key, "")
        if not val:
            f.hard("spine", "### Story spine", f"missing {key}:")
        elif val.lower() in STUB_VALUES or words(val) < 4:
            f.hard("spine", "### Story spine",
                   f"{key} is a stub ({val!r}) — state it in a real sentence")
    promise = spine.get("PROMISE-PAGE", "")
    payoff = spine.get("PAYOFF-PAGE", "")
    if not (promise.isdigit() and payoff.isdigit()):
        f.hard("spine", "### Story spine",
               "PROMISE-PAGE / PAYOFF-PAGE must both be page ints")
    else:
        p_i, y_i = int(promise), int(payoff)
        if not (1 <= p_i <= n_pages and 1 <= y_i <= n_pages):
            f.hard("spine", "### Story spine",
                   f"PROMISE-PAGE {p_i} / PAYOFF-PAGE {y_i} outside 1..{n_pages}")
        elif y_i <= p_i:
            f.hard("spine", "### Story spine",
                   f"PAYOFF-PAGE ({y_i}) must come after PROMISE-PAGE ({p_i})")
    ending = spine.get("ENDING", "").lower()
    if ending not in ENDINGS:
        f.hard("spine", "### Story spine", f"ENDING must be one of {sorted(ENDINGS)}")
    if ending == "cliffhanger" and words(spine.get("HOOK", "")) < 4:
        f.hard("spine", "### Story spine",
               "ENDING is cliffhanger but HOOK is missing/stub — name the planted question")

    # ---- cast --------------------------------------------------------------
    cast = doc["cast"]
    if not cast:
        f.hard("cast", "### Cast", "no cast entries")
    ids = [c["id"] for c in cast]
    if len(ids) != len(set(ids)):
        f.hard("cast", "### Cast", f"duplicate cast ids: {ids}")
    marks_seen: dict[str, str] = {}
    for c in cast:
        where = f"cast '{c['id']}'"
        if not c["wardrobe"]:
            f.hard("cast", where, "missing wardrobe: clause")
        mark = (c["marks"] or "").strip().lower()
        if not mark or mark in STUB_VALUES:
            f.hard("cast", where,
                   "missing marks: — every character needs a named non-wardrobe distinguishing mark")
        elif mark in marks_seen:
            f.hard("cast", where,
                   f"marks duplicate cast '{marks_seen[mark]}' — marks must be distinct per character")
        else:
            marks_seen[mark] = c["id"]
        if c["arc"] is None and c["fixed_tier"] is None:
            f.soft("cast", where, "no tiers/fixed-tier clause — assumed non-arc")
    arc_chars = {c["id"]: c["arc"] for c in cast if c["arc"]}
    for cid, curve in doc["tier_curves"].items():
        if cid not in arc_chars:
            f.hard("cast", "## Header",
                   f"TIER-CURVE names {cid!r} but cast has no matching 'tiers' entry")
        elif arc_chars[cid] != curve:
            f.hard("cast", f"cast '{cid}'",
                   f"cast tiers {arc_chars[cid]} disagree with TIER-CURVE {curve}")
    for cid in arc_chars:
        if cid not in doc["tier_curves"]:
            f.hard("header", "## Header", f"arc character {cid!r} has no TIER-CURVE line")

    if not doc["locations"]:
        f.hard("locations", "### Locations", "no location entries")

    # ---- scenes ------------------------------------------------------------
    scene_pages: set[int] = set()
    for sc in scenes:
        where = f"scene '{sc['name']}'"
        if not sc["pages"]:
            f.hard("scene", where, "missing 'pages a–b' clause")
            continue
        a, b = sc["pages"]
        if not (1 <= a <= b <= n_pages):
            f.hard("scene", where, f"page range {a}–{b} invalid for a {n_pages}-page script")
        scene_pages.update(range(a, b + 1))
        bad_regions = [r for r in sc["regions"] if r not in BODY_REGION_BEATS]
        if bad_regions:
            f.hard("scene", where,
                   f"unknown regions {bad_regions} — allowed: {sorted(BODY_REGION_BEATS)}")
        if not sc["regions"]:
            f.hard("scene", where, "missing regions: clause")
        elif len(sc["regions"]) < 3:
            f.soft("scene", where,
                   f"only {len(sc['regions'])} region(s) declared — scenes usually cover ≥3")
        bad_devices = [d for d in sc["devices"] if d not in DEVICES]
        if bad_devices:
            f.soft("scene", where, f"unknown devices {bad_devices} — menu: {sorted(DEVICES)}")
        if len([d for d in sc["devices"] if d in DEVICES]) < 2:
            f.soft("scene", where,
                   "fewer than 2 escalation devices declared (escalation-devices.md wants ≥2)")
        if sc["reveal_page"] is None:
            f.hard("scene", where, "missing 'reveal: <page>' clause")
        elif sc["pages"] and not (a <= sc["reveal_page"] <= b):
            f.hard("scene", where,
                   f"reveal page {sc['reveal_page']} outside the scene range {a}–{b}")

    # ---- panels ------------------------------------------------------------
    all_panels: list[dict] = []
    cast_ids = set(ids)
    clothed = hdr.get("ALWAYS-CLOTHED", "yes").lower() != "no"

    for page in pages:
        if not page["panels"]:
            f.hard("page", f"page {page['n']}", "page has no panels")
            continue
        idxs = [p["idx"] for p in page["panels"]]
        if idxs != list(range(1, len(idxs) + 1)):
            f.hard("page", f"page {page['n']}",
                   f"panels must be numbered 1..k in order; got {idxs}")
        if page["splash"] and len(page["panels"]) > 1:
            f.hard("page", f"page {page['n']}",
                   "SPLASH page must contain exactly one panel (the grid-break is one image)")
        for p in page["panels"]:
            p["pid"] = f"{p['page']}.{p['idx']}"
            all_panels.append(p)

    n_panels = len(all_panels)
    metrics["panels"] = n_panels
    silent = 0

    for p in all_panels:
        where = f"panel {p['pid']}"
        a = p["annots"]

        if not p["action"]:
            f.hard("panel", where, "no action line (every panel needs one)")

        beat = a.get("beat", "").lower() or None
        if beat and beat not in ALL_BEATS:
            f.hard("beat", where, f"unknown beat {beat!r} — allowed: {sorted(ALL_BEATS)}")
            beat = None
        p["beat"] = beat

        staging = a.get("staging")
        if staging and staging not in STAGING_VALUES:
            f.hard("staging", where,
                   f"unknown staging {staging!r} — allowed: {sorted(STAGING_VALUES)}")
        situation = a.get("situation")
        if situation and situation not in REGISTERS:
            f.hard("situation", where,
                   f"unknown situation register {situation!r} — allowed: {sorted(REGISTERS)}")
        p["situation"] = situation if situation in REGISTERS else None
        size = a.get("size")
        if size and size not in SIZES:
            f.soft("size", where, f"unknown size {size!r} — allowed: {sorted(SIZES)}")

        # tier annotation
        p["tier"] = None
        if "tier" in a:
            tm = re.match(r"^(?:(\S+)\s+)?(\d+)$", a["tier"])
            if not tm:
                f.hard("tier", where, f"unparseable tier {a['tier']!r} (want 'N' or '<id> N')")
            else:
                who = tm.group(1)
                if who is None:
                    if len(arc_chars) > 1:
                        f.hard("tier", where,
                               "bare [tier: N] is ambiguous with multiple arc characters — qualify it")
                    elif arc_chars:
                        who = next(iter(arc_chars))
                if who is not None and who not in arc_chars:
                    f.hard("tier", where, f"tier names {who!r}, not an arc character")
                elif who is not None:
                    p["tier"] = (who, int(tm.group(2)))

        # camera annotation
        p["distance"] = p["angle"] = None
        cam = a.get("camera", "")
        if cam:
            head = cam.split(",")[0].split("(")[0].strip().lower()
            if head not in DISTANCE_SCORE:
                f.soft("camera", where,
                       f"camera head {head!r} is not a Gate-A distance token "
                       f"({sorted(DISTANCE_SCORE)}) — Stage 3 will have to rewrite it")
            else:
                p["distance"] = head
            low = cam.lower()
            p["angle"] = next((x for x in ANGLES if x in low), None)
        elif beat in BODY_REGION_BEATS and beat != "whole_body":
            f.soft("camera", where,
                   f"body-region beat {beat!r} without a camera crop hint — conceive the crop here")

        # L20 hard ceiling: body-region beat annotated full-or-wider
        if beat in BODY_REGION_BEATS - {"whole_body"} and p["distance"] in WIDE_OR_FULL:
            f.hard("camera", where,
                   f"body-region beat {beat!r} annotated at {p['distance']!r} — region beats "
                   "render as before/after at full+; use mcu / ecu-region (L20)")

        # chars annotation
        p["chars"] = None
        if "chars" in a:
            val = a["chars"].strip()
            if val in {"—", "-", "none"}:
                p["chars"] = []
            else:
                clist = [c.strip() for c in val.split(",") if c.strip()]
                unknown = [c for c in clist if c not in cast_ids]
                if unknown:
                    f.hard("chars", where, f"unknown cast ids {unknown}")
                p["chars"] = clist

        # L39 — panels with 2+ characters must name their situation register
        # (script-breakdown §4.8 requires panel_situation there; the writer
        # supplies it so Stage 3 never invents it).
        if p["chars"] is not None and len(p["chars"]) >= 2 and not p["situation"]:
            f.hard("situation", where,
                   f"{len(p['chars'])}-character panel with no [situation:] register — "
                   f"required on multi-character panels (L39); pick from {sorted(REGISTERS)}")

        # dialogue checks (L13 + balloon budget + speakers)
        on_screen = [d for d in p["dialogue"] if d["type"] in ON_SCREEN_TYPES]
        speakers = {d["speaker"] for d in on_screen}
        for d in p["dialogue"]:
            if d["speaker"].lower().replace(" ", "-") not in cast_ids:
                f.hard("dialogue", f"{where} line {d['line']}",
                       f"speaker {d['speaker']!r} is not a cast id")
            wc = words(d["text"])
            if wc > 25:
                f.hard("dialogue", f"{where} line {d['line']}",
                       f"{wc}-word line (max 25) — split into chained balloons")
        if len(on_screen) >= 3 and len(speakers) >= 2:
            f.hard("dialogue", where,
                   f"{len(on_screen)} on-screen lines from {len(speakers)} speakers — split into "
                   "per-speaker panels (L13)")
        elif len(on_screen) == 2 and len(speakers) == 2:
            f.soft("dialogue", where,
                   "2 speakers on one panel — acceptable only as a tight close-framed "
                   "back-and-forth (L13 marginal); prefer a split")
        if len(on_screen) > 2 and len(speakers) == 1:
            f.soft("dialogue", where,
                   f"{len(on_screen)} balloons from one speaker — consider splitting the speech")

        # L12 — on-screen dialogue wants close framing
        if on_screen and p["distance"] in WIDE_OR_FULL:
            f.soft("dialogue", where,
                   f"on-screen dialogue at {p['distance']!r} — tighten to mcu/medium or make it "
                   "a caption/off-panel (L12)")

        if not p["dialogue"]:
            silent += 1

        # coverage + extras lint
        prose = " ".join(p["action"]) + " " + (p["costume"] or "")
        if clothed:
            cm = COVERAGE_HARD_RE.search(prose)
            if cm:
                f.hard("coverage", where,
                       f"coverage violation ({cm.group(0)!r}) with ALWAYS-CLOTHED: yes — garments "
                       "strain and split at seams; coverage is always preserved")
            sm = COVERAGE_SOFT_RE.search(prose)
            if sm:
                f.soft("coverage", where,
                       f"{sm.group(0)!r} — confirm this respects the coverage default")
        em = EXTRAS_RE.search(prose)
        if em:
            f.soft("extras", where,
                   f"background-extras smell ({em.group(0)!r}) — named cast only "
                   "(feedback_no_extra_characters)")

    metrics["silent_panels"] = silent
    metrics["silent_pct"] = round(100 * silent / n_panels, 1) if n_panels else 0
    if n_panels >= 12 and silent == 0:
        f.soft("dialogue", "document",
               "no silent panels — let ~1 in 5 reaction/growth beats carry themselves")

    # L39 budget: multi-character celebration registers read as lineup filler.
    celebration_multi = [p["pid"] for p in all_panels
                         if p.get("situation") in CELEBRATION_REGISTERS
                         and p.get("chars") is not None and len(p["chars"]) >= 2]
    if len(celebration_multi) > 3:
        f.soft("situation", "document",
               f"{len(celebration_multi)} multi-character showcase/celebratory panels "
               f"(budget ~3/chapter, L39): {celebration_multi}")

    # ---- growth density ----------------------------------------------------
    growth_flags = []
    for page in pages:
        is_growth = any(p.get("beat") in GROWTH_BEATS for p in page["panels"])
        growth_flags.append(is_growth)
        if page["growth"] and not is_growth:
            f.soft("density", f"page {page['n']}",
                   "flagged GROWTH but no panel carries a growth beat")
        if is_growth and not page["growth"]:
            f.soft("density", f"page {page['n']}",
                   "carries growth beats but isn't flagged GROWTH in the page header")

    g_pages = sum(growth_flags)
    ratio = g_pages / n_pages if n_pages else 0.0
    metrics["growth_pages"] = g_pages
    metrics["growth_pct"] = round(100 * ratio, 1)
    floor = None
    if hdr.get("GROWTH-TARGET"):
        try:
            floor = float(hdr["GROWTH-TARGET"])
        except ValueError:
            f.hard("header", "## Header", f"GROWTH-TARGET not a float: {hdr['GROWTH-TARGET']!r}")
    if floor is None:
        floor = CHAPTER_FLOORS.get(ctype)
    metrics["growth_floor"] = floor
    if floor is not None and n_pages and ratio < floor:
        f.hard("density", "document",
               f"growth-page ratio {ratio:.0%} under the {ctype or 'declared'} floor {floor:.0%} "
               f"({g_pages}/{n_pages} pages) — add growth beats or split thin moments across "
               "more pages (growth-density mandate)")

    first_g = next((i for i, g in enumerate(growth_flags) if g), None)
    if first_g is None:
        if scenes:
            f.hard("density", "document", "no growth pages at all despite declared scenes")
    else:
        metrics["first_growth_page"] = first_g + 1
        frac = (first_g + 1) / n_pages
        metrics["first_growth_pct"] = round(100 * frac, 1)
        # Floor of page 2 mirrors gribble.php's firstBy = max(2, 15% of pages):
        # on a short script, page 2 is the earliest possible start after setup
        # and can never be "late" regardless of the ratio.
        if frac > 0.25 and first_g + 1 > 2:
            f.soft("density", "document",
                   f"first growth lands {frac:.0%} in (page {first_g + 1}) — fire the engine "
                   "inside the first ~15–20% (Gribble median 11%)")

    # ---- scene decomposition + growth-outside-scene ------------------------
    panels_by_page = {page["n"]: page["panels"] for page in pages}
    for sc in scenes:
        if not sc["pages"]:
            continue
        a, b = sc["pages"]
        where = f"scene '{sc['name']}'"
        beats_present: dict[str, int] = {}
        growth_panels = 0
        for pg in range(a, b + 1):
            for p in panels_by_page.get(pg, []):
                if p.get("beat"):
                    beats_present[p["beat"]] = beats_present.get(p["beat"], 0) + 1
                    if p["beat"] in GROWTH_BEATS:
                        growth_panels += 1
        sc["growth_panels"] = growth_panels
        if not any(bt in beats_present for bt in SETUP_BEATS):
            f.hard("decomposition", where,
                   f"no setup beat in pages {a}–{b} (need ≥1 of {sorted(SETUP_BEATS)})")
        missing = [r for r in sc["regions"] if r not in beats_present]
        if missing:
            f.hard("decomposition", where,
                   f"declared regions never appear as beats: {missing}")
        if not any(bt in beats_present for bt in RESOLUTION_BEATS):
            f.hard("decomposition", where,
                   "no reveal/aftermath beat — a transformation without a reveal has no payoff")

    for page in pages:
        for p in page["panels"]:
            if p.get("beat") in GROWTH_BEATS and page["n"] not in scene_pages:
                f.hard("decomposition", f"panel {p['pid']}",
                       f"growth beat {p['beat']!r} outside any declared transformation scene")

    strong_scenes = sum(1 for sc in scenes if sc.get("growth_panels", 0) >= 3)
    metrics["scenes_with_3plus_growth_panels"] = strong_scenes
    if scenes and strong_scenes < 2:
        f.soft("density", "document",
               f"only {strong_scenes} scene(s) with 3+ growth panels — the house mandate is "
               "several 3+-panel growth scenes per chapter")

    # ---- tier curve --------------------------------------------------------
    traces: dict[str, list[tuple[str, int]]] = {cid: [] for cid in arc_chars}
    for p in all_panels:
        if p.get("tier"):
            who, t = p["tier"]
            traces.setdefault(who, []).append((p["pid"], t))
    metrics["tier_traces"] = {k: [t for _, t in v] for k, v in traces.items()}
    for cid, curve in doc["tier_curves"].items():
        start, end = curve
        if start > end:
            f.hard("tier", f"TIER-CURVE {cid}", f"start {start} > end {end}")
        trace = traces.get(cid, [])
        if not trace:
            f.hard("tier", f"TIER-CURVE {cid}",
                   "no [tier:] annotations for this arc character")
            continue
        prev_pid, prev_t = trace[0]
        if prev_t != start:
            f.hard("tier", f"panel {prev_pid}",
                   f"first tier annotation for {cid} is {prev_t}, declared start is {start}")
        for pid, t in trace[1:]:
            if t < prev_t:
                f.hard("tier", f"panel {pid}",
                       f"tier regressed for {cid}: {prev_t} (panel {prev_pid}) → {t} — the curve "
                       "is monotonic (feedback_dont_invent_state_changes)")
            prev_pid, prev_t = pid, t
        peak = max(t for _, t in trace)
        if peak > end:
            f.hard("tier", f"TIER-CURVE {cid}",
                   f"tier {peak} exceeds the declared end {end} — never outgrow the concept's curve")
        if peak < end:
            f.hard("tier", f"TIER-CURVE {cid}",
                   f"declared end tier {end} is never reached (peak annotated: {peak})")

    # ---- L35 faceless runs -------------------------------------------------
    run = 0
    run_start = None
    for p in all_panels:
        if p.get("beat") in BODY_REGION_BEATS - {"whole_body"}:
            run += 1
            run_start = run_start or p["pid"]
            if run == 3:
                f.soft("faces", f"panels {run_start}…{p['pid']}",
                       "3+ consecutive body-region crops with no face cut — interleave a "
                       "reaction/reveal panel (L35 reaction-intercut)")
        else:
            run, run_start = 0, None

    # ---- capstone repetition ----------------------------------------------
    def keywords(p):
        return set(WORD_RE.findall(" ".join(p["action"]).lower()))

    capstones = [p for p in all_panels
                 if p.get("beat") in {"whole_body", "reveal"}
                 or p["annots"].get("size") == "splash"]
    for prev, cur in zip(capstones, capstones[1:]):
        ka, kb = keywords(prev), keywords(cur)
        if len(ka) >= 8 and len(kb) >= 8:
            sim = len(ka & kb) / len(ka | kb)
            if sim >= 0.55:
                f.soft("escalation", f"panels {prev['pid']} + {cur['pid']}",
                       f"capstone panels restate each other (similarity {sim:.2f}) — each reveal "
                       "must re-peg scale against a NEW gauge (escalation, not repetition)")

    # ---- camera aggregates (pre-check of Gate B's L20 chapter gates) -------
    scored = [p for p in all_panels if p.get("distance")]
    if len(scored) >= 6:
        mean = sum(DISTANCE_SCORE[p["distance"]] for p in scored) / len(scored)
        metrics["camera_mean_distance"] = round(mean, 2)
        metrics["camera_annotated_panels"] = len(scored)
        limit = MEAN_DISTANCE_MAX_TRANSFORMATION if scenes else 3.0
        if mean > limit:
            f.soft("camera", "document",
                   f"annotated mean camera distance {mean:.1f} > {limit} — Gate B will HARD-fail "
                   "this downstream (L20)")
        middle = sum(1 for p in scored if p["distance"] in MIDDLE_DISTANCES) / len(scored)
        metrics["camera_middle_pct"] = round(100 * middle, 1)
        if middle < MIDDLE_FRAC_MIN:
            f.soft("camera", "document",
                   f"only {middle:.0%} of annotated panels at middle distances (target ≥30%) — "
                   "the missing-middle failure shape (L20)")
        combos: dict[tuple, list[str]] = {}
        for p in scored:
            if p.get("angle"):
                combos.setdefault((p["distance"], p["angle"]), []).append(p["pid"])
        for combo, pids in combos.items():
            if len(pids) > SAME_COMBO_MAX:
                f.soft("camera", "document",
                       f"{len(pids)} panels at {combo[0]} × {combo[1]} (max {SAME_COMBO_MAX}) — "
                       f"vary: {pids}")

    metrics["scenes"] = [{"name": sc["name"], "pages": sc.get("pages"),
                          "growth_panels": sc.get("growth_panels", 0),
                          "devices": sc["devices"]} for sc in scenes]
    return metrics


# --------------------------------------------------------------------------

def main(argv: list[str]) -> int:
    args = [a for a in argv[1:] if not a.startswith("--")]
    as_json = "--json" in argv
    if len(args) != 1:
        print("usage: validate_script.py <script.md> [--json]")
        return 2
    path = Path(args[0])
    if not path.exists():
        print(f"not found: {path}")
        return 2

    f = Findings()
    doc = parse_script(path.read_text(encoding="utf-8"), f)
    metrics = check(doc, f)

    hard = [r for r in f.rows if r["severity"] == "hard"]
    soft = [r for r in f.rows if r["severity"] == "soft"]

    if as_json:
        print(json.dumps({"script": str(path), "metrics": metrics,
                          "findings": f.rows}, indent=2))
    else:
        title = doc["title"] or path.name
        print(f"== validate_script — {title} ==")
        print(f"pages: {metrics.get('pages')}  panels: {metrics.get('panels')}  "
              f"growth: {metrics.get('growth_pages')}/{metrics.get('pages')} "
              f"({metrics.get('growth_pct')}% vs floor "
              f"{int((metrics.get('growth_floor') or 0) * 100)}%)  "
              f"first growth: p{metrics.get('first_growth_page', '—')}  "
              f"silent: {metrics.get('silent_pct')}%")
        for cid, trace in (metrics.get("tier_traces") or {}).items():
            print(f"tier {cid}: {trace}")
        if metrics.get("camera_mean_distance") is not None:
            print(f"camera: mean {metrics['camera_mean_distance']} over "
                  f"{metrics['camera_annotated_panels']} annotated panels, "
                  f"middle {metrics.get('camera_middle_pct')}%")
        for sc in metrics.get("scenes", []):
            print(f"scene {sc['name']}: pages {sc['pages']}, "
                  f"{sc['growth_panels']} growth panels, devices {sc['devices']}")
        if hard:
            print(f"\nHARD ({len(hard)}) — script rejected:")
            for r in hard:
                print(f"  [{r['code']}] {r['where']}: {r['message']}")
        if soft:
            print(f"\nSOFT ({len(soft)}):")
            for r in soft:
                print(f"  [{r['code']}] {r['where']}: {r['message']}")
        if not hard:
            print(f"\nOK — no hard findings ({len(soft)} soft)")
    return 1 if hard else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
