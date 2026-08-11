#!/usr/bin/env python3
"""margo-full production driver utilities (state, downloads, sheets, ingest).

The Claude session is the generation driver (Higgsfield MCP); this script does
everything deterministic around it:

  python3 drive.py record <beat> <round> <job_id> [<job_id>...]   # log submitted jobs
  python3 drive.py urls <beat>                # list jobs still lacking a file
  python3 drive.py fetch <beat> <job_id> <url>  # download one result
  python3 drive.py sheet <beat> [<beat>...]   # contact sheet(s) -> sheets/<beat>.jpg
  python3 drive.py pair <beat> <v1> <v2> [...]  # finalist composite -> sheets/<beat>-final.jpg
  python3 drive.py winner <beat> <variant> [--notes "..."]  # mark winner + ingest to board
  python3 drive.py status                     # per-beat rollup
"""
import json, sys, os, subprocess, time, fcntl, contextlib
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[3]
sys.path.insert(0, str(ROOT / "runners/bakeoff"))
SHEET = json.loads((ROOT / "runners/bakeoff/margo-full-beats.json").read_text())
BEATS = {b["id"]: b for b in SHEET["beats"]}
ORDER = [b["id"] for b in SHEET["beats"]]
STATE_F = RUN / "state.json"

LOCK_F = RUN / ".state.lock"

@contextlib.contextmanager
def locked():
    """Hold an exclusive lock across a full read-modify-write of state.json.

    Multiple driver sessions run against this one file; without this, two
    concurrent load/save pairs silently lose one side's writes."""
    LOCK_F.touch(exist_ok=True)
    with open(LOCK_F, "r+") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)

def _load():
    return json.loads(STATE_F.read_text()) if STATE_F.exists() else {"beats": {}, "spend_notes": []}

def _save(s):
    tmp = STATE_F.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(s, indent=1))
    os.replace(tmp, STATE_F)

def _bs(s, beat):
    return s["beats"].setdefault(beat, {"jobs": {}, "winner": None, "rounds": {}})

def record(beat, rnd, job_ids):
    s = _load(); b = _bs(s, beat)
    for j in job_ids:
        b["jobs"].setdefault(j, {"round": rnd, "file": None})
    b["rounds"][str(rnd)] = b["rounds"].get(str(rnd), 0) + len(job_ids)
    _save(s); print(f"{beat}: recorded {len(job_ids)} jobs (round {rnd}); total {len(b['jobs'])}")

def fetch(beat, job_id, url):
    s = _load(); b = _bs(s, beat)
    d = RUN / "variants" / beat; d.mkdir(parents=True, exist_ok=True)
    n = sum(1 for j in b["jobs"].values() if j.get("file")) + 1
    out = d / f"v{n:02d}-{job_id[:8]}.png"
    subprocess.run(["curl", "-sf", "-o", str(out), url], check=True)
    b["jobs"].setdefault(job_id, {"round": 0})["file"] = out.name
    _save(s); print(out.name)

def fetchroll(beat, sample_url):
    """Derive result URLs for every un-fetched job of this beat from one sample URL
    (all jobs submitted in the same call share the URL timestamp prefix)."""
    import re, urllib.request
    s = _load(); b = _bs(s, beat)
    m = re.match(r"(.*/hf_\d{8}_\d{6}_)[0-9a-f-]+(\.png)$", sample_url)
    if not m: print("bad sample url"); return
    pre, suf = m.group(1), m.group(2)
    d = RUN / "variants" / beat; d.mkdir(parents=True, exist_ok=True)
    n = sum(1 for j in b["jobs"].values() if j.get("file"))
    ok = miss = 0
    for job_id, meta in sorted(b["jobs"].items(), key=lambda kv: kv[1]["round"]):
        if meta.get("file"): continue
        url = pre + job_id + suf
        try:
            data = urllib.request.urlopen(url, timeout=60).read()
        except Exception:
            miss += 1; print(f"  MISS {job_id[:8]} (different roll timestamp or not done)"); continue
        n += 1
        out = d / f"v{n:02d}-{job_id[:8]}.png"
        out.write_bytes(data)
        meta["file"] = out.name; ok += 1
    _save(s); print(f"{beat}: fetched {ok}, missed {miss}, files now {n}")

