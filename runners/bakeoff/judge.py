#!/usr/bin/env python3
"""Two-stage judge for the bakeoff lane.

Stage A (gross defects) runs server-side via bridge do=qascan — the live ck_ai_qa
scan in studio/inc/defects.php, emitting canonical registry defect types. This
module maps its output (see registry.resolve) and hosts Stage B: a preference
ranker over the survivors, calibrated against the owner's real picks
(research/picks-profile-eva.md).

Stage B runs as a FRESH `claude -p` subprocess per beat (headless CLI, Sonnet by
default — cheap-model judging per house doctrine). The judge is never the model
that generated the variants, and rubric files are handed to it BY PATH to read
verbatim — never paraphrased into the prompt.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

# Canonical rubric files — passed by path, read verbatim by the judge.
RUBRIC_PATHS = [
    REPO / "research/comic-corpus/analysis-rubric.md",
    REPO / "skills/comic-production/references/cinematic-framing.md",
    REPO / "skills/comic-production/references/qa-checklist.md",
]

JUDGE_MODEL = "sonnet"

# Selection weights distilled from the owner's REAL picks (picks-profile-eva.md,
# 8 favorites vs 114 siblings, 8 blind graders). Order matters; expression is
# deliberately last — 0/8 favorites won on expression (it's a tiebreaker only).
WEIGHTS = """Judge in this strict priority order (earlier criteria dominate later ones):
1. CAMERA & COMPOSITION — adherence to the requested camera, plus crop aggression,
   diagonals, and FG/BG depth. (Strongest predictor of the owner's pick: 6/2/0 win/tie/loss.)
2. GROWTH / PAYOFF DENSITY — how much of the frame the muscle/transformation payoff
   occupies; on money-shot beats flexed mass should be >=40% of frame.
3. MUSCLE RENDERING — vascularity, striation, believable volume under light.
4. DEFECT ABSENCE — remaining minor defects (Stage A already removed blockers).
5. WARDROBE / IDENTITY FIDELITY — match to the attached references.
6. LIGHTING — golden-hour raking key with long shadows beats flat midday diffuse;
   dusk chiaroscuro wins climax beats.
7. EXPRESSION — TIEBREAKER ONLY. Do not let a prettier or more intense face outrank
   a better-composed, denser variant (0/8 owner picks won on expression)."""


class JudgeError(RuntimeError):
    pass


def rank_variants(beat_prompt: str, variants: list[dict], *, beat_kind: str = "panel",
                  model: str = JUDGE_MODEL, timeout: int = 420) -> dict:
    """variants: [{slot, path, stageA_summary}] with >=2 entries. Returns
    {winner: slot, ranking: [{slot, score, reasons}], raw: str}."""
    if len(variants) < 2:
        raise ValueError("stage B needs >=2 survivors")
    rubrics = "\n".join(f"- {p}" for p in RUBRIC_PATHS if p.is_file())
    vlist = "\n".join(
        f'- slot "{v["slot"]}": image file {v["path"]}'
        + (f' — stage-A notes: {v["stageA_summary"]}' if v.get("stageA_summary") else "")
        for v in variants
    )
    slots = [v["slot"] for v in variants]
    prompt = f"""You are the selection judge for ONE comic-panel beat (beat kind: {beat_kind}).
Several generated variants of the same beat survived a defect gate; pick the one the owner
would keep.

First, Read these rubric files IN FULL (verbatim context, do not skip):
{rubrics}

Then Read (view) every variant image:
{vlist}

The beat's generation prompt was:
---
{beat_prompt}
---

{WEIGHTS}

Reply with ONLY a JSON object, no prose before or after:
{{"winner": "<slot>", "ranking": [{{"slot": "<slot>", "score": <0-100>, "reasons": "<one sentence>"}}, ...]}}
Include every slot ({", ".join(slots)}) exactly once in "ranking", best first."""

    cmd = ["claude", "-p", prompt, "--model", model, "--allowedTools", "Read",
           "--output-format", "json"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        raise JudgeError(f"claude -p failed to run: {e}") from e
    if proc.returncode != 0:
        raise JudgeError(f"claude -p exit {proc.returncode}: {proc.stderr[:300]}")
    text = proc.stdout
    try:
        wrapper = json.loads(text)
        text = wrapper.get("result", text) if isinstance(wrapper, dict) else text
    except json.JSONDecodeError:
        pass
    verdict = _extract_json(text)
    if not verdict or "winner" not in verdict:
        raise JudgeError(f"judge reply unparseable: {text[:300]!r}")
    if verdict["winner"] not in slots:
        raise JudgeError(f"judge picked unknown slot {verdict['winner']!r}")
    verdict["raw"] = text[:2000]
    return verdict


def _extract_json(text: str):
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
