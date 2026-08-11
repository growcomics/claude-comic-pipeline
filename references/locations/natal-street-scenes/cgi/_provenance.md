# natal-street-scenes / cgi — provenance

DAZ3D-Iray-style CGI conversions of the Natal street/coastal reference photos, generated 2026-06-12.

## Upgrade (2026-06-12, second pass)
The seven canonical plates were **re-rendered at higher fidelity** after the first low-poly batch read "too low res." Target dialed to **mid**: detailed / high-poly but still obviously a CG render (not photoreal, not low-poly). Calibration on the crosswalk found NB Pro overshot to near-photoreal; the working recipe is **Nano Banana 2** with a "detailed, clean synthetic CG, solid smooth modeled geometry, NOT low-poly, NOT photoreal" prompt, re-rendered from each original photo. The canonical filenames below now hold these mid-fi versions; the earlier low-poly `via-costeira-aerial-daz-v1-soft/-v2-mid` variants were removed. New Flow media ids: alecrim 81139d1a · coastline 7bbe5faa · food-truck c35fc931 · art-wall 3d0eb9d7 · erivan 09bd8fdb · via-costeira e6a9d02d · crosswalk 16474463.

## Method
Each source photo was uploaded into a Google Flow project (Omni / pill edit UI, **Nano Banana 2** model, 0-credit on the PRO account) and re-rendered in-place via the image-edit flow with a content-preserving DAZ-conversion prompt. The prompt locked composition / camera / layout / scale and changed only the medium to an **obvious low-to-mid fidelity 3D render** ("older DAZ Studio Iray hobbyist scene / early-2020s video-game environment; NOT photoreal, NOT hyperrealistic, NOT illustrated/anime/cartoon/2D"). Calibrated to the user's "push it more stylized" direction — the keepers read as faceted low-poly terrain, CG card trees, modeled buildings, plasticky materials.

- **Backend:** Google Flow (browser-driven via Chrome MCP), account "M" (PRO), project `6acf9ebe-d8a9-4384-9ca7-d1b1754e177a`.
- **Model:** Nano Banana 2.
- **Native output:** 1376×768 (16:9) or 1200×896 (4:3 street shots).
- **Download:** Flow `media.getMediaUrlRedirect` → signed `flow-content.google` URL → curl.

## Plates

| file | shot | source photo (location) | Flow media id |
|---|---|---|---|
| via-costeira-aerial-daz.jpg | wide aerial | Via Costeira coastal highway, dunes + hotels | bd1a6f64 (3-pass, most stylized — final) |
| via-costeira-aerial-daz-v2-mid.jpg | wide aerial | Via Costeira (mid-stylization variant) | 33fb9543 |
| via-costeira-aerial-daz-v1-soft.jpg | wide aerial | Via Costeira (soft/near-photo variant) | c3502719 |
| coastline-reefs-aerial-daz.jpg | wide aerial | coastline w/ reefs, umbrellas, Newton Navarro bridge | 912dab1d |
| erivan-franca-street-daz.jpg | tight street | Av. Erivan França, Ponta Negra (sidewalk level) | 44161df3 |
| ponta-negra-artwall-street-daz.jpg | tight street | Ponta Negra street, vendor art wall + police car + dune | 1a9c7392 |
| beachfront-foodtruck-avenue-daz.jpg | tight street | beachfront avenue, food-truck vans, high-rises | 9e6a161e |
| alecrim-commercial-street-daz.jpg | tight street | Alecrim commercial street, vendors + storefronts | 68456b8e |
| avenue-crosswalk-daz.jpg | tight street | tree-lined avenue, crosswalk, ÔNIBUS lane | cf61c779 |

Source photos are the Wikimedia Commons references in the parent folder (see `../_provenance.md`). The Via Costeira plate has three stylization passes banked; `via-costeira-aerial-daz.jpg` (no suffix) is the chosen final.

## QA
All nine visually inspected after download: valid JPEGs, correct composition preserved, clearly CGI (not photographic), matching the requested 2020-DAZ look. The two `-v1-soft` / `-v2-mid` Via Costeira files are retained as a stylization ladder, not as the canonical plate.
