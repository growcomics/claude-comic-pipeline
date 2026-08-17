#!/usr/bin/env python3
"""Bank a batch of judged winners, with the duplicate-variant-prefix guard.

  python3 bankmany.py picks.jsonl

Each line: {"beat": "...", "variant": "v05", "notes": "judge one-liner"}

`drive.py winner` globs `<variant>-*.png` and takes the FIRST match, so a beat whose
variants dir holds two files with the same vNN prefix can silently bank a KILLED tile.
This refuses to bank any beat with a duplicated prefix, and reports it instead.
"""
import json, subprocess, sys, collections
from pathlib import Path

RUN = Path(__file__).resolve().parent


def dupes(beat):
    d = RUN / "variants" / beat
    c = collections.Counter(f.name.split("-")[0] for f in d.glob("v*.png"))
    return [k for k, v in c.items() if v > 1]


def main(path):
    ok, skipped = [], []
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        p = json.loads(line)
        beat, var = p["beat"], p["variant"]
        dp = dupes(beat)
        if var in dp:
            skipped.append((beat, var, f"DUPLICATE PREFIX {dp} — resolve by hand"))
            continue
        cmd = ["python3", str(RUN / "drive.py"), "winner", beat, var]
        if p.get("notes"):
            cmd += ["--notes", p["notes"]]
        r = subprocess.run(cmd, cwd=RUN, capture_output=True, text=True)
        if r.returncode == 0:
            ok.append(r.stdout.strip())
            print("OK  " + r.stdout.strip())
        else:
            skipped.append((beat, var, (r.stderr or r.stdout).strip().splitlines()[-1:]))
            print(f"ERR {beat} {var}: {(r.stderr or r.stdout).strip()[-300:]}")
    print(f"\nbanked {len(ok)}, skipped {len(skipped)}")
    for s in skipped:
        print("  SKIP", s)


if __name__ == "__main__":
    main(sys.argv[1])
