# CAST CANON — "Scientists" (GrowGetter remake) (vision-shadow insert)

Sources: `references/CANON-NOTES.md` (cast lock + wardrobe locks) + `shotlist.json`.
Canonical reference images (attached to this audit):

1. **REFERENCE — cast lineup** at `references/characters/cast-lineup.png` (whole cast).
2. **Per-character identity sheets** at `references/characters/<id>/identity-sheet.png`
   for every character appearing in the batch's panels.

## Cast (locked looks)

- **rochelle** — dark-brown CHIN-LENGTH BOB, small stud earrings, soft/curvy baseline.
  States: baseline / grown / titan.
  Wardrobe: baseline = white lab coat, TEAL blouse, grey pencil skirt. grown =
  strained white tank top, open lab coat tight at shoulders, grey joggers. titan =
  white improvised wrap costume, edges torn, breasts and groin fully covered.
- **jill** — CARAMEL-BROWN LONG WAVY side-swept hair. States: baseline / grown / super.
  Wardrobe: baseline = white lab coat, BURGUNDY blouse, black slacks. grown =
  burgundy button-up straining at every button, bare midriff, black slacks. super =
  black athletic crop top, black training shorts.
- **jim** — SHORT TOUSLED BROWN hair, average build. Navy/white striped track jacket +
  jeans. States: baseline / grown.
- **donny** — SANDY-BLOND SHORT SPIKY hair. States: baseline / grown. (Distinct from
  jim: blond vs brown hair.)
- **dan** — BALD, gym-fit. States: baseline / grown.
- **assistant** — light-brown LONG WAVY hair, slim, timid. NEVER grows (always
  baseline — if she renders muscular, that's tier_visualization_mismatch).
- **blonde** — long straight BLONDE hair, one-off office woman (p25 area).
- **cheer-squad** — FIVE cheerleaders in red+white uniforms (ponytail enforcer-lead,
  space-buns, pigtails, curly, long-hair). **Five figures for the squad is the
  scripted count — do not flag the squad's five members as extras.**

## Identity-swap watch-outs

- jim ↔ donny confusion (brown tousled vs sandy-blond spiky).
- rochelle ↔ jill confusion (dark bob vs caramel long wavy; teal vs burgundy).

## Costume-state rule

Every panel's PANEL CONTEXT carries the scripted `costume_state` and per-character
`muscle_size_tier`. A character wearing a DIFFERENT state's wardrobe than scripted
(e.g. grown-state tank when baseline lab-coat is scripted) is costume_discontinuity.
A character rendered at visibly lower muscle mass than their scripted tier is
tier_visualization_mismatch (tier 0 = ungrown baseline; higher = grown/super/titan
states with visible beyond-bodybuilder mass; use the turnaround/identity sheets as
the anchor for what each state looks like).

## Coverage rule (always_clothed)

Garments may strain, stretch, or tear at seams, but coverage of breasts/buttocks/groin
is always preserved. A panel that breaks coverage is costume_discontinuity (note it
explicitly in the reason).

## Locations

Canonical sets: kitchen, lab (wide/med/close), city, field. The scripted location is
in PANEL CONTEXT; a clearly different venue class is location_mismatch.

## Lettering

These pages are FULLY LETTERED (flat yellow caption boxes, white oval bubbles with
black outline, 2D overlay on the photoreal render — the 2D lettering layer is legal).
Lettering IS expected: check every bubble and caption per category 8, and check
bubble tails per category 5.
