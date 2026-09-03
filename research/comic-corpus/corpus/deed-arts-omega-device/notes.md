# The Omega Device — Analysis (rubric v1.0)

**Source:** Google Drive folder "The Omega Device" (inked + Colored subfolders), shared directly by the artist — owner-commissioned work, MaxxMuscleComics.com branding on both covers.
**Creators:** Art by Deed Arts / Story unknown (owner to confirm).
**Pages:** 11 of a larger, unknown-length work (artist file numbers p0, p0b, p2, p3, p4, p5, p10, p11, p20, p21, p41 — **not a contiguous chapter**).
**Analyzed:** 2026-09-02

> **⚠ Sampling caveat, read first:** This is a partial artist delivery, not a contiguous read. Page numbers below are the artist's own file numbers (page-00 → page 0, page-00b → page 1, page-02 → page 2, etc. — see the page-numbering note under Scores). Because the pages jump from 2 to 41 with huge unseen gaps, **the growth-page ratio computed below is NOT a meaningful density metric** for the underlying comic — it almost certainly overstates density, since a partial delivery like this is likely to have been curated around the interesting/action/growth beats. Treat the ratio as "density of the sampled pages," not "density of the comic." Per-page `role`/`growth_state` tags are still recorded faithfully for each page shown.
>
> **⚠ Genre note:** despite living in the FMG corpus, this comic is primarily **male** muscle growth (MMG) — two male characters visibly transform (the protagonist "Omega" and the redheaded antagonist), plus one clearly female transformation reveal (p10). The rubric's axes generalize fine to MMG staging; the four scores below and the angle/pose study apply the same way regardless of the transforming character's sex.
>
> **⚠ Content note:** p5, p10, p11, and p41 contain explicit nudity/sexual content. Per the rubric's content-safety rule, all tagging in `angle-study.json` for these pages is composition-only (camera, pose, crop, muscle emphasis) — no sexual content is described anywhere in this analysis.

## Scores (0–5)
| Axis | Score | One-line justification |
|---|---|---|
| Growth density | 4 | Heavy zoom coverage (p4 is 4 straight ECU money-shots), a genuinely novel progressive-timeline device (p3), ≥5 escalation devices across the hero scene — held at 4 rather than 5 because the sampled ratio (see caveat above) can't be trusted as a true density measure for the full comic. |
| Camera dynamism | 4 | Full distance spread (WS→ECU), pervasive low/worm's-eye angles, foreshortening, and a real signature staging move reused 4 times — held at 4 by a handful of flat-level dialogue clusters (p2 panels 1/3/5, p20 panels 2/3, p21 panels 4/6). |
| Expression intensity | 3 | Strong peak faces exist (p10 intensity-5, p20 panel4 intensity-5, p41 intensity-5) but the marquee growth page (p4) goes faceless on 3 of its 4 panels during the loudest SFX beats — the exact "dead face during peak growth" failure the rubric flags. |
| Story & structure | 2 | Low-confidence score: the visible pages imply a coherent power-corrupts arc (device → transformation → celebration → villain turns violent → jailbreak → cosmic threat), but with only 11 of an unknown-larger page count and huge gaps (p21→p41), pacing/tease-payoff genuinely cannot be judged from this sample. |

## Page numbering used in this analysis
Per explicit instruction for this partial delivery: **page 0 = cover A** (page-00.jpg), **page 1 = cover B** (page-00b.jpg — which is actually the cover of *"The Omega Device #2"*, a separate issue, not an alternate cover of issue 1). All other pages use the artist's own file number directly (page-02 → page 2, page-41 → page 41, etc.). **Known deviation:** `beats.schema.json` requires `page ≥ 1`; page 0 (cover A) violates that minimum by explicit task instruction. This is flagged in the validation output rather than silently worked around — see `page_notes` on page 0 in `beats.json`.

