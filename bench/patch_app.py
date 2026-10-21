from pathlib import Path
import difflib
root=Path('app-patched')
for file in ['shared/multivariate-ma.js','multivariate-ma/index.html','hub/shared/tests/multivariate-ma-parity.spec.mjs']:
 (root/file).write_bytes(Path('app-original',file).read_bytes())
def edit(file,old,new):
 p=root/file;s=p.read_text(encoding='utf-8');assert old in s,(file,old[:80]);p.write_text(s.replace(old,new),encoding='utf-8',newline='\n')
engine='shared/multivariate-ma.js';page='multivariate-ma/index.html'
edit(engine,'      order();\n      var c =', '''      order();
      var spread = 0;
      for (i = 1; i <= n; i++) for (j = 0; j < n; j++) spread = Math.max(spread, Math.abs(simplex[i][j] - simplex[0][j]) / Math.max(1, Math.abs(simplex[0][j])));
      if (spread < 1e-10 && Math.abs(fv[n] - fv[0]) < 1e-12 * Math.max(1, Math.abs(fv[0]))) break;
      var c =''')
edit(engine,'    var k = studies.length, m = studies[0].y.length, i, a, b;', '''    var k = studies.length, m = studies[0].y && studies[0].y.length, i, a, b;
    if (!m) throw new Error("Outcomes must be finite and covariance matrices conformable.");
    studies.forEach(function (s) {
      if (!Array.isArray(s.y) || s.y.length !== m || !s.y.every(Number.isFinite) || !Array.isArray(s.S) || s.S.length !== m || !s.S.every(function (r) { return Array.isArray(r) && r.length === m && r.every(Number.isFinite); })) throw new Error("Outcomes must be finite and covariance matrices conformable.");
      var L = s.S.map(function (r) { return r.slice(); });
      for (var a = 0; a < m; a++) for (var b = 0; b <= a; b++) {
        if (s.S[a][b] !== s.S[b][a]) throw new Error("Within-study covariance must be symmetric.");
        var v = s.S[a][b];
        for (var d = 0; d < b; d++) v -= L[a][d] * L[b][d];
        if (a === b) { if (!(v > 0)) throw new Error("Within-study covariance must be positive definite."); L[a][b] = Math.sqrt(v); }
        else L[a][b] = v / L[b][b];
      }
    });''')
