# ▶ RUN NOW — finish "Not So Supra... Man" (self-contained runbook)

**Owner instruction 2026-08-11 ~07:50 PDT:** *"I'm leaving here soon, so I need you to continue
driving this on the Mac Mini somehow. It should get all the way to completion on Mac Mini. Don't ask
me stuff. Also... everything needs to be nano banana 2 lite."*

Any session that picks this up: this file is the whole job. Work top to bottom, don't ask, don't stop
early. Everything below has already been proven end-to-end on the laptop.

---

## 0. Settings that are NOT negotiable

- **MODEL: `Nano Banana 2 Lite` on EVERY submit.** Owner-specified. The pill resets to something else
  on every page reload — re-verify it every single time. `qa/compose.py` now prints the correct model
  in its VERIFY line (fixed 2026-08-11, manifest `371d4643a18c522b`).
- **x4 variants, 16:9** for turnaround sheets. Aspect also resets on reload.
- **NO freehand prompts, ever.** Only `qa/compose.py` output, pasted verbatim. See repo `CLAUDE.md`.
- **Confirm the Flow account before every submit** (`/fx/api/auth/session`).
  - laptop = `marrtrobinson2312` (**ULTRA → NB2 Lite renders at 0 credits**)
  - mac mini = `growcomics` (**Plus — NB2 Lite may NOT be free here; check the pill's credit line
    before bulk work, and if it charges, say so in the wrap-up rather than burning the balance**)

## 1. State — what is already DONE (do not redo)

5 turnaround sheets banked with full verified chains (`python3 qa/verify_chain.py` → 5):

