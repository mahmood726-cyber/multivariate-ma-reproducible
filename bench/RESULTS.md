# Multivariate meta-analysis validation

Source commit: `acd363fa33f0decd2fcafcf08814f663bb9d6178`. The source checkout was not edited, committed or pushed. [fix.patch](fix.patch) applies only to the page, its shared statistical engine and its existing parity fixture.

Original: **18591/18684 checks pass**. Patched: **18682/18682 checks pass**.

These totals include numerical comparisons, exact input membership, accessor consistency, displayed strings, generated SVG geometry and focused invalid-input checks. They are not counts of independent statistical experiments. One invalid covariance configuration is a refusal check, not numerical parity. The two extra original checks come from the extra study point accepted by the malformed-number probe. Browser rendering was not tested.

## Coverage and data

The installed data catalog was enumerated programmatically: 6 mvmeta, 12 mixmeta and 114 metadat candidates, **132 total**. **22 datasets supply 92 unique configurations**; 110 are excluded with schema-specific reasons in [dataset-ledger.csv](dataset-ledger.csv). Aliases and duplicated data in different packages remain distinct candidates. [inventory.json](inventory.json) captures every candidate schema and installed documentation is archived in documentation/.

All pairs of outcomes from applicable multivariate vectors are included. The page has two numeric outcome columns and no subset selector; larger vectors are therefore tested as every unordered pair. It offers only REML, unstructured between-study covariance and explicit within-study covariance. There is no estimator, single-rho or correlation-matrix selector. Covariance inputs here are the supplied matrices or **all applicable numerical assumptions in the installed examples**: p53 rho=.95; Kalaian rho=.66; DBS/Ishak AR1=.97 (and zero for the mixmeta example); gliomas AR1=.61 and zero. These are external data-construction recipes, not claimed page controls or an exhaustive sweep over continuous covariance inputs.

The corpus contains 2,093 study rows across configurations; 1,209 satisfy the page's complete-pair numeric rule and 884 are omitted. These are repeated row/configuration counts, not distinct studies. Accepted corpus sizes range from 2 to 31; a separate 2,001-study probe checks the absence of a study-count cap. [row-ledger.csv](row-ledger.csv) records every accepted/omitted row and reason, and [configuration-ledger.csv](configuration-ledger.csv) records recipes, counts and input hashes. Missing either outcome, a variance or covariance removes the entire row. The R fit deliberately uses exactly those complete pairs; this is **not** validation of a partially observed mvmeta analysis.

Stored effects and variances are used where present. Hyp stores SEs: variances are SE squared and covariance is rho times both SEs. Fine uses metafor::escalc OR with its default zero-only .5 correction and the installed Trikalinos–Olkin covariance equations. Both the raw and the installed example's full-matrix .08 ridge inputs are separate recipes; no app-side ridge was added. The raw month18/month24 configuration contains an invalid covariance and must be refused. Craft uses metafor::rcalc and all 15 outcome pairs. The single covariance accepted by the page is canonicalized from the upper triangle before serialization; this removes rcalc's few-ulp triangle asymmetry without changing the supplied scalar. Kearon and Rivera use logit sensitivity/specificity from disjoint disease/non-disease samples, zero within-study covariance, and metafor::escalc PLO with .5 added to all cells. Smoking retains the package's documented pseudo-reference-arm augmentation; its extreme variances are not silently trimmed.

The inclusion rule requires a paired outcome/coefficient vector and supplied or documented constructible sampling covariance. For example, Riley has two survival outcomes but no known covariance or numerical correlation assumption in the installed example, so it is explicitly excluded. Multiple marginal binary endpoints alone do not identify joint covariances. Pure multilevel collections, arbitrary new first-stage constructions, and single-endpoint network data without a supplied common vector are excluded; they are not claimed validated.

## Model and exposed quantities

For each accepted study, y_i is a two-vector and S_i contains the two variances and supplied covariance. The model is y_i ~ N(mu, S_i + G). G is an unstructured positive-semidefinite matrix; conditional mu and its covariance are GLS. The original engine uses raw lower-Cholesky parameters and two Nelder–Mead runs: 2,000 iterations at simplex step .05, then 1,000 at .005. There is no explicit convergence flag or optimizer tolerance in the original; its opts argument is unused. There are no ML, fixed, moments, Knapp–Hartung, Q, I2, z-test or p-value outputs. Such absent outputs receive no pass counts.

The page displays k, REML log-likelihood (3 decimals), two pooled means and normal marginal 95% CIs (3 decimals), two between-study SDs (4 decimals), and the between-study correlation (3 decimals). The normal quantile is 1.959963984540054. It draws study points, a pooled diamond, and an 81-vertex joint 95% ellipse based on muVcov and chi-square(2)'s .95 quantile. This ellipse is different from two marginal intervals.

