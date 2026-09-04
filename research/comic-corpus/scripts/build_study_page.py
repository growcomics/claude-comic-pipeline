#!/usr/bin/env python3
"""Build synthesis/deed-arts-staging-study.html from its sources. Never hand-edit the HTML.

    cd research/comic-corpus && python3 scripts/build_study_page.py

Sources (all read-only):
  synthesis/deed-arts-staging-study.md      the write-up: summary, camera table, eight moves, seen, 2D->3D
  synthesis/cards.json                      the 76-card angle deck (built by scripts/angle_deck.py)
  skills/comic-production/references/lessons-learned.md       the L40 lesson
  skills/comic-production/references/cinematic-framing.md     the "Body-to-camera staging — L40" section
  corpus/deed-arts-*/{meta,beats,angle-study}.json + notes.md the two book studies
  skills/comic-production/references/sketches/angle-card-examples/ledger.json
                                            real renders per card (optional; cards without an entry render as before)

The output deliberately has no <!doctype>/<html>/<head>/<body> wrapper: it is written to be published as-is
through the Artifact tool, which adds that skeleton, and browsers render the bare file fine from disk (the leading
<meta charset> keeps the middle-dot separators intact when the file is opened or served without the wrapper).
Example images are linked by relative path into skills/…/angle-card-examples/, so keep the page inside the repo.
"""
import html
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]           # research/comic-corpus
REPO = ROOT.parents[1]                               # repo root
SYN = ROOT / "synthesis"
REFS = REPO / "skills/comic-production/references"
EXAMPLES = REFS / "sketches/angle-card-examples"
OUT = SYN / "deed-arts-staging-study.html"
EX_REL = "../../../skills/comic-production/references/sketches/angle-card-examples"
BOOKS = ["deed-arts-poppy-sailor-gal-1", "deed-arts-omega-device"]
SHORT = {"deed-arts-omega-device": "Omega", "deed-arts-poppy-sailor-gal-1": "Poppy"}
GROUP_LABEL = {"worm": "Worm's-eye", "low": "Low angle", "eye": "Eye level", "high": "High angle",
               "dutch": "Dutch", "OTS": "Over-shoulder"}
MODEL_LABEL = "nano_banana_2"


# ---------------------------------------------------------------- markdown (the small subset these files use)
def esc(s):
    return html.escape(s, quote=False)


def attr(s):
    return html.escape(s, quote=True)


def inline(s):
    codes = []

    def stash(m):
        codes.append("<code>" + esc(m.group(1)) + "</code>")
        return f"\x00{len(codes) - 1}\x00"

    t = re.sub(r"`([^`]+)`", stash, s)
    t = esc(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![\w*])\*(?!\s)([^*]+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", t)
    t = re.sub(r"(?<!\w)_(?!\s)([^_]+?)(?<!\s)_(?!\w)", r"<em>\1</em>", t)
    t = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', t)
    return re.sub(r"\x00(\d+)\x00", lambda m: codes[int(m.group(1))], t)


_ids = set()


def heading_id(prefix, text):
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60] or "h"
    hid = f"{prefix}-{slug}"
    n = 1
    while hid in _ids:
        n += 1
        hid = f"{prefix}-{slug}-{n}"
    _ids.add(hid)
    return hid


LI = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$")


def list_html(block):
    items = []
    for ln in block:
        m = LI.match(ln)
        if m:
            items.append([len(m.group(1).expandtabs(4)), m.group(2)[0].isdigit(), m.group(3)])
        elif ln.strip() and items:
            items[-1][2] += " " + ln.strip()

    def build(pos, ind):
        tag = "ol" if items[pos][1] else "ul"
        h = [f"<{tag}>"]
        while pos < len(items) and items[pos][0] == ind:
            text = items[pos][2]
            pos += 1
            sub = ""
            if pos < len(items) and items[pos][0] > ind:
                sub, pos = build(pos, items[pos][0])
            h.append(f"<li>{inline(text)}{sub}</li>")
        h.append(f"</{tag}>")
        return "".join(h), pos

    parts, pos = [], 0
    while pos < len(items):
        s, pos = build(pos, items[pos][0])
        parts.append(s)
    return "".join(parts)


