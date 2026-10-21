source('r_session.R')
corpus<-jsonlite::fromJSON('corpus.json',simplifyVector=FALSE)
for(nm in c('remlprof.fn','remlprof.gr','par2Psi','initpar','glsfit'))writeLines(capture.output(print(get(nm,asNamespace('mvmeta')))),file.path('documentation',paste0('mvmeta-',nm,'-source.txt')))
rd<-tools::Rd_db('metafor');for(nm in c('rma.mv','rcalc','escalc'))writeLines(capture.output(tools::Rd2txt(rd[[paste0(nm,'.Rd')]])),file.path('documentation',paste0('metafor-',nm,'.txt')))
matrows<-function(M)lapply(seq_len(nrow(M)),function(i)unname(M[i,]))
out<-list()
for(c in corpus) {
 id<-c[['id']]; ss<-c[['studies']][unlist(c[['accepted']])];k<-length(ss);warnings<-character()
 r<-tryCatch(withCallingHandlers({
  if(k<2)stop('Enter >= 2 studies.')
  Y<-do.call(rbind,lapply(ss,function(s)unlist(s[['y']])));S<-lapply(ss,function(s)do.call(rbind,lapply(s[['S']],unlist)))
  if(any(vapply(S,function(s)min(eigen(s,symmetric=TRUE,only.values=TRUE)[['values']])<=0,logical(1))))stop('Within-study covariance must be positive definite.')
  # mvmeta uses analytic-gradient BFGS. Repeated starts are independent of app output.
  fits<-list();start<-diag(pmax(apply(Y,2,var)-colMeans(t(vapply(S,diag,numeric(2)))),1e-4))
  for(g in list(NULL,start,start*.1,start*10)) {
   f<-tryCatch(mvmeta::mvmeta(Y~1,S=S,method='reml',bscov='unstr',control=list(maxiter=10000,reltol=1e-13,initPsi=g,optim=list(maxit=10000,reltol=1e-13))),error=function(e)NULL)
   if(!is.null(f)&&isTRUE(f[['converged']]))fits[[length(fits)+1L]]<-f
  }
  if(!length(fits))stop('mvmeta did not converge')
  f<-fits[[which.max(vapply(fits,function(x)as.numeric(logLik(x)),0))]]
  mu<-unname(as.numeric(coef(f)));CV<-unname(vcov(f));G<-unname(f[['Psi']]);se<-sqrt(diag(CV))
  raw<-list(mu=mu,muVcov=matrows(CV),G=matrows(G),logLik=as.numeric(logLik(f)))
  # mvmeta omits the metafor +.5*log|X'X| REML normalization; balanced two outcomes add log(k).
  ll<-as.numeric(logLik(f))+log(k);adjudication<-'none'
  Xlist<-rep(list(diag(2)),k);ylist<-lapply(seq_len(k),function(i)Y[i,]);nalist<-rep(list(c(FALSE,FALSE)),k)
  reml_at<-function(g) {
   # Evaluate the installed package likelihood using its fixed-Psi parametrization.
   get('remlprof.fn',asNamespace('mvmeta'))(numeric(),Xlist,ylist,S,nalist,2,k,1,2*k,'fixed',list(Psifix=g))
  }
  zero<-matrix(0,2,2);ff<-mvmeta::mvmeta(Y~1,S=S,method='fixed');mu0<-as.numeric(coef(ff));C0<-vcov(ff)
  W<-lapply(S,solve);score<-Reduce('+',lapply(seq_len(k),function(i) {w<-W[[i]];wr<-w%*%(Y[i,]-mu0);w-w%*%C0%*%w-tcrossprod(wr)}))
  if(min(eigen(score,symmetric=TRUE)[['values']])>=0 && reml_at(zero)>=as.numeric(logLik(f))-1e-12*max(1,abs(as.numeric(logLik(f))))) {G<-zero;adjudication<-'zero covariance score positive semidefinite; installed REML likelihood confirms boundary'}
  if(k==2) {
   delta<-Y[1,]-Y[2,];q<-as.numeric(crossprod(delta,solve(S[[1]]+S[[2]],delta)))
   G<-if(q>1) .5*(1-1/q)*tcrossprod(delta) else zero
   adjudication<-'two-study exact constrained REML covariance; package GLS and profile likelihood; raw mvmeta retained'
  }
  if(adjudication!='none') {
   ff<-mvmeta::mvmeta(Y~1,S=lapply(S,function(s)s+G),method='fixed');mu<-as.numeric(coef(ff));CV<-unname(vcov(ff));se<-sqrt(diag(CV));ll<-reml_at(G)+log(k)
  }
  list(status='ok',k=k,m=2,mu=mu,muSE=se,muVcov=matrows(CV),G=matrows(G),rho=if(all(diag(G)>0))G[1,2]/sqrt(prod(diag(G))) else NULL,logLik=ll,ciLower=mu-qnorm(.975)*se,ciUpper=mu+qnorm(.975)*se,sd=sqrt(diag(G)),converged=f[['converged']],niter=f[['niter']],startLogLik=vapply(fits,function(x)as.numeric(logLik(x)),0),raw_mvmeta=raw,adjudication=adjudication)
 },warning=function(w){warnings<<-c(warnings,conditionMessage(w));invokeRestart('muffleWarning')}),error=function(e)list(status='refused',reason=conditionMessage(e),k=k))
 r[['id']]<-id;r[['warnings']]<-unique(warnings);out[[length(out)+1L]]<-r
 write_json17(out,'reference-partial.json')
 cat(length(out),id,r[['status']],if(r[['status']]=='refused')r[['reason']] else '', '\n')
}
write_json17(out,'reference.json')
cat('REFERENCE',length(out),'configurations;',sum(vapply(out,function(x)x[['status']]=='ok',logical(1))),'fits; boundary adjudication recorded\n')
