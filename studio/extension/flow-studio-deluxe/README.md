# Flow Studio Deluxe (GENERATED — do not edit)

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
