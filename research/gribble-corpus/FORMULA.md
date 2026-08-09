# The Gribble Formula

Distilled from a full parse of the Gribble script corpus (`~/Documents/gribble stories/`)
on 2026-08-02 — **41 unique scripts · 1,355 pages · 5,397 panels** after dropping exact
duplicates. Every number below is measured by `profile.py`, not estimated; the machine
copy is `gribble-profile.json`. This file is the source the Command Center's
✍️ Script Writer (`studio/gribble.php`) compiles into its system prompt.

---

## 1. The format (non-negotiable)

Gribble writes an **artist-facing script**, never prose. Exact shape:

```
Title
by Gribble

Page 1
Panel 1- The scene is a street outside a house, there is a large moving truck parked...
Susan- "Alright guys, the big boss has had some complaints about you two lately."

Panel 2- Lenny is checking his watch.
Carl- "Hey Lenny, isn't it lunch time?"
```

- `Page N` alone on its line. `Panel N- ` then art direction. `Speaker- "line"` under it.
- Dialogue always in double quotes, speaker name then a hyphen. (A minority of scripts
  use `Speaker: "line"` — both are in-house, hyphen is dominant.)

> **Attribution.** The `by Gribble` line above describes *his* scripts. Generated scripts
> must never carry it — they are not his work. `studio/gribble.php` emits
> **`AI-generated · Gribble-inspired`** instead, enforced by `gr_fix_byline()` on every
> save (owner call, 2026-08-09).

## 2. The page grid — and the one deliberate break

**98.4% of pages are worth exactly four panels of space.** The four-panel grid is the
default and it is nearly absolute. But a third of pages don't *draw* four frames:

| Layout | Pages | Share |
|---|---|---|
| `1+1+1+1` — normal four-panel grid | 907 | **66.9%** |
| `4` — one image filling the whole page | 417 | **30.8%** |
| everything else (`1+3`, `1+1+1`, `1+1`, 6-panel…) | 31 | 2.3% |

The merged page is written one of two ways, both meaning "one drawing, whole page":

```
Panels 1, 2, 3 and 4- Susan transforms into a super muscular woman...
(Full page panel)- Buffy is done growing. She is floating in the air, flexing.
```

**This is the single most important structural fact in the corpus:**

> **70.3% of merged full-page slots depict growth, versus 1.7% of ordinary panels — a 41×
> enrichment.** The grid break *is* the transformation device.

Gribble runs a tight four-panel rhythm for story, and when the body changes he throws the
grid away and gives the whole page to one image. A generator that emits uniform 4-panel
pages has failed to write Gribble no matter how good the dialogue is.

## 3. Growth density

- **Growth pages: 28.9% mean / 26.8% median of every script.** Roughly one page in 3.5
  is a transformation page.
- **5.4 separate growth runs per script.** Growth is not one act-two set-piece — it
  recurs across the whole book.
- **Runs are multi-page: mean 1.7 pages, max 6, and 22.7% of runs are 3+ consecutive
  pages.** "Pages of transformation," literally.
- **First growth lands at 11% of the way in (median).** He does not make you wait; the
  engine fires on page 2–3 of a 20-page script.
- Growth is spread across the arc — the position histogram is close to flat with a mild
  mid-book dip and a bump at 80–90% (the final escalation before the payoff).

The top-density scripts show the ceiling: *The Power of Chocolate* 50% growth pages,
*Not Exactly as Planned* 49% with runs of `[6,3,2,1,2,3,1,2]`, *Social Order* 48% with
four separate 3-page runs.

## 4. Panel economy

| Measure | Value |
|---|---|
| Art direction per panel | 23 words mean, **18 median**, p90 41 |
| Dialogue lines per panel | 1.16 mean |
| Words per line | 10.1 mean, **8 median**; only 5.3% exceed 25 words |
| Silent panels (no dialogue) | **18.2%** |
| Named speakers per script | ~6 |

