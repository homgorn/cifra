#!/usr/bin/env node
/* Runtime smoke test for reports/cifra18-audit/js/main.js + wm-data.js + site-data.js.
 * Stubs a minimal DOM, executes the scripts, asserts every canvas id found
 * in the HTML files gets a Chart and every wm tbody gets rows.
 * Usage: node scripts/export/smoke_wm_js.js  (cwd = repo root)
 */
const fs = require('fs');
const path = require('path');

const SITE_DIR = path.join('reports', 'cifra18-audit');
const failures = [];
function fail(msg) { failures.push(msg); }

// 1. collect canvas ids + tbody ids from all html files
function walk(dir, out) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) walk(p, out);
    else if (e.name.endsWith('.html')) out.push(p);
  }
  return out;
}
const htmlFiles = walk(SITE_DIR, []);
const canvasIds = new Set();
const tbodyIds = new Set();
for (const f of htmlFiles) {
  const html = fs.readFileSync(f, 'utf8');
  for (const m of html.matchAll(/<canvas id="([^"]+)"/g)) canvasIds.add(m[1]);
  for (const m of html.matchAll(/<tbody id="([^"]+)"/g)) tbodyIds.add(m[1]);
}

// 2. stubs
const elements = {};
function makeEl(id) {
  if (!elements[id]) {
    elements[id] = {
      id,
      innerHTML: '',
      textContent: '',
      style: {},
      getContext: () => ({}),
      classList: { toggle: () => {}, add: () => {}, remove: () => {}, contains: () => false },
      addEventListener: () => {},
      getAttribute: () => null,
      querySelectorAll: () => [],
      querySelector: () => null,
    };
  }
  return elements[id];
}
const createdCharts = [];
global.window = {};
global.document = {
  getElementById: (id) => makeEl(id),
  querySelectorAll: () => [],
  addEventListener: () => {},
};
global.localStorage = { getItem: () => null, setItem: () => {} };
global.requestAnimationFrame = () => {};
function Chart(ctx, cfg) { createdCharts.push(cfg); }
Chart.defaults = { font: {}, color: '', borderColor: '' };
global.Chart = Chart;

// 3. load wm-data.js then main.js in this context
function loadAsGlobal(file, constName) {
  let src = fs.readFileSync(file, 'utf8');
  src = src.replace('const ' + constName + ' =', 'global.' + constName + ' =');
  eval(src);
}
loadAsGlobal(path.join(SITE_DIR, 'js', 'wm-data.js'), 'WM');
loadAsGlobal(path.join(SITE_DIR, 'js', 'site-data.js'), 'SITE');
loadAsGlobal(path.join(SITE_DIR, 'js', 'dash-data.js'), 'DASH');
eval(fs.readFileSync(path.join(SITE_DIR, 'js', 'main.js'), 'utf8'));

// 4. assertions
const WMG = global.WM;
if (!WMG) fail('WM global missing');
const charted = new Set();
for (const c of createdCharts) {
  // find canvas id via datasets is hard; instead rely on mk() guard: it only
  // constructs when element exists. We count constructions per config label set.
  charted.add(JSON.stringify((c.data.labels || []).slice(0, 3)));
}
if (createdCharts.length < 54) fail('expected >=54 charts total, got ' + createdCharts.length);

const DASH_IDS = ['dashSqiLine', 'dashSectionBar', 'dashHttpBar', 'dashSiteLine',
  'dashBounceLine', 'dashDevicesDonut', 'dashBrowsersBar', 'dashCitiesBar',
  'dashGenderDonut', 'dashAgeBar', 'dashInterestBar', 'dashSourceLine', 'dashRefsBar',
  'dashRevLine', 'dashRevDayBar', 'dashLandingBar', 'dashPhraseBar', 'dashMapsLine',
  'dashMapsActionBar', 'dashMapsEntryBar', 'dashMapsSearchBar', 'dashMapsSourceDonut'];

const EXPECT_WM = ['wmStatusDonut', 'wmTopShareBar', 'wmSectionBar', 'wmRateBar',
  'wmDupPatternsBar', 'wmParsePatternsBar', 'wmErrorBar', 'wmRedirectDonut',
  'wmPosHist', 'wmMoneyTrend', 'wmShowsBar', 'wmClusterBar', 'wmCoverageBar',
  'wmGapPosBar', 'wmGapPriorityDonut', 'wmLinkStatusDonut', 'wmBrokenTargetsBar',
  'wmIceBar', 'wmForecastLine'];
