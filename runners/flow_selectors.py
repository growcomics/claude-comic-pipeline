"""flow_selectors.py — Google Labs Flow UI element selectors.

Flow is in active development; Google can and does change selectors.
When the runner breaks because of a UI change, update THIS FILE.

Update process:
  1. Open Flow at labs.google/fx/tools/flow in Chrome
  2. Right-click the broken element, Inspect
  3. Copy a selector that's reasonably stable (prefer aria-label, data-testid,
     role+text over class names that look auto-generated)
  4. Replace the constant below
  5. Test with: python flow_runner.py --project <test> --dry-run

Each selector is a Playwright Locator expression. The runner tries multiple
fallback strategies for each element — class names break first, role+text
breaks less often, aria-label is most stable.

Last verified: 2026-05-14
"""

from __future__ import annotations

# Top-level page detection
FLOW_URL = "https://labs.google/fx/tools/flow"
FLOW_URL_PATTERNS = [
    "labs.google/fx/tools/flow",
    "labs.google/fx/tools/whisk",  # legacy fallback (Whisk merged into Flow)
]

# Authentication detection — is the user signed in?
SIGNED_IN_INDICATOR_SELECTORS = [
    'role=button[name=/Generate/i]',
    'role=textbox[name=/prompt/i]',
    'role=textbox[name=/describe/i]',
    # Fallback: presence of the "New project" or "Create" button
    'role=button[name=/new project/i]',
    'role=button[name=/create/i]',
]

SIGN_IN_REQUIRED_INDICATOR_SELECTORS = [
    'role=button[name=/sign in/i]',
    'role=link[name=/sign in/i]',
    'role=button[name=/log in/i]',
    'text=/please sign in/i',
]

# Project creation / opening
NEW_PROJECT_BUTTON_SELECTORS = [
    'role=button[name=/new project/i]',
    'role=button[name=/create new/i]',
    'role=link[name=/new project/i]',
    'text=/create new project/i',
]

# Prompt text area
PROMPT_TEXTAREA_SELECTORS = [
    'role=textbox[name=/prompt/i]',
    'role=textbox[name=/describe/i]',
    'role=textbox[name=/what do you want to create/i]',
    'textarea[placeholder*="describe" i]',
    'textarea[placeholder*="prompt" i]',
    'textarea[placeholder*="scene" i]',
]

# Model selector — we need to be on the image (Nano Banana / Imagen) model,
# not the video (Veo) model. Defaults change over time.
MODEL_PICKER_BUTTON_SELECTORS = [
    'role=button[name=/model/i]',
    'role=button[name=/nano banana/i]',
    'role=button[name=/imagen/i]',
    '[data-testid*="model" i]',
]

# Image mode (vs Video mode)
IMAGE_MODE_BUTTON_SELECTORS = [
    'role=button[name=/create image/i]',
    'role=button[name=/image/i]',
    'role=tab[name=/image/i]',
    'text=/^Image$/',
]

# Count picker — Flow generates 4 by default; we still verify
COUNT_PICKER_BUTTON_SELECTORS = [
    'role=button[name=/count/i]',
    'role=button[name=/number/i]',
    'role=button[name=/x4/i]',
    'role=button[name=/x1/i]',
]

# Aspect ratio picker
ASPECT_PICKER_BUTTON_SELECTORS = [
    'role=button[name=/aspect/i]',
    'role=button[name=/ratio/i]',
    '[data-testid*="aspect" i]',
]

# Aspect ratio options (sub-menu items after clicking the picker)
ASPECT_OPTIONS = {
    "1:1": ['role=menuitem[name=/1:1/]', 'role=button[name=/1:1/]', 'text=/^1:1$/'],
    "3:4": ['role=menuitem[name=/3:4/]', 'role=button[name=/3:4/]', 'text=/^3:4$/'],
    "4:3": ['role=menuitem[name=/4:3/]', 'role=button[name=/4:3/]', 'text=/^4:3$/'],
    "16:9": ['role=menuitem[name=/16:9/]', 'role=button[name=/16:9/]', 'text=/^16:9$/'],
    "9:16": ['role=menuitem[name=/9:16/]', 'role=button[name=/9:16/]', 'text=/^9:16$/'],
}

# Reference image attachment — Flow uses "ingredients" terminology
ADD_INGREDIENT_BUTTON_SELECTORS = [
    'role=button[name=/add ingredient/i]',
    'role=button[name=/add reference/i]',
    'role=button[name=/upload/i]',
    'role=button[name=/add image/i]',
    '[data-testid*="ingredient" i]',
    '[data-testid*="upload" i]',
]

# File input that appears after clicking "Add ingredient" (or accepts a drop)
FILE_INPUT_SELECTORS = [
    'input[type="file"]',
    'input[accept*="image"]',
]

# Generate button
GENERATE_BUTTON_SELECTORS = [
    'role=button[name=/^generate$/i]',
    'role=button[name=/^create$/i]',
    'role=button[name=/^run$/i]',
    'role=button[name=/^go$/i]',
]

# Generation-in-progress indicator (appears after clicking Generate)
GENERATING_INDICATOR_SELECTORS = [
    'role=progressbar',
    'text=/generating/i',
    'text=/creating/i',
    'text=/working/i',
    '[aria-live="polite"][aria-busy="true"]',
]

# Generated variants — appear as 4 image elements after generation completes
VARIANT_GRID_SELECTORS = [
    '[role="grid"] img',
    '[data-testid*="variant" i] img',
    '[data-testid*="result" i] img',
    '[aria-label*="generated image" i]',
]

# Per-variant download — Flow usually shows a download icon on hover or
# from a context menu. Easier path: read the img src and fetch directly.
# These selectors are fallbacks for cases where hotlinking img src doesn't work.
VARIANT_DOWNLOAD_BUTTON_SELECTORS = [
    'role=button[name=/download/i]',
    'role=menuitem[name=/download/i]',
    'role=button[name=/save/i]',
    'a[download]',
]

# Content-policy refusal — the textual response Flow shows when safety filter blocks
REFUSAL_INDICATOR_SELECTORS = [
    'text=/content (policy|safety|guidelines)/i',
    'text=/cannot generate/i',
    'text=/unable to (generate|create)/i',
    'text=/(violates|blocked|refused)/i',
    'role=alert',
]

# Error indicators (transient — retryable)
ERROR_INDICATOR_SELECTORS = [
    'text=/(error|failed|something went wrong)/i',
    'text=/try again/i',
    'role=alert[name=/error/i]',
]


# Timeouts (seconds)
TIMEOUT_PAGE_LOAD = 30
TIMEOUT_ELEMENT_VISIBLE = 15
TIMEOUT_GENERATION = 180  # max wait for 4 variants to appear
TIMEOUT_VARIANT_DOWNLOAD = 30
