# Production System Vision — the full comic assembly line

> **Status: design / north-star.** Written 2026-06-14 as preparation, deliberately ahead of implementation. The user asked to capture the whole-system vision now so a future session (a stronger model) can pick it up cold and build without a long re-brief. **No code here — this is the map.** When you build a stage, build it to the contracts named here, and update this doc + the CHANGELOG.

---

## 1. The vision in one line

A **seven-stage assembly line** that takes a spark of an idea and ends with a published comic, where each stage hands a well-defined artifact to the next, the boring/mechanical work is enforced by gates, the judgment work is done by Claude + subagents, and the human is the **producer** who approves at a small number of high-leverage gates — not a laborer driving every panel.

```
  IDEATOR → WRITER → STORYBOARD → REFERENCE → PAGE BUILD → REVIEWER → PUBLISHER
   (concept) (script) (shotlist)   (ref pack)  (panels)    (QA)       (posting)
       ▲                                                                  │
       └──────────────────── analytics flywheel ─────────────────────────┘
```

The line already exists and is **strong in the middle** (storyboard → review). It is **missing at both ends** (ideator, writer) and **stubbed at the exit** (publisher). The connective tissue between stages — the schema contracts — is partially designed (experiment/04) but not enforced end-to-end.

---

## 2. The seven stages — purpose, I/O, current state

For each stage: what it does, what it consumes, what it emits, how mature it is today, and the file pointers.

### Stage 1 — IDEATOR  *(concept generation)*  — **SHELL (scaffolded 2026-06-14)**
- **Purpose**: turn a seed (theme, character, "do something with X", or nothing at all) into a ranked slate of comic concept pitches.
- **Input**: optional seed; the character roster; corpus findings (what works); publisher analytics (what performed) once the flywheel exists.
- **Output**: a `concepts.json` slate — each concept a logline, transformation arc, cast, setting, hook, est. page count, and a why-it'll-perform rationale.
- **Current state**: **shell built** at `skills/ideator/` — `SKILL.md` (the concept-tournament workflow + I/O contract), `references/concept-schema.json` (the Ideator→Writer contract), `references/rubric.md` (the scoring rubric, grounded in the corpus findings). The **tournament engine itself (generate + score) is a documented STUB** in `scripts/tournament.py` (`BUILD ME (stronger model)`) — deliberately deferred per §8. Until it's built, ideation runs by hand against the same contract.
- **Asset to feed it**: `research/comic-corpus/` — the corpus skill studies reference comics against a rubric. The ideator consumes corpus conclusions so pitches are grounded in what actually works, not invented in a vacuum. The corpus now also ingests the user's own **scripts** (B1) and a premium **catalog** via the authenticated session (B2) as feedstock.

### Stage 2 — WRITER  *(script generation)*  — **MISSING**
- **Purpose**: turn one selected concept into a full, panel-ready script.
- **Input**: a chosen concept from Stage 1 (or a human-written concept).
- **Output**: a script in the format `script-breakdown` already consumes (page → panel beats, dialogue, transformation decomposition, escalation curve). Same shape as the Ultra-Gal PDF the pipeline already digests.
- **Current state**: nothing dedicated. Scripts arrive as PDFs/prose from the user.
- **Must be pipeline-aware**: the writer should write *to the pipeline's strengths* — it knows the system does tier escalation, body-region ECUs, transformation triptychs, L34 staging, L35 expression beats, the growth-sequence order (breasts→glutes→muscle, per `posing-and-expressions.md`), and the escalation devices in `escalation-devices.md`. A good script pre-bakes those so storyboard + page-build have an easy time.

### Stage 3 — STORYBOARD  *(script → shotlist)*  — **MATURE ✓**
- **Purpose**: break a script into a structured per-panel shotlist.
- **Input**: a script. **Output**: `shotlist.json` + `references_required.json` (L28 manifest) + `shotlist.md`.
- **Current state**: the `script-breakdown` skill. Mature. Emits camera, staging (L34 `subject_staging`), tiers, dialogue, transformation beats, the reference manifest.
- **Files**: `skills/script-breakdown/SKILL.md`.

