# Grow-Island — Style Study, Cast/Story Bible & Continuity Audit

Reverse-engineered from the full 63-page *Grow Island* pilot (Page_01–Page_63).
This is the deep reference behind `preset.md`. Three parts:

1. **Style study** — how it's shot, framed, colored, lettered (the art direction)
2. **Story bible** — cast, locations, plot (task: reverse-engineer)
3. **Continuity audit** — every drift/inconsistency found, with fixes

---

## PART 1 — STYLE STUDY

### 1.1 Page construction — the defining trait

**Every single one of the 63 pages is one full-bleed splash. Zero multi-panel
grids. Zero interior gutters. Anywhere.** This is the structural signature: a
page is not a grid of panels, it is **one wide cinematic still** with dialogue
baked on top. Some pages carry a thin black bleed edge; title pages use black
letterbox bars. Orientation is **16:9 landscape** throughout.

Consequence for production: you do NOT build pages in `page-composer` from
multiple panel renders. You generate one image per page at the page's final
aspect, with lettering already in it.

### 1.2 Shot distance — rhythm, not randomness

The comic uses a consistent distance vocabulary tied to narrative function:

| Function | Distance | Subject fills | Notes |
|---|---|---|---|
| Dialogue / character intro | **Medium → medium-close** | 55–90% frame H | The workhorse. Eye-level, one subject dominant. |
| Scene-setting / ensemble | **Wide / establishing** | bodies 15–40% H | Group line-ups, architecture, arrivals. |
| Growth beat | **Extreme body-part crop** | body 85–95% H | Often **faceless** — torso/arm/glute only; the body IS the subject. |
| Transformation payoff | **Full-body reveal** | 70% H, head-to-thigh | One per completed transformation. |
| Intimacy / two-shot | **Medium two-shot** | 65–75% H | Plant or doorway as center divider. |

The body fills *more* of the frame the more important the body is to the beat —
talking heads sit at medium; the moment a body part changes, the camera crops
in tight on just that part.

### 1.3 Camera angle — eye-level is home base

Overwhelmingly **eye-level**. Angle changes are rare and purposeful:

- **Low-angle / worm's-eye** → monumentalize a growing or victorious figure
  (the chicken-fight "hero" shots, growing biceps).
- **Slight high-angle** → intimacy / tenderness (embraces, a partner cradled).
- **Dramatic high or dutch tilt** → reserved for stairwell/transition pages
  (converging rafters, vertiginous staircases).
- **Bird's-eye** → used once, for the night exterior establishing finale.

If you over-use dramatic angles this style breaks — the calm eye-level baseline
is what makes the rare angle land.

### 1.4 Shape & composition — photoreal forms, simple staging

The **rendering** is fully photoreal DAZ3D CGI (ray-traced skin, specular
muscle sculpting, real fabric texture) — forms are NOT simplified. What's
"simple" is the **composition**:

- **One dominant subject**, centered or symmetrically staged.
- **Backgrounds photoreal but softened** — shallow depth of field / bokeh on
  close & medium shots so the body is always the sharpest element. Backgrounds
  only resolve to full sharpness on wide reveals.
- **In-frame framing devices**: doorways bracket a figure; a potted palm
  divides a two-shot; a foreground body (often a back-to-camera torso) acts as
  a framing column and pushes glute/figure emphasis; architecture lines lead in.
- **Deliberate negative space** left open for the baked bubble stack.
- **Silhouette title device**: title/chapter pages knock out a flat white
  muscular-female double-biceps-flex SILHOUETTE that splits the logo
  "GROW [figure] ISLAND", set over a photoreal villa establishing shot.

### 1.5 Color & lighting — warm resort, two modes, one accent

**Base palette:** warm tropical resort — tans, beige, cream, golden wood-brown,
bronze tanned skin. Moderate saturation, low-to-moderate contrast.

**Two lighting modes**, switched per scene:
- **(A) Warm interior / day** — soft, flat, cozy; amber lamp glow, honey wood,
  cream upholstery. The dominant mode.
- **(B) Cool night** — navy/black sky, dark teal water, low-key drama, warm key
  light on faces; the finale adds **neon magenta + lime** deck accents.
- **Chiaroscuro** (amber sconce pools against near-black wood/stone) is reserved
  for stairwells and transitional beats.

**The one-accent rule:** each character/arc gets a single high-chroma wardrobe
hue that pops against the neutral set and reads as identity:
- Sofia → red-and-white horizontal stripes
- Skye → dusty mauve-pink
- Vivian → grey/charcoal activewear with green seams
- Contest/growth "team uniform" → **red bikini** (women) + **cyan/blue trunks** (men)

The red bikini and cyan trunks are the recurring focal pops of the back half.

### 1.6 Facial expressions — expressive, never at camera

- Expressiveness scales with distance: dialogue close-ups are **highly
  expressive** (warm open smiles, smug half-smiles, wide-eyed alarm, gasping
  strain — the standout faces are close-ups). Wide shots = small, low-detail
  faces.
- **Eye-contact convention:** characters look **at each other / off-camera**,
  never at the viewer — EXCEPT (a) the host addressing the show, and (b)
  **confessional asides** rendered against a flat plain wall (reality-TV
  interview framing).
