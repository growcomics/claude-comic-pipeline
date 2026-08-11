# Owner defect walkthrough — autopilot-test (2026-08-10)

Source: owner reviewed https://3dmusclecomics.com/studio/review.php?p=autopilot-test (120 panels, Flow Autopilot run of 2026-08-09) beat by beat, in their own words. This file is CALIBRATION GROUND TRUTH for the judge/ranker in the over-generate→judge→retry lane and for the defect registry. Registry maintainers: align IDs in skills/comic-production/references/DEFECT-REGISTRY.md with these observations; lane builders: these are the detector + severity specs the owner actually cares about.

## Per-beat observations (verbatim intent, structured)

| Beat | Observation | Defect class | Notes for detector/prevention |
|---|---|---|---|
| B2 | Lab coat suddenly OFF vs prior beat | **Wardrobe state continuity** | Garment on/off must persist across beats unless a transition panel shows the change. Detector: per-character garment-state tracking across consecutive beats. |
| B2–B3 | Two people talking rendered as FULL-BODY wide shots | **Camera grammar / shot-scale mismatch** | "When two people are talking it's torso-up or tighter. We're breaking the cinematic filmmaker's guide we made" → enforce skills/continuity-check/cinematic-framing.md: dialogue beats default to medium/medium-close-up. Detector: shot-scale classifier vs beat type. |
| B7 | Lab coat off again, no transition panel | Wardrobe state continuity | Same as B2. A half-on/half-off transition panel would legitimize the change. |
| B7 | Character breaks the fourth wall (looks into camera) | **Fourth-wall gaze (AI ref-pose bleed)** | Root cause: forward-facing reference images bias output to face camera. Prevention: 3/4 + profile view packs in refs; detector: gaze-at-camera on non-POV beats. Acceptable only rarely/deliberately. |
| B8 | Jacket suddenly dirty | **Garment condition continuity** | Soil/damage state is part of wardrobe lock, not just the garment itself. |
| B13 | Speech bubble is BLUE where every other bubble is white | **Lettering style consistency** | Bubble style/color must be uniform project-wide. Easy detector (color histogram on bubble regions). |
| B14 | Chair positions changed between beats | **Set/prop continuity** | Environment object layout must persist within a scene. |
| B14 (+recurring) | "Constantly doing these full-body shots everywhere — way too much" | **Shot-scale monotony** | Recurring systemic failure, not one-off. Shot-scale distribution per page must vary (see cinematic-framing rubric). |
| B15 | Extreme facial close-up with no narrative reason | Shot-scale mismatch (other direction) | Scale must fit the beat's purpose — both too-wide AND too-close are failures. |
| B18 | "Unimpressive: angle poor, lighting/shadows flat, no exertion emotion — flat face, background characters flat, not laid out dynamically" | **Dead-face + flat staging + flat lighting** (compound) | Money-shot beats need exertion/emotion expression, dynamic angle, directional lighting, staged (not lined-up) background cast. Maps to corpus findings (expression-intensity, camera-dynamism) + L35. |
| B19 | Lifting an "empty/glitch bar", rest of the barbell lying on the ground | **Object integrity / prop glitch** | Physically incoherent props = insta-kill class. Detector: equipment integrity check. |
| B20 | "Her SKIN is torn like clothing — recurring problem" | **Skin-rendered-as-torn-fabric** | Known recurring class: model confuses skin with garment and applies tear/damage to skin. INSTA-KILL. (Garment tearing at seams is fine per always_clothed rules; skin tearing never.) |
| B23 | "Not busty/curvy/muscular enough — very generic. My Flow work is way, way rounder and bigger" | **Body under-scaling vs owner standard** | Confirms feedback_chest_oversize_compensate + growth-density mandate: model scales DOWN; specs must over-shoot. Ranker: compare body scale against the owner's ⭐ Flow picks as the reference distribution, not against 'realistic'. |

## Implicit judge calibration extracted

- **Insta-kill tier** (from tone + "recurring problem" emphasis): skin-torn-as-fabric (B20), glitch/incoherent props (B19), wardrobe state flips with no transition (B2/7/8).
- **Systemic quality tier** (degrades everything, retry-worthy): shot-scale monotony (full-body default), dead-face/flat staging/flat lighting on beats that should have energy, fourth-wall gaze.
- **Consistency tier** (uniformity checks, cheap detectors): bubble style/color, prop layout, garment condition.
- **Taste/ranker signal**: body scale should match the owner's own Flow favorites (rounder/bigger), NOT generic-realistic. The screenshotted Beat-~20 panel (redhead flex, torn tank, green amulet glow) shows the production standard the owner engages with.
- **Camera doctrine**: the existing cinematic-framing.md rubric is the owner's stated standard ("the whole cinematic filmmaker's guide thing we made") — the lane must actually ENFORCE it per beat type, not merely include it.

## UX notes fixed same day
- Lightbox: full-size affordance was undiscoverable → added ⤢ 100% + ⤓ Original buttons + tip chip.
- Dense grid: winners hard to spot → thick accent ring + bigger check on approved tiles in dense mode.
