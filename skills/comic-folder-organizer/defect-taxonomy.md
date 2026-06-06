# Defect Taxonomy — Stage 11 Defect QA pass

This is the catalog the Defect QA subagent uses to scan a story-ordered sequence for **technical render defects** — the unintended failures that need cleanup or regeneration. Pass this file to the subagent **verbatim**; do not paraphrase it from memory (paraphrasing drops categories and the guardrails are easy to lose).

Defect QA is about *within-panel technical quality*. It is **not** continuity (cross-panel wardrobe/prop/location drift — that's the `continuity-check` skill), and it is **not** story (missing beats — that's Stage 12 Story Doctor).

---

## ⛔ Read this first: do-NOT-flag guardrails

This cast is deliberately off-distribution. The following are **intended features, never defects.** Flagging them is the most common Defect-QA failure mode.

- **Muscle size.** Heavily muscled figures (size 5+) are the project look. A huge bicep, traps, or quad is *correct*, not a deformity. Only flag musculature if it's anatomically *broken* (e.g. a muscle fused into the wrong limb, a tricep growing out of a forearm), not because it's large.
- **Chest / bust size.** Large busts are an intended, locked feature — and prompts deliberately **oversize** them to compensate for the model scaling off-distribution features toward average. Never flag "breasts too large." Only flag if anatomically broken (e.g. three breasts, a breast merged into an arm).
- **Photoreal CGI / 3D / DAZ3D rendering.** This is the chosen style. Do **not** flag "looks 3D / not 2D / too rendered." That's the spec.
- **Intended transformation states.** Costume destruction, suit-rip, hair-down, mid-growth proportions at a TF tier are *story states*, not render bugs — when they match the scene. Only flag a wardrobe failure if it's clearly an unintended glitch (a stray hole in an otherwise-intact locked outfit), not an intended TF beat.
- **Beauty anchoring.** Deliberately striking/idealized faces are intended. Don't flag "face too perfect / airbrushed."

**When you genuinely can't tell** whether something is an intended feature or a defect (e.g. "is this arm huge-on-purpose or melted?"), output it as an **`ASK`** row rather than auto-marking FIX. The user resolves it in the review composite.

---

## Defect categories

Scan every panel for these. Each finding is one row in the output.

### 1. Hands & fingers  (category: `hands`)
The highest-frequency defect class in AI generation. Look for:
- Extra fingers (6+), missing fingers, fused/webbed fingers, two thumbs.
- Claw-curl, boneless/rubber fingers, fingers bending the wrong way.
- Hands merged into props or into another character's body.
- Mismatched hand sizes, a hand with no visible thumb.

### 2. Faces & eyes  (category: `face`)
- Asymmetric / melted / smeared facial features, drifting jawline.
- Eyes: lazy/wall-eye, double iris, mismatched eye sizes, pupils pointing different directions, missing catchlight asymmetry.
- Teeth: fused row, too many teeth, teeth bleeding into lips.
- Ear mismatch, earring fused to face, a second faint face ghosted behind the main one.
- **Severity weights up sharply when the face is the central subject** (ECU / close-up). A melted face in a wide background figure is minor; a melted hero close-up is a blocker.

### 3. Limbs & gross anatomy  (category: `anatomy`)
- Extra or missing limbs, a third arm/leg, fused bodies between two characters.
- Joints bending backward, a forearm with no elbow, a limb emerging from the torso.
- Foreshortening failures (an arm that dissolves where it should recede).
- Remember the guardrail: **large muscle ≠ anatomy defect.** Only structural breakage counts here.

### 4. Phantom / extra characters  (category: `extras`)
- Any person in frame beyond the named cast for that scene. Background extras, a duplicated character, a half-formed figure in the crowd.
- QA-count the people in frame against the scene's cast list; if count > expected, flag it.
- (This is a standing project rule — comic panels contain only the named cast.)

