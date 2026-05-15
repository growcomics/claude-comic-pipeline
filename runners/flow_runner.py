#!/usr/bin/env python3
"""flow_runner.py — drive Google Labs Flow for unattended panel generation.

Connects to an existing Chrome instance via CDP (Chrome DevTools Protocol)
at http://localhost:9222. The user must launch Chrome with that flag and
sign into their Google account before running this script. This setup is
already standard in the user's pipeline.

The runner does NOT launch its own Chrome. That would lose the user's signed-
in session. We attach to the existing Chrome, find or open a Flow tab, and
drive it via Playwright Python.

Per-panel loop:
  1. Get the next pending panel via next_panel.py --as-json
  2. Open or focus the Flow project tab
  3. Paste the composed prompt
  4. Set aspect ratio to plan['aspect']
  5. Set image-generation count to 4
  6. Attach each ref in plan['refs_to_attach_in_order']
  7. Click Generate, wait for 4 variants
  8. Download each variant as v1.png..v4.png
  9. Call variant_picker to pick the best
 10. Copy picked variant to pages/panels/<panel_id>.png
 11. Commit state.json
 12. Loop

Halt conditions: documented in runner_core.HaltReason. Most failures are
retried with exponential backoff; only the documented halts stop the run.

Selectors for Flow's UI live in flow_selectors.py — that file is the seam
for adapting when Google changes things.
"""

from __future__ import annotations

import argparse
import logging
import shutil
import sys
import time
import traceback
from pathlib import Path
from typing import Iterable

