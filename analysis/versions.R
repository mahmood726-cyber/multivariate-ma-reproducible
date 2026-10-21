# R and package versions recorded in every validation-bundle R log (bench/*.log). Any difference refuses the run.
REQUIRED <- c(R='4.6.0', mvmeta='1.0.3', mixmeta='1.2.2', metafor='5.2.1', metadat='1.6.0', jsonlite='2.0.0')
installed_versions <- function(pkgs=names(REQUIRED)[-1]) {
 c(R=as.character(getRversion()), vapply(pkgs, function(p) tryCatch(as.character(packageVersion(p)), error=function(e) 'MISSING'), ''))
}
check_versions <- function(actual, expected=REQUIRED) {
 if(!identical(actual, expected)) stop('Wrong R/package versions. Required: ', paste(names(expected), expected, collapse=', '),
  '. Found: ', paste(names(actual), actual, collapse=', '), call.=FALSE)
 invisible(TRUE)
}