def sheet(beats):
    from PIL import Image, ImageDraw
    for beat in beats:
        d = RUN / "variants" / beat
        files = sorted(d.glob("v*.png"))
        if not files: print(f"{beat}: no variants"); continue
        TW = 300
        thumbs = []
        for f in files:
            im = Image.open(f).convert("RGB")
            im.thumbnail((TW, TW * 2))
            thumbs.append((f.name.split("-")[0], im))
        cols = 4; rows = (len(thumbs) + cols - 1) // cols
        ch = max(t.size[1] for _, t in thumbs) + 22
        out = Image.new("RGB", (cols * (TW + 8) + 8, rows * (ch + 8) + 8), (24, 24, 24))
        dr = ImageDraw.Draw(out)
        for i, (label, t) in enumerate(thumbs):
            x = 8 + (i % cols) * (TW + 8); y = 8 + (i // cols) * (ch + 8)
            out.paste(t, (x, y + 20))
            dr.text((x + 2, y + 2), label, fill=(255, 220, 80))
        sd = RUN / "sheets"; sd.mkdir(exist_ok=True)
        p = sd / f"{beat}.jpg"; out.save(p, quality=88)
        print(p)

def pair(beat, variants):
    from PIL import Image, ImageDraw
    d = RUN / "variants" / beat
    ims = []
    for v in variants:
        f = next(iter(d.glob(f"{v}-*.png")))
        im = Image.open(f).convert("RGB"); im.thumbnail((640, 1280))
        ims.append((v, im))
    W = sum(i.size[0] for _, i in ims) + 8 * (len(ims) + 1)
    H = max(i.size[1] for _, i in ims) + 30
    out = Image.new("RGB", (W, H), (24, 24, 24)); dr = ImageDraw.Draw(out)
    x = 8
    for v, im in ims:
        dr.text((x + 2, 2), v, fill=(255, 220, 80)); out.paste(im, (x, 24)); x += im.size[0] + 8
    sd = RUN / "sheets"; sd.mkdir(exist_ok=True)
    p = sd / f"{beat}-final.jpg"; out.save(p, quality=90)
    print(p)

def winner(beat, variant, notes=""):
    from bridge_client import Bridge
    s = _load(); b = _bs(s, beat)
    d = RUN / "variants" / beat
    f = next(iter(d.glob(f"{variant}-*.png")))
    job8 = f.stem.split("-")[1]
    job = next((j for j in b["jobs"] if j.startswith(job8)), job8)
    bd = BEATS[beat]
    br = Bridge()
    seq = ORDER.index(beat)
    orig = f"{beat}-{variant}.png"
    out = br.ingest("margo-full", f, orig=orig, gen=job,
                    prompt=bd["fullPrompt"], seq=seq)
    # do=ingest only returns "file" on its dedupe path; normally it returns
    # {ok,count,group}. Resolve the stored name by looking the orig back up,
    # newest first — without this, write_decisions/annotate got file=None and
    # silently no-opped, leaving every ingest unrated + unaccepted.
    fname = out.get("file")
    if not fname:
        cands = [m for m in br.images("margo-full") if m.get("orig") == orig]
        if not cands:
            raise SystemExit(f"{beat}: ingest ok but '{orig}' not found on board")
        fname = sorted(cands, key=lambda m: m.get("ts", 0))[-1]["file"]
    br.write_decisions("margo-full", [{"file": fname, "accepted": True, "rating": "good",
                                       "addtags": ["bakeoff", "judge-pick"]}])
    if notes:
        br.call("annotate", p="margo-full", notes=json.dumps(
            [{"file": fname, "verdict": "pass", "notes": notes[:800], "src": "bakeoff-judge"}]))
    b["winner"] = {"variant": variant, "job": job, "board_file": fname, "notes": notes, "ts": int(time.time())}
    _save(s); print(f"{beat}: winner {variant} ({job8}) -> board {fname}")

def status():
    s = _load()
    done = [k for k, v in s["beats"].items() if v.get("winner")]
    print(f"winners {len(done)}/{len(ORDER)}")
    for bid in ORDER:
        v = s["beats"].get(bid)
        if not v: continue
        w = v.get("winner")
        nf = sum(1 for j in v["jobs"].values() if j.get("file"))
        print(f"  {bid}: jobs={len(v['jobs'])} files={nf} winner={w['variant'] if w else '-'}")

if __name__ == "__main__":
    a = sys.argv[1:]
    cmd = a[0]
    if cmd == "record":
        with locked(): record(a[1], int(a[2]), a[3:])
    elif cmd == "fetchroll":
        with locked(): fetchroll(a[1], a[2])
    elif cmd == "fetch":
        with locked(): fetch(a[1], a[2], a[3])
    elif cmd == "sheet": sheet(a[1:])
    elif cmd == "pair": pair(a[1], a[2:])
    elif cmd == "winner":
        notes = ""
        args = a[1:]
        if "--notes" in args:
            i = args.index("--notes"); notes = args[i + 1]; args = args[:i]
        with locked(): winner(args[0], args[1], notes)
    elif cmd == "status": status()
    else: print(__doc__)
