#!/usr/bin/env python3
"""ws_hook.py - PreToolUse hook for the opsbox `ws-worker` job (python3 stdlib only).

The worker's job prompts are written by lieutenants (untrusted), so the credit bound must not depend on the agent
following its playbook. opsjob wires this hook (jobs/ws-worker.conf HOOKS) on:

  mcp__claude_ai_higgsfield__generate_image   allowed ONLY with a fresh one-shot token that `wsw submit-ok` wrote
                                              (exit 0) into the wsw state dir: unused, < 180 s old, for the claimed
                                              job, and the call must be exactly model nano_banana_pro, resolution 1k,
                                              count 1, use_unlim false/absent, no folder_id (no other keys at all),
                                              aspect_ratio == the job's aspect, sha256(prompt) == the job's prompt
                                              hash, at most one medias entry per ref. The token is used up by the
                                              call - or by a denied attempt, so a denial can never be "fixed" by
                                              retrying with other params.
  mcp__claude_ai_higgsfield__media_import_url allowed ONLY for a signed ref url of the claimed job
                                              (https://3dmusclecomics.com/studio/ws-worker.php?do=refimg&...).

Read-only Higgsfield tools the job uses get no decision (the job's permissions decide); any other tool that reaches
this hook is denied. Any internal error denies. Output: the PreToolUse decision JSON on stdout, exit 0.
State dir: WS_STATE_DIR (default ~/.opsbox/ws), shared with wsw (claim.json, token.json, state.lock).
A copy lives in claude-comic-pipeline studio/worker/ws_hook.py - keep the two byte-identical.
"""
import fcntl
import hashlib
import json
import os
import sys
import time
import unicodedata

STATE_DIR = os.path.abspath(os.path.expanduser(os.environ.get('WS_STATE_DIR') or '~/.opsbox/ws'))
TOKEN_TTL = 180
REF_PREFIX = (os.environ.get('WS_BASE') or 'https://3dmusclecomics.com/studio/ws-worker.php') + '?do=refimg&'
MODEL, RESOLUTION = 'nano_banana_pro', '1k'
GEN_KEYS = {'model', 'resolution', 'count', 'aspect_ratio', 'prompt', 'medias', 'use_unlim'}
DEFER = {'jobs_wait', 'job_display', 'show_generation_by_ids', 'balance', 'media_upload', 'media_confirm'}


def decision(d, why):
    return {'hookSpecificOutput': {'hookEventName': 'PreToolUse', 'permissionDecision': d,
                                   'permissionDecisionReason': 'ws_hook: ' + why}}


def prompt_sha256(prompt):
    """sha256 of the prompt after NFC + whitespace collapsing. MUST stay identical to wsw's."""
    s = ' '.join(unicodedata.normalize('NFC', str(prompt)).split())
    return hashlib.sha256(s.encode('utf-8')).hexdigest()


def _sp(name):
    return os.path.join(STATE_DIR, name)


def _read(name):
    try:
        with open(_sp(name), encoding='utf-8') as f:
            d = json.load(f)
        return d if isinstance(d, dict) else None
    except (OSError, ValueError):
        return None


def _write(name, obj):   # atomic: tmp file + rename
    tmp = '%s.tmp%d' % (_sp(name), os.getpid())
    with os.fdopen(os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, separators=(',', ':'))
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, _sp(name))


class _Lock:
    def __enter__(self):
        self.fd = os.open(_sp('state.lock'), os.O_RDWR | os.O_CREAT, 0o600)
        fcntl.flock(self.fd, fcntl.LOCK_EX)
        return self

    def __exit__(self, *exc):
        try:
            fcntl.flock(self.fd, fcntl.LOCK_UN)
        finally:
            os.close(self.fd)


def gen_params(inp):
    """The generate_image params, from {"params": {...}} / {"params": "<json>"} or a flat input. None = malformed."""
    if 'params' in inp:
        if set(inp) != {'params'}:
            return None
        p = inp['params']
        if isinstance(p, str):
            try:
                p = json.loads(p)
            except ValueError:
                return None
        return p if isinstance(p, dict) else None
    return inp


