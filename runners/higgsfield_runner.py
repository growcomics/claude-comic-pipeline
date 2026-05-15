#!/usr/bin/env python3
"""higgsfield_runner.py — drive Higgsfield for unattended comic panel generation.

Two operating modes, selected via production-config.json:

  Mode A (recommended if you don't have a working Higgsfield runner yet):
    Direct HTTP API calls via the user's existing token_relay.js. The runner
    fetches an auth token from the token_relay endpoint, then POSTs to
    Higgsfield's generation API directly, polls for completion, downloads PNGs.

    Config:
      "higgsfield": {
        "mode": "api",
        "token_relay_url": "http://localhost:7878/token",
        "api_base": "https://higgsfield.ai/api",
        "folder_id": "<your-folder-id>",
        "default_ref_type": "nano_banana_2_job"
      }

  Mode B (recommended if you already have runner.py working):
    Adapter that invokes the user's existing runner.py with panels translated
    from shotlist.json + next_panel.py plans. The user's runner is responsible
    for state.json AND the actual submission; this runner is a thin wrapper
    that handles variant picking and Stage 3 orchestration.

    Config:
      "higgsfield": {
        "mode": "external_script",
        "runner_script": "/Users/jay/mac-mini/higgsfield/runner.py",
        "panels_input": "panels.json",    # filename the existing runner reads
        "panels_output": "state.json"     # filename the existing runner writes
      }

If the user's existing runner.py expects a different invocation pattern, edit
the _ExternalScriptBackend.submit_panel() method below.

Both modes share runner_core's state.json, variant_picker, and halt-reason
codification. From Claude Code's perspective they look identical.

API endpoints, token_relay protocol:
  The token_relay.js (Node.js) endpoint serves the current Higgsfield browser
  session's auth token. Default: GET http://localhost:7878/token returns
  {"token": "..."}. If your token_relay has a different shape, adjust
  _fetch_token() below.

  Higgsfield's actual API endpoints aren't formally documented; this runner
  uses the endpoints observed in the user's existing pipeline. If Higgsfield
  changes the API, edit the URL constants below.

  THIS IS UNSUPPORTED THIRD-PARTY USAGE. If Higgsfield ships a public API,
  prefer that. The token_relay approach is a stopgap.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

# Local imports
sys.path.insert(0, str(Path(__file__).resolve().parent))
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
# Mode A: direct API via token_relay


class HiggsfieldApiBackend(RunnerBackend):
    """Submits panels directly to Higgsfield via HTTP. Auth via token_relay."""

    DEFAULT_TOKEN_RELAY_URL = "http://localhost:7878/token"
    DEFAULT_API_BASE = "https://higgsfield.ai/api/v1"  # placeholder; update if needed

    def __init__(self, config: dict):
        hf = config.get("higgsfield", {}) or {}
        self.token_relay_url = hf.get(
            "token_relay_url", self.DEFAULT_TOKEN_RELAY_URL
        )
        self.api_base = hf.get("api_base", self.DEFAULT_API_BASE).rstrip("/")
        self.folder_id = hf.get("folder_id", "")
        self.default_ref_type = hf.get("default_ref_type", "nano_banana_2_job")
        self._cached_token: str | None = None
        self._cached_token_expires_at: float = 0

    # ----- auth -----

    def _fetch_token(self) -> str:
        """Get a fresh auth token from the token_relay endpoint."""
        if (
            self._cached_token
            and time.time() < self._cached_token_expires_at - 60
        ):
            return self._cached_token

        try:
            import requests  # lazy import so missing-pkg doesn't break health check
        except ImportError as e:
            raise RuntimeError(
                "requests package not installed. `pip install requests`"
            ) from e

        try:
            resp = requests.get(self.token_relay_url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            raise RuntimeError(
                f"token_relay GET {self.token_relay_url} failed: {e}. "
                "Is the token_relay.js Node server running on the Mac Mini?"
            )

        token = data.get("token") or data.get("authToken") or data.get("access_token")
        if not token:
            raise RuntimeError(
                f"token_relay response had no token field. Got: {data}. "
                "Adjust _fetch_token() to match your token_relay protocol."
            )

        self._cached_token = token
        # Cache for 30 min (Higgsfield tokens typically last longer)
        self._cached_token_expires_at = time.time() + 30 * 60
        return token

    # ----- RunnerBackend interface -----

    def check_health(self) -> tuple[bool, str]:
        try:
            token = self._fetch_token()
        except RuntimeError as e:
            return False, str(e)

        try:
            import requests
        except ImportError as e:
            return False, f"requests pkg missing: {e}"

        # Verify API reachable with a no-op (HEAD on /folders or similar).
        # We don't know the exact endpoint shape — this is a best-effort ping.
        try:
            resp = requests.head(
                f"{self.api_base}/folders/{self.folder_id}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
                allow_redirects=False,
            )
            if resp.status_code in (200, 204, 301, 302, 401, 403, 404):
                # 401/403/404 are still "API reachable" — auth or folder error,
                # not network error. Treat as healthy and let submit_panel
                # surface the real error.
                pass
        except Exception as e:
            return False, f"Higgsfield API unreachable: {e}"

        return True, f"Higgsfield API at {self.api_base}, folder={self.folder_id or 'unset'}"

    def submit_panel(
        self,
        plan: dict,
        project_root: Path,
        count: int,
        timeout_s: int,
    ) -> GenerationResult:
        """POST the panel to Higgsfield's generation endpoint, poll for results,
        download variants."""
        import requests

        token = self._fetch_token()
        panel = plan["next_panel"]
        panel_id = panel.get("panel_id", "unknown")
        prompt = plan.get("composed_prompt", "")
        aspect = plan.get("aspect", "3:4")

        if not prompt:
            raise RuntimeError(f"empty composed_prompt for {panel_id}")

        # Upload refs first (Higgsfield expects URLs, not local paths)
        ref_urls = self._upload_refs(
            plan.get("refs_to_attach_in_order", []) or [],
            project_root,
            token,
        )

        # Build job request. Field names below are best-effort guesses; adjust
        # to match Higgsfield's actual API shape from observed network traffic
        # in your existing runner.py.
        job_body = {
            "prompt": prompt,
            "aspect_ratio": aspect,
            "count": count,
            "folder_id": self.folder_id,
            "type": self.default_ref_type,
            "reference_images": ref_urls,
        }

        log_status(f"Panel {panel_id}: submitting to Higgsfield ({len(ref_urls)} refs)")
        try:
            resp = requests.post(
                f"{self.api_base}/jobs",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json=job_body,
                timeout=30,
            )
        except Exception as e:
            raise RuntimeError(f"Higgsfield job POST failed: {e}")

        if resp.status_code == 401:
            # Auth expired — clear cache and let runner_core's retry kick in
            self._cached_token = None
            raise RuntimeError("Higgsfield auth expired; token will refresh on retry")

        if resp.status_code == 429:
            raise RuntimeError("Higgsfield rate limit; will retry")

        if resp.status_code == 402:
            raise RuntimeError("Higgsfield credits exhausted (HTTP 402)")

        if resp.status_code >= 400:
            text = resp.text[:500]
            # Detect content-policy refusal patterns
            low = text.lower()
            if any(
                p in low for p in ["content policy", "safety", "violates", "refused"]
            ):
                return GenerationResult(
                    variant_paths=[],
                    raw_metadata={"status": resp.status_code, "body": text},
                    refusal=True,
                    refusal_reason=text,
                )
            raise RuntimeError(f"Higgsfield job POST HTTP {resp.status_code}: {text}")

        job = resp.json()
        job_id = job.get("id") or job.get("job_id")
        if not job_id:
            raise RuntimeError(f"Higgsfield job POST returned no job_id: {job}")

        log_status(f"Panel {panel_id}: job_id={job_id}, polling for completion")

        # Poll
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            try:
                presp = requests.get(
                    f"{self.api_base}/jobs/{job_id}",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=15,
                )
            except Exception as e:
                logger.warning("poll error: %s, retrying", e)
                time.sleep(3)
                continue

            if presp.status_code == 401:
                self._cached_token = None
                token = self._fetch_token()
                continue

            if presp.status_code >= 400:
                raise RuntimeError(
                    f"Higgsfield job GET HTTP {presp.status_code}: {presp.text[:300]}"
                )

            data = presp.json()
            status = (data.get("status") or "").lower()
            if status in ("completed", "succeeded", "done"):
                # Find result URLs
                results = data.get("results") or data.get("outputs") or []
                if isinstance(results, dict):
                    results = list(results.values())
                if not results:
                    raise RuntimeError(f"job {job_id} completed but has no results")
                urls = []
                for r in results:
                    if isinstance(r, dict):
                        u = r.get("url") or r.get("output_url") or r.get("png_url")
                        if u:
                            urls.append(u)
                    elif isinstance(r, str):
                        urls.append(r)
                if len(urls) < count:
                    raise RuntimeError(
                        f"job {job_id} returned {len(urls)} URLs, expected {count}"
                    )
                # CRITICAL: per user memory note, ref URLs must use .png not _min.webp
                urls = [u.replace("_min.webp", ".png") for u in urls]
                variant_paths = self._download_variants(
                    urls[:count], project_root, panel_id, token
                )
                return GenerationResult(
                    variant_paths=variant_paths,
                    raw_metadata={"job_id": job_id, "result_urls": urls},
                    refusal=False,
                )

            if status in ("failed", "error", "refused"):
                msg = data.get("error") or data.get("message") or status
                low = str(msg).lower()
                if any(p in low for p in ["content", "safety", "policy", "violates"]):
                    return GenerationResult(
                        variant_paths=[],
                        raw_metadata={"job_id": job_id, "status": status, "error": msg},
                        refusal=True,
                        refusal_reason=str(msg),
                    )
                raise RuntimeError(f"Higgsfield job {job_id} failed: {msg}")

            # Still in progress
            time.sleep(3)

        raise RuntimeError(f"Higgsfield job {job_id} timed out after {timeout_s}s")

    def close(self) -> None:
        self._cached_token = None

    # ----- helpers -----

    def _upload_refs(
        self, refs: list[dict], project_root: Path, token: str
    ) -> list[str]:
        """Upload each ref image to Higgsfield's media endpoint and return URLs."""
        import requests
        urls: list[str] = []
        for ref in refs:
            kind = ref.get("kind", "")
            if kind == "note" or not ref.get("path"):
                continue
            if kind.startswith("MISSING_"):
                raise RuntimeError(f"unexpected MISSING_ ref: {ref}")
            abs_path = (project_root / ref["path"]).resolve()
            if not abs_path.is_file():
                raise RuntimeError(f"ref file missing on disk: {abs_path}")
            try:
                with open(abs_path, "rb") as f:
                    resp = requests.post(
                        f"{self.api_base}/media",
                        headers={"Authorization": f"Bearer {token}"},
                        files={"file": (abs_path.name, f, "image/png")},
                        timeout=30,
                    )
            except Exception as e:
                raise RuntimeError(f"ref upload failed for {abs_path}: {e}")
            if resp.status_code >= 400:
                raise RuntimeError(
                    f"ref upload HTTP {resp.status_code} for {abs_path}: "
                    f"{resp.text[:300]}"
                )
            data = resp.json()
            url = data.get("url") or data.get("media_url")
            if not url:
                raise RuntimeError(f"ref upload no URL in response: {data}")
            # CRITICAL: .png not _min.webp
            url = url.replace("_min.webp", ".png")
            urls.append(url)
        return urls

    def _download_variants(
        self,
        urls: list[str],
        project_root: Path,
        panel_id: str,
        token: str,
    ) -> list[Path]:
        import requests
        out_dir = project_root / "pages" / "panels" / panel_id
        out_dir.mkdir(parents=True, exist_ok=True)
        saved: list[Path] = []
        for i, url in enumerate(urls, start=1):
            try:
                resp = requests.get(
                    url,
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=60,
                )
                resp.raise_for_status()
                out = out_dir / f"v{i}.png"
                out.write_bytes(resp.content)
                saved.append(out)
            except Exception as e:
                raise RuntimeError(f"variant {i} download failed: {e}")
        return saved


