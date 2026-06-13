#!/usr/bin/env python3
"""Pre-flight gate (manila-bay-rising / Chapter 1): refuse a page submit unless its
ref stack + structured prompt pass (D1-D13). Ch1-scoped — no tier>=6 anchor/lineup
machinery; tier>=2 only needs the lineup/turnaround attached + height clamp.

Usage:
  python3 qa/preflight.py --panel p05-01 --prompt-json /tmp/p05.json \
      --attached "face:hae-won,turnaround:hae-won:t1,face:cel,turnaround:cel:t1,scene:manila-bay-sunset,prior:p04-04"

Exit 0 = PASS (submit allowed). Exit 1 = FAIL (reasons printed; do NOT submit).
Run from the project root (projects/manila-bay-rising/).
"""
import argparse, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import integrity; integrity.verify_or_die()  # LAYER 8

CONTACT_WORDS = re.compile(
    r"\b(carr(y|ies|ying)|lift|hug|embrace|grab|press(es|ing)?|slam|pin(s|ned)?|"
    r"catch(es)?|hold(s|ing)?|hand on|wrapped|tow(s|ing)?|pull(s|ing)?)\b", re.I)
BANNED_VFX = re.compile(r"\b(volumetric|god.?rays?|cinematic VFX|physically accurate|"
                        r"anatomy-conforming|micro-?filaments?|fresnel)\b", re.I)
APPEARANCE_ADJ = re.compile(r"\b(blonde?|black-?bob|curly|hazel|blue eyes|ice-blue|bald|freckle|"
                            r"square-?jaw|chin-length|bangs)\b", re.I)
# Ch1 chapter openers / new-thread panels with legitimately empty continuity_refs
NO_PRIOR_OK = ("p01-01", "p03-01", "p04-01", "p04-02")

def fail(msgs):
    print("PREFLIGHT FAIL:")
    for m in msgs: print(f"  ✗ {m}")
    sys.exit(1)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", required=True)
    ap.add_argument("--prompt-json", required=True)
    ap.add_argument("--attached", required=True,
                    help="comma list kind:id (face:X, turnaround:X:tN, scene:loc, staging:X, prior:pNN)")
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

    # D1/D11: every character needs face + turnaround attached
    for c in chars:
        if not any(c in f for f in kinds.get("face", [])):
            errs.append(f"D1: no face ref attached for '{c}'")
        if not any(c in t for t in kinds.get("turnaround", [])):
            errs.append(f"D4/D11: no wardrobe-state turnaround attached for '{c}'")

    # D8: every located panel needs a scene ref (every Ch1 location has one)
    scenes = kinds.get("scene", [])
    if panel.get("location") and not scenes:
        errs.append("D8: no scene ref attached (every location has a banked scene ref)")

    # D9: contact/novel pose requires staging ref
    if len(chars) >= 2 and CONTACT_WORDS.search(panel.get("action", "")) and "staging" not in kinds:
        errs.append("D9: physical-contact action with no staging ref attached")

    # continuity: prior panel required except for chapter openers
    if "prior" not in kinds and a.panel not in NO_PRIOR_OK:
        errs.append("D1: no prior accepted panel attached for continuity")

    # tier>=2: lineup/turnaround attached + height clamp present
    tiers = panel.get("muscle_size_tier") or {}
    big = any(isinstance(t, int) and t >= 2 for t in tiers.values())
    blob = json.dumps(prompt)
    if big:
        if not kinds.get("turnaround") and "lineup" not in kinds:
            errs.append("D4: tier>=2 page without a tier turnaround/lineup attached")
        if "never beyond it" not in blob and "height changes ONLY" not in blob:
            errs.append("D7: tier page missing the height clamp sentence")

    # D12: structured prompt completeness
    for key in ("camera", "characters", "spatial_rules", "negative"):
        if key not in prompt: errs.append(f"D12: prompt JSON missing '{key}'")
    for ch in prompt.get("characters", []):
        app = ch.get("appearance", "")
        if not app.startswith("EXACTLY the"):
            errs.append(f"D11: appearance for '{ch.get('id')}' is not pointer-only")
        if APPEARANCE_ADJ.search(app) and "attached" not in app:
            errs.append(f"D11: appearance adjectives without ref pointer for '{ch.get('id')}'")
        hands = json.dumps(ch.get("pose", {})).lower()
        if len(chars) >= 2 and "hand" not in hands:
            errs.append(f"D13: no per-hand accounting for '{ch.get('id')}'")
    if len(chars) >= 2 and not any("hands total" in s for s in prompt.get("spatial_rules", [])):
        errs.append("D13: spatial_rules missing the total-hands line")

    # D10: effects vocabulary
    if BANNED_VFX.search(blob):
        errs.append("D10: banned VFX language present (use vfx-style-bible vocabulary)")

    if errs: fail(errs)
    print(f"PREFLIGHT PASS: {a.panel} — refs {sorted(kinds)} ok, prompt structured-complete")

if __name__ == "__main__":
    main()
