#!/usr/bin/env Rscript
# Replay the released formatter's raw-to-window calculation on its 17 sites.
args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 2) stop("Usage: author_prepared_replay.R SOURCE_ROOT OUTPUT_DIR")
root <- normalizePath(args[[1]], mustWork = TRUE)
output <- args[[2]]
author <- file.path(root, "author")
dir.create(output, recursive = TRUE, showWarnings = FALSE)
work <- file.path(output, "work")
dir.create(work, recursive = TRUE, showWarnings = FALSE)

lookup <- read.csv(file.path(author, "LANDCLIM.ALLEUROPE.taxa.LUT.080219.csv"),
                   header = TRUE, check.names = FALSE)
taxon <- read.csv(file.path(author, "run.all.taxa.100219.csv"), header = FALSE)
bins <- as.numeric(unlist(read.csv(file.path(author, "bins.csv"), header = FALSE)))
TWlookup <- read.csv(file.path(author, "TWlookup.csv"), header = TRUE)
site.info <- read.csv(file.path(author, "site.metadata.csv"), header = TRUE)
site_files <- unlist(lapply(c("512", "562"), function(grid) {
  read.csv(file.path(author, "run.REVEALS.files", paste0("site.list.", grid, ".csv")),
           header = FALSE)[[1]]
}))
if (length(site_files) != 17 || anyDuplicated(site_files)) {
  stop("Author example site lists changed")
}

replay_site <- function(filename) {
  site <- sub("^LRAready_", "", sub("\\.csv$", "", filename))
  scratch <- file.path(work, site)
  dir.create(scratch, recursive = TRUE, showWarnings = FALSE)
  poll.data <- read.csv(file.path(author, "input", paste0(site, ".csv")),
                        header = TRUE, check.names = FALSE)
  poll.harm <- setNames(poll.data,
                        lookup$RPP.LANDCLIMII[match(names(poll.data), lookup$oldvar)])
  harmonized <- file.path(scratch, "poll.harm.csv")
  write.csv(t(poll.harm), harmonized)
  poll.harm <- read.csv(harmonized, header = TRUE)
  poll.harm <- poll.harm[, colSums(is.na(poll.harm)) != nrow(poll.harm)]
  poll.agg <- aggregate(. ~ X, poll.harm, sum)
  excluded <- file.path(scratch, "rpp.excl.csv")
  write.table(poll.agg, sep = ",", file = excluded, row.names = FALSE,
              col.names = FALSE)

  data <- read.csv(excluded, header = FALSE)
  poll.joined <- merge(x = taxon, y = data, by = "V1", all = TRUE)
  poll.joined[is.na(poll.joined)] <- 0
  ready <- file.path(scratch, "ready_rpp.excl.csv")
  write.table(t(poll.joined[1:nrow(taxon), ]), ready, sep = ",",
              row.names = FALSE, col.names = FALSE)

  radius <- site.info$radius[site.info$filename == site]
  model <- site.info$model[site.info$filename == site]
  pollen.uf <- read.csv(ready, header = TRUE)
  age <- pollen.uf[, 1]
  ages.binned <- cbind(age, findInterval(age, bins))
  pollen.bound <- as.data.frame(cbind(ages.binned[, 2], pollen.uf))
  names(pollen.bound)[1] <- "bins"
  poll.ready <- aggregate(. ~ bins, pollen.bound, sum)
  TW.code <- as.data.frame(poll.ready[, 1])
  TW.code[] <- TWlookup$class[match(poll.ready[, 1], TWlookup$TW)]
  poll.ready3 <- cbind(TW.code, radius = radius, model = model,
                       poll.ready[, 3:ncol(poll.ready)])
  names(poll.ready3)[1] <- "TW"
  TWcols <- as.data.frame(TWlookup$class)
  names(TWcols)[1] <- "TW"
  poll.final <- merge(x = TWcols, y = poll.ready3, by = "TW", all = TRUE)
  poll.final[is.na(poll.final)] <- 0
  generated <- file.path(scratch, filename)
  write.table(t(poll.final[1:25, ]), generated, sep = ",",
              row.names = TRUE, col.names = FALSE)

  reference <- file.path(author, "run.REVEALS.files", filename)
  expected <- read.csv(reference, header = FALSE, check.names = FALSE)
  actual <- read.csv(generated, header = FALSE, check.names = FALSE)
  same_shape <- identical(dim(expected), dim(actual))
  matched <- if (same_shape) sum(as.matrix(expected) == as.matrix(actual)) else NA_integer_
  cells <- if (same_shape) length(as.matrix(expected)) else NA_integer_
  data.frame(site = site, sample_rows = nrow(poll.data),
             prepared_rows = nrow(actual), prepared_columns = ncol(actual),
             matched_cells = matched, compared_cells = cells,
             cell_equal = same_shape && matched == cells,
             byte_equal = identical(readBin(reference, "raw", file.info(reference)$size),
                                    readBin(generated, "raw", file.info(generated)$size)))
}

result <- do.call(rbind, lapply(site_files, replay_site))
write.csv(result, file.path(output, "sites.csv"), row.names = FALSE)
cat(nrow(result), "author sites replayed;", sum(result$cell_equal),
    "cell-equal;", sum(result$byte_equal), "byte-equal\n")
if (!all(result$cell_equal) || !all(result$byte_equal)) {
  stop("At least one author prepared file differs from the raw-input replay")
}
