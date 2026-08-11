# Site apply notes — Not So Supra... Man → GrowGetter

_What to add where. Pointers into the runbook, pre-filled with this project's values._
_Every step is run by the human (or by Claude WITH per-action approval) — this file only maps the path._

> ⚠️ **This comic is ALREADY on comic-platform staging** (ingested 2026-07-30 per
> runbook Appendix A). Steps 1-5 are DONE — re-run `--verify-only` to confirm,
> then this file's remaining work is steps 6-8 + the WP-side post.

**Runbook:** `~/Documents/comic-platform/docs/PUBLISH-A-COMIC.md` (walked 2026-07-30 with
Not So Supra... Man — this skill mechanizes the PREP half; the runbook is the APPLY half).

1. **Manifest** — `publish/growgetter/not-so-supra-man.json`:
   ```json
{
  "id": "not-so-supra-man",
  "property": "growgetter",
  "title": "Not So Supra... Man",
  "issue": 1,
  "series": "not-so-supra-man",
  "seriesTitle": "Not So Supra... Man",
  "releaseDate": "2026-07-30",
  "status": "paid",
  "slugs": [
    "not-so-supra-man"
  ],
  "artworkDir": "/Users/mattmenashe/Documents/claude-comic-pipeline/projects/not-so-supra-man/pages/lettered",
  "artworkGlob": "*.png"
}
   ```
   Add every slug you intend to hand out NOW (step 1a note) — e.g. the long-form
   `not-so-supra-man-female-muscle-growth-comic` house shape.
2. **Send:** `python3 tools/publish/new_comic.py publish/growgetter/not-so-supra-man.json --dry-run` — read the
   `uploading: 0 pages` line (paid comics upload NO pages — structurally enforced), then run
   without `--dry-run`, then `--verify-only` until every line is PASS.
3. **Paywall check** (runbook step 2) — paid comic must have zero publicly fetchable pages.
4. **Dialogue + translations** (steps 3-4) if this comic has balloons: OCR with
   `tools/ocr/ocr_comic.py --local-dir /Users/mattmenashe/Documents/claude-comic-pipeline/projects/not-so-supra-man/pages/lettered`, review, then ONE translate subagent per language.
5. **URLs/SEO** (step 5) — verify slugs resolve; canonical/hreflang come from the router.
6. **After posting elsewhere**, record syndication (step 6) — never before.
7. **Flip reminder:** paid → free flip is release + 6 months = **2027-01-30**. The flip does NOT fire
   on its own (project_platform_flip_never_fires) — `tools/flip/flip_platform.py` runs monthly, human-driven.
8. **WP side** (step 8) — the old system needs its matching post until cutover.