Panels are terse. An 18-word median direction is one clear action, not a paragraph.
Roughly one panel in five is silent — usually a reaction beat or a growth image.

## 5. The voice (writing to the artist)

He addresses the artist directly in first person plural, and hedges constantly:

- `Shot of …` (211×) — his default panel opener. `We see …` (123×), `We now …` (67×),
  `We start off with …` (24×).
- **`maybe` appears 151 times** and `or something` 33× — he offers the artist latitude:
  *"(at least a foot shorter than Susan, maybe more)"*.
- `Let's …` (112×) — `"let's make her African American for a bit of diversity"`,
  `"We'll call the men Lenny and Carl"`. Characters get named inline, casually.
- **Parenthetical asides everywhere**, clarifying scale, wardrobe state or intent:
  *(not REALLY fat, just obviously overweight)*, *(the armbands are snapping off too)*,
  *(to be clear Black and Red have their backs to the lockers)*.
- Ends on **`The End`** (110×), sometimes with a `Note:` proposing the sequel.
- Dialogue is plain and vernacular. Shouts go all-caps with stretched vowels and stacked
  punctuation: `WHAAA...!?!`, `AAAGGGHHH!!! LET GO!`, `OOOOOOHHHHHHHH!!!!!!!!!`.

## 6. Story shape

