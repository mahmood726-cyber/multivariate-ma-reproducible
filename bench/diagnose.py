import json
def read(p):return json.load(open(p,encoding='utf-8'))
r=read('reference.json');a=read('app-original.json')
print('First reference:',r[0]);print('First app:',a[0]['capture']['result']);print('Metafor:',read('metafor-crosscheck.json'))
def flat(x):return sum([flat(y) for y in x],[]) if isinstance(x,list) else [x]
for c,z in zip(a,r):
 if z['status']!='ok':continue
 f=c['capture']['result']
 for q in ['mu','muSE','G','rho','logLik']:
  e=max(abs(x-y)/max(1,abs(y)) for x,y in zip(flat(f[q]),flat(z[q])))
  if e>1e-6:print(c['id'],q,e,'APP',f[q],'REF',z[q])
