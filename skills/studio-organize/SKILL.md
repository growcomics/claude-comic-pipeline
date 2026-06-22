---
name: studio-organize
description: >
  Organize a Comic Studio project's uploaded draft variants — pull them from the
  web Studio, pick the best of each beat (and group/rate the rest), and push the
  results back. The Studio counterpart of comic-folder-organizer: same judgment,
  but the images live in the web app (3dmusclecomics.com/studio) instead of a
  local folder. Trigger when the user says "organize the <project> studio
  project", "pick the best in Studio", "AI-organize <project>", or after they
  upload a batch of variants to a Studio project.
---

# Studio Organize

The Comic Studio (`3dmusclecomics.com/studio`) is where draft variants are
uploaded and tracked. This skill is the **AI "pick the best" pass** for it — it
runs through Claude Code (no server-side AI key), exactly like
`comic-folder-organizer`, but sources/sinks via the Studio bridge.

**Tool:** `studio/tools/studio_organize.py` (in this repo).
**Auth:** bridge key at `~/Documents/.3dmc-studio-bridge-key` (rotatable in
`studio/data/bridge.json`). Endpoint: `studio/bridge.php`.

## The one-command flow

```bash
cd ~/Documents/claude-comic-pipeline
python3 studio/tools/studio_organize.py list                 # see projects
python3 studio/tools/studio_organize.py pull <project>       # download + contact sheet + skeleton
# → Read the printed CONTACT SHEET, judge, edit the decisions.json
python3 studio/tools/studio_organize.py push <project> --decisions /tmp/studio-<project>/decisions.json --cover <best.png>
```

1. **pull** downloads every variant (thumbnails) to `/tmp/studio-<project>/`,
   builds `contact.png` grouped by beat (existing `group`, else auto-grouped by
   generation timestamp into `Beat 1..N`), and writes a `decisions.json`
   skeleton (groups pre-filled, ratings blank).
2. **Read `contact.png`** and judge. For near-identical variants where the
   winner isn't obvious at thumbnail size, `pull --full` (originals) or just use
   the in-app **lightbox** (Compare → ←/→ → Enter) which is full-res.
3. **Edit `decisions.json`** — for each beat set exactly one winner
   (`"rating":"good","accepted":true`); leave the rest `"unrated"` (don't mark
   clean variants "bad" — only genuine defects). Keep/adjust the `group` labels.
4. **push** writes it back; pass `--cover <file>` to set the project cover to the
   strongest hero shot. Confirm in the Studio (the kept ones show green + gold).

## Judging rubric (pick the winner of each beat)

Same craft bar as `skills/continuity-check/qa-checklist.md` /
`comic-folder-organizer`. Prefer the variant with, in order:

1. **Clean face** — eyes both correct, no melt/asymmetry, on-model likeness.
2. **Correct hands & anatomy** — finger count, no fused/extra limbs, plausible joints.
3. **Expression + pose** — registers the beat's emotion; dynamic, not flat/stiff.
4. **On-model** — body proportions / costume / hair match the cast refs; muscle
   tier consistent with neighbours.
5. **Cleanliness** — no warped props, no stray extras, no artifacts/seams; correct framing.
6. **Composition** — depth/tension over a flat camera-plane (per
   `staging-and-composition.md`).

If two are tied, prefer the one that best continues the previous beat's winner
(continuity). If *every* variant of a beat is defective, mark them all `unrated`
and flag it to the user as a re-generate.

## Grouping

Beats default to generation-timestamp groups (variants made together = one
panel/beat). Reorder beats in the app (▲▼ / type-a-number) — order is the
intended page/panel sequence. To regroup in a push, set each image's `group`.

## Analysis pass (annotate)

Beyond picking winners, attach an **AI analysis** to each image — shown in the
Studio as a 🔍/⚠ badge in the grid and a panel in the lightbox. Flow:

1. `pull <project>` (downloads + contact sheet, as above).
2. Read the images — contact sheet for a coarse pass; `pull --full` or the in-app
   lightbox (full-res) for fine defect-level detail.
3. Write a notes file — a JSON array, one entry per image:
   ```json
   [{ "file": "abc123.png",
      "caption": "Mid-transformation, kneeling, energy surge from the rock",
      "defects": ["left hand 6 fingers", "soft right eye"],
      "tier": "tier 3 / early growth",
      "tags": ["transformation", "outdoor"],
      "notes": "Continuity with prior panel's cape; best of this beat" }]
   ```
4. `annotate <project> --notes notes.json` — writes it back via the bridge.

Field guidance (genre-aware, per the corpus + `qa-checklist.md`):
- **caption** — one line: who, what's happening, the beat's emotion.
- **defects** — concrete visible flaws only: hands/fingers, face/eyes asymmetry,
  anatomy, warped props/costume, stray extras, artifacts/seams. Empty if clean.
- **tier** — transformation / muscle stage if visible ("tier 6 peak", "pre-TF").
- **tags** — reusable labels (transformation, FMG, costume-change, ECU, hero-pose…).
- **notes** — continuity vs neighbours, why it's the pick, what to fix.

Annotation and winner-picking compose — do both in one session: pull once, judge
+ analyze, then `push` (winners/grouping) and `annotate` (analysis).

## Notes

- Decisions are idempotent; re-running `push` with updated picks just overwrites.
- This does NOT generate or delete — it rates/groups/sets-cover. Deleting rejects
  stays a human action in the app.
- A future upgrade could move the judgment server-side (an in-app "Auto-pick"
  button via the Claude API) — that would need an Anthropic key on the host.
