  // ---- REML objective, score and Fisher information on the entries of G ----
  // obj(G) = ½[Σ log|V_i| + log|Σ W_i| + Σ r_i'W_i r_i]  (= −REML logLik + const).
  function _mm(A, B) { return A.map(function (row) { return B[0].map(function (_, j) { return row.reduce(function (s, x, l) { return s + x * B[l][j]; }, 0); }); }); }
  function _tr(A) { var t = 0; for (var i = 0; i < A.length; i++) t += A[i][i]; return t; }
  function _isPD(M) {
    var n = M.length, L = [], i, j, d;
    for (i = 0; i < n; i++) { L.push(new Array(n).fill(0)); for (j = 0; j <= i; j++) { var v = M[i][j]; for (d = 0; d < j; d++) v -= L[i][d] * L[j][d]; if (i === j) { if (!(v > 0)) return false; L[i][j] = Math.sqrt(v); } else L[i][j] = v / L[j][j]; } }
    return true;
  }
  function _objG(studies, G) {
    var pr = _profile(studies, G); if (!pr) return Infinity;
    var val = pr.logdetV + _logdet(pr.sumW);
    studies.forEach(function (s, i) { var r = s.y.map(function (v, j) { return v - pr.mu[j]; }), w = _matVec(pr.Ws[i], r); val += r.reduce(function (t, v, j) { return t + v * w[j]; }, 0); });
    return 0.5 * val;
  }
  function _params(m) { var P = []; for (var a = 0; a < m; a++) for (var b = a; b < m; b++) P.push([a, b]); return P; }
  function _E(m, a, b) { var E = []; for (var i = 0; i < m; i++) E.push(new Array(m).fill(0)); E[a][b] = 1; E[b][a] = 1; return E; }
  // Gradient of the REML log-likelihood with respect to the free entries of G and the
  // expected (Fisher) information ½tr(P D_a P D_b), computed per study without forming
  // the (km)x(km) REML projection P:
  //   tr(P D_a P D_b) = Σ_i [tr(W E_a W E_b) − tr(W E_a WCW E_b) − tr(WCW E_a W E_b)] + tr(C B_a C B_b),
  //   C = (Σ W_i)⁻¹, B_a = Σ_i W_i E_a W_i.
  function _scoreInfo(studies, G) {
    var m = G.length, pr = _profile(studies, G); if (!pr) return null;
    var C = pr.sumWinv, P = _params(m), Es = P.map(function (ab) { return _E(m, ab[0], ab[1]); });
    var grad = P.map(function () { return 0; }), T = P.map(function () { return P.map(function () { return 0; }); });
    var B = Es.map(function () { var Z = []; for (var i = 0; i < m; i++) Z.push(new Array(m).fill(0)); return Z; });
    studies.forEach(function (s, i) {
      var W = pr.Ws[i], r = s.y.map(function (v, j) { return v - pr.mu[j]; }), u = _matVec(W, r), WCW = _mm(_mm(W, C), W);
      var Pii = W.map(function (row, x) { return row.map(function (v, y) { return v - WCW[x][y]; }); });
      var WE = Es.map(function (E) { return _mm(W, E); });
      Es.forEach(function (E, a) {
        var quad = 0, x, y; for (x = 0; x < m; x++) for (y = 0; y < m; y++) quad += u[x] * E[x][y] * u[y];
        grad[a] += -0.5 * _tr(_mm(Pii, E)) + 0.5 * quad;
        var WEW = _mm(WE[a], W); for (x = 0; x < m; x++) for (y = 0; y < m; y++) B[a][x][y] += WEW[x][y];
        Es.forEach(function (E2, b) {
          T[a][b] += _tr(_mm(WE[a], WE[b])) - _tr(_mm(_mm(WE[a], WCW), E2)) - _tr(_mm(_mm(WCW, E), WE[b]));
        });
      });
    });
    var info = T.map(function (row, a) { return row.map(function (t, b) { return 0.5 * (t + _tr(_mm(_mm(C, B[a]), _mm(C, B[b])))); }); });
    return { grad: grad, info: info, params: P };
  }
  // Fisher-scoring polish of an interior (positive-definite) G. Step-halving keeps G
  // positive definite and never accepts a worse REML objective (tolerance 1e-14 relative).
  // Convergence criterion: largest accepted change in any entry of G < 1e-12 (absolute);
  // otherwise the reason it stopped is reported. maxAbsScore = max |∂ℓ_REML/∂G_ab| at exit.
  function _fisherPolish(studies, G, maxit) {
    var f = _objG(studies, G), it, stop = "max-iterations";
    for (it = 0; it < (maxit || 100); it++) {
      var si = _scoreInfo(studies, G); if (!si) { stop = "profile-failed"; break; }
      var inv = _matInv(si.info); if (!inv) { stop = "singular-information"; break; }
      var delta = _matVec(inv, si.grad), step = 1, accepted = null;
      for (var h = 0; h < 40; h++, step /= 2) {
        var Gn = G.map(function (row) { return row.slice(); });
        si.params.forEach(function (ab, j) { Gn[ab[0]][ab[1]] += step * delta[j]; if (ab[0] !== ab[1]) Gn[ab[1]][ab[0]] = Gn[ab[0]][ab[1]]; });
        if (!_isPD(Gn)) continue;
        var fn = _objG(studies, Gn);
        if (fn <= f + 1e-14 * Math.max(1, Math.abs(f))) { accepted = { G: Gn, f: fn, d: step * Math.max.apply(null, delta.map(Math.abs)) }; break; }
      }
      if (!accepted) { stop = "no-acceptable-step"; break; }
      G = accepted.G; f = accepted.f;
      if (accepted.d < 1e-12) { stop = "converged"; it++; break; }
    }
    var fin = _scoreInfo(studies, G);
    return { G: G, f: f, iterations: it, stop: stop, maxAbsScore: fin ? Math.max.apply(null, fin.grad.map(Math.abs)) : NaN };
  }
