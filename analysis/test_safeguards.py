"""Negative tests: every archive gate must reject a planted defect. Fixtures here are tests, not research output.

Run: python analysis/test_safeguards.py   (the version test also needs Rscript on PATH or RSCRIPT set)
"""
import copy, hashlib, lzma, os, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (ROOT, read, sha, inventory, clean_text, provenance_text, metadata, sizes, compressed, deep_compare,
                    check_expected, source_files)
import verify_archive as va

class Safeguards(unittest.TestCase):
    def rejects(self, fn, *args):
        with self.assertRaises((AssertionError, KeyError, ValueError, lzma.LZMAError)):
            fn(*args)

    def test_inventory(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'x'; p.write_bytes(b'x'); pins = {'x': sha(p)}; inventory([p], Path(d), pins)
            self.rejects(inventory, [], Path(d), pins); self.rejects(inventory, [p], Path(d), {})
            self.rejects(inventory, [p], Path(d), dict(pins, y='0' * 64))
            p.write_bytes(b'y'); self.rejects(inventory, [p], Path(d), pins)

    def test_pinned_inventory_is_complete(self):
        pins = read(ROOT / 'SOURCE_SHA256.json')
        self.assertEqual(set(pins), {p.relative_to(ROOT).as_posix() for p in source_files()})

    def test_text_hygiene(self):
        clean_text(b'portable text')
        self.assertTrue(all(va.is_text(Path('x' + suffix)) for suffix in ['.cmd', '.bat', '.ps1']))
        for bad in [b'\xef\xbb\xbftext', ('C' + ':\\' + 'Users' + '\\someone\\file').encode(), ('C' + ':/' + 'Users' + '/x').encode(),
                    ('/' + 'c/' + 'Users/x').encode(), ('/' + 'home/' + 'someone/x').encode(), ('gh' + 'p_' + 'a' * 36).encode(),
                    ('-----BEGIN ' + 'OPENSSH PRIVATE KEY-----').encode()]:
            self.rejects(clean_text, bad)

    def test_provenance_release_filled(self):
        for name in ['README.md', 'CITATION.cff', '.zenodo.json']:
            text = (ROOT / name).read_text(encoding='utf-8'); provenance_text(text, name)
            self.rejects(provenance_text, text.replace('10.5281/zenodo.23515177', 'x'))
            self.rejects(provenance_text, text.replace('v1.8.0', 'x'))
            self.rejects(provenance_text, text + ' <' + 'ALLMETA_RELEASE' + '>')
            self.rejects(provenance_text, text + ' <' + 'ALLMETA_RELEASE_DOI' + '>')
            self.rejects(provenance_text, text + ' ' + 'ALLMETA_RELEASE')
            self.rejects(provenance_text, text + ' <' + 'ALLMETA_UNKNOWN' + '>')
            self.rejects(provenance_text, text + ' 10.5281/zenodo.12345678')
            self.rejects(provenance_text, text + ' the next allmeta release (pending)')

    def test_release_equivalence_gate(self):
        va.release_equivalence()
        eq = ROOT / 'RELEASE_EQUIVALENCE.md'; v18 = ROOT / 'release-equivalence/v1-results-patched-v1.8.0.json'
        text, raw = eq.read_bytes(), v18.read_bytes()
        try:
            for fact in va.EQUIVALENCE_FACTS:
                eq.write_bytes(text.replace(fact.encode(), b'x')); self.rejects(va.release_equivalence)
            eq.write_bytes(text)
            import json
            for mutate in [lambda x: x['summary'][0].update(passed=x['summary'][0]['passed'] - 1),
                           lambda x: x['failures'][0].update(quantity='mu'),
                           lambda x: x.update(passed=x['passed'] + 1)]:
                x = json.loads(raw); mutate(x); v18.write_text(json.dumps(x), encoding='utf-8'); self.rejects(va.release_equivalence)
        finally:
            eq.write_bytes(text); v18.write_bytes(raw)
        va.release_equivalence()

    def test_roundtrip_gate(self):
        import run_plus_checks as rp
        e = read(ROOT / 'expected/plus_values.json')
        rp.roundtrip(e['roundtrip']); rp.roundtrip_v1rule_history(e['roundtrip_v1rule_history'])
        for mutate in [lambda x: x.update(passed=x['passed'] + 1), lambda x: x['failed'].pop(0),
                       lambda x: x['failed'].append(['planted', 'z']), lambda x: x['adjudicated'].pop(0),
                       lambda x: x['failed_by_quantity'].update(z=22)]:
            x = copy.deepcopy(e['roundtrip']); mutate(x); self.rejects(rp.roundtrip, x)
        x = copy.deepcopy(e['roundtrip_v1rule_history']); x['adjudicated'].pop(0); self.rejects(rp.roundtrip_v1rule_history, x)
        page = read(ROOT / 'plus/roundtrip/page/001.json'); app = dict(page['result'])
        ok, ll = rp.fit_integrity(page['input']['rows'], app, list(zip(app['z'], app['p'])), None, 1e-6)
        self.assertTrue(ok)
        for q, j in [('mu', 0), ('muSE', 1)]:
            bad = copy.deepcopy(app); bad[q][j] *= 1 + 1e-5
            self.assertFalse(rp.fit_integrity(page['input']['rows'], bad, list(zip(bad['z'], bad['p'])), None, 1e-6)[0])
        self.assertFalse(rp.fit_integrity(page['input']['rows'], app, [(app['z'][0] * (1 + 1e-5), app['p'][0]), (app['z'][1], app['p'][1])], None, 1e-6)[0])
        self.assertFalse(rp.fit_integrity(page['input']['rows'], dict(app, logLik=app['logLik'] + 1e-3), list(zip(app['z'], app['p'])), None, 1e-6)[0])

    def test_zenodo_metadata(self):
        z = read(ROOT / '.zenodo.json'); metadata(z, va.CFG['title'])
        for field, value in [('title', 'wrong'), ('creators', [{'name': 'Someone, Else'}]), ('creators', []), ('version', '2.0.0'),
                             ('license', 'other'), ('related_identifiers', [])]:
            zz = copy.deepcopy(z); zz[field] = value; self.rejects(metadata, zz, va.CFG['title'])

    def test_sizes(self):
        sizes([1]); self.rejects(sizes, [90_000_000]); self.rejects(sizes, [80_000_000] * 7); self.rejects(sizes, [])

    def test_compression(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'x.xz'; p.write_bytes(lzma.compress(b'x'))
            r = dict(stored_sha256=sha(p), original_sha256=hashlib.sha256(b'x').hexdigest()); compressed(p, r)
            self.rejects(compressed, p, dict(r, original_sha256='0' * 64)); p.write_bytes(b'bad'); self.rejects(compressed, p, r)

    def test_reference_comparator(self):
        a = {'k': 'x', 'n': 3, 'v': [1.0, 2.5e-7], 'p': None, 'ok': True}
        deep_compare(copy.deepcopy(a), a)
        for mutate in [lambda b: b.update(k='y'), lambda b: b.update(n=4), lambda b: b['v'].__setitem__(0, 1.0 + 1e-10),
                       lambda b: b['v'].append(1.0), lambda b: b.pop('p'), lambda b: b.update(p=0.0), lambda b: b.update(ok=1),
                       lambda b: b['v'].__setitem__(1, float('nan'))]:
            b = copy.deepcopy(a); mutate(b); self.rejects(deep_compare, b, a)

    def test_expected_count_gate(self):
        e = read(ROOT / 'expected/paper_values.json')
        for v in ['original', 'patched']:
            r = read(ROOT / f'results/results-{v}.json'); check_expected(r, e[v], v)
            for mutate in [lambda x: x.update(passed=x['passed'] - 1), lambda x: x.update(total=x['total'] + 1),
                           lambda x: x['summary'].pop(0), lambda x: x['summary'][0].update(passed=-1),
                           lambda x: x['failures'].append(dict(id='planted', quantity='planted'))]:
                x = copy.deepcopy(r); mutate(x); self.rejects(check_expected, x, e[v], v)

    def test_bundle_mapping(self):
        proof = {r['stored']: r for r in read(ROOT / 'analysis/compression_proof.json')}
        self.assertEqual(va.bundle_name('app/original/' + va.CFG['page'], proof), 'app-original/' + va.CFG['page'])
        self.assertEqual(va.bundle_name('bench/fix.patch', proof), 'fix.patch')
        self.assertIsNone(va.bundle_name('README.md', proof)); self.assertIsNone(va.bundle_name('data/bundle-provenance.json', proof))

    def test_patch_replay_detects_drift(self):
        va.patch_replay()
        with tempfile.TemporaryDirectory() as d:
            copy_dir = Path(d) / 'patched'; shutil.copytree(ROOT / 'app/patched', copy_dir); va.patch_replay(copy_dir)
            page = copy_dir / va.CFG['page']; page.write_bytes(page.read_bytes() + b'<!-- drift -->'); self.rejects(va.patch_replay, copy_dir)
            page.unlink(); self.rejects(va.patch_replay, copy_dir)

    def test_eol_record(self):
        eol = va.eol_record(); rel = next(iter(eol)); p = ROOT / rel
        self.assertEqual(va.bundle_digest(p, rel, {}, eol), eol[rel])
        with tempfile.TemporaryDirectory() as d:
            q = Path(d) / 'x'; raw = p.read_bytes()
            q.write_bytes(raw.replace(va.LF, va.CRLF)); self.rejects(va.bundle_digest, q, rel, {}, eol)
            q.write_bytes(raw + b'x'); self.rejects(va.bundle_digest, q, rel, {}, eol)

    def test_fresh_run_gates(self):
        import json, run_checks as rc
        e = read(ROOT / 'expected/paper_values.json')
        with tempfile.TemporaryDirectory() as d:
            w = Path(d)
            for src in ['data/corpus.json', 'data/row-ledger.csv', 'results/reference.json', 'results/metafor-crosscheck.json']:
                shutil.copyfile(ROOT / src, w / Path(src).name)
            rc.fresh_corpus(w); rc.fresh_reference(w, e)
            corpus = read(w / 'corpus.json'); corpus[0]['studies'][0]['y'][0] += 1e-9
            (w / 'corpus.json').write_text(json.dumps(corpus), encoding='utf-8'); self.rejects(rc.fresh_corpus, w)
            shutil.copyfile(ROOT / 'data/corpus.json', w / 'corpus.json')
            (w / 'row-ledger.csv').write_text((ROOT / 'data/row-ledger.csv').read_text(encoding='utf-8').replace('accepted', 'omitted', 1), encoding='utf-8')
            self.rejects(rc.fresh_corpus, w)
            ref = read(w / 'reference.json'); ref[0]['mu'][0] *= 1 + 1e-8
            (w / 'reference.json').write_text(json.dumps(ref), encoding='utf-8'); self.rejects(rc.fresh_reference, w, e)
            ref = read(ROOT / 'results/reference.json'); ref[0]['status'] = 'refused'
            (w / 'reference.json').write_text(json.dumps(ref), encoding='utf-8'); self.rejects(rc.fresh_reference, w, e)
            shutil.copyfile(ROOT / 'results/reference.json', w / 'reference.json')
            x = read(w / 'metafor-crosscheck.json'); x['logLik'] += 1e-6
            (w / 'metafor-crosscheck.json').write_text(json.dumps(x), encoding='utf-8'); self.rejects(rc.fresh_reference, w, e)

    def test_versions_refused(self):
        rscript = os.environ.get('RSCRIPT') or shutil.which('Rscript')
        if not rscript:
            self.skipTest('Rscript not available')
        script = "source('analysis/versions.R'); x <- REQUIRED; x[['mvmeta']] <- '0.0.0'; check_versions(x)"
        p = subprocess.run([rscript, '--vanilla', '-e', script], cwd=ROOT, capture_output=True, text=True)
        self.assertNotEqual(p.returncode, 0); self.assertIn('Wrong R/package versions', p.stderr)
        p = subprocess.run([rscript, '--vanilla', '-e', "source('analysis/versions.R'); check_versions(REQUIRED)"], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)

if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Safeguards)
    r = unittest.TextTestRunner(verbosity=2).run(suite)
    if not r.wasSuccessful():
        raise SystemExit(1)
    print(f'SAFEGUARDS PASS: {r.testsRun} test groups; planted defects rejected ({len(r.skipped)} skipped)', flush=True)
