# Conditional Nordic panel reference; not original-author R or field validation.

physical_window_require <- function(condition, message) {
  if (!isTRUE(condition)) stop(message, call. = FALSE)
}

physical_window_read <- function(path, columns) {
  physical_window_require(file.exists(path) && !dir.exists(path), "Missing TSV input")
  result <- utils::read.delim(
    path, header = TRUE, colClasses = "character", check.names = FALSE,
    stringsAsFactors = FALSE, na.strings = character(), comment.char = "",
    quote = "\"", fill = FALSE, blank.lines.skip = FALSE
  )
  physical_window_require(identical(names(result), columns), "TSV columns differ")
  physical_window_require(nrow(result) > 0 && !anyNA(result), "Empty/missing TSV cells")
  physical_window_require(all(nzchar(as.matrix(result))), "Empty TSV value")
  result
}

physical_window_numbers <- function(values, lower = -Inf, integer = FALSE) {
  physical_window_require(all(grepl(
    "^[+-]?([0-9]+(\\.[0-9]*)?|\\.[0-9]+)([eE][+-]?[0-9]+)?$", values
  )), "Nondecimal numeric input")
  result <- as.double(values)
  physical_window_require(all(is.finite(result) & result >= lower), "Invalid number")
  if (integer) {
    physical_window_require(all(result == floor(result) & result <= 2^53), "Invalid integer")
  }
  result
}

physical_window_axis <- function(values, size) {
  identical(physical_window_numbers(values, 1, TRUE), as.double(seq_len(size)))
}

physical_window_inputs <- function(tuples_path, scenarios_path, windows_path,
                                   expected = c(23L, 9L, 29L, 182L, 518L)) {
  tuples <- physical_window_read(tuples_path, c(
    "tuple_id", "receiver_radius_m", "source_inner_radius_m", "regional_extent_m",
    "fall_speed_m_s", "empirical_diffusion_coefficient", "turbulence_parameter",
    "wind_speed_m_s"
  ))
  scenarios <- physical_window_read(scenarios_path, c(
    "case_id", "taxon_index", "taxon", "tuple_id", "ppe", "ppe_sd", "saved_factor"
  ))
  windows <- physical_window_read(windows_path, c(
    "case_id", "window_id", "younger_cal_bp", "older_cal_bp_exclusive",
    "taxon_index", "count", "panel_count_denominator"
  ))
  physical_window_require(!anyDuplicated(tuples$tuple_id), "Duplicate tuple")
  for (name in names(tuples)[-1]) {
    tuples[[name]] <- physical_window_numbers(tuples[[name]], 0)
  }
  physical_window_require(all(
    tuples$receiver_radius_m <= tuples$source_inner_radius_m &
    tuples$source_inner_radius_m < tuples$regional_extent_m &
    tuples$fall_speed_m_s > 0 & tuples$empirical_diffusion_coefficient > 0 &
    tuples$turbulence_parameter > 0 & tuples$wind_speed_m_s > 0
  ), "Invalid physical tuple")
  physical_window_require(all(scenarios$tuple_id %in% tuples$tuple_id), "Foreign tuple")
  physical_window_require(setequal(scenarios$tuple_id, tuples$tuple_id), "Unused tuple")
  cases <- unique(scenarios$case_id)
  physical_window_require(identical(unique(windows$case_id), cases), "Case order differs")
  for (name in c("ppe", "ppe_sd", "saved_factor")) {
    scenarios[[name]] <- physical_window_numbers(scenarios[[name]], 0)
  }
  physical_window_require(all(scenarios$ppe > 0 & scenarios$saved_factor > 0 &
    scenarios$saved_factor <= 1), "Invalid PPE/factor")
  window_count <- 0L
  for (case in cases) {
    panel <- scenarios[scenarios$case_id == case, , drop = FALSE]
    n <- nrow(panel)
    physical_window_require(n >= 2 && n <= 6 &&
      physical_window_axis(panel$taxon_index, n) && !anyDuplicated(panel$taxon),
      "Invalid literal taxon axis")
    data <- windows[windows$case_id == case, , drop = FALSE]
    ids <- unique(data$window_id)
    physical_window_require(physical_window_axis(ids, length(ids)), "Window order differs")
    previous <- -Inf
    for (id in ids) {
      rows <- data[data$window_id == id, , drop = FALSE]
      physical_window_require(nrow(rows) == n &&
        physical_window_axis(rows$taxon_index, n), "Window taxon axis differs")
      for (name in c("younger_cal_bp", "older_cal_bp_exclusive", "panel_count_denominator")) {
        physical_window_require(length(unique(rows[[name]])) == 1L, "Window identity differs")
      }
      young <- physical_window_numbers(rows$younger_cal_bp[1], 0)
      old <- physical_window_numbers(rows$older_cal_bp_exclusive[1], 0)
      physical_window_require(young < old && young >= previous && old <= 11700,
                              "Invalid chronological support")
      previous <- old
      counts <- physical_window_numbers(rows$count, 0, TRUE)
      total <- physical_window_numbers(rows$panel_count_denominator[1], 1, TRUE)
      physical_window_require(sum(counts) == total, "Panel count closure differs")
      window_count <- window_count + 1L
    }
  }
  actual <- c(nrow(tuples), length(cases), nrow(scenarios), window_count, nrow(windows))
  physical_window_require(identical(as.integer(actual), as.integer(expected)),
                          "Complete physical/window population differs")
  list(tuples = tuples, scenarios = scenarios, windows = windows, cases = cases)
}

