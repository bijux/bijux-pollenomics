# Reuse the original source entry; time its exact reconstruction expression.
# Fixed candidate replay replaces search, not source numerical functions.
driver_args <- commandArgs(trailingOnly = TRUE)
stopifnot(length(driver_args) == 6L)
expressions <- parse(driver_args[6])
is_result <- function(x) is.call(x) && length(x) >= 3L && identical(x[[1]], as.name("<-")) &&
  identical(x[[2]], as.name("result"))
stopifnot(sum(vapply(expressions, is_result, logical(1))) == 1L)
driver_started <- proc.time()[["elapsed"]]
call_seconds <- numeric(6)
for (expression in expressions) {
  if (!is_result(expression)) {
    eval(expression, envir = .GlobalEnv)
  } else {
    setup_seconds <- proc.time()[["elapsed"]] - driver_started
    for (repetition in seq_len(6L)) {
      REPLAY_TRACE <- list()
      before <- proc.time()[["elapsed"]]
      eval(expression, envir = .GlobalEnv)
      call_seconds[repetition] <- proc.time()[["elapsed"]] - before
      products <- list(result$cover$mean, result$pollenpercentages$mean,
                       result$mBestValue, REPLAY_TRACE)
      if (repetition == 1L) reference_products <- products
      stopifnot(identical(reference_products, products), length(REPLAY_TRACE) == 8L)
    }
    after_calls <- proc.time()[["elapsed"]]
  }
}
write.csv(data.frame(call = seq_len(6L), seconds = call_seconds),
          file.path(output, "timings.csv"), row.names = FALSE)
write.csv(data.frame(setup_seconds = setup_seconds,
                     export_seconds = proc.time()[["elapsed"]] - after_calls),
          file.path(output, "stages.csv"), row.names = FALSE)
original_candidates <- CANDIDATES
refusal <- optimized_all_nonfinite_refusal(local, regional, params, rings, CANDIDATES)
CANDIDATES <- original_candidates
stopifnot(identical(refusal, "refused: all replay candidates invalid"))
writeLines(refusal, file.path(output, "all-undefined-refusal.txt"))
