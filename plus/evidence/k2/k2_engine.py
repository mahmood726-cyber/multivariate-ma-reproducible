import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
helpers = open(sys.argv[2], encoding='utf-8').read()
tail = open(sys.argv[3], encoding='utf-8').read()
anchor = '  function fit(studies, opts) {'
assert anchor in s
s = s.replace(anchor, helpers + '\n' + anchor, 1)
old = '''      G = _fromChol(opt.x, m);
      // At a rank-one boundary'''
new = '''      G = _fromChol(opt.x, m);
      boundary = "interior";
      // Interior optimum: polish the simplex result by Fisher scoring.
      var detRel = m === 2 ? (G[0][0] * G[1][1] - G[0][1] * G[0][1]) / (G[0][0] * G[1][1]) : 1;
      if (_isPD(G) && detRel > 1e-8 && opts.polish !== false) {
        var pol = _fisherPolish(studies, G, 100);
        polish = { iterations: pol.iterations, stop: pol.stop, maxAbsScore: pol.maxAbsScore };
        if (pol.f <= opt.f + 1e-12 * Math.max(1, Math.abs(opt.f))) { G = pol.G; opt.f = pol.f; }
      }
      // At a rank-one boundary'''
assert old in s
s = s.replace(old, new, 1)
old2 = 'if (rankValue <= opt.f + 1e-12 * Math.max(1, Math.abs(opt.f))) { G = _fromChol([v[0], v[1], 0], 2); opt.f = rankValue; }'
assert old2 in s
s = s.replace(old2, 'if (rankValue <= opt.f + 1e-12 * Math.max(1, Math.abs(opt.f))) { G = _fromChol([v[0], v[1], 0], 2); opt.f = rankValue; boundary = "rank-one"; }', 1)
old3 = 'if (m === 2 && score[0][0] >= 0 && score[1][1] >= 0 && score[0][0] * score[1][1] >= score[0][1] * score[1][0] && zeroValue <= opt.f + 1e-12 * Math.max(1, Math.abs(opt.f))) { G = zero; opt.f = zeroValue; }'
assert old3 in s
s = s.replace(old3, 'if (((m === 1 && score[0][0] >= 0) || (m === 2 && score[0][0] >= 0 && score[1][1] >= 0 && score[0][0] * score[1][1] >= score[0][1] * score[1][0])) && zeroValue <= opt.f + 1e-12 * Math.max(1, Math.abs(opt.f))) { G = zero; opt.f = zeroValue; boundary = "zero"; }', 1)
o5 = '    var opt, G, pr;\n    if (k === 2) {'
assert o5 in s
s = s.replace(o5, '    var opt, G, pr, boundary = "two-study-exact", polish = null;\n    if (k === 2) {', 1)
old4 = '    return { mu: pr.mu, muSE: muSE, muVcov: pr.sumWinv, G: G, rho: rho, logLik: logLik, m: m, k: k };\n  }'
assert old4 in s
s = s.replace(old4, tail.rstrip('\n'), 1)
o6 = '  var api = { fit: fit };'
assert o6 in s
s = s.replace(o6, '  var api = { fit: fit, fitUnivariate: fitUnivariate, sweepRho: sweepRho, zTest: zTest, chisqSF: chisqSF, covFromR: covFromR, _objG: _objG, _scoreInfo: _scoreInfo };', 1)
open(p, 'w', encoding='utf-8', newline='').write(s)
print('ok')
