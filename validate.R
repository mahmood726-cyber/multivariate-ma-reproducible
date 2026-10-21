# One-command validation: Rscript validate.R   (run from the archive root)
# 1. refuses unless R and package versions equal those recorded in the validation bundle;
# 2. SHA-256 checks the complete source inventory (SOURCE_SHA256.json);
# 3. rebuilds the 92-configuration corpus from the installed mvmeta, mixmeta and metadat data (analysis/refit_corpus.R),
#    refits every configuration with mvmeta REML (analysis/refit_reference.R) and repeats the metafor rma.mv
#    cross-check (analysis/refit_crosscheck.R); no archived corpus, fit or cross-check value is reused;
# 5. finally sources validate_plus.R (plus layer: fresh plus R refit, page replay, round trip; prints 'N/N plus checks pass').
# 4. analysis/run_checks.py requires the fresh corpus and row ledger to equal the archived ones, the fresh fits to
#    reproduce the archived reference within 1e-10, then compares the archived page outputs (results/app-*.json,
#    focused-*.json, runtime-*.json) with the FRESH R values, requires every per-quantity count and the exact list of
#    failing checks to equal expected/paper_values.json, and prints "N/N checks pass". Any failure exits nonzero.
# Set R_ENVIRON_USER to an empty file (NUL on Windows) so a user .Renviron cannot change the library paths;
# set R_LIBS_USER/R_LIBS to the libraries holding the exact versions and PYTHON to a Python 3 executable if
# `python` is not on PATH. No packages are installed and no network access is needed.
start <- proc.time()[['elapsed']]
source('analysis/versions.R')
cat('.libPaths():\n'); print(.libPaths())
cat(R.version.string, '\n')
actual <- installed_versions()
print(actual)
check_versions(actual)
cat('Version check PASS\n')
pins <- jsonlite::fromJSON('SOURCE_SHA256.json', simplifyVector=FALSE)
files <- list.files('.', recursive=TRUE, all.files=TRUE, no..=TRUE)
files <- files[!grepl('^(\\.git|\\.validate-work|\\.verify-[^/]*)/', files) & !grepl('(^|/)(__pycache__|\\.pytest_cache)/', files) &
               !(files %in% c('SOURCE_SHA256.json', 'PROGRESS.md'))]
if(anyDuplicated(names(pins)) || !setequal(files, names(pins)) || length(files) != length(pins))
 stop('Source inventory mismatch: missing ', paste(head(setdiff(names(pins), files), 3), collapse=', '), '; extra ', paste(head(setdiff(files, names(pins)), 3), collapse=', '))
hashes <- tools::sha256sum(names(pins))
bad <- names(pins)[unname(hashes) != unlist(pins, use.names=FALSE)]
if(length(bad)) stop('Input SHA-256 mismatch: ', paste(head(bad, 5), collapse=', '))
cat(sprintf('Input SHA-256 checks PASS: %d files\n', length(pins)))
work <- '.validate-work'
if(file.exists(work)) stop('Existing .validate-work refused (stale-result guard); move it aside before a new full run')
dir.create(work)
fit <- function(script) {
 env <- new.env(parent=globalenv()); env$OUT <- work
 t0 <- proc.time()[['elapsed']]; sys.source(script, envir=env, keep.source=FALSE)
 cat(sprintf('%s finished in %.1f seconds\n', script, proc.time()[['elapsed']] - t0)); flush.console()
}
fit('analysis/refit_corpus.R')
fit('analysis/refit_reference.R')
fit('analysis/refit_crosscheck.R')
python <- Sys.getenv('PYTHON', unset='python')
status <- system2(python, c('-B', 'analysis/run_checks.py', work))
if(!identical(as.integer(status), 0L)) stop('Archive comparison failed (analysis/run_checks.py exit status ', status, ')')
summary <- jsonlite::fromJSON(file.path(work, 'summary.json'), simplifyVector=FALSE)
if(!identical(summary[['patched_passed', exact=TRUE]], summary[['patched_checks', exact=TRUE]])) stop('Patched comparison is not all-pass')
cat(sprintf('Runtime: %.1f seconds\n', proc.time()[['elapsed']] - start))
cat(summary[['final_line', exact=TRUE]], '\n', sep='')

# Plus layer (comparison/sensitivity panel, source commit d089222): see validate_plus.R
PLUS_CALLED_FROM_VALIDATE <- TRUE
source('validate_plus.R')
cat(sprintf('Total runtime: %.1f seconds\n', proc.time()[['elapsed']] - start))
