# Real-photo environment references → the Comic Studio

**Problem.** Backgrounds generated fully by AI read as "too AI" — the gym's
background crowd all looks the same, geometry is invented fresh each panel, the
location has no real-world anchor. (Owner feedback on the muller pages: *"not a
great reference at all."*)

**Fix (the owner's workflow).** Scour the internet for **real photos** of the
location → restyle each to the project's **DAZ3D / CGI** look → use those plates as
the **environment reference attached to every panel** at that location → composite
the character INTO the real-derived environment. Real → DAZ → insert. Far more
realistic than a from-scratch AI background, and consistent panel-to-panel.

This doc is the end-to-end SOP. The new piece that makes it usable is the bridge
verb `ingest_ref` + `studio/tools/push-env-refs.sh`, which land the plates into a
studio project as `kind=scene` references so the existing studio machinery
(refs.php → shots.php → worker/Flow) carries them the rest of the way.

---

## The pipeline

```
 1. GATHER     reference-gathering skill  → references/locations/<slug>/<slug>-NN.jpg
    (real photos)                            + _provenance.md  (source URL, license, QA)

 2. CONVERT    restyle each plate to CGI  → references/locations/<slug>/cgi/<name>-daz.jpg
    (real → DAZ)                             (Flow Nano Banana 2 / Higgsfield image-edit,
                                              content-preserving DAZ-conversion prompt)

 3. PUSH       push-env-refs.sh           → studio project, kind=scene, approved (+locked)
    (→ studio)   (bridge do=ingest_ref)

 4. ATTACH     shots.php match_scene()    → the plate is listed to attach on every panel
    (every panel)                            whose `location` matches the ref's char/label

 5. INSERT     worker / Flow              → character composited INTO the CGI plate
    (the character)                          (env ref attached every panel — continuity holds)
```

Steps 1–2 already have a proven track record in this repo
(`references/locations/natal-street-scenes/` — 7 real Wikimedia plates →
`cgi/*-daz.jpg`). This doc adds steps 3–5 (into the studio).

---

## 1. Gather real photos (reference-gathering skill)

Run the **reference-gathering** skill for the location. It searches Google Images /
Wikimedia / YouTube, QA-verifies each frame, and writes
`references/locations/<slug>/<slug>-NN.jpg` plus a `_provenance.md` entry per image
(source URL, author, **license**, QA note).

Provenance/copyright: these are *references for derivative CGI work*, not assets to
republish. Prefer **CC0 / Wikimedia Commons / press-kit / official** sources. The
skill refuses to save anything it can't attribute. (See the skill's "Hard rules".)

> Example query set for a gym: `commercial gym interior weight floor`,
> `gym squat rack row wide`, `cardio machines gym window light`,
> `gym free-weight area mirror wall`. Pull 12–20, keep the 5–7 clearest.

## 2. Convert real → DAZ/CGI (the "scene-style" restyle)

Each real plate is restyled into your project's CGI look so it anchors the *render
style* (Iray lighting, scale, materials) while keeping the *real composition*. Two
proven backends:

- **Flow (free on Pro)** — upload the photo into a Flow project, **Nano Banana 2**,
  image-edit in place with a content-preserving DAZ-conversion prompt that locks
  composition/camera/scale and changes only the medium. (This is exactly how
  `natal-street-scenes/cgi/` was produced — see its `_provenance.md` for the recipe
  and the calibration notes.)
- **Higgsfield (MCP, paid)** — `generate_image` with the photo as a reference image
  and the same conversion instruction; `nano_banana_pro`, 1k, count=1.

Save each to `references/locations/<slug>/cgi/<name>-daz.jpg`, and log the
backend + model + source photo in `cgi/_provenance.md`.

The full conversion technique + prompt patterns live in
`skills/comic-production/references/environment-references.md` (the DAZ3D
scene-conversion guide), including **establish-then-chain (L10)**: after the first
accepted panel in a location, chain off *that* panel instead of the plate to stop
drift.

**One-step alternative.** If you'd rather skip the standalone convert step, you can
attach the *raw* photo as the env ref and let the panel prompt do restyle+insert in
one shot ("use the attached photo for the location; render it in CGI/DAZ style;
insert the character"). It's faster but gives less control over plate consistency —
prefer the convert-first path for hero locations.

## 3. Push the plates into the studio

`studio/tools/push-env-refs.sh` lands plates into a studio project as `kind=scene`
references through the bridge (`do=ingest_ref`). It needs the bridge key
(`~/Documents/.3dmc-studio-bridge-key` or `$STUDIO_BRIDGE_KEY`).

```bash
# Folder mode — push a whole gathered location (CGI plates → approved + locked):
studio/tools/push-env-refs.sh \
  --project muller \
  --location "Commercial gym" \
  --dir references/locations/commercial-gym/ \
  --lock

# add --include-source to ALSO push the raw photos as *pending* context refs
# (visible + provenance-tracked, but NOT attached to panels unless you approve them)

# Explicit-file mode — push specific plates:
studio/tools/push-env-refs.sh --project muller --location "Commercial gym" \
  --status approved --lock plate-weightfloor-daz.jpg plate-cardio-daz.jpg

# Preview without sending:
studio/tools/push-env-refs.sh --project muller --location "Commercial gym" \
  --dir references/locations/commercial-gym/ --dry-run
```

What lands:
- each plate → a gallery image tagged `isref` (so it stays OFF the live-panels
  board) + a `$c['refs']` entry `{kind:scene, char:"Commercial gym", label:<stem>,
  status, src:"gathered", role, prov}`.
- `--lock` (when the project is already locked) appends the plate to
  `refsLockedSet` so the worker picks it up immediately; otherwise just
  re-lock in refs.php.

> **`--location` is the match key.** `shots.php match_scene()` scores a panel's
> `location` text against each scene ref's `char + label`. Name the location with
> words that appear in your panels' locations ("commercial gym", "gym interior") so
> the plate auto-attaches. A plate with no word overlap still shows up in the
> guide's fallback list to pick manually.

## 4. Review + lock in the studio

Open `refs.php?p=<project>` → the plates appear under **Scenes & locations** with
their provenance. Approve the keepers, set/confirm `kind = scene`, and **Lock
references**. Locking freezes the approved set into `refsLockedSet` (what every page
builds from).

## 5. Attach on every panel + insert the character

Open `shots.php?p=<project>` (Production guide). For each panel, the matched scene
plate is shown under **attach these refs** next to the copy-ready Flow prompt. Attach
it on **every** panel set in that location (the env-ref-every-panel lesson — without
it Flow invents a new room each generation). The worker's `genspec` already returns
the locked scene files for the same reason.

The panel prompt then composites the character into the plate. Use the
environment-references.md language: *"the attached env reference IS this location —
same architecture, scale, lighting; render the character performing [beat]"*; and
after the first accepted panel, **chain off that panel** for the rest of the
location.

---

## Where each piece lives

| Piece | Path |
|---|---|
| Bridge verb | `studio/bridge.php` — `do=ingest_ref` (key-gated) |
| Pusher CLI | `studio/tools/push-env-refs.sh` |
| Gather skill | `skills/reference-gathering/SKILL.md` (locations section) |
| Convert guide | `skills/comic-production/references/environment-references.md` |
| Studio helper | `refs.php` — "🌍 Real-photo location refs" card (copy-ready gather brief) |
| Worked example | `references/locations/natal-street-scenes/` (real → `cgi/*-daz.jpg`) |

## `ingest_ref` contract (for a worker / script that isn't the CLI)

```
POST bridge.php
  key=<bridge key>           do=ingest_ref           p=<project id>
  file=<multipart image>     [orig=<filename>]
  kind=scene                 (default scene; face|body|view|prop also valid)
  char="<location>"          (match key — e.g. "Commercial gym")
  label="<plate/view>"       (e.g. "weight floor wide")
  status=approved|pending    (default pending; CLI sends approved for plates)
  role=cgi-plate|real-source (provenance tag)
  prov="<source URL / license / author / QA>"
  lock=1                     (only if status=approved AND project already locked)
→ {ok, file, refId, kind, status, refsTotal, lockedNow}
```
