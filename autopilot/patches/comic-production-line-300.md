# Patch: `skills/comic-production/SKILL.md` — Mandatory Rules Block + Transformation Type

Two-part behavior change:
- Moves "ask the user which rules to drop" from a per-project chat interrupt to a one-time config read
- Adds transformation-type awareness so FMG / BE / Glute / MMG / Mixed each get the right defaults

## Find this block (line ~300)

```markdown
7. Mandatory rules block — before starting any comic, present the full rules list to the user and ask which ones to drop or modify for this project. Do not skip this step. Copy the final agreed-upon block verbatim into every panel prompt.

   **Pre-production rules review** — present this at project start:

   | # | Rule | Why it exists |
   |---|---|---|
   | 1 | Muscles are natural healthy skin tone — NOT red, NOT inflamed | Model renders muscles as red/inflamed during growth without this |
   ...
   | 10 | Once a character has grown muscles they stay at that size or larger in all subsequent panels — muscles never revert | Model reverts characters to reference image size without this |

   Ask the user: *"These are the default mandatory rules for every panel. Are there any you want to remove or modify for this comic?"*

   Common reasons to modify:
   - Rule 3 (muscles = breasts): drop if the story has male characters or non-transformation arcs
   - Rule 8 (no camera eye contact): drop for cover panels or direct-address moments
   - Rule 10 (no reversion): drop if the story includes a de-transformation arc
```

## Replace with

```markdown
7. Mandatory rules block — read which rules apply from `production-config.json` at the project root if it exists. Compose the block from rules 1–10 minus any not in `mandatory_rules.active`, plus any `mandatory_rules.extra_lines`. Copy the resulting block verbatim into every panel prompt.

   The pipeline supports five transformation types via the config's `transformation_type` field. Each has its own default rule set. The `production-briefing` skill writes the right defaults at project setup; this skill just reads them.

   If no config exists (legacy projects), fall back to pre-2026-05-13 behavior: present the full rules list at project start and ask which to drop. The ask happens ONCE per project, not per panel.

   **The 10 rules** — same as before, transformation-type-agnostic. The transformation type only determines which are default-ON; the rules themselves don't change.

   | # | Rule | Why it exists |
   |---|---|---|
   | 1 | Muscles are natural healthy skin tone — NOT red, NOT inflamed | Model renders muscles as red/inflamed during growth without this |
   | 2 | Skin is wet, shiny, glistening with effort, like oiled skin catching warm light | Gives the model a positive visual alternative to "straining" |
   | 3 | Any character with enlarged muscles also has proportionally enlarged, full breasts with prominent cleavage visible | Model won't add both unless explicitly told, every time |
   | 4 | All characters fully clothed at all times — clothes may be torn, stretched, or splitting at seams but always cover the body | Prevents nudity while allowing dramatic clothing destruction |
   | 5 | Speech bubbles show exactly the correct character speaking their correct line — never the wrong character | Model assigns bubbles by character position — wrong attribution breaks the story |
   | 6 | Every speech bubble contains a unique line — no character repeats themselves | Without this, characters echo each other or repeat lines across panels |
   | 7 | Every character has a vivid, animated, expressive face — never neutral or blank | Model defaults to lifeless expressions — the single biggest quality killer |
   | 8 | All characters look at each other, never at the camera | Eye contact with viewer breaks the fourth wall in narrative panels |
   | 9 | Correct human anatomy — exactly two arms per person, no extra limbs | Model occasionally generates extra limbs |
   | 10 | Once a character has grown muscles they stay at that size or larger in all subsequent panels — muscles never revert | Model reverts characters to reference image size without this |

   **Per-transformation-type defaults** (written automatically by `production-briefing` based on `transformation_type`):

   | Type | Active rules | Why these defaults |
   |---|---|---|
   | `fmg` | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 (all) | The historical default. The whole rule set was authored for FMG. |
   | `be` | 2, 4, 5, 6, 7, 8, 9 | Rule 1 (muscle skin tone) is N/A — no muscle growth. Rule 3 (muscle=breasts) is redundant — this IS the breast arc. Rule 10 (muscles never revert) is N/A — BE has its own monotonicity (in `extra_lines`). |
   | `glute` | 2, 4, 5, 6, 7, 8, 9 | Same reasoning as BE. Glute-specific monotonicity goes in `extra_lines`. |
   | `mmg` | 1, 2, 4, 5, 6, 7, 8, 9, 10 | Rule 3 OFF — male characters, no breasts. All other rules apply identically. |
   | `mixed` | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 (all) | Multi-arc — every rule may apply on some panel. Manual emphasis via `extra_lines`. |

   **Recommended `extra_lines` per type** — these aren't rules from the table above; they're project-specific addendums the briefing appends to the rules block:

   - **FMG**: usually none. The rule table itself is FMG-tuned.
   - **BE**: monotonic breast size, hourglass silhouette, round shape, seam-tearing clothing. See `production-briefing/SKILL.md` for the canonical BE extras.
   - **Glute**: monotonic glute size, hourglass silhouette, rounded shape, balanced thighs, seam-tearing wardrobe.
   - **MMG**: male anatomy throughout, pectorals (not breasts), V-taper, masculine facial structure, body-hair continuity.
   - **Mixed**: which arcs apply to which characters, growth order, current-active-stage lineup convention.

   **Common one-off drops** (overrides on top of the type default):
   - Rule 3 (muscles = breasts): drop for any male-only comic regardless of type
   - Rule 8 (no camera eye contact): drop for cover panels or direct-address moments
   - Rule 10 (no reversion): drop if the story includes an intentional de-transformation arc
```

## Why

Before: every new project triggered a chat back-and-forth at panel-compose time to agree on the rules block. With autopilot, the chat is gone — the agent should look up the answer, not ask. AND the pipeline assumed FMG by default, which is wrong for BE / glute / MMG runs.

After: rules answer lives in `production-config.json`. Read once at the start of generation; reuse for every panel. The transformation type drives the default — BE projects don't waste rules on muscle skin tone, MMG projects don't waste rules on muscle=breasts. Legacy ask behavior preserved when no config exists.

## Lines changed

~30 lines edited inside the existing section. The rule table itself is unchanged (still 10 rules, same text, same reasoning). What's new is the per-type default mapping plus the `extra_lines` guidance.
