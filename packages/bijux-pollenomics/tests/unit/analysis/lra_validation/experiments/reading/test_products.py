"""The public retained reader preserves singleton keys and owned copies."""

import json
from pathlib import Path

from bijux_pollenomics.analysis.lra_validation import Fold, manifest_sha256
from bijux_pollenomics.analysis.lra_validation.experiments import (
    read_spatial_block_local_pollen_predictions,
    read_withheld_predictions,
)
from bijux_pollenomics.analysis.lra_validation.experiments.reading.products import (
    _same_outer_fold,
)

from ..test_scoring import prediction_product


def test_retained_reader_extraction_preserves_public_key_shape(tmp_path: Path) -> None:
    product, _ = prediction_product(tmp_path)
    _, _, folds, rows, methods = read_withheld_predictions(
        product.directory, expected_manifest_sha256=product.manifest_sha256
    )
    assert len(rows) == len(folds) * len(methods)
    assert all(len(key) == 2 for key in rows)


def test_block_local_reader_requires_a_caller_pinned_manifest(tmp_path: Path) -> None:
    missing = tmp_path / "not-a-product"
    try:
        read_spatial_block_local_pollen_predictions(
            missing, expected_manifest_sha256="0" * 64
        )
    except Exception as exc:
        assert getattr(exc, "reason_code", None) == "invalid_experiment_product"
    else:
        raise AssertionError("An absent pinned product must refuse")


def test_block_local_outer_fold_accepts_exact_json_round_trip() -> None:
    typed = Fold("block:a", ("q03",), ("q01", "q02"), ("g03",), ("g01", "g02"))
    reopened = json.loads(json.dumps(typed.as_dict()))
    assert _same_outer_fold(reopened, typed.as_dict())


def test_block_local_outer_fold_refuses_rehashed_changed_membership() -> None:
    typed = Fold("block:a", ("q03",), ("q01", "q02"), ("g03",), ("g01", "g02"))
    reopened = json.loads(json.dumps(typed.as_dict()))
    changed = json.loads(json.dumps(reopened))
    changed["train_record_ids"] = ["q04"]
    assert manifest_sha256(changed) != manifest_sha256(reopened)
    assert not _same_outer_fold(changed, typed.as_dict())