There are **no download/export controls**. `_almLastMultivariate()` exposes schema, k, mu, muSE, G, rho and logLik; the runner records its actual result and compares it exactly with the observed engine return. muVcov is captured from the actual engine call. Displayed strings are checked against accessor/engine numbers at their shown precision. No imaginary CSV/JSON download or p-value comparison is counted.

The patch preserves that model and output schema. It validates finite conformable symmetric positive-definite within-study matrices, uses the exact constrained REML solution for k=2, and confirms an exact G=0 boundary with the covariance score and profile objective before reporting correlation as undefined. At rank-one boundaries it refines the two identifiable directions using the analytic profile gradient and a central-difference Hessian (step 1e-4*max(1,abs(parameter)), at most 12 steps, gradient stop 1e-10, backtracking through 1/1024). It accepts only gradient improvement without objective deterioration beyond 1e-12*max(1,abs(objective)). The two simplex caps remain; an early stop requires normalized parameter spread below 1e-10 and objective spread below 1e-12*max(1,abs(objective)). There is no claim of a global optimum certificate for arbitrary inputs.

## R reference and tolerances

R 4.6.0; mvmeta 1.0.3, mixmeta 1.2.2, metafor 5.2.1, metadat 1.6.0, jsonlite 2.0.0. Every R script prints R version, .libPaths() and these versions. Logs retain startup locale warnings; portable library placeholders replace machine paths. At most one R process was running for this job.

The primary fit is mvmeta::mvmeta(Y~1, S, method="reml", bscov="unstr"), analytic-gradient BFGS with maxit=10,000 and reltol=1e-13. Four app-independent initializations are evaluated (package default plus diagonal moment starts at scales 1, .1 and 10), choosing the highest converged likelihood. There are 91 successful fits with no fit warnings. A separate positive-definite-input gate identifies the remaining invalid configuration; it is not a package convergence failure.

mvmeta's REML log-likelihood omits metafor's +.5 log|X'X| constant. With two balanced outcomes X'X=diag(k,k), so **log(k)** is added. Installed `remlprof.fn` and the app source document this adjustment. The same REML/UN parametrization is cross-checked with metafor::rma.mv on Berkey using outcome indicators and random outcome|study. Final nlminb controls are rel.tol=1e-10, x.tol=1e-10, iter.max=10,000 and eval.max=20,000; the cross-check passes all quantities.

Boundary adjudication is explicit in reference.json, with raw mvmeta values retained. Eleven fits have a positive-semidefinite covariance score at G=0 and an installed-package profile likelihood at least as high to numerical precision. They use exact G=0 and package fixed-effects GLS at that boundary. Four configurations have k=2: for d=y1-y2 and q=d'(S1+S2)^(-1)d, the constrained REML solution is G=.5*max(1-1/q,0)*dd'. This follows by whitening the single REML difference. Package GLS and `remlprof.fn` evaluate this covariance; it avoids accepting an arbitrary correlation at zero or a poorly resolved covariance in a flat likelihood. The raw BFGS outputs are not silently treated as exact. No R package was patched.

Iterative quantities use abs(app-ref)/max(1,abs(ref)) <=1e-6; the exact two-study quantities use 1e-9. SVG algebraic checks use 1e-9. Counts, input membership, refusals, schema and displayed/accessor strings are exact. Undefined correlation is explicitly checked as null, not omitted or numerically compared. There are no p-values to which the requested 1e-9 absolute tolerance can be applied. No relaxed flat-likelihood variance tolerance was used.

The initial harness had an R list-to-matrix decoding error, fixed before final comparison; the initial log is retained. Tightening nlminb to 1e-12 caused a convergence failure, and default finite-difference BFGS was less accurate on Berkey. [diagnose_reference.log](diagnose_reference.log) records the optimizer investigation; the final nlminb result and independent mvmeta fit agree. The raw initial files are diagnostics only and excluded from pass counts.

## Faults and app-only changes

