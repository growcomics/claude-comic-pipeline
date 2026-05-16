# Comic Test Log — running thread

**Started 2026-05-16** · A running thread of end-to-end comic tests on the checks-and-balances architecture. Each entry: a comic generated through the pipeline, the architecture's findings, my read on what worked / what didn't, then a separate section for the user's review notes so we can compare and calibrate. The diff between my findings and the user's is the calibration signal — the goal is to keep iterating until my read converges with theirs.

Companion to:
- [Design doc — Checks-and-Balances Rule Architecture](../checks-and-balances-design.md)
- [Original blog post — Checks and Balances](2026-05-16-checks-and-balances.md)

---

## Test 1 — 6-panel Chun Li FMG transformation (2026-05-16)

**Project:** `checks-balances-demo-2026-05-16/` · **Model:** `nano_banana_flash` · **Resolution:** 1k · **Cost:** 7 generation submissions (6 successful + 1 NSFW retry) ≈ 10.5 credits + ~$0.20 in vision-audit subagent tokens ≈ **under $5 total**.

### The panels

![6-panel grid](./assets/comic-test-log/test-01-6panel/grid.png)

Story: Chun Li in her training dojo at golden hour. An inner power surge triggers a transformation across 6 beats — setup, first sensation, chest growth ECU, bicep ECU, full-body stage change, hero reveal pose.

| # | Panel | Camera | Tier | Beat |
|---|---|---|---|---|
| p1-01 | ![](./assets/comic-test-log/test-01-6panel/p1-01.png) | medium | 1 | consider |
| p1-02 | ![](./assets/comic-test-log/test-01-6panel/p1-02.png) | mcu | 1 | first_sensation |
| p1-03 | ![](./assets/comic-test-log/test-01-6panel/p1-03.png) | ecu-region | 3 | chest |
| p1-04 | ![](./assets/comic-test-log/test-01-6panel/p1-04.png) | ecu-region | 4 | arms |
| p1-05 | ![](./assets/comic-test-log/test-01-6panel/p1-05.png) | 3q-full | 5 | whole_body |
| p1-06 | ![](./assets/comic-test-log/test-01-6panel/p1-06.png) | low-angle-front | 6 | reveal |

### Architecture's findings

**Pre-render (deterministic, free):** 6 `checks.json` ledgers written. 4 L1.5 view-aware-chaining fallbacks recorded as defects (mcu/3q-full/ecu-region transitions don't have compatible priors in the legacy compatibility table — informational, not actionable). Everything else clean.

**Post-render (phase 5 vision audits via subagent with per-rule `vision_rubric`):** 48 rubric checks across 6 panels. **45 pass, 3 fail.**

**The 3 fails — all L11 silhouette regression:**

| Panel | Tier | What the rubric saw |
|---|---|---|
| p1-03 | 3 (chest) | Silhouette regressed to fitness-model/glamour-bust framing — enlarged breasts in a halter-style top, NOT the broad-shouldered, defined-pec, visible-abs muscular tier 3. Garment reinterpreted as a bodice/swimsuit. |
| p1-05 | 5 (whole_body) | Shoulders read more like tier 4 than tier 5 — broad but not the 2.5x-shoulder massive-cartoony FMG of figure 5. Regression toward 'athletic strongwoman'. |
| p1-06 | 6 (reveal) | Shoulders read tier 4-to-5, not the 3x-shoulder peak-cartoony FMG of figure 6. Arms spread exaggerates apparent width but actual deltoid/lat mass falls short. |

This is the documented L11 failure mode — `nano_banana_flash` normalizes off-distribution silhouettes toward its realistic-fitness prior unless the prompt fights it harder. p1-04 (tier 4 bicep ECU) is the one high-tier panel that landed clean because an isolated bicep is harder to soften toward realism than a full-body shot.

**The 45 passes — what the architecture held cleanly:**

- **L17 canonical character** — every panel. Twin ox-horn buns + red ribbons + blue cheongsam with gold trim + white spiked wristbands + white tights + brown thigh-high boots present on **every panel including the ECUs**.
- **L21 ref-as-prop suppression** — every panel. Zero watermarks, zero inset face cards, zero figure-number overlays.
- **L24 anachronistic accessories** — every panel. Zero watches, rings, smartwatches, leather cuffs.
- **L22 hair state** — every panel with head visible. Canonical buns held.
- **L23 dense verbal env anchor on p1-06** — env_ref was dropped due to the 3-ref ceiling; the verbal anchor took over and **the dojo rendered cleanly** (wooden floor + paper lanterns + sliding doors) instead of collapsing to a grey void. **First successful field use of L23.**
- **L20 body-region framing** — p1-03 and p1-04 both filled 70%+ of the frame with the named region, head/feet cropped OUT. The "DOMINATES / cropped OUT" vocabulary works.
- **L18 anatomy coherence, L15 vogue face, L10 RENDER DIRECTIVE, female_anatomy** — all every panel.

### The NSFW filter event (L2 in real time)

p1-05 on first submission returned `status: nsfw` (no image). Retry with the same prompt passed cleanly — exactly per L2's retry policy: filter variance often clears on retry; reframe only after 4 failures.

### Defects summary

```
$ python3 skills/comic-production/scripts/discover_defects.py checks-balances-demo-2026-05-16/
```

| Rule | Count | Class |
|---|---|---|
| `L1.5` | 4 | architectural fallback (mcu/3q-full transitions) — informational |
| `L11` | 3 | silhouette regression at tiers 3/5/6 — **actionable** |

### Phase 6 retry recommendation (illustrative)

`retry_panel.py p1-03` returned `auto_resubmit_with_corrected_refs` (currently a bug — the CLI builds a thin ctx that doesn't reflect ref-attachment state; the lineup IS attached on p1-03). The *correct* retry for L11 with lineup-attached + tier ≥ 5 is `auto_resubmit_with_stronger_contribution` per the rule's logic: escalate silhouette vocabulary to "shoulders 3x normal width, biceps the size of the head, every muscle group hyper-defined." Logged as a phase 6 v0 fix.

### My read

The architecture worked as designed. Pre-render gates caught everything in the rule set. Post-render vision audit caught real, repeatable failure modes (L11 silhouette regression at high tier). The defects log gives us a structured target for the next iteration: the L11 module's `retry_strategy` ladder is the right shape; we need to actually fire it.

What's notable: **L17 + L21 + L22 + L24 + L23 + L20 all delivered consistently** across a small but real test. These are the rules where my biggest concerns were "does the prompt actually move the needle on the model" — and the test says yes. The hard rule is L11, and L11's failure isn't a prompt-engineering failure, it's a model-prior failure that needs either a stronger prompt or a different model for tier ≥ 5 work.

### User review (pending)

*Reserved for the user's review notes. Will add as a follow-up commit once feedback is in.*

### Alignment diff (pending)

*Once the user's review lands, I'll diff their findings vs mine and document where my read drifted from theirs — that's the calibration target for Test 2.*

---

## Test 2 — coming next

15-page FMG transformation comic. Same character (Chun Li, refs reused), expanded story arc with more body-region beats and more camera variety. Will publish here once generated and audited.

---

*Format note: each test entry has the same shape — generated panels, architecture findings, my read, user review (pending), alignment diff (pending). The thread grows as we run more tests; the diff between my read and the user's review is the calibration target for the next test's analysis.*
