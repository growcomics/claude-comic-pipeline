<?php
// Studio bridge — lets a Claude Code session (the "AI organizer", like
// comic-folder-organizer) pull a project's draft images and write ratings /
// grouping / cover back. KEY-GATED (shared secret in data/bridge.json) so it
// works without a browser login. The key is rotatable by editing bridge.json.
//   GET  bridge.php?key=..&do=projects
//   GET  bridge.php?key=..&do=images&p=<id>
//   GET  bridge.php?key=..&do=img&p=<id>&f=<file>[&t=1]      -> {b64}
//   POST bridge.php  key,do=write,p,decisions=<json>[,cover] -> writes ratings
declare(strict_types=1);
require_once __DIR__ . '/inc/boot.php';
header('Content-Type: application/json');
header('X-Robots-Tag: noindex');
function bout($a){ echo json_encode($a); exit; }

// Normalize a refs_used payload (the references a generated panel was built from) into a
// safe, capped list stored on image metadata. Accepts a JSON string OR an already-decoded
// array. Each item -> {file?,label?,kind?,src?,url?}. A bare string becomes {label}.
// Renders in the review detail view (studio `file` -> thumbnail; otherwise a labeled chip,
// with an external `url` link for Flow input refs). See studio/review.php.
function ck_parse_refs_used($raw): array {
    $arr = is_array($raw) ? $raw : json_decode((string)$raw, true);
    if (!is_array($arr)) return [];
    $out = [];
    foreach ($arr as $it) {
        if (is_string($it)) { $it = ['label' => $it]; }
        if (!is_array($it)) continue;
        $e = [];
        $file = basename((string)($it['file'] ?? ''));
        if ($file !== '' && preg_match('/^[A-Za-z0-9._-]+$/', $file)) $e['file'] = mb_substr($file, 0, 120);
        $label = trim((string)($it['label'] ?? '')); if ($label !== '') $e['label'] = mb_substr($label, 0, 120);
        $kind = (string)($it['kind'] ?? ''); if ($kind !== '') $e['kind'] = mb_substr($kind, 0, 24);
        $src = (string)($it['src'] ?? ''); if ($src !== '') $e['src'] = mb_substr($src, 0, 16);
        $url = trim((string)($it['url'] ?? '')); if ($url !== '' && preg_match('#^https?://#i', $url)) $e['url'] = mb_substr($url, 0, 400);
        if ($e) $out[] = $e;
        if (count($out) >= 24) break;
    }
    return $out;
}

define('BRIDGE_FILE', SDATA . '/bridge.json');
$cfg = s_read(BRIDGE_FILE, []);
$key = (string)($cfg['key'] ?? '');
$given = (string)($_POST['key'] ?? $_GET['key'] ?? ($_SERVER['HTTP_X_BRIDGE_KEY'] ?? ''));
if ($key === '' || strlen($given) < 16 || !hash_equals($key, $given)) { http_response_code(403); bout(['ok'=>false,'error'=>'bad key']); }

$do = $_POST['do'] ?? $_GET['do'] ?? '';
if ($do === 'projects') bout(['ok'=>true,'projects'=>projects_all()]);

$id = preg_replace('/[^a-z0-9-]/','',(string)($_POST['p'] ?? $_GET['p'] ?? ''));
// Verbs that don't operate on a single named project (worker queue verbs claim/heartbeat/done
// span all projects; ingest_init creates one). genspec IS project-scoped, so it stays gated below.
$noProjVerbs = ['ingest_init','ingest','ingest_ref','claim','heartbeat','done','jobs'];
if (!in_array($do, $noProjVerbs, true) && (!$id || !project_get($id))) bout(['ok'=>false,'error'=>'unknown project']);

if ($do === 'images') bout(['ok'=>true,'project'=>project_get($id),'images'=>images_all($id)]);

if ($do === 'img') {
    $f = basename((string)($_GET['f'] ?? $_POST['f'] ?? ''));
    $p = project_dir($id) . (empty($_GET['t']) && empty($_POST['t']) ? '' : '/thumb') . '/' . $f;
    if (!is_file($p)) $p = project_dir($id) . '/' . $f;
    if (!is_file($p)) bout(['ok'=>false,'error'=>'no file']);
    bout(['ok'=>true,'file'=>$f,'b64'=>base64_encode((string)file_get_contents($p))]);
}

