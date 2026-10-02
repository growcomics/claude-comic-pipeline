#!/usr/bin/env node
// studio/tests/locks/run.mjs: PHP-wasm 8.1 tests for the LOCKED read-modify-writes of the legacy Studio
// pages (2026-10-01): api.php, bridge.php, creator.php, port.php, index.php, project.php, gribble.php,
// growgetter.php. Kept apart from tests/ws/run.mjs so that suite stays at its 374 checks.
//
//   node studio/tests/locks/run.mjs                 PASS/FAIL per assertion + summary; exit 1 on any failure
//   node studio/tests/locks/run.mjs --old <dir>     sensitivity check: overlay the PRE-conversion pages from
//                                                   <dir>/studio/ and run the same checks; the lock-file and
//                                                   lost-update checks are expected to FAIL there
//
// Three kinds of check:
//  1. behaviour: every converted action still produces the same images-<pid>.json / projects.json result
//  2. "took the lock": the test deletes <store>.lock before the request; s_with_lock() fopen()s it, so it
//     must exist afterwards. The old unlocked writes never create it.
//  3. lost update: php-wasm runs one request at a time, so a concurrent writer is SIMULATED at the exact
//     point where the old code sat between its read and its write: store_image() (uploads), ck_enqueue()
//     (creator.php actions) and ck_defect_log_analysis() (bridge annotate). These TEST-ONLY hooks (in memory,
//     never on disk) write the store directly, the way another request would have committed in between. In the
//     converted code each hook point runs before the lock is taken, so the simulated write must survive.
// Plus unit tests of creator.php's ck_cfg_merge3() and a static scan that no page calls images_save() /
// projects_save() any more. Nothing here reads a real secret, touches live data, or makes a network call.
// This folder must NOT be deployed to the live server.
import { createRequire } from 'module';
import { readFileSync, readdirSync } from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const require = createRequire('/Users/mattmenashe/Documents/comic-platform/tools/phptest/node_modules/x.js');
const { loadNodeRuntime } = require('@php-wasm/node');
const { PHP, PHPRequestHandler, setPhpIniEntries } = require('@php-wasm/universal');

const HERE = path.dirname(fileURLToPath(import.meta.url));
const SRC = path.resolve(HERE, '../..');                      // .../studio
const OLD = (() => { const i = process.argv.indexOf('--old'); return i > 0 ? process.argv[i + 1] : ''; })();
const SKIP_DIRS = new Set(['data', 'uploads', 'tests', 'extension', 'tools', 'worker', 'docs']);
const BKEY = 'test-bridge-key-0123456789abcdef';
const PAGES = ['api.php', 'bridge.php', 'creator.php', 'port.php', 'index.php', 'project.php', 'gribble.php', 'growgetter.php'];

const php = new PHP(await loadNodeRuntime('8.1', { emscriptenOptions: { processId: 1 } }));
const handler = new PHPRequestHandler({ php, documentRoot: '/www', absoluteUrl: 'http://localhost', cookieStore: false });
php.requestHandler = handler;
php.mkdirTree('/tmp/sess');
await setPhpIniEntries(php, { error_reporting: 'E_ALL', display_errors: '1', html_errors: '0', 'session.save_path': '/tmp/sess' });

function copyTree(srcDir, dstDir, top) {
  php.mkdirTree(dstDir);
  for (const ent of readdirSync(srcDir, { withFileTypes: true })) {
    if (/\.bak/.test(ent.name) || ent.name === '.DS_Store') continue;
    const s = path.join(srcDir, ent.name), d = dstDir + '/' + ent.name;
    if (ent.isDirectory()) { if (top && SKIP_DIRS.has(ent.name)) continue; copyTree(s, d, false); }
    else if (ent.isFile()) php.writeFile(d, readFileSync(s));
  }
}
copyTree(SRC, '/www/studio', true);
if (OLD) for (const f of PAGES) php.writeFile('/www/studio/' + f, readFileSync(path.join(OLD, 'studio', f)));
for (const d of ['/www/studio/data/ws', '/www/studio/uploads', '/www/admin/data', '/www/assets/comics']) php.mkdirTree(d);

// ---- TEST-ONLY hooks (in memory) ----------------------------------------------------------------
// lk_inject(): if /tmp/lk-inject.json exists, consume it and apply it as "another request committed now":
//   {img: {pid, row}}           append row to images-<pid>.json
//   {cfg: {pid, ref, note, run, adjustDone}}  edit creator-<pid>.json like bridge/review would
const INJ = '/tmp/lk-inject.json';
function patch(file, at, add, where = 'after') {
  let s = php.readFileAsText(file);
  if (!s.includes(at)) { console.error(`cannot patch ${file}: anchor not found: ${at}`); process.exit(2); }
  s = s.replace(at, where === 'after' ? at + add : add + at);
  php.writeFile(file, s);
}
patch('/www/studio/inc/boot.php', 'declare(strict_types=1);', `
function lk_inject(): void {
    if (!is_file('${INJ}')) return;
    $j = json_decode((string)file_get_contents('${INJ}'), true); @unlink('${INJ}');
    if (!empty($j['img'])) { $f = imeta_path($j['img']['pid']); $m = s_read($f, []); $m[] = $j['img']['row']; s_write($f, $m); }
    if (!empty($j['cfg'])) {
        $q = $j['cfg']; $f = SDATA . '/creator-' . $q['pid'] . '.json'; $c = s_read($f, []);
        if (!empty($q['ref']))  { $c['refs'][] = $q['ref']; }
        if (!empty($q['note'])) { $c['feedback'] = $c['feedback'] ?? []; array_unshift($c['feedback'], $q['note']); }
        if (!empty($q['run']))  { foreach ($q['run'] as $k => $v) $c['run'][$k] = $v; }
        if (!empty($q['adjustDone'])) foreach ($c['adjusts'] as &$a) if (($a['id'] ?? '') === $q['adjustDone']) { $a['status'] = 'done'; $a['resultFile'] = 'from-bridge.png'; }
        unset($a); s_write($f, $c);
    }
}`);
patch('/www/studio/inc/boot.php', 'function store_image(string $tmp, string $orig, string $id): ?array {', '\n    lk_inject();');
patch('/www/studio/inc/defects.php', 'function ck_defect_log_analysis(string $project, string $file, string $panel, array $an, string $src): void {', '\n    lk_inject();');
patch('/www/studio/creator.php', 'function ck_enqueue(array $job): string {', '\n    lk_inject();');
const inject = o => php.writeFile(INJ, JSON.stringify(o));

