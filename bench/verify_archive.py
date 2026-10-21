from pathlib import Path
import json,csv,hashlib,zipfile,re,tempfile,shutil,subprocess,math,collections
root=Path(__file__).resolve().parent
def read(p):return json.loads((root/p).read_text(encoding='utf-8'))
def digest(b):return hashlib.sha256(b).hexdigest()
manifest=read('source-manifest.json');C=read('corpus.json');R=read('reference.json')
ids=[c['id'] for c in C];assert len(ids)==len(set(ids))==92
for name in ['reference.json','app-original.json','app-patched.json']:
 rows=read(name);keys=[r['id'] for r in rows];assert len(keys)==len(set(keys)) and set(keys)==set(ids),name
for item in manifest['files']:
 p=root/'app-original'/item['path'];assert digest(p.read_bytes())==item['sha256'],str(p.relative_to(root))
 source=root/'allmeta'/item['path']
 if source.exists():assert source.read_bytes()==p.read_bytes(),item['path']
if (root/'allmeta/.git').exists():
 assert subprocess.check_output(['git','-C',str(root/'allmeta'),'rev-parse','HEAD'],text=True).strip()==manifest['commit']
 assert not subprocess.check_output(['git','-C',str(root/'allmeta'),'status','--porcelain'],text=True).strip()
def finite(x):
 if isinstance(x,list):return all(finite(y) for y in x)
 return isinstance(x,(int,float)) and math.isfinite(x)
for variant in ['original','patched']:
 rows=read(f'app-{variant}.json')
 for c,a in zip(C,rows):
  assert c['id']==a['id']
  # Check the exact scalar numeric input transmitted to the page independent of
  # decimal spellings (R uses 17 digits; JavaScript writes shortest round-trip).
  lines=a['input'].splitlines();assert len(lines)==len(c['studies'])
  for line,s in zip(lines,c['studies']):
   tokens=line.split(',')[-5:];want=[s['y'][0],s['S'][0][0],s['y'][1],s['S'][1][1],s['S'][0][1]]
   got=[None if x.strip()=='NA' else float(x) for x in tokens];assert got==want,(c['id'],got,want)
  expected=[{key:c['studies'][i-1][key] for key in ['y','S']} for i in c['accepted']]
  assert a['capture']['studies']==expected,c['id']
  if variant=='patched' and a['output']:
   f=a['capture']['result'];assert all(finite(f[q]) for q in ['mu','muSE','muVcov','G','logLik'])
   assert f['rho'] is None or finite(f['rho'])
 ledger=list(csv.DictReader((root/'configuration-ledger.csv').open(encoding='utf-8')))
 assert len(ledger)==len(ids) and {r['id'] for r in ledger}==set(ids)
 for c,row in zip(C,ledger):assert digest(json.dumps(c['studies'],sort_keys=True,separators=(',',':')).encode())==row['input_sha256']
checks=read('checks-patched.json');assert checks and all(c['passed'] for c in checks)
assert len(checks)==read('results-patched.json')['total']==read('results.json')['counts']['patched']['total']
dl=list(csv.DictReader((root/'dataset-ledger.csv').open(encoding='utf-8')))
assert len(dl)==132 and len({(d['package'],d['dataset']) for d in dl})==132
assert sum(int(d['configurations']) for d in dl)==92
assert all(d['reason'] and (root/d['documentation']).exists() for d in dl)
for log in root.glob('*.log'):
 if log.name=='codex.log':continue
 t=log.read_text(encoding='utf-8');assert 'R version 4.6.0' in t and all(p in t for p in ['mvmeta 1.0.3','mixmeta 1.2.2','metafor 5.2.1','<R_LIBS_USER>']),log.name
replay=(root/'patch-replay-check').resolve();assert replay.is_relative_to(root)
replay.mkdir(exist_ok=True)
if True:
 for p in (root/'app-original').rglob('*'):
  if p.is_file():
   dest=replay/p.relative_to(root/'app-original');dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes())
 proc=subprocess.run(['git','apply','--check',str(root/'fix.patch')],cwd=replay,capture_output=True,text=True)
 assert proc.returncode==0,proc.stderr
 proc=subprocess.run(['git','apply',str(root/'fix.patch')],cwd=replay,capture_output=True,text=True)
 assert proc.returncode==0,proc.stderr
 for p in (root/'app-patched').rglob('*'):
  if p.is_file():assert (replay/p.relative_to(root/'app-patched')).read_bytes()==p.read_bytes(),str(p.relative_to(root))
verification={'source_commit':manifest['commit'],'source_unchanged':True,'patch_replay_matches':True,'exact_configuration_coverage':92,'unique_candidate_coverage':132,'input_membership_and_numeric_values_exact':True,'patched_output_finite':True,'patched_checks':len(checks),'patched_checks_pass':True,'all_candidate_documentation_present':True,'all_R_logs_have_versions_and_library_paths':True}
(root/'verification.json').write_text(json.dumps(verification,indent=2)+'\n')
# Include portable evidence/scripts, source snapshots, docs and offline runtime.
exclude={'TASK.md','RUN.json','codex.log','reference-partial.json','archive-manifest.json','archive-verification.json','P18-validation.zip','P18-validation.zip.sha256'}
files={}
for p in root.iterdir():
 if p.is_file() and p.name not in exclude and p.suffix in {'.py','.R','.cjs','.json','.csv','.log','.txt','.md','.patch'}:files[p.name]=p.read_bytes()
for folder in ['app-original','app-patched','documentation','node_modules']:
 for p in (root/folder).rglob('*'):
  if p.is_file():files[p.relative_to(root).as_posix()]=p.read_bytes()
task=(root/'TASK.md').read_text(encoding='utf-8')
task=re.sub(r'[A-Za-z]:[/\\][^\s,;\n)]+','<LOCAL_INSTALLATION_PATH>',task)
files['TASK.md']=task.encode('utf-8')
# The precise current host names must never leak through bundled prose/logs.
machine=re.compile(rb'(?i)(?:[A-Z]:[/\\](?:Users|Projects|claude-temp)[/\\]|/ho'+rb'me/[^/\s]+/)')
bad=[name for name,b in files.items() if machine.search(b)]
assert not bad,('machine paths in deliverables',bad)
archive_manifest={'root':'P18-validation','files':[{'path':name,'bytes':len(b),'sha256':digest(b)} for name,b in sorted(files.items())]}
b=(json.dumps(archive_manifest,indent=2)+'\n').encode();(root/'archive-manifest.json').write_bytes(b);files['archive-manifest.json']=b
archive=root/'P18-validation.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for name,b in sorted(files.items()):z.writestr('P18-validation/'+name,b)
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 assert len(z.namelist())==len(files)==len(set(z.namelist()))
 for entry in archive_manifest['files']:
  b=z.read('P18-validation/'+entry['path']);assert len(b)==entry['bytes'] and digest(b)==entry['sha256']
sha=digest(archive.read_bytes());(root/'P18-validation.zip.sha256').write_text(sha+'  P18-validation.zip\n')
verification.update(archive_files=len(files),archive_bytes=archive.stat().st_size,archive_sha256=sha,all_archive_hashes_match=True,no_machine_paths=True)
(root/'archive-verification.json').write_text(json.dumps(verification,indent=2)+'\n')
print(f"VERIFIED: {len(files)} archived files; 132 candidates; 92 configurations; exact patch replay; {len(checks)}/{len(checks)} patched checks pass")
print('ARCHIVE: P18-validation.zip SHA256 '+sha)