if ($do === 'write') {
    $decs = json_decode((string)($_POST['decisions'] ?? '[]'), true) ?: [];
    $meta = images_all($id);
    $byfile = []; foreach ($meta as $k=>$m) $byfile[$m['file']] = $k;
    $n = 0;
    foreach ($decs as $d) {
        $f = $d['file'] ?? ''; if (!isset($byfile[$f])) continue;
        $k = $byfile[$f];
        if (isset($d['rating']) && in_array($d['rating'], RATINGS, true)) $meta[$k]['rating'] = $d['rating'];
        if (array_key_exists('accepted', $d)) $meta[$k]['accepted'] = (bool)$d['accepted'];
        if (isset($d['group'])) $meta[$k]['group'] = mb_substr((string)$d['group'], 0, 60);
        $n++;
    }
    images_save($id, $meta);
    $cover = basename((string)($_POST['cover'] ?? ''));
    if ($cover !== '') { $all = projects_all(); foreach ($all as &$pp) if (($pp['id']??'')===$id) $pp['cover'] = $cover; unset($pp); projects_save($all); }
    bout(['ok'=>true,'updated'=>$n]);
}
// ---- ingest (used by the Flow → Studio extension) ----
// resolve or create a project by name, return its id
if ($do === 'ingest_init') {
    $name = trim((string)($_POST['project'] ?? $_GET['project'] ?? ''));
    if ($name === '') bout(['ok'=>false,'error'=>'no project name']);
    // new=1 → always create a FRESH section (each Flow→Studio batch gets its own
    // project). Otherwise resolve an existing project by id/name = "append to".
    $forceNew = !empty($_POST['new']) || !empty($_GET['new']);
    $all = projects_all(); $pid = '';
    if (!$forceNew) {
        foreach ($all as $p) if (($p['id']??'')===$name || strcasecmp((string)($p['name']??''),$name)===0) { $pid=$p['id']; break; }
    }
    if ($pid === '') {
        $disp = mb_substr($name, 0, 80);
        if ($forceNew) {                                    // timestamp the section so it's unique + self-documenting
            $disp .= ' · ' . date('M j, H:i');
            $lc = array_map(fn($p)=>strtolower((string)($p['name']??'')), $all);
            if (in_array(strtolower($disp), $lc, true)) { $k=2; while (in_array(strtolower($disp.' #'.$k), $lc, true)) $k++; $disp .= ' #'.$k; }
        }
        $base = slugify($name); $pid=$base; $k=2; $taken=array_column($all,'id');
        while (in_array($pid,$taken,true)) $pid=$base.'-'.$k++;
        array_unshift($all, ['id'=>$pid,'name'=>$disp,'status'=>'active','stage'=>'page-build',
            'tags'=>[],'notes'=>'','cover'=>null,'created'=>date('c'),'updated'=>date('c')]);
        projects_save($all);
    }
    bout(['ok'=>true,'project'=>$pid]);
}
// store one uploaded image into a project (multipart field 'file')
if ($do === 'ingest') {
    $pid = preg_replace('/[^a-z0-9-]/','',(string)($_POST['p'] ?? ''));
    if ($pid==='' || !project_get($pid)) bout(['ok'=>false,'error'=>'unknown project']);
    $f = $_FILES['file'] ?? null;
    if (!$f || ($f['error'] ?? 1) !== UPLOAD_ERR_OK || !is_uploaded_file($f['tmp_name'])) bout(['ok'=>false,'error'=>'no file']);
    if (($f['size'] ?? 0) > MAX_BYTES) bout(['ok'=>false,'error'=>'too big']);
    $orig = (string)($_POST['orig'] ?? $f['name'] ?? 'flow.png');
    $res = store_image($f['tmp_name'], $orig, $pid);
    if (!$res) bout(['ok'=>false,'error'=>'store failed (unsupported image?)']);
    $meta = images_all($pid);
    $seq = (int)($_POST['seq'] ?? count($meta));
    // generation key: identical Flow prompt (or gen id) = same beat. Auto-group on the way in.
    $gen = trim((string)($_POST['gen'] ?? ''));
    $promptRaw = trim((string)($_POST['prompt'] ?? ''));
    $genkey = $promptRaw !== '' ? 'p:' . substr(sha1(mb_strtolower(preg_replace('/\s+/', ' ', $promptRaw))), 0, 16)
            : ($gen !== '' ? 'g:' . $gen : '');
    // optional lineage: a worker landing a DERIVED version (iterative refinement) passes the
    // parent file it edited from. We chain it under that parent, in the parent's beat, rather
    // than auto-numbering a fresh Beat. See studio/docs/ITERATIVE-REFINEMENT.md.
    $parentF = basename((string)($_POST['parent'] ?? ''));
    $lineage = []; $lineGroup = null;
    if ($parentF !== '') {
        foreach ($meta as $mx) if (($mx['file'] ?? '') === $parentF) {
            $lineGroup = (string)($mx['group'] ?? '');
            $root = (string)($mx['root'] ?? ''); if ($root === '') $root = $parentF;
            $lineage = ['parent'=>$parentF, 'root'=>$root, 'ver'=>((int)($mx['ver'] ?? 1)) + 1, 'derived'=>true,
                        'adjust'=>mb_substr(trim((string)($_POST['adjust'] ?? '')), 0, 1000)];
            $genkey = (string)($mx['genkey'] ?? '');            // inherit parent's genkey so "Group similar" keeps the chain together
            break;
        }
    }
    $grp = '';
    if ($lineGroup !== null) {
        $grp = $lineGroup;                                  // derived version stays in its parent's beat
    } elseif ($genkey !== '') {
        foreach ($meta as $m) if (($m['genkey'] ?? '') === $genkey && ($m['group'] ?? '') !== '') { $grp = $m['group']; break; }
        if ($grp === '') { $mx = 0; foreach ($meta as $m) if (preg_match('/(\d+)/', (string)($m['group'] ?? ''), $z)) $mx = max($mx, (int)$z[1]); $grp = 'Beat ' . ($mx + 1); }
    }
    // prompt + refs-used: store the actual text + the references the panel was built from, so the
    // review detail view can show "what built this" (the owner's "see the references used" ask).
    // Previously only the genkey HASH of the prompt was kept — the text itself was unrecoverable.
    $extra = [];
    if ($promptRaw !== '') $extra['prompt'] = mb_substr($promptRaw, 0, 2000);
    $refsUsed = ck_parse_refs_used($_POST['refs_used'] ?? '');
    if ($refsUsed) $extra['refs_used'] = $refsUsed;
    $meta[] = array_merge(['file'=>$res['file'],'orig'=>mb_substr($orig,0,120),'rating'=>'unrated','accepted'=>false,'group'=>$grp,'tags'=>[],'ts'=>time()+$seq,'gen'=>$gen,'genkey'=>$genkey], $extra, $lineage);
    images_save($pid, $meta);
    bout(['ok'=>true,'count'=>count($meta),'group'=>$grp]);
}

