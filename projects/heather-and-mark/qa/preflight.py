#!/usr/bin/env python3
"""Pre-flight gate (D1-D14): refuse a page submit unless its ref stack + v4 prompt pass.

Usage:
  python3 qa/preflight.py --panel p16-01 --prompt-json /tmp/p16.json \
      --attached "face:dana-lane,turnaround:dana-t6-torn,scene:doomer-lab-medium,prior:p15-01"

Exit 0 = PASS (submit allowed). Exit 1 = FAIL (reasons printed; do NOT submit).
Run from the project root (projects/not-so-supra-man/).
"""
import argparse, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import integrity; integrity.verify_or_die()  # LAYER 8

CONTACT_WORDS = re.compile(
    r"\b(carr(y|ies|ying)|lift|hug|embrace|grab|press(es|ing)?|chokeslam|slam|pin(s|ned)?|"
    r"arm-?wrestle|catch(es)?|hold(s|ing)?|hand on|shoulders into|wrapped)\b", re.I)
BANNED_VFX = re.compile(r"\b(volumetric|god.?rays?|cinematic VFX|physically accurate|"
                        r"anatomy-conforming|micro-?filaments?|fresnel)\b", re.I)
APPEARANCE_ADJ = re.compile(r"\b(blonde?|black-?bob|curly|hazel|blue eyes|ice-blue|bald|freckle|"
                            r"square-?jaw|chin-length|bangs)\b", re.I)
CAMERA_DISTANCE = {  # camera keyword -> required scene-rung class
    "wide": "wide", "establish": "wide", "splash": "wide", "birds-eye": "wide",
    "full": "medium", "cowboy": "medium", "medium": "medium",
    "mcu": "close", "ecu": "close", "close": "close", "over-shoulder": "medium",
}

def fail(msgs):
    print("PREFLIGHT FAIL:")
    for m in msgs: print(f"  ✗ {m}")
    sys.exit(1)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", required=True)
    ap.add_argument("--prompt-json", required=True)
    ap.add_argument("--attached", required=True,
                    help="comma list kind:id (face:X, turnaround:X, scene:loc-rung, staging:X, prior:pNN, anchor, lineup)")
    a = ap.parse_args()

    shot = json.load(open("shotlist.json"))
    panel = None
    for pg in shot["pages"]:
        for p in pg["panels"]:
            if p["panel_id"] == a.panel: panel = p
    if not panel: fail([f"panel {a.panel} not in shotlist"])

    prompt = json.load(open(a.prompt_json))
    attached = [s.strip() for s in a.attached.split(",") if s.strip()]
    kinds = {}
    for item in attached:
        k, _, v = item.partition(":")
        kinds.setdefault(k, []).append(v)

    errs = []
    chars = [c for c in panel.get("characters", [])]

    # D1/D5/D11: every character needs face + turnaround attached
    for c in chars:
        if not any(c in f for f in kinds.get("face", [])):
            errs.append(f"D1: no face ref attached for '{c}'")
        if not any(c.split('-')[0] in t or c in t for t in kinds.get("turnaround", [])):
            errs.append(f"D4/D11: no wardrobe-state turnaround attached for '{c}'")

    # D8: scene rung must match camera distance class
    cam = panel.get("camera", "").lower()
    want = next((cls for kw, cls in CAMERA_DISTANCE.items() if kw in cam), "medium")
    scenes = kinds.get("scene", [])
    if panel.get("location") and panel["location"] not in ("lab-exterior",) and not scenes:
        errs.append(f"D8: no scene ref attached (camera wants a '{want}' rung)")
    if scenes and not any(want in s for s in scenes):
        errs.append(f"D8: scene rung {scenes} does not match camera distance '{want}'")

    # D9: contact/novel pose requires staging ref
    if len(chars) >= 2 and CONTACT_WORDS.search(panel.get("action", "")) and "staging" not in kinds:
        errs.append("D9: physical-contact action with no staging ref attached")

    # continuity: prior panel after the first accepted page
    if "prior" not in kinds and a.panel not in ("p01-01", "p02-01"):
        errs.append("D1: no prior accepted panel attached for continuity")

    # D6/D14: tier pages need lineup/anchor + height clamp
    tiers = panel.get("muscle_size_tier") or {}
    big = any(isinstance(t, int) and t >= 6 for t in tiers.values())
    blob = json.dumps(prompt)
    if big:
        if "anchor" not in kinds and "lineup" not in kinds:
            errs.append("D6/D14: tier>=6 page without size anchor/lineup attached")
        if "height does NOT" not in blob and "height does not" not in blob:
            errs.append("D7: tier page missing the height clamp sentence")

    # D12: v4 prompt completeness
    for key in ("camera", "characters", "spatial_rules", "negative"):
        if key not in prompt: errs.append(f"D12: prompt JSON missing '{key}'")
    for ch in prompt.get("characters", []):
        app = ch.get("appearance", "")
        if not app.startswith("EXACTLY the"):
            errs.append(f"D11: appearance for '{ch.get('id')}' is not pointer-only")
        if APPEARANCE_ADJ.search(app.replace("black-bob", "") if False else app) and "attached reference" not in app:
            errs.append(f"D11: appearance adjectives without ref pointer for '{ch.get('id')}'")
        hands = json.dumps(ch.get("pose", {})).lower()
        if "hand" not in hands:
            errs.append(f"D13: no per-hand accounting for '{ch.get('id')}'")
    if not any("hands total" in s for s in prompt.get("spatial_rules", [])):
        errs.append("D13: spatial_rules missing the total-hands line")

    # D10: effects vocabulary
    if BANNED_VFX.search(blob):
        errs.append("D10: banned VFX language present (use vfx-style-bible vocabulary)")

    if errs: fail(errs)
    print(f"PREFLIGHT PASS: {a.panel} — refs {sorted(kinds)} ok, prompt v4-complete")

if __name__ == "__main__":
    main()
