"""High-precision scalar oracle for a Gaussian weighted Hellinger barycenter.

The Decimal calculation starts from the literal binary64 input values. It is
an independent numerical reference, not an interval certificate or source audit.
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal, DecimalException, localcontext
import math

PRECISION = 80
CLOSURE_TOLERANCE = 1e-9


def _require(condition: object, message: str) -> None:
    if not condition:
        raise ValueError("Independent Hellinger predictor: " + message)


def _number(value: object) -> Decimal:
    _require(type(value) in (int, float), "native finite numeric scalar required")
    assert isinstance(value, int | float)
    try:
        native = float(value)
    except OverflowError as error:
        raise ValueError("Independent Hellinger predictor: binary64 range") from error
    _require(math.isfinite(native), "finite binary64 scalar required")
    return Decimal.from_float(native)


def predict(
    compositions: Sequence[Sequence[float]],
    distances_km: Sequence[float],
    length_scale_km: float,
) -> dict[str, list[float]]:
    """Compute normalized root means without importing the host predictor.

    Source rows retain the host's explicit absolute 1e-9 closure admission;
    accepted rows are not silently renormalized before taking their roots.
    Positive Gaussian weights and supported output components must remain
    positive when represented in the declared binary64 output format.
    """
    _require(
        bool(compositions) and len(compositions) == len(distances_km),
        "nonempty matched training/distance rows",
    )
    dimension = len(compositions[0])
    _require(
        dimension > 0 and all(len(row) == dimension for row in compositions),
        "common nonempty taxon axis",
    )
    scale = _number(length_scale_km)
    _require(scale > 0, "positive length scale")
    distances = [_number(value) for value in distances_km]
    _require(min(distances) >= 0, "nonnegative distances")
    rows = [[_number(value) for value in row] for row in compositions]
    _require(
        all(0 <= value <= 1 for row in rows for value in row),
        "closed nonnegative taxon fractions",
    )
    try:
        with localcontext() as context:
            context.prec = PRECISION
            tolerance = Decimal.from_float(CLOSURE_TOLERANCE)
            _require(
                all(abs(sum(row, Decimal(0)) - 1) <= tolerance for row in rows),
                "source composition closure",
            )
            nearest = min(distances)
            # Subtract squared distances before exponentiation. At least one
            # relative weight is exactly one, including remote equal-distance ties.
            relative = [
                (
                    -((distance - nearest) * (distance + nearest)) / (2 * scale * scale)
                ).exp()
                for distance in distances
            ]
            _require(
                all(value > 0 and float(value) > 0 for value in relative),
                "positive relative weight underflow",
            )
            total_weight = sum(relative)
            weights = [value / total_weight for value in relative]
            _require(
                all(float(value) > 0 for value in weights),
                "positive normalized weight underflow",
            )
            root_mean = [
                sum(
                    weights[index] * rows[index][taxon].sqrt()
                    for index in range(len(rows))
                )
                for taxon in range(dimension)
            ]
            denominator = sum(value * value for value in root_mean)
            _require(denominator > 0, "positive root norm")
            exact = [value * value / denominator for value in root_mean]
            fractions = [float(value) for value in exact]
            _require(
                all(math.isfinite(value) for value in fractions),
                "finite output fractions",
            )
            _require(
                all(
                    value > 0 or not any(row[taxon] > 0 for row in rows)
                    for taxon, value in enumerate(fractions)
                ),
                "positive output support underflow",
            )
            return {
                "fractions": fractions,
                "weights": [float(value) for value in weights],
            }
    except DecimalException as error:
        raise ValueError(
            "Independent Hellinger predictor: reference arithmetic range refused"
        ) from error
