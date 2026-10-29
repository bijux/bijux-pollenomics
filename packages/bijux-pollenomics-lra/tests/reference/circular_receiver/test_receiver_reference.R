# Controlled reference laws only; no field input, Python model, optimizer or fitting.
args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 2L) stop("Usage: test_receiver_reference.R SOURCE_R ABSENT_OUTPUT")
reference <- normalizePath(args[1], mustWork = TRUE)
output <- args[2]
if (file.exists(output) || !dir.exists(dirname(output))) stop("Absent output with existing parent required")
source(reference, local = TRUE)
if (!dir.create(output)) stop("Unable to create controlled output")
rows <- list()
record <- function(name, actual, expected, tolerance) {
  if (!is.finite(actual) || abs(actual - expected) > tolerance) stop(paste("Mismatch", name))
  rows[[length(rows) + 1L]] <<- data.frame(
    case = name, actual = actual, expected = expected,
    absolute_difference = abs(actual - expected), tolerance = tolerance,
    stringsAsFactors = FALSE
  )
}
factor <- function(receiver, inner, outer, fall = 0.03) {
  circular_receiver_annulus_reference(receiver, inner, outer, fall, 0.12, 0.25, 3)
}
for (fall in c(0.003, 0.03, 0.12)) {
  a <- 4 * fall / (0.25 * 3 * sqrt(pi) * 0.12)
  expected <- exp(-a * 81^(1 / 8)) - exp(-a * 500^(1 / 8))
  result <- factor(0, 81, 500, fall)
  record(paste("point", fall), result$factor, expected, 1e-15)
}
record("circle_contains", receiver_reference_overlap(2, 5, 0), 4 * pi, 1e-14)
record("circle_disjoint", receiver_reference_overlap(2, 5, 7), 0, 0)
record("circle_symmetry", receiver_reference_overlap(2, 5, 4),
       receiver_reference_overlap(5, 2, 4), 1e-14)
first <- factor(80, 81, 500)
second <- factor(80, 500, 1000)
whole <- factor(80, 81, 1000)
record("annulus_additivity", first$factor + second$factor, whole$factor, 1e-8)
# Previously exposed independent mathematical controls, not new field results.
record("exposed_inner_ring", first$factor, 0.09730993326551013, 1e-8)
record("exposed_outer_ring", second$factor, 0.027010985523778817, 1e-8)
if (first$factor <= 0 || first$factor >= 1 || second$factor <= 0 || second$factor >= 1) {
  stop("Ordinary annulus probability must lie strictly between zero and one")
}
refusals <- list()
refuse <- function(name, thunk, code) {
  result <- tryCatch({ thunk(); NULL }, error = function(error) {
    if (!inherits(error, "circular_receiver_reference_error")) stop(error)
    error
  })
  if (is.null(result) || !identical(result$reason_code, code)) stop(paste("Wrong refusal", name))
  refusals[[length(refusals) + 1L]] <<- data.frame(
    case = name, reason_code = result$reason_code, stringsAsFactors = FALSE
  )
}
refuse("receiver_outside_inner", function() factor(80, 79, 500), "invalid_geometry")
refuse("empty_annulus", function() factor(80, 80, 80), "invalid_geometry")
refuse("nonfinite_outer", function() factor(80, 80, Inf), "invalid_parameter")
refuse("zero_fall", function() factor(80, 80, 500, 0), "invalid_parameter")
refuse("logical_radius", function() factor(TRUE, 80, 500), "invalid_parameter")
refuse("invalid_budget", function() circular_receiver_annulus_reference(
  80, 81, 500, 0.03, 0.12, 0.25, 3, quadrature_limit = 1L), "invalid_budget")
diagnostics <- do.call(rbind, lapply(list(first, second, whole), function(result) {
  as.data.frame(result, stringsAsFactors = FALSE)
}))
diagnostics$case <- c("inner_ring", "outer_ring", "combined_annulus")
write.table(diagnostics, file.path(output, "numerical-diagnostics.tsv"),
            row.names = FALSE, quote = TRUE, sep = "\t")
write.table(do.call(rbind, rows), file.path(output, "scalar-controls.tsv"),
            row.names = FALSE, quote = TRUE, sep = "\t")
write.table(do.call(rbind, refusals), file.path(output, "refusals.tsv"),
            row.names = FALSE, quote = TRUE, sep = "\t")
writeLines(c(
  "Source-only controlled numerical reference; no field reconstruction or original-author-R claim.",
  "Nine mathematical checks and six typed refusal cases; results exist only after actual R execution.",
  "Adaptive error estimates are nonrigorous; analytic tail bound is recorded separately."
), file.path(output, "scope.txt"))
