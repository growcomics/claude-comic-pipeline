#!/usr/bin/env node
// studio/tests/ws/run.mjs: PHP-wasm 8.1 request tests for the Lieutenant workspace (2026-10-01).
//
//   node studio/tests/ws/run.mjs            PASS/FAIL per assertion + summary; exit 1 on any failure
//   node studio/tests/ws/run.mjs --verbose  also print the response snippet of every failure in full
//
// What it does: copies the studio CODE (never data/ or uploads/) from this worktree into a virtual
// filesystem at /www/studio, builds a throwaway fixture (fake admin users with password "pw", 3
// projects in 2 brands, small images-<pid>.json files with real PNGs made by GD, a test worker key),
// then drives real requests through @php-wasm's PHPRequestHandler. SCRIPT_NAME / SCRIPT_FILENAME
// are set by the handler exactly like a web server, so the gate's realpath check runs for real.
// Every identity (owner, lieutenant, collab, editor) has its own cookie jar.
//
// Nothing here reads a real secret, touches live data, or makes a network call. The only patches
// are TEST-ONLY and in memory: ws-worker.php learns a fake CDN host (fake-test.cloudfront.net) that
// "downloads" a fixture PNG, so the ingest success path can run without the network.
//
// Needs the php-wasm packages already installed at comic-platform/tools/phptest/node_modules.
// This folder must NOT be deployed to the live server.
import { createRequire } from 'module';
import { readFileSync, readdirSync } from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { createHash, createHmac } from 'crypto';

const require = createRequire('/Users/mattmenashe/Documents/comic-platform/tools/phptest/node_modules/x.js');
const { loadNodeRuntime } = require('@php-wasm/node');
const { PHP, PHPRequestHandler, setPhpIniEntries } = require('@php-wasm/universal');

const VERBOSE = process.argv.includes('--verbose');
const HERE = path.dirname(fileURLToPath(import.meta.url));
const SRC = path.resolve(HERE, '../..');                      // .../studio
const SKIP_DIRS = new Set(['data', 'uploads', 'tests', 'extension', 'tools', 'worker', 'docs']);
const WKEY = 'test-worker-key-0123456789abcdefghij';          // worker keys must be >= 24 chars
const FAKE_DL = '/tmp/ws-test-fake-dl.png';
const sha256 = s => createHash('sha256').update(s).digest('hex');

// ---- php + handler ------------------------------------------------------------------------------
const php = new PHP(await loadNodeRuntime('8.1', { emscriptenOptions: { processId: 1 } }));
const handler = new PHPRequestHandler({ php, documentRoot: '/www', absoluteUrl: 'http://localhost', cookieStore: false });
php.requestHandler = handler;
php.mkdirTree('/tmp/sess');
await setPhpIniEntries(php, { error_reporting: 'E_ALL', display_errors: '1', html_errors: '0', 'session.save_path': '/tmp/sess' });

// ---- copy the studio code ----------------------------------------------------------------------
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
for (const d of ['/www/studio/data/ws', '/www/studio/uploads', '/www/admin/data', '/www/studio/pulse']) php.mkdirTree(d);

// TEST-ONLY: a fake CDN host for the ingest success path (no network in wasm).
{
  let w = php.readFileAsText('/www/studio/ws-worker.php');
  const a = 'function ws_wk_url_ok(string $url): array {';
  const b = 'function ws_wk_download(string $url): array {';
  if (!w.includes(a) || !w.includes(b)) { console.error('cannot patch ws-worker.php for the fake download host'); process.exit(2); }
  const fake = `is_file('${FAKE_DL}') && strpos($url, 'https://fake-test.cloudfront.net/') === 0`;
  w = w.replace(a, a + `\n    if (${fake}) return ['ok' => true, 'host' => 'fake-test.cloudfront.net', 'ip' => '203.0.113.7'];`);
  w = w.replace(b, b + `\n    if (${fake}) { $t = tempnam(sys_get_temp_dir(), 'wsw'); copy('${FAKE_DL}', $t); return ['ok' => true, 'path' => $t, 'ext' => 'png']; }`);
  php.writeFile('/www/studio/ws-worker.php', w);
}
// TEST-ONLY: when /tmp/ws-test-canned.json exists, ws_ai_call() records the request it WOULD send
// (body + headers minus the key) and returns the canned answer instead of calling the network.
// The hook sits right before curl, so the real body/header building (model, fallbacks, beta) runs.
const CANNED = '/tmp/ws-test-canned.json', LASTREQ = '/tmp/ws-test-lastreq.json';
{
  let w = php.readFileAsText('/www/studio/inc/workspace.php');
  const at = '    @set_time_limit($timeout + 20);';
  if (!w.includes(at)) { console.error('cannot patch inc/workspace.php for the canned Claude answer'); process.exit(2); }
  w = w.replace(at, `    if (is_file('${CANNED}')) {
        file_put_contents('${LASTREQ}', json_encode(['body' => $body, 'headers' => array_values(array_filter($headers, fn($h) => stripos($h, 'x-api-key') !== 0))]));
        $c = json_decode((string)file_get_contents('${CANNED}'), true);
        if (empty($c['ok'])) return ['ok' => false, 'json' => null, 'error' => (string)$c['error'], 'usd' => 0.0];
        return ['ok' => true, 'json' => $c['json'], 'error' => null, 'usd' => ws_ai_cost($c['json'])];
    }
` + at);
  php.writeFile('/www/studio/inc/workspace.php', w);
}
// Dummy pages that exist on the live server but not in this worktree (same auth hook as the live ones:
// finance.php calls require_auth(); pulse/index.php calls is_authed() from a sub-folder).
const dummies = {
  'finance.php': `<?php declare(strict_types=1); require_once __DIR__ . '/inc/boot.php'; require_auth(); echo 'FINANCE PAGE';`,
  'pulse/index.php': `<?php declare(strict_types=1); require_once __DIR__ . '/../inc/boot.php'; if (!is_authed()) { header('Location: ../login.php'); exit; } echo 'PULSE PAGE';`,
};
for (const [f, code] of Object.entries(dummies)) { try { php.readFileAsText('/www/studio/' + f); } catch { php.writeFile('/www/studio/' + f, code); } }

// ---- fixture data ------------------------------------------------------------------------------
async function phpOut(code) { return (await php.run({ code })).text; }
async function makePng(w, h, rgb) {
  return Buffer.from(await phpOut(`<?php $im = imagecreatetruecolor(${w}, ${h}); imagefill($im, 0, 0, imagecolorallocate($im, ${rgb.join(',')})); ob_start(); imagepng($im); echo base64_encode(ob_get_clean());`), 'base64');
}
const HAS_GD = (await phpOut('<?php echo extension_loaded("gd") ? "1" : "0";')) === '1';
if (!HAS_GD) { console.error('GD is missing in this php-wasm build; the fixture needs it to make PNGs.'); process.exit(2); }
const pwHash = await phpOut('<?php echo password_hash("pw", PASSWORD_DEFAULT);');
const T0 = Math.floor(Date.now() / 1000);

php.writeFile('/www/admin/data/users.json', JSON.stringify([
  { username: 'grow', name: 'Grow', role: 'owner', hash: pwHash },
  { username: 'ed', name: 'Editor Ed', role: 'editor', hash: pwHash },
]));
php.writeFile('/www/studio/data/users-studio.json', '[]');
php.writeFile('/www/studio/data/projects.json', JSON.stringify([
  { id: 'alpha-comic', name: 'Alpha Comic', status: 'active', stage: 'page-build', tags: [], notes: '', cover: null, created: '2026-09-01', updated: '2026-09-01' },
  { id: 'beta-comic', name: 'Beta Comic', status: 'active', stage: 'writer', tags: [], notes: '', cover: null, created: '2026-09-01', updated: '2026-09-01' },
  { id: 'gamma-comic', name: 'Gamma <b>Comic</b>', status: 'active', stage: 'page-build', tags: [], notes: '', cover: null, created: '2026-09-01', updated: '2026-09-01' },
]));
const PNG = {};
const fixtureImgs = {
  'alpha-comic': [['p1a.png', 'Page 01', [200, 40, 40]], ['p1b.png', 'Page 01', [40, 200, 40]], ['p1c.png', 'Page 01', [40, 40, 200]],
                  ['p2a.png', 'Page 02', [90, 90, 90]], ['p2b.png', 'Page 02', [120, 120, 20]], ['p2c.png', 'Page 02', [60, 20, 120], { acc: true }],
                  ['ref1.png', '', [10, 10, 10]]],
  'gamma-comic': [['g1.png', 'Page 01', [250, 250, 0]]],
};
for (const [pid, rows] of Object.entries(fixtureImgs)) {
  php.mkdirTree(`/www/studio/uploads/${pid}/thumb`);
  const meta = [];
  let i = 0;
  for (const [f, g, rgb, opt] of rows) {
    const b = await makePng(80, 100, rgb); PNG[pid + '/' + f] = b;
    php.writeFile(`/www/studio/uploads/${pid}/${f}`, b);
    php.writeFile(`/www/studio/uploads/${pid}/thumb/${f}`, b);
    const row = { file: f, orig: f, rating: opt && opt.acc ? 'good' : 'unrated', accepted: !!(opt && opt.acc), group: g, tags: f === 'p1c.png' ? ['judge-pick'] : [], ts: T0 - 3600 + (i++) * 10, gen: '', genkey: '' };
    if (f.startsWith('ref')) row.isref = true;
    meta.push(row);
  }
  php.writeFile(`/www/studio/data/images-${pid}.json`, JSON.stringify(meta));
}
const UPLOAD_PNG = await makePng(90, 120, [30, 160, 220]);
const FAKE_PNG = await makePng(100, 130, [220, 120, 30]);

// ---- request helpers ----------------------------------------------------------------------------
let pass = 0, fail = 0; const failures = []; const diag = [];
function check(name, cond, extra) {
  if (cond) { pass++; console.log('PASS ' + name); return true; }
  fail++; failures.push(name);
  let s = extra === undefined ? '' : (typeof extra === 'string' ? extra : JSON.stringify(extra));
  if (!VERBOSE && s.length > 500) s = s.slice(0, 500) + '…';
  console.log('FAIL ' + name + (s ? '\n     ' + s : ''));
  return false;
}
function section(t) { console.log('\n== ' + t); }
const WARN_RE = /\b(Warning|Notice|Deprecated|Fatal error|Parse error|Uncaught)\b[^\n]{0,300}? on line \d+/;

