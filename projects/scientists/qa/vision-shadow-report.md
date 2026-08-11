# Vision-Shadow Agreement Report — `scientists`

> **ADVISORY SIDECAR.** Nothing in this report gates anything. The shadow reads
> banked state and writes `qa/receipts/*.vision.json` advisory files only; the
> compose→audit→bank→verify chain and its integrity manifest are untouched.

- Generated: 2026-08-11T06:28:53Z  ·  Scope: **82 panels**  ·  Image coverage of banked logs: **100.0%**
- Ground truth: banked chain verdict.json (+ notes-classification.json soft labels)
- Vision side: rubric v3 categories + v5 confidence semantics + face cards (`qa/vision-shadow/rubric.md`, sha256 `1ee8927bcbd6d899…`), detections counted at confidence high+medium.
- Agreement is scored per COMPARISON GROUP (canonical registry IDs bucketed — see `vision_shadow.py group_of_id`); registry IDs are cited per flag in the advisory receipts.

## Headline

- Defective panels (per ground truth): **14** — shadow flagged the SAME defect group on **4** (29%), flagged anything at all on 8.
- Clean panels (per ground truth): **68** — shadow agreed clean on **38** (56%).

## Per-group agreement (ship bar: recall ≥ 80%, precision ≥ 70%, support ≥ 5)

| Group | Support | agree-fail (TP) | vision-only (FP) | subagent-only (FN) | agree-pass (TN) | Recall | Precision | Verdict |
|---|---|---|---|---|---|---|---|---|
| WARD | 2 | 1 | 22 | 1 | 58 | 50% | 4% | insufficient-support |
| HAIR | 2 | 1 | 17 | 1 | 63 | 50% | 6% | insufficient-support |
| IDENT | 0 | 0 | 3 | 0 | 79 | n/a | 0% | insufficient-support |
| COUNT | 1 | 1 | 3 | 0 | 78 | 100% | 25% | insufficient-support |
| SIZE | 0 | 0 | 8 | 0 | 74 | n/a | 0% | insufficient-support |
| ANATOMY | 0 | 0 | 1 | 0 | 81 | n/a | 0% | insufficient-support |
| COMPOSITE | 1 | 0 | 3 | 1 | 78 | 0% | 0% | insufficient-support |
| LETTER | 4 | 1 | 2 | 3 | 76 | 25% | 33% | insufficient-support |
| OTHER | 4 | 0 | 0 | 4 | 78 | 0% | n/a | insufficient-support |

## Disagreements — vision-only flags (35 panels)

Vision flagged a group the banked verdict didn't. Each is either a vision false
positive or a defect that ESCAPED the banked QA — the drill-down below says which
after human/orchestrator review of the flagged panels.

