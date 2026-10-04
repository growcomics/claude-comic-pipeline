/* Creator Pulse — accounts + data layer.
   Each account renders from a DB object. Data source priority:
     1. data/<accountId>.json  — real data written by tools/sync_patreon.py
     2. makeDemoData(profile)  — deterministic seeded demo data
   To hook up a real Patreon account, see the Account page or README.md. */

// ---------- built-in accounts ----------
const BUILTIN_ACCOUNTS = [
  {
    id: 'bloom',
    name: 'Bloom Beauty Comics',
    profile: {
      seed: 987654321, creator: 'Bloom Beauty Comics', initials: 'BB',
      tiers: {
        a: { label: 'Shape Seeker', color: '#4a69dd' },
        b: { label: 'Founders Tier', color: '#b7392b' },
        c: { label: 'Full Bloom', color: '#f0a13a' },
        none: { label: '[No associated tier]', color: '#3d8b4f' }
      },
      prices: { a: 4.5, b: 10, c: 13.2 },
      countA: { start: 3, targets: [[0, 3], [0.8, 6], [1, 10]] },
      countB: 9,
      countC: { start: 60, targets: [[0, 62], [0.55, 66], [0.85, 60], [1, 55]] },
      free: { start: 98, targets: [[0, 100], [0.5, 108], [0.9, 113], [1, 115]] },
      former: 402, declined: 6, years: [18, 41, 89],
      stats: { patrons: 74, earningsPerMonth: 923.35, churnPct: 48.235, retentionMonths: 2.07, avgPledge: 12.47, lifetimeValue: 25.85 },
      // real cohort table captured from the live service
      cohorts: [
        { month: 'August 2025', n: 21, pct: [90, 62, 52, 48, 43, 33, 33, 33, 33, 33, 33, 33] },
        { month: 'September 2025', n: 49, pct: [78, 53, 47, 47, 47, 43, 43, 43, 43, 43, 43] },
        { month: 'October 2025', n: 20, pct: [75, 55, 55, 50, 50, 45, 45, 45, 45, 45] },
        { month: 'November 2025', n: 33, pct: [91, 58, 48, 33, 27, 24, 24, 21, 21] },
        { month: 'December 2025', n: 27, pct: [81, 63, 59, 52, 44, 44, 41, 41] },
        { month: 'January 2026', n: 31, pct: [68, 42, 42, 42, 42, 35, 35] },
        { month: 'February 2026', n: 24, pct: [79, 50, 46, 42, 33, 33] },
        { month: 'March 2026', n: 37, pct: [73, 27, 22, 22, 22] },
        { month: 'April 2026', n: 36, pct: [69, 44, 36, 36] },
        { month: 'May 2026', n: 42, pct: [76, 43, 43] },
        { month: 'June 2026', n: 45, pct: [71, 64] },
        { month: 'July 2026', n: 4, pct: [100] }
      ]
    }
  },
  {
    id: 'growgetter',
    name: 'GrowGetter Muscle Growth',
    profile: {
      seed: 24681357, creator: 'GrowGetter Muscle Growth', initials: 'GG',
      tiers: {
        a: { label: 'Pump Club', color: '#4a69dd' },
        b: { label: 'OG Growers', color: '#b7392b' },
        c: { label: 'Max Mass', color: '#f0a13a' },
        none: { label: '[No associated tier]', color: '#3d8b4f' }
      },
      prices: { a: 5, b: 15, c: 12 },
      countA: { start: 10, targets: [[0, 10], [1, 22]] },
      countB: 12,
      countC: { start: 150, targets: [[0, 152], [0.6, 175], [1, 190]] },
      free: { start: 300, targets: [[0, 305], [1, 380]] },
      former: 610, declined: 14, years: [35, 120, 240]
    }
  },
  {
    id: 'maxx',
    name: 'Maxx Muscle Comics',
    profile: {
      seed: 55501234, creator: 'Maxx Muscle Comics', initials: 'MM',
      tiers: {
        a: { label: 'Flex Fan', color: '#4a69dd' },
        b: { label: 'Iron Circle', color: '#b7392b' },
        c: { label: 'Titan Tier', color: '#f0a13a' },
        none: { label: '[No associated tier]', color: '#3d8b4f' }
      },
      prices: { a: 3, b: 8, c: 10 },
      countA: { start: 2, targets: [[0, 2], [1, 5]] },
      countB: 4,
      countC: { start: 30, targets: [[0, 30], [0.7, 36], [1, 33]] },
      free: { start: 60, targets: [[0, 60], [1, 75]] },
      former: 150, declined: 3, years: [8, 22, 40]
    }
  },
  {
    id: 'giantess',
    name: 'GiantessGirlComics',
    profile: {
      seed: 77733311, creator: 'GiantessGirlComics', initials: 'GC',
      tiers: {
        a: { label: 'Lookout', color: '#4a69dd' },
        b: { label: 'Keepers', color: '#b7392b' },
        c: { label: 'Colossal', color: '#f0a13a' },
        none: { label: '[No associated tier]', color: '#3d8b4f' }
      },
      prices: { a: 3, b: 7, c: 9 },
      countA: { start: 1, targets: [[0, 1], [1, 3]] },
      countB: 2,
      countC: { start: 12, targets: [[0, 12], [1, 15]] },
      free: { start: 25, targets: [[0, 25], [1, 40]] },
      former: 55, declined: 1, years: [2, 9, 16]
    }
  }
];

