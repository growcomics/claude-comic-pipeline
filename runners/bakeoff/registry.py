#!/usr/bin/env python3
"""Canonical defect-registry bindings for the bakeoff lane.

Single source of truth is skills/comic-production/references/defect-registry.json —
this module only READS it (never redefines IDs; see project_defect_registry doctrine).
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
REGISTRY_JSON = REPO / "skills/comic-production/references/defect-registry.json"


@lru_cache(maxsize=1)
def registry() -> dict:
    return json.loads(REGISTRY_JSON.read_text())


@lru_cache(maxsize=1)
def by_ck_type() -> dict:
    """Map ck_ai_qa 'typed' slugs (ck_type) -> registry record."""
    out = {}
    for d in registry()["defects"]:
        ck = d.get("ck_type")
        if ck and ck not in out:
            out[ck] = d
    return out


@lru_cache(maxsize=1)
def by_id() -> dict:
    return {d["id"]: d for d in registry()["defects"]}


def resolve(typed: list[dict], *, beat_kind: str = "panel") -> list[dict]:
    """Map ck_ai_qa typed defects to registry records with a blocking verdict.

    A variant is BLOCKED by any defect whose registry severity is 'blocker', or
    any typed defect the vision model itself rated high-severity.
    Ref-sheet exception (picks-profile B95): garbled/baked lettering does not
    block reference sheets — sheet labels are informational, not comic lettering.
    """
    out = []
    for t in typed:
        rec = by_ck_type().get(t.get("type", "other"))
        rid = rec["id"] if rec else "MISC-00"
        sev = rec["severity"] if rec else "major"
        blocking = sev == "blocker" or t.get("sev") == "high"
        if beat_kind == "sheet" and rid.startswith("LET-"):
            blocking = False
        # Multi-phase sequence splashes (grid-break full-pagers) repeat the same
        # character by design — duplicate-character is the point, not a defect.
        if beat_kind == "sequence" and rid in ("CAST-01", "CAST-02", "CAST-03"):
            blocking = False
        out.append({
            "id": rid, "slug": (rec or {}).get("slug", t.get("type")),
            "sev": sev, "model_sev": t.get("sev"), "detail": t.get("detail", ""),
            "blocking": blocking,
        })
    return out


# What to tell the generator on a re-roll, per registry ID. These are corrective
# clauses injected into the retry prompt (pillar 3) — targeted, not a rule wall.
RETRY_INJECTION = {
    "CAST-01": "CRITICAL FIX: the previous roll DUPLICATED a character. Each named character appears exactly ONCE in the panel.",
    "CAST-02": "CRITICAL FIX: the previous roll added an unnamed extra person. ONLY the named cast appears — zero background people, pedestrians, or bystanders.",
    "CAST-03": "FIX: wrong number of people last roll. The panel contains exactly the characters named in this prompt, no more, no fewer.",
    "FACE-01": "FIX: faces were wooden last roll. The named emotion must visibly transform the whole face — eyes, brows, open mouth.",
    "WARD-01": "CRITICAL FIX: wardrobe drifted last roll. Garments must match the attached reference images EXACTLY — same color, cut, and coverage state.",
    "PROP-01": "FIX: an anachronistic prop (wristwatch/phone/modern item) appeared last roll. No wristwatches. No modern devices unless named in this prompt.",
    "BODY-03": "FIX: wrong transformation stage last roll. Match the muscle size shown in the attached stage reference exactly — do not scale it up or down.",
    "BODY-05": "CRITICAL FIX: malformed anatomy last roll (extra/missing limbs or digits, impossible joints). Anatomy must be structurally correct.",
    "LET-01": "CRITICAL FIX: lettering was missing last roll. Render every quoted line inside a clean flat 2D WHITE speech bubble exactly as specified (L19) — a specified line with a blank or missing bubble is a defect.",
    "LET-02": "CRITICAL FIX: lettering was garbled last roll. Bubble text must be crisp, correctly spelled, and match the quoted dialogue exactly.",
    "PROP-02": "CRITICAL FIX: a reference image was rendered as an object inside the scene last roll. Reference images define appearance ONLY — never draw them as posters, screens, or pictures in the panel.",
    "STYLE-01": "CRITICAL FIX: style drifted to 2D last roll. Render as photoreal DAZ3D/Iray CGI — NOT flat illustration, NOT cel shading, NOT anime, NOT comic-book linework.",
    "MISC-00": "FIX the specific defect noted from the previous roll.",
}


def injections_for(resolved: list[dict]) -> list[str]:
    """Ordered, deduped corrective clauses for the blocking defects of a round."""
    seen, out = set(), []
    for d in resolved:
        if not d["blocking"]:
            continue
        clause = RETRY_INJECTION.get(d["id"], RETRY_INJECTION["MISC-00"])
        detail = (d.get("detail") or "").strip()
        if detail:
            clause = f"{clause} (observed: {detail[:120]})"
        if d["id"] not in seen:
            seen.add(d["id"])
            out.append(clause)
    return out
