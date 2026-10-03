#!/usr/bin/env python3
"""Self-test for ws_hook.py (python3 stdlib only): python3 studio/worker/test_ws_hook.py

Runs ws_hook.py as Claude Code would (hook JSON on stdin, decision JSON on stdout) against a temp state dir with a
hand-made claim.json / token.json, and checks the allow/deny cases. Also checks that wsw and ws_hook.py hash prompts
the same way. Exit 0 = all passed.
"""
import hashlib
import importlib.machinery
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

sys.dont_write_bytecode = True   # loading wsw / ws_hook.py as modules must not drop a __pycache__ next to them
HERE = os.path.dirname(os.path.abspath(__file__))
HOOK = os.path.join(HERE, 'ws_hook.py')
WSW = os.path.join(HERE, 'wsw')
GEN = 'mcp__claude_ai_higgsfield__generate_image'
IMP = 'mcp__claude_ai_higgsfield__media_import_url'
REF = ('https://3dmusclecomics.com/studio/ws-worker.php?do=refimg&p=lt-made-comic&f=ab12cd34ef.png&exp=1790000000&sig='
       + 'a' * 64)
PROMPT = 'Page 1: she flexes  in the gym.\n\nStyle: DAZ3D render, éclat lighting'

passed = failed = 0


def load(path, name):
    loader = importlib.machinery.SourceFileLoader(name, path)
    spec = importlib.util.spec_from_loader(name, loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


def check(label, cond, detail=''):
    global passed, failed
    if cond:
        passed += 1
        print('ok   ' + label)
    else:
        failed += 1
        print('FAIL ' + label + ('  ' + str(detail)[:300] if detail else ''))


class Env:
    def __init__(self):
        self.dir = tempfile.mkdtemp(prefix='wshook-')
        self.hook = load(HOOK, 'ws_hook_mod')

    def write(self, name, obj):
        with open(os.path.join(self.dir, name), 'w') as f:
            json.dump(obj, f)

    def read(self, name):
        try:
            with open(os.path.join(self.dir, name)) as f:
                return json.load(f)
        except OSError:
            return None

    def claim(self, job_id='wsj_A', prompt=PROMPT, aspect='9:16', refs=(REF,)):
        self.write('claim.json', {'job': {'id': job_id, 'prompt': prompt, 'aspect': aspect},
                                  'refs': [{'file': 'x.png', 'url': u} for u in refs]})

    def token(self, job_id='wsj_A', prompt=PROMPT, aspect='9:16', age=0, used=False, max_medias=1):
        self.write('token.json', {'job': job_id, 'promptSha256': self.hook.prompt_sha256(prompt), 'aspect': aspect,
                                  'maxMedias': max_medias, 'ts': int(time.time() - age), 'used': used})

    def run(self, tool, inp, raw=None, state_dir=None):
        ev = raw if raw is not None else json.dumps({'hook_event_name': 'PreToolUse', 'tool_name': tool, 'tool_input': inp})
        env = dict(os.environ, WS_STATE_DIR=state_dir or self.dir)
        env.pop('WS_BASE', None)
        p = subprocess.run([sys.executable, HOOK], input=ev.encode(), capture_output=True, env=env, timeout=30)
        out = p.stdout.decode().strip()
        if p.returncode != 0:
            return {'rc': p.returncode, 'stderr': p.stderr.decode()[:300]}
        if not out:
            return None
        h = json.loads(out)['hookSpecificOutput']
        return {'d': h['permissionDecision'], 'why': h.get('permissionDecisionReason', ''), 'event': h.get('hookEventName')}

    def close(self):
        shutil.rmtree(self.dir, ignore_errors=True)


def good(**over):
    p = {'model': 'nano_banana_pro', 'resolution': '1k', 'count': 1, 'aspect_ratio': '9:16', 'prompt': PROMPT,
         'medias': [{'role': 'image', 'value': '0f8fad5b-d9cb-469f-a165-70867728950e'}], 'use_unlim': False}
    p.update(over)
    return p


def without(key):
    p = good()
    del p[key]
    return p


def main():
    e = Env()
    try:
        allow = lambda r: r is not None and r.get('d') == 'allow'   # noqa: E731
        deny = lambda r: r is not None and r.get('d') == 'deny'     # noqa: E731

        # ---- generate_image: the happy path, then one-shot ----
        e.claim(); e.token()
        r = e.run(GEN, {'params': good()})
        check('allow: fresh token + exact params (params-nested)', allow(r) and r['event'] == 'PreToolUse', r)
        check('token is marked used after an allow', (e.read('token.json') or {}).get('used') is True)
        r = e.run(GEN, {'params': good()})
        check('deny: same token twice (one-shot)', deny(r) and 'already used' in r['why'], r)

        e.token(); r = e.run(GEN, good())
        check('allow: flat (top-level) input shape', allow(r), r)
        e.token(); r = e.run(GEN, {'params': json.dumps(good())})
        check('allow: params given as a JSON string', allow(r), r)
        e.token(); r = e.run(GEN, {'params': without('medias')})
        check('allow: no medias (job without refs)', allow(r), r)
        e.token(); r = e.run(GEN, {'params': without('use_unlim')})
        check('allow: use_unlim absent', allow(r), r)
        e.token(); r = e.run(GEN, {'params': good(prompt='Page 1: she flexes in the gym. Style: DAZ3D render, éclat lighting')})
        check('allow: same prompt with whitespace collapsed', allow(r), r)

        # ---- no / bad token ----
        os.remove(os.path.join(e.dir, 'token.json'))
        r = e.run(GEN, {'params': good()})
        check('deny: no token (no submit-ok)', deny(r) and 'submit-ok' in r['why'], r)
        e.token(age=200); r = e.run(GEN, {'params': good()})
        check('deny: token older than 180 s', deny(r) and 'stale' in r['why'], r)
        e.token(age=-60); r = e.run(GEN, {'params': good()})
        check('deny: token from the future', deny(r) and 'stale' in r['why'], r)
        e.token(used=True); r = e.run(GEN, {'params': good()})
        check('deny: token already used', deny(r), r)
        e.token(job_id='wsj_OTHER'); r = e.run(GEN, {'params': good()})
        check('deny: token for another job', deny(r) and 'another job' in r['why'], r)
        os.remove(os.path.join(e.dir, 'claim.json')); e.token()
        r = e.run(GEN, {'params': good()})
        check('deny: no claimed job (state cleared by done)', deny(r) and 'no claimed job' in r['why'], r)
        e.claim()

        # ---- param mismatches (each burns the token) ----
        cases = [
            ('model', {'params': good(model='gpt_image_2_5')}, 'model'),
            ('resolution 2k', {'params': good(resolution='2k')}, 'resolution'),
            ('resolution absent', {'params': without('resolution')}, 'resolution'),
            ('count 2', {'params': good(count=2)}, 'count'),
            ('count absent', {'params': without('count')}, 'count'),
            ('count true', {'params': good(count=True)}, 'count'),
            ('count "1"', {'params': good(count='1')}, 'count'),
            ('use_unlim true', {'params': good(use_unlim=True)}, 'use_unlim'),
            ('folder_id', {'params': good(folder_id='00000000-0000-0000-0000-000000000000')}, 'not allowed'),
            ('get_cost', {'params': good(get_cost=True)}, 'not allowed'),
            ('aspect', {'params': good(aspect_ratio='16:9')}, 'aspect'),
            ('prompt changed', {'params': good(prompt=PROMPT + ' Extra muscles.')}, 'prompt'),
            ('prompt missing', {'params': without('prompt')}, 'prompt'),
            ('two medias for one ref', {'params': good(medias=[{'role': 'image', 'value': 'a'}, {'role': 'image', 'value': 'b'}])}, 'medias'),
            ('media is a url', {'params': good(medias=[{'role': 'image', 'value': 'https://evil.example/x.png'}])}, 'medias'),
            ('extra top-level key', {'params': good(), 'x': 1}, 'malformed'),
            ('params not json', {'params': '{not json'}, 'malformed'),
            ('params a list', {'params': [1]}, 'malformed'),
        ]
        for label, inp, word in cases:
            e.token()
            r = e.run(GEN, inp)
            tok = e.read('token.json') or {}
            burnt = tok.get('used') is True
            check('deny: ' + label, deny(r) and word in r['why'] and burnt, [r, tok.get('used')])
        e.token(); e.run(GEN, {'params': good(model='seedream')})
        r = e.run(GEN, {'params': good()})
        check('deny: a denied call used the token up (no retry with fixed params)', deny(r) and 'already used' in r['why'], r)

        # ---- media_import_url ----
        r = e.run(IMP, {'url': REF, 'type': 'image'})
        check('allow: import of the claimed job ref', allow(r), r)
        r = e.run(IMP, {'url': REF.replace('sig=' + 'a' * 64, 'sig=' + 'b' * 64), 'type': 'image'})
        check('deny: signed-looking ref that is not the job\'s', deny(r) and 'not a ref' in r['why'], r)
        r = e.run(IMP, {'url': 'https://evil.example.com/x.png', 'type': 'image'})
        check('deny: import from another host', deny(r) and 'signed Studio ref' in r['why'], r)
        r = e.run(IMP, {'url': 'https://3dmusclecomics.com.evil.com/studio/ws-worker.php?do=refimg&p=x', 'type': 'image'})
        check('deny: host suffix trick', deny(r), r)
        r = e.run(IMP, {'url': 'https://3dmusclecomics.com/studio/ws-worker.php?do=claim&x=1', 'type': 'image'})
        check('deny: Studio url that is not do=refimg', deny(r), r)
        r = e.run(IMP, {'url': REF, 'type': 'video'})
        check('deny: type video', deny(r), r)
        os.remove(os.path.join(e.dir, 'claim.json'))
        r = e.run(IMP, {'url': REF, 'type': 'image'})
        check('deny: import with no claimed job', deny(r), r)
        e.claim()

        # ---- an edit job (cockpit Adjust, kind 'edit'): ONE ref = the parent image, server-built prompt, parent aspect ----
        edit_ref = REF.replace('f=ab12cd34ef.png', 'f=g1parent00.png')
        edit_prompt = ('Edit this comic page image. Keep the same 2D/3D art style, page layout, panel borders, characters, faces, '
                       'hair, outfits, colors, lettering and speech bubbles exactly as they are. Change only this: Make her tank top '
                       'red. Every person has exactly two arms, two hands and two legs. Do not add any new text, people or objects.')
        e.claim(job_id='wsj_E', prompt=edit_prompt, aspect='4:5', refs=(edit_ref,))
        r = e.run(IMP, {'url': edit_ref, 'type': 'image'})
        check('edit job: allow import of the parent image (its one signed ref)', allow(r), r)
        e.token(job_id='wsj_E', prompt=edit_prompt, aspect='4:5', max_medias=1)
        r = e.run(GEN, {'params': good(prompt=edit_prompt, aspect_ratio='4:5')})
        check('edit job: allow the exact edit prompt + parent aspect + the one parent media', allow(r), r)
        e.token(job_id='wsj_E', prompt=edit_prompt, aspect='4:5', max_medias=1)
        r = e.run(GEN, {'params': good(prompt=edit_prompt, aspect_ratio='4:5', medias=[{'role': 'image', 'value': 'a'}, {'role': 'image', 'value': 'b'}])})
        check('edit job: deny a second media (no refs beyond the image to edit)', deny(r) and 'medias' in r['why'], r)
        e.token(job_id='wsj_E', prompt=edit_prompt, aspect='4:5', max_medias=1)
        r = e.run(GEN, {'params': good(prompt=edit_prompt + ' Make her bigger.', aspect_ratio='4:5')})
        check('edit job: deny a reworded edit prompt', deny(r) and 'prompt' in r['why'], r)
        e.token(job_id='wsj_E', prompt=edit_prompt, aspect='4:5', max_medias=1)
        r = e.run(GEN, {'params': good(prompt=edit_prompt, aspect_ratio='3:4')})
        check('edit job: deny an aspect other than the parent\'s', deny(r) and 'aspect' in r['why'], r)
        e.claim()

        # ---- other tools ----
        r = e.run('mcp__claude_ai_higgsfield__jobs_wait', {'jobs': [{'index': 0, 'job_id': 'x'}]})
        check('no decision for read-only jobs_wait (permissions decide)', r is None, r)
        r = e.run('mcp__claude_ai_higgsfield__balance', {})
        check('no decision for balance', r is None, r)
        r = e.run('mcp__claude_ai_higgsfield__generate_video', {'params': {}})
        check('deny: generate_video', deny(r), r)
        r = e.run('mcp__claude_ai_higgsfield__generate_image_batch', {'params': {}})
        check('deny: generate_image_batch', deny(r), r)
        r = e.run('Bash', {'command': 'ls'})
        check('deny: a non-Higgsfield tool that reaches the hook', deny(r), r)

        # ---- internal errors deny ----
        r = e.run(GEN, None, raw='this is not json')
        check('deny: malformed hook input (internal error)', deny(r) and 'internal error' in r['why'], r)
        r = e.run(GEN, {'params': good()}, state_dir=os.path.join(e.dir, 'missing', 'dir'))
        check('deny: state dir missing (internal error)', deny(r) and 'internal error' in r['why'], r)
        e.write('token.json', {'job': 'wsj_A', 'promptSha256': 'x', 'aspect': '9:16', 'maxMedias': 'lots', 'ts': int(time.time()), 'used': False})
        r = e.run(GEN, {'params': good()})
        check('deny: corrupt token field (internal error)', deny(r), r)

        # ---- wsw and the hook hash prompts the same way ----
        try:
            w = load(WSW, 'wsw_mod')
            same = all(w.prompt_sha256(s) == e.hook.prompt_sha256(s) for s in (PROMPT, '', '  a\tb\n', 'Café é'))
            check('wsw.prompt_sha256 == ws_hook.prompt_sha256', same)
            check('prompt hash is NFC + whitespace-collapsed sha256',
                  e.hook.prompt_sha256(' a \n b ') == hashlib.sha256(b'a b').hexdigest())
        except SystemExit as ex:
            check('wsw imports as a module', False, ex)
    finally:
        e.close()
    print('\n%d passed, %d failed' % (passed, failed))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
