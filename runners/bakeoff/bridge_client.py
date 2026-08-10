#!/usr/bin/env python3
"""Bridge client for the bakeoff lane — stdlib-only, mirrors studio/worker/worker.py.

Talks to studio/bridge.php with the key from ~/Documents/_imptest/bridgekey.txt
(override: BRIDGE_KEY env, BRIDGE_KEY_FILE env). The key is never logged.
"""
from __future__ import annotations

import base64
import json
import mimetypes
import os
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

DEFAULT_BRIDGE = "https://3dmusclecomics.com/studio/bridge.php"
DEFAULT_KEY_FILE = Path.home() / "Documents/_imptest/bridgekey.txt"


class BridgeError(RuntimeError):
    pass


def _key() -> str:
    k = os.environ.get("BRIDGE_KEY", "").strip()
    if k:
        return k
    kf = Path(os.environ.get("BRIDGE_KEY_FILE", str(DEFAULT_KEY_FILE)))
    if not kf.is_file():
        raise BridgeError(f"bridge key file missing: {kf}")
    return kf.read_text().strip()


class Bridge:
    def __init__(self, url: str | None = None, timeout: int = 120):
        self.url = (url or os.environ.get("BRIDGE_URL", DEFAULT_BRIDGE)).rstrip("?")
        self.timeout = timeout
        self._k = _key()

    # -- transport ----------------------------------------------------------
    def call(self, do: str, files: dict | None = None, **fields) -> dict:
        """POST do=<verb>. files = {field: (filename, bytes)}. Returns decoded JSON."""
        fields = {k: v for k, v in fields.items() if v is not None}
        fields["do"] = do
        if files:
            body, ctype = _multipart(fields, files)
        else:
            body = urllib.parse.urlencode(fields).encode()
            ctype = "application/x-www-form-urlencoded"
        req = urllib.request.Request(
            self.url, data=body,
            headers={"Content-Type": ctype, "X-Bridge-Key": self._k},
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                raw = r.read()
        except urllib.error.HTTPError as e:
            raise BridgeError(f"do={do} HTTP {e.code}: {e.read()[:300]!r}") from e
        except urllib.error.URLError as e:
            raise BridgeError(f"do={do} network error: {e.reason}") from e
        try:
            out = json.loads(raw)
        except json.JSONDecodeError:
            raise BridgeError(f"do={do} non-JSON reply: {raw[:300]!r}")
        if isinstance(out, dict) and out.get("ok") is False:
            raise BridgeError(f"do={do} rejected: {out.get('error')}")
        return out

    # -- verbs used by the lane --------------------------------------------
    def genspec(self, pid: str) -> dict:
        return self.call("genspec", p=pid)

    def images(self, pid: str) -> list:
        return self.call("images", p=pid).get("images", [])

    def img_bytes(self, pid: str, file: str, thumb: bool = False) -> bytes:
        out = self.call("img", p=pid, f=file, t=(1 if thumb else None))
        return base64.b64decode(out["b64"])

    def ingest(self, pid: str, png_path: Path, *, orig: str, gen: str, prompt: str,
               refs_used: list | None = None, parent: str | None = None,
               accepted: int = 0, seq: int | None = None) -> dict:
        data = png_path.read_bytes()
        return self.call(
            "ingest", files={"file": (orig, data)}, p=pid, orig=orig, gen=gen,
            prompt=prompt, parent=parent, accepted=accepted, seq=seq,
            refs_used=json.dumps(refs_used) if refs_used else None,
        )

    def qascan(self, pid: str, file: str) -> dict:
        return self.call("qascan", p=pid, f=file)

    def write_decisions(self, pid: str, decisions: list) -> dict:
        return self.call("write", p=pid, decisions=json.dumps(decisions))

    def flag(self, pid: str, file: str, defect: str, note: str = "", src: str = "gate") -> dict:
        return self.call("flag", p=pid, f=file, defect=defect, note=note,
                         by="bakeoff", src=src)

    def push_yield(self, stats: dict) -> dict:
        """Requires the do=yield verb on the live bridge (deployed with this lane)."""
        return self.call("yield", stats=json.dumps(stats))


def _multipart(fields: dict, files: dict) -> tuple[bytes, str]:
    boundary = "----bakeoff" + uuid.uuid4().hex
    out = bytearray()
    for k, v in fields.items():
        out += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n"
                f"{v}\r\n").encode()
    for k, (fname, data) in files.items():
        ctype = mimetypes.guess_type(fname)[0] or "application/octet-stream"
        out += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"; "
                f"filename=\"{fname}\"\r\nContent-Type: {ctype}\r\n\r\n").encode()
        out += data + b"\r\n"
    out += f"--{boundary}--\r\n".encode()
    return bytes(out), f"multipart/form-data; boundary={boundary}"