edit(engine,'    var opt = _nelderMead(obj, x0, 0.05, 2000);\n    opt = _nelderMead(obj, opt.x, 0.005, 1000);\n    var G = _fromChol(opt.x, m), pr = _profile(studies, G);', '''    var opt, G, pr;
    if (k === 2) {
      // REML is the likelihood of the single difference d, with variance S1+S2+2G.
      // Whiten by S1+S2: the constrained optimum is rank one (or exactly zero).
      var delta = studies[0].y.map(function (v, j) { return v - studies[1].y[j]; });
      var wd = _matVec(_matInv(_add(studies[0].S, studies[1].S)), delta);
      var q = delta.reduce(function (s, v, j) { return s + v * wd[j]; }, 0);
      var factor = q > 1 ? 0.5 * (1 - 1 / q) : 0;
      G = delta.map(function (v) { return delta.map(function (w) { return factor * v * w; }); });
      pr = _profile(studies, G);
      var value = pr.logdetV + _logdet(pr.sumW);
      studies.forEach(function (s, i) { var dv = s.y.map(function (v, j) { return v - pr.mu[j]; }), w = _matVec(pr.Ws[i], dv); value += dv.reduce(function (t, v, j) { return t + v * w[j]; }, 0); });
      opt = { f: 0.5 * value };
    } else {
      opt = _nelderMead(obj, x0, 0.05, 2000);
      opt = _nelderMead(obj, opt.x, 0.005, 1000);
      G = _fromChol(opt.x, m);
      // At a rank-one boundary, the redundant Cholesky direction can collapse
      // the simplex before the two identifiable directions are stationary.
      if (m === 2 && G[0][0] > 0 && G[1][1] > 0 && G[0][0] * G[1][1] - G[0][1] * G[0][1] < 1e-8 * G[0][0] * G[1][1]) {
        var v = [Math.sqrt(G[0][0]), G[0][1] / Math.sqrt(G[0][0])];
        function rankGradient(v) {
          var g = v.map(function (a) { return v.map(function (b) { return a * b; }); }), p = _profile(studies, g), sc = [[0, 0], [0, 0]];
          studies.forEach(function (s, i) {
            var w = p.Ws[i], dr = s.y.map(function (y, j) { return y - p.mu[j]; }), wr = _matVec(w, dr);
            for (var a = 0; a < 2; a++) for (var b = 0; b < 2; b++) {
              var t = 0;
              for (var u = 0; u < 2; u++) for (var z = 0; z < 2; z++) t += w[a][u] * p.sumWinv[u][z] * w[z][b];
              sc[a][b] += w[a][b] - t - wr[a] * wr[b];
            }
          });
          return _matVec(sc, v);
        }
        for (var iter = 0; iter < 12; iter++) {
          var grad = rankGradient(v), h = [[], []];
          if (Math.max(Math.abs(grad[0]), Math.abs(grad[1])) < 1e-10) break;
          for (var j = 0; j < 2; j++) {
            var left = v.slice(), right = v.slice(), step = 1e-4 * Math.max(1, Math.abs(v[j]));
            left[j] -= step; right[j] += step;
            var gl = rankGradient(left), gr = rankGradient(right);
            for (var i = 0; i < 2; i++) h[i][j] = (gr[i] - gl[i]) / (2 * step);
          }
          if (!(h[0][0] > 0 && h[1][1] > 0 && h[0][0] * h[1][1] > h[0][1] * h[1][0])) break;
          var delta = _matVec(_matInv(h), grad), accepted = false;
          for (var rate = 1; rate >= 1 / 1024; rate /= 2) {
            var next = v.map(function (x, j) { return x - rate * delta[j]; }), val = obj([next[0], next[1], 0]), ng = rankGradient(next);
            if (val <= opt.f + 1e-12 * Math.max(1, Math.abs(opt.f)) && Math.hypot(ng[0], ng[1]) < Math.hypot(grad[0], grad[1])) { v = next; opt.f = val; accepted = true; break; }
          }
          if (!accepted) break;
        }
        var rankValue = obj([v[0], v[1], 0]);
        if (rankValue <= opt.f + 1e-12 * Math.max(1, Math.abs(opt.f))) { G = _fromChol([v[0], v[1], 0], 2); opt.f = rankValue; }
      }
      // Confirm the exact zero boundary by its covariance score, not an arbitrary rho.
      var zero = G.map(function (row) { return row.map(function () { return 0; }); });
      var zp = _profile(studies, zero), score = zero.map(function (row) { return row.slice(); });
      studies.forEach(function (s, i) {
        var W = zp.Ws[i], dv = s.y.map(function (v, j) { return v - zp.mu[j]; }), wr = _matVec(W, dv);
        for (var a = 0; a < m; a++) for (var b = 0; b < m; b++) {
          var correction = 0;
          for (var u = 0; u < m; u++) for (var v = 0; v < m; v++) correction += W[a][u] * zp.sumWinv[u][v] * W[v][b];
          score[a][b] += W[a][b] - correction - wr[a] * wr[b];
        }
      });
      var zeroValue = obj(new Array(x0.length).fill(0));
      if (m === 2 && score[0][0] >= 0 && score[1][1] >= 0 && score[0][0] * score[1][1] >= score[0][1] * score[1][0] && zeroValue <= opt.f + 1e-12 * Math.max(1, Math.abs(opt.f))) { G = zero; opt.f = zeroValue; }
      pr = _profile(studies, G);
    }
    if (!pr || !Number.isFinite(opt.f)) throw new Error("REML fit did not produce finite results.");''')
edit(engine,'var rho = (m === 2) ? G[0][1] / Math.sqrt(G[0][0] * G[1][1]) : null;', 'var rho = (m === 2 && G[0][0] > 0 && G[1][1] > 0) ? Math.max(-1, Math.min(1, G[0][1] / Math.sqrt(G[0][0] * G[1][1]))) : null;')
edit(page,'var y1 = parseFloat(p[p.length - 5]), v1 = parseFloat(p[p.length - 4]), y2 = parseFloat(p[p.length - 3]), v2 = parseFloat(p[p.length - 2]), cov = parseFloat(p[p.length - 1]);','''function number(s) { return s.trim() ? Number(s) : NaN; }
        var y1 = number(p[p.length - 5]), v1 = number(p[p.length - 4]), y2 = number(p[p.length - 3]), v2 = number(p[p.length - 2]), cov = number(p[p.length - 1]);''')
