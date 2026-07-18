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
