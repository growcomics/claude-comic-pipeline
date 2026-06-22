# Flow Toolkit — consolidation plan

> **Status: plan / proposal (2026-06-22).** Goal: fold the four separate Flow
> browser extensions into ONE, sharing a single harvester + config, so there's
> one install, one UI, and one place to fix when Flow's page changes. No build
> yet — this is the map + the decisions to make first.

## 1. What exists today (4 extensions)

| Extension | Ver | What it does | How it reads Flow | Perms |
|---|---|---|---|---|
| `flow-bulk-downloader` | 1.0.0 | Download every image to disk, full-res | **DOM scanner** (scroll gallery, collect `<img>`) | downloads |
| `flow-to-studio` | 1.0.0 | Push images into a 3DMC Studio project (ingest) | **DOM scanner** (same code) | storage |
| `flow-review-harvester` | 1.1.0 | Export output+prompt+input-refs+model+manifest review bundle | **tRPC `flow.projectInitialData`** (one API call, structured) + account check | downloads |
| `flow-bulk-delete` | 0.1.0 | Select tiles → soft-delete (clicks each "Move to Trash") | **DOM tiles + button clicks** (no scanner) | storage, scripting, activeTab |

**The problem:** the gallery scanner is duplicated in 2–3 of them and drifts; 4 separate installs to manage; inconsistent UIs; and when Flow changes its DOM/API, every copy needs the same fix.

## 2. The key insight

There are two ways to read a Flow project, and one is strictly better:
- **DOM scanner** (downloader, flow-to-studio): scroll + scrape `<img>` URLs. Gets *output images only*, brittle to layout changes.
- **tRPC `flow.projectInitialData`** (review-harvester): one same-origin API call returns *everything* — each generation's prompt, **input reference images**, output media, model, timestamp — plus the active account.

So the unified extension should **standardize on the tRPC harvest as the single source of truth** (DOM scan only as a fallback). Every action then operates on one rich, normalized dataset.

## 3. Proposed architecture — "Flow Toolkit"

One MV3 extension. A shared core + one panel + four action modes.

- **`flow-core.js` (shared):** `getProject()` → tRPC `projectInitialData`, normalized to `[{id, prompt, inputs[], outputs[], model, ts}]`; `getAccount()` → `/fx/api/auth/session` + the `data-flow-account` stamp; `scanDOM()` fallback. **One harvester — kills the drift.**
- **One injected panel** with an action switcher:
  - **Download** → disk, full-res (from downloader).
  - **Send to Studio** → bridge `ingest` (config: Studio URL + key) (from flow-to-studio).
  - **Review bundle** → output + prompt + input-refs + `manifest.json` (from harvester).
  - **Bulk delete** → select → soft-delete to Trash, **guarded** (from flow-bulk-delete).
- **One config** (`chrome.storage`): Studio URL+key, download folder, "confirm account before destructive".
- **Account safety banner:** always show the active Flow account in the panel; require an explicit confirm before *delete* (the dual-account rule — growcomics vs marrtrobinson).
- **Manifest = union:** perms `downloads, storage, scripting, activeTab`; hosts `labs.google`, `*.googleusercontent.com`, `flow-content.google`, `3dmusclecomics.com`.

## 4. Phasing

- **Phase 1 — safe core.** Extract `flow-core.js` (tRPC harvest + account). Build the panel with the three non-destructive actions: **Download, Send to Studio, Review bundle** (they all just consume the harvest). Package to the admin Extensions page; test against a real Flow project.
- **Phase 2 — delete (guarded).** Fold in bulk-delete as a visually distinct tab with: explicit multi-select, a dry-run count, a typed/confirm step, and clear "soft delete → recoverable in Trash" messaging. It's destructive + currently v0.1, so it gets its own hardening pass.
- **Phase 3 — cut over.** Replace the four Extensions-page entries with the single **Flow Toolkit**; keep the old singles for one release as fallback, then retire them.

## 5. Decisions needed before building

1. **Bulk-delete: include or keep separate?** One extension is the goal, but putting a destructive action in the same panel as the everyday ones risks an accidental click. Options: (a) include it as a heavily-guarded, separated tab; (b) keep delete as its own standalone extension and consolidate only the three safe tools.
2. **Name** — e.g. `Flow Toolkit`, `Flow → 3DMC`, `Flow Studio Tools`.
3. **Harvest source** — adopt tRPC-first (recommended; richer + more robust) vs keep the DOM scanner.

## 6. Risks / notes
- `flow.projectInitialData` is an internal Flow API; if Google changes it, the core needs an update (but it's one place, vs three scanners today).
- Bulk-delete depends on Flow's "Move to Trash" control text/markup — most fragile piece; keep its selectors isolated + easy to patch.
- Account confirm is non-negotiable for delete (deleting on the wrong account is the worst-case error).