## Growth-page accounting
**⚠ Not a valid density metric for the underlying comic — see sampling caveat above.** Computed strictly per the rubric's formula on the 11 sampled pages:
- Growth pages (trigger/early/mid/peak OR role==active-growth): **6 / 11 → growth-page ratio = 55%** (pages 2, 3, 4, 5, 10, 41)
- Transformation / growth scenes:
  - **Hero transformation — p3 (mid) → p4 (peak) → p5 (aftermath/full-body-reveal)** — devices: multi-panel-progressive (via p3's stacked-silhouette timeline), clothing-destruction, zoom-escalation, sfx-driven, full-body-reveal.
  - **Heroine reveal — p10 (peak)** — devices: sfx-driven, full-body-reveal. No build-up panels are present in this delivery; reads as one-and-done (may be an artifact of the missing pages between p5 and p10, not necessarily the full comic's actual pacing).
  - **Cosmic climax — p41 (peak)** — devices: size-comparison (literal planet at his feet), full-body-reveal.
- Zoom coverage: heavy where it appears. p4 is 4 consecutive ECU panels (arms→shoulders→arms→glutes); no other page uses ECU as its dominant shot.

## Camera
- **Distance spread:** wide across the sample — EWS is unused, but WS/MS/MCU/CU/ECU all appear. p4 deliberately locks to ECU for all 4 panels (a dedicated zoom page, not monotony); p2, p11, p20, p21 mix distances more freely.
- **Flat-panel hotspots:** p2 panels 1, 3, 5 (three separate flat-level beats across an 8-panel dialogue page); p20 panels 2–3 (a thinking→reaction pair bracketed by two strong panels); p21 panels 4 and 6 (plain reaction two-shots).
- **Best dynamic compositions to steal:**
  - **p1 (cover B) panel 1 / p20 panel 1 / p21 panels 1 & 5** — the signature rear worm's-eye, arms-crossed-behind-the-back shot, restaged four times across just 11 pages. This is the single strongest, most reusable device in the set.
  - **p3** — a single bleed splash compressing an entire growth escalation into one frame via 5 staggered, increasingly large figures receding into a speed-line vanishing point.
  - **p41** — a colossal figure straddling a literal tiny Earth, the boldest scale-comparison device sampled.
  - **p20 panel 4** — both fists punched directly at the lens in heavy foreshortening, the dynamic climax of an otherwise talk-heavy page.

## Expressions
- **Where faces carry the beat:** p10 (intensity-5 triumphant smirk under a "BOOOM!" SFX), p20 panel 4 (intensity-5 rage mid-foreshortened-punch), p41 (intensity-5 maniacal laugh at cosmic scale), and p4 panel 1 (the one growth ECU that *does* pair a face with the muscle tear — intensity-5 ecstasy).
- **Dead-face defects (the call-out):** **p4 panels 2–4 go completely faceless** during the loudest SFX ("BULGE!!", "SHKZROOM", "THOOOOM") — the artist proves on panel 1 of the very same page that he can pair a face with a growth ECU, then doesn't for the next three. p11 panels 3 and 6 (explicit content) also carry no tagged expression, though that's partly a content-safety tagging choice rather than a drawn defect.

## Story & structure
- **Hook:** fast on the cover — both covers promise an already-transformed hero/villain in mid-power-display before any story page is read.
- **Pacing:** cannot be reliably assessed — the visible pages jump p2→p3→p4→p5 (one continuous transformation run, good pacing signal) then skip straight to p10, p11, p20, p21, p41 with unknown gaps of unseen pages between each. What's visible reads front-loaded and eventful; what's missing is unknowable from this sample.
- **Tease vs payoff:** the hero's transformation (p2 trigger → p3 escalation → p4 ECU burst → p5 reveal) is a well-built four-page tease-to-payoff arc. The heroine's transformation (p10) has no visible tease at all in this sample — straight to payoff, though this is very likely just the missing pages, not the actual comic's structure.
- **Cliffhanger / continuity:** p41 ends on an explicit "to be continued" beat — a colossal, laughing, cosmic-scale antagonist straddling the Earth is about as hard a pull-forward as the genre offers.
- **Dialogue & SFX:** unlike some corpus entries, this one is **fully lettered** — dialogue balloons carry plot and characterization throughout (the villain's crude gloating on p20, the couple's pillow talk on p11, the cop's confused "excuse me" on p21). SFX is used heavily and well on growth/impact beats (RIP/BULGE/SHKZROOM/THOOOOM on p4; WHOOOOM/CRASH/CRACK-AK on p21) — SFX size and repetition (RIPPP → RIIIIIP → RIIIIIIIP) scale visibly with intensity, a nice nonverbal escalation cue.
- **Clarity:** action-to-action legibility is good within each page; the *cross-page* narrative (why the villain is now transformed and violent, what "Roxy" being in jail means, what evidence he's breaking her out to reach) is not reconstructible from this sample because of the missing pages.

**Narrative arc:** ordinary man argues with his girlfriend and a bully outside a wall → she hands him a mysterious device → he presses the button and undergoes an explosive muscle transformation → full-body hero reveal as "Omega" → his girlfriend also reveals her own transformed super body and they celebrate together → meanwhile the empowered bully turns violent, gloats, and breaks an ally out of police custody → his power escalates to cosmic, planet-straddling scale (to be continued).

## Angle & pose study
*(Full per-panel data in `angle-study.json`; this section summarizes the artist's staging vocabulary for the 3D-CGI pipeline.)*

- **Camera-to-body relationship:** Deed Arts strongly favors **low and worm's-eye cameras** (13 of 34 panels are low/worm/dutch — 38%) whenever a figure is meant to read as powerful; talking-head/dialogue beats default to plain eye-level (20 of 34 panels). There is essentially no high-angle/vulnerability staging anywhere in the sample — every muscle character is shot to look dominant, never small.
- **Which limb goes at the lens:** `toward_camera` splits fairly evenly between **back** (6 panels) and **chest** (5) as the dominant "hero mass" targets, with **fist** (4, all foreshortened punches/flexes) as the next most common. Notably, **glute** and **thigh** each appear only once despite being visually prominent in several panels — the artist tends to frame the *back* as the money-shot rather than isolating the glutes/legs on their own, even in the rear-view "signature pose."
- **How he crops the figure:** heavy use of **full-bleed, full-body crops** for splash/reveal pages (`crop: full`, `panel_shape: bleed`) contrasted with tight **body-part-only** ECU crops for the dedicated growth-burst page (p4). There is almost no "head-cut-off" or "feet-cut" cropping — figures are either shown whole (reveal pages) or reduced to a single muscle group filling the frame (growth pages); very little in between.
- **How he sells each muscle group:** `muscle_sold_histogram` = back 5, arms 5, full-silhouette 3, chest 2, glutes 2, abs 2, shoulders 1 (14 panels have no figure/muscle focus — dialogue-only beats). **Back** is sold almost entirely through the rear worm's-eye crossed-arm pose reused four times; **arms** are sold through foreshortened bicep ECUs and fist-at-camera punches; **glutes** are sold as a side-effect of the back-focused rear shots rather than as their own composition.
- **Page-layout rhythm:** splash pages (0, 1, 3, 5, 10, 41 — over half the sample) carry zero grid structure at all; the grid pages (2, 4, 11, 20, 21) use conventional 2–3 panel rows with the occasional bleed/borderless panel used specifically to mark a tonal break (the p2 trigger handoff bleeds past its gutter; the p4 growth ECUs are otherwise hard-bordered). The result is a rhythm of **quiet grid pages building toward a wordless splash payoff** — visible clearly in the p2(grid)→p3(splash)→p4(grid)→p5(splash) sequence.
- **Best 8–10 stagings to steal for photoreal 3D-CGI panels:**
  1. **p1 (cover B) n1 / p20 n1 / p21 n1 / p21 n5** — the signature rear worm's-eye crossed-arm pose. *Prompt seed:* "Camera down at worm's-eye level behind and below the figure, looking up a towering back with the arms crossed low behind the body, the head tipped back and small at the top of the frame so the trapezius and rear-delt mass fills the panel."
  2. **p3 n1** — single-frame ghost-trail growth timeline. *Prompt seed:* "Camera low and close, staggered ghost-repeats of the same standing pose recede into the distance behind the figure, each one larger and more muscular than the last until the nearest, biggest figure fills the foreground in a double-bicep flex with radiating speed-lines behind him."
  3. **p5 n1** — low-angle full-body reveal walk. *Prompt seed:* "Camera low, just below chest height, angled slightly upward as the figure strides forward with both arms flexed out to the sides in a lat-spread pose, radiating speed-lines behind him, filling nearly the whole frame."
  4. **p10 n1** — eye-level three-quarter power pose with SFX-driven reveal. *Prompt seed:* "Camera at eye height, the figure stands in a three-quarter power pose with one hand near the chin and the other on the hip, weight shifted onto the back leg, sparkles and a radiating burst pattern filling the background behind her silhouette."
  5. **p20 n4** — foreshortened double-fist-at-camera. *Prompt seed:* "Camera close at chest height, both fists punched directly toward the lens in heavy foreshortening, the face visible just behind and above them, radiating speed-lines filling the background."
  6. **p21 n5** — rear-view contact-deform action beat. *Prompt seed:* "Camera low behind the figure as one arm punches forward into a shattering surface, debris flying, the back and glute mass filling most of the frame, a small startled onlooker in the corner for scale."
  7. **p41 n1** — cosmic scale-comparison. *Prompt seed:* "Camera at an extreme low worm's-eye angle looking up past a tiny planet at the figure's feet, straddled stance, arms crossed over the chest, head tipped back, a radiating starburst filling the space behind him so the whole body reads as a silhouette against light."
  8. **p4 n1** — growth ECU paired with a face. *Prompt seed:* "Extreme close crop on a flexing bicep tearing through a sleeve, sharp claw-shaped force lines radiating outward, a small triumphant face inset in the upper corner of the frame."
  9. **p21 n1** — low three-quarter landing crouch. *Prompt seed:* "Camera low and close as the figure lands in a crouch, seen from a three-quarter angle behind and below, impact debris and speed-lines radiating from the point of landing."
  10. **p2 n8** — bleed/ghost trigger handoff. *Prompt seed:* "Camera at eye height on a hand passing a small glowing device to a second figure, a thin energy arc connecting the device to the receiver's temple, the panel bleeding into a smoky borderless background rather than a hard frame."

## What does NOT translate to 3D
- **Impossible crossed-arm forearm interlock** in the signature rear pose (p1 n1, p20 n1, p21 n1/n5) — reads fine as flat linework but the forearms overlap in ways a rigged 3D figure can't physically replicate; needs re-blocking for CGI.
- **Claw-shaped radiating force lines** drawn directly onto the muscle surface (all of p4) — a pure 2D FX convention; replace with practical rim light, particle dust, or a post-process glow rather than trying to model the lines.
- **Solid-black cape/cloth tearing into hard graphic shapes** (p4 n2) — reads as fabric only through flat silhouette; a 3D cloth sim would need real tear geometry.
- **Stacked-ghost-repeat single-panel growth timeline** (p3) — a compositing trick, not a single-camera shot; must be built as a multi-render composite, not attempted in one pass.
- **Halo/glow rim outlining entire figures against the background** (p0, p1, p3, p5, p10, p41) — a flat ink/shader trick; needs to become genuine rim/backlighting in the render, not a uniform outline.

## Strengths to steal
- **p3's single-panel stacked-silhouette growth timeline** compresses a full transformation escalation into one bleed splash — a directly reusable "ghost-trail" composite idea for CGI.
- **The rear worm's-eye crossed-arm pose repeats 4 times** across just 11 pages (p1, p20 n1, p21 n1, p21 n5) — proof this artist has a genuine go-to "power entrance" staging worth stealing wholesale.
- **p4 stacks four back-to-back ECU money-shots** (bicep, delt, forearm, glute) with escalating SFX (ZRAAK→BULGE→SHKZROOM→THOOOOM) — a clean template for a rapid-fire growth-burst sequence.
- **p5, p10, and p41 all close their beats with a full-body reveal splash at a low/worm's-eye angle** — consistent payoff grammar worth copying for the pipeline's own growth climaxes.
- **p41's literal planet-scale-comparison** is the boldest size-comparison device in the set — cheap to reproduce in CGI as a comped miniature-Earth prop.
- **SFX lettering scales with intensity** (RIPPP → RIIIIIP → RIIIIIIIP) — a nonverbal escalation cue the pipeline's lettering pass could reuse.

## Weaknesses to avoid
- **p4's three tightest growth ECUs go faceless** (panels 2–4) exactly during the loudest SFX beats — the same dead-face-during-peak-growth gap flagged elsewhere in the corpus, made worse here because panel 1 of the same page proves the artist can pair a face with the muscle tear.
- **p10's female transformation has zero build-up panels** in this delivery — straight to a "BOOOM!" reveal with no escalation, the one-and-done pattern the rubric scores down (though this may be an artifact of the missing pages rather than the full comic's real structure).
- **p2 leans on three flat-level dialogue panels** (1, 3, 5) before the trigger — the setup drags camera-wise even though the confrontation has real stakes.
- **p20 panels 2–3 are plain flat-level talking-head beats** bracketing a much stronger foreshortened fist panel — a mid-page dip in dynamism.
- **Explicit content on p11 (panels 3, 6)** leaves large parts of that page low-yield for the staging study beyond its two non-sexual flex panels.
