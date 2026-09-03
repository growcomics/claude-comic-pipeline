# FMG Size-Taste Rules — v1.0 (2026-09-02)

> Owner-confirmed 2026-09-02: the mobility test (§1, S14) is a HARD VETO. This doc is mirrored in the private
> knowledge-base (`blueprints/size-taste/`) together with the anchor image, the guide transcripts and the raw ratings.

Source of truth for *how big*, *where the mass goes*, and *what the peak must still look like* in 3D Muscle Comics
growth sequences. Built from the owner's FMG Anatomy Guide (PDF, 16 pp), the 2026-09-02 calibration Q&A, and the
Alice / Chun-Li ladder ratings. Memory files under `~/.claude/.../memory/` hold the one-fact-per-file provenance.

## 1. The anchor and the ceiling

- **Anchor image:** `flow_re_sheets/_calibration/ANCHOR_chunli_a4d0b131.jpg` (owner: "really good, quite dialed in").
  On the 1-9 Sonnet read scale it is tier 7 — hyper, biceps larger than the head, thighs wider than the waist —
  but *defined*, shot knee-up, lit by a spotlight with a gradient across every muscle.
- **Ceiling:** at most ONE step bigger than the anchor (≈ tier 8) and only while every shape rule below holds.
  The Alice rungs 5-8 (tier 8, smooth/blob, full-body far, flat white light) are the canonical overshoot.
- **Usual failure is still TOO SMALL.** The ceiling exists so ladders stop at the right rung, not to shrink prompts.
- Ceiling is a house ceiling (all books, all characters) until the owner says otherwise.
- **The real test of "too big" is mobility, not centimetres.** "The whole point of power is that I want to be
  able to use the power." A frame where she could not move — arms welded to the sides as stacked spheres, hands
  dangling, thighs fused, no visible knee or elbow — "looks like something that's sick" (Alice rung 7, 542bf501).
  The same size with hands on hips, bent elbows and separated thighs (712989ea) passes. The Chun-Li anchor is
  gigantic AND looks like she can move. Stop the ladder at the last rung that still passes this test.

## 2. Where mass goes (guide p.3 + owner override)

| GO BIG | KEEP SMALL / FEMININE |
|---|---|
| biceps, triceps, thighs (quads + hams), lats, glutes, calves, bust, **shoulders (owner: "can be big")** | traps, neck, hands, knees, feet, head |

- Bust grows **in step with the muscle from rung 1**; never a flat chest on a growing body.
- Glute mass balances bust mass; hips and glutes may merge into one continuous shape.
- Shoulders may grow but **never wider than the hips/glutes** (equal = hourglass ✓, hips wider = feminine ✓,
  shoulders wider = reverse triangle = manly ✗).
- Calves grow, but knees, ankles and boots keep their silhouette — calves that swallow the boot are wrong.
- Growth lands on the **named** muscle as a recognisable shape; an anonymous swelling ("weird muscle") is the
  owner's "uneven growth" fail at any tier.
- **Biceps lead.** They should out-size the neighbouring muscles, not tie with them.
- **Forearms scale with the upper arm** (thick, several tapering shapes, short wrist, small hand); normal forearms
  under huge biceps are "weird".

## 3. Shape rules at every tier

1. **Waist:** narrow with STRAIGHT sides — a `|`, not a `(`. Corset curve = fail. Not thinner than the anchor —
   and not thicker either: a thick/wide waist at hyper size "looks like she's fat" even on a cut frame
   (Chun-Li step 8, dd12b5f1). Big square abs are fine.
2. **Abs:** visible at the peak (wardrobe must open the midriff), square grid never triangular, each block
   smoothly domed "like a bread bun", never hard-edged.
3. **Definition:** FMG muscle is always visible and separated, even relaxed; a big anchor muscle wrapped by
   smaller detailed muscles reads bigger than one sphere. Blob = fail.
4. **Round is fine, blob is not:** "very, very round" spheres work when the camera is close and light gives
   each sphere a volumetric gradient; far + flat = "a bunch of blobs of circles".
5. **Veins:** a little is OK; the anchor's subtle arm/thigh veins are the maximum.
6. **Bust:** round, lifted, "ignores gravity"; its own separated projecting mass, never smeared into the
   silhouette by a smooth one-piece bodice.
7. **Curves, not triangles:** smooth transitions between muscle masses; no hard angular junctions.
8. **Flow, not mirror symmetry:** the two sides of the body should differ in pose/shape so they complement
   each other; identical stacked-sphere limbs are the "drumstick" fail. (Mass should still be evenly
   distributed across muscle groups.)
9. **Lats hinted** even from the front so the hourglass has a top.
10. **Forearms** taper in several shapes to a SHORT wrist and a small hand — no drumstick bulge, no long wrist.
11. **Skeleton fixed:** no height gain, no longer arms.

## 4. The frame around the body (these decide "good" as much as size)

- **Expression is a gate at growth peaks:** visibly thrilled / delighted / overwhelmed; a mild polite smile or
  "staring into nowhere" fails. Never a menacing roar. Give her an eyeline (her own arm, a mirror, a witness).
- **Camera:** never the flat frontal eye-level default. Diagonal high looking down, or ground-level looking up;
  knee-up / waist-up at the top rungs with the flexed mass ≥40% of frame.
- **Lighting:** golden hour, raking key, or a practical (spotlight, window sun, energy glow) — a visible gradient
  across the musculature. Flat white-lab light is "pretty terrible".
- **Wardrobe:** strain → tears → shreds as the ladder climbs; midriff open by mid-ladder; bust and crotch stay
  covered; accessories (gloves, boots) locked — appearing/disappearing gloves is a break.
