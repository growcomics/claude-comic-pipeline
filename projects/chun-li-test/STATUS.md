# chun-li-test
_Last updated: 2026-05-21 (30-panel expansion run on macmini Flow)_

## Stages
- ✅ **Script breakdown** — shotlist.json — **30 pages**, 2 cast (Chun Li + Bison), 1 location
- ✅ **References** — 4 refs generated natively in Flow on macmini (Matt Pro account)
- ✅ **Generation** — **30/30 panels** (p01–p10 originals + p11–p30 new arc, all in-Flow with baked lettering)
- ⏳ **Continuity** — pending full-issue audit on the new 20
- ⏳ **Composition** — n/a (lettering baked at generation per L19, no post-letter pass needed)
- ⏳ **Posting** — not started

## Flow project (macmini)
- **URL:** https://labs.google/fx/tools/flow/project/b57857fe-44f3-4b57-a782-b555e3415d5d
- **Browser:** macmini (deviceId 2a9bd64b-caf7-4f66-9bd4-0a64ab7eb6ee), PRO account
- **Model:** Nano Banana 2, x4 default, 16:9 aspect

## References generated in Flow (favorited inside the project)

| # | Name in Flow | Purpose | Source |
|---|---|---|---|
| 1 | "Chun Li hero stance reference" | Chun Li canonical SF2 face/body anchor | Text-to-image in Flow |
| 2 | "M. Bison standing villain stance" | Bison canonical SF2 dictator anchor (cape + cap + skull insignia) | Text-to-image in Flow |
| 3 | "M. Bison final form berserker" | Bison hypermuscular Psycho Power saturated form anchor (p23–p27) | Text-to-image in Flow |
| 4 | "Bison's villain chamber throne" | Throne / dais / Shadaloo banners scene reference | Text-to-image in Flow |

All four refs visible in the Favorites panel inside the Flow project.

## Cast

### chun-li (canonical SF2)
Twin buns + red ribbons, brown eyes, defined cheekbones. Tier 2 baseline → tier 7 peak-form bodysuit (cobalt+gold, high leg cuts, silver gauntlets, white sash). L33 always-clothed.

### bison (NEW, p11+)
M. Bison canonical SF2 dictator design — red Shadaloo tunic with gold buttons, white epaulettes, red cape, red peaked cap with silver Shadaloo skull insignia, black goatee, glowing pale-violet eyes. Tier 1 baseline → Tier 8 hyper-Psycho-Power saturated berserker form (p23–p28) → reverted Tier 1 defeated (p29–p30).

## Story arc (30 panels)

### Pages 1–10 (original — Chun Li solo transformation arc, ON DISK)
Chun Li enters Bison's empty chamber, absorbs ambient Psycho Power, transforms tier 2 → tier 7, new bodysuit materializes. Splashes at p01, p07, p10.

### Pages 11–15 (NEW — Bison's reveal)
- **p11** SPLASH 4/9 — Bison emerges from throne, banners behind, smug declaration
- **p12** ECU Bison face — "You THINK you've tasted my power, child?"
- **p13** Medium two-shot — Chun Li and Bison facing each other, "I tasted ENOUGH. Show me the rest."
- **p14** ECU Chun Li fierce intensity — "For my father, Bison."
- **p15** Wide two-shot with violet energy column between them — "Then COME and take it."

### Pages 16–20 (NEW — opening exchange)
- **p16** Bison Psycho Crusher launch with FOOOM SFX
- **p17** Chun Li Spinning Bird Kick intercept with WHIRRRRR SFX
- **p18** SPLASH 5/9 — mid-air collision climax with KRAKABOOM SFX
- **p19** Aftermath two-shot — "Was that ALL of you?"
- **p20** ECU Bison rage cracking — "IMPOSSIBLE."

### Pages 21–25 (NEW — Bison's escalation)
- **p21** Bison transformation begin (power-up pose, KRRRRR SFX) — "YOU FORCE MY HAND, CHILD!"
- **p22** ECU torso bursting tunic with RRIIIPPP SFX — captions "The seal he placed on himself." / "He's BREAKING IT."
- **p23** SPLASH 6/9 — Bison FINAL FORM reveal hypermuscular with FOOSH SFX — "BEHOLD MY TRUE FORM!"
- **p24** Chun Li smug reaction — "Show off." with captions "I felt his TRUE form coming a mile away." / "I'm ready."
- **p25** SPLASH 7/9 — Chun Li counter-flex with violet column + FOOSH SFX — "YOU AREN'T THE ONLY ONE WITH A TRUE FORM!"

### Pages 26–30 (NEW — climax & finale)
- **p26** Chun Li Hundred Lightning Kicks (fan-shaped multi-image kick chain) with BAM BAM BAM SFX — "HYAH HYAH HYAH HYAH HYAH!"
- **p27** Bison final-form taking impact with KRACK SFX — "HRAGH!"
- **p28** SPLASH 8/9 — Chun Li finishing Spinning Bird Kick with violet vortex + WHIRRRRR SFX — "SPINNING BIRD KICK!!!"
- **p29** Bison defeated, reverted, cap fallen on floor — "I... I cannot..."
- **p30** FINAL SPLASH 9/9 — Chun Li victorious hands-on-hips, Bison kneeling defeated, dawning gold-violet light through cathedral windows — "For my father." / "His reign of shadow is OVER." / "Today, Shadaloo falls."

## Splash count
**9 full-page splashes** across 30 panels (p01, p07, p10, p11, p18, p23, p25, p28, p30).

## Lettering
All 30 panels have **baked-in-image lettering** per L19:
- White elliptical speech bubbles with tails (regular outline = balloon, jagged outline = shout)
- Yellow rounded-rectangle internal-thought caption boxes
- Bold red SFX text (impact / damage / rip / krack)
- Bold violet SFX text (Psycho Power energy effects)
- Bold cyan-and-white SFX (kick impacts)

`allow_baked_lettering: true` — page-composer not required for lettering.

## Next steps
- (optional) Full-issue continuity audit on p11–p30 (face/wardrobe drift, monotonic body state, hard rule checks)
- (optional) Download each accepted panel JPG from Flow to `pages/panels/pXX-01.jpg` for `page-composer` PDF export
- (optional) Per-panel variant lock (currently all variants are still in the Flow project — picking the official "v1" per panel and trashing the rest would clean it up)

## Why this run was on macmini Flow not Higgsfield
Per user directive 2026-05-21: "make it 100% in flow", "I don't want to use any Higgsfield." All references generated natively in Flow from text (no uploads, per the chrome-mcp Flow-upload-block memory). All 20 new panels driven through the Flow UI with view-aware ref attachment via the + asset picker.
