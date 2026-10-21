# Multivariate (bivariate) meta-analysis in the browser: validation against the R packages mvmeta and metafor

Validated page: the allmeta `multivariate-ma` app at source commit `acd363fa33f0decd2fcafcf08814f663bb9d6178` (app/original; the six page files are byte-identical to allmeta release v1.7.0) and that commit plus `bench/fix.patch` (app/patched). Upstream repository: https://github.com/mahmood726-cyber/allmeta. At archive build time the fixes were not merged upstream; the archived app outputs are those of the acd363f snapshot and its patch, not of later code. The patched engine is that of pull request #154 at commit `1b9b9327d75262b9ff8c32ecc5d6414c264071d6` (merge `85f328c`), and the corrected-page tier (18682/18682) is validated and cited at that commit. Release containing the fixes and the plus panel: allmeta v1.8.0 (tag commit `1cb3f8409c7af75ed41f7e1811f9c502f900fc79`), DOI 10.5281/zenodo.23515177. v1.8.0 also changed the engine and the output schema through pull request #152; `RELEASE_EQUIVALENCE.md` records what was re-executed on the v1.8.0 bytes (plus tiers and round trip: equivalent; corrected-page tier: 18581/18682, every failure the output-schema version).

## What is validated

The page fits one model: two outcomes per study, y_i ~ N(mu, S_i + G), where S_i is the supplied 2 x 2 within-study covariance (two variances and one covariance per row) and G is an unstructured between-study covariance estimated by REML. It displays k, the REML log-likelihood, the two pooled means with normal 95% confidence intervals, the two between-study SDs, the between-study correlation, and a study scatter with the pooled point and a joint 95% confidence ellipse. Rows missing an outcome, a variance or the covariance are omitted (complete pairs only). The page offers no other estimator (no ML, method of moments or fixed effect), no assumed-correlation control, no more than two outcomes, no Q, I-squared, z or p-values and no download controls; none of these is checked.

Reference: **R 4.6.0, mvmeta 1.0.3** (`mvmeta(Y ~ 1, S, method = "reml", bscov = "unstr")`, BFGS with maxit 10000 and reltol 1e-13, best of four app-independent starts), with mixmeta 1.2.2 and metadat 1.6.0 data and a metafor 5.2.1 `rma.mv(struct = "UN", method = "REML")` cross-check on Berkey. mvmeta's REML log-likelihood omits metafor's 0.5 log|X'X| constant; log(k) is added for two balanced outcomes. Boundary fits are adjudicated explicitly (`results/reference.json`, field `adjudication`): 11 fits at G = 0 confirmed by the covariance score and the installed profile likelihood, and 4 two-study fits using the exact constrained REML solution.

