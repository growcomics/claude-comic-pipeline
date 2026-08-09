<?php
// Studio — ✍️ GRIBBLE SCRIPT WRITER: generate a full comic script in Gribble's voice
// and, more importantly, in Gribble's STRUCTURE.
//
// Everything the model is told about "what Gribble does" comes from a real parse of
// the 41-script corpus (~/Documents/gribble stories/, 1,355 pages / 5,397 panels) —
// see research/gribble-corpus/{profile.py,FORMULA.md,gribble-profile.json}. The two
// findings that drive this whole page:
//
//   1. GROWTH DENSITY — 28.9% of his pages are transformation pages, in ~5 separate
//      runs per script, and 22.7% of those runs span 3+ consecutive pages. Growth is
//      not one act-two set-piece; it recurs the whole way through, first hit at ~11%.
//   2. THE GRID BREAK — 98.4% of pages are worth four panels, but only 66.9% DRAW
//      four frames; 30.8% collapse into one full-page image written
//      "Panels 1, 2, 3 and 4- ..." or "(Full page panel)- ...". Those merged pages are
//      70.3% growth vs 1.7% for ordinary panels — a 41x enrichment. The grid break IS
//      the transformation device.
//
// So this generator does not just prompt-and-hope: after the model writes, the server
// PARSES the script with a port of the corpus parser, scores it against the measured
// targets, and sends one repair pass naming the exact misses. The owner sees the
// structure report next to the script.
//
// Verbs (POST): gr_write (generate+validate+repair) · gr_check (re-score pasted text)
//               gr_create (turn the script into a studio project, tagged gribble)
// Standalone file like growgetter.php/review.php — the ONLY other touches are one
// tile on cc.php and one button on index.php.
declare(strict_types=1);
require_once __DIR__ . '/inc/boot.php';

// Auth: browser session OR the bridge key (data/bridge.json), same trust level as
// bridge.php + growgetter.php, so a headless session can drive the JSON verbs.
$grKeyOk = false;
$grGiven = (string)($_POST['key'] ?? ($_SERVER['HTTP_X_BRIDGE_KEY'] ?? ''));
if ($grGiven !== '') {
    $grBk = (string)(s_read(SDATA . '/bridge.json', [])['key'] ?? '');
    $grKeyOk = $grBk !== '' && strlen($grGiven) >= 16 && hash_equals($grBk, $grGiven);
}
if (!$grKeyOk) require_auth();

function gr_cfile(string $id): string { return SDATA . '/creator-' . preg_replace('/[^a-z0-9-]/', '', $id) . '.json'; }
function gr_ai_cfg(): ?array { $f = SDATA . '/ai.json'; if (!is_file($f)) return null; $j = s_read($f, []); return !empty($j['key']) ? $j : null; }
function gr_jout(array $a): void { header('Content-Type: application/json'); header('X-Robots-Tag: noindex'); echo json_encode($a); exit; }

/* ===========================================================================
   THE LIBRARY — every generated script is kept, automatically.
   Owner ask (2026-08-09): "store the comics that get generated so I can review
   them later." Before this, gr_write handed the script to the browser and forgot
   it; the only way to keep one was to click "Create studio project", so a closed
   tab lost the work. Now gr_write always saves first, then returns.
   Layout: one JSON per script at data/gribble/s-<id>.json (data/.htaccess is
   "Require all denied" and subdirectories inherit that, so scripts are not
   web-readable), plus a small index.json holding ONLY list-view metadata — the
   library renders without opening fifty full scripts.
   Deletion is a soft status flip to 'trashed'; the file is never unlinked.
   =========================================================================== */
function gr_libdir(): string { $d = SDATA . '/gribble'; if (!is_dir($d)) @mkdir($d, 0775, true); return $d; }
function gr_sfile(string $id): string { return gr_libdir() . '/s-' . preg_replace('/[^a-z0-9]/', '', $id) . '.json'; }
function gr_ifile(): string { return gr_libdir() . '/index.json'; }

/** Pull the one-line synopsis the writer puts under the by-line (owner ask
 *  2026-08-09 — the library list is unreadable as a wall of titles). Lives above
 *  "Page 1" so gr_parse() ignores it and the structure score is unaffected. */
function gr_synopsis(string $script): string {
    if (preg_match('/^\s*synopsis\s*[:\-–]\s*(.+?)\s*$/im', $script, $m))
        return mb_substr(trim($m[1]), 0, 300);
    return '';
}

/** Metadata row for the list view — must stay small. */
function gr_row(array $rec): array {
    $m = (array)($rec['report']['metrics'] ?? []);
    return [
        'id'         => (string)$rec['id'],
        'title'      => (string)($rec['title'] ?? 'Untitled'),
        'synopsis'   => (string)($rec['synopsis'] ?? ''),
        'createdAt'  => (string)($rec['createdAt'] ?? date('c')),
        'by'         => (string)($rec['by'] ?? ''),
        'sfw'        => !empty($rec['sfw']),
        'starred'    => !empty($rec['starred']),
        'status'     => (string)($rec['status'] ?? 'active'),
        'pid'        => (string)($rec['pid'] ?? ''),
        'pages'      => (int)($m['pages'] ?? 0),
        'growthPct'  => (float)($m['growthPct'] ?? 0),
        'mergedPct'  => (float)($m['mergedPct'] ?? 0),
        'clean'      => empty($rec['report']['fails']),
        'words'      => (int)($rec['words'] ?? 0),
    ];
}

/** Write the record and upsert its index row, race-safe. */
function gr_lib_save(array $rec): array {
    if (empty($rec['id'])) $rec['id'] = nid();
    $rec += ['createdAt'=>date('c'), 'status'=>'active', 'starred'=>false, 'pid'=>''];
    if (empty($rec['synopsis'])) $rec['synopsis'] = gr_synopsis((string)($rec['script'] ?? ''));
    $rec['by']    = $rec['by'] ?? current_studio_user();
    $rec['words'] = str_word_count((string)($rec['script'] ?? ''));
    s_write(gr_sfile($rec['id']), $rec);
    $row = gr_row($rec);
    s_with_lock(gr_ifile(), function ($idx) use ($row) {
        $list = is_array($idx['scripts'] ?? null) ? $idx['scripts'] : [];
        $hit = false;
        foreach ($list as $k => $r) if (($r['id'] ?? '') === $row['id']) { $list[$k] = $row; $hit = true; break; }
        if (!$hit) array_unshift($list, $row);
        return ['data'=>['scripts'=>$list], 'result'=>true];
    });
    return $rec;
}

function gr_lib_get(string $id): ?array {
    $f = gr_sfile($id);
    if ($id === '' || !is_file($f)) return null;
    $r = s_read($f, []);
    return is_array($r) && !empty($r['id']) ? $r : null;
}

/** Mutate one record + its index row through a callback. */
function gr_lib_patch(string $id, callable $fn): ?array {
    $rec = gr_lib_get($id);
    if (!$rec) return null;
    return gr_lib_save($fn($rec));
}

function gr_lib_list(string $status = 'active'): array {
    $idx = s_read(gr_ifile(), []);
    $list = is_array($idx['scripts'] ?? null) ? $idx['scripts'] : [];
    $list = array_values(array_filter($list, fn($r) => ($r['status'] ?? 'active') === $status));
    usort($list, function ($a, $b) {                       // starred first, then newest
        $s = (int)!empty($b['starred']) <=> (int)!empty($a['starred']);
        return $s !== 0 ? $s : strcmp((string)($b['createdAt'] ?? ''), (string)($a['createdAt'] ?? ''));
    });
    return $list;
}

