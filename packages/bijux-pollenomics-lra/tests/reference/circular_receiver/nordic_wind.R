# Independent Nordic wind scalar reference; unchanged receiver tolerances and budget.
# A completed diagnostic is not scientific acceptance of any refused quadrature.

diagnostic_text <- function(value) {
  if (is.null(value) || !length(value)) return("")
  if (is.numeric(value)) return(paste(sprintf("%.17g", value), collapse = ","))
  paste(as.character(value), collapse = " | ")
}

diagnostic_install_refusal_capture <- function(reference, state) {
  original <- reference$receiver_reference_refuse
  if (!is.function(original)) stop("Missing original typed refusal function")
  reference$receiver_reference_refuse <- function(code, message) {
    frame <- parent.frame()
    fields <- c("index", "left", "right", "coefficient", "exponent", "boundaries",
                "total", "estimated_error", "subdivisions")
    details <- lapply(fields, function(name) {
      if (exists(name, envir = frame, inherits = FALSE)) {
        diagnostic_text(get(name, envir = frame, inherits = FALSE))
      } else ""
    })
    names(details) <- fields
    details$reason_code <- diagnostic_text(code)
    details$original_refusal_message <- diagnostic_text(message)
    for (name in c("value", "abs.error", "subdivisions", "message")) {
      value <- if (exists("segment", envir = frame, inherits = FALSE)) {
        get("segment", envir = frame, inherits = FALSE)[[name]]
      } else NULL
      details[[paste0("integrate_", name)]] <- diagnostic_text(value)
    }
    state$last_refusal <- details
    # Preserve the original error class/code/message; no fallback value is returned.
    original(code, message)
  }
  invisible(reference)
}

diagnostic_request <- function(reference, row, state) {
  state$last_refusal <- NULL
  state$warnings <- character()
  original_fields <- c("receiver_radius_m", "source_inner_radius_m", "regional_extent_m",
    "fall_speed_m_s", "empirical_diffusion_coefficient", "turbulence_parameter", "wind_speed_m_s")
  values <- lapply(row[original_fields], function(x) as.double(x[1]))
  names(values) <- c("receiver_radius_m", "inner_radius_m", "outer_radius_m",
    "fall_speed_m_s", "diffusion_coefficient", "turbulence_parameter", "wind_speed_m_s")
  result <- tryCatch(withCallingHandlers(
    do.call(reference$circular_receiver_annulus_reference, c(values, list(
      absolute_tolerance = 1e-11, relative_tolerance = 1e-10, quadrature_limit = 1000L
    ))), warning = function(w) {
      state$warnings <- c(state$warnings, conditionMessage(w))
      invokeRestart("muffleWarning")
    }), error = function(error) error)
  output <- c(list(tuple_id = row$tuple_id[1]), lapply(row[original_fields], function(x) x[1]))
  output$status <- "completed_compensated_reference"
  output$error_class <- output$reason_code <- output$error_message <- ""
  for (name in c("factor", "raw_factor", "estimated_absolute_error", "tail_mass_bound",
                 "subdivisions_used")) output[[name]] <- ""
  if (inherits(result, "error")) {
    known <- c("invalid_parameter", "invalid_geometry", "invalid_budget", "survival_unresolved",
      "point_unresolved", "geometry_transform_unresolved", "distance_unresolved",
      "overlap_unresolved", "quadrature_not_converged", "response_invalid")
    output$status <- if (inherits(result, "circular_receiver_reference_error") &&
      length(result$reason_code) == 1L && result$reason_code %in% known) "refused" else "fatal"
    output$error_class <- paste(class(result), collapse = ",")
    output$reason_code <- diagnostic_text(result$reason_code)
    output$error_message <- conditionMessage(result)
  } else {
    for (name in c("factor", "raw_factor", "estimated_absolute_error", "tail_mass_bound",
                   "subdivisions_used")) output[[name]] <- diagnostic_text(result[[name]])
  }
  output$warnings <- diagnostic_text(state$warnings)
  detail <- state$last_refusal
  if (!is.null(detail)) detail <- c(list(tuple_id = row$tuple_id[1]), detail)
  list(row = output, detail = detail)
}

diagnostic_main <- function(args = commandArgs(trailingOnly = TRUE)) {
  if (length(args) != 4L) stop(
    "Usage: reference_factors.R PHYSICAL_WINDOWS_R RECEIVER_R EXPORTED_TUPLES ABSENT_OUTPUT"
  )
  shared <- new.env(parent = globalenv())
  sys.source(args[1], envir = shared)
  check <- shared$physical_window_require
  columns <- c("tuple_id", "receiver_radius_m", "source_inner_radius_m", "regional_extent_m",
    "fall_speed_m_s", "empirical_diffusion_coefficient", "turbulence_parameter", "wind_speed_m_s")
  tuples <- shared$physical_window_read(args[3], columns)
  check(nrow(tuples) == 46L && identical(tuples$tuple_id, sprintf("wind-tuple:%d", 1:46)),
        "Exact exported ordered46 tuple identities required")
  for (name in columns[-1]) shared$physical_window_numbers(tuples[[name]], 0)
  check(!file.exists(args[4]) && dir.exists(dirname(args[4])), "Fresh owned output required")
  reference <- new.env(parent = globalenv())
  sys.source(args[2], envir = reference)
  check(is.function(reference$circular_receiver_annulus_reference), "Missing original reference")
  state <- new.env(parent = emptyenv())
  diagnostic_install_refusal_capture(reference, state)
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
    attempt <- diagnostic_request(reference, tuples[index, , drop = FALSE], state)
    rows[[length(rows)+1L]] <- attempt$row
    if (!is.null(attempt$detail)) details[[length(details)+1L]] <- attempt$detail
    fatal <- identical(attempt$row$status, "fatal")
  }
  check(length(rows) == 46L, "Diagnostic request population incomplete")
  check(dir.create(args[4]), "Cannot create diagnostic output")
  write <- function(value, name) utils::write.table(value, file.path(args[4], name),
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
    file.path(args[4], "scope.txt"))
  if (fatal) quit(save = "no", status = 1L)
  invisible(rows)
}

if (sys.nframe() == 0L) diagnostic_main()
