# Generated from bench/compare.py; only input/output paths differ (see analysis/compare_archive.diff).
# corpus.json, reference.json and metafor-crosscheck.json are read from the fresh R run; app observations from results/.
import json, math, sys, collections, re, xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
variant,REFDIR,OUTDIR=sys.argv[1],Path(sys.argv[2]),Path(sys.argv[3])
assert variant in ('original','patched')
FRESH={'corpus.json','reference.json','metafor-crosscheck.json'}
def read(name): return json.loads(((REFDIR if name in FRESH else ROOT/'results')/name).read_text(encoding='utf-8'))
corpus=read('corpus.json'); refs=read('reference.json'); apps=read(f'app-{variant}.json')
checks=[]
def check(id,q,a,b,tol=0,absolute=False):
    numeric=isinstance(a,(int,float)) and not isinstance(a,bool) and isinstance(b,(int,float)) and not isinstance(b,bool)
    err=abs(a-b)/(1 if absolute else max(1,abs(b))) if numeric and math.isfinite(a) and math.isfinite(b) else None
    ok=(err<=tol) if numeric and err is not None else (a==b and a is not None and b is not None)
    checks.append(dict(id=id,quantity=q,actual=a,reference=b,tolerance=tol,error=err,passed=bool(ok)))
def index(rows,name):
    ids=[r['id'] for r in rows];check('coverage',name+'_unique',len(ids),len(set(ids)))
    check('coverage',name+'_keys',sorted(ids),sorted(c['id'] for c in corpus))
    return {r['id']:r for r in rows}
R=index(refs,'reference');A=index(apps,'app')
def scalar(id,q,a,b,tol=1e-6):
    if isinstance(b,list):
        for i,x in enumerate(b): scalar(id,q,a[i] if isinstance(a,list) and i<len(a) else None,x,tol)
    elif b is None:check(id,q+'_undefined',a is None,True)
    else:check(id,q,a,b,tol)
def fmt(x,d=3):return f'{x:.{d}f}' if isinstance(x,(float,int)) and math.isfinite(x) else '\u2014'
def display(id,a):
    f=(a.get('capture') or {}).get('result');o=a.get('output');cards=a.get('cards',[])
    check(id,'valid_capture',bool(f and o and not a.get('error')),True)
    if not f or not o:return
    for q in ['k','mu','muSE','G','rho','logLik']:scalar(id,'accessor_'+q,o.get(q),f.get(q),0)
    check(id,'schema',o.get('_schema'),'multivariate-ma-results-v1')
    expected=[f'{fmt(f["mu"][j])} [{fmt(f["mu"][j]-1.959963984540054*f["muSE"][j])}, {fmt(f["mu"][j]+1.959963984540054*f["muSE"][j])}]' for j in range(2)]
    expected += [fmt(math.sqrt(f['G'][j][j]),4) for j in range(2)]+[fmt(f['rho'])]
    check(id,'display_cards',[x['value'] for x in cards],expected)
    check(id,'display_headline',f'k = {f["k"]} studies' in a['headline'] and ('logLik = '+fmt(f['logLik'])) in a['headline'],True)
    svg=a.get('svg','')
    try:
        tree=ET.fromstring(svg); ns={'s':'http://www.w3.org/2000/svg'}
        circles=tree.findall('s:circle',ns);polygon=tree.find('s:polygon',ns)
        check(id,'plot_study_count',len(circles),f['k'])
        pts=[list(map(float,p.split(','))) for p in polygon.attrib['points'].split()]
        check(id,'ellipse_vertices',len(pts),81)
        check(id,'ellipse_in_viewport',all(56-1e-8<=x<=540+1e-8 and 20-1e-8<=y<=316+1e-8 for x,y in pts),True)
        check(id,'svg_finite',all(math.isfinite(x) for p in pts for x in p),True)
        studies=a['capture']['studies'];coords=[[float(e.attrib['cx']),float(e.attrib['cy'])] for e in circles]
        transforms=[]
        for j in range(2):
            pair=next(((h,l) for h in range(len(studies)) for l in range(h) if studies[h]['y'][j]!=studies[l]['y'][j]),None)
            if pair:
                h,l=pair;scale=(coords[h][j]-coords[l][j])/(studies[h]['y'][j]-studies[l]['y'][j]);offset=coords[h][j]-scale*studies[h]['y'][j];transforms.append((scale,offset))
                for s,p in zip(studies,coords):check(id,'plot_study_coordinate',p[j],offset+scale*s['y'][j],1e-9)
            else: transforms.append(None)
        if all(transforms):
            cv=f['muVcov'];det=cv[0][0]*cv[1][1]-cv[0][1]**2
            for p in pts:
                x,y=[(p[j]-transforms[j][1])/transforms[j][0]-f['mu'][j] for j in range(2)]
                check(id,'ellipse_mahalanobis',(cv[1][1]*x*x-2*cv[0][1]*x*y+cv[0][0]*y*y)/det,-2*math.log(.05),1e-9)
    except Exception as e:check(id,'valid_svg',str(e),True)
