cat(R.version.string, '\n'); print(.libPaths())
for(p in c('mvmeta','mixmeta','metafor','metadat','jsonlite')) cat(p, as.character(packageVersion(p)), '\n')
source('json17.R')
dir.create('documentation',showWarnings=FALSE)
