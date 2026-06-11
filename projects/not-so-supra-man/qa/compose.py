#!/usr/bin/env python3
"""LAYER 0+1: the ONLY legal source of generation prompts. Emits the final
single-line prompt + attach list + aspect, and writes a receipt — or REFUSES.

Freehanding prompts is banned (CLAUDE.md protocol). Run from project root.

  python3 qa/compose.py --job sheet:deedee-t8-destroya
  python3 qa/compose.py --job sheet:dana-t9-ANCHOR-SWAP --pass pass_1
  python3 qa/compose.py --job page:p20-01

Receipts land in qa/receipts/<job>.receipt.json (consumed by audit + bank).
"""
import argparse, hashlib, json, os, re, sys

STYLE = ("Photorealistic 3D CGI render, DAZ Studio Iray render-engine look, photoreal CGI. "
         "NOT illustrated, NOT anime, NOT cartoon, NOT 2D.")
NEG = "No text, no words, no logos, no speech bubbles. No extra limbs, no extra hands."
APPEARANCE_WORDS = re.compile(r"\b(blonde?|curly|hazel|ice-blue|bald|freckl\w*|square-?jaw\w*|"
                              r"chin-length|bangs|jet-black|black-?bob)\b", re.I)

def refuse(msgs):
    print("COMPOSE REFUSED:")
    for m in msgs: print(f"  ✗ {m}")
    sys.exit(1)

def receipt(job, kind, prompt, attach, aspect, flags):
    os.makedirs("qa/receipts", exist_ok=True)
    body = {"job": job, "kind": kind, "prompt_sha": hashlib.sha256(prompt.encode()).hexdigest(),
            "attach": attach, "aspect": aspect, "flags": flags}
    path = f"qa/receipts/{job.replace(':','_')}.receipt.json"
    json.dump(body, open(path, "w"), indent=1)
    return path

def ledger():
    return json.load(open("references/ref-ledger.json"))

def compose_sheet(sheet_id, pass_key):
    specs = json.load(open("references/turnaround-specs.json"))
    spec = next((s for s in specs["sheets"] if s["id"] == sheet_id), None)
    if not spec: refuse([f"unknown sheet '{sheet_id}'"])
    if "pass_1" in spec:  # multi-pass (anchor swap)
        if not pass_key or pass_key not in spec: refuse([f"sheet '{sheet_id}' needs --pass pass_1|pass_2|pass_3_turnaround"])
        sub = spec[pass_key]
        prompt, attach, aspect = sub["prompt"], sub["attach_order"], sub.get("aspect", "16:9")
        gate = sub.get("gate", spec.get("gate", ""))
    else:
        prompt, attach, aspect = spec["prompt"], spec["attach"], "16:9"
        gate = spec.get("gate", "")
    errs = []
    led = ledger()
    # self-heal: if this wardrobe state's turnaround ALREADY exists (spec save path is in the
    # ledger), prose-bootstrap is illegal — regenerate with pointer language instead.
    save_path = spec.get("save") or (spec.get(pass_key, {}).get("save") if pass_key else None)
    bootstrap = True
    for ch in led["characters"].values():
        for k, v in ch.items():
            if k.startswith("turnaround") and isinstance(v, dict) and save_path and v.get("disk") == save_path:
                bootstrap = False
    if not bootstrap:
        prompt = ("Character turnaround model sheet: the SAME character, outfit, damage state, muscle size "
                  "and height EXACTLY as the attached turnaround reference, four views, scale silhouette and "
                  "grid as in the reference. " + STYLE + " " + NEG)
        attach = [f"EXISTING turnaround for {sheet_id} (ledger)"] + attach
    if len(attach) < 2: errs.append(f"D1: sheet needs >=2 refs, has {len(attach)}")
    if "silhouette" not in prompt.lower(): errs.append("D7: no scale-silhouette sentence")
    if re.search(r"\btowering|giantess\b", prompt, re.I) and "NOT a giantess" not in prompt:
        errs.append("D7: scale-ambiguous language without clamp")
    if errs: refuse(errs)
    line = prompt if prompt.endswith(".") else prompt + "."
    if "No text" not in line: line += " " + NEG
    return line, attach, aspect, {"bootstrap": bootstrap, "gate": gate, "tier_job": "t9" in sheet_id.lower()}