// ---- one text call to the Anthropic API, expecting plain script text back ---
// Scripts are long-form prose, not JSON — asking for JSON here would only invite
// escaping bugs across thousands of quoted dialogue lines.
function gr_ai_text(string $system, string $user, int $maxTokens = 8000, int $timeout = 240): ?string {
    $cfg = gr_ai_cfg(); if (!$cfg || !function_exists('curl_init')) return null;
    $models = [(string)($cfg['writerModel'] ?? 'claude-sonnet-5'), 'claude-sonnet-4-6'];
    foreach ($models as $model) {
        // claude-sonnet-5 runs adaptive thinking BY DEFAULT and max_tokens caps
        // thinking + answer together — the whole script budget was consumed by
        // thinking, returning zero text (2026-08-09). Templated script generation
        // doesn't need thinking; disable it so the budget goes to the script.
        $payload = json_encode(['model'=>$model, 'max_tokens'=>$maxTokens, 'system'=>$system,
            'thinking'=>['type'=>'disabled'],
            'messages'=>[['role'=>'user','content'=>$user]]]);
        $ch = curl_init('https://api.anthropic.com/v1/messages');
        curl_setopt_array($ch, [CURLOPT_POST=>true, CURLOPT_RETURNTRANSFER=>true, CURLOPT_TIMEOUT=>$timeout,
            CURLOPT_HTTPHEADER=>['content-type: application/json','anthropic-version: 2023-06-01','x-api-key: '.$cfg['key']],
            CURLOPT_POSTFIELDS=>$payload]);
        $resp = curl_exec($ch); $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE); $cerr = curl_error($ch); curl_close($ch);
        $GLOBALS['gr_ai_last'] = "model={$model} http={$code}" . ($cerr !== '' ? " curl={$cerr}" : '') . ' body=' . mb_substr((string)$resp, 0, 160);
        if ($resp && $code < 400) {
            $j = json_decode((string)$resp, true);
            // Newer models (e.g. claude-sonnet-5) may lead with a thinking block —
            // content[0] is then type=thinking with no text. Collect ALL text blocks.
            $txt = '';
            foreach ((array)($j['content'] ?? []) as $blk) {
                if (($blk['type'] ?? '') === 'text') $txt .= (string)($blk['text'] ?? '');
            }
            $txt = trim($txt);
            if ($txt !== '') return $txt;
        }
        // 404/400 = this account can't see that model id; fall through to the next.
        if ($code !== 404 && $code !== 400) return null;
    }
    return null;
}

/* ===========================================================================
   THE MEASURED PROFILE — every number below is from profile.py over the corpus.
   Keep these in sync with research/gribble-corpus/gribble-profile.json.
   =========================================================================== */
const GR_FORMULA = <<<'TXT'
THE GRIBBLE FORMULA — measured from a full parse of his 41-script corpus
(1,355 pages / 5,397 panels). These are counts, not impressions. Match them.

## FORMAT (exact, non-negotiable)
Artist-facing script. Never prose narration.
    Page 1
    Panel 1- The scene is a street outside a house, there is a moving truck parked...
    Susan- "Alright guys, the boss has had complaints about you two lately."

    Panel 2- Lenny is checking his watch.
    Carl- "Hey Lenny, isn't it lunch time?"
"Page N" alone on its line. "Panel N- " then art direction. Speaker name, hyphen,
then the line in double quotes. Blank line between panels.

## THE PAGE GRID AND THE GRID BREAK (the most important rule)
Every page is worth EXACTLY FOUR PANELS of space (98.4% of his pages).
But only 66.9% of pages draw four separate frames. 30.8% collapse the whole page
into ONE image, written as either:
    Panels 1, 2, 3 and 4- <one continuous description>
    (Full page panel)- <one image>
70.3% of those merged pages depict GROWTH, versus 1.7% of ordinary panels.
THE GRID BREAK IS THE TRANSFORMATION DEVICE. Run a tight four-panel rhythm for
story; when the body changes, throw the grid away and give the whole page to one
image. A script of uniform four-panel pages is NOT a Gribble script.

## GROWTH DENSITY (the product)
- 25-35% of all pages must be growth pages (his mean is 28.9%).
- At least 3 SEPARATE growth runs, spread across the whole script (he averages 5.4).
- At least one run of 3+ CONSECUTIVE growth pages (22.7% of his runs are; max 6).
- The FIRST growth page lands inside the first ~15% of the script (his median: 11%).
- Growth continues to escalate; each run lands bigger than the last, and there is a
  final escalation around 80-90% through.
- Growth happens ON THE PAGE, never between pages. Show it: seams straining, a shirt
  splitting at the shoulder, a bicep swelling past her own head, a doorframe she now
  fills, a bystander's double-take.

## PANEL ECONOMY
- Art direction: ~18 words median per panel (mean 23, cap around 41). One clear
  action, not a paragraph.
- Dialogue: 1.16 lines per panel; ~8-10 words per line; almost never over 25.
- 18% of panels carry NO dialogue at all — reaction beats and growth images.
- About 6 named speakers per script.

## THE VOICE (he is writing to his artist)
- Open panels with "Shot of ...", "We see ...", "We now ...", "We start off with ...".
- Hedge and give the artist latitude — "maybe" appears 151 times, "or something" 33.
  e.g. "(at least a foot shorter than Susan, maybe more)".
- Name characters inline and casually: "We'll call the men Lenny and Carl."
- Parenthetical asides everywhere, clarifying scale, wardrobe state, or intent:
  "(not REALLY fat, just obviously overweight)", "(the armbands are snapping off too)".
- Plain vernacular dialogue. Shouts in ALL CAPS with stretched vowels and stacked
  punctuation: "WHAAA...!?!", "AAAGGGHHH!!! LET GO!", "OOOOOOHHHHHHHH!!!!!!!"
- End the script with "The End", optionally followed by a "Note:" teasing a sequel.

## STORY SHAPE
An ordinary, overlooked woman -> a COUNTABLE growth engine lands early (spinach, a
formula, a stone, a belt, a cloak, numbered doses) -> first growth run by ~10% in ->
a rival or witness registers the change -> escalating growth runs with strength feats
between them -> a final full-page payoff (flexing, floating, towering, lifting
something absurd) -> "The End".

## STORY DISCIPLINE (from the corpus study of published FMG comics — story is the
axis everyone fails: median 2/5, no book above 3. These four failures are why.)
- SPINE: she WANTS something ordinary on page 1 (the promotion, the team spot,
  respect from a named rival) and the ending must ANSWER that want. Growth is how
  the answer arrives, not the answer itself. Every run should change her SITUATION
  — someone's mind, her standing, the plan — not just her measurements.
- ESCALATION, NOT REPETITION: no two growth pages stage the same beat. Each run
  tops the last with a NEW proof of scale — a heavier prop, a bigger bystander
  reaction, a place she no longer fits. Never write two near-identical full-page
  images in a row; a repeated splash is padding, not climax.
- LAND THE ENDING: never stop mid-swing. After the final payoff, spend at least a
  beat on consequence — the rival's face, the new status quo, a last line — then
  "The End".
- KEEP THE LEADS DISTINCT: if more than one character grows, they stay
  tellable-apart at every size — different build, coloring, wardrobe and manner of
  speaking. Never let two characters converge on the same look by the final page.
TXT;

const GR_SFW = 'SFW RULES (apply to every panel): all characters are adults and stay FULLY CLOTHED. '
    . 'During growth, clothing may strain and seams may visibly split — a signature beat — but coverage of chest, torso and hips is ALWAYS preserved; garments never tear away entirely. '
    . 'No nudity, no sexual content, no sensual posing or fetish framing. Keep the language clean — no profanity. '
    . 'Muscle growth is STRENGTH, SPORT, HEROISM and CONFIDENCE. '
    . 'Note: muscle SIZE is never an SFW problem — hugely, exaggeratedly muscular is exactly the product. SFW constrains coverage and framing, NOT how big she gets.';

