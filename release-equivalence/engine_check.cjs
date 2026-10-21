// Supplementary engine-only check: fit each archived accepted-study set with a given shared/multivariate-ma.js
// and compare with reference.json using compare.py's numeric rules. Not a page capture.
// Usage: node engine_check.cjs <engine.js> <archived app-patched.json> <reference.json> <corpus.json>
'use strict';
const fs = require('fs'), vm = require('vm');
const [engine, appf, reff, corpf] = process.argv.slice(2);
const ctx = vm.createContext({ window: {}, console }); ctx.window.window = ctx.window;
vm.runInContext(fs.readFileSync(engine, 'utf8'), ctx, { filename: engine });
const MV = ctx.window.AlmMultivariate;
const app = Object.fromEntries(JSON.parse(fs.readFileSync(appf, 'utf8')).map(a => [a.id, a]));
const refs = JSON.parse(fs.readFileSync(reff, 'utf8')), corpus = JSON.parse(fs.readFileSync(corpf, 'utf8'));
let checks = 0, passed = 0; const byQ = {}, fails = [];
const rec = (id, q, ok, a, b, e) => { checks++; byQ[q] = byQ[q] || [0, 0]; byQ[q][0]++; if (ok) { passed++; byQ[q][1]++; } else fails.push({ id, q, a, b, e }); };
const chk = (id, q, a, b, tol) => {
  if (Array.isArray(b)) return b.forEach((x, i) => chk(id, q, Array.isArray(a) ? a[i] : undefined, x, tol));
  if (b === null) return rec(id, q + '_undefined', a === null || a === undefined, a, b, null);
  const e = (typeof a === 'number' && isFinite(a)) ? Math.abs(a - b) / Math.max(1, Math.abs(b)) : Infinity;
  rec(id, q, e <= tol, a, b, e);
};
corpus.forEach((c, i) => {
  const r = refs[i]; if (r.status !== 'ok') return;
  const studies = app[c.id].capture.studies;
  let f = null; try { f = MV.fit(studies); } catch (e) { rec(c.id, 'fit_error', false, e.message); return; }
  const tol = (r.adjudication || '').startsWith('two-study exact') ? 1e-9 : 1e-6;
  for (const q of ['mu', 'muSE', 'muVcov', 'G', 'rho', 'logLik']) chk(c.id, q, f[q], r[q], tol);
  for (const q of ['k', 'm']) chk(c.id, q, f[q], r[q], 0);
  for (let j = 0; j < 2; j++) {
    chk(c.id, 'ciLower', f.mu[j] - 1.959963984540054 * f.muSE[j], r.ciLower[j], tol);
    chk(c.id, 'ciUpper', f.mu[j] + 1.959963984540054 * f.muSE[j], r.ciUpper[j], tol);
    chk(c.id, 'sd', f.G[j][j] >= 0 ? Math.sqrt(f.G[j][j]) : null, r.sd[j], tol);
  }
});
console.log('ENGINE', engine, passed + '/' + checks, 'numeric checks pass');
console.log('by quantity', JSON.stringify(byQ));
fails.forEach(x => console.log('FAIL', x.id, x.q, x.a, x.b, x.e));
