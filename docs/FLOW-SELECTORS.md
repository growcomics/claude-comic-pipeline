# Flow Selectors — Maintenance Guide

Google Labs Flow is in active development. Selectors change. When the Flow runner breaks because of a UI change, the fix lives in **one file**: `runners/flow_selectors.py`.

This doc tells you how to update it.

## Symptoms of a selector mismatch

The runner halts with one of:

- `Prompt textarea not found. flow_selectors.PROMPT_TEXTAREA_SELECTORS may be out of date.`
- `'Add ingredient' button not found. flow_selectors.ADD_INGREDIENT_BUTTON_SELECTORS may be out of date.`
- `Generate button not found. flow_selectors.GENERATE_BUTTON_SELECTORS may be out of date.`
- `Variant grid not found (got 0 images, expected 4)`

Any of these means a selector list in `flow_selectors.py` no longer matches what Flow renders.

## Updating procedure

1. **Open Flow in Chrome** (the same Chrome running with `--remote-debugging-port=9222`)
2. **Sign in if needed**, navigate to `labs.google/fx/tools/flow`
3. **Open DevTools** (Cmd+Opt+I on Mac, F12 on others)
4. **Click the broken element** in the page (the prompt textarea, Add ingredient button, etc.)
5. **Right-click in DevTools → Copy → Copy selector** — but DO NOT use this directly. The class-based selector Chrome gives you will break the next time Flow re-renders.
6. **Find a stable attribute** on the element instead. Preference order:

| Attribute type | Stability | Example |
|---|---|---|
| `aria-label` | High | `role=textbox[name=/prompt/i]` |
| `data-testid` | High | `[data-testid="prompt-input"]` |
| `role` + visible text | Medium-high | `role=button[name=/^Generate$/i]` |
| Visible text only | Medium | `text=/^Generate$/i` |
| `placeholder` | Medium | `textarea[placeholder*="describe" i]` |
| CSS class (auto-generated like `.css-xyz123`) | LOW — avoid | Don't use |

7. **Add the new selector** to the matching list in `flow_selectors.py`. Keep the existing entries too — multiple fallbacks is fine, the runner tries them in order:

```python
PROMPT_TEXTAREA_SELECTORS = [
    'role=textbox[name=/prompt/i]',
    '[data-testid="prompt-input"]',     # ← new one you added
    'role=textbox[name=/describe/i]',
    # ... existing fallbacks
]
```

8. **Test the fix**:
```bash
python flow_runner.py --project <test-project> --dry-run
```
The health check should pass. Then run a one-panel project to confirm:
```bash
python flow_runner.py --project <test-project>
```

## Element catalog

These are the elements the runner needs to find, in order of use:

| Element | Selector list | Notes |
|---|---|---|
| Sign-in indicator | `SIGN_IN_REQUIRED_INDICATOR_SELECTORS` | If visible, runner halts with `AUTH_EXPIRED` |
| Signed-in indicator | `SIGNED_IN_INDICATOR_SELECTORS` | Presence confirms Flow is loaded and authed |
| Image mode | `IMAGE_MODE_BUTTON_SELECTORS` | Flow has Image/Video tabs; we need Image |
| Aspect picker | `ASPECT_PICKER_BUTTON_SELECTORS` | Opens the aspect ratio submenu |
| Aspect options | `ASPECT_OPTIONS["3:4"]` etc. | Sub-menu items under the picker |
| Prompt textarea | `PROMPT_TEXTAREA_SELECTORS` | Where the runner types the composed prompt |
| Add ingredient | `ADD_INGREDIENT_BUTTON_SELECTORS` | Triggers a file picker for each ref |
| Generate | `GENERATE_BUTTON_SELECTORS` | Submits the panel |
| Generating indicator | `GENERATING_INDICATOR_SELECTORS` | Optional — used only for status logging |
| Variant grid | `VARIANT_GRID_SELECTORS` | The 4 result images; runner reads img.src |
| Refusal banner | `REFUSAL_INDICATOR_SELECTORS` | If visible after Generate, halt with CONTENT_POLICY_REFUSAL |
| Error banner | `ERROR_INDICATOR_SELECTORS` | If visible, retry with backoff |

Each list is a "try these in order" set. The runner uses the first one that resolves to a visible element within the per-attempt timeout.

## A note on the "newline = submit" footgun

Flow treats `\n` in the prompt textarea as "submit" — pressing Enter while typing triggers generation. The runner protects against this:

```python
# in flow_runner.FlowBackend._set_prompt():
safe_prompt = " ".join(line.strip() for line in prompt.splitlines() if line.strip())
page.keyboard.type(safe_prompt, delay=2)
```

Multi-line prompts from `next_panel.py` get joined with spaces before typing. Don't undo this — generation will fire on the first newline.

## Watching the runner work

For initial debugging:

```bash
python flow_runner.py --project <test-project> --verbose --max-panel-seconds 600 2>&1 | tee runner.log
```

`--verbose` enables debug logging. `2>&1 | tee runner.log` captures the full transcript including stack traces. If the runner halts mid-panel, the log shows exactly which selector list failed.

You can also watch the browser visually if Chrome's window is visible — Playwright operates the user's existing Chrome, so every click and type is observable in real time. Useful for spotting UI changes.

## When Google does a major Flow redesign

Bigger redesigns (like Whisk merging into Flow in Feb 2026) can break many selectors at once. The right move:

1. Don't try to fix everything in one session
2. Update `flow_selectors.py` element-by-element, testing after each
3. Start with `SIGNED_IN_INDICATOR_SELECTORS` and `PROMPT_TEXTAREA_SELECTORS` — those gate everything else
4. Then `ADD_INGREDIENT_BUTTON_SELECTORS` and `GENERATE_BUTTON_SELECTORS`
5. Last: `ASPECT_OPTIONS` and `VARIANT_GRID_SELECTORS`
6. Each update: `--dry-run` first, then one-panel test, then commit

The runner is designed for this incremental update cycle. Multi-fallback selector lists mean a partial fix usually works — old selectors still match the cases that haven't changed, new ones handle what has.

## Filing a bug if a runner failure ISN'T a selector issue

If the selectors all match but generation still fails (variants don't appear, downloads fail, etc.), it's a runner bug, not a selector bug. Capture:

1. `runner.log` from a `--verbose` run
2. A screenshot of the Flow page at the moment of failure
3. The exact `production-config.json` and the panel ID where it broke

Then check `_wait_for_results` and `_capture_variants` in `flow_runner.py` — those are the two places where logic (not selectors) is doing the work.
