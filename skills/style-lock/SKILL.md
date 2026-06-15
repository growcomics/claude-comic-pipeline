---
name: style-lock
description: Lock a single visual style across an entire comic project — pick a preset (default photoreal-DAZ3D), copy its template into a project-level style.md, and enforce mandatory prompt prefix/suffix/negative on every panel. Use when the user wants a consistent look across pages, define the style of a comic, prevent style drift between panels, build a style guide, lock model parameters, or pick a model for the project. Trigger phrases include "lock the style", "style guide for the comic", "consistent look", "style across panels", "no style drift", "pick the model", "match the style of X".
---

# Style Lock

Lock a project's visual style up front and enforce it on every panel prompt.
Without this, generated panels drift across pages — different line weights,
different palettes, different rendering — even when the same Soul is used.

`style-lock` produces a `style.md` at project root that the generator and
`page-composer` both read. The starting point is a **preset** in
`styles/<slug>/preset.md`. The default preset is **`photoreal-daz3d`** — the
DAZ3D Iray "3D Muscle Comics" house style used by Bay Watch / Lana & Lacy.

## When this skill is the right tool

- Start of a new comic project, before any panels are generated
- "Make sure all panels look the same"
- "Lock the style"
- "Match the style of [reference comic / artist]"
- Mid-project rescue: pages 1–4 look fine, pages 5–8 drifted

If a `style.md` already exists, this skill updates it; it doesn't overwrite
without explicit confirmation. If only one or two panels drifted, that's a
generation-prompt bug, not a style-lock issue — fix the prompt, don't relock.

## Default preset

**`styles/photoreal-daz3d/preset.md`** — photorealistic DAZ3D Iray render,
3D Muscle Comics house style, 3:4 portrait, Nano Banana 2 Pro, golden-hour
outdoor lighting, no ink lines, baked 2D lettering (L19). This is the default for any
new comic project unless the user explicitly asks for a different aesthetic.

The previous ink-line example template now lives at
`styles/ink-line/preset.md` as a secondary preset for stylized projects.

See `styles/README.md` for the full preset list, the folder shape, and how
to add a new preset (one folder, one `preset.md`, one row in the table — no
SKILL.md edits required).

## Output: `style.md` at project root

Every preset's `preset.md` contains a self-contained **Template** block.
Copy that block verbatim into `style.md` at the project root, fill the
placeholders (`<project>`, `<date>`, character energy-color rules, suit /
wardrobe state by chapter, sample-shot reference page), and lock the file.

The template's required sections:

- **Model** — name, aspect, resolution, batch, seed strategy
- **Mandatory prompt prefix / suffix / negative** — appended verbatim to
  every panel prompt; the negative is load-bearing
- **Project-specific hard rules** — character energy colors, suit state by
  chapter, scale tiers
- **Lettering** — font, balloon stroke, caption tint, SFX styling (the
  baked-overlay style targets per L19; lettering bakes into the render, `page-composer` is layout + PDF only)
- **Banned** — explicit list of looks the project must not produce
- **Style sample reference** — the locked-in test image for drift checks

For Bay Watch / Lana & Lacy, the `lana-lacey-skill` repo's
`series-profile.md` §2 ships a pre-filled version of the photoreal-DAZ3D
template with energy colors and suit-state rules already populated — copy
that block instead of filling the template by hand.

## Workflow

### 1. Pick the preset