// ---------- custom accounts (added via the Account page, stored locally) ----------
const CUSTOM_KEY = 'cp-custom-accounts';
function customAccounts() { return JSON.parse(localStorage.getItem(CUSTOM_KEY) || '[]'); }
function saveCustomAccounts(list) { localStorage.setItem(CUSTOM_KEY, JSON.stringify(list)); }

function hashCode(str) {
  let h = 2166136261;
  for (let i = 0; i < str.length; i++) { h ^= str.charCodeAt(i); h = Math.imul(h, 16777619); }
  return h >>> 0;
}

function profileForCustom(acc) {
  const h = hashCode(acc.name);
  const scale = 15 + (h % 180);
  return {
    seed: h, creator: acc.name, initials: acc.initials,
    tiers: {
      a: { label: 'Supporter', color: '#4a69dd' },
      b: { label: 'Insider', color: '#b7392b' },
      c: { label: 'Superfan', color: '#f0a13a' },
      none: { label: '[No associated tier]', color: '#3d8b4f' }
    },
    prices: { a: 3, b: 10, c: 8 },
    countA: { start: Math.max(1, Math.round(scale * 0.06)), targets: [[0, Math.max(1, Math.round(scale * 0.06))], [1, Math.max(2, Math.round(scale * 0.12))]] },
    countB: Math.max(1, Math.round(scale * 0.08)),
    countC: { start: Math.round(scale * 0.8), targets: [[0, Math.round(scale * 0.8)], [0.6, Math.round(scale * 0.95)], [1, Math.round(scale * 0.85)]] },
    free: { start: Math.round(scale * 1.4), targets: [[0, Math.round(scale * 1.4)], [1, Math.round(scale * 1.9)]] },
    former: Math.round(scale * 4), declined: Math.max(1, Math.round(scale * 0.07)),
    years: [Math.round(scale * 0.2), Math.round(scale * 0.55), Math.round(scale * 1.1)]
  };
}

function listAccounts() {
  return [
    ...BUILTIN_ACCOUNTS.map(a => ({ ...a, custom: false })),
    ...customAccounts().map(a => ({ ...a, profile: profileForCustom(a), custom: true }))
  ];
}

