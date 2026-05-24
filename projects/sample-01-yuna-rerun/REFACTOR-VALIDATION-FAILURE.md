# Refactor Validation — Pre-flight Hard Stop

**Date:** 2026-05-24
**Validator:** Claude on Mac mini, per `~/Downloads/yuna-rerun-mini-handoff.md`
**Branch:** `feat/yuna-rerun-refactor-validation` (off `refactor/refs-are-truth-prompts-are-action` @ `aa52c29`)
**Outcome:** Stopped before panel 1 generation. Zero Higgsfield credits spent.

## TL;DR

The handoff's premise — "same shotlist, only the rule registry differs" — is structurally invalid. The refactor branch deleted the appearance-text fields from the shotlist schema by design. The baseline shotlist (`sample-01-yuna-cosmic-ascension/shotlist.json`, generated on `feat/overnight-samples-2026-05-23`) and the refactor branch's expected shotlist (chun-li-test on `refactor/refs-are-truth-prompts-are-action`) have **different fields**, not just different shapes. There is no honest field-by-field translation that preserves the baseline as a fair comparison point.

Also: the handoff's claim that the original run "didn't save prompts" is wrong. The prompts are saved at `projects/sample-01-yuna-cosmic-ascension/panel-prompts.json` on the overnight branch.

## 1. Schema mismatch — side-by-side, panel 1

### Baseline shotlist (overnight-samples branch)

```json
{
  "project": "sample-01-yuna-cosmic-ascension",
  "cast": ["Yuna Hoshino"],
  "location": "ISS Observation Cupola",
  "page_count": 10,
  "panels_per_page": 1,
  "panels": [
    {
      "page": 1,
      "panel_id": "01-01",
      "body_tier": 2,
      "camera_distance": "wide-establishing",
      "aspect_ratio": "16:9",
      "framing": "splash establishing shot — Yuna in profile at the ISS observation cupola, Earth's blue curvature visible through the seven-window cupola dome, control panels glowing softly to her left, a clipboard drifting in zero-g near her shoulder. Low angle, dramatic deep-space backdrop behind the cupola.",
      "pose": "floating with one hand braced on a padded handhold, the other reaching toward a control panel, body angled toward the windows",
      "expression": "focused, professional, faintly intrigued — eyes on a readout",
      "mood": "professional calm before contact, deep-space majesty",
      "wardrobe_state": "NASA/JAXA blue flight suit, zipped to collar, HOSHINO name tag on left chest, JAXA flag patch on right shoulder, mission patches intact",
      "props_in_frame": "control panel with backlit indicators, floating clipboard, padded handhold",
      "dialogue_caption": null,
      "is_splash": true,
      "tier_reinforcement_attach": null
    }
  ]
}
```

### Refactor branch shotlist (chun-li-test)

```json
{
  "project": "chun-li-test",
  "version": 1,
  "page_count": 30,
  "panels_per_page": 1,
  "pages": [
    {
      "page_number": 1,
      "panels": [
        {
          "panel_id": "p01-01",
          "size": "splash",
          "tier": 2,
          "characters": ["chun-li"],
          "location": "bisons-lair",
          "time_of_day": "interior, no diurnal cue",
          "weather": "n/a (interior)",
          "camera": "wide-establish, low-angle, three-quarter",
          "action": "Chun Li strides into Bison's villain chamber, defiant fighting stance, hands raised in classic guard. Ambient purple-violet Psycho Power energy fills the air around her, swirling like volumetric smoke. Wide low-angle hero shot establishing the cathedral-scale chamber.",
          "hair_state": "twin buns secured with red silk ribbons, classic SF2 ox-horns silhouette",
          "costume_state": "Tier 2 baseline. Canonical SF2 cobalt-blue silk qipao with gold trim, side slits, white thigh-highs, brown spiked leather gauntlets on both wrists, white sash. Pristine.",
          "expression": "Defiant, alert, brow set, eyes scanning. Strikingly beautiful — vogue-cover glamour Asian features, defined cheekbones, flawless skin.",
          "dialogue": [{"character": "chun-li", "text": "BISON! Show yourself!"}]
        }
      ]
    }
  ]
}
```

