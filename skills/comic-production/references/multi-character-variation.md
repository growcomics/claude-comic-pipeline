# Pose Variation & Anti-Uniformity Guide

## The #1 Rule: No Two Characters Do the Same Thing

AI image generators default to **uniformity**. Given a prompt with multiple characters, the model will make them all face the same direction, strike the same pose, hold the same expression, and stand at the same height. This looks robotic, staged, and dead on the page.

**Good comic art** gives every character in every panel a unique body position, gesture, angle, and expression — even when they're doing the same activity. This is what separates a real comic page from an AI lineup.

---

## What "Uniform" Looks Like (The Problem)

These are the failure modes the model produces when you don't explicitly fight uniformity:

| Failure | What the model does | Why it kills the panel |
|---|---|---|
| **Mirror posing** | All characters in the same flexing pose, same arm angles | Looks like a copy-paste, not a group of individuals |
| **Synchronized action** | All characters drinking/eating/walking in identical timing | Feels like a dance routine, not natural behavior |
| **Lineup formation** | Characters standing in a row, evenly spaced, all facing camera | Static, no depth, no story — a police lineup |
| **Same body angle** | Everyone at 0° or 45° to camera, same torso rotation | Flat composition, no visual variety |
| **Identical expressions** | All smiling, all shocked, all angry — same face on every character | Removes individuality, makes characters feel interchangeable |
| **Same eye direction** | Everyone looking at the same spot | Removes tension and interpersonal dynamics |
| **Uniform height/stance** | All characters standing straight, same posture | No personality — slouchers, leaners, and fidgeters make groups feel alive |

---

## What "Varied" Looks Like (The Goal)

In a well-composed multi-character panel, **every single character** has:

- A **different body angle** relative to the camera (one facing left, one turned 3/4 away, one looking over their shoulder)
- A **different arm/hand position** (one flexing, one on hip, one pointing, one holding something, one crossed arms)
- A **different leg stance** (one wide, one crossed, one stepping forward, one knee bent)
- A **different facial expression** (one grinning, one smirking, one shocked, one determined)
- A **different eye direction** (one looking at another character, one looking at their own body, one looking off-panel)
- A **different head tilt/angle** (chin up, chin down, tilted left, turned right)
- A **different vertical position** in the frame when possible (one crouching, one standing tall, one leaning on something)

The key insight: **even characters doing the same activity look different doing it.** Four people drinking from bottles don't all tilt their heads back at the same angle with the same hand. One chugs, one sips cautiously, one holds the bottle away examining it, one has already finished and is wiping her mouth.

---

## Prompt Engineering for Pose Variation

### The Character-by-Character Method

**Never describe characters as a group.** Always describe each character individually with their own unique action, pose, and expression. The model treats group descriptions as instructions to make everyone identical.

**BAD (produces uniformity):**
```
Four athletes in the locker room drinking glowing green bottles, all wearing Strongwoods JV uniforms.
```

**GOOD (produces variety):**
```
Four athletes in the locker room, each wearing Strongwoods JV uniforms:

CHARACTER 1 (blonde, far left): Standing with her back partially turned to camera, looking over her right shoulder at the others. Left hand holds the green bottle at waist level, hasn't opened it yet. Expression: one eyebrow raised skeptically, lips pressed together, head tilted slightly.

CHARACTER 2 (brunette, center-left): Sitting on the bench with one leg up, chugging from the bottle with her head tilted far back. Free hand grips the edge of the bench. Expression: eyes squeezed shut, throat exposed, fully committed to drinking.

CHARACTER 3 (black hair, center-right): Standing facing camera but looking down at the bottle in both hands, holding it up to read the label. Hasn't drunk yet. Expression: brow furrowed, mouth slightly open, nose wrinkled — suspicious.

CHARACTER 4 (redhead, far right): Leaning against the lockers with one shoulder, bottle already empty and dangling from two fingers at her side. Free hand on her stomach. Expression: satisfied closed-mouth smile, eyes half-lidded, chin slightly raised.
```

### The Pose Assignment Checklist

Before writing any multi-character panel prompt, fill in this grid. **No two characters can share the same value in any column:**

| Character | Body angle | Arms | Legs | Expression | Looking at | Head position |
|---|---|---|---|---|---|---|
| Char 1 | ? | ? | ? | ? | ? | ? |
| Char 2 | ? | ? | ? | ? | ? | ? |
| Char 3 | ? | ? | ? | ? | ? | ? |
| Char 4 | ? | ? | ? | ? | ? | ? |

---

## Pose Library (Mix and Match)

### Body Angles (pick a different one per character)
- Facing camera straight on (0°)
- Three-quarter view facing left (45° left)
- Three-quarter view facing right (45° right)
- Profile view (90°, facing left or right)
- Back turned, looking over shoulder
- Angled away, torso twisted back toward camera
- Leaning forward toward camera
- Leaning back away from camera

