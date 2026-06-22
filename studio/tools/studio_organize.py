#!/usr/bin/env python3
"""Studio organizer — pull a Comic Studio project's draft variants, build a
contact sheet for a Claude Code session to judge, and push ratings / grouping /
winners back. The mechanics live here; the *judgment* (which variant is best) is
done by Claude viewing the contact sheet (and full-res for close calls), exactly
like comic-folder-organizer. See skills/studio-organize/SKILL.md.

Usage:
  studio_organize.py list
  studio_organize.py pull  <project> [--full] [--out DIR]
  studio_organize.py push  <project> --decisions FILE.json [--cover FILE]

Auth: bridge key from $STUDIO_BRIDGE_KEY or ~/Documents/.3dmc-studio-bridge-key.
Endpoint: $STUDIO_BRIDGE or https://3dmusclecomics.com/studio/bridge.php
"""
import sys, os, re, json, base64, argparse, urllib.request, urllib.parse

BRIDGE = os.environ.get("STUDIO_BRIDGE", "https://3dmusclecomics.com/studio/bridge.php")
KEYFILE = os.path.expanduser("~/Documents/.3dmc-studio-bridge-key")

def _key():
    k = os.environ.get("STUDIO_BRIDGE_KEY")
    if k: return k.strip()
    try:
        return open(KEYFILE).read().strip()
    except OSError:
        sys.exit(f"no bridge key (set $STUDIO_BRIDGE_KEY or create {KEYFILE})")

def _get(params):
    params = dict(params); params["key"] = _key()
    with urllib.request.urlopen(BRIDGE + "?" + urllib.parse.urlencode(params), timeout=90) as r:
        return json.load(r)

def _post(fields):
    fields = dict(fields); fields["key"] = _key()
    req = urllib.request.Request(BRIDGE, data=urllib.parse.urlencode(fields).encode())
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.load(r)

def beat_ts(orig):
    m = re.search(r'_(\d{8}_\d{6})_', orig or "")
    return m.group(1) if m else ""

def suggest_group(img, ts_order):
    """Existing group wins; else group by generation timestamp -> 'Beat N'."""
    if img.get("group"): return img["group"]
    ts = beat_ts(img.get("orig", ""))
    return f"Beat {ts_order.index(ts)+1}" if ts in ts_order else "Ungrouped"

def cmd_list(a):
    for p in _get({"do": "projects"}).get("projects", []):
        print(f"  {p['id']:26} {p.get('name','')}  [{p.get('stage','')}/{p.get('status','')}]  cover={p.get('cover')}")

def build_contact(out, imgs, groups):
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print("  (PIL not installed — skipping contact sheet; view images individually)"); return None
    TW, TH, PAD, LBL = 260, 330, 8, 18
    order = list(groups.keys())
    maxc = max((len(v) for v in groups.values()), default=1)
    W = PAD + maxc * (TW + PAD)
    H = PAD + len(order) * (TH + LBL + PAD)
    sheet = Image.new("RGB", (W, H), (20, 21, 28)); d = ImageDraw.Draw(sheet)
    for r, g in enumerate(order):
        y = PAD + r * (TH + LBL + PAD)
        d.text((PAD, y), f"{g}", fill=(250, 250, 250))
        for c, im in enumerate(groups[g]):
            x = PAD + c * (TW + PAD); yy = y + LBL
            p = os.path.join(out, im["file"])
            if not os.path.exists(p): continue
            t = Image.open(p).convert("RGB"); w, h = t.size; sc = min(TW/w, TH/h)
            t = t.resize((int(w*sc), int(h*sc)))
            sheet.paste(t, (x + (TW-t.size[0])//2, yy + (TH-t.size[1])//2))
            d.rectangle([x, yy, x+TW, yy+16], fill=(0, 0, 0))
            d.text((x+3, yy+3), f"{im['file'][:10]}  ({im.get('rating','unrated')}{'*' if im.get('accepted') else ''})", fill=(255, 220, 120))
    path = os.path.join(out, "contact.png"); sheet.save(path); return path

def cmd_pull(a):
    d = _get({"do": "images", "p": a.project})
    if not d.get("ok"): sys.exit("pull failed: " + json.dumps(d))
    imgs = d["images"]
    out = a.out or f"/tmp/studio-{a.project}"
    os.makedirs(out, exist_ok=True)
    ts_order = sorted({beat_ts(x.get("orig", "")) for x in imgs if beat_ts(x.get("orig", ""))})
    for x in imgs:
        x["suggest_group"] = suggest_group(x, ts_order)
        r = _get({"do": "img", "p": a.project, "f": x["file"], **({} if a.full else {"t": "1"})})
        if r.get("ok"):
            open(os.path.join(out, x["file"]), "wb").write(base64.b64decode(r["b64"]))
    # group for the contact sheet
    groups = {}
    for x in imgs:
        groups.setdefault(x["suggest_group"], []).append(x)
    groups = dict(sorted(groups.items(), key=lambda kv: (kv[0] == "Ungrouped", int(re.search(r'(\d+)', kv[0]).group(1)) if re.search(r'(\d+)', kv[0]) else 9999)))
    json.dump({"project": a.project, "dir": out, "images": imgs}, open(os.path.join(out, "manifest.json"), "w"), indent=2)
    # decisions skeleton (groups pre-filled, ratings blank) for Claude to fill in
    skel = [{"file": x["file"], "group": x["suggest_group"], "rating": x.get("rating", "unrated"), "accepted": bool(x.get("accepted"))} for x in imgs]
    json.dump(skel, open(os.path.join(out, "decisions.json"), "w"), indent=2)
    sheet = build_contact(out, imgs, groups)
    print(f"pulled {len(imgs)} {'full-res' if a.full else 'thumb'} images -> {out}")
    if sheet: print(f"CONTACT SHEET (Read this): {sheet}")
    print(f"decisions skeleton: {os.path.join(out, 'decisions.json')}  (set winners: rating=good + accepted=true)")
    print(f"groups: " + ", ".join(f"{g}({len(v)})" for g, v in groups.items()))

def cmd_push(a):
    decs = json.load(open(a.decisions))
    f = {"do": "write", "p": a.project, "decisions": json.dumps(decs)}
    if a.cover: f["cover"] = a.cover
    print(_post(f))

def cmd_annotate(a):
    # notes file: [{file, caption?, defects?[], tier?, notes?, tags?[]}, ...]
    notes = json.load(open(a.notes))
    print(_post({"do": "annotate", "p": a.project, "notes": json.dumps(notes)}))

def main():
    ap = argparse.ArgumentParser(description="Comic Studio organizer bridge")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list").set_defaults(fn=cmd_list)
    p = sub.add_parser("pull"); p.add_argument("project"); p.add_argument("--full", action="store_true"); p.add_argument("--out"); p.set_defaults(fn=cmd_pull)
    p = sub.add_parser("push"); p.add_argument("project"); p.add_argument("--decisions", required=True); p.add_argument("--cover"); p.set_defaults(fn=cmd_push)
    p = sub.add_parser("annotate"); p.add_argument("project"); p.add_argument("--notes", required=True); p.set_defaults(fn=cmd_annotate)
    a = ap.parse_args(); a.fn(a)

if __name__ == "__main__":
    main()
