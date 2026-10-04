/* Creator Pulse — app shell: accounts, hash router, chart cards, CSV export, annotations. */

const PINK = '#d94f63';
let T = null; // current account's tier config, set on account load
Chart.defaults.font.family = '"Nunito Sans", sans-serif';
Chart.defaults.color = '#8a8f9c';

// ---------- utils ----------
const $ = sel => document.querySelector(sel);
const app = $('#app');
const money = v => '$' + Number(v).toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 2 });
const html = (strings, ...vals) => strings.map((s, i) => s + (vals[i] ?? '')).join('');

function fmtAxisDate(iso) {
  const d = new Date(iso + 'T00:00:00Z');
  return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', timeZone: 'UTC' });
}

let liveCharts = [];
function destroyCharts() { liveCharts.forEach(c => c.destroy()); liveCharts = []; }

// per-page date range (defaults mirror the original: last 45 days)
const range = { from: '2026-05-22', to: '2026-07-06' };

function sliceRange() {
  let a = DB.dates.findIndex(d => d >= range.from);
  if (a < 0) a = 0;
  let b = DB.dates.length - 1;
  while (b > 0 && DB.dates[b] > range.to) b--;
  return [a, b];
}

// ---------- annotations (click chart to add, click same date to remove) ----------
const ANN_KEY = 'cp-annotations';
const annotations = JSON.parse(localStorage.getItem(ANN_KEY) || '{}');
function saveAnn() { localStorage.setItem(ANN_KEY, JSON.stringify(annotations)); }

const annotationPlugin = {
  id: 'cpAnnotations',
  afterDraw(chart) {
    const list = annotations[chart.$cpId] || [];
    if (!list.length) return;
    const { ctx, chartArea, scales } = chart;
    list.forEach(a => {
      const idx = chart.data.labels.indexOf(a.x);
      if (idx < 0) return;
      const px = scales.x.getPixelForValue(idx);
      ctx.save();
      ctx.strokeStyle = '#052d49';
      ctx.setLineDash([4, 4]);
      ctx.beginPath();
      ctx.moveTo(px, chartArea.top);
      ctx.lineTo(px, chartArea.bottom);
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle = '#052d49';
      ctx.font = '700 11px "Nunito Sans"';
      ctx.textAlign = px > chartArea.right - 120 ? 'right' : 'left';
      ctx.fillText(a.label, px + (ctx.textAlign === 'left' ? 5 : -5), chartArea.top + 12);
      ctx.restore();
    });
  }
};
Chart.register(annotationPlugin);

// ---------- chart card factory ----------
function chartCard(spec, labels, datasets, opts = {}) {
  const card = document.createElement('div');
  card.className = 'card chart-card';
  card.innerHTML = html`
    <h2><span class="hash">#</span>${spec.title}</h2>
    <div class="chart-wrap"><canvas></canvas></div>
    <div class="chart-foot">
      <span>Tip: Click the chart to add an annotation, hover to view it, and click the annotation to remove it.</span>
      <a href="#" data-csv>Export CSV</a>
    </div>`;

  const canvas = card.querySelector('canvas');
  const type = spec.type || 'line';
  const chart = new Chart(canvas, {
    type,
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: datasets.length > 1
          ? { position: 'top', labels: { boxWidth: 26, boxHeight: 12, font: { size: 11 } } }
          : { display: false },
        tooltip: {
          callbacks: {
            label: c => (c.dataset.label ? c.dataset.label + ': ' : '') +
              (spec.money ? money(c.parsed.y) : c.parsed.y + (spec.suffix || ''))
          }
        }
      },
      scales: (opts.chartOpts && opts.chartOpts.indexAxis === 'y')
        ? {
            y: { grid: { display: false }, ticks: { autoSkip: false, font: { size: 11 } } },
            x: {
              border: { display: false }, grid: { color: '#eef0f4' }, beginAtZero: true,
              ticks: { font: { size: 11 }, precision: 0 }
            }
          }
        : {
            x: {
              grid: { display: false },
              ticks: {
                maxTicksLimit: spec.xTicks || 12, maxRotation: 0, font: { size: 11 },
                callback(v) { const l = this.getLabelForValue(v); return spec.rawX ? l : fmtAxisDate(l); }
              }
            },
            y: {
              border: { display: false },
              grid: { color: '#eef0f4' },
              beginAtZero: !!spec.zero,
              ticks: {
                maxTicksLimit: 6, font: { size: 11 },
                callback: v => spec.money ? money(v) : v + (spec.suffix || ''),
                precision: 0
              }
            }
          },
      ...(opts.chartOpts || {})
    }
  });
  chart.$cpId = DB.accountId + '|' + spec.title; // annotation bucket, scoped per account
  liveCharts.push(chart);

  // click → add / remove annotation
  canvas.addEventListener('click', evt => {
    const pts = chart.scales.x;
    const rect = canvas.getBoundingClientRect();
    const x = evt.clientX - rect.left;
    if (x < chart.chartArea.left || x > chart.chartArea.right) return;
    const idx = Math.round(pts.getValueForPixel(x));
    const label = chart.data.labels[Math.min(Math.max(idx, 0), chart.data.labels.length - 1)];
    const bucket = annotations[chart.$cpId] || (annotations[chart.$cpId] = []);
    const existing = bucket.findIndex(a => a.x === label);
    if (existing >= 0) {
      bucket.splice(existing, 1);
    } else {
      const note = prompt('Annotation for ' + label + ':');
      if (!note) return;
      bucket.push({ x: label, label: note });
    }
    saveAnn();
    chart.draw();
  });

  // CSV export
  card.querySelector('[data-csv]').addEventListener('click', evt => {
    evt.preventDefault();
    const head = ['date', ...datasets.map(d => d.label || spec.title)];
    const rows = labels.map((l, i) => [l, ...datasets.map(d => d.data[i] ?? '')]);
    const csv = [head, ...rows].map(r => r.map(c => '"' + String(c).replaceAll('"', '""') + '"').join(',')).join('\n');
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv' }));
    a.download = spec.title.toLowerCase().replace(/[^a-z0-9]+/g, '-') + '.csv';
    a.click();
    URL.revokeObjectURL(a.href);
  });

  return card;
}

