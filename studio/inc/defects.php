<?php
// defects.php — defect-taxonomy helpers + the global defect event log.
//
// Companion to the GENERATED inc/defect-taxonomy.php (regenerate via the pipeline
// repo: skills/comic-production/scripts/gen_defect_taxonomy.py). Canonical taxonomy
// narrative: skills/comic-production/references/DEFECT-REGISTRY.md.
//
// Registry IDs are the SHARED CONTRACT between the ck_ai_qa auto-scan, gg_qa,
// bridge-side gate reports, and human 🏴 flags: every writer logs the same
// id/slug pair into data/defect-log.json, so per-defect frequency stats and the
// defects-per-page trend compare human perception and auto-detection directly.
//
// Markers for DEPLOY-NOTES greps: ck_defect_event ck_defect_norm ck_defect_options DEFECT_LOG_FILE
declare(strict_types=1);

require_once __DIR__ . '/defect-taxonomy.php';

define('DEFECT_LOG_FILE', SDATA . '/defect-log.json');
define('DEFECT_LOG_MAX', 20000);                    // newest N events kept

// Look up a taxonomy row by canonical id ('CAST-01') or slug ('duplicate_character').
// Returns ['id','slug','label','cat','sev','pick'] or null.
function ck_defect_row(string $key): ?array {
    global $DEFECT_TAXONOMY, $DEFECT_ID_BY_SLUG;
    $id = isset($DEFECT_TAXONOMY[$key]) ? $key : ($DEFECT_ID_BY_SLUG[$key] ?? '');
    return $id !== '' ? (['id' => $id] + $DEFECT_TAXONOMY[$id]) : null;
}

// Map a live ck_ai_qa defect type (+ its detail text) to a canonical registry id.
// The scanner's 'anachronism' covers two registry classes: reference-sheet leaks
// normalise to PROP-02 ref_as_object, everything else to PROP-01.
function ck_defect_norm(string $ckType, string $detail = ''): string {
    global $DEFECT_CK_MAP;
    if ($ckType === 'nsfw') return 'WARD-06';                     // gg_qa SFW scan → coverage violation
    if ($ckType === 'anachronism'
        && preg_match('/\b(reference|ref sheet|model[ -]sheet|lineup|face[ -]card|turnaround|inset photo|watermark|figure number|grid line)/i', $detail))
        return 'PROP-02';
    return $DEFECT_CK_MAP[$ckType] ?? 'MISC-00';
}

// Append ONE event to the global defect log (race-safe; trims to newest 20k).
// $e keys: defect (id or slug, required), project, file, src(human|qa|ggqa|gate),
// optional panel, sev(high|med|low), note, by, verdict(pass|warn|fail).
function ck_defect_event(array $e): void {
    $row = ck_defect_row((string)($e['defect'] ?? ''));
    if (!$row) return;
    $ev = [
        'ts'      => date('c'),
        'project' => mb_substr(preg_replace('/[^a-z0-9-]/', '', (string)($e['project'] ?? '')), 0, 60),
        'file'    => basename((string)($e['file'] ?? '')),
        'panel'   => mb_substr((string)($e['panel'] ?? ''), 0, 60),
        'defect'  => $row['id'],
        'slug'    => $row['slug'],
        'sev'     => in_array($e['sev'] ?? '', ['high', 'med', 'low'], true) ? $e['sev'] : '',
        'src'     => in_array($e['src'] ?? '', ['human', 'qa', 'ggqa', 'gate'], true) ? $e['src'] : 'human',
        'by'      => mb_substr((string)($e['by'] ?? ''), 0, 40),
        'note'    => mb_substr(trim((string)($e['note'] ?? '')), 0, 500),
        'verdict' => in_array($e['verdict'] ?? '', ['pass', 'warn', 'fail'], true) ? $e['verdict'] : '',
    ];
    s_with_lock(DEFECT_LOG_FILE, function ($log) use ($ev) {
        if (!is_array($log)) $log = [];
        $log[] = $ev;
        if (count($log) > DEFECT_LOG_MAX) $log = array_slice($log, -DEFECT_LOG_MAX);
        return ['data' => $log, 'result' => true];
    });
}

