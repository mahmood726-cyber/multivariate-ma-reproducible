import json,csv,hashlib,collections
from pathlib import Path
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def write(p,rows):
 with open(p,'w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
inv=read('inventory.json');corpus=read('corpus.json');used=collections.Counter((x['package'],x['dataset']) for x in corpus)
reasons={
'alcohol':'dose-response observations at study-specific doses; no common outcome/coefficient vector or within-study covariance is supplied; would require first-stage dose-response modelling',
'bcg':'logRR and logOR are alternative measures of the same endpoint; their joint sampling covariance is not supplied; raw arm outcomes are not two separate outcomes',
'school':'one effect per school nested in district; multilevel intercept model, not two labeled outcomes per independent study',
'thrombolytic':'one effect per trial; time-to-treatment is a moderator, not a second outcome',
'dat.aloe2013':'one partial-correlation outcome per study; t, R2 and predictors are construction inputs',
'dat.anker2025':'sex-specific subgroup contrasts and interaction are transformations/partitions of one endpoint; no two distinct outcome vector; subgroup analysis outside the paired-outcome corpus rule',
'dat.assink2016':'multiple delinquency effects nested in studies; no unique outcome pair or sampling covariance supplied',
'dat.bakdash2021':'multiple SA/performance correlations per SampleID with duplicate outcome types; sampling covariances not supplied or reconstructable from full correlation matrices',
'dat.bartos2023':'coin-flip counts partitioned by starting face; repeated participant experiments, not a study-level paired outcome meta-analysis dataset',
'dat.besson2016':'multiple rodent behavior and body-mass outcomes with nested dam/animal/control reuse; within-study covariance and a unique independent study/outcome vector unavailable',
'dat.bornmann2007':'multiple grant-award strata; single binary endpoint, no paired outcome vector/covariance',
'dat.bourassa1996':'handedness/eye-dominance cross-tabulations estimate one association per sample, not multiple outcome effects',
'dat.cannon2006':'six correlated binary endpoints; marginal event counts do not identify within-study cross-endpoint covariances; no documented correlation assumption',
'dat.chiarito2020':'multiple binary cardiovascular endpoints; joint event counts/covariances not supplied',
'dat.collins1985a':'bleeding, operation and death endpoints have marginal counts only; no cross-endpoint covariance or documented correlation assumption',
'dat.collins1985b':'pregnancy/perinatal endpoints with different follow-up populations; joint sampling covariance unavailable',
'dat.crede2010':'attendance correlations for course grades/GPA; cross-outcome correlations needed for sampling covariance are absent',
'dat.curtin2002':'treatment arms for one blood-pressure endpoint; corr is repeated/crossover design information, not a second outcome vector',
'dat.curtis1998':'single plant-mass outcome with species/treatment moderators and repeated papers; no paired outcome covariance',
'dat.dagostino1998':'multiple cold-symptom outcomes and scales; joint continuous/binary sampling covariances unavailable',
'dat.gibson2002':'effects on a single endpoint represented as continuous or dichotomized outcomes across studies; no paired covariance',
'dat.huber2000':'individual participant recurrence endpoint; would require a new first-stage paired effect definition',
'dat.karner2014':'multiple binary and continuous COPD endpoints; within-study cross-endpoint covariance unavailable',
'dat.knapp2017':'planning and IQ SMDs with shared groups and repeated tasks; cross-outcome sampling covariance not supplied',
'dat.konstantopoulos2011':'one school achievement effect nested in districts; not unique paired outcomes per study',
'dat.lehmann2018':'attractiveness effects from mixed parallel/repeated-measures designs; RM_r is design correlation, not paired-effect covariance',
'dat.lim2014':'separate correlation collections with phylogenetic trees; no paired study-level outcomes with known within-study covariance',
'dat.linde2015':'network of antidepressants with multiple marginal binary endpoints; endpoint covariance unknown and different treatment contrasts cannot be treated as common outcomes without a new network construction',
'dat.lloyd2010':'DAS and HAQ mean changes with confidence intervals; within-study covariance not supplied and no documented numerical assumption',
'dat.lopez2019':'arm-level depression scores on multiple scales/treatments; within-study endpoint covariance unavailable and contrasts not supplied as a common outcome vector',
'dat.maire2019':'ecological time-series summaries and between-observation distance matrix; no paired effect vector with known within-study covariance',
'dat.mccurdy2020':'dependent memory effects with sample/condition replication; cross-outcome covariance and unique pairing unavailable',
'dat.metap':'collections of p-values; no paired effect estimates and covariance matrices',
'dat.moura2021':'assortative-mating correlations with phylogenetic dependence; cross-outcome sampling covariance unavailable',
'dat.nissen2007':'infarction and death marginal counts only; joint sampling covariance unknown',
'dat.riley2003':'OS and DFS logHRs; within-study correlations are unknown and installed example supplies no numerical assumption; page has no missing-covariance/rho-estimation mode',
'dat.tannersmith2016':'multiple longitudinal motivation/crime effects per study; no known within-study covariance or unique paired outcome types',
'dat.tian2009':'network arms with deaths and infarctions; marginal counts lack cross-endpoint covariance',
'dat.white2020':'multiple signal/quality correlations with species/sample dependence; no full correlation matrices for sampling covariance',
'dat.yusuf1985':'separate beta-blocker comparisons and outcome tables; no documented joint covariance/pairing',
}
network={'dat.baker2009','dat.dogliotti2014','dat.dong2013','dat.franchini2012','dat.gurusamy2011','dat.hasselblad1998','dat.linde2016','dat.pagliaro1992','dat.senn2013','dat.stowe2010','dat.woods2010'}
ledger=[]
for x in inv:
 key=(x['package'],x['name']);n=used[key]
 reason=('supplied paired effects/covariance or documented sampling-covariance construction; all bivariate outcome pairs included; incomplete rows recorded separately' if n else reasons.get(x['name'], 'single endpoint treatment network in arm/contrast format; no common paired-outcome vector supplied; full NMA contrast construction outside this bivariate-outcome validation' if x['name'] in network else f"{x['title']}: installed schema contains one effect/endpoint per observation, or its raw-data inputs, and no second labeled effect with known sampling covariance"))
 doc=Path('documentation')/f"{x['package']}-{x['name']}.txt"
 if not doc.exists() and x['name']=='dat.berkey1998r':doc=Path('documentation/metadat-dat.berkey1998.txt')
 ledger.append(dict(package=x['package'],dataset=x['name'],title=x['title'],status='included' if n else 'excluded',configurations=n,reason=reason,documentation=doc.as_posix(),columns='; '.join(','.join(o['columns'] or []) for o in x['objects'])))
write('dataset-ledger.csv',ledger)
R={r['id']:r for r in read('reference.json')};rows=[]
for c in corpus:
 accepted=c['accepted'] if isinstance(c['accepted'],list) else [c['accepted']]
 rows.append(dict(id=c['id'],package=c['package'],dataset=c['dataset'],outcomes=' + '.join(c['outcomes']),estimator='REML',between_study='unstructured',covariance=c['covariance'],recipe=c['recipe'],rows=len(c['studies']),accepted=len(accepted),omitted=len(c['studies'])-len(accepted),reference_status=R[c['id']]['status'],reference_reason=R[c['id']].get('reason',''),input_sha256=hashlib.sha256(json.dumps(c['studies'],sort_keys=True,separators=(',',':')).encode()).hexdigest()))
write('configuration-ledger.csv',rows)
refusals=[]
for variant in ['original','patched']:
 file=Path(f'app-{variant}.json')
 if not file.exists():continue
 for a in read(file):
  r=R[a['id']]
  if r['status']!='ok' or not a.get('output') or a.get('error'):
   refusals.append(dict(variant=variant,id=a['id'],reference_status=r['status'],reference_reason=r.get('reason',''),app_status='error' if a.get('error') else 'ok' if a.get('output') else 'refused',app_reason=a.get('error') or a['headline']))
 for a in read(f'focused-{variant}.json') if Path(f'focused-{variant}.json').exists() else []:
  if a['status']=='refused' or not a.get('output') or a.get('error'):refusals.append(dict(variant=variant,id='focused::'+a['id'],reference_status=a['status'],reference_reason='input contract: empty/singleton or invalid covariance/outcomes',app_status='error' if a.get('error') else 'ok' if a.get('output') else 'refused',app_reason=a.get('error') or a.get('headline','')))
write('refusal-ledger.csv',refusals)
print(f'LEDGERS: {len(ledger)} candidates; {sum(x["status"]=="included" for x in ledger)} included; {len(rows)} unique configurations')
