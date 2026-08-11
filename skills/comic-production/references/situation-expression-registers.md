# Situation-Expression Registers (L39)
## Anti-uniformity within a situation-appropriate register

The four-woman showcase templates in `posing-and-expressions.md` fixed pose/expression
uniformity — but they fit exactly ONE dramatic situation: the celebratory showcase.
Reusing their poses and emotions on a confrontation, a defeat, or a reveal produces
panels that are varied and wrong: a woman mid-face-off wearing "ecstatic, laughing joy"
is a worse storytelling failure than a uniform panel.

**The rule: the situation names the register.** The shotlist beat declares a
`panel_situation`; that situation maps to a register — a menu of 4 poses and 4 emotions
that belong to that dramatic moment. Each character in the panel gets a DIFFERENT
pose+emotion pair drawn FROM that register. Variety stays mandatory
(`multi-character-variation.md` still applies in full); the register bounds WHICH
varied choices are legal for this beat.

This doc EXTENDS `posing-and-expressions.md` — the showcase register below IS that
guide's template set, unchanged. Everything else here covers the situations that guide
doesn't. Companion layer: `staging-and-composition.md` (L34) places the bodies in
space; this doc (L39) governs what each body and face is doing there.

---

## The selection rule (mechanical)

1. **The shotlist beat declares `panel_situation`** (emitted by `script-breakdown`;
   required on any panel with 2+ named characters, encouraged on solo panels).
2. **The situation names the register.** Pose and emotion choices come ONLY from that
   register's two menus below. A showcase pose or emotion on a non-showcase beat is a
   defect (proposed gate: D15).
3. **Each character gets a DIFFERENT pose+emotion pair.** Hard floor: no two characters
   in the panel share the same pair. With ≤4 characters, go further — all-distinct on
   both axes (each register carries 4×4 for exactly this reason). With 5+ characters,
   individual poses/emotions may repeat but pairs never do; stagger which axis repeats.
4. **Equal transformation tier among peers** — the posing guide's key rule. All peers
   in the panel carry identical scale language; variety comes from pose angle and
   reaction, NEVER from size hierarchy. (Deliberate story-tier differences declared in
   `muscle_size_tier` are unaffected — this rule bans *undeclared* size variety.)
5. **The staging stanza carries the labels.** In `qa/staging/<panel_id>.json`, each
   character's stanza gains `register_pose` and `register_emotion` — EXACT label
   strings from the menus. The prose `pose` / `expression` fields then elaborate those
   labels: pose in body terms, expression in mechanical face terms from the table below
   (never just the emotion name — `feedback_expression_intensity`).
6. **Same key, different notes.** The register keeps everyone in the same dramatic key;
   anti-uniformity keeps each character playing a different note in it. Both are
   mandatory; neither substitutes for the other.

---

## The registers

Labels are exact strings (kebab-case) — staging files and the D15 gate match them
verbatim.

| `panel_situation` | The beat is… | Pose menu | Emotion menu |
|---|---|---|---|
| `showcase` | A posed display of the transformation (the posing-guide lineups) | `frontal-flex`, `rear-3q-display`, `dynamic-frontal`, `side-3q-flex` | `triumphant-pride`, `ecstatic-joy`, `theatrical-commitment`, `playful-overwhelm` |
| `celebratory` | Shared victory/joy in motion — cheering, not posing | `hands-up-cheer`, `mid-leap`, `arms-thrown-wide`, `shoulders-back-laughing` | `joy`, `triumph`, `euphoria`, `mutual-recognition` |
| `confrontation` | Two sides squared off; violence possible but not started | `forward-lean-aggressive`, `guard-up-coiled`, `predatory-step-in`, `weight-back-assessing` | `locked-jaw-determination`, `fierce-narrowed-focus`, `contemptuous-smirk`, `cold-clinical-assessment` |
| `mid-action` | The fight/feat is happening THIS instant | `mid-strike`, `mid-recover`, `mid-dodge`, `mid-counter` | `strain`, `snarl`, `locked-focus`, `grimace` |
| `surprise-reveal` | Something unexpected just became visible (a transformation, an arrival, a truth) | `recoil-step-back`, `hands-framing-face`, `lean-in-fascination`, `arrested-mid-motion` | `wide-eyed-shock`, `dawning-realization`, `fascinated-awe`, `first-flex-curiosity` |
| `aftermath-victory` | The dust settled; our side won | `hand-on-hip-swagger`, `foot-on-debris`, `arms-crossed-pleased`, `dismissive-hair-flick` | `smug-satisfaction`, `earned-tired-pride`, `contemptuous-amusement`, `quiet-exultation` |
| `aftermath-defeat` | The dust settled; this side lost | `slumped-against-wall`, `one-knee-recovering`, `hand-to-mouth-pain`, `defiant-stare-up` | `pain-with-resolve`, `disbelief`, `barely-suppressed-rage`, `quiet-acceptance` |
| `dialogue-tense` | Words as weapons — negotiation, threat, interrogation | `forward-engaged-listening`, `arms-crossed-challenge`, `hand-on-table-emphatic`, `lean-on-wall-casual-threat` | `skeptical`, `contemptuous`, `urgent`, `coldly-assessing` |
| `intimate` | Guard down between characters — comfort, connection, vulnerability | `open-toward-each-other`, `hand-reaching`, `forehead-touch`, `weight-shared-leaning` | `soft`, `vulnerable`, `tender`, `open` |