- During growth body-part crops the face is often **cropped out entirely** —
  expression is deferred, the changing body is the whole subject.

### 1.7 Lettering — baked in, three registers

All lettering is **baked into the render** (consistent with comic-production
L19), in three registers:

1. **Speech** — white oval/round bubbles, thin (2–3px) black outline, short
   pointed tail to speaker, **ALL-CAPS bold comic sans-serif**. Multiple
   bubbles **stacked vertically down one side** carry monologue / back-and-forth.
2. **Character-ID plates** — small white rounded rectangle, thin black border,
   black ALL-CAPS **"NAME – ROLE"** (VIVIAN – FITNESS INFLUENCER, SOFIA –
   UNEMPLOYED, SKYE – PUBLICIST, ROB – MUSICIAN, VIN – FITNESS INFLUENCER,
   KUNAL – PROFESSOR). Used on intro pages; later names come via dialogue.
3. **Title / time tabs** — small black box, white ALL-CAPS ("DAY 1", "NIGHT 1").

**SFX** — bold ALL-CAPS block letters, **orange→yellow vertical gradient fill,
black outline + drop shadow, slight italic**, often a small red/orange jagged
burst graphic, placed **adjacent to the changing body part** ("GROW!", "POW!",
"BOOM", "TONED!", "CAKE", "SH—/HK"). Non-verbal sounds (*GASP*, *PHEW*,
stretched vowels "EEEEE", "RAAAA") go **inside ordinary bubbles**, not as drawn
SFX. No narration/story caption boxes beyond the ID plates and time tabs.

### 1.8 The growth-reveal grammar (signature technique)

Transformations are **on-demand, body-part-at-a-time, and monotonic** (never
shrink back). The reproducible device:

- Render each beat as a **BEFORE/AFTER POSE-REUSE PAIR** — two consecutive
  pages with **identical composition/pose**; the second shows the localized
  size increase **plus an adjacent SFX word**.
  - arms: p50 (request) → p51 "BOOM"
  - tone: p52 → p53 "TONED!"
  - waist: p54 → p55 "SH—…HK"
  - bust: p56 → p57
  - glutes: p58 → p59 "CAKE"
