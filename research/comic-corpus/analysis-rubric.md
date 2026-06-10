# Comic Corpus — Analysis Rubric v1.0

**This is a CANONICAL rubric. Pass it to analysis agents VERBATIM — never paraphrase.**
Per `feedback_dont_paraphrase_canonical_rubrics.md`. Bump `rubric_version` on any change so re-runs stay comparable.

The corpus exists to learn what makes a female-muscle-growth (FMG) comic *work*, so the pipeline can reproduce the good elements and avoid the flat defaults. This rubric scores every page and panel of a comic on the four axes the production pipeline most often fumbles, plus story structure. Output is BOTH machine-readable (`beats.json`) and human-readable (`notes.md`).

These are amateur/indie comics. **Nobody gets everything right.** The job is to separate the elements that work from the ones that fumble — score honestly, cherry-pick the wins.

---

## How to analyze a comic

1. Read EVERY page in order (`pages/page-01...page-NN`). Do not sample — the growth-page ratio requires a complete count.
2. For each page: identify its **role**, **growth_state**, segment it into **panels**, and score each panel on the axes below.
3. Group pages into **scenes**, flagging every transformation/growth scene with its escalation devices.
4. Write `beats.json` (schema below) and `notes.md` (template below) into the comic's corpus folder.
5. Be concrete and cite page/panel numbers in notes. "Page 13 panel 2" not "later on."

---

## AXIS 1 — Growth density  *(the niche axis — weight this highest)*

This is an FMG comic. Growth IS the product. The single most-cited community metric is the **growth-page ratio**: how many pages are actively about muscle growth / transformation, relative to total pages.

Per page, set **`growth_state`**:
- `none` — no growth content (setup, dialogue, action, aftermath with no active change)
- `trigger` — the catalyst moment (drinks the potion, reads the book, the spark)
- `early` — growth beginning, subtle changes
- `mid` — visible active growth, clear escalation
- `peak` — maximum/climactic growth, the money pages
- `aftermath` — growth done, showing off / reacting to the new body

Per page, set **`role`** (story function): `cover | setup | buildup | active-growth | aftermath | action | dialogue | denouement | cliffhanger`.

A page counts toward the **growth-page ratio** if `growth_state` ∈ {trigger, early, mid, peak} OR `role == active-growth`.

For each growth SCENE (in `scene_breakdown`), record **`escalation_devices`** — the creative techniques used. Catalog every one you see:
- `multi-panel-progressive` — same body part across N panels, growing stage→stage→stage (the gold-standard device the user specifically wants more of)
- `clothing-destruction` — garments straining, tearing, bursting as growth proceeds
- `zoom-escalation` — camera pushes in tighter as growth intensifies
- `size-comparison` — growth shown against a fixed reference (doorway, other person, prior panel)
- `slow-burn` — growth spread across many pages vs one-and-done
- `reaction-intercut` — cutting to face/onlooker reactions between growth beats
- `sfx-driven` — sound effects (KREEEEK, RIIIP) carrying the growth sensation
- `full-body-reveal` — splash/wide showing the complete transformed result

Per panel, set:
- **`growth_focus`** (bool) — is this panel a zoomed-in growth money-shot (a body part actively growing/flexing in detail)?
- **`body_part_focus`** — what the panel centers: `arms | back | chest | shoulders | abs | legs | glutes | full | face | none`

**Score `growth_density_score` (0–5) for the whole comic:**
- 0 — growth is an afterthought; <10% of pages
- 2 — growth present but rushed; one-and-done transformation, no zoom coverage
- 3 — solid growth presence, ~25–35% of pages, some zoom
- 4 — growth-forward, long scenes, good zoom coverage, ≥2 escalation devices
- 5 — growth is the spine; long multi-page transformation, heavy ECU coverage, progressive multi-panel devices, ≥4 escalation devices

---

## AXIS 2 — Camera dynamism  *(the flatness axis)*

The pipeline's #1 visual failure is FLAT panels: level eyelines, characters on the same plane at the same size, every panel a mid-shot. The user's directive: **bias hard toward dynamic — better too much than too little.** Score what THIS comic does so we can match its wins.

Per panel, set **`shot_distance`** (the distance taxonomy):
- `EWS` — extreme wide / establishing (environment dominates, figures small)
- `WS` — wide (full body + surroundings)
- `MLS` — medium-long (knees up)
- `MS` — medium (waist up)
- `MCU` — medium close-up (chest up)
- `CU` — close-up (head & shoulders / single body part)
- `ECU` — extreme close-up (eyes, or a body-part detail filling frame)

Per panel, set **`angle`**: `eye | low | high | dutch | OTS | aerial | worm | bird | pov`.

