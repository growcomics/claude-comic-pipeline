# Comic Pipeline v4 — Architecture

The unanswered question from v1-v3 was: **how do you GUARANTEE Claude Code never stops mid-generation?**

v1-v3 answers (prose, hooks, briefing) reduce the probability but can't guarantee it. The model is probabilistic. Hooks intercept symptoms. Even with three layers, there's a non-zero chance Claude reaches for some new interactive tool that wasn't on the matcher list, or writes a question in plain text that the Stop hook catches but the user still sees.

v4's answer: **take Claude Code out of the per-panel loop entirely.** Claude does the smart upstream work (briefing, script breakdown, reference gathering), then hands off to a deterministic Python runner that executes per-panel generation without Claude Code involvement. The runner uses the Claude **API** (not Claude Code) for variant picking so quality isn't sacrificed — but it's an API call, not an interactive session, so there's no AskUserQuestion path. When the runner finishes, control returns to Claude Code for continuity check and composition.

This shifts the guarantee from "the model behaves" to "the code executes." Code halts only on the failure modes you explicitly programmed it to halt on.

---

## Pipeline split

```
Stage 0  Briefing                Claude Code (interactive)    ← captures all decisions
Stage 1  Script breakdown        Claude Code (interactive)    ← one-time per project
Stage 2  Reference gathering     Claude Code (interactive)    ← one-time per project
─────────────────── HAND-OFF ────────────────────────
Stage 3  Generation              Python runner (subprocess)   ← no Claude Code at all
Stage 4  Continuity check        Claude Code (interactive)    ← runs full audit
Stage 5  Composition             Python (page-composer)       ← deterministic
```

The hand-off works like this. Claude Code's `/build-comic autopilot` invokes the runner as a subprocess:

```bash
python ~/.claude/skills/comic-production/scripts/runners/<platform>_runner.py \
    --project <project_root> \
    --config production-config.json
```

Claude Code's only role during Stage 3 is `subprocess.run()` and wait. It can't ask anything because it's not doing anything — it's waiting for a process to exit. When the runner exits, Claude Code inspects state.json and proceeds.

---

## What's preserved (the quality concern)

The user's concern: **continuity across panels must not regress.** Characters must look the same. Locations must look the same. Props must look the same. Transformation tiers must stay monotonic.

All of that continuity logic already lives in `next_panel.py`. It implements:

| Continuity mechanism | Where it lives | What it does |
|---|---|---|
| **View-aware chaining (L1.5)** | `VIEW_COMPATIBILITY` table, `pick_chain_anchor()` | Picks the most recent view-compatible prior panel as the state anchor — not blindly N-1 |
| **L10 env chaining** | `pick_location_anchor()` | First panel in a location uses `_source.jpg`; subsequent panels in the same location use the accepted establishing shot |
| **Face card per character** | `find_face_card()` | Canonical identity anchor attached on every panel with that character |
| **L11 lineup attachment** | `should_attach_lineup()`, `find_lineup()` | Muscle-size lineup ref attached on full-body or stage-change panels |
| **Prop refs** | shotlist `props[]` resolution | Each named prop has its ref folder attached |
| **L7 no-baked-lettering** | `compose_prompt()` rules block | Speech bubbles / SFX / captions never in the render prompt — added at page-composer stage |
| **Mandatory rules block** | `mandatory_rules.active` from config | Per-type rules baked into every prompt |

The runner does not reimplement any of this. It invokes `next_panel.py --as-json` for each panel and gets back a complete plan with: composed prompt, refs to attach in order, aspect ratio, count, anchor identification, stage-change flag. The runner's job is faithful execution of that plan.

**That means: zero quality regression vs. having Claude Code drive the loop manually.** The plan composition is identical. The difference is who clicks "generate" — Claude Code (probabilistic, can ask questions) vs. a Python script (deterministic, cannot).

---

## Variant picking — preserving quality without an interactive Claude

Today, Claude Code visually inspects the 4 variants per panel and picks the best one. The criteria are documented in `shotlist-driven-flow.md` step 6: face acting, anatomy, CGI fidelity, camera adherence, reference adherence.

The runner can't open the panels in a UI to inspect them itself. So the runner uses the **Claude API directly**:

```
runner saves 4 variants to disk
       ↓
runner base64-encodes each PNG
       ↓
runner calls anthropic.Anthropic().messages.create() with:
  - model: claude-opus-4-7
  - system prompt: variant evaluation criteria from shotlist-driven-flow.md
  - user content: the 4 images + panel context (camera, action, transformation tier, rules)
       ↓
Claude returns: {"pick": 1-4, "reason": "...", "concerns": [...]}
       ↓
runner saves picked variant as accepted.png
       ↓
runner advances to next panel
```

**Quality is preserved.** It's still Claude doing the picking, with the same criteria. The difference is the model is called via API (no AskUserQuestion possible), not via Claude Code (where AskUserQuestion exists).

Variant picking can be configured in `production-config.json`:

- `generation.variant_picker = "claude_api"` (default) — uses Claude API as above
- `generation.variant_picker = "first"` — always pick variant 1, fastest, no API cost
- `generation.variant_picker = "heuristic"` — image hashing + simple checks (no API call, no quality guarantee for face acting)

Default is the API picker. Costs ~$0.01-0.05 per panel depending on image size (small images, ~$0.01 ea). For a 30-panel comic, ~$0.30-1.50 in API costs. Cheap vs. an hour of attended supervision.

---

## What halts the runner — the only stop conditions

By design, the runner halts cleanly on a defined set of conditions. State.json preserves enough info for resume. Anything else is treated as a transient error and retried.

| Halt condition | Trigger | Recovery |
|---|---|---|
| `MISSING_*` ref from `next_panel.py` | Required ref file not on disk | User drops file in stated path, re-runs |
| Content-policy refusal (Flow only) | Safety filter rejects prompt | User edits shotlist entry, re-runs |
| Auth expired / token bridge dead | Higgsfield/Flow auth fails | User re-auths, re-runs |
| Max retries on one panel | All retries fail with same error | User inspects, edits or skips, re-runs |
| Filesystem unwritable | OS error on save | User fixes permissions, re-runs |
| Anthropic API key missing | env var unset for variant_picker=claude_api | User sets ANTHROPIC_API_KEY, re-runs |
| Higgsfield credits exhausted | API returns insufficient-credit error | User tops up, re-runs |
| Catastrophic browser crash (Flow only) | CDP connection lost beyond reconnect | User restarts Chrome, re-runs |

That's the complete list. Network blips, slow generations, single-variant failures, transient timeouts — all retried automatically with backoff. State.json is updated atomically after each panel commit, so resume picks up exactly where the runner halted.

---

## State management

`state.json` at project root tracks runner state:

```json
{
  "version": 1,
  "platform": "flow",
  "started_at": "2026-05-14T12:00:00Z",
  "last_updated": "2026-05-14T13:42:15Z",
  "panels": {
    "p01-01": {
      "state": "accepted",
      "picked_variant": 2,
      "pick_reason": "best face acting, V1 had flat expression",
      "concerns": [],
      "attempts": 1,
      "completed_at": "2026-05-14T12:03:21Z"
    },
    "p01-02": {
      "state": "accepted",
      "picked_variant": 1,
      "attempts": 1
    },
    "p01-03": {
      "state": "in_progress",
      "attempts": 2,
      "last_error": "transient timeout, retrying"
    }
  },
  "halt_reason": null,
  "halt_panel_id": null
}
```

On startup, runner reads state.json. Panels with `state="accepted"` are skipped. The first panel without `state="accepted"` becomes the resume point.

State is written atomically: write to `state.json.tmp`, fsync, rename to `state.json`. No partial writes survive a crash.

---

## Two-runner architecture

`flow_runner.py` and `higgsfield_runner.py` share a `runner_core.py` module with the panel-loop scaffolding. They only differ in:

- **flow_runner.py**: drives Flow via Playwright + CDP. Connects to existing Chrome with `--remote-debugging-port=9222`. Opens labs.google/fx/tools/flow. For each panel: paste prompt, attach refs via drag-drop or file picker, set aspect, click generate, wait for 4 variants, download each. Resilient to UI changes via configurable selectors.

- **higgsfield_runner.py**: uses Higgsfield's HTTP API via the existing token_relay.js (or directly with an API key if Higgsfield exposes one). For each panel: POST to the generation endpoint with prompt + ref URLs, poll for completion, download outputs.

Both call the same `variant_picker.py` and write to the same state.json format. Switching platforms = changing `platform` in production-config.json.

---

## How Claude Code orchestrates the runner

The updated `commands/build-comic.md` autopilot section:

```
Stage 3 (Generation) in autopilot mode:

1. Touch .autopilot-active sentinel
2. Determine platform from production-config.json -> platform
3. Build subprocess command:
     python ~/.claude/skills/comic-production/scripts/runners/<platform>_runner.py \
         --project <cwd> \
         --config production-config.json
4. Invoke via Bash tool, attach stdout to a log file
5. While the subprocess runs:
   - Stream stdout/stderr to chat as status updates (one line per panel)
   - Periodically (every 60s) refresh STATUS.md and read it back inline
6. When subprocess exits, check exit code:
   - 0: all panels complete, advance to Stage 4
   - 1: halt with reason in state.json, surface to user
   - 2: catastrophic error (no resume possible), surface and stop
```

Claude Code is not in the per-panel loop. It's a subprocess invoker + progress streamer.

---

## What about the user's existing Higgsfield runner?

The user mentioned (per memory) an existing `runner.py` for Higgsfield with `state.json`, `token_bridge.js`, `token_relay.js`. v4 ships its own `higgsfield_runner.py` but provides an **interface contract** so the user's existing runner can be substituted via `production-config.json`:

```json
{
  "higgsfield": {
    "runner_script": "/Users/jay/mac-mini/higgsfield/runner.py",
    "runner_args": ["--config-from-stdin"]
  }
}
```

If `runner_script` is set, autopilot invokes the user's existing script with the panel queue piped to stdin and reads results from a file the user's script writes. See `higgsfield_runner.py` docstring for the contract.

---

## Cost / time estimate

For a typical 25-30 page comic, ~150 panels:

| Phase | Time | Cost |
|---|---|---|
| Briefing | 5-10 min | $0 (interactive, no API) |
| Script breakdown | 5-15 min | $0-2 (interactive Claude Code) |
| Reference gathering | 30-60 min | $0-3 (manual + interactive) |
| **Generation (runner)** | **2-4 hr unattended** | **~$2-8 (variant picker API)** |
| Continuity check | 5-15 min | $1-5 (vision audit) |
| Composition | 2-5 min | $0 (pure Python) |

Generation is unattended. The user walks away after Stage 2 and comes back to either a finished comic or a state.json telling them which panel halted and why.

For a side-by-side: today the same comic takes ~6-12 hours of attended Claude Code session time. v4 cuts that to ~1 hour of attended pre-work + 2-4 hours of unattended generation. Strictly better.

---

## What does NOT change

Per the consistent v1-v3 promise:

- Every L1-L13 lesson stays enforced (codified in next_panel.py)
- View-aware chaining unchanged
- Env ref chaining unchanged
- L7 no-baked-lettering unchanged
- L9 job_id capture unchanged
- L11 lineup attachment unchanged
- Mandatory rules block per transformation type unchanged
- Prose discipline + Stop hook + PreToolUse hook from v2/v3 still apply during stages 0-2 and 4

The runner is additive to Stage 3 only. Other stages keep working exactly as v3.

---

## What v4 ships

```
comic-autopilot-v4/
├── runners/
│   ├── runner_core.py             ← shared scaffolding (panel loop, state, retries)
│   ├── variant_picker.py          ← Claude API vision for variant selection
│   ├── flow_runner.py             ← Playwright-based Flow driver
│   ├── flow_selectors.py          ← user-editable Flow UI selectors
│   ├── higgsfield_runner.py       ← Higgsfield runner (uses user's token_relay or stub)
│   ├── requirements.txt           ← playwright, anthropic, pillow
│   └── README.md
├── commands/
│   └── build-comic.md             ← updated autopilot section
├── docs/
│   ├── ARCHITECTURE.md            ← this file
│   ├── VARIANT-PICKING.md         ← deep dive on the Claude API approach
│   ├── HIGGSFIELD-INTEGRATION.md  ← how to use user's existing runner OR the v4 one
│   └── FLOW-SELECTORS.md          ← updating selectors when Google changes Flow's UI
├── tests/
│   ├── test_variant_picker.py     ← mocked API call test
│   ├── test_state.py              ← state.json atomic writes test
│   └── test_flow_runner_mock.py   ← mocked Playwright test
└── INSTALL-V4.md                  ← install steps
```

The runners run from `~/.claude/skills/comic-production/scripts/runners/` so they're packaged as part of the Claude Code skill. The user updates them by re-installing.
