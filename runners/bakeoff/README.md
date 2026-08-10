# Bakeoff lane — anchor → over-generate → judge → retry → select

The automated generation lane rebuilt around the owner's PROVEN manual method
(over-generate in Flow, favorite winners, anchor with images) instead of the
specify→generate-once→hope flow. Diagnosis (agreed 2026-08-05): ~30 simultaneous
prompt constraints × ~90-95% per-clause compliance ≈ ~20% clean panels — single-shot
can't converge no matter how many rules the prompt wall gains. Over-generation +
selection is what actually works (owner keep-rate ~8% on a 341-panel project).

## The five pillars

1. **Beat contract + fan-out** — a job = one beat: composition anchor image(s),
   identity refs (locked board refs via `genspec`), an action/camera-only prompt
   (appearance prose is linted — refs are truth), N variants (default 4).
2. **Two-stage judge** — Stage A: the live server-side `ck_ai_qa` scan
   (`bridge.php do=qascan`) per variant, mapped to canonical DEFECT-REGISTRY IDs
   (`registry.py` reads `defect-registry.json`; blockers + model-high-sev block;
   ref-sheets exempt from lettering blocks per picks-profile B95). Stage B: a
   fresh `claude -p` (Sonnet) ranker over survivors, rubric files passed by path
   and read verbatim, weights calibrated on the owner's real picks
   (`research/picks-profile-eva.md`): camera/composition first, expression
   tiebreaker only. The judge never grades its own generations.
3. **Retry loop** — zero-clean beats re-roll with the specific registry findings
   injected as corrective clauses (`registry.RETRY_INJECTION`), max 2 retries,
   then land FLAGGED in the human-review queue (`do=flag` + tags
   `bakeoff,needs-human`) — never silently shipped.
4. **Selection** — winner lands `accepted=true rating=good` + tags
   `bakeoff,judge-pick` via `do=write` (existing board semantics; `port.php
   ?only=approved` etc. respect it). Losers stay unrated on the board —
   recoverable, and they feed keep/trash telemetry. An owner-accepted panel in
   the same group is NEVER overridden (mirrors the flowfav invariant).
5. **Yield metric** — per run: clean-variant rate per roll, beats cleared after
   retry, human-queue count, defects-per-shipped-panel by registry ID. Persisted
   to `data/bakeoff-yield.json` (repo) and pushed to the studio
   (`do=yield` → `studio/data/bakeoff-yield.json`, trend card on cc.php).
   This number trending is the whole point.

## Flow of a run

```bash
python3 runners/bakeoff/bakeoff.py plan --sheet mysheet.json
# -> runs/bo-YYYYMMDD-HHMMSS/{state.json,jobsheet.json,refs/,variants/<beat>/}

# DRIVER executes jobsheet.json (see below), writing r<round>v<N>.png files

python3 runners/bakeoff/bakeoff.py collect --run runners/bakeoff/runs/bo-...
python3 runners/bakeoff/bakeoff.py judge   --run ...   # ingest + stage A + stage B
python3 runners/bakeoff/bakeoff.py retry   --run ...   # queues injected re-rolls
# (drive new jobsheet entries, collect, judge again — until no beat is 'retry')
python3 runners/bakeoff/bakeoff.py select  --run ...
python3 runners/bakeoff/bakeoff.py stats   --run ... --credits <spent>
```

Every subcommand is idempotent and resumable; state lives in `<run>/state.json`.

## Beat sheet contract (`beatsheet.schema.json`)

```json
{
  "project": "studio-project-id",
  "backend": "flow-chrome | higgsfield-mcp | flow-manual",
  "style": "optional style block override",
  "beats": [{
    "id": "b01",
    "kind": "panel | sheet",
    "prompt": "ACTION + CAMERA + SETTING only — no appearance prose",
    "anchors": [{"board": "abc123.jpg"}, {"local": "~/path/plate.png"}],
    "identityRefs": [{"char": "Lana", "kinds": ["face","view"], "max": 2}],
    "aspect": "3:4",
    "variants": 4
  }]
}
```

