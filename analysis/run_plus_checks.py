"""Plus layer: compare the archived plus-panel page outputs with a FRESH R refit (called by validate_plus.R).

Usage: python -B analysis/run_plus_checks.py WORK
WORK must hold plus-corpus.json (rebuilt by make_plus_corpus.py from the fresh v1 corpus) and plus-reference.json
(written by plus/source/multivariate-ma/validate/generate-plus.R run on that corpus by validate_plus.R).

Gates (all fail closed, nonzero exit):
 1. the rebuilt plus corpus is byte-identical to the archived plus corpus;
 2. the fresh R reference reproduces the archived plus reference within 1e-10 (structure, strings, statuses exact);
 3. the archived page outputs (plus/app-plus.json, captured from the source commit by analysis/dump_plus_app.cjs)
    are compared with the FRESH R values by a line-for-line port of the source commit's plus-contract.js:
    iterative REML quantities 1e-6 relative to max(1,|R|), two-study exact fits and the closed-form p(z) grid 1e-9,
    p-values 1e-6 absolute, statuses / k / refusal reasons / undefined-rho status / displayed strings exact;
    a bivariate fit at a boundary whose parameters differ beyond tolerance passes iff page logLik >= R logLik - 1e-8,
    and the set of fits passed that way must equal the list pinned in expected/plus_values.json;
 4. the number of checks is derived from the reference structure alone and must equal the pinned count
    (so a missing page result is a failed check, never a smaller denominator);
 5. the archived exported-R-script round trip (plus/roundtrip) is re-compared from its stored files with a port of
    the STRICT allmeta v1.8.0 roundtrip-compare.cjs (fitIntegrity; z/p never adjudicated) and must reproduce the
    pinned counts, the exact list of failing checks and the pinned list of parameter-adjudicated fits; the superseded
    d089222 rule is also re-run as labelled history and must reproduce roundtrip-result.v1rule.json.
"""
import json, math, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, read, dump, deep_compare

PLUS = ROOT / 'plus'
VALIDATE = PLUS / 'source' / 'multivariate-ma' / 'validate'
TOL_IT, TOL_EXACT, TOL_LL_ADJ = 1e-6, 1e-9, 1e-8
REFERENCE_RTOL = 1e-10
INF, NAN = float('inf'), float('nan')


