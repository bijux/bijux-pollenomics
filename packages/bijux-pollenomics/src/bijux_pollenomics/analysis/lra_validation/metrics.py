"""Target-specific descriptive scores; none alone constitutes final acceptance."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from math import isclose, log, sqrt

from .contracts import ValidationRefusal, finite_number, required_identity


@dataclass(frozen=True)
class CompositionScore:
    """A single observation's explicit taxon denominator and fraction-unit errors.

    Mean signed bias over a closed composition cancels by construction. Use
    signed_error_by_taxon across independent sites to assess directional bias;
    the composition-level bias is not an accuracy or calibration criterion.
    """

    target: str
    status: str
    taxon_count: int
    scored_taxon_count: int
    missing_observed_taxa: tuple[str, ...]
    mae_fraction: float | None
    rmse_fraction: float | None
    bias_fraction: float | None
    total_variation: float | None
    count_conditioned_deviance: float | None = None
    observed_total_count: int | None = None
    zero_probability_positive_count: bool = False
    signed_error_by_taxon: tuple[tuple[str, float], ...] = ()

    def as_dict(self) -> dict[str, object]:
        """Render finite JSON-safe scores; impossible predictions have explicit flags."""
        return {field: getattr(self, field) for field in self.__dataclass_fields__}


def closed_composition(values: Mapping[str, float]) -> dict[str, float]:
    """Require named fractions with an explicit closed taxon denominator."""
    if not values:
        raise ValidationRefusal(
            "empty_composition", "Composition must name at least one taxon"
        )
    result = {
        required_identity(key): finite_number(value) for key, value in values.items()
    }
    if any(value < 0 or value > 1 for value in result.values()):
        raise ValidationRefusal(
            "invalid_composition", "Negative or out-of-range fractions cannot be scored"
        )
    if not isclose(sum(result.values()), 1.0, rel_tol=0, abs_tol=1e-9):
        raise ValidationRefusal(
            "unclosed_composition",
            "Fractions must sum to one without implicit renormalization",
        )
    return result


def _score(
    target: str, predicted: Mapping[str, float], observed: Mapping[str, float | None]
) -> CompositionScore:
    prediction = closed_composition(predicted)
    if set(prediction) != set(observed):
        raise ValidationRefusal(
            "taxon_denominator_mismatch",
            "Predicted and observed taxon keys must match; absence is not zero",
        )
    missing = tuple(sorted(key for key, value in observed.items() if value is None))
    present = {
        key: finite_number(value)
        for key, value in observed.items()
        if value is not None
    }
    if (
        any(value < 0 or value > 1 for value in present.values())
        or sum(present.values()) > 1 + 1e-9
    ):
        raise ValidationRefusal(
            "invalid_composition",
            "Observed fractions exceed their declared denominator",
        )
    if missing:
        # A partial composition cannot silently become a different denominator.
        return CompositionScore(
            target,
            "missing_observation",
            len(prediction),
            0,
            missing,
            None,
            None,
            None,
            None,
        )
    closed_composition(present)
    errors = [prediction[key] - present[key] for key in sorted(prediction)]
    n = len(errors)
    return CompositionScore(
        target,
        "scored",
        n,
        n,
        (),
        sum(abs(value) for value in errors) / n,
        sqrt(sum(value * value for value in errors) / n),
        sum(errors) / n,
        0.5 * sum(abs(value) for value in errors),
        signed_error_by_taxon=tuple(
            (key, prediction[key] - present[key]) for key in sorted(prediction)
        ),
    )


def score_vegetation(
    predicted: Mapping[str, float], observed: Mapping[str, float | None]
) -> CompositionScore:
    """Score matched-support vegetation fractions; missing observations stay missing.

    Temporal, spatial, taxonomy and observational-independence admission must be
    evidenced by the caller. This arithmetic routine cannot establish that support.
    """
    return _score("vegetation_cover", predicted, observed)


def score_pollen(
    predicted: Mapping[str, float], observed_counts: Mapping[str, int | None]
) -> CompositionScore:
    """Score raw counts against frozen predicted composition, conditioning on total.

    Multinomial deviance is 2*sum(count*ln(count/(total*probability))). Zero observed
    counts contribute zero, without pseudocounts. A positive count predicted with
    zero probability has infinite deviance, represented by an explicit failure
    flag and null numeric field so persisted JSON remains standards-compliant.
    """
    prediction = closed_composition(predicted)
    if set(prediction) != set(observed_counts):
        raise ValidationRefusal(
            "taxon_denominator_mismatch", "Pollen count keys must match predicted taxa"
        )
    for count in observed_counts.values():
        if count is not None and (
            isinstance(count, bool) or not isinstance(count, int) or count < 0
        ):
            raise ValidationRefusal(
                "invalid_pollen_counts",
                "Pollen observations must be nonnegative integer counts or null",
            )
    missing = tuple(
        sorted(key for key, value in observed_counts.items() if value is None)
    )
    if missing:
        return CompositionScore(
            "pollen_composition",
            "missing_observation",
            len(prediction),
            0,
            missing,
            None,
            None,
            None,
            None,
        )
    counts = {key: value for key, value in observed_counts.items() if value is not None}
    total = sum(counts.values())
    if total > 2**53:
        raise ValidationRefusal(
            "pollen_count_precision_exceeded",
            "Count total exceeds exact binary64 integer precision",
        )
    if total == 0:
        return CompositionScore(
            "pollen_composition",
            "zero_total_count",
            len(prediction),
            0,
            (),
            None,
            None,
            None,
            None,
            observed_total_count=0,
        )
    score = _score(
        "pollen_composition",
        prediction,
        {key: count / total for key, count in counts.items()},
    )
    impossible = any(
        count > 0 and prediction[key] == 0 for key, count in counts.items()
    )
    deviance = (
        None
        if impossible
        else max(
            0.0,
            2
            * sum(
                count * (log(count / total) - log(prediction[key]))
                for key, count in counts.items()
                if count > 0
            ),
        )
    )
    return CompositionScore(
        **{
            **score.as_dict(),
            "count_conditioned_deviance": deviance,
            "observed_total_count": total,
            "zero_probability_positive_count": impossible,
        }
    )
