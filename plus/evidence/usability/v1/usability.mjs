// Scripted usability walkthrough of the multivariate-ma page with the plus panel (allmeta PR #152 head d089222).
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
page.on('response', r => { if (r.status() >= 400) log.errors.push('HTTP ' + r.status() + ' ' + r.url()); });
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
await browser.close(); server.close();
fs.writeFileSync(path.join(out, 'walkthrough.json'), JSON.stringify(log, null, 1));
console.log('ERRORS', JSON.stringify(log.errors));
console.log('TOTAL CLICKS (load Berkey -> read -> sweep -> export R):', clicks);
