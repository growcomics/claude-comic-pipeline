# Cinematography — camera & lighting for photoreal DAZ3D comics

*Hollywood camera-and-lighting craft, translated into prompt language. Every panel
should make a deliberate choice from each of the three axes below: **shot size**,
**camera angle**, and **lighting**. Variety across a page is mandatory — a page of
flat eye-level medium two-shots reads as amateur. `style-lock` should copy the
"Prompt phrasing" lines into each project's `style.md`; `script-breakdown` should
set `size`, `camera`, and a `lighting` note on every panel using these rules.*

---

## 1. Shot size — distance dictates emotion

| Shot | What it shows | Use it for |
|---|---|---|
| **Establishing / wide** | Whole space + figures small | Open a scene, show geography, group dynamics, scale gags |
| **Full** | Head-to-toe, one+ figures | Posing, full-body action, costume reveals, power stances |
| **Cowboy** (mid-thigh up) | Stance + gesture | Confident attitude, a flex that still shows the torso |
| **Medium** (waist up) | Body language + face | Dialogue, reactions, two-shots |
| **MCU** (chest up) | Face + a little body | Emotional dialogue, the line that lands |
| **CU** (head/face) | Expression only | Peak emotion, decisions, the "tell" |
| **ECU / macro** | One detail fills frame | A transformation beat (a bicep tearing a sleeve), an eye, the bottle |

**Rules of thumb:** open wide, then push in as tension rises; cut OUT to wide to
release it. A **transformation beat** (`transformation_beat` set) is *always* an
ECU/macro where the region fills 70%+ and head/feet crop out (this is L20). Give
every page at least one solo CU/ECU — don't shoot the whole page in two-shots.

## 2. Camera angle — height & tilt carry power

- **Eye-level** — neutral, honest. The default; use for ordinary dialogue.
- **Low angle (looking up)** — POWER, dominance, awe. Subject towers, looks heroic/
  intimidating. Use for the flex, the reveal, the "now you're in trouble" beat.
- **High angle (looking down)** — vulnerability, smallness, defeat. Use for the one
  who's nervous, shrinking, or about to lose.
- **Worm's-eye / hero low** — extreme low, near the floor — maximum monumentality for
  a splash/finale power pose.
- **Bird's-eye / top-down** — pattern, geometry, the whole game board — great for the
  circle-of-players / the spinning bottle.
- **Dutch tilt (canted)** — unease, chaos, a wild turn. Use sparingly for a big surge
  or a "wait, it landed on ME" jolt.
- **Over-the-shoulder (OTS)** — anchors a two-person exchange; foreground shoulder
  gives depth. **POV** — puts the reader in the scene.

**Pair angle with the beat:** dominance → low; defeat/nervous → high; reveal/finale →
hero-low; the game board → top-down; the shock → dutch.

## 3. Lighting — the Hollywood toolkit

Light is shape, mood, and separation. Name the setup in the prompt; don't leave it to
chance (flat front-on flash is the #1 amateur tell).

**Three-point (the workhorse):**
- **Key** — the main, directional light. Its *angle* (45° front-side, high) and
  *hardness* set the mood. Hard key = drama/edges; soft key = beauty/flattering.
- **Fill** — softer, opposite the key, lifts the shadows. A **high key-to-fill ratio**
  (little fill) = moody, contrasty, "low-key." Low ratio (lots of fill) = bright,
  friendly, "high-key."
- **Back / rim / kicker** — behind the subject, rakes the edges, draws a bright halo
  that **separates** them from the background. Essential for muscle: a rim along a
  flexed arm makes the form read. This is the most-skipped, most-valuable light.

**Beyond three-point:**
- **Bounce light** — soft, motivated fill from a nearby surface (a wall, the floor);
  natural, wrapping, gentle on skin. Use for warm, cozy, group scenes.
- **Motivated / practical** — light that comes from something *in* the frame (a lamp,
  a window, fairy lights, a glowing magic aura). Always say where the light is from —
  it grounds the photoreal CGI.
- **Low-key / chiaroscuro** — mostly shadow, a single hard key + strong rim. Tension,
  power, "the surge." **High-key** — bright, even, few shadows. Comedy, lightness, the
  fun group beats.
- **Color contrast** — warm key + cool rim (or vice-versa) adds depth and a filmic look.
  Keep a character's *identity* colors (e.g. a magic aura) constant; vary the ambient.

**Muscle/transformation lighting:** hard side or back rim light to carve definition;
low fill so shadows model the muscle; a kicker on the tearing fabric. Sweat sheen is
NOT wanted unless the project says so (keep skin healthy-matte).

## 4. Prompt phrasing (copy these into panels / style.md)

- Camera: `"[SIZE] shot, [ANGLE], [LENS]"` — e.g. `"low-angle hero full shot, 35mm,
  subject towering"`, `"top-down wide of the circle, 24mm"`, `"macro ECU of the bicep,
  100mm, region fills frame"`.
- Lighting: `"[KEY] key + [FILL] fill + [BACK] rim, [PRACTICAL], [MOOD]"` — e.g.
  `"hard warm key from the left, low fill, strong cool rim separating her from the
  dark room, fairy-light practicals, low-key dramatic"`, or `"soft bounced daylight
  key, high fill, gentle rim, bright high-key, cozy"`.
- Always end with the project STYLE-LOCK (DAZ3D Iray photoreal) and negative
  (`flat front-on flash lighting, painterly, cel-shaded` …).

## 5. Page-level discipline (the checklist)

1. No two adjacent panels share the same shot size AND angle.
2. Every page has ≥1 wide (geography) and ≥1 CU/ECU (emotion or beat).
3. Power beats → low angle + rim light. Nervous/loss beats → high angle + soft flat.
4. Transformation beats → ECU/macro + hard rim carving the muscle.
5. Name a light source every panel; never "flat front-on flash."