class Client {
  constructor(name) { this.name = name; this.sid = null; }
  async req(method, url, { body, headers } = {}) {
    const h = Object.assign({}, headers || {});
    if (this.sid) h.cookie = 'mgstudio=' + this.sid;
    const res = await handler.request({ method, url, headers: h, body });
    for (const c of (res.headers['set-cookie'] || [])) {
      const m = /^mgstudio=([^;]*)/.exec(c);
      if (m) this.sid = (m[1] === '' || m[1] === 'deleted' || /Max-Age=0/i.test(c)) ? null : m[1];
    }
    let text = ''; try { text = res.text; } catch { text = ''; }
    let json = null; try { json = JSON.parse(text); } catch { /* not JSON */ }
    const ctype = (res.headers['content-type'] || [''])[0];
    if (!/^image\//.test(ctype)) {
      const m = WARN_RE.exec(text);
      if (m) diag.push(`${this.name} ${method} ${url} :: ${m[0]}`);
    }
    if (res.errors && res.errors.trim()) diag.push(`${this.name} ${method} ${url} :: stderr ${res.errors.trim().slice(0, 300)}`);
    return { status: res.httpStatusCode, text, json, loc: (res.headers.location || [])[0] || '', ctype, bytes: res.bytes, headers: res.headers };
  }
  get(url, headers) { return this.req('GET', url, { headers }); }
  post(url, body, headers) { return this.req('POST', url, { body, headers }); }
}
const readJson = f => { try { return JSON.parse(php.readFileAsText(f)); } catch { return null; } };
const readText = f => { try { return php.readFileAsText(f); } catch { return null; } };
const exists = f => { try { return php.fileExists(f); } catch { return false; } };
const D = '/www/studio/data';
const csrfFromHtml = html => (/name="csrf" value="([a-f0-9]+)"/.exec(html) || [])[1] || '';
const bootFromHtml = (html, id) => { const m = new RegExp(`<script type="application/json" id="${id}">(.*?)</script>`, 's').exec(html); try { return m ? JSON.parse(m[1]) : null; } catch { return null; } };
const onceFromHtml = html => (/id="onceUrl" readonly value="([^"]*)"/.exec(html) || [])[1] || '';
const tokOf = url => { try { return new URL(url.replace(/&amp;/g, '&')).searchParams.get('t') || ''; } catch { return ''; } };
const usageToday = () => { const u = readJson(D + '/ws/usage.json') || {}; const days = Object.keys(u.days || {}).sort(); return days.length ? u.days[days[days.length - 1]] : { users: {}, gens: 0 }; };
const short = r => ({ status: r.status, loc: r.loc, body: (r.text || '').slice(0, 300) });

const owner = new Client('owner'), lt = new Client('lt'), collab = new Client('collab'), editor = new Client('editor');
let r;

// =================================================================================================
section('GATE: owner sign-in and owner pages');
r = await owner.post('/studio/login.php', { username: 'grow', password: 'nope' });
check('owner wrong password -> stays on the form with an error', r.status === 200 && r.text.includes('Wrong username or password'), short(r));
r = await owner.post('/studio/login.php', { username: 'grow', password: 'pw' });
check('owner login.php POST -> 302 index.php + session cookie', r.status === 302 && r.loc === 'index.php' && !!owner.sid, short(r));
r = await owner.get('/studio/index.php');
check('owner opens index.php (Projects + Team/Workspace links)', r.status === 200 && r.text.includes('Projects') && r.text.includes('href="team.php"') && r.text.includes('href="ws.php"'), short(r));
r = await owner.get('/studio/cc.php');
check('owner opens cc.php', r.status === 200 && /Command Center|cc/i.test(r.text), short(r));
r = await owner.get('/studio/finance.php');
check('owner opens finance.php (dummy, require_auth)', r.status === 200 && r.text.includes('FINANCE PAGE'), short(r));
r = await owner.get('/studio/team.php');
let OWN_CSRF = csrfFromHtml(r.text);
check('owner opens team.php', r.status === 200 && r.text.includes('Team') && OWN_CSRF.length === 32, short(r));

r = await owner.post('/studio/team.php', { csrf: OWN_CSRF, do: 'brands', 'brand[alpha-comic]': '3DMC', 'brand[beta-comic]': '3DMC', 'brand[gamma-comic]': 'Maxx Muscle' });
let team = readJson(D + '/ws/team.json');
check('team.php brands: 3 comics assigned to 2 brands', r.status === 303 && team && team.projectBrands['alpha-comic'] === '3DMC' && team.projectBrands['beta-comic'] === '3DMC' && team.projectBrands['gamma-comic'] === 'Maxx Muscle', [short(r), team && team.projectBrands]);