// Log every defect from one ck_ai_qa / gg_qa analysis result. Prefers the typed
// entries ($an['typed'], added 2026-07-18 alongside the flat labels); falls back
// to parsing the legacy flat strings ("wardrobe drift: ..."). No defects = no events.
function ck_defect_log_analysis(string $project, string $file, string $panel, array $an, string $src): void {
    $verdict = (string)($an['verdict'] ?? '');
    $typed = (array)($an['typed'] ?? []);
    if ($typed) {
        foreach ($typed as $t) {
            if (!is_array($t)) continue;
            ck_defect_event([
                'project' => $project, 'file' => $file, 'panel' => $panel,
                'defect'  => ck_defect_norm((string)($t['type'] ?? ''), (string)($t['detail'] ?? '')),
                'sev'     => (string)($t['sev'] ?? ''), 'src' => $src,
                'note'    => mb_substr((string)($t['detail'] ?? ''), 0, 200), 'verdict' => $verdict,
            ]);
        }
        return;
    }
    foreach ((array)($an['defects'] ?? []) as $lbl) {          // legacy flat labels
        $lbl = trim((string)$lbl); if ($lbl === '') continue;
        $type = str_replace(' ', '_', trim((string)strtok($lbl, ':')));
        ck_defect_event([
            'project' => $project, 'file' => $file, 'panel' => $panel,
            'defect'  => ck_defect_norm($type, $lbl), 'src' => $src,
            'note'    => mb_substr($lbl, 0, 200), 'verdict' => $verdict,
        ]);
    }
}

// <option> markup for the 🏴 flag picker: pick=true rows grouped by category,
// value = canonical id, label = "ID — label". Escaped here; echo raw.
function ck_defect_options(): string {
    global $DEFECT_TAXONOMY, $DEFECT_CATEGORIES;
    $out = '';
    foreach ($DEFECT_CATEGORIES as $cat => $catLabel) {
        $opts = '';
        foreach ($DEFECT_TAXONOMY as $id => $d) {
            if ($d['cat'] !== $cat || empty($d['pick'])) continue;
            $opts .= '<option value="' . h($id) . '">' . h($id . ' — ' . $d['label']) . '</option>';
        }
        if ($opts !== '') $out .= '<optgroup label="' . h($catLabel) . '">' . $opts . '</optgroup>';
    }
    return $out;
}

// ====================================================================
// AI QA SCAN engine — moved here from creator.php on 2026-07-18 so the
// key-gated bridge.php do=qascan shares the exact same engine as the
// cockpit's do=qascan_one. Depends on boot.php (ext_of, ck_stage_*).
// Markers: ck_ai_cfg ck_qa_checklist ck_qa_cast ck_qa_match ck_ai_qa
// ====================================================================

