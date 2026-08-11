# Vision Audit — Shadow-Sidecar Agreement Run (2026-08-10)

**What this is:** experiment 02 ended 2026-05-22 with "iterate, don't ship — labeled data
too thin." Months of real production then banked pages WITH fresh-subagent verdicts, so
the labeled-data problem solved itself. This run wires the audit as a **shadow sidecar**
(`skills/continuity-check/scripts/vision_shadow.py`) — zero edits to any `qa/*.py` gate,
reads banked state, writes advisory files only — and measures agreement at scale on the
two richest local projects.

- **Rubric:** experiment 02's ship spec — v3 category language + v5 confidence-semantics
  block, verbatim, + canonical face cards attached (v3's biggest win), + per-project cast
  canon insert, + one marked extension (`location_mismatch` → ENV-01). Core at
  `skills/continuity-check/references/vision-shadow-rubric-core.md`.
- **Verdicts:** 16 sonnet vision subagents (8–9 panels each) + 1 sonnet text classifier
  over banked verdict notes; orchestrator (Fable 5) personally adjudicated disagreements.
  **Zero generation credits spent.**
- **Scope:** `not-so-supra-man` 45 banked HF panels (GT = the checked-in 46-page human
  audit table `qa-report.md`, verified same-generation as the on-disk images);
  `scientists` 82 banked pages (GT = chain `verdict.json` + note-mined soft labels —
  pass-heavy by construction). 100% image coverage of both banked logs.
- **Outputs:** advisory `qa/receipts/<job>.vision.json` per panel (registry IDs cited per
  flag) + `qa/vision-shadow-report.md` per project (confusion tables, disagreement
  drill-downs with panel pointers, orchestrator adjudication appendix).

## Headline numbers

not-so-supra-man (fail-rich GT): 23 defective pages → same-group catch **17/23 (74%)**,
any-flag 20/23 (87%); 13 clean pages → agreed clean 6/13. scientists (pass-heavy GT):
68 clean pages → agreed clean 38/68; 14 soft-flagged pages → same-group catch 4/14.

Per-group vs the ship bar (recall ≥80% / precision ≥70%, support ≥5) — **strictly
against banked-subagent ground truth, no group clears both bars**. Closest: WARD
(wardrobe/emblem/costume-state) at 77% recall / 65% precision, support 22.

**But the adjudication flips the interpretation of "false positives":** every vision-only
flag the orchestrator eyeballed proved REAL — a systematic 12-panel Destroya hair-drift
(platinum vs the honey-gold face card) the human audit never logged, two full wardrobe
escapes (p19 one-boot state, p21 red-torso suit + shield emblem), and a costume-STATE
escape on a banked scientists page (p14-01, baseline outfit where grown-state scripted).
Post-adjudication WARD precision ≈73%; HAIR goes from "0% precision" to a verified
discovery. The shadow and the chain judge see different things: the chain judge compares
against ATTACHED refs, the shadow against SCRIPTED state + canonical cards.

## Promote / iterate / park

| Category (registry) | Decision | Grounds |
|---|---|---|
| WARD — wardrobe/emblem/costume-state (WARD-01/04/05) | **PROMOTE as always-on advisory** | 77% recall on support 22; ~73% precision post-adjudication; caught 2 verified escapes. Below hard-gate bar (missed p45 emblem-shape BLOCKER, p29 boots) — advisory, not gate. |
| HAIR (HAIR-01) | **PROMOTE as always-on advisory** | Human-side support ~0 but 12/15 flags verified real (systematic drift). This is precisely the "human-side gap" class the defect registry flagged to build against. |
| ENV — location (ENV-01, shadow extension) | **Advisory, iterate** | 75% recall / 38% precision naive; several FPs plausibly real (p37 rooftop vs scripted city-street). Tighten venue-class language. |
| LETTER (LET-01..04) | **Iterate** | Definitional mismatch: rubric allows paraphrase, banked notes log wording swaps (LET-04). Add scripted-dialogue comparison to the rubric, re-measure. |
| COUNT / ANATOMY / COMPOSITE (CAST-02/03, BODY-05, ENV-03) | **Advisory, insufficient data** | 100% on support 1–2 each (caught the p18 stray figure, p20 floating head). Promising; needs more labeled fails. |
| SIZE / tier (BODY-01/02/07) | **PARK for pure vision** | 0/3 on NSS incl. the unmissable doll-scale p30; SCI tier flags directional at state level but unreliable at tier granularity. Use the deterministic anchor-comparison lane (D14-style side-by-side gates) instead. |
| STYLE (STYLE-01) | **PARK / iterate** | Missed the one anime-page BLOCKER (p39) with high-confidence "photoreal". Single-panel holistic style reads are unreliable; keep the Studio per-rule scanner as the tool. |
| IDENT — identity swap (IDENT-01, CAST-01) | **Park (unchanged)** | 0% recall in experiment 02 and no signal here (support 0–1). |

## Recommended wiring (no gate edits, consistent with this run)

1. Run the sidecar post-bank per project (plan → subagent batches → ingest → report).
2. Pipe WARD + HAIR flags at high+medium confidence into the Studio 🏴 defect queue as
   ADVISORY candidates — receipts already cite registry IDs, so `do=flag` ingestion is a
   field-mapping exercise. Human accepts/rejects; acceptance rate becomes the live
   precision measure that decides any future gate promotion.
3. Keep gates untouched. The two-sided disagreement pattern (shadow misses style/size
   blockers; chain judge misses state/canon escapes) means the shadow is a COMPLEMENTARY
   detector, not a replacement judge.

## Caveats

- Scientists GT is pass-heavy (banked = passed); its "precision" numbers are floor
  estimates until the owner adjudicates the flagged rows in the report drill-downs.
- Note-mined soft labels came from one sonnet classifier pass (22 observations / 82
  notes); a second pass or human skim would firm up the LETTER/OTHER rows.
- NSS `p43-01` (the tier-9 benchmark page) is on disk but in no banked log — excluded.
- Orchestrator adjudication covered the decisive disagreements (7 panels + 2 reference
  cards viewed in main context); remaining vision-only rows are labeled pending-owner in
  the per-project reports.
