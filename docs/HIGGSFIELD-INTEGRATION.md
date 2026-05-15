# Higgsfield Integration

The v4 runner supports Higgsfield in two modes. Pick whichever matches your current setup.

## Decision tree

```
Do you already have a working runner.py for Higgsfield?
├── YES → use mode="external_script" (wraps your existing runner)
└── NO  → use mode="api" (direct HTTP via token_relay)
```

You set the mode in `production-config.json`:

```json
{
  "higgsfield": {
    "mode": "external_script",
    ...
  }
}
```

---

## Mode A: `external_script` — wraps your existing runner.py

This is the recommended mode if you already have a working `runner.py` (per the Mac Mini setup: `--remote-debugging-port=9222`, `token_bridge.js`, `token_relay.js`, `state.json`). The v4 wrapper:

1. Reads the next panel plan from `next_panel.py --as-json`
2. Writes a single-panel `panels.json` to the project root
3. Invokes your existing `runner.py` as a subprocess
4. Waits for it to write `results.json` (or PNGs to `pages/panels/<panel_id>/v[1-4].png`)
5. Hands the variants to `variant_picker.py`
6. Commits the picked variant + updates state.json

Your existing runner stays the source of truth for Higgsfield auth, browser state, retry-on-token-refresh, etc. The v4 wrapper adds orchestration around it without touching the parts that work.

### Config

```json
{
  "higgsfield": {
    "mode": "external_script",
    "runner_script": "/Users/jay/Documents/higgsfield-pipeline/runner.py",
    "folder_id": "abc-123-folder-uuid",
    "panels_input": "panels.json",
    "panels_output": "results.json"
  }
}
```

### Expected runner.py CLI

The wrapper invokes your runner like:

```bash
python <runner_script> --panels <project>/panels.json --output <project>/results.json
```

Your runner should:

1. Read `panels.json` — see schema below
2. For each panel, submit to Higgsfield with the prompt, refs, aspect, and count
3. Write each variant PNG to `pages/panels/<panel_id>/v{N}.png`
4. Write `results.json` summarizing what was produced
5. Exit 0 on success, non-zero on failure

If your runner uses different CLI args, edit `_ExternalScriptBackend.submit_panel()` in `higgsfield_runner.py` lines ~270-285. The 4 lines you'd change:

```python
cmd = [
    sys.executable,
    self.runner_script,
    "--panels", str(panels_path),
    "--output", str(results_path),
]
```

### panels.json schema (wrapper writes this)

```json
{
  "folder_id": "abc-123",
  "panels": [
    {
      "panel_id": "p01-03",
      "prompt": "<the full composed prompt from next_panel.py>",
      "aspect": "3:4",
      "count": 4,
      "refs": [
        {"kind": "state_anchor", "path": "pages/panels/p01-02.png"},
        {"kind": "face_card", "path": "references/characters/kara/face.png"},
        {"kind": "env_anchor", "path": "pages/panels/p01-01.png"},
        {"kind": "lineup", "path": "references/muscle-size-lineup.png"}
      ]
    }
  ]
}
```

Refs are pre-filtered: no `note` entries (informational only), no `MISSING_*` entries (caught by runner_core before invoking your script).

### results.json schema (your runner writes this)

Two options — pick whichever matches your existing setup:

**Option 1**: write PNGs to `pages/panels/<panel_id>/v{N}.png` and an empty results.json. The wrapper will find them at the expected location.

**Option 2**: write paths in results.json:

```json
{
  "panels": [
    {
      "panel_id": "p01-03",
      "variant_paths": [
        "pages/panels/p01-03/v1.png",
        "pages/panels/p01-03/v2.png",
        "pages/panels/p01-03/v3.png",
        "pages/panels/p01-03/v4.png"
      ],
      "job_id": "higgsfield-abc-123"
    }
  ]
}
```

The wrapper checks both locations.

### Content-policy refusals

If Higgsfield refuses a prompt, your runner should:

- Exit with non-zero status AND
- Print the refusal text to stderr (the wrapper greps for "content policy", "safety", "violates")

The wrapper detects this and triggers `CONTENT_POLICY_REFUSAL` halt — runner_core writes the refusal text to state.json and stops cleanly.

---

## Mode B: `api` — direct HTTP via token_relay

Use this if you don't already have a working runner. The v4 `HiggsfieldApiBackend` talks to the Higgsfield API directly, fetching the auth token from your existing `token_relay.js`.

### Config

```json
{
  "higgsfield": {
    "mode": "api",
    "token_relay_url": "http://localhost:7878/token",
    "api_base": "https://higgsfield.ai/api/v1",
    "folder_id": "abc-123-folder-uuid",
    "default_ref_type": "nano_banana_2_job"
  }
}
```

### What needs to be true on the Mac Mini

1. Chrome running with `--remote-debugging-port=9222`
2. `token_bridge.js` injected into the Higgsfield tab (you already have this)
3. `token_relay.js` Node server running on `:7878` (or whatever port you set in `token_relay_url`)
4. The `token_relay.js` responds to `GET /token` with `{"token": "<bearer>"}` (or `{"authToken": ...}` or `{"access_token": ...}`)

If your `token_relay.js` uses a different response shape, edit `_fetch_token()` in `higgsfield_runner.py` lines ~85-95.

### What the API endpoints are

**WARNING**: Higgsfield doesn't publish their API spec. The endpoints used in `higgsfield_runner.py` are best-effort guesses based on what's observable in browser DevTools when using the site. They WILL drift as Higgsfield updates their API.

Endpoints used:

- `POST {api_base}/jobs` — submit a generation job
- `GET {api_base}/jobs/{job_id}` — poll for status
- `POST {api_base}/media` — upload a ref image, returns a URL
- `HEAD {api_base}/folders/{folder_id}` — health check

If these are wrong for the current Higgsfield API, the calls return 4xx and the runner halts with the response body in the error message. **Adjust the URLs in `higgsfield_runner.py` lines ~140-170 to match what's actually in flight in your browser**, then re-run.

### URL transformation rule (from L9)

Per your existing pipeline lessons: **ref URLs returned by Higgsfield must use `.png` not `_min.webp`**. The runner enforces this:

```python
url = url.replace("_min.webp", ".png")
```

Applied to both ref upload responses and result download URLs.

### Credits exhaustion

If Higgsfield returns HTTP 402 (Payment Required), the runner halts with `CREDITS_EXHAUSTED`. Top up your Higgsfield credits and re-run — state.json resumes from the last completed panel.

---

## Switching between modes

Just change `higgsfield.mode` in `production-config.json`. The runner_core handles both identically; the only difference is which backend class is instantiated. State.json format is identical, resume works across mode switches.

You might want to do this if:

- Your existing runner.py is mid-refactor — temporarily use `api` mode
- The `api` mode is hitting an undocumented endpoint change — temporarily switch to `external_script` while you debug

---

## Testing without burning credits

```bash
# Dry-run: connect to token_relay, do a HEAD on folders, exit
python higgsfield_runner.py --project <test-project> --dry-run
```

Prints `health check: OK` or `health check: FAIL` plus a useful message. Costs zero credits, takes <2 seconds.

For a full integration test with one panel, create a minimal project:

```bash
mkdir -p ~/Desktop/claude/hf-smoketest
cd ~/Desktop/claude/hf-smoketest
# Write a 1-panel shotlist.json + production-config.json with platform=higgsfield
# Place needed reference PNGs in references/
python ~/.claude/skills/comic-production/scripts/runners/higgsfield_runner.py \
    --project .
```

The runner generates one panel, picks a variant, writes state.json. Inspect `pages/panels/p01-01.png` to confirm output. Cost: ~1 Higgsfield credit + ~$0.02 in Anthropic API calls (or $0 if you set `generation.variant_picker = "heuristic"`).
