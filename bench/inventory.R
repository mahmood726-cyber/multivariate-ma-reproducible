source('r_session.R')
inventory <- list()
for(pkg in c('mvmeta','mixmeta','metadat')) {
 items <- data(package=pkg)[['results',exact=TRUE]]
 rd <- tools::Rd_db(pkg)
 for(nm in names(rd)) {
  txt <- paste(capture.output(tools::Rd2txt(rd[[nm,exact=TRUE]])),collapse='\n')
  writeLines(txt,file.path('documentation',paste0(pkg,'-',sub('\\.Rd$','',nm),'.txt')))
 }
 for(i in seq_len(nrow(items))) {
  nm <- items[i,'Item']; e <- new.env(); data(list=nm,package=pkg,envir=e)
  objects <- lapply(ls(e),function(on) {
   x <- get(on,e); list(name=on,class=class(x),dim=dim(x),columns=names(x),summary=capture.output(str(x)),head=capture.output(head(x)))
  })
  inventory[[length(inventory)+1L]] <- list(package=pkg,name=nm,title=items[i,'Title'],objects=objects)
 }
}
write_json17(inventory,'inventory.json')
for(pkg in c('mvmeta','mixmeta')) for(nm in c(pkg,paste0(pkg,'.control'),paste0(pkg,'.reml'),paste0(pkg,'.fixed'),paste0(pkg,'.fit'))) {
 f <- get0(nm,envir=asNamespace(pkg)); if(!is.null(f))writeLines(capture.output(print(f)),file.path('documentation',paste0(pkg,'-',nm,'-source.txt')))
}
cat('INVENTORY',length(inventory),'datasets\n')
