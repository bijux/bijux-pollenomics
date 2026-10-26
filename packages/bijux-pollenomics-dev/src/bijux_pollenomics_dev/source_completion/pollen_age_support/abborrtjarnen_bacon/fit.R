# Use the unmodified fixed-transition sampler and an explicit physical-state reader.
args <- commandArgs(trailingOnly = TRUE)
stopifnot(length(args) %in% c(3L, 4L))
prepare.only <- length(args) == 4L && args[4] == "prepare-only"
stopifnot(length(args) == 3L || prepare.only)
suppressPackageStartupMessages(library(rbacon, lib.loc = args[1]))
suppressPackageStartupMessages(library(coda))
stopifnot(as.character(packageVersion("rbacon")) == "4.0.2")
case <- jsonlite::read_json(args[2], simplifyVector = FALSE)
p <- case$protocol
depths <- unlist(case$depths)
sample.ids <- unlist(case$sample_ids)
controls <- do.call(rbind, lapply(case$controls, as.data.frame))
curve.dir <- paste0(normalizePath(system.file("extdata", package = "rintcal", lib.loc = args[1]), mustWork = TRUE), "/")
stopifnot(nzchar(curve.dir), length(depths) == 107L)
all.ages <- list()
all.free <- list()
chains <- list()
warnings <- character()
runtime.versions <- list(R = R.version.string, platform = R.version$platform,
  packages = lapply(c("rbacon", "rintcal", "rice", "coda", "Rcpp"),
    function(name) list(package = name, version = as.character(packageVersion(name)))))
options(digits = 17)

withCallingHandlers({
  for (i in seq_along(p$execution$seeds)) {
    seed <- p$execution$seeds[[i]]
    jsonlite::write_json(list(chains = chains, active_seed = seed,
      active_stage = "source_preparation", warnings = warnings, runtime = runtime.versions),
      file.path(args[3], "fit-summary.json"), auto_unbox = TRUE, pretty = TRUE)
    chain.dir <- file.path(args[3], paste0("seed-", seed))
    stopifnot(!file.exists(chain.dir))
    dir.create(file.path(chain.dir, "ABBO"), recursive = TRUE)
    write.csv(controls[, c("sample_id", "age", "error", "depth", "cc")],
      file.path(chain.dir, "ABBO", "ABBO.csv"), row.names = FALSE)
    # The source's run=FALSE branch plots priors only; a null device prevents
    # an unowned Rplots.pdf and no raw-column age helper is invoked.
    grDevices::pdf(file = NULL)
    set <- Bacon("ABBO", coredir = paste0(chain.dir, "/"), run = FALSE,
      remember = FALSE, ask = FALSE, suggest = FALSE, accept.suggestions = FALSE,
      thick = 5, d.min = 648, d.max = 896, d.by = 1, add.bottom = TRUE,
      seed = seed, th0 = unlist(p$model$initial_top_age_pairs[[i]]),
      acc.shape = 1.5, acc.mean = (8000 + 52) / (880.5 - 648),
      mem.mean = 0.3, mem.strength = 20, normal = FALSE, t.a = 3, t.b = 4,
      delta.R = 0, delta.STD = 0, cc = 1, cc1 = "IntCal20", cc.dir = curve.dir,
      postbomb = 0, youngest.age = -202, oldest.age = 1e6,
      hiatus.depths = NA, boundary = NA, slump = numeric(0), BCAD = FALSE,
      ssize = 4000, burnin = 500, plot.pdf = FALSE, save.elbowages = FALSE,
      save.info = FALSE, verbose = FALSE)
    grDevices::dev.off()
    # The source's nonempty th0 formal is not assigned to its returned object.
    # Populate the declared starts and use its unmodified native-input writer.
    set$th0 <- as.numeric(unlist(p$model$initial_top_age_pairs[[i]]))
    rbacon:::write.Bacon.file(set, save.info = FALSE)
    stopifnot(all(is.na(set$hiatus.depths)), length(set$slump) == 0L,
      !isTRUE(set$BCAD))
    line <- grep("^Bacon 0:", readLines(set$bacon.file), value = TRUE)
    stopifnot(length(line) == 1L)
    tokens <- trimws(strsplit(gsub(";", "", sub("^[^:]*:", "", line)), ",")[[1]])
    native <- as.numeric(tokens[-1])
    stopifnot(tokens[1] == "FixT", length(native) == 12L,
      native[1] == 51, native[10] == 648, native[11] == 903,
      (native[11] - native[10]) / native[1] == 5,
      native[12] == seed,
      identical(native[4:5], as.numeric(unlist(p$model$initial_top_age_pairs[[i]]))))
    native.path <- paste0(set$prefix, ".out")
    stopifnot(file.exists(native.path), file.info(native.path)$size == 0)
    if (prepare.only) {
      jsonlite::write_json(list(sections = native[1], native_top_depth_cm = native[10],
        native_bottom_depth_cm = native[11], native_seed = native[12],
        native_initial_top_age_pair = native[4:5], native_input = set$bacon.file,
        native_calibration_directory = curve.dir,
        native_output_bytes = file.info(native.path)$size, model_fits = 0),
        file.path(args[3], "prepared-contract.json"), auto_unbox = TRUE, pretty = TRUE)
      cat("source preparation passed; model_fits=0\n")
      quit(save = "no", status = 0)
    }
    cat("starting native chain seed=", seed, " sections=", set$K, "\n", sep = "")
    jsonlite::write_json(list(chains = chains, active_seed = seed,
      active_stage = "native_sampling", warnings = warnings, runtime = runtime.versions),
      file.path(args[3], "fit-summary.json"), auto_unbox = TRUE, pretty = TRUE)
    rbacon:::bacon(set$bacon.file, native.path, 4500L, curve.dir)
    raw <- as.matrix(read.table(native.path))
    stopifnot(ncol(raw) == set$K + 3L, nrow(raw) == 7501L)
    # Equivalent to source scissors(500) followed by the fixed last-4000
    # selection. Preserve the entire original native file unchanged.
    indices <- seq.int(nrow(raw) - 4000L + 1L, nrow(raw))
    stopifnot(indices[1] == 3502L, min(indices) > 500L)
    states <- raw[indices, seq_len(set$K + 2L), drop = FALSE]
    rates <- states[, 1L + seq_len(set$K), drop = FALSE]
    w <- states[, set$K + 2L]
    stopifnot(all(is.finite(states)), all(rates > 0), all(w > 0 & w < 1))
    for (j in seq.int(set$K - 1L, 1L))
      rates[, j] <- w * rates[, j + 1L] + (1 - w) * states[, j + 1L]
    physical <- set
    physical$output <- states
    physical$output[, 1L + seq_len(set$K)] <- rates
    ages <- vapply(depths, function(d)
      Bacon.Age.d(d, set = physical, its = physical$output), numeric(4000))
    stopifnot(all(is.finite(ages)), all(ages[, -1] >= ages[, -ncol(ages)]))
    connection <- gzfile(file.path(chain.dir, "ages.csv.gz"), "wt")
    write.table(format(ages, digits = 17, trim = TRUE), connection,
      sep = ",", quote = FALSE, row.names = FALSE, col.names = sample.ids)
    close(connection)
    all.ages[[i]] <- cbind(ages, memory_section = w)
    colnames(all.ages[[i]]) <- c(sample.ids, "memory_section")
    all.free[[i]] <- cbind(states, energy = raw[indices, ncol(raw)])
    colnames(all.free[[i]]) <- c("top_age", paste0("alpha_", seq_len(set$K)), "memory_section", "energy")
    chains[[i]] <- list(seed = seed, native_output = native.path, sections = set$K,
      top_depth_cm = min(set$elbows), section_thickness_cm = set$thick,
      elbows_cm = set$elbows, raw_rows = nrow(raw), retained_rows = length(indices),
      first_native_row = min(indices), last_native_row = max(indices),
      explicit_burn_rows = 500L, source_tail_selection_removals = 3001L,
      native_save_interval_attempts = 25L * (set$K + 2L),
      native_rng_seed = native[12], native_initial_top_age_pair = native[4:5],
      native_top_depth_cm = native[10], native_bottom_depth_cm = native[11],
      requested_pollen_depth_range_cm = c(648, 896),
      deepest_control_depth_cm = 880.5,
      extrapolation_to_deepest_sample_cm = 15.5,
      extrapolation_to_native_model_bottom_cm = 22.5,
      native_parameter_header = line)
    jsonlite::write_json(list(chains = chains, active_seed = NULL,
      active_stage = "completed_chain_extraction", warnings = warnings, runtime = runtime.versions),
      file.path(args[3], "fit-summary.json"), auto_unbox = TRUE, pretty = TRUE)
  }
}, warning = function(w) { warnings <<- c(warnings, conditionMessage(w)) })

