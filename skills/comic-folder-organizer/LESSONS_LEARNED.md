# Comic Folder Organizer — Lessons Learned

A retrospective from the Bay Watch chapter 5 organize session (2026-05-21 → 2026-05-23). The chapter went from a 173-file mess of timestamped generations, descriptive Higgsfield/Flow filenames, fractional inserts, and three overlapping TF scenes to a clean 70-panel story-ordered sequence. Many of the corrections below were the user pushing back on shortcuts I took — they are encoded as rules in `SKILL.md` so the next session avoids the same mistakes.

## The process mistakes

### 1. I executed bulk trashes/renames without a preview composite

The user explicitly called this out: *"I don't like that you did all this without giving me a composite image to change, I'm afraid you might have trashed things that shouldn't have been trashed."* Even though `trash/` is recoverable, **the user wants the veto opportunity before a change lands, not after**. Every bulk operation needs a labeled review composite first.

### 2. I showed the drop list without showing the keepers

When proposing dupe cuts, the right format is `[keeper] [drop] [drop] [drop]` rows, not a flat list of trashed files. Without the keeper next to the drop, the user can't sanity-check the pruning logic — they don't know what they're losing the *alternative* of.

### 3. I confused the outfit lock

I treated the red one-piece in panel 011 as Lana's canonical outfit and built an entire 63-panel "drift" composite around the wrong assumption. The user's character sheet showed Lana = TEAL, Lacy = OLIVE — the red panel was the outlier. **Never infer the lock from a single in-context panel.** Always ask the user to point at the character sheet or confirm the canonical colors before auditing for drift.

### 4. I used Opus 4.7 to read 100+ images sequentially

The user said *"don't use a ton of tokens if you can read them with a lesser model than opus 4.7."* Visual scanning is exactly the kind of bulk task Sonnet handles well. Delegate to a Sonnet subagent for batch reads; reserve Opus for synthesis, planning, and the final composite/script work.

### 5. I treated the chapter as one flat sequence

It actually had four scene blocks: opening → Asian (Kay) TF → lesbian TF (redhead + ponytail brunette) → Ritchie TF → closing. New supplementary files weren't just "inserts at slot N" — they belonged to *scene blocks*. Once I asked the user *"is the Asian TF area 010–039?"* the placements became coherent. **Segment by scene block first, then place panels within their block.**

### 6. "Lesbians" did not mean Lana + Lacy

User vocabulary differed from cast naming. The "lesbians" referred to the redhead lifeguard + dark-ponytail brunette lifeguard pair, not Lana + Lacy. **Confirm scene/character nicknames upfront** — write them into a mental scene-cast dictionary at the start of the session.

### 7. I auto-paired visually-similar panels as dupes

Panel 019 looked like 015 to me; the user said it wasn't. **Visual similarity alone is not enough** — different beats can look 90% the same (especially in close-up sequences). Surface the suspected dupe as a question in a side-by-side composite, don't pre-trash it.

### 8. I lost the file-name-vs-content thread

Sonnet flip-flopped on which panel had the "KRA-KOOM" SFX (060 vs 062). My proposal twice swapped the anchor. **When sub-agent reads conflict with the user's mental model, defer to the user** — they wrote the script and know the canonical content per panel.

### 9. I didn't use file size as a thumbnail heuristic

The user's folder had double-stamped filenames like `Breasts_kissing_..._.jpeg_..._221459.jpeg` at 81–139KB — clearly downscaled thumbnails of earlier full-res generations. I flagged them as "borderline" instead of immediately treating them as trash candidates. **Sub-150KB jpegs with double-stamped filenames are almost always thumbnails. Default to trash, surface for confirmation only.**

### 10. I missed that repositioning is a first-class action

I framed dupe-handling as "keep or trash" — but some panels were neither. They were keepers in the *wrong slot* (e.g., 027 belonged at beach landing, not mid-Kay-TF; 069 belonged in Asian TF, not Ritchie). **REPOSITION must be in the action vocabulary alongside KEEP / TRASH / REFS.**

### 11. I didn't anticipate fractional manual insertions

Mid-session the user dragged files into Finder and named them `074.5.jpeg`, `009.4.jpeg` to insert between existing panels. The renumber script needs to **respect natural-sort order including decimals** — `009 < 009.4 < 009.5 < 010` — and collapse the result back to integers.

### 12. I named new supplementary files with their long Higgsfield names

The user couldn't easily reference them when discussing the proposal. *"first rename all those images so it's easier for me to type them in here"* — I should have renamed them to `n01`, `n02`, ... immediately on import, before any composite was built.

### 13. I didn't ask before guessing on ambiguous user directives

When the user said *"n10 is after 069"* and *"069 belongs in the solo asian TF area"*, the literal reading would put n10 (a Ritchie scene panel) inside Kay's TF. **Use `AskUserQuestion` to clarify before acting** when a directive is structurally ambiguous.

### 14. I built one huge "everything" composite instead of focused ones

The first review composite tried to show 63 trashed panels in a tall stack. The follow-up — *"Regenerate showing the ones that you kept adjacent to the ones that you deleted"* — was the right format. **One composite per question.** Trash review is a different doc from keepers-vs-drops, which is different from the final-sequence-approval composite.

### 15. I didn't surface a flags-resolution composite

By the end of the session there were 3 unresolved ambiguities (019/015, 060/062 KRA-KOOM, n03 placement). I tried to describe them in prose. The user said *"give me an image to resolve"* — and a side-by-side flags composite was exactly the right artifact. **When you list a flag, also offer to build a visual flag-resolution composite.**

## The shape of a good session

What worked, in retrospect, was a repeating four-step loop:

1. **Audit** — read panels (with a Sonnet subagent, in batch) and produce a structured action list (TRASH / REFS / DUPE-DROP / REPOSITION / NEW-INSERT).
2. **Compose** — build a labeled review composite that visually pairs each proposed change with its context (neighbor / keeper / candidates).
3. **Veto loop** — user calls out exceptions: trash this, keep that, move this to scene X, this is a ref not a story panel. Apply the explicit calls atomically. If anything is structurally ambiguous, ask with `AskUserQuestion`.
4. **Renumber when fully resolved** — only do the sequential rename once the structural decisions are locked. Use two-stage temp-prefix renaming to prevent collisions, and preserve user-imposed sort order (including fractional inserts).

Don't compress the loop. Trying to fast-path past the compose step is what produced the "you trashed things without showing me" pushback.
