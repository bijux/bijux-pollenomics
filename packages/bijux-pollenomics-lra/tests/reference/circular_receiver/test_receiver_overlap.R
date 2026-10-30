# Analytic circle geometry controls; no adaptive quadrature or scientific inputs.
args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 3L) stop("Usage: test_receiver_overlap.R CORRECTED_R ORIGINAL_R ABSENT_OUTPUT")
if (file.exists(args[3]) || !dir.exists(dirname(args[3]))) stop("Absent owned output required")
stable <- new.env(parent = baseenv())
original <- new.env(parent = baseenv())
sys.source(args[1], envir = stable)
sys.source(args[2], envir = original)
overlap <- stable$receiver_reference_overlap
rows <- list()
record <- function(name, actual, lower, upper, slack = 0) {
  if (!all(is.finite(c(actual, lower, upper))) || lower > upper ||
      actual < lower - slack || actual > upper + slack) stop(paste("Mismatch", name))
  rows[[length(rows) + 1L]] <<- data.frame(
    case = name, actual = actual, lower_bound = lower, upper_bound = upper,
    floating_slack = slack, stringsAsFactors = FALSE
  )
}
record("coincident", overlap(1, 1, 0), pi, pi)
record("internal_tangency", overlap(1, 5, 4), pi, pi)
record("external_tangency", overlap(1, 5, 6), 0, 0)
record("disjoint", overlap(1, 5, 7), 0, 0)
record("unit_equal_radius_at_one", overlap(1, 1, 1),
       2*pi/3 - sqrt(3)/2, 2*pi/3 - sqrt(3)/2, 2e-15)
record("unit_equal_radius_at_sqrt_two", overlap(1, 1, sqrt(2)),
       pi/2 - 1, pi/2 - 1, 2e-15)
# The exact equal-radius loss is 2*d + O(d^3) at unit radius.
record("equal_radius_near_coincident", overlap(1, 1, 1e-12), pi-2e-12, pi-2e-12, 2e-15)
for (distance in c(1e-150, 1e-300)) {
  record(paste0("equal_radius_tiny_", distance), overlap(1, 1, distance), pi, pi, 2e-15)
}
# The larger disk contains the equal-radius translated intersection. The lost
# unit-disk area is at most 2*d; this is a bound, not a copy of the lens formula.
record("unequal_near_coincident", overlap(1, 1+1e-12, 2e-12), pi-4e-12, pi, 2e-15)
for (radius in c(1e5, 1e12)) {
  # At d=R, the normalized exact-area series is pi/2-r/(3R)-r^3/(120R^3).
  # For r/R<=.00049, the next term is below 2e-20.
  small <- if (radius == 1e5) 49 else 1
  ratio <- small / radius
  expected <- pi/2 - ratio/3 - ratio^3/120
  record(paste0("large_circle_through_center_", radius),
         overlap(small, radius, radius)/small^2, expected, expected, 2e-14)
}
cap <- function(height) acos(1-height) - (1-height)*sqrt(height*(2-height))
for (radius in c(1e5, 1e12)) {
  distance <- radius + 1 - .001
  height <- (radius + 1) - distance
  # The large-circle boundary lies between two parallel cuts separated by at
  # most epsilon for every point of the unit disk. Their unit caps bound A.
  epsilon <- 1/(radius + sqrt(radius^2-1))
  lower <- cap(max(0, height-epsilon))
  upper <- cap(height)
  area <- overlap(1, radius, distance)
  record(paste0("near_external_tangency_", radius), area, lower, upper, 2e-14)
  if (area <= 0) stop("Positive near-tangent area lost")
}
record("near_internal_tangency", overlap(1, 1e5, 1e5-1+1e-5), pi-2e-5, pi, 2e-14)
# Exact binary inputs: both original classification branches admit the partial
# lens. R+r and R-r round r=11/16 to 3/4, corrupting their later differences.
# The disk boundary is between parallel cuts x=t and x=t+epsilon, where
# epsilon <= r^2/(R+sqrt(R^2-r^2)); normalized unit-disk caps bound the area.
large_binary <- 3 * 2^49
small_binary <- 11/16
for (offset in c(1/4, 1/2, -1/2)) {
  distance <- large_binary + offset
  if (distance >= large_binary + small_binary ||
      distance <= large_binary - small_binary) stop("Partial-lens control is unreachable")
  exact_offset <- distance - large_binary
  normalized_height <- (small_binary - exact_offset) / small_binary
  normalized_epsilon <- small_binary /
    (large_binary + sqrt(large_binary^2 - small_binary^2))
  record(paste0("binary_partial_parallel_cut_", offset),
         overlap(small_binary, large_binary, distance) / small_binary^2,
         cap(normalized_height - normalized_epsilon), cap(normalized_height), 2e-14)
}
record("argument_symmetry", overlap(2, 5, 4)-overlap(5, 2, 4), 0, 0)
record("uniform_scaling", overlap(2000, 3000, 4000)/1e6-overlap(2, 3, 4), 0, 0, 2e-14)
for (case in list(c(1,1,1), c(2,3,2), c(1,2,.5))) {
  expected <- original$receiver_reference_overlap(case[1], case[2], case[3])
  record(paste0("original_well_conditioned_", paste(case, collapse="_")),
         overlap(case[1], case[2], case[3]), expected, expected, 2e-14)
}
refused <- tryCatch({overlap(1e200, 1e200, 1e200); FALSE}, error=function(error) {
  if (!inherits(error, "circular_receiver_reference_error")) stop(error)
  identical(error$reason_code, "overlap_unresolved")
})
if (!isTRUE(refused)) stop("Original overflow refusal was lost")
if (!dir.create(args[3])) stop("Cannot create owned output")
utils::write.table(do.call(rbind, rows), file.path(args[3], "overlap-controls.tsv"),
                   row.names=FALSE, quote=TRUE, sep="\t")
writeLines("Analytic equal/tangent/extreme-aspect/scale/symmetry controls and three original well-conditioned overlaps; one typed overflow refusal. No quadrature or field evidence.",
           file.path(args[3], "scope.txt"))