The `showcase` menus are the posing guide's own template set: the four poses are its
"full frontal / rear three-quarter / dynamic frontal / three-quarter side" display
angles, and its facial-acting table already covers the four emotions
(`theatrical-commitment` ≈ its "shocked delight" third-woman register;
`playful-overwhelm` ≈ its "overwhelmed excitement"). For showcase beats, use
`posing-and-expressions.md` directly — its three full prompts are the canonical
elaborations.

---

## Face mechanics — the non-showcase extension table

`posing-and-expressions.md` § "Quick Reference — Facial Acting Mechanics" covers the
celebratory/showcase side. This table completes the set for every other register
emotion. Same rule as the posing guide: **never just name the emotion — write the
face mechanically** (brows, eyes, mouth, jaw, head). Copy the mechanical description
into the staging stanza's `expression` prose.

| Emotion | Mechanical description |
|---|---|
| `joy` | Cheeks lifted high, mouth open in a laugh, eyes crescent-shaped, head tipped slightly back |
| `triumph` | Chin raised, mouth open mid-shout, brows lifted, eyes blazing wide, neck extended |
| `euphoria` | Eyes closed, brows drifted upward and relaxed, mouth open in a breathless smile, head rolled back |
| `mutual-recognition` | Eyes locked on the other character (never the camera), brows raised, grin breaking into a laugh, head tilted toward them |
| `locked-jaw-determination` | Jaw set, lips pressed thin, eyes narrowed, brow slightly lowered |
| `fierce-narrowed-focus` | Eyes narrowed to slits and locked on the target, brows drawn hard together, nostrils flared, mouth a flat line |
| `contemptuous-smirk` | One mouth-corner raised, eyes half-lidded and steady, head tilted, one brow faintly arched |
| `cold-clinical-assessment` | Face still, eyes tracking slowly over the target, brows level, lips barely pursed, head fractionally tilted |
| `strain` | Teeth gritted and bared, jaw clenched, brow knotted downward, eyes squeezed near shut, neck tendons standing |
| `snarl` | Upper lip curled to show teeth, nose wrinkled, brows slammed down, eyes wide and hot |
| `locked-focus` | Eyes fixed unblinking on the target, brows level and tense, lips parted for breath, face otherwise still mid-motion |
| `grimace` | Mouth stretched wide and pulled down, teeth together, one eye more closed than the other, brow twisted asymmetrically |
| `wide-eyed-shock` | Eyes at maximum width showing white, brows at the hairline, mouth dropped fully open, head pulled back on the neck |
| `dawning-realization` | Brows rising asymmetrically, lips parting, eyes refocusing off-target, head slowly lifting |
| `fascinated-awe` | Eyes wide and shining, fixed on the subject, brows high but soft, mouth open in a slack half-smile, head leaning in |
| `first-flex-curiosity` | Eyes down on her own body (arm, hand, shoulder), one brow raised, lips parted around a half-formed question, head tilted toward the flexing limb |
| `smug-satisfaction` | Eyes nearly closed in contentment, one corner of the mouth raised higher than the other *(same row as the posing-guide table — kept identical to avoid drift)* |
| `earned-tired-pride` | Soft closed-mouth smile, sweat-damp brow relaxed, eyes half-lidded but warm, chin level, chest still heaving slightly |
| `contemptuous-amusement` | Half-laugh with one mouth-corner up, brows relaxed, eyes angled DOWN at the beaten opponent, slight head shake |
| `quiet-exultation` | Eyes closed, chin tipped up, slow exhale through a faint smile, brows smooth, shoulders dropping |
| `pain-with-resolve` | Brow knotted, teeth gritted, one eye more closed than the other, chin up |
| `disbelief` | Brows pulled up in the middle, eyes wide but unfocused, mouth half-open with no words coming, slight head shake |
| `barely-suppressed-rage` | Jaw clenched and rippling, lips pressed white-thin, brows lowered hard, eyes burning and locked on the victor, nostrils flared |
| `quiet-acceptance` | Face slack and calm, eyes steady and level, brows neutral, mouth a soft closed line, slow blink |
| `skeptical` | One brow raised high with the other lowered, head tilted, lips pressed with one corner tucked, eyes steady on the speaker |
| `contemptuous` | Eyes sliding off the speaker, faint sneer at one lip corner, chin raised, brows flat |
| `urgent` | Leaning in, eyes wide and locked, brows raised and drawn together in the middle, mouth open mid-word |
| `coldly-assessing` | Level unblinking gaze, brows flat, lips neutral, head perfectly still while only the eyes track |
| `soft` | Eyes half-lidded and warm, brows gently raised in the middle, small closed smile, head tilted toward the other |
| `vulnerable` | Eyes wide and searching the other's face, brows knit upward in the middle, lips parted uncertainly, chin slightly dropped |
| `tender` | Gaze steady on the other's eyes, soft full smile, brows relaxed, head inclined until foreheads nearly touch |
| `open` | Full face turned to the other with nothing guarded — brows up, eyes bright and direct, unforced smile, shoulders squared to them |

