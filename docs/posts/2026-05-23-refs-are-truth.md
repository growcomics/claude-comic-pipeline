# Refs Are the Truth, Prompts Are Deltas: enforcing L10 in code

**2026-05-23** · A 55% prompt-size reduction by deleting the appearance prose every panel was carrying. The pipeline's most important architectural principle was documented but not enforced; this is the diff that fixes it.

## The principle that wasn't enforced

L10 has been in the rules doc for months: **"references are the truth, prompts are deltas."** The idea is simple. When you generate a comic panel, you attach reference images — a face card for the character, a body-tier lineup for proportion, an env ref for the location, the prior accepted panel for state continuity. Those images carry **identity**. The prompt's job is the opposite: it carries the **delta** — the camera, the pose, the action, the momentary state change.

Identity is in the refs. Deltas are in the prompt.

That principle was load-bearing in the docs and load-bearing in our heads. But when we looked at what the composer was actually emitting — the real strings being sent to the image model — every panel was a 1,700-word essay about what the character looks like.

## The evidence

I ran the composer on `chun-li-test` panel 6 at peak conditions: tier 6 stage-change, lineup attached, tier-6 reinforcement PNGs attached, env ref attached, prior panel attached. Worst case across our actual projects. Here's what the model was being told:

```
11,509 chars · 1,770 words · 53 lines
```

Section-by-section breakdown:

| Section | Words |
|---------|------:|
| L15 BEAUTY ANCHOR — "vogue-cover face quality, sculpted cheekbones..." | 53 |
| L11 STYLE ANCHOR — "cartoony hyper-FMG comic-book proportions..." | 160 |
| **L11 LINEUP PROPORTIONS — "Size tier: 6. The attached muscle-size lineup is a 3D BODY CHART with six figures..."** | **~700** |
| L29 TIER-6 REINFORCEMENT — "Two additional reference images attached showing..." | 210 |
| L10 RENDER DIRECTIVE — "render the attached references exactly as shown..." | 100 |
| L17 canonical anchor + per-character prose | ~50 |
| MANDATORY ANCHORS appearance bits | ~25 |
| … action / camera / lighting / safety / lettering sections | ~470 |

Of those 1,770 words, **about 1,283 (73%) were describing the character's appearance.** Tier-6 muscle volume. Breast scale. Vogue-cover face. Canonical Chun Li. Hair style. Body proportions.

But all of that was already in the attached references.

The face card had Chun Li's face. The body-tier lineup had figure 6 — the canonical tier-6 proportions. The tier-6 reinforcement PNGs had the full-body and anatomical-detail anchors. The prior panel had her current costume state. **The prompt was redundantly re-describing the refs to the model, every single panel.**

The user caught this and named it:

> our prompts need to be guiding the comic by indicating what the character is supposed to be doing, not what they look like... ever. What they look like is determined by the reference.

## How it happened

The pipeline accreted. Each rule was discovered the same way: a real comic came back wrong, we figured out why, we wrote the rule down, and we wired enforcement somewhere. The "wire enforcement" step kept landing in the same place — `compose_prompt()` in `next_panel.py` — and the cleanest available pattern was "add some prose to the prompt."

L15 was added because female characters were rendering as bland AI-default faces. The fix was a glamour anchor paragraph.

L11 was added because tier 6 was rendering at tier 4 proportions. The fix was a giant per-tier description of muscle volume and breast scale.

L29-L32 were added because the multi-figure lineup interpolated downward at peak tiers. The fix was per-tier reinforcement PNGs PLUS 800 chars of prose describing what each PNG depicted.

Each individual addition was reasonable. The cumulative result violated L10.

## The refactor

Restructured `skills/comic-production/rules/` into four categories with file-system enforcement:

```
rules/
├── attach/   — reference-image attachment (no prompt text)
├── action/   — camera / lighting / state-delta / hair-state text
├── match/    — short "match the attached <ref>" directives
└── safety/   — negation / "do not render X"
```

