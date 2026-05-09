# Style presets

Each subfolder is one named visual style. The default preset is
`photoreal-daz3d/` (Bay Watch / Lana & Lacy aesthetic). Additional presets
ship alongside it as siblings.

## Folder shape

```
styles/
├── README.md                    # this file
├── photoreal-daz3d/             # default
│   └── preset.md
├── ink-line/                    # secondary example
│   └── preset.md
└── <new-slug>/                  # add new presets here
    └── preset.md
```

Each preset folder contains exactly one required file:

- `preset.md` — a self-contained, copy-paste-ready `style.md` template plus
  the rationale for the choices and a "when to pick this preset" note.

Optional siblings inside a preset folder (none required):

- `sample.png` — a locked-in reference render for drift checks.
- `notes.md` — additional notes / per-character prompt fragments / etc.

## How to add a new preset

1. Pick a slug — short, lowercase, hyphenated, descriptive of the aesthetic
   (e.g. `manga-screentone`, `watercolor-eurocomic`, `noir-bw`).
2. Create `styles/<slug>/preset.md`. Copy the structure from
   `styles/photoreal-daz3d/preset.md` (Template block + rationale + when to
   pick this preset). Be **specific** — vague descriptors drift; specific
   ones hold.
3. Test on a known shot before declaring the preset locked. Save the chosen
   reference render as `styles/<slug>/sample.png` if you want a drift-check
   anchor.
4. Update the table below.

That's the whole operation: one folder, one file, one row in the table. Do
not edit `SKILL.md` to add presets — the skill discovers them from this
folder.

## Available presets

| Slug | Default | Aesthetic | When to pick |
|------|---------|-----------|--------------|
| [`photoreal-daz3d`](photoreal-daz3d/preset.md) | **yes** | DAZ3D Iray photorealistic 3D, 3D Muscle Comics house style | Bay Watch / Lana & Lacy and any photoreal-3D comic |
| [`ink-line`](ink-line/preset.md) | no | Modern indie / Eurocomic ink-line, cel-shaded, limited palette | Stylized illustrated projects, flashback chapters |

## Switching the default

The default preset is whichever folder is referenced by `SKILL.md`'s
"Default preset" line. To change it:

1. Update the `default` value in the new preset's `preset.md` header.
2. Set `default: no` on the previous default preset.
3. Update the "Default preset" line in `skills/style-lock/SKILL.md`.
4. Update the table above.

Do not change the default mid-project — it invalidates every previously
generated panel's continuity. A new default applies to new projects only.

## Per-panel style tagging (mixed-style books)

For chapters or sequences that need a different look (flashback, dream,
side-story), don't rewrite `style.md`. Tag the affected panels in
`shotlist.json`:

```json
{ "panel_id": "ch4-p07-a", "style": "ink-line", ... }
```

The panel-prompt builder loads `styles/<slug>/preset.md` for the tagged
panels and falls back to the project default for the rest.
