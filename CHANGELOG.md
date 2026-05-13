# Changelog

All notable changes to the `claude-comic-pipeline` are tracked here.

This file is the **canonical source for what changed and why**. Any session (human or agent) editing this repo must append an entry here when it lands a meaningful change. Trivial cleanups can be skipped; anything that touches behavior, prompt architecture, the build-comic workflow, or a published reference doc must be logged.

Format: each entry is dated (YYYY-MM-DD), grouped in reverse-chronological order. Entries cite the relevant commit hash(es) and explain the *why* — what failure mode prompted the change, what the new behavior is, where readers can dig deeper.

Categories used per dated section: **Added** / **Changed** / **Fixed** / **Removed** / **Deprecated**. Skip categories with no entries.

---

## 2026-05-13

### Added
- **`CHANGELOG.md`** (this file) at repo root. From now on, every session that lands a meaningful change must append an entry here. See the header for the convention.

---

## 2026-05-12

### Added
- **L11 — Cartoony FMG proportions need explicit anchoring or the model regresses to realistic fitness** (`78815c5`, `7905431`). New lesson + supporting reference doc at `skills/comic-production/references/peak-body-scale.md`. Diagnosed from the April-claudemade and Supergirl runs: generated tier-4+ panels were visibly *smaller* than declared because (1) the lineup ref was attached on too few panels, and (2) prompt vocabulary like "match the muscle proportions of figure N" was too gentle, letting the model regress to its realistic-fitness prior. Two-part fix:
  - **Attachment rule broadened (replaces L5)**: `should_attach_lineup()` in `next_panel.py` now returns True on **stage-change OR full-body camera** (`front-full`, `3q-full`, `side-full`, `back-full`, `low-angle-front`, `low-angle-back`, `splash`). ECU and mcu skip. On Flow refs are free; the silhouette consistency gain outweighs slight composition risk.
  - **Vocabulary upgrade**: for any tier ≥ 2 panel, `compose_prompt()` emits a "cartoony hyper-FMG comic-book proportions, NOT realistic fitness modelling" anchor before the action delta, a tier-specific silhouette descriptor with dimensional anchors (e.g. tier 4: "shoulders 2x normal width with clear deltoid mass, large defined biceps and triceps, full powerful chest, ridged abdominal definition, strong sculpted quads"), a "Render the silhouette TO MATCH the lineup figure — do not approximate to a smaller realistic build" directive, and an explicit "NOT realistic fitness, NOT athletic" negation.
- **`peak-body-scale.md` reference doc** (`78815c5`): tier-by-tier silhouette catalog (1–9), working vocabulary, vocabulary to avoid ("athletic" / "toned" pulls toward realistic fitness), failure modes. Tier 4 explicitly called out as "the friction zone" — the threshold between realistic and cartoony where the model fights the cartoony commit hardest.

### Changed
- **L11 surgical scoping** (`7905431`): the original L11 prompt told the model to "match the EXACT silhouette" of the lineup figure, which the model interpreted holistically — copying hair, face, costume, pose from the lineup figure (a brunette in white tank + gray shorts). Validated on a real Higgsfield generation of `comic-april-mutagen-v2` panel `p15-01` (tier-6 splash). The new prompt declares the lineup a "PROPORTION reference ONLY" with an explicit do-NOT-borrow list: face, hair, skin tone, clothing, costume, pose, facial expression, lighting, setting, background. Resubmit produced cartoony-big proportions WITHOUT the lineup figure's hair/clothing bleeding through. Validation: see chat session record from 2026-05-12 around 23:00 PT.
- **`panel_status()` in `next_panel.py` now recognizes both folder-naming conventions** (`7905431`):
  - `pages/panels/<panel_id>/` (older form)
  - `pages/panels/panel-<panel_id>/` (newer form used by April + Supergirl projects)
- **`panel_status()` now recognizes both accepted-image conventions** (`7905431`):
  - `_accepted.txt` (one line naming the variant, e.g. `v1`) + `v1.png`
  - `v*_accepted.png` filename suffix (used by `rules_audit` + `compose_page`)
  
  Without these fixes `next_panel.py` was silently inoperable on projects using the panel- prefix + v*_accepted.png shape — which is what the rest of the pipeline emits. The lineup-bug debugging session surfaced both.

### Fixed
- **`find_lineup()` path resolution** (`0b963c6`). Supergirl panel 13 (tier-4-tears) rendered without the muscle-size lineup attached because `find_lineup()` only looked at `~/.claude/skills/comic-production/assets/`, which doesn't exist on dev machines. The repo-bundled lineup at `skills/comic-production/assets/muscle-size-lineup.png` was invisible. Worse: the prompt composer still wrote *"match figure N in the attached muscle-size lineup reference"*, invoking a ref that was never attached — model fell back to text interpretation and produced an undersized build. Now `find_lineup()` tries, in order: project-local override (`<root>/references/style/<filename>`), repo-bundled (script-relative), user-installed (`~/.claude/...`), plugin-installed (`~/Library/.../Claude/...` glob).
- **No-phantom-refs guardrail** (`0b963c6`). `compose_prompt()` takes a `lineup_attached: bool` and only references the lineup in the prompt when it's actually attached; otherwise falls back to verbal-only growth instructions. `build_plan()` emits a loud `MISSING_lineup` entry in `refs_to_attach` when `find_lineup()` returns None on a panel that needs one; `build-comic.md` hard rule says HALT on any `MISSING_*` entry — never invoke a ref that isn't on disk.

---

## 2026-05-11