- Chain the "after" page **view-aware** off the "before" page job + the
  canonical face ref (Key Rules #8/#9).
- End a transformation on a **full-body reveal** (p60).
- **Growth order observed:** male physique first (whole), then female by
  request **arms → tone → waist → bust → glutes**. NOTE: this differs from the
  skill's canonical breasts→glutes→muscles order in
  `posing-and-expressions.md`; Grow-Island is request-driven, so order follows
  dialogue, not the default sequence.

---

## PART 2 — STORY BIBLE (reverse-engineered)

### 2.1 Premise

**Grow Island** is a reality-TV dating/competition show on a tropical island,
hosted by an emcee for sponsor **Grow Getter Industries (GGI)**. It reuses the
**"Bloom House"** set/format from a prior season (explicitly lampshaded; a past
"Bloom House mishap" is referenced as why the host can't "fraternize with
guests"). The hook: winning couples earn **body transformations** ("grow").
There's a running fourth-wall gag about a 24-hour uncensored stream.

### 2.2 Cast

**Women**
- **Vivian** — fitness influencer; short dark pixie/undercut, grey keyhole
  activewear + leggings, fingerless gloves; cockiest baseline (athletic tier 2).
- **Sofia** ("Sophia" in one bubble — see audit) — unemployed; long dark-brown
  wavy hair, red-and-white striped crop top, white jeans; bubbly/scatterbrained.
- **Skye** — publicist; auburn/strawberry hair (worn as a bob, later a side
  braid), dusty mauve-pink sweater; warm/easygoing. Becomes the female
  growth-arc lead in the red bikini (named "Skye" on p42).
- **Viv** — Vincent's partner (a *second* fitness-influencer woman; dark hair
  pulled back, white/grey cutout athletic top + yellow-trim leggings). Likely
  distinct from Vivian — see audit ambiguity.

**Men**
- **Host / MC ("GGI")** — brown/auburn hair, beard, grey suit; runs the show.
- **Rob** — musician; blond undercut, beard, aviators, olive jacket.
- **Vincent / "Vin"** — fitness influencer; brown swept-back undercut, athletic;
  partnered with Viv.
- **Kunal** — professor; shaggy grey/silver hair, round glasses, dark speckled
  sweater; shy; Skye's roommate & contest partner; male growth subject.
- Assorted carrier/partner men in the contest (lean→athletic).

### 2.3 Locations

One hero location reused throughout — a **multi-level tropical jungle villa**
(the "Bloom House" set). Sub-spaces seen: open-plan rattan/thatch lounge;
tiki-bar lounge; modern wood-slat lounge; bedrooms (bunk/loft beds); tiled
bathroom; stone staircase & dramatic rafter stairwell; outdoor deck + pool;
the **lagoon "arena"**; a stylized **deep-water STARFIELD backdrop** used only
for Skye & Kunal's contest pair; sundeck with loungers; oceanside night
exterior with neon deck lighting (finale).

### 2.4 Plot arc (three acts)

- **Act 1 — Introductions (p1–22).** Cover silhouette teases the FMG payoff.
  Host opens the GGI pilot, notes the reused Bloom House set, introduces the
  women (Vivian, Sofia, Skye) then the men (Rob, Vincent, Kunal). Couples and
  roommates form — Skye and shy Kunal are surprise roommates and bond; Vincent
  reunites with Viv. Pure setup; all bodies baseline.
- **Act 2 — Night 1, "Shoulder Wars" (p23–44).** First challenge is a
  chicken-fight in the lagoon. Couples pair up, change into red-bikini/blue-trunk
  swimwear, and compete through comedic, trash-talking wipeouts (Skye & Kunal
  shown against the stylized starfield). Skye & Kunal win; the host crowns them
  the first-ever Grow Island winners and calls Kunal up for his prize.
- **Act 3 — The "Grow" payoff (p45–63).** Kunal grows his physique
  (GROW!/POW!/BOOM). Then the female lead gets an **on-demand FMG
  transformation** — arms → tone → waist → bust → glutes — each a before/after
  pose-reuse pair with SFX, ending in a full-body reveal and celebration. The
  finale cuts to the **losing rival couple** at night, lamenting they're "not
  even the strongest people here anymore" and vowing revenge — setting up
  ongoing competitive stakes.

---

## PART 3 — CONTINUITY AUDIT

Findings from the full read, highest-impact first. None are render-quality
failures; they're identity/continuity items to lock before a sequel or a
re-letter.

| # | Severity | Page(s) | Issue | Fix |
|---|---|---|---|---|
| 1 | **High** | 45–49 | **Male growth-lead identity drift** — p45–47 lead has tousled wavy dirty-blond hair; p48–49 male has short straight blond hair. Cyan trunks match (implies same man), hair doesn't. | Lock ONE male face/hair ref; regen p48–49 against it, or disambiguate as two characters in dialogue. |
| 2 | **High** | 56–62 | **Multiple distinct "partner" men in the finale suite** — blond resort guy (56–60), grey-haired "partner" (61), young dark-haired teammate (62). If meant to be one partner, identity is inconsistent. | Verify against script: are these 3 separate cast or 1 drifting partner? Lock refs accordingly. |
| 3 | **Med** | 42→43 | **Skye size jump with no on-panel beat** — bust/curves go tier ~3 (contest) → ~4 (winner's lounge) between pages, no growth frame shown. | Likely intended first reward beat; if so, add a transition/SFX beat, else treat as drift. |
| 4 | **Med** | 42 vs Act 1 | **Redhead identity ambiguity** — the red-bikini growth lead is named "Skye" (p42), but Act 1 has multiple auburn/redhead women (Skye the publicist + others). Confirm the growth lead = Skye the publicist. | Establish one canonical Skye face ref spanning Act 1 → Act 3. |
| 5 | **Med** | 26/29 | **Host hair-tone drift** — reads sandy-blond in lounge group pages, auburn/brown on the night deck. | Confirm one host; lock hair tone; recolor outliers. |
| 6 | **Med** | 42–44 | **Kunal hair-tone drift** — dark-brown wavy (p42–43) → lighter blond (p44). | Lock Kunal ref; recolor p44. |
| 7 | **Low** | 19–20 vs 21 | **Skye hair restyle mid-conversation** — loose bob → side braid within one scene. | Pick one; or justify (she braided it). |
| 8 | **Low** | 6 vs 7 | **Name spelling** — "SOPHIA" (p6 dialogue) vs "SOFIA" (p7 ID plate). | Pick canonical spelling; fix the other. |
| 9 | **Low** | 36/40/42 vs 35/37/39 | **Contest backdrop split** — same contest staged against a detailed lagoon AND a flat starfield. Internally consistent as a per-couple device (starfield = Skye/Kunal) but reads as a setting mismatch if intended as one shared pool. | Decide: stylistic per-couple mode (keep) vs one pool (unify). |
| 10 | **Low** | 54–55 | **Unrequested bust uptick** — breast tier ticks ~3.5→4 during the *toning* request, no bust request. | Minor; align to dialogue or add a bust beat. |
| 11 | **Low** | name | **Vivian vs Viv** — possibly two different fitness-influencer women (Vivian solo intro; Viv = Vincent's partner). | Confirm whether one or two characters; name distinctly. |

**What's solid (positive findings):**
- Growth in the dedicated Act-3 arc is **cleanly monotonic** — no reversions.
- **Wardrobe accents are stable** within each character (red bikini, cyan
  trunks, mauve sweater, striped top); clothing strains/tears but the hue holds.
- **Faces hold within each close-up sequence**; drift only appears across
  scene cuts (the items above).
- **100% single-splash format consistency** — no layout drift across 63 pages.
- **World-building is consistent** — "Bloom House" / GGI references line up
  across multiple speakers.

---

## Source

Full pilot: `~/Downloads/grow island/Page_01.jpg … Page_63.jpg` (63 pages,
16:9, photoreal DAZ3D CGI). Analyzed 2026-05-28.
