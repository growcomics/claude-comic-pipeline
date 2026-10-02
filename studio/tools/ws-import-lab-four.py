#!/usr/bin/env python3
"""Import the pilot comic THE FORMULA (~/Documents/lab-four-comic) into the Studio
lieutenant workspace (2026-10-01).

What it does, in order:
  1. bridge ingest_init  -> creates/resolves the studio project ("The Formula")
  2. bridge ingest_ref   -> uploads the cast/scene reference images (isref)
  3. bridge ingest       -> uploads every take the owner's picker showed (QA-passed),
                            with that page's prompt; resumable (skips takes whose
                            orig name is already in the project)
  4. bridge write        -> group = "Page NN", owner picks -> accepted + rating good,
                            Claude's pick -> tag judge-pick
  5. prints the workspace files (proj/picks/chat seed + projectBrands) as JSON to
     --out, for the deployer to push into data/ws/ (the bridge has no verb for them)

Key: BRIDGE_KEY env var (never printed). Run with --dry-run first.
"""
import argparse, json, os, re, sys, hashlib, time, urllib.request, urllib.parse, uuid

BASE = os.environ.get('BRIDGE_URL', 'https://3dmusclecomics.com/studio/bridge.php')
UA = 'Mozilla/5.0 (studio-ws-import)'  # Cloudflare blocks the default Python-urllib UA (error 1010)
SRC = os.path.expanduser('~/Documents/lab-four-comic')


def post(data, files=None, timeout=180):
    key = os.environ.get('BRIDGE_KEY', '').strip()
    if not key:
        sys.exit('BRIDGE_KEY not set')
    data = dict(data, key=key)
    if files:
        bnd = uuid.uuid4().hex
        body = b''
        for k, v in data.items():
            body += f'--{bnd}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
        for k, path in files.items():
            name = os.path.basename(path)
            body += (f'--{bnd}\r\nContent-Disposition: form-data; name="{k}"; filename="{name}"\r\n'
                     f'Content-Type: image/jpeg\r\n\r\n').encode() + open(path, 'rb').read() + b'\r\n'
        body += f'--{bnd}--\r\n'.encode()
        req = urllib.request.Request(BASE, data=body, headers={'Content-Type': f'multipart/form-data; boundary={bnd}', 'User-Agent': UA})
    else:
        req = urllib.request.Request(BASE, data=urllib.parse.urlencode(data).encode(), headers={'User-Agent': UA})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode())
        except Exception as e:  # transient network / 5xx
            if attempt == 3:
                raise
            time.sleep(3 * (attempt + 1))


def strip_page_no(t):
    # "Page 1, a flashback ..." -> "A flashback ..." (page numbers in prompts get lettered onto the art)
    t = re.sub(r'^\s*Page\s+\d+\s*[,:.\-–—]\s*', '', t.strip(), flags=re.I)
    return t[:1].upper() + t[1:]


def build_manifest():
    pages_j = json.load(open(f'{SRC}/pages.json'))
    v2 = json.load(open(f'{SRC}/pages_v2.json'))
    shown = json.load(open(f'{SRC}/picker-data-lab1.json'))
    picks = json.load(open(f'{SRC}/picks-lab1.json'))
    story = open(f'{SRC}/STORY.md').read()
    style = (pages_j['style'].strip() + ' ' + v2['lock'].strip() + pages_j['guard']).strip()
    v2p = {x['p']: x for x in v2['pages']}
    ref_sets = {'pre': pages_j['pre_refs'], 'post': pages_j['post_refs']}
    pages = []
    all_refs = []
    for pg in pages_j['pages']:
        n = int(pg['p'])
        sh = next(x for x in shown if int(x['page']) == n)
        refs = v2p[n]['refs'] if n in v2p else ref_sets[pg['refs']]
        refs = [r for r in refs if r not in (pg.get('drop') or [])]
        prompt = v2p[n]['text'] if n in v2p else pg['text']
        pick = picks.get(str(n))
        pick = [pick] if isinstance(pick, str) else (pick or [])
        title = re.sub(r'\s*\(\d+ shown.*$', '', sh['title']).strip()
        pages.append({'n': n, 'title': title, 'prompt': strip_page_no(prompt), 'takes': sh['ids'],
                      'claude': [sh['claude']] if sh.get('claude') else [], 'pick': pick,
                      'comment': picks.get('_comments', {}).get(str(n), ''), 'refs': refs})
        for r in refs:
            if r not in all_refs:
                all_refs.append(r)
    return {'name': 'The Formula', 'brand': '3DMC', 'aspect': '3:4', 'story': story[:20000], 'style': style,
            'pages': pages, 'refs': all_refs}


