#!/usr/bin/env python3
"""LAYER 0+1 (manila-bay-rising / Chapter 1): the ONLY legal source of generation
prompts. Emits the final prompt + attach list + aspect, and writes a receipt — or
REFUSES. Freehanding prompts is banned (CLAUDE.md protocol). Run from project root.

  python3 qa/compose.py --job sheet:hae-won-face
  python3 qa/compose.py --job sheet:cel-t2
  python3 qa/compose.py --job page:p05-01

Receipts land in qa/receipts/<job>.receipt.json (consumed by audit + bank).

Ch1 scope: max muscle tier 3, three characters (hae-won, cel, dr-santos), ten
locations, single-rung scene ladders. No anchor-swap / no t9 / no torn multi-pass
machinery — that is later-chapter work and is intentionally absent here.
"""
import argparse, hashlib, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import integrity; integrity.verify_or_die()  # LAYER 8

STYLE = ("Photorealistic 3D CGI render, DAZ Studio Iray render-engine look, photoreal CGI. "
         "NOT illustrated, NOT anime, NOT cartoon, NOT 2D.")
NEG = "No text, no words, no logos, no speech bubbles. No extra limbs, no extra hands."
NEG_PAGE_BLEED = " No mannequin, no reference silhouette figure, no grid lines, no model-sheet layout."

def refuse(msgs):
    print("COMPOSE REFUSED:")
    for m in msgs: print(f"  ✗ {m}")
    sys.exit(1)

def receipt(job, kind, prompt, attach, aspect, flags):
    os.makedirs("qa/receipts", exist_ok=True)
    body = {"job": job, "kind": kind, "prompt_sha": hashlib.sha256(prompt.encode()).hexdigest(),
            "attach": attach, "aspect": aspect, "flags": flags,
            "gates_fingerprint": integrity.manifest_fingerprint()}
    path = f"qa/receipts/{job.replace(':','_')}.receipt.json"
    json.dump(body, open(path, "w"), indent=1)
    return path

def ledger():
    return json.load(open("references/ref-ledger.json"))

# ---------------------------------------------------------------- SHEETS
def compose_sheet(sheet_id):
    specs = json.load(open("references/turnaround-specs.json"))
    spec = next((s for s in specs["sheets"] if s["id"] == sheet_id), None)
    if not spec: refuse([f"unknown sheet '{sheet_id}'"])
    genesis = bool(spec.get("genesis"))
    attach = list(spec.get("attach", []))
    aspect = spec.get("aspect", "16:9")
    prompt = spec["prompt"]
    errs = []
    # D1: non-genesis sheets must carry >=2 refs (face + prior rung / lineup).
    # genesis face cards legitimately bootstrap identity in prose with 0-1 refs.
    if not genesis and len(attach) < 2:
        errs.append(f"D1: non-genesis sheet needs >=2 refs, has {len(attach)}")
    if not genesis and "silhouette" not in prompt.lower():
        errs.append("D7: non-genesis sheet missing the scale-silhouette sentence")
    if re.search(r"\b(towering|giantess)\b", prompt, re.I) and "NOT a giantess" not in prompt:
        errs.append("D7: scale-ambiguous language without clamp")
    if errs: refuse(errs)
    line = prompt if prompt.endswith(".") else prompt + "."
    line += " " + STYLE + " " + NEG
    return line, attach, aspect, {"genesis": genesis, "tier_job": False, "bootstrap": genesis}

# ---------------------------------------------------------------- SCENES
def compose_scene(location):
    """scene:<location> — DAZ-convert the gathered internet establishing photo into
    a DAZ3D location render that becomes the single-rung scene ref for that location."""
    specs = json.load(open("references/turnaround-specs.json"))
    spec = next((s for s in specs.get("scenes", []) if s["id"] == location), None)
    if not spec: refuse([f"unknown scene '{location}' (add it to turnaround-specs.json scenes[])"])
    attach = list(spec.get("attach", []))
    if len(attach) < 1:
        refuse([f"D8: scene '{location}' must attach >=1 source photo to DAZ-convert, has {len(attach)}"])
    aspect = spec.get("aspect", "16:9")
    line = spec["prompt"]
    line = line if line.endswith(".") else line + "."
    line += " " + STYLE + " " + NEG
    return line, attach, aspect, {"genesis": True, "tier_job": False, "bootstrap": True, "scene": True}

# ---------------------------------------------------------------- PAGES
def find_panel(panel_id):
    shot = json.load(open("shotlist.json"))
    for pg in shot["pages"]:
        for p in pg["panels"]:
            if p["panel_id"] == panel_id: return p
    return None

def state_for(char, panel):
    cs = panel.get("costume_state", "") or ""
    for seg in cs.split(";"):
        seg = seg.strip()
        if seg.lower().startswith(char + ":"):
            return seg.partition(":")[2].strip().lower()
    return ""

