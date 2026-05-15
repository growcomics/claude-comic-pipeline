# Stop Hook Install — `stop-autopilot.py`

Forces Claude Code to continue working when the comic pipeline autopilot is mid-run. Without this hook, autopilot still works most of the time — the hook is a safety net for the case where Claude tries to halt and ask a question that the skill rewrites missed.

## What it does

- Fires every time Claude finishes a response (Stop event).
- Checks for `.autopilot-active` sentinel file (autopilot mode wrote it at project root).
- If present and no `.autopilot-halt-reason` file exists → blocks the stop, feeds Claude continuation instructions.
- If no sentinel found, or autopilot wrote a halt reason → allows the normal stop.
- Loop-guard via `stop_hook_active` field per Claude Code docs.

## Requirements

- Python 3.8+ (script uses `from __future__ import annotations` and pathlib). macOS ships 3.9+; the Mac Mini definitely has it.
- No third-party packages.

## Install — user-level (every project gets it)

```bash
mkdir -p ~/.claude/hooks
cp stop-autopilot.py ~/.claude/hooks/stop-autopilot.py
chmod +x ~/.claude/hooks/stop-autopilot.py
```

Then add the Stop entry to `~/.claude/settings.json`. If you already have hooks configured, merge — don't overwrite.

Minimum settings file content if you have nothing else there:

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "$HOME/.claude/hooks/stop-autopilot.py",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

If you already have `Stop` hooks, append the new one to the existing array's `hooks` list, OR add another object to the `Stop` array if you want different matchers:

```json
{
  "hooks": {
    "Stop": [
      { "matcher": "*", "hooks": [ /* your existing hooks */, { "type": "command", "command": "$HOME/.claude/hooks/stop-autopilot.py", "timeout": 5 } ] }
    ]
  }
}
```

## Install — project-level (only this comic project)

If you don't want the hook firing in non-comic projects:

```bash
mkdir -p <project_root>/.claude/hooks
cp stop-autopilot.py <project_root>/.claude/hooks/stop-autopilot.py
chmod +x <project_root>/.claude/hooks/stop-autopilot.py
```

Then add to `<project_root>/.claude/settings.json` (creating the file if needed):

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/stop-autopilot.py",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

## Verify install

In a Claude Code session, run:

```
/hooks
```

You should see your Stop hook listed under the `Stop` event. Claude Code's `/hooks` slash command shows what's currently registered.

## Test

Quick test that the hook is wired correctly:

```bash
# 1. Make a fake project with a sentinel
mkdir -p /tmp/autopilot-test
cd /tmp/autopilot-test
touch .autopilot-active
echo "generation" > .autopilot-stage

# 2. Open Claude Code in that directory
cd /tmp/autopilot-test
claude

# 3. Inside the session, type something innocuous
> What's 2+2?

# 4. Claude will answer "4" and try to stop. The hook fires, sees the
#    sentinel, and forces continuation with the autopilot-active instructions.
#    Claude should then explain it sees autopilot is active and the user
#    isn't really running autopilot — and the user can rm .autopilot-active.

# Clean up
rm .autopilot-active .autopilot-stage
```

If the hook doesn't fire, check:
- `chmod +x` on the script
- Path in settings.json resolves correctly (`echo "$HOME/.claude/hooks/stop-autopilot.py"` and verify the file exists at that path)
- `python3` is on PATH (run `which python3` — should return /usr/bin/python3 or similar)
- Run `/hooks` inside Claude Code to confirm registration

## Known bug to dodge: don't install via the plugin system

[GitHub issue #10412](https://github.com/anthropics/claude-code/issues/10412): Stop hooks installed via the **plugin system** (under `~/.claude/plugins/marketplaces/.../hooks/`) silently fail when blocking with exit code 2. The hook here uses JSON-on-stdout instead of exit-2-stderr, so the plugin bug may not affect it — but the safe path is to install at `~/.claude/hooks/` directly. Not via plugins/marketplaces.

## Uninstall

```bash
rm ~/.claude/hooks/stop-autopilot.py
```

Then remove the corresponding entry from `~/.claude/settings.json`. Without the entry the file is harmless.

## Behavior summary

| Sentinel exists at cwd/transcript? | `.autopilot-halt-reason` exists? | `stop_hook_active`? | Result |
|---|---|---|---|
| No | (n/a) | (n/a) | Allow stop (exit 0, no output) |
| Yes | No | False | Block stop with reason, force continuation |
| Yes | Yes | False | Allow stop (autopilot itself requested halt) |
| Yes or No | (n/a) | True | Allow stop (loop guard — we already continued once) |

## What this hook can't do

- Won't catch Claude asking a question if the question is a deliberate part of a skill's design. The skill rewrites (`patches/*.md`) handle those.
- Won't restart the pipeline after it halts. If Claude writes `.autopilot-halt-reason`, the user has to fix the underlying issue and run `/build-comic autopilot` again.
- Won't run other validations. Pair with `comic-status-board` and `continuity-check` rules audit for actual content validation — those run as pipeline stages, not hooks.
