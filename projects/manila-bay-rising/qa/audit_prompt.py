#!/usr/bin/env python3
"""LAYER 2: INDEPENDENT second checker. Different code, different rule encoding
than compose.py — both must pass before a submit. Verifies the receipt matches
the prompt actually about to be pasted (sha256), then lints it cold.

  python3 qa/audit_prompt.py --receipt qa/receipts/<job>.receipt.json --prompt-file /tmp/p.txt

v2 (user-blessed fix batch): pages that attach a turnaround MUST carry the
anti-reference-bleed negative; GROWTH-PROGRESSIVE pages MUST carry a
progression_rule (independent encodings of the compose-side fixes).
"""
import argparse, hashlib, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import integrity; integrity.verify_or_die()  # LAYER 8

BANNED_APPEARANCE = re.compile(r"\b(blonde?|curly|hazel|ice-blue|bald|freckl\w*|square-?jaw\w*|"
                               r"chin-length|bangs|jet-black|black-?bob)\b", re.I)
BANNED_VFX = re.compile(r"\b(volumetric|god.?rays?|physically accurate|anatomy-conforming|"
                        r"micro-?filaments?|fresnel|cinematic VFX)\b", re.I)
SCALE_RISK = re.compile(r"\b(towering|giantess|colossal height|taller than)\b", re.I)

def fail(msgs):
    print("AUDIT FAIL:")
    for m in msgs: print(f"  ✗ {m}")
    sys.exit(1)

a = argparse.ArgumentParser()
a.add_argument("--receipt", required=True)
a.add_argument("--prompt-file", required=True)
args = a.parse_args()

rec = json.load(open(args.receipt))
prompt = open(args.prompt_file).read().strip()
errs = []

if hashlib.sha256(prompt.encode()).hexdigest() != rec["prompt_sha"]:
    errs.append("prompt does NOT match the composed receipt — freehand edit detected (Layer 0 bypass)")
if not rec.get("flags", {}).get("bootstrap") and BANNED_APPEARANCE.search(prompt):
    hits = sorted(set(m.group(0).lower() for m in BANNED_APPEARANCE.finditer(prompt)))
    errs.append(f"D11: appearance words in a non-bootstrap job: {hits}")
if BANNED_VFX.search(prompt): errs.append("D10: banned VFX language")
if SCALE_RISK.search(prompt) and "height does NOT" not in prompt and "NOT a giantess" not in prompt:
    errs.append("D7: scale-risk language without a height clamp")
if rec["kind"] == "sheet" and not rec.get("flags", {}).get("genesis") and len(rec["attach"]) < 2: errs.append("D1: sheet with <2 refs")
if rec["kind"] == "page":
    n_faces = sum(1 for s in rec["attach"] if s.startswith("face:"))
    minref = 3 if n_faces else 1  # character pages need face+turnaround+scene; establishing pages just a scene ref
    if len(rec["attach"]) < minref: errs.append(f"D1: page with <{minref} refs (faces={n_faces})")
if rec.get("flags", {}).get("tier_job") and not any("anchor" in s or "turnaround" in s for s in rec["attach"]):
    errs.append("D6/D14: tier job without anchor/turnaround in attach list")
if "NOT illustrated" not in prompt and "not illustrated" not in prompt: errs.append("style anchor missing")
if rec["kind"] == "page" and any("turnaround" in s for s in rec["attach"]) and "no mannequin" not in prompt.lower():
    errs.append("reference-bleed: page attaches a turnaround but lacks the no-mannequin/no-grid negative")
if "GROWTH-PROGRESSIVE" in prompt and "progression_rule" not in prompt:
    errs.append("end-state paradox: progressive page lacks a progression_rule (stages must build TOWARD the attached turnaround)")

if errs: fail(errs)
marker = args.receipt.replace(".receipt.json", ".audit-pass")
open(marker, "w").write(rec["prompt_sha"])
print(f"AUDIT PASS  sha={rec['prompt_sha'][:12]}…  marker={marker}")