def compose_page(panel_id):
    panel = find_panel(panel_id)
    if not panel: refuse([f"unknown panel '{panel_id}'"])
    errs = []
    led = ledger()
    plan = json.load(open("pages-plan.json"))
    entry = next((e for e in plan["pages"] if e["id"] == panel_id), None)
    if not entry: refuse([f"no pages-plan entry for {panel_id}"])

    chars = panel.get("characters", [])
    tiers = panel.get("muscle_size_tier") or {}
    contact = len(chars) >= 2
    staging_path = f"qa/staging/{panel_id}.json"
    if contact and not os.path.exists(staging_path):
        refuse([f"D9/D13: multi-character page requires {staging_path} "
                "(per-character position/pose/expression + spatial_rules incl. a total-hands line); author it first"])
    staging = json.load(open(staging_path)) if os.path.exists(staging_path) else {}

    # PRIOR CHECK: continuity_refs must be banked WITH chain in pages-log
    log = json.load(open("pages-log.json")) if os.path.exists("pages-log.json") else {"done": {}}
    for ref_id in panel.get("continuity_refs", []) or []:
        rec = log.get("done", {}).get(ref_id)
        if not rec or "chain" not in rec:
            errs.append(f"D1: continuity ref {ref_id} is not banked-with-chain yet — generate pages in order")

    refs, characters = [], []
    for c in chars:
        ch = led["characters"].get(c, {})
        if not ch.get("face"):
            errs.append(f"D1: no face ref in ledger for {c} — generate the sheet first")
        tier = tiers.get(c) if isinstance(tiers.get(c), int) else 1
        if tier < 1: tier = 1
        tkey = f"turnaround_t{tier}"
        if not ch.get(tkey):
            errs.append(f"D4/D11: tier-{tier} turnaround ({tkey}) not in ledger for {c} — generate the sheet first")
        refs += [f"face:{c}", f"turnaround:{c}:t{tier}"]
        cstanza = {
            "id": c,
            "appearance": (f"EXACTLY the person from the attached face card and tier-{tier} turnaround for {c} — "
                           "same face, hair, outfit, muscle size and height. No appearance changes."),
            "position": staging.get(c, {}).get("position", "<MISSING>") if contact else "as the sole figure in frame",
            "pose": staging.get(c, {}).get("pose", "<MISSING>") if contact else "natural to the action",
            "expression": staging.get(c, {}).get("expression", "<MISSING>") if contact else "read from the action",
        }
        characters.append(cstanza)
        if contact and "<MISSING>" in json.dumps(cstanza):
            errs.append(f"D12: staging stanza incomplete for {c}")

    # SCENE LADDER (single-rung for Ch1): one banked scene ref per location.
    loc = panel.get("location")
    if loc:
        rung = (led.get("scene_ladders", {}).get(loc, {}) or {})
        if not rung or not rung.get("flow_id"):
            errs.append(f"D8: scene ref '{loc}' not banked in scene_ladders — generate/bank it first")
        refs.append(f"scene:{loc}")

    for ref_id in panel.get("continuity_refs", []) or []:
        refs.append(f"prior:{ref_id}")

    action = panel.get("action", "")
    spatial = list(staging.get("spatial_rules", ["exactly one person in the image"] if (chars and not contact) else []))
    body = {
        "instruction": "Generate one image.",
        "style": STYLE,
        "camera": entry.get("camera", panel.get("camera")),
        "scene": {"environment": "EXACTLY the attached scene reference",
                  "continuity": ("continue from the attached previous panel"
                                 if panel.get("continuity_refs") else "establishing beat")},
        "characters": characters,
        "spatial_rules": spatial,
        "action": action,
        "lighting": staging.get("lighting", panel.get("time_of_day", "")),
        "negative": (NEG + NEG_PAGE_BLEED).lower(),
    }

    # tier>=2: size rule + strain coverage insurance
    big = any(isinstance(t, int) and t >= 2 for t in tiers.values())
    if big:
        bigtier = max(t for t in tiers.values() if isinstance(t, int))
        body["size_rule"] = (f"muscle mass and fullness per the attached tier-{bigtier} turnaround — "
                             "height changes ONLY per the tier lineup, never beyond it")
    cs = panel.get("costume_state", "")
    if re.search(r"strain|stretch|tight|seam", cs, re.I):
        body["spatial_rules"].append("coverage of chest and hips fully intact")

    if errs: refuse(errs)
    prompt = json.dumps(body, separators=(",", ":"))
    return prompt, refs, entry["aspect"], {"genesis": False, "tier_job": False, "bootstrap": False}

# ---------------------------------------------------------------- CLI
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--job", required=True, help="sheet:<id> | page:<panel_id>")
    a = ap.parse_args()
    kind, _, ident = a.job.partition(":")
    if kind == "sheet": prompt, attach, aspect, flags = compose_sheet(ident)
    elif kind == "scene": prompt, attach, aspect, flags = compose_scene(ident)
    elif kind == "page": prompt, attach, aspect, flags = compose_page(ident)
    else: refuse([f"unknown job kind '{kind}'"])
    rpath = receipt(a.job, kind, prompt, attach, aspect, flags)
    print(f"COMPOSE OK [{a.job}]  aspect={aspect}  receipt={rpath}")
    print(f"VERIFY PILL BEFORE SUBMIT: model=Nano Banana 2  count=x4  aspect={aspect}")
    print("ATTACH (in order):")
    for r in attach: print(f"  - {r}")
    print("PROMPT (paste verbatim, single line):")
    print(prompt)

if __name__ == "__main__":
    main()
