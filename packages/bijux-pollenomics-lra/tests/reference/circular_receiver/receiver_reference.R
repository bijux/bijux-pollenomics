# Independent displacement/circle-overlap reference for one declared GPM operator.
# This is neither the historical author R implementation nor physical calibration.

receiver_reference_refuse <- function(code, message) {
  stop(structure(
    list(message = message, call = NULL, reason_code = code),
    class = c("circular_receiver_reference_error", "error", "condition")
  ))
}

receiver_reference_scalar <- function(value, name, positive = FALSE) {
  if (!(typeof(value) %in% c("integer", "double")) || length(value) != 1L ||
      !is.null(dim(value)) || !is.finite(value) || value < 0 ||
      (positive && value == 0)) {
    receiver_reference_refuse("invalid_parameter", paste("Invalid scalar", name))
  }
  as.double(value)
}

receiver_reference_overlap <- function(first, second, separation) {
  # Standard circle-lens area; no receiver-offset angular integrand is reused.
  if (separation >= first + second) return(0)
  if (separation <= abs(first - second)) return(pi * min(first, second)^2)
  square <- separation^2
  first_cosine <- (square + first^2 - second^2) / (2 * separation * first)
  second_cosine <- (square + second^2 - first^2) / (2 * separation * second)
  radicand <- (-separation + first + second) *
    (separation + first - second) * (separation - first + second) *
    (separation + first + second)
  if (!all(is.finite(c(first_cosine, second_cosine, radicand)))) {
    receiver_reference_refuse("overlap_unresolved", "Circle-overlap arithmetic overflow")
  }
  # Retain the original finite-arithmetic domain guard above, but do not use its
  # ill-conditioned cosines or subtract large triangle and sector areas.
  small <- min(first, second)
  large <- max(first, second)
  total_radius <- large + small
  radius_difference <- large - small
  # Regroup both Heron difference factors before dividing: for equal radii and
  # tiny separation they remain d/d, rather than rounding d+r-r to zero.
  if (separation < large / 2) {
    height <- sqrt(total_radius - separation) * sqrt(total_radius + separation) *
      sqrt((separation + radius_difference) / separation) *
      sqrt((separation - radius_difference) / separation) / 2
  } else {
    # Keep the small radius after subtracting the nearby large distances.
    # R+r and R-r may round away part of r before the partial-lens differences.
    height <- sqrt((large - separation) + small) * sqrt(total_radius + separation) *
      sqrt((separation + radius_difference) / separation) *
      sqrt(((separation - large) + small) / separation) / 2
  }
  if (small == large) {
    small_projection <- large_projection <- separation / 2
  } else if (separation < large / 2) {
    # The difference-of-squares form preserves near-coincident unequal circles.
    scaled_difference <- (radius_difference / separation) * total_radius
    small_projection <- (separation - scaled_difference) / 2
    large_projection <- (separation + scaled_difference) / 2
  } else {
    # Near the large circumference, factor d^2-R^2 before adding the small r^2.
    small_projection <- ((separation - large) * (separation + large) + small^2) /
      (2 * separation)
    large_projection <- ((separation - small) * (separation + small) + large^2) /
      (2 * separation)
  }
  if (!all(is.finite(c(height, small_projection, large_projection))) || height < 0) {
    receiver_reference_refuse("overlap_unresolved", "Circle-overlap arithmetic overflow")
  }
  segment <- function(theta) {
    # theta-sin(theta)cos(theta), with cancellation removed near zero.
    # At theta<=0.01, the first omitted term is <=4096*theta^13/13! <6.6e-33.
    if (theta <= 0.01) {
      squared <- theta^2
      return(theta^3 * (2/3 + squared * (-2/15 + squared *
        (4/315 + squared * (-2/2835 + squared * 4/155925)))))
    }
    theta - sin(theta) * cos(theta)
  }
  area <- small^2 * segment(atan2(height, small_projection)) +
    large^2 * segment(atan2(height, large_projection))
  if (!is.finite(area) || area < 0 || area > pi * small^2) {
    receiver_reference_refuse("overlap_unresolved", "Circle-overlap area is unresolved")
  }
  area
}