### Arm Positions (pick a different one per character)
- Double bicep flex (classic)
- Single arm flex, other arm on hip
- Arms crossed over chest
- One hand on hip, other hanging
- Both hands raised overhead in triumph
- Pointing at something/someone
- Holding an object (bottle, equipment, phone)
- One arm behind head, stretching
- Hands clasped in front
- Fists clenched at sides
- Examining own forearm/bicep
- Reaching toward another character
- Hand on another character's shoulder
- Thumbs hooked in waistband/pockets

### Leg Stances (pick a different one per character)
- Wide power stance
- Weight shifted to one leg, other relaxed
- One foot forward, walking pose
- Legs crossed at ankles
- One knee slightly bent
- Sitting on bench/chair/ledge
- Crouching or squatting
- One foot up on a bench or step
- Standing on tiptoes
- Kneeling on one knee

### Head & Gaze Directions (pick a different one per character)
- Looking directly at another specific character
- Looking down at own body (admiring, shocked, confused)
- Looking off-panel to the left or right
- Chin raised, looking down at someone shorter
- Chin tucked, looking up through eyebrows
- Head thrown back (laughing, drinking, in ecstasy)
- Head tilted to one side
- Turned to whisper to the character next to them

---

## Special Scenarios

### Group Flexing Scene
Even when everyone is flexing, **vary the flex type**:
- Character A: front double bicep, legs wide, leaning forward
- Character B: side chest pose, turned 90°, one arm across body
- Character C: back lat spread, turned away from camera, looking over shoulder
- Character D: most muscular (crab pose), crouched slightly, face scrunched with effort

**Never let two characters do the same flex in the same panel.**

### Transformation / Growth Scene (Multiple Characters Growing Simultaneously)
Each character should be at a **different stage or reacting differently**:
- Character A: mid-growth, arching back, arms flared out
- Character B: just starting, looking down at her arms with wide eyes
- Character C: finished growing, casually flexing and admiring the result
- Character D: hasn't started yet, watching the others with shock

### Confrontation / Face-Off Scene
The two sides should have **asymmetric energy**:
- One side: aggressive forward lean, fists clenched, stepping forward
- Other side: defensive, arms at sides or crossed, standing ground, leaning back slightly
- **Never mirror the two sides** — the whole tension comes from the asymmetry

### Locker Room / Casual Group Scene
Maximum variety in **posture and activity**:
- One character sitting, legs stretched out
- One character standing, leaning on a locker
- One character mid-action (tying shoes, pulling on a shirt, toweling off)
- One character talking, hands gesturing
- Scatter them at **different depths** in the space — not all on the same plane

---

## Mandatory Prompt Language

Add this block to the mandatory rules section of **every multi-character panel**:

```
POSE VARIATION RULES (MANDATORY):
- Every character in this panel MUST have a unique, distinct pose — no two characters may share the same arm position, body angle, leg stance, or facial expression.
- Characters must NOT stand in a symmetrical lineup or mirror each other's poses.
- Each character's body must be angled differently relative to the camera.
- Each character must be looking in a different direction or at a different target.
- Each character must have a unique facial expression described mechanically (brow angle, mouth shape, eye width, head tilt).
- If characters are performing the same action (e.g., drinking, flexing), each must be at a different stage or doing it in a visually distinct way.
```

---

## QA Checklist: Pose Variation

After every multi-character panel generates, check:

- [ ] Can you tell the characters apart by pose alone (silhouette test)?
- [ ] Are any two characters in the same arm position? → **REJECT, re-prompt**
- [ ] Are any two characters at the same body angle? → **REJECT, re-prompt**
- [ ] Are all characters in a straight line at the same depth? → **REJECT, re-prompt**
- [ ] Are all characters the same height in frame (no sitting, leaning, crouching)? → **Consider re-prompting**
- [ ] Do all characters have the same facial expression? → **REJECT, re-prompt**
- [ ] Does the panel feel like a "police lineup"? → **REJECT, re-prompt**

If a panel fails any of these checks, **do not accept it.** Revise the prompt to be more specific about each character's unique pose and regenerate.

---

## Quick Reference: Anti-Uniformity Prompt Fragments

Copy-paste these into prompts when you need to break specific uniformity patterns:

**Anti-lineup:**
```
Characters are scattered naturally throughout the space at different depths — NOT standing in a row. Some are closer to camera, some further back.
```

**Anti-mirror:**
```
No two characters mirror each other's body position. Each character's torso is rotated to a different angle relative to the camera.
```

**Anti-sync:**
```
Each character is at a different moment in the action — one just starting, one mid-action, one finishing, one hasn't begun yet.
```

**Anti-expression-clone:**
```
Every character has a distinctly different emotional reaction to this moment. No two faces show the same emotion or the same mechanical expression.
```
