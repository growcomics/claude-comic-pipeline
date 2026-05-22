"""L33 — Body-region focus panels need calibrated 2D action-line + SFX overlay.

Body-region extreme-close-ups (bicep flex, chest peak, abs hardening, glute
flex, quad pump) on photoreal CGI render flat without comic-genre energy.
The fix is a scope-bounded 2D overlay layer composited ON TOP of the
photoreal bicep/chest/etc: a radial burst of action lines emanating from
the focal point plus a single SFX word in classic comic-burst lettering.

Calibration ran 2026-05-17 via a 13-variant PIL programmatic matrix on the
Rogue bicep-flex source. User picked:

  Baseline (tier 1-5): A2 lines (medium, 10-12 mixed-thickness radial)
                       + B2 SFX (medium FLEX-style word, ~15% frame height,
                       behind/beside the body region, classic burst).
  Tier 6+:             A3 lines (heavy, 18-25 dense + chromatic accent)
                       + B2 SFX (held constant). One-step escalation on
                       lines only — the calibration showed bumping BOTH
                       crowded the photoreal tone.

  Body-region scope:   bicep / chest / abs / glutes / quads. Face ECUs and
                       full-body shots OUT of scope.

The overlay is a 2D vector layer (matches L19's lettering metaphor) — the
underlying bicep/chest/etc stays photoreal CGI with ray-traced SSS, the
lines and SFX sit ON TOP as a clearly named overlay layer that does NOT
turn the body 2D.

See:
  - skills/comic-production/references/lessons-learned.md § L33
  - skills/comic-production/references/the-rules-explained.md § L33
  - skills/comic-production/references/sfx-calibration/ (the matrix +
    contact sheet + the chosen-level samples)

This rule layers ON TOP of L20: L20 forces the ECU framing on body-region
panels; L33 adds the SFX treatment to that same framing. Both fire on
overlapping but not identical sets of `transformation_beat` values — L20
fires on the full body-region set including shoulders/back/hips/suit_fail,
L33 fires only on the calibrated subset (arms/chest/abs/rear/legs).
"""

from __future__ import annotations

from ._base import Rule, Verification, STATUS_PASS, STATUS_SKIPPED


# Body-region transformation_beat values where L33 fires. Subset of L20's
# body-region beats — these are the regions the May 2026 calibration covered.
# arms == bicep, rear == glutes, legs == quads, plus chest and abs.
_L33_BEATS = {"arms", "chest", "abs", "rear", "legs"}

# Friendly region label per beat — substituted into the prompt fragment.
_BEAT_TO_REGION = {
    "arms":  "bicep / arm",
    "chest": "chest / pec",
    "abs":   "abdomen",
    "rear":  "glute / rear",
    "legs":  "quad / leg",
}

# Tier at which we escalate one level on action lines. Calibration explicitly
# picked tier 6 as the boundary (matches L29 — peak-tier work starts at 6).
_TIER_ESCALATION_THRESHOLD = 6

# Calibrated levels, encoded as verbal-density descriptions the rendering
# model can interpret. These are the exact A2/A3/B2 wording from the
# 2026-05-17 calibration matrix and must stay in sync with the contact
# sheet's per-cell sub-descriptions.
_LEVELS = {
    "lines_baseline": (
        "MEDIUM-density radial action lines: 10-12 strokes emanating outward "
        "from the body-region focal point, mix of thin and bold widths, white "
        "with light edge glow, clearly readable as a comic-book energy burst "
        "but NOT dominant"
    ),
    "lines_tier6_plus": (
        "HEAVY radial action lines: 18-25 dense strokes emanating outward "
        "from the body-region focal point, bold widths with slight chromatic-"
        "aberration accent (faint cyan/magenta fringing on the outer edges), "
        "reads as peak-tier energy burst"
    ),
    "sfx": (
        "a single SFX word in CLASSIC COMIC-BURST lettering, sized at "
        "approximately 15% of the frame height, placed BEHIND/BESIDE the body "
        "region (not on top of it), yellow fill with thick black outline, "
        "slight tilt (-8 degrees), drop shadow"
    ),
}

