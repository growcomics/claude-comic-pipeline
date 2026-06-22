# Flow → 3DMC Studio (Chrome extension)

Send a Google Flow project's images straight into the [Comic Studio](https://3dmusclecomics.com/studio) — no manual download/upload.

## Install (unpacked)
1. Chrome → `chrome://extensions` → toggle **Developer mode** (top-right).
2. **Load unpacked** → choose this folder (`studio/extension/flow-to-studio`).

## Set up (once)
1. In the Studio, open **⚙ Flow import** (on the projects page) and copy the **Bridge URL** + **Your Studio key**.
2. Open a Google Flow project (`labs.google/fx/tools/flow/...`). A **→ 3DMC Studio** panel appears bottom-right.
3. Click its **⚙**, paste the URL + key, **Save settings**.

## Use
1. On any Flow project page, set the **Studio project** name (defaults to the Flow title — created in Studio if new).
2. **Send 5 / 10 / 20 / #** most-recent, or **Send ALL to Studio**. It scrolls the gallery, grabs full-resolution images, and pushes each into the project.
3. Open the project in the Studio → organize (Compare / One beat each) → Port to a comic.

## Notes
- The key authorizes writes to your Studio (`studio/data/bridge.json`); rotate it there if it leaks.
- Images arrive ungrouped in upload order; use **One beat each** (sequence) or **Compare** (variants) to organize.
- Harvesting logic is shared with the Flow Bulk Downloader; this variant POSTs to the Studio instead of saving to disk.
