// Engine-only measurement: sweepRho/supplied/univariate vs generate-plus.R reference.
const fs = require('fs'); const eng = require(process.argv[2]);
const corpus = JSON.parse(fs.readFileSync(process.argv[3], 'utf8')), ref = JSON.parse(fs.readFileSync(process.argv[4], 'utf8'));
const R = Object.fromEntries(ref.configurations.map(r => [r.id, r]));
const err = (a, b) => Math.abs(a - b) / Math.max(1, Math.abs(b));
const rows = []; const t0 = Date.now();
function cmpFit(id, f, r) {
  let m = 0, q = '';
  const c = (n, a, b) => { if (b == null) { if (a != null) { m = Infinity; q = n + ':undef'; } return; } if (a == null) { m = Infinity; q = n + ':null'; return; } const e = err(a, b); if (!(e <= m)) { m = e; q = n; } };
  for (let j = 0; j < 2; j++) { c('mu', f.mu[j], r.mu[j]); c('se', f.muSE[j], r.muSE[j]); for (let l = 0; l < 2; l++) { c('G', f.G[j][l], r.G[j][l]); c('V', f.muVcov[j][l], r.muVcov[j][l]); } }
  c('rho', f.rho, r.rho); c('ll', f.logLik, r.logLik);
  const tol = r.adjudication.startsWith('two-study') ? 1e-9 : 1e-6;
  rows.push({ id, q, m, ok: m <= tol, adj: r.adjudication.slice(0, 8), js: (f.optimizer||{}).boundary, rgrad: r.rGradMax, pol: (f.optimizer||{}).polish && f.optimizer.polish.stop });
}
for (const c of corpus.configurations) {
  const r = R[c.id]; if (!r) continue;
  const sup = c.rows.map(x => ({ y: x.y, S: [[x.v[0], x.cov], [x.cov, x.v[1]]] }));
  let f = null; try { f = eng.fit(sup); } catch (e) { if (r.supplied.status !== 'refused') rows.push({ id: c.id + '#sup', q: 'threw ' + e.message, m: Infinity, ok: false }); }
  if (f) { if (r.supplied.status === 'refused') rows.push({ id: c.id + '#sup', q: 'should refuse', m: Infinity, ok: false }); else cmpFit(c.id + '#sup', f, r.supplied); }
  const sw = eng.sweepRho(c.rows.map(x => ({ y: x.y, v: x.v })), corpus.grid);
  sw.forEach((s, i) => { const rr = r.sweep[i]; if (s.status !== rr.status) rows.push({ id: c.id + '#' + s.rhoW, q: 'status ' + s.status + ' ' + (s.reason || ''), m: Infinity, ok: false }); else if (s.status === 'ok') cmpFit(c.id + '#' + s.rhoW, s.fit, rr); });
  for (let j = 0; j < 2; j++) { const u = eng.fitUnivariate(c.rows.map(x => x.y[j]), c.rows.map(x => x.v[j])), ru = r.univariate[j];
    const m = Math.max(err(u.mu, ru.mu), err(u.se, ru.se), err(u.tau2, ru.tau2), err(u.logLik, ru.logLik)); rows.push({ id: c.id + '#uni' + j, q: 'uni', m, ok: m <= 1e-6, js: (u.optimizer||{}).boundary, adj: 'tau2=' + ru.tau2 }); }
}
rows.sort((a, b) => b.m - a.m);
console.log('fits', rows.length, 'fails', rows.filter(r => !r.ok).length, 'ms', Date.now() - t0);
for (const r of rows.slice(0, +process.argv[5] || 15)) console.log(JSON.stringify(r));
