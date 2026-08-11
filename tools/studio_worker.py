#!/usr/bin/env python3
"""
studio_worker.py — transport layer for the 3DMC comic-creator worker.

A live Claude session on the Mac runs the generation (Flow via Chrome MCP,
Higgsfield via its MCP). THIS script just does the queue HTTP plumbing so the
session never has to hand-roll multipart/auth:

    pull      claim the next open job for this backend/account   -> prints job JSON
    progress  heartbeat + status/progress; relays stop+comments  -> prints {stopRequested, comments,...}
    ingest    push a finished panel image into the gallery (idempotent via --result-id)

Config (no secret on the command line): ~/.config/studio-worker/config.json
    { "url": "https://3dmusclecomics.com/studio/bridge.php",
      "key": "<paste the bridge key from Studio -> Flow import>",
      "account": "growcomics" }
Env overrides: STUDIO_URL, STUDIO_KEY, STUDIO_ACCOUNT, STUDIO_WORKER_ID.

The key is sent ONLY in the X-Bridge-Key header (never the URL), matching the
server's header-only enforcement for queue verbs.
"""
import argparse, json, os, sys, mimetypes, uuid
from pathlib import Path
from urllib import request, error

CONFIG_PATH = Path(os.path.expanduser("~/.config/studio-worker/config.json"))

def load_cfg():
    cfg = {}
    if CONFIG_PATH.is_file():
        try: cfg = json.loads(CONFIG_PATH.read_text())
        except Exception as e: sys.exit(f"config read error: {e}")
    cfg["url"]     = os.environ.get("STUDIO_URL",     cfg.get("url", "https://3dmusclecomics.com/studio/bridge.php"))
    cfg["key"]     = os.environ.get("STUDIO_KEY",     cfg.get("key", ""))
    cfg["account"] = os.environ.get("STUDIO_ACCOUNT", cfg.get("account", ""))
    cfg["worker"]  = os.environ.get("STUDIO_WORKER_ID", cfg.get("worker", "mac-" + uuid.getnode().__str__()[-6:]))
    if not cfg["key"]:
        sys.exit("no bridge key — set it in ~/.config/studio-worker/config.json or $STUDIO_KEY")
    return cfg

def post_form(cfg, fields):
    data = "&".join(f"{request.quote(str(k))}={request.quote(str(v))}" for k, v in fields.items() if v is not None).encode()
    req = request.Request(cfg["url"], data=data, method="POST",
                          headers={"X-Bridge-Key": cfg["key"], "Content-Type": "application/x-www-form-urlencoded"})
    try:
        with request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())
    except error.HTTPError as e:
        return {"ok": False, "error": f"http {e.code}", "body": e.read().decode()[:300]}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def post_multipart(cfg, fields, file_path):
    boundary = "----studioworker" + uuid.uuid4().hex
    fp = Path(file_path)
    if not fp.is_file(): return {"ok": False, "error": f"no file {file_path}"}
    ctype = mimetypes.guess_type(fp.name)[0] or "application/octet-stream"
    body = bytearray()
    for k, v in fields.items():
        if v is None: continue
        body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode()
    body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{fp.name}\"\r\nContent-Type: {ctype}\r\n\r\n".encode()
    body += fp.read_bytes() + b"\r\n" + f"--{boundary}--\r\n".encode()
    req = request.Request(cfg["url"], data=bytes(body), method="POST",
                          headers={"X-Bridge-Key": cfg["key"], "Content-Type": f"multipart/form-data; boundary={boundary}"})
    try:
        with request.urlopen(req, timeout=120) as r:
            return json.loads(r.read().decode())
    except error.HTTPError as e:
        return {"ok": False, "error": f"http {e.code}", "body": e.read().decode()[:300]}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def main():
    ap = argparse.ArgumentParser(description="3DMC comic-creator worker transport")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("pull", help="claim the next open job")
    p.add_argument("--backend", required=True, choices=["flow", "higgsfield"])
    p.add_argument("--account", default=None, help="Flow account (defaults to config)")

    p = sub.add_parser("progress", help="heartbeat + status; returns stop + new comments")
    p.add_argument("--job", required=True)
    p.add_argument("--status", default=None, choices=["running", "blocked", "needs_login", "done", "error", "stopped"])
    p.add_argument("--done", type=int, default=None)
    p.add_argument("--total", type=int, default=None)
    p.add_argument("--note", default=None)
    p.add_argument("--comment-cursor", type=int, default=0)

    p = sub.add_parser("ingest", help="push a finished panel image into the gallery")
    p.add_argument("--job", required=True)
    p.add_argument("--project", required=True)
    p.add_argument("--file", required=True)
    p.add_argument("--result-id", default=None, help="stable id so a retry can't double-ingest")
    p.add_argument("--seq", type=int, default=None)
    p.add_argument("--orig", default=None)

    args = ap.parse_args()
    cfg = load_cfg()

    if args.cmd == "pull":
        out = post_form(cfg, {"do": "queue_pull", "backend": args.backend,
                              "account": args.account if args.account is not None else cfg["account"],
                              "worker_id": cfg["worker"]})
    elif args.cmd == "progress":
        out = post_form(cfg, {"do": "queue_progress", "job": args.job, "status": args.status,
                              "done": args.done, "total": args.total, "note": args.note,
                              "comment_cursor": args.comment_cursor, "worker_id": cfg["worker"]})
    elif args.cmd == "ingest":
        out = post_multipart(cfg, {"do": "ingest", "p": args.project, "job": args.job,
                                   "result_id": args.result_id or str(uuid.uuid4()),
                                   "seq": args.seq, "orig": args.orig or Path(args.file).name}, args.file)
    print(json.dumps(out))
    sys.exit(0 if out.get("ok") else 1)

if __name__ == "__main__":
    main()
