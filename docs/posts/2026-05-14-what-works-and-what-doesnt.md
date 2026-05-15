# What works and what doesn't: Grok vs Nano Banana 2 vs GPT Image 2 for comic-panel generation

**2026-05-14** · A 3-way model bake-off on the same shotlist, same references, and the same recalibrated prompts. Hard numbers on which model to use for which beat, why each one fails when it fails, and the pipeline-code changes the data drove this week.

## Why we ran this

The pipeline ships with a rulebook (`lessons-learned.md`, lessons L1 through L24). Most of those lessons were discovered the same way: a panel came back wrong, we figured out what the model latched onto, we wrote a rule, we baked it into [`compose_prompt()`](../../skills/comic-production/scripts/next_panel.py) so the next run inherits the fix automatically.

That works until a new model shows up. Grok Imagine launched on Higgsfield, and we wanted to know: do the same rules survive on a more stylized model? Does Nano Banana 2 actually deserve its position as the default? Is GPT Image 2 a usable alternative for the panels Nano Banana 2 struggles with?

So we built a 6-panel Chun-Li transformation comic — the canonical pipeline stress-test — and ran it on all three models with identical inputs.

## The setup

- **6-panel single-image-per-page transformation** of Chun Li from tier 1 (canonical baseline) to tier 5 (hyper-developed FMG silhouette) in her training dojo.
- **Same shotlist, same refs, same prompts on all three models.** Face card (newly regenerated to fix a hair-styling drift in the v1), body baseline, dojo environment ref, muscle-size lineup. Prompts use the full L19 photoreal-CGI anchor block, the L24 enumerated-substitute accessory negation list, and the new May-14 female-anatomy anchor on body-region ECUs.
- **All three models on their cheap tier.** Grok `std` mode (1 credit/img), Nano Banana 2 Flash 1k (1.5 credits/img), GPT Image 2 medium quality 1k (2 credits/img). 27 credits total for the comparison; ~$5 in pipeline currency.

## The composite

![3-way model comparison composite — Grok, NB2, GPT Image 2 across 6 panels](./assets/composite-3way-2026-05-14.png)

*Left to right: GPT Image 2, Nano Banana 2, Grok Imagine. Top to bottom: P1 mcu (consider beat, tier 1), P2 medium (first sensation, tier 1), P3 ECU on right bicep (arms beat, tier 3), P4 3q-full (stage change, tier 4), P5 ECU on abs (abs beat, tier 5; GPT2 hard-blocked by safety filter), P6 low-angle reveal (tier 5).*

Open the full-resolution image (1744 × 3772 px) for detail — the per-model wristband renderings, the tier-4 silhouette diffs, and the face-card identity carry-through are easier to read at full scale.

## What works

### Nano Banana 2 — the pipeline workhorse

NB2 was the clear winner on every test that required the prompt to actually do something specific. It read the prompt and rendered the prompt.

- **Tier scale-up landed cleanly** at tier 3 (P3 bicep ECU), tier 4 (P4 stage change full-body — shoulders 2× normal width, visible breast contour through the qipao, sculpted quads), and tier 5 (P5 abs, P6 reveal). It treated the muscle-size lineup as an actual proportion reference instead of a suggestion.
- **ECU framing obeyed.** When the prompt said "extreme close-up on the right bicep," that's what came back. Macro framing, the bicep dominating, head off-frame, white spiked wristband visible at the bottom edge — every detail.
- **Pose deltas delivered.** P2's "first sensation" reaction shot — Chun Li examining her own arm as the surge starts — rendered as a reaction shot, not a generic combat stance.
- **L24 accessory suppression worked.** Both wrists with canonical white spiked wristbands, both attempts. No dark cuffs, no smartwatches, no studded leather substitutes.
- **L23 verbal env anchor held the dojo** on every panel where the env ref was dropped to fit the 3-ref ceiling. Red lanterns, latticed sliding doors, calligraphy scrolls, dark-wood floor — all rendered from the dense verbal anchor in the prompt body.

