"""Public experiment orchestration refuses invalid budgets before work starts."""

from pathlib import Path

import pytest

from bijux_pollenomics.analysis.lra_validation.experiments import (
    prepare_experiment_predictions,
)

from .test_inputs import fixture_inputs


@pytest.mark.parametrize("workers", [0, -1, True, 1_000_000])
def test_worker_budget_is_validated_before_work(tmp_path: Path, workers: int) -> None:
    payload = fixture_inputs(tmp_path / "inputs")
    with pytest.raises(ValueError):
        prepare_experiment_predictions(
            payload,
            input_root=tmp_path / "inputs",
            cache_root=tmp_path / "cache",
            destination=tmp_path / "prediction",
            workers=workers,
        )
    assert not (tmp_path / "prediction").exists()
    assert not (tmp_path / "cache").exists()