const GR_MATURE = 'CONTENT RULES: all characters are adults. Clothing may tear and shred during growth. '
    . 'Mature language is allowed where it fits the moment. Still NO explicit sexual content and no sexual framing of the transformation — '
    . 'the fantasy is strength and power, and growth scenes stay about size, muscle and awe.';

// Random seed banks — server-side so repeat clicks genuinely vary.
const GR_ENGINES = [
    'a health food she chokes down that turns out to be something else entirely',
    'an experimental strength formula in numbered doses',
    'a cursed artifact dug out of the wrong tomb',
    'a gym machine calibrated catastrophically wrong',
    'a wish granted by something that does not explain the terms',
    'an ancient stone worn on a cord around the neck',
    'a belt/bracer/cloak that rewrites whoever wears it',
    'a lab accident with a beam that was pointed at the wrong person',
    'a training regimen from a book nobody should have printed',
    'a family inheritance nobody warned her about',
];
const GR_PROTAGONISTS = [
    'a mousy office worker nobody listens to',
    'an overlooked college student in the back row',
    'the benched member of the team',
    'a harried single mother with no time for herself',
    'a small, perpetually underestimated woman',
    'a lab assistant doing all the work and getting none of the credit',
    'a shy librarian who has never raised her voice',
    'a delivery driver on a bad route',
];
const GR_SETTINGS = [
    'a suburban house and the street outside it', 'a college campus', 'a corporate office',
    'a gym', 'a research lab', 'a construction site', 'a small-town main street',
    'a high school reunion', 'a hospital', 'a beach town in summer',
];
const GR_TONES = [
    'wish-fulfillment with a wink', 'underdog sports triumph', 'comedy with escalating chaos',
    'power-corrupts cautionary tale', 'straight superhero origin', 'revenge on the people who laughed',
];

/* ===========================================================================
   PARSER — a port of research/gribble-corpus/profile.py. This is what makes the
   page honest: the script is measured, not assumed.
   =========================================================================== */
const GR_ACTIVE = '/\b(grow|growing|grew|grows|growth|swell|swelling|swells|expand|expanding|bulging|ballooning|inflating|surging|ripping|tearing|splitting|straining|bursting|transform|transforming|getting (?:bigger|larger|taller)|continues? to|even (?:bigger|larger|more))\b/i';
const GR_GROWTH = '/\b(grow|growing|grew|grows|growth|swell|swelling|swells|expand|expanding|bigger|larger|taller|bulge|bulging|balloon|ballooning|inflat|surg|ripping|rips|tearing|tears|split|splitting|strain|straining|burst|bursting|muscles?|muscular|bicep|triceps?|pecs?|abs|quads?|lats|physique|transform|transformation|massive|enormous|huge|towering|gigantic)\b/i';

function gr_is_growth(string $t): bool {
    $a = preg_match_all(GR_ACTIVE, $t); $g = preg_match_all(GR_GROWTH, $t);
    return $a >= 2 || ($a >= 1 && $g >= 3);
}

/** Parse a script into pages of slots. slot = [span, desc, lines[]] */
function gr_parse(string $script): array {
    $pages = []; $cur = null; $si = -1;
    foreach (preg_split('/\R/', $script) as $raw) {
        $t = trim($raw);
        if ($t === '') continue;
        if (preg_match('/^page\s*(\d+)\s*[:.]?\s*$/i', $t)) {
            if ($cur !== null) $pages[] = $cur;
            $cur = []; $si = -1; continue;
        }
        if (preg_match('/^\(?\s*full[- ]?page(?:\s+panel)?\s*\)?\s*[-:.]\s*(.*)$/i', $t, $m)) {
            if ($cur === null) $cur = [];
            $cur[] = ['span'=>4, 'desc'=>trim($m[1]), 'lines'=>[]]; $si = count($cur) - 1; continue;
        }
        // "Panel 3- ..." or the merged "Panels 1, 2, 3 and 4- ..."
        if (preg_match('/^\(?\s*panels?\s*((?:\d+\s*(?:,|and|&|-|\+)?\s*)+)\)?\s*[-:.]\s*(.*)$/i', $t, $m)) {
            if ($cur === null) $cur = [];
            $span = max(1, preg_match_all('/\d+/', $m[1]));
            $cur[] = ['span'=>$span, 'desc'=>trim($m[2]), 'lines'=>[]]; $si = count($cur) - 1; continue;
        }
        if ($si < 0 || $cur === null) continue;
        if (preg_match('/^([A-Z][A-Za-z0-9\'’.& \/]{0,28}?)\s*[-:]\s*["“](.*)$/u', $t, $m)) {
            $cur[$si]['lines'][] = [trim(rtrim($m[1], '-:')), rtrim(rtrim(trim($m[2]), '"'), '”')];
        } else {
            $cur[$si]['desc'] = trim($cur[$si]['desc'] . ' ' . $t);
        }
    }
    if ($cur) $pages[] = $cur;
    return array_values(array_filter($pages, fn($p) => count($p) > 0));
}

function gr_median(array $a): float {
    if (!$a) return 0.0;
    sort($a); $n = count($a); $m = intdiv($n, 2);
    return $n % 2 ? (float)$a[$m] : ($a[$m-1] + $a[$m]) / 2.0;
}

/** Jaccard similarity of two art directions over unique lowercase words of 3+
 *  chars. Pages under 8 such words score 0 — his terse beats ("More of Debra
 *  becoming Mega Woman.") are legit shorthand, not repetition, and tiny sets
 *  make Jaccard noisy. Mirrored exactly in validate_story_gates.py. */
function gr_sim(string $a, string $b): float {
    preg_match_all("/[a-z']{3,}/", strtolower($a), $ma);
    preg_match_all("/[a-z']{3,}/", strtolower($b), $mb);
    $A = array_unique($ma[0]); $B = array_unique($mb[0]);
    if (count($A) < 8 || count($B) < 8) return 0.0;
    return count(array_intersect($A, $B)) / count(array_unique(array_merge($A, $B)));
}

