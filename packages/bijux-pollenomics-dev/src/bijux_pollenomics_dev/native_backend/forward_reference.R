# Independent binary64 matrix reference; no DISQOVER compatibility claim.
arguments <- commandArgs(trailingOnly=TRUE)
root <- arguments[[1]]
read_matrix <- function(name) as.matrix(read.csv(file.path(root, paste0(name, ".csv")), header=FALSE))
cover <- read_matrix("cover")
kernels <- read_matrix("kernels")
regional <- as.numeric(read_matrix("regional"))
fractions <- as.numeric(read_matrix("fractions"))
productivity <- as.numeric(read_matrix("productivity"))
stopifnot(all(is.finite(cover)), all(cover >= 0),
          all(abs(rowSums(cover)-1) <= 1e-12),
          all(is.finite(kernels)), all(kernels >= 0),
          all(is.finite(regional)), all(regional >= 0),
          all(is.finite(fractions)), all(fractions >= 0 & fractions <= 1),
          all(is.finite(productivity)), all(productivity > 0))
factors <- as.numeric(crossprod(fractions, kernels))
mass <- sweep(sweep(cover, 2, factors * productivity, "*"), 2, regional, "+")
stopifnot(all(is.finite(mass)), all(rowSums(mass) > 0))
result <- mass / rowSums(mass)
write.table(result, file.path(root, "R-output.csv"), row.names=FALSE, col.names=FALSE, sep=",", quote=FALSE)
writeLines(c(R.version.string, as.character(packageVersion("base"))), file.path(root, "R-version.txt"))
