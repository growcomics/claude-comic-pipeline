# manila-bay-rising — generation runbook (Chapter 1)

Built 2026-06-13. The full compose→audit→submit→postflight→bank gate chain exists in `qa/` and is validated (all scripts ast-clean, all specs load, dry-run confirms the gate bites). Backend: **Flow** (signed in as growcomics@gmail.com; the old project link `bcbf138a…` is dead — a fresh Flow project will be created). Model pill: **Nano Banana 2**, count x4, aspect per job.

## STEP 0 — BLESS THE GATE (USER-ONLY, one time)

Claude is prohibited from blessing. Review the `qa/` diff, then run:

```bash
cd ~/Documents/claude-comic-pipeline/projects/manila-bay-rising
python3 qa/integrity.py --rebless --i-am-the-user
python3 qa/integrity.py            # should print: gates intact ✓
git add qa && git commit -m "manila-bay-rising: bless Ch1 qa gate chain"
```

Until this runs, every gate script `sys.exit(2)`s ("ALL GATES LOCKED") and nothing generates.

## The per-item chain (every scene / sheet / panel)

1. `python3 qa/compose.py --job <job>` → prints ATTACH list + single-line PROMPT, writes `qa/receipts/<job>.receipt.json`.
2. Write the prompt to a file; `python3 qa/audit_prompt.py --receipt qa/receipts/<job>.receipt.json --prompt-file /tmp/p.txt` → writes `.audit-pass`. Quote both PASS lines.
3. On Flow: verify the pill (NB2, x4, aspect), attach EXACTLY the receipt's list, paste the prompt verbatim, submit.
4. Download the pick. A **fresh-context subagent** judges it against `qa/judge-rubric.md` + `qa/defect-registry.json` → write `qa/receipts/<job>.verdict.json` with `{"pass":bool,"tags":[...]}`. Generator never grades its own work.
5. `python3 qa/bank.py --job <job> --flow-id <uuid> --disk <save-path> [--ledger-key <id>.<key> for sheets]` → enters ledger/scene_ladders/pages-log only if receipt+audit+verdict all present and verdict.pass.

`python3 qa/verify_chain.py` anytime audits for chainless entries.

## STEP 1 — Scenes (14 jobs) → `scene_ladders`
DAZ-convert each gathered location ref. Order doesn't matter; all establishing scenes are prerequisites for their panels.
```
scene:up-manila-lab   scene:up-manila-lab-reverse
scene:up-manila-ermita
scene:manila-bay-outfall   scene:manila-bay-outfall-reverse
scene:manila-bay-sunset
scene:manila-bay-dolomite-beach   scene:manila-bay-dolomite-beach-reverse
scene:makati-skyline   scene:edsa   scene:poblacion-night   scene:entertainment-city
scene:bayfront-hotel   scene:bayfront-hotel-reverse
```
Bank: `--job scene:<id> --flow-id <uuid> --disk <save from spec>` (no --ledger-key; banks into scene_ladders.<id>).

## STEP 2 — Character sheets (18 jobs, IN ORDER per character)
Faces first (genesis, prose-bootstrap — NO attach), then t1, then t2 (needs t1), t3 (needs t2), then views (need face+t1).
```
hae-won-face → hae-won-t1 → hae-won-t2 → hae-won-t3 → hae-won-view-{3q-full,profile,back-full}
cel-face → cel-t1 → cel-t2 → cel-t3 → cel-view-{3q-full,profile,back-full}
dr-santos-face → dr-santos-t1 → dr-santos-view-{3q-full,profile}
```
Bank each with `--ledger-key` from `references/turnaround-specs.json` (e.g. `--ledger-key hae-won.turnaround_t2 --disk references/characters/hae-won/body-tier2.png`).
NOTE: faces are prose-bootstrap (no seed/casting photo). If you want to anchor identity on a real face instead, drop a seed image in the char folder and add it to that face sheet's `attach` before composing — a correction you flagged you'd make.

## STEP 3 — Panels (30, IN PAGE ORDER) → `pages-log`
Pages must run in order: many panels' `continuity_refs` require the prior panel banked-with-chain first (compose refuses otherwise). Multi-character panels already have `qa/staging/<panel>.json`.
```
p01-01..p01-04, p02-01..p02-03, p03-01, p04-01..p04-04, p05-01..p05-03,
p06-01..p06-03, p07-01..p07-03, p08-01..p08-03, p09-01..p09-03, p10-01..p10-03
```
Tier map (auto-applied from shotlist): all t1 except p09-02/p09-03/p10-01 = t2, p10-02/p10-03 = t3.

## STEP 4 — Lettering & pages (after panels banked)
- `continuity-check` skill: vision audit across the 30 banked panels (wardrobe/props/location/time drift) before lettering.
- `page-composer` skill: layout per page (sizes in shotlist: splash/wide/tall/standard), place balloons/captions/SFX from the shotlist `dialogue`/`captions`/`sfx`, render pages → `pages/page-NN.png`.
- Export print-ready PDF.

## Decision log (so a fresh session/the reviewer can verify compose ↔ data agree)
- **Single-rung scene ladders**: `scene_ladders.<location>` is a flat `{flow_id,disk,chain}` object (one DAZ render per location), not wide/medium/close rungs. compose_page attaches `scene:<location>`; bank `scene:` branch writes it; verify_chain audits it.
- **Genesis faces** bootstrap in prose with empty attach (`genesis:true`); audit skips the ≥2-ref rule for them.
- **audit page min-refs is character-aware**: ≥3 when any `face:` attached, ≥1 (scene only) for character-less establishing panels.
- **Reverse scenes** (`-reverse`) exist for the 4 hero locations for L14 180° continuity; they are generatable/bankable but not wired into compose_page's required stack — attach manually when a panel faces the opposite way.
- **Props** (bawal-lumangoy-sign, compound-vial): not yet wired as gated sheets. Generate as needed (sign from the BABALA style refs; vial from prose) and attach in the relevant panels (p02-03/p07-01 sign; p01-02/p01-03 vial).
