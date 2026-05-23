# Experiment 03 — Test Panel Selection

**Hypothesis under test:** Complex composite panels produce better results when generated in ingredient passes and then composited, vs. one-shotting them.

**Selection criterion:** Panels where the audit log (`projects/ultra-gal-origin/audits/pages-01-07-audit-2026-05-16.md`) flagged a defect that maps to the "this is too much for one prompt" failure mode — cast-count violations, foreground/background integration failures, multi-character identity confusion, object-character binding errors, or wide-establish collapse.

The repo gitignores `projects/*/pages/`, so per-panel retry counts aren't on disk. I'm using the QA audit as a proxy for "panels the one-shot approach struggled with" — it's a better signal than retry count anyway, because it records the failure mode and the audit was already deemed authoritative.

All five candidates are from `ultra-gal-origin` (the most recent, most QA'd project with the richest defect log).

---

## Panel 1 — `p05-02` (Both characters mid-growth, low-angle-back)

**Cast:** dr-mundy, heather
**Location:** mundy-lab-a
**Camera:** ecu-region, low-angle-back

**One-shot defect (from audit):** "Re-render to include BOTH characters mid-growth (currently only Mundy's back visible)." Tier-1 critical. The one-shot prompt dropped Heather entirely — a CAST-COUNT VIOLATION on a 2-character composite.

**Why this is a good multi-pass candidate:** This is the textbook "one-shot can't keep all the characters" failure. If multi-pass works anywhere, it should work here — generate each character separately at full quality, then composite into the BG.

**Audit-flagged failure category:** Cast-count violation, multi-character composite drop.

---

## Panel 2 — `p05-04` (Bicep ECU with mirroring BG arm)

**Cast:** dr-mundy, heather
**Location:** mundy-lab-a
**Camera:** ecu-region, low-angle-front

**One-shot defect:** "Re-render to include Heather's mirroring arm in BG." Tier-1 critical. Foreground bicep rendered fine; background arm was simply missing.

**Why this is a good multi-pass candidate:** This is a foreground/background integration problem. ECU on Mundy's flexing bicep is the hero element; the second character is reduced to a BG arm element. One-shot is fighting the framing — the model focuses on the ECU subject and forgets the BG mirror. Multi-pass lets us generate the bicep and the BG arm separately and force the composite.

**Audit-flagged failure category:** Foreground/background integration failure.

---

## Panel 3 — `p02-02` (Lenny + Mundy MCU, high-angle)

**Cast:** dr-mundy, lenny
**Location:** mundy-lab-a
**Camera:** mcu, high-angle

**One-shot defect:** "Re-render with correct cast (Lenny dark-haired, NOT Carl) AND fix duplicate 'REALLY? WHAT DO YOU DO?' bubble." Tier-1 critical. The one-shot swapped Lenny (dark-haired) for Carl (blonde) — IDENTITY CONFUSION between two background-similar male characters.

**Why this is a good multi-pass candidate:** Multi-character identity confusion is a one-shot-specific failure: the model interpolates between similar face-cards when both are in context. If we pin Lenny first as a standalone ingredient pass — locked dark-haired, blue overalls — and then composite him in next to Mundy, the model can't substitute him with Carl because Carl isn't in the composite-pass reference set.

**Audit-flagged failure category:** Multi-character identity drift (Lenny↔Carl swap).

---

## Panel 4 — `p03-03` (Heather tips bag, birds-eye)

**Cast:** dr-mundy, heather
**Location:** mundy-lab-a
**Camera:** mcu, birds-eye

**One-shot defect:** "Re-stage so HEATHER is holding/tipping the paper bag (not Mundy)." Tier-2 high-priority. Object-character binding got swapped — the bag ended up with the wrong character.

**Why this is a good multi-pass candidate:** Object-character binding errors happen when one-shot prompts ask the model to put a prop in a specific character's hand in a multi-character scene. The model picks one of the two and 50% of the time picks wrong. Multi-pass: render Heather-with-bag as ingredient 1 (no other characters in frame, prop binding unambiguous), then composite Mundy into the scene. Prop ends up where we want it because the ingredient pass already locked it.

**Audit-flagged failure category:** Object-character binding error.

---

## Panel 5 — `p01-01` (Wide establishing shot, lab + workout corner)

**Cast:** lenny, carl
**Location:** mundy-lab-a
**Camera:** cowboy, low-angle-back

**One-shot defect:** "Restage as TRUE wide-establish of the lab + workout corner. Currently medium 3-shot." Tier-3 camera variety. Plus "Solar-system poster rarely renders" (rendered only in 2/25 panels) and "Workout-corner setting elements persist only in p01-01 / p01-02".

**Why this is a good multi-pass candidate:** Wide-establish failures are a special case of "too much in one prompt" — the model can't simultaneously satisfy (a) wide framing, (b) 2 characters, (c) lab equipment, (d) solar-system poster, (e) workout corner. Something always gets dropped. Multi-pass: generate the lab environment as the "scene plate" first (wide, all environmental elements), then drop the characters in. This is the closest analogue to the user's discord description ("take the scene I have and prompt the same thing with the camera angle, and generate that image").

**Audit-flagged failure category:** Wide-establish collapse / environmental element drop.

---

## Coverage of failure-mode space

| Panel | Cast-count drop | FG/BG integration | Identity confusion | Object binding | Wide-establish collapse |
|---|---|---|---|---|---|
| p05-02 | ✓ | | | | |
| p05-04 | | ✓ | | | |
| p02-02 | | | ✓ | | |
| p03-03 | | | | ✓ | |
| p01-01 | | ✓ | | | ✓ |

Five panels, five distinct composite-failure categories (with p01-01 overlapping two). If multi-pass wins across categories, that's strong signal. If it only wins in some, the recommendation can be category-specific (which is more useful than "ship it everywhere" anyway).
