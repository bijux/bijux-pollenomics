# Pure conditional-algebra controls; does not invoke physical quadrature.
args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 1L) stop("Usage: test_physical_windows.R DRIVER_R")
source(args[1], local = TRUE)

same <- function(actual, expected, tolerance = 2e-14) {
  if (!identical(dim(actual), dim(expected)) || length(actual) != length(expected) ||
      any(!is.finite(actual)) || any(abs(actual - expected) > tolerance)) {
    stop("Independent controlled conditional moment differs")
  }
}
refuses <- function(thunk) {
  result <- tryCatch({ thunk(); FALSE }, error = function(error) TRUE)
  if (!isTRUE(result)) stop("Expected invalid-input refusal")
}

result <- physical_window_moments(c(10, 30), c(2, 1), c(0.5, 0.5), c(0.2, 0.1))
sign_matrix <- matrix(c(1, -1, -1, 1), nrow = 2)
same(result$conditional_cover, c(1, 6) / 7)
same(result$direct_pollen_panel_fraction, c(1, 3) / 4)
# Hand calculation: count contrast variance 120/245^2, PPE 18/245^2.
same(result$counting_covariance, 120 / 60025 * sign_matrix)
same(result$assumed_ppe_covariance, 18 / 60025 * sign_matrix)
same(result$total_conditional_covariance, 138 / 60025 * sign_matrix)
same(result$conditional_standard_error, rep(sqrt(138) / 245, 2))
scaled <- physical_window_moments(c(30, 90), c(2, 1), c(0.5, 0.5), c(0.2, 0.1))
same(scaled$conditional_cover, result$conditional_cover)
same(scaled$counting_covariance, result$counting_covariance / 3)
same(scaled$assumed_ppe_covariance, result$assumed_ppe_covariance)
common <- physical_window_moments(c(10, 30), c(4, 2), c(0.25, 0.25), c(0.4, 0.2))
for (name in names(result)) same(common[[name]], result[[name]])
boundary <- physical_window_moments(c(0, 40), c(2, 1), c(0.5, 0.5), c(0.2, 0.1))
same(boundary$conditional_cover, c(0, 1))
same(boundary$total_conditional_covariance, matrix(0, 2, 2))
refuses(function() physical_window_moments(c(0, 0), c(2, 1), c(0.5, 0.5), c(0.2, 0.1)))
refuses(function() physical_window_moments(c(-1, 30), c(2, 1), c(0.5, 0.5), c(0.2, 0.1)))
refuses(function() physical_window_moments(c(1.5, 30), c(2, 1), c(0.5, 0.5), c(0.2, 0.1)))
refuses(function() physical_window_moments(c(10, 30), c(0, 1), c(0.5, 0.5), c(0.2, 0.1)))
refuses(function() physical_window_moments(c(10, 30), c(2, 1), c(0, 0.5), c(0.2, 0.1)))
refuses(function() physical_window_moments(c(10, 30), c(2, 1), c(0.5, 0.5), c(-0.2, 0.1)))
refuses(function() physical_window_moments(c(10, 30), c(2, 1), c(0.5), c(0.2, 0.1)))
refuses(function() physical_window_numbers(c("1", "NA")))
refuses(function() physical_window_numbers(c("1", "1e999")))
if (physical_window_axis(c("1", "1"), 2L)) stop("Duplicate taxon index accepted")
if (physical_window_axis(c("2", "1"), 2L)) stop("Reordered taxon index accepted")
cat("Conditional moment/alignment controls passed; no physical tuples evaluated.\n")
