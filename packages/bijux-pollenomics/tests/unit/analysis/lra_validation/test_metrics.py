"""Separate vegetation/pollen denominators, zeros and invalid analytical outputs."""

import json
from math import log, sqrt
from typing import Any

import pytest

from bijux_pollenomics.analysis.lra_validation import (
    ValidationRefusal,
    score_pollen,
    score_vegetation,
)


def test_vegetation_fraction_metrics_have_explicit_taxon_denominator() -> None:
    score = score_vegetation({"tree": 0.8, "grass": 0.2}, {"tree": 0.6, "grass": 0.4})
    assert score.target == "vegetation_cover"
    assert score.status == "scored"
    assert score.mae_fraction == pytest.approx(0.2)
    assert score.rmse_fraction == pytest.approx(0.2)
    assert score.bias_fraction == pytest.approx(0)
    assert score.total_variation == pytest.approx(0.2)
    assert score.scored_taxon_count == 2


def test_missing_vegetation_never_becomes_zero_or_a_pollen_score() -> None:
    cover = {"tree": 1.0, "grass": 0.0}
    missing = score_vegetation(cover, {"tree": None, "grass": 0.0})
    zero = score_vegetation(cover, {"tree": 0.0, "grass": 1.0})
    pollen = score_pollen(cover, {"tree": 10, "grass": 0})
    assert missing.status == "missing_observation"
    assert missing.missing_observed_taxa == ("tree",)
    assert missing.mae_fraction is None and missing.scored_taxon_count == 0
    assert zero.mae_fraction == 1.0
    assert pollen.target == "pollen_composition" and pollen.mae_fraction == 0


@pytest.mark.parametrize(
    "predicted",
    [
        {"tree": -0.2, "grass": 1.2},
        {"tree": 0.2, "grass": 0.2},
        {"tree": float("nan"), "grass": 0.2},
        {"tree": True, "grass": 0},
    ],
)
def test_invalid_or_negative_analytical_love_is_not_clipped(
    predicted: dict[str, float],
) -> None:
    with pytest.raises(ValidationRefusal):
        score_vegetation(predicted, {"tree": 0.8, "grass": 0.2})


def test_absent_taxon_is_not_imputed_zero() -> None:
    with pytest.raises(ValidationRefusal) as error:
        score_vegetation({"tree": 1.0, "grass": 0}, {"tree": 1.0})
    assert error.value.reason_code == "taxon_denominator_mismatch"


def test_pollen_count_conditioned_deviance_uses_natural_log_no_pseudocounts() -> None:
    score = score_pollen({"tree": 0.25, "grass": 0.75}, {"tree": 5, "grass": 5})
    assert score.count_conditioned_deviance == pytest.approx(
        2 * (5 * log(2) + 5 * log(2 / 3))
    )
    assert score.observed_total_count == 10
    assert score.mae_fraction == 0.25


def test_impossible_pollen_prediction_has_explicit_json_safe_failure() -> None:
    score = score_pollen({"tree": 1.0, "grass": 0.0}, {"tree": 9, "grass": 1})
    assert score.zero_probability_positive_count
    assert score.count_conditioned_deviance is None
    json.dumps(score.as_dict(), allow_nan=False)


def test_zero_count_is_not_missing_and_zero_total_is_unscorable() -> None:
    prediction = {"tree": 1.0, "grass": 0.0}
    assert (
        score_pollen(prediction, {"tree": 10, "grass": 0}).count_conditioned_deviance
        == 0
    )
    empty = score_pollen(prediction, {"tree": 0, "grass": 0})
    assert empty.status == "zero_total_count" and empty.observed_total_count == 0
    assert (
        score_pollen(prediction, {"tree": 10, "grass": None}).status
        == "missing_observation"
    )


@pytest.mark.parametrize("count", [-1, True, 0.5, float("inf")])
def test_non_count_units_are_refused(count: Any) -> None:
    with pytest.raises(ValidationRefusal):
        score_pollen({"tree": 1.0}, {"tree": count})