---

## Per-register prompt fragments

Drop-in fragments for the staging/prompt layer, in the `multi-character-variation.md`
style. Replace bracketed names; keep the equal-tier line whenever peers share the frame.

**showcase** — use the three full prompts in `posing-and-expressions.md` verbatim as
the base; they ARE this register's fragments.

**celebratory**
```
The group erupts in shared victory — same emotional key, different notes. [A] throws
both hands up mid-cheer; [B] is caught mid-leap; [C] flings her arms wide; [D] laughs
with her shoulders thrown back. No two faces share an expression. Equal size and
transformation tier across all of them — the energy varies, the scale does not.
```

**confrontation**
```
The two sides square off with asymmetric energy — nobody mirrors. [A] leans forward
aggressive, jaw set and lips pressed thin; [B] coils with her guard up, eyes narrowed
to slits; [C] hangs her weight back, reading the room with a cold, level gaze. Equal
size and tier on both sides — menace comes from intent angles, never from one figure
being drawn bigger.
```

**mid-action**
```
Frozen mid-exchange, every figure at a DIFFERENT instant of the action: [A] mid-strike
with teeth gritted and bared; [B] mid-dodge, eyes locked and unblinking; [C] mid-recover,
face twisted in an asymmetric grimace. Motion reads through diagonals and weight, not
speed lines. Equal tier — impact varies by pose, not size.
```

**surprise-reveal**
```
The same instant hits each witness differently: [A] recoils a full step, eyes at
maximum width, mouth dropped open; [B] leans IN, wide-eyed and shining with fascinated
awe; [C] is arrested mid-motion, brows rising asymmetrically as the realization lands.
The revealed subject holds the focal point; every witness's eyeline converges on it.
```

**aftermath-victory**
```
The fight is over and won. [A] stands hand-on-hip with a smug half-smile; [B] plants a
foot on the debris, chin tipped up in quiet exultation; [C] crosses her arms with an
earned, tired smile, chest still heaving slightly. Relaxed weight, dropped shoulders —
the tension has left every body, pride hasn't.
```

**aftermath-defeat**
```
The losing side, each processing it differently: [A] slumped against the wall, jaw
clenched and eyes burning with suppressed rage; [B] pushes up from one knee, brow
knotted, teeth gritted, chin defiantly up; [C] stares at nothing, brows pulled up in
the middle, mouth half-open in disbelief. Nobody theatrical — the drama is in how each
body carries the loss.
```

