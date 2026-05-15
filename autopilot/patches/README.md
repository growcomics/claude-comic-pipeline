# Patch overview — what changes in existing skills

The new autopilot mode requires surgical edits to existing skill files. Each patch is in its own file in this folder. Total lines changed across 4 files: ~50. Net behavior: backward compatible — existing modes (`status`, `auto`, named stage) work exactly as before. FMG-only behavior is preserved when no config exists.

| File | Patch doc | Lines edited | What changes |
|---|---|---|---|
| `skills/comic-production/SKILL.md` | `comic-production-line-300.md` | ~30 | Rules block: read from `production-config.json` if it exists, else ask once at start (legacy). Adds per-transformation-type defaults table (FMG / BE / Glute / MMG / Mixed). |
| `skills/comic-production/references/shotlist-driven-flow.md` | `shotlist-driven-flow-break-conditions.md` | ~20 | Per-panel break conditions become config-keyed policies. Default `on_all_bad=retry-with-cgi-anchor-boost`. |
| `skills/continuity-check/SKILL.md` | `continuity-check-line-130.md` | ~10 | "Ask which to fix" at audit end becomes 4-option policy. Default `batch-end`. |
| `skills/comic-production/scripts/next_panel.py` | `next_panel-find-lineup.md` | ~15 | **Optional.** `find_lineup()` reads `lineup_files.tier_low/tier_high` from config so BE/glute/MMG projects can use their own lineup PNGs. Symlink workaround documented for skip-this-patch case. |

Plus one *replacement* file (not a patch — straight swap):

| File | Replacement source | What changes |
|---|---|---|
| `commands/build-comic.md` | `commands/build-comic.md` | Adds `autopilot` mode + briefing auto-invocation. Existing modes unchanged. |

And two new files (additions, not edits):

| File | Source | Purpose |
|---|---|---|
| `skills/production-briefing/SKILL.md` | `skills/production-briefing/SKILL.md` | New skill — one-shot pre-flight interview. Leads with transformation-type question. |
| `~/.claude/hooks/stop-autopilot.py` | `hooks/stop-autopilot.py` | New Stop hook — forces continuation when `.autopilot-active` sentinel exists. |

## Apply order

1. **Back up the originals**:
   ```bash
   cd ~/.claude
   mkdir -p backups/2026-05-13
   cp commands/build-comic.md backups/2026-05-13/build-comic.md.bak
   cp skills/comic-production/SKILL.md backups/2026-05-13/comic-production.SKILL.md.bak
   cp skills/comic-production/references/shotlist-driven-flow.md backups/2026-05-13/shotlist-driven-flow.md.bak
   cp skills/continuity-check/SKILL.md backups/2026-05-13/continuity-check.SKILL.md.bak
   cp skills/comic-production/scripts/next_panel.py backups/2026-05-13/next_panel.py.bak
   ```

2. **Apply the patches**. Each patch doc shows the exact "Find this" / "Replace with" pair. Open each existing file, find the marked section, swap in the new text. The `next_panel.py` patch is optional — see the symlink workaround at the bottom of `next_panel-find-lineup.md`.

3. **Drop in the replacement**:
   ```bash
   cp output/commands/build-comic.md ~/.claude/commands/build-comic.md
   ```

4. **Add the new briefing skill**:
   ```bash
   mkdir -p ~/.claude/skills/production-briefing
   cp output/skills/production-briefing/SKILL.md ~/.claude/skills/production-briefing/SKILL.md
   ```

5. **Install the Stop hook** (see `hooks/INSTALL.md`).

6. **Restart Claude Code**.

## Per-transformation-type lineup PNGs — extra work

If you're producing BE / glute / MMG comics, you'll need to author the corresponding lineup PNG (numbered 1-6 figures, progressive growth, same outfit/hair/background as the FMG lineup but for the target attribute). One-time per type.

The pipeline searches these locations in order:
1. `<project>/references/style/<filename>` (project-local override)
2. Repo-bundled `assets/`
3. `~/.claude/skills/comic-production/assets/`

So you can either:
- **Per-project** (most flexible): drop the lineup PNG in `<project>/references/style/breast-size-lineup.png` (or glute, or male-muscle, etc.)
- **User-level** (reuse across all projects): drop it in `~/.claude/skills/comic-production/assets/breast-size-lineup.png`

Without the `next_panel.py` patch (#4 above), you can also symlink to the FMG default filename:
```bash
cd <project>/references/style/
ln -s breast-size-lineup.png muscle-size-lineup.png
```

## Verify

In a fresh Claude Code session:

```
/help
```

Should show `/build-comic` with description mentioning `autopilot`.

In any directory:
```
/build-comic
```
Status mode — unchanged.

```
/build-comic auto
```
Auto mode — unchanged, gates at the same points.

```
/build-comic autopilot
```
- In fresh project (no config) → triggers `production-briefing` skill. Asks transformation type first, then everything else.
- After answering, `production-config.json` written at project root. Exit.
- Re-run → reads config, runs end-to-end.

## Rollback

```bash
cd ~/.claude
mv backups/2026-05-13/build-comic.md.bak commands/build-comic.md
mv backups/2026-05-13/comic-production.SKILL.md.bak skills/comic-production/SKILL.md
mv backups/2026-05-13/shotlist-driven-flow.md.bak skills/comic-production/references/shotlist-driven-flow.md
mv backups/2026-05-13/continuity-check.SKILL.md.bak skills/continuity-check/SKILL.md
mv backups/2026-05-13/next_panel.py.bak skills/comic-production/scripts/next_panel.py
rm -rf skills/production-briefing
```

Then remove the Stop hook entry from `~/.claude/settings.json` and `rm ~/.claude/hooks/stop-autopilot.py`.

Restart Claude Code. Back to pre-autopilot state.