| Panel | Image | Vision-only groups | Vision reason (first) |
|---|---|---|---|
| `p01-01` | `projects/scientists/pages/p01-01.png` | WARD | Jim's visible leg-wear at the table shows a white stripe running down the outer leg that continues the jacket's stripe pattern, reading as matching navy tracksu |
| `p02-01` | `projects/scientists/pages/p02-01.png` | HAIR | Jill's hair reads as a saturated copper/auburn under the lab lights, noticeably more red-orange than the warmer-honey/caramel-brown base tone shown on her ident |
| `p02-02` | `projects/scientists/pages/p02-02.png` | HAIR | Direct comparison against the identity-sheet reference (warm honey/caramel-brown with blonde-ish highlights) shows Jill's panel hair reading as a more saturated |
| `p02-03` | `projects/scientists/pages/p02-03.png` | COMPOSITE | A faint cyan/blue halo is visible along the left contour of Rochelle's hair and shoulder against the blurred cabinet background — this doesn't correspond to any |
| `p02-04` | `projects/scientists/pages/p02-04.png` | HAIR | Consistent with p02-01/p02-02, Jill's long wavy hair here reads as a saturated copper/auburn, more red-orange than the honey/caramel-brown base tone on her iden |
| `p03-04` | `projects/scientists/pages/p03-04.png` | LETTER | A large 'FIZZZ' SFX is baked in over the right-side bench (near the microscope/shelving) with no fizzing liquid or reaction visible beneath it and no SFX script |
| `p05-02` | `projects/scientists/pages/p05-02.png` | HAIR | Jill's hair in this bright, close face CU reads noticeably lighter and more golden/honey-toned than the deeper caramel-brown in her identity-sheet reference - a |
| `p08-03` | `projects/scientists/pages/p08-03.png` | LETTER | "BOOM" appears twice — once beside each raised fist — while PANEL CONTEXT scripts only a single 'SFX: "BOOM"' callout; reads as an unscripted duplicated SFX rep |
| `p08-04` | `projects/scientists/pages/p08-04.png` | SIZE, WARD | Rochelle's white lab coat and teal blouse render fully intact and unstrained — no visible split sleeves, no strain lines at the blouse — while costume_state scr |
| `p08-05` | `projects/scientists/pages/p08-05.png` | SIZE, WARD | Rochelle is carrying her white lab coat draped over her arm rather than wearing it, and the teal blouse she IS wearing shows no visible strain — doesn't match t |
| `p10-05` | `projects/scientists/pages/p10-05.png` | WARD | The extreme-foreground shoulder/collar area (presumed Rochelle) shows structured light/white-toned fabric rather than the plain black tank established for her i |
| `p10-06` | `projects/scientists/pages/p10-06.png` | COUNT | A second, soft-focus humanoid silhouette (head/shoulder shape consistent with a standing figure, likely Dan continuing from the prior panel) is visible in the b |
| `p11-01` | `projects/scientists/pages/p11-01.png` | COUNT | A second character — a heavily-muscled, shirtless man at the lab bench, build consistent with Dan's established tier-9 size — is clearly visible in the backgrou |
| `p11-05` | `projects/scientists/pages/p11-05.png` | SIZE, WARD | Panel context specifies 'donny: shredded tee, grown; dan: shredded tank, grown', but both garments render fully intact — a snug, unripped grey crew-neck tee on  |
| `p11-06` | `projects/scientists/pages/p11-06.png` | HAIR, IDENT, WARD | The two background giants (continuity carry-over of Donny and Dan from p11-05) both show dark brown/black hair on their heads. This matches neither canonical re |
| `p12-02` | `projects/scientists/pages/p12-02.png` | HAIR | Two squad members read perceptibly lighter/warmer than their identity-sheet references: the ponytail leader's hair (medium ashy-brown on her reference) reads di |
| `p12-03` | `projects/scientists/pages/p12-03.png` | HAIR | The ponytail leader's hair reads as light golden/sandy-blonde with warm highlights here, compared to the cooler medium ashy-brown shown on her identity sheet. T |
| `p12-04` | `projects/scientists/pages/p12-04.png` | ANATOMY, COMPOSITE, HAIR, SIZE, WARD | Two figures show localized skin-texture rendering artifacts: the ponytail leader (leftmost) has a dark, star-shaped scribble-like mark on her deltoid that doesn |
| `p12-05` | `projects/scientists/pages/p12-05.png` | COMPOSITE, WARD | A set of 4-5 perfectly straight, evenly-spaced black parallel diagonal lines cuts across the entire frame (visible over both the torso/uniform and the leg, roug |
| `p12-06` | `projects/scientists/pages/p12-06.png` | HAIR, WARD | The 3rd cheerleader from left (pigtails hairstyle) has warm golden/honey-blonde pigtails in this panel, but her identity-sheet reference (references/characters/ |
| `p13-01` | `projects/scientists/pages/p13-01.png` | HAIR, IDENT, WARD | The pigtails cheerleader (2nd from left) again shows warm dark-blonde/light-brown pigtails here, not the silver/ash-grey from her identity-sheet reference. Same |
| `p13-02` | `projects/scientists/pages/p13-02.png` | HAIR, SIZE, WARD | The pigtails cheerleader (3rd from left) again shows warm blonde pigtails, not the silver/ash-grey of her identity-sheet reference. Same drift as p12-06 and p13 |
| `p13-03` | `projects/scientists/pages/p13-03.png` | COUNT, HAIR, SIZE, WARD | The pigtails cheerleader (visible in the right-side cluster with Rochelle) again shows warm blonde pigtails rather than the canonical silver/ash-grey from her i |
| `p13-04` | `projects/scientists/pages/p13-04.png` | IDENT, WARD | The central figure delivering Rochelle's line ("I FINISHED WHAT WE STARTED...") wears a burgundy tied button-up + black slacks -- Jill's canonical 'grown' outfi |
| `p13-05` | `projects/scientists/pages/p13-05.png` | WARD | The visible sleeve on the arm holding the flask is burgundy fabric with a rolled cuff, consistent with Jill's 'grown' burgundy button-up blouse seen in earlier  |
| `p14-01` | `projects/scientists/pages/p14-01.png` | SIZE, WARD | Jill is rendered in her BASELINE outfit -- white lab coat over a fully-buttoned, unstrained burgundy blouse -- matching her identity sheet, but this panel's cos |
| `p14-02` | `projects/scientists/pages/p14-02.png` | HAIR, WARD | Jill's hair here reads as a saturated auburn/copper-red, distinctly warmer/redder than the caramel-brown of her identity-sheet reference and than her own hair c |
| `p14-03` | `projects/scientists/pages/p14-03.png` | WARD | Jill wears a burgundy blouse with a structured collar (visible at the nape), split down the back seam -- continuing the same burgundy-blouse look from p14-01/p1 |
| `p14-04` | `projects/scientists/pages/p14-04.png` | HAIR, WARD | Hair reads as a saturated auburn/copper-red in the midtones, not just the golden rim-lit edges — a visible hue shift toward red/orange versus Jill's caramel-bro |
| `p14-05` | `projects/scientists/pages/p14-05.png` | HAIR | Same auburn/copper-toned hair as the preceding face-CU panel — a visible hue shift toward red/orange versus Jill's caramel-brown identity-sheet reference. |
| `p14-06` | `projects/scientists/pages/p14-06.png` | HAIR, SIZE, WARD | Jill's hair (left) reads as a warm auburn/copper tone, a visible shift from her caramel-brown reference, even under this flatter overcast light (less attributab |
| `p15-01` | `projects/scientists/pages/p15-01.png` | WARD | Scripted costume_state is 'track jacket, grown' (CAST CANON's grown wardrobe is a strained white tank top + open lab coat + grey joggers, as correctly rendered  |
| `p15-02` | `projects/scientists/pages/p15-02.png` | WARD | Same drift as p15-01: scripted 'grown' tier should show the white tank top + open lab coat + grey joggers (per CAST CANON and the p14-06 establishing panel), bu |
| `p15-04` | `projects/scientists/pages/p15-04.png` | WARD | Rochelle is scripted 'shredded jacket + straining tank' but is rendered wearing a collared teal blouse, torn grey skirt, and open white lab coat (her baseline g |
| `p16-01` | `projects/scientists/pages/p16-01.png` | HAIR | Rochelle's hair falls to shoulder/collarbone length in this panel, longer than the crisp chin-length bob shown in references/characters/rochelle/identity-sheet. |

## Disagreements — subagent-only flags (10 panels)

The banked verdict recorded a defect group the shadow missed (vision false
negatives — these cap recall).

| Panel | Image | Missed groups | GT severity | GT issue |
|---|---|---|---|---|
| `p01-03` | `projects/scientists/pages/p01-03.png` | LETTER | — | Transcription: Rochelle balloon 'FORGET IT. I'M LATE FOR THE LAB.' Exact match. Flat white oval bubble, black outline, all-caps. Tail direct |
| `p03-04` | `projects/scientists/pages/p03-04.png` | HAIR | — | Transcription: thought cloud 'THE SUGAR HELPS IT BIND. DRINK UP.' Exact match to spec. Correct bubble TYPE -- rendered as a scalloped/cloud- |
| `p03-05` | `projects/scientists/pages/p03-05.png` | OTHER | — | Transcription: caption 'SHE FINISHED THE WHOLE CUP.' + SFX 'GLOW'. Exact match to spec. Caption renders as a flat yellow rounded-rectangle b |
| `p04-06` | `projects/scientists/pages/p04-06.png` | WARD | — | Runner verdict was FAIL solely on nipple show-through under the opaque strained blouse. Orchestrator override to PASS: house always-clothed  |
| `p05-03` | `projects/scientists/pages/p05-03.png` | OTHER | — | Transcription: Rochelle speech balloon 'THIS ISN'T OVER, JILL.' + SFX 'CRUNCH'. Exact match, correct speech-balloon type with tail to Rochel |
| `p06-06` | `projects/scientists/pages/p06-06.png` | OTHER | — | Fresh run, recomposed prompt. Take 1 (job 22e16ceb-4d90-4083-aeef-38d7cb0f9476, verbatim work/final-p06-06.txt, aspect_ratio 3:4 echoed and  |
| `p10-01` | `projects/scientists/pages/p10-01.png` | LETTER | — | Take 1 (job 465da1a9-d105-4b30-acce-b4f63b1f1894) returned status=failed, no image. Take 2 (job 523f0f08-8a1f-40f0-b83c-77c228301810) PASSED |
| `p10-05` | `projects/scientists/pages/p10-05.png` | OTHER | — | Transcription: Rochelle balloon 'STAND STILL.' | Dan balloon '...YES.' | SFX 'SNAP'. All exact. Take 1 (job 082df87b-5878-4c9a-b8df-193bae2d |
| `p10-06` | `projects/scientists/pages/p10-06.png` | LETTER | — | Take 1 (job 238489c7-e1d8-48f2-b3e2-7d2dbb99afb0) PASSED: Rochelle correctly in BLACK tank + jeans (fixed from prior teal-blouse failures),  |
| `p16-01` | `projects/scientists/pages/p16-01.png` | COMPOSITE | — | FAIL then PASS. take1 (job 5e55246c-4e5d-4987-bcdb-9b600ff58235, aspect 16:9, same medias): job returned status "failed" (no image produced, |

## Full panel matrix

| Panel | GT groups (sev) | Vision groups | agree-fail | vision-only | subagent-only |
|---|---|---|---|---|---|
| `p01-01` | clean | WARD | — | WARD | — |
| `p01-02` | clean | clean | — | — | — |
| `p01-03` | LETTER | clean | — | — | LETTER |
| `p01-04` | clean | clean | — | — | — |
| `p01-05` | clean | clean | — | — | — |
| `p02-01` | clean | HAIR | — | HAIR | — |
| `p02-02` | clean | HAIR | — | HAIR | — |
| `p02-03` | clean | COMPOSITE | — | COMPOSITE | — |
| `p02-04` | clean | HAIR | — | HAIR | — |
| `p03-01` | clean | clean | — | — | — |
| `p03-02` | HAIR | HAIR | HAIR | — | — |
| `p03-03` | COUNT | COUNT | COUNT | — | — |
| `p03-04` | HAIR | LETTER | — | LETTER | HAIR |
| `p03-05` | OTHER | clean | — | — | OTHER |
| `p04-01` | clean | clean | — | — | — |
| `p04-02` | clean | clean | — | — | — |
| `p04-03` | clean | clean | — | — | — |
| `p04-04` | clean | clean | — | — | — |
| `p04-05` | clean | clean | — | — | — |
| `p04-06` | WARD | clean | — | — | WARD |
| `p05-01` | clean | clean | — | — | — |
| `p05-02` | clean | HAIR | — | HAIR | — |
| `p05-03` | OTHER | clean | — | — | OTHER |
| `p05-04` | clean | clean | — | — | — |
| `p05-05` | clean | clean | — | — | — |
| `p06-01` | clean | clean | — | — | — |
| `p06-02` | clean | clean | — | — | — |
| `p06-03` | clean | clean | — | — | — |
| `p06-04` | clean | clean | — | — | — |
| `p06-05` | clean | clean | — | — | — |
| `p06-06` | OTHER | clean | — | — | OTHER |
| `p07-01` | clean | clean | — | — | — |
| `p07-02` | clean | clean | — | — | — |
| `p07-03` | clean | clean | — | — | — |
| `p07-04` | clean | clean | — | — | — |
| `p07-05` | clean | clean | — | — | — |
| `p08-01` | clean | clean | — | — | — |
| `p08-02` | clean | clean | — | — | — |
| `p08-03` | clean | LETTER | — | LETTER | — |
| `p08-04` | clean | SIZE, WARD | — | SIZE, WARD | — |
| `p08-05` | clean | SIZE, WARD | — | SIZE, WARD | — |
| `p09-01` | clean | clean | — | — | — |
| `p09-02` | clean | clean | — | — | — |
| `p09-03` | clean | clean | — | — | — |
| `p09-04` | clean | clean | — | — | — |
| `p09-05` | clean | clean | — | — | — |
| `p10-01` | LETTER | clean | — | — | LETTER |
| `p10-02` | clean | clean | — | — | — |
| `p10-03` | LETTER | LETTER | LETTER | — | — |
| `p10-04` | clean | clean | — | — | — |
| `p10-05` | OTHER | WARD | — | WARD | OTHER |
| `p10-06` | LETTER | COUNT | — | COUNT | LETTER |
| `p11-01` | clean | COUNT | — | COUNT | — |
| `p11-02` | clean | clean | — | — | — |
| `p11-03` | clean | clean | — | — | — |
| `p11-04` | clean | clean | — | — | — |
| `p11-05` | clean | SIZE, WARD | — | SIZE, WARD | — |
| `p11-06` | clean | HAIR, IDENT, WARD | — | HAIR, IDENT, WARD | — |
| `p12-01` | clean | clean | — | — | — |
| `p12-02` | clean | HAIR | — | HAIR | — |
| `p12-03` | clean | HAIR | — | HAIR | — |
| `p12-04` | clean | ANATOMY, COMPOSITE, HAIR, SIZE, WARD | — | ANATOMY, COMPOSITE, HAIR, SIZE, WARD | — |
| `p12-05` | clean | COMPOSITE, WARD | — | COMPOSITE, WARD | — |
| `p12-06` | clean | HAIR, WARD | — | HAIR, WARD | — |
| `p13-01` | clean | HAIR, IDENT, WARD | — | HAIR, IDENT, WARD | — |
| `p13-02` | clean | HAIR, SIZE, WARD | — | HAIR, SIZE, WARD | — |
| `p13-03` | clean | COUNT, HAIR, SIZE, WARD | — | COUNT, HAIR, SIZE, WARD | — |
| `p13-04` | clean | IDENT, WARD | — | IDENT, WARD | — |
| `p13-05` | clean | WARD | — | WARD | — |
| `p14-01` | clean | SIZE, WARD | — | SIZE, WARD | — |
| `p14-02` | clean | HAIR, WARD | — | HAIR, WARD | — |
| `p14-03` | clean | WARD | — | WARD | — |
| `p14-04` | clean | HAIR, WARD | — | HAIR, WARD | — |
| `p14-05` | WARD | HAIR, WARD | WARD | HAIR | — |
| `p14-06` | clean | HAIR, SIZE, WARD | — | HAIR, SIZE, WARD | — |
| `p15-01` | clean | WARD | — | WARD | — |
| `p15-02` | clean | WARD | — | WARD | — |
| `p15-03` | clean | clean | — | — | — |
| `p15-04` | clean | WARD | — | WARD | — |
| `p15-05` | clean | clean | — | — | — |
| `p15-06` | clean | clean | — | — | — |
| `p16-01` | COMPOSITE | HAIR | — | HAIR | COMPOSITE |

> Cost: 10 sonnet vision subagents (~8-9 panels each) + 1 sonnet text classifier over 82 banked verdict notes; zero generation credits spent.
> Ground truth here is PASS-heavy by construction (banked = passed the gate); subagent-only flags come from note-mined soft labels.

## Orchestrator adjudication (Fable 5, personally viewed the disputed panels)

- `p14-01` costume flag CONFIRMED REAL at the state level: Jill renders in her baseline lab-coat + fully-buttoned burgundy blouse while the shotlist scripts "athletic top, grown" (verified against `references/characters/jill/identity-sheet.png`). Her mass reads above baseline but below full scripted tier — the paired tier flag is overstated but directionally right. The banked chain judge validates against ATTACHED refs; the shadow validates against the SCRIPTED state — that gap is exactly what it caught.
- The dense p12–p15 flag cluster (costume-state + tier + cheer-squad detail mismatches, with specific falsifiable reasons like "red sneakers vs the identity sheet's white sneakers + crew socks") is consistent with the known late-book size/state under-render bias, not hallucination; individual rows remain pending owner adjudication.
- The LETTER recall (1/4 vs note-mined LET-04 labels) is definitional: the shadow rubric treats paraphrase as legal while the banked notes log wording swaps — aligning those definitions is a rubric iteration, not a vision failure.
