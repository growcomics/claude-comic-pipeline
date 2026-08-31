# Owner-caught defects that QA missed — transcript + annotation mining (2026-08-30)

*Investigation: catalogue of comic defects the owner had to point out manually — i.e.
defects Claude's QA/judge passes FAILED to spot — mined from local session transcripts
(~231 JSONL files under `~/.claude/projects/`), the bootcamp case-study annotations
(`~/Documents/bootcamp-casestudy/data/annotations.json`, 21 rounds), and the prior
owner walkthroughs (`owner-defect-feedback-2026-08-10.md`). Companion to
`skills/comic-production/references/DEFECT-REGISTRY.md`; every class here now carries
a registry ID. Registry rows added by this investigation: LET-05, LET-06, LET-07,
BODY-10, BODY-11, PROP-04, CAM-08, CAM-09.*

## A. Confirmed incidents — owner correction AFTER a QA/judge approval

| Date | Session | Owner said (verbatim gist) | Defect → registry ID | What QA had just said |
|---|---|---|---|---|
| 2026-06-23 | cockpit/schedule | "only one of the three has the same style shirt as the one that I picked… we mentioned ABS, so it kind of modifies the shirt" | Wardrobe drift via anatomy keyword → **WARD-01** | Claude declared the test comic "done — transformation reads start-to-finish" |
| 2026-08-11 05:32 | cockpit/schedule | "I never see the huge breasts that are common in what I make… the bicep will see the skin, and it will have a gradient into the clothing, which is just not possible" | Size under-render → **BODY-01**; skin-fabric gradient → **WARD-07** (named as new class that day) | v2 panels framed as judge-validated ("the composite convinced the judge") |
| 2026-08-11 06:49 | cockpit/schedule | "the breasts are still pretty small… we have to re-roll the breasts on top of each other" | Size under-render → **BODY-01** | "Green frames are the pool-judge's top picks" |
| 2026-08-20/21 | Scientists release worktree | Release QA found p09-03 "Rochelle renders baseline-slender between two grown-state panels" and p14-06 balloon bakes "I I PERFECTED IT" | Size regression → **BODY-02**; lettering garble (duplicated word) → **LET-02** | Both panels had passed the full mechanical gate chain and were staged in the release bundle |
| 2026-07-28 | growth-animation session | "it looks like bare skin or something… the muscles get too big, so the transition didn't really work" | Skin/garment confusion in animation → **BODY-10** family | Claude had posted a QA review grid of the clips without flagging it |
| 2026-08-25/26/27 | Müller movie session (video, adjacent lane) | "The guy looks totally different here… again"; "it never really has exactly four people. Sometimes it's five or six… duplicate characters"; "the way you tried to cover it up… it's terrible" | Identity drift → **IDENT-01**; cast count/duplicates → **CAST-01/03**; failed patch worse than defect (process) | Claude had shipped review grids / a "fix ledger" without these on its own list |

| 2026-08-20 | owner bug ticket (session 2afb130a…) | "Rendered in DAZ3D Iray (2021 Version)" baked across the bottom of a PUBLISHED page — live at 3dmusclecomics.com nuclear-woman part-01 page-06 | Watermark baked in → **LET-05** — escaped every QA layer all the way to the public site | No in-session approval visible; the page shipped through the whole pipeline unflagged (fix task spawned same day) |

Pattern: **the judge/QA pass systematically approves size-under-rendered panels**
(3 of 6 incidents are BODY-01/02) — confirming the registry's existing "be harsher
than feels natural" calibration note is still not harsh enough in practice.

## B. Defect types in owner vocabulary but MISSING from the registry (now added)

Cross-reference of the annotations tag vocabulary (26 tags, 21 rounds) and the
2026-08-10/11 owner walkthroughs against the pre-existing 57 registry classes:

| New ID | slug | Evidence | Detection heuristic for QA readers |
|---|---|---|---|
| **LET-05** | `watermark_branding` | 12/193 loser annotations "watermark present" — invented trademarks ("MASTERS OF THE UNIVERSE" wordmark) and render-engine credits ("RENDERED IN DAZ STUDIO") baked into art | Scan corners/edges for ANY rendered wordmark, logo, brand, render-engine credit, or signature not in the lettering spec. Hard fail regardless of image quality. |
| **LET-06** | `sfx_misuse` | 6 annotations "SFX crowding" + 1 "SFX missing" | SFX present exactly per shotlist `sfx[]`; SFX must not cover faces, the growth payload, or >~20% of panel; missing SFX on an impact/growth beat is a defect too. |
| **LET-07** | `lettering_style_drift` | Owner walkthrough B13: one BLUE bubble in an all-white-bubble project | Bubble shape/fill/outline/font must be uniform project-wide; any odd-one-out bubble color or style = flag (cheap: compare bubble fill across the page). |
| **BODY-10** | `skin_torn_as_fabric` | Owner B20 "her SKIN is torn like clothing — recurring problem", insta-kill; 2026-07-28 animation incident | Any tear/rip/damage texture applied to skin rather than garment. Garment tears at seams are legal; skin tearing never. Sibling of WARD-07 (both = skin/fabric material confusion). |
| **BODY-11** | `growth_plateau` | 8 annotations "growth plateaued" | Sequence-level: compare each growth rung to its predecessor — if the delta is not visibly larger on ANY axis, the rung failed even if the single image is clean. Needs neighbour-panel context (judge-level, not single-image scan). |
| **PROP-04** | `prop_glitch` | Owner B19 barbell with "empty/glitch bar", rest on the ground, insta-kill; 1 annotation "prop mangled" | Physically incoherent equipment/props: broken continuity of a bar/handle, floating parts, objects fused or duplicated. Check every held/load-bearing prop end to end. |
| **CAM-08** | `fourth_wall_gaze` | Owner B7: character looks into camera on a non-POV beat (ref-pose bleed) | Any character making eye contact with camera on a beat that isn't scripted POV/address = flag. Root cause is forward-facing refs; prevention = view packs. |
| **CAM-09** | `payload_cropped` | 6 annotations "waist out of frame" (+1 "wrong camera height") | The panel's declared payload region (waist, bust, bicep — from the beat) must be fully in frame; framing that crops the growth payload fails even at correct camera distance. |

Tags that already mapped cleanly (no action): composition flat→CAM-03, text
artifact→LET-02, scale mismatch/inconsistent→BODY-07, camera did not flip→CAM-06,
identity drift→IDENT-01, waist reverted→BODY-02, lighting mismatch→ENV-03,
excluded subject present→CAST-02, wrong character→IDENT-01/02, hands/anatomy
break→BODY-05, 2D drift→STYLE-01, no dialogue→LET-01, wardrobe reverted→WARD-02,
background noise→ENV, occluded in lineup→ref-quality (GEN-03 adjacent), near
miss→not a defect (judgment tag), pose unreadable→CAM-03 adjacent.

## D. Deep-mine round 2 (2026-08-31) — owner defect LISTINGS across all transcripts

Owner requested a deeper pass: bug-ticket-style defect listings, not "you missed" phrasing.
Full-corpus sweep (232 files, all human-authored messages extracted and reviewed).
Registry rows added by this round: **LET-08, CONT-02, GEN-05**.

### Owner defect reports by session (static-comic lane)

