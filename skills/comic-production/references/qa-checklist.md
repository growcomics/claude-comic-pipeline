# Quality Assurance Checklist
## Run This After Every Batch of Generated Pages

> **STATUS: PARTIALLY DEPRECATED — read before using.** Last reviewed 2026-05-11.
>
> Two areas of this checklist pre-date the discovery of **L7 Case B** in `lessons-learned.md` (lettering and SFX baked into the generation prompt cause 2D illustration drift in CGI panels):
>
> - **Transformation Scenes → "Action lines and SFX present"** — obsolete. SFX text ("RRRRIP!", "CRACK!", "THROB") and "action lines radiating outward" in the render are exactly what causes L7 Case B 2D drift. Confirmed in the Chun-Li growth series. These now belong in `page-composer` post-render. The render itself should have NO baked-in lettering. See L7 Case B for the alternative (physical scene cues only: sweat, fabric strain, dust, motion blur — described in non-comic-coded language).
> - **Dialogue and Text** (whole section) — obsolete. Speech bubbles, attribution, repeated lines, text legibility — all of these are now checked at the `page-composer` stage, not against the generation output. The render must NOT include speech bubbles, thought bubbles, or caption boxes. Per L4 (deprecated) and L7 Case B, dialogue/captions live in `shotlist.json`'s `dialogue[]` / `captions[]` arrays and are added as vector overlays.
>
> What's still valid: **Character Consistency, Background and Environment Consistency, Facial Expressions and Character Acting, Anatomy, Production Hygiene**, and most of the Transformation Scenes section (everything except the SFX check). The visual-quality-standards benchmarks (`assets/visual-quality-standards.json`) for breast size, bicep detail, and abs detail are still the canonical floor.
>
> The deprecated items are preserved with inline ⚠️ markers so this doc remains useful as a historical record and so contributors can see what changed.

This checklist catches the most common and damaging issues. Run through it for every batch of generated pages before delivering to the user. Each item comes from real production failures — they're ordered roughly by how often they occur and how badly they hurt the final product.

---

## Character Consistency (check across sequential panels)

- [ ] **Body type stable**: Each character maintains the same body type across panels. No one goes from chubby to thin to chubby, or from muscular back to baseline, between consecutive panels. After a transformation, the character stays at that size or larger.
- [ ] **Clothing stable**: Each character's outfit stays the same within a scene. No sleeves appearing/disappearing, no outfit changes mid-conversation, no text/logos appearing and vanishing on clothing between panels.
- [ ] **Skin tone stable**: Characters don't get lighter or darker between panels. Watch for this especially with characters who appear in different lighting conditions.
- [ ] **Hair consistent**: Hair color, length, and style stay the same unless the story explicitly changes them.
- [ ] **Character count correct**: If three characters are in a scene, there are exactly three in every panel of that scene. No one appears or disappears without a story reason.

**How to fix**: Add more explicit character descriptions to the prompt — specify outfit details, body type, skin tone, and hair in every panel, not just the first one. The model has no memory. If you described a character wearing a sleeveless top in panel 1 but didn't mention it in panel 3, panel 3 may add sleeves.

---

## Background and Environment Consistency

- [ ] **Location stays the same within a scene**: Characters don't teleport. If a scene is set in a lab, every panel in that scene shows the lab — not a rooftop, not an outdoor area, not a different room. This is one of the most jarring issues when it happens.
- [ ] **Environment description used**: The panel prompt includes the full environment description from the ENVIRONMENTS lookup, copied verbatim, not paraphrased from memory.
- [ ] **Props and furniture consistent**: If there's a stainless steel table in one panel, it should be there in the next. If characters weren't leaning on something before, they shouldn't suddenly be leaning on it.
- [ ] **Lighting consistent within a scene**: Morning light stays morning light. Lab fluorescents don't become natural sunlight mid-scene.

**How to fix**: Always paste the environment description from your ENVIRONMENTS lookup into every panel prompt in that scene. Don't rely on the model to remember what the room looked like. If environment images were pre-rendered (Phase 1.3), cross-reference them visually. For hero locations, also see `environment-references.md` (the DAZ3D-scene-reference trick: attach a real DAZ3D render as an env ref with transform instructions for stronger anchoring).

---

## Facial Expressions and Character Acting

- [ ] **No blank/neutral faces**: Every character has a vivid, readable expression. No one stares blankly into space, especially during dramatic moments.
- [ ] **Eyes directed correctly**: Characters look at each other or at what's happening — not at the camera/viewer, and not staring off into empty space.
- [ ] **Expressions match the moment**: During transformations, characters react with appropriate emotion (shock, joy, excitement). During conversations, faces match what's being said.
- [ ] **Background character reactions present**: During dramatic moments, bystanders react visibly — wide eyes, open mouths, pointing, stepping back. No one stands neutrally during something extraordinary.
- [ ] **Each character's expression is distinct**: In multi-character panels, everyone has a different emotional beat. No identical smiles or repeated expressions. (See `multi-character-variation.md` for the anti-uniformity rules and `posing-and-expressions.md` for the mechanical facial-acting vocabulary.)