### 5. Anachronistic / hallucinated accessories  (category: `accessory`)
- Wristwatches, smartwatches, modern jewelry, lanyards, sunglasses, phones — anything the model hallucinated onto a character who shouldn't have it.
- Especially check wrists, necks, ears, fingers when those are in frame.
- (Models love to add watches and jewelry; if the wrist/neck is visible and the canonical look doesn't include it, flag it.)

### 6. Text & SFX garbling  (category: `text`)
- SFX lettering that's misspelled, gibberish, or melted ("KRAA-KOOOM", warped letterforms).
- Speech-bubble text that's garbled, doubled, or nonsense.
- Stray hallucinated text/signage/watermarks in the background.

### 7. Props & environment  (category: `prop`)
- Warped, melted, or duplicated props; an object floating with no support.
- Impossible geometry (a doorway that goes nowhere, furniture fused to a wall).
- Duplicated background elements (the same window/locker tiled unnaturally).
- Environment that contradicts the locked location (only if clearly a render glitch, not a scene change — scene changes are continuity, not defect).

### 8. Render artifacts  (category: `artifact`)
- Smearing, JPEG-mush, color banding, posterization in what should be smooth gradients.
- Visible compositing seams or a hard rectangle where two generations were stitched.
- Unintended heavy blur on the subject, or a focus that's on the wrong plane.
- Low-res / upscaling halos, double-stamped thumbnail mush (also caught by the <150KB heuristic in Stage 8).

### 9. Duplication / cloning  (category: `clone`)
- The same face appearing twice in one panel (a character and their accidental twin).
- Mirror-duplicated body parts, a cloned hand pasted on the wrong arm.

---

## Severity scale

| Sev | Meaning | Typical default remedy |
|---|---|---|
| **S1** | **Blocker.** Defect on the central subject that the eye lands on first. Breaks the panel. (Melted hero face, 3-armed lead, garbled hero-shot SFX.) | **REGEN** |
| **S2** | **Noticeable.** Real defect, but localized or off-center. Reads as wrong on a second look. (6 fingers on a mid-frame hand, a phantom watch, a garbled secondary SFX.) | **INPAINT** (or REGEN if inpaint is hard) |
| **S3** | **Minor / cosmetic.** Small, peripheral, or won't read at final post size. (A slightly-off background hand, faint banding in the sky.) | **KEEP** (or optional INPAINT) |

Severity is driven by **how central the defect is**, not just how bad it is in isolation. The same melted hand is S1 in a hand-focused close-up and S3 in a distant background figure.

---

## Triage decision rules (regen vs inpaint vs keep)

Default the remedy per-panel using these rules:

- **REGEN (regenerate the whole panel)** when the defect is *structural and central*: the subject's anatomy/face is broken, the cast count is wrong on the main figures, the whole composition is off, or the defect can't be cleanly inpainted without re-rendering the subject. Regen costs the most credits — reserve it for defects that the eye can't unsee.
- **INPAINT (localized touch-up)** when the defect is *contained and peripheral*: one hand, a watch, a patch of garbled text, a single warped background prop. The rest of the panel is good and worth keeping.
- **KEEP** when the defect is *cosmetic and won't read* at the size/context the panel posts at — out of focus, tiny, at the frame edge. Don't burn credits chasing invisible blemishes.
- **ASK** when you can't tell intended-feature from defect (see guardrails). Surface it; don't decide.

When in doubt between REGEN and INPAINT, prefer INPAINT (cheaper) and let the user upgrade it to REGEN in the review composite.

---

## Output format (subagent → orchestrator)

Defects only — omit clean panels entirely. One row per finding:

```
NNN.ext | FIX | <S1|S2|S3> | <category> | <one-line description + where in frame> | <REGEN|INPAINT|KEEP>
NNN.ext | ?   | <S?>       | <category> | <why it's ambiguous: intended feature or defect?> | ASK
```

Examples:
```
034.png | FIX | S1 | face     | Lacy face melted/asymmetric, central ECU subject        | REGEN
041.jpg | FIX | S2 | hands    | right hand 6 fingers, mid-frame holding clipboard       | INPAINT
041.jpg | FIX | S3 | accessory| faint wristwatch on Lana, far edge of frame             | KEEP
058.png | FIX | S2 | text     | SFX reads "KRAAA-KOOOM", warped letterforms             | INPAINT
063.png | ?   | S2 | anatomy  | Mira's upper arm enormous — intended muscle or melt?    | ASK
072.png | FIX | S1 | extras   | unnamed 3rd lifeguard in background, cast is only 2      | REGEN
```

Then the orchestrator builds `_defects_review.png` (grouped by severity, cyan borders) for the veto gate, and writes the confirmed survivors to `_defects_report.md` as a regeneration checklist. FIX panels stay in the sequence as keepers until the user regenerates them.
