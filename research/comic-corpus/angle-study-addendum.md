# Angle & Pose Study — Rubric Addendum v1.0

**This is a CANONICAL addendum. Pass it to analysis agents VERBATIM alongside `analysis-rubric.md`.**
It extends the rubric's AXIS 2 (camera dynamism) with the fields needed to turn a hand-drawn
artist's staging into reusable camera/pose instructions for the 3D-CGI pipeline. It never
replaces the rubric: the agent still writes `beats.json` + `notes.md` per the rubric, and
ADDITIONALLY writes `angle-study.json` per this addendum.

Why it exists: the pipeline's #1 visual failure is flat, same-distance, level-eyeline panels.
Studying how a strong hand artist *stages the body* (which limb comes at the lens, where the
camera sits, how the frame crops the figure, which muscle the composition is built to sell)
gives us a vocabulary we can append to generation prompts. The artist's drawing style is NOT
studied and must NOT leak into the output: panels are rendered as photoreal 3D CGI. Extract
staging, never style.

## Content-safety rule

Some source pages are explicit. The study is about composition ONLY. Tag the camera, pose,
crop, and muscle emphasis; do not describe sexual content. If a panel is explicit, set
`"explicit": true`, tag it structurally, and keep `notes` to the staging.

## Per-panel fields  (`angle-study.json` → `pages[].panels[]`, keyed by the same `page` / `n` as `beats.json`)

- **`pose`** — one short line naming the body pose in plain words, e.g. `"front double-bicep, elbows above shoulder line, chin down"`.
- **`pose_family`** — `flex-display | action-strike | lift-carry | stance-power | walk-stride | recline | crouch-coil | reach-grab | struggle-restraint | growth-writhe | everyday-idle | other`
- **`muscle_sold`** — the muscle group the composition is *built* to sell (not just visible): `arms | shoulders | traps-neck | back | chest | abs | glutes | legs | calves | full-silhouette | none`
- **`sell_mechanism`** — array, the devices doing the selling:
  - `foreshortening` — a limb/mass shortens toward the lens
  - `silhouette` — a clean readable outline against a plain field
  - `overlap` — one mass in front of another to force depth
  - `frame-crop` — the panel edge cuts the body to make a part read huge
  - `scale-contrast` — a fixed reference (person, doorway, prop) sets the size
  - `rim-light` — edge light carving the muscle
  - `cloth-strain` — fabric tension outlining the mass
  - `contact-deform` — a surface/prop/other body deforms under the muscle
  - `motion-line` — speed/burst lines
  - `tangent-break` — the figure breaks the panel border
  - `other`
- **`toward_camera`** — the body part thrust nearest the lens: `none | fist | forearm | elbow | shoulder | chest | back | glute | thigh | knee | foot | face | hand-open`
- **`body_line`** — `straight | s-curve | c-curve | twist-contrapposto | diagonal-lean | coil-crouch | arch-back | x-spread`
- **`crop`** — how the frame cuts the figure: `full | head-to-thigh | waist-up | chest-up | body-part-only | head-cut-off | feet-cut | bleed`
- **`camera_height`** — camera relative to the subject: `below-knee | knee | hip | chest | eye | above-head | top-down`
- **`lens_feel`** — `wide-distorted | normal | long-compressed`
- **`panel_shape`** — `tall | wide | square | inset | bleed | irregular`
- **`figure_scale`** — share of the panel the main figure fills: `"<25" | "25-50" | "50-75" | ">75"`
- **`onlooker_in_frame`** — bool, is a reacting second figure staged in the same panel (size-contrast or reaction)
- **`explicit`** — bool
- **`steal_score`** — 0–5, how reusable this exact staging is for a 3D-CGI muscle panel (5 = copy it directly, 0 = nothing to take)
- **`prompt_seed`** — ONE plain-speech sentence that would reproduce this staging in a generation prompt. Rules: describe camera + pose + crop + which muscle it sells. NO appearance (hair, face, outfit, skin), NO size adjectives, NO drawing-style words, NO character names. Example: `"Camera down at knee height looking up, she plants one foot toward the lens, fist on hip, the frame cuts her at the thigh so the shoulders fill the top of the panel."`
- **`notes`** — short, staging only.

## Per-page fields  (`angle-study.json` → `pages[]`)

- **`page`** — page number as printed/filed (use the source page number, not the file index)
- **`layout`** — plain words: grid rhythm, how tall/wide panels alternate, where the big panel sits, bleed usage, inset usage.
- **`reading_flow`** — how the eye is led across the page (diagonals, size steps, gutters).
- **`panels`** — array per above.

## Comic-level fields  (`angle-study.json` top level)

- **`comic_id`**, **`addendum_version`** (`"1.0"`), **`artist`**
- **`signature_moves`** — the 5–8 staging devices this artist returns to most, each with page/panel citations and a one-line "how to steal it for CGI".
- **`angle_histogram`** — counts of `angle` values across all panels (reuse the rubric's `angle` enum).
- **`camera_height_histogram`**, **`toward_camera_histogram`**, **`muscle_sold_histogram`** — counts.
- **`top_steals`** — the 10 highest `steal_score` panels, each `{page, n, steal_score, prompt_seed}`.
- **`avoid`** — staging habits of this artist that do NOT translate to 3D CGI (e.g. impossible anatomy that only works in ink), with citations.

## Method

1. Read EVERY page in order from `pages/small/` (downscaled copies; originals in `pages/` are too large to view). Do not sample.
2. Segment panels exactly as you did for `beats.json` so `page`/`n` line up one-to-one.
3. Tag every panel. A panel with no figure gets `pose_family: other`, `muscle_sold: none`, `steal_score: 0`.
4. Write `prompt_seed` for EVERY panel with `steal_score ≥ 2`. Seeds are the product; be concrete.
5. Fill the comic-level fields last, from the tags, not from memory.
6. Validate that every `page`/`n` pair in `angle-study.json` exists in `beats.json`.