def table_html(rows):
    def cells(r):
        r = r.strip()
        r = r[1:] if r.startswith("|") else r
        r = r[:-1] if r.endswith("|") else r
        return [c.strip() for c in r.split("|")]

    head = cells(rows[0])
    body = [cells(r) for r in rows[1:] if not re.match(r"^\|?\s*:?-{2,}", r)]
    h = '<div class="tablewrap"><table><thead><tr>' + "".join(f"<th>{inline(c)}</th>" for c in head) + "</tr></thead><tbody>"
    for b in body:
        h += "<tr>" + "".join(f"<td>{inline(c)}</td>" for c in b) + "</tr>"
    return h + "</tbody></table></div>"


def md_to_html(md, idprefix, shift=0, drop_rules=False):
    lines = md.split("\n")
    out, para, i, n = [], [], 0, len(lines)

    def flush():
        if para:
            out.append("<p>" + inline(" ".join(x.strip() for x in para)) + "</p>")
            para.clear()

    while i < n:
        line = lines[i]
        s = line.strip()
        if not s:
            flush()
            i += 1
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", s)
        if m:
            flush()
            level = min(len(m.group(1)) + shift, 6)
            text = m.group(2).strip()
            out.append(f'<h{level} id="{heading_id(idprefix, text)}">{inline(text)}</h{level}>')
            i += 1
            continue
        if re.match(r"^(-{3,}|\*{3,}|_{3,})$", s):
            flush()
            if not drop_rules:
                out.append("<hr>")
            i += 1
            continue
        if s.startswith("|"):
            flush()
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append(lines[i])
                i += 1
            out.append(table_html(rows))
            continue
        if s.startswith(">"):
            flush()
            q = []
            while i < n and lines[i].strip().startswith(">"):
                q.append(re.sub(r"^>\s?", "", lines[i].strip()))
                i += 1
            out.append("<blockquote>" + md_to_html("\n".join(q), idprefix, shift, drop_rules) + "</blockquote>")
            continue
        if LI.match(line):
            flush()
            block = []
            while i < n:
                cur = lines[i]
                if LI.match(cur) or (cur.strip() and cur[:1] in " \t"):
                    block.append(cur)
                    i += 1
                elif not cur.strip():
                    j = i + 1
                    while j < n and not lines[j].strip():
                        j += 1
                    if j < n and (LI.match(lines[j]) and lines[j][:1] in " \t" or (lines[j][:1] in " \t" and lines[j].strip())):
                        i = j
                    else:
                        break
                else:
                    break
            out.append(list_html(block))
            continue
        para.append(line)
        i += 1
    flush()
    return "\n".join(out)


def md_sections(md):
    """Split on '## ' headings -> (intro_text, {title: body})."""
    intro, sections, title, buf = [], {}, None, []
    for line in md.split("\n"):
        if line.startswith("# ") and title is None and not intro:
            continue
        if line.startswith("## "):
            if title is None:
                intro = buf
            else:
                sections[title] = buf
            title, buf = line[3:].strip(), []
            continue
        buf.append(line)
    if title is None:
        intro = buf
    else:
        sections[title] = buf
    return "\n".join(intro), {k: "\n".join(v) for k, v in sections.items()}


def section_starting(sections, prefix):
    for k, v in sections.items():
        if k.startswith(prefix):
            return v
    sys.exit(f"missing section starting with {prefix!r} in the study markdown")


def slice_h2(md, heading_start):
    """Return the '## <heading_start>…' section of a markdown file up to the next '## '."""
    lines = md.split("\n")
    start = next((i for i, l in enumerate(lines) if l.startswith("## " + heading_start)), None)
    if start is None:
        sys.exit(f"missing '## {heading_start}' section")
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    return lines[start][3:].strip(), "\n".join(lines[start + 1:end])


# ---------------------------------------------------------------- sources
study_md = (SYN / "deed-arts-staging-study.md").read_text()
deck = json.loads((SYN / "cards.json").read_text())
lessons_md = (REFS / "lessons-learned.md").read_text()
framing_md = (REFS / "cinematic-framing.md").read_text()
ledger = json.loads((EXAMPLES / "ledger.json").read_text()) if (EXAMPLES / "ledger.json").exists() else None

intro_md, sections = md_sections(study_md)
cards = deck["cards"]
groups = deck["groups"]

results = {}
if ledger:
    for c in ledger.get("cards", []):
        if c.get("result"):
            results[c["card_id"]] = dict(c["result"], family=c.get("family", ""), expect=c.get("expect", {}))

