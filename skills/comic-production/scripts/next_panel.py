#!/usr/bin/env python3
"""Find the next pending panel in a shotlist-driven project and produce a plan.

Reads `shotlist.json`, walks `pages/panels/` for accepted-version history,
applies view-aware chaining (L1.5) to pick a state anchor, identifies the refs
to attach (face card, env ref, muscle lineup if stage-change), maps the camera
category to an aspect ratio, and composes a starter prompt from template
fragments. Output is intended for Claude to consume during the per-panel
Flow UI loop documented in `references/shotlist-driven-flow.md`.

Usage:
    python next_panel.py <project_root>
    python next_panel.py <project_root> --as-json

If every panel in the shotlist has an accepted version, prints a "no pending
panels" message and exits 0.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Per-rule registry (phase 2 of the checks-and-balances refactor). The rules/
# package lives at skills/comic-production/rules/, parallel to scripts/. Add
# the comic-production directory to sys.path so the import works regardless
# of where this file is invoked from.
_COMIC_PRODUCTION_DIR = Path(__file__).resolve().parent.parent
if str(_COMIC_PRODUCTION_DIR) not in sys.path:
    sys.path.insert(0, str(_COMIC_PRODUCTION_DIR))
from rules._registry import get_rule  # noqa: E402


# ---------------------------------------------------------------------------
# View-aware chaining (L1.5)
#
# Maps each target view to the set of prior views whose state can chain.
# See comic-production/references/lessons-learned.md L1.5 for the source.

VIEW_COMPATIBILITY = {
    "front-full":      {"front-full", "3q-full", "low-angle-front", "wide-establish", "splash"},
    "3q-full":         {"front-full", "3q-full", "low-angle-front", "wide-establish", "splash"},
    "back-full":       {"back-full", "low-angle-back"},
    "side-full":       {"side-full", "profile", "3q-full"},
    "profile":         {"profile", "side-full", "3q-full"},
    "low-angle-front": {"front-full", "3q-full", "low-angle-front", "wide-establish"},
    "low-angle-back":  {"back-full", "low-angle-back"},
    "high-angle":      {"front-full", "3q-full", "high-angle"},
    "ecu-face":        set(),  # face card alone is the canonical anchor
    "ecu-region":      set(),  # depends — needs a panel where that region was prominent
    "wide-establish":  {"front-full", "3q-full", "wide-establish", "splash"},
    "splash":          {"front-full", "3q-full", "low-angle-front", "wide-establish", "splash"},
}

# Camera category → Flow aspect ratio (per references/shotlist-driven-flow.md)
ASPECT_FOR_CAMERA = {
    "ecu-face": "1:1",
    "ecu-region": "1:1",
    "front-full": "3:4",
    "3q-full": "3:4",
    "back-full": "3:4",
    "low-angle-front": "3:4",
    "low-angle-back": "3:4",
    "profile": "3:4",
    "side-full": "3:4",
    "mcu": "4:3",
    "medium": "4:3",
    "cowboy": "4:3",
    "high-angle": "3:4",
    "wide-establish": "16:9",
    "splash": "3:4",
}


# ---------------------------------------------------------------------------
# Shotlist + panel-folder readers


def read_shotlist(root: Path) -> dict | None:
    p = root / "shotlist.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except json.JSONDecodeError as e:
        print(f"error: shotlist.json failed to parse: {e}", file=sys.stderr)
        sys.exit(1)


def iter_panels(shotlist: dict):
    """Yield (page_number, panel_dict) in story order."""
    for page in shotlist.get("pages", []):
        page_num = page.get("page_number", 0)
        for panel in page.get("panels", []):
            yield page_num, panel


def panel_status(root: Path, panel: dict) -> dict:
    """Determine whether a panel has been generated/accepted, and how.

    Recognized accepted-state conventions (in priority order):
      1. `<panel_id>/_accepted.txt` whose contents name the accepted variant
         (e.g. "v1") + `<panel_id>/v1.png`.
      2. `<panel_id>/v*_accepted.png` — the accepted variant carries the
         `_accepted` suffix on its filename. Matches rules_audit + compose_page.
      3. Flat fallback: `<panel_id>.png` directly under `pages/panels/`.

    A folder with `v*.png` variants but no accepted marker is "in_progress".
    """
    panel_id = panel.get("panel_id") or panel.get("name") or "<unknown>"
    panels_root = root / "pages" / "panels"

    # Folder naming conventions (try both): exact panel_id, or "panel-<id>".
    # rules_audit + compose_page use the "panel-<id>" form; some older
    # projects use the bare panel_id form.
    folder = panels_root / panel_id
    if not folder.is_dir():
        prefixed = panels_root / f"panel-{panel_id}"
        if prefixed.is_dir():
            folder = prefixed
    if folder.is_dir():
        # Convention 1: explicit _accepted.txt
        accepted_marker = folder / "_accepted.txt"
        if accepted_marker.exists():
            label = accepted_marker.read_text().strip()
            cand = folder / f"{label}.png"
            if cand.exists():
                return {"state": "accepted", "image": cand, "label": label}
            return {"state": "accepted", "image": None, "label": label}
        # Convention 2: v*_accepted.png suffix
        accepted_suffix = sorted(folder.glob("v*_accepted.png"))
        if accepted_suffix:
            picked = accepted_suffix[-1]  # most recent variant
            return {"state": "accepted", "image": picked, "label": picked.stem}
        # Otherwise: folder has variants but no accepted marker → in_progress
        variants = sorted(p for p in folder.iterdir()
                          if p.suffix.lower() in {".png", ".jpg", ".jpeg"}
                          and p.stem.startswith("v"))
        if variants:
            return {"state": "in_progress", "image": None, "label": None,
                    "pending_variants": len(variants)}

    # Flat fallback
    for suffix in (".png", ".jpg", ".jpeg"):
        flat = panels_root / f"{panel_id}{suffix}"
        if flat.exists():
            return {"state": "accepted", "image": flat, "label": "v1 (flat)"}

    return {"state": "pending", "image": None, "label": None}


# ---------------------------------------------------------------------------
# View-aware anchor selection



# --- view-vocabulary normalization (maps shotlist camera dialect -> VIEW_COMPATIBILITY keys) ---
_VIEW_ALIASES = {
    "full-body": "front-full",
    "three-quarter": "3q-full",
    "3q": "3q-full",
    "wide splash": "splash",
    "wide-splash": "splash",
    "wide": "wide-establish",
    "wide-establish": "wide-establish",
    "mcu": "mcu",
    "medium": "medium",
    "medium two-shot": "medium",
    "medium-wide": "medium-wide",
    "medium close-up": "mcu",
    "medium shot": "medium",
    "close-up": "mcu",
    "extreme close-up": "ecu-region",
    "full body": "front-full",
    "wide establishing": "wide-establish",
    "low-angle": "low-angle-front",
    "low-angle-front": "low-angle-front",
    "low-angle-back": "low-angle-back",
    "high-angle": "high-angle",
    "profile": "profile",
    "side-full": "side-full",
    "back-full": "back-full",
    "front-full": "front-full",
    "splash": "splash",
    "ecu-face": "ecu-face",
    "ecu-region": "ecu-region",
}

def _canon_view(raw: str) -> str:
    """Map a compound shotlist camera string to a single VIEW_COMPATIBILITY key.
    Tries each comma-token (longest first) against the alias table; returns the
    first hit, else the bare first token."""
    if not raw:
        return ""
    tokens = [t.strip().lower() for t in raw.split(",") if t.strip()]
    # strip parentheticals like "ecu-region (torso/chest)"
    tokens = [t.split("(")[0].strip() for t in tokens]
    for tok in sorted(tokens, key=len, reverse=True):
        if tok in _VIEW_ALIASES:
            return _VIEW_ALIASES[tok]
    return tokens[0] if tokens else ""
# --- end view-vocabulary normalization ---

def pick_chain_anchor(root: Path, target_view: str, accepted_history: list[dict]) -> dict | None:
    """Walk accepted_history backwards (most-recent-first) and return the most
    recent panel whose view is compatible with target_view. Returns the panel
    dict (with status appended) or None if no match.

    accepted_history is a list of dicts: {"panel": <shotlist panel>,
    "page_number": int, "status": {state, image, label, ...}}
    """
    compatible = VIEW_COMPATIBILITY.get(target_view, set())
    if not compatible:
        return None  # face card alone, or ECU-region needs special handling
    for item in reversed(accepted_history):
        prior_view = _canon_view(item["panel"].get("camera") or item["panel"].get("view") or "")
        if prior_view in compatible:
            return item
    return None


def is_stage_change(panel: dict, accepted_history: list[dict]) -> bool:
    """Return True if this panel's muscle_size_tier differs from the most-recent
    accepted panel's tier. Used to decide whether to attach the lineup ref."""
    tier = panel.get("muscle_size_tier")
    if tier is None:
        return False
    for item in reversed(accepted_history):
        prior_tier = item["panel"].get("muscle_size_tier")
        if prior_tier is not None:
            return tier != prior_tier
    # No prior tier found — first sized panel is a stage-change by definition
    return True


# Cameras where the body is the focal subject — attach the lineup ref on these
# even when the tier hasn't changed, so the muscular build stays anchored across the
# scene (per L11). ECU-face / mcu / ecu-region don't qualify (size isn't the
# focal element at that framing).
FULL_BODY_CAMERAS = {
    "front-full", "3q-full", "side-full", "back-full",
    "low-angle-front", "low-angle-back", "splash",
}

# Cameras that are TOO wide for an on-screen speaker to be the focal point.
# Used by L12: panels with on-screen dialogue + a wide camera produce comics
# where the reader can't tell who's talking. See lessons-learned L12 for the
# full diagnosis and the table of acceptable vs marginal vs wrong cameras.
WIDE_CAMERAS_FOR_DIALOGUE = {"wide-establish", "splash"}

# Dialogue bubble types that imply an ON-SCREEN speaker (whose face must be
# the focal point). Caption and off-panel don't tie to a visible character so
# camera distance is independent of them.
ON_SCREEN_DIALOGUE_TYPES = {"balloon", "thought", "whisper", "shout"}


def detect_dialogue_camera_conflict(panel: dict) -> tuple[bool, list[str]]:
    """L12 detection: returns (conflict_present, list_of_on_screen_speakers).

    Conflict = the panel has on-screen dialogue (balloon/thought/whisper/shout)
    AND the camera distance is wide (wide-establish or splash). At that framing
    the speaker won't be the focal point and the page reads as broken.
    """
    camera = (panel.get("camera") or "").split(",")[0].strip()
    if camera not in WIDE_CAMERAS_FOR_DIALOGUE:
        return (False, [])
    speakers: list[str] = []
    for d in panel.get("dialogue", []) or []:
        if d.get("type", "balloon") in ON_SCREEN_DIALOGUE_TYPES:
            spk = d.get("speaker") or d.get("character") or ""
            if spk and spk not in speakers:
                speakers.append(spk)
    return (bool(speakers), speakers)


# L20 per-beat distance ceilings — mirror of rules_audit.py PER_BEAT_TIGHTNESS.
# Kept in sync manually; both encode "transformation beats default to MCU or
# closer; reveal is the only beat that legitimately uses full+."
_DISTANCE_SCORE = {
    "ecu-face": 0, "ecu-region": 1, "mcu": 2, "medium": 3,
    "cowboy": 4, "full": 5, "wide-establish": 6, "splash": 5,
}
_PER_BEAT_TIGHTNESS = {
    "consider": 3, "decide": 4, "trigger": 4, "first_sensation": 4,
    "chest": 3, "hips": 3, "rear": 4, "suit_fail": 4,
    "arms": 2, "abs": 2, "legs": 2, "shoulders": 3, "back": 3,
    "whole_body": 5, "reveal": 6, "aftermath": 4,
}