/** Score a parsed script against the measured corpus targets. */
function gr_report(string $script): array {
    $pages = gr_parse($script);
    $n = count($pages);
    if ($n === 0) return ['ok'=>false, 'pages'=>0, 'fails'=>['The script has no parseable "Page N" headers at all.'], 'metrics'=>[]];

    $gflags = []; $mflags = []; $badGrid = []; $descW = []; $silent = 0; $slots = 0;
    $lineW = []; $speakers = []; $pdesc = [];
    foreach ($pages as $i => $page) {
        $spanSum = 0; $merged = false; $txt = ''; $pd = '';
        foreach ($page as $s) {
            $slots++; $spanSum += $s['span'];
            if ($s['span'] > 1) $merged = true;
            $descW[] = str_word_count($s['desc']);
            if (!$s['lines']) $silent++;
            $txt .= ' ' . $s['desc']; $pd .= ' ' . $s['desc'];
            foreach ($s['lines'] as $l) {
                $txt .= ' ' . $l[1]; $lineW[] = str_word_count($l[1]);
                $speakers[$l[0]] = ($speakers[$l[0]] ?? 0) + 1;
            }
        }
        if ($spanSum !== 4) $badGrid[] = $i + 1;
        $mflags[] = $merged;
        $pdesc[] = trim($pd);
        $gflags[] = gr_is_growth($txt) || ($merged && preg_match(GR_GROWTH, $txt));
    }

    // consecutive growth runs
    $runs = []; $c = 0;
    foreach ($gflags as $g) { if ($g) $c++; elseif ($c) { $runs[] = $c; $c = 0; } }
    if ($c) $runs[] = $c;

    $gPages = count(array_filter($gflags));
    $mPages = count(array_filter($mflags));
    $firstG = array_search(true, $gflags, true);
    $mAlign = $mPages ? count(array_filter(array_keys($mflags), fn($k) => $mflags[$k] && $gflags[$k])) / $mPages : 0.0;

    // L36/F5b — escalation-by-repetition: consecutive merged full-page images that
    // restate each other ("three near-identical cosmic splashes"). Similarity is
    // desc-only (art direction), consecutive MERGED pages only — his ordinary-panel
    // parallel montages (Crown of Abuul's per-character transformations) are a real
    // device and stay legal.
    $pairSim = []; $simMax = 0.0;
    for ($i = 0; $i + 1 < $n; $i++) {
        if (!($mflags[$i] && $mflags[$i + 1])) continue;
        $pairSim[$i] = gr_sim($pdesc[$i], $pdesc[$i + 1]);
        $simMax = max($simMax, $pairSim[$i]);
    }
    $repPairs = []; $repChains = [];
    foreach ($pairSim as $i => $s) {
        if ($s >= 0.55) $repPairs[] = ($i + 1) . '+' . ($i + 2);
        if ($s >= 0.40 && ($pairSim[$i + 1] ?? 0.0) >= 0.40) $repChains[] = ($i + 1) . '-' . ($i + 3);
    }

    // L36/F5c — the ending must land, not stop mid-swing. Closure = any of: a
    // terminal "The End", at least one page after the last growth page, or dialogue
    // on the final page. Composite on purpose: 8/41 of his scripts skip "The End",
    // 4/41 (incl. Not Exactly as Planned) end ON the payoff page — only the
    // three-way OR passes all 41.
    $lastG = -1; foreach ($gflags as $k => $g) if ($g) $lastG = $k;
    $lastDlg = 0; foreach ($pages[$n - 1] as $s) $lastDlg += count($s['lines']);
    $hasEnd = (bool)preg_match('/\bthe\s+end\b/i', substr($script, -400));
    $closed = $hasEnd || ($lastG >= 0 && $lastG < $n - 1) || $lastDlg > 0;

    $m = [
        'pages'          => $n,
        'slots'          => $slots,
        'growthPages'    => $gPages,
        'growthPct'      => round(100.0 * $gPages / $n, 1),
        'runs'           => $runs,
        'runCount'       => count($runs),
        'longestRun'     => $runs ? max($runs) : 0,
        'mergedPages'    => $mPages,
        'mergedPct'      => round(100.0 * $mPages / $n, 1),
        'mergedAlignPct' => round(100.0 * $mAlign, 1),
        'firstGrowthPct' => $firstG === false ? null : round(100.0 * ($firstG + 1) / $n, 1),
        'descMedian'     => gr_median($descW),
        'silentPct'      => $slots ? round(100.0 * $silent / $slots, 1) : 0,
        'wordsPerLine'   => round(gr_median($lineW), 1),
        'speakers'       => count(array_filter($speakers, fn($v) => $v >= 3)),
        'badGridPages'   => $badGrid,
        'splashRepeatPairs' => $repPairs,
        'splashRepeatChains'=> $repChains,
        'splashSimMax'   => round($simMax, 2),
        'endTheEnd'      => $hasEnd,
        'endDenouement'  => $lastG >= 0 ? $n - 1 - $lastG : null,
        'endClosed'      => $closed,
    ];

    // ---- the gate ----------------------------------------------------------
    // Calibrated by research/gribble-corpus/validate_targets.py, which runs these
    // exact rules over Gribble's own 37 full-length scripts. 70% of them pass. Any
    // rule that rejected his good work was measuring the wrong thing and got
    // loosened — an earlier draft of this gate rejected Social Order, Not Exactly as
    // Planned and The Power of Chocolate, his three highest-growth scripts.
    // TWO floors are deliberately held ABOVE his median and knowingly reject his
    // low-growth outliers (The Hotter Sister, 4.8% growth, 0% merged): growth density
    // and the grid-break device. Standing owner direction is that growth IS the
    // product, so the generator imitates his BEST scripts, not his average one.
    // The two L36 story rules (splash repetition, ending closure) are calibrated by
    // research/gribble-corpus/validate_story_gates.py: all 41 of his scripts pass
    // both (his max merged-pair similarity is 0.455 vs the 0.55 threshold). The
    // unmeasurable story failures — spine (F5a) and lead distinctness (F5d) — are
    // handled in GR_FORMULA's STORY DISCIPLINE block, NOT gated: no text metric
    // detects them without also rejecting his good work.
    $needRuns = $n >= 16 ? 3 : 2;
    $f = [];
    if (count($badGrid) > max(2, (int)round(0.1 * $n)))
        $f[] = 'Pages ' . implode(', ', array_slice($badGrid, 0, 8)) . ' are not worth exactly four panels of space. Every page must total four: either four "Panel N-" slots, or a merged "Panels 1, 2, 3 and 4-" / "(Full page panel)-", or a mix like "Panel 1-" plus "Panels 2, 3 and 4-".';
    if ($m['growthPct'] < 20)
        $f[] = "Growth density is {$m['growthPct']}% of pages — too low. Target 25-35%. Add transformation pages.";
    if ($m['growthPct'] > 55)
        $f[] = "Growth density is {$m['growthPct']}% — so high there is no story left between the growth. Target 25-35%.";
    if ($m['runCount'] < $needRuns)
        $f[] = "Only {$m['runCount']} separate growth run(s). Gribble averages 5 — spread growth across the whole script, not one block.";
    if ($m['longestRun'] < 2)
        $f[] = "Longest growth run is {$m['longestRun']} page. Growth must run for CONSECUTIVE pages — aim for at least one run of 3.";
    if ($m['mergedPct'] < 20)
        $f[] = "Only {$m['mergedPct']}% of pages break the four-panel grid. Gribble merges ~31% into single full-page images — and that is how he stages growth.";
    if ($m['mergedPct'] > 65)
        $f[] = "{$m['mergedPct']}% of pages are merged full-page images — too many. Target ~31%; the four-panel grid must stay the default rhythm.";
    if ($mPages && $m['mergedAlignPct'] < 45)
        $f[] = "Only {$m['mergedAlignPct']}% of the merged full-page images are growth pages. In the corpus it is 70% — merge the grid FOR the transformation, not at random.";
    if ($m['firstGrowthPct'] === null)
        $f[] = 'No growth pages detected at all.';
    elseif ($m['firstGrowthPct'] > 30)
        $f[] = "First growth lands {$m['firstGrowthPct']}% of the way in — too late. Gribble's median is 11%; fire the engine early.";
    if ($m['descMedian'] > 30)
        $f[] = "Panel directions run long (median {$m['descMedian']} words). Gribble's median is 18 — one clear action per panel.";
    if ($m['silentPct'] < 8)
        $f[] = "Only {$m['silentPct']}% of panels are silent. Gribble runs ~18% — let reaction beats and growth images carry themselves.";
    if ($repPairs)
        $f[] = 'Pages ' . implode(', ', array_slice($repPairs, 0, 4)) . ' are back-to-back full-page images that restate each other. A repeated splash is padding, not climax — each one must top the last with a NEW proof of scale: a heavier prop, a bigger reaction, a place she no longer fits.';
    elseif ($repChains)
        $f[] = 'Pages ' . implode(', ', array_slice($repChains, 0, 3)) . ' run three consecutive full-page images that all read the same. Keep one, and make the others escalate — new feat, new witness, new scale — or return to the four-panel grid between them.';
    if (!$closed)
        $f[] = 'The script stops mid-swing: the last page is still mid-growth, nothing lands after the final transformation, and there is no "The End". Give the payoff a landing — at least a beat of consequence (the rival\'s face, the new status quo, a last line), then "The End".';

    return ['ok'=>!$f, 'pages'=>$n, 'metrics'=>$m, 'fails'=>$f];
}

