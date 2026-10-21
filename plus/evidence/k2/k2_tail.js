    if (boundary === "two-study-exact" && G.every(function (row) { return row.every(function (v) { return v === 0; }); })) boundary = "two-study-exact-zero";
    return { mu: pr.mu, muSE: muSE, muVcov: pr.sumWinv, G: G, rho: rho, logLik: logLik, m: m, k: k, optimizer: { boundary: boundary, polish: polish } };
  }

  // ---- normal-theory z test (two-sided) via the regularized upper incomplete gamma ----
  function _lgamma(z) {
    var c = [676.5203681218851, -1259.1392167224028, 771.3234287776531, -176.6150291621406, 12.507343278686905, -.13857109526572012, 9.984369578019572e-6, 1.5056327351493116e-7];
    if (z < .5) return Math.log(Math.PI) - Math.log(Math.sin(Math.PI * z)) - _lgamma(1 - z);
    z--; var x = .99999999999980993; for (var i = 0; i < c.length; i++) x += c[i] / (z + i + 1);
    var t = z + 7.5; return .5 * Math.log(2 * Math.PI) + (z + .5) * Math.log(t) - t + Math.log(x);
  }
  // P(chi-square_df > x): series for small x, Lentz continued fraction otherwise.
  function chisqSF(x, df) {
    if (!Number.isFinite(x) || x < 0 || !(df > 0)) throw new Error("invalid chi-square argument");
    if (x === 0) return 1;
    var a = df / 2, z = x / 2, scale = Math.exp(-z + a * Math.log(z) - _lgamma(a)), n;
    if (z < a + 1) { var term = 1 / a, sum = term; for (n = 1; n < 10000; n++) { term *= z / (a + n); sum += term; if (Math.abs(term) < Math.abs(sum) * 2e-16) return Math.max(0, 1 - sum * scale); } }
    else { var b = z + 1 - a, cc = 1e300, d = 1 / b, h = d; for (n = 1; n < 10000; n++) { var an = -n * (n - a); b += 2; d = an * d + b; if (Math.abs(d) < 1e-300) d = 1e-300; cc = b + an / cc; if (Math.abs(cc) < 1e-300) cc = 1e-300; d = 1 / d; var del = d * cc; h *= del; if (Math.abs(del - 1) < 2e-16) return scale * h; } }
    throw new Error("incomplete gamma did not converge");
  }
  // Two-sided Wald test of mu = 0 using the normal distribution (as mvmeta and rma.mv with test="z").
  function zTest(mu, se) {
    if (!Number.isFinite(mu) || !Number.isFinite(se) || !(se > 0)) return { status: "refused", reason: "SE must be positive and finite" };
    var z = mu / se; return { status: "ok", z: z, p: chisqSF(z * z, 1) };
  }

  // ---- univariate REML (m = 1) on the same rows: y_i ~ N(mu, v_i + tau2) ----
  function fitUnivariate(y, v, opts) {
    if (!Array.isArray(y) || !Array.isArray(v) || y.length !== v.length) throw new Error("y and v must be arrays of equal length");
    var f = fit(y.map(function (yi, i) { return { y: [yi], S: [[v[i]]] }; }), opts);
    return { k: f.k, mu: f.mu[0], se: f.muSE[0], tau2: f.G[0][0], logLik: f.logLik, optimizer: f.optimizer };
  }

  // ---- within-study correlation helpers ----
  function covFromR(v1, v2, r) { return r * Math.sqrt(v1 * v2); }
  // rows: [{ y:[y1,y2], v:[v1,v2] }]; grid: within-study correlations, each |rho_w| < 1.
  // Every study receives the SAME assumed within-study correlation rho_w (supplied
  // covariances, if any, are replaced). Pure: no DOM, no state.
  function sweepRho(rows, grid, opts) {
    if (!Array.isArray(rows) || !Array.isArray(grid)) throw new Error("rows and grid must be arrays");
    return grid.map(function (rw) {
      if (typeof rw !== "number" || !Number.isFinite(rw) || !(Math.abs(rw) < 1)) return { rhoW: rw, status: "refused", reason: "within-study correlation must satisfy |rho| < 1" };
      try {
        var f = fit(rows.map(function (r) { var c = covFromR(r.v[0], r.v[1], rw); return { y: r.y.slice(), S: [[r.v[0], c], [c, r.v[1]]] }; }), opts);
        return { rhoW: rw, status: "ok", fit: f };
      } catch (e) { return { rhoW: rw, status: "refused", reason: e.message }; }
    });
  }
