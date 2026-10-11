args <- commandArgs(trailingOnly = TRUE)
input <- normalizePath(args[1])
output <- normalizePath(args[2])
.libPaths(c(args[3], .libPaths()))
options(digits = 17, warn = 1)
stopifnot(getRversion() == "4.6.0")
stopifnot(as.character(packageVersion("disqover")) == "0.9.14")
stopifnot(readLines(system.file("SOURCE_SHA256", package = "disqover"))[1] == args[4])
source(args[5])

local <- read.csv(file.path(input, "local.csv"), check.names = FALSE)
regional <- read.csv(file.path(input, "regional.csv"), check.names = FALSE)
ppes <- read.csv(file.path(input, "ppes.csv"), check.names = FALSE)
rings <- read.csv(file.path(input, "rings.csv"), check.names = FALSE)
for (name in c("local", "regional", "ppes", "rings")) {
  table <- get(name)
  exact <- read.csv(file.path(input, paste0(name, "-hex.csv")), check.names = FALSE,
                    colClasses = "character")
  stopifnot(identical(names(exact), names(table)[vapply(table, is.numeric, logical(1))]))
  for (column in names(exact)) table[[column]] <- as.numeric(exact[[column]])
  assign(name, table)
  write.csv(table, file.path(output, paste0("r-input-", name, ".csv")), row.names = FALSE)
  numeric_columns <- vapply(table, is.numeric, logical(1))
  writeLines(sprintf("%a", as.numeric(unlist(table[numeric_columns], use.names = FALSE))),
             file.path(output, paste0("r-input-", name, "-hex.txt")))
}
candidate_hex <- read.csv(file.path(input, "candidates-hex.csv"), check.names = FALSE,
                          colClasses = "character")
CANDIDATES <- matrix(as.numeric(as.matrix(candidate_hex)), nrow = nrow(candidate_hex),
                     ncol = ncol(candidate_hex))
writeLines(sprintf("%a", as.numeric(CANDIDATES)),
           file.path(output, "r-input-candidates-hex.txt"))
stopifnot(identical(names(local)[-1], as.character(ppes$Taxon)))
stopifnot(identical(names(regional)[-1], as.character(ppes$Taxon)))
stopifnot(identical(ncol(CANDIDATES), nrow(ppes)), nrow(CANDIDATES) == 32L)

params <- list(
  ppes = ppes,
  fallspeed = ppes[, c("Taxon", "fallspeed")],
  dBasinRegional = 300,
  tBasinRegional = "lake",
  dBasinLocal = 12.9,
  tBasinLocal = "lake",
  tBasin = "lake",
  dwm = "lsm unstable",
  error = FALSE
)
result <- with_binding(
  "RcppDE", "DEoptim", replay_de_traced,
  clone_with("LOVEoptim", list(REVEALSinR = fixed_reveals, rmultinom = fixed_multinomial))(
    local, regional, params, rings, 10, repeats = 2
  )
)
write.csv(result$cover$mean, file.path(output, "r-cover.csv"), row.names = FALSE, na = "NaN")
write.csv(result$pollenpercentages$mean, file.path(output, "r-pollen.csv"), row.names = FALSE, na = "NaN")
write.csv(result$mBestValue, file.path(output, "r-objective.csv"), row.names = FALSE, na = "NaN")
write.csv(F("calK")(rings, params), file.path(output, "r-k.csv"), row.names = FALSE)
write.csv(as.data.frame(do.call(rbind, REPLAY_TRACE)), file.path(output, "r-trace.csv"), row.names = FALSE)
writeLines(capture.output(sessionInfo()), file.path(output, "r-session.txt"))