def detect_camera_too_far_for_beat(panel: dict) -> tuple[bool, str | None, int | None, int | None]:
    """L20 detection: returns (overshoot, beat, distance_score, beat_max).

    Fires when a panel has a `transformation_beat` set (not `reveal`) AND its
    camera distance is wider than the beat's typical ceiling.
    """
    beat = panel.get("transformation_beat")
    if not beat or beat == "reveal":
        return (False, None, None, None)
    camera = (panel.get("camera") or "").split(",")[0].strip()
    score = _DISTANCE_SCORE.get(camera)
    beat_max = _PER_BEAT_TIGHTNESS.get(beat)
    if score is None or beat_max is None:
        return (False, beat, score, beat_max)
    return (score > beat_max, beat, score, beat_max)


def detect_multi_speaker_crowding(panel: dict) -> tuple[bool, int, int]:
    """L13 detection: returns (split_recommended, n_lines, n_speakers).

    Recommends splitting into per-speaker panels when there are ≥3 dialogue
    entries from ≥2 distinct on-screen speakers. Captions and off-panel
    dialogue don't count toward this threshold.
    """
    n_lines = 0
    speakers: set[str] = set()
    for d in panel.get("dialogue", []) or []:
        if d.get("type", "balloon") not in ON_SCREEN_DIALOGUE_TYPES:
            continue
        n_lines += 1
        spk = d.get("speaker") or d.get("character") or ""
        if spk:
            speakers.add(spk)
    return (n_lines >= 3 and len(speakers) >= 2, n_lines, len(speakers))


def should_attach_lineup(panel: dict, stage_change: bool) -> bool:
    """L11 attachment rule: attach the muscle-size lineup on stage-change panels
    AND on every full-body panel of the arc character.

    The older rule (L5: stage-change only) was a cost-cutting heuristic from the
    Higgsfield era. On Flow refs are free; the muscular-build consistency from
    attaching on full-body shots far outweighs any composition-influence risk.
    """
    if panel.get("muscle_size_tier") is None:
        return False
    if stage_change:
        return True
    camera = (panel.get("camera") or "").split(",")[0].strip()
    return camera in FULL_BODY_CAMERAS


def should_attach_tier6_reinforcement(panel: dict) -> bool:
    """L29 attachment rule: attach BOTH tier-6 reinforcement PNGs whenever
    `panel.muscle_size_tier == 6`.

    Strict tier-6 trigger. Fires in addition to (NOT instead of) the
    lineup. Both refs attach together — splitting them defeats the dual-
    anchor purpose (full-body overview + anatomical detail).
    """
    tier = panel.get("muscle_size_tier")
    try:
        return int(tier) == 6
    except (TypeError, ValueError):
        return False


def should_attach_tier7_reinforcement(panel: dict) -> bool:
    """L30 attachment rule: same shape as L29 but at `muscle_size_tier == 7`.

    Tier 7 ("beyond peak") needs its own dedicated reinforcement sheets
    because the multi-figure muscle-size-lineup-4-9.png chart averages
    its tier-7 figure toward the middle of the chart (tiers 5-6); the
    dedicated tier-7 sheets isolate the beyond-peak proportions as their
    own anchor.
    """
    tier = panel.get("muscle_size_tier")
    try:
        return int(tier) == 7
    except (TypeError, ValueError):
        return False


def should_attach_tier8_reinforcement(panel: dict) -> bool:
    """L31 attachment rule: sibling of L30 at `muscle_size_tier == 8`.

    Tier 8 ("super-peak cartoony FMG") inherits the same multi-figure
    interpolation failure mode L29/L30 fix at tier 6/7. Dedicated tier-8
    sheets isolate the super-peak proportions.
    """
    tier = panel.get("muscle_size_tier")
    try:
        return int(tier) == 8
    except (TypeError, ValueError):
        return False


def should_attach_tier9_reinforcement(panel: dict) -> bool:
    """L32 attachment rule: sibling of L31 at `muscle_size_tier == 9`.

    Tier 9 ("maximum cartoony FMG") caps the peak-tier reinforcement
    series. Same failure mode and fix as L29/L30/L31.
    """
    tier = panel.get("muscle_size_tier")
    try:
        return int(tier) == 9
    except (TypeError, ValueError):
        return False


# ---------------------------------------------------------------------------
# Ref discovery


def find_face_card(root: Path, char_slug: str) -> Path | None:
    char_dir = root / "references" / "characters" / char_slug
    if not char_dir.is_dir():
        return None
    for name in ("face-card.png", "face.png", "face-card.jpg", "face.jpg"):
        p = char_dir / name
        if p.exists():
            return p
    # Fallback: first image
    for p in sorted(char_dir.iterdir()):
        if p.suffix.lower() in {".png", ".jpg", ".jpeg"} and not p.name.startswith("_"):
            return p
    return None


def find_env_ref(root: Path, location_slug: str) -> Path | None:
    """Fallback DAZ source ref. Prefer pick_location_anchor() which implements
    L10 env chaining (use the first accepted panel in this location instead)."""
    loc_dir = root / "references" / "locations" / location_slug
    src = loc_dir / "_source.jpg"
    if src.exists():
        return src
    if loc_dir.is_dir():
        for p in sorted(loc_dir.iterdir()):
            if p.suffix.lower() in {".png", ".jpg", ".jpeg"} and not p.name.startswith("_"):
                return p
    return None


def pick_location_anchor(root: Path, location_slug: str, accepted_history: list[dict]) -> dict | None:
    """L10 env chaining: the first accepted panel in this location is the
    canonical visual anchor for the location. Returns that history item, or
    None if no accepted panel yet exists for this location.

    When this returns a result, callers should attach that panel's image as
    the env reference *instead of* `_source.jpg`. The DAZ source did its job
    on the first panel; afterward, your real chamber image is the better
    anchor than a stand-in render.
    """
    if not location_slug:
        return None
    for item in accepted_history:
        if (item["panel"].get("location") or "") == location_slug:
            if item["status"].get("image"):
                return item
    return None


def _read_production_config(root: Path) -> dict | None:
    """Read production-config.json at project root. Returns None if missing
    or malformed (caller falls back to FMG defaults). UTF-8 explicit for
    Windows safety.

    Restored from pre-v4 local; required by autopilot + production-briefing
    flow so non-FMG transformation types (BE / glute / MMG) can ship a
    custom lineup filename via `lineup_files.tier_low / tier_high`.
    """
    cfg_path = root / "production-config.json"
    if not cfg_path.is_file():
        return None
    try:
        return json.loads(cfg_path.read_text(encoding="utf-8"))
    except Exception:
        return None


def find_lineup(root: Path, tier: int | None) -> Path | None:
    """Resolve the size-anchor lineup ref. Filenames come from
    production-config.json's `lineup_files` block when present; falls back to
    the FMG defaults (`muscle-size-lineup.png` / `muscle-size-lineup-4-9.png`)
    when the config is missing.

    Tries, in order:

    1. Project-local override:  <root>/references/style/<filename>
       (lets a project ship a custom lineup).
    2. Repo-bundled assets:     <pipeline>/skills/comic-production/assets/...
       (resolved relative to this script — works wherever the repo is cloned).
    3. User-installed skill:    ~/.claude/skills/comic-production/assets/...
    4. Plugin-installed skill:  ~/Library/Application Support/Claude/.../skills/
       comic-production/assets/...  (best-effort glob).

    Returns None only if every candidate is missing. When the caller gets
    None for a tier > 1 panel, that's a HARD bug — the prompt must not
    reference a lineup that isn't attached.
    """
    if tier is None:
        return None

    cfg = _read_production_config(root)
    lineup_cfg = (cfg or {}).get("lineup_files", {})
    tier_low_name = lineup_cfg.get("tier_low", "muscle-size-lineup.png")
    tier_high_name = lineup_cfg.get("tier_high", "muscle-size-lineup-4-9.png")
    active_range = lineup_cfg.get("active_range", "auto")

    if active_range == "low":
        filename = tier_low_name
    elif active_range == "high":
        filename = tier_high_name
    else:  # auto
        filename = tier_high_name if tier >= 7 else tier_low_name

    candidates: list[Path] = [
        root / "references" / "style" / filename,
        Path(__file__).resolve().parent.parent / "assets" / filename,
        Path.home() / ".claude" / "skills" / "comic-production" / "assets" / filename,
    ]
    # Best-effort: plugin-installed location (path is non-deterministic)
    plugin_root = Path.home() / "Library" / "Application Support" / "Claude" / "local-agent-mode-sessions"
    if plugin_root.exists():
        for match in plugin_root.rglob(f"comic-production/assets/{filename}"):
            candidates.append(match)
            break

    for p in candidates:
        if p.exists():
            return p
    return None


# L29 — tier-6 reinforcement refs. Repo-bundled under
# skills/comic-production/references/peak-body-scale/tier-6/. Project-local
# overrides are honored at references/style/ so a project can ship custom
# tier-6 anchors (the same override pattern the lineup uses).
TIER6_REINFORCEMENT_FILENAMES = (
    "tier-6-full-body.png",
    "tier-6-anatomical-detail.png",
)

# L30 — tier-7 reinforcement refs. Sibling pattern to TIER6_*.
TIER7_REINFORCEMENT_FILENAMES = (
    "tier-7-full-body.png",
    "tier-7-anatomical-detail.png",
)

# L31 — tier-8 reinforcement refs. Sibling pattern to TIER6_*/TIER7_*.
TIER8_REINFORCEMENT_FILENAMES = (
    "tier-8-full-body.png",
    "tier-8-anatomical-detail.png",
)

# L32 — tier-9 reinforcement refs. Note: both files are intentionally
# the same composite image (user-directed Grok edit of A-02 candidate
# with bigger bust). The composite already contains both full-body and
# detail-zoom panels, so the dual-attach pattern still gives the model
# two ref slots pointing at calibrated tier-9 proportions.
TIER9_REINFORCEMENT_FILENAMES = (
    "tier-9-full-body.png",
    "tier-9-anatomical-detail.png",
)


def _find_peak_reinforcement_refs(root: Path, tier: int) -> list[Path]:
    """Shared resolver for any peak-tier reinforcement ref pair. Returns
    paths in canonical order (full-body first, anatomical-detail second),
    or an empty list if either file is missing (all-or-nothing — partial
    refs would mis-anchor)."""
    filenames = (f"tier-{tier}-full-body.png",
                 f"tier-{tier}-anatomical-detail.png")
    tier_subdir = f"tier-{tier}"

    pipeline_root = (Path(__file__).resolve().parent.parent
                     / "references" / "peak-body-scale" / tier_subdir)
    user_root = (Path.home() / ".claude" / "skills" / "comic-production"
                 / "references" / "peak-body-scale" / tier_subdir)
    plugin_root = Path.home() / "Library" / "Application Support" / "Claude" / "local-agent-mode-sessions"

    resolved: list[Path] = []
    for filename in filenames:
        candidates: list[Path] = [
            root / "references" / "style" / filename,
            pipeline_root / filename,
            user_root / filename,
        ]
        if plugin_root.exists():
            for match in plugin_root.rglob(
                f"comic-production/references/peak-body-scale/{tier_subdir}/{filename}"
            ):
                candidates.append(match)
                break
        found = next((p for p in candidates if p.exists()), None)
        if found is None:
            return []
        resolved.append(found)
    return resolved


