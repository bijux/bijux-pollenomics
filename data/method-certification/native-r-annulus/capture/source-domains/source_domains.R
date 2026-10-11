# TEST-ONLY source-domain and corrected-matrix reference; never shipped runtime.
args <- commandArgs(trailingOnly=TRUE)
out <- normalizePath(args[1]); .libPaths(c(args[2], .libPaths()))
options(digits=17, warn=1)
stopifnot(as.character(packageVersion("disqover")) == "0.9.14")
stopifnot(readLines(system.file("SOURCE_SHA256",package="disqover"))[1] == args[4])
source(args[3])
writeLines(capture.output(sessionInfo()), file.path(out,"R_session_info.txt"))
cases <- read.csv(file.path(out,"case_manifest.csv"),check.names=FALSE)
parameters <- read.csv(file.path(out,"parameters.csv"),check.names=FALSE)
CANDIDATES <- rbind(c(.2,.5,.3),c(.6,.1,.3),c(.25,.25,.5))
status <- data.frame(id=character(),status=character(),message=character())
for(i in seq_len(nrow(cases))) {
 c <- cases[i,]; id <- c$id
 tryCatch({
  p <- parameters[seq_len(c$taxa_count),,drop=FALSE]
  rings <- read.csv(file.path(out,paste0(id,"-rings.csv")))
  lp <- list(ppes=p,fallspeed=p[,c("Taxon","fallspeed")],dwm=c$method,
             dBasinRegional=300,tBasinRegional="lake",dBasinLocal=12,
             tBasinLocal="lake",tBasin="lake",error=FALSE)
  local <- data.frame(coordinate=1,Alnus=30,Betula=50,Pinus=20)[,seq_len(c$taxa_count+1),drop=FALSE]
  regional <- data.frame(coordinate=1,Alnus=60,Betula=10,Pinus=30)[,seq_len(c$taxa_count+1),drop=FALSE]
  if(c$kind == "wrapper_refusal") {
   value <- tryCatch({F("REVEALSinR")(regional,p,"lake",300,n=c$iterations,verbose=FALSE);0},
                     error=function(e) {writeLines(conditionMessage(e),file.path(out,paste0(id,"-source-error.txt")));as.numeric(grepl("dim(X) must have a positive length",conditionMessage(e),fixed=TRUE))})
  } else if(c$kind == "forward") {
   k <- F("calK")(rings,lp)
   cover <- as.numeric(unlist(c[,c("cover0","cover1","cover2")]))
   frac <- rings$terrestrial/rings$ring; j <- c$count; tail <- (j+1):nrow(rings)
   # Explicit corrected-matrix profile: axis preservation is intentional.
   background <- colSums(t(t(k[tail,,drop=FALSE]) * (cover*p$ppe))*frac[tail])
   localmass <- colSums(t(t(k[1:j,,drop=FALSE]) * (c(.2,.5,.3)*p$ppe))*frac[1:j])
   total <- localmass+background
   value <- c(as.numeric(k),background,total/sum(total))
  } else {
   regional_function <- if(c$taxa_count==1) function(...)data.frame(coordinate=1,Alnus.mean=100) else fixed_reveals
   CANDIDATES <- if(c$taxa_count==1)matrix(1,nrow=1,ncol=1) else rbind(c(.2,.5,.3),c(.6,.1,.3),c(.25,.25,.5))
   if(c$kind=="analytical") {
    result <- clone_with("LOVEr",list(REVEALSinR=regional_function))(local,regional,lp,rings,c$count,repeats=2)
    value <- c(as.numeric(result$Mean),as.numeric(result$SD))
   } else {
    result <- with_binding("RcppDE","DEoptim",replay_de,clone_with("LOVEoptim",list(REVEALSinR=regional_function,rmultinom=fixed_multinomial))(local,regional,lp,rings,c$count,repeats=1))
    value <- c(as.numeric(result$cover$mean),as.numeric(result$pollenpercentages$mean))
    if(c$kind=="ring_refusal") {
     write.csv(data.frame(value=value),file.path(out,paste0(id,"-legacy-output.csv")),row.names=FALSE)
     # R's one-row matrix drop is observed without changing the source solver.
     k<-F("calK")(rings,lp);j<-c$count;frac<-rings$terrestrial/rings$ring
     regional_result<-fixed_reveals(regional,p,"lake",300,n=1,verbose=FALSE)
     cover<-as.numeric(unlist(regional_result[,grepl("mean",names(regional_result))]))/100
     background<-colSums(t(t(k[(j+1):nrow(rings),,drop=FALSE])*(cover*p$ppe))*frac[(j+1):nrow(rings)])
     localmass<-colSums(t(t(k[1:j,,drop=FALSE])*(result$cover$mean[j,]*p$ppe))*frac[1:j])
     corrected<-round(100*(localmass+background)/sum(localmass+background),2)
     write.csv(data.frame(value=corrected),file.path(out,paste0(id,"-corrected-output.csv")),row.names=FALSE)
     value<-as.numeric(any(abs(corrected-result$pollenpercentages$mean[j,])>1e-4))
    }
   }
  }
  write.csv(data.frame(value=as.numeric(value)),file.path(out,paste0(id,"-R.csv")),row.names=FALSE,na="NaN")
  status[nrow(status)+1,] <- list(id,"completed","")
 },error=function(e) {status[nrow(status)+1,]<<-list(id,"error",conditionMessage(e))})
}
write.csv(status,file.path(out,"R_case_status.csv"),row.names=FALSE)
quit(status=if(all(status$status=="completed"))0L else 1L)
