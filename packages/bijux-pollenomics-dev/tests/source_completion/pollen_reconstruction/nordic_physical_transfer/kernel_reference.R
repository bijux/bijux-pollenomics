# Three new Pinus responses through the retained independent circle-overlap reference.

reference_text <- function(value) {
  if (is.numeric(value)) return(paste(sprintf("%.17g", value), collapse = ","))
  if (is.null(value)) return("")
  paste(as.character(value), collapse = " | ")
}

reference_main <- function(args = commandArgs(trailingOnly = TRUE)) {
  if (length(args) != 3L) stop("Usage: kernel_reference.R RECEIVER_R REQUESTS_TSV ABSENT_OUTPUT")
  columns <- c("tuple_id", "receiver_radius_m", "inner_radius_m", "outer_radius_m",
    "fall_speed_m_s", "diffusion_coefficient", "turbulence_parameter", "wind_speed_m_s",
    "absolute_tolerance", "relative_tolerance", "quadrature_limit")
  requests <- utils::read.delim(args[2], header = TRUE, sep = "\t", quote = "\"",
    colClasses = "character", check.names = FALSE, na.strings = NULL)
  if (!identical(names(requests), columns) || nrow(requests) != 3L || anyNA(requests)) {
    stop("Exact three-row request table required")
  }
  radii <- c(80, 69, 89)
  expected <- data.frame(tuple_id = paste0("pinus-radius:", radii),
    receiver_radius_m = as.character(radii), inner_radius_m = as.character(radii),
    outer_radius_m = "100000", fall_speed_m_s = ".031", diffusion_coefficient = ".12",
    turbulence_parameter = ".25", wind_speed_m_s = "3", absolute_tolerance = "1e-11",
    relative_tolerance = "1e-10", quadrature_limit = "1000", stringsAsFactors = FALSE)
  if (!identical(requests, expected)) stop("Ordered prospective tuple/profile mismatch")
  if (file.exists(args[3]) || !dir.exists(dirname(args[3]))) stop("Absent owned output required")
  # No replacement of reference functions or integration controls is installed.
  reference <- new.env(parent = globalenv())
  sys.source(args[1], envir = reference)
  if (!is.function(reference$circular_receiver_annulus_reference)) stop("Missing reference")
  fields <- c("factor", "raw_factor", "estimated_absolute_error", "tail_mass_bound", "method",
    "coefficient_from_parameters", "exponent", "absolute_tolerance", "relative_tolerance",
    "quadrature_limit", "subdivisions_used")
  known <- c("invalid_parameter", "invalid_geometry", "invalid_budget", "survival_unresolved",
    "point_unresolved", "geometry_transform_unresolved", "distance_unresolved",
    "overlap_unresolved", "quadrature_not_converged", "response_invalid")
  rows <- list()
  for (index in seq_len(3L)) {
    warnings <- character()
    value <- tryCatch(withCallingHandlers(
      reference$circular_receiver_annulus_reference(
        receiver_radius_m = radii[index], inner_radius_m = radii[index],
        outer_radius_m = 100000, fall_speed_m_s = .031, diffusion_coefficient = .12,
        turbulence_parameter = .25, wind_speed_m_s = 3,
        absolute_tolerance = 1e-11, relative_tolerance = 1e-10, quadrature_limit = 1000L),
      warning = function(w) {
        warnings <<- c(warnings, conditionMessage(w))
        invokeRestart("muffleWarning")
      }), error = function(error) error)
    row <- list(tuple_id = requests$tuple_id[index], status = "completed")
    for (field in fields) row[[field]] <- ""
    row$error_class <- row$reason_code <- row$error_message <- ""
    if (inherits(value, "error")) {
      row$status <- if (inherits(value, "circular_receiver_reference_error") &&
        length(value$reason_code) == 1L && value$reason_code %in% known) "refused" else "fatal"
      row$error_class <- paste(class(value), collapse = ",")
      row$reason_code <- reference_text(value$reason_code)
      row$error_message <- conditionMessage(value)
    } else {
      if (!is.list(value) || !identical(sort(names(value)), sort(fields))) {
        stop("Reference result shape changed")
      }
      for (field in fields) row[[field]] <- reference_text(value[[field]])
    }
    row$warnings <- reference_text(warnings)
    rows[[index]] <- as.data.frame(row, stringsAsFactors = FALSE)
  }
  if (!dir.create(args[3])) stop("Cannot create owned output")
  write <- function(value, name) utils::write.table(value, file.path(args[3], name),
    row.names = FALSE, quote = TRUE, sep = "\t", na = "NA")
  write(do.call(rbind, rows), "outcomes.tsv")
  write(data.frame(r_version = R.version.string, platform = R.version$platform,
    stats_version = as.character(utils::packageVersion("stats")),
    base_version = as.character(utils::packageVersion("base")), stringsAsFactors = FALSE), "runtime.tsv")
  # Refused/fatal rows remain complete receipts; the Python checker refuses agreement.
  invisible(rows)
}

if (sys.nframe() == 0L) reference_main()