# Local imports
sys.path.insert(0, str(Path(__file__).resolve().parent))
import flow_selectors as sel
from runner_core import (
    GenerationResult,
    HaltReason,
    RunOptions,
    RunnerBackend,
    add_common_args,
    load_config,
    log_status,
    resolve_next_panel_script,
    run,
    setup_logging,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Selector helpers — try a list in order, return the first that matches


def try_locators(page, selectors: Iterable[str], timeout_ms: int = 5000):
    """Try each selector. Return the first that resolves to a visible element,
    or None if none match within timeout_ms total (split across attempts)."""
    per_attempt = max(500, timeout_ms // max(1, len(list(selectors))))
    selectors = list(selectors)  # re-iterate
    for sel_str in selectors:
        try:
            loc = page.locator(sel_str).first
            loc.wait_for(state="visible", timeout=per_attempt)
            return loc
        except Exception:
            continue
    return None


def is_any_visible(page, selectors: Iterable[str], timeout_ms: int = 2000) -> bool:
    return try_locators(page, selectors, timeout_ms) is not None


# ---------------------------------------------------------------------------
# Flow backend


class FlowBackend(RunnerBackend):
    def __init__(self, cdp_url: str = "http://localhost:9222"):
        self.cdp_url = cdp_url
        self._pw = None
        self._browser = None
        self._page = None
        # Persistent set of edit-IDs the runner has already consumed for some
        # earlier panel. Cross-panel filter so a leftover-in-DOM generation
        # from p01-01 doesn't get re-captured as p01-02's content.
        self._processed_edit_ids: set[str] = set()

    def _ensure_browser(self):
        if self._page is not None:
            return
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as e:
            raise RuntimeError(
                "playwright not installed. Run: pip install playwright && "
                "playwright install chromium"
            ) from e

        log_status(f"Connecting to Chrome at {self.cdp_url}")
        self._pw = sync_playwright().start()
        try:
            self._browser = self._pw.chromium.connect_over_cdp(self.cdp_url)
        except Exception as e:
            raise RuntimeError(
                f"Cannot connect to Chrome at {self.cdp_url}. "
                "Is Chrome running with --remote-debugging-port=9222? "
                f"Underlying error: {e}"
            )

        # Find an existing Flow tab, or open one
        for ctx in self._browser.contexts:
            for pg in ctx.pages:
                url = pg.url or ""
                if any(p in url for p in sel.FLOW_URL_PATTERNS):
                    self._page = pg
                    log_status(f"Attached to existing Flow tab: {url}")
                    return

        # No existing Flow tab — open one in the first context
        if not self._browser.contexts:
            raise RuntimeError(
                "Chrome has no browser contexts. This is unusual; restart Chrome."
            )
        ctx = self._browser.contexts[0]
        self._page = ctx.new_page()
        log_status(f"Opening {sel.FLOW_URL}")
        self._page.goto(sel.FLOW_URL, wait_until="domcontentloaded", timeout=sel.TIMEOUT_PAGE_LOAD * 1000)

    def check_health(self) -> tuple[bool, str]:
        try:
            self._ensure_browser()
        except Exception as e:
            return False, str(e)

        page = self._page
        # Wait for page to settle, then check sign-in state
        try:
            page.wait_for_load_state("networkidle", timeout=sel.TIMEOUT_PAGE_LOAD * 1000)
        except Exception:
            pass  # don't fail health check on slow loads

        if is_any_visible(page, sel.SIGN_IN_REQUIRED_INDICATOR_SELECTORS, 2000):
            return False, (
                "Flow shows a sign-in prompt. Sign into your Google account in Chrome, "
                "then re-run the runner. (The runner does not handle Google OAuth — "
                "this preserves your security posture; tokens stay in your browser.)"
            )

        if not is_any_visible(page, sel.SIGNED_IN_INDICATOR_SELECTORS, 5000):
            return False, (
                "Flow UI not detected. Either Flow is loading slowly, or selectors are "
                "out of date in flow_selectors.py. Check that " + sel.FLOW_URL + " "
                "is accessible in your Chrome and update flow_selectors.py if Google "
                "has changed the UI."
            )

        return True, f"Flow ready at {page.url}"

    def close(self) -> None:
        # Do NOT close the browser — it's the user's Chrome, we just disconnect
        try:
            if self._browser:
                self._browser.close()  # this disconnects from CDP, doesn't kill Chrome
        except Exception:
            pass
        try:
            if self._pw:
                self._pw.stop()
        except Exception:
            pass
        self._page = None
        self._browser = None
        self._pw = None

    def submit_panel(
        self, plan: dict, project_root: Path, count: int, timeout_s: int
    ) -> GenerationResult:
        self._ensure_browser()
        page = self._page
        panel = plan["next_panel"]
        panel_id = panel.get("panel_id", "unknown")
        aspect = plan.get("aspect", "3:4")
        prompt = plan.get("composed_prompt", "")

        if not prompt:
            raise RuntimeError(f"empty composed_prompt for panel {panel_id}")

        # Make sure we have a fresh prompt area (Flow tends to clear after each
        # generation, but new projects sometimes carry state)
        log_status(f"Panel {panel_id}: preparing Flow UI")

        # 0. Ensure we're on the project root URL, NOT an /edit/<id> view (which
        # has no prompt area). Strip /edit/<UUID> and reload if needed.
        import re as _re
        cur_url = page.url or ""
        if "/edit/" in cur_url:
            project_url = _re.sub(r"/edit/[a-f0-9-]+/?$", "", cur_url)
            logger.info("panel %s: stripping /edit/ from URL → %s", panel_id, project_url)
            page.goto(project_url, wait_until="domcontentloaded")
            time.sleep(2.0)

        # 1. Ensure we're on Image mode (not Video)
        self._select_image_mode(page)

        # 2. Set count to 4 (or `count`)
        # Flow's default is 4 so we usually skip — but verify if visible
        # (skipped for now; relying on Flow default)

        # 3. Set aspect ratio
        self._set_aspect_ratio(page, aspect)

        # 4. Clear and paste prompt
        self._set_prompt(page, prompt)

        # 5. Attach refs in order. Skip "note" and "MISSING_*" entries.
        ref_count = self._attach_refs(
            page, project_root, plan.get("refs_to_attach_in_order", []) or []
        )
        log_status(f"Panel {panel_id}: attached {ref_count} refs")

        # 6. Capture (a) the FULL set of currently-visible edit-IDs and (b) the
        # topmost (newest) edit-ID. Both are used as filters post-click:
        #   - persistent self._processed_edit_ids: stuff this run already saved
        #     for earlier panels; never re-capture
        #   - baseline_now: stuff visible right before THIS click (catches
        #     anything previously off-screen but not yet generated)
        #   - boundary_edit_id: anchor for "is this above the click?" — used
        #     to drop lazy-loaded OLDER entries that appear below the top
        # All three together ensure the new edit-IDs we capture are exactly
        # the ones produced by THIS click.
        #
        # Scroll the gallery DOWN aggressively to force lazy-load of all
        # currently-existing entries — otherwise lazy-loaded olds appear
        # post-click and look "new". Then scroll back to top so the new gen
        # (which lands at the top) is in viewport.
        for _ in range(5):
            page.evaluate("window.scrollBy(0, window.innerHeight * 1.5)")
            time.sleep(0.4)
        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(0.6)
        ordered_pre = self._get_edit_ids_ordered(page)
        baseline_now = set(ordered_pre)
        boundary_edit_id = ordered_pre[0] if ordered_pre else None
        logger.info(
            "panel %s: pre-click — baseline=%d, boundary=%s, processed=%d",
            panel_id, len(baseline_now),
            (boundary_edit_id or "<none>")[:8],
            len(self._processed_edit_ids),
        )

        # 7. Generate
        self._click_generate(page)
        log_status(f"Panel {panel_id}: generation started, waiting for new generations...")

        # 8. Wait for new edit-IDs (above boundary AND not in baseline AND not
        # already processed)
        new_edit_ids, refusal_text = self._wait_for_new_generations(
            page, timeout_s, boundary_edit_id, baseline_now,
            expected_count=count,
        )
        if refusal_text:
            return GenerationResult(
                variant_paths=[], raw_metadata={}, refusal=True,
                refusal_reason=refusal_text,
            )
        if not new_edit_ids:
            raise RuntimeError(f"Generation produced no new edit-IDs for {panel_id}")

        log_status(
            f"Panel {panel_id}: {len(new_edit_ids)} new generation(s) detected; downloading"
        )

        # 9. Download each new generation's preview image as v{N}.png
        variant_paths = self._download_new_generations(
            page, project_root, panel_id, new_edit_ids, max_count=count,
        )
        if len(variant_paths) == 0:
            raise RuntimeError(f"No variants captured for {panel_id}")

        # 10. Persist these edit-IDs in the cross-panel filter so the next
        # panel can't re-capture them as "new" if they're still in DOM.
        self._processed_edit_ids.update(new_edit_ids[:len(variant_paths)])

        return GenerationResult(
            variant_paths=variant_paths,
            raw_metadata={"flow_url": page.url},
            refusal=False,
        )

    # ----- UI driver helpers -----

    def _select_image_mode(self, page) -> None:
        """If Flow is showing a Video/Image toggle, click Image."""
        # Only click if explicitly on video mode — Flow usually defaults right
        # Best-effort, don't fail
        loc = try_locators(page, sel.IMAGE_MODE_BUTTON_SELECTORS, 2000)
        if loc:
            try:
                loc.click()
                time.sleep(0.5)
            except Exception:
                pass

    def _set_aspect_ratio(self, page, aspect: str) -> None:
        options = sel.ASPECT_OPTIONS.get(aspect)
        if not options:
            logger.warning("no aspect-ratio mapping for %s, using Flow default", aspect)
            return
        # Open picker
        picker = try_locators(page, sel.ASPECT_PICKER_BUTTON_SELECTORS, 3000)
        if not picker:
            logger.warning("aspect-ratio picker not found, using Flow default")
            return
        try:
            picker.click()
            time.sleep(0.3)
        except Exception as e:
            logger.warning("clicking aspect picker failed (%s), using default", e)
            return
        # Click the right option
        opt = try_locators(page, options, 3000)
        if opt:
            try:
                opt.click()
            except Exception:
                pass
        time.sleep(0.3)

    def _set_prompt(self, page, prompt: str) -> None:
        textarea = try_locators(page, sel.PROMPT_TEXTAREA_SELECTORS, sel.TIMEOUT_ELEMENT_VISIBLE * 1000)
        if not textarea:
            raise RuntimeError(
                "Prompt textarea not found. flow_selectors.PROMPT_TEXTAREA_SELECTORS "
                "may be out of date."
            )
        # Click into it, select all, type. Avoid newlines — Flow treats \n as submit.
        textarea.click()
        try:
            page.keyboard.press("Control+A")
        except Exception:
            page.keyboard.press("Meta+A")
        page.keyboard.press("Delete")
        # Flow treats \n as Enter (submits) — replace any newlines with periods + space
        safe_prompt = " ".join(line.strip() for line in prompt.splitlines() if line.strip())
        page.keyboard.type(safe_prompt, delay=2)
        time.sleep(0.5)

    def _attach_refs(self, page, project_root: Path, refs: list[dict]) -> int:
        """Attach each ref. Returns the count of refs successfully attached.

        Strategy: find the file input directly (input[type=file]) and use
        set_input_files. This is the most robust way — bypasses any drag-drop
        or modal-clicking complexity.
        """
        attached = 0
        for ref in refs:
            kind = ref.get("kind", "")
            # Check MISSING_ FIRST — its path is None so the noop-continue below
            # would otherwise mask it.
            if kind.startswith("MISSING_"):
                raise RuntimeError(f"unexpected MISSING_ ref reached submit: {ref}")
            if kind == "note" or not ref.get("path"):
                continue  # informational, no file
            path = ref["path"]
            abs_path = (project_root / path).resolve()
            if not abs_path.is_file():
                raise RuntimeError(
                    f"ref file not found on disk: {abs_path} (ref kind={kind})"
                )

            # May 2026: Flow no longer triggers a native file chooser when the
            # ADD button is clicked — it opens a custom asset-picker modal.
            # Instead, target the hidden <input type="file" accept="image/*"
            # multiple> directly and feed it via set_input_files. This bypasses
            # the modal entirely and matches Flow's own JS upload path.
            file_input = page.locator('input[type="file"][accept*="image"]').first
            try:
                file_input.set_input_files(str(abs_path), timeout=10000)
            except Exception as e:
                # Fall back to the legacy ADD-button + file-chooser route.
                add_btn = try_locators(page, sel.ADD_INGREDIENT_BUTTON_SELECTORS, 5000)
                if not add_btn:
                    raise RuntimeError(
                        f"hidden file input not usable ({e}); 'Add ingredient' "
                        "button also not found. flow_selectors may be out of date."
                    )
                with page.expect_file_chooser(timeout=10000) as fc_info:
                    add_btn.click()
                file_chooser = fc_info.value
                file_chooser.set_files(str(abs_path))
            attached += 1
            # Wait for the ref to appear in the prompt before adding the next
            time.sleep(1.5)

        return attached

    def _click_generate(self, page) -> None:
        btn = try_locators(page, sel.GENERATE_BUTTON_SELECTORS, sel.TIMEOUT_ELEMENT_VISIBLE * 1000)
        if not btn:
            raise RuntimeError(
                "Generate button not found. flow_selectors.GENERATE_BUTTON_SELECTORS "
                "may be out of date."
            )
        btn.click()

    # ----- Edit-ID-based generation tracking (May 14 2026 Flow UI) -----
    #
    # Flow's project view shows ONE preview image per past generation, wrapped
    # in <a href="/.../edit/<EDIT-ID>">. New generations get new edit-IDs.
    # We track these IDs to identify exactly the new generations from a click.

    _EDIT_ID_JS = """
    () => [...new Set(
        [...document.querySelectorAll('a[href*="/edit/"]')]
            .map(a => {
                const m = a.href.match(/\\/edit\\/([a-f0-9-]+)/);
                return m ? m[1] : null;
            })
            .filter(Boolean)
    )]
    """

    def _get_edit_ids_ordered(self, page) -> list[str]:
        """Return /edit/<UUID> hrefs in DOM order (newest first per Flow's
        project gallery convention, verified May 14 2026)."""
        try:
            return page.evaluate(self._EDIT_ID_JS)
        except Exception as e:
            logger.warning("edit-id read failed: %s", e)
            return []

    def _get_top_edit_id(self, page) -> str | None:
        """Return the topmost (newest) edit-ID, or None if the gallery is empty."""
        ids = self._get_edit_ids_ordered(page)
        return ids[0] if ids else None

    def _wait_for_new_generations(
        self,
        page,
        timeout_s: int,
        boundary_edit_id: str | None,
        baseline_now: set[str],
        expected_count: int,
    ) -> tuple[list[str], str | None]:
        """Wait until edit-IDs appear that are: (a) ABOVE the boundary in DOM
        order, (b) NOT in `baseline_now` (the full visible set at click time),
        (c) NOT in `self._processed_edit_ids` (cross-panel filter).

        Returns (new_edit_ids_in_dom_order_newest_first, refusal_text_or_None).

        On content-policy refusal returns ([], "<refusal text>").
        On timeout raises RuntimeError so runner_core's retry kicks in.
        """
        deadline = time.time() + timeout_s

        # Watch for an immediate refusal banner
        refusal_check_until = time.time() + 10
        while time.time() < refusal_check_until:
            refusal = try_locators(page, sel.REFUSAL_INDICATOR_SELECTORS, 500)
            if refusal:
                try:
                    return [], (refusal.text_content() or "content-policy refusal").strip()
                except Exception:
                    return [], "content-policy refusal (text not readable)"
            time.sleep(0.5)

        def _filter_new(ordered: list[str]) -> list[str]:
            """Contiguous-from-top filter: collect new edit-IDs starting from
            DOM position 0 (newest) and BREAK on the first one that is either
            the boundary, in baseline, or already processed.

            This is stricter than skip-and-continue: if an old/lazy-loaded
            entry appears above a truly-new one, we stop early and miss the
            new one — but we never capture an old one as "new". Better to
            occasionally lose a true positive than to repeatedly accept false
            positives (which silently corrupt panel content).
            """
            out = []
            for eid in ordered:
                if (
                    (boundary_edit_id is not None and eid == boundary_edit_id)
                    or eid in baseline_now
                    or eid in self._processed_edit_ids
                ):
                    break
                out.append(eid)
            return out

        # Poll for filtered new edit-IDs
        while time.time() < deadline:
            refusal = try_locators(page, sel.REFUSAL_INDICATOR_SELECTORS, 200)
            if refusal:
                try:
                    return [], (refusal.text_content() or "content-policy refusal").strip()
                except Exception:
                    return [], "content-policy refusal"

            err = try_locators(page, sel.ERROR_INDICATOR_SELECTORS, 200)
            if err:
                try:
                    text = err.text_content() or ""
                    raise RuntimeError(f"Flow error banner: {text.strip()[:200]}")
                except RuntimeError:
                    raise
                except Exception:
                    pass

            ordered = self._get_edit_ids_ordered(page)
            new_ordered = _filter_new(ordered)
            if new_ordered:
                # Give Flow a moment to finish populating sibling generations
                # (xN mode lands generations staggered)
                time.sleep(3)
                ordered = self._get_edit_ids_ordered(page)
                new_ordered = _filter_new(ordered)
                return new_ordered[:max(expected_count, 1)], None

            time.sleep(1.0)

        raise RuntimeError(
            f"Timeout waiting for new Flow generation after {timeout_s}s "
            f"(boundary edit_id={boundary_edit_id or '<none>'}, "
            f"baseline_now={len(baseline_now)}, processed={len(self._processed_edit_ids)})"
        )

    def _download_new_generations(
        self,
        page,
        project_root: Path,
        panel_id: str,
        new_edit_ids: list[str],
        max_count: int,
    ) -> list[Path]:
        """For each new edit-ID, find its preview img.src on the project page
        and download it as v{N}.png in pages/panels/<panel_id>/."""
        out_dir = project_root / "pages" / "panels" / panel_id
        out_dir.mkdir(parents=True, exist_ok=True)

        # Map edit_id -> img src by inspecting <a href*="/edit/<id>"> > img.
        # Read inside the page so DOM updates are seen atomically.
        srcs_by_id: dict = page.evaluate("""
        () => {
            const out = {};
            for (const a of document.querySelectorAll('a[href*="/edit/"]')) {
                const m = a.href.match(/\\/edit\\/([a-f0-9-]+)/);
                if (!m) continue;
                const img = a.querySelector('img');
                if (img) out[m[1]] = img.getAttribute('src') || img.src || '';
            }
            return out;
        }
        """)

        # If any expected edit-id is missing a src (img not yet loaded), wait
        # briefly and re-poll up to 3 times.
        for _ in range(3):
            missing = [eid for eid in new_edit_ids if not srcs_by_id.get(eid)]
            if not missing:
                break
            time.sleep(2)
            srcs_by_id = page.evaluate("""
            () => {
                const out = {};
                for (const a of document.querySelectorAll('a[href*="/edit/"]')) {
                    const m = a.href.match(/\\/edit\\/([a-f0-9-]+)/);
                    if (!m) continue;
                    const img = a.querySelector('img');
                    if (img) out[m[1]] = img.getAttribute('src') || img.src || '';
                }
                return out;
            }
            """)

        request = page.context.request
        saved: list[Path] = []
        for i, eid in enumerate(new_edit_ids[:max_count], start=1):
            src = srcs_by_id.get(eid)
            if not src:
                logger.warning(
                    "no img.src found for new edit_id %s (img not loaded yet?)",
                    eid,
                )
                continue
            if not src.startswith("http"):
                src = f"https://labs.google{src}"
            try:
                resp = request.get(
                    src, timeout=sel.TIMEOUT_VARIANT_DOWNLOAD * 1000,
                )
                if resp.status >= 400:
                    logger.warning(
                        "download HTTP %s for edit_id %s — skipping",
                        resp.status, eid,
                    )
                    continue
                out = out_dir / f"v{i}.png"
                out.write_bytes(resp.body())
                saved.append(out)
            except Exception as e:
                logger.warning(
                    "download failed for edit_id %s (%s) — skipping", eid, e,
                )
                continue

        return saved


# ---------------------------------------------------------------------------
# CLI


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Drive Google Labs Flow for unattended comic panel generation."
    )
    add_common_args(parser)
    parser.add_argument(
        "--cdp-url",
        default="http://localhost:9222",
        help="Chrome DevTools Protocol URL (default: http://localhost:9222)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Connect to Chrome and check health, but don't submit anything.",
    )
    args = parser.parse_args()

    project_root = Path(args.project).resolve()
    if not project_root.is_dir():
        print(f"error: project root does not exist: {project_root}", file=sys.stderr)
        return 2

    setup_logging(project_root, args.log_file, args.verbose)

    try:
        config = load_config(project_root)
    except Exception as e:
        print(f"error loading config: {e}", file=sys.stderr)
        return 2

    if config.get("platform") not in ("flow", "hybrid"):
        log_status(
            f"WARNING: production-config.json -> platform = {config.get('platform')}; "
            "flow_runner expects 'flow' or 'hybrid'. Proceeding anyway."
        )

    backend = FlowBackend(cdp_url=args.cdp_url)

    if args.dry_run:
        ok, msg = backend.check_health()
        print(f"health check: {'OK' if ok else 'FAIL'} — {msg}")
        backend.close()
        return 0 if ok else 1

    opts = RunOptions(
        project_root=project_root,
        config=config,
        next_panel_script=resolve_next_panel_script(args.next_panel_script),
        backend=backend,
        max_panel_seconds=args.max_panel_seconds,
    )

    final_state = run(opts)

    if final_state.halt_reason:
        log_status(
            f"FINAL: halted — reason={final_state.halt_reason} "
            f"panel={final_state.halt_panel_id} detail={final_state.halt_detail[:200]}"
        )
        return 1

    log_status(
        f"FINAL: all panels accepted. "
        f"Total API cost: ${final_state.total_api_cost_usd:.4f}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
