source('r_session.R')
getdat <- function(pkg,nm) { e<-new.env();data(list=nm,package=pkg,envir=e);get(nm,e) }
corpus<-list(); rows<-list(); attempts<-list()
matrows <- function(M) lapply(seq_len(nrow(M)),function(i)unname(M[i,]))
add <- function(pkg,nm,Y,S,labels,recipe,option='supplied') {
 Y<-as.matrix(Y); labels<-as.character(labels)
 for(pair in combn(seq_len(ncol(Y)),2,simplify=FALSE)) {
  id<-paste(pkg,nm,paste(colnames(Y)[pair],collapse='+'),'REML',option,sep='::')
  # The page accepts one covariance. Canonicalize its upper-triangle value on both
  # sides before serialization (rcalc can differ by a few ulps across triangles).
  studies<-lapply(seq_len(nrow(Y)),function(i){s<-S[[i]][pair,pair,drop=FALSE];s[2,1]<-s[1,2];list(label=labels[i],y=unname(Y[i,pair]),S=matrows(s))})
  accepted<-vapply(seq_len(nrow(Y)),function(i)all(is.finite(c(Y[i,pair],S[[i]][pair,pair])))&&all(diag(S[[i]])[pair]>0),logical(1))
  for(i in seq_len(nrow(Y)))rows[[length(rows)+1L]]<<-data.frame(id=id,row=i,label=labels[i],status=if(accepted[i])'accepted' else 'omitted',reason=if(accepted[i])'two finite outcomes and covariance; positive variances' else 'page complete-pair rule: missing/nonfinite outcome or covariance, or nonpositive variance')
  corpus[[length(corpus)+1L]]<<-list(id=id,package=pkg,dataset=nm,outcomes=colnames(Y)[pair],method='REML',covariance=option,recipe=recipe,studies=studies,accepted=which(accepted))
 }
}
wide <- function(d,yn,vn,cn=NULL,rho=NULL) {
 Y<-as.matrix(d[yn]); V<-as.matrix(d[vn]); m<-ncol(Y)
 S<-lapply(seq_len(nrow(Y)),function(i) {
  z<-diag(V[i,],m)
  for(a in seq_len(m-1))for(b in (a+1):m) z[a,b]<-z[b,a]<-if(!is.null(cn))d[[cn[a,b],exact=TRUE]][i] else rho[a,b]*sqrt(V[i,a]*V[i,b])
  z
 }); list(Y=Y,S=S)
}
for(pkg in c('mvmeta','mixmeta'))for(nm in c('berkey98','fibrinogen','hsls','hyp','p53','smoking')) {
 d<-getdat(pkg,nm); option<-'supplied'; recipe<-'stored effects, variances and covariances'
 if(nm=='berkey98') {Y<-as.matrix(d[c('PD','AL')]);S<-lapply(seq_len(nrow(d)),function(i)matrix(c(d[['var_PD']][i],rep(d[['cov_PD_AL']][i],2),d[['var_AL']][i]),2))}
 if(nm %in% c('fibrinogen','hsls','smoking')) {
  ids<-switch(nm,fibrinogen=2:5,hsls=1:3,smoking=c('B','C','D')); yn<-paste0(if(nm=='smoking')'y' else 'b',ids)
  cn<-outer(ids,ids,Vectorize(function(a,b) switch(nm,fibrinogen=paste0('V_',min(a,b),'_',max(a,b)),hsls=paste0('V',min(a,b),max(a,b)),smoking=paste0('S',min(a,b),max(a,b)))))
  w<-wide(d,yn,diag(cn),cn);Y<-w[['Y']];S<-w[['S']]
 }
 if(nm=='hyp') {Y<-as.matrix(d[c('sbp','dbp')]);S<-lapply(seq_len(nrow(d)),function(i) {se<-as.numeric(d[i,c('sbp_se','dbp_se')]);outer(se,se)*matrix(c(1,rep(d[['rho']][i],2),1),2)}); recipe<-'stored SEs squared; covariance=rho*sbp_se*dbp_se'}
 if(nm=='p53') {w<-wide(d,c('y1','y2'),c('V1','V2'),rho=matrix(c(1,.95,.95,1),2));Y<-w[['Y']];S<-w[['S']];option<-'documented-rho-0.95';recipe<-'installed p53 example assumes rho=.95; page receives explicit covariance, incomplete pairs omitted'}
 add(pkg,nm,Y,S,seq_len(nrow(d)),recipe,option)
}
for(pkg in c('mixmeta','metadat')) {
 nm<-if(pkg=='mixmeta')'dbs' else 'dat.ishak2007';d<-getdat(pkg,nm)
 yn<-if(pkg=='mixmeta')c('eff_month3','eff_month6','eff_month12','eff_long') else paste0('y',1:4,'i')
 vn<-if(pkg=='mixmeta')c('var_month3','var_month6','var_month12','var_long') else paste0('v',1:4,'i')
 for(r in if(pkg=='mixmeta')c(0,.97) else .97) {
  w<-wide(d,yn,vn,rho=r^abs(outer(1:4,1:4,'-')))
  add(pkg,nm,w[['Y']],w[['S']],seq_len(nrow(d)),'installed example within-study AR1 on ordered occasions; bivariate UN REML, not full HAR model',paste0('documented-AR1-',r))
 }
}
d<-getdat('mixmeta','gliomas');times<-sort(unique(d[['time']]));stud<-unique(d[['study']])
Y<-V<-matrix(NA_real_,length(stud),4,dimnames=list(NULL,paste0('month',times)))
for(i in seq_along(stud))for(j in 1:4){idx<-which(d[['study']]==stud[i]&d[['time']]==times[j]);Y[i,j]<-d[['logOR']][idx];V[i,j]<-d[['logORvar']][idx]}
for(r in c(0,.61)) {S<-lapply(seq_len(nrow(Y)),function(i)outer(sqrt(V[i,]),sqrt(V[i,]))*r^abs(outer(1:4,1:4,'-')));add('mixmeta','gliomas',Y,S,stud,'stored logOR and variance; installed example within-study AR1',paste0('documented-AR1-',r))}
for(nm in c('dat.berkey1998','dat.berkey1998r','dat.kalaian1996')) {
 d<-getdat('metadat',nm); stud<-unique(d[[if(nm=='dat.kalaian1996')'study' else 'trial']]);on<-unique(d[['outcome']]);Y<-V<-matrix(NA_real_,length(stud),2,dimnames=list(NULL,on));S<-list()
 for(i in seq_along(stud)) {
  x<-d[d[[if(nm=='dat.kalaian1996')'study' else 'trial']]==stud[i],];ix<-match(on,x[['outcome']]);Y[i,]<-x[['yi']][ix];V[i,]<-x[['vi']][ix]
  if(nm=='dat.kalaian1996')S[[i]]<-outer(sqrt(V[i,]),sqrt(V[i,]))*matrix(c(1,.66,.66,1),2) else S[[i]]<-as.matrix(x[ix,c('v1i','v2i')])
 }
 add('metadat',nm,Y,S,stud,if(nm=='dat.kalaian1996')'installed example vcalc rho=.66; pair-complete studies' else 'stored covariance rows in original outcome order',if(nm=='dat.kalaian1996')'documented-rho-0.66' else 'supplied')
}
d<-getdat('metadat','dat.fine1993');Y<-V<-matrix(NA_real_,nrow(d),4,dimnames=list(NULL,paste0('month',c(6,12,18,24))))
for(j in 1:4) {z<-metafor::escalc(measure='OR',ai=d[[paste0('e',j,'i')]],n1i=d[['nei']],ci=d[[paste0('c',j,'i')]],n2i=d[['nci']]);Y[,j]<-z[['yi']];V[,j]<-z[['vi']]}
S<-lapply(seq_len(nrow(d)),function(i){z<-diag(V[i,]);for(a in 1:3)for(b in (a+1):4)z[a,b]<-z[b,a]<-d[['nei']][i]/(d[[paste0('e',a,'i')]][i]*(d[['nei']][i]-d[[paste0('e',b,'i')]][i]))+d[['nci']][i]/(d[[paste0('c',a,'i')]][i]*(d[['nci']][i]-d[[paste0('c',b,'i')]][i]));z})
add('metadat','dat.fine1993',Y,S,d[['study']],'escalc OR default zero-only .5 correction; documented Trikalinos-Olkin covariance; no implicit ridge','documented-covariance-raw')
Sc<-lapply(seq_along(S),function(i){z<-S[[i]];ix<-which(is.finite(diag(z)));if(length(ix)==4){eg<-eigen(z);if(any(eg[['values']]<=.08))z<-round(eg[['vectors']]%*%diag(eg[['values']]+.08)%*%t(eg[['vectors']]),12)};z})
add('metadat','dat.fine1993',Y,Sc,d[['study']],'same effects; installed example ridge .08 added to all eigenvalues if full matrix eigenvalue <=.08; study17 unchanged','documented-covariance-ridge')
d<-getdat('metadat','dat.craft2003');rr<-metafor::rcalc(ri~var1+var2|study,ni=ni,data=d);dd<-rr[['dat']];VV<-rr[['V']];on<-unique(as.character(dd[['var1.var2']]));stud<-unique(dd[['study']]);Y<-matrix(NA_real_,length(stud),length(on),dimnames=list(NULL,on));S<-list()
for(i in seq_along(stud)){ix<-match(on,as.character(dd[['var1.var2']][dd[['study']]==stud[i]]));ix<-which(dd[['study']]==stud[i])[ix];Y[i,]<-dd[['yi']][ix];S[[i]]<-VV[ix,ix]}
add('metadat','dat.craft2003',Y,S,stud,'metafor::rcalc raw correlation covariance per installed example; all 15 pairs','rcalc')
for(nm in c('dat.kearon1998','dat.rivera2025')) {
 d<-getdat('metadat',nm)
 if(nm=='dat.kearon1998'){x1<-d[['tp']];n1<-d[['np']];x2<-d[['tn']];n2<-d[['nn']]}else{x1<-d[['TP']];n1<-d[['TP']]+d[['FN']];x2<-d[['TN']];n2<-d[['TN']]+d[['FP']]}
 a<-metafor::escalc(measure='PLO',xi=x1,ni=n1,add=.5,to='all');b<-metafor::escalc(measure='PLO',xi=x2,ni=n2,add=.5,to='all');Y<-cbind(logit_sensitivity=a[['yi']],logit_specificity=b[['yi']]);S<-lapply(seq_len(nrow(d)),function(i)diag(c(a[['vi']][i],b[['vi']][i])))
 add('metadat',nm,Y,S,seq_len(nrow(d)),'escalc PLO .5 to all cells; sensitivity and specificity in disjoint case/noncase samples; covariance zero','disjoint-binomial-samples')
}
write_json17(corpus,'corpus.json');write.csv(do.call(rbind,rows),'row-ledger.csv',row.names=FALSE)
cat('CORPUS',length(corpus),'configurations from',length(unique(vapply(corpus,function(c)paste(c[['package']],c[['dataset']]),''))),'datasets\n')
