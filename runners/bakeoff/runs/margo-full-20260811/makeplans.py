#!/usr/bin/env python3
"""Rebuild plan/<beat>.json from margo-full-beats.json (the source of truth).

  python3 makeplans.py <beat> [<beat>...]     # or: all
Plans are what the generation driver reads, so they MUST be regenerated after any
edit to a beat's fullPrompt / variants / refs, or the driver silently rolls the
old prompt (this is exactly how the b70/b74 cast-count fix nearly got missed).
"""
import json, sys
from pathlib import Path
RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[3]
SHEET = json.loads((ROOT / "runners/bakeoff/margo-full-beats.json").read_text())
BEATS = {b["id"]: b for b in SHEET["beats"]}
MEDIA = json.loads((RUN / "refs/higgsfield-media-ids.json").read_text())

def build(bid):
    b = BEATS[bid]
    medias = []
    for r in b.get("identityRefs", []):
        mid = MEDIA.get(r["label"])
        if not mid:
            raise SystemExit(f"{bid}: no media id for ref '{r['label']}'")
        medias.append({"value": mid, "role": "image_references"})
    plan = {"beat": bid, "variants": b.get("variants", 8),
            "model": SHEET.get("backend_model", "nano_banana_2_lite"),
            "aspect_ratio": b.get("aspect", "3:4"), "prompt": b["fullPrompt"],
            "medias": medias, "beatKind": b.get("beatKind"), "stage": b.get("stage"),
            "chars": b.get("chars", []), "dialogue": b.get("dialogue", []),
            "wardrobe": b.get("wardrobe")}
    (RUN / "plan").mkdir(exist_ok=True)
    (RUN / "plan" / f"{bid}.json").write_text(json.dumps(plan, indent=1, ensure_ascii=False))
    print(f"{bid}: variants={plan['variants']} aspect={plan['aspect_ratio']} "
          f"refs={len(medias)} prompt={len(plan['prompt'])}c")

if __name__ == "__main__":
    a = sys.argv[1:]
    ids = list(BEATS) if (not a or a == ["all"]) else a
    for i in ids:
        build(i)
