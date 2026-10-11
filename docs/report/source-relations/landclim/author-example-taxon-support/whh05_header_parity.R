#!/usr/bin/env Rscript
# Check how the retained author formatter's read.csv call names WHH05 columns.
args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 2) stop("Usage: whh05_header_parity.R SOURCE_ROOT OUTPUT_CSV")
root <- normalizePath(args[[1]], mustWork = TRUE)
output <- args[[2]]
author <- file.path(root, "author")
pollen <- read.csv(file.path(author, "input", "WHH05.csv"),
                   header = TRUE, check.names = FALSE)
lookup <- read.csv(file.path(author, "LANDCLIM.ALLEUROPE.taxa.LUT.080219.csv"),
                   header = TRUE, check.names = FALSE)
crosswalk <- read.csv(file.path(root, "reference", "taxon-name-crosswalk.csv"),
                      header = TRUE, check.names = FALSE)
prepared <- read.csv(file.path(author, "run.REVEALS.files", "LRAready_WHH05.csv"),
                     header = FALSE, check.names = FALSE)
source_names <- c("Fagus", "Fraxinus", "Juniperus", "Calluna", "Poaceae")
expected_targets <- c("Fagus sylvatica", "Fraxinus", "Juniperus",
                      "Calluna vulgaris", "Poaceae")
rows <- lapply(seq_along(source_names), function(i) {
  name <- source_names[[i]]
  column <- match(name, names(pollen))
  target <- lookup$RPP.LANDCLIMII[match(name, lookup$oldvar)]
  if (is.na(column) || is.na(target) || target != expected_targets[[i]]) {
    stop(paste("WHH05 parsed name or lookup changed:", name))
  }
  prepared_name <- crosswalk$prepared[match(target, crosswalk$source)]
  position <- which(prepared[[1]] == prepared_name)
  if (length(position) != 1) stop(paste("Prepared target missing:", target))
  raw_sum <- sum(as.numeric(pollen[[column]]))
  prepared_sum <- sum(as.numeric(prepared[position, -1]))
  if (raw_sum != prepared_sum) stop(paste("WHH05 count sum differs:", name))
  data.frame(r_read_name = name, source_column_index = column - 1L,
             author_target = target, raw_column_sum = raw_sum,
             prepared_target_sum = prepared_sum, sums_equal = TRUE)
})
result <- do.call(rbind, rows)
dir.create(dirname(output), recursive = TRUE, showWarnings = FALSE)
write.csv(result, output, row.names = FALSE)
cat(nrow(result), "R-parsed WHH05 names match source lookup and prepared sums\n")