Anchors = composition truth (storyboard-sheet crop, prior accepted panel, or
blueprint). Identity refs resolve against the project's LOCKED refs only
(`genspec` doctrine). Everything is downloaded into `<run>/refs/` so any driver
can attach them.

## Driver protocol (generation is pluggable, the lane is not)

`jobsheet.json` is a list of `{beat, round, prompt, style, aspect, count,
anchors[], refs[], out[], done}`. A driver generates `count` images for each
undone entry — anchors + refs attached as images, `prompt` (+`style`) as text —
and writes them to the `out` paths. Then `collect` picks them up.

- **higgsfield-mcp** — a Claude session with the Higgsfield MCP: per entry, run
  `generate_image` (`{"params":{model:"nano_banana_pro", resolution:"1k",
  count:<N>, ...medias}}`) as ONE call per entry, download results to `out`.
  PAID (~2 credits/image at 1k) — check credits first.
  **⚠️ Two corrections from the first live run (2026-08-09), both of which would
  have failed or degraded the nightly driver:**
  1. `nano_banana_flash` **no longer exists** in the Higgsfield catalog — the
     call errors with `unknown model`. Current image ids: `nano_banana_2`,
     `nano_banana_pro`, `nano_banana`, `nano_banana_2_lite`. Note that requesting
     `nano_banana_pro` currently comes back tagged `nano_banana_2` in the job —
     the API substitutes silently, so don't claim Pro was used without checking
     the returned `model` field.
  2. **Use ONE `count:N` call per entry, NOT N sequential `count:1` calls.**
     These models take no seed parameter, so identical sequential submissions
     collide: four sequential `count:1` calls returned only **3 distinct images**
     (two byte-identical, same MD5, different job ids), while a single `count:4`
     call returned **4 distinct**. Sequential burns ~25% of spend on duplicates
     and shrinks the variant pool the whole lane depends on. This overrides the
     general "count=1 per Higgsfield submit" house rule *for this lane*, where
     distinct variants are the entire point.
- **flow-chrome** — a Claude session driving Google Flow via the Chrome
  extension (Omni attach flow, Nano Banana Pro, x4). FREE with Pro. Verify the
  model + account every submit (house rules).
- **flow-manual** — the owner runs the entries in Flow by hand; the jobsheet IS
  the job sheet.

The night-shift worker drains this lane by running the loop above off a beat
sheet (it already holds a Higgsfield MCP session) — it is a DRIVER of this lane,
not a rival runner.

## What this lane reuses (and must keep reusing)

- `bridge.php` verbs: `genspec`, `img`, `ingest` (accepted=0, prompt→genkey
  beat-grouping, `parent` chaining keeps retries in the round-1 group), `qascan`,
  `write`, `flag`, `yield`.
- `studio/inc/defects.php ck_ai_qa` — Stage A. Extend THAT scan (and the
  registry JSON) when detection gaps appear; do not grow a rival scanner here.
- `skills/comic-production/references/defect-registry.json` — single source of
  truth for IDs/severities. `registry.py` only reads it.
- Rubrics by path (verbatim): `research/comic-corpus/analysis-rubric.md`,
  `cinematic-framing.md`, `qa-checklist.md`.
- Prior art: `runners/variant_picker.py` (criteria ordering), `runner_core.py`
  (halt taxonomy). This lane supersedes their single-shot orientation for new
  work but does not delete them.

## Rule diet

`research/rule-diet-report.md` (2026-08-09) classifies all 38 prompt-wall
lessons: 22 are mechanical attach-requirements (enforced by construction here),
15 are post-gen detectors (Stage A/B territory), 1 is prompt-prose-only. As
judge coverage is validated, (c)+thinnable prose items are prune CANDIDATES —
owner decision, nothing deleted.
