"""The block-local producer is outcome-free and preserves target-level accounting."""

from inspect import signature
from pathlib import Path

from bijux_pollenomics.analysis.lra_validation.experiments.block_assimilation import (
    _failure,
    prepare_spatial_block_local_pollen_predictions,
)
from bijux_pollenomics.analysis.lra_validation.experiments.configuration import (
    LOCAL_METHOD,
    SpatialBlockLocalPollenSpec,
)
from bijux_pollenomics.analysis.lra_validation.splits import grouped_block_holdouts

from .fitted.test_admission import block_local_payload


def test_producer_has_no_outcome_or_scoring_input() -> None:
    parameters = signature(prepare_spatial_block_local_pollen_predictions).parameters
    assert set(parameters) == {
        "spec",
        "input_root",
        "cache_root",
        "destination",
        "workers",
    }
    assert not ({"outcome_root", "outcome_inventory", "thresholds"} & set(parameters))


def test_failure_is_one_terminal_target_not_a_replacement_fold(tmp_path: Path) -> None:
    spec = SpatialBlockLocalPollenSpec(block_local_payload(tmp_path))
    fold = next(
        item
        for item in grouped_block_holdouts([site.record for site in spec.sites])
        if len(item.test_record_ids) == 3
    )
    row = _failure(fold, fold.test_record_ids[1], fold.test_group_ids[1], ValueError())
    assert row["fold_id"] == fold.fold_id
    assert row["record_id"] == fold.test_record_ids[1]
    assert row["method"] == LOCAL_METHOD
    assert row["status"] == "refused"


def test_interrupt_status_and_reason_are_coupled(tmp_path: Path) -> None:
    spec = SpatialBlockLocalPollenSpec(block_local_payload(tmp_path))
    fold = grouped_block_holdouts([site.record for site in spec.sites])[0]
    row = _failure(
        fold,
        fold.test_record_ids[0],
        fold.test_group_ids[0],
        KeyboardInterrupt(),
        not_run=True,
    )
    assert (row["status"], row["reason_code"]) == (
        "not_run",
        "experiment_interrupted",
    )