def find_tier6_reinforcement_refs(root: Path) -> list[Path]:
    """Resolve the two tier-6 reinforcement PNGs. Returns a list of paths in
    canonical order (full-body first, anatomical-detail second). Returns an
    EMPTY list when either file is missing — callers MUST handle this as a
    HARD failure for tier-6 panels because L29 verbal-only fallback at tier
    6 is significantly weaker than the multi-figure lineup interpolation
    failure mode it exists to fix.

    Search order per file:

    1. Project-local override:  <root>/references/style/<filename>
    2. Repo-bundled refs:       <pipeline>/skills/comic-production/
                                references/peak-body-scale/tier-6/<filename>
    3. User-installed skill:    ~/.claude/skills/comic-production/
                                references/peak-body-scale/tier-6/<filename>
    4. Plugin-installed skill:  ~/Library/Application Support/Claude/.../
                                skills/comic-production/references/peak-
                                body-scale/tier-6/<filename> (best-effort glob)
    """
    resolved: list[Path] = []
    pipeline_root = (Path(__file__).resolve().parent.parent
                     / "references" / "peak-body-scale" / "tier-6")
    user_root = (Path.home() / ".claude" / "skills" / "comic-production"
                 / "references" / "peak-body-scale" / "tier-6")
    plugin_root = Path.home() / "Library" / "Application Support" / "Claude" / "local-agent-mode-sessions"

    for filename in TIER6_REINFORCEMENT_FILENAMES:
        candidates: list[Path] = [
            root / "references" / "style" / filename,
            pipeline_root / filename,
            user_root / filename,
        ]
        if plugin_root.exists():
            for match in plugin_root.rglob(
                f"comic-production/references/peak-body-scale/tier-6/{filename}"
            ):
                candidates.append(match)
                break
        found = next((p for p in candidates if p.exists()), None)
        if found is None:
            return []  # All-or-nothing — partial refs would mis-anchor.
        resolved.append(found)
    return resolved


def find_tier7_reinforcement_refs(root: Path) -> list[Path]:
    """L30 sibling of find_tier6_reinforcement_refs. Resolves the tier-7
    reinforcement pair from project override → repo-bundled →
    user-installed → plugin-installed paths."""
    return _find_peak_reinforcement_refs(root, 7)


def find_tier8_reinforcement_refs(root: Path) -> list[Path]:
    """L31 sibling of find_tier7_reinforcement_refs. Tier-8 pair."""
    return _find_peak_reinforcement_refs(root, 8)


def find_tier9_reinforcement_refs(root: Path) -> list[Path]:
    """L32 sibling. Tier-9 pair (both files are the same composite image)."""
    return _find_peak_reinforcement_refs(root, 9)


# ---------------------------------------------------------------------------
# Prompt-injection helpers for L21–L24 and the new May-14-validation findings.
#
# These were authoring-time rules until 2026-05-14, when the chun-li-grok-
# validation run produced empirical evidence that compose_prompt needs to
# emit them automatically. See CHANGELOG 2026-05-14 entries for the failure
# cases each one fixes.

# L21 — every prompt that attaches any ref must include this clause near the
# render directive. Models occasionally render an attached face card / lineup
# / state-anchor as a physical scene object (a photo, badge, poster, or
# watermark-style number floating in the corner). Empirically validated on
# Grok p6 v2 where the lineup's "1" label rendered into the panel as a
# watermark; removing it via the v3 prompt suppressed it.
L21_REF_EXCLUSION = (
    "DO NOT render any reference image as a physical scene object — "
    "no inset photos, no watermarks, no figure numbers, no badges. "
    "References are for identity, proportion, location, and state guidance "
    "only and must NOT appear inside the rendered scene."
)


# L22 — hair state per panel. Read explicitly from `panel.hair_state`. Do NOT
# auto-derive from tier + transformation_beat: the May 14 lesson
# `feedback_dont_invent_state_changes` says a tier bump alone is NOT consent
# to escalate to hair-down / suit_fail. The shotlist author owns this field;
# the composer's job is only to surface it as a named, anchored line.
def _hair_state_line(panel: dict) -> str | None:
    hs = panel.get("hair_state")
    if not hs or not isinstance(hs, str) or not hs.strip():
        return None
    return f"Hair state: {hs.strip()}."


# L23 — when the env ref is dropped (3-ref ceiling forces face + state anchor
# + lineup with no room for env), inject 5+ named location elements verbally
# so the background doesn't collapse to a grey void. Pulls from the
# shotlist's locations[].description, which should already be detailed.
# Empirically validated on Grok p4/p6: env dropped, the dense verbal anchor
# held the dojo cleanly.
def _env_dense_anchor(shotlist: dict, location_slug: str) -> str | None:
    if not location_slug:
        return None
    locs = shotlist.get("locations", []) or []
    for loc in locs:
        if loc.get("id") == location_slug:
            desc = (loc.get("description") or "").strip()
            if desc:
                return (
                    f"Background (no env ref attached this panel — render "
                    f"from this dense anchor instead): {desc}"
                )
    return None


# L24 — accessories: canonical inventory + enumerated negation. The negation
# is the load-bearing part: models hallucinate dark studded cuffs / watches /
# tactical gloves when only "no jewelry" is forbidden. The negation list must
# enumerate the substitutes models actually produce.
#
# Per-character accessories live on shotlist.cast[i].accessories as:
#   { "canonical": "white spiked wristbands on both wrists",
#     "negation": ["watches", "bracelets", "dark cuffs",
#                  "leather cuffs", "studded gloves", "smartwatches"] }
#
# Cameras where wrists / neck / ears / fingers may be in frame — i.e. where
# the model has room to hallucinate. ECU-region on an arm is included
# because the wrist is usually at the bottom of frame.
L24_CAMERAS = {
    "ecu-face", "ecu-region", "mcu", "medium", "cowboy",
    "front-full", "3q-full", "back-full", "side-full", "profile",
    "low-angle-front", "low-angle-back", "high-angle",
    "wide-establish", "splash",
}


def _l24_accessory_line(panel: dict, cast_lookup: dict) -> str | None:
    camera = (panel.get("camera") or "").split(",")[0].strip()
    if camera not in L24_CAMERAS:
        return None
    chars = panel.get("characters", []) or []
    if not chars:
        return None
    pieces: list[str] = []
    for char_id in chars:
        char = cast_lookup.get(char_id)
        if not char:
            continue
        acc = char.get("accessories")
        if not acc:
            continue
        canonical = (acc.get("canonical") or "").strip()
        negation = acc.get("negation") or []
        if not canonical and not negation:
            continue
        if canonical:
            pieces.append(f"Accessories ({char_id}): {canonical} — canonical, ONLY these.")
        if negation:
            neg_terms = ", ".join(f"NO {n}" for n in negation)
            pieces.append(neg_terms + ", no anachronistic accessories.")
    if not pieces:
        return None
    return " ".join(pieces)


# L19 — bake 2D comic-style lettering into the CGI render, with the 2D scope
# named explicitly so the comic-coded vocabulary does NOT pull bodies/scene
# to 2D illustration (the L7 Case B failure mode).
#
# Earlier L19 phrasing rendered lettering as "physical 3D scene objects"
# (chrome-extruded SFX, semi-translucent photoreal speech panels). That held
# CGI but produced literal-3D bubbles that don't match classic comic-book
# lettering. May 16 rewrite: bubbles render as flat 2D vector graphics
# overlaid on the photoreal scene, with the 2D scope bounded to lettering
# only and the photoreal scope explicitly reaffirmed.
#
# Test render confirming the new vocabulary: job 607cf047-23d2-453e (May 16,
# 2026). Two-character dialogue panel, nano_banana_flash, 1k, count=1. Result:
# classic white-oval bubbles with bold black outlines + yellow caption box +
# photoreal CGI bodies and dojo environment; no 2D drift on the non-lettering
# content.

_BUBBLE_STYLE_BY_TYPE = {
    "balloon": (
        "classic comic-book speech balloon — clean white rounded oval shape "
        "with a bold 3-4 pixel solid black outline"
    ),
    "thought": (
        "classic comic-book thought bubble — clean white cloud-shaped "
        "outline with a bold 3-4 pixel solid black border, small "
        "cloud-bubble trail of three round dots leading to the thinker"
    ),
    "whisper": (
        "classic comic-book whisper bubble — clean white rounded oval "
        "shape with a thin DASHED black outline (broken/dashed border, "
        "not solid), denoting a quiet voice"
    ),
    "shout": (
        "classic comic-book shout balloon — white JAGGED-EDGED starburst "
        "shape with a bold solid black outline (spiky/zig-zag border, "
        "not smooth), denoting yelling"
    ),
    "off-panel": (
        "classic comic-book speech balloon — clean white rounded oval "
        "shape with a bold solid black outline, drawn at the edge of "
        "the frame with its tail pointing OFF the panel (speaker is "
        "off-screen, not visible in this frame)"
    ),
}

_BUBBLE_FONT = (
    "bold black sans-serif comic display font ALL CAPS text inside "
    "(Bangers-style lettering, no shading, no extrusion)"
)


def _l19_lettering_block(panel: dict) -> str:
    """L19 — render dialogue, captions, and SFX as flat 2D comic-book
    lettering composited onto the photoreal CGI scene.

    The 2D scope is bounded explicitly to the bubble / caption / SFX
    graphics. The rest of the panel (bodies, costumes, environment) stays
    photoreal CGI. This defuses L7 Case B's 2D-drift failure mode.
    """
    parts: list[str] = []

    # Header: name the scope of the 2D style up front.
    parts.append(
        "LETTERING — classic comic-book lettering composited onto the "
        "photoreal CGI scene. The 2D comic styling applies ONLY to the "
        "bubble / caption / SFX graphics. Everything else in the panel "
        "(bodies, costumes, skin, hair, environment, props, lighting) "
        "remains photoreal DAZ3D CGI with ray-traced subsurface scattering "
        "and physically-based rendering. The bubbles are flat 2D vector "
        "graphics overlaid on the 3D scene; they do NOT turn the scene 2D."
    )

    # Dialogue bubbles.
    for i, d in enumerate(panel.get("dialogue", []) or []):
        bubble_type = (d.get("type") or "balloon").strip()
        speaker = (d.get("speaker") or d.get("character") or "").strip()
        text = (d.get("text") or "").strip().replace('"', "'")
        if not text:
            continue
        shape = _BUBBLE_STYLE_BY_TYPE.get(bubble_type,
                                          _BUBBLE_STYLE_BY_TYPE["balloon"])
        # Tail / attribution. For caption / off-panel handle separately.
        if bubble_type == "off-panel":
            attribution = (
                f"tail pointing OFF the edge of the frame (speaker `{speaker}` "
                f"is off-screen)"
            ) if speaker else "tail pointing OFF the edge of the frame"
        elif bubble_type == "thought":
            attribution = (
                f"cloud-bubble trail of three round dots leading to "
                f"`{speaker}`"
            ) if speaker else "cloud-bubble trail of three round dots"
        else:
            attribution = (
                f"short triangular black-outlined tail pointing directly to "
                f"`{speaker}`'s mouth"
            ) if speaker else "short triangular black-outlined tail"

        parts.append(
            f"Bubble {i + 1}: {shape}, positioned over `{speaker}`'s side "
            f"of the frame so the tail attribution is unambiguous; "
            f"{attribution}. {_BUBBLE_FONT} reads exactly: \"{text}\". "
            f"Flat 2D vector graphic — NO 3D shading, NO bevel/extrusion, "
            f"NO translucency, NO chrome, NO drop shadow onto the scene."
        )

    def _as_obj(x):
        return {"text": x} if isinstance(x, str) else (x or {})
    # Captions.
    for i, c in enumerate(panel.get("captions", []) or []):
        c = _as_obj(c)
        text = (c.get("text") or "").strip().replace('"', "'")
        if not text:
            continue
        parts.append(
            f"Caption box {i + 1}: classic comic-book caption — yellow "
            f"rounded-corner rectangle with a bold 3-4 pixel solid black "
            f"outline, positioned at the bottom edge of the panel. "
            f"{_BUBBLE_FONT} reads exactly: \"{text}\". Flat 2D vector "
            f"graphic — NO 3D shading, NO bevel, NO drop shadow on the scene."
        )

    # SFX (sound effects).
    for i, s in enumerate(panel.get("sfx", []) or []):
        s = _as_obj(s)
        text = (s.get("text") or "").strip().replace('"', "'")
        if not text:
            continue
        scale = (s.get("scale") or "medium").strip()
        size_word = {"small": "small", "medium": "bold", "large": "huge"}.get(
            scale, "bold")
        parts.append(
            f"SFX {i + 1}: the word \"{text}\" rendered as {size_word} "
            f"flat 2D comic-book lettering overlaid on the scene — bold "
            f"black or yellow comic display font ALL CAPS, with a solid "
            f"black outline. Flat 2D vector lettering only — NO 3D "
            f"extrusion, NO chrome letter sculptures, NO ray-traced "
            f"shadows on the scene. The SFX is part of the comic-lettering "
            f"overlay layer, not the photoreal layer."
        )

    # Closing scope reaffirmation.
    parts.append(
        "The lettering layer is composited ON TOP of the photoreal CGI "
        "render — like a comic letterer added bubbles and captions directly "
        "onto a photograph. The bodies and scene stay photoreal CGI; only "
        "the bubble / caption / SFX graphics are flat 2D overlay."
    )

    return " ".join(parts)


