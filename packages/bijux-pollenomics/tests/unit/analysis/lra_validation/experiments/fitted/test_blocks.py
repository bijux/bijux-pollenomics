"""Block scheduling failures do not manufacture successful target accounting."""

from pathlib import Path

import pytest

from bijux_pollenomics.analysis.lra_validation.experiments import (
    prepare_spatial_block_predictions,
)
from bijux_pollenomics.analysis.lra_validation.experiments.fitted.blocks import _failure

from .test_admission import block_payload


@pytest.mark.parametrize("workers", [0, -1, True, 1000000])
def test_block_worker_budget_precedes_backend_and_cache(
    tmp_path: Path, workers: int
) -> None:
    request = block_payload(tmp_path / "inputs")
    with pytest.raises(ValueError):
        prepare_spatial_block_predictions(
            request,
            input_root=tmp_path / "inputs",
            cache_root=tmp_path / "cache",
            destination=tmp_path / "product",
            workers=workers,
        )
    assert not (tmp_path / "product").exists() and not (tmp_path / "cache").exists()


def test_interrupt_receipt_preserves_actual_target_and_exception() -> None:
    row = _failure("block:a", "target", "group", KeyboardInterrupt(), True)
    assert row["record_id"] == "target" and row["group_id"] == "group"
    assert row["status"] == "not_run" and row["exception_type"] == "KeyboardInterrupt"
