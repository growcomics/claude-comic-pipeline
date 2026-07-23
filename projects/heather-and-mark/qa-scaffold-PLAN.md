# QA-Scaffold Plan — Heather & Mark fix pass

Prep doc only. No qa/ gate script was modified anywhere in the repo, no generation was run,
`integrity.py` was never executed. This is the scaffolding plan for the ~35-job fix pass the
owner approved (7 blockers + 26 pure script-format-lettering re-letters + 2 new wide-establish
beats for the 14.5in chapter — see the count reconciliation note in §5).

## 1. Donor chosen: `projects/ultra-gal-origin/qa/`

Four candidates had a real `qa/` chain: `manila-bay-rising`, `not-so-supra-man`, `tmb-daz-study`,
`ultra-gal-origin`. (`cheer-ascension/qa/` only has `judge-rubric.md` + empty `receipts/`/`staging/`
— no scripts, disqualified.)

Verified directly with `shasum -a 256 -c MANIFEST.sha256` in each project (read-only — this is
just checking hashes, not running `integrity.py`):

| Project | Manifest check | compose.py lineage |
|---|---|---|
| `manila-bay-rising` | **all 6 hashes OK** | Oldest/simplest version — docstring says "Ch1 scope: max muscle tier 3... No anchor-swap / no t9 / no torn multi-pass machinery." Different hashes from the other three; a scoped-down early fork. |
| `tmb-daz-study` | **all 6 hashes OK** | Byte-identical to ultra-gal-origin's 6 scripts (`diff` = empty). Same "v2 (user-blessed fix batch)" generation. Thinner support-file set (no `judge-rubric.md`, no `vfx-style-bible.md`, no `prompt-template-v4.json`), only 17 receipts — a smaller production run. |
| **`ultra-gal-origin`** | **all 6 hashes OK** | Same v2 lineage as tmb-daz-study, byte-identical scripts. Most recent bless date (Jun 15), 35 real banked receipts (vs. tmb-daz-study's 17), fuller `staging/` (8 entries vs. 5), has `vfx-style-bible.md`. The most complete *currently valid* example of this chain generation. |
| `not-so-supra-man` | **compose.py: FAILED** (`shasum -a 256 -c`: live hash `3a8254d8…` ≠ manifest's `b98c0c58…`) | Has the newest logic on top of v2 — an added "L34 subject staging" block (`STAGING_TYPES`, `STAGING_DIRECTIVE`, `FLAT_LINEUP_RE`, a `D14` gate) — confirmed via `diff` against ultra-gal-origin's compose.py. But its `compose.py` was edited *after* its own `MANIFEST.sha256` was last generated (file mtimes: manifest 6/11 20:45, compose.py 6/14 14:45) and was never re-blessed. Per `integrity.py`'s own logic this project's gates are **currently locked** — right now, running any protocol script in `not-so-supra-man/qa/` would print `GATE INTEGRITY FAILURE` and exit 2. Disqualified as a donor: cloning a broken chain would clone the breakage.

**Chosen: `ultra-gal-origin`.** Fully self-consistent (all 6 guarded files verified against its own
manifest), the most evolved lineage among the *valid* candidates, and the most real production
mileage (35 banked, chain-verified receipts) to model heather-and-mark's inputs on.

(Note: `not-so-supra-man`'s L34 staging logic is objectively newer code than what ultra-gal-origin
ships. If the owner wants that logic in heather-and-mark's clone too, the move is to have
`not-so-supra-man` re-blessed first — `python3 qa/integrity.py --rebless --i-am-the-user` after
reviewing `git diff` there — then clone from it instead. Not done here; flagging for the owner's
call, not assuming it.)

## 2. Re-blessing verdict: **not needed for the clone itself.** Read on for a caveat.

`MANIFEST.sha256` hashes **bare filenames only** — no project path is baked into the hash file
(confirmed by `cat`-ing all four manifests: every line is `<sha256>  <filename>`, e.g.
`b98c0c581c…  compose.py`). `integrity.py`'s `verify_or_die()` resolves everything against
`HERE = os.path.dirname(os.path.abspath(__file__))` — i.e. its own directory — and none of the 6
guarded scripts reference a project name or absolute path anywhere (grepped all 5 I read in full;
every file path they touch — `shotlist.json`, `pages-plan.json`, `references/ref-ledger.json`,
`pages-log.json`, `qa/staging/<id>.json`, `qa/receipts/…` — is relative to cwd/project root).

**Consequence:** a byte-for-byte clone of `qa/{integrity.py, compose.py, audit_prompt.py, bank.py,
verify_chain.py, preflight.py, MANIFEST.sha256}` into `projects/heather-and-mark/qa/` will pass
`shasum -a 256 -c MANIFEST.sha256` immediately — the manifest travels with its files as one unit.
**No owner re-blessing is required for the plain clone.**

**The caveat (see §6, this is the plan's biggest finding):** the clone gives you a working,
self-verifying gate *harness*, but `compose.py` as shipped has no job kind for "i2i-edit this
exact existing accepted image, changing only X" — which is what ~33 of the ~35 fix jobs actually
need. Bending the existing `page:`/`sheet:` kinds to fit is possible but lossy (§6). The clean fix
is a small, owner-reviewed extension to `compose.py` adding an `edit:<panel_id>` kind — and *that*
edit, because it touches a guarded file, **would** lock all gates until the owner runs
`integrity.py --rebless --i-am-the-user` after reviewing the diff. So: re-bless not needed to
stand the chain up; re-bless *would* become necessary only if the owner accepts the recommended
`compose.py` extension in §6.

## 3. What compose.py actually requires (read from `ultra-gal-origin/qa/compose.py` + its inputs)

Two job kinds, both invoked as `python3 qa/compose.py --job <kind>:<id>`:

- **`sheet:<id>`** — character turnaround/model-sheet jobs. Reads `references/turnaround-specs.json`
  (`{"sheets": [{"id", "prompt", "attach": [...], "save": "...", "gate": "..."}]}`, or a multi-pass
  variant with `pass_1`/`pass_2`/`pass_3_turnaround` sub-objects for anchor-swaps) and
  `references/ref-ledger.json` (for the self-heal/bootstrap check — if the target wardrobe state's
  turnaround is already banked, it forces pointer language instead of prose re-description).
  Hard gates: `len(attach) >= 2` (**unconditional — no genesis/bootstrap bypass in this version**,
  unlike the "genesis" concept referenced in manila-bay-rising's older docstring) and the literal
  word `"silhouette"` must appear somewhere in the prompt (D7 scale-anchor check), or compose
  refuses.
- **`page:<panel_id>`** — a single finished panel. Reads, all at **project root** (not under `qa/`):
  - `shotlist.json` — `{cast[], pages: [{panels: [{panel_id, characters[], location, camera,
    action, costume_state, muscle_size_tier: {char:int}, continuity_refs[], dialogue[], captions[],
    sfx[]}]}]}` (exact shape confirmed by reading ultra-gal-origin's file in full)
  - `pages-plan.json` — `{"pages": [{"id", "camera", "aspect"}]}`
  - `references/ref-ledger.json` — `{"characters": {char_id: {"face": {...}, "turnaround_<key>":
    {...}}}, "scene_ladders": {location: {"wide"|"medium"|"close": {"flow_id": "..."}}}}`
  - `pages-log.json` — `{"done": {panel_id: {"flow_id", "disk", "chain": {"receipt","audit",
    "verdict","verdict_tags","prompt_sha"}}}}`, used ONLY to satisfy `continuity_refs`
  - `qa/staging/<panel_id>.json` — **required whenever a panel has ≥2 characters** (`{char_id:
    {"position","pose","expression","turnaround_key"}, "spatial_rules": [...], "lighting": "..."}`)

  Hard gates in `compose_page()`: every character needs `ledger.characters[c].face` truthy (D1);
  a resolvable wardrobe turnaround via `pick_turnaround()`, which pattern-matches the panel's
  `costume_state` string against tier/keyword rules (D4/D11); every `continuity_refs` entry must
  be a `pages-log.json["done"]` entry that **has a `"chain"` key** (D1 — a chainless/legacy entry
  does NOT satisfy this, it explicitly checks `"chain" not in rec`); and — easy to miss — every
  panel's `location` (unless it's the donor's own `"lab-exterior"` literal, which is meaningless
  here) triggers a **scene-ladder check**: `ref-ledger.json["scene_ladders"][location][distance-class]`
  must exist with a `flow_id`, where distance-class is derived from `camera` via a fixed
  wide/medium/close bucket table. No matching rung → refusal (D8).

- **Independent second gate**: `audit_prompt.py` re-derives the prompt sha, checks it against the
  receipt (catches any hand-edit — "Layer 0 bypass"), then lints for banned appearance/VFX
  language, scale-risk phrases without a height clamp, minimum attach counts (**sheet ≥2, page
  ≥3** — note this is *stricter* than `compose_sheet`'s own D1 and applies **unconditionally**,
  it does not know about any genesis/bootstrap flag), the style-anchor phrase, and — for pages
  that attach a turnaround — the anti-reference-bleed negative.
- **`bank.py`** refuses to record anything without all three: `<job>.receipt.json` +
  `<job>.audit-pass` (hash-matched to the receipt) + `<job>.verdict.json` with `"pass": true`
  (the fresh-context subagent's post-flight judgment — never the generator grading itself, per
  `CLAUDE.md`). On success it writes into `references/ref-ledger.json` (sheets, via
  `--ledger-key char.key`) or `pages-log.json["done"]` (pages).
- **`verify_chain.py`** is a read-only report: counts ledger/pages-log entries with vs. without a
  `"chain"` key. Its own comment says entries without a chain are **"pre-protocol or bypassed —
  expected here"** for legacy data; it does not fail the run, it just lists them. This is more
  tolerant than `compose_page`'s own D1 continuity check (see §6).

## 4. Exactly what to clone vs. what NOT to clone

**Clone byte-for-byte** (the manifest binds to exact bytes, so partial/re-typed copies would break
the hash even with identical logic — use `cp`, not retyping):
```
projects/ultra-gal-origin/qa/integrity.py       -> projects/heather-and-mark/qa/integrity.py
projects/ultra-gal-origin/qa/compose.py         -> projects/heather-and-mark/qa/compose.py
projects/ultra-gal-origin/qa/audit_prompt.py    -> projects/heather-and-mark/qa/audit_prompt.py
projects/ultra-gal-origin/qa/bank.py            -> projects/heather-and-mark/qa/bank.py
projects/ultra-gal-origin/qa/verify_chain.py    -> projects/heather-and-mark/qa/verify_chain.py
projects/ultra-gal-origin/qa/preflight.py       -> projects/heather-and-mark/qa/preflight.py
projects/ultra-gal-origin/qa/MANIFEST.sha256    -> projects/heather-and-mark/qa/MANIFEST.sha256
```
All 6 guarded files must come along together — `integrity.py` also checks `set(want) ==
set(GUARDED)`, so a partial clone (e.g. skipping `preflight.py`) fails the file-list check even if
every present hash matches.

**Create empty, do not copy contents:**
```
projects/heather-and-mark/qa/receipts/   (mkdir only)
projects/heather-and-mark/qa/staging/    (mkdir only)
```

**Do NOT clone** `defect-registry.json`, `judge-rubric.md`, `vfx-style-bible.md`,
`prompt-template-v4.json` — ultra-gal-origin doesn't even have the last two under this donor
selection issue aside, these are the *donor's own creative content* (Lois/Superman/Lucille
characters, Ultra Woman's tiers and wardrobe rules). None of the 6 guarded scripts read
`defect-registry.json` or `judge-rubric.md` directly — they're reference material the **post-flight
fresh-context judge subagent** reads per `CLAUDE.md` step 4 ("judges it against the registry
rubric"), not machine-enforced inputs. heather-and-mark should get its own, and the natural,
already-in-hand source is `qa-report.md` itself: recommend using it directly as the post-flight
judge's rubric ("does this regenerated panel resolve the specific qa-report.md defect line it was
assigned to fix, without introducing a new one — camera/wardrobe/identity/tier held per the job's
constraints?") rather than authoring a generic defect-registry.json from scratch. Cheaper and more
targeted than porting Ultra Woman's registry.

## 5. Job-count reconciliation (owner said "~37")

Owner's framing: 7 blockers + 28 script-format lettering re-rolls + 1-2 new wide shots ≈ 37.
Two panels — **059 and 062** — are blockers *and* appear in the qa-report's 28-panel systemic
prefix-leak list. Fixing 059's garbled/orphan bubble and 062's stat-regression necessarily
touches the same lettering layer as the prefix-strip, so each is **one job**, not two. That
collapses the count to **7 blockers + 26 lettering-only panels + 2 new beats = 35 jobs**, not 37.
Documented here rather than padding the list to hit a round number. See `fix-jobs.json`.

Also explicitly OUT OF SCOPE for this ~35-job pass (owner asked for blockers + the systemic
lettering row + new wides only — not a full should-fix sweep):
- **061, 069** — duplicate-caption defects (same defect *class* as blocker 007, but not in the
  named 28-panel systemic row) — cheap follow-up candidates, not included.
- Clothing-continuity / prop-morph / mirror-logic / extras-duplication should-fix items that
  happen to land on a panel also getting a lettering fix (e.g. 021's tape-prop morph, 042's
  coverage gap, 046's costume reset, 053's duplicate gym extras) — these panels get **lettering-
  only** touch-ups here; their other defects are untouched and remain in the qa-report backlog.
- The **065→068 reorder** suggestion — a manifest/reading-order change, not a generation job.

## 6. The impedance mismatch (read this before running anything)

`compose_page()` is built for **prospective, forward** production: shotlist entries, ledger
turnarounds, and scene-ladder rungs all get populated *as panels are generated in order*, and each
new panel chains off ones already banked *through this same chain*. heather-and-mark's 69 panels
were already produced and accepted through a different/earlier process — there is no existing
`shotlist.json`/`ref-ledger.json`/`pages-plan.json`/`pages-log.json` for this project at all, and
the fix pass is fundamentally a **retrofit edit** (re-letter text, or narrow anatomy correction) on
**already-existing accepted images**, not a request for fresh panels.

Concretely, using `page:<panel_id>` for a fix job as coded requires, before compose will even run:
1. A `shotlist.json` entry for that panel (characters/action/camera/costume_state/tier).
2. A `ref-ledger.json` entry with a `face` + a matching `turnaround_<key>` for every character in
   frame, resolvable by `pick_turnaround()`'s keyword/tier matching against `costume_state`.
3. A `ref-ledger.json["scene_ladders"][location][distance-class]` rung for that panel's location —
   **every** location we touch (gym, beach, living-room, bedroom-a, bedroom-b, hotel-room,
   clothing-store, city-street, dinner-table) needs at least one rung authored; none of
   heather-and-mark's locations match the donor's hardcoded `"lab-exterior"` skip.
4. A `pages-plan.json` entry (`id`/`camera`/`aspect`).
5. If `continuity_refs` is declared non-empty, that referenced panel must be a `pages-log.json`
   `"done"` entry **with a `"chain"` key** — legacy/backfilled entries without one explicitly fail
   this check (D1), even though `verify_chain.py` would tolerate them as "pre-protocol."

None of that infrastructure encodes "keep this exact image, change only the baked text" — the
composed prompt is a **fresh from-refs generation instruction**, with no field anywhere for
"attach panel 009.jpeg itself as the sole edit source." The closest existing precedent is
`compose_sheet`'s self-heal branch, but it only ever points at a *ledger-recorded turnaround*, not
an arbitrary existing panel file, and it's gated by the sheet-type minimum-2-refs + mandatory
`"silhouette"` sentence — both irrelevant, and actively unwanted, for a single-panel lettering
retouch (`"silhouette"` boilerplate would ask the model to draw a scale-comparison silhouette into
a panel that shouldn't change at all).

**Two honest paths, for the owner to pick — not decided here:**

- **(A) No script change (fallback).** Backfill the infrastructure above (items 1-5), declare
  `continuity_refs: []` on every fix-panel shotlist entry to dodge the D1 continuity trap (we are
  not truly forward-chaining these — see below), and run fix jobs as ordinary `page:` jobs. This
  produces a **fresh reroll** of the panel from refs/turnaround, not a true i2i edit — real risk
  of unwanted drift (background, pose, exact framing) beyond the intended fix, which is exactly
  the failure class the whole gate system exists to prevent. Workable for the 3 `i2i re-render`
  jobs below (007, 032, 033) where a materially different render is the point anyway; risky for
  the 30 `i2i re-letter` jobs where pixel-identical-except-text is the entire goal. Also note:
  CLAUDE.md's submit step says "attach exactly the receipt's list" — there is no protocol-legal
  way to *additionally* hand-attach the existing accepted panel image as an extra i2i source at
  submit time without deviating from the receipt, so (A) cannot be quietly patched around this way
  either.
- **(B) Recommended.** Ask the owner to review and bless a small `compose.py` addition — a third
  job kind, e.g. `edit:<panel_id>`, that reads a lighter per-panel spec (existing panel path +
  correction instruction) and composes the already-validated "keep the exact same camera angle,
  framing, character poses, expressions, speech bubbles, and composition as the source image —
  [narrow instruction]" pattern that's already documented and production-validated in
  `skills/comic-production/references/cinematic-framing.md`'s "Lighting-pass fragments" section
  (28/28 composition-lock hold rate cited there for a similar i2i-attach-and-retouch flow). This
  is a guarded-file edit — it will lock all 6 gates until the owner runs
  `python3 qa/integrity.py --rebless --i-am-the-user` after reviewing the diff, per protocol. That
  re-bless is a genuinely different question from "does cloning need a re-bless" (§2's answer, no)
  — it's "does *improving* the clone for this project's actual need require one" (yes, if the
  owner wants it).

`fix-jobs.json` is written to be useful under either path: each job's `constraints` block states
the edit intent in plain terms (what must stay identical, what must change) independent of which
compose.py code path eventually executes it, and `compose_job_hint` names the honest current gap.

## 7. Panels needing `qa/staging/<panel_id>.json` (2+ characters in contact)

Per `compose_page()`'s D9/D13 gate (`len(chars) >= 2` -> staging file required). Cross-checked
against the fix-job list and the transcription's scene notes — the two-character panels in this
batch are the tape-measure/hotel-room ritual beats and the bedroom beats:

- **021** (hotel/living room, tape from drawer — Mark + Heather)
- **023** (hotel room, hands clasped — Mark + Heather)
- **027** (bedroom, faces close — Mark + Heather, 2 dialogue lines)
- **035** (bedroom, hand on chest — Mark + Heather, 2 lines)
- **037** (bedroom massage — Mark + Heather, 2 lines)
- **038** (bedroom massage continued — Mark + Heather, thought bubble + line)
- **043** (living room, Heather standing over seated Mark)
- **047** (living room, bridal carry — Mark + Heather, 2 lines)
- **049** (ECU interlaced hands — Mark + Heather, 2 lines, Mark mostly out of frame)
- **063** (bedroom mirror, Mark embracing from behind)
- **068** (bedroom, shoulder kiss — Mark + Heather)
- Both **new wide-establish beats** (Mark + Heather in the hotel room / bedroom) will also need one.

Since all ~35 fix jobs here are lettering-only or narrow anatomy touch-ups (not fresh
`page:`-kind compositions unless the owner picks path A), a full `spatial_rules`/`position`/`pose`
staging file is only strictly required if path (A) is used for these panels. Authoring them is
still worthwhile prep either way (they double as the plain-language "what's physically happening
here" reference for whoever executes the fix), so §8 includes authoring them as a step.

## 8. Step-by-step order of operations (once the owner signs off)

1. Owner decides path (A) fallback vs. (B) `compose.py edit:` extension (§6). This gates whether
   step 6 is "extend compose.py + re-bless" or "skip."
2. `cp` the 7 files listed in §4 into `projects/heather-and-mark/qa/`; `mkdir` empty
   `receipts/`/`staging/`. Verify immediately: `cd projects/heather-and-mark/qa && shasum -a 256 -c
   MANIFEST.sha256` — expect all 6 `OK` with zero edits (confirms §2's portability claim in
   practice, not just in theory).
3. Author `projects/heather-and-mark/shotlist.json`, `pages-plan.json`, `references/ref-ledger.json`
   (character face/turnaround per tier-state actually used across acts 2/3b/3c/4a/4b/5, plus
   `scene_ladders` per location touched), `pages-log.json` — scoped to the ~35 touched panels
   plus whatever their (empty, per §6) continuity needs, not a full 69-panel backfill, unless the
   owner separately wants full retroactive chain coverage of the whole book.
4. Author the `qa/staging/<panel_id>.json` files listed in §7.
5. Author `qa-report.md`-derived judge instructions for the post-flight subagent step (§4) — a
   short doc, not a full defect-registry port.
6. If path (B): owner reviews and applies the `compose.py edit:` extension, then runs
   `python3 qa/integrity.py --rebless --i-am-the-user` and commits the re-blessed
   `MANIFEST.sha256` per its own instructions ("commit it so the change is visible in git
   history").
7. Run the chain per-job exactly as `CLAUDE.md` §"Generation protocol" specifies: compose -> audit
   -> submit (exact receipt attach list) -> fresh-subagent post-flight verdict -> bank -> (anytime)
   `verify_chain.py`. Recommended order: 3 `i2i re-render` blockers first (007, 032, 033 — highest
   visual risk, most valuable to see early), then the 4 remaining lettering blockers (009, 020,
   059, 062 — 062 needs the owner's number confirmation, see `fix-jobs.json`), then the 26 plain
   re-letters (cheapest/lowest-risk, batchable), then the 2 new wide beats last (they're genuinely
   new `page:` compositions regardless of path A/B, and benefit from every other fix in the act
   being settled first so the establishing shot's wardrobe/tier reads consistently against
   its neighbors).
8. `verify_chain.py` after banking to confirm no chainless entries snuck into the *new* work (pre-
   existing panels' backfilled ledger/log entries will legitimately show as chainless "pre-protocol"
   — that's expected and fine per its own comment; anything from *this* pass should NOT show up
   there).
