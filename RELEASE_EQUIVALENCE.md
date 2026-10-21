# Equivalence of the archived pages with allmeta v1.8.0

allmeta v1.8.0: tag `v1.8.0`, commit `1cb3f8409c7af75ed41f7e1811f9c502f900fc79`, DOI 10.5281/zenodo.23515177.

The archive has two app snapshots, and they relate to v1.8.0 differently:

| Tier | Archived snapshot | Validated at | Executed on the v1.8.0 bytes |
|---|---|---|---|
| Corrected page (v1), 18682/18682 | `app/patched/` (acd363f + `bench/fix.patch`) | pull request #154 commit `1b9b9327d75262b9ff8c32ecc5d6414c264071d6` (merge `85f328c`, an ancestor of v1.8.0) | 18581/18682: every one of the 101 failures is the output-schema version check |
| Plus panel, 54612/54612 | `plus/source/` (d0892228c2c0af009ca5270cfc8eb73ffa12eb31, pull request #152, merged into v1.8.0 as f2faaa5) | d089222 and v1.8.0 | byte-identical capture; 54612/54612 |
| Exported-R-script round trip | `plus/roundtrip/` | v1.8.0 strict rule | 29473/29502 (strict rule; the reported result) |

## 1. Corrected-page tier: validated at the pull request #154 commit, not at v1.8.0

The v1 tier stays pinned to the pull request #154 bytes. The paper cites the 18682/18682 result at that commit.
`app/patched/` equals the pull request #154 head `1b9b932` in the engine (`shared/multivariate-ma.js`); the page differs
from 1b9b932 only in its footer text. `app/patched/` is not replaced with v1.8.0 bytes: the verifier requires it to equal
`app/original` plus `bench/fix.patch` byte for byte.

allmeta v1.8.0 changed the multivariate engine and the page's output schema through pull request #152. Comparing the six
`app/patched/` files with their v1.8.0 blobs (`git diff 1b9b932 1cb3f84`):

| File | vs v1.8.0 | Change | Class |
|---|---|---|---|
| `shared/multivariate-ma.js` | differs (+166/-7) | analytic REML score and Fisher information, a Fisher-scoring polish, an allocation-free m = 2 objective, several starts, boundary and rank-one handling | **ENGINE** |
| `multivariate-ma/index.html` | differs (+225/-50) | plus panel scripts, per-study r and assumed rho_w input modes, a header-row parser, input debounced 250 ms, output schema `multivariate-ma-results-v2`, download and export controls | **ENGINE** (input parsing, output contract) |
| `shared/build-info.js` | differs | build stamp v1.7.0 7899ce5 to v1.8.0 42a94da | NON-ENGINE |
| `hub/shared/a11y-landmarks.js` | identical | | |
| `hub/shared/tests/multivariate-ma-parity.spec.mjs` | identical | | |
| `shared/forced-colors.css` | identical | | |

At v1.8.0 the page also loads six files that the v1 page did not have (`multivariate-ma/plus.js`, `multivariate-ma/plus-ui.js`,
`multivariate-ma/validate/plus-adapter.js`, `multivariate-ma/validate/plus-contract.js`, `multivariate-ma/validate/plus-pins.js`,
`shared/alm-validate.js`). The runs below used all 12 page files at their v1.8.0 blob bytes (each checked against
`git cat-file blob 1cb3f84:<path>`).

Check by execution (21 Oct 2026, Node v24.13.0, linkedom 0.18.12, Windows). The archive's own capture runner
`bench/run_node.cjs` was run with the archived `data/corpus.json`, the focused probes and `results/reference.json`, and the
captures were scored with the archive's comparison code:

| Run | Page bytes | Runner | Result |
|---|---|---|---|
| Control | archived `app/patched/` | `bench/run_node.cjs`, unmodified | `app-patched.json` `0801b9c34ee1ea0eba91df936e5ea6b6c29f76007076880e16c77880d7cb5853`, `focused-patched.json` `036820a059f881858ec36a7f8d829b6c0c1b0beb0d60151d0a17f8eedd213889`, `runtime-patched.json` `ea1268915edfba709c7b149e50f66e8c163cb69cb057028b2660e456752bab71`: all byte-identical to `results/`; **18682/18682** (`release-equivalence/v1-control-compare.log`) |
| A | v1.8.0 | unmodified | crash: `ReferenceError: location is not defined` in `shared/alm-validate.js` (`release-equivalence/v1-v1.8.0-unmodified-runner.log`) |
| B | v1.8.0 | A + the plus runner's shim: skip the `alm-validate.js` browser widget, add timer/URL globals (`release-equivalence/run_node_v180.diff`) | 132/2330 checks: the 250 ms input debounce means the runner reads the stale default-example output (`release-equivalence/v1-v1.8.0-unsynced-compare.log`) |
| C | v1.8.0 | B + synchronous `setTimeout` (`release-equivalence/run_node_v180sync.diff`) | `app-patched.json` `b74adba223f5316a54428c64c04c593070b2d4e6be00d731ac11c67d62db4cdd`, `focused-patched.json` `1ee7dbe1b339840080120901fba37f9462ecc9e93f4477b745bb593cbe4ab315`; **18581/18682** (`release-equivalence/v1-v1.8.0-synctimers-compare.log`, `release-equivalence/v1-results-patched-v1.8.0.json`) |

In run C, all 101 failing checks are the quantity `schema` (`multivariate-ma-results-v2` where the archived contract
requires `multivariate-ma-results-v1`), one per page capture. Every other per-quantity count is identical to the control
run and to `expected/paper_values.json`: all numeric (mu, muSE, muVcov, G, rho, logLik, CI, SD), accessor, default
example, display, SVG/ellipse, refusal and focused checks pass at the archive's tolerances (1e-6 iterative, 1e-9 exact
and geometry, exact otherwise). The verifier checks this from `release-equivalence/v1-results-patched-v1.8.0.json`.

