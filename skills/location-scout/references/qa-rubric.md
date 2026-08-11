# Location-pack CGI conversion QA rubric (canonical)

Pass this rubric VERBATIM to the QA subagent (per `feedback_dont_paraphrase_canonical_rubrics`).
The subagent views the SOURCE capture and the CGI conversion side by side and returns one
verdict line per plate.

## What a conversion must satisfy

1. **COMPOSITION** — same camera angle, framing, and perspective as the source. The
   architecture/layout is recognizably the same place. FAIL if buildings/structures were
   invented, removed, or rearranged; if the camera moved; or if the scene is a different
   location entirely.
2. **PEOPLE** — the plate must be EMPTY of people. Distant unrecognizable silhouettes are a
   soft warn; any clear human figure is FAIL (cast is inserted at generation time — stray
   people become phantom background extras, per `feedback_no_extra_characters`).
3. **OVERLAYS** — no Google Maps/Street View watermarks, brand stamps, timestamps, UI chrome,
   or readable third-party brand names/logos surviving into the plate. FAIL if present in a
   focal zone; warn if a faint corner remnant.
4. **MEDIUM** — the plate must read as a 3D CGI render (DAZ3D/Iray, archviz, game-cinematic),
   NOT a photograph. FAIL if it is indistinguishable from the source photo (the Vegas-v1
   failure mode). Also FAIL the opposite extreme: 2D-illustrated/anime/cartoon looks.
5. **INTEGRITY** — no melted/garbled geometry in focal areas, no duplicated structures, no
   AI-text artifacts (garbled signage is acceptable only if the source signage was removed
   entirely; invented readable text is FAIL).

## Output format (one line per plate, pipe-delimited)

```
<plate-file> | PASS | -
<plate-file> | WARN | <short reason, e.g. "faint watermark remnant lower-left">
<plate-file> | FAIL | <category: composition|people|overlays|medium|integrity> — <short reason>
```

A pack ships when every plate is PASS or WARN. Any FAIL goes back through conversion
(re-render with stricter language) or falls back to attaching the source photo directly.

## Recording

Verdicts are recorded per slot in `_targets.json` under `qa`:

```json
"qa": {"verdict": "pass", "notes": null, "checked_at": "<iso8601>", "rubric": "qa-rubric v1"}
```

`cgi_convert.py --record-qa <slot-id> --qa-verdict pass|warn|fail [--qa-notes "..."]` writes
this; `--emit-manifest` propagates it into `meta/locations.json`, and `pack_index.py` carries
it into the repo-level index. Flat packs record QA in `cgi/_provenance.md` prose plus an
optional `_qa.json` (same shape, keyed by plate filename) that `pack_index.py` reads.
