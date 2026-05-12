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
    """Determine whether a panel has been generated/accepted, and how."""
    panel_id = panel.get("panel_id") or panel.get("name") or "<unknown>"
    panels_root = root / "pages" / "panels"

    # Folder layout: pages/panels/<panel_id>/v*.png + _accepted.txt
    folder = panels_root / panel_id
    if folder.is_dir():
        accepted_marker = folder / "_accepted.txt"
        if accepted_marker.exists():
            label = accepted_marker.read_text().strip()
            cand = folder / f"{label}.png"
            if cand.exists():
                return {"state": "accepted", "image": cand, "label": label}
            return {"state": "accepted", "image": None, "label": label}
        # Folder exists but no _accepted yet — has variants pending
        variants = sorted(p for p in folder.iterdir()
                          if p.suffix.lower() in {".png", ".jpg", ".jpeg"}
                          and p.stem.startswith("v"))
        if variants:
            return {"state": "in_progress", "image": None, "label": None,
                    "pending_variants": len(variants)}

    # Flat layout fallback: pages/panels/<panel_id>.png
    for suffix in (".png", ".jpg", ".jpeg"):
        flat = panels_root / f"{panel_id}{suffix}"
        if flat.exists():
            return {"state": "accepted", "image": flat, "label": "v1 (flat)"}

    return {"state": "pending", "image": None, "label": None}


# ---------------------------------------------------------------------------
# View-aware anchor selection


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
        prior_view = item["panel"].get("camera") or item["panel"].get("view") or ""
        # Normalize: handle "low-angle-front, three-quarter" → take first token
        prior_view = prior_view.split(",")[0].strip()
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


def find_lineup(root: Path, tier: int | None) -> Path | None:
    """Pick the appropriate lineup file based on the tier. The skill's assets/
    folder is at the user's ~/.claude/skills/comic-production/assets/."""
    if tier is None:
        return None
    skill_root = Path.home() / ".claude" / "skills" / "comic-production" / "assets"
    if tier <= 6:
        p = skill_root / "muscle-size-lineup.png"
    else:
        p = skill_root / "muscle-size-lineup-4-9.png"
    return p if p.exists() else None


# ---------------------------------------------------------------------------
# Prompt composer


def compose_prompt(panel: dict, shotlist: dict, anchor: dict | None,
                   stage_change: bool, env_ref: Path | None,
                   env_anchor_from: dict | None = None) -> str:
    """Compose a starter prompt for this panel — L10 delta-only skeleton.

    The body describes only what is *new* in this panel (camera, action,
    expression, lighting state change, costume state change). Constants
    (character identity, costume design, location architecture) are
    delegated to the attached references via an explicit render directive.

    `env_anchor_from`: when L10 env chaining promoted a prior accepted panel
    to env anchor (instead of `_source.jpg`), this is that history item.
    The prompt language adapts so the model knows it's chaining off the
    actual chamber image rather than a stand-in DAZ render.

    Single-line output (Flow treats `\\n` as submit; use period-separated
    sentences within one continuous string).
    """

    camera = (panel.get("camera") or "").split(",")[0].strip()
    action = (panel.get("action") or "").strip()
    location_slug = panel.get("location") or ""
    chars = panel.get("characters") or []
    tier = panel.get("muscle_size_tier")
    time_of_day = panel.get("time_of_day") or ""

    parts: list[str] = []

    # 1. Render anchor (positive CGI vocabulary, L7-compliant)
    parts.append(
        "DAZ Studio Iray render of a real 3D scene. Ray-traced subsurface "
        "scattering on skin, specular highlights catching warm rim light, "
        "physically-accurate fabric weave with visible thread detail, "
        "8K texture detail, shallow depth of field with photographic bokeh."
    )

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
    parts.append(cam_fragments.get(camera,
        f"Camera: {camera or 'eye-level medium shot'}."))

    # 3. Subjects (name only — identity comes from attached face cards)
    if chars:
        parts.append(f"Subjects: {', '.join(chars)}.")

    # 4. DELTA — action / pose / expression. Wrapped with a sanitization
    #    directive so the model knows: even if the action text mentions
    #    things that look like constants (clothing, wall types, etc.),
    #    those are *cues for the action context only*, not redescriptions.
    if action:
        action_clean = action.rstrip(".")
        parts.append(
            f"DELTA — action only: {action_clean}. (Any mention of clothing, "
            "architecture, or character features in the delta is contextual "
            "shorthand; the visual identity of those things comes from the "
            "attached references.)"
        )

    # 5. Lighting state CHANGE only (not the location's baseline lighting)
    if time_of_day:
        parts.append(f"Momentary lighting state: {time_of_day}.")

    # 6. Size tier — applied via the lineup ref when stage_change, or by name
    if tier is not None:
        if stage_change:
            parts.append(
                f"Size tier: {tier}. Match the muscle proportions, breast "
                f"proportions, and waist of figure {tier} in the attached "
                f"muscle-size lineup reference."
            )
        else:
            parts.append(
                f"Size tier: {tier}. Carry forward the build from the prior "
                f"accepted panel (no growth in this panel; size is unchanged)."
            )

    # 7. Environment — env-chaining-aware language
    if env_ref:
        if env_anchor_from:
            parts.append(
                f"Location: {location_slug}. The attached environment "
                f"reference IS this location — it's the accepted establishing "
                f"shot from panel `{env_anchor_from['panel'].get('panel_id')}`. "
                "Render the same architecture, the same wall layout, the same "
                "equipment placement, the same scale, the same depth. The "
                "delta describes ONLY what is happening in this panel; the "
                "location itself is fixed by this reference."
            )
        else:
            parts.append(
                f"Location: {location_slug}. The attached environment reference "
                "establishes the location's render style — Iray quality, "
                "lighting setup, scale, depth, atmosphere. Use it as the visual "
                "anchor for the location's architecture. Do not reinterpret."
            )

    # 8. State anchor — prior panel for costume/hair/body/damage continuity
    if anchor:
        anchor_view = anchor["panel"].get("camera", "?")
        parts.append(
            f"State anchor: prior panel `{anchor['panel'].get('panel_id', '?')}` "
            f"({anchor_view}) is attached as a reference. Preserve costume "
            "state, hair state, body size, and any cumulative damage from "
            "that panel exactly. Costume tears never regress across panels."
        )

    # 9. Render directive — THE LOAD-BEARING L10 SENTENCE
    parts.append(
        "RENDER DIRECTIVE: render the attached references exactly as shown. "
        "Do not reinterpret character appearance, costume design, or location "
        "architecture from the prompt text. Those are FIXED by the references. "
        "The prompt describes only what is new in this panel — camera, action, "
        "expression, momentary lighting state, momentary costume state change. "
        "References override prompt text on all visual identity."
    )

    # 10. Mandatory rules (L7-compliant — no rendered lettering)
    parts.append(
        "Mandatory: muscles natural healthy skin tone (NOT red, NOT inflamed); "
        "skin has subtle healthy sheen, not oiled or wet; vivid expressive face "
        "(not neutral or blank); correct human anatomy with exactly two arms "
        "and exactly two legs; once a character has grown to a size they stay "
        "at that size or larger; NO speech bubbles, NO SFX text, NO captions, "
        "NO action lines in the render — all lettering is added in post by "
        "page-composer."
    )

    # 11. Closing CGI anchor
    parts.append("Photographic CGI render, NOT illustrated.")

    return " ".join(parts)


