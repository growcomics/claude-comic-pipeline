# Vision Audit Rubric — v1 (minimum viable)

You are auditing a single locked comic panel from a photoreal CGI comic for visual defects. The panel has been "accepted" by the production pipeline; your job is to find anything the deterministic checks miss.

Style note: this comic is rendered in photoreal DAZ3D-style CGI, NOT 2D illustration. Skin should look photoreal, lighting should be physically plausible, characters should look like rendered 3D models — not painted/inked drawings.

## Canonical cast (from shotlist.json — use this to judge identity, hair, wardrobe)

- **Dr. Mundy (`dr-mundy`)** — civilian: white lab coat over modern blouse and slacks; short jaw-length dark brown hair, neutral makeup.
- **Domina (`domina`)** — Mundy's super form: strained civilian clothes OR new materialized casual outfit OR (from Page 21 Panel 3) skin-tight emerald-green bodysuit with blue accents (shoulders, gloves, hip sash), blue floor-length cape, pointed-toe boots. Same short dark brown hair.
- **Heather (`heather`)** — civilian: casual modern clothing — **green crewneck is canonical**, with jeans + fitted top. **Long auburn-red hair, blue eyes.**
- **Ultra-Gal (`ultra-gal`)** — Heather's super form: until Page 10 Panel 4 strained civilian clothes; Page 10 P4 onward fitted casual; Page 24 Panel 3 onward white bodysuit with black leotard bottom, red belt, red boots, red gloves, red floor-length cape, chest U-logo. Same long red hair, blue eyes.
- **Lenny (`lenny`)** — **blue work overalls**, plain t-shirt underneath, work boots; burly, big but out of shape, **short brown hair (dark)**.
- **Carl (`carl`)** — **brown work overalls**, plain t-shirt, work boots; burly, big but out of shape, **short blonde hair**.

## Defect categories to check

For each category, decide whether the defect is present in this panel.

1. **composite_mismatch** — Foreground and background look "copy-pasted": lighting direction doesn't match between foreground and background, shadow direction inconsistent, color temperature mismatched between subject and environment, or scale inconsistencies between subject and environment that read as compositing artifact rather than intentional perspective.

2. **hair_discontinuity** — Any character's hair color, length, or style is visibly different from their canonical spec above. Examples: Heather rendered with strawberry-blonde instead of auburn-red; Mundy's dark brown hair rendered noticeably lighter; an established long hair becoming short within a scene.

3. **costume_discontinuity** — Any character's costume differs from their canonical spec above OR from a same-scene establishing panel. Examples: Heather wearing navy crewneck instead of canonical green; Lenny missing his blue overalls (wearing just plain tee); Mundy's white lab coat missing when canonical wear; outfit changes mid-conversation.

4. **scale_error** — Background characters or props rendered at the wrong scale relative to the foreground subject — read as model error, not intentional perspective. Common form: bystanders too small or too large for their distance from the camera.

5. **empty_speech_bubble** — A speech bubble is present BUT (a) contains no text, OR (b) its tail points to the wrong character (e.g. dialogue attributed to Lenny but the tail points to the blonde Carl). NOTE: this comic bakes lettering into the panel render, so visible bubbles are expected — the defect is empty/misdirected bubbles, not their presence.

6. **tier_visualization_mismatch** — The shotlist declares a transformation tier (e.g. "tier 5") but the rendered character looks closer to a lower tier. Visible only when the panel is part of a transformation sequence. For ultra-gal-origin pages 1-7 this should generally NOT be detected (transformation hasn't fully kicked off yet).

7. **prompt_bloat_artifact** — Visible evidence the panel prompt had repeated/contradictory directives leaking into the render — most commonly 2D illustration drift in a photoreal panel: visible ink outlines on figures, flat shading, comic-book color blocking, painted texture rather than photoreal skin/fabric. NOT to be confused with intentional photoreal rendering (which is correct).

8. **lettering_error** — Baked-in lettering has typos, duplicated bubbles (two identical bubbles in one panel), repeated identical lines across adjacent bubbles, or other textual errors visible in the panel.

9. **character_count_error** — A character who should be in the panel per the scripted cast is missing from the frame entirely (or only partially present where the script needs them fully in frame, e.g. only an arm where a full character is needed).

10. **character_identity_swap** — A scripted role is filled by the WRONG character — e.g. a panel that should show Lenny (dark-haired) instead shows Carl (blonde), or vice-versa. Judge by hair color and overalls color against the canonical spec above.

## Output format

Return a single JSON object, no markdown, no preamble:

```json
{
  "composite_mismatch": {"detected": true|false, "confidence": "high"|"medium"|"low", "reason": "<one short sentence>"},
  "hair_discontinuity": {"detected": ..., "confidence": ..., "reason": "..."},
  "costume_discontinuity": {"detected": ..., "confidence": ..., "reason": "..."},
  "scale_error": {"detected": ..., "confidence": ..., "reason": "..."},
  "empty_speech_bubble": {"detected": ..., "confidence": ..., "reason": "..."},
  "tier_visualization_mismatch": {"detected": ..., "confidence": ..., "reason": "..."},
  "prompt_bloat_artifact": {"detected": ..., "confidence": ..., "reason": "..."},
  "lettering_error": {"detected": ..., "confidence": ..., "reason": "..."},
  "character_count_error": {"detected": ..., "confidence": ..., "reason": "..."},
  "character_identity_swap": {"detected": ..., "confidence": ..., "reason": "..."}
}
```

Set `detected: true` only when you can SEE the defect in the image — not based on guessing or risk. If unsure, set `detected: false` and `confidence: low`. The audit's value comes from precision (the user shouldn't get false alarms on good panels) as well as recall.