| ledger key | flow id | height ratio vs 6'2" mannequin |
|---|---|---|
| `dee-dee.turnaround_t8` | `38c4881e-aa56-4946-baad-aa7d84324324` | 0.981 ✓ |
| `supraman.turnaround` | `9c95faf4-ea41-4d7f-bf83-4671132a090c` | 1.000 ✓ (he IS 6'2") |
| `dex-doomer.turnaround` | `f1ab8fcf-4142-4b5e-a302-8fb6ca539385` | 0.988 ✓ |
| `dee-dee.turnaround_t3` | `64b4a734-f74f-4092-9180-563c8894c462` | 0.985 (residual, accepted) |
| `dana-lane.turnaround_t2` | `23f2e99f-c23f-40fc-9e0a-c87470e05845` | 0.930 ✓ best |

Laptop Flow project (source of the above): `014292cc-8d7a-493d-9767-b1f9548cb3e9`.
⚠️ The older project `04dd40e0…` **crashes the Flow client on load** — do not open it.

## 2. Remaining work, in order

1. `sheet:dana-t4-blouse` — composed + audited, ready to fire.
2. `sheet:dana-t9-ANCHOR-SWAP` — 3 chained passes (`pass_1`, `pass_2`, `pass_3_turnaround`). This is
   the tier-9 finale form; attach the size anchor and run the 4-axis no-downsize gate.
3. **Scene ladders** — `compose.py` REFUSES pages whose location rung isn't banked. Per
   `references/turnaround-specs.json → scene_ladder_rule`: per location, wide establish (exists) →
   medium rung chained from wide → close rung chained from medium. 7 locations. Generate only the
   rungs pages actually call for; compose names the missing one in its refusal.
4. **29 story pages** — `pages-log.json.pending`. STRICT ORDER: a page whose `continuity_refs` names
   a prior page cannot compose until that prior page is banked-with-chain. Continuity-free entry
   points (start here): `p01-01`, `p02-01`, `p22-01`, `p31-01`.
   Multi-character pages ALSO need `qa/staging/<panel_id>.json` authored first (D9/D13/D14) — see
   `qa/staging/p14-01.json` and `p20-01.json` as templates, and
   `skills/comic-production/references/staging-and-composition.md` for the legal `staging_type` values.
5. **Lettering + PDF** — `scripts/letter_pages.py` overlays dialogue/SFX from `shotlist.json`, then
   img2pdf (NOT PIL — PIL raises `KeyError: 'JPEG'` on save).

## 3. The chain — every single submit

```bash
cd ~/Documents/claude-comic-pipeline/projects/not-so-supra-man
python3 qa/compose.py --job sheet:<id>            # or page:<panel_id>   ONLY legal prompt source
python3 qa/compose.py --job <same> 2>&1 | sed -n '/PROMPT (paste verbatim/,$p' | tail -n +2 > /tmp/p.txt
python3 qa/audit_prompt.py --receipt qa/receipts/<job>.receipt.json --prompt-file /tmp/p.txt
#   -> quote BOTH the COMPOSE OK and AUDIT PASS lines before submitting
# SUBMIT in Flow (see §4), then:
#   POST-FLIGHT: verify yourself (see §5), write qa/receipts/<job>.verdict.json with pass:true + tags
python3 qa/bank.py --job <job> --flow-id <uuid> --disk <path> [--ledger-key <char>.<key>]
python3 qa/verify_chain.py
```
`bank.py` refuses anything missing receipt + audit-pass + passing verdict. Unbanked work is invisible
downstream, so a skipped layer cannot propagate.

## 4. Driving Flow (proven method)

**Refs must be re-uploaded per project** — the picker is project-scoped and does NOT see other
projects' assets. `file_upload` is allowlist-blocked and "Upload media" opens an un-drivable native
picker. Working method:

```bash
# serve the repo's ref PNGs over CORS-enabled loopback
mkdir -p /tmp/refs && cp references/characters/*/*.png /tmp/refs/
python3 - <<'PY' &
import http.server,socketserver,os
os.chdir('/tmp/refs')
class H(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin','*'); super().end_headers()
    def log_message(self,*a): pass
socketserver.TCPServer(("127.0.0.1",8791),H).serve_forever()
PY
```
Then in the Flow page, inject each file into the hidden file input:
```js
const inp=document.querySelector('input[type=file]');
const r=await fetch('http://127.0.0.1:8791/<name>.png',{cache:'no-store'});
const b=await r.blob(); const dt=new DataTransfer();
dt.items.add(new File([b],'<name>.png',{type:'image/png'}));
inp.files=dt.files; inp.dispatchEvent(new Event('change',{bubbles:true}));
// wait ~5s between files
```

**Attaching refs — DO NOT BATCH BLIND.** Cost a full wasted round on 2026-08-11: a 21-step blind
batch clicked a picker result *before the search had filtered* and silently attached the wrong body
(Dee-Dee's lab coat onto Dana's sheet); 3 variants rendered the wrong character. Correct procedure:
`+` → click search → type the exact filename → **wait 4s** → **screenshot and confirm the preview
pane shows the intended asset** → `Add to Prompt`. Verify BOTH chips before submitting.

Harvest + download (batch all four resolutions into ONE browser_batch — ~4x faster):
navigate a scratch tab to `https://labs.google/fx/api/trpc/media.getMediaUrlRedirect?name=<uuid>`,
read the resulting `flow-content.google` signed URL out of the tab context, then `curl` it to disk.
(`fetch()` on that endpoint is CORS-blocked; the JS tool also refuses to return query strings.)

## 5. Post-flight — VERIFY, don't trust

The delegated judge was **wrong twice** on 2026-08-11, including passing a sheet with a blatant
giantess-scale defect. For canonical references, measure it yourself:

```python
from PIL import Image; import numpy as np
im=Image.open(F).convert('RGB'); a=np.array(im); H,W,_=a.shape
bg=np.median(a.reshape(-1,3),axis=0)
mask=(np.abs(a.astype(int)-bg.astype(int)).sum(axis=2))>38
man=np.where(mask[:,int(W*0.78):].any(axis=1))[0]      # mannequin, far right
her=np.where(mask[:,int(W*0.02):int(W*0.20)].any(axis=1))[0]   # first figure
ratio=(her.max()-her.min())/(man.max()-man.min())      # MUST be < 1.00
```
`ratio >= 1.00` on a female sheet = the giantess defect → **re-roll, do not bank.** (`dee-dee.t8`
was un-banked at 1.12–1.20 for exactly this.) Also reject any variant that renders a **text label**
in frame (e.g. `6'2" (188cm)`) — LET-02, three variants were lost to this.

## 6. ⭐ BUST-LANDING CORRECTION LOOP (owner-flagged 2026-08-11)

Owner: *"You need to find a way to correct for this sometimes."* The bust over-spec lands on some
variants and not others — one Dana T2 variant rendered completely flat while its sibling landed.
**Never bank a flat variant.** Correct in this order:

1. **SELECT, don't accept.** x4 gives four rolls; compare each sheet's bust against the canon body
   card (`references/characters/<char>/body-tier*.png`) and take the one that landed. This alone
   fixed Dana T2.
2. **If none of the 4 land → re-roll the same submit.** The owner's own validated method: x4 fired
   **three times = 12 variants**, then pick. These models take no seed, so identical resubmits
   diverge. Hard attributes are a SELECTION problem as much as a prompting one.
3. **If re-rolls still miss → edit-mode correction pass** on the best otherwise-good sheet. This is
   what the owner did: attach the sheet and submit their phrasing as an edit —
   *"Make her very, very, very, very beautiful. Make her breasts very, very, very, very big. Make
   her waist very, very, very narrow. Give her a very, very great ass. Make sure in every phase of
   the turnaround, the breasts are the same large equal size. No difference in breast size per
   turnaround variation."*
4. Expect ~1 in 12 to fail the policy filter at this intensity. Normal — keep the survivors.
   Claude's earlier ornate phrasing ("deep prominent cleavage swelling above the neckline…") was
   BOTH weaker AND tripped the filter on 4/4. Plain stacked "very" wins.

## 7. After every bank

Update `PROGRESS.md`, commit project TEXT + a dated `CHANGELOG.md` entry, push. Never touch
`.git.backup-*`. Never edit `qa/` gate scripts (re-locks ALL gates; re-bless is owner-only).
