# Flow accounts — dual-account access + the confirm-before-acting rule

The comic work runs across **two Google Flow accounts**. This file documents how
to use both at once and — critically — how to **confirm which account a tab is
on before doing anything**, so actions never land on the wrong account.

> Investigated and written 2026-06-14. The `marrtrobinson` facts were confirmed
> live that day; the `growcomics` facts are from memory `feedback_flow_omni_ui`
> and should be re-confirmed the next time the mac mini browser is connected.

## The two accounts

| Account | Purpose | Browser / profile | Plan (Flow) | Confirmed |
| --- | --- | --- | --- | --- |
| **growcomics@gmail.com** | Primary comic production ("g" account) | **mac mini** Chrome | Plus | from memory — re-confirm |
| **marrtrobinson2312@gmail.com** | Secondary / overflow account | **laptop** Chrome (deviceId `6b35bfe8-66a7-44c7-8ca2-191cf22b7b87`) | PRO (`PAYGATE_TIER_ONE` / `G1_TIER1`), 1844 credits on 2026-06-14 | live 2026-06-14 |

### Default login per machine (RULE)

Each machine has a **standing default account** — these are the default logins:

- **Laptop** → **marrtrobinson2312** (deviceId `6b35bfe8-66a7-44c7-8ca2-191cf22b7b87`)
- **Mac mini** → **growcomics**

So: **when driving the laptop, default to marrtrobinson; when driving the mac mini,
default to growcomics.** When you `select_browser` a machine, expect its default
account — and still run the confirm-account check below. If the active account does
NOT match the machine's default, stop (the wrong profile is loaded) and switch back
before acting.

Model rule is unchanged on both: **Nano Banana Pro** for comic gens
(`feedback_flow_nano_banana_pro`). Flow model keys seen in payloads:
`NARWHAL` = "Nano Banana 2", `GEM_PIX_2` = "Nano Banana Pro".

## Access — one account per browser profile (NOT a URL switcher)

Flow does **not** honor Google's `/u/N/` account-switcher path
(`labs.google/fx/u/1/tools/flow` → **404**, verified 2026-06-14). A Flow tab is
whichever Google account its browser **profile** is signed into. So:

- **Both accounts at once** = two browser profiles, one account each. The
  existing setup already is this: the **mac mini** browser holds growcomics and
  the **laptop** browser holds marrtrobinson. To run both on a single machine,
  create two named Chrome profiles (e.g. "Flow-Main" = growcomics, "Flow-Alt" =
  marrtrobinson) and sign each into one account.
- **Targeting from Claude (Chrome MCP):** `list_connected_browsers` enumerates
  the profiles by `deviceId`; `select_browser <deviceId>` picks one. Map:
  - `6b35bfe8-66a7-44c7-8ca2-191cf22b7b87` (name "laptop") → **marrtrobinson2312**
  - mac mini deviceId → **growcomics** (record it the next time it connects)

Do **not** store passwords here or anywhere. Login is the user's action.

## ⚠️ MANDATORY: confirm the account before any Flow action

Before any submit, edit, ref upload, delete, or download in a Flow tab, confirm
the active account matches the account you intend to work in. Two ways:

1. **If the Flow Review Harvester extension is loaded (preferred):** it stamps
   the live account onto the document. One read settles it:
   ```js
   document.documentElement.dataset.flowAccount   // -> "marrtrobinson2312@gmail.com"
   ```
   (Also shown at the top of the harvester panel.)

2. **Without the extension:** scan the page's server-rendered data for the
   signed-in gmail (works via the Chrome MCP `javascript_tool`; the
   `/api/auth/session` route is redacted by the MCP, so use this):
   ```js
   [...new Set([...document.querySelectorAll('script')]
     .flatMap(s => (s.textContent||'').match(/[a-z0-9._%+-]+@gmail\.com/gi) || []))]
   ```

If the active account is **not** the one the task targets, switch browsers
(`select_browser`) or have the user switch the Chrome profile — then re-check.
Never assume; a wrong-account submit burns the wrong credits and pollutes the
wrong project.

## Harvesting a project for review

Use the **Flow Review Harvester** extension
(`~/Documents/flow-review-harvester/`) to export a project's generations as a
structured bundle Claude can review in one pass — per generation: the output
image(s), the exact prompt, the attached input reference images, and metadata
(model, timestamp, **account**, project). See that repo's `README.md` for the
manifest format. The bundle's `account` field disambiguates which of the two
accounts each generation came from.

### Review-pass doctrine

A harvested bundle plugs into the existing QA doctrine. Hand a fresh subagent the
`manifest.json` + the referenced images and the **canonical** rubric — read and
pass `skills/continuity-check/qa-checklist.md` + `cinematic-framing.md` verbatim
(never paraphrase; per `feedback_audit_use_canonical_rubric` and
`feedback_dont_paraphrase_canonical_rubrics`). The subagent audits
prompt-vs-output-vs-refs across the whole batch without driving the Flow UI.