Corpus: all 132 candidate datasets in mvmeta, mixmeta and metadat enumerated (`data/dataset-ledger.csv`); **22 datasets give 92 configurations** (every outcome pair of each applicable multivariate vector; covariance from the supplied matrices or the installed examples' documented assumptions), 2,093 study rows across configurations of which 1,209 are complete pairs (`data/row-ledger.csv`). One configuration (dat.fine1993 month18 + month24, raw covariance) has an invalid within-study covariance and must be refused. Plus 18 focused probes (invalid input, malformed numbers, escaping, two studies, a 2,001-study no-cap probe, engine API refusals) and the page's built-in Berkey example.

Comparison of the page's own JavaScript (Node.js v24.13.0 with linkedom 0.18.12, all shipped scripts executed): original **18591/18684 checks pass**, patched **18682/18682 checks pass**. Tolerances: abs(app - ref)/max(1, abs(ref)) at most 1e-6 for iterative REML quantities, 1e-9 for the exact two-study fits and SVG geometry; counts, input membership, refusals, schema and displayed strings exact.

## Reproduce

Requirements: R 4.6.0 with exactly mvmeta 1.0.3, mixmeta 1.2.2, metafor 5.2.1, metadat 1.6.0 and jsonlite 2.0.0; Python 3 (standard library only); git (for the patch replay in the verifier). No package is installed and no network access is needed. Set `R_LIBS_USER` / `R_LIBS` to the libraries holding those versions and `R_ENVIRON_USER` to an empty file (`NUL` on Windows). From the archive root:

```text
Rscript validate.R
python analysis/verify_archive.py
python analysis/test_safeguards.py
```

`validate.R` prints `.libPaths()` and every package version and refuses to run on any version difference; SHA-256 checks the complete inventory in `SOURCE_SHA256.json`; then, in one R process, **rebuilds the corpus from the installed package data, refits all 92 configurations with mvmeta and repeats the metafor cross-check**, with no archived corpus or fit reused. `analysis/run_checks.py` requires the rebuilt corpus and row ledger to equal `data/`, the fresh fits to reproduce `results/reference.json` within 1e-10, then compares the archived page outputs with the **fresh** R values using the bundle's comparison code (`analysis/compare_archive.py`, which differs from `bench/compare.py` only in file paths; see `analysis/compare_archive.diff`), requires every per-quantity count and the exact list of failing checks to equal `expected/paper_values.json`, and exits nonzero on any failure. An existing `.validate-work/` is refused so a stale result cannot pass. The final lines are:

```text
Original (released page, expected failures): 18591/18684 checks pass - per-quantity counts and the 93 failing checks match expected/paper_values.json
Runtime: ... seconds
18682/18682 checks pass
```

From a fresh clone on the 4-core Windows validation node (R 4.6.0, Python 3.13) the complete `validate.R` run took 28.7 seconds. A planted 1e-5 relative change to one archived patched-page mean (with its hash re-pinned) makes it fail with exit status 1.

`verify_archive.py` checks the inventory, that every carried-over file is byte-identical to the validation bundle's own manifest (`bench/bundle-archive-manifest.json`, via a recorded reversible CRLF-to-LF normalization), that `app/original` matches the upstream hashes in `app/source-manifest.json`, that `app/original` plus `bench/fix.patch` reproduces `app/patched` byte for byte, keyed coverage, text hygiene and metadata. `test_safeguards.py` plants a defect for each gate and requires it to be rejected.

## Faults found and fixed

| Fault (original page) | Location | Case | Original | Required / R | Patched |
|---|---|---|---:|---:|---:|
| Built-in Berkey example (and its parity test) used covariance values as the AL variances | `multivariate-ma/index.html`, `hub/shared/tests/multivariate-ma-parity.spec.mjs` | default example, mu[AL] | -0.35675435789045523 | -0.33921517838083126 | -0.3392151787432598 |
| Same | same | default example, logLik | 3.751802206426391 | 3.691767694370326 | 3.691767694370328 |
| Arbitrary correlation at the G = 0 boundary; weak precision on rank-one boundaries | `shared/multivariate-ma.js` | gliomas month6 + month18, rho | 0.8363270432429618 | undefined | undefined |
| Same | same | smoking B + D, G[1,1] | 0.0582707158024849 | 0.05826371767185507 | 0.05826371767185508 |
| Invalid (not positive definite) within-study covariance accepted; stale results not cleared | `shared/multivariate-ma.js`, `multivariate-ma/index.html` | dat.fine1993 month18 + month24 (raw) | fitted | refuse with reason | refused |
| Malformed numbers accepted by prefix parsing (`.1oops`) | `multivariate-ma/index.html` | malformed-number probe, k | 4 | 3 | 3 |
| Outcome names escaped twice | `multivariate-ma/index.html` | escaped-outcome probe, labels | double-escaped | escaped once | escaped once |
| Confidence ellipse clipped by the plot range | `multivariate-ma/index.html` | ellipses wholly inside the plot | 79/101 | 101/101 | 101/101 |

Per-quantity before/after counts are in `results/comparison-*.txt` and `expected/paper_values.json`; the narrative and every fault's root cause are in `bench/RESULTS.md`. The patch keeps the model and the output schema.

## Limits

- Two outcomes only, REML only, unstructured G only, complete pairs only: partially observed studies are omitted, not modelled, so this is not a validation of a partially observed mvmeta analysis. No ML, method-of-moments or fixed-effect fit exists in the page and none is validated.
- Covariances for p53, Kalaian, DBS, Ishak, gliomas, Fine, Craft, Kearon and Rivera are constructed from the installed examples' documented assumptions; they are data-construction recipes for testing, not page controls and not an exhaustive sweep. Corpus configurations are software tests, not clinical or scientific analyses.
- App outputs were captured by running the page in a Node VM with linkedom; browser layout, CSS rendering, accessibility and performance are **unverified, not passes**. `validate.R` re-runs R, not the page; the page observations are archived. The Node runner's third-party modules are not redistributed (identity recorded in `data/bundle-provenance.json`).
- The patched optimizer has no global-optimum certificate for arbitrary inputs; agreement is shown on this corpus.
- Only R 4.6.0 with the listed package versions was used; other versions are refused rather than assumed equivalent.

| Item | Static | Dynamic / source-backed |
|---|---|---|
| Rules | REML/UN model, tolerances, page semantics | Fresh mvmeta refit and metafor cross-check |
| Corpus | Archived corpus and ledgers | Rebuilt from installed package data and required identical |
| Findings | Expected per-quantity counts and failing checks | Recomputed comparison against fresh fits |
| Provenance | Source commit, fix.patch, bundle zip SHA-256 | Inventory, bundle-manifest identity, patch replay |

## Layout

`app/` holds the original and patched page snapshots (page, shared engine, build info, stylesheet, landmark script and the parity test), `app-sha256.json`, the upstream `source-manifest.json` and the allmeta licence. `data/` holds the corpus, the dataset, configuration, row and refusal ledgers, the dataset inventory and `bundle-provenance.json`. `results/` holds the archived page captures (corpus, focused probes, runtime records), the archived mvmeta reference and metafor cross-check, the comparison outputs and the xz-compressed per-check records. `expected/paper_values.json` pins the counts. `bench/` keeps the validation bundle's own scripts, logs, `RESULTS.md`, `fix.patch` and installed package documentation (GPL-licensed upstream text). `analysis/` holds the fresh-refit, comparison, verifier and safeguard code. `RELEASE_EQUIVALENCE.md` and `release-equivalence/` record the re-execution on the allmeta v1.8.0 bytes (logs, runner diffs, the v1.8.0 corrected-page comparison and the value-by-value capture difference). MIT applies to the archive tooling.

## Plus layer (comparison and within-study-correlation sensitivity panel)

`plus/` archives the allmeta multivariate-ma plus panel and its R checks: the page source at commit
d0892228c2c0af009ca5270cfc8eb73ffa12eb31 (branch feat/multivariate-ma-plus, draft pull request #152, which merges the
v1 fix of pull request #154; byte-identical git blobs, `plus/source-manifest.json`). Pull request #152 was merged
(f2faaa5) into allmeta v1.8.0; the plus page outputs were re-captured on the v1.8.0 bytes and are byte-identical to
`plus/app-plus.json` (`RELEASE_EQUIVALENCE.md`).

`Rscript validate.R` now ends by sourcing `validate_plus.R` (also runnable on its own) in the same R process, after the
same fail-closed version check and SHA-256 inventory:
1. rebuilds the plus corpus from the fresh v1 corpus (`plus/source/multivariate-ma/validate/make_plus_corpus.py`) and
   requires it to be byte-identical to the archived plus corpus;
2. refits the plus R reference from scratch with the source commit's own `generate-plus.R` (mvmeta 4 starts, then
   nlminb, then a Newton polish on mvmeta's analytic REML gradient; metafor `rma` per outcome; `rma.mv` on Berkey) for
   92 configurations x (supplied covariance + 19 rho_w values): 1,839 bivariate fits, 1 refusal, 184 univariate fits.
   This step takes about 27 minutes;
3. `analysis/run_plus_checks.py` requires the fresh reference to reproduce the archived one within 1e-10, replays the
   archived page outputs (`plus/app-plus.json`) against the fresh R values (1e-6 relative for iterative REML
   quantities, 1e-9 for two-study exact fits and the closed-form p(z) grid, exact statuses, refusal reasons and displayed
   strings), re-compares the archived exported-R-script round trip under the strict allmeta v1.8.0 rule (below), and
   prints `54612/54612 plus checks pass`.

One plus-replay fit passes only by the logLik rule (a boundary case passes iff the page's REML logLik is not more than
1e-8 below R's); it is listed by id in `expected/plus_values.json`, and the run fails if the set changes.

### Exported-R-script round trip (strict rule)

The round trip exports, for 94 cases, the page's own R script (default single-start mvmeta, BFGS, reltol 1e-13, plus
metafor), runs it with Rscript, and compares the R output with the page export (`plus/roundtrip/`). It is scored with
the **strict** comparator of allmeta v1.8.0 (`multivariate-ma/validate/roundtrip-compare.cjs` at 1cb3f84, ported line
for line in `analysis/run_plus_checks.py`): parameters 1e-6 relative to max(1, |R|); a fit whose mu, SE or G differ
more passes those checks only if the page fit is internally consistent (GLS and REML rebuilt from the reported G and the
input covariances) and its recomputed REML logLik is not more than 1e-8 below R's; **z and p are never adjudicated**.

Result (`plus/roundtrip/roundtrip-result.json`, `rt-compare.log`): **29473/29502 checks pass; 29 fail (z 23, p 6) in
16 fits; 64 fits with parameter adjudication.** The 29 failing checks and the 64 adjudicated fits are pinned by id in
`expected/plus_values.json` (`roundtrip`), and the run fails if either set, or any count, changes. The failures are
expected and explained by R, not by the page:
- class a (3 fits, 12 checks): default single-start mvmeta stops at a local maximum whose REML logLik is 0.00383
  below the page's, so R's z and p are those of a worse fit (scaled differences up to 0.0775);
- class b (13 fits, 17 checks): z differs by at most 2.68e-6 (scaled), just above the 1e-6 tolerance, with
  |dlogLik| at most 4.4e-11; the page and R reach the same optimum to optimizer precision.

| # | Fit (`failed[].id`) | Class | Failed checks (quantity: scaled difference) | Max scaled difference | Page REML logLik - R logLik (recomputed) | Parameter-adjudicated |
|---:|---|:-:|---|---:|---:|:-:|
| 1 | `mvmeta::fibrinogen::b2+b3::REML::supplied#rhoW=-0.9` | b | z: 1.18e-06 | 1.18e-06 | 7.6e-12 | no |
| 2 | `mvmeta::fibrinogen::b2+b3::REML::supplied#rhoW=-0.2` | b | z: 2.68e-06, z: 1.22e-06 | 2.68e-06 | 4.37e-11 | no |
| 3 | `mvmeta::fibrinogen::b3+b5::REML::supplied#rhoW=-0.9` | b | z: 1.26e-06 | 1.26e-06 | 2.02e-11 | yes |
| 4 | `mvmeta::hsls::b2+b3::REML::supplied#rhoW=0.7` | b | z: 1.59e-06 | 1.59e-06 | 9.97e-12 | yes |
| 5 | `mixmeta::fibrinogen::b2+b3::REML::supplied#rhoW=-0.9` | b | z: 1.18e-06 | 1.18e-06 | 7.6e-12 | no |
| 6 | `mixmeta::fibrinogen::b2+b3::REML::supplied#rhoW=-0.2` | b | z: 2.68e-06, z: 1.22e-06 | 2.68e-06 | 4.37e-11 | no |
| 7 | `mixmeta::fibrinogen::b3+b5::REML::supplied#rhoW=-0.9` | b | z: 1.26e-06 | 1.26e-06 | 2.02e-11 | yes |
| 8 | `mixmeta::hsls::b2+b3::REML::supplied#rhoW=0.7` | b | z: 1.59e-06 | 1.59e-06 | 9.97e-12 | yes |
| 9 | `mixmeta::dbs::eff_month3+eff_long::REML::documented-AR1-0#rhoW=0.7` | b | z: 1.08e-06 | 1.08e-06 | 4.38e-12 | yes |
| 10 | `mixmeta::dbs::eff_month3+eff_long::REML::documented-AR1-0.97#rhoW=0.7` | b | z: 1.08e-06 | 1.08e-06 | 4.38e-12 | yes |
| 11 | `mixmeta::dbs::eff_month6+eff_long::REML::documented-AR1-0.97#main` | b | z: 1.35e-06, z: 1.35e-06 | 1.35e-06 | 6.97e-12 | yes |
| 12 | `metadat::dat.ishak2007::y1i+y4i::REML::documented-AR1-0.97#rhoW=0.7` | b | z: 1.08e-06 | 1.08e-06 | 4.38e-12 | yes |
| 13 | `metadat::dat.ishak2007::y2i+y4i::REML::documented-AR1-0.97#main` | b | z: 1.35e-06, z: 1.35e-06 | 1.35e-06 | 6.97e-12 | yes |
| 14 | `mixmeta::gliomas::month6+month12::REML::documented-AR1-0#rhoW=0.8` | a | z: 0.0775, p: 0.0168, z: 0.0075, p: 2.33e-06 | 0.0775 | 0.00383 | yes |
| 15 | `mixmeta::gliomas::month6+month12::REML::documented-AR1-0.61#rhoW=0.8` | a | z: 0.0775, p: 0.0168, z: 0.0075, p: 2.33e-06 | 0.0775 | 0.00383 | yes |
| 16 | `metadat::dat.fine1993::month6+month12::REML::documented-covariance-raw#rhoW=0.8` | a | z: 0.0775, p: 0.0168, z: 0.0075, p: 2.33e-06 | 0.0775 | 0.00383 | yes |

Generated from `plus/roundtrip/roundtrip-result.json` and the archived page and R files; dlogLik uses the page logLik
recomputed by the integrity check. No boundary, interior or flat-likelihood classification of these fits is claimed:
none is part of allmeta v1.8.0.

History (superseded, kept for the record): the round trip was first scored with the comparator of the plus source
commit d089222, which adjudicated z and p together with the other parameters on the reported logLik. That gives
29502/29502 with 68 logLik-adjudicated fits (`plus/roundtrip/roundtrip-result.v1rule.json`, `rt-compare.v1rule.log`,
`plus/evidence/roundtrip-rerun/rt-compare.log`). `run_plus_checks.py` re-runs that rule too and requires it to
reproduce the stored history file (`expected/plus_values.json`, `roundtrip_v1rule_history`), but it is not the reported
result.

Evidence recorded in `plus/evidence/`:
- `node-replay/`: whole-page Node.js replay at the source commit, 54612/54612 (`final-evidence-node.json`, `final-node.log`).
- `edge-playwright/`: the same replay and the plus/sanity/parity specs in Microsoft Edge via Playwright (11 passed,
  `MV PLUS 54612/54612`, axe WCAG 2.1 A/AA 0 violations), and the pixel specs (2 passed; references generated in the
  same environment, so not independent).
- `roundtrip-rerun/`: the exported-R-script round trip rerun on the source commit d089222 (94 scripts; `rt.cmd`,
  export and timing logs); its outputs are `plus/roundtrip/`. Its `rt-compare.log` is the superseded-rule history
  (29502/29502, 68 logLik-rule fits); the reported strict result is `plus/roundtrip/rt-compare.log`.
- `k2/`: engine before/after at strict tolerance without the logLik rule (`K2.md`): v1 fix engine 4/2023 fits outside
  tolerance, polish-only engine 4/2023, final multi-start engine 1/2023 (the rank-one craft2003 fit above).
- `PATH_TOKENS.md`: the placeholder tokens that replace machine-specific paths in the recorded `.cmd` files.
- `usability/`: scripted walkthroughs (`v1/`, `v2/`: script, printed log, `walkthrough.json`, screenshots) and axe.
- `figure2/`: the Figure 2 captures (default page data, berkey98) with the displayed text they show.
