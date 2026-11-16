args <- commandArgs(trailingOnly=TRUE)
source(file.path(args[1], "REVEALS.R"), local=.GlobalEnv)
source(file.path(args[1], "dispersal_models.R"), local=.GlobalEnv)
output <- args[2]
# The exact upstream source programs are evaluated without installing disqover,
# loading a package dataset, or changing their wrapper validation function.
fixed_ppe <- function(n, mean, sds) mean
fixed_pollen <- function(n=1, pollen, ...) pollen
speeds <- c(0.006, 0.01, 0.024, 0.15)
rows <- list()
for (basin in c("peatland", "lake")) {
 for (diameter in c(10, 100, 2000)) {
  for (cutoff in c(1e5, 1e6, 1000001)) {
   for (speed in speeds) {
    k <- DispersalFactorK(speed, basin, diameter, "gpm neutral", cutoff)
    stopifnot(length(k)==1L)
    if (basin=="lake" && cutoff>1e6) stopifnot(is.na(k)) else stopifnot(is.finite(k), k>0)
    rows[[length(rows)+1L]] <- data.frame(basin=basin, diameter=diameter, cutoff=cutoff, speed=speed, factor=k)
   }
  }
 }
}
factors <- do.call(rbind, rows)
write.csv(factors, file.path(output, "r-deposition.csv"), row.names=FALSE)
rows <- list()
for (basin in c("peatland", "lake")) {
 for (diameter in c(10, 100, 2000)) {
  for (cutoff in c(1e5, 1e6)) {
   for (other in c(0.024, 0.15)) {
    k <- vapply(c(0.006,other), DispersalFactorK, 0.0, tBasin=basin,dBasin=diameter,dwm="gpm neutral",regionCutoff=cutoff)
    for (first_count in c(20,80)) {
     params <- data.frame(ppe=c(1,5),ppe.error=c(0,0))
     cover <- REVEALS(c(1500,first_count,100-first_count), n=2, ppes=params,
        ppefun=fixed_ppe, deposition=k, pollenfun=fixed_pollen,
        writeresults=FALSE, verbose=FALSE)$meansim
     rows[[length(rows)+1L]] <- data.frame(basin=basin,diameter=diameter,cutoff=cutoff,other_speed=other,first_count=first_count,Filipendula=cover[1],Betula=cover[2])
    }
   }
  }
 }
}
write.csv(do.call(rbind,rows), file.path(output, "r-cover.csv"), row.names=FALSE)
pollen <- data.frame(age=1500,Filipendula=20,Betula=80)
params <- data.frame(species=c("Filipendula","Betula"),fallspeed=c(0.006,0.024),ppe=c(1,5),ppe.error=0)
refusal <- tryCatch({REVEALSinR(pollen,params,"peatland",100,"gpm neutral",n=2,ppefun=fixed_ppe,pollenfun=fixed_pollen,verbose=FALSE);stop("Original wrapper unexpectedly admitted expanded fall speed")},error=function(e)conditionMessage(e))
stopifnot(grepl("fallspeed(s) too low (<0.01 m/s)", refusal, fixed=TRUE))
writeLines(refusal,file.path(output,"r-wrapper-refusal.txt"))
writeLines(c(R.version.string,R.version$platform,capture.output(sessionInfo())),file.path(output,"r-runtime.txt"))