The numbers are equal within those tolerances, **not bit for bit**. Comparing the run C capture with the archived
`results/app-patched.json` value by value (`release-equivalence/capture_diff.py`, output
`release-equivalence/v1-capture-diff.json`): 8051 of 9685 numbers are exactly equal; the others differ by at most
6.59e-8 (scaled, G), 4.3e-8 (muVcov), 3.8e-8 (rho), 2.0e-8 (muSE), 6.6e-9 (mu) and 1.2e-14 (logLik), which is the effect
of the v1.8.0 Fisher-scoring polish. Non-numeric differences: the schema string (91 outputs), the SVG viewBox height
(91), the refusal headline wording of the one refused configuration (1), and new output fields (z, p, muVcov, mode,
labels, outcomes, omitted, optimizer, rhoW). Supplementary engine-only check (not a page capture): the PR #154 and v1.8.0
`shared/multivariate-ma.js`, fitted on the archived accepted-study sets, both give 2002/2002 against the reference
(`release-equivalence/engine_check.cjs`, `engine-check.log`).

Under the archive protocol this is not an execution pass (the counts are not equal), so the 18682/18682 tier is **not**
claimed for v1.8.0. It is claimed at pull request #154 commit 1b9b932.

## 2. Plus tiers: executed on the v1.8.0 bytes, byte-identical

Of the 29 files in `plus/source/`, 21 are byte-identical to their v1.8.0 blobs (including `shared/multivariate-ma.js`,
`multivariate-ma/plus.js`, `validate/run-plus-node.cjs`, `validate/roundtrip-export.cjs`, `validate/generate-plus.R`, the
pins, the plus corpus and the plus reference). The other 8 differ (`git diff d089222 1cb3f84`):

