"""Base classes for the per-rule architecture.

`Rule` is the interface every rule module implements. `Verification` is the
return shape of pre/post-render checks. See docs/checks-and-balances-design.md
section 3.A for the design and section 3.C for the verification taxonomy.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


# Valid Verification.status values. The ledger schema and the future GUI grid
# both depend on this set being stable.
STATUS_PASS = "pass"
STATUS_FAIL = "fail"
STATUS_PENDING = "pending"
STATUS_SKIPPED = "skipped"
STATUS_BLOCKED = "blocked"
STATUS_NA = "n/a"
STATUS_REFUSED = "refused"

VALID_STATUSES = {
    STATUS_PASS, STATUS_FAIL, STATUS_PENDING,
    STATUS_SKIPPED, STATUS_BLOCKED, STATUS_NA, STATUS_REFUSED,
}


@dataclass
class Verification:
    """Return shape of verify_pre_render / verify_post_render.

    status — one of VALID_STATUSES. Anything else raises in __post_init__.
    reason — free-text human-readable explanation.
    evidence — optional structured payload (phase 5 vision verification will
               populate this with image-region snippets, subagent IDs, etc.).
    """
    status: str
    reason: str | None = None
    evidence: dict | None = None

    def __post_init__(self) -> None:
        if self.status not in VALID_STATUSES:
            raise ValueError(
                f"Verification.status must be one of {sorted(VALID_STATUSES)}, "
                f"got {self.status!r}"
            )

    def to_dict(self) -> dict:
        out: dict = {"status": self.status, "reason": self.reason}
        if self.evidence is not None:
            out["evidence"] = self.evidence
        return out


class Rule:
    """Base class every per-rule module subclasses.

    Class attributes (override in subclass):
      id                          — "L21", "L11", etc.
      title                       — one-line human-readable.
      slot                        — composition slot name (or tuple of names
                                    for rules that contribute to >1 slot).
      severity                    — "hard" or "soft".
      applicable_transformations  — tuple of transformation types this rule
                                    fires on. ("*",) = all. ("fmg",) =
                                    FMG-only.
      vision_rubric               — None when the rule has no post-render
                                    visual check, OR a short rubric string
                                    that a vision subagent uses to verify
                                    the rendered panel. The verify-panel-
                                    vision CLI dispatches per-rule subagents
                                    with this rubric + the accepted variant
                                    image + the canonical refs.

    Methods (override in subclass):
      should_apply           — does this rule fire on this panel?
      compose_contribution   — what does it add to the prompt at the given
                               slot? Return None when not applicable or no
                               contribution.
      verify_pre_render      — deterministic shotlist-time check.
      verify_post_render     — deterministic-or-vision post-image check.
      retry_strategy         — what to do when verification fails.

    The default implementations are conservative: should_apply returns True,
    compose_contribution returns None, verify_pre_render returns
    pass-if-applies, verify_post_render returns pending,
    retry_strategy returns accept_and_log. Subclasses override what they need.
    """

    id: str = ""
    title: str = ""
    slot: str | tuple[str, ...] = ""
    severity: str = "hard"
    applicable_transformations: tuple[str, ...] = ("*",)
    vision_rubric: str | None = None

    # section_label drives the human-readable section header in the formatted
    # prompt output (see compose_prompt in next_panel.py). Set this to a short
    # bracketable phrase like "CHARACTER — L17 canonical anchor". For multi-
    # slot rules (currently only L11), set this to a dict keyed by slot name.
    # If left blank the helper falls back to the rule id.
    section_label: str | dict[str, str] = ""

    # ---- composition ------------------------------------------------------

    def should_apply(self, panel: dict, ctx: dict) -> bool:
        return True

    def compose_contribution(self, panel: dict, ctx: dict, slot: str) -> str | None:
        """Return the prompt fragment this rule contributes at the given slot,
        or None if it doesn't contribute there.
        """
        return None

    def section_label_for(self, slot: str) -> str:
        """Resolve the human-readable section label for the given slot.

        Single-slot rules just return their string `section_label`. Multi-
        slot rules (L11) override `section_label` to a dict and this method
        picks the entry for the active slot.
        """
        label = self.section_label
        if isinstance(label, dict):
            return label.get(slot) or self.id
        return label or self.id

    # ---- verification -----------------------------------------------------

    def verify_pre_render(self, panel: dict, ctx: dict) -> Verification:
        if self.should_apply(panel, ctx):
            return Verification(STATUS_PASS, reason=f"{self.id} applied")
        return Verification(STATUS_SKIPPED, reason=f"{self.id} did not apply")

    def verify_post_render(self, panel: dict, image_path: Path | None,
                           ctx: dict) -> Verification:
        """Default: pending. Subclasses that need vision verification override.
        Phase 5 will wire fresh-subagent invocation here per the design doc.
        """
        return Verification(STATUS_PENDING, reason=None)

    # ---- retry ------------------------------------------------------------

    def retry_strategy(self, panel: dict, ctx: dict, failure: dict) -> dict:
        """Default: accept_and_log. Subclasses override.

        See docs/checks-and-balances-design.md § 3.D for retry kinds:
          auto_resubmit_with_stronger_contribution
          auto_resubmit_with_corrected_refs
          auto_resubmit_with_different_face_card
          shotlist_edit_required
          ref_generation_required
          accept_and_log
        """
        return {"kind": "accept_and_log",
                "reason": f"{self.id} has no retry strategy defined"}

    # ---- helpers ----------------------------------------------------------

    def applies_to_transformation(self, transformation_type: str) -> bool:
        return ("*" in self.applicable_transformations
                or transformation_type in self.applicable_transformations)

    def slots(self) -> tuple[str, ...]:
        """Normalize slot to a tuple."""
        if isinstance(self.slot, str):
            return (self.slot,) if self.slot else ()
        return tuple(self.slot)

    def __repr__(self) -> str:
        return f"<Rule {self.id} ({self.title!r}) slot={self.slot!r}>"