def isnum(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def rel(a, r):
    return abs(a - r) / max(1.0, abs(r)) if isnum(a) and isnum(r) else INF


def absd(a, r):
    return abs(a - r) if isnum(a) and isnum(r) else INF


def jsnum(x):
    """String(x) of a JavaScript number for the grid values used in check ids."""
    return str(int(x)) if float(x) == int(x) else repr(float(x))


class Replay:
    def __init__(self):
        self.checks = 0; self.passed = 0; self.failed = []; self.adjudicated = []; self.by_q = {}
        self.app_higher = 0; self.ref_higher = 0; self.max_ll = 0.0; self.maxima = {}

    def rec(self, id_, q, ok, app=None, ref=None, diff=None):
        self.checks += 1
        s = self.by_q.setdefault(q, [0, 0]); s[0] += 1
        if ok:
            self.passed += 1; s[1] += 1
        else:
            self.failed.append(dict(id=id_, quantity=q, app=app, ref=ref, diff=diff if diff is None or math.isfinite(diff) else 'inf'))
        if diff is not None and math.isfinite(diff):
            self.maxima[q] = max(self.maxima.get(q, 0.0), diff)

    def exact(self, id_, q, a, r):
        self.rec(id_, q, a == r and type(a) is type(r) or (isnum(a) and isnum(r) and a == r), a, r, 0.0 if a == r else INF)

    def fit(self, id_, app, status, reason, r):
        """Port of fitChecks() in plus-contract.js. app = the archived page record {status, reason, fit, tests}."""
        f, tests = app.get('fit'), app.get('tests')
        self.exact(id_, 'status', status, r['status'])
        if r['status'] != 'ok':
            self.exact(id_, 'refusal_reason', reason if status == 'refused' else None, r['reason']); return
        ok = status == 'ok' and f is not None
        tol = TOL_EXACT if re.match(r'two-study exact', r['adjudication']) else TOL_IT
        self.exact(id_, 'k', f['k'] if ok else None, r['k'])
        app_ll = f['logLik'] if ok and isnum(f['logLik']) else NAN
        ll_diff = (app_ll - r['logLik']) if ok else -INF
        d = rel(f['logLik'], r['logLik']) if ok else INF
        self.rec(id_, 'logLik', ok and d <= tol, f['logLik'] if ok else None, r['logLik'], d)
        if ok and math.isfinite(ll_diff):
            self.max_ll = max(self.max_ll, abs(ll_diff))
            if ll_diff > 1e-10: self.app_higher += 1
            elif ll_diff < -1e-10: self.ref_higher += 1
        app_rho_null = bool(ok and f['rhoIsNull'])
        if r['rho'] is None:
            self.exact(id_, 'rho_undefined', app_rho_null if ok else None, True)
        pending = []
        def num(q, a, rv, t, absolute=False):
            pending.append((q, a, rv, absd(a, rv) if absolute else rel(a, rv), t))
        for j in range(2):
            num('mu', f['mu'][j] if ok else None, r['mu'][j], tol); num('muSE', f['muSE'][j] if ok else None, r['muSE'][j], tol)
            num('z', tests[j]['z'] if ok else None, r['z'][j], tol); num('p', tests[j]['p'] if ok else None, r['p'][j], tol, True)
            for l in range(2):
                num('G', f['G'][j][l] if ok else None, r['G'][j][l], tol); num('muVcov', f['muVcov'][j][l] if ok else None, r['muVcov'][j][l], tol)
        if r['rho'] is not None:
            num('rho', None if (not ok or app_rho_null) else f['rho'], r['rho'], tol)
        any_fail = any(not (x[3] <= x[4]) for x in pending)
        at_boundary = ok and (r['adjudication'] != 'none' or bool(re.search(r'zero|rank-one', f.get('boundary') or ''))
                              or (r['rho'] is not None and abs(r['rho']) > 1 - 1e-6) or app_rho_null)
        adj = any_fail and at_boundary and ll_diff >= -TOL_LL_ADJ
        if adj:
            self.adjudicated.append(id_)
        for q, a, rv, dd, t in pending:
            self.rec(id_, q, adj or dd <= t, a, rv, dd)


def expected_checks(ref, with_display):
    """Port of expectedChecks() in plus-contract.js."""
    n = 0
    fit = lambda s: 20 if s['status'] == 'ok' else 2
    for r in ref['configurations']:
        n += fit(r['supplied']) + sum(fit(s) for s in r['sweep'])
        n += sum(9 if u['status'] == 'ok' else 1 for u in r['univariate'])
        if with_display:
            if r['supplied']['status'] == 'ok':
                n += 22
            n += sum(8 if s['status'] == 'ok' else 3 for s in r['sweep'])
    return n + len(ref['pnormGrid']) + len(ref['metaforBerkeySweep']) * 9


def replay(corpus, ref, app):
    """Port of replay() in plus-contract.js over archived page outputs. Returns (numeric Replay, display Replay)."""
    assert corpus['schema'] == 'multivariate-ma-plus-corpus-v1' and ref['schema'] == 'multivariate-ma-plus-reference-v1', 'plus schema'
    assert app['schema'] == 'multivariate-ma-plus-app-outputs-v1', 'plus app-output schema'
    grid = corpus['grid']
    assert ref['grid'] == grid and len(grid) == 19, 'plus grid'
    cs, rs, aps = corpus['configurations'], ref['configurations'], app['configurations']
    assert len(cs) == len(rs) == len(aps), 'plus configuration counts differ'
    R, D = Replay(), Replay()
    for i, (c, r, a) in enumerate(zip(cs, rs, aps)):
        assert c['id'] == r['id'] == a['id'], f'plus configuration identity differs at {i}'
        sup = a['supplied']
        R.fit(c['id'] + '#supplied', sup, sup['status'], sup['reason'], r['supplied'])
        assert isinstance(a['sweep'], list) and len(a['sweep']) == len(grid) == len(r['sweep']), 'plus sweep length ' + c['id']
        for j, s in enumerate(a['sweep']):
            assert r['sweep'][j]['rhoW'] == grid[j], 'plus sweep grid ' + c['id']
            R.fit(c['id'] + '#rhoW=' + jsnum(grid[j]), s, s['status'], s['reason'], r['sweep'][j])
        for j in range(2):
            id_ = c['id'] + '#univariate' + str(j)
            u = a['univariate'][j] if a['univariate'] else dict(status=sup['status'])
            ru = r['univariate'][j]
            R.exact(id_, 'uni_status', u['status'], ru['status'])
            if ru['status'] != 'ok':
                continue
            ok = u['status'] == 'ok'
            R.exact(id_, 'uni_k', u['k'] if ok else None, ru['k'])
            for q in ['mu', 'se', 'tau2', 'logLik', 'z']:
                d = rel(u[q], ru[q]) if ok else INF; R.rec(id_, 'uni_' + q, d <= TOL_IT, u.get(q), ru[q], d)
            d = absd(u['p'], ru['p']) if ok else INF; R.rec(id_, 'uni_p', d <= TOL_IT, u.get('p'), ru['p'], d)
            ref_ratio = (r['supplied']['muSE'][j] ** 2) / (ru['se'] ** 2) if r['supplied']['status'] == 'ok' else None
            ar = a['varRatio'][j] if a['varRatio'] else None
            dr = (0.0 if ar is None else INF) if ref_ratio is None else rel(ar, ref_ratio)
            R.rec(id_, 'varRatio', dr <= TOL_IT, ar, ref_ratio, dr)
        for x in a['display']:
            D.rec(c['id'] + '#display', 'display:' + x['key'], isinstance(x['shown'], str) and x['shown'] == x['expected'], x['shown'], x['expected'])
        if i == 0:
            for j, m in enumerate(ref['metaforBerkeySweep']):
                s = a['sweep'][j]; ok = s['status'] == 'ok'; f = s['fit']; id_ = c['id'] + '#rma.mv#rhoW=' + jsnum(m['rhoW'])
                for q in range(2):
                    d = rel(f['mu'][q], m['mu'][q]) if ok else INF; R.rec(id_, 'rma.mv_mu', d <= TOL_IT, None, m['mu'][q], d)
                    d = rel(f['muSE'][q], m['muSE'][q]) if ok else INF; R.rec(id_, 'rma.mv_muSE', d <= TOL_IT, None, m['muSE'][q], d)
                    for l in range(2):
                        d = rel(f['G'][q][l], m['G'][q][l]) if ok else INF; R.rec(id_, 'rma.mv_G', d <= TOL_IT, None, m['G'][q][l], d)
                d = rel(f['logLik'], m['logLik']) if ok else INF; R.rec(id_, 'rma.mv_logLik', d <= TOL_IT, None, m['logLik'], d)
    assert [x['z'] for x in app['pnorm']] == [x['z'] for x in ref['pnormGrid']], 'p(z) grid differs'
    for x, y in zip(app['pnorm'], ref['pnormGrid']):
        d = absd(x['p'], y['p']); R.rec('pnorm#z=' + jsnum(y['z']), 'p_closed_form', d <= TOL_EXACT, x['p'], y['p'], d)
    n_num, n_all = expected_checks(ref, False), expected_checks(ref, True)
    assert R.checks == n_num, f'Plus numeric check cardinality mismatch: {R.checks} != {n_num}'
    assert R.checks + D.checks == n_all, f'Plus check cardinality mismatch: {R.checks + D.checks} != {n_all}'
    return R, D


_LG = [676.5203681218851, -1259.1392167224028, 771.3234287776531, -176.6150291621406, 12.507343278686905,
       -.13857109526572012, 9.984369578019572e-6, 1.5056327351493116e-7]


def _lgamma(z):
    """Port of _lgamma() in shared/multivariate-ma.js (Lanczos, g = 7)."""
    if z < .5:
        return math.log(math.pi) - math.log(math.sin(math.pi * z)) - _lgamma(1 - z)
    z -= 1; x = .99999999999980993
    for i, c in enumerate(_LG):
        x += c / (z + i + 1)
    t = z + 7.5
    return .5 * math.log(2 * math.pi) + (z + .5) * math.log(t) - t + math.log(x)


def chisq_sf(x, df):
    """Port of chisqSF() in shared/multivariate-ma.js: P(chi-square_df > x)."""
    assert isnum(x) and x >= 0 and df > 0, 'invalid chi-square argument'
    if x == 0:
        return 1.0
    a, z = df / 2, x / 2
    scale = math.exp(-z + a * math.log(z) - _lgamma(a))
    if z < a + 1:
        term = 1 / a; total = term
        for n in range(1, 10000):
            term *= z / (a + n); total += term
            if abs(term) < abs(total) * 2e-16:
                return max(0.0, 1 - total * scale)
    else:
        b = z + 1 - a; cc = 1e300; d = 1 / b; h = d
        for n in range(1, 10000):
            an = -n * (n - a); b += 2; d = an * d + b
            if abs(d) < 1e-300: d = 1e-300
            cc = b + an / cc
            if abs(cc) < 1e-300: cc = 1e-300
            d = 1 / d; delta = d * cc; h *= delta
            if abs(delta - 1) < 2e-16:
                return scale * h
    raise AssertionError('incomplete gamma did not converge')


def z_test(mu, se):
    """Port of zTest() in shared/multivariate-ma.js; None where the page refuses."""
    if not (isnum(mu) and isnum(se) and se > 0):
        return None
    z = mu / se
    return z, chisq_sf(z * z, 1)


def fit_integrity(rows, app, tests, rho_w, tol):
    """Port of fitIntegrity() in validate/plus-contract.js at allmeta v1.8.0 (1cb3f84): rebuild GLS and REML from the
    reported G and the input covariances, without optimizing or trusting the reported means, SEs, z, p or logLik.
    Returns (internally consistent, recomputed REML logLik)."""
    fail = (False, -INF)
    if not rows or len(rows) < 2 or not app or not app.get('G'):
        return fail
    G = app['G']; a, b, c = G[0][0], G[0][1], G[1][1]
    if not all(isnum(x) for x in (a, b, c, G[1][0])) or a < 0 or c < 0 or b != G[1][0] \
            or abs(b) > math.sqrt(a) * math.sqrt(c) * (1 + 8 * 2.220446049250313e-16):
        return fail
    s00 = s01 = s11 = h0 = h1 = ld = 0.0; weights = []
    for row in rows:
        cov = row['cov'] if rho_w is None else rho_w * math.sqrt(row['v'][0] * row['v'][1])
        v0, v1, v01 = row['v'][0] + a, row['v'][1] + c, cov + b
        det = v0 * v1 - v01 * v01
        if not (v0 > 0 and det > 0):
            return fail
        w0, w1, w01 = v1 / det, v0 / det, -v01 / det
        weights.append((w0, w01, w1)); ld += math.log(det)
        s00 += w0; s01 += w01; s11 += w1
        h0 += w0 * row['y'][0] + w01 * row['y'][1]; h1 += w01 * row['y'][0] + w1 * row['y'][1]
    sd = s00 * s11 - s01 * s01
    if not (sd > 0):
        return fail
    V = [[s11 / sd, -s01 / sd], [-s01 / sd, s00 / sd]]
    mu = [V[0][0] * h0 + V[0][1] * h1, V[1][0] * h0 + V[1][1] * h1]; q = 0.0
    for row, w in zip(rows, weights):
        d0, d1 = row['y'][0] - mu[0], row['y'][1] - mu[1]
        q += d0 * (w[0] * d0 + w[1] * d1) + d1 * (w[1] * d0 + w[2] * d1)
    ll = -0.5 * (ld + math.log(sd) + q) - (len(rows) - 1) * math.log(2 * math.pi) + math.log(len(rows))
    valid = rel(app.get('logLik'), ll) <= tol
    for j in range(2):
        se = math.sqrt(V[j][j]); t = z_test(app['mu'][j], app['muSE'][j])
        valid = valid and rel(app['mu'][j], mu[j]) <= tol and rel(app['muSE'][j], se) <= tol and \
            t is not None and rel(tests[j][0], t[0]) <= tol and absd(tests[j][1], t[1]) <= tol
        if app.get('muVcov'):
            for l in range(2):
                valid = valid and rel(app['muVcov'][j][l], V[j][l]) <= tol
    rho = b / math.sqrt(a * c) if a > 0 and c > 0 else None
    valid = valid and (app.get('rho') is None if rho is None else rel(app.get('rho'), rho) <= tol)
    return bool(valid), ll


def _roundtrip_walk(pair):
    """Walk the archived round-trip files in the order of roundtrip-compare.cjs; pair(R, id, page, R_fit, rows, rhoW)
    checks one bivariate fit."""
    rt = PLUS / 'roundtrip'
    index = read(rt / 'index.json')
    R = Replay(); missing = []
    for c in index:
        pf, rf = rt / 'page' / (c['n'] + '.json'), rt / 'scripts' / c['n'] / 'multivariate-ma-results.json'
        if not rf.is_file():
            missing.append(c['n']); R.rec(c['id'], 'R output missing', False); continue
        page, Rr = read(pf), read(rf)
        rows = (page.get('input') or {}).get('rows')
        R.rec(c['id'], 'k', Rr['k'] == c['k'])
        main = page.get('result')
        pair(R, c['id'] + '#main', main if main and main.get('mu') else None, Rr['main'], rows, None)
        if not Rr['rma.mv'].get('error') and main and main.get('mu'):
            R.rec(c['id'] + '#rma.mv', 'logLik_not_worse', main['logLik'] - Rr['rma.mv']['logLik'] >= -1e-8)
        for j in range(2):
            u, r = page['univariate'][j], Rr['univariate'][j]
            for q in ['mu', 'se', 'tau2', 'logLik', 'z']:
                R.rec(c['id'] + '#uni' + str(j), 'uni_' + q, rel(u[q], r[q]) <= 1e-6)
            R.rec(c['id'] + '#uni' + str(j), 'uni_p', absd(u['p'], r['p']) <= 1e-6)
        R.rec(c['id'], 'sweep_length', len(page['sweep']) == len(Rr['sweep']))
        for s, r in zip(page['sweep'], Rr['sweep']):
            id_ = c['id'] + '#rhoW=' + jsnum(s['rhoW'])
            R.rec(id_, 'rhoW', s['rhoW'] == r['rhoW'])
            pair(R, id_, s if s['status'] == 'ok' else None, r, rows, s['rhoW'])
    return index, R, missing


def _rt_pairs(page, Rr):
    out = []
    for j in range(2):
        out += [('mu', page['mu'][j], Rr['mu'][j]), ('se', page['muSE'][j], Rr['se'][j]), ('z', page['z'][j], Rr['z'][j]), ('p', page['p'][j], Rr['p'][j])]
        out += [('G', page['G'][j][l], Rr['G'][j][l]) for l in range(2)]
    return out


def _count_by_quantity(fails):
    out = {}
    for _, q in fails:
        out[q] = out.get(q, 0) + 1
    return out


def roundtrip(expected):
    """Port of the STRICT roundtrip-compare.cjs of allmeta v1.8.0 (1cb3f84) over the archived round-trip files.
    Parameters 1e-6 relative to max(1,|R|); a fit whose mu/se/G differ more passes those checks only if the page fit is
    internally consistent (fit_integrity) and its RECOMPUTED REML logLik is >= R's - 1e-8; z and p are never
    adjudicated. The counts, the exact set of failing (id, quantity) pairs, the failures by quantity and the
    adjudicated fits must equal both the stored plus/roundtrip/roundtrip-result.json and expected/plus_values.json."""
    adjudicated = []
    def pair(R, id_, page, Rr, rows, rho_w):
        R.rec(id_, 'status', (page is None) == (Rr.get('error') is not None))
        if page is None or Rr.get('error') is not None:
            return
        pairs = _rt_pairs(page, Rr)
        bad = [x for x in pairs if x[0] not in ('z', 'p') and not (rel(x[1], x[2]) <= 1e-6)]
        ok, ll = fit_integrity(rows, page, list(zip(page['z'], page['p'])), rho_w, 1e-6)
        dll = ll - Rr['logLik']
        R.rec(id_, 'logLik_not_worse', ok and dll >= -1e-8)
        adj = bool(bad) and ok and dll >= -1e-8
        if adj:
            adjudicated.append(id_)
        for q, a, b in pairs:
            R.rec(id_, q, ok and ((adj and q not in ('z', 'p')) or rel(a, b) <= 1e-6))
    index, R, missing = _roundtrip_walk(pair)
    stored = read(PLUS / 'roundtrip' / 'roundtrip-result.json')
    assert stored['schema'] == 'multivariate-ma-plus-roundtrip-v1', 'Round-trip result schema'
    assert (R.checks, R.passed) == (stored['checks'], stored['passed']) == (expected['checks'], expected['passed']), \
        f"Round trip {R.passed}/{R.checks} differs from stored {stored['passed']}/{stored['checks']} or pinned {expected['passed']}/{expected['checks']}"
    assert len(index) == stored['cases'] == expected['cases'] and not missing and not stored['missing'], 'Round-trip case coverage'
    fails = sorted([f['id'], f['quantity']] for f in R.failed)
    assert fails == sorted([f['id'], f['q']] for f in stored['failed']) == expected['failed'], \
        'Round-trip failing checks differ from plus/roundtrip/roundtrip-result.json or expected/plus_values.json'
    assert _count_by_quantity(fails) == expected['failed_by_quantity'], 'Round-trip failures by quantity'
    assert sorted(adjudicated) == sorted(a['id'] for a in stored['adjudicated']) == expected['adjudicated'], 'Round-trip adjudication list differs'
    return R, adjudicated


def roundtrip_v1rule_history(expected):
    """HISTORY ONLY (superseded, not the reported result): the round-trip rule of the plus source commit d089222
    (z/p adjudicated with the other parameters on the reported logLik, no integrity check). Must reproduce
    plus/roundtrip/roundtrip-result.v1rule.json and the pinned history values in expected/plus_values.json."""
    adjudicated = []
    def pair(R, id_, page, Rr, rows, rho_w):
        R.rec(id_, 'status', (page is None) == (Rr.get('error') is not None))
        if page is None or Rr.get('error') is not None:
            return
        pairs = _rt_pairs(page, Rr)
        bad = [x for x in pairs if not (rel(x[1], x[2]) <= 1e-6)]
        dll = page['logLik'] - Rr['logLik']
        R.rec(id_, 'logLik_not_worse', dll >= -1e-8)
        adj = bool(bad) and dll >= -1e-8
        if adj:
            adjudicated.append(id_)
        for q, a, b in pairs:
            R.rec(id_, q, adj or rel(a, b) <= 1e-6)
    index, R, missing = _roundtrip_walk(pair)
    stored = read(PLUS / 'roundtrip' / 'roundtrip-result.v1rule.json')
    assert (R.checks, R.passed) == (stored['checks'], stored['passed']) == (expected['checks'], expected['passed']), 'Round-trip history (old rule) counts'
    assert len(index) == stored['cases'] == expected['cases'] and not missing and not R.failed and not stored['failed'], 'Round-trip history coverage'
    assert sorted(adjudicated) == sorted(a['id'] for a in stored['adjudicated']) == sorted(expected['adjudicated']), 'Round-trip history adjudication list'
    return R, adjudicated


def main():
    work = Path(sys.argv[1]).resolve()
    exp = read(ROOT / 'expected/plus_values.json')
    archived_corpus_path = VALIDATE / 'plus' / 'corpus.json'
    assert (work / 'plus-corpus.json').read_bytes() == archived_corpus_path.read_bytes(), \
        'Rebuilt plus corpus differs from plus/source/multivariate-ma/validate/plus/corpus.json'
    corpus = read(archived_corpus_path)
    print(f"Fresh plus corpus: {len(corpus['configurations'])} configurations rebuilt from the fresh v1 corpus by make_plus_corpus.py, "
          f"byte-identical to the archived plus corpus", flush=True)
    fresh, archived = read(work / 'plus-reference.json'), read(VALIDATE / 'plus' / 'reference.json')
    worst = deep_compare(fresh, archived, 'plus-reference', REFERENCE_RTOL)
    exact = sum(f == a for f, a in zip(fresh['configurations'], archived['configurations']))
    fits = [s for c in fresh['configurations'] for s in [c['supplied']] + c['sweep']]
    n_ok, n_ref = sum(s['status'] == 'ok' for s in fits), sum(s['status'] == 'refused' for s in fits)
    n_uni = sum(u['status'] == 'ok' for c in fresh['configurations'] for u in c['univariate'])
    assert (n_ok, n_ref, n_uni) == (exp['bivariate_fits_ok'], exp['bivariate_refusals'], exp['univariate_fits_ok']), 'Fresh plus fit counts'
    print(f"Fresh plus R reference (generate-plus.R; mvmeta 4 starts -> nlminb -> Newton on remlprof.gr; metafor rma; rma.mv on Berkey): "
          f"{n_ok} bivariate fits, {n_ref} refusal, {n_uni} univariate fits; {len(fresh['configurations'])}/{len(fresh['configurations'])} "
          f"configuration records match the archived reference ({exact} exactly equal; max scaled difference {worst:.3g}; tolerance {REFERENCE_RTOL:g})", flush=True)
    app = read(PLUS / 'app-plus.json')
    R, D = replay(corpus, fresh, app)
    assert R.checks == exp['numeric_checks'] and D.checks == exp['display_checks'] and R.checks + D.checks == exp['checks'], 'Plus check counts differ from expected/plus_values.json'
    assert not R.failed and not D.failed, f'Plus failures: {len(R.failed)} numeric, {len(D.failed)} display; first {(R.failed + D.failed)[:3]!r}'
    assert sorted(R.adjudicated) == sorted(exp['adjudicated']), f'Plus logLik-adjudicated fits differ from expected/plus_values.json: {R.adjudicated}'
    print(f"Plus page outputs versus the FRESH R values: {R.passed}/{R.checks} numeric checks pass; {D.passed}/{D.checks} displayed-string checks pass; "
          f"{len(R.adjudicated)} boundary fit passed by the logLik rule ({'; '.join(R.adjudicated)}); page logLik above R by >1e-10 in {R.app_higher} fits, "
          f"R above page by >1e-10 in {R.ref_higher}; max |dlogLik| {R.max_ll:.3g}", flush=True)
    T, rt_adj = roundtrip(exp['roundtrip'])
    by_q = _count_by_quantity(sorted([f['id'], f['quantity']] for f in T.failed))
    print(f"Exported R-script round trip, strict allmeta v1.8.0 rule (archived page exports and Rscript outputs, re-compared): "
          f"{exp['roundtrip']['cases']} scripts, {T.passed}/{T.checks} checks pass; {len(T.failed)} expected failures "
          f"({', '.join(f'{q} {n}' for q, n in sorted(by_q.items(), key=lambda x: (-x[1], x[0])))}) match expected/plus_values.json; "
          f"{len(rt_adj)} fits with parameter adjudication (the exported script uses default single-start mvmeta)", flush=True)
    H, h_adj = roundtrip_v1rule_history(exp['roundtrip_v1rule_history'])
    print(f"History only (superseded rule of d089222): {H.passed}/{H.checks}, {len(h_adj)} logLik-adjudicated fits, "
          f"reproduces plus/roundtrip/roundtrip-result.v1rule.json", flush=True)
    total, passed = R.checks + D.checks, R.passed + D.passed
    line = f'{passed}/{total} plus checks pass'
    dump(work / 'plus-summary.json', dict(numeric_checks=R.checks, numeric_passed=R.passed, display_checks=D.checks, display_passed=D.passed,
                                          adjudicated=R.adjudicated, reference_max_difference=worst, reference_exact=exact,
                                          maxima=R.maxima, roundtrip_checks=T.checks, roundtrip_passed=T.passed,
                                          roundtrip_adjudicated=len(rt_adj), plus_checks=total, plus_passed=passed, final_line=line))


if __name__ == '__main__':
    main()
