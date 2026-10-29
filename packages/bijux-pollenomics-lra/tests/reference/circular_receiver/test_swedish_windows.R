# Artificial complete adapter population; no physical quadrature or field data.
args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 3L) stop("Usage: test_swedish_windows.R SHARED_R ADAPTER_R ABSENT_OUTPUT")
shared <- new.env(parent = globalenv())
sys.source(args[1], envir = shared)
adapter <- new.env(parent = shared)
sys.source(args[2], envir = adapter)
check <- shared$physical_window_require
check(!file.exists(args[3]) && dir.exists(dirname(args[3])), "Fresh owned output required")
check(dir.create(args[3]), "Cannot create controlled output")
root <- args[3]
write <- function(value, name) utils::write.table(
  value, file.path(root, name), row.names = FALSE, quote = TRUE, sep = "\t"
)
profiles <- c("metadata_radius_wind_3", "half_metadata_radius_wind_3",
  "double_metadata_radius_wind_3", "metadata_radius_wind_2", "metadata_radius_wind_4",
  "metadata_radius_wind_3_zero_ppe_uncertainty")
codes <- c("ABB", "BOKE", "BUS", "TIB")
sizes <- c(2L, 3L, 2L, 2L)
counts <- c(22L, 13L, 19L, 23L)
tuples <- data.frame(tuple_id = sprintf("t%03d", 1:45), receiver_radius_m = 1,
  source_inner_radius_m = 1, regional_extent_m = 1000, fall_speed_m_s = (1:45)/1000,
  empirical_diffusion_coefficient = .12, turbulence_parameter = .25, wind_speed_m_s = 3)
scenarios <- windows <- list()
offset <- 0L
for (core in seq_along(codes)) {
  n <- sizes[core]
  for (profile in seq_along(profiles)) {
    case <- paste(codes[core], profiles[profile], sep = ".")
    for (j in seq_len(n)) {
      scenarios[[length(scenarios)+1L]] <- data.frame(case_id = case,
        taxon_index = j, taxon = paste0("controlled", j),
        tuple_id = sprintf("t%03d", offset + (min(profile, 5L)-1L)*n + j),
        ppe = 1, ppe_sd = 0, saved_factor = .5)
    }
    for (window in seq_len(counts[core])) for (j in seq_len(n)) {
      windows[[length(windows)+1L]] <- data.frame(case_id = case, window_id = window,
        younger_cal_bp = window-1L, older_cal_bp_exclusive = window,
        taxon_index = j, count = 1L, panel_count_denominator = n)
    }
  }
  offset <- offset + 5L*n
}
# The zero-PPE alternative must reuse the baseline physical tuple, not the fifth.
scenarios <- do.call(rbind, scenarios)
for (core in seq_along(codes)) {
  zero <- scenarios$case_id == paste(codes[core], profiles[6], sep = ".")
  baseline <- scenarios$case_id == paste(codes[core], profiles[1], sep = ".")
  scenarios$tuple_id[zero] <- scenarios$tuple_id[baseline]
}
windows <- do.call(rbind, windows)
write(tuples, "tuples.tsv"); write(scenarios, "scenarios.tsv"); write(windows, "windows.tsv")
paths <- file.path(root, c("tuples.tsv", "scenarios.tsv", "windows.tsv"))
inputs <- shared$physical_window_inputs(paths[1], paths[2], paths[3],
  expected = c(45L,24L,54L,462L,1002L))
refused <- tryCatch({shared$physical_window_inputs(paths[1], paths[2], paths[3],
  expected = c(44L,24L,54L,462L,1002L)); FALSE}, error = function(e) TRUE)
check(refused, "Changed population was accepted")
m <- shared$physical_window_moments(c(3,1), c(1,1), c(1,1), c(0,0))
check(max(abs(m$conditional_cover-c(.75,.25))) < 1e-15, "Controlled composition differs")
check(max(abs(m$counting_covariance - matrix(c(3,-3,-3,3)/64,2))) < 1e-15,
  "Controlled counting covariance differs")
check(all(m$assumed_ppe_covariance == 0), "Zero PPE must remain exactly zero")
stub <- file.path(root, "controlled_reference.R")
writeLines("circular_receiver_annulus_reference <- function(...) list(factor=.5, raw_factor=.5, estimated_absolute_error=0, tail_mass_bound=0, subdivisions_used=1L)", stub)
environment(adapter$swedish_window_reference) <- shared
result <- adapter$swedish_window_reference(stub, inputs, file.path(root, "products"))
check(nrow(result$factors) == 45L && nrow(result$values) == 19440L,
  "Complete adapter output population differs")
check(all(result$values$value[result$values$quantity == "assumed_ppe_covariance"] == 0),
  "Zero PPE output changed")
writeLines("Artificial complete45/24/54/462/1002 input and19440 output, changed population refusal, exact two-component moments andzeroPPE passed. No field data or quadrature.", file.path(root, "controls.txt"))
