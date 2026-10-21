import os, pathlib, subprocess, sys, re
root=pathlib.Path(__file__).resolve().parent
env=os.environ.copy()
base=root.parents[1]
env.update(R_LIBS_USER=env.get('AUDIT_R_LIBS_USER',str(base/'Rlib_dta')),R_LIBS=env.get('AUDIT_R_LIBS',str(base/'Rlib_extra')),R_ENVIRON_USER='NUL')
r=pathlib.Path(env.get('RSCRIPT',str(pathlib.Path.home()/'R/R-4.6.0/bin/Rscript.exe')))
result=subprocess.run([str(r),'--vanilla',*sys.argv[1:]],env=env,cwd=root,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace')
text=result.stdout
for path,label in [(str(base/'Rlib_dta'),'<R_LIBS_USER>'),(str(base/'Rlib_extra'),'<R_LIBS>'),(str(pathlib.Path.home()/'R/R-4.6.0/library'),'<R_HOME>/library'),(str(root),'<AUDIT_ROOT>')]:
    text=text.replace(path,label).replace(path.replace('\\','/'),label)
pathlib.Path(pathlib.Path(sys.argv[1]).stem+('-'+'-'.join(sys.argv[2:]) if len(sys.argv)>2 else '')+'.log').write_text(text,encoding='utf-8')
print(text)
sys.exit(result.returncode)