# New (May 14): female-anatomy anchoring on body-region ECUs at tier >= 2.
# Body-region ECUs on a female muscular character drift to male anatomy
# (square pectorals, no breast contour) when the face is off-frame. Caught
# critically on chun-li-grok-validation p5 (tier 5 abs ECU rendered male).
# Inject an explicit female-anatomy line when:
#   - camera is a body-region close-up (ecu-region)
#   - tier >= 2 (heavy muscle ECUs are the failure surface)
#   - arc character is female (heuristic: cast[].pronoun in {"she","her"}
#     or sex == "f"; falls back to True if undeclared, since FMG comics are
#     overwhelmingly female-coded)
def _arc_character_is_female(panel: dict, cast_lookup: dict) -> bool:
    chars = panel.get("characters", []) or []
    if not chars:
        return False
    char = cast_lookup.get(chars[0])
    if not char:
        return False
    sex = (char.get("sex") or "").lower()
    if sex in ("f", "female"):
        return True
    if sex in ("m", "male"):
        return False
    pronoun = (char.get("pronoun") or "").lower()
    if pronoun in ("she", "she/her", "her"):
        return True
    if pronoun in ("he", "he/him", "him"):
        return False
    # Default for FMG / transformation comics is female arc character.
    return True


FEMALE_ANATOMY_ANCHOR = (
    "Female anatomy anchor: the body is unambiguously FEMALE despite the "
    "hyper-developed muscle. Feminine bone structure, visible breast "
    "contour where the chest is in or near frame, feminine waist taper "
    "above the hips, smaller hands and wrists than a male equivalent, "
    "soft feminine collarbone line. NOT a male body — no square male "
    "pectorals, no flat-plane male upper chest."
)


def _female_anatomy_anchor_needed(panel: dict, cast_lookup: dict) -> bool:
    camera = (panel.get("camera") or "").split(",")[0].strip()
    if camera != "ecu-region":
        return False
    tier = panel.get("muscle_size_tier")
    if tier is None:
        return False
    try:
        if int(tier) < 2:
            return False
    except (TypeError, ValueError):
        return False
    return _arc_character_is_female(panel, cast_lookup)


# Per-model muscularity ceilings (May 14 finding). Some models refuse to
# render extreme female muscle builds regardless of prompt — Grok
# Imagine demonstrably caps around tier 2-3 on female anatomy.
# Used by build_plan to emit a routing-recommendation WARNING; compose_prompt
# does not change behavior based on the model (it doesn't know it).
MODEL_MUSCULARITY_CEILING: dict[str, int] = {
    "grok_image": 3,
    # Add other models here as ceilings are empirically established.
}


def _cast_lookup(shotlist: dict) -> dict:
    """Build a {char_id: char_dict} map from shotlist.cast[]."""
    return {c.get("id"): c for c in (shotlist.get("cast") or []) if c.get("id")}


# ---------------------------------------------------------------------------
# L20 strengthening — aggressive body-region camera directive
#
# When a panel's transformation_beat is a body-region beat (chest, hips, etc),
# the model needs explicit ECU-dominance vocabulary to actually shoot tight.
# Soft "ecu-region" or "mcu" labels get interpreted generously. The
# "DOMINATES" + "cropped OUT" phrasing is load-bearing.

_BODY_REGION_BEAT_TO_REGION = {
    "chest": "chest",
    "hips": "hips and waist",
    "rear": "rear and lower-back",
    "arms": "arms (biceps, shoulders, triceps)",
    "abs": "abdomen and midsection",
    "legs": "legs (quadriceps, hamstrings)",
    "back": "upper back and shoulders",
    "shoulders": "shoulders and deltoids",
    "suit_fail": "the tearing fabric over the body region in transition",
}


def _body_region_camera_directive(panel: dict) -> str | None:
    """L20 strengthening: aggressive ECU vocabulary for body-region beats.

    Returns the directive string or None if the panel isn't a body-region beat.
    Prepended near the camera fragment in compose_prompt so the model commits
    to tight framing BEFORE reading the action content.
    """
    beat = panel.get("transformation_beat")
    if not beat:
        return None
    region = _BODY_REGION_BEAT_TO_REGION.get(beat)
    if not region:
        return None
    return (
        f"L20 framing directive: EXTREME CLOSE-UP on the {region} filling "
        "70%+ of the frame. Macro 100mm lens equivalent, shallow depth-of-field, "
        f"background completely defocused. The {region} DOMINATES the panel — "
        "head and feet cropped OUT of frame. This is a body-region ECU, NOT a "
        "full-body shot. Do not pull back."
    )


# ---------------------------------------------------------------------------
# L15 — Female beauty anchor (mandatory glamour vocabulary)
#
# Inject on any panel where a female cast member is the focal subject. The
# heuristic matches a character if cast[].sex in {"f","female"} or
# cast[].pronoun in {"she","her","her/hers","she/her"}. Default: assume
# female unless cast entry explicitly marks otherwise. Override on a per-
# character basis via `glamour_anchor: false` on the cast entry.

_FEMALE_BEAUTY_ANCHOR = (
    "L15 glamour anchor: render any female character in this panel with "
    "vogue-cover face quality — sculpted cheekbones, refined jawline, "
    "expressive eyes with long natural lashes and depth in the gaze, "
    "magazine-cover finish. Strikingly beautiful — the kind of face that "
    "commands attention. NOT plain, NOT generic-AI-face."
)


def _female_focal_in_panel(panel: dict, cast_lookup: dict) -> bool:
    """Returns True if any female cast member is in the panel and not
    suppressed via cast[].glamour_anchor: false."""
    for char_id in (panel.get("characters") or []):
        entry = cast_lookup.get(char_id) or {}
        if entry.get("glamour_anchor") is False:
            continue  # explicit opt-out
        sex = (entry.get("sex") or "").lower()
        pronoun = (entry.get("pronoun") or "").lower()
        if sex in {"f", "female", "woman"} or pronoun in {"she", "her", "her/hers", "she/her"}:
            return True
        # If sex and pronoun unset, default-assume female (most comics this
        # pipeline ships are FMG-heavy). Override via explicit `sex: "m"` or
        # `glamour_anchor: false` on the cast entry.
        if not sex and not pronoun and entry.get("glamour_anchor") is not False:
            return True
    return False


def _female_beauty_anchor_line(panel: dict, cast_lookup: dict) -> str | None:
    """L15: returns the glamour anchor when a female cast member is in the
    panel, else None."""
    if _female_focal_in_panel(panel, cast_lookup):
        return _FEMALE_BEAUTY_ANCHOR
    return None


# ---------------------------------------------------------------------------
# L17 — Canonical character anchor
#
# For IP/known characters (Chun Li, Lex, Supergirl, April O'Neil), the prompt
# must explicitly name "the canonical version of X" + a description of the
# canon details + a negation of generic interpretation. Cast entries opt in
# via `canonical: true` and provide a `canonical_anchor` text string.

def _canonical_character_directive(panel: dict, cast_lookup: dict) -> str | None:
    """L17: returns a canonical-anchor line for any IP character in the panel,
    or None if no character has `canonical: true`.

    The cast entry format:
        {
          "id": "chunli",
          "canonical": true,
          "canonical_anchor": "the Street Fighter Chun Li — ox-horn hair buns,
                               blue cheongsam with gold trim, white tights,
                               brown thigh-high boots, white spiked wristbands"
        }
    """
    anchors = []
    for char_id in (panel.get("characters") or []):
        entry = cast_lookup.get(char_id) or {}
        if not entry.get("canonical"):
            continue
        anchor_text = entry.get("canonical_anchor") or ""
        if anchor_text:
            anchors.append(f"{char_id}: {anchor_text}")
        else:
            # Cast says canonical but no anchor text provided — fallback to
            # a generic negation that's still useful.
            anchors.append(f"{char_id}: render the canonical published version, NOT a generic interpretation")
    if not anchors:
        return None
    return (
        "L17 canonical anchor: render the canonical published versions of these "
        "IP characters EXACTLY as fans recognize them. " + " ".join(anchors)
        + ". Do not drift toward generic AI interpretations."
    )


# ---------------------------------------------------------------------------
# L18 — Pose anatomy coherence (universal soft guardrail)

_POSE_ANATOMY_ANCHOR = (
    "L18 anatomy coherence: torso, hips, abdomen, and feet all face the same "
    "direction. No impossible twists between hips and torso. All limbs attach "
    "naturally to the body. Both shoulders visible if the chest is visible; "
    "both hips visible if the legs are visible."
)


def _pose_anatomy_anchor() -> str:
    """L18: always-emit anatomy coherence line. Cheap soft guardrail."""
    return _POSE_ANATOMY_ANCHOR


# ---------------------------------------------------------------------------
# Phase 1 of the checks-and-balances refactor — per-rule trace.
#
# See docs/checks-and-balances-design.md for the full design. Phase 1's scope
# is "ledger emit-only": compose_prompt's STRING OUTPUT is byte-identical to
# the legacy path, but it now also populates a trace dict recording which L-
# rules fired and what each contributed. The trace gets serialized to
# pages/panels/panel-<id>/checks.json by checks_ledger.write_checks_ledger.
#
# Phase 2+ will move each entry below into its own per-rule module under
# skills/comic-production/rules/. For phase 1 we keep the registry inline.