# ---------------------------------------------------------------------------
# Mode B: adapter for an existing user runner.py


class _ExternalScriptBackend(RunnerBackend):
    """Invoke the user's existing Higgsfield runner.py as a subprocess.

    Contract: the external script reads a panels.json file describing what
    to generate and writes a results file describing what was produced. The
    runner_core handles variant picking and state.json after the external
    script completes its panels.

    Default invocation:
        <runner_script> --panels panels.json --output results.json --folder <id>

    Edit this class to match your existing runner's CLI."""

    def __init__(self, config: dict):
        hf = config.get("higgsfield", {}) or {}
        self.runner_script = hf.get("runner_script", "")
        self.folder_id = hf.get("folder_id", "")
        self.panels_input = hf.get("panels_input", "panels.json")
        self.panels_output = hf.get("panels_output", "results.json")
        if not self.runner_script:
            raise RuntimeError(
                "higgsfield.runner_script is empty in production-config.json. "
                "Set it to the absolute path of your existing runner.py."
            )

    def check_health(self) -> tuple[bool, str]:
        p = Path(self.runner_script)
        if not p.is_file():
            return False, f"runner_script not found: {p}"
        return True, f"external runner: {p}"

    def submit_panel(
        self, plan: dict, project_root: Path, count: int, timeout_s: int
    ) -> GenerationResult:
        """Translate the plan to a one-panel panels.json, invoke the external
        runner, read back its output, return GenerationResult."""

        panel = plan["next_panel"]
        panel_id = panel.get("panel_id", "unknown")

        # Build panels.json with just this one panel
        panels_payload = {
            "folder_id": self.folder_id,
            "panels": [
                {
                    "panel_id": panel_id,
                    "prompt": plan.get("composed_prompt", ""),
                    "aspect": plan.get("aspect", "3:4"),
                    "count": count,
                    "refs": [
                        {"kind": r.get("kind"), "path": r.get("path")}
                        for r in (plan.get("refs_to_attach_in_order") or [])
                        if r.get("path") and not str(r.get("kind", "")).startswith("MISSING_")
                        and r.get("kind") != "note"
                    ],
                }
            ],
        }

        panels_path = project_root / self.panels_input
        results_path = project_root / self.panels_output
        panels_path.write_text(json.dumps(panels_payload, indent=2), encoding="utf-8")
        if results_path.exists():
            results_path.unlink()

        # Invoke the external runner. Adjust CLI args to match your runner.py.
        cmd = [
            sys.executable,
            self.runner_script,
            "--panels", str(panels_path),
            "--output", str(results_path),
        ]
        log_status(f"Panel {panel_id}: invoking external runner: {cmd}")
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(project_root),
                capture_output=True,
                text=True,
                timeout=timeout_s,
                check=False,
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"external runner timed out after {timeout_s}s")

        if proc.returncode != 0:
            err = (proc.stderr or proc.stdout or "no stderr").strip()
            # Detect content-policy in stderr
            low = err.lower()
            if any(p in low for p in ["content policy", "safety", "violates"]):
                return GenerationResult(
                    variant_paths=[],
                    raw_metadata={"stdout": proc.stdout, "stderr": proc.stderr},
                    refusal=True,
                    refusal_reason=err[:500],
                )
            raise RuntimeError(
                f"external runner exit {proc.returncode}: {err[:500]}"
            )

        if not results_path.is_file():
            raise RuntimeError(
                f"external runner exit 0 but no {results_path} produced"
            )

        results = json.loads(results_path.read_text(encoding="utf-8"))
        # Expected shape: {"panels": [{"panel_id": "...", "variant_paths": [...]}]}
        # OR: variants written to pages/panels/<panel_id>/v[1-4].png already.
        out_dir = project_root / "pages" / "panels" / panel_id
        out_dir.mkdir(parents=True, exist_ok=True)

        # Look for v1..vN.png in the expected place
        existing = sorted(out_dir.glob("v*.png"))
        if len(existing) >= count:
            return GenerationResult(
                variant_paths=existing[:count],
                raw_metadata={"external_results": results},
                refusal=False,
            )

        # Or accept paths from results
        for entry in results.get("panels", []):
            if entry.get("panel_id") != panel_id:
                continue
            paths = entry.get("variant_paths") or []
            if len(paths) >= count:
                return GenerationResult(
                    variant_paths=[Path(p) for p in paths[:count]],
                    raw_metadata={"external_results": results},
                    refusal=False,
                )

        raise RuntimeError(
            f"external runner produced no variants for {panel_id}"
        )

    def close(self) -> None:
        pass


# ---------------------------------------------------------------------------
# CLI


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Drive Higgsfield for unattended comic panel generation."
    )
    add_common_args(parser)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Health check only; don't submit anything.",
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

    hf = config.get("higgsfield", {}) or {}
    mode = hf.get("mode", "api")  # default to API mode

    if mode == "api":
        backend = HiggsfieldApiBackend(config)
    elif mode == "external_script":
        try:
            backend = _ExternalScriptBackend(config)
        except RuntimeError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
    else:
        print(
            f"error: higgsfield.mode must be 'api' or 'external_script', got '{mode}'",
            file=sys.stderr,
        )
        return 2

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
