args <- commandArgs(trailingOnly=TRUE)
if (length(args) != 3) stop("Expected source directory, zipfR library, output directory")
library(zipfR, lib.loc=args[2])
if (as.character(packageVersion("zipfR")) != "0.6.70") stop("Expected pinned zipfR 0.6-70")
source_dir <- file.path(args[1], "run.REVEALS.files")
setwd(args[3])
for (expression in parse(file.path(source_dir,"LRA-REVEALS-release.R"))) {
 if (is.call(expression) && as.character(expression[[1]]) %in% c("<-","=") && as.character(expression[[2]]) %in% c("KPf","REVEALS")) eval(expression)
}
# Pure-function cache: original function body is preserved and is evaluated once
# per exact input tuple. No optimizer, random draw or arithmetic formula changes.
original_KPf <- KPf
cache <- new.env(parent=emptyenv())
KPf <- function(vg,u,Zmax,radius,model,dwm) {
 key <- paste(sprintf("%.17g",c(vg,u,Zmax,radius)),model,dwm,collapse="|")
 if (!exists(key,envir=cache,inherits=FALSE)) assign(key,original_KPf(vg,u,Zmax,radius,model,dwm),envir=cache)
 get(key,envir=cache,inherits=FALSE)
}
avg <- read.csv(file.path(source_dir,"av-RPP.all.landclimII.csv"),row.names=1,check.names=FALSE)
alvc <- read.csv(file.path(source_dir,"avar-RPP.all.landclimII.csv"),row.names=1,check.names=FALSE)
# Record exact R syntactic-name crosswalk; never infer a taxon match by position.
write.csv(data.frame(source=rownames(avg),prepared=make.names(rownames(avg))),"taxon-name-crosswalk.csv",row.names=FALSE)
for (grid in c("512","562")) {
 paths <- readLines(file.path(source_dir,paste0("site.list.",grid,".csv")))
 pollen <- lapply(paths,function(p) read.csv(file.path(source_dir,p),row.names=1,check.names=FALSE))
 names(pollen) <- sub("^LRAready_|\\.csv$","",paths)
 for (table in pollen) stopifnot(identical(rownames(table)[-c(1,2)],make.names(rownames(avg))))
 dir.create(grid)
 captured <- list()
 sample <- function(x,...) {
   draw <- base::sample(x,...)
   kt <- get("kt",envir=parent.frame())
   captured[[length(captured)+1L]] <<- list(bin=kt,sites=draw)
   draw
 }
 set.seed(20220912)
 started <- proc.time()
 result <- REVEALS(pollen,avg,alvc,3,100000,"gpm neutral")
 write.csv(result$Mean_V,file.path(grid,"regional-cover.csv"))
 write.csv(result$Mean_SE,file.path(grid,"regional-se.csv"))
 write.csv(result$No_sites,file.path(grid,"site-count.csv"))
 for (k in seq_along(pollen)) {
   write.csv(result$V_sites[[k]],file.path(grid,paste0("site-",k,"-cover.csv")))
   write.csv(result$SE_sites[[k]],file.path(grid,paste0("site-",k,"-se.csv")))
 }
 for (bin in unique(vapply(captured,function(x)x$bin,integer(1)))) {
   draws <- do.call(rbind,lapply(Filter(function(x)x$bin==bin,captured),function(x)x$sites))
   write.table(draws-1L,file.path(grid,paste0("bootstrap-bin-",bin,".csv")),sep=",",row.names=FALSE,col.names=FALSE)
 }
 writeLines(capture.output(proc.time()-started),file.path(grid,"timing.txt"))
 saveRDS(result,file.path(grid,"reference-output.rds"))
 cat("Completed exact author grid",grid,"\n")
}
writeLines(capture.output(sessionInfo()),"R_session_info.txt")
