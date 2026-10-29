# All four saved Swedish fixed-basin panels; no historical or field admission.
# Source the existing qualified R reader and moment equations without changing them.

swedish_window_reference <- function(reference_path, inputs, output) {
  physical_window_require(!file.exists(output) && dir.exists(dirname(output)),
                          "Absent output with existing parent required")
  reference <- new.env(parent = baseenv())
  sys.source(reference_path, envir = reference)
  physical_window_require(is.function(reference$circular_receiver_annulus_reference),
                          "Missing qualified circular reference")
  factors <- inputs$tuples
  diagnostics <- vector("list", nrow(factors))
  for (index in seq_len(nrow(factors))) {
    x <- factors[index, ]
    result <- reference$circular_receiver_annulus_reference(
      x$receiver_radius_m, x$source_inner_radius_m, x$regional_extent_m,
      x$fall_speed_m_s, x$empirical_diffusion_coefficient, x$turbulence_parameter,
      x$wind_speed_m_s, absolute_tolerance = 1e-11,
      relative_tolerance = 1e-10, quadrature_limit = 1000L
    )
    diagnostics[[index]] <- data.frame(
      tuple_id = x$tuple_id, factor = result$factor, raw_factor = result$raw_factor,
      estimated_absolute_error = result$estimated_absolute_error,
      tail_mass_bound = result$tail_mass_bound, subdivisions_used = result$subdivisions_used
    )
  }
  diagnostics <- do.call(rbind, diagnostics)
  values <- list()
  for (case in inputs$cases) {
    panel <- inputs$scenarios[inputs$scenarios$case_id == case, , drop = FALSE]
    data <- inputs$windows[inputs$windows$case_id == case, , drop = FALSE]
    fresh <- diagnostics$factor[match(panel$tuple_id, diagnostics$tuple_id)]
    for (id in unique(data$window_id)) {
      rows <- data[data$window_id == id, , drop = FALSE]
      for (track in c("fresh_factor", "saved_factor")) {
        response <- if (track == "fresh_factor") fresh else panel$saved_factor
        moments <- physical_window_moments(
          as.double(rows$count), panel$ppe, response, panel$ppe_sd
        )
        for (name in names(moments)) {
          value <- moments[[name]]
          for (i in seq_len(nrow(panel))) {
            columns <- if (is.matrix(value)) seq_len(nrow(panel)) else 0L
            for (j in columns) {
              values[[length(values) + 1L]] <- data.frame(
                case_id = case, window_id = id, track = track, quantity = name,
                i = i, j = j, value = if (j == 0L) value[i] else value[i, j]
              )
            }
          }
        }
      }
    }
  }
  values <- do.call(rbind, values)
  physical_window_require(nrow(values) == 19440L, "Complete scalar population differs")
  physical_window_require(dir.create(output), "Unable to create output")
  options(digits = 17)
  utils::write.table(diagnostics, file.path(output, "factors.tsv"),
                    row.names = FALSE, quote = TRUE, sep = "\t")
  utils::write.table(values, file.path(output, "values.tsv"),
                    row.names = FALSE, quote = TRUE, sep = "\t")
  invisible(list(factors = diagnostics, values = values))
}

swedish_window_main <- function(args = commandArgs(trailingOnly = TRUE)) {
  if (length(args) != 6L) stop(
    "Usage: swedish_windows.R PHYSICAL_WINDOWS_R RECEIVER_R TUPLES_TSV SCENARIOS_TSV WINDOWS_TSV ABSENT_OUTPUT",
    call. = FALSE
  )
  shared <- new.env(parent = globalenv())
  sys.source(args[1], envir = shared)
  environment(swedish_window_reference) <- shared
  inputs <- shared$physical_window_inputs(
    args[3], args[4], args[5], expected = c(45L, 24L, 54L, 462L, 1002L)
  )
  swedish_window_reference(args[2], inputs, args[6])
}

if (sys.nframe() == 0L) swedish_window_main()
