# Path tokens in the recorded command files

The command files `roundtrip-rerun/rt.cmd` and `k2/run1.cmd` are the commands that produced the evidence next to them.
Machine-specific paths in them were replaced by the tokens below; nothing else was changed. Substitute your own paths
to rerun them.

| Token | Meaning |
|---|---|
| `<R_LIBS_USER>`, `<R_LIBS>` | the two R libraries that together hold the pinned package versions listed in the README (Reproduce) |
| `<RSCRIPT>` | the R 4.6.0 `Rscript` executable |
| `<NODE_MODULES>` | a `node_modules` folder holding linkedom 0.18.12 (Node.js v24.13.0) |
| `<AUDIT_ROOT>` | the working folder of the run: for `rt.cmd`, a folder holding the plus source at d089222 under `src/`; for `run1.cmd`, the folder holding `src.tar`, `nm.tar` and the `k2/` scripts |
