args <- commandArgs(trailingOnly = TRUE)
stopifnot(length(args) == 4L)
config <- jsonlite::fromJSON(args[1], simplifyVector = FALSE)
python <- read.csv(args[2], check.names = FALSE)
stopifnot(identical(config$schema_version, "love-objective-cases.1"))
stopifnot(identical(as.character(packageVersion("disqover")), "0.9.14"))
source_sha <- readLines(system.file("SOURCE_SHA256", package = "disqover"), warn = FALSE)[1]
stopifnot(identical(source_sha, "ea496ae82807b52c9dd3d4b39b4dfa294bfac4068e20184ce56187bff70caf5c"))
objective <- getFromNamespace("tf", "disqover")
rows <- list()
for (item in config$cases) {
  regional <- as.numeric(unlist(item$regional))
  local_k <- do.call(rbind, lapply(item$local_k, function(row) as.numeric(unlist(row))))
  local_fraction <- as.numeric(unlist(item$local_fraction))
  observed <- as.numeric(unlist(item$observed))
  ppe <- as.numeric(unlist(item$ppe))
  n <- length(regional)
  selected <- python[python$case == item$name, , drop = FALSE]
  stopifnot(nrow(selected) == 1L)
  py_candidate <- as.numeric(selected[1, paste0("c", seq_len(n))])
  set.seed(config$optimizer_seed)
  fit <- RcppDE::DEoptim(
    objective, lower = rep(0, n), upper = rep(1, n),
    vPoldepRegio = regional, mKlocal = local_k,
    vFlocal = local_fraction, vSampleLocPro = observed, ppes = ppe,
    control = RcppDE::DEoptim.control(
      trace = FALSE, NP = 10L * n, itermax = config$iterations
    )
  )$optim
  row <- data.frame(
    case = item$name, bestval = fit$bestval, iter = fit$iter,
    nfeval = fit$nfeval,
    r_at_python = objective(
      py_candidate, regional, local_k, local_fraction, observed, ppe
    ),
    c1 = fit$bestmem[1], c2 = fit$bestmem[2],
    c3 = if (n == 3L) fit$bestmem[3] else NA_real_
  )
  rows[[length(rows) + 1L]] <- row
}
write.table(
  do.call(rbind, rows), file = args[3], sep = ",", row.names = FALSE,
  col.names = TRUE, quote = FALSE, na = "", eol = "\n"
)
writeLines(trimws(capture.output(sessionInfo()), which = "right"), args[4])
