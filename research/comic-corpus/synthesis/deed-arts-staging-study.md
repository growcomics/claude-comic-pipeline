# Deed Arts staging study — what the hand artist does with the camera that our 3D panels don't

**Studied 2026-09-02.** Two owner-commissioned books by Deed Arts (signs as Blackdeedarts): *The Omega Device* (11 non-contiguous delivery pages, male muscle growth with one female reveal page) and *Poppy - The Sailor Gal* issue 1 (17 pages plus the issue-2 cover, female muscle growth). 113 panels tagged by Sonnet subagents against `analysis-rubric.md` + `angle-study-addendum.md`; the orchestrator personally verified pages Omega 3/10/20 and Poppy 14/16. Per-panel data: `corpus/deed-arts-*/angle-study.json`. Rolled deck: `angle-deck.md` (76 cards) and `cards.json`.

The purpose is composition, not style. The artist draws 2D; our panels are photoreal 3D CGI. Everything below is about where the camera sits, what comes at the lens, how the frame crops the body, and how a page escalates. Nothing about line, color, or anatomy exaggeration is carried over.

---

## The one-paragraph version

Deed Arts never shoots a muscle character from above. Across both books the camera sits at chest height or eye level looking level or up on 80% of panels; the only high angles are establishing shots and one point-of-view gag. Something is always coming at the lens: the chest on 31% of panels, then forearm, back, open hand, fist, glute. Growth is sold by cropping, not adjectives: the frame cuts the figure so the muscle being sold is the widest mass in the panel (waist-up for flexes so both fists stay in frame, body-part-only for growth close-ups, full body only for the reveal). Pages escalate in panel size, with the biggest panel always last and usually bled. And he has two page templates he reuses constantly: the **flex ladder** (identical pose, redrawn bigger three times down the page) and the **body-part close-up column** (three or four extreme close-ups on different muscle groups, tied by one energy motif and escalating sound effects).

---

## Where the camera sits (113 panels)

| Field | What the artist does |
|---|---|
| Angle | eye 53%, low 35%, worm 3%, high 2%, dutch 1% |
| Camera height | eye 48%, chest 32%, below-knee 8%, hip 5%, above head 3% |
| Body part nearest the lens | chest 31%, nothing 23%, forearm 7%, back 7%, open hand 6%, face 6%, fist 5%, glute 4%, shoulder 3% |
| Muscle the panel is built to sell | arms 25%, chest 15%, full silhouette 7%, back 5%, glutes 5%, shoulders 2%, abs 2% (34% of panels sell nothing: dialogue beats) |
| Crop | waist-up 26%, full 22%, chest-up 19%, body-part-only 19%, head-to-thigh 7% |
| Body line | straight 36%, c-curve 21%, x-spread 12%, s-curve 10%, diagonal lean 9%, twist 5%, arch-back 3% |
| Sell mechanism | scale-contrast 15%, frame-crop 14%, cloth-strain 12%, contact-deform 11%, foreshortening 9%, motion lines 9%, overlap 8%, silhouette 7%, rim light 6% |
| Flat-level panels | Poppy 7.6% of panels, Omega 23.5% (its dialogue pages) |

Read the table as a set of defaults we have been getting wrong. Our pipeline's documented failure is the level mid-shot from a near-front angle. This artist's default for any muscle beat is: camera at the chest or lower, looking up, with a limb or the chest breaking toward the lens.

---

## The eight moves, ranked by how often he returns to them

