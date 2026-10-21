@echo off
set R_LIBS_USER=<R_LIBS_USER>
set R_LIBS=<R_LIBS>
set R_ENVIRON_USER=NUL
set NODE_PATH=<NODE_MODULES>
set W=<AUDIT_ROOT>
echo start %DATE% %TIME% > %W%\rt-time.txt
cd /d %W%\src\multivariate-ma\validate
node roundtrip-export.cjs %W%\rt > %W%\rt-export.log 2>&1
for /d %%d in (%W%\rt\scripts\*) do (
  pushd %%d
  "<RSCRIPT>" --vanilla analysis.R > run.log 2>&1
  popd
)
node roundtrip-compare.cjs %W%\rt > %W%\rt-compare.log 2>&1
echo exit=%ERRORLEVEL% >> %W%\rt-compare.log
echo end %DATE% %TIME% >> %W%\rt-time.txt
echo done > %W%\rt.done
