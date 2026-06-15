# scripts-raw — drop your comic SCRIPTS here  (B1 feedstock)

The dropzone for the user's own comic **story scripts** (premise, transformation arc,
beats) — the kind of text the pipeline already digests (e.g. the Ultra-Gal PDF).
This is **distinct from** rendered-comic ingestion (`../scripts/ingest.py`, which
fetches page **images** and scores all four visual axes).

## Deliver → normalize

Drop a script file here (`.txt`, `.md`, `.pdf`, `.docx`), or paste via stdin, then:

```bash
# from research/comic-corpus/
scripts/ingest_script.py --local scripts-raw/my-script.md --title "My Script"
cat my-script.txt | scripts/ingest_script.py --stdin --slug my-script --title "My Script"
scripts/ingest_script.py --list        # show script records + status
```

This registers `corpus/<slug>/` with `record_type: "script"`, extracts the text to
`source.txt` (gitignored), and writes a `script-record.json` **skeleton**
(`analysis_status: pending`). Then a **fresh subagent** analyzes the script against
`../analysis-rubric.md` and fills the record + `notes.md`.

## A script supports only the TEXT axes of the rubric

The corpus rubric has four axes. A text script can be honestly scored on **two**:
- ✅ **Growth density** — from the beat structure / scene ladder (corpus F1 targets apply).
- ✅ **Story & structure** — the script's whole job (corpus F5: the differentiation axis).
- ⛔ **Camera dynamism** and ⛔ **Expression intensity** are **visual** — deferred to
  storyboard/render and recorded under `deferred_axes`. Scoring them from prose would
  be inventing data.

Otherwise scripts are analyzed the *same way* reference comics are: same vocabulary
(escalation devices, chapter type, growth ratio, strengths/weaknesses), so script
feedstock and rendered-comic feedstock pool into one corpus the ideator reads.

## Raw stays local; records are versioned

Files dropped here, and each record's extracted `source.txt` / `source.<ext>`, are
**gitignored** — only the normalized analysis (`script-record.json`, `notes.md`,
`meta.json`) is committed. This mirrors how rendered pages are gitignored but their
analysis is kept. (The scripts are the user's own IP, so raw text *could* be committed —
flip the gitignore line if desired — but the record is built to capture everything the
corpus needs without the raw.)