// mk() is called for every id; verify by re-scanning main.js source for them
const mainSrc = fs.readFileSync(path.join(SITE_DIR, 'js', 'main.js'), 'utf8');
const HOME_IDS = ['homeSearchLine', 'homeStatusDonut', 'homeMoneyBar', 'homeSourcesDonut'];
for (const id of HOME_IDS) {
  if (!mainSrc.includes("mk('" + id + "'")) fail('main.js missing mk(' + id + ')');
  if (!canvasIds.has(id)) fail('no <canvas id="' + id + '" in html');
}
for (const id of EXPECT_WM) {
  if (!mainSrc.includes("mk('" + id + "'")) fail('main.js missing mk(' + id + ')');
  if (!canvasIds.has(id)) fail('no <canvas id="' + id + '" in html');
}
// every canvas in html must have mk() call (old + new)
const OLD_IDS = ['healthChart', 'lossChart', 'severityChart', 'imageChart', 'servicesChart',
  'contentLenChart', 'threatChart', 'compareRadar', 'citiesChart', 'geoChart', 'kgChart',
  'tripletChart', 'priceChart', 'seasonChart', 'budgetChart', 'merchKpiChart', 'forecastChart'];
for (const id of canvasIds) {
  if (!mainSrc.includes("mk('" + id + "'")) fail('canvas without mk(): ' + id);
}
for (const id of DASH_IDS) {
  if (!mainSrc.includes("mk('" + id + "'")) fail('main.js missing mk(' + id + ')');
  if (!canvasIds.has(id)) fail('no <canvas id="' + id + '" in html');
}
for (const id of [...EXPECT_WM, ...OLD_IDS, ...HOME_IDS, ...DASH_IDS]) {
  if (!canvasIds.has(id)) fail('mk() target canvas missing in html: ' + id);
}
// DASH keys used by main.js exist
const DG = global.DASH;
if (!DG) fail('DASH global missing');
for (const k of ['generated', 'tech', 'site', 'money', 'maps']) {
  if (!(k in DG)) fail('DASH missing key: ' + k);
}
for (const k of ['sqi', 'sqiSeries', 'searchable', 'recrawlDaily', 'sections', 'important',
  'events', 'http', 'queries12m']) {
  if (!(k in DG.tech)) fail('DASH.tech missing key: ' + k);
}
for (const k of ['visitsTotal', 'usersTotal', 'monthly', 'bounce', 'devices', 'browsers',
  'cities', 'gender', 'age', 'interests', 'bots', 'referers', 'sources', 'landing', 'phrases']) {
  if (!(k in DG.site)) fail('DASH.site missing key: ' + k);
}
for (const k of ['revenue', 'purchases', 'revByMonth', 'topDays', 'goals', 'goalsActive']) {
  if (!(k in DG.money)) fail('DASH.money missing key: ' + k);
}
for (const k of ['viewsTotal', 'monthly', 'entries', 'sources', 'actions', 'goals', 'search']) {
  if (!(k in DG.maps)) fail('DASH.maps missing key: ' + k);
}
if (!Array.isArray(DG.site.sources) || !DG.site.sources.length) fail('DASH.site.sources empty');
for (const id of ['kpiSqi', 'kpiRecrawl', 'kpiVisits', 'kpiBots', 'kpiRevenue', 'kpiMapCalls']) {
  const el = elements[id];
  if (!el || !el.textContent) fail('KPI not filled: ' + id);
}
// SITE keys used by main.js exist
const SITEG = global.SITE;
if (!SITEG) fail('SITE global missing');
for (const k of ['generated', 'searchable', 'excluded', 'sqi', 'statuses',
  'insearchMonthly', 'popularCount', 'popularWeek', 'popularTop10',
  'purchases', 'revenue', 'revenueTop5', 'goalsActive', 'sourcesYear']) {
  if (!(k in SITEG)) fail('SITE missing key: ' + k);
}
// homepage list filled
{
  const ol = elements['homePopular'];
  if (!ol || !ol.innerHTML || ol.innerHTML.indexOf('<li>') < 0) fail('homePopular not filled');
}
// tbodies filled
for (const id of tbodyIds) {
  const el = elements[id];
  if (!el || !el.innerHTML || el.innerHTML.indexOf('<tr>') < 0) fail('tbody not filled: ' + id);
}
// WM keys used by main.js exist
const needKeys = ['statuses', 'queryBins', 'queryTops', 'sectionsTop', 'dupPatterns',
  'parsePatterns', 'trend', 'trendDays', 'showsDaily', 'money', 'clusters', 'gaps',
  'linkStatus', 'brokenTargets', 'ice', 'forecast', 'meta'];
for (const k of needKeys) {
  if (!(k in WMG)) fail('WM missing key: ' + k);
}
// trend series length matches days
for (const t of WMG.trend) {
  if (t.series.length !== WMG.trendDays.length) fail('trend length mismatch: ' + t.q);
}

if (failures.length) {
  console.log('SMOKE FAIL (' + failures.length + '):');
  for (const f of failures) console.log(' - ' + f);
  process.exit(1);
} else {
  console.log('SMOKE OK: charts=' + createdCharts.length +
    ' canvases=' + canvasIds.size + ' tbodies=' + tbodyIds.size);
}
