args <- commandArgs(trailingOnly = TRUE)
stopifnot(length(args) == 1L)
job <- normalizePath(args[[1]], mustWork = TRUE)
output <- file.path(job, "native")
stopifnot(!dir.exists(output))
dir.create(output)
data <- read.csv(file.path(job, "inputs", "panel-comparison.csv"),
                 stringsAsFactors = FALSE, check.names = FALSE)
stopifnot(nrow(data) == 167L, all(is.finite(data$corrected_panel_cover_percent)))
names <- c(ABB = "ABB (Abborrtjarnen): Betula / Pinus",
           BOKE = "BOKE (Bokesjon): Betula / Fraxinus / Ulmus",
           BUS = "BUS (Bussjosjon): Betula / Ulmus",
           TIB = "Tibetanus: Pinus / Poaceae")
taxa <- c("Betula", "Pinus sylvestris", "Fraxinus", "Ulmus", "Poaceae")
colors <- setNames(c("#167A53", "#294A99", "#B46E15", "#873889", "#BD4E3D"), taxa)
draw <- function() {
  par(mfrow = c(2, 2), mar = c(4.0, 4.3, 3.0, 1.0),
      oma = c(4.4, 0, 2.2, 0), las = 1, family = "sans", cex = 0.83)
  for (core in c("ABB", "BOKE", "BUS", "TIB")) {
    subset <- data[data$core == core, ]
    plot(NA, xlim = c(11700, 0), ylim = c(0, 100),
         xlab = "Calendar years BP (datum AD 1950)", ylab = "Fraction of this panel (%)",
         main = names[[core]], axes = FALSE)
    axis(1, at = seq(0, 12000, 2000), labels = seq(0, 12000, 2000))
    axis(2, at = seq(0, 100, 20))
    abline(h = seq(0, 100, 20), col = "#E7E7E7")
    box(col = "#888888")
    for (taxon in unique(subset$taxon)) {
      row <- subset[subset$taxon == taxon, ]
      row <- row[order(row$window_midpoint_cal_bp), ]
      col <- colors[[taxon]]
      points(row$window_midpoint_cal_bp, row$direct_panel_pollen_percent,
             col = adjustcolor(col, alpha.f = 0.7), pch = 1, cex = 0.65)
      points(row$window_midpoint_cal_bp, row$corrected_panel_cover_percent,
             col = col, pch = 16, cex = 0.65)
      arrows(row$window_midpoint_cal_bp,
             pmax(0, row$corrected_panel_cover_percent - row$conditional_standard_error_pp),
             row$window_midpoint_cal_bp,
             pmin(100, row$corrected_panel_cover_percent + row$conditional_standard_error_pp),
             angle = 90, code = 3, length = 0.025, col = adjustcolor(col, alpha.f = 0.65))
    }
    legend("topleft", legend = unique(subset$taxon),
           col = colors[unique(subset$taxon)], pch = 16, bty = "n", cex = 0.8)
  }
  mtext("Declared static basins: direct pollen and corrected panel composition", outer = TRUE,
        side = 3, line = 0.55, font = 2, cex = 1.05)
  mtext("Open circles: direct pollen. Filled circles: corrected fraction. Bars: conditional +/-1 SE.",
        outer = TRUE, side = 1, line = 0.6, cex = 0.9)
  mtext("Points use occupied-window midpoints; raw age bounds are missing. No time interpolation.",
        outer = TRUE, side = 1, line = 1.85, cex = 0.86)
  mtext("Panels differ by core. These fractions describe restricted panels; full land cover is unestablished.",
        outer = TRUE, side = 1, line = 3.1, cex = 0.86)
}
png(file.path(output, "panel-comparison.png"), width = 1740, height = 1380,
    res = 150, type = "quartz", family = "sans")
stopifnot(dev.cur() != 1L)
draw()
dev.off()
file <- file.path(output, "panel-comparison.png")
stopifnot(file.exists(file), file.info(file)$size > 1000)
header <- readBin(file, what = "raw", n = 8L)
stopifnot(identical(header, as.raw(c(137,80,78,71,13,10,26,10))))
cat("Rendered", nrow(data), "derived panel points in four core facets; actual Quartz PNG\n")