// ---- enrich: backfill prompt + refs_used onto already-ingested panels --------
// Panels imported before prompt/refs capture existed (e.g. the muller chapter) carry only
// the genkey HASH of their prompt — no text, no input refs. The Flow auto-sync can re-read the
// project and POST the recovered {gen, prompt, refs_used} here to fill those fields in, so the
// review detail view shows the real prompt + the references used. Matched by gen (Flow workflow
// id) first, then genkey, then file. Only fills MISSING fields unless force=1 (no clobber).
//   POST bridge.php  key, do=enrich, p=<id>, items=<json [{gen|genkey|file, prompt?, refs_used?}]> [, force=1]
if ($do === 'enrich') {
    $items = json_decode((string)($_POST['items'] ?? '[]'), true);
    if (!is_array($items)) bout(['ok'=>false,'error'=>'bad items']);
    $force = !empty($_POST['force']);
    $meta = images_all($id);
    $byGen = []; $byKey = []; $byFile = [];
    foreach ($meta as $k => $m) {
        if (($g = (string)($m['gen'] ?? '')) !== '') $byGen[$g][] = $k;
        if (($gk = (string)($m['genkey'] ?? '')) !== '') $byKey[$gk][] = $k;
        if (($f = (string)($m['file'] ?? '')) !== '') $byFile[$f] = $k;
    }
    $touched = 0; $changed = false;
    foreach ($items as $it) {
        if (!is_array($it)) continue;
        $gen = trim((string)($it['gen'] ?? '')); $gk = trim((string)($it['genkey'] ?? '')); $file = basename((string)($it['file'] ?? ''));
        $targets = [];
        if      ($gen  !== '' && isset($byGen[$gen]))  $targets = $byGen[$gen];
        elseif  ($gk   !== '' && isset($byKey[$gk]))   $targets = $byKey[$gk];
        elseif  ($file !== '' && isset($byFile[$file])) $targets = [$byFile[$file]];
        if (!$targets) continue;
        $prompt = mb_substr(trim((string)($it['prompt'] ?? '')), 0, 2000);
        $refs   = ck_parse_refs_used($it['refs_used'] ?? '');
        foreach ($targets as $k) {
            $did = false;
            if ($prompt !== '' && ($force || empty($meta[$k]['prompt'])))    { $meta[$k]['prompt'] = $prompt; $did = true; }
            if ($refs   && ($force || empty($meta[$k]['refs_used'])))        { $meta[$k]['refs_used'] = $refs; $did = true; }
            if ($did) { $changed = true; $touched++; }
        }
    }
    if ($changed) images_save($id, $meta);
    bout(['ok'=>true,'enriched'=>$touched]);
}