Per panel, set **`staging`** (array — the composition devices; this is the user's ✓/✗ storyboard lesson encoded):
- `flat-level` — ✗ THE FAILURE MODE: level horizontal eyeline, figures same plane & same size, static. (The red-X panels.)
- `diagonal` — ✓ raked tension axis; confrontation/energy staged on a diagonal (the boxers ✓)
- `depth-fg-bg` — ✓ strong foreground/background separation, perspective convergence (the doorway ✓)
- `scale-contrast` — ✓ deliberately varied figure sizes in frame, e.g. big-FG-head + smaller others (the trio ✓)
- `OTS` — over-the-shoulder framing
- `foreshortening` — a limb/fist/body thrust toward camera
- `dutch` — canted horizon for unease/energy
- `low-hero` — low angle making the subject tower (power)
- `high-vuln` — high angle making the subject small (vulnerability)

**Derived per page (the agent reports these in `page_notes`, stats script recomputes):**
- distance_spread — count of DISTINCT shot_distances on the page (1 = monotonous, 3+ = dynamic)
- flat_panel_count — panels whose staging includes `flat-level` and nothing dynamic

**Score `camera_dynamism_score` (0–5) for the whole comic:**
- 0 — nearly every panel flat-level mid-shots, one distance band
- 2 — some variety but defaults to flat; rare angles
- 3 — decent distance spread, occasional diagonal/depth
- 4 — consistently varied distance, frequent dynamic staging, real angle variety
- 5 — every page reads cinematically: wide distance spread, diagonals/depth/scale-contrast throughout, bold angles

---

## AXIS 3 — Expression intensity  *(the dead-face axis)*

Like actors in an action movie: a character's face must register the stress/intensity of the moment. A plain face makes the *reader* feel nothing. Score whether faces carry the beat.

Per panel (when a face is visible), set:
- **`expression`** — the named emotion: `strain | effort | shock | awe | ecstasy | fear | panic | rage | smug | joy | determination | pain | shyness | neutral` (or another precise word). Use `neutral` ONLY for genuinely blank faces.
- **`expression_intensity`** (0–5):
  - 0 — no face visible / not applicable (record null)
  - 1 — plain, dead, emotionless face in a context that should carry emotion (THE FAILURE)
  - 2 — mild, underplayed
  - 3 — clear, readable emotion appropriate to the beat
  - 4 — strong, expressive, sells the moment
  - 5 — peak intensity (mid-growth ecstasy/strain, climactic shock)

**Pay special attention to transformation panels** — growth beats demand high-intensity faces (strain, ecstasy, awe). A peak-growth panel with a neutral face is a defect worth calling out.

**Score `expression_intensity_score` (0–5)** for the whole comic — the degree to which faces consistently carry the emotional register of their beats.

---

## AXIS 4 — Story & structure  *(the engagement axis)*

Per the whole comic, assess in `notes.md`:
- **Hook** — how fast does it grab? What's the page-1 promise?
- **Pacing** — setup vs growth vs payoff balance. Where does it drag? Where does it rush?
- **Tease vs payoff** — does it build anticipation before delivering, or dump everything at once? (Directly relevant to the edging/never-pays-off structure of the redhead-houseguest project — note how this comic handles delay vs release.)
- **Cliffhanger / continuity** — does it end on a pull-forward?
- **Dialogue & SFX** — how is lettering used? Do SFX carry sensation?
- **Clarity** — is the sequence of events legible panel-to-panel?

Record `narrative_arc` as a one-line beat string, e.g. `"ordinary girls → find book → one reads it → painful transformation → emerges as muscle hero → flies off (to be continued)"`.

---

## What this comic does WELL vs FUMBLES  *(the cherry-pick)*

In `notes.md`, two explicit lists:
- **`strengths`** — elements worth STEALING for the pipeline (concrete, cite pages). e.g. "P13's KREEEEK→CRASSHH SFX escalation sells the growth sensation without any dialogue."
- **`weaknesses`** — elements to AVOID / where it fumbles (concrete, cite pages). e.g. "P6–8 are three near-identical flat-level mid-shots; the conversation has no camera movement."

Be a discerning critic, not a fan. The corpus is only useful if it tells the truth.

---

## Popularity / signal

If the page or source provides engagement data (comment count, view count, likes, Patreon tier, ranking), record it in `meta.json` under `popularity`. If none is visible, set `popularity: {"available": false}` — do NOT invent numbers. Popularity is the ground-truth "successful" signal; without it, scores are craft-quality only.

---

## Output 1 — `beats.json` (machine-readable, per comic)

```json
{
  "comic_id": "the-mysterious-book-1-the-opening",
  "rubric_version": "1.0",
  "analyzed_pages": 25,
  "scores": {
    "growth_density_score": 0,
    "camera_dynamism_score": 0,
    "expression_intensity_score": 0,
    "story_structure_score": 0
  },
  "narrative_arc": "one-line beat string",
  "pages": [
    {
      "page": 1,
      "role": "cover",
      "growth_state": "none",
      "panel_count": 1,
      "panels": [
        {
          "n": 1,
          "shot_distance": "MS",
          "angle": "low",
          "staging": ["scale-contrast"],
          "expression": "awe",
          "expression_intensity": 4,
          "growth_focus": false,
          "body_part_focus": "none",
          "sfx": [],
          "notes": "short panel note"
        }
      ],
      "page_notes": "distance_spread=1; flat_panel_count=0; short page summary"
    }
  ],
  "scene_breakdown": [
    {"scene": "transformation-1", "pages": [11,12,13,14], "type": "active-growth", "escalation_devices": ["multi-panel-progressive","clothing-destruction","sfx-driven"]}
  ],
  "strengths": ["concrete, page-cited"],
  "weaknesses": ["concrete, page-cited"]
}
```

## Output 2 — `notes.md` (human-readable, per comic)

```markdown
# <Comic Title> — Analysis (rubric v1.0)

**Source:** <url>  **Creators:** <art / story>  **Pages:** N  **Analyzed:** <date>

## Scores (0–5)
| Axis | Score | One-line justification |
|---|---|---|
| Growth density | X | ... |
| Camera dynamism | X | ... |
| Expression intensity | X | ... |
| Story & structure | X | ... |

## Growth-page accounting
- Growth pages (trigger/early/mid/peak): A / N  →  **growth-page ratio = XX%**
- Transformation scenes: list with page ranges and escalation devices
- Zoom coverage: how much ECU/CU growth-focus

## Camera
- Distance spread across the book; flat-panel hotspots (cite pages)
- Best dynamic compositions to steal (cite pages)

## Expressions
- How faces carry beats; dead-face defects (cite pages)

## Story & structure
- Hook / pacing / tease-vs-payoff / cliffhanger / narrative arc

## Strengths to steal
- ...

## Weaknesses to avoid
- ...
```
