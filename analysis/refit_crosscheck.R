# Generated from bench/crosscheck.R: reads the FRESH corpus from OUT, writes to OUT.
# Statistical code is unchanged; see analysis/refit_crosscheck.diff.
source('analysis/json17.R')
c<-jsonlite::fromJSON(file.path(OUT,'corpus.json'),simplifyVector=FALSE)[[1]];ss<-c[['studies']]
Y<-do.call(rbind,lapply(ss,function(s)unlist(s[['y']])));S<-lapply(ss,function(s)do.call(rbind,lapply(s[['S']],unlist)))
d<-data.frame(yi=c(t(Y)),outcome=factor(rep(1:2,nrow(Y))),study=rep(seq_len(nrow(Y)),each=2));V<-metafor::bldiag(S)
f<-metafor::rma.mv(yi,V,mods=~outcome-1,random=~outcome|study,struct='UN',method='REML',data=d,control=list(rel.tol=1e-10,x.tol=1e-10,iter.max=10000,eval.max=20000))
matrows<-function(M)lapply(seq_len(nrow(M)),function(i)unname(M[i,]))
write_json17(list(id=c[['id']],mu=unname(as.numeric(coef(f))),muSE=unname(f[['se']]),G=matrows(unname(f[['G']])),rho=unname(f[['rho']]),logLik=as.numeric(logLik(f)),control=f[['control']]),file.path(OUT,'metafor-crosscheck.json'))
cat('METAFOR CROSSCHECK: REML UN converged; logLik',format(logLik(f),digits=17),'\n')