// ---- ingest_ref: store an image AND register it as a project REFERENCE -----
// Lets a Claude Code session running the reference-gathering skill push real-photo
// (or DAZ-converted) LOCATION plates straight into a project's reference set as
// kind=scene, so the references workspace (refs.php) shows them and the production
// guide (shots.php) attaches them to every panel at that location — the env-ref-every-
// panel lesson. Closes the "AI-only backgrounds look too AI" gap: source real photos,
// restyle to the project's CGI look, drop them in as scene refs, insert the character.
// Mirrors creator.php's `uploadref` EXACTLY (a gallery entry tagged isref so it stays
// OFF the live-panels board + a $c['refs'] entry) so refs.php renders it with no change.
//   POST bridge.php  key, do=ingest_ref, p=<id>, file=<multipart image>,
//        [kind=scene|face|body|view|prop]  (default scene)
//        [char=<location group, e.g. "Commercial gym">]   (match key for shots.php)
//        [label=<plate/view, e.g. "weight floor wide">]
//        [status=approved|pending]  (default pending; the chosen CGI plate -> approved)
//        [role=cgi-plate|real-source]  (informational provenance tag)
//        [prov=<source URL / license / author / QA note>]
//        [lock=1]  (only if status=approved AND the project is already locked:
//                   append to refsLockedSet so the worker picks it up immediately)
if ($do === 'ingest_ref') {
    $pid = preg_replace('/[^a-z0-9-]/','',(string)($_POST['p'] ?? ''));
    if ($pid==='' || !project_get($pid)) bout(['ok'=>false,'error'=>'unknown project']);
    $f = $_FILES['file'] ?? null;
    if (!$f || ($f['error'] ?? 1) !== UPLOAD_ERR_OK || !is_uploaded_file($f['tmp_name'])) bout(['ok'=>false,'error'=>'no file']);
    if (($f['size'] ?? 0) > MAX_BYTES) bout(['ok'=>false,'error'=>'too big']);
    $orig = (string)($_POST['orig'] ?? $f['name'] ?? 'scene.jpg');
    $res = store_image($f['tmp_name'], $orig, $pid);
    if (!$res) bout(['ok'=>false,'error'=>'store failed (unsupported image?)']);
    // gallery meta — tagged isref so it stays OFF the live-panels board (same as uploadref)
    $meta = images_all($pid);
    $meta[] = ['file'=>$res['file'],'orig'=>mb_substr($orig,0,120),'rating'=>'good','accepted'=>false,
               'group'=>'','tags'=>[],'isref'=>true,'ts'=>time()];
    images_save($pid, $meta);
    // build the reference entry (mirror uploadref's shape; src=gathered marks the source)
    $kind   = in_array(($_POST['kind'] ?? ''), ['face','body','view','scene','prop'], true) ? (string)$_POST['kind'] : 'scene';
    $status = (($_POST['status'] ?? '') === 'approved') ? 'approved' : 'pending';
    $role   = mb_substr(trim((string)($_POST['role'] ?? '')), 0, 24);
    $prov   = mb_substr(trim((string)($_POST['prov'] ?? '')), 0, 1200);
    $ref = ['id'=>nid(), 'file'=>$res['file'],
            'char'=>mb_substr(trim((string)($_POST['char'] ?? '')), 0, 40),
            'kind'=>$kind,
            'label'=>mb_substr(trim((string)($_POST['label'] ?? '')), 0, 80),
            'status'=>$status, 'src'=>'gathered', 'ts'=>time()];
    if ($role !== '') $ref['role'] = $role;
    if ($prov !== '') $ref['prov'] = $prov;
    $lock = !empty($_POST['lock']) && $status === 'approved';
    $cf = SDATA . '/creator-' . $pid . '.json';     // $pid already sanitized above
    $tot = s_with_lock($cf, function($c) use ($ref, $lock) {
        if (!is_array($c)) $c = [];
        $c['refs'] = array_values((array)($c['refs'] ?? []));
        $c['refs'][] = $ref;
        // if the project is ALREADY locked, optionally make this ref live for the worker NOW
        if ($lock && !empty($c['refsLocked'])) {
            $set = (array)($c['refsLockedSet'] ?? []);
            if (!in_array($ref['file'], $set, true)) { $set[] = $ref['file']; $c['refsLockedSet'] = array_values($set); }
        }
        return ['data'=>$c, 'result'=>count($c['refs'])];
    });
    bout(['ok'=>true,'file'=>$res['file'],'refId'=>$ref['id'],'kind'=>$kind,'status'=>$status,
          'refsTotal'=>(int)$tot,'lockedNow'=>$lock]);
}

