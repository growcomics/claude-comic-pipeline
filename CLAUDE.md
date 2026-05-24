# Comic Pipeline — Working Rules for Claude

This file tells Claude how to work in this repo. It auto-loads whenever a Claude Code session operates here or in any subdirectory.

## Source-of-truth rules

### 1. ALWAYS use the local skill files, NEVER the published `anthropic-skills:*` versions

This repo IS the source of truth for the comic pipeline. The published `anthropic-skills:comic-production` skill is older, generic, and does NOT contain L1–L32+, the rule registry, the tier-6/7/8/9 reinforcement refs, the always-clothed flag, L19 hybrid lettering, the surgical-scoping work, the refs-are-truth refactor, or anything else built here after the original bundle date.

When the user asks for a comic, route through the LOCAL skills only:

- `skills/comic-production/SKILL.md` — comic production workflow
- `skills/build-comic/` (or `commands/build-comic.md`) — orchestrator entry point
- `skills/script-breakdown/SKILL.md` — script → shotlist
- `skills/reference-gathering/SKILL.md` — refs gathering
- `skills/reference-acquisition/SKILL.md` — internet → 3D base ref conversion (refactor-branch addition)
- `skills/production-briefing/SKILL.md` — Phase 0 interview
- `skills/continuity-check/SKILL.md` — audit
- `skills/page-composer/SKILL.md` — layout + lettering
- `skills/comic-status-board/SKILL.md` — status
- `skills/style-lock/SKILL.md` — style presets

Do NOT invoke `anthropic-skills:comic-production`. If it gets surfaced by the matcher, override and use the local files instead.

### 2. ALWAYS verify branch + freshness before any comic work

Before any generation, breakdown, audit, or composition work, run:

```bash
cd ~/Documents/claude-comic-pipeline
git fetch --all --prune --quiet
git branch --show-current      # echo so the user sees what branch is active
git rev-list --count HEAD..@{u} 2>/dev/null && echo "commits behind upstream"
git log --oneline -1           # current HEAD
```

If the user has not specified a branch, default to `main`. If `main` is behind upstream:

```bash
git checkout main && git pull --ff-only origin main
```

If you're on a feature branch with unpushed work, do NOT auto-switch — surface the state to the user and let them choose.

### 3. ALWAYS update CHANGELOG.md atomically with the change

Per `feedback_changelog_with_timestamp.md`. Every commit that ships work to this repo must include a dated CHANGELOG entry in the same commit. New entries go at the TOP of the file under the current date.

### 4. NEVER touch `.git.backup-20260512-072853/`

Per `feedback_dont_delete_git_backup.md`. It's an intentional pre-rewrite history backup. Leave it alone, don't propose cleanup.

### 5. NEVER commit `projects/` content

`projects/` is symlinked to Google Drive (`~/Library/CloudStorage/GoogleDrive-growcomics@gmail.com/My Drive/claude-comic-projects/`). It's in `.gitignore`. Project outputs are NOT versioned in git.

## Generation defaults (active across all comic work here)

- **Backend**: Higgsfield direct via MCP (`mcp__c26fa20c-...`) — never browser-drive Higgsfield. Per `feedback_higgsfield_mcp.md`.
- **Model**: `nano_banana_flash` default. `nano_banana_pro` only when explicitly preferred. Per `feedback_higgsfield_model_flash.md`.
- **Count**: 1 per Higgsfield submit (paid). 4 per Flow submit (free). Per `feedback_higgsfield_count_one.md`.
- **Resolution**: 1k default. 2k only when explicitly requested. Per `feedback_higgsfield_resolution.md`.
- **Style**: photoreal CGI / DAZ3D. NOT 2D-stylized. Per `feedback_comic_style_3d.md`. Only L19 lettering and SFX overlays are 2D — and that overlay scope is explicitly bounded.
- **Coverage**: `always_clothed: true` is the default for every project. Garments may strain, stretch, or tear at seams; coverage of breasts/buttocks/groin is always preserved.
- **Cast**: NO background extras in panels. Only the named cast appears in frame. Per `feedback_no_extra_characters.md`.
- **Refs as truth**: appearance is carried by attached references (face card, body-tier lineup, costume turnaround, tier-N reinforcement, prior accepted panel, view pack, env ref). Prompts describe ACTION, CAMERA, LIGHTING — never appearance walls. The `refactor/refs-are-truth-prompts-are-action` branch enforces this structurally; main still has appearance-text rules in flight.

## Architecture pointers

- **L-lessons catalog**: `skills/comic-production/references/lessons-learned.md`. L1–L32+ encode failure modes + fixes. Auto-injected by the rule registry walker in `next_panel.py`.
- **Rule registry**: `skills/comic-production/rules/` — per-rule modules. On the refactor branch this is restructured into `attach/ action/ match/ safety/` subdirectories.
- **Tier reinforcement refs**: `skills/comic-production/references/peak-body-scale/tier-{6,7,8,9}/`. Auto-attach when a panel hits the corresponding tier.
- **Canonical rubrics**: `skills/continuity-check/qa-checklist.md` + `cinematic-framing.md`. Pass these verbatim to QA subagents — never paraphrase. Per `feedback_dont_paraphrase_canonical_rubrics.md`.

## QA pattern

Per `feedback_audit_via_subagent.md` — spawn a fresh subagent for the audit pass. The main agent shortcuts to "looks fine" after generation; subagent gives independent read against the canonical rubric.

## Where outputs live

- Code: `~/Documents/claude-comic-pipeline/` (this repo, in git)
- Project outputs: `~/Library/CloudStorage/GoogleDrive-growcomics@gmail.com/My Drive/claude-comic-projects/` (Google Drive, synced cross-machine, visible to the dashboard)
- Dashboard: `resedas-mac-mini.tailf37470.ts.net:8765` (read-only, auto-discovers projects/)
