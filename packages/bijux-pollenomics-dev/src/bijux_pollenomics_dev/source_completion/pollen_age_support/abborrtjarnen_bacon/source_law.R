# Exercise the archived helper's column interpretation without fitting a core.
args <- commandArgs(trailingOnly = TRUE)
stopifnot(length(args) == 2L, !file.exists(args[2]))
suppressPackageStartupMessages(library(rbacon, lib.loc = args[1]))
stopifnot(as.character(packageVersion("rbacon")) == "2.5.3")

# Repeated synthetic fixture rows preserve the helper's matrix shape.
set <- list(
  output = matrix(rep(c(0, 2, 10, 0.5), 2), nrow = 2, byrow = TRUE),
  hiatus.depths = NA_real_, slump = numeric(0), BCAD = FALSE,
  elbows = c(0, 5, 10), thick = 5
)
depths <- c(0, 5, 10)
raw <- vapply(depths, function(d) Bacon.Age.d(d, set = set), numeric(2))

# The native likelihood's backward recursion gives x1=.5*10+.5*2=6.
set$output[, 2] <- 0.5 * 10 + (1 - 0.5) * 2
physical <- vapply(depths, function(d) Bacon.Age.d(d, set = set), numeric(2))
stopifnot(
  identical(as.numeric(raw[1, ]), c(0, 10, 60)),
  identical(as.numeric(physical[1, ]), c(0, 30, 80)),
  identical(raw[1, ], raw[2, ]), identical(physical[1, ], physical[2, ])
)
result <- data.frame(
  depth_cm = depths, native_helper_on_raw_columns = raw[1, ],
  native_helper_on_physical_rates = physical[1, ],
  analytical_physical_age = c(0, 30, 80)
)
write.csv(result, args[2], row.names = FALSE)
cat("package=rbacon2.5.3 model_fits=0 source_law_witness=passed\n")