**How to fix**: Use mechanical face descriptions from `posing-and-expressions.md` (eyelid position, cheek lift, brow angle, mouth shape) rather than just naming emotions. Describe who is looking at whom. For background characters, explicitly describe their reactions.

---

## Camera Variety (multi-panel sequences)

- [ ] **No camera-static sequences**: Across any 10-panel sequence, the panel cameras include ≥5 distinct distance categories (ecu-face / ecu-region / mcu / medium / cowboy / full / wide-establish / splash), ≥4 distinct angle categories (eye-level / low-angle-front / low-angle-back / high-angle / worms-eye / birds-eye / dutch / over-shoulder / profile / three-quarter), ≤3 panels at the same distance × angle combo, and ≥1 ECU + ≥1 wide-establish or splash. See the variety check in `cinematic-framing.md`.

**How to fix**: Reassign per-panel `camera` values in the shotlist using one of the rhythm patterns (pull-in, pull-out, alternating field, orbit). Document an intentional violation if the scene legitimately demands sustained framing (e.g., a long dialogue beat).

---

## Transformation Scenes

- [ ] **L35 — Growth-page ratio meets the chapter-type target**: Count growth pages (any panel with an active growth beat — trigger / first_sensation / body-region / whole_body / reveal) ÷ total pages. Compare against the target for this chapter type (transformation ≥60%, climax ≥70%, action/plot ≥30%; see `script-breakdown` §4.6). If under target, the chapter under-delivers the niche payload — add or spread growth beats. Corpus baseline: 21–77%, median ~50% (`research/comic-corpus/synthesis/success-elements.md`).
- [ ] **L35 — No faceless money-shot run**: Scan each transformation's body-region ECU sequence. A run of more than ~2 consecutive face-cropped ECUs with no interleaved face-bearing reaction/reveal panel is a defect — the corpus's #1 weakness (emotionless money-shots). **How to fix**: insert a reaction-intercut panel (the grower's strained/ecstatic face, or a witness recoiling) per `references/escalation-devices.md`.
- [ ] **L35 — Face sells the growth on every face-visible growth panel**: On any growth panel where a face is in frame (stage_change, whole_body, reveal, aftermath, trigger, first_sensation), the face registers PEAK intensity matched to the beat (strain / ecstasy / awe / triumphant) — never neutral, calm, or slack. A dead face on a growth beat is a hard defect. (See also "Facial Expressions" above.)
- [ ] **L35 — Scene uses ≥2 escalation devices**: Each transformation scene visibly employs at least two devices from `references/escalation-devices.md` (sfx-driven, reaction-intercut, full-body-reveal, size-comparison, multi-panel-progressive, zoom-escalation, clothing-destruction, slow-burn). Avoid escalation-by-repetition — each reveal must change scale, angle, or stakes, not repeat the same big-body splash.
- [ ] **Multi-panel expansion**: Transformations are spread across multiple panels (growth beginning, closeup of focal body part, optional torso laughing shot, final reveal). No single-panel transformations unless it's a very minor change.
- [ ] ⚠️ **DEPRECATED — Action lines and SFX present**: ~~Transformation panels include visual storytelling cues — action lines radiating from growing areas, SFX text ("RRRRIP!", "CRACK!", "THROB") near tearing fabric or swelling muscles.~~ This check is OBSOLETE per L7 Case B. Baked-in SFX text causes 2D drift in CGI panels. **New check**: transformation panels include *physical-scene* storytelling cues only — sweat, fabric strain, dust kicked up, motion blur, particle effects — in non-comic-coded language. SFX text and action lines are added by `page-composer` post-render as vector overlays.
- [ ] **Growth sequence order**: Multi-panel transformations follow breasts-first, glutes-second, muscles-third order (unless the story requires otherwise). See `posing-and-expressions.md` "Growth Sequence Order".
- [ ] **Muscle color correct**: Muscles are rendered as natural healthy skin tone, not red or inflamed. Skin is wet/shiny/glistening, not raw or damaged.
- [ ] **Muscles and breasts together**: Any character with enlarged muscles also has proportionally enlarged breasts. These are always specified together.
- [ ] **Skin not torn/damaged**: Skin looks smooth and glistening. Words like "straining," "tearing," or "bursting" are used for fabric only, never for skin.
- [ ] **No duplicate transformation scenes**: Each transformation happens once. If a regeneration was needed, the old version should be removed. No two panels showing the same growth beat.
- [ ] **Breast size meets minimum**: Compare any panel described as having "large" breasts against the benchmark in `assets/visual-quality-standards.json`. If they're smaller than the reference, they're not large — redo with stronger size language in the prompt.
- [ ] **Bicep detail sufficient**: For flex or bicep closeup panels, compare against the bicep benchmark. Target the same level of vein visibility, fiber definition, and skin sheen.
- [ ] **Abs detail sufficient**: For torso or abs closeup panels, compare against the abs benchmark. Target the same level of segment definition and lighting quality. (See also `fmg-anatomy-guide.md` "Abs-Specific Failures" table for the most common abs errors and their fixes.)
- [ ] **Stage-change panels use the muscle-size lineup**: For any panel that crosses a size tier (size 3→4, size 5→6, etc.), the lineup ref (`assets/muscle-size-lineup.png` or `assets/muscle-size-lineup-4-9.png`) was attached and the panel prompt called out the specific number. See L5 in `lessons-learned.md`.