// ---- fixture ------------------------------------------------------------------------------------
async function phpOut(code) { return (await php.run({ code })).text; }
async function makePng(w, h, rgb) {
  return Buffer.from(await phpOut(`<?php $im = imagecreatetruecolor(${w}, ${h}); imagefill($im, 0, 0, imagecolorallocate($im, ${rgb.join(',')})); ob_start(); imagepng($im); echo base64_encode(ob_get_clean());`), 'base64');
}
const pwHash = await phpOut('<?php echo password_hash("pw", PASSWORD_DEFAULT);');
const D = '/www/studio/data';
php.writeFile('/www/admin/data/users.json', JSON.stringify([{ username: 'grow', name: 'Grow', role: 'owner', hash: pwHash }]));
php.writeFile('/www/studio/data/users-studio.json', '[]');
php.writeFile(D + '/bridge.json', JSON.stringify({ key: BKEY }));
php.writeFile('/www/admin/data/content.json', JSON.stringify({ series: [] }));
const proj = (id, name) => ({ id, name, status: 'active', stage: 'page-build', tags: [], notes: '', cover: null, created: '2026-09-01', updated: '2026-09-01' });
php.writeFile(D + '/projects.json', JSON.stringify([proj('lk-a', 'Lock A'), proj('lk-b', 'Lock B'), proj('lk-c', 'Lock C')]));
const PNG = await makePng(60, 80, [200, 60, 60]);
const T0 = Math.floor(Date.now() / 1000) - 3600;
const row = (file, group, extra = {}) => Object.assign({ file, orig: file, rating: 'unrated', accepted: false, group, tags: [], ts: T0, gen: '', genkey: '' }, extra);
function seedImages(pid, rows) {
  php.mkdirTree(`/www/studio/uploads/${pid}/thumb`);
  rows.forEach((r, i) => { r.ts = T0 + i; php.writeFile(`/www/studio/uploads/${pid}/${r.file}`, PNG); php.writeFile(`/www/studio/uploads/${pid}/thumb/${r.file}`, PNG); });
  php.writeFile(`${D}/images-${pid}.json`, JSON.stringify(rows));
}
const freshA = () => seedImages('lk-a', [
  row('a1.png', 'Beat 1'), row('a2.png', 'Beat 1', { rating: 'good' }), row('a3.png', 'Beat 2', { accepted: true }),
  row('a4.png', 'Beat 2', { rating: 'bad' }), row('a5.png', 'Beat 3', { genkey: 'p:k5' }), row('ref.png', '', { isref: true, rating: 'good' }),
]);
freshA();
seedImages('lk-b', [row('b1.png', 'Beat 1', { accepted: true, rating: 'good' }), row('b2.png', 'Beat 2')]);
seedImages('lk-c', [row('c1.png', 'Beat 1', { genkey: 'p:aaa' }), row('c2.png', 'Beat 2', { genkey: 'p:bbb' })]);

// ---- helpers ------------------------------------------------------------------------------------
let pass = 0, fail = 0; const failures = [], diag = [];
function check(name, cond, extra) {
  if (cond) { pass++; console.log('PASS ' + name); return true; }
  fail++; failures.push(name);
  let s = extra === undefined ? '' : (typeof extra === 'string' ? extra : JSON.stringify(extra));
  if (s.length > 600) s = s.slice(0, 600) + '…';
  console.log('FAIL ' + name + (s ? '\n     ' + s : ''));
  return false;
}
const section = t => console.log('\n== ' + t);
const WARN_RE = /\b(Warning|Notice|Deprecated|Fatal error|Parse error|Uncaught)\b[^\n]{0,300}? on line \d+/;
class Client {
  constructor(name) { this.name = name; this.sid = null; }
  async req(method, url, { body, headers } = {}) {
    const h = Object.assign({}, headers || {});
    if (this.sid) h.cookie = 'mgstudio=' + this.sid;
    const res = await handler.request({ method, url, headers: h, body });
    for (const c of (res.headers['set-cookie'] || [])) { const m = /^mgstudio=([^;]*)/.exec(c); if (m) this.sid = m[1] || null; }
    let text = ''; try { text = res.text; } catch { text = ''; }
    let json = null; try { json = JSON.parse(text); } catch { /* not JSON */ }
    const m = WARN_RE.exec(text); if (m) diag.push(`${method} ${url} :: ${m[0]}`);
    if (res.errors && res.errors.trim()) diag.push(`${method} ${url} :: stderr ${res.errors.trim().slice(0, 300)}`);
    return { status: res.httpStatusCode, text, json, loc: (res.headers.location || [])[0] || '' };
  }
  get(url) { return this.req('GET', url); }
  post(url, body) { return this.req('POST', url, { body }); }
}
const readJson = f => { try { return JSON.parse(php.readFileAsText(f)); } catch { return null; } };
const exists = f => { try { return php.fileExists(f); } catch { return false; } };
const unlock = f => { try { php.unlink(f + '.lock'); } catch { /* none */ } };
const IMG = pid => `${D}/images-${pid}.json`, PROJ = D + '/projects.json', CFG = pid => `${D}/creator-${pid}.json`;
const files = pid => (readJson(IMG(pid)) || []).map(m => m.file);
const byFile = (pid, f) => (readJson(IMG(pid)) || []).find(m => m.file === f);
const projRow = id => (readJson(PROJ) || []).find(p => p.id === id);
const short = r => ({ status: r.status, loc: r.loc, body: (r.text || '').slice(0, 300) });
// run a request with the given store lock files removed first; returns [response, {store: lockExistsAfter}]
async function locked(stores, fn) { for (const s of stores) unlock(s); const r = await fn(); return [r, Object.fromEntries(stores.map(s => [s, exists(s + '.lock')]))]; }
const allLocked = l => Object.values(l).every(Boolean);