for c in corpus:
    id=c['id'];r=R.get(id);a=A.get(id)
    if not r or not a:check(id,'present',False,True);continue
    accepted=c['accepted'] if isinstance(c['accepted'],list) else [c['accepted']]
    studies=[{k:s[k] for k in ['y','S']} for i,s in enumerate(c['studies'],1) if i in accepted]
    check(id,'input_membership',(a.get('capture') or {}).get('studies'),studies)
    if r['status']=='refused':
        check(id,'refusal',bool(a.get('output') is None and not a.get('svg') and not a.get('cards') and a.get('headline')),True)
        continue
    check(id,'fit_status',bool(a.get('output') and not a.get('error')),True)
    f=(a.get('capture') or {}).get('result') or {}
    tol=1e-9 if r.get('adjudication','').startswith('two-study exact') else 1e-6
    for q in ['mu','muSE','muVcov','G','rho','logLik']:scalar(id,q,f.get(q),r[q],tol)
    for q in ['k','m']:scalar(id,q,f.get(q),r[q],0)
    for j in range(2):
        for side,sgn in [('ciLower',-1),('ciUpper',1)]:
            val=f['mu'][j]+sgn*1.959963984540054*f['muSE'][j] if f else None
            check(id,side,val,r[side][j],tol)
        val=math.sqrt(f['G'][j][j]) if f and f['G'][j][j]>=0 else None
        check(id,'sd',val,r['sd'][j],tol)
    display(id,a)
for a in read(f'focused-{variant}.json'):
    id='focused::'+a['id']
    if a['status']=='refused':
        if a.get('api'): check(id,'api_refusal',bool(a['error'] and a['output'] is None),True)
        else:check(id,'ui_refusal',bool(a['output'] is None and not a['cards'] and not a['svg'] and a['headline'] and not a['error']),True)
    else:
        check(id,'focused_k',(a.get('output') or {}).get('k'),a['k'])
        display(id,a)
        if a.get('names'):check(id,'outcome_labels',[x['label'] for x in a['cards']], [a['names'][0]+' pooled',a['names'][1]+' pooled','Between-study SD '+a['names'][0],'Between-study SD '+a['names'][1],'Between-study \u03c1'])
x=read('metafor-crosscheck.json');r=R[x['id']]
for q in ['mu','muSE','G','rho','logLik']:scalar('metafor-crosscheck',q,x[q],r[q])
default=read(f'runtime-{variant}.json')['defaultUninstrumented']
for q in ['mu','muSE','G','rho','logLik']:scalar('built-in-Berkey','default_'+q,default.get(q),r[q])
summary=[]
for q in sorted(set(c['quantity'] for c in checks)):
    cc=[c for c in checks if c['quantity']==q];errs=[c['error'] for c in cc if c['error'] is not None]
    summary.append(dict(quantity=q,checks=len(cc),passed=sum(c['passed'] for c in cc),max_error=max(errs,default=None),tolerance=max(c['tolerance'] for c in cc)))
result=dict(variant=variant,total=len(checks),passed=sum(c['passed'] for c in checks),summary=summary,failures=[c for c in checks if not c['passed']])
(OUTDIR/f'results-{variant}.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
(OUTDIR/f'checks-{variant}.json').write_text(json.dumps(checks,ensure_ascii=False),encoding='utf-8')
lines=[f'{s["quantity"]}: {s["passed"]}/{s["checks"]}; max error={s["max_error"]}; tolerance={s["tolerance"]}' for s in summary]+[f'{result["passed"]}/{result["total"]} checks pass']
text='\n'.join(lines);print(text);(OUTDIR/f'comparison-{variant}.txt').write_text(text+'\n',encoding='utf-8')
