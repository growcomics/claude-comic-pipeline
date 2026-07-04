<?php
// Studio — 🎲 GrowGetter-style random comic generator (ALWAYS SFW).
// One click runs the full pre-production groundwork for a brand-new comic in the
// style of growgettercomics.com's transformation stories, kept strictly SFW:
//   1. gg_premise  — AI invents a random premise (title, logline, cast, script)
//                    from server-side random seeds (engine / protagonist / setting /
//                    tone) so repeat clicks genuinely vary. Hard SFW rules baked in.
//   2. gg_create   — creates the studio project + creator config (brief / script /
//                    wardrobe / style, tagged growgetter + sfw).
//   3. breakdown   — the browser then calls creator.php?do=breakdown (existing
//                    endpoint) to turn the script into the page/panel plan.
//   4. gg_refplan  — AI researches the REFERENCE set the story needs (face card +
//                    stage-aware bodies per character, env plate per location, all
//                    with SFW-locked generation prompts), stores it on the config
//                    and enqueues a kind=refs worker job carrying the specs.
//   5. gg_qa       — per-image SFW + defect QA (vision call): verdict pass|warn|fail
//                    written into the image `analysis` field (same shape as the
//                    cockpit 🔎 QA scan), so badges/filters light up everywhere.
// Standalone file (like review.php / refs.php) to stay clear of the creator.php
// clobber hazard — the ONLY other touch is one link on index.php.
declare(strict_types=1);
require_once __DIR__ . '/inc/boot.php';
// Auth: a browser session (require_auth), OR the bridge key (data/bridge.json —
// same trust level as bridge.php) so a headless Claude session / worker can drive
// the generator's JSON verbs without a login. Key auth skips CSRF (the key IS the
// credential); session auth keeps the CSRF check below.
$ggKeyOk = false;
$ggGiven = (string)($_POST['key'] ?? ($_SERVER['HTTP_X_BRIDGE_KEY'] ?? ''));
if ($ggGiven !== '') {
    $ggBk = (string)(s_read(SDATA . '/bridge.json', [])['key'] ?? '');
    $ggKeyOk = $ggBk !== '' && strlen($ggGiven) >= 16 && hash_equals($ggBk, $ggGiven);
}
if (!$ggKeyOk) require_auth();

function gg_cfile(string $id): string { return SDATA . '/creator-' . preg_replace('/[^a-z0-9-]/', '', $id) . '.json'; }
function gg_ai_cfg(): ?array { $f = SDATA . '/ai.json'; if (!is_file($f)) return null; $j = s_read($f, []); return !empty($j['key']) ? $j : null; }
function gg_jout(array $a): void { header('Content-Type: application/json'); header('X-Robots-Tag: noindex'); echo json_encode($a); exit; }

// ---- one text call to the Anthropic API, expecting a JSON object back ------
function gg_ai_json(string $system, string $user, int $maxTokens = 4000, int $timeout = 150): ?array {
    $cfg = gg_ai_cfg(); if (!$cfg || !function_exists('curl_init')) return null;
    $payload = json_encode(['model'=>'claude-sonnet-4-6', 'max_tokens'=>$maxTokens, 'system'=>$system,
        'messages'=>[['role'=>'user','content'=>$user]]]);
    $ch = curl_init('https://api.anthropic.com/v1/messages');
    curl_setopt_array($ch, [CURLOPT_POST=>true, CURLOPT_RETURNTRANSFER=>true, CURLOPT_TIMEOUT=>$timeout,
        CURLOPT_HTTPHEADER=>['content-type: application/json','anthropic-version: 2023-06-01','x-api-key: '.$cfg['key']],
        CURLOPT_POSTFIELDS=>$payload]);
    $resp = curl_exec($ch); $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE); curl_close($ch);
    if (!$resp || $code >= 400) return null;
    $j = json_decode($resp, true); $txt = (string)($j['content'][0]['text'] ?? '');
    if (preg_match('/\{.*\}/s', $txt, $m)) $txt = $m[0];
    $o = json_decode($txt, true);
    return is_array($o) ? $o : null;
}

// ---- job enqueue (same shape creator.php's ck_enqueue writes) ---------------
function gg_enqueue(array $job): string {
    $job['id'] = 'job_' . nid();
    $job += ['status'=>'open','progress'=>['done'=>0,'total'=>0,'note'=>''],'stopRequested'=>false,'comments'=>[],'seen'=>[],'createdAt'=>date('c')];
    s_with_lock(JOBS_FILE, function($jobs) use ($job){ $jobs[] = $job; return ['data'=>$jobs,'result'=>true]; });
    return $job['id'];
}

// ---- the SFW mandate (baked into premise, refs, prompts and QA) -------------
const GG_SFW_RULES =
    'ABSOLUTE SFW RULES (non-negotiable, apply to every character, panel and prompt): '
  . 'All characters are adults. Everyone is FULLY CLOTHED at all times in modest athletic wear, streetwear, work clothes or full-coverage hero costumes — '
  . 'no swimwear, no underwear, no lingerie, no shirtless/topless anyone, no bath/shower/locker-room scenes. '
  . 'During growth scenes clothing may strain and seams may visibly split at the shoulder or side (a signature beat) — but coverage of chest, torso and hips is ALWAYS preserved; garments never tear away or fall off. '
  . 'No sexual content, sensual posing, innuendo or fetish framing of any kind. '
  . 'Muscle growth is portrayed as SPORTS, STRENGTH, HEROISM and CONFIDENCE — the fantasy of becoming powerful, framed like a superhero origin or a sports training montage. '
  . 'Clothing may read as athletic-fitting but always keeps full coverage; never sexualize the transformation. '
  . 'IMPORTANT: muscle SIZE is never an SFW problem — hugely, exaggeratedly muscular physiques in modest full-coverage clothing are exactly the product. SFW constrains coverage and framing, NOT how big the muscles are.';

// ---- the GrowGetter formula (distilled from a full scan of growgettercomics.com,
// its free readers, blog and series announcements — 2026-07-03). Feeds the premise
// generator. Server-side random seeds below force variety across clicks.
const GG_FORMULA = <<<'TXT'
THE GROWGETTER FORMULA — what makes a GrowGetter-style comic (from a study of the
catalog: Muller, Seven Idols, Heather & Me, The Magic Cloak, Worst to First,
Superior, The Goddess Lucy, Breaker, UltraGal, The Curse, and ~40 more):
• CORE RECIPE: a relatable ORDINARY WOMAN + one countable GROWTH ENGINE (artifact
  set / serum doses / cursed object / training arc / cosmic accident) + a RIVAL who
  taps the same engine + a mundane contemporary setting + character-first buildup
  with growth sequences as earned payoffs + an escalation ladder that ends in a
  named showdown.
• THE PROTAGONIST is always a maximally relatable "before": a neurotic housewife,
  an average student, the benched junior athlete, an ordinary woman with big dreams.
  Deliberately unremarkable, so the transformation delta is as big as possible.
