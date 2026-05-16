"""L10 — References are the truth, prompts are deltas.

The most architecturally important rule in the pipeline. Refs carry identity
/ costume design / location architecture / lighting baseline; the prompt
carries camera / pose / gesture / expression / action / momentary state. The
RENDER DIRECTIVE sentence is the load-bearing piece — it tells the model
that refs override prompt text on visual identity and prompt overrides refs
on pose and action.

See:
  - skills/comic-production/references/lessons-learned.md § L10
  - skills/comic-production/references/the-rules-explained.md § L10
"""

from __future__ import annotations

from ._base import Rule, Verification, STATUS_PASS


L10_RENDER_DIRECTIVE = (
    "RENDER DIRECTIVE: render the attached references exactly as shown. "
    "Do not reinterpret character appearance, costume design, or location "
    "architecture from the prompt text — those are FIXED by the "
    "references. The prompt's job is the opposite: it specifies what "
    "is new in this panel — camera, pose, gesture, facial expression, "
    "action, momentary lighting state, momentary costume state change. "
    "Refs carry identity and constants; prompt carries pose and "
    "deltas. References override prompt text on visual identity; "
    "prompt overrides references on pose and action."
)


class L10(Rule):
    id = "L10"
    title = "References are the truth, prompts are deltas"
    slot = "11_render_directive"
    severity = "hard"
    applicable_transformations = ("*",)
    vision_rubric = (
        "Look at this rendered comic panel and compare it to the attached "
        "reference images. Does the rendered character match the face card "
        "(same face, same canonical features)? Does the costume match the "
        "body baseline (same garment, same colors, same accessories)? If a "
        "location ref is attached, does the rendered background match it "
        "(same architecture, same lighting baseline)? PASS if visual "
        "identity matches the refs. FAIL with a specific description of the "
        "drift (e.g. 'face is different from face card', 'costume color "
        "shifted from red to maroon', 'background invented a different room')."
    )

    def should_apply(self, panel: dict, ctx: dict) -> bool:
        return True  # render directive always emitted

    def compose_contribution(self, panel: dict, ctx: dict, slot: str) -> str | None:
        if slot != "11_render_directive":
            return None
        return L10_RENDER_DIRECTIVE

    def verify_pre_render(self, panel: dict, ctx: dict) -> Verification:
        return Verification(
            status=STATUS_PASS,
            reason="render directive always emitted (slot 11_render_directive)",
        )

    def retry_strategy(self, panel: dict, ctx: dict, failure: dict) -> dict:
        return {
            "kind": "auto_resubmit_with_stronger_contribution",
            "rule_id": self.id,
            "strengthening": (
                "strengthen the render directive with explicit identity-vs-"
                "pose phrasing: 'refs are TRUTH for identity; prompt is TRUTH "
                "for camera and pose. NEVER reinterpret a ref's clothing, "
                "face, or architecture from the prompt text — those values "
                "are FIXED by the ref images.'"
            ),
        }