/* ===========================================================================
   VERBS
   =========================================================================== */
$do = ($_SERVER['REQUEST_METHOD'] === 'POST') ? (string)($_POST['do'] ?? '') : '';
if ($do !== '' && !$grKeyOk) csrf_check();

if ($do === 'gr_check') {
    gr_jout(['ok'=>true, 'report'=>gr_report((string)($_POST['script'] ?? ''))]);
}

if ($do === 'gr_write') {
    @set_time_limit(600);
    if (!gr_ai_cfg()) gr_jout(['ok'=>false,'err'=>'AI is not set up — add the API key in the references workspace (refs.php) first.']);

    $pages  = max(6, min(40, (int)($_POST['pages'] ?? 20)));
    $sfw    = ((string)($_POST['sfw'] ?? '1')) !== '0';
    $idea   = mb_substr(trim((string)($_POST['idea'] ?? '')), 0, 2000);
    $title  = mb_substr(trim((string)($_POST['title'] ?? '')), 0, 80);
    $pick   = fn(array $bank, string $given) => ($given !== '' && $given !== 'random' && in_array($given, $bank, true)) ? $given : $bank[random_int(0, count($bank)-1)];
    $seed = [
        'engine'      => $pick(GR_ENGINES,      (string)($_POST['engine'] ?? '')),
        'protagonist' => $pick(GR_PROTAGONISTS, (string)($_POST['protagonist'] ?? '')),
        'setting'     => $pick(GR_SETTINGS,     (string)($_POST['setting'] ?? '')),
        'tone'        => $pick(GR_TONES,        (string)($_POST['tone'] ?? '')),
    ];

    // Concrete page budget, derived from the corpus ratios for THIS page count.
    $gTarget = max(2, (int)round($pages * 0.29));
    $mTarget = max(2, (int)round($pages * 0.31));
    $firstBy = max(2, (int)ceil($pages * 0.15));

    $sys = "You are Gribble, a comic writer who writes female muscle-growth transformation scripts for artists to draw.\n\n"
         . GR_FORMULA . "\n\n" . ($sfw ? GR_SFW : GR_MATURE) . "\n\n"
         . "THIS SCRIPT'S BUDGET (hit these exactly — they are computed from the corpus ratios):\n"
         . "- Length: EXACTLY {$pages} pages, numbered Page 1 to Page {$pages}.\n"
         . "- Growth pages: about {$gTarget} of the {$pages}.\n"
         . "- Growth runs: at least 3 separate runs, at least one of them 3+ consecutive pages.\n"
         . "- First growth page: no later than Page {$firstBy}.\n"
         . "- Merged full-page images: about {$mTarget} pages written as \"Panels 1, 2, 3 and 4- ...\" or \"(Full page panel)- ...\", and they should mostly BE the growth pages.\n"
         . "- Every other page: exactly four \"Panel N- \" slots.\n"
         . "- Roughly one panel in five carries no dialogue at all.\n\n"
         . "Output ONLY the script, and start it EXACTLY like this:\n"
         . "    <Title>\n    by Gribble\n    Synopsis: <ONE sentence, max 25 words, saying what happens and to whom — this is the line the owner reads in the library list, so make it concrete and specific, not a teaser>\n\n    Page 1\n"
         . "No preamble, no commentary, no markdown fences, no page-count summary at the end.";

    // Anti-repetition. Independent random seeds do NOT stop the model falling into
    // the same lexical rut: a batch of five run on 2026-08-09 came back Ironclad
    // Smoothie / Iron Reserves / Ironbearer / Iron Ward, and three synopses opened
    // "An overlooked ...". Feed the titles already in the library back in as a
    // blocklist, and ban the openings the seeds themselves suggest.
    $used = array_slice(array_map(fn($r) => (string)($r['title'] ?? ''), gr_lib_list('active')), 0, 20);
    $leads = [];
    foreach ($used as $u) { $w = strtok(trim($u), " \t"); if ($w) $leads[strtolower($w)] = true; }
    $avoid = '';
    if ($used) {
        $avoid = "\nTITLES ALREADY IN THIS LIBRARY — do not reuse any of them, and do NOT start your title "
               . "with any of these words (" . implode(', ', array_keys($leads)) . "):\n  "
               . implode("\n  ", $used) . "\n"
               . "Pick a title from a DIFFERENT house pattern than the ones above — if they are mostly "
               . "The-[Artifact], use a name-as-title or a stakes phrase instead.\n";
    }
    $avoid .= "Do NOT open the synopsis with \"An overlooked\" or \"A shy\" — name her job and what she wants instead. "
            . "Do not copy the seed wording verbatim into the script; it is a starting point, not dialogue.\n";

    $user = "Write the script.\n\n"
          . ($title !== '' ? "TITLE: {$title}\n" : "TITLE: invent a short punchy one (1-3 words).\n")
          . $avoid
          . ($idea !== '' ? "THE OWNER'S IDEA (this is the story — follow it):\n{$idea}\n\n" : '')
          . "Seeds for this generation" . ($idea !== '' ? " (use them only where they do not conflict with the owner's idea)" : '') . ":\n"
          . "GROWTH ENGINE: {$seed['engine']}\nPROTAGONIST: {$seed['protagonist']}\nSETTING: {$seed['setting']}\nTONE: {$seed['tone']}\n";

    $maxTok = min(16000, $pages * 480 + 1500);
    $script = gr_ai_text($sys, $user, $maxTok);
    if ($script === null || $script === '') gr_jout(['ok'=>false,'err'=>'The AI did not return a script — try again. [' . ($GLOBALS['gr_ai_last'] ?? 'no call made: missing data/ai.json key or no curl') . ']']);
    $script = trim(preg_replace('/^```[a-z]*\s*|\s*```$/i', '', $script));

    // --- validate, and repair once if the structure missed ------------------
    $rep = gr_report($script);
    $repaired = false;
    if (!$rep['ok']) {
        $fixUser = "Here is a draft script. It is close, but the STRUCTURE misses the Gribble targets. "
                 . "Rewrite it in full, fixing every point below and changing as little else as possible. "
                 . "Keep the same story, cast and title.\n\nWHAT TO FIX:\n- " . implode("\n- ", $rep['fails'])
                 . "\n\nDRAFT:\n" . $script . "\n\nOutput ONLY the corrected full script.";
        $fixed = gr_ai_text($sys, $fixUser, $maxTok);
        if ($fixed) {
            $fixed = trim(preg_replace('/^```[a-z]*\s*|\s*```$/i', '', $fixed));
            $rep2 = gr_report($fixed);
            // keep the repair only if it actually reduced the miss count
            if (count($rep2['fails']) < count($rep['fails'])) { $script = $fixed; $rep = $rep2; $repaired = true; }
        }
    }

    $t = $title;
    if ($t === '' && preg_match('/^\s*(.+?)\s*$/m', $script, $mm)) $t = mb_substr(trim($mm[1]), 0, 80);

    // Save BEFORE returning — a closed tab must never lose a generated script.
    $rec = gr_lib_save(['title'=>$t, 'script'=>$script, 'report'=>$rep, 'seed'=>$seed,
                        'repaired'=>$repaired, 'sfw'=>$sfw, 'idea'=>$idea, 'pagesAsked'=>$pages]);

    gr_jout(['ok'=>true, 'id'=>$rec['id'], 'title'=>$t, 'synopsis'=>$rec['synopsis'],
             'script'=>$script, 'report'=>$rep, 'seed'=>$seed, 'repaired'=>$repaired,
             'sfw'=>$sfw, 'createdAt'=>$rec['createdAt'], 'library'=>gr_lib_list('active')]);
}

