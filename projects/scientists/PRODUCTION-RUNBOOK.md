# Scientists remake — production runbook (pages 5-16 completion run)

## Fixed parameters
- Model: nano_banana_2_lite, 1k, count=1, medias role "image_references". ~30s renders.
- Every panel: compose -> audit -> runner subagent submits work/final-<id>.txt VERBATIM -> judge subagent transcribes lettering + verdicts -> qa/bank.py.
- Continuity: every panel of page N has continuity_refs = [final banked panel of page N-1] so whole pages compose in one pass.

## Media id map (Higgsfield)
- rochelle identity 216f4259-3f9b-44ba-a2c2-b26df3b63da1 | grown 60fd435a-a14c-4d12-b165-362301a1555e | titan 1a7ba4ae-e293-4e04-9025-0095c86fc27a
- jill identity 88a992ca-8322-4b8c-a8f0-92e572788135 | grown db62c7f5-a01c-43d2-bc6e-a914a131dd77 | super f1e7caa4-ddbc-4199-8f2e-cf5448ef4614
- jim identity c26afa1a-61b1-4aa4-81a8-023974626da2 | grown cf1e5e9a-15db-4098-823a-91436f9c1e39
- donny identity 0a330eaf-e9fc-44bb-b81c-aa995be56d56 | grown 6557f4a9-d7d2-4851-b3bd-dc1ad1307ec8
- dan identity 74cf20ed-77f8-406f-bece-f89c1b19158a | grown 5eff6e96-7f16-4182-9b2f-12f3755c874e
- cheer-squad identity fe3c5d09-cac8-431b-9359-186596951657 | grown 282abe0e-2c59-4eca-9e84-a0f7b9c023f9
- env kitchen wide c0721aa4-497e-4169-b48e-f0cf0b7caf90 | kitchen med (upload) a9851461-129c-4b0f-8d53-51085006853e | kitchen close a0c53efa-cf4f-42b4-aaed-bee6309f27c9
- env lab wide 42167676-4b08-43fd-be8d-55b2f1187a41 | lab med 6b05421f-665a-4e9b-8681-f5aad1c88c83 | lab close 0de61697-275a-41b6-b288-2b53c6ba132e
- env field wide b1709a91-3bf9-4e38-baf7-4081cb4f72db | city wide 4ba2c16e-5caf-4e83-9e31-31d2435230f6
- anchor for tier>=9 panels ("anchor:lana" attach) -> use rochelle titan turnaround 1a7ba4ae
- last banked panels: p04-06 d3c515e3-7e25-40c5-aac2-f4e89babb68e

## Remaining page plan (each page = one wave pair with its neighbor)
- p05 lab: dosing confrontation; Jill deliberately doses herself (5)
- p06 lab: JILL growth 6-beat -> jill grown; "I GREW MORE THAN YOU." rivalry beat (6)
- p07 kitchen: Rochelle home huge; Jim thrilled; gives him tablet (5)
- p08 kitchen: JIM growth; Rochelle cold; walks out on him (5)
- p09 lab night: mind-control formula done; assistant discovers, threatened, flees (5)
- p10 living-room: Dan lured, dosed, grows, obeys (6)
- p11 living-room: Donny bursts in, dosed, grows, both enslaved (6)
- p12 field: squad dosed via cooler; group growth (6)
- p13 field: enforcer wrecks equipment; Jill arrives, confronts Rochelle (5)
- p14 field: Jill drinks improved formula -> SUPER growth (jill super target) (6)
- p15 field->city: Rochelle ultimate formula -> TITAN growth (tier 9-10; attach titan) (6)
- p16 city-ruins: splash finale + coda caption (2)

## Known failure modes to watch (judges must transcribe lettering)
- identity hijack from prior-panel ref (fix: staging identity lock naming the attached identity card)
- wardrobe: maroon-cuff bleed onto Rochelle; sleeves vanish on mid-growth (fix: staging wardrobe lock line)
- SFX typos (BOM/BOOM); garbled glyphs; dropped words = FAIL
- coverage: strain OK, opacity = coverage (house canon; do not fail contour show-through)

## Source-illustration refs (owner instruction 2026-07-30, mid-run)
EVERY panel submit now ALSO attaches the matching ORIGINAL lineart crop/page (references/harvest/, media ids in references/harvest/media-ids.json) as a pose/composition/count anchor, in addition to the CGI sheets + scene rung + prior panel. Use -cov variants where they exist. Log the addition in the verdict notes. Mapping for remaining pages: p13 squad beats -> cheer-lineup-p36 (cb65163e) / cheer-ponytail-p37-cov (3cc427fa); p14 Jill super growth -> jill-super-p40-cov (dcef6c21), standoff -> rochelle-arms-p39 (c3d43492); p15 titan growth -> rochelle-titan-p42 (ab5e29d9) + env-city-p43 (c27bc1bd); p16 splash -> rochelle-titan-p44 (5ebae816).
