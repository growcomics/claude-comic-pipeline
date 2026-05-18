"""L23 — When env ref is dropped, inject a dense verbal env anchor.

Stage-change full-body panels need lineup ref attached (L11), which combined
with face card + state anchor hits the 3-ref ceiling and forces the env ref
to be dropped. Without explicit verbal env anchoring, the background
collapses to a grey/blurry void. Caught on chun-li-ascension v2 p06.

Pulls the dense anchor from shotlist.locations[].description so the
shotlist author can encode rich location detail once and have it surface
automatically when needed.

See:
  - skills/comic-production/references/lessons-learned.md § L23
  - skills/comic-production/references/the-rules-explained.md § L23
"""

from __future__ import annotations

from ._base import Rule, Verification, STATUS_PASS, STATUS_SKIPPED, STATUS_FAIL


class L23(Rule):
    id = "L23"
    title = "When env ref is dropped, add a dense verbal env anchor"
    slot = "9_environment"
    section_label = "ENVIRONMENT — L23 verbal anchor"
    severity = "soft"
    applicable_transformations = ("*",)
    vision_rubric = (
        "Look at this rendered comic panel. The shotlist declares a specific "
        "location (e.g. 'training dojo with wooden floorboards, paper "
        "sliding doors, calligraphy scrolls'). Does the rendered background "
        "actually depict the named location with the named elements? Or did "
        "the background collapse to a grey/blurry void, or render a generic "
        "interior unrelated to the named location? PASS if the named "
        "location elements are visible in the background. FAIL with a "
        "description if the background is a void or invented a different "
        "setting."
    )

    def should_apply(self, panel: dict, ctx: dict) -> bool:
        env_dropped = ctx.get("env_dropped", False)
        location_slug = ctx.get("location_slug") or ""
        env_ref = ctx.get("env_ref")
        return bool(env_dropped) and bool(location_slug) and env_ref is None

    def compose_contribution(self, panel: dict, ctx: dict, slot: str) -> str | None:
        if slot != "9_environment":
            return None
        if not self.should_apply(panel, ctx):
            return None
        shotlist = ctx.get("shotlist") or {}
        location_slug = ctx.get("location_slug") or ""
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

    def verify_pre_render(self, panel: dict, ctx: dict) -> Verification:
        env_ref = ctx.get("env_ref")
        env_dropped = ctx.get("env_dropped", False)
        location_slug = ctx.get("location_slug") or ""
        if env_ref:
            return Verification(
                status=STATUS_SKIPPED,
                reason=f"env ref attached (location={location_slug!r}) — dense verbal anchor not needed",
            )
        if not env_dropped or not location_slug:
            return Verification(
                status=STATUS_SKIPPED,
                reason=f"no env_ref to drop (location={location_slug!r}, env_dropped={env_dropped})",
            )
        # env_dropped + location_slug set + env_ref None — should fire. Verify
        # the location actually has a description on disk.
        shotlist = ctx.get("shotlist") or {}
        for loc in shotlist.get("locations", []) or []:
            if loc.get("id") == location_slug:
                if (loc.get("description") or "").strip():
                    return Verification(
                        status=STATUS_PASS,
                        reason=(f"env ref dropped for 3-ref ceiling, "
                                f"location={location_slug!r} — dense verbal "
                                "anchor injected"),
                    )
                break
        return Verification(
            status=STATUS_FAIL,
            reason=(f"env ref dropped but location {location_slug!r} has no "
                    "description in shotlist.locations[]"),
        )

    def retry_strategy(self, panel: dict, ctx: dict, failure: dict) -> dict:
        # If the background still collapses to a void on post-render vision,
        # the location description in the shotlist is too thin. Surface that
        # as a shotlist edit rather than a prompt strengthening — the rule's
        # contribution is already maximally specific.
        return {
            "kind": "shotlist_edit_required",
            "rule_id": self.id,
            "suggestion": (
                "expand shotlist.locations[<id>].description with 5+ named "
                "physical elements (wall material + color, floor material, "
                "lighting source + direction, foreground props, background "
                "depth elements). The dense verbal anchor is only as good as "
                "the description it pulls from."
            ),
        }