| File | Change | Class |
|---|---|---|
| `multivariate-ma/index.html` | header row recognised only when its fields equal `y1,v1,y2,v2[,cov/r]` | ENGINE (input parsing) |
| `multivariate-ma/plus-ui.js` | `clearSweep()`: the sweep display is cleared on new data or a re-run | ENGINE by rule (UI code, not on the fit path) |
| `multivariate-ma/validate/plus-contract.js` | strict contract: `fitIntegrity`; z and p never adjudicated | ENGINE (validation code) |
| `multivariate-ma/validate/plus-adapter.js` | display audit recomputes z/p from mu/SE via `zTest` | ENGINE (validation code) |
| `multivariate-ma/validate/roundtrip-compare.cjs` | strict round-trip rule | ENGINE (validation code) |
| `shared/alm-validate.js` | live-R widget prints `R version` once (browser widget; skipped in Node) | ENGINE by rule (display string only) |
| `multivariate-ma/validate/README-plus.md` | documents the stricter adjudication | NON-ENGINE |
| `shared/build-info.js` | build stamp | NON-ENGINE |

`plus/source/` keeps the d089222 bytes because its manifest, the Edge/Playwright, K2 and usability evidence were all
produced at that commit. Equivalence with v1.8.0 is shown by execution on the 29 files at their v1.8.0 bytes:

- `analysis/dump_plus_app.cjs` (the archive's plus capture): `app-plus.json` SHA-256
  `f368030ab2e5ed2bb9298ed3556e319a2c176cfe48396591460adeeb8174fd9e`, **byte-identical** to the archived
  `plus/app-plus.json`. Its embedded contract replay under the strict v1.8.0 contract gives 54612/54612 with 1
  adjudicated fit (the same craft2003 fit pinned in `expected/plus_values.json`).
- `validate/run-plus-node.cjs` (the pinned whole-page replay): `PLUS NODE REPLAY 54612/54612 passed; 0 failed;
  manifest 54612; adjudicated fits 1`. The evidence record (`release-equivalence/plus-node-replay-v1.8.0.json`) equals
  `plus/evidence/node-replay/final-evidence-node.json` except the `seconds` field.

The plus tier result 54612/54612 therefore applies unchanged to allmeta v1.8.0.

## 3. Round trip: executed on the v1.8.0 bytes, strict rule

- `validate/roundtrip-export.cjs` at v1.8.0 exported 94 cases with 93 page fits ok
  (`release-equivalence/roundtrip-export-v1.8.0.log`). Of the 189 exported files, 1 is byte-identical to `plus/roundtrip/`
  and 188 differ only in the embedded build stamp (`7899ce599bfd` to `42a94da2110a`); with the stamp masked, 0 differ
  (NON-ENGINE). The Rscript step was not re-run: it is an R tier, and the exported scripts differ only in the stamp
  comment.
- `validate/roundtrip-compare.cjs` at v1.8.0 (strict) on the archived page and R files:
  `ROUNDTRIP 29473/29502 passed; 29 failed; 64 fits with parameter adjudication; 0 R outputs missing`, failures by
  quantity `{"z":23,"p":6}` (`release-equivalence/roundtrip-compare-v1.8.0.log`). Its `roundtrip-result.json` has
  SHA-256 `597d927e09a09e3bed40494e02fd7aee75226e1c4c274a8cb83daa767e4b6b99`, byte-identical to the archived
  `plus/roundtrip/roundtrip-result.json`.
- `analysis/run_plus_checks.py` ports the strict rule line for line and reproduces the same 29473/29502, the same 29
  failing checks and the same 64 adjudicated fits from the archived files, as pinned in `expected/plus_values.json`.

The superseded d089222 rule (z/p adjudicated on the reported logLik) gives 29502/29502 with 68 adjudicated fits; it is
kept as labelled history only (`plus/roundtrip/roundtrip-result.v1rule.json`, SHA-256
`276e8c6670502c64a582a010e333fcb1a9b25ac7fe695681ed649f96ea462000`).

Not re-run: the R reference tiers (they do not depend on the app) and the Edge/Playwright tiers (no runner in this
environment). `release-equivalence/v1-results-patched-v1.8.0.json` and the logs are stored with LF line endings.
