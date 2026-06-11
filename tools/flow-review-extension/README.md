# Flow Red-Pen — comic production QA extension

Tags Flow generations with **production-QA verdicts** keyed by media uuid (the same
`getMediaUrlRedirect?name=<uuid>` ids the pipeline logs in `pages-log.json`), so your
clicks merge directly into Claude's fix queue with zero translation.

## Install (one time, ~30 seconds)

1. Chrome → `chrome://extensions`
2. Toggle **Developer mode** (top right)
3. **Load unpacked** → select this folder
   (`~/Documents/claude-comic-pipeline/tools/flow-review-extension`)
4. Open your Flow project. Hover any generation → the tag bar appears.

## Tags → fix recipes

Each tag is a *systemic* failure category that maps to a concrete regen recipe:

| Tag | Means | Claude's fix recipe |
|---|---|---|
| ✓ accept | Page is good | Locked, never regenerated |
| ★ gold | Best-of-the-best | Attached as style anchor on every regen |
| 📐 angle | Too front-facing / camera not as specced | Camera fragment moved to prompt front + angle-matched view-pack ref attached + re-roll |
| 😐 face | Expression flat / wrong emotion | Per-beat expression block injected (from shotlist dialogue type + transformation beat) + re-roll |
| 🖼️ refs | Needs fuller reference stack | Re-roll with FULL stack: face card + body tier + view ref + env ref + prior accepted panel |
| 📏 size | Under tier / downsized | Re-roll with anchor + lineup + escalated size language, gated vs anchor |
| 👗 ward | Wardrobe/continuity wrong | Re-roll with prior-panel state anchor + explicit costume-state carry-forward |
| 🎨 style | 2D / not photoreal CGI | Re-roll with boosted CGI anchor prefix |
| ✗ reject | Useless | Full re-roll with all of the above |
| 📝 note | Free text | Read verbatim, folded into the regen prompt |

Multiple tags combine (e.g. 📐+😐 = camera fix AND expression fix in one re-roll).

## Hand the verdicts back

Click the floating **⤓ red-pen verdicts (N)** pill (bottom-left) → a
`flow-redpen-verdicts-<timestamp>.json` lands in `~/Downloads`.
Tell Claude the exact filename (Downloads is shared — exact names only).
Double-click the pill to clear all verdicts.

## Notes

- Verdicts persist in `chrome.storage.local` across reloads until you clear them.
- Tiny thumbnails (<120 px, e.g. attached-ref chips) are deliberately not decorated.
- Works on any Flow project — it keys off media uuids, not this comic specifically.
