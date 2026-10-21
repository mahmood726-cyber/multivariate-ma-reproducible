source('r_session.R')
corpus<-jsonlite::fromJSON('corpus.json',simplifyVector=FALSE)
results<-list()
for(index in c(1,15)) {
 c<-corpus[[index]];ss<-c[['studies']][unlist(c[['accepted']])];Y<-do.call(rbind,lapply(ss,function(s)unlist(s[['y']])));S<-lapply(ss,function(s)do.call(rbind,lapply(s[['S']],unlist)))
 d<-data.frame(yi=c(t(Y)),outcome=factor(rep(1:2,nrow(Y))),study=rep(seq_len(nrow(Y)),each=2));V<-metafor::bldiag(S)
 for(ctrl in list(list(),list(rel.tol=1e-10,x.tol=1e-10,iter.max=10000,eval.max=20000),list(optimizer='optim',optmethod='BFGS',reltol=1e-14,maxit=10000),list(optimizer='optim',optmethod='Nelder-Mead',reltol=1e-14,maxit=10000))) {
  f<-tryCatch(metafor::rma.mv(yi,V,mods=~outcome-1,random=~outcome|study,struct='UN',method='REML',data=d,control=ctrl),error=function(e)e)
  if(inherits(f,'error')) {cat(c[['id']],conditionMessage(f),'\n');next}
  r<-list(id=c[['id']],control=ctrl,mu=as.numeric(coef(f)),muSE=as.numeric(f[['se']]),G=lapply(1:2,function(i)unname(f[['G']][i,])),rho=f[['rho']],logLik=as.numeric(logLik(f)));results[[length(results)+1L]]<-r;print(r)
 }
 for(rt in c(1e-14,1e-15,1e-16)) {
  f<-mvmeta::mvmeta(Y~1,S=S,method='reml',control=list(maxiter=10000,reltol=rt));print(list(reltol=rt,mu=coef(f),G=f[['Psi']],se=sqrt(diag(vcov(f))),logLik=logLik(f),converged=f[['converged']]))
 }
}
write_json17(results,'diagnostic-reference.json')
