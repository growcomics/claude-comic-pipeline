<?php
// patreon-sync.php — pulls live member counts for all Patreon accounts via the
// API v2 creator tokens and caches them in data/patreon-stats.json.
// Tokens live OUTSIDE the web root (<home>/private/patreon-tokens.json).
// Auth: studio session OR bridge key. GET ?back=1 redirects to the posting board.
declare(strict_types=1);
require_once __DIR__ . '/inc/boot.php';

function ps_bridge_ok(): bool {
    $cfg = s_read(SDATA . '/bridge.json', array());
    $key = (string)($cfg['key'] ?? '');
    $given = (string)($_POST['key'] ?? $_GET['key'] ?? ($_SERVER['HTTP_X_BRIDGE_KEY'] ?? ''));
    return $key !== '' && strlen($given) >= 16 && hash_equals($key, $given);
}
$keyAuthed = ps_bridge_ok();
if (!$keyAuthed) require_auth();

$tokFile = dirname(dirname(STUDIO_ROOT)) . '/private/patreon-tokens.json';
$tokens = is_file($tokFile) ? json_decode((string)file_get_contents($tokFile), true) : null;
if (!is_array($tokens) || !$tokens) {
    http_response_code(500);
    header('Content-Type: application/json');
    exit(json_encode(array('ok' => false, 'error' => 'token file missing/unreadable: ' . basename($tokFile))));
}

$stats = array('ts' => gmdate('c'), 'accounts' => array());
foreach ($tokens as $key => $t) {
    $out = array('ok' => false, 'members' => null, 'url' => '');
    $cid = preg_replace('/[^0-9]/', '', (string)($t['campaign_id'] ?? ''));
    if ($cid === '' || empty($t['access_token'])) {
        $out['error'] = 'missing campaign_id/token';
        $stats['accounts'][$key] = $out;
        continue;
    }
    $ch = curl_init('https://www.patreon.com/api/oauth2/v2/campaigns/' . $cid . '?' . http_build_query(array(
        'fields[campaign]' => 'patron_count,url',
    )));
    curl_setopt_array($ch, array(
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 15,
        CURLOPT_HTTPHEADER => array('Authorization: Bearer ' . $t['access_token']),
    ));
    $body = curl_exec($ch);
    $code = (int)curl_getinfo($ch, CURLINFO_RESPONSE_CODE);
    curl_close($ch);
    $j = is_string($body) ? json_decode($body, true) : null;
    $attrs = $j['data']['attributes'] ?? null;
    if ($code === 200 && is_array($attrs)) {
        $out['ok'] = true;
        $out['members'] = (int)($attrs['patron_count'] ?? 0);
        $out['url'] = (string)($attrs['url'] ?? '');
    } else {
        $out['error'] = 'http ' . $code . (isset($j['errors'][0]['code_name']) ? ' ' . $j['errors'][0]['code_name'] : '');
    }
    $stats['accounts'][$key] = $out;
}
s_write(SDATA . '/patreon-stats.json', $stats);

if (isset($_GET['back'])) {
    $suffix = $keyAuthed ? '?key=' . urlencode((string)($_GET['key'] ?? '')) : '';
    header('Location: posting.php' . $suffix);
    exit;
}
header('Content-Type: application/json');
echo json_encode($stats, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES);
