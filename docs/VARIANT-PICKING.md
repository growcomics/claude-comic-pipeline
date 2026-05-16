# Variant Picking — Preserving Quality Without an Interactive Claude

When Claude Code drives panel generation manually, it visually inspects 4 variants per panel and picks the best one. The criteria are in `shotlist-driven-flow.md` step 6: face acting, anatomy, CGI fidelity, camera adherence, reference adherence, composition.

The runner can't open a UI to inspect images. So how does it pick variants without sacrificing quality? Three strategies, configured via `production-config.json -> generation.variant_picker`:

## Strategy 1: `claude_api` (DEFAULT, RECOMMENDED)

Calls the Anthropic Messages API directly with the 4 variant images and the panel plan as input. Claude returns a JSON object with the picked variant index, reason, and concerns. This preserves the exact same picking quality as interactive Claude Code — with zero risk of mid-pipeline user prompts (API calls don't have `AskUserQuestion`).

```python
response = anthropic.Anthropic().messages.create(
    model="claude-opus-4-7",
    max_tokens=600,
    system=<system prompt with picking criteria per transformation_type>,
    messages=[{
        "role": "user",
        "content": [
            {"type": "image", "source": {"type": "base64", ...}},  # variant 1
            {"type": "text", "text": "Variant 1"},
            {"type": "image", "source": {"type": "base64", ...}},  # variant 2
            {"type": "text", "text": "Variant 2"},
            # ... variants 3 and 4
            {"type": "text", "text": "<panel context + JSON output instruction>"}
        ]
    }]
)
# Parse response.content[0].text as JSON
```

### System prompt structure

The system prompt encodes the 6 criteria in strict priority order, with a transformation-type-specific section for criterion #5 (reference adherence). The picker reads `production-config.json -> transformation_type` and injects the matching block:

- `fmg`: muscle size matches lineup tier, natural skin tone, breasts scale with muscle
- `be`: breast size matches tier, hourglass figure, round shape, cleavage at tier 2+
- `glute`: hip-to-waist ratio matches tier, rounded full glute, thigh proportion balanced
- `mmg`: muscle size matches lineup tier, **male anatomy only — no breasts, no hourglass**
- `mixed`: identify active growth stage for this panel, evaluate against that stage's tier

Each transformation type has its own version of the prompt so the picker enforces the right anatomy invariants. **This is critical for continuity** — without per-type prompts, an MMG comic could see the picker prefer a feminized variant, breaking the entire arc.

### Output schema

The picker is constrained to output JSON:

```json
{
  "picked": 3,
  "reason": "best face acting; V1 had flat expression, V2 missed the requested wide-establish camera, V4 drifted to 2D",
  "concerns": ["V3 has minor shadow noise on left arm"],
  "all_bad": false
}
```

`all_bad` is the escape hatch: when ALL four variants fail badly enough that none is usable (all drifted to 2D, all have anatomy issues), the picker sets `all_bad: true`. The runner then applies the `on_all_bad` policy:

- `halt` — stop and surface to user
- `retry-with-cgi-anchor-boost` (default) — retry the panel, runner adds emphasis to the CGI/photoreal anchors in the next attempt
- `skip-with-flag` — accept the least-bad variant but mark it FLAGGED in state.json for later review

`all_bad` is rare. Usually one variant is acceptable even if none is perfect.

### Cost

Claude Opus 4.7 at the default settings: ~$0.02 per panel pick. For a 30-page comic at ~150 panels, total picker cost is ~$3 — far less than the time savings of unattended generation.

To use a cheaper model, set `CLAUDE_VARIANT_MODEL=claude-sonnet-4-6` in the environment. Sonnet is roughly 5x cheaper but slightly less reliable on the "all_bad" determination.

### Failure modes and fallbacks

| Failure | What the runner does |
|---|---|
| `ANTHROPIC_API_KEY` not set | Falls back to `heuristic` automatically, logs warning |
| `anthropic` package not installed | Falls back to `heuristic`, logs warning |
| API rate limit (429) | Exponential backoff, 3 retries |
| API returns malformed JSON | Logs raw response, retries; after 3 attempts halts the panel |
| API returns `picked` outside 1-N range | Halts the panel with descriptive error |
| Persistent API outage | After 3 attempts, halt with `MAX_RETRIES_EXCEEDED` — re-run later |

The picker never silently corrupts state — every failure either retries or halts cleanly.

## Strategy 2: `heuristic` (free, no quality guarantee)

No API call. Picks by:

1. Skip any variant that's missing on disk or 0 bytes
2. Skip variants that are byte-identical duplicates of another (md5 match)
3. Pick the largest remaining variant by file size

The largest-file heuristic works because: at fixed PNG dimensions, more visual detail → more bytes. Bland or 2D-drifted variants compress smaller; richly detailed photoreal variants compress larger. Empirically picks the "best" variant ~55-65% of the time on the user's existing comic projects. Not enough for production but useful as a free fallback when the API picker is down.

Use cases:
- API outage / rate limit emergency
- Cost-sensitive runs where ~30-50% picks need post-hoc review anyway
- Smoke tests where any variant is fine

## Strategy 3: `first` (always picks variant 1)

Trivial. Picks variant 1 always. Used in tests where the picker logic isn't being exercised. Quality depends entirely on whether Flow/Higgsfield's variant 1 happens to be the best — which it isn't, with high probability.

Not recommended for production. Listed for completeness.

## Why three strategies and not just claude_api?

Defense in depth. The `claude_api` strategy is the default and the right answer 99% of the time. The other two exist so a transient API issue doesn't stall an entire overnight generation run — the picker falls back automatically, the runner continues, the user reviews flagged panels in the morning. Robustness over single-path purity.

## Side notes

- The picker calls the API **once per panel**. For a 150-panel run, that's 150 calls — well within rate limits.
- All variants are base64-encoded in the request. There's no upload step. The API call is stateless.
- The picker never modifies the variants themselves — it only picks one. The other 3 stay on disk at `pages/panels/<panel_id>/v{N}.png` so the user can inspect/swap-in later.
- The picked variant is copied to the canonical `pages/panels/<panel_id>.png` location — that's where `next_panel.py` looks for accepted history when picking chain anchors for subsequent panels.

## Testing the picker without spending API credits

```bash
# Heuristic mode — no API calls, no spend
python variant_picker.py \
    --project ~/Desktop/claude/test-project \
    --panel-id p01-01 \
    --strategy heuristic

# Same but with claude_api — uses real API, costs ~$0.02
ANTHROPIC_API_KEY=sk-ant-... python variant_picker.py \
    --project ~/Desktop/claude/test-project \
    --panel-id p01-01 \
    --strategy claude_api
```

The CLI uses a stub panel plan; for production-quality picking, the runner builds a real plan from `next_panel.py --as-json`.
