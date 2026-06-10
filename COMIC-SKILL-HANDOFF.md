# Comic Production Skill — Handoff / Setup on a Second Computer

**For the human:** You don't need to run any of this yourself. Copy this file to the other
computer (AirDrop, iCloud Drive, email it to yourself, or drop it on the Desktop). Then open
Claude Code there and say:

> "Read COMIC-SKILL-HANDOFF.md and set up the comic production skill on this computer."

Claude will do every terminal step below for you. The only thing **you** might have to do by
hand is the GitHub SSH key approval (Step 1) — and Claude will tell you exactly what to click.

---

## The one-line summary (for Claude)

The 8 comic skills are **symlinks** in `~/.claude/skills/` pointing into a single private git
repo. To replicate the skill on a new machine: ensure SSH access to GitHub, clone the repo to
the exact path below, check out the working branch, and recreate the symlinks. That's it — no
files get copied by hand; git carries everything (scripts, references, rules, and the binary
muscle-lineup PNG assets, which ARE tracked in git).

| Fact | Value |
|---|---|
| GitHub repo (SSH) | `git@github.com:growcomics/claude-comic-pipeline.git` |
| Clone destination | `~/code/claude-comic-pipeline` (must be this exact path — symlinks depend on it) |
| Working branch | `feat/flow-runner` |
| Symlink source | `~/code/claude-comic-pipeline/skills/<name>` |
| Symlink target | `~/.claude/skills/<name>` |
| GitHub account | growcomics (email: growcomics@gmail.com) |

**The 8 skills to symlink:**
`comic-production`, `comic-status-board`, `continuity-check`, `page-composer`,
`production-briefing`, `reference-gathering`, `script-breakdown`, `style-lock`

---

## ⚠️ Before you start (do this ON THE SOURCE computer first)

The source machine may have **uncommitted work** that the clone won't include unless it's
pushed. On the source computer, have Claude run:

```bash
cd ~/code/claude-comic-pipeline
git status            # see what's outstanding
git add -A && git commit -m "WIP before second-machine handoff"
git push -u origin feat/flow-runner
```

If this is skipped, the new computer will still get a working skill — just not the very latest
unsaved edits.

---

## Setup steps (Claude runs these ON THE NEW computer)

### Step 1 — Confirm GitHub SSH access

```bash
ssh -T git@github.com
```

- **If it greets you by username** (`Hi growcomics! You've successfully authenticated...`) → good, go to Step 2.
- **If it says "Permission denied (publickey)"** → this machine has no SSH key registered with
  GitHub yet. Claude should generate one and show the human what to paste into GitHub:

  ```bash
  ls ~/.ssh/id_ed25519.pub 2>/dev/null || ssh-keygen -t ed25519 -C "growcomics@gmail.com" -f ~/.ssh/id_ed25519 -N ""
  cat ~/.ssh/id_ed25519.pub
  ```

  **Human action:** copy the printed key, go to https://github.com/settings/keys → "New SSH
  key", paste it, save. Then re-run `ssh -T git@github.com` to confirm.

  *(Alternative if SSH is a hassle: switch the clone URL in Step 2 to HTTPS
  `https://github.com/growcomics/claude-comic-pipeline.git` and authenticate with a GitHub
  Personal Access Token or the `gh` CLI `gh auth login`.)*

### Step 2 — Clone the repo to the exact path

```bash
mkdir -p ~/code
git clone git@github.com:growcomics/claude-comic-pipeline.git ~/code/claude-comic-pipeline
cd ~/code/claude-comic-pipeline
git checkout feat/flow-runner
```

### Step 3 — Recreate the symlinks into ~/.claude/skills/

```bash
mkdir -p ~/.claude/skills
for s in comic-production comic-status-board continuity-check page-composer \
         production-briefing reference-gathering script-breakdown style-lock; do
  ln -sfn ~/code/claude-comic-pipeline/skills/$s ~/.claude/skills/$s
done
```

### Step 4 — Verify

```bash
ls -la ~/.claude/skills/ | grep comic           # should show arrows -> ~/code/claude-comic-pipeline/...
ls ~/code/claude-comic-pipeline/skills/comic-production/assets/   # should list the muscle-lineup PNGs
```

Then in Claude Code, `/comic-production` should be available and load this skill.

---

## Keeping the two computers in sync (ongoing)

Whenever you finish work on one computer, have Claude push it; on the other, pull before
starting:

```bash
# after working — on whichever machine you used:
cd ~/code/claude-comic-pipeline && git add -A && git commit -m "describe the change" && git push

# before working — on the other machine:
cd ~/code/claude-comic-pipeline && git pull
```

You can just tell Claude "push my comic work" or "pull the latest comic skill" — it knows the
repo from this file.

---

## Notes / gotchas

- **Same Claude (Anthropic) account does NOT sync skills.** Skills are local files on disk;
  only git syncs them. That's why this handoff exists.
- **The clone path matters.** Symlinks point at `~/code/claude-comic-pipeline`. If you clone
  somewhere else, either clone to that path or update the symlink source paths in Step 3.
- **Binary assets are safe.** The muscle-size lineup PNGs and `visual-quality-standards.json`
  are committed to git, so the clone gets them — nothing to copy separately.
- **The skill itself never calls GitHub.** GitHub is only used to move the skill *files* between
  your computers. There's no API token or secret baked into the skill.
- **`projects/*/pages/`, `final/`, `*.pdf`** and a few other output folders are gitignored —
  finished render outputs don't travel between machines via this repo. Only the skill code,
  references, configs, and shotlists do.