// ---- annotate (AI analysis pass): per-image caption / defects / tier / notes / tags ----
if ($do === 'annotate') {
    $notes = json_decode((string)($_POST['notes'] ?? '[]'), true) ?: [];
    $meta = images_all($id);
    $byfile = []; foreach ($meta as $k=>$m) $byfile[$m['file']] = $k;
    $n = 0;
    foreach ($notes as $note) {
        $f = $note['file'] ?? ''; if (!isset($byfile[$f])) continue;
        $k = $byfile[$f];
        $meta[$k]['analysis'] = [
            'caption' => mb_substr((string)($note['caption'] ?? ''), 0, 300),
            'defects' => array_values(array_slice(array_map(fn($d)=>mb_substr((string)$d,0,60), (array)($note['defects'] ?? [])), 0, 12)),
            // QA-scan fields: same shape creator.php's server-side 🔎 QA scan writes, so a
            // Claude-Code-driven annotate and the in-app QA scan populate the an-tag badge
            // identically. verdict: pass|warn|fail; people = human-figure count (duplicate/extra cue).
            'verdict' => in_array($note['verdict'] ?? '', ['pass','warn','fail'], true) ? (string)$note['verdict'] : '',
            'people'  => isset($note['people']) && is_numeric($note['people']) ? (int)$note['people'] : null,
            'tier'    => mb_substr((string)($note['tier'] ?? ''), 0, 60),
            'notes'   => mb_substr((string)($note['notes'] ?? ''), 0, 800),
            'src'     => mb_substr((string)($note['src'] ?? 'annotate'), 0, 20),
            'at'      => date('c'),
        ];
        if (isset($note['tags'])) $meta[$k]['tags'] = array_values(array_slice(array_map(fn($t)=>mb_substr((string)$t,0,40), (array)$note['tags']), 0, 12));
        $n++;
    }
    images_save($id, $meta);
    bout(['ok'=>true,'annotated'=>$n]);
}

// ---- worker (the generation engine) ---------------------------------------
// A Mac-side worker DRIVES generation by polling these key-gated verbs. It pulls
// work off the SAME queue the cockpit's "▶ Queue generation" button fills:
//   jobs      -> read-only snapshot of the queue (optional &status= filter) — worker poll / debugging
//   claim     -> atomically take the oldest OPEN job (open->claimed); FIFO, optional &backend= filter
//   genspec   -> read-only: a project's plan + brief + wardrobe + style + ONLY the LOCKED refs
//   heartbeat -> progress {done,total,note} + liveness; promotes claimed->running; echoes stopRequested + comments
//   done      -> terminal: done | blocked | needs_login | error | stopped (mirrors run-state back to the cockpit)
// Panels are pushed back via the existing `ingest` verb. EVERY job mutation runs inside
// s_with_lock(JOBS_FILE,...) so two poll cycles / two workers can never double-claim & double-spend.
function ck_is_terminal(string $s): bool { return in_array($s, ['done','blocked','needs_login','error','stopped'], true); }
function ck_creator_cfg(string $id): array {
    $f = SDATA . '/creator-' . preg_replace('/[^a-z0-9-]/', '', $id) . '.json';
    return is_file($f) ? s_read($f, []) : [];
}