books = []
for slug in BOOKS:
    d = ROOT / "corpus" / slug
    meta = json.loads((d / "meta.json").read_text())
    beats = json.loads((d / "beats.json").read_text())
    angle = json.loads((d / "angle-study.json").read_text())
    notes = (d / "notes.md").read_text()
    books.append((slug, meta, beats, angle, notes))

pages_read = sum(len(b[2]["pages"]) for b in books)
panels_tagged = sum(len(p.get("panels", [])) for b in books for p in b[2]["pages"])


# ---------------------------------------------------------------- pieces
def card_html(c):
    t = c["tags"]
    src = c["source"]
    label = f'{SHORT.get(src["comic"], src["comic"])} P{src["page"]}.{src["panel"]}'
    score = c["steal_score"]
    dots = "".join('<i class="on"></i>' if k < score else "<i></i>" for k in range(5))
    text = esc(c["text"])
    r = results.get(c["id"])
    cls = "card"
    body = f'<p class="seed">{text}</p>'
    if r and r.get("status") == "pass" and r.get("winner_file"):
        cls += " has-ex"
        cap = f'Real render · {MODEL_LABEL} · landed {r["landed"]} of {r["of"]}'
        body = (f'<div class="body">{body}<figure class="ex"><a href="{EX_REL}/{attr(r["winner_file"])}">'
                f'<img src="{EX_REL}/{attr(r["winner_file"])}" loading="lazy" alt="{attr(r["family"])} — real render of this card"></a>'
                f'<figcaption>{esc(cap)}</figcaption></figure></div>')
    elif r:
        body += (f'<p class="nolanding">Did not land on {MODEL_LABEL}: {r["landed"]} of {r["of"]} variants held camera height, '
                 f'nearest part, and crop together. Kept in the deck.</p>')
    return (f'<article class="{cls}" data-group="{attr(c["group"])}" data-muscle="{attr(t["muscle_sold"])}" data-score="{score}">'
            f'<header><span class="slate">{esc(label)}</span><span class="score" aria-label="steal score {score} of 5">{dots}</span></header>'
            f'{body}'
            f'<footer><span>{esc(t["shot_distance"])} · {esc(t["angle"])} · {esc(t["camera_height"])} cam</span>'
            f'<span>at lens: {esc(t["toward_camera"])}</span><span>sells: {esc(t["muscle_sold"])}</span><span>crop: {esc(t["crop"])}</span>'
            f'<button type="button" class="copy" data-copy="{attr(c["text"])}">Copy</button></footer></article>')


def chips(kind, pairs):
    return "".join(f'<button type="button" class="chip" data-filter="{kind}" data-value="{attr(v)}">{esc(lbl)} <b>{n}</b></button>'
                   for v, lbl, n in pairs)


group_counts = Counter(c["group"] for c in cards)
muscle_counts = Counter(c["tags"]["muscle_sold"] for c in cards)
angle_chips = chips("group", [(g["id"], GROUP_LABEL.get(g["id"], g["title"]), group_counts[g["id"]]) for g in groups if group_counts[g["id"]]])
muscle_chips = chips("muscle", [(m, m, n) for m, n in sorted(muscle_counts.items())])

# study sections
summary_html = md_to_html(section_starting(sections, "The one-paragraph"), "summary", drop_rules=True)
camera_html = md_to_html(section_starting(sections, "Where the camera"), "camera", drop_rules=True)
moves_html = md_to_html(section_starting(sections, "The eight moves"), "moves", drop_rules=True)
seen_html = md_to_html(section_starting(sections, "Things the subagents"), "seen", drop_rules=True)
translate_html = md_to_html(section_starting(sections, "What does NOT translate"), "translate", drop_rules=True)
intro_html = md_to_html(intro_md, "intro", drop_rules=True)

# L40 (lesson + framing guide)
l40_title, l40_body = slice_h2(lessons_md, "L40")
l40_html = f'<h2 id="{heading_id("l40", l40_title)}">{inline(l40_title)}</h2>\n' + md_to_html(l40_body, "l40", drop_rules=True)
fr_title, fr_body = slice_h2(framing_md, "Body-to-camera staging")
framing_html = f'<h3 id="{heading_id("framing", fr_title)}">{inline(fr_title)}</h3>\n' + md_to_html(fr_body, "framing", shift=1)


