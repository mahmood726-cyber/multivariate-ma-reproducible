from pathlib import Path
import shutil, hashlib, json, subprocess, re
root=Path(__file__).resolve().parent
files=['multivariate-ma/index.html','shared/multivariate-ma.js','shared/build-info.js','shared/forced-colors.css','hub/shared/a11y-landmarks.js','hub/shared/tests/multivariate-ma-parity.spec.mjs']
manifest={'commit':subprocess.check_output(['git','-C','allmeta','rev-parse','HEAD'],text=True).strip(),'files':[]}
for f in files:
    src=root/'allmeta'/f
    for variant in ['original','patched']:
        dst=root/f'app-{variant}'/f; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(src,dst)
    manifest['files'].append({'path':f,'sha256':hashlib.sha256(src.read_bytes()).hexdigest()})
Path('source-manifest.json').write_text(json.dumps(manifest,indent=2))
for p in (root.parent/'P17/node_modules').iterdir():
    if p.name!='playwright-core' and p.is_dir(): shutil.copytree(p,root/'node_modules'/p.name,dirs_exist_ok=True)
for p in Path('documentation').glob('*.txt'):
    text=p.read_text(encoding='utf-8'); text=re.sub('.\x08','',text); p.write_text(text,encoding='utf-8')
shutil.copyfile('allmeta/LICENSE','LICENSE.app.txt') if Path('allmeta/LICENSE').exists() else None
print('SETUP: source snapshot and local linkedom dependencies copied')
