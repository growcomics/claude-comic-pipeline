# Lieutenant Workspace (MVP plan, 2026-10-01)

Goal: a hired lieutenant can run a comic end to end in a browser at
`3dmusclecomics.com/studio`, without the owner's Claude Code. Release stays owner-only.

## Owner decisions (2026-10-01 poll)

| Decision | Choice |
|---|---|
| Chat brain | Claude API from the Studio server (existing key in `data/ai.json`) |
| Sign-in | Magic link per person (Artist Portal pattern) |
| Visibility | Every comic of the person's brand(s) |
| Generation | Higgsfield worker, 50 images/person/day, at least 30 s between submits |

## What the lieutenant sees

`ws.php` opens on **My comics**: every comic tagged with the person's brand(s), plus **New comic**.

Each comic page has five panels:

1. **Pages.** One row per page with its prompt, takes, pick and comment. Buttons: **Generate 2 or 4 takes** and **Upload results**.
2. **Chat.** A team thread with Claude in it. Claude can:
   - draft page prompts from the story,
   - say what's left,
   - suggest fixes.
   Claude only *proposes* actions (set a prompt, add pages, generate takes). Each proposal shows as a card, and nothing runs until a person clicks **Confirm**.
3. **Refs & uploads.** Drag-drop character sheets, locations and source images, and mark which refs a page uses.
4. **Queue.** Jobs show their state live (queued → generating → landed), next to the person's remaining quota for the day.
5. **Picker** (`picker.php`), in the owner's format:
   - a grid of every take per page; click a take to multi-pick it,
   - a lightbox with ←/→ for takes, ↑/↓ for pages and Enter to pick,
   - a comment box per page and a **Copy list** button,
   - Claude's pick tagged,
   - settled pages hidden, with a **show settled** toggle.

There are no port, post, publish or release controls anywhere for lieutenants.

## What the owner gets

`team.php` (owner only) lets the owner:

- add a person and get their private magic link, which is shown once and can be rotated or deactivated,
- set each person's brands,
- assign each comic to a brand,
- see each person's usage: images per day, and chat messages and dollars,
- set the per-person and global daily caps.

## Generation engine

- **New queue.** `data/ws/jobs.json` is separate from the old `jobs.json`, so dormant Flow jobs never run.
- **Worker.** An opsbox timer job.
  - On 2026-10-01 a check confirmed that headless `claude -p` on the VM can see the `claude_ai_higgsfield` tools.
  - Each run claims jobs and generates with `nano_banana_pro`, 1k, one image per call, at least 30 s apart.
  - Results land under the right page.
  - It authenticates with its own scoped key in `data/ws/worker.json`, never the master bridge key.
- **Caps** are enforced by the server when a job is queued: 50 images per person per day, plus a global daily ceiling as a credit guard (default 150).
- **Credit-rule exception.** This lifts the old "Higgsfield cap 0" rule for this lane only.

## Security fixes that ship first

An audit on 2026-10-01 found that the Studio is not safe to share yet:

1. **Public source.** Ten `*.bak-*` PHP files under `/studio/` download as raw source with no login, because the `.htaccess` regex misses them.
   - Fix: widen the deny rule and move the files into a locked attic folder. Nothing is deleted.
2. **No roles.** Every login sees finance, posting, port-to-site, Patreon, ops and the AI-key controls, and the master bridge key is printed on the Studio home.
   - Fix: add one hook in `inc/boot.php` `is_authed()` → `ws_gate()`. A lieutenant session can reach only `ws.php`, `ws-api.php`, `picker.php`, `img.php` (own-brand comics only), `help.php` and logout. Every other page returns 403.
   - Existing logins (admin, editor, collab) behave exactly as before.
3. **Unclaimed finance page.** `finance.php` is unclaimed. Owner action: open it once and click claim.

## Data (all new files, locked writes)

All of these live under `data/ws/`, which `data/.htaccess` already denies to the web.

| File | Contents |
|---|---|
| `team.json` | `people[{id, name, brands[], active, tokenHash, rev, caps, createdAt, lastSeenAt}]`, `projectBrands{pid: brand}`, `brands[]`, `settings` |
| `proj-<pid>.json` | `pages[{n, title, prompt, refs[], status}]`, `refs[{file, label, kind}]`, `story`, `style` |
| `chat-<pid>.json` | `msgs[{id, ts, uid, by, role, text, actions[]}]` |
| `picks-<pid>.json` | `pages{group: {pick[] or 'drop', c, prev_c, sig, by, ts}}` |
| `jobs.json` | `jobs[{id, pid, page, prompt, refs[], takes, uid, status, done, files[], …}]` |
| `usage.json` | `{day: {uid: {gens, msgs, usd}}, global: {day: gens}}` |

Images stay in the existing `images-<pid>.json` and `uploads/<pid>/`, with `group = 'Page NN'`. That way `review.php`, `export.php` and the owner's cockpit keep working. Picks are mirrored into image `accepted`.

## Files

**New:**
- `inc/ws.php`: gate, roles, brands, quotas, stores
- `ws.php`
- `ws-api.php`
- `picker.php`
- `team.php`
- `ws-worker.php`: key-gated `claim`, `refurl`, `submit_ok`, `ingest_url`, `done`

**Edited (small):**
- `inc/boot.php`: one hook in `is_authed()`, plus a `require_once`
- `.htaccess`: deny `*.bak*`
- `index.php`: Team link for the owner

**Orchestrator:** `ops/opsbox/jobs/ws-worker.{conf,md}`

## Ship protocol

1. Build in worktree `feat/studio-workspace`.
2. Test locally with PHP-wasm 8.1: real requests through the gate, quotas, picker saves, and magic-link login.
3. Parse-check every file.
4. Deploy one file at a time. For each: fetch live first, fetch it back after the push, curl-check, and confirm the `error_log` mtime has not changed.
5. Run an adversarial security review before the gate goes live.
6. Smoke-test with a throwaway lieutenant and a throwaway project, then remove both.
7. Commit with a CHANGELOG entry and push to the private `backup` remote.
8. Snapshot the ops hub.