def cite(x):
    return f'p{x["page"]}.{x["n"]}' if isinstance(x, dict) else str(x)


def book_html(slug, meta, beats, angle, notes):
    title = re.sub(r"\s*\(.*\)\s*$", "", meta["title"])
    sc = beats["scores"]
    npages = len(beats["pages"])
    npanels = sum(len(p.get("panels", [])) for p in beats["pages"])
    moves = "".join(
        f'<li><strong>{esc(m["move"])}</strong> <span class="cite">{esc(", ".join(cite(x) for x in m.get("citations", [])))}</span>'
        f'<br>{esc(m.get("steal_for_cgi") or m.get("steal") or "")}</li>'
        for m in angle.get("signature_moves", []))
    notes_body = "\n".join(l for l in notes.split("\n") if not l.startswith("# "))
    return f"""
<section id="{slug}" class="book">
  <p class="eyebrow">Book study</p>
  <h2>{esc(title)}</h2>
  <dl class="facts">
    <div><dt>Genre</dt><dd>{esc(meta.get("genre", ""))}</dd></div>
    <div><dt>Pages / panels</dt><dd>{npages} / {npanels}</dd></div>
    <div><dt>Growth density</dt><dd>{sc["growth_density_score"]} / 5</dd></div>
    <div><dt>Camera dynamism</dt><dd>{sc["camera_dynamism_score"]} / 5</dd></div>
    <div><dt>Expression intensity</dt><dd>{sc["expression_intensity_score"]} / 5</dd></div>
    <div><dt>Story &amp; structure</dt><dd>{sc["story_structure_score"]} / 5</dd></div>
  </dl>
  <h3>Signature moves</h3>
  <ol class="moves">{moves}</ol>
  <h3>Full analysis notes</h3>
  <div class="prose notes">{md_to_html(notes_body, slug, shift=2)}</div>
</section>"""


# real-render section
def examples_section():
    if not ledger or not results:
        return "", ""
    rows, n_pass = [], 0
    for c in ledger["cards"]:
        r = c.get("result")
        if not r:
            continue
        n_pass += r["status"] == "pass"
        crit = r.get("criteria", {})
        img = (f'<a href="{EX_REL}/{attr(r["winner_file"])}"><img src="{EX_REL}/{attr(r["winner_file"])}" loading="lazy" alt="{attr(c["family"])}"></a>'
               if r.get("winner_file") else "—")
        verdict = '<span class="pass">pass</span>' if r["status"] == "pass" else '<span class="fail">did not land</span>'
        ex = c.get("expect", {})
        rows.append(f'<tr><td>{img}</td><td>{esc(c["family"])}<br><span class="cite">{esc(c["card_id"])}</span></td>'
                    f'<td>{esc(ex.get("camera_height", ""))}<br><span class="cite">{crit.get("camera_height", "?")}/{r["of"]}</span></td>'
                    f'<td>{esc(ex.get("toward_camera", ""))}<br><span class="cite">{crit.get("toward_camera", "?")}/{r["of"]}</span></td>'
                    f'<td>{esc(ex.get("crop", ""))}<br><span class="cite">{crit.get("crop", "?")}/{r["of"]}</span></td>'
                    f'<td>{r["landed"]}/{r["of"]} {verdict}</td><td>{esc(r.get("note", ""))}</td></tr>')
    n = len(rows)
    ref = ledger.get("reference", {}).get("file", "")
    nav = '  <a href="#renders">Real renders</a>\n'
    sec = f"""
<section id="renders">
  <p class="eyebrow">Validation · {esc(ledger.get("date", ""))} · Higgsfield {MODEL_LABEL}</p>
  <h2>{n_pass} of {n} cards landed as real renders</h2>
  <div class="prose">
    <p>Ten cards, one per staging family, each generated once as a single count-4 call on {MODEL_LABEL} at 1k, 3:4, with the pipeline's photoreal DAZ style block, the line "the same character from the reference", and the card text verbatim. Reference: <code>{esc(ref)}</code>. A fresh Sonnet judge scored every variant on the three things the card promises: camera height, the body part nearest the lens, and the crop. A variant lands only if all three hold; a card passes with two landing variants of four. The winner of each passing card sits beside its seed in the deck above and is committed under <code>skills/comic-production/references/sketches/angle-card-examples/</code>; the ledger there records every job id and the model tag the job came back with.</p>
  </div>
  <div class="tablewrap results"><table><thead><tr><th>Render</th><th>Family · card</th><th>Camera height</th><th>Nearest the lens</th><th>Crop</th><th>Landed</th><th>Judge's note</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>
</section>"""
    return nav, sec


