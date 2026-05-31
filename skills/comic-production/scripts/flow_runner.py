#!/usr/bin/env python3
"""flow_runner.py — Playwright/CDP batch driver for Google Labs Flow.

This is the missing piece several projects' production-config.json complained
about ("Flow uploads can't be driven from this session and the flow_runner.py
isn't installed"). It drives `labs.google/fx/tools/flow` (Nano Banana 2)
deterministically over the Chrome DevTools Protocol, so a whole `shotlist.json`
can be produced panel-by-panel without hand-clicking the UI.

Design (intentional):

  * BRAINS ARE NOT DUPLICATED. All view-aware chaining (L1.5), ref selection
    (face card / env / lineup / tier reinforcement), aspect mapping, and prompt
    composition come from `next_panel.py --as-json`, which this script shells
    out to. flow_runner only does the MECHANICS: connect, set aspect/count,
    upload refs, type the prompt, submit, wait, download the x4 variants.

  * REFS ARE LOCAL FILES. Every ref next_panel.py emits is a path on disk (the
    state anchor is the prior accepted PNG; face/env/lineup are files). So we
    attach them through Flow's "Upload image" file input via Playwright's file
    chooser — deterministic, no flaky gallery hover/drag. This is the key reason
    a robust batch driver is possible at all.

  * CLAUDE PICKS THE VARIANT. After generating x4, the driver downloads all four
    to pages/panels/<panel_id>/v1..v4.png and STOPS, printing a JSON checkpoint.
    Claude looks at the four images, writes `_accepted.txt` naming the winner
    (or calls `accept`), then re-invokes — at which point next_panel.py sees the
    panel accepted and advances the chain. Retries are free and never advance
    the chain (matches references/shotlist-driven-flow.md exactly).

  * RESUME-SAFE. Progress lives on disk in the SAME convention next_panel.py
    already reads (pages/panels/<panel_id>/_accepted.txt). Re-running `next`
    always picks up the first pending panel. There is no separate state to
    corrupt.

Subcommands
-----------
  probe    Connect, find/open the Flow tab, and dump an accessibility snapshot
           + screenshot + candidate selectors to <project>/.flow/. Run this once
           on a new machine to calibrate selectors against the live DOM.
  next     Generate the next pending panel: compose via next_panel.py, drive the
           UI, download x4 variants, stop at the Claude-vision checkpoint.
  accept   Mark a panel's winning variant: writes _accepted.txt. Convenience for
           the checkpoint step (Claude can also just write the file directly).
  status   Print progress (accepted / remaining) via next_panel.py.

Quick start
-----------
  # 1. One-time: launch Chrome with the debugging port and sign into Flow.
  /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome \\
      --remote-debugging-port=9222

  # 2. One-time: install Playwright into an isolated venv (see flow_runner_README.md).

  # 3. Calibrate selectors once (writes <project>/.flow/probe-*.{json,png}).
  python flow_runner.py /path/to/project probe

  # 4. Per panel: generate, then let Claude pick.
  python flow_runner.py /path/to/project next
  #   -> downloads v1..v4, prints {"status":"awaiting_pick", ...}
  #   Claude reads the four PNGs, then:
  python flow_runner.py /path/to/project accept p03-02 v3
  #   ...loop back to `next`.

Selectors are NOT hardcoded into the logic. They live in a JSON config
(flow_selectors.json next to this script, overridable per-project at
<project>/.flow/selectors.json) so a UI change is a config edit, not a code
edit. `probe` exists to make that edit a 5-minute job.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
NEXT_PANEL = HERE / "next_panel.py"
DEFAULT_SELECTORS_PATH = HERE / "flow_selectors.json"

FLOW_URL = "https://labs.google/fx/tools/flow"
FLOW_URL_FRAGMENT = "labs.google/fx/tools/flow"


# ---------------------------------------------------------------------------
# Selector config — the only DOM-coupled knowledge in the tool.
#
# Each entry is an ORDERED list of strategies tried in turn until one resolves.
# A strategy is {"by": <kind>, "value": <str>, ["name": <str>]}. Supported
# kinds map onto Playwright locators:
#   role         -> page.get_by_role(value, name=name)        (name optional/regex)
#   placeholder  -> page.get_by_placeholder(value)
#   text         -> page.get_by_text(value, exact=False)
#   testid       -> page.get_by_test_id(value)
#   css          -> page.locator(value)
#   xpath        -> page.locator("xpath=" + value)
# This default set is derived from references/flow-workflow.md's documented UI.
# It is a STARTING POINT — run `probe` and tune <project>/.flow/selectors.json
# against the real page. The file-upload path (most important) is the least
# likely to drift because it keys off the OS file chooser, not a CSS class.
# ---------------------------------------------------------------------------
DEFAULT_SELECTORS = {
    "prompt_input": [
        {"by": "placeholder", "value": "What do you want to create?"},
        {"by": "role", "value": "textbox"},
        {"by": "css", "value": "textarea"},
        {"by": "css", "value": "div[contenteditable='true']"},
    ],
    "submit_button": [
        {"by": "role", "value": "button", "name": "(?i)^(generate|create|submit|send)$"},
        {"by": "css", "value": "button[aria-label*='enerate']"},
        {"by": "css", "value": "button[type='submit']"},
        # last resort: Enter in the prompt field (handled specially in code)
        {"by": "enter"},
    ],
    "settings_pill": [
        {"by": "role", "value": "button", "name": "(?i)nano banana"},
        {"by": "text", "value": "Nano Banana"},
        {"by": "css", "value": "button:has-text('Nano Banana')"},
    ],
    "add_ref_button": [
        {"by": "role", "value": "button", "name": "(?i)add|attach|reference|image"},
        {"by": "css", "value": "button[aria-label*='dd']"},
    ],
    # Within the asset picker / + menu, the control that reveals the OS file
    # chooser. We click this inside an expect_file_chooser() block.
    "upload_image": [
        {"by": "text", "value": "Upload image"},
        {"by": "role", "value": "button", "name": "(?i)upload"},
        {"by": "role", "value": "menuitem", "name": "(?i)upload"},
    ],
    # Direct hidden file input fallback (used if the picker isn't needed and
    # Flow exposes an <input type=file> we can set_input_files() straight away).
    "file_input": [
        {"by": "css", "value": "input[type='file']"},
    ],
    # Aspect-ratio option buttons inside the settings popup. {ASPECT} is
    # substituted with the target value, e.g. "3:4".
    "aspect_option": [
        {"by": "role", "value": "button", "name": "(?i)^{ASPECT}$"},
        {"by": "text", "value": "{ASPECT}"},
    ],
    # Count option (x1/x2/x3/x4). {COUNT} substituted with e.g. "x4" / "4".
    "count_option": [
        {"by": "role", "value": "button", "name": "(?i)^{COUNT}$"},
        {"by": "text", "value": "{COUNT}"},
    ],
    # Result image tiles for the most recent generation. We read their src to
    # download. This is the most generation-specific selector — tune it first.
    "result_images": [
        {"by": "css", "value": "img[src*='googleusercontent']"},
        {"by": "css", "value": "img[src^='blob:']"},
        {"by": "css", "value": "[data-generation] img"},
    ],
    # Any visible "%"/progress indicator; while present, generation is running.
    "progress_indicator": [
        {"by": "text", "value": "%"},
        {"by": "css", "value": "[role='progressbar']"},
    ],
    # Attached-ref thumbnails in the prompt bar (to confirm attach worked).
    "attached_ref_thumb": [
        {"by": "css", "value": "[data-ref-thumb]"},
        {"by": "css", "value": ".prompt-bar img"},
    ],
}


def load_selectors(project_root: Path) -> dict:
    """Merge: built-in defaults < flow_selectors.json (skill) < project override."""
    sel = json.loads(json.dumps(DEFAULT_SELECTORS))  # deep copy
    for path in (DEFAULT_SELECTORS_PATH, project_root / ".flow" / "selectors.json"):
        if path.exists():
            try:
                override = json.loads(path.read_text())
                for k, v in override.items():
                    sel[k] = v
            except Exception as e:  # noqa: BLE001
                print(f"[flow_runner] WARN: bad selectors file {path}: {e}",
                      file=sys.stderr)
    return sel


# ---------------------------------------------------------------------------
# Plan acquisition — delegate entirely to next_panel.py.
# ---------------------------------------------------------------------------
def get_plan(project_root: Path, panel_id: str | None = None) -> dict:
    """Run next_panel.py --as-json and return the parsed plan dict.

    We invoke with the SAME interpreter running this script so the dependency
    set matches. next_panel.py has no third-party deps, so any Python works.
    """
    cmd = [sys.executable, str(NEXT_PANEL), str(project_root), "--as-json"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            f"next_panel.py failed (exit {proc.returncode}):\n{proc.stderr}")
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"next_panel.py did not emit JSON:\n{proc.stdout[:500]}") from e


# ---------------------------------------------------------------------------
# Ref extraction from a plan.
#
# next_panel.py emits refs_to_attach_in_order; we keep only the ones that are
# real files to upload, in order, and skip notes / warnings / dropped-for-ceiling
# entries (those carry information for the prompt, not a file to attach).
# ---------------------------------------------------------------------------
ATTACHABLE_KINDS = {
    "state_anchor", "face_card", "env_anchor", "env_ref", "lineup",
    "tier6_reinforcement", "tier7_reinforcement",
    "tier8_reinforcement", "tier9_reinforcement",
}


def refs_to_upload(plan: dict, project_root: Path) -> list[dict]:
    """Resolve attachable refs to absolute, existing file paths, in order."""
    out: list[dict] = []
    for r in plan.get("refs_to_attach_in_order", []):
        kind = r.get("kind", "")
        if kind not in ATTACHABLE_KINDS:
            continue
        raw = r.get("path")
        if not raw:
            continue
        p = Path(raw)
        if not p.is_absolute():
            p = (project_root / p)
        p = p.expanduser()
        if not p.exists():
            print(f"[flow_runner] WARN: ref file missing on disk, skipping: {p}",
                  file=sys.stderr)
            continue
        out.append({"kind": kind, "path": str(p.resolve())})
    return out


def plan_warnings(plan: dict) -> list[dict]:
    """Surface WARNING_* / MISSING_* refs that should halt or flag a panel
    (mirrors shotlist-driven-flow.md 'When to break the loop')."""
    halts, flags = [], []
    for r in plan.get("refs_to_attach_in_order", []):
        kind = r.get("kind", "")
        if kind.startswith("WARNING_DIALOGUE_CAMERA") or kind.startswith("WARNING_MULTI_SPEAKER"):
            halts.append(r)
        elif kind.startswith("WARNING_") or kind.startswith("MISSING_"):
            flags.append(r)
    return {"halt": halts, "flag": flags}


# ---------------------------------------------------------------------------
# Flow page driver. All Playwright contact lives here.
# ---------------------------------------------------------------------------
@dataclass
class FlowDriver:
    selectors: dict
    cdp_url: str = "http://127.0.0.1:9222"  # IPv4: 'localhost' can resolve to ::1, which Chrome's CDP doesn't bind
    headless_note: str = ""
    _pw: object = field(default=None, repr=False)
    _browser: object = field(default=None, repr=False)
    _context: object = field(default=None, repr=False)
    page: object = field(default=None, repr=False)

    # ---- connection ----
    def connect(self):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as e:
            raise RuntimeError(
                "Playwright is not installed in this interpreter.\n"
                "Set up an isolated venv (see flow_runner_README.md):\n"
                "  uv venv ~/.flow-venv && \\\n"
                "  ~/.flow-venv/bin/python -m pip install playwright && \\\n"
                "  ~/.flow-venv/bin/python -m playwright install chromium\n"
                "Then run flow_runner.py with ~/.flow-venv/bin/python."
            ) from e

        self._pw = sync_playwright().start()
        try:
            self._browser = self._pw.chromium.connect_over_cdp(self.cdp_url)
        except Exception as e:  # noqa: BLE001
            raise RuntimeError(
                f"Cannot connect to Chrome over CDP at {self.cdp_url}.\n"
                "Launch Chrome with the debugging port and sign into Flow:\n"
                "  /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome "
                "--remote-debugging-port=9222\n"
                f"Verify with: curl {self.cdp_url}/json/version\n"
                f"Underlying error: {e}"
            ) from e

        # Reuse the existing (signed-in) context rather than making a new one.
        contexts = self._browser.contexts
        self._context = contexts[0] if contexts else self._browser.new_context()
        self.page = self._find_flow_page() or self._open_flow_page()
        return self

    def _find_flow_page(self):
        for ctx in self._browser.contexts:
            for pg in ctx.pages:
                try:
                    if FLOW_URL_FRAGMENT in (pg.url or ""):
                        self._context = ctx
                        return pg
                except Exception:  # noqa: BLE001
                    continue
        return None

    def _open_flow_page(self):
        pg = self._context.new_page()
        pg.goto(FLOW_URL, wait_until="domcontentloaded")
        return pg

    def close(self):
        # Do NOT close the browser — it's the user's. Just detach Playwright.
        try:
            if self._pw:
                self._pw.stop()
        except Exception:  # noqa: BLE001
            pass

    # ---- selector resolution ----
    def _resolve(self, key: str, subst: dict | None = None, *, required=True):
        """Return the first resolving Playwright Locator for a selector key,
        or None. `subst` substitutes {PLACEHOLDERS} in strategy values/names."""
        import re
        strategies = self.selectors.get(key, [])
        for strat in strategies:
            by = strat.get("by")
            val = strat.get("value", "")
            name = strat.get("name")
            if subst:
                for k, v in subst.items():
                    val = val.replace("{" + k + "}", v)
                    if name:
                        name = name.replace("{" + k + "}", v)
            try:
                loc = self._locator_for(by, val, name)
            except Exception:  # noqa: BLE001
                continue
            if loc is None:
                continue
            try:
                if loc.count() > 0:
                    return loc.first
            except Exception:  # noqa: BLE001
                # Some locators (role with regex name) don't support count well
                try:
                    loc.first.wait_for(state="attached", timeout=1500)
                    return loc.first
                except Exception:  # noqa: BLE001
                    continue
        if required:
            print(f"[flow_runner] WARN: no selector resolved for '{key}'. "
                  f"Run `probe` and tune .flow/selectors.json.", file=sys.stderr)
        return None

    def _locator_for(self, by, val, name):
        import re
        pg = self.page
        if by == "placeholder":
            return pg.get_by_placeholder(val)
        if by == "role":
            if name:
                return pg.get_by_role(val, name=re.compile(name) if name.startswith("(?") else name)
            return pg.get_by_role(val)
        if by == "text":
            return pg.get_by_text(val, exact=False)
        if by == "testid":
            return pg.get_by_test_id(val)
        if by == "css":
            return pg.locator(val)
        if by == "xpath":
            return pg.locator("xpath=" + val)
        if by == "enter":
            return None  # handled by caller
        return None

    # ---- actions ----
    def set_aspect_and_count(self, aspect: str, count: str):
        """Open the settings popup and set aspect ratio + variant count."""
        pill = self._resolve("settings_pill")
        if pill:
            pill.click()
            self.page.wait_for_timeout(400)
        # aspect
        aspect_opt = self._resolve("aspect_option", {"ASPECT": aspect}, required=False)
        if aspect_opt:
            aspect_opt.click()
            self.page.wait_for_timeout(200)
        else:
            print(f"[flow_runner] WARN: aspect '{aspect}' option not found; "
                  "leaving current aspect.", file=sys.stderr)
        # count (popup resets to x4 each open per flow-workflow.md, but set it
        # explicitly so non-x4 runs are honored)
        count_norm = count if count.startswith("x") else f"x{count}"
        count_opt = self._resolve("count_option", {"COUNT": count_norm}, required=False)
        if not count_opt:
            count_opt = self._resolve("count_option", {"COUNT": count_norm.lstrip("x")}, required=False)
        if count_opt:
            count_opt.click()
            self.page.wait_for_timeout(200)
        # close popup
        self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(200)

    def attach_ref(self, file_path: str) -> bool:
        """Attach one ref by uploading the local file via Flow's file chooser.

        Strategy 1 (preferred): click the +/upload control inside an
        expect_file_chooser() block and set_files. Strategy 2: set_input_files
        directly on a hidden <input type=file>.
        """
        # Strategy 1: file chooser
        for opener_key in ("add_ref_button", "upload_image"):
            opener = self._resolve(opener_key, required=False)
            if not opener:
                continue
            try:
                with self.page.expect_file_chooser(timeout=4000) as fc_info:
                    opener.click()
                    # The first click may open a menu; try the explicit upload item.
                    up = self._resolve("upload_image", required=False)
                    if up and opener_key == "add_ref_button":
                        try:
                            up.click(timeout=2000)
                        except Exception:  # noqa: BLE001
                            pass
                fc = fc_info.value
                fc.set_files(file_path)
                self.page.wait_for_timeout(800)
                return True
            except Exception:  # noqa: BLE001
                continue
        # Strategy 2: direct hidden input
        finp = self._resolve("file_input", required=False)
        if finp:
            try:
                finp.set_input_files(file_path)
                self.page.wait_for_timeout(800)
                return True
            except Exception as e:  # noqa: BLE001
                print(f"[flow_runner] WARN: file_input upload failed: {e}",
                      file=sys.stderr)
        return False

    def type_prompt(self, prompt: str):
        field_loc = self._resolve("prompt_input")
        if not field_loc:
            raise RuntimeError("Prompt input not found — calibrate selectors.")
        field_loc.click()
        # Clear any residual text, then type single-line (no newlines — Flow
        # treats Enter as submit).
        field_loc.fill("")
        single = " ".join(prompt.splitlines()).strip()
        field_loc.type(single, delay=0)
        self._prompt_field = field_loc

    def submit(self):
        # Try a real submit button first; fall back to Enter (single-line
        # prompts submit on Enter in Flow). _resolve already walks all non-enter
        # strategies, so one call suffices.
        loc = self._resolve("submit_button", required=False)
        if loc:
            try:
                loc.click()
                return
            except Exception:  # noqa: BLE001
                pass
        self.page.keyboard.press("Enter")

    def wait_for_generation(self, timeout_s: int = 180, expected: int = 4) -> bool:
        """Poll until generation completes: progress indicator gone AND at least
        `expected` result images present and stable across two polls."""
        deadline = time.time() + timeout_s
        last_count = -1
        stable_polls = 0
        while time.time() < deadline:
            self.page.wait_for_timeout(2500)
            prog = self._resolve("progress_indicator", required=False)
            running = False
            if prog:
                try:
                    running = prog.is_visible()
                except Exception:  # noqa: BLE001
                    running = False
            imgs = self._resolve("result_images", required=False)
            count = 0
            if imgs:
                try:
                    count = imgs.count()
                except Exception:  # noqa: BLE001
                    count = 0
            if not running and count >= expected:
                if count == last_count:
                    stable_polls += 1
                    if stable_polls >= 2:
                        return True
                else:
                    stable_polls = 0
            last_count = count
        return False

    def newest_result_srcs(self, n: int = 4) -> list[str]:
        """Return the src URLs of the n most-recent result images (DOM order
        assumed newest-first or newest-last; we take a best-effort newest set)."""
        loc = self._resolve("result_images", required=False)
        if not loc:
            return []
        srcs = []
        try:
            total = loc.count()
        except Exception:  # noqa: BLE001
            total = 0
        # Take the LAST n by default (Flow appends new gens). Tunable later.
        idxs = list(range(max(0, total - n), total))
        for i in idxs:
            try:
                s = loc.nth(i).get_attribute("src")
                if s:
                    srcs.append(s)
            except Exception:  # noqa: BLE001
                continue
        return srcs

    def download_srcs(self, srcs: list[str], dest_dir: Path, prefix="v") -> list[Path]:
        """Download each image URL to dest_dir/v1.png, v2.png ... using the
        browser context's authenticated request (carries cookies). blob: URLs
        are fetched via an in-page fetch + base64 bridge."""
        dest_dir.mkdir(parents=True, exist_ok=True)
        out: list[Path] = []
        for i, src in enumerate(srcs, start=1):
            target = dest_dir / f"{prefix}{i}.png"
            ok = False
            if src.startswith("blob:"):
                ok = self._download_blob(src, target)
            else:
                try:
                    resp = self._context.request.get(src)
                    if resp.ok:
                        target.write_bytes(resp.body())
                        ok = True
                except Exception:  # noqa: BLE001
                    ok = False
                if not ok:
                    ok = self._download_blob(src, target)  # fetch via page too
            if ok:
                out.append(target)
            else:
                print(f"[flow_runner] WARN: failed to download variant {i}: {src[:80]}",
                      file=sys.stderr)
        return out

    def _download_blob(self, src: str, target: Path) -> bool:
        """Fetch an image inside the page and return bytes via base64."""
        try:
            b64 = self.page.evaluate(
                """async (url) => {
                    const r = await fetch(url);
                    const b = await r.blob();
                    return await new Promise((res) => {
                        const fr = new FileReader();
                        fr.onloadend = () => res(fr.result.split(',')[1]);
                        fr.readAsDataURL(b);
                    });
                }""", src)
            import base64
            target.write_bytes(base64.b64decode(b64))
            return True
        except Exception:  # noqa: BLE001
            return False

    def screenshot(self, path: Path):
        try:
            self.page.screenshot(path=str(path), full_page=False)
        except Exception as e:  # noqa: BLE001
            print(f"[flow_runner] WARN: screenshot failed: {e}", file=sys.stderr)

    def accessibility_snapshot(self) -> dict:
        try:
            return self.page.accessibility.snapshot(interesting_only=False) or {}
        except Exception:  # noqa: BLE001
            return {}


# ---------------------------------------------------------------------------
# Subcommand implementations
# ---------------------------------------------------------------------------
def cmd_status(project_root: Path) -> int:
    plan = get_plan(project_root)
    if plan.get("next_panel") is None:
        print(json.dumps({
            "status": "complete",
            "accepted_count": plan.get("accepted_count"),
            "message": plan.get("message"),
        }, indent=2))
        return 0
    print(json.dumps({
        "status": "pending",
        "next_panel": plan["next_panel"]["panel_id"],
        "page": plan["next_panel"]["page_number"],
        "camera": plan["next_panel"]["camera"],
        "aspect": plan["aspect"],
        "count": plan["count"],
        "accepted_count": plan["accepted_count"],
        "remaining_count": plan["remaining_count"],
        "stage_change": plan["stage_change"],
        "refs": [r for r in plan["refs_to_attach_in_order"]],
    }, indent=2, default=str))
    return 0


def cmd_probe(project_root: Path, cdp_url: str) -> int:
    sel = load_selectors(project_root)
    flow_dir = project_root / ".flow"
    flow_dir.mkdir(parents=True, exist_ok=True)
    drv = FlowDriver(selectors=sel, cdp_url=cdp_url).connect()
    try:
        ts = time.strftime("%Y%m%d-%H%M%S", time.localtime())
        shot = flow_dir / f"probe-{ts}.png"
        drv.screenshot(shot)
        snap = drv.accessibility_snapshot()
        # Resolve each known selector and report whether it currently matches.
        resolved = {}
        for key in sel:
            loc = drv._resolve(key, required=False)
            matched = False
            sample = None
            if loc:
                try:
                    matched = loc.count() > 0
                    if matched:
                        sample = (loc.first.get_attribute("aria-label")
                                  or loc.first.inner_text()[:60] if matched else None)
                except Exception:  # noqa: BLE001
                    matched = True
            resolved[key] = {"matched": matched, "sample": sample}
        out = flow_dir / f"probe-{ts}.json"
        out.write_text(json.dumps({
            "url": drv.page.url,
            "selectors_resolved": resolved,
            "accessibility_snapshot": snap,
        }, indent=2, default=str))
        print(json.dumps({
            "status": "probed",
            "screenshot": str(shot),
            "report": str(out),
            "selectors_resolved": resolved,
        }, indent=2))
        return 0
    finally:
        drv.close()


def cmd_next(project_root: Path, cdp_url: str, *, count_override: str | None,
             timeout_s: int, auto_pick: str | None, dry_run: bool) -> int:
    plan = get_plan(project_root)
    if plan.get("next_panel") is None:
        print(json.dumps({"status": "complete",
                          "message": plan.get("message"),
                          "accepted_count": plan.get("accepted_count")}, indent=2))
        return 0

    np = plan["next_panel"]
    panel_id = np["panel_id"]
    aspect = plan["aspect"]
    count = count_override or plan.get("count", "x4")
    prompt = plan["composed_prompt"]
    refs = refs_to_upload(plan, project_root)
    warns = plan_warnings(plan)

    panel_dir = project_root / "pages" / "panels" / panel_id
    summary = {
        "status": "dry_run" if dry_run else None,
        "panel_id": panel_id,
        "page": np["page_number"],
        "camera": np["camera"],
        "aspect": aspect,
        "count": count,
        "stage_change": plan["stage_change"],
        "refs_to_attach": refs,
        "halt_warnings": warns["halt"],
        "flag_warnings": warns["flag"],
        "prompt": prompt,
        "panel_dir": str(panel_dir),
    }

    # Hard-halt conditions (L12/L13) — surface and stop before spending a gen.
    if warns["halt"]:
        summary["status"] = "halt"
        summary["reason"] = ("next_panel.py raised a hard-halt warning "
                             "(dialogue/camera or multi-speaker). Fix the shotlist "
                             "entry and re-run. See shotlist-driven-flow.md.")
        print(json.dumps(summary, indent=2, default=str))
        return 2

    if dry_run:
        print(json.dumps(summary, indent=2, default=str))
        return 0

    sel = load_selectors(project_root)
    drv = FlowDriver(selectors=sel, cdp_url=cdp_url).connect()
    try:
        drv.set_aspect_and_count(aspect, count)
        attached, failed = [], []
        for r in refs:
            ok = drv.attach_ref(r["path"])
            (attached if ok else failed).append(r["path"])
        drv.type_prompt(prompt)
        drv.screenshot(panel_dir / "_pre-submit.png")
        drv.submit()
        n_expected = int(str(count).lstrip("x") or "4")
        done = drv.wait_for_generation(timeout_s=timeout_s, expected=n_expected)
        drv.screenshot(panel_dir / "_post-gen.png")
        if not done:
            summary["status"] = "timeout"
            summary["attached_refs"] = attached
            summary["failed_refs"] = failed
            summary["reason"] = (f"Generation did not complete within {timeout_s}s "
                                 "(or result_images selector needs calibration). "
                                 "See _post-gen.png and run `probe`.")
            print(json.dumps(summary, indent=2, default=str))
            return 3
        srcs = drv.newest_result_srcs(n=n_expected)
        variants = drv.download_srcs(srcs, panel_dir, prefix="v")
        summary["attached_refs"] = attached
        summary["failed_refs"] = failed
        summary["variants"] = [str(p) for p in variants]

        if auto_pick and variants:
            _write_accept(panel_dir, auto_pick)
            summary["status"] = "auto_accepted"
            summary["accepted_variant"] = auto_pick
            summary["next_hint"] = "Re-run `next` for the following panel."
        else:
            summary["status"] = "awaiting_pick"
            summary["next_hint"] = (
                f"Read the {len(variants)} variant PNGs above, pick the best per the "
                "QA criteria in shotlist-driven-flow.md step 6, then run: "
                f"flow_runner.py {project_root} accept {panel_id} v<N>  (or write "
                f"'{panel_dir}/_accepted.txt' with the variant label). Then re-run `next`.")
        print(json.dumps(summary, indent=2, default=str))
        return 0
    finally:
        drv.close()


def _write_accept(panel_dir: Path, variant: str):
    panel_dir.mkdir(parents=True, exist_ok=True)
    label = variant if variant.startswith("v") else f"v{variant}"
    (panel_dir / "_accepted.txt").write_text(label + "\n")


def cmd_accept(project_root: Path, panel_id: str, variant: str) -> int:
    panel_dir = project_root / "pages" / "panels" / panel_id
    if not panel_dir.is_dir():
        # try panel-<id> form used by some projects
        alt = project_root / "pages" / "panels" / f"panel-{panel_id}"
        if alt.is_dir():
            panel_dir = alt
    label = variant if variant.startswith("v") else f"v{variant}"
    vfile = panel_dir / f"{label}.png"
    if not vfile.exists():
        print(json.dumps({
            "status": "error",
            "message": f"variant file not found: {vfile}. "
                       f"Available: {sorted(p.name for p in panel_dir.glob('v*.png'))}",
        }, indent=2))
        return 1
    _write_accept(panel_dir, label)
    print(json.dumps({
        "status": "accepted",
        "panel_id": panel_id,
        "variant": label,
        "accepted_marker": str(panel_dir / "_accepted.txt"),
        "next_hint": "Run `next` for the following panel.",
    }, indent=2))
    return 0


# ---------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__.split("\n")[0],
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project_root", type=Path)
    ap.add_argument("command", choices=["next", "accept", "status", "probe"])
    ap.add_argument("rest", nargs="*", help="for `accept`: <panel_id> <variant>")
    ap.add_argument("--cdp-url", default=os.environ.get("FLOW_CDP_URL", "http://127.0.0.1:9222"))
    ap.add_argument("--count", default=None, help="override variant count, e.g. x1 / x4")
    ap.add_argument("--timeout", type=int, default=180, help="per-panel generation timeout (s)")
    ap.add_argument("--auto-pick", default=None,
                    help="skip the Claude checkpoint and auto-accept this variant (e.g. v1)")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the composed plan + refs without driving the browser")
    args = ap.parse_args()

    root = args.project_root.expanduser().resolve()
    if not root.exists():
        print(f"error: project root does not exist: {root}", file=sys.stderr)
        return 1

    try:
        if args.command == "status":
            return cmd_status(root)
        if args.command == "probe":
            return cmd_probe(root, args.cdp_url)
        if args.command == "accept":
            if len(args.rest) < 2:
                print("usage: flow_runner.py <project> accept <panel_id> <variant>",
                      file=sys.stderr)
                return 1
            return cmd_accept(root, args.rest[0], args.rest[1])
        if args.command == "next":
            return cmd_next(root, args.cdp_url, count_override=args.count,
                            timeout_s=args.timeout, auto_pick=args.auto_pick,
                            dry_run=args.dry_run)
        return 1
    except RuntimeError as e:
        # Operational errors (CDP unreachable, Playwright missing, next_panel
        # failure) — surface a clean, actionable JSON message, not a traceback.
        print(json.dumps({"status": "error", "message": str(e)}, indent=2))
        return 1


if __name__ == "__main__":
    sys.exit(main())