def compose_page(panel_id):
    shot = json.load(open("shotlist.json"))
    panel = None
    for pg in shot["pages"]:
        for p in pg["panels"]:
            if p["panel_id"] == panel_id: panel = p
    if not panel: refuse([f"unknown panel '{panel_id}'"])
    errs = []
    led = ledger()
    plan = json.load(open("pages-plan.json"))
    entry = next((e for e in plan["pages"] if e["id"] == panel_id), None)
    if not entry: refuse([f"no pages-plan entry for {panel_id}"])
    staging_path = f"qa/staging/{panel_id}.json"
    chars = panel.get("characters", [])
    contact = len(chars) >= 2
    if contact and not os.path.exists(staging_path):
        refuse([f"D9/D13: multi-character page requires {staging_path} "
                "(per-character position/orientation + per-HAND accounting + total-hands line); author it first"])
    staging = json.load(open(staging_path)) if os.path.exists(staging_path) else {}
    # mechanical v4 assembly — appearance is pointer-only BY CONSTRUCTION
    refs, characters = [], []
    for i, c in enumerate(chars):
        ch = led["characters"].get(c, {})
        t_keys = [k for k in ch if k.startswith("turnaround")]
        if not ch.get("face"): errs.append(f"D1: no face ref in ledger for {c}")
        if not t_keys: errs.append(f"D4/D11: no wardrobe turnaround in ledger for {c} — generate the sheet first")
        refs += [f"face:{c}", f"turnaround:{c}:{t_keys[0] if t_keys else '?'}"]
        characters.append({
            "id": c,
            "appearance": f"EXACTLY the person from the attached face card and turnaround for {c} — same face, hair, outfit, damage state, muscle size and height. No appearance changes.",
            "position": staging.get(c, {}).get("position", "<MISSING>"),
            "pose": staging.get(c, {}).get("pose", "<MISSING>"),
            "expression": staging.get(c, {}).get("expression", "<MISSING>"),
        })
        if contact and "<MISSING>" in json.dumps(characters[-1]): errs.append(f"D12: staging stanza incomplete for {c}")
    if panel.get("location") and panel["location"] not in ("lab-exterior",):
        refs.append(f"scene:{panel['location']}:{entry['aspect']}")
    if panel_id not in ("p01-01", "p02-01"): refs.append("prior:last-accepted")
    tiers = panel.get("muscle_size_tier") or {}
    t9 = any(isinstance(t, int) and t >= 9 for t in tiers.values())
    if t9: refs.append("anchor:lana")
    body = {"instruction": "Generate one image.", "style": STYLE,
            "camera": entry.get("camera", panel.get("camera")),
            "scene": {"environment": "EXACTLY the attached scene reference", "continuity": "continue from the attached previous panel"},
            "characters": characters,
            "spatial_rules": staging.get("spatial_rules", ["<MISSING>"] if contact else []),
            "action": panel.get("action", ""),
            "lighting": staging.get("lighting", panel.get("time_of_day", "")),
            "negative": NEG.lower()}
    if any(isinstance(t, int) and t >= 4 for t in tiers.values()):
        body["size_rule"] = "muscle mass per the attached turnaround — height does NOT change"
    if errs: refuse(errs)
    return json.dumps(body, separators=(",", ":")), refs, entry["aspect"], {"bootstrap": False, "tier_job": t9}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--job", required=True, help="sheet:<id> | page:<panel_id>")
    ap.add_argument("--pass", dest="pass_key", default=None)
    a = ap.parse_args()
    kind, _, ident = a.job.partition(":")
    if kind == "sheet": prompt, attach, aspect, flags = compose_sheet(ident, a.pass_key)
    elif kind == "page": prompt, attach, aspect, flags = compose_page(ident)
    else: refuse([f"unknown job kind '{kind}'"])
    rpath = receipt(a.job, kind, prompt, attach, aspect, flags)
    print(f"COMPOSE OK [{a.job}]  aspect={aspect}  receipt={rpath}")
    print("ATTACH (in order):")
    for r in attach: print(f"  - {r}")
    print("PROMPT (paste verbatim, single line):")
    print(prompt)

if __name__ == "__main__":
    main()
