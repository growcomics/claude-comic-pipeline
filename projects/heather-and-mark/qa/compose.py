#!/usr/bin/env python3
"""LAYER 0+1: the ONLY legal source of generation prompts. Emits the final
single-line prompt + attach list + aspect, and writes a receipt — or REFUSES.

Freehanding prompts is banned (CLAUDE.md protocol). Run from project root.

  python3 qa/compose.py --job sheet:deedee-t8-destroya
  python3 qa/compose.py --job sheet:dana-t9-ANCHOR-SWAP --pass pass_1
  python3 qa/compose.py --job page:p20-01
  python3 qa/compose.py --job edit:009

Receipts land in qa/receipts/<job>.receipt.json (consumed by audit + bank).

v2 (user-blessed fix batch): costume-state->turnaround mapping, prior-panel
existence check (continuity_refs must be banked WITH chain), scene-ladder rung
enforcement by camera distance, anti-reference-bleed negatives, progressive
stage-direction rule, torn-state coverage insurance, pill-verify reminder.

v3 (owner-reviewed, heather-and-mark fix-pass): edit:<panel_id> job kind for
i2i retouch of an ALREADY-ACCEPTED panel — baked-lettering correction and/or a
narrow anatomy fix, sourced entirely from fix-jobs.json (project root). Unlike
sheet:/page:, this kind does not touch shotlist.json/ref-ledger.json — it
requires only a fix-jobs.json entry for the panel and the source panel file
itself. Composes the composition-lock + L19 scope-bounded re-lettering pattern
(skills/comic-production/references/cinematic-framing.md "Lighting-pass
fragments"; skills/comic-production/references/lessons-learned.md L19).
"""
import argparse, hashlib, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import integrity; integrity.verify_or_die()  # LAYER 8

STYLE = ("Photorealistic 3D CGI render, DAZ Studio Iray render-engine look, photoreal CGI. "
         "NOT illustrated, NOT anime, NOT cartoon, NOT 2D.")
NEG = "No text, no words, no logos, no speech bubbles. No extra limbs, no extra hands."
NEG_PAGE_BLEED = " No mannequin, no reference silhouette figure, no grid lines, no model-sheet layout."
# edit: jobs correct baked lettering, so — unlike NEG above — this does NOT ban text/bubbles.
NEG_EDIT = "No extra limbs, no extra hands, no new characters, no changes outside the corrected region."
CAMERA_DISTANCE = {
    "wide": "wide", "establish": "wide", "splash": "wide", "birds-eye": "wide",
    "full": "medium", "cowboy": "medium", "medium": "medium", "over-shoulder": "medium",
    "mcu": "close", "ecu": "close", "close": "close",
}
# L19 bubble-shape vocabulary (lessons-learned.md L19), keyed by substring match against
# a corrected_dialogue entry's bubble_type.
BUBBLE_SHAPE = {
    "shout": "JAGGED-EDGED starburst comic shout bubble with a bold 3-4 pixel black outline",
    "thought": "cloud-shaped thought bubble with a trail of small circles, bold 3-4 pixel black outline",
    "whisper": "rounded oval speech balloon with a DASHED bold 3-4 pixel black outline",
    "caption": "yellow rounded-corner caption rectangle with a bold 3-4 pixel black outline",
    "speech": "classic comic-book speech balloon — clean white rounded oval with a bold 3-4 pixel black outline",
}

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

def state_for(char, panel):
    """Pull this character's costume-state fragment from the panel's combined string."""
    cs = panel.get("costume_state", "") or ""
    short = char.split("-")[0] if char != "dee-dee" else "dee-dee"
    for seg in cs.split(";"):
        seg = seg.strip()
        if seg.lower().startswith(short + ":"):
            return seg.partition(":")[2].strip().lower()
    return cs.lower()