1. **Low-hero flex ladder.** The same front double-bicep pose, redrawn three times down the page at increasing scale, camera height and crop held constant. Poppy p8 panels 2-4, p14 panels 2-4, p17 panel 2. Cheap in ink because the linework alone reads bigger. In CGI it needs real change between rungs (grip tension, jaw, rim light, fabric) or it reads as a lazy re-render. This is the same idea as our growth prompt ladder, and it confirms holding the camera still is what makes the growth legible.
2. **Body-part close-up column.** Three or four sequential extreme close-ups on different muscle groups (bicep, delt, forearm, glute on Omega p4; chest, chest, abs, glutes on Poppy p13), with one continuous energy motif and escalating SFX. Faces are cut most of the time, which is the artist's one recurring defect. Our version should inset a face in the corner of the first close-up, as Omega p4 panel 1 does.
3. **Rear worm's-eye power pose.** Camera behind and below, arms crossed low behind the body, head tipped back and small at the top of frame so traps and rear delts fill the panel. Omega uses it four times in eleven pages. Note the impossible forearm interlock has to be re-blocked for a rigged figure.
4. **Low full-body reveal splash.** Every payoff closes on a low-angle near-full-frame standing pose with radiating light behind the silhouette. Omega p5, p10, p41; Poppy p8 panel 4, p14 panel 4. The camera is below the hips for men and at about hip height for women.
5. **Foreshortened strike at the lens.** Both fists punched toward the camera with the face just behind them (Omega p20 panel 4), or one punching arm rocketing at the lens with hair swept back (Poppy p9 panel 4). Used once per book, always as the anger beat.
6. **Scale-contrast onlooker.** A small reacting figure in the corner or a normal-scale captain flanked by huge crew (Poppy p9, p17 panel 3; Omega p21 panel 5). And the boldest version: a planet under the feet (Omega p41). Sells size without a measured prop.
7. **Cloth strain as its own panel.** A stretch, then a rip, then a snap, each with its own panel and its own sound effect (Poppy p16 panels 1-2, p7 panel 2; Omega p11 panel 2). Fabric tension outlines the mass before skin is shown.
8. **Biggest panel last.** On every growth page the final panel is the largest, usually bled, often with the figure crowding past the border. The 2D border-break does not translate; the CGI substitute is an extreme frame-crop where the mass fills the lens.

---

## Things the subagents did not tag that I saw on the verified pages

- **The female reveal (Omega p10) is built on a crossed-knee S-curve.** One knee crosses in front of the other so the thighs become the widest mass in the frame, the hand-at-chin and hand-on-hip pull the shoulders wide, and the head is small at the top. The camera is at hip height, not eye level as tagged. Head small, shoulders and thighs wide, waist pinched between them is the femininity lock this artist uses on a peak-tier body, and it belongs in our counter-lock vocabulary.
- **Two figures growing at once are staged as an overlap pair** (Poppy p16). Near figure larger and lower, far figure higher and behind, facing different directions so one panel shows a front and a three-quarter back at the same time. That is a direct answer to our multi-character growth pages, which tend to line the cast up at one depth.
- **Growth pages open on a torso close-up with no face** (Poppy p14 panel 1: abs and ripping shirt) and only introduce the face on rung two. The reader meets the body before the reaction. Worth trying as a page-opener pattern.
- **Expression on a growth beat is ecstasy even when the dialogue says alarm** (Poppy p16 panel 2). The artist trusts the face over the balloon. Our registers should allow that mismatch on growth beats instead of flagging it.

---

## What does NOT translate to 3D (and what to do instead)

| 2D device | CGI substitute |
|---|---|
| Interlocked crossed forearms in the rear pose | Re-block as arms crossed with one forearm over the other, or fists on hips |
| Claw-shaped force lines drawn on the muscle | Rim light, dust, or a post glow |
| Solid black cloth tearing into graphic shapes | Real tear geometry or a straining seam |
| Muscle mass breaking the panel border | Extreme frame-crop, mass filling the lens |
| Stacked BULGE BULGE lettering carrying a faceless beat | Pose, tension, and lighting do that work; lettering stays a thin overlay |
| Ghost-trail growth timeline in one panel (Omega p3) | A composite of three to five renders at increasing scale, not a single generation |
| Uniform glow outline around the whole figure | Genuine backlight in the render |

---

## How this feeds production

- **Prompt Deck.** `synthesis/cards.json` is loadable by the Prompt Deck append mode. One card per beat, appended after the continuation line and the refs. The cards are camera, pose, crop, and muscle-sold sentences only, so they compose with the additive growth prompt method.
- **script-breakdown.** L40 in `lessons-learned.md` and the new "Body-to-camera staging" section in `cinematic-framing.md` add a four-question check for every solo muscle panel: camera height, part nearest the lens, muscle sold, crop.
- **Page templates.** The flex ladder and the close-up column are now named devices for the three-panel growth scenes; both end on the biggest panel.
- **QA.** A growth-focus panel shot from above the head, or with nothing coming at the lens, is a soft flag.

---

## Open items for the owner

- Confirm the story credit on *The Omega Device* (Poppy's issue-2 cover credits story to Shadowninja).
- Both books are commissioned work, so the raw pages are the owner's to keep locally; they stay gitignored regardless.
- The Omega book is male muscle growth, which makes it the first MMG entry in the corpus and a reference for the promised gay muscle site.
