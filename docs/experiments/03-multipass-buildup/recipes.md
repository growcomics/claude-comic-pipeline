# Per-Panel Recipes

Exact prompts + refs for both variants on each test panel. The control prompt is derived from the panel's `action` field in the shotlist — the same content the autopilot would emit for one-shot. The multi-pass recipe is the experiment's invention.

Generation platform: **Google Flow Nano Banana 2** (free tier — submit produces 4-up, pick strongest variant).

Same character refs used in both variants. The experiment is testing GENERATION STRATEGY, not references.

---

## p05-02 — Both characters mid-growth, low-angle-back

### Variant A (control / one-shot)

**Refs to attach:** `dr-mundy/face-card.png`, `dr-mundy/body-tier3-sheet.png`, `heather/face-card.png`, `heather/body-tier3-sheet.png`, `mundy-lab-a/_source.jpg`

**Prompt:**
```
Comic panel, photoreal CGI / DAZ3D style. Camera: low-angle-back, ECU region.
Dr. Mundy (foreground left) and Heather (foreground right) standing side-by-side in the modern university space-geology lab. Mid-growth, tier 3 — both bodies taller, broader shoulders, fuller chests, leg muscles defining under straining fabric.
Heather wide-eyed with amazement; Mundy intense, satisfied. Lab coats and clothing straining at seams but holding (full coverage).
Background: lab benches, periodic table poster, solar-system poster, fluorescent drop-ceiling lighting.
No background extras. Only the named cast.
```

### Variant B (multi-pass)

**Ingredient 1 — Mundy mid-growth**
- Refs: `dr-mundy/face-card.png`, `dr-mundy/body-tier3-sheet.png`
- Prompt:
```
Comic panel, photoreal CGI / DAZ3D style. Camera: low-angle-back, ECU region.
Dr. Mundy standing alone. Mid-growth tier 3 — taller, broader shoulders, fuller chest, leg muscles defining under straining lab coat. Lab coat seams holding, full coverage. Intense satisfied expression. Plain neutral background (will be composited).
```

**Ingredient 2 — Heather mid-growth**
- Refs: `heather/face-card.png`, `heather/body-tier3-sheet.png`
- Prompt:
```
Comic panel, photoreal CGI / DAZ3D style. Camera: low-angle-back, ECU region.
Heather standing alone. Mid-growth tier 3 — taller, broader shoulders, fuller chest. Green crewneck and jeans straining at seams, full coverage. Wide-eyed with amazement. Plain neutral background (will be composited).
```

**Ingredient 3 — Lab scene plate**
- Refs: `mundy-lab-a/_source.jpg`
- Prompt:
```
Comic panel, photoreal CGI / DAZ3D style. Camera: low-angle-back, wide.
Modern university space-geology lab interior. Lab benches, periodic table poster on left wall, solar-system poster on right wall, fluorescent drop-ceiling lighting, microscope on bench, monitor on bench. Empty — no people.
```

**Composite**
- Refs: Ingredient 1, Ingredient 2, Ingredient 3 (the three saved outputs above)
- Prompt:
```
Composite panel. Place Mundy ingredient at foreground-left and Heather ingredient at foreground-right of the lab scene plate. Both characters facing into the room (camera is low-angle-back). Match lighting from the lab plate (fluorescent overhead). Photoreal CGI.
```

---

## p02-02 — Lenny + Mundy MCU high-angle

### Variant A (control / one-shot)

**Refs:** `dr-mundy/face-card.png`, `lenny/face-card.png`, `mundy-lab-a/_source.jpg`

**Prompt:**
```
Comic panel, photoreal CGI / DAZ3D style. Camera: medium close-up, high-angle (camera elevated 4-5 ft above subjects).
Lenny (dark-haired man in blue overalls) tilts his head curiously, looking at Dr. Mundy. Mundy smugly folds her arms across her chest. Both in the modern university space-geology lab.
Lenny: dark hair, blue overalls over a tee. Mundy: lab coat over dark top.
Speech bubble from Lenny: "Really? What do you do?"
Speech bubble from Mundy: "I'm a space geologist."
No background extras. Only the named cast.
```

### Variant B (multi-pass)