# Genre-appropriate SFX word per region. The calibration used FLEX for
# bicep; the other regions get parallel FMG-genre SFX vocab. Avoid generic
# action SFX ("BAM", "POW") — those read as superhero combat.
_BEAT_TO_SFX_WORD = {
    "arms":  "FLEX",
    "chest": "POMF",   # FMG genre convention for bust beats
    "abs":   "FLEX",
    "rear":  "FLEX",
    "legs":  "FLEX",
}


def _resolve_levels(panel: dict) -> dict | None:
    """Pick the per-panel (lines_level, sfx_level, sfx_word) from the panel
    manifest and the calibrated defaults. Returns None when the rule doesn't
    apply to this panel.
    """
    beat = panel.get("transformation_beat")
    if beat not in _L33_BEATS:
        # Allow explicit opt-in via body_region_focus=true even without a
        # matching transformation_beat — supports panels that frame a body
        # region without naming the beat (e.g. a flex pose).
        if not panel.get("body_region_focus"):
            return None
        beat = panel.get("body_region_part") or "arms"
        if beat == "bicep":
            beat = "arms"
        elif beat == "glutes":
            beat = "rear"
        elif beat == "quads":
            beat = "legs"
        if beat not in _L33_BEATS:
            return None

    region = _BEAT_TO_REGION[beat]
    tier = panel.get("muscle_size_tier") or 1
    is_peak = isinstance(tier, int) and tier >= _TIER_ESCALATION_THRESHOLD

    # Per-panel overrides (auto / off / subtle / medium / heavy)
    lines_override = (panel.get("action_lines_level") or "auto").lower()
    sfx_override = (panel.get("sfx_level") or "auto").lower()

    if lines_override == "off":
        lines_desc = None
    elif lines_override == "auto":
        lines_desc = _LEVELS["lines_tier6_plus"] if is_peak else _LEVELS["lines_baseline"]
    elif lines_override == "subtle":
        lines_desc = (
            "SUBTLE radial action lines: 4-6 thin strokes emanating outward "
            "from the body-region focal point, low contrast (light grey), "
            "soft energy hint only"
        )
    elif lines_override == "medium":
        lines_desc = _LEVELS["lines_baseline"]
    elif lines_override == "heavy":
        lines_desc = _LEVELS["lines_tier6_plus"]
    else:
        lines_desc = _LEVELS["lines_tier6_plus"] if is_peak else _LEVELS["lines_baseline"]

    if sfx_override == "off":
        sfx_desc = None
    elif sfx_override in ("auto", "medium"):
        sfx_desc = _LEVELS["sfx"]
    elif sfx_override == "subtle":
        sfx_desc = (
            'a single small lowercase SFX word "*flex*" in italic, light grey, '
            "low alpha, placed in the bottom-right corner — integrated tonally"
        )
    elif sfx_override == "heavy":
        sfx_desc = (
            'a single SFX word in HEAVY comic-burst lettering, sized at '
            "approximately 30% of the frame height, dominating the panel, "
            "yellow fill with dark-red outline and heavy drop shadow"
        )
    else:
        sfx_desc = _LEVELS["sfx"]

    sfx_word = panel.get("sfx_word") or _BEAT_TO_SFX_WORD.get(beat, "FLEX")

    if lines_desc is None and sfx_desc is None:
        # Both axes opted off — nothing to contribute.
        return None

    return {
        "beat": beat,
        "region": region,
        "is_peak": is_peak,
        "tier": tier,
        "lines_desc": lines_desc,
        "sfx_desc": sfx_desc,
        "sfx_word": sfx_word,
    }


def _compose_line(resolved: dict) -> str:
    """Assemble the prompt fragment from the resolved level pack."""
    pieces = [
        f"L33 BODY-REGION SFX OVERLAY ({resolved['region']}, "
        f"tier {resolved['tier']}"
        f"{', peak-tier escalation' if resolved['is_peak'] else ''}): "
        "Composite a 2D comic-book overlay layer ON TOP of the photoreal "
        f"DAZ3D CGI render of the {resolved['region']}. The underlying body "
        "region, skin, costume, muscle definition, lighting, and ray-traced "
        "subsurface scattering must remain UNCHANGED — the overlay sits as "
        "a clearly named 2D vector layer that does NOT turn the body 2D."
    ]
    if resolved["lines_desc"]:
        pieces.append(f"Action lines: {resolved['lines_desc']}.")
    if resolved["sfx_desc"]:
        pieces.append(
            f'SFX text: the word "{resolved["sfx_word"]}" rendered as '
            f"{resolved['sfx_desc']}."
        )
    pieces.append(
        "The 2D comic styling applies ONLY to the action-line and SFX "
        "overlay graphics; everything else (body, costume, skin, hair, "
        "environment) remains photoreal CGI."
    )
    return " ".join(pieces)