// ===== LIBRARY VERBS =========================================================
if ($do === 'gr_list') {
    $st = (string)($_POST['status'] ?? 'active');
    gr_jout(['ok'=>true, 'library'=>gr_lib_list($st === 'trashed' ? 'trashed' : 'active')]);
}

if ($do === 'gr_get') {
    $rec = gr_lib_get((string)($_POST['id'] ?? ''));
    if (!$rec) gr_jout(['ok'=>false,'err'=>'No such saved script.']);
    gr_jout(['ok'=>true, 'id'=>$rec['id'], 'title'=>$rec['title'], 'script'=>$rec['script'],
             'synopsis'=>(string)($rec['synopsis'] ?? ''),
             'report'=>$rec['report'] ?? gr_report($rec['script']), 'seed'=>$rec['seed'] ?? [],
             'sfw'=>!empty($rec['sfw']), 'repaired'=>!empty($rec['repaired']),
             'createdAt'=>$rec['createdAt'] ?? '', 'pid'=>$rec['pid'] ?? '',
             'starred'=>!empty($rec['starred']), 'note'=>$rec['note'] ?? '']);
}

if ($do === 'gr_star' || $do === 'gr_trash' || $do === 'gr_restore' || $do === 'gr_rename' || $do === 'gr_note') {
    $id = (string)($_POST['id'] ?? '');
    $val = (string)($_POST['v'] ?? '');
    $rec = gr_lib_patch($id, function (array $r) use ($do, $val) {
        if ($do === 'gr_star')    $r['starred'] = $val !== '0';
        if ($do === 'gr_trash')   $r['status']  = 'trashed';   // soft — the file stays
        if ($do === 'gr_restore') $r['status']  = 'active';
        if ($do === 'gr_rename' && trim($val) !== '') $r['title'] = mb_substr(trim($val), 0, 80);
        if ($do === 'gr_note')    $r['note'] = mb_substr($val, 0, 2000);
        return $r;
    });
    if (!$rec) gr_jout(['ok'=>false,'err'=>'No such saved script.']);
    gr_jout(['ok'=>true, 'library'=>gr_lib_list('active'), 'trashed'=>gr_lib_list('trashed')]);
}

if ($do === 'gr_create') {
    $script = trim((string)($_POST['script'] ?? ''));
    $title  = mb_substr(trim((string)($_POST['title'] ?? '')), 0, 80);
    if ($script === '') gr_jout(['ok'=>false,'err'=>'No script to create from.']);
    if ($title === '') $title = 'Untitled Gribble script';
    $sfw = ((string)($_POST['sfw'] ?? '1')) !== '0';

    $all = projects_all();
    $base = slugify($title); $pid = $base; $k = 2; $taken = array_column($all, 'id');
    while (in_array($pid, $taken, true)) $pid = $base . '-' . $k++;
    array_unshift($all, ['id'=>$pid, 'name'=>$title, 'status'=>'active', 'stage'=>'writer',
        'tags'=>array_values(array_filter(['gribble', $sfw ? 'sfw' : ''])),
        'notes'=>'✍️ Written by the Gribble Script Writer (corpus-matched structure).',
        'cover'=>null, 'created'=>date('c'), 'updated'=>date('c')]);
    projects_save($all);

    $rep = gr_report($script);
    $m = $rep['metrics'];
    $brief = "GRIBBLE-STYLE SCRIPT.\n"
           . "Structure (measured): {$m['pages']} pages · {$m['growthPct']}% growth pages in "
           . count($m['runs']) . " runs (longest {$m['longestRun']}) · {$m['mergedPct']}% merged full-page images.\n"
           . "The merged 'Panels 1, 2, 3 and 4-' pages are the transformation pages — they must be composed as ONE full-page image, not a four-panel grid.\n"
           . ($sfw ? GR_SFW : GR_MATURE);
    $c = [
        'projectId'=>$pid, 'name'=>$title, 'stage'=>'writer',
        'brief'   => mb_substr($brief, 0, 4000),
        'script'  => mb_substr($script, 0, 60000),
        'style'   => 'Photoreal 3D CGI / DAZ3D render, cinematic lighting, dynamic comic staging.'
                   . ($sfw ? ' Strictly SFW: every character fully clothed at all times.' : ''),
        'sfw'     => $sfw,
        'gribble' => ['report'=>$rep, 'generatedAt'=>date('c'), 'by'=>current_studio_user()],
        'refs'=>[], 'plan'=>[], 'feedback'=>[],
        'run'     => ['state'=>'idle','backend'=>'flow','account'=>'growcomics','stopRequested'=>false],
        'createdAt'=>date('c'), 'updatedAt'=>date('c'),
    ];
    s_write(gr_cfile($pid), $c);

    // Link the project back onto the saved script so the library shows which
    // scripts already went into production (and never offers a second project).
    $lid = (string)($_POST['id'] ?? '');
    if ($lid !== '') gr_lib_patch($lid, function (array $r) use ($pid) { $r['pid'] = $pid; return $r; });
    else gr_lib_save(['title'=>$title, 'script'=>$script, 'report'=>$rep, 'sfw'=>$sfw, 'pid'=>$pid]);

    gr_jout(['ok'=>true, 'pid'=>$pid, 'title'=>$title, 'library'=>gr_lib_list('active')]);
}

$CSRF = csrf(); // boot.php defines csrf(), not csrf_token() — csrf_token() fataled every browser GET (2026-08-09)
?><!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark"><meta name="robots" content="noindex,nofollow">
<title>Gribble Script Writer</title>
<link rel="icon" href="assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="assets/studio.css">
<style>
.gr-wrap{display:grid;grid-template-columns:340px 1fr;gap:18px;align-items:start}
@media(max-width:900px){.gr-wrap{grid-template-columns:1fr}}
.gr-card{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:16px}
.gr-card h2{margin:0 0 10px;font-size:14px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}
.gr-card label{display:block;font-size:12px;color:var(--muted);margin:10px 0 4px}
.gr-card input[type=text],.gr-card textarea,.gr-card select{width:100%;background:var(--bg);color:var(--text);
  border:1px solid var(--border);border-radius:8px;padding:8px 10px;font:inherit;font-size:13px}
.gr-card textarea{min-height:90px;resize:vertical}
.gr-row{display:flex;gap:10px;align-items:center;margin-top:12px;flex-wrap:wrap}
.gr-script{white-space:pre-wrap;font:13px/1.65 ui-monospace,SFMono-Regular,Menlo,monospace;background:var(--bg);
  border:1px solid var(--border);border-radius:10px;padding:16px;max-height:66vh;overflow:auto}