edit(page,'      var f = window.AlmMultivariate.fit(parsed.studies);','''      _last = null; stats.innerHTML = ""; document.getElementById("plot-host").innerHTML = "";
      var f;
      try { f = window.AlmMultivariate.fit(parsed.studies); }
      catch (error) { head.textContent = error.message; return; }''')
edit(page,'card(esc(o1) + " pooled"','card(o1 + " pooled"');edit(page,'card(esc(o2) + " pooled"','card(o2 + " pooled"')
edit(page,'card("Between-study SD " + esc(o1)','card("Between-study SD " + o1');edit(page,'card("Between-study SD " + esc(o2)','card("Between-study SD " + o2')
edit(page,'var xs = studies.map(function (s) { return s.y[0]; }).concat([f.mu[0]]);\n      var ys = studies.map(function (s) { return s.y[1]; }).concat([f.mu[1]]);','''var radius = Math.sqrt(-2 * Math.log(0.05));
      var xs = studies.map(function (s) { return s.y[0]; }).concat([f.mu[0] - radius * f.muSE[0], f.mu[0] + radius * f.muSE[0]]);
      var ys = studies.map(function (s) { return s.y[1]; }).concat([f.mu[1] - radius * f.muSE[1], f.mu[1] + radius * f.muSE[1]]);''')
edit(page,'r = 2.4477468307;', 'r = Math.sqrt(-2 * Math.log(0.05));')
edit(page,'the two effect sizes, their within-study variances, and their within-study covariance.', 'the two effect sizes, their positive within-study variances, and their covariance (a positive-definite matrix is required). Rows missing either outcome or a numeric covariance are omitted; at least two complete rows are required. Between-study correlation is undefined when a between-study variance is zero.')
# Keep method description accurate after the exact k=2 boundary repair.
edit(page,'G by Cholesky-parameterised Nelder-Mead', 'G by Cholesky-parameterised Nelder-Mead, with the exact REML solution for two studies')
for old,new in [('0.0075, -0.32, 0.0030,','0.0075, -0.32, 0.0077,'),('0.0057, -0.60, 0.0009,','0.0057, -0.60, 0.0008,'),('0.0021, -0.12, 0.0007,','0.0021, -0.12, 0.0014,'),('0.0029, -0.31, 0.0009,','0.0029, -0.31, 0.0015,'),('0.0148, -0.39, 0.0072,','0.0148, -0.39, 0.0304,')]:edit(page,old,new)
test='hub/shared/tests/multivariate-ma-parity.spec.mjs'
edit(test,'AL_v = [0.0030, 0.0009, 0.0007, 0.0009, 0.0072]','AL_v = [0.0077, 0.0008, 0.0014, 0.0015, 0.0304]')
for old,new in [('-0.3567543553','-0.3392151784'),('0.3567947972','0.3534281696'),('0.0817510871','0.0879051358'),('0.0597050546','0.0588486314'),('0.0311744793','0.0326513321'),('0.0121786270','0.0117330253'),('0.4567653812','0.6087986836'),('3.7518022064','3.6917676944')]:edit(test,old,new)
patch=''
for file in [engine,page,test]:
 a=Path('app-original',file).read_text(encoding='utf-8').splitlines(keepends=True);b=(root/file).read_text(encoding='utf-8').splitlines(keepends=True)
 patch+=''.join(difflib.unified_diff(a,b,fromfile='a/'+file,tofile='b/'+file))
Path('fix.patch').write_text(patch,encoding='utf-8',newline='\n')
for file in [engine,page,test]:
 if b'\r\n' in Path('app-original',file).read_bytes():
  p=root/file;p.write_bytes(p.read_bytes().replace(b'\r\n',b'\n').replace(b'\n',b'\r\n'))
print('PATCH: app-only covariance, boundary, parsing, label and plot repairs')
