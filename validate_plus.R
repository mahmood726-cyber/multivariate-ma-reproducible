# Plus layer of the validation (the allmeta multivariate-ma plus panel at source commit d089222, PR #152 head).
# Called at the end of validate.R (which has already checked versions and the SHA-256 inventory and rebuilt the v1
# corpus into .validate-work); it can also be run on its own: Rscript validate_plus.R
# 1. rebuilds the plus corpus from the FRESH v1 corpus (plus/source/multivariate-ma/validate/make_plus_corpus.py)
#    and requires it to be byte-identical to the archived plus corpus;
# 2. refits the plus R reference from scratch with the source commit's own generate-plus.R (mvmeta 4 starts ->
#    nlminb -> Newton polish on mvmeta's analytic REML gradient; metafor rma per outcome; rma.mv on Berkey), in this
#    R process; no archived plus reference value is reused;
# 3. analysis/run_plus_checks.py requires the fresh reference to reproduce the archived one within 1e-10, replays the
#    archived plus page outputs (plus/app-plus.json) against the FRESH R values with the plus-contract tolerances and
#    the pinned list of logLik-adjudicated boundary fits, re-compares the archived exported-R-script round trip, and
#    prints "N/N plus checks pass". Any failure stops with a nonzero exit status.
plus_start <- proc.time()[['elapsed']]
if(!exists('PLUS_CALLED_FROM_VALIDATE')) {
 source('analysis/versions.R')
 cat('.libPaths():\n'); print(.libPaths()); cat(R.version.string, '\n')
 actual <- installed_versions(); print(actual); check_versions(actual); cat('Version check PASS\n')
 pins <- jsonlite::fromJSON('SOURCE_SHA256.json', simplifyVector=FALSE)
 hashes <- tools::sha256sum(names(pins))
 bad <- names(pins)[unname(hashes) != unlist(pins, use.names=FALSE)]
 if(length(bad) || any(is.na(hashes))) stop('Input SHA-256 mismatch: ', paste(head(bad, 5), collapse=', '))
 cat(sprintf('Input SHA-256 checks PASS: %d files\n', length(pins)))
 work <- '.validate-work'
 if(file.exists(work)) stop('Existing .validate-work refused (stale-result guard); move it aside before a new full run')
 dir.create(work)
 env <- new.env(parent=globalenv()); env$OUT <- work
 sys.source('analysis/refit_corpus.R', envir=env, keep.source=FALSE)
 python <- Sys.getenv('PYTHON', unset='python')
}
plus_src <- 'plus/source/multivariate-ma/validate'
for(f in c('plus-corpus.json', 'plus-reference.json', 'plus-summary.json')) if(file.exists(file.path(work, f))) stop('Stale plus result refused: ', f)
if(!file.exists(file.path(work, 'corpus.json'))) stop('Fresh v1 corpus missing from ', work)
status <- system2(python, c('-B', file.path(plus_src, 'make_plus_corpus.py'), file.path(work, 'corpus.json'), file.path(work, 'plus-corpus.json')))
if(!identical(as.integer(status), 0L)) stop('make_plus_corpus.py failed (exit status ', status, ')')
t0 <- proc.time()[['elapsed']]
local({
 plus_args <- c(file.path(work, 'plus-corpus.json'), file.path(work, 'plus-reference.json'))
 env <- new.env(parent=globalenv())
 env$commandArgs <- function(trailingOnly=FALSE) plus_args   # generate-plus.R reads its two paths from commandArgs()
 sys.source(file.path(plus_src, 'generate-plus.R'), envir=env, keep.source=FALSE)
})
cat(sprintf('%s finished in %.1f seconds\n', file.path(plus_src, 'generate-plus.R'), proc.time()[['elapsed']] - t0)); flush.console()
status <- system2(python, c('-B', 'analysis/run_plus_checks.py', work))
if(!identical(as.integer(status), 0L)) stop('Plus comparison failed (analysis/run_plus_checks.py exit status ', status, ')')
plus_summary <- jsonlite::fromJSON(file.path(work, 'plus-summary.json'), simplifyVector=FALSE)
if(!identical(plus_summary[['plus_passed', exact=TRUE]], plus_summary[['plus_checks', exact=TRUE]])) stop('Plus comparison is not all-pass')
cat(sprintf('Plus runtime: %.1f seconds\n', proc.time()[['elapsed']] - plus_start))
cat(plus_summary[['final_line', exact=TRUE]], '\n', sep='')