PHASE_1_RULE_REGISTRY: dict[str, dict] = {
    # Active in compose_prompt — these get real pre_render statuses
    "L10":            {"title": "References are the truth, prompts are deltas", "slot": "11_render_directive", "applicable_transformations": ["*"], "phase1_tracked": True},
    "L11":            {"title": "Cartoony FMG proportions need explicit anchoring", "slot": ["5_style_anchor", "8_tier_build"], "applicable_transformations": ["fmg"], "phase1_tracked": True},
    "L29":            {"title": "Tier-6 needs dedicated proportion reinforcement refs", "slot": "8b_tier_reinforcement", "applicable_transformations": ["fmg"], "phase1_tracked": True},
    "L30":            {"title": "Tier-7 needs dedicated proportion reinforcement refs", "slot": "8b_tier_reinforcement", "applicable_transformations": ["fmg"], "phase1_tracked": True},
    "L31":            {"title": "Tier-8 needs dedicated proportion reinforcement refs", "slot": "8b_tier_reinforcement", "applicable_transformations": ["fmg"], "phase1_tracked": True},
    "L32":            {"title": "Tier-9 needs dedicated proportion reinforcement refs", "slot": "8b_tier_reinforcement", "applicable_transformations": ["fmg"], "phase1_tracked": True},
    "L15":            {"title": "Female characters must read as beautiful", "slot": "3_subject_identity", "applicable_transformations": ["fmg"], "phase1_tracked": True},
    "L17":            {"title": "Known/canonical characters can't drift", "slot": "3_subject_identity", "applicable_transformations": ["*"], "phase1_tracked": True},
    "L18":            {"title": "Pose anatomy coherence", "slot": "13_anatomy_guardrail", "applicable_transformations": ["*"], "phase1_tracked": True},
    "L20":            {"title": "Camera distance bias (in-prompt directive)", "slot": "2_camera_strengthening", "applicable_transformations": ["*"], "phase1_tracked": True},
    "L21":            {"title": "Suppress in-scene rendering of reference images", "slot": "12_ref_safety", "applicable_transformations": ["*"], "phase1_tracked": True},
    "L22":            {"title": "Hair state must be explicit in every face-visible panel", "slot": "4_subject_state", "applicable_transformations": ["*"], "phase1_tracked": True},
    "L23":            {"title": "When env ref is dropped, add dense verbal env anchor", "slot": "9_environment", "applicable_transformations": ["*"], "phase1_tracked": True},
    "L24":            {"title": "Suppress anachronistic accessories explicitly", "slot": "4_subject_state", "applicable_transformations": ["*"], "phase1_tracked": True},
    "female_anatomy": {"title": "Female anatomy anchor on body-region ECUs (May 14 lesson)", "slot": "4_subject_state", "applicable_transformations": ["fmg"], "phase1_tracked": True},
    # Active in build_plan
    "L1.5":           {"title": "Chain view-aware, not blindly to N-1", "slot": "10_state_anchor", "applicable_transformations": ["*"], "phase1_tracked": True},
    "L12":            {"title": "Dialogue panels need close framing", "slot": None, "applicable_transformations": ["*"], "phase1_tracked": True},
    "L13":            {"title": "Multi-speaker beats split into per-speaker panels", "slot": None, "applicable_transformations": ["*"], "phase1_tracked": True},
    "L20_chapter":    {"title": "L20 chapter-aggregate / per-beat overshoot", "slot": None, "applicable_transformations": ["*"], "phase1_tracked": True},
    "L28":            {"title": "Reference completeness is mandatory", "slot": None, "applicable_transformations": ["*"], "phase1_tracked": True},
    # Deferred — known to phase 1, tracked in a later phase
    "L1":             {"title": "Progressive sequences must be chained", "slot": None, "applicable_transformations": ["*"], "phase1_tracked": False, "phase1_reason": "runner concern (post-render deterministic) — phase 4+"},
    "L9":             {"title": "Capture every panel's job_id before submitting the next", "slot": None, "applicable_transformations": ["*"], "phase1_tracked": False, "phase1_reason": "runner concern (post-render deterministic) — phase 4+"},
    "L14":            {"title": "Multi-view location references for shot-reverse-shot", "slot": None, "applicable_transformations": ["*"], "phase1_tracked": False, "phase1_reason": "gated upstream in reference-gathering"},
    "L16":            {"title": "Multi-angle character reference packs", "slot": None, "applicable_transformations": ["*"], "phase1_tracked": False, "phase1_reason": "gated upstream in reference-gathering"},
    "L19":            {"title": "Bake 2D comic-style lettering with scope-bounded overlay", "slot": None, "applicable_transformations": ["*"], "phase1_tracked": False, "phase1_reason": "auto-injected by compose_prompt when panel has dialogue/captions/sfx — emission verified, no separate trace slot"},
    "L25":            {"title": "Body-region reveals are sticky", "slot": None, "applicable_transformations": ["*"], "phase1_tracked": False, "phase1_reason": "authoring-guidance only — not auto-injected — phase 3"},
    "L26":            {"title": "Costume identity must be canonical across panels", "slot": None, "applicable_transformations": ["*"], "phase1_tracked": False, "phase1_reason": "authoring-guidance only — not auto-injected — phase 3"},
    "L27":            {"title": "Skin sheen and texture continuity", "slot": None, "applicable_transformations": ["*"], "phase1_tracked": False, "phase1_reason": "authoring-guidance only — not auto-injected — phase 3"},
    # Historical / superseded / infrastructure — not modeled as live rules
    "L2":             {"title": "Higgsfield safety filter rejections", "slot": None, "applicable_transformations": ["*"], "phase1_tracked": False, "phase1_reason": "platform-runtime — will track as 'refused' status in phase 4"},
    "L3":             {"title": "Use png not webp", "slot": None, "applicable_transformations": ["*"], "phase1_tracked": False, "phase1_reason": "infrastructure exemption"},
    "L4":             {"title": "Speech bubble positioning", "slot": None, "applicable_transformations": ["*"], "phase1_tracked": False, "phase1_reason": "applied inside L19 lettering block (bubble shape per dialogue type, tail attribution per speaker)"},
    "L5":             {"title": "Lineup ref attach pattern (superseded by L11)", "slot": None, "applicable_transformations": ["*"], "phase1_tracked": False, "phase1_reason": "superseded by L11"},
    "L6":             {"title": "The display widget shows only the latest result", "slot": None, "applicable_transformations": ["*"], "phase1_tracked": False, "phase1_reason": "infrastructure exemption"},
    "L7":             {"title": "Comic-coded vocab pulls toward 2D (superseded by L19)", "slot": None, "applicable_transformations": ["*"], "phase1_tracked": False, "phase1_reason": "superseded by L19"},
    "L8":             {"title": "Cumulative state in multi-beat growth comics", "slot": None, "applicable_transformations": ["*"], "phase1_tracked": False, "phase1_reason": "covered by L1 + L25 + L26 + L27"},
}

TRACE_SCHEMA_VERSION = 1


def _init_trace(transformation_type: str = "fmg") -> dict:
    """Return a fresh trace dict pre-populated with every rule in the registry.

    Untracked rules get a stable {applied: false, reason: <phase1_reason>} row
    so the ledger renders a complete grid. Tracked rules start as
    {applied: false, reason: "not yet recorded"} and get overwritten by
    compose_prompt / build_plan as they actually evaluate.
    """
    trace: dict = {}
    for rule_id, spec in PHASE_1_RULE_REGISTRY.items():
        applic = spec.get("applicable_transformations", ["*"])
        applicable_here = ("*" in applic) or (transformation_type in applic)
        if not spec.get("phase1_tracked"):
            trace[rule_id] = {
                "applied": False,
                "slot": spec.get("slot"),
                "applicable_transformations": applic,
                "reason": spec.get("phase1_reason", "deferred"),
            }
        elif not applicable_here:
            trace[rule_id] = {
                "applied": False,
                "slot": spec.get("slot"),
                "applicable_transformations": applic,
                "reason": f"n/a — applicable_transformations={applic} but project transformation_type='{transformation_type}'",
            }
        else:
            trace[rule_id] = {
                "applied": False,
                "slot": spec.get("slot"),
                "applicable_transformations": applic,
                "reason": "not yet evaluated",
            }
    return trace


def _record_applied(trace: dict | None, rule_id: str, *,
                    contribution: str | None = None,
                    pre_render_status: str = "pass",
                    pre_render_reason: str | None = None,
                    post_render_status: str = "pending",
                    post_render_reason: str | None = None) -> None:
    """Record an applied rule in the trace. No-op when trace is None."""
    if trace is None or rule_id not in trace:
        return
    entry = trace[rule_id]
    entry["applied"] = True
    if contribution is not None:
        entry["compose_contribution"] = contribution
    entry["pre_render"] = {"status": pre_render_status, "reason": pre_render_reason}
    entry["post_render"] = {"status": post_render_status, "reason": post_render_reason}
    entry.pop("reason", None)


def _record_skipped(trace: dict | None, rule_id: str, reason: str) -> None:
    """Record a rule that was evaluated and intentionally not applied."""
    if trace is None or rule_id not in trace:
        return
    entry = trace[rule_id]
    entry["applied"] = False
    entry["reason"] = f"skipped — {reason}"


def _record_failed(trace: dict | None, rule_id: str, *,
                   pre_render_reason: str,
                   contribution: str | None = None) -> None:
    """Record a rule whose pre_render verification failed."""
    if trace is None or rule_id not in trace:
        return
    entry = trace[rule_id]
    entry["applied"] = True
    if contribution is not None:
        entry["compose_contribution"] = contribution
    entry["pre_render"] = {"status": "fail", "reason": pre_render_reason}
    entry["post_render"] = {"status": "blocked", "reason": "pre_render failed"}
    entry.pop("reason", None)


def _format_section(label: str, body: str) -> str:
    """Wrap a prompt fragment in a `[LABEL]\\n<body>` section for the
    human-readable formatted prompt output.

    Trims whitespace from the body but preserves internal line breaks so a
    directive that already has structure stays structured. Skips entirely
    when the body is empty/whitespace-only — callers should not pass empty
    bodies but this is a defensive guard.
    """
    body_stripped = (body or "").strip()
    if not body_stripped:
        return ""
    return f"[{label}]\n{body_stripped}"


def _apply_rule_at_slot(rule_id: str, slot: str, panel: dict, ctx: dict,
                        parts: list, trace: dict | None,
                        transformation_type: str) -> str | None:
    """Phase 3 registry-driven helper: look up the rule, check it applies
    to the transformation type, call compose_contribution + verify_pre_render,
    append to parts (wrapped in a labeled section) and record to trace.

    Returns the contribution string unwrapped (or None if not emitted). The
    trace records the unwrapped contribution so the ledger schema is
    unchanged.

    Multi-slot rules (currently only L11) read the active slot from
    ctx["_active_slot"] which this helper injects. Existing single-slot
    rules ignore the extra key.
    """
    rule = get_rule(rule_id)
    if rule is None or not rule.applies_to_transformation(transformation_type):
        return None
    # Inject _active_slot so multi-slot rules can branch in verify_pre_render
    # without changing the Rule base class signature.
    ctx_with_slot = dict(ctx)
    ctx_with_slot["_active_slot"] = slot
    contribution = rule.compose_contribution(panel, ctx_with_slot, slot)
    verif = rule.verify_pre_render(panel, ctx_with_slot)
    if contribution is not None:
        label = rule.section_label_for(slot)
        section = _format_section(label, contribution)
        if section:
            parts.append(section)
        _record_applied(trace, rule_id,
                        contribution=contribution,
                        pre_render_status=verif.status,
                        pre_render_reason=verif.reason)
        return contribution
    # No contribution at this slot. Record per verification status.
    if verif.status == "fail":
        _record_failed(trace, rule_id,
                       pre_render_reason=verif.reason or "")
    else:
        _record_skipped(trace, rule_id,
                        verif.reason or f"{rule_id} did not apply")
    return None


# ---------------------------------------------------------------------------
# Prompt composer