renders_nav, renders_section = examples_section()
n_ex = sum(1 for r in results.values() if r.get("status") == "pass")
n_fail = sum(1 for r in results.values() if r.get("status") != "pass")
deck_note = (f" {n_ex} cards carry a real {MODEL_LABEL} render beside the seed; {n_fail} that did not land are marked and kept."
             if results else "")

CSS = r"""
:root{
  --bg:#ECEFEC; --surface:#FFFFFF; --ink:#151A1C; --muted:#5B6568; --line:#C6CECA; --line-soft:#DDE3DF;
  --accent:#D3521B; --accent-ink:#FFFFFF; --mark:#E9A400; --ok:#1E7A3C; --code-bg:#E1E6E2; --hero:#1B2124; --hero-ink:#EEF1EC;
  --display:"Barlow Condensed","Arial Narrow","Helvetica Neue",Arial,sans-serif;
  --body:"Literata","Iowan Old Style",Georgia,serif;
  --mono:"IBM Plex Mono","SFMono-Regular",Menlo,Consolas,monospace;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --bg:#14181A; --surface:#1C2225; --ink:#E9ECE8; --muted:#9AA5A8; --line:#313B3F; --line-soft:#262E32;
    --accent:#F0703A; --accent-ink:#14181A; --mark:#F2B705; --ok:#4CC27A; --code-bg:#242D31; --hero:#0F1315; --hero-ink:#EEF1EC;
  }
}
:root[data-theme="dark"]{
  --bg:#14181A; --surface:#1C2225; --ink:#E9ECE8; --muted:#9AA5A8; --line:#313B3F; --line-soft:#262E32;
  --accent:#F0703A; --accent-ink:#14181A; --mark:#F2B705; --ok:#4CC27A; --code-bg:#242D31; --hero:#0F1315; --hero-ink:#EEF1EC;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--body);font-size:16.5px;line-height:1.55;-webkit-font-smoothing:antialiased}
a{color:var(--accent)}
a:focus-visible,button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
code{font-family:var(--mono);font-size:.82em;background:var(--code-bg);padding:.1em .35em;border-radius:2px}
h1,h2,h3,h4{font-family:var(--display);line-height:1.05;margin:0;text-wrap:balance;letter-spacing:.01em}
h2{font-size:2.2rem;font-weight:700;text-transform:uppercase;margin-top:8px}
h3{font-size:1.45rem;font-weight:600;margin-top:32px;margin-bottom:8px}
h4{font-size:1.15rem;font-weight:600;margin-top:22px;margin-bottom:4px}
h5{font-family:var(--display);font-size:1rem;text-transform:uppercase;letter-spacing:.06em;margin:18px 0 4px}
p{margin:0 0 1em}
.eyebrow{font-family:var(--mono);font-size:.72rem;text-transform:uppercase;letter-spacing:.14em;color:var(--muted);margin:0 0 6px}
hr{border:0;border-top:1px solid var(--line);margin:28px 0}
blockquote{margin:0 0 1em;padding:8px 16px;border-left:3px solid var(--mark);background:var(--surface)}
.hero{background:var(--hero);color:var(--hero-ink);padding:44px 24px 40px}
.hero .in{max-width:1120px;margin:0 auto;display:grid;grid-template-columns:minmax(0,1fr) auto;gap:32px;align-items:end}
.hero h1{font-size:clamp(2.6rem,6vw,4.6rem);font-weight:700;text-transform:uppercase;letter-spacing:.005em}
.hero .sub{max-width:62ch;font-size:1.05rem;margin-top:14px;opacity:.9}
.hero .eyebrow{color:var(--hero-ink);opacity:.7}
.slate-grid{display:grid;grid-template-columns:repeat(2,minmax(120px,1fr));gap:1px;background:var(--hero-ink);border:1px solid var(--hero-ink);font-family:var(--mono)}
.slate-grid div{background:var(--hero);padding:10px 14px}
.slate-grid b{display:block;font-family:var(--display);font-size:2rem;font-weight:700;line-height:1}
.slate-grid span{font-size:.7rem;text-transform:uppercase;letter-spacing:.12em;opacity:.75}
.page{max-width:1120px;margin:0 auto;padding:32px 24px 80px;display:grid;grid-template-columns:210px minmax(0,1fr);gap:48px}
nav.toc{position:sticky;top:20px;align-self:start;font-family:var(--display);font-size:1rem;text-transform:uppercase;letter-spacing:.03em}
nav.toc a{display:block;color:var(--muted);text-decoration:none;padding:5px 0;border-left:2px solid var(--line-soft);padding-left:12px}
nav.toc a:hover,nav.toc a.active{color:var(--ink);border-left-color:var(--accent)}
main{min-width:0}
section{padding:36px 0;border-top:1px solid var(--line)}
section:first-child{border-top:0;padding-top:0}
.prose{max-width:68ch}
.prose ul,.prose ol{padding-left:1.3em;margin:0 0 1em}
.prose li{margin:.3em 0}
.prose li>ul,.prose li>ol{margin:.3em 0 0}
.tablewrap{overflow-x:auto;margin:0 0 1.2em}
table{border-collapse:collapse;width:100%;font-size:.93rem;font-variant-numeric:tabular-nums}
th,td{text-align:left;vertical-align:top;padding:8px 10px;border-bottom:1px solid var(--line-soft)}
th{font-family:var(--display);font-size:1rem;text-transform:uppercase;letter-spacing:.04em;border-bottom:2px solid var(--ink)}
.facts{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:1px;background:var(--line);border:1px solid var(--line);margin:16px 0 0}
.facts div{background:var(--surface);padding:10px 12px}
.facts dt{font-family:var(--mono);font-size:.68rem;text-transform:uppercase;letter-spacing:.12em;color:var(--muted)}
.facts dd{margin:2px 0 0;font-family:var(--display);font-size:1.5rem;font-weight:600;font-variant-numeric:tabular-nums}
.moves{padding-left:1.4em;max-width:72ch}
.moves li{margin:.55em 0}
.cite{font-family:var(--mono);font-size:.72rem;color:var(--muted)}
.notes{margin-top:8px}
.filters{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:12px 0 18px}
.filters .lab{font-family:var(--mono);font-size:.7rem;text-transform:uppercase;letter-spacing:.12em;color:var(--muted);margin-right:4px;width:100%}
.chip{font-family:var(--display);font-size:.95rem;text-transform:uppercase;letter-spacing:.03em;background:var(--surface);color:var(--ink);border:1px solid var(--line);padding:5px 10px;cursor:pointer}
.chip b{font-family:var(--mono);font-weight:500;font-size:.72rem;color:var(--muted);margin-left:4px}
.chip.active{background:var(--accent);color:var(--accent-ink);border-color:var(--accent)}
.chip.active b{color:var(--accent-ink)}
.count{font-family:var(--mono);font-size:.75rem;color:var(--muted);margin:0 0 12px}
.deck{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:14px}
.card{background:var(--surface);border:1px solid var(--line);display:grid;gap:10px;padding:12px 14px 12px}
.card[hidden]{display:none}
.card header{display:flex;justify-content:space-between;align-items:center;font-family:var(--mono);font-size:.74rem;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
.card .seed{margin:0;font-size:1rem;line-height:1.5}
.card .body{display:grid;grid-template-columns:minmax(0,1fr) 128px;gap:12px;align-items:start}
.card figure.ex{margin:0}
.card figure.ex img{display:block;width:100%;aspect-ratio:3/4;object-fit:cover;border:1px solid var(--line);background:var(--code-bg)}
.card figure.ex figcaption{font-family:var(--mono);font-size:.62rem;line-height:1.35;color:var(--muted);margin-top:5px}
.nolanding{margin:0;font-family:var(--mono);font-size:.7rem;line-height:1.4;color:var(--accent);border:1px dashed var(--accent);padding:6px 9px}
.card footer{display:flex;flex-wrap:wrap;gap:6px 12px;font-family:var(--mono);font-size:.68rem;color:var(--muted);align-items:center;border-top:1px solid var(--line-soft);padding-top:8px}
.copy{margin-left:auto;font-family:var(--display);font-size:.85rem;text-transform:uppercase;letter-spacing:.05em;border:1px solid var(--line);background:transparent;color:var(--ink);padding:3px 9px;cursor:pointer}
.copy:hover{border-color:var(--accent);color:var(--accent)}
.score{display:inline-flex;gap:3px}
.score i{width:9px;height:9px;background:var(--line-soft);display:inline-block}
.score i.on{background:var(--mark)}
.results img{width:76px;aspect-ratio:3/4;object-fit:cover;display:block;border:1px solid var(--line);background:var(--code-bg)}
.results td{font-size:.88rem}
.pass{color:var(--ok);font-weight:600}
.fail{color:var(--accent);font-weight:600}
.rule{background:var(--surface);border:1px solid var(--line);border-left:4px solid var(--accent);padding:18px 22px;max-width:74ch}
.rule h2{font-size:1.7rem}
.rule h3{margin-top:20px}
.callout{font-family:var(--display);font-size:1.35rem;line-height:1.25;max-width:40ch;padding:14px 0 14px 18px;border-left:4px solid var(--mark);margin:18px 0 22px}
@media (max-width:900px){
  .page{grid-template-columns:1fr;gap:24px}
  nav.toc{position:static;display:flex;flex-wrap:wrap;gap:4px 14px}
  nav.toc a{border-left:0;padding-left:0}
  .hero .in{grid-template-columns:1fr}
}
@media (prefers-reduced-motion:no-preference){ .chip,.copy{transition:background .15s,color .15s,border-color .15s} }
"""

