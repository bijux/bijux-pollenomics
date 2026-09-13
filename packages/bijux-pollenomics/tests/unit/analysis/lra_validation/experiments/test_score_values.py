"""Shared observation decoding preserves meaningful descriptive denominators."""

import pytest

from bijux_pollenomics.analysis.lra_validation import ValidationRefusal
from bijux_pollenomics.analysis.lra_validation.experiments import (
    scoring as experiment_scoring,
)
from bijux_pollenomics.analysis.lra_validation.experiments.score_values import (
    score_observation,
)
from bijux_pollenomics.analysis.lra_validation.temporal.persistence import (
    scoring as temporal_scoring,
)


def test_existing_scorers_share_the_exact_decoder() -> None:
    alias = "_score"
    assert (
        getattr(experiment_scoring, alias)
        is getattr(temporal_scoring, alias)
        is score_observation
    )


def test_unequal_pollen_count_and_vegetation_errors_are_separate() -> None:
    predicted: dict[str, object] = {
        "vegetation_fraction": {"A": 0.7, "B": 0.3},
        "pollen_fraction": {"A": 0.7, "B": 0.3},
    }
    observed: dict[str, object] = {
        "vegetation_unit": "fraction",
        "pollen_unit": "count",
        "vegetation_fraction": {"A": 0.5, "B": 0.5},
        "pollen_count": {"A": 6, "B": 4},
    }
    vegetation = score_observation("vegetation_cover", predicted, observed)
    pollen = score_observation("pollen_composition", predicted, observed)
    assert vegetation["mae_fraction"] == pytest.approx(0.2)
    assert pollen["mae_fraction"] == pytest.approx(0.1)
    assert pollen["observed_total_count"] == 10
    assert pollen["count_conditioned_deviance"] == pytest.approx(0.4516484216871465)
    assert vegetation["count_conditioned_deviance"] is None


@pytest.mark.parametrize(
    "observation", [None, {"vegetation_unit": "fraction", "vegetation_fraction": None}]
)
def test_unavailable_observation_is_not_zero(
    observation: dict[str, object] | None,
) -> None:
    assert score_observation("vegetation_cover", {}, observation) == {
        "status": "missing_observation",
        "mae_fraction": None,
        "reason": "target_not_supplied",
    }


def test_boolean_count_is_not_an_integer_observation() -> None:
    with pytest.raises(ValidationRefusal) as failure:
        score_observation(
            "pollen_composition",
            {"pollen_fraction": {"A": 0.7, "B": 0.3}},
            {"pollen_unit": "count", "pollen_count": {"A": True, "B": 9}},
        )

    assert failure.value.reason_code == "invalid_pollen_counts"
