# Cover/Banner Design QA — Pass i4

Fresh-context review of six renditions from `tools/cover-composer/compose_cover.py`, cross-checked against the composer source (`cover_crop()`, `cover-spec.json` params) to root-cause defects, not just describe them.

House formula: non-muscular state sharp/foreground; muscular state as a darkened glowing background TEASE; exact kicker "3D MUSCLE COMICS PRESENTS" + title; masthead legible at thumbnail size.

---

## Heather & Mark — cover-3x4.jpg — **8/10**

- **[nit]** The background tease figure's eye sits right against the panel's top-right border corner — reads slightly crowded even though it's technically unclipped by the canvas. Root cause: the framed panel leaves only a ~171px background margin on that side (`fx+fw = 0.19W+0.62W = 0.81W`), and `post_focus`/`post_zoom` (overridden to `post_focus_y:0.5, post_zoom:1.35` for the cover) happens to land her face flush against that margin's inner edge.
- **[nit]** Blurred gym-crowd extras (mouths open, mid-motion) visible low in frame behind the title. Acceptable as cover-art environment (not an in-page panel), but a couple of the faces read oddly frozen at a glance.
- Formula adherence: **correct** — Mark & Heather are both clearly non-muscular in the sharp foreground; the purple-clad female torso reads as a dark, glowing background tease.
- No bubble-crop issues — the single caption box is fully inside the panel, untruncated.
- Masthead: kicker + "HEATHER & MARK" fully legible, strong contrast, survives mental shrink to a 56×74 thumb — this is the strongest composition of the six for thumbnail read because it's a tight head-and-shoulders crop.

## Heather & Mark — banner-16x9.jpg — **8/10**

- **[should-fix]** The left zone (where site UI chrome typically overlays) is nearly filled edge-to-edge by the kicker+title+underline stack already. Little vertical clearance remains for any additional overlaid UI element without collision.
- **[nit]** Title lockup sits over a diagonal dumbbell + blurred onlooker crowd — legible thanks to bold fill/drop-shadow, but busier backdrop than necessary for a zone that must also host UI.
- Formula adherence: correct, same as cover. Caption box fully visible/uncropped.

---

## K-Pop Star — cover-3x4.jpg — **5/10**

- **[blocker] Formula violation.** The sharp foreground framed panel itself contains the *entire* muscular reveal — a mirror-split, lightning-bolt-divided before/after, both halves equally in-focus and equally prominent. This is not "muscular state as background tease," it's muscular state *in the foreground*. The genuine background tease (blurred glowing abs/bicep close-up) is present too, but it's now redundant rather than doing the teasing work on its own. Root cause is upstream of the composer: `pre_image` (`panels/pre.png`) was itself authored as a split-transformation asset, and nothing in the pipeline validates that `pre_image` is purely non-muscular before compositing.
- **[should-fix]** The raised hand beside her shoulder, inside the foreground panel, is sliced by the panel's own right-edge crop (`cover_crop()` centers on `pre_focus=0.5` with no awareness of hand position in the source), cutting off part of the fingers.
- **[nit]** Bottom ~15% of the canvas (below the fading ghost-legs) is flat dead black space, only partly offset by the title block sitting above it.
- Masthead: legible, good contrast against the dark ground.
- Thumbnail survivability: **weaker than the other two.** It's a mid/full-body two-shot rather than a head-and-shoulders crop, so both faces shrink to near-illegible dots at 56×74. The vertical lightning-bolt + pink/purple color block still reads as a recognizable shape, but character-face recognition is largely lost.

## K-Pop Star — banner-16x9.jpg — **5/10**

- **[blocker]** Same foreground-panel formula violation as the cover (identical `pre_image`).
- **[should-fix]** The left ~60% background-tease zone is a full-detail, high-contrast close-up (arm, midriff, hair) with the title lockup laid directly over image texture rather than a calmer patch. This is the busiest of the three banners for hosting additional site UI chrome — least safe-zone clearance of the set.
- **[nit]** "STAR" trails off toward the brighter garment/hip highlight; contrast dips slightly versus "K-POP," which sits on a clean dark patch.
- Masthead otherwise legible.

---

## Baywatch — cover-3x4.jpg — **6/10**

