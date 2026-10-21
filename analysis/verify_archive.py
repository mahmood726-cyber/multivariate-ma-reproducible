"""Fail-closed archive verifier: inventory, bundle provenance, compression, patch replay, coverage, text hygiene, metadata.

Run from anywhere: python analysis/verify_archive.py   (needs git on PATH for the patch replay)
"""
import hashlib, json, shutil, subprocess, sys, tempfile
CR, LF, CRLF = bytes([13]), bytes([10]), bytes([13, 10])
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (ROOT, read, sha, source_files, inventory, clean_text, is_text, provenance_text, metadata, sizes,
                    compressed, check_expected, quantities, RELEASE, RELEASE_DOI, RELEASE_COMMIT)

CONFIG = {
    18: dict(title='Multivariate (bivariate) meta-analysis in the browser: validation against the R packages mvmeta and metafor',
             page='multivariate-ma/index.html', commit='acd363fa33f0decd2fcafcf08814f663bb9d6178',
             bundle_excluded={'archive-manifest.json', 'PROGRESS.md'},
             bundle_excluded_prefix=('node_modules/',)),
}
PAPER = read(ROOT / 'expected/paper_values.json')['paper']
CFG = CONFIG[PAPER]

def bundle_name(rel, proof):
    """Map an archive path to the path it had in the extracted validation bundle (None for files authored here)."""
    parts = rel.split('/')
    if rel in proof:
        return proof[rel]['original_name']
    if parts[0] == 'app' and len(parts) > 2 and parts[1] in ('original', 'patched'):
        return f'app-{parts[1]}/' + '/'.join(parts[2:])
    if rel in ('app/source-manifest.json', 'app/LICENSE.app.txt'):
        return parts[-1]
    if parts[0] in ('data', 'results') and rel != 'data/bundle-provenance.json':
        return '/'.join(parts[1:])
    if parts[0] == 'bench':
        if rel == 'bench/bundle-README.md':
            return 'README.md'
        if rel == 'bench/bundle-archive-manifest.json':
            return None
        return '/'.join(parts[1:])
    return None

def bundle_manifest():
    m = read(ROOT / 'bench/bundle-archive-manifest.json')
    assert m['root'] == 'P18-validation', 'Unexpected bundle root'
    out = {x['path']: x['sha256'] for x in m['files']}
    assert len(out) == len(m['files']), 'Duplicate bundle manifest path'
    return out

def eol_record():
    return read(ROOT / 'analysis/eol_normalization.json')

def bundle_digest(p, rel, proof, eol):
    """SHA-256 of the file as it was in the bundle: the xz original, the CRLF form of a normalized file, or the bytes as stored."""
    if rel in proof:
        return proof[rel]['original_sha256']
    raw = Path(p).read_bytes()
    if rel in eol:
        assert CR not in raw, 'EOL-normalized file still contains CR: ' + rel
        crlf = raw.replace(LF, CRLF); assert hashlib.sha256(crlf).hexdigest() == eol[rel], 'EOL-normalized file changed: ' + rel
        return eol[rel]
    return hashlib.sha256(raw).hexdigest()

def provenance_against_bundle():
    proof = {r['stored']: r for r in read(ROOT / 'analysis/compression_proof.json')}
    eol = eol_record()
    manifest = bundle_manifest(); matched = set(); authored = []
    for p in source_files():
        rel = p.relative_to(ROOT).as_posix(); name = bundle_name(rel, proof)
        if name is None:
            authored.append(rel); continue
        if name not in manifest:
            raise AssertionError('Bundle file absent from bundle manifest: ' + rel)
        digest = bundle_digest(p, rel, proof, eol)
        assert digest == manifest[name], 'Archive file differs from the validation bundle: ' + rel
        matched.add(name)
    missing = sorted(n for n in set(manifest) - matched
                     if n not in CFG['bundle_excluded'] and not n.startswith(CFG.get('bundle_excluded_prefix', ('\0',))))
    assert not missing, f'Bundle files neither archived nor documented as excluded: {missing[:5]}'
    return len(matched), authored

