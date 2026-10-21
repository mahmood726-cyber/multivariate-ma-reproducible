// Capture the plus-panel page outputs for the archive (analysis/dump_plus_app.cjs).
// Runs the page exactly as validate/run-plus-node.cjs of the source commit does (every shipped page script in one
// Node VM context with linkedom; alm-validate.js and a11y-landmarks.js are browser widgets and skipped), drives
// the pinned contract replay (AlmMvPlusContract.replay with the displayed-string audit) and records, for every
// configuration, the page's own outputs that the contract compares: the supplied-covariance fit, the 19-point
// rho_w sweep, the two univariate fits, the variance ratios, the displayed strings, and p(z) on the reference grid.
// Usage: node dump_plus_app.cjs <app-root containing multivariate-ma/> <out.json>     (needs the npm package linkedom)
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm'), crypto = require('crypto');
const { parseHTML } = require('linkedom');
const root = path.resolve(process.argv[2]), outFile = process.argv[3];
const app = path.join(root, 'multivariate-ma');
const { window, document } = parseHTML(fs.readFileSync(path.join(app, 'index.html'), 'utf8'));
window.matchMedia = () => ({ matches: false });
const ctx = vm.createContext({ window, document, console, matchMedia: window.matchMedia, setTimeout, clearTimeout, URL, Blob: function () {}, navigator: {}, performance: { now: () => Date.now() } });
window.setTimeout = setTimeout; window.clearTimeout = clearTimeout;
const executed = [];
for (const s of document.querySelectorAll('script')) {
  const src = s.getAttribute('src');
  if (src && /alm-validate\.js$|a11y-landmarks\.js$/.test(src)) { executed.push(src + ' (skipped: browser widget)'); continue; }
  vm.runInContext(src ? fs.readFileSync(path.join(app, src), 'utf8') : s.textContent, ctx, { filename: src || 'index.html:inline' });
  executed.push(src || 'inline');
}
const manifest = window.AlmMvPlusManifest, loaded = {}, pins = [];
for (const f of manifest.files) {
  const bytes = fs.readFileSync(path.join(app, f.path)), sha = crypto.createHash('sha256').update(bytes).digest('hex');
  if (sha !== f.sha256 || bytes.length !== f.bytes) throw new Error('SHA-256/size mismatch: ' + f.path);
  loaded[f.path] = JSON.parse(bytes.toString('utf8')); pins.push({ path: f.path, sha256: sha });
}
const corpus = loaded[manifest.files[0].path], ref = loaded[manifest.files[1].path];
const num = x => (typeof x === 'number' && Number.isFinite(x)) ? x : null;
const arr = a => Array.isArray(a) ? a.map(x => Array.isArray(x) ? arr(x) : num(x)) : null;
const fitOut = f => f ? { k: f.k, logLik: num(f.logLik), mu: arr(f.mu), muSE: arr(f.muSE), G: arr(f.G), muVcov: arr(f.muVcov),
  rho: f.rho === null ? null : num(f.rho), rhoIsNull: f.rho === null, boundary: (f.optimizer && f.optimizer.boundary) || null } : null;
const testsOut = t => Array.isArray(t) ? t.map(x => ({ z: num(x.z), p: num(x.p) })) : null;
const one = (status, reason, fit, tests, boundary) => ({ status, reason: reason === undefined ? null : reason,
  fit: status === 'ok' ? fitOut(fit) : null, tests: status === 'ok' ? testsOut(tests) : null, boundary: boundary || null });
const P = window.AlmMvPlus, configs = []; let cur = null;
const recorder = {
  compute(parsed) {
    const res = P.compute(parsed);
    cur = { supplied: one(res.status, res.reason, res.fit, res.tests),
      univariate: res.univariate ? res.univariate.map(u => ({ status: u.status, k: u.k === undefined ? null : u.k, mu: num(u.mu), se: num(u.se), tau2: num(u.tau2), logLik: num(u.logLik), z: num(u.z), p: num(u.p) })) : null,
      varRatio: res.varRatio ? res.varRatio.map(x => x === null ? null : num(x)) : null, sweep: null, display: null };
    configs.push(cur); return res;
  },
  sweep(parsed, grid) { const sw = P.sweep(parsed, grid); cur.sweep = sw.map(s => one(s.status, s.reason, s.fit, s.tests, s.boundary)); return sw; },
};
const display = (c, r, parsed, res, sw) => { const d = window.AlmMvPlusDisplay(c, r, parsed, res, sw); cur.display = d.map(x => ({ key: x.key, shown: x.shown, expected: x.expected })); return d; };
const r = window.AlmMvPlusContract.replay(corpus, ref, recorder, { display });
if (configs.length !== corpus.configurations.length) throw new Error('configuration capture count');
configs.forEach((c, i) => { c.id = corpus.configurations[i].id; });
const pnorm = ref.pnormGrid.map(x => ({ z: x.z, p: num(window.AlmMultivariate.zTest(x.z, 1).p) }));
const doc = { schema: 'multivariate-ma-plus-app-outputs-v1', node: process.version, linkedom: require('linkedom/package.json').version, executed, pins,
  contractReplay: { checks: r.checks, passed: r.passed, failedChecks: r.failedChecks, adjudicated: r.adjudicated.map(a => a.id) },
  configurations: configs, pnorm };
fs.writeFileSync(outFile, JSON.stringify(doc) + '\n');
console.log('PLUS APP OUTPUTS', configs.length, 'configurations; contract replay', r.passed + '/' + r.checks, '; adjudicated', r.adjudicated.length);
process.exit(r.failedChecks ? 1 : 0);