def test_extremely_small_positive_probability_has_finite_deviance() -> None:
    score = score_pollen({"tree": 5e-324, "grass": 1.0}, {"tree": 1, "grass": 0})
    assert score.count_conditioned_deviance == pytest.approx(-2 * log(5e-324))
    assert not score.zero_probability_positive_count
    json.dumps(score.as_dict(), allow_nan=False)


def test_imprecise_count_total_and_unrepresentable_fractions_refuse() -> None:
    with pytest.raises(ValidationRefusal, match="exact binary64 integer"):
        score_pollen({"tree": 1.0}, {"tree": 2**53 + 1})
    with pytest.raises(ValidationRefusal, match="binary64 range"):
        score_vegetation({"tree": 10**1000}, {"tree": 1.0})


def test_signed_errors_remain_available_by_taxon_for_cohort_bias() -> None:
    score = score_vegetation({"tree": 0.8, "grass": 0.2}, {"tree": 0.6, "grass": 0.4})
    assert dict(score.signed_error_by_taxon) == pytest.approx(
        {"tree": 0.2, "grass": -0.2}
    )


def _decimal_rmse(predicted: dict[str, float], observed: dict[str, float]) -> float:
    from decimal import Decimal, localcontext

    with localcontext() as context:
        context.prec = 1100
        errors = [
            Decimal.from_float(predicted[key]) - Decimal.from_float(observed[key])
            for key in sorted(predicted)
        ]
        mean_square = sum((value * value for value in errors), Decimal(0)) / len(errors)
        return float(mean_square.sqrt())


@pytest.mark.parametrize("value", [1e-154, 1e-160, 1e-200, 1e-300, 1e-320, 5e-324])
@pytest.mark.parametrize("reverse", [False, True])
def test_tiny_composition_rmse_preserves_representable_fraction_error(
    value: float, reverse: bool
) -> None:
    from math import ulp

    predicted = {"rare": value, "tree": 0.5, "grass": 0.5}
    observed = {"rare": 0.0, "tree": 0.5, "grass": 0.5}
    if reverse:
        predicted, observed = observed, predicted
    expected = _decimal_rmse(predicted, observed)
    result = score_vegetation(predicted, observed)
    assert expected > 0 and result.rmse_fraction is not None
    assert result.rmse_fraction > 0
    assert abs(result.rmse_fraction - expected) <= 2 * ulp(expected)
    assert result.target == "vegetation_cover" and result.status == "scored"
    assert result.taxon_count == result.scored_taxon_count == 3
    assert result.mae_fraction == value / 3
    assert result.total_variation == value / 2
    assert result.signed_error_by_taxon == tuple(
        (key, predicted[key] - observed[key]) for key in sorted(predicted)
    )
    reordered = score_vegetation(
        dict(reversed(list(predicted.items()))), dict(reversed(list(observed.items())))
    )
    assert reordered == result
    json.dumps(result.as_dict(), allow_nan=False)


@pytest.mark.parametrize("value", [1e-160, 1e-200, 1e-300])
def test_tiny_pollen_rmse_keeps_count_denominator_and_deviance(value: float) -> None:
    from math import ulp

    predicted = {"rare": value, "tree": 0.5, "grass": 0.5}
    counts = {"rare": 0, "tree": 1, "grass": 1}
    expected = _decimal_rmse(predicted, {"rare": 0.0, "tree": 0.5, "grass": 0.5})
    result = score_pollen(predicted, counts)
    assert result.rmse_fraction is not None and result.rmse_fraction > 0
    assert abs(result.rmse_fraction - expected) <= 2 * ulp(expected)
    assert result.observed_total_count == 2
    assert result.count_conditioned_deviance == 0
    assert not result.zero_probability_positive_count
    assert result.target == "pollen_composition" and result.scored_taxon_count == 3