def check_params(p, tok):
    """'' when the call matches the token exactly, else why not."""
    extra = sorted(set(p) - GEN_KEYS)
    if extra:
        return 'parameters not allowed: %s' % ', '.join(map(str, extra))[:200]
    if p.get('model') != MODEL:
        return 'model must be %s' % MODEL
    if p.get('resolution') != RESOLUTION:
        return 'resolution must be %s' % RESOLUTION
    c = p.get('count')
    if isinstance(c, bool) or c != 1:
        return 'count must be exactly 1'
    if 'use_unlim' in p and p['use_unlim'] is not False:
        return 'use_unlim must be false or absent'
    if not isinstance(p.get('aspect_ratio'), str) or p['aspect_ratio'] != tok.get('aspect'):
        return 'aspect_ratio must be the job aspect %r' % tok.get('aspect')
    if not isinstance(p.get('prompt'), str) or prompt_sha256(p['prompt']) != tok.get('promptSha256'):
        return 'prompt is not the claimed job prompt, character for character'
    m = p.get('medias', [])
    if not isinstance(m, list) or len(m) > int(tok.get('maxMedias') or 0):
        return 'medias must be a list with at most one entry per ref of the job'
    for e in m:
        if not isinstance(e, dict) or set(e) - {'role', 'value'} or not isinstance(e.get('value'), str) \
                or not isinstance(e.get('role'), str) or e['value'].lower().startswith(('http:', 'https:')):
            return 'each medias entry must be {role, value: media_id}'
    return ''


def gate_generate(inp):
    p = gen_params(inp)
    with _Lock():
        claim = _read('claim.json')
        tok = _read('token.json')
        job = (claim or {}).get('job') if isinstance((claim or {}).get('job'), dict) else None
        if not job or not job.get('id'):
            return decision('deny', 'no claimed job in this run')
        if not tok:
            return decision('deny', 'no submit token: run `wsw submit-ok JOB` (exit 0) right before every generate_image')
        if tok.get('used'):
            return decision('deny', 'the submit token was already used: one generate_image per exit-0 `wsw submit-ok`')
        if tok.get('job') != job.get('id'):
            return decision('deny', 'the submit token is for another job')
        age = time.time() - float(tok.get('ts') or 0)
        if not (-5 <= age < TOKEN_TTL):
            return decision('deny', 'the submit token is stale (%ds old; limit %ds): run `wsw submit-ok JOB` again' % (int(age), TOKEN_TTL))
        why = 'malformed generate_image input' if p is None else check_params(p, tok)
        tok['used'] = True
        tok['usedAt'] = int(time.time())
        if why:
            tok['deniedReason'] = why   # burnt: a denied call is not retried with other params on the same token
        _write('token.json', tok)
    if why:
        return decision('deny', why + ' (token used up; run `wsw fail JOB "hook denied"`)')
    return decision('allow', 'generate_image for job %s (one-shot token used)' % job.get('id'))


def gate_import(inp):
    url = inp.get('url')
    if not isinstance(url, str) or not url.startswith(REF_PREFIX) or any(ch.isspace() or ord(ch) < 32 for ch in url) or '#' in url:
        return decision('deny', 'media_import_url only for signed Studio ref urls (%s...)' % REF_PREFIX)
    claim = _read('claim.json') or {}
    refs = [r.get('url') for r in (claim.get('refs') or []) if isinstance(r, dict)]
    if url not in refs:
        return decision('deny', 'that url is not a ref of the claimed job')
    if set(inp) - {'url', 'type'} or inp.get('type', 'image') not in ('image', 'auto'):
        return decision('deny', 'media_import_url takes only url and type=image')
    return decision('allow', 'import of a signed ref of the claimed job')


def decide(ev):
    name = str(ev.get('tool_name') or '')
    inp = ev.get('tool_input')
    if not isinstance(inp, dict):
        inp = {}
    short = name.rsplit('__', 1)[-1] if name.startswith('mcp__') and 'higgsfield' in name else ''
    if short == 'generate_image':
        return gate_generate(inp)
    if short == 'media_import_url':
        return gate_import(inp)
    if short in DEFER:
        return None   # read-only / upload plumbing: the job's permission rules decide
    return decision('deny', 'tool %s is not allowed for the workspace worker' % name[:80])


def main():
    try:
        ev = json.load(sys.stdin)
        d = decide(ev if isinstance(ev, dict) else {})
    except Exception as e:   # any internal error denies
        d = decision('deny', 'internal error (%s: %s)' % (type(e).__name__, str(e)[:160]))
    if d is not None:
        sys.stdout.write(json.dumps(d) + '\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
