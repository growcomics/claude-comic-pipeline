# commercial-gym / cgi — provenance

DAZ3D/CGI conversions of the real commercial-gym reference photos, generated 2026-06-27.

## Method
Each real photo (../commercial-gym-NN.jpg, sourced from Wikimedia Commons — see ../_provenance.md)
was uploaded to Higgsfield and re-rendered image-to-image with a content-preserving CGI-conversion
prompt: lock architecture / camera / layout / equipment placement + scale + lighting, change only the
medium to a photoreal 3D CGI / DAZ3D-Iray render, EMPTY the gym (remove all people), and strip every
brand name / logo / neon sign / readable text. Calibrated to the muller house style (photoreal CGI, not
low-poly — per feedback_comic_style_3d). These are the EMPTY environment plates that get attached to
muller's gym panels; the named character (Andrea) is inserted at generation time.

- Backend: Higgsfield MCP (direct), model nano_banana_pro (served as nano_banana_2), 1k, count=1.
- Pushed to the studio (project muller) as kind=scene refs via studio/tools/push-env-refs.sh.

## Plates
| file | shot | source photo | Higgsfield job id |
|---|---|---|---|
| commercial-gym-01-daz.png | weight floor (establish), 16:9 | commercial-gym-01.jpg (GymNation) | a237cabb-d0da-4aac-8545-f097d63d87db |
| commercial-gym-02-daz.png | resistance-machine floor, 4:3 | commercial-gym-02.jpg (The Gym Group) | e51d0731-7dc3-4d00-9d9d-260764214ab9 |
| commercial-gym-03-daz.png | cardio area (treadmills+elliptical), 4:3 | commercial-gym-03.jpg (Mandarin Oriental) | 77694618-1ae5-42eb-87ed-cde1e8c0d02e |

## QA
All three visually inspected: valid CGI renders, composition preserved, EMPTY (no people), no brand/text
artifacts, clearly rendered-3D (not photographic, not low-poly). Good env plates for the muller gym.
