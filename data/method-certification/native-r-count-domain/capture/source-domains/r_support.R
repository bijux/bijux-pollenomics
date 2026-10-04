# TEST-ONLY support. Numerical functions come from installed disqover 0.9.14.
# Replay comparisons replace random samplers and/or optimizers only; they do
# not certify convergence behaviour of the original third-party optimizers.
ns <- asNamespace("disqover")
F <- function(name) get(name, envir=ns, inherits=FALSE)
fixed_ppe <- function(n,mean,sds) mean
fixed_pollen <- function(n=1,pollen,...) matrix(100*pollen/sum(pollen),ncol=n)
fixed_reveals <- function(...) F("REVEALSinR")(...,ppefun=fixed_ppe,pollenfun=fixed_pollen)
clone_with <- function(name,bindings=list()) {
  f <- F(name); e <- list2env(bindings,parent=environment(f)); environment(f) <- e; f
}
with_binding <- function(package,name,replacement,expression) {
  e <- asNamespace(package); original <- get(name,e,inherits=FALSE)
  locked <- bindingIsLocked(name,e)
  if (locked) unlockBinding(name,e)
  assign(name,replacement,e); if (locked) lockBinding(name,e)
  on.exit({if(bindingIsLocked(name,e))unlockBinding(name,e);assign(name,original,e);if(locked)lockBinding(name,e)},add=TRUE)
  force(expression)
}
replay_de <- function(fn,lower,upper,control=list(),...) {
  stopifnot(ncol(CANDIDATES)==length(lower),all(t(t(CANDIDATES)>=lower)),all(t(t(CANDIDATES)<=upper)))
  values <- apply(CANDIDATES,1,function(x)fn(x,...));values[!is.finite(values)]<-Inf
  if(all(is.infinite(values)))stop("All replay candidates invalid")
  i <- which.min(values)
  list(optim=list(bestmem=as.numeric(CANDIDATES[i,]),bestval=values[i],iter=1))
}
REPLAY_TRACE <- list()
replay_de_traced <- function(fn,lower,upper,control=list(),...) {
  stopifnot(ncol(CANDIDATES)==length(lower),all(t(t(CANDIDATES)>=lower)),all(t(t(CANDIDATES)<=upper)))
  values <- apply(CANDIDATES,1,function(x)fn(x,...));values[!is.finite(values)]<-Inf
  if(all(is.infinite(values)))stop("All replay candidates invalid")
  i <- which.min(values)
  REPLAY_TRACE[[length(REPLAY_TRACE)+1L]] <<- c(bestval=values[i],iter=1,nfev=nrow(CANDIDATES),success=1,best_index=i)
  list(optim=list(bestmem=as.numeric(CANDIDATES[i,]),bestval=values[i],iter=1))
}
optimized_context <- function(pollen_reg,params,rings,ring_index) {
  k <- F("calK")(rings,params)
  regional <- fixed_reveals(pollen_reg,params$ppes,params$tBasinRegional,params$dBasinRegional,n=1,verbose=FALSE)
  regional_cover <- as.numeric(regional[,grepl("mean",names(regional)),drop=FALSE])/100
  regional_rows <- (ring_index+1L):nrow(rings)
  regional_fraction <- rings$terrestrial[regional_rows]/rings$ring[regional_rows]
  deposition <- colSums(t(t(k[regional_rows,,drop=FALSE])*(regional_cover*params$ppes$ppe))*regional_fraction)
  list(k=k,regional_cover=regional_cover,deposition=deposition,local_k=k[seq_len(ring_index),,drop=FALSE],local_fraction=rings$terrestrial[seq_len(ring_index)]/rings$ring[seq_len(ring_index)])
}
optimized_intermediates <- function(pollen_loc,pollen_reg,params,rings,max_ring,candidates) {
  k <- F("calK")(rings,params)
  regional <- fixed_reveals(pollen_reg,params$ppes,params$tBasinRegional,params$dBasinRegional,n=1,verbose=FALSE)
  regional_cover <- as.numeric(regional[,grepl("mean",names(regional)),drop=FALSE])/100
  observed <- as.numeric(pollen_loc[,-1,drop=FALSE])
  observed <- observed/sum(observed)
  values <- c(as.numeric(k),regional_cover)
  for(j in seq_len(max_ring)) {
    local_fraction <- rings$terrestrial[seq_len(j)]/rings$ring[seq_len(j)]
    if(sum(local_fraction)>0) {
      context <- optimized_context(pollen_reg,params,rings,j)
      objectives <- apply(candidates,1,function(candidate)F("tf")(candidate,context$deposition,context$local_k,context$local_fraction,observed,params$ppes$ppe))
      values <- c(values,context$deposition,objectives)
    }
  }
  values
}
optimized_zero_objective <- function(pollen_loc,pollen_reg,params,rings,candidates) {
  fraction <- rings$terrestrial/rings$ring
  first_active <- which(cumsum(fraction)>0)[1]
  context <- optimized_context(pollen_reg,params,rings,first_active)
  observed <- as.numeric(pollen_loc[,-1,drop=FALSE])
  observed <- observed/sum(observed)
  F("tf")(rep(0,ncol(candidates)),context$deposition,context$local_k,context$local_fraction,observed,params$ppes$ppe)
}
optimized_all_nonfinite_refusal <- function(pollen_loc,pollen_reg,params,rings,candidates) {
  fraction <- rings$terrestrial/rings$ring
  first_active <- which(cumsum(fraction)>0)[1]
  context <- optimized_context(pollen_reg,params,rings,first_active)
  observed <- as.numeric(pollen_loc[,-1,drop=FALSE])
  observed <- observed/sum(observed)
  CANDIDATES <<- matrix(0,nrow=2,ncol=ncol(candidates))
  tryCatch({
    replay_de(F("tf"),rep(0,ncol(candidates)),rep(1,ncol(candidates)),vPoldepRegio=context$deposition,mKlocal=context$local_k,vFlocal=context$local_fraction,vSampleLocPro=observed,ppes=params$ppes$ppe)
    "accepted"
  },error=function(e){
    if(!identical(conditionMessage(e),"All replay candidates invalid"))stop(e)
    "refused: all replay candidates invalid"
  })
}
fixed_multinomial <- function(n,size,prob) {
  # The source supplies a one-row dataframe; base rmultinom coerces prob.
  prob <- as.numeric(unlist(prob))
  matrix(rep(size*prob/sum(prob),n),ncol=n)
}
flatten_numeric <- function(x) {
  if(is.list(x))return(unlist(lapply(x,flatten_numeric),use.names=FALSE))
  as.numeric(x)
}
