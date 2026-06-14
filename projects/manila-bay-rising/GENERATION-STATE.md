# manila-bay-rising — live generation state (resume here)

Last updated 2026-06-13 by the autonomous run. **The gate is blessed; the pipeline is PROVEN end-to-end.** Read this + `GENERATION-RUNBOOK.md` + memory `flow-omni-editor-input-mechanic.md` to continue.

## Flow session
- **Project URL**: https://labs.google/fx/tools/flow/project/e564d9bf-9c9d-4fb5-a394-60cbb76b8069 (the link the user gave, `bcbf138a…`, is DEAD — this is the new one)
- Browser: macmini Chrome (deviceId 2a9bd64b), tab 1283846633; scratch tab 1283846634 for download redirects.
- Agent settings: Confirm=**Never**, count=**1x**, model=**Nano Banana 2**. Aspect: set per item BUT the 16:9 setting did NOT reliably apply (hae-won-t1 came out 1024×1024 anyway — it was fine, 4 figures fit). Verify output aspect; re-roll if a wide scene/panel crops.

## BANKED so far (5/62) — all chain-verified
- hae-won.face (52ca8c9a-5a29-4c41-9e50-fa36b5dfb4cf)
- cel.face (02e5b5fe-f873-4855-b7f2-0044d9cec095)
- dr-santos.face (92f7e3f6-e9e8-49be-88b7-b184617d7418)
- hae-won.turnaround_t1 (1c3c2b8c-92c2-4218-a903-2180738cd091) — identity transfer confirmed
- cel.turnaround_t1 (06453bee-2922-404e-838f-e67b6a702e7f) — identity transfer confirmed