class L33(Rule):
    id = "L33"
    title = "Body-region focus panels need calibrated action lines + SFX overlay"
    slot = "11_render_directive"
    severity = "soft"
    applicable_transformations = ("*",)
    vision_rubric = (
        "Look at this rendered comic panel. The shotlist declares a "
        "body-region focus beat (arm/bicep, chest, abs, rear/glute, or "
        "leg/quad) requiring an extreme close-up on the body region. Two "
        "checks: (1) Does the panel show a 2D comic-style overlay layer — "
        "radial action lines emanating from the body-region focal point and "
        "an SFX word in classic comic-burst lettering — clearly composited "
        "ON TOP of the photoreal bicep/chest/etc? (2) Does the underlying "
        "body region still read as photoreal CGI (ray-traced skin, "
        "physically-based muscle definition), NOT as 2D illustration? PASS "
        "if both the overlay is present at the calibrated level AND the "
        "body region stays photoreal. FAIL with which axis is wrong — "
        "missing overlay, overlay missing one axis, overlay 'painted into' "
        "the body, or body has drifted to 2D illustration."
    )

    def should_apply(self, panel: dict, ctx: dict) -> bool:
        return _resolve_levels(panel) is not None

    def compose_contribution(self, panel: dict, ctx: dict, slot: str) -> str | None:
        if slot != "11_render_directive":
            return None
        resolved = _resolve_levels(panel)
        if not resolved:
            return None
        return _compose_line(resolved)

    def verify_pre_render(self, panel: dict, ctx: dict) -> Verification:
        resolved = _resolve_levels(panel)
        if resolved is None:
            return Verification(
                status=STATUS_SKIPPED,
                reason=(
                    "no body-region focus (transformation_beat not in "
                    "{arms, chest, abs, rear, legs} and body_region_focus "
                    "not set)"
                ),
            )
        return Verification(
            status=STATUS_PASS,
            reason=(
                f"body-region beat={resolved['beat']!r} tier={resolved['tier']} "
                f"peak={resolved['is_peak']} — SFX overlay directive injected "
                f"(lines={'on' if resolved['lines_desc'] else 'off'}, "
                f"sfx={'on' if resolved['sfx_desc'] else 'off'})"
            ),
        )

    def retry_strategy(self, panel: dict, ctx: dict, failure: dict) -> dict:
        evidence = failure.get("evidence") or {}
        axis = evidence.get("missing_axis")
        if axis == "lines":
            strengthening = (
                "escalate the action-lines block — make 'CLEARLY VISIBLE 2D "
                "vector lines' explicit, name the focal point as 'the bicep "
                "peak' (or appropriate region), and demand 'NOT painted into "
                "the muscle — sits as a flat overlay layer'"
            )
        elif axis == "sfx":
            strengthening = (
                "escalate the SFX block — repeat the word in quotes, name "
                "the 'classic comic-burst lettering with thick black outline "
                "and yellow fill' explicitly, demand 'placed BEHIND the body, "
                "not on top of the muscle'"
            )
        elif axis == "body_2d_drift":
            strengthening = (
                "escalate the photoreal-scope negation — repeat 'the body, "
                "skin, costume, and muscle definition remain photoreal DAZ3D "
                "CGI; NOT a 2D illustration on the body; only the action "
                "lines and SFX word are 2D overlay graphics'"
            )
        else:
            strengthening = (
                "escalate ALL three pieces — the overlay-layer scope, the "
                "action-lines density, and the photoreal-body negation"
            )
        return {
            "kind": "auto_resubmit_with_stronger_contribution",
            "rule_id": self.id,
            "strengthening": strengthening,
        }
