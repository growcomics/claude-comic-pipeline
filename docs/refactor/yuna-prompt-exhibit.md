# Prompt exhibit — the bloat we're refactoring away

The user's L10 architectural principle: "references are the truth,
prompts are deltas." But the actual prompts have become walls of
appearance description. This doc captures the evidence.

## Why this doc uses chun-li-test, not Yuna

The brief asked for a Yuna prompt as exhibit, but:

- `projects/sample-01-yuna-cosmic-ascension/` ships WITHOUT a
  `shotlist.json` or `production-config.json`.
- The 5 accepted panels there were generated via Flow (browser, manual
  paste). The prompts were never persisted (that's the bug part 3c
  fixes). Re-running `next_panel.py` against the Yuna project is
  impossible without the shotlist.
- The README at `projects/sample-01-yuna-cosmic-ascension/final/README.md`
  references `references/characters/yuna-hoshino/face-card.png` and
  `references/locations/iss-cupola-env.png` — neither actually exists
  on disk (the project's `references/` only contains an empty `props/`).

So Yuna can demonstrate the SYMPTOM (visible drift across panels) but
not the CAUSE (the prompt content). For the cause, we use chun-li-test,
which has an intact shotlist and produces a worst-case realistic prompt
at peak conditions.

## The BEFORE prompt — `chun-li-test` `p06-01` peak tier-6

Captured by calling `compose_prompt` with peak conditions:
`lineup_attached=True, tier6_refs_attached=True, env_ref=set,
stage_change=True, anchor=p05-01`.

Stats:
- **11,509 chars**
- **1,770 words**
- **53 lines**

Full prompt: `docs/refactor/_chun-li-p06-BEFORE.txt`.

Breakdown of who emits what:

```
RENDER STYLE — Iray photoreal              ~50 words   (inline, KEEP)
CAMERA — base framing                       ~15 words   (inline, KEEP)
SUBJECTS                                     ~3 words   (inline, KEEP)
BEAUTY ANCHOR — L15                         ~53 words   (DELETE — face card)
HAIR — L22                                  ~20 words   (KEEP — state delta)
STYLE — L11 cartoony FMG anchor            ~160 words   (REWRITE — match body ref)
ACTION DELTA                                ~80 words   (inline, KEEP)
LIGHTING STATE                               ~6 words   (inline, KEEP)
LINEUP PROPORTIONS — L11 surgical scope    ~700 words   (REWRITE — match body ref)
TIER-6 REINFORCEMENT — L29                 ~210 words   (REWRITE — match body ref)
ENVIRONMENT — ref anchor                    ~40 words   (KEEP — use ref)
STATE ANCHOR — L1.5                         ~40 words   (KEEP — use ref)
RENDER DIRECTIVE — L10                     ~100 words   (REWRITE — one-line match)
REF SAFETY — L21                            ~45 words   (KEEP — safety)
POSE & ANATOMY — L18                        ~45 words   (KEEP — safety)
MANDATORY ANCHORS                           ~45 words   (GUT — strip appearance bits)
LETTERING — L19 2D overlay                 ~300 words   (KEEP — bubble structure)
CLOSING ANCHOR — CGI scope                  ~40 words   (KEEP — render scope)
```

Of those 1,770 words, **~1,283 words (~73%) describe the character's
appearance.** That whole block is duplicative with the attached refs.

## The projected AFTER prompt — same panel, refactored rules

With L15 deleted, L17 / L10 reduced to one-line match directives, L11's
1900-char tier directive reduced to one line, and L29-L32 directives
reduced to one shared match line:

```
Estimated 3,000-3,500 chars
        ~480-560 words
        ~22-28 lines
```

A ~70% reduction in prompt token count. More importantly, every word
that remains is either:
- describing what the character is DOING in this panel (action delta,
  camera, lighting, hair state, mood),
- pointing at an attached reference image to MATCH (face card, body
  tier, env, prior panel),
- describing what NOT to render (anatomy coherence, ref safety,
  accessory suppression),
- or describing the lettering / overlay layer (bubbles, SFX).

The refactored prompt would say "match the attached face card" once
and rely on the face card to carry the canonical Chun Li look. The
700 words of "deltoids 3x normal mass, biceps as wide as the waist,
breast scale slightly larger than figure 6 shows" become "match the
attached body-tier reference exactly."

That's L10 enforced in code.

## The actual AFTER prompt

See `docs/refactor/validation/` for the post-refactor render of the
same panel after the new composer runs.