def app_sources():
    app = ROOT / 'app'
    inventory([p for p in app.rglob('*') if p.is_file() and p.name != 'app-sha256.json'], app, read(app / 'app-sha256.json'))
    m = read(app / 'source-manifest.json')
    rows = [(x['path'], x['sha256']) for x in m['files']]
    rows = list(rows); assert rows, 'Empty upstream source manifest'
    eol = eol_record()
    for rel, digest in rows:
        assert bundle_digest(app / 'original' / rel, 'app/original/' + rel, {}, eol) == digest, 'Original page asset differs from upstream manifest: ' + rel
    assert m['commit'] == CFG['commit'], 'Unexpected source commit'
    assert (app / 'original' / CFG['page']).is_file() and (app / 'patched' / CFG['page']).is_file(), 'Missing page snapshot'
    return len(rows)

def patch_replay(patched=None):
    patched = Path(patched) if patched else ROOT / 'app/patched'
    # Outside the archive work tree: inside a Git work tree, git apply would resolve paths from that repository's root.
    with tempfile.TemporaryDirectory(prefix='verify-replay-') as tmp:
        work = Path(tmp) / 'replay'
        shutil.copytree(ROOT / 'app/original', work)
        subprocess.run(['git', 'init', '-q', str(work)], check=True, capture_output=True)
        for args in (['apply', '--check'], ['apply']):
            r = subprocess.run(['git', '-c', 'core.autocrlf=false', '-c', 'core.eol=lf', '-C', str(work), *args, str(ROOT / 'bench/fix.patch')], capture_output=True, text=True)
            assert r.returncode == 0, 'fix.patch does not apply to app/original: ' + r.stderr
        a = {p.relative_to(work).as_posix(): sha(p) for p in work.rglob('*') if p.is_file() and '.git' not in p.relative_to(work).parts}
        b = {p.relative_to(patched).as_posix(): sha(p) for p in patched.rglob('*') if p.is_file()}
        assert a == b, 'app/original + bench/fix.patch is not byte-identical to app/patched: ' + repr(sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))[:5])
        return len(b)

def coverage():
    expected = read(ROOT / 'expected/paper_values.json')
    keys = [c['id'] for c in read(ROOT / 'data/corpus.json')]
    sets = dict(reference=[r['id'] for r in read(ROOT / 'results/reference.json')],
                original=[a['id'] for a in read(ROOT / 'results/app-original.json')],
                patched=[a['id'] for a in read(ROOT / 'results/app-patched.json')])
    assert len(keys) == len(set(keys)) == expected['configurations'], 'Corpus key coverage'
    for name, ks in sets.items():
        assert len(ks) == len(set(ks)) and set(ks) == set(keys), 'Keyed coverage: ' + name
    import csv
    with open(ROOT / 'data/configuration-ledger.csv', encoding='utf-8', newline='') as f:
        ledger = [r['id'] for r in csv.DictReader(f)]
    assert sorted(ledger) == sorted(keys) and len(ledger) == len(set(ledger)), 'Configuration ledger coverage'
    with open(ROOT / 'data/dataset-ledger.csv', encoding='utf-8', newline='') as f:
        ds = list(csv.DictReader(f))
    assert len(ds) == expected['candidate_datasets'] and sum(r['status'] == 'included' for r in ds) == expected['included_datasets'], 'Dataset ledger'
    for v in ['original', 'patched']:
        check_expected(read(ROOT / f'results/results-{v}.json'), expected[v], 'archived ' + v)
    assert expected['patched']['passed'] == expected['patched']['checks'], 'Patched archive must be all-pass'
    return len(keys)

PR154 = '1b9b9327d75262b9ff8c32ecc5d6414c264071d6'
EQUIVALENCE_FACTS = [RELEASE_COMMIT, RELEASE_DOI, PR154, '85f328c', '18682/18682', '18581/18682', '54612/54612', '29473/29502',
                     'multivariate-ma-results-v2', 'f368030ab2e5ed2bb9298ed3556e319a2c176cfe48396591460adeeb8174fd9e',
                     '597d927e09a09e3bed40494e02fd7aee75226e1c4c274a8cb83daa767e4b6b99', 'byte-identical', 'not bit for bit']