**Ingredient 1 — Lenny (identity-locked)**
- Refs: `lenny/face-card.png`
- Prompt:
```
Comic panel, photoreal CGI / DAZ3D style. Camera: medium close-up, high-angle.
Lenny standing in a lab. Dark hair, blue overalls over a plain tee. Tilts his head curiously, looking off-camera. Solo, no other people. Plain background.
```

**Ingredient 2 — Mundy (arms-folded pose)**
- Refs: `dr-mundy/face-card.png`
- Prompt:
```
Comic panel, photoreal CGI / DAZ3D style. Camera: medium close-up, high-angle.
Dr. Mundy standing in a lab. Lab coat over dark top. Arms folded across chest, smug expression. Solo, no other people. Plain background.
```

**Ingredient 3 — Lab scene plate (high-angle)**
- Refs: `mundy-lab-a/_source.jpg`
- Prompt:
```
Comic panel, photoreal CGI / DAZ3D style. Camera: high-angle (4-5 ft elevation), looking down into the lab.
Empty modern university space-geology lab. Lab benches, posters on walls. No people.
```

**Composite**
- Refs: Ingredient 1, Ingredient 2, Ingredient 3
- Prompt:
```
Composite panel. Place Lenny ingredient at left and Mundy ingredient at right of the lab scene plate, facing each other. Camera is high-angle MCU. Match lighting.
Speech bubble from Lenny: "Really? What do you do?"
Speech bubble from Mundy: "I'm a space geologist."
```

---

## p05-04 — Bicep ECU with mirroring BG arm

### Variant A (control / one-shot)

**Refs:** `dr-mundy/face-card.png`, `dr-mundy/body-tier4.png`, `heather/face-card.png`, `mundy-lab-a/_source.jpg`

**Prompt:**
```
Comic panel, photoreal CGI / DAZ3D style. Camera: ECU region, low-angle-front.
Bicep close-up. Dr. Mundy's right bicep flexes involuntarily, swelling against the lab-coat sleeve. Sleeve is taut but seams hold (full coverage). Veins beginning to show.
In the BACKGROUND (defocused), Heather's right arm mirrors the swell — same flex, same partial sleeve strain, blurry but identifiable.
Modern lab interior in deep BG. No background extras.
```

### Variant B (multi-pass)

**Ingredient 1 — Mundy's bicep (FG hero)**
- Refs: `dr-mundy/face-card.png`, `dr-mundy/body-tier4.png`
- Prompt:
```
Comic panel, photoreal CGI / DAZ3D style. Camera: ECU region, low-angle-front.
Dr. Mundy's right bicep close-up, flexing, swelling against the lab-coat sleeve. Sleeve taut, seams holding, full coverage. Veins beginning to show. Plain neutral background.
```

**Ingredient 2 — Heather's mirroring arm (BG element)**
- Refs: `heather/face-card.png`, `heather/body-tier4.png`
- Prompt:
```
Comic panel, photoreal CGI / DAZ3D style. Camera: medium, low-angle-front.
Heather's right arm flexing, sleeve strained, partial bicep swell visible. Slight motion blur / defocus to suggest BG position. Plain neutral background.
```

**Ingredient 3 — Lab scene plate**
- Refs: `mundy-lab-a/_source.jpg`
- Prompt:
```
Comic panel, photoreal CGI / DAZ3D style. Camera: ECU region, low-angle-front, shallow depth of field.
Lab interior, defocused. Lab benches, posters, fluorescent lighting — all softened by depth of field.
```

**Composite**
- Refs: Ingredient 1, Ingredient 2, Ingredient 3
- Prompt:
```
Composite panel. Mundy's flexing bicep dominates the foreground (ECU). Heather's mirroring arm visible in the mid-background, defocused. Lab scene plate as deep BG. Camera: ECU low-angle-front, shallow depth of field. Match lighting.
```

---

## p03-03 — Heather tips bag, birds-eye  *(staged for follow-up if time)*

### Variant A (control / one-shot)

**Refs:** `dr-mundy/face-card.png`, `heather/face-card.png`, `mundy-lab-a/_source.jpg`