def compose_prompt(panel: dict, shotlist: dict, anchor: dict | None,
                   stage_change: bool, env_ref: Path | None,
                   env_anchor_from: dict | None = None,
                   lineup_attached: bool = False,
                   env_dropped: bool = False,
                   tier6_refs_attached: bool = False,
                   tier7_refs_attached: bool = False,
                   tier8_refs_attached: bool = False,
                   tier9_refs_attached: bool = False,
                   _trace: dict | None = None,
                   transformation_type: str = "fmg") -> str:
    """Compose a starter prompt for this panel — L10 delta-only skeleton.

    The body describes only what is *new* in this panel (camera, action,
    expression, lighting state change, costume state change). Constants
    (character identity, costume design, location architecture) are
    delegated to the attached references via an explicit render directive.

    `env_anchor_from`: when L10 env chaining promoted a prior accepted panel
    to env anchor (instead of `_source.jpg`), this is that history item.
    The prompt language adapts so the model knows it's chaining off the
    actual chamber image rather than a stand-in DAZ render.

    Output is formatted as labeled sections separated by blank lines so the
    prompt is human-scannable when inspecting a panel that misfired. Image
    models (Nano Banana 2 / GPT Image 2) tokenize whitespace, so line breaks
    do not change semantics vs. the prior single-line concatenation. The
    Flow runner already flattens newlines to spaces before pasting (Flow's
    text area treats `\\n` as submit); the Higgsfield API accepts multi-
    line strings directly.
    """

    camera = (panel.get("camera") or "").split(",")[0].strip()
    action = (panel.get("action") or "").strip()
    location_slug = panel.get("location") or ""
    chars = panel.get("characters") or []
    tier = panel.get("muscle_size_tier")
    time_of_day = panel.get("time_of_day") or ""
    cast_lookup = _cast_lookup(shotlist)

    # Shared ctx dict for rule modules (phase 3a). Every rule reads what it
    # needs from this dict; extra keys are ignored.
    ctx = {
        "env_ref": env_ref,
        "anchor": anchor,
        "env_anchor_from": env_anchor_from,
        "lineup_attached": lineup_attached,
        "tier6_refs_attached": tier6_refs_attached,
        "tier7_refs_attached": tier7_refs_attached,
        "tier8_refs_attached": tier8_refs_attached,
        "tier9_refs_attached": tier9_refs_attached,
        "env_dropped": env_dropped,
        "stage_change": stage_change,
        "shotlist": shotlist,
        "cast_lookup": cast_lookup,
        "camera": camera,
        "location_slug": location_slug,
        "transformation_type": transformation_type,
    }

    parts: list[str] = []

    # 1. Render anchor (positive CGI vocabulary, L7-compliant)
    parts.append(_format_section(
        "RENDER STYLE — Iray photoreal",
        "DAZ Studio Iray render of a real 3D scene. Ray-traced subsurface "
        "scattering on skin, specular highlights catching warm rim light, "
        "physically-accurate fabric weave with visible thread detail, "
        "8K texture detail, shallow depth of field with photographic bokeh."
    ))

    # 2. Camera fragment
    cam_fragments = {
        "ecu-face": "Extreme close-up on the face, framed eyes-to-chin. 85mm lens equivalent, shallow depth of field, background blurred to soft bokeh.",
        "ecu-region": "Extreme close-up framed on the focal body region, macro 100mm lens equivalent, hyperdetailed texture, background completely defocused.",
        "mcu": "Medium close-up from chest up. Standard 50mm lens equivalent, eye-level.",
        "medium": "Medium shot waist-up. 35mm equivalent, conversational distance.",
        "cowboy": "Cowboy shot — framed from mid-thigh up. 35mm equivalent.",
        "front-full": "Full body front view, 28mm equivalent, eye-level, subject occupies the full vertical of the frame.",
        "3q-full": "Three-quarter view at 45 degrees, full body, 35mm equivalent, eye-level.",
        "back-full": "Back-full view, 28mm equivalent, subject's back as the focal point.",
        "side-full": "Side-on full body view, 35mm equivalent.",
        "profile": "Pure profile — camera perpendicular to subject's facing direction, 50mm equivalent.",
        "low-angle-front": "Low angle — camera at hip height tilted up, subject towers over the lens, foreshortened legs in foreground, 24mm equivalent for slight wide-angle distortion.",
        "low-angle-back": "Low angle from behind — camera at knee height, subject's back fills the upper frame.",
        "high-angle": "High angle — camera elevated, looking down on subject.",
        "wide-establish": "Wide establishing shot, subject is small in frame, environment fully visible, 24mm equivalent, deep focus.",
        "splash": "Splash composition — single dramatic image, subject the focal point filling the panel, cinematic full-bleed framing.",
    }
    parts.append(_format_section(
        "CAMERA — base framing",
        cam_fragments.get(camera, f"Camera: {camera or 'eye-level medium shot'}.")
    ))

    # 2a. L20 strengthening — slot 2_camera_strengthening. Body-region camera
    # directive for any panel with a body-region transformation beat. Slots
    # right after the base camera fragment so the model commits to ECU
    # framing BEFORE the action content has a chance to soften it.
    # PHASE 3A — routed through rules._registry.
    _apply_rule_at_slot("L20", "2_camera_strengthening",
                        panel, ctx, parts, _trace, transformation_type)

    # 3. Subjects (name only — identity comes from attached face cards)
    if chars:
        parts.append(_format_section(
            "SUBJECTS",
            f"Subjects: {', '.join(chars)}."
        ))

    # 3.0 L17 — match canonical face card. POST-REFACTOR (2026-05-23):
    # was a multi-line appearance directive, now emits one-line
    # "match the attached canonical face card" when the character is
    # canonical. Source of truth for canon is the face card, not prose.
    _apply_rule_at_slot("L17", "3_subject_identity",
                        panel, ctx, parts, _trace, transformation_type)

    # POST-REFACTOR: L15 (female beauty anchor) DELETED — beauty is in
    # the face card asset. Regenerate the face card if a character
    # reads as not-beautiful; do not paraphrase beauty into the prompt.

    # 3a. L22 hair state — slot 4_subject_state, first. STATE delta
    # (action-class), not appearance. Hair STYLE is in the face card;
    # hair STATE is per-panel (up/down, wet/dry, intact/loose).
    _apply_rule_at_slot("L22", "4_subject_state",
                        panel, ctx, parts, _trace, transformation_type)

    # 3b. L24 accessory canonical + enumerated negation — slot 4_subject_state.
    # Negation-safety. Compliant.
    _apply_rule_at_slot("L24", "4_subject_state",
                        panel, ctx, parts, _trace, transformation_type)

    # POST-REFACTOR: female_anatomy DELETED — face card + body-tier
    # reinforcement refs carry female-ness; the prose anchor was a
    # band-aid replaced by stronger refs.

    # 3d. L11 — match body-tier reference. POST-REFACTOR: was the L11
    # STYLE prose (~600 chars); now one-line "match the attached body-
    # tier reference" directive. Slots before the action delta so the
    # model commits to the body anchor before reading action content.
    _apply_rule_at_slot("L11", "5_style_anchor",
                        panel, ctx, parts, _trace, transformation_type)

    # 4. DELTA — action / pose / expression. Wrapped with a sanitization
    #    directive so the model knows: even if the action text mentions
    #    things that look like constants (clothing, wall types, etc.),
    #    those are *cues for the action context only*, not redescriptions.
    if action:
        action_clean = action.rstrip(".")
        parts.append(_format_section(
            "ACTION DELTA",
            f"DELTA — action only: {action_clean}. (Any mention of clothing, "
            "architecture, or character features in the delta is contextual "
            "shorthand; the visual identity of those things comes from the "
            "attached references.)"
        ))

    # 5. Lighting state CHANGE only (not the location's baseline lighting)
    if time_of_day:
        parts.append(_format_section(
            "LIGHTING STATE",
            f"Momentary lighting state: {time_of_day}."
        ))

    # 6. L11 tier muscular-build — slot 8_tier_build. The biggest single
    # contribution in compose_prompt; varies by (lineup_attached, stage_change,
    # tier). PHASE 3B — routed through rules._registry. FMG-only; non-FMG
    # projects skip via applicable_transformations and the tier line is
    # absent for non-FMG arc characters (a known gap until the BE/MMG/glute
    # variants are written).
    _apply_rule_at_slot("L11", "8_tier_build",
                        panel, ctx, parts, _trace, transformation_type)

    # 6a. L29 tier-6 reinforcement — slot 8b_tier_reinforcement. Fires only
    # when panel.muscle_size_tier == 6 AND both tier-6 reinforcement PNGs
    # were attached at generation time (build_plan sets
    # ctx['tier6_refs_attached']). Sits immediately after L11's lineup
    # directive so the surgical-scoping language for the reinforcement
    # refs is co-located with the lineup language and the model reads
    # them as a paired anchor.
    _apply_rule_at_slot("L29", "8b_tier_reinforcement",
                        panel, ctx, parts, _trace, transformation_type)

    # 6b. L30 tier-7 reinforcement — slot 8b_tier_reinforcement, sibling
    # of L29. Fires at panel.muscle_size_tier == 7 with both tier-7 refs
    # attached. Same slot as L29; multiple rules share the slot in
    # registry order — only one of L29/L30 fires per panel since the
    # tier match conditions are mutually exclusive.
    _apply_rule_at_slot("L30", "8b_tier_reinforcement",
                        panel, ctx, parts, _trace, transformation_type)

    # 6c. L31 tier-8 reinforcement — same slot, sibling of L29/L30.
    _apply_rule_at_slot("L31", "8b_tier_reinforcement",
                        panel, ctx, parts, _trace, transformation_type)

    # 6d. L32 tier-9 reinforcement — same slot, sibling of L29/L30/L31.
    _apply_rule_at_slot("L32", "8b_tier_reinforcement",
                        panel, ctx, parts, _trace, transformation_type)

    # 7. Environment — POST-REFACTOR (2026-05-23). Two slots:
    #   - 9_environment_match: MatchEnv emits the one-line match-the-
    #     attached-env-ref directive (was inline ENVIRONMENT prose).
    #   - 9_environment: L23 emits the dense verbal fallback ONLY when
    #     env_ref had to be dropped (3-ref ceiling).
    _apply_rule_at_slot("MATCH_ENV", "9_environment_match",
                        panel, ctx, parts, _trace, transformation_type)
    _apply_rule_at_slot("L23", "9_environment",
                        panel, ctx, parts, _trace, transformation_type)

    # 8. State anchor — POST-REFACTOR: routed through L1 (the new
    # match/match_prior_panel.py rule). Was inline STATE ANCHOR — L1.5
    # prose. The selection of WHICH prior panel happens in build_plan;
    # the match directive emission happens here.
    _apply_rule_at_slot("L1", "10_state_anchor",
                        panel, ctx, parts, _trace, transformation_type)

    # 9. L10 render directive — slot 11_render_directive. THE LOAD-BEARING L10
    # SENTENCE. PHASE 3A — routed through rules._registry.
    _apply_rule_at_slot("L10", "11_render_directive",
                        panel, ctx, parts, _trace, transformation_type)

    # 9a. L21 ref-exclusion — slot 12_ref_safety. PHASE 2/3 — routed through
    # rules._registry. Re-using the shared ctx (the standalone L21 ctx is no
    # longer needed; L21 reads env_ref / anchor / lineup_attached from ctx).
    _apply_rule_at_slot("L21", "12_ref_safety",
                        panel, ctx, parts, _trace, transformation_type)

    # 9b. L18 pose anatomy coherence — slot 13_anatomy_guardrail. Universal
    # soft guardrail. PHASE 3A — routed through rules._registry.
    _apply_rule_at_slot("L18", "13_anatomy_guardrail",
                        panel, ctx, parts, _trace, transformation_type)

    # 10. Mandatory anchors — POST-REFACTOR (2026-05-23):
    # Stripped appearance bits ("muscles natural healthy skin tone",
    # "skin subtle healthy sheen") — those come from the body-tier ref
    # and the face card per L10. "vivid expressive face" stays as a
    # MOOD directive (action-class). Anatomy moves out (L18 covers it
    # at slot 13_anatomy_guardrail). Size-monotonicity stays because
    # it's a state-continuity rule, not an appearance description.
    parts.append(_format_section(
        "MANDATORY ANCHORS",
        "Mood: vivid expressive face (not neutral or blank). "
        "Continuity: once a character has grown to a size they stay "
        "at that size or larger."
    ))

    # 10a. L19 lettering block — only emitted when the panel has any
    # dialogue, captions, or SFX. The 2D-flat scope is named explicitly so
    # the comic-coded vocabulary does NOT pull bodies/scene to 2D (the L7
    # Case B failure mode this block is designed to defuse).
    if (panel.get("dialogue") or panel.get("captions")
            or panel.get("sfx")):
        parts.append(_format_section(
            "LETTERING — L19 2D overlay",
            _l19_lettering_block(panel)
        ))

    # 11. Closing CGI anchor — explicitly scopes the negation to bodies/skin
    # so the bubble graphics are not implicated by "NOT illustrated."
    parts.append(_format_section(
        "CLOSING ANCHOR — CGI scope",
        "Photographic CGI render on the bodies, costumes, skin, hair, "
        "environment, and lighting; NOT a 2D illustration on the bodies, "
        "NOT cartoon-shaded skin. Only the bubble / caption / SFX graphics "
        "are flat 2D comic-book overlay."
    ))

    # Drop any empty sections (defensive — _format_section returns "" for
    # whitespace-only bodies). Join with blank-line separators so each
    # section is visually distinct in the rendered prompt.
    return "\n\n".join(p for p in parts if p)


# ---------------------------------------------------------------------------
# Main