.gr-chips{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 12px}
.gr-chip{font-size:12px;border:1px solid var(--border);border-radius:999px;padding:4px 11px;color:var(--muted)}
.gr-chip b{color:var(--text);font-weight:700}
.gr-chip.ok{border-color:#2E7D5B;color:#8FE3B8}
.gr-chip.bad{border-color:#8C3B37;color:#F0A9A6}
.gr-fails{margin:0 0 12px;padding:10px 12px;border:1px solid #8C3B37;border-radius:10px;background:#2A1614;font-size:12.5px;line-height:1.6}
.gr-fails li{margin:3px 0}
.gr-note{color:var(--muted);font-size:12px;line-height:1.6}
.gr-bars{display:flex;gap:3px;margin:8px 0 14px;flex-wrap:wrap}
.gr-pg{width:15px;height:26px;border-radius:3px;background:#2B2F3A;border:1px solid var(--border);position:relative}
.gr-pg.g{background:#2E7D5B;border-color:#3E9B72}
.gr-pg.m::after{content:'';position:absolute;inset:2px;border:1px dashed rgba(255,255,255,.55);border-radius:2px}
.gr-spin{display:inline-block;animation:grspin 1s linear infinite}@keyframes grspin{to{transform:rotate(360deg)}}
/* library */
.gr-item{display:block;border:1px solid var(--border);border-radius:9px;padding:9px 10px;margin-bottom:7px;cursor:pointer;background:var(--bg)}
.gr-item:hover{border-color:var(--accent)}
.gr-item.on{border-color:var(--accent);box-shadow:inset 2px 0 0 var(--accent)}
.gr-item .t{font-size:13px;font-weight:600;display:flex;align-items:center;gap:6px}
.gr-item .t span.ttl{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.gr-item .meta{color:var(--muted);font-size:11px;margin-top:3px;display:flex;gap:8px;flex-wrap:wrap}
.gr-item .meta b{color:var(--text);font-weight:600}
.gr-item .acts{margin-top:6px;display:flex;gap:10px}
.gr-item .acts a{font-size:11px;color:var(--muted);text-decoration:none}
.gr-item .acts a:hover{color:var(--text);text-decoration:underline}
.gr-item .syn{color:var(--text);opacity:.78;font-size:11.5px;line-height:1.45;margin-top:3px}
.gr-dot{width:7px;height:7px;border-radius:50%;flex:none;background:#2E7D5B}
.gr-dot.warn{background:#B8862B}
</style>
<script src="https://3dmusclecomics.com/hub/nav.js"></script>
</head><body>
<header class="topbar">
  <div class="brand"><span class="dot"></span> ✍️ Gribble Script Writer</div>
  <a class="ghost" href="cc.php">⌘ Command Center</a>
  <a class="ghost" href="index.php">🎬 Pipeline</a>
  <a class="ghost" href="growgetter.php">🎲 GrowGetter</a>
  <span class="spacer"></span>
  <span class="ghost"><?= h(current_studio_user()) ?></span>
</header>
<main class="wrap">
  <div class="pagehead"><h1>Gribble Script Writer</h1></div>
  <p class="gr-note" style="margin:0 0 16px">
    Writes a full comic script in Gribble's format and structure — measured from his 41-script corpus
    (1,355 pages). The two rules that matter: <b>28.9% of pages are growth pages</b>, in several runs
    with at least one running 3+ pages straight; and <b>~31% of pages break the four-panel grid</b> into a
    single full-page image — which is how he stages a transformation (70% of his merged pages are growth,
    vs 1.7% of ordinary panels). Every draft is parsed and scored against those targets before you see it.
  </p>

  <div class="gr-wrap">
   <div><!-- left column: the form and the library stack together, so the grid stays 2-up -->
    <div class="gr-card">
      <h2>The story</h2>
      <label>Title <span style="opacity:.6">(blank = let it invent one)</span></label>
      <input type="text" id="gtitle" placeholder="e.g. The Power Belt">
      <label>Your idea <span style="opacity:.6">(blank = fully random)</span></label>
      <textarea id="gidea" placeholder="A shy lab assistant tests the formula on herself after her boss takes credit for it one time too many..."></textarea>
      <label>Pages</label>
      <input type="text" id="gpages" value="20">
      <label>Growth engine</label>
      <select id="gengine"><option value="random">— random —</option>
        <?php foreach (GR_ENGINES as $e): ?><option value="<?= h($e) ?>"><?= h($e) ?></option><?php endforeach; ?>
      </select>
      <label>Protagonist</label>
      <select id="gprot"><option value="random">— random —</option>
        <?php foreach (GR_PROTAGONISTS as $e): ?><option value="<?= h($e) ?>"><?= h($e) ?></option><?php endforeach; ?>
      </select>
      <label>Setting</label>
      <select id="gset"><option value="random">— random —</option>
        <?php foreach (GR_SETTINGS as $e): ?><option value="<?= h($e) ?>"><?= h($e) ?></option><?php endforeach; ?>
      </select>
      <label>Tone</label>
      <select id="gtone"><option value="random">— random —</option>
        <?php foreach (GR_TONES as $e): ?><option value="<?= h($e) ?>"><?= h($e) ?></option><?php endforeach; ?>
      </select>
      <div class="gr-row"><label style="margin:0"><input type="checkbox" id="gsfw" checked> Keep it SFW</label></div>
      <div class="gr-row">
        <button class="btn" id="gwrite" onclick="grWrite()">✍️ Write the script</button>
      </div>
      <div class="gr-note" id="gstatus" style="margin-top:10px"></div>
    </div>

    <div class="gr-card" style="margin-top:18px">
      <h2 style="display:flex;align-items:center;gap:8px">
        <span id="glibhead">📚 Saved scripts</span>
        <span class="spacer" style="flex:1"></span>
        <a href="#" id="gtrashtog" onclick="return grToggleTrash()" style="font-size:11px;text-transform:none;letter-spacing:0">show trash</a>
      </h2>
      <div id="glib"></div>
    </div>
   </div>

    <div class="gr-card">
      <h2>The script</h2>
      <div id="gout"><p class="gr-note">Nothing written yet. A 20-page script takes a minute or two — it is written, parsed, scored, and repaired if the structure missed.</p></div>
    </div>
  </div>
</main>
<script>
var CSRF = <?= json_encode($CSRF) ?>;
var LAST = null;
var LIB  = <?= json_encode(gr_lib_list('active')) ?>;   // rendered server-side on first paint
var TRASHVIEW = false;
function esc(s){ var d=document.createElement('div'); d.textContent=String(s==null?'':s); return d.innerHTML; }
function post(data){
  data.csrf = CSRF;
  var body = Object.keys(data).map(function(k){ return encodeURIComponent(k)+'='+encodeURIComponent(data[k]); }).join('&');
  return fetch(location.pathname, {method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body:body})
    .then(function(r){ return r.json(); });
}
function grWrite(){
  var btn = document.getElementById('gwrite');
  btn.disabled = true;
  document.getElementById('gstatus').innerHTML = '<span class="gr-spin">⏳</span> writing, then parsing and scoring the structure…';
  post({do:'gr_write', title:document.getElementById('gtitle').value, idea:document.getElementById('gidea').value,
        pages:document.getElementById('gpages').value, engine:document.getElementById('gengine').value,
        protagonist:document.getElementById('gprot').value, setting:document.getElementById('gset').value,
        tone:document.getElementById('gtone').value, sfw:document.getElementById('gsfw').checked?'1':'0'})
  .then(function(j){
    btn.disabled = false;
    document.getElementById('gstatus').textContent = '';
    if(!j.ok){ document.getElementById('gout').innerHTML = '<div class="gr-fails">'+esc(j.err||'failed')+'</div>'; return; }
    LAST = j; render(j);
    if (j.library) { LIB = j.library; TRASHVIEW = false; renderLib(); }
  }).catch(function(e){ btn.disabled=false; document.getElementById('gstatus').textContent = 'error: '+e; });
}

/* ---- the library ------------------------------------------------------- */
function grWhen(iso){
  if(!iso) return '';
  var d = new Date(iso), now = new Date(), ms = now - d;
  if (ms < 36e5) return Math.max(1, Math.round(ms/6e4)) + 'm ago';
  if (ms < 864e5 && d.getDate() === now.getDate()) return d.toLocaleTimeString([], {hour:'numeric', minute:'2-digit'});
  return d.toLocaleDateString([], {month:'short', day:'numeric'});
}
function renderLib(){
  var el = document.getElementById('glib');
  document.getElementById('glibhead').textContent = TRASHVIEW ? '🗑 Trashed scripts' : '📚 Saved scripts';
  document.getElementById('gtrashtog').textContent = TRASHVIEW ? '← back to saved' : 'show trash';
  if(!LIB || !LIB.length){
    el.innerHTML = '<p class="gr-note">'+(TRASHVIEW ? 'Nothing in the trash.' : 'Nothing saved yet. Every script you write is kept here automatically.')+'</p>';
    return;
  }
  el.innerHTML = LIB.map(function(r){
    var on = LAST && LAST.id === r.id;
    var acts = TRASHVIEW
      ? '<a href="#" onclick="return grLibAct(\''+r.id+'\',\'gr_restore\')">restore</a>'
      : '<a href="#" onclick="return grLibAct(\''+r.id+'\',\'gr_star\',\''+(r.starred?'0':'1')+'\')">'+(r.starred?'unstar':'star')+'</a>'
      + '<a href="#" onclick="return grLibRename(\''+r.id+'\')">rename</a>'
      + '<a href="#" onclick="return grLibAct(\''+r.id+'\',\'gr_trash\')">trash</a>'
      + (r.pid ? '<a href="creator.php?p='+encodeURIComponent(r.pid)+'">project ↗</a>' : '');
    return '<div class="gr-item'+(on?' on':'')+'" onclick="grOpen(\''+r.id+'\')">'
      + '<div class="t"><span class="gr-dot'+(r.clean?'':' warn')+'" title="'+(r.clean?'hit every structure target':'missed a target')+'"></span>'
      +   '<span class="ttl">'+(r.starred?'★ ':'')+esc(r.title)+'</span></div>'
      + (r.synopsis ? '<div class="syn">'+esc(r.synopsis)+'</div>' : '')
      + '<div class="meta"><span><b>'+r.pages+'</b>pp</span><span>growth <b>'+r.growthPct+'%</b></span>'
      +   '<span>merges <b>'+r.mergedPct+'%</b></span><span>'+grWhen(r.createdAt)+'</span>'
      +   (r.sfw?'':'<span>mature</span>')+(r.pid?'<span>✓ in production</span>':'')+'</div>'
      + '<div class="acts" onclick="event.stopPropagation()">'+acts+'</div></div>';
  }).join('');
}
function grOpen(id){
  post({do:'gr_get', id:id}).then(function(j){
    if(!j.ok){ alert(j.err||'could not open'); return; }
    LAST = j; render(j); renderLib();
    document.getElementById('gout').scrollIntoView({behavior:'smooth', block:'start'});
  });
}
function grLibAct(id, verb, v){
  post({do:verb, id:id, v:(v==null?'':v)}).then(function(j){
    if(!j.ok){ alert(j.err||'failed'); return; }
    LIB = TRASHVIEW ? j.trashed : j.library; renderLib();
  });
  return false;
}
function grLibRename(id){
  var cur = (LIB.filter(function(r){return r.id===id;})[0]||{}).title || '';
  var v = prompt('Rename this script', cur);
  if(v==null || !v.trim()) return false;
  return grLibAct(id, 'gr_rename', v.trim());
}
function grToggleTrash(){
  TRASHVIEW = !TRASHVIEW;
  post({do:'gr_list', status: TRASHVIEW?'trashed':'active'}).then(function(j){
    if(j.ok){ LIB = j.library; renderLib(); }
  });
  return false;
}
function render(j){
  var m = j.report.metrics || {}, fails = j.report.fails || [];
  function chip(label, val, good){ return '<span class="gr-chip '+(good?'ok':'bad')+'">'+label+' <b>'+val+'</b></span>'; }
  var chips = ''
    + chip('pages', m.pages, true)
    + chip('growth pages', m.growthPct+'%', m.growthPct>=20 && m.growthPct<=55)
    + chip('growth runs', (m.runs||[]).join('+')||'0', m.runCount>=(m.pages>=16?3:2) && m.longestRun>=2)
    + chip('full-page merges', m.mergedPct+'%', m.mergedPct>=20 && m.mergedPct<=65)
    + chip('merges that are growth', m.mergedAlignPct+'%', m.mergedAlignPct>=45)
    + chip('first growth at', (m.firstGrowthPct==null?'—':m.firstGrowthPct+'%'), m.firstGrowthPct!=null && m.firstGrowthPct<=30)
    + chip('silent panels', m.silentPct+'%', m.silentPct>=8)
    + chip('direction median', m.descMedian+'w', m.descMedian<=30)
    + chip('splash repeats', (m.splashRepeatPairs||[]).length ? m.splashRepeatPairs.join(' ') : 'none',
           !(m.splashRepeatPairs||[]).length && !(m.splashRepeatChains||[]).length)
    + chip('ending', m.endClosed ? 'lands' : 'mid-swing', !!m.endClosed);
  // page strip: green = growth page, dashed inner border = merged full-page image
  var strip = '';
  var g = {}, mm = {};
  // rebuild flags from runs is lossy — the server sends counts, so draw from metrics we have
  var html = ''
    + (j.title ? '<div style="font-size:16px;font-weight:700;margin:0 0 2px">'+esc(j.title)+'</div>' : '')
    + (j.synopsis ? '<div class="gr-note" style="margin:0 0 10px">'+esc(j.synopsis)+'</div>' : '')
    + '<div class="gr-chips">'+chips+'</div>'
    + (j.repaired ? '<div class="gr-note" style="margin:-4px 0 10px">↻ first draft missed the targets — this is the repaired pass.</div>' : '')
    + (fails.length ? '<div class="gr-fails"><b>Still off after the repair pass:</b><ul>'+fails.map(function(f){return '<li>'+esc(f)+'</li>';}).join('')+'</ul></div>' : '')
    + '<div class="gr-row" style="margin:0 0 12px">'
    +   '<button class="btn" onclick="grCopy()">📋 Copy</button> '
    +   '<button class="btn" onclick="grDownload()">⬇ Download .txt</button> '
    +   (j.pid
          ? '<a class="btn" href="creator.php?p='+encodeURIComponent(j.pid)+'">🎬 Open studio project</a>'
          : '<button class="btn" onclick="grProject()">🎬 Create studio project</button>')
    +   '<span class="gr-note" id="gproj">'
    +     (j.createdAt ? '💾 saved to the library · ' + grWhen(j.createdAt) : '')
    +   '</span>'
    + '</div>'
    + '<div class="gr-script" id="gscript">'+esc(j.script)+'</div>';
  document.getElementById('gout').innerHTML = html;
}
function grCopy(){ navigator.clipboard.writeText(LAST.script); document.getElementById('gproj').textContent='copied'; }
function grDownload(){
  var b = new Blob([LAST.script], {type:'text/plain'}), a = document.createElement('a');
  a.href = URL.createObjectURL(b); a.download = (LAST.title||'gribble-script').replace(/[^a-z0-9]+/gi,'-').toLowerCase()+'.txt';
  a.click();
}
function grProject(){
  document.getElementById('gproj').innerHTML = '<span class="gr-spin">⏳</span> creating…';
  post({do:'gr_create', script:LAST.script, title:LAST.title, sfw:LAST.sfw?'1':'0', id:(LAST.id||'')}).then(function(j){
    document.getElementById('gproj').innerHTML = j.ok
      ? '✅ <a href="creator.php?p='+encodeURIComponent(j.pid)+'">open '+esc(j.title)+'</a>'
      : '❌ '+esc(j.err||'failed');
    if(j.ok){ if(LAST) LAST.pid = j.pid; if(j.library){ LIB = j.library; renderLib(); } }
  });
}
renderLib();
</script>
</body></html>
