#!/usr/bin/env python3
"""runner_core.py — shared scaffolding for flow_runner and higgsfield_runner.

Provides:
  * State management (state.json atomic read/write)
  * Panel-loop driver (iterate panels, call platform-specific submit, handle
    retries, halt conditions)
  * Halt reason codification (the only conditions a runner may halt on)
  * Status-stream helpers (one-line-per-panel logs for parent process to read)

Platform-specific behavior (Flow Playwright vs Higgsfield HTTP) is injected
via a `RunnerBackend` protocol. Subclasses implement `submit_panel`,
`fetch_variants`, `check_health`, `close`.

This file has no Playwright or anthropic dependencies — those are only in the
platform-specific runners. runner_core can be imported anywhere.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import traceback
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterator

from variant_picker import VariantPickResult, pick_variant

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Halt reasons — the COMPLETE list of conditions a runner may halt on.
# Anything else is a transient error and gets retried.


class HaltReason:
    MISSING_REF = "MISSING_REF"  # next_panel.py says a required ref is absent
    CONTENT_POLICY_REFUSAL = "CONTENT_POLICY_REFUSAL"  # Flow safety filter
    AUTH_EXPIRED = "AUTH_EXPIRED"  # platform auth failed and won't recover
    MAX_RETRIES_EXCEEDED = "MAX_RETRIES_EXCEEDED"  # same error N times
    FILESYSTEM_ERROR = "FILESYSTEM_ERROR"  # can't write panels/state
    API_KEY_MISSING = "API_KEY_MISSING"  # ANTHROPIC_API_KEY unset for picker
    CREDITS_EXHAUSTED = "CREDITS_EXHAUSTED"  # platform credit exhausted
    BROWSER_CRASH = "BROWSER_CRASH"  # CDP connection lost beyond recovery
    SCRIPT_AMBIGUITY = "SCRIPT_AMBIGUITY"  # next_panel.py error in shotlist
    USER_INTERRUPT = "USER_INTERRUPT"  # SIGINT


# ---------------------------------------------------------------------------
# State management


@dataclass
class PanelState:
    state: str  # "pending" | "in_progress" | "accepted" | "halted"
    picked_variant: int | None = None
    pick_reason: str = ""
    pick_strategy: str = ""
    concerns: list[str] = field(default_factory=list)
    attempts: int = 0
    last_error: str = ""
    completed_at: str = ""


@dataclass
class RunnerState:
    version: int = 1
    platform: str = ""
    started_at: str = ""
    last_updated: str = ""
    panels: dict[str, PanelState] = field(default_factory=dict)
    halt_reason: str | None = None
    halt_panel_id: str | None = None
    halt_detail: str = ""
    total_api_cost_usd: float = 0.0

    def to_json(self) -> dict:
        return {
            "version": self.version,
            "platform": self.platform,
            "started_at": self.started_at,
            "last_updated": self.last_updated,
            "panels": {
                pid: asdict(ps) for pid, ps in self.panels.items()
            },
            "halt_reason": self.halt_reason,
            "halt_panel_id": self.halt_panel_id,
            "halt_detail": self.halt_detail,
            "total_api_cost_usd": round(self.total_api_cost_usd, 4),
        }

    @classmethod
    def from_json(cls, data: dict) -> "RunnerState":
        state = cls(
            version=data.get("version", 1),
            platform=data.get("platform", ""),
            started_at=data.get("started_at", ""),
            last_updated=data.get("last_updated", ""),
            halt_reason=data.get("halt_reason"),
            halt_panel_id=data.get("halt_panel_id"),
            halt_detail=data.get("halt_detail", ""),
            total_api_cost_usd=float(data.get("total_api_cost_usd", 0.0)),
        )
        for pid, ps_data in (data.get("panels") or {}).items():
            state.panels[pid] = PanelState(
                state=ps_data.get("state", "pending"),
                picked_variant=ps_data.get("picked_variant"),
                pick_reason=ps_data.get("pick_reason", ""),
                pick_strategy=ps_data.get("pick_strategy", ""),
                concerns=list(ps_data.get("concerns", []) or []),
                attempts=int(ps_data.get("attempts", 0)),
                last_error=ps_data.get("last_error", ""),
                completed_at=ps_data.get("completed_at", ""),
            )
        return state


def load_state(project_root: Path) -> RunnerState:
    p = project_root / "state.json"
    if not p.is_file():
        return RunnerState(started_at=_now_iso())
    try:
        return RunnerState.from_json(json.loads(p.read_text(encoding="utf-8")))
    except Exception as e:
        logger.warning("state.json unreadable (%s) — starting fresh", e)
        return RunnerState(started_at=_now_iso())


def save_state(project_root: Path, state: RunnerState) -> None:
    """Atomic write of state.json. write -> fsync -> rename."""
    state.last_updated = _now_iso()
    p = project_root / "state.json"
    tmp = project_root / "state.json.tmp"
    data = json.dumps(state.to_json(), indent=2)
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    # Atomic rename (POSIX guarantee; Windows >= 10 also)
    os.replace(tmp, p)


def _now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


# ---------------------------------------------------------------------------
# Config loading


def load_config(project_root: Path) -> dict:
    p = project_root / "production-config.json"
    if not p.is_file():
        raise FileNotFoundError(
            f"production-config.json not found at {p}. "
            "Run /build-comic autopilot first to invoke the briefing skill."
        )
    return json.loads(p.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Panel plan invocation (calls next_panel.py)


def get_next_panel_plan(
    project_root: Path,
    next_panel_script: Path,
    panel_id_hint: str | None = None,
) -> dict | None:
    """Invoke next_panel.py --as-json on the project and return the plan.

    Returns None if all panels are accepted.
    Raises RuntimeError on script error.

    If panel_id_hint is set and next_panel.py supports it (future flag), the
    runner can target a specific panel for resume. Currently next_panel.py
    auto-detects from state on disk so the hint is informational only.
    """
    cmd = [sys.executable, str(next_panel_script), str(project_root), "--as-json"]
    # Pass the config path so next_panel.py reads lineup_files and other
    # config-driven fields (per the v2 patch).
    config_path = project_root / "production-config.json"
    if config_path.is_file():
        cmd += ["--config", str(config_path)]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError("next_panel.py timed out after 120s")
    except FileNotFoundError as e:
        raise RuntimeError(f"next_panel.py not found at {next_panel_script}: {e}")

    if proc.returncode != 0:
        raise RuntimeError(
            f"next_panel.py exited with code {proc.returncode}: {proc.stderr.strip()}"
        )

    try:
        plan = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"next_panel.py output not valid JSON: {e}\nstdout: {proc.stdout[:500]}"
        )

    if plan.get("error"):
        raise RuntimeError(f"next_panel.py error: {plan['error']}")

    if plan.get("next_panel") is None:
        return None  # All done

    return plan


def detect_missing_refs(plan: dict) -> list[str]:
    """Walk refs_to_attach_in_order for entries with 'MISSING_' prefix.
    Returns list of missing-ref descriptors. Empty list = clean.
    """
    missing = []
    for ref in plan.get("refs_to_attach_in_order", []) or []:
        kind = (ref.get("kind") or "").upper()
        path = ref.get("path") or ""
        if kind.startswith("MISSING_") or path.startswith("MISSING_"):
            missing.append(f"{kind}: {ref.get('reason', '')}")
    return missing


# ---------------------------------------------------------------------------
# RunnerBackend protocol — platforms implement this


@dataclass
class GenerationResult:
    """What a backend returns from a single panel submission."""
    variant_paths: list[Path]  # PNGs on disk, in order v1, v2, v3, v4
    raw_metadata: dict  # platform-specific (job_id, urls, etc.)
    refusal: bool = False  # True if platform refused for content policy
    refusal_reason: str = ""


class RunnerBackend(ABC):
    """Platform-specific runner. Implement these four methods.

    The runner_core orchestrates: check_health -> for each panel:
        submit_panel -> wait -> fetch_variants -> save to disk -> pick variant
        -> commit accepted -> next.
    """

    @abstractmethod
    def check_health(self) -> tuple[bool, str]:
        """Verify the platform is reachable and auth is valid.
        Returns (ok, message). On failure, runner aborts before doing any work.
        """
        ...

    @abstractmethod
    def submit_panel(
        self,
        plan: dict,
        project_root: Path,
        count: int,
        timeout_s: int,
    ) -> GenerationResult:
        """Submit a panel for generation and return paths to the saved variants.

        Implementations:
          * Read plan["composed_prompt"], plan["aspect"], etc.
          * Attach each ref in plan["refs_to_attach_in_order"]
          * Submit and wait for `count` variants
          * Save each variant to <project_root>/pages/panels/<panel_id>/v{N}.png
          * Return GenerationResult

        Raise exceptions for transient errors (timeouts, network glitches).
        Set refusal=True with refusal_reason for content-policy refusals.
        """
        ...

    @abstractmethod
    def close(self) -> None:
        """Clean shutdown — close browser, drop API client, etc."""
        ...


# ---------------------------------------------------------------------------
# The panel loop


@dataclass
class RunOptions:
    project_root: Path
    config: dict
    next_panel_script: Path
    backend: RunnerBackend
    log_path: Path | None = None
    max_panel_seconds: int = 600  # per-panel timeout
    progress_callback: callable | None = None  # called after each panel


def run(opts: RunOptions) -> RunnerState:
    """The main panel loop. Returns the final state. Caller checks
    state.halt_reason to decide what to surface."""
    pr = opts.project_root
    cfg = opts.config
    state = load_state(pr)
    if not state.platform:
        state.platform = cfg.get("platform", "unknown")
    save_state(pr, state)

    # SIGINT handler — flush state then re-raise so subprocess parent can detect
    def _on_sigint(*a, **kw):
        state.halt_reason = HaltReason.USER_INTERRUPT
        state.halt_detail = "SIGINT received"
        save_state(pr, state)
        sys.exit(130)

    signal.signal(signal.SIGINT, _on_sigint)

    # Health check before doing any work
    log_status("Checking platform health...")
    ok, msg = opts.backend.check_health()
    if not ok:
        state.halt_reason = HaltReason.AUTH_EXPIRED
        state.halt_detail = msg
        save_state(pr, state)
        log_status(f"HALT: health check failed — {msg}")
        opts.backend.close()
        return state

    log_status(f"Platform OK: {msg}")

    gen_cfg = cfg.get("generation", {})
    max_retries = int(gen_cfg.get("max_retries_per_panel", 3))
    on_all_bad = gen_cfg.get("on_all_bad", "retry-with-cgi-anchor-boost")
    pick_strategy = gen_cfg.get("variant_picker", "claude_api")

    # Main loop
    while True:
        try:
            plan = get_next_panel_plan(pr, opts.next_panel_script)
        except RuntimeError as e:
            state.halt_reason = HaltReason.SCRIPT_AMBIGUITY
            state.halt_detail = f"next_panel.py failed: {e}"
            save_state(pr, state)
            log_status(f"HALT: {state.halt_detail}")
            opts.backend.close()
            return state

        if plan is None:
            log_status("All panels accepted. Run complete.")
            opts.backend.close()
            return state

        panel = plan["next_panel"]
        panel_id = panel.get("panel_id", "unknown")

        # Missing-ref guardrail (L11 phantom-ref rule)
        missing = detect_missing_refs(plan)
        if missing:
            state.halt_reason = HaltReason.MISSING_REF
            state.halt_panel_id = panel_id
            state.halt_detail = "; ".join(missing)
            save_state(pr, state)
            log_status(f"HALT on {panel_id}: missing refs — {state.halt_detail}")
            opts.backend.close()
            return state

        # Mark in-progress
        ps = state.panels.setdefault(panel_id, PanelState(state="pending"))
        ps.state = "in_progress"
        ps.attempts += 1
        save_state(pr, state)

        log_status(
            f"Panel {panel_id} (page {plan.get('page_number', '?')}) — "
            f"camera={panel.get('camera', '?')} attempt={ps.attempts}"
        )

        # Submit
        count = int(plan.get("count", 4))
        try:
            result = opts.backend.submit_panel(
                plan, pr, count=count, timeout_s=opts.max_panel_seconds
            )
        except Exception as e:
            tb = traceback.format_exc()
            ps.last_error = f"submit_panel exception: {e}"
            save_state(pr, state)
            log_status(f"Panel {panel_id} — submit failed: {e}")
            if ps.attempts >= max_retries:
                state.halt_reason = HaltReason.MAX_RETRIES_EXCEEDED
                state.halt_panel_id = panel_id
                state.halt_detail = f"after {max_retries} attempts: {e}\n\n{tb}"
                save_state(pr, state)
                log_status(f"HALT: max retries on {panel_id}")
                opts.backend.close()
                return state
            # backoff and retry
            time.sleep(min(2**ps.attempts, 30))
            continue

        # Content-policy refusal halt
        if result.refusal:
            state.halt_reason = HaltReason.CONTENT_POLICY_REFUSAL
            state.halt_panel_id = panel_id
            state.halt_detail = result.refusal_reason
            save_state(pr, state)
            log_status(f"HALT on {panel_id}: content refusal — {result.refusal_reason}")
            opts.backend.close()
            return state

        # Variant pick
        try:
            pick = pick_variant(
                result.variant_paths,
                plan,
                cfg,
                strategy=pick_strategy,
            )
        except RuntimeError as e:
            ps.last_error = f"variant_picker exception: {e}"
            save_state(pr, state)
            log_status(f"Panel {panel_id} — picker failed: {e}")
            if "ANTHROPIC_API_KEY" in str(e):
                state.halt_reason = HaltReason.API_KEY_MISSING
                state.halt_panel_id = panel_id
                state.halt_detail = str(e)
                save_state(pr, state)
                opts.backend.close()
                return state
            if ps.attempts >= max_retries:
                state.halt_reason = HaltReason.MAX_RETRIES_EXCEEDED
                state.halt_panel_id = panel_id
                state.halt_detail = f"picker failed {max_retries} times: {e}"
                save_state(pr, state)
                opts.backend.close()
                return state
            time.sleep(2)
            continue

        # All-bad handling
        if pick.all_bad:
            log_status(
                f"Panel {panel_id} — all variants bad per picker. on_all_bad={on_all_bad}"
            )
            if on_all_bad == "halt":
                state.halt_reason = HaltReason.MAX_RETRIES_EXCEEDED
                state.halt_panel_id = panel_id
                state.halt_detail = f"all variants bad: {pick.reason}"
                save_state(pr, state)
                opts.backend.close()
                return state
            elif on_all_bad == "retry-with-cgi-anchor-boost":
                if ps.attempts >= max_retries:
                    state.halt_reason = HaltReason.MAX_RETRIES_EXCEEDED
                    state.halt_panel_id = panel_id
                    state.halt_detail = f"all variants bad after {max_retries} retries"
                    save_state(pr, state)
                    opts.backend.close()
                    return state
                # The backend retry handler is responsible for boosting the
                # prompt — we just retry the panel here.
                ps.last_error = "all variants bad, retrying with cgi anchor boost"
                save_state(pr, state)
                continue
            elif on_all_bad == "skip-with-flag":
                ps.state = "accepted"  # flagged accepted
                ps.picked_variant = pick.picked
                ps.pick_reason = f"FLAGGED: {pick.reason}"
                ps.concerns = pick.concerns + ["all_bad=true, skipped per policy"]
                ps.completed_at = _now_iso()
                save_state(pr, state)
                _commit_accepted(pr, panel_id, result.variant_paths, pick.picked)
                log_status(f"Panel {panel_id} — skipped with flag")
                continue

        # Normal commit
        if pick.api_cost_usd:
            state.total_api_cost_usd += pick.api_cost_usd
        ps.state = "accepted"
        ps.picked_variant = pick.picked
        ps.pick_reason = pick.reason
        ps.pick_strategy = pick.strategy_used
        ps.concerns = pick.concerns
        ps.completed_at = _now_iso()
        save_state(pr, state)
        _commit_accepted(pr, panel_id, result.variant_paths, pick.picked)

        log_status(
            f"Panel {panel_id} done — picked V{pick.picked} ({pick.strategy_used})"
            f"{' [concerns: ' + ', '.join(pick.concerns) + ']' if pick.concerns else ''}"
        )

        if opts.progress_callback:
            try:
                opts.progress_callback(state)
            except Exception:
                logger.exception("progress_callback failed (ignored)")


def _commit_accepted(
    project_root: Path,
    panel_id: str,
    variant_paths: list[Path],
    picked_idx: int,
) -> None:
    """Copy the picked variant to the canonical accepted location:
    pages/panels/<panel_id>.png — where next_panel.py expects to find it.

    Also writes pages/panels/<panel_id>/_accepted.txt so next_panel.py's
    folder-based acceptance check recognizes the panel as done. Without this
    marker, next_panel.py sees v*.png variants in the folder, classifies the
    panel as in_progress, and the runner loops re-generating it forever.
    """
    src = variant_paths[picked_idx - 1]
    dst = project_root / "pages" / "panels" / f"{panel_id}.png"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)

    folder = project_root / "pages" / "panels" / panel_id
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "_accepted.txt").write_text(f"v{picked_idx}")


def log_status(msg: str) -> None:
    """One-line stdout writes — designed for the parent (Claude Code) to read
    as a progress stream. Each line is flushed immediately.

    Windows note: stdout's default encoding is cp1252, which can't encode many
    unicode chars (e.g. → ← arrows from Playwright error traces). Without a
    safe fallback, a single un-encodable char crashes the runner mid-panel
    instead of triggering the normal retry path. Use the stream's own encoding
    with errors='replace' so logging is never the failure point.
    """
    stamp = dt.datetime.now().strftime("%H:%M:%S")
    line = f"[{stamp}] {msg}"
    try:
        print(line, flush=True)
    except UnicodeEncodeError:
        enc = getattr(sys.stdout, "encoding", None) or "ascii"
        sys.stdout.buffer.write(line.encode(enc, errors="replace") + b"\n")
        sys.stdout.flush()


# ---------------------------------------------------------------------------
# Argv parser shared by both runners


def add_common_args(parser):
    parser.add_argument(
        "--project",
        required=True,
        help="Project root directory (cwd of the comic)",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Path to production-config.json (default: <project>/production-config.json)",
    )
    parser.add_argument(
        "--next-panel-script",
        default=None,
        help="Path to next_panel.py (default: ~/.claude/skills/comic-production/scripts/next_panel.py)",
    )
    parser.add_argument(
        "--max-panel-seconds",
        type=int,
        default=600,
        help="Per-panel timeout in seconds (default 600)",
    )
    parser.add_argument(
        "--log-file",
        default=None,
        help="Path to a log file (default: <project>/runner.log)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose debug logging",
    )


def resolve_next_panel_script(arg_value: str | None) -> Path:
    if arg_value:
        return Path(arg_value).expanduser().resolve()
    # Default: under ~/.claude/skills/comic-production/scripts/next_panel.py
    return (
        Path.home()
        / ".claude"
        / "skills"
        / "comic-production"
        / "scripts"
        / "next_panel.py"
    ).resolve()


def setup_logging(project_root: Path, log_file: str | None, verbose: bool) -> None:
    # Reconfigure stdout/stderr to never blow up on non-cp1252 chars. Playwright
    # error traces include → ← arrows; a single un-encodable char would
    # otherwise crash the runner mid-loop instead of letting retry handle the
    # underlying transient error.
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream is not None and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass

    level = logging.DEBUG if verbose else logging.INFO
    log_path = (
        Path(log_file).expanduser().resolve()
        if log_file
        else project_root / "runner.log"
    )
    log_path.parent.mkdir(parents=True, exist_ok=True)
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setLevel(level)
    fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logging.getLogger().addHandler(fh)
    logging.getLogger().setLevel(level)