Every Rule subclass declares `category: str`. Audit tools can filter or order by category without inspecting module paths. The categorization is enforced by file location — if a rule's text describes what a character looks like, it can't live in `action/` or `safety/` or `match/` (those categories don't accept appearance prose). It can only live in `attach/`, which doesn't emit text at all.

### Appearance-emitting rules gutted

| Rule | Before | After |
|------|--------|-------|
| L11 (cartoony FMG anchor + tier prose) | ~1,900 chars peak | One-line "match the attached body-tier reference" |
| L17 (canonical character prose) | per-character canon descriptions | One-line "match the attached canonical face card for {chars}" |
| L10 (render directive paragraph) | 300 chars about identity-vs-pose | One-line "match the attached references exactly" |
| L29/L30/L31/L32 (tier reinforcement directives) | ~800 chars each | One shared line "tier-N reinforcement refs are attached — match exactly" |

### Rules deleted entirely

- **L15 (glamour anchor) — DELETED.** Beauty is in the face card. If a character renders as not-beautiful, regenerate the face card. Do not paraphrase beauty into every panel prompt.
- **female_anatomy — DELETED.** Face card + body-tier reinforcement refs carry female-ness now. The prose anchor was a band-aid replaced by stronger refs.

### Rules moved (behavior unchanged)

L18 → `safety/anatomy_coherence.py`. L20 → `action/camera_directive.py`. L21 → `safety/ref_safety.py`. L22 → `action/hair_state.py` (reclassified — hair STATE is a per-panel delta, action-class; hair STYLE is in the face card). L23 → `action/environment_directive.py`. L24 → `safety/accessory_suppression.py`.

### Two new attach rules

`attach/prior_panel.py` formalizes L1 chaining (attach the prior accepted panel as a state-continuity anchor) as a first-class attach rule. It was inline composer logic before; now it's a registry-resident rule with its own `verify_pre_render`.

`attach/internet_3d_base.py` is new. The user's canonical workflow for a new character is: find a great internet image of the character, run it through Higgsfield Nano Banana 2 with a "render as photoreal 3D model, A-pose, plain background" prompt, save the output at `references/characters/<slug>/internet-3d-base.png`. The new attach rule looks for that file and auto-attaches it for every panel the character is in. A new skill at `skills/reference-acquisition/SKILL.md` documents the workflow.

## The persistence gap

There was a second bug behind the first one. The Yuna astronaut comic shipped overnight — 5 panels with visible character drift across them. But when we went to diagnose the drift, **there was no `prompt.txt` anywhere in the project.** The runner had generated, picked, and committed the variants. It had written `_accepted.txt` as the marker file next to each PNG. But the actual prompt the model received? Gone. The composer had returned it as a string in the plan dict, the runner had passed it to Higgsfield, and nobody had saved it.

So we couldn't see what the model had been told. We couldn't tell whether the drift was a prompt problem, a ref problem, a model problem, or a configuration problem.

The fix is six lines in [`runners/runner_core.py:516`](https://github.com/growcomics/claude-comic-pipeline/blob/refactor/refs-are-truth-prompts-are-action/runners/runner_core.py):

```python
def _commit_accepted(project_root, panel_id, variant_paths, picked_idx,
                     plan=None, pick=None):
    # ... existing copy + marker writes ...
    if plan is not None:
        composed = plan.get("composed_prompt") or ""
        if composed:
            (folder / "prompt.txt").write_text(composed)
        refs = plan.get("refs_to_attach_in_order") or []
        (folder / "attached_refs.json").write_text(
            json.dumps(refs, indent=2, default=str)
        )
        plan_record = dict(plan)
        plan_record["accepted_variant"] = picked_idx
        # ... pick metadata ...
        (folder / "panel-plan.json").write_text(
            json.dumps(plan_record, indent=2, default=str)
        )
```

Every accepted panel now writes three files alongside the PNG: the exact composed prompt, the list of attached references with reasons, and the full plan dict including the variant-picker's reasoning. Without these, future drift is undiagnosable. The Yuna project shipped without them and that's why we couldn't tell what was wrong.

## The validation

Same panel, same conditions, after the refactor:

```
 5,114 chars ·  787 words · 50 lines
```

**55.6% reduction in tokens. 55.5% reduction in words.** Same prompt structure, same composition order, same rule attribution in the trace. Every section that's left is one of:

- describing what the character is DOING in this panel (action delta, camera, lighting, hair state, mood)
- pointing at an attached ref to MATCH (face card, body tier, env, prior panel)
- describing what NOT to render (anatomy coherence, ref safety, accessory suppression)
- describing the lettering / overlay layer (bubbles, SFX, captions)

The same composer at tier 2 and tier 7 lands at ~5K chars too — the bloat-scaling-with-tier is gone. Every tier just says "match the attached body-tier reference" and the actual proportion truth lives in the attached PNG.

## What this doesn't validate

Prompt size isn't quality. A shorter prompt that produces worse images is a regression, not a refactor. The PROMPT-level A/B is the half I can run in code; the IMAGE-level A/B requires burning Higgsfield credits to re-render the same panel under both prompts and comparing visual output. That A/B is documented as a follow-up the user runs locally:

```bash
HIGGSFIELD_PROMPT="$(cat docs/refactor/validation/chun-li-p06-BEFORE.txt)" \
  python3 runners/higgsfield_runner.py --project projects/chun-li-test \
    --panel p06-01 --variant-suffix old

HIGGSFIELD_PROMPT="$(cat docs/refactor/validation/chun-li-p06-AFTER.txt)" \
  python3 runners/higgsfield_runner.py --project projects/chun-li-test \
    --panel p06-01 --variant-suffix new
```

Per the `feedback_validate_with_credits` memory, the user should run 4-8 generations on each prompt before deciding to merge. The refactor's correctness rests on the principle being enforced in code, which the prompt-level A/B demonstrates; the image-level A/B is the verification that the model handles the refactored prompt at least as well as the bloated one.

## Backward compatibility

Existing accepted panels stay as-is — no PNG gets retouched. Existing project configs parse unchanged — no shotlist field renamed, no production-config key moved. Rule IDs are preserved: `L21` still identifies the ref-safety rule even though it now lives at `safety/ref_safety.py`. Audit ledgers and `checks.json` files written by the old code remain interpretable.

The one thing that DOES change: re-running `next_panel.py` against any existing project produces a DIFFERENT prompt. That's the point. If a project is mid-flight and depends on getting the same prompt structure on re-render, finish that project before merging this branch.

## What L10 enforced in code looks like

Take the section of the AFTER prompt that used to be 700 words of "Size tier: 6. The attached muscle-size lineup is a 3D BODY CHART..." It's now this:

```
[BODY TIER — L11 match-the-ref]
Body proportions: match figure 6 of the attached muscle-size lineup
exactly — both the muscle mass AND the breast scale. Borrow proportions
only; do not borrow face, hair, costume, or pose from the lineup.
```

35 words. The model is being asked to match an attached image, not to memorize a paragraph that describes the image. If the lineup PNG is wrong, regenerate the PNG. If the rendered body lands at the wrong tier, the fix is "render a better lineup figure" or "attach the tier-6 reinforcement PNGs" — not "add more adjectives to the prompt."

That's the architectural shift. The fix moves from PROMPT to REF. Every appearance problem becomes a reference-image problem, which is a fundamentally different category of problem to solve — you regenerate ONE image once and the fix persists across every future panel that attaches that ref. Versus the prompt-bloat path, which fixes the problem for ONE panel and requires the same prose to be reproduced in every subsequent panel.

L10, in code. Branch: [`refactor/refs-are-truth-prompts-are-action`](https://github.com/growcomics/claude-comic-pipeline/tree/refactor/refs-are-truth-prompts-are-action). PR not auto-opened — image-level A/B pending.