const owner = new Client('owner');
let r, l;
r = await owner.post('/studio/login.php', { username: 'grow', password: 'pw' });
check('owner login', r.status === 302 && !!owner.sid, short(r));
r = await owner.get('/studio/project.php?p=lk-a');
const CSRF = (/name="csrf" value="([a-f0-9]+)"/.exec(r.text) || [])[1] || '';
check('csrf token from project.php', CSRF.length === 32, short(r));
const api = (body, stores = [IMG('lk-a')]) => locked(stores, () => owner.post('/studio/api.php', Object.assign({ csrf: CSRF, p: 'lk-a' }, body)));
const bridge = (body, stores) => locked(stores, () => owner.post('/studio/bridge.php', Object.assign({ key: BKEY }, body)));
const mp = (fields, fileField, names) => {                       // multipart body with PNG parts
  const fd = new FormData();
  for (const [k, v] of Object.entries(fields)) fd.append(k, v);
  for (const n of names) fd.append(fileField, new Blob([PNG], { type: 'image/png' }), n);
  return fd;
};
const mpPost = async (client, url, fd) => {
  const req = new Request('http://localhost' + url, { method: 'POST', body: fd });
  const body = new Uint8Array(await req.arrayBuffer());
  return client.req('POST', url, { body, headers: { 'content-type': req.headers.get('content-type') } });
};