- **[blocker]** The left speech bubble is truncated by the panel's own crop boundary, reading "'s so good to just / nwind after that / crazy shift." — the leading "It" and "U" are sliced off. This sits inside the sharp, focal foreground panel, so it's highly visible and reads as a production error rather than a stylistic crop. Root cause: `cover_crop()` is purely geometric (focus fraction + zoom on the source panel) with no awareness of where baked text/bubbles sit in `pre_image`, so the chosen `pre_focus`/`pre_zoom` sliced straight through the bubble.
- Formula adherence: **correct and well-executed** — the foreground pair reads as a toned/pre-transformation baseline, and the dialogue ("my arms are actually feeling a little heavy today") does clever double-duty narrating the coming change. The background tease is genuinely dark and glowing (lightning-vein texture on the shoulder/glute), with no stray caption fragments bleeding through — the `post_topdim` scrim band is doing its job.
- Masthead: "BAYWATCH" fully legible, good contrast against the blurred torso backdrop.
- Thumbnail survivability: good — strong red/blue/tan color blocking reads clearly even shrunk to 56×74; the cut bubble text will still read as visibly "broken" at 220px hero-card size, less so at the smallest thumb.

## Baywatch — banner-16x9.jpg — **6/10**

- **[blocker]** Identical truncated speech bubble, re-cropped for the 16:9 fit ("od to just / after that / shift."). Confirms the defect is systemic to the crop parameters on this `pre_image`, not a one-off render — the same source gets clipped both times it's fit into a frame.
- **[should-fix]** A second, sharp laughing face sits in the extreme top-left corner of the banner — exactly where site nav/logo chrome commonly anchors, risking a collision with real UI.
- Formula adherence: correct, same as cover. Masthead legible, good contrast.

---

## Grades summary

| Image | Grade |
|---|---|
| Heather & Mark — cover-3x4 | 8/10 |
| Heather & Mark — banner-16x9 | 8/10 |
| K-Pop Star — cover-3x4 | 5/10 |
| K-Pop Star — banner-16x9 | 5/10 |
| Baywatch — cover-3x4 | 6/10 |
| Baywatch — banner-16x9 | 6/10 |

---

## Top-5 systemic improvements for the COMPOSER

1. **Content-aware safe-crop in `cover_crop()`.** The single most reproducible defect class: `cover_crop()` crops purely by focus-fraction + zoom with zero awareness of bubble/caption/hand/face bounding boxes baked into the source panel. This is what truncated Baywatch's speech bubble (same bug, both output sizes) and sliced K-Pop Star's hand. Add either (a) a manual exclusion-box field in `cover-spec.json` the crop window must not intersect, or (b) a lightweight bubble/text-region detector that fails the compose (or warns loudly) when the computed crop clips a text region.

2. **Validate `pre_image` is actually non-muscular before compositing.** Nothing in the pipeline checks that the "sharp foreground = non-muscular" contract holds for the resolved `pre_image`. K-Pop Star's `panels/pre.png` is itself a baked before/after split, so the composer faithfully rendered a formula violation because its input already violated the formula. Add a QA gate — ideally the repo's existing fresh-subagent audit pattern — that checks the resolved `pre_image` (and `post_image`) against the formula before compose, not just the final render after the fact.

3. **Background-tease placement safe zone.** When the framed panel leaves a narrow side margin (Heather & Mark's ~171px cover margin), `post_focus`/`post_zoom` can land a tease figure's face or hand flush against the panel border, reading as crowded/cropped even when technically unclipped. Add a computed check (or documented rule of thumb) that keeps the tease's focal point centered within the visible margin width rather than flush to the frame edge.

4. **Banner left-zone clutter/contrast budget.** The composer's own geometry reserves the framed panel for the rightmost ~30-38% of the banner (`fx=0.62W`), so the left ~60% is exactly the zone site UI chrome overlays. Right now that zone's busyness is whatever the raw tease crop produces — K-Pop Star's is a full-detail high-contrast close-up with the title dropped directly on top of texture; Baywatch's puts a sharp secondary face in the top-left corner where nav/logo chrome usually anchors. Add a stricter `post_blur`/`post_brightness` band (or a hard "keep top-left corner clear" rule) specifically for the banner variant, independent of cover tuning.

5. **Thumbnail-legibility self-check.** Since the composer already knows both target sizes, have it also render an in-memory 56×74 downscale and flag when the foreground subject's face bounding box would fall under a minimum pixel width — mid/full-body `pre_image` crops (K-Pop Star) would get flagged for a tighter `pre_zoom`, matching the tighter close-up that makes Heather & Mark the best thumbnail performer of the set.