**dialogue-tense**
```
Words as weapons. [A] leans forward engaged, mouth open mid-word, urgent; [B] answers
with crossed arms and one raised brow, openly skeptical; [C] lounges against the wall
in casual threat, eyes coldly tracking. Nobody neutral, nobody matching — three
different postures of the same standoff.
```

**intimate**
```
Guard fully down. [A] turns her whole body open toward [B], eyes warm and half-lidded;
[B] reaches a hand toward her, brows knit upward, lips parted and uncertain. Close
proximity, shared weight, soft mechanical faces from the register — no flexing, no
display posing, no camera-awareness.
```

---

## Staging-stanza contract (and the proposed D15 gate)

In the compose-gated flow (`qa/compose.py` projects), each character's stanza in
`qa/staging/<panel_id>.json` gains two keys on multi-character panels (alongside the
top-level `staging_type` that the L34/D14 gate already requires):

```json
{
  "staging_type": "tension-block",
  "vera":  {"position": "…", "register_pose": "predatory-step-in",
            "pose": "predatory-step-in: …prose elaboration…",
            "register_emotion": "contemptuous-smirk",
            "expression": "one mouth-corner raised, eyes half-lidded and steady, head tilted"},
  "spatial_rules": ["…"], "lighting": "…"
}
```

- `register_pose` / `register_emotion` — exact labels from this doc's menus.
- `pose` prose opens with the label, then elaborates in body terms.
- `expression` prose is the mechanical face description (table above), not the label.

