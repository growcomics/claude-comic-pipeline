# Flow Red-Pen — comic production QA extension (v0.2.0, taxonomy D1–D14)

Tags Flow generations with **production-QA verdicts** keyed by media uuid (the same
`getMediaUrlRedirect?name=<uuid>` ids the pipeline logs), so your clicks merge directly into
Claude's fix queue with zero translation. The tag set is **regenerated from the per-project
defect registry** (`projects/<project>/qa/defect-registry.json`) — registry first, then this file.

## Install (one time, ~30 seconds)

1. Chrome → `chrome://extensions`
2. Toggle **Developer mode** (top right)
3. **Load unpacked** → select this folder
   (`~/Documents/claude-comic-pipeline/tools/flow-review-extension`)
4. Open your Flow project. Hover any generation → the tag bar appears.
5. After any update to this folder: hit ↻ on the extension card, then reload the Flow tab.

## Tags → fix recipes

| Tag | Means | Claude's fix recipe |
|---|---|---|
| ✓ accept | Page is good | Locked, never regenerated |
| ★ gold | Best-of-the-best | Style anchor on every regen; positive exemplar for QA calibration |
| 🖼️ refs (D1/D5) | Ref stack thin/wrong, identity or continuity drift | Re-roll with full stack: turnaround + face + scene rung + staging + prior panel |
| 🔤 prose (D11) | Appearance was written in prompt text instead of carried by refs | Attach every character's face+turnaround; pointer-only language; re-roll |
| 🎲 vary (D12) | The 4 variants diverge wildly in blocking | Re-roll with maximal structured JSON prompt (per-limb staging pinned) |
| 🖐️ anatomy (D13) | Extra/phantom limbs or hands | Per-hand accounting + total-hands line + staging ref; auto-reject on count mismatch |
| 😐 face (D2) | Expression flat / wrong emotion | Per-beat expression block; re-roll |
| 📐 angle (D3) | Too front-facing / camera not as specced | Camera-first prompt + angle-matched turnaround view; re-roll |
| 👗 ward (D4) | Outfit wrong/inconsistent vs wardrobe state | Re-roll against the state turnaround + prior panel |
| 📏 size (D6/D14) | Muscle size under tier OR far below the size anchor | Anchor-first identity swap (anchor = PRIMARY image, enumerated keep-list), wide aspect, literal side-by-side gate |
| 🧍 height (D7) | Giant/shrunken vs height chart | Height-pinned turnaround (scale silhouette + grid) + height clamp language; re-roll |
| 📷 scene (D8) | Background invented / scene-ref proximity mismatch | Generate/attach the scene-ladder rung matching the shot distance; re-roll |
| 🧩 staging (D9) | Pose/interaction staging wrong | Generate staging ref → inspect/perfect it → re-roll page from it |
| ⚡ vfx (D10) | Effect too perfect / AI-looking | Re-roll with vfx-style-bible vocabulary (DAZ store-prop + postwork look) |
| 🎨 style | Not photoreal CGI | Boosted CGI anchor prefix; re-roll |
| ✗ reject | Useless | Full re-roll under all applicable gates |
| 📝 note | Free text | Read verbatim, folded into the regen prompt |

Tags combine (📐+😐 = one re-roll with both fixes). ✓/✗ are mutually exclusive.

## Hand the verdicts back

Click the floating **⤓ red-pen verdicts (N)** pill (bottom-left) → a
`flow-redpen-verdicts-<timestamp>.json` lands in `~/Downloads`.
Tell Claude the exact filename (Downloads is shared — exact names only).
Double-click the pill to clear all verdicts.

## Notes

- Verdicts persist in `chrome.storage.local` across reloads until you clear them.
- Tiny thumbnails (<120 px, e.g. attached-ref chips) are deliberately not decorated.
- Works on any Flow project — it keys off media uuids, not one comic.
- Doctrine behind the taxonomy: `skills/comic-production/references/qa-defect-doctrine.md`.