circular_receiver_annulus_reference <- function(
    receiver_radius_m, inner_radius_m, outer_radius_m, fall_speed_m_s,
    diffusion_coefficient, turbulence_parameter, wind_speed_m_s,
    absolute_tolerance = 1e-11, relative_tolerance = 1e-10,
    quadrature_limit = 1000L) {
  receiver <- receiver_reference_scalar(receiver_radius_m, "receiver_radius_m")
  inner <- receiver_reference_scalar(inner_radius_m, "inner_radius_m")
  outer <- receiver_reference_scalar(outer_radius_m, "outer_radius_m")
  fall <- receiver_reference_scalar(fall_speed_m_s, "fall_speed_m_s", TRUE)
  diffusion <- receiver_reference_scalar(diffusion_coefficient, "diffusion_coefficient", TRUE)
  gamma <- receiver_reference_scalar(turbulence_parameter, "turbulence_parameter", TRUE)
  wind <- receiver_reference_scalar(wind_speed_m_s, "wind_speed_m_s", TRUE)
  absolute <- receiver_reference_scalar(absolute_tolerance, "absolute_tolerance", TRUE)
  relative <- receiver_reference_scalar(relative_tolerance, "relative_tolerance", TRUE)
  if (receiver > inner || inner >= outer) {
    receiver_reference_refuse("invalid_geometry", "Require 0 <= receiver <= inner < outer")
  }
  if (!is.integer(quadrature_limit) || length(quadrature_limit) != 1L ||
      is.na(quadrature_limit) || quadrature_limit < 20L || quadrature_limit > 1000L) {
    receiver_reference_refuse("invalid_budget", "Require integer subdivisions from 20 to 1000")
  }
  coefficient <- (4 * fall) / (gamma * wind * sqrt(pi) * diffusion)
  exponent <- gamma / 2
  survival_one <- exp(-coefficient)
  if (!is.finite(coefficient) || coefficient <= 0 ||
      !(survival_one > 0 && survival_one < 1)) {
    receiver_reference_refuse("survival_unresolved", "One-metre survival is unresolved")
  }
  # Match the analytic point limit, retaining differences lost by exp subtraction.
  if (receiver == 0) {
    left <- coefficient * inner^exponent
    right <- coefficient * outer^exponent
    difference <- exp(-left) - exp(-right)
    if (difference == 0 && exp(-left) > 0) {
      if (inner == 0 || left == 0) {
        increment <- right
      } else {
        ratio <- (outer - inner) / inner
        log_ratio <- if (is.finite(ratio)) log1p(ratio) else log(outer) - log(inner)
        increment <- left * expm1(exponent * log_ratio)
      }
      difference <- exp(-left) * -expm1(-increment)
    }
    if (!is.finite(difference) || difference < 0 || difference > 1) {
      receiver_reference_refuse("point_unresolved", "Point survival difference is invalid")
    }
    return(list(
      factor = difference, raw_factor = difference, estimated_absolute_error = 0,
      tail_mass_bound = 0, method = "analytic_point_limit",
      coefficient_from_parameters = coefficient, exponent = exponent,
      absolute_tolerance = absolute, relative_tolerance = relative,
      quadrature_limit = quadrature_limit, subdivisions_used = 0L
    ))
  }
  area <- pi * receiver^2
  boundaries <- sort(unique(coefficient *
    c(inner - receiver, inner + receiver, outer - receiver, outer + receiver)^exponent))
  if (!is.finite(area) || area <= 0 || !all(is.finite(boundaries))) {
    receiver_reference_refuse("geometry_transform_unresolved", "Finite area/hazard transform required")
  }
  # Beyond this cap the omitted probability is bounded by exp(-700).
  # This analytic tail bound is separate from integrate()'s nonrigorous estimate.
  cap <- 700
  tail <- if (max(boundaries) > cap) exp(-cap) else 0
  boundaries <- sort(unique(pmin(boundaries, cap)))
  total <- 0
  estimated_error <- 0
  subdivisions <- 0L
  integrand <- function(q) {
    vapply(q, function(value) {
      distance <- (value / coefficient)^(1 / exponent)
      if (!is.finite(distance)) {
        receiver_reference_refuse("distance_unresolved", "Inverse hazard overflow")
      }
      lens <- receiver_reference_overlap(receiver, outer, distance) -
        receiver_reference_overlap(receiver, inner, distance)
      result <- exp(-value) * lens / area
      if (!is.finite(result)) {
        receiver_reference_refuse("overlap_unresolved", "Nonfinite overlap density")
      }
      result
    }, numeric(1))
  }
  for (index in seq_len(max(0L, length(boundaries) - 1L))) {
    left <- boundaries[index]
    right <- boundaries[index + 1L]
    if (left >= right) next
    segment <- stats::integrate(
      integrand, left, right, subdivisions = quadrature_limit,
      abs.tol = absolute / 4, rel.tol = relative, stop.on.error = FALSE
    )
    if (!identical(segment$message, "OK") ||
        !all(is.finite(c(segment$value, segment$abs.error)))) {
      receiver_reference_refuse("quadrature_not_converged", "R adaptive integration refused")
    }
    total <- total + segment$value
    estimated_error <- estimated_error + segment$abs.error
    subdivisions <- subdivisions + segment$subdivisions
  }
  if (!is.finite(total) || !is.finite(estimated_error) ||
      total < -absolute || total > 1 + absolute) {
    receiver_reference_refuse("response_invalid", "Annulus probability is invalid")
  }
  list(
    factor = min(1, max(0, total)), raw_factor = total,
    estimated_absolute_error = estimated_error, tail_mass_bound = tail,
    method = "displacement_circle_overlap_one_dimensional",
    coefficient_from_parameters = coefficient, exponent = exponent,
    absolute_tolerance = absolute, relative_tolerance = relative,
    quadrature_limit = quadrature_limit, subdivisions_used = subdivisions
  )
}
