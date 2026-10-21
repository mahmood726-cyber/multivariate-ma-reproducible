# P18 validation archive

Read RESULTS.md for findings, strict counts and limitations. results.json provides machine-readable totals; dataset-, configuration-, row- and refusal-ledger.csv provide coverage and reasons.

app-original/ contains the audited source snapshots. app-patched/ contains proposed repairs; fix.patch is a unified diff against the source tree. node_modules/ supplies the offline linkedom runtime and dependency licenses. Run `node run_node.cjs original`, `node run_node.cjs patched`, then both `python compare.py` variants to replay against the stored R reference. For a full reference rebuild, configure RSCRIPT and the two AUDIT_R_LIBS environment variables and run corpus.R, reference.R and crosscheck.R through run_r.py, sequentially. Scripts use relative paths. Do not run setup.py against the finished archive: it is a source-ingest helper and the snapshots/dependencies are already present.

documentation/ contains installed help and reference-function snapshots. Initial reference files and diagnose_reference.* are diagnostic history, not pass evidence. The primary references are reference.json and metafor-crosscheck.json. No p-values, Q, I2 or file-download outputs exist in this page. Browser layout was not tested.

verify_archive.py verifies exact key coverage, numerical finiteness, membership, source hashes, patch replay, artifact checksums and absence of machine-specific paths, and creates P18-validation.zip with a P18-validation/ root. TASK.md inside the archive is a portable transcription of the original task with local installation paths replaced by placeholders; the user's original local TASK.md is preserved outside the archive. codex.log and RUN.json are execution-environment files and are intentionally excluded.