diagnose <- function(values, filename) {
  series <- do.call(coda::mcmc.list, lapply(values, coda::mcmc))
  result <- tryCatch({
    psrf <- coda::gelman.diag(series, confidence = 0.95, transform = FALSE,
      autoburnin = FALSE, multivariate = FALSE)$psrf
    ess <- coda::effectiveSize(series)
    data.frame(parameter = rownames(psrf), rhat = psrf[, 1],
      rhat_upper_95 = psrf[, 2], effective_sample_size = ess)
  }, error = function(e) list(error = conditionMessage(e)))
  if (is.data.frame(result)) {
    write.csv(result, file.path(args[3], filename), row.names = FALSE)
    return(list(status = "computed", qualified = all(is.finite(as.matrix(result[, -1]))) &&
      all(result$rhat_upper_95 < 1.05) && all(result$effective_sample_size >= 400),
      maximum_rhat_upper_95 = max(result$rhat_upper_95), minimum_effective_sample_size = min(result$effective_sample_size)))
  }
  list(status = "refused", qualified = FALSE, error = result$error)
}
summary <- list(chains = chains, warnings = warnings, runtime = runtime.versions,
  age_diagnostics = diagnose(all.ages, "age-diagnostics.csv"),
  free_parameter_diagnostics = diagnose(all.free, "free-parameter-diagnostics.csv"))
jsonlite::write_json(summary, file.path(args[3], "fit-summary.json"),
  auto_unbox = TRUE, pretty = TRUE, digits = 17, na = "null")
cat("native fit and complete diagnostics terminal\n")
