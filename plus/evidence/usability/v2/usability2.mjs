// Scripted usability walkthrough of the multivariate-ma page with the plus panel (allmeta PR #152 head d089222).
// v2 (19 Oct, P18 finalisation): adds own-data paste, option change, JSON export, R-reference checks of what the user reads,
// a rho_w-mode 6-field probe, the URL of any failed request, and the Figure 2 capture (deviceScaleFactor 3).
// Usage: node usability.mjs <site-root containing multivariate-ma/> <outdir>   (Edge via Playwright channel msedge)
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
const require = createRequire(process.env.PW_MODULES + '/x.js');
const { chromium } = require('playwright');
const AxeBuilder = require('@axe-core/playwright').default;

const root = path.resolve(process.argv[2]), out = path.resolve(process.argv[3]);
fs.mkdirSync(out, { recursive: true });
const types = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.mjs': 'text/javascript', '.png': 'image/png', '.md': 'text/plain' };
const server = http.createServer((req, res) => {
  const p = path.join(root, decodeURIComponent(new URL(req.url, 'http://x').pathname));
  if (!p.startsWith(root) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { 'content-type': types[path.extname(p)] || 'application/octet-stream' }); fs.createReadStream(p).pipe(res);
});
await new Promise(r => server.listen(8099, '127.0.0.1', r));
const url = 'http://127.0.0.1:8099/multivariate-ma/index.html';
const log = { url, source: 'allmeta PR #152 head d089222 (feat/multivariate-ma-plus), served locally', steps: [], badInputs: [], keyboard: [], defaults: {}, axe: null, errors: [] };
const browser = await chromium.launch({ channel: 'msedge' });
log.browser = 'Microsoft Edge ' + browser.version();
const ctx = await browser.newContext({ viewport: { width: 1100, height: 900 }, acceptDownloads: true });
const page = await ctx.newPage();
page.on('pageerror', e => log.errors.push('pageerror: ' + e.message));
ctx.on('response', r => { if (r.status() >= 400) log.errors.push('HTTP ' + r.status() + ' ' + r.url()); });
ctx.on('requestfailed', r => log.errors.push('requestfailed ' + r.url()));
page.on('console', m => { if (m.type() === 'error' && !/frame-ancestors/.test(m.text())) log.errors.push('console: ' + m.text()); });
let clicks = 0;
const shot = async (name, locator) => { const f = path.join(out, name + '.png'); if (locator) await locator.screenshot({ path: f, scale: 'css' }); else await page.screenshot({ path: f, scale: 'css' }); return path.basename(f); };
const step = (s) => { log.steps.push({ clicksSoFar: clicks, ...s }); console.log('STEP', clicks, s.action, '|', s.observed); };
const settle = () => page.waitForFunction(() => window._almLastMultivariate && window._almLastMultivariate() && window.AlmMvPlusUI);

// 1. fresh load
await page.goto(url); await settle();
const head = await page.locator('#headline').textContent();
const o = await page.evaluate(() => window._almLastMultivariate());
log.defaults = { mode: await page.locator('#f-mode').inputValue(), outcome1: await page.locator('#f-o1').inputValue(), outcome2: await page.locator('#f-o2').inputValue(),
  rhoW: await page.locator('#f-rhow').inputValue(), sweepFrom: await page.locator('#plus-from').inputValue(), sweepTo: await page.locator('#plus-to').inputValue(), sweepStep: await page.locator('#plus-step').inputValue(),
  dataFirstLine: (await page.locator('#f-data').inputValue()).split('\n')[0] };