// ---------- demo data factory ----------
function makeDemoData(profile, accountId) {
  let seed = profile.seed >>> 0 || 1;
  const rnd = () => {
    seed = (seed * 1664525 + 1013904223) >>> 0;
    return seed / 4294967296;
  };

  const DAY = 86400000;
  const START = Date.UTC(2025, 7, 1);   // Aug 1 2025
  const END = Date.UTC(2026, 6, 6);     // Jul 6 2026 ("today")
  const dates = [];
  for (let t = START; t <= END; t += DAY) dates.push(new Date(t).toISOString().slice(0, 10));
  const N = dates.length;

  function walk(startVal, targets, noise, round, min = 0) {
    const out = [];
    let v = startVal;
    for (let i = 0; i < N; i++) {
      const f = i / (N - 1);
      let tv = targets[targets.length - 1][1];
      for (let k = 0; k < targets.length - 1; k++) {
        if (f >= targets[k][0] && f <= targets[k + 1][0]) {
          const span = targets[k + 1][0] - targets[k][0];
          const p = span === 0 ? 0 : (f - targets[k][0]) / span;
          tv = targets[k][1] + (targets[k + 1][1] - targets[k][1]) * p;
          break;
        }
      }
      v += (tv - v) * 0.12 + (rnd() - 0.5) * noise;
      v = Math.max(min, v);
      out.push(round ? Math.round(v) : +v.toFixed(2));
    }
    return out;
  }

  const spikes = (pMax, vMax) => Array.from({ length: N }, () => (rnd() < pMax ? Math.ceil(rnd() * vMax) : 0));

  const S = {};
  const sizeScale = Math.max(0.5, (profile.countC.start + profile.countB + profile.countA.start) / 70);

  // patron counts
  S.countC = walk(profile.countC.start, profile.countC.targets, 1.4 * sizeScale, true);
  S.countB = walk(profile.countB, [[0, profile.countB], [1, profile.countB]], 0.15, true);
  S.countA = walk(profile.countA.start, profile.countA.targets, 0.8, true);
  S.supporting = S.countC.map((v, i) => v + S.countB[i] + S.countA[i]);
  S.freePatrons = walk(profile.free.start, profile.free.targets, 0.35, true);

  // money
  const P = profile.prices;
  S.earnC = S.countC.map(v => +(v * P.c * (0.97 + rnd() * 0.06)).toFixed(2));
  S.earnB = S.countB.map(v => +(v * P.b).toFixed(2));
  S.earnA = S.countA.map(v => +(v * P.a * (0.95 + rnd() * 0.1)).toFixed(2));
  S.earnings = S.earnC.map((v, i) => +(v + S.earnB[i] + S.earnA[i]).toFixed(2));

  S.avgPledge = S.earnings.map((v, i) => +(v / Math.max(1, S.supporting[i])).toFixed(2));
  S.avgPledgeC = S.earnC.map((v, i) => +(v / Math.max(1, S.countC[i])).toFixed(2));
  S.avgPledgeB = S.countB.map(() => P.b);
  S.avgPledgeA = S.earnA.map((v, i) => +(v / Math.max(1, S.countA[i])).toFixed(2));

  // retention (months)
  S.retention = walk(1.25, [[0, 1.3], [0.7, 1.7], [0.94, 1.75], [1, 2.07]], 0.05, false);
  S.retentionC = walk(1.6, [[0, 1.7], [1, 2.3]], 0.05, false);
  S.retentionB = walk(10, [[0, 10], [1, 10.1]], 0.01, false);
  S.retentionA = walk(0.4, [[0, 0.5], [1, 1.1]], 0.04, false);
  S.retentionNone = walk(3.1, [[0, 3.1], [1, 3.3]], 0.02, false);

  // lifetime value
  S.ltv = S.avgPledge.map((v, i) => +(v * S.retention[i]).toFixed(2));
  S.ltvC = S.avgPledgeC.map((v, i) => +(v * S.retentionC[i]).toFixed(2));
  S.ltvB = S.avgPledgeB.map((v, i) => +(v * S.retentionB[i]).toFixed(2));
  S.ltvA = S.avgPledgeA.map((v, i) => +(v * S.retentionA[i]).toFixed(2));

  // cumulative total pledged
  let cumC = profile.countC.start * P.c * 9, cumB = profile.countB * P.b * 9, cumA = profile.countA.start * P.a * 9;
  S.totalPledged = []; S.totalPledgedC = []; S.totalPledgedB = []; S.totalPledgedA = [];
  for (let i = 0; i < N; i++) {
    if (dates[i].slice(8) === '01') {
      cumC += S.earnC[i]; cumB += S.earnB[i]; cumA += S.earnA[i];
    }
    S.totalPledgedC.push(+cumC.toFixed(2));
    S.totalPledgedB.push(+cumB.toFixed(2));
    S.totalPledgedA.push(+cumA.toFixed(2));
    S.totalPledged.push(+(cumC + cumB + cumA).toFixed(2));
  }

  // payments
  S.paid = dates.map((d, i) => {
    const dom = +d.slice(8);
    if (dom <= 3) return +(S.earnings[i] * (0.3 - dom * 0.08) * (0.9 + rnd() * 0.2) * 3).toFixed(2);
    return +(rnd() < 0.35 ? rnd() * 40 * sizeScale : 0).toFixed(2);
  });
  S.refunded = dates.map(() => (rnd() < 0.03 ? +(rnd() * 26 * sizeScale).toFixed(2) : 0));
  S.lostEarnings = dates.map(() => (rnd() < 0.3 ? +(rnd() * 55 * sizeScale).toFixed(2) : 0));

  // growth percentages
  const growth30 = arr => arr.map((v, i) => (i < 30 ? null : +(((v - arr[i - 30]) / Math.max(1e-6, arr[i - 30])) * 100).toFixed(2)));
  S.earningsGrowth30 = growth30(S.earnings);
  S.supportingGrowth30 = growth30(S.supporting);

  // events
  const evScale = Math.min(3, Math.max(1, Math.round(sizeScale)));
  S.newPatrons = spikes(0.7, 4 * evScale);
  S.newPatronsC = S.newPatrons.map(v => (v > 0 ? Math.round(v * 0.7) : 0));
  S.newPatronsA = S.newPatrons.map((v, i) => v - S.newPatronsC[i]);
  S.upgrades = spikes(0.18, 2 * evScale);
  S.upgradesC = S.upgrades.map(v => (v > 0 && rnd() < 0.75 ? v : 0));
  S.upgradesA = S.upgrades.map((v, i) => v - S.upgradesC[i]);
  S.downgrades = spikes(0.1, 2 * evScale);
  S.downgradesC = S.downgrades.map(v => (v > 0 && rnd() < 0.8 ? v : 0));
  S.downgradesA = S.downgrades.map((v, i) => v - S.downgradesC[i]);
  S.comebacks = spikes(0.3, 5 * evScale);
  S.comebacksC = S.comebacks.map(v => (v > 0 ? Math.round(v * 0.6) : 0));
  S.comebacksA = S.comebacks.map((v, i) => v - S.comebacksC[i]);
  S.cancels = spikes(0.55, 4 * evScale);
  S.cancelsC = S.cancels.map(v => (v > 0 ? Math.round(v * 0.65) : 0));
  S.cancelsA = S.cancels.map((v, i) => v - S.cancelsC[i]);
  S.paymentFails = spikes(0.35, 3 * evScale);
  S.paymentFailsC = S.paymentFails.map(v => (v > 0 ? Math.round(v * 0.7) : 0));
  S.paymentFailsA = S.paymentFails.map((v, i) => v - S.paymentFailsC[i]);

  const lost = S.cancels.map((v, i) => v + S.paymentFails[i]);
  S.lostPct30 = lost.map((_, i) => {
    if (i < 30) return null;
    let a = 0, b = 0;
    for (let k = i - 29; k <= i; k++) a += lost[k];
    for (let k = Math.max(0, i - 59); k <= i - 30; k++) b += lost[k];
    return b === 0 ? null : +(((a - b) / b) * 100).toFixed(2);
  });
  S.lostPct30C = S.lostPct30.map(v => (v == null ? null : +(v * (0.8 + rnd() * 0.4)).toFixed(2)));
  S.lostPct30A = S.lostPct30.map(v => (v == null ? null : +(v * (0.5 + rnd() * 0.9)).toFixed(2)));

  // ---- overview ----
  const patrons = profile.stats?.patrons ?? S.supporting[N - 1];
  const monthIdx = m => dates.indexOf(`2026-0${m}-01`);
  const heroMonths = {
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Today'],
    data: [1, 2, 3, 4, 5, 6, 7].map(m => S.supporting[Math.max(0, monthIdx(m))]).concat([patrons])
  };
  const yearLabels = [];
  for (let i = profile.years.length; i >= 1; i--) yearLabels.push(String(2026 - i));
  const heroYears = { labels: [...yearLabels, '2026'], data: [...profile.years, patrons] };

  const last30lost = lost.slice(-30).reduce((a, b) => a + b, 0);
  const stats = profile.stats || {
    patrons,
    earningsPerMonth: S.earnings[N - 1],
    churnPct: +((last30lost / Math.max(1, patrons + last30lost)) * 100).toFixed(3),
    retentionMonths: +S.retention[N - 1].toFixed(2),
    avgPledge: S.avgPledge[N - 1],
    lifetimeValue: S.ltv[N - 1]
  };

  const overview = {
    creator: profile.creator,
    initials: profile.initials,
    patrons,
    patronsByMonth: heroMonths,
    patronsByYear: heroYears,
    pie: { active: patrons, declined: profile.declined, former: profile.former },
    stats,
    lastSynced: 'July 6, 2026 7:04am'
  };

  // ---- activity ----
  const names = ['nicolas', 'T9ast', 'MuscleFanX', 'Britt_88', 'kaijuu', 'pauline', 'D3rrick', 'hyperGrowthFan', 'sam_v', 'Odette', 'flexAppeal', 'jmarch', 'Wrenna', 'bulkmode', 'quietwolf'];
  const tierNames = [profile.tiers.c.label, profile.tiers.a.label, profile.tiers.b.label];
  const kinds = [
    { k: 'paid', t: (n, tier) => `${n} paid for ${tier}` },
    { k: 'upgrade', t: (n, tier) => `${n} upgraded to ${tier}` },
    { k: 'pledge', t: (n, tier) => `${n} started pledging for ${tier}` }
  ];
  const activity = [];
  let evT = Date.UTC(2026, 6, 5, 21, 6);
  for (let i = 0; i < 60; i++) {
    const kind = kinds[Math.floor(rnd() * kinds.length)];
    const n = names[Math.floor(rnd() * names.length)];
    const tier = tierNames[Math.floor(rnd() * (rnd() < 0.7 ? 2 : 3))];
    const d = new Date(evT);
    activity.push({
      kind: kind.k,
      text: kind.t(n, tier),
      when: d.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric', timeZone: 'UTC' }) + ' ' +
            d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', timeZone: 'UTC' }).toLowerCase().replace(' ', '')
    });
    evT -= (0.5 + rnd() * 9) * 3600000;
  }

  // ---- cohorts ----
  let cohorts = profile.cohorts;
  if (!cohorts) {
    const months = ['August 2025', 'September 2025', 'October 2025', 'November 2025', 'December 2025',
      'January 2026', 'February 2026', 'March 2026', 'April 2026', 'May 2026', 'June 2026', 'July 2026'];
    cohorts = months.map((month, i) => {
      const slots = 12 - i;
      const n = Math.max(1, Math.round((3 + rnd() * 12) * sizeScale * 0.6));
      const pct = [];
      let p = 65 + rnd() * 30;
      for (let k = 0; k < slots; k++) {
        pct.push(Math.round(p));
        p *= k === 0 ? 0.5 + rnd() * 0.35 : 0.85 + rnd() * 0.15;
      }
      return { month, n, pct };
    });
  }

  // ---- patrons page ----
  const peerPages = BUILTIN_ACCOUNTS
    .filter(a => a.id !== accountId)
    .map(a => ({ name: a.name, nsfw: true, patrons: Math.max(1, Math.round((1 + rnd() * 8) * sizeScale)) }))
    .slice(0, 3);

  const curMix = [
    ['United States dollar (USD)', 0.77], ['Euro (EUR)', 0.09], ['Pound sterling (GBP)', 0.028],
    ['Canadian dollar (CAD)', 0.028], ['Polish złoty (PLN)', 0.024], ['Singapore dollar (SGD)', 0.014],
    ['Norwegian krone (NOK)', 0.013], ['Brazilian real (BRL)', 0.012], ['Swedish krona (SEK)', 0.011]
  ];
  const currencies = curMix.map(([label, f], i) => [label, Math.max(i < 2 ? 1 : 0, Math.round(patrons * f))])
    .filter(c => c[1] > 0);

  const histShare = fracs => fracs.map(f => Math.round(patrons * f));
  const startYears = { labels: ['2020', '2021', '2022', '2023', '2024', '2025', '2026'], data: histShare([0.013, 0.027, 0.04, 0.08, 0.12, 0.35, 0.36]) };
  const startMonths = { labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], data: histShare([0.095, 0.068, 0.081, 0.108, 0.122, 0.149, 0.081, 0.054, 0.081, 0.054, 0.068, 0.04]) };
  const startDaysOfMonth = { labels: Array.from({ length: 31 }, (_, i) => String(i + 1)), data: Array.from({ length: 31 }, () => Math.floor(rnd() * 5 * sizeScale)) };
  const startWeekdays = { labels: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'], data: histShare([0.162, 0.122, 0.149, 0.135, 0.176, 0.108, 0.149]) };
  const startHours = { labels: Array.from({ length: 24 }, (_, i) => String(i)), data: Array.from({ length: 24 }, () => Math.floor(rnd() * 7 * sizeScale)) };

  // ---- emails ----
  const emails = {
    planNote: 'From this page, you can set emails that are automatically sent to your patrons on specific days and occasions.',
    planDetail: 'Your plan includes 20,000 emails/month; each extra package of 20,000 emails is charged $15 + sales tax. Any unused credit is not rolled over to the next month.',
    currentMonth: Math.max(1, Math.round(patrons * 0.12)),
    lastMonth: Math.max(2, Math.round(patrons * 1.01)),
    drips: [
      { id: 'joined3d', title: '3 days after a patron joined your page', enabled: false },
      { id: 'digest1w', title: 'every 1 week send a recurring digest of recent posts', enabled: false },
      { id: 'support1d', title: '1 day after a patron started supporting you continuously', enabled: true, tiers: 1, sent: Math.round(patrons * 9.5), clicks: Math.round(patrons * 0.23), uniqueClicks: Math.round(patrons * 0.12) },
      { id: 'support1y', title: '1 year after a patron started supporting you continuously', enabled: false },
      { id: 'declined3d', title: '3 days after a payment is declined', enabled: false }
    ]
  };

  return {
    accountId, live: false,
    dates, series: S, overview, activity, cohorts,
    peerPages, currencies, startYears, startMonths, startDaysOfMonth, startWeekdays, startHours,
    emails,
    tiers: profile.tiers
  };
}

// ---------- account loading ----------
var DB = null;

async function loadAccount(id) {
  const accounts = listAccounts();
  const acc = accounts.find(a => a.id === id) || accounts[0];
  // prefer real synced data if tools/sync_patreon.py has written it.
  // Served through the session-gated passthrough (data.php) so revenue JSON is never
  // publicly fetchable; a 4xx (not authed / no data yet) falls through to demo data.
  try {
    const r = await fetch('data.php?acct=' + encodeURIComponent(acc.id), { cache: 'no-store' });
    if (r.ok) {
      DB = await r.json();
      DB.accountId = acc.id;
      DB.live = true;
      return acc.id;
    }
  } catch (e) { /* no synced data — fall back to demo */ }
  DB = makeDemoData(acc.profile, acc.id);
  return acc.id;
}
