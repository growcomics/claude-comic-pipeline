# Picks Profile — eva (+ muller Beat 95): why the Flow favorites win

**Date:** 2026-07-20 · **Method:** 8 Flow-favorited generations (7 eva beats + muller Beat 95)
compared against ALL beat siblings (114 images total) by 8 independent fresh-context grader
subagents, each reading `research/comic-corpus/analysis-rubric.md`,
`skills/comic-production/references/cinematic-framing.md`, and
`skills/comic-production/references/qa-checklist.md` verbatim before any image. Each grader
blind-ranked the beat FIRST, then ran a revealed 7-dimension favorite-vs-siblings comparison.
Raw verdicts: `research/picks-profile-eva-verdicts/*.json`. Favorites were pulled from Flow's
`projectContents.workflows[].metadata.favorited` (see the ⭐ pick-loop in `studio/DEPLOY-NOTES.md`).

## Headline numbers

Blind agreement: graders' blind #1 matched the owner's favorite **5 / 8** beats.
(Disagreements: Beat 18 — blind preferred the owner's own STUDIO pick; Beat 30 — blind
preferred the torn-top peak-ecstasy roll; muller B95 — blind preferred the cleaner-text sheet.)

Per-dimension score of the favorite vs its siblings (8 beats):

| Dimension | fav better | tie | fav worse |
|---|---|---|---|
| Camera / composition | **6** | 2 | **0** |
| Growth payoff density | **5** | 2 | 1 |
| Muscle rendering / size | **5** | 2 | 1 |
| Defect absence | **5** | 1 | 2 |
| Wardrobe / identity fidelity | **4** | 4 | **0** |
| Lighting | **4** | 4 | **0** |
| Expression intensity | **0** | 5 | **3** |

## What actually drives a pick (in order of evidence strength)

1. **Camera & scale-in-frame — the strongest single signal (6/8, never worse).** The favorite
   is repeatedly the roll that breaks the flat-frontal default: diagonal motion axis + elevated
   three-quarter (B4), the only tight portrait crop where the bicep fills 40–50% of frame (B17),
   one of only three three-quarter stagings in a 12-roll batch (B18), diagonal knee-up with FG
   mass + cape sweep (B30). CONFIRMS `feedback_overshoot_camera_dynamism` and L20 (get close).
2. **Payload density & visibility (5/8).** Surge FX that sheath BOTH arms + torso as dense arcs
   (B8), the biggest boulder-mass biceps plus a stacked laser column (B38), abs/obliques made
   *visible* by cropping the garment (B20), the curviest body in figure-revealing wardrobe (B95).
   CONFIRMS `feedback_growth_density_mandate`, over-spec size direction, and chest over-spec.
3. **Canon fidelity (4/8, never worse).** In B30 the intact S-shield costume beat siblings with
   rawer faces and flashier cameras; ~half that batch drifted (gray tanks, skirts, destroyed
   logos). In B18 the prompt's explicit beauty clause dominated. CONFIRMS refs-are-truth +
   wardrobe lock (`feedback_wardrobe_drift_from_anatomy_keywords`, L21-L24 family).
4. **Cleanliness (5/8) — with a ref-sheet exception.** Favorites are usually the defect-free
   roll (single legible SFX, correct beat state, no invented VFX/accessories). BUT muller B95
   shows garbled sheet labels are tolerated on reference sheets — sheets are consumed as visual
   refs, not shipped pages. Don't over-reject ref sheets on lettering alone.
5. **Lighting (4/8, never worse).** Golden-hour raking key with long cast shadows (B4, B17, B30),
   dusk chiaroscuro with the energy column as warm key (B38). The light *gradient across the
   musculature* recurs as the differentiator — flat midday/diffuse siblings lose.

## The contrarian finding: expression does NOT drive the Flow pick

**0/8 favorites won on expression intensity; in 3 beats the favorite's face was honestly
WORSE than shock/ecstasy siblings** (B17 soft smile on a "Wow" beat, B38 face half-swallowed by
laser bloom, B95 sternest faces in the batch). The owner trades face for size, FX density,
canon fidelity, and crop aggression at *selection* time.

**Nuance — two value systems observed (Beat 18):** the owner's Flow favorite (prettiest face,
correct eyeline, cleanest render) and the owner's in-Studio manual pick (triumphant grin +
reacting witnesses) are DIFFERENT images. Flow-time favoriting optimizes *character rendering*;
review-time picking optimizes *storytelling*. `feedback_expression_intensity` therefore stays a
GENERATION mandate (batches with dead faces limit the choice pool — 10 of 19 B30 rolls had
closed-lip smiles on a triumph beat), but selection evidence says expression is a tiebreaker,
not the criterion.

## Prompt-able rules distilled from the 8 picks

