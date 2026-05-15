#!/usr/bin/env python3
"""
pre-tool-autopilot.py — Claude Code PreToolUse hook for comic pipeline autopilot.

Blocks `AskUserQuestion` while autopilot is active, so Claude cannot pause the
pipeline mid-run to ask a strategic question. All decisions during autopilot
are supposed to come from `production-config.json` (or from one of the
approved hard-halt conditions, which write `.autopilot-halt-reason` and stop
cleanly).

Blocks when:
  1. A `.autopilot-active` sentinel file exists at cwd or any ancestor, AND
  2. No `.autopilot-halt-reason` file exists in the same dir (the legitimate
     "I'm winding down on an approved hard halt — one clarifying question is
     allowed" exception, per build-comic.md).

Receives JSON via stdin (PreToolUse payload):
  {
    "session_id": str,
    "transcript_path": str,
    "tool_name": str,
    "tool_input": dict,
    ...
  }

Output: JSON on stdout with permissionDecision=deny when blocking. Exit 0.

Companion to stop-autopilot.py. Install at ~/.claude/hooks/ and register in
~/.claude/settings.json under "hooks.PreToolUse" with matcher
"AskUserQuestion".
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def find_sentinel(start: Path) -> Path | None:
    try:
        cur = start.resolve()
    except Exception:
        return None
    while True:
        try:
            if (cur / ".autopilot-active").is_file():
                return cur
        except Exception:
            pass
        parent = cur.parent
        if parent == cur:
            return None
        cur = parent


def main() -> int:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0

    tool_name = payload.get("tool_name", "")
    if tool_name != "AskUserQuestion":
        return 0

    sentinel_dir = find_sentinel(Path.cwd())
    if sentinel_dir is None:
        tp = payload.get("transcript_path")
        if tp:
            try:
                sentinel_dir = find_sentinel(Path(tp).parent)
            except Exception:
                sentinel_dir = None
    if sentinel_dir is None:
        return 0

    if (sentinel_dir / ".autopilot-halt-reason").is_file():
        return 0

    reason = (
        f"Autopilot is active at {sentinel_dir}. AskUserQuestion is forbidden "
        "mid-pipeline. Every decision is either (a) answered in "
        f"{sentinel_dir}/production-config.json (consult policies.*, "
        "generation.*, mandatory_rules.*) or (b) one of the approved hard-halt "
        "conditions (content-policy refusal, MISSING_* ref guardrail, "
        "WARNING_DIALOGUE_CAMERA_CONFLICT, WARNING_MULTI_SPEAKER_CROWDING, "
        "Stage 1 audit HARD, environmental failure, script ambiguity). If a "
        "hard halt fires, write the reason to "
        f"{sentinel_dir}/.autopilot-halt-reason and then ONE clarifying "
        "AskUserQuestion is permitted (this hook will allow it once that file "
        "exists). Otherwise: read the config, decide, continue."
    )

    decision = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }
    print(json.dumps(decision))
    return 0


if __name__ == "__main__":
    sys.exit(main())