**D15 (PROPOSED — `docs/proposals/d15-expression-register-gate.diff`, not yet applied):**
- HARD: multi-character panel missing `panel_situation` in the shotlist.
- HARD: `register_pose` / `register_emotion` missing or outside the situation's register.
- HARD: two characters sharing the same pose+emotion pair.
- SOFT: more than 3 multi-character `showcase`/`celebratory` panels in a chapter
  (the celebration registers are the AI-comic tell when overused — warn, don't refuse).

Applying a gate diff is a user-only act (Layer 8): the user reviews, applies, and
re-blesses at the next gate review. Until then, the register system binds through
authoring discipline and this doc; the gate is the backstop, not the rule.

---

## Seams with the neighboring rules

- **L34 / `staging-and-composition.md` places the bodies in space; L39 governs what
  each body and face is doing there.** Companion layers on the same staging stanza — a
  confrontation beat typically pairs `staging_type: tension-block` (L34/D14) with the
  `confrontation` register (L39/D15).
- **L35 growth-intensity owns the face on growth beats.** When a panel carries an
  active growth beat, L35's peak-intensity directive governs the grower's face;
  `panel_situation` still governs the WITNESSES' varied reactions and everyone's poses.
  The `mid-action` and `surprise-reveal` emotion menus are deliberately
  L35-compatible (strain, awe, shock).
- **L37 body-orientation variety composes freely** — any register pose can be rendered
  from front / 3q / profile / rear; rotate orientations across the panel per L37.
- **`multi-character-variation.md` is the backbone this doc bounds.** Its checklist
  grid, pose library, and QA checks all still apply; the register narrows which grid
  values are legal for the beat. Its "POSE VARIATION RULES" block stays mandatory in
  multi-character prompts.
- **`posing-and-expressions.md` is unchanged and canonical for `showcase`.** This doc
  extends it; it does not amend it.

---

## Worked examples (dry-run validated 2026-08-10)

Three staging stanzas walked against the registers — the L39 authoring shapes to copy.

### 1. `confrontation` — Vera faces two rivals (3 characters, all tier 6)

```json
{
  "staging_type": "tension-block",
  "vera": {"position": "foreground left third, closest to camera",
           "register_pose": "predatory-step-in", "register_emotion": "contemptuous-smirk",
           "pose": "predatory-step-in: mid-stride toward the pair, weight rolling onto the lead foot, shoulders squared to them",
           "expression": "one mouth-corner raised, eyes half-lidded and steady, head tilted"},
  "rook": {"position": "midground right, angled 3q toward Vera",
           "register_pose": "guard-up-coiled", "register_emotion": "locked-jaw-determination",
           "pose": "guard-up-coiled: fists raised loose, elbows in, knees bent, weight on the balls of her feet",
           "expression": "jaw set, lips pressed thin, eyes narrowed, brow slightly lowered"},
  "tess": {"position": "deep background right, half-shadowed by the doorway",
           "register_pose": "weight-back-assessing", "register_emotion": "cold-clinical-assessment",
           "pose": "weight-back-assessing: hips settled onto the back leg, arms loose, making no move yet",
           "expression": "face still, eyes tracking slowly over Vera, brows level, lips barely pursed"},
  "spatial_rules": ["all three at tier 6 — identical scale language, no size hierarchy",
                    "intent diagonals converge on the space between Vera and Rook"],
  "lighting": "hard single overhead, long shadows"
}
```
**Why it reads:** three different threat-postures and three different hostile faces, all
inside one register — the panel is unmistakably a face-off, and no two characters play
it the same way. Aggressor/defender/observer hierarchy comes from pose and L34 depth,
not from anyone being drawn bigger.

### 2. `surprise-reveal` — Vera's first flex, two witnesses (3 characters)

```json
{
  "staging_type": "depth-staged",
  "vera": {"position": "center midground, dominant scale (the depth-staged lead)",
           "register_pose": "arrested-mid-motion", "register_emotion": "first-flex-curiosity",
           "pose": "arrested-mid-motion: frozen halfway through raising her arm, the flex catching even her off guard",
           "expression": "eyes down on her own arm, one brow raised, lips parted around a half-formed question"},
  "tess": {"position": "midground left, a full step back from her original mark",
           "register_pose": "recoil-step-back", "register_emotion": "wide-eyed-shock",
           "pose": "recoil-step-back: rear foot landing the step away, hands half-risen, torso pulling back",
           "expression": "eyes at maximum width showing white, brows at the hairline, mouth dropped fully open"},
  "mara": {"position": "foreground right edge, partially cropped (FG witness)",
           "register_pose": "lean-in-fascination", "register_emotion": "fascinated-awe",
           "pose": "lean-in-fascination: bent toward Vera from the waist, hand braced on the bench",
           "expression": "eyes wide and shining fixed on the arm, brows high but soft, mouth open in a slack half-smile"},
  "spatial_rules": ["both witnesses' eyelines converge on Vera's flexed arm",
                    "witnesses at identical tier — reaction varies, scale does not"],
  "lighting": "warm gym practicals, face-forward key on Vera"
}
```
**Why it reads:** one event, three legible and DIFFERENT responses — shock, awe, and
the grower's own curiosity — all from the reveal register. On a growth beat, L35's
intensity directive would take over Vera's face; here (pre-growth flex) the register
carries it.

### 3. `aftermath-defeat` — the beaten pair (2 characters)

```json
{
  "staging_type": "depth-staged",
  "rook": {"position": "foreground left, slumped at the base of the cracked wall",
           "register_pose": "slumped-against-wall", "register_emotion": "barely-suppressed-rage",
           "pose": "slumped-against-wall: legs folded under her, one shoulder propping her against the masonry",
           "expression": "jaw clenched and rippling, lips pressed white-thin, brows lowered hard, eyes burning off-frame toward the victor"},
  "tess": {"position": "deep midground right, pushing up from the rubble at smaller perspective scale",
           "register_pose": "one-knee-recovering", "register_emotion": "pain-with-resolve",
           "pose": "one-knee-recovering: one knee down, forearm braced across the raised thigh, head coming up first",
           "expression": "brow knotted, teeth gritted, one eye more closed than the other, chin up"},
  "spatial_rules": ["no theatrical posing — collapsed and rising weight only",
                    "both at the same tier they fought at; defeat shows in posture, never in size"],
  "lighting": "dust-hazed backlight, low contrast"
}
```
**Why it reads:** defeat with two distinct temperatures — rage held in and pain pushed
through — nobody wearing a showcase face at the bottom of a loss. The defiant chin-up
line keeps the losers characterful instead of pathetic.

**Negative case (what D15 catches):** give Rook `register_emotion: "ecstatic-joy"` in
example 1 and the gate refuses — `ecstatic-joy` is not in the `confrontation` register.
That is the exact leak (showcase emotion on a face-off beat) this system exists to stop.
