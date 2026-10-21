from pathlib import Path
import json,csv,collections,hashlib,re,subprocess
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
original=read('results-original.json');patched=read('results-patched.json');C=read('corpus.json');R=read('reference.json');A={x['id']:x for x in read('app-original.json')};B={x['id']:x for x in read('app-patched.json')}
manifest=read('source-manifest.json')
test='hub/shared/tests/multivariate-ma-parity.spec.mjs'
if not any(x['path']==test for x in manifest['files']):manifest['files'].append(dict(path=test,sha256=hashlib.sha256(Path('app-original',test).read_bytes()).hexdigest()))
Path('source-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
allchecks={v:read(f'checks-{v}.json') for v in ['original','patched']}
numerical={'mu','muSE','muVcov','G','rho','rho_undefined','logLik','ciLower','ciUpper','sd','k','m'}
counts={v:{'total':len(x),'passed':sum(y['passed'] for y in x)} for v,x in allchecks.items()}
for v,x in allchecks.items():
 for group,sel in [('corpus_numerical',lambda c:c['id'].startswith(('mvmeta::','mixmeta::','metadat::')) and c['quantity'] in numerical),('corpus_configurations',lambda c:c['quantity'] in {'fit_status','refusal'}),('focused',lambda c:c['id'].startswith('focused::')),('default_example',lambda c:c['id']=='built-in-Berkey'),('metafor_crosscheck',lambda c:c['id']=='metafor-crosscheck')]:
  cc=[c for c in x if sel(c)];counts[v][group]={'total':len(cc),'passed':sum(c['passed'] for c in cc)}
stats={'commit':manifest['commit'],'candidate_datasets':132,'included_datasets':22,'excluded_datasets':110,'configurations':len(C),'reference_fits':91,'reference_refusals':1,'rows_across_configurations':sum(len(c['studies']) for c in C),'accepted_rows_across_configurations':sum(len(c['accepted']) for c in C),'counts':counts,'quantities_original':original['summary'],'quantities_patched':patched['summary'],'limitations':['Node/linkedom generated DOM and SVG only; no real browser rendering','Complete-pair analysis only; no partially observed multivariate model','Finite set of supplied/documented covariance inputs, not all possible numeric covariances','Primary oracle boundary adjudication uses installed likelihood and GLS plus exact two-study covariance; raw mvmeta retained']}
Path('results.json').write_text(json.dumps(stats,indent=2)+'\n')
text=f'''# Multivariate meta-analysis validation

Source commit: `{manifest['commit']}`. The source checkout was not edited, committed or pushed. [fix.patch](fix.patch) applies only to the page, its shared statistical engine and its existing parity fixture.

Original: **{original['passed']}/{original['total']} checks pass**. Patched: **{patched['passed']}/{patched['total']} checks pass**.

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
'''
default0=read('runtime-original.json')['defaultUninstrumented'];default1=read('runtime-patched.json')['defaultUninstrumented'];ref=R[0]
examples=[('Default Berkey mu[AL]',default0['mu'][1],ref['mu'][1],default1['mu'][1]),('Default Berkey logLik',default0['logLik'],ref['logLik'],default1['logLik'])]
smoke=next(c['id'] for c in C if c['package']=='mvmeta' and c['dataset']=='smoking' and c['outcomes']==['yB','yD']);rr=next(r for r in R if r['id']==smoke)
examples.append(('Smoking B/D G[1,1]',A[smoke]['output']['G'][1][1],rr['G'][1][1],B[smoke]['output']['G'][1][1]))
zero=next(c['id'] for c in C if c['package']=='mixmeta' and c['dataset']=='gliomas' and c['outcomes']==['month6','month18'] and c['covariance']=='documented-AR1-0')
examples.append(('Gliomas month6/month18 rho',A[zero]['output']['rho'],'undefined',B[zero]['output']['rho']))
for label,a,r,b in examples:text+=f'| {label} | {a} | {r} | {"undefined" if b is None else b} |\n'
text+='''| Malformed-number probe accepted k | 4 | 3 | 3 |
| Ellipses wholly inside plot | 79/101 | 101/101 | 101/101 |
| Invalid covariance corpus configuration | fitted | refuse with reason | refused |

## Per-quantity results

All errors use the scale described above. Groups mixing the exact two-study and iterative cases show the maximum allowed tolerance here; checks-*.json records the individual tolerance.

| Quantity | Original pass/checks | Patched pass/checks | Patched maximum error | Maximum tolerance |
|---|---:|---:|---:|---:|
'''
orig={s['quantity']:s for s in original['summary']}
for s in patched['summary']:
 o=orig.get(s['quantity'],{'passed':0,'checks':0});text+=f"| {s['quantity']} | {o['passed']}/{o['checks']} | {s['passed']}/{s['checks']} | {s['max_error'] if s['max_error'] is not None else 'exact'} | {s['tolerance']} |\n"
text+='\nSeparate count groups (overlapping only where stated; overall total is the comparator output):\n\n'
for group in ['corpus_numerical','corpus_configurations','focused','default_example','metafor_crosscheck']:
 x=counts['original'][group];y=counts['patched'][group];text+=f"- {group}: original {x['passed']}/{x['total']}; patched {y['passed']}/{y['total']}.\n"
text+='''
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
'''
text+=Path('comparison-original.txt').read_text().splitlines()[-1]+'\n'+Path('comparison-patched.txt').read_text().splitlines()[-1]+'\n```\n'
text+='\nIncluded dataset/configuration counts:\n\n| Package | Dataset | Configurations |\n|---|---|---:|\n'
for (pkg,nm),n in collections.Counter((c['package'],c['dataset']) for c in C).items():text+=f'| {pkg} | {nm} | {n} |\n'
Path('RESULTS.md').write_text(text,encoding='utf-8')
Path('README.md').write_text('''# P18 validation archive

Read RESULTS.md for findings, strict counts and limitations. results.json provides machine-readable totals; dataset-, configuration-, row- and refusal-ledger.csv provide coverage and reasons.

app-original/ contains the audited source snapshots. app-patched/ contains proposed repairs; fix.patch is a unified diff against the source tree. node_modules/ supplies the offline linkedom runtime and dependency licenses. Run `node run_node.cjs original`, `node run_node.cjs patched`, then both `python compare.py` variants to replay against the stored R reference. For a full reference rebuild, configure RSCRIPT and the two AUDIT_R_LIBS environment variables and run corpus.R, reference.R and crosscheck.R through run_r.py, sequentially. Scripts use relative paths. Do not run setup.py against the finished archive: it is a source-ingest helper and the snapshots/dependencies are already present.

documentation/ contains installed help and reference-function snapshots. Initial reference files and diagnose_reference.* are diagnostic history, not pass evidence. The primary references are reference.json and metafor-crosscheck.json. No p-values, Q, I2 or file-download outputs exist in this page. Browser layout was not tested.

verify_archive.py verifies exact key coverage, numerical finiteness, membership, source hashes, patch replay, artifact checksums and absence of machine-specific paths, and creates P18-validation.zip with a P18-validation/ root. TASK.md inside the archive is a portable transcription of the original task with local installation paths replaced by placeholders; the user's original local TASK.md is preserved outside the archive. codex.log and RUN.json are execution-environment files and are intentionally excluded.
''',encoding='utf-8')
print(f"REPORT: original {original['passed']}/{original['total']}; patched {patched['passed']}/{patched['total']}; 92 configurations")