def release_equivalence():
    """RELEASE_EQUIVALENCE.md must exist and state the release, the PR #154 pin and the executed counts; the stored v1.8.0
    corrected-page comparison must differ from the pinned patched result ONLY in the output-schema check."""
    eq = (ROOT / 'RELEASE_EQUIVALENCE.md').read_text(encoding='utf-8')
    assert '<ALLMETA_RELEASE' not in eq, 'Unfilled release token: RELEASE_EQUIVALENCE.md'
    missing = [f for f in EQUIVALENCE_FACTS if f not in eq]
    assert not missing, f'Release equivalence record incomplete: {missing}'
    exp = read(ROOT / 'expected/paper_values.json')['patched']
    v18 = read(ROOT / 'release-equivalence/v1-results-patched-v1.8.0.json')
    got = quantities(v18); schema = exp['quantities']['schema']['checks']
    assert got == dict(exp['quantities'], schema=dict(checks=schema, passed=0)), 'v1.8.0 corrected-page counts differ beyond the schema check'
    assert (v18['total'], v18['passed']) == (exp['checks'], exp['checks'] - schema) == (18682, 18581), 'v1.8.0 corrected-page totals'
    assert len(v18['failures']) == schema and {(f['quantity'], f['actual'], f['reference']) for f in v18['failures']} ==         {('schema', 'multivariate-ma-results-v2', 'multivariate-ma-results-v1')}, 'v1.8.0 corrected-page failures are not all the schema version'
    diff = read(ROOT / 'release-equivalence/v1-capture-diff.json')
    assert diff['configurations'] == exp_configurations() and 0 < diff['max_scaled_difference'] < 1e-6, 'v1.8.0 capture difference record'
    rt = read(ROOT / 'plus/roundtrip/roundtrip-result.json')
    assert sha(ROOT / 'plus/roundtrip/roundtrip-result.json') in eq and (rt['checks'], rt['passed']) == (29502, 29473), 'Round-trip equivalence'
    assert sha(ROOT / 'plus/app-plus.json') in eq, 'Plus capture equivalence'
    return v18['passed'], v18['total']

def exp_configurations():
    return read(ROOT / 'expected/paper_values.json')['configurations']

def verify():
    files = source_files()
    n = inventory(files, ROOT, read(ROOT / 'SOURCE_SHA256.json'))
    sizes([p.stat().st_size for p in files + [ROOT / 'SOURCE_SHA256.json']])
    proof = read(ROOT / 'analysis/compression_proof.json')
    assert {r['stored'] for r in proof} == {p.relative_to(ROOT).as_posix() for p in files if p.suffix == '.xz'}, 'Compression inventory'
    for r in proof:
        compressed(ROOT / r['stored'], r)
    eol = eol_record()
    assert all((ROOT / rel).is_file() for rel in eol), 'EOL record lists a missing file'
    for p in files + [ROOT / 'SOURCE_SHA256.json']:
        if is_text(p):
            rel, raw = p.relative_to(ROOT).as_posix(), p.read_bytes()
            if rel in CFG.get('bom_allowed', ()) and raw.startswith(bytes([0xEF, 0xBB, 0xBF])):
                raw = raw[3:]
            clean_text(raw, rel)
    for name in ['README.md', 'CITATION.cff', '.zenodo.json']:
        provenance_text((ROOT / name).read_text(encoding='utf-8'), name)
    metadata(read(ROOT / '.zenodo.json'), CFG['title'])
    matched, authored = provenance_against_bundle()
    upstream = app_sources(); replay = patch_replay(); keys = coverage(); v18_passed, v18_total = release_equivalence()
    print(f'ARCHIVE PASS: {n} pinned files; {matched} identical to the validation-bundle manifest ({len(eol_record())} via reversible CRLF-to-LF normalization); {len(authored)} archive-authored; '
          f'{upstream} original assets match upstream {read(ROOT / "app/source-manifest.json")["commit"][:7]}; fix.patch replay matches {replay} patched files; '
          f'{keys} configurations with exact keyed coverage; allmeta {RELEASE} ({RELEASE_COMMIT[:7]}, DOI {RELEASE_DOI}) filled; '
          f'release equivalence recorded (v1 tier pinned at PR #154 {PR154[:7]}; v1.8.0 run {v18_passed}/{v18_total}, schema-only failures)', flush=True)

if __name__ == '__main__':
    verify()
