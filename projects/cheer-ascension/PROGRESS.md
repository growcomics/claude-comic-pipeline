# Cheer Ascension — progress

**Demo project proving the full generation protocol** (compose → audit → submit → post-flight judge → bank), built 2026-06-10. Single character (Kelsey Brandt), 6 pages, tier ladder 2→4→6, one location (practice-field), always_clothed, no extras, no baked text.

## Protocol wiring
- Gates are SHARED from `../not-so-supra-man/qa/` (run from this project root, e.g. `python3 ../not-so-supra-man/qa/compose.py --job sheet:kelsey-t2-turnaround`). One user blessing covers both projects.
- Receipts/verdicts land in `qa/receipts/` here; staging stanzas in `qa/staging/` (all 6 pages pre-authored, with `turnaround_key` overrides on t4/t6 pages).
- Bootstrap-class jobs (face card, t2 body card, scene rungs, shaker prop) cannot flow through compose yet — their prompts are PRE-COMMITTED in `references/bootstrap-prompts.json` and pasted verbatim. Proposed gate extension (card:/scene: job kinds) awaits user blessing as a future diff.

## Reference gathering (done — skills/reference-gathering, Google Images path)
4 genuine Daz/Iray product renders gathered with provenance (`references/style/daz-cheer-inspiration/_provenance.md`).
**Chosen starting ref: dforce-cheer-outfit-g8.jpg** — same character ×3 uniform variants on studio grey; anchors render style + uniform construction + slim t2 baseline. Others: HOT Cheerleader 1 (glam escalation energy), Cheer Fantasy Pro (pom-poms/action), Cheer Fantasy HS (practice-field environment read).

## Build order (each item: compose → audit → submit ×4 → judge → bank)
1. ☑ kelsey-face (bootstrap) → 2. ☑ kelsey-t2-card (bootstrap) → 3. ☑ kelsey-t2-turnaround (sheet, 28099981 — FIRST full-chain bank)
4. ☐ kelsey-t4-card (sheet) → 5. ☐ kelsey-t4-strain-turnaround (sheet)
6. ☐ kelsey-t6-card (sheet) → 7. ☐ kelsey-t6-strain-turnaround (sheet) → 8. ☐ kelsey-t6-rebuilt-turnaround (sheet)
9. ☑ field-wide (user-accepted bcf73770) → 10. ☑ field-medium (d96a2994) → 11. ☑ field-close (02a87013) → 12. ☑ comet-fuel-shaker (edd62fe1) — ALL BOOTSTRAPS DONE
13. ☐ pages p01 → p06 strictly in order (compose enforces priors + rungs)

## Status
- 2026-06-11 (macmini): user re-blessed v2 gates in-session (fingerprint `768c204c16de92f3`, commit `f96b4c1`) — chained jobs UNLOCKED. **kelsey-t2-card banked**: `47120b51` (V1 of attempt 3) at judge-measured ratio 0.890 vs the 6'2" mannequin. Attempts 1–2 all-failed D7 scale (model renders her too tall); fix that landed = exact percentage + "grid line through chin AND head top" cue + not-same-height negatives (bootstrap prompt v3, commits `f940b62`/`c644066`). Next: field-wide → field-medium → field-close rungs + shaker (bootstraps), then the 6 chained sheets/pages.
- 2026-06-10: project scaffolded; refs gathered + provenance; all 6 staging files authored; gates verified LOCKED pending user rebless (single bless unlocks both projects). Flow project created: `d8ff2c7c-7cd4-4daa-9e90-84cfd123f0db` ("Jun 10, 11:31 PM"); face card banked (`12c236a4`, V2 of 4).