def build_plan(root: Path, target_panel_id: str | None = None) -> dict:
    """Build a per-panel plan.

    When `target_panel_id` is None (default), composes for the next pending
    panel — the historical behavior. When set, composes for that specific
    panel using only the accepted history that exists for panels BEFORE it
    in story order. Used by `write_ledger.py` to emit retroactive ledgers
    for already-accepted panels.
    """
    shotlist = read_shotlist(root)
    if shotlist is None:
        return {"error": "No shotlist.json at project root", "project_root": str(root)}

    # Walk panels in story order
    accepted_history: list[dict] = []
    next_panel = None
    next_page = None

    if target_panel_id is None:
        # Legacy path: find the first pending panel; accepted_history is
        # everything accepted in story order.
        for page_num, panel in iter_panels(shotlist):
            status = panel_status(root, panel)
            if status["state"] == "accepted":
                accepted_history.append({"panel": panel, "page_number": page_num, "status": status})
            elif next_panel is None:
                next_panel = panel
                next_page = page_num
                # Don't break — we still want full history for context
    else:
        # Targeted path: find the specific panel; accepted_history is
        # everything accepted BEFORE it in story order (irrespective of
        # whether the target itself is accepted).
        for page_num, panel in iter_panels(shotlist):
            if (panel.get("panel_id") or panel.get("name")) == target_panel_id:
                next_panel = panel
                next_page = page_num
                break
            status = panel_status(root, panel)
            if status["state"] == "accepted":
                accepted_history.append({"panel": panel, "page_number": page_num, "status": status})
        if next_panel is None:
            return {
                "project_root": str(root),
                "next_panel": None,
                "message": f"target_panel_id={target_panel_id!r} not found in shotlist.json",
                "accepted_count": len(accepted_history),
            }

    if next_panel is None:
        return {
            "project_root": str(root),
            "next_panel": None,
            "message": "All shotlist panels have an accepted version. Nothing pending.",
            "accepted_count": len(accepted_history),
        }

    # Resolve refs and anchor for the next panel
    target_view = _canon_view(next_panel.get("camera") or "")
    anchor = pick_chain_anchor(root, target_view, accepted_history)
    stage_change = is_stage_change(next_panel, accepted_history)

    # Phase 1 trace — populated by compose_prompt's helper sites plus the
    # build-plan-level findings below. Transformation type read from
    # production-config.json (defaults to "fmg" for legacy projects).
    transformation_type = ((_read_production_config(root) or {})
                           .get("transformation_type") or "fmg")
    trace = _init_trace(transformation_type)

    refs_to_attach: list[dict] = []
    if anchor and anchor["status"].get("image"):
        refs_to_attach.append({
            "kind": "state_anchor",
            "from_panel": anchor["panel"].get("panel_id"),
            "path": str(anchor["status"]["image"].relative_to(root)),
            "reason": f"view-compatible prior ({anchor['panel'].get('camera')}) for target view ({target_view})",
        })
        # L1.5 applied case is recorded by compose_prompt's state-anchor block
    elif target_view == "ecu-face":
        refs_to_attach.append({
            "kind": "note",
            "from_panel": None,
            "path": None,
            "reason": "ecu-face: use face card alone as canonical anchor (no state anchor needed per L1.5 Rule #9)",
        })
        _record_skipped(trace, "L1.5",
                        "ecu-face: face card alone serves as the canonical anchor (L1.5 Rule #9)")
    elif not anchor and accepted_history:
        refs_to_attach.append({
            "kind": "note",
            "from_panel": None,
            "path": None,
            "reason": f"no view-compatible prior found for target view ({target_view}); fall back to canonical view-matched character ref + verbal state carry-forward",
        })
        _record_failed(trace, "L1.5",
                       pre_render_reason=f"no view-compatible prior in accepted_history for target view {target_view!r} — falling back to canonical ref + verbal state carry-forward")
    else:
        # First panel in the chain (no accepted_history yet)
        _record_skipped(trace, "L1.5",
                        "first panel in chain — no prior accepted panel exists yet")

    # Face card(s)
    for slug in next_panel.get("characters", []) or []:
        face = find_face_card(root, slug)
        if face:
            refs_to_attach.append({
                "kind": "face_card",
                "character": slug,
                "path": str(face.relative_to(root)),
                "reason": f"canonical face anchor for {slug}",
            })

    # Env ref — L10 env chaining: prefer first accepted panel in this location
    # over `_source.jpg`. The DAZ render is a stand-in; the accepted panel is
    # the real location.
    env_ref = None
    env_anchor_from = None
    loc_slug = next_panel.get("location")
    if loc_slug:
        env_anchor_from = pick_location_anchor(root, loc_slug, accepted_history)
        if env_anchor_from:
            env_ref = env_anchor_from["status"]["image"]
            refs_to_attach.append({
                "kind": "env_anchor",
                "location": loc_slug,
                "from_panel": env_anchor_from["panel"].get("panel_id"),
                "path": str(env_ref.relative_to(root)),
                "reason": f"L10 env chaining — accepted establishing shot for `{loc_slug}` "
                          f"from panel `{env_anchor_from['panel'].get('panel_id')}`",
            })
        else:
            env_ref = find_env_ref(root, loc_slug)
            if env_ref:
                refs_to_attach.append({
                    "kind": "env_ref",
                    "location": loc_slug,
                    "path": str(env_ref.relative_to(root)),
                    "reason": f"DAZ3D source ref for `{loc_slug}` — first appearance "
                              f"of this location; once this panel is accepted, "
                              f"subsequent panels will chain off its image instead",
                })

    # Lineup ref attachment per L11 (broader than L5): attach on stage-change
    # AND on every full-body camera panel of the arc character. Reason: the
    # body is the focal subject on full-body shots and the muscular build needs
    # the lineup anchor or the model regresses to realistic-fitness builds.
    # find_lineup() searches multiple paths; if it returns None when we should
    # attach, surface that loudly so the agent can fix the asset location
    # before generating.
    tier = next_panel.get("muscle_size_tier")
    lineup_attached = False
    if should_attach_lineup(next_panel, stage_change):
        camera_first = (next_panel.get("camera") or "").split(",")[0].strip()
        reason_label = "STAGE-CHANGE" if stage_change else f"FULL-BODY camera ({camera_first})"
        lineup = find_lineup(root, tier)
        if lineup:
            refs_to_attach.append({
                "kind": "lineup",
                "tier": tier,
                "path": str(lineup),
                "reason": f"{reason_label} panel (tier={tier}) — lineup ref MUST be "
                          f"attached so the model has a 3D muscular-build target. "
                          f"Per L11 (cartoony FMG proportions need explicit anchoring).",
            })
            lineup_attached = True
            _record_applied(trace, "L28",
                            pre_render_reason=f"required lineup ref present on disk: {lineup}")
        else:
            missing_reason = (
                f"{reason_label} panel (tier={tier}) but lineup file NOT FOUND on disk. "
                f"Tried: project references/style/, repo assets/, ~/.claude/skills/.../assets/. "
                f"Drop a muscle-size-lineup.png (tiers 1-6) or muscle-size-lineup-4-9.png (tiers 7+) "
                f"into one of those locations before generating. Falling back to verbal-only "
                f"muscular-build instructions, which is significantly less reliable."
            )
            refs_to_attach.append({
                "kind": "MISSING_lineup",
                "tier": tier,
                "path": None,
                "reason": missing_reason,
            })
            # L28-style hard failure: a declared/required ref isn't on disk.
            _record_failed(trace, "L28",
                           pre_render_reason=f"MISSING_lineup: {missing_reason}")
    else:
        _record_skipped(trace, "L28",
                        "no lineup required for this panel (not stage-change AND not full-body camera AND no manifest miss observed)")

    # L29 — tier-6 reinforcement refs. Attaches BOTH dedicated tier-6
    # anatomical PNGs (peak-body-scale/tier-6/) on top of the lineup
    # whenever `panel.muscle_size_tier == 6`. The lineup interpolates the
    # tier-6 figure downward against the other five figures on the chart;
    # the reinforcement refs isolate tier-6 proportions as their own
    # dedicated anchor. See L29 (`rules/l29_tier6_reinforcement.py`).
    tier6_refs_attached = False
    if should_attach_tier6_reinforcement(next_panel):
        tier6_refs = find_tier6_reinforcement_refs(root)
        if len(tier6_refs) == len(TIER6_REINFORCEMENT_FILENAMES):
            for ref_path in tier6_refs:
                refs_to_attach.append({
                    "kind": "tier6_reinforcement",
                    "tier": 6,
                    "path": str(ref_path),
                    "reason": (
                        f"TIER-6 panel — `{ref_path.name}` MUST be attached "
                        "alongside the muscle-size lineup. The lineup alone "
                        "interpolates tier-6 downward; the dedicated tier-6 "
                        "reinforcement sheets isolate the peak proportions. "
                        "Per L29 (tier-6 needs dedicated proportion reinforcement)."
                    ),
                })
            tier6_refs_attached = True
        else:
            missing_t6_reason = (
                "TIER-6 panel but one or both tier-6 reinforcement PNGs NOT "
                "FOUND on disk. Tried: project references/style/, repo "
                "skills/comic-production/references/peak-body-scale/tier-6/, "
                "~/.claude/skills/.../peak-body-scale/tier-6/. Drop both "
                f"{', '.join(TIER6_REINFORCEMENT_FILENAMES)} into one of "
                "those locations before generating. Falling back to lineup-"
                "only is significantly less reliable at tier 6 (per L29)."
            )
            refs_to_attach.append({
                "kind": "MISSING_tier6_reinforcement",
                "tier": 6,
                "path": None,
                "reason": missing_t6_reason,
            })

    # L30 — tier-7 reinforcement refs. Same pattern as L29 but for
    # `panel.muscle_size_tier == 7`. The tier-4-to-9 lineup chart
    # interpolates the tier-7 figure toward the middle of the chart
    # (tiers 5-6); the dedicated tier-7 reinforcement sheets isolate
    # the beyond-peak proportions. See L30
    # (`rules/l30_tier7_reinforcement.py`).
    tier7_refs_attached = False
    if should_attach_tier7_reinforcement(next_panel):
        tier7_refs = find_tier7_reinforcement_refs(root)
        if len(tier7_refs) == len(TIER7_REINFORCEMENT_FILENAMES):
            for ref_path in tier7_refs:
                refs_to_attach.append({
                    "kind": "tier7_reinforcement",
                    "tier": 7,
                    "path": str(ref_path),
                    "reason": (
                        f"TIER-7 panel — `{ref_path.name}` MUST be attached "
                        "alongside the muscle-size lineup-4-9. The lineup "
                        "alone interpolates tier-7 toward the chart's "
                        "middle; the dedicated tier-7 reinforcement sheets "
                        "isolate the beyond-peak proportions. Per L30."
                    ),
                })
            tier7_refs_attached = True
        else:
            missing_t7_reason = (
                "TIER-7 panel but one or both tier-7 reinforcement PNGs NOT "
                "FOUND on disk. Tried: project references/style/, repo "
                "skills/comic-production/references/peak-body-scale/tier-7/, "
                "~/.claude/skills/.../peak-body-scale/tier-7/. Drop both "
                f"{', '.join(TIER7_REINFORCEMENT_FILENAMES)} into one of "
                "those locations before generating. Falling back to lineup-"
                "only is significantly less reliable at tier 7 (per L30)."
            )
            refs_to_attach.append({
                "kind": "MISSING_tier7_reinforcement",
                "tier": 7,
                "path": None,
                "reason": missing_t7_reason,
            })

    # L31 — tier-8 reinforcement refs. Same pattern as L29/L30 at
    # `panel.muscle_size_tier == 8`.
    tier8_refs_attached = False
    if should_attach_tier8_reinforcement(next_panel):
        tier8_refs = find_tier8_reinforcement_refs(root)
        if len(tier8_refs) == len(TIER8_REINFORCEMENT_FILENAMES):
            for ref_path in tier8_refs:
                refs_to_attach.append({
                    "kind": "tier8_reinforcement",
                    "tier": 8,
                    "path": str(ref_path),
                    "reason": (
                        f"TIER-8 panel — `{ref_path.name}` MUST be attached "
                        "alongside the muscle-size lineup-4-9. Per L31 "
                        "(tier-8 needs dedicated proportion reinforcement)."
                    ),
                })
            tier8_refs_attached = True
        else:
            missing_t8_reason = (
                "TIER-8 panel but one or both tier-8 reinforcement PNGs NOT "
                "FOUND on disk. Drop both "
                f"{', '.join(TIER8_REINFORCEMENT_FILENAMES)} into "
                "skills/comic-production/references/peak-body-scale/tier-8/ "
                "(or project references/style/) before generating. Per L31."
            )
            refs_to_attach.append({
                "kind": "MISSING_tier8_reinforcement",
                "tier": 8,
                "path": None,
                "reason": missing_t8_reason,
            })

    # L32 — tier-9 reinforcement refs. Same pattern as L29/L30/L31 at
    # `panel.muscle_size_tier == 9`. Both files are intentionally the
    # same composite image (user-directed Grok edit); the dual attach
    # still gives the model two ref slots pointing at calibrated
    # tier-9 proportions.
    tier9_refs_attached = False
    if should_attach_tier9_reinforcement(next_panel):
        tier9_refs = find_tier9_reinforcement_refs(root)
        if len(tier9_refs) == len(TIER9_REINFORCEMENT_FILENAMES):
            for ref_path in tier9_refs:
                refs_to_attach.append({
                    "kind": "tier9_reinforcement",
                    "tier": 9,
                    "path": str(ref_path),
                    "reason": (
                        f"TIER-9 panel — `{ref_path.name}` MUST be attached "
                        "alongside the muscle-size lineup-4-9. Per L32 "
                        "(tier-9 needs dedicated proportion reinforcement)."
                    ),
                })
            tier9_refs_attached = True
        else:
            missing_t9_reason = (
                "TIER-9 panel but one or both tier-9 reinforcement PNGs NOT "
                "FOUND on disk. Drop both "
                f"{', '.join(TIER9_REINFORCEMENT_FILENAMES)} into "
                "skills/comic-production/references/peak-body-scale/tier-9/ "
                "(or project references/style/) before generating. Per L32."
            )
            refs_to_attach.append({
                "kind": "MISSING_tier9_reinforcement",
                "tier": 9,
                "path": None,
                "reason": missing_t9_reason,
            })

    # L12 + L13: surface shotlist-shape warnings at planning time so the agent
    # driving generation can fix the shotlist or override before paying for an
    # output that's broken-by-design. These warnings live alongside MISSING_*
    # entries in refs_to_attach so the build-comic HALT rule catches them.
    conflict, speakers = detect_dialogue_camera_conflict(next_panel)
    if conflict:
        l12_reason = (
            f"L12 violation: panel has on-screen dialogue from {speakers} but "
            f"camera is `{target_view}` (too wide for the speaker to be the focal "
            "point). Either tighten the camera (mcu / medium / cowboy / ecu-face) "
            "or convert the dialogue to a caption / off-panel type. Rendering "
            "at the current camera will produce a panel where the reader can't "
            "tell who's talking."
        )
        refs_to_attach.append({
            "kind": "WARNING_DIALOGUE_CAMERA_CONFLICT",
            "speakers": speakers,
            "camera": target_view,
            "reason": l12_reason,
        })
        _record_failed(trace, "L12", pre_render_reason=l12_reason)
    else:
        _record_skipped(trace, "L12",
                        "no dialogue/camera conflict — either no on-screen dialogue or camera is close enough")
    split_needed, n_lines, n_speakers = detect_multi_speaker_crowding(next_panel)
    if split_needed:
        l13_reason = (
            f"L13 violation: panel has {n_lines} on-screen dialogue lines from "
            f"{n_speakers} distinct speakers. Rendering all of them in one image "
            "produces a cramped sitcom-freeze-frame. Split this beat into "
            f"{n_lines} per-speaker panels in the shotlist; each new panel "
            "frames the speaker who's talking on it."
        )
        refs_to_attach.append({
            "kind": "WARNING_MULTI_SPEAKER_CROWDING",
            "n_lines": n_lines,
            "n_speakers": n_speakers,
            "reason": l13_reason,
        })
        _record_failed(trace, "L13", pre_render_reason=l13_reason)
    else:
        _record_skipped(trace, "L13",
                        f"single-speaker (or zero-speaker) panel — n_lines={n_lines}, n_speakers={n_speakers}")

    too_far, beat, dscore, beat_max = detect_camera_too_far_for_beat(next_panel)
    if too_far:
        l20_chapter_reason = (
            f"L20 overshoot: beat `{beat}` is shot at `{target_view}` "
            f"(distance score {dscore}); typical ceiling for this beat is {beat_max}. "
            "Body-region transformation beats need the region to dominate the frame; "
            "full-body framings make the change small and the panel reads as "
            "before/after rather than the change happening now. Tighten the camera "
            "(MCU or ecu-region) or accept the finding if this beat doubles as an "
            "establishing shot. See script-breakdown SKILL.md § Step 4.5 and "
            "camera-distance-analysis/README.md."
        )
        refs_to_attach.append({
            "kind": "WARNING_CAMERA_TOO_FAR_FOR_BEAT",
            "beat": beat,
            "camera": target_view,
            "distance_score": dscore,
            "beat_max_score": beat_max,
            "reason": l20_chapter_reason,
        })
        _record_failed(trace, "L20_chapter",
                       pre_render_reason=l20_chapter_reason)
    else:
        _record_skipped(trace, "L20_chapter",
                        f"camera {target_view!r} within beat ceiling for beat={beat!r}")

    aspect = ASPECT_FOR_CAMERA.get(target_view, "3:4")

    # L23 enforcement: count attached refs against the model's 3-ref ceiling.
    # If we'd exceed it, drop env (most recoverable via the dense verbal anchor
    # in the prompt). Count: face card(s) per character + state_anchor + lineup
    # + env. Stage-change full-body panels typically have face + state-anchor +
    # lineup at minimum, which already hits 3.
    n_face_cards = sum(1 for r in refs_to_attach if r.get("kind") == "face_card")
    n_state_anchor = 1 if (anchor and anchor["status"].get("image")) else 0
    n_lineup = 1 if lineup_attached else 0
    n_env = 1 if env_ref else 0
    n_tier6 = sum(1 for r in refs_to_attach if r.get("kind") == "tier6_reinforcement")
    n_tier7 = sum(1 for r in refs_to_attach if r.get("kind") == "tier7_reinforcement")
    n_tier8 = sum(1 for r in refs_to_attach if r.get("kind") == "tier8_reinforcement")
    n_tier9 = sum(1 for r in refs_to_attach if r.get("kind") == "tier9_reinforcement")
    total_refs = n_face_cards + n_state_anchor + n_lineup + n_env + n_tier6 + n_tier7 + n_tier8 + n_tier9

    env_dropped_for_ceiling = False
    composer_env_ref: Path | None = env_ref
    composer_env_anchor_from = env_anchor_from
    if total_refs > 3 and env_ref:
        env_dropped_for_ceiling = True
        composer_env_ref = None
        composer_env_anchor_from = None
        # Mark the env entry in refs_to_attach as "dropped for ceiling" so the
        # production driver knows the prompt has the verbal anchor instead.
        for r in refs_to_attach:
            if r.get("kind") in ("env_ref", "env_anchor"):
                r["kind"] = f"{r['kind']}_dropped_for_ceiling"
                r["reason"] = (
                    "DROPPED to fit the 3-ref ceiling — prompt instead "
                    "carries a dense verbal env anchor (L23). Do NOT attach "
                    "this ref at submit time; use the verbal anchor in the "
                    "composed prompt as the location signal."
                )
                break

    # Per-model muscularity ceiling check (May 14 finding). build_plan does
    # not know which model the production driver will use, so this is a hint
    # rather than an enforcement: surface a WARNING when the panel's tier
    # exceeds any known ceiling. The driver picks the model.
    if tier is not None:
        try:
            t_int = int(tier)
        except (TypeError, ValueError):
            t_int = None
        if t_int is not None:
            for model_id, ceiling in MODEL_MUSCULARITY_CEILING.items():
                if t_int > ceiling:
                    refs_to_attach.append({
                        "kind": "WARNING_MODEL_MUSCULARITY_CEILING",
                        "model": model_id,
                        "tier": t_int,
                        "ceiling": ceiling,
                        "reason": (
                            f"Tier {t_int} exceeds the observed muscularity "
                            f"ceiling for model `{model_id}` (≈ tier {ceiling} "
                            "on female anatomy). If using this model, expect "
                            "the muscular build to regress toward fitness-model "
                            "build regardless of prompt or lineup ref. "
                            "Recommend routing to nano_banana_flash or "
                            "nano_banana_2 for this panel. See chun-li-grok-"
                            "validation/ for empirical evidence."
                        ),
                    })

    prompt = compose_prompt(next_panel, shotlist, anchor, stage_change,
                            composer_env_ref,
                            env_anchor_from=composer_env_anchor_from,
                            lineup_attached=lineup_attached,
                            env_dropped=env_dropped_for_ceiling,
                            tier6_refs_attached=tier6_refs_attached,
                            tier7_refs_attached=tier7_refs_attached,
                            tier8_refs_attached=tier8_refs_attached,
                            tier9_refs_attached=tier9_refs_attached,
                            _trace=trace,
                            transformation_type=transformation_type)

    return {
        "project_root": str(root),
        "next_panel": {
            "panel_id": next_panel.get("panel_id"),
            "page_number": next_page,
            "camera": next_panel.get("camera"),
            "characters": next_panel.get("characters", []),
            "location": next_panel.get("location"),
            "action": next_panel.get("action"),
            "muscle_size_tier": tier,
        },
        "accepted_count": len(accepted_history),
        "remaining_count": sum(1 for _, _ in iter_panels(shotlist)) - len(accepted_history),
        "aspect": aspect,
        "count": "x4",  # Flow default per shotlist-driven-flow.md
        "refs_to_attach_in_order": refs_to_attach,
        "stage_change": stage_change,
        "composed_prompt": prompt,
        "anchor_panel_id": anchor["panel"].get("panel_id") if anchor else None,
        "transformation_type": transformation_type,
        "_trace": trace,
    }