• THE RIVAL IS MANDATORY: a second woman who gets (or wants) the same power — the
  conflict is woman-vs-woman strength rivalry culminating in a showdown. Issue 2 of
  a series is almost always the rival's counter-move ("Brandi Punches Back",
  "Vanessa's Revenge", "Domina's Deception").
• SUPPORTING ARCHETYPES: an enabler/scientist who explains or supplies the engine
  (and sometimes becomes the threat); a normal-strength witness/love interest whose
  awe registers the growth for the reader.
• THE PAYOFF DOCTRINE (the creator's own stated rule): growth scenes are "the
  payoff" — invest pages in character and rivalry setup first, then deliver
  concentrated growth sequences as EARNED payoffs. Story interest, not the payoff
  itself, is what carries a series.
• ESCALATION LADDERS ARE LITERAL AND COUNTABLE: seven idols, six cloak owners, four
  afterlife realms, formula doses — a countable mechanism guarantees each
  installment outgrows the last. Build one into the premise.
• STRUCTURE of an opening chapter (~20 pages, here compressed to 8-10): grounded
  slice-of-life opening establishing her overlooked/underestimated; the engine
  lands by page 2-3; first growth beat mid-chapter with strength-feat set-pieces
  (a lift she couldn't do, a doorframe she now fills, a rival's double-take,
  astonished-bystander reaction shots); ends on a cliffhanger tease of the rival
  or the next rung of the ladder.
• SETTING: overwhelmingly contemporary mundane — gym, home, campus, lab, track
  meet, small business. Growth reads bigger against normal doorframes and normal
  people. Allowed exceptions: pulp tomb-raiding adventure, or a mythic realm tour.
• TITLES are short (1-3 words), punchy, never literary. Three house patterns:
  (A) name-as-title ("Muller", "UltraGal", "Breaker"); (B) The-[Artifact/Engine]
  ("The Magic Cloak", "The Power Belt", "The Curse", "Seven Idols"); (C) stakes
  phrase ("Worst to First", "Superior", "Charged!").
• EMOTIONAL REGISTERS available: wish-fulfillment self-improvement, underdog
  sports triumph, power-corrupts caution, sweet slow-burn romance, classic cape
  heroics, pulp adventure.
• MUSCLE SIZE IS THE PRODUCT (owner-verified 2026-07-04; calibrated from the
  source comics). The catalog's own size ladder: "athletic" → "very muscular,
  biceps the size of a head" → "fantasy sized, biceps double the size of a
  head" → "extreme proportions". A TRANSFORMED (post) character sits at the
  fantasy tier: shoulders 2.5-3 head-widths across with the head reading small
  between mountainous traps; neck thicker than the head; flexed biceps LARGER
  THAN HER HEAD with forearms nearly as thick; a massive chest shelf; lats so
  wide the arms rest at 45°; each thigh wider than her waist; visibly TALLER,
  filling a doorframe. THE FOUR CONSTANT DIMENSIONS (owner-specified, in every
  transformed figure): (1) a BIG CHEST — a large feminine bust carried forward
  on the pec shelf; (2) a BIG ROUNDED BUTT and heavily developed hips/glutes;
  (3) a VERY NARROW wasp waist between them — the exaggerated hourglass is the
  silhouette; (4) VISIBLE ABS — a defined 6-8-pack reading even through the
  costume fabric across that narrow waist. The figure stays FEMININE — pretty
  face, long hair — never male-bodybuilder blocky, and the muscle renders as
  SMOOTH, ROUND, pumped mass (no shredded striations, veins rare).
  MID-transformation = competitive-bodybuilder tier with the same four
  dimensions at smaller scale. "Merely athletic/toned" as a transformed state
  is a FAILURE of the format.
• GROWTH SCENES ARE MANDATORY AND MULTIPLE (3-4 per chapter in hero-mode,
  progress-reveal beats in slow-burn mode), and each is a SEQUENCE — never one
  cut-away panel. The canonical burst sequence (6-8 panels over 1-2 pages):
  (1) trigger ECU — hands on the vial/artifact, object glowing; (2) face ECU —
  gasp or wild grin, eyes flaring, hair lifting; (3) full-body energy pose,
  back arched, first seams popping; (4) an ECU MONTAGE of single body parts
  each filling its own panel on burst/speedline backgrounds, in order:
  chest/shoulders swell → bicep balloons → thighs/hips widen, with baked SFX
  as the only text (FWOOMP, BAAAM, RIIIP, KRZZT); (5) full-body AFTER splash
  from a low angle, her new mass filling a doorframe/panel, scale sold by
  furniture or bystanders; (6) post-growth beats — she squeezes her own bicep
  in disbelief, a strength-feat demo, and a bystander reaction (dropped jaw).
  Dialogue drops out during the burst; SFX carry it. Slow-burn variant: same-
  pose mirror before/afters, prompted flexes, "not as big as I thought" hooks.
TXT;

// ---- random seed banks (server-side randomness => real variety per click) ---
// Drawn from the catalog's engine/archetype frequency so rolls feel on-brand.
const GG_ENGINES = [
    'a magic artifact that empowers whoever holds it — and can change hands (a cloak, belt, crown, ring or old gym relic)',
    'a SET of legendary artifacts to collect, each one granting another rung of strength (idols, medallions, potions)',
    'an experimental serum or secret formula measured in doses — each dose a bigger transformation',
    'an industrial or lab accident (strange sludge, a charged meteorite, an overloaded machine) with empowering side-effects',
    'a superhero origin — cosmic exposure grants super strength, and she must learn to control it as a villainess rises',
    'a curse from a spurned mystic that was meant as punishment but becomes a gift she learns to own',
    'gym training supercharged by a freak accident — she was already working out; now every session counts tenfold',
    'pure training and dedication, no magic at all — a slow-burn strength journey carried by friendship and heart',
    'a team of underdog athletes discovering a secret training method before the championship against the elite squad',
    'a strength-transfer dynamic — a rival siphons her progress until the tables turn',
    'an enchanted contest or festival where each round physically empowers the contestants',
    'a mythic realm tour — a mantle of divine strength and a trial to face in each realm',
];
const GG_PROTAGONISTS = [
    'an underappreciated housewife who decides to improve her life at the local gym',
    'the smallest player on a struggling college track team, always benched',
    'a shy librarian who has never set foot in a gym',
    'an overworked office assistant everyone talks over in meetings',
    'a hobby adventurer chasing legends nobody else believes in',
    'an average university student with big dreams and an empty trophy shelf',
    'a kind-hearted café worker whose day starts with a spilled drink',
    'a junior firefighter recruit repeatedly told she is too small for the job',
    'a night-shift security guard at a strange museum',
    'a delivery courier tired of asking strangers for help with heavy packages',
];
const GG_SETTINGS = [
    'a contemporary small town: home, one old-school gym, a main street where everyone knows everyone',
    'a big-city university campus and its athletics department',
    'a family-run neighborhood gym about to be bought out by a flashy chain',
    'a corporate research lab and the quiet suburb next door',
    'a high-school-to-college track and field circuit in championship season',
    'a museum of ancient wonders after closing time',
    'underground tombs and jungle ruins on a collect-the-relics expedition',
    'a contemporary city with a superhero problem it does not know it has yet',
    'a mountain village hosting a legendary strength festival',
    'a mythic ladder of realms, each with its own trial',
];
const GG_TONES = [
    'wish-fulfillment self-improvement with light comedy',
    'high-energy underdog sports drama',
    'classic cape comic — origin, secret identity, rising villainess',
    'pulp adventure — brisk, mysterious, serial cliffhangers',
    'sweet slow-burn slice-of-life with gentle humor',
    'power-corrupts morality tale with a hopeful ending',
];

$do = ($_SERVER['REQUEST_METHOD'] === 'POST') ? (string)($_POST['do'] ?? '') : '';
if ($do !== '' && !$ggKeyOk) csrf_check();

// ===== 1) PREMISE ============================================================
if ($do === 'gg_premise') {
    @set_time_limit(180);
    if (!gg_ai_cfg()) gg_jout(['ok'=>false,'err'=>'AI is not set up — add the API key in the references workspace (refs.php) first.']);
    $pick = fn(array $bank, string $given) => ($given !== '' && $given !== 'random' && in_array($given, $bank, true)) ? $given : $bank[random_int(0, count($bank)-1)];
    $seed = [
        'engine'      => $pick(GG_ENGINES,      (string)($_POST['engine'] ?? '')),
        'protagonist' => $pick(GG_PROTAGONISTS, (string)($_POST['protagonist'] ?? '')),
        'setting'     => $pick(GG_SETTINGS,     (string)($_POST['setting'] ?? '')),
        'tone'        => $pick(GG_TONES,        (string)($_POST['tone'] ?? '')),
    ];
    $sys = 'You are the head writer for a comic studio producing GrowGetter-style transformation comics that are ALWAYS strictly SFW.'
        . "\n\n" . GG_FORMULA . "\n\n" . GG_SFW_RULES . "\n\n"
        . 'Given the random seeds, invent ONE coherent, fresh comic premise and write the opening chapter script. Follow the formula: a RIVAL is mandatory in the cast; build a COUNTABLE escalation ladder into the engine; title in one of the three house patterns; the growth beats are earned payoffs after character setup. Reply ONLY with compact JSON, no prose and no markdown fences, of the form: '
        . '{"title":"<short punchy title in a GrowGetter house pattern>","logline":"<1-2 sentence hook>",'
        . '"ladder":"<one sentence naming the countable escalation mechanism, e.g. \'five bronze medallions, each doubling her strength\'>",'
        . '"cast":[{"name":"<first name or full name>","role":"protagonist|rival|friend|mentor","look":"<2 sentence visual identity: age (adult), build BEFORE any transformation, hair, face vibe, everyday outfit — modest and fully clothed>","arc":"<how they change across the chapter, or \'constant\'>"}],'
        . '"locations":["<3-5 named recurring locations>"],'
        . '"wardrobe":"<one paragraph locking each cast member\'s outfit(s) for continuity — every garment modest, full coverage>",'
        . '"script":"<the chapter script: 8-10 pages labeled PAGE 1..PAGE N, each page 2-4 sentences of visual action plus short quoted dialogue lines. Grounded slice-of-life opening and the engine landing by page 2-3 — then AT LEAST TWO (ideally three) full GROWTH-SEQUENCE pages following the canonical burst: trigger close-up (hands on the glowing vial/artifact) → face close-up (gasp, eyes flaring) → energy pose with first seams popping → single-body-part close-up montage (chest/shoulders swell, then bicep balloons, then thighs/hips widen — SFX like FWOOMP/BAAAM/RIIIP carry these panels, dialogue drops out) → low-angle full-body AFTER splash with her new mass filling a doorframe and scale sold by props or bystanders → she squeezes her own bicep in disbelief, performs a strength feat, and a bystander reacts with a dropped jaw. Growth happens ON THE PAGE, never between pages, and each sequence lands one rung BIGGER on the size ladder. Closing cliffhanger teases the rival or the next rung. Only the named cast ever appears.>"}'
        . "\nCast size: protagonist + 2-3 supporting characters (one MUST be role \"rival\"), all adults. The transformation stays a strength/sports/heroism fantasy — never sexualized. Keep the total under 3800 tokens.";
    $user = "Random seeds for this generation:\nENGINE: {$seed['engine']}\nPROTAGONIST: {$seed['protagonist']}\nSETTING: {$seed['setting']}\nTONE: {$seed['tone']}\n\nInvent the premise and write the script. JSON only.";
    $o = gg_ai_json($sys, $user, 4000, 170);
    if (!$o || trim((string)($o['title'] ?? '')) === '' || trim((string)($o['script'] ?? '')) === '')
        gg_jout(['ok'=>false,'err'=>'The AI did not return a usable premise — try again.']);
    $cast = [];
    foreach ((array)($o['cast'] ?? []) as $m) {
        if (!is_array($m)) continue;
        $nm = trim((string)($m['name'] ?? '')); if ($nm === '') continue;
        $cast[] = ['name'=>mb_substr($nm,0,40), 'role'=>mb_substr(trim((string)($m['role'] ?? '')),0,20),
                   'look'=>mb_substr(trim((string)($m['look'] ?? '')),0,400), 'arc'=>mb_substr(trim((string)($m['arc'] ?? '')),0,200)];
        if (count($cast) >= 5) break;
    }
    if (!$cast) gg_jout(['ok'=>false,'err'=>'Premise came back without a cast — try again.']);
    gg_jout(['ok'=>true, 'seed'=>$seed,
        'premise'=>[
            'title'    => mb_substr(trim((string)$o['title']), 0, 80),
            'logline'  => mb_substr(trim((string)($o['logline'] ?? '')), 0, 400),
            'ladder'   => mb_substr(trim((string)($o['ladder'] ?? '')), 0, 300),
            'cast'     => $cast,
            'locations'=> array_slice(array_values(array_filter(array_map(fn($l)=>mb_substr(trim((string)$l),0,80), (array)($o['locations'] ?? [])), 'strlen')), 0, 6),
            'wardrobe' => mb_substr(trim((string)($o['wardrobe'] ?? '')), 0, 1000),
            'script'   => mb_substr(trim((string)$o['script']), 0, 16000),
        ]]);
}

// ===== 2) CREATE PROJECT =====================================================
if ($do === 'gg_create') {
    $pr = json_decode((string)($_POST['premise'] ?? ''), true);
    $seed = json_decode((string)($_POST['seed'] ?? ''), true) ?: [];
    if (!is_array($pr) || trim((string)($pr['title'] ?? '')) === '' || trim((string)($pr['script'] ?? '')) === '')
        gg_jout(['ok'=>false,'err'=>'No premise to create from.']);
    $title = mb_substr(trim((string)$pr['title']), 0, 80);
    $all = projects_all();
    $base = slugify($title); $pid = $base; $k = 2; $taken = array_column($all, 'id');
    while (in_array($pid, $taken, true)) $pid = $base . '-' . $k++;
    array_unshift($all, ['id'=>$pid, 'name'=>$title, 'status'=>'active', 'stage'=>'writer',
        'tags'=>['growgetter','sfw'], 'notes'=>'🎲 Generated by the GrowGetter random-comic generator (always SFW).',
        'cover'=>null, 'created'=>date('c'), 'updated'=>date('c')]);
    projects_save($all);
    $castNames = array_values(array_filter(array_map(fn($m)=>trim((string)($m['name'] ?? '')), (array)($pr['cast'] ?? [])), 'strlen'));
    $brief = "GROWGETTER-STYLE COMIC — ALWAYS SFW.\n"
           . 'Logline: ' . trim((string)($pr['logline'] ?? '')) . "\n"
           . (trim((string)($pr['ladder'] ?? '')) !== '' ? 'Escalation ladder: ' . trim((string)$pr['ladder']) . "\n" : '')
           . 'Cast (only these people ever appear): ' . implode(', ', $castNames) . "\n"
           . GG_SFW_RULES;
    $c = [
        'projectId'=>$pid, 'name'=>$title, 'stage'=>'writer',
        'brief'   => mb_substr($brief, 0, 4000),
        'script'  => mb_substr((string)$pr['script'], 0, 16000),
        'wardrobe'=> mb_substr(trim((string)($pr['wardrobe'] ?? '')), 0, 1000),
        'style'   => 'Photoreal 3D CGI / DAZ3D render, cinematic lighting, dynamic comic staging. Strictly SFW: every character fully clothed in modest wear at all times.',
        'sfw'     => true,
        'autoApprove' => true,   // panels land approved; the board is veto-only (owner ask 2026-07-04)
        'gg'      => ['seed'=>$seed, 'premise'=>['logline'=>(string)($pr['logline'] ?? ''), 'ladder'=>(string)($pr['ladder'] ?? ''),
                      'cast'=>(array)($pr['cast'] ?? []), 'locations'=>(array)($pr['locations'] ?? [])],
                      'generatedAt'=>date('c'), 'by'=>current_studio_user()],
        'refs'=>[], 'plan'=>[], 'feedback'=>[],
        'run'     => ['state'=>'idle','backend'=>'flow','account'=>'growcomics','stopRequested'=>false],
        'createdAt'=>date('c'), 'updatedAt'=>date('c'),
    ];
    s_write(gg_cfile($pid), $c);
    gg_jout(['ok'=>true, 'pid'=>$pid, 'title'=>$title]);
}

// ===== 4) REFERENCE PLAN + WORKER JOB =======================================
// ("3) breakdown" is the existing creator.php?p=<pid> do=breakdown endpoint —
// the browser pipeline calls it directly between gg_create and gg_refplan.)
if ($do === 'gg_refplan') {
    @set_time_limit(180);
    if (!gg_ai_cfg()) gg_jout(['ok'=>false,'err'=>'AI is not set up — add the API key first.']);
    $pid = preg_replace('/[^a-z0-9-]/','',(string)($_POST['pid'] ?? ''));
    if ($pid === '' || !project_get($pid)) gg_jout(['ok'=>false,'err'=>'Unknown project.']);
    $cf = gg_cfile($pid); $c = s_read($cf, []);
    $gg = (array)($c['gg'] ?? []); $prem = (array)($gg['premise'] ?? []);
    $castTxt = '';
    foreach ((array)($prem['cast'] ?? []) as $m)
        $castTxt .= '- ' . ($m['name'] ?? '') . ' (' . ($m['role'] ?? '') . '): ' . ($m['look'] ?? '') . ' Arc: ' . ($m['arc'] ?? '') . "\n";
    $locTxt = implode("\n", array_map(fn($l)=>'- ' . $l, (array)($prem['locations'] ?? [])));
    $sys = 'You are the reference director for a photoreal 3D/CGI comic. Plan the complete REFERENCE IMAGE set pre-production needs, and write one text-to-image generation prompt per reference.'
        . "\n" . GG_SFW_RULES . "\n"
        . 'Rules for reference prompts: photoreal 3D CGI / DAZ3D render style. Character sheets are shot on a neutral seamless grey studio background, full body visible head to toe, even soft lighting, no text or labels baked into the image. '
        . 'For each CHARACTER whose arc involves transformation, plan a face card (stage-agnostic) plus a full-body sheet per stage — and CALIBRATE THE SIZES to the house ladder: pre = ordinary, unremarkable build; mid = competitive female BODYBUILDER tier (unmistakably heavily muscled: broad thick shoulders, large round biceps, wide back, thick legs — never merely "toned"/"athletic"); post = FANTASY tier, exaggerated beyond bodybuilder realism: shoulders 2.5-3 head-widths across, head small between mountainous traps, neck thicker than the head, flexed biceps LARGER THAN HER HEAD, lats pushing the arms out to 45 degrees, each thigh wider than her waist, visibly taller — ALWAYS with the four constant dimensions: a BIG feminine bust carried on the massive chest shelf, a BIG rounded butt and powerful glutes, a VERY NARROW wasp waist between them (the exaggerated hourglass IS the silhouette), and VISIBLE 6-8-pack abs reading through the fabric across that waist — pretty face, SMOOTH ROUND pumped muscle (no shredded striations, no prominent veins) — always in modest full-coverage athletic clothing that visibly strains but holds. IMPORTANT: image generators normalize physiques DOWN toward average, so write each sheet\'s size language one class LARGER than the target, use the concrete head/waist comparisons, and repeat the size words (massive, enormous, hugely muscled) at least twice per prompt. TWO STRUCTURAL RULES: (a) every body sheet is a TURNAROUND — three full-body views side by side (front, side profile, back), identical size and outfit in all three; (b) each transformation sheet\'s prompt must tell the worker to ATTACH the project\'s numbered muscle-size scale reference (kind=view, "size scale") and anchor the stage to a NUMBER on it ("her muscle size is exactly SIZE N on the attached scale") — a visual anchor beats prose. Non-transforming characters get a face card + one body sheet with stage "". '
        . 'For each LOCATION, one wide establishing environment plate with NO people in frame. '
        . 'Reply ONLY with compact JSON: {"refs":[{"char":"<character name, or location name for scenes>","kind":"face|body|scene","stage":"pre|mid|post|","label":"<2-4 word label>","prompt":"<the full generation prompt, 2-4 sentences, SFW, self-contained>"}]}. 12-20 refs total.';
    $user = "CAST:\n" . $castTxt . "\nLOCATIONS:\n" . $locTxt . "\nWARDROBE LOCK:\n" . mb_substr((string)($c['wardrobe'] ?? ''), 0, 800) . "\n\nPlan the reference set. JSON only.";
    $o = gg_ai_json($sys, $user, 4000, 170);
    $specs = [];
    foreach ((array)($o['refs'] ?? []) as $r) {
        if (!is_array($r)) continue;
        $kind = in_array(($r['kind'] ?? ''), ['face','body','view','scene','prop'], true) ? (string)$r['kind'] : '';
        $prompt = trim((string)($r['prompt'] ?? ''));
        if ($kind === '' || $prompt === '') continue;
        $specs[] = ['id'=>nid(), 'char'=>mb_substr(trim((string)($r['char'] ?? '')),0,40), 'kind'=>$kind,
                    'stage'=>ck_stage_key((string)($r['stage'] ?? '')), 'label'=>mb_substr(trim((string)($r['label'] ?? '')),0,80),
                    'prompt'=>mb_substr($prompt . ' Strictly SFW: fully clothed, modest coverage.', 0, 1200)];
        if (count($specs) >= 24) break;
    }
    if (!$specs) gg_jout(['ok'=>false,'err'=>'The AI did not return a usable reference plan — try again.']);
    $backend = in_array(($_POST['backend'] ?? ''), ['flow','higgsfield'], true) ? (string)$_POST['backend'] : 'flow';
    $account = $backend === 'flow' ? (in_array(($_POST['account'] ?? ''), ['growcomics','marrtrobinson'], true) ? (string)$_POST['account'] : 'growcomics') : '';
    $jobId = '';
    s_with_lock($cf, function($cc) use ($specs, &$c) {
        if (!is_array($cc)) $cc = $c;
        $cc['refplan'] = $specs; $cc['updatedAt'] = date('c');
        $c = $cc;
        return ['data'=>$cc, 'result'=>true];
    });
    $jobId = gg_enqueue([
        'projectId'=>$pid, 'kind'=>'refs', 'scope'=>'refs',
        'backend'=>$backend, 'account'=>$account,
        'refplan'=>$specs,
        'brief'=>(string)($c['brief'] ?? ''), 'wardrobe'=>(string)($c['wardrobe'] ?? ''),
        'sfw'=>true, 'createdBy'=>current_studio_user(),
    ]);
    s_with_lock($cf, function($cc) use ($jobId) {
        if (!is_array($cc)) return ['result'=>false];
        $cc['run'] = (array)($cc['run'] ?? []); $cc['run']['state'] = 'queued'; $cc['run']['jobId'] = $jobId; $cc['run']['queuedAt'] = date('c');
        return ['data'=>$cc, 'result'=>true];
    });
    gg_jout(['ok'=>true, 'pid'=>$pid, 'jobId'=>$jobId, 'refs'=>$specs]);
}

// ===== replace a growgetter project's page/panel plan =========================
// Lets a worker session RESTRUCTURE the shotlist (e.g. expand growth beats into
// multi-panel growth sequences per the size/density doctrine) without the
// session-only creator.php breakdown. Only projects tagged growgetter. Plan is
// normalized to the breakdown shape and written race-safe.
//   POST growgetter.php  do=gg_plan, pid, plan=<json {pages:[{stage,panels:[{id,beat,camera,location,characters[],dialogue}]}]>
if ($do === 'gg_plan') {
    $pid = preg_replace('/[^a-z0-9-]/','',(string)($_POST['pid'] ?? ''));
    $proj = $pid !== '' ? project_get($pid) : null;
    if (!$proj) gg_jout(['ok'=>false,'err'=>'Unknown project.']);
    if (!in_array('growgetter', (array)($proj['tags'] ?? []), true)) gg_jout(['ok'=>false,'err'=>'Not a growgetter project.']);
    $in = json_decode((string)($_POST['plan'] ?? ''), true);
    $pages = is_array($in) ? ($in['pages'] ?? $in) : null;
    if (!is_array($pages) || !$pages) gg_jout(['ok'=>false,'err'=>'Bad plan JSON.']);
    $out = []; $pi = 0;
    foreach ($pages as $pg) {
        $pi++; $panels = [];
        foreach ((array)($pg['panels'] ?? []) as $qi => $pn) {
            if (!is_array($pn)) continue;
            $panels[] = [
                'id'         => mb_substr((string)($pn['id'] ?? ('p'.$pi.'-'.($qi+1))), 0, 20),
                'beat'       => mb_substr((string)($pn['beat'] ?? ''), 0, 400),
                'camera'     => mb_substr((string)($pn['camera'] ?? ''), 0, 80),
                'location'   => mb_substr((string)($pn['location'] ?? ''), 0, 80),
                'characters' => array_slice(array_map(fn($x)=>mb_substr((string)$x,0,40), (array)($pn['characters'] ?? [])), 0, 6),
                'dialogue'   => mb_substr((string)($pn['dialogue'] ?? ''), 0, 300),
            ];
        }
        if ($panels) $out[] = ['stage'=>ck_stage_key((string)($pg['stage'] ?? '')), 'panels'=>$panels];
    }
    if (!$out) gg_jout(['ok'=>false,'err'=>'Plan had no panels.']);
    s_with_lock(gg_cfile($pid), function($c) use ($out) {
        if (!is_array($c)) $c = [];
        $c['plan'] = $out; $c['updatedAt'] = date('c');
        return ['data'=>$c, 'result'=>true];
    });
    gg_jout(['ok'=>true, 'pages'=>count($out), 'panels'=>array_sum(array_map(fn($p)=>count($p['panels']), $out))]);
}

// ===== list a project's scannable images (feeds the SFW QA loop) =============
if ($do === 'gg_images') {
    $pid = preg_replace('/[^a-z0-9-]/','',(string)($_POST['pid'] ?? ''));
    if ($pid === '' || !project_get($pid)) gg_jout(['ok'=>false,'err'=>'Unknown project.']);
    $files = [];
    foreach (images_all($pid) as $m) {
        $f = (string)($m['file'] ?? ''); if ($f === '') continue;
        $files[] = ['file'=>$f, 'scanned'=>!empty($m['analysis']['verdict'])];
    }
    gg_jout(['ok'=>true, 'images'=>$files]);
}

// ===== 5) SFW + DEFECT QA (one image per call; the browser loops) ===========
if ($do === 'gg_qa') {
    @set_time_limit(90);
    if (!gg_ai_cfg()) gg_jout(['ok'=>false,'err'=>'AI is not set up — add the API key first.']);
    $pid = preg_replace('/[^a-z0-9-]/','',(string)($_POST['pid'] ?? ''));
    if ($pid === '' || !project_get($pid)) gg_jout(['ok'=>false,'err'=>'Unknown project.']);
    $file = basename((string)($_POST['file'] ?? ''));
    $path = project_dir($pid) . '/' . $file;
    if ($file === '' || !is_file($path)) gg_jout(['ok'=>false,'err'=>'No such image.']);
    $cfg = gg_ai_cfg();
    $data = @file_get_contents($path);
    if ($data === false) gg_jout(['ok'=>false,'err'=>'Unreadable image.']);
    $ext = ext_of($path); $mime = $ext==='png'?'image/png':($ext==='webp'?'image/webp':($ext==='gif'?'image/gif':'image/jpeg'));
    $c = s_read(gg_cfile($pid), []);
    $castNames = array_values(array_filter(array_map(fn($m)=>trim((string)($m['name'] ?? '')), (array)($c['gg']['premise']['cast'] ?? [])), 'strlen'));
    // is this image a registered REFERENCE (character sheet / env plate)? Then the
    // extra-person check must not fire on the sheet's own single subject, and an
    // env plate expects zero people.
    $refOf = null;
    foreach ((array)($c['refs'] ?? []) as $r) if (($r['file'] ?? '') === $file) { $refOf = $r; break; }
    $sys = 'You are a strict QA inspector for an ALWAYS-SFW comic. You are shown ONE AI-generated image (a comic panel or a reference sheet). Check, in priority order:'
        . "\n1. SFW COMPLIANCE — any nudity, underwear/swimwear/lingerie, shirtless figures, torn-away clothing, sexualized posing or framing, or sheer/skimpy coverage is an automatic FAIL. Exposed midriff/torso is a fail. HOWEVER — and this is a hard rule, not a judgment call: form-fitting athletic sportswear (leggings, compression tights, compression tops, singlets, unitards, track kits) that fully covers torso and hips is STANDARD ATHLETE UNIFORM and must NEVER be reported as a defect, regardless of how form-fitting it is or that body contours are visible through it, including on muscular physiques. Do not emit an nsfw defect whose only basis is tight/form-fitting clothing or visible contours — judge COVERAGE only."
        . "\n2. DUPLICATE CHARACTER — the same character appearing twice in one image (cloned figure)."
        . "\n3. UNWANTED EXTRA — a person in frame beyond those the image is supposed to contain."
        . "\n4. MALFORMED ANATOMY — extra/missing fingers or limbs, fused bodies, melted faces."
        . "\n5. TEXT ARTIFACT — garbled text or labels baked into the art."
        . "\n6. GROWTH UNDERSIZED — this is a muscle-growth comic in the exaggerated house style: a character described to you as MID-transformation must read as heavily muscled (competitive-bodybuilder scale), and POST-transformation as MASSIVE beyond bodybuilder realism (shoulders more than twice head-width, huge arms and legs). If the figure reads merely slim/toned/athletic when a mid or post stage is expected, that is a growth_undersized defect (high severity). Size is judged only when a stage expectation is stated below."
        . "\nReply ONLY with compact JSON: {\"caption\":\"<one short sentence>\",\"people\":<integer human-figure count>,\"defects\":[{\"type\":\"nsfw|duplicate_character|extra_person|anatomy|text_artifact|growth_undersized|other\",\"severity\":\"high|med|low\",\"detail\":\"<short phrase>\"}],\"verdict\":\"pass|warn|fail\"}. "
        . 'verdict is "fail" on ANY nsfw defect or any high-severity defect; "warn" for minor issues; "pass" if clean. When unsure about SFW compliance, FAIL it — this pipeline must never ship a borderline image.';
    if ($refOf) {
        $rk = (string)($refOf['kind'] ?? ''); $rc = trim((string)($refOf['char'] ?? '')); $rl = trim((string)($refOf['label'] ?? ''));
        if ($rk === 'scene' || $rk === 'prop') {
            $u = 'This image is a ' . ($rk === 'scene' ? 'LOCATION/environment reference plate' : 'prop reference') . ($rc !== '' ? ' ("' . $rc . '")' : '')
               . ". It should contain ZERO people — flag ANY human figure as extra_person.\n";
        } else {
            $u = 'This image is a CHARACTER REFERENCE SHEET of cast member ' . ($rc !== '' ? $rc : 'a named character') . ($rl !== '' ? ' (' . $rl . ')' : '')
               . ". Exactly ONE figure — that character — is expected; do NOT flag the single subject as an extra person. Only flag extra_person if MORE than one figure appears.\n";
            $rstg = ck_stage_key((string)($refOf['stage'] ?? ''));
            if ($rstg === 'mid')  $u .= "STAGE EXPECTATION: this is a MID-transformation sheet — competitive female-BODYBUILDER scale with the house hourglass (big chest, big glutes, very narrow waist, visible abs). Merely toned/athletic = growth_undersized (high); a blocky straight-waisted figure with a flat chest and no visible abs = other defect 'hourglass missing' (med).\n";
            if ($rstg === 'post') $u .= "STAGE EXPECTATION: this is a POST-transformation sheet — FANTASY tier: shoulders 2.5-3 head-widths, biceps reading as large as her head or bigger, thighs wider than her waist, visibly towering — WITH the four house dimensions: big feminine bust, big rounded glutes, very narrow wasp waist, visible abs through the fabric. Undersized = growth_undersized (high); missing the hourglass/bust/abs = other defect 'hourglass missing' (med).\n";
        }
    } else {
        $u = ($castNames ? 'The only allowed people (the named cast): ' . implode(', ', $castNames) . ".\n" : '');
    }
    $u .= 'Inspect the image now. JSON only.';
    $payload = json_encode(['model'=>$cfg['model'] ?? 'claude-haiku-4-5', 'max_tokens'=>500, 'system'=>$sys,
        'messages'=>[['role'=>'user','content'=>[
            ['type'=>'image','source'=>['type'=>'base64','media_type'=>$mime,'data'=>base64_encode($data)]],
            ['type'=>'text','text'=>$u]]]]]);
    $ch = curl_init('https://api.anthropic.com/v1/messages');
    curl_setopt_array($ch, [CURLOPT_POST=>true, CURLOPT_RETURNTRANSFER=>true, CURLOPT_TIMEOUT=>45,
        CURLOPT_HTTPHEADER=>['content-type: application/json','anthropic-version: 2023-06-01','x-api-key: '.$cfg['key']],
        CURLOPT_POSTFIELDS=>$payload]);
    $resp = curl_exec($ch); $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE); curl_close($ch);
    if (!$resp || $code >= 400) gg_jout(['ok'=>false,'err'=>'QA call failed — try again.']);
    $j = json_decode($resp, true); $txt = (string)($j['content'][0]['text'] ?? '');
    if (preg_match('/\{.*\}/s', $txt, $m)) $txt = $m[0];
    $o = json_decode($txt, true);
    if (!is_array($o)) gg_jout(['ok'=>false,'err'=>'QA reply was not parseable — try again.']);
    $defs = []; $hi = 0; $nsfw = false;
    foreach ((array)($o['defects'] ?? []) as $d) {
        if (is_array($d)) {
            $t = trim((string)($d['type'] ?? '')); $sev = trim((string)($d['severity'] ?? '')); $det = trim((string)($d['detail'] ?? ''));
            if ($t === 'nsfw') $nsfw = true;
            if ($sev === 'high') $hi++;
            $label = ($t !== '' ? strtoupper($t === 'nsfw' ? 'NOT SFW' : str_replace('_',' ',$t)) : 'defect') . ($det !== '' ? ': ' . $det : '');
        } else { $label = trim((string)$d); }
        if ($label !== '') $defs[] = mb_substr($label, 0, 60);
    }
    $defs = array_values(array_slice($defs, 0, 12));
    $verdict = in_array($o['verdict'] ?? '', ['pass','warn','fail'], true) ? (string)$o['verdict'] : ($defs ? ($hi ? 'fail' : 'warn') : 'pass');
    if ($nsfw) $verdict = 'fail';
    $people = isset($o['people']) && is_numeric($o['people']) ? (int)$o['people'] : null;
    $analysis = [
        'caption' => mb_substr(trim((string)($o['caption'] ?? '')), 0, 300),
        'defects' => $defs,
        'verdict' => $verdict,
        'people'  => $people,
        'tier'    => '',
        'notes'   => 'SFW QA' . ($people !== null ? ' · ' . $people . ' figure' . ($people===1?'':'s') : ''),
        'src'     => 'ggqa',
        'at'      => date('c'),
    ];
    s_with_lock(imeta_path($pid), function($meta) use ($file, $analysis) {
        foreach ($meta as $k => $m2) if (($m2['file'] ?? '') === $file) { $meta[$k]['analysis'] = $analysis; return ['data'=>$meta, 'result'=>true]; }
        return ['result'=>false];
    });
    gg_jout(['ok'=>true, 'file'=>$file, 'verdict'=>$verdict, 'defects'=>$defs, 'caption'=>$analysis['caption']]);
}