step({ action: 'fresh load (no click)', observed: head.trim(), screenshot: await shot('01_fresh_load') });
// 2. load Berkey example explicitly (1 click)
await page.locator('#btn-ex-berkey').click(); clicks++; await settle();
const o2 = await page.evaluate(() => window._almLastMultivariate());
const statsText = (await page.locator('#stats').innerText()).replace(/\s+/g, ' ').trim();
step({ action: 'click "Berkey example"', observed: (await page.locator('#headline').textContent()).trim(), pooled: { PD: o2.mu[0], AL: o2.mu[1], seP: o2.muSE[0], seA: o2.muSE[1], rho: o2.rho, logLik: o2.logLik }, stats: statsText, screenshot: await shot('02_berkey_core_output') });
log.coreOutputClicks = { fromFreshLoad: 0, viaExplicitExampleButton: clicks, sameAsDefault: JSON.stringify(o.mu) === JSON.stringify(o2.mu) };
// 3. read the univariate-vs-multivariate table
const cmp = (await page.locator('#plus-cmp-body').innerText()).replace(/\t/g, ' | ');
step({ action: 'read comparison table (no click)', observed: cmp.split('\n').length + ' rows', table: cmp, screenshot: await shot('03_uv_mv_table', page.locator('#plus-cmp-body').locator('xpath=ancestor::table[1]')) });
// 4. run the rho_w sweep (1 click)
await page.locator('#plus-run').click(); clicks++;
await page.waitForFunction(() => /19 of 19/.test(document.getElementById('plus-status').textContent));
step({ action: 'click "Run sweep"', observed: (await page.locator('#plus-status').textContent()).trim(), rows: await page.locator('#plus-sweep-body tr').count(), screenshot: await shot('04_sweep', page.locator('#plus-sweep-plot')) });
// 5. export R script (1 click)
const [dl] = await Promise.all([page.waitForEvent('download'), page.locator('#plus-dl-r').click()]); clicks++;
const rtext = fs.readFileSync(await dl.path(), 'utf8');
fs.writeFileSync(path.join(out, 'exported_' + dl.suggestedFilename()), rtext);
step({ action: 'click "Download R script"', observed: dl.suggestedFilename() + ' (' + rtext.length + ' bytes; contains mvmeta: ' + /mvmeta\(Y ~ 1/.test(rtext) + ', rma.mv: ' + /rma\.mv\(/.test(rtext) + ', machine path: ' + /[A-Z]:\\|\/Users\/|\/home\//.test(rtext) + ')' });
log.totalClicks = clicks;
// ---- v2: own data paste -> option change -> read core output -> export JSON, checked against the archived R reference ----
const REF = JSON.parse(fs.readFileSync(path.join(root, 'multivariate-ma/validate/plus/reference.json'), 'utf8'));
const refHyp = REF.configurations.find(c => c.id === 'mvmeta::hyp::sbp+dbp::REML::supplied');
const relErr = (a, b) => Math.abs(a - b) / Math.max(1, Math.abs(b));
log.checks = []; const chk = (name, a, b, tol) => { const e = relErr(a, b); const ok = e <= tol; log.checks.push({ name, page: a, R: b, relErr: e, tol, ok }); console.log('CHECK', ok ? 'PASS' : 'FAIL', name, a, b, e); return ok; };
const hypText = await page.evaluate(() => String(window.AlmMvPage.EXAMPLE_HYP));
await page.locator('#btn-clear').click(); clicks++;
await page.locator('#f-mode').selectOption('r');
await page.locator('#f-data').fill(hypText);
await page.locator('#f-o1').fill('SBP'); await page.locator('#f-o2').fill('DBP');
await page.waitForTimeout(800); await settle();
const oh = await page.evaluate(() => window._almLastMultivariate());
for (let j = 0; j < 2; j++) { chk('hyp pasted mu' + j, oh.mu[j], refHyp.supplied.mu[j], 1e-6); chk('hyp pasted muSE' + j, oh.muSE[j], refHyp.supplied.muSE[j], 1e-6); }
chk('hyp pasted rho', oh.rho, refHyp.supplied.rho, 1e-6); chk('hyp pasted logLik', oh.logLik, refHyp.supplied.logLik, 1e-6);
step({ action: 'click "Clear", select "Per-study correlation", paste 10 hyp rows (typed input, no click), type outcome names', observed: (await page.locator('#headline').textContent()).trim(),
  omitted: (await page.locator('#omitted').textContent()).trim(), stats: (await page.locator('#stats').innerText()).replace(/\s+/g, ' ').trim(), screenshot: await shot('06_own_data_hyp') });
await page.locator('#plus-from').fill('-0.5'); await page.locator('#plus-to').fill('0.5'); await page.locator('#plus-step').fill('0.25');
await page.locator('#plus-run').click(); clicks++;
await page.waitForFunction(() => /5 of 5/.test(document.getElementById('plus-status').textContent));
const sw = await page.evaluate(() => { const st = window.AlmMvPlusUI.state(); return st && st.sweep ? JSON.parse(JSON.stringify(st.sweep)) : null; });
const sweepText = (await page.locator('#plus-sweep-body').innerText());
let swOk = 0, swN = 0;
if (sw) for (const s of sw) { const rr = refHyp.sweep.find(x => Math.abs(x.rhoW - s.rhoW) < 1e-12); if (!rr || s.status !== 'ok') continue; const mu = s.fit ? s.fit.mu : s.mu; for (let j = 0; j < 2; j++) { swN++; if (chk('hyp sweep rhoW=' + s.rhoW + ' mu' + j, mu[j], rr.mu[j], 1e-6)) swOk++; } }
step({ action: 'change sweep grid to -0.5..0.5 step 0.25 (typed), click "Run sweep"', observed: (await page.locator('#plus-status').textContent()).trim(), sweepAccessor: sw ? 'present' : 'absent', sweepChecks: swOk + '/' + swN, table: sweepText, screenshot: await shot('07_hyp_sweep', page.locator('#plus-sweep-plot')) });
const [jd] = await Promise.all([page.waitForEvent('download'), page.locator('#plus-dl-json').click()]); clicks++;
const jtext = fs.readFileSync(await jd.path(), 'utf8'); fs.writeFileSync(path.join(out, 'exported_' + jd.suggestedFilename()), jtext);
step({ action: 'click "Download results (JSON)"', observed: jd.suggestedFilename() + ' (' + jtext.length + ' bytes; contains -9.50: ' + /-9\.50/.test(jtext) + ')' });
log.totalClicksIncludingOwnData = clicks;
// rho_w mode with the 6-field per-study-r rows still in the box: does the page refuse or reinterpret?
await page.locator('#f-mode').selectOption('rhoW'); await page.waitForTimeout(800);
log.rhoWModeWithSixFields = { headline: (await page.locator('#headline').textContent()).trim(), omitted: (await page.locator('#omitted').textContent()).trim(),
  firstRows: await page.evaluate(() => { const c = window.AlmMvPage.current(); return c && c.parsed ? c.parsed.rows.slice(0, 2).map(r => ({ label: r.label, y: r.y, v: r.v })) : null; }), screenshot: await shot('08_rhoW_mode_six_fields') };
console.log('RHOW6', JSON.stringify(log.rhoWModeWithSixFields));


// Bad inputs
async function bad(name, mode, text, extra) {
  await page.locator('#btn-clear').click(); await page.locator('#f-mode').selectOption(mode);
  if (extra) await extra();
  await page.locator('#f-data').fill(text);
  await page.waitForTimeout(600);
  const r = { input: name, mode, text, headline: (await page.locator('#headline').textContent()).trim(),
    omitted: (await page.locator('#omitted').textContent().catch(() => '')).trim(), statsShown: await page.locator('#stats .stat').count(),
    resultObject: await page.evaluate(() => window._almLastMultivariate() === null ? 'null (cleared)' : 'present'),
    flaggedRows: await page.locator('#derived-body tr[data-flag]').count() };
  r.screenshot = await shot('05_bad_' + name, page.locator('#headline').locator('xpath=..'));
  log.badInputs.push(r); console.log('BAD', name, '|', r.headline, '|', r.omitted);
}
await bad('malformed_number', 'cov', 'a, .1oops, .2, .3, .4, .1\nb, .5, .3, .6, .5, .1\nc, .2, .2, .2, .2, .05\nd, .3, .2, .1, .3, .05');
await bad('r_ge_1', 'r', 'a, .1, .2, .3, .4, 1.0\nb, .5, .3, .6, .5, .2\nc, .2, .2, .2, .2, .1');
await bad('non_pd_covariance', 'cov', 'a, .1, .2, .3, .4, 1\nb, .5, .3, .6, .5, .1\nc, .2, .2, .2, .2, 0');

// Keyboard-only path on a fresh page
const kp = await ctx.newPage(); await kp.goto(url);
await kp.waitForFunction(() => window._almLastMultivariate && window._almLastMultivariate() && window.AlmMvPlusUI);
const order = [];
for (let i = 0; i < 80; i++) {
  await kp.keyboard.press('Tab');
  const id = await kp.evaluate(() => { const a = document.activeElement; return a ? (a.id || a.tagName.toLowerCase() + (a.textContent ? ':' + a.textContent.trim().slice(0, 20) : '')) : null; });
  order.push(id);
  if (id === 'plus-run') break;
}
const tabsToRun = order.length;
await kp.keyboard.press('Enter');
await kp.waitForFunction(() => /19 of 19/.test(document.getElementById('plus-status').textContent), null, { timeout: 30000 });
const focusVisible = await kp.evaluate(() => { const a = document.activeElement, s = getComputedStyle(a); return { id: a.id, outline: s.outlineStyle + ' ' + s.outlineWidth, boxShadow: s.boxShadow }; });
log.keyboard.push({ path: 'Tab from page start to "Run sweep", then Enter', tabsToRunSweep: tabsToRun, focusOrder: order, sweepStatus: (await kp.locator('#plus-status').textContent()).trim(), focusStyleOnRun: focusVisible });
let tabsToR = 0;
for (let i = 0; i < 40; i++) { await kp.keyboard.press('Tab'); tabsToR++; if (await kp.evaluate(() => document.activeElement && document.activeElement.id) === 'plus-dl-r') break; }
const [kdl] = await Promise.all([kp.waitForEvent('download'), kp.keyboard.press('Enter')]);
log.keyboard.push({ path: 'Tab onward to "Download R script", then Enter', tabsFromRunSweep: tabsToR, download: kdl.suggestedFilename() });
console.log('KEYBOARD', tabsToRun, 'tabs to Run sweep;', tabsToR, 'more to R download ->', kdl.suggestedFilename());

// axe on the fresh page with the sweep shown
const ap = await ctx.newPage(); await ap.goto(url);
await ap.waitForFunction(() => window._almLastMultivariate && window._almLastMultivariate() && window.AlmMvPlusUI);
await ap.locator('#plus-run').click(); await ap.waitForFunction(() => /19 of 19/.test(document.getElementById('plus-status').textContent));
const ax = await new AxeBuilder({ page: ap }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']).analyze();
log.axe = { tags: 'wcag2a, wcag2aa, wcag21a, wcag21aa', axeVersion: ax.testEngine && ax.testEngine.version, violations: ax.violations.map(v => ({ id: v.id, impact: v.impact, nodes: v.nodes.length })), passes: ax.passes.length, incomplete: ax.incomplete.map(v => v.id) };
console.log('AXE violations', ax.violations.length, 'passes', ax.passes.length, 'incomplete', JSON.stringify(log.axe.incomplete));

// ---- Figure 2 capture: default page (berkey98), deviceScaleFactor 3 ----
{
  const fctx = await browser.newContext({ viewport: { width: 1100, height: 900 }, deviceScaleFactor: 3 });
  const fp = await fctx.newPage(); await fp.goto(url);
  await fp.waitForFunction(() => window._almLastMultivariate && window._almLastMultivariate() && window.AlmMvPlusUI);
  await fp.addStyleTag({ content: '#hub-back{display:none !important}' });
  const tbl = fp.locator('#plus-cmp-body').locator('xpath=ancestor::table[1]');
  await tbl.screenshot({ path: path.join(out, 'fig2_A_uv_mv_berkey98.png') });
  await fp.locator('#plus-run').click();
  await fp.waitForFunction(() => /19 of 19/.test(document.getElementById('plus-status').textContent));
  await fp.locator('#plus-sweep-plot').screenshot({ path: path.join(out, 'fig2_B_sweep_berkey98.png') });
  log.figure2 = { browser: log.browser, deviceScaleFactor: 3, data: 'default page data (mvmeta berkey98, 5 trials)', hidden: '#hub-back',
    tableText: (await fp.locator('#plus-cmp-body').innerText()).replace(/\t/g, ' | '), sweepStatus: (await fp.locator('#plus-status').textContent()).trim(),
    sweepTable: await fp.locator('#plus-sweep-body').innerText(), headline: (await fp.locator('#headline').textContent()).trim(),
    accessor: await fp.evaluate(() => { const o = window._almLastMultivariate(); return { mu: o.mu, muSE: o.muSE, rho: o.rho, logLik: o.logLik, plusKeys: o.plus ? Object.keys(o.plus) : null }; }) };
  await fctx.close();
}
await browser.close(); server.close();
fs.writeFileSync(path.join(out, 'walkthrough.json'), JSON.stringify(log, null, 1));
console.log('ERRORS', JSON.stringify(log.errors));
console.log('TOTAL CLICKS (load Berkey -> read -> sweep -> export R):', log.totalClicks, '; incl. own data -> option -> JSON:', clicks);
console.log('REFERENCE CHECKS', log.checks.filter(c => c.ok).length + '/' + log.checks.length);
