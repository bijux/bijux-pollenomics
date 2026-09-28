#!/usr/bin/env Rscript
# Compare the 2016 author REVEALS function with a pinned later LRA release.
args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 4) {
  stop("Usage: replay.R AUTHOR_ROOT PETRKUNES_ROOT ZIPFR_LIBRARY OUTPUT_DIR")
}
author <- normalizePath(args[[1]], mustWork = TRUE)
secondary <- normalizePath(args[[2]], mustWork = TRUE)
zipfr_library <- normalizePath(args[[3]], mustWork = TRUE)
output <- args[[4]]
dir.create(output, recursive = TRUE, showWarnings = FALSE)
suppressPackageStartupMessages(library("zipfR", lib.loc = zipfr_library,
                                       character.only = TRUE))
if (as.character(packageVersion("zipfR")) != "0.6.70" ||
    read.dcf(file.path(secondary, "DESCRIPTION"), fields = "Version")[[1]] != "0.1.2") {
  stop("Pinned R dependency or secondary LRA version changed")
}

reference <- file.path(author, "author", "run.REVEALS.files")
original_environment <- new.env(parent = globalenv())
secondary_environment <- new.env(parent = globalenv())
for (expression in parse(file.path(reference, "LRA-REVEALS-release.R"))) {
  if (is.call(expression) && as.character(expression[[1]]) %in% c("<-", "=") &&
      as.character(expression[[2]]) %in% c("KPf", "REVEALS")) {
    eval(expression, envir = original_environment)
  }
}
source(file.path(secondary, "R", "KPf.R"), local = secondary_environment)
source(file.path(secondary, "R", "REVEALS.R"), local = secondary_environment)
reveals_body_identical <- identical(body(original_environment$REVEALS),
                                    body(secondary_environment$REVEALS))
kpf_body_identical <- identical(body(original_environment$KPf),
                                body(secondary_environment$KPf))
avg <- read.csv(file.path(reference, "av-RPP.all.landclimII.csv"),
                row.names = 1, check.names = FALSE)
alvc <- read.csv(file.path(reference, "avar-RPP.all.landclimII.csv"),
                 row.names = 1, check.names = FALSE)
if (nrow(avg) != 31 || nrow(alvc) != 31 || ncol(alvc) != 31) {
  stop("Author PPE axis changed")
}
site_files <- read.csv(file.path(reference, "site.list.512.csv"), header = FALSE)[[1]]
if (length(site_files) != 9 || anyDuplicated(site_files)) stop("Author grid 512 sites changed")
sites <- setNames(lapply(site_files, function(name) {
  read.csv(file.path(reference, name), row.names = 1, check.names = FALSE)
}), sub("^LRAready_", "", sub("\\.csv$", "", site_files)))
sites <- lapply(sites, function(site) site[, "225", drop = FALSE])
active <- sites[vapply(sites, function(site) site["radius", "225"] > 0, logical(1))]
if (length(active) != 6 ||
    !identical(as.numeric(vapply(active, function(site) site["radius", "225"], 0.0)),
               c(150, 100, 10, 15, 10, 200))) {
  stop("Selected unequal-basin window changed")
}
cases <- list(single = active[["BROADOWN"]],
              unequal_pair = active[c("BROADOWN", "HARESDOWN")],
              six_sites = active,
              full_grid = sites)

summary <- list()
taxa <- list()
extract <- function(result, single) {
  if (single) {
    list(cover = as.numeric(result$V_sites[[1]][, "225"]),
         se = as.numeric(result$SE_sites[[1]][, "225"]), sites = 1)
  } else {
    list(cover = as.numeric(result$Mean_V[, "225"]),
         se = as.numeric(result$Mean_SE[, "225"]),
         sites = as.numeric(result$No_sites[1, "225"]))
  }
}
for (name in names(cases)) {
  set.seed(750225)
  first <- original_environment$REVEALS(cases[[name]], avg, alvc, 3, 100000,
                                         "gpm neutral")
  set.seed(750225)
  second <- secondary_environment$REVEALS(cases[[name]], avg, alvc, 3, 100000,
                                           "gpm neutral")
  first_values <- extract(first, is.data.frame(cases[[name]]))
  second_values <- extract(second, is.data.frame(cases[[name]]))
  cover_first <- first_values$cover
  cover_second <- second_values$cover
  se_first <- first_values$se
  se_second <- second_values$se
  if (length(cover_first) != 31 || length(cover_second) != 31 ||
      length(se_first) != 31 || length(se_second) != 31 ||
      !identical(is.na(cover_first), is.na(cover_second)) ||
      !identical(is.na(se_first), is.na(se_second))) {
    stop(paste("Comparison axes or masks differ:", name))
  }
  cover_delta <- abs(cover_first - cover_second)
  se_delta <- abs(se_first - se_second)
  summary[[name]] <- data.frame(
    scenario = name,
    supplied_sites = if (is.data.frame(cases[[name]])) 1 else length(cases[[name]]),
    radius_m = paste(if (is.data.frame(cases[[name]])) cases[[name]]["radius", "225"]
                     else vapply(cases[[name]], function(site) site["radius", "225"], 0.0),
                     collapse = ";"),
    finite_cover_pairs = sum(is.finite(cover_delta)),
    max_absolute_cover_difference = max(cover_delta, na.rm = TRUE),
    finite_se_pairs = sum(is.finite(se_delta)),
    max_absolute_se_difference = max(se_delta, na.rm = TRUE),
    original_no_sites = first_values$sites,
    secondary_no_sites = second_values$sites,
    reveals_body_identical = reveals_body_identical,
    kpf_body_identical = kpf_body_identical
  )
  taxa[[name]] <- data.frame(
    scenario = name, taxon = rownames(avg),
    original_cover = cover_first, secondary_cover = cover_second,
    absolute_cover_difference = cover_delta,
    original_se = se_first, secondary_se = se_second,
    absolute_se_difference = se_delta
  )
}
write.csv(do.call(rbind, summary), file.path(output, "summary.csv"),
          row.names = FALSE, na = "", fileEncoding = "UTF-8")
write.csv(do.call(rbind, taxa), file.path(output, "taxa.csv"),
          row.names = FALSE, na = "", fileEncoding = "UTF-8")
cat("Four original-versus-tagged R source comparisons retained\n")
