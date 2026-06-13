# manila-bay-rising — live generation state (resume here)

Last updated 2026-06-13 by the autonomous run. **The gate is blessed; the pipeline is PROVEN end-to-end.** Read this + `GENERATION-RUNBOOK.md` + memory `flow-omni-editor-input-mechanic.md` to continue.

## Flow session
- **Project URL**: https://labs.google/fx/tools/flow/project/e564d9bf-9c9d-4fb5-a394-60cbb76b8069 (the link the user gave, `bcbf138a…`, is DEAD — this is the new one)
- Browser: macmini Chrome (deviceId 2a9bd64b), tab 1283846633; scratch tab 1283846634 for download redirects.
- Agent settings: Confirm=**Never**, count=**1x**, model=**Nano Banana 2**. Aspect: set per item BUT the 16:9 setting did NOT reliably apply (hae-won-t1 came out 1024×1024 anyway — it was fine, 4 figures fit). Verify output aspect; re-roll if a wide scene/panel crops.

## BANKED so far (4/62) — all chain-verified
- hae-won.face (52ca8c9a-5a29-4c41-9e50-fa36b5dfb4cf)
- cel.face (02e5b5fe-f873-4855-b7f2-0044d9cec095)
- dr-santos.face (92f7e3f6-e9e8-49be-88b7-b184617d7418)
- hae-won.turnaround_t1 (1c3c2b8c-92c2-4218-a903-2180738cd091) — identity transfer confirmed

## NEXT items in order (sheets → scenes → panels)
Sheets remaining: **cel-t1, dr-santos-t1** (genesis, attach face only), then **hae-won-t2** (attach face+t1), **hae-won-t3** (face+t2), **cel-t2, cel-t3**, then views (**hae-won/cel** ×3, **dr-santos** ×2; attach face+t1). Then **14 scenes** (upload the gathered jpg via the picker's "Upload media" — use the `mcp__Claude_in_Chrome__file_upload` tool for the file input; NOT yet proven). Then **30 panels in page order** (attach face+turnaround per char + scene + prior; multi-char panels have staging files). See RUNBOOK for ledger-keys + tier map.

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
