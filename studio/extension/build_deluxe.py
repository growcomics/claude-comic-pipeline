#!/usr/bin/env python3
"""Build **Flow Studio Deluxe** from the 3DMC Studio Tools source.

Deluxe is not a fork. It is the same extension with a different manifest name,
and content.js / patreon.js key their behaviour off that name (`/deluxe/i`):
always the full panel (→ Studio / Auto-sync, 🔬 Bake-off, 🗑 Delete, Patreon
downloader), no Creator/Advanced switch, nothing hidden — the owner/staff build.
Contributors keep getting 3DMC Studio Tools from /toolbox/.

    python3 studio/extension/build_deluxe.py            # folder + zip
    python3 studio/extension/build_deluxe.py --no-zip   # folder only (load unpacked)

Outputs
  studio/extension/flow-studio-deluxe/            GENERATED — load this unpacked; never hand-edit
  studio/extension/dist/flow-studio-deluxe-v<ver>.zip   top-level folder flow-studio-deluxe/
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "flow-studio-tools")
OUT = os.path.join(HERE, "flow-studio-deluxe")
DIST = os.path.join(HERE, "dist")
NAME = "Flow Studio Deluxe"
SKIP = {".DS_Store", "README.md"}

DESCRIPTION = (
    "The owner/staff build of 3DMC Studio Tools with nothing hidden: on Google Flow — "
    "Download images, Send/Auto-sync them into the 3DMC Comic Studio, export a Review bundle, "
    "Bulk-delete (guarded), run a model bake-off, insert canonical prompt blocks or deal an Angle "
    "card; on Patreon — bulk-download a post's gallery. Every tab is always on; there is no "
    "Creator/Advanced switch. Paste the Studio bridge URL + key once under ⚙."
)

README = """# Flow Studio Deluxe (GENERATED — do not edit)

This folder is built from `../flow-studio-tools/` by `../build_deluxe.py`. Every
file here is a copy of that source except `manifest.json` (renamed) and this README.
Fix bugs in `flow-studio-tools/`, then rebuild:

    python3 studio/extension/build_deluxe.py

**What Deluxe is:** the same 3DMC Studio Tools panel with *nothing hidden* — → Studio /
Auto-sync, 🔬 Bake-off, 🗑 Delete and the Patreon gallery downloader are always on and
there is no Creator/Advanced switch. `content.js` and `patreon.js` detect the build from
the manifest name (`/deluxe/i`). Contributors keep using 3DMC Studio Tools from
https://3dmusclecomics.com/toolbox/ ; Deluxe is for the owner and staff (Admin → Extensions).

**Install (unpacked):** `chrome://extensions` → Developer mode → Load unpacked → this folder.
Then open a Flow project, click the panel's ⚙, paste the Studio **Bridge URL** + **key**
from the Studio home page ("⚙ Flow import") and Save. Do not run both flavors at once —
the first one to load keeps the page and the other bows out (see the console).
"""


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def build(make_zip=True):
    if not os.path.isdir(SRC):
        sys.exit(f"source missing: {SRC}")
    with open(os.path.join(SRC, "manifest.json"), encoding="utf-8") as f:
        manifest = json.load(f)
    ver = manifest["version"]

    # 1) fresh copy of the source folder
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    copied = []
    for name in sorted(os.listdir(SRC)):
        if name in SKIP or name.startswith("."):
            continue
        src = os.path.join(SRC, name)
        if os.path.isfile(src):
            shutil.copy2(src, os.path.join(OUT, name))
            copied.append(name)

    # 2) the one real difference: the manifest name (+ a version_name the header shows)
    manifest["name"] = NAME
    manifest["version_name"] = f"{ver} Deluxe"
    manifest["description"] = DESCRIPTION
    with open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
        f.write("\n")
    with open(os.path.join(OUT, "README.md"), "w", encoding="utf-8") as f:
        f.write(README)

    # 3) sanity: every script parses, the flavor hook is present, manifest is valid JSON
    for name in copied:
        if name.endswith(".js"):
            subprocess.run(["node", "--check", os.path.join(OUT, name)], check=True)
    for name in ("content.js", "patreon.js"):
        with open(os.path.join(OUT, name), encoding="utf-8") as f:
            if "DELUXE" not in f.read():
                sys.exit(f"{name} has no DELUXE flavor hook — source out of date")
    with open(os.path.join(OUT, "manifest.json"), encoding="utf-8") as f:
        assert json.load(f)["name"] == NAME
    print(f"built {OUT}  ({len(copied) + 1} files, v{ver})")

    if not make_zip:
        return None

    # 4) zip with a top-level folder, like the /toolbox/ package
    os.makedirs(DIST, exist_ok=True)
    zpath = os.path.join(DIST, f"flow-studio-deluxe-v{ver}.zip")
    if os.path.exists(zpath):
        os.remove(zpath)
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for name in sorted(os.listdir(OUT)):
            if name.startswith("."):
                continue
            z.write(os.path.join(OUT, name), f"flow-studio-deluxe/{name}")
    size = os.path.getsize(zpath)
    digest = sha256(zpath)
    info = {"name": NAME, "version": ver, "zip": os.path.basename(zpath), "bytes": size, "sha256": digest}
    with open(os.path.join(DIST, "flow-studio-deluxe-latest.json"), "w", encoding="utf-8") as f:
        json.dump(info, f, indent=2)
        f.write("\n")
    print(json.dumps(info, indent=2))
    return info


def package_standard():
    """Zip the contributor build exactly as /toolbox/ ships it: top-level folder
    `3dmc-studio-tools/`, no README/.DS_Store, into dist/3dmc-studio-tools-v<ver>.zip."""
    with open(os.path.join(SRC, "manifest.json"), encoding="utf-8") as f:
        ver = json.load(f)["version"]
    for name in sorted(os.listdir(SRC)):
        if name.endswith(".js"):
            subprocess.run(["node", "--check", os.path.join(SRC, name)], check=True)
    os.makedirs(DIST, exist_ok=True)
    zpath = os.path.join(DIST, f"3dmc-studio-tools-v{ver}.zip")
    if os.path.exists(zpath):
        os.remove(zpath)
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for name in sorted(os.listdir(SRC)):
            if name in SKIP or name.startswith("."):
                continue
            z.write(os.path.join(SRC, name), f"3dmc-studio-tools/{name}")
    info = {"name": "3DMC Studio Tools", "version": ver, "zip": os.path.basename(zpath),
            "bytes": os.path.getsize(zpath), "sha256": sha256(zpath)}
    with open(os.path.join(DIST, "3dmc-studio-tools-latest.json"), "w", encoding="utf-8") as f:
        json.dump(info, f, indent=2)
        f.write("\n")
    print(json.dumps(info, indent=2))
    return info


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-zip", action="store_true", help="build the folder only")
    ap.add_argument("--all", action="store_true", help="also package the standard 3dmc-studio-tools zip for /toolbox/")
    a = ap.parse_args()
    build(make_zip=not a.no_zip)
    if a.all:
        package_standard()