### GPT Image 2 — the cinematic specialist

GPT Image 2 is the prettiest renderer of the three. Face rendering is cinematic in a way the others aren't. It's the model you reach for when the character is the camera's full attention.

- **Best face / aesthetic / character-beauty work.** P1 and P2 both came back with cinematic compositions, deep facial detail, and very vivid red ribbons. If the panel is a portrait or a dialogue beat, GPT Image 2 wins on raw look.
- **Tier scale-up actually overshoots.** P4 and P6 came back larger than NB2 — possibly tier 5+ when we asked for tier 4 or tier 5. This is a feature for splash / hero / reveal panels where you want maximum impact.
- **Pose deltas delivered.** P2's reaction shot rendered closer to the intent than either Grok or NB2 — Chun Li looking at her own hands in palpable "what is happening" surprise.

### The L1–L24 rule set survives across models

A nice secondary finding: most of the lessons are not Nano-Banana-specific.

- **L19 (photoreal CGI register, no 2D drift) held on all three models.** Even Grok, which is tagged as "expressive / bold / high-contrast" and is biased toward stylized output, never broke into 2D illustration. The opening render-engine anchor + closing negation block is doing real work.
- **L20 (camera distance bias) held on NB2 and GPT2.** Every framing matched its declared beat.
- **L21 (ref-exclusion clause) prevented lineup-number watermarks** that we saw in the previous run when the clause was dropped.

## What doesn't work

### Grok Imagine — capped on female muscularity

Grok refuses to render hyper-developed female silhouettes. We tried four times across two correction strategies (image-edit-on-base and rebuild-from-scratch with concrete dimensional language). The model returned the same tier-1-to-tier-2 athletic build every time.

In the composite, look at P4 and P6 across the three columns. NB2 and GPT2 deliver shoulders 2× normal width with visible mass. Grok returns canonical baseline-tier Chun Li in the dojo — pretty, on-brand, on-pose, but wrong on the one thing the prompt was about.

This is a hard model ceiling, not a prompt problem. We added a `MODEL_MUSCULARITY_CEILING` table to [`next_panel.py`](../../skills/comic-production/scripts/next_panel.py) (currently `{"grok_image": 3}`) so the planner warns when a panel's declared tier exceeds the model's actual delivery range and recommends rerouting to NB2 or NB2 Pro.

### Grok ignores pose deltas

Grok has a strong learned prior for "Chun Li in dojo = generic martial stance." Any prompt-level pose delta gets overridden by this prior. P2's reaction-shot prompt, P4's specific stage-change pose, P6's palms-forward triumphant reveal — Grok rendered all three as the same Wing-Chun-style guard. NB2 and GPT2 obey the per-panel pose intent; Grok does not.

The fix in the rule set: if you're using Grok, move pose / camera / expression to the opening of the prompt (not buried in the delta paragraph), and prefer NB2 for panels where the pose is the storytelling beat.

### GPT Image 2's safety filter is much stricter on FMG body-region ECUs

P5 was the abdomen ECU at tier 5. NB2 returned NSFW-rejected on the first attempt; a retry with the same prompt cleared it (the filter has variance, per the `feedback_nsfw_retry_policy` memory).

GPT2 hard-blocked on three attempts: the original prompt, a reframe that emphasized "muscle definition through stretched fabric," and a second reframe that kept the qipao fully covering the torso with no exposed midriff. **Three attempts, three blocks.** The placeholder tile in the composite shows where the panel should be.

This is a clean GPT-Image-2-specific failure mode. It matches our existing memory note (`feedback_gpt_image_2_nsfw_strict`) and the recommendation stands: default to NB2 for FMG content; reach for GPT2 only on panels where the body region isn't the camera's primary target.

### Don't auto-derive transformation beats from tier alone

This isn't a model finding — it's a process finding from running the validation.