### Added
- **L10 — References are the truth, prompts are deltas** (`1202441`). Major prompt-architecture change. Diagnosed from Supergirl panels 02 vs 05 (same `lex-lab-redsun` location, env ref attached, but rendered as visibly different chambers). Root cause: per-panel prompts re-described constants (character features, location architecture, costume design) that were already encoded in attached references. Model treated text and refs as competing signals and interpolated.
  
  Fix: delta-only prompt skeleton. Prompt body describes ONLY camera, action, expression, lighting state change, costume state change. Constants delegated entirely to attached references. Every prompt ends with the load-bearing render directive: *"render the attached references exactly as shown. Do not reinterpret character appearance, costume design, or location architecture from the prompt text. References override prompt text on all visual identity."*
  
- **Env chaining (corollary of L10)** (`1202441`). First panel in a hero location attaches `_source.jpg` (the DAZ stand-in render). Once accepted, that panel becomes the location's canonical anchor — every subsequent panel in the location attaches the *accepted* establishing shot's PNG as env ref, NOT `_source.jpg`. The DAZ render did its job on the first panel; the accepted shot is more specific and prevents the model from re-interpolating architecture each panel. `next_panel.py`'s `pick_location_anchor()` walks `accepted_history` for prior panels in the same location.
- **`page-composer` script + bundled Pillow renderer** (`ccddfb9`). `skills/page-composer/scripts/compose_page.py` lettering pass. Auto-detects single-image-per-page vs multi-panel mode from shotlist. Renders balloons, thought ellipses, jagged shouts, dashed whispers, yellow caption boxes, stroked SFX. Defaults to short stub tails when `speaker_position` isn't given; optional `--pdf` via `img2pdf` (lossless). SKILL.md rewritten for single-image-per-page primary mode; multi-panel as fallback. Upgrade path logged (HTML/CSS via headless Chrome, face-aware bubble placement, smarter grids, bundled fonts, per-character styling).
- **`continuity-check` two-mode workflow** (`ccddfb9`). `skills/continuity-check/scripts/rules_audit.py` for the deterministic first pass (asset presence, monotonic muscle_size_tier, coarse 3-level costume damage non-regression with carryover phrasing recognition, stage-change lineup ref presence, field hygiene). Vision audit is agent-driven (workflow encoded in SKILL.md) — Claude Reads each panel image and diffs against shotlist intent + prior panel. Rules-first because it's fast and free; vision pass focuses on pixel-level drift the rules can't see.
- **Bundled fonts** (`e4b6bd1`). `skills/page-composer/fonts/`: Comic Neue Bold (dialogue/captions) + Bangers (SFX), both SIL OFL 1.1. Verified via Pillow. Output is now deterministic across machines. Resolution order: env var → bundled → macOS system → Pillow default.
- **Act-boundary continuity gate** (`e4b6bd1`). `/build-comic auto` now runs the rules audit at every act boundary inside Stage 3 (resolved from optional `shotlist.acts` field, or fallback every 8 pages). HARD findings pause for sign-off; clean passes continue. Stage 4 reframed as the full-issue vision audit. Hard rule added: never skip the per-act rules audit — it's free and fast.
- **`next_panel.py` helper** (`6a1d2a5`). Reads shotlist + walks `pages/panels/` for accepted-version history, applies view-aware chaining (L1.5) to pick a state anchor, identifies refs to attach (face card, env ref, muscle lineup if stage-change), maps camera category to Flow aspect ratio, composes a starter prompt. Output intended for Claude during the per-panel Flow UI loop documented in `references/shotlist-driven-flow.md`.
- **`comic-status-board` skill** (`533423a`). Surfaces project status in chat at stage boundaries via `generate_status.py` (markdown) and `generate_composite.py` (Pillow grid renderer with 3 modes: references / generation / composition). STATUS artifacts written at project root (not buried in subfolders) per user feedback, and surfaced inline via Read so the user sees them in chat.

### Changed
- **Post-L7 pipeline rewrite** (`acfb319`). Integrated `comic-production` skill; dropped `souls` stage (Higgsfield Souls training, no longer used — identity is anchored via face card + body ref chaining), dropped `style` stage (replaced by style-lock as a *preset library*, not a pipeline stage), dropped `stylize` stage (current CGI render path produces the right look directly). Added `posting` stage stub (manual today). Added hard rules: no baked-in lettering (L7 Case B), job_id capture (L9), view-aware chaining (L1.5), camera variety check, env reference for hero locations, multi-character POSE VARIATION block, single-line Flow prompts.

---

## 2026-05-09

### Added
- **`style-lock` as preset library** (`d2497c0`). `photoreal-DAZ3D` as the default preset; extensible `styles/` folder. Style-lock survives the post-L7 rewrite as a reference library for shotlist authoring, not a pipeline stage that produces `style.md`.

---

## Earlier history

Earlier commits (`311d322`, `80cea83`) predate this changelog. Initial repo bootstrap, first stylization skill draft, AI-bootstrap warning, Higgsfield-first principle. See `git log` for details.

---

## Convention for future entries

When you land a change:

1. Append under today's date heading (`## YYYY-MM-DD`). Create one if it's a new day. Reverse-chronological — newest dates at top.
2. Use **Added** / **Changed** / **Fixed** / **Removed** / **Deprecated** categories. Skip empty ones.
3. Cite the commit hash(es) in parentheses. Use the short hash form (7 chars).
4. Explain the **why** — what failure mode the change fixes or what capability it adds. Future readers (humans and agents) should be able to understand the rationale without `git log -p`.
5. Cross-reference reference docs (`peak-body-scale.md`, `lessons-learned.md` L-numbers) where relevant.
6. Keep entries scannable but complete. Multi-paragraph entries are fine when the change has real depth (like L10 / L11); one-liners are fine for narrow fixes.
7. Append the entry **before** committing, so the commit message and changelog land together.
