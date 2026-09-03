#!/usr/bin/env python3
"""Roll every corpus/<slug>/angle-study.json into (a) a human angle deck and
(b) a Prompt Deck cards.json of appendable camera/pose sentences.

    scripts/angle_deck.py --corpus-root corpus --out synthesis/angle-deck.md --cards synthesis/cards.json
    scripts/angle_deck.py --corpus-root corpus --json      # machine rollup to stdout

Reads the addendum fields (angle-study-addendum.md). Joins each panel to its
beats.json twin (same page/n) to pick up the rubric's `angle` / `shot_distance` /
`staging`. Only panels with steal_score >= MIN_STEAL and a prompt_seed become cards.
The seed text is the card; the artist's drawing style never enters the deck.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

MIN_STEAL = 3

# card groups: rubric `angle` first, then the addendum's toward_camera as a tiebreak label
GROUP_ORDER = ["worm", "low", "eye", "high", "bird", "aerial", "dutch", "OTS", "pov", "other"]
GROUP_TITLES = {
    "worm": "Worm's-eye (camera on the floor)",
    "low": "Low angle (camera below the hips)",
    "eye": "Eye level",
    "high": "High angle",
    "bird": "Bird's-eye",
    "aerial": "Aerial",
    "dutch": "Dutch / canted",
    "OTS": "Over-the-shoulder",
    "pov": "POV",
    "other": "Other",
}


def load_entries(root: Path):
    for study in sorted(root.glob("*/angle-study.json")):
        slug = study.parent.name
        beats_path = study.parent / "beats.json"
        try:
            study_d = json.loads(study.read_text())
        except json.JSONDecodeError as e:  # keep going, report
            print(f"WARN {slug}: angle-study.json unreadable ({e})", file=sys.stderr)
            continue
        beats = {}
        if beats_path.exists():
            bd = json.loads(beats_path.read_text())
            for pg in bd.get("pages", []):
                for pn in pg.get("panels", []):
                    beats[(pg.get("page"), pn.get("n"))] = pn
        yield slug, study_d, beats


def norm(s):
    return re.sub(r"[^a-z0-9 ]", "", (s or "").lower()).strip()


def collect(root: Path):
    cards, hist, per_artist = [], defaultdict(Counter), {}
    seen = set()
    for slug, study, beats in load_entries(root):
        artist = re.split(r"\s*\(", study.get("artist") or "unknown")[0].strip() or "unknown"
        per_artist.setdefault(artist, {"comics": [], "signature_moves": [], "avoid": []})
        per_artist[artist]["comics"].append(slug)
        per_artist[artist]["signature_moves"] += study.get("signature_moves", []) or []
        per_artist[artist]["avoid"] += study.get("avoid", []) or []
        for pg in study.get("pages", []):
            for pn in pg.get("panels", []):
                key = (pg.get("page"), pn.get("n"))
                twin = beats.get(key, {})
                for f in ("camera_height", "toward_camera", "muscle_sold", "body_line", "crop", "pose_family", "lens_feel"):
                    if pn.get(f):
                        hist[f][pn[f]] += 1
                if twin.get("angle"):
                    hist["angle"][twin["angle"]] += 1
                if twin.get("shot_distance"):
                    hist["shot_distance"][twin["shot_distance"]] += 1
                for m in pn.get("sell_mechanism") or []:
                    hist["sell_mechanism"][m] += 1
                seed = (pn.get("prompt_seed") or "").strip()
                score = pn.get("steal_score") or 0
                if score < MIN_STEAL or not seed:
                    continue
                k = norm(seed)[:80]
                if k in seen:
                    continue
                seen.add(k)
                angle = twin.get("angle") or "other"
                if angle not in GROUP_TITLES:
                    angle = "other"
                cards.append({
                    "id": f"{slug}-p{pg.get('page')}-{pn.get('n')}",
                    "group": angle,
                    "subgroup": pn.get("toward_camera") or "none",
                    "label": f"{pn.get('pose_family','?')} · sells {pn.get('muscle_sold','?')} · {twin.get('shot_distance','?')}/{angle}/{pn.get('camera_height','?')}-cam",
                    "text": seed,
                    "chars": len(seed),
                    "steal_score": score,
                    "source": {"comic": slug, "page": pg.get("page"), "panel": pn.get("n"), "artist": artist},
                    "tags": {
                        "shot_distance": twin.get("shot_distance"),
                        "angle": angle,
                        "camera_height": pn.get("camera_height"),
                        "toward_camera": pn.get("toward_camera"),
                        "muscle_sold": pn.get("muscle_sold"),
                        "body_line": pn.get("body_line"),
                        "crop": pn.get("crop"),
                        "pose_family": pn.get("pose_family"),
                        "sell_mechanism": pn.get("sell_mechanism") or [],
                        "explicit": bool(pn.get("explicit")),
                    },
                })
    cards.sort(key=lambda c: (GROUP_ORDER.index(c["group"]) if c["group"] in GROUP_ORDER else 99, -c["steal_score"], c["id"]))
    return cards, hist, per_artist


def fmt_cites(c):
    if isinstance(c, str):
        return c
    out = []
    for x in c or []:
        if isinstance(x, dict):
            out.append(f"p{x.get('page')}.{x.get('n')}")
        else:
            out.append(str(x))
    return ", ".join(out)


def fmt_avoid(a):
    if isinstance(a, dict):
        habit = a.get("habit") or a.get("name") or a.get("what") or ""
        why = a.get("why") or a.get("reason") or ""
        cites = fmt_cites(a.get("citations") or a.get("cites"))
        return f"**{habit}** — {why} _({cites})_" if cites else f"**{habit}** — {why}"
    return str(a)


def fmt_hist(c: Counter, n=None):
    tot = sum(c.values()) or 1
    items = c.most_common(n)
    return ", ".join(f"{k} {v} ({100*v//tot}%)" for k, v in items)


def write_md(path: Path, cards, hist, per_artist):
    L = ["# Angle Deck — camera/pose seeds mined from the corpus", ""]
    L.append(f"{len(cards)} cards (steal_score ≥ {MIN_STEAL}, deduped). Generated by `scripts/angle_deck.py` from every `corpus/*/angle-study.json`.")
    L.append("Cards are plain-speech camera + pose + crop sentences meant to be APPENDED to a Flow/Higgsfield prompt after the continuation line and the refs. They carry no appearance and no style.")
    L.append("")
    L.append("## Where this artist puts the camera (all tagged panels)")
    for f, title in (("angle", "Angle"), ("camera_height", "Camera height"), ("shot_distance", "Distance"), ("toward_camera", "Body part nearest the lens"), ("muscle_sold", "Muscle the panel is built to sell"), ("body_line", "Body line"), ("crop", "Crop"), ("pose_family", "Pose family"), ("sell_mechanism", "Sell mechanism"), ("lens_feel", "Lens feel")):
        if hist.get(f):
            L.append(f"- **{title}:** {fmt_hist(hist[f])}")
    L.append("")
    for artist, info in per_artist.items():
        L.append(f"## Signature moves — {artist}  ({', '.join(info['comics'])})")
        for mv in info["signature_moves"]:
            if isinstance(mv, dict):
                name = mv.get("name") or mv.get("move") or mv.get("device") or "move"
                cites = fmt_cites(mv.get("citations") or mv.get("cites") or mv.get("examples") or "")
                how = mv.get("how_to_steal") or mv.get("how_to_steal_for_cgi") or mv.get("steal_for_cgi") or mv.get("steal") or mv.get("how") or ""
                desc = mv.get("description") or mv.get("what") or ""
                L.append(f"- **{name}** — {desc} _{cites}_  → {how}".replace("  ", " "))
            else:
                L.append(f"- {mv}")
        if info["avoid"]:
            L.append("")
            L.append(f"**Does not translate to 3D CGI ({artist}):**")
            for a in info["avoid"]:
                L.append(f"- {fmt_avoid(a)}")
        L.append("")
    L.append("## Cards by angle")
    by_group = defaultdict(list)
    for c in cards:
        by_group[c["group"]].append(c)
    for g in GROUP_ORDER:
        if g not in by_group:
            continue
        L.append("")
        L.append(f"### {GROUP_TITLES[g]}  ({len(by_group[g])})")
        L.append("")
        L.append("| ★ | sells | toward lens | crop | seed | source |")
        L.append("|---|---|---|---|---|---|")
        for c in by_group[g]:
            t = c["tags"]
            src = f"{c['source']['comic']} p{c['source']['page']}.{c['source']['panel']}"
            L.append(f"| {c['steal_score']} | {t['muscle_sold']} | {t['toward_camera']} | {t['crop']} | {c['text']} | {src} |")
    path.write_text("\n".join(L) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus-root", type=Path, default=Path("corpus"))
    ap.add_argument("--out", type=Path, help="markdown deck path")
    ap.add_argument("--cards", type=Path, help="Prompt Deck cards.json path")
    ap.add_argument("--json", action="store_true", help="print machine rollup")
    a = ap.parse_args(argv)
    cards, hist, per_artist = collect(a.corpus_root)
    if a.json:
        print(json.dumps({"cards": cards, "hist": {k: dict(v) for k, v in hist.items()}, "artists": per_artist}, indent=1, ensure_ascii=False))
    if a.out:
        write_md(a.out, cards, hist, per_artist)
        print(f"wrote {a.out} ({len(cards)} cards)")
    if a.cards:
        deck = {
            "title": "Angle Deck",
            "generatedBy": "research/comic-corpus/scripts/angle_deck.py",
            "usage": "APPEND one card after the continuation line + refs. Text only; no appearance, no style.",
            "groups": [{"id": g, "title": GROUP_TITLES[g]} for g in GROUP_ORDER if any(c["group"] == g for c in cards)],
            "cards": [{k: c[k] for k in ("id", "group", "subgroup", "label", "text", "chars", "steal_score", "source", "tags")} for c in cards],
        }
        a.cards.write_text(json.dumps(deck, indent=1, ensure_ascii=False) + "\n")
        print(f"wrote {a.cards} ({len(cards)} cards)")
    if not (a.json or a.out or a.cards):
        print(f"{len(cards)} cards; pass --out/--cards/--json", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
