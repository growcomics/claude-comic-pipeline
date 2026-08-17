# margo-full finalist ranker brief (Tier 2)

RUN DIR: `/Users/mattmenashe/Documents/claude-comic-pipeline/runners/bakeoff/runs/margo-full-20260811`

You rank the shortlisted finalists for a set of beats of an 86-page photoreal-CGI
muscle-growth comic and name one winner per beat. The upstream triage was a cheap pass and
is NOT trusted — apply every kill rule yourself.

## Read first (verbatim, never paraphrased into your reasoning)
- `skills/comic-production/references/qa-checklist.md`
- `skills/comic-production/references/cinematic-framing.md`
(both under `/Users/mattmenashe/Documents/claude-comic-pipeline/`)

## Per beat
1. Read the beat's entry in `judge-cards.json` (run dir): `chars`, `wardrobe`,
   `expect_text`, `action`, `stage`.
2. Read `sheets/<beat>-final.jpg` ONCE — the finalists side by side, each labelled vNN in
   yellow at its top-left.
3. Apply the KILL rules. A killed tile cannot win:
   - **COAT** — the lab coat was removed from this comic entirely. Any white/light lab
     coat, jacket, blazer, smock or sleeved over-garment on MARGO is an automatic kill,
     including one merely draped over her shoulders. Look for a collar, lapels, or sleeves
     over the grey tank.
   - **LET** — transcribe every bubble/caption. Text that differs from `expect_text`,
     a blank bubble, gibberish, a duplicated/extra bubble, or a coloured bubble kills the
     tile. A beat whose card has an empty `expect_text` must show NO bubbles or captions.
   - **HEAD** — visible human count must equal `len(chars)`. A mirror reflection of the
     same person counts once (say so). No background extras.
   - **WARD-07** — bare skin blending/gradienting into fabric on the same limb with no
     torn edge. (Legal: a seam split with crisp frayed edges.)
   - **SKIN** — skin rendered as torn fabric; any wound or damaged skin.
   - **COVER** — breasts, groin or buttocks uncovered. Garments may strain and tear;
     coverage is always preserved.
   - **PROP** — glitched or incoherent props (broken/melting barbells, fused hands,
     extra limbs).
   - **FLAT** (rule 9) — blank, neutral, waxy, doll-like or merely mild expression on a
     beat whose action line calls for intensity. A calm face on a dramatic beat is a KILL.
   - **MOUTH** — a speaking character rendered with a closed mouth under the balloon.
4. Rank the survivors, earlier criteria dominating later:
   1. **Camera & composition** — does it match the card's action line; crop aggression,
      diagonals, FG/BG depth. (Strongest predictor of the owner's real picks.)
   2. **Growth / payoff density** — how much of the frame the muscle payoff occupies.
   3. **Body scale vs stage** — s1 slim / s2 athletic / s3 heavily muscular /
      s4 beyond-bodybuilder / s5 colossal. The owner's standard is BIGGER and ROUNDER than
      "realistic" — flag UNDER-SCALE if the physique reads a stage low.
   4. **Lighting drama** — directional key, colored practical/FX source, rim light,
      background darker than the subject, glossy specular skin.
   5. **Expression intensity** (tiebreaker).
5. Read the FULL-RES file of your top pick once
   (`variants/<beat>/<vNN>-*.png`) to confirm no defect hides at thumbnail scale —
   especially lettering spelling, seams, and hands. If it fails, drop to the next survivor.

## Output
Append one JSON object per line to the picks file you were given (create it if needed):
```
{"beat":"<beat>","variant":"vNN","notes":"<=60 words, board-ready: why it won and what the runners-up lost on","ladder":true|false,"killed":{"vNN":"CODE reason"}}
```
- `variant` must be `null` if EVERY finalist is killed — then also say so in your reply.
- `ladder` is true only if the winner clearly under-scales its stage and a size-escalation
  refinement pass is warranted.
Then reply with a one-line-per-beat summary. Do not run `drive.py` at all.
