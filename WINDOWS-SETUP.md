# Windows Machine — Generation Backend Setup

**For the human:** copy this to the Windows computer (or just `git pull` the repo there — it's
committed). Then tell Claude: *"Read WINDOWS-SETUP.md and get a generation backend working."*

You have **three** ways to render panels. They are ranked by how fast they unblock you on a
fresh Windows machine. **Path A (Google Flow) needs no installs and no credits — use it.**

---

## Diagnosis (what the Windows machine reported)

| Backend | State | Real blocker |
|---|---|---|
| Higgsfield **MCP** (connected image MCP) | Installed & connected ✓ | Account has only **1.58 credits** → `generate_image` returns 403. **Not an install problem — a credits/account problem.** |
| Higgsfield **Python runner** | Not usable | **Python not installed** (only the Windows Store stub) + Chrome token-bridge not set up. |
| Google **Flow** (Chrome MCP) | Chrome MCP connected ✓ (macmini / laptop / Browser 2 listed) | Just needs a signed-in Flow account — **which you have.** |

---

## ✅ Path A — Google Flow via Chrome MCP (RECOMMENDED — free, no installs)

This is the right path because: Flow is **free on a Google Pro/Pro Ultra plan**, it runs the same
Nano Banana 2 model, it needs **no Python, no token bridge, no Higgsfield credits**, and the
Chrome MCP is already connected on this machine.

**Steps (Claude does most of this):**

1. **Pick the browser** when Claude asks ("Which connected Chrome browser…") — choose the one
   where you're signed into your Google Flow account (e.g. `laptop` or `macmini`).
2. **Make sure that Chrome is signed into the Google account that has Flow** (Pro/Pro Ultra), and
   open `https://labs.google/fx/tools/flow`. Create or open a project.
3. Tell Claude: *"Drive Flow to generate the panels in `projects/violet-sentinel-growth/` —
   start with the Phase 0 reference sheet, then the 5 pages in order."*
4. Claude follows the skill's Flow guide automatically:
   - `skills/comic-production/references/flow-workflow.md` — UI mechanics, ref attachment
   - `skills/comic-production/references/shotlist-driven-flow.md` — the per-panel loop

**Notes / gotchas (from the skill):**
- Flow aspect ratios are fixed (16:9, 4:3, 1:1, 3:4, 9:16). Use **3:4** for portrait comic pages.
- Output count x4 is free on Pro — let Claude pick the best variant.
- **Content policy:** on Flow, drop celebrity names from prompts that already have detailed body
  descriptions; the face reference card carries the likeness. (See flow-workflow.md "Content
  Policy Quirks.")
- No batch/resume on Flow — it's hand-driven per panel, but free. Fine for these 5 pages.

That's the whole unblock. Everything below is optional.

---

## Path B — Fix Higgsfield MCP (only if you specifically want Higgsfield)

The MCP is **already installed and connected** — do **not** reinstall it. The only problem is the
account it's authenticated to has 1.58 credits. Two fixes:

1. **Top up / switch plan.** Open `https://higgsfield.ai` → Billing, and either buy Flash credits
   or activate the unlimited plan. Then in Claude: *"check the Higgsfield balance"* and once it's
   positive, *"generate the panels."*
2. **Re-auth to the paid account.** If your *Mac* uses a different Higgsfield account that already
   has credits/unlimited, sign the Windows Higgsfield connector into **that same account** (in the
   Claude app's connector/MCP settings, disconnect and reconnect, logging into the paid account).
   This is the likely root cause — the Windows machine connected to a fresh/free account.

No file installs are needed for the MCP path — it's a connector + credits.

---

## Path C — Higgsfield Python runner (optional, for overnight batch)

Only worth it if you want unattended batch runs of many panels. More setup. Windows specifics:

1. **Install real Python** (the Store stub doesn't work). In PowerShell:
   ```powershell
   winget install -e --id Python.Python.3.12
   ```
   Then close/reopen the terminal and confirm: `python --version`.
2. **Install Node deps for the token relay:**
   ```powershell
   cd $HOME\code\claude-comic-pipeline\skills\comic-production\scripts
   npm install chrome-remote-interface
   ```
3. **Launch Chrome with the debug port** (one time, Windows path):
   ```powershell
   & "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
   ```
   Verify: open `http://localhost:9222/json` in a browser — it should list tabs.
4. **Inject the token bridge:** open `https://higgsfield.ai/image/nano_banana_2`, log in,
   DevTools → Console, paste the contents of `scripts/token_bridge.js`, Enter.
5. **Start the relay:** `node token_relay.js` (leave running).
6. Tell Claude: *"run the Higgsfield runner on panels.json"* — it drives `runner.py`.

⚠️ Path C still needs Higgsfield **credits or unlimited** (same as Path B). If credits are the
problem, Path C doesn't solve it — only Path A (Flow) is truly free.

---

## TL;DR

- **Want to generate right now, free?** → **Path A (Flow).** Pick the browser, sign into Flow, go.
- **Want Higgsfield specifically?** → **Path B**: it's already installed, just fix credits/account.
- **Want overnight batch?** → **Path C**: install Python + token bridge (and still need credits).

The skill, prompts, refs, and the `violet-sentinel-growth` project are already cloned and ready —
this is purely about which rendering backend to point at.
