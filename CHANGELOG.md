# Changelog

## 1.0.0

Initial reproducibility archive for the multivariate-ma validation against mvmeta 1.0.3 (REML, unstructured between-study covariance) with a metafor 5.2-1 rma.mv cross-check, and the plus panel layer. The allmeta release identifiers are filled: v1.8.0 (tag commit 1cb3f84, DOI 10.5281/zenodo.23515177), which contains pull requests #154 (the fixes) and #152 (the plus panel). The verifier now requires the filled values instead of the tokens, and RELEASE_EQUIVALENCE.md.

- RELEASE_EQUIVALENCE.md: the corrected-page tier (18682/18682) stays validated and cited at the pull request #154 commit 1b9b932 (merge 85f328c). v1.8.0 changed the engine and the output schema through pull request #152; the archive's runner on the v1.8.0 bytes gives 18581/18682, every failure the output-schema version (`-v1` to `-v2`), with all numeric checks passing (values within 6.6e-8, not bit-identical). The plus capture is byte-identical on the v1.8.0 bytes (54612/54612), and the round trip was re-scored with the v1.8.0 comparator.
- Round trip: the strict allmeta v1.8.0 rule (z/p never adjudicated; fit integrity and recomputed logLik) is adopted: 29473/29502, 29 expected failures (z 23, p 6) in 16 fits, 64 parameter-adjudicated fits, all pinned in `expected/plus_values.json`; `analysis/run_plus_checks.py` ports the strict rule. The earlier 29502/29502 (68 logLik-adjudicated fits) result is kept as labelled history.
- Hygiene: machine paths in the recorded `.cmd` files replaced by documented tokens (`plus/evidence/PATH_TOKENS.md`); `.cmd` and `.bat` added to the text-hygiene scan; the bundle-run host recorded as `worker`.
- SOURCE_SHA256.json re-pinned. The repository history is squashed into one commit.
