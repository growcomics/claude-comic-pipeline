# L35 real-render A/B validation — growth money-shot intensity

**Verdict: VALIDATED (both branches), with one calibration note.** The two verbatim L35
directive blocks (`_FACE_INTENSITY`, `_PHYSICAL_MANIFESTATION` in
`rules/l35_growth_intensity.py`) produce a large, consistent, measurable lift in face
intensity and physical growth manifestation over action-only baseline prompts, at zero
cost to style, wardrobe coverage, or framing compliance.

Run 2026-06-09 on **Google Labs Flow** (labs.google/fx/tools/flow, Omni-agent chat UI),
project "L35 Render Validation 2026-06-09" on the growcomics account. 16 real
generations (4 arms × 4 variants), per `feedback_validate_with_credits` (4–8+ gens).
Higgsfield was NOT used (≈1.58 credits left); this validation ran on Flow's free tier.

**Model caveat:** the plan was Nano Banana Pro, but the account's **daily Pro quota was
exhausted** at run time (Flow refused with "You've reached the daily limit for Nano
Banana Pro generations"). The run used **🍌 Nano Banana 2** (Flow's default) for ALL 16
generations — the A/B comparison is internally consistent, and NB2 is the same model
family as the production default `nano_banana_flash`. Re-confirming on
Pro/`nano_banana_pro` when credits/quota allow is optional, not blocking.

## Protocol

Two beats, each as an A/B pair. Arm A = action/camera/lighting prompt only (no
expression or manifestation language). Arm B = the **same prompt verbatim** + the L35
directive block(s) exactly as the rule module emits them (face-visible beats get
`_FACE_INTENSITY` + `_PHYSICAL_MANIFESTATION`; body-region ECUs get
`_PHYSICAL_MANIFESTATION` only, per the L20 branch).

- **Beat 1 — face-visible whole-body growth beat**: muscular athletic woman (tank top +
  leggings, coverage preserved), mid-growth-surge in a commercial gym at night,
  three-quarter dynamic angle with foreshortening (no steep low angle — Flow filter),
  whole body + face in frame.
- **Beat 2 — body-region ECU**: flexed right arm + shoulder mid-growth-surge, head
  fully cropped out, region filling 70%+ of frame, tank-top edge at the shoulder.

Settings: Agent settings → image 16:9, Nano Banana 2, confirm=Never. Each arm's first
image submitted as "Generate one image. <prompt>"; variants 2–4 via "Run that exact
same prompt 3 more times … verbatim" (Flow's Omni agent re-runs the stored prompt; it
echoed the full verbatim text in chat and confirmed "using the verbatim prompt", and
each generation's detail-view prompt matched). Note: in the Omni UI a submit yields
**1 image** regardless of the count setting — the count x4 default did not fan out.

## Files (best 2 per arm, Flow-native 1376×768 1K JPEG)

| File | Flow media id | What it shows |
|---|---|---|
| `beat1-baseline-1.jpg` | `1d5062f5` | The baseline arm's BEST face: closed-mouth stern determination — still no strain/effort register, dry skin, intact fabric |
| `beat1-baseline-2.jpg` | `c671660d` | Representative baseline: calm neutral gaze off-frame, zero manifestation — the corpus "dead face on a money-shot" failure, reproduced |
| `beat1-l35-1.jpg` | `d5f7aea1` | Teeth-gritted snarl, engaged brow, jaw/neck tension, facial flush, sweat sheen + airborne droplets, dust motes |
| `beat1-l35-2.jpg` | `ca804066` | Open-mouth strained cry, straps torn to shreds at the seams, sweat-glazed skin, dust/vapor whirl (displaced air) — peak face + peak manifestation in one panel |
| `beat2-baseline-1.jpg` | `0f39715e` | Baseline ECU: smooth tan skin, ambient gym sheen only, intact strap, inert |
| `beat2-baseline-2.jpg` | `d40666b4` | Baseline ECU: veiny flex, mild sheen, no event phenomena (also dropped the tank-top edge entirely — baseline drift) |
| `beat2-l35-1.jpg` | `cdcb437c` | L35 ECU: standing sweat droplets, vapor rising under the lamp, strap torn at two seam points with thread wisps, warm natural flush |
| `beat2-l35-2.jpg` | `5e68a933` | L35 ECU: seam burst with threads flying, growth motion-smear ghosting on the bicep silhouette (displaced air/motion), deeper flush |

Files are committed as Flow-native JPEG (no recompression) rather than PNG — same
precedent as `sketches/staging-examples/` (L34). Full project (all 16 gens) remains in
the Flow project "L35 Render Validation 2026-06-09" for re-inspection.

## Per-arm observations (all 4 variants judged per arm, best-of-4 committed)

**Beat 1 baseline (4 variants):** dead/neutral faces **3/4**; the 4th is a closed-mouth
"determined" look — better, but still FAILS the L35 vision rubric (no strain, ecstasy,
awe, or exertion register). Peak-intensity faces: **0/4**. Manifestation: sweat 0/4,
fabric strain 0/4 (one faint legging scuff), displaced air 0/4 (ambient haze only).
The growth reads as a finished physique, not an event.

**Beat 1 L35 (4 variants):** peak-intensity faces **4/4** (gritted-teeth snarl ×2,
open-mouth strain ×2), every one with engaged brow, jaw/neck tension and effort flush —
dead faces **0/4**. Manifestation: sweat sheen 4/4 (airborne/running droplets on 3),
obvious fabric seam-tear 2/4 + damp strained cling 2/4, displaced dust/vapor 3/4.
Same identity, wardrobe class, setting and camera as baseline — the directive did not
disturb style or framing.

**Beat 2 baseline (4 variants):** ambient lighting sheen only 4/4; seam strain **0/4**;
flush 0/4; particles 0/4. Static "already-buff" body.

**Beat 2 L35 (4 variants):** heavy sweat + standing droplets **4/4**; seam-tear /
thread-burst **4/4**; displaced air 3/4 (vapor, dust drift, motion-ghosting); skin
flush 4/4 — of which **2/4 oversaturated** into a lobster-red full-arm repaint (the two
committed files are the natural-flush pair; the over-red pair was left in the Flow
project). Head correctly cropped 4/4; no SFX text or action lines anywhere.

## Dead-face count (the corpus metric L35 exists to fix)

| Arm | Dead/neutral faces | Peak-intensity faces |
|---|---|---|
| Beat 1 baseline | 3/4 (+1 low-intensity determined) | 0/4 |
| Beat 1 L35 | **0/4** | **4/4** |
| Beat 2 (both arms) | n/a — head cropped per L20, face directive correctly omitted | — |

## Verdict detail

- **Face branch (face-visible beats): VALIDATED.** `_FACE_INTENSITY` converts a 0/4
  peak-face rate to 4/4 with legible, nameable emotions (strain, ferocious effort,
  overwhelmed cry). Exactly the corpus Finding 3 fix.
- **Manifestation branch (all growth beats): VALIDATED.** `_PHYSICAL_MANIFESTATION`
  reliably adds sweat, seam-level fabric failure (coverage preserved in 16/16 — the
  always-clothed default held), flush, and displaced-air phenomena that make the growth
  read as a *happening-now event*; baselines render it as a static body. Corpus
  Finding 4 confirmed in render.
- **Calibration note (non-blocking):** at ECU scale on Flow/NB2, "skin taut and
  flushed" over-triggers in ~half of renders (full-arm red repaint). If this recurs on
  production models, consider an ECU-scale soften (e.g. "warm exertion flush, natural
  skin tone preserved") — a prompt-calibration tweak, not a rule-design change. Watch
  for it in QA via the existing L35 vision rubric.
- Filter note: zero content-policy trips in 16/16 submits with this phrasing (no steep
  low-angle language, no celebrity names, neutral anatomy terms).

## Reproduce / extend

1. Flow → project "L35 Render Validation 2026-06-09" (all 16 gens + prompts in-session).
2. Prompts: Beat-1/Beat-2 base prompts above; Arm B appends the directive strings from
   `rules/l35_growth_intensity.py` **verbatim** (never paraphrase; `feedback_dont_paraphrase_canonical_rubrics.md`).
3. Judge with the L35 `vision_rubric` (same file) — (A) face registers peak intensity
   when visible, (B) growth reads as physical phenomena.

## Related

- `rules/l35_growth_intensity.py` — the rule under test (directive strings + vision rubric)
- `references/lessons-learned.md` § L35 — the lesson
- `references/escalation-devices.md` — device menu this run exercised (sweat/fabric/displaced-air = physical-manifestation device; motion-ghosting appeared as a bonus)
- `research/comic-corpus/synthesis/success-elements.md` Findings 3–4 — the corpus basis
- `sketches/staging-examples/` — L34 precedent for committed reference figures
