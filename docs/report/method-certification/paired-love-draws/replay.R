args <- commandArgs(trailingOnly = TRUE)
options(digits = 17)
stopifnot(length(args) == 5L)
draws <- jsonlite::fromJSON(args[1], simplifyVector = FALSE)
setup <- jsonlite::fromJSON(args[2])
stopifnot(identical(draws$schema_version, "paired-love-draws.1"))
stopifnot(identical(as.character(packageVersion("disqover")), "0.9.14"))
stopifnot(identical(
  readLines(system.file("SOURCE_SHA256", package = "disqover"), warn = FALSE)[1],
  "ea496ae82807b52c9dd3d4b39b4dfa294bfac4068e20184ce56187bff70caf5c"
))
source(args[3])
local <- as.data.frame(t(as.numeric(setup$local)), check.names = FALSE)
regional_pollen <- as.data.frame(t(as.numeric(setup$regional)), check.names = FALSE)
names(local) <- names(regional_pollen) <- setup$pollen_columns
params <- setup$params
params$ppes <- setup$ppes
params$fallspeed <- setup$fallspeed
params$error <- TRUE
rings <- setup$rings
taxa <- as.character(params$ppes$Taxon)
regional <- as.numeric(unlist(draws$regional_cover))
stopifnot(identical(taxa, as.character(unlist(draws$taxa))))
stopifnot(length(regional) == length(taxa), abs(sum(regional) - 1) < 5e-5)
regional_stub <- function(...) {
  as.data.frame(setNames(as.list(100 * regional), paste0(taxa, ".mean")), check.names = FALSE)
}
call_count <- 0L
valid <- as.integer(unlist(draws$valid_ring_positions))
ppe_stub <- function(n, mean, sds) {
  call_count <<- call_count + 1L
  repetition <- (call_count - 1L) %/% length(valid) + 1L
  ring <- valid[(call_count - 1L) %% length(valid) + 1L]
  value <- as.numeric(unlist(draws$local_ppe[[repetition]][[ring]]))
  stopifnot(length(value) == n, all(value > 0))
  value
}
count_stub <- function(n, size, prob) {
  repetition <- (call_count - 1L) %/% length(valid) + 1L
  ring <- valid[(call_count - 1L) %% length(valid) + 1L]
  value <- as.numeric(unlist(draws$local_counts[[repetition]][[ring]]))
  stopifnot(n == 1L, length(value) == length(taxa), sum(value) == size)
  matrix(value, ncol = 1L)
}
local_lov <- clone_with("lov", list(rmultinom = count_stub))
replayed <- clone_with(
  "LOVEr", list(REVEALSinR = regional_stub, lov = local_lov)
)
result <- with_binding(
  "disqover", "rnorm_reveals", ppe_stub,
  replayed(
    local, regional_pollen, params, rings, 10L, repeats = 2L
  )
)
stopifnot(call_count == 2L * length(valid))
rows <- list()
for (field in c("Mean", "Q10", "Q90", "SD")) {
  matrix_value <- result[[field]]
  for (ring in seq_len(10L)) {
    for (taxon in seq_along(taxa)) {
      rows[[length(rows) + 1L]] <- data.frame(
        field = field, ring = ring, taxon = taxa[taxon],
        value = matrix_value[ring, taxon]
      )
    }
  }
}
write.table(
  do.call(rbind, rows), file = args[4], sep = ",", row.names = FALSE,
  col.names = TRUE, quote = FALSE, na = "", eol = "\n"
)
writeLines(trimws(capture.output(sessionInfo()), which = "right"), args[5])