1. **Incorrect Berkey example and parity fixture** — multivariate-ma/index.html:69–73 and hub/shared/tests/multivariate-ma-parity.spec.mjs:20. AL variances were copied from covariance values. All installed aliases give .0077, .0008, .0014, .0015, .0304. The original example and test agree with each other on the wrong dataset. Both are corrected; the untouched default page result is now checked against installed Berkey data.
2. **Arbitrary boundary correlation / weak covariance precision** — shared/multivariate-ma.js:110 and :121. Dividing tiny approximate variances produces meaningless rho when G=0; a redundant Cholesky direction also hides residual gradient on rank-one boundaries. Exact k=2, score-confirmed zero boundaries and rank-one refinement repair these defects.
3. **Invalid covariance acceptance and stale results** — shared/multivariate-ma.js:84 and multivariate-ma/index.html:101. Positive diagonal entries alone do not establish a valid covariance. The patch validates the matrix, clears previous output before fitting, catches errors and displays their reason.
4. **Malformed numeric acceptance** — multivariate-ma/index.html:88. parseFloat accepts `.1oops`; strict nonblank Number conversion rejects it. Existing complete-row omission behavior is retained and explained in the page.
5. **Double-escaped outcome names** — multivariate-ma/index.html:105–109. Callers escaped names and card escaped them again. Names are now escaped once.
6. **Clipped confidence ellipse** — multivariate-ma/index.html:116–128. Plot limits used study/pooled points only. Limits now include analytic ellipse extrema; the joint quantile uses sqrt(-2 log(.05)).

Before/after examples (full-precision evidence is saved in the JSON captures):

| Quantity / case | Original | Required / R | Patched |
|---|---:|---:|---:|
| Default Berkey mu[AL] | -0.35675435789045523 | -0.33921517838083126 | -0.3392151787432598 |
| Default Berkey logLik | 3.751802206426391 | 3.691767694370326 | 3.691767694370328 |
| Smoking B/D G[1,1] | 0.0582707158024849 | 0.05826371767185507 | 0.05826371767185508 |
| Gliomas month6/month18 rho | 0.8363270432429618 | undefined | undefined |
| Malformed-number probe accepted k | 4 | 3 | 3 |
| Ellipses wholly inside plot | 79/101 | 101/101 | 101/101 |
| Invalid covariance corpus configuration | fitted | refuse with reason | refused |

## Per-quantity results

All errors use the scale described above. Groups mixing the exact two-study and iterative cases show the maximum allowed tolerance here; checks-*.json records the individual tolerance.

| Quantity | Original pass/checks | Patched pass/checks | Patched maximum error | Maximum tolerance |
|---|---:|---:|---:|---:|
| G | 360/368 | 368/368 | 9.511508350246048e-07 | 1e-06 |
| accessor_G | 404/404 | 404/404 | 0.0 | 0 |
| accessor_k | 101/101 | 101/101 | 0.0 | 0 |
| accessor_logLik | 101/101 | 101/101 | 0.0 | 0 |
| accessor_mu | 202/202 | 202/202 | 0.0 | 0 |
| accessor_muSE | 202/202 | 202/202 | 0.0 | 0 |
| accessor_rho | 101/101 | 80/80 | 0.0 | 0 |
| accessor_rho_undefined | 0/0 | 21/21 | exact | 0 |
| api_refusal | 1/4 | 4/4 | exact | 0 |
| app_keys | 1/1 | 1/1 | exact | 0 |
| app_unique | 1/1 | 1/1 | 0.0 | 0 |
| ciLower | 178/182 | 182/182 | 5.998911670745954e-07 | 1e-06 |
| ciUpper | 178/182 | 182/182 | 3.6194876552008734e-07 | 1e-06 |
| default_G | 0/4 | 4/4 | 4.2676489425685915e-10 | 1e-06 |
| default_logLik | 0/1 | 1/1 | 4.811670144112978e-16 | 1e-06 |
| default_mu | 0/2 | 2/2 | 5.247288159537788e-10 | 1e-06 |
| default_muSE | 0/2 | 2/2 | 5.120643908895772e-10 | 1e-06 |
| default_rho | 0/1 | 1/1 | 1.1617607986735834e-08 | 1e-06 |
| display_cards | 101/101 | 101/101 | exact | 0 |
| display_headline | 101/101 | 101/101 | exact | 0 |
| ellipse_in_viewport | 79/101 | 101/101 | exact | 0 |
| ellipse_mahalanobis | 8100/8100 | 8100/8100 | 5.549387613004089e-12 | 1e-09 |
| ellipse_vertices | 101/101 | 101/101 | 0.0 | 0 |
| fit_status | 91/91 | 91/91 | exact | 0 |
| focused_k | 9/10 | 10/10 | 0.0 | 0 |
| input_membership | 92/92 | 92/92 | exact | 0 |
| k | 91/91 | 91/91 | 0.0 | 0 |
| logLik | 92/92 | 92/92 | 1.6891094949231962e-13 | 1e-06 |
| m | 91/91 | 91/91 | 0.0 | 0 |
| mu | 182/184 | 184/184 | 4.210983436392368e-07 | 1e-06 |
| muSE | 180/184 | 184/184 | 1.8437970997880654e-07 | 1e-06 |
| muVcov | 356/364 | 364/364 | 4.1485234358260214e-07 | 1e-06 |
| outcome_labels | 0/1 | 1/1 | exact | 0 |
| plot_study_coordinate | 6436/6436 | 6434/6434 | 1.0799858638444551e-14 | 1e-09 |
| plot_study_count | 101/101 | 101/101 | 0.0 | 0 |
| reference_keys | 1/1 | 1/1 | exact | 0 |
| reference_unique | 1/1 | 1/1 | 0.0 | 0 |
| refusal | 0/1 | 1/1 | exact | 0 |
| rho | 77/79 | 79/79 | 1.054125782218307e-07 | 1e-06 |
| rho_undefined | 0/13 | 13/13 | exact | 0 |
| schema | 101/101 | 101/101 | exact | 0 |
| sd | 174/182 | 182/182 | 4.6489600609662455e-07 | 1e-06 |
| svg_finite | 101/101 | 101/101 | exact | 0 |
| ui_refusal | 2/4 | 4/4 | exact | 0 |
| valid_capture | 101/101 | 101/101 | exact | 0 |

