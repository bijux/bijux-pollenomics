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
fixed_multinomial <- function(n,size,prob) {
  # The source supplies a one-row dataframe; base rmultinom coerces prob.
  prob <- as.numeric(unlist(prob))
  matrix(rep(size*prob/sum(prob),n),ncol=n)
}
flatten_numeric <- function(x) {
  if(is.list(x))return(unlist(lapply(x,flatten_numeric),use.names=FALSE))
  as.numeric(x)
}