const lineDs = (label, data, color, extra = {}) => ({
  label, data, borderColor: color, backgroundColor: color,
  borderWidth: 2, pointRadius: 0, pointHoverRadius: 4, tension: 0.25, spanGaps: true, ...extra
});
const barDs = (label, data, color) => ({
  label, data,
  backgroundColor: color ? color + '55' : 'rgba(217,79,99,.35)',
  borderColor: color || PINK, borderWidth: 1.5
});

// ---------- metric-page scaffolding ----------
function metricPage(title, buildCharts) {
  destroyCharts();
  app.innerHTML = html`
    <div class="page">
      <div class="page-head">
        <h1>${title}</h1>
        <div class="range-filter">
          From <input type="date" id="from" value="${range.from}">
          To <input type="date" id="to" value="${range.to}">
          <button class="btn" id="apply">Apply</button>
        </div>
      </div>
      <div id="charts"></div>
      <p class="last-synced">Last synced: ${DB.overview.lastSynced}</p>
    </div>`;

  const mount = $('#charts');
  const [a, b] = sliceRange();
  const labels = DB.dates.slice(a, b + 1);
  const cut = arr => (Array.isArray(arr) ? arr : []).slice(a, b + 1);
  buildCharts(mount, labels, cut);

  $('#apply').addEventListener('click', () => {
    range.from = $('#from').value || range.from;
    range.to = $('#to').value || range.to;
    metricPage(title, buildCharts);
  });
}

function tierLines(cut, a, b, c, extra) {
  const ds = [
    lineDs(T.a.label, cut(a), T.a.color),
    lineDs(T.b.label, cut(b), T.b.color),
    lineDs(T.c.label, cut(c), T.c.color)
  ];
  if (extra) ds.push(extra);
  return ds;
}