Separate count groups (overlapping only where stated; overall total is the comparator output):

- corpus_numerical: original 1949/2002; patched 2002/2002.
- corpus_configurations: original 91/92; patched 92/92.
- focused: original 4972/4988; patched 4986/4986.
- default_example: original 0/10; patched 10/10.
- metafor_crosscheck: original 10/10; patched 10/10.

## Execution, replay and limits

The permitted pure-JavaScript route was used: Node v24.13.0 and linkedom, executing every external script and the complete inline page script. The fit wrapper only records actual arguments and returns. Original source is unchanged; the patched snapshot differs only by fix.patch. No independent JavaScript statistical engine is used as the oracle. An isolated diagnostic probe exposed the original profile function to inspect its gradient; it is not the page evidence or comparison oracle.

The captures verify parsed DOM text, generated SVG, actual numerical return/accessor values and refusal behavior. They do not verify Edge layout, CSS rasterization, screen-reader behavior, keyboard navigation, browser performance or native download interactions. The existing Playwright fixture was corrected but not executed in a browser; the full page and its default example were executed in Node. Shared build-info.js carries embedded SHA 7899ce599bfdedecd4d13b8f35540d129906fb95, older than the checkout; source-manifest.json records the actual audited commit and file hashes.

Run commands, from the validation directory (library/executable locations can be supplied through RSCRIPT, AUDIT_R_LIBS_USER and AUDIT_R_LIBS):

```text
python run_r.py inventory.R
python setup.py
python run_r.py corpus.R
python run_r.py reference.R
python run_r.py crosscheck.R
node run_node.cjs original
python patch_app.py
node run_node.cjs patched
python compare.py original
python compare.py patched
python ledgers.py
python report.py
python verify_archive.py
```

setup.py is only for a source checkout plus the local predecessor dependencies. The archive already contains app snapshots and offline node_modules, so replay starts at corpus/reference or directly at run_node. patch_app.py reconstructs patched files from original snapshots, and fix.patch is independently replay-checked. The original full page capture remains valid after upper-triangle canonicalization because its input text is byte-for-byte unchanged; verification reconstructs and checks that text for both runs. No configurations or failures were discarded to obtain a pass.

Verbatim final output lines:

```text
CORPUS 92 configurations from 22 datasets
REFERENCE 92 configurations; 91 fits; boundary adjudication recorded
METAFOR CROSSCHECK: REML UN converged; logLik 3.6917676943703217
APP original: 92 configurations; 18 focused cases; no download controls exist
APP patched: 92 configurations; 18 focused cases; no download controls exist
18591/18684 checks pass
18682/18682 checks pass
```

Included dataset/configuration counts:

| Package | Dataset | Configurations |
|---|---|---:|
| mvmeta | berkey98 | 1 |
| mvmeta | fibrinogen | 6 |
| mvmeta | hsls | 3 |
| mvmeta | hyp | 1 |
| mvmeta | p53 | 1 |
| mvmeta | smoking | 3 |
| mixmeta | berkey98 | 1 |
| mixmeta | fibrinogen | 6 |
| mixmeta | hsls | 3 |
| mixmeta | hyp | 1 |
| mixmeta | p53 | 1 |
| mixmeta | smoking | 3 |
| mixmeta | dbs | 12 |
| metadat | dat.ishak2007 | 6 |
| mixmeta | gliomas | 12 |
| metadat | dat.berkey1998 | 1 |
| metadat | dat.berkey1998r | 1 |
| metadat | dat.kalaian1996 | 1 |
| metadat | dat.fine1993 | 12 |
| metadat | dat.craft2003 | 15 |
| metadat | dat.kearon1998 | 1 |
| metadat | dat.rivera2025 | 1 |