JS = r"""
(function(){
  var active={group:null,muscle:null};
  var cards=[].slice.call(document.querySelectorAll('#deckgrid .card'));
  var count=document.getElementById('count');
  function apply(){
    var n=0;
    cards.forEach(function(c){
      var ok=(!active.group||c.dataset.group===active.group)&&(!active.muscle||c.dataset.muscle===active.muscle);
      c.hidden=!ok; if(ok)n++;
    });
    count.textContent='Showing '+n+' of '+cards.length;
  }
  document.querySelectorAll('.chip').forEach(function(ch){
    ch.addEventListener('click',function(){
      var f=ch.dataset.filter,v=ch.dataset.value;
      var was=active[f]===v; active[f]=was?null:v;
      document.querySelectorAll('.chip[data-filter="'+f+'"]').forEach(function(x){x.classList.toggle('active',!was&&x.dataset.value===v);});
      apply();
    });
  });
  document.querySelectorAll('.copy').forEach(function(b){
    b.addEventListener('click',function(){
      var t=b.dataset.copy;
      function done(){b.textContent='Copied';setTimeout(function(){b.textContent='Copy';},1200);}
      try{navigator.clipboard.writeText(t).then(done,function(){fallback();});}catch(e){fallback();}
      function fallback(){var ta=document.createElement('textarea');ta.value=t;document.body.appendChild(ta);ta.select();try{document.execCommand('copy');done();}catch(e){}document.body.removeChild(ta);}
    });
  });
  var links=[].slice.call(document.querySelectorAll('nav.toc a'));
  var secs=links.map(function(a){return document.querySelector(a.getAttribute('href'));});
  function spy(){
    var y=window.scrollY+120,cur=0;
    secs.forEach(function(s,i){if(s&&s.offsetTop<=y)cur=i;});
    links.forEach(function(a,i){a.classList.toggle('active',i===cur);});
  }
  window.addEventListener('scroll',spy,{passive:true});spy();
})();
"""

