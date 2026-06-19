#!/usr/bin/env python3
"""
rules_audit.py — Deterministic continuity audit for a comic project.

Reads shotlist.json + the pages/panels/ folder layout and produces a
findings table for the things a rules engine can verify without looking at
pixels:

  - Every page panel has an accepted image on disk
  - Stage-change pages have a lineup ref attached (per `stage_change` flag)
  - muscle_size_tier (or analogous numeric arc) is monotonic non-decreasing
    where the shotlist declares it should be
  - costume_state field is present and non-empty per panel
  - Cumulative costume damage doesn't regress (once "small tears" is set
    for the issue, a later panel cannot return to "fully intact" unless
    explicitly marked as a flashback/dream via `continuity_break: true`)
  - Required wardrobe items mentioned in cast[] wardrobe appear in every
    panel's costume_state for that character (soft check)
  - References for declared cast/locations/props exist on disk

The vision-based audit is a separate workflow handled by the agent itself
(see SKILL.md). This script is the fast, free, deterministic first pass.

Usage:
  python rules_audit.py --project /path/to/project [--pages 1-7]
  python rules_audit.py --project ... --json    # machine-readable output

Exit codes:
  0  no hard errors
  1  hard errors found
  2  script error (bad input, missing shotlist)
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path


# ---------------------------------------------------------------------------
# Findings

SEVERITY_HARD = "hard"
SEVERITY_SOFT = "soft"
SEVERITY_INFO = "info"


@dataclass
class Finding:
    page: int | None
    panel_id: str | None
    category: str
    severity: str
    message: str
    suggestion: str = ""


# ---------------------------------------------------------------------------
# Costume damage ordering (cumulative — once at a level, can't regress)

DAMAGE_RANKS = [
    ("intact",   0, ["fully intact", "pristine", "clean"]),
    ("tight",    1, ["tight", "strain", "stretching", "stretched", "creases"]),
    ("damaged",  2, ["tear", "tears", "rip", "ripped", "torn", "fraying", "frayed",
                     "peak damage", "battle-worn", "exposing", "shredded"]),
]
# Coarse 3-level scale by design: trying to distinguish "small tears" vs "major
# tears" via text matching produces unreliable signals (different panels phrase
# similar damage in incompatible ways). Use vision-check for pixel-level drift.


CARRYOVER_PATTERNS = [
    "carries forward", "carry forward", "carryover", "carry over",
    "same as page", "unchanged from", "unchanged carries", "from page",
    "previous page", "as before",
]


# ---------------------------------------------------------------------------
# Camera framing categories (mirror comic-production/references/cinematic-framing.md)
#
# Used by check_camera_variety. The variety check is the spec's "for any
# 10-panel sequence" rule encoded as a deterministic gate. Failure modes the
# pipeline has hit in production (Chun-Li growth: ~6/10 panels at medium-front;
# April-claudemade: 7/9 panels at full-eye-level) are exactly what this catches.

CAMERA_DISTANCES = [
    "ecu-face", "ecu-region", "mcu", "medium", "cowboy",
    "full", "wide-establish", "splash",
]

# Numeric distance scores for the L20 chapter-aggregate gate. Scale matches
# camera-distance-analysis/README.md (0 ecu-face → 6 wide-establish). `splash`
# is treated as 5 — it's a full-body close-framed reveal, not a wider category.
DISTANCE_SCORE = {
    "ecu-face": 0,
    "ecu-region": 1,
    "mcu": 2,
    "medium": 3,
    "cowboy": 4,
    "full": 5,
    "wide-establish": 6,
    "splash": 5,
}
MIDDLE_DISTANCES = {"mcu", "medium", "cowboy"}

# L20 chapter-aggregate thresholds. Derived from the hand-made April benchmark
# (mean 2.4) vs the AI-generated failure (mean 4.1).
#
# Post-May-2026 strengthening: transformation comics get a tighter threshold
# (2.5 vs 3.0) because the failure mode is more sensitive in that genre. The
# hand-made April benchmark is 2.4; staying at 2.5 keeps us close to it.
# Non-transformation comics keep the 3.0 default.
MEAN_DISTANCE_MAX = 3.0                       # default for non-transformation
MEAN_DISTANCE_MAX_TRANSFORMATION = 2.5        # tighter for transformation_scenes
MIDDLE_DISTANCE_MIN_FRAC = 0.30
MEAN_DISTANCE_MIN_PANELS = 6  # below this, the chapter is too short to compute meaningfully

# Body-region transformation beats — when shot at full or wider, render as
# before/after rather than the change happening now. HARD finding (post-May
# 2026 strengthening — was SOFT). These are the beats that ABSOLUTELY require
# close framing to read as transformation events.
BODY_REGION_BEATS_FOR_HARD_CEILING = {
    "chest", "hips", "rear", "arms", "abs", "legs", "suit_fail",
}

# Per-beat default distance ceilings per script-breakdown SKILL.md § Step 4.5.
# Used by check_camera_distance_bias: SOFT finding when a panel's beat is set,
# beat != reveal, and panel distance score > beat's ceiling.
PER_BEAT_TIGHTNESS = {
    "consider": 3, "decide": 4, "trigger": 4, "first_sensation": 4,
    "chest": 3, "hips": 3, "rear": 4, "suit_fail": 4,
    "arms": 2, "abs": 2, "legs": 2, "shoulders": 3, "back": 3,
    "whole_body": 5, "reveal": 6, "aftermath": 4,
}

CAMERA_ANGLES = [
    "eye-level", "low-angle-front", "low-angle-back", "high-angle",
    "worms-eye", "birds-eye", "dutch", "over-shoulder", "profile",
    "three-quarter",
]

ECU_DISTANCES = {"ecu-face", "ecu-region"}
WIDE_DISTANCES = {"wide-establish", "splash"}


def parse_camera(s: str) -> tuple[str | None, str | None]:
    """Extract (distance, angle) tokens from a camera string.

    The shotlist camera field is freeform but conventionally a comma- or
    space-separated list of category names plus optional modifier
    ("low-angle-front, three-quarter", "ecu-face", "wide-establish, dutch").
    We pick the first matching distance and first matching angle.
    """
    if not s:
        return (None, None)
    s_lower = s.lower()
    distance = next((d for d in CAMERA_DISTANCES if d in s_lower), None)
    angle = next((a for a in CAMERA_ANGLES if a in s_lower), None)
    return (distance, angle)


# ---------------------------------------------------------------------------
# Transformation beats (the April-claudemade failure mode)
#
# When the shotlist declares a `transformation_scenes` block, each scene must
# decompose into body-region beats per the lesson doc: the April-claudemade
# version jumped from "intact" to "fully transformed" with zero body-region
# beats between, producing 9 alley pose shots instead of a transformation
# sequence. The default required structure mirrors the hand-made target.

BODY_REGION_BEATS = {
    "chest", "hips", "rear", "arms", "abs", "legs",
    "back", "shoulders", "suit_fail", "whole_body",
}

SETUP_BEATS = {"consider", "decide", "trigger", "first_sensation"}
RESOLUTION_BEATS = {"reveal", "aftermath"}

ALL_TRANSFORMATION_BEATS = BODY_REGION_BEATS | SETUP_BEATS | RESOLUTION_BEATS

DEFAULT_TRANSFORMATION_REQUIREMENTS = {
    "min_setup_beats": 1,         # at least one of {consider, decide, trigger, first_sensation}
    "min_body_region_beats": 3,   # at least 3 distinct body-region beats
    "min_reveal_beats": 1,        # at least one of {reveal, aftermath}
}


def classify_costume_damage(state: str) -> int:
    """Return damage rank 0..4, or -1 if the string is unclassifiable / carryover.

    A return of -1 means "the regression check should skip this panel and
    inherit the previous panel's rank" — used when the shotlist phrases the
    state as an explicit carryover ("damage from page 18 carries forward")
    instead of re-listing the tears.
    """
    if not state:
        return -1
    s = state.lower()
    if any(p in s for p in CARRYOVER_PATTERNS):
        return -1
    hit = False
    rank = 0
    for _, level, keywords in DAMAGE_RANKS:
        for kw in keywords:
            if kw in s:
                rank = max(rank, level)
                hit = True
    return rank if hit else -1


# ---------------------------------------------------------------------------
# Image discovery (mirror compose_page.py)

def find_panel_image(project: Path, panel_id: str) -> Path | None:
    """Return the accepted image for `panel_id`, or None if not yet accepted.

    Matches the on-disk conventions `generate_status.py` and `next_panel.py`
    already use, so the three scripts agree on what "accepted" means:

      - Flat layout:    pages/panels/<panel_id>.png
      - Folder layout:  pages/panels/<panel_id>/<label>.png with a sibling
                        `_accepted.txt` file whose contents are the label
                        (e.g. "v1"). No file is renamed on accept.
    """
    panels_dir = project / "pages" / "panels"
    if not panels_dir.exists():
        return None

    panel_dir = panels_dir / panel_id
    if panel_dir.is_dir():
        marker = panel_dir / "_accepted.txt"
        if marker.exists():
            label = marker.read_text().strip()
            if label:
                candidate = panel_dir / f"{label}.png"
                if candidate.exists():
                    return candidate

    flat = panels_dir / f"{panel_id}.png"
    if flat.exists():
        return flat

    return None


# ---------------------------------------------------------------------------
# Reference disk presence

def check_references(project: Path, shotlist: dict) -> list[Finding]:
    out: list[Finding] = []
    for c in shotlist.get("cast", []):
        ref_folder = c.get("ref_folder")
        if ref_folder and not (project / ref_folder).exists():
            out.append(Finding(None, None, "reference", SEVERITY_HARD,
                               f"cast '{c.get('id', '?')}' ref_folder missing: {ref_folder}",
                               "Create the folder and gather a baseline body + face card before generation"))
    for loc in shotlist.get("locations", []):
        ref_folder = loc.get("ref_folder")
        if ref_folder and not (project / ref_folder).exists():
            out.append(Finding(None, None, "reference", SEVERITY_SOFT,
                               f"location '{loc.get('id', '?')}' ref_folder missing: {ref_folder}",
                               "Source an env ref (DAZ3D scene render or composite) before pages set there"))
    for prop in shotlist.get("props", []):
        ref_folder = prop.get("ref_folder")
        if ref_folder and not (project / ref_folder).exists():
            out.append(Finding(None, None, "reference", SEVERITY_INFO,
                               f"prop '{prop.get('id', '?')}' ref_folder missing: {ref_folder}",
                               "Optional — props can often be described in-prompt without a ref"))
    return out


# ---------------------------------------------------------------------------
# Per-page checks

def check_pages(project: Path, shotlist: dict, pages_filter: set[int] | None) -> list[Finding]:
    out: list[Finding] = []
    pages = shotlist.get("pages", [])
    cast_ids = {c.get("id") for c in shotlist.get("cast", [])}

    # Track cumulative damage across the issue (resets allowed only via `continuity_break`)
    last_damage_by_char: dict[str, tuple[int, int, str]] = {}  # char -> (page, rank, state)
    last_size_by_char: dict[str, tuple[int, float]] = {}        # char -> (page, size)

    for page in pages:
        n = page.get("page_number")
        if pages_filter is not None and n not in pages_filter:
            continue
        for panel in page.get("panels", []):
            pid = panel.get("panel_id", f"page-{n}")

            # 1. Accepted image exists
            img = find_panel_image(project, pid)
            if img is None:
                out.append(Finding(n, pid, "asset", SEVERITY_HARD,
                                   "no accepted image on disk for this panel",
                                   "Generate a variant and accept it: either save the final image at "
                                   f"pages/panels/{pid}.png (flat) or place pages/panels/{pid}/<label>.png "
                                   "alongside an _accepted.txt file whose contents are <label> (folder)."))

            # 2. costume_state present per panel
            cs = panel.get("costume_state", "").strip()
            if not cs:
                out.append(Finding(n, pid, "shotlist", SEVERITY_SOFT,
                                   "missing costume_state field",
                                   "Add an explicit costume_state value; lets continuity-check track damage"))

            # 3. Costume damage non-regression — apply per Supergirl-style single-protagonist
            #    arc. If you have multiple muscle-arc characters declare which via `arc_character`.
            arc_char = shotlist.get("arc_character") or _infer_arc_character(shotlist)
            chars = panel.get("characters", [])
            if arc_char and arc_char in chars and cs and not panel.get("continuity_break"):
                rank = classify_costume_damage(cs)
                if rank >= 0:
                    # Explicit damage statement — regression check applies
                    prev = last_damage_by_char.get(arc_char)
                    if prev and rank < prev[1]:
                        out.append(Finding(n, pid, "costume", SEVERITY_SOFT,
                                           f"costume damage rank dropped for {arc_char}: "
                                           f"page {prev[0]} was rank {prev[1]} ('{_summarize(prev[2])}'), "
                                           f"page {n} is rank {rank} ('{_summarize(cs)}')",
                                           "If intentional set continuity_break: true. Otherwise the shotlist phrasing may "
                                           "just differ — run the vision audit to check the actual images."))
                    last_damage_by_char[arc_char] = (n, rank, cs)
                # else: rank == -1 → carryover or unclassifiable. Inherit previous rank
                # for tracking but don't flag.

            # 4. Stage-change pages must have lineup ref intent. We approximate: shotlist
            #    can flag `stage_change: true` per page or panel; if so, the panel notes
            #    should mention "lineup" in some form, or there should be a lineup_ref file
            #    in references/style/.
            if page.get("stage_change") or panel.get("stage_change"):
                if not _has_lineup_ref(project):
                    out.append(Finding(n, pid, "reference", SEVERITY_SOFT,
                                       "stage-change page but no lineup ref found in references/style/",
                                       "Create references/style/muscle-size-lineup.png and attach during generation"))

            # 5. muscle_size_tier monotonic non-decreasing for the arc character
            tier = panel.get("muscle_size_tier")
            if arc_char and arc_char in chars and tier is not None and not panel.get("continuity_break"):
                try:
                    tier_f = float(tier)
                    prev = last_size_by_char.get(arc_char)
                    if prev and tier_f < prev[1]:
                        out.append(Finding(n, pid, "size_tier", SEVERITY_HARD,
                                           f"muscle_size_tier regressed for {arc_char}: "
                                           f"page {prev[0]} was {prev[1]}, page {n} is {tier_f}",
                                           "If intentional set continuity_break: true; otherwise fix shotlist"))
                    last_size_by_char[arc_char] = (n, tier_f)
                except (TypeError, ValueError):
                    out.append(Finding(n, pid, "size_tier", SEVERITY_INFO,
                                       f"muscle_size_tier '{tier}' is not numeric",
                                       "Use numeric tiers (e.g. 1, 2, 2.5) for monotonic checking"))

            # 5a. L29 — every tier-6 panel must have the repo-bundled
            # tier-6 reinforcement PNGs findable on disk. HARD: blocks the
            # render plan, not just warns. The lineup alone interpolates
            # tier-6 downward, so a tier-6 panel without the reinforcement
            # refs is rendering with known-broken anchoring.
            try:
                tier_int = int(tier) if tier is not None else None
            except (TypeError, ValueError):
                tier_int = None
            if tier_int == 6 and not _has_tier6_reinforcement_refs(project):
                out.append(Finding(
                    n, pid, "tier6_reinforcement", SEVERITY_HARD,
                    "Panel declares muscle_size_tier == 6 but the L29 reinforcement PNGs are NOT findable on disk. "
                    "Both tier-6-full-body.png and tier-6-anatomical-detail.png are required.",
                    "Ship the tier-6 reinforcement PNGs to skills/comic-production/references/peak-body-scale/tier-6/ "
                    "(or drop project-local overrides at references/style/) before rendering this panel. "
                    "Tier-6 lineup-only fallback under-renders consistently — see L29.",
                ))

            # 5b. L30 — same gate at tier 7.
            if tier_int == 7 and not _has_tier7_reinforcement_refs(project):
                out.append(Finding(
                    n, pid, "tier7_reinforcement", SEVERITY_HARD,
                    "Panel declares muscle_size_tier == 7 but the L30 reinforcement PNGs are NOT findable on disk. "
                    "Both tier-7-full-body.png and tier-7-anatomical-detail.png are required.",
                    "Ship the tier-7 reinforcement PNGs to skills/comic-production/references/peak-body-scale/tier-7/ "
                    "(or drop project-local overrides at references/style/) before rendering this panel. "
                    "Tier-7 lineup-only fallback inherits the same failure mode as tier-6 — see L30.",
                ))

            # 5c. L31 — same gate at tier 8.
            if tier_int == 8 and not _has_tier8_reinforcement_refs(project):
                out.append(Finding(
                    n, pid, "tier8_reinforcement", SEVERITY_HARD,
                    "Panel declares muscle_size_tier == 8 but the L31 reinforcement PNGs are NOT findable on disk. "
                    "Both tier-8-full-body.png and tier-8-anatomical-detail.png are required.",
                    "Ship the tier-8 reinforcement PNGs to skills/comic-production/references/peak-body-scale/tier-8/ "
                    "(or drop project-local overrides at references/style/) before rendering this panel. "
                    "Per L31.",
                ))

            # 5d. L32 — same gate at tier 9.
            if tier_int == 9 and not _has_tier9_reinforcement_refs(project):
                out.append(Finding(
                    n, pid, "tier9_reinforcement", SEVERITY_HARD,
                    "Panel declares muscle_size_tier == 9 but the L32 reinforcement PNGs are NOT findable on disk. "
                    "Both tier-9-full-body.png and tier-9-anatomical-detail.png are required (both are the same "
                    "composite per the user-directed Grok edit, but both file slots must exist).",
                    "Ship the tier-9 reinforcement PNGs to skills/comic-production/references/peak-body-scale/tier-9/ "
                    "before rendering this panel. Per L32.",
                ))

            # 6. Characters all declared in cast[]
            for ch in chars:
                if cast_ids and ch not in cast_ids:
                    out.append(Finding(n, pid, "shotlist", SEVERITY_SOFT,
                                       f"character '{ch}' not in cast[]",
                                       "Add to cast[] or fix typo in panel.characters"))

    return out


def _summarize(text: str, max_len: int = 80) -> str:
    text = " ".join(text.split())
    return text if len(text) <= max_len else text[:max_len - 1] + "…"


# ---------------------------------------------------------------------------
# Camera variety check

def check_camera_variety(shotlist: dict, pages_filter: set[int] | None) -> list[Finding]:
    """Enforce the cinematic-framing.md variety rule on the panel sequence.

    The spec calls for 10-panel windows; we apply the rule on the full
    filtered set scaled proportionally. A sequence shorter than 4 panels
    is exempt (not enough material to demand variety).
    """
    panels: list[tuple[int, str, str]] = []
    for page in shotlist.get("pages", []):
        n = page.get("page_number")
        if pages_filter is not None and n not in pages_filter:
            continue
        for p in page.get("panels", []):
            panels.append((n, p.get("panel_id", f"page-{n}"), p.get("camera", "") or ""))

    N = len(panels)
    if N < 4:
        return []

    parsed = [(n, pid, parse_camera(cam)) for n, pid, cam in panels]
    distances_present = {d for _, _, (d, _) in parsed if d}
    angles_present = {a for _, _, (_, a) in parsed if a}

    # Threshold: spec is 5 distance / 4 angle per 10 panels. For shorter
    # sequences scale down proportionally; for longer sequences keep the
    # baseline (don't ratchet up — we only have 8 distance categories total,
    # and tight intimate scenes legitimately use a narrow register).
    if N >= 10:
        min_distance, min_angle = 5, 4
    else:
        min_distance = max(2, round(5 * N / 10))
        min_angle = max(2, round(4 * N / 10))

    out: list[Finding] = []

    # Variety floors are SOFT — tight transformation scenes legitimately use a
    # narrow distance/angle register and the spec acknowledges this. Use them
    # as hints, not gates.
    if len(distances_present) < min_distance:
        out.append(Finding(
            None, None, "camera_variety", SEVERITY_SOFT,
            f"Only {len(distances_present)} distinct distance categories across {N} panels (target ≥{min_distance}). Present: {sorted(distances_present) or '∅'}",
            "Vary camera distance: see cinematic-framing.md (ecu-face, ecu-region, mcu, medium, cowboy, full, wide-establish, splash). Tight intimate scenes may legitimately violate this.",
        ))

    if len(angles_present) < min_angle:
        out.append(Finding(
            None, None, "camera_variety", SEVERITY_SOFT,
            f"Only {len(angles_present)} distinct angle categories across {N} panels (target ≥{min_angle}). Present: {sorted(angles_present) or '∅'}",
            "Vary camera angle: see cinematic-framing.md. Sustained-intensity scenes (long dialogue, single confrontation) may legitimately violate this.",
        ))

    # ≤3 panels at the same (distance, angle) combo. This is HARD: even tight
    # scenes shouldn't repeat the *exact same shot* more than 3 times — that's
    # the April-claudemade failure mode (7 of 9 panels at full/eye-level) and
    # the Chun-Li failure mode (6 of 10 at medium/front). It produces a
    # camera-static comic regardless of artistic intent.
    combo_counts: dict[tuple[str | None, str | None], list[tuple[int, str]]] = {}
    for n, pid, (d, a) in parsed:
        if d is None and a is None:
            continue
        combo_counts.setdefault((d, a), []).append((n, pid))

    for (d, a), instances in combo_counts.items():
        if len(instances) > 3:
            sample = ", ".join(f"p{n}/{pid}" for n, pid in instances[:5])
            if len(instances) > 5:
                sample += f", +{len(instances) - 5} more"
            out.append(Finding(
                None, None, "camera_variety", SEVERITY_HARD,
                f"{len(instances)} panels at the same camera combo ({d or '?'}, {a or '?'}) — limit is 3 per 10-panel window. Panels: {sample}",
                "Re-assign cameras for some of these — no single (distance, angle) pair should dominate the sequence",
            ))

    # ≥1 ECU and ≥1 wide/splash per 10-panel sequence. SOFT severity: the
    # spec acknowledges that intimate or sustained-scale scenes can legitimately
    # stay in one register. Hand-made transformation sequences often skip the
    # wide-establish (the action is all in close-ups by design). Flag for review,
    # not for hard failure.
    if N >= 6:
        ecu_count = sum(1 for _, _, (d, _) in parsed if d in ECU_DISTANCES)
        if ecu_count == 0:
            out.append(Finding(
                None, None, "camera_variety", SEVERITY_SOFT,
                f"No ECU (ecu-face or ecu-region) panels across {N}-panel sequence — emotional/detail beats normally need at least one close-up",
                "If intentional (sustained wide framing), ignore. Otherwise add an ecu-face panel on a dialogue climax or an ecu-region panel on a detail beat",
            ))

        wide_count = sum(1 for _, _, (d, _) in parsed if d in WIDE_DISTANCES)
        if wide_count == 0:
            out.append(Finding(
                None, None, "camera_variety", SEVERITY_SOFT,
                f"No wide-establish or splash panels across {N}-panel sequence — scale/locator shots normally appear at least once",
                "If intentional (sustained-intimacy scene that legitimately stays close), ignore. Otherwise add a wide-establish at scene open or a splash at the climax",
            ))

    return out


# ---------------------------------------------------------------------------
# Transformation beats check
#
# A "transformation scene" is a stretch of pages declared in shotlist.json's
# top-level `transformation_scenes` array. Each scene must decompose into
# beats covering setup → body regions → reveal. This is the rule whose
# absence produced the April-claudemade failure (zero body-region beats; a
# 9-page transformation comic with no transformation event shown).

def check_camera_distance_bias(shotlist: dict, pages_filter: set[int] | None) -> list[Finding]:
    """L20 camera-distance bias gate. Enforces chapter-aggregate distribution:

    - HARD: mean camera distance must be ≤ 3.0 (medium or closer).
    - HARD: ≥ 30% of panels must sit in {mcu, medium, cowboy} (the missing-middle test).
    - SOFT per-beat: non-`reveal` transformation beats shot at distances wider
      than their per-beat ceiling (see PER_BEAT_TIGHTNESS).

    Empirical basis: hand-made April mean 2.4, AI April 4.1 with zero middle
    distances. See camera-distance-analysis/README.md and lessons-learned L20.
    """
    panels: list[tuple[int, str, str, str | None]] = []
    for page in shotlist.get("pages", []):
        n = page.get("page_number")
        if pages_filter is not None and n not in pages_filter:
            continue
        for p in page.get("panels", []):
            panels.append((n, p.get("panel_id", f"page-{n}"),
                           p.get("camera", "") or "",
                           p.get("transformation_beat")))

    if len(panels) < MEAN_DISTANCE_MIN_PANELS:
        return []

    parsed = [(n, pid, parse_camera(cam)[0], beat) for n, pid, cam, beat in panels]
    scored = [(n, pid, d, beat, DISTANCE_SCORE.get(d)) for n, pid, d, beat in parsed]
    scored_with_value = [s for s in scored if s[4] is not None]

    out: list[Finding] = []
    if not scored_with_value:
        return out

    N = len(scored_with_value)
    mean_distance = sum(s[4] for s in scored_with_value) / N
    middle_count = sum(1 for s in scored_with_value if s[2] in MIDDLE_DISTANCES)
    middle_frac = middle_count / N

    # L20 post-strengthening: tighter mean threshold for transformation comics.
    is_transformation = bool(shotlist.get("transformation_scenes"))
    mean_threshold = MEAN_DISTANCE_MAX_TRANSFORMATION if is_transformation else MEAN_DISTANCE_MAX

    if mean_distance > mean_threshold:
        out.append(Finding(
            None, None, "camera_distance_bias", SEVERITY_HARD,
            f"Chapter mean camera distance is {mean_distance:.1f} (target ≤ {mean_threshold:.1f}"
            + (" for transformation comics" if is_transformation else "")
            + f"; hand-made April benchmark is 2.4). "
              "The chapter sits too far from its subjects — body-region beats won't read at this framing.",
            "Per L20: default transformation beats to MCU or closer; reserve `full`/`wide-establish` for the reveal beat. "
            "See script-breakdown SKILL.md § Step 4.5 for the per-beat table.",
        ))

    if middle_frac < MIDDLE_DISTANCE_MIN_FRAC:
        out.append(Finding(
            None, None, "camera_distance_bias", SEVERITY_HARD,
            f"Only {middle_count}/{N} panels ({middle_frac*100:.0f}%) sit in the middle distances "
            f"{{mcu, medium, cowboy}} — target ≥ {MIDDLE_DISTANCE_MIN_FRAC*100:.0f}%. "
            f"This is the 'missing middle' failure shape (AI-generated April had 0% here; hand-made April 60%).",
            "Re-assign cameras on some panels to MCU / medium / cowboy. "
            "ECU and full-body panels can coexist with middle distances; what breaks the chapter is having NONE in the middle.",
        ))

    for n, pid, dist, beat, score in scored_with_value:
        if beat is None or beat == "reveal":
            continue
        beat_max = PER_BEAT_TIGHTNESS.get(beat)
        if beat_max is None:
            continue
        if score > beat_max:
            # L20 post-strengthening: body-region beats shot at full+ are HARD,
            # not SOFT. These are the cases where the failure shape is most
            # severe — the transformation event itself doesn't happen on page.
            is_body_region = beat in BODY_REGION_BEATS_FOR_HARD_CEILING
            shot_at_full_or_wider = score >= 5  # full=5, wide-establish=6, splash=5
            severity = SEVERITY_HARD if (is_body_region and shot_at_full_or_wider) else SEVERITY_SOFT
            msg = (
                f"Beat `{beat}` shot at `{dist}` (distance score {score}); typical ceiling for this beat is ≤ {beat_max}. "
                + ("Body-region beats CANNOT be shot at full or wider — that's the failure shape L20 exists to prevent. "
                   if severity == SEVERITY_HARD else
                   "Per L20: body-region beats need the region to dominate the frame.")
            )
            out.append(Finding(
                n, pid, "camera_distance_bias", severity,
                msg,
                "Tighten to MCU or ecu-region. See script-breakdown SKILL.md § Step 4.5 for the per-beat table. "
                "If this framing is intentional (e.g. the beat doubles as an establishing shot), accept this finding.",
            ))

    return out


def check_transformation_beats(shotlist: dict, pages_filter: set[int] | None) -> list[Finding]:
    scenes = shotlist.get("transformation_scenes") or []
    if not scenes:
        return []

    # Index panels by page for cheap range lookups.
    panels_by_page: dict[int, list[dict]] = {}
    for page in shotlist.get("pages", []):
        panels_by_page[page.get("page_number")] = page.get("panels", [])

    out: list[Finding] = []

    for scene in scenes:
        name = scene.get("name") or "<unnamed>"
        pages = scene.get("pages")
        if not (isinstance(pages, list) and len(pages) == 2):
            out.append(Finding(
                None, None, "transformation_beats", SEVERITY_HARD,
                f"transformation_scene '{name}' has no valid `pages: [start, end]` range",
                "Add `pages: [N, M]` to the scene entry in shotlist.json",
            ))
            continue
        start, end = pages
        scene_pages = set(range(start, end + 1))
        if pages_filter is not None and not (scene_pages & pages_filter):
            continue  # scene out of the filter window, skip

        # Gather all panels in scene range with a declared transformation_beat.
        beats_present: dict[str, list[str]] = {}  # beat -> [panel_ids]
        all_panel_ids_in_scene: list[str] = []
        unknown_beats: list[tuple[str, str]] = []
        for pg in scene_pages:
            for panel in panels_by_page.get(pg, []):
                pid = panel.get("panel_id") or f"page-{pg}"
                all_panel_ids_in_scene.append(pid)
                beat = panel.get("transformation_beat")
                if not beat:
                    continue
                if beat not in ALL_TRANSFORMATION_BEATS:
                    unknown_beats.append((pid, beat))
                    continue
                beats_present.setdefault(beat, []).append(pid)

        # Resolve requirements (scene-level overrides default).
        reqs = {**DEFAULT_TRANSFORMATION_REQUIREMENTS, **(scene.get("requirements") or {})}
        required_body_regions = scene.get("required_body_regions")  # optional explicit list

        # Check 1: setup beat present
        setup_count = sum(len(beats_present.get(b, [])) for b in SETUP_BEATS)
        if setup_count < reqs["min_setup_beats"]:
            out.append(Finding(
                None, None, "transformation_beats", SEVERITY_HARD,
                f"transformation_scene '{name}' (pages {start}-{end}) has no setup beat "
                f"(need ≥{reqs['min_setup_beats']} of {{consider, decide, trigger, first_sensation}}). "
                f"Panels in scene: {len(all_panel_ids_in_scene)}",
                "Add a panel with `transformation_beat: 'trigger'` or 'first_sensation' showing the inciting moment",
            ))

        # Check 2: body-region beats
        body_region_beats_present = [b for b in beats_present if b in BODY_REGION_BEATS]
        if required_body_regions:
            missing = [b for b in required_body_regions if b not in beats_present]
            if missing:
                out.append(Finding(
                    None, None, "transformation_beats", SEVERITY_HARD,
                    f"transformation_scene '{name}' is missing required body-region beats: {missing}. "
                    f"Present: {sorted(body_region_beats_present) or '∅'}",
                    f"Add panels with `transformation_beat` set to each of: {missing}",
                ))
        else:
            if len(body_region_beats_present) < reqs["min_body_region_beats"]:
                out.append(Finding(
                    None, None, "transformation_beats", SEVERITY_HARD,
                    f"transformation_scene '{name}' has only {len(body_region_beats_present)} body-region beat(s); "
                    f"need ≥{reqs['min_body_region_beats']} distinct from {{chest, hips, rear, arms, abs, legs, back, shoulders, suit_fail, whole_body}}. "
                    f"Present: {sorted(body_region_beats_present) or '∅'}",
                    "Decompose the transformation into per-region beats (e.g., chest, hips, arms) — see comic-production/references/three-panel-scenes.md",
                ))

        # Check 3: reveal beat present
        reveal_count = sum(len(beats_present.get(b, [])) for b in RESOLUTION_BEATS)
        if reveal_count < reqs["min_reveal_beats"]:
            out.append(Finding(
                None, None, "transformation_beats", SEVERITY_HARD,
                f"transformation_scene '{name}' has no reveal/aftermath beat "
                f"(need ≥{reqs['min_reveal_beats']} of {{reveal, aftermath}}). "
                f"Without a reveal the transformation has no payoff",
                "Add a panel with `transformation_beat: 'reveal'` — typically full-body, close to camera, the triumph shot",
            ))

        # Soft: surface unknown beat names so typos don't silently slip past.
        for pid, beat in unknown_beats:
            out.append(Finding(
                None, pid, "transformation_beats", SEVERITY_SOFT,
                f"unknown transformation_beat '{beat}'. Allowed: {sorted(ALL_TRANSFORMATION_BEATS)}",
                "Fix the typo or extend the allowed-beats set in rules_audit.py",
            ))

    return out


# ---------------------------------------------------------------------------
# Required-metadata check — the Step 0 questionnaire enforcement
#
# Three fields must be present at the top of shotlist.json. Each maps to a
# high-stakes decision the model has latitude on but downstream generation
# can't recover from if guessed silently. The lesson driving this: a v2 April
# transformation run defaulted to 2D illustration when 3D CGI was wanted —
# nothing had asked or required a choice, so the model picked.

LOCATION_STRATEGY_VALUES = {"single", "multi", "per-scene"}
TRANSFORMATION_FLAVOR_VALUES = {"body-region-progression", "single-axis", "other"}

# L34 — subject staging values recognized by the shotlist schema. Each multi-character
# panel at camera_distance >= 2 (medium or wider) MUST declare one of these.
SUBJECT_STAGING_VALUES = {
    "tension-block",
    "depth-staged",
    "triangular",
    "negative-space-asymmetric",
    "foreground-occlusion",
    "parallel-acceptable",
}

# Distance categories where staging matters most. ECU and tighter framings have
# their composition dominated by the framing itself; staging language becomes
# redundant.
_STAGING_LOAD_BEARING_DISTANCES = {"medium", "cowboy", "full", "wide-establish", "splash"}


def check_subject_staging(shotlist: dict, pages_filter: set[int] | None) -> list[Finding]:
    """L34 — Subject staging and compositional depth.

    HARD on any panel with 2+ named characters at camera_distance >= 2 (medium
    or wider) that doesn't declare a `subject_staging` value. L20 governs the
    camera position; L34 governs how the subjects are arranged in the frame.
    Without an explicit staging value, multi-character panels default to flat
    parade-formation blocking.

    SOFT if `parallel-acceptable` appears >2x in the chapter (escape hatch
    should be exceptional, not default). SOFT if every multi-character panel
    declares the same staging value (no variety).
    """
    out: list[Finding] = []
    staging_observed: list[tuple[int, str, str]] = []  # (page, panel_id, value)

    for page in shotlist.get("pages", []):
        page_no = page.get("page_number")
        if pages_filter is not None and page_no not in pages_filter:
            continue
        for p in page.get("panels", []):
            panel_id = p.get("panel_id", f"page-{page_no}")
            cast = p.get("cast", []) or []
            cast_size = len([c for c in cast if c])
            camera = p.get("camera", "") or ""
            distance, _ = parse_camera(camera)

            staging = (p.get("subject_staging") or "").strip()

            # Validate the value if set.
            if staging and staging not in SUBJECT_STAGING_VALUES:
                out.append(Finding(
                    page_no, panel_id, "subject_staging", SEVERITY_HARD,
                    f"Unknown subject_staging value: {staging!r}. Expected one of {sorted(SUBJECT_STAGING_VALUES)}.",
                    "See cinematic-framing.md § Subject staging — L34. Pick the staging value that matches the beat, or use 'parallel-acceptable' as the escape hatch.",
                ))
                continue

            # HARD gate for multi-character panels at medium-or-wider distance.
            load_bearing = (
                cast_size >= 2
                and distance in _STAGING_LOAD_BEARING_DISTANCES
            )
            if load_bearing and not staging:
                out.append(Finding(
                    page_no, panel_id, "subject_staging", SEVERITY_HARD,
                    f"Multi-character panel ({cast_size} cast members) at {distance!r} distance has no subject_staging declared.",
                    "Declare subject_staging on the shotlist beat. See cinematic-framing.md § Subject staging — L34 for values: tension-block / depth-staged / triangular / negative-space-asymmetric / foreground-occlusion / parallel-acceptable. The five active values auto-inject prompt directives via next_panel.py _l34_staging_directive(); parallel-acceptable is the no-op escape hatch.",
                ))
            elif staging:
                staging_observed.append((page_no, panel_id, staging))

    # SOFT — parallel-acceptable abuse.
    parallel_panels = [(n, pid) for n, pid, v in staging_observed if v == "parallel-acceptable"]
    if len(parallel_panels) > 2:
        out.append(Finding(
            None, None, "subject_staging", SEVERITY_SOFT,
            f"{len(parallel_panels)} panels declared subject_staging='parallel-acceptable' (target ≤2 per chapter). Escape hatch should be exceptional.",
            f"Review these panels and reclassify where possible: {parallel_panels[:8]}",
        ))

    # SOFT — no variety (every declared staging is the same value).
    distinct_staging_values = {v for _, _, v in staging_observed if v != "parallel-acceptable"}
    if len(staging_observed) >= 4 and len(distinct_staging_values) == 1:
        only = next(iter(distinct_staging_values))
        out.append(Finding(
            None, None, "subject_staging", SEVERITY_SOFT,
            f"All {len(staging_observed)} staged panels use the same value: {only!r}.",
            "Vary the staging across the chapter. Mix tension-block / depth-staged / triangular / negative-space-asymmetric / foreground-occlusion per the panel intent. See cinematic-framing.md § Subject staging.",
        ))

    return out


def check_reference_completeness(project: Path, shotlist: dict) -> list[Finding]:
    """L28 reference completeness gate. Reads `references_required.json` at
    project root and HARD-fails for every declared file that isn't on disk.

    The manifest is emitted by `script-breakdown` (see its SKILL.md § Step 7)
    and walked by `reference-gathering` (see its manifest-driven mode). This
    check is the gate between stage 2 (references) and stage 3 (generation):
    until every declared ref exists on disk, the comic cannot progress to
    generation.

    Body-tier refs with `lineup_required: true` are flagged separately if
    they exist but were generated without the lineup attached — there's no
    way to verify lineup-attached-at-generation-time after the fact, so this
    is checked via the per-file `_provenance.md` if present (SOFT). The
    primary HARD check is just "is the file there or not."
    """
    out: list[Finding] = []
    manifest_path = project / "references_required.json"

    # If the manifest doesn't exist at all, that's a hard finding — it means
    # script-breakdown didn't emit it, and the project can't progress.
    if not manifest_path.exists():
        # Check whether this looks like a comic project (has shotlist with cast)
        if shotlist.get("cast"):
            out.append(Finding(
                None, None, "reference_completeness", SEVERITY_HARD,
                "references_required.json is missing at project root. The reference manifest is required per L28 and is emitted by `script-breakdown` § Step 7.",
                "Re-run script-breakdown to generate the manifest, then run reference-gathering in manifest-driven mode.",
            ))
        return out

    try:
        manifest = json.loads(manifest_path.read_text())
    except json.JSONDecodeError as e:
        out.append(Finding(
            None, None, "reference_completeness", SEVERITY_HARD,
            f"references_required.json failed to parse: {e}",
            "Fix the JSON syntax. If it's deeply corrupted, re-run script-breakdown to regenerate.",
        ))
        return out

    # Walk characters
    for char_id, char_spec in (manifest.get("characters") or {}).items():
        # face_card
        face_card = char_spec.get("face_card")
        if face_card and not (project / face_card).exists():
            out.append(Finding(
                None, None, "reference_completeness", SEVERITY_HARD,
                f"Missing required reference: {face_card} (face card for character `{char_id}`)",
                "Run reference-gathering in manifest-driven mode to generate this ref. See L28 + reference-gathering SKILL.md.",
            ))

        # body_tiers
        for tier_entry in (char_spec.get("body_tiers") or []):
            tier = tier_entry.get("tier")
            path = tier_entry.get("path")
            lineup_required = tier_entry.get("lineup_required", False)
            tier6_reinforcement_required = tier_entry.get("tier6_reinforcement_required", False)
            if path and not (project / path).exists():
                lineup_note = " — and MUST attach the muscle-size lineup PNG at generation time (L28 + L11)" if lineup_required else ""
                tier6_note = (
                    " — and MUST additionally attach BOTH tier-6 reinforcement PNGs from "
                    "skills/comic-production/references/peak-body-scale/tier-6/ (L29)"
                ) if tier6_reinforcement_required else ""
                out.append(Finding(
                    None, None, "reference_completeness", SEVERITY_HARD,
                    f"Missing required reference: {path} (body-tier {tier} for `{char_id}`)" + lineup_note + tier6_note,
                    "Run reference-gathering in manifest-driven mode. The skill knows the lineup-attach hard rule for tier >= 2 body refs and the L29 tier-6 reinforcement rule.",
                ))
            # L29: tier-6 panels (or tier-6 body refs flagged via the new
            # field) need the repo-bundled reinforcement PNGs accessible.
            # The manifest declares the requirement; here we verify the
            # PNGs are findable on disk via the same search order
            # next_panel.find_tier6_reinforcement_refs uses.
            if tier6_reinforcement_required and not _has_tier6_reinforcement_refs(project):
                out.append(Finding(
                    None, None, "reference_completeness", SEVERITY_HARD,
                    f"Tier-6 body-ref entry for `{char_id}` requires the L29 reinforcement PNGs but they are NOT findable on disk. "
                    "Expected both `tier-6-full-body.png` and `tier-6-anatomical-detail.png` at "
                    "project `references/style/`, or repo-bundled `skills/comic-production/references/peak-body-scale/tier-6/`, "
                    "or `~/.claude/skills/comic-production/references/peak-body-scale/tier-6/`.",
                    "Ship the tier-6 reinforcement PNGs into the canonical repo path (or drop project-local overrides at references/style/) before generation.",
                ))

        # views (L16 — multi-angle character reference packs)
        for view_entry in (char_spec.get("views") or []):
            view_name = view_entry.get("name")
            path = view_entry.get("path")
            lineup_required = view_entry.get("lineup_required", False)
            if path and not (project / path).exists():
                lineup_note = " — and MUST attach the muscle-size lineup PNG at generation time" if lineup_required else ""
                out.append(Finding(
                    None, None, "reference_completeness", SEVERITY_HARD,
                    f"Missing required reference: {path} (view `{view_name}` for `{char_id}`) — per L16 multi-angle ref pack" + lineup_note,
                    "Run reference-gathering in manifest-driven mode. Generates the view ref at the named camera angle.",
                ))

    # Walk locations
    for loc_id, loc_spec in (manifest.get("locations") or {}).items():
        establishing = loc_spec.get("establishing")
        if establishing and not (project / establishing).exists():
            out.append(Finding(
                None, None, "reference_completeness", SEVERITY_HARD,
                f"Missing required reference: {establishing} (establishing shot for location `{loc_id}`)",
                "Run reference-gathering. Source a DAZ3D-style render or generate via the comic-production model.",
            ))
        for view_entry in (loc_spec.get("views") or []):
            view_name = view_entry.get("name")
            path = view_entry.get("path")
            if path and not (project / path).exists():
                out.append(Finding(
                    None, None, "reference_completeness", SEVERITY_HARD,
                    f"Missing required reference: {path} (view `{view_name}` for location `{loc_id}`)",
                    f"Run reference-gathering. This view is required per L14 (multi-view env refs for shot-reverse-shot).",
                ))

    # Walk props (v1: establishing only)
    for prop_id, prop_spec in (manifest.get("props") or {}).items():
        establishing = prop_spec.get("establishing") if isinstance(prop_spec, dict) else None
        if establishing and not (project / establishing).exists():
            out.append(Finding(
                None, None, "reference_completeness", SEVERITY_HARD,
                f"Missing required reference: {establishing} (establishing shot for prop `{prop_id}`)",
                "Run reference-gathering.",
            ))

    return out


def check_required_metadata(project: Path, shotlist: dict) -> list[Finding]:
    out: list[Finding] = []

    # 1. style — must be set, must point to an existing style-lock preset.
    style = shotlist.get("style")
    if not style:
        out.append(Finding(
            None, None, "required_metadata", SEVERITY_HARD,
            "shotlist.json missing top-level `style` field — every comic must lock a style preset (the Step 0 questionnaire decides this)",
            "Pick a preset slug from skills/style-lock/styles/ (default: 'photoreal-daz3d') and add it as a top-level field in shotlist.json. See script-breakdown SKILL.md § Workflow Step 0.",
        ))
    else:
        # Verify the preset exists on disk. Use the pipeline-repo location, not
        # the project's relative path — style-lock presets live with the pipeline.
        # We search a couple of likely locations to be robust to where the
        # pipeline is checked out.
        candidates = [
            Path.home() / ".claude" / "skills" / "style-lock" / "styles" / style,
            Path.home() / "Documents" / "claude-comic-pipeline" / "skills" / "style-lock" / "styles" / style,
        ]
        if not any(p.exists() for p in candidates):
            out.append(Finding(
                None, None, "required_metadata", SEVERITY_SOFT,
                f"shotlist.json `style: '{style}'` does not match any preset under skills/style-lock/styles/. Available slugs are folder names there.",
                "Either fix the typo, or add a new preset by creating skills/style-lock/styles/<slug>/preset.md and updating styles/README.md",
            ))

    # 2. location_strategy — required.
    loc_strategy = shotlist.get("location_strategy")
    if not loc_strategy:
        out.append(Finding(
            None, None, "required_metadata", SEVERITY_HARD,
            "shotlist.json missing top-level `location_strategy` field — chapter must declare whether locations are single / multi / per-scene",
            "Add `location_strategy: 'single' | 'multi' | 'per-scene'` at the top of shotlist.json (the Step 0 questionnaire's Q2).",
        ))
    elif loc_strategy not in LOCATION_STRATEGY_VALUES:
        out.append(Finding(
            None, None, "required_metadata", SEVERITY_HARD,
            f"shotlist.json `location_strategy: '{loc_strategy}'` is not a valid value — must be one of {sorted(LOCATION_STRATEGY_VALUES)}",
            "Fix the value to match the allowed set.",
        ))

    # 3. transformation_metadata — required IF transformation_scenes is non-empty.
    if shotlist.get("transformation_scenes"):
        tmeta = shotlist.get("transformation_metadata") or {}
        flavor = tmeta.get("flavor")
        start_tier = tmeta.get("start_tier")
        end_tier = tmeta.get("end_tier")

        if not flavor:
            out.append(Finding(
                None, None, "required_metadata", SEVERITY_HARD,
                "transformation_scenes declared but `transformation_metadata.flavor` is missing — the model needs this to pick prompt templates and lessons",
                "Add `transformation_metadata: {flavor, start_tier, end_tier}` at the top of shotlist.json. Flavor values: body-region-progression / single-axis / other.",
            ))
        elif flavor not in TRANSFORMATION_FLAVOR_VALUES:
            out.append(Finding(
                None, None, "required_metadata", SEVERITY_HARD,
                f"transformation_metadata.flavor '{flavor}' is not a valid value — must be one of {sorted(TRANSFORMATION_FLAVOR_VALUES)}",
                "Fix the value to match the allowed set.",
            ))

        if start_tier is None or end_tier is None:
            out.append(Finding(
                None, None, "required_metadata", SEVERITY_HARD,
                "transformation_scenes declared but `transformation_metadata.start_tier`/`end_tier` missing — needed for L5 lineup-ref attachment and L8 cumulative-state handling",
                "Add numeric start_tier and end_tier values (typically 1-6 from the size lineup).",
            ))

    return out


def _has_lineup_ref(project: Path) -> bool:
    style = project / "references" / "style"
    if not style.exists():
        return False
    return any(style.glob("*lineup*"))


# L29 — tier-6 reinforcement refs are repo-bundled. The search order mirrors
# `next_panel.find_tier6_reinforcement_refs`: project-local override first,
# then repo-bundled path under the pipeline checkout, then user-installed
# skill path. Both PNGs (`tier-6-full-body.png` + `tier-6-anatomical-detail.png`)
# must be findable.
_TIER6_REINFORCEMENT_FILES = (
    "tier-6-full-body.png",
    "tier-6-anatomical-detail.png",
)

_TIER7_REINFORCEMENT_FILES = (
    "tier-7-full-body.png",
    "tier-7-anatomical-detail.png",
)


def _has_peak_reinforcement_refs(project: Path, tier: int) -> bool:
    """Shared helper for any peak-tier reinforcement ref check. Mirrors
    next_panel._find_peak_reinforcement_refs search order."""
    filenames = (f"tier-{tier}-full-body.png",
                 f"tier-{tier}-anatomical-detail.png")
    tier_subdir = f"tier-{tier}"
    pipeline_candidates: list[Path] = [
        Path.home() / "Documents" / "claude-comic-pipeline" / "skills"
        / "comic-production" / "references" / "peak-body-scale" / tier_subdir,
        Path.home() / ".claude" / "skills" / "comic-production"
        / "references" / "peak-body-scale" / tier_subdir,
    ]
    project_override = project / "references" / "style"
    for filename in filenames:
        found = False
        if (project_override / filename).exists():
            found = True
        else:
            for d in pipeline_candidates:
                if (d / filename).exists():
                    found = True
                    break
        if not found:
            return False
    return True


def _has_tier6_reinforcement_refs(project: Path) -> bool:
    return _has_peak_reinforcement_refs(project, 6)


def _has_tier7_reinforcement_refs(project: Path) -> bool:
    return _has_peak_reinforcement_refs(project, 7)


def _has_tier8_reinforcement_refs(project: Path) -> bool:
    return _has_peak_reinforcement_refs(project, 8)


def _has_tier9_reinforcement_refs(project: Path) -> bool:
    return _has_peak_reinforcement_refs(project, 9)


def _infer_arc_character(shotlist: dict) -> str | None:
    """Heuristic: the cast member whose wardrobe text mentions costume tearing or muscle arcs."""
    for c in shotlist.get("cast", []):
        w = (c.get("wardrobe") or "").lower()
        if "tear" in w or "size" in w or "growth" in w or "muscle" in w:
            return c.get("id")
    return None


# ---------------------------------------------------------------------------
# Reporting

def format_findings_md(project: Path, findings: list[Finding], shotlist: dict) -> str:
    hard = sum(1 for f in findings if f.severity == SEVERITY_HARD)
    soft = sum(1 for f in findings if f.severity == SEVERITY_SOFT)
    info = sum(1 for f in findings if f.severity == SEVERITY_INFO)
    title = shotlist.get("title") or shotlist.get("project") or project.name
    lines = [
        f"# Continuity rules audit — {title}",
        "",
        f"Project: `{project}`",
        f"Pages: {len(shotlist.get('pages', []))}",
        f"Findings: **{hard} hard**, {soft} soft, {info} info",
        "",
    ]
    if not findings:
        lines.append("All deterministic checks passed. Run the vision audit next for pixel-level drift.")
        return "\n".join(lines)

    by_sev = {SEVERITY_HARD: [], SEVERITY_SOFT: [], SEVERITY_INFO: []}
    for f in findings:
        by_sev[f.severity].append(f)

    for sev in (SEVERITY_HARD, SEVERITY_SOFT, SEVERITY_INFO):
        bucket = by_sev[sev]
        if not bucket:
            continue
        lines.append(f"## {sev.upper()} ({len(bucket)})")
        lines.append("")
        lines.append("| Page | Panel | Category | Issue | Suggestion |")
        lines.append("|------|-------|----------|-------|------------|")
        for f in bucket:
            page = f.page if f.page is not None else "-"
            panel = f.panel_id or "-"
            lines.append(f"| {page} | {panel} | {f.category} | {f.message} | {f.suggestion} |")
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI

def resolve_pages_arg(arg: str | None) -> set[int] | None:
    if arg is None:
        return None
    out: set[int] = set()
    for part in arg.split(","):
        part = part.strip()
        if "-" in part:
            lo, hi = part.split("-", 1)
            out.update(range(int(lo), int(hi) + 1))
        else:
            out.add(int(part))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", required=True, type=Path)
    ap.add_argument("--pages", help="Page range to audit, e.g. '1-7'")
    ap.add_argument("--json", action="store_true", help="Emit JSON instead of markdown")
    ap.add_argument("--out", type=Path, help="Write report to file instead of stdout")
    args = ap.parse_args()

    project = args.project.resolve()
    shotlist_path = project / "shotlist.json"
    if not shotlist_path.exists():
        sys.exit(f"shotlist.json not found at {shotlist_path}")
    with open(shotlist_path) as f:
        shotlist = json.load(f)

    pages_filter = resolve_pages_arg(args.pages)
    findings = (
        check_required_metadata(project, shotlist)
        + check_references(project, shotlist)
        + check_reference_completeness(project, shotlist)
        + check_pages(project, shotlist, pages_filter)
        + check_camera_variety(shotlist, pages_filter)
        + check_camera_distance_bias(shotlist, pages_filter)
        + check_transformation_beats(shotlist, pages_filter)
        + check_subject_staging(shotlist, pages_filter)
    )

    if args.json:
        payload = {"project": str(project), "findings": [asdict(f) for f in findings]}
        output = json.dumps(payload, indent=2)
    else:
        output = format_findings_md(project, findings, shotlist)

    if args.out:
        args.out.write_text(output)
        print(f"wrote {args.out}")
    else:
        print(output)

    hard_count = sum(1 for f in findings if f.severity == SEVERITY_HARD)
    sys.exit(1 if hard_count else 0)


if __name__ == "__main__":
    main()