**Prompt:**
```
Comic panel, photoreal CGI / DAZ3D style. Camera: medium close-up, birds-eye (directly overhead, 90°).
Heather and Dr. Mundy in the modern lab, viewed from straight above. Heather has tipped a small paper bag upside down over her own cupped left palm — a small rock is just sliding out (visible at the bag's mouth). Mundy is angry, still scowling.
Heather is holding the bag. Mundy is NOT holding the bag.
Speech bubble from Mundy: "Just tell me who you are and why you're bothering me!"
Speech bubble from Heather: "Oh sorry..."
No background extras.
```

### Variant B (multi-pass)

**Ingredient 1 — Heather tipping bag (prop-locked)**
- Refs: `heather/face-card.png`
- Prompt: Solo Heather, birds-eye view, holding paper bag in right hand, tipping it over cupped left palm. Rock visible just leaving the bag. Plain background.

**Ingredient 2 — Mundy angry**
- Refs: `dr-mundy/face-card.png`
- Prompt: Solo Mundy, birds-eye view, standing, angry scowl. Plain background.

**Ingredient 3 — Lab plate (birds-eye)**
- Refs: `mundy-lab-a/_source.jpg`
- Prompt: Lab floor + bench from directly above. No people.

**Composite**
- Refs: Ingredients 1-3
- Prompt: Birds-eye composite. Heather at left tipping bag (rock falling), Mundy at right scowling. On the lab plate. Match lighting.
Speech bubbles per Variant A.

---

## p01-01 — Wide establishing shot  *(staged for follow-up if time)*

### Variant A (control / one-shot)

**Refs:** `lenny/face-card.png`, `carl/face-card.png`, `mundy-lab-a/_source.jpg`

**Prompt:**
```
Comic panel, photoreal CGI / DAZ3D style. Camera: cowboy (wide, full-body upward to chest), low-angle-back.
WIDE ESTABLISHING SHOT of the modern university space-geology lab. Wall posters of the solar system AND periodic table visible. Clean stainless lab benches with a microscope and flat-screen monitor. Workout corner with barbell and plates visible. Drop ceiling with fluorescent lighting panels.
Lenny (dark-haired, blue overalls) and Carl (blonde, plain tee) seen from behind, mid-room, working at a bench.
Speech bubble from Carl: "There, that's the last one..."
No background extras.
```

### Variant B (multi-pass)

**Ingredient 1 — Full lab environment (the "scene plate")**
- Refs: `mundy-lab-a/_source.jpg`
- Prompt:
```
Comic panel, photoreal CGI / DAZ3D style. Camera: cowboy / wide, low-angle-back.
WIDE ESTABLISHING SHOT of modern university space-geology lab. Solar-system wall poster on right, periodic table poster on left, both clearly visible. Lab benches with microscope and monitor. Workout corner with barbell and plates visible at one end. Drop ceiling with fluorescent panels. Empty — NO people. All environmental elements present.
```

**Ingredient 2 — Lenny (back view)**
- Refs: `lenny/face-card.png`
- Prompt:
```
Lenny seen from behind, full body, standing at a lab bench. Dark hair, blue overalls. Plain background.
```

**Ingredient 3 — Carl (back view)**
- Refs: `carl/face-card.png`
- Prompt:
```
Carl seen from behind, full body, standing at a lab bench. Blonde hair, plain tee. Plain background.
```

**Composite**
- Refs: Ingredients 1-3
- Prompt:
```
Composite panel. Drop Lenny and Carl ingredients into the lab scene plate, mid-room at a bench, seen from behind. Cowboy framing, low-angle-back. Match lighting.
Speech bubble from Carl: "There, that's the last one..."
```

---

## Execution order

Run in this order — calibration before scaling:
1. **p05-02** (clearest expected win — cast-count drop is the canonical multi-pass test)
2. **p02-02** (different failure mode — identity confusion)
3. **p05-04** (third failure mode — FG/BG integration)
4. **p03-03** (if time permits)
5. **p01-01** (if time permits)

After each panel, save A and B outputs in `outputs/{control,multipass}/` with neutral labels (NOT "control" / "multipass" in the user-visible filenames — that would bias the rater). See `outputs/README.md` for the relabeling scheme.