- **Money-shot beats:** tight portrait/near-ECU crop, flexed muscle ≥40% of frame, dense
  vascularity, exactly ONE SFX word, background dropped to bokeh. (B17)
- **Trigger/surge beats:** energy FX must sheath both arms AND torso as dense arcs hugging the
  musculature — never wisps; state explicitly that the catalyst object is already gone. (B8)
- **Climax beats:** stack the escalation — over-spec size + FX wreath + eruptive beam + dusk
  chiaroscuro key. Size alone or FX alone loses to the stack. (B38)
- **Walking/aftermath beats:** mid-stride on a diagonal, slightly elevated three-quarter camera,
  low raking golden-hour sun with long shadows — motion + light gradient beats a bigger but
  statically posed figure. (B4)
- **Scripted-pose beats:** frame wide enough to include every named pose landmark and hold the
  canonical costume; pose-complete + on-costume outranks literal framing compliance AND rawer
  faces. (B30)
- **Turnaround upgrades:** make the upgrade visible (crop the garment so abs/obliques show),
  hard-lock wardrobe/tattoo/view-count across views; reject sheets that drop a view, strip rear
  views, or invent VFX/accessories. (B20)
- **Character spec sheets:** figure-revealing wardrobe (tank + shorts, bare legs) + body-detail
  crops (chest MCU, high-angle lean) alongside the 5-view turnaround. (B95)
- **Outdoor default light:** ask for golden-hour raking key + long cast shadows; flat midday
  diffuse is a losing look. (B4/B17/B30/B38)

## Confirms vs contradicts the existing lesson base

- **CONFIRMS:** overshoot camera dynamism; growth-density mandate; over-spec size (incl. chest);
  L20 get-close; wardrobe/canon lock; L21 (no ref-render leakage observed in favorites);
  refs-are-truth. L24 is *validated by omission*: the anachronistic wristwatch appears batch-wide
  in eva (all 19 B30 rolls, most of B17/B18) — suppression was missing from the eva genspec.
- **NUANCES/CONTRADICTS:** `feedback_expression_intensity` — selection evidence (0/8) says the
  Flow pick doesn't reward it; keep it as a generation mandate, treat it as a tiebreaker in QA
  scoring. Baked-lettering-garble as an auto-reject — contradicted for REF SHEETS only (B95).
- **NEW LESSON CANDIDATES (proposed, NOT applied):**
  - *L-cand-A:* Aerial/overhead prose ("overhead", "camera is 150 ft in the air") fails in
    ~50% of rolls — always use the cinematic-framing high-angle/bird's-eye fragments instead
    of bare altitude prose. (B4 + B38 both showed mass non-compliance.)
  - *L-cand-B:* Golden-hour raking key as the default outdoor volume block; dusk chiaroscuro
    variant on climax beats. (4/8 lighting wins share this signature.)
  - *L-cand-C:* One-SFX rule — duplicate SFX words ("BULGE! BULGE!") recur (2/16 in B17) and
    cost otherwise-winning rolls the pick; QA should flag duplicated SFX as a defect.

## Systemic defects surfaced (feed to the defect registry / genspec)

- Wristwatch on essentially every eva roll → add L24 suppression to the eva genspec.
- Background extras (park pedestrians, dogs, pointing trios) in most park-env rolls, including
  2 favorites — the no-extras default is not reaching Flow prompts on this project.
- Beat-state leakage: 2/12 B8 rolls kept the rock the prompt said had melted.
- Wardrobe roulette: 1/12 B8 topless; 4/24 B20 sheets topless on rear views; ~half of B30
  drifted costume. Always-clothed + costume-lock language needs reinforcement on Flow.

## Coverage & conflicts

- eva: 7/7 favorites synced to Studio (tag `flow-fav`; 6 also ★ kept). **Conflict, Beat 18:**
  owner's in-Studio keep (`65a129a178.jpg`) ≠ Flow favorite (`ae80ee28a5.jpg`); owner's manual
  pick kept the beat win, favorite carries tag+approved only. Grader head-to-head sided with
  the STUDIO pick for the page, and suggests banking the favorite as a beauty ref-chain anchor.
- muller: 1 favorite (Beat 95) synced.
- **Not yet covered:** 56 favorites in Flow projects never synced to Studio — 54 of them in the
  "Jul 11, 01:16 AM" project (Esmeralda electric-chair story, 1,721 gens). A Whole-project send
  + the auto-favorite loop would bring those picks in. The growcomics (mac mini) Flow account
  was not reachable from this session; its projects (muller June batches, Google Flow Jun-30
  sections, Daughter of Hercules, Goth Giantess, Spin & Swell…) await the same sweep there.
  Flow's `searchUserProjects` cursor pagination 400s on replay, capping enumeration at the 20
  most recent projects per session — revisit if older projects need sweeping.
