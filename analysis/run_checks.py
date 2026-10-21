"""Compare the fresh R run (written by validate.R into WORK) with the archived corpus/reference and the archived app outputs.

Usage (called by validate.R): python -B analysis/run_checks.py .validate-work
Exits nonzero on any mismatch; writes WORK/summary.json only when every gate passes.
"""
import csv, os, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, read, dump, deep_compare, check_expected

REFERENCE_RTOL = 1e-10  # fresh mvmeta/metafor fits versus the archived reference (same versions); app tolerances are 1e-6 / 1e-9


def by_id(records, label):
    ids = [r['id'] for r in records]
    assert len(ids) == len(set(ids)), 'Duplicate ids in ' + label
    return {r['id']: r for r in records}


def rows(p):
    with open(p, encoding='utf-8', newline='') as f:
        return list(csv.reader(f))


def fresh_corpus(work):
    fresh, archived = read(work / 'corpus.json'), read(ROOT / 'data/corpus.json')
    assert [c['id'] for c in fresh] == [c['id'] for c in archived], 'Fresh corpus ids/order differ'
    deep_compare(fresh, archived, 'corpus', rtol=0.0)
    assert rows(work / 'row-ledger.csv') == rows(ROOT / 'data/row-ledger.csv'), 'Fresh row ledger differs from data/row-ledger.csv'
    n_rows = len(rows(ROOT / 'data/row-ledger.csv')) - 1
    print(f'Fresh corpus: {len(fresh)} configurations rebuilt from the installed packages, identical to data/corpus.json; '
          f'row ledger identical ({n_rows} rows)', flush=True)
    return len(fresh)


def fresh_reference(work, expected):
    fresh, archived = by_id(read(work / 'reference.json'), 'fresh reference'), by_id(read(ROOT / 'results/reference.json'), 'archived reference')
    assert list(fresh) == list(archived), 'Fresh reference ids/order differ'
    worst = 0.0; exact = 0
    for k in archived:
        worst = max(worst, deep_compare(fresh[k], archived[k], 'reference:' + k, REFERENCE_RTOL)); exact += fresh[k] == archived[k]
    status = [r['status'] for r in fresh.values()]
    assert status.count('ok') == expected['reference_fits'] and status.count('refused') == expected['reference_refusals'] and \
        len(status) == expected['configurations'], 'Fresh reference status counts'
    x, y = read(work / 'metafor-crosscheck.json'), read(ROOT / 'results/metafor-crosscheck.json')
    worst_x = deep_compare(x, y, 'metafor-crosscheck', REFERENCE_RTOL)
    print(f'Fresh mvmeta reference: {status.count("ok")} fits and {status.count("refused")} refusal over {len(status)} configurations; '
          f'{len(status)}/{len(status)} records match the archived reference ({exact} exactly equal; max scaled difference {worst:.3g}; '
          f'tolerance {REFERENCE_RTOL:g}); metafor rma.mv cross-check reproduced (max scaled difference {worst_x:.3g})', flush=True)
    return dict(records=len(status), exact=exact, max_difference=worst, crosscheck_max_difference=worst_x)


def compare(work, variant):
    r = subprocess.run([sys.executable, '-B', str(ROOT / 'analysis/compare_archive.py'), variant, str(work), str(work)],
                       capture_output=True, text=True, encoding='utf-8', env=dict(os.environ, PYTHONIOENCODING='utf-8'))
    (work / f'compare-{variant}.log').write_text(r.stdout + r.stderr, encoding='utf-8')
    assert r.returncode == 0, f'compare_archive.py {variant} failed: {r.stderr[-2000:]}'
    print(r.stdout, end='', flush=True)
    return read(work / f'results-{variant}.json')


def main():
    work = Path(sys.argv[1]).resolve()
    expected = read(ROOT / 'expected/paper_values.json')
    n = fresh_corpus(work)
    assert n == expected['configurations'], 'Fresh corpus size'
    rep = fresh_reference(work, expected)
    results = {}
    for v in ['original', 'patched']:
        print(f'--- {v} page outputs versus the fresh R values', flush=True)
        results[v] = compare(work, v)
        check_expected(results[v], expected[v], 'fresh ' + v)
    o, p = results['original'], results['patched']
    assert p['passed'] == p['total'] and not p['failures'], 'Patched comparison is not all-pass'
    lines = [f"Original (released page, expected failures): {o['passed']}/{o['total']} checks pass - per-quantity counts and the "
             f"{len(o['failures'])} failing checks match expected/paper_values.json",
             f"{p['passed']}/{p['total']} checks pass"]
    print(lines[0], flush=True)
    dump(work / 'summary.json', dict(corpus_configurations=n, reference=rep, original_checks=o['total'], original_passed=o['passed'],
                                     patched_checks=p['total'], patched_passed=p['passed'], final_line=lines[-1]))


if __name__ == '__main__':
    main()