def render_plan_text(plan: dict) -> str:
    """Render the plan as readable text for Claude to consume in a non-JSON context."""
    if plan.get("error"):
        return f"ERROR: {plan['error']}"
    if plan.get("next_panel") is None:
        return f"✅ No pending panels. {plan['accepted_count']} accepted."

    np = plan["next_panel"]
    lines = [
        f"## Next Panel: {np['panel_id']} (page {np['page_number']})",
        "",
        f"- Camera: {np['camera']}",
        f"- Characters: {', '.join(np['characters']) or '(none)'}",
        f"- Location: {np['location'] or '(none)'}",
        f"- Action: {np['action'] or '(none)'}",
        f"- Muscle size tier: {np['muscle_size_tier'] or '(n/a)'}",
        f"- Aspect: {plan['aspect']} · Count: {plan['count']}",
        f"- Anchor panel: {plan['anchor_panel_id'] or '(none — fallback to canonical refs)'}",
        f"- Stage-change panel: {plan['stage_change']}",
        f"- Progress: {plan['accepted_count']}/{plan['accepted_count'] + plan['remaining_count']} accepted",
        "",
        "## Refs to attach (in this order)",
    ]
    for r in plan["refs_to_attach_in_order"]:
        lines.append(f"- **{r['kind']}**: {r.get('path') or '—'} ({r['reason']})")
    lines.append("")
    lines.append("## Composed prompt (paste into Flow as a single line)")
    lines.append("")
    lines.append("```")
    lines.append(plan["composed_prompt"])
    lines.append("```")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--as-json", action="store_true",
                        help="Output JSON instead of human-readable text")
    args = parser.parse_args()

    root = args.project_root.expanduser().resolve()
    if not root.exists():
        print(f"error: project root does not exist: {root}", file=sys.stderr)
        sys.exit(1)

    plan = build_plan(root)
    if args.as_json:
        print(json.dumps(plan, indent=2, default=str))
    else:
        print(render_plan_text(plan))


if __name__ == "__main__":
    main()