@pytest.mark.parametrize(
    ("predicted", "observed"),
    [
        ({"tree": 0.8, "grass": 0.2}, {"tree": 0.6, "grass": 0.4}),
        ({"tree": 1.0, "grass": 0.0}, {"tree": 0.0, "grass": 1.0}),
        (
            {"rare": 1e-300, "tree": 0.75, "grass": 0.25},
            {"rare": 0.0, "tree": 0.5, "grass": 0.5},
        ),
    ],
)
def test_normal_mean_square_keeps_existing_bitwise_arithmetic(
    predicted: dict[str, float], observed: dict[str, float]
) -> None:
    errors = [predicted[key] - observed[key] for key in sorted(predicted)]
    expected = sqrt(sum(value * value for value in errors) / len(errors))
    result = score_vegetation(predicted, observed)
    assert result.rmse_fraction is not None
    assert result.rmse_fraction.hex() == expected.hex()


def test_true_zero_and_missing_observation_keep_their_postures() -> None:
    composition = {"rare": 1e-300, "tree": 0.5, "grass": 0.5}
    zero = score_vegetation(composition, composition)
    assert zero.rmse_fraction == 0 and zero.status == "scored"
    missing = score_vegetation(composition, {"rare": None, "tree": 0.5, "grass": 0.5})
    assert missing.status == "missing_observation"
    assert missing.rmse_fraction is None and missing.scored_taxon_count == 0


def _smallest_subnormal_axis(
    taxon_count: int, changed_taxa: int
) -> tuple[dict[str, float], dict[str, float]]:
    from math import nextafter

    smallest = nextafter(0.0, 1.0)
    predicted = {
        f"rare{index:02}": smallest if index < changed_taxa else 0.0
        for index in range(taxon_count - 2)
    }
    observed = dict.fromkeys(predicted, 0.0)
    predicted.update(tree=0.5, grass=0.5)
    observed.update(tree=0.5, grass=0.5)
    return predicted, observed


@pytest.mark.parametrize("taxon_count,changed_taxa", [(17, 5), (31, 7)])
@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("permutation", ["original", "reverse", "rotate"])
def test_smallest_subnormal_rmse_rounds_only_the_final_fraction(
    taxon_count: int, changed_taxa: int, reverse: bool, permutation: str
) -> None:
    from math import nextafter

    predicted, observed = _smallest_subnormal_axis(taxon_count, changed_taxa)
    if reverse:
        predicted, observed = observed, predicted
    keys = list(predicted)
    if permutation == "reverse":
        keys.reverse()
    elif permutation == "rotate":
        keys = keys[3:] + keys[:3]
    predicted = {key: predicted[key] for key in keys}
    observed = {key: observed[key] for key in reversed(keys)}
    expected = _decimal_rmse(predicted, observed)
    assert expected == (nextafter(0.0, 1.0) if taxon_count == 17 else 0.0)
    result = score_vegetation(predicted, observed)
    assert result.rmse_fraction == expected
    assert result.taxon_count == result.scored_taxon_count == taxon_count
    assert result.target == "vegetation_cover" and result.status == "scored"


@pytest.mark.parametrize("taxon_count,changed_taxa", [(17, 5), (31, 7)])
def test_pollen_smallest_subnormal_rmse_keeps_declared_axis(
    taxon_count: int, changed_taxa: int
) -> None:
    predicted, observed = _smallest_subnormal_axis(taxon_count, changed_taxa)
    counts = {key: 1 if key in {"tree", "grass"} else 0 for key in observed}
    result = score_pollen(predicted, counts)
    assert result.observed_total_count == 2 and result.taxon_count == taxon_count
    assert result.rmse_fraction == _decimal_rmse(predicted, observed)
    assert result.count_conditioned_deviance == 0
    assert not result.zero_probability_positive_count


@pytest.mark.parametrize(
    "taxon_count,units,expected_units",
    [(100, 5, 0), (36, 3, 0), (4, 3, 2), (16, 6, 2), (16, 10, 2)],
)
@pytest.mark.parametrize("reverse", [False, True])
def test_exact_subnormal_half_ties_choose_even_final_fraction(
    taxon_count: int, units: int, expected_units: int, reverse: bool
) -> None:
    from math import nextafter

    smallest = nextafter(0.0, 1.0)
    predicted, observed = _smallest_subnormal_axis(taxon_count, 0)
    predicted["rare00"] = units * smallest
    if reverse:
        predicted, observed = observed, predicted
    reference = _decimal_rmse(predicted, observed)
    assert reference == expected_units * smallest
    assert score_vegetation(predicted, observed).rmse_fraction == reference