# ---------------------------------------------------------------------------
# Main


def build_plan(root: Path) -> dict:
    shotlist = read_shotlist(root)
    if shotlist is None:
        return {"error": "No shotlist.json at project root", "project_root": str(root)}

    # Walk panels in story order
    accepted_history: list[dict] = []
    next_panel = None
    next_page = None

    for page_num, panel in iter_panels(shotlist):
        status = panel_status(root, panel)
        if status["state"] == "accepted":
            accepted_history.append({"panel": panel, "page_number": page_num, "status": status})
        elif next_panel is None:
            next_panel = panel
            next_page = page_num
            # Don't break — we still want full history for context

    if next_panel is None:
        return {
            "project_root": str(root),
            "next_panel": None,
            "message": "All shotlist panels have an accepted version. Nothing pending.",
            "accepted_count": len(accepted_history),
        }

    # Resolve refs and anchor for the next panel
    target_view = (next_panel.get("camera") or "").split(",")[0].strip()
    anchor = pick_chain_anchor(root, target_view, accepted_history)
    stage_change = is_stage_change(next_panel, accepted_history)

    refs_to_attach: list[dict] = []
    if anchor and anchor["status"].get("image"):
        refs_to_attach.append({
            "kind": "state_anchor",
            "from_panel": anchor["panel"].get("panel_id"),
            "path": str(anchor["status"]["image"].relative_to(root)),
            "reason": f"view-compatible prior ({anchor['panel'].get('camera')}) for target view ({target_view})",
        })
    elif target_view == "ecu-face":
        refs_to_attach.append({
            "kind": "note",
            "from_panel": None,
            "path": None,
            "reason": "ecu-face: use face card alone as canonical anchor (no state anchor needed per L1.5 Rule #9)",
        })
    elif not anchor and accepted_history:
        refs_to_attach.append({
            "kind": "note",
            "from_panel": None,
            "path": None,
            "reason": f"no view-compatible prior found for target view ({target_view}); fall back to canonical view-matched character ref + verbal state carry-forward",
        })

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

    # Lineup ref (only on stage-change panels)
    tier = next_panel.get("muscle_size_tier")
    if stage_change and tier is not None:
        lineup = find_lineup(root, tier)
        if lineup:
            refs_to_attach.append({
                "kind": "lineup",
                "tier": tier,
                "path": str(lineup),
                "reason": f"stage-change panel (tier={tier}) — attach lineup per L5",
            })

    aspect = ASPECT_FOR_CAMERA.get(target_view, "3:4")
    prompt = compose_prompt(next_panel, shotlist, anchor, stage_change, env_ref,
                            env_anchor_from=env_anchor_from)

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