def pick_turnaround(char, ch_entry, panel, staging):
    override = staging.get(char, {}).get("turnaround_key")
    keys = [k for k in ch_entry if k.startswith("turnaround")]
    if override:
        if override in ch_entry: return override
        refuse([f"staging override turnaround_key '{override}' not in ledger for {char}"])
    if not keys: return None
    state = state_for(char, panel)
    tiers = panel.get("muscle_size_tier") or {}
    tier = tiers.get(char) if isinstance(tiers.get(char), int) else 0
    want = None
    if "corset" in state: want = "t8"
    elif "lab coat" in state: want = "t3"
    elif tier >= 7: want = "t9"
    elif re.search(r"torn|remnant|shred|tear|split", state): want = "torn"
    elif "suit" in state: want = "t6_suit"
    elif "blouse" in state and tier >= 4: want = "t4"
    elif "blouse" in state or "reporter" in state or (tier and tier <= 2): want = "t2"
    matches = [k for k in keys if want and want in k]
    if len(matches) == 1: return matches[0]
    refuse([f"D4: ambiguous turnaround for {char} (state='{state}', tier={tier}, "
            f"candidates={keys}) — set turnaround_key in the staging file"])

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

    # PRIOR CHECK: shotlist continuity_refs must be banked WITH a chain (v2 pages only count)
    log = json.load(open("pages-log.json")) if os.path.exists("pages-log.json") else {"done": {}}
    for ref_id in panel.get("continuity_refs", []) or []:
        rec = log.get("done", {}).get(ref_id)
        if not rec or "chain" not in rec:
            errs.append(f"D1: continuity ref {ref_id} is not banked-with-chain yet — generate pages in order")

    refs, characters = [], []
    for c in chars:
        ch = led["characters"].get(c, {})
        if not ch.get("face"): errs.append(f"D1: no face ref in ledger for {c}")
        tkey = pick_turnaround(c, ch, panel, staging) if ch else None
        if not tkey: errs.append(f"D4/D11: no wardrobe turnaround in ledger for {c} — generate the sheet first")
        refs += [f"face:{c}", f"turnaround:{c}:{tkey or '?'}"]
        characters.append({
            "id": c,
            "appearance": f"EXACTLY the person from the attached face card and turnaround for {c} — same face, hair, outfit, damage state, muscle size and height. No appearance changes.",
            "position": staging.get(c, {}).get("position", "<MISSING>"),
            "pose": staging.get(c, {}).get("pose", "<MISSING>"),
            "expression": staging.get(c, {}).get("expression", "<MISSING>"),
        })
        if contact and "<MISSING>" in json.dumps(characters[-1]): errs.append(f"D12: staging stanza incomplete for {c}")

    # SCENE LADDER: rung must match camera distance AND exist in the ledger (D8)
    loc = panel.get("location")
    if loc and loc not in ("lab-exterior",):
        cam = (entry.get("camera") or panel.get("camera") or "").lower()
        want = next((cls for kw, cls in CAMERA_DISTANCE.items() if kw in cam), "medium")
        rung = (led.get("scene_ladders", {}).get(loc, {}) or {}).get(want, {})
        if not rung or not rung.get("flow_id"):
            errs.append(f"D8: scene ladder rung '{loc}:{want}' not banked — generate it first (chained from the wide)")
        refs.append(f"scene:{loc}:{want}")

    for ref_id in panel.get("continuity_refs", []) or []:
        refs.append(f"prior:{ref_id}")
    tiers = panel.get("muscle_size_tier") or {}
    t9 = any(isinstance(t, int) and t >= 9 for t in tiers.values())
    if t9: refs.append("anchor:lana")

    action = panel.get("action", "")
    body = {"instruction": "Generate one image.", "style": STYLE,
            "camera": entry.get("camera", panel.get("camera")),
            "scene": {"environment": "EXACTLY the attached scene reference", "continuity": "continue from the attached previous panel" if panel.get("continuity_refs") else "establishing beat"},
            "characters": characters,
            "spatial_rules": list(staging.get("spatial_rules", ["<MISSING>"] if contact else [])),
            "action": action,
            "lighting": staging.get("lighting", panel.get("time_of_day", "")),
            "negative": (NEG + NEG_PAGE_BLEED).lower()}
    if any("torn" in state_for(c, panel) or "remnant" in state_for(c, panel) for c in chars):
        body["spatial_rules"].append("coverage of chest and hips fully intact in every stage")
    if "GROWTH-PROGRESSIVE" in action:
        body["progression_rule"] = ("damage and musculature progress TOWARD the state shown in the attached "
                                    "turnaround, reaching it only in the FINAL stage; earlier stages show progressively less")
    if any(isinstance(t, int) and t >= 4 for t in tiers.values()):
        body["size_rule"] = "muscle mass per the attached turnaround — height does NOT change"
    if errs: refuse(errs)
    return json.dumps(body, separators=(",", ":")), refs, entry["aspect"], {"bootstrap": False, "tier_job": t9}