if ($do === 'jobs') {
    $want = (string)($_POST['status'] ?? $_GET['status'] ?? '');
    $out = [];
    foreach (jobs_all() as $j) {
        if ($want !== '' && ($j['status'] ?? '') !== $want) continue;
        $out[] = ['id'=>$j['id'] ?? '', 'projectId'=>$j['projectId'] ?? '', 'status'=>$j['status'] ?? '',
            'scope'=>$j['scope'] ?? '', 'kind'=>$j['kind'] ?? '', 'backend'=>$j['backend'] ?? '', 'account'=>$j['account'] ?? '',
            'progress'=>$j['progress'] ?? null, 'stopRequested'=>!empty($j['stopRequested']),
            'worker'=>$j['worker'] ?? '', 'heartbeatAt'=>(int)($j['heartbeatAt'] ?? 0), 'createdAt'=>$j['createdAt'] ?? ''];
    }
    bout(['ok'=>true, 'jobs'=>$out, 'now'=>time()]);
}

if ($do === 'claim') {
    $worker = mb_substr(trim((string)($_POST['worker'] ?? $_GET['worker'] ?? '')), 0, 60); if ($worker === '') $worker = 'worker';
    $want   = (string)($_POST['backend'] ?? $_GET['backend'] ?? '');         // optional: only claim jobs for this backend
    $job = s_with_lock(JOBS_FILE, function($jobs) use ($worker, $want) {
        $pick = null;
        foreach ($jobs as $i => $j) {
            if (($j['status'] ?? '') !== 'open') continue;                  // only un-claimed jobs
            if (!empty($j['stopRequested'])) continue;                      // cancelled before it ever ran
            if ($want !== '' && ($j['backend'] ?? '') !== $want) continue;
            if ($pick === null || ($j['createdAt'] ?? '') < ($jobs[$pick]['createdAt'] ?? '')) $pick = $i;  // oldest = FIFO
        }
        if ($pick === null) return ['result'=>null];
        $jobs[$pick]['status']      = 'claimed';
        $jobs[$pick]['worker']      = $worker;
        $jobs[$pick]['claimedAt']   = date('c');
        $jobs[$pick]['heartbeatAt'] = time();
        return ['data'=>$jobs, 'result'=>$jobs[$pick]];
    });
    bout(['ok'=>true, 'job'=>$job]);                                        // job===null => nothing to do
}

if ($do === 'heartbeat') {
    $jid     = preg_replace('/[^A-Za-z0-9_]/', '', (string)($_POST['job'] ?? $_GET['job'] ?? ''));
    $worker  = mb_substr(trim((string)($_POST['worker'] ?? '')), 0, 60);
    $hasProg = isset($_POST['done']) || isset($_POST['total']) || isset($_POST['note']);
    $pdone   = (int)($_POST['done'] ?? 0); $ptotal = (int)($_POST['total'] ?? 0);
    $pnote   = mb_substr(trim((string)($_POST['note'] ?? '')), 0, 200);
    $ret = s_with_lock(JOBS_FILE, function($jobs) use ($jid, $worker, $hasProg, $pdone, $ptotal, $pnote) {
        foreach ($jobs as &$j) {
            if (($j['id'] ?? '') !== $jid) continue;
            $st = $j['status'] ?? '';
            if (ck_is_terminal($st)) return ['result'=>['found'=>true,'stop'=>true,'status'=>$st,'stopRequested'=>true,'comments'=>$j['comments'] ?? []]];
            if ($st === 'claimed') $j['status'] = 'running';               // first heartbeat promotes claimed -> running
            $j['heartbeatAt'] = time();
            if ($worker !== '') $j['worker'] = $worker;
            if ($hasProg) $j['progress'] = ['done'=>$pdone, 'total'=>$ptotal, 'note'=>$pnote];
            $stop = !empty($j['stopRequested']);
            return ['data'=>$jobs, 'result'=>['found'=>true,'stop'=>$stop,'status'=>$j['status'],'stopRequested'=>$stop,'comments'=>$j['comments'] ?? []]];
        }
        return ['result'=>['found'=>false,'stop'=>true,'status'=>'gone','stopRequested'=>true,'comments'=>[]]];
    });
    bout(['ok'=>true] + $ret);
}

