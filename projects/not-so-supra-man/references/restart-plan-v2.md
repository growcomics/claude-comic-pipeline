# RESTART v2 — full rebuild in a NEW Flow project, references-first (D1–D14 enforced)

Status: **blocked on growcomics Google sign-in** (macmini Chrome account chooser shows the account
signed out; agent cannot enter credentials). The moment the session is back: execute top to bottom.
Model: **Nano Banana 2 · x4** (Pro rate-limits bulk runs). One page/batch in flight at a time.

## Phase 0 — project setup
1. Flow dashboard → **+ New project**; record project id here.
2. Pill: Nano Banana 2, x4, aspect per item below.
3. **Verify cross-project asset access**: open `+` picker → project dropdown (top-left) → old
   project ("Jun 09, 11:25 PM") → search "lana". If the anchor is reachable cross-project, reuse it
   and the locked face cards. If NOT: user drags `projects/not-so-supra-man/.flow-scratch/anchor-4d81c347.jpg`
   into the new project once (agent's file_upload is allowlist-blocked) — everything else regenerates.

## Phase 1 — identity (1:1, best-of-4 each)
4–7. Face cards: Dana, Supraman, Dee-Dee, Doomer (prompts = the locked v1 prompts; if old cards are
reachable cross-project, attach them so identity carries; else regenerate and re-lock).

## Phase 2 — Dana T9 via D14 anchor-first swap (16:9, LITERAL gate)
8. PASS 1 identity swap (anchor PRIMARY + Dana face; keep-list enumerated; strip text/caption).
9. PASS 2 zoom-out full body → becomes canonical `body-tier9-v2`.
10. PASS 3 four-view turnaround + 6'2" scale silhouette + grid → `turnaround-t9-battle`.
   GATE each pass: side-by-side vs anchor — under on ANY axis = reject, escalate keep-language.

## Phase 3 — body ladder (3:4; every prompt carries the height clamp)
11. Dana T2 reporter (face attached). 12. Dana T4 (face+T2). 13. Dana T6 suit (face+T4; "muscle mass
increases, height does NOT — she is 5'10\""). 14. Dee-Dee T3 lab coat. 15. Dee-Dee T8 Destroya
(face + best old Destroya card if reachable; else D14 swap off the strongest card). 16. Supraman.
17. Doomer.

## Phase 4 — wardrobe-state TURNAROUNDS (16:9, scale silhouette + grid, per turnaround-specs.json)
18. dana-t2-reporter (NEW — pages 2–6 need her intact-blouse state pinned too)
19. dana-t6-torn   20. dana-t6-suit   21. (t9 done in Phase 2)   22. deedee-t3-labcoat (NEW)
23. deedee-t8-destroya   24. supraman-suit   25. doomer-suit (NEW — simple)

## Phase 5 — SCENE LADDERS (D8; chain each rung from its parent; 16:9)
26–28. doomer-lab: wide → medium (chair/console region) → close (chair detail) — 15 pages live here
29–30. hq-gym: wide → medium (rack/table region)
31–32. doomer-lab-2: wide → medium (monitor wall / workbench)
33–34. city-street: wide → medium (crater/taxi region)
35. lab-quarters: wide (+ medium if p17 needs it)
36. lab-exterior: wide only (p18)
37. hq-locker: wide (p19)

## Phase 6 — props
38. disinto-ray   39. graviton-barbell

## Phase 7 — pages 1–46
Per page, composed AT RUNTIME as v4 maximal JSON (qa/prompt-template-v4.json), run through
`qa/preflight.py` BEFORE submit. Attach: [state turnaround] + [face] + [scene rung matching camera
distance] + [staging ref if contact/novel pose — generate+inspect it first] + [prior accepted panel].
Effects language only from qa/vfx-style-bible.md. Growth-progressive pages per
skills/comic-production/references/three-panel-growth-v4.md (size-chart pinning, per-panel face
beats, escalating action lines, no baked text). Tier pages: lineup/anchor attached, literal gate.
User red-pens in Flow with the extension; verdicts → fix queue → re-rolls.
