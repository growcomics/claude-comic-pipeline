#!/usr/bin/env python3
"""
stop-autopilot.py — Claude Code Stop hook for comic pipeline autopilot.

Forces Claude to continue working when:
  1. A `.autopilot-active` sentinel file exists at the cwd (or an ancestor),
  2. No `.autopilot-halt-reason` file exists (which would signal a clean halt
     requested by autopilot itself on one of the approved conditions),
  3. `stop_hook_active` is False in the hook payload (loop guard).

Receives JSON via stdin:
  { "session_id": str, "stop_hook_active": bool, "transcript_path": str }

Output protocol: JSON-on-stdout + exit 0 (rather than exit-2-stderr) to dodge
the "Stop hook error" UI label per github.com/anthropics/claude-code issue
#34600.

Install: place at ~/.claude/hooks/stop-autopilot.py (chmod +x on macOS/Linux;
Windows just needs the file there), and register in ~/.claude/settings.json
under "hooks.Stop". See INSTALL.md.

Bug to dodge: github.com/anthropics/claude-code issue #10412 — Stop hooks
installed via the PLUGIN system silently fail with exit 2. Install at
~/.claude/hooks/ directly, NOT via plugins/marketplaces.

Cross-platform notes:
  - Uses pathlib + json + sys only; no third-party deps.
  - File reads explicitly UTF-8 (Windows default codepage is not UTF-8).
  - Walks Path.cwd() and parents looking for the sentinel — works identically
    on Windows, macOS, Linux.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def find_sentinel(start: Path) -> Path | None:
    """Walk up from start looking for .autopilot-active. Returns the directory
    containing the sentinel, or None if none found before the filesystem root.
    """
    try:
        cur = start.resolve()
    except Exception:
        return None
    while True:
        try:
            if (cur / ".autopilot-active").is_file():
                return cur
        except Exception:
            # Permission issues, e.g. on some Windows ancestor dirs. Try parent.
            pass
        parent = cur.parent
        if parent == cur:
            return None
        cur = parent


def main() -> int:
    # Read the hook payload from stdin.
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        # Malformed JSON → don't block the stop. Allow normal halt.
        return 0

    # Loop guard: if we're already in a forced continuation, allow stop.
    if payload.get("stop_hook_active", False):
        return 0

    # Look for the sentinel. Try cwd first, then the transcript_path's directory.
    sentinel_dir: Path | None = find_sentinel(Path.cwd())
    if sentinel_dir is None:
        tp = payload.get("transcript_path")
        if tp:
            try:
                sentinel_dir = find_sentinel(Path(tp).parent)
            except Exception:
                sentinel_dir = None

    # No autopilot active → allow normal stop.
    if sentinel_dir is None:
        return 0

    # If autopilot explicitly requested a halt (wrote .autopilot-halt-reason),
    # allow the stop. That file is autopilot's way of saying "I hit one of the
    # approved halt conditions, the user needs to look."
    if (sentinel_dir / ".autopilot-halt-reason").is_file():
        return 0

    # Otherwise we're mid-pipeline. Block the stop and feed Claude continuation
    # instructions.
    stage = ""
    stage_file = sentinel_dir / ".autopilot-stage"
    if stage_file.is_file():
        try:
            stage = stage_file.read_text(encoding="utf-8").strip().splitlines()[0].strip()
        except Exception:
            stage = ""

    reason = (
        f"Autopilot is active at {sentinel_dir} "
        f"(current stage: {stage or 'unknown'}). "
        "Do NOT stop and ask the user. "
        f"Read production-config.json at {sentinel_dir} for any decision "
        "policy you need. "
        "Continue the pipeline per the policies in the config and the rules "
        "in commands/build-comic.md autopilot section. "
        "If you have hit one of the approved halt conditions "
        "(content-policy refusal, MISSING_* ref guardrail, "
        "WARNING_DIALOGUE_CAMERA_CONFLICT, WARNING_MULTI_SPEAKER_CROWDING, "
        "Stage 1 audit HARD, environmental failure, script-level ambiguity), "
        f"write the reason to {sentinel_dir}/.autopilot-halt-reason "
        "and then you may stop. Otherwise continue working."
    )

    # Emit JSON on stdout, exit 0. This blocks the stop and feeds reason back
    # to Claude as continuation instructions, without the "error" UI label.
    print(json.dumps({"decision": "block", "reason": reason}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