if ($do !== '') gg_jout(['ok'=>false,'err'=>'unknown action']);

// ===== PAGE ==================================================================
$ggProjects = [];
foreach (projects_all() as $p) {
    if (!in_array('growgetter', (array)($p['tags'] ?? []), true)) continue;
    $imgs = images_all($p['id']); $qa = ['pass'=>0,'warn'=>0,'fail'=>0,'none'=>0];
    foreach ($imgs as $im) { $v = (string)($im['analysis']['verdict'] ?? ''); if (isset($qa[$v])) $qa[$v]++; else $qa['none']++; }
    $ggProjects[] = ['p'=>$p, 'n'=>count($imgs), 'qa'=>$qa];
}
$CSRF = csrf();
?><!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><meta name="color-scheme" content="dark">
<meta name="robots" content="noindex,nofollow"><title>🎲 GrowGetter Generator · Studio</title>
<link rel="icon" href="assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="assets/studio.css?v=<?= @filemtime(STUDIO_ROOT . '/assets/studio.css') ?>">
<style>
.gg-steps{list-style:none;padding:0;margin:14px 0 0}
.gg-steps li{display:flex;gap:10px;align-items:flex-start;padding:7px 0;border-bottom:1px solid rgba(255,255,255,.05);font-size:14px}
.gg-steps .st{flex:none;width:22px;text-align:center}
.gg-steps .muted2{color:var(--muted);font-size:12px;margin-top:2px}
.gg-spin{display:inline-block;animation:ggspin 1s linear infinite}
@keyframes ggspin{to{transform:rotate(360deg)}}
.gg-cast{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
.gg-cast span{background:rgba(122,127,236,.15);border:1px solid rgba(122,127,236,.4);border-radius:999px;padding:3px 10px;font-size:12px}
.gg-links a{margin-right:8px}
.gg-qa-badge{font-size:12px;border-radius:6px;padding:2px 8px;margin-left:6px}
select.gg{background:#14151C;color:#fff;border:1px solid #2a2c38;border-radius:8px;padding:8px;max-width:100%}
.gg-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:10px;margin-top:10px}
</style></head><body>
<header class="topbar"><div class="brand"><span class="dot"></span> Comic Studio</div>
  <a class="ghost" href="index.php">← Projects</a><span class="spacer"></span>
  <span class="ghost"><?= h(current_studio_user()) ?></span> <a class="ghost" href="login.php?do=logout">Log out</a></header>
<main class="wrap">
  <div class="pagehead"><h1>🎲 GrowGetter Generator <span class="badge" style="--c:#1D9E75">always SFW</span></h1></div>
  <p class="muted" style="max-width:680px">One click invents a random <strong>GrowGetter-style</strong> transformation comic — premise, cast, chapter script, page/panel plan, and a full stage-aware reference plan (face cards, pre/mid/post body sheets, environment plates) queued for the generation worker. Every stage is locked to <strong>strictly SFW</strong>: fully clothed cast, strength-and-heroism framing, and an SFW QA scan that fails anything borderline.</p>

  <div class="card" style="margin-top:14px">
    <div style="display:flex;gap:10px;flex-wrap:wrap;align-items:center">
      <select class="gg" id="seed-engine"><option value="random">🎲 Random engine</option>
        <?php foreach (GG_ENGINES as $x): ?><option value="<?= h($x) ?>"><?= h(mb_substr($x,0,70)) ?>…</option><?php endforeach; ?></select>
      <select class="gg" id="seed-protagonist"><option value="random">🎲 Random protagonist</option>
        <?php foreach (GG_PROTAGONISTS as $x): ?><option value="<?= h($x) ?>"><?= h(mb_substr($x,0,70)) ?></option><?php endforeach; ?></select>
      <select class="gg" id="seed-setting"><option value="random">🎲 Random setting</option>
        <?php foreach (GG_SETTINGS as $x): ?><option value="<?= h($x) ?>"><?= h(mb_substr($x,0,70)) ?></option><?php endforeach; ?></select>
      <select class="gg" id="seed-tone"><option value="random">🎲 Random tone</option>
        <?php foreach (GG_TONES as $x): ?><option value="<?= h($x) ?>"><?= h($x) ?></option><?php endforeach; ?></select>
    </div>
    <div style="display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-top:10px">
      <select class="gg" id="gg-backend"><option value="flow">Backend: Flow (free)</option><option value="higgsfield">Backend: Higgsfield</option></select>
      <select class="gg" id="gg-account"><option value="growcomics">Flow account: growcomics</option><option value="marrtrobinson">Flow account: marrtrobinson</option></select>
      <button class="btn primary" id="gg-go" style="font-size:15px">🎲 Generate random comic</button>
    </div>
    <ul class="gg-steps" id="gg-steps" hidden>
      <li data-s="premise"><span class="st">•</span><div><strong>Premise &amp; script</strong><div class="muted2">Rolling the seeds and writing the chapter…</div></div></li>
      <li data-s="create"><span class="st">•</span><div><strong>Project</strong><div class="muted2">Creating the studio project…</div></div></li>
      <li data-s="breakdown"><span class="st">•</span><div><strong>Page / panel plan</strong><div class="muted2">Breaking the script into a shotlist…</div></div></li>
      <li data-s="refplan"><span class="st">•</span><div><strong>Reference research</strong><div class="muted2">Planning face cards, stage-aware body sheets and environment plates, then queuing the generation job…</div></div></li>
    </ul>
    <div id="gg-result" hidden style="margin-top:14px"></div>
  </div>

  <?php if ($ggProjects): ?>
  <h2 style="margin-top:26px;font-size:17px">Generated comics</h2>
  <div class="gg-grid">
    <?php foreach ($ggProjects as $g): $p = $g['p']; $qa = $g['qa']; ?>
    <div class="card">
      <div style="font-weight:700"><?= h($p['name']) ?></div>
      <div class="muted" style="font-size:12px;margin:4px 0 8px"><?= (int)$g['n'] ?> image<?= $g['n']===1?'':'s' ?>
        <?php if ($g['n']): ?> · QA: <?= (int)$qa['pass'] ?>✓ <?= (int)$qa['warn'] ?>⚠ <?= (int)$qa['fail'] ?>✗ <?= (int)$qa['none'] ?>·unscanned<?php endif; ?></div>
      <div class="gg-links" style="font-size:13px">
        <a href="creator.php?p=<?= h(urlencode($p['id'])) ?>">🎬 Cockpit</a>
        <a href="refs.php?p=<?= h(urlencode($p['id'])) ?>">🗂 Refs</a>
        <a href="shots.php?p=<?= h(urlencode($p['id'])) ?>">📑 Guide</a>
        <a href="review.php?p=<?= h(urlencode($p['id'])) ?>">🖼 Review</a>
      </div>
      <?php if ($g['n']): ?><button class="btn sm" style="margin-top:8px" onclick="ggQaScan('<?= h($p['id']) ?>', this)">🛡 SFW QA scan</button><?php endif; ?>
    </div>
    <?php endforeach; ?>
  </div>
  <?php endif; ?>
</main>
<script>
var CSRF = <?= json_encode($CSRF) ?>;
function post(url, data) {
  data.csrf = CSRF;
  return fetch(url, {method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'},
    body: new URLSearchParams(data)}).then(function(r){ return r.json(); });
}
function step(name, state, note) {
  var li = document.querySelector('.gg-steps li[data-s="' + name + '"]'); if (!li) return;
  var st = li.querySelector('.st');
  st.innerHTML = state === 'run' ? '<span class="gg-spin">⏳</span>' : (state === 'ok' ? '✅' : (state === 'err' ? '❌' : '•'));
  if (note) li.querySelector('.muted2').textContent = note;
}
document.getElementById('gg-go').addEventListener('click', function() {
  var btn = this; btn.disabled = true;
  var steps = document.getElementById('gg-steps'); steps.hidden = false;
  var out = document.getElementById('gg-result'); out.hidden = true; out.innerHTML = '';
  ['premise','create','breakdown','refplan'].forEach(function(s){ step(s, '', null); });
  var seed = {
    engine: document.getElementById('seed-engine').value,
    protagonist: document.getElementById('seed-protagonist').value,
    setting: document.getElementById('seed-setting').value,
    tone: document.getElementById('seed-tone').value
  };
  var backend = document.getElementById('gg-backend').value;
  var account = document.getElementById('gg-account').value;
  var premise = null, seedUsed = null, pid = null;
  step('premise', 'run');
  post('growgetter.php', {do:'gg_premise', engine:seed.engine, protagonist:seed.protagonist, setting:seed.setting, tone:seed.tone})
  .then(function(r) {
    if (!r.ok) throw {at:'premise', msg:r.err};
    premise = r.premise; seedUsed = r.seed;
    step('premise', 'ok', '“' + premise.title + '” — ' + premise.logline);
    step('create', 'run');
    return post('growgetter.php', {do:'gg_create', premise: JSON.stringify(premise), seed: JSON.stringify(seedUsed)});
  })
  .then(function(r) {
    if (!r.ok) throw {at:'create', msg:r.err};
    pid = r.pid;
    step('create', 'ok', 'Project “' + r.title + '” created (' + pid + ').');
    step('breakdown', 'run');
    return post('creator.php?p=' + encodeURIComponent(pid), {do:'breakdown'});
  })
  .then(function(r) {
    if (!r.ok) throw {at:'breakdown', msg:r.err};
    step('breakdown', 'ok', r.pages + ' pages · ' + r.panels + ' panels planned.');
    step('refplan', 'run');
    return post('growgetter.php', {do:'gg_refplan', pid:pid, backend:backend, account:account});
  })
  .then(function(r) {
    if (!r.ok) throw {at:'refplan', msg:r.err};
    step('refplan', 'ok', r.refs.length + ' references planned · worker job ' + r.jobId + ' queued.');
    var cast = (premise.cast || []).map(function(m){ return '<span>' + esc(m.name) + ' · ' + esc(m.role) + '</span>'; }).join('');
    var out = document.getElementById('gg-result');
    out.innerHTML = '<div class="card" style="border-color:#1D9E75">'
      + '<div style="font-weight:800;font-size:16px">✅ “' + esc(premise.title) + '” is ready for production</div>'
      + '<div class="muted" style="margin-top:4px">' + esc(premise.logline) + '</div>'
      + (premise.ladder ? '<div class="muted" style="margin-top:4px;font-size:12px">📶 Escalation ladder: ' + esc(premise.ladder) + '</div>' : '')
      + '<div class="gg-cast">' + cast + '</div>'
      + '<div class="gg-links" style="margin-top:12px">'
      + '<a class="btn sm primary" href="creator.php?p=' + encodeURIComponent(pid) + '">🎬 Open the cockpit</a>'
      + '<a class="btn sm" href="refs.php?p=' + encodeURIComponent(pid) + '">🗂 References</a>'
      + '<a class="btn sm" href="shots.php?p=' + encodeURIComponent(pid) + '">📑 Production guide</a>'
      + '</div>'
      + '<div class="muted" style="font-size:12px;margin-top:10px">Next: the worker picks up the queued reference job and generates the reference set. Approve the refs, lock them, then queue page generation from the cockpit. Run the 🛡 SFW QA scan here (or the cockpit 🔎 QA) as images land.</div>'
      + '</div>';
    out.hidden = false;
    btn.disabled = false;
  })
  .catch(function(e) {
    var at = (e && e.at) || 'premise';
    step(at, 'err', (e && e.msg) || 'Request failed — check your connection and try again.');
    btn.disabled = false;
  });
});
function esc(s){ var d = document.createElement('div'); d.textContent = String(s == null ? '' : s); return d.innerHTML; }
// ---- SFW QA scan: loop every image in a project through do=gg_qa -----------
// One image per request (no PHP timeout); rescans everything, including images
// an earlier pass already verdicted, so a re-run picks up newly landed panels.
function ggQaScan(pid, btn) {
  btn.disabled = true;
  var label = btn.textContent;
  post('growgetter.php', {do:'gg_images', pid:pid}).then(function(r) {
    if (!r.ok) throw r.err;
    var files = r.images.map(function(x){ return x.file; });
    var i = 0, pass = 0, warn = 0, fail = 0;
    function next() {
      if (i >= files.length) {
        btn.textContent = '🛡 ' + pass + '✓ ' + warn + '⚠ ' + fail + '✗ — rescan';
        btn.disabled = false;
        return;
      }
      var f = files[i++];
      btn.textContent = '🛡 scanning ' + i + '/' + files.length + '…';
      post('growgetter.php', {do:'gg_qa', pid:pid, file:f}).then(function(q) {
        if (q.ok) { if (q.verdict === 'pass') pass++; else if (q.verdict === 'warn') warn++; else fail++; }
        next();
      }).catch(next);
    }
    if (!files.length) { btn.textContent = '🛡 no images yet'; btn.disabled = false; return; }
    next();
  }).catch(function(e) {
    btn.textContent = label; btn.disabled = false;
    alert('QA scan failed: ' + e);
  });
}
</script>
</body></html>
