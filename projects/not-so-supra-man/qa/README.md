# Predictive QA system — design + calibration protocol

Goal (user-defined): a QA layer that predicts defects as well as the user does,
tested against the user's own verdicts, feeding fixes automatically.

## Three layers

**1. Pre-flight (predict BEFORE spending a generation)**
Computed per panel from shotlist + defect registry. Submit is BLOCKED unless:
- required ref stack attached (face + wardrobe-state turnaround + env + prior accepted panel)
- the panel's costume_state has a canonical turnaround in references/
- camera fragment is prompt-LEADING; non-frontal camera ⇒ multi-angle ref attached
- expression block present when the panel has dialogue or a transformation beat
- tier pages: tier card attached (+ anchor at T9), size language over-specced one notch

**2. Post-flight (inspect BEFORE accepting)**
Fresh-context audit subagent scores every variant against the registry's detection
checks (angle-vs-camera, expression-vs-beat, outfit-vs-turnaround, size 4-axis,
identity, continuity, style, anatomy, baked text). Output: predicted tags in the
SAME vocabulary as the Red-Pen extension + severity + one-line reason per variant.
Auto-reject routes straight to the matching fix recipe.

**3. Calibration ("as good as the user") — the test loop**
1. Test set: all variants of ~6 representative pages.
2. QA agent tags them BLIND (before seeing user verdicts).
3. User tags the same set via the Red-Pen extension; export JSON.
4. Diff → per-tag agreement matrix (what the agent missed, what it over-flagged).
5. Refine rubric with the disagreements; user ★ goldens = positive exemplars,
   user-flagged fails + notes = negative exemplars.
6. Repeat until agreement target (≥85–90% on reject-level calls), then the QA
   agent gates ALL acceptance; periodic spot-diffs vs user keep it calibrated.

## Regeneration rule

`defect-registry.json` is the single source of truth. When it changes:
- the extension's TAGS array is regenerated from it
- the post-flight rubric is regenerated from its detection checks
- validated prevention gates graduate to the repo rule registry as L-lessons
  (cross-project, enforced by next_panel.py's walker)
