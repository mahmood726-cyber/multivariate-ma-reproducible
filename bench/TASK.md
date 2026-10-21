# Job P18 (paper 18): multivariate-ma app vs R (mvmeta / metafor rma.mv) - run on BASEIMAGE

Read ../kit/codex_common3.md first and follow it. Model this job on ../P16 (TASK.md, RESULTS.md, corpus.R, reference.R,
compare.py, ledgers, documentation/, P16-validation.zip layout) and ../kit/codex16 (paper 14 lane): same rigour, same
deliverables, same archive-ready layout. This is a v1 validation: validate what the page does now; do not add features.

App: ./allmeta/multivariate-ma/index.html (allmeta main, cloned in ./allmeta - record the commit) and every shared file it
loads. Find exactly what the page computes and displays/exports: the multivariate model (outcomes, within-study covariance
construction - supplied correlations or a single assumed rho, how missing outcomes are handled), estimator (REML/ML/
method of moments/fixed), between-study covariance (unstructured? Psi), pooled vector, SEs, CIs, z/p, correlations of
random effects, Q tests, I2-type statistics, any refusals, caps and convergence settings. Read
hub/shared/tests/multivariate-ma-parity.spec.mjs for orientation. Validate THAT; do not re-implement it.

Reference: R 4.6.0 with mvmeta, mixmeta and metafor from R_LIBS_USER=<LOCAL_INSTALLATION_PATH>,
R_LIBS=<LOCAL_INSTALLATION_PATH>, R_ENVIRON_USER=NUL; Rscript at <LOCAL_INSTALLATION_PATH> Files/R/R-4.6.0/bin/Rscript.exe
(or <LOCAL_INSTALLATION_PATH> if that exists). Print .libPaths() and package versions in every R log. Use the
R function whose estimator matches the page (mvmeta::mvmeta for REML/ML/MM/fixed; cross-check one estimator with
metafor::rma.mv where the parametrisation matches, and say so).
Corpus: every multivariate dataset available offline in the installed packages (mvmeta, mixmeta, metadat: e.g. berkey98,
hyp, fibrinogen, p53, dat.berkey1998, dat.kalaian1996, dat.ishak2007 ... - discover them, do not trust this list), each in
every configuration the page offers (estimator x correlation option x outcome subset as offered). Record every candidate and
every exclusion with its reason in dataset-ledger.csv; one row per configuration in configuration-ledger.csv.
Tolerances as in ../kit/codex16/TASK.md (closed form 1e-9 relative to max(1,|ref|); iterative 1e-6 with convergence
settings stated for both sides; p-values 1e-9 absolute; exact for k, membership, refusals, displayed strings vs exports at
shown decimals).
Page capture: run the page's own code in node (linkedom/jsdom, as P17 did with run_node.cjs) if the engine is pure JS, else
headless Edge via Playwright - state which.

Then: fix.patch for any defect (root cause, file:line; app-side only), rerun, RESULTS.md (counts before/after, faults with
before/after numbers, honest limits). Missing or invalid app evidence is never a pass; unique keys and exact coverage;
record every refusal with its reason; no machine paths in deliverables. Do not edit ./allmeta; copy the page into this
folder for patching. Do not git commit/push. Run at most ONE R process at a time (the machine is shared). Keep PROGRESS.md
updated so the job can resume. Final deliverable: P18-validation.zip in this folder (same layout as P16-validation.zip).
