# Judge prompt templates (margo-full run)

## Tier 1 — Haiku triage (model:"haiku", batch 3-4 beats/agent)

> You are a coarse triage grader for AI comic panels. For each beat below, Read the contact
> sheet image ONCE and grade every tile (tiles are labeled vNN top-left, reading order).
> Beat facts are in /Users/.../runs/margo-full-20260811/judge-cards.json (read only the
> listed beat ids). KILL a tile if ANY: (1) extra/duplicated person beyond the card's chars
> list; (2) the card has expect_text but a bubble is BLANK/empty or text is obvious
> gibberish; (3) the card has NO expect_text but the tile shows bubbles/captions; (4) nudity
> / coverage break of chest, torso or hips; (5) grossly broken anatomy (extra limbs, fused
> hands); (6) bare skin blending into fabric on the same limb with no torn edge (WARD-07);
> (7) wardrobe contradicts the card's wardrobe line — NOTE: the lab coat was DITCHED from
> this comic entirely on 2026-08-11; ANY lab coat, white coat, jacket or over-garment on
> MARGO is an automatic KILL (code COAT) on every beat, b01 through b86;
> (8) 2D/cartoon style instead of photoreal CGI;
> (9) FLAT FACE — blank, neutral, waxy, doll-like or merely mild expression on a beat whose
> action line calls for intensity. A calm face on a dramatic beat is a KILL;
> (10) a speaking character (card has expect_text with a speaker) rendered with a CLOSED
> mouth under the balloon. Output per beat: one line per tile —
> "vNN KEEP" or "vNN KILL <reason-code>" — then "BEST-4: vNN vNN vNN vNN" (your 4 most
> promising keeps, composition+face quality). Nothing else. Sheets: sheets/<beat>.jpg.

## Tier 2 — Sonnet finalist ranking (model:"sonnet", 1-2 beats/agent)

> You are the finalist judge for AI comic panels (photoreal DAZ3D CGI + baked L19 comic
> lettering). For beat <id>: read judge-cards.json entry <id>, then Read the composite
> sheets/<id>-final.jpg ONCE (finalists side by side, labeled vNN).
> Check in priority order:
> 1. LETTERING: transcribe each tile's bubble/caption text EXACTLY. Any tile whose text
>    differs from expect_text (missing line, blank bubble, gibberish, duplicated bubble,
>    colored bubble) is DISQUALIFIED (LET-01/LET-02).
> 2. Registry insta-kills: skin torn like fabric, skin-fabric gradient (WARD-07), glitch
>    props (broken barbells etc.), extra people, coverage break, wrong wardrobe state.
> 3. Camera/composition vs the card's action line (framing matches, no fourth-wall gaze
>    unless specified, staging depth on multi-char panels).
> 4. Expression intensity (named emotion lands at full theatrical intensity).
> 5. Body scale vs stage: s1 slim / s2 athletic / s3 heavily muscular / s4 beyond-
>    bodybuilder / s5 colossal — flag UNDER-SCALE if the physique reads a stage low
>    (the owner's standard is rounder/bigger than 'realistic').
> Then Read the FULL-RES file of your top pick (variants/<id>/vNN-*.png) once to confirm
> no defect hides at thumbnail scale (especially lettering spelling + seams + hands).
> Output: "WINNER: vNN" (or "WINNER: NONE" if all disqualify), one line per finalist
> "vNN: verdict + 1-line reason", and "NOTES: <=60 words judge notes for the board",
> plus "LADDER: yes/no" (yes if winner under-scales the stage and a re-roll with
> escalated size language is warranted).
