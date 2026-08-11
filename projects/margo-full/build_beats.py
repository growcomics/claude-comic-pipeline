#!/usr/bin/env python3
"""margo-full — full-comic expansion of the Margo/Kress/investors serum arc.

Owner directive 2026-08-12: expand the 11-beat autopilot-ab chapter into a full
80-100 page comic; dialogue BAKED IN from the very beginning (L19 scope-bounded
lettering, feedback_bake_dialogue); growth density per the mandate (growth IS
the product — multiple 3+-panel growth sequences at different stages);
escalation devices per script-breakdown SKILL 4.6; camera variety per the
extension blocks.

Emits:
  runners/bakeoff/margo-full-beats.json   (beat-sheet JSON, beatsheet.schema.json)
  projects/margo-full/SCRIPT.md           (human-readable script)

Story spine (SKILL 4.7):
  WANT     Margo wants credit for the serum she built — her name on her work.
  OBSTACLE Kress owns the room, the investors, and the clipboard; his agenda is
           selling her research as his own before she can object.
  COST     Proving it means becoming the demonstration: her body, her old life
           as the invisible back-room scientist, and every seam she owns.
  PROMISE  p1: the serum + the stone react. PAYOFF: b82 finale — the reaction
           made flesh at full scale, in front of the money.
  ENDING   landed + hook (the stone pulses again: it isn't done).

Growth ladder: s1 slim scientist -> s2 athletic -> s3 heavily muscular ->
s4 beyond-bodybuilder -> s5 colossal maximum (tier bumps only, no invented
state changes). Stage anchors: the accepted winner of each reveal beat becomes
the identity anchor for that stage's subsequent beats (rolling winner-anchor,
Psycho Cammy method).
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

STYLE_V5 = (
    "Photoreal 3D CGI render, DAZ3D/Iray look, physically-based skin and fabric shading "
    "with a glossy specular sheen — hard highlights pop on flexed muscle. LIGHTING: strong "
    "DIRECTIONAL key from behind or beside the subject, never flat overhead fill; warm key "
    "against cool fill (or cool rim against a warm key); one saturated practical or FX light "
    "source coloring the scene; high contrast with deep shadow falloff; a rim light traces "
    "the body's edge and the background stays darker than the subject. BODIES: dramatically "
    "oversized, far BEYOND the reference baseline — the bust renders dramatically enlarged, "
    "well past athletic-realistic proportions, round and heavy; each bicep rivals her head in "
    "size when flexed; delts, pecs, chest and glutes carry exaggerated round mass; the "
    "physique dominates and fills the frame. Garments visibly strain and split at their seams "
    "under the mass, but coverage of chest, torso and hips is always preserved. SLEEVES: when "
    "a muscle flexes inside a sleeved garment the fabric responds physically — the sleeve seam "
    "splits open around the flexed muscle with crisp torn fabric edges; bare skin NEVER blends "
    "or gradients into fabric on the same limb. FRAMING: money shots use a LOW HERO ANGLE and "
    "a TIGHT CROP — the camera framing, not words, carries the sense of scale; the subject "
    "fills 75-90% of the frame. FACES: never blank or neutral — the emotion named in the "
    "prompt renders at full theatrical intensity. NOT 2D illustration, NOT anime, NOT cartoon. "
    "Strictly SFW: every character fully clothed; garments may strain or split at seams but "
    "skin itself is NEVER torn or damaged; chest, torso and hips stay covered. No background "
    "extras — only the named cast appears. "
    "LETTERING: classic comic-book lettering composited onto the photoreal CGI scene. The 2D "
    "comic styling applies ONLY to the bubble / caption / SFX graphics; everything else in the "
    "panel (bodies, costumes, skin, hair, environment, props, lighting) remains photoreal 3D "
    "CGI. Speech bubbles are clean WHITE rounded ovals with bold solid black outlines and bold "
    "black ALL-CAPS sans-serif comic display font, identical style on every panel, a short "
    "triangular black-outlined tail pointing to the speaker's mouth — flat 2D vector graphics, "
    "NO 3D shading, NO bevel, NO translucency, NEVER colored. Caption boxes are yellow "
    "rounded-corner rectangles with bold black outlines at a panel edge. SFX are bold flat "
    "comic display capitals with a solid black outline, no 3D extrusion. Bubble and caption "
    "text must read EXACTLY as quoted — crisp, correctly spelled, no gibberish, no duplicated "
    "bubbles. Panels with no quoted dialogue contain NO bubbles, captions, or stray text."
)

# (v5 delta vs v4: the "No text, lettering, or speech bubbles" clause is RETIRED and replaced
# with the L19 scope-bounded lettering block — owner call 2026-08-12, restoring
# feedback_bake_dialogue. Everything else carried over from v4 unchanged.)

B = []  # (id, beatKind, stage, chars, wardrobe, refs, anchor, prompt, dialogue)

def beat(id, kind, stage, chars, wardrobe, refs, anchor, prompt, dialogue=()):
    B.append(dict(id=id, beatKind=kind, stage=stage, chars=list(chars), wardrobe=wardrobe,
                  refs=list(refs), anchor=anchor, prompt=prompt,
                  dialogue=[dict(zip(("speaker", "text", "type"), d)) for d in dialogue]))

M, K, H, D, I = "MARGO", "KRESS", "HARLAN", "DEV", "INGRID"
LAB, GYM = "env-lab", "env-gym"
COAT_ON = "lab coat ON, buttoned, sleeves down; grey tank + dark leggings beneath; stone amulet at collarbone"
COAT_TIGHT = "lab coat ON but visibly TIGHT, seams strained; amulet glowing at collarbone"
TANK2 = "grey tank top + dark leggings, fits an athletic build; lab coat GONE (destroyed last scene); amulet at collarbone"
TANK3 = "grey tank top strained over heavy muscle, one shoulder seam torn open with crisp fabric edges; dark leggings; amulet glowing"
TANK4 = "grey tank top reduced to strained straps over massive muscle — seams split at both shoulders and down the back, crisp torn edges, chest/torso/hips fully covered; dark leggings straining; amulet blazing"
TANK5 = "the torn grey tank and leggings at their absolute structural limit over a colossal physique — every seam split wide with crisp torn edges, coverage of chest, torso and hips fully preserved; amulet blazing green"

# ============================== ACT 1 — THE BACK ROOM (lab corner, night) ==============================
beat("b01-establish", "connective", "s1", [M], COAT_ON, [ "margo", LAB], None,
     "WIDE ESTABLISHING shot of the cluttered lab corner at the back of the gym at night — benches of glassware, a humming centrifuge, cork boards of charts. MARGO sits hunched over a microscope, small in the frame, the only warm light a bench lamp; cool blue gym darkness beyond the doorway.",
     [(None, "GRANITE PEAK FITNESS. THE BACK ROOM. 11:48 PM.", "caption")])
beat("b02-vial", "connective", "s1", [M], COAT_ON, ["margo", LAB], None,
     "MEDIUM CLOSE-UP, eye level. MARGO lifts a vial of luminous green serum to the bench light and studies it, exhausted but quietly hopeful — expression and pose reflect that. The green glow rakes her glasses and face against the dark lab.",
     [(M, "EIGHTEEN MONTHS. IT'S FINALLY STABLE.", "balloon")])
beat("b03-stone-reacts", "connective", "s1", [M], COAT_ON, ["margo", LAB], None,
     "DETAIL EXTREME CLOSE-UP on the bench top: the serum vial standing beside the stone amulet, both pulsing the same saturated green, reflections crawling across scratched steel. MARGO's blurred silhouette watches in the background bokeh.",
     [(None, "THE STONE REACTS TO THE SERUM. IT ALWAYS HAS.", "caption"), (None, "THRMMM", "sfx")])
beat("b03b-dig-photo", "connective", "s1", [M], COAT_ON, ["margo", LAB], None,
     "DETAIL CLOSE-UP of the cork board above the bench: a faded field photo of a dig site pinned beside charts — a gloved hand holding the same stone, half-buried in rock. MARGO's fingertip touches the photo's corner at frame edge.",
     [(None, "SHE FOUND THE STONE ON A DIG. THE SERUM CAME AFTER.", "caption")])
beat("b04-kress-enters", "connective", "s1", [M, K], COAT_ON, ["margo", "kress", LAB], None,
     "KRESS strides into the lab corner and looms over MARGO's bench. Conversational TWO-SHOT, TORSO-UP medium framing, over MARGO's shoulder toward KRESS, tight staging; his smirk lit hard from the bench lamp below.",
     [(K, "WORKING LATE AGAIN, MARGO?", "balloon")])
beat("b05-clipboard", "connective", "s1", [M, K], COAT_ON, ["margo", "kress", LAB], None,
     "KRESS snatches the clipboard of results out of MARGO's hands without looking at her, dismissive. MEDIUM CLOSE two-shot, torso-up, camera slightly low behind MARGO's shoulder, the clipboard exchange dominating the frame; her hands still open where it was.",
     [(K, "I'LL TAKE IT FROM HERE.", "balloon"), (M, "THAT'S MY RESEARCH!", "shout")])
beat("b06-kress-gloats", "connective", "s1", [K], "navy tracksuit, gold chain — as reference", ["kress", LAB], None,
     "MEDIUM CLOSE-UP of KRESS alone, clipboard tucked under one arm, tapping it with two fingers, smug and unhurried — expression and pose reflect that. Slight LOW angle so he looms; bench lamp warm key from the side, lab dark behind.",
     [(K, "INVESTORS TOMORROW. BIG MONEY.", "balloon")])
beat("b07-stay-out", "connective", "s1", [M, K], COAT_ON, ["margo", "kress", LAB], None,
     "KRESS walks away toward the gym floor through the doorway, BACK to camera, clipboard under his arm — MARGO small and sharp-eyed at her bench in the mid-ground. Staged DEPTH shot, camera at her eye level so his exit towers.",
     [(K, "STAY OUT OF SIGHT.", "balloon")])
beat("b08-my-serum", "connective", "s1", [M], COAT_ON, ["margo", LAB], None,
     "MEDIUM CLOSE-UP. MARGO alone, fists pressed to the bench, jaw set, eyes burning past the camera (NOT at it) — cold fury hardening into resolve at full intensity. The green vial glow underlights her face.",
     [(M, "IT'S MY SERUM.", "balloon")])
beat("b09-hand-vial", "connective", "s1", [M], COAT_ON, ["margo", LAB], None,
     "DETAIL CLOSE-UP: MARGO's hand closing deliberately around the green vial; beside her wrist the amulet's glow flares brighter, throwing double shadows. High angle looking down on the bench.",
     [(None, "SHE DECIDES.", "caption"), (None, "VMMM", "sfx")])
beat("b10-drink", "payoff", "s1", [M], COAT_ON, ["margo", LAB], None,
     "MARGO tips her head back and drinks the serum in one motion, throat to the light, amulet flaring green against her collarbone. MEDIUM shot, DRAMATIC LOW angle in profile, green FX light flooding up across her jaw, deep shadows behind.",
     [(M, "ONE DOSE. JUST TO PROVE IT WORKS.", "thought"), (None, "GLUG", "sfx")])

# ============================== ACT 2 — FIRST CHANGE (s1 -> s2, lab corner) ==============================
# transformation scene 1 — devices: multi-panel-progressive, zoom-escalation, clothing-destruction, size-comparison
beat("b11-eyes", "connective", "s1", [M], COAT_ON, ["margo", LAB], None,
     "EXTREME CLOSE-UP on MARGO's eyes snapping wide behind her glasses, green glow blooming in the lenses, pupils tight — shock and heat at full intensity. The rest of the frame falls to darkness.",
     [(M, "OH—", "balloon"), (None, "THRUMM", "sfx")])
beat("b12-hand-flex", "connective", "s1", [M], COAT_ON, ["margo", LAB], None,
     "DETAIL EXTREME CLOSE-UP of MARGO's bare hand splayed on the bench, tendons rising, faint veins surfacing along the forearm where the cuff ends, green light crawling up the skin from the amulet's glow.",
     [(M, "WARM. IT'S SPREADING.", "thought")])
beat("b13-sleeve-tight", "connective", "s1", [M], COAT_TIGHT, ["margo", LAB], None,
     "DETAIL CLOSE-UP: MARGO's forearm and bicep swelling INSIDE the lab coat sleeve, the fabric pulling taut with visible strain lines radiating from the seam — the sleeve is intact but at its limit. Slight diagonal dutch angle.",
     [(None, "CREEAK", "sfx")])
beat("b14-sleeve-stare", "connective", "s1", [M], COAT_TIGHT, ["margo", LAB], None,
     "MEDIUM CLOSE-UP, three-quarter — MARGO raises her flexed arm and STARES at her own bicep straining the taut sleeve, eyes on the muscle, NOT at camera; astonished delight breaking across her face at full intensity.",
     [(M, "THE SLEEVE'S GETTING TIGHT!", "balloon")])
beat("b14b-both-sleeves", "connective", "s1", [M], COAT_TIGHT + "; both sleeves taut, buttons gapping", ["margo", LAB], None,
     "MEDIUM shot, front three-quarter: MARGO holds BOTH arms half-flexed before her, both coat sleeves now taut as drum skins, the button placket gapping across her chest under the strain — she looks from one arm to the other, breath quick, thrilled alarm at full intensity.",
     [(M, "BOTH ARMS. IT'S EVERYWHERE.", "balloon"), (None, "creak... creak...", "sfx")])
beat("b15-back-split", "payoff", "s1", [M], COAT_TIGHT + "; back seam actively SPLITTING", ["margo", LAB], None,
     "BEHIND THREE-QUARTER medium shot: MARGO's shoulders widen visibly and the lab coat's BACK SEAM splits open along the stitching with crisp torn fabric edges — the coat otherwise clean. Her face turned in profile surprise, green rim light tracing the tear.",
     [(None, "RRRIP", "sfx"), (M, "!!", "shout")])
beat("b16-delight", "connective", "s1", [M], COAT_TIGHT + "; back seam torn open", ["margo", LAB], None,
     "REACTION MEDIUM CLOSE-UP: MARGO half-turned, one hand over her mouth, eyes enormous with delighted disbelief — expression at full theatrical intensity. The split coat seam visible over her shoulder; warm lamp key, green fill.",
     [(M, "IT'S ACTUALLY WORKING!", "balloon")])
beat("b17-coat-off-reveal", "payoff", "s2", [M], TANK2 + "; the ruined coat dangling from one hand", ["margo", LAB], None,
     "REVEAL: MARGO shrugs out of the ruined lab coat, now visibly ATHLETIC — full-body but TIGHT framing, LOW HERO ANGLE, her new physique filling 80% of the frame, the destroyed coat trailing from one fist toward the floor. Proud rising grin, chin up — expression and pose reflect that.",
     [(M, "LOOK AT ME...", "balloon")])
beat("b18-doorframe", "connective", "s2", [M], TANK2, ["margo", LAB], "winner:b17-coat-off-reveal",
     "SIZE-COMPARISON: MARGO stands in the lab doorway flexing one arm, her shoulders now nearly spanning the frame that used to swallow her — the doorframe is the fixed gauge. MEDIUM shot, slight low angle, gym darkness behind her, green amulet key light.",
     [(M, "STRONGER. WAY STRONGER.", "balloon")])
beat("b18b-calipers", "connective", "s2", [M], TANK2, ["margo", LAB], "winner:b17-coat-off-reveal",
     "SCIENCE BEAT: MARGO clamps lab calipers around her own flexed bicep and reads the scale, eyebrows shooting up — the scientist measuring herself, delight fighting rigor. DETAIL close on calipers + bicep, her grin soft-focus above.",
     [(M, "FOURTEEN CENTIMETERS OVERNIGHT?!", "balloon")])
beat("b19-crate", "connective", "s2", [M], TANK2, ["margo", LAB], "winner:b17-coat-off-reveal",
     "MARGO lifts a loaded equipment crate one-handed to shoulder height, surprised at her own ease — eyebrows up, grin crooked. MEDIUM shot with the crate dominating the near foreground for depth, dutch diagonal.",
     [(M, "THIS WEIGHED A TON YESTERDAY.", "balloon"), (None, "CLANK", "sfx")])
beat("b20-mirror-flex", "connective", "s2", [M], TANK2, ["margo", LAB], "winner:b17-coat-off-reveal",
     "MARGO hits a tentative first double-bicep in the dark reflection of a glass cabinet, studying herself, half scientist half showman — fascinated appraisal at full intensity. OVER-SHOULDER shot INTO the reflection, bench lamp warm key.",
     [(M, "HYPOTHESIS: THIS IS AMAZING.", "balloon")])
beat("b21-tingle-again", "connective", "s2", [M], TANK2, ["margo", LAB], "winner:b17-coat-off-reveal",
     "DETAIL CLOSE-UP: the amulet pulsing slow and deep against MARGO's collarbone, her hand hovering over it, green light between her fingers. Dark frame, single FX light source.",
     [(M, "AND THE STONE ISN'T FINISHED.", "thought"), (None, "thrmm... thrmm...", "sfx")])
beat("b22-tomorrow", "connective", "s2", [M], TANK2, ["margo", LAB], "winner:b17-coat-off-reveal",
     "MEDIUM CLOSE-UP, three-quarter: MARGO looks toward the doorway to the gym floor, rolling one shoulder, wolfish determination sharpening her face — expression and pose reflect that. Cool gym light on her face, warm lab behind.",
     [(M, "TOMORROW, KRESS GETS A SURPRISE.", "balloon")])

# ============================== ACT 3 — THE PITCH (gym floor, next morning) ==============================
beat("b23-pitch-establish", "connective", "s1", [K, H, D, I], "cast as references", ["kress", "investors", GYM], None,
     "WIDE ESTABLISHING: the gym presentation area in morning light — KRESS at a whiteboard up front, THREE INVESTORS on folding chairs staged at different depths (HARLAN nearest, arms crossed; DEV mid; INGRID far, checking her watch). Nobody in a flat row; high windows throw long light shafts.",
     [(None, "NEXT MORNING. THE PITCH.", "caption")])
beat("b24-kress-pitch", "connective", "s1", [K], "navy tracksuit, gold chain", ["kress", GYM], None,
     "TORSO-UP medium of KRESS mid-pitch, clipboard raised like scripture, salesman grin at maximum wattage — expression and pose reflect that. Slight LOW angle, whiteboard formulas out of focus behind him.",
     [(K, "GENTLEMEN — THE FUTURE OF FITNESS!", "balloon")])
beat("b25-investors-cold", "connective", "s1", [H, D, I], "investors as reference", ["investors", GYM], None,
     "STAGED TRIO SHOT at three depths: HARLAN large in near-foreground profile, unimpressed, arms crossed; DEV mid-ground polishing his glasses; INGRID background tapping her phone. Long morning shadows rake the floor.",
     [(H, "WE'VE HEARD THIS SPEECH BEFORE.", "balloon")])
beat("b26-margo-watches", "connective", "s2", [M], TANK2, ["margo", GYM], "winner:b17-coat-off-reveal",
     "MARGO leans in the back hallway doorway, arms crossed over her chest, watching the pitch with narrowed eyes — simmering, patient. MEDIUM shot, she is framed BY the doorway, half in hallway shadow, gym light slicing across her face.",
     [(M, "GO AHEAD. SELL MY WORK.", "thought")])
beat("b27-harlan-challenge", "connective", "s1", [H], "investors as reference", ["investors", GYM], None,
     "TORSO-UP of HARLAN with one hand raised to stop the pitch, eyebrow up, the patient smile of a man who owns the room — expression and pose reflect that. Slight HIGH angle from Kress's position looking down the aisle at him.",
     [(H, "WHERE'S YOUR PROOF, KRESS?", "balloon")])
beat("b28-kress-sweat", "connective", "s1", [K], "navy tracksuit, gold chain", ["kress", GYM], None,
     "CLOSE-UP of KRESS laughing it off nervously, glancing sideways, a bead of sweat sliding down his temple, collar suddenly tight — flop-sweat panic under the grin at full intensity. Hard window key from behind, cool fill.",
     [(K, "PROOF! OF COURSE... HA.", "balloon")])
beat("b29-margo-steps", "connective", "s2", [M], TANK2, ["margo", GYM], "winner:b17-coat-off-reveal",
     "MARGO steps out of the hallway onto the gym floor before she can stop herself, one fist clenched, stride resolute — jaw set, eyes locked forward. MEDIUM full-length but TIGHT, camera TRACKING low beside her, morning light flaring behind.",
     [(M, "I'M THE PROOF.", "balloon")])
beat("b30-kress-freeze", "connective", "s1", [K], "navy tracksuit, gold chain", ["kress", GYM], None,
     "MEDIUM CLOSE-UP of KRESS — head and shoulders, whipping around toward the voice, eyes wide, grin collapsing — caught mid-syllable. Slight dutch angle, his gold chain mid-swing with the turn.",
     [(K, "MARGO?! NOT NOW—", "shout")])
beat("b31-investors-lean", "connective", "s1", [H, D, I], "investors as reference", ["investors", GYM], None,
     "STAGED SHOT: all three investors lean forward on their folding chairs in unison, suddenly interested — HARLAN's arms uncrossing, DEV's glasses catching light, INGRID lowering her phone. Shot from behind KRESS's shoulder for depth.",
     [(I, "AND WHO IS SHE?", "balloon")])
beat("b32-walk-past", "connective", "s2", [M, K], TANK2, ["margo", "kress", GYM], "winner:b17-coat-off-reveal",
     "TWO-SHOT with staged depth: MARGO walks PAST the frozen KRESS toward the barbell rack, not sparing him a glance, amulet glowing faint green — he is near-foreground, blurred, deflating; she is mid-ground, sharp, purposeful.",
     [(M, "WATCH CLOSELY.", "balloon")])

# ---- growth sequence 2 (s2 -> s3, public, with reaction intercuts) ----
beat("b33-round-two", "connective", "s2", [M], TANK2, ["margo", GYM], "winner:b17-coat-off-reveal",
     "MEDIUM CLOSE-UP: MARGO wraps her fist around the amulet at her collarbone; it flares BRIGHT green between her fingers, underlighting a slow, wicked grin — anticipation at full intensity. Background falls dark around the FX light.",
     [(M, "ROUND TWO.", "balloon"), (None, "THRUMM", "sfx")])
beat("b34-delts", "connective", "s2", [M], TANK2 + "; straps digging in, stitches straining", ["margo", GYM], "winner:b17-coat-off-reveal",
     "DETAIL EXTREME CLOSE-UP: MARGO's shoulders and delts SWELLING, the tank straps digging into rising muscle, stitches visibly straining at the seam — motion implied by stretched fabric and green light crawling across skin.",
     [(None, "CREEEAK", "sfx")])
beat("b34b-chest", "connective", "s2", [M], TANK2 + "; front of the tank stretching, hem rising, coverage preserved", ["margo", GYM], "winner:b17-coat-off-reveal",
     "DETAIL CLOSE-UP, front three-quarter: MARGO's chest and torso SWELLING against the tank, the fabric stretching glossy with radiating strain-lines, the hem pulling upward over her tightening waist — coverage of chest and torso fully preserved; green light rolls across the straining weave.",
     [(None, "creeeeak", "sfx")])
beat("b35-dev-react", "connective", "s1", [D], "investors as reference", ["investors", GYM], None,
     "REACTION CLOSE-UP of DEV, glasses sliding down his nose, mouth open, pen frozen above his notepad — pure disbelief at full intensity. Green FX glow from off-frame washes one side of his face.",
     [(D, "IS SHE... GROWING?", "balloon")])
beat("b36-biceps-pop", "connective", "s2", [M], TANK2 + "; shoulder seams opening", ["margo", GYM], "winner:b17-coat-off-reveal",
     "DETAIL CLOSE-UP: MARGO's biceps ballooning as she curls both arms, veins surfacing, the tank's shoulder seams POPPING open stitch by stitch with crisp torn edges. Tight diagonal frame, green key + warm rim.",
     [(None, "POP-POP-POP", "sfx")])
beat("b37-kress-react", "connective", "s1", [K], "navy tracksuit, gold chain", ["kress", GYM], None,
     "REACTION CLOSE-UP of KRESS, horrified and fascinated in equal measure, sweat now streaming, hand half-raised as if to object to physics itself — full theatrical intensity. Cool fill, green FX edge light.",
     [(K, "THAT'S IMPOSSIBLE.", "balloon")])
beat("b38-s3-reveal", "payoff", "s3", [M], TANK3, ["margo", GYM], None,
     "REVEAL money shot: MARGO at stage three — heavily muscular, dramatically bigger and rounder than before — hits a MOST-MUSCULAR crunch, torn-seam tank straining, ELEVATED-INTIMATE camera (slightly above eye line, close, personal) with her physique filling 85% of the frame; triumphant snarl-grin at full intensity.",
     [(M, "IMPOSSIBLE? I CALL IT TUESDAY.", "balloon")])
beat("b39-trio-react", "connective", "s1", [H, D, I], "investors as reference", ["investors", GYM], None,
     "STAGED TRIO REACTION at depths: HARLAN on his feet in near-foreground, chair tipping behind him; DEV pointing, half-risen, mid-ground; INGRID background with her phone raised to film. Nobody in a flat row; long shadows.",
     [(H, "GOOD LORD.", "balloon")])

# ============================== ACT 4 — FEATS OF STRENGTH (gym floor) ==============================
beat("b40-chalk", "connective", "s3", [M], TANK3, ["margo", GYM], "winner:b38-s3-reveal",
     "DETAIL CLOSE-UP: MARGO claps chalk between her palms in front of the loaded barbell, a white cloud blooming through a shaft of window light, her grin visible through the dust — relish at full intensity.",
     [(M, "LET'S TALK NUMBERS.", "balloon"), (None, "PAFF", "sfx")])
beat("b41-money-lift", "payoff", "s3", [M, H, D, I], TANK3, ["margo", "investors", GYM], "winner:b38-s3-reveal",
     "MONEY SHOT: MARGO mid-lift with a barbell loaded far beyond plausibility — the bar visibly BENDING under the plates — LOW HERO ANGLE, TIGHT crop, her exertion face blazing (teeth gritted into a grin), physique filling 85% of the frame; the INVESTORS tiny at staged depths behind, awestruck.",
     [(M, "SIX HUNDRED... EASY.", "balloon"), (None, "KRRNK", "sfx")])
beat("b41b-ingrid-fumble", "connective", "s1", [I], "investors as reference", ["investors", GYM], None,
     "REACTION CLOSE-UP: INGRID fumbling her phone mid-film, juggling it against her chest, eyes never leaving the off-frame lift — professional cool cracked wide open at full intensity.",
     [(I, "TELL ME I GOT THAT.", "balloon")])
beat("b42-dev-bar", "connective", "s1", [D], "investors as reference", ["investors", GYM], None,
     "REACTION MEDIUM CLOSE-UP of DEV gripping his folding chair with both hands, leaning so far forward he is nearly off it — glee and terror mixed at full intensity.",
     [(D, "THE BAR IS BENDING!", "shout")])
beat("b43-bar-down", "connective", "s3", [M], TANK3, ["margo", GYM], "winner:b38-s3-reveal",
     "MARGO lowers the SAME fully-loaded barbell under total control — one single intact bar, all plates on it — into a controlled floor slam, dust ring blasting outward at her feet. MEDIUM shot, slight low angle, backlit dust.",
     [(None, "WHOOM", "sfx")])
beat("b44-seam-rip", "connective", "s3", [M], TANK3 + "; the shoulder seam tearing further", ["margo", GYM], "winner:b38-s3-reveal",
     "CLOSE-UP on MARGO's shoulder: the tank's FABRIC seam rips open a little further — torn threads, crisp fabric edges, skin beneath intact and unbroken — as she rolls the shoulder. She glances at it sideways, deadpan amusement.",
     [(M, "OOPS. WARDROBE BUDGET.", "balloon"), (None, "rrrip", "sfx")])
beat("b44b-latspread", "connective", "s3", [M, H, D], TANK3, ["margo", "investors", GYM], "winner:b38-s3-reveal",
     "SHOWCASE: MARGO hits a slow LAT SPREAD for the investors, back to a mirror so both sides read, the torn shoulder seam gaping wider — HARLAN and DEV staged at two depths in the foreground corner, dwarfed. ELEVATED-INTIMATE camera, her wingspan filling the frame.",
     [(M, "STILL WITH ME, GENTLEMEN?", "balloon")])
beat("b45-tape", "connective", "s3", [M, I], TANK3, ["margo", "investors", GYM], "winner:b38-s3-reveal",
     "HUMOR TWO-SHOT: INGRID stretches a measuring tape around MARGO's flexed bicep and runs out of tape — the tab end short of closing the loop. ELEVATED-INTIMATE close framing on the bicep + tape + Ingrid's raised eyebrow.",
     [(I, "TAPE'S... TOO SHORT.", "balloon"), (M, "BUY A LONGER ONE.", "balloon")])
beat("b46-kress-reclaim", "connective", "s3", [K, M, D], "Kress rumpled; Margo " + TANK3, ["kress", "margo", GYM], "winner:b38-s3-reveal",
     "STAGED DEPTH SHOT: KRESS in near-foreground trying to reclaim the floor, gesturing weakly with the clipboard, voice-thin — while behind him the enormous MARGO flexes for a delighted DEV, both ignoring him completely.",
     [(K, "AS I WAS SAYING—", "balloon")])
beat("b47-harlan-cuts", "connective", "s1", [H, K], "investors as reference", ["investors", "kress", GYM], None,
     "HARLAN stands and cuts KRESS off mid-word with one raised palm, looking straight PAST him — impressed, decided. TWO-SHOT, torso-up, Harlan sharp in focus, Kress soft and shrinking at frame edge.",
     [(H, "QUIET, KRESS. MA'AM — YOUR TERMS?", "balloon")])
beat("b48-terms", "connective", "s3", [M], TANK3, ["margo", GYM], "winner:b38-s3-reveal",
     "MEDIUM CLOSE-UP of MARGO dusting chalk off her palms, cocky half-smile, chin tipped — a scientist discovering leverage, at full intensity. Warm window key behind her shoulder, cool fill.",
     [(M, "FULL CREDIT. MY NAME ON IT.", "balloon")])
beat("b49-kress-protest", "connective", "s1", [K], "navy tracksuit, gold chain, rumpled", ["kress", GYM], None,
     "CLOSE-UP of KRESS, finger raised in protest, tie of sweat down his temple, voice cracking — indignation curdling into desperation at full intensity. Slight HIGH angle to shrink him.",
     [(K, "IT'S MY PROGRAM!", "shout")])
beat("b50-clipboard-back", "connective", "s3", [M, K], TANK3, ["margo", "kress", GYM], "winner:b38-s3-reveal",
     "DETAIL-DRIVEN TWO-SHOT: MARGO holds the clipboard up out of KRESS's reach with two fingers, reading it idly; he grabs air below, small in the frame. Low angle up the line of her arm to the clipboard.",
     [(M, "SAYS THE DATA. MY DATA.", "balloon")])

# ---- growth sequence 3 (s3 -> s4, the demonstration for the deal) ----
beat("b51-ceiling", "connective", "s3", [M, H], TANK3, ["margo", "investors", GYM], "winner:b38-s3-reveal",
     "MARGO palms the amulet and looks at HARLAN over her shoulder with a slow, dangerous grin — an offer forming. OVER-SHOULDER framing from behind Harlan, her eyes catching the green FX glow.",
     [(M, "WANT TO SEE THE CEILING?", "balloon")])
beat("b52-amulet-blaze", "connective", "s3", [M], TANK3, ["margo", GYM], "winner:b38-s3-reveal",
     "EXTREME CLOSE-UP: the amulet BLAZING in MARGO's fist, green light flooding the frame and streaming between her fingers, her collarbone and jaw rim-lit above it. Everything else drops to black.",
     [(None, "VMMMM", "sfx")])
beat("b53-quads", "connective", "s3", [M], TANK3 + "; leggings seams straining at the thigh", ["margo", GYM], "winner:b38-s3-reveal",
     "DETAIL CLOSE-UP: MARGO's quads THICKENING, the leggings' side seams straining with visible stitch-stress lines, one seam beginning to open at the outer thigh with crisp fabric edges — coverage intact. Low diagonal frame, green key.",
     [(None, "creeeak", "sfx")])
beat("b54-lats", "connective", "s3", [M], TANK3 + "; back of the tank splitting down the middle", ["margo", GYM], "winner:b38-s3-reveal",
     "REAR THREE-QUARTER DETAIL: MARGO's lats FLARING wide as she spreads into a back pose, the tank splitting down the back seam with crisp torn edges peeling apart — green light pouring through the widening tear.",
     [(None, "RRRIP", "sfx")])
beat("b55-harlan-grip", "connective", "s1", [H], "investors as reference", ["investors", GYM], None,
     "REACTION CLOSE-UP: HARLAN gripping the back of a folding chair, knuckles white, a slow hungry grin spreading — a man watching his money multiply, at full intensity. Green FX wash from off-frame.",
     [(H, "CEILING? SHE IS THE CEILING.", "balloon")])
beat("b56-striations", "connective", "s3", [M], TANK3, ["margo", GYM], "winner:b38-s3-reveal",
     "DETAIL EXTREME CLOSE-UP on MARGO's shoulder and upper arm mid-flex: striations sharpening under sweat-sheened skin, fibers shifting, green and warm light carving every cut. No face in frame.",
     [(None, "DENSITY. DEFINITION. MORE.", "caption")])
beat("b56b-silhouette", "connective", "s3", [M], TANK3 + "; leggings seams straining at the hip, coverage preserved", ["margo", GYM], "winner:b38-s3-reveal",
     "PROFILE SILHOUETTE DETAIL: MARGO side-on against the blown-out window light, her silhouette visibly THICKENING through the hips and glutes as the growth rolls downward, leggings seams straining with crisp stitch-stress lines — coverage fully preserved; green FX pulse traces the outline.",
     [(None, "thrmm... thrmm...", "sfx")])
beat("b57-margo-face", "connective", "s3", [M], TANK3, ["margo", GYM], "winner:b38-s3-reveal",
     "FACE INTERCUT (never leave a money-run faceless): CLOSE-UP of MARGO mid-surge, head tipped back, teeth bared in ecstatic strain, green light rippling up her throat — peak-intensity expression.",
     [(M, "HAH... THERE IT IS...", "balloon")])
beat("b58-s4-reveal", "payoff", "s4", [M], TANK4, ["margo", GYM], None,
     "REVEAL money shot: MARGO at stage four — beyond-bodybuilder mass, dramatically rounder and heavier than the last stage — arms crossed over her chest in a colossal stance, LOW HERO ANGLE, TIGHT crop, physique filling 90% of the frame, torn tank seams framing the mass; imperious satisfaction at full intensity.",
     [(M, "STAGE FOUR. STILL CLIMBING.", "balloon")])
beat("b59-dev-in", "connective", "s1", [D], "investors as reference", ["investors", GYM], None,
     "REACTION SHOT: DEV scribbling numbers so fast his notepad pages flip, papers sliding off his knee, eyes never leaving off-frame MARGO — frantic conversion at full intensity.",
     [(D, "I'M IN. WHATEVER IT COSTS.", "balloon")])
beat("b60-ingrid-film", "connective", "s1", [I], "investors as reference", ["investors", GYM], None,
     "REACTION MEDIUM CLOSE-UP: INGRID filming with her phone held high, delighted, already composing the campaign in her head — expression and pose reflect that. Green FX glow rims her silhouette.",
     [(I, "THIS SELLS ITSELF.", "balloon")])
beat("b61-kress-chair", "connective", "s1", [K], "navy tracksuit, rumpled, chain askew", ["kress", GYM], None,
     "KRESS slumped onto a folding chair among the investors' empty ones, clipboard dangling from two fingers, staring at nothing — hollowed out. MEDIUM shot, HIGH angle pressing him down, one hard shaft of window light missing him.",
     [(K, "...MY GYM.", "whisper")])
beat("b62-overhead", "payoff", "s4", [M, H], TANK4, ["margo", "investors", GYM], "winner:b58-s4-reveal",
     "FEAT: MARGO one-arm presses the fully loaded barbell OVERHEAD, casually, mid-conversation with HARLAN — the bar bowed over her fist, plates stacked to the sleeve ends. ELEVATED-INTIMATE camera close on her calm face + the bar, Harlan small below.",
     [(M, "WE'LL LICENSE THE FORMULA.", "balloon")])
beat("b62b-pinky-curl", "connective", "s4", [M, K], TANK4, ["margo", "kress", GYM], "winner:b58-s4-reveal",
     "HUMOR FEAT: MARGO idly curls KRESS's prized chrome dumbbell on her PINKY finger while talking terms — KRESS watches from the side, hollow-eyed, as his trophy iron bobs like a toy. TWO-SHOT, the dumbbell arc dominating the diagonal.",
     [(M, "NICE DUMBBELL. CUTE.", "balloon")])
beat("b63-handshake", "connective", "s4", [M, H], TANK4, ["margo", "investors", GYM], "winner:b58-s4-reveal",
     "DETAIL TWO-SHOT: the handshake — HARLAN's hand disappearing entirely into MARGO's, his other hand bracing his forearm for the grip; both grinning, deal struck. Tight on the hands, faces soft above.",
     [(H, "PARTNERS. FIFTY-ONE, YOU.", "balloon")])
beat("b64-plates", "connective", "s4", [M, D], TANK4, ["margo", "investors", GYM], "winner:b58-s4-reveal",
     "SHOWCASE FEAT: MARGO stacks four 45-pound plates on one open palm like poker chips while DEV counts them, disbelieving, pen in his teeth. STAGED two-shot, plates dominant in the near frame, diagonal composition.",
     [(D, "FOUR... FIVE... THAT'S A LEG PRESS.", "balloon")])
beat("b65-bench-bend", "connective", "s4", [M], TANK4, ["margo", GYM], "winner:b58-s4-reveal",
     "FEAT DETAIL: MARGO absent-mindedly straightens a BENT barbell across her knee like a twig, bar groaning back into line, plates racked behind her. CLOSE framing on hands + bar + her unimpressed face above.",
     [(None, "KREEENK", "sfx"), (M, "KRESS BUYS CHEAP BARS.", "balloon")])

# ============================== ACT 5 — FINALE (s4 -> s5) ==============================
beat("b66-one-last", "connective", "s4", [M], TANK4, ["margo", GYM], "winner:b58-s4-reveal",
     "QUIET BEAT before the storm: MEDIUM CLOSE-UP of MARGO looking down at the amulet resting in her huge palm, its glow strobing faster — her expression softening into wonder, then sharpening into decision.",
     [(M, "ONE LAST DEMONSTRATION.", "balloon")])
beat("b67-surge-start", "connective", "s4", [M], TANK4, ["margo", GYM], "winner:b58-s4-reveal",
     "MARGO presses the amulet flat to her sternum; her WHOLE BODY halos green, hair lifting off her shoulders in the updraft, dust ringing outward at her feet. MEDIUM shot, low angle, FX light overwhelming the windows.",
     [(None, "VMMMMMM", "sfx")])
beat("b68-torso", "connective", "s4", [M], TANK5, ["margo", GYM], "winner:b58-s4-reveal",
     "DETAIL CLOSE-UP: MARGO's chest and torso EXPANDING, the tank strained to a lattice at every seam — crisp torn edges spreading, coverage of chest and torso fully preserved — green light lancing through each split.",
     [(None, "RRRRIP", "sfx")])
beat("b69-arms", "connective", "s4", [M], TANK5, ["margo", GYM], "winner:b58-s4-reveal",
     "DETAIL CLOSE-UP: MARGO's arms at their limit — each bicep now rivaling her head, forearms cabled, fists clenched at her sides as the growth rolls through them in visible waves of green light.",
     [(None, "THRUM THRUM THRUM", "sfx")])
beat("b70-cast-shield", "connective", "s1", [H, D, I, K], "cast as references", ["investors", "kress", GYM], None,
     "REACTION WIDE: all three INVESTORS and KRESS shielding their eyes against the green blaze, staged at four different depths — Harlan leaning IN toward it, Dev half-behind his notepad, Ingrid still filming, Kress cowering. Hard FX shadows streak the floor.",
     [(D, "SHE'S STILL GOING!", "shout")])
beat("b71-margo-more", "connective", "s4", [M], TANK5, ["margo", GYM], "winner:b58-s4-reveal",
     "EXTREME CLOSE-UP of MARGO's face tipped up into the light, eyes blazing green, ecstatic — the peak-intensity money-run face, teeth bared in a rapturous grin.",
     [(M, "MORE!", "shout")])
beat("b71b-height", "connective", "s4", [M], TANK5, ["margo", GYM], "winner:b58-s4-reveal",
     "SCALE BEAT: MARGO visibly GAINS HEIGHT mid-surge — her eye-line rises past the top of the whiteboard behind her, marker tray now at her waist; she looks DOWN at it, startled laugh breaking through the strain.",
     [(M, "I'M TALLER. I'M ACTUALLY TALLER!", "balloon")])
beat("b72-rack-compare", "connective", "s5", [M], TANK5, ["margo", GYM], None,
     "SIZE-COMPARISON: MARGO now stands BESIDE the barbell rack and OVERTOPS its uprights — the rack that framed her earlier feats is the fixed gauge, and she dwarfs it. FULL shot but tight, low angle, green glow ebbing to a steady pulse.",
     [(None, "THE RACK USED TO TOWER OVER HER.", "caption")])
beat("b73-floorboards", "connective", "s5", [M], TANK5, ["margo", GYM], "winner:b72-rack-compare",
     "DETAIL LOW SHOT at floor level: MARGO takes one step forward and the gym floorboards FLEX under her foot, dust jumping from the seams, plates rattling on the rack behind. Her scale carried entirely by the frame.",
     [(None, "WHOMP", "sfx")])
beat("b74-finale", "payoff", "s5", [M, K, H, D, I], TANK5, ["margo", "kress", "investors", GYM], None,
     "TRIUMPHANT FULL-PAGE FINALE: MARGO hits a colossal DOUBLE-BICEP at her absolute maximum — dramatically bigger, rounder and heavier than every prior stage — LOW HERO ANGLE from near floor level, she towers over the camera filling 90% of the frame; hard warm backlight from the high windows blows out and halos her hair and shoulders in gold against cool fill; KRESS and the INVESTORS react in awe at staged depths around her — one cropped large in near-foreground, the others smaller in mid and background, nobody in a flat row; ecstatic triumphant joy at full theatrical intensity.",
     [(M, "GRANITE PEAK'S NEW HEADLINER!", "shout")])
beat("b75-aftermath", "connective", "s5", [M, H, K], TANK5, ["margo", "investors", "kress", GYM], "winner:b74-finale",
     "AFTERMATH: dust settling in the window light. HARLAN formally hands the clipboard UP to MARGO with both hands like a treaty; far in the background KRESS sweeps scattered plates back toward the rack, demoted. Staged depth, warm quiet light.",
     [(H, "YOUR RESEARCH, DOCTOR VALE.", "balloon")])
beat("b75b-group-photo", "connective", "s5", [M, H, D, I], TANK5, ["margo", "investors", GYM], "winner:b74-finale",
     "CELEBRATORY BEAT: INGRID holds her phone high for a group shot — MARGO crouched LOW to fit the frame and still towering, one arm flexed, HARLAN and DEV flanking at staged depths, everyone grinning. Slight wide, warm window light, confetti of chalk dust.",
     [(I, "SAY 'GAINS'!", "balloon")])
beat("b76-hook", "connective", "s5", [M], TANK5, ["margo", GYM], "winner:b74-finale",
     "CLOSING BEAT: EXTREME CLOSE-UP of the amulet in MARGO's palm; above it, soft-focus, her knowing smile as the stone pulses ONCE, hard, green light flaring between her closing fingers.",
     [(None, "THE STONE ISN'T DONE. NOT EVEN CLOSE.", "caption"), (None, "thrmm.", "sfx")])


# ============================== EMIT ==============================

BUBBLE_SHAPE = {
    "balloon": "clean WHITE rounded oval speech balloon with a bold solid black outline",
    "thought": "cloud-shaped WHITE thought bubble with a bold black outline and a trail of small circles to the thinker",
    "whisper": "WHITE rounded oval speech balloon with a DASHED black outline",
    "shout":   "WHITE jagged-edged starburst speech balloon with a bold black outline",
}

def lettering_block(dialogue):
    """L19 scope-bounded lettering block — exact quoted text, per-line shape + tail."""
    if not dialogue:
        return ("NO TEXT in this panel: no speech bubbles, no captions, no SFX, "
                "no signage lettering of any kind.")
    lines = ["LETTERING — classic comic-book lettering composited onto the photoreal CGI "
             "scene; the 2D comic styling applies ONLY to these graphics, everything else "
             "stays photoreal 3D CGI:"]
    n = 0
    for d in dialogue:
        t, typ, spk = d["text"], d.get("type", "balloon"), d.get("speaker")
        if typ == "caption":
            lines.append(f'A yellow rounded-corner caption rectangle with a bold black outline at the bottom edge of the panel, bold black ALL-CAPS comic display font, reads exactly: "{t}"')
        elif typ == "sfx":
            lines.append(f'SFX lettering, bold flat comic display capitals with a solid black outline, integrated into the scene near the sound source, no 3D extrusion, reads exactly: "{t}"')
        else:
            n += 1
            shape = BUBBLE_SHAPE.get(typ, BUBBLE_SHAPE["balloon"])
            tail = (f", short triangular black-outlined tail pointing to {spk}'s mouth" if spk and typ != "thought"
                    else (f", dot-trail to {spk}" if spk else ""))
            lines.append(f'Bubble {n}: {shape}{tail}; bold black ALL-CAPS comic display font inside reads exactly: "{t}". Flat 2D vector graphic — no 3D shading, no bevel, never colored.')
    lines.append("Exactly these graphics and NO others — no extra bubbles, no duplicated or "
                 "garbled text, spelling exactly as quoted.")
    return " ".join(lines)


def main():
    beats_out = []
    for b in B:
        beats_out.append({
            "id": b["id"], "kind": "panel", "beatKind": b["beatKind"], "stage": b["stage"],
            "prompt": b["prompt"], "dialogue": b["dialogue"], "wardrobe": b["wardrobe"],
            "chars": b["chars"],
            "identityRefs": [{"label": r} for r in b["refs"]],
            "anchors": ([{"winner": b["anchor"].split(":", 1)[1]}] if b["anchor"] else []),
            "aspect": "3:4",
            "variants": 12 if b["beatKind"] == "payoff" else 8,
            "fullPrompt": b["prompt"] + "\n\n" + lettering_block(b["dialogue"]) + "\n\n" + STYLE_V5,
        })
    sheet = {
        "project": "margo-full",
        "backend": "higgsfield-mcp",
        "style": STYLE_V5,
        "styleVersion": "v5 (v4 + L19 lettering restored, no-text clause RETIRED — owner call 2026-08-12)",
        "beats": beats_out,
    }
    out = ROOT / "runners/bakeoff/margo-full-beats.json"
    out.write_text(json.dumps(sheet, indent=1))

    md = ["# MARGO — full comic script (margo-full)", "",
          f"{len(beats_out)} beats/pages, story order. Growth ladder s1→s5. "
          "Dialogue BAKED per L19; bubbles ≤ ~8 words.", ""]
    act = ""
    ACTS = {"b01": "## ACT 1 — THE BACK ROOM", "b11": "## ACT 2 — FIRST CHANGE (s1→s2)",
            "b23": "## ACT 3 — THE PITCH", "b33": "## ACT 3b — SECOND SURGE (s2→s3)",
            "b40": "## ACT 4 — FEATS OF STRENGTH", "b51": "## ACT 4b — THIRD SURGE (s3→s4)",
            "b66": "## ACT 5 — FINALE (s4→s5)"}
    for i, b in enumerate(beats_out, 1):
        key = b["id"].split("-")[0]
        if key in ACTS and ACTS[key] != act:
            act = ACTS[key]; md += [act, ""]
        md.append(f"### p{i:02d} · {b['id']} · {b['beatKind']} · {b['stage']} · {'/'.join(b['chars'])}")
        md.append(f"**Wardrobe:** {b['wardrobe']}")
        md.append(f"**Panel:** {b['prompt']}")
        for d in b["dialogue"]:
            who = d.get("speaker") or d.get("type", "").upper()
            md.append(f"> **{who}** ({d.get('type','balloon')}): {d['text']}")
        md.append("")
    (ROOT / "projects/margo-full/SCRIPT.md").write_text("\n".join(md))

    n_growth = sum(1 for b in beats_out if b["stage"] != "s1" or b["id"].startswith(("b10", "b11", "b12", "b13", "b14", "b15", "b16")))
    print(f"beats={len(beats_out)} payoff={sum(1 for b in beats_out if b['beatKind']=='payoff')} "
          f"round1_gens={sum(b['variants'] for b in beats_out)} growthish={n_growth}")
    print("wrote", out)

if __name__ == "__main__":
    main()
