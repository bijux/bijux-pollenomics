"""The preserved singleton workflow refuses invalid scheduling before numerical work."""

from pathlib import Path

import pytest

from bijux_pollenomics.analysis.lra_validation.experiments import (
    prepare_fitted_spatial_predictions,
)

from .test_model import payload


@pytest.mark.parametrize("workers", [0, -1, True, 1000000])
def test_singleton_worker_budget_precedes_backend_and_cache(
    tmp_path: Path, workers: int
) -> None:
    request = payload(tmp_path / "inputs")
    with pytest.raises(ValueError):
        prepare_fitted_spatial_predictions(
            request,
            input_root=tmp_path / "inputs",
            cache_root=tmp_path / "cache",
            destination=tmp_path / "product",
            workers=workers,
        )
    assert not (tmp_path / "product").exists() and not (tmp_path / "cache").exists()


def test_failed_fitted_fold_rechecks_sources(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from ..test_workflow import check_failed_source_revalidation

    check_failed_source_revalidation(
        tmp_path,
        monkeypatch,
        "bijux_pollenomics.analysis.lra_validation.experiments.fitted.workflow",
        "prepare_fitted_spatial_predictions",
        payload(tmp_path / "inputs"),
    )