def label_for(path):
    b = os.path.splitext(os.path.basename(path))[0]
    return ('Cast lineup ' + b.split('_', 1)[1]) if b.startswith('cast_') else ('Scene/stage keeper ' + b)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--out', default='ws-seed-the-formula.json')
    a = ap.parse_args()
    m = build_manifest()
    ntakes = sum(len(p['takes']) for p in m['pages'])
    print(f"manifest: {len(m['pages'])} pages, {ntakes} takes, {len(m['refs'])} refs")
    if a.dry_run:
        for p in m['pages']:
            print(f"  p{p['n']:02d} {len(p['takes']):2d} takes pick={len(p['pick'])} refs={len(p['refs'])} '{p['title'][:40]}' :: {p['prompt'][:70]}")
        return
    r = post({'do': 'ingest_init', 'project': m['name']})
    pid = r['project']
    print('project', pid)
    existing = post({'do': 'images', 'p': pid}).get('images', [])
    have = {x.get('orig'): x['file'] for x in existing}
    # refs
    ref_file = {}
    for path in m['refs']:
        orig = os.path.basename(path)
        if orig in have:
            ref_file[path] = have[orig]; continue
        kind = 'body' if orig.startswith('cast_') else 'scene'
        r = post({'do': 'ingest_ref', 'p': pid, 'orig': orig, 'kind': kind, 'label': label_for(path), 'status': 'approved'},
                 {'file': f'{SRC}/{path}'})
        if not r.get('ok'):
            sys.exit(f'ref failed {path}: {r}')
        ref_file[path] = r['file']; print('  ref', orig, '->', r['file'])
    # takes
    take_file = {}
    for p in m['pages']:
        for path in p['takes']:
            orig = os.path.basename(path)
            if orig in have:
                take_file[path] = have[orig]; continue
            r = post({'do': 'ingest', 'p': pid, 'orig': orig, 'gen': os.path.splitext(orig)[0], 'prompt': p['prompt'],
                      'accepted': '0'}, {'file': f'{SRC}/{path}'})
            if not r.get('ok'):
                sys.exit(f'take failed {path}: {r}')
            print(f"  p{p['n']:02d} {orig} ok ({r.get('count')})")
    imgs = post({'do': 'images', 'p': pid})['images']
    have = {x.get('orig'): x['file'] for x in imgs}
    for p in m['pages']:
        for path in p['takes']:
            take_file[path] = have[os.path.basename(path)]
    # groups, picks, claude tags
    decs = []
    for p in m['pages']:
        grp = f"Page {p['n']:02d}"
        for path in p['takes']:
            f = take_file[path]
            d = {'file': f, 'group': grp, 'accepted': path in p['pick']}
            if path in p['pick']:
                d['rating'] = 'good'
            if path in p['claude']:
                d['addtags'] = ['judge-pick']
            decs.append(d)
    r = post({'do': 'write', 'p': pid, 'decisions': json.dumps(decs)})
    print('write', r)
    # workspace seed files
    now = int(time.time())
    proj = {'story': m['story'], 'style': m['style'], 'aspect': m['aspect'],
            'pages': [{'n': p['n'], 'title': p['title'], 'prompt': p['prompt'],
                       'refs': [ref_file[x] for x in p['refs'] if x in ref_file]} for p in m['pages']],
            'refs': [{'file': ref_file[x], 'label': label_for(x), 'kind': 'ref'} for x in m['refs']]}
    picks = {'pages': {}}
    for p in m['pages']:
        grp = f"Page {p['n']:02d}"
        files = sorted(take_file[x] for x in p['takes'])
        picks['pages'][grp] = {'pick': [take_file[x] for x in p['pick']], 'c': p['comment'], 'prev_c': '',
                               'sig': hashlib.sha1('|'.join(files).encode()).hexdigest(), 'by': 'Grow', 'ts': now}
    redo = 'Page 6 (redo: the whole torso should grow, not one arm), and re-rolls for pages 3, 4, 8 (Tess drawn as a second Jada), 10 and 11.'
    chat = {'msgs': [
        {'id': 1, 'ts': now, 'role': 'system', 'by': 'Studio',
         'text': '📁 The Formula imported from the owner\'s first pass: 12 pages, the takes that passed QA, the cast refs and the owner\'s picks.'},
        {'id': 2, 'ts': now, 'role': 'system', 'by': 'Studio', 'text': '📝 Open work from the owner: ' + redo},
    ]}
    out = {'pid': pid, 'brand': m['brand'], 'proj': proj, 'picks': picks, 'chat': chat}
    json.dump(out, open(a.out, 'w'), indent=1, ensure_ascii=False)
    print('seed written to', a.out)


if __name__ == '__main__':
    main()