page = f"""<meta charset="utf-8">
<title>Deed Arts Staging Study</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700&family=Literata:ital,opsz,wght@0,7..72,400;0,7..72,600;1,7..72,400&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>{CSS}</style>

<header class="hero">
  <div class="in">
    <div>
      <p class="eyebrow">Comic-corpus study · 2 September 2026</p>
      <h1>Deed Arts Staging Study</h1>
      <p class="sub">How one hand artist places the camera, crops the body, and escalates a growth page, mined from two commissioned books and turned into camera cards the 3D pipeline can append to a prompt. Composition only. His drawing style stays on his pages.</p>
    </div>
    <div class="slate-grid" role="list">
      <div role="listitem"><b>{len(books)}</b><span>books</span></div>
      <div role="listitem"><b>{pages_read}</b><span>pages read</span></div>
      <div role="listitem"><b>{panels_tagged}</b><span>panels tagged</span></div>
      <div role="listitem"><b>{len(cards)}</b><span>camera cards</span></div>
    </div>
  </div>
</header>

<div class="page">
<nav class="toc" aria-label="Sections">
  <a href="#summary">Summary</a>
  <a href="#camera">Where the camera sits</a>
  <a href="#moves">The eight moves</a>
  <a href="#seen">Seen on the pages</a>
  <a href="#translate">2D to 3D</a>
  <a href="#deck">Angle deck</a>
{renders_nav}  <a href="#l40">Lesson L40</a>
  <a href="#{BOOKS[0]}">Poppy study</a>
  <a href="#{BOOKS[1]}">Omega study</a>
  <a href="#use">How to use it</a>
</nav>
<main>
<section id="summary"><p class="eyebrow">Read this first</p><h2>What he does that our panels don't</h2><div class="prose">{intro_html}</div><p class="callout">The camera never goes above the muscle character's head. Something always comes at the lens. The crop makes the sold muscle the widest thing in the frame.</p><div class="prose">{summary_html}</div></section>
<section id="camera"><p class="eyebrow">{panels_tagged} panels, both books</p><h2>Where the camera sits</h2><div class="prose">{camera_html}</div></section>
<section id="moves"><p class="eyebrow">Ranked by how often he returns to them</p><h2>The eight moves</h2><div class="prose">{moves_html}</div></section>
<section id="seen"><p class="eyebrow">Orchestrator verification</p><h2>Seen on the pages, missed by the tagging</h2><div class="prose">{seen_html}</div></section>
<section id="translate"><p class="eyebrow">Substitutions</p><h2>What does not translate to 3D</h2><div class="prose">{translate_html}</div></section>

<section id="deck">
  <p class="eyebrow">Angle deck · steal score 3 and up · deduplicated</p>
  <h2>{len(cards)} camera cards</h2>
  <p class="prose">Each card is one sentence of camera, pose, crop, and the muscle it sells, written from a real panel. Append one after the continuation line and the references. No appearance, no size words, no style. Filter by angle or by the muscle being sold; Copy puts the sentence on your clipboard.{deck_note}</p>
  <div class="filters">
    <span class="lab">Angle</span>{angle_chips}
  </div>
  <div class="filters">
    <span class="lab">Muscle sold</span>{muscle_chips}
  </div>
  <p class="count" id="count">Showing {len(cards)} of {len(cards)}</p>
  <div class="deck" id="deckgrid">{"".join(card_html(c) for c in cards)}</div>
</section>
{renders_section}
<section id="l40">
  <p class="eyebrow">Routed to production</p>
  <div class="rule prose">{l40_html}</div>
  <h3>The framing-guide version</h3>
  <div class="prose">{framing_html}</div>
</section>

{"".join(book_html(*b) for b in books)}

<section id="use">
  <p class="eyebrow">In practice</p>
  <h2>How to use it in Flow</h2>
  <div class="prose">
    <ol>
      <li>Keep your prompt exactly as you write it now: the continuation line, the style line, the references, the growth delta.</li>
      <li>Pick one card from the deck that matches the beat, and append it as the last sentence. The Prompt Deck append mode is being built for this; until then, Copy and paste.</li>
      <li>On a growth page, hold the camera still across the rungs (the flex ladder) or cut between body-part close-ups with one motif (the column). Make the last panel the biggest.</li>
      <li>Before you submit a solo muscle panel, answer L40's four questions: camera height, part nearest the lens, muscle sold and its crop, body line.</li>
    </ol>
    <p>Source files in the pipeline repo: <code>research/comic-corpus/synthesis/cards.json</code> (the deck), <code>angle-study-addendum.md</code> (how panels get tagged), and the two <code>corpus/deed-arts-*</code> folders (per-panel data). Raw pages stay local and out of git. Real renders and the pass ledger: <code>skills/comic-production/references/sketches/angle-card-examples/</code>.</p>
  </div>
</section>
</main>
</div>

<script>{JS}</script>
"""

OUT.write_text(page)
print(f"wrote {OUT.relative_to(REPO)}: {len(page):,} bytes, {len(cards)} cards, "
      f"{n_ex} with renders, {n_fail} marked did-not-land, {len(books)} books")