physical_window_moments <- function(counts, ppe, factors, sd) {
  n <- length(counts)
  physical_window_require(n >= 2 && all(lengths(list(ppe, factors, sd)) == n),
                          "Moment axes differ")
  physical_window_require(all(is.finite(c(counts, ppe, factors, sd))) &&
    all(counts >= 0 & counts == floor(counts)) && sum(counts) > 0 &&
    all(ppe > 0 & factors > 0 & sd >= 0), "Invalid moment inputs")
  total <- sum(counts)
  inverse_response <- 1 / (ppe * factors)
  weighted <- counts * inverse_response
  normalizer <- sum(weighted)
  physical_window_require(is.finite(normalizer) && normalizer > 0, "Invalid normalization")
  cover <- weighted / normalizer
  # Differentiate with respect to native counts, rather than closed fractions.
  count_derivative <- (diag(inverse_response, nrow = n) -
    outer(cover, inverse_response)) / normalizer
  native_count_covariance <- diag(counts, nrow = n) - tcrossprod(counts) / total
  count_covariance <- count_derivative %*% native_count_covariance %*% t(count_derivative)
  # Shared parameters are diagonal within this marginal; cross-window blocks excluded.
  ppe_derivative <- -sweep(diag(cover, nrow = n) - tcrossprod(cover), 2, ppe, "/")
  ppe_covariance <- ppe_derivative %*% diag(sd^2, nrow = n) %*% t(ppe_derivative)
  covariance <- count_covariance + ppe_covariance
  physical_window_require(all(is.finite(c(cover, count_covariance, ppe_covariance))) &&
    all(diag(covariance) >= 0), "Unresolved conditional moments")
  list(
    conditional_cover = cover, direct_pollen_panel_fraction = counts / total,
    conditional_standard_error = sqrt(diag(covariance)),
    counting_covariance = count_covariance, assumed_ppe_covariance = ppe_covariance,
    total_conditional_covariance = covariance
  )
}

physical_window_reference <- function(reference_path, inputs, output) {
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
  physical_window_require(nrow(values) == 13680L, "Complete scalar population differs")
  physical_window_require(dir.create(output), "Unable to create output")
  options(digits = 17)
  utils::write.table(diagnostics, file.path(output, "factors.tsv"),
                    row.names = FALSE, quote = TRUE, sep = "\t")
  utils::write.table(values, file.path(output, "values.tsv"),
                    row.names = FALSE, quote = TRUE, sep = "\t")
  invisible(list(factors = diagnostics, values = values))
}

physical_window_main <- function(args = commandArgs(trailingOnly = TRUE)) {
  physical_window_require(length(args) == 5L,
    "Usage: physical_windows.R REFERENCE_R TUPLES_TSV SCENARIOS_TSV WINDOWS_TSV ABSENT_OUTPUT")
  inputs <- physical_window_inputs(args[2], args[3], args[4])
  physical_window_reference(args[1], inputs, args[5])
}

if (sys.nframe() == 0L) physical_window_main()