if ($do === 'done') {
    $jid    = preg_replace('/[^A-Za-z0-9_]/', '', (string)($_POST['job'] ?? $_GET['job'] ?? ''));
    $status = (string)($_POST['status'] ?? 'done'); if (!ck_is_terminal($status)) $status = 'done';
    $note   = mb_substr(trim((string)($_POST['note'] ?? '')), 0, 300);
    $pid = '';
    $ok = s_with_lock(JOBS_FILE, function($jobs) use ($jid, $status, $note, &$pid) {
        foreach ($jobs as &$j) {
            if (($j['id'] ?? '') !== $jid) continue;
            $pid = (string)($j['projectId'] ?? '');
            $j['status'] = $status; $j['endedAt'] = date('c'); $j['heartbeatAt'] = time();
            if ($note !== '') { $j['progress'] = $j['progress'] ?? ['done'=>0,'total'=>0,'note'=>'']; $j['progress']['note'] = $note; }
            return ['data'=>$jobs, 'result'=>true];
        }
        return ['result'=>false];
    });
    // mirror terminal state into the cockpit's run.* so the board doesn't show a stale "queued"/"running"
    if ($ok && $pid !== '') {
        $cf = SDATA . '/creator-' . preg_replace('/[^a-z0-9-]/', '', $pid) . '.json';
        if (is_file($cf)) s_with_lock($cf, function($c) use ($status) {
            $c['run'] = $c['run'] ?? []; $c['run']['state'] = $status; $c['run']['stopRequested'] = false; $c['run']['endedAt'] = date('c');
            return ['data'=>$c, 'result'=>true];
        });
    }
    bout(['ok'=>$ok, 'status'=>$status]);
}

if ($do === 'genspec') {
    // read-only: everything the worker needs to generate this project's panels.
    $c = ck_creator_cfg($id);
    $lockedFiles = array_values(array_filter((array)($c['refsLockedSet'] ?? []), 'strlen'));
    $lset = array_flip($lockedFiles);
    $refs = []; $byChar = []; $scenes = []; $props = [];
    foreach ((array)($c['refs'] ?? []) as $r) {
        $file = (string)($r['file'] ?? '');
        if ($file === '' || !isset($lset[$file])) continue;                // ONLY the locked set
        $kind = (string)($r['kind'] ?? 'view'); $char = trim((string)($r['char'] ?? ''));
        $refs[] = ['id'=>$r['id'] ?? '', 'file'=>$file, 'char'=>$char, 'kind'=>$kind, 'label'=>(string)($r['label'] ?? '')];
        if ($kind === 'scene')    $scenes[] = $file;
        elseif ($kind === 'prop') $props[]  = $file;
        elseif ($char !== '')     $byChar[mb_strtolower($char)][] = $file;
    }
    $proj_g = project_get($id);
    bout(['ok'=>true,
        'project'    => ['id'=>$id, 'name'=>$proj_g['name'] ?? $id],
        'locked'     => !empty($c['refsLocked']),
        'style'      => (string)($c['style'] ?? ''),
        'brief'      => (string)($c['brief'] ?? ''),
        'wardrobe'   => (string)($c['wardrobe'] ?? ''),
        'script'     => (string)($c['script'] ?? ''),
        'plan'       => $c['plan'] ?? [],
        'refs'       => $refs,
        'refsByChar' => (object)$byChar,                                    // {} not [] when empty
        'scenes'     => $scenes,
        'props'      => $props,
        'imgBase'    => 'bridge.php?do=img&p=' . rawurlencode($id) . '&f=', // worker GETs each ref's bytes here (with its key)
    ]);
}

bout(['ok'=>false,'error'=>'unknown action']);