| Date | Session | Owner-named defects → registry IDs |
|---|---|---|
| 2026-05-11→23 | Chun-Li (33c33c3a) | "images 3,4,5 are cartoons when it's supposed to be a 3d comic" → STYLE-01 · repeated costume/tights/bare-legs discrepancies → WARD-01 · "chun li is not beautiful" → IDENT-04 · "hard to recognize with her hair like that" → IDENT-02/HAIR-01 · "missing text and SFX" → LET-01/LET-06 · "abs one direction, feet facing the other" → BODY-05 · facial drift doctrine complaint → IDENT-01 |
| 2026-06-10 | 95c1df3e | "often it's really flat… angles could be more interesting" → CAM-02/03 · "transformation scenes could be longer, more zoom in" → PAGE-01/CAM-01 · "very plain face… audience would also not have any emotion" → FACE-01 · "be very careful… muscle proportions… possible to downsize and we have to start all over" → BODY-01 (ref inspection mandate) |
| 2026-07-07 | cb1fd163 | "Chun-Li is just a little bit too far away" → CAM-01 · "blurring out the background… more visual weight to the foreground muscle" → CAM (DOF/separation, fold into CAM-01 guidance) · "nothing showed off her ass or great chest" → CAM-09/payload emphasis |
| 2026-07-30 | f1bdf56d | "you don't use reference images… breasts way too small, muscles nowhere near round enough" → BODY-01 + GEN-03 root cause |
| 2026-08-11→12 | Gribble/Margo (6dbca314) | "emotionless faces" → FACE-01 · "should have ~80 pages… only seeing like 20" → process · "I'm not seeing text" → LET-01 · "speech bubble and then a completely closed mouth" → **LET-08 (NEW)** · sleeves torn on 8-9 then not later → WARD-02 · "reflection in the mirror doesn't have the lab coat" → **CONT-02 (NEW)** · ripped sleeves on random people in 23-25 → WARD-02 · office↔weights scene confusion → ENV-01 · "measuring a different girl that's there for no reason" → CAST-02 |
| 2026-08-11 | cockpit beat review (40f00da9) | (already in §A/B: WARD-01/02, CAM-08, LET-07, ENV-04, CAM-02, FACE-01, PROP-04, BODY-10, BODY-01) plus "your images just seem much more lifeless… dull… lighting isn't there" → ENV-03/FACE-01 · "a lot of repeat images" → PAGE-04 · "never saw a text, but the text should be baked in" → LET-01 |
| 2026-08-16 | d1e91cf3 | "I don't like the 3D lettering… should just be plain comic text" → LET-07 (project lettering-style spec) |
| 2026-08-20 | 2afb130a | live watermark (LET-05, §A) · "page-08 shows a visible render-fidelity dip (softer/more airbrushed skin)" → BODY-08/STYLE-01 evidence |
| 2026-08-23 | Evil-Lyn ref review (98b0ac94) | pre- vs post-transformation refs conflated; hands/expressions/faces mixed between states; Skeletor in the pack though not in the story; "his full body is super muscular, and then it's not" → **GEN-05 (NEW)** · "the face is cropped, so modifications never look like the original character" → GEN-05 (ref quality → downstream IDENT-01) |
| 2026-07-26→08-02 | platform (72440852, d255f96c) | recurring "text bubbles are blank" on ported comics → LET-01 · logo/wallpaper tiling crop reads as gibberish → platform UI, not panel art |

### Video/animation lane (Müller e6cfe2f7 2026-08-25→27; 1ae1ae97 07-28; 37a39cfa 08-31)

The single richest defect thread on file. Most map to existing registry IDs (video QA
should reuse them): cast count never stable / duplicates → CAST-01/03 · face "a
different person now" → IDENT-01 · veiny-bicep skin texture mismatched to character →
IDENT/BODY-08 · multiple belly buttons (recurring, "looks gross") → BODY-05 · blurry
text + stray "comic book text that shouldn't be there" → LET-02 · title card covering
her face → LET-06-style placement · hair color drift → HAIR-01 · "way fatter than she
was in the nurse's outfit" → BODY continuity · dialogue given to the wrong girl →
LET-03. Video-ONLY classes (not registered; live in the Seedance lessons instead):
unison posing ("never do anything in unison"), frozen mid-walk background extras,
missing treadmill / physics errors, frozen floating objects, liquid rendering as
solid, surreal "Salvador Dali house" backgrounds, voice/accent drift, Mandarin when
no dialogue given, "BA YE RN" pronunciation, uneven one-arm-at-a-time growth,
overshoot past the next growth stage.

## C. Method notes / negative results

- Substring search over all transcripts: most correction-phrase hits were noise
  (skill boilerplate, agent-judge prompts, task-notification wrappers). Genuine
  owner corrections cluster in ONE session lane: the pool-judge/autopilot comic
  work of 2026-08-11 and release QA of 2026-08-20.
- `the-biggest` project transcripts contained no owner overrides — its automated
  QA subagents did the rejecting (pass=false verdicts), which is the desired state.
- The Müller video incidents are an adjacent lane but the same failure pattern:
  review grids shipped without identity/count checks that the static-panel
  registry already mandates. Video QA should reuse registry IDs.
