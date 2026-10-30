"""Zero-compatible composition means under declared spatial kernel weights."""

from __future__ import annotations

from collections.abc import Mapping
from math import exp, fsum, isfinite, sqrt

from ..contracts import ValidationRefusal, finite_number, required_identity
from ..metrics import closed_composition


def gaussian_distance_weights(
    distances_km: Mapping[str, float], *, length_scale_km: float
) -> dict[str, float]:
    """Normalize Gaussian weights without losing all support to underflow.

    Subtract the nearest squared distance from every log weight. Exact nearest
    ties therefore retain weight one before normalization, even when every
    unshifted exponential would underflow. A lost relative weight refuses.
    This is a numerical kernel, not a
    geographic covariance or an evidence-based extrapolation policy.
    """
    scale = finite_number(length_scale_km)
    if scale <= 0 or not distances_km:
        raise ValidationRefusal(
            "invalid_hellinger_spatial_configuration",
            "Positive scale and sites required",
        )
    distances = {
        required_identity(key): finite_number(value)
        for key, value in sorted(distances_km.items())
    }
    if min(distances.values()) < 0:
        raise ValidationRefusal("invalid_distance", "Distances cannot be negative")
    nearest = min(distances.values())
    weights = {}
    for group, distance in distances.items():
        if distance == nearest:
            weight = 1.0
        else:
            difference = (distance - nearest) / scale
            total = distance / scale + nearest / scale
            exponent = -0.5 * difference * total
            weight = exp(exponent)
            if not isfinite(exponent) or weight == 0:
                raise ValidationRefusal(
                    "hellinger_weight_underflow",
                    "Positive relative Gaussian weight lost",
                )
        weights[group] = weight
    total_weight = fsum(weights.values())
    normalized = {group: value / total_weight for group, value in weights.items()}
    if any(value == 0 for value in normalized.values()):
        raise ValidationRefusal(
            "hellinger_weight_underflow", "Positive normalized Gaussian weight lost"
        )
    return normalized


def hellinger_barycentre(
    compositions: Mapping[str, Mapping[str, float]], weights: Mapping[str, float]
) -> dict[str, float]:
    """Minimize weighted squared Hellinger distance on the closed simplex.

    If a is the weighted sum of square-root compositions, the unique minimizer
    is square(a) / dot(a, a). Nonnegative unit-sum weights and closed source
    compositions make a nonzero. This keeps shared exact zeros without a
    pseudocount. The result need not lie in the ordinary convex hull of the
    training compositions. The caller owns training exclusion and scale choice.
    """
    if not compositions or set(compositions) != set(weights):
        raise ValidationRefusal(
            "hellinger_group_mismatch",
            "Require the same nonempty composition/weight keys",
        )
    admitted = {
        required_identity(group): closed_composition(values)
        for group, values in sorted(compositions.items())
    }
    numeric_weights = {group: finite_number(weights[group]) for group in admitted}
    if min(numeric_weights.values()) < 0:
        raise ValidationRefusal("invalid_hellinger_weights", "Negative weight")
    maximum = max(numeric_weights.values())
    if maximum == 0:
        raise ValidationRefusal("invalid_hellinger_weights", "No positive weight")
    scaled = {group: value / maximum for group, value in numeric_weights.items()}
    total_weight = fsum(scaled.values())
    normalized = {group: value / total_weight for group, value in scaled.items()}
    if any(numeric_weights[group] > 0 and normalized[group] == 0 for group in admitted):
        raise ValidationRefusal(
            "hellinger_weight_underflow", "Positive input weight lost"
        )
    taxa = tuple(sorted(next(iter(admitted.values()))))
    if any(set(row) != set(taxa) for row in admitted.values()):
        raise ValidationRefusal(
            "taxon_denominator_mismatch", "All source compositions need the same taxa"
        )
    roots = {
        taxon: fsum(
            normalized[group] * sqrt(admitted[group][taxon]) for group in admitted
        )
        for taxon in taxa
    }
    normalizer = fsum(value * value for value in roots.values())
    if not isfinite(normalizer) or normalizer <= 0:
        raise ValidationRefusal(
            "hellinger_mean_nonfinite", "Undefined square-root mean"
        )
    result = {taxon: value * value / normalizer for taxon, value in roots.items()}
    if any(
        result[taxon] == 0
        and any(
            numeric_weights[group] > 0 and admitted[group][taxon] > 0
            for group in admitted
        )
        for taxon in taxa
    ):
        raise ValidationRefusal(
            "hellinger_composition_underflow", "Positive supported component lost"
        )
    return result