### Stage 4 — REFERENCE  *(ref pack assembly)*  — **MATURE ✓**
- **Purpose**: produce every reference the shotlist declares before any panel renders (refs-are-truth).
- **Input**: `references_required.json`. **Output**: a complete ref pack (face cards, body-tier lineups, costume turnarounds, tier-6/7/8/9 reinforcement, view packs, env refs, location-scout city packs) + a ref ledger.
- **Current state**: `reference-gathering` (manifest-driven), `reference-acquisition` (internet→3D base), `location-scout` (city → CGI background pack), `style-lock` (style presets), `peak-body-scale` tier refs. Mature.
- **Files**: `skills/reference-gathering/`, `skills/reference-acquisition/`, `skills/location-scout/`, `skills/style-lock/`, `skills/comic-production/references/peak-body-scale/`.

### Stage 5 — PAGE BUILD  *(panel + page generation)*  — **MATURE ✓✓✓**  *(90% of the work to date)*
- **Purpose**: generate every panel, letter it, compose the page.
- **Input**: shotlist + ref pack. **Output**: banked, accepted, lettered pages.
- **Current state**: the deepest part of the system. `comic-production` + `next_panel.py` rule registry (L1–L34 auto-injected) + the per-project `qa/` gate chain (compose → audit → submit → post-flight → bank → verify → integrity) + `page-composer` (layout + L19 baked lettering) + `production-briefing` (Phase 0 config) + the dual-backend (Higgsfield MCP / Flow). Mature and heavily hardened.
- **Files**: `skills/comic-production/`, `projects/<p>/qa/*.py`, `commands/build-comic.md`, `skills/page-composer/`, `skills/production-briefing/`.

### Stage 6 — REVIEWER  *(QA / audit)*  — **MATURE ✓✓**  *(one piece unwired)*
- **Purpose**: catch what the gates can't — visual defects, continuity drift, dead faces, flat staging — before publish.
- **Input**: banked pages + the canonical rubric. **Output**: per-panel verdicts, defect registry, re-render directives.
- **Current state**: `continuity-check` + `qa-checklist.md` + `cinematic-framing.md` + the qa gate chain's post-flight verdict step + the fresh-subagent audit pattern + `qa-defect-doctrine.md`. The **vision-audit** (experiment/02) is designed and measured but not wired into the gate as an automatic step — that's the one open piece. The Flow review-harvester (in progress) feeds this stage by bundling output+prompt+input-refs for fast digestion.
- **Files**: `skills/continuity-check/`, `skills/comic-production/references/qa-checklist.md`, `qa-defect-doctrine.md`, `docs/experiments/02-vision-audit-pilot/`.

### Stage 7 — PUBLISHER  *(posting)*  — **STUB ONLY ✗**
- **Purpose**: take a finished comic and publish it to its destinations, then capture engagement for the flywheel.
- **Input**: a compiled, lettered, reviewed comic + metadata. **Output**: posted content + `posted.json` record + (eventually) engagement metrics.
- **Current state**: a stub. `build-comic.md` names "Stage 6 — Posting" with a `posting/posted.json` sentinel, never exercised. No posting skill exists.
- **Destinations on file**: `3dmusclecomics.com` (static site at `~/Documents/3dmusclecomics-site`, comics.js manifest, Cloudflare Pages) + social platforms (multi-platform crop bundles).

---

## 3. Current-state heat map

| Stage | Maturity | Where it lives |
|---|---|---|
| 1 Ideator | 🟡 shell (engine stubbed) | `skills/ideator/` (SKILL + schema + rubric); feedstock at `research/comic-corpus` |
| 2 Writer | ❌ missing | — (scripts arrive manually today) |
| 3 Storyboard | ✅ mature | `skills/script-breakdown/` |
| 4 Reference | ✅ mature | `skills/reference-gathering/`, `reference-acquisition/`, `location-scout/`, `style-lock/` |
| 5 Page build | ✅✅✅ deep | `skills/comic-production/`, `projects/<p>/qa/`, `page-composer/`, `production-briefing/` |
| 6 Reviewer | ✅✅ (vision-audit unwired) | `skills/continuity-check/`, `qa-checklist.md`, `docs/experiments/02` |
| 7 Publisher | ⚠️ stub | `build-comic.md` posting sentinel only; site at `~/Documents/3dmusclecomics-site` |

**The build priority writes itself: the two missing front-end stages (ideator, writer) and the missing exit stage (publisher) are where the leverage is.** The middle is done.

---

