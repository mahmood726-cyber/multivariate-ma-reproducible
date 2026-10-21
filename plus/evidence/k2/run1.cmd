@echo off
set L=<AUDIT_ROOT>
cd /d %L%
if not exist site mkdir site
tar -xf src.tar -C site
if not exist nm\node_modules mkdir nm\node_modules
tar -xf nm.tar -C nm\node_modules
set C=%L%\site\multivariate-ma\validate\plus
echo K2 start %DATE% %TIME% > k2.log
set K1_ENGINE=%L%\engine-v1-1b9b932.js
echo ==== v1 engine 1b9b932 (single-start Nelder-Mead, via k1shim) >> k2.log
node sweep_vs_ref.cjs %L%\k1shim.cjs %C%\corpus.json %C%\reference.json 8 >> k2.log 2>&1
echo ==== intermediate engine (1b9b932 + Fisher-scoring polish, single start; k2_engine.py) >> k2.log
node sweep_vs_ref.cjs %L%\k2-rebuilt.js %C%\corpus.json %C%\reference.json 8 >> k2.log 2>&1
echo ==== final engine d089222 shared/multivariate-ma.js (polish + 5 screened starts) >> k2.log
node sweep_vs_ref.cjs %L%\site\shared\multivariate-ma.js %C%\corpus.json %C%\reference.json 8 >> k2.log 2>&1
echo K2 end %DATE% %TIME% >> k2.log
set PW_MODULES=%L%\nm\node_modules
node usability2.mjs %L%\site %L%\walk > walk.log 2>&1
echo exit=%ERRORLEVEL% >> walk.log
echo done > run1.done