### Field-by-field delta

| Concern | Baseline (old) | Refactor (new) | Translation feasibility |
|---|---|---|---|
| Top-level structure | flat `panels[]` with `page` field per panel | nested `pages[].panels[]` with `page_number` | Mechanical |
| Tier | `body_tier` | `tier` | Mechanical rename |
| Camera | `camera_distance: "wide-establishing"` (single value) | `camera: "wide-establish, low-angle, three-quarter"` (comma-list of categorical anchors) | Lossy — baseline doesn't carry low-angle / three-quarter axes as separate camera tokens; they're folded into `framing` prose |
| Aspect ratio | explicit `aspect_ratio: "16:9"` | derived from `size` via `ASPECT_FOR_CAMERA` lookup | Lossy — refactor's mapping forces categorical sizes |
| Action / scene description | `framing` (scene prose) + `pose` (body pose) | `action` (single field, must be short delta) | **Semantic compression**: refactor wants short action-delta only, baseline carries scene-establishing prose. Translation requires editorial cuts. |
| Hair state | NOT IN BASELINE | `hair_state` REQUIRED (L22 reads it) | **Synthesis required** — baseline's prompts had hair appearance in the shared_prefix, never per-panel. Forced to invent. |
| Cast | inferred from top-level `cast: ["Yuna Hoshino"]` | per-panel `characters[]` slug list | Synthesis (mechanical for solo cast, but contaminates per-panel cast-presence semantics) |
| Location | inferred from top-level `location: "ISS Observation Cupola"` | per-panel `location` slug | Synthesis required (must coin a slug like `iss-cupola`) |
| Time of day / weather | NOT IN BASELINE | required | **Synthesis required** — invent values |
| Wardrobe / costume | `wardrobe_state` (scene-relative state prose) | `costume_state` (state delta) | Lossy rename, but the field role differs — baseline state is descriptive, refactor expects delta-from-prior-panel |
| Mood / props | `mood`, `props_in_frame` | NO EQUIVALENT FIELDS | Information loss |
| Dialogue | `dialogue_caption: null` (single string) | `dialogue: [{character, text}]` (per-speaker list) | Mechanical |
| Splash flag | `is_splash: true` | `size: "splash"` | Mechanical |

**Conclusion:** the refactor deleted the appearance-text fields by design. Forcing the baseline through a translator requires inventing values (`hair_state`, `time_of_day`, `weather`) and performing editorial compression (`framing` + `pose` → short `action`). The translator's outputs **are themselves the experiment** — any A/B comparison would conflate "the rule registry's behavior" with "the translator's editorial choices."

## 2. Handoff bug — `panel-prompts.json` exists

> Handoff text: "**SAVE the composed prompt** to `projects/sample-01-yuna-rerun/pages/page-NN/panels/panel-NN-NN/prompt.txt` — this was missing on the original Yuna run and was the diagnostic gap"

**Actual:** the original Yuna run **did** save prompts. They live at:

```
overnight branch: projects/sample-01-yuna-cosmic-ascension/panel-prompts.json
```

Confirmed present in `git ls-tree -r origin/feat/overnight-samples-2026-05-23 -- projects/sample-01-yuna-cosmic-ascension/`.

The file contains:
- `shared_prefix` — ~150 words of appearance text including Yuna's hair, eyes, complexion, age, beauty + setting anchor + suppression rules. Submitted with every panel.
- `panels[].prompt` — per-panel prose with embedded TIER N callouts, POSE / EXPRESSION / WARDROBE / HAIR repeats.

This is great news for the comparison doc — the appearance-text-word-count metric **is** measurable against a real baseline. But it undermines the handoff's framing that prompts were a "diagnostic gap" on the original run.

## 3. Tertiary findings (lower priority, surfaced for completeness)