> **Corrected 2026-08-09.** The first version of this section said "ordinary woman →
> countable engine → strength feats → payoff." That was inherited from the GrowGetter
> generator's formula, not derived from Gribble, and it is **wrong** — it produced
> scripts the owner rightly called not-very-Gribble ("she saves the ward," "she beats
> her rival for team captain"). What follows is measured from `plot_scan.py`, which
> extracts the open / peak / ending of all 41 scripts.

Gribble does not write wholesome empowerment. He writes **a contested power source, a
hostile takeover of it, and an ending where somebody becomes a god and demands worship.**

### Device frequency (41 scripts)

| Device | Scripts | Share |
|---|---|---|
| Villain turn — the grower enjoys it, turns cruel, taunts, laughs | 39 | **95%** |
| Overpowering — physical humiliation of someone previously stronger | 36 | **88%** |
| Twist markers | 36 | **88%** |
| Giantess / cosmic escalation | 33 | **80%** |
| Backfire — power unstable, uncontrollable, or lost | 21 | 51% |
| Power transfer — drained, stolen, absorbed, hijacked | 18 | 44% |

### Ending type (last two pages)

| Ending | Share |
|---|---|
| **Apotheosis / domination** — godhood, conquest, a demand for worship | **71%** |
| **Deflation** — the power is lost, shrinks away, resets | 12% |
| Neither | 17% |
| Ends on an **ALL-CAPS shouted proclamation** | **59%** |

Actual closing lines: `NOW TO RULE THE WORLD!` · `KNEEL! BOW DOWN AND WORSHIP ME!` ·
`I HAVE BECOME REALITY ITSELF!` · `SOON ALL WILL WORSHIP MY DIVINE MIGHT!` ·
`NOW ALL WILL WORSHIP DOMINA THE ALMIGHTY!!!!`

### The four engines

1. **THE POWER IS CONTESTED, NOT CONSUMED.** The source is an artifact or machine that
   *anyone* can grab — a crown, cloak, belt, stone, idol, book, wand, ray, curse, wish,
   meteorite. It is not a personal supplement. Two or more characters reach for it, and
   that competition is the plot. "She drinks a smoothie and gets strong" is not a Gribble
   story; it is the first two pages of one.

2. **THE POWER CHANGES HANDS — AND THE PROTAGONIST OFTEN LOSES IT.** This is the twist.
   The character who ends up supreme is frequently *not* the one the story opened on:
   - *Superior* — Janet is erased mid-scene; **Sarah** wins and ends the universe.
   - *The Ultra-Cool Ultra-Origin of Ultra-Gal* — Dr. Mundy fakes amnesia, keeps the
     powers, and walks off as the supervillain **Domina**. The hero's origin story is
     secretly the villain's origin story.
   - *Social Order* — **Cindy**, the chubby girl who just wanted tutoring, ends as the
     goddess with the protagonist kneeling.
   - *Rivalry* — the twins cancel each other out; **Megan**, their victim, absorbs it all.
   - *The Power Belt* — the assistant, **Helen**, ends 200 feet tall.
   - *The Omega Device* — **Ox**, a background biker, becomes the god.
   - *Ultra-Gal 4* — Ultra-Gal rigs the machine in reverse, and it still can't be undone.

3. **ONE-UPMANSHIP, EXPLICITLY SIZED.** Each transformation is measured against the last
   holder, in the script text: *"she'll end up four times the size of Jill"*, *"MUCH
   bigger than Holly and Molly combined"*, *"someone growing bigger than Milo later and
   then Milo growing even bigger than that person afterwards, so take that into account."*
   The ladder is between PEOPLE, not against her own past self.

4. **DOMINANCE IS THE MONEY SHOT, NOT THE LIFT.** The payoff is one character physically
   overpowering another: lifted by the throat, stomped, flicked away with a finger,
   backhanded through skyscrapers, made to kneel. The vocabulary is contemptuous —
   `PUNY MORTAL`, `Fucking insect!`, `pathetic mortals`. Feats against objects (a couch,
   a girder) are warm-ups; feats against *people* are the climax.

### Scale ladder

Person → doorframe → vehicle → building → city → planet → universe. 80% of scripts leave
human scale entirely. The final image is usually a solo shot: floating, flexing, laughing,
often with the Earth or a galaxy for scale.

### Note on content

The raw corpus is explicit adult material — nudity, sex, orgasmic transformation, profanity.
**The plot machinery above is separable from that content**, and the generator's SFW mode
keeps the twist, the takeover, the dominance and the apotheosis while dropping the sex.
What SFW must NOT do is sand off the villain turn — that is the story, not the rating.

## 7. Generator gate (as shipped)

`studio/gribble.php` parses every draft and scores it against the rules below, then
sends one repair pass naming the exact misses. The thresholds were calibrated by
`validate_targets.py`, which runs the identical rules over Gribble's own 37
full-length scripts — **70% of them pass**.

That calibration mattered: a first draft of this gate passed only **22%** of his work,
rejecting *Social Order*, *Not Exactly as Planned* and *The Power of Chocolate* — his
three highest-growth scripts, i.e. exactly the ones worth imitating. Any rule that
rejects his good work is measuring the wrong thing.

**Aim (what the prompt asks for)** — the corpus centre:
25–35% growth pages · ~31% merged pages · first growth by 15% in · ~5 growth runs ·
one run of 3+ pages · 18-word median direction · ~18% silent panels.

**Gate (what triggers a repair pass)** — deliberately wider than the aim, so the
generator is corrected only when it is genuinely off-model:

| Rule | Fails when | Kind |
|---|---|---|
| Four-panel budget | >10% of pages aren't worth 4 panels | descriptive |
| Growth density | <20% or >55% of pages | **floor is deliberate** |
| Growth runs | <3 runs (<2 under 16pp) | descriptive |
| Run length | longest run is 1 page | descriptive |
| Grid break | <20% or >65% merged pages | **floor is deliberate** |
| Merge alignment | <45% of merged pages are growth | descriptive |
| First growth | later than 30% in | descriptive |
| Direction length | median >30 words | descriptive |
| Silent panels | <8% | descriptive |

The two **deliberate floors** — growth density and the grid-break device — are held
above his median on purpose and knowingly reject his low-growth outliers (*The Hotter
Sister*: 4.8% growth, 0% merged). Standing owner direction is that growth is the
product, so the generator imitates his best scripts rather than his average one.

Voice items aren't gated (they're not reliably measurable per-script) but are in the
prompt: `Shot of` / `We see` openers, parenthetical asides, `maybe` hedges, all-caps
shouts with stretched vowels, ~6 named speakers, ending on `The End`.
