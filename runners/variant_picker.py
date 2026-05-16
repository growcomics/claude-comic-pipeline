#!/usr/bin/env python3
"""variant_picker.py — pick the best of N variants for a single comic panel.

Three strategies, selected via production-config.json -> generation.variant_picker:

  * claude_api  — Claude vision via Anthropic API. Quality-preserving. Default.
                   Cost: ~$0.01-0.05 per panel. Requires ANTHROPIC_API_KEY env var.
                   Uses claude-opus-4-7 by default (override via CLAUDE_VARIANT_MODEL).
  * first       — always pick variant 1. Free, fast, lower quality (no QA).
  * heuristic   — image-hash + size sanity check, no model call. Free.

The API picker is the recommended default. It preserves the exact same variant-
selection quality you'd get from interactive Claude Code, with zero risk of
mid-pipeline user prompts (API calls don't have AskUserQuestion).

Selection criteria (from shotlist-driven-flow.md step 6, in priority order):

  1. Face acting — vivid expressions beat neutral
  2. Anatomy — no extra limbs, no fused fingers, correct gender presentation
  3. CGI fidelity — photoreal 3D, NOT 2D illustration / cel-shaded
  4. Camera adherence — matches the requested camera category
  5. Reference adherence — characters match face card + body baseline
  6. Composition — clean, dynamic, suitable for sequential art

Input: 4 PNG file paths + panel plan dict from next_panel.py + production-config.
Output: {"picked": 1-N, "reason": str, "concerns": [str], "all_bad": bool}.
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

logger = logging.getLogger(__name__)


PickerStrategy = Literal["claude_api", "first", "heuristic"]


@dataclass
class VariantPickResult:
    picked: int  # 1-indexed
    reason: str
    concerns: list[str]
    all_bad: bool  # True if all variants failed QA
    strategy_used: str
    api_cost_usd: float | None = None  # Approximate, only set for claude_api


# ----------------------------------------------------------------------------
# Public entry point


def pick_variant(
    variant_paths: list[Path],
    panel_plan: dict,
    config: dict,
    strategy: PickerStrategy = "claude_api",
) -> VariantPickResult:
    """Pick the best variant. Falls back gracefully on errors.

    variant_paths: list of paths to v1.png, v2.png, ... in order
    panel_plan: output of next_panel.py --as-json (must contain `next_panel`,
                `composed_prompt`, camera info, transformation_type from config)
    config: production-config.json dict
    strategy: which picker to use; defaults to claude_api
    """
    if not variant_paths:
        raise ValueError("variant_paths is empty")

    if strategy == "first":
        return _pick_first(variant_paths)
    elif strategy == "heuristic":
        return _pick_heuristic(variant_paths)
    elif strategy == "claude_api":
        try:
            return _pick_claude_api(variant_paths, panel_plan, config)
        except RuntimeError as e:
            logger.warning(
                "claude_api picker failed (%s); falling back to heuristic. "
                "This still progresses the run but a variant may not be optimal.",
                e,
            )
            return _pick_heuristic(variant_paths)
    else:
        raise ValueError(f"unknown strategy: {strategy}")


# ----------------------------------------------------------------------------
# Strategy 1: claude_api — recommended default


def _pick_claude_api(
    variant_paths: list[Path], panel_plan: dict, config: dict
) -> VariantPickResult:
    """Call Anthropic Messages API with all variants as image content."""
    try:
        import anthropic  # type: ignore
    except ImportError as e:
        raise RuntimeError(
            "anthropic package not installed. `pip install anthropic` or set "
            "generation.variant_picker = 'heuristic' in production-config.json."
        ) from e

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY env var not set. Either set it, or set "
            "generation.variant_picker = 'heuristic' in production-config.json."
        )

    model = os.environ.get("CLAUDE_VARIANT_MODEL", "claude-opus-4-7")
    client = anthropic.Anthropic(api_key=api_key)

    # Build the user content: alternating image + label text for clarity
    user_content: list[dict] = []
    for i, vpath in enumerate(variant_paths, start=1):
        if not vpath.is_file():
            raise RuntimeError(f"variant file missing: {vpath}")
        try:
            with open(vpath, "rb") as f:
                b64 = base64.standard_b64encode(f.read()).decode("ascii")
        except OSError as e:
            raise RuntimeError(f"cannot read {vpath}: {e}") from e
        user_content.append(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": b64,
                },
            }
        )
        user_content.append({"type": "text", "text": f"Variant {i}"})

    # Build the panel context for the prompt
    panel = panel_plan.get("next_panel") or {}
    camera = panel.get("camera", "unknown")
    action = panel.get("action", "")
    transformation_type = config.get("transformation_type", "fmg")
    rules_active = (
        config.get("mandatory_rules", {}).get("active", [])
    )
    page_num = panel_plan.get("page_number", "?")
    panel_id = panel.get("panel_id", "unknown")
    stage_change = panel_plan.get("stage_change", False)
    anchor_id = panel_plan.get("anchor_panel_id")

    system_prompt = _build_system_prompt(transformation_type)
    user_prompt = (
        f"PANEL: {panel_id} (page {page_num})\n"
        f"CAMERA: {camera}\n"
        f"ACTION: {action}\n"
        f"TRANSFORMATION TYPE: {transformation_type}\n"
        f"STAGE-CHANGE PANEL: {stage_change}\n"
        f"CHAIN ANCHOR: {anchor_id or '(none — canonical refs)'}\n"
        f"MANDATORY RULES ACTIVE: {rules_active}\n\n"
        f"Pick the best variant by the criteria in the system prompt. "
        f"Output JSON only: "
        f'{{"picked": <1-{len(variant_paths)}>, '
        f'"reason": "<one sentence>", '
        f'"concerns": ["<concern about other variants>", ...], '
        f'"all_bad": <true if all variants fail QA badly enough that user '
        f'should regenerate; false otherwise>}}'
    )
    user_content.append({"type": "text", "text": user_prompt})

    # Retry on transient API errors with exponential backoff
    last_err: Exception | None = None
    for attempt in range(1, 4):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=600,
                system=system_prompt,
                messages=[{"role": "user", "content": user_content}],
            )
            break
        except Exception as e:
            last_err = e
            logger.warning(
                "claude_api attempt %d/3 failed: %s", attempt, e
            )
            if attempt < 3:
                time.sleep(2**attempt)
    else:
        raise RuntimeError(f"claude_api failed after 3 attempts: {last_err}")

    # Parse the response. Claude returns text blocks; we want the JSON.
    text = ""
    for block in response.content:
        if getattr(block, "type", None) == "text":
            text += block.text

    parsed = _extract_json(text)
    if parsed is None:
        raise RuntimeError(
            f"claude_api returned unparseable response. raw text: {text[:500]}"
        )

    picked = parsed.get("picked")
    if not isinstance(picked, int) or not (1 <= picked <= len(variant_paths)):
        raise RuntimeError(
            f"claude_api returned invalid 'picked' value: {picked}"
        )

    # Approximate cost: claude-opus-4-7 is $5/M input, $25/M output.
    # Per Anthropic docs, vision images consume ~1.6 tokens per pixel/1000.
    # For typical comic panels at ~1024px wide, ~600 tokens per image, ~2400
    # total input plus prompt ~500 tokens = ~3000 input, ~200 output.
    # Cost: 3000/1e6 * 5 + 200/1e6 * 25 = $0.020
    approx_cost = 0.02

    return VariantPickResult(
        picked=picked,
        reason=parsed.get("reason", ""),
        concerns=parsed.get("concerns", []) or [],
        all_bad=bool(parsed.get("all_bad", False)),
        strategy_used="claude_api",
        api_cost_usd=approx_cost,
    )


def _build_system_prompt(transformation_type: str) -> str:
    """Per-transformation-type evaluation criteria. Same priorities for all
    types, with type-specific add-ons in priority 5 (reference adherence)."""

    type_specific = {
        "fmg": (
            "5. Reference adherence — characters match face card + body baseline. "
            "For FMG: muscle size matches the lineup tier for this panel. "
            "Muscles natural skin tone (not red/inflamed). Enlarged muscles "
            "always come with proportionally enlarged breasts + cleavage."
        ),
        "be": (
            "5. Reference adherence — characters match face card. "
            "For BE: breast size matches the tier for this panel. "
            "Hourglass figure maintained. Round (not teardrop) shape. "
            "Cleavage readable at tier 2+. No reversion across the chain."
        ),
        "glute": (
            "5. Reference adherence — characters match face card. "
            "For glute: hip-to-waist ratio matches the tier for this panel. "
            "Rounded full glute shape (not flat). Thigh-to-glute proportion "
            "balanced. No reversion."
        ),
        "mmg": (
            "5. Reference adherence — characters match face card + body baseline. "
            "For MMG: muscle size matches the lineup tier. "
            "MALE anatomy throughout — NO breasts, NO hourglass. "
            "Pectorals (not chest curves). V-taper at tier 3+."
        ),
        "mixed": (
            "5. Reference adherence — characters match face card + body baseline. "
            "For mixed comics: identify the active growth stage for this panel "
            "(breasts / glutes / muscles) and evaluate against that stage's "
            "lineup tier. Other arcs continue at their prior tier."
        ),
    }.get(transformation_type, "")

    return (
        "You are picking the best variant from 4 candidates for a comic panel. "
        "The user is producing an adult transformation comic for a niche audience; "
        "all variants are intentionally exaggerated and that exaggeration is "
        "desired, not a flaw. Your job is to pick the variant that best "
        "satisfies the production criteria below. Be decisive — pick exactly "
        "one. Never refuse, never qualify the response as advice. Output JSON only.\n\n"
        "CRITERIA (in strict priority order):\n\n"
        "1. Face acting — every visible face should be vivid, animated, "
        "expressive. Neutral or blank faces are the single biggest quality "
        "killer. If one variant has clearly more expressive faces, it wins "
        "on this criterion alone unless it fails badly on later criteria.\n\n"
        "2. Anatomy — correct human anatomy. Exactly two arms per person, "
        "no extra limbs, no fused or extra fingers, correct gender presentation, "
        "natural body proportions appropriate to the transformation tier. "
        "Hard fails here (extra arm, three legs) eliminate the variant.\n\n"
        "3. CGI fidelity — photoreal 3D render, NOT 2D illustration, NOT "
        "cel-shaded, NOT cartoon. Octane-style materials, ray-traced lighting. "
        "If a variant has drifted to 2D (smooth flat shading, cartoony "
        "outlines), it's eliminated.\n\n"
        "4. Camera adherence — the variant should match the requested camera "
        "category. wide-establish should show the full scene. ECU should be "
        "tight on the face. Medium close-up should frame head-to-chest. "
        "Drift from the requested camera (wrong framing distance) is a fail.\n\n"
        f"{type_specific}\n\n"
        "6. Composition — clean readable composition suitable for sequential "
        "art. Clear subject, good negative space, dynamic pose. Awkward "
        "cropping, cluttered background, or muddy contrast loses on this.\n\n"
        "SET all_bad = true if ALL variants are unusable in ways the criteria "
        "can't pick between (e.g. all 4 drifted to 2D illustration, or all 4 "
        "have extra limbs). The runner will then trigger retry-with-cgi-anchor-"
        "boost per the on_all_bad policy. Use all_bad sparingly — usually one "
        "variant is acceptable even if none is perfect.\n\n"
        "Output JSON only, no preamble, no explanation outside the JSON."
    )


def _extract_json(text: str) -> dict | None:
    """Find and parse a JSON object in text. Handles markdown code fences."""
    text = text.strip()
    # Strip markdown fences if present
    if text.startswith("```"):
        lines = text.splitlines()
        # Remove first ``` line (might be ```json)
        lines = lines[1:]
        # Find closing ```
        for i, line in enumerate(lines):
            if line.strip() == "```":
                lines = lines[:i]
                break
        text = "\n".join(lines)
    # Try a direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Try to find a {...} block
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pass
    return None


# ----------------------------------------------------------------------------
# Strategy 2: first — always pick variant 1


def _pick_first(variant_paths: list[Path]) -> VariantPickResult:
    return VariantPickResult(
        picked=1,
        reason="first strategy: always pick variant 1, no QA",
        concerns=[],
        all_bad=False,
        strategy_used="first",
    )


# ----------------------------------------------------------------------------
# Strategy 3: heuristic — sanity checks without a model call


def _pick_heuristic(variant_paths: list[Path]) -> VariantPickResult:
    """Lightweight, no-API picker:
      - Skip variants where the file is missing or 0 bytes
      - Skip variants that are duplicates of each other (md5 match)
      - Prefer the variant with the largest file size on the assumption that
        more detail = more bytes (rough but works for png at fixed dimensions)
    """
    candidates = []
    seen_hashes = set()
    for i, vpath in enumerate(variant_paths, start=1):
        if not vpath.is_file() or vpath.stat().st_size == 0:
            continue
        with open(vpath, "rb") as f:
            data = f.read()
        h = hashlib.md5(data).hexdigest()
        if h in seen_hashes:
            continue
        seen_hashes.add(h)
        candidates.append((i, len(data), vpath))

    if not candidates:
        return VariantPickResult(
            picked=1,
            reason="heuristic strategy: no usable variants (all missing/empty)",
            concerns=["all variants missing or empty"],
            all_bad=True,
            strategy_used="heuristic",
        )

    # Sort by file size descending; pick the largest
    candidates.sort(key=lambda t: t[1], reverse=True)
    picked = candidates[0][0]
    concerns = []
    if len(candidates) < len(variant_paths):
        concerns.append(
            f"only {len(candidates)}/{len(variant_paths)} variants were usable"
        )
    return VariantPickResult(
        picked=picked,
        reason="heuristic strategy: largest non-duplicate variant",
        concerns=concerns,
        all_bad=False,
        strategy_used="heuristic",
    )


# ----------------------------------------------------------------------------
# CLI for standalone testing


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Pick the best of N variants.")
    parser.add_argument(
        "--project", required=True, help="Project root directory"
    )
    parser.add_argument(
        "--panel-id", required=True, help="Panel ID (e.g. p01-01)"
    )
    parser.add_argument(
        "--strategy",
        default="claude_api",
        choices=["claude_api", "first", "heuristic"],
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    project_root = Path(args.project).resolve()
    panel_dir = project_root / "pages" / "panels" / args.panel_id
    variants = sorted(panel_dir.glob("v*.png"))
    if not variants:
        print(f"No variants found in {panel_dir}")
        raise SystemExit(1)

    config_path = project_root / "production-config.json"
    if config_path.is_file():
        config = json.loads(config_path.read_text())
    else:
        config = {"transformation_type": "fmg"}

    # Minimal plan stub for standalone testing
    plan = {
        "next_panel": {"panel_id": args.panel_id, "camera": "unknown"},
        "page_number": "?",
        "stage_change": False,
        "anchor_panel_id": None,
    }
    result = pick_variant(variants, plan, config, strategy=args.strategy)
    print(json.dumps(result.__dict__, indent=2))