## 4. The contracts between stages (the connective tissue)

Each handoff is an artifact + a schema. This is the schema-contracts work (experiment/04) generalized to the whole line. **The contract is what lets a stronger model build one stage without breaking its neighbors.**

| Handoff | Artifact | Schema status |
|---|---|---|
| Ideator → Writer | `concepts.json` (slate) + a `selected_concept` | **schema exists** (`skills/ideator/references/concept-schema.json`); engine stubbed |
| Writer → Storyboard | `script.md`/`.json` in the script-breakdown input shape | partly implicit (the PDF/prose shape script-breakdown already parses) |
| Storyboard → Reference | `shotlist.json` + `references_required.json` | exists (experiment/04 schemas) |
| Reference → Page build | ref ledger + complete ref pack | exists (`ref-ledger.json`, L28 manifest) |
| Page build → Reviewer | banked `pages-log.json` + receipts/verdicts | exists (qa chain) |
| Reviewer → Publisher | a "ship-clean" signal + final PDF/PNG bundle + metadata | to design |
| Publisher → Ideator | engagement/analytics record | to design (the flywheel) |

**Design rule** (from experiment/04 + the gate doctrine): every contract gets a JSON schema and a validator at the boundary, so a stage that emits a malformed artifact fails loudly at the handoff instead of silently corrupting the next stage. The "layers disagreeing about vocabulary" failure (Magnamus's diagnosis) is prevented by making the contracts explicit.

---

## 5. The three weak stages — design proposals (the actual ideation)

### IDEATOR — a concept tournament, not a single guess
- **Shape**: a skill that runs a **judge-panel / tournament**. Generate N concepts from deliberately different angles (transformation-flavor-first, character-first, setting-first, hook-first), score each against a rubric grounded in corpus findings, surface the top 3 with rationale. Beats one-shot ideation because the solution space is wide.
- **Rubric axes**: hook strength, transformation payoff density (the genre lives on growth — `feedback_growth_density_mandate.md`), camera/staging potential, cast reuse (cheaper if it uses existing locked characters), novelty vs. proven patterns, est. production cost.
- **Feedstock**: `research/comic-corpus` conclusions (what reference comics do well), the locked character roster, and — once it exists — publisher analytics. Until analytics exist, the corpus is the ground truth.
- **Human gate**: the user picks 1 of the top 3 (or asks for a fresh slate). High-leverage, low-effort approval.
- **Output**: `concepts.json` + the selected concept.

### WRITER — pipeline-aware scriptwriting
- **Shape**: a skill that expands one concept into a full panel-ready script in the exact shape `script-breakdown` consumes. The contract is the whole point — the writer's output drops straight into Stage 3 with zero reformatting.
- **Bakes in the craft rules the pipeline already knows**: growth-sequence order (breasts→glutes→muscle), the escalation curve (`escalation-devices.md`), camera variety + L34 staging beats, L35 expression beats, the always-clothed constraint, no-background-extras, the tier curve, transformation decomposition into body-region beats.
- **Writes to strength**: because it knows the pipeline can do triptych growth, ECU mass-ups, tier reinforcement, hero splashes, it structures the story so the big visual moments land where the pipeline is strongest.
- **Human gate**: the user reads + approves the script (or requests revisions). This is the last cheap point to change the story before expensive generation.
- **Output**: `script.md` ready for storyboard.

### PUBLISHER — prepared posts, human-gated publish, analytics capture
- **Shape**: a skill that takes a reviewed comic and **prepares** everything for posting, then stops for approval. It does NOT auto-post.
- **Why human-gated, always (at least crawl/walk)**: posting publicly is an irreversible, outward-facing action — it falls under "explicit permission required" in the operating rules. The publisher prepares; the human publishes. Even in "run" mode, publish stays a per-post or per-batch human approval, never silent.
- **What it prepares**: per-destination bundles — for `3dmusclecomics.com` (add to the comics.js manifest + the Cloudflare Pages deploy), for social (per-platform crops: IG square, Twitter wide, etc. — the export-target preset idea), captions, tags, a posting schedule, a content-warning/age-gate check.
- **Analytics capture (the flywheel)**: after posting, record which comic went where and capture engagement over time into an analytics store the ideator reads. This is what turns the line into a self-improving loop — the system learns what to make next from what performed.
- **Output**: `posted.json` + the analytics record.

---

## 6. Orchestration + the autonomy spectrum

`build-comic.md` is the existing orchestrator for stages 3–7. The vision extends it upstream (1–2) into a true 1-through-7 conductor, and a project carries a **current-stage marker** the dashboard visualizes.

**Crawl → Walk → Run** (the forever-agent idea, gated honestly):
- **Crawl**: human approves every stage gate. Used while each new stage is unproven.
- **Walk**: human approves concept (1), script (2), and publish (7); stages 3–6 run autonomously with the gate chain enforcing quality. This is the realistic near-term target — the middle is already gate-hardened enough to trust.
- **Run**: the forever-agent. The system ideates → writes → builds → reviews on a loop, surfacing finished comics for a single publish approval + spot-checks. Analytics feed the next idea. Human touches only the two ends.

The gate chain (compose/audit/bank/verify/integrity) is what makes Walk and Run *safe* — autonomy is only as trustworthy as the mechanical gates underneath it. "Claude's promises are not load-bearing; only in-path gates are" (CLAUDE.md). Every new stage should ship with its own gate before it's trusted in Walk/Run.

---

## 7. Cross-cutting systems (serve every stage)

- **Dashboard** (`resedas-mac-mini...:8765`) — read-only visibility into every project's stage. v1 would add the upstream stages + a publish-approval surface.
- **QA gate spine** — the per-project `qa/` chain. The mechanical backbone of trust; lives inside page-build + review but its discipline (receipts, integrity lock, fresh-subagent verdicts) is the model every stage's gate should copy.
- **Flow review-harvester** (in progress) — bundles output+prompt+input-refs so the reviewer digests work fast. Feeds Stage 6.
- **Corpus** (`research/comic-corpus`) — the research base. Feeds Stage 1 (ideator) + Stage 2 (writer).
- **Memory + lessons-learned** (L1–L34, the `feedback_*` memory notes) — institutional knowledge every stage draws on. The system's accumulated craft.
- **Schema contracts** (experiment/04) — the validators at each handoff. The thing that keeps the seven stages from drifting apart.

---

## 8. Build roadmap (sequenced for the next model)

Suggested order, highest-leverage first. Each is its own focused build with its own gate + CHANGELOG entry.

1. **Wire the vision-audit into the reviewer gate** (experiment/02 → production). Closes the one open piece in the mature middle; makes Walk-mode review trustworthy. Lowest risk, high value.
2. **Publisher stage — prepare + human-gated publish** to 3dmusclecomics.com first (single destination), with `posted.json` + a minimal analytics stub. Makes the line end-to-end for the first time.
3. **Writer stage** — pipeline-aware scriptwriting to the script-breakdown contract. Unlocks "concept → finished comic" without a hand-written script.
4. **Ideator stage** — concept tournament fed by the corpus. Closes the front end; with analytics from #2 it becomes the flywheel's intake.
5. **Contracts pass** — formalize + validate every handoff schema (generalize experiment/04 across all seven boundaries). Hardens the whole line for Walk/Run.
6. **Orchestration upgrade** — extend `build-comic.md` to conduct 1–7 with the crawl/walk/run autonomy modes + the dashboard stage marker.
7. **Run mode / forever-agent** — only after every stage has a gate and the flywheel is live.

---

## 9. Open decisions for the user (answer before building the relevant stage)

1. **Ideator feedstock**: until analytics exist, should the ideator lean purely on corpus findings, or also on a hand-maintained "what's worked for us" list?
2. **Writer voice**: one house style, or per-project tone selection (camp / serious / sensual / dominant)?
3. **Publisher destinations + order**: 3dmusclecomics.com first, then which social platforms, in what priority? Any platform-specific content rules (age-gating, caption conventions)?
4. **Publish autonomy ceiling**: confirm publish stays human-approved even in Run mode (recommended), or is there a destination you'd ever let post unattended?
5. **Analytics source**: where does engagement data come from (site analytics, platform APIs, manual entry)? This determines how real the flywheel can get.
6. **Autonomy target**: is Walk the near-term goal (human approves concept/script/publish), or are you aiming straight for Run?

---

*North-star doc. Build to the contracts in §4, in the order in §8, answering §9 first for each stage. Keep this doc current as stages land — it is the map the next session reads instead of a long re-brief.*