// ---------- pages ----------
function renderDashboard() {
  destroyCharts();
  const o = DB.overview;
  const s = o.stats;
  app.innerHTML = html`
    <div class="overview-grid">
      <div class="overview-main">
        <div class="welcome">
          <div class="avatar">${o.initials}</div>
          <div>
            <h1>Welcome back, ${o.creator}</h1>
            <p>Today is ${new Date().toLocaleDateString('en-US', { month: 'long', day: '2-digit', year: 'numeric' })}. Your Patreon analytics are all set. Look around and act.${DB.live ? '' : ' <em>(demo data)</em>'}</p>
          </div>
        </div>
        <div class="stat-grid">
          <div class="hero-card">
            <div class="hero-top">
              <div>
                <div class="big" id="hero-count">${o.patrons}</div>
                <div class="label">Patrons supporting you</div>
              </div>
              <div class="hero-toggle">
                <button class="on" data-mode="months">Months</button>
                <button data-mode="years">Years</button>
              </div>
            </div>
            <div class="hero-chart"><canvas id="hero-canvas"></canvas></div>
          </div>
          <div class="stat-card tall" style="grid-column: span 1;">
            <div class="pie-wrap"><canvas id="pie-canvas"></canvas></div>
          </div>
          <div class="stat-card">
            ${statIcon('bars')}
            <div class="value">${money(s.earningsPerMonth)}</div>
            <div class="desc">Estimated earnings per month</div>
          </div>
          <div class="stat-card">
            ${statIcon('bars')}
            <div class="value">${s.churnPct}%</div>
            <div class="desc">Of your patrons stopped supporting you last month</div>
          </div>
          <div class="stat-card">
            ${statIcon('trend')}
            <div class="value">${s.retentionMonths} months</div>
            <div class="desc">How long your patrons support you on average</div>
          </div>
          <div class="stat-card">
            ${statIcon('bars')}
            <div class="value">${money(s.avgPledge)}</div>
            <div class="desc">Average amount pledged by your patrons</div>
          </div>
          <div class="stat-card">
            ${statIcon('trend')}
            <div class="value">${money(s.lifetimeValue)}</div>
            <div class="desc">Estimated lifetime amount pledged by your patrons</div>
          </div>
        </div>
        <p class="last-synced">Last synced: ${o.lastSynced}</p>
      </div>
      <aside class="activity">
        <h2>Activity</h2>
        <div id="feed"></div>
        <button class="load-more" id="more">Load more</button>
      </aside>
    </div>`;

  // hero sparkline
  let heroChart = null;
  function drawHero(mode) {
    const src = mode === 'years' ? o.patronsByYear : o.patronsByMonth;
    if (heroChart) { heroChart.destroy(); liveCharts = liveCharts.filter(c => c !== heroChart); }
    heroChart = new Chart($('#hero-canvas'), {
      type: 'line',
      data: {
        labels: src.labels,
        datasets: [{
          data: src.data, borderColor: '#fff', borderWidth: 2.5,
          pointRadius: 3.5, pointBackgroundColor: '#fff', tension: 0.3
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false, animation: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false }, ticks: { color: 'rgba(255,255,255,.95)', font: { size: 12, weight: 700 }, maxRotation: 0, autoSkip: false } },
          y: { display: false, suggestedMin: Math.min(...src.data) - 8 }
        }
      }
    });
    liveCharts.push(heroChart);
  }
  drawHero('months');
  document.querySelectorAll('.hero-toggle button').forEach(b =>
    b.addEventListener('click', () => {
      document.querySelectorAll('.hero-toggle button').forEach(x => x.classList.remove('on'));
      b.classList.add('on');
      drawHero(b.dataset.mode);
    }));

  // pie
  liveCharts.push(new Chart($('#pie-canvas'), {
    type: 'pie',
    data: {
      labels: ['Active patrons', 'Declined patrons', 'Former patrons'],
      datasets: [{
        data: [o.pie.active, o.pie.declined, o.pie.former],
        backgroundColor: ['#2e6fd8', '#e0637a', '#c9ccd6'],
        borderWidth: 1, borderColor: '#fff'
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false, animation: false,
      plugins: { legend: { position: 'top', labels: { boxWidth: 24, boxHeight: 12, font: { size: 10.5 } } } }
    }
  }));

  // activity feed
  let shown = 0;
  const feed = $('#feed');
  function loadMore(n) {
    DB.activity.slice(shown, shown + n).forEach(ev => {
      const div = document.createElement('div');
      div.className = 'event';
      const dot = ev.kind === 'paid' ? ['dot-paid', '$'] : ev.kind === 'upgrade' ? ['dot-upgrade', '↑'] : ['dot-pledge', '♥'];
      div.innerHTML = html`
        <div class="dot ${dot[0]}">${dot[1]}</div>
        <div><div class="what">${ev.text}</div><div class="when">${ev.when}</div></div>`;
      feed.appendChild(div);
    });
    shown += n;
    if (shown >= DB.activity.length) $('#more').style.display = 'none';
  }
  loadMore(6);
  $('#more').addEventListener('click', () => loadMore(8));
}

function statIcon(kind) {
  const path = kind === 'trend'
    ? '<path d="M3 15l4-4 3 2 6-7" stroke="#d94f63" stroke-width="2.4" fill="none"/><rect x="2" y="17" width="18" height="2" rx="1"/>'
    : '<rect x="3" y="10" width="3" height="8" rx="1"/><rect x="8" y="6" width="3" height="12" rx="1"/><rect x="13" y="12" width="3" height="6" rx="1"/><rect x="17" y="8" width="3" height="10" rx="1"/>';
  return `<div class="stat-icon"><svg viewBox="0 0 22 22">${path}</svg></div>`;
}

// ----- Balance -----
function renderBalance() {
  metricPage('Balance', (mount, labels, cut) => {
    const S = DB.series;
    const add = (spec, ds) => mount.appendChild(chartCard(spec, labels, ds));
    add({ title: 'Your estimated earnings per month', money: true },
      [lineDs('Earnings', cut(S.earnings), PINK)]);
    add({ title: 'Your estimated earnings per month by tier', money: true },
      tierLines(cut, S.earnA, S.earnB, S.earnC));
    add({ title: 'How much each patron supports you on average each month', money: true },
      [lineDs('Average pledge', cut(S.avgPledge), PINK)]);
    add({ title: 'How much each patron supports you on average each month by tier', money: true },
      tierLines(cut, S.avgPledgeA, S.avgPledgeB, S.avgPledgeC));
    add({ title: 'How much you could expect in total from someone that starts supporting you', money: true },
      [lineDs('Expected lifetime value', cut(S.ltv), PINK)]);
    add({ title: 'How much you could expect in total from someone that starts supporting you by tier', money: true },
      tierLines(cut, S.ltvA, S.ltvB, S.ltvC));
    add({ title: "How much you've been pledged in total on Patreon", money: true },
      [lineDs('Total pledged', cut(S.totalPledged), PINK)]);
    add({ title: "How much you've been pledged in total on Patreon by tier", money: true },
      tierLines(cut, S.totalPledgedA, S.totalPledgedB, S.totalPledgedC));
    add({ title: 'The percentage of your earnings growth compared to 30 days before', suffix: '%' },
      [lineDs('Growth', cut(S.earningsGrowth30), PINK)]);
    add({ title: 'Amount of pledges that have been paid', money: true, type: 'bar', zero: true },
      [barDs('Paid', cut(S.paid))]);
    add({ title: 'Amount of pledges that have been refunded', money: true, type: 'bar', zero: true },
      [barDs('Refunded', cut(S.refunded))]);
    add({ title: "How much earnings you've lost", money: true, type: 'bar', zero: true },
      [barDs('Lost', cut(S.lostEarnings))]);
  });
}

// ----- Retention -----
function renderRetention() {
  metricPage('Retention', (mount, labels, cut) => {
    const S = DB.series;
    const add = (spec, ds) => mount.appendChild(chartCard(spec, labels, ds));
    add({ title: 'How long your patrons support you on average', suffix: ' months' },
      [lineDs('Average', cut(S.retention), PINK)]);
    add({ title: 'How long your patrons support you on average by tier', suffix: ' months' },
      tierLines(cut, S.retentionA, S.retentionB, S.retentionC,
        lineDs(T.none.label, cut(S.retentionNone), T.none.color)));
    add({ title: 'How many patrons came back to support you after canceling', type: 'bar', zero: true },
      [barDs('Comebacks', cut(S.comebacks))]);
    add({ title: 'How many patrons came back to support you after canceling by tier', type: 'bar', zero: true },
      [barDs(T.a.label, cut(S.comebacksA), T.a.color),
       barDs(T.c.label, cut(S.comebacksC), T.c.color)]);
    add({ title: 'How many patrons canceled or had their payment fail', type: 'bar', zero: true },
      [barDs('Canceled', cut(S.cancels)), barDs('Payment failed', cut(S.paymentFails), '#8a8f9c')]);
    add({ title: 'How many patrons canceled by tier', type: 'bar', zero: true },
      [barDs(T.a.label, cut(S.cancelsA), T.a.color),
       barDs(T.c.label, cut(S.cancelsC), T.c.color)]);
    add({ title: 'How many patrons had their payment fail by tier', type: 'bar', zero: true },
      [barDs(T.a.label, cut(S.paymentFailsA), T.a.color),
       barDs(T.c.label, cut(S.paymentFailsC), T.c.color)]);
    add({ title: 'The percentage of lost patrons compared to 30 days before', suffix: '%' },
      [lineDs('Lost patrons', cut(S.lostPct30), PINK)]);
    add({ title: 'The percentage of lost patrons compared to 30 days before by tier', suffix: '%' },
      [lineDs(T.a.label, cut(S.lostPct30A), T.a.color),
       lineDs(T.c.label, cut(S.lostPct30C), T.c.color)]);

    // cohort table
    if (DB.cohorts && DB.cohorts.length) {
      const card = document.createElement('div');
      card.className = 'card';
      const maxMonths = Math.max(...DB.cohorts.map(c => c.pct.length));
      card.innerHTML = html`
        <h2 style="text-align:center;font-size:17px;font-weight:800;margin-bottom:16px;">
          <span class="hash" style="color:${PINK}">#</span>
          How many patrons are still supporting you based on the month they started pledging
        </h2>
        <div class="cohort-scroll">
          <table class="cohort">
            <thead>
              <tr>
                <th style="text-align:left"></th><th>Patrons</th>
                <th colspan="${maxMonths}" style="text-align:left;color:#8a8f9c">Months since pledge start</th>
              </tr>
              <tr>
                <th></th><th></th>
                ${Array.from({ length: maxMonths }, (_, i) => `<th>${i}</th>`).join('')}
              </tr>
            </thead>
            <tbody>
              ${DB.cohorts.map(c => html`
                <tr>
                  <th>${c.month}</th>
                  <td class="n">${c.n}</td>
                  ${Array.from({ length: maxMonths }, (_, i) => {
                    const p = c.pct[i];
                    if (p == null) return '<td></td>';
                    const alpha = (p / 100) * 0.75 + 0.08;
                    const dark = p >= 60;
                    return `<td class="pct" style="background:rgba(217,79,99,${alpha.toFixed(2)});color:${dark ? '#fff' : '#2d313d'}">${p}%</td>`;
                  }).join('')}
                </tr>`).join('')}
            </tbody>
          </table>
        </div>`;
      mount.appendChild(card);
    }
  });
}

// ----- Strategy -----
function renderStrategy() {
  metricPage('Strategy', (mount, labels, cut) => {
    const S = DB.series;
    const add = (spec, ds) => mount.appendChild(chartCard(spec, labels, ds));
    add({ title: 'How your free patrons have grown over time' },
      [lineDs('Free patrons', cut(S.freePatrons), PINK)]);
    add({ title: 'How your supporting patrons have grown over time' },
      [lineDs('Supporting patrons', cut(S.supporting), PINK)]);
    add({ title: 'How your supporting patrons have grown over time by tier', zero: true },
      tierLines(cut, S.countA, S.countB, S.countC));
    add({ title: "The percentage of your supporting patrons' growth compared to 30 days before", suffix: '%' },
      [lineDs('Growth', cut(S.supportingGrowth30), PINK)]);
    add({ title: 'How many new patrons started supporting you', type: 'bar', zero: true },
      [barDs('New patrons', cut(S.newPatrons))]);
    add({ title: 'How many new patrons started supporting you by tier', type: 'bar', zero: true },
      [barDs(T.a.label, cut(S.newPatronsA), T.a.color),
       barDs(T.c.label, cut(S.newPatronsC), T.c.color)]);
    add({ title: 'How many patrons increased their pledged amount', type: 'bar', zero: true },
      [barDs('Upgrades', cut(S.upgrades))]);
    add({ title: 'How many patrons increased their pledged amount by tier', type: 'bar', zero: true },
      [barDs(T.a.label, cut(S.upgradesA), T.a.color),
       barDs(T.c.label, cut(S.upgradesC), T.c.color)]);
    add({ title: 'How many patrons decreased their pledged amount', type: 'bar', zero: true },
      [barDs('Downgrades', cut(S.downgrades))]);
    add({ title: 'How many patrons decreased their pledged amount by tier', type: 'bar', zero: true },
      [barDs(T.a.label, cut(S.downgradesA), T.a.color),
       barDs(T.c.label, cut(S.downgradesC), T.c.color)]);
  });
}

// ----- Patrons -----
function renderPatrons() {
  destroyCharts();
  app.innerHTML = html`
    <div class="page">
      <div class="page-head"><h1>Active patrons</h1></div>
      <div class="card">
        <h2 style="text-align:center;font-size:17px;font-weight:800;">
          <span style="color:${PINK}">#</span> What other pages your patrons are currently pledging (top 30)
        </h2>
        <p class="note" style="margin-top:10px;">Please note that this is only showing pages that are using Creator Pulse.<br>
          Do you know other Patreon creators? <strong>Tell them about Creator Pulse, and you'll benefit from it!</strong></p>
        <div class="pages-grid">
          ${(DB.peerPages || []).map(p => html`
            <div class="peer">
              ${p.nsfw ? '<span class="nsfw">NSFW</span>' : ''}<a href="#">${p.name}</a>
              <div class="count">${p.patrons} patron${p.patrons === 1 ? '' : 's'}</div>
            </div>`).join('')}
        </div>
      </div>
      <div id="charts"></div>
      <p class="last-synced">Last synced: ${DB.overview.lastSynced}</p>
    </div>`;

  const mount = $('#charts');
  const add = (title, src, horizontal) => {
    if (!src || !src.labels) return;
    const spec = { title, type: 'bar', zero: true, rawX: true, xTicks: 31 };
    const card = chartCard(spec, src.labels, [barDs('Patrons', src.data)],
      horizontal ? { chartOpts: { indexAxis: 'y' } } : {});
    mount.appendChild(card);
  };
  add('The currencies associated with your current patrons',
    { labels: (DB.currencies || []).map(c => c[0]), data: (DB.currencies || []).map(c => c[1]) }, true);
  add('The years when your current patrons started supporting you', DB.startYears);
  add('The months when your current patrons started supporting you', DB.startMonths);
  add('The days of the month when your current patrons started supporting you', DB.startDaysOfMonth);
  add('The days of the week when your current patrons started supporting you', DB.startWeekdays);
  add('The UTC hours of the day when your current patrons started supporting you', DB.startHours);
}

// ----- Emails -----
function renderEmails() {
  destroyCharts();
  const E = DB.emails || {};
  // Task 14 — honesty pass: live (synced) accounts have no real mailer integration and
  // Patreon's API exposes no email-campaign stats, so show a clear notice instead of the
  // seeded demo drip numbers sitting next to real analytics.
  if (DB.live && (E.hidden || !Array.isArray(E.drips))) {
    app.innerHTML = html`
      <div class="page">
        <div class="page-head"><h1>Emails</h1></div>
        <div class="card"><p class="note" style="text-align:left">
          Automated patron emails aren't connected for <strong>${DB.overview.creator}</strong> yet.
          Patreon's API doesn't expose email-campaign stats, so this section stays empty for live
          accounts rather than show demo numbers next to your real analytics. It will light up once
          a mailer integration is added.
        </p></div>
      </div>`;
    return;
  }
  // per-account enable/disable state
  const dripKey = 'cp-drips-' + DB.accountId;
  const saved = JSON.parse(localStorage.getItem(dripKey) || '{}');
  E.drips.forEach(d => { if (d.id in saved) d.enabled = saved[d.id]; });

  app.innerHTML = html`
    <div class="page">
      <div class="page-head"><h1>Emails</h1></div>
      <div class="email-top">
        <div class="card"><p>${E.planNote}</p><p style="margin-top:10px;">${E.planDetail}</p></div>
        <div class="card usage"><h3>Current month usage</h3><p>${E.currentMonth} emails</p></div>
        <div class="card usage"><h3>Last month usage</h3><p>${E.lastMonth} emails</p></div>
      </div>
      <div class="card" id="drips"></div>
    </div>`;

  const wrap = $('#drips');
  wrap.innerHTML = E.drips.map(d => html`
    <div class="drip-row" data-id="${d.id}">
      <div class="drip-head">
        <h3>${d.title}</h3>
        <button data-toggle>${d.enabled ? 'Edit' : 'Enable'}</button>
      </div>
      <div class="drip-status">
        ${d.enabled
          ? `Enabled${d.tiers ? ` on <u>${d.tiers} tier${d.tiers === 1 ? '' : 's'}</u>` : ''}` +
            (d.sent != null ? ` <span class="muted">( Sent: <strong>${d.sent}</strong> - Click: <strong>${d.clicks}</strong> - Unique click: <strong>${d.uniqueClicks}</strong> )</span>` : '')
          : 'Disabled'}
      </div>
      ${d.enabled && d.sent != null ? '<a class="drip-link" href="#">See deliveries</a>' : ''}
    </div>`).join('');

  wrap.querySelectorAll('[data-toggle]').forEach(btn =>
    btn.addEventListener('click', () => {
      const id = btn.closest('.drip-row').dataset.id;
      const drip = E.drips.find(d => d.id === id);
      drip.enabled = !drip.enabled;
      localStorage.setItem(dripKey, JSON.stringify(Object.fromEntries(E.drips.map(d => [d.id, d.enabled]))));
      renderEmails();
    }));
}

// ----- Account (manage + hook up accounts) -----
function renderAccount() {
  destroyCharts();
  const accounts = listAccounts();
  app.innerHTML = html`
    <div class="page">
      <div class="page-head"><h1>Accounts</h1></div>

      <div class="card">
        <h2 style="font-size:17px;font-weight:900;margin-bottom:6px;">Current account</h2>
        <p style="font-size:14.5px;">
          <strong>${DB.overview.creator}</strong> —
          ${DB.live
            ? '<span class="badge badge-live">Live data</span> synced from <code>data/' + DB.accountId + '.json</code>'
            : '<span class="badge badge-demo">Demo data</span> seeded locally; hook up the real Patreon account below to go live'}
        </p>
      </div>

      <div class="card">
        <h2 style="font-size:17px;font-weight:900;margin-bottom:14px;">Your accounts</h2>
        <div id="acct-list"></div>
      </div>

      <div class="card">
        <h2 style="font-size:17px;font-weight:900;margin-bottom:10px;">Add an account</h2>
        <div class="add-acct">
          <input id="acc-name" type="text" placeholder="Patreon page name (e.g. My New Comic)" maxlength="60">
          <button class="btn btn-pink" id="acc-add">Add account</button>
        </div>
        <p class="note" style="text-align:left;margin-top:10px;">
          New accounts start with seeded demo data so every page works immediately.
          To show its real numbers, hook it up below.
        </p>
      </div>

      <div class="card">
        <h2 style="font-size:17px;font-weight:900;margin-bottom:10px;">Hook up real Patreon data</h2>
        <ol class="hookup">
          <li>Get a <strong>Creator Access Token</strong> for each Patreon page: log into that page's creator account and visit
            <code>patreon.com/portal/registration/register-clients</code> → create a client → copy the Creator's Access Token.</li>
          <li>Copy <code>accounts.config.example.json</code> to <code>accounts.config.json</code> (kept local, never served)
            and paste each account's id + token.</li>
          <li>Run <code>python3 tools/sync_patreon.py</code>. It writes <code>data/&lt;account-id&gt;.json</code>,
            which this app automatically prefers over demo data. Run it daily (cron) to accumulate history.</li>
        </ol>
        <p class="note" style="text-align:left;">Account ids must match the ones in the list above (e.g. <code>growgetter</code>).</p>
      </div>
    </div>`;

  const list = $('#acct-list');
  list.innerHTML = accounts.map(a => html`
    <div class="acct-row" data-id="${a.id}">
      <div class="acct-avatar small">${(a.profile && a.profile.initials) || a.initials || a.name.slice(0, 2).toUpperCase()}</div>
      <div class="acct-info">
        <strong>${a.name}</strong>
        <span class="muted">id: ${a.id}${a.custom ? ' · custom' : ''}</span>
      </div>
      ${a.id === DB.accountId
        ? '<span class="badge badge-live">current</span>'
        : `<button class="btn" data-switch="${a.id}">Switch</button>`}
      ${a.custom ? `<button class="btn btn-danger" data-remove="${a.id}">Remove</button>` : ''}
    </div>`).join('');

  list.querySelectorAll('[data-switch]').forEach(b =>
    b.addEventListener('click', () => switchAccount(b.dataset.switch)));

  list.querySelectorAll('[data-remove]').forEach(b =>
    b.addEventListener('click', () => {
      const id = b.dataset.remove;
      if (!confirm('Remove account "' + id + '" from Creator Pulse? (Does not touch Patreon.)')) return;
      saveCustomAccounts(customAccounts().filter(a => a.id !== id));
      if (DB.accountId === id) switchAccount('bloom'); else { renderSwitcher(); renderAccount(); }
    }));

  $('#acc-add').addEventListener('click', () => {
    const name = $('#acc-name').value.trim();
    if (!name) return;
    let id = name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'account';
    const taken = new Set(listAccounts().map(a => a.id));
    let n = 2, base = id;
    while (taken.has(id)) id = base + '-' + n++;
    const initials = name.split(/\s+/).map(w => w[0]).join('').slice(0, 2).toUpperCase();
    saveCustomAccounts([...customAccounts(), { id, name, initials }]);
    switchAccount(id);
  });
}

function renderStub(title, note) {
  destroyCharts();
  app.innerHTML = html`
    <div class="page">
      <div class="page-head"><h1>${title}</h1></div>
      <div class="card"><p class="note">${note}</p></div>
    </div>`;
}

// ----- Rollup (all accounts) — Task 8 -----
const ROLLUP_COLORS = ['#d94f63', '#2e6fd8', '#1D9E75', '#EF9F27', '#7A7FEC', '#b7392b'];
async function renderRollup() {
  destroyCharts();
  app.innerHTML = html`
    <div class="page">
      <div class="page-head"><h1>All accounts</h1></div>
      <div id="rollup"><p class="note">Loading account data…</p></div>
    </div>`;
  const ids = BUILTIN_ACCOUNTS.map(a => a.id);
  const loaded = await Promise.all(ids.map(async (id) => {
    try {
      const r = await fetch('data.php?acct=' + encodeURIComponent(id), { cache: 'no-store' });
      if (r.ok) { const d = await r.json(); d._id = id; return d; }
    } catch (e) { /* not live — skip */ }
    return null;
  }));
  const live = loaded.filter(Boolean);
  const mount = $('#rollup');
  if (!live.length) {
    mount.innerHTML = '<div class="card"><p class="note">No live account data yet. Add Patreon tokens and run the sync to populate this view.</p></div>';
    return;
  }
  const st = d => d.overview.stats;
  const totMRR = live.reduce((s, d) => s + (st(d).earningsPerMonth || 0), 0);
  const totPat = live.reduce((s, d) => s + (st(d).patrons || 0), 0);
  const blendChurn = totPat ? live.reduce((s, d) => s + (st(d).churnPct || 0) * (st(d).patrons || 0), 0) / totPat : 0;
  const avgPledge = totPat ? totMRR / totPat : 0;

  mount.innerHTML = html`
    <div class="stat-grid" style="margin-bottom:18px">
      <div class="stat-card"><div class="value">${money(totMRR)}</div><div class="desc">Total estimated MRR · ${live.length} account${live.length === 1 ? '' : 's'}</div></div>
      <div class="stat-card"><div class="value">${totPat.toLocaleString()}</div><div class="desc">Total paying patrons</div></div>
      <div class="stat-card"><div class="value">${blendChurn.toFixed(1)}%</div><div class="desc">Blended churn (patron-weighted)</div></div>
      <div class="stat-card"><div class="value">${money(avgPledge)}</div><div class="desc">Blended average pledge</div></div>
    </div>
    <div class="card">
      <h2 style="font-size:16px;font-weight:800;margin-bottom:12px"><span class="hash" style="color:${PINK}">#</span> Accounts compared</h2>
      <div class="cohort-scroll">
        <table class="cohort">
          <thead><tr><th style="text-align:left">Account</th><th>Patrons</th><th>MRR</th><th>Avg pledge</th><th>Churn</th><th>Retention</th></tr></thead>
          <tbody>
            ${live.map(d => html`
              <tr>
                <th style="text-align:left"><a href="#/dashboard?acct=${d._id}" style="color:inherit">${d.overview.creator}</a></th>
                <td class="n">${st(d).patrons}</td>
                <td class="n">${money(st(d).earningsPerMonth)}</td>
                <td class="n">${money(st(d).avgPledge)}</td>
                <td class="n">${st(d).churnPct}%</td>
                <td class="n">${st(d).retentionMonths} mo</td>
              </tr>`).join('')}
            <tr style="font-weight:800;border-top:2px solid #d9dce3">
              <th style="text-align:left">Total</th>
              <td class="n">${totPat}</td>
              <td class="n">${money(totMRR)}</td>
              <td class="n">${money(avgPledge)}</td>
              <td class="n">${blendChurn.toFixed(1)}%</td>
              <td class="n">—</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    <div class="card" style="margin-top:16px">
      <h2 style="font-size:16px;font-weight:800;margin-bottom:12px"><span class="hash" style="color:${PINK}">#</span> Supporting patrons over time</h2>
      <div class="chart-wrap" style="height:320px"><canvas id="rollup-canvas"></canvas></div>
    </div>`;

  const allDates = [...new Set(live.flatMap(d => d.dates))].sort();
  const datasets = live.map((d, i) => {
    const map = {};
    d.dates.forEach((dt, j) => { map[dt] = d.series.supporting[j]; });
    const color = ROLLUP_COLORS[i % ROLLUP_COLORS.length];
    return {
      label: d.overview.creator, data: allDates.map(dt => (dt in map ? map[dt] : null)),
      borderColor: color, backgroundColor: color, borderWidth: 2,
      pointRadius: allDates.length < 4 ? 3 : 0, tension: 0.25, spanGaps: true
    };
  });
  liveCharts.push(new Chart($('#rollup-canvas'), {
    type: 'line',
    data: { labels: allDates, datasets },
    options: {
      responsive: true, maintainAspectRatio: false, animation: false,
      interaction: { mode: 'index', intersect: false },
      plugins: { legend: { position: 'top', labels: { boxWidth: 22, font: { size: 11 } } } },
      scales: {
        x: { grid: { display: false }, ticks: { maxTicksLimit: 10, maxRotation: 0, font: { size: 11 }, callback(v) { return fmtAxisDate(this.getLabelForValue(v)); } } },
        y: { beginAtZero: false, border: { display: false }, grid: { color: '#eef0f4' }, ticks: { font: { size: 11 }, precision: 0 } }
      }
    }
  }));
}

// ---------- account switcher ----------
function renderSwitcher() {
  const mount = $('#acct-switch');
  const accounts = listAccounts();
  const cur = accounts.find(a => a.id === DB.accountId) || accounts[0];
  const initials = DB.overview ? DB.overview.initials : cur.name.slice(0, 2).toUpperCase();
  mount.innerHTML = html`
    <div class="acct-avatar">${initials}</div>
    <select id="acct-select" title="Switch account">
      ${accounts.map(a => `<option value="${a.id}" ${a.id === DB.accountId ? 'selected' : ''}>${a.name}</option>`).join('')}
      <option value="__add">+ Add account…</option>
    </select>`;
  $('#acct-select').addEventListener('change', e => {
    if (e.target.value === '__add') { location.hash = '#/account'; renderSwitcher(); return; }
    switchAccount(e.target.value);
  });
}

async function switchAccount(id) {
  localStorage.setItem('cp-account', id);
  await loadAccount(id);
  T = DB.tiers;
  renderSwitcher();
  route();
}

// ---------- router ----------
const routes = {
  dashboard: renderDashboard,
  rollup: renderRollup,
  balance: renderBalance,
  retention: renderRetention,
  strategy: renderStrategy,
  patrons: renderPatrons,
  emails: renderEmails,
  account: renderAccount,
  logout: () => renderStub('Logged out', 'This is a demo — no real session to end. <a href="#/dashboard">Back to the dashboard</a>.')
};

function route() {
  if (!DB) return; // boot() will call us once data is ready
  const name = (location.hash.replace('#/', '') || 'dashboard').split('?')[0];
  const render = routes[name] || renderDashboard;
  document.querySelectorAll('.nav-main a').forEach(a =>
    a.classList.toggle('active', a.dataset.route === name));
  render();
  window.scrollTo(0, 0);
}

// Task 15 — accept ?acct=<id> from the URL query or the hash query, so site.php can
// deep-link straight to a specific account (e.g. pulse/?acct=bloom).
function acctParam() {
  const fromSearch = new URLSearchParams(location.search).get('acct');
  if (fromSearch) return fromSearch;
  const q = location.hash.split('?')[1];
  return q ? new URLSearchParams(q).get('acct') : null;
}

async function boot() {
  const valid = new Set(listAccounts().map(a => a.id));
  const wanted = acctParam();
  const saved = (wanted && valid.has(wanted)) ? wanted : (localStorage.getItem('cp-account') || 'bloom');
  await loadAccount(saved);
  T = DB.tiers;
  renderSwitcher();
  route();
}

window.addEventListener('hashchange', route);
boot();
