# Independent scalar cutoff population adapter; shared diagnostic and receiver math stay unchanged.
# Sources provide functions only; the saved report is never supplied to R.

regional_cutoff_main <- function(args = commandArgs(trailingOnly = TRUE)) {
  if (length(args) != 5L) stop(
    "Usage: regional_cutoff.R PHYSICAL_WINDOWS_R RECEIVER_R NORDIC_WIND_R EXPORTED_TUPLES ABSENT_OUTPUT"
  )
  shared <- new.env(parent = globalenv())
  sys.source(args[1], envir = shared)
  adapter <- new.env(parent = globalenv())
  sys.source(args[3], envir = adapter)
  check <- shared$physical_window_require
  check(is.function(adapter$diagnostic_request) &&
    is.function(adapter$diagnostic_install_refusal_capture),
    "Missing unchanged scalar diagnostic helpers")
  columns <- c("tuple_id", "receiver_radius_m", "source_inner_radius_m", "regional_extent_m",
    "fall_speed_m_s", "empirical_diffusion_coefficient", "turbulence_parameter", "wind_speed_m_s")
  tuples <- shared$physical_window_read(args[4], columns)
  check(nrow(tuples) == 46L && identical(tuples$tuple_id, sprintf("extent-tuple:%d", 1:46)),
        "Exact exported ordered46 tuple identities required")
  for (name in columns[-1]) shared$physical_window_numbers(tuples[[name]], 0)
  extents <- as.double(tuples$regional_extent_m)
  check(all(extents %in% c(50000, 200000)) &&
    all(as.double(tuples$wind_speed_m_s) == 3) &&
    sum(extents == 50000) == 23L && sum(extents == 200000) == 23L,
    "Exact fixed-wind cutoff population required")
  check(!file.exists(args[5]) && dir.exists(dirname(args[5])), "Fresh owned output required")
  reference <- new.env(parent = globalenv())
  sys.source(args[2], envir = reference)
  check(is.function(reference$circular_receiver_annulus_reference), "Missing original reference")
  state <- new.env(parent = emptyenv())
  adapter$diagnostic_install_refusal_capture(reference, state)
  rows <- details <- list()
  fatal <- FALSE
  for (index in seq_len(nrow(tuples))) {
    if (fatal) {
      row <- rows[[length(rows)]]
      row$tuple_id <- tuples$tuple_id[index]
      for (name in columns[-1]) row[[name]] <- tuples[[name]][index]
      row$status <- "not_run_after_fatal"
      for (name in c("error_class", "reason_code", "error_message", "factor", "raw_factor",
                     "estimated_absolute_error", "tail_mass_bound", "subdivisions_used", "warnings")) row[[name]] <- ""
      rows[[length(rows)+1L]] <- row
      next
    }
    attempt <- adapter$diagnostic_request(reference, tuples[index, , drop = FALSE], state)
    rows[[length(rows)+1L]] <- attempt$row
    if (!is.null(attempt$detail)) details[[length(details)+1L]] <- attempt$detail
    fatal <- identical(attempt$row$status, "fatal")
  }
  check(length(rows) == 46L, "Diagnostic request population incomplete")
  check(dir.create(args[5]), "Cannot create diagnostic output")
  write <- function(value, name) utils::write.table(value, file.path(args[5], name),
    row.names = FALSE, quote = TRUE, sep = "\t", na = "NA")
  write(do.call(rbind, lapply(rows, as.data.frame, stringsAsFactors = FALSE)), "tuple-outcomes.tsv")
  if (length(details)) {
    write(do.call(rbind, lapply(details, as.data.frame, stringsAsFactors = FALSE)), "integration-refusals.tsv")
  } else {
    write(data.frame(tuple_id = character(), index = character(), left = character(),
      right = character(), coefficient = character(), exponent = character(), boundaries = character(),
      total = character(), estimated_error = character(), subdivisions = character(), reason_code = character(),
      original_refusal_message = character(), integrate_value = character(), integrate_abs.error = character(),
      integrate_subdivisions = character(), integrate_message = character()), "integration-refusals.tsv")
  }
  statuses <- vapply(rows, function(x) x$status, character(1))
  write(data.frame(requests = 46L, completed = sum(statuses == "completed_compensated_reference"),
    refused = sum(statuses == "refused"), fatal = sum(statuses == "fatal"),
    not_run = sum(statuses == "not_run_after_fatal"), scientific_admission = FALSE,
    original_absolute_tolerance = 1e-11, original_relative_tolerance = 1e-10,
    original_quadrature_limit = 1000L, saved_python_report_unchanged = TRUE), "summary.tsv")
  writeLines(c("Compensated receiver lens arithmetic; original integrate controls retained. No moments, scores or scientific admission.",
    "Failed integrate return fields are captured from the original caller frame before the original typed refusal is rethrown.",
    "Known typed refusals remain refused. Unknown errors stop further requests and yield native failure after retaining all46 dispositions.",
    "Successful scalar rows retain compensated-reference return values; refused quadrature is never replaced by an invented factor."),
    file.path(args[5], "scope.txt"))
  if (fatal) quit(save = "no", status = 1L)
  invisible(rows)
}

if (sys.nframe() == 0L) regional_cutoff_main()