The first version of this run included an authoring mistake: when the user said "stage change at tier 4," I autonomously escalated that to a `suit_fail` beat with hair shaking loose and qipao tearing to remnants. The audit then dinged Grok for failing to render the hair shaking loose and the costume tearing. **But Grok was actually right** — those state changes weren't in the brief. The model correctly kept the buns intact and the qipao undamaged.

The lesson: "stage change at tier N" means a tier bump only. Hair-down, suit-fail, costume-destruction are independent authoring decisions that need explicit consent. The pipeline now has a feedback memory (`feedback_dont_invent_state_changes`) that captures this, and `compose_prompt()`'s L22 hair-state helper deliberately does *not* auto-derive — it only surfaces what's explicitly set on `panel.hair_state`.

## The routing matrix we ended up with

| Panel type | Primary | Alternate | Skip |
|---|---|---|---|
| Tier 1 dialogue / character intro / talking heads | NB2 | GPT2 (slightly more cinematic) | — |
| Pose-delta-heavy (reaction shots, specific stances, action) | NB2 | GPT2 | Grok |
| Body-region ECU at tier ≥ 2 (arms, abs, chest, hips) | **NB2 only** | — | Grok (refuses framing), GPT2 (safety filter) |
| Stage-change full-body at tier 4+ | **NB2** | GPT2 if you want more aggressive scale | Grok |
| Reveal / splash at tier 5+ | NB2 (precise) or GPT2 (over-tier impact) | — | Grok |
| Text-heavy reference graphics (status boards, infographics) | NB2 1k (validated 2026-05-13) | GPT2 at quality=high + 2k | — |

The pipeline's planner now warns on panels that exceed Grok's muscularity ceiling, and the suggested model is named directly in the warning's `reason` field.

## What landed in the code this week

The week's findings turned into actual pipeline code, not just lessons-learned entries:

- **L21 / L22 / L23 / L24 auto-injection in [`compose_prompt()`](../../skills/comic-production/scripts/next_panel.py).** Five new helpers — `L21_REF_EXCLUSION`, `_hair_state_line`, `_env_dense_anchor`, `_l24_accessory_line`, `_female_anatomy_anchor_needed` — wired into the prompt skeleton at the appropriate slots. The lessons fire automatically on every future panel; no manual injection.
- **3-ref ceiling enforcement in [`build_plan()`](../../skills/comic-production/scripts/next_panel.py).** When face card + state anchor + lineup would already use 3 refs, env is dropped and `env_dropped=True` flips so L23's dense verbal anchor fires. The env entry in `refs_to_attach` gets relabeled `_dropped_for_ceiling` so the production driver knows the prompt is carrying the verbal fallback instead.
- **`MODEL_MUSCULARITY_CEILING` table.** Currently `{"grok_image": 3}` based on this validation. `build_plan` emits a `WARNING_MODEL_MUSCULARITY_CEILING` with a per-panel routing recommendation when the declared tier exceeds the model's ceiling.
- **Updated [CHANGELOG.md](../../CHANGELOG.md)** with the day's auto-injection landing, the 3-ref ceiling enforcement, the model muscularity ceiling, the face-card regen, the 3-way comparison, and the new "don't invent state changes" memory.

## What's still open

- GPT Image 2's FMG body-region threshold — we know it hard-blocks tier-5 abdomen ECU, but we don't yet know the lower bound (is tier 3 safe? tier 4?). Worth a dedicated micro-test.
- Multi-view location refs (L14 extension of `pick_location_anchor()`) — logged in May 13's changelog, still pending. Not addressed this week.
- A model-specific prompt-shape pivot for Grok — moving pose / camera to the opening of the prompt — might recover some of Grok's pose-obedience for tier-1 / tier-2 work where Grok's cost advantage matters.

## tl;dr

Default to Nano Banana 2. Use GPT Image 2 for cinematic portraits and high-tier reveals where you want over-the-top scale. Skip Grok for anything with a meaningful muscle silhouette or a specific pose — its strong character prior overrides the prompt. The L1–L24 rule set transfers across models cleanly enough that we're confident shipping the auto-injection layer.

The composite tells the story in one image. The pipeline code now enforces what it shows.