Default to **`photoreal-daz3d`**. Only deviate when the user explicitly asks
for a different aesthetic ("ink-line indie look", "watercolor", "manga
screentone", etc.). For deviations:

1. Check `styles/` for an existing preset that fits.
2. If none fits, follow `styles/README.md` to add a new preset folder
   *before* writing `style.md`. The preset is the durable artifact; the
   project's `style.md` is just an instantiation.

#### Quick-select triggers (short signals in the build prompt)

A user can opt into a non-default preset with a short token anywhere in the
request — no need to describe the aesthetic. When you see one of these
signals, select the mapped preset and skip the "distill a new preset" steps
(2–3) entirely; the preset already exists. The default stays
`photoreal-daz3d` unless a trigger is present.

| If the prompt contains… | Select preset |
|---|---|
| `grow-island`, `grow island style`, `GI style`, `#grow-island`, `style: grow-island` | **`grow-island`** |
| `ink-line`, `indie ink look`, `style: ink-line` | `ink-line` |
| (nothing / `daz3d`, `photoreal`, `default`) | `photoreal-daz3d` |

Matching is case-insensitive and substring-based. Recommended canonical
signal to teach users: **just put `grow-island style` in the prompt** (e.g.
"build chapter 2 in grow-island style"). For per-panel exceptions inside an
otherwise-default book, tag the panel with `"style": "grow-island"` in
`shotlist.json` instead of switching the whole project.

### 2. Gather style refs (only when distilling a new preset)

This step is for *new presets*, not for projects using an existing preset.
If you're starting a Bay Watch chapter using `photoreal-daz3d`, skip to
step 3.

If style refs aren't already in `references/_style/`, delegate to
`reference-gathering`: *"mood-board, 12 images, [genre + era + artist]
aesthetic"*. Don't proceed without 5+ style refs — single-image style
anchors don't generalize.

Read all style refs. Write a 5–10 attribute distillation. Be **specific**.
Vague descriptions ("modern", "dynamic") produce drift; specific ones
("heavy 2pt outer line, no rim light, 35° hard shadows from upper-left")
hold.

Attributes to capture:

- Line weight (outer vs interior, in approximate point sizes) — or, for
  photoreal presets, render engine / skin micro-detail level
- Color approach (palette breadth, saturation, dominant hues)
- Lighting (key light direction, hardness, presence/absence of rim)
- Rendering (cel-shade / painterly / inked / screentone / photoreal-3D /
  mixed)
- Era/genre cue (90s manga, 70s underground, modern indie, retro
  Eurocomic, photoreal-3D, etc.)
- Forbidden traits (photoreal-vs-illustrated, 3D-vs-2D, stock-flash,
  anime-eyes if not anime)

Save the new preset to `styles/<slug>/preset.md` and update the table in
`styles/README.md`.

### 3. Copy the preset's template into `style.md`

Open the chosen preset (e.g. `styles/photoreal-daz3d/preset.md`). Copy the
**Template** block into `style.md` at the project root. Fill:

- `<project>` (chapter / book name)
- `<date>` (lock-in date)
- Character energy-color rules (project-specific hard rules — never blanks)
- Suit / wardrobe state by chapter
- Sample-shot reference page (a known-good panel from this project, or the
  preset's bundled `sample.png` if no project panel exists yet)

Lock the file.

### 4. Test on a known shot

Pick a representative panel from `shotlist.json` (a character + a location,
preferably with a Soul already trained and reference images attached).
Generate it with the full prefix + suffix + negative from `style.md`. `Read`
the result.

- If it matches the preset's aesthetic and looks like the character: lock
  the parameters; save as `pages/_style-sample.png` for later drift checks.
- If it drifts: tighten the prefix/suffix wording in `style.md` and retry.
  Most drift comes from vague style descriptors that the model under-weights.
  Strong cues ("DAZ3D Iray photorealistic render", "heavy 2pt outer line")
  survive better than weak ones ("photoreal", "bold lines").
- **Likeness drift, not style drift?** That is almost always missing
  reference-image attachment, not a style-lock problem. See "Reference
  attachment is the primary identity lever" below.

### 5. Wire into generation

Generation must:

1. Read `style.md`
2. Prepend the prefix to every panel prompt verbatim
3. Append the suffix verbatim
4. Pass the negative prompt
5. Use the locked model + parameters
6. Attach the canonical face/hair reference image and the closest canonical
   full-body shot for any recurring character in the panel (this is a
   pipeline contract, not a style-lock contract — but the panel-prompt
   builder must enforce it for the locked style to actually hold likeness)

Document this contract in `style.md` so it survives handoffs to other
workflows or re-runs.

## Reference attachment is the primary identity lever

Empirically (GROA-2 audit, 2026-05-09), reference-image attachment — not
Higgsfield Souls — is what carries character likeness through the locked
style. Souls are a safety net. If the panel-prompt builder skips ref
attachment, even a perfectly locked photoreal style produces a generic-face
render that *looks* on-style but isn't the right character.

Treat ref attachment as a hard requirement of the photoreal preset, not as
optional polish. The `photoreal-daz3d/preset.md` file calls this out
explicitly; carry the same rule forward into any new preset that involves
recurring characters.

## Drift detection

Re-run the sample shot every ~10 panels generated, or any time the user
notices "this page looks off". Compare to `_style-sample.png`. If the new
render diverges in line weight / palette / lighting / skin texture:

- **Sample also drifted** → the model was bumped (provider change), or
  parameters changed. Investigate root cause.
- **Sample is fine, only page 7 drifted** → the prompt skipped the
  prefix/suffix, dropped the ref attachment, or the panel-prompt builder
  has a bug.

Fix the root cause; don't paper over by tweaking prompts panel-by-panel.

## Hard rules

- **Default to `photoreal-daz3d`.** Only deviate when the user explicitly
  asks for a different aesthetic, and document the choice in `style.md`.
- **Lock once, change deliberately.** Mid-project parameter changes
  invalidate every previous panel's continuity.
- **Prefix and suffix go on every panel — no exceptions.** "Quick test"
  panels still need them or they'll look wrong sitting next to locked
  panels.
- **No "match this random image" without distillation.** Pinning aesthetic
  to a single image works for one panel, not 50. Build a preset first.
- **The negative prompt is load-bearing.** Don't drop it for terseness —
  banning the wrong aesthetic (cartoon for photoreal, photoreal for
  ink-line) is what keeps the generator from defaulting to its training-set
  average.
- **One `style.md` per chapter at most.** If chapter 4 needs a different
  style for a flashback, tag those panels with `"style": "<slug>"` in
  `shotlist.json` — don't rewrite `style.md`.
- **Adding a preset is a single-folder operation.** Create
  `styles/<slug>/preset.md` and add a row to `styles/README.md`. Do not edit
  `SKILL.md` to add presets.

## Common asks

- **"Match [artist]'s style"** — gather 8–12 of that artist's panels via
  `reference-gathering`, distill into a new preset under `styles/<slug>/`,
  test. Note: if the artist is alive and copyrighted, the user is
  responsible for the licensing call; flag it.
- **"Different style for the flashback pages"** — tag those panels with
  `"style": "ink-line"` (or whichever preset slug fits) in `shotlist.json`.
  Don't fork `style.md`.
- **"Style drifted on page 7"** — run the sample-shot drift check first to
  localize the problem (model vs. prompt vs. parameters vs. missing ref
  attachment).
- **"I don't have refs, just a vibe"** — push back; if a new preset is
  needed, gather 5+ style refs first. A vibe-only preset drifts within
  3 panels. If the existing default preset fits, use it.

## Hand-off

After `style.md` is locked, generation can begin. `page-composer` will also
read this file for font/balloon/caption/SFX styling — those keys live under
"Lettering" in the preset template.
