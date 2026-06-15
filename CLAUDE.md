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

### 5. Project TEXT is versioned in git; project BINARIES are not

(Amended 2026-06-10 by user instruction — the old blanket "never commit projects/" was too blunt and contradicted the repo's own granular .gitignore.) Per-project TEXT — shotlists, page plans/logs, QA defect registries and rubrics, prompt templates, turnaround/reference specs, height charts, VFX style bibles, ref ledgers, PROGRESS/STATUS — **is pipeline state and IS committed**, with a CHANGELOG entry like any other change. Binary outputs stay out via .gitignore (`pages/`, `final/`, `source/`, `.flow-scratch/`, and all `*.png`/`*.jpg`/`*.pdf` under `projects/`): renders are recoverable from the Flow media ids recorded in the ledgers/logs, and heavy sources live outside git. (The old note claiming `projects/` is a Drive symlink is stale — it's a real directory in this repo.) When starting work on a project whose text isn't yet tracked, add it — but only stage that project's text, never bulk-add other projects unreviewed.

## Generation defaults (active across all comic work here)

- **Backend**: Higgsfield direct via MCP (`mcp__c26fa20c-...`) — never browser-drive Higgsfield. Per `feedback_higgsfield_mcp.md`.
- **Model**: `nano_banana_flash` default. `nano_banana_pro` only when explicitly preferred. Per `feedback_higgsfield_model_flash.md`.
- **Count**: 1 per Higgsfield submit (paid). 4 per Flow submit (free). Per `feedback_higgsfield_count_one.md`.
- **Resolution**: 1k default. 2k only when explicitly requested. Per `feedback_higgsfield_resolution.md`.
- **Style**: photoreal CGI / DAZ3D. NOT 2D-stylized. Per `feedback_comic_style_3d.md`. Only L19 lettering and SFX overlays are 2D — and that overlay scope is explicitly bounded.
- **Coverage**: `always_clothed: true` is the default for every project. Garments may strain, stretch, or tear at seams; coverage of breasts/buttocks/groin is always preserved.
- **Cast**: NO background extras in panels. Only the named cast appears in frame. Per `feedback_no_extra_characters.md`.
- **Refs as truth**: appearance is carried by attached references (face card, body-tier lineup, costume turnaround, tier-N reinforcement, prior accepted panel, view pack, env ref). Prompts describe ACTION, CAMERA, LIGHTING — never appearance walls. The `refactor/refs-are-truth-prompts-are-action` branch enforces this structurally; main still has appearance-text rules in flight.
- **Flow account (dual-account safety)**: two Flow accounts exist (growcomics = primary/mac mini; marrtrobinson = laptop). Flow has no `/u/N/` switcher — account = browser profile. CONFIRM the active account before any Flow submit/edit/upload/delete/download, per `skills/comic-production/references/flow-accounts.md`.

## Architecture pointers

- **L-lessons catalog**: `skills/comic-production/references/lessons-learned.md`. L1–L32+ encode failure modes + fixes. Auto-injected by the rule registry walker in `next_panel.py`.
- **Rule registry**: `skills/comic-production/rules/` — per-rule modules. On the refactor branch this is restructured into `attach/ action/ match/ safety/` subdirectories.
- **Tier reinforcement refs**: `skills/comic-production/references/peak-body-scale/tier-{6,7,8,9}/`. Auto-attach when a panel hits the corresponding tier.
- **Canonical rubrics**: `skills/continuity-check/qa-checklist.md` + `cinematic-framing.md`. Pass these verbatim to QA subagents — never paraphrase. Per `feedback_dont_paraphrase_canonical_rubrics.md`.

## Generation protocol (MANDATORY — no freehand prompts, ever)

(Added 2026-06-10 after repeated rule-breaking under throughput pressure. Diagnosis: Claude's promises are not load-bearing; only in-path mechanical gates are. Full chain in `projects/<project>/qa/`.)

Every Flow/Higgsfield submit follows this chain — **reference sheets included**:

1. **COMPOSE** — `python3 qa/compose.py --job sheet:<id>|page:<panel>` is the ONLY legal source of prompts. Paste its output verbatim. It refuses if refs/staging/clamps are missing. Freehanding or editing a prompt is a protocol violation — the audit hash will catch it.
2. **AUDIT** — `python3 qa/audit_prompt.py --receipt … --prompt-file …` (independent checker). Both PASS lines get quoted in the transcript before the submit.
3. **SUBMIT** — attach exactly the receipt's list (verify each in the preview pane), then paste the composed prompt.
4. **POST-FLIGHT** — download the pick; a FRESH-context subagent judges it against the registry rubric → `qa/receipts/<job>.verdict.json`. The generator never grades its own work.
5. **BANK** — `python3 qa/bank.py` is the only way picks enter the ledger/pages-log; it refuses any entry lacking receipt + audit + passing verdict. Unbanked work is invisible downstream.
6. **VERIFY (user-side)** — `python3 qa/verify_chain.py` audits the ledger for chainless entries at any time.
7. **GATE INTEGRITY (Layer 8)** — every protocol script self-verifies all gate scripts against `qa/MANIFEST.sha256` before running; ANY edit to ANY gate locks ALL gates. **Claude is prohibited from running `integrity.py --rebless`** — re-blessing is a user-only act, done after reviewing the git diff on `qa/`. Receipts embed the manifest fingerprint, so every banked item records which gate-version produced it. If Claude believes a gate has a bug, the move is: report it to the user with the proposed diff — never patch-and-proceed.

## QA pattern

Per `feedback_audit_via_subagent.md` — spawn a fresh subagent for the audit pass. The main agent shortcuts to "looks fine" after generation; subagent gives independent read against the canonical rubric.

## Where outputs live

- Code: `~/Documents/claude-comic-pipeline/` (this repo, in git)
- Project outputs: `~/Library/CloudStorage/GoogleDrive-growcomics@gmail.com/My Drive/claude-comic-projects/` (Google Drive, synced cross-machine, visible to the dashboard)
- Dashboard: `resedas-mac-mini.tailf37470.ts.net:8765` (read-only, auto-discovers projects/)