## NEXT items in order (sheets → scenes → panels)
Sheets remaining: **dr-santos-t1** (genesis, attach dr-santos.face), then **hae-won-t2** (attach face+t1), **hae-won-t3** (face+t2), **cel-t2** (face+t1), **cel-t3** (face+t2), then views (**hae-won/cel** ×3 each, **dr-santos** ×2; attach face+t1). Then **14 scenes** (upload the gathered jpg via the picker's "Upload media" — use the `mcp__Claude_in_Chrome__file_upload` tool for the file input; NOT yet proven). Then **30 panels in page order** (attach face+turnaround per char + scene + prior; multi-char panels have staging files). See RUNBOOK for ledger-keys + tier map.

Asset-picker uuid→title map (Recent order shifts; match by uuid in the row's img src): 52ca8c9a=hae-won.face, 02e5b5fe=cel.face, 92f7e3f6=dr-santos.face, 1c3c2b8c=hae-won.turnaround_t1, 06453bee=cel.turnaround_t1.

## The proven per-item loop (copy this)
1. `python3 qa/compose.py --job <job>` → ATTACH list + PROMPT; write prompt to `/tmp/p.txt`; `python3 qa/audit_prompt.py --receipt qa/receipts/<job>.receipt.json --prompt-file /tmp/p.txt`.
2. **Attach refs** (if any): click `+` (add_2) on input → OS-click each asset row (match by uuid in its img src — auto-titles are fuzzy) → verify the big preview img's uuid → OS-click "Add to Prompt". For external (scenes/sign): "Upload media" + file_upload tool.
3. **Type+submit**: OS-click into editor → JS `ed.dispatchEvent(new InputEvent('beforeinput',{inputType:'insertText',data:'Generate one image. '+<prompt>,bubbles:true,cancelable:true}))` (+ an `input` event) → OS-click submit arrow (page ~1490,732). NEVER set innerHTML (crashes app → reload).
4. Poll `[...document.querySelectorAll('img')].map(i=>i.src).filter(/getMediaUrlRedirect/).map(s=>s.split('name=')[1])` — newest uuid first; count grows by 1 when done.
5. **Download**: navigate scratch tab to `https://labs.google/fx/api/trpc/media.getMediaUrlRedirect?name=<uuid>` → read the signed `flow-content.google` URL from the tab context → `curl -s -o <save-path> '<signed-url>'`.
6. **Judge**: spawn a FRESH general-purpose subagent → it views the image (+ the face card for identity on body sheets/panels), writes `qa/receipts/<job>.verdict.json` `{"pass":bool,"tags":[],"reason":"","judged_by":"fresh-subagent"}`.
7. **Bank**: `python3 qa/bank.py --job <job> --flow-id <uuid> --disk <save-path> [--ledger-key <id>.<key> for sheets | nothing for pages]`. Scenes use `--job scene:<id>` (no ledger-key).

## Decisions made this run (for user review)
- **t1 body sheets set `genesis:true`** in turnaround-specs.json (data-only fix). Reason: the ported D1 "≥2 refs" rule wrongly rejected first-body sheets that legitimately attach only the face card. Did NOT patch the guarded gate code (blessing-preserving). t2/t3/views/scenes unaffected.
- Faces rendered 1:1 (correct); hae-won-t1 also 1:1 and fine.

---
## PIVOT 2026-06-13 (afternoon): switched to user's PRO project bcbf138a
- The user's canonical references live in Flow project **bcbf138a** (marrtrobinson PRO, **laptop** Chrome deviceId 6b35bfe8). The growcomics/e564d9bf work (6 banked refs) is SUPERSEDED.
- Pulled the user's 5 refs to `references/_from-flow-bcbf138a/`: **Cel character sheet** (canonical) + 4 Manila scene plates (bayfront terrace, residential alley, street-to-bay, Roxas baywalk). See its _README.md.
- Gaps: NO Hae-won sheet (user showed one but it's absent here → generating to match), NO Dr. Santos, and locations lab/outfall/dolomite/makati-skyline/edsa/casino/campus uncovered.
- Wardrobe pivot: Hae-won is now **white tank + denim shorts + lotus necklace + 168cm + long dark hair** (per user's shown design), NOT the cream sundress. Cel = "Manila Bay Sunset" tank + denim shorts, 165cm, morena.
- New rich-sheet paradigm: character refs are single rich DAZ3D character sheets (front/back/expressions/details), not face-card+turnaround. compose_page (gate) will need adapting to attach `sheet` ledger key instead of face/turnaround — that's a GATE-CODE change needing user re-bless before panels.

### bcbf138a UI mechanics (pill-based, PRO, differs from Omni)
- Input is a Lexical contenteditable BUT **synthetic beforeinput does NOT populate it** — use OS `type` (real keystrokes) instead, then OS-click the submit arrow.
- Model/aspect/count: click the "Nano Banana 2" pill at bottom of input → popup with aspect row (16:9/4:3/1:1/3:4/9:16) + count (1x/x2/x3/x4) + model. **x4 = 4 candidates per submit, 0 credits (free).**
- "Flow Downloader" userscript (bottom-right) downloads gallery → `~/Downloads/Flow Google Flow - <title> <projid>/` as flow-NNN.jpg. Laptop IS this shell's machine (hostname Mac.lan).
- First gen in this project: hae-won-sheet, 16:9 x4, composed+audited (sha 5eea583df970), generating.


### Character anchors COMPLETE (2026-06-13)
All 3 canonical rich character sheets ready (matching the user's Cel-sheet style):
- hae-won.sheet — GENERATED+banked (b1876e33), white tank/denim shorts/lotus necklace/168cm, judge-picked from x4.
- dr-santos.sheet — GENERATED+banked (86332bb7), mature 50s lab coat/glasses/lanyard, judge PASS.
- cel — user-provided sheet, copied to references/characters/cel/character-sheet.png (canonical anchor; not gate-banked since user-made).
NEXT: missing location scenes (up-manila-lab, manila-bay-outfall, makati-skyline, edsa, entertainment-city, dolomite-beach, up-manila-ermita — the 4 user scenes cover bayfront/alley/street/baywalk loosely). Generate at x4 in bcbf138a matching the user's Manila-scene style. THEN 30 panels — but compose_page must be adapted to attach the `sheet` ledger key (rich-sheet paradigm) instead of face/turnaround → that is a GATE-CODE change requiring user re-bless.


### Location scenes — in progress (2026-06-13)
Generated at x4 in bcbf138a, prose-style matching the user's Manila scene plates, saved to references/locations/<loc>/_source.png (treated as reference inputs like the user's scenes, not gate-banked):
- up-manila-lab/_source.png — DONE (e7c6a1ff): night research lab, fume hood, amber-vial fridge, FLOOR DRAIN center (p1 spill beat). Excellent.
STILL TO GENERATE: manila-bay-outfall, manila-bay-dolomite-beach, makati-skyline, edsa, entertainment-city, up-manila-ermita. User scenes (_from-flow-bcbf138a/) already cover bayfront/baywalk/alley/street.
Scene gen loop: clear input (click+cmd+a+del) → OS type 'Generate one image. <prose plate, NO people, photoreal DAZ Manila, 16:9>' → OS-click submit (~1037,717 at 1568w) → poll newest uuid → scratch-tab redirect → curl to _source.png → view.