- **Panel folder structure in the handoff is also wrong.** Handoff says save at `pages/page-NN/panels/panel-NN-NN/`. Refactor branch's actual layout (verified against chun-li-test) is **flat**: `pages/panels/panel-<panel_id>/`. `panel_status` reads from `root / "pages" / "panels"`, not nested by page number. Easy to fix in handoff text.
- **Missing baseline refs.** `references_required.json` lists 5 character refs (face-card, body-tier-lineup, multi-angle-pack, costume-turnaround-baseline, costume-turnaround-peak) + 1 location ref. Only 2 are committed on the baseline branch (face-card.png + iss-cupola-env.png). The baseline run proceeded with stand-ins per `missing_ref_guardrail: use-stand-in-and-log`. The refactor's attach-rules (especially `attach/body_tier.py`, `attach/tier_reinforcement.py`) need these refs to function — if they're absent on the re-run too, the validation would test the refactor's fallback behavior, not its happy path.
- **Model retirement, already known.** `nano_banana_flash` was retired 2026-05-21. The handoff says default to flash; the laptop's memory bundle correctly overrides to `nano_banana_pro`. Not a blocker, just worth keeping the handoff text in sync.

## 4. Fix-forward — two viable paths

### Path A: build an overnight→refactor schema-migration tool, then re-run

**Approach:** add a `scripts/migrate_shotlist_overnight_to_refactor.py` that takes an old-schema shotlist and emits a new-schema one. Codify the field-mapping rules explicitly (so the translation is auditable). Re-run the baseline shotlist through the migration, then through the refactor's `next_panel.py`.

**Pros:** preserves the original A/B intent (same story, same character beats, same panel count, same intended visuals). Cheaper — no new Higgsfield credits beyond the 10 re-run panels (~$0.40).

**Cons:** the migration tool has to *invent* `hair_state`, `time_of_day`, `weather`, and compress `framing + pose` into a short `action`. Those choices land in the migration tool, not in the rule registry — but they still contaminate the A/B unless the user reviews and signs off on the migration output before generation.

**Recommended if:** the user wants to test whether the refactor produces better OUTPUT on the same STORY. The migration tool's editorial cuts are auditable, the rule registry's contribution is isolated.

### Path B: author a fresh shotlist on the refactor's new schema, regenerate baseline, then re-run

**Approach:** write a new Yuna shotlist (or pick a different character entirely) directly in the refactor schema. Generate the baseline on `main` using whatever legacy compose path still exists there (or on the overnight branch with the old compose). Then generate the re-run on `refactor/...` using the refactor compose.

**Pros:** zero translation confound. Both runs consume the same input. Pure rule-registry A/B.

**Cons:** ~2× the Higgsfield cost (need a new baseline run, ~$0.80 instead of ~$0.40). More work upfront (need to author the shotlist). The new baseline is not the same baseline the user has already eyeballed and diagnosed as "broken."

**Recommended if:** the user values experimental cleanliness over historical continuity, or if they're skeptical that the migration tool in Path A could ever be neutral.

## 5. What I didn't do

- No git commit, no push, no PR.
- No CHANGELOG entry.
- No Higgsfield `generate_image` call. Balance unchanged: 359.26 credits.
- No modification to the original baseline project on the overnight branch.

The validation branch (`feat/yuna-rerun-refactor-validation`) exists locally and has zero commits beyond the branch point. The working tree contains `projects/sample-01-yuna-rerun/` (extracted baseline snapshot + this failure doc) — all uncommitted. Discard or commit at your discretion.

## 6. Recommendation

Path A. The user's intent on this re-run was a diagnosis of the refactor against a known-broken baseline. A migration tool with explicit, auditable field rules + a user review pass on the migrated shotlist before generation preserves that intent at minimum extra cost. The migration tool itself becomes a useful artifact for any future re-runs of old projects on the refactor's new schema.

If Path A's migration tool turns out to require too many synthesis choices to be neutral (likely true for `hair_state` and `action`-compression specifically), pivot to Path B.

Either way, the panel-prompts.json discovery means the comparison doc's prompt-structure A/B is recoverable — that part of the deliverable doesn't require new generation. A pure prompt-A/B (baseline `panel-prompts.json` vs refactor-composed prompts on the migrated shotlist) could be a faster, cheaper intermediate deliverable before committing to full image generation.