// =================================================================================================
section('STATIC: no legacy page calls images_save() / projects_save()');
{
  const hits = [];
  for (const f of readdirSync(SRC)) if (f.endsWith('.php')) {
    const src = readFileSync(path.join(OLD && PAGES.includes(f) ? path.join(OLD, 'studio') : SRC, f), 'utf8');
    src.split('\n').forEach((ln, i) => { if (/\b(images_save|projects_save)\s*\(/.test(ln)) hits.push(`${f}:${i + 1}`); });
  }
  check('no images_save( / projects_save( outside inc/boot.php', hits.length === 0, hits.join(' '));
}

// =================================================================================================
section('MERGE: creator.php ck_cfg_merge3() (unit)');
{
  const src = php.readFileAsText('/www/studio/creator.php');
  const a = src.indexOf('const CK_CFG_NONE'), b = src.indexOf('function creator_list()');
  if (a < 0 || b < 0) check('ck_cfg_merge3 present in creator.php', false, 'not found');
  else {
    const cases = {
      untouched:   [{ x: 1, y: 1 }, { x: 2, y: 1 }, { x: 1, y: 9 }],                                    // -> {x:2,y:9}
      runFields:   [{ run: { state: 'running', backend: 'flow' } }, { run: { state: 'queued', backend: 'flow', jobId: 'j2' } }, { run: { state: 'done', backend: 'flow', endedAt: 'T' } }],
      refsBoth:    [{ refs: [{ id: 'r1', file: 'a' }] }, { refs: [{ id: 'r1', file: 'a' }, { id: 'r2', file: 'b' }] }, { refs: [{ id: 'r1', file: 'a' }, { id: 'r3', file: 'c' }] }],
      refsDelEdit: [{ refs: [{ id: 'r1', k: 'v' }, { id: 'r2', k: 'v' }] }, { refs: [{ id: 'r2', k: 'v' }] }, { refs: [{ id: 'r1', k: 'v' }, { id: 'r2', k: 'w' }] }],
      rowFields:   [{ adjusts: [{ id: 'a1', status: 'pending', note: 'n' }] }, { adjusts: [{ id: 'a1', status: 'pending', note: 'n2' }] }, { adjusts: [{ id: 'a1', status: 'done', note: 'n', resultFile: 'f' }] }],
      feedback:    [{ feedback: [{ t: 'old' }] }, { feedback: [{ t: 'mine' }, { t: 'old' }] }, { feedback: [{ t: 'review' }, { t: 'old' }] }],
      feedbackNew: [{}, { feedback: [{ t: 'mine' }] }, { feedback: [{ t: 'review' }] }],
      polishTwo:   [{ plan: [{ stage: '', panels: [{ id: 'p1-1', beat: 'x' }, { id: 'p1-2', beat: 'y' }] }] },
                    { plan: [{ stage: '', panels: [{ id: 'p1-1', beat: 'x', polished: 'P1' }, { id: 'p1-2', beat: 'y' }] }] },
                    { plan: [{ stage: '', panels: [{ id: 'p1-1', beat: 'x' }, { id: 'p1-2', beat: 'y', polished: 'P2' }] }] }],
      restructure: [{ plan: [{ stage: '', panels: [{ id: 'p1-1', beat: 'x' }] }] },
                    { plan: [{ stage: '', panels: [{ id: 'p1-1', beat: 'x', polished: 'P1' }] }] },
                    { plan: [{ stage: 'pre', panels: [{ id: 'p1-1', beat: 'x2' }, { id: 'p1-2', beat: 'z' }] }, { stage: 'post', panels: [{ id: 'p2-1', beat: 'w' }] }] }],
      breakdown:   [{ plan: [{ stage: '', panels: [{ id: 'p1-1', beat: 'x' }] }] },
                    { plan: [{ stage: '', panels: [{ id: 'q1', beat: 'n1' }] }, { stage: '', panels: [{ id: 'q2', beat: 'n2' }] }] },
                    { plan: [{ stage: '', panels: [{ id: 'p1-1', beat: 'x', polished: 'old' }] }] }],
      unsetKey:    [{ plan: [{ panels: [{ id: 'p1', polished: 'X' }] }], brief: 'b' }, { plan: [{ panels: [{ id: 'p1' }] }], brief: 'b' }, { plan: [{ panels: [{ id: 'p1', polished: 'X' }] }], brief: 'b2' }],
      unlock:      [{ refsLocked: true, refsLockedSet: ['a', 'b'] }, { refsLocked: false, refsLockedSet: [] }, { refsLocked: true, refsLockedSet: ['a', 'b', 'c'] }],
      conflict:    [{ brief: 'a' }, { brief: 'mine' }, { brief: 'theirs' }],
      lazyCreate:  [{}, { projectId: 'x', refs: [], plan: [], run: { state: 'idle' } }, {}],
      newAdjusts:  [{ name: 'n' }, { name: 'n', adjusts: [] }, { name: 'n', adjusts: [{ id: 'a9', status: 'done' }] }],
    };
    const code = '<?php ' + src.slice(a, b) + `\n$cases = json_decode(${JSON.stringify(JSON.stringify(cases))}, true); $out = [];
foreach ($cases as $k => [$b, $m, $t]) $out[$k] = ck_cfg_merge3($b, $m, $t);
echo json_encode($out);`;
    const res = await php.run({ code });
    let o = null; try { o = JSON.parse(res.text); } catch { /* */ }
    if (!check('merge unit code runs', !!o, res.text.slice(0, 400) + (res.errors || ''))) o = {};
    const eq = (x, y) => JSON.stringify(x) === JSON.stringify(y);
    check('merge: fields this request did not touch keep the current value', eq(o.untouched, { x: 2, y: 9 }), o.untouched);
    check('merge: run.* merges per field (mine state wins, their endedAt kept, my jobId added)', eq(o.runFields, { run: { state: 'queued', backend: 'flow', endedAt: 'T', jobId: 'j2' } }), o.runFields);
    check('merge: refs added on both sides are both kept', eq(o.refsBoth, { refs: [{ id: 'r1', file: 'a' }, { id: 'r3', file: 'c' }, { id: 'r2', file: 'b' }] }), o.refsBoth);
    check('merge: a ref removed here stays removed; their edit to another ref survives', eq(o.refsDelEdit, { refs: [{ id: 'r2', k: 'w' }] }), o.refsDelEdit);
    check('merge: one adjust row edited on both sides merges field by field', eq(o.rowFields, { adjusts: [{ id: 'a1', status: 'done', note: 'n2', resultFile: 'f' }] }), o.rowFields);
    check('merge: feedback notes from both sides kept, mine first', eq(o.feedback, { feedback: [{ t: 'mine' }, { t: 'review' }, { t: 'old' }] }), o.feedback);
    check('merge: first-ever feedback note on both sides: both kept', eq(o.feedbackNew, { feedback: [{ t: 'mine' }, { t: 'review' }] }), o.feedbackNew);
    check('merge: two concurrent polishes of different panels both land', eq(o.polishTwo, { plan: [{ stage: '', panels: [{ id: 'p1-1', beat: 'x', polished: 'P1' }, { id: 'p1-2', beat: 'y', polished: 'P2' }] }] }), o.polishTwo);
    check('merge: a polish on top of a concurrently restructured plan keeps the new plan + the polish', eq(o.restructure, { plan: [{ stage: 'pre', panels: [{ id: 'p1-1', beat: 'x2', polished: 'P1' }, { id: 'p1-2', beat: 'z' }] }, { stage: 'post', panels: [{ id: 'p2-1', beat: 'w' }] }] }), o.restructure);
    check('merge: a fresh breakdown (new shape) replaces the plan', eq(o.breakdown, { plan: [{ stage: '', panels: [{ id: 'q1', beat: 'n1' }] }, { stage: '', panels: [{ id: 'q2', beat: 'n2' }] }] }), o.breakdown);
    check('merge: a key unset here is removed; their brief edit survives', eq(o.unsetKey, { plan: [{ panels: [{ id: 'p1' }] }], brief: 'b2' }), o.unsetKey);
    check('merge: unlocking refs clears the locked set even if a ref was added to it meanwhile', eq(o.unlock, { refsLocked: false, refsLockedSet: [] }), o.unlock);
    check('merge: same value changed on both sides -> this request wins', eq(o.conflict, { brief: 'mine' }), o.conflict);
    check('merge: missing file -> the defaults are written (lazy create)', eq(o.lazyCreate, { projectId: 'x', refs: [], plan: [], run: { state: 'idle' } }), o.lazyCreate);
    check('merge: an empty list added here does not wipe rows added meanwhile', eq(o.newAdjusts, { name: 'n', adjusts: [{ id: 'a9', status: 'done' }] }), o.newAdjusts);
  }
}

// =================================================================================================
section('api.php: per-image actions');
[r, l] = await api({ action: 'rate', file: 'a1.png', rating: 'bad' });
check('rate -> stored, images lock taken', r.json?.ok && byFile('lk-a', 'a1.png').rating === 'bad' && allLocked(l), [short(r), l]);
[r, l] = await api({ action: 'keep', file: 'a1.png', accepted: '1' });
check('keep -> stored, images lock taken', r.json?.accepted === true && byFile('lk-a', 'a1.png').accepted === true && allLocked(l), [short(r), l]);
[r, l] = await api({ action: 'group', file: 'a1.png', group: 'Beat 9' });
check('group -> stored, images lock taken', r.json?.ok && byFile('lk-a', 'a1.png').group === 'Beat 9' && allLocked(l), [short(r), l]);
[r, l] = await api({ action: 'group', file: 'a1.png', group: 'Beat 1' });
[r, l] = await api({ action: 'winner', file: 'a1.png' }, [IMG('lk-a'), PROJ]);
check('winner -> a1 accepted+good, a2 loses good; cover set (empty before); both locks taken',
  r.json?.ok && byFile('lk-a', 'a1.png').accepted && byFile('lk-a', 'a1.png').rating === 'good' && byFile('lk-a', 'a2.png').rating === 'unrated'
  && !byFile('lk-a', 'a2.png').accepted && projRow('lk-a').cover === 'a1.png' && allLocked(l), [short(r), l, projRow('lk-a')]);
[r, l] = await api({ action: 'cover', file: 'a3.png' }, [PROJ]);
check('cover -> projects.json cover, projects lock taken', r.json?.ok && projRow('lk-a').cover === 'a3.png' && allLocked(l), [short(r), l]);
[r] = await api({ action: 'rate', file: 'nope.png', rating: 'good' });
check('unknown image -> Image not found, nothing written', r.json?.ok === false && /not found/i.test(r.json?.error || ''), short(r));
[r, l] = await api({ action: 'delete', file: 'a3.png' }, [IMG('lk-a'), PROJ]);
check('delete -> row + files gone, cover cleared, both locks taken',
  r.json?.ok && r.json.count === 5 && !files('lk-a').includes('a3.png') && !exists('/www/studio/uploads/lk-a/a3.png') && projRow('lk-a').cover === null && allLocked(l), [short(r), l]);

section('api.php: whole-gallery actions');
freshA();
[r, l] = await api({ action: 'move_beat', beat: 'Beat 3', to: '1' }, [IMG('lk-a'), PROJ]);
check('move_beat -> Beat 3 becomes Beat 1, others shift; updated stamped; both locks taken',
  r.json?.ok && byFile('lk-a', 'a5.png').group === 'Beat 1' && byFile('lk-a', 'a1.png').group === 'Beat 2' && byFile('lk-a', 'a3.png').group === 'Beat 3'
  && projRow('lk-a').updated !== '2026-09-01' && allLocked(l), [short(r), l]);
[r] = await api({ action: 'move_beat', beat: 'Beat 77', to: '1' });
check('move_beat unknown beat -> error', r.json?.ok === false, short(r));
freshA();
[r, l] = await api({ action: 'bulk', op: 'approve', files: JSON.stringify(['a1.png', 'a4.png']) }, [IMG('lk-a'), PROJ]);
check('bulk approve -> 2 updated, both locks taken', r.json?.updated === 2 && byFile('lk-a', 'a4.png').accepted && byFile('lk-a', 'a4.png').rating === 'good' && allLocked(l), [short(r), l]);
await api({ action: 'cover', file: 'a4.png' });
[r, l] = await api({ action: 'bulk', op: 'delete', files: JSON.stringify(['a4.png', 'a5.png']) }, [IMG('lk-a'), PROJ]);
check('bulk delete -> 2 deleted, files gone, cover (a4) cleared, both locks taken',
  r.json?.deleted === 2 && r.json.count === 4 && !files('lk-a').includes('a5.png') && !exists('/www/studio/uploads/lk-a/a4.png') && projRow('lk-a').cover === null && allLocked(l), [short(r), l]);
freshA();
await api({ action: 'cover', file: 'a2.png' });
[r, l] = await api({ action: 'purge' }, [IMG('lk-a'), PROJ]);
check('purge -> keeps good/kept only (a2, a3, ref), deletes 3, cover a2 kept',
  r.json?.deleted === 3 && r.json.kept === 3 && files('lk-a').join() === 'a2.png,a3.png,ref.png' && projRow('lk-a').cover === 'a2.png' && allLocked(l), [short(r), l, files('lk-a')]);
freshA();
[r, l] = await api({ action: 'one_beat_each' }, [IMG('lk-a'), PROJ]);
check('one_beat_each -> every image its own kept beat', r.json?.ok && (readJson(IMG('lk-a')) || []).every((m, i) => m.group === 'Beat ' + (i + 1) && m.accepted) && allLocked(l), [short(r), l]);
freshA();
{
  const m = readJson(IMG('lk-a')); m[0].genkey = 'p:same'; m[1].genkey = 'p:same'; m[4].genkey = 'p:other'; php.writeFile(IMG('lk-a'), JSON.stringify(m));
}
[r, l] = await api({ action: 'group_similar' }, [IMG('lk-a'), PROJ]);
check('group_similar -> same genkey = same beat; both locks taken',
  r.json?.ok && byFile('lk-a', 'a1.png').group === byFile('lk-a', 'a2.png').group && byFile('lk-a', 'a1.png').group !== byFile('lk-a', 'a5.png').group && allLocked(l), [short(r), l, readJson(IMG('lk-a')).map(m => m.group)]);

section('api.php: upload keeps a write that lands while the files are processed');
freshA();
inject({ img: { pid: 'lk-a', row: row('concurrent.png', 'Page 01') } });
for (const s of [IMG('lk-a'), PROJ]) unlock(s);
r = await mpPost(owner, '/studio/api.php', mp({ csrf: CSRF, p: 'lk-a', action: 'upload' }, 'files[]', ['up1.png', 'up2.png']));
check('upload -> 2 added', r.json?.ok && r.json.added?.length === 2, short(r));
check('upload: the concurrent row written during store_image survives (lost update fixed)', files('lk-a').includes('concurrent.png'), files('lk-a'));
check('upload: count reports the merged gallery (6 + 1 concurrent + 2)', r.json?.count === 9, r.json);
check('upload: images + projects locks taken', exists(IMG('lk-a') + '.lock') && exists(PROJ + '.lock'));

// =================================================================================================
section('bridge.php');
[r, l] = await bridge({ do: 'write', p: 'lk-b', decisions: JSON.stringify([{ file: 'b2.png', rating: 'good', accepted: true, addtags: ['flow-fav'] }]), cover: 'b2.png' }, [IMG('lk-b'), PROJ]);
check('write -> rating/accept/tag + cover; both locks taken', r.json?.updated === 1 && byFile('lk-b', 'b2.png').tags.includes('flow-fav') && projRow('lk-b').cover === 'b2.png' && allLocked(l), [short(r), l]);
[r, l] = await bridge({ do: 'enrich', p: 'lk-b', items: JSON.stringify([{ file: 'b1.png', prompt: 'a prompt' }]) }, [IMG('lk-b')]);
check('enrich -> fills the missing prompt; lock taken', r.json?.enriched === 1 && byFile('lk-b', 'b1.png').prompt === 'a prompt' && allLocked(l), [short(r), l]);
[r, l] = await bridge({ do: 'enrich', p: 'lk-b', items: JSON.stringify([{ file: 'b1.png', prompt: 'other' }]) }, [IMG('lk-b')]);
check('enrich no-clobber -> 0 enriched, prompt kept', r.json?.enriched === 0 && byFile('lk-b', 'b1.png').prompt === 'a prompt', short(r));
inject({ img: { pid: 'lk-b', row: row('during-annotate.png', 'Beat 5') } });
[r, l] = await bridge({ do: 'annotate', p: 'lk-b', notes: JSON.stringify([{ file: 'b1.png', caption: 'cap', defects: ['DUP'], verdict: 'fail', src: 'qa' }]) }, [IMG('lk-b')]);
check('annotate -> analysis stored; lock taken', r.json?.annotated === 1 && byFile('lk-b', 'b1.png').analysis?.verdict === 'fail' && allLocked(l), [short(r), l]);
check('annotate: a write landing during the defect-log step survives (lost update fixed)', files('lk-b').includes('during-annotate.png'), files('lk-b'));
[r, l] = await bridge({ do: 'ingest_init', project: 'Lock A' }, [PROJ]);
check('ingest_init existing name -> resolves lk-a; nothing added', r.json?.project === 'lk-a' && (readJson(PROJ) || []).length === 3, short(r));
[r, l] = await bridge({ do: 'ingest_init', project: 'Lock A', new: '1' }, [PROJ]);
check('ingest_init new=1 -> fresh unique id, row added, lock taken', /^lock-a(-\d+)?$/.test(r.json?.project || '') && r.json.project !== 'lk-a' && !!projRow(r.json.project) && allLocked(l), [short(r), l]);
const NEWP = r.json?.project;
[r, l] = await bridge({ do: 'ingest_init', project: 'Lock A', new: '1' }, [PROJ]);
check('ingest_init new=1 again -> a different id, both rows kept', r.json?.project && r.json.project !== NEWP && !!projRow(NEWP) && !!projRow(r.json.project), short(r));
{
  const fd = mp({ key: BKEY, do: 'ingest', p: 'lk-c', prompt: 'brand new prompt' }, 'file', ['in1.png']);
  for (const s of [IMG('lk-c')]) unlock(s);
  r = await mpPost(owner, '/studio/bridge.php', fd);
  check('ingest new prompt -> auto-group Beat 3 (max+1); lock taken', r.json?.ok && r.json.group === 'Beat 3' && r.json.count === 3 && exists(IMG('lk-c') + '.lock'), short(r));
  const f1 = (readJson(IMG('lk-c')) || []).at(-1)?.file;
  r = await mpPost(owner, '/studio/bridge.php', mp({ key: BKEY, do: 'ingest', p: 'lk-c', prompt: 'brand new prompt' }, 'file', ['in2.png']));
  check('ingest same prompt -> joins Beat 3', r.json?.group === 'Beat 3' && r.json.count === 4, short(r));
  r = await mpPost(owner, '/studio/bridge.php', mp({ key: BKEY, do: 'ingest', p: 'lk-c', parent: 'c1.png', adjust: 'bigger' }, 'file', ['in3.png']));
  const d = (readJson(IMG('lk-c')) || []).at(-1);
  check('ingest with parent -> derived v2 in the parent beat, parent genkey inherited', r.json?.group === 'Beat 1' && d.parent === 'c1.png' && d.ver === 2 && d.derived && d.genkey === 'p:aaa' && d.adjust === 'bigger', [short(r), d]);
  check('ingest: earlier ingest row still present', !!f1 && files('lk-c').includes(f1));
}
{
  inject({ img: { pid: 'lk-c', row: row('during-refcache.png', '') } });
  unlock(IMG('lk-c'));
  r = await mpPost(owner, '/studio/bridge.php', mp({ key: BKEY, do: 'ingest_refcache', p: 'lk-c', refkey: 'rk1' }, 'file', ['ref.png']));
  check('ingest_refcache -> cached=false, isref row with refkey; lock taken', r.json?.ok && r.json.cached === false && byFile('lk-c', r.json.file)?.refkey === 'rk1' && exists(IMG('lk-c') + '.lock'), short(r));
  check('ingest_refcache: a write landing during store_image survives (lost update fixed)', files('lk-c').includes('during-refcache.png'), files('lk-c'));
  r = await mpPost(owner, '/studio/bridge.php', mp({ key: BKEY, do: 'ingest_refcache', p: 'lk-c', refkey: 'rk1' }, 'file', ['ref.png']));
  check('ingest_refcache same refkey -> cached=true', r.json?.cached === true, short(r));
  unlock(IMG('lk-c'));
  r = await mpPost(owner, '/studio/bridge.php', mp({ key: BKEY, do: 'ingest_ref', p: 'lk-c', kind: 'scene', char: 'Gym', status: 'approved' }, 'file', ['plate.png']));
  check('ingest_ref -> isref gallery row + creator refs entry; images lock taken',
    r.json?.ok && byFile('lk-c', r.json.file)?.isref && (readJson(CFG('lk-c'))?.refs || []).some(x => x.file === r.json.file) && exists(IMG('lk-c') + '.lock'), short(r));
}

// =================================================================================================
section('creator.php: images writes');
{
  const cr = (body) => owner.post('/studio/creator.php?p=lk-b', Object.assign({ csrf: CSRF }, body));
  inject({ img: { pid: 'lk-b', row: row('during-uploadref.png', 'Beat 7') } });
  unlock(IMG('lk-b')); unlock(CFG('lk-b'));
  r = await mpPost(owner, '/studio/creator.php?p=lk-b', mp({ csrf: CSRF, do: 'uploadref', kind: 'face', char: 'Ana' }, 'reffile[]', ['s1.png', 's2.png']));
  const c = readJson(CFG('lk-b')) || {};
  const refFiles = (c.refs || []).map(x => x.file);
  check('uploadref -> 302, 2 refs + 2 isref gallery rows; images + creator locks taken',
    r.status === 302 && refFiles.length === 2 && refFiles.every(f => byFile('lk-b', f)?.isref) && exists(IMG('lk-b') + '.lock') && exists(CFG('lk-b') + '.lock'), [short(r), refFiles]);
  check('uploadref: a write landing during store_image survives (lost update fixed)', files('lk-b').includes('during-uploadref.png'), files('lk-b'));
  const rid = (c.refs || [])[0]?.id, rfile = (c.refs || [])[0]?.file;
  unlock(IMG('lk-b'));
  r = await cr({ do: 'removeref', rid });
  check('removeref -> ref + its gallery row + file gone; images lock taken', r.status === 302 && !files('lk-b').includes(rfile) && !(readJson(CFG('lk-b'))?.refs || []).some(x => x.id === rid)
    && !exists(`/www/studio/uploads/lk-b/${rfile}`) && exists(IMG('lk-b') + '.lock'), [short(r), files('lk-b')]);
}

section('creator.php: creator-<id>.json commit keeps concurrent writes');
{
  const cr = (body) => owner.post('/studio/creator.php?p=lk-b', Object.assign({ csrf: CSRF }, body));
  r = await cr({ do: 'brief', brief: 'the brief' });
  check('brief -> saved', r.status === 302 && readJson(CFG('lk-b'))?.brief === 'the brief', short(r));
  // a reshoot note: feedback prepend + ck_enqueue(); "bridge/review" commit while it runs
  inject({ cfg: { pid: 'lk-b', ref: { id: 'bridge-ref', file: 'plate-x.png', kind: 'scene', status: 'approved' }, note: { ts: 'T', by: 'review', panel: 'Beat 1', text: 'from review' }, run: { endedAt: 'E1', state: 'done' } } });
  unlock(CFG('lk-b'));
  r = await cr({ do: 'feedback', text: 'reshoot this', panel: 'Beat 2' });
  let c = readJson(CFG('lk-b')) || {};
  check('feedback -> 302, my note first', r.status === 302 && c.feedback?.[0]?.text === 'reshoot this', [short(r), c.feedback]);
  check('feedback: the review note committed meanwhile survives', (c.feedback || []).some(f => f.text === 'from review'), c.feedback);
  check('feedback: the ref ingest_ref added meanwhile survives', (c.refs || []).some(x => x.id === 'bridge-ref'), c.refs);
  check('feedback: run.state = queued (mine), run.endedAt from the worker kept, brief kept',
    c.run?.state === 'queued' && c.run?.endedAt === 'E1' && c.brief === 'the brief' && exists(CFG('lk-b') + '.lock'), [c.run, c.brief]);
  // adjust: a new pending adjust (mine) while the bridge flips an older one to done (theirs)
  c.adjusts = [{ id: 'adj_old', parentFile: 'b1.png', root: 'b1.png', ver: 2, beat: 'Beat 1', note: 'n', status: 'pending', jobId: '', ts: 1 }];
  php.writeFile(CFG('lk-b'), JSON.stringify(c));
  inject({ cfg: { pid: 'lk-b', adjustDone: 'adj_old' } });
  r = await cr({ do: 'adjust', file: 'b1.png', note: 'make it bigger' });
  c = readJson(CFG('lk-b')) || {};
  const old = (c.adjusts || []).find(a => a.id === 'adj_old'), mine = (c.adjusts || []).find(a => a.id === r.json?.adjustId);
  check('adjust -> JSON ok, new pending adjust stored', r.json?.ok && mine?.status === 'pending', [short(r), c.adjusts]);
  check('adjust: the older adjust the bridge resolved meanwhile stays done', old?.status === 'done' && old?.resultFile === 'from-bridge.png', old);
  // gallery-only project: first cockpit POST lazily creates the config with its defaults
  try { php.unlink(CFG('lk-a')); } catch { /* none */ }
  r = await owner.post('/studio/creator.php?p=lk-a', { csrf: CSRF, do: 'style', style: 'CGI' });
  c = readJson(CFG('lk-a')) || {};
  check('first POST on a gallery-only project creates the config (defaults + style)', r.status === 302 && c.projectId === 'lk-a' && c.style === 'CGI' && Array.isArray(c.refs) && c.run?.state === 'idle', c);
}

section('creator.php: adjustresult');
{
  let c = readJson(CFG('lk-b')) || {};
  const pend = (c.adjusts || []).find(a => a.status === 'pending');
  inject({ img: { pid: 'lk-b', row: row('during-adjustresult.png', 'Beat 8') } });
  unlock(IMG('lk-b'));
  r = await mpPost(owner, '/studio/creator.php?p=lk-b', mp({ csrf: CSRF, do: 'adjustresult', adjustId: pend?.id || '' }, 'resultfile', ['v3.png']));
  c = readJson(CFG('lk-b')) || {};
  const done = (c.adjusts || []).find(a => a.id === pend?.id);
  const res = done?.resultFile && byFile('lk-b', done.resultFile);
  check('adjustresult -> derived row under the parent beat; adjust done; images lock taken',
    r.status === 302 && done?.status === 'done' && res?.parent === 'b1.png' && res?.derived && res?.group === 'Beat 1' && exists(IMG('lk-b') + '.lock'), [short(r), done, res]);
  check('adjustresult: a write landing during store_image survives (lost update fixed)', files('lk-b').includes('during-adjustresult.png'), files('lk-b'));
}

// =================================================================================================
section('port.php');
{
  freshA();
  unlock(IMG('lk-a'));
  r = await owner.post('/studio/port.php', { csrf: CSRF, do: 'port', p: 'lk-a', only: 'approved', series: '__new__', new_title: 'Lock Series', part: '__new__' });
  const stamped = (readJson(IMG('lk-a')) || []).filter(m => m.ported_to).map(m => m.file);
  check('port approved -> only the approved image stamped ported_to; lock taken',
    r.status === 302 && /done=/.test(r.loc) && stamped.join() === 'a3.png' && byFile('lk-a', 'a3.png').ported_to === 'lock-series/part-01' && exists(IMG('lk-a') + '.lock'), [short(r), stamped]);
}

// =================================================================================================
section('projects.json writers: index.php, project.php, gribble.php, growgetter.php');
{
  unlock(PROJ);
  r = await owner.post('/studio/index.php', { csrf: CSRF, do: 'create', name: 'Lock A' });
  check('index.php create -> unique id (lock-a taken by ingest_init), 302, lock taken', r.status === 302 && /project\.php\?p=lock-a-\d+/.test(r.loc) && exists(PROJ + '.lock'), short(r));
  const before = (readJson(PROJ) || []).length;
  unlock(PROJ);
  r = await owner.post('/studio/project.php?p=lk-c', { csrf: CSRF, do: 'save_meta', name: 'Lock C renamed', status: 'on-hold', stage: 'review', tags: 'x, y', notes: 'n' });
  const pc = projRow('lk-c');
  check('project.php save_meta -> fields saved, other rows kept, lock taken', r.status === 302 && pc?.name === 'Lock C renamed' && pc.status === 'on-hold' && pc.tags.join() === 'x,y'
    && (readJson(PROJ) || []).length === before && exists(PROJ + '.lock'), [short(r), pc]);
  r = await owner.post('/studio/project.php?p=lk-c', { csrf: CSRF, do: 'delete_project' });
  check('project.php delete_project -> row + images file gone, others kept', r.status === 302 && !projRow('lk-c') && !exists(IMG('lk-c')) && (readJson(PROJ) || []).length === before - 1, short(r));
  unlock(PROJ);
  r = await owner.post('/studio/growgetter.php', { key: BKEY, do: 'gg_create', premise: JSON.stringify({ title: 'Lock B', script: 'Page 1. A thing happens.', cast: [{ name: 'Ana' }] }) });
  check('growgetter gg_create -> unique id, row + config, lock taken', r.json?.ok && /^lock-b(-\d+)?$/.test(r.json.pid) && projRow(r.json.pid)?.tags?.includes('growgetter')
    && readJson(CFG(r.json.pid))?.autoApprove === true && exists(PROJ + '.lock'), short(r));
  unlock(PROJ);
  r = await owner.post('/studio/gribble.php', { key: BKEY, do: 'gr_create', title: 'Lock B', script: 'Page 1\nPanel 1- A gym. She flexes.\n', sfw: '1' });
  check('gribble gr_create -> another unique id, row added, lock taken', r.json?.ok && /^lock-b-\d+$/.test(r.json.pid) && projRow(r.json.pid)?.tags?.includes('gribble') && exists(PROJ + '.lock'), short(r));
}

section('PHP warnings / notices');
check('no PHP warnings, notices or fatals in any response', diag.length === 0, diag.slice(0, 20).join('\n     '));

console.log(`\n${pass} passed, ${fail} failed` + (OLD ? `  (--old ${OLD})` : '') + (fail ? '\nFailed:\n  - ' + failures.join('\n  - ') : ''));
process.exit(fail ? 1 : 0);
