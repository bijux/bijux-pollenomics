"""Positive observed taxa must survive finite covariance correction arithmetic."""

from collections.abc import Sequence
from typing import Literal
import warnings

import numpy as np
from numpy.typing import NDArray
import pytest

from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.reconstruction.fixed_site_covariance import (
    FixedSiteCovariance,
    fixed_site_cover_covariance,
)
from bijux_pollenomics_lra.reconstruction.joint_fixed_site_covariance import (
    ConditionalResultInput,
    CountSupport,
    JointFixedSiteCovariance,
    joint_fixed_site_covariance,
)


def evaluate(
    consumer: Literal["fixed", "joint"],
    counts: Sequence[int],
    deposition: Sequence[float],
    ppe: Sequence[float],
    measured: Sequence[bool] | None = None,
) -> FixedSiteCovariance | JointFixedSiteCovariance:
    count_array: NDArray[np.int64] = np.array(counts)
    measured_array: NDArray[np.bool_] = (
        np.ones(2, dtype=bool) if measured is None else np.array(measured)
    )
    if consumer == "fixed":
        return fixed_site_cover_covariance(
            count_array[None, :],
            np.array([deposition]),
            np.array(ppe),
            np.zeros((2, 2)),
            taxon_measured=measured_array[None, :],
        )
    item = ConditionalResultInput(
        "observed-panel",
        CountSupport(1, 1, 1, 0, 100, "a" * 64),
        ("a", "b"),
        count_array,
        np.array(deposition),
        measured_array,
    )
    return joint_fixed_site_covariance(
        (item,),
        parameter_ids=("a", "b"),
        ppe=np.array(ppe),
        ppe_covariance=np.zeros((2, 2)),
        assume_disjoint_window_count_independence=False,
        assume_distinct_unit_count_independence=False,
    )


@pytest.mark.parametrize("consumer", ["fixed", "joint"])
@pytest.mark.parametrize(
    ("deposition", "ppe"),
    [
        ([1e200, 1e200], [1e200, 1e100]),
        ([1e308, 1e308], [10.0, 0.1]),
        ([1e-200, 1e-200], [1e-200, 1e-100]),
    ],
)
def test_unrepresentable_correction_factors_refuse_without_losing_taxa(
    consumer: Literal["fixed", "joint"],
    deposition: Sequence[float],
    ppe: Sequence[float],
) -> None:
    # The source values are finite; their product/reciprocal can lose the
    # positive observed support or produce a nonfinite correction derivative.
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        with pytest.raises(ValidationError, match="correction factors"):
            evaluate(consumer, [30, 70], deposition, ppe)


@pytest.mark.parametrize("consumer", ["fixed", "joint"])
@pytest.mark.parametrize(
    ("counts", "deposition"), [([30, 70], [1e308, 1e308]), ([1, 1], [2e-308, 2e-308])]
)
def test_representable_extreme_factors_retain_exact_binomial_profile(
    consumer: Literal["fixed", "joint"],
    counts: Sequence[int],
    deposition: Sequence[float],
) -> None:
    out = evaluate(consumer, counts, deposition, [1, 1])
    total = sum(counts)
    probability = counts[0] / total
    variance = probability * (1 - probability) / total
    np.testing.assert_allclose(out.cover, [probability, 1 - probability], rtol=3e-15)
    np.testing.assert_allclose(
        out.counting_covariance,
        np.array([[variance, -variance], [-variance, variance]]),
        rtol=3e-15,
    )


@pytest.mark.parametrize("consumer", ["fixed", "joint"])
def test_observed_zero_retains_its_finite_parameter_axis(
    consumer: Literal["fixed", "joint"],
) -> None:
    out = evaluate(consumer, [0, 70], [1, 1], [1, 1])
    np.testing.assert_array_equal(out.cover, [0, 1])
    np.testing.assert_array_equal(out.counting_covariance, np.zeros((2, 2)))


@pytest.mark.parametrize("consumer", ["fixed", "joint"])
def test_unmeasured_taxon_refuses_before_extreme_arithmetic(
    consumer: Literal["fixed", "joint"],
) -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        with pytest.raises(ValidationError, match="[Uu]nmeasured|measured"):
            evaluate(
                consumer, [30, 70], [1e308, 1e308], [10, 0.1], measured=[False, True]
            )