**How to fix**: Include the (still-valid portion of the) mandatory rules block from `prompt-templates.md` in every transformation prompt. Use the transformation panel templates from `prompt-templates.md` (Panels A–E, MINUS the deprecated SFX section). For size/detail issues, reference the visual quality standards and use more emphatic size language ("enormous," "massive," "overwhelmingly large" rather than just "large").

---

## ⚠️ DEPRECATED — Dialogue and Text

> The entire section below is obsolete. The render must not include speech bubbles, thought bubbles, captions, or any baked-in text. All lettering is done by `page-composer` as vector overlays on top of the clean CGI render. These checks now apply at the `page-composer` review stage instead, and they apply to the lettered overlays — not to the model's output.
>
> Preserved for historical reference only.

- [ ] ~~**Correct character speaking**: Speech bubbles appear next to/above the correct character. The bubble clearly belongs to the character who is supposed to be speaking that line.~~
- [ ] ~~**No repeated lines**: Every speech bubble contains a unique line. No character says the same thing twice in one panel or in adjacent panels.~~
- [ ] ~~**Dialogue matches the script**: The text in bubbles matches what the script says. No paraphrasing, no missing lines, no added lines.~~
- [ ] ~~**Text is legible**: Speech bubble and narration text is readable and not cut off or overlapping.~~

**Replacement check (during render QA, pre-page-composer)**:
- [ ] **No baked-in lettering**: The generated panel contains zero speech bubbles, thought bubbles, caption boxes, SFX text, or any visible written words apart from incidental real-world signage (e.g., shop signs, posters in the environment that happen to be in the scene). If any speech bubble or SFX text is in the render, **reject and regenerate** — the prompt has a lettering instruction that needs to be removed.

---

## Anatomy

- [ ] **Two arms per character**: No extra limbs, no missing arms.
- [ ] **Two legs per character**: No third or fourth legs (the model generates extra legs more often than extra arms; check both).
- [ ] **Proportions correct**: Limbs are proportional, hands are correctly formed, faces have normal proportions.
- [ ] **Character positioning logical**: People are standing/sitting in physically plausible positions. No impossible body angles or floating limbs.
- [ ] **FMG anatomy rules followed** (when applicable): See `fmg-anatomy-guide.md` — hourglass figure preserved, small head/hands/feet, round (not teardrop) breasts, pillowy (not blocky) abs, asymmetric leg contours, no drumstick forearms.

---

## Continuity (chained sequences)

- [ ] **Job IDs captured**: Every panel's job_id was recorded before the next panel was submitted. See L9 in `lessons-learned.md`. Missing IDs = broken chain = silent state regression in subsequent panels.
- [ ] **View-aware chaining**: When a panel's view differs from the prior panel's, the chain anchor was a view-compatible earlier panel (not blindly N−1). See L1.5.
- [ ] **No costume regression**: Across a chained sequence, costume damage (torn seams, missing fabric, etc.) accumulates monotonically — never resets or shrinks. See L1.
- [ ] **No size regression**: Once a character reaches a muscle/breast/glute size, they stay at that size or larger in all subsequent panels.

---

## Production Hygiene

- [ ] **All images saved to project folder**: Every generated panel has been downloaded and saved to the project's directory with a consistent naming scheme (e.g., `01-front-full.png`, `02-ecu-bicep.png`, etc.).
- [ ] **Pages in correct order**: Panels within the folder appear in story order when sorted by filename.
- [ ] **No orphaned/extra images**: Only the best version of each panel is in the folder. Failed generations and rejected alternatives have been excluded.
- [ ] **Job ID log preserved**: For Higgsfield runs, `state.json` is preserved. For Flow runs, `job_ids.md` (or equivalent chain log) is current. This is the recovery record if anything needs to be redone.

---

## Quick Pass vs. Full Review

**Quick pass** (for mid-batch spot checks): Check character consistency, background consistency, expressions, and the no-baked-lettering check. These are the most common failures and can be caught at a glance.

**Full review** (before delivering to the user): Run every item on this checklist. Focus extra attention on transformation scenes (especially stage-change panels with lineup ref + size language) and continuity across the chain. After this checklist passes, hand off to `page-composer` for lettering — that's where dialogue, captions, and SFX get added as vector overlays.
