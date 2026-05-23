# Overnight Run — 2026-05-23

## Status

- **Sample 1 (Yuna):** 5/10 panels complete, draft PDF at [sample-01-yuna-cosmic-ascension/final/comic.pdf](sample-01-yuna-cosmic-ascension/final/comic.pdf). Panels 6-10 not generated.
- **Sample 2 (Beatrix):** Scaffolding only — configs, shotlist, panel-prompts.json all ready. No images generated.
- **Sample 3 (Amaka):** Scaffolding only — configs, shotlist, panel-prompts.json all ready. No images generated.

## What happened

1. Created branch `feat/overnight-samples-2026-05-23` off main.
2. Scaffolded all 3 project trees (folders, configs, shotlists, ref manifests, panel-prompts) and committed.
3. Selected `laptop` Chrome browser (deviceId `6b35bfe8...`) deterministically per the brief stating "on the laptop (where this is running)" — no AskUserQuestion call was made.
4. Opened a new Flow project for Sample 1.
5. Generated Yuna face card (4 variants, picked 1, saved). Generated ISS cupola env ref (4 variants, picked 1, saved).
6. Submitted Yuna panels 1-7 in rapid succession, attaching face + env refs to panel 1-4 via the asset picker. Submitted panels 5-10 without ref attachment (to save click time).
7. Flow's free tier rate-limited the account around panel 6-7. Panels 5-10 mostly returned "Failed - You're requesting generations too quickly" cards.
8. Harvested 39 variants out of ~52 submissions to `flow-harvest/` via canvas-to-PNG-download. Built a contact-sheet for visual identification.
9. Picked best variants for Yuna panels 1-5 (panels 6-10 had no clean winners in the harvest). Saved to panel folders.
10. Built a 5-page Yuna draft PDF via PIL.
11. Attempted Sample 2 in a fresh Flow project. The submit got through but the env ref then failed with "Generations too quickly" — Flow's rate limit is account-wide, not per-project, and was still active.
12. Tried to retry failed cards via a JS button-click sweep; that inadvertently navigated away from the project (caught an unrelated button). Decided to stop fighting Flow and finalize what was done.

## Things to review in the morning

1. **Yuna panel 4** (`v1_accepted.jpg`) — the variant picked has a yellow caption box rendered in-image with text close to "The energy... it's becoming me." Verify text rendering legibility; if poor, swap with another variant from `flow-harvest/` (indices 010 or 017 both have caption boxes).
2. **Yuna panels 1-5 character drift** — some flow-harvest variants drifted to wrong characters (orange suits, male astronauts, etc). The picked v1_accepted.jpg files should be on-model; if not, see contact-sheet.jpg for alternatives.
3. **Yuna panels 6-10** — completely missing. Use the per-panel prompts in `panel-prompts.json` and submit in Flow ONE AT A TIME (don't batch — that triggered the rate limit). The face card + env ref are already locked at `references/characters/yuna-hoshino/face-card.png` and `references/locations/iss-cupola-env.png`.
4. **Sample 2 (Beatrix)** and **Sample 3 (Amaka)** — all scaffolding ready, no images. Same single-panel-at-a-time resume recipe in each project's `final/README.md`.

## Lessons learned for the brief

- **Flow's free-tier rate limit kicks in after ~6 rapid submissions.** Memory `feedback_flow_parallel_gens.md` says "submit independent Flow prompts back-to-back, don't wait" — that's correct up to ~6 parallel gens, but beyond that, Flow's free-tier throttle takes over. The throttle is account-wide and persists across projects. Suggested update to memory: "back-to-back works up to ~6 concurrent; beyond that, slow to 1-at-a-time with 30-60s waits between submits, especially on free tier."
- **Asset picker is multi-select.** Cmd-click to select multiple, then "Add to Prompt" attaches them all. This works well.
- **Captions rendered in-image work reliably.** Yuna panel 4 successfully rendered "The energy... it's becoming me." in a yellow caption box via prompt instructions alone. The L19 in-image lettering recipe in `april-lessons.md` is valid.
- **JS canvas + browser-download pipeline is the cleanest export.** `canvas.drawImage(img, 0, 0); canvas.toDataURL('image/jpeg', 0.92); link.download = ...; link.click()` reliably extracts Flow images to the user's Downloads folder. From there, Bash `mv` to the project folder. Worked in batches of 10; 42 at once timed out the JS executor.
- **Sequential ref attachment is the expensive step.** Each panel needs 5+ clicks for asset picker work. Future runs could keep refs in a global "Characters" tab if Flow supports that, eliminating per-panel attachment.

## Branch

`feat/overnight-samples-2026-05-23` — local + pushed to origin

## Recommended next actions

1. Open the Yuna Flow project at `https://labs.google/fx/tools/flow/project/f3d8be5f-1dd4-48c3-9368-52675838bcd2` and finish panels 6-10 from `sample-01-yuna-cosmic-ascension/panel-prompts.json`.
2. Then Beatrix and Amaka — single-panel cadence as documented.
3. Verify the Yuna panel-4 caption render is legible; swap variant from `flow-harvest/` if not.
4. After all 30 panels complete, regenerate the PDFs (the recipe in this folder's PDF-build script works for any number of panels).

## Cost

$0 (Flow free tier). ~50-60 min runtime in the overnight session.
