# Observe original native likelihood ages at fixed serialized states, without fitting.
args <- commandArgs(trailingOnly = TRUE)
stopifnot(length(args) == 3L)
archive <- normalizePath(args[1], mustWork = TRUE)
library_path <- normalizePath(args[2], mustWork = TRUE)
output <- args[3]
stopifnot(!file.exists(output))
.libPaths(c(library_path, .libPaths()))
stopifnot(requireNamespace("Rcpp", quietly = TRUE))
digest <- system2("shasum", c("-a", "256", shQuote(archive)), stdout = TRUE)
stopifnot(
  length(digest) == 1L,
  strsplit(digest, " ")[[1]][1] ==
    "be84e057411fde7bfad86af9f1148285ca10adf64af18331a08703ed8f95aa42"
)
dir.create(output, recursive = TRUE)
output <- normalizePath(output, mustWork = TRUE)
source_root <- file.path(output, "upstream")
dir.create(source_root)
members <- c(paste0("rbacon/src/", c(
  "bacon.h", "cal.h", "Matrix.h", "Matrix.cpp", "ranfun.h",
  "ranfun.cpp", "gauss.cpp", "twalk.h"
)), "rbacon/R/calc.R")
stopifnot(all(members %in% untar(archive, list = TRUE)))
untar(archive, files = members, exdir = source_root)
helper_expressions <- parse(file.path(source_root, "rbacon", "R", "calc.R"))
helper_environment <- new.env(parent = baseenv())
helper_definition <- Filter(function(expression) {
  is.call(expression) && identical(expression[[1]], as.name("<-")) &&
    identical(expression[[2]], as.name("Bacon.Age.d"))
}, as.list(helper_expressions))
stopifnot(length(helper_definition) == 1L)
eval(helper_definition[[1]], envir = helper_environment)
source_helper <- helper_environment$Bacon.Age.d
source_root <- normalizePath(file.path(source_root, "rbacon", "src"))
script <- sub("^--file=", "", grep("^--file=", commandArgs(), value = TRUE))
stopifnot(length(script) == 1L)
wrapper <- file.path(dirname(normalizePath(script)), "likelihood_oracle.cpp")
old_flags <- Sys.getenv("PKG_CPPFLAGS")
Sys.setenv(PKG_CPPFLAGS = paste(old_flags, paste0("-I", shQuote(source_root))))
Rcpp::sourceCpp(wrapper, cacheDir = file.path(output, "build"), rebuild = TRUE)
Sys.setenv(PKG_CPPFLAGS = old_flags)

cases <- list(
  list(id = "two-section", top = 0, origin = 0, alpha = c(2, 10), memory = .5),
  list(id = "three-section", top = -52, origin = 648, alpha = c(2, 6, 10), memory = .5),
  list(id = "constant-innovations", top = -52, origin = 648, alpha = c(4, 4, 4), memory = .7),
  list(id = "memory-near-zero", top = 0, origin = 0, alpha = c(2, 6, 10), memory = .000001),
  list(id = "memory-near-one", top = 0, origin = 0, alpha = c(2, 6, 10), memory = .999999),
  list(id = "nondivisible-requested-range", top = -52, origin = 648,
       requested_max = 896, alpha = rep(c(2, 6, 10), length.out = 51), memory = .5)
)
comparisons <- list()
for (case in cases) {
  sections <- length(case$alpha)
  thick <- 5
  depths <- if (is.null(case$requested_max)) {
    case$origin + c(0, 2.5, 5, 7.5, sections * thick)
  } else {
    elbows <- seq(case$origin, case$requested_max, by = thick)
    elbows <- c(elbows, max(elbows) + thick)
    stopifnot(length(elbows) == sections, max(elbows) == 898)
    c(648, 650.5, 653, 893, 896, 898, 903)
  }
  state <- c(case$top, case$alpha, case$memory)
  states <- matrix(rep(state, 2), nrow = 2, byrow = TRUE)
  source <- bacon_likelihood_ages(states, depths, case$origin, thick, -202, 1e6)
  stopifnot(all(source$source_support), all(source$finite_energy),
            source$native_section_width == thick,
            source$native_top_depth == case$origin,
            source$native_model_end == case$origin + sections * thick)

  # This correction makes the helper's rate columns represent the same
  # physical accumulation history that native SetThetas uses in the likelihood.
  physical <- states
  for (index in seq.int(sections - 1L, 1L)) {
    physical[, index + 1L] <- case$memory * physical[, index + 2L] +
      (1 - case$memory) * states[, index + 1L]
  }
  set <- list(
    output = states, hiatus.depths = NA_real_, slump = numeric(0),
    BCAD = FALSE, elbows = case$origin + seq.int(0, sections) * thick,
    thick = thick
  )
  corrected <- vapply(depths, function(depth) {
    source_helper(depth, set = set, its = physical, BCAD = FALSE)
  }, numeric(2))
  raw <- vapply(depths, function(depth) {
    source_helper(depth, set = set, its = states, BCAD = FALSE)
  }, numeric(2))
  stopifnot(all(is.finite(source$ages)), max(abs(source$ages - corrected)) <= 1e-8)
  for (row in seq_len(nrow(states))) {
    comparisons[[length(comparisons) + 1L]] <- data.frame(
      case = case$id, fixture_row = row, sections = sections,
      origin_cm = case$origin, thick_cm = thick, top_age_cal_bp = case$top,
      innovations = paste(sprintf("%.17g", case$alpha), collapse = ";"),
      memory = case$memory, depth_cm = depths,
      requested_max_cm = if (is.null(case$requested_max)) max(depths) else case$requested_max,
      native_model_end_cm = source$native_model_end,
      native_section_width_cm = source$native_section_width,
      native_likelihood_age = source$ages[row, ],
      corrected_helper_age = corrected[row, ], raw_helper_age = raw[row, ]
    )
  }
}
comparison <- do.call(rbind, comparisons)
stopifnot(any(abs(comparison$native_likelihood_age - comparison$raw_helper_age) > 1))

invalid <- rbind(
  c(0, 2, 10, 0), c(0, 2, 10, 1), c(0, 2, 0, .5), c(-203, 2, 10, .5)
)
refused <- bacon_likelihood_ages(invalid, c(0, 5, 10), 0, 5, -202, 1e6)
stopifnot(!any(refused$source_support), all(is.na(refused$ages)))
refusals <- data.frame(
  case = c("zero-memory", "unit-memory", "zero-terminal-rate", "top-outside-bound"),
  source_support = refused$source_support,
  finite_energy = refused$finite_energy
)
options(digits = 17)
write.csv(comparison, file.path(output, "comparisons.csv"), row.names = FALSE)
write.csv(refusals, file.path(output, "refusals.csv"), row.names = FALSE)
maximum <- max(abs(comparison$native_likelihood_age - comparison$corrected_helper_age))
summary <- sprintf(paste0(
  '{"source_version":"4.0.2","model_fits":0,"fixture_cases":6,',
  '"comparison_rows":%d,"source_support_refusals":4,',
  '"absolute_tolerance":1e-8,"relative_tolerance":0,',
  '"maximum_native_corrected_helper_gap":%.17g,"passed":true}\n'
), nrow(comparison), maximum)
writeLines(summary, file.path(output, "summary.json"))
cat(summary)
