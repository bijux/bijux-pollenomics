"""Verify stable Hellinger fractions and explicit historical arithmetic contracts."""

from math import sqrt
from typing import Any

import pytest

from bijux_pollenomics.analysis.lra_validation import ValidationRefusal
from bijux_pollenomics.analysis.lra_validation.metrics import hellinger_distance


def test_hellinger_distance_has_closed_composition_endpoints() -> None:
    assert hellinger_distance({"tree": 1, "grass": 0}, {"tree": 1, "grass": 0}) == 0
    assert hellinger_distance({"tree": 1, "grass": 0}, {"tree": 0, "grass": 1}) == 1
    assert hellinger_distance(
        {"tree": 1, "grass": 0}, {"tree": 0.5, "grass": 0.5}
    ) == pytest.approx(sqrt(1 - 1 / sqrt(2)))
    with pytest.raises(ValidationRefusal, match="taxon keys must match"):
        hellinger_distance({"tree": 1}, {"grass": 1})


def _decimal_hellinger(
    predicted: dict[str, float], observed: dict[str, float]
) -> float:
    from decimal import Decimal, localcontext

    with localcontext() as context:
        context.prec = 1100
        squared_roots = sum(
            (
                (
                    Decimal.from_float(predicted[key]).sqrt()
                    - Decimal.from_float(observed[key]).sqrt()
                )
                ** 2
                for key in sorted(predicted)
            ),
            Decimal(0),
        )
        return float((squared_roots / 2).sqrt())


@pytest.mark.parametrize(
    "left,right,closed_rest",
    [
        (float.fromhex("0x0.0000000000001p-1022"), 0.0, True),
        (1e-300, 0.0, True),
        (0.25, float.fromhex("0x1.0000000000001p-2"), True),
        (float.fromhex("0x1.fffffffffffffp-1"), 1.0, False),
        (0.8, 0.6, True),
        (1.0, 0.0, True),
        (0.0, 0.0, True),
    ],
)
@pytest.mark.parametrize("reverse", [False, True])
def test_hellinger_preserves_finite_fraction_distance(
    left: float, right: float, closed_rest: bool, reverse: bool
) -> None:
    from math import ulp

    # The public closure tolerance admits the adjacent and subnormal cases;
    # the oracle scores their actual fractions without implicit normalization.
    predicted = {"tree": left, "grass": 1.0 - left if closed_rest else 0.0}
    observed = {"tree": right, "grass": 1.0 - right if closed_rest else 0.0}
    if reverse:
        predicted, observed = observed, predicted
    expected = _decimal_hellinger(predicted, observed)
    result = hellinger_distance(predicted, observed)
    assert (result > 0) == (expected > 0)
    assert abs(result - expected) <= 4 * ulp(expected)
    assert (
        hellinger_distance(dict(reversed(list(predicted.items()))), observed) == result
    )


@pytest.mark.parametrize("value", [-0.1, float("nan"), True])
def test_hellinger_preserves_invalid_fraction_refusal(value: Any) -> None:
    with pytest.raises(ValidationRefusal):
        hellinger_distance({"tree": value, "grass": 1.0}, {"tree": 0.0, "grass": 1.0})


@pytest.mark.parametrize("profile", ["stable", "source-compatible-22c6e480"])
def test_explicit_hellinger_profiles_keep_closed_endpoints(profile: Any) -> None:
    assert (
        hellinger_distance(
            {"tree": 1.0, "grass": 0.0},
            {"tree": 0.0, "grass": 1.0},
            arithmetic_profile=profile,
        )
        == 1.0
    )
    with pytest.raises(ValidationRefusal):
        hellinger_distance({"tree": -1.0}, {"tree": 1.0}, arithmetic_profile=profile)


def test_source_arithmetic_keeps_historical_underflow_without_changing_default() -> (
    None
):
    tiny = float.fromhex("0x0.0000000000001p-1022")
    predicted = {"tree": tiny, "grass": 1.0}
    observed = {"tree": 0.0, "grass": 1.0}
    stable = hellinger_distance(predicted, observed)
    assert stable > 0.0
    assert stable == hellinger_distance(
        predicted, observed, arithmetic_profile="stable"
    )
    # Half the least subnormal squared-root contribution rounds to zero in
    # the retained source arithmetic. This is a provenance limit, not a fix.
    assert (
        hellinger_distance(
            predicted, observed, arithmetic_profile="source-compatible-22c6e480"
        )
        == 0.0
    )


def test_unknown_hellinger_arithmetic_profile_refuses() -> None:
    unknown: Any = "unreviewed"
    with pytest.raises(ValueError, match="Unknown Hellinger arithmetic profile"):
        hellinger_distance({"tree": 1.0}, {"tree": 1.0}, arithmetic_profile=unknown)


def test_source_hellinger_retains_nontrivial_historical_distance() -> None:
    predicted = {"tree": 0.5, "grass": 0.25, "herb": 0.25}
    observed = {"tree": 0.25, "grass": 0.5, "herb": 0.25}
    assert hellinger_distance(
        predicted, observed, arithmetic_profile="source-compatible-22c6e480"
    ) == float.fromhex("0x1.a827999fcef34p-3")


@pytest.mark.parametrize(
    "rare_first,expected",
    [
        (False, float.fromhex("0x1.ffffffffffffep-1")),
        (True, 1.0),
    ],
)
def test_source_hellinger_retains_prediction_insertion_order(
    rare_first: bool, expected: float
) -> None:
    # Both compositions close exactly. Left-to-right historical summation loses
    # individual rare contributions after the large terms, but retains their sum
    # when they precede those terms; sorting or fsum would change the contract.
    rare = {f"rare{index:02}": 2.0**-54 for index in range(16)}
    common = {"tree": 1.0 - 2.0**-50, "grass": 0.0}
    predicted = {**rare, **common} if rare_first else {**common, **rare}
    observed = {"tree": 0.0, "grass": 1.0, **dict.fromkeys(rare, 0.0)}
    assert (
        hellinger_distance(
            predicted, observed, arithmetic_profile="source-compatible-22c6e480"
        )
        == expected
    )
    assert (
        hellinger_distance(
            predicted,
            dict(reversed(list(observed.items()))),
            arithmetic_profile="source-compatible-22c6e480",
        )
        == expected
    )
