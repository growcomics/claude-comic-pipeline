# Continuity — keeping panels consistent across a comic

*The single biggest quality failure in panel-by-panel generation is drift: props change
shape, set dressing vanishes, characters teleport, geometry mutates on a camera move.
These rules prevent it. Apply on every multi-panel project.*

## 1. Winner-first chaining (the core loop)
Generate a panel → **pick the good variant FIRST** (human approves) → use that approved
image as a **reference for the next panel**. Never build panel N+1 off an unreviewed
panel N. The approved panel carries the room state, set dressing and character placement
forward. This is the chain anchor.

## 2. Reference stack per panel
Attach, in order:
1. **Character refs** (identity — faces/hair/tattoos/outfits; from the cast sheet).
2. **Location/room ref** (the environment; for camera moves see §5).
3. **Key-object refs** (recurring props — see §3).
4. **The previous approved panel** (so placement + set dressing persist).
Then the prompt specifies ONLY what changes this beat (pose, action, growth, camera).

## 3. Dedicated refs for recurring objects
Any important prop reused across many panels (a bottle, a weapon, a phone, a magic item)
gets its **own generated reference image** up front, alongside the character + location
refs. Reuse it every panel so the object stays identical instead of being re-imagined.
Generate these in the reference stage; list them in `references_required.json`.

## 4. Prop & placement persistence
- Set dressing (snacks, cans, bowls, clutter) **stays where it was** — don't drop, add or
  move it between panels unless the action moves it. Carry the previous panel as ref and
  say "same items in the same places."
- Characters **keep their positions/seats** between panels unless they actually move.
  Don't reshuffle the circle. State positions explicitly when they matter.

## 5. Camera moves need a full-room reference
If the camera rotates or repositions, the model will happily invent a new room. Attach a
**whole-room reference** (a wide establishing render of the full set) so a rotation reveals
the *real* other side of the room, not a hallucinated one — and doesn't silently add or
delete furniture/objects. Lock the room layout once, in a 360-aware establishing ref.

## 6. Object physics & logic
Honor how things actually behave. A spun bottle that has **stopped lies ON ITS SIDE
pointing at the chosen person** — never standing upright. A dropped item is on the floor.
A poured drink is lower. Think through each prop's real state for the beat before prompting.

## 7. Practical checklist before generating a panel
- [ ] Did I pick/approve the previous panel and attach it as the chain ref?
- [ ] Are the character refs + location ref + key-object refs attached?
- [ ] Does the prompt keep set dressing + placement, changing only the beat's action?
- [ ] If the camera moved, is a full-room ref attached?
- [ ] Do recurring objects (the bottle) match their dedicated ref + correct physics?