def compose_edit(panel_id):
    """i2i retouch of an already-accepted panel — NOT a fresh composition. Reads fix-jobs.json
    (project root) for the panel's job entry and requires the source panel file to exist; refuses
    on either being missing. No shotlist/ref-ledger/staging dependency — see PLAN section 6."""
    jobs_path = "fix-jobs.json"
    if not os.path.exists(jobs_path): refuse([f"{jobs_path} not found at project root"])
    jobs = json.load(open(jobs_path)).get("jobs", [])
    job = next((j for j in jobs if os.path.splitext(j.get("panel") or "")[0] == panel_id), None)
    if not job: refuse([f"no fix-jobs.json entry for panel_id '{panel_id}'"])
    panel_file = job.get("panel") or ""
    panel_path = os.path.join("panels", panel_file)
    if not panel_file or not os.path.exists(panel_path):
        refuse([f"source panel '{panel_path}' does not exist — edit: requires the exact panel it corrects"])

    c = job.get("constraints", {}) or {}
    holds = [c.get(k) for k in ("identity_lock", "tier_lock", "wardrobe_lock", "camera_lock") if c.get(k)]
    other = [o for o in (c.get("other") or []) if o]

    parts = ["Keep the exact same camera angle, framing, character poses, expressions, and "
             "composition as the source image."]
    parts.append(STYLE)  # D-style-anchor: audit_prompt.py's "NOT illustrated" check is unconditional,
                          # not scoped to kind=="page" — every job kind must carry this substring.
    fix_line = (job.get("defect_summary") or "").strip()
    if fix_line: parts.append(f"Correction: {fix_line}")
    if holds: parts.append("Hold exactly as shown in the source, do not drift: " + "; ".join(holds) + ".")
    if other: parts.append(" ".join(other))

    dlg = job.get("corrected_dialogue") or []
    if dlg:
        blocks = []
        for d in dlg:
            btype = (d.get("bubble_type") or "").lower()
            shape = next((v for k, v in BUBBLE_SHAPE.items() if k in btype), BUBBLE_SHAPE["speech"])
            tail = d.get("tail_target")
            tail_txt = f", tail pointing to {tail}" if tail and tail.lower() != "none" else ", no tail (floating box)"
            blocks.append(f'{shape}{tail_txt}, bold black comic display font reads exactly: "{d.get("line", "")}"')
        parts.append("LETTERING — classic comic-book lettering composited onto the photoreal CGI scene, flat 2D "
                      "vector graphics only (no 3D shading, no bevel, no chrome, no drop shadow on the scene); "
                      "everything else in the panel stays exactly as in the source image. Re-letter to: "
                      + " | ".join(blocks) + ". No speaker-name prefix, no stray quotation marks beyond the "
                      "quoted text itself.")

    prompt = " ".join(p.strip() for p in parts if p and p.strip())
    prompt = prompt if prompt.endswith(".") else prompt + "."
    prompt += " " + NEG_EDIT

    attach = [panel_path]
    plan = json.load(open("pages-plan.json")) if os.path.exists("pages-plan.json") else {"pages": []}
    entry = next((e for e in plan.get("pages", []) if e["id"] == panel_id), None)
    aspect = entry["aspect"] if entry else "match-source"
    return prompt, attach, aspect, {"bootstrap": False, "edit": True, "source_job": job.get("id"), "source_panel": panel_path}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--job", required=True, help="sheet:<id> | page:<panel_id> | edit:<panel_id>")
    ap.add_argument("--pass", dest="pass_key", default=None)
    a = ap.parse_args()
    kind, _, ident = a.job.partition(":")
    if kind == "sheet": prompt, attach, aspect, flags = compose_sheet(ident, a.pass_key)
    elif kind == "page": prompt, attach, aspect, flags = compose_page(ident)
    elif kind == "edit": prompt, attach, aspect, flags = compose_edit(ident)
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
