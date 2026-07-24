# 3DMC Studio Tools (Chrome extension)

> Chrome-displayed name: **3DMC Studio Tools** (renamed from "Flow Studio Tools" in v2.0.0, since it now spans Flow *and* Patreon). The repo folder stays `flow-studio-tools/`.

**v2.0.0** — one extension for the whole comic pipeline. It consolidates **six** homegrown extensions: on **Google Flow** it Downloads / Sends / **Auto-syncs** to the Studio / exports Review bundles / Bulk-deletes; on **Patreon** it bulk-downloads a post's gallery. Two non-overlapping surfaces, one install.

## Flow side (`labs.google/fx/tools/flow/*`)

Built on a **single tRPC harvest** (`flow.projectInitialData`: prompts + input refs + outputs + model + account), so every action reads the same data. The panel (bottom-right) shows the **active Flow account** up top.

- **Download** — save the output images to disk (full-res), into a per-project folder.
- **→ Studio** — push outputs into a 3DMC Comic Studio project (ingest). Two modes:
  - **Manual:** pick a count (5 / 10 / 25 / # / **Whole project**) and send once. Blank section field = a fresh Studio section each send; type a name to append.
  - **Auto-sync (NEW):** type a **section name**, then flip **Auto-sync ON**. From then on, every *new* Flow generation in this project is pushed into that section automatically as it lands — no manual sends. Configurable interval (default 20s, min 8s). It dedupes per-project (a "seen" set in `chrome.storage`), so nothing double-imports, and tracks each Flow project separately. *(Replaces the old Flow → Studio Auto-Sync / Auto-Pull extensions.)*
- **Review** — export a bundle: outputs + deduped input reference images + a `manifest.json` pairing each output with its prompt, model, refs, seed.
- **🗑 Delete** — tick tiles on the page, then Move to Flow's **Trash** (soft/recoverable). Guarded: shows the active account + requires typing the exact count to confirm. (`flow-delete.js`.)
- **Prompt buttons (v2.2.0; insert rewritten in v2.2.2; Director added in v2.3.0)** — one-click insert of canonical prompt blocks into Flow's composer, for manual driving sessions: **🎥 Director** *appends* the scene-adaptive reframe block (attach a source panel as ref — the scene, poses, lettering, and lighting stay; the model chooses the camera move — dolly / orbit / height / zoom — for that specific beat, with an explicit "don't default to a low hero angle" guard; unlike the fixed blocks it never ruts into one angle), **📷 Cine+Light** *appends* the cinematic-framing + golden-hour volume-lighting master block, **🎬 Framing** *appends* the cinematic-framing block **only** (hero staging, no lighting — for pairing with a separate lighting choice, or when you'll relight afterward), and **🎨 DAZ style** *prepends* the canonical style prefix from `prompt-templates.md` (exact tested wording). Cine+Light and Framing prescribe a **fixed** camera, so they're for **fresh** generations; Director is **for** i2i reframes. None of the three camera blocks may be paired with the i2i keep-composition lock sentence — Director's whole job is to move the camera, and the fixed blocks fight the lock. **How the insert works:** Flow's composer is a Slate editor whose model ignores `execCommand`/`beforeinput` (text put in that way vanished on blur/submit — the v2.2.1 bug). So the insert now goes through Slate's own `editor.insertText` via a `world:"MAIN"` injector (`flow-inject.js`): `content.js` (isolated world) hands the block to it over a shared-DOM bridge, and it inserts into Slate's model + calls `onChange()`, so the text persists exactly like typed input. Verified live against the real composer (2026-07-19). A textarea path remains for any non-Slate surface.

## Patreon side (`www.patreon.com/*`)

A self-contained module (`patreon.js`) — completely separate from the Flow panel. On any Patreon **post** page (`/posts/…`) a small **Patreon Gallery** panel appears (bottom-right). Click **⬇ Download all images** to save every full-res gallery image to `Downloads/Patreon/<post-slug>/`. It re-fetches the current post fresh and filters by post id, so it never grabs the wrong post's images (the SPA stale-data bug). Downloads run in the background worker, so they survive closing the panel or navigating away. *(Replaces the Patreon Gallery Downloader extension.)*

> **Naming:** resolved — the extension was renamed to **3DMC Studio Tools** (was "Flow Studio Tools") because it now spans Flow *and* Patreon. The `FlowCore` object and the `flow-studio-tools/` folder keep their names internally. See `../FLOW-TOOLKIT-PLAN.md` Phase 4.

## Install (unpacked)
1. Chrome → `chrome://extensions` → **Developer mode** on.
2. **Load unpacked** → this folder (`studio/extension/flow-studio-tools`).
3. After testing both surfaces, remove the now-redundant standalone extensions (Flow Bulk Image Downloader, Flow Review Harvester, Flow → Studio Auto-Sync, Flow → Studio Auto-Pull, Flow Bulk Delete, Patreon Gallery Downloader). Leave **Chrome Remote Desktop** — that's Google's, not ours.

## Set up (once, for → Studio / Auto-sync)
In the Studio open **⚙ Flow import**, copy the **Bridge URL** + **key**, then in the panel's **⚙** paste them and Save. (Download / Review / Patreon need no setup.)

## Notes / architecture
- Flow harvest is tRPC-first (`FlowCore.getProject()` in `flow-core.js`) — one place to fix if Flow changes.
- Cross-origin image fetches (Flow media redirects → CDN; bridge ingest; Patreon CDN) all happen in the **service worker** (`background.js`), sidestepping page CORS. Auto-sync reuses the existing port-based `studio` ingest path rather than duplicating a bridge client.
- The two content scripts share `background.js` but never each other's UI/globals — Flow on `labs.google`, Patreon on `patreon.com`, no overlap.
