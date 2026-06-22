# Flow Studio Tools (Chrome extension)

One toolbox for Google Flow projects — replaces the separate downloader / review-harvester / flow-to-studio extensions. Built on a **single tRPC harvest** (`flow.projectInitialData`: prompts + input refs + outputs + model + account), so every action reads the same data.

**Four actions:**
- **Download** — save the output images to disk (full-res), into a per-project folder.
- **→ Studio** — push the outputs straight into a 3DMC Comic Studio project (ingest).
- **Review** — export a bundle: outputs + the deduped input reference images + a `manifest.json` pairing each output with its prompt, model, refs, seed.
- **🗑 Delete** — tick tiles on the page, then Move to Flow's **Trash** (soft/recoverable). Guarded: shows the active account + requires typing the exact count to confirm. (`flow-delete.js`.)

The first three use a count selector (5 / 10 / 25 / # / **Whole project**); the panel shows the **active Flow account** up top.

**Phase 3 (next):** once proven, retire the four standalone Flow extensions from the Extensions page. See `../FLOW-TOOLKIT-PLAN.md`.

## Install (unpacked)
1. Chrome → `chrome://extensions` → **Developer mode** on.
2. **Load unpacked** → this folder (`studio/extension/flow-studio-tools`). Or download it from the admin **Extensions** page.

## Set up (once, for → Studio)
In the Studio open **⚙ Flow import**, copy the **Bridge URL** + **key**, then in the panel's **⚙** paste them and Save. (Download / Review need no setup.)

## Use
Open a Flow project (`labs.google/fx/tools/flow/project/...`). Pick a tab (Download / → Studio / Review), then a count. Done.

## Notes
- Harvest is tRPC-first (`FlowCore.getProject()` in `flow-core.js`), with a DOM scan as fallback — one place to fix if Flow changes.
- `chrome.downloads` + the bridge `ingest` both fetch with your logged-in sessions, sidestepping page CORS.
- The four older extensions (bulk-downloader, review-harvester, flow-to-studio, bulk-delete) stay installed until this is proven, then retire (Phase 3).