- **Face reads 25+**, glamour makeup and hair intact unless the beat says sweaty.
- **Camera changes on every rung** ("the same camera angle all the time really, really, really sucks — remember
  this for later"), and she LOOKS at the part that grew; blank stares fail.
- **Wardrobe continuity:** gloves, pants, boots do not appear/disappear between rungs. Accidental show-through
  under strained fabric is a bonus when it happens; never prompt for it (filter).
- **Base model:** start the ladder from a sheet that already shows midriff skin and carries a big round bust; a
  full-coverage suit with a modest bust (Alice's Umbrella suit) is "a really bad model to work on".
- **Render style:** no thick ink outlines — "that's just not something that happens in CGI" (STYLE-01).

## 5. Scoring rubric (for Sonnet judges and the pre-tag pass)

Score each candidate 0-2 on every line; any HARD line at 0 disqualifies.

| # | Line | 0 | 1 | 2 | Hard? |
|---|---|---|---|---|---|
| S1 | Size vs anchor | < tier 5 or > anchor+1 | one tier off target | on target for the rung | ✔ |
| S2 | Definition | blob | smooth, some shapes | defined/cut, every muscle its own shape | ✔ |
| S3 | Mass placement | swelling on unnamed/KEEP-SMALL parts | mostly right | GO-BIG list only, small list small | ✔ |
| S4 | Waist | corset curve or thick | narrow but curved | narrow, straight-sided, abs visible | ✔ |
| S5 | Bust | flat or merged into torso | big but flattened | big, round, lifted, separated, in step with muscle | |
| S6 | Shoulder/hip | shoulders wider | equal | equal or hips wider, lats hinted | ✔ |
| S7 | Hands/traps/neck/head | any grew | slightly | all small | ✔ |
| S8 | Balance/flow | mirrored stacked spheres, uneven groups | minor | even mass, asymmetric flowing shapes | |
| S9 | Expression | neutral / mild / roar | pleasant | thrilled, eyeline on something | ✔ at peaks |
| S10 | Camera | frontal eye-level far | 3/4 or moderate crop | dynamic angle, knee-up or closer | |
| S11 | Lighting | flat | some modelling | gradient/raking/golden | |
| S12 | Wardrobe | continuity break / abs hidden at peak | minor drift | on-model, torn per rung, abs shown | ✔ at peaks |
| S13 | Veins | heavy road-map | — | none to subtle | |
| S14 | **Mobility** | welded/blocky, could not move | stiff but articulated | bent joints, hands busy, stance, athletic | ✔ |
| S15 | Camera change vs previous rung | identical angle | small change | new angle/crop, eyeline on the grown part | ✔ in ladders |
| S16 | Render style | ink outlines / 2D drift | slight | clean CGI | ✔ |

**Weighting (owner-validated):** score impact first — lighting (S11), definition (S2), mobility (S14), camera
(S10) — then size (S1), then anatomy hygiene. Only the hard lines veto. A judge's "melted forearm" is a note,
not a veto: the owner rated Sonnet's worst Chun-Li frame (step04/d608a266, golden-hour, striated, wide stance,
mirror) "interesting and good… breasts should be bigger".

## 6. Prompt-language block (append to every growth rung, after the delta)

> Her biceps are the biggest muscles on her body; her triceps, shoulders, lats, chest, glutes, thighs, calves
> and thick forearms all grow with them; her chest swells
> bigger and rounder with her muscles. Every muscle stays clearly separated and visible, each its own shape.
> Her waist stays narrow with straight sides and her abs show through the torn suit. Her hips and glutes stay
> as wide as her shoulders. Her traps, neck, hands, knees and feet stay small and delicate; her head stays the
> same size; her skeleton does not get longer and her arms are not too long. She is agile and explosive, mid-
> motion — [weight on one leg / stepping forward / twisting to look] — elbows and knees bending freely. She is
> thrilled, laughing in delighted excitement, staring at [her own swelling biceps / the mirror / him]. Camera [low on the floor looking up /
> high and to the side looking down], framed from the knees up so her flexed muscles fill the frame. Low warm
> golden-hour light rakes across her muscles with a strong highlight-to-shadow gradient. Subtle veins only.
> Same gloves/boots as the previous panel. There are only two arms. There is only one panel here.

Size intensifiers (stacked "very", "giga", "freakishly") stay in the DELTA sentence, not in this block, and stop
one rung after the frame first reads like the anchor.

## 7. Defect registry additions (proposed — registry row FIRST, then coverage)

- **BODY-12 `size_overshoot`** — mass beyond anchor+1 / limbs wider than torso as featureless spheres.
- **BODY-13 `mass_wrong_place`** — growth on KEEP-SMALL parts (traps, neck, hands, knees, feet, head) or an
  unnamed swelling; calves swallowing boots.
- **BODY-14 `waist_corset_curve`** — cinched/curved-in waist instead of straight-sided narrow.
- **BODY-15 `bust_not_scaled`** — bust flat or merged while muscle grew; teardrop/sagging bust.
- **BODY-16 `immobile_mass`** — limbs welded to the torso, no visible joints, could not move.
- **CAM-xx `same_angle_as_previous`** — consecutive ladder rungs with an identical camera.
- (existing BODY-01 stays the under-render class.)

## 8. Open items

- Owner rating pass DONE (15 prose notes, no 1-5 verdicts) — folded into v0.2. Hard lines in §5 confirmed (mobility = hard veto).
- Repo placement decided: both (this file + private knowledge-base mirror).
- Numbered size-lineup image (figures 5-9, anchor = 7) in progress on Nano Banana 2 Lite; will land in `assets/` as `muscle-size-lineup-chunli-5-9.png`.