r = await owner.post('/studio/team.php', { csrf: OWN_CSRF, do: 'add', name: 'Lt One', 'brands[0]': '3DMC' });
check('team.php add person -> 303', r.status === 303 && /team\.php#people/.test(r.loc), short(r));
r = await owner.get('/studio/team.php');
let LINK1 = onceFromHtml(r.text), TOK1 = tokOf(LINK1);
check('one-time magic link rendered once (ws.php?t=, 48 hex)', /\/studio\/ws\.php\?t=[a-f0-9]{48}$/.test(LINK1) && TOK1.length === 48, LINK1);
r = await owner.get('/studio/team.php');
check('magic link not shown again on the next load', r.status === 200 && onceFromHtml(r.text) === '', onceFromHtml(r.text));
team = readJson(D + '/ws/team.json');
const LT_ID = team.people[0] && team.people[0].id;
check('team.json stores only the token hash, never the token', !readText(D + '/ws/team.json').includes(TOK1) && team.people[0].tokenHash === sha256('ws-magic|' + TOK1) && /^lt_[a-f0-9]+$/.test(LT_ID), team.people[0]);

section('GATE: lieutenant magic link + confinement');
r = await lt.get('/studio/ws.php?t=' + TOK1);
check('ws.php?t=<token> -> 302 ws.php + session', r.status === 302 && r.loc === 'ws.php' && !!lt.sid, short(r));
r = await lt.get('/studio/ws.php');
let LT_BOOT = bootFromHtml(r.text, 'wsboot'); let LT_CSRF = LT_BOOT && LT_BOOT.csrf;
check('lt list: own-brand comics only, no Studio/Team links', r.status === 200 && r.text.includes('Alpha Comic') && r.text.includes('Beta Comic') && !r.text.includes('Gamma') && !r.text.includes('href="team.php"') && !r.text.includes('href="index.php"') && !!LT_CSRF, short(r));

const denied = [
  ['team.php', 403], ['review.php?p=alpha-comic', 403], ['creator.php', 403], ['creator.php?p=alpha-comic', 403], ['api.php', 403],
  ['finance.php', 403], ['pulse/index.php', 403], ['post/index.php', 403], ['cc.php', 403], ['export.php?p=alpha-comic', 403],
  ['ops.php', 403], ['project.php?p=alpha-comic', 403], ['ws.php?p=gamma-comic', 403], ['ws.php?p=no-such-comic', 403],
  ['ws-api.php?do=state&p=gamma-comic', 403], ['img.php?p=gamma-comic&f=g1.png', 403], ['img.php?p=gamma-comic&f=g1.png&t=1', 403],
  ['picker.php?p=gamma-comic', 403], ['picker.php?do=sig&p=gamma-comic', 403], ['ws-api.php?do=state&p=alpha-comic&pid=gamma-comic', 403],
];
for (const [u, code] of denied) {
  r = await lt.get('/studio/' + u);
  check(`lt ${u} -> ${code}`, r.status === code && !r.text.includes('FINANCE PAGE') && !r.text.includes('PULSE PAGE'), short(r));
}
{ // every other page in the studio root: 403 for a lieutenant (key-only endpoints refuse without their key)
  const ALLOW = new Set(['ws.php', 'ws-api.php', 'picker.php', 'img.php', 'help.php', 'login.php', 'index.php']);
  const KEY_ONLY = new Set(['bridge.php', 'ws-worker.php']);
  const pages = php.listFiles('/www/studio').filter(f => f.endsWith('.php') && !ALLOW.has(f)).sort();
  const bad = [];
  for (const f of pages) {
    const x = await lt.get('/studio/' + f);
    const ok = KEY_ONLY.has(f) ? (x.status === 403 && x.json && x.json.ok === false) : x.status === 403;
    if (!ok) bad.push(`${f}=${x.status}`);
  }
  check(`lt: all ${pages.length} other root pages refused (403)`, bad.length === 0 && pages.length >= 20, bad.join(' '));
}
r = await lt.req('POST', '/studio/picker.php?p=alpha-comic', { body: { csrf: LT_CSRF, do: 'save', p: 'gamma-comic', page: 'Page 01', c: 'x' } });
check('lt picker GET p=own + POST p=foreign -> 403 at the gate', r.status === 403 && !exists(D + '/ws/picks-alpha-comic.json'), short(r));
r = await lt.post('/studio/api.php', { csrf: LT_CSRF, p: 'alpha-comic', action: 'rate' });
check('lt POST api.php -> 403 JSON', r.status === 403 && r.json && r.json.ok === false, short(r));
r = await lt.get('/studio/index.php');
check('lt index.php -> 302 ws.php', r.status === 302 && r.loc === 'ws.php', short(r));
r = await lt.get('/studio/ws.php?p[]=alpha-comic');
check('lt ws.php?p[]=… (array param) -> 403, no PHP warning', r.status === 403 && !WARN_RE.test(r.text), short(r));
r = await lt.get('/studio/img.php?p[]=gamma-comic&f=g1.png');
check('lt img.php?p[]=… (array param) -> 403', r.status === 403, short(r));
r = await lt.post('/studio/ws-api.php?do=setproj&p=alpha-comic', { csrf: LT_CSRF, p: 'gamma-comic', story: 'x' });
check('lt ws-api GET p=own + POST p=foreign -> refused, foreign store untouched', (r.status === 400 || r.status === 403) && !exists(D + '/ws/proj-gamma-comic.json'), short(r));
r = await lt.post('/studio/picker.php', { csrf: LT_CSRF, do: 'save', p: 'gamma-comic', page: 'Page 01', c: 'x' });
check('lt picker POST p=foreign -> 403', r.status === 403 && !exists(D + '/ws/picks-gamma-comic.json'), short(r));

const allowed = ['ws.php?p=alpha-comic', 'ws.php?p=beta-comic', 'picker.php?p=alpha-comic', 'help.php', 'ws-api.php?do=state&p=alpha-comic', 'ws-api.php?do=ping&p=beta-comic'];
for (const u of allowed) { r = await lt.get('/studio/' + u); check(`lt ${u} -> 200`, r.status === 200, short(r)); }
r = await lt.get('/studio/img.php?p=alpha-comic&f=p1a.png');
check('lt img.php own brand -> 200 image bytes', r.status === 200 && r.ctype === 'image/png' && Buffer.from(r.bytes).equals(PNG['alpha-comic/p1a.png']), [r.status, r.ctype]);
r = await lt.get('/studio/img.php?p=alpha-comic&f=p1a.png&t=1');
check('lt img.php own brand thumb -> 200', r.status === 200 && r.ctype === 'image/png', [r.status]);
r = await lt.get('/studio/img.php?p=alpha-comic&f=..%2F..%2Fdata%2Fprojects.json');
check('lt img.php traversal -> 404', r.status === 404, short(r));
team = readJson(D + '/ws/team.json');
check('gate stamped lastSeenAt', !!(team.people[0] && team.people[0].lastSeenAt), team.people[0]);

section('GATE: rotate / deactivate kill sessions');
r = await owner.post('/studio/team.php', { csrf: OWN_CSRF, do: 'rotate', id: LT_ID });
r = await owner.get('/studio/team.php');
const LINK2 = onceFromHtml(r.text), TOK2 = tokOf(LINK2);
check('rotate shows a new one-time link', TOK2.length === 48 && TOK2 !== TOK1, LINK2);
r = await lt.get('/studio/ws-api.php?do=state&p=alpha-comic');
check('rotated: existing lieutenant session -> 401', r.status === 401 && r.json && r.json.ok === false, short(r));
r = await lt.get('/studio/ws.php?p=alpha-comic');
check('rotated: session is gone (signed-out page, no comic)', r.status === 200 && r.text.includes('open your private link') && !r.text.includes('wsboot'), short(r));
r = await lt.get('/studio/ws.php?t=' + TOK1);
check('rotated: old link -> 401', r.status === 401 && r.text.includes('not valid any more'), short(r));
r = await lt.get('/studio/ws.php?t=' + TOK2);
check('rotated: new link signs in', r.status === 302 && r.loc === 'ws.php', short(r));
r = await lt.get('/studio/ws-api.php?do=state&p=alpha-comic');
check('rotated: new session works', r.status === 200 && r.json && r.json.ok, short(r));
r = await owner.post('/studio/team.php', { csrf: OWN_CSRF, do: 'active', id: LT_ID, on: '0' });
check('deactivate -> 303', r.status === 303, short(r));
r = await lt.get('/studio/ws-api.php?do=state&p=alpha-comic');
check('deactivated: existing session -> 401', r.status === 401, short(r));
r = await lt.get('/studio/ws.php?t=' + TOK2);
check('deactivated: link -> 401', r.status === 401, short(r));
r = await owner.post('/studio/team.php', { csrf: OWN_CSRF, do: 'active', id: LT_ID, on: '1' });
r = await lt.get('/studio/ws.php?t=' + TOK2);
check('re-activated: latest link works again', r.status === 302 && r.loc === 'ws.php', short(r));
r = await lt.get('/studio/ws.php');
LT_BOOT = bootFromHtml(r.text, 'wsboot'); LT_CSRF = LT_BOOT && LT_BOOT.csrf;
check('re-activated: list renders with a CSRF token', r.status === 200 && !!LT_CSRF, short(r));

section('GATE: brand changes apply to a live session; no owner controls on lieutenant pages');
r = await owner.post('/studio/team.php', { csrf: OWN_CSRF, do: 'edit', id: LT_ID, 'brands[0]': 'Maxx Muscle' });
const sw1 = await lt.get('/studio/ws-api.php?do=state&p=gamma-comic'), sw2 = await lt.get('/studio/ws-api.php?do=state&p=alpha-comic'), sw3 = await lt.get('/studio/ws.php');
check('owner moves the lieutenant to Maxx Muscle -> sees gamma, loses alpha at once', r.status === 303 && sw1.status === 200 && sw2.status === 403 && sw3.text.includes('Gamma') && !sw3.text.includes('Alpha Comic'), [sw1.status, sw2.status]);
r = await owner.post('/studio/team.php', { csrf: OWN_CSRF, do: 'edit', id: LT_ID, 'brands[0]': '3DMC' });
r = await lt.get('/studio/ws-api.php?do=state&p=alpha-comic');
check('brand restored -> alpha visible again', r.status === 200, short(r));
for (const u of ['ws.php', 'ws.php?p=alpha-comic', 'picker.php?p=alpha-comic']) {
  r = await lt.get('/studio/' + u);
  const bad = ['port.php', 'posting.php', 'review.php', 'creator.php', 'team.php', 'href="index.php"', 'finance.php', 'bridge.php', 'cc.php'].filter(s => r.text.includes(s));
  check(`lt ${u}: no links to owner / publish / port pages`, r.status === 200 && bad.length === 0, bad);
}

section('GATE: collab + editor logins are not confined');
php.writeFile(D + '/users-studio.json', JSON.stringify([{ username: 'collab', name: 'Colla Borator', role: 'collab', hash: pwHash }]));
r = await collab.post('/studio/login.php', { username: 'collab', password: 'pw' });
check('collab login -> 302 index.php', r.status === 302 && r.loc === 'index.php' && !!collab.sid, short(r));
r = await collab.get('/studio/index.php');
check('collab index.php -> 200, no Team link', r.status === 200 && r.text.includes('Projects') && !r.text.includes('href="team.php"'), short(r));
for (const u of ['ws.php?p=gamma-comic', 'img.php?p=gamma-comic&f=g1.png', 'ws-api.php?do=state&p=gamma-comic', 'picker.php?p=gamma-comic', 'finance.php', 'pulse/index.php', 'cc.php']) {
  r = await collab.get('/studio/' + u); check(`collab ${u} -> 200`, r.status === 200, short(r));
}
r = await collab.get('/studio/team.php');
check('collab team.php -> 403 (owner only)', r.status === 403 && r.text.includes('owner only'), short(r));
r = await editor.post('/studio/login.php', { username: 'ed', password: 'pw' });
check('editor login -> 302 index.php', r.status === 302 && r.loc === 'index.php', short(r));
r = await editor.get('/studio/index.php');
check('editor index.php -> 200, no Team link', r.status === 200 && !r.text.includes('href="team.php"'), short(r));
r = await editor.get('/studio/team.php');
check('editor team.php -> 403', r.status === 403, short(r));
r = await editor.get('/studio/ws.php?p=gamma-comic');
check('editor ws.php?p=gamma-comic -> 200', r.status === 200 && r.text.includes('wsboot'), short(r));

// =================================================================================================
section('CSRF: every POST endpoint rejects a missing / wrong token');
const API_POST = ['create', 'setproj', 'page_save', 'page_delete', 'upload', 'ref_update', 'ref_remove', 'generate', 'cancel', 'ready', 'chat_send', 'action'];
const projBefore = readText(D + '/projects.json');
for (const a of API_POST) {
  const r1 = await lt.post(`/studio/ws-api.php?do=${a}&p=alpha-comic`, { name: 'x', brand: '3DMC', n: '1', text: 'x', page: '1', takes: '1' });
  const r2 = await lt.post(`/studio/ws-api.php?do=${a}&p=alpha-comic`, { csrf: 'f'.repeat(32), name: 'x', brand: '3DMC', n: '1', text: 'x', page: '1', takes: '1' });
  const r3 = await lt.post(`/studio/ws-api.php?do=${a}&p=alpha-comic`, { name: 'x' }, { 'X-CSRF': 'nope' });
  check(`ws-api ${a}: no/wrong/header-wrong token -> 403 JSON`, [r1, r2, r3].every(x => x.status === 403 && x.json && x.json.ok === false), [r1.status, r2.status, r3.status, r1.text.slice(0, 120)]);
}
check('ws-api: nothing written by rejected POSTs', readText(D + '/projects.json') === projBefore && !exists(D + '/ws/proj-alpha-comic.json') && !exists(D + '/ws/chat-alpha-comic.json'));
r = await lt.get('/studio/ws-api.php?do=create&name=x&brand=3DMC');
check('ws-api POST action via GET -> 405', r.status === 405, short(r));
{
  const r1 = await lt.post('/studio/picker.php?p=alpha-comic', { do: 'save', page: 'Page 01', c: 'x' });
  const r2 = await lt.post('/studio/picker.php?p=alpha-comic', { csrf: 'f'.repeat(32), do: 'save', page: 'Page 01', c: 'x' });
  check('picker save: no/wrong token -> 403', r1.status === 403 && r2.status === 403 && !exists(D + '/ws/picks-alpha-comic.json'), [r1.status, r2.status]);
}
const teamBefore = readText(D + '/ws/team.json');
for (const a of ['add', 'edit', 'rotate', 'active', 'brands', 'bulkbrand', 'brand_add', 'brand_del', 'settings', 'cancel']) {
  const r1 = await owner.post('/studio/team.php', { do: a, id: LT_ID, name: 'Evil', 'brands[0]': '3DMC', on: '0', brand: '3DMC' });
  const r2 = await owner.post('/studio/team.php', { csrf: 'f'.repeat(32), do: a, id: LT_ID, name: 'Evil', 'brands[0]': '3DMC', on: '0', brand: '3DMC' });
  check(`team.php ${a}: no/wrong token -> 403`, r1.status === 403 && r2.status === 403 && /CSRF/.test(r1.text), [r1.status, r2.status, r1.text.slice(0, 80)]);
}
check('team.php: team.json unchanged by rejected POSTs', readText(D + '/ws/team.json') === teamBefore);

// =================================================================================================
section('WORKSPACE: comics, pages, uploads, refs');
const API = (c, csrf) => (doName, body = {}, pid = null, headers) =>
  c.post(`/studio/ws-api.php?do=${doName}` + (pid ? '&p=' + pid : ''), Object.assign({ csrf }, body), headers);
let L = API(lt, LT_CSRF);
r = await L('create', { name: 'Foreign Brand Comic', brand: 'Maxx Muscle' });
check('lt create with a foreign brand -> 400', r.status === 400 && r.json && !r.json.ok, short(r));
r = await L('create', { name: 'Lt Made Comic', brand: '3DMC', style: 'glossy 3D render' });
const C = r.json && r.json.id;
check('lt create own brand -> ok', r.status === 200 && C === 'lt-made-comic', short(r));
const projs = readJson(D + '/projects.json');
team = readJson(D + '/ws/team.json');
check('create: project row + brand + style + chat line', projs.some(p => p.id === C && p.stage === 'page-build') && team.projectBrands[C] === '3DMC'
  && readJson(D + `/ws/proj-${C}.json`).style === 'glossy 3D render' && /created by Lt One/.test(readText(D + `/ws/chat-${C}.json`) || ''), team.projectBrands);
r = await lt.get(`/studio/ws.php?p=${C}`);
check('lt opens the new comic', r.status === 200 && bootFromHtml(r.text, 'wsboot').pid === C, short(r));
{
  const evil = '<script>alert(1)</script><img src=x onerror=alert(2)> Evil "q\' &';
  r = await L('create', { name: evil, brand: '3DMC', style: '</script><script>alert(3)</script>' });
  const EV = r.json && r.json.id;
  const pages = [await lt.get('/studio/ws.php'), await lt.get('/studio/ws.php?p=' + EV), await lt.get('/studio/picker.php?p=' + EV), await owner.get('/studio/index.php'), await owner.get('/studio/team.php')];
  const raw = pages.map((x, i) => [i, x.status, /<script>alert|<img src=x|<\/script><script>/.test(x.text)]);
  check('hostile comic name/style is escaped on ws.php, picker, index.php, team.php', !!EV && raw.every(([, s, hit]) => s === 200 && !hit), raw);
  const ev = (await lt.get(`/studio/ws-api.php?do=state&p=${EV}`)).json;
  check('hostile text round-trips verbatim through the JSON API (rendered via textContent)', ev && ev.project.name === evil && ev.proj.style === '</script><script>alert(3)</script>', ev && ev.project);
}

r = await L('setproj', { story: 'Once upon a gym.\r\nThe end.', style: 'warm light', aspect: '9:16' }, C);
check('setproj ok', r.status === 200 && r.json.ok, short(r));
r = await L('setproj', { aspect: '5:4' }, C);
check('setproj bad aspect -> 400', r.status === 400, short(r));
r = await L('page_save', { n: '0', title: 'Arrival', prompt: 'She walks into the gym. "Hi," she says.' }, C);
check('page_save append -> n=1', r.json && r.json.ok && r.json.n === 1, short(r));
r = await L('page_save', { n: '0', title: 'Second', prompt: 'Close-up, two women, one man.' }, C);
check('page_save append -> n=2', r.json && r.json.ok && r.json.n === 2, short(r));
r = await L('page_save', { n: '0', title: 'Third', prompt: 'Wide shot.' }, C);
check('page_save append -> n=3', r.json && r.json.ok && r.json.n === 3, short(r));
r = await L('page_save', { n: '1', title: 'Arrival!' }, C);
let st = (await lt.get(`/studio/ws-api.php?do=state&p=${C}`)).json;
let pg = n => st.pages.find(p => p.n === n);
check('partial page_save keeps the prompt; setproj stored', pg(1).title === 'Arrival!' && pg(1).prompt.startsWith('She walks') && st.proj.story === 'Once upon a gym.\nThe end.' && st.proj.aspect === '9:16', [pg(1), st.proj.story]);
r = await L('page_delete', { n: '3' }, C);
check('page_delete n=3 -> ok', r.status === 200 && r.json.ok, short(r));
r = await L('page_delete', { n: '3' }, C);
check('page_delete missing page -> 404', r.status === 404, short(r));
r = await L('page_save', { n: '0', title: 'Third again', prompt: 'Wide shot again.' }, C);
check('page_save after delete reuses the next number (3)', r.json && r.json.n === 3, short(r));

r = await L('upload', { kind: 'ref', 'files[]': new File([UPLOAD_PNG], 'Andrea sheet.png', { type: 'image/png' }) }, C);
const REF1 = r.json && r.json.files && r.json.files[0];
check('upload kind=ref (multipart) -> ok', r.status === 200 && r.json.ok && /^[a-f0-9]{10}\.png$/.test(REF1 || ''), short(r));
check('ref stored on disk + images row isref', exists(`/www/studio/uploads/${C}/${REF1}`) && exists(`/www/studio/uploads/${C}/thumb/${REF1}`) && (readJson(D + `/images-${C}.json`) || []).some(m => m.file === REF1 && m.isref));
r = await L('upload', { kind: 'take', page: '1', 'files[]': new File([UPLOAD_PNG], 'take one.png', { type: 'image/png' }) }, C);
const TAKE1 = r.json && r.json.files && r.json.files[0];
check('upload kind=take page=1 -> ok, grouped "Page 01"', r.status === 200 && r.json.ok && (readJson(D + `/images-${C}.json`) || []).some(m => m.file === TAKE1 && m.group === 'Page 01' && !m.isref), short(r));
r = await L('upload', { kind: 'take', page: '9', 'files[]': new File([UPLOAD_PNG], 't.png', { type: 'image/png' }) }, C);
check('upload take to a missing page -> 400', r.status === 400, short(r));
r = await L('upload', { kind: 'ref', 'files[]': new File([Uint8Array.from([1, 2, 3, 4])], 'evil.png', { type: 'image/png' }) }, C);
check('upload non-image -> 400', r.status === 400 && /readable image/.test(JSON.stringify(r.json)), short(r));
r = await L('upload', { kind: 'ref', 'files[]': new File([Buffer.from('<?php echo 1;')], 'x.php', { type: 'image/png' }) }, C);
check('upload .php -> 400', r.status === 400, short(r));
r = await L('upload', { kind: 'bogus', 'files[]': new File([UPLOAD_PNG], 'a.png') }, C);
check('upload bad kind -> 400', r.status === 400, short(r));

r = await L('page_save', { n: '1', 'refs[0]': REF1, 'refs[1]': 'not-a-ref.png', 'refs[2]': '../../x.png' }, C);
st = (await lt.get(`/studio/ws-api.php?do=state&p=${C}`)).json;
check('page_save refs: only known refs kept', JSON.stringify(pg(1).refs) === JSON.stringify([REF1]) && st.refs.length === 1 && st.refs[0].label === 'Andrea sheet' && pg(1).takes === 1, [pg(1), st.refs]);
r = await L('ref_update', { file: REF1, label: 'Andrea <turnaround>' }, C);
check('ref_update ok', r.status === 200 && (readJson(D + `/ws/proj-${C}.json`).refs[0].label === 'Andrea <turnaround>'), short(r));
r = await L('ref_update', { file: '../../data/ai.json', label: 'x' }, C);
check('ref_update traversal -> 400/404', r.status === 400 || r.status === 404, short(r));
r = await L('ref_update', { file: 'nope.png', label: 'x' }, C);
check('ref_update unknown file -> 404', r.status === 404, short(r));
r = await L('ref_remove', { file: REF1 }, C);
st = (await lt.get(`/studio/ws-api.php?do=state&p=${C}`)).json;
check('ref_remove: gone from refs and page refs; file kept', r.status === 200 && st.refs.length === 0 && pg(1).refs.length === 0 && exists(`/www/studio/uploads/${C}/${REF1}`), [short(r), st.refs, pg(1)]);
r = await L('upload', { kind: 'ref', 'files[]': new File([UPLOAD_PNG], 'Gym plate.png', { type: 'image/png' }) }, C);
const REF2 = r.json && r.json.files && r.json.files[0];
r = await L('page_save', { n: '1', refs: REF2 }, C);
st = (await lt.get(`/studio/ws-api.php?do=state&p=${C}`)).json;
check('page_save refs as comma string -> attached', JSON.stringify(pg(1).refs) === JSON.stringify([REF2]), pg(1));

section('WORKSPACE: generate, quotas, cancel');
const settingsBase = { gensPerDay: '50', globalGensPerDay: '150', msgsPerDay: '80', usdPerDay: '3', maxTakes: '4', minGapSec: '20',
  genModel: 'nano_banana_pro', genResolution: '1k', chatModel: 'claude-opus-5-5', chatEffort: 'low', workerEnabled: '1' };
const setSettings = async o => owner.post('/studio/team.php', Object.assign({ csrf: OWN_CSRF, do: 'settings' }, settingsBase, o));
r = await setSettings({ gensPerDay: '5', globalGensPerDay: '8' });
check('team settings: gensPerDay=5, globalGensPerDay=8', r.status === 303 && readJson(D + '/ws/team.json').settings.gensPerDay === 5 && readJson(D + '/ws/team.json').settings.globalGensPerDay === 8, [short(r), readJson(D + '/ws/team.json').settings]);
r = await setSettings({ maxTakes: '99' });
check('team settings out of range -> nothing saved', readJson(D + '/ws/team.json').settings.maxTakes === 4, readJson(D + '/ws/team.json').settings);

r = await L('generate', { page: '1', takes: '4' }, C);
const JOB_LT = r.json && r.json.job && r.json.job.id;
check('lt generate 4 -> ok, 1 left', r.status === 200 && r.json.ok && r.json.left === 1 && /^wsj_/.test(JOB_LT || ''), short(r));
r = await L('generate', { page: '1', takes: '4' }, C);
check('lt second generate 4 -> quota error (1 left)', r.status === 400 && r.json && !r.json.ok && r.json.left === 1 && /left today|limit/i.test(r.json.error), short(r));
r = await L('generate', { page: '2', takes: '9' }, C);
check('takes above maxTakes are clamped (4 > 1 left -> refused)', r.status === 400, short(r));
r = await L('generate', { page: '7', takes: '1' }, C);
check('generate on a missing page -> 400', r.status === 400 && /does not exist/.test(r.json.error), short(r));
r = await owner.get(`/studio/ws.php?p=${C}`);
const OWN_WS_CSRF = bootFromHtml(r.text, 'wsboot').csrf;
check('owner shares one CSRF token across team.php and ws.php', OWN_WS_CSRF === OWN_CSRF, [OWN_WS_CSRF, OWN_CSRF]);
const O = API(owner, OWN_CSRF);
r = await O('generate', { page: '2', takes: '4' }, C);
const JOB_OWN = r.json && r.json.job && r.json.job.id;
check('owner generate 4 -> ok (global 8/8 used)', r.status === 200 && r.json.ok, short(r));
r = await O('generate', { page: '2', takes: '1' }, C);
check('owner generate past the global cap -> studio-wide limit error', r.status === 400 && /studio-wide/i.test(r.json.error), short(r));
r = await L('generate', { page: '1', takes: '1' }, C);
check('lt generate 1 with global cap reached -> refused', r.status === 400 && r.json.left === 0, short(r));
let u = usageToday();
check('usage.json: lt 4, global 8', u.users[LT_ID].gens === 4 && u.gens === 8, u);
r = await L('cancel', { job: JOB_OWN }, C);
check("lt cannot cancel the owner's job", r.status === 409 && /own jobs/.test(r.json.error), short(r));
r = await L('cancel', { job: 'wsj_<script>' }, C);
check('cancel bad job id -> 400', r.status === 400, short(r));
r = await L('cancel', { job: JOB_LT }, C);
st = (await lt.get(`/studio/ws-api.php?do=state&p=${C}`)).json;
u = usageToday();
check('lt cancel own queued job -> quota released', r.status === 200 && u.users[LT_ID].gens === 0 && u.gens === 4 && st.quota.left === 4 && st.jobs.find(j => j.id === JOB_LT).status === 'cancelled', [short(r), u, st.quota]);
r = await L('cancel', { job: JOB_LT }, C);
check('cancel twice -> 409', r.status === 409, short(r));
r = await O('cancel', { job: JOB_OWN }, C);
check('owner cancels own job -> ok, global 0', r.status === 200 && usageToday().gens === 0, short(r));

section('WORKSPACE: ready, chat, action cards, ping');
r = await L('ready', {}, C);
check('ready -> stage review', r.status === 200 && r.json.stage === 'review' && readJson(D + '/projects.json').find(p => p.id === C).stage === 'review', short(r));
r = await L('ping', {}, C);
check('ping via POST is not a POST action -> 404/405/200 JSON (never HTML)', !!r.json, short(r));
r = await lt.get(`/studio/ws-api.php?do=ping&p=${C}`);
const SIG0 = r.json && r.json.sig, CHATSIG0 = r.json && r.json.chat, REST0 = r.json && r.json.rest;
check('ping -> sig', r.status === 200 && /^[a-f0-9]{32}$/.test(SIG0 || ''), short(r));
r = await L('chat_send', { text: 'hello team', ai: '0' }, C);
check('chat_send ai=0 appends', r.status === 200 && r.json.msgs.length === 1 && r.json.msgs[0].text === 'hello team' && r.json.msgs[0].by === 'Lt One'
  && (readJson(D + `/ws/chat-${C}.json`).msgs || []).some(m => m.text === 'hello team'), short(r));
r = await lt.get(`/studio/ws-api.php?do=ping&p=${C}`);
check('ping sig changes after a chat write (chat sig moves, rest does not)', r.json.sig !== SIG0 && r.json.chat !== CHATSIG0 && r.json.rest === REST0, [SIG0, r.json]);
r = await L('chat_send', { text: 'Claude, split the story', ai: '1' }, C);
check('chat_send ai=1 without ai.json -> 200 with a graceful system line', r.status === 200 && r.json.ok && r.json.msgs.length === 2 && r.json.msgs[1].role === 'system' && /No AI key/.test(r.json.msgs[1].text), short(r));
check('failed Claude call refunded the chat count', ((usageToday().users[LT_ID] || {}).msgs | 0) === 0, usageToday());
r = await L('chat_send', { text: '   ', ai: '0' }, C);
check('empty message -> 400', r.status === 400, short(r));
r = await L('chat_send', { text: 'x'.repeat(4001), ai: '0' }, C);
check('message over 4000 chars -> 400', r.status === 400, short(r));
r = await lt.get(`/studio/ws-api.php?do=chat&p=${C}&since=0`);
const lastChatId = r.json.msgs[r.json.msgs.length - 1].id;
r = await lt.get(`/studio/ws-api.php?do=chat&p=${C}&since=${lastChatId}`);
check('chat since=<last> -> empty', r.status === 200 && r.json.msgs.length === 0, short(r));

// hand-inject Claude messages with action cards
{
  const chat = readJson(D + `/ws/chat-${C}.json`);
  let id = Math.max(...chat.msgs.map(m => m.id));
  const now = Math.floor(Date.now() / 1000);
  chat.msgs.push({ id: ++id, ts: now, uid: 'claude', by: 'Claude', role: 'ai', text: 'Here is what I propose:', actions: [
    { aid: 'a1', kind: 'set_prompt', args: { page: 1, title: 'Arrival (v2)', prompt: 'Injected prompt from Claude.' }, summary: 'Set page 1 prompt', status: 'pending' },
    { aid: 'a2', kind: 'generate', args: { page: 99, takes: 2 }, summary: 'Generate 2 takes of page 99', status: 'pending' },
    { aid: 'a3', kind: 'add_pages', args: { pages: [{ title: 'Extra', prompt: 'Extra page.' }] }, summary: 'Add 1 page: Extra', status: 'pending' },
    { aid: 'a4', kind: 'set_prompt', args: { page: 0, prompt: '' }, summary: 'invalid', status: 'pending' },
  ] });
  chat.msgs.push({ id: ++id, ts: now - 3 * 86400, uid: 'claude', by: 'Claude', role: 'ai', text: 'old', actions: [
    { aid: 'a1', kind: 'add_pages', args: { pages: [{ title: 'Old', prompt: 'Old.' }] }, summary: 'old', status: 'pending' }] });
  php.writeFile(D + `/ws/chat-${C}.json`, JSON.stringify(chat));
}
const aiMsg = readJson(D + `/ws/chat-${C}.json`).msgs.find(m => m.role === 'ai' && m.text !== 'old').id;
const oldMsg = readJson(D + `/ws/chat-${C}.json`).msgs.find(m => m.text === 'old').id;
const userMsg = readJson(D + `/ws/chat-${C}.json`).msgs.find(m => m.role === 'user').id;
const cardStatus = (mid, aid) => (readJson(D + `/ws/chat-${C}.json`).msgs.find(m => m.id === mid).actions.find(a => a.aid === aid) || {}).status;
r = await L('action', { msg: String(aiMsg), aid: 'a1', decision: 'confirm' }, C);
st = (await lt.get(`/studio/ws-api.php?do=state&p=${C}`)).json;
check('action confirm set_prompt -> prompt saved, card confirmed', r.status === 200 && r.json.ok && pg(1).prompt === 'Injected prompt from Claude.' && pg(1).title === 'Arrival (v2)' && cardStatus(aiMsg, 'a1') === 'confirmed', [short(r), pg(1)]);
r = await L('action', { msg: String(aiMsg), aid: 'a1', decision: 'confirm' }, C);
check('confirming the same card twice -> 409', r.status === 409, short(r));
r = await L('action', { msg: String(aiMsg), aid: 'a2', decision: 'confirm' }, C);
check('confirm generate on a missing page -> clean 400, card failed, no job', r.status === 400 && /page 99|Page 99/.test(r.json.error) && cardStatus(aiMsg, 'a2') === 'failed'
  && !(readJson(D + '/ws/jobs.json').jobs || []).some(j => j.page === 99), short(r));
const pagesBefore = st.pages.length;
r = await L('action', { msg: String(aiMsg), aid: 'a3', decision: 'dismiss' }, C);
st = (await lt.get(`/studio/ws-api.php?do=state&p=${C}`)).json;
check('dismiss -> card dismissed, nothing added', r.status === 200 && cardStatus(aiMsg, 'a3') === 'dismissed' && st.pages.length === pagesBefore, short(r));
r = await L('action', { msg: String(aiMsg), aid: 'a4', decision: 'confirm' }, C);
check('confirm an invalid (re-validated) card -> 400, failed', r.status === 400 && cardStatus(aiMsg, 'a4') === 'failed', short(r));
r = await L('action', { msg: String(oldMsg), aid: 'a1', decision: 'confirm' }, C);
check('card older than a day -> 409', r.status === 409 && /day old/.test(r.json.error), short(r));
r = await L('action', { msg: String(userMsg), aid: 'a1', decision: 'confirm' }, C);
check('action on a user message -> 409', r.status === 409, short(r));
r = await L('action', { msg: String(aiMsg), aid: 'zz', decision: 'confirm' }, C);
check('bad aid -> 400', r.status === 400, short(r));
r = await L('action', { msg: '99999', aid: 'a1', decision: 'confirm' }, C);
check('unknown message -> 404', r.status === 404, short(r));

section('WORKSPACE: Claude chat (canned API answer, no network)');
php.writeFile(D + '/ai.json', JSON.stringify({ key: 'sk-ant-TEST-ONLY-not-a-real-key' }));   // fake key, virtual FS only
const canned = o => php.writeFile(CANNED, JSON.stringify(o));
const msgJson = (obj, extra = {}) => ({ ok: true, json: Object.assign({ model: 'claude-opus-5-5', stop_reason: 'end_turn',
  content: [{ type: 'thinking', thinking: '' }, { type: 'text', text: JSON.stringify(obj) }], usage: { input_tokens: 3000, output_tokens: 500, cache_read_input_tokens: 1000 } }, extra) });
canned(msgJson({ reply: 'Here is a plan for the next pages.', actions: [
  { kind: 'add_pages', page: 0, title: '', prompt: '', takes: 0, pages: [{ title: 'Pump', prompt: 'She curls the bar, veins rising.' }, { title: '', prompt: '' }, { title: 'Mirror', prompt: 'She flexes at the mirror.' }] },
  { kind: 'drop_database', page: 1, title: '', prompt: '', takes: 0, pages: [] },
  { kind: 'generate', page: 1, title: '', prompt: '', takes: 0, pages: [] },
  { kind: 'set_prompt', page: 0, title: '', prompt: 'no page', takes: 0, pages: [] },
] }));
r = await L('chat_send', { text: 'Claude, add two gym pages', ai: '1' }, C);
const aiRow = r.json && r.json.msgs && r.json.msgs[1];
check('Claude reply -> ai message with 2 valid cards (bogus + invalid dropped, empty page skipped)', r.status === 200 && aiRow && aiRow.role === 'ai' && aiRow.actions.length === 2
  && aiRow.actions[0].kind === 'add_pages' && aiRow.actions[0].args.pages.length === 2 && aiRow.actions[1].kind === 'generate' && aiRow.actions[1].args.takes === 2
  && aiRow.actions.every(a => a.status === 'pending') && aiRow.actions[0].aid === 'a1', short(r));
const req = readJson(LASTREQ);
check('outgoing request: claude-opus-5-5, effort low, json_schema format, cached system, fallbacks "default" + beta header',
  req && req.body.model === 'claude-opus-5-5' && req.body.output_config.effort === 'low' && req.body.output_config.format.type === 'json_schema'
  && req.body.system[0].cache_control.type === 'ephemeral' && req.body.fallbacks === 'default' && req.body.max_tokens > 0
  && req.headers.includes('anthropic-beta: server-side-fallback-2026-07-01') && req.headers.includes('anthropic-version: 2023-06-01')
  && !JSON.stringify(req).includes('sk-ant-TEST'), req && { model: req.body.model, oc: req.body.output_config && req.body.output_config.effort, fb: req.body.fallbacks, h: req.headers });
check('context sent to Claude is built server-side (comic, story, pages, quota)', req && /Comic: Lt Made Comic/.test(req.body.messages[0].content) && /Once upon a gym/.test(req.body.messages[0].content)
  && /Images left today for Lt One/.test(req.body.messages[0].content) && /NEW MESSAGE from Lt One: Claude, add two gym pages/.test(req.body.messages[0].content));
u = usageToday();
check('chat usage: 1 reply counted, cost recorded', u.users[LT_ID].msgs === 1 && u.users[LT_ID].usd > 0, u.users[LT_ID]);
st = (await lt.get(`/studio/ws-api.php?do=state&p=${C}`)).json;
const nPagesBefore = st.pages.length;
r = await L('action', { msg: String(aiRow.id), aid: 'a1', decision: 'confirm' }, C);
st = (await lt.get(`/studio/ws-api.php?do=state&p=${C}`)).json;
check('confirm Claude add_pages card -> 2 pages appended', r.status === 200 && st.pages.length === nPagesBefore + 2 && st.pages.some(p => p.title === 'Mirror'), [short(r), st.pages.map(p => p.n + ':' + p.title)]);
canned(msgJson({ reply: '', actions: [] }, { stop_reason: 'refusal', content: [] }));
r = await L('chat_send', { text: 'something it declines', ai: '1' }, C);
check('refusal -> polite ai line, no cards', r.status === 200 && r.json.msgs[1].role === 'ai' && /can't help/.test(r.json.msgs[1].text) && r.json.msgs[1].actions.length === 0, short(r));
canned(msgJson({ reply: 'x' }, { stop_reason: 'max_tokens', content: [{ type: 'text', text: '{"reply":"cut' }] }));
r = await L('chat_send', { text: 'split all 80 pages', ai: '1' }, C);
check('max_tokens -> system line about a too-long answer', r.status === 200 && r.json.msgs[1].role === 'system' && /too long/.test(r.json.msgs[1].text), short(r));
canned({ ok: true, json: { model: 'claude-opus-5-5', stop_reason: 'end_turn', content: [{ type: 'text', text: 'not json at all' }], usage: {} } });
r = await L('chat_send', { text: 'hello?', ai: '1' }, C);
check('unreadable answer -> system line, no 500', r.status === 200 && r.json.msgs[1].role === 'system' && /could not be read/.test(r.json.msgs[1].text), short(r));
canned({ ok: false, error: 'Claude error (529): overloaded' });
const msgsBeforeFail = usageToday().users[LT_ID].msgs;
r = await L('chat_send', { text: 'are you there', ai: '1' }, C);
check('API error -> system line, chat count refunded', r.status === 200 && /overloaded/.test(r.json.msgs[1].text) && usageToday().users[LT_ID].msgs === msgsBeforeFail, [short(r), usageToday().users[LT_ID]]);
await setSettings({ msgsPerDay: String(usageToday().users[LT_ID].msgs) });
canned(msgJson({ reply: 'should not be sent', actions: [] }));
php.writeFile(LASTREQ, 'none');
r = await L('chat_send', { text: 'one more', ai: '1' }, C);
check('lieutenant chat cap reached -> limit line, no API call', r.status === 200 && /Daily Claude chat limit/.test(r.json.msgs[1].text) && readText(LASTREQ) === 'none', short(r));
r = await O('chat_send', { text: 'owner question', ai: '1' }, C);
check('owner is not bound by the lieutenant chat cap', r.status === 200 && r.json.msgs[1].role === 'ai' && r.json.msgs[1].text === 'should not be sent', short(r));
await setSettings({});
php.writeFile(CANNED, ''); php.unlink(CANNED); php.unlink(D + '/ai.json');

section('WORKSPACE: malformed input never corrupts a store');
{
  const FORM = { 'content-type': 'application/x-www-form-urlencoded' };
  const raw = (c, url, s) => c.req('POST', url, { body: new Uint8Array(Buffer.from(s, 'latin1')), headers: FORM });
  r = await raw(lt, `/studio/ws-api.php?do=chat_send&p=${C}`, `csrf=${LT_CSRF}&ai=0&text=bad%FF%FEbytes%00%07end`);
  const chatNow = readJson(D + `/ws/chat-${C}.json`);
  check('chat_send with invalid UTF-8 + control chars -> stored cleaned, chat store still valid', r.status === 200 && chatNow && chatNow.msgs.length > 3
    && chatNow.msgs.some(m => typeof m.text === 'string' && m.text.startsWith('bad') && m.text.endsWith('end') && !/[\x00\x07]/.test(m.text)), short(r));
  r = await raw(lt, `/studio/ws-api.php?do=page_save&p=${C}`, `csrf=${LT_CSRF}&n=1&title=T%C3%28itle%FF`);
  check('page_save with invalid UTF-8 -> proj store still valid', r.status === 200 && readJson(D + `/ws/proj-${C}.json`) && readJson(D + `/ws/proj-${C}.json`).pages.length >= 3, short(r));
  r = await raw(lt, `/studio/picker.php?p=${C}`, `csrf=${LT_CSRF}&do=save&p=${C}&page=Page%2001&c=note%FF%FE`);
  check('picker comment with invalid UTF-8 -> picks store valid', r.status === 200 && readJson(D + `/ws/picks-${C}.json`) !== null, short(r));
  r = await raw(lt, `/studio/ws-api.php?do=setproj&p=${C}`, `csrf=${LT_CSRF}&story[]=x&style[a]=y`);
  check('setproj with array fields -> no warning, proj store valid', (r.status === 200 || r.status === 400) && !WARN_RE.test(r.text) && readJson(D + `/ws/proj-${C}.json`) !== null, short(r));
  r = await raw(lt, `/studio/ws-api.php?do=generate&p=${C}`, `csrf=${LT_CSRF}&page[]=1&takes=1`);
  check('generate with array page -> 400, no warning', r.status === 400 && !WARN_RE.test(r.text), short(r));
  r = await raw(lt, `/studio/ws-api.php?do=setproj`, `csrf=${LT_CSRF}&p[]=${C}&story=x`);
  check('POST p[] (array) -> refused at the gate', r.status === 403, short(r));
  const teamNow = readText(D + '/ws/team.json');
  r = await raw(owner, '/studio/team.php', `csrf=${OWN_CSRF}&do=add&name=Bad%FFName&brands%5B%5D=3DMC`);
  check('team add with invalid UTF-8 name -> refused, team.json unchanged', r.status === 303 && readText(D + '/ws/team.json') === teamNow, short(r));
  r = await raw(owner, '/studio/team.php', `csrf=${OWN_CSRF}&do=edit&id[]=x&brands=3DMC`);
  check('team edit with array id -> clean error, no warning', r.status === 303 && !WARN_RE.test(r.text), short(r));
  await owner.get('/studio/team.php');   // consume the flash
}

// =================================================================================================
section('PICKER');
const A = 'alpha-comic';
r = await lt.get('/studio/picker.php?p=' + A);
let pk = bootFromHtml(r.text, 'pkdata');
const pkPage = g => pk && pk.pages.find(p => p.g === g);
check('picker renders groups (refs excluded), all to do', r.status === 200 && pk && pk.pages.map(p => p.g).join(',') === 'Page 01,Page 02' && pkPage('Page 01').takes.length === 3 && pk.pages.every(p => p.todo), pk && pk.pages.map(p => [p.g, p.todo, p.takes.length]));
check("picker tags Claude's pick (judge-pick)", pkPage('Page 01').takes.find(t => t.f === 'p1c.png').cl === true);
check('take kept earlier in review.php shows as KEPT (sorted last), not pre-picked', pkPage('Page 02').takes.slice(-1)[0].f === 'p2c.png' && pkPage('Page 02').takes.slice(-1)[0].k === true && pkPage('Page 02').pick.length === 0, pkPage('Page 02'));
check('picker page is lieutenant-safe (no Review link, no hub nav)', !r.text.includes('review.php') && !r.text.includes('hub/nav.js'));
const PK_CSRF = (/data-csrf="([a-f0-9]+)"/.exec(r.text) || [])[1];
check('picker embeds the session CSRF token', PK_CSRF === LT_CSRF, [PK_CSRF, LT_CSRF]);
r = await lt.get('/studio/picker.php?do=sig&p=' + A);
check('do=sig -> img + picks stamps', r.status === 200 && r.json.ok && /^\d+\.\d+$/.test(r.json.img) && r.json.picks === '0', short(r));
const SAVE = (body, hdr = true) => lt.post('/studio/picker.php?p=' + A, Object.assign({ do: 'save', p: A }, hdr ? {} : { csrf: LT_CSRF }, body), hdr ? { 'X-CSRF': LT_CSRF } : undefined);
const imgRow = f => readJson(D + `/images-${A}.json`).find(m => m.file === f);
r = await SAVE({ page: 'Page 01', pick: JSON.stringify(['p1a.png', 'p1b.png']) });
let picks = readJson(D + `/ws/picks-${A}.json`);
check('save multi-pick -> settled, picks file written', r.status === 200 && r.json.ok && r.json.todo === false && JSON.stringify(picks.pages['Page 01'].pick) === '["p1a.png","p1b.png"]' && picks.pages['Page 01'].by === 'Lt One', [short(r), picks]);
check('multi-pick mirrored into images accepted/rating', imgRow('p1a.png').accepted === true && imgRow('p1a.png').rating === 'good' && imgRow('p1b.png').accepted === true && imgRow('p1c.png').accepted === false, [imgRow('p1a.png'), imgRow('p1c.png')]);
r = await SAVE({ page: 'Page 02', pick: 'drop' }, false);
picks = readJson(D + `/ws/picks-${A}.json`);
check('drop (csrf as a field) -> pick "drop", takes not accepted', r.status === 200 && picks.pages['Page 02'].pick === 'drop' && imgRow('p2a.png').accepted === false && r.json.todo === false, short(r));
check("drop never clears the owner's earlier review keep", imgRow('p2c.png').accepted === true && imgRow('p2c.png').rating === 'good', imgRow('p2c.png'));
let imgBefore = readText(D + `/images-${A}.json`);
r = await SAVE({ page: 'Page 01', c: 'Hands look off' });
check('comment-only save -> c stored, images file untouched', r.status === 200 && readJson(D + `/ws/picks-${A}.json`).pages['Page 01'].c === 'Hands look off' && readText(D + `/images-${A}.json`) === imgBefore
  && JSON.stringify(readJson(D + `/ws/picks-${A}.json`).pages['Page 01'].pick) === '["p1a.png","p1b.png"]', short(r));
r = await SAVE({ page: 'Page 01', pick: JSON.stringify(['p1b.png', 'p1a.png']) });
check('same pick in another order -> images file untouched', r.status === 200 && readText(D + `/images-${A}.json`) === imgBefore, short(r));
for (const [label, pick, re] of [['foreign take (other comic)', ['g1.png'], /not on Page 01/], ['foreign take via path', ['../gamma-comic/g1.png'], /not on Page 01/],
  ['take from another page', ['p2a.png'], /not on Page 01/], ['bad file name', ['a b.png'], /Bad file name/], ['not a list', { x: 1 }, /Bad pick list/]]) {
  r = await SAVE({ page: 'Page 01', pick: JSON.stringify(pick) });
  check(`pick rejected: ${label}`, r.status === 400 && re.test(r.json.error) && readText(D + `/images-${A}.json`) === imgBefore, short(r));
}
r = await SAVE({ page: 'Page 99', pick: JSON.stringify(['p1a.png']) });
check('pick on a page with no takes -> 400', r.status === 400, short(r));
r = await SAVE({ page: 'Page 01' });
check('save with neither pick nor c -> 400', r.status === 400, short(r));
r = await lt.post('/studio/picker.php?p=' + A, { do: 'nope', p: A }, { 'X-CSRF': LT_CSRF });
check('unknown picker action -> 400 JSON', r.status === 400 && r.json && !r.json.ok, short(r));
r = await lt.get('/studio/picker.php?p=' + A);
pk = bootFromHtml(r.text, 'pkdata');
check('after picks: both pages settled', pk.pages.every(p => !p.todo) && /show settled \(2\)/.test(r.text), pk.pages.map(p => [p.g, p.todo]));
// a new take lands on Page 01 -> the page is "to do" again, old comment shown as "last".
// (Back-date the saved record a few seconds: "new" means landed AFTER the pick, and this test runs in < 1 s.)
{ const p = readJson(D + `/ws/picks-${A}.json`); p.pages['Page 01'].ts -= 5; php.writeFile(D + `/ws/picks-${A}.json`, JSON.stringify(p)); }
r = await L('page_save', { n: '1', title: 'Page one', prompt: 'p' }, A);
r = await L('upload', { kind: 'take', page: '1', 'files[]': new File([UPLOAD_PNG], 'new take.png', { type: 'image/png' }) }, A);
const NEWTAKE = r.json && r.json.files && r.json.files[0];
check('new take uploaded to alpha Page 01', r.status === 200 && !!NEWTAKE, short(r));
r = await lt.get('/studio/picker.php?p=' + A);
pk = bootFromHtml(r.text, 'pkdata');
check('sig change -> Page 01 back to "to do", stale, last comment kept, new take flagged', pkPage('Page 01').todo && pkPage('Page 01').stale && pkPage('Page 01').last === 'Hands look off' && pkPage('Page 01').c === ''
  && pkPage('Page 01').takes.find(t => t.f === NEWTAKE).n === true && !pkPage('Page 02').todo, pkPage('Page 01'));
r = await SAVE({ page: 'Page 01', pick: JSON.stringify(['p1a.png', 'p1b.png']) });
picks = readJson(D + `/ws/picks-${A}.json`);
check('keep pick after new takes -> settled, comment archived to prev_c', r.status === 200 && r.json.todo === false && picks.pages['Page 01'].prev_c === 'Hands look off' && picks.pages['Page 01'].c === '', picks.pages['Page 01']);
r = await SAVE({ page: 'Page 01', pick: '[]' });
check('unpick all -> to do; picker-given "good" undone', r.status === 200 && r.json.todo === true && imgRow('p1a.png').accepted === false && imgRow('p1a.png').rating === 'unrated', [short(r), imgRow('p1a.png')]);
r = await SAVE({ page: 'Page 02', pick: JSON.stringify(['p2b.png']) });
check('restore a dropped page with a pick', r.status === 200 && readJson(D + `/ws/picks-${A}.json`).pages['Page 02'].pick[0] === 'p2b.png' && imgRow('p2b.png').accepted === true, short(r));
r = await SAVE({ page: 'Page 02', pick: JSON.stringify(['p2a.png']) });
check('switching the pick clears only the picker\'s own earlier pick; review keep stays', r.status === 200 && imgRow('p2b.png').accepted === false && imgRow('p2a.png').accepted === true && imgRow('p2c.png').accepted === true, [imgRow('p2a.png'), imgRow('p2b.png'), imgRow('p2c.png')]);
r = await owner.get('/studio/picker.php?p=gamma-comic');
check('owner opens the picker on any comic (with Review link)', r.status === 200 && r.text.includes('review.php?p=gamma-comic'), short(r));

// =================================================================================================
section('WORKER');
php.writeFile(D + '/ws/worker.json', JSON.stringify({ keyHash: sha256(WKEY) }));
php.writeFile(D + '/ws/jobs.json', JSON.stringify({ jobs: [], meta: {} }));
php.writeFile(D + '/ws/usage.json', '{}');
await setSettings({});
const W = (doName, body, key = WKEY, method = 'POST') => {
  const hdr = key === null ? {} : { 'X-WS-Key': key };
  return method === 'GET'
    ? new Client('worker').get('/studio/ws-worker.php?do=' + doName + (body ? '&' + new URLSearchParams(body).toString() : ''), hdr)
    : new Client('worker').post('/studio/ws-worker.php?do=' + doName, Object.assign({ do: doName }, body || {}), hdr);
};
r = await L('generate', { page: '1', takes: '2' }, C); const JA = r.json && r.json.job && r.json.job.id;
r = await L('generate', { page: '2', takes: '2' }, C); const JB = r.json && r.json.job && r.json.job.id;
check('two jobs queued (A page 1 with a ref, B page 2)', !!JA && !!JB && usageToday().users[LT_ID].gens === 4, [JA, JB]);

r = await W('claim', { worker: 'w1' }, 'wrong-key-wrong-key-wrong-key-xx', 'GET');
check('worker: wrong key -> 403', r.status === 403 && r.json && r.json.ok === false, short(r));
r = await W('claim', { worker: 'w1' }, null, 'GET');
check('worker: no key -> 403', r.status === 403, short(r));
r = await W('claim', { worker: 'w1', key: WKEY }, null, 'GET');
check('worker: key in the query string -> 403', r.status === 403, short(r));
r = await W('claim', { worker: 'w1' }, WKEY.slice(0, 10), 'GET');
check('worker: short key -> 403', r.status === 403, short(r));
r = await W('claim', { worker: 'w1' }, WKEY, 'GET');
const claimA = r.json;
check('claim -> oldest queued job (A) with signed ref URLs', r.status === 200 && claimA.job && claimA.job.id === JA && claimA.job.aspect === '9:16' && /Injected prompt from Claude/.test(claimA.job.prompt)
  && claimA.refs.length === 1 && claimA.refs[0].file === REF2 && /ws-worker\.php\?do=refimg&p=lt-made-comic&f=[a-f0-9]{10}\.png&exp=\d+&sig=[a-f0-9]{64}$/.test(claimA.refs[0].url), short(r));
const refUrl = new URL(claimA.refs[0].url);
const refPath = '/studio/ws-worker.php' + refUrl.search;
r = await new Client('anon').get(refPath);
check('refimg with a valid signature -> image bytes, no key needed', r.status === 200 && r.ctype === 'image/png' && Buffer.from(r.bytes).length === (php.readFileAsBuffer(`/www/studio/uploads/${C}/${REF2}`)).length, [r.status, r.ctype]);
const sp = refUrl.searchParams;
const sigFlip = sp.get('sig').slice(0, -1) + (sp.get('sig').endsWith('0') ? '1' : '0');
r = await new Client('anon').get(`/studio/ws-worker.php?do=refimg&p=${C}&f=${sp.get('f')}&exp=${sp.get('exp')}&sig=${sigFlip}`);
check('refimg tampered signature -> 403', r.status === 403, short(r));
const KH = sha256(WKEY);
const signed = (p, f, exp) => createHmac('sha256', KH).update(`${p}|${f}|${exp}`).digest('hex');
let expPast = Math.floor(Date.now() / 1000) - 5;
r = await new Client('anon').get(`/studio/ws-worker.php?do=refimg&p=${C}&f=${sp.get('f')}&exp=${expPast}&sig=${signed(C, sp.get('f'), expPast)}`);
check('refimg expired signature -> 403', r.status === 403, short(r));
let expFar = Math.floor(Date.now() / 1000) + 7200 + 3600;
r = await new Client('anon').get(`/studio/ws-worker.php?do=refimg&p=${C}&f=${sp.get('f')}&exp=${expFar}&sig=${signed(C, sp.get('f'), expFar)}`);
check('refimg expiry too far ahead -> 403', r.status === 403, short(r));
r = await new Client('anon').get(`/studio/ws-worker.php?do=refimg&p=gamma-comic&f=g1.png&exp=${sp.get('exp')}&sig=${sp.get('sig')}`);
check('refimg signature reused for another file -> 403', r.status === 403, short(r));

r = await W('claim', { worker: 'w2' }, WKEY, 'GET');
check('single flight: second worker -> busy', r.status === 200 && r.json.job === null && r.json.reason === 'busy', short(r));
r = await W('claim', { worker: 'w1' });
check('same worker re-claims -> resumed A', r.status === 200 && r.json.job && r.json.job.id === JA && r.json.resumed === true, short(r));
r = await W('submit_ok', { job: JA }, WKEY, 'GET');
check('submit_ok via GET -> 405', r.status === 405, short(r));
r = await W('submit_ok', { job: JA });
check('submit_ok first -> ok', r.status === 200 && r.json.ok === true, short(r));
r = await W('submit_ok', { job: JA });
check('submit_ok again at once -> wait (minGapSec 20)', r.status === 200 && r.json.ok === false && r.json.wait > 0 && r.json.wait <= 20, short(r));
r = await W('heartbeat', { job: JA, note: 'generating take 1' });
check('heartbeat -> ok, keep going', r.status === 200 && r.json.ok && r.json.stop === false && readJson(D + '/ws/jobs.json').jobs.find(j => j.id === JA).note === 'generating take 1', short(r));
r = await W('heartbeat', { job: 'wsj_nope' });
check('heartbeat unknown job -> stop', r.json && r.json.stop === true, short(r));
r = await W('take_failed', { job: JA, reason: 'content filter' });
check('take_failed -> failed 1', r.status === 200 && r.json.ok && r.json.failed === 1, short(r));

for (const [label, url, re] of [
  ['http://', 'http://img.cloudfront.net/a.png', /https/], ['IPv4 host', 'https://93.184.216.34/a.png', /host not allowed/],
  ['IPv6 host', 'https://[::1]/a.png', /host not allowed/], ['non-allowlisted host', 'https://evil.example.com/a.png', /host not allowed: evil\.example\.com/],
  ['suffix trick', 'https://cloudfront.net.evil.com/a.png', /host not allowed/], ['credentials', 'https://u:p@img.cloudfront.net/a.png', /credentials/],
  ['non-443 port', 'https://img.cloudfront.net:8443/a.png', /port/], ['file://', 'file:///etc/passwd', /https/], ['empty', '', /https/]]) {
  r = await W('ingest_url', { job: JA, url });
  check(`ingest_url rejects ${label}`, r.status === 400 && r.json && r.json.ok === false && re.test(r.json.error), short(r));
}
php.writeFile(FAKE_DL, FAKE_PNG);
r = await W('ingest_url', { job: JA, url: 'https://fake-test.cloudfront.net/out/1.png', gen: 'gen-1' });
const ING1 = r.json && r.json.file;
const rowIng = (readJson(D + `/images-${C}.json`) || []).find(m => m.file === ING1);
check('ingest_url (stubbed CDN) -> stored under Page 01 with job + refs_used', r.status === 200 && r.json.ok && r.json.done === 1 && rowIng && rowIng.group === 'Page 01' && rowIng.wsJob === JA
  && rowIng.tags.includes('ws-gen') && rowIng.refs_used.length === 1 && exists(`/www/studio/uploads/${C}/${ING1}`), [short(r), rowIng]);
r = await W('ingest_url', { job: JA, url: 'https://fake-test.cloudfront.net/out/1.png', gen: 'gen-1' });
check('ingest_url same gen again -> duplicate, not stored twice', r.status === 200 && r.json.duplicate === true && (readJson(D + `/images-${C}.json`) || []).filter(m => m.wsJob === JA).length === 1, short(r));
r = await W('ingest_url', { job: JA, url: 'https://fake-test.cloudfront.net/out/2.png', gen: 'gen-2' });
check('ingest_url second take -> done 2', r.status === 200 && r.json.done === 2, short(r));
r = await W('ingest_url', { job: JA, url: 'https://fake-test.cloudfront.net/out/3.png', gen: 'gen-3' });
check('ingest_url beyond takes -> 409', r.status === 409, short(r));
r = await W('done', { job: JA, status: 'done' });
const chatA = readJson(D + `/ws/chat-${C}.json`).msgs;
check('done A -> done, nothing to release, ✅ chat line', r.status === 200 && r.json.status === 'done' && r.json.released === 0 && chatA.some(m => m.role === 'system' && /Page 1: 2 new takes landed/.test(m.text))
  && usageToday().users[LT_ID].gens === 4, [short(r), usageToday()]);
r = await W('done', { job: JA, status: 'done' });
check('done twice -> already', r.status === 200 && r.json.already === true, short(r));
r = await W('ingest_url', { job: JA, url: 'https://fake-test.cloudfront.net/out/4.png', gen: 'gen-4' });
check('ingest_url on a finished job -> 409', r.status === 409, short(r));
st = (await lt.get(`/studio/ws-api.php?do=state&p=${C}`)).json;
check('workspace state shows job A done 2/2 and page 1 takes', st.jobs.find(j => j.id === JA).status === 'done' && st.jobs.find(j => j.id === JA).done === 2 && pg(1).takes === 3, [st.jobs.find(j => j.id === JA), pg(1)]);

r = await W('claim', { worker: 'w1' });
check('claim -> job B', r.status === 200 && r.json.job && r.json.job.id === JB && r.json.refs.length === 0, short(r));
{ // the worker went quiet 1000 s ago
  const j = readJson(D + '/ws/jobs.json');
  const x = j.jobs.find(y => y.id === JB);
  x.heartbeatAt = Math.floor(Date.now() / 1000) - 1000; x.claimedAt = new Date(Date.now() - 1100e3).toISOString();
  php.writeFile(D + '/ws/jobs.json', JSON.stringify(j));
}
r = await W('claim', { worker: 'w2' });
const jb = readJson(D + '/ws/jobs.json').jobs.find(y => y.id === JB);
check('stale running job (>15 min) is re-queued and re-claimed', r.status === 200 && r.json.job && r.json.job.id === JB && r.json.resumed === false && jb.attempts === 1 && jb.worker === 'w2' && jb.status === 'running', [short(r), jb]);
r = await W('take_failed', { job: JB, reason: 'blocked' });
r = await W('take_failed', { job: JB, reason: 'blocked' });
r = await W('done', { job: JB, status: 'done' });
check('done B with nothing landed -> error, releases 2, ⚠ chat line', r.status === 200 && r.json.status === 'error' && r.json.released === 2 && usageToday().users[LT_ID].gens === 2
  && readJson(D + `/ws/chat-${C}.json`).msgs.some(m => /Page 2: generation stopped/.test(m.text)), [short(r), usageToday()]);

r = await L('generate', { page: '3', takes: '1' }, C); const JC = r.json && r.json.job && r.json.job.id;
r = await W('claim', { worker: 'w1' });
check('claim C', r.json && r.json.job && r.json.job.id === JC, short(r));
r = await L('cancel', { job: JC }, C);
check('lt cancels a running job -> stop requested', r.status === 200 && readJson(D + '/ws/jobs.json').jobs.find(j => j.id === JC).stopRequested === true, short(r));
r = await W('heartbeat', { job: JC });
check('heartbeat after cancel -> stop', r.json && r.json.stop === true, short(r));
r = await W('submit_ok', { job: JC });
check('submit_ok after cancel -> stop', r.json && r.json.ok === false && r.json.stop === true, short(r));
r = await W('done', { job: JC, status: 'done' });
check('done after cancel -> cancelled, quota back', r.json && r.json.status === 'cancelled' && r.json.released === 1 && usageToday().users[LT_ID].gens === 2, [short(r), usageToday()]);

r = await W('cooldown', { minutes: '2', reason: 'rate limited' });
check('cooldown -> until', r.status === 200 && r.json.ok && r.json.until > Date.now() / 1000, short(r));
r = await L('generate', { page: '3', takes: '1' }, C); const JD = r.json && r.json.job && r.json.job.id;
r = await W('claim', { worker: 'w1' });
check('claim during cooldown -> reason cooldown', r.json && r.json.job === null && r.json.reason === 'cooldown' && r.json.retryAfter > 0, short(r));
r = await W('status', null, WKEY, 'GET');
check('status -> counts + not claimable during cooldown', r.status === 200 && r.json.ok && r.json.counts.queued === 1 && r.json.counts.done === 1 && r.json.claimable === false, short(r));
{ const j = readJson(D + '/ws/jobs.json'); j.meta.cooldownUntil = 0; php.writeFile(D + '/ws/jobs.json', JSON.stringify(j)); }
await setSettings({ workerEnabled: '0' });
r = await W('claim', { worker: 'w1' });
check('worker disabled in team settings -> reason disabled', r.json && r.json.job === null && r.json.reason === 'disabled', short(r));
await setSettings({});
r = await W('claim', { worker: 'w1' });
check('worker re-enabled -> claims D', r.json && r.json.job && r.json.job.id === JD, short(r));
r = await W('cooldown', { minutes: 'abc' });
check('cooldown bad minutes -> 400', r.status === 400, short(r));
r = await W('nonsense', {});
check('unknown verb -> 400', r.status === 400, short(r));

// =================================================================================================
section('REGRESSION: owner / collab still behave as before');
r = await owner.get('/studio/img.php?p=gamma-comic&f=g1.png');
check('owner img.php any comic -> 200', r.status === 200 && r.ctype === 'image/png', [r.status]);
r = await owner.get('/studio/img.php?p=gamma-comic&f=g1.png&t=1');
check('owner img.php thumb -> 200', r.status === 200, [r.status]);
r = await owner.get('/studio/img.php?p=gamma-comic&f=..%2Fx.png');
check('owner img.php traversal -> 404', r.status === 404, [r.status]);
r = await owner.get('/studio/img.php?p=gamma-comic&f=missing.png');
check('owner img.php missing file -> 404', r.status === 404, [r.status]);
r = await owner.get('/studio/index.php');
check('owner index.php lists all 4 projects', r.status === 200 && ['Alpha Comic', 'Beta Comic', 'Gamma &lt;b&gt;Comic&lt;/b&gt;', 'Lt Made Comic'].every(n => r.text.includes(n)), short(r));
r = await owner.get('/studio/ws.php');
check('owner ws.php lists every comic (unconfined)', r.status === 200 && r.text.includes('Gamma') && r.text.includes('Alpha Comic'), short(r));
r = await owner.post('/studio/index.php', { csrf: OWN_CSRF, do: 'create', name: 'Owner Legacy Project' });
check('owner index.php create project (legacy path) -> 302 project.php', r.status === 302 && /project\.php\?p=owner-legacy-project/.test(r.loc), short(r));
r = await collab.get('/studio/img.php?p=alpha-comic&f=p1b.png');
check('collab img.php -> 200', r.status === 200, [r.status]);
r = await collab.get('/studio/login.php?do=logout');
check('collab logout -> 302 login.php', r.status === 302 && r.loc === 'login.php', short(r));
r = await collab.get('/studio/index.php');
check('after logout index.php -> 302 login.php', r.status === 302 && r.loc === 'login.php', short(r));
r = await lt.get('/studio/login.php');
check('lieutenant on login.php -> bounced (index.php -> ws.php)', r.status === 302, short(r));
r = await lt.get('/studio/login.php?do=logout');
check('lieutenant logout works', r.status === 302 && r.loc === 'login.php', short(r));
r = await lt.get('/studio/ws-api.php?do=state&p=alpha-comic');
check('after lieutenant logout -> 401', r.status === 401, short(r));

section('PHP warnings / notices');
check('no PHP warnings, notices or fatals in any response', diag.length === 0, diag.slice(0, 20).join('\n     '));

console.log(`\n${pass} passed, ${fail} failed` + (fail ? '\nFailed:\n  - ' + failures.join('\n  - ') : ''));
process.exit(fail ? 1 : 0);