// function_exists guard: during a rolling deploy the OLD creator.php (which still
// declares these at top level, hoisted before this include runs) may load the NEW
// defects.php — the guard makes that window fatal-free in either deploy order.
if (!function_exists('ck_ai_qa')) {

function ck_ai_cfg(): ?array { $f = SDATA . '/ai.json'; if (!is_file($f)) return null; $j = s_read($f, []); return !empty($j['key']) ? $j : null; }

// ---- AI QA SCAN: inspect a GENERATED PANEL for defects ----------------------
// The owner's pain (Beat 48): "QA should have picked up duplicate guys here — a
// defect in the image AND the system." This is the QA pass that catches what
// slipped through. ONE vision call per panel (same pattern as ck_ai_classify);
// returns a structured `analysis` stored on the image's `analysis` field — the
// SAME shape the bridge `annotate` verb writes and the organizer's `an-tag`
// badge reads. Prioritises DUPLICATE characters + unwanted EXTRAS.
function ck_qa_checklist(): string {
    return
      "DUPLICATE CHARACTER — the SAME character appears two or more times in one panel (a cloned / twinned figure). This is the #1 defect to catch.\n"
    . "UNWANTED EXTRA / BACKGROUND PERSON — any human in frame who is not one of the named cast (strangers, crowd, photo-bombers, blurred background people). The cast is fixed: only named characters may appear.\n"
    . "WRONG PEOPLE COUNT — more (or fewer) people than the panel's intended cast.\n"
    . "WOODEN / NEUTRAL FACE ON AN EMOTIONAL BEAT — a flat, dead, expressionless face when the beat calls for emotion (talking, strain, shock, effort, fear).\n"
    . "WARDROBE DRIFT — a character's outfit or colour differs from the intended wardrobe, or changes mid-scene.\n"
    . "ANACHRONISTIC / HALLUCINATED PROP — watches, jewellery, phones or modern objects that do not belong; a reference sheet rendered as a literal in-scene object.\n"
    . "WRONG TRANSFORMATION STAGE — the character is muscular / transformed when this beat should be soft / untransformed (or vice-versa).\n"
    . "MALFORMED ANATOMY — extra or missing fingers / limbs, fused or distorted bodies, broken hands, melted faces.\n"
    . "TEXT / LETTERING ARTIFACT — garbled gibberish text, stray tier labels or metadata baked into the art.";
}
// Distinct named characters for this project (the cast), drawn from the plan +
// the character references (face / body / view). Scenes and props are excluded.
function ck_qa_cast(array $c): array {
    $names = [];
    foreach ((array)($c['plan'] ?? []) as $pg) foreach ((array)($pg['panels'] ?? []) as $pn)
        foreach ((array)($pn['characters'] ?? []) as $nm) { $nm = trim((string)$nm); if ($nm !== '') $names[mb_strtolower($nm)] = $nm; }
    foreach ((array)($c['refs'] ?? []) as $r) {
        $kd = $r['kind'] ?? ''; if ($kd === 'scene' || $kd === 'prop') continue;
        $nm = trim((string)($r['char'] ?? '')); if ($nm !== '') $names[mb_strtolower($nm)] = $nm;
    }
    return array_values($names);
}
// Best-effort: find the PLAN panel a generated image belongs to, for richer
// cast / expression / stage context. Generated panels rarely carry a hard plan
// link, so we only match when a plan panel id token (e.g. "p3-2") appears as a
// whole token in the image's planId / gen field. Returns
// ['panel'=>plan panel, 'stage'=>page stage] or null (-> image-only QA, which
// still catches the owner's duplicate / extra pain against the cast list).
function ck_qa_match(array $c, array $im): ?array {
    $hay = ' ' . (string)($im['planId'] ?? '') . ' ' . (string)($im['gen'] ?? '') . ' ';
    foreach ((array)($c['plan'] ?? []) as $pg) foreach ((array)($pg['panels'] ?? []) as $pn) {
        $pid = trim((string)($pn['id'] ?? '')); if ($pid === '') continue;
        if (preg_match('/(^|[^a-z0-9])' . preg_quote($pid, '/') . '([^a-z0-9]|$)/i', $hay))
            return ['panel' => $pn, 'stage' => ck_stage_key((string)($pg['stage'] ?? ''))];
    }
    return null;
}
// ONE vision call: inspect $imgPath against $ctx (cast names, optional matched
// plan panel, stage, wardrobe). Returns the normalised analysis array (caption,
// defects[] as short strings, verdict pass|warn|fail, people, notes, src) or null.
function ck_ai_qa(string $imgPath, array $ctx): ?array {
    $cfg = ck_ai_cfg(); if (!$cfg || !is_file($imgPath) || !function_exists('curl_init')) return null;
    $data = @file_get_contents($imgPath); if ($data === false) return null;
    $ext = ext_of($imgPath); $mime = $ext==='png'?'image/png':($ext==='webp'?'image/webp':($ext==='gif'?'image/gif':'image/jpeg'));
    $cast = array_values(array_filter(array_map(fn($n)=>trim((string)$n), (array)($ctx['cast'] ?? [])), 'strlen'));
    $sys = 'You are a strict QA inspector for AI-generated comic panels. You are shown ONE generated panel. Find generation DEFECTS — flaws an editor would reject or fix — using this checklist:' . "\n" . ck_qa_checklist() . "\n"
         . 'PRIORITISE the first three (duplicate character, unwanted extra, wrong people count) — those matter most. '
         . 'Count the distinct HUMAN figures in the frame carefully, including blurred, background and partially-cropped people. '
         . 'Reply ONLY with compact JSON, no prose and no markdown fences: {"caption":"<one short sentence of what is shown>","people":<integer count of human figures>,"defects":[{"type":"duplicate_character|extra_person|people_count|wooden_face|wardrobe_drift|anachronism|wrong_stage|anatomy|text_artifact|other","severity":"high|med|low","detail":"<short specific phrase>"}],"verdict":"pass|warn|fail"}. '
         . 'verdict is "fail" if any high-severity defect (especially a duplicate character or an unwanted extra), "warn" for minor defects, "pass" if clean. If you are unsure whether an extra person is a defect, FLAG it — for this QA a false positive is cheaper than the miss it exists to catch. Use an empty defects array for a clean panel.';
    $u = '';
    if ($cast) $u .= 'The ONLY characters allowed in this comic (the named cast) are: ' . implode(', ', $cast) . ". Anyone else in frame is an unwanted extra.\n";
    $pn = $ctx['panel'] ?? null;
    if (is_array($pn)) {
        $want = array_values(array_filter(array_map(fn($x)=>trim((string)$x), (array)($pn['characters'] ?? [])), 'strlen'));
        if ($want) $u .= 'This specific panel should contain ONLY: ' . implode(', ', $want) . ' (' . count($want) . ' character' . (count($want)===1?'':'s') . ").\n";
        if (trim((string)($pn['beat'] ?? '')) !== '')     $u .= 'Intended action: ' . trim((string)$pn['beat']) . "\n";
        if (trim((string)($pn['dialogue'] ?? '')) !== '') $u .= 'A character is SPEAKING here ("' . mb_substr(trim((string)$pn['dialogue']),0,160) . '") — a wooden / neutral face is a defect on this beat.' . "\n";
        $stg = ck_stage_label((string)($ctx['stage'] ?? ''));
        if ($stg !== '') $u .= 'Transformation stage for this beat: ' . $stg . ' — flag the character if their build does not match this stage.' . "\n";
    } else {
        $u .= "No per-panel cast is linked; judge duplicates and extras against the named cast above (or, if none is listed, flag any obviously cloned or out-of-place figure).\n";
    }
    if (trim((string)($ctx['wardrobe'] ?? '')) !== '') $u .= 'Wardrobe continuity note: ' . mb_substr(trim((string)$ctx['wardrobe']),0,300) . "\n";
    $u .= 'Inspect the panel now. JSON only.';
    $payload = json_encode(['model'=>$cfg['model'] ?? 'claude-haiku-4-5', 'max_tokens'=>600, 'system'=>$sys,
        'messages'=>[['role'=>'user','content'=>[
            ['type'=>'image','source'=>['type'=>'base64','media_type'=>$mime,'data'=>base64_encode($data)]],
            ['type'=>'text','text'=>$u]]]]]);
    $ch = curl_init('https://api.anthropic.com/v1/messages');
    curl_setopt_array($ch, [CURLOPT_POST=>true, CURLOPT_RETURNTRANSFER=>true, CURLOPT_TIMEOUT=>45,
        CURLOPT_HTTPHEADER=>['content-type: application/json','anthropic-version: 2023-06-01','x-api-key: '.$cfg['key']],
        CURLOPT_POSTFIELDS=>$payload]);
    $resp = curl_exec($ch); $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE); curl_close($ch);
    if (!$resp || $code >= 400) return null;
    $j = json_decode($resp, true); $txt = $j['content'][0]['text'] ?? '';
    if (preg_match('/\{.*\}/s', $txt, $m)) $txt = $m[0];
    $o = json_decode($txt, true); if (!is_array($o)) return null;
    // normalise the model's structured defects into the stored flat string[] shape
    $defs = []; $typed = []; $hi = 0;
    foreach ((array)($o['defects'] ?? []) as $d) {
        if (is_array($d)) {
            $t = trim((string)($d['type'] ?? '')); $sev = trim((string)($d['severity'] ?? '')); $det = trim((string)($d['detail'] ?? ''));
            $label = ($t !== '' ? str_replace('_', ' ', $t) : 'defect') . ($det !== '' ? ': ' . $det : '');
            if ($sev === 'high') $hi++;
            $typed[] = ['type'=>$t, 'sev'=>$sev, 'detail'=>mb_substr($det, 0, 200)];   // registry-id events (inc/defects.php)
        } else { $label = trim((string)$d); }
        if ($label !== '') $defs[] = mb_substr($label, 0, 60);
    }
    $defs = array_values(array_slice($defs, 0, 12));
    $verdict = in_array($o['verdict'] ?? '', ['pass','warn','fail'], true) ? $o['verdict'] : ($defs ? ($hi ? 'fail' : 'warn') : 'pass');
    $people  = isset($o['people']) && is_numeric($o['people']) ? (int)$o['people'] : null;
    return [
        'caption' => mb_substr(trim((string)($o['caption'] ?? '')), 0, 300),
        'defects' => $defs,
        'typed'   => array_values(array_slice($typed, 0, 12)),
        'verdict' => $verdict,
        'people'  => $people,
        'notes'   => $people !== null ? ($people . ' figure' . ($people===1?'':'s') . ' detected') : '',
        'tier'    => '',
        'src'     => 'qa',
    ];
}

} // end function_exists('ck_ai_qa') guard
