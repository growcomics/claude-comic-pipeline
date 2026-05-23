# Runbook — Execute the remaining 4 panels

This experiment only ran 1 of 5 panels (`p05-02`) end-to-end in the session that authored it, because Flow's asset picker proved to be the rate-limiting bottleneck for multi-ref attachment when driven through Chrome MCP. The other 4 panels (`p02-02`, `p05-04`, `p03-03`, `p01-01`) are fully specified in [`recipes.md`](recipes.md) and ready to execute.

This runbook is what Matt or Magnamus follows to fill them in.

## Setup (do once)

1. Open Flow at the experiment's project: https://labs.google/fx/tools/flow/project/ece3f3b6-e5fd-4809-931a-9cb1d5b90320
2. Confirm Nano Banana Pro is selected (chip at bottom right of prompt area), count=x4 (Flow's default — leave it).
3. Confirm the 9 renamed refs are present in the asset library — search for "mundy", "heather", "lenny", "carl", "lab" to verify:
   - `mundy-face.png`, `mundy-tier3.png`, `mundy-tier4.png`
   - `heather-face.png`, `heather-tier3.png`, `heather-tier4.png`
   - `lenny-face.png`, `carl-face.png`
   - `lab-mundy-a.jpg`

   If they aren't there, re-upload from `/tmp/exp03-refs/` (created during the experiment author's run).

## Per panel

Repeat for each panel in `recipes.md`:

### Step 1 — Variant A (control / one-shot)

1. Open the prompt at bottom of project view (no refs attached).
2. Click `+` → search for the refs listed in the panel's Variant A → click ref → "Add to Prompt." Iterate until all the listed refs are attached. Verify thumbnail row shows the expected count.
3. Paste the Variant A prompt verbatim into the prompt box.
4. Submit (→ arrow). Wait for the 4-up to render (~30-60s).
5. The 4 variants are now in the gallery. Don't pick yet — leave them for the blind rating.

### Step 2 — Variant B (multi-pass) ingredients

For each ingredient (typically 2-3 per panel):

1. Click `+` → attach the ingredient's listed refs.
2. Paste the ingredient prompt.
3. Submit. Wait for 4-up.
4. **Pick the strongest variant from the 4-up** — click into the variant, mark it (you can rename it to e.g. `p05-02_ingredient-mundy_pick`) or just remember its position.

### Step 3 — Variant B composite

1. Click `+` → search for the picked ingredient outputs from Step 2 (recency-sorted, so they're at the top of the asset list).
2. Attach all 2-3 ingredients as refs. Verify thumbnail row count.
3. Paste the composite prompt verbatim.
4. Submit. Wait for 4-up.

### Step 4 — Capture URLs

Open the browser dev console on the Flow project page and run:

```js
Array.from(document.querySelectorAll('img'))
  .map(i => i.src)
  .filter(s => s.includes('media.getMediaUrlRedirect'))
  .slice(0, 8)
```

The 8 newest URLs are the 4 multi-pass composite + 4 control outputs (in that order — newest first because the composite was submitted last). Paste them into `outputs/README.md` under a new section for this panel.

### Step 5 — Add the pair to `ab-ratings.md`

Copy the p05-02 section template, change the panel ID, fill in nothing — leave it blank for blind rating.

## Rating round (do after all 5 panels are generated)

1. Open `ab-ratings.md`.
2. **Don't peek at the reveal section at the bottom** until you've rated.
3. Open Flow, line up the X and Y 4-ups side by side for each panel.
4. Fill in the table per rater (Matt, Magnamus).
5. After all 5 panels are rated, expand the reveal, count the preferences.

## Decision

If multi-pass wins ≥ 70% of pairs (≥4 out of 5): ship the `composition_mode: "build_up"` flag on a **separate follow-up branch** (not on this experiment branch).

If it wins < 70%: write up the categories where multi-pass clearly helped (if any) and ship as a targeted-use tool. If it doesn't win anywhere, document the negative result and close the experiment.

Either way, update `CHANGELOG.md` with the final findings on the same dated section the scaffold added.

## Estimated time

~15 minutes per panel through Flow's UI (4 panels × ~15 min = ~1 hour, plus rating time).

## Known UI gotchas (encountered during smoke-test)

- Flow's asset-picker `Add to Prompt` button position drifts as the picker re-renders. Always screenshot before clicking, don't batch coordinate-clicks blindly.
- Clicking a thumbnail in the main gallery opens its edit view, not a select-for-prompt. Use the `+` flow.
- Filenames with duplicate basenames (`face-card.png` × 4 characters) can't be distinguished in the picker. The refs were pre-renamed in `/tmp/exp03-refs/` to avoid this — keep that naming.
- Flow's NSFW filter sometimes drops one variant out of the 4-up silently (we saw 3/4 for Heather mid-growth tier 3). Re-running usually clears it (memory `feedback_nsfw_retry_policy.md`).