@pytest.mark.parametrize("taxon_count,changed_taxa", [(3, 1), (17, 15), (100, 98)])
@pytest.mark.parametrize("offset", [-3, -2, -1, 0, 1, 2, 3])
@pytest.mark.parametrize("reverse", [False, True])
def test_rmse_minimum_normal_seam_rounds_exact_declared_axis(
    taxon_count: int, changed_taxa: int, offset: int, reverse: bool
) -> None:
    from decimal import Decimal, localcontext
    from math import nextafter
    from sys import float_info

    smallest = nextafter(0.0, 1.0)
    with localcontext() as context:
        context.prec = 1100
        center = float(
            Decimal.from_float(float_info.min)
            * (Decimal(taxon_count) / Decimal(changed_taxa)).sqrt()
        )
    predicted, observed = _smallest_subnormal_axis(taxon_count, 0)
    for index in range(changed_taxa):
        predicted[f"rare{index:02}"] = center + offset * smallest
    if reverse:
        predicted, observed = observed, predicted
    expected = _decimal_rmse(predicted, observed)
    result = score_vegetation(predicted, observed)
    assert result.rmse_fraction == expected
    assert result.taxon_count == result.scored_taxon_count == taxon_count
    assert result.target == "vegetation_cover" and result.status == "scored"
    assert result.signed_error_by_taxon == tuple(
        (key, predicted[key] - observed[key]) for key in sorted(predicted)
    )
    assert (
        score_vegetation(
            dict(reversed(list(predicted.items()))),
            dict(reversed(list(observed.items()))),
        )
        == result
    )


@pytest.mark.parametrize("taxon_count,changed_taxa", [(3, 1), (17, 15), (100, 98)])
def test_pollen_rmse_minimum_normal_seam_retains_counts_and_refusals(
    taxon_count: int, changed_taxa: int
) -> None:
    from decimal import Decimal, localcontext
    from math import nextafter
    from sys import float_info

    with localcontext() as context:
        context.prec = 1100
        center = float(
            Decimal.from_float(float_info.min)
            * (Decimal(taxon_count) / Decimal(changed_taxa)).sqrt()
        )
    predicted, observed = _smallest_subnormal_axis(taxon_count, 0)
    for index in range(changed_taxa):
        predicted[f"rare{index:02}"] = center - nextafter(0.0, 1.0)
    counts: dict[str, int | None] = {
        key: 1 if key in {"tree", "grass"} else 0 for key in observed
    }
    result = score_pollen(predicted, counts)
    assert result.rmse_fraction == _decimal_rmse(predicted, observed)
    assert result.taxon_count == taxon_count and result.observed_total_count == 2
    assert result.count_conditioned_deviance == 0
    assert not result.zero_probability_positive_count
    counts["rare00"] = None
    missing = score_pollen(predicted, counts)
    assert missing.status == "missing_observation" and missing.rmse_fraction is None
    with pytest.raises(ValidationRefusal, match="nonnegative integer"):
        score_pollen(
            predicted,
            {key: True if key == "rare00" else value for key, value in counts.items()},
        )


@pytest.mark.parametrize("offset", [-4, -2, -1, 0, 1, 2, 4])
def test_rmse_adjacent_normal_guard_edge_has_bounded_fraction_error(
    offset: int,
) -> None:
    from decimal import Decimal, localcontext
    from math import nextafter, ulp
    from sys import float_info

    with localcontext() as context:
        context.prec = 1100
        center = float(Decimal.from_float(1.5 * float_info.min) * Decimal(3).sqrt())
    predicted = {
        "rare": center + offset * nextafter(0.0, 1.0),
        "tree": 0.5,
        "grass": 0.5,
    }
    observed = {"rare": 0.0, "tree": 0.5, "grass": 0.5}
    expected = _decimal_rmse(predicted, observed)
    result = score_vegetation(predicted, observed)
    assert result.rmse_fraction is not None
    assert abs(result.rmse_fraction - expected) <= 2 * ulp(expected)
